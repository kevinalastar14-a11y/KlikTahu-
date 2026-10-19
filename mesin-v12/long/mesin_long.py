#!/usr/bin/env python3
"""MESIN LONG 16:9 - video panjang KlikTahu (1920x1080).

Terpisah total dari mesin Shorts (render.py / mesin_v11 tidak diubah; hanya dipinjam
primitifnya). Isi:
  - penyelarasan kata (align): waktu tiap kata dari audio VO -> beat visual & SFX
    dikunci ke KATA yang diucapkan, bukan fraksi durasi (akurat untuk bab 50-60 s)
  - Ctx: API adegan  C.w("kata"), C.tt(...), C.u(...), C.win(a, b)
  - latar antariksa: gradasi + nebula + 2 lapis bintang paralaks + kelip
  - komponen: lubang hitam (piringan akresi + cincin lensa + bayangan + cincin foton
    berlapis, gumpalan panas berputar), bintang, Bumi, astronot (bisa diregang /
    dimerahkan), roket, jam, galaksi spiral, parabola radio, mata
  - tipografi: teks ber-alpha ter-cache, judul kinetik per kata, kartu kaca,
    callout bergaris, penghitung angka format Indonesia, stiker (mesin_v11)
  - kamera: napas halus + dorong pada beat berat + zoom per adegan
  - transisi bab (zoom-blur keluar / mendarat masuk), kartu judul bab, HUD
    (brand, chip bab, bilah progres bersegmen), finishing (tajam, vinyet, grain)
"""
import math
import os
import random
import re
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import diagrams as D                      # noqa: E402
import mesin_v11 as M                     # noqa: E402
import mesin_fx as FX                     # noqa: E402  (FX 2026: bloom, grade, liquid glass, dll.)
from diagrams import (mix, clamp, seg, eo, eio, eob, esmooth, font, tw, tlh,  # noqa: E402,F401
                      FB, FS, FM, FR, WHITE, hexc)

W, H = 1920, 1080


def S(v):
    return v * D.SS


# ------------------------------------------------------------------ palet antariksa
SP0 = (4, 5, 14)
SP1 = (10, 11, 30)
SP2 = (22, 17, 46)
TEKS = (240, 242, 250)
REDUP = (150, 158, 192)
ORANYE = (242, 153, 74)
EMAS = (246, 200, 90)
SIAN = (86, 204, 242)
MERAH = (235, 87, 87)
UNGU = (187, 107, 217)
HIJAU = (111, 207, 151)
PANAS = (255, 222, 170)
KACA = (16, 18, 42)

_CACHES = []


def _cache():
    d = {}
    _CACHES.append(d)
    return d


def set_ss(ss):
    D.SS = float(ss)


# ================================================================== penyelarasan kata
def normw(w):
    return re.sub(r"[^0-9a-z]", "", w.lower())


def _read_mono(p):
    with wave.open(p) as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels())
    return a.mean(axis=1).astype(np.float64) / 32768.0, sr


def _wbobot(w):
    return len(normw(w)) + 1.6


def _peta_bicara(sp, i0, i1, fracs):
    """Petakan fraksi bobot -> indeks hop di [i0, i1) dengan hanya menghitung hop bicara."""
    seg_ = sp[i0:i1]
    cs = np.cumsum(seg_)
    tot = int(cs[-1]) if len(cs) else 0
    if tot < 1:
        return [i0 + int((i1 - i0) * f) for f in fracs]
    return [i0 + int(np.searchsorted(cs, f * tot + 0.5)) for f in fracs]


def align(tl, audio_dir, thr_db=-40.0, gap_fill=0.12, min_jeda=0.16):
    """Isi sc['words'] = [[kata_normal, detik_relatif_adegan], ...].

    1) Jeda nyata di audio (>= 0,16 s) dicocokkan ke tanda baca naskah dengan DP
       (monoton, boleh melewati) -> jangkar: kata sesudah tanda baca mulai tepat
       saat suara kembali.
    2) Di antara jangkar, kata dibagi menurut bobot huruf pada waktu bicara saja.
    """
    for sc in tl["scenes"]:
        words = sc["vo"].split()
        a, sr = _read_mono(os.path.join(audio_dir, sc["id"] + ".wav"))
        hop = int(sr * 0.01)
        n = len(a) // hop
        db = 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-9)
        sp = db > thr_db
        g = int(gap_fill / 0.01)
        idx = np.where(sp)[0]
        for i0, i1 in zip(idx[:-1], idx[1:]):
            if 1 < i1 - i0 <= g:
                sp[i0:i1] = True
        idx = np.where(sp)[0]
        s0, s1 = int(idx[0]), int(idx[-1]) + 1
        # jeda (awal, akhir) di dalam ujaran
        jeda = []
        run = None
        for i in range(s0, s1):
            if not sp[i]:
                run = i if run is None else run
            elif run is not None:
                if (i - run) * 0.01 >= min_jeda:
                    jeda.append((run, i))
                run = None
        # tanda baca & perkiraan waktunya (model: bicara per bobot + jeda per tanda baca)
        pj = [j for j, w in enumerate(words[:-1]) if w[-1] in ",.?!;:"]
        pw = {",": 0.30, ";": 0.4, ":": 0.4, ".": 0.55, "?": 0.6, "!": 0.55}
        wts = np.array([_wbobot(w) for w in words])
        jeda_tot = sum(pw[words[j][-1]] for j in pj)
        rate = max(1e-3, ((s1 - s0) * 0.01 - jeda_tot) / wts.sum())
        exp = {}
        t_ = s0 * 0.01
        for j, w in enumerate(words):
            t_ += wts[j] * rate
            if j in pj:
                exp[j] = t_ + pw[w[-1]] / 2
                t_ += pw[w[-1]]
        # DP monoton: pasangkan tanda baca <-> jeda
        m, k = len(pj), len(jeda)
        INF = 1e9
        SKIP_P, SKIP_J = 0.9, 0.9
        cost = np.full((m + 1, k + 1), INF)
        back = np.zeros((m + 1, k + 1), dtype=np.int8)
        cost[0, :] = np.arange(k + 1) * SKIP_J
        cost[:, 0] = np.arange(m + 1) * SKIP_P
        for x in range(1, m + 1):
            ex = exp[pj[x - 1]]
            bonus = 0.25 if words[pj[x - 1]][-1] in ".?!" else 0.0
            for y in range(1, k + 1):
                mid = (jeda[y - 1][0] + jeda[y - 1][1]) * 0.005
                dur_j = (jeda[y - 1][1] - jeda[y - 1][0]) * 0.01
                c_m = cost[x - 1, y - 1] + min(abs(ex - mid), 3.0) - bonus * min(1.0, dur_j / 0.4)
                c_p = cost[x - 1, y] + SKIP_P
                c_j = cost[x, y - 1] + SKIP_J
                best = min(c_m, c_p, c_j)
                cost[x, y] = best
                back[x, y] = 0 if best == c_m else (1 if best == c_p else 2)
        x, y = m, k
        anchor = {}
        while x > 0 and y > 0:
            if back[x, y] == 0:
                anchor[pj[x - 1]] = jeda[y - 1]
                x, y = x - 1, y - 1
            elif back[x, y] == 1:
                x -= 1
            else:
                y -= 1
        # bagi kata per segmen di antara jangkar
        starts = [0] * len(words)
        batas = [(-1, s0)] + sorted((j, e) for j, (b_, e) in anchor.items())
        ends_ = {j: b_ for j, (b_, e) in anchor.items()}
        for bi, (jb, t_start) in enumerate(batas):
            j0 = jb + 1
            if bi + 1 < len(batas):
                j1 = batas[bi + 1][0]
                t_end = ends_[j1]
            else:
                j1 = len(words) - 1
                t_end = s1
            ws = wts[j0:j1 + 1]
            if len(ws) == 0:
                continue
            fr = np.concatenate([[0.0], np.cumsum(ws)])[:-1] / ws.sum()
            pos = _peta_bicara(sp, t_start, max(t_start + 1, t_end), fr)
            for q, j in enumerate(range(j0, j1 + 1)):
                starts[j] = pos[q]
        off = sc["vo_at"] - sc["start"]
        sc["words"] = [[normw(w), round(off + int(i) * 0.01, 3)] for w, i in zip(words, starts)]
        sc["align_info"] = {"tanda_baca": m, "jeda": k, "jangkar": len(anchor)}
    return tl


class Ctx:
    """Konteks adegan. Semua waktu relatif awal adegan (detik)."""

    def __init__(self, sc, tl, tg, i, n):
        self.sc, self.tl, self.tg, self.i, self.n = sc, tl, tg, i, n
        self.dur = sc["dur"]
        self.acc = hexc(sc.get("accent", "#F2994A"))
        self.words = sc.get("words") or []
        self.zoom, self.fx, self.fy = 1.0, 0.5, 0.5

    def w(self, key, n=1, off=0.0):
        ks = [normw(k) for k in key.split()]
        hit = 0
        for j in range(len(self.words) - len(ks) + 1):
            if all(self.words[j + m][0] == ks[m] for m in range(len(ks))):
                hit += 1
                if hit == n:
                    return self.words[j][1] + off
        raise KeyError(f"{self.sc['id']}: kata '{key}' ke-{n} tidak ada di naskah")

    def tt(self, key, n=1, off=0.0):
        return self.tl - self.w(key, n, off)

    def u(self, key, d=0.6, n=1, off=0.0, ease=esmooth):
        return ease(clamp((self.tl - self.w(key, n, off)) / max(1e-3, d)))

    def win(self, a, b, fi=0.4, fo=0.4):
        """Alpha jendela [a, b] (detik) dengan fade masuk/keluar."""
        return clamp((self.tl - a) / fi) * clamp((b - self.tl) / fo)

    def end(self):
        return self.dur


# ================================================================== teks & UI
_TXT = _cache()


