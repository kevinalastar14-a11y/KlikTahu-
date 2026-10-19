#!/usr/bin/env python3
"""MESIN v12 "KONTINUITAS" - inti (dipakai episode dengan `"mesin": "v12"` di content.json).

Prinsip (docs/STANDAR_PRODUKSI_V12.md): satu dunia visual yang terus berubah bentuk, bukan
kumpulan adegan. Modul ini menyediakan:

  1. CUE kata  : waktu BEAT dikunci ke KATA yang diucapkan (build/kata.json dari align_kata.py).
                 Fungsi gambar dan SFX memakai sumber waktu yang SAMA -> sinkron AV tepat.
  2. Easing    : ease12 (antisipasi -> akselerasi -> deselerasi -> overshoot <= 8% -> settle),
                 follow (gerak sekunder tertunda), esm/eo/eio.
  3. Morph     : interpolasi bentuk poligon (resample N titik + rotasi indeks terbaik).
  4. Kamera    : gerak kamera kontinu sepanjang video (energi per babak), nol di frame 0 dan
                 frame akhir supaya loop mulus. Tidak ada reset zoom tiap adegan.
  5. Aksen     : warna aksen dicampur halus melintasi batas adegan (latar mesh tidak melompat).
  6. Loop      : campuran frame akhir -> frame 0 (loop_blend detik) dipakai render.py.
  7. Primitif  : cakram langit (bintang ter-cache), garis meteor, jam, kompas, chip, orbit.

Semua koordinat dalam ruang desain 1080x1920 (diagrams.S mengalikan SS).
"""
import json
import math
import os
import re

from PIL import Image, ImageDraw, ImageFilter

import diagrams as D
import mesin_fx as FX
from diagrams import (INK, CREAM, WHITE, MUTED, mix, seg, clamp, esmooth, eob, eo, font, tw, tlh,
                      paste_c, rrect_on, line_on, dot_on, ring_on, poly_on, _note)

S = lambda v: v * D.SS            # noqa: E731
NAVY = (18, 24, 54)
NAVY2 = (30, 40, 86)
STAR = (236, 240, 255)
KUNING = (246, 196, 62)
ORANYE = (240, 130, 60)

# ------------------------------------------------------------------ 1. CUE kata
_KATA = {"path": None, "data": None}
EVENTS12 = {}        # visual -> fungsi(sc_timeline) -> [(t_abs, jenis, gain)] (diisi modul episode)
KELUAR = [1.0]       # faktor keluar elemen non-persisten (1 -> 0 di 0,35 s terakhir adegan); diset per adegan


def set_keluar(tl, dur, ada_lanjutan=True, lebar=0.35):
    """Hitung & simpan faktor keluar: teks/chip/alat memudar sebelum batas adegan supaya potongan
    hanya menyisakan elemen persisten (cakram langit, cakrawala, chip tanggal)."""
    KELUAR[0] = (1.0 - esm((tl - (dur - lebar)) / (lebar * 0.85))) if ada_lanjutan else 1.0
    return KELUAR[0]


def _norm(w):
    return re.sub(r"[^a-z0-9]", "", str(w).lower())


def kata_json():
    """build/kata.json (dimuat sekali per proses). {} kalau belum ada."""
    bdir = os.environ.get("KT_BUILD") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
    p = os.path.join(bdir, "kata.json")
    if _KATA["path"] != p or _KATA["data"] is None:
        try:
            _KATA["data"] = json.load(open(p))
        except Exception:                      # noqa: BLE001
            _KATA["data"] = {}
        _KATA["path"] = p
    return _KATA["data"]


def t_kata(sc_id, kata, dur, fraksi, ke=1):
    """Detik (relatif adegan) saat `kata` ke-`ke` diucapkan; fallback fraksi x dur."""
    lst = kata_json().get(sc_id) or []
    n = 0
    target = _norm(kata)
    for w, a, _b in lst:
        if _norm(w) == target:
            n += 1
            if n == ke:
                return float(a)
    return fraksi * dur


def cues(sc, dur, tabel):
    """tabel = {nama: (kata|None, fraksi[, ke])} -> {nama: detik}. Monoton tidak dipaksa."""
    out = {}
    for nama, spec in tabel.items():
        kata, fr = spec[0], spec[1]
        ke = spec[2] if len(spec) > 2 else 1
        out[nama] = t_kata(sc.get("id", ""), kata, dur, fr, ke) if kata else fr * dur
    return out


