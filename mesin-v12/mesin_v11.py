#!/usr/bin/env python3
"""MESIN v11 "EDITOR" — paket motion graphics setara channel edukasi besar.

Dipakai episode yang menyetel `"mesin": "v11"` di content.json (episode lama tidak
berubah sedikit pun). Isi paket:

  A. TIPOGRAFI & STIKER
     _judul11   judul kinetik: kata jatuh satu per satu (skala 1,5 -> 1 dengan pegas)
                + sapuan STABILO di belakang kata kunci (gaya editor YouTube)
     _stiker11  stiker tebal: outline putih, bayangan keras, pop + goyang pelan
     _chip11    label kecil pop dengan titik aksen
  B. GERAK & CAHAYA
     _glow11    cahaya lembut (sprite radial ter-cache: murah)
     _panah11   panah gambar-tangan yang menggambar dirinya sendiri (bezier)
     _gelom11   gelombang sinus berjalan (amplitudo bisa meredam)
     _busur11   busur pancaran sinyal (menara/router)
     _partikel11 ledakan partikel saat elemen muncul
  C. OBJEK SIAP PAKAI
     _hp11 (HP + batang sinyal + pemutar loading), _menara11 (BTS kisi + lampu + pancaran),
     _router11, _micro11, _orang11, _baterai11, _dinding11
  D. TRANSISI BARU (render.py): punch (dorong + kilat + blur arah), slide (whip
     elastis + blur gerak), glitch (pecah RGB + irisan bergeser) — semuanya dengan
     aberasi kromatik halus.
  E. BEAT: satu sumber kebenaran untuk SFX + guncangan kamera. BEATS[visual] berisi
     (fraksi_durasi, jenis_suara). Fungsi gambar memakai fraksi yang SAMA, jadi suara
     selalu jatuh tepat saat elemen muncul. events(scenes) -> dipakai sfx.py & render.py.

Zona aman Shorts: teks penting tidak diletakkan di y > 1640 (tertutup judul/tombol UI)
dan x > 950 pada y 1100-1700 (kolom tombol suka/komentar/bagikan).
"""
import math
import re
from PIL import Image, ImageDraw, ImageFilter, ImageChops

import diagrams as D
import mesin_fx as FX          # FX 2026 (kilau, pegas, transisi zoomthru/tinta/cahaya)
from diagrams import (INK, CREAM, WHITE, MUTED, RED, BLUE, GREEN, AMBER, FB, FS, FM,
                      mix, seg, clamp, esmooth, eob, eo, font, tw, tlh, paste_c, ell,
                      rrect_on, line_on, dot_on, ring_on, poly_on, _dw, _note)

S = lambda v: v * D.SS            # noqa: E731  (SS dibaca dinamis: render mengubahnya)
GELAP = (28, 32, 44)
KUNING = (246, 196, 62)


# =============================================================== A. tipografi
def _wrap_words(words, f, maxw):
    lines, cur = [], []
    for w_ in words:
        t = " ".join(cur + [w_])
        if cur and tw(t, f) > maxw:
            lines.append(cur)
            cur = [w_]
        else:
            cur.append(w_)
    if cur:
        lines.append(cur)
    return lines


def _judul11(img, text, accent, tl, al, y=560, hl="", fsz=56, t0=0.10, maxw=900):
    """Judul kinetik 1-2 baris. hl = kata kunci yang diberi sapuan stabilo."""
    if al <= 0.01 or not text:
        return
    words = text.split()
    size = fsz
    while size > 34:
        f = font(FB, size)
        lines = _wrap_words(words, f, maxw)
        if len(lines) <= 2:
            break
        size -= 4
    f = font(FB, size)
    lh = tlh(f) * 1.06
    hl_set = set(w_.strip(",.?!:") for w_ in hl.upper().split()) if hl else set()
    sp = tw(" ", f)
    idx = 0
    y0 = y - (len(lines) - 1) * lh / 2
    for li, ln in enumerate(lines):
        wline = tw(" ".join(ln), f)
        x = 540 - wline / 2
        yy = y0 + li * lh
        # stabilo di belakang kata kunci (satu sapuan per baris)
        hx = [(x + tw(" ".join(ln[:k]), f) + (sp if k else 0), tw(w_, f))
              for k, w_ in enumerate(ln) if w_.upper().strip(",.?!:") in hl_set]
        if hx:
            ha = min(h[0] for h in hx) - 14
            hb = max(h[0] + h[1] for h in hx) + 14
            q = esmooth(seg(tl, t0 + 0.45 + li * 0.1, t0 + 0.80 + li * 0.1))
            if q > 0:
                xb = ha + (hb - ha) * q
                poly_on(img, [(ha, yy - lh * 0.10), (xb, yy - lh * 0.16),
                              (xb + 6, yy + lh * 0.36), (ha - 4, yy + lh * 0.40)],
                        mix(accent, WHITE, 0.55), al * 0.92)
        for k, w_ in enumerate(ln):
            tk = tl - (t0 + idx * 0.065)
            idx += 1
            ww = tw(w_, f)
            if tk <= 0:
                x += ww + sp
                continue
            cx = x + ww / 2
            kunci = w_.upper().strip(",.?!:") in hl_set
            col = mix(accent, INK, 0.30) if kunci else INK
            if KINETIK_2026:
                _kata11(img, cx, yy, w_, size, col, al, tk, lh)
            else:
                q = clamp(tk / 0.32)
                sc = 1.0 + 0.5 * (1.0 - eob(q, 2.0))
                paste_c(img, cx, yy + (1 - eo(q)) * -18, w_, f, col, al * min(1.0, q * 2.2), scale=sc)
            x += ww + sp


KINETIK_2026 = True     # judul: kata terangkat dari balik garis (mask reveal) + blur gerak + bayangan lembut
_W11 = {}


