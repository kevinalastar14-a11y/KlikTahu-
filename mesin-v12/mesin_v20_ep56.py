#!/usr/bin/env python3
"""mesin_v20_ep56.py — EP56 "Kamu Merasa Jatuh Tepat Sebelum Tidur".

Kenapa episode ini
------------------
Mesin riset kanal (analisis/peringkat_topik.json + PEMETA_PELUANG.md) menaruh
keluarga **mimpi & tidur** di peringkat 1 (skor_views 540,8) dengan permintaan
pencarian yang besar ("kenapa mimpi jatuh", "kenapa badan nyentak saat tidur").
Topik ini:
  * dialami 60-70% orang -> penonton merasa "ini saya";
  * punya jawaban yang memuaskan dalam 10 detik -> hook kuat;
  * tidak menyinggung kesehatan serius -> aman untuk monetisasi;
  * belum pernah dibuat di kanal (Ep25 = mimpi cepat lupa, Ep27 = ngorok).

Struktur 10 babak (satu ide per layar)
--------------------------------------
  1  HOOK      kamar malam, orang tidur, badan menyentak
  2  NAMA      "HYPNIC JERK" muncul sebagai tipografi
  3  SEBARAN   7 dari 10 orang, 1 dari 10 tiap malam
  4  WAKTU     jam + pita tahap tidur
  5  OTAK      batang otak, EEG, garis pandu
  6  PRIMATA   leluhur di dahan, jatuh
  7  TEORI     dua teori dibandingkan
  8  NORMAL    pemicu: kurang tidur, kafein, stres
  9  CEGAH     tiga langkah
 10  PENUTUP   merek + CTA + loop sempurna ke babak 1

API: `siapkan()`, `frame(t)`, `daftar()`, `naskah()`.
Pratinjau: `python3 mesin_v20_ep56.py`
"""
from __future__ import annotations

import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image

import mesin_v18_inti as M
import mesin_v20_cahaya as C
import mesin_v20_makhluk as K
from mesin_v18_inti import (Kanvas, blit, blit_c, clamp, eio, eo, lerp, mix,
                            seg, smooth, spr_text, tw)

W_, H_ = 1080, 1920
FPS = 60
BASE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- identitas
JUDUL = "KAMU MERASA JATUH TEPAT SEBELUM TIDUR"
SUMBER = "Sleep Medicine 2016 · AASM · Univ. Colorado"
BABAK = [
    ("SENTAKAN", C.CYAN),
    ("NAMANYA", C.VIOLET),
    ("SEBARAN", C.GOLD),
    ("WAKTUNYA", C.CYAN),
    ("OTAK", C.VIOLET),
    ("LELUHUR", C.GREEN),
    ("DUA TEORI", C.GOLD),
    ("PEMICU", C.CORAL),
    ("CARA", C.GREEN),
    ("SIMPAN", C.GOLD),
]

# ---------------------------------------------------------------- naskah VO
# Satu baris = satu babak. Dipakai untuk caption karaoke + QC kata.
CAPTION = [
    "MERASA JATUH, LALU BADAN NYENTAK?",
    "ITU PUNYA NAMA: HYPNIC JERK",
    "7 DARI 10 ORANG PERNAH",
    "SELALU DI MENIT-MENIT PERTAMA TIDUR",
    "BATANG OTAK SALAH BACA SINYAL",
    "SISA REFLEKS LELUHUR PRIMATA",
    "DUA TEORI, SATU MEKANISME",
    "KURANG TIDUR · KAFEIN · STRES",
    "TIGA CARA MEMBUATNYA JARANG",
    "INI BUKAN PENYAKIT, CUKUP TIDUR TERATUR",
]
NASKAH = [
    "Pernah merasa seperti jatuh dari ketinggian, lalu tubuh menyentak tepat sebelum tidur? Itu bukan mimpi.",
    "Namanya hypnic jerk. Hampir semua orang pernah mengalaminya, tapi hampir tidak ada yang tahu namanya.",
    "Sekitar tujuh dari sepuluh orang pernah merasakannya. Satu dari sepuluh mengalaminya hampir setiap malam.",
    "Biasanya ini terjadi di menit-menit pertama tidur, saat otot mulai melemas dan napas melambat.",
    "Ketika otot melemas, batang otak salah membaca sinyal, lalu mengirim perintah kejut ke seluruh tubuh.",
    "Salah satu teorinya, ini sisa refleks leluhur primata. Saat jatuh dari dahan, tubuh harus langsung menyambar.",
    "Teori lain, otot yang melemas dibaca otak sebagai tanda jatuh, jadi otak mengejutkan tubuh supaya tidak terjerembap.",
    "Kabar baiknya, ini normal dan bukan penyakit. Yang membuatnya sering hanya kurang tidur, kafein, dan stres.",
    "Kalau ingin lebih jarang, kurangi kopi sore, tidur di jam yang sama, dan jangan begadang semalaman.",
    "Tubuhmu hanya ketinggalan zaman. Ini bukan penyakit, cuma perlu tidur lebih teratur. Simpan videonya.",
]

# ---------------------------------------------------------------- waktu babak
# Durasi babak SELALU berasal dari audio/vo/timing.json (hasil
# mesin_v20_suara.py). Dulu ada cadangan `_DEF_DUR` + syarat "panjangnya 10":
# kalau timing.json berisi 6 babak (varian kilat), syarat itu gagal dan mesin
# diam-diam memakai angka cadangan 75,9 s — render jadi 4554 frame sementara
# audio 79,32 s, tanpa satu pun peringatan. Sekarang: berkas salah atau hilang
# = berhenti dengan pesan jelas, bukan render yang tampak normal tapi keliru.
_DEF_DUR = [7.85, 7.695, 7.97, 7.515, 7.19, 7.975, 8.5, 8.8, 6.95, 8.87]


