#!/usr/bin/env python3
"""mesin_v16_laut.py — SISTEM VISUAL LAUT DALAM (Ep55+), generasi v16.

Kenapa modul baru (bukan menambah di v15):
  * v15 menggambar setiap bentuk lewat mask SEUKURAN KANVAS (1620x2880 pada SS=1,5).
    Satu poligon = satu bitmap 4,7 juta piksel. Itu sumber utama ~1,1 s/frame.
  * v16 memotong setiap bentuk ke kotak batasnya sendiri (bbox-lokal) dan meng-cache
    gradasi isi. Hasil: gambar sama, waktu jauh lebih kecil, dan gradasi bisa lebih
    halus karena tidak perlu diskalakan ulang.

Isi modul:
  - palet AIR 6 lapis kedalaman (bukan satu biru datar)
  - bentuk2/elips2/garis2 : primitif cepat (bbox-lokal, cache, outline bersih)
  - air()      : gradasi kedalaman + pita arus bergerak
  - sinar()    : berkas cahaya volumetrik dari permukaan
  - kaustik()  : jaring cahaya di dasar (numpy, murah, deterministik)
  - salju()    : partikel laut (marine snow), deterministik per waktu
  - gelembung() : aliran gelembung naik
  - dasar()    : lantai laut + riak pasir
  - hiu()      : siluet hiu parametrik (ramping <-> gempal), skala bebas
  - paus()     : siluet paus untuk skala & narasi
  - penyelam() : manusia 1,8 m untuk pembanding ukuran
  - gigi()/baris_gigi() : gigi megalodon + deret gigi mulut (mengatup <-> menganga)
  - kartu2()/label2() : tipografi v2 (kicker, sorot bergerak, wrapping seimbang)

Selftest:  python3 mesin_v16_laut.py
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import diagrams as D
from diagrams import (INK, CREAM, WHITE, MUTED, mix, clamp, seg, eo, font, tw,
                      tlh, paste_c, rrect_on, line_on, dot_on, ring_on, S)

from mesin_v15_ilustrasi import (KREM, LANGIT, LANGIT_2, SENJA, TEAL, TEAL_D, TEAL_L,
                                 PASIR, PASIR_D, TERRA, TERRA_D, OLIVE, OLIVE_D,
                                 NAVY, NAVY_D, AMBER_H, grad_v, kurva)

F_HEAD = "Poppins-Bold.ttf"
F_SUB = "Poppins-SemiBold.ttf"

# ------------------------------------------------------------------ palet laut
AIR_PERMUKAAN = (128, 196, 190)
AIR_TERANG = (58, 138, 142)
AIR_TENGAH = (28, 88, 104)
AIR_DALAM = (16, 54, 74)
AIR_GELAP = (10, 30, 46)
AIR_HITAM = (6, 18, 30)
CAHAYA_AIR = (206, 246, 236)
SOROT = (255, 214, 150)

LAPIS = [AIR_PERMUKAAN, AIR_TERANG, AIR_TENGAH, AIR_DALAM, AIR_GELAP, AIR_HITAM]

_CACHE = {}
_PANEL_CACHE = {}
_CACHE_MAX = 420


def _cache(key, fn):
    if key in _CACHE:
        return _CACHE[key]
    v = fn()
    if len(_CACHE) > _CACHE_MAX:
        _CACHE.clear()
    _CACHE[key] = v
    return v


# ------------------------------------------------------------------ primitif cepat
def _grad_isi(w, h, tone, light=0.24, dark=0.18, axis="v"):
    """Gradasi isi bentuk, UKURAN PIKEL (bukan unit dunia); di-cache per (ukuran, warna)."""
    w, h = max(2, int(w)), max(2, int(h))

    def build():
        top = np.array(mix(tone, WHITE, light), dtype=np.float32)
        mid = np.array(tone, dtype=np.float32)
        bot = np.array(mix(tone, INK, dark), dtype=np.float32)
        ys = np.linspace(0.0, 1.0, h, dtype=np.float32)
        arr = np.empty((h, 3), dtype=np.float32)
        for c in range(3):
            arr[:, c] = np.interp(ys, [0.0, 0.48, 1.0], [top[c], mid[c], bot[c]])
        out = np.repeat(arr[:, None, :], w, axis=1)
        rng = np.random.default_rng((abs(hash(tone)) + w * 7 + h) % 997)
        out += rng.normal(0.0, 0.8, (h, 1, 1)).astype(np.float32)
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")

    return _cache(("g", w, h, tone, round(light, 2), round(dark, 2), axis), build)


def _dilate(mask, k):
    """Dilasi mask L dengan jendela (2k+1) memakai numpy shift (cepat, tanpa MaxFilter)."""
    if k < 1:
        return mask
    a = np.asarray(mask, dtype=np.uint8)
    out = a.copy()
    pad = np.pad(a, k, mode="edge")
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            if abs(dx) + abs(dy) > k + 1:
                continue
            sh = pad[k + dy:k + dy + a.shape[0], k + dx:k + dx + a.shape[1]]
            np.maximum(out, sh, out=out)
    return Image.fromarray(out, "L")


def _bbox(pts, pad):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def bentuk2(img, pts, tone, outline=INK, ow=3.4, alpha=1.0, light=0.24, dark=0.18):
    """Poligon bergradasi + outline, digambar HANYA pada bbox-nya (cepat)."""
    if len(pts) < 3 or alpha <= 0.01:
        return
    pad = ow * 2 + 6
    x0, y0, x1, y1 = _bbox(pts, pad)
    cx0 = max(0, int(math.floor(S(x0))))
    cy0 = max(0, int(math.floor(S(y0))))
    cx1 = min(img.width, int(math.ceil(S(x1))))
    cy1 = min(img.height, int(math.ceil(S(y1))))
    if cx1 - cx0 < 2 or cy1 - cy0 < 2:
        return
    w, h = cx1 - cx0, cy1 - cy0
    lp = [(S(px) - cx0, S(py) - cy0) for px, py in pts]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon(lp, fill=255)
    bb = m.getbbox()
    if not bb:
        return
    fill = _grad_isi(w, h, tone, light, dark)
    lay = fill.convert("RGBA")
    if alpha < 0.999:
        m = m.point(lambda v: int(v * alpha))
    lay.putalpha(m)
    img.paste(lay.convert("RGB"), (cx0, cy0), lay)
    if outline is not None and ow > 0.3:
        k = max(1, int(round(ow * D.SS * 0.5)))
        dil = _dilate(m, k)
        edge = Image.fromarray(np.clip(np.asarray(dil, np.int16) - np.asarray(m, np.int16), 0, 255)
                               .astype(np.uint8))
        ol = Image.new("RGBA", (w, h), outline + (int(255 * 0.9),))
        ol.putalpha(edge)
        img.paste(ol.convert("RGB"), (cx0, cy0), ol)


def elips2(img, cx, cy, rx, ry, tone, outline=INK, ow=3.2, alpha=1.0, light=0.26, dark=0.18):
    if rx <= 0 or ry <= 0 or alpha <= 0.01:
        return
    pad = ow * 2 + 4
    x0 = max(0, int(math.floor(S(cx - rx - pad))))
    y0 = max(0, int(math.floor(S(cy - ry - pad))))
    x1 = min(img.width, int(math.ceil(S(cx + rx + pad))))
    y1 = min(img.height, int(math.ceil(S(cy + ry + pad))))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    w, h = x1 - x0, y1 - y0
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([S(cx - rx) - x0, S(cy - ry) - y0, S(cx + rx) - x0, S(cy + ry) - y0],
                              fill=255)
    fill = _grad_isi(w, h, tone, light, dark)
    lay = fill.convert("RGBA")
    if alpha < 0.999:
        m = m.point(lambda v: int(v * alpha))
    lay.putalpha(m)
    img.paste(lay.convert("RGB"), (x0, y0), lay)
    if outline is not None and ow > 0.3:
        k = max(1, int(round(ow * D.SS * 0.5)))
        dil = _dilate(m, k)
        edge = Image.fromarray(np.clip(np.asarray(dil, np.int16) - np.asarray(m, np.int16), 0, 255)
                               .astype(np.uint8))
        ol = Image.new("RGBA", (w, h), outline + (int(255 * 0.86),))
        ol.putalpha(edge)
        img.paste(ol.convert("RGB"), (x0, y0), ol)


def garis2(img, pts, col, wpx, alpha=1.0, bulge=0.0):
    """Polyline menebal (kesan kuas) — tetap memakai line_on (sudah lokal)."""
    n = len(pts)
    if n < 2 or alpha <= 0.01:
        return
    for i in range(n - 1):
        t = i / max(1, n - 2)
        line_on(img, pts[i], pts[i + 1], col, wpx * (1.0 - bulge * t), alpha)
    dot_on(img, pts[0][0], pts[0][1], wpx * 0.5, col, alpha)
    dot_on(img, pts[-1][0], pts[-1][1], wpx * 0.5 * (1.0 - bulge), col, alpha)


def kabut(img, y0, y1, col, kuat=0.5, seed=3):
    """Kabut kedalaman: gradasi yang lebih pekat di bawah (memisahkan lapisan jauh)."""
    def build():
        h = max(2, int(round(S(y1 - y0))))
        a = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
        al = (a ** 1.5) * kuat
        arr = np.empty((h, img.width, 4), dtype=np.uint8)
        arr[:, :, 0] = col[0]
        arr[:, :, 1] = col[1]
        arr[:, :, 2] = col[2]
        arr[:, :, 3] = (np.clip(al, 0, 1) * 255).astype(np.uint8)
        return Image.fromarray(arr, "RGBA")
    lay = _cache(("kabut", y0, y1, col, round(kuat, 3), img.width), build)
    img.paste(lay.convert("RGB"), (0, int(round(S(y0)))), lay)


# ------------------------------------------------------------------ air
def air(img, t=0.0, atas=AIR_TERANG, bawah=AIR_HITAM, y0=0, y1=1920, pita=True, seed=11):
    """Latar air: gradasi kedalaman + pita arus tipis yang bergerak lambat."""
    h = max(2, int(round(S(y1 - y0))))
    w = img.width

    def build():
        ys = np.linspace(0.0, 1.0, h, dtype=np.float32)
        out = np.empty((h, w, 3), dtype=np.float32)
        for c in range(3):
            out[:, :, c] = np.interp(ys, [0.0, 0.45, 1.0],
                                     [atas[c], mix(atas, bawah, 0.55)[c], bawah[c]])[:, None]
        rng = np.random.default_rng(seed)
        out += rng.normal(0.0, 1.1, (h, 1, 1)).astype(np.float32)
        return np.clip(out, 0, 255).astype(np.uint8)

    arr = _cache(("air", atas, bawah, y0, y1, w, seed), build)
    if pita:
        yy = np.arange(h, dtype=np.float32)[:, None]
        xx = np.arange(w, dtype=np.float32)[None, :] / max(1, w)
        band = (np.sin(yy * 0.012 + xx * 6.0 + t * 0.55) +
                0.6 * np.sin(yy * 0.021 - xx * 3.4 + t * 0.35))
        a = np.clip(band, 0, 1)[:, :] * 7.0
        img_arr = arr.astype(np.float32)
        img_arr += a[:, :, None]
        arr = np.clip(img_arr, 0, 255).astype(np.uint8)
    img.paste(Image.fromarray(arr, "RGB"), (0, int(round(S(y0)))))


def _poli_alpha(img, pts, col, alpha):
    """Poligon ber-alpha, digambar lokal pada bbox-nya (cepat, tanpa blur)."""
    if alpha <= 0.004 or len(pts) < 3:
        return
    pad = 4
    x0, y0, x1, y1 = _bbox(pts, pad)
    cx0 = max(0, int(math.floor(S(x0)))); cy0 = max(0, int(math.floor(S(y0))))
    cx1 = min(img.width, int(math.ceil(S(x1)))); cy1 = min(img.height, int(math.ceil(S(y1))))
    if cx1 - cx0 < 2 or cy1 - cy0 < 2:
        return
    lay = Image.new("RGBA", (cx1 - cx0, cy1 - cy0), (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(S(px) - cx0, S(py) - cy0) for px, py in pts],
                                fill=col + (int(255 * alpha),))
    img.paste(lay.convert("RGB"), (cx0, cy0), lay)


def sinar(img, t, n=6, x0=80, x1=1000, y0=-40, y1=1500, col=CAHAYA_AIR, kuat=0.16, seed=5):
    """Berkas cahaya volumetrik. Dipanggil HANYA saat membangun `_base` adegan (di-cache),
    jadi boleh memakai blur penuh: hasilnya lembut seperti cahaya nyata.
    """
    f = 2
    w, h = max(2, img.width // f), max(2, img.height // f)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(seed)
    for i in range(n):
        u = rng.random()
        cx = x0 + (x1 - x0) * u
        lebar = 40 + 110 * rng.random()
        ay = y1 * (0.75 + 0.25 * rng.random())
        goyang = 40 * math.sin(t * 0.30 + i * 1.7)
        al = int(255 * kuat * (0.55 + 0.45 * math.sin(t * 0.22 + i * 2.1)))
        pts = [(S(cx - lebar * 0.5) / f, S(y0) / f), (S(cx + lebar * 0.5) / f, S(y0) / f),
               (S(cx + lebar * 2.9 + goyang) / f, S(ay) / f),
               (S(cx - lebar * 2.2 + goyang) / f, S(ay) / f)]
        d.polygon(pts, fill=col + (max(6, al),))
    lay = lay.filter(ImageFilter.GaussianBlur(max(2, 18 * D.SS / f)))
    lay = lay.resize(img.size, Image.BILINEAR)
    img.paste(lay.convert("RGB"), (0, 0), lay)


def kaustik(img, t, y0, y1, col=CAHAYA_AIR, kuat=0.10, skala=1.0, seed=3):
    """Jaring cahaya di dasar laut (murah: dua gelombang sinus bersilang)."""
    h = max(2, int(round(S(y1 - y0))))
    w = img.width
    yy = np.arange(h, dtype=np.float32)[:, None] / max(1, S(1))
    xx = np.arange(w, dtype=np.float32)[None, :] / max(1, S(1))
    a = np.sin(xx * 0.011 * skala + t * 0.9 + yy * 0.004) * np.sin(yy * 0.014 * skala - t * 0.7)
    a = np.clip(a, 0, 1) ** 2.4
    fade = np.linspace(1.0, 0.25, h, dtype=np.float32)[:, None]
    alpha = (a * fade * kuat * 255).astype(np.uint8)
    arr = np.empty((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = col[0]
    arr[:, :, 1] = col[1]
    arr[:, :, 2] = col[2]
    arr[:, :, 3] = alpha
    lay = Image.fromarray(arr, "RGBA")
    img.paste(lay.convert("RGB"), (0, int(round(S(y0)))), lay)


def salju(img, t, n=90, y0=0, y1=1920, col=(214, 240, 236), kuat=0.5, seed=7, ukuran=2.6):
    """Partikel 'marine snow': deterministik dari (seed, indeks) + waktu -> tidak berkedip."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        px = rng.random()
        py = rng.random()
        sp = 0.10 + 0.22 * rng.random()
        r = ukuran * (0.5 + 1.5 * rng.random())
        x = px * 1080 + 26 * math.sin(t * 0.5 + i * 1.3)
        y = ((py + t * sp * 0.06) % 1.0) * (y1 - y0) + y0
        a = kuat * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 0.8 + i)))
        dot_on(img, x, y, r, col, a)


