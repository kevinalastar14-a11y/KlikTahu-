#!/usr/bin/env python3
"""mesin_v19_ep55.py — EP55 "Megalodon" dengan bahasa visual KlikTahu LAMA.

Kenapa ada v19
--------------
v16–v18 menggambar semuanya di atas kertas krem dengan outline tinta. Itu terbaca
"buku ilustrasi", bukan "video sains sinematik". Video panjang lama kanal ini
(contoh: "Apa yang Terjadi Kalau Kamu Masuk ke Lubang Hitam") memakai bahasa yang
berbeda dan jauh lebih matang:

  * latar GELAP bergradasi (navy -> hitam) + nebula samar + bintang tiga lapis;
  * satu merek kecil di kiri atas, satu badge babak di kanan atas;
  * bar progres segmen di tepi bawah (emas = babak lewat, cyan = aktif);
  * panel kaca ber-border 1 px berisi grafik batang berlabel;
  * garis pandu (leader line) untuk menjelaskan bagian objek;
  * pill caption berwarna dengan border menyala;
  * objek ber-rim light: bentuk dibaca dari cahaya, bukan dari outline;
  * debu bercahaya, vignette, grain — bukan bidang putih.

v19 memindahkan seluruh episode ke bahasa itu. Yang dipertahankan dari v18:
timing VO (8 babak, 102,76 s), naskah, dan syarat teknis (1080x1920, 60 fps,
frame akhir = frame 0, tanpa musik).

Struktur berkas
---------------
  1. konstanta & palet          : zona tata letak, babak, warna per babak
  2. siapkan()                  : raster SEMUA sprite sekali (merek, badge, pill,
                                  hiu, paus, penyelam, gigi, plinth, LUT, grain)
  3. HUD                        : merek + badge + progres + pill caption + sumber
  4. latar per babak (8)        : fungsi `_latar_*`, dipanggil SEKALI per render
  5. aktor per babak (8)        : fungsi `_aktor_*`, dipanggil tiap frame
  6. tabel SCENES + API         : `daftar()`, `frame(t)`, `siapkan()`
  7. pratinjau                  : `python3 mesin_v19_ep55.py`

Aturan komposisi (dipatuhi semua babak)
---------------------------------------
  y    0–120   : HUD (merek kiri, badge kanan)
  y  260–1000  : visual utama (objek besar)
  y 1000–1290  : visual sekunder / angka besar
  y 1322       : pill caption
  y 1424–1740  : panel kaca (grafik / kartu data)
  y 1802       : baris sumber
  y 1890–1910  : progres segmen
Objek penting tidak boleh masuk 120 px teratas atau 150 px terbawah.
"""
from __future__ import annotations

import math
import os
import sys

import cv2
import numpy as np
from PIL import Image

import mesin_v18_inti as M
import mesin_v19_gelap as G
from mesin_v18_inti import (Kanvas, blit, blit_add, clamp, eio, eo, lerp, mix,
                            seg, smooth, spr_text, tw)

W_, H_ = 1080, 1920
FPS = 60

# ---------------------------------------------------------------- zona tata letak
Y_PIL = 1322
Y_PANEL = 1424
Y_SUMBER = 1802
X_TEPI = 62

# ---------------------------------------------------------------- identitas babak
JUDUL_EP = "Megalodon"
SUMBER_TEKS = "Shimada dkk. 2025 · Palaeontologia Electronica · NHM"

BABAK = [
    ("LAUT PURBA", G.CYAN),
    ("JEJAK WAKTU", G.VIOLET),
    ("UKURAN", G.CYAN),
    ("BENTUK", G.GREEN),
    ("GIGI", G.GOLD),
    ("CARA MAKAN", G.CORAL),
    ("KEPUNAHAN", G.VIOLET),
    ("SISA", G.GOLD),
]

# Pill caption per babak: (teks, warna). Satu ide per layar, <= 7 kata.
PIL = [
    ("HIDUP 24 METER · TERSISA CUMA GIGI", G.CYAN),
    ("20 JUTA TAHUN, LALU HILANG", G.VIOLET),
    ("DIUKUR ULANG 29 AHLI", G.CYAN),
    ("BUKAN HIU PUTIH YANG DIPERBESAR", G.GREEN),
    ("GIGI BERGERIGI 18 CM", G.GOLD),
    ("YANG DISERANG: EKORNYA DULU", G.CORAL),
    ("BUKAN SATU SEBAB", G.VIOLET),
    ("GIGINYA MASIH ADA", G.GOLD),
]

# =============================================================== 2. sprite global

_MEREK = None
_BADGE = []
_PIL_SPR = []
_SRC = None
_HIU = None          # megalodon 980 px
_HIU_SEDANG = None   # megalodon 720 px
_HIU_PUTIH = None    # hiu putih 560 px
_HIU_KECIL = None    # siluet 420 px (kepunahan)
_HIU_KIRI = None     # megalodon 980 px, dicerminkan (berenang ke kiri)
_HIU_TENGAH = None   # megalodon 860 px untuk intro
_HIU_TENGAH_KIRI = None
_PAUS = None
_SELAM = None
_GIGI_BESAR = None
_GIGI_KECIL = None
_DERET = []
_PLINTH = None
_LUT = None
_VIGNETTE = None
_GRAIN_POS = []
_GRAIN_NEG = []
_FRAME0 = None


def _pil_spr(teks, warna, size=34):
    """Pill caption yang menyusut sendiri kalau teksnya terlalu panjang."""
    while size > 22:
        w = tw(teks, M.F_SEMI, size) + 26 * 2 + 26
        if w <= W_ - 2 * X_TEPI - 12:
            break
        size -= 1
    return G.pill_spr(teks, warna=warna, size=size, pad_x=26, pad_y=12)