def _path_timing(varian="penuh"):
    """Timeline INDUK selalu audio/vo/timing.json (10 babak).

    Varian kilat tidak punya timeline sendiri: ia memilih 6 babak dari timeline
    induk lewat _IDX, dan `mesin_v20_suara.py` membangun audionya dari subset
    yang sama. Dulu loading-nya "kalau panjangnya 10 pakai, kalau tidak pakai
    angka cadangan", sehingga saat audio/vo/timing.json tertimpa timing 6 babak,
    mesin diam-diam merender 75,9 s padahal audionya 79,3 s — video tampak
    normal, durasi salah. Sekarang kondisi itu berhenti dengan pesan jelas.
    """
    sub = "vo" if varian == "penuh" else f"vo_{varian}"
    return os.path.join(BASE, "audio", sub, "timing.json")


def _muat_durasi():
    p = _path_timing("penuh")
    if not os.path.exists(p):
        raise RuntimeError(
            f"timeline induk tidak ada: {p}\n"
            "jalankan dulu: python3 mesin_v20_suara.py --episode mesin_v20_ep56 "
            "--dari-klip audio/vo/sumber --keluar keluaran/KlikTahu_Ep56_audio.m4a"
        )
    dur = [float(x) for x in json.load(open(p))["dur"]]
    if len(dur) != len(_DEF_DUR):
        raise RuntimeError(
            f"{p} berisi {len(dur)} babak, seharusnya {len(_DEF_DUR)}. "
            "Berkas ini tertimpa timing varian lain — bangun ulang audio penuh."
        )
    return dur


# Varian keluaran. "penuh" = 10 babak (79,3 s) untuk penonton yang sudah kenal
# kanal; "kilat" = 6 babak (~45 s) untuk uji jangkauan feed — data 2026
# menunjukkan pita 22-45 s punya retensi & loop terbaik. Varian "kilat" punya
# audio/vo_kilat/timing.json sendiri; jangan pernah berbagi folder timing.
VARIAN = {
    "penuh": ["hook", "nama", "sebaran", "waktu", "otak", "primata", "teori",
              "pemicu", "cara", "penutup"],
    "kilat": ["hook", "nama", "sebaran", "otak", "teori", "penutup"],
}
_VAR = os.environ.get("KT_VARIAN", "penuh")
if _VAR not in VARIAN:
    _VAR = "penuh"
PILIH = VARIAN[_VAR]

ALL_IDS = ["hook", "nama", "sebaran", "waktu", "otak", "primata", "teori",
           "pemicu", "cara", "penutup"]

_DUR_INDUK = _muat_durasi()          # 10 babak, sumber kebenaran
DUR = list(_DUR_INDUK)
_IDX = [ALL_IDS.index(v) for v in PILIH]
DUR = [DUR[i] for i in _IDX]
# Cek silang: audio varian kilat dibangun dari subset babak yang sama. Kalau
# angka di audio/vo_kilat/timing.json tidak lagi cocok dengan timeline induk,
# caption & panel akan bergeser -> hentikan sekarang, jangan render.
def _cek_timing_varian():
    for nama, pilih in VARIAN.items():
        p = _path_timing(nama)
        if not os.path.exists(p):
            continue
        dur_v = [float(x) for x in json.load(open(p))["dur"]]
        harus = [_DUR_INDUK[ALL_IDS.index(v)] for v in pilih]
        if len(dur_v) != len(harus):
            raise RuntimeError(
                f"{p}: {len(dur_v)} babak, varian '{nama}' butuh {len(harus)}"
            )
        for i, (a, b) in enumerate(zip(dur_v, harus)):
            if abs(a - b) > 0.02:
                raise RuntimeError(
                    f"{p} babak {i + 1}: {a:.2f} s != {b:.2f} s di timeline induk. "
                    "Bangun ulang audio varian itu."
                )


_cek_timing_varian()

MULAI = [0.0]
for d in DUR[:-1]:
    MULAI.append(MULAI[-1] + d)
TOTAL = sum(DUR)

# ---------------------------------------------------------------- zona layout
# Zona tata letak v20 (1080x1920). Isi memakai 190-1180: hampir setengah layar,
# karena pratinjau v19 menunjukkan banyak ruang kosong di tengah.
Y_KONTEN = (190, 1150)
Y_CAPTION = 1256
Y_SCRIM = (1120, 1420)
Y_PANEL_BAWAH = 1416
Y_SUMBER = 1806

_GLYPH = {}
_LUT = None
_FRAME0 = None


# ================================================================ siapkan
def siapkan():
    global _LUT, _GLYPH
    if _LUT is not None:
        return
    _LUT = C.grade_lut()
    _GLYPH = {}


# ================================================================ util babak
def _masuk(t, d=0.55, jeda=0.0):
    return smooth(clamp((t - jeda) / d))


def _keluar(t, dur, d=0.45):
    return 1.0 - smooth(clamp((t - (dur - d)) / d))


def _bob(t, amp=12.0, laju=0.9, fasa=0.0):
    return math.sin(t * laju + fasa) * amp


def _isi(k, x0, y0, x1, y1, warna, alpha=255):
    C._isi(k, x0, y0, x1, y1, warna, alpha)


def _tag(k, t, tl, dur, warna):
    """Label kecil kanan atas isi babak (bukan HUD)."""
    a = _masuk(tl, 0.5, 0.15) * _keluar(tl, dur, 0.4)
    C.label_kecil(k, f"{JUDUL}", 62, 224, C.TEKS_3, 20, 0.5 * a, "kiri", 2.6)


def _p(k, tl, warna, x=62, y=Y_SUMBER - 4):
    pass


# ================================================================ 1. HOOK
def _latar_kamar(k):
    C.latar_kamar_lengkap(k)
    return k


