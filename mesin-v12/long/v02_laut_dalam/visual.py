#!/usr/bin/env python3
"""Visual Long02 - "Perjalanan ke Dasar Laut Terdalam di Bumi" (16:9).

Konsep: satu penyelaman tanpa putus. Ada satu fungsi KEDALAMAN global (meter) yang
dikunci ke kata narasi. Fungsi itu menggerakkan:
  - latar laut (gradasi warna air per kedalaman, berkas sinar matahari yang memudar,
    salju laut 2 lapis yang bergerak naik saat kita turun, kelip bioluminesensi),
  - HUD penyelaman di kiri (alat ukur kedalaman berpita zona + angka meter, tekanan,
    suhu, cahaya) - digambar tajam di kanvas final lewat hook `overlay`.
Setiap bab = beberapa shot yang dikunci ke KATA (C.w("kata")). BEATS memakai kata yang
sama, jadi SFX & dorongan kamera jatuh tepat saat elemen muncul.
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import mesin_long as L
from mesin_long import (D, S, W, H, mix, clamp, seg, eo, eio, eob, esmooth, teks, judul, kaca, chip,
                        stiker, stempel, angka, callout, panah, centang, partikel, glow, garis_ukur,
                        lebar, fmt_id, FB, FS, FM, TEKS, REDUP, ORANYE, EMAS, SIAN, MERAH, UNGU, HIJAU,
                        SP0, WHITE)

HERE = os.path.dirname(os.path.abspath(__file__))
M = L.M
_GW = L._cache()


def glow(img, cx, cy, r, col, alpha):
    """Cahaya lembut tanpa tepi kotak (masker radial numpy turun mulus ke 0 di tepi)."""
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
CX = 1110          # pusat konten (kiri dipakai HUD kedalaman)
LAUT = (20, 90, 150)
BIRU_M = (70, 180, 240)
PASIR = (58, 52, 50)


def muncul(C, key, n=1, off=0.0, d=0.45):
    q = C.u(key, d, n, off, ease=eo)
    return q, (1 - q) * 36


def jendela(C, k0, k1, n0=1, n1=1, o0=-0.25, o1=-0.25, fi=0.45, fo=0.45):
    a = C.w(k0, n0, o0) if isinstance(k0, str) else k0
    b = C.w(k1, n1, o1) if isinstance(k1, str) else k1
    return C.win(a, b, fi, fo)


def kaca_teks(img, cx, cy, judul_, isi, alpha, acc, w=520, h=150, dy=0.0, fsz=40, isifsz=24):
    kaca(img, cx - w / 2, cy - h / 2 + dy, cx + w / 2, cy + h / 2 + dy, alpha, acc)
    teks(img, cx, cy - (18 if isi else 0) + dy, judul_, fsz, TEKS, alpha, name=FB)
    if isi:
        teks(img, cx, cy + fsz * 0.72 + dy, isi, isifsz, REDUP, alpha, name=FS)


def silang_besar(img, cx, cy, r, tt, alpha=1.0, col=MERAH, wd=14):
    if tt <= 0 or alpha <= 0.01:
        return
    q = esmooth(clamp(tt / 0.35))
    a = r
    D.line_on(img, (cx - a, cy - a), (cx - a + 2 * a * min(1, q * 2), cy - a + 2 * a * min(1, q * 2)), col, wd, alpha)
    if q > 0.5:
        k = (q - 0.5) * 2
        D.line_on(img, (cx + a, cy - a), (cx + a - 2 * a * k, cy - a + 2 * a * k), col, wd, alpha)


def gelombang(img, x0, x1, y, amp, lam, ph, col, wd, alpha, n=60):
    pts = [(x0 + (x1 - x0) * j / n, y + amp * math.sin((x0 + (x1 - x0) * j / n) / lam * 6.283 + ph))
           for j in range(n + 1)]
    M._pline(img, pts, col, wd, alpha)


# ====================================================================== KEDALAMAN
# (waktu, meter). waktu = detik relatif adegan, atau (kata, ke-n, offset), atau "end".
KD = {
    "v02_intro": [(0, 0), (("menyelam", 2, 0.1), 0), (("menyelam", 2, 1.3), 5)],
    "v02_matahari": [(0, 5), (("air", 1, 0), 10), (("dua", 1, -0.4), 20), (("setiap", 1, 0), 22),
                     (("sepuluh", 1, 0), 30), (("penyelam", 1, -0.2), 32), (("empat", 1, -0.3), 40),
                     (("tapi", 1, 0), 45), (("dua", 2, -0.6), 200), ("end", 200)],
    "v02_senja": [(0, 200), (("tumbuhan", 1, 0), 250), (("tapi", 1, 0), 300), (("begitu", 1, 0), 450),
                  (("semakin", 1, 0), 600), (("seribu", 1, -0.6), 1000), ("end", 1000)],
    "v02_malam": [(0, 1000), (("gelap", 1, 0), 1050), (("tapi", 1, 0), 1150), (("salah", 1, 0), 1400),
                  (("zona", 2, 0), 1500), (("dua", 1, -0.4), 2000), (("cumicumi", 1, 0), 2100), ("end", 2200)],
    "v02_titanic": [(0, 2200), (("tiga", 1, -0.6), 3700), (("sedikit", 1, 0), 3700), (("tiga", 2, -0.4), 3800),
                    (("coba", 1, 0), 3820), (("sekeliling", 1, 0), 3850), ("end", 3900)],
    "v02_ventilasi": [(0, 3900), (("empat", 1, -0.4), 4000), (("tapi", 1, 0), 4100),
                      (("mengejutkan", 1, 0), 4300), (("mereka", 1, 0), 4500), ("end", 5000)],
    "v02_hadal": [(0, 5000), (("enam", 1, -0.3), 6000), (("zona", 2, 0), 6200), (("indonesia", 1, 0), 6500),
                  (("tujuh", 1, -0.4), 7200), (("bahkan", 1, 0), 7500), (("delapan", 1, -0.4), 8336),
                  (("para", 1, 0), 8336), ("end", 8400)],
    "v02_terdalam": [(0, 8400), (("sepuluh", 1, -0.3), 8400), (("meter", 1, 0.0), 10935), ("end", 10935)],
    "v02_manusia": [(0, 10935), ("end", 10935)],
    "v02_naik": [(0, 10935), (("naik", 1, 0), 10935), (("perjalanan", 1, 1.0), 0), ("end", 0)],
}
_KDC = {}


def _kunci(C):
    key = C.sc["visual"]
    r = _KDC.get((key, id(C.sc)))
    if r is None:
        r = []
        for tspec, m in KD[key]:
            if tspec == "end":
                t_ = C.dur
            elif isinstance(tspec, tuple):
                t_ = C.w(*tspec)
            else:
                t_ = float(tspec)
            r.append((t_, float(m)))
        _KDC[(key, id(C.sc))] = r
    return r


def dalam(C, tl=None):
    tl = C.tl if tl is None else tl
    ks = _kunci(C)
    if tl <= ks[0][0]:
        return ks[0][1]
    for (t0, m0), (t1, m1) in zip(ks, ks[1:]):
        if tl <= t1:
            if t1 - t0 < 1e-6:
                return m1
            return m0 + (m1 - m0) * esmooth(clamp((tl - t0) / (t1 - t0)))
    return ks[-1][1]


def _interp(d, tabel):
    xs = [a for a, _ in tabel]
    return float(np.interp(d, xs, [b for _, b in tabel]))


def suhu(d):
    return _interp(d, [(0, 28), (50, 27), (200, 18), (500, 8), (1000, 4), (4000, 2), (11000, 2)])


def cahaya(d):
    return 100.0 * math.exp(-d / 43.43)


ZONA = [(0, 200, "ZONA MATAHARI", EMAS), (200, 1000, "ZONA SENJA", SIAN),
        (1000, 4000, "ZONA TENGAH MALAM", UNGU), (4000, 6000, "ZONA ABISAL", ORANYE),
        (6000, 11000, "ZONA HADAL", HIJAU)]


def zona(d):
    for z in ZONA:
        if d < z[1]:
            return z
    return ZONA[-1]


# ====================================================================== LATAR LAUT
_GR = [(0, (74, 178, 222), (26, 108, 168)), (30, (40, 140, 196), (16, 82, 140)),
       (200, (12, 58, 108), (6, 32, 74)), (1000, (5, 18, 46), (3, 10, 30)),
       (4000, (3, 7, 20), (2, 4, 13)), (11000, (2, 4, 11), (1, 2, 7))]
_LB = L._cache()


def _warna_air(d):
    x = math.log10(1 + d)
    xs = [math.log10(1 + g[0]) for g in _GR]
    top = tuple(int(np.interp(x, xs, [g[1][c] for g in _GR])) for c in range(3))
    bot = tuple(int(np.interp(x, xs, [g[2][c] for g in _GR])) for c in range(3))
    return top, bot


def _gradasi(d):
    key = (int(math.log10(1 + d) * 300), round(D.SS, 3))
    im = _LB.get(key)
    if im is None:
        top, bot = _warna_air(d)
        cah = clamp(1 - d / 260.0)
        gw, gh = 48, 27
        yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
        u = yy / (gh - 1)
        v = xx / (gw - 1)
        t_ = np.array(top, np.float32)
        b_ = np.array(bot, np.float32)
        arr = t_ + (b_ - t_) * (u[..., None] ** 1.1)
        sinar = np.exp(-((v - 0.55) ** 2) / 0.09) * (1 - u) ** 2 * (0.25 + 0.55 * cah)
        arr = arr + sinar[..., None] * (np.array(top, np.float32) * 0.5 + 18)
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").resize(
            (int(S(W)), int(S(H))), Image.BILINEAR)
        if len(_LB) > 90:
            _LB.clear()
        _LB[key] = im
    return im


def _sinar_spr():
    key = ("sinar", round(D.SS, 3))
    s = _LB.get(key)
    if s is None:
        w, h = int(S(W * 1.3)), int(S(H))
        s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(s)
        rng = random.Random(4)
        for k in range(11):
            x = rng.uniform(0.05, 0.95) * w
            wt = S(rng.uniform(40, 130))
            sl = S(rng.uniform(-260, -120))
            a = rng.randint(22, 50)
            dd.polygon([(x - wt * 0.3, 0), (x + wt * 0.3, 0), (x + sl + wt, h), (x + sl - wt, h)],
                       fill=(210, 240, 255, a))
        s = s.filter(ImageFilter.GaussianBlur(S(22)))
        m = np.array(s.getchannel("A"), np.float32)
        fade = np.linspace(1, 0, h, dtype=np.float32)[:, None] ** 1.3
        s.putalpha(Image.fromarray((m * fade).astype(np.uint8)))
        _LB[key] = s
    return s


def _salju_spr():
    key = ("salju", round(D.SS, 3))
    s = _LB.get(key)
    if s is None:
        w, h = int(S(W)), int(S(H))
        rng = random.Random(11)
        lap = []
        for n, (r0, r1), (a0, a1) in ((330, (0.7, 1.5), (60, 150)), (80, (1.6, 3.2), (110, 220))):
            im = Image.new("RGBA", (w, h * 2), (0, 0, 0, 0))
            dd = ImageDraw.Draw(im)
            for _ in range(n):
                x, y = rng.random() * w, rng.random() * h
                r = S(rng.uniform(r0, r1))
                a = rng.randint(a0, a1)
                c = rng.choice([(235, 245, 255), (210, 230, 240), (245, 240, 225)])
                for dy in (0, h):
                    if r > S(1.8):
                        dd.ellipse([x - r * 2.2, y + dy - r * 2.2, x + r * 2.2, y + dy + r * 2.2], fill=c + (a // 7,))
                    dd.ellipse([x - r, y + dy - r * 0.8, x + r, y + dy + r * 0.8], fill=c + (a,))
            lap.append(im)
        s = lap
        _LB[key] = s
    return s


def _g(d):
    """Posisi gulir partikel (px logis) sebagai fungsi kedalaman."""
    return 150.0 * math.sqrt(max(0.0, d))


_KELIP = [(random.Random(k).random() * W, random.Random(k + 50).random() * H,
           random.Random(k + 90).choice([SIAN, (120, 255, 210), (150, 170, 255), UNGU]),
           random.Random(k + 7).random() * 6.28, random.Random(k + 3).uniform(0.4, 1.1)) for k in range(22)]


def latar(t, C):
    d = dalam(C)
    C.d = d
    img = _gradasi(d).copy()
    w, h = img.size
    ra = clamp(1 - d / 230.0)
    if ra > 0.02 and not getattr(C, "tanpa_sinar", False):
        s = _sinar_spr()
        ox = int((s.width - w) / 2 + S(60 * math.sin(t * 0.21)))
        c = s.crop((ox, 0, ox + w, h))
        a = ra * (0.85 + 0.15 * math.sin(t * 0.7))
        c.putalpha(c.getchannel("A").point(lambda v: int(v * a)))
        img.paste(c, (0, 0), c)
    far, near = _salju_spr()
    gd = _g(d)
    for lay, k, v in ((far, 0.45, 7.0), (near, 1.0, 16.0)):
        oy = int(S(gd * k - t * v)) % h
        c = lay.crop((int(S(8 * math.sin(t * 0.15 + k * 3))) % 2, oy, int(S(8 * math.sin(t * 0.15 + k * 3))) % 2 + w, oy + h))
        img.paste(c, (0, 0), c)
    # jejak kecepatan saat turun/naik cepat
    try:
        v = (_g(dalam(C, C.tl + 0.04)) - gd) / 0.04
    except Exception:
        v = 0.0
    if abs(v) > 260:
        a = clamp((abs(v) - 260) / 900) * 0.5
        rng = random.Random(int(t * 30))
        for _ in range(26):
            x, y = rng.random() * W, rng.random() * H
            ln = 40 + 160 * a
            D.line_on(img, (x, y), (x, y + (ln if v > 0 else -ln)), (220, 240, 255), 2, a * rng.uniform(0.3, 1))
    # kelip bioluminesensi di zona gelap
    ka = clamp((d - 700) / 400) * clamp((9500 - d) / 1500) * _kelip_on(C)
    if ka > 0.02:
        for x, y, col, ph, sp in _KELIP:
            b = math.sin(t * sp * 2.2 + ph)
            if b > 0.55:
                yy = (y - gd * 0.7) % H
                q = (b - 0.55) / 0.45
                glow(img, x, yy, 34, col, 0.45 * q * ka)
                D.dot_on(img, x, yy, 2.6, mix(col, WHITE, 0.5), q * ka)
    return img


# ====================================================================== HUD KEDALAMAN
GY0, GY1, GX = 150, 900, 70


def _gy(d):
    return GY0 + (GY1 - GY0) * math.sqrt(clamp(d / 11000.0))


def overlay(img, C):
    d = getattr(C, "d", None)
    if d is None:
        d = dalam(C)
    vis = C.sc["visual"]
    a = 1.0
    if C.i > 0:
        a *= clamp((C.tl - 3.35) / 0.5)
    a *= clamp((C.dur - 0.25 - C.tl) / 0.3) if C.i < C.n - 1 else 1.0
    if vis == "v02_intro":
        a = clamp((C.tl - C.w("menyelam", 2, 0.2)) / 0.5)
    if vis == "v02_naik":
        a = 1 - clamp((C.tl - C.w("perjalanan", 1, 1.6)) / 0.6)
    a *= getattr(C, "hud_a", 1.0)
    if a <= 0.01:
        return
    # pita zona
    for z0, z1, nama, col in ZONA:
        y0, y1 = _gy(z0) + (2 if z0 else 0), _gy(z1) - 2
        D.rrect_on(img, GX - 5, y0, GX + 5, y1, 4, mix(col, SP0, 0.62), 0.9 * a)
        if d > z0:
            yy = min(y1, _gy(d))
            if yy > y0 + 1:
                D.rrect_on(img, GX - 5, y0, GX + 5, yy, 4, col, 0.95 * a)
    for m in (200, 1000, 4000, 6000, 11000):
        y = _gy(m)
        D.line_on(img, (GX - 12, y), (GX - 7, y), REDUP, 2, 0.7 * a)
        teks(img, GX - 16, y, fmt_id(m), 13, REDUP, 0.75 * a, name=FS, anchor="r")
    teks(img, GX - 16, GY0, "0", 13, REDUP, 0.75 * a, name=FS, anchor="r")
    z = zona(d)
    ym = _gy(d)
    D.poly_on(img, [(GX + 9, ym), (GX + 23, ym - 9), (GX + 23, ym + 9)], WHITE, a)
    glow(img, GX, ym, 26, z[3], 0.5 * a)
    # kotak angka mengikuti penanda
    by = min(max(ym, GY0 + 40), GY1 - 90)
    x0, x1 = GX + 30, GX + 250
    kaca(img, x0, by - 46, x1, by + 104, 0.86 * a, z[3], r=16)
    D.line_on(img, (GX + 23, ym), (x0, by - 10), mix(z[3], WHITE, 0.3), 2, 0.6 * a)
    teks(img, x0 + 20, by - 18, fmt_id(d) + " m", 38, TEKS, a, name=FB, anchor="l")
    teks(img, x0 + 20, by + 16, z[2], 14, z[3], a, name=FB, anchor="l")
    atm = 1 + d / 10.0
    cah = cahaya(d)
    cs = ("%.0f%%" % cah) if cah >= 1 else ("<1%" if cah > 0.001 else "0%")
    for j, (lab, val) in enumerate((("TEKANAN", fmt_id(atm) + " atm"), ("SUHU", "%.0f\u00b0C" % suhu(d)),
                                     ("CAHAYA", cs))):
        y = by + 42 + j * 19
        teks(img, x0 + 20, y, lab, 13, REDUP, a * 0.9, name=FS, anchor="l")
        teks(img, x1 - 16, y, val, 14, TEKS, a, name=FB, anchor="r")


# ====================================================================== SPRITE UTIL
_SP = L._cache()


def sprite(key, w, h, fn, ov=3):
    """Sprite RGBA ter-cache: fn(dd, f, im) menggambar dalam satuan logis x f (supersample)."""
    k = (key, round(D.SS, 3))
    s = _SP.get(k)
    if s is None:
        f = D.SS * ov
        big = Image.new("RGBA", (max(2, int(w * f)), max(2, int(h * f))), (0, 0, 0, 0))
        dd = ImageDraw.Draw(big)
        fn(dd, f, big)
        s = big.resize((max(2, int(w * D.SS)), max(2, int(h * D.SS))), Image.LANCZOS)
        _SP[k] = s
    return s


_FL = L._cache()


def taruh(img, spr, cx, cy, alpha=1.0, k=1.0, flip=False, rot=0.0, key=None):
    if alpha <= 0.01 or k <= 0.01:
        return
    s = spr
    if flip:
        fk = (id(spr), "flip")
        s = _FL.get(fk)
        if s is None:
            s = spr.transpose(Image.FLIP_LEFT_RIGHT)
            _FL[fk] = s
    if abs(k - 1) > 0.004:
        s = L._resized(("tr", id(spr), flip), s, k)
    if abs(rot) > 0.3:
        s = s.rotate(rot, resample=Image.BICUBIC, expand=True)
    L._put_c(img, s, cx, cy, alpha)


def _P(pts, f, ox=0.0, oy=0.0):
    return [((x + ox) * f, (y + oy) * f) for x, y in pts]


def _E(dd, f, x0, y0, x1, y1, col, a=255, outline=None, wd=0):
    dd.ellipse([x0 * f, y0 * f, x1 * f, y1 * f], fill=(col + (a,)) if col else None,
               outline=(outline + (a,)) if outline else None, width=int(wd * f))


def _kurva(pts, n=14):
    """Catmull-Rom halus melalui titik (tertutup)."""
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for j in range(n):
            t_ = j / n
            t2, t3 = t_ * t_, t_ * t_ * t_
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t_ + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in range(2)))
    return out


# ====================================================================== MAKHLUK
def ikan(img, cx, cy, L_, col=(250, 170, 80), alpha=1.0, flip=False, tg=0.0, rot=0.0, perut=None):
    """Ikan umum (menghadap kanan). 6 fase kibasan ter-cache."""
    fase = int((tg * 7.0) % 6)

    def fn(dd, f, im, fase=fase):
        sw = math.sin(fase / 6 * 6.283) * 7
        body = _kurva([(98, 30), (80, 16), (52, 10), (26, 16), (14, 30), (26, 44), (52, 50), (80, 44)], 10)
        dd.polygon([((20) * f, 30 * f), (2 * f, (12 + sw) * f), (8 * f, 30 * f), (2 * f, (48 + sw) * f)],
                   fill=mix(col, SP0, 0.25) + (255,))
        dd.polygon(_P(body, f), fill=col + (255,))
        pc = perut or mix(col, WHITE, 0.45)
        dd.polygon(_P(_kurva([(92, 34), (70, 40), (46, 46), (30, 40), (46, 36), (72, 34)], 6), f), fill=pc + (230,))
        dd.polygon(_P([(50, 11), (64, 2), (70, 12)], f), fill=mix(col, SP0, 0.2) + (255,))
        dd.polygon(_P([(60, 34), (50, 44), (66, 38)], f), fill=mix(col, SP0, 0.25) + (220,))
        _E(dd, f, 80, 22, 88, 30, (250, 250, 250))
        _E(dd, f, 82.5, 24, 87, 28.5, (15, 15, 25))
        dd.arc([70 * f, 16 * f, 84 * f, 44 * f], 290, 70, fill=mix(col, SP0, 0.3) + (200,), width=int(1.6 * f))
    spr = sprite(("ikan", col, perut, fase), 100, 60, fn)
    taruh(img, spr, cx, cy, alpha, L_ / 100.0, flip, rot)


def kawanan(img, cx, cy, n, L_, tg, alpha=1.0, col=(120, 200, 235), sebar=(420, 160), flip=False, seed=1,
            cepat=1.0, rapat=1.0):
    rng = random.Random(seed)
    for k in range(n):
        ox, oy = rng.uniform(-1, 1) * sebar[0], rng.uniform(-1, 1) * sebar[1]
        ph = rng.random() * 6.28
        x = cx + ox * rapat + 16 * math.sin(tg * 0.9 * cepat + ph)
        y = cy + oy * rapat + 10 * math.sin(tg * 1.3 * cepat + ph * 1.7)
        s = L_ * rng.uniform(0.75, 1.15)
        ikan(img, x, y, s, col, alpha * rng.uniform(0.75, 1.0), flip, tg * cepat + ph)


def ikan_lentera(img, cx, cy, L_, tg=0.0, alpha=1.0, flip=False, nyala=1.0):
    fase = int((tg * 7.0) % 6)

    def fn(dd, f, im, fase=fase):
        col = (46, 70, 110)
        sw = math.sin(fase / 6 * 6.283) * 6
        dd.polygon(_P([(16, 30), (0, 14 + sw), (6, 30), (0, 46 + sw)], f), fill=mix(col, SP0, 0.3) + (255,))
        dd.polygon(_P(_kurva([(98, 32), (86, 18), (56, 14), (26, 20), (14, 30), (26, 40), (56, 46), (86, 44)], 10), f),
                   fill=col + (255,))
        dd.polygon(_P(_kurva([(96, 34), (80, 42), (50, 44), (28, 38), (50, 36), (80, 36)], 6), f),
                   fill=(120, 140, 170, 220))
        _E(dd, f, 78, 20, 92, 34, (230, 235, 240))
        _E(dd, f, 82, 23, 90, 31, (10, 10, 20))
    spr = sprite(("lentera", fase), 100, 60, fn)
    k = L_ / 100.0
    taruh(img, spr, cx, cy, alpha, k, flip, 0)
    if nyala > 0.02:
        sgn = -1 if flip else 1
        for j in range(6):
            px = cx + sgn * (30 - j * 11) * k
            py = cy + (11 + (j % 2) * 1.5) * k
            glow(img, px, py, 9 * k + 4, (90, 230, 255), 0.55 * nyala * alpha)
            D.dot_on(img, px, py, max(1.2, 2.2 * k), (200, 250, 255), nyala * alpha)


def ubur(img, cx, cy, r, tg, alpha=1.0, col=(170, 150, 255), nyala=0.6):
    """Ubur-ubur tembus pandang berdenyut + tentakel bergelombang."""
    if alpha <= 0.01:
        return
    p = 0.5 + 0.5 * math.sin(tg * 2.4)
    rx, ry = r * (1.0 + 0.08 * p), r * (0.72 - 0.1 * p)
    glow(img, cx, cy, r * 2.2, col, 0.25 * nyala * alpha)
    for j in range(7):
        x0 = cx - rx * 0.7 + rx * 1.4 * j / 6
        pts = [(x0 + 8 * math.sin(tg * 2 + j + u * 5) * (u + 0.2), cy + r * 0.1 + u * r * 2.4) for u in
               [q / 10 for q in range(11)]]
        M._pline(img, pts, mix(col, WHITE, 0.3), 2, alpha * 0.55)
    bell = [(cx + rx * math.cos(a_), cy - ry * math.sin(a_)) for a_ in [math.pi * q / 24 for q in range(25)]]
    rok = [(cx - rx + rx * 2 * q / 10, cy + r * 0.08 * math.sin(q * 1.9 + tg * 3)) for q in range(11)]
    D.poly_on(img, bell + rok, mix(col, SP0, 0.2), alpha * 0.45)
    D.ring_on(img, cx, cy - ry * 0.35, rx * 0.45, mix(col, WHITE, 0.5), 2, alpha * 0.5, squash=0.55)
    M._pline(img, bell[:25], mix(col, WHITE, 0.55), 3, alpha * 0.9)


def udang(img, cx, cy, L_, alpha=1.0, flip=False, tg=0.0, col=(240, 110, 80), rot=0.0):
    fase = int((tg * 5) % 4)

    def fn(dd, f, im, fase=fase):
        segs = [(78, 28, 13), (66, 26, 14), (54, 27, 13), (43, 30, 12), (33, 35, 10), (25, 41, 8), (19, 47, 6)]
        for j in range(3):
            y = 36 + j * 0 + 0
            dd.line([((58 - j * 12) * f, 36 * f), ((56 - j * 12 + (fase - 1.5) * 1.5) * f, 48 * f)],
                    fill=mix(col, SP0, 0.2) + (255,), width=int(1.6 * f))
        dd.polygon(_P([(16, 50), (6, 44), (8, 56), (20, 54)], f), fill=mix(col, SP0, 0.15) + (255,))
        for x, y, r in segs[::-1]:
            _E(dd, f, x - r, y - r * 0.8, x + r, y + r * 0.8, col)
            _E(dd, f, x - r * 0.7, y - r * 0.75, x + r * 0.5, y - r * 0.2, mix(col, WHITE, 0.35), 180)
        dd.polygon(_P([(86, 24), (99, 22), (88, 30)], f), fill=col + (255,))
        _E(dd, f, 82, 20, 88, 26, (20, 15, 20))
        dd.line([(88 * f, 22 * f), (99 * f, 4 * f), (70 * f, 1 * f)], fill=mix(col, WHITE, 0.2) + (255,), width=int(1.4 * f))
        dd.line([(88 * f, 24 * f), (99 * f, 12 * f)], fill=mix(col, WHITE, 0.2) + (255,), width=int(1.4 * f))
    spr = sprite(("udang", col, fase), 100, 60, fn)
    taruh(img, spr, cx, cy, alpha, L_ / 100.0, flip, rot)


def pemancing(img, cx, cy, L_, tg, alpha=1.0, mulut=0.3, lure=1.0, flip=False):
    """Ikan pemancing (anglerfish): kepala besar, gigi tajam, umpan bercahaya."""
    mq = int(round(clamp(mulut) * 5))

    def fn(dd, f, im, mq=mq):
        mo = mq / 5.0
        col = (48, 40, 52)
        dd.polygon(_P([(20, 60), (2, 34), (6, 60), (2, 86)], f), fill=mix(col, SP0, 0.2) + (255,))
        body = _kurva([(64, 18), (94, 26), (112, 44 - mo * 8), (100, 60), (116, 82 + mo * 10), (92, 96), (58, 100),
                       (30, 88), (16, 62), (30, 34)], 10)
        dd.polygon(_P(body, f), fill=col + (255,))
        # rahang bawah & mulut
        dd.polygon(_P([(112, 44 - mo * 8), (70, 58), (116, 82 + mo * 10)], f), fill=(18, 10, 16, 255))
        for j in range(6):
            u = j / 5
            x = 110 - u * 34
            ya = 44 - mo * 8 + u * (58 - 44 + mo * 8)
            dd.polygon(_P([(x - 3, ya - 1), (x + 3, ya - 1), (x - 1, ya + 9)], f), fill=(235, 230, 215, 255))
            yb = 82 + mo * 10 - u * (82 + mo * 10 - 58)
            dd.polygon(_P([(x - 3, yb + 1), (x + 3, yb + 1), (x + 1, yb - 9)], f), fill=(235, 230, 215, 255))
        dd.polygon(_P([(56, 22), (40, 6), (64, 20)], f), fill=mix(col, SP0, 0.1) + (255,))
        dd.polygon(_P([(50, 96), (40, 116), (64, 98)], f), fill=mix(col, SP0, 0.1) + (255,))
        _E(dd, f, 78, 30, 90, 42, (210, 220, 230))
        _E(dd, f, 81, 33, 88, 40, (8, 8, 12))
        for j in range(5):
            _E(dd, f, 40 + j * 9, 44 + (j % 2) * 16, 43 + j * 9, 47 + (j % 2) * 16, (80, 70, 86), 200)
        # tangkai umpan
        dd.line(_P([(70, 20), (84, 0), (110, 2), (122, 12)], f), fill=(80, 70, 86, 255), width=int(2.4 * f))
    spr = sprite(("angler", mq), 130, 120, fn)
    k = L_ / 130.0
    taruh(img, spr, cx, cy, alpha, k, flip)
    sgn = -1 if flip else 1
    lx, ly = cx + sgn * (122 - 65) * k, cy + (14 - 60) * k + 3 * math.sin(tg * 2.2)
    if lure > 0.01:
        fl = 0.85 + 0.15 * math.sin(tg * 6)
        glow(img, lx, ly, 70 * k + 20, (120, 240, 255), 0.55 * lure * fl * alpha)
        glow(img, lx, ly, 24 * k + 8, (220, 255, 255), 0.8 * lure * alpha)
        D.dot_on(img, lx, ly, 5.5 * k + 1, (235, 255, 255), alpha * max(0.3, lure))
    return lx, ly


def paus_sperma(img, cx, cy, L_, alpha=1.0, flip=False, tg=0.0, rot=0.0):
    fase = int((tg * 3) % 6)

    def fn(dd, f, im, fase=fase):
        col = (84, 92, 108)
        sw = math.sin(fase / 6 * 6.283) * 10
        dd.polygon(_P([(30, 40), (4, 26 + sw), (10, 40 + sw * 0.6), (4, 56 + sw)], f), fill=mix(col, SP0, 0.2) + (255,))
        body = [(30, 38), (60, 30), (110, 22), (150, 16), (240, 14), (262, 20), (264, 50), (240, 62), (180, 64),
                (110, 58), (60, 48)]
        dd.polygon(_P(body, f), fill=col + (255,))
        dd.polygon(_P([(240, 50), (262, 48), (250, 60), (200, 62)], f), fill=mix(col, SP0, 0.3) + (255,))
        dd.line(_P([(252, 54), (198, 58)], f), fill=(40, 44, 54, 255), width=int(2 * f))
        for j in range(8):
            dd.arc([(100 + j * 12) * f, 22 * f, (112 + j * 12) * f, 50 * f], 180, 260, fill=(70, 78, 92, 200), width=int(1.5 * f))
        dd.polygon(_P([(160, 60), (150, 76), (174, 62)], f), fill=mix(col, SP0, 0.25) + (255,))
        _E(dd, f, 204, 42, 210, 48, (20, 20, 26))
    spr = sprite(("paus", fase), 270, 80, fn)
    taruh(img, spr, cx, cy, alpha, L_ / 270.0, flip, rot)


def cumi(img, cx, cy, L_, tg, alpha=1.0, col=(200, 80, 70), rot=0.0):
    """Cumi-cumi raksasa (kepala ke kanan-atas), tentakel bergelombang digambar langsung."""
    if alpha <= 0.01:
        return
    k = L_ / 300.0
    ca, sa = math.cos(math.radians(-rot)), math.sin(math.radians(-rot))

    def T(x, y):
        return cx + (x * ca - y * sa) * k, cy + (x * sa + y * ca) * k
    mantle = _kurva([(150, 0), (110, -24), (40, -30), (-10, -24), (-30, 0), (-10, 24), (40, 30), (110, 24)], 8)
    D.poly_on(img, [T(-x, y) for x, y in mantle], col, alpha)
    D.poly_on(img, [T(-150, 0), T(-190, -40), T(-170, 0), T(-190, 40)], mix(col, SP0, 0.2), alpha)
    D.dot_on(img, *T(18, -8), 9 * k + 1, (240, 230, 200), alpha)
    D.dot_on(img, *T(19, -8), 5 * k + 1, (20, 10, 10), alpha)
    for j in range(8):
        oy = -16 + j * 4.5
        pts = [T(30 + u * 140, oy + (j - 3.5) * u * 12 + 10 * math.sin(tg * 2 + j + u * 6) * u) for u in
               [q / 12 for q in range(13)]]
        M._pline(img, pts, mix(col, SP0, 0.1), max(2, 9 * k * (1.2 - 0.2 * j / 8)), alpha)
    for j in (-1, 1):
        pts = [T(30 + u * 250, j * (6 + u * 20) + 14 * math.sin(tg * 1.6 + j + u * 5) * u) for u in
               [q / 18 for q in range(19)]]
        M._pline(img, pts, mix(col, WHITE, 0.1), max(2, 5 * k), alpha)
        D.dot_on(img, pts[-1][0], pts[-1][1], 9 * k, mix(col, WHITE, 0.1), alpha)


def ikan_siput(img, cx, cy, L_, tg, alpha=1.0, flip=False):
    """Ikan siput hadal: pucat merah muda, tembus pandang, kepala bulat besar, ekor meruncing panjang."""
    fase = int((tg * 4) % 6)

    def fn(dd, f, im, fase=fase):
        col = (240, 208, 214)
        us = [q / 12 for q in range(13)]
        sw = [math.sin(fase / 6 * 6.283 + u * 5) * 5 * u * u for u in us]
        xs = [132 - u * 126 for u in us]
        top = [(xs[i], 20 + 15 * u ** 0.8 + sw[i]) for i, u in enumerate(us)]
        bot = [(xs[i], 58 - 17 * u ** 0.8 + sw[i]) for i, u in enumerate(us)]
        fin_t = [(p[0], p[1] - 9 * math.sin(math.pi * min(1, u * 1.1))) for p, u in zip(top, us)]
        fin_b = [(p[0], p[1] + 10 * math.sin(math.pi * min(1, u * 1.1))) for p, u in zip(bot, us)]
        dd.polygon(_P(fin_t + top[::-1], f), fill=(250, 226, 232, 110))
        dd.polygon(_P(bot + fin_b[::-1], f), fill=(250, 226, 232, 110))
        dd.polygon(_P(top + bot[::-1], f), fill=col + (225,))
        for i in range(1, 12):
            dd.line(_P([top[i], bot[i]], f), fill=(220, 180, 190, 90), width=max(1, int(0.8 * f)))
        _E(dd, f, 112, 12, 166, 66, (246, 216, 222), 245)
        _E(dd, f, 118, 34, 140, 56, (226, 170, 182), 120)
        _E(dd, f, 146, 26, 156, 36, (26, 18, 28))
        _E(dd, f, 148, 27, 151, 30, (255, 255, 255))
        dd.arc([140 * f, 40 * f, 166 * f, 58 * f], 20, 110, fill=(200, 150, 160, 255), width=int(1.5 * f))
        dd.polygon(_P([(126, 52), (112, 70), (134, 58)], f), fill=(255, 232, 238, 170))
    spr = sprite(("siput2", fase), 170, 80, fn)
    taruh(img, spr, cx, cy, alpha, L_ / 170.0, flip)


def amfipoda(img, cx, cy, L_, tg, alpha=1.0, flip=False):
    fase = int((tg * 6) % 4)

    def fn(dd, f, im, fase=fase):
        col = (238, 226, 205)
        for j in range(7):
            x = 20 + j * 10
            y = 30 - 12 * math.sin(j / 6 * math.pi)
            _E(dd, f, x - 8, y - 7, x + 8, y + 9, mix(col, (200, 160, 130), j / 10))
        for j in range(6):
            x = 24 + j * 10
            dd.line([(x * f, 36 * f), ((x - 4 + (fase % 2) * 3 * (1 if j % 2 else -1)) * f, 48 * f)],
                    fill=(210, 190, 170, 255), width=int(1.6 * f))
        _E(dd, f, 84, 16, 98, 30, col)
        _E(dd, f, 90, 19, 94, 23, (30, 20, 20))
        dd.line([(96 * f, 18 * f), (106 * f, 4 * f)], fill=(220, 200, 180, 255), width=int(1.4 * f))
        dd.line([(92 * f, 17 * f), (98 * f, 2 * f)], fill=(220, 200, 180, 255), width=int(1.4 * f))
    spr = sprite(("amfi", fase), 110, 54, fn)
    taruh(img, spr, cx, cy, alpha, L_ / 110.0, flip)


def kepiting(img, cx, cy, L_, tg, alpha=1.0, col=(236, 228, 218)):
    fase = int((tg * 4) % 2)

    def fn(dd, f, im, fase=fase):
        for s_ in (-1, 1):
            for j in range(3):
                x0 = 50 + s_ * (14 + j * 6)
                dd.line([(x0 * f, 40 * f), ((50 + s_ * (34 + j * 8)) * f, (30 + (fase if j % 2 else 1 - fase) * 4) * f),
                         ((50 + s_ * (40 + j * 8)) * f, 56 * f)], fill=mix(col, SP0, 0.2) + (255,), width=int(2.4 * f))
            dd.line([((50 + s_ * 18) * f, 30 * f), ((50 + s_ * 30) * f, 14 * f)], fill=col + (255,), width=int(3 * f))
            _E(dd, f, 50 + s_ * 30 - 7, 4, 50 + s_ * 30 + 7, 18, col)
        _E(dd, f, 26, 24, 74, 50, col)
        _E(dd, f, 32, 26, 68, 38, mix(col, WHITE, 0.4), 160)
        _E(dd, f, 41, 22, 45, 26, (20, 20, 20))
        _E(dd, f, 55, 22, 59, 26, (20, 20, 20))
    spr = sprite(("kepiting", col, fase), 100, 60, fn)
    taruh(img, spr, cx, cy, alpha, L_ / 100.0)


def cacing_tabung(img, x, ybase, h, tg, alpha=1.0, seed=0):
    """Rumpun cacing tabung: tabung putih + bulu merah bergoyang."""
    rng = random.Random(seed)
    for j in range(7):
        ox = (j - 3) * 16 + rng.uniform(-5, 5)
        hh = h * rng.uniform(0.6, 1.0)
        sw = 6 * math.sin(tg * 1.4 + j)
        top = (x + ox + sw, ybase - hh)
        D.line_on(img, (x + ox, ybase), top, (226, 222, 210), 11, alpha)
        D.line_on(img, (x + ox - 2, ybase), (top[0] - 2, top[1] + 6), (250, 248, 240), 3, alpha * 0.8)
        for q in range(5):
            an = -math.pi / 2 + (q - 2) * 0.35 + 0.1 * math.sin(tg * 3 + j + q)
            D.line_on(img, top, (top[0] + 18 * math.cos(an), top[1] + 18 * math.sin(an)), (230, 50, 60), 5, alpha)
        D.dot_on(img, top[0], top[1] - 4, 8, (240, 70, 70), alpha)


# ====================================================================== OBJEK
def kapal(img, cx, cy, L_, alpha=1.0, tg=0.0):
    """Kapal riset di permukaan (cy = garis air)."""
    def fn(dd, f, im):
        dd.polygon(_P([(8, 60), (300, 60), (320, 42), (0, 42)], f), fill=(236, 240, 246, 255))
        dd.polygon(_P([(14, 60), (296, 60), (286, 78), (30, 78)], f), fill=(200, 60, 60, 255))
        dd.rectangle([0, 58 * f, 320 * f, 62 * f], fill=(30, 40, 60, 255))
        dd.polygon(_P([(170, 42), (170, 18), (248, 18), (262, 42)], f), fill=(246, 248, 252, 255))
        for j in range(5):
            dd.rectangle([(180 + j * 14) * f, 24 * f, (190 + j * 14) * f, 32 * f], fill=(50, 90, 140, 255))
        dd.rectangle([200 * f, 4 * f, 206 * f, 18 * f], fill=(220, 225, 235, 255))
        dd.line(_P([(60, 42), (100, 0), (132, 16)], f), fill=(250, 190, 60, 255), width=int(4 * f))
        dd.line(_P([(132, 16), (132, 40)], f), fill=(60, 60, 70, 255), width=int(1.5 * f))
        dd.text((40 * f, 43 * f), "KLIKTAHU", fill=(30, 50, 90, 255), font=L.font(FB, int(10 * f)))
    spr = sprite("kapal", 320, 80, fn)
    k = L_ / 320.0
    taruh(img, spr, cx, cy - 8 * k + 3 * math.sin(tg * 1.3), alpha, k, rot=1.2 * math.sin(tg * 0.9))


def penyelam(img, cx, cy, L_, tg, alpha=1.0, rot=0.0):
    """Penyelam scuba (kepala ke kanan), kaki mengayuh."""
    fase = int((tg * 4) % 6)

    def fn(dd, f, im, fase=fase):
        k1 = math.sin(fase / 6 * 6.283) * 8
        suit = (30, 34, 44)
        dd.line(_P([(70, 40), (38, 34 + k1 * 0.4), (14, 30 + k1)], f), fill=suit + (255,), width=int(9 * f))
        dd.line(_P([(70, 44), (38, 48 - k1 * 0.4), (14, 52 - k1)], f), fill=suit + (255,), width=int(9 * f))
        dd.polygon(_P([(16, 26 + k1), (-2 + 2, 16 + k1), (4, 38 + k1)], f), fill=(250, 200, 50, 255))
        dd.polygon(_P([(16, 48 - k1), (2, 44 - k1), (6, 64 - k1)], f), fill=(250, 200, 50, 255))
        dd.rounded_rectangle([64 * f, 30 * f, 130 * f, 54 * f], radius=int(12 * f), fill=suit + (255,))
        dd.rounded_rectangle([72 * f, 18 * f, 124 * f, 32 * f], radius=int(7 * f), fill=(250, 200, 50, 255))
        dd.line(_P([(112, 44), (140, 58)], f), fill=suit + (255,), width=int(7 * f))
        _E(dd, f, 128, 26, 152, 50, suit)
        dd.rounded_rectangle([140 * f, 30 * f, 156 * f, 42 * f], radius=int(4 * f), fill=(120, 200, 240, 255))
        dd.line(_P([(146, 44), (122, 22)], f), fill=(40, 40, 40, 255), width=int(2 * f))
    spr = sprite(("selam", fase), 160, 70, fn)
    taruh(img, spr, cx, cy, alpha, L_ / 160.0, rot=rot)


def gelembung(img, x, y, tg, alpha=1.0, n=8, tinggi=260, seed=0, r=6):
    rng = random.Random(seed)
    for j in range(n):
        u = (tg * rng.uniform(0.35, 0.6) + j / n) % 1.0
        rr = r * rng.uniform(0.5, 1.2) * (0.6 + 0.6 * u)
        xx = x + 10 * math.sin(tg * 3 + j) + rng.uniform(-14, 14)
        yy = y - u * tinggi
        D.ring_on(img, xx, yy, rr, (215, 240, 255), 2, alpha * (1 - u) * 0.9)
        D.dot_on(img, xx - rr * 0.3, yy - rr * 0.3, rr * 0.25, WHITE, alpha * (1 - u))


_SOR = L._cache()


def sorot(img, x, y, ang, pj, lebar_, alpha=1.0, col=(200, 235, 255)):
    """Kerucut sorot lampu kapal selam (sprite lembut ter-cache, diputar)."""
    if alpha <= 0.01:
        return
    key = (col, int(pj / 20), int(lebar_ / 20), int(ang), round(D.SS, 3))
    s = _SOR.get(key)
    if s is None:
        base = _SOR.get(("base", col, round(D.SS, 3)))
        if base is None:
            w_, h_ = int(S(300)), int(S(150))
            yy, xx = np.mgrid[0:h_, 0:w_].astype(np.float32)
            u = xx / (w_ - 1)
            half = (0.12 + 0.88 * u) * 0.5
            v = np.abs(yy / (h_ - 1) - 0.5)
            m = np.clip(1 - v / np.maximum(half, 1e-3), 0, 1) ** 0.8 * (1 - u) ** 1.2 * 150
            arr = np.zeros((h_, w_, 4), np.uint8)
            arr[..., 0], arr[..., 1], arr[..., 2] = col
            arr[..., 3] = np.clip(m, 0, 255).astype(np.uint8)
            base = Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(S(4)))
            _SOR[("base", col, round(D.SS, 3))] = base
        s = base.resize((max(2, int(S(pj))), max(2, int(S(lebar_)))), Image.BILINEAR)
        s = s.rotate(-ang, resample=Image.BICUBIC, expand=True)
        if len(_SOR) > 120:
            _SOR.clear()
        _SOR[key] = s
    an = math.radians(ang)
    L._put_c(img, s, x + math.cos(an) * pj / 2, y + math.sin(an) * pj / 2, alpha)


def dasar_laut(img, y, alpha=1.0, col=(46, 44, 52), seed=3, batu=True, terang=0.0):
    """Dasar laut bergelombang dari y ke bawah + batu."""
    if alpha <= 0.01:
        return
    rng = random.Random(seed)
    pts = [(-20, H + 20)]
    for j in range(25):
        x = -20 + (W + 40) * j / 24
        pts.append((x, y + 14 * math.sin(j * 1.3 + seed) + 8 * math.sin(j * 3.1 + seed * 2)))
    pts.append((W + 20, H + 20))
    D.poly_on(img, pts, mix(col, WHITE, 0.06 + terang * 0.1), alpha)
    pts2 = [(p[0], p[1] + 26) for p in pts[1:-1]]
    D.poly_on(img, [(-20, H + 20)] + pts2 + [(W + 20, H + 20)], mix(col, SP0, 0.35), alpha)
    if batu:
        for j in range(9):
            bx = rng.uniform(60, W - 60)
            by = y + rng.uniform(4, 60)
            r = rng.uniform(10, 34)
            D.poly_on(img, [(bx - r, by + r * 0.3), (bx - r * 0.6, by - r * 0.5), (bx + r * 0.3, by - r * 0.6),
                            (bx + r, by + r * 0.3)], mix(col, SP0, 0.15), alpha)


def titanic(img, cx, cy, L_, alpha=1.0, terang=1.0):
    """Haluan Titanic yang karam (cy = dasar lumpur)."""
    def fn(dd, f, im):
        hull = (86, 58, 44)
        dd.polygon(_P([(20, 150), (0, 70), (40, 64), (560, 58), (600, 20), (620, 22), (596, 150)], f),
                   fill=hull + (255,))
        dd.polygon(_P([(40, 64), (560, 58), (600, 20), (608, 22), (568, 72), (42, 78)], f), fill=(120, 84, 60, 255))
        for j in range(16):
            x = 80 + j * 30
            _E(dd, f, x, 90, x + 8, 98, (30, 22, 20))
            if j % 3 == 0:
                _E(dd, f, x + 8, 112, x + 14, 118, (30, 22, 20))
        for j in range(40):
            x = 40 + j * 13
            dd.line([(x * f, 52 * f), (x * f, 64 * f)], fill=(140, 100, 70, 255), width=int(1.3 * f))
        dd.line([(40 * f, 52 * f), (560 * f, 46 * f)], fill=(140, 100, 70, 255), width=int(1.6 * f))
        dd.line(_P([(430, 58), (440, -30)], f), fill=(110, 80, 60, 255), width=int(5 * f))
        dd.line(_P([(440, -30), (500, -60)], f), fill=(110, 80, 60, 200), width=int(2 * f))
        dd.polygon(_P([(120, 60), (140, 20), (260, 22), (270, 60)], f), fill=(96, 68, 52, 255))
        for j in range(6):
            dd.rectangle([(146 + j * 18) * f, 30 * f, (156 + j * 18) * f, 40 * f], fill=(30, 22, 20, 255))
        for j in range(26):
            rx = random.Random(j).uniform(20, 590)
            ry = random.Random(j + 40).uniform(66, 146)
            rr = random.Random(j + 80).uniform(3, 10)
            dd.polygon(_P([(rx, ry), (rx + rr, ry + rr * 2.5), (rx - rr * 0.6, ry + rr * 2)], f), fill=(170, 90, 50, 220))
        dd.polygon(_P([(-20, 150), (640, 150), (640, 170), (-20, 170)], f), fill=(52, 48, 52, 255))
        dd.polygon(_P([(-20, 140), (60, 128), (140, 146), (640, 144), (640, 160), (-20, 160)], f), fill=(64, 58, 60, 255))
    spr = sprite("titanic", 640, 170, fn)
    k = L_ / 640.0
    taruh(img, spr, cx, cy - 70 * k, alpha, k)


def gelas(img, cx, cy, h, alpha=1.0, label=True, keriput=0.0):
    """Gelas styrofoam (cx, cy = tengah)."""
    kq = int(round(clamp(keriput) * 4))

    def fn(dd, f, im, kq=kq):
        kr = kq / 4
        pts = [(10, 6), (90, 6), (76 + kr * 3, 130), (24 - kr * 3, 130)]
        dd.polygon(_P(pts, f), fill=(246, 244, 238, 255))
        dd.polygon(_P([(10, 6), (26, 6), (32, 130), (24, 130)], f), fill=(226, 224, 218, 255))
        dd.rounded_rectangle([4 * f, 0, 96 * f, 14 * f], radius=int(6 * f), fill=(252, 252, 248, 255))
        if label:
            dd.text((50 * f, 70 * f), "KLIKTAHU", fill=(242, 153, 74, 255), font=L.font(FB, int(9 * f)), anchor="mm")
        for j in range(int(kr * 6)):
            y = 30 + j * 16
            dd.line(_P([(20 + j % 2 * 6, y), (80 - j % 3 * 5, y + 4)], f), fill=(200, 198, 190, 255), width=int(1.4 * f))
    spr = sprite(("gelas", label, kq), 100, 132, fn)
    taruh(img, spr, cx, cy, alpha, h / 132.0)


def cerobong(img, cx, ybase, h, tg, alpha=1.0, asap=1.0, tinggi=1.6):
    """Cerobong ventilasi hidrotermal + semburan air hitam panas."""
    def fn(dd, f, im):
        col = (70, 58, 56)
        pts = _kurva([(40, 0), (58, 20), (54, 60), (70, 120), (64, 180), (92, 240), (-12, 240), (16, 180),
                      (10, 120), (26, 60), (22, 20)], 6)
        dd.polygon(_P(pts, f), fill=col + (255,))
        for j in range(22):
            x = random.Random(j).uniform(10, 70)
            y = random.Random(j + 9).uniform(10, 230)
            dd.ellipse([(x - 6) * f, (y - 4) * f, (x + 6) * f, (y + 4) * f], fill=(100, 84, 72, 255))
        dd.polygon(_P([(24, 2), (56, 2), (50, 12), (30, 12)], f), fill=(255, 140, 60, 255))
    spr = sprite("cerobong", 80, 240, fn)
    k = h / 240.0
    taruh(img, spr, cx, ybase - h / 2, alpha, k)
    top = (cx, ybase - h + 6 * k)
    glow(img, top[0], top[1], 60 * k + 10, (255, 140, 60), 0.5 * alpha)
    if asap > 0.01:
        for j in range(14):
            u = (tg * 0.45 + j / 14) % 1.0
            r = (14 + 90 * u) * k
            x = top[0] + 40 * k * math.sin(j * 1.7 + tg * 0.8) * u + 60 * k * u
            y = top[1] - u * h * tinggi
            c = mix((30, 26, 30), (60, 58, 66), u)
            D.dot_on(img, x, y, r, c, alpha * asap * 0.75 * (1 - u) ** 0.8)


def everest(img, cx, ybase, h, alpha=1.0):
    def fn(dd, f, im):
        dd.polygon(_P([(0, 300), (150, 40), (190, 0), (240, 60), (300, 120), (400, 300)], f), fill=(92, 96, 110, 255))
        dd.polygon(_P([(190, 0), (240, 60), (220, 300), (150, 300)], f), fill=(70, 74, 88, 255))
        dd.polygon(_P([(150, 40), (190, 0), (240, 60), (218, 58), (196, 76), (172, 56)], f), fill=(245, 248, 252, 255))
    spr = sprite("everest", 400, 300, fn)
    k = h / 300.0
    taruh(img, spr, cx, ybase - h / 2, alpha, k)


def mobil(img, cx, cy, L_, alpha=1.0, rot=0.0, col=(235, 87, 87)):
    def fn(dd, f, im):
        dd.rounded_rectangle([0, 34 * f, 200 * f, 70 * f], radius=int(14 * f), fill=col + (255,))
        dd.polygon(_P([(40, 36), (66, 6), (140, 6), (168, 36)], f), fill=col + (255,))
        dd.polygon(_P([(56, 34), (72, 12), (100, 12), (100, 34)], f), fill=(170, 220, 245, 255))
        dd.polygon(_P([(108, 34), (108, 12), (136, 12), (154, 34)], f), fill=(170, 220, 245, 255))
        for x in (46, 154):
            _E(dd, f, x - 20, 52, x + 20, 92, (30, 30, 36))
            _E(dd, f, x - 9, 63, x + 9, 81, (190, 190, 200))
        _E(dd, f, 186, 42, 198, 52, (255, 230, 150))
    spr = sprite(("mobil", col), 200, 92, fn)
    taruh(img, spr, cx, cy, alpha, L_ / 200.0, rot=rot)


def trieste(img, cx, cy, L_, alpha=1.0, tg=0.0, lampu=1.0):
    def fn(dd, f, im):
        dd.rounded_rectangle([0, 10 * f, 300 * f, 80 * f], radius=int(35 * f), fill=(214, 218, 222, 255))
        dd.rounded_rectangle([0, 56 * f, 300 * f, 80 * f], radius=int(12 * f), fill=(180, 186, 192, 255))
        dd.rectangle([120 * f, 0, 170 * f, 12 * f], fill=(200, 60, 50, 255))
        dd.rectangle([138 * f, 80 * f, 150 * f, 100 * f], fill=(120, 126, 132, 255))
        _E(dd, f, 110, 94, 178, 162, (60, 70, 84))
        _E(dd, f, 118, 100, 150, 130, (90, 102, 118), 200)
        _E(dd, f, 150, 120, 164, 134, (255, 220, 140))
        dd.text((150 * f, 44 * f), "TRIESTE", fill=(60, 70, 90, 255), font=L.font(FB, int(20 * f)), anchor="mm")
    spr = sprite("trieste", 300, 164, fn)
    k = L_ / 300.0
    y = cy + 5 * math.sin(tg * 0.8)
    taruh(img, spr, cx, y, alpha, k)
    if lampu > 0.01:
        glow(img, cx + (157 - 150) * k, y + (127 - 82) * k, 40 * k, (255, 220, 150), 0.6 * lampu * alpha)


def deepsea_challenger(img, cx, cy, h, alpha=1.0, tg=0.0):
    def fn(dd, f, im):
        dd.rounded_rectangle([20 * f, 0, 70 * f, 300 * f], radius=int(24 * f), fill=(170, 220, 60, 255))
        dd.rounded_rectangle([20 * f, 0, 36 * f, 300 * f], radius=int(10 * f), fill=(140, 190, 40, 255))
        dd.rectangle([6 * f, 230 * f, 84 * f, 262 * f], fill=(60, 66, 76, 255))
        _E(dd, f, 20, 250, 70, 300, (60, 66, 76))
        for j in range(4):
            _E(dd, f, 34 + j * 6, 238, 40 + j * 6, 244, (255, 230, 160))
        dd.text((45 * f, 120 * f), "DC", fill=(40, 60, 20, 255), font=L.font(FB, int(14 * f)), anchor="mm")
    spr = sprite("dsc", 90, 300, fn)
    taruh(img, spr, cx, cy + 4 * math.sin(tg), alpha, h / 300.0)


def kapal_selam(img, cx, cy, L_, alpha=1.0, remuk=0.0, col=(246, 200, 90)):
    """Kapal selam biasa; remuk 0..1 = penyok ditekan air."""
    rq = int(round(clamp(remuk) * 5))

    def fn(dd, f, im, rq=rq):
        r_ = rq / 5
        top = [(20 + x * 20, 30 + r_ * 14 * math.sin(x * 1.3) ** 2) for x in range(12)]
        bot = [(20 + x * 20, 90 - r_ * 14 * math.cos(x * 1.1) ** 2) for x in range(12)][::-1]
        dd.polygon(_P([(0, 60)] + top + [(250, 60)] + bot, f), fill=col + (255,))
        dd.polygon(_P([(100, 34 + r_ * 6), (110, 6 + r_ * 8), (160, 6 + r_ * 8), (170, 34 + r_ * 6)], f), fill=col + (255,))
        for j in range(3):
            _E(dd, f, 80 + j * 40, 52, 96 + j * 40, 68, (40, 70, 110))
        dd.polygon(_P([(0, 60), (-16, 40), (-16, 80)], f), fill=mix(col, SP0, 0.3) + (255,))
    spr = sprite(("ksl", col, rq), 256, 96, fn)
    taruh(img, spr, cx, cy, alpha, L_ / 256.0)


def kantong_plastik(img, cx, cy, h, tg, alpha=1.0):
    def fn(dd, f, im):
        body = _kurva([(20, 40), (40, 30), (60, 34), (80, 30), (100, 40), (104, 110), (86, 140), (60, 146),
                       (30, 140), (14, 110)], 8)
        dd.polygon(_P(body, f), fill=(236, 240, 244, 190))
        dd.arc([22 * f, 0, 52 * f, 50 * f], 180, 360, fill=(236, 240, 244, 230), width=int(6 * f))
        dd.arc([66 * f, 0, 96 * f, 50 * f], 180, 360, fill=(236, 240, 244, 230), width=int(6 * f))
        for j in range(6):
            dd.line(_P([(30 + j * 12, 50), (26 + j * 13, 130)], f), fill=(200, 208, 216, 200), width=int(2 * f))
        dd.text((60 * f, 96 * f), "SHOP", fill=(210, 80, 80, 200), font=L.font(FB, int(15 * f)), anchor="mm")
    spr = sprite("kantong", 120, 150, fn)
    taruh(img, spr, cx, cy + 4 * math.sin(tg * 0.9), alpha, h / 150.0, rot=4 * math.sin(tg * 0.6))


def bulan(img, cx, cy, r, alpha=1.0):
    def fn(dd, f, im):
        _E(dd, f, 0, 0, 200, 200, (196, 198, 206))
        for x, y, rr in [(60, 60, 22), (130, 50, 14), (120, 120, 30), (50, 140, 16), (160, 150, 12), (90, 96, 10)]:
            _E(dd, f, x - rr, y - rr, x + rr, y + rr, (160, 162, 172))
            _E(dd, f, x - rr * 0.8, y - rr * 0.9, x + rr * 0.7, y + rr * 0.5, (176, 178, 188))
    spr = sprite("bulan", 200, 200, fn)
    glow(img, cx, cy, r * 1.8, (200, 210, 240), 0.2 * alpha)
    taruh(img, spr, cx, cy, alpha, r / 100.0)


def matahari(img, cx, cy, r, tg, alpha=1.0, col=(255, 210, 90)):
    if alpha <= 0.01:
        return
    glow(img, cx, cy, r * 3, col, 0.35 * alpha)
    for j in range(12):
        an = j * math.pi / 6 + tg * 0.3
        D.line_on(img, (cx + r * 1.3 * math.cos(an), cy + r * 1.3 * math.sin(an)),
                  (cx + r * 1.75 * math.cos(an), cy + r * 1.75 * math.sin(an)), col, max(3, r * 0.14), alpha)
    D.dot_on(img, cx, cy, r, col, alpha)
    D.dot_on(img, cx - r * 0.2, cy - r * 0.2, r * 0.6, mix(col, WHITE, 0.4), alpha * 0.6)


def termometer(img, cx, cy, h, isi, alpha=1.0, col=MERAH, label=""):
    """Termometer vertikal; isi 0..1."""
    if alpha <= 0.01:
        return
    D.rrect_on(img, cx - 18, cy - h / 2, cx + 18, cy + h / 2, 18, (230, 236, 244), alpha)
    D.dot_on(img, cx, cy + h / 2, 34, (230, 236, 244), alpha)
    D.dot_on(img, cx, cy + h / 2, 24, col, alpha)
    top = cy + h / 2 - (h - 20) * clamp(isi)
    D.rrect_on(img, cx - 9, top, cx + 9, cy + h / 2, 9, col, alpha)
    for j in range(6):
        y = cy - h / 2 + 20 + j * (h - 40) / 5
        D.line_on(img, (cx + 20, y), (cx + 32, y), (230, 236, 244), 3, alpha * 0.7)
    if label:
        teks(img, cx + 46, top, label, 36, TEKS, alpha, name=FB, anchor="l")


def cincin_persen(img, cx, cy, r, p, alpha=1.0, col=SIAN, wd=26):
    if alpha <= 0.01:
        return
    D.ring_on(img, cx, cy, r, mix(col, SP0, 0.7), wd, alpha)
    n = max(2, int(60 * p))
    pts = [(cx + r * math.cos(-math.pi / 2 + 6.283 * p * j / n), cy + r * math.sin(-math.pi / 2 + 6.283 * p * j / n))
           for j in range(n + 1)]
    M._pline(img, pts, col, wd, alpha)


def jari(img, cx, ytop, alpha=1.0, k=1.0):
    def fn(dd, f, im):
        col = (232, 184, 150)
        dd.rounded_rectangle([0, 0, 80 * f, 330 * f], radius=int(40 * f), fill=col + (255,))
        dd.rounded_rectangle([14 * f, 10 * f, 66 * f, 70 * f], radius=int(22 * f), fill=(246, 214, 196, 255))
        for y in (140, 150, 240, 250):
            dd.arc([16 * f, (y - 8) * f, 64 * f, (y + 8) * f], 20, 160, fill=(200, 150, 120, 255), width=int(2 * f))
    spr = sprite("jari", 80, 330, fn)
    taruh(img, spr, cx, ytop + 165 * k, alpha, k)


def profil_zona(img, x0, y0, x1, y1, alpha, aktif=None, prog=1.0, label=True, tg=0.0, fsz=26):
    """Kolom laut 5 zona (skala akar). aktif = indeks zona yang disorot (atau None)."""
    if alpha <= 0.01:
        return []
    hh = y1 - y0
    pos = []
    for j, (z0, z1, nama, col) in enumerate(ZONA):
        a0 = y0 + hh * math.sqrt(z0 / 11000.0)
        a1 = y0 + hh * math.sqrt(z1 / 11000.0)
        q = clamp(prog * 5 - j)
        if q <= 0:
            pos.append((a0, a1))
            continue
        top, bot = _warna_air((z0 + z1) / 2)
        on = aktif == j
        D.rrect_on(img, x0, a0 + 2, x0 + (x1 - x0) * eo(q), a1 - 2, 10, mix(top, col, 0.22 if not on else 0.45),
                   alpha * (0.95 if on or aktif is None else 0.55))
        if on:
            D.rrect_on(img, x0 - 4, a0 - 2, x1 + 4, a1 + 2, 12, col, alpha * 0.9, outline=col, width=4)
            D.rrect_on(img, x0, a0 + 2, x1, a1 - 2, 10, mix(top, col, 0.35), alpha)
        if label and q > 0.6:
            la = alpha * clamp((q - 0.6) / 0.4) * (1.0 if on or aktif is None else 0.6)
            teks(img, x0 + 26, (a0 + a1) / 2, nama, fsz, col if not on else WHITE, la, name=FB, anchor="l")
            teks(img, x1 - 20, (a0 + a1) / 2, fmt_id(z0) + " - " + fmt_id(z1 if z1 < 11000 else 10935) + " m",
                 fsz * 0.72, REDUP if not on else TEKS, la, name=FS, anchor="r")
        pos.append((a0, a1))
    return pos


# ====================================================================== util adegan
def _langit(w, h):
    def fn(dd, f, im):
        for j in range(60):
            u = j / 59
            c = mix((70, 150, 225), (200, 232, 248), u ** 1.4)
            dd.rectangle([0, j * h / 60 * f, w * f, (j + 1) * h / 60 * f + 2], fill=c + (255,))
    return sprite(("langit", w, h), w, h, fn, ov=1)


def _gelap_bawah():
    def fn(dd, f, im):
        for j in range(80):
            u = j / 79
            dd.rectangle([0, j * 15 * f, W * f, (j + 1) * 15 * f + 2], fill=(3, 8, 22, int(255 * clamp(u * 1.3) ** 1.2)))
    return sprite("gelapbawah", W, 1200, fn, ov=1)


def tetes(img, cx, cy, r, col, alpha=1.0):
    pts = [(cx + r * math.cos(a_), cy + r * math.sin(a_)) for a_ in [math.pi * (-0.15 + 1.3 * q / 20) for q in range(21)]]
    pts = [(cx, cy - r * 2.3)] + pts
    D.poly_on(img, pts, col, alpha)
    D.dot_on(img, cx - r * 0.35, cy - r * 0.1, r * 0.22, mix(col, WHITE, 0.6), alpha * 0.8)


def kepala(img, cx, cy, s, alpha=1.0, col=(214, 222, 236)):
    """Siluet kepala profil menghadap kanan + telinga (cx, cy = telinga)."""
    def fn(dd, f, im):
        prof = _kurva([(40, 150), (20, 100), (30, 50), (70, 18), (120, 10), (165, 30), (180, 70), (184, 92),
                       (198, 116), (186, 124), (188, 140), (180, 150), (184, 162), (168, 176), (150, 180),
                       (140, 200), (140, 240), (60, 240), (64, 190)], 8)
        dd.polygon(_P(prof, f), fill=col + (255,))
        _E(dd, f, 80, 88, 108, 130, mix(col, SP0, 0.22))
        _E(dd, f, 87, 98, 101, 120, mix(col, SP0, 0.4))
    spr = sprite(("kepala", col), 200, 240, fn)
    taruh(img, spr, cx + (100 - 94) * s, cy + (120 - 109) * s, alpha, s)


def kelp(img, x, ybase, h, tg, alpha=1.0, col=(70, 160, 90), seed=0):
    rng = random.Random(seed)
    for j in range(5):
        ox = (j - 2) * 26 + rng.uniform(-6, 6)
        hh = h * rng.uniform(0.7, 1.0)
        pts = [(x + ox + 18 * math.sin(tg * 1.1 + j + u * 3) * u, ybase - hh * u) for u in [q / 12 for q in range(13)]]
        M._pline(img, pts, col, 9, alpha)
        for q in range(2, 12, 2):
            p = pts[q]
            s_ = 1 if q % 4 else -1
            D.poly_on(img, [p, (p[0] + s_ * 26, p[1] - 14), (p[0] + s_ * 8, p[1] - 4)], mix(col, WHITE, 0.15), alpha)


def panah_tekan(img, cx, cy, r, tt, alpha=1.0, n=8, col=(120, 200, 255)):
    """Panah-panah menekan ke dalam (tekanan)."""
    if tt <= 0 or alpha <= 0.01:
        return
    q = eo(clamp(tt / 0.5))
    for j in range(n):
        an = j * 6.283 / n + 0.2
        pul = 8 * math.sin(tt * 6 + j)
        r0 = r + 110 - 30 * q + pul
        r1 = r + 20 + pul
        panah(img, (cx + r0 * math.cos(an), cy + r0 * math.sin(an)), (cx + r1 * math.cos(an), cy + r1 * math.sin(an)),
              col, 6, alpha * q, 1.0, 22)


def salju_tebal(img, tg, alpha=1.0, n=90, seed=5):
    rng = random.Random(seed)
    for j in range(n):
        x0 = rng.random() * W
        sp = rng.uniform(18, 45)
        y = (rng.random() * H + tg * sp) % H
        x = x0 + 12 * math.sin(tg * 0.6 + j)
        r = rng.uniform(2.0, 5.0)
        D.dot_on(img, x, y, r, (236, 240, 245), alpha * rng.uniform(0.5, 1.0))


def _kelip_on(C):
    if C.sc["visual"] == "v02_malam":
        return clamp((C.tl - C.w("lihat", 1, -0.4)) / 0.6)
    return 1.0


# ============================================================ BAB 0 - PEMBUKA
def v02_intro(img, C):
    tl, tg = C.tl, C.tg
    t_set = C.w("setiap", 1, -0.3)
    t_sep = C.w("sepanjang", 1, -0.4)
    t_anh = C.w("anehnya", 1, -0.3)
    t_tar = C.w("tarik", 1, -0.3)
    # ---- shot A: kapal di permukaan -> kamera turun melihat 11 km air di bawah
    a = C.win(-1, t_set, 0.01, 0.5)
    if a > 0.01:
        pan = eio(C.u("bawah", 2.0, 1, -0.3))
        wl = 540 - 470 * pan
        taruh(img, _langit(W, 620), W / 2, wl - 310, a)
        matahari(img, 1540, wl - 360, 60, tg, a)
        D.rrect_on(img, -10, wl - 6, W + 10, wl + 10, 0, (180, 225, 245), a * 0.8)
        for j in range(3):
            gelombang(img, -20, W + 20, wl + 4 + j * 16, 5, 180 + j * 40, tg * (1.2 + j * 0.3) + j, (215, 240, 255), 3, a * (0.8 - j * 0.2))
        kapal(img, 960, wl + 6, 560, a, tg)
        taruh(img, _gelap_bawah(), W / 2, wl + 120 + 600 + 300 * (1 - pan), a * pan)
        teks(img, 960, wl - 250, "SAMUDRA PASIFIK", 30, WHITE, a * C.u("pasifik", 0.4, 1, -0.3) * (1 - pan), name=FB,
             stroke=3, scol=(20, 60, 100))
        # garis duga turun
        g = C.u("sedalam", 3.0, 1, -0.3, ease=eio)
        if g > 0:
            y1 = wl + 60 + (960 - wl - 60) * g
            D.line_on(img, (960, max(wl + 60, 0)), (960, y1), (230, 240, 255), 4, a * 0.9, dash=18)
            D.dot_on(img, 960, y1, 9, EMAS, a)
            glow(img, 960, y1, 60, EMAS, 0.4 * a)
        angka(img, 1340, 470, 10935, C.tt("sebelas", 1, -0.4), fsz=120, dur=2.0, suf=" m", alpha=a,
              sub="HAMPIR 11 KILOMETER AIR DI BAWAH KAKIMU", subfsz=28)
        stiker(img, 1340, 700, "TITIK TERDALAM DI BUMI", C.tt("dasarnya", 1, -0.2), bg=MERAH, fsz=36, tg=tg, alpha=a)
        callout(img, (960, 960), (600, 900), "DASAR", C.tt("menyelam", 1, -0.2), acc=EMAS, alpha=a * (pan > 0.9))
    # ---- shot B: dunia berubah tiap beberapa ratus meter
    a = C.win(t_set, t_sep, 0.5, 0.5)
    if a > 0.01:
        D.rrect_on(img, -10, -10, W + 10, H + 10, 0, (4, 16, 40), 0.35 * a)
        judul(img, 960, 210, "SETIAP BEBERAPA RATUS METER, DUNIA BERUBAH", tl - t_set - 0.1, fsz=56,
              hl=("BERUBAH",), alpha=a, maxw=1600)
        kartu = [("cahaya", 1, "CAHAYA HILANG", EMAS), ("dingin", 1, "AIR MAKIN DINGIN", SIAN),
                 ("tekanannya", 1, "TEKANAN MEREMUKKAN", MERAH)]
        for j, (kw, n, lab, col) in enumerate(kartu):
            q, dy = muncul(C, kw, n, -0.35)
            if q <= 0.01:
                continue
            x = 480 + j * 480
            kaca(img, x - 200, 360 + dy, x + 200, 800 + dy, a * q, col)
            teks(img, x, 740 + dy, lab, 30, TEKS, a * q, name=FB)
            if j == 0:
                redup = 1 - 0.85 * C.u("menghilang", 1.6, 1, -0.2)
                matahari(img, x, 540 + dy, 62, tg, a * q * redup)
                D.dot_on(img, x, 540 + dy, 62, (40, 50, 70), a * q * (1 - redup) * 0.9)
            elif j == 1:
                v = 28 - 26 * C.u("dingin", 2.0, 1, 0.0)
                termometer(img, x - 50, 530 + dy, 230, 0.15 + 0.75 * (v / 28), a * q, col=SIAN)
                teks(img, x + 60, 530 + dy, "%d\u00b0C" % round(v), 52, TEKS, a * q, name=FB)
            else:
                rem = C.u("meremukkan", 0.7, 1, -0.1)
                kapal_selam(img, x, 540 + dy, 230, a * q, rem)
                panah_tekan(img, x, 540 + dy, 110, C.tt("kuat", 1, -0.3), a * q * 0.9, n=6)
    # ---- shot C: yang akan kita temui
    a = C.win(t_sep, t_anh, 0.5, 0.5)
    if a > 0.01:
        D.rrect_on(img, -10, -10, W + 10, H + 10, 0, (4, 12, 30), 0.55 * a)
        teks(img, 960, 190, "DI SEPANJANG JALAN KITA AKAN BERTEMU...", 44, TEKS, a * clamp((tl - t_sep) / 0.5), name=FB)
        items = [("makhluk", "MAKHLUK YANG|MEMBUAT CAHAYA", SIAN), ("bangkai", "BANGKAI KAPAL|PALING TERKENAL", ORANYE),
                 ("sesuatu", "SESUATU YANG TAK|SEHARUSNYA ADA", MERAH)]
        for j, (kw, lab, col) in enumerate(items):
            tt = C.tt(kw, 1, -0.3)
            if tt <= 0:
                continue
            x, y = 500 + j * 460, 540
            pop = eob(clamp(tt / 0.45), 2.0)
            r = 175 * pop
            D.dot_on(img, x, y, r, (6, 14, 32), a)
            if j == 0:
                pemancing(img, x - 10, y + 20, 250 * pop, tg, a, mulut=0.3)
            elif j == 1:
                titanic(img, x, y + 60, 330 * pop, a)
            else:
                gl = 1 if (int(tg * 12) % 7) else 0
                teks(img, x + (4 if not gl else 0), y + 10, "?", int(190 * max(0.2, pop)), MERAH, a * 0.95, name=FB)
            D.ring_on(img, x, y, r, col, 6, a)
            glow(img, x, y, r * 1.3, col, 0.15 * a)
            for m_, ln in enumerate(lab.split("|")):
                teks(img, x, y + 235 + m_ * 38, ln, 28, TEKS, a * clamp((tt - 0.3) / 0.3), name=FB)
    # ---- shot D: peta Bulan lebih lengkap daripada peta dasar laut
    a = C.win(t_anh, t_tar, 0.5, 0.5)
    if a > 0.01:
        D.rrect_on(img, -10, -10, W + 10, H + 10, 0, (4, 12, 30), 0.55 * a)
        judul(img, 960, 180, "ANEHNYA...", tl - t_anh, fsz=62, hl=("ANEHNYA...",), alpha=a)
        q, dy = muncul(C, "bulan", 1, -0.5)
        bulan(img, 600, 520 + dy, 175, a * q)
        teks(img, 600, 780 + dy, "PETA BULAN", 34, TEKS, a * q, name=FB)
        centang(img, 600, 870, 40, C.tt("lengkap", 1, -0.2), alpha=a)
        teks(img, 960, 520, "VS", 60, REDUP, a * C.u("daripada", 0.4, 1, -0.3), name=FB)
        q2, dy2 = muncul(C, "peta", 2, -0.4)
        if q2 > 0.01:
            x0, y0 = 1110, 360
            kaca(img, x0 - 20, y0 - 20 + dy2, x0 + 440, y0 + 330 + dy2, a * q2, SIAN, r=14)
            rng = random.Random(8)
            for gx in range(12):
                for gy in range(9):
                    on = rng.random() < 0.26
                    col = (60, 170, 220) if on else (20, 32, 56)
                    D.rrect_on(img, x0 + gx * 35, y0 + gy * 34 + dy2, x0 + gx * 35 + 31, y0 + gy * 34 + 30 + dy2, 4,
                               col, a * q2 * (0.95 if on else 0.8))
            teks(img, x0 + 210, y0 + 150 + dy2, "?", 150, (120, 140, 180), a * q2 * 0.5, name=FB)
            teks(img, 1320, 780 + dy2, "PETA DASAR LAUT", 34, TEKS, a * q2, name=FB)
            centang(img, 1320, 870, 40, C.tt("sendiri", 1, -0.1), col=MERAH, alpha=a, silang=True)
    # ---- shot E: judul besar + mulai menyelam
    a = C.win(t_tar, C.dur + 1, 0.5, 0.1)
    if a > 0.01:
        tj = C.w("menyelam", 2, 0.0)
        plunge = eio(clamp((tl - tj) / 1.3))
        D.rrect_on(img, -10, -10, W + 10, H + 10, 0, (4, 12, 30), 0.35 * a * (1 - plunge))
        teks(img, 960, 190 - 300 * plunge, "K L I K T A H U   ·   V I D E O   P A N J A N G", 22, EMAS, a * clamp((tl - t_tar) / 0.5),
             name=FB)
        judul(img, 960, 400 - 400 * plunge, "PERJALANAN KE DASAR LAUT TERDALAM DI BUMI", tl - t_tar - 0.1, fsz=84,
              hl=("TERDALAM",), alpha=a, maxw=1400)
        py = 700 + 520 * plunge
        penyelam(img, 960, py + 8 * math.sin(tg * 1.4), 380, tg, a, rot=-90 * plunge - 10)
        gelembung(img, 1000, py - 40, tg, a, n=10, tinggi=380, seed=2, r=8)
        if 0 < tl - tj < 0.6:
            glow(img, 960, 700, 500, (200, 240, 255), 0.4 * (1 - (tl - tj) / 0.6))


# ============================================================ BAB 1 - ZONA MATAHARI
_SPEK = [("MERAH", (235, 70, 60), "merah"), ("JINGGA", (245, 150, 60), "jingga"), ("KUNING", (245, 215, 70), "kuning"),
         ("HIJAU", (90, 200, 110), None), ("BIRU", (70, 150, 240), None), ("NILA", (120, 100, 230), None)]


def v02_matahari(img, C):
    tl, tg = C.tl, C.tg
    t_air = C.w("air", 1, -0.3)
    t_sin = C.w("sini", 1, -0.5)
    t_pny = C.w("penyelam", 1, -0.3)
    t_dua = C.w("dua", 2, -0.7)
    # ---- shot A: penyelam turun
    a = C.win(-1, t_air, 0.01, 0.5)
    if a > 0.01:
        chip(img, CX, 170, "ZONA MATAHARI  ·  0 - 200 m", a * clamp((tl - 3.4) / 0.4), acc=EMAS, fsz=26)
        kawanan(img, CX + 250 - tl * 30, 380, 14, 60, tg, a * 0.8, col=(250, 200, 90), sebar=(260, 90), seed=3)
        penyelam(img, CX - 60, 600 + 12 * math.sin(tg), 460, tg, a, rot=-28)
        gelembung(img, CX + 110, 480, tg, a, n=10, tinggi=420, seed=1, r=9)
        teks(img, CX, 900, "SESUATU YANG ANEH TERJADI PADA WARNA", 36, TEKS, a * C.u("aneh", 0.5, 1, -0.3), name=FB,
             stroke=2, scol=(10, 40, 80))
    # ---- shot B: warna diserap + darah jadi hijau
    a = C.win(t_air, t_sin, 0.5, 0.5)
    if a > 0.01:
        t_krn = C.w("karena", 1, -0.3)
        a1 = a * (1 - clamp((tl - t_krn) / 0.5))
        judul(img, CX, 210, "AIR LAUT MENYERAP WARNA", tl - t_air, fsz=58, hl=("MENYERAP",), alpha=a1)
        for j, (nm, col, kw) in enumerate(_SPEK):
            q = eob(clamp((tl - t_air - 0.1 - j * 0.08) / 0.4), 1.8)
            if q <= 0.01:
                continue
            x = CX - 450 + j * 180
            hh = 380
            hilang = C.u(kw, 0.9, 1, -0.2) if kw else 0.0
            top = 700 - hh * q * (1 - hilang)
            D.rrect_on(img, x - 58, 320, x + 58, 700, 16, (255, 255, 255), a1 * 0.08)
            if top < 699:
                D.rrect_on(img, x - 58, top, x + 58, 700, 16, col, a1)
                glow(img, x, top + 40, 90, col, 0.25 * a1 * (1 - hilang))
            teks(img, x, 750, nm, 26, col if not hilang else REDUP, a1, name=FB)
            if kw:
                silang_besar(img, x, 520, 40, C.tt(kw, 1, 0.3), a1 * 0.95, wd=10)
        # darah
        a2 = a * clamp((tl - t_krn - 0.2) / 0.5)
        if a2 > 0.01:
            teks(img, CX, 200, "DI KEDALAMAN 20 METER...", 48, TEKS, a2, name=FB)
            q1, dy1 = muncul(C, "darah", 1, -0.3)
            tetes(img, CX - 300, 560 + dy1, 90, (215, 40, 50), a2 * q1)
            teks(img, CX - 300, 740 + dy1, "DI PERMUKAAN", 28, REDUP, a2 * q1, name=FB)
            panah(img, (CX - 150, 560), (CX + 150, 560), TEKS, 6, a2, C.u("terlihat", 0.5, 1, -0.2))
            q2, dy2 = muncul(C, "hijau", 1, -0.3)
            col2 = mix((215, 40, 50), (36, 84, 60), eo(clamp(C.tt("hijau", 1, -0.3) / 0.8)))
            tetes(img, CX + 300, 560 + dy2, 90, col2, a2 * q2)
            teks(img, CX + 300, 740 + dy2, "DI 20 METER", 28, REDUP, a2 * q2, name=FB)
            stiker(img, CX + 300, 850, "HIJAU KEHITAMAN, BUKAN MERAH!", C.tt("bukan", 1, -0.2), bg=HIJAU, fsz=32, tg=tg,
                   alpha=a2, fg=(10, 30, 20))
    # ---- shot C: tekanan +1 atm tiap 10 m
    a = C.win(t_sin, t_pny, 0.5, 0.5)
    if a > 0.01:
        judul(img, CX, 170, "TEKANAN MULAI TERASA", tl - t_sin, fsz=54, hl=("TEKANAN",), alpha=a)
        x = CX - 330
        t_set = C.w("setiap", 1, -0.3)
        for j in range(4):
            y = 290 + j * 170
            q = eob(clamp((tl - t_set - j * 0.55) / 0.4), 1.6)
            if q <= 0.01:
                continue
            D.line_on(img, (x - 180, y), (x + 40, y), (200, 225, 245), 3, a * q * 0.8, dash=12)
            teks(img, x - 190, y, "%d m" % (j * 10), 28, TEKS, a * q, name=FB, anchor="r")
            rb = 62 * (j + 1) ** (-1 / 3)
            D.dot_on(img, x + 110, y, rb * q, (242, 110, 90), a)
            D.dot_on(img, x + 110 - rb * 0.3, y - rb * 0.35, rb * 0.25 * q, (255, 200, 190), a)
            chip(img, x + 250, y, "%d atm" % (j + 1), a * q, acc=SIAN, fsz=24)
        t_tel = C.w("telingamu", 1, -0.4)
        ar = a * C.win(C.w("satu", 1, -0.4), t_tel, 0.4, 0.4)
        if ar > 0.01:
            angka(img, CX + 330, 360, 1, C.tt("satu", 1, -0.4), fsz=130, pre="+", suf=" ATM", alpha=ar,
                  sub="SETIAP TURUN 10 METER", subfsz=28)
            q, dy = muncul(C, "sama", 1, -0.3)
            kaca(img, CX + 80, 560 + dy, CX + 580, 820 + dy, ar * q, SIAN)
            teks(img, CX + 330, 610 + dy, "1 ATM =", 34, EMAS, ar * q, name=FB)
            teks(img, CX + 330, 670 + dy, "BERAT SELURUH UDARA", 32, TEKS, ar * q, name=FB)
            teks(img, CX + 330, 720 + dy, "DI ATAS KEPALA KITA", 32, TEKS, ar * q, name=FB)
        ak = a * clamp((tl - t_tel) / 0.4)
        if ak > 0.01:
            kepala(img, CX + 292, 485, 1.6, ak)
            for k in range(3):
                u = ((tg * 1.2) + k / 3) % 1.0
                D.ring_on(img, CX + 292, 485, 30 + 90 * u, MERAH, 5, ak * (1 - u) * C.u("sakit", 0.3, 1, -0.2))
            stiker(img, CX + 300, 800, "TELINGA SAKIT!", C.tt("sakit", 1, -0.2), bg=MERAH, fsz=36, tg=tg, alpha=ak)
    # ---- shot D: 40 m batas penyelam rekreasi vs perjalanan panjang
    a = C.win(t_pny, t_dua, 0.5, 0.5)
    if a > 0.01:
        x = CX + 250
        y0, y1 = 190, 930
        teks(img, CX - 230, 300, "PENYELAM REKREASI", 44, TEKS, a * C.u("penyelam", 0.5, 1, -0.3), name=FB)
        q = C.u("penyelam", 0.6, 1, -0.3)
        D.rrect_on(img, x - 16, y0, x + 16, y0 + (y1 - y0) * q, 8, (30, 60, 110), a)
        D.rrect_on(img, x - 16, y0, x + 16, y0 + 6, 3, EMAS, a)
        teks(img, x + 36, y0, "0 m", 24, TEKS, a, name=FB, anchor="l")
        penyelam(img, x - 120, y0 + 20, 140, tg, a * q, rot=-10)
        callout(img, (x + 16, y0 + 4), (x + 150, y0 + 120), "40 m", C.tt("empat", 1, -0.3), acc=EMAS, fsz=34,
                sub="BATAS REKREASI", alpha=a)
        angka(img, CX - 230, 450, 40, C.tt("empat", 1, -0.3), fsz=170, suf=" m", alpha=a, col=EMAS,
              sub="BATAS AMAN PENYELAM REKREASI", subfsz=28)
        tp = C.tt("panjang", 1, -0.6)
        if tp > 0:
            teks(img, x + 36, y1, "10.935 m", 30, MERAH, a * clamp(tp / 0.4), name=FB, anchor="l")
            panah(img, (x - 60, 400), (x - 60, 880), MERAH, 6, a, esmooth(clamp(tp / 0.8)))
            teks(img, CX - 230, 700, "PERJALANAN KITA", 40, TEKS, a * clamp(tp / 0.4), name=FB)
            teks(img, CX - 230, 755, "MASIH SANGAT PANJANG", 40, MERAH, a * clamp((tp - 0.2) / 0.4), name=FB)
    # ---- shot E: 1% cahaya di 200 m
    a = C.win(t_dua, C.dur + 1, 0.5, 0.1)
    if a > 0.01:
        tt = C.tt("dua", 2, -0.5)
        pc = 100 - 99 * eo(clamp((tl - C.w("dua", 2, -0.5)) / 3.2))
        matahari(img, CX - 300, 470, 90, tg, a * (0.25 + 0.75 * pc / 100))
        angka(img, CX + 220, 440, pc, 5, fsz=190, suf="%", alpha=a * clamp(tt / 0.3), col=EMAS,
              sub="CAHAYA MATAHARI YANG TERSISA DI 200 m", subfsz=28)
        D.rrect_on(img, CX - 520, 700, CX + 520, 730, 15, (255, 255, 255), a * 0.12)
        D.rrect_on(img, CX - 520, 700, CX - 520 + 1040 * max(0.012, pc / 100), 730, 15, EMAS, a)
        stempel(img, CX, 860, "ZONA MATAHARI BERAKHIR", C.tt("berakhir", 1, -0.2), col=EMAS, fsz=52)


# ============================================================ BAB 2 - ZONA SENJA
def _senja_kartu():
    def fn(dd, f, im):
        w_, h_ = 560, 300
        for j in range(60):
            u = j / 59
            c = mix(mix((40, 50, 120), (230, 110, 90), u ** 1.2), (255, 190, 110), max(0, u - 0.7) * 2)
            dd.rectangle([0, j * h_ / 60 * f, w_ * f, ((j + 1) * h_ / 60 + 1) * f], fill=c + (255,))
        _E(dd, f, 230, 190, 330, 290, (255, 214, 130))
        dd.rectangle([0, 240 * f, w_ * f, h_ * f], fill=(24, 30, 70, 255))
        for j in range(8):
            dd.line([((60 + j * 60) * f, (256 + j % 3 * 10) * f), ((100 + j * 60) * f, (256 + j % 3 * 10) * f)],
                    fill=(255, 190, 120, 160), width=int(3 * f))
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=int(26 * f), fill=255)
        im.putalpha(m)
    return sprite("senjakartu", 560, 300, fn)


def v02_senja(img, C):
    tl, tg = C.tl, C.tg
    t_tum = C.w("tumbuhan", 1, -0.3)
    t_tap = C.w("tapi", 1, -0.3)
    t_beg = C.w("begitu", 1, -0.3)
    t_sem = C.w("semakin", 1, -0.3)
    # ---- shot A
    a = C.win(-1, t_tum, 0.01, 0.5)
    if a > 0.01:
        chip(img, CX, 170, "ZONA SENJA  ·  200 - 1.000 m", a * clamp((tl - 3.4) / 0.4), acc=SIAN, fsz=26)
        judul(img, CX, 330, "CAHAYA TINGGAL BIRU REDUP", C.tt("sini", 1, -0.3), fsz=62, hl=("BIRU", "REDUP"),
              hlcol=SIAN, alpha=a)
        q, dy = muncul(C, "langit", 1, -0.4)
        taruh(img, _senja_kartu(), CX, 640 + dy, a * q)
        teks(img, CX, 840 + dy, "SEPERTI LANGIT SESAAT SETELAH MATAHARI TERBENAM", 28, TEKS, a * q, name=FS)
    # ---- shot B: tumbuhan tak bisa hidup
    a = C.win(t_tum, t_tap, 0.5, 0.5)
    if a > 0.01:
        kelp(img, CX - 250, 900, 560, tg, a, col=(80, 175, 105))
        silang_besar(img, CX - 250, 600, 150, C.tt("tidak", 1, -0.1), a)
        for k in range(4):
            x = CX + 150 + k * 80
            D.line_on(img, (x, 170), (x - 60, 170 + 300 * C.u("cahayanya", 0.8, 1, -0.3)), (200, 230, 255), 5, a * 0.5,
                      dash=14)
        teks(img, CX + 280, 560, "CAHAYA TERLALU LEMAH", 38, TEKS, a * C.u("lemah", 0.4, 1, -0.3), name=FB)
        teks(img, CX + 280, 650, "FOTOSINTESIS", 60, EMAS, a * C.u("fotosintesis", 0.4, 1, -0.3), name=FB)
        tt = C.tt("fotosintesis", 1, 0.5)
        if tt > 0:
            wd = lebar("FOTOSINTESIS", 60)
            D.line_on(img, (CX + 280 - wd / 2 - 10, 652), (CX + 280 - wd / 2 - 10 + (wd + 20) * esmooth(clamp(tt / 0.3)), 652),
                      MERAH, 9, a)
    # ---- shot C: penuh kehidupan, bersembunyi dari pemangsa
    a = C.win(t_tap, t_beg, 0.5, 0.5)
    if a > 0.01:
        judul(img, CX, 180, "JUSTRU PENUH KEHIDUPAN", tl - t_tap, fsz=58, hl=("KEHIDUPAN",), hlcol=SIAN, alpha=a)
        sem = C.u("bersembunyi", 1.2, 1, -0.2)
        al = a * (1 - 0.55 * sem)
        q1 = C.u("kehidupan", 0.5, 1, -0.2)
        for k in range(5):
            ikan_lentera(img, CX - 500 + (k % 3) * 90 + 10 * math.sin(tg + k), 440 + k * 80 + (k % 2) * 20, 160, tg + k, al * q1, nyala=1 - sem * 0.6)
        q2 = C.u("udang", 0.5, 1, -0.3)
        for k in range(3):
            udang(img, CX - 40 + k * 120, 540 + k * 70 + 8 * math.sin(tg * 1.3 + k), 170, al * q2, tg=tg + k, flip=k % 2 == 1)
        q3 = C.u("uburubur", 0.5, 1, -0.3)
        ubur(img, CX + 420, 440 + 14 * math.sin(tg * 0.8), 95, tg, al * q3)
        ubur(img, CX + 560, 640 + 14 * math.sin(tg * 0.8 + 1), 70, tg + 1.3, al * q3, col=(120, 200, 255))
        callout(img, (CX - 400, 470), (CX - 400, 330), "IKAN LENTERA", C.tt("lentera", 1, -0.2), acc=SIAN, alpha=a * (1 - sem))
        callout(img, (CX + 60, 610), (CX + 60, 850), "UDANG", C.tt("udang", 1, -0.1), acc=ORANYE, alpha=a * (1 - sem))
        callout(img, (CX + 400, 440), (CX + 250, 330), "UBUR-UBUR", C.tt("uburubur", 1, 0.1), acc=UNGU, alpha=a * (1 - sem))
        chip(img, CX, 900, "BERSEMBUNYI SEPANJANG SIANG", a * sem, acc=SIAN, fsz=26)
        tp = C.tt("pemangsa", 1, -0.8)
        if tp > 0:
            ikan(img, -300 + tp * 700, 330, 360, (70, 90, 120), a * 0.95, tg=tg, perut=(140, 160, 180))
    # ---- shot D: migrasi vertikal harian
    a = C.win(t_beg, t_sem, 0.5, 0.5)
    if a > 0.01:
        x0, x1 = CX - 560, CX + 560
        ysurf, yb0, yb1 = 300, 640, 860
        kaca(img, x0 - 30, 200, x1 + 30, 900, a * 0.7, None, r=24, pekat=0.55)
        gelombang(img, x0, x1, ysurf, 6, 120, tg * 2, (180, 225, 250), 4, a)
        teks(img, x0 + 10, ysurf - 36, "PERMUKAAN", 22, REDUP, a, name=FB, anchor="l")
        D.rrect_on(img, x0, yb0, x1, yb1, 14, (40, 100, 170), a * 0.25)
        teks(img, x0 + 10, yb1 + 26, "ZONA SENJA", 22, SIAN, a, name=FB, anchor="l")
        malam = C.u("malam", 0.8, 1, -0.3) * (1 - C.u("pagi", 0.8, 1, -0.2))
        matahari(img, x1 - 70, 250 + 60 * malam, 34, tg, a * (1 - malam))
        D.dot_on(img, x1 - 70, 250, 34, (230, 234, 250), a * malam)
        D.dot_on(img, x1 - 56, 240, 30, (18, 30, 60), a * malam)
        naik = C.u("naik", 2.0, 1, -0.3, ease=eio) * (1 - C.u("turun", 2.0, 1, -0.2, ease=eio))
        rng = random.Random(21)
        for k in range(140):
            px = rng.uniform(x0 + 30, x1 - 160)
            pyb = rng.uniform(yb0 + 15, yb1 - 15)
            pyt = rng.uniform(ysurf + 30, ysurf + 190)
            y = pyb + (pyt - pyb) * clamp(naik * 1.15 - rng.random() * 0.15)
            D.dot_on(img, px + 5 * math.sin(tg * 2 + k), y, 3.2, (140, 230, 255), a * 0.9 * C.u("miliaran", 0.6, 1, -0.3))
        teks(img, CX - 100, 470, "MILIARAN HEWAN", 40, TEKS, a * C.u("miliaran", 0.5, 1, -0.3) * (1 - C.u("para", 0.4, 1, -0.2)), name=FB)
        panah(img, (x1 - 110, yb0 - 10), (x1 - 110, ysurf + 40), SIAN, 7, a * (1 - C.u("turun", 0.4, 1, -0.2)), C.u("naik", 0.8, 1, -0.2))
        panah(img, (x1 - 60, ysurf + 40), (x1 - 60, yb0 - 10), EMAS, 7, a, C.u("turun", 0.8, 1, -0.2))
        stiker(img, CX, 560, "MIGRASI HEWAN TERBESAR DI BUMI", C.tt("migrasi", 1, -0.3), bg=SIAN, fg=(6, 20, 40), fsz=44,
               tg=tg, alpha=a)
        chip(img, CX, 680, "TERJADI SETIAP MALAM", a * C.u("setiap", 0.4, 1, -0.3), acc=EMAS, fsz=28)
    # ---- shot E: makin dingin, cahaya hilang
    a = C.win(t_sem, C.dur + 1, 0.5, 0.1)
    if a > 0.01:
        v = 28 - 24 * C.u("empat", 1.6, 1, -1.2)
        termometer(img, CX - 330, 520, 380, 0.1 + 0.85 * v / 28, a, col=SIAN)
        angka(img, CX - 50, 520, v, 5, fsz=130, suf="\u00b0C", alpha=a, col=TEKS)
        teks(img, CX - 330, 820, "SUHU DI 1.000 m", 28, REDUP, a, name=FB)
        q, dy = muncul(C, "cahaya", 1, -0.4)
        matahari(img, CX + 330, 470 + dy, 70, tg, a * q * (1 - 0.8 * C.u("hilang", 0.8, 1, -0.2)))
        silang_besar(img, CX + 330, 470, 110, C.tt("hilang", 1, 0.1), a)
        teks(img, CX + 330, 680, "CAHAYA MATAHARI", 34, TEKS, a * q, name=FB)
        teks(img, CX + 330, 740, "HILANG SEPENUHNYA", 34, MERAH, a * C.u("hilang", 0.4, 1, -0.2), name=FB)


# ============================================================ BAB 3 - ZONA TENGAH MALAM
def v02_malam(img, C):
    tl, tg = C.tl, C.tg
    t_tap = C.w("tapi", 1, -0.3)
    t_bio = C.w("namanya", 1, -0.3)
    t_sal = C.w("salah", 1, -0.3)
    t_zon = C.w("zona", 2, -0.3)
    # ---- shot A: gelap total
    a = C.win(-1, t_tap, 0.01, 0.5)
    if a > 0.01:
        chip(img, CX, 170, "ZONA TENGAH MALAM  ·  1.000 - 4.000 m", a * clamp((tl - 3.4) / 0.4), acc=UNGU, fsz=26)
        q = C.u("gelap", 0.8, 1, -0.3)
        teks(img, CX, 470, "G E L A P   T O T A L", 96, TEKS, a * q, name=FB, scale=1.0 + 0.05 * (1 - q))
        teks(img, CX, 590, "SELAMANYA", 48, UNGU, a * C.u("selamanya", 0.5, 1, -0.3), name=FB)
        q2, dy = muncul(C, "sinar", 1, -0.4)
        kaca(img, CX - 330, 700 + dy, CX + 330, 820 + dy, a * q2, UNGU)
        teks(img, CX, 760 + dy, "0% SINAR MATAHARI SAMPAI KE SINI", 30, TEKS, a * q2, name=FB)
    # ---- shot B: kilatan cahaya -> 76% hewan berbioluminesensi
    a = C.win(t_tap, t_bio, 0.5, 0.5)
    if a > 0.01:
        tl_ = C.tt("lihat", 1, -0.3)
        rng = random.Random(33)
        for k in range(34):
            x, y = rng.uniform(360, W - 80), rng.uniform(140, H - 100)
            col = rng.choice([SIAN, (120, 255, 200), (160, 150, 255), (90, 220, 255)])
            ph, sp = rng.random() * 6.28, rng.uniform(1.0, 2.2)
            b = 0.5 + 0.5 * math.sin(tg * sp + ph)
            q = clamp((tl_ - k * 0.03) / 0.3)
            if q > 0 and b > 0.3:
                glow(img, x, y, 40, col, 0.5 * b * q * a)
                D.dot_on(img, x, y, 3.5, mix(col, WHITE, 0.6), b * q * a)
        teks(img, CX, 200, "TAPI TUNGGU DULU... LIHAT ITU!", 44, TEKS, a * C.u("tunggu", 0.4, 1, -0.3) * (1 - C.u("tujuh", 0.4, 1, -0.5)), name=FB)
        q, dy = muncul(C, "tujuh", 1, -0.4)
        if q > 0.01:
            p = 0.76 * eo(clamp(C.tt("tujuh", 1, -0.3) / 1.4))
            D.dot_on(img, CX - 300, 540, 190, (6, 10, 26), a * q * 0.9)
            cincin_persen(img, CX - 300, 540 + dy, 170, p, a * q, col=SIAN, wd=30)
            glow(img, CX - 300, 540, 260, SIAN, 0.18 * a * q)
            teks(img, CX - 300, 540 + dy, "%d%%" % round(p * 100), 96, TEKS, a * q, name=FB)
            teks(img, CX + 260, 450 + dy, "HEWAN LAUT DALAM", 44, TEKS, a * q, name=FB)
            teks(img, CX + 260, 515 + dy, "BISA MEMBUAT", 44, TEKS, a * q, name=FB)
            teks(img, CX + 260, 580 + dy, "CAHAYA SENDIRI", 44, SIAN, a * q, name=FB)
            chip(img, CX + 260, 680, "LEWAT REAKSI KIMIA DI TUBUHNYA", a * C.u("reaksi", 0.4, 1, -0.3), acc=SIAN, fsz=24)
    # ---- shot B2: bioluminesensi untuk apa
    a = C.win(t_bio, t_sal, 0.5, 0.5)
    if a > 0.01:
        judul(img, CX, 220, "BIOLUMINESENSI", tl - t_bio, fsz=86, col=SIAN, alpha=a)
        glow(img, CX, 220, 420, SIAN, 0.12 * a)
        items = [("memancing", "MEMANCING MANGSA"), ("pasangan", "MENCARI PASANGAN"), ("mengecoh", "MENGECOH PEMANGSA")]
        for j, (kw, lab) in enumerate(items):
            q, dy = muncul(C, kw, 1, -0.4)
            if q <= 0.01:
                continue
            x = CX - 440 + j * 440
            kaca(img, x - 190, 380 + dy, x + 190, 800 + dy, a * q, [SIAN, UNGU, HIJAU][j])
            if j == 0:
                pemancing(img, x - 10, 560 + dy, 220, tg, a * q, mulut=0.4)
            elif j == 1:
                ikan_lentera(img, x - 70, 560 + dy, 130, tg, a * q)
                ikan_lentera(img, x + 70, 560 + dy, 130, tg + 1, a * q, flip=True)
                pul = 0.5 + 0.5 * math.sin(tg * 5)
                glow(img, x, 530 + dy, 50, UNGU, 0.6 * pul * a * q)
            else:
                tt = C.tt(kw, 1, 0.1)
                udang(img, x + 60 + 60 * eo(clamp(tt / 0.8)), 560 + dy, 130, a * q, tg=tg)
                if tt > 0:
                    for k in range(12):
                        rr = random.Random(k)
                        u = clamp(tt / 1.2)
                        glow(img, x - 20 - u * 80 * rr.random(), 560 + dy + (rr.random() - 0.5) * 140 * u, 40,
                             (120, 255, 220), 0.5 * a * q * (1 - 0.5 * u))
            teks(img, x, 740 + dy, lab, 28, TEKS, a * q, name=FB)
    # ---- shot C: ikan pemancing
    a = C.win(t_sal, t_zon, 0.5, 0.5)
    if a > 0.01:
        th = C.w("hap", 1, -0.05)
        d_ = tl - th
        mulut = 0.35 if d_ < -0.25 else (0.35 + 0.65 * clamp((d_ + 0.25) / 0.2) if d_ < 0 else max(0.05, 1 - d_ / 0.12))
        q = C.u("salah", 1.0, 1, -0.3)
        ax, ay = CX + 180, 560
        ly = pemancing(img, ax, ay + 10 * math.sin(tg * 0.7), 620, tg, a * q, mulut=mulut,
                       lure=q * (0.5 + 0.5 * C.u("umpan", 0.4, 1, -0.3)))
        chip(img, CX - 420, 880, "IKAN PEMANCING", a * C.u("pemancing", 0.4, 1, -0.3), acc=SIAN, fsz=30)
        callout(img, ly, (ly[0] - 240, ly[1] - 110), "UMPAN BERCAHAYA", C.tt("umpan", 1, -0.2), acc=SIAN, fsz=30,
                sub="DI ATAS KEPALANYA", alpha=a)
        tp = C.tt("penasaran", 1, -0.6)
        if tp > 0 and d_ < 0.02:
            u = eio(clamp(tp / (th - C.w("penasaran", 1, -0.6))))
            fx = CX - 700 + (ax + 150 - (CX - 700)) * u
            ikan(img, fx, 560 + 30 * math.sin(tg * 2) * (1 - u), 110, (240, 190, 90), a, tg=tg)
        if d_ > 0:
            stiker(img, CX - 200, 820, "HAP!", d_, bg=MERAH, fsz=80, tg=tg, alpha=a)
            if d_ < 0.4:
                glow(img, ax + 200, 560, 300, WHITE, 0.4 * (1 - d_ / 0.4) * a)
    # ---- shot D: paus sperma & cumi raksasa
    a = C.win(t_zon, C.dur + 1, 0.5, 0.1)
    if a > 0.01:
        chip(img, CX, 170, "TAMU DARI PERMUKAAN", a * C.u("tamu", 0.4, 1, -0.3), acc=ORANYE, fsz=28)
        tp = C.tt("paus", 1, -0.5)
        if tp > 0:
            u = tp / 14.0
            px, py = CX - 520 + 520 * u, 280 + 260 * u
            paus_sperma(img, px, py, 700, a * clamp(tp / 0.6), tg=tg, rot=-22)
        angka(img, CX + 380, 330, 2000, C.tt("dua", 1, -0.3), fsz=90, pre="> ", suf=" m", alpha=a, col=EMAS,
              sub="DALAMNYA PAUS SPERMA MENYELAM", subfsz=24)
        tj = C.tt("satu", 3, -0.4)
        if tj > 0:
            L.jam(img, CX + 250, 560, 60, tj * 400, a * clamp(tj / 0.4), acc=EMAS)
            teks(img, CX + 340, 560, "> 1 JAM", 56, TEKS, a * clamp(tj / 0.4), name=FB, anchor="l")
            teks(img, CX + 340, 612, "MENAHAN NAPAS", 24, REDUP, a * clamp(tj / 0.4), name=FS, anchor="l")
        tc = C.tt("cumicumi", 1, -0.4)
        if tc > 0:
            qc = eo(clamp(tc / 0.8))
            cumi(img, CX + 180 + 200 * (1 - qc), 840, 480, tg, a * qc, rot=8)
            chip(img, CX - 330, 760, "CUMI-CUMI RAKSASA", a * qc, acc=MERAH, fsz=28)
            garis_ukur(img, CX - 110, CX + 560, 960, "\u00b1 12 METER", C.tt("dua", 2, -0.3), col=TEKS, alpha=a, fsz=30)


# ============================================================ BAB 4 - TITANIC & SALJU LAUT
def v02_titanic(img, C):
    tl, tg = C.tl, C.tg
    t_sed = C.w("sedikit", 1, -0.3)
    t_tek = C.w("tekanan", 1, -0.6)
    t_cob = C.w("coba", 1, -0.3)
    t_sek = C.w("sekeliling", 1, -0.4)
    # ---- shot A: profil dasar laut + garis rata-rata
    a = C.win(-1, t_sed, 0.01, 0.5)
    if a > 0.01:
        x0, x1, ys = CX - 640, CX + 640, 330
        judul(img, CX, 190, "KEDALAMAN RATA-RATA LAUTAN", C.tt("kedalaman", 1, -0.3), fsz=52, hl=("RATA-RATA",), alpha=a)
        q = C.u("terus", 1.4, 1, -0.3)
        prof = [(0, 0.02), (0.1, 0.04), (0.16, 0.25), (0.24, 0.55), (0.4, 0.6), (0.55, 0.58), (0.62, 0.64),
                (0.66, 0.98), (0.7, 0.66), (0.85, 0.58), (1.0, 0.56)]
        hh = 560
        pts = [(x0 + (x1 - x0) * u * q, ys + hh * v) for u, v in prof]
        D.rrect_on(img, x0, ys - 4, x0 + (x1 - x0) * q, ys + 2, 2, (180, 225, 250), a * 0.8)
        D.poly_on(img, [(x0, ys + hh + 40)] + pts + [(pts[-1][0], ys + hh + 40)], (40, 36, 44), a * 0.95)
        M._pline(img, pts, (120, 110, 120), 4, a)
        tr = C.tt("ratarata", 1, -0.4)
        yr = ys + hh * 0.34
        if tr > 0:
            u = esmooth(clamp(tr / 0.7))
            D.line_on(img, (x0, yr), (x0 + (x1 - x0) * u, yr), EMAS, 4, a, dash=20)
            chip(img, x0 + 20, yr - 40, "RATA-RATA  \u00b1 3.700 m", a * clamp((tr - 0.4) / 0.3), acc=EMAS, fsz=26,
                 anchor="l")
        callout(img, (x0 + (x1 - x0) * 0.45, yr), (x0 + (x1 - x0) * 0.45 + 140, yr + 140), "KITA DI SINI",
                C.tt("kita", 1, -0.2), acc=SIAN, alpha=a)
    # ---- shot B: Titanic
    a = C.win(t_sed, t_cob, 0.5, 0.5)
    if a > 0.01:
        dim = 1 - 0.7 * C.u("tekanan", 0.6, 1, -0.6)
        dasar_laut(img, 880, a)
        rev = C.u("terbaring", 2.0, 1, -0.4)
        sw = math.sin(tg * 0.35) * 6
        sorot(img, CX - 600, 120, 38 + sw, 1300, 700, a * 0.8 * rev)
        titanic(img, CX + 40, 900, 1100, a * (0.15 + 0.85 * rev) * dim)
        a2 = a * (1 - C.u("tekanan", 0.5, 1, -0.6))
        tt = C.tt("titanic", 1, -0.3)
        if tt > 0:
            teks(img, CX, 190, "T I T A N I C", 96, TEKS, a2 * clamp(tt / 0.4), name=FB,
                 scale=1 + 0.08 * (1 - eo(clamp(tt / 0.6))))
            chip(img, CX, 290, "DI KEDALAMAN \u00b1 3.800 m", a2 * clamp((tt - 0.3) / 0.3), acc=ORANYE, fsz=26)
        tn = C.tt("tenggelam", 1, -0.3)
        if tn > 0:
            xa, xb, yt = CX - 330, CX + 330, 400
            D.dot_on(img, xa, yt, 12, ORANYE, a2)
            teks(img, xa, yt - 44, "1912", 40, TEKS, a2, name=FB)
            teks(img, xa, yt + 40, "TENGGELAM", 20, REDUP, a2, name=FS)
            u = esmooth(clamp(C.tt("ditemukan", 1, -0.3) / 1.2))
            D.line_on(img, (xa, yt), (xa + (xb - xa) * u, yt), ORANYE, 5, a2)
            if u > 0.98:
                D.dot_on(img, xb, yt, 12, HIJAU, a2)
                teks(img, xb, yt - 44, "1985", 40, TEKS, a2, name=FB)
                teks(img, xb, yt + 40, "DITEMUKAN", 20, REDUP, a2, name=FS)
            angka(img, CX, yt - 40, 73, C.tt("tujuh", 2, -0.3), fsz=44, suf=" TAHUN", alpha=a2, col=EMAS, dur=0.9)
        # ---- tekanan 380x
        tk = C.tt("tiga", 4, -0.4)
        if tk > 0:
            ak = a * clamp((tl - t_tek) / 0.4)
            angka(img, CX, 450, 380, tk, fsz=190, suf="\u00d7", alpha=ak, col=TEKS, dur=1.2,
                  sub="TEKANAN DI PERMUKAAN", subfsz=30)
            panah_tekan(img, CX, 450, 230, tk, ak * 0.8, n=10)
    # ---- shot D: gelas styrofoam menyusut
    a = C.win(t_cob, t_sek, 0.5, 0.5)
    if a > 0.01:
        judul(img, CX, 180, "GELAS STYROFOAM DIBAWA KE SINI", tl - t_cob, fsz=52, hl=("STYROFOAM",), alpha=a)
        q1, dy1 = muncul(C, "gelas", 1, -0.4)
        gelas(img, CX - 300, 560 + dy1, 330, a * q1)
        teks(img, CX - 300, 800, "DI PERMUKAAN", 30, REDUP, a * q1, name=FB)
        q2, dy2 = muncul(C, "dibawa", 1, -0.3)
        sus = C.u("menyusut", 1.4, 1, -0.2, ease=eio)
        h2 = 330 - 210 * sus
        yb = 725
        gelas(img, CX + 300, yb - h2 / 2 + dy2, h2, a * q2, keriput=sus)
        teks(img, CX + 300, 800, "DI 3.800 m", 30, REDUP, a * q2, name=FB)
        tm = C.tt("memeras", 1, -0.3)
        panah_tekan(img, CX + 300, yb - h2 / 2, h2 * 0.45, tm, a * (1 - sus * 0.6), n=8)
        tu = C.tt("udara", 1, -0.2)
        if tu > 0:
            gelembung(img, CX + 300, yb - h2, tu, a * (1 - clamp((tu - 3) / 1)), n=10, tinggi=300, seed=5, r=7)
            chip(img, CX + 300, 300, "UDARA DI BUSA TERPERAS KELUAR", a * clamp(tu / 0.4), acc=SIAN, fsz=24)
        stiker(img, CX + 300, 900, "SEUKURAN GELAS MAINAN!", C.tt("seukuran", 1, -0.2), bg=EMAS, fg=(40, 20, 0), fsz=34,
               tg=tg, alpha=a)
    # ---- shot E: salju laut
    a = C.win(t_sek, C.dur + 1, 0.5, 0.1)
    if a > 0.01:
        salju_tebal(img, tg, a * C.u("butiran", 1.0, 1, -0.4), n=170)
        ab = a * C.u("butiran", 0.5, 1, -0.3) * (1 - C.u("salju", 0.4, 2, -0.5))
        teks(img, CX, 300, "BUTIRAN PUTIH MELAYANG TURUN", 52, TEKS, ab, name=FB)
        teks(img, CX, 380, "SEPERTI HUJAN SALJU...", 52, REDUP, ab * C.u("seperti", 0.4, 1, -0.3), name=FB)
        dasar_laut(img, 900, a)
        judul(img, CX, 330, "SALJU LAUT", C.tt("salju", 2, -0.3), fsz=110, col=WHITE, alpha=a)
        glow(img, CX, 330, 380, (200, 220, 240), 0.1 * a * C.u("salju", 0.5, 2, -0.3))
        tq = C.tt("sisa", 1, -0.3)
        if tq > 0:
            kaca(img, CX - 650, 480, CX - 110, 600, a * clamp(tq / 0.4), REDUP)
            teks(img, CX - 380, 540, "SISA MAKHLUK DARI ATAS", 28, TEKS, a * clamp(tq / 0.4), name=FB)
            panah(img, (CX - 95, 540), (CX + 75, 540), TEKS, 6, a, C.u("menjadi", 0.5, 1, -0.3))
        tm = C.tt("makanan", 1, -0.3)
        if tm > 0:
            kaca(img, CX + 90, 480, CX + 700, 600, a * clamp(tm / 0.4), HIJAU)
            teks(img, CX + 400, 540, "MAKANAN PENGHUNI LAUT DALAM", 26, TEKS, a * clamp(tm / 0.4), name=FB)
            for k in range(4):
                amfipoda(img, CX + 180 + k * 120, 880 - (k % 2) * 8, 70, tg + k, a * clamp((tm - k * 0.15) / 0.4), flip=k % 2 == 0)


def teks_pangkat(img, cx, cy, base, sup, fsz, col, alpha):
    wb, ws = lebar(base, fsz), lebar(sup, fsz * 0.55)
    x = cx - (wb + ws + 4) / 2
    teks(img, x, cy, base, fsz, col, alpha, anchor="l")
    teks(img, x + wb + 4, cy - fsz * 0.42, sup, int(fsz * 0.55), col, alpha, anchor="l")


def bendera_id(img, x, y, w, alpha):
    D.rrect_on(img, x, y, x + w, y + w * 0.34, 3, (225, 40, 50), alpha)
    D.rrect_on(img, x, y + w * 0.33, x + w, y + w * 0.67, 3, (245, 245, 245), alpha)


def bakteri(img, cx, cy, s, tg, alpha):
    rng = random.Random(4)
    for k in range(9):
        x = cx + rng.uniform(-60, 60) * s
        y = cy + rng.uniform(-40, 40) * s
        an = rng.uniform(0, 3.14) + 0.2 * math.sin(tg + k)
        dx, dy = math.cos(an) * 18 * s, math.sin(an) * 18 * s
        D.line_on(img, (x - dx, y - dy), (x + dx, y + dy), (120, 220, 140), max(4, int(14 * s)), alpha)


def bulan_es(img, cx, cy, r, alpha):
    D.dot_on(img, cx, cy, r, (214, 226, 238), alpha)
    rng = random.Random(9)
    for k in range(7):
        a0 = rng.uniform(0, 6.28)
        pts = [(cx + r * 0.9 * math.cos(a0), cy + r * 0.9 * math.sin(a0))]
        for q in range(4):
            a0 += rng.uniform(-0.6, 0.6)
            pts.append((pts[-1][0] - math.cos(a0) * r * 0.35, pts[-1][1] - math.sin(a0) * r * 0.35))
        M._pline(img, pts, (190, 120, 90), 3, alpha * 0.8)
    glow(img, cx, cy, r * 1.6, (200, 220, 255), 0.18 * alpha)


def rec_bingkai(img, x0, y0, x1, y1, tg, alpha):
    ln = 60
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        D.line_on(img, (x, y), (x + sx * ln, y), WHITE, 5, alpha)
        D.line_on(img, (x, y), (x, y + sy * ln), WHITE, 5, alpha)
    if (tg * 1.5) % 1 < 0.6:
        D.dot_on(img, x0 + 40, y0 + 44, 11, MERAH, alpha)
    teks(img, x0 + 62, y0 + 44, "REC", 26, WHITE, alpha, anchor="l")
    teks(img, x1 - 30, y0 + 44, "8.336 m", 24, WHITE, alpha, name=FS, anchor="r")


def mata_gelap(img, cx, cy, s, tg, alpha, col=(150, 255, 200), ph=0.0):
    kedip = 1.0 if (tg * 0.5 + ph) % 1 > 0.06 else 0.1
    for dx in (-18, 18):
        glow(img, cx + dx * s, cy, 26 * s, col, 0.5 * alpha)
        D.dot_on(img, cx + dx * s, cy, 7 * s, mix(col, WHITE, 0.5), alpha * kedip)


# ============================================================ BAB 5 - VENTILASI HIDROTERMAL
def v02_ventilasi(img, C):
    tl, tg = C.tl, C.tg
    t_tap = C.w("tapi", 1, -0.3)
    t_mgj = C.w("mengejutkan", 1, -0.3)
    t_mer = C.w("mereka", 1, -0.3)
    # ---- shot A: dataran abisal
    a = C.win(-1, t_tap, 0.01, 0.5)
    if a > 0.01:
        chip(img, CX, 170, "ZONA ABISAL  ·  4.000 - 6.000 m", a * clamp((tl - 3.4) / 0.4), acc=ORANYE, fsz=26)
        dasar_laut(img, 780, a, batu=False, seed=6)
        garis_ukur(img, 420, W - 80, 720, "LUAS DAN DATAR", C.tt("luas", 1, -0.3), col=TEKS, alpha=a * (1 - C.u("lumpur", 0.4, 1, -0.4)), fsz=32)
        tlm = C.tt("lumpur", 1, -0.4)
        if tlm > 0:
            bx0, bx1, by1 = CX - 60, CX + 520, 700
            kaca(img, bx0 - 30, 300, bx1 + 30, by1 + 40, a * clamp(tlm / 0.4), ORANYE)
            for k in range(8):
                q = clamp((tlm - k * 0.35) / 0.35)
                if q <= 0:
                    continue
                y = by1 - k * 42
                col = mix((110, 90, 70), (170, 150, 120), k / 8)
                D.rrect_on(img, bx0, y - 40 * eo(q), bx1, y, 4, col, a)
            teks(img, (bx0 + bx1) / 2, 340, "LUMPUR HALUS", 34, TEKS, a * clamp(tlm / 0.4), name=FB)
            chip(img, (bx0 + bx1) / 2, by1 + 90, "TERKUMPUL SELAMA JUTAAN TAHUN", a * C.u("jutaan", 0.4, 1, -0.3), acc=EMAS, fsz=24)
        ts = C.tt("suhunya", 1, -0.3)
        if ts > 0:
            v = 28 - 26 * eo(clamp(ts / 1.2))
            termometer(img, CX - 360, 470, 300, 0.1 + 0.8 * v / 28, a * clamp(ts / 0.4), col=SIAN)
            angka(img, CX - 360, 700, v, 5, fsz=70, suf="\u00b0C", alpha=a * clamp(ts / 0.4))
            chip(img, CX - 360, 790, "HAMPIR MEMBEKU", a * C.u("membeku", 0.4, 1, -0.3), acc=SIAN, fsz=24)
    # ---- latar ventilasi (shot B + C)
    a = C.win(t_tap, t_mer, 0.5, 0.5)
    if a > 0.01:
        vx, vb = CX - 120, 900
        glow(img, vx, 520, 520, (255, 120, 50), 0.12 * a * C.u("menyembur", 0.6, 1, -0.3))
        dasar_laut(img, 880, a, seed=8)
        q = C.u("kejutan", 0.8, 1, -0.4)
        cerobong(img, vx, vb + 10, 470 * (0.4 + 0.6 * eo(q)), tg, a * q, asap=C.u("menyembur", 0.8, 1, -0.3))
        callout(img, (vx - 30, 880), (vx - 330, 820), "RETAKAN DASAR LAUT", C.tt("retakan", 1, -0.2), acc=ORANYE,
                alpha=a * (1 - C.u("mengejutkan", 0.4, 1, -0.3)))
        ab = a * (1 - C.u("mengejutkan", 0.4, 1, -0.3))
        callout(img, (vx + 60, 300), (vx + 300, 230), "AIR PANAS HITAM", C.tt("hitam", 1, -0.3), acc=MERAH, alpha=ab)
        te = C.tt("empat", 2, -0.4)
        if te > 0:
            v = 2 + 398 * eo(clamp(te / 1.4))
            termometer(img, CX + 250, 500, 340, 0.05 + 0.9 * v / 400, ab * clamp(te / 0.3), col=MERAH)
            angka(img, CX + 470, 470, v, 5, fsz=96, pre="> " if v > 399 else "", suf="\u00b0C", alpha=ab * clamp(te / 0.3), col=TEKS)
        stiker(img, CX + 450, 640, "TAPI TIDAK MENDIDIH!", C.tt("mendidih", 1, -0.2), bg=MERAH, fsz=34, tg=tg, alpha=ab)
        tk = C.tt("tekanan", 1, -0.3)
        if tk > 0:
            for k in range(5):
                x = CX + 330 + k * 70
                panah(img, (x, 740), (x, 820), SIAN, 6, ab, esmooth(clamp((tk - k * 0.06) / 0.4)))
            teks(img, CX + 470, 860, "TEKANAN SANGAT BESAR", 26, SIAN, ab * clamp(tk / 0.4), name=FB)
        chip(img, CX, 170, "VENTILASI HIDROTERMAL", a * C.u("ventilasi", 0.4, 1, -0.3), acc=MERAH, fsz=32)
        # ---- kehidupan di sekitar
        tc = C.tt("cacing", 1, -0.3)
        if tc > 0:
            cacing_tabung(img, vx - 230, 890, 170, tg, a * clamp(tc / 0.5), seed=1)
            cacing_tabung(img, vx + 200, 895, 130, tg + 1, a * clamp(tc / 0.5), seed=2)
            callout(img, (vx - 230, 730), (vx - 300, 640), "CACING TABUNG", tc, acc=MERAH, alpha=a)
        tkp = C.tt("kepiting", 1, -0.3)
        if tkp > 0:
            for k in range(3):
                kepiting(img, vx + 340 + k * 110 + 10 * math.sin(tg + k), 870 - (k % 2) * 10, 90, tg + k, a * clamp((tkp - k * 0.1) / 0.4))
            callout(img, (vx + 450, 850), (vx + 600, 700), "KEPITING", tkp, acc=EMAS, alpha=a)
        tu = C.tt("udang", 1, -0.3)
        if tu > 0:
            for k in range(7):
                rr = random.Random(k + 5)
                udang(img, vx + rr.uniform(-160, 160) + 12 * math.sin(tg + k), 600 + rr.uniform(-60, 200), 70,
                      a * clamp((tu - k * 0.06) / 0.4), tg=tg + k, flip=k % 2 == 0, col=(236, 220, 210))
            callout(img, (vx + 120, 620), (vx + 400, 520), "UDANG", tu, acc=SIAN, alpha=a)
        tn = C.tt("tanpa", 1, -0.3)
        if tn > 0:
            matahari(img, CX + 560, 320, 40, tg, a * clamp(tn / 0.4) * 0.8)
            silang_besar(img, CX + 560, 320, 70, tn - 0.2, a, wd=10)
            teks(img, CX + 560, 430, "TANPA SINAR MATAHARI", 28, TEKS, a * clamp(tn / 0.4), name=FB)
    # ---- shot D: rantai makanan dari zat kimia
    a = C.win(t_mer, C.dur + 1, 0.5, 0.1)
    if a > 0.01:
        judul(img, CX, 190, "MAKANAN DARI PERUT BUMI", C.tt("bergantung", 1, -0.3), fsz=54, hl=("PERUT", "BUMI"), alpha=a)
        nodes = [("zat", "ZAT KIMIA", "DARI PERUT BUMI", ORANYE), ("bakteri", "BAKTERI", "MENGUBAHNYA", HIJAU),
                 ("makanan", "MAKANAN", "BAGI SEMUA PENGHUNI", SIAN)]
        a2 = a * (1 - C.u("penemuan", 0.5, 1, -0.3) * 0.75)
        for j, (kw, t1, t2, col) in enumerate(nodes):
            q, dy = muncul(C, kw, 1, -0.4)
            if q <= 0.01:
                continue
            x = CX - 440 + j * 440
            kaca(img, x - 170, 330 + dy, x + 170, 690 + dy, a2 * q, col)
            if j == 0:
                L.bumi(img, x, 470 + dy, 80, a2 * q)
            elif j == 1:
                bakteri(img, x, 470 + dy, 1.2, tg, a2 * q)
            else:
                cacing_tabung(img, x - 40, 530 + dy, 110, tg, a2 * q)
                kepiting(img, x + 60, 515 + dy, 70, tg, a2 * q)
            teks(img, x, 600 + dy, t1, 34, col, a2 * q, name=FB)
            teks(img, x, 645 + dy, t2, 20, TEKS, a2 * q, name=FS)
            if j:
                panah(img, (x - 262, 510), (x - 185, 510), TEKS, 6, a2, q)
        tp = C.tt("penemuan", 1, -0.3)
        if tp > 0:
            ap = a * clamp(tp / 0.5)
            teks(img, CX, 790, "MENGUBAH CARA ILMUWAN MEMANDANG KEHIDUPAN", 34, TEKS, ap, name=FB)
            tq = C.tt("planet", 1, -0.4)
            if tq > 0:
                bulan_es(img, CX + 520, 880, 60, a * clamp(tq / 0.4))
                stiker(img, CX - 60, 880, "BAHKAN DI PLANET LAIN?", tq, bg=UNGU, fsz=38, tg=tg, alpha=a)


# ============================================================ BAB 6 - ZONA HADAL
def v02_hadal(img, C):
    tl, tg = C.tl, C.tg
    t_zn2 = C.w("zona", 2, -0.3)
    t_ind = C.w("indonesia", 1, -0.3)
    t_bah = C.w("bahkan", 1, -0.3)
    t_par = C.w("para", 1, -0.3)
    # dinding palung di sisi (suasana)
    wa = clamp((tl - 3.2) / 0.8) * 0.9
    for s_ in (-1, 1):
        x0 = W if s_ > 0 else 330
        pts = [(x0, -20), (x0 - s_ * 170, 250), (x0 - s_ * 110, 520), (x0 - s_ * 230, 800), (x0 - s_ * 150, H + 20),
               (x0 + s_ * 40, H + 20), (x0 + s_ * 40, -20)]
        D.poly_on(img, pts, (8, 14, 22), wa)
    # ---- shot A: zona hadal & Hades
    a = C.win(-1, t_zn2, 0.01, 0.5)
    if a > 0.01:
        teks(img, CX, 380, "Z O N A   H A D A L", 104, HIJAU, a * clamp((tl - 3.4) / 0.5), name=FB,
             scale=1 + 0.06 * (1 - eo(clamp((tl - 3.4) / 0.8))))
        glow(img, CX, 380, 460, HIJAU, 0.12 * a * clamp((tl - 3.4) / 0.5))
        chip(img, CX, 500, "6.000 - 10.935 m", a * clamp((tl - 3.8) / 0.4), acc=HIJAU, fsz=28)
        th = C.tt("hades", 1, -0.3)
        if th > 0:
            kaca(img, CX - 360, 610, CX + 360, 820, a * clamp(th / 0.4), HIJAU)
            teks(img, CX, 675, "H A D E S", 60, TEKS, a * clamp(th / 0.4), name=FB)
            teks(img, CX, 750, "DEWA DUNIA BAWAH  ·  MITOLOGI YUNANI", 26, REDUP, a * C.u("dewa", 0.4, 1, -0.3), name=FS)
    # ---- shot B: lempeng menunjam membentuk palung
    a = C.win(t_zn2, t_ind, 0.5, 0.5)
    if a > 0.01:
        judul(img, CX, 170, "HANYA ADA DI PALUNG", tl - t_zn2, fsz=54, hl=("PALUNG",), hlcol=HIJAU, alpha=a)
        x0, x1 = CX - 620, CX + 620
        q = C.u("palung", 0.8, 1, -0.4)
        kanan = [(CX + 20, 470), (CX + 200, 430), (x1, 420), (x1, 640), (CX + 330, 640), (CX + 140, 560)]
        kiri = [(x0, 480), (CX - 180, 480), (CX - 20, 560), (CX + 200, 700), (CX + 420, 900), (CX + 300, 960),
                (CX + 80, 790), (CX - 120, 640), (x0, 620)]
        D.poly_on(img, kiri, (96, 70, 58), a * q)
        for k in range(6):
            u = ((tg * 0.08) + k / 6) % 1.0
            px = x0 + 40 + (CX - 220 - x0) * u
            D.line_on(img, (px, 495), (px, 605), (120, 90, 74), 6, a * q * 0.8)
        D.poly_on(img, kanan, (120, 110, 96), a * q)
        D.poly_on(img, [(x0, 480), (CX - 180, 480), (CX - 20, 560), (CX - 20, 568), (CX - 180, 490), (x0, 490)],
                  (140, 110, 90), a * q)
        callout(img, (CX - 420, 550), (CX - 470, 760), "LEMPENG BUMI", C.tt("lempeng", 1, -0.2), acc=ORANYE, alpha=a)
        callout(img, (CX + 420, 520), (CX + 470, 760), "LEMPENG LAINNYA", C.tt("lempeng", 2, -0.2), acc=EMAS, alpha=a)
        tm = C.tt("menunjam", 1, -0.3)
        panah(img, (CX - 420, 460), (CX - 140, 460), WHITE, 7, a, esmooth(clamp(tm / 0.5)))
        panah(img, (CX + 20, 620), (CX + 260, 840), WHITE, 7, a, esmooth(clamp((tm - 0.3) / 0.6)))
        teks(img, CX + 240, 690, "MENUNJAM", 30, WHITE, a * clamp((tm - 0.4) / 0.3), name=FB, anchor="l")
        tp = C.tt("jurang", 1, -0.3)
        if tp > 0:
            D.ring_on(img, CX, 540, 50 + 10 * math.sin(tg * 4), HIJAU, 5, a * clamp(tp / 0.3))
            callout(img, (CX, 500), (CX + 140, 330), "PALUNG", tp, acc=HIJAU, fsz=36, sub="JURANG SEMPIT & DALAM", alpha=a)
    # ---- shot C: Palung Weber, Indonesia
    a = C.win(t_ind, t_bah, 0.5, 0.5)
    if a > 0.01:
        q, dy = muncul(C, "indonesia", 1, -0.3)
        bendera_id(img, CX - 560, 250 + dy, 120, a * q)
        teks(img, CX - 420, 270 + dy, "INDONESIA JUGA PUNYA", 44, TEKS, a * q, name=FB, anchor="l")
        tw_ = C.tt("weber", 1, -0.4)
        if tw_ > 0:
            aw = a * clamp(tw_ / 0.4)
            teks(img, CX - 560, 400, "PALUNG WEBER", 76, EMAS, aw, name=FB, anchor="l")
            chip(img, CX - 560, 490, "LAUT BANDA, MALUKU", a * C.u("banda", 0.4, 1, -0.3), acc=EMAS, fsz=28, anchor="l")
            chip(img, CX - 560, 560, "TERDALAM DI INDONESIA", a * C.u("banda", 0.4, 1, 0.3), acc=HIJAU, fsz=24, anchor="l")
        td = C.tt("dalamnya", 1, -0.4)
        if td > 0:
            bx, by0, by1 = CX + 330, 300, 900
            u = eio(clamp(td / 2.6))
            D.rrect_on(img, bx - 60, by0, bx + 60, by1, 20, (255, 255, 255), a * 0.07)
            D.rrect_on(img, bx - 60, by0, bx + 60, by0 + (by1 - by0) * 7200 / 10935 * u + 2, 20, EMAS, a * 0.9)
            teks(img, bx, by0 - 30, "PERMUKAAN", 22, REDUP, a, name=FB)
            D.line_on(img, (bx - 90, by1), (bx + 90, by1), MERAH, 3, a * 0.8, dash=12)
            teks(img, bx + 100, by1, "MARIANA 10.935 m", 22, MERAH, a * 0.9, name=FS, anchor="l")
            angka(img, bx + 100 + 110, by0 + (by1 - by0) * 7200 / 10935 * u, 7200, C.tt("tujuh", 1, -0.4), fsz=54, pre="> ",
                  suf=" m", alpha=a, col=TEKS)
    # ---- shot D: ikan siput 8.336 m
    a = C.win(t_bah, t_par, 0.5, 0.5)
    if a > 0.01:
        t_rek = C.w("merekam", 1, -0.3)
        t_tub = C.w("tubuhnya", 1, -0.3)
        a1 = a * (1 - clamp((tl - t_rek) / 0.4))
        teks(img, CX, 300, "BAHKAN DI KEDALAMAN INI...", 50, REDUP, a1 * C.u("bahkan", 0.5, 1, -0.3), name=FB)
        teks(img, CX, 430, "MASIH ADA IKAN?!", 90, TEKS, a1 * C.u("ikan", 0.5, 1, -0.3), name=FB)
        chip(img, CX, 560, "TAHUN 2023", a1 * C.u("tahun", 0.4, 1, -0.2), acc=HIJAU, fsz=34)
        a2 = a * clamp((tl - t_rek) / 0.5)
        if a2 > 0.01:
            fx, fy = CX + 20 + 30 * math.sin(tg * 0.4), 600 + 16 * math.sin(tg * 0.7)
            sorot(img, CX - 700, 300, 14, 1300, 600, a2 * 0.5)
            ikan_siput(img, fx, fy, 620, tg, a2)
            rec_bingkai(img, CX - 560, 250, CX + 560, 900, tg, a2 * (1 - clamp((tl - t_tub) / 0.5)) * 0.9)
            angka(img, CX, 330, 8336, C.tt("delapan", 1, -0.3), fsz=110, suf=" m", alpha=a2 * (1 - clamp((tl - t_tub) / 0.5)),
                  col=HIJAU, dur=1.4)
            stiker(img, CX, 820, "IKAN TERDALAM YANG PERNAH TEREKAM KAMERA", C.tt("terdalam", 2, -0.3), bg=HIJAU,
                   fg=(6, 30, 16), fsz=34, tg=tg, alpha=a2 * (1 - clamp((tl - t_tub) / 0.4)))
            callout(img, (fx + 120, fy - 10), (fx + 300, fy - 220), "LEMBEK", C.tt("lembek", 1, -0.2), acc=HIJAU, fsz=34, alpha=a2)
            callout(img, (fx - 60, fy - 20), (fx - 300, fy - 220), "PUCAT", C.tt("pucat", 1, -0.1), acc=HIJAU, fsz=34, alpha=a2)
            callout(img, (fx - 180, fy + 20), (fx - 330, fy + 230), "TANPA SISIK KERAS", C.tt("sisik", 1, -0.3), acc=HIJAU, fsz=34, alpha=a2)
    # ---- shot E: batas hidup ikan
    a = C.win(t_par, C.dur + 1, 0.5, 0.1)
    if a > 0.01:
        y = 540
        q = C.u("menduga", 0.8, 1, -0.4)
        D.line_on(img, (CX - 620, y), (CX - 620 + 1240 * q, y), MERAH, 5, a, dash=26)
        chip(img, CX, y - 60, "BATAS HIDUP IKAN  \u00b1 8.200 - 8.400 m", a * clamp((C.tt("menduga", 1, -0.4) - 0.5) / 0.4), acc=MERAH, fsz=28)
        for k in range(3):
            ikan_siput(img, CX - 400 + k * 330 + 30 * math.sin(tg * 0.5 + k), 330 + (k % 2) * 60, 220, tg + k, a * q, flip=k == 1)
        tt = C.tt("tidak", 1, -0.3)
        if tt > 0:
            ikan_siput(img, CX, 760, 260, tg, a * 0.35 * clamp(tt / 0.4))
            silang_besar(img, CX, 760, 110, tt - 0.2, a)
            teks(img, CX, 930, "DI BAWAHNYA, IKAN DIDUGA TAK BISA HIDUP", 32, TEKS, a * clamp(tt / 0.5), name=FB)


# ============================================================ BAB 7 - TITIK TERDALAM
def v02_terdalam(img, C):
    tl, tg = C.tl, C.tg
    t_seb = C.w("seberapa", 1, -0.3)
    t_tek = C.w("tekanannya", 1, -0.3)
    t_air = C.w("airnya", 1, -0.3)
    t_tap = C.w("tapi", 1, -0.3)
    # ---- shot A: tiba di Challenger Deep
    a = C.win(-1, t_seb, 0.01, 0.5)
    if a > 0.01:
        dasar_laut(img, 900, a, seed=11)
        tm = tl - C.w("meter", 1, 0.0)
        pop = 1 + 0.1 * math.exp(-max(0, tm) * 6) * (tm > 0)
        ang = clamp((tl - 3.2) / 0.4)
        d = getattr(C, "d", dalam(C))
        teks(img, CX, 400, fmt_id(d) + " m", 170, WHITE if tm < 0 else EMAS, a * ang, name=FB, scale=pop)
        if 0 < tm < 0.6:
            glow(img, CX, 400, 600, EMAS, 0.35 * (1 - tm / 0.6) * a)
        tc = C.tt("challenger", 1, -0.3)
        if tc > 0:
            teks(img, CX, 580, "C H A L L E N G E R   D E E P", 56, TEKS, a * clamp(tc / 0.4), name=FB)
        chip(img, CX - 190, 680, "PALUNG MARIANA", a * C.u("mariana", 0.4, 1, -0.4), acc=SIAN, fsz=28)
        stiker(img, CX + 210, 690, "TITIK TERDALAM DI BUMI", C.tt("titik", 1, -0.2), bg=EMAS, fg=(40, 20, 0), fsz=34, tg=tg, alpha=a)
    # ---- shot B: Everest ditaruh di palung
    a = C.win(t_seb, t_tek, 0.5, 0.5)
    if a > 0.01:
        ys, yf = 230, 940
        px = (yf - ys) / 10935.0
        teks(img, CX, 150, "SEBERAPA DALAM ITU?", 50, TEKS, a * clamp((tl - t_seb) / 0.4), name=FB)
        gelombang(img, 360, W - 60, ys, 6, 140, tg * 2, (180, 225, 250), 4, a)
        teks(img, 380, ys - 30, "PERMUKAAN  0 m", 22, REDUP, a, name=FB, anchor="l")
        D.poly_on(img, [(340, yf), (CX - 520, yf), (CX - 360, ys + 140), (340, ys + 120)], (30, 30, 40), a * 0.9)
        D.poly_on(img, [(W, yf), (CX + 520, yf), (CX + 380, ys + 160), (W, ys + 110)], (30, 30, 40), a * 0.9)
        D.rrect_on(img, 340, yf, W, H + 10, 0, (34, 32, 40), a)
        teks(img, 380, yf + 40, "DASAR  10.935 m", 24, MERAH, a, name=FB, anchor="l")
        te = C.tt("everest", 1, -0.3)
        if te > 0:
            q = eo(clamp(te / 1.2))
            hh = 8849 * px
            everest(img, CX, yf + 120 * (1 - q), hh, a * clamp(te / 0.4))
            teks(img, CX + 220, yf - hh + 40, "EVEREST 8.849 m", 30, TEKS, a * clamp((te - 0.6) / 0.4), name=FB, anchor="l")
            tp = C.tt("puncaknya", 1, -0.3)
            if tp > 0:
                yp = yf - hh
                D.line_on(img, (CX - 180, yp), (CX - 180, yp - (yp - ys) * esmooth(clamp(tp / 0.8))), SIAN, 4, a, dash=10)
                D.line_on(img, (CX - 200, ys), (CX - 160, ys), SIAN, 4, a * clamp(tp / 0.8))
                D.line_on(img, (CX - 200, yp), (CX - 160, yp), SIAN, 4, a)
                angka(img, CX - 360, (ys + yp) / 2, 2, C.tt("dua", 1, -0.3), fsz=56, pre="> ", suf=" KM", alpha=a, col=SIAN, dur=0.6)
                teks(img, CX - 360, (ys + yp) / 2 + 50, "AIR DI ATAS PUNCAK", 20, REDUP, a * C.u("dua", 0.4, 1, 0.0), name=FS)
    # ---- shot C: tekanan > 1000x = mobil di ujung jari
    a = C.win(t_tek, t_air, 0.5, 0.5)
    if a > 0.01:
        ta = C.w("artinya", 1, -0.3)
        a1 = a * (1 - clamp((tl - ta) / 0.4))
        angka(img, CX, 450, 1000, C.tt("seribu", 1, -0.4), fsz=190, pre="> ", suf="\u00d7", alpha=a1, dur=1.2,
              sub="TEKANAN DI PERMUKAAN", subfsz=32)
        panah_tekan(img, CX, 450, 330, C.tt("seribu", 1, 0.2), a1 * 0.7, n=10)
        a2 = a * clamp((tl - ta) / 0.4)
        if a2 > 0.01:
            fx, fy = CX - 60, 600
            jari(img, fx, fy, a2)
            tsq = C.tt("sentimeter", 1, -0.3)
            if tsq > 0:
                D.rrect_on(img, fx - 26, fy + 4, fx + 26, fy + 56, 4, SIAN, a2 * clamp(tsq / 0.3) * 0.5, outline=SIAN, width=3)
                teks_pangkat(img, fx - 200, fy + 30, "1 cm", "2", 40, SIAN, a2 * clamp(tsq / 0.3))
                D.line_on(img, (fx - 130, fy + 30), (fx - 30, fy + 30), SIAN, 3, a2 * clamp(tsq / 0.3))
            angka(img, CX + 380, 440, 1, C.tt("satu", 1, -0.3), fsz=130, suf=" TON", alpha=a2, col=EMAS, dur=0.4,
                  sub="MENEKAN SETIAP CM PERSEGI", subfsz=26)
            tmb = C.tt("mobil", 1, -0.4)
            if tmb > 0:
                u = clamp(tmb / 0.6)
                ymb = -150 + (fy - 44 - (-150)) * (u * u)
                bounce = 10 * math.sin(clamp((tmb - 0.6) / 0.5) * math.pi) * math.exp(-max(0, tmb - 0.6) * 4) if tmb > 0.6 else 0
                mobil(img, fx, ymb + bounce, 300, a2, rot=0)
                if 0.6 < tmb < 1.0:
                    partikel(img, fx, fy, tmb - 0.6, EMAS, a2, n=12, jarak=160)
                stiker(img, CX + 380, 760, "SEPERTI MOBIL DI UJUNG JARI!", tmb - 0.8, bg=MERAH, fsz=34, tg=tg, alpha=a2)
    # ---- shot D: dingin & gelap
    a = C.win(t_air, t_tap, 0.5, 0.5)
    if a > 0.01:
        termometer(img, CX - 360, 520, 360, 0.18, a, col=SIAN)
        teks(img, CX - 190, 470, "1 - 4\u00b0C", 90, TEKS, a * C.u("dingin", 0.4, 1, -0.3), name=FB, anchor="l")
        teks(img, CX - 190, 560, "AIR DINGIN", 30, REDUP, a * C.u("dingin", 0.4, 1, -0.3), name=FB, anchor="l")
        tg_ = C.tt("gelapnya", 1, -0.3)
        if tg_ > 0:
            teks(img, CX + 80, 720, "G E L A P   T O T A L", 70, TEKS, a * clamp(tg_ / 0.5), name=FB)
    # ---- shot E: amfipoda
    a = C.win(t_tap, C.dur + 1, 0.5, 0.1)
    if a > 0.01:
        dasar_laut(img, 860, a, seed=12, terang=0.6)
        sorot(img, CX - 700, 160, 30, 1400, 760, a * 0.7)
        teks(img, CX, 220, "TAPI DASAR PALUNG INI...", 50, TEKS, a * clamp((tl - t_tap) / 0.4) * (1 - C.u("makhluk", 0.4, 1, -0.3)), name=FB)
        stiker(img, CX, 320, "TIDAK KOSONG!", C.tt("kosong", 1, -0.2), bg=HIJAU, fg=(6, 30, 16), fsz=56, tg=tg,
               alpha=a * (1 - C.u("amfipoda", 0.4, 1, 0.4)))
        tm = C.tt("makhluk", 1, -0.3)
        if tm > 0:
            for k in range(6):
                rr = random.Random(k + 70)
                x = CX - 450 + k * 180 + ((tg * 20 * (1 if k % 2 else -1)) % 60)
                amfipoda(img, x, 850 - rr.uniform(0, 30), rr.uniform(110, 170), tg + k, a * clamp((tm - k * 0.1) / 0.4), flip=k % 2 == 1)
            amfipoda(img, CX + 60, 600 + 10 * math.sin(tg), 340, tg, a * clamp(tm / 0.5))
            callout(img, (CX + 120, 590), (CX + 260, 420), "AMFIPODA", C.tt("amfipoda", 1, -0.3), acc=HIJAU, fsz=40,
                    sub="MIRIP UDANG, BERKEMBANG BIAK DI SINI", alpha=a)
            chip(img, CX, 950, "TUBUHNYA TAHAN TEKANAN LUAR BIASA", a * C.u("menyesuaikan", 0.4, 1, -0.3), acc=HIJAU, fsz=28)


# ============================================================ BAB 8 - MANUSIA DI DASAR PALUNG
def v02_manusia(img, C):
    tl, tg = C.tl, C.tg
    t_prj = C.w("perjalanan", 1, -0.3)
    t_lm2 = C.w("lima", 2, -0.3)
    t_tap = C.w("tapi", 1, -0.3)
    # ---- shot A: Trieste 1960
    a = C.win(-1, t_prj, 0.01, 0.5)
    if a > 0.01:
        dasar_laut(img, 900, a, seed=14)
        a0 = a * clamp((tl - 3.3) / 0.4) * (1 - C.u("tahun", 0.4, 1, -0.3))
        teks(img, CX, 420, "PERNAHKAH MANUSIA", 70, TEKS, a0, name=FB)
        teks(img, CX, 510, "SAMPAI KE SINI?", 70, EMAS, a0, name=FB)
        stempel(img, CX, 700, "PERNAH!", C.tt("pernah", 1, -0.2), col=HIJAU, fsz=80, alpha=a * (1 - C.u("tahun", 0.4, 1, -0.3)))
        tt = C.tt("tahun", 1, -0.3)
        if tt > 0:
            u = eo(clamp(tt / 2.5))
            trieste(img, CX + 150, -150 + 700 * u, 560, a, tg)
            sorot(img, CX + 160, -150 + 700 * u + 120, 100, 380, 260, a * 0.5 * u)
            chip(img, CX - 420, 250, "TAHUN 1960", a * C.u("seribu", 0.4, 1, -0.2), acc=EMAS, fsz=36)
            tj = C.tt("jacques", 1, -0.3)
            if tj > 0:
                kaca(img, CX - 640, 340, CX - 200, 460, a * clamp(tj / 0.4), SIAN)
                teks(img, CX - 420, 380, "JACQUES PICCARD", 32, TEKS, a * clamp(tj / 0.4), name=FB)
                teks(img, CX - 420, 425, "& DON WALSH", 32, TEKS, a * C.u("don", 0.4, 1, -0.2), name=FB)
            callout(img, (CX + 150, -150 + 700 * u), (CX + 480, 200), "TRIESTE", C.tt("trieste", 1, -0.3), acc=EMAS, fsz=34,
                    alpha=a)
    # ---- shot B: 5 jam turun, jendela retak, 20 menit
    a = C.win(t_prj, t_lm2, 0.5, 0.5)
    if a > 0.01:
        x0, x1, y = CX - 580, CX + 520, 330
        pxm = (x1 - x0 - 80) / 300.0
        teks(img, x0, y - 70, "PERJALANAN TURUN", 30, REDUP, a, name=FB, anchor="l")
        D.rrect_on(img, x0, y - 22, x0 + 300 * pxm, y + 22, 22, (255, 255, 255), a * 0.08)
        u = eio(clamp(C.tt("memakan", 1, -0.3) / 1.6))
        D.rrect_on(img, x0, y - 22, x0 + max(44, 300 * pxm * u), y + 22, 22, ORANYE, a)
        angka(img, x0 + 150 * pxm, y + 80, 5, C.tt("lima", 1, -0.3), fsz=56, pre="\u00b1 ", suf=" JAM", alpha=a, col=ORANYE, dur=0.5)
        tdm = C.tt("dua", 1, -0.3)
        if tdm > 0:
            xb = x0 + 300 * pxm + 12
            D.rrect_on(img, xb, y - 22, xb + max(10, 20 * pxm * clamp(tdm / 0.5)), y + 22, 10, HIJAU, a)
            callout(img, (xb + 10, y + 22), (xb - 60, y + 180), "\u00b1 20 MENIT", tdm, acc=HIJAU, fsz=40, sub="DI DASAR PALUNG", alpha=a)
        tr = C.tt("jendelanya", 1, -0.3)
        if tr > 0:
            wx, wy, r = CX - 250, 700, 150
            ar = a * clamp(tr / 0.4)
            D.dot_on(img, wx, wy, r + 26, (170, 176, 184), ar)
            D.dot_on(img, wx, wy, r, (12, 26, 48), ar)
            glow(img, wx - 40, wy - 40, 90, (120, 170, 220), 0.25 * ar)
            for k in range(8):
                D.dot_on(img, wx + (r + 13) * math.cos(k * 0.785), wy + (r + 13) * math.sin(k * 0.785), 6, (120, 126, 134), ar)
            tk = C.tt("retak", 1, -0.1)
            if tk > 0:
                q = esmooth(clamp(tk / 0.35))
                rng = random.Random(3)
                for k in range(6):
                    an = rng.uniform(0, 6.28)
                    pts = [(wx + 20, wy - 10)]
                    for j in range(4):
                        an += rng.uniform(-0.5, 0.5)
                        pts.append((pts[-1][0] + math.cos(an) * r * 0.3 * q, pts[-1][1] + math.sin(an) * r * 0.3 * q))
                    M._pline(img, pts, (235, 245, 255), 3, ar)
                stiker(img, wx + 380, wy + 110, "JENDELANYA RETAK!", tk, bg=MERAH, fsz=40, tg=tg, alpha=a)
    # ---- shot C: James Cameron 2012
    a = C.win(t_lm2, t_tap, 0.5, 0.5)
    if a > 0.01:
        tt = C.tt("lima", 2, -0.3)
        u = eo(clamp(tt / 2.0))
        deepsea_challenger(img, CX - 400, -200 + 760 * u, 460, a, tg)
        glow(img, CX - 400, -200 + 760 * u + 210, 90, (255, 230, 160), 0.5 * a)
        chip(img, CX - 400, 180, "TAHUN 2012", a * C.u("tahun", 0.4, 2, -0.2), acc=EMAS, fsz=34)
        tc = C.tt("james", 1, -0.3)
        if tc > 0:
            teks(img, CX + 250, 290, "JAMES CAMERON", 64, TEKS, a * clamp(tc / 0.4), name=FB)
        teks(img, CX + 250, 360, "SUTRADARA FILM TITANIC", 28, REDUP, a * C.u("sutradara", 0.4, 1, -0.3), name=FS)
        stiker(img, CX + 250, 470, "SENDIRIAN!", C.tt("sendirian", 1, -0.2), bg=EMAS, fg=(40, 20, 0), fsz=40, tg=tg, alpha=a)
        ts = C.tt("dua", 2, -0.3)
        if ts > 0:
            bx = CX - 80
            q = eio(clamp(ts / 1.0))
            teks(img, bx, 620, "1960", 28, REDUP, a, name=FB, anchor="l")
            D.rrect_on(img, bx + 90, 600, bx + 90 + 560, 640, 20, ORANYE, a)
            teks(img, bx + 670, 620, "\u00b1 5 JAM", 28, TEKS, a, name=FB, anchor="l")
            teks(img, bx, 710, "2012", 28, REDUP, a, name=FB, anchor="l")
            D.rrect_on(img, bx + 90, 690, bx + 90 + max(40, 280 * q), 730, 20, HIJAU, a)
            teks(img, bx + 90 + 280 * q + 20, 710, "\u00b1 2,5 JAM", 28, TEKS, a * clamp(ts / 0.6), name=FB, anchor="l")
    # ---- shot D: kantong plastik di 10.898 m
    a = C.win(t_tap, C.dur + 1, 0.5, 0.1)
    if a > 0.01:
        dasar_laut(img, 880, a, seed=15)
        teks(img, CX, 330, "TEMUAN YANG MEMBUAT SEDIH", 54, TEKS, a * C.u("temuan", 0.4, 1, -0.3) * (1 - C.u("kantong", 0.4, 1, -0.4)), name=FB)
        tk = C.tt("kantong", 1, -0.4)
        rev = clamp(tk / 1.2)
        sorot(img, CX - 650, 180, 30, 1300, 560, a * 0.75 * rev)
        if tk > 0:
            kantong_plastik(img, CX + 260, 790, 220, tg, a * rev)
            callout(img, (CX + 260, 700), (CX + 400, 560), "KANTONG PLASTIK", clamp(tk - 0.5), acc=MERAH, fsz=30, alpha=a)
        chip(img, CX - 360, 200, "LAPORAN TAHUN 2018", a * C.u("tahun", 0.4, 3, -0.2), acc=MERAH, fsz=30)
        angka(img, CX - 360, 440, 10898, C.tt("sepuluh", 1, -0.3), fsz=110, suf=" m", alpha=a, col=TEKS, dur=2.2,
              sub="PALUNG MARIANA", subfsz=26)
        stiker(img, CX - 300, 650, "SAMPAH SUDAH SAMPAI KE TITIK TERDALAM", C.tt("sampah", 1, -0.2), bg=MERAH, fsz=34, tg=tg,
               alpha=a * (1 - C.u("tempat", 0.4, 1, -0.2)))
        tt = C.tt("tempat", 1, -0.3)
        if tt > 0:
            kaca(img, CX - 640, 580, CX + 40, 720, a * clamp(tt / 0.4), MERAH)
            teks(img, CX - 300, 625, "TEMPAT YANG HAMPIR TIDAK PERNAH", 30, TEKS, a * clamp(tt / 0.4), name=FB)
            teks(img, CX - 300, 675, "DIKUNJUNGI MANUSIA", 30, MERAH, a * clamp(tt / 0.4), name=FB)


# ============================================================ BAB 9 - KEMBALI KE PERMUKAAN
def v02_naik(img, C):
    tl, tg = C.tl, C.tg
    t_prj = C.w("perjalanan", 1, 0.6)
    t_anh = C.w("anehnya", 1, -0.3)
    t_kal = C.w("kalau", 1, -0.3)
    # ---- shot A: naik cepat
    a = C.win(-1, t_prj + 0.8, 0.01, 0.5)
    if a > 0.01:
        u = clamp((tl - C.w("naik", 1, 0)) / 3.7)
        deepsea_challenger(img, CX, 560 - 40 * math.sin(u * math.pi), 420, a, tg)
        gelembung(img, CX, 900, tg * 3, a, n=16, tinggi=700, seed=9, r=10)
        teks(img, CX, 180, "KEMBALI KE PERMUKAAN", 64, TEKS, a * clamp((tl - 3.4) / 0.4), name=FB, stroke=3, scol=(10, 30, 60))
        for k in range(4):
            panah(img, (CX - 300 + k * 200, 900), (CX - 300 + k * 200, 760), WHITE, 6, a * 0.5, esmooth(clamp((tl - 3.4 - k * 0.1) / 0.4)))
    # ---- shot B: rekap 5 zona
    a = C.win(t_prj, t_anh, 0.5, 0.5)
    if a > 0.01:
        judul(img, CX, 150, "5 LAPISAN LAUT YANG KITA LEWATI", C.tt("lima", 1, -0.3), fsz=50, hl=("5",), alpha=a)
        kw = [("zona", 1), ("zona", 2), ("zona", 3), ("zona", 4), ("zona", 5)]
        akt = None
        for j, (k_, n_) in enumerate(kw):
            if tl >= C.w(k_, n_, -0.3):
                akt = j
        prog = clamp((tl - t_prj) / 1.2)
        profil_zona(img, CX - 640, 220, CX - 80, 930, a, aktif=akt, prog=prog, fsz=24)
        if akt is not None:
            tt = tl - C.w(*kw[akt], -0.3)
            q = eo(clamp(tt / 0.4))
            dy = (1 - q) * 30
            z = ZONA[akt]
            x = CX + 330
            kaca(img, x - 300, 300 + dy, x + 300, 820 + dy, a * q, z[3])
            teks(img, x, 360 + dy, z[2], 34, z[3], a * q, name=FB)
            cy = 560 + dy
            if akt == 0:
                for k, (nm, col, kw_) in enumerate(_SPEK[:4]):
                    hh = 180 * (0.25 if k < 3 and tt > 1 + k * 0.4 else 1)
                    D.rrect_on(img, x - 170 + k * 110, cy + 90 - hh, x - 90 + k * 110, cy + 90, 10, col, a * q)
                cap = ["WARNA MENGHILANG", "SATU PER SATU"]
            elif akt == 1:
                rng = random.Random(3)
                up = 0.5 + 0.5 * math.sin(tg * 1.5)
                for k in range(50):
                    D.dot_on(img, x + rng.uniform(-220, 220), cy + 90 - rng.uniform(0, 60) - 140 * up * rng.uniform(0.7, 1),
                             3.2, (140, 230, 255), a * q)
                cap = ["MIGRASI TERBESAR DI BUMI", "SETIAP MALAM"]
            elif akt == 2:
                pemancing(img, x, cy + 10, 260, tg, a * q)
                cap = ["DITERANGI CAHAYA", "MAKHLUK HIDUP"]
            elif akt == 3:
                cerobong(img, x, cy + 120, 180, tg, a * q, tinggi=0.9)
                cap = ["AIR PANAS YANG", "TIDAK MENDIDIH"]
            else:
                jari(img, x, cy - 30, a * q, k=0.55)
                mobil(img, x, cy - 52, 170, a * q)
                cap = ["TEKANAN SEBERAT MOBIL", "DI UJUNG JARI"]
            teks(img, x, 720 + dy, cap[0], 30, TEKS, a * q, name=FB)
            teks(img, x, 764 + dy, cap[1], 30, TEKS, a * q, name=FB)
    # ---- shot C: baru seperempat dasar laut terpetakan rinci
    a = C.win(t_anh, t_kal, 0.5, 0.5)
    if a > 0.01:
        t_sia = C.w("siapa", 1, -0.3)
        a1 = a * (1 - 0.8 * clamp((tl - t_sia) / 0.6))
        teks(img, CX, 170, "ANEHNYA, SAMPAI HARI INI...", 46, TEKS, a1 * clamp((tl - t_anh) / 0.4), name=FB)
        gx0, gy0, nx, ny, c = CX - 620, 260, 24, 10, 44
        ts = C.tt("seperempat", 1, -0.3)
        rng = random.Random(12)
        sel = [(i, j) for i in range(nx) for j in range(ny)]
        rng.shuffle(sel)
        on = set(sel[:int(len(sel) * 0.25 * clamp(ts / 1.5))]) if ts > 0 else set()
        for i in range(nx):
            for j in range(ny):
                col = (60, 180, 230) if (i, j) in on else (22, 34, 60)
                D.rrect_on(img, gx0 + i * 52, gy0 + j * c, gx0 + i * 52 + 46, gy0 + j * c + 38, 5, col, a1 * 0.92)
        angka(img, CX - 300, 800, 25, ts, fsz=110, suf="%", alpha=a1, col=SIAN, dur=1.5, sub="DIPETAKAN SECARA RINCI", subfsz=26)
        tb = C.tt("sebagian", 1, -0.3)
        if tb > 0:
            teks(img, CX + 300, 790, "75%", 110, MERAH, a1 * clamp(tb / 0.4), name=FB)
            teks(img, CX + 300, 890, "BELUM PERNAH KITA LIHAT DENGAN JELAS", 24, REDUP, a1 * clamp(tb / 0.4), name=FS)
        tq = tl - t_sia
        if tq > 0:
            aq = a * clamp(tq / 0.5)
            D.rrect_on(img, -10, -10, W + 10, H + 10, 0, (2, 4, 10), 0.86 * aq)
            rng = random.Random(40)
            for k in range(9):
                mata_gelap(img, rng.uniform(420, W - 120), rng.choice([rng.uniform(170, 380), rng.uniform(700, 940)]), rng.uniform(1.2, 2.2), tg, aq * clamp((tq - k * 0.2) / 0.3),
                           col=rng.choice([(150, 255, 200), (255, 200, 120), (140, 200, 255)]), ph=k * 0.13)
            teks(img, CX, 500, "MAKHLUK APA LAGI", 80, TEKS, aq, name=FB)
            teks(img, CX, 600, "YANG MENUNGGU DI SANA?", 80, EMAS, aq * C.u("menunggu", 0.4, 1, -0.3), name=FB)
    # ---- shot D: CTA
    a = C.win(t_kal, C.dur + 1, 0.4, 0.3)
    if a > 0.01:
        tk = C.tt("kliktahu", 1, -0.5)
        teks(img, CX, 250, "KlikTahu", 90, TEKS, a * clamp(tk / 0.4), scale=eob(clamp(tk / 0.5), 2) if tk > 0 else 0)
        if tk > 0:
            q = eo(clamp(tk / 0.4))
            klik = tk - 1.1
            sub = klik > 0
            col = (90, 94, 110) if sub else (230, 40, 40)
            sc_ = 1.0 - 0.08 * math.sin(math.pi * clamp(klik / 0.25)) if klik > 0 else 1.0
            D.rrect_on(img, CX - 250 * sc_, 420 - 55 * sc_, CX + 250 * sc_, 420 + 55 * sc_, 55, col, a * q)
            teks(img, CX, 420, "SUBSCRIBED" if sub else "SUBSCRIBE", 44, WHITE, a * q)
            u = esmooth(clamp((tk - 0.3) / 0.8))
            kx, ky = CX + 340 - 220 * u, 620 - 180 * u
            D.poly_on(img, [(kx, ky), (kx, ky + 50), (kx + 13, ky + 38), (kx + 24, ky + 60), (kx + 32, ky + 56),
                            (kx + 21, ky + 34), (kx + 38, ky + 34)], WHITE, a * q * (1 - clamp((tk - 2.2) / 0.4)),
                      outline=SP0)
            if sub:
                partikel(img, CX, 420, klik, EMAS, a, n=16, jarak=260)
        teks(img, CX, 170, "SUKA PERJALANAN SEPERTI INI?", 36, REDUP, a * C.u("suka", 0.4, 1, -0.3) * (1 - clamp(tk / 0.3)), name=FB)
        tko = C.tt("tulis", 1, -0.4)
        if tko > 0:
            q, dy = eo(clamp(tko / 0.4)), (1 - eo(clamp(tko / 0.4))) * 30
            kaca(img, CX - 500, 600 + dy, CX + 500, 860 + dy, a * q, ORANYE)
            D.dot_on(img, CX - 410, 680 + dy, 40, ORANYE, a * q)
            teks(img, CX - 410, 680 + dy, "K", 36, SP0, a * q)
            teks(img, CX - 340, 670 + dy, "Tulis di komentar:", 30, REDUP, a * q, name=FS, anchor="l")
            msg = "Ke mana kita harus pergi berikutnya?"
            n = int(len(msg) * clamp((tko - 0.3) / 2.2))
            teks(img, CX - 340, 740 + dy, msg[:n] + ("|" if (tg * 2) % 1 < 0.5 else ""), 32, TEKS, a * q, anchor="l")
            for j, s_ in enumerate(["INTI BUMI?", "GUNUNG BERAPI?", "ANTARIKSA?"]):
                chip(img, CX - 330 + j * 330, 950, s_, a * clamp((C.tt("berikutnya", 1, -0.3) - j * 0.15) / 0.3), acc=[MERAH, ORANYE, UNGU][j], fsz=24)


# ====================================================================== REGISTRASI
VIS = {
    "v02_intro": v02_intro, "v02_matahari": v02_matahari, "v02_senja": v02_senja, "v02_malam": v02_malam,
    "v02_titanic": v02_titanic, "v02_ventilasi": v02_ventilasi, "v02_hadal": v02_hadal, "v02_terdalam": v02_terdalam,
    "v02_manusia": v02_manusia, "v02_naik": v02_naik,
}

BEATS = {
    "v02_intro": [(0.3, 1, 0, "gelembung", 0.5), ("pasifik", 1, -0.2, "pop", 0.6), ("bawah", 1, -0.3, "whoosh", 0.8),
                  ("sebelas", 1, -0.4, "riser", 0.7), ("kilometer", 1, 0.3, "impact", 0.8), ("dasarnya", 1, -0.2, "pop", 0.8),
                  ("setiap", 1, -0.3, "swish", 0.7), ("cahaya", 1, -0.35, "pop", 0.7), ("dingin", 1, -0.35, "pop", 0.7),
                  ("tekanannya", 1, -0.35, "pop", 0.7), ("meremukkan", 1, -0.1, "retak", 0.8),
                  ("sepanjang", 1, -0.4, "swish", 0.7), ("makhluk", 1, -0.3, "kilau", 0.7), ("bangkai", 1, -0.3, "thud", 0.7),
                  ("sesuatu", 1, -0.3, "glitch", 0.8), ("anehnya", 1, -0.3, "swish", 0.7), ("bulan", 1, -0.5, "pop", 0.7),
                  ("lengkap", 1, -0.2, "ding", 0.6), ("peta", 2, -0.4, "pop", 0.7), ("sendiri", 1, -0.1, "click", 0.7),
                  ("tarik", 1, -0.3, "impact", 0.9), ("menyelam", 2, 0.0, "whoosh", 1.0), ("menyelam", 2, 0.25, "gelembung", 0.9)],
    "v02_matahari": [(3.5, 1, 0, "gelembung", 0.6), ("air", 1, -0.3, "swish", 0.7), ("merah", 1, -0.2, "zap", 0.6),
                     ("jingga", 1, -0.2, "zap", 0.6), ("kuning", 1, -0.2, "zap", 0.6), ("darah", 1, -0.3, "pop", 0.7),
                     ("hijau", 1, -0.3, "glitch", 0.6), ("bukan", 1, -0.2, "pop", 0.8), ("sini", 1, -0.5, "swish", 0.7),
                     ("setiap", 1, -0.3, "tick", 0.7), ("sepuluh", 1, -0.1, "tick", 0.7), ("satu", 1, -0.4, "impact", 0.7),
                     ("sama", 1, -0.3, "pop", 0.6), ("telingamu", 1, -0.4, "swish", 0.6), ("sakit", 1, -0.2, "pop", 0.8),
                     ("penyelam", 1, -0.3, "swish", 0.7), ("empat", 1, -0.3, "impact", 0.7), ("panjang", 1, -0.6, "riser", 0.6),
                     ("dua", 2, -0.7, "swish", 0.7), ("satu", 2, -0.2, "ding", 0.7), ("berakhir", 1, -0.2, "impact", 0.9)],
    "v02_senja": [("sini", 1, -0.3, "kilau", 0.5), ("langit", 1, -0.4, "pop", 0.7), ("tumbuhan", 1, -0.3, "swish", 0.7),
                  ("tidak", 1, -0.1, "zap", 0.6), ("fotosintesis", 1, 0.5, "click", 0.7), ("tapi", 1, -0.3, "swish", 0.7),
                  ("ikan", 1, -0.3, "pop", 0.6), ("udang", 1, -0.3, "pop", 0.6), ("uburubur", 1, -0.3, "pop", 0.6),
                  ("pemangsa", 1, -0.6, "whoosh", 0.7), ("begitu", 1, -0.3, "swish", 0.7), ("naik", 1, -0.3, "riser", 0.6),
                  ("turun", 1, -0.2, "swish_up", 0.6), ("migrasi", 1, -0.3, "impact", 0.8), ("setiap", 1, -0.3, "pop", 0.6),
                  ("semakin", 1, -0.3, "swish", 0.7), ("empat", 1, -0.3, "tick", 0.7), ("hilang", 1, 0.1, "zap", 0.7)],
    "v02_malam": [("gelap", 1, -0.3, "boom", 0.7), ("selamanya", 1, -0.3, "pop", 0.5), ("sinar", 1, -0.4, "pop", 0.6),
                  ("lihat", 1, -0.3, "kilau", 0.9), ("tujuh", 1, -0.4, "riser", 0.6), ("persen", 1, 0.0, "ding", 0.7),
                  ("reaksi", 1, -0.3, "pop", 0.6), ("namanya", 1, -0.3, "swish", 0.7), ("bioluminesensi", 1, 0, "kilau", 0.8),
                  ("memancing", 1, -0.4, "pop", 0.6), ("pasangan", 1, -0.4, "pop", 0.6), ("mengecoh", 1, -0.4, "pop", 0.6),
                  ("salah", 1, -0.3, "swish", 0.7), ("umpan", 1, -0.2, "kilau", 0.7), ("penasaran", 1, -0.4, "swish", 0.5),
                  ("hap", 1, -0.05, "gigit", 1.0), ("hap", 1, 0.0, "impact", 0.7), ("zona", 2, -0.3, "swish", 0.7),
                  ("paus", 1, -0.5, "whoosh", 0.8), ("dua", 1, -0.3, "impact", 0.6), ("satu", 3, -0.4, "detak", 0.7),
                  ("cumicumi", 1, -0.4, "thud", 0.8), ("belas", 1, -0.3, "pop", 0.6)],
    "v02_titanic": [("terus", 1, -0.3, "whoosh", 0.6), ("ratarata", 1, -0.4, "ding", 0.7), ("sedikit", 1, -0.3, "swish", 0.7),
                    ("terbaring", 1, -0.4, "riser", 0.6), ("titanic", 1, -0.3, "boom", 0.9), ("tenggelam", 1, -0.3, "pop", 0.6),
                    ("ditemukan", 1, -0.3, "tick", 0.6), ("tujuh", 2, -0.3, "ding", 0.7), ("tiga", 4, -0.4, "impact", 0.8),
                    ("coba", 1, -0.3, "swish", 0.7), ("gelas", 1, -0.4, "pop", 0.7), ("dibawa", 1, -0.3, "pop", 0.6),
                    ("memeras", 1, -0.3, "retak", 0.6), ("udara", 1, -0.2, "gelembung", 0.8), ("menyusut", 1, -0.2, "zap", 0.6),
                    ("seukuran", 1, -0.2, "pop", 0.8), ("sekeliling", 1, -0.4, "swish", 0.7), ("salju", 2, -0.3, "kilau", 0.8),
                    ("sisa", 1, -0.3, "pop", 0.6), ("makanan", 1, -0.3, "pop", 0.6)],
    "v02_ventilasi": [("abisal", 1, -0.3, "boom", 0.5), ("luas", 1, -0.3, "swish", 0.6), ("lumpur", 1, -0.4, "thud", 0.6),
                      ("jutaan", 1, -0.3, "pop", 0.6), ("suhunya", 1, -0.3, "tick", 0.6), ("membeku", 1, -0.3, "pop", 0.6),
                      ("tapi", 1, -0.3, "swish", 0.7), ("kejutan", 1, -0.4, "riser", 0.6), ("menyembur", 1, -0.3, "boom", 0.9),
                      ("hitam", 1, -0.3, "pop", 0.6), ("empat", 2, -0.4, "riser", 0.6), ("celsius", 1, 0.0, "impact", 0.7),
                      ("mendidih", 1, -0.2, "pop", 0.8), ("ventilasi", 1, -0.3, "ding", 0.7), ("cacing", 1, -0.3, "pop", 0.6),
                      ("kepiting", 1, -0.3, "pop", 0.6), ("udang", 1, -0.3, "pop", 0.6), ("tanpa", 1, -0.3, "zap", 0.6),
                      ("mereka", 1, -0.3, "swish", 0.7), ("zat", 1, -0.4, "pop", 0.6), ("bakteri", 1, -0.4, "pop", 0.6),
                      ("makanan", 1, -0.4, "pop", 0.6), ("penemuan", 1, -0.3, "swish", 0.6), ("planet", 1, -0.4, "kilau", 0.8)],
    "v02_hadal": [("hadal", 1, 0.0, "boom", 0.7), ("hades", 1, -0.3, "impact", 0.7), ("zona", 2, -0.3, "swish", 0.7),
                  ("jurang", 1, -0.4, "thud", 0.6), ("lempeng", 1, -0.2, "pop", 0.6), ("menunjam", 1, -0.3, "whoosh", 0.7),
                  ("lempeng", 2, -0.2, "pop", 0.6), ("palung", 1, -0.3, "ding", 0.6), ("indonesia", 1, -0.3, "impact", 0.8),
                  ("weber", 1, -0.4, "pop", 0.7), ("dalamnya", 1, -0.4, "riser", 0.6), ("tujuh", 1, -0.4, "impact", 0.7),
                  ("bahkan", 1, -0.3, "swish", 0.7), ("ikan", 1, -0.3, "pop", 0.7), ("merekam", 1, -0.3, "click", 0.8),
                  ("delapan", 1, -0.3, "riser", 0.5), ("terdalam", 2, -0.3, "impact", 0.8), ("lembek", 1, -0.2, "pop", 0.6),
                  ("pucat", 1, -0.1, "pop", 0.6), ("sisik", 1, -0.3, "pop", 0.6), ("para", 1, -0.3, "swish", 0.6),
                  ("tidak", 1, -0.3, "zap", 0.6)],
    "v02_terdalam": [("sepuluh", 1, -0.3, "riser", 0.9), ("meter", 1, 0.0, "boom", 1.0), ("challenger", 1, -0.3, "impact", 0.7),
                     ("mariana", 1, -0.4, "pop", 0.6), ("titik", 1, -0.2, "pop", 0.8), ("seberapa", 1, -0.3, "swish", 0.7),
                     ("everest", 1, -0.3, "boom", 0.7), ("puncaknya", 1, -0.3, "tick", 0.6), ("dua", 1, -0.3, "ding", 0.7),
                     ("tekanannya", 1, -0.3, "swish", 0.7), ("seribu", 1, -0.4, "impact", 0.8), ("artinya", 1, -0.3, "swish", 0.6),
                     ("sentimeter", 1, -0.3, "pop", 0.6), ("satu", 1, -0.3, "pop", 0.7), ("mobil", 1, 0.2, "impact", 1.0),
                     ("airnya", 1, -0.3, "swish", 0.6), ("gelapnya", 1, -0.3, "boom", 0.5), ("tapi", 1, -0.3, "swish", 0.6),
                     ("kosong", 1, -0.2, "pop", 0.8), ("makhluk", 1, -0.3, "pop", 0.6), ("amfipoda", 1, -0.3, "ding", 0.7)],
    "v02_manusia": [("pernah", 1, -0.2, "impact", 0.9), ("tahun", 1, -0.3, "whoosh", 0.7), ("seribu", 1, -0.2, "pop", 0.6),
                    ("jacques", 1, -0.3, "pop", 0.6), ("don", 1, -0.2, "pop", 0.5), ("trieste", 1, -0.3, "ding", 0.6),
                    ("perjalanan", 1, -0.3, "swish", 0.7), ("lima", 1, -0.3, "tick", 0.7), ("jendelanya", 1, -0.3, "pop", 0.6),
                    ("retak", 1, -0.1, "retak", 1.0), ("dua", 1, -0.3, "ding", 0.6), ("lima", 2, -0.3, "swish", 0.7),
                    ("tahun", 2, -0.2, "pop", 0.6), ("james", 1, -0.3, "pop", 0.6), ("sendirian", 1, -0.2, "impact", 0.7),
                    ("dua", 2, -0.3, "tick", 0.6), ("tapi", 1, -0.3, "swish", 0.6), ("kantong", 1, -0.4, "riser", 0.5),
                    ("tahun", 3, -0.2, "pop", 0.6), ("sepuluh", 1, -0.3, "tick", 0.6), ("sampah", 1, -0.2, "impact", 0.8),
                    ("tempat", 1, -0.3, "pop", 0.5)],
    "v02_naik": [("naik", 1, 0.0, "riser", 0.8), ("naik", 1, 0.4, "whoosh", 0.9), ("perjalanan", 1, 0.6, "gelembung", 0.8),
                 ("lima", 1, -0.3, "swish", 0.6), ("zona", 1, -0.3, "pop", 0.7), ("zona", 2, -0.3, "pop", 0.7),
                 ("zona", 3, -0.3, "pop", 0.7), ("zona", 4, -0.3, "pop", 0.7), ("zona", 5, -0.3, "pop", 0.7),
                 ("anehnya", 1, -0.3, "swish", 0.7), ("seperempat", 1, -0.3, "riser", 0.5), ("sebagian", 1, -0.3, "impact", 0.7),
                 ("siapa", 1, -0.3, "boom", 0.6), ("menunggu", 1, -0.3, "kilau", 0.6), ("kalau", 1, -0.3, "swish", 0.7),
                 ("kliktahu", 1, -0.5, "pop", 0.8), ("kliktahu", 1, 0.6, "click", 0.9), ("tulis", 1, -0.4, "pop", 0.7),
                 ("berikutnya", 1, -0.3, "ding", 0.7)],
}