def _txt_layer(text, fsz, col, name, stroke, scol):
    key = (text, round(fsz, 1), col, name, stroke, scol, round(D.SS, 3))
    lay = _TXT.get(key)
    if lay is None:
        f = font(name, fsz)
        bb = f.getbbox(text, stroke_width=int(S(stroke)))
        pad = int(S(6 + stroke))
        lay = Image.new("RGBA", (bb[2] - bb[0] + pad * 2, int(S(tlh(f) * 1.25)) + pad * 2), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        dd.text((lay.width / 2, lay.height / 2), text, font=f, fill=col + (255,), anchor="mm",
                stroke_width=int(S(stroke)), stroke_fill=(scol or (0, 0, 0)) + (255,))
        _TXT[key] = lay
        if len(_TXT) > 1500:
            _TXT.clear()
    return lay


def _paste(img, lay, X, Y, alpha):
    if alpha >= 0.995:
        img.paste(lay, (int(X), int(Y)), lay)
    elif alpha > 0.004:
        m = lay.getchannel("A").point(lambda v: int(v * alpha))
        img.paste(lay.convert("RGB"), (int(X), int(Y)), m)


BAYANG_TEKS = True          # FX 2026: bayangan lembut di bawah teks (kedalaman + keterbacaan)


def _bayang_teks(lay, key, fsz):
    return FX.bayang(lay, max(2.0, S(fsz * 0.07 + 1.5)), 0.62, key=key)


def teks(img, cx, cy, text, fsz, col=TEKS, alpha=1.0, name=FB, scale=1.0, anchor="m",
         stroke=0, scol=None, rot=0.0, bayang=None):
    """Teks ber-alpha. anchor: 'm' tengah, 'l' kiri (cx = tepi kiri), 'r' kanan.
    bayang: None = otomatis (teks >= 18 px), True/False = paksa."""
    if alpha <= 0.01 or not text or scale <= 0.02:
        return 0
    lay = _txt_layer(text, fsz, col, name, stroke, scol)
    pakai_b = BAYANG_TEKS and (bayang if bayang is not None else fsz >= 18)
    shd = None
    if pakai_b:
        shd, spad = _bayang_teks(lay, (text, round(fsz, 1), name, stroke, round(D.SS, 3)), fsz)
    if abs(scale - 1) > 0.01:
        lay = lay.resize((max(2, int(lay.width * scale)), max(2, int(lay.height * scale))), Image.BICUBIC)
        if shd is not None:
            shd = shd.resize((max(2, int(shd.width * scale)), max(2, int(shd.height * scale))), Image.BILINEAR)
            spad = spad * scale
    if abs(rot) > 0.05:
        lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
        if shd is not None:
            shd = shd.rotate(rot, resample=Image.BILINEAR, expand=True)
    wd = lay.width / D.SS
    x = {"m": cx - wd / 2, "l": cx - S(6 + stroke) / D.SS, "r": cx - wd + S(6 + stroke) / D.SS}[anchor]
    X, Y = S(x), S(cy) - lay.height / 2
    if shd is not None:
        oy = S(fsz * 0.045 + 1)
        _paste(img, shd, X + (lay.width - shd.width) / 2, Y + (lay.height - shd.height) / 2 + oy, clamp(alpha))
    _paste(img, lay, X, Y, clamp(alpha))
    return tw(text, font(name, fsz))


def lebar(text, fsz, name=FB):
    return tw(text, font(name, fsz))


def judul(img, cx, cy, text, tt, fsz=72, col=TEKS, hl=(), hlcol=EMAS, alpha=1.0, maxw=1500,
          stagger=0.07, lh=1.18, name=FB, garis=True):
    """Judul kinetik v2 (2026): tiap kata TERANGKAT dari balik garis (mask reveal) dengan motion
    blur vertikal + pegas, bayangan lembut, stabilo kata kunci menyapu dengan pendar aksen."""
    if alpha <= 0.01 or tt <= 0:
        return
    words = text.split()
    f = font(name, fsz)
    sp = tw(" ", f)
    lines, cur = [], []
    for w_ in words:
        tr = " ".join(cur + [w_])
        if cur and tw(tr, f) > maxw:
            lines.append(cur)
            cur = [w_]
        else:
            cur.append(w_)
    if cur:
        lines.append(cur)
    hls = {normw(h) for h in hl}
    lhh = tlh(f) * lh
    y0 = cy - (len(lines) - 1) * lhh / 2
    k = 0
    for li, ln in enumerate(lines):
        wl = sum(tw(w_, f) for w_ in ln) + sp * (len(ln) - 1)
        x = cx - wl / 2
        yy = y0 + li * lhh
        for w_ in ln:
            tk = tt - k * stagger
            ww = tw(w_, f)
            kunci = normw(w_) in hls
            if tk > 0:
                if kunci and garis:
                    gq = esmooth(clamp((tk - 0.22) / 0.38))
                    if gq > 0:
                        x0g, x1g = x - 12, x - 12 + (ww + 24) * gq
                        glow(img, (x0g + x1g) / 2, yy, max(40, (ww + 24) * 0.7), hlcol, 0.22 * alpha * gq)
                        D.rrect_on(img, x0g, yy - lhh * 0.31, x1g, yy + lhh * 0.35,
                                   12, mix(hlcol, SP0, 0.18), alpha * 0.94)
                        D.rrect_on(img, x0g, yy - lhh * 0.31, x1g, yy - lhh * 0.31 + 5, 3,
                                   mix(hlcol, WHITE, 0.45), alpha * 0.55)
                warna = SP0 if (kunci and garis) else (hlcol if kunci else col)
                _kata_naik(img, x + ww / 2, yy, w_, fsz, warna, alpha, name, tk, lhh)
            x += ww + sp
            k += 1


def _kata_naik(img, cx, cy, w_, fsz, col, alpha, name, tk, lhh):
    """Satu kata: naik dari bawah garis potong + blur gerak + pegas + bayangan."""
    e = FX.spring(tk, 0.55, 13.0)
    q = clamp(tk / 0.5)
    dy = (1 - e) * lhh * 0.78
    lay = _txt_layer(w_, fsz, col, name, 0, None)
    key = (w_, round(fsz, 1), name, 0, round(D.SS, 3))
    X = S(cx) - lay.width / 2
    Y = S(cy + dy) - lay.height / 2
    clip = S(cy + lhh * 0.50)                     # garis potong (bawah baris)
    vis = int(clip - Y)
    if vis <= 2:
        return
    a = alpha * min(1.0, q * 3.0)
    if q < 0.55:                                  # blur gerak vertikal saat masih meluncur
        f_ = 1 + 5 * (1 - q / 0.55)
        lay = lay.resize((lay.width, max(2, int(lay.height / f_))), Image.BILINEAR).resize(lay.size, Image.BILINEAR)
    if vis < lay.height:
        lay = lay.crop((0, 0, lay.width, vis))
    if BAYANG_TEKS and q > 0.35:
        shd, spad = _bayang_teks(_txt_layer(w_, fsz, col, name, 0, None), key, fsz)
        sa = a * clamp((q - 0.35) / 0.4)
        if vis >= lay.height and dy < 2:
            _paste(img, shd, X - spad, Y - spad + S(fsz * 0.045 + 1), sa)
    _paste(img, lay, X, Y, a)


_KACA = _cache()


KACA_CAIR = True            # FX 2026: panel LIQUID GLASS (latar diburamkan + dibiaskan + kilap tepi)


def kaca(img, x0, y0, x1, y1, alpha=1.0, acc=None, r=22, isi=KACA, pekat=0.74, sapu=None, bayang=0.42):
    """Kartu kaca. v2026 = liquid glass: latar di belakang panel diburamkan & dibiaskan, tint gelap
    (kekentalan mengikuti `pekat` supaya teks tetap terbaca), cahaya tepi atas, garis tepi bergradasi,
    bayangan lembut, bilah aksen kiri, kilau menyapu opsional (sapu 0..1)."""
    if alpha <= 0.01:
        return
    if KACA_CAIR:
        FX.kaca_cair(img, S(x0), S(y0), S(x1), S(y1), S(r), tint=isi, pekat=0.30 + 0.52 * pekat,
                     alpha=alpha, acc=acc, bayang_opa=bayang, sapu=sapu)
        return
    w_, h_ = int(S(x1 - x0)), int(S(y1 - y0))
    key = (w_, h_, acc, r, isi, pekat, round(D.SS, 3))
    lay = _KACA.get(key)
    if lay is None:
        lay = Image.new("RGBA", (w_ + 4, h_ + 4), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([2, 2, w_ + 1, h_ + 1], radius=int(S(r)), fill=isi + (int(255 * pekat),),
                             outline=(255, 255, 255, 46), width=max(1, int(S(1.6))))
        if acc:
            dd.rounded_rectangle([2, int(S(r * 0.7)), 2 + int(S(7)), h_ + 1 - int(S(r * 0.7))],
                                 radius=int(S(3)), fill=acc + (255,))
        _KACA[key] = lay
        if len(_KACA) > 300:
            _KACA.clear()
    _paste(img, lay, S(x0) - 2, S(y0) - 2, alpha)


def chip(img, cx, cy, text, alpha=1.0, acc=ORANYE, fsz=22, name=FS, fg=TEKS, anchor="m", dot=True):
    """Pil kecil gelap dengan titik aksen."""
    if alpha <= 0.01:
        return 0
    wt = lebar(text, fsz, name)
    pad = 22
    wd = wt + pad * 2 + (22 if dot else 0)
    hg = fsz * 1.16 * 1.55 + 10
    x0 = {"m": cx - wd / 2, "l": cx, "r": cx - wd}[anchor]
    kaca(img, x0, cy - hg / 2, x0 + wd, cy + hg / 2, alpha, None, r=hg / 2, pekat=0.78, bayang=0.30)
    xt = x0 + pad
    if dot:
        glow(img, xt + 6, cy, 16, acc, 0.55 * alpha)
        D.dot_on(img, xt + 6, cy, 6, acc, alpha)
        xt += 22
    teks(img, xt, cy, text, fsz, fg, alpha, name=name, anchor="l")
    return wd


_STK2 = _cache()


def _stiker_base(text, fsz, bg, fg):
    key = (text, fsz, bg, fg, round(D.SS, 3))
    v = _STK2.get(key)
    if v is None:
        f = font(FB, fsz)
        wt, ht = tw(text, f), tlh(f)
        px, py, rim = 30, 15, 5
        w_, h_ = int(S(wt + px * 2 + rim * 2)), int(S(ht + py * 2 + rim * 2))
        r = int(S(min(24, (ht + py * 2) / 2)))
        lay = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([0, 0, w_ - 1, h_ - 1], radius=r + int(S(rim)), fill=(255, 255, 255, 255))
        # isi bergradasi (atas lebih terang) = kesan cembung/mengilap
        g = np.linspace(0, 1, h_, dtype=np.float32)[:, None]
        top, bot = np.array(mix(bg, WHITE, 0.12), np.float32), np.array(mix(bg, SP0, 0.18), np.float32)
        arr = top[None, None, :] * (1 - g[..., None]) + bot[None, None, :] * g[..., None]
        arr = np.repeat(arr, w_, axis=1)
        isi = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
        m = Image.new("L", (w_, h_), 0)
        ImageDraw.Draw(m).rounded_rectangle([int(S(rim)), int(S(rim)), w_ - 1 - int(S(rim)), h_ - 1 - int(S(rim))],
                                            radius=r, fill=255)
        lay.paste(isi, (0, 0), m)
        # kilap setengah atas
        hl = Image.new("L", (w_, h_), 0)
        ImageDraw.Draw(hl).rounded_rectangle([int(S(rim + 4)), int(S(rim + 3)), w_ - 1 - int(S(rim + 4)),
                                              int(h_ * 0.46)], radius=max(2, r - int(S(4))), fill=46)
        lay.paste(Image.new("RGB", (w_, h_), WHITE), (0, 0), hl)
        dd.text((w_ / 2, h_ / 2 + S(1)), text, font=f, fill=fg + (255,), anchor="mm")
        shd = FX.bayang(lay, S(9), 0.55)
        v = (lay, shd)
        _STK2[key] = v
        if len(_STK2) > 200:
            _STK2.clear()
    return v


def stiker(img, cx, cy, text, tt, bg=MERAH, fsz=34, rot=-3.0, tg=0.0, alpha=1.0, fg=WHITE):
    """Stiker v2 (2026): isi bergradasi mengilap + tepi putih + bayangan lembut, pop PEGAS dari
    miring, kilau menyapu saat mendarat, goyang pelan."""
    if alpha <= 0.01 or tt <= 0 or not text:
        return
    lay, (shd, pad) = _stiker_base(text, fsz, bg, fg)
    e = FX.spring(tt, 0.38, 16.0)
    k = 0.35 + 0.65 * e
    ang = rot + (1 - e) * -14 + 1.3 * math.sin(tg * 2.0 + cx * 0.01)
    if 0.18 < tt < 0.95:
        lay = FX.kilau(lay, (tt - 0.18) / 0.77, 0.25, 0.6)
    L2 = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
    S2 = shd.rotate(ang, resample=Image.BILINEAR, expand=True)
    if abs(k - 1) > 0.01:
        L2 = L2.resize((max(2, int(L2.width * k)), max(2, int(L2.height * k))), Image.BICUBIC)
        S2 = S2.resize((max(2, int(S2.width * k)), max(2, int(S2.height * k))), Image.BILINEAR)
    a = alpha * clamp(tt / 0.08)
    lift = S(6 + 10 * (1 - e))                   # bayangan menjauh saat stiker "terangkat"
    _paste(img, S2, S(cx) - S2.width / 2, S(cy) - S2.height / 2 + lift, a * 0.9)
    _paste(img, L2, S(cx) - L2.width / 2, S(cy) - L2.height / 2, a)


def stempel(img, cx, cy, text, tt, col=MERAH, fsz=64, rot=-6.0, alpha=1.0):
    """Stempel menghantam: skala 2 -> 1 + bingkai."""
    if tt <= 0 or alpha <= 0.01:
        return
    q = clamp(tt / 0.28)
    sc_ = 2.0 - 1.0 * eob(q, 2.0)
    a = alpha * clamp(tt / 0.12)
    f = font(FB, fsz)
    wd, hg = tw(text, f) + 60, tlh(f) + 30
    key = ("stempel", text, fsz, col, round(D.SS, 3))
    lay = _TXT.get(key)
    if lay is None:
        lay = Image.new("RGBA", (int(S(wd + 20)), int(S(hg + 20))), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([S(10), S(10), S(wd + 10), S(hg + 10)], radius=int(S(14)),
                             outline=col + (255,), width=int(S(7)), fill=(10, 8, 20, 170))
        dd.text((lay.width / 2, lay.height / 2), text, font=f, fill=col + (255,), anchor="mm")
        _TXT[key] = lay
    l2 = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
    l2 = l2.resize((max(2, int(l2.width * sc_)), max(2, int(l2.height * sc_))), Image.BICUBIC)
    if q < 0.7:                                    # blur gerak saat menghantam
        f_ = 1 + 3 * (1 - q / 0.7)
        l2 = l2.resize((max(2, int(l2.width / f_)), max(2, int(l2.height / f_))), Image.BILINEAR).resize(
            l2.size, Image.BILINEAR)
    shd, pad = FX.bayang(l2, S(8), 0.5) if q >= 0.7 else (None, 0)
    if shd is not None:
        _paste(img, shd, S(cx) - shd.width / 2, S(cy) - shd.height / 2 + S(6), a)
    _paste(img, l2, S(cx) - l2.width / 2, S(cy) - l2.height / 2, a)
    if 0 < tt < 0.5:
        for k_ in range(10):
            an = k_ * math.pi / 5 + 0.3
            r0 = wd * 0.55 + 140 * eo(tt / 0.5)
            D.line_on(img, (cx + r0 * math.cos(an), cy + r0 * 0.5 * math.sin(an)),
                      (cx + (r0 + 40) * math.cos(an), cy + (r0 + 40) * 0.5 * math.sin(an)),
                      col, 5, alpha * (1 - tt / 0.5))


def fmt_id(v, des=0):
    if des:
        s = f"{v:,.{des}f}"
    else:
        s = f"{int(round(v)):,}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


ODOMETER = True             # FX 2026: angka bergulir per digit (odometer) + blur gerak + kilau mendarat


def angka(img, cx, cy, nilai, tt, fsz=96, col=TEKS, dur=1.1, des=0, awal=0.0, pre="", suf="",
          alpha=1.0, name=FB, sub="", subcol=REDUP, subfsz=26, ribuan=True):
    """Penghitung angka format Indonesia. v2026: digit BERGULIR seperti odometer (digit rendah
    berputar cepat dengan blur gerak, digit tinggi ikut berguling saat digit di bawahnya lewat 9),
    lalu mendarat dengan pegas + kilau + pendar. Keterangan kecil di bawah."""
    if tt <= 0 or alpha <= 0.01:
        return
    q = eo(clamp(tt / dur))
    v = awal + (nilai - awal) * q
    a = alpha * clamp(tt / 0.15)
    if ODOMETER and nilai != awal and tt < dur:
        _odometer(img, cx, cy, v, nilai, awal, tt, dur, fsz, col, a, name, des, pre, suf, ribuan)
    else:
        s_ = pre + (fmt_id(v, des) if ribuan else str(int(round(v)))) + suf
        u = (tt - dur) / 0.9 if ODOMETER else 1.0
        pop = 1.0 + 0.10 * (1 - FX.spring(max(0.0, tt - dur), 0.4, 14.0)) if 0 <= u < 1 else 1.0
        if 0 <= u < 0.85:
            # pendaratan: pegas + kilau menyapu + pendar
            glow(img, cx, cy, fsz * 2.2, col, 0.22 * a * (1 - u))
            base = _txt_layer(s_, fsz, col, name, 0, None)
            shd, spad = _bayang_teks(base, (s_, round(fsz, 1), name, 0, round(D.SS, 3)), fsz)
            lay = FX.kilau(base, u / 0.85, 0.2, 0.7)
            if abs(pop - 1) > 0.01:
                lay = lay.resize((int(lay.width * pop), int(lay.height * pop)), Image.BICUBIC)
                shd = shd.resize((int(shd.width * pop), int(shd.height * pop)), Image.BILINEAR)
            _paste(img, shd, S(cx) - shd.width / 2, S(cy) - shd.height / 2 + S(fsz * 0.045 + 1), a)
            _paste(img, lay, S(cx) - lay.width / 2, S(cy) - lay.height / 2, a)
        else:
            teks(img, cx, cy, s_, fsz, col, a, name=name, scale=pop)
    if sub:
        teks(img, cx, cy + fsz * 0.95, sub, subfsz, subcol, alpha * clamp((tt - 0.2) / 0.3), name=FS)


def _odometer(img, cx, cy, v, nilai, awal, tt, dur, fsz, col, alpha, name, des, pre, suf, ribuan):
    templ = pre + (fmt_id(nilai, des) if ribuan else str(int(round(nilai)))) + suf
    f = font(name, fsz)
    total_w = tw(templ, f)
    x = cx - total_w / 2
    # nilai tempat tiap digit (dari kanan, memperhitungkan desimal)
    body = templ[len(pre):len(templ) - len(suf)] if suf else templ[len(pre):]
    int_part = body.split(",")[0] if des else body
    n_int = sum(ch.isdigit() for ch in int_part)
    # hitung place untuk digit berurutan di body
    digit_places = []
    ci = 0
    for ch in body:
        if ch.isdigit():
            if ci < n_int:
                digit_places.append(10 ** (n_int - 1 - ci))
            else:
                digit_places.append(10 ** -(ci - n_int + 1))
            ci += 1
    kec = abs(nilai - awal) * 3.0 / max(0.2, dur) * (1 - clamp(tt / dur)) ** 2   # turunan eo
    cell = tlh(f) * 1.18
    lead_hidden = True
    di = 0
    body_start = len(pre)
    for idx, ch in enumerate(templ):
        wch = tw(ch, f)
        cxc = x + wch / 2
        in_body = body_start <= idx < body_start + len(body)
        if in_body and ch.isdigit():
            p = digit_places[di]
            di += 1
            c = v / p
            d0 = int(math.floor(c + 1e-9)) % 10
            if p >= 1 and v < p and p > 1:
                x += wch
                continue                           # nol di depan: disembunyikan
            lead_hidden = False
            low = v - math.floor(v / p) * p        # sisa di bawah tempat ini
            pl = p / 10
            if p == digit_places[-1]:
                frac = c - math.floor(c)
            else:
                frac = clamp((low - (p - pl)) / pl)
            spd = kec / p
            _digit_roll(img, cxc, cy, d0, frac, fsz, col, alpha, name, cell, clamp(spd / 30.0))
        else:
            if in_body and lead_hidden and ch in ".,":
                x += wch
                continue
            teks(img, cxc, cy, ch, fsz, col, alpha, name=name)
        x += wch


def _digit_roll(img, cx, cy, d, frac, fsz, col, alpha, name, cell, blur):
    """Satu jendela digit odometer: jendela setinggi huruf kapital, digit d turun keluar & d+1 masuk.
    Digit yang berputar sangat cepat -> satu digit buram vertikal (terbaca "berputar")."""
    lay0 = _txt_layer(str(d), fsz, col, name, 0, None)
    tinggi = fsz * 1.00                                  # jendela terlihat (digit Poppins = 0,87 fsz)
    jarak = fsz * 1.12                                   # jarak antar digit pada gulungan
    ymid = cy - fsz * 0.025                              # pusat visual glyph digit (terukur)
    Y0, Y1 = S(ymid - tinggi / 2), S(ymid + tinggi / 2)
    if blur > 0.55:
        # berputar kencang: tumpukan digit sekarang & berikutnya diburamkan kuat
        f_ = 6.0
        a1 = _txt_layer(str((d + 1) % 10), fsz, col, name, 0, None)
        for lay, off, aa in ((lay0, -frac, 1 - frac), (a1, 1 - frac, frac)):
            l2 = lay.resize((lay.width, max(2, int(lay.height / f_))), Image.BILINEAR).resize(lay.size, Image.BILINEAR)
            _paste_clip(img, l2, S(cx) - l2.width / 2, S(ymid + off * jarak * 0.35) - l2.height / 2, Y0, Y1,
                        alpha * (0.55 + 0.45 * aa))
        return
    for dd_, off in ((d, -frac), ((d + 1) % 10, 1 - frac)):
        if abs(off) >= 0.999:
            continue
        lay = _txt_layer(str(dd_), fsz, col, name, 0, None)
        if blur > 0.06:
            f_ = 1 + 5 * blur
            lay = lay.resize((lay.width, max(2, int(lay.height / f_))), Image.BILINEAR).resize(lay.size, Image.BILINEAR)
        _paste_clip(img, lay, S(cx) - lay.width / 2, S(ymid + off * jarak) - lay.height / 2, Y0, Y1, alpha)


def _paste_clip(img, lay, X, Y, Y0, Y1, alpha):
    top = max(0, int(Y0 - Y))
    bot = min(lay.height, int(Y1 - Y))
    if bot - top <= 2:
        return
    # tepi jendela dilembutkan (fade 10%) supaya digit tidak terpotong tajam
    part = lay.crop((0, top, lay.width, bot))
    hh = part.height
    fade = max(2, int((Y1 - Y0) * 0.06))
    m = part.getchannel("A")
    g = np.ones(hh, np.float32)
    ytop, ybot = Y + top, Y + bot
    for j in range(hh):
        yy = ytop + j
        g[j] = min(1.0, (yy - Y0) / fade, (Y1 - yy) / fade)
    g = np.clip(g, 0, 1)
    gm = Image.fromarray((np.repeat(g[:, None], part.width, axis=1) * 255).astype(np.uint8), "L")
    part = part.copy()
    part.putalpha(ImageChops.multiply(m, gm))
    _paste(img, part, X, Y + top, alpha)


def callout(img, p, q, text, tt, col=TEKS, acc=ORANYE, fsz=26, alpha=1.0, anchor=None, sub=""):
    """Titik di objek -> garis siku menggambar diri -> label di ujung."""
    if tt <= 0 or alpha <= 0.01:
        return
    u1 = esmooth(clamp(tt / 0.45))
    pop = FX.spring(tt, 0.4, 16.0)
    glow(img, p[0], p[1], 34, acc, 0.45 * alpha * min(1.0, pop))
    D.dot_on(img, p[0], p[1], 7 * pop + 0.01, acc, alpha)
    D.dot_on(img, p[0], p[1], 3 * pop + 0.01, WHITE, alpha * 0.9)
    D.ring_on(img, p[0], p[1], 7 + 18 * clamp(tt / 0.6), acc, 2.5, alpha * (1 - clamp(tt / 0.6)))
    if tt > 0.8:                                   # denyut berulang (sonar) supaya titik terasa hidup
        ph = ((tt - 0.8) % 1.8) / 1.8
        D.ring_on(img, p[0], p[1], 8 + 22 * eo(ph), acc, 2.0, alpha * 0.6 * (1 - ph))
    mid = (q[0], p[1]) if abs(q[1] - p[1]) < 4 else (p[0] + (q[0] - p[0]) * 0.35, q[1])
    pts = [p, mid, q]
    L1 = math.hypot(mid[0] - p[0], mid[1] - p[1])
    L2 = math.hypot(q[0] - mid[0], q[1] - mid[1])
    Ld = (L1 + L2) * u1
    if Ld <= L1:
        f_ = Ld / max(1, L1)
        pts = [p, (p[0] + (mid[0] - p[0]) * f_, p[1] + (mid[1] - p[1]) * f_)]
    else:
        f_ = (Ld - L1) / max(1, L2)
        pts = [p, mid, (mid[0] + (q[0] - mid[0]) * f_, mid[1] + (q[1] - mid[1]) * f_)]
    M._pline(img, pts, acc, 9, alpha * 0.16)
    M._pline(img, pts, acc, 3, alpha * 0.95)
    if 0.02 < u1 < 0.999:
        glow(img, pts[-1][0], pts[-1][1], 22, mix(acc, WHITE, 0.4), 0.7 * alpha)
    if u1 >= 0.98:
        ta = clamp((tt - 0.42) / 0.25)
        anc = anchor or ("l" if q[0] >= p[0] else "r")
        dx = 12 if anc == "l" else -12
        teks(img, q[0] + dx, q[1] - (12 if sub else 0), text, fsz, col, alpha * ta, name=FB, anchor=anc)
        if sub:
            teks(img, q[0] + dx, q[1] + fsz * 0.9, sub, fsz * 0.72, REDUP, alpha * ta, name=FS, anchor=anc)


def panah(img, p0, p1, col, width=6, alpha=1.0, prog=1.0, head=20):
    """Panah lurus yang tumbuh (prog 0..1)."""
    if alpha <= 0.01 or prog <= 0.01:
        return
    x = p0[0] + (p1[0] - p0[0]) * prog
    y = p0[1] + (p1[1] - p0[1]) * prog
    D.line_on(img, p0, (x, y), col, width * 2.6, alpha * 0.15)
    D.line_on(img, p0, (x, y), col, width, alpha)
    an = math.atan2(y - p0[1], x - p0[0])
    hd = head * min(1.0, prog * 2)
    pts = [(x + math.cos(an) * hd * 0.5, y + math.sin(an) * hd * 0.5),
           (x - math.cos(an - 0.55) * hd, y - math.sin(an - 0.55) * hd),
           (x - math.cos(an + 0.55) * hd, y - math.sin(an + 0.55) * hd)]
    D.poly_on(img, pts, col, alpha)


def centang(img, cx, cy, r, tt, col=HIJAU, alpha=1.0, silang=False):
    """Centang / silang digambar progresif di dalam lingkaran."""
    if tt <= 0 or alpha <= 0.01:
        return
    pop = eob(clamp(tt / 0.3), 2.0)
    D.dot_on(img, cx, cy, r * pop, mix(col, SP0, 0.15), alpha)
    q = esmooth(clamp((tt - 0.12) / 0.35))
    if silang:
        a = r * 0.42
        D.line_on(img, (cx - a, cy - a), (cx - a + 2 * a * min(1, q * 2), cy - a + 2 * a * min(1, q * 2)),
                  WHITE, r * 0.2, alpha)
        if q > 0.5:
            k = (q - 0.5) * 2
            D.line_on(img, (cx + a, cy - a), (cx + a - 2 * a * k, cy - a + 2 * a * k), WHITE, r * 0.2, alpha)
    else:
        p1, p2, p3 = (cx - r * 0.45, cy + r * 0.02), (cx - r * 0.12, cy + r * 0.35), (cx + r * 0.5, cy - r * 0.36)
        if q < 0.4:
            k = q / 0.4
            M._pline(img, [p1, (p1[0] + (p2[0] - p1[0]) * k, p1[1] + (p2[1] - p1[1]) * k)], WHITE, r * 0.2, alpha)
        else:
            k = (q - 0.4) / 0.6
            M._pline(img, [p1, p2, (p2[0] + (p3[0] - p2[0]) * k, p2[1] + (p3[1] - p2[1]) * k)], WHITE, r * 0.2, alpha)


def partikel(img, cx, cy, tt, col, alpha=1.0, n=14, jarak=140, seed=3):
    M._partikel11(img, cx, cy, tt, col, alpha, n=n, jarak=jarak, seed=seed)


_GW = _cache()


def glow(img, cx, cy, r, col, alpha):
    """Cahaya lembut, masker radial numpy turun mulus ke 0 di tepi (versi mesin_v11 punya tepi
    kotak samar pada radius besar)."""
    if alpha <= 0.01 or r <= 2:
        return
    key = (int(r), col, round(D.SS, 3))
    spr = _GW.get(key)
    if spr is None:
        n = max(8, int(S(int(r)) * 2))
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        c = (n - 1) / 2.0
        rr = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
        m = (np.clip(1 - rr, 0, 1) ** 2.2 * 255).astype(np.uint8)
        spr = (Image.new("RGB", (n, n), col), Image.fromarray(m, "L"))
        if len(_GW) > 400:
            _GW.clear()
        _GW[key] = spr
    rgb, m = spr
    a = m if alpha >= 0.995 else m.point(lambda v: int(v * clamp(alpha)))
    img.paste(rgb, (int(S(cx) - rgb.width / 2), int(S(cy) - rgb.height / 2)), a)


def garis_ukur(img, x0, x1, y, text, tt, col=TEKS, alpha=1.0, fsz=24, tick=16):
    """Garis ukur horizontal |<---->| yang membentang dari tengah + label."""
    if tt <= 0 or alpha <= 0.01:
        return
    q = esmooth(clamp(tt / 0.6))
    cx = (x0 + x1) / 2
    a0, a1 = cx - (cx - x0) * q, cx + (x1 - cx) * q
    D.line_on(img, (a0, y), (a1, y), col, 3, alpha)
    D.line_on(img, (a0, y - tick), (a0, y + tick), col, 3, alpha)
    D.line_on(img, (a1, y - tick), (a1, y + tick), col, 3, alpha)
    if q > 0.9:
        teks(img, cx, y - fsz * 1.2, text, fsz, col, alpha * clamp((tt - 0.5) / 0.3), name=FB)


# ================================================================== sprite util
def _put_c(img, spr, cx, cy, alpha=1.0):
    _paste(img, spr, S(cx) - spr.width / 2, S(cy) - spr.height / 2, clamp(alpha))


_RS = _cache()


def _resized(key, spr, k):
    kq = round(k, 3)
    kk = (key, kq, round(D.SS, 3))
    r = _RS.get(kk)
    if r is None:
        if abs(kq - 1) < 0.002:
            r = spr
        else:
            r = spr.resize((max(2, int(spr.width * kq)), max(2, int(spr.height * kq))), Image.BICUBIC)
        if len(_RS) > 220:
            _RS.clear()
        _RS[kk] = r
    return r


def _radial(n, stops):
    """Sprite radial RGBA n x n dari daftar (r_norm, (r,g,b,a))."""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2.0
    rr = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    out = np.zeros((n, n, 4), np.float32)
    xs = [s[0] for s in stops]
    for ch in range(4):
        out[..., ch] = np.interp(rr, xs, [s[1][ch] for s in stops])
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


# ================================================================== latar antariksa
_BG = _cache()


def _bg_parts():
    key = round(D.SS, 3)
    if key in _BG:
        return _BG[key]
    w, h = int(S(W)), int(S(H))
    g = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top, bot = np.array(SP0, np.float32), np.array(SP1, np.float32)
    arr = top + (bot - top) * g ** 1.2
    base = Image.fromarray(np.broadcast_to(arr, (h, w, 3)).astype(np.uint8), "RGB")
    for cx, cy, r, col, a in [(260, 180, 760, (64, 34, 110), 0.42), (1700, 900, 860, (22, 52, 110), 0.40),
                              (1150, 60, 520, (100, 40, 86), 0.20), (700, 1000, 600, (40, 30, 90), 0.25)]:
        glow(base, cx, cy, r, col, a)
    rng = random.Random(7)
    far = Image.new("RGBA", (w * 2, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(far)
    for _ in range(820):
        x, y = rng.random() * w, rng.random() * h
        r = S(rng.uniform(0.5, 1.25))
        c = rng.choice([(255, 255, 255), (205, 222, 255), (255, 236, 214)])
        a = rng.randint(50, 190)
        for dx in (0, w):
            d.ellipse([x + dx - r, y - r, x + dx + r, y + r], fill=c + (a,))
    near = Image.new("RGBA", (w * 2, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(near)
    for _ in range(140):
        x, y = rng.random() * w, rng.random() * h
        r = S(rng.uniform(1.2, 2.3))
        c = rng.choice([(255, 255, 255), (190, 215, 255), (255, 226, 196)])
        for dx in (0, w):
            d.ellipse([x + dx - r * 2.6, y - r * 2.6, x + dx + r * 2.6, y + r * 2.6], fill=c + (26,))
            d.ellipse([x + dx - r, y - r, x + dx + r, y + r], fill=c + (235,))
    twk = [(rng.random() * W, rng.random() * H, rng.uniform(5, 11), rng.random() * 6.28, rng.uniform(0.6, 1.6))
           for _ in range(26)]
    _BG[key] = (base, far, near, twk)
    return _BG[key]


def latar(t, drift=1.0, bintang=1.0):
    base, far, near, twk = _bg_parts()
    img = base.copy()
    w, h = base.size
    if bintang > 0.01:
        for lay, v in ((far, 5.0), (near, 13.0)):
            ox = int(S(t * v * drift)) % w
            c = lay.crop((ox, 0, ox + w, h))
            if bintang < 0.99:
                c.putalpha(c.getchannel("A").point(lambda a: int(a * bintang)))
            img.paste(c, (0, 0), c)
        for x, y, r, ph, sp in twk:
            a = 0.5 + 0.5 * math.sin(t * sp + ph)
            xx = (x - t * 13.0 * drift) % W
            if a > 0.35:
                D.star4(img, xx, y, r * (0.6 + 0.5 * a), (235, 240, 255), bintang * (a - 0.3))
    return img


# ================================================================== LUBANG HITAM
_BH = _cache()
BH_R0 = 170          # jari-jari master (px logis)


def _bh_parts(tilt):
    key = (round(D.SS, 3), round(tilt, 3))
    if key in _BH:
        return _BH[key]
    R = S(BH_R0)
    Wd, Hd = int(R * 6.4), int(R * 4.4)
    cx, cy = Wd / 2, Hd / 2
    rng = random.Random(5)

    def warna(f):
        # 0 = tepi luar (merah gelap, transparan) -> 0,6 jingga -> 1 kuning pucat
        st = [(0.0, (110, 22, 4, 0)), (0.35, (215, 80, 18, 150)), (0.7, (255, 160, 60, 235)),
              (0.9, (255, 214, 140, 255)), (1.0, (255, 242, 205, 255))]
        for (f0, c0), (f1, c1) in zip(st[:-1], st[1:]):
            if f <= f1:
                u = (f - f0) / (f1 - f0)
                return tuple(int(c0[j] + (c1[j] - c0[j]) * u) for j in range(4))
        return st[-1][1]

    # piringan akresi + tekstur alur
    disk = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disk)
    n = 90
    for k in range(n):
        f = k / (n - 1)
        rx = R * (3.0 - 1.92 * f)
        dd.ellipse([cx - rx, cy - rx * tilt, cx + rx, cy + rx * tilt], fill=warna(f))
    for _ in range(120):
        rx = R * rng.uniform(1.15, 2.8)
        a0 = rng.uniform(0, 360)
        terang = rng.random() < 0.8
        dd.arc([cx - rx, cy - rx * tilt, cx + rx, cy + rx * tilt], a0, a0 + rng.uniform(25, 110),
               fill=(255, 226, 170, rng.randint(40, 110)) if terang else (170, 60, 14, rng.randint(25, 60)),
               width=max(1, int(R * rng.uniform(0.012, 0.03))))
    rin = R * 1.08
    dd.ellipse([cx - rin, cy - rin * tilt, cx + rin, cy + rin * tilt], fill=(0, 0, 0, 0))
    disk = disk.filter(ImageFilter.GaussianBlur(R * 0.028))
    a = np.asarray(disk).astype(np.float32)
    gx = np.linspace(1.35, 0.72, Wd, dtype=np.float32)[None, :, None]     # Doppler: kiri lebih terang
    a[..., :3] = np.clip(a[..., :3] * gx, 0, 255)
    ym = np.clip((np.arange(Hd, dtype=np.float32)[:, None] - cy) / max(1.0, R * 0.03) + 0.5, 0, 1)
    xm = np.clip((R * 1.2 - np.abs(np.arange(Wd, dtype=np.float32)[None, :] - cx)) / max(1.0, R * 0.12), 0, 1)
    fr = a.copy()
    fr[..., 3] *= ym * xm          # hanya bagian depan yang menutupi bayangan
    back = Image.fromarray(a.astype(np.uint8), "RGBA")
    front = Image.fromarray(fr.astype(np.uint8), "RGBA")
    # cincin lensa: busur terang tegas dekat bayangan, memudar ke luar; atas lebih tebal
    lens = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lens)
    N = 60
    for k in range(N):
        f = k / (N - 1)
        ro = R * (1.5 - 0.46 * f)
        c = warna(min(1.0, 0.45 + 0.6 * f))
        c = c[:3] + (int(255 * f ** 2.2),)
        dl.ellipse([cx - ro * 0.99, cy - ro - R * 0.12 * (1 - f), cx + ro * 0.99, cy + ro * 0.88], fill=c)
    dl.ellipse([cx - R * 1.03, cy - R * 1.03, cx + R * 1.03, cy + R * 1.03], fill=(0, 0, 0, 0))
    lens = lens.filter(ImageFilter.GaussianBlur(R * 0.012))
    la = np.asarray(lens).astype(np.float32)
    yy = np.linspace(0, 1, Hd, dtype=np.float32)[:, None]
    la[..., 3] *= np.clip(1.2 - 0.62 * yy, 0.45, 1.0)
    la[..., :3] = np.clip(la[..., :3] * np.linspace(1.25, 0.8, Wd, dtype=np.float32)[None, :, None], 0, 255)
    lens = Image.fromarray(la.astype(np.uint8), "RGBA")
    # bayangan + cincin foton
    shadow = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    ds.ellipse([cx - R * 1.06, cy - R * 1.06, cx + R * 1.06, cy + R * 1.06], fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(R * 0.05))
    ds = ImageDraw.Draw(shadow)
    ds.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(0, 0, 0, 255))
    photon = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    dp = ImageDraw.Draw(photon)
    dp.ellipse([cx - R * 1.03, cy - R * 1.03, cx + R * 1.03, cy + R * 1.03],
               outline=(255, 246, 225, 255), width=max(2, int(R * 0.03)))
    photon = photon.filter(ImageFilter.GaussianBlur(R * 0.008))
    _BH[key] = {"back": back, "lens": lens, "shadow": shadow, "photon": photon, "front": front}
    return _BH[key]


def lubang_hitam(img, cx, cy, r, tg=0.0, alpha=1.0, disk=1.0, lens=1.0, glow_a=1.0, tilt=0.22,
                 photon=1.0, gumpal=1.0, spin=1.0):
    """Lubang hitam gaya sinematik. r = jari-jari bayangan (px logis)."""
    if alpha <= 0.01 or r < 2:
        return
    P = _bh_parts(tilt)
    k = r / BH_R0
    kt = ("bh", round(tilt, 3))
    if glow_a > 0.01 and disk > 0.01:
        glow(img, cx, cy, r * 3.4, (255, 130, 40), 0.22 * glow_a * alpha * disk)
        glow(img, cx, cy, r * 1.9, (255, 190, 110), 0.12 * glow_a * alpha * disk)

    def put(name, a):
        if a > 0.01:
            _put_c(img, _resized(kt + (name,), P[name], k), cx, cy, a)

    def gumpalan(depan):
        if gumpal <= 0.01 or disk <= 0.01:
            return
        for j in range(18):
            th = j * 2.39996 + tg * spin * (1.4 - 0.05 * j)
            rr = r * (1.4 + 1.25 * ((j * 37) % 11) / 10.0)
            x, y = cx + rr * math.cos(th), cy + rr * tilt * math.sin(th)
            dep = math.sin(th) > 0
            if dep != depan:
                continue
            if not dep and abs(x - cx) < r * 1.05:
                continue
            terang = 0.55 + 0.45 * (0.5 - 0.5 * math.cos(th))   # kiri lebih terang
            D.dot_on(img, x, y, max(1.2, r * 0.022), (255, 240, 205), alpha * disk * gumpal * terang * 0.85)

    put("back", alpha * disk)
    gumpalan(False)
    put("lens", alpha * lens * max(disk, 0.0))
    put("shadow", alpha)
    put("photon", alpha * photon)
    put("front", alpha * disk)
    gumpalan(True)


def lubang_polos(img, cx, cy, r, alpha=1.0, tepi=SIAN, tepi_a=0.0, dash=False):
    """Lubang hitam tampak diagram (bayangan + horizon garis putus)."""
    if alpha <= 0.01:
        return
    glow(img, cx, cy, r * 1.8, (60, 40, 110), 0.35 * alpha)
    D.dot_on(img, cx, cy, r, (0, 0, 0), alpha)
    if tepi_a > 0.01:
        if dash:
            n = max(24, int(r / 6))
            for k in range(n):
                a0 = k * 2 * math.pi / n
                a1 = a0 + math.pi / n
                D.line_on(img, (cx + r * math.cos(a0), cy + r * math.sin(a0)),
                          (cx + r * math.cos(a1), cy + r * math.sin(a1)), tepi, 4, alpha * tepi_a)
        else:
            D.ring_on(img, cx, cy, r, tepi, 4, alpha * tepi_a)


# ================================================================== bintang / matahari
_BT = _cache()


def bintang(img, cx, cy, r, col=(255, 200, 110), alpha=1.0, tg=0.0, korona=1.0):
    if alpha <= 0.01 or r < 1:
        return
    key = (col, round(D.SS, 3))
    spr = _BT.get(key)
    if spr is None:
        n = int(S(400))
        spr = _radial(n, [(0.0, (255, 255, 245, 255)), (0.35, mix((255, 255, 240), col, 0.45) + (255,)),
                          (0.9, col + (255,)), (0.985, mix(col, (120, 40, 10), 0.35) + (255,)),
                          (1.0, mix(col, (120, 40, 10), 0.5) + (0,))])
        _BT[key] = spr
    if korona > 0.01:
        glow(img, cx, cy, r * 3.0, col, 0.38 * alpha * korona)
        glow(img, cx, cy, r * 1.6, mix(col, WHITE, 0.3), 0.30 * alpha * korona)
    k = r / 200.0
    pul = 1 + 0.012 * math.sin(tg * 3.1)
    _put_c(img, _resized(("bt", col), spr, k * pul), cx, cy, alpha)


# ================================================================== bumi
_BM = _cache()


def bumi(img, cx, cy, r, alpha=1.0, atmos=1.0):
    if alpha <= 0.01 or r < 1:
        return
    key = round(D.SS, 3)
    spr = _BM.get(key)
    if spr is None:
        n = int(S(400))
        c = n / 2
        lay = _radial(n, [(0.0, (70, 150, 230, 255)), (0.8, (34, 96, 190, 255)), (0.985, (20, 60, 150, 255)),
                          (1.0, (20, 60, 150, 0))])
        land = Image.new("L", (n, n), 0)
        dl = ImageDraw.Draw(land)
        rng = random.Random(21)
        for bx, by, s in [(0.34, 0.33, 0.20), (0.40, 0.55, 0.15), (0.66, 0.40, 0.17), (0.62, 0.70, 0.12),
                          (0.25, 0.70, 0.08), (0.78, 0.25, 0.08)]:
            for _ in range(9):
                x = (bx + rng.uniform(-s, s) * 0.8) * n
                y = (by + rng.uniform(-s, s) * 0.8) * n
                rr = s * n * rng.uniform(0.25, 0.55)
                dl.ellipse([x - rr, y - rr * 0.8, x + rr, y + rr * 0.8], fill=255)
        land = land.filter(ImageFilter.GaussianBlur(n * 0.006))
        green = Image.new("RGBA", (n, n), (76, 164, 96, 255))
        m = ImageChops.multiply(land, lay.getchannel("A"))
        lay.paste(green, (0, 0), m)
        cl = Image.new("L", (n, n), 0)
        dc = ImageDraw.Draw(cl)
        for _ in range(26):
            x, y = rng.uniform(0.1, 0.9) * n, rng.uniform(0.1, 0.9) * n
            dc.ellipse([x - n * 0.08, y - n * 0.015, x + n * 0.08, y + n * 0.015], fill=150)
        cl = ImageChops.multiply(cl.filter(ImageFilter.GaussianBlur(n * 0.01)), lay.getchannel("A"))
        lay.paste(Image.new("RGBA", (n, n), (240, 246, 255, 255)), (0, 0), cl)
        # terminator: sisi kanan-bawah lebih gelap
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        sh = np.clip(1.15 - ((xx - c * 0.55) * 0.8 + (yy - c * 0.6) * 0.5) / n * 1.4, 0.18, 1.0)
        a = np.asarray(lay).astype(np.float32)
        a[..., :3] *= sh[..., None]
        spr = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        _BM[key] = spr
    if atmos > 0.01:
        glow(img, cx, cy, r * 1.35, (90, 170, 255), 0.35 * alpha * atmos)
    _put_c(img, _resized(("bumi",), spr, r / 200.0), cx, cy, alpha)
    if atmos > 0.01:
        D.ring_on(img, cx, cy, r * 1.01, (140, 200, 255), max(1.5, r * 0.02), 0.5 * alpha * atmos)


# ================================================================== astronot
_AS = _cache()


def _astro_master():
    key = round(D.SS, 3)
    if key in _AS:
        return _AS[key]
    s = D.SS * 1.6
    w_, h_ = int(200 * s), int(270 * s)
    lay = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    P = lambda *v: [x * s for x in v]   # noqa: E731
    put = (238, 240, 246, 255)
    abu = (170, 178, 196, 255)
    gel = (60, 66, 90, 255)
    d.rounded_rectangle(P(52, 92, 148, 190), radius=18 * s, fill=abu)                 # ransel
    d.rounded_rectangle(P(60, 96, 140, 196), radius=26 * s, fill=put, outline=gel, width=int(3 * s))  # badan
    d.rounded_rectangle(P(26, 104, 62, 176), radius=16 * s, fill=put, outline=gel, width=int(3 * s))  # lengan kiri
    d.rounded_rectangle(P(138, 104, 174, 176), radius=16 * s, fill=put, outline=gel, width=int(3 * s))  # lengan kanan
    d.rounded_rectangle(P(66, 184, 98, 256), radius=14 * s, fill=put, outline=gel, width=int(3 * s))   # kaki
    d.rounded_rectangle(P(102, 184, 134, 256), radius=14 * s, fill=put, outline=gel, width=int(3 * s))
    d.rounded_rectangle(P(62, 238, 100, 262), radius=10 * s, fill=abu)                  # sepatu
    d.rounded_rectangle(P(100, 238, 138, 262), radius=10 * s, fill=abu)
    d.rounded_rectangle(P(78, 128, 122, 152), radius=6 * s, fill=(242, 153, 74, 255))  # panel dada
    d.ellipse(P(84, 134, 94, 144), fill=(86, 204, 242, 255))
    d.ellipse(P(46, 12, 154, 112), fill=put, outline=gel, width=int(3 * s))             # helm
    d.ellipse(P(62, 32, 138, 94), fill=(30, 40, 78, 255))                               # visor
    d.ellipse(P(72, 40, 100, 58), fill=(140, 190, 255, 200))                            # kilau
    d.ellipse(P(108, 70, 120, 80), fill=(140, 190, 255, 120))
    _AS[key] = lay
    return lay


def astronot(img, cx, cy, h=160, alpha=1.0, rot=0.0, regang=1.0, tipis=None, merah=0.0):
    """Astronot: regang = faktor panjang (spagetifikasi), merah = pergeseran merah 0..1."""
    if alpha <= 0.01 or h < 4:
        return
    m = _astro_master()
    k = h / 270.0 * D.SS / (D.SS * 1.6)
    tip = tipis if tipis is not None else 1.0 / math.sqrt(max(1.0, regang))
    wd, hg = max(2, int(m.width * k * tip)), max(2, int(m.height * k * regang))
    spr = m.resize((wd, hg), Image.BICUBIC)
    if merah > 0.01:
        rgb = spr.convert("RGB")
        tint = Image.new("RGB", spr.size, (200, 30, 20))
        rgb = Image.blend(rgb, ImageChops.multiply(rgb, tint), clamp(merah) * 0.85)
        rgb.putalpha(spr.getchannel("A"))
        spr = rgb
    if abs(rot) > 0.1:
        spr = spr.rotate(rot, resample=Image.BICUBIC, expand=True)
    _put_c(img, spr, cx, cy, alpha)


# ================================================================== roket
_RK = _cache()


def roket(img, cx, cy, h=150, ang=0.0, alpha=1.0, api=1.0, tg=0.0):
    """Roket; ang derajat searah jarum jam dari atas (0 = ke atas, 90 = ke kanan)."""
    if alpha <= 0.01:
        return
    key = round(D.SS, 3)
    m = _RK.get(key)
    if m is None:
        s = D.SS * 1.6
        w_, h_ = int(120 * s), int(300 * s)
        m = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
        d = ImageDraw.Draw(m)
        P = lambda *v: [x * s for x in v]   # noqa: E731
        d.polygon(P(60, 10, 88, 60, 32, 60), fill=(235, 87, 87, 255))                  # hidung
        d.rounded_rectangle(P(32, 52, 88, 170), radius=16 * s, fill=(240, 242, 248, 255))
        d.rectangle(P(32, 56, 88, 64), fill=(235, 87, 87, 255))
        d.ellipse(P(46, 78, 74, 106), fill=(40, 60, 110, 255), outline=(170, 178, 196, 255), width=int(4 * s))
        d.ellipse(P(52, 84, 62, 94), fill=(150, 200, 255, 220))
        d.polygon(P(32, 120, 8, 176, 32, 160), fill=(235, 87, 87, 255))                # sirip
        d.polygon(P(88, 120, 112, 176, 88, 160), fill=(235, 87, 87, 255))
        d.rectangle(P(44, 168, 76, 180), fill=(120, 128, 150, 255))
        _RK[key] = m
    k = h / 300.0 / 1.6
    ms = m.resize((max(2, int(m.width * k)), max(2, int(m.height * k))), Image.BICUBIC)
    oy = ms.height // 2
    lay = Image.new("RGBA", (ms.width, ms.height * 2), (0, 0, 0, 0))
    if api > 0.01:
        d = ImageDraw.Draw(lay)
        fl = 1.0 + 0.18 * math.sin(tg * 37) + 0.1 * math.sin(tg * 23)
        bx = ms.width / 2
        by = ms.height * 0.585 + oy
        L = ms.height * 0.55 * api * fl
        d.polygon([(bx - ms.width * 0.13, by), (bx + ms.width * 0.13, by), (bx, by + L)], fill=(255, 170, 60, 230))
        d.polygon([(bx - ms.width * 0.07, by), (bx + ms.width * 0.07, by), (bx, by + L * 0.62)], fill=(255, 245, 200, 255))
    lay.paste(ms, (0, oy), ms)
    if abs(ang) > 0.1:
        lay = lay.rotate(-ang, resample=Image.BICUBIC, expand=True)
    _put_c(img, lay, cx, cy, alpha)


# ================================================================== jam
def jam(img, cx, cy, r, detik, alpha=1.0, col=TEKS, acc=ORANYE, glow_a=0.0):
    if alpha <= 0.01:
        return
    if glow_a > 0.01:
        glow(img, cx, cy, r * 1.8, acc, 0.3 * glow_a * alpha)
    D.dot_on(img, cx, cy, r, KACA, alpha)
    D.ring_on(img, cx, cy, r, col, max(2, r * 0.06), alpha)
    for k in range(12):
        a = k * math.pi / 6
        r0 = r * (0.76 if k % 3 == 0 else 0.84)
        D.line_on(img, (cx + r0 * math.sin(a), cy - r0 * math.cos(a)),
                  (cx + r * 0.92 * math.sin(a), cy - r * 0.92 * math.cos(a)), col, max(1.5, r * 0.035), alpha)
    am = detik / 600.0 * 2 * math.pi
    D.line_on(img, (cx, cy), (cx + r * 0.55 * math.sin(am), cy - r * 0.55 * math.cos(am)), col, max(2, r * 0.07), alpha)
    asec = math.floor(detik) / 60.0 * 2 * math.pi
    D.line_on(img, (cx, cy), (cx + r * 0.8 * math.sin(asec), cy - r * 0.8 * math.cos(asec)), acc, max(1.5, r * 0.035), alpha)
    D.dot_on(img, cx, cy, max(2, r * 0.07), acc, alpha)


# ================================================================== galaksi spiral
_GX = _cache()


def galaksi(img, cx, cy, r, tg=0.0, alpha=1.0, tilt=0.5, rot=0.0, spin=0.0):
    if alpha <= 0.01:
        return
    key = round(D.SS, 3)
    m = _GX.get(key)
    if m is None:
        n = int(S(700))
        c = n / 2
        m = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        d = ImageDraw.Draw(m)
        rng = random.Random(9)
        for arm in range(2):
            for _ in range(2600):
                u = rng.random() ** 0.8
                th = u * 3.6 * math.pi + arm * math.pi
                rr = c * (0.08 + 0.9 * u)
                jit = c * 0.07 * (1 - u * 0.5)
                x = c + rr * math.cos(th) + rng.gauss(0, jit)
                y = c + rr * math.sin(th) + rng.gauss(0, jit)
                pr = rng.random()
                col = (255, 150, 200) if pr < 0.05 else ((170, 200, 255) if pr < 0.6 else (255, 240, 220))
                s_ = S(rng.uniform(0.6, 1.8))
                d.ellipse([x - s_, y - s_, x + s_, y + s_], fill=col + (rng.randint(80, 220),))
        for _ in range(1500):
            rr = abs(rng.gauss(0, c * 0.16))
            th = rng.random() * 6.283
            x, y = c + rr * math.cos(th), c + rr * math.sin(th)
            s_ = S(rng.uniform(0.6, 1.5))
            d.ellipse([x - s_, y - s_, x + s_, y + s_], fill=(255, 230, 190, rng.randint(90, 230)))
        m = m.filter(ImageFilter.GaussianBlur(S(0.5)))
        core = _radial(int(n * 0.5), [(0, (255, 240, 210, 230)), (0.35, (255, 200, 140, 120)), (1, (255, 160, 90, 0))])
        m.alpha_composite(core, (int(c - core.width / 2), int(c - core.height / 2)))
        _GX[key] = m
    ang = rot + tg * spin
    spr = m.rotate(ang, resample=Image.BICUBIC) if abs(ang) > 0.05 else m
    k = r / 350.0
    spr = spr.resize((max(2, int(spr.width * k)), max(2, int(spr.height * k * tilt))), Image.BICUBIC)
    _put_c(img, spr, cx, cy, alpha)


# ================================================================== parabola radio & mata
def parabola(img, cx, cy, s=1.0, alpha=1.0, col=TEKS, ang=-30.0):
    if alpha <= 0.01:
        return
    D.poly_on(img, [(cx - 16 * s, cy + 40 * s), (cx + 16 * s, cy + 40 * s), (cx + 5 * s, cy), (cx - 5 * s, cy)],
              mix(col, SP0, 0.35), alpha)
    pts = []
    for k in range(21):
        u = -1 + k / 10.0
        x, y = u * 38 * s, -(u * u) * 20 * s + 6 * s
        a = math.radians(ang)
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy - 8 * s + x * math.sin(a) + y * math.cos(a)))
    D.poly_on(img, pts, col, alpha)
    tip = (cx + 30 * s * math.sin(math.radians(ang)), cy - 8 * s - 30 * s * math.cos(math.radians(ang)))
    D.line_on(img, (cx, cy - 6 * s), tip, col, 3 * s, alpha)
    D.dot_on(img, tip[0], tip[1], 5 * s, ORANYE, alpha)


def mata(img, cx, cy, r, alpha=1.0, tg=0.0, col=TEKS):
    if alpha <= 0.01:
        return
    pts_a = [(cx - r * 1.6 + r * 3.2 * k / 20, cy - r * 0.9 * math.sin(math.pi * k / 20)) for k in range(21)]
    pts_b = [(cx + r * 1.6 - r * 3.2 * k / 20, cy + r * 0.9 * math.sin(math.pi * k / 20)) for k in range(21)]
    D.poly_on(img, pts_a + pts_b, col, alpha)
    D.dot_on(img, cx, cy, r * 0.62, (40, 120, 200), alpha)
    D.dot_on(img, cx, cy, r * 0.3, SP0, alpha)
    D.dot_on(img, cx - r * 0.2, cy - r * 0.2, r * 0.12, WHITE, alpha)


# ================================================================== HUD, kartu bab, finishing
def hud(img, tl_data, i, t, acc, tl):
    """Digambar pada kanvas final (SS=1): brand, chip bab, bilah progres bersegmen."""
    scenes = tl_data["scenes"]
    total = tl_data["total"]
    chip(img, 44, 46, "KlikTahu", 0.88, acc=ORANYE, fsz=19, anchor="l")
    if i > 0:
        a = clamp((tl - 3.3) / 0.5) * clamp((scenes[i]["dur"] - 0.4 - tl) / 0.3)
        if a > 0.01:
            chip(img, W - 44, 46, f"{i:02d}  ·  {scenes[i].get('bab', '').upper()}", 0.85 * a, acc=acc, fsz=17,
                 anchor="r", name=FS)
    y = H - 9
    x0, x1 = 0, W
    for j, sc in enumerate(scenes):
        a0 = x0 + (x1 - x0) * sc["start"] / total + (2 if j else 0)
        a1 = x0 + (x1 - x0) * (sc["start"] + sc["dur"]) / total - 2
        D.rrect_on(img, a0, y - 3, a1, y + 3, 2, (255, 255, 255), 0.16)
        f = clamp((t - sc["start"]) / sc["dur"])
        if f > 0:
            ac = hexc(sc.get("accent", "#F2994A"))
            D.rrect_on(img, a0, y - 3, a0 + (a1 - a0) * f, y + 3, 2, ac, 0.9)
            if 0 < f < 1:                          # kepala progres bercahaya
                hx = a0 + (a1 - a0) * f
                glow(img, hx, y, 26, ac, 0.9)
                D.dot_on(img, hx, y, 4.5, mix(ac, WHITE, 0.55), 1.0)


_KB = _cache()


def _angka_garis(text, fsz, col):
    """Angka raksasa bergaya GARIS (outline) dengan isi gradasi tipis - ter-cache."""
    key = (text, fsz, col, round(D.SS, 3))
    v = _KB.get(key)
    if v is None:
        f = font(FB, fsz)
        st = max(2, int(S(3)))
        bb = f.getbbox(text, stroke_width=st)
        pad = int(S(20))
        w_, h_ = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
        full = Image.new("L", (w_, h_), 0)
        ImageDraw.Draw(full).text((w_ / 2, h_ / 2), text, font=f, fill=255, anchor="mm", stroke_width=st,
                                  stroke_fill=255)
        inner = Image.new("L", (w_, h_), 0)
        ImageDraw.Draw(inner).text((w_ / 2, h_ / 2), text, font=f, fill=255, anchor="mm")
        garis = ImageChops.subtract(full, inner)
        g = np.linspace(0.30, 0.02, h_, dtype=np.float32)[:, None]
        isi = ImageChops.multiply(inner, Image.fromarray((np.repeat(g, w_, axis=1) * 255).astype(np.uint8), "L"))
        a_ = ImageChops.lighter(garis, isi)
        lay = Image.new("RGBA", (w_, h_), col + (0,))
        lay.putalpha(a_)
        v = lay
        _KB[key] = v
    return v


def kartu_bab(img, n, judul_bab, tl, acc):
    """Kartu judul bab v2 (0 - 3,4 s): latar di belakang DIBURAMKAN (depth of field), angka
    raksasa bergaris + kilau menyapu, label BAB dengan jarak huruf melebar, judul kinetik v2,
    garis aksen berpendar."""
    if tl > 3.4 or tl < 0:
        return
    keluar = esmooth(clamp((tl - 2.65) / 0.6))
    al = clamp(tl / 0.35) * (1 - keluar)
    if al <= 0.01:
        return
    dy = -60 * keluar
    # latar buram (fokus pindah ke kartu)
    w_, h_ = img.size
    sm = img.reduce(8).filter(ImageFilter.GaussianBlur(3)).resize((w_, h_), Image.BILINEAR)
    sm = Image.blend(sm, Image.new("RGB", (w_, h_), SP0), 0.45)
    img.paste(Image.blend(img, sm, 0.92 * al))
    glow(img, W / 2, H / 2 + dy, 640, acc, 0.22 * al)
    # angka bergaris raksasa
    lay = _angka_garis(f"{n:02d}", 360, mix(acc, SP0, 0.25))
    sc_ = 1.0 + 0.08 * (1 - eo(clamp(tl / 1.0)))
    if 0.3 < tl < 1.5:
        lay = FX.kilau(lay, (tl - 0.3) / 1.2, 0.18, 0.9)
    if abs(sc_ - 1) > 0.005:
        lay = lay.resize((int(lay.width * sc_), int(lay.height * sc_)), Image.BICUBIC)
    _paste(img, lay, S(W / 2) - lay.width / 2, S(H / 2 - 20 + dy) - lay.height / 2, al * 0.55)
    # label BAB: jarak huruf melebar
    lab = "BAB " + f"{n:02d}"
    gap = " " * (1 + int(2 * eo(clamp(tl / 0.8))))
    teks(img, W / 2, H / 2 - 112 + dy + 20 * (1 - eo(clamp(tl / 0.45))), gap.join(lab), 24, acc,
         al * clamp(tl / 0.4), name=FB)
    judul(img, W / 2, H / 2 + dy, judul_bab.upper(), tl - 0.12, fsz=72, col=TEKS, alpha=al, maxw=1500)
    g = esmooth(clamp((tl - 0.45) / 0.6))
    if g > 0:
        glow(img, W / 2, H / 2 + 86 + dy, 200 * g + 10, acc, 0.5 * al)
        D.rrect_on(img, W / 2 - 170 * g, H / 2 + 83 + dy, W / 2 + 170 * g, H / 2 + 89 + dy, 3, acc, al)
        D.rrect_on(img, W / 2 - 60 * g, H / 2 + 84 + dy, W / 2 + 60 * g, H / 2 + 88 + dy, 2,
                   mix(acc, WHITE, 0.6), al)


_FIN = _cache()


def _vinyet(w, h):
    key = ("v", w, h)
    v = _FIN.get(key)
    if v is None:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        m = np.clip(1.0 - 0.34 * np.clip(d - 0.55, 0, None) ** 1.5, 0.55, 1.0)
        v = Image.fromarray((np.repeat(m[..., None], 3, axis=2) * 255).astype(np.uint8), "RGB")
        _FIN[key] = v
    return v


def _grain(w, h, k):
    key = ("g", w, h, k % 6)
    g = _FIN.get(key)
    if g is None:
        rng = np.random.default_rng(100 + k % 6)
        n = rng.integers(0, 11, (h, w), dtype=np.uint8)
        g = Image.fromarray(np.repeat(n[..., None], 3, axis=2), "RGB")
        _FIN[key] = g
    return g


def kamera(img, zoom=1.0, fx=0.5, fy=0.5, dx=0.0, dy=0.0):
    """Potong + skala ke 1920x1080 (zoom >= 1)."""
    w, h = img.size
    z = max(1.0, zoom)
    cw, ch = w / z, h / z
    x0 = (w - cw) * clamp(fx) + S(dx)
    y0 = (h - ch) * clamp(fy) + S(dy)
    x0 = min(max(0, x0), w - cw)
    y0 = min(max(0, y0), h - ch)
    return img.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))