# ------------------------------------------------------------------ 2. easing
def esm(t):
    return esmooth(clamp(t))


def eio(t):
    t = clamp(t)
    return 4 * t * t * t if t < 0.5 else 1 - ((-2 * t + 2) ** 3) / 2


def ease12(t, antisipasi=0.07, overshoot=0.06):
    """Antisipasi (mundur) -> akselerasi -> deselerasi -> overshoot kecil -> settle. t 0..1."""
    t = clamp(t)
    a = 0.18                                   # porsi waktu antisipasi
    if t < a:
        u = t / a
        return -antisipasi * math.sin(math.pi * u) ** 1.2
    u = (t - a) / (1 - a)
    # quintic out + overshoot yang teredam
    base = 1 - (1 - u) ** 5
    ov = overshoot * math.sin(math.pi * clamp((u - 0.45) / 0.55)) * (1 - u) ** 0.6 * 2.2
    return base + ov


def follow(t, lag, dur=0.5):
    """Gerak sekunder: elemen anak mengikuti induk dengan jeda `lag` detik (t detik sejak mulai)."""
    return ease12(clamp((t - lag) / dur), 0.03, 0.08)


def pulsa(tg, f=1.0, ph=0.0):
    return 0.5 + 0.5 * math.sin(2 * math.pi * f * tg + ph)


# ------------------------------------------------------------------ 3. morph bentuk
def _resample(pts, n):
    if len(pts) < 2:
        return [pts[0]] * n if pts else []
    seglen = []
    for i in range(len(pts)):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % len(pts)]
        seglen.append(math.hypot(x1 - x0, y1 - y0))
    tot = sum(seglen) or 1.0
    out, acc, i, d = [], 0.0, 0, 0.0
    step = tot / n
    for k in range(n):
        target = k * step
        while i < len(pts) - 1 and acc + seglen[i] < target - 1e-9:
            acc += seglen[i]; i += 1
        u = (target - acc) / (seglen[i] or 1.0)
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % len(pts)]
        out.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u))
    return out