def gelembung(img, t, x, y0, y1, n=10, col=(224, 248, 244), seed=9, skala=1.0):
    rng = np.random.default_rng(seed)
    for i in range(n):
        px = rng.random()
        sp = 0.5 + 0.8 * rng.random()
        ph = rng.random()
        u = (ph + t * sp * 0.16) % 1.0
        r = (3 + 7 * rng.random()) * skala
        cx = x + (px - 0.5) * 150 * skala + 12 * math.sin(t * 1.4 + i)
        cy = y1 - u * (y1 - y0)
        ring_on(img, cx, cy, r, col, max(1.2, 1.5 * skala), 0.5)
        dot_on(img, cx - r * 0.3, cy - r * 0.3, max(0.8, r * 0.22), col, 0.55)


def dasar(img, y, tone=PASIR_D, t=0.0, amp=26, seed=17, riak=True):
    """Lantai laut: bukit pasir bergelombang + riak halus."""
    rng = np.random.default_rng(seed)
    pts = [(-40, 1960)]
    n = 9
    for i in range(n + 1):
        x = -40 + (1160 * i / n)
        yy = y + math.sin(i * 1.05 + seed * 0.7) * amp + (rng.random() - 0.5) * amp * 0.5
        pts.append((x, yy))
    pts.append((1120, 1960))
    bentuk2(img, pts, tone, outline=mix(tone, INK, 0.45), ow=3.0, light=0.16, dark=0.22)
    if riak:
        for i in range(7):
            yy = y + 34 + i * 26
            if yy > 1900:
                break
            garis2(img, kurva((-20, yy + 8), (540, yy - 16 + 6 * math.sin(t * 0.4 + i)),
                              (1100, yy + 10), 18), mix(tone, WHITE, 0.35), 2.0, 0.16)


