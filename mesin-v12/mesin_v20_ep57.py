#!/usr/bin/env python3
"""mesin_v20_ep57.py — EP57 "Kenapa Waktu Terasa Makin Cepat Saat Dewasa".

Kenapa episode ini
------------------
Topik ini menang di tiga hal sekaligus:
  * dialami SEMUA orang dewasa -> tidak perlu penjelasan awal, penonton langsung
    merasa "ini saya" (sinyal swipe-away terbaik yang bisa didapat);
  * ada jawaban populer yang SALAH-SETENGAH (teori proporsional) dan bukti baru
    2026 yang membantahnya -> menyediakan momen "ternyata bukan itu", pemicu
    komentar dan share;
  * tidak menyinggung kesehatan serius -> aman untuk monetisasi, dan bisa
    diakhiri dengan tindakan nyata (rute baru, hal baru) yang membuat penonton
    menyimpan video.

Struktur 10 babak (satu ide per layar)
--------------------------------------
  1  HOOK       jam berputar makin cepat; pertanyaan
  2  PROPORSI   teori populer: umur 5 = 20%, umur 50 = 2% (Paul Janet, 1877)
  3  SURVEI     77% dari 918 orang yakin tahun datang makin cepat (Ogden, 2023)
  4  PENANDA    otak menghitung waktu dari penanda kejadian baru
  5  ODDBALL    kejadian aneh terasa lebih lama (efek oddball)
  6  OTAK       studi 2025: 577 orang, otak menua lebih jarang berpindah status
  7  MITOS      studi 2026: jumlah memori lama tidak berhubungan; mencatalah
  8  AUTOPILOT  rasa terburu-buru (10% varian) > usia (1-4% varian)
  9  CARA       tiga langkah memperlambat waktu
 10  PENUTUP    ringkasan + CTA + loop sempurna ke babak 1

API: `siapkan()`, `frame(t)`, `daftar()`, `naskah()`.
Pratinjau: `python3 mesin_v20_ep57.py`
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
JUDUL = "KENAPA WAKTU MAKIN CEPAT SAAT DEWASA"
SUMBER = "Comm. Biol. 2025 · Mem. & Cogn. 2026 · Ogden 2023"
BABAK = [
    ("PERTANYAAN", C.CYAN),
    ("PROPORSIONAL", C.VIOLET),
    ("SURVEI", C.GOLD),
    ("PENANDA", C.CYAN),
    ("ODDBALL", C.VIOLET),
    ("OTAK MENUA", C.CYAN),
    ("MITOS", C.CORAL),
    ("AUTOPILOT", C.GOLD),
    ("CARA", C.GREEN),
    ("PENUTUP", C.CYAN),
]

CAPTION = [
    "JAM YANG SAMA, RASA YANG BEDA",
    "UMUR 5: SETAHUN = 20% HIDUP",
    "77% BILANG TAHUN MAKIN CEPAT",
    "OTAK MENGHITUNG DARI PENANDA BARU",
    "KEJADIAN ANEH TERASA LEBIH LAMA",
    "OTAK MENUA LEBIH JARANG BERPINDAH",
    "BUKAN JUMLAH MEMORI, TAPI MENCATAT",
    "YANG BIKIN CEPAT: RASA TERBURU",
    "TIGA CARA MEMPERLAMBAT WAKTU",
    "WAKTU TIDAK DICURI, CUMA TIDAK DICATAT",
]

# Naskah VO. Ditulis untuk diucapkan mesin TTS bahasa Indonesia: kalimat pendek,
# tanda baca jelas, tanpa singkatan yang dibaca aneh ("s.d." / "vs" / "%").
NASKAH = [
    "Satu jam selalu enam puluh menit. Tapi kenapa waktu terasa makin cepat setiap tahun?",
    "Jawaban populer: waktu dinilai dari umur. Umur lima tahun, setahun itu dua puluh persen "
    "hidup. Umur lima puluh, tinggal dua persen.",
    "Survei sembilan ratus delapan belas orang: tujuh puluh tujuh persen yakin Natal datang "
    "makin cepat tiap tahun.",
    "Otak tidak menyimpan waktu, tapi menghitung kejadian baru. Hari yang sama dengan kemarin "
    "tidak dicatat, jadi minggunya menguap.",
    "Satu kejadian aneh di antara yang membosankan terasa lebih lama. Namanya efek oddball. "
    "Perhatian meregangkan waktu.",
    "Studi dua ribu dua puluh lima memindai lima ratus tujuh puluh tujuh orang saat menonton "
    "film. Otak yang menua lebih jarang berpindah status.",
    "Studi dua ribu dua puluh enam membantah mitosnya. Bukan jumlah memori lama, tapi "
    "kemampuan mencatat hal baru yang menentukan.",
    "Yang paling menentukan bukan umur. Rasa terburu-buru menyumbang sepuluh persen, usia "
    "cuma satu sampai empat persen.",
    "Jadi coba rute baru, pelajari satu hal baru, dan tandai minggumu. Waktu akan terasa "
    "lebih panjang.",
    "Waktumu tidak dicuri. Kamu cuma berhenti mencatat. Simpan videonya, lalu coba satu hal "
    "baru minggu ini.",
]

# ---------------------------------------------------------------- waktu babak
# Timeline INDUK selalu audio/vo/timing.json (10 babak). Varian kilat memilih
# subset lewat _IDX. Berkas salah panjang = berhenti keras, bukan render senyap.
_DEF_DUR = [7.6, 8.2, 8.0, 7.5, 7.4, 8.4, 8.3, 7.6, 8.0, 8.0]

#: Setiap episode punya folder audio sendiri: audio/vo57/sumber (klip VO) dan
#: audio/vo57/timing.json. Dulu semua episode berbagi audio/vo — begitu episode
#: baru dibangun, timeline episode lama tertimpa dan render memakai durasi yang
#: salah tanpa error (lihat docs/MESIN_V20.md jebakan 18).
AUDIO_DIR = "vo57"


def _path_timing(varian="penuh"):
    sub = AUDIO_DIR if varian == "penuh" else f"{AUDIO_DIR}_{varian}"
    return os.path.join(BASE, "audio", sub, "timing.json")


def _muat_durasi():
    p = _path_timing("penuh")
    if not os.path.exists(p):
        raise RuntimeError(
            f"timeline induk tidak ada: {p}\n"
            f"jalankan dulu: python3 mesin_v20_suara.py --episode mesin_v20_ep57 "
            f"--dari-klip audio/{AUDIO_DIR}/sumber --keluar keluaran/KlikTahu_Ep57_audio.m4a"
        )
    d = json.load(open(p))
    # Penjaga: timeline SEMENTARA (dibuat untuk pratinjau tata letak sebelum VO
    # ada) tidak boleh dipakai render. Dulu tidak ada penjaga apa pun, jadi
    # render bisa jalan dengan durasi cadangan dan hasilnya tampak normal.
    if d.get("sementara") and not os.environ.get("KT_SEMENTARA"):
        raise RuntimeError(
            f"{p} masih timeline SEMENTARA (belum dari VO). Bangun audio dulu, "
            "atau set KT_SEMENTARA=1 kalau memang hanya mau pratinjau tata letak."
        )
    dur = [float(x) for x in d["dur"]]
    if len(dur) != len(_DEF_DUR):
        raise RuntimeError(
            f"{p} berisi {len(dur)} babak, seharusnya {len(_DEF_DUR)}. "
            "Berkas ini tertimpa timing varian lain — bangun ulang audio penuh."
        )
    return dur


# Varian keluaran: "penuh" 10 babak, "kilat" 6 babak untuk uji jangkauan feed.
VARIAN = {
    "penuh": ["hook", "proporsi", "survei", "penanda", "oddball", "otak",
              "mitos", "autopilot", "cara", "penutup"],
    "kilat": ["hook", "proporsi", "penanda", "otak", "mitos", "penutup"],
}
_VAR = os.environ.get("KT_VARIAN", "penuh")
if _VAR not in VARIAN:
    _VAR = "penuh"
PILIH = VARIAN[_VAR]

ALL_IDS = ["hook", "proporsi", "survei", "penanda", "oddball", "otak",
           "mitos", "autopilot", "cara", "penutup"]

_DUR_INDUK = _muat_durasi()          # 10 babak, sumber kebenaran
DUR = list(_DUR_INDUK)
_IDX = [ALL_IDS.index(v) for v in PILIH]
DUR = [DUR[i] for i in _IDX]


def _cek_timing_varian():
    """Timing varian harus sama dengan subset timeline induk (±20 ms)."""
    for nama, pilih in VARIAN.items():
        p = _path_timing(nama)
        if not os.path.exists(p):
            continue
        dur_v = [float(x) for x in json.load(open(p))["dur"]]
        harus = [_DUR_INDUK[ALL_IDS.index(v)] for v in pilih]
        if len(dur_v) != len(harus):
            raise RuntimeError(f"{p}: {len(dur_v)} babak, varian '{nama}' butuh {len(harus)}")
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
Y_KONTEN = (190, 1150)
Y_CAPTION = 1256
Y_SCRIM = (1120, 1420)
Y_PANEL_BAWAH = 1416
Y_SUMBER = 1806

_GLYPH = {}
_LUT = None
_FRAME0 = None
_FRAME0_NOCAP = None
_DEBU = None


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


def _busur(k, cx, cy, r, frac, warna, alpha=1.0, tebal=0):
    """Potongan lingkaran (untuk menunjukkan 20% vs 2% dari hidup).

    Digambar di lapisan RGBA lalu di-blit, jadi alpha-nya benar (cv2 pada RGBA
    mengabaikan alpha -> selalu lewat lapisan).
    """
    d = int(r * 2 + 8)
    lap = np.zeros((d, d, 4), np.uint8)
    c = (int(d / 2), int(d / 2))
    if tebal:
        cv2.ellipse(lap, c, (int(r), int(r)), 0, -90, -90 + 360 * frac,
                    (*warna, 255), int(tebal), cv2.LINE_AA)
    else:
        cv2.ellipse(lap, c, (int(r), int(r)), 0, -90, -90 + 360 * max(0.01, frac),
                    (*warna, 255), -1, cv2.LINE_AA)
        # lubang tengah -> bentuk donat
        cv2.circle(lap, c, int(r * 0.62), (0, 0, 0, 0), -1, cv2.LINE_AA)
    blit(k.a, lap, int(cx - d / 2), int(cy - d / 2), alpha)


def _siap_debu():
    global _DEBU
    if _DEBU is None:
        r = M.rng(57)
        _DEBU = np.stack([r.uniform(0, W_, 80), r.uniform(0, H_, 80),
                          r.uniform(2, 8, 80), r.uniform(0, 6.28, 80),
                          r.uniform(0.2, 1.0, 80)], 1)
    return _DEBU


# ================================================================ 1. HOOK
def _latar_hook(k):
    C.latar_jatuh(k)
    C.bintang(k, 360, 57, 0, H_, 0.9)
    return k


def _aktor_hook(k, t, dur):
    """Jam besar: jarum menit makin cepat, cincin waktu meregang."""
    a = _masuk(t, 0.7, 0.02)
    r = 232
    cx, cy = 540, 470
    if a > 0:
        C.pendar(k, cx, cy, 430, (110, 165, 255), 0.30 * a, 2.4)
        blit_c(k.a, K.jam(r, C.CYAN, (14, 20, 36)), cx, cy, a)
        # jarum menit berputar makin cepat (waktu yang dipercepat)
        laju = 190 + 900 * smooth(clamp(t / max(0.8, dur)))
        for gh in range(3):                       # jejak gerak
            sudut = t * laju - gh * 22
            jar = K.jarum_jam_spr(r, sudut, 0.80, C.CYAN, 0.030)
            blit_c(k.a, jar, cx, cy, a * (0.55 - gh * 0.15))
        blit_c(k.a, K.jarum_jam_spr(r, t * laju, 0.80, C.PUTIH, 0.034), cx, cy, a)
        blit_c(k.a, K.jarum_jam_spr(r, 40 + t * 26, 0.56, C.GOLD, 0.028), cx, cy, a)
        for i2 in range(3):
            rr = int(r * (1.08 + i2 * 0.06 + 0.02 * math.sin(t * 3 + i2)))
            C.cincin(k, cx, cy, rr, C.CYAN, 2.0, (0.34 - i2 * 0.09) * a, glow=0.6)

    C.tulis_wipe(k, "WAKTU MAKIN", W_ / 2, 790, (t - 0.25) / 0.5, C.TEKS, 74, M.F_BOLD,
                 1.2, "tengah", "kiri", C.CYAN_L)
    C.tulis_wipe(k, "CEPAT?", W_ / 2, 878, (t - 0.5) / 0.5, C.GOLD, 132, M.F_BOLD,
                 2.0, "tengah", "tengah", C.PUTIH)
    aa = _masuk(t, 0.7, 1.15)
    if aa > 0:
        C.label_kecil(k, "DAN TIDAK ADA YANG MEMBERI TAHU KAPAN MULAINYA", 540, 1030,
                      C.TEKS_2, 23, aa, "tengah", 2.4)


# ================================================================ 2. PROPORSIONAL
def _latar_proporsi(k):
    C.latar_otak(k, 61)
    C.berkas(k, 300, 0, 1500, 90, 320, (140, 175, 255), 0.12, 0.0, 0.5)
    return k


def _aktor_proporsi(k, t, dur):
    """Dua kartu: umur 5 (setahun = 20%) vs umur 50 (setahun = 2%)."""
    a0 = _masuk(t, 0.6, 0.02)
    C.label_kecil(k, "TEORI PALING POPULER", 62, 200, C.TEKS_2, 26, a0, "kiri", 3.0)
    # Judul duduk di atas panel kiri -> panel diberi titik atas sendiri (dulu
    # panel mulai y=330 dan menimpa huruf "PROPORSIONAL").
    C.tulis(k, "PROPORSIONAL", 62, 238, C.VIOLET_L, 54, M.F_BOLD, 1.4, a0)

    kartu = [(62, "UMUR 5", 0.20, "20%", "SETAHUN DARI HIDUPMU", C.GOLD),
             (556, "UMUR 50", 0.02, "2%", "SETAHUN DARI HIDUPMU", C.CORAL)]
    for i2, (x, umur, frac, besar, ket, warna) in enumerate(kartu):
        aa = _masuk(t, 0.7, 0.20 + i2 * 0.30)
        if aa <= 0:
            continue
        C.panel(k, x, 316, 462, 486, aa, aksen=warna, radius=30)
        C.label_kecil(k, umur, x + 38, 348, C.TEKS_3, 22, aa, "kiri", 2.6)
        cx, cy = x + 231, 512
        # cincin latar penuh: penonton melihat "potongan dari satu lingkaran"
        C.cincin(k, cx, cy, 104, warna, 14.0, 0.16 * aa, glow=0.0)
        _busur(k, cx, cy, 104, frac, warna, 0.95 * aa, tebal=26)
        C.tulis(k, besar, x + 231, 474, warna, 88, M.F_BOLD, 1.0, aa, True, "tengah")
        C.label_kecil(k, ket, x + 231, 652, C.TEKS_2, 21, aa, "tengah", 2.2)
        C.tulis(k, "1 TAHUN", x + 231, 690, C.TEKS, 34, M.F_BOLD, 1.2, aa, True, "tengah")

    b = _masuk(t, 0.7, 1.05)
    if b > 0:
        C.panel(k, 62, 838, 956, 268, b, aksen=C.VIOLET, radius=28)
        C.label_kecil(k, "PENCETUS · PAUL JANET · 1877", 100, 858, C.TEKS_3, 21, b, "kiri", 2.4)
        C.tulis(k, "MAKIN TUA, PEMBAGINYA", 100, 892, C.TEKS, 38, M.F_BOLD, 1.2, b)
        C.tulis(k, "MAKIN BESAR", 100, 936, C.VIOLET_L, 38, M.F_BOLD, 1.2, b)
        C.label_kecil(k, "SATU TAHUN JADI POTONGAN YANG MAKIN KECIL", 100, 1000,
                      C.TEKS_2, 22, b, "kiri", 1.8)
        C.label_kecil(k, "TAPI: INI MENJELASKAN POLANYA, BUKAN SEBABNYA", 100, 1042,
                      C.CORAL, 21, _masuk(t, 0.6, 1.6), "kiri", 1.8)


# ================================================================ 3. SURVEI
def _latar_survei(k):
    C.latar_otak(k, 71)
    return k


def _aktor_survei(k, t, dur):
    """77% dari 918 orang: piktogram 10x10 + kartu angka besar."""
    a0 = _masuk(t, 0.6, 0.02)
    C.label_kecil(k, "YANG DIRASAKAN HAMPIR SEMUA ORANG", 62, 200, C.TEKS_2, 25, a0, "kiri", 2.8)
    C.tulis(k, "77%", 62, 232, C.GOLD, 148, M.F_BOLD, 1.0, a0, True)
    C.label_kecil(k, "YAKIN NATAL & TAHUN BARU", 62, 404, C.TEKS, 24, a0, "kiri", 2.0)
    C.label_kecil(k, "DATANG MAKIN CEPAT TIAP TAHUN", 62, 436, C.TEKS, 24, a0, "kiri", 2.0)

    p = _masuk(t, 1.0, 0.35)
    C.panel(k, 62, 500, 956, 400, _masuk(t, 0.6, 0.15), aksen=C.GOLD, radius=28)
    C.label_kecil(k, "100 ORANG DEWASA", 100, 522, C.TEKS_3, 21, a0, "kiri", 2.4)
    C.piktogram(k, 108, 574, 10, 10, 0.77, C.GOLD, p, r=13, jarak=86)
    C.label_kecil(k, "SETUJU  77%", 100, 856, C.GOLD, 24, _masuk(t, 0.7, 1.1), "kiri", 2.0)
    C.label_kecil(k, "TIDAK SETUJU  9%  ·  NETRAL  14%", 100, 890, C.TEKS_3, 21,
                  _masuk(t, 0.7, 1.1), "kiri", 1.8)

    b = _masuk(t, 0.7, 1.3)
    if b > 0:
        C.panel(k, 62, 930, 956, 196, b, aksen=C.CYAN, radius=28)
        C.label_kecil(k, "SURVEI 918 ORANG · RUTH OGDEN · 2023", 100, 950, C.TEKS_3, 21, b,
                      "kiri", 2.2)
        C.tulis(k, "BUKAN PERASAAN SENDIRIAN", 100, 982, C.TEKS, 40, M.F_BOLD, 1.2, b)
        C.label_kecil(k, "POLA INI MUNCUL DI BANYAK NEGARA", 100, 1044, C.TEKS_2, 22, b,
                      "kiri", 1.8)


# ================================================================ 4. PENANDA
def _latar_penanda(k):
    C.latar_otak(k, 81)
    C.berkas(k, 620, 0, 1400, 120, 380, (110, 200, 255), 0.10, 0.0, 1.4)
    return k


def _aktor_penanda(k, t, dur):
    """Dua garis waktu: minggu biasa (sedikit penanda) vs minggu liburan (banyak)."""
    a0 = _masuk(t, 0.6, 0.02)
    C.label_kecil(k, "OTAK MENGHITUNG WAKTU DARI PENANDA", 62, 200, C.TEKS_2, 25, a0,
                  "kiri", 2.6)

    baris = [("MINGGU BIASA", [0.5], 300, C.TEKS_2, "TERASA 1 HARI"),
             ("MINGGU LIBURAN", [0.08, 0.18, 0.28, 0.37, 0.46, 0.55, 0.63, 0.71,
                                 0.79, 0.87, 0.94], 610, C.CYAN, "TERASA 1 BULAN")]
    for i2, (nama, tanda, y, warna, hasil) in enumerate(baris):
        aa = _masuk(t, 0.7, 0.18 + i2 * 0.38)
        if aa <= 0:
            continue
        C.panel(k, 62, y - 60, 956, 250, aa, aksen=warna, radius=28)
        C.label_kecil(k, nama, 100, y - 38, warna if i2 else C.TEKS_3, 23, aa, "kiri", 2.6)
        # garis waktu
        _isi(k, 100, y + 34, 980, y + 38, (255, 255, 255), int(28 * aa))
        p = _masuk(t, 0.9, 0.3 + i2 * 0.38)
        for j2, f in enumerate(tanda):
            x = int(100 + 880 * f)
            if p * 1.15 < f + 0.06:
                continue
            C.pendar(k, x, y + 36, 46, warna, 0.5 * aa, 2.2)
            C.cincin(k, x, y + 36, 15, warna, 3.0, 0.95 * aa, glow=0.6)
            _isi(k, x - 2, y + 20, x + 2, y + 54, warna, int(220 * aa))
        C.tulis(k, hasil, 100, y + 96, warna if i2 else C.TEKS_2, 34, M.F_BOLD, 1.2, aa)
        C.label_kecil(k, f"{len(tanda)} PENANDA" if i2 else "HAMPIR TANPA PENANDA",
                      980, y + 104, C.TEKS_3, 21, aa, "kanan", 1.8)

    b = _masuk(t, 0.7, 1.35)
    if b > 0:
        C.panel(k, 62, 900, 956, 224, b, aksen=C.GOLD, radius=28)
        C.label_kecil(k, "EFEKNYA DIKENAL SEBAGAI", 100, 920, C.TEKS_3, 21, b, "kiri", 2.4)
        C.tulis(k, "PARADOKS LIBURAN", 100, 950, C.GOLD, 52, M.F_BOLD, 1.4, b)
        C.label_kecil(k, "SEMINGGU LIBURAN BISA TERASA LEBIH PANJANG DARI 2 BULAN KANTOR",
                      100, 1030, C.TEKS_2, 21, b, "kiri", 1.6)
        C.label_kecil(k, "KARENA YANG DIHITUNG ADALAH JUMLAH KEJADIAN BARU", 100, 1066,
                      C.TEKS_3, 20, b, "kiri", 1.6)


# ================================================================ 5. ODDBALL
def _latar_oddball(k):
    C.latar_otak(k, 91)
    return k


def _aktor_oddball(k, t, dur):
    """Deretan kejadian sama + satu oddball yang meregangkan waktu."""
    a0 = _masuk(t, 0.6, 0.02)
    C.label_kecil(k, "EFEK ODDBALL · WITTMANN", 62, 200, C.TEKS_2, 25, a0, "kiri", 2.8)
    C.tulis(k, "YANG ANEH TERASA", 62, 236, C.TEKS, 46, M.F_BOLD, 1.2, a0)
    C.tulis(k, "LEBIH LAMA", 62, 290, C.VIOLET_L, 56, M.F_BOLD, 1.4, a0)

    p = _masuk(t, 1.0, 0.25)
    C.panel(k, 62, 392, 956, 290, _masuk(t, 0.6, 0.10), aksen=C.VIOLET, radius=28)
    C.label_kecil(k, "DERET KEJADIAN YANG SAMA", 100, 414, C.TEKS_3, 21, a0, "kiri", 2.2)
    n = 9
    for i2 in range(n):
        f = p * 1.2 - i2 * 0.05
        if f <= 0:
            continue
        x = 128 + i2 * 96
        y = 512
        aneh = i2 == 4
        rr = int((34 if aneh else 22) * clamp(f))
        warna = C.GOLD if aneh else C.TEKS_3
        if aneh:
            C.pendar(k, x, y, 90, C.GOLD, 0.55 * clamp(f), 2.4)
            C.cincin(k, x, y, int(48 + 8 * math.sin(t * 4)), C.GOLD, 3.0, 0.9 * clamp(f), glow=0.7)
        C.cincin(k, x, y, rr, warna, 3.0 if aneh else 2.0, 0.9 * clamp(f), glow=0.5)
    C.label_kecil(k, "SAMA PERSIS, TAPI SATU BERBEDA", 100, 612, C.TEKS_3, 21,
                  _masuk(t, 0.6, 0.9), "kiri", 1.8)

    b = _masuk(t, 0.7, 0.85)
    if b > 0:
        # dua batang: durasi nyata vs durasi yang dirasakan
        C.panel(k, 62, 712, 956, 386, b, aksen=C.CYAN, radius=28)
        C.label_kecil(k, "DURASI DI KLIP", 100, 740, C.TEKS_3, 21, b, "kiri", 2.2)
        _isi(k, 100, 776, int(100 + 660 * b), 812, C.TEKS_2, int(220 * b))
        C.label_kecil(k, "SAMA", 780, 784, C.TEKS_3, 21, b, "kiri", 1.8)
        C.label_kecil(k, "DURASI YANG DIRASAKAN", 100, 866, C.TEKS_3, 21, b, "kiri", 2.2)
        pb = _masuk(t, 1.0, 1.05)
        _isi(k, 100, 902, int(100 + 860 * pb), 938, C.GOLD, int(235 * b))
        _isi(k, 100, 902, int(100 + 860 * pb), 906, mix(C.GOLD, (255, 255, 255), 0.4),
             int(235 * b))
        C.label_kecil(k, "TERASA 10-20% LEBIH PANJANG", 100, 962, C.GOLD, 24, pb, "kiri", 2.0)
        C.label_kecil(k, "PERHATIAN EKSTRA = WAKTU TEREGANG", 100, 1012, C.TEKS_2, 22, b,
                      "kiri", 1.8)


# ================================================================ 6. OTAK MENUA
def _latar_otak(k):
    C.latar_otak(k, 101)
    C.berkas(k, 520, 0, 1500, 100, 360, (140, 190, 255), 0.13, 0.0, 1.0)
    return k


def _aktor_otak(k, t, dur):
    """Otak + pita status saraf: usia 20 (banyak transisi) vs usia 70 (sedikit)."""
    a = _masuk(t, 0.8, 0.02)
    ob = K.otak(720, sorot="korteks")
    if a > 0:
        C.pendar(k, 540, 440, 420, (120, 150, 255), 0.24 * a, 2.6)
        blit_c(k.a, ob, 540, 430 + _bob(t, 9, 0.7), a)
        C.cincin(k, 540, 430, int(300 + 6 * math.sin(t * 2.4)), C.CYAN, 2.0, 0.22 * a, glow=0.6)

    b = _masuk(t, 0.7, 0.35)
    C.label_kecil(k, "577 ORANG DIPINDAI · USIA 18-88 · KLIP 8 MENIT", 62, 742, C.TEKS_2, 21,
                  b, "kiri", 2.2)
    pita = [("USIA 20-AN", 12, C.CYAN, 806), ("USIA 70-AN", 5, C.CORAL, 920)]
    p = _masuk(t, 1.0, 0.6)
    for nama, n, warna, y in pita:
        if p <= 0:
            continue
        # Nama + jumlah digabung di kiri ATAS batang. Dulu jumlah ditaruh di
        # kanan, menabrak batang kedua belas (12 batang memenuhi 62-1018).
        C.label_kecil(k, f"{nama} · {n} PERPINDAHAN", 62, y - 30, warna, 21, p, "kiri", 2.2)
        for i2 in range(n):
            f = p * 1.2 - i2 * 0.04
            if f <= 0:
                continue
            x0 = 62 + i2 * (956 / 13)
            x1 = x0 + (956 / 13) * 0.66
            _isi(k, int(x0), y, int(x1), y + 24, warna, int(210 * clamp(f)))
            _isi(k, int(x0), y, int(x1), y + 5, mix(warna, (255, 255, 255), 0.4),
                 int(210 * clamp(f)))

    c = _masuk(t, 0.7, 1.45)
    if c > 0:
        C.panel(k, 62, 1020, 956, 118, c, aksen=C.GOLD, radius=24)
        C.tulis(k, "LEBIH SEDIKIT MOMEN DICATAT", 100, 1040, C.GOLD, 34, M.F_BOLD, 1.2, c)
        C.label_kecil(k, "COMMUNICATIONS BIOLOGY · SEPT 2025 · 8 MENIT FILM HITCHCOCK",
                      100, 1096, C.TEKS_3, 19, c, "kiri", 1.6)


# ================================================================ 7. MITOS
def _latar_mitos(k):
    C.latar_otak(k, 111)
    return k


def _aktor_mitos(k, t, dur):
    """Mitos (memori lama) dicoret; bukti 2026 (mencatat hal baru) dicentang."""
    a0 = _masuk(t, 0.6, 0.02)
    C.label_kecil(k, "DUA PENJELASAN · SATU BARU DIUJI", 62, 200, C.TEKS_2, 25, a0, "kiri", 2.6)

    kartu = [
        ("MITOS", "JUMLAH MEMORI LAMA", "MAKIN SEDIKIT MEMORI", C.CORAL, 250, False),
        ("BUKTI 2026", "KECEPATAN MENCATAT", "SULIT MEREKAM HAL BARU", C.GREEN, 574, True),
    ]
    for i2, (tag, judul, sub, warna, y, benar) in enumerate(kartu):
        aa = _masuk(t, 0.7, 0.15 + i2 * 0.42)
        if aa <= 0:
            continue
        tinggi = 300 if i2 == 0 else 330
        C.panel(k, 62, y, 956, tinggi, aa, aksen=warna, radius=28)
        C.label_kecil(k, tag, 100, y + 26, warna, 21, aa, "kiri", 2.6)
        C.tulis(k, judul, 100, y + 62, C.TEKS, 46, M.F_BOLD, 1.2, aa)
        C.label_kecil(k, sub, 100, y + 132, C.TEKS_2, 23, aa, "kiri", 1.8)
        # lambang: silang untuk mitos, centang untuk bukti
        cx, cy = 930, y + 150
        C.cincin(k, cx, cy, 52, warna, 3.0, 0.9 * aa, glow=0.6)
        if aa > 0.4:
            lap = np.zeros((130, 130, 4), np.uint8)
            if benar:
                pts = [(40, 68), (58, 88), (92, 44)]
            else:
                pts = [(44, 44), (86, 86)]
            cv2.polylines(lap, [np.array(pts, np.int32)], False, (*warna, 255), 7, cv2.LINE_AA)
            if not benar:
                cv2.polylines(lap, [np.array([(86, 44), (44, 86)], np.int32)], False,
                              (*warna, 255), 7, cv2.LINE_AA)
            blit(k.a, lap, cx - 65, cy - 65)
        if i2 == 1:
            _isi(k, 100, y + 196, 940, y + 197, (255, 255, 255), int(26 * aa))
            C.label_kecil(k, "120 ORANG DEWASA · DIUJI ULANG", 100, y + 210, C.TEKS_3, 21,
                          aa, "kiri", 2.0)
            C.tulis(k, "YANG MENURUN: MENGKODE MEMORI", 100, y + 244, warna, 30, M.F_BOLD,
                    1.0, aa)

    b = _masuk(t, 0.7, 1.25)
    if b > 0:
        C.panel(k, 62, 936, 956, 196, b, aksen=C.GOLD, radius=28)
        C.label_kecil(k, "KESIMPULAN STUDI · MEMORY & COGNITION 2026", 100, 956, C.TEKS_3, 20,
                      b, "kiri", 2.0)
        C.tulis(k, "BUKAN YANG TERSIMPAN,", 100, 986, C.TEKS, 36, M.F_BOLD, 1.2, b)
        C.tulis(k, "TAPI YANG BARU MASUK", 100, 1030, C.GOLD, 36, M.F_BOLD, 1.2, b)


# ================================================================ 8. AUTOPILOT
def _latar_autopilot(k):
    C.latar_otak(k, 121)
    C.berkas(k, 700, 0, 1400, 130, 400, (255, 200, 120), 0.09, 0.0, 0.9)
    return k


def _aktor_autopilot(k, t, dur):
    """Batang: rasa terburu-buru 10% vs usia 4% / 1%."""
    a0 = _masuk(t, 0.6, 0.02)
    C.label_kecil(k, "YANG PALING MENENTUKAN", 62, 200, C.TEKS_2, 25, a0, "kiri", 2.8)
    C.tulis(k, "BUKAN UMUR.", 62, 236, C.TEKS, 52, M.F_BOLD, 1.2, a0)
    C.tulis(k, "TAPI RASA TERBURU.", 62, 296, C.GOLD, 52, M.F_BOLD, 1.2, a0)
    C.label_kecil(k, "BESAR PENGARUH TERHADAP RASA WAKTU CEPAT", 62, 376, C.TEKS_3, 21,
                  _masuk(t, 0.6, 0.5), "kiri", 1.8)

    baris = [("RASA TERBURU-BURU", 0.92, "10%"),
             ("USIA · DEKADE", 0.37, "4%"),
             ("USIA · UMUM", 0.09, "1%")]
    p = _masuk(t, 1.0, 0.35)
    C.panel(k, 62, 420, 956, 380, _masuk(t, 0.6, 0.12), aksen=C.GOLD, radius=28)
    C.grafik_batang(k, 96, 470, 700, baris, p, 30, 108, C.GOLD, 300, True)

    b = _masuk(t, 0.7, 1.15)
    if b > 0:
        C.panel(k, 62, 840, 956, 284, b, aksen=C.CYAN, radius=28)
        C.label_kecil(k, "ARTINYA", 100, 860, C.TEKS_3, 21, b, "kiri", 2.4)
        C.tulis(k, "MINGGU YANG PENUH", 100, 892, C.TEKS, 40, M.F_BOLD, 1.2, b)
        C.tulis(k, "TERASA LEBIH PANJANG", 100, 940, C.CYAN, 40, M.F_BOLD, 1.2, b)
        C.label_kecil(k, "SURVEI BELANDA · FRIEDMAN & JANSSEN · 2010", 100, 1014,
                      C.TEKS_3, 20, b, "kiri", 1.8)
        C.label_kecil(k, "LEBIH KUAT DARIPADA USIA, YANG CUMA 1-4 PERSEN", 100, 1050,
                      C.TEKS_2, 21, b, "kiri", 1.6)


# ================================================================ 9. CARA
def _latar_cara(k):
    C.latar_otak(k, 131)
    C.berkas(k, 540, 0, 1300, 150, 420, (110, 220, 180), 0.10, 0.0, 0.7)
    return k


def _aktor_cara(k, t, dur):
    """Tiga langkah berurutan dengan centang."""
    a = _masuk(t, 0.6, 0.02)
    C.label_kecil(k, "CARA MEMPERLAMBAT WAKTU", 62, 200, C.TEKS_2, 26, a, "kiri", 3.0)
    langkah = [("RUTE BARU", "JALAN PULANG YANG BEDA", C.CYAN),
               ("SATU HAL BARU", "KECIL SAJA, TAPI PERTAMA KALI", C.GOLD),
               ("TANDAI MINGGU", "CATAT SATU MOMEN TIAP PEKAN", C.GREEN)]
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
        C.tulis(k, "PENANDA BARU = WAKTU", 540, 1058, C.TEKS, 34, M.F_BOLD, 1.2, b, True,
                "tengah")
        C.tulis(k, "YANG TERASA LEBIH PANJANG", 540, 1104, C.GREEN, 34, M.F_BOLD, 1.2, b,
                True, "tengah")


# ================================================================ 10. PENUTUP
def _latar_penutup(k):
    C.latar_jatuh(k)
    C.bintang(k, 420, 77, 0, H_, 1.0)
    return k


def _aktor_penutup(k, t, dur):
    """Kartu merek + ringkasan + CTA; menyatu ke babak 1."""
    a = _masuk(t, 0.6, 0.02)
    C.pendar(k, 540, 560, 520, (120, 160, 255), 0.22 * a, 2.6)
    C.tulis(k, "WAKTUMU TIDAK", 540, 330, C.TEKS, 62, M.F_BOLD, 1.4, a, True, "tengah")
    C.tulis(k, "DICURI", 540, 412, C.GOLD, 96, M.F_BOLD, 1.6, a, True, "tengah")
    C.tulis(k, "CUMA TIDAK DICATAT", 540, 540, C.CYAN, 44, M.F_BOLD, 1.4, a, True, "tengah")

    b = _masuk(t, 0.7, 0.45)
    if b > 0:
        C.panel(k, 132, 640, 816, 300, b, aksen=C.GOLD, radius=30)
        C.label_kecil(k, "RINGKASAN 3 DETIK", 540, 666, C.TEKS_3, 21, b, "tengah", 2.8)
        for i2, teks in enumerate(("BUKAN UMUR, TAPI PENANDA",
                                   "OTAK MENCATAT HAL BARU",
                                   "RUTIN MEMBUAT WAKTU MENGHILANG")):
            yy = 710 + i2 * 72
            C.cincin(k, 196, yy + 22, 16, C.GOLD, 2.4, 0.9 * b, glow=0.5)
            C.tulis(k, teks, 236, yy, C.TEKS, 34, M.F_BOLD, 1.0, b)

    c = _masuk(t, 0.8, 1.15)
    if c > 0:
        C.panel(k, 268, 976, 544, 112, c, aksen=C.GOLD, radius=56)
        C.tulis(k, "SIMPAN VIDEO INI", 540, 1000, C.GOLD, 42, M.F_BOLD, 1.6, c, True,
                "tengah")
        C.label_kecil(k, "LALU COBA SATU HAL BARU MINGGU INI", 540, 1102, C.TEKS_2, 23, c,
                      "tengah", 2.2)


# ---------------------------------------------------------------- panel bawah
_AUTO = "__DURASI__"

BAWAH = [
    [("EFEK", "WAKTU CEPAT"), ("TERASA SEJAK", "USIA 20-30"), ("SIFAT", "UNIVERSAL")],
    [("TEORI", "PROPORSIONAL"), ("PENCETUS", "PAUL JANET"), ("TAHUN", "1877")],
    [("SURVEI", "918 ORANG"), ("SETUJU", "77%"), ("TIDAK SETUJU", "9%")],
    [("PENANDA", "KEJADIAN BARU"), ("RUTIN", "TIDAK DICATAT"), ("EFEK", "PARADOKS LIBURAN")],
    [("EFEK", "ODDBALL"), ("PEMICU", "HAL BARU"), ("HASIL", "TERASA LEBIH LAMA")],
    [("PESERTA", "577 ORANG"), ("USIA", "18-88"), ("STIMULUS", "FILM 8 MENIT")],
    [("STUDI", "120 ORANG"), ("MEMORI LAMA", "TIDAK BERHUBUNGAN"),
     ("YANG PENTING", "MENCATAT BARU")],
    [("PREDIKTOR", "RASA TERBURU"), ("KEKUATAN", "10% VARIAN"), ("USIA", "1-4% VARIAN")],
    [("LANGKAH 1", "RUTE BARU"), ("LANGKAH 2", "HAL BARU"), ("LANGKAH 3", "CATAT MOMEN")],
    [("SUMBER", "COMM. BIOL. 2025"), ("DURASI", _AUTO), ("SERI", "SAINS KlikTahu")],
]

# Judul babak untuk daftar waktu di deskripsi YouTube.
BABAK_VIDEO = [
    "Kenapa jam yang sama terasa beda",
    "Teori proporsional: 20% vs 2%",
    "Survei: 77% merasa tahun makin cepat",
    "Otak menghitung dari penanda baru",
    "Efek oddball: yang aneh terasa lebih lama",
    "Otak menua lebih jarang berpindah status",
    "Mitos memori lama vs bukti 2026",
    "Rasa terburu-buru lebih menentukan dari usia",
    "Tiga cara memperlambat waktu",
    "Waktu tidak dicuri, cuma tidak dicatat",
]

# Teks pustaka (judul/deskripsi/tag) — dibaca pustaka_v20 supaya tidak perlu
# mengubah skrip itu tiap episode baru.
META = {
    "judul": "Kenapa Waktu Terasa Makin Cepat Saat Dewasa? Ternyata Bukan Umur",
    "judul_alt": [
        "Kenapa Setahun Terasa Makin Cepat? Ini Jawaban Sainsnya",
        "Waktu Terasa Cepat Bukan Karena Umur, Tapi Karena Ini",
        "Otakmu Berhenti Mencatat: Sebab Waktu Terasa Cepat",
    ],
    "deskripsi": (
        "Setahun waktu kecil terasa panjang, sekarang lewat begitu saja. Ternyata "
        "penjelasan populernya — teori proporsional — hanya menjelaskan polanya, "
        "bukan sebabnya.\n\n{daftar_babak}\n\n"
        "Sumber: Communications Biology (2025, studi pemindaian 577 orang usia 18-88), "
        "Memory & Cognition (2026, 120 orang dewasa), survei Ruth Ogden (2023, 918 orang), "
        "Friedman & Janssen (2010). Ini informasi umum, bukan diagnosis.\n\n"
        "#KlikTahu #Sains #Waktu #Otak #FaktaUnik"
    ),
    "tag": ["kenapa waktu terasa cepat", "waktu cepat saat dewasa", "sains waktu",
            "cara kerja otak", "memori dan waktu", "efek oddball", "fakta sains",
            "psikologi waktu", "kliktahu", "sains indonesia"],
    "hashtag": ["#KlikTahu", "#Sains", "#Waktu", "#Otak", "#FaktaUnik"],
}

# Teks thumbnail (dipakai pustaka_v20.buat_thumb_utama).
THUMB = {
    "atas": "SETAHUN TERASA",
    "besar": "MAKIN CEPAT?",
    "angka": "2%",
    "keterangan": "DARI HIDUPMU TIAP TAHUN",
    "t_utama": 0.55,       # fraksi durasi babak hook
    "t_alt": (1.15, 0.55),  # (detik masuk babak, fraksi durasi babak)
}

# ================================================================ tabel
SCENES = [
    dict(id="hook", latar=_latar_hook, aktor=_aktor_hook),
    dict(id="proporsi", latar=_latar_proporsi, aktor=_aktor_proporsi),
    dict(id="survei", latar=_latar_survei, aktor=_aktor_survei),
    dict(id="penanda", latar=_latar_penanda, aktor=_aktor_penanda),
    dict(id="oddball", latar=_latar_oddball, aktor=_aktor_oddball),
    dict(id="otak", latar=_latar_otak, aktor=_aktor_otak),
    dict(id="mitos", latar=_latar_mitos, aktor=_aktor_mitos),
    dict(id="autopilot", latar=_latar_autopilot, aktor=_aktor_autopilot),
    dict(id="cara", latar=_latar_cara, aktor=_aktor_cara),
    dict(id="penutup", latar=_latar_penutup, aktor=_aktor_penutup),
]
_SEMUA = {s["id"]: s for s in SCENES}
SCENES = [_SEMUA[v] for v in PILIH]
CAPTION = [CAPTION[i] for i in _IDX]
BABAK = [BABAK[i] for i in _IDX]
BAWAH = [BAWAH[i] for i in _IDX]
NASKAH = [NASKAH[i] for i in _IDX]
BABAK_VIDEO = [BABAK_VIDEO[i] for i in _IDX]
for _i, _s in enumerate(SCENES):
    _s["dur"] = DUR[_i]
# Durasi di layar dihitung dari timeline asli, bukan ditulis tangan.
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
    elif s == "penutup":
        skala = 1.05 - 0.04 * eio(clamp(tl / dur))
    elif s == "otak":
        skala = 1.03 + 0.03 * eio(clamp(tl / dur))
    else:
        skala = 1.015 + 0.035 * eio(clamp(tl / max(0.6, dur)))
    gx, gy = C.shake(tl + i * 3.7, 2.2, 0.9, i)
    out = C.dorong(k, (W_ / 2, H_ / 2), skala, (gx, gy))
    if i > 0 and tl < 0.42:
        out = C.whip(C._KanvasDari(out), tl / 0.42, "kanan", 0.85)
    return out


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

    if bersih:
        return C.finishing(C._KanvasDari(out), t, _LUT, True, (2.0, 5))

    k2 = object.__new__(Kanvas)
    k2.w, k2.h = W_, H_
    k2.a = out
    f = 0.0
    if i == len(SCENES) - 1:
        f = smooth(seg(tl, dur - 0.85, dur))

    C.scrim(k2, Y_SCRIM[0], Y_SCRIM[1], (0, 132))
    _hud(k2, i, tl, dur)
    if not tanpa_caption:
        C.caption_karaoke(k2, CAPTION[i], tl, dur * 0.86, BABAK[i][1], Y_CAPTION, 48, 904,
                          alpha=max(0.0, 1.0 - f))
    _bawah(k2, i, tl)

    out = C.finishing(k2, t, _LUT, True, (2.0, 5))

    # Loop: blend ke frame 0 TANPA caption supaya caption penutup & pembuka
    # tidak saling tembus.
    if f > 0.995:
        return _frame0().copy()
    if f > 0.001:
        out = cv2.addWeighted(out, 1.0 - f, _frame0_tanpa_caption(), f, 0.0)
    return out


def _frame0():
    global _FRAME0
    if _FRAME0 is None:
        _FRAME0 = frame(0.0) + 0
    return _FRAME0


def _frame0_tanpa_caption():
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
        print(f"  {s['id']:9s} {(time.time() - t2) / 3 * 1000:6.2f} ms/frame")

    os.makedirs("/tmp/v20ep57", exist_ok=True)
    for i, s in enumerate(SCENES):
        for f2, frac in ((0, 0.28), (1, 0.62), (2, 0.9)):
            tm = MULAI[i] + s["dur"] * frac
            Image.fromarray(frame(tm)).save(f"/tmp/v20ep57/{i:02d}_{f2}_{s['id']}.jpg", quality=88)
    print("total detik:", round(TOTAL, 2))


if __name__ == "__main__":
    _pratinjau()