def _kata_lay(w_, size, col):
    key = (w_, size, col, round(D.SS, 3))
    v = _W11.get(key)
    if v is None:
        f = font(FB, size)
        bb = f.getbbox(w_)
        pad = int(S(8))
        lay = Image.new("RGBA", (bb[2] - bb[0] + pad * 2 + int(S(4)), int(S(tlh(f) * 1.3)) + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(lay).text((lay.width / 2, lay.height / 2), w_, font=f, fill=col + (255,), anchor="mm")
        shd = FX.bayang(lay, S(5), 0.22, warna=mix(CREAM, INK, 0.55))
        v = (lay, shd)
        if len(_W11) > 900:
            _W11.clear()
        _W11[key] = v
    return v


def _kata11(img, cx, cy, w_, size, col, al, tk, lh):
    (lay, (shd, spad)) = _kata_lay(w_, size, col)
    e = FX.spring(tk, 0.55, 13.0)
    q = clamp(tk / 0.45)
    dy = (1 - e) * lh * 0.80
    X = S(cx) - lay.width / 2
    Y = S(cy + dy) - lay.height / 2
    clip = S(cy + lh * 0.52)
    vis = int(clip - Y)
    if vis <= 2:
        return
    a = clamp(al * min(1.0, q * 3.0))
    L2 = lay
    if q < 0.55:
        f_ = 1 + 5 * (1 - q / 0.55)
        L2 = lay.resize((lay.width, max(2, int(lay.height / f_))), Image.BILINEAR).resize(lay.size, Image.BILINEAR)
    if vis < L2.height:
        L2 = L2.crop((0, 0, L2.width, vis))
    elif dy < 2:
        m = shd.getchannel("A").point(lambda v: int(v * a))
        img.paste(shd.convert("RGB"), (int(X - spad), int(Y - spad + S(4))), m)
    m = L2.getchannel("A") if a >= 0.995 else L2.getchannel("A").point(lambda v: int(v * a))
    img.paste(L2.convert("RGB"), (int(X), int(Y)), m)


_STK = {}


def _stiker_layer(text, fsz, fg, bg, stroke):
    key = (text, fsz, fg, bg, stroke, round(D.SS, 3))
    lay = _STK.get(key)
    if lay is not None:
        return lay
    f = font(FB, fsz)
    wt, ht = tw(text, f), tlh(f)
    pad_x, pad_y, sh = 30, 16, 8
    w_, h_ = wt + pad_x * 2, ht + pad_y * 2
    lay = Image.new("RGBA", (int(S(w_ + sh + 16)), int(S(h_ + sh + 16))), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    o = S(8)
    r = S(min(26, h_ / 2))
    dd.rounded_rectangle([o + S(sh), o + S(sh), o + S(w_ + sh), o + S(h_ + sh)], radius=r,
                         fill=mix(INK, bg, 0.25) + (255,))
    dd.rounded_rectangle([o, o, o + S(w_), o + S(h_)], radius=r, fill=bg + (255,),
                         outline=WHITE + (255,), width=max(2, int(S(stroke))))
    # v2026: kilap setengah atas (kesan cembung/mengilap)
    hl = Image.new("L", lay.size, 0)
    ImageDraw.Draw(hl).rounded_rectangle([o + S(stroke + 3), o + S(stroke + 2), o + S(w_ - stroke - 3),
                                          o + S(h_ * 0.46)], radius=max(2, r - S(4)), fill=52)
    lay.paste(Image.new("RGBA", lay.size, (255, 255, 255, 255)), (0, 0), hl)
    dd.text((o + S(w_ / 2), o + S(h_ / 2)), text, font=f, fill=fg + (255,), anchor="mm")
    _STK[key] = lay
    return lay


def _stiker11(img, cx, cy, text, alpha, tt, bg=None, fg=WHITE, fsz=34, rot=-4.0, tg=0.0, stroke=5):
    """Stiker pop (skala 0 -> 1,15 -> 1) + goyang halus. tt = waktu sejak muncul (detik)."""
    if alpha <= 0.01 or tt <= 0 or not text:
        return
    bg = bg or RED
    base = _stiker_layer(text, round(fsz * K_TXT), fg, bg, stroke)
    e = FX.spring(tt, 0.38, 16.0)
    k = 0.35 + 0.65 * e
    wob = rot + (1 - e) * -12 + 1.6 * math.sin(tg * 2.2 + cx * 0.01)
    if 0.18 < tt < 0.95:
        base = FX.kilau(base, (tt - 0.18) / 0.77, 0.22, 0.55)
    lay = base.rotate(wob, resample=Image.BICUBIC, expand=True)
    if abs(k - 1.0) > 0.01:
        lay = lay.resize((max(2, int(lay.width * k)), max(2, int(lay.height * k))), Image.BICUBIC)
    w_d, h_d = base.width / D.SS, base.height / D.SS
    _note("stiker", cx - w_d / 2, cy - h_d / 2, cx + w_d / 2, cy + h_d / 2, text)
    pos = (int(S(cx) - lay.width / 2), int(S(cy) - lay.height / 2))
    a = clamp(alpha * min(1.0, tt / 0.10))
    if a < 0.995:
        m = lay.getchannel("A").point(lambda v: int(v * a))
        img.paste(lay.convert("RGB"), pos, m)
    else:
        img.paste(lay, pos, lay)


def _chip11(img, cx, cy, text, col, alpha, tt, fsz=24):
    if alpha <= 0.01 or tt <= 0:
        return
    D._pop_pill(img, cx, cy, text, fsz, mix(WHITE, col, 0.12), alpha, tt, fg=mix(col, INK, 0.35), dot=False)


def _label11(img, cx, cy, text, col, alpha, fsz=24, name=FS):
    if alpha > 0.02:
        paste_c(img, cx, cy, text, font(name, round(fsz * K_TXT)), col, alpha)


# =============================================================== B. gerak & cahaya
_GLOW = {}


def _glow11(img, cx, cy, r, col, alpha):
    """Cahaya lembut (bloom palsu) - sprite radial ter-cache, ditempel additif-ish."""
    if alpha <= 0.01 or r <= 2:
        return
    key = (int(r), col, round(D.SS, 3))
    spr = _GLOW.get(key)
    if spr is None:
        n = max(8, int(S(r) * 2))
        m = Image.radial_gradient("L").resize((n, n), Image.BICUBIC)
        # v12 fix: radial_gradient bernilai 128 di tepi tengah sisi (bukan 255) -> alpha harus 0 pada lingkaran
        # dalam, kalau tidak tepi kotak sprite terlihat di atas latar gelap
        m = m.point(lambda v: int(255 * max(0.0, 1 - v / 128.0) ** 2.2))
        spr = (Image.new("RGB", (n, n), col), m)
        _GLOW[key] = spr
    rgb, m = spr
    a = m.point(lambda v: int(v * clamp(alpha)))
    img.paste(rgb, (int(S(cx) - rgb.width / 2), int(S(cy) - rgb.height / 2)), a)


def _bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


def _pline(img, pts, col, width, alpha):
    if alpha <= 0.01 or len(pts) < 2:
        return
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    bx = D._box(img, min(xs) - width * 2, min(ys) - width * 2, max(xs) + width * 2, max(ys) + width * 2)
    if bx is None:
        return
    X0, Y0, X1, Y1 = bx
    lay = Image.new("RGBA", (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    ox, oy = X0 / D.SS, Y0 / D.SS
    P = [(S(x - ox), S(y - oy)) for x, y in pts]
    wd = max(1, int(S(width)))
    dd.line(P, fill=col + (255,), width=wd, joint="curve")
    rr = wd / 2
    for (x, y) in (P[0], P[-1]):
        dd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (255,))
    D._put_at(img, lay, X0, Y0, alpha)


def _panah11(img, p0, p2, alpha, prog, col, width=9, lengkung=0.25, head=26):
    """Panah melengkung yang menggambar diri (prog 0..1)."""
    if alpha <= 0.01 or prog <= 0:
        return
    mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2
    dx, dy = p2[0] - p0[0], p2[1] - p0[1]
    p1 = (mx - dy * lengkung, my + dx * lengkung)
    u1 = clamp(prog)
    n = max(3, int(24 * u1))
    pts = [_bez(p0, p1, p2, u1 * i / n) for i in range(n + 1)]
    _pline(img, pts, col, width, alpha)
    if u1 > 0.85:
        a = pts[-1]; b = pts[-3]
        ang = math.atan2(a[1] - b[1], a[0] - b[0])
        hk = head * eob(clamp((u1 - 0.85) / 0.15), 2.0)
        poly_on(img, [a, (a[0] - hk * math.cos(ang - 0.5), a[1] - hk * math.sin(ang - 0.5)),
                      (a[0] - hk * math.cos(ang + 0.5), a[1] - hk * math.sin(ang + 0.5))], col, alpha)


def _gelom11(img, x0, x1, y, amp, lam, fase, col, width, alpha, amp_fn=None, step=6):
    """Gelombang sinus berjalan. amp_fn(x) -> faktor amplitudo (untuk peredaman)."""
    if alpha <= 0.01 or x1 <= x0:
        return
    pts = []
    x = x0
    while x <= x1:
        a = amp * (amp_fn(x) if amp_fn else 1.0)
        pts.append((x, y + a * math.sin((x - x0) / lam * 2 * math.pi - fase)))
        x += step
    _pline(img, pts, col, width, alpha)


def _busur11(img, cx, cy, r, col, width, alpha, a0=-50, a1=50):
    """Busur (derajat, 0 = kanan). Dipakai untuk pancaran sinyal."""
    if alpha <= 0.01 or r <= 2:
        return
    bx = D._box(img, cx - r - width, cy - r - width, cx + r + width, cy + r + width)
    if bx is None:
        return
    X0, Y0, X1, Y1 = bx
    lay = Image.new("RGBA", (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    ox, oy = X0 / D.SS, Y0 / D.SS
    dd.arc([S(cx - ox - r), S(cy - oy - r), S(cx - ox + r), S(cy - oy + r)], a0, a1,
           fill=col + (255,), width=max(1, int(S(width))))
    D._put_at(img, lay, X0, Y0, alpha)


def _pancar11(img, cx, cy, tg, col, alpha, rmax=160, n=3, a0=-55, a1=55, width=7, kec=0.7):
    """Busur-busur yang berjalan keluar (sinyal memancar)."""
    for k in range(n):
        ph = (tg * kec + k / float(n)) % 1.0
        _busur11(img, cx, cy, 24 + rmax * ph, col, width, alpha * (1 - ph) ** 1.2, a0, a1)


def _partikel11(img, cx, cy, tt, col, alpha, n=12, jarak=120, seed=3):
    """Ledakan partikel sekali saat elemen muncul (tt = detik sejak muncul)."""
    if alpha <= 0.01 or tt <= 0 or tt > 0.7:
        return
    u = tt / 0.7
    for k in range(n):
        a = (k / n) * 2 * math.pi + seed
        dd = jarak * eo(u) * (0.7 + 0.3 * ((k * 7 + seed) % 5) / 4)
        r = 7 * (1 - u) + 2
        x, y = cx + dd * math.cos(a), cy + dd * math.sin(a)
        if k % 3 == 0:
            D.star4(img, x, y, r * 1.8, mix(col, WHITE, 0.25), alpha * (1 - u))
        else:
            dot_on(img, x, y, r, col, alpha * (1 - u))


# =============================================================== C. objek
def _bars11(img, x, ybase, n_on, alpha, col, w=12, gap=5, hmax=40, n=4, off=None):
    off = off or mix(CREAM, INK, 0.25)
    for i in range(n):
        h = hmax * (i + 1) / n
        c = col if i < n_on else off
        rrect_on(img, x + i * (w + gap), ybase - h, x + i * (w + gap) + w, ybase, min(4, w / 3), c, alpha)


def _spinner11(img, cx, cy, r, tg, col, alpha, width=8):
    a = (tg * 360 * 1.1) % 360
    _busur11(img, cx, cy, r, mix(col, WHITE, 0.75), width, alpha, 0, 360)
    _busur11(img, cx, cy, r, col, width, alpha, a, a + 100)


def _hp11(img, cx, cy, w, h, alpha, tg, bars=4, spin=False, layar=None, gelap=False, bar_col=None):
    """HP modern: badan gelap, layar, status bar (sinyal + baterai), opsional loading."""
    if alpha <= 0.01:
        return
    D._bayang_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, alpha, blur=14, off=10)
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, w * 0.16, GELAP, alpha)
    scr = layar or ((40, 46, 60) if gelap else (250, 250, 252))
    m = w * 0.055
    rrect_on(img, cx - w / 2 + m, cy - h / 2 + m, cx + w / 2 - m, cy + h / 2 - m, w * 0.12, scr, alpha)
    rrect_on(img, cx - w * 0.12, cy - h / 2 + m + 8, cx + w * 0.12, cy - h / 2 + m + 8 + w * 0.06,
             w * 0.03, GELAP, alpha)
    top = cy - h / 2 + m + 14 + w * 0.03
    bw = max(5, w * 0.03)
    _bars11(img, cx + w / 2 - m - 18 - 4 * (bw + 3), top + w * 0.05, bars, alpha,
            bar_col or (INK if not gelap else WHITE), w=bw, gap=3, hmax=w * 0.07)
    if spin:
        _spinner11(img, cx, cy - h * 0.06, w * 0.12, tg, BLUE, alpha, width=max(4, w * 0.025))


def _menara11(img, cx, base, h, alpha, tg, col=None, nyala=1.0, pancar=True, pc=None, rmax=170):
    """BTS kisi: dua kaki, batang silang, panel antena, lampu merah berkedip."""
    if alpha <= 0.01:
        return
    col = col or mix(INK, CREAM, 0.12)
    top = base - h
    wb = h * 0.24
    line_on(img, (cx - wb, base), (cx - 6, top + 20), col, 7, alpha)
    line_on(img, (cx + wb, base), (cx + 6, top + 20), col, 7, alpha)
    n = 5
    for i in range(n):
        y1 = base - h * (i / n) * 0.92
        y2 = base - h * ((i + 1) / n) * 0.92
        w1 = wb * (1 - (i / n) * 0.92)
        w2 = wb * (1 - ((i + 1) / n) * 0.92)
        line_on(img, (cx - w1, y1), (cx + w2, y2), col, 3, alpha * 0.8)
        line_on(img, (cx + w1, y1), (cx - w2, y2), col, 3, alpha * 0.8)
        line_on(img, (cx - w2, y2), (cx + w2, y2), col, 3, alpha * 0.8)
    line_on(img, (cx, top + 20), (cx, top - 28), col, 5, alpha)
    for sx in (-1, 1):
        rrect_on(img, cx + sx * 20 - 8, top + 10, cx + sx * 20 + 8, top + 58, 4, col, alpha)
    blink = 0.5 + 0.5 * math.sin(tg * 4.0)
    if nyala > 0.05:
        _glow11(img, cx, top - 30, 30, (255, 90, 80), alpha * nyala * blink * 0.8)
    dot_on(img, cx, top - 30, 7, mix((120, 60, 60), (240, 70, 60), nyala * (0.4 + 0.6 * blink)), alpha)
    if pancar and nyala > 0.05:
        pc = pc or BLUE
        _pancar11(img, cx + 30, top + 34, tg, pc, alpha * nyala, rmax=rmax, a0=-50, a1=50)
        _pancar11(img, cx - 30, top + 34, tg + 0.17, pc, alpha * nyala, rmax=rmax, a0=130, a1=230)


def _router11(img, cx, cy, alpha, tg, col=None, s=1.0, pancar=True, kedip=1.0):
    col = col or GELAP
    w, h = 190 * s, 58 * s
    line_on(img, (cx - w * 0.32, cy - h / 2), (cx - w * 0.40, cy - h / 2 - 70 * s), col, 7 * s, alpha)
    line_on(img, (cx + w * 0.32, cy - h / 2), (cx + w * 0.40, cy - h / 2 - 70 * s), col, 7 * s, alpha)
    D._bayang_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, alpha, blur=8, off=5)
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 16 * s, col, alpha)
    for k in range(4):
        on = 0.5 + 0.5 * math.sin(tg * 6 + k * 1.7)
        dot_on(img, cx - w * 0.30 + k * w * 0.2, cy + 4, 5 * s,
               mix((70, 90, 80), (80, 230, 140), on * kedip), alpha)
    if pancar:
        _pancar11(img, cx, cy - h / 2 - 20 * s, tg, mix(BLUE, WHITE, 0.1), alpha * kedip,
                  rmax=150 * s, a0=-150, a1=-30, width=6 * s)


def _micro11(img, cx, cy, alpha, tg, nyala=0.0, s=1.0):
    w, h = 420 * s, 270 * s
    D._bayang_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, alpha, blur=12, off=8)
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 26 * s, (214, 216, 222), alpha,
             outline=mix(INK, CREAM, 0.35), width=4)
    wx0, wy0, wx1, wy1 = cx - w / 2 + 24 * s, cy - h / 2 + 26 * s, cx + w * 0.18, cy + h / 2 - 26 * s
    dalam = mix((48, 52, 64), (255, 170, 70), nyala * (0.75 + 0.25 * math.sin(tg * 9)))
    rrect_on(img, wx0, wy0, wx1, wy1, 16 * s, dalam, alpha)
    if nyala > 0.05:
        _glow11(img, (wx0 + wx1) / 2, (wy0 + wy1) / 2, 150 * s, (255, 180, 90), alpha * nyala * 0.55)
        ang = tg * 2.2
        pcx, pcy = (wx0 + wx1) / 2, wy1 - 34 * s
        ell(img, pcx - 70 * s, pcy - 12 * s, pcx + 70 * s, pcy + 12 * s, fill=(236, 228, 214), alpha=alpha * 0.9)
        bx = pcx + 34 * s * math.cos(ang)
        rrect_on(img, bx - 26 * s, pcy - 46 * s, bx + 26 * s, pcy - 6 * s, 10 * s, (205, 120, 70), alpha)
    px = cx + w * 0.34
    rrect_on(img, px - 44 * s, cy - h / 2 + 30 * s, px + 44 * s, cy - h / 2 + 76 * s, 8 * s,
             (40, 60, 50) if nyala < 0.5 else (30, 200, 120), alpha)
    for r_ in range(3):
        for c_ in range(3):
            dot_on(img, px - 26 * s + c_ * 26 * s, cy + r_ * 30 * s, 8 * s, mix(INK, CREAM, 0.45), alpha)