def _aktor_hook(k, t, dur):
    """Kamar malam; orang tidur; pada t=0.62*dur badan menyentak (puncak hook)."""
    sentak = 0.62 * dur
    kaget = t >= sentak
    j = 0.0
    if kaget:
        dt = t - sentak
        j = math.exp(-dt * 7.0) * math.sin(dt * 34.0)
        if dt < 0.22:
            f = 1.0 - dt / 0.22
            C.kilat(k, 540, 860, 1000, (205, 225, 255), 0.5 * f)

    masuk = _masuk(t, 0.9)
    dy = int(lerp(90, 0, masuk))
    # ---- tempat tidur
    kas = K.kasur(1080, 400)
    blit(k.a, kas, 0, 950 + dy)

    # ---- orang tidur (kepala di atas bantal)
    sp = K.orang_tidur(1.72, "kaget" if kaget else "tutup")
    skala = 560.0 / sp.shape[1]
    sp2 = cv2.resize(sp, (int(sp.shape[1] * skala), int(sp.shape[0] * skala)),
                     interpolation=cv2.INTER_AREA)
    bx = int(520 + j * 30)
    by = int(1046 - sp2.shape[0] + 120 + dy + j * 34)
    blit(k.a, sp2, bx, by)
    # napas: cincin halus dari hidung
    if not kaget:
        # napas: lengkung halus di depan mulut (bukan cincin di wajah)
        for i2 in range(3):
            f = ((t * 0.7 + i2 * 0.33) % 1.0)
            a2 = (1 - f) * 0.5
            C.pendar(k, bx - 6 - f * 46, by + 128 - f * 24, int(12 + f * 26),
                     (150, 200, 255), a2 * 0.35, 2.4)
    # ---- selimut
    sel = K.selimut_bergelombang(820, 260, t * 1.3)
    blit(k.a, sel, 120, 1060 + dy)
    # ---- debu
    C.bokeh(k, _DEBU, t, 1.0, (0, 0), 0.55)
    # ---- sentakan
    if kaget and t - sentak < 0.6:
        f = 1.0 - (t - sentak) / 0.6
        # gelombang kejut: mulai di luar kepala (jangan menutupi mata) lalu melebar
        C.cincin(k, bx + 128, by + 96, int(150 + (1 - f) * 330), (255, 255, 255),
                 2.0, alpha=f * 0.34, glow=0.8)
        C.flare_anamorfik(k, 540, 820, int(320 + (1 - f) * 500), (190, 225, 255), f * 0.8, 10)
        # tanda sentak: bintang ledak di atas kepala
        C.kilat(k, bx + 200, by - 20, int(120 + (1 - f) * 180), (255, 240, 214), f * 0.8)
    # ---- label kamar
    a = _masuk(t, 0.6, 0.4)
    C.label_kecil(k, "02:14 · KAMAR TIDUR", 62, 214, C.TEKS_3, 22, a, "kiri", 3.0)


_DEBU = None
_FRAME0_NOCAP = None


def _siap_debu():
    global _DEBU
    if _DEBU is None:
        r = M.rng(56)
        _DEBU = np.stack([r.uniform(0, W_, 80), r.uniform(0, H_, 80),
                          r.uniform(2, 8, 80), r.uniform(0, 6.28, 80),
                          r.uniform(0.2, 1.0, 80)], 1)
    return _DEBU


def _latar_hook(k):
    C.latar_kamar_lengkap(k)
    return k


# ================================================================ 2. NAMA
def _latar_nama(k):
    C.latar_jatuh(k)
    return k


def _aktor_nama(k, t, dur):
    """Tipografi: HYPNIC JERK + figur jatuh di belakang."""
    fj = K.figur(430, "jatuh")
    sc = 0.9
    fs = cv2.resize(fj, (int(fj.shape[1] * sc), int(fj.shape[0] * sc)), interpolation=cv2.INTER_AREA)
    blit(k.a, fs, 640, int(300 + _bob(t, 22, 0.8) - t * 14), 0.50)
    r = M.rng(7)
    for i2 in range(18):
        x = r.uniform(40, W_ - 40)
        y = (r.uniform(0, H_) + t * r.uniform(800, 1700)) % (H_ + 220) - 110
        L = int(r.uniform(50, 170))
        lap = np.zeros((L + 2, 5, 4), np.uint8)
        lap[..., :3] = (170, 210, 255)
        lap[..., 3] = np.linspace(0, 200, L + 2)[::-1, None].astype(np.uint8)
        blit(k.a, lap, int(x), int(y))

    C.tulis_wipe(k, "KAMU MERASA", W_ / 2, 596, (t - 0.1) / 0.5, C.TEKS, 80, M.F_BOLD,
                 1.0, "tengah", "kiri", C.CYAN_L)
    C.tulis_wipe(k, "JATUH", W_ / 2, 722, (t - 0.32) / 0.45, C.CYAN, 150, M.F_BOLD,
                 2.0, "tengah", "tengah", C.PUTIH)
    aa = _masuk(t, 0.6, 0.95)
    if aa > 0:
        C.panel(k, 130, 950, 820, 158, aa, aksen=C.VIOLET, radius=28)
        C.label_kecil(k, "NAMA ILMIAHNYA · SLEEP START", 540, 968, C.TEKS_3, 20, aa, "tengah", 2.8)
        C.tulis(k, "HYPNIC JERK", 540, 1002, C.VIOLET_L, 56, M.F_BOLD, 1.4, aa, True, "tengah")


# ================================================================ 3. SEBARAN
def _latar_sebaran(k):
    C.latar_otak(k, 8)
    return k


def _aktor_sebaran(k, t, dur):
    """Piktogram 7/10 + dua kartu angka (mengisi 190-1180)."""
    a0 = _masuk(t, 0.6)
    C.label_kecil(k, "SEBERAPA UMUM?", 62, 200, C.TEKS_2, 26, a0, "kiri", 3.0)

    C.panel(k, 62, 250, 956, 560, _masuk(t, 0.6, 0.1), aksen=C.GOLD, radius=30)
    C.label_kecil(k, "10 ORANG DEWASA", 108, 288, C.TEKS_3, 23, a0, "kiri", 2.6)
    p = _masuk(t, 1.0, 0.30)
    C.piktogram(k, 122, 352, 10, 4, 0.7, C.GOLD, p, r=18, jarak=98)
    C.label_kecil(k, "7 PERNAH MERASAKAN", 108, 748, C.GOLD, 28, _masuk(t, 0.8, 1.15), "kiri", 2.4)
    C.label_kecil(k, "3 TIDAK / LUPA", 966, 750, C.TEKS_3, 23, _masuk(t, 0.8, 1.15), "kanan", 2.0)

    a2 = _masuk(t, 0.7, 0.9)
    C.panel(k, 62, 846, 462, 300, a2, aksen=C.CYAN, radius=26)
    C.tulis(k, "70%", 100, 878, C.GOLD, 108, M.F_BOLD, 0.0, a2)
    C.label_kecil(k, "PERNAH SEKALI SEUMUR HIDUP", 100, 1050, C.TEKS_2, 20, a2, "kiri", 2.2)
    C.panel(k, 556, 846, 462, 300, a2, aksen=C.CORAL, radius=26)
    C.tulis(k, "10%", 594, 878, C.CORAL, 108, M.F_BOLD, 0.0, a2)
    C.label_kecil(k, "MENGALAMI TIAP MALAM", 594, 1050, C.TEKS_2, 20, a2, "kiri", 2.2)


