#!/usr/bin/env python3
"""mesin_v17_terang.py — LAUT TERANG: sistem visual gaya KlikTahu untuk tema laut.

Kenapa modul ini ada
--------------------
Ep55 (v16 "LAUT DALAM") secara teknis bersih, tapi **keluar dari bahasa visual
KlikTahu**: latar teal gelap nyaris hitam, hewan tanpa garis luar, kartu krem
kehilangan kontras. Pembanding Ep52-Ep54: kertas krem, air/objek beroutline
tinta tipis, warna terakota-olive-navy, banyak ruang kosong.

v17 memakai ULANG mesin cepat v16 (primitif bbox-lokal, cache gradasi, dilasi
numpy) tetapi menggambar dunia yang berbeda:

  kertas krem -> langit -> permukaan bergelombang -> air teal muda (TIDAK hitam)
  -> sinar krem -> pasir beroutline -> biota beroutline tinta

Isi:
  - palet TERANG (6 lapis air, tidak ada yang mendekati hitam)
  - langit()/matahari()/awan_kecil() : pita langit di atas permukaan
  - permukaan()  : garis gelombang beroutline + buih
  - air_t()      : gradasi air terang + pita arus
  - sinar_t()    : berkas cahaya krem (poligon datar, bukan volumetrik gelap)
  - dasar_pasir(): pasir + kerikil + rumput laut, tepi beroutline
  - gelembung_t(): gelembung beroutline
  - hiu_t()      : hiu beroutline + perut krem + mata + insang + 2 sirip kecil
  - paus_t()     : paus beroutline untuk skala & narasi
  - penyelam_t() : manusia 1,8 m beroutline
  - gigi_t()     : gigi dengan outline tinta + akar terakota
  - baris_gigi_t(): mulut menganga, rongga gelap, gusi terakota

Selftest:  python3 mesin_v17_terang.py
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import diagrams as D
import mesin_v15_ilustrasi as V15
import mesin_v16_laut as V16
from diagrams import (INK, CREAM, WHITE, MUTED, mix, clamp, font, tw, tlh, paste_c,
                      rrect_on, line_on, dot_on, ring_on, S)

from mesin_v15_ilustrasi import (KERTAS, KREM, LANGIT, LANGIT_2, SENJA, TEAL, TEAL_D,
                                 TEAL_L, PASIR, PASIR_D, TERRA, TERRA_D, OLIVE, OLIVE_D,
                                 NAVY, NAVY_D, AMBER_H, grad_v, kurva)

F_HEAD = "Poppins-Bold.ttf"
F_SUB = "Poppins-SemiBold.ttf"

# ---------------------------------------------------------------- palet TERANG
# Tidak ada satu pun warna di sini yang turun ke hitam. Air terdalam = TEAL.
AIR_1 = (182, 216, 204)      # permukaan, hampir kertas
AIR_2 = (146, 194, 181)      # dangkal
AIR_3 = (104, 168, 156)      # tengah
AIR_4 = (66, 136, 126)       # dalam
AIR_5 = (58, 124, 116)       # terdalam (tetap terang, bukan hitam)
BUIH = (252, 250, 242)
PASIR_T = (233, 208, 173)
PASIR_TD = (211, 181, 145)
HIU = (38, 74, 82)           # badan hiu: slate-teal gelap, tetap beroutline
HIU_2 = (30, 54, 66)         # versi lebih dingin (hiu putih)
HIU_PERUT = (250, 244, 230)
DARAH = (150, 60, 46)

# ---------------------------------------------------------------- primitif
bentuk2 = V16.bentuk2
elips2 = V16.elips2
garis2 = V16.garis2
spline = V16.spline
label2 = V16.label2
kartu2 = V16.kartu2
sumber = V16.sumber
_CACHE = V16._CACHE


def grad_t(w, h, stops, seed=1, dither=1.1):
    """Gradasi vertikal tanpa banding: dither per PIKEL (v15 memakai per baris -> garis)."""
    hh, ww = max(2, int(round(S(h)))), max(2, int(round(S(w))))
    ys = np.linspace(0.0, 1.0, hh, dtype=np.float32)
    pos = np.array([st[0] for st in stops], dtype=np.float32)
    cols = np.array([st[1] for st in stops], dtype=np.float32)
    out = np.empty((hh, ww, 3), dtype=np.float32)
    for c in range(3):
        out[:, :, c] = np.interp(ys, pos, cols[:, c])[:, None]
    rng = np.random.default_rng(seed + 31)
    out += rng.normal(0.0, dither, (hh, ww, 1)).astype(np.float32)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def kabut_t(img, y0, y1, col=AIR_1, kuat=0.55):
    """Lapisan kabut terang (kedalaman dibalik: makin jauh makin pucat)."""
    V16.kabut(img, y0, y1, col, kuat)


# ---------------------------------------------------------------- langit
SURF = 330           # garis permukaan air (px)


def langit(img, y0=0, y1=SURF, a=None, b=None, seed=3):
    a = a or LANGIT
    b = b or mix(LANGIT_2, SENJA, 0.30)
    g = grad_t(1080, y1 - y0, [(0.0, mix(a, WHITE, 0.22)), (0.55, a), (1.0, b)], seed=seed)
    img.paste(g, (0, int(round(S(y0)))))


def matahari(img, cx, cy, r, t=0.0):
    """Matahari gaya KlikTahu: piringan beroutline + berkas pendek berputar."""
    for i in range(10):
        a = t * 0.20 + i * math.pi / 5
        r0, r1 = r * 1.30, r * 1.62 + 6 * math.sin(t * 1.4 + i)
        line_on(img, (cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
                (cx + r1 * math.cos(a), cy + r1 * math.sin(a)), mix(SENJA, TERRA, 0.35), 7.0, 0.90)
    elips2(img, cx, cy, r, r, mix(AMBER_H, SENJA, 0.35), outline=mix(TERRA_D, INK, 0.25),
           ow=3.0, light=0.30, dark=0.10)


def awan_kecil(img, cx, cy, w, h, tone=None, seed=1):
    tone = tone or mix(WHITE, CREAM, 0.35)
    rng = np.random.default_rng(seed)
    for i in range(4):
        u = (i + 0.5) / 4
        r = h * (0.55 + 0.35 * math.sin(math.pi * u)) * (0.9 + 0.2 * rng.random())
        elips2(img, cx + (u - 0.5) * w * 0.9, cy - r * 0.15, r * 1.25, r, tone,
               outline=mix(INK, NAVY, 0.4), ow=2.6, light=0.30, dark=0.04)


def permukaan(img, y=SURF, t=0.0, amp=9, n=26):
    """Garis permukaan air: pita krem beroutline + buih kecil di puncak."""
    pts = [(x, y + amp * math.sin(x / 78.0 + t * 1.1)) for x in range(-30, 1120, n)]
    bentuk2(img, pts + [(1120, y - 60), (-30, y - 60)], mix(AIR_1, BUIH, 0.55),
            outline=None, ow=0, light=0.20, dark=0.02)
    garis2(img, pts, mix(INK, TEAL_D, 0.55), 3.4, 0.72)
    for i in range(11):
        x = 30 + i * 96 + (t * 14) % 96
        yy = y + amp * math.sin(x / 78.0 + t * 1.1)
        dot_on(img, x, yy - 9, 3.4, BUIH, 0.75)


def air_t(img, t=0.0, y0=SURF, y1=1920, atas=AIR_1, bawah=AIR_5, seed=11):
    """Air terang: gradasi 3 stop + pita arus tipis (bukan gradasi gelap)."""
    g = grad_t(1080, y1 - y0, [(0.0, atas), (0.24, mix(atas, bawah, 0.26)),
                               (0.52, mix(atas, bawah, 0.55)), (0.80, mix(atas, bawah, 0.86)),
                               (1.0, bawah)], seed=seed)
    img.paste(g, (0, int(round(S(y0)))))
    for k in range(3):
        yy = y0 + (y1 - y0) * (0.30 + k * 0.22)
        for i in range(6):
            x = (i * 190 + t * (12 + k * 7)) % 1280 - 120
            pw = 150 + k * 40
            pts = [(x + j * pw / 7.0, yy + 7 * math.sin(j * 0.8 + t + i)) for j in range(8)]
            garis2(img, pts, mix(BUIH, AIR_1, 0.35), 3.0 - k * 0.4, 0.16)


def sinar_t(img, t=0.0, n=4, x0=90, x1=1010, y0=SURF - 10, y1=1500, col=None, kuat=0.34, seed=5):
    """Berkas cahaya krem datar (gaya poster, bukan volumetrik gelap)."""
    col = col or mix(BUIH, AMBER_H, 0.10)
    rng = np.random.default_rng(seed)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(n):
        xa = x0 + (x1 - x0) * (i + 0.5) / n + (rng.random() - 0.5) * 60
        wa = 26 + rng.random() * 34
        wb = wa * (2.4 + rng.random())
        xb = xa + 120 + (rng.random() - 0.5) * 260
        a0 = kuat * (0.55 + 0.45 * math.sin(t * 0.8 + i * 1.7))
        a0 = max(0.0, a0)
        for ruas in range(3):                      # 3 ruas: makin dalam makin tipis
            u0, u1 = ruas / 3.0, (ruas + 1) / 3.0
            ya, yb = y0 + (y1 - y0) * u0, y0 + (y1 - y0) * u1
            x_0 = xa + (xb - xa) * u0
            x_1 = xa + (xb - xa) * u1
            w_0 = wa + (wb - wa) * u0
            w_1 = wa + (wb - wa) * u1
            aa = a0 * (1.0 - 0.55 * u0)
            d.polygon([(S(x_0 - w_0), S(ya)), (S(x_0 + w_0), S(ya)),
                       (S(x_1 + w_1), S(yb)), (S(x_1 - w_1), S(yb))],
                      fill=col + (int(235 * aa),))
    lay = lay.filter(ImageFilter.GaussianBlur(S(9)))
    img.paste(lay.convert("RGB"), (0, 0), lay)


def dasar_pasir(img, y=1770, t=0.0, tone=None, amp=16, seed=17, outline=True, rumput=True):
    """Pasir: tepi bergelombang beroutline tinta + kerikil + rumput laut."""
    tone = tone or PASIR_T
    rng = np.random.default_rng(seed)
    pts = [(x, y + amp * math.sin(x / 118.0 + seed * 0.7) + rng.random() * 5)
           for x in range(-30, 1120, 30)]
    bentuk2(img, pts + [(1120, 1930), (-30, 1930)], tone,
            outline=mix(INK, OLIVE_D, 0.35) if outline else None, ow=3.4,
            light=0.16, dark=0.06)
    for i in range(26):                                    # butir pasir
        x = rng.random() * 1080
        yy = y + 40 + rng.random() * (1900 - y)
        dot_on(img, x, yy, 1.5 + rng.random() * 1.7, PASIR_TD, 0.30)
    if rumput:
        for i, gx in enumerate((92, 150, 946, 1006)):
            h = 66 + (i * 29) % 44
            for k in range(3):
                bx = gx + (k - 1) * 13
                pts2 = kurva((bx, y + 12), (bx + 16 * (k - 1) + 2, y - h * 0.5),
                             (bx + 30 * (k - 1), y - h), 14)
                garis2(img, pts2, mix(OLIVE, OLIVE_D, 0.35 + 0.12 * k), 7.0, 0.92)
    for i, (cx, r, tn) in enumerate(((300, 13, PASIR_TD), (352, 8, mix(TERRA, PASIR, 0.45)),
                                     (806, 11, PASIR_TD), (846, 7, mix(OLIVE, PASIR, 0.5)))):
        elips2(img, cx, y + 92 + i * 9, r * 1.3, r, tn, outline=mix(INK, OLIVE_D, 0.4),
               ow=2.2, light=0.26, dark=0.10)


def gelembung_t(img, cx, cy, r, al=1.0):
    elips2(img, cx, cy, r, r, mix(BUIH, AIR_1, 0.20), outline=mix(INK, TEAL_D, 0.5),
           ow=1.8, alpha=al, light=0.34, dark=0.02)


def gelembung_naik(img, t, x0, x1, ymin, ymax, n=7, seed=9, skala=1.0):
    rng = np.random.default_rng(seed)
    for i in range(n):
        ph = rng.random()
        u = (ph + t * (0.16 + 0.10 * rng.random())) % 1.0
        x = x0 + (x1 - x0) * rng.random() + 12 * math.sin(t * 1.3 + i)
        y = ymax - (ymax - ymin) * u
        r = (3.2 + 4.6 * rng.random()) * skala
        gelembung_t(img, x, y, r, 0.55 + 0.35 * math.sin(u * math.pi))


# ---------------------------------------------------------------- biota
def _badan_hiu(x, y, L, H, ayun):
    """Kurva badan hiu (dinormalisasi), moncong di kiri."""
    atas = spline([(x, y + 0.06 * H), (x + 0.07 * L, y - 0.30 * H), (x + 0.18 * L, y - 0.46 * H),
                   (x + 0.34 * L, y - 0.50 * H), (x + 0.52 * L, y - 0.40 * H),
                   (x + 0.70 * L, y - 0.24 * H), (x + 0.86 * L, y - 0.11 * H),
                   (x + 0.965 * L, y - 0.045 * H)], 26)
    bawah = spline([(x + 0.965 * L, y + 0.045 * H), (x + 0.86 * L, y + 0.13 * H),
                    (x + 0.70 * L, y + 0.24 * H), (x + 0.52 * L, y + 0.31 * H),
                    (x + 0.34 * L, y + 0.30 * H), (x + 0.18 * L, y + 0.24 * H),
                    (x + 0.07 * L, y + 0.14 * H), (x, y + 0.06 * H)], 26)
    sh = lambda p: (p[0], p[1] + ayun * (max(0.0, (p[0] - x) / L) ** 2.2))
    return [sh(p) for p in atas], [sh(p) for p in bawah]


def hiu_t(img, x, y, panjang, tinggi=0.155, tone=None, outline=None, t=0.0,
          ekor_bulan=True, insang=True, mata=True, mulut=True, perut=True,
          alpha=1.0, bayang=0.0, sirip=1.0):
    """Hiu gaya KlikTahu: badan beroutline tinta, perut krem, mata + insang.

    Berbeda dari hiu() v16 yang berupa SILUET: di sini badan punya garis luar
    tinta 3,6 px dan perut krem — bahasa ilustrasi Ep52-54.
    """
    L, H = float(panjang), float(panjang) * float(tinggi)
    tone = tone or HIU
    outline = outline or mix(INK, NAVY_D, 0.35)
    ow = 3.6 if L > 320 else 3.0
    ayun = math.sin(t * 1.45) * 0.030 * L
    atas, bawah = _badan_hiu(x, y, L, H, ayun)
    badan = atas + bawah

    if bayang > 0:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).polygon([(S(px), S(py + 26)) for px, py in badan],
                                    fill=mix(INK, TEAL_D, 0.45) + (int(52 * bayang),))
        lay = lay.filter(ImageFilter.GaussianBlur(S(14)))
        img.paste(lay.convert("RGB"), (0, 0), lay)

    # --- sirip punggung (tepi belakang cekung)
    dx0 = 0.355
    p_awal = (x + dx0 * L, y - 0.49 * H + ayun * (dx0 ** 2.2))
    p_ujung = (x + (dx0 + 0.072) * L, y - (0.49 + 0.92 * sirip) * H)
    p_akhir = (x + 0.555 * L, y - 0.40 * H + ayun * (0.555 ** 2.2))
    punggung = (spline([p_awal, (x + (dx0 + 0.030) * L, y - (0.49 + 0.54 * sirip) * H),
                        p_ujung], 10) +
                spline([p_ujung, (x + (dx0 + 0.108) * L, y - 0.58 * H), p_akhir], 10))
    # --- sirip dada
    dada = spline([(x + 0.255 * L, y + 0.155 * H), (x + 0.315 * L, y + 0.42 * H),
                   (x + 0.235 * L, y + 0.78 * H), (x + 0.385 * L, y + 0.72 * H),
                   (x + 0.345 * L, y + 0.30 * H), (x + 0.325 * L, y + 0.175 * H)], 16)
    dada = [(px, py + ayun * 0.10) for px, py in dada]
    # --- sirip punggung kedua + sirip dubur (detail yang bikin "hiu", bukan ikan)
    punggung2 = spline([(x + 0.735 * L, y - 0.215 * H), (x + 0.775 * L, y - 0.335 * H),
                        (x + 0.815 * L, y - 0.185 * H)], 8)
    dubur = spline([(x + 0.795 * L, y + 0.135 * H + ayun * 0.4), (x + 0.822 * L, y + 0.245 * H),
                    (x + 0.852 * L, y + 0.115 * H + ayun * 0.4)], 8)
    # --- ekor
    ex, ey = x + 0.965 * L, y + ayun
    if ekor_bulan:
        ekor = spline([(ex - 0.015 * L, ey - 0.02 * H), (ex + 0.075 * L, ey - 0.46 * H),
                       (ex + 0.055 * L, ey - 0.02 * H), (ex + 0.062 * L, ey + 0.30 * H),
                       (ex - 0.010 * L, ey + 0.02 * H)], 18)
    else:
        ekor = spline([(ex - 0.02 * L, ey - 0.02 * H), (ex + 0.13 * L, ey - 0.52 * H),
                       (ex + 0.10 * L, ey - 0.02 * H), (ex + 0.13 * L, ey + 0.22 * H),
                       (ex - 0.012 * L, ey + 0.02 * H)], 18)

    for shp, tn in ((punggung2, tone), (dubur, tone), (punggung, mix(tone, INK, 0.10)),
                    (dada, mix(tone, INK, 0.16)), (ekor, mix(tone, INK, 0.06))):
        bentuk2(img, shp, tn, outline=outline, ow=max(2.2, ow * 0.72), alpha=alpha,
                light=0.16, dark=0.20)
    bentuk2(img, badan, tone, outline=outline, ow=ow, alpha=alpha, light=0.24, dark=0.18)

    # --- perut krem: poligon antara garis perut dan garis inset (sampel u sama -> tidak zigzag)
    if perut:
        ctrl_b = [(x + 0.965 * L, y + 0.045 * H), (x + 0.86 * L, y + 0.13 * H),
                  (x + 0.70 * L, y + 0.24 * H), (x + 0.52 * L, y + 0.31 * H),
                  (x + 0.34 * L, y + 0.30 * H), (x + 0.18 * L, y + 0.24 * H),
                  (x + 0.07 * L, y + 0.14 * H), (x, y + 0.06 * H)]
        ctrl_b = [(px, py + ayun * (max(0.0, (px - x) / L) ** 2.2)) for px, py in ctrl_b]
        bawah_h = [(px, py) for px, py in spline(ctrl_b, 70)]
        atas_p = [(px, py - H * (0.048 + 0.062 * math.sin(math.pi * clamp((px - x) / L))))
                  for px, py in bawah_h]
        potong = [(bb, bp, ap) for bb, bp, ap in zip(bawah_h, bawah_h, atas_p)
                  if 0.085 < clamp((bb[0] - x) / L) < 0.885]
        if len(potong) > 6:
            kanan = [(bp[0], bp[1]) for _, bp, _ in potong]
            kiri = [(ap[0], ap[1]) for _, _, ap in potong]
            bentuk2(img, kanan + kiri[::-1], HIU_PERUT, outline=None, ow=0,
                    alpha=0.92 * alpha, light=0.10, dark=0.03)

    # --- detail wajah & insang
    if insang:
        for i in range(5):
            gx = x + (0.208 + i * 0.0205) * L
            garis2(img, [(gx, y - 0.185 * H + ayun * 0.02), (gx + 0.013 * L, y + 0.045 * H + ayun * 0.02)],
                   mix(INK, tone, 0.30), max(1.6, L * 0.0042), 0.60 * alpha)
    if mulut:
        m = spline([(x + 0.004 * L, y + 0.055 * H), (x + 0.030 * L, y + 0.105 * H),
                    (x + 0.075 * L, y + 0.098 * H), (x + 0.112 * L, y + 0.072 * H)], 20)
        garis2(img, m, mix(INK, tone, 0.12), max(2.0, L * 0.0062), 0.82 * alpha)
    if mata:
        er = max(2.0, L * 0.0090)
        elips2(img, x + 0.088 * L, y - 0.055 * H, er, er, WHITE,
               outline=mix(INK, tone, 0.2), ow=2.0, alpha=alpha, light=0.0, dark=0.0)
        dot_on(img, x + 0.090 * L, y - 0.055 * H, er * 0.55, INK, 0.92 * alpha)


def paus_t(img, x, y, panjang, tinggi=0.20, tone=None, outline=None, t=0.0, alpha=1.0,
           ekor_atas=0.0):
    """Paus beroutline (untuk skala & migrasi)."""
    L, H = float(panjang), float(panjang) * float(tinggi)
    tone = tone or mix(HIU, TEAL, 0.35)
    outline = outline or mix(INK, NAVY_D, 0.3)
    ayun = math.sin(t * 1.2 + ekor_atas) * 0.05 * L
    atas = spline([(x, y), (x + 0.06 * L, y - 0.24 * H), (x + 0.20 * L, y - 0.38 * H),
                   (x + 0.40 * L, y - 0.34 * H), (x + 0.62 * L, y - 0.22 * H),
                   (x + 0.85 * L, y - 0.10 * H), (x + 0.95 * L, y)], 22)
    bawah = spline([(x + 0.95 * L, y), (x + 0.84 * L, y + 0.20 * H), (x + 0.62 * L, y + 0.32 * H),
                    (x + 0.40 * L, y + 0.34 * H), (x + 0.18 * L, y + 0.28 * H),
                    (x + 0.05 * L, y + 0.14 * H), (x, y)], 22)
    atas = [(px, py + ayun * (max(0.0, (px - x) / L) ** 3)) for px, py in atas]
    bawah = [(px, py + ayun * (max(0.0, (px - x) / L) ** 3)) for px, py in bawah]
    ekor = spline([(x + 0.95 * L, y + ayun - 0.05 * H), (x + 1.06 * L, y + ayun - 0.42 * H),
                   (x + 1.02 * L, y + ayun), (x + 1.07 * L, y + ayun + 0.30 * H),
                   (x + 0.95 * L, y + ayun + 0.05 * H)], 16)
    bentuk2(img, ekor, mix(tone, INK, 0.08), outline=outline, ow=2.6, alpha=alpha,
            light=0.14, dark=0.20)
    bentuk2(img, atas + bawah, tone, outline=outline, ow=3.2, alpha=alpha, light=0.26, dark=0.16)
    # perut krem
    pita = [(px, py - (py - y) * 0.34) for px, py in bawah[2:len(bawah) - 2]]
    if len(pita) >= 3:
        bentuk2(img, [(px, py - 0.03 * H) for px, py in bawah[2:len(bawah) - 2]] + pita[::-1],
                HIU_PERUT, outline=None, ow=0, alpha=0.85 * alpha, light=0.12, dark=0.05)
    # sirip dada kecil + mata
    fin = spline([(x + 0.24 * L, y + 0.24 * H), (x + 0.30 * L, y + 0.46 * H),
                  (x + 0.36 * L, y + 0.22 * H)], 8)
    bentuk2(img, fin, mix(tone, INK, 0.12), outline=outline, ow=2.4, alpha=alpha, light=0.16)
    dot_on(img, x + 0.075 * L, y + 0.03 * H, max(1.6, L * 0.010), INK, 0.85 * alpha)
    garis2(img, [(x + 0.008 * L, y + 0.10 * H), (x + 0.05 * L, y + 0.13 * H),
                 (x + 0.09 * L, y + 0.10 * H)], mix(INK, tone, 0.2), 2.2, 0.5 * alpha)


def penyelam_t(img, x, y, tinggi=1.8, skala=54, tone=None, t=0.0, alpha=1.0):
    """Penyelam 1,8 m: siluet beroutline + tabung oksigen + gelembung."""
    tone = tone or mix(NAVY, TEAL_D, 0.35)
    outline = mix(INK, NAVY_D, 0.3)
    hh = tinggi * skala
    hp = hh * 0.16                                    # tinggi kepala
    cy = y - hh + hp * 0.5
    elips2(img, x, cy, hp * 0.62, hp * 0.62, mix(tone, WHITE, 0.18), outline=outline,
           ow=2.4, alpha=alpha)
    # badan
    bentuk2(img, [(x - hp * 0.55, y - hh + hp * 1.05), (x + hp * 0.55, y - hh + hp * 1.05),
                  (x + hp * 0.42, y - hh * 0.34), (x - hp * 0.42, y - hh * 0.34)],
            tone, outline=outline, ow=2.6, alpha=alpha, light=0.18, dark=0.16)
    # tabung
    bentuk2(img, [(x + hp * 0.48, y - hh + hp * 0.9), (x + hp * 0.95, y - hh + hp * 0.9),
                  (x + hp * 0.95, y - hh * 0.5), (x + hp * 0.48, y - hh * 0.5)],
            mix(TERRA, AMBER_H, 0.30), outline=outline, ow=2.2, alpha=alpha, light=0.24)
    # kaki
    for s in (-1, 1):
        garis2(img, [(x + s * hp * 0.28, y - hh * 0.34), (x + s * hp * 0.34, y - hh * 0.06),
                     (x + s * hp * 0.52, y - hh * 0.02)], tone, hp * 0.30, 0.95 * alpha)
    # lengan
    garis2(img, [(x - hp * 0.5, y - hh + hp * 1.2), (x - hp * 1.0, y - hh + hp * 1.9)],
           tone, hp * 0.26, 0.95 * alpha)
    # gelembung
    for i in range(3):
        u = (t * 0.35 + i * 0.33) % 1.0
        gelembung_t(img, x + hp * 0.75 + 6 * math.sin(t + i), cy - hp * 0.8 - u * hh * 0.5,
                    2.6 + 1.8 * (1 - u), 0.5 * alpha)


def gigi_t(img, x, y, tinggi, rot=0.0, tone=None, alpha=1.0, gerigi=True,
           outline=None, lebar_r=0.74, akar=True):
    """Gigi megalodon: mahkota LEBAR (lebar 0,74 x tinggi), tepi bergerigi,
    akar V bercabang yang selalu kelihatan di bawah gusi.

    Catatan desain: gigi sempit dan tegak selalu terbaca "layar kapal" pada
    ilustrasi. Yang membuatnya terbaca gigi adalah (a) mahkota lebar, (b) akar V
    terlihat, (c) gigi dimiringkan 10-30 derajat, bukan berdiri tegak.
    """
    h = float(tinggi)
    w = h * float(lebar_r)
    tone = tone or mix(CREAM, PASIR, 0.06)
    outline = outline or mix(INK, TERRA_D, 0.42)
    ca, sa = math.cos(rot), math.sin(rot)

    def T(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)

    # --- akar (V bercabang, terlihat di bawah garis gusi)
    if akar:
        r = spline([T(-w * 0.40, 0.0), T(-w * 0.44, h * 0.10), T(-w * 0.26, h * 0.12),
                    T(-w * 0.10, h * 0.055), T(0.0, h * 0.10), T(w * 0.10, h * 0.055),
                    T(w * 0.26, h * 0.12), T(w * 0.44, h * 0.10), T(w * 0.40, 0.0)], 10)
        bentuk2(img, r, mix(TERRA, TERRA_D, 0.34), outline=outline, ow=2.2,
               alpha=alpha, light=0.16, dark=0.22)

    # --- mahkota: tepi cembung keluar, ujung membulat-tajam, takik 7 pasang
    kiri, kanan = [], []
    N = 7
    takik = h * 0.020 if gerigi else 0.0
    for i in range(N + 1):
        u = i / N
        setengah = (w * 0.5) * (1.0 - u ** 1.75)          # cembung: lebar bertahan
        ser = takik if (gerigi and i % 2 == 1 and 0.10 < u < 0.92) else 0.0
        geser = -w * (0.055 * u ** 2)
        kiri.append(T(geser - setengah + ser, -u * h))
        kanan.append(T(geser + setengah - ser, -u * h))
    bentuk2(img, kiri + kanan[::-1], tone, outline=outline, ow=2.4, alpha=alpha,
            light=0.26, dark=0.16)
    # garis gusi (tegas di pangkal) + kilau
    if alpha > 0.4:
        garis2(img, [kiri[0], kanan[0]], mix(TERRA_D, INK, 0.30), max(2.0, h * 0.035), 0.55 * alpha)
        gl = [(px, py) for px, py in kiri[1:N - 1]]
        garis2(img, [(px + w * 0.10, py) for px, py in gl],
                 mix(WHITE, tone, 0.42), max(2.0, w * 0.075), 0.40 * alpha)


def rahang_terbuka(img, x, y, skala=1.0, buka=0.4, al=1.0, gigi_n=8):
    """Kepala megalodon dengan mulut menganga: rahang atas + rahang bawah terpisah.

    Versi balok + busur gigi menghasilkan kotak gelap (bukan kepala). Di sini
    rahang atas dan bawah adalah dua bentuk terpisah dengan rongga gelap di
    antaranya — cara ilustrasi klasik menggambar maw.
    """
    S_ = skala
    tone = mix(HIU, TEAL_D, 0.22)
    outline = mix(INK, NAVY_D, 0.35)
    # --- rahang atas: baji dari kiri, moncong di kanan
    atas = (spline([(x - 210 * S_, y - 120 * S_), (x - 40 * S_, y - 132 * S_),
                    (x + 110 * S_, y - 104 * S_), (x + 214 * S_, y - 44 * S_)], 12) +
            spline([(x + 214 * S_, y - 44 * S_), (x + 150 * S_, y + 26 * S_),
                    (x + 20 * S_, y + 44 * S_), (x - 210 * S_, y + 30 * S_)], 12))
    bentuk2(img, atas, tone, outline=outline, ow=3.6, alpha=al, light=0.24, dark=0.18)
    # --- rahang bawah: turun sesuai `buka`
    drop = (150 + 190 * clamp(buka)) * S_
    bawah = (spline([(x - 210 * S_, y + 40 * S_), (x + 10 * S_, y + 52 * S_),
                     (x + 158 * S_, y + 60 * S_), (x + 196 * S_, y + 40 * S_ + drop * 0.55)], 12) +
             spline([(x + 196 * S_, y + 40 * S_ + drop * 0.55), (x + 120 * S_, y + 66 * S_ + drop),
                     (x - 20 * S_, y + 74 * S_ + drop), (x - 210 * S_, y + 52 * S_ + drop)], 12))
    bentuk2(img, bawah, mix(tone, INK, 0.10), outline=outline, ow=3.4, alpha=al,
            light=0.20, dark=0.20)
    # --- rongga mulut (gelap) di antara kedua rahang
    rongga = [(x - 200 * S_, y + 24 * S_), (x + 12 * S_, y + 44 * S_), (x + 150 * S_, y + 24 * S_),
              (x + 120 * S_, y + 62 * S_ + drop), (x - 20 * S_, y + 70 * S_ + drop),
              (x - 200 * S_, y + 48 * S_ + drop)]
    bentuk2(img, rongga, mix(DARAH, INK, 0.55), outline=None, ow=0, alpha=al,
            light=0.05, dark=0.30)
    # --- gigi atas (menggantung ke bawah) & bawah (menunjuk ke atas)
    for baris in (0, 1):
        for i in range(gigi_n):
            u = 0.10 + 0.80 * i / max(1, gigi_n - 1)
            gx = x - 168 * S_ + 330 * S_ * u
            depan = 1.0 - abs(u - 0.55) * 1.4
            hh = (34 + 46 * max(0.0, depan)) * S_
            if baris == 0:
                gy = y + 40 * S_ + 6 * S_
                gigi_t(img, gx, gy, hh, rot=math.pi + (u - 0.5) * 0.30, alpha=al,
                       lebar_r=0.66, tone=mix(CREAM, PASIR, 0.06 + 0.14 * abs(u - 0.5)))
            else:
                gy = y + 66 * S_ + drop - 6 * S_
                gigi_t(img, gx, gy, hh * 0.92, rot=(u - 0.5) * 0.30, alpha=al,
                       lebar_r=0.66, tone=mix(CREAM, PASIR, 0.10 + 0.14 * abs(u - 0.5)))
    # --- gusi
    garis2(img, [(x - 196 * S_, y + 34 * S_), (x + 8 * S_, y + 46 * S_), (x + 158 * S_, y + 30 * S_)],
             mix(TERRA, TERRA_D, 0.30), 12 * S_, 0.95 * al)
    garis2(img, [(x - 196 * S_, y + 56 * S_ + drop), (x - 6 * S_, y + 70 * S_ + drop),
                   (x + 160 * S_, y + 56 * S_ + drop)],
             mix(TERRA, TERRA_D, 0.34), 11 * S_, 0.92 * al)
    # --- mata + insang pada rahang atas
    elips2(img, x - 96 * S_, y - 74 * S_, 11 * S_, 11 * S_, WHITE,
           outline=outline, ow=2.2, alpha=al, light=0.0, dark=0.0)
    dot_on(img, x - 94 * S_, y - 74 * S_, 5.0 * S_, INK, 0.9 * al)
    for i in range(4):
        gx = x - 150 * S_ + i * 26 * S_
        garis2(img, [(gx, y - 44 * S_), (gx + 10 * S_, y - 4 * S_)],
                 mix(INK, tone, 0.35), 2.6 * S_, 0.40 * al)


def lempeng_fosil(img, cx, cy, w, h, gigi=(), tone=None, al=1.0, label=None):
    """Lempeng batu fosil (cream beroutline) dengan gigi KECIL yang tertanam.

    Pelajaran penting: gigi besar yang berdiri sendiri selalu terbaca "layar
    kapal". Gigi harus (a) kecil relatif terhadap lempeng, (b) rapat, (c) akarnya
    masuk ke lempeng, (d) dimiringkan. Untuk menunjukkan detail gerigi dipakai
    kaca pembesar (inset), bukan memperbesar giginya.
    """
    tone = tone or mix(CREAM, PASIR, 0.22)
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    # lempeng: poligon bersudut tumpul (bukan persegi)
    bentuk2(img, [(x0 + 18, y0), (x1 - 26, y0 + 6), (x1, y0 + h * 0.34), (x1 - 10, y1 - 8),
                  (x0 + 24, y1), (x0 - 4, y1 - h * 0.42), (x0 - 2, y0 + h * 0.22)],
            tone, outline=mix(INK, NAVY_D, 0.42), ow=3.0, alpha=al, light=0.18, dark=0.10)
    # lapisan sedimen
    for i in range(3):
        yy = y0 + h * (0.30 + i * 0.22)
        garis2(img, [(x0 + 26, yy), (x1 - 22, yy - 3)], mix(tone, INK, 0.22), 2.0, 0.30 * al)
    # gigi: akar masuk lempeng, mahkota menonjol ke atas
    for (gx, gy, hh, rot) in gigi:
        gigi_t(img, gx, gy, hh, rot=rot, alpha=al, lebar_r=0.52,
               tone=mix(CREAM, WHITE, 0.30), gerigi=True)
    if label:
        label2(img, cx, y1 + 44, label, fsz=21, tone=mix(NAVY, INK, 0.12),
               bg=mix(BUIH, CREAM, 0.30), al=al)


def inset_kaca(img, cx, cy, r, isi, al=1.0, ring_tone=None):
    """Kaca pembesar: gambar isi di kanvas kecil lalu di-clip bulat.

    `isi(lay, R)` menggambar pada layar persegi berukuran 2R (piksel layar).
    """
    R = int(round(S(r)))
    if R < 8:
        return
    lay = Image.new("RGB", (2 * R, 2 * R), mix(CREAM, WHITE, 0.45))
    isi(lay, R)
    mask = Image.new("L", (2 * R, 2 * R), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=255)
    if al < 0.999:
        mask = mask.point(lambda v: int(v * al))
    img.paste(lay, (int(round(S(cx - r))), int(round(S(cy - r)))), mask)
    ring_on(img, cx, cy, r, ring_tone or mix(INK, NAVY_D, 0.40), 5.0, 0.92 * al)
    ring_on(img, cx, cy, r + 8, mix(BUIH, WHITE, 0.5), 2.4, 0.40 * al)


def baris_gigi_t(img, cx, cy, lebar, tinggi, buka=0.0, n=9, al=1.0):
    """Mulut menganga: rongga coklat tua, gusi terakota, gigi krem beroutline."""
    rx, ry = lebar * 0.5, tinggi * 0.5
    turun_b = ry * (1.02 + 1.15 * clamp(buka))
    atas = V16._busur_gigi(cx, cy, rx, ry, 0.0, 26)
    bawah = V16._busur_gigi(cx, cy, rx, ry, turun_b, 26)
    bentuk2(img, atas + list(reversed(bawah)), mix(DARAH, INK, 0.42), outline=mix(INK, DARAH, 0.3),
            ow=3.0, alpha=al, light=0.10, dark=0.28)
    garis2(img, atas, mix(TERRA, TERRA_D, 0.35), max(10, lebar * 0.032), 0.96 * al)
    garis2(img, bawah, mix(TERRA, TERRA_D, 0.30), max(9, lebar * 0.028), 0.94 * al)
    for baris, (turun, arah) in enumerate(((0.0, 1), (turun_b, -1))):
        for i in range(n):
            u = 0.055 + (i + 0.5) / n * 0.89
            gx, gy = V16._y_busur(cx, cy, rx, ry, turun, u)
            depan = 1.0 - abs(u - 0.5) * 2
            pjg = ry * (0.30 + 0.26 * depan)
            sudut = (u - 0.5) * 0.55
            rot = (math.pi + sudut) if arah > 0 else sudut
            gigi_t(img, gx, gy + (3 if arah > 0 else -3), pjg, rot=rot, alpha=al,
                   tone=mix(CREAM, PASIR, 0.05 + 0.22 * abs(u - 0.5)), gerigi=False)


# ---------------------------------------------------------------- angka & tanda
def kurung_ukur(img, x0, x1, y, label=None, tone=None, al=1.0, fsz=21, bawah_label=True,
                ujung=16.0, w=3.2):
    """Garis ukur beroutline + ujung tegak + label kapsul (dipakai di semua skala)."""
    tone = tone or mix(TERRA, TERRA_D, 0.25)
    garis2(img, [(x0, y), (x1, y)], tone, w, 0.95 * al)
    for xx in (x0, x1):
        line_on(img, (xx, y - ujung), (xx, y + ujung), tone, w, 0.95 * al)
    if label:
        label2(img, (x0 + x1) / 2, y + (66 if bawah_label else -66), label, fsz=fsz,
               tone=mix(NAVY, INK, 0.15), bg=mix(BUIH, CREAM, 0.35), al=al)


def panah(img, x0, y0, x1, y1, tone=None, w=4.0, al=1.0, kepala=18.0):
    tone = tone or mix(TERRA, TERRA_D, 0.2)
    a = math.atan2(y1 - y0, x1 - x0)
    garis2(img, [(x0, y0), (x1, y1)], tone, w, 0.95 * al)
    bentuk2(img, [(x1, y1),
                  (x1 - kepala * math.cos(a - 0.42), y1 - kepala * math.sin(a - 0.42)),
                  (x1 - kepala * math.cos(a + 0.42), y1 - kepala * math.sin(a + 0.42))],
            tone, outline=None, ow=0, alpha=0.95 * al, light=0.1, dark=0.05)


# ---------------------------------------------------------------- selftest
def _contoh():
    D.SS = 1.0
    im = Image.new("RGB", (1080, 1920), KERTAS)
    langit(im)
    matahari(im, 866, 146, 58)
    awan_kecil(im, 250, 168, 190, 34, seed=2)
    air_t(im, 0.0)
    sinar_t(im, 0.6)
    permukaan(im, SURF, 0.4)
    hiu_t(im, 110, 760, 860, tinggi=0.150, t=0.5, bayang=0.8)
    dasar_pasir(im, 1770)
    gigi_t(im, 300, 1160, 230, rot=0.14)
    kartu2(im, ["HIU 24 METER", "YANG TERSISA CUMA GIGI"], hl="CUMA GIGI", y=1478, fsz=62,
           tab=TERRA, kicker="LAUT PURBA · GIGI SEBESAR TELAPAK TANGAN")
    V16.sumber(im, "Sumber: Shimada dkk. 2025 · NHM · Nature Comm. 2022")
    im.save("build/uji_v17.png")
    print("ok -> build/uji_v17.png")


if __name__ == "__main__":
    import os
    os.makedirs("build", exist_ok=True)
    _contoh()