def _orang11(img, cx, cy, s, col, alpha):
    dot_on(img, cx, cy - 22 * s, 11 * s, col, alpha)
    rrect_on(img, cx - 15 * s, cy - 8 * s, cx + 15 * s, cy + 26 * s, 12 * s, col, alpha)


def _baterai11(img, cx, cy, w, h, frac, alpha, col=None):
    frac = clamp(frac)
    col = col or (GREEN if frac > 0.5 else AMBER if frac > 0.2 else RED)
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 14, WHITE, alpha,
             outline=GELAP, width=6)
    rrect_on(img, cx + w / 2, cy - h * 0.18, cx + w / 2 + 14, cy + h * 0.18, 5, GELAP, alpha)
    if frac > 0.02:
        rrect_on(img, cx - w / 2 + 12, cy - h / 2 + 12, cx - w / 2 + 12 + (w - 24) * frac,
                 cy + h / 2 - 12, 8, col, alpha)


def _dinding11(img, x, y0, y1, tebal, col, alpha, pola="bata"):
    rrect_on(img, x - tebal / 2, y0, x + tebal / 2, y1, 6, col, alpha)
    garis = mix(col, INK, 0.25)
    if pola == "bata":
        yy, k = y0 + 22, 0
        while yy < y1 - 4:
            line_on(img, (x - tebal / 2 + 2, yy), (x + tebal / 2 - 2, yy), garis, 2, alpha * 0.7)
            xx = x + (tebal * 0.2 if k % 2 else -tebal * 0.2)
            line_on(img, (xx, yy - 22), (xx, yy), garis, 2, alpha * 0.7)
            yy += 22; k += 1
    elif pola == "besi":
        for k in range(int((y1 - y0) / 26)):
            yy = y0 + 13 + k * 26
            line_on(img, (x - tebal / 2 + 3, yy + 8), (x + tebal / 2 - 3, yy - 8), mix(col, WHITE, 0.3), 3, alpha)
    elif pola == "kaca":
        line_on(img, (x - tebal * 0.2, y0 + 30), (x + tebal * 0.2, y0 + 80), WHITE, 3, alpha * 0.8)