# ------------------------------------------------------------------ siluet hewan
def spline(ctrl, n=48, closed=False):
    """Catmull-Rom melalui titik kontrol -> kurva halus (tanpa sudut)."""
    P = [tuple(p) for p in ctrl]
    if len(P) < 3:
        return P
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
    else:
        P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(len(P) - 3):
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        for k in range(n // max(1, len(P) - 3) + 1):
            t = k / max(1, (n // max(1, len(P) - 3)))
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


def hiu(img, x, y, panjang, tinggi=0.155, tone=AIR_GELAP, outline=None, t=0.0,
        riak_ekor=1.0, alpha=1.0, mulut=True, insang=True, sirip_punggung=1.0,
        mata=True, rim=None, ekor_bulan=True):
    """Siluet hiu yang benar secara bentuk (bukan balok memanjang).

    tinggi : tinggi badan / panjang. 0,14 ramping (mako/lemon) .. 0,22 gempal (hiu putih)
    Ekor bulan (crescent) untuk perenang cepat; `ekor_bulan=False` -> heteroserkal.
    """
    L = float(panjang)
    H = L * float(tinggi)
    ayun = math.sin(t * 1.5) * 0.035 * L * riak_ekor

    # ---- badan: sisi atas & bawah dari kurva spline (moncong lancip, perut membulat)
    snout = (x, y + 0.10 * H)
    atas = spline([(x, y + 0.06 * H),
                   (x + 0.07 * L, y - 0.30 * H),
                   (x + 0.18 * L, y - 0.46 * H),
                   (x + 0.34 * L, y - 0.50 * H),
                   (x + 0.52 * L, y - 0.40 * H),
                   (x + 0.70 * L, y - 0.24 * H),
                   (x + 0.86 * L, y - 0.11 * H),
                   (x + 0.965 * L, y - 0.045 * H)], 26)
    bawah = spline([(x + 0.965 * L, y + 0.045 * H),
                    (x + 0.86 * L, y + 0.13 * H),
                    (x + 0.70 * L, y + 0.24 * H),
                    (x + 0.52 * L, y + 0.31 * H),
                    (x + 0.34 * L, y + 0.30 * H),
                    (x + 0.18 * L, y + 0.24 * H),
                    (x + 0.07 * L, y + 0.14 * H),
                    snout], 26)
    atas = [(px, py + ayun * (max(0.0, (px - x) / L) ** 2.2)) for px, py in atas]
    bawah = [(px, py + ayun * (max(0.0, (px - x) / L) ** 2.2)) for px, py in bawah]
    badan = atas + bawah

    # ---- sirip punggung (segitiga melengkung, tepi belakang cekung)
    dx0, dx1 = 0.36, 0.56
    p_awal = (x + dx0 * L, y - 0.50 * H + ayun * (dx0 ** 2.2))
    p_ujung = (x + (dx0 + 0.075) * L, y - (0.50 + 0.95 * sirip_punggung) * H)
    p_akhir = (x + dx1 * L, y - 0.42 * H + ayun * (dx1 ** 2.2))
    punggung = ([(px, py) for px, py in spline([p_awal,
                                                (x + (dx0 + 0.035) * L, y - (0.50 + 0.55 * sirip_punggung) * H),
                                                p_ujung], 12)] +
                [(px, py) for px, py in spline([p_ujung,
                                                (x + (dx0 + 0.115) * L, y - 0.60 * H),
                                                p_akhir], 12)])

    # ---- sirip dada (panjang, menyapu ke belakang-bawah)
    dada = spline([(x + 0.255 * L, y + 0.155 * H),
                   (x + 0.315 * L, y + 0.42 * H),
                   (x + 0.235 * L, y + 0.78 * H),
                   (x + 0.385 * L, y + 0.72 * H),
                   (x + 0.345 * L, y + 0.30 * H),
                   (x + 0.325 * L, y + 0.175 * H)], 16)

    # ---- ekor
    ex, ey = x + 0.965 * L, y + ayun
    if ekor_bulan:
        ekor = spline([(ex - 0.015 * L, ey - 0.02 * H),
                       (ex + 0.075 * L, ey - 0.46 * H),
                       (ex + 0.055 * L, ey - 0.02 * H),
                       (ex + 0.062 * L, ey + 0.30 * H),
                       (ex - 0.010 * L, ey + 0.02 * H)], 18)
    else:
        ekor = spline([(ex - 0.02 * L, ey - 0.02 * H),
                       (ex + 0.13 * L, ey - 0.52 * H),
                       (ex + 0.10 * L, ey - 0.02 * H),
                       (ex + 0.13 * L, ey + 0.22 * H),
                       (ex - 0.012 * L, ey + 0.02 * H)], 18)

    for shp, tn, ow in ((punggung, mix(tone, INK, 0.05), 2.4), (dada, mix(tone, INK, 0.12), 2.2),
                        (ekor, mix(tone, INK, 0.06), 2.2)):
        bentuk2(img, shp, tn, outline=outline, ow=ow, light=0.16, dark=0.22, alpha=alpha)
    bentuk2(img, badan, tone, outline=outline, ow=2.8, light=0.22, dark=0.20, alpha=alpha)

    # ---- detail: perut lebih terang, mulut, insang, mata
    perut = spline([(x + 0.10 * L, y + 0.10 * H),
                    (x + 0.34 * L, y + 0.26 * H),
                    (x + 0.60 * L, y + 0.22 * H),
                    (x + 0.85 * L, y + 0.11 * H)], 18)
    for i in range(len(perut) - 1):
        line_on(img, perut[i], perut[i + 1], mix(tone, WHITE, 0.30), max(1.6, H * 0.10),
                alpha * 0.30)
    if rim:
        garis2(img, [(px, py) for px, py in atas[4:len(atas) - 4]], rim,
               max(1.2, L * 0.005), 0.42 * alpha)
    if mulut:
        m = spline([(x + 0.012 * L, y + 0.055 * H),
                    (x + 0.06 * L, y + 0.135 * H),
                    (x + 0.13 * L, y + 0.115 * H)], 12)
        garis2(img, m, mix(tone, WHITE, 0.55), max(1.4, L * 0.006), 0.55 * alpha)
    if insang:
        for i in range(5):
            gx = x + (0.215 + i * 0.021) * L
            garis2(img, [(gx, y - 0.14 * H), (gx + 0.010 * L, y + 0.10 * H)],
                   mix(tone, WHITE, 0.34), max(1.0, L * 0.0035), 0.30 * alpha)
    if mata:
        dot_on(img, x + 0.085 * L, y - 0.06 * H, max(1.6, L * 0.0075),
               mix(tone, WHITE, 0.70), 0.9 * alpha)


def paus(img, x, y, panjang, tinggi=0.16, tone=None, outline=None, t=0.0, alpha=1.0,
         ekor_atas=True):
    """Siluet paus: kepala tumpul membulat, badan gemuk, ekor horizontal bergerak vertikal."""
    tone = tone or mix(AIR_DALAM, TEAL_D, 0.45)
    L, H = float(panjang), float(panjang) * tinggi
    ayun = math.sin(t * 0.9) * 0.05 * L
    atas = spline([(x, y - 0.05 * H),
                   (x + 0.06 * L, y - 0.34 * H),
                   (x + 0.22 * L, y - 0.50 * H),
                   (x + 0.46 * L, y - 0.50 * H),
                   (x + 0.70 * L, y - 0.38 * H),
                   (x + 0.88 * L, y - 0.16 * H),
                   (x + 0.96 * L, y - 0.05 * H)], 24)
    bawah = spline([(x + 0.96 * L, y + 0.05 * H + ayun),
                    (x + 0.86 * L, y + 0.22 * H),
                    (x + 0.62 * L, y + 0.42 * H),
                    (x + 0.36 * L, y + 0.46 * H),
                    (x + 0.14 * L, y + 0.38 * H),
                    (x + 0.03 * L, y + 0.16 * H),
                    (x, y - 0.05 * H)], 24)
    bentuk2(img, atas + bawah, tone, outline=outline, ow=2.6, light=0.18, dark=0.20, alpha=alpha)
    ex, ey = x + 0.96 * L, y + ayun * 0.8
    bentuk2(img, spline([(ex - 0.02 * L, ey), (ex + 0.10 * L, ey - 0.13 * H),
                         (ex + 0.13 * L, ey - 0.10 * H), (ex + 0.05 * L, ey + 0.01 * H),
                         (ex + 0.13 * L, ey + 0.12 * H), (ex + 0.09 * L, ey + 0.04 * H),
                         (ex - 0.02 * L, ey + 0.02 * H)], 16),
            mix(tone, INK, 0.08), outline=outline, ow=2.0, light=0.12, dark=0.2, alpha=alpha)
    # sirip dada panjang (ciri paus)
    bentuk2(img, spline([(x + 0.30 * L, y + 0.22 * H), (x + 0.34 * L, y + 0.52 * H),
                         (x + 0.22 * L, y + 0.88 * H), (x + 0.40 * L, y + 0.92 * H),
                         (x + 0.40 * L, y + 0.44 * H)], 14),
            mix(tone, INK, 0.06), outline=outline, ow=2.0, light=0.12, dark=0.2, alpha=alpha)
    # mulut lebar
    garis2(img, spline([(x + 0.02 * L, y + 0.10 * H), (x + 0.14 * L, y + 0.20 * H),
                        (x + 0.30 * L, y + 0.18 * H)], 12),
           mix(tone, WHITE, 0.45), max(1.6, L * 0.006), 0.5 * alpha)
    dot_on(img, x + 0.10 * L, y + 0.02 * H, max(1.4, L * 0.006), mix(tone, WHITE, 0.6), 0.7)


def penyelam(img, x, y, tinggi=1.8, skala=1.0, tone=INK, outline=None, t=0.0, alpha=1.0):
    """Siluet manusia (pembanding ukuran). tinggi dalam meter; 1 m = `skala` px."""
    h = tinggi * skala
    cx = x
    kepala_r = h * 0.055
    cy = y - h + kepala_r
    elips2(img, cx, cy, kepala_r * 1.02, kepala_r * 1.12, tone, outline=outline, ow=1.4,
           alpha=alpha, light=0.25, dark=0.15)
    bentuk2(img, [(cx - h * 0.072, cy + kepala_r * 1.15), (cx + h * 0.072, cy + kepala_r * 1.15),
                  (cx + h * 0.088, y - h * 0.36), (cx - h * 0.088, y - h * 0.36)], tone,
           outline=outline, ow=1.6, alpha=alpha, light=0.2, dark=0.12)
    garis2(img, [(cx - h * 0.068, cy + h * 0.24), (cx - h * 0.14, y - h * 0.44)], tone,
           max(2.0, h * 0.028), alpha)
    garis2(img, [(cx + h * 0.068, cy + h * 0.24), (cx + h * 0.15, y - h * 0.46)], tone,
           max(2.0, h * 0.028), alpha)
    garis2(img, [(cx - h * 0.042, y - h * 0.36), (cx - h * 0.058, y)], tone,
           max(2.2, h * 0.034), alpha)
    garis2(img, [(cx + h * 0.042, y - h * 0.36), (cx + h * 0.058, y)], tone,
           max(2.2, h * 0.034), alpha)


# ------------------------------------------------------------------ gigi & mulut
def gigi(img, x, y, tinggi, rot=0.0, tone=None, outline=None, alpha=1.0, gerigi=True,
         lengkung=0.16):
    """Gigi megalodon yang benar: segitiga sempit (tinggi 1,7x lebar), tepi sedikit cembung,
    ujung runcing, gerigi halus di kedua tepi, akar V pendek.

    `lengkung` = seberapa tepi menekuk ke belakang (0 = lurus).
    """
    tone = tone or mix(CREAM, PASIR, 0.20)
    outline = outline or mix(TERRA_D, INK, 0.30)
    h = float(tinggi)
    w = h * 0.46                      # lebar dasar mahkota
    ca, sa = math.cos(rot), math.sin(rot)

    def T(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)

    # --- akar: leher sempit lalu dua ujung bercabang pendek (khas Otodus)
    akar = spline([T(-w * 0.50, 0.005 * h), T(-w * 0.40, 0.055 * h), T(-w * 0.30, 0.10 * h),
                   T(-w * 0.13, 0.065 * h), T(0.0, 0.105 * h), T(w * 0.13, 0.065 * h),
                   T(w * 0.30, 0.10 * h), T(w * 0.40, 0.055 * h), T(w * 0.50, 0.005 * h)], 12)
    bentuk2(img, akar, mix(tone, INK, 0.26), outline=outline, ow=2.0, light=0.12, dark=0.24,
           alpha=alpha)

    # --- mahkota: dua tepi cembung; kalau `gerigi`, tepinya bergerigi (takik nyata)
    kiri, kanan = [], []
    N = 26 if gerigi else 16
    takik = h * 0.016 if gerigi else 0.0
    for i in range(N + 1):
        u = i / N
        setengah = (w * 0.5) * (1.0 - u ** 1.55)
        px_geser = -w * lengkung * u ** 2
        gigi_takik = takik if (gerigi and i % 2 == 1 and 0.06 < u < 0.94) else 0.0
        kiri.append(T(px_geser - setengah + gigi_takik, -u * h))
        kanan.append(T(px_geser + setengah - gigi_takik, -u * h))
    bentuk2(img, kiri + kanan[::-1], tone, outline=outline, ow=2.2, light=0.36, dark=0.12,
           alpha=alpha)


def _busur_gigi(cx, cy, rx, ry, turun=0.0, n=26):
    """Busur gusi: cekung (naik di tengah) -> daftar titik + fungsi y pada u."""
    pts = []
    for i in range(n + 1):
        u = i / n
        x = cx - rx + 2 * rx * u
        y = cy + turun - ry * (0.62 + 0.38 * math.sin(math.pi * u) ** 0.75)
        pts.append((x, y))
    return pts


def _y_busur(cx, cy, rx, ry, turun, u):
    x = cx - rx + 2 * rx * u
    y = cy + turun - ry * (0.62 + 0.38 * math.sin(math.pi * u) ** 0.75)
    return x, y


def baris_gigi(img, cx, cy, lebar, tinggi, buka=0.0, n=9, al=1.0):
    """Mulut megalodon tampak depan: rongga gelap + gusi atas/bawah + deret gigi.

    Urutan gambar dijaga (rongga -> gusi -> gigi) supaya gusi tidak menimpa gigi.
    """
    rx = lebar * 0.5
    ry = tinggi * 0.5
    turun_b = ry * (1.02 + 1.15 * clamp(buka))
    atas = _busur_gigi(cx, cy, rx, ry, 0.0, 26)
    bawah = _busur_gigi(cx, cy, rx, ry, turun_b, 26)

    # 1) rongga mulut: daerah antara kedua gusi
    rongga = atas + list(reversed(bawah))
    bentuk2(img, rongga, mix(AIR_HITAM, TERRA_D, 0.34), outline=None, ow=0,
           light=0.04, dark=0.30, alpha=al)
    # 2) gusi
    garis2(img, atas, mix(TERRA_D, TERRA, 0.30), max(9, lebar * 0.030), 0.95 * al)
    garis2(img, bawah, mix(TERRA_D, TERRA, 0.24), max(8, lebar * 0.026), 0.92 * al)

    # 3) gigi atas (menggantung) & bawah (berdiri) — depan paling besar
    for baris, (turun, arah) in enumerate(((0.0, 1), (turun_b, -1))):
        for i in range(n):
            u = 0.055 + (i + 0.5) / n * 0.89
            gx, gy = _y_busur(cx, cy, rx, ry, turun, u)
            depan = 1.0 - abs(u - 0.5) * 2
            pjg = ry * (0.30 + 0.26 * depan)
            sudut = (u - 0.5) * 0.55
            rot = (math.pi + sudut) if arah > 0 else sudut
            gigi(img, gx, gy + (3 if arah > 0 else -3), pjg, rot=rot, alpha=al,
                 tone=mix(CREAM, PASIR, 0.05 + 0.22 * abs(u - 0.5)), gerigi=False,
                 lengkung=0.10)


# ------------------------------------------------------------------ tipografi v2
def _wrap(text, f, maxw):
    kata = text.split()
    baris, kini = [], ""
    for k in kata:
        coba = (kini + " " + k).strip()
        if tw(coba, f) <= maxw or not kini:
            kini = coba
        else:
            baris.append(kini)
            kini = k
    if kini:
        baris.append(kini)
    return baris


def kartu2(img, lines, y=1470, fsz=62, hl=None, al=1.0, dy=0.0, tab=None, kicker=None,
           lebar_maks=980, shadow=True, fokus=0.0):
    """Kartu judul v2: kicker DI DALAM kartu, dua baris besar, sorot bergerak.

    Kicker diletakkan di dalam kartu (bukan pil melayang di atasnya) supaya tidak
    pernah bertabrakan dengan ilustrasi di belakangnya.
    """
    if al <= 0.02:
        return
    f = font(F_HEAD, fsz)
    baris = []
    for ln in lines:
        if tw(ln, f) > lebar_maks:
            baris += _wrap(ln, f, lebar_maks)
        else:
            baris.append(ln)
    lh = tlh(f) * 1.06
    total_h = lh * len(baris)
    pad_x, pad_y = 46, 34
    kick_h = 54 if kicker else 0
    wcard = min(lebar_maks + pad_x * 2, max(tw(b, f) for b in baris) + pad_x * 2)
    y0 = y - total_h / 2 - pad_y + dy - kick_h
    y1 = y + total_h / 2 + pad_y + dy
    x0, x1 = 540 - wcard / 2, 540 + wcard / 2

    # Panel + bayangan di-cache: GaussianBlur(16) pada ~1000x300 px butuh ~35 ms/frame.
    # Isi (teks, kicker, tab) digambar sesudahnya, jadi tampilan tidak berubah.
    _key = (round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1), bool(shadow))
    _cached = _PANEL_CACHE.get(_key) if shadow else None
    if _cached is not None:
        img.paste(_cached[0], _cached[1], _cached[0])
    else:
        if shadow:
            pad = 70
            bx0 = max(0, int(S(x0 - pad))); by0 = max(0, int(S(y0 - pad)))
            bx1 = min(img.width, int(S(x1 + pad))); by1 = min(img.height, int(S(y1 + pad)))
            lay = Image.new("RGBA", (max(2, bx1 - bx0), max(2, by1 - by0)), (0, 0, 0, 0))
            ImageDraw.Draw(lay).rounded_rectangle([S(x0 + 6) - bx0, S(y0 + 14) - by0,
                                                   S(x1 + 6) - bx0, S(y1 + 14) - by0],
                                                  radius=S(34), fill=mix(NAVY, INK, 0.4) + (78,))
            lay = lay.filter(ImageFilter.GaussianBlur(S(16)))
            panel = lay.copy()
            ImageDraw.Draw(panel).rounded_rectangle(
                [S(x0) - bx0, S(y0) - by0, S(x1) - bx0, S(y1) - by0], radius=S(34),
                fill=mix(CREAM, WHITE, 0.78) + (int(255 * 0.98 * al),),
                outline=mix(NAVY, INK, 0.22) + (255,), width=max(1, int(S(3.4))))
            if len(_PANEL_CACHE) > 48:
                _PANEL_CACHE.clear()
            _PANEL_CACHE[_key] = (panel, (bx0, by0))
            img.paste(panel, (bx0, by0), panel)
        else:
            rrect_on(img, x0, y0, x1, y1, 34, mix(CREAM, WHITE, 0.78), 0.98 * al,
                     outline=mix(NAVY, INK, 0.22), width=3.4)

    # garis pemisah tipis antara kicker & judul
    if kicker:
        fk = font(F_SUB, 25)
        paste_c(img, 540, y0 + 34, kicker, fk, mix(NAVY, MUTED, 0.45), 0.92 * al)
        line_on(img, (x0 + 34, y0 + 62), (x1 - 34, y0 + 62), mix(NAVY, MUTED, 0.55), 2.0, 0.18 * al)

    for i, ln in enumerate(baris):
        cy = y0 + kick_h + pad_y + lh * (i + 0.5)
        col = mix(NAVY, INK, 0.12)
        if hl and hl in ln:
            a = ln.index(hl)
            pre, post = ln[:a], ln[a + len(hl):]
            wpre, whl = tw(pre, f), tw(hl, f)
            x_start = 540 - tw(ln, f) / 2
            sapu = clamp((fokus - 0.15) / 0.55)
            rrect_on(img, x_start + wpre - 8, cy - lh * 0.44, x_start + wpre + whl + 8,
                     cy + lh * 0.46, 12, mix(AMBER_H, SENJA, 0.35), 0.55 * sapu * al)
        paste_c(img, 540, cy, ln, f, col, al)

    if tab:
        rrect_on(img, x0 + 40, y0 - 15, x0 + 40 + 104, y0 + 13, 14, tab, 0.96 * al)


def label2(img, cx, cy, text, fsz=26, tone=None, bg=None, al=1.0, pad=(30, 18), bunder=22):
    """Label kapsul v2 dengan bayangan tipis (untuk angka satuan di peta/ilustrasi)."""
    tone = tone or mix(NAVY, INK, 0.1)
    bg = bg or mix(CREAM, WHITE, 0.6)
    f = font(F_SUB, fsz)
    w = tw(text, f) + pad[0] * 2
    h = tlh(f) + pad[1] * 2
    m = 46                                   # margin aman: label tidak boleh terpotong tepi
    cx = min(max(cx, m + w / 2), 1080 - m - w / 2)
    cy = min(max(cy, m + h / 2), 1920 - m - h / 2)
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, bunder, bg, 0.95 * al,
             outline=mix(NAVY, INK, 0.28), width=2.4)
    paste_c(img, cx, cy, text, f, tone, al)


def sumber(img, text, y=1692, al=1.0):
    paste_c(img, 540, y, text, font(F_SUB, 22), mix(NAVY, MUTED, 0.35), 0.62 * al)


# ------------------------------------------------------------------ selftest
def _contoh():
    import types
    for ss in (0.35, 1.0):
        D.SS = ss
        img = Image.new("RGB", (int(1080 * ss), int(1920 * ss)), AIR_TENGAH)
        air(img, 3.2)
        sinar(img, 2.4, kuat=0.2)
        salju(img, 5.0, n=40)
        dasar(img, 1580)
        kaustik(img, 2.0, 1450, 1920)
        hiu(img, 120, 900, 620, tinggi=0.15, tone=AIR_GELAP, t=1.0)
        hiu(img, 120, 1100, 380, tinggi=0.22, tone=mix(AIR_GELAP, TEAL_D, 0.4), t=2.0)
        paus(img, 400, 620, 420)
        penyelam(img, 880, 1500, 1.8, skala=90)
        gigi(img, 900, 700, 180, rot=0.18)
        baris_gigi(img, 540, 420, 640, 300, buka=0.35)
        kartu2(img, ["MEGALODON BUKAN", "HIU PUTIH RAKSASA"], hl="BUKAN", y=1470, fsz=62)
        label2(img, 300, 300, "24,3 METER")
        sumber(img, "Sumber: uji internal")
        img.resize((int(540 * ss), int(960 * ss)), Image.LANCZOS).save(f"/tmp/v16_selftest_{ss}.jpg",
                                                                     quality=90)
    print("selftest v16: primitif OK (air, sinar, kaustik, salju, hiu, paus, penyelam, gigi, baris_gigi, kartu)")


if __name__ == "__main__":
    _contoh()