# ================================================================ 4. WAKTU
def _latar_waktu(k):
    C.latar_otak(k, 12)
    C.berkas(k, 320, 0, 1400, 70, 300, (120, 180, 255), 0.13, 0.0, 0.4)
    C.berkas(k, 780, 0, 1400, 46, 220, (150, 210, 255), 0.10, 0.0, 2.1)
    return k


def _aktor_waktu(k, t, dur):
    """Jam besar + pita tahap tidur (N1 -> N2) + penanda sentakan."""
    a = _masuk(t, 0.7, 0.05)
    r = 232
    cx, cy = 430, 560
    if a > 0:
        C.pendar(k, cx, cy, 360, (110, 160, 255), 0.28 * a, 2.4)
        blit_c(k.a, K.jam(r), cx, cy, a)
        blit_c(k.a, K.jarum_jam_spr(r, 360 * (t / max(1.0, dur)) + 40, 0.62,
                                    (255, 255, 255), 0.038), cx, cy, a)
        blit_c(k.a, K.jarum_jam_spr(r, 30 + t * 12, 0.82, C.CYAN, 0.024), cx, cy, a)
        C.cincin(k, cx, cy, int(r * (1.07 + 0.02 * math.sin(t * 3))), C.CYAN, 2.0, 0.30 * a, glow=0.6)

    b = _masuk(t, 0.6, 0.35)
    C.label_kecil(k, "MENIT KE", 790, 452, C.TEKS_2, 26, b, "kiri", 3.0)
    C.tulis(k, "1 – 5", 790, 486, C.GOLD, 96, M.F_BOLD, 1.0, b, True, "kiri")
    C.label_kecil(k, "SETELAH KEPALA", 790, 618, C.TEKS_3, 22, b, "kiri", 2.2)
    C.label_kecil(k, "MENYENTUH BANTAL", 790, 654, C.TEKS_3, 22, b, "kiri", 2.2)

    # ---- pita tahap tidur
    yy = 940
    C.label_kecil(k, "TAHAP TIDUR", 62, yy - 96, C.TEKS_2, 24, _masuk(t, 0.6, 0.6), "kiri", 3.0)
    p = _masuk(t, 1.0, 0.7)
    x0, x1 = 62, 1018
    segs = [("BANGUN", 0.0, 0.22, C.TEKS_2), ("N1 · MELEMAS", 0.22, 0.62, C.CYAN),
            ("N2 · RINGAN", 0.62, 1.0, C.VIOLET)]
    for nama, f0, f1, warna in segs:
        xa = int(x0 + (x1 - x0) * f0)
        xb = min(int(x0 + (x1 - x0) * f1), int(x0 + (x1 - x0) * p))
        if xb > xa:
            _isi(k, xa, yy, xb, yy + 22, warna, 215)
            _isi(k, xa, yy, xb, yy + 5, mix(warna, (255, 255, 255), 0.45))
        if p > f0:
            C.label_kecil(k, nama, int(x0 + (x1 - x0) * f0), yy - 42, warna, 21, p, "kiri", 2.2)
    if p > 0.4:
        xj = int(x0 + (x1 - x0) * 0.33)
        fl = 0.6 + 0.4 * math.sin(t * 8)
        C.pendar(k, xj, yy + 11, 70, C.CORAL, 0.55 * fl, 2.0)
        C.cincin(k, xj, yy + 11, 30, C.CORAL, 3.0, 0.9, glow=0.7)
        C.tulis(k, "SENTAKAN DI SINI", xj, yy + 52, C.CORAL, 30, M.F_BOLD, 1.4, p, True, "tengah")
    C.label_kecil(k, "OTOT PALING CEPAT MELEMAS DI FASE N1", 540, 1052, C.TEKS_3, 20,
                  _masuk(t, 0.6, 1.3), "tengah", 2.2)


# ================================================================ 5. OTAK
def _latar_otak(k):
    C.latar_otak(k, 3)
    C.berkas(k, 500, 0, 1500, 100, 360, (140, 190, 255), 0.14, 0.0, 1.2)
    return k


def _aktor_otak(k, t, dur):
    """Otak besar + batang otak menyala + panel EEG + penjelasan."""
    a = _masuk(t, 0.8, 0.05)
    ob = K.otak(830, sorot="batang")
    if a > 0:
        C.pendar(k, 500, 510, 470, (120, 150, 255), 0.26 * a, 2.6)
        blit_c(k.a, ob, 500, 500 + _bob(t, 10, 0.7), a)
    gp = _masuk(t, 0.7, 1.0)
    if gp > 0:
        C.garis_pandu(k, (652, 646), "BATANG OTAK", C.GOLD, "kanan", 26, gp, gp)
    # kartu penjelasan + panah
    a2 = _masuk(t, 0.7, 1.35)
    if a2 > 0:
        C.panel(k, 62, 792, 956, 184, a2, aksen=C.GOLD, radius=26)
        C.tulis(k, "OTOT MELEMAS", 100, 818, C.TEKS, 38, M.F_BOLD, 1.2, a2)
        C.label_kecil(k, "SINYAL DIBACA OTAK SEBAGAI", 100, 874, C.TEKS_3, 21, a2, "kiri", 2.2)
        C.tulis(k, "SEDANG JATUH", 100, 900, C.CORAL, 50, M.F_BOLD, 1.6, a2)
        C.panah(k, 668, 850, "kanan", C.GOLD, 56, a2)
        C.tulis(k, "KEJUT", 772, 852, C.GOLD, 38, M.F_BOLD, 1.4, a2)
        C.label_kecil(k, "REFLEKS PALING PURBA", 772, 904, C.TEKS_3, 19, a2, "kiri", 1.6)
    # EEG
    C.panel(k, 62, 998, 956, 170, _masuk(t, 0.7, 1.6), aksen=C.VIOLET, radius=26)
    C.label_kecil(k, "AKTIVITAS LISTRIK OTAK", 100, 1022, C.TEKS_3, 21,
                  _masuk(t, 0.7, 1.7), "kiri", 2.4)
    if t > 1.6:
        C.eeg(k, 100, 1048, 880, 104, t, C.VIOLET, 1.0, 6.0)


