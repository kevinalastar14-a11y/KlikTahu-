#!/usr/bin/env python3
"""mesin_v17_ep55.py — Ep55 "Megalodon Bukan Hiu Putih Raksasa — Dan Kita Cuma Punya Giginya"

Mesin v17 LAUT TERANG: delapan dunia yang SEMUANYA memakai bahasa visual KlikTahu
(kertas krem, permukaan bergelombang, air teal muda, outline tinta, perut krem,
seabed pasir berkerikil). Ini pengganti mesin v16 "LAUT DALAM" yang gelap.

Timing TIDAK berubah: cue kata, SFX, dan durasi scene sama persis dengan v16,
sehingga audio master (VO + ambient) tidak perlu dibuat ulang.

Dunia:
  1 t17_intro   : hiu raksasa + garis 24,3 m + gigi di dasar — hook
  2 t17_waktu   : pita waktu 20 jtl -> 3,6 jtl, gigi fosil di sepanjang pita
  3 t17_ukur    : satu tubuh utuh, kurung 1,8 / 11 / 3,6 m, penyelam 1,8 m
  4 t17_bentuk  : dua hiu panjang sama, tinggi badan berbeda
  5 t17_gigi    : potongan rahang 5 gigi + penggaris 18 cm + gigi lepas
  6 t17_gigit   : mulut menganga + paus kecil + bekas luka di ekor
  7 t17_punah   : laut mendingin, rak dangkal menyempit, paus migrasi
  8 t17_loop    : kembali ke komposisi frame 0 (gigi + hiu jauh)

Selftest:  python3 mesin_v17_ep55.py
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import diagrams as D
import mesin_v11 as M11
import mesin_v12 as M
import mesin_v15_ilustrasi as V15
import mesin_v17_terang as T
from diagrams import (INK, CREAM, WHITE, MUTED, mix, clamp, seg, eo, font, tw, tlh,
                      paste_c, rrect_on, line_on, dot_on, ring_on, S)
from mesin_v15_ilustrasi import (KERTAS, KREM, LANGIT, LANGIT_2, SENJA, TEAL, TEAL_D,
                                 PASIR, PASIR_D, TERRA, TERRA_D, OLIVE, OLIVE_D,
                                 NAVY, NAVY_D, AMBER_H, kurva)

SUMBER = "Sumber: Shimada dkk. 2025 · NHM · Nature Comm. 2022"
SUMBER_GIGI = "Sumber: Shimada dkk. 2025 · Palaeontologia Electronica"
SUMBER_PUNAH = "Sumber: NHM · Nature Communications 2022 · PeerJ 2019"
Y_KARTU = 1478

# ------------------------------------------------------------------ cache dunia
_BASE = {}
_CACHE_DIR = os.path.join(os.environ.get("KT_BUILD", "build"), "v17base")


def _base(nama, builder):
    """Bangun latar dunia sekali, simpan ke disk, pakai ulang lintas proses render.

    Kenapa di-cache: latar (langit, seabed, ratusan butir pasir, rumput) mahal dan
    tidak berubah antar-frame. Hanya lapisan gerak yang digambar ulang per frame.
    """
    key = (nama, round(D.SS, 6))
    im = _BASE.get(key)
    if im is not None:
        return im
    path = os.path.join(_CACHE_DIR, f"{nama}_{int(round(D.SS * 1000))}.png")
    if os.path.exists(path):
        try:
            im = Image.open(path).convert("RGB")
            im.load()
            _BASE[key] = im
            return im
        except Exception:
            pass
    im = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), T.AIR_3)
    builder(im)
    _BASE[key] = im
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        im.save(path)
    except Exception:
        pass
    return im


# ------------------------------------------------------------------ lapisan umum
def _langit_air(im, seed=1, matahari_x=868, matahari_y=150, awan=(250, 172), t=0.0,
                atas=None, bawah=None):
    """Langit + matahari + awan + air + sinar + permukaan. Dipakai SEMUA dunia."""
    T.langit(im, 0, T.SURF, seed=seed)
    if awan:
        T.awan_kecil(im, awan[0], awan[1], 196, 36, seed=seed + 3)
        T.awan_kecil(im, awan[0] + 240, awan[1] + 26, 132, 24, seed=seed + 5)
    if matahari_x:
        T.matahari(im, matahari_x, matahari_y, 56, t=t)
    T.air_t(im, t, atas=atas or T.AIR_1, bawah=bawah or T.AIR_5, seed=seed + 7)
    T.sinar_t(im, t, n=4, seed=seed + 11)
    T.permukaan(im, T.SURF, t, amp=9)


def _ikan_kecil(img, x, y, L, tone=None, ekor=1.0, al=1.0):
    """Ikan kecil pengisi ruang (beroutline, 3 detik selesai digambar)."""
    tone = tone or mix(TEAL, TEAL_D, 0.35)
    bentuk2 = T.bentuk2
    bentuk2(img, [(x, y), (x + 0.30 * L, y - 0.16 * L), (x + 0.62 * L, y - 0.10 * L),
                  (x + 0.62 * L, y + 0.10 * L), (x + 0.30 * L, y + 0.16 * L)],
            tone, outline=mix(INK, NAVY_D, 0.35), ow=2.4, alpha=al, light=0.26)
    bentuk2(img, [(x + 0.60 * L, y), (x + 0.86 * L * ekor, y - 0.20 * L),
                  (x + 0.80 * L * ekor, y), (x + 0.86 * L * ekor, y + 0.20 * L)],
            mix(tone, INK, 0.12), outline=mix(INK, NAVY_D, 0.35), ow=2.2, alpha=al)
    dot_on(img, x + 0.20 * L, y - 0.02 * L, max(1.4, L * 0.026), INK, 0.85 * al)


def _rumput(img, x, y, h, n=3, tone=None, t=0.0, ayun=0.0):
    """Rumpun rumput laut: 3 helai melengkung beroutline."""
    tone = tone or mix(OLIVE, OLIVE_D, 0.30)
    for k in range(n):
        bx = x + (k - (n - 1) / 2) * 15
        sway = ayun * math.sin(t * 1.2 + k)
        pts = kurva((bx, y), (bx + 14 * (k - (n - 1) / 2) + 3, y - h * 0.55),
                    (bx + 30 * (k - (n - 1) / 2) + sway, y - h), 14)
        T.garis2(img, pts, mix(tone, INK, 0.10 + 0.10 * k), 6.0, 0.95)


def _lempeng_fosil(img, cx, cy, rx, ry, gigi=(), seed=1, tone=None):
    """Lempeng fosil di dasar laut: gusi terakota + gigi yang benar-benar ditanam.

    Versi pertama memakai batu bulat + gigi tegak -> terbaca "perahu layar" karena
    akar gigi tertutup batu. Di sini gusi digambar sebagai pita, akar gigi
    MENONJOL di atas gusi, dan lempengnya rata (bukan gundukan).
    """
    tone = tone or mix(T.PASIR_TD, TEAL, 0.22)
    # lempeng: poligon rata dengan sudut membulat
    T.bentuk2(img, [(cx - rx, cy + ry * 0.15), (cx - rx * 0.55, cy - ry),
                    (cx + rx * 0.60, cy - ry * 0.92), (cx + rx, cy + ry * 0.22),
                    (cx + rx * 0.62, cy + ry * 0.62), (cx - rx * 0.58, cy + ry * 0.58)],
              tone, outline=mix(INK, NAVY_D, 0.42), ow=3.0, light=0.18, dark=0.10)
    # lapisan sedimen
    for i in range(3):
        yy = cy - ry * 0.30 + i * ry * 0.34
        T.garis2(img, [(cx - rx * 0.7, yy), (cx + rx * 0.7, yy - 3)],
                 mix(tone, INK, 0.18), 2.2, 0.35)
    # gusi
    if gigi:
        gx0 = min(g[0] for g in gigi) - 30
        gx1 = max(g[0] for g in gigi) + 30
        T.bentuk2(img, [(gx0, cy - ry * 0.10), (gx1, cy - ry * 0.14),
                        (gx1, cy + ry * 0.22), (gx0, cy + ry * 0.26)],
                  mix(TERRA, TERRA_D, 0.35), outline=mix(INK, NAVY_D, 0.40), ow=2.6,
                  light=0.22, dark=0.16)
        for (gx, gy, hh, rot) in gigi:
            T.gigi_t(img, gx, gy, hh, rot=rot, lebar_r=0.50,
                     tone=mix(CREAM, PASIR, 0.06 + 0.10 * abs(rot)))


def _batu(img, cx, cy, rx, ry, tone=None, seed=1):
    """Bongkahan batu beroutline (untuk menaruh gigi fosil)."""
    tone = tone or mix(T.PASIR_TD, TEAL, 0.28)
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(9):
        a = 2 * math.pi * i / 9
        rr = 0.86 + 0.28 * rng.random()
        pts.append((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)))
    T.bentuk2(img, pts, tone, outline=mix(INK, NAVY_D, 0.40), ow=3.0, light=0.22, dark=0.12)


# ------------------------------------------------------------------ 1 · HOOK
def _dunia_intro(im):
    _langit_air(im, seed=51, t=0.0)
    # hiu utama: bahasa KlikTahu (perut krem, outline tinta), bukan siluet
    T.hiu_t(im, 96, 700, 880, tinggi=0.152, t=0.0, bayang=1.0, sirip=1.05)
    T.dasar_pasir(im, 1780, seed=52)
    # BAKI FOSIL: alas gelap ala lemari museum -> gigi krem terbaca gigi, bukan layar
    T.bentuk2(im, [(112, 1132), (466, 1124), (480, 1190), (120, 1198)],
              mix(T.HIU, TEAL_D, 0.42), outline=mix(INK, NAVY_D, 0.45), ow=3.2,
              light=0.14, dark=0.12)
    T.garis2(im, [(130, 1162), (466, 1154)], mix(T.HIU, INK, 0.35), 2.2, 0.45)
    # gigi TEGAK, kecil, rapat, di atas busur rahang (rotasi besar -> terbaca panah)
    for (gx, gy, hh, rt) in ((186, 1144, 78, -0.26), (238, 1136, 94, -0.14), (292, 1132, 104, 0.0),
                             (346, 1136, 92, 0.14), (398, 1144, 76, 0.26)):
        T.gigi_t(im, gx, gy, hh, rot=rt, lebar_r=0.56, tone=mix(CREAM, PASIR, 0.02))
    _rumput(im, 60, 1770, 130, t=0.0)
    _rumput(im, 1020, 1770, 120, t=0.0)
    _ikan_kecil(im, 700, 430, 74, al=0.55)
    _ikan_kecil(im, 790, 388, 58, al=0.45)


def sc_intro(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("intro17", _dunia_intro), (0, 0))
    # garis ukur 24,3 m tumbuh di bawah siluet
    p = eo(seg(tl, 0.25, 1.5))
    if p > 0.01:
        y = 906
        x1 = 96 + 880 * p
        T.garis2(img, [(96, y), (x1, y)], mix(TERRA, TERRA_D, 0.25), 3.6, 0.92 * al)
        line_on(img, (96, y - 15), (96, y + 15), mix(TERRA, TERRA_D, 0.25), 3.6, 0.92 * al)
        if p > 0.96:
            line_on(img, (976, y - 15), (976, y + 15), mix(TERRA, TERRA_D, 0.25), 3.6, 0.92 * al)
            T.label2(img, 540, y + 52, "24,3 METER · BATAS ATAS", fsz=23,
                     tone=mix(NAVY, INK, 0.12), bg=mix(T.BUIH, CREAM, 0.35), al=al)
    # gelembung dari moncong hiu
    T.gelembung_naik(img, tl, 150, 250, 560, 700, n=4, seed=4, skala=0.8)
    # sorot lembut pada gigi fosil
    q = 0.5 + 0.5 * math.sin(tl * 1.6)
    ring_on(img, 286, 1092, 128 + 7 * q, mix(AMBER_H, WHITE, 0.35), 2.2, 0.10 + 0.10 * q)
    T.kartu2(img, ["HIU 24 METER", "YANG TERSISA CUMA GIGI"], hl="CUMA GIGI", y=Y_KARTU, fsz=62,
             al=al, dy=dy, tab=accent, kicker="LAUT PURBA · GIGI SEBESAR TELAPAK TANGAN")
    T.sumber(img, SUMBER, al=al)


# ------------------------------------------------------------------ 2 · WAKTU
def _dunia_waktu(im):
    _langit_air(im, seed=52, t=0.0, matahari_x=870, matahari_y=146,
                awan=(210, 168), atas=T.AIR_1, bawah=mix(T.AIR_4, T.AIR_5, 0.35))
    # pita waktu: kartu krem beroutline (bahasa KlikTahu)
    y = 772
    T.bentuk2(im, [(64, y - 62), (1016, y - 62), (1016, y + 62), (64, y + 62)],
              mix(CREAM, KREM, 0.25), outline=mix(INK, NAVY_D, 0.35), ow=3.4,
              light=0.20, dark=0.06)
    xa, xb = 132, 946
    for i in range(45):
        xx = xa + (xb - xa) * i / 44
        line_on(im, (xx, y + 62), (xx, y + 62 - (16 if i % 5 else 26)),
                mix(INK, PASIR_D, 0.40), 2.0, 0.35)
    line_on(im, (xa, y + 8), (xb, y + 8), mix(INK, TEAL_D, 0.55), 3.0, 0.55)
    # gigi fosil berdiri di sepanjang pita
    rng = np.random.default_rng(5)
    for i in range(9):
        u = 0.05 + 0.90 * (i / 8.0) + (rng.random() - 0.5) * 0.03
        xx = xa + (xb - xa) * u
        hh = 62 + 26 * rng.random()
        T.gigi_t(im, xx, y + 6, hh, rot=(rng.random() - 0.5) * 0.22, gerigi=False,
                 tone=mix(CREAM, PASIR, 0.10 + 0.18 * rng.random()))
    # dua hiu kecil di atas pita
    T.hiu_t(im, 120, 548, 330, tinggi=0.150, t=0.0, insang=False, mulut=False, sirip=0.9)
    T.hiu_t(im, 640, 570, 236, tinggi=0.168, t=0.3, insang=False, mulut=False,
            ekor_bulan=False, tone=T.HIU_2)
    T.label2(im, 214, y + 150, "20 JUTA TAHUN LALU", fsz=22, tone=mix(NAVY, INK, 0.12),
             bg=mix(T.BUIH, CREAM, 0.30))
    T.label2(im, 862, y + 150, "3,6 JUTA TAHUN LALU", fsz=22, tone=mix(NAVY, INK, 0.12),
             bg=mix(T.BUIH, CREAM, 0.30))
    T.dasar_pasir(im, 1800, seed=53, amp=14)
    _rumput(im, 990, 1800, 110)
    _ikan_kecil(im, 760, 1130, 62, al=0.40)


def sc_waktu(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("waktu17", _dunia_waktu), (0, 0))
    p = eo(seg(tl, 0.35, 2.3))
    xa, xb, y = 132, 946, 772
    x = xa + (xb - xa) * p
    line_on(img, (x, y - 74), (x, y + 74), mix(TERRA, TERRA_D, 0.30), 3.4, 0.80 * al)
    dot_on(img, x, y + 8, 8, mix(AMBER_H, WHITE, 0.30), 0.95 * al,
           outline=mix(TERRA_D, INK, 0.3), width=2.2)
    ring_on(img, x, y + 8, 20 + 4 * math.sin(tl * 3.0), mix(AMBER_H, WHITE, 0.30), 2.2, 0.40 * al)
    # kilau bergiliran di gigi fosil
    for i in range(5):
        gx = 148 + i * 190
        ring_on(img, gx, y - 30, 34, mix(AMBER_H, WHITE, 0.55), 1.8,
                0.10 + 0.14 * (0.5 + 0.5 * math.sin(tl * 2.1 + i * 1.1)))
    T.label2(img, 996, y - 108, "KINI", fsz=21, tone=mix(NAVY, INK, 0.12),
             bg=mix(TERRA, AMBER_H, 0.42), al=al)
    T.gelembung_naik(img, tl, 300, 780, 1100, 1500, n=5, seed=8, skala=0.9)
    T.kartu2(img, ["HIDUP 20 JUTA TAHUN,", "HILANG 3,6 JUTA TAHUN LALU"], hl="3,6 JUTA TAHUN LALU",
             y=Y_KARTU, fsz=55, al=al, dy=dy, tab=accent, kicker="TULANG RAWAN TIDAK MENJADI FOSIL")
    T.sumber(img, SUMBER_GIGI, al=al)


# ------------------------------------------------------------------ 3 · UKUR
def _dunia_ukur(im):
    _langit_air(im, seed=54, t=0.0, atas=mix(T.AIR_1, T.AIR_2, 0.35),
                bawah=mix(T.AIR_4, T.AIR_5, 0.45))
    # satu tubuh utuh: 16,4 m individu Belgia (900 px)
    T.hiu_t(im, 92, 760, 900, tinggi=0.148, t=0.0, sirip=0.95, bayang=0.9)
    # batas bagian: garis putus-putus vertikal
    k = 900 / 16.4
    xs = [92, 92 + 1.8 * k, 92 + 12.8 * k, 992]
    for xx in xs[1:3]:
        for yy in range(620, 940, 24):
            line_on(im, (xx, yy), (xx, yy + 12), mix(TERRA_D, INK, 0.30), 2.4, 0.55)
    # kurung bagian di bawah tubuh
    yb = 1000
    for (b0, b1, txt) in ((xs[0], xs[1], "1,8 m"), (xs[1], xs[2], "11 m tulang belakang"),
                          (xs[2], xs[3], "3,6 m")):
        T.kurung_ukur(im, b0, b1, yb, txt, fsz=21, ujung=13.0, w=3.0)
    # penyelam pembanding 1,8 m
    T.penyelam_t(im, 1000, 1408, 1.8, skala=54, t=0.0)
    T.label2(im, 900, 1262, "PENYELAM 1,8 m", fsz=19, tone=mix(NAVY, INK, 0.12),
             bg=mix(T.BUIH, CREAM, 0.30))
    T.dasar_pasir(im, 1800, seed=55, amp=12)
    _rumput(im, 60, 1800, 120)
    _rumput(im, 1020, 1800, 100)


def sc_ukur(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("ukur17", _dunia_ukur), (0, 0))
    # garis ukur total tumbuh dari kiri
    p = eo(seg(tl, 0.2, 1.5))
    y, x0 = 612, 92
    if p > 0.01:
        x1 = x0 + 900 * p
        T.garis2(img, [(x0, y), (x1, y)], mix(TERRA, TERRA_D, 0.22), 3.8, 0.95 * al)
        line_on(img, (x0, y - 16), (x0, y + 16), mix(TERRA, TERRA_D, 0.22), 3.8, 0.95 * al)
        if p > 0.97:
            line_on(img, (x0 + 900, y - 16), (x0 + 900, y + 16),
                    mix(TERRA, TERRA_D, 0.22), 3.8, 0.95 * al)
            T.label2(img, 540, y - 58, "16,4 METER · INDIVIDU BELGIA", fsz=23,
                     tone=mix(NAVY, INK, 0.12), bg=mix(AMBER_H, WHITE, 0.55), al=al)
    # batas 24,3 m: garis putus-putus (skala sama) muncul kemudian
    q = eo(seg(tl, 1.0, 2.0))
    if q > 0.02:
        x_end = x0 + 900 * (24.3 / 16.4) * q
        xx = x0
        while xx < x_end:
            line_on(img, (xx, 512), (min(xx + 15, x_end), 512), mix(INK, TEAL_D, 0.45), 3.0, 0.50 * al)
            xx += 30
        if q > 0.97:
            T.label2(img, 812, 458, "BATAS 24,3 M · 94 TON", fsz=21, tone=mix(NAVY, INK, 0.12),
                     bg=mix(T.BUIH, CREAM, 0.35), al=al)
    # gelembung dari penyelam
    T.gelembung_naik(img, tl, 940, 1030, 1180, 1380, n=4, seed=6, skala=0.7)
    T.kartu2(img, ["16,4 METER DARI 11 METER", "TULANG BELAKANG"], hl="16,4 METER", y=Y_KARTU,
             fsz=56, al=al, dy=dy, tab=accent, kicker="DIUKUR ULANG 29 AHLI · 2025")
    T.sumber(img, SUMBER, al=al)


# ------------------------------------------------------------------ 4 · BENTUK
def _dunia_bentuk(im):
    _langit_air(im, seed=56, t=0.0, atas=mix(T.AIR_1, T.AIR_2, 0.25),
                bawah=mix(T.AIR_4, T.AIR_5, 0.55))
    # megalodon: panjang 940, badan ramping
    T.hiu_t(im, 70, 588, 940, tinggi=0.150, t=0.0, sirip=0.80, bayang=0.8)
    T.label2(im, 258, 436, "MEGALODON · LEBIH RAMPING", fsz=21, tone=mix(NAVY, INK, 0.12),
             bg=mix(T.BUIH, CREAM, 0.32))
    # hiu putih: panjang sama, badan jauh lebih tebal
    T.hiu_t(im, 70, 1010, 940, tinggi=0.245, t=0.0, sirip=0.85, tone=T.HIU_2, bayang=0.8)
    T.label2(img=im, cx=258, cy=1236, text="HIU PUTIH · GEMPAL", fsz=21,
             tone=mix(NAVY, INK, 0.12), bg=mix(T.BUIH, CREAM, 0.32))
    T.dasar_pasir(im, 1820, seed=57, amp=12)
    _ikan_kecil(im, 900, 740, 56, al=0.35)
    _ikan_kecil(im, 960, 800, 44, al=0.30)


def sc_bentuk(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("bentuk17", _dunia_bentuk), (0, 0))
    # penanda tinggi badan di kanan (dua kurung pendek)
    p = eo(seg(tl, 0.15, 1.1))
    for yy, hh in ((588, 0.150 * 940), (1010, 0.245 * 940)):
        x = 1030
        if p <= 0.02:
            continue
        T.garis2(img, [(x, yy - hh / 2), (x, yy + hh / 2)], mix(TERRA, TERRA_D, 0.25), 3.0, 0.85 * p * al)
        for y2 in (yy - hh / 2, yy + hh / 2):
            line_on(img, (x - 13, y2), (x + 8, y2), mix(TERRA, TERRA_D, 0.25), 3.0, 0.85 * p * al)
    if p > 0.85:
        T.label2(img, 540, 1300, "PANJANG SAMA · BEDA TINGGI BADAN", fsz=21,
                 tone=mix(NAVY, INK, 0.12), bg=mix(AMBER_H, WHITE, 0.45), al=al)
    # kilau bergerak di punggung megalodon
    for i in range(6):
        u = (tl * 0.18 + i / 6.0) % 1.0
        dot_on(img, 84 + 900 * u, 588 - 72, 3.0, mix(T.BUIH, WHITE, 0.5), 0.30 * al)
    T.gelembung_naik(img, tl, 400, 700, 1180, 1500, n=4, seed=9, skala=0.8)
    T.kartu2(img, ["BUKAN HIU PUTIH", "YANG DIPERBESAR"], hl="BUKAN HIU PUTIH", y=Y_KARTU, fsz=62,
             al=al, dy=dy, tab=accent, kicker="TUBUH LEBIH DEKAT KE HIU LEMON")
    T.sumber(img, "Sumber: Shimada dkk. 2025 · Palaeontologia Electronica", al=al)


# ------------------------------------------------------------------ 5 · GIGI
def _dunia_gigi(im):
    _langit_air(im, seed=58, t=0.0, awan=None, atas=mix(T.AIR_2, T.AIR_3, 0.30),
                bawah=mix(T.AIR_4, T.AIR_5, 0.60))
    # lempeng fosil besar (gigi kecil tertanam) di kiri
    T.lempeng_fosil(im, 372, 1268, 468, 176,
                    gigi=((222, 1206, 74, -0.24), (280, 1198, 88, -0.10), (340, 1194, 94, 0.04),
                          (400, 1198, 86, 0.18), (456, 1208, 72, 0.30)),
                    label="GIGI FOSIL · PANJANG 18 CM")
    _batu(im, 812, 1330, 150, 62, seed=13)
    _batu(im, 940, 1298, 96, 42, seed=17)
    # gigi kecil melayang (bukan deret raksasa) untuk kesan "puluhan ribu"
    rng = np.random.default_rng(9)
    for i in range(4):
        x = 676 + rng.random() * 120
        y = 470 + i * 92 + rng.random() * 26
        T.gigi_t(im, x, y, 46 + 16 * rng.random(), rot=(rng.random() - 0.5) * 1.1,
                 lebar_r=0.62, tone=mix(CREAM, PASIR, 0.10 + 0.16 * rng.random()), gerigi=False)
    # penggaris 18 cm
    x0, x1, yr = 640, 936, 806
    T.bentuk2(im, [(x0 - 8, yr - 15), (x1 + 8, yr - 15), (x1 + 8, yr + 15), (x0 - 8, yr + 15)],
              mix(CREAM, KREM, 0.30), outline=mix(INK, NAVY_D, 0.35), ow=2.6, light=0.20, dark=0.06)
    for i in range(10):
        xx = x0 + (x1 - x0) * i / 9
        line_on(im, (xx, yr + 15), (xx, yr + 15 - (22 if i % 3 else 31)),
                mix(INK, TEAL_D, 0.45), 2.4, 0.70)
    T.label2(im, (x0 + x1) / 2, yr - 58, "18 CM", fsz=25, tone=mix(NAVY, INK, 0.12),
             bg=mix(T.BUIH, CREAM, 0.32))
    T.dasar_pasir(im, 1830, seed=59, amp=10)
    _rumput(im, 1010, 1830, 96)


def _isi_kaca(lay, R):
    """Isi kaca pembesar: satu gigi dibesarkan, gerigi di kedua tepi KELIHATAN.

    Digambar langsung di ruang PIKEL (0..2R) supaya tidak bergantung pada S(SS).
    """
    lay.paste(mix(CREAM, WHITE, 0.34), (0, 0, 2 * R, 2 * R))
    # latar batu halus
    rng = np.random.default_rng(4)
    for _ in range(70):
        x, y = rng.random() * 2 * R, rng.random() * 2 * R
        lay.putpixel((int(x), int(y)), mix(CREAM, PASIR, 0.30 + 0.25 * rng.random()))
    apex = (R * 1.02, R * 0.20)
    dasar_y = R * 1.80
    half = R * 0.62
    kiri, kanan = [], []
    N = 9
    for i in range(N + 1):
        u = i / N
        w = half * (1.0 - u ** 1.55)                 # menyempit ke ujung
        ser = (R * 0.045) if (i % 2 and 0.10 < u < 0.92) else 0.0
        yy = dasar_y - (dasar_y - apex[1]) * u
        geser = -half * 0.10 * u ** 2                # ujung menekuk ke kiri
        kiri.append((apex[0] + geser - w + ser, yy))
        kanan.append((apex[0] + geser + w - ser, yy))
    pts = kiri + kanan[::-1]
    m = Image.new("L", (2 * R, 2 * R), 0)
    ImageDraw.Draw(m).polygon([(int(x), int(y)) for x, y in pts], fill=255)
    # isi: gradasi krem (dibuat manual, ukuran piksel)
    hh, ww = 2 * R, 2 * R
    ys = np.linspace(0.0, 1.0, hh, dtype=np.float32)
    out = np.empty((hh, ww, 3), dtype=np.uint8)
    for c in range(3):
        top = mix(CREAM, WHITE, 0.62)[c]
        bot = mix(CREAM, PASIR, 0.34)[c]
        out[:, :, c] = np.clip(top + (bot - top) * ys, 0, 255).astype(np.uint8)[:, None]
    lay.paste(Image.fromarray(out, "RGB"), (0, 0), m)
    # outline tebal (MaxFilter tidak perlu; cukup dilasi 2 px)
    ol = m.filter(ImageFilter.MaxFilter(7))
    ed = Image.fromarray(np.clip(np.asarray(ol, np.int16) - np.asarray(m, np.int16), 0, 255).astype(np.uint8))
    lay.paste(mix(INK, TERRA_D, 0.45), (0, 0), ed)
    # kilau tipis di sisi kiri
    gl = [(int(x + R * 0.10), int(y)) for x, y in kiri[1:N - 2]]
    if len(gl) > 2:
        d = ImageDraw.Draw(lay)
        d.line(gl, fill=mix(WHITE, CREAM, 0.25), width=max(2, int(R * 0.035)))


def sc_gigi(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("gigi17", _dunia_gigi), (0, 0))
    # kaca pembesar: muncul dengan pop, isinya tepi gigi bergerigi
    p = eo(seg(tl, 0.25, 0.75))
    if p > 0.02:
        r = 148 * (0.86 + 0.14 * p)
        T.inset_kaca(img, 856, 980, r, _isi_kaca, al=min(1.0, p * 1.2) * al)
        if p > 0.96:
            T.label2(img, 856, 1166, "GERIGI SEPERTI GERGAJI", fsz=21,
                     tone=mix(NAVY, INK, 0.12), bg=mix(T.BUIH, CREAM, 0.30), al=al)
    # kilau menyapu gigi pada lempeng (kecil, jadi tidak berisik)
    for gi, (gx, gy, hh) in enumerate(((238, 1218, 62), (300, 1198, 74), (364, 1192, 80),
                                        (428, 1200, 72), (488, 1216, 60))):
        a = 0.10 + 0.30 * max(0.0, math.sin(tl * 2.2 - gi * 0.6))
        dot_on(img, gx + 8, gy - hh * 0.5, 3.0, mix(AMBER_H, WHITE, 0.45), a * al)
    # serbuk fosil melayang
    rng = np.random.default_rng(11)
    for i in range(6):
        x = 640 + rng.random() * 300
        y = 400 + ((rng.random() * 520) + tl * 14) % 520
        dot_on(img, x, y, 2.2, mix(T.BUIH, WHITE, 0.5), 0.13 * al)
    q = 0.5 + 0.5 * math.sin(tl * 1.4)
    ring_on(img, 372, 1210, 236 + 7 * q, mix(AMBER_H, WHITE, 0.40), 2.0, 0.05 + 0.06 * q)
    T.kartu2(img, ["SATU HIU,", "PULUHAN RIBU GIGI"], hl="PULUHAN RIBU GIGI", y=Y_KARTU, fsz=58,
             al=al, dy=dy, tab=accent, kicker="GIGI TERUS BERGANTI SEPANJANG HIDUP")
    T.sumber(img, SUMBER_GIGI, al=al)


# ------------------------------------------------------------------ 6 · GIGIT
def _dunia_gigit(im):
    _langit_air(im, seed=60, t=0.0, awan=None, atas=mix(T.AIR_2, T.AIR_3, 0.50),
                bawah=mix(T.AIR_4, T.AIR_5, 0.70))
    # paus kecil di kanan (ekor menghadap mulut)
    T.paus_t(im, 596, 612, 430, tinggi=0.20, t=0.0)
    # kepala megalodon: rahang atas + rahang bawah terpisah (buka disetel di sc_)
    T.rahang_terbuka(im, 250, 560, skala=1.05, buka=0.42)
    T.dasar_pasir(im, 1820, seed=61, amp=12)
    _rumput(im, 120, 1820, 120)
    _rumput(im, 990, 1820, 104)


def sc_gigit(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("gigit17", _dunia_gigit), (0, 0))
    gigit = eo(seg(tl, 0.9, 1.25))
    buka = max(0.02, 0.42 + 0.14 * math.sin(tl * 2.2) * (1 - gigit) - 0.40 * gigit)
    T.rahang_terbuka(img, 250, 560, skala=1.05, buka=buka, al=al, gigi_n=8)
    # bekas luka pada ekor paus (bukan darah)
    p = eo(seg(tl, 1.1, 1.7))
    for i in range(4):
        y0s = 566 + i * 27
        T.garis2(img, [(716, y0s), (716 + 58 * p, y0s + 10), (716 + 100 * p, y0s + 4)],
                 mix(TERRA, AMBER_H, 0.25), 2.6, 0.42 * al)
    # busur gerak dari mulut ke ekor
    for i in range(3):
        u = (tl * 0.85 + i / 3.0) % 1.0
        dot_on(img, 512 + 176 * u, 606 + 10 * math.sin(u * 6.0), 3.8,
               mix(T.BUIH, WHITE, 0.5), 0.22 * al)
    ring_on(img, 300, 610, 236 + 10 * math.sin(tl * 2.4), mix(AMBER_H, WHITE, 0.35), 2.2, 0.10 * al)
    T.label2(img, 890, 462, "EKOR DULU", fsz=22, tone=mix(NAVY, INK, 0.12),
             bg=mix(AMBER_H, WHITE, 0.50), al=al)
    T.kartu2(img, ["YANG DISERANG", "EKORNYA DULU"], hl="EKORNYA", y=Y_KARTU, fsz=60,
             al=al, dy=dy, tab=accent, kicker="DARI BEKAS LUKA PADA FOSIL PAUS")
    T.sumber(img, "Sumber: Nature Communications 2022 · PeerJ 2019", al=al)


# ------------------------------------------------------------------ 7 · PUNAH
def _dunia_punah(im):
    # laut mendingin: air lebih biru, langit lebih pucat
    T.langit(im, 0, T.SURF, a=mix(LANGIT, WHITE, 0.30), b=mix(LANGIT_2, (198, 210, 214), 0.55), seed=62)
    T.awan_kecil(im, 230, 168, 190, 34, seed=65)
    T.air_t(im, 0.0, atas=(170, 206, 204), bawah=mix(T.AIR_5, NAVY, 0.40), seed=63)
    T.sinar_t(im, 3.0, n=3, kuat=0.22, seed=62)
    T.permukaan(im, T.SURF, 0.0, amp=7)
    # rak laut dangkal menyempit (kiri)
    T.bentuk2(im, [(-40, 1004), (300, 986), (410, 1030), (520, 1160), (-40, 1180)],
              mix(T.PASIR_TD, TEAL, 0.30), outline=mix(INK, NAVY_D, 0.40), ow=3.0,
              light=0.16, dark=0.12)
    # paus migrasi ke kutub (kanan atas) + panah
    T.paus_t(im, 120, 386, 250, tinggi=0.20, t=0.0, tone=mix(T.HIU, TEAL, 0.30))
    T.paus_t(im, 250, 318, 176, tinggi=0.21, t=0.4, tone=mix(T.HIU, TEAL, 0.52), alpha=0.95)
    for i in range(3):
        x0 = 430 + i * 40
        T.panah(im, x0, 392 + i * 20, x0 + 112, 336 + i * 20,
                tone=mix(T.BUIH, TEAL_D, 0.30), w=6.0, al=0.65, kepala=16)
    # hiu putih kecil sebagai pesaing baru (kanan bawah)
    T.hiu_t(im, 600, 1216, 268, tinggi=0.205, t=0.0, insang=False, tone=T.HIU_2)
    T.hiu_t(im, 728, 1320, 208, tinggi=0.215, t=0.5, insang=False, tone=mix(T.HIU_2, INK, 0.10))
    # butir es
    rng = np.random.default_rng(17)
    for i in range(30):
        x = 60 + rng.random() * 380
        y = 380 + rng.random() * 520
        dot_on(im, x, y, 2.0 + rng.random() * 2.2, mix(T.BUIH, WHITE, 0.55), 0.35)
    T.dasar_pasir(im, 1810, seed=64, amp=10, tone=mix(T.PASIR_TD, TEAL, 0.22))


def sc_punah(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("punah17", _dunia_punah), (0, 0))
    chip = (("SAMUDRA MENDINGIN", 0.18), ("LAUT DANGKAL MENYEMPIT", 0.72),
            ("PAUS PINDAH KE KUTUB", 1.26), ("HIU PUTIH BERSAING", 1.80))
    for i, (txt, t0) in enumerate(chip):
        p = eo(seg(tl, t0, t0 + 0.45))
        if p <= 0:
            continue
        x = 232 if i % 2 == 0 else 604
        y = 856 + (i // 2) * 92
        T.label2(img, x, y, txt, fsz=22, tone=mix(NAVY, INK, 0.12),
                 bg=mix(T.BUIH, CREAM, 0.30), al=p * al)
    # butir es turun pelan
    for i in range(16):
        x = (70 + i * 63 + tl * 10) % 1020
        y = (400 + (i * 167) % 620 + tl * 34) % 620 + 380
        dot_on(img, x, y, 2.2, mix(T.BUIH, WHITE, 0.60), 0.20 * al)
    p = 0.5 + 0.5 * math.sin(tl * 1.7)
    ring_on(img, 520, 360, 40 + 8 * p, mix(T.BUIH, WHITE, 0.35), 2.0, 0.14 * al)
    T.kartu2(img, ["RAKSASA KALAH", "OLEH PERUBAHAN"], hl="PERUBAHAN", y=Y_KARTU, fsz=62,
             al=al, dy=dy, tab=accent, kicker="BUKAN SATU SEBAB · 3,6 JUTA TAHUN LALU")
    T.sumber(img, SUMBER_PUNAH, al=al)


# ------------------------------------------------------------------ 8 · LOOP
def _dunia_loop(im):
    """Frame akhir harus menyerupai frame 0: komposisi intro, sedikit lebih tenang."""
    _langit_air(im, seed=51, t=0.0, atas=T.AIR_1, bawah=mix(T.AIR_4, T.AIR_5, 0.35))
    T.hiu_t(im, 96, 700, 880, tinggi=0.152, t=0.0, bayang=1.0, sirip=1.05,
            tone=mix(T.HIU, TEAL_D, 0.18))
    T.dasar_pasir(im, 1780, seed=52)
    T.bentuk2(im, [(112, 1132), (466, 1124), (480, 1190), (120, 1198)],
              mix(T.HIU, TEAL_D, 0.42), outline=mix(INK, NAVY_D, 0.45), ow=3.2,
              light=0.14, dark=0.12)
    # gigi TEGAK, kecil, rapat, di atas busur rahang (rotasi besar -> terbaca panah)
    for (gx, gy, hh, rt) in ((186, 1144, 78, -0.26), (238, 1136, 94, -0.14), (292, 1132, 104, 0.0),
                             (346, 1136, 92, 0.14), (398, 1144, 76, 0.26)):
        T.gigi_t(im, gx, gy, hh, rot=rt, lebar_r=0.56, tone=mix(CREAM, PASIR, 0.02))
    _rumput(im, 60, 1770, 130)
    _rumput(im, 1020, 1770, 120)


def sc_loop(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("loop17", _dunia_loop), (0, 0))
    # garis ukur tetap ada (sama seperti frame 0) supaya potongan terasa menyatu
    y = 906
    T.garis2(img, [(96, y), (976, y)], mix(TERRA, TERRA_D, 0.25), 3.6, 0.72 * al)
    for xx in (96, 976):
        line_on(img, (xx, y - 15), (xx, y + 15), mix(TERRA, TERRA_D, 0.25), 3.6, 0.72 * al)
    # napas cahaya pada vitrin gigi (sorot lembut)
    p = 0.5 + 0.5 * math.sin(tl * 1.2)
    ring_on(img, 286, 1092, 124 + 7 * p, mix(AMBER_H, WHITE, 0.35), 2.2, 0.08 + 0.09 * p)
    for i in range(8):                       # debu halus di sorot
        x = 176 + ((i * 47 + tl * 7) % 240)
        yy = 1080 + ((i * 61 + tl * 12) % 220)
        dot_on(img, x, yy, 2.0, mix(CREAM, WHITE, 0.4), 0.16 * al)
    T.gelembung_naik(img, tl, 150, 250, 560, 700, n=3, seed=4, skala=0.7)
    T.kartu2(img, ["GIGINYA MASIH ADA", "HIUNYA TIDAK"], hl="HIUNYA TIDAK", y=Y_KARTU, fsz=64,
             al=al, dy=dy, tab=accent, kicker="3,6 JUTA TAHUN, TANPA SATU PUN TULANG UTUH")
    T.sumber(img, "Sumber: NHM · koleksi gigi fosil 20-3,6 juta tahun", al=al)


VISUALS = {
    "t17_intro": sc_intro,
    "t17_waktu": sc_waktu,
    "t17_ukur": sc_ukur,
    "t17_bentuk": sc_bentuk,
    "t17_gigi": sc_gigi,
    "t17_gigit": sc_gigit,
    "t17_punah": sc_punah,
    "t17_loop": sc_loop,
}

# ------------------------------------------------------------------ cue kata -> SFX
# Timing diambil APA ADANYA dari v16 (sudah teruji terhadap audio master).
CUES = {
    "t17_intro": {"terbesar": ("terbesar", 0.03), "meter": ("meter", 0.12),
                  "gigi": ("gigi", 0.52), "telapak": ("telapak", 0.86)},
    "t17_waktu": {"megalodon": ("Megalodon", 0.02), "dua": ("dua", 0.14), "puluh": ("puluh", 0.18),
                  "tahun": ("tahun", 0.26), "rawan": ("rawan", 0.56), "fosil": ("fosil", 0.63),
                  "giginya": ("giginya", 0.82)},
    "t17_ukur": {"gigi": ("Gigi", 0.02), "ukuran": ("ukuran", 0.10), "puluh": ("puluh", 0.30),
                 "sembilan": ("sembilan", 0.36), "meter": ("meter", 0.56), "ton": ("ton", 0.84)},
    "t17_bentuk": {"bentuknya": ("Bentuknya", 0.02), "putih": ("putih", 0.10),
                   "ramping": ("ramping", 0.26), "lemon": ("lemon", 0.34),
                   "sirip": ("sirip", 0.44), "cepat": ("cepat", 0.86)},
    "t17_gigi": {"bergerigi": ("bergerigi", 0.06), "gergaji": ("gergaji", 0.14),
                 "sentimeter": ("sentimeter", 0.26), "mengganti": ("berganti", 0.40),
                 "puluhan": ("puluhan", 0.58), "ribu": ("ribu", 0.63), "tulang": ("tulang", 0.90)},
    "t17_gigit": {"gigitan": ("Gigitan", 0.02), "kuat": ("kuat", 0.14), "paus": ("paus", 0.28),
                  "luka": ("luka", 0.44), "ekor": ("ekor", 0.60), "menggigit": ("menggigit", 0.82)},
    "t17_punah": {"tiga": ("Tiga", 0.02), "hilang": ("hilang", 0.14),
                  "mendingin": ("mendingin", 0.34), "menyempit": ("menyempit", 0.42),
                  "kutub": ("kutub", 0.52), "makanan": ("makanan", 0.62), "beban": ("beban", 0.92)},
    "t17_loop": {"giginya": ("Giginya", 0.02), "museum": ("museum", 0.18),
                 "hitam": ("hitam", 0.28), "bergerigi": ("bergerigi", 0.34),
                 "muncul": ("muncul", 0.86)},
}

SFX = {
    "t17_intro": {"terbesar": ("riser", 0.40, 0), "gigi": ("ding", 0.42, 0),
                  "telapak": ("pop", 0.40, 0)},
    "t17_waktu": {"megalodon": ("pop", 0.38, 0), "tahun": ("click", 0.40, 0),
                  "fosil": ("thud", 0.40, 0), "giginya": ("ding", 0.36, 0)},
    "t17_ukur": {"gigi": ("pop", 0.38, 0), "meter": ("click", 0.40, 0), "ton": ("thud", 0.42, 0)},
    "t17_bentuk": {"ramping": ("swish", 0.38, 0), "lemon": ("pop", 0.38, 0),
                   "cepat": ("ding", 0.36, 0)},
    "t17_gigi": {"bergerigi": ("click", 0.40, 0), "sentimeter": ("pop", 0.38, 0),
                 "ribu": ("riser", 0.34, 0), "tulang": ("thud", 0.40, 0)},
    "t17_gigit": {"kuat": ("thud", 0.44, 0), "paus": ("pop", 0.38, 0),
                  "ekor": ("swish", 0.40, 0), "menggigit": ("click", 0.42, 0)},
    "t17_punah": {"hilang": ("thud", 0.42, 0), "mendingin": ("swish", 0.38, 0),
                  "kutub": ("pop", 0.38, 0), "beban": ("riser", 0.34, 0)},
    "t17_loop": {"museum": ("pop", 0.38, 0), "hitam": ("thud", 0.38, 0),
                 "muncul": ("ding", 0.40, 0)},
}
BEATS55 = {k: [] for k in CUES}


def events_v12(sc):
    """Event SFX per kata untuk mesin v12 (dipanggil master_audio & render)."""
    vis = sc.get("visual", "")
    if vis not in CUES:
        return []
    c = M.cues(sc, sc["dur"], {k: v for k, v in CUES[vis].items()})
    out = [(sc["start"] + c[nama] + off, jenis, g) for nama, (jenis, g, off) in SFX.get(vis, {}).items()]
    if str(sc.get("trans") or "").lower() == "morph":
        out.append((sc["start"] - 0.08, "morph", 0.55))
    return out


def daftar():
    M11.BEATS.update(BEATS55)
    D.VISUALS.update(VISUALS)
    M.EVENTS12.update({k: events_v12 for k in CUES})
    return sorted(VISUALS)


daftar()


if __name__ == "__main__":
    D.SS = 1.0
    im = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), T.AIR_3)
    for nama, fn in VISUALS.items():
        sc = {"id": nama.split("_")[1], "visual": nama, "start": 10.0, "dur": 14.0,
              "trans": "morph", "accent": "#2E7068", "captions": []}
        for tl in (0.0, 0.12, 2.0, 7.0, 13.98):
            fn(im, None, sc, tl, 14.0, 10.0 + tl, TERRA, 1.0, 0.0)
        assert events_v12(sc), nama
    print(f"selftest ep55-v17: {len(VISUALS)} visual OK "
          f"({sum(len(v) for v in CUES.values())} cue, {sum(len(v) for v in SFX.values())} SFX)")