# =============================================================== E. BEAT (SFX + kamera)
# (fraksi durasi adegan, jenis). Fungsi gambar di bawah memakai angka yang SAMA.
BEATS = {
    "intro_sinyal42": [(0.02, "impact"), (0.20, "pop"), (0.36, "glitch"), (0.52, "pop"), (0.56, "pop"),
                       (0.66, "riser_end"), (0.70, "impact")],
    "garis42": [(0.05, "pop"), (0.08, "pop"), (0.11, "pop"), (0.14, "pop"), (0.20, "swish"),
                (0.26, "impact"), (0.38, "whoosh"), (0.52, "pop"), (0.76, "impact")],
    "antre42": [(0.05, "whoosh"), (0.30, "pop"), (0.36, "swish"), (0.42, "swish"), (0.48, "swish"),
                (0.60, "tick"), (0.76, "impact")],
    "tembus42": [(0.05, "whoosh"), (0.26, "thud"), (0.34, "thud"), (0.42, "thud"), (0.56, "pop"),
                 (0.72, "door"), (0.80, "impact")],
    "wifi42": [(0.05, "pop"), (0.14, "whoosh"), (0.40, "whoosh"), (0.55, "thud"), (0.70, "swish"),
               (0.80, "ding"), (0.86, "ding")],
    "micro42": [(0.04, "impact"), (0.30, "whoosh"), (0.44, "impact"), (0.66, "click"), (0.69, "zap"),
                (0.74, "glitch"), (0.80, "pop")],
    "padam42": [(0.12, "click"), (0.16, "boom"), (0.30, "pop"), (0.55, "glitch"), (0.58, "boom"),
                (0.66, "whoosh"), (0.80, "impact")],
    "tips42": [(0.06, "swish"), (0.10, "ding"), (0.28, "swish"), (0.32, "ding"), (0.46, "swish"),
               (0.50, "ding"), (0.64, "swish"), (0.68, "ding"), (0.84, "click")],
    "rangkuman42": [(0.05, "swish"), (0.20, "pop"), (0.35, "pop"), (0.50, "pop"), (0.70, "impact"),
                    (0.74, "whoosh")],
}
BEAT_KAMERA = {"impact": 0.045, "boom": 0.035, "thud": 0.020, "door": 0.025}


def _b(nama, i):
    return BEATS[nama][i][0]


def events(scenes):
    """Semua event suara + kamera dari timeline (detik absolut)."""
    global N_FAKTA
    nf = sum(1 for s_ in scenes if re.match(r"f\d+$", str(s_.get("id", ""))))
    if nf:
        N_FAKTA = nf
    ev = []
    # hanya episode v11 (punya visual ber-BEAT atau transisi v11) -> episode lama tetap sunyi
    if not any(s_.get("visual") in BEATS or str(s_.get("trans") or "").lower() in TRANSISI
               for s_ in scenes):
        return ev
    for i, sc in enumerate(scenes):
        st, dur = sc["start"], sc["dur"]
        tr = str(sc.get("trans") or "").lower()
        try:
            import mesin_v12 as _M12v
            fn12 = _M12v.EVENTS12.get(sc.get("visual", ""))
        except Exception:                      # noqa: BLE001
            fn12 = None
        if fn12:
            # v12: semua event dari CUE kata (satu sumber kebenaran untuk gambar + SFX)
            ev += fn12(sc)
            if sc.get("type") == "fact" and sc.get("badge"):
                ev.append((st + 0.12, "swish_up", 0.55))
            continue
        if i > 0:
            if tr == "punch":
                ev += [(st - 0.30, "whoosh", 0.8), (st - 0.02, "impact", 0.7)]
            elif tr == "slide":
                ev += [(st - 0.22, "swish", 1.0)]
            elif tr == "glitch":
                ev += [(st - 0.06, "glitch", 0.9)]
            else:
                ev += [(st - 0.25, "whoosh", 0.6)]
        if sc.get("type") == "fact" and sc.get("badge"):
            ev.append((st + 0.12, "swish_up", 0.55))
        for fr, jenis in BEATS.get(sc.get("visual", ""), []):
            if jenis == "riser_end":
                ev.append((st + fr * dur - 1.1, "riser", 0.7))
            else:
                ev.append((st + fr * dur, jenis, 1.0))
        if sc.get("type") == "outro":
            ev += [(st + 0.80, "pop", 0.9), (st + 1.10, "ding", 0.8)]
    return sorted(e for e in ev if e[0] >= 0)


def punch_kamera(tl, evs):
    """Dorongan kamera singkat di event berat (impact/boom/thud) - peluruhan 0,28 s."""
    k = 0.0
    for t, jenis, g in evs:
        a = BEAT_KAMERA.get(jenis)
        if not a:
            continue
        d = tl - t
        if 0 <= d < 0.35:
            k = max(k, a * g * math.exp(-d / 0.09) * (1 - d / 0.35))
    return k


# =============================================================== D. transisi
def _kromatik(img, px):
    """Aberasi kromatik: kanal merah & biru digeser berlawanan (px dalam piksel render)."""
    px = int(round(px))
    if px < 1:
        return img
    r, g, b = img.split()
    r = ImageChops.offset(r, px, 0)
    b = ImageChops.offset(b, -px, 0)
    return Image.merge("RGB", (r, g, b))


def _zoom(img, k, ax=0.5, ay=0.46):
    if abs(k - 1) < 0.002:
        return img
    w, h = img.size
    cw, ch = w / k, h / k
    x0 = (w - cw) * ax
    y0 = (h - ch) * ay
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.BICUBIC)