TRANSISI_POOL = ("zoomthru", "tinta", "whip", "iris")


def jenis_transisi(i):
    """Jenis transisi MENUJU adegan i (bergantian supaya tiap pergantian bab terasa baru)."""
    return TRANSISI_POOL[(i - 1) % len(TRANSISI_POOL)]


def transisi(out, tl, dur, first, last, i=None, acc=None, acc_next=None):
    """Transisi bab v2 (2026). Keluar bab i -> fase keluar jenis(i+1); masuk bab i -> fase masuk
    jenis(i). Jenis: zoomthru (dorong menembus + blur radial + kilat), tinta (sapuan bentuk bertepi
    aksen), whip (geser cepat + blur gerak), iris (lingkaran menutup/membuka + cincin aksen).
    Tanpa i -> perilaku lama (zoom-blur)."""
    TO, TI = 0.36, 0.5
    if i is None:
        if not last and tl > dur - TO:
            u = clamp((tl - (dur - TO)) / TO)
            out = M._zoom(out, 1.0 + 0.32 * u * u, 0.5, 0.5)
            out = M._blur_arah(out, 22 * u * u)
            out = Image.blend(out, Image.new("RGB", out.size, SP0), 0.9 * u)
            out = M._kromatik(out, 7 * u)
        elif not first and tl < TI:
            u = clamp(tl / TI)
            out = M._zoom(out, 1.16 - 0.16 * eo(u), 0.5, 0.5)
            if u < 0.6:
                out = M._blur_arah(out, 16 * (1 - u / 0.6))
            out = Image.blend(out, Image.new("RGB", out.size, SP0), 0.85 * (1 - eo(u)))
            out = M._kromatik(out, 7 * (1 - u))
        return out
    acc = acc or ORANYE
    if not last and tl > dur - TO:
        u = clamp((tl - (dur - TO)) / TO)
        out = FX.trans_keluar(out, u, jenis_transisi(i + 1), acc_next or acc, SP0)
        out = M._kromatik(out, 6 * u)
    elif not first and tl < TI:
        u = clamp(tl / TI)
        out = FX.trans_masuk(out, u, jenis_transisi(i), acc, SP0)
        out = M._kromatik(out, 6 * (1 - u))
    return out


