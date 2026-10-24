#!/usr/bin/env python3
"""mesin_v16_ep55.py — Ep55 "Megalodon Bukan Hiu Putih Raksasa — Dan Kita Cuma Punya Giginya"

Mesin v16 LAUT DALAM. Delapan dunia yang semuanya berada di bawah permukaan air:
gigi di dasar laut, garis waktu, potongan tubuh yang diukur, perbandingan bentuk,
potret gigi, mulut yang menganga, laut yang mendingin, lalu kembali ke gigi.

Semua digambar kode (tidak ada aset gambar). Selftest:  python3 mesin_v16_ep55.py
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import diagrams as D
import mesin_v11 as M11
import mesin_v12 as M
import mesin_v15_ilustrasi as V15
import mesin_v16_laut as V
from diagrams import (INK, CREAM, WHITE, MUTED, mix, clamp, seg, eo, font, tw, tlh,
                      paste_c, rrect_on, line_on, dot_on, ring_on, S)
from mesin_v15_ilustrasi import (KREM, PASIR, PASIR_D, TERRA, TERRA_D, OLIVE, OLIVE_D,
                                 NAVY, NAVY_D, AMBER_H, grad_v, kurva)

SUMBER = "Sumber: Shimada dkk. 2025 · NHM · Nature Comm. 2022"
SUMBER_GIGI = "Sumber: Shimada dkk. 2025 · Palaeontologia Electronica"
SUMBER_PUNAH = "Sumber: NHM · Nature Communications 2022 · PeerJ 2019"
Y_KARTU = 1478

AIR_T = V.AIR_TERANG
AIR_M = V.AIR_TENGAH
AIR_D = V.AIR_DALAM
AIR_G = V.AIR_GELAP
AIR_H = V.AIR_HITAM

# ------------------------------------------------------------------ cache dasar
_BASE = {}
_CACHE_DIR = os.path.join(os.environ.get("KT_BUILD", "build"), "v16base")


def _base(nama, builder):
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
    im = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), AIR_M)
    builder(im)
    _BASE[key] = im
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        im.save(path)
    except Exception:
        pass
    return im


# ------------------------------------------------------------------ 1 · HOOK
def _dunia_intro(im):
    V.air(im, 0.0, atas=mix(V.AIR_TERANG, V.AIR_PERMUKAAN, 0.35), bawah=V.AIR_GELAP, seed=51)
    V.sinar(im, 1.2, n=6, kuat=0.20, seed=51)
    V.salju(im, 0.0, n=70, kuat=0.42, seed=51)
    # permukaan air di atas
    for i in range(3):
        yy = 96 + i * 26
        pts = [(x, yy + 12 * math.sin(x / 130.0 + i)) for x in range(-20, 1120, 40)]
        V.garis2(im, pts, mix(V.CAHAYA_AIR, WHITE, 0.3), 4.0 - i * 0.8, 0.18 - i * 0.04)
    # hiu utama: utuh di dalam layar (skala diukur di bawahnya)
    V.hiu(im, 96, 700, 890, tinggi=0.148, tone=mix(AIR_H, AIR_G, 0.30), t=0.0,
          outline=mix(V.CAHAYA_AIR, WHITE, 0.16), sirip_punggung=1.05,
          rim=mix(V.CAHAYA_AIR, WHITE, 0.34))
    # kedalaman depan: punggung batu gelap di kiri bawah (parallax)
    V.bentuk2(im, [(-60, 1180), (150, 1108), (330, 1150), (360, 1920), (-60, 1920)],
              mix(AIR_H, INK, 0.35), outline=None, ow=0, light=0.08, dark=0.2)
    V.bentuk2(im, [(1010, 1240), (1140, 1180), (1140, 1920), (990, 1920)],
              mix(AIR_H, INK, 0.30), outline=None, ow=0, light=0.06, dark=0.2)
    # gigi di depan (fokus kedua)
    V.dasar(im, 1760, tone=mix(PASIR_D, AIR_M, 0.42), amp=20, seed=52)
    V.kaustik(im, 0.0, 1660, 1920, kuat=0.06)
    V.gigi(im, 286, 1226, 224, rot=0.16, tone=mix(CREAM, PASIR, 0.10))
    V.gigi(im, 430, 1258, 148, rot=-0.10, tone=mix(CREAM, PASIR, 0.20))


def sc_intro(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("intro55", _dunia_intro), (0, 0))
    # garis ukur 24 m di bawah siluet
    p = eo(seg(tl, 0.25, 1.6))
    y = 862
    x0, x1 = 96, 96 + 890 * p
    line_on(img, (x0, y), (x1, y), mix(V.CAHAYA_AIR, WHITE, 0.25), 4.0, 0.85)
    for xx in (96, 986):
        line_on(img, (xx, y - 24), (xx, y + 24), mix(V.CAHAYA_AIR, WHITE, 0.25), 4.0, 0.85)
    if p > 0.9:
        V.label2(img, 540, y + 58, "24,3 METER  ·  BATAS ATAS", fsz=24,
                 tone=mix(AIR_H, INK, 0.1), bg=mix(V.CAHAYA_AIR, WHITE, 0.55), al=al)
    # sorot lembut pada gigi
    p2 = 0.5 + 0.5 * math.sin(tl * 1.7)
    ring_on(img, 300, 1180, 140 + 6 * p2, mix(V.CAHAYA_AIR, WHITE, 0.4), 2.4, 0.10 + 0.10 * p2)
    V.kartu2(img, ["HIU 24 METER", "YANG TERSISA CUMA GIGI"], hl="CUMA GIGI", y=Y_KARTU, fsz=62,
             al=al, dy=dy, tab=accent, kicker="LAUT PURBA · GIGI SEBESAR TELAPAK TANGAN")
    V.sumber(img, SUMBER, al=al)


# ------------------------------------------------------------------ 2 · GARIS WAKTU
def _dunia_skala(im):
    V.air(im, 0.0, atas=mix(V.AIR_TERANG, V.AIR_TENGAH, 0.55), bawah=V.AIR_HITAM, seed=52)
    V.sinar(im, 2.0, n=5, kuat=0.14, seed=52)
    V.salju(im, 0.0, n=55, kuat=0.34, seed=52)
    # pita waktu
    y = 690
    V.bentuk2(im, [(-40, y - 54), (1120, y - 54), (1120, y + 54), (-40, y + 54)],
              mix(AIR_G, AIR_H, 0.4), outline=None, ow=0, light=0.10, dark=0.20)
    # rentang hidup megalodon: 20 -> 3,6 (kiri ke kanan)
    xa, xb = 120, 900
    for i in range(60):
        xx = xa + (xb - xa) * i / 59
        line_on(im, (xx, y), (xx, y + (18 if i % 5 else 28)), mix(V.CAHAYA_AIR, WHITE, 0.2), 2.0, 0.30)
    V.garis2(im, [(xa, y), (xb, y)], mix(V.CAHAYA_AIR, WHITE, 0.35), 5.0, 0.85)
    V.elips2(im, xa, y, 12, 12, mix(V.CAHAYA_AIR, WHITE, 0.4), outline=None, ow=0)
    V.elips2(im, xb, y, 12, 12, mix(TERRA, AMBER_H, 0.5), outline=None, ow=0)
    # gigi-gigi kecil di sepanjang garis (fosil yang ditemukan)
    rng = np.random.default_rng(5)
    for i in range(11):
        xx = xa + (xb - xa) * (0.06 + 0.88 * rng.random())
        s = 0.5 + 0.5 * rng.random()
        V.gigi(im, xx, y - 34, 42 * s, rot=(rng.random() - 0.5) * 0.7,
               tone=mix(CREAM, PASIR, 0.1 + 0.2 * rng.random()), gerigi=False)
    # label ujung
    V.label2(im, 196, y + 132, "20 JUTA TAHUN LALU", fsz=22, tone=mix(AIR_H, INK, 0.05),
             bg=mix(V.CAHAYA_AIR, WHITE, 0.5))
    V.label2(im, 872, y + 132, "3,6 JUTA TAHUN LALU", fsz=22, tone=mix(AIR_H, INK, 0.05),
             bg=mix(V.CAHAYA_AIR, WHITE, 0.5))
    # siluet hiu di atas pita (hidup) dan tanda silang (hilang)
    V.hiu(im, 130, 380, 410, tinggi=0.150, tone=mix(AIR_G, AIR_H, 0.20), t=0.0,
          outline=None, mulut=False, insang=False)
    V.hiu(im, 640, 402, 280, tinggi=0.170, tone=mix(AIR_G, AIR_H, 0.35), t=0.3,
          outline=None, mulut=False, insang=False, ekor_bulan=False)
    # "sekarang" di kanan
    V.garis2(im, [(978, y - 74), (978, y + 74)], mix(TERRA, AMBER_H, 0.3), 4.0, 0.7)
    V.label2(im, 940, y - 116, "KINI", fsz=21, tone=mix(AIR_H, INK, 0.05),
             bg=mix(TERRA, AMBER_H, 0.45))
    # lapisan sedimen di bawah
    V.dasar(im, 1660, tone=mix(PASIR_D, AIR_D, 0.55), amp=26, seed=53)
    V.kaustik(im, 0.0, 1560, 1920, kuat=0.06)


def sc_skala(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("skala55", _dunia_skala), (0, 0))
    # penanda waktu bergerak di sepanjang pita: 20 -> 3,6
    p = eo(seg(tl, 0.4, 2.4))
    xa, xb, y = 120, 900, 690
    x = xa + (xb - xa) * p
    line_on(img, (x, y - 74), (x, y + 74), mix(V.CAHAYA_AIR, WHITE, 0.5), 3.0, 0.55 * al)
    dot_on(img, x, y, 9, mix(AMBER_H, WHITE, 0.35), 0.9 * al)
    ring_on(img, x, y, 22 + 4 * math.sin(tl * 3.0), mix(AMBER_H, WHITE, 0.3), 2.0, 0.35 * al)
    # kilau pada gigi-gigi fosil
    for i, (gx, gy) in enumerate(((300, 656), (470, 656), (700, 656))):
        ring_on(img, gx, gy, 30, mix(V.CAHAYA_AIR, WHITE, 0.5), 1.8,
                0.10 + 0.12 * (0.5 + 0.5 * math.sin(tl * 2.2 + i)))
    V.kartu2(img, ["HIDUP 20 JUTA TAHUN,", "HILANG 3,6 JUTA TAHUN LALU"], hl="3,6 JUTA TAHUN LALU",
             y=Y_KARTU, fsz=55, al=al, dy=dy, tab=accent, kicker="TULANG RAWAN TIDAK MENJADI FOSIL")
    V.sumber(img, SUMBER_GIGI, al=al)


# ------------------------------------------------------------------ 3 · PENGUKURAN
def _dunia_ukur(im):
    V.air(im, 0.0, atas=mix(V.AIR_TERANG, V.AIR_TENGAH, 0.35), bawah=V.AIR_GELAP, seed=54)
    V.sinar(im, 0.8, n=5, kuat=0.16, seed=54)
    V.salju(im, 0.0, n=50, kuat=0.30, seed=54)
    # satu tubuh utuh: 16,4 m individu Belgia, digambar pada 900 px
    x, y, L = 92, 760, 900
    V.hiu(im, x, y, L, tinggi=0.148, tone=mix(AIR_G, AIR_H, 0.10), t=0.0,
          outline=mix(V.CAHAYA_AIR, WHITE, 0.22), sirip_punggung=0.95,
          rim=mix(V.CAHAYA_AIR, WHITE, 0.40))
    # penanda tiga bagian: kepala 1,8 | tulang belakang 11 | ekor 3,6
    k = L / 16.4
    xs = [x, x + 1.8 * k, x + 12.8 * k, x + 16.4 * k]
    for i in range(3):
        mid = (xs[i] + xs[i + 1]) / 2
        tip = xs[i] + 0.03 if i == 0 else (xs[i + 1] - 0.03 if i == 2 else mid)
        for seg_i in range(3):
            a = seg_i / 3.0
            pass
    # tanda batas bagian (garis putus-putus vertikal)
    for xx in xs[1:3]:
        for yy in range(610, 940, 26):
            line_on(im, (xx, yy), (xx, yy + 12), mix(V.CAHAYA_AIR, WHITE, 0.35), 2.4, 0.5)
    # kurung bagian di bawah tubuh
    yb = 990
    for (b0, b1, txt) in ((xs[0], xs[1], "1,8 m"), (xs[1], xs[2], "11 m tulang belakang"),
                          (xs[2], xs[3], "3,6 m")):
        V.garis2(im, [(b0, yb), (b1, yb)], mix(V.CAHAYA_AIR, WHITE, 0.45), 3.0, 0.62)
        line_on(im, (b0, yb - 17), (b0, yb + 17), mix(V.CAHAYA_AIR, WHITE, 0.45), 3.0, 0.62)
        line_on(im, (b1, yb - 17), (b1, yb + 17), mix(V.CAHAYA_AIR, WHITE, 0.45), 3.0, 0.62)
        V.label2(im, (b0 + b1) / 2, yb + 62, txt, fsz=21, tone=mix(AIR_H, INK, 0.05),
                 bg=mix(V.CAHAYA_AIR, WHITE, 0.5))
    # penyelam pembanding (1,8 m) di kanan bawah, tidak menumpuk label
    V.penyelam(im, 986, 1408, 1.8, skala=54, tone=mix(AIR_H, INK, 0.15), alpha=0.92)
    V.label2(im, 900, 1262, "PENYELAM 1,8 m", fsz=19, tone=mix(AIR_H, INK, 0.05),
             bg=mix(V.CAHAYA_AIR, WHITE, 0.45))
    V.dasar(im, 1750, tone=mix(PASIR_D, AIR_D, 0.6), amp=20, seed=55)
    V.kaustik(im, 0.0, 1660, 1920, kuat=0.05)


def sc_ukur(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("ukur55", _dunia_ukur), (0, 0))
    # garis ukur total: 16,4 m tumbuh dari kiri ke kanan
    p = eo(seg(tl, 0.2, 1.7))
    y, x0 = 596, 92
    L = 900 * p
    V.garis2(img, [(x0, y), (x0 + L, y)], mix(AMBER_H, WHITE, 0.35), 4.0, 0.9 * al)
    line_on(img, (x0, y - 22), (x0, y + 22), mix(AMBER_H, WHITE, 0.35), 4.0, 0.9 * al)
    if p > 0.99:
        line_on(img, (x0 + 900, y - 22), (x0 + 900, y + 22), mix(AMBER_H, WHITE, 0.35), 4.0, 0.9 * al)
        V.label2(img, 540, y - 56, "16,4 METER · INDIVIDU BELGIA", fsz=23,
                 tone=mix(AIR_H, INK, 0.05), bg=mix(AMBER_H, WHITE, 0.6), al=al)
    # batas 24,3 m: garis putus-putus di atas (skala yang sama)
    q = eo(seg(tl, 1.1, 2.2))
    if q > 0.02:
        x_end = x0 + 900 * (24.3 / 16.4) * q
        for xx in range(x0, int(x_end), 30):
            line_on(img, (xx, 500), (min(xx + 16, x_end), 500), mix(V.CAHAYA_AIR, WHITE, 0.5),
                    3.2, 0.55 * al)
        if q > 0.98:
            V.label2(img, 700, 452, "BATAS 24,3 M · 94 TON", fsz=21,
                     tone=mix(AIR_H, INK, 0.05), bg=mix(V.CAHAYA_AIR, WHITE, 0.55), al=al)
    V.kartu2(img, ["16,4 METER DARI 11 METER", "TULANG BELAKANG"], hl="16,4 METER", y=Y_KARTU,
             fsz=56, al=al, dy=dy, tab=accent, kicker="DIUKUR ULANG 29 AHLI · 2025")
    V.sumber(img, SUMBER, al=al)


# ------------------------------------------------------------------ 4 · BENTUK
def _dunia_bentuk(im):
    V.air(im, 0.0, atas=mix(V.AIR_TERANG, V.AIR_TENGAH, 0.45), bawah=V.AIR_HITAM, seed=56)
    V.sinar(im, 2.6, n=5, kuat=0.13, seed=56)
    V.salju(im, 0.0, n=50, kuat=0.30, seed=56)
    # laut dalam: dua siluet sejajar, panjang sama
    V.hiu(im, 70, 560, 940, tinggi=0.150, tone=mix(AIR_G, AIR_H, 0.15), t=0.0,
          outline=mix(V.CAHAYA_AIR, WHITE, 0.18), sirip_punggung=0.8, ekor_bulan=True,
          mulut=False, rim=mix(V.CAHAYA_AIR, WHITE, 0.3))
    V.label2(im, 250, 396, "MEGALODON · LEBIH RAMING", fsz=21, tone=mix(AIR_H, INK, 0.05),
             bg=mix(V.CAHAYA_AIR, WHITE, 0.55))
    # versi gempal (hiu putih) — panjang sama, badan jauh lebih tebal
    V.hiu(im, 70, 940, 940, tinggi=0.245, tone=mix(AIR_G, AIR_H, 0.30), t=0.0,
          outline=mix(V.CAHAYA_AIR, WHITE, 0.12), sirip_punggung=0.85,
          mulut=False, rim=mix(V.CAHAYA_AIR, WHITE, 0.22))
    V.label2(im, 250, 1188, "HIU PUTIH · GEMPAL", fsz=21, tone=mix(AIR_H, INK, 0.05),
             bg=mix(V.CAHAYA_AIR, WHITE, 0.55))
    # garis bantu panjang yang sama
    for yy in (560, 940):
        pass
    V.dasar(im, 1720, tone=mix(PASIR_D, AIR_D, 0.6), amp=18, seed=57)
    V.kaustik(im, 0.0, 1650, 1920, kuat=0.05)


def sc_bentuk(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("bentuk55", _dunia_bentuk), (0, 0))
    # garis vertikal pembanding panjang (kiri) dan penanda tinggi badan (kanan)
    p = eo(seg(tl, 0.15, 1.2))
    for yy, hh, nm in ((560, 0.150 * 940, "tinggi 14%"), (940, 0.245 * 940, "tinggi 24%")):
        x = 1012
        line_on(img, (x, yy - hh / 2), (x, yy + hh / 2), mix(AMBER_H, WHITE, 0.35), 3.0, 0.75 * p)
        line_on(img, (x - 12, yy - hh / 2), (x + 12, yy - hh / 2), mix(AMBER_H, WHITE, 0.35), 3.0, 0.75 * p)
        line_on(img, (x - 12, yy + hh / 2), (x + 12, yy + hh / 2), mix(AMBER_H, WHITE, 0.35), 3.0, 0.75 * p)
    if p > 0.8:
        V.label2(img, 540, 1196, "PANJANG SAMA · BEDA TINGGI BADAN", fsz=21,
                 tone=mix(AIR_H, INK, 0.05), bg=mix(AMBER_H, WHITE, 0.55), al=al)
    # kilau bergerak di sepanjang punggung megalodon
    for i in range(8):
        u = (tl * 0.22 + i / 8.0) % 1.0
        dot_on(img, 70 + 940 * u, 560 - 70, 3.2, mix(V.CAHAYA_AIR, WHITE, 0.5), 0.22 * al)
    V.kartu2(img, ["BUKAN HIU PUTIH", "YANG DIPERBESAR"], hl="BUKAN HIU PUTIH", y=Y_KARTU, fsz=62,
             al=al, dy=dy, tab=accent, kicker="TUBUH LEBIH DEKAT KE HIU LEMON")
    V.sumber(img, "Sumber: Shimada dkk. 2025 · Palaeontologia Electronica", al=al)


# ------------------------------------------------------------------ 5 · GIGI
def _dunia_gigi(im):
    V.air(im, 0.0, atas=mix(V.AIR_TERANG, V.AIR_TENGAH, 0.30), bawah=V.AIR_HITAM, seed=58)
    V.sinar(im, 1.6, n=5, kuat=0.18, seed=58)
    V.salju(im, 0.0, n=60, kuat=0.36, seed=58)
    # bongkahan batu tempat fosil menempel
    V.bentuk2(im, [(-40, 1216), (1120, 1176), (1120, 1360), (-40, 1400)],
              mix(PASIR_D, AIR_D, 0.30), outline=None, ow=0, light=0.16, dark=0.26)
    # potongan rahang: gusi melengkung + 5 gigi bergradasi ukuran
    gusi = [(120, 1162), (300, 1090), (520, 1062), (740, 1092), (890, 1150)]
    V.garis2(im, V15.kurva((120, 1162), (520, 1030), (890, 1152), 26),
             mix(TERRA_D, TERRA, 0.22), 22, 0.95)
    for i, (gx, gy, hh) in enumerate(((190, 1156, 210), (320, 1118, 268), (470, 1100, 330),
                                      (620, 1112, 292), (760, 1146, 222))):
        V.gigi(im, gx, gy, hh, rot=(i - 2) * 0.16, tone=mix(CREAM, PASIR, 0.10 + 0.04 * abs(i - 2)))
    # serpihan gigi lepas (bukti gigi terus berganti)
    rng = np.random.default_rng(9)
    for i in range(6):
        x = 800 + rng.random() * 190
        y = 300 + i * 120 + rng.random() * 40
        V.gigi(im, x, y, 52 + 40 * rng.random(), rot=(rng.random() - 0.5) * 1.5,
               tone=mix(CREAM, PASIR, 0.2 + 0.2 * rng.random()))
    # penggaris 18 cm di kanan, sejajar gigi terbesar
    x0, x1, yr = 640, 940, 780
    V.garis2(im, [(x0, yr), (x1, yr)], mix(V.CAHAYA_AIR, WHITE, 0.45), 5.0, 0.92)
    for i in range(10):
        xx = x0 + (x1 - x0) * i / 9
        line_on(im, (xx, yr - (24 if i % 3 else 38)), (xx, yr), mix(V.CAHAYA_AIR, WHITE, 0.45),
                3.0, 0.82)
    V.label2(im, (x0 + x1) / 2, yr - 74, "18 CM", fsz=25, tone=mix(AIR_H, INK, 0.05),
             bg=mix(V.CAHAYA_AIR, WHITE, 0.62))
    V.dasar(im, 1800, tone=mix(PASIR_D, AIR_H, 0.5), amp=14, seed=59)
    V.kaustik(im, 0.0, 1720, 1920, kuat=0.05)


def sc_gigi(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("gigi55", _dunia_gigi), (0, 0))
    # kilau gerigi bergerak di sepanjang tepi tiap gigi (menegaskan "bergerigi")
    for gi, (gx, gy, hh, rot) in enumerate(((190, 1156, 210, -0.32), (320, 1118, 268, -0.16),
                                            (470, 1100, 330, 0.0), (620, 1112, 292, 0.16),
                                            (760, 1146, 222, 0.32))):
        w = hh * 0.46
        for k in range(5):
            u = 0.20 + k * 0.13
            setengah = w * 0.5 * (1.0 - u ** 1.55)
            px = -w * 0.16 * u ** 2
            py = -u * hh
            ca, sa = math.cos(rot), math.sin(rot)
            for sgn in (-1, 1):
                x = gx + (px + sgn * setengah) * ca - py * sa
                y = gy + (px + sgn * setengah) * sa + py * ca
                a = 0.06 + 0.30 * max(0.0, math.sin(tl * 2.2 - gi * 0.5 - k * 0.35))
                dot_on(img, x, y, 3.0, mix(AMBER_H, WHITE, 0.5), a * al)
    # serpihan gigi melayang pelan
    rng = np.random.default_rng(11)
    for i in range(7):
        x = 810 + rng.random() * 170
        y = 320 + ((rng.random() * 640) + tl * 20) % 640
        dot_on(img, x, y, 2.4, mix(V.CAHAYA_AIR, WHITE, 0.5), 0.09 * al)
    p = 0.5 + 0.5 * math.sin(tl * 1.5)
    ring_on(img, 470, 1060, 300 + 8 * p, mix(V.CAHAYA_AIR, WHITE, 0.45), 2.0, 0.05 + 0.05 * p)
    V.label2(img, 250, 1250, "GERIGI SEPERTI GERGAJI", fsz=21, tone=mix(AIR_H, INK, 0.05),
             bg=mix(V.CAHAYA_AIR, WHITE, 0.55), al=al)
    V.kartu2(img, ["SATU HIU,", "PULUHAN RIBU GIGI"], hl="PULUHAN RIBU GIGI", y=Y_KARTU, fsz=58,
             al=al, dy=dy, tab=accent, kicker="GIGI TERUS BERGANTI SEPANJANG HIDUP")
    V.sumber(img, SUMBER_GIGI, al=al)


# ------------------------------------------------------------------ 6 · GIGITAN
def _dunia_gigit(im):
    V.air(im, 0.0, atas=mix(V.AIR_TENGAH, V.AIR_DALAM, 0.20), bawah=V.AIR_HITAM, seed=60)
    V.sinar(im, 2.2, n=4, kuat=0.12, seed=60)
    V.salju(im, 0.0, n=55, kuat=0.30, seed=60)
    # mangsa: paus kecil di kanan, ekor menghadap mulut
    V.paus(im, 590, 600, 440, tinggi=0.17, tone=mix(AIR_G, AIR_H, 0.30), outline=None, t=0.0)
    # kepala megalodon dari kiri: moncong membuka, bagian luar kanvas (skala)
    V.bentuk2(im, [(-160, 300), (150, 330), (330, 430), (330, 900), (150, 980), (-160, 1010)],
              mix(AIR_G, AIR_H, 0.28), outline=None, ow=0, light=0.14, dark=0.22)
    # rahang: deret gigi menghadap kanan
    V.baris_gigi(im, 300, 620, 470, 400, buka=0.40, n=9)
    V.dasar(im, 1700, tone=mix(PASIR_D, AIR_H, 0.55), amp=22, seed=61)
    V.kaustik(im, 0.0, 1600, 1920, kuat=0.05)


def sc_gigit(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("gigit55", _dunia_gigit), (0, 0))
    # rahang membuka-menutup pelan, lalu menggigit di detik 0,9
    gigit = eo(seg(tl, 0.9, 1.25))
    buka = max(0.0, 0.40 + 0.18 * math.sin(tl * 2.2) * (1 - gigit))
    # goresan gigitan pada ekor paus (bekas luka, bukan darah)
    p = eo(seg(tl, 1.1, 1.7))
    for i in range(4):
        y0s = 556 + i * 28
        V.garis2(img, [(706, y0s), (706 + 60 * p, y0s + 10), (706 + 104 * p, y0s + 4)],
                 mix(TERRA, AMBER_H, 0.30), 2.6, 0.38 * al)
    # busur gerak dari mulut ke ekor
    for i in range(3):
        u = (tl * 0.9 + i / 3.0) % 1.0
        x = 520 + 170 * u
        y = 600 + 12 * math.sin(u * 6.2)
        dot_on(img, x, y, 4.0, mix(V.CAHAYA_AIR, WHITE, 0.5), 0.20 * al)
    ring_on(img, 300, 620, 230 + 10 * math.sin(tl * 2.6), mix(AMBER_H, WHITE, 0.4), 2.2, 0.10 * al)
    V.label2(img, 880, 470, "EKOR DULU", fsz=22, tone=mix(AIR_H, INK, 0.05),
             bg=mix(AMBER_H, WHITE, 0.6), al=al)
    V.kartu2(img, ["YANG DISERANG", "EKORNYA DULU"], hl="EKORNYA", y=Y_KARTU, fsz=60,
             al=al, dy=dy, tab=accent, kicker="DARI BEKAS LUKA PADA FOSIL PAUS")
    V.sumber(img, "Sumber: Nature Communications 2022 · PeerJ 2019", al=al)


# ------------------------------------------------------------------ 7 · KEPUNAHAN
def _dunia_punah(im):
    # air mendingin: dari teal hangat di atas ke biru-navy dingin di bawah
    V.air(im, 0.0, atas=mix(V.AIR_TERANG, V.AIR_TENGAH, 0.55), bawah=(8, 24, 40), seed=62)
    V.sinar(im, 3.0, n=3, kuat=0.07, seed=62)
    V.salju(im, 0.0, n=70, kuat=0.30, seed=62)
    # rak laut dangkal yang menyempit (kiri) vs laut dalam (kanan)
    V.bentuk2(im, [(-40, 980), (300, 960), (400, 1010), (520, 1160), (-40, 1180)],
              mix(PASIR_D, AIR_D, 0.45), outline=None, ow=0, light=0.12, dark=0.24)
    # panah paus migrasi ke kutub (kanan atas)
    V.paus(im, 120, 360, 240, tinggi=0.16, tone=mix(AIR_G, AIR_H, 0.35), outline=None, t=0.0)
    V.paus(im, 240, 300, 180, tinggi=0.16, tone=mix(AIR_G, AIR_H, 0.5), outline=None, t=0.4)
    for i in range(3):
        x0 = 420 + i * 40
        V.garis2(im, [(x0, 380 + i * 22), (x0 + 120, 320 + i * 22)],
                 mix(V.CAHAYA_AIR, WHITE, 0.35), 4.0, 0.30)
        V.bentuk2(im, [(x0 + 120, 310 + i * 22), (x0 + 96, 316 + i * 22), (x0 + 104, 336 + i * 22)],
                  mix(V.CAHAYA_AIR, WHITE, 0.35), outline=None, ow=0, alpha=0.35)
    # hiu putih kecil-kecil di kanan bawah (pesaing baru)
    V.hiu(im, 640, 1220, 260, tinggi=0.20, tone=mix(AIR_G, AIR_H, 0.45), t=0.0,
          outline=None, mulut=False, insang=False, ekor_bulan=False)
    V.hiu(im, 760, 1320, 200, tinggi=0.21, tone=mix(AIR_G, AIR_H, 0.55), t=0.5,
          outline=None, mulut=False, insang=False, ekor_bulan=False)
    # serpihan salju es di kiri atas (petunjuk pendinginan)
    for i in range(26):
        x = 60 + (i * 71) % 380
        y = 120 + ((i * 137) % 520)
        dot_on(im, x, y, 2.0 + (i % 3), mix(V.CAHAYA_AIR, WHITE, 0.6), 0.20)
    V.dasar(im, 1660, tone=(26, 44, 60), amp=20, seed=63)
    V.kaustik(im, 0.0, 1580, 1920, kuat=0.035)


def sc_punah(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("punah55", _dunia_punah), (0, 0))
    # empat faktor sebagai chip yang muncul bergiliran
    chip = (("SAMUDRA MENDINGIN", 0.20), ("LAUT DANGKAL MENYEMPIT", 0.75),
            ("PAUS PINDAH KE KUTUB", 1.30), ("HIU PUTIH BERSAING", 1.85))
    for i, (txt, t0) in enumerate(chip):
        p = eo(seg(tl, t0, t0 + 0.45))
        if p <= 0:
            continue
        x = 150 if i % 2 == 0 else 560
        y = 820 + (i // 2) * 96
        V.label2(img, x + 60, y, txt, fsz=22, tone=mix(AIR_H, INK, 0.05),
                 bg=mix(V.CAHAYA_AIR, WHITE, 0.5), al=p * al)
    # butir es turun pelan
    for i in range(18):
        x = (60 + i * 61 + tl * 12) % 1030
        y = (120 + (i * 173) % 700 + tl * 42) % 720 + 60
        dot_on(img, x, y, 2.2, mix(V.CAHAYA_AIR, WHITE, 0.65), 0.16 * al)
    # panah migrasi paus berdenyut
    p = 0.5 + 0.5 * math.sin(tl * 1.8)
    ring_on(img, 520, 350, 40 + 8 * p, mix(V.CAHAYA_AIR, WHITE, 0.4), 2.0, 0.12 * al)
    V.kartu2(img, ["RAKSASA KALAH", "OLEH PERUBAHAN"], hl="PERUBAHAN", y=Y_KARTU, fsz=62,
             al=al, dy=dy, tab=accent, kicker="BUKAN SATU SEBAB · 3,6 JUTA TAHUN LALU")
    V.sumber(img, SUMBER_PUNAH, al=al)


# ------------------------------------------------------------------ 8 · LOOP
def _dunia_loop(im):
    V.air(im, 0.0, atas=mix(V.AIR_TERANG, V.AIR_PERMUKAAN, 0.30), bawah=V.AIR_GELAP, seed=64)
    V.sinar(im, 0.8, n=5, kuat=0.18, seed=64)
    V.salju(im, 0.0, n=66, kuat=0.42, seed=64)
    # siluet raksasa jauh di belakang (sama seperti intro, lebih redup)
    V.hiu(im, -300, 700, 1700, tinggi=0.150, tone=mix(AIR_D, AIR_G, 0.40), t=0.0,
          outline=None, mulut=False, insang=False, mata=False)
    # vitrin museum: alas + kaca + gigi
    V.bentuk2(im, [(252, 1246), (828, 1246), (828, 1298), (252, 1298)],
              mix(PASIR_D, AIR_D, 0.55), outline=mix(V.CAHAYA_AIR, WHITE, 0.20), ow=2.6,
              light=0.18, dark=0.22)
    V.bentuk2(im, [(288, 888), (792, 888), (792, 1246), (288, 1246)],
              mix(AIR_G, V.AIR_TENGAH, 0.40), outline=mix(V.CAHAYA_AIR, WHITE, 0.32), ow=3.0,
              light=0.20, dark=0.18)
    # pendar sorot dari atas vitrin
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(S(430), S(892)), (S(650), S(892)), (S(770), S(1240)),
                                 (S(310), S(1240))], fill=(255, 226, 180, 52))
    lay = lay.filter(ImageFilter.GaussianBlur(S(26)))
    im.paste(lay.convert("RGB"), (0, 0), lay)
    V.gigi(im, 540, 1204, 214, rot=0.05, tone=mix(CREAM, PASIR, 0.08))
    V.label2(im, 540, 830, "OTODUS MEGALODON · GIGI FOSIL", fsz=21, tone=mix(AIR_H, INK, 0.05),
             bg=mix(V.CAHAYA_AIR, WHITE, 0.62))
    V.dasar(im, 1720, tone=mix(PASIR_D, AIR_D, 0.55), amp=18, seed=65)
    V.kaustik(im, 0.0, 1640, 1920, kuat=0.05)


def sc_loop(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("loop55", _dunia_loop), (0, 0))
    # sorot vitrin bernapas
    p = 0.5 + 0.5 * math.sin(tl * 1.2)
    ring_on(img, 540, 1104, 152 + 6 * p, mix(AMBER_H, WHITE, 0.35), 2.2, 0.10 + 0.08 * p)
    # partikel debu di dalam sorot
    for i in range(10):
        x = 400 + ((i * 47 + tl * 9) % 280)
        y = 906 + ((i * 83 + tl * 16) % 320)
        dot_on(img, x, y, 2.0, mix(CREAM, WHITE, 0.4), 0.12 * al)
    V.kartu2(img, ["GIGINYA MASIH ADA", "HIUNYA TIDAK"], hl="HIUNYA TIDAK", y=Y_KARTU, fsz=64,
             al=al, dy=dy, tab=accent, kicker="3,6 JUTA TAHUN, TANPA SATU PUN TULANG UTUH")
    V.sumber(img, "Sumber: NHM · koleksi gigi fosil 20-3,6 juta tahun", al=al)


VISUALS = {
    "mega_intro60": sc_intro,
    "mega_skala60": sc_skala,
    "mega_ukur60": sc_ukur,
    "mega_bentuk60": sc_bentuk,
    "mega_gigi60": sc_gigi,
    "mega_gigit60": sc_gigit,
    "mega_punah60": sc_punah,
    "mega_loop60": sc_loop,
}

# ------------------------------------------------------------------ cue kata -> SFX
CUES = {
    "mega_intro60": {"terbesar": ("terbesar", 0.03), "meter": ("meter", 0.12),
                     "gigi": ("gigi", 0.52), "telapak": ("telapak", 0.86)},
    "mega_skala60": {"megalodon": ("Megalodon", 0.02), "dua": ("dua", 0.14), "puluh": ("puluh", 0.18),
                     "tahun": ("tahun", 0.26), "rawan": ("rawan", 0.56), "fosil": ("fosil", 0.63),
                     "giginya": ("giginya", 0.82)},
    "mega_ukur60": {"gigi": ("Gigi", 0.02), "ukuran": ("ukuran", 0.10), "puluh": ("puluh", 0.30),
                    "sembilan": ("sembilan", 0.36), "meter": ("meter", 0.56),
                    "ton": ("ton", 0.84)},
    "mega_bentuk60": {"bentuknya": ("Bentuknya", 0.02), "putih": ("putih", 0.10),
                      "ramping": ("ramping", 0.26), "lemon": ("lemon", 0.34),
                      "sirip": ("sirip", 0.44), "cepat": ("cepat", 0.86)},
    "mega_gigi60": {"bergerigi": ("bergerigi", 0.06), "gergaji": ("gergaji", 0.14),
                    "sentimeter": ("sentimeter", 0.26), "mengganti": ("berganti", 0.40),
                    "puluhan": ("puluhan", 0.58), "ribu": ("ribu", 0.63),
                    "tulang": ("tulang", 0.90)},
    "mega_gigit60": {"gigitan": ("Gigitan", 0.02), "kuat": ("kuat", 0.14),
                     "paus": ("paus", 0.28), "luka": ("luka", 0.44),
                     "ekor": ("ekor", 0.60), "menggigit": ("menggigit", 0.82)},
    "mega_punah60": {"tiga": ("Tiga", 0.02), "hilang": ("hilang", 0.14),
                     "mendingin": ("mendingin", 0.34), "menyempit": ("menyempit", 0.42),
                     "kutub": ("kutub", 0.52), "makanan": ("makanan", 0.62),
                     "beban": ("beban", 0.92)},
    "mega_loop60": {"giginya": ("Giginya", 0.02), "museum": ("museum", 0.18),
                    "hitam": ("hitam", 0.28), "bergerigi": ("bergerigi", 0.34),
                    "muncul": ("muncul", 0.86)},
}

SFX = {
    "mega_intro60": {"terbesar": ("riser", 0.40, 0), "gigi": ("ding", 0.42, 0),
                     "telapak": ("pop", 0.40, 0)},
    "mega_skala60": {"megalodon": ("pop", 0.38, 0), "tahun": ("click", 0.40, 0),
                     "fosil": ("thud", 0.40, 0), "giginya": ("ding", 0.36, 0)},
    "mega_ukur60": {"gigi": ("pop", 0.38, 0), "meter": ("click", 0.40, 0),
                    "ton": ("thud", 0.42, 0)},
    "mega_bentuk60": {"ramping": ("swish", 0.38, 0), "lemon": ("pop", 0.38, 0),
                      "cepat": ("ding", 0.36, 0)},
    "mega_gigi60": {"bergerigi": ("click", 0.40, 0), "sentimeter": ("pop", 0.38, 0),
                    "ribu": ("riser", 0.34, 0), "tulang": ("thud", 0.40, 0)},
    "mega_gigit60": {"kuat": ("thud", 0.44, 0), "paus": ("pop", 0.38, 0),
                     "ekor": ("swish", 0.40, 0), "menggigit": ("click", 0.42, 0)},
    "mega_punah60": {"hilang": ("thud", 0.42, 0), "mendingin": ("swish", 0.38, 0),
                     "kutub": ("pop", 0.38, 0), "beban": ("riser", 0.34, 0)},
    "mega_loop60": {"museum": ("pop", 0.38, 0), "hitam": ("thud", 0.38, 0),
                    "muncul": ("ding", 0.40, 0)},
}
BEATS55 = {k: [] for k in CUES}


def events_v12(sc):
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
    im = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), V.AIR_TENGAH)
    for nama, fn in VISUALS.items():
        sc = {"id": nama.split("60")[0].replace("mega_", ""), "visual": nama, "start": 10.0,
              "dur": 14.0, "trans": "morph", "accent": "#2E7068", "captions": []}
        for tl in (0.0, 0.12, 2.0, 7.0, 13.98):
            fn(im, None, sc, tl, 14.0, 10.0 + tl, (46, 112, 104), 1.0, 0.0)
        assert events_v12(sc), nama
    print(f"selftest ep55: {len(VISUALS)} visual OK ({sum(len(v) for v in CUES.values())} cue, "
          f"{sum(len(v) for v in SFX.values())} SFX)")