def _blur_arah(img, px, vertikal=False):
    """Blur gerak satu arah murah: kecilkan satu sumbu lalu besarkan lagi."""
    if px < 2:
        return img
    w, h = img.size
    f = max(2, int(px))
    if vertikal:
        return img.resize((w, max(8, h // f)), Image.BILINEAR).resize((w, h), Image.BILINEAR)
    return img.resize((max(8, w // f), h), Image.BILINEAR).resize((w, h), Image.BILINEAR)


def trans_punch(prev, img, p, acc):
    """Dorong masuk: adegan lama zoom-in cepat + blur, kilat putih, adegan baru mendarat."""
    if p < 0.5:
        u = p / 0.5
        out = _zoom(prev, 1.0 + 0.35 * u ** 2)
        out = _blur_arah(out, 18 * u ** 2, vertikal=True)
        fl = u ** 3
    else:
        u = (p - 0.5) / 0.5
        k = 1.0 + 0.16 * (1 - eob(u, 1.8))
        out = _zoom(img, max(0.97, k))
        fl = (1 - u) ** 2.5
    if fl > 0.02:
        out = Image.blend(out, Image.new("RGB", out.size, mix(WHITE, acc, 0.10)), 0.85 * fl)
    return _kromatik(out, S(9) * math.sin(math.pi * p))


def trans_slide(prev, img, p, acc):
    """Whip elastis ke kiri: blur gerak di tengah, adegan baru mendarat dengan pegas."""
    w, h = img.size
    u = esmooth(p)
    over = 1.0 - eob(p, 1.3)
    x_new = int(w * over) if p < 1 else 0
    canvas = Image.new("RGB", (w, h), CREAM)
    canvas.paste(prev, (x_new - w, 0))
    canvas.paste(img, (x_new, 0))
    kec = math.sin(math.pi * min(1.0, u * 1.2))
    canvas = _blur_arah(canvas, 26 * kec)
    if 0 < x_new < w:
        dd = ImageDraw.Draw(canvas)
        dd.rectangle([x_new - S(5), 0, x_new + S(5), h], fill=mix(acc, WHITE, 0.30))
    return _kromatik(canvas, S(7) * kec)


def trans_glitch(prev, img, p, acc, seed=11):
    """Glitch: irisan horizontal bergeser + pecah RGB + blok aksen, lalu stabil."""
    import random
    src = prev if p < 0.45 else img
    inten = math.sin(math.pi * clamp(p)) ** 0.8
    rnd = random.Random(seed + int(p * 14))
    out = src.copy()
    w, h = out.size
    for _ in range(int(3 + 7 * inten)):
        y0 = rnd.randint(0, h - 10)
        hh = rnd.randint(int(S(8)), int(S(90)))
        dx = int(rnd.uniform(-1, 1) * S(70) * inten)
        band = src.crop((0, y0, w, min(h, y0 + hh)))
        out.paste(band, (dx, y0))
    if inten > 0.35:
        for _ in range(2):
            x0 = rnd.randint(0, w - 50)
            y0 = rnd.randint(0, h - 50)
            ImageDraw.Draw(out).rectangle([x0, y0, x0 + rnd.randint(40, int(S(260))), y0 + rnd.randint(6, int(S(26)))],
                                          fill=mix(acc, WHITE, rnd.uniform(0.0, 0.5)))
    return _kromatik(out, S(14) * inten)


def trans_zoomthru(prev, img, p, acc):
    """v2026: dorong MENEMBUS adegan lama (blur radial) -> kilat aksen -> adegan baru mendarat."""
    return _kromatik(FX.trans_dua(prev, img, p, "zoomthru", acc), S(6) * math.sin(math.pi * p))


def trans_tinta(prev, img, p, acc):
    """v2026: sapuan bentuk bertepi bergelombang + garis aksen (wipe bentuk ala editor)."""
    return FX.trans_dua(prev, img, p, "tinta", acc)


def trans_cahaya(prev, img, p, acc):
    """v2026: crossfade + kebocoran cahaya hangat yang menyapu (light leak)."""
    return FX.trans_dua(prev, img, p, "cahaya", acc)


TRANSISI = {"punch": trans_punch, "slide": trans_slide, "glitch": trans_glitch,
            "zoomthru": trans_zoomthru, "tinta": trans_tinta, "cahaya": trans_cahaya}


# =============================================================== adegan Ep42 (sinyal)
N_FAKTA = 7          # diisi render dari timeline (jumlah adegan fakta f1..fN)
GESER = -70          # konten adegan fakta v11 dinaikkan: isi zona kosong atas, jauhi UI bawah
K_TXT = 1.12         # label/stiker v11 lebih besar dari mesin lama (layar HP)


def _bab11(img, sc, accent, tl, al, y=268):
    """Penanda bab 'FAKTA 3/7' + segmen progres: retensi (penonton tahu sisa isi)."""
    m = re.match(r"f(\d+)$", str(sc.get("id", "")))
    if not m or al <= 0.01:
        return
    n, tot = int(m.group(1)), max(int(m.group(1)), N_FAKTA)
    q = eob(seg(tl, 0.02, 0.40), 1.8)
    if q <= 0:
        return
    f = font(FB, 26)
    txt = f"FAKTA {n}/{tot}"
    wt = tw(txt, f) + 52
    rrect_on(img, 540 - wt / 2, y - 28 * q, 540 + wt / 2, y + 28 * q, 28, accent, al * clamp(q))
    _note("bab", 540 - wt / 2, y - 28, 540 + wt / 2, y + 28, txt)
    paste_c(img, 540, y, txt, f, WHITE, al * clamp(q), scale=0.8 + 0.2 * clamp(q))
    sw, gap = 46, 10
    x0 = 540 - (tot * sw + (tot - 1) * gap) / 2
    for k in range(tot):
        qk = esmooth(seg(tl, 0.15 + k * 0.03, 0.35 + k * 0.03))
        if qk <= 0:
            continue
        col = accent if k < n else mix(CREAM, INK, 0.16)
        if k == n - 1:
            col = mix(accent, WHITE, 0.25 * (0.5 + 0.5 * math.sin(tl * 5)))
        rrect_on(img, x0 + k * (sw + gap), y + 42, x0 + k * (sw + gap) + sw * qk, y + 51, 5, col, al)


def _hdr(img, sc, accent, tl, al):
    _bab11(img, sc, accent, tl, al)
    _judul11(img, sc.get("badge", ""), accent, tl, al, y=470, hl=sc.get("hl", ""), fsz=64, maxw=930)


def sc_intro_sinyal42(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "intro_sinyal42"
    L = sc.get("lines") or ["SINYAL PENUH,", "TAPI KOK LEMOT?"]
    _judul11(img, L[0], INK, tl, al, y=470, fsz=70, t0=0.05)
    _judul11(img, L[1], accent, tl, al, y=575, fsz=70, t0=0.30, hl="LEMOT?")
    q = esmooth(seg(tl, 0.20, 0.75))
    if q <= 0.01:
        return
    # menara jauh di belakang (tersangka)
    qt = esmooth(_dw(tl, dur, _b(N, 5) - 0.02, _b(N, 6)))
    _menara11(img, 860, 1470 + dy, 420, al * (0.35 + 0.65 * qt) * q, tg,
              col=mix(INK, CREAM, 0.55 - 0.4 * qt), nyala=qt, pc=accent)
    if qt > 0:
        _glow11(img, 860, 1200 + dy, 230, mix(accent, WHITE, 0.6), al * qt * 0.35)
    # HP besar
    cy = 1150 + dy + (1 - eob(q, 1.5)) * 260
    _hp11(img, 430, cy, 380, 700, al * q, tg, bars=4, spin=False)
    # layar: pemutar video tertahan
    rrect_on(img, 270, cy - 240, 590, cy - 60, 22, (34, 38, 50), al * q)
    _spinner11(img, 430, cy - 150, 38, tg, WHITE, al * q, width=8)
    rrect_on(img, 270, cy - 40, 590, cy - 30, 5, mix(CREAM, INK, 0.18), al * q)
    rrect_on(img, 270, cy - 40, 270 + 320 * 0.22, cy - 30, 5, RED, al * q)
    # batang sinyal besar berkedip (penuh)
    qb = esmooth(_dw(tl, dur, _b(N, 1), _b(N, 1) + 0.06))
    if qb > 0:
        rrect_on(img, 260, cy + 20, 600, cy + 150, 26, mix(WHITE, BLUE, 0.08), al * qb,
                 outline=mix(BLUE, WHITE, 0.4), width=3)
        _bars11(img, 300, cy + 125, 4, al * qb, mix(BLUE, INK, 0.1), w=26, gap=10, hmax=80)
        _label11(img, 515, cy + 62, "PENUH", mix(BLUE, INK, 0.25), al * qb, fsz=30, name=FB)
        _label11(img, 515, cy + 104, "4 garis", MUTED, al * qb, fsz=22)
    # gelembung pesan gagal
    qm = esmooth(_dw(tl, dur, _b(N, 2), _b(N, 2) + 0.05))
    if qm > 0:
        rrect_on(img, 280, cy + 190, 580, cy + 262, 30, mix(WHITE, RED, 0.10), al * qm,
                 outline=mix(RED, WHITE, 0.4), width=3)
        _label11(img, 430, cy + 226, "Mengirim...  gagal", RED, al * qm, fsz=22, name=FB)
    # tanda tanya melompat
    for k, (x, y, rot) in enumerate(((140, 860, -12), (650, 760, 10))):
        tt = tl - _b(N, 3 + k) * dur
        _stiker11(img, x, y + dy, "?", al, tt, bg=AMBER, fsz=54, rot=rot, tg=tg)
    # panah ke menara: tersangka
    tt = tl - _b(N, 6) * dur
    if tt > 0:
        _panah11(img, (690, 1020 + dy), (820, 1110 + dy), al, clamp(tt / 0.4), accent, width=8)
        _stiker11(img, 700, 950 + dy, "TERSANGKANYA?", al, tt, bg=accent, fsz=28, rot=5, tg=tg)


def sc_garis42(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "garis42"
    _hdr(img, sc, accent, tl, al)
    # kiri: batang sinyal raksasa = KEKUATAN
    for i in range(4):
        tt = tl - _b(N, i) * dur
        if tt <= 0:
            continue
        k = eob(clamp(tt / 0.35), 2.2)
        h = 70 + i * 55
        x = 150 + i * 62
        rrect_on(img, x, 1010 + dy - h * k, x + 44, 1010 + dy, 10, mix(accent, INK, 0.05 * i), al)
        _partikel11(img, x + 22, 1010 + dy - h, tt, accent, al, n=6, jarak=50, seed=i)
    qa = esmooth(_dw(tl, dur, _b(N, 3), _b(N, 3) + 0.05))
    _label11(img, 262, 1060 + dy, "KEKUATAN", mix(accent, INK, 0.3), al * qa, fsz=30, name=FB)
    # kanan: spidometer = KECEPATAN
    qs = esmooth(_dw(tl, dur, _b(N, 4), _b(N, 4) + 0.05))
    if qs > 0:
        turun = esmooth(_dw(tl, dur, _b(N, 8), _b(N, 8) + 0.05))
        frac = (0.78 + 0.05 * math.sin(tg * 3)) * (1 - turun) + 0.12 * turun
        D._meter_on(img, 800, 990 + dy, 150 * (0.6 + 0.4 * eob(qs)), frac,
                    mix(GREEN, RED, turun), al * qs)
        _label11(img, 800, 1060 + dy, "KECEPATAN", mix(INK, CREAM, 0.1), al * qs, fsz=30, name=FB)
    # tanda tidak sama besar
    tt = tl - _b(N, 5) * dur
    if tt > 0:
        k = eob(clamp(tt / 0.3), 2.5)
        paste_c(img, 540, 900 + dy, "≠" if False else "=/=", font(FB, 64), RED, al, scale=0.6 + 0.4 * k)
        _partikel11(img, 540, 900 + dy, tt, RED, al, n=10, jarak=90)
    # bawah: HP "mendengar" menara
    qh = esmooth(_dw(tl, dur, _b(N, 6), _b(N, 6) + 0.06))
    if qh > 0:
        rrect_on(img, 90, 1150 + dy, 990, 1560 + dy, 40, mix(WHITE, CREAM, 0.3), al * qh,
                 outline=mix(accent, WHITE, 0.6), width=3)
        _hp11(img, 240, 1370 + dy, 150, 280, al * qh, tg, bars=4)
        _menara11(img, 830, 1520 + dy, 300, al * qh, tg, pc=accent, rmax=120)
        for k in range(3):
            fase = tg * 5 + k
            _gelom11(img, 330, 720, 1330 + dy + k * 34, 12 * (1 - k * 0.25), 70, fase,
                     mix(accent, WHITE, 0.2 + 0.25 * k), 5, al * qh)
        tt = tl - _b(N, 7) * dur
        _stiker11(img, 525, 1245 + dy, "HP MENDENGAR MENARA", al, tt, bg=accent, fsz=26, rot=-3, tg=tg)
        _label11(img, 560, 1505 + dy, "terdengar jelas = sinyal kuat", MUTED, al * qh, fsz=24)
    tt = tl - _b(N, 8) * dur
    _stiker11(img, 540, 1615 + dy, "BELUM TENTU CEPAT!", al, tt, bg=RED, fsz=36, rot=-4, tg=tg)


def sc_antre42(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "antre42"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(_dw(tl, dur, _b(N, 0), _b(N, 0) + 0.06))
    if q <= 0.01:
        return
    tcx, tbase = 540, 1060 + dy
    _glow11(img, tcx, tbase - 260, 200, mix(accent, WHITE, 0.55), al * q * 0.5)
    _menara11(img, tcx, tbase, 330, al * q, tg, pc=accent, rmax=150)
    # kerumunan bertambah
    naik = esmooth(_dw(tl, dur, 0.18, 0.66))
    n = int(6 + 70 * naik)
    for k in range(n):
        a = (k * 2.39996) % (2 * math.pi)
        rr = 1.0 - (k % 9) / 12.0
        x = tcx + math.cos(a) * 380 * rr
        y = 1270 + dy + math.sin(a) * 110 * rr + (k % 3) * 8
        if x < 90 or x > 990:
            continue
        muncul = clamp((naik * 76 - k + 6) / 3)
        if k % 7 == 0:
            line_on(img, (tcx, tbase - 250), (x, y - 30), mix(accent, CREAM, 0.7), 2, al * muncul * 0.5)
        _orang11(img, x, y, 0.9, mix(INK, accent, 0.25 + 0.15 * ((k * 5) % 3)), al * muncul)
    # stiker konteks
    for i, (txt, x, y, rot) in enumerate((("KONSER", 200, 800, -8), ("STADION", 880, 820, 7),
                                          ("MALAM HARI", 210, 960, 5))):
        tt = tl - _b(N, 2 + i) * dur
        _stiker11(img, x, y + dy, txt, al, tt, bg=[AMBER, accent, (90, 70, 150)][i], fsz=26, rot=rot, tg=tg)
    # hitungan orang + donat jatah
    qc = esmooth(_dw(tl, dur, _b(N, 1), _b(N, 1) + 0.05))
    if qc > 0:
        orang = int(10 + 990 * naik)
        _label11(img, 300, 1530 + dy, f"{orang:,}".replace(",", "."), mix(accent, INK, 0.2), al * qc, fsz=62, name=FB)
        _label11(img, 300, 1590 + dy, "orang di satu menara", MUTED, al * qc, fsz=22)
        jatah = 1.0 / (1.0 + 9 * naik)
        D._donut_on(img, 760, 1545 + dy, 78, jatah, RED if jatah < 0.3 else accent, al * qc, tg)
        _label11(img, 760, 1545 + dy, f"{int(round(jatah * 100))}%", mix(INK, CREAM, 0.1), al * qc, fsz=30, name=FB)
        _label11(img, 760, 1648 + dy, "jatahmu", MUTED, al * qc, fsz=22)
    tt = tl - _b(N, 6) * dur
    _stiker11(img, 540, 1440 + dy, "SINYAL PENUH, JATAH MENGECIL", al, tt, bg=RED, fsz=28, rot=-3, tg=tg)


_BAHAN = [("KACA", 0.85, (170, 205, 230), "kaca", 22), ("BETON", 0.45, (160, 150, 140), "bata", 56),
          ("BESI", 0.14, (90, 96, 110), "besi", 40)]


def sc_tembus42(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "tembus42"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(_dw(tl, dur, _b(N, 0), _b(N, 0) + 0.06))
    if q <= 0.01:
        return
    ymid = 980 + dy
    _menara11(img, 145, ymid + 170, 260, al * q, tg, pc=accent, rmax=90)
    xs = [380, 580, 780]
    muncul = [esmooth(_dw(tl, dur, _b(N, 1 + i), _b(N, 1 + i) + 0.04)) for i in range(3)]

    def amp_at(x):
        a = 1.0
        for i, xw in enumerate(xs):
            if x > xw:
                a *= (1.0 - (1.0 - _BAHAN[i][1]) * muncul[i])
        return a

    _gelom11(img, 200, 930, ymid, 62, 110, tg * 7, accent, 8, al * q, amp_fn=amp_at, step=5)
    _glow11(img, 200, ymid, 70, mix(accent, WHITE, 0.5), al * q * 0.6)
    for i, (nama, _, col, pola, tebal) in enumerate(_BAHAN):
        m = muncul[i]
        if m <= 0:
            continue
        yy0 = ymid - 150 - (1 - eob(m)) * 120
        _dinding11(img, xs[i], yy0, ymid + 150, tebal, col, al * m, pola)
        _label11(img, xs[i], ymid + 190, nama, mix(col, INK, 0.5), al * m, fsz=24, name=FB)
        pct = int(round(amp_at(xs[i] + 1) * 100))
        _label11(img, (xs[i] + (xs[i + 1] if i < 2 else 930)) / 2, ymid - 170, f"{pct}%",
                 mix(accent, INK, 0.3) if pct > 30 else RED, al * m, fsz=30, name=FB)
    _label11(img, 290, ymid - 170, "100%", mix(accent, INK, 0.3), al * q, fsz=30, name=FB)
    qa = esmooth(_dw(tl, dur, _b(N, 4), _b(N, 4) + 0.05))
    _label11(img, 540, ymid + 250, "makin tebal penghalang = makin lemah", MUTED, al * qa, fsz=26)
    # lift: pintu menutup, sinyal hilang
    ql = esmooth(_dw(tl, dur, _b(N, 5) - 0.06, _b(N, 5)))
    if ql > 0:
        lx, ly = 540, 1500 + dy
        rrect_on(img, lx - 170, ly - 170, lx + 170, ly + 170, 16, (120, 126, 138), al * ql, outline=GELAP, width=5)
        rrect_on(img, lx - 150, ly - 150, lx + 150, ly + 150, 8, (238, 236, 230), al * ql)
        _hp11(img, lx, ly, 120, 220, al * ql, tg, bars=0)
        tutup = esmooth(_dw(tl, dur, _b(N, 5) - 0.02, _b(N, 5) + 0.03))
        for s_ in (-1, 1):
            x_in = lx + s_ * 150 * (1 - tutup)
            rrect_on(img, min(x_in, lx + s_ * 150), ly - 150, max(x_in, lx + s_ * 150), ly + 150, 4,
                     (176, 182, 194), al * ql * (1.0 if tutup > 0.02 else 0))
        _label11(img, lx - 230, ly - 120, "LIFT", GELAP, al * ql, fsz=26, name=FB)
        tt = tl - _b(N, 6) * dur
        _stiker11(img, lx, ly + 205, "SINYAL LANGSUNG HILANG", al, tt, bg=RED, fsz=28, rot=-3, tg=tg)


def sc_wifi42(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "wifi42"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(_dw(tl, dur, _b(N, 0), _b(N, 0) + 0.05))
    if q <= 0.01:
        return
    _router11(img, 180, 960 + dy, al * q, tg, s=0.8)
    teal, ungu = (31, 122, 107), accent
    # jalur 2,4 GHz: gelombang panjang, jauh
    qa = esmooth(_dw(tl, dur, _b(N, 1), _b(N, 1) + 0.10))
    if qa > 0:
        x1 = 300 + 630 * qa
        _gelom11(img, 300, x1, 840 + dy, 30, 150, tg * 5, teal, 8, al,
                 amp_fn=lambda x: 1.0 - 0.35 * (x - 300) / 630)
        _chip11(img, 380, 770 + dy, "2,4 GHz", teal, al, qa * 3, fsz=26)
        _label11(img, 760, 770 + dy, "JAUH - lebih lambat", mix(teal, INK, 0.3), al * qa, fsz=26, name=FB)
    # jalur 5 GHz: gelombang pendek, cepat, kalah dinding
    qb = esmooth(_dw(tl, dur, _b(N, 2), _b(N, 2) + 0.08))
    if qb > 0:
        tembok = esmooth(_dw(tl, dur, _b(N, 3) - 0.02, _b(N, 3)))
        xe = 300 + (660 - 300) * qb if tembok < 0.5 else 660
        _gelom11(img, 300, min(xe, 650), 1060 + dy, 26, 48, tg * 11, ungu, 7, al)
        if tembok > 0:
            _dinding11(img, 690, 980 + dy, 1140 + dy, 40, (160, 150, 140), al * tembok, "bata")
            _gelom11(img, 715, 920, 1060 + dy, 6, 48, tg * 11, ungu, 5, al * tembok * 0.5)
            _partikel11(img, 668, 1060 + dy, tl - _b(N, 3) * dur, ungu, al, n=8, jarak=60)
        _chip11(img, 380, 1140 + dy, "5 GHz", ungu, al, qb * 3, fsz=26)
        _label11(img, 800, 1180 + dy, "CEPAT - kalah dinding", mix(ungu, INK, 0.3), al * qb, fsz=26, name=FB)
    # denah rumah: dekat pilih 5, jauh pilih 2,4
    qd = esmooth(_dw(tl, dur, _b(N, 4), _b(N, 4) + 0.06))
    if qd > 0:
        y0 = 1260 + dy
        rrect_on(img, 110, y0, 970, y0 + 330, 20, mix(WHITE, CREAM, 0.4), al * qd, outline=GELAP, width=5)
        line_on(img, (520, y0), (520, y0 + 330), GELAP, 8, al * qd)
        _router11(img, 250, y0 + 230, al * qd, tg, s=0.55)
        _label11(img, 315, y0 + 40, "dekat router", MUTED, al * qd, fsz=22)
        _label11(img, 745, y0 + 40, "kamar jauh", MUTED, al * qd, fsz=22)
        _hp11(img, 420, y0 + 190, 90, 160, al * qd, tg, bars=4)
        _hp11(img, 830, y0 + 190, 90, 160, al * qd, tg, bars=3)
        tt = tl - _b(N, 5) * dur
        _stiker11(img, 420, y0 + 300, "PILIH 5", al, tt, bg=ungu, fsz=28, rot=-5, tg=tg)
        tt = tl - _b(N, 6) * dur
        _stiker11(img, 740, y0 + 300, "PILIH 2,4", al, tt, bg=teal, fsz=28, rot=4, tg=tg)


def sc_micro42(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "micro42"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(_dw(tl, dur, _b(N, 0), _b(N, 0) + 0.05))
    if q <= 0.01:
        return
    nyala = esmooth(_dw(tl, dur, _b(N, 3), _b(N, 3) + 0.03))
    _micro11(img, 330, 880 + dy - (1 - eob(q)) * 100, al * q, tg, nyala=nyala, s=0.9)
    goyah = 0.35 + 0.65 * abs(math.sin(tg * 23)) if nyala > 0.5 else 1.0
    _router11(img, 820, 930 + dy, al * q, tg, s=0.85, kedip=goyah)
    if nyala > 0:
        for k in range(3):
            _gelom11(img, 540, 710, 860 + dy + k * 40, 14, 44, tg * 12 + k, mix(accent, WHITE, 0.2 * k), 5,
                     al * nyala * 0.8)
        tt = tl - _b(N, 5) * dur
        if 0 < tt < 1.4:
            _glow11(img, 700, 900 + dy, 110, (255, 220, 120), al * (1 - tt / 1.4) * 0.8)
    # penggaris frekuensi
    qr = esmooth(_dw(tl, dur, _b(N, 1), _b(N, 1) + 0.08))
    if qr > 0:
        y = 1300 + dy
        x0, x1 = 150, 930
        line_on(img, (x0, y), (x0 + (x1 - x0) * qr, y), GELAP, 6, al)
        for k in range(11):
            xx = x0 + (x1 - x0) * k / 10
            if xx <= x0 + (x1 - x0) * qr:
                line_on(img, (xx, y - (18 if k % 5 == 0 else 10)), (xx, y), GELAP, 3, al)
        _label11(img, x0, y + 40, "2,40", MUTED, al * qr, fsz=22)
        _label11(img, (x0 + x1) / 2, y + 40, "2,45", MUTED, al * qr, fsz=22)
        _label11(img, x1, y + 40, "2,50 GHz", MUTED, al * qr, fsz=22)
        # pita wifi 2,400-2,4835
        bx1 = x0 + (x1 - x0) * 0.835
        rrect_on(img, x0, y - 110, x0 + (bx1 - x0) * qr, y - 40, 14, mix(BLUE, WHITE, 0.55), al * 0.9)
        _label11(img, (x0 + bx1) / 2, y - 75, "WIFI", mix(BLUE, INK, 0.3), al * qr, fsz=26, name=FB)
        # pin microwave 2,45 jatuh ke dalam pita
        tt = tl - _b(N, 2) * dur
        if tt > 0:
            px = (x0 + x1) / 2
            py = y - 150 - 160 * (1 - eob(clamp(tt / 0.35), 2.0))
            poly_on(img, [(px - 22, py - 40), (px + 22, py - 40), (px, py + 10)], RED, al)
            dot_on(img, px, py - 52, 26, RED, al)
            dot_on(img, px, py - 52, 10, WHITE, al)
            _label11(img, px, py - 104, "MICROWAVE 2,45", RED, al, fsz=24, name=FB)
            _partikel11(img, px, y - 75, tt - 0.3, RED, al, n=12, jarak=110)
    tt = tl - _b(N, 6) * dur
    if tt > 0:
        _hp11(img, 820, 1500 + dy, 110, 200, al, tg, bars=3, spin=True)
        _stiker11(img, 480, 1500 + dy, "WIFI TERSENDAT!", al, tt, bg=RED, fsz=34, rot=-4, tg=tg)


def sc_padam42(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "padam42"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, 0.2, 0.7))
    if q <= 0.01:
        return
    padam_pln = esmooth(_dw(tl, dur, _b(N, 0), _b(N, 0) + 0.01))
    bat = 1.0 - esmooth(_dw(tl, dur, _b(N, 2), _b(N, 3)))
    mati = esmooth(_dw(tl, dur, _b(N, 3), _b(N, 3) + 0.03))
    # tiang PLN + bohlam
    line_on(img, (120, 1260 + dy), (120, 830 + dy), mix(INK, CREAM, 0.3), 8, al * q)
    line_on(img, (120, 850 + dy), (250, 880 + dy), mix(INK, CREAM, 0.4), 3, al * q * (1 - padam_pln * 0.7))
    lamp = 1.0 - padam_pln
    if lamp > 0.05:
        _glow11(img, 120, 790 + dy, 80, KUNING, al * q * lamp * 0.8)
    dot_on(img, 120, 790 + dy, 26, mix((150, 150, 150), KUNING, lamp), al * q)
    _label11(img, 120, 730 + dy, "PLN", GELAP, al * q, fsz=22, name=FB)
    # menara A
    _menara11(img, 330, 1260 + dy, 360, al * q, tg, pc=accent, nyala=1.0 - mati,
              col=mix(INK, CREAM, 0.12 + 0.3 * mati))
    if mati > 0:
        D._check5_on(img, 330, 1020 + dy, 70, "cross", al, mati)
    # baterai + jam
    qb = esmooth(_dw(tl, dur, _b(N, 2) - 0.04, _b(N, 2)))
    if qb > 0:
        _baterai11(img, 330, 1360 + dy, 190, 80, bat, al * qb)
        _label11(img, 330, 1435 + dy, f"cadangan {int(round(bat * 100))}%", MUTED, al * qb, fsz=22)
        jcx, jcy = 330, 1560 + dy
        ring_on(img, jcx, jcy, 52, GELAP, 6, al * qb)
        ang = tg * 9 if bat > 0.01 else 0
        line_on(img, (jcx, jcy), (jcx + 38 * math.sin(ang), jcy - 38 * math.cos(ang)), GELAP, 5, al * qb)
        line_on(img, (jcx, jcy), (jcx + 24 * math.sin(ang / 12), jcy - 24 * math.cos(ang / 12)), RED, 6, al * qb)
        _stiker11(img, 480, 1560 + dy, "3-5 JAM", al, tl - _b(N, 2) * dur, bg=AMBER, fsz=30, rot=-6, tg=tg)
    # menara B menampung semua
    penuh = esmooth(_dw(tl, dur, _b(N, 5), _b(N, 6)))
    _menara11(img, 790, 1260 + dy, 360, al * q, tg, pc=RED if penuh > 0.5 else accent, nyala=1.0)
    if penuh > 0:
        _glow11(img, 790, 1100 + dy, 190, (255, 120, 110), al * penuh * 0.45)
    for k in range(14):
        u = clamp(penuh * 1.4 - k * 0.03)
        x = 360 + (790 - 360) * esmooth(u) + ((k * 37) % 120 - 60)
        y = 1330 + dy + ((k * 53) % 90) - 20 * math.sin(math.pi * u)
        if u > 0.02:
            _orang11(img, x, y, 0.8, mix(INK, RED, 0.3 * u), al * min(1, u * 4))
    tt = tl - _b(N, 5) * dur
    if tt > 0:
        _panah11(img, (420, 1180 + dy), (700, 1180 + dy), al, clamp(tt / 0.5), RED, width=9, lengkung=-0.28)
    tt = tl - _b(N, 6) * dur
    _stiker11(img, 790, 1470 + dy, "PENUH SESAK", al, tt, bg=RED, fsz=32, rot=5, tg=tg)


def _ik_jendela(img, cx, cy, a, col):
    rrect_on(img, cx - 34, cy - 34, cx + 34, cy + 34, 6, mix(BLUE, WHITE, 0.7), a, outline=col, width=5)
    line_on(img, (cx, cy - 34), (cx, cy + 34), col, 4, a)
    line_on(img, (cx - 34, cy), (cx + 34, cy), col, 4, a)


def _ik_pesawat(img, cx, cy, a, col, tg):
    poly_on(img, [(cx - 34, cy + 4), (cx + 34, cy - 6), (cx + 36, cy + 2), (cx - 32, cy + 12)], col, a)
    poly_on(img, [(cx - 4, cy - 2), (cx + 10, cy - 34), (cx + 18, cy - 32), (cx + 12, cy + 2)], col, a)
    poly_on(img, [(cx - 4, cy + 8), (cx + 12, cy + 38), (cx + 20, cy + 36), (cx + 12, cy + 6)], col, a)


def sc_tips42(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "tips42"
    _hdr(img, sc, accent, tl, al)
    tips = [("Dekati jendela", "gelombang tidak terhalang beton"),
            ("Router tinggi & terbuka", "jangan di lantai / dalam lemari"),
            ("Jauhkan dari microwave", "beda ruangan lebih baik"),
            ("Mode pesawat nyala-mati", "HP mencari menara yang lega")]
    for i, (judul, sub) in enumerate(tips):
        t_in = _b(N, i * 2) * dur
        tt = tl - t_in
        if tt <= 0:
            continue
        k = eob(clamp(tt / 0.45), 1.4)
        y = 820 + i * 205 + dy
        x_off = (1 - k) * 700
        a = al * clamp(tt / 0.2)
        rrect_on(img, 100 + x_off, y - 80, 930 + x_off, y + 80, 34, WHITE, a,
                 outline=mix(accent, WHITE, 0.55), width=3)
        dot_on(img, 190 + x_off, y, 56, mix(accent, WHITE, 0.82), a)
        ik = mix(accent, INK, 0.2)
        if i == 0:
            _ik_jendela(img, 190 + x_off, y, a, ik)
        elif i == 1:
            _router11(img, 190 + x_off, y + 16, a, tg, s=0.34, pancar=False)
            _pancar11(img, 190 + x_off, y - 12, tg, ik, a, rmax=40, a0=-150, a1=-30, width=4)
        elif i == 2:
            _micro11(img, 190 + x_off, y, a, tg, s=0.2)
            line_on(img, (150 + x_off, y + 40), (230 + x_off, y - 40), RED, 7, a)
        else:
            _ik_pesawat(img, 190 + x_off, y, a, ik, tg)
        paste_c(img, 540 + x_off, y - 18, judul, font(FB, 32), INK, a)
        paste_c(img, 540 + x_off, y + 26, sub, font(FS, 22), MUTED, a)
        tc = tl - _b(N, i * 2 + 1) * dur
        if tc > 0:
            D._check5_on(img, 860 + x_off, y, 40, "check", a, clamp(tc / 0.35), col=GREEN)
    # sakelar mode pesawat berkedip on-off
    tt = tl - _b(N, 8) * dur
    if tt > 0:
        on = 1.0 if tt < 0.9 else 0.0
        y = 1640 + dy
        rrect_on(img, 460, y - 34, 620, y + 34, 34, mix(GREEN, WHITE, 0.2) if on else mix(CREAM, INK, 0.3), al)
        dot_on(img, 580 if on else 500, y, 28, WHITE, al)
        _label11(img, 330, y, "mode pesawat", MUTED, al, fsz=24)
        _label11(img, 700, y, "ON" if on else "OFF", GREEN if on else MUTED, al, fsz=26, name=FB)


def sc_rangkuman42(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "rangkuman42"
    _hdr(img, sc, accent, tl, al)
    items = [("GARIS = KEKUATAN", "bukan kecepatan"), ("MENARA DIBAGI", "ramai = jatah mengecil"),
             ("DINDING MENYERAP", "gelombang radio melemah")]
    for i, (a_, b_) in enumerate(items):
        tt = tl - _b(N, 1 + i) * dur
        if tt <= 0:
            continue
        k = eob(clamp(tt / 0.4), 1.8)
        y = 830 + i * 190 + dy
        a = al * clamp(tt / 0.15)
        rrect_on(img, 120, y - 72, 900, y + 72, 30, mix(WHITE, accent, 0.06), a,
                 outline=mix(accent, WHITE, 0.5), width=3)
        dot_on(img, 200, y, 44 * k, accent, a)
        paste_c(img, 200, y, str(i + 1), font(FB, 40), WHITE, a)
        paste_c(img, 560, y - 18, a_, font(FB, 34), INK, a, scale=0.85 + 0.15 * k)
        paste_c(img, 560, y + 26, b_, font(FS, 24), MUTED, a)
    tt = tl - _b(N, 4) * dur
    if tt > 0:
        _stiker11(img, 470, 1450 + dy, "KIRIM KE TEMAN", al, tt, bg=RED, fsz=40, rot=-4, tg=tg)
        _label11(img, 470, 1540 + dy, "yang selalu menyalahkan HP-nya", MUTED, al * clamp(tt / 0.3), fsz=26)
        _panah11(img, (740, 1470 + dy), (930, 1560 + dy), al, clamp((tt - 0.2) / 0.5), RED,
                 width=10, lengkung=-0.3)


def _geser(fn):
    def w(img, d, sc, tl, dur, tg, accent, al, dy):
        return fn(img, d, sc, tl, dur, tg, accent, al, dy + GESER)
    w.__name__ = fn.__name__
    return w


VISUALS11 = {
    "intro_sinyal42": sc_intro_sinyal42, "garis42": sc_garis42, "antre42": sc_antre42,
    "tembus42": sc_tembus42, "wifi42": sc_wifi42, "micro42": sc_micro42, "padam42": sc_padam42,
    "tips42": sc_tips42, "rangkuman42": sc_rangkuman42,
}
# episode v11 berikutnya: modul terpisah per episode (mesin_v11_epNN.py) - mendaftar BEATS sendiri
if __name__ != "__main__":       # saat dijalankan langsung, __main__ memuat ulang sebagai modul
    import mesin_v11_ep43 as _E43
    import mesin_v11_ep44 as _E44
    import mesin_v11_ep45 as _E45
    import mesin_v11_ep46 as _E46
    import mesin_v11_ep47 as _E47
    import mesin_v11_ep48 as _E48
    import mesin_v11_ep49 as _E49
    VISUALS11.update(_E43.VISUALS43)
    VISUALS11.update(_E44.VISUALS44)
    VISUALS11.update(_E45.VISUALS45)
    VISUALS11.update(_E46.VISUALS46)
    VISUALS11.update(_E47.VISUALS47)
    VISUALS11.update(_E48.VISUALS48)
    VISUALS11.update(_E49.VISUALS49)
VISUALS11 = {k: (v if k.startswith("intro") else _geser(v)) for k, v in VISUALS11.items()}
D.VISUALS.update(VISUALS11)
# v12 KONTINUITAS: modul episode v12 mendaftar sendiri (BEATS/VISUALS/EVENTS12 lewat daftar()),
# tanpa _geser; impor di sini hanya memastikan modul termuat (aman terhadap impor melingkar)
import mesin_v12_ep50  # noqa: E402,F401


def _selftest():
    img = Image.new("RGB", (int(1080 * D.SS), int(1920 * D.SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "GARIS SINYAL BUKAN KECEPATAN", "hl": "BUKAN KECEPATAN",
          "lines": ["SINYAL PENUH,", "TAPI KOK LEMOT?"]}
    assert len(VISUALS11) >= 63, len(VISUALS11)
    for n, fn in VISUALS11.items():
        assert n in BEATS, n
        for tl in (0.3, 2.0, 6.0, 9.0, 12.0, 14.5):
            fn(img, d, sc, tl, 15.0, tl, D.hexc("#2F6FB5"), 1.0, 0.0)
    a = Image.new("RGB", (400, 700), CREAM); b = Image.new("RGB", (400, 700), WHITE)
    for nm, f in TRANSISI.items():
        for p in (0.0, 0.3, 0.5, 0.8, 1.0):
            out = f(a, b, p, BLUE)
            assert out.size == a.size, nm
    ev = events([{"start": 0, "dur": 10, "type": "intro", "visual": "intro_sinyal42"},
                 {"start": 10, "dur": 12, "type": "fact", "visual": "garis42", "trans": "punch", "badge": "X"}])
    assert ev and all(e[0] >= 0 for e in ev)
    assert punch_kamera(10.0, ev) > 0
    print(f"selftest v11: {len(VISUALS11)} adegan, {len(TRANSISI)} transisi, {len(ev)} event OK")


if __name__ == "__main__":
    # impor sebagai modul (bukan __main__) supaya modul episode (mesin_v11_epNN) tidak memuat salinan ganda
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    import mesin_v11 as _m
    _m._selftest()