def siapkan():
    """Raster semua sprite SEKALI. Dipanggil renderer sebelum frame pertama."""
    global _MEREK, _BADGE, _PIL_SPR, _SRC, _HIU, _HIU_SEDANG, _HIU_PUTIH
    global _HIU_KECIL, _HIU_KIRI, _HIU_TENGAH, _HIU_TENGAH_KIRI
    global _PAUS, _SELAM, _GIGI_BESAR, _GIGI_KECIL, _DERET
    global _PLINTH, _LUT, _VIGNETTE, _GRAIN_POS, _GRAIN_NEG, _FRAME0
    if _HIU is not None:
        return

    _MEREK = G.merek("KlikTahu", size=34)
    _BADGE = [G.badge_babak(nama, warna=warna, size=24, nomor=f"{i + 1:02d}")
              for i, (nama, warna) in enumerate(BABAK)]
    _PIL_SPR = [_pil_spr(teks, warna) for teks, warna in PIL]
    _SRC = G.label_kecil(SUMBER_TEKS, G.TEKS_3, 22, tracking=0.6)

    # ---- makhluk. Semua ber-rim light supaya terbaca di latar gelap.
    _HIU = G.hiu_gelap(980, "megalodon", rim_kuat=1.05)
    _HIU_SEDANG = G.hiu_gelap(720, "megalodon", rim_kuat=0.95)
    _HIU_KIRI = np.ascontiguousarray(_HIU[:, ::-1])
    _HIU_TENGAH = G.hiu_gelap(860, "megalodon", rim_kuat=1.0)
    _HIU_TENGAH_KIRI = np.ascontiguousarray(_HIU_TENGAH[:, ::-1])
    _HIU_PUTIH = G.hiu_gelap(560, "putih", warna=(44, 54, 66),
                             perut=(150, 158, 168), rim_warna=(210, 226, 240),
                             rim_kuat=0.8)
    _HIU_KECIL = G.hiu_gelap(420, "megalodon", rim_kuat=0.55,
                             warna=(18, 28, 42), perut=(54, 70, 92),
                             rim_warna=(120, 150, 185))
    _PAUS = G.paus_gelap(560, warna=(38, 54, 80), rim_warna=(176, 220, 255), rim_kuat=1.0)
    _SELAM = G.penyelam_gelap(300)
    _GIGI_BESAR = G.gigi_gelap(520, rim_kuat=0.34)
    _GIGI_KECIL = G.gigi_gelap(150, rim_kuat=0.30)
    _DERET = [G.gigi_gelap(h, rim_kuat=0.28) for h in (120, 150, 180, 150, 120)]
    _PLINTH = G.plinth(560, 120)

    # ---- warna akhir: kontras naik sedikit, saturasi naik, lift biru tipis.
    _LUT = M.lut_grade(kontras=1.07, saturasi=1.10, lift=(1, 2, 5), gamma=1.01)

    yy = np.linspace(-1, 1, H_, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, W_, dtype=np.float32)[None, :]
    r = np.sqrt((xx * 0.82) ** 2 + yy ** 2) / math.sqrt(1 + 0.82 ** 2)
    vig = np.clip((1.0 - 0.30 * np.clip(r, 0, 1) ** 1.7) * 255.0, 0, 255)
    _VIGNETTE = np.repeat(vig.astype(np.uint8)[:, :, None], 3, axis=2)

    # ---- grain: lempeng noise positif/negatif. Ditambahkan dengan cv2.add +
    # cv2.subtract (uint8, ~1 ms tiap operasi) supaya tidak perlu konversi
    # float32 penuh setiap frame (15 ms) — ini penghematan terbesar di render.
    rng = np.random.default_rng(41)
    _GRAIN_POS, _GRAIN_NEG = [], []
    for i in range(3):
        n = rng.normal(0, 3.0, (H_, W_)).astype(np.float32)
        n = cv2.GaussianBlur(n, (0, 0), 0.6)
        pos = np.repeat(np.clip(n, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)
        neg = np.repeat(np.clip(-n, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)
        _GRAIN_POS.append(pos)
        _GRAIN_NEG.append(neg)
    _FRAME0 = None


def _strip_angka(k, y, butir, alpha=1.0, w_total=None):
    """Strip angka kunci: 3-4 kolom (nilai, satuan, label) di dalam satu panel.

    Dipakai untuk mengisi sepertiga bawah frame dengan informasi, bukan ruang
    kosong — pola yang sama dipakai video panjang referensi (angka besar di
    dalam panel kaca).
    """
    w_total = w_total or (W_ - 2 * X_TEPI)
    G.panel(k, X_TEPI, y, w_total, 268, alpha=alpha * 0.95, aksen=butir[0][3],
            fill=(11, 17, 34, 168), garis=(255, 255, 255, 44))
    n = len(butir)
    kol = w_total / n
    for i, (nilai, satuan, label, warna) in enumerate(butir):
        cx = X_TEPI + kol * i + kol / 2
        vs = spr_text(nilai, warna, M.F_BOLD, 96, tracking=-3)
        gr = int(96 * 0.55)
        blit_add(k.a, G.glow_spr(gr, warna, 0.18 * alpha, 2.2),
                 cx - gr, y + 40 + (vs.shape[0] // 2) - gr)
        blit(k.a, vs, cx - vs.shape[1] / 2, y + 34, alpha)
        us = G.label_kecil(satuan.upper(), mix(warna, (255, 255, 255), 0.35), 26,
                           tracking=1.6)
        blit(k.a, us, cx - us.shape[1] / 2, y + 146, alpha * 0.95)
        ls = G.label_kecil(label.upper(), G.TEKS_3, 21, tracking=0.8)
        blit(k.a, ls, cx - ls.shape[1] / 2, y + 196, alpha * 0.85)
        if i:
            cv2.line(k.a, (int(X_TEPI + kol * i), int(y + 46)),
                     (int(X_TEPI + kol * i), int(y + 222)), (70, 82, 110), 1, cv2.LINE_AA)


# =============================================================== 3. HUD

def _hud(k, i, tl, dur):
    """Merek + badge babak + pill caption + sumber + progres segmen."""
    blit(k.a, _MEREK, 40, 40, 0.92)
    b = _BADGE[i]
    blit(k.a, b, W_ - 40 - b.shape[1], 40, 0.95)

    # pill caption: masuk 0,55 s, keluar 0,35 s sebelum babak berakhir
    a = smooth(seg(tl, 0.55, 1.05)) * (1.0 - smooth(seg(tl, dur - 0.35, dur - 0.05)))
    if a > 0.01:
        p = _PIL_SPR[i]
        dy = (1 - eo(seg(tl, 0.55, 1.15))) * 22
        blit(k.a, p, (W_ - p.shape[1]) / 2, Y_PIL + dy, a)

    blit(k.a, _SRC, (W_ - _SRC.shape[1]) / 2, Y_SUMBER, 0.40)
    G.progres_bawah(k, clamp(tl / max(dur, 1e-3)), warna=BABAK[i][1],
                    tinggi=4, segmen=len(BABAK), aktif=i)


def _label(k, teks, x, y, warna=G.TEKS_3, size=24, alpha=1.0, tracking=1.0):
    """Label mikro ber-tracking lebar (gaya HUD referensi)."""
    s = G.label_kecil(teks, warna, size, tracking=tracking)
    blit(k.a, s, x, y, alpha)
    return s.shape[1]


# =============================================================== 4. LATAR

def _dasar_air(k, puncak=(20, 38, 74), dasar=(3, 6, 14), sinar=6, kuat_sinar=0.15):
    """Latar laut dalam: gradasi, berkas cahaya dari permukaan, kabut, plankton."""
    G.kedalaman_air(k, 0, H_, puncak=puncak, dasar=dasar)
    G.berkas_atas(k, 0.0, n=sinar, y0=-40, y1=1560, warna=(150, 214, 255),
                  kuat=kuat_sinar, lebar=(34, 104), miring=0.20)
    G.kabut_bawah(k, 980, H_, warna=(9, 16, 34), kuat=0.92)
    G.bintang(k, n=90, seed=17, y0=140, y1=1100, redup=0.30)


def _latar_intro(k):
    _dasar_air(k, puncak=(24, 46, 88), dasar=(3, 6, 14), sinar=7, kuat_sinar=0.17)
    # gelembung cahaya di kejauhan (bokeh) — kedalaman, bukan hiasan
    for (cx, cy, r, a) in [(150, 760, 60, 0.05), (980, 620, 46, 0.045),
                           (860, 1120, 74, 0.035), (240, 1180, 40, 0.03)]:
        G.pendar(k, cx, cy, r, (120, 200, 255), a, 2.6)


def _latar_waktu(k):
    # babak waktu: ruang, bukan air — bintang + nebula ungu samar
    G.latar_gelap(k, 0, 1400, bintang_n=620, nebula_kuat=0.80, seed=11)
    G.kabut_bawah(k, 900, H_, warna=(10, 14, 34), kuat=0.95)
    G.nebula(k, 900, 1500, 0.55, seed=23)


def _latar_ukur(k):
    _dasar_air(k, puncak=(18, 34, 66), dasar=(3, 6, 15), sinar=5, kuat_sinar=0.13)
    # sorot dari permukaan tepat di atas hiu (panggung ukur)
    G.sorot_spot(k, 520, -80, 760, warna=(170, 220, 255), kuat=0.30, sebar=34)


def _latar_bentuk(k):
    _dasar_air(k, puncak=(16, 32, 62), dasar=(4, 7, 16), sinar=4, kuat_sinar=0.10)
    G.kabut_bawah(k, 1100, H_, warna=(10, 18, 38), kuat=0.80)


def _latar_gigi(k):
    # ruang gelap dengan satu sorot emas: gigi seperti artefak museum
    G.latar_gelap(k, 0, H_, bintang_n=210, nebula_kuat=0.45, seed=31,
                  gradasi=[(0.0, (12, 14, 26)), (0.45, (16, 18, 34)),
                           (1.0, (4, 5, 12))])
    G.sorot_spot(k, 540, -40, 900, warna=(255, 226, 168), kuat=0.34, sebar=40)
    G.kabut_bawah(k, 1200, H_, warna=(9, 10, 20), kuat=0.75)


def _latar_gigit(k):
    _dasar_air(k, puncak=(14, 24, 50), dasar=(2, 4, 10), sinar=3, kuat_sinar=0.08)
    G.pendar(k, 120, 1520, 420, (120, 40, 44), 0.16, 2.4)
    G.pendar(k, 980, 980, 300, (60, 90, 130), 0.10, 2.6)


def _latar_punah(k):
    G.latar_gelap(k, 0, H_, bintang_n=420, nebula_kuat=0.62, seed=47,
                  gradasi=[(0.0, (14, 18, 38)), (0.40, (12, 16, 34)),
                           (1.0, (3, 5, 12))])
    G.kabut_bawah(k, 1150, H_, warna=(8, 12, 26), kuat=0.85)


def _latar_loop(k):
    # museum: lantai gelap memantul, satu sorot vertikal
    G.latar_gelap(k, 0, H_, bintang_n=120, nebula_kuat=0.30, seed=59,
                  gradasi=[(0.0, (10, 12, 22)), (0.50, (13, 16, 28)),
                           (1.0, (3, 4, 10))])
    G.sorot_spot(k, 540, -120, 880, warna=(255, 232, 186), kuat=0.30, sebar=36)
    # pantulan pelat: gradasi lembut, BUKAN garis lantai (garis keras terbaca UI)
    G.kabut_bawah(k, 1300, H_, warna=(9, 11, 20), kuat=0.86)
    G.pendar(k, 540, 1290, 420, (90, 84, 70), 0.10, 2.8)


# =============================================================== 5. AKTOR

def _masuk(t, t0=0.0, d=0.5):
    return smooth(seg(t, t0, t0 + d))


def _keluar(t, dur, d=0.4):
    return 1.0 - smooth(seg(t, dur - d, dur))


def _bob(t, amp=16.0, laju=0.7, fase=0.0):
    return amp * math.sin(t * laju * 2 * math.pi + fase)


def _aktor_intro(k, t, dur):
    """Hiu melintas pelan (hook 0 s) + penyelam pembanding + strip angka kunci."""
    # --- hiu: sudah terlihat sejak frame 0, menghadap kiri, melintas lambat
    p = _masuk(t, 0.0, 0.8)
    x = 104 + 20 * math.sin(t * 0.40) - 7.0 * t
    y = 366 + _bob(t, 15, 0.22)
    sw = M.swim(_HIU_TENGAH_KIRI, amp=14.0, lam=292.0, phase=t * 3.2, ramp=0.44, kuasa=1.6)
    blit(k.a, sw, x, y, 0.97 * p)
    # gelembung di belakang ekor (ekor kini di kanan karena sprite dicerminkan)
    if p > 0.2:
        for i in range(5):
            bx = x + 760 + 20 * i + 8 * math.sin(t * 1.3 + i)
            by = y + 190 + 54 * math.sin(t * 0.8 + i * 0.8) - i * 8
            G.pendar(k, bx, by, 7 + i * 2, (170, 225, 255), 0.09 * p, 2.4)

    # --- penyelam pembanding skala (di bawah kepala hiu)
    a_sel = _masuk(t, 1.1, 0.7)
    sx, sy = 714, 892 + _bob(t, 8, 0.33, 1.0)
    blit(k.a, _SELAM, sx, sy, 0.92 * a_sel)
    G.pendar(k, sx + 28, sy + 60, 70, (150, 220, 255), 0.09 * a_sel, 2.6)
    if a_sel > 0.6:
        G.garis_pandu(k, (sx + 54, sy + 40), "MANUSIA 1,8 M", warna=G.TEKS_2,
                      arah="kanan", size=24, alpha=a_sel, anim=seg(t, 1.5, 2.0),
                      jarak=12)

    # --- angka utama: batas atas 2025
    a_st = _masuk(t, 0.8, 0.6)
    G.stat_besar(k, "24,3", "meter", "BATAS ATAS · 2025", X_TEPI, 986,
                 warna=G.GOLD, size=172, alpha=a_st, anim=a_st)

    # --- gigi kecil melayang (bukti yang tersisa) di sisi kanan
    for i, (gx, gy, gs, ph) in enumerate([(846, 1046, 0.28, 0.0), (930, 1152, 0.19, 1.7)]):
        a_g = _masuk(t, 2.0 + i * 0.35, 0.8) * 0.9
        if a_g <= 0:
            continue
        h, w = _GIGI_BESAR.shape[:2]
        m = cv2.resize(_GIGI_BESAR, (max(1, int(w * gs)), max(1, int(h * gs))),
                       interpolation=cv2.INTER_AREA)
        rot = 10 * math.sin(t * 0.5 + ph)
        Mm = cv2.getRotationMatrix2D((m.shape[1] / 2, m.shape[0] / 2), rot, 1.0)
        m = cv2.warpAffine(m, Mm, (m.shape[1], m.shape[0]), flags=cv2.INTER_LINEAR,
                           borderValue=(0, 0, 0, 0))
        blit(k.a, m, gx, gy + _bob(t, 9, 0.4, ph), a_g)

    # --- strip angka: mengisi sepertiga bawah, bukan ruang kosong
    a_k = _masuk(t, 1.8, 0.7)
    _strip_angka(k, 1436,
                 [("24", "m", "batas atas", G.CYAN),
                  ("18", "cm", "gigi terbesar", G.GOLD),
                  ("20", "juta th", "muncul pertama", G.VIOLET)], alpha=a_k)


def _aktor_waktu(k, t, dur):
    """Garis waktu 20 juta -> 3,6 juta tahun; hiu memudar; gigi jatuh."""
    y_line = 640
    x0, x1 = 120, 960
    # hiu memudar di belakang garis waktu
    a_h = 0.30 * (1.0 - smooth(seg(t, 2.8, 6.0)))
    if a_h > 0.02:
        sw = M.swim(_HIU_SEDANG, amp=12, lam=280, phase=t * 2.6)
        blit(k.a, sw, lerp(-80, 180, eio(seg(t, 0.4, 6.6))), 300, a_h)

    # garis dasar + progres
    prog = eio(seg(t, 0.8, 4.6))
    cv2.line(k.a, (x0, y_line), (int(lerp(x0, x1, prog)), y_line),
             (*G.VIOLET, 255), 3, cv2.LINE_AA)
    cv2.line(k.a, (int(lerp(x0, x1, prog)), y_line), (x1, y_line),
             (70, 80, 110), 2, cv2.LINE_AA)

    # dua simpul
    for (nx, teks, warna, t0) in [(x0 + 34, "20 JUTA TAHUN", G.CYAN, 0.8),
                                  (x1 - 54, "3,6 JUTA TAHUN", G.CORAL, 3.0)]:
        a_n = _masuk(t, t0, 0.5)
        if a_n <= 0:
            continue
        pul = 0.5 + 0.5 * math.sin(t * 2.2 + nx * 0.01)
        G.pendar(k, nx, y_line, 46 + 10 * pul, warna, 0.30 * a_n, 2.2)
        G.cincin(k, nx, y_line, 22 + 6 * pul, warna, 2.4, 0.55 * a_n, glow=0.4)
        G.cincin(k, nx, y_line, 8, warna, 3.0, 0.95 * a_n, glow=0.5)
        s = G.label_kecil(teks, warna, 26, tracking=1.4)
        blit(k.a, s, nx - s.shape[1] / 2, y_line + 44, a_n)

    # penanda bergerak di sepanjang garis (berhenti sebelum simpul terakhir)
    if prog > 0.02:
        mx = lerp(x0, x1 - 74, eio(seg(t, 0.8, 4.6)))
        G.pendar(k, mx, y_line, 34, (220, 210, 255), 0.35, 2.4)
        G.kilau_bintang(k, mx, y_line, 13, (245, 240, 255), 0.9, t * 1.5)

    # gigi jatuh: yang tersisa setelah hiu hilang
    for i in range(7):
        t0 = 2.6 + i * 0.55
        a_g = _masuk(t, t0, 0.4)
        if a_g <= 0:
            continue
        yy = lerp(700, 1180, eio(seg(t, t0, t0 + 3.4)))
        xx = 240 + i * 96 + 22 * math.sin(t * 0.7 + i)
        spr = _GIGI_KECIL
        h, w = spr.shape[:2]
        m = cv2.resize(spr, (int(w * 0.62), int(h * 0.62)), interpolation=cv2.INTER_AREA)
        rot = 20 * math.sin(t * 0.6 + i)
        Mm = cv2.getRotationMatrix2D((m.shape[1] / 2, m.shape[0] / 2), rot, 1.0)
        m = cv2.warpAffine(m, Mm, (m.shape[1], m.shape[0]), flags=cv2.INTER_LINEAR,
                           borderValue=(0, 0, 0, 0))
        blit(k.a, m, xx, yy, a_g * 0.85)

    # panel: apa yang tersisa
    a_p = _masuk(t, 1.4, 0.6)
    if a_p > 0:
        G.panel(k, X_TEPI, Y_PANEL, W_ - 2 * X_TEPI, 300, alpha=a_p * 0.92,
                aksen=G.VIOLET)
        _label(k, "YANG TERSISA DARI TUBUHNYA", X_TEPI + 34, Y_PANEL + 28,
               G.TEKS_3, 24, a_p)
        G.bar_chart(k, X_TEPI + 34, Y_PANEL + 82, W_ - 2 * X_TEPI - 68,
                    [("GIGI", 0.88, "RIBUAN", G.GOLD),
                     ("TULANG RAWAN", 0.06, "NYARIS NOL", G.CORAL)],
                    alpha=a_p, tinggi_bar=32, jarak=92, label_w=300,
                    anim=eio(seg(t, 1.6, 2.6)), ukuran_label=28)


def _bracket(k, x0, x1, y, warna=G.CYAN, tebal=2.6, alpha=1.0, tutup=16):
    """Kurung ukur horizontal (dipakai babak ukuran)."""
    tebal = int(round(tebal))
    cv2.line(k.a, (int(x0), int(y)), (int(x1), int(y)), (*warna[:3], 210), tebal, cv2.LINE_AA)
    for xx in (x0, x1):
        cv2.line(k.a, (int(xx), int(y - tutup)), (int(xx), int(y + tutup)),
                 (*warna[:3], 210), tebal, cv2.LINE_AA)


def _aktor_ukur(k, t, dur):
    """Hiu + tiga kurung ukur bertingkat: 11 m tulang, 16,4 m, batas 24,3 m."""
    a_h = _masuk(t, 0.25, 0.9)
    sx, sy = 96, 430
    sw = M.swim(_HIU, amp=11, lam=330, phase=t * 2.2)
    blit(k.a, sw, sx, sy, 0.97 * a_h)
    lebar = 990 * 0.965

    # kurung 1: tulang belakang 11 m (sepertiga panjang tubuh)
    a1 = _masuk(t, 1.0, 0.5)
    if a1 > 0:
        _bracket(k, sx + 40, sx + lebar * 0.44, 372, G.TEKS_2, 2.2, a1)
        s = G.label_kecil("11 M · TULANG BELAKANG", G.TEKS_2, 22, tracking=1.0)
        blit(k.a, s, sx + 44, 330, a1 * 0.9)

    # kurung 2: 16,4 m (rekonstruksi 2025)
    a2 = _masuk(t, 2.0, 0.5)
    if a2 > 0:
        p = eio(seg(t, 2.0, 3.0))
        _bracket(k, sx + 20, sx + 20 + (lebar * 0.68 + 10) * p, 300, G.CYAN, 2.6, a2)
        s = G.label_kecil("16,4 M · REKONSTRUKSI 2025", G.CYAN, 22, tracking=1.0)
        blit(k.a, s, sx + 24, 258, a2 * 0.95)

    # kurung 3: batas 24,3 m (putus-putus, coral)
    a3 = _masuk(t, 3.4, 0.5)
    if a3 > 0:
        p = eio(seg(t, 3.4, 4.6))
        x_akhir = sx + lebar * 1.0
        xx = sx
        while xx < sx + (x_akhir - sx) * p:
            cv2.line(k.a, (int(xx), 230), (int(min(xx + 14, x_akhir)), 230),
                     (*G.CORAL[:3], 230), 3, cv2.LINE_AA)
            xx += 26
        for xe in (sx, sx + (x_akhir - sx) * p):
            cv2.line(k.a, (int(xe), 214), (int(xe), 246), (*G.CORAL[:3], 230), 3, cv2.LINE_AA)
        s = G.label_kecil("24,3 M · BATAS ATAS", G.CORAL, 22, tracking=1.0)
        blit(k.a, s, sx + lebar - s.shape[1] - 4, 186, a3)

    # angka besar 16,4: diletakkan di bawah perut hiu, rata kanan
    a_st = _masuk(t, 4.0, 0.6)
    G.stat_besar(k, "16,4", "meter", "PANJANG REKONSTRUKSI", 596, 946,
                 warna=G.CYAN, size=146, alpha=a_st, anim=a_st)

    # panel: tiga perkiraan panjang
    a_p = _masuk(t, 1.2, 0.6)
    if a_p > 0:
        G.panel(k, X_TEPI, Y_PANEL, W_ - 2 * X_TEPI, 300, alpha=a_p * 0.92, aksen=G.CYAN)
        _label(k, "PERKIRAAN PANJANG TUBUH", X_TEPI + 34, Y_PANEL + 28, G.TEKS_3, 24, a_p)
        G.bar_chart(k, X_TEPI + 34, Y_PANEL + 82, W_ - 2 * X_TEPI - 68,
                    [("HIU PUTIH", 0.30, "6,1 M", G.TEKS_2),
                     ("SHIMADA 2025", 0.72, "16,4 M", G.CYAN),
                     ("BATAS ATAS", 1.00, "24,3 M", G.CORAL)],
                    alpha=a_p, tinggi_bar=30, jarak=74, label_w=290,
                    anim=eio(seg(t, 1.6, 3.0)), ukuran_label=27)


def _aktor_bentuk(k, t, dur):
    """Perbandingan bentuk: megalodon ramping vs hiu putih yang diperbesar."""
    # --- megalodon di atas
    a1 = _masuk(t, 0.3, 0.8)
    sw = M.swim(_HIU_SEDANG, amp=10, lam=300, phase=t * 2.0)
    blit(k.a, sw, 110 + _bob(t, 10, 0.15), 380, 0.96 * a1)
    if a1 > 0.7:
        G.garis_pandu(k, (300, 470), "TUBUH RAMPING", G.GREEN, arah="kiri", size=24,
                      alpha=a1, anim=seg(t, 1.1, 1.7), jarak=18)
        G.garis_pandu(k, (612, 742), "SIRIP DADA PANJANG", G.CYAN, arah="kanan",
                      size=24, alpha=a1, anim=seg(t, 2.2, 2.8), jarak=18)

    # --- hiu putih di bawah
    a2 = _masuk(t, 2.6, 0.8)
    sw2 = M.swim(_HIU_PUTIH, amp=8, lam=240, phase=t * 2.4)
    blit(k.a, sw2, 132, 1010, 0.94 * a2)
    if a2 > 0.7:
        G.garis_pandu(k, (300, 1090), "HIU PUTIH 6 M", G.TEKS_2, arah="kanan",
                      size=24, alpha=a2, anim=seg(t, 3.2, 3.8), jarak=18)

    # --- pembanding manusia di antara keduanya
    a3 = _masuk(t, 4.6, 0.6)
    if a3 > 0:
        blit(k.a, _SELAM, 812, 840, a3 * 0.9)
        G.garis_pandu(k, (884, 872), "1,8 M", G.GOLD, arah="kanan", size=22,
                      alpha=a3, anim=seg(t, 4.8, 5.4), jarak=12)

    # --- panel: perbandingan panjang (mengisi sepertiga bawah)
    a4 = _masuk(t, 4.2, 0.7)
    if a4 > 0:
        G.panel(k, X_TEPI, Y_PANEL, W_ - 2 * X_TEPI, 300, alpha=a4 * 0.92, aksen=G.GREEN)
        _label(k, "BUKAN HIU PUTIH YANG DIPERBESAR", X_TEPI + 34, Y_PANEL + 26,
               G.TEKS_3, 23, a4)
        G.bar_chart(k, X_TEPI + 34, Y_PANEL + 86, W_ - 2 * X_TEPI - 68,
                    [("MEGALODON", 1.00, "16,4 M", G.GREEN),
                     ("HIU PUTIH", 0.37, "6,1 M", G.TEKS_2)],
                    alpha=a4, tinggi_bar=34, jarak=88, label_w=300,
                    anim=eio(seg(t, 4.4, 5.4)), ukuran_label=28)


def _lensa(k, cx, cy, r, t, alpha=1.0):
    """Lingkaran pembesar: isi gelap, tepi menyala, gigi bergerigi di dalamnya."""
    # isi gelap (menggunakan lingkaran berlapis supaya tidak perlu mask rumit)
    cv2.circle(k.a, (int(cx), int(cy)), int(r), (8, 10, 18), -1, cv2.LINE_AA)
    G.pendar(k, cx, cy, r + 18, (255, 220, 150), 0.16 * alpha, 2.4)
    G.cincin(k, cx, cy, r, (255, 224, 160), 2.6, 0.95 * alpha, glow=0.5)
    G.cincin(k, cx, cy, r + 14, (255, 224, 160), 1.2, 0.35 * alpha, dash=12)
    # gigi bergerigi: deret segitiga naik-turun di dalam lensa
    n = 11
    for i in range(n):
        x0 = cx - r * 0.72 + (i / (n - 1)) * r * 1.44
        y0 = cy + r * 0.30
        hh = r * (0.42 if i % 2 == 0 else 0.30)
        ww = r * 0.10
        pts = np.array([[x0 - ww, y0], [x0, y0 - hh], [x0 + ww, y0]], np.int32)
        cv2.fillPoly(k.a, [pts], (236, 244, 252))
        cv2.polylines(k.a, [pts], True, (255, 226, 160), 1, cv2.LINE_AA)
    # label
    s = G.label_kecil("GERIGI SEPERTI GERGAJI", (255, 224, 160), 20, tracking=0.8)
    blit(k.a, s, cx - s.shape[1] / 2, cy + r + 22, alpha * 0.9)


def _aktor_gigi(k, t, dur):
    """Gigi utama + lensa gerigi + deret gigi + panel hitung."""
    # --- gigi utama, masuk dengan sedikit rotasi
    a_g = _masuk(t, 0.3, 0.8)
    if a_g > 0:
        h, w = _GIGI_BESAR.shape[:2]
        rot = -6 + 3 * math.sin(t * 0.5)
        Mm = cv2.getRotationMatrix2D((w / 2, h / 2), rot, 1.0)
        g = cv2.warpAffine(_GIGI_BESAR, Mm, (w, h), flags=cv2.INTER_LINEAR,
                           borderValue=(0, 0, 0, 0))
        blit(k.a, g, 190, 330 + _bob(t, 12, 0.22), a_g)
        G.pendar(k, 190 + w * 0.5, 330 + h * 0.45, 300, (255, 220, 150), 0.13 * a_g, 2.6)

    # --- dimensi 18 cm di kiri gigi
    a_d = _masuk(t, 1.4, 0.6)
    if a_d > 0:
        x = 132
        y0, y1 = 436, 792
        p = eio(seg(t, 1.4, 2.2))
        cv2.line(k.a, (x, y0), (x, int(lerp(y0, y1, p))), (*G.GOLD[:3], 220), 3, cv2.LINE_AA)
        for yy, sgn in ((y0, 1), (int(lerp(y0, y1, p)), -1)):
            cv2.line(k.a, (x - 12, yy), (x + 12, yy), (*G.GOLD[:3], 220), 3, cv2.LINE_AA)
        G.tulis_pendar(k, "18 CM", x - 46, 812, G.GOLD, 44, pendar_warna=G.GOLD,
                       pendar_kuat=0.3, alpha=a_d)

    # --- lensa gerigi
    a_l = _masuk(t, 3.0, 0.7)
    if a_l > 0:
        _lensa(k, 760, 560, 168, t, a_l)

    # --- deret gigi bawah
    a_r = _masuk(t, 4.2, 0.8)
    if a_r > 0:
        for i, spr in enumerate(_DERET):
            xx = 190 + i * 128
            yy = 1010 + 18 * math.sin(t * 0.8 + i * 0.7)
            blit(k.a, spr, xx, yy, a_r * (0.55 + 0.45 * i / len(_DERET)))

    # --- panel: hitungan gigi
    a_p = _masuk(t, 1.0, 0.7)
    if a_p > 0:
        G.panel(k, X_TEPI, Y_PANEL, W_ - 2 * X_TEPI, 300, alpha=a_p * 0.92, aksen=G.GOLD)
        _label(k, "SATU HIU · SEUMUR HIDUP", X_TEPI + 34, Y_PANEL + 28, G.TEKS_3, 24, a_p)
        G.stat_besar(k, "PULUHAN", "ribu gigi", "GANTI GIGI SEPANJANG HIDUP",
                     X_TEPI + 34, Y_PANEL + 78, warna=G.GOLD, size=104, alpha=a_p,
                     anim=eio(seg(t, 1.2, 2.0)))


def _aktor_gigit(k, t, dur):
    """Paus kecil di atas, megalodon menyerang pangkal ekornya dari bawah."""
    # --- paus: berenang ke kanan (kepala di kanan), sebagian keluar frame
    a_p = _masuk(t, 0.3, 0.9)
    px = 420 + 26 * eio(seg(t, 0, dur))
    py = 470 + _bob(t, 10, 0.18)
    paus = M.gelombang_dada(_PAUS, amp=3.6, lam=210, phase=t * 1.4)
    blit(k.a, paus, px, py, 0.96 * a_p)
    # cahaya dari atas: punggung paus sedikit lebih terang + mata kecil
    if a_p > 0.05:
        G.pendar(k, px + 250, py + 40, 260, (110, 165, 220), 0.09 * a_p, 2.6)
        G.pendar(k, px + 528, py + 96, 12, (210, 240, 255), 0.55 * a_p, 2.0, 0.6)

    # --- megalodon menyerang dari bawah-kiri, menyentak lalu mundur
    serang = eo(seg(t, 1.8, 3.0)) * (1.0 - 0.50 * eo(seg(t, 4.2, 5.8)))
    hx = lerp(-300, -70, serang)
    hy = lerp(1000, 830, serang)
    a_h = _masuk(t, 1.2, 0.7)
    sw = M.swim(_HIU_SEDANG, amp=13, lam=270, phase=t * 3.0)
    blit(k.a, sw, hx, hy, 0.95 * a_h)

    # --- pusat serangan: pangkal ekor paus (ekor di KIRI sprite paus)
    tx, ty = px + 58, py + 158
    a_s = _masuk(t, 2.8, 0.5)
    if a_s > 0:
        G.pendar(k, tx, ty, 96, (255, 120, 110), 0.22 * a_s, 2.2)
        G.cincin(k, tx, ty, 34 + 40 * eio(seg(t, 2.8, 4.0)), G.CORAL, 3.0, 0.7 * a_s, glow=0.5)
        G.cincin(k, tx, ty, 18 + 22 * eio(seg(t, 3.2, 4.4)), G.CORAL_L, 2.0, 0.5 * a_s, glow=0.4)
        # garis pandu turun ke kiri: label di bawah ekor, tidak menimpa badan
        p_anim = eio(seg(t, 2.9, 3.8))
        y_bawah = ty + 118
        cv2.line(k.a, (int(tx), int(ty + 40)), (int(tx), int(lerp(ty + 40, y_bawah, p_anim))),
                 (*G.CORAL[:3], 220), 2, cv2.LINE_AA)
        if p_anim > 0.9:
            cv2.line(k.a, (int(tx), int(y_bawah)), (int(tx - 96), int(y_bawah)),
                     (*G.CORAL[:3], 220), 2, cv2.LINE_AA)
            cv2.circle(k.a, (int(tx), int(ty)), 5, G.CORAL, -1, cv2.LINE_AA)
            s_lab = spr_text("EKOR DULU", G.CORAL, M.F_BOLD, 34, tracking=-0.5)
            blit(k.a, s_lab, tx - 96 - s_lab.shape[1], y_bawah - 50, a_s)
        # busur bekas gigitan di pangkal ekor
        for i in range(3):
            rr = 48 + i * 24
            cv2.ellipse(k.a, (int(tx), int(ty)), (rr, int(rr * 0.42)), -16,
                        200, 330, (255, 140, 130), 2, cv2.LINE_AA)

    # --- label paus: teks kecil tanpa garis (garis sudah dipakai untuk ekor)
    a_m = _masuk(t, 0.8, 0.6)
    if a_m > 0.4:
        s_m = G.label_kecil("PAUS KECIL · MANGSA", G.TEKS_2, 24, tracking=1.2)
        blit(k.a, s_m, px + 330, py + 300, a_m * 0.85)

    # --- kartu penjelasan bekas luka fosil
    a_k = _masuk(t, 5.0, 0.7)
    if a_k > 0:
        G.panel(k, X_TEPI, Y_PANEL, W_ - 2 * X_TEPI, 250, alpha=a_k * 0.9, aksen=G.CORAL)
        _label(k, "BUKTI DARI FOSIL PAUS", X_TEPI + 34, Y_PANEL + 26, G.TEKS_3, 23, a_k)
        s1 = spr_text("LUKA DI PANGKAL EKOR", G.TEKS, M.F_BOLD, 42, tracking=-0.5)
        blit(k.a, s1, X_TEPI + 34, Y_PANEL + 66, a_k)
        s2 = G.label_kecil("MELUMPUHKAN SEBELUM MENGGIGIT", G.TEKS_2, 25, tracking=0.6)
        blit(k.a, s2, X_TEPI + 36, Y_PANEL + 132, a_k * 0.92)


def _aktor_punah(k, t, dur):
    """Dua ketukan: (1) tren + hiu memudar, (2) empat sebab menyala berurutan."""
    # ---------- ketukan 1: tren suhu & hiu memudar
    a1 = _masuk(t, 0.3, 0.8) * (1.0 - smooth(seg(t, 7.4, 8.6)))
    if a1 > 0.01:
        sw = M.swim(_HIU_KECIL, amp=9, lam=230, phase=t * 2.0)
        blit(k.a, sw, lerp(120, 240, eio(seg(t, 0.3, 8.0))), 300, 0.55 * a1)
        # panel tren
        G.panel(k, X_TEPI, 470, W_ - 2 * X_TEPI, 320, alpha=a1 * 0.9, aksen=G.CORAL)
        _label(k, "SUHU SAMUDRA · 20 JUTA -> 3,6 JUTA TAHUN", X_TEPI + 32, 496,
               G.TEKS_3, 22, a1)
        G.garis_tren(k, X_TEPI + 60, 560, W_ - X_TEPI - 60, 700, warna=G.CORAL,
                     tebal=5, alpha=a1, titik=True, bayang=False,
                     anim=eio(seg(t, 1.0, 4.2)))
        for i, (tx, ty, teks, warna) in enumerate(
                [(X_TEPI + 60, 560, "PANAS", G.CORAL_L), (W_ - X_TEPI - 60, 700, "DINGIN", G.CYAN)]):
            s = G.label_kecil(teks, warna, 22, tracking=1.0)
            blit(k.a, s, tx - (0 if i == 0 else s.shape[1]), ty - 44, a1 * 0.9)

    # ---------- ketukan 2: empat sebab
    a2 = _masuk(t, 7.0, 0.7)
    if a2 > 0.01:
        _label(k, "EMPAT TEKANAN SEKALIGUS", X_TEPI, 300, G.TEKS_3, 24, a2)
        kartu = [("salju", "SAMUDRA", "MENDINGIN", G.CYAN),
                 ("gelombang", "LAUT DANGKAL", "MENYEMPIT", G.BLUE),
                 ("paus", "PAUS PINDAH", "KE KUTUB", G.VIOLET),
                 ("hiu", "HIU PUTIH", "BERSAING", G.CORAL)]
        for i, (ik, l1, l2, warna) in enumerate(kartu):
            t0 = 7.2 + i * 0.85
            a_k = _masuk(t, t0, 0.55)
            if a_k <= 0:
                continue
            cx = X_TEPI + (i % 2) * 490
            cy = 380 + (i // 2) * 236
            G.panel(k, cx, cy, 466, 208, alpha=a_k * 0.95, aksen=warna, radius=24,
                    fill=(11, 17, 34, 170), garis=(255, 255, 255, 46))
            ik_s = G.ikon(ik, 86, warna, 4.4)
            blit(k.a, ik_s, cx + 26, cy + 58, a_k * 0.95)
            s1 = spr_text(l1, G.TEKS, M.F_SEMI, 30, tracking=-0.3)
            blit(k.a, s1, cx + 132, cy + 74, a_k)
            s2 = spr_text(l2, warna, M.F_BOLD, 30, tracking=-0.3)
            blit(k.a, s2, cx + 132, cy + 116, a_k)
            # garis penanda bawah
            cv2.line(k.a, (cx + 132, cy + 164), (int(cx + 132 + 120 * a_k), cy + 164),
                     (*warna[:3], 190), 3, cv2.LINE_AA)

        # hiu memudar di belakang kartu (kecil, redup)
        a_g = _masuk(t, 8.0, 1.2) * 0.20 * (1.0 - smooth(seg(t, 13.5, 17.0)))
        if a_g > 0.01:
            sw = M.swim(_HIU_KECIL, amp=8, lam=220, phase=t * 1.6)
            blit(k.a, sw, 330, 1084, a_g)
        # panel tren bawah: mengisi ruang, menegaskan arah perubahan
        a_b = _masuk(t, 8.6, 0.8)
        if a_b > 0:
            G.panel(k, X_TEPI, Y_PANEL, W_ - 2 * X_TEPI, 268, alpha=a_b * 0.92,
                    aksen=G.CYAN, fill=(11, 17, 34, 170), garis=(255, 255, 255, 44))
            _label(k, "SUHU SAMUDRA TURUN TERUS", X_TEPI + 34, Y_PANEL + 26,
                   G.TEKS_3, 23, a_b)
            G.garis_tren(k, X_TEPI + 46, Y_PANEL + 92, X_TEPI + 660, Y_PANEL + 208,
                         warna=G.CYAN, tebal=5, alpha=a_b, titik=True, bayang=False,
                         anim=eio(seg(t, 8.8, 11.0)))
            s_b = G.label_kecil("DINGIN", G.CYAN, 24, tracking=1.4)
            blit(k.a, s_b, X_TEPI + 676, Y_PANEL + 186, a_b * 0.9)
            s_c = G.label_kecil("PANAS", G.CORAL_L, 24, tracking=1.4)
            blit(k.a, s_c, X_TEPI + 46, Y_PANEL + 60, a_b * 0.9)


def _aktor_loop(k, t, dur):
    """Gigi di atas plinth, satu sorot; siluet hiu samar memudar."""
    # siluet hiu di belakang (hampir hilang)
    a_h = _masuk(t, 0.4, 1.4) * (0.17 - 0.09 * smooth(seg(t, 3.0, dur)))
    if a_h > 0.01:
        sw = M.swim(_HIU_KECIL, amp=7, lam=240, phase=t * 1.4)
        blit(k.a, sw, lerp(-60, 60, eio(seg(t, 0, dur))), 330, a_h)

    # plinth + gigi
    a_g = _masuk(t, 0.8, 1.0)
    px = (W_ - _PLINTH.shape[1]) / 2
    py = 1060
    blit(k.a, _PLINTH, px, py, 0.95 * a_g)
    if a_g > 0:
        h, w = _GIGI_BESAR.shape[:2]
        skala = 0.78
        gg = cv2.resize(_GIGI_BESAR, (int(w * skala), int(h * skala)),
                        interpolation=cv2.INTER_AREA)
        rot = 3 * math.sin(t * 0.4)
        Mm = cv2.getRotationMatrix2D((gg.shape[1] / 2, gg.shape[0] / 2), rot, 1.0)
        gg = cv2.warpAffine(gg, Mm, (gg.shape[1], gg.shape[0]),
                            flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        blit(k.a, gg, (W_ - gg.shape[1]) / 2, py - gg.shape[0] + 96, a_g)
        G.pendar(k, W_ / 2, py - gg.shape[0] * 0.6 + 96, 260, (255, 226, 170),
                 0.14 * a_g, 2.6)
        G.garis_pandu(k, (W_ / 2 + 96, py - gg.shape[0] * 0.55 + 96),
                      "SPESIMEN MUSEUM", G.TEKS_2, arah="kanan", size=22,
                      alpha=a_g, anim=seg(t, 1.8, 2.6), jarak=18)

    # teks penutup (di atas pill): dua baris
    a_t = _masuk(t, 2.2, 0.8)
    if a_t > 0:
        s1 = G.label_kecil("HIUNYA TIDAK PERNAH MUNCUL LAGI", G.TEKS_2, 27, tracking=1.6)
        blit(k.a, s1, (W_ - s1.shape[1]) / 2, 1226, a_t * 0.9)


# =============================================================== 6. TABEL BABAK

SCENES = [
    dict(id="intro",  dur=10.65, warna=G.CYAN,   latar=_latar_intro,  aktor=_aktor_intro),
    dict(id="waktu",  dur=11.29, warna=G.VIOLET, latar=_latar_waktu,  aktor=_aktor_waktu),
    dict(id="ukur",   dur=13.88, warna=G.CYAN,   latar=_latar_ukur,   aktor=_aktor_ukur),
    dict(id="bentuk", dur=12.01, warna=G.GREEN,  latar=_latar_bentuk, aktor=_aktor_bentuk),
    dict(id="gigi",   dur=16.40, warna=G.GOLD,   latar=_latar_gigi,   aktor=_aktor_gigi),
    dict(id="gigit",  dur=12.66, warna=G.CORAL,  latar=_latar_gigit,  aktor=_aktor_gigit),
    dict(id="punah",  dur=17.59, warna=G.VIOLET, latar=_latar_punah,  aktor=_aktor_punah),
    dict(id="loop",   dur=8.28,  warna=G.GOLD,   latar=_latar_loop,   aktor=_aktor_loop),
]

TOTAL = sum(s["dur"] for s in SCENES)
MULAI = [0.0]
for _s in SCENES:
    MULAI.append(MULAI[-1] + _s["dur"])

_LATAR_CACHE = {}


def daftar():
    """Metadata untuk renderer: id, durasi, waktu mulai, total."""
    return {"scenes": [{"id": s["id"], "dur": s["dur"], "mulai": MULAI[i]}
                       for i, s in enumerate(SCENES)],
            "total": TOTAL, "fps": FPS}


def latar_scene(i):
    """Bangun latar babak ke-i SEKALI, simpan sebagai ndarray RGB."""
    key = SCENES[i]["id"]
    l = _LATAR_CACHE.get(key)
    if l is None:
        k = Kanvas(W_, H_, G.BG_1)
        SCENES[i]["latar"](k)
        l = k.a
        _LATAR_CACHE[key] = l
    return l


def _grade(k):
    """LUT + vignette + grain. Dipakai semua frame supaya warna konsisten."""
    out = cv2.LUT(k.a, _LUT)
    out = cv2.multiply(out, _VIGNETTE, scale=1.0 / 255.0)
    return out


def _frame0():
    """Frame 0 dihitung sekali lalu dipakai sebagai target loop di akhir."""
    global _FRAME0
    if _FRAME0 is None:
        _FRAME0 = frame(0.0)
    return _FRAME0


def frame(t):
    """Komposisi satu frame RGB (1080x1920) pada waktu global `t` detik."""
    siapkan()
    t = clamp(t, 0.0, TOTAL - 1e-4)
    i = 0
    while i < len(SCENES) - 1 and t >= MULAI[i + 1]:
        i += 1
    s = SCENES[i]
    tl = t - MULAI[i]
    dur = s["dur"]

    # Kanvas dialokasikan tanpa mengisi 6 MB lalu langsung dibuang:
    # `Kanvas(...)` butuh ~8 ms/frame hanya untuk alokasi + fill.
    k = object.__new__(Kanvas)
    k.w, k.h = W_, H_
    k.a = latar_scene(i).copy()
    s["aktor"](k, tl, dur)
    _hud(k, i, tl, dur)
    out = _grade(k)

    # grain halus (lempeng diputar tiap 1/12 detik) -> tidak terlihat statis
    gi = int(t * 12.0) % len(_GRAIN_POS)
    out = cv2.subtract(cv2.add(out, _GRAIN_POS[gi]), _GRAIN_NEG[gi])

    # ---- loop sempurna: 0,9 detik terakhir menyatu ke frame 0
    if i == len(SCENES) - 1:
        f = smooth(seg(tl, dur - 0.9, dur))
        if f > 0.995:
            return _frame0().copy()
        if f > 0.001:
            base = _frame0()
            out = cv2.addWeighted(out, 1.0 - f, base, f, 0.0)
    return out


def naskah():
    """Naskah VO (dipakai QC untuk cek kata kunci per babak) — TIDAK dirender."""
    return [
        "Hiu terbesar yang pernah hidup panjangnya dua puluh empat meter. Yang tersisa "
        "dari tubuhnya cuma gigi, dan giginya sebesar telapak tangan.",
        "Megalodon hidup dua puluh juta sampai tiga koma enam juta tahun lalu. Tulang "
        "rawan tidak menjadi fosil, jadi hampir semua yang kita tahu berasal dari giginya.",
        "Gigi itu memberi ukuran tubuh. Tahun dua ribu dua puluh lima, dua puluh sembilan "
        "ahli menghitung ulang batas masuk akal dua puluh empat koma tiga meter.",
        "Bentuknya bukan hiu putih yang diperbesar. Tubuhnya lebih ramping, seperti hiu "
        "lemon, dengan sirip dada panjang. Raksasa tidak perlu gempal untuk cepat.",
        "Gigi megalodon bergerigi seperti gergaji, panjang sampai delapan belas sentimeter. "
        "Ia berganti gigi sepanjang hidup jadi satu individu meninggalkan puluhan ribu gigi.",
        "Gigitan megalodon jauh lebih kuat dari hiu putih. Mangsanya paus kecil. Dari bekas "
        "luka pada fosil paus ia melumpuhkan ekor dulu baru menggigit bagian lain.",
        "Tiga koma enam juta tahun lalu ia hilang. Bukan satu sebab: samudra mendingin, "
        "laut dangkal menyempit, paus pindah ke kutub, dan hiu putih berebut makanan.",
        "Giginya masih tersimpan di museum, hitam dan bergerigi. Hiu itu sendiri tak pernah "
        "muncul lagi.",
    ]


# =============================================================== 7. PRATINJAU

def _pratinjau():
    import time
    t0 = time.time()
    siapkan()
    print(f"[siapkan] sprite: {(time.time() - t0) * 1000:.0f} ms")
    t1 = time.time()
    for i in range(len(SCENES)):
        latar_scene(i)
    print(f"[latar] {len(SCENES)} babak: {(time.time() - t1) * 1000:.0f} ms")

    waktu = [MULAI[i] + SCENES[i]["dur"] * 0.55 for i in range(len(SCENES))]
    for i, t in enumerate(waktu):
        t2 = time.time()
        for _ in range(3):
            f = frame(t)
        print(f"  {SCENES[i]['id']:7s} {(time.time() - t2) / 3 * 1000:6.2f} ms/frame")
    waktu.append(TOTAL - 0.05)
    waktu.append(2.4)

    os.makedirs("/tmp/v19", exist_ok=True)
    for i, t in enumerate(waktu):
        Image.fromarray(frame(t)).save(f"/tmp/v19/{i:02d}_{t:06.2f}.jpg", quality=90)
    sheet = Image.new("RGB", (360 * 4, 640 * 3), (0, 0, 0))
    for i in range(min(12, len(waktu))):
        im = Image.open(f"/tmp/v19/{i:02d}_{waktu[i]:06.2f}.jpg").resize((360, 640))
        sheet.paste(im, ((i % 4) * 360, (i // 4) * 640))
    sheet.save("/tmp/v19_sheet.jpg", quality=92)
    print("-> /tmp/v19_sheet.jpg")


if __name__ == "__main__":
    _pratinjau()