def morph(pa, pb, u, n=96):
    """Poligon A -> B (u 0..1). Titik di-resample sama banyak, indeks B diputar agar jarak minimum."""
    u = clamp(u)
    A, B = _resample(pa, n), _resample(pb, n)
    best, bo = None, 0
    for off in range(0, n, max(1, n // 24)):
        dsum = sum((A[i][0] - B[(i + off) % n][0]) ** 2 + (A[i][1] - B[(i + off) % n][1]) ** 2 for i in range(0, n, 4))
        if best is None or dsum < best:
            best, bo = dsum, off
    return [(A[i][0] + (B[(i + bo) % n][0] - A[i][0]) * u, A[i][1] + (B[(i + bo) % n][1] - A[i][1]) * u)
            for i in range(n)]


def bentuk_lingkaran(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def bentuk_bintang(cx, cy, r, n=5, dalam=0.45):
    pts = []
    for i in range(2 * n):
        rr = r if i % 2 == 0 else r * dalam
        a = -math.pi / 2 + i * math.pi / n
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def bentuk_butir(cx, cy, r, seed=3, n=14):
    """Butiran debu tak beraturan (deterministik)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (0.72 + 0.28 * (0.5 + 0.5 * math.sin(seed * 1.7 + i * 2.3) * math.cos(seed + i * 0.9)))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def bentuk_rumah(cx, cy, w, h):
    return [(cx - w / 2, cy + h / 2), (cx - w / 2, cy - h * 0.15), (cx, cy - h / 2),
            (cx + w / 2, cy - h * 0.15), (cx + w / 2, cy + h / 2)]


# ------------------------------------------------------------------ 4. kamera & 5. aksen
def energi_adegan(sc, meta):
    e = ((meta or {}).get("v12") or {}).get("energi") or {}
    return float(e.get(sc.get("id", ""), 0.5))


def jendela_loop(tl, total, lebar=1.0):
    """0 di t=0 dan t=total, 1 di tengah (supaya frame awal == frame akhir)."""
    return esm(tl / lebar) * esm((total - tl) / lebar)


def kamera(tl, total, scenes, meta, beats=None):
    """(zoom k, dx, dy) kontinu. Energi babak mengatur amplitudo hanyut + dorongan BEAT."""
    i = 0
    for j, s in enumerate(scenes):
        if tl >= s["start"]:
            i = j
    sc = scenes[i]
    e_now = energi_adegan(sc, meta)
    # campur energi ke adegan berikutnya di 1,2 s terakhir (eskalasi terkendali, tanpa lompatan)
    if i + 1 < len(scenes):
        sisa = sc["start"] + sc["dur"] - tl
        if sisa < 1.2:
            e_now = e_now + (energi_adegan(scenes[i + 1], meta) - e_now) * esm(1 - sisa / 1.2)
    w = jendela_loop(tl, total, 1.1)
    amp = (4.0 + 11.0 * e_now) * w
    dx = amp * (0.6 * math.sin(tl * 0.21) + 0.4 * FX.nois2(tl * 0.35, 11))
    dy = amp * 0.7 * (0.6 * math.cos(tl * 0.17 + 0.8) + 0.4 * FX.nois2(tl * 0.35, 12))
    k = 1.0 + (0.012 + 0.030 * e_now) * w * (0.5 + 0.5 * math.sin(tl * 0.12 + 1.0))
    # dorongan singkat di beat berat (sama dengan SFX)
    if beats:
        for t, jenis, g in beats:
            a = {"impact": 0.040, "thump": 0.045, "boom": 0.035, "thud": 0.018}.get(jenis)
            if a and 0 <= tl - t < 0.35:
                d = tl - t
                k += a * g * math.exp(-d / 0.09) * (1 - d / 0.35) * w
    return k, dx, dy


def aksen_pada(tl, scenes, lebar=0.9):
    """Warna aksen dicampur halus di sekitar batas adegan."""
    i = 0
    for j, s in enumerate(scenes):
        if tl >= s["start"]:
            i = j
    a = D.hexc(scenes[i]["accent"])
    if i + 1 < len(scenes):
        sisa = scenes[i]["start"] + scenes[i]["dur"] - tl
        if sisa < lebar:
            a = mix(a, D.hexc(scenes[i + 1]["accent"]), esm(1 - sisa / lebar) * 0.5)
    if i > 0:
        lewat = tl - scenes[i]["start"]
        if lewat < lebar:
            a = mix(D.hexc(scenes[i - 1]["accent"]), a, 0.5 + 0.5 * esm(lewat / lebar))
    return a


def loop_blend(meta):
    return float(((meta or {}).get("v12") or {}).get("loop_blend", 0.7)) if ((meta or {}).get("v12") or {}).get("loop", True) else 0.0


# ------------------------------------------------------------------ 7. primitif
_CAK = {}


def _bima_sakti(n, seed):
    """Pita Bima Sakti: derau lembut (numpy) dipotong pita diagonal Gaussian, lalu blur. Di-cache per ukuran."""
    import numpy as np
    rnd = np.random.default_rng(seed)
    kecil = 28
    nz = rnd.random((kecil, kecil)).astype("float32")
    im = Image.fromarray((nz * 255).astype("uint8"), "L").resize((n, n), Image.BICUBIC)
    a = np.asarray(im).astype("float32") / 255.0
    yy, xx = np.mgrid[0:n, 0:n].astype("float32")
    # pita diagonal (kiri-bawah -> kanan-atas), lebar ~0,26 n, sedikit melengkung
    d = ((xx - n / 2) * 0.62 + (yy - n / 2) * 0.78) / n + 0.06 * np.sin(xx / n * 4.0)
    pita = np.exp(-(d / 0.13) ** 2)
    # dua 'awan' lebih terang + celah gelap (great rift) agar tidak seperti garis
    pita *= 0.75 + 0.45 * np.exp(-(((xx - n * 0.62) / (n * 0.22)) ** 2 + ((yy - n * 0.40) / (n * 0.22)) ** 2))
    pita *= 1.0 - 0.45 * np.exp(-(d / 0.035) ** 2)
    alpha = np.clip(pita * (0.35 + 0.65 * a), 0, 1)
    lay = Image.fromarray((alpha * 255).astype("uint8"), "L").filter(ImageFilter.GaussianBlur(n * 0.012))
    return lay


def cakram_langit(img, cx, cy, r, tg, gelap=1.0, alpha=1.0, bintang=1.0, seed=5, paralaks=1.0):
    """Cakram langit malam dengan KEDALAMAN: isi navy (gelap 0..1), pita Bima Sakti samar, bintang 3 lapis
    (jauh/tengah/dekat) dengan paralaks berbeda + kedip, dan beberapa bintang terang berwarna dengan glint."""
    if alpha <= 0.01 or r <= 2:
        return
    col = mix(mix(NAVY2, NAVY, clamp(gelap)), CREAM, 0.0)
    key = (int(r), round(D.SS, 3), seed)
    lay = _CAK.get(key)
    if lay is None:
        n = int(S(r) * 2) + 4
        lay = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        dd.ellipse([2, 2, n - 2, n - 2], fill=(255, 255, 255, 255))
        import random
        rnd = random.Random(seed)
        pts = []
        for _ in range(int(r * 0.46)):
            a = rnd.random() * 2 * math.pi
            rr = r * math.sqrt(rnd.random()) * 0.96
            ukuran = 1.0 + 1.6 * rnd.random() ** 3
            lapis = 0 if ukuran < 1.25 else (1 if ukuran < 1.9 else 2)       # jauh / tengah / dekat
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a), ukuran, rnd.random(), lapis))
        # bintang terang berwarna (Betelgeuse-oranye, Rigel-biru, putih): 5 buah, tidak di tepi
        terang = []
        for k in range(5):
            a = rnd.random() * 2 * math.pi
            rr = r * (0.25 + 0.55 * rnd.random())
            warna = ((255, 205, 160), (190, 210, 255), (255, 250, 235), (200, 215, 255), (255, 225, 190))[k]
            terang.append((cx + rr * math.cos(a), cy + rr * math.sin(a), 2.4 + 0.8 * rnd.random(), rnd.random(), warna))
        galaksi = _bima_sakti(n, seed)
        # pita hanya di dalam cakram
        galaksi = Image.fromarray((__import__("numpy").asarray(galaksi).astype("float32")
                                   * __import__("numpy").asarray(lay.getchannel("A")).astype("float32") / 255.0
                                   ).astype("uint8"), "L")
        lay = (lay, pts, terang, galaksi)
        _CAK[key] = lay
    mask, pts, terang, galaksi = lay
    base = Image.new("RGB", mask.size, col)
    m = mask.getchannel("A") if alpha >= 0.995 else mask.getchannel("A").point(lambda v: int(v * alpha))
    x0, y0 = int(S(cx) - mask.width / 2), int(S(cy) - mask.height / 2)
    img.paste(base, (x0, y0), m)
    # pita Bima Sakti (samar; ikut 'gelap' dan 'bintang')
    ag = alpha * bintang * clamp(gelap * 1.2) * 0.16
    if ag > 0.01:
        gm = galaksi.point(lambda v, a=ag: int(v * a))
        img.paste(Image.new("RGB", mask.size, mix(STAR, NAVY2, 0.35)), (x0, y0), gm)
    ring_on(img, cx, cy, r, mix(col, WHITE, 0.18), 3, alpha * 0.9)
    if bintang > 0.01:
        # paralaks: lapis dekat bergeser paling jauh (hanyut sangat pelan, tanpa lompatan)
        ox = paralaks * 3.2 * math.sin(tg * 0.11 + 0.4)
        oy = paralaks * 2.2 * math.cos(tg * 0.09 + 1.1)
        fac = (0.22, 0.55, 1.0)
        for (x, y, rr, ph, lp) in pts:
            k = 0.55 + 0.45 * math.sin(tg * (1.3 + ph * 2.0) + ph * 20)
            a = alpha * bintang * (0.35 + 0.65 * k) * clamp(gelap * 1.3)
            if a > 0.03:
                dot_on(img, x + ox * fac[lp], y + oy * fac[lp], rr, STAR, a)
        for (x, y, rr, ph, warna) in terang:
            k = 0.7 + 0.3 * math.sin(tg * (0.9 + ph) + ph * 9)
            a = alpha * bintang * clamp(gelap * 1.3) * k
            if a > 0.03:
                xx, yy = x + ox * 0.8, y + oy * 0.8
                dot_on(img, xx, yy, rr * 2.6, warna, a * 0.16)
                dot_on(img, xx, yy, rr, mix(warna, WHITE, 0.4), a)
                g = rr * 3.4
                line_on(img, (xx - g, yy), (xx + g, yy), warna, 1, a * 0.45)
                line_on(img, (xx, yy - g), (xx, yy + g), warna, 1, a * 0.45)


def garis_meteor(img, p0, p1, u, col=STAR, width=4, alpha=1.0, ekor=0.55, train=False, train_dur=0.6):
    """Garis meteor: kepala bergerak dari p0 ke p1 (u 0..1), ekor memudar di belakang.
    train=True: untuk u di (1, 1+train_dur] digambar JEJAK PERSISTEN (ciri Orionid: cepat, 66 km/s,
    meninggalkan jejak bercahaya yang memudar) - garis penuh yang menipis & meredup, tanpa kepala."""
    if alpha <= 0.01 or u <= 0:
        return
    if u > 1.0 and train:
        f = clamp((u - 1.0) / train_dur)
        if f >= 1.0:
            return
        a = alpha * (1 - f) ** 1.6
        wd = max(1, width * (0.75 - 0.5 * f))
        # jejak paling terang di 60-85% lintasan (tempat meteor paling panas)
        n = 8
        for i in range(n):
            a0, a1 = i / n, (i + 1) / n
            q0 = (p0[0] + (p1[0] - p0[0]) * a0, p0[1] + (p1[1] - p0[1]) * a0)
            q1 = (p0[0] + (p1[0] - p0[0]) * a1, p0[1] + (p1[1] - p0[1]) * a1)
            prof = math.exp(-((a0 + a1) / 2 - 0.72) ** 2 / 0.09)
            line_on(img, q0, q1, mix(col, (170, 200, 255), 0.5 * f), wd, a * (0.25 + 0.75 * prof))
        return
    u = clamp(u)
    hx, hy = p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u
    u0 = max(0.0, u - ekor)
    n = 10
    for i in range(n):
        a0 = u0 + (u - u0) * i / n
        a1 = u0 + (u - u0) * (i + 1) / n
        q0 = (p0[0] + (p1[0] - p0[0]) * a0, p0[1] + (p1[1] - p0[1]) * a0)
        q1 = (p0[0] + (p1[0] - p0[0]) * a1, p0[1] + (p1[1] - p0[1]) * a1)
        line_on(img, q0, q1, col, max(1, width * (0.3 + 0.7 * (i + 1) / n)), alpha * ((i + 1) / n) ** 1.4)
    dot_on(img, hx, hy, width * 0.9, WHITE, alpha)
    return hx, hy


_EKOR_CACHE = {}


def _ekor_sprite(panjang_px, lebar_px, col):
    """Sprite ekor komet (RGBA, ekor ke arah +x, inti di x = lebar_px): gradasi halus + blur, di-cache."""
    key = (int(panjang_px), int(lebar_px), col)
    sp = _EKOR_CACHE.get(key)
    if sp is not None:
        return sp
    pad = int(lebar_px * 1.2) + 4
    Wd, Hd = int(panjang_px + lebar_px + pad * 2), int(lebar_px * 2 + pad * 2)
    lay = Image.new("RGBA", (Wd, Hd), col + (0,))
    d = ImageDraw.Draw(lay)
    x_inti, yc = pad + lebar_px * 0.5, Hd / 2
    n = 72
    for i in range(n):
        u = i / n
        x0 = x_inti + panjang_px * u
        x1 = x_inti + panjang_px * (i + 1) / n + 1.5
        h = 2 + lebar_px * (0.25 + 0.75 * u) * 0.5
        a = int(255 * 0.62 * (1 - u) ** 1.35)
        d.rectangle([x0, yc - h, x1, yc + h], fill=col + (a,))
    lay = lay.filter(ImageFilter.GaussianBlur(max(1.0, lebar_px * 0.30)))
    sp = (lay, x_inti, yc)
    _EKOR_CACHE[key] = sp
    return sp


def komet(img, cx, cy, s, tg, alpha=1.0, arah=(-0.8, -0.6), ekor=1.0, col=None):
    """Komet: inti terang + koma + ekor debu halus (sprite gradasi, bukan rangkaian titik)."""
    if alpha <= 0.01:
        return
    col = col or mix(KUNING, WHITE, 0.35)
    ax, ay = arah
    L = math.hypot(ax, ay) or 1.0
    ax, ay = ax / L, ay / L
    panjang = 260 * s * ekor

    def _tempel(lay, x_inti, yc, phi, a):
        rot = lay.rotate(-phi, resample=Image.BICUBIC, expand=True)
        # posisi inti setelah rotasi (rotasi mengelilingi pusat sprite)
        vx, vy = x_inti - lay.size[0] / 2, yc - lay.size[1] / 2
        r_ = math.radians(phi)
        rx, ry = vx * math.cos(r_) - vy * math.sin(r_), vx * math.sin(r_) + vy * math.cos(r_)
        px = int(round(D.S(cx) - (rot.size[0] / 2 + rx)))
        py = int(round(D.S(cy) - (rot.size[1] / 2 + ry)))
        m = rot.split()[3]
        if a < 0.995:
            m = m.point(lambda v, aa=a: int(v * aa))
        img.paste(rot.convert("RGB"), (px, py), m)

    if panjang > 4:
        phi0 = math.degrees(math.atan2(ay, ax))
        # 1) ekor ion: lurus menjauhi Matahari, lebih panjang, tipis, kebiruan (digambar dulu = di belakang)
        lay_i, xi, yi = _ekor_sprite(D.S(panjang * 1.35), D.S(16 * s), mix((150, 190, 255), NAVY, 0.25))
        _tempel(lay_i, xi, yi, phi0 - 9.0 + 0.8 * math.sin(tg * 2.3), alpha * 0.6)
        # 2) ekor debu: lebih lebar, hangat, sedikit melengkung/goyang
        lay, x_inti, yc = _ekor_sprite(D.S(panjang), D.S(34 * s), mix(col, NAVY, 0.18))
        _tempel(lay, x_inti, yc, phi0 + 1.4 * math.sin(tg * 1.7), alpha)
    import mesin_v11 as V
    V._glow11(img, cx, cy, 70 * s, mix(col, WHITE, 0.3), alpha * 0.7)
    dot_on(img, cx, cy, 13 * s, WHITE, alpha)
    dot_on(img, cx, cy, 20 * s, mix(col, WHITE, 0.2), alpha * 0.45)


def jam(img, cx, cy, r, jam_desimal, alpha, col, tg=0.0, label=None):
    """Jam analog sederhana (jam_desimal 0..24)."""
    alpha = alpha * KELUAR[0]
    if alpha <= 0.01:
        return
    dot_on(img, cx, cy, r, mix(WHITE, CREAM, 0.4), alpha, outline=col, width=5)
    for k in range(12):
        a = -math.pi / 2 + k * math.pi / 6
        r0 = r * (0.84 if k % 3 else 0.78)
        line_on(img, (cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
                (cx + r * 0.92 * math.cos(a), cy + r * 0.92 * math.sin(a)), mix(col, INK, 0.3), 3 if k % 3 else 5, alpha)
    h = (jam_desimal % 12) / 12 * 2 * math.pi - math.pi / 2
    m = (jam_desimal % 1) * 2 * math.pi - math.pi / 2
    line_on(img, (cx, cy), (cx + r * 0.52 * math.cos(h), cy + r * 0.52 * math.sin(h)), INK, 7, alpha)
    line_on(img, (cx, cy), (cx + r * 0.76 * math.cos(m), cy + r * 0.76 * math.sin(m)), col, 5, alpha)
    dot_on(img, cx, cy, 6, col, alpha)
    if label:
        paste_c(img, cx, cy - r - 30, label, font(D.FS, 24), mix(col, INK, 0.2), alpha)


def kompas(img, cx, cy, r, alpha, col, sudut_jarum=0.0, tebal=5):
    """Kompas: lingkaran + U/T/S/B + jarum (0 = Timur ke kanan; sudut dalam derajat searah jarum)."""
    alpha = alpha * KELUAR[0]
    if alpha <= 0.01:
        return
    dot_on(img, cx, cy, r, mix(WHITE, CREAM, 0.4), alpha, outline=col, width=tebal)
    f = font(D.FB, 24)
    for lab, ang in (("U", -90), ("T", 0), ("S", 90), ("B", 180)):
        a = math.radians(ang)
        paste_c(img, cx + r * 0.74 * math.cos(a), cy + r * 0.74 * math.sin(a), lab, f,
                col if lab == "T" else mix(INK, CREAM, 0.35), alpha)
    a = math.radians(sudut_jarum)
    tip = (cx + r * 0.55 * math.cos(a), cy + r * 0.55 * math.sin(a))
    ek = (cx - r * 0.35 * math.cos(a), cy - r * 0.35 * math.sin(a))
    px, py = -math.sin(a) * r * 0.10, math.cos(a) * r * 0.10
    poly_on(img, [tip, (cx + px, cy + py), ek, (cx - px, cy - py)], col, alpha)
    dot_on(img, cx, cy, 6, WHITE, alpha, outline=col, width=3)


def chip(img, cx, cy, text, col, alpha, tt, fsz=26, persisten=False):
    import mesin_v11 as V
    V._chip11(img, cx, cy, text, col, alpha * (1.0 if persisten else KELUAR[0]), tt, fsz=fsz)


def label(img, cx, cy, text, col, alpha, fsz=24, name=None):
    import mesin_v11 as V
    V._label11(img, cx, cy, text, col, alpha * KELUAR[0], fsz=fsz, name=name or D.FS)


def stiker(img, cx, cy, text, alpha, tt, **kw):
    import mesin_v11 as V
    V._stiker11(img, cx, cy, text, alpha * KELUAR[0], tt, **kw)


def bab(img, sc, accent, tl, al=1.0, y=268):
    import mesin_v11 as V
    V._bab11(img, sc, accent, tl, al * KELUAR[0], y=y)


def silang(img, cx, cy, r, col, alpha, u=1.0):
    """Tanda silang 'bukan' yang menggambar diri (u 0..1)."""
    alpha = alpha * KELUAR[0]
    if alpha <= 0.01 or u <= 0:
        return
    u1 = clamp(u * 2); u2 = clamp(u * 2 - 1)
    line_on(img, (cx - r, cy - r), (cx - r + 2 * r * u1, cy - r + 2 * r * u1), col, 8, alpha)
    if u2 > 0:
        line_on(img, (cx + r, cy - r), (cx + r - 2 * r * u2, cy - r + 2 * r * u2), col, 8, alpha)


def elips_pts(cx, cy, a, b, n=72, rot=0.0):
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = a * math.cos(t), b * math.sin(t)
        out.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    return out


def titik_elips(cx, cy, a, b, u, rot=0.0):
    t = 2 * math.pi * u
    x, y = a * math.cos(t), b * math.sin(t)
    return (cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot))


def polyline_on(img, pts, col, width, alpha, tutup=True):
    if alpha <= 0.01 or len(pts) < 2:
        return
    n = len(pts) if tutup else len(pts) - 1
    for i in range(n):
        line_on(img, pts[i], pts[(i + 1) % len(pts)], col, width, alpha)


def _selftest():
    import numpy as np                      # noqa: F401
    assert abs(ease12(1.0) - 1.0) < 1e-6 and ease12(0.0) == 0.0 and ease12(0.08) < 0
    assert max(ease12(t / 100) for t in range(101)) <= 1.085
    a = bentuk_lingkaran(0, 0, 10); b = bentuk_bintang(0, 0, 10)
    m = morph(a, b, 0.5)
    assert len(m) == 96 and all(math.isfinite(x) and math.isfinite(y) for x, y in m)
    assert morph(a, b, 0.0)[0] != morph(a, b, 1.0)[0]
    sc = [{"id": "intro", "start": 0, "dur": 5, "accent": "#1F2A5A"}, {"id": "f1", "start": 5, "dur": 5, "accent": "#8A3B2E"}]
    meta = {"v12": {"energi": {"intro": 0.5, "f1": 1.0}}}
    k0, dx0, dy0 = kamera(0.0, 10, sc, meta)
    kE, dxE, dyE = kamera(10.0, 10, sc, meta)
    assert abs(k0 - 1) < 1e-6 and abs(dx0) < 1e-6 and abs(kE - 1) < 1e-6 and abs(dyE) < 1e-6, (k0, kE)
    k5 = kamera(5.0, 10, sc, meta)
    assert k5[0] >= 1.0
    assert aksen_pada(4.9, sc) != aksen_pada(2.0, sc)
    assert t_kata("tidak_ada", "kata", 10.0, 0.5) == 5.0
    img = Image.new("RGB", (int(1080 * D.SS), int(1920 * D.SS)), CREAM)
    cakram_langit(img, 540, 760, 380, 1.0)
    garis_meteor(img, (300, 500), (700, 900), 0.6)
    komet(img, 440, 700, 1.0, 0.5)
    jam(img, 300, 1480, 90, 21.5, 1.0, (31, 122, 107), label="21.30")
    kompas(img, 780, 1480, 90, 1.0, (106, 79, 179), 0.0)
    silang(img, 500, 500, 30, (200, 60, 40), 1.0, 0.7)
    polyline_on(img, elips_pts(540, 760, 300, 110, rot=0.4), INK, 3, 1.0)
    print("selftest v12 inti OK")


if __name__ == "__main__":
    _selftest()