# ================================================================ 6. PRIMATA
def _latar_primata(k):
    C.latar_langit(k, 3)
    return k


def _aktor_primata(k, t, dur):
    """Dahan + primata + figur jatuh (tiga lapisan parallax)."""
    a = _masuk(t, 0.9, 0.05)
    blit(k.a, K.dahan(1080), 0, 330, a)
    pr = K.primata(360)
    blit_c(k.a, pr, 296, 396 + pr.shape[0] / 2 - _bob(t, 7, 1.1), a)
    fj = K.figur(400, "jatuh")
    fy = 560 + max(0.0, (t - 1.1)) * 210
    fj2 = fj
    if t > 1.1:
        s2 = 1.0 - min(0.4, (t - 1.1) * 0.07)
        fj2 = cv2.resize(fj, (int(fj.shape[1] * s2), int(fj.shape[0] * s2)), interpolation=cv2.INTER_AREA)
    blit(k.a, fj2, 700, int(fy), 0.92 * a)
    if t > 1.1:
        for i2 in range(7):
            yy = int(fy - 40 - i2 * 44)
            ww = int(80 - i2 * 9)
            _isi(k, 780 - ww // 2, yy, 780 + ww // 2, yy + 3, (170, 210, 255), max(0, 70 - i2 * 9))
    b = _masuk(t, 0.7, 0.55)
    C.tulis(k, "LELUHUR KITA", 62, 846, C.TEKS, 46, M.F_BOLD, 1.4, b)
    C.tulis(k, "TIDUR DI DAHAN", 62, 900, C.GREEN, 60, M.F_BOLD, 1.4, b)
    C.label_kecil(k, "JATUH DARI POHON = MATI", 62, 1000, C.TEKS_3, 22, b, "kiri", 2.0)
    c = _masuk(t, 0.7, 1.5)
    if c > 0:
        C.panel(k, 62, 1018, 956, 88, c, aksen=C.GREEN, radius=24)
        C.tulis(k, "REFLEKS PRIMATA PURBA", 100, 1030, C.TEKS, 34, M.F_BOLD, 1.2, c)
        C.label_kecil(k, "BELUM TERBUKTI", 982, 1056, C.CORAL, 19, c, "kanan", 1.8)


# ================================================================ 7. TEORI
def _latar_teori(k):
    C.latar_otak(k, 21)
    return k


def _aktor_teori(k, t, dur):
    """Dua teori dibandingkan + kesepakatan ahli."""
    a = _masuk(t, 0.6, 0.05)
    C.label_kecil(k, "DUA PENJELASAN", 62, 200, C.TEKS_2, 26, a, "kiri", 3.0)
    for i2, (judul, isi, warna, y) in enumerate((
            ("OTAK SALAH BACA", ["OTOT MELEMAS »", "DIBACA JATUH » KEJUT"], C.CYAN, 250),
            ("SINYAL BERTABRAKAN", ["BATANG OTAK & KORTEKS", "TIDAK MATI BERSAMAAN"], C.VIOLET, 570))):
        aa = _masuk(t, 0.7, 0.15 + i2 * 0.35)
        if aa <= 0:
            continue
        C.panel(k, 62, y, 956, 290, aa, aksen=warna, radius=28)
        C.tulis(k, f"0{i2 + 1}", 100, y + 28, warna, 38, M.F_BOLD, 1.0, aa, False)
        C.tulis(k, judul, 100, y + 82, C.TEKS, 50, M.F_BOLD, 1.4, aa)
        for j2, baris in enumerate(isi):
            C.label_kecil(k, baris, 100, y + 162 + j2 * 40, C.TEKS_2, 26, aa, "kiri", 1.4)
        icx, icy = 880, y + 145
        if i2 == 0:
            C.cincin(k, icx, icy, 66, warna, 3.0, 0.8 * aa, glow=0.6)
            C.panah(k, icx - 37, icy - 37, "bawah", warna, 52, aa)
        else:
            for k2 in range(3):
                C.cincin(k, icx, icy, 24 + k2 * 22, warna, 2.0, (0.7 - k2 * 0.18) * aa, glow=0.5)
            C.tulis(k, "≠", icx - 22, icy - 32, warna, 50, M.F_BOLD, 0, aa, False, "kiri")
    b = _masuk(t, 0.7, 1.3)
    if b > 0:
        C.panel(k, 62, 884, 956, 218, b, aksen=C.GOLD, radius=28)
        C.label_kecil(k, "YANG DISEPAKATI SEMUA AHLI", 100, 900, C.TEKS_3, 21, b, "kiri", 2.4)
        C.tulis(k, "BUKAN PENYAKIT", 100, 928, C.GREEN, 66, M.F_BOLD, 1.4, b)
        C.label_kecil(k, "VARIAN NORMAL DALAM ICDS-3 · TIDAK MERUSAK SARAF", 100, 1040,
                      C.TEKS_2, 22, b, "kiri", 1.8)
        C.label_kecil(k, "BUKAN GEJALA PARKINSON JIKA SENDIRIAN", 100, 1070,
                      C.TEKS_3, 20, b, "kiri", 1.6)


# ================================================================ 8. PEMICU
def _latar_pemicu(k):
    C.latar_otak(k, 31)
    return k


def _aktor_pemicu(k, t, dur):
    """Empat pemicu dengan batang perbandingan + catatan penting."""
    a = _masuk(t, 0.6, 0.05)
    C.label_kecil(k, "YANG BIKIN LEBIH SERING", 62, 200, C.TEKS_2, 26, a, "kiri", 3.0)
    C.tulis(k, "BUKAN MASALAH SERIUS.", 62, 240, C.TEKS, 44, M.F_BOLD, 1.2, a)
    C.tulis(k, "CUMA KEBIASAAN.", 62, 292, C.CORAL, 44, M.F_BOLD, 1.2, a)
    baris = [("KURANG TIDUR", 0.92, "≤ 5 JAM"),
             ("KAFEIN SORE", 0.68, "> 2 GELAS"),
             ("STRES & CEMAS", 0.55, "TINGGI"),
             ("JAM TIDUR ACAK", 0.41, "TIDAK TERATUR")]
    p = _masuk(t, 1.0, 0.3)
    C.panel(k, 62, 388, 956, 480, _masuk(t, 0.6, 0.12), aksen=C.CORAL, radius=28)
    C.grafik_batang(k, 104, 438, 760, baris, p, 28, 98, C.CORAL, 240, True)
    b = _masuk(t, 0.7, 1.25)
    if b > 0:
        C.panel(k, 62, 900, 956, 210, b, aksen=C.GOLD, radius=28)
        C.label_kecil(k, "CATATAN PENTING", 100, 916, C.TEKS_3, 21, b, "kiri", 2.4)
        C.tulis(k, "SERING SENTAK + NGANTUK BERAT", 100, 944, C.GOLD, 34, M.F_BOLD, 1.0, b)
        C.label_kecil(k, "BISA JADI TANDA KURANG TIDUR KRONIS ATAU APNEA.", 100, 1002,
                      C.TEKS_2, 21, b, "kiri", 1.6)
        C.label_kecil(k, "KONSULTASI KALAU TERJADI HAMPIR TIAP MALAM.", 100, 1032,
                      C.TEKS_3, 21, b, "kiri", 1.6)
        C.label_kecil(k, "BUKAN DIAGNOSIS · INFORMASI UMUM", 100, 1066,
                      C.TEKS_3, 19, b, "kiri", 1.6)


# ================================================================ 9. CARA
def _latar_cara(k):
    C.latar_otak(k, 41)
    C.berkas(k, 540, 0, 1300, 150, 420, (110, 220, 180), 0.10, 0.0, 0.7)
    return k


def _aktor_cara(k, t, dur):
    """Tiga langkah berurutan, masing-masing dengan centang."""
    a = _masuk(t, 0.6, 0.05)
    C.label_kecil(k, "CARA MEMBUATNYA JARANG", 62, 200, C.TEKS_2, 26, a, "kiri", 3.0)
    langkah = [("KOPI TERAKHIR", "SEBELUM JAM 2 SIANG", C.GOLD),
               ("JAM TIDUR SAMA", "BANGUN DI JAM YANG SAMA", C.CYAN),
               ("RITUAL 10 MENIT", "REDUP · DINGIN · TANPA LAYAR", C.GREEN)]
    for i2, (judul, sub, warna) in enumerate(langkah):
        aa = _masuk(t, 0.6, 0.15 + i2 * 0.42)
        if aa <= 0:
            continue
        y = 256 + i2 * 300
        C.panel(k, 62, y, 956, 262, aa, aksen=warna, radius=28)
        C.tulis(k, f"0{i2 + 1}", 100, y + 62, warna, 86, M.F_BOLD, 0.0, aa * 0.95, False)
        C.tulis(k, judul, 262, y + 62, C.TEKS, 52, M.F_BOLD, 1.4, aa)
        C.label_kecil(k, sub, 262, y + 142, C.TEKS_2, 24, aa, "kiri", 2.0)
        cx = 946
        C.cincin(k, cx, y + 131, 38, warna, 2.6, 0.9 * aa, glow=0.6)
        if aa > 0.55:
            lap = np.zeros((90, 90, 4), np.uint8)
            cv2.polylines(lap, [np.array([(26, 46), (39, 60), (64, 28)], np.int32)],
                          False, (*warna, 255), 5, cv2.LINE_AA)
            blit(k.a, lap, cx - 45, y + 86)
    b = _masuk(t, 0.7, 1.55)
    if b > 0:
        C.tulis(k, "MASIH SERING? CEK JAM TIDURMU,", 540, 1058, C.TEKS, 34, M.F_BOLD, 1.2, b, True, "tengah")
        C.tulis(k, "BUKAN OBATNYA.", 540, 1104, C.GREEN, 34, M.F_BOLD, 1.2, b, True, "tengah")
        C.label_kecil(k, "ALKOHOL MENJELANG TIDUR MEMPERPARAH SENTAKAN", 540, 1160,
                      C.TEKS_3, 21, b, "tengah", 1.8)


# ================================================================ 10. PENUTUP
def _latar_penutup(k):
    C.latar_jatuh(k)
    return k


def _aktor_penutup(k, t, dur):
    """Kartu merek + ringkasan + CTA; menyatu ke babak 1."""
    a = _masuk(t, 0.6, 0.05)
    C.pendar(k, 540, 620, 520, (120, 160, 255), 0.22 * a, 2.6)
    C.tulis(k, "TUBUHMU CUMA", 540, 380, C.TEKS, 66, M.F_BOLD, 1.4, a, True, "tengah")
    C.tulis(k, "KETINGGALAN", 540, 466, C.CYAN, 84, M.F_BOLD, 1.6, a, True, "tengah")
    C.tulis(k, "ZAMAN", 540, 566, C.CYAN, 84, M.F_BOLD, 1.6, a, True, "tengah")
    C.label_kecil(k, "REFLEKS YANG DULU MENYELAMATKAN HIDUP", 540, 686, C.TEKS_3, 24, a, "tengah", 2.4)
    b = _masuk(t, 0.7, 0.45)
    if b > 0:
        C.panel(k, 132, 736, 816, 300, b, aksen=C.GOLD, radius=30)
        C.label_kecil(k, "RINGKASAN 3 DETIK", 540, 762, C.TEKS_3, 21, b, "tengah", 2.8)
        for i2, teks in enumerate(("NAMANYA HYPNIC JERK", "SEBABNYA REFLEKS PURBA", "PICUNYA KURANG TIDUR")):
            yy = 806 + i2 * 72
            C.cincin(k, 196, yy + 22, 16, C.GOLD, 2.4, 0.9 * b, glow=0.5)
            C.tulis(k, teks, 236, yy, C.TEKS, 38, M.F_BOLD, 1.2, b)
    c = _masuk(t, 0.8, 1.15)
    if c > 0:
        C.panel(k, 296, 1052, 488, 112, c, aksen=C.GOLD, radius=56)
        C.tulis(k, "SIMPAN VIDEO INI", 540, 1076, C.GOLD, 42, M.F_BOLD, 1.6, c, True, "tengah")
        C.label_kecil(k, "BIAR BESOK NGGAK KAGET LAGI", 540, 1178, C.TEKS_2, 23, c, "tengah", 2.2)



# ---------------------------------------------------------------- panel bawah
# Tiga baris data per babak. Ini yang membuat layar penuh tanpa hiasan kosong:
# penonton Shorts berhenti kalau ada informasi baru di setiap zona layar.
_AUTO = "__DURASI__"  # penanda: nilainya dihitung dari TOTAL, bukan ditulis tangan

BAWAH = [
    [("NAMA ILMIAH", "HYPNIC JERK"), ("ARTI", "SENTAKAN TIDUR"), ("BAHAYA", "TIDAK")],
    [("ASAL KATA", "HYPNOS = TIDUR"), ("JENIS", "MYOCLONUS"), ("PUSAT", "BATANG OTAK")],
    [("POPULASI", "60–70%"), ("TIAP MALAM", "±10%"), ("PALING SERING", "USIA 8–12")],
    [("FASE", "N1 » N2"), ("MULAI", "1–5 MENIT"), ("OTOT", "PALING LEMAS")],
    [("PENGIRIM", "BATANG OTAK"), ("JALUR", "REFLEKS KEJUT"), ("SINYAL", "OTOT MELEMAS")],
    [("TEORI", "REFLEKS PURBA"), ("STATUS", "BELUM TERBUKTI"), ("USIA IDE", "±60 JUTA TH")],
    [("SUMBER", "SLEEP MED. 2016"), ("KLASIFIKASI", "NORMAL · ICDS-3"), ("OBAT", "TIDAK PERLU")],
    [("PEMICU 1", "KURANG TIDUR"), ("PEMICU 2", "KAFEIN SORE"), ("PEMICU 3", "STRES")],
    [("KOPI", "SEBELUM 14.00"), ("JAM TIDUR", "KONSISTEN"), ("SUHU KAMAR", "18–20 °C")],
    # "AUTO" = diisi otomatis dari TOTAL di bawah (jangan tulis angka tangan).
    [("SUMBER", "AASM · SLEEP MED."), ("DURASI", _AUTO), ("SERI", "SAINS KlikTahu")],
]


def _bawah(k, i, tl):
    """Panel data bawah: tiga baris label/nilai, muncul berurutan."""
    baris = BAWAH[i]
    y0 = Y_PANEL_BAWAH
    a = _masuk(tl, 0.55, 0.30)
    if a <= 0:
        return
    C.panel(k, 62, y0, 956, 316, a, aksen=BABAK[i][1], radius=26)
    for j, (label, nilai) in enumerate(baris):
        aa = _masuk(tl, 0.5, 0.42 + j * 0.12)
        if aa <= 0:
            continue
        yy = y0 + 34 + j * 88
        if j:
            _isi(k, 100, yy - 12, 980, yy - 11, (255, 255, 255), int(20 * aa))
        C.label_kecil(k, label, 100, yy + 6, C.TEKS_3, 21, aa, "kiri", 2.4)
        C.tulis(k, nilai, 980, yy - 6, C.TEKS, 34, M.F_BOLD, 0.8, aa, True, "kanan")

# ================================================================ tabel
SCENES = [
    dict(id="hook", latar=_latar_hook, aktor=_aktor_hook),
    dict(id="nama", latar=_latar_nama, aktor=_aktor_nama),
    dict(id="sebaran", latar=_latar_sebaran, aktor=_aktor_sebaran),
    dict(id="waktu", latar=_latar_waktu, aktor=_aktor_waktu),
    dict(id="otak", latar=_latar_otak, aktor=_aktor_otak),
    dict(id="primata", latar=_latar_primata, aktor=_aktor_primata),
    dict(id="teori", latar=_latar_teori, aktor=_aktor_teori),
    dict(id="pemicu", latar=_latar_pemicu, aktor=_aktor_pemicu),
    dict(id="cara", latar=_latar_cara, aktor=_aktor_cara),
    dict(id="penutup", latar=_latar_penutup, aktor=_aktor_penutup),
]
_SEMUA = {s["id"]: s for s in SCENES}
SCENES = [_SEMUA[v] for v in PILIH]
CAPTION = [CAPTION[i] for i in _IDX]
BABAK = [BABAK[i] for i in _IDX]
BAWAH = [BAWAH[i] for i in _IDX]
# NASKAH ikut difilter: varian "kilat" hanya 6 babak, jadi naskah VO-nya juga
# 6 bagian. Tanpa ini `--dari-klip` membandingkan 6 klip dengan 10 naskah.
NASKAH = [NASKAH[i] for i in _IDX]
for _i, _s in enumerate(SCENES):
    _s["dur"] = DUR[_i]
# Durasi yang tampil di layar (panel data babak terakhir) dihitung dari timeline
# asli. Dulu ditulis tangan "75 DETIK" dan langsung salah begitu VO mengubah
# durasi babak.
BAWAH = [[(l, (f"{TOTAL:.0f} DETIK" if v == _AUTO else v)) for l, v in baris]
         for baris in BAWAH]

_LATAR_CACHE = {}


def daftar():
    return {"scenes": [{"id": s["id"], "dur": s["dur"], "mulai": MULAI[i]}
                       for i, s in enumerate(SCENES)],
            "total": TOTAL, "fps": FPS}


def latar_scene(i):
    key = SCENES[i]["id"]
    l = _LATAR_CACHE.get(key)
    if l is None:
        k = Kanvas(W_, H_, C.MALAM_1)
        SCENES[i]["latar"](k)
        l = k.a
        _LATAR_CACHE[key] = l
    return l


# ================================================================ frame
def _hud(k, i, tl, dur):
    nama, warna = BABAK[i]
    frac = (MULAI[i] + min(tl, dur)) / TOTAL
    C.hud(k, "KlikTahu", nama, warna, f"{i + 1:02d}", frac, SUMBER)


def _kamera(k, i, tl, dur):
    """Gerak kamera: dorongan halus per babak + goyangan tangan + whip di cut."""
    s = SCENES[i]["id"]
    if s == "hook":
        skala = 1.02 + 0.055 * eio(clamp(tl / dur))
    elif s == "nama":
        skala = 1.05 - 0.04 * eio(clamp(tl / dur))
    elif s == "primata":
        skala = 1.03 + 0.03 * eio(clamp(tl / dur))
    else:
        skala = 1.015 + 0.035 * eio(clamp(tl / max(0.6, dur)))
    gx, gy = C.shake(tl + i * 3.7, 2.2, 0.9, i)
    out = C.dorong(k, (W_ / 2, H_ / 2), skala, (gx, gy))
    # whip pada 0.45 detik pertama tiap cut
    if i > 0 and tl < 0.42:
        out = C.whip(C._KanvasDari(out), tl / 0.42, "kanan", 0.85)
    return out


def frame(t, bersih=False, tanpa_caption=False, tanpa_teks=False):
    """Komposisi satu frame.

    `bersih=True` menghilangkan HUD/caption/panel bawah — dipakai pembuat
    thumbnail supaya tidak ada teks mesin yang bertumpuk dengan teks thumbnail.
    """
    siapkan()
    _siap_debu()
    t = clamp(t, 0.0, TOTAL - 1e-4)
    i = 0
    while i < len(SCENES) - 1 and t >= MULAI[i + 1]:
        i += 1
    s = SCENES[i]
    tl = t - MULAI[i]
    dur = s["dur"]

    k = object.__new__(Kanvas)
    k.w, k.h = W_, H_
    k.a = latar_scene(i).copy()
    if tanpa_teks:
        C.TANPA_TEKS = True
    try:
        s["aktor"](k, tl, dur)
    finally:
        C.TANPA_TEKS = False

    out = _kamera(k, i, tl, dur)

    # HUD & caption digambar SETELAH kamera -> tetap tajam (bukan ikut di-zoom)
    if bersih:
        return C.finishing(C._KanvasDari(out), t, _LUT, True, (2.0, 5))

    k2 = object.__new__(Kanvas)
    k2.w, k2.h = W_, H_
    k2.a = out
    # blend loop dihitung lebih dulu: caption-nya ikut diredupkan
    f = 0.0
    if i == len(SCENES) - 1:
        f = smooth(seg(tl, dur - 0.85, dur))

    # scrim caption: supaya teks tetap terbaca di atas gambar apa pun
    C.scrim(k2, Y_SCRIM[0], Y_SCRIM[1], (0, 132))
    _hud(k2, i, tl, dur)
    if not tanpa_caption:
        C.caption_karaoke(k2, CAPTION[i], tl, dur * 0.86, BABAK[i][1], Y_CAPTION, 48, 904,
                          alpha=max(0.0, 1.0 - f))
    _bawah(k2, i, tl)

    out = C.finishing(k2, t, _LUT, True, (2.0, 5))

    # Loop: blend ke frame 0 TANPA caption. Kalau yang dipakai frame 0 penuh,
    # caption penutup dan caption pembuka saling tembus (hantu teks 0,8 detik).
    if f > 0.995:
        return _frame0().copy()
    if f > 0.001:
        out = cv2.addWeighted(out, 1.0 - f, _frame0_tanpa_caption(), f, 0.0)
    return out


def _frame0():
    global _FRAME0
    if _FRAME0 is None:
        _FRAME0 = frame(0.0) + 0  # salinan tersendiri (dipakai blend loop)
    return _FRAME0


def _frame0_tanpa_caption():
    """Frame 0 tanpa caption — dasar blend loop supaya tidak ada hantu teks."""
    global _FRAME0_NOCAP
    if _FRAME0_NOCAP is None:
        _FRAME0_NOCAP = frame(0.0, tanpa_caption=True) + 0
    return _FRAME0_NOCAP


# ================================================================ pratinjau
def _pratinjau():
    import time
    t0 = time.time()
    siapkan()
    _siap_debu()
    print(f"[siapkan] {(time.time() - t0) * 1000:.0f} ms")
    t1 = time.time()
    for i in range(len(SCENES)):
        latar_scene(i)
    print(f"[latar] {len(SCENES)}: {(time.time() - t1) * 1000:.0f} ms")

    for i, s in enumerate(SCENES):
        tm = MULAI[i] + s["dur"] * 0.62
        t2 = time.time()
        for _ in range(3):
            frame(tm)
        print(f"  {s['id']:8s} {(time.time() - t2) / 3 * 1000:6.2f} ms/frame")

    os.makedirs("/tmp/v20", exist_ok=True)
    for i, s in enumerate(SCENES):
        for f2, frac in ((0, 0.28), (1, 0.62), (2, 0.9)):
            tm = MULAI[i] + s["dur"] * frac
            Image.fromarray(frame(tm)).save(f"/tmp/v20/{i:02d}_{f2}_{s['id']}.jpg", quality=88)
    print("total detik:", round(TOTAL, 2))


if __name__ == "__main__":
    _pratinjau()