FINISH = dict(preset="sinema", bloom_kuat=0.42, bloom_thr=0.68, vin=0.34, grain_kuat=4.2)


def akhiri(out, k, sharpen=38):
    """Finishing v2026: tajam -> bloom (pendar lensa) -> grading filmic -> vinyet -> grain film."""
    out = out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=sharpen, threshold=2))
    if FX.AKTIF:
        return FX.finishing(out, k, **FINISH)
    out = ImageChops.multiply(out, _vinyet(out.width, out.height))
    return ImageChops.add(out, _grain(out.width, out.height, k), 1.0, -5)


# ================================================================== event SFX + kamera
BEAT_KAMERA = {"impact": 0.05, "boom": 0.06, "thud": 0.025, "door": 0.025}


def events(tl_data, beats):
    """Semua event suara (detik absolut): transisi bab + beat adegan (dikunci ke kata)."""
    ev = []
    scenes = tl_data["scenes"]
    for i, sc in enumerate(scenes):
        st = sc["start"]
        if i > 0:
            ev += [(st - 0.30, "whoosh", 0.75), (st + 0.10, "swish_up", 0.5), (st + 0.55, "thud", 0.45)]
        C = Ctx(sc, 0.0, st, i, len(scenes))
        for b in beats.get(sc["visual"], []):
            key, nth, off, jenis, g = b
            t_ = C.w(key, nth, off) if isinstance(key, str) else float(key)
            ev.append((st + t_, jenis, g))
    ev.sort()
    return ev


def punch(t, evs):
    k = 0.0
    for te, jenis, g in evs:
        a = BEAT_KAMERA.get(jenis)
        if not a:
            continue
        d = t - te
        if 0 <= d < 0.4:
            k = max(k, a * g * math.exp(-d / 0.1) * (1 - d / 0.4))
    return k
