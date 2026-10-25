#!/usr/bin/env python3
"""mesin_v21_ep58.py — EP58 "Ikan yang Seharusnya Punah 66 Juta Tahun Lalu".

Kenapa episode ini
------------------
Video short lama KlikTahu (acuan gaya) memakai pola: satu hewan purba, satu
pertanyaan besar, tujuh fakta bernomor, penutup "ingat tiga hal". Pola itu
terbukti menahan penonton, jadi Ep58 memakai pola yang sama — tetapi isinya
diangkat ke level berikutnya:

  * bukan hewan asing bagi penonton Indonesia: spesimen keduanya ditemukan di
    Manado dan menyandang nama *Latimeria menadoensis* -> kebanggaan lokal,
    pemicu komentar ("aku orang Manado, baru tahu");
  * ada koreksi nyata terhadap anggapan populer ("fosil hidup" itu keliru,
    dan coelacanth bukan nenek moyang langsung manusia) -> pemicu debat;
  * setiap angka bisa dilacak (1938, 1997, 1999, 400 juta, 66 juta, 2,86 Gb,
    ±3 tahun kehamilan, status kritis IUCN) -> kredibilitas, aman monetisasi;
  * tidak ada klaim kesehatan -> tidak kena sensor, dan bisa ditutup dengan
    ajakan menyimpan video.

Struktur 9 babak (satu ide per layar, seperti acuan 7 fakta + pembuka + penutup)
------------------------------------------------------------------------------
  1  HOOK       "sudah punah 66 juta tahun" -> ikan berenang di kartu laut
  2  FAKTA 1    umur 400 juta tahun, 170 juta tahun sebelum dinosaurus
  3  FAKTA 2    22 Desember 1938, Marjorie Courtenay-Latimer, 1,5 meter
  4  FAKTA 3    nama Latin, "duri berongga", sirip berdaging
  5  FAKTA 4    1997 Manado, 1999 Latimeria menadoensis, dua spesies
  6  FAKTA 5    sirip cuping -> kerabat tetrapoda, BUKAN leluhur langsung
  7  FAKTA 6    "fosil hidup" itu keliru: genom 2,86 Gb, hamil ±3 tahun
  8  FAKTA 7    populasi ratusan, tertangkap jaring, status kritis
  9  PENUTUP    tiga hal + ajakan ikuti & simpan

API: `siapkan()`, `frame(t)`, `daftar()`, `naskah()`, `META`, `THUMB`.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import mesin_v18_inti as I  # noqa: E402
import mesin_v21_kertas as K  # noqa: E402
from mesin_v18_inti import clamp, eio, eo, lerp, seg, smooth, tw  # noqa: E402
from mesin_v21_kertas import (ABU, BIRU, CORAL, GOLD, HIJAU, KARTU, KARTU_2, KERTAS_3,  # noqa: E402
                              KERTAS, KERTAS_2, LANGIT, NAVY, PASIR, ROSE,
                              TEAL, TINTA, TINTA_2, TINTA_3, W, H, Z)

FPS = 60

# ---------------------------------------------------------------- identitas
JUDUL = "IKAN YANG SEHARUSNYA PUNAH 66 JUTA TAHUN LALU"
KATEGORI = "HEWAN PURBA"
SUMBER_UMUM = "Fosil Devon ±400 jt th · Nature 2013 · IUCN Red List"
TOTAL_FAKTA = 7

BABAK = [
    ("PEMBUKA", 0),
    ("UMUR", 1),
    ("1938", 2),
    ("NAMA", 3),
    ("MANADO", 4),
    ("SIRIP", 5),
    ("MITOS", 6),
    ("ANCAMAN", 7),
    ("PENUTUP", 0),
]

# Naskah VO: kalimat pendek, angka dieja supaya TTS tidak salah baca.
NASKAH = [
    "Ikan ini muncul empat ratus juta tahun lalu. Jauh sebelum dinosaurus ada. "
    "Lalu hilang dari catatan fosil. Dianggap punah sejak enam puluh enam juta tahun lalu. "
    "Tapi ternyata ia masih ada.",
    "Fosil tertuanya berasal dari zaman Devon, sekitar empat ratus juta tahun lalu. "
    "Artinya ikan ini sudah berenang seratus tujuh puluh juta tahun sebelum dinosaurus pertama muncul.",
    "Dua puluh dua Desember seribu sembilan ratus tiga puluh delapan. Marjorie Courtenay Latimer, "
    "kurator museum di Afrika Selatan, melihat ikan biru sepanjang satu setengah meter "
    "di antara tumpukan tangkapan nelayan.",
    "Ia beri nama Latimeria chalumnae. Dari bahasa Yunani: koilos, rongga, dan akantha, duri. "
    "Jadi namanya berarti duri berongga. Ciri lainnya, siripnya berdaging, bukan tipis seperti ikan biasa.",
    "Tahun seribu sembilan ratus sembilan puluh tujuh, nelayan di Manado menangkap ikan yang sama. "
    "Dua tahun kemudian ilmuwan menamainya Latimeria menadoensis. Indonesia punya spesiesnya sendiri.",
    "Sirip berdaging itu membuat ilmuwan menghubungkannya dengan nenek moyang hewan berkaki empat. "
    "Tapi bukan nenek moyang langsung. Ia kerabat jauh, bukan leluhur kita.",
    "Karena itu ia sering disebut fosil hidup. Sebenarnya keliru. Ia tetap berevolusi, hanya lambat. "
    "Genomnya dua koma delapan miliar huruf. Masa kehamilannya diperkirakan sampai tiga tahun.",
    "Sekarang populasinya di Komoro diperkirakan tinggal ratusan. Ia sering tertangkap jaring tanpa sengaja. "
    "Uni Internasional untuk Konservasi Alam menempatkannya di status kritis.",
    "Tiga hal. Lebih tua dari dinosaurus. Ditemukan dua kali, dan yang kedua di Indonesia. "
    "Lalu kini terancam. Ikuti KlikTahu, dan simpan video ini.",
]

AUDIO_DIR = "vo58"
_DEF_DUR = [10.6, 10.2, 11.4, 11.0, 10.8, 10.2, 11.2, 10.6, 9.6]

SUMBER = [
    "Fosil: Devon ±400 juta tahun (Forey 1998)",
    "Fosil Devon ±400 jt th · dinosaurus ±230 jt th",
    "East London Museum, 22 Desember 1938",
    "Latimeria chalumnae · Smith 1939",
    "Latimeria menadoensis · Pouyaud dkk. 1999",
    "Sirip cuping (lobed fin) · tetrapoda ±375 jt th",
    "Nature 2013 (genom 2,86 Gb) · kehamilan ±3 th",
    "IUCN Red List: kritis (critically endangered)",
    "Sumber: Nature 2013 · IUCN · East London Museum",
]


# ---------------------------------------------------------------- timeline
def _path_timing():
    return os.path.join(BASE, "audio", AUDIO_DIR, "timing.json")


def _muat_durasi():
    p = _path_timing()
    if not os.path.exists(p):
        # Pratinjau tata letak sebelum VO ada: pakai durasi cadangan, tetapi
        # render final wajib memakai timing hasil ukur klip (penjaga di bawah).
        if os.environ.get("KT_SEMENTARA"):
            return list(_DEF_DUR)
        raise RuntimeError(
            f"timeline belum ada: {p}\njalankan: python3 mesin_v20_suara.py "
            f"--episode mesin_v21_ep58 --dari-klip audio/{AUDIO_DIR}/sumber "
            f"--keluar keluaran/KlikTahu_Ep58_audio.m4a --target-lufs=-14"
        )
    d = json.load(open(p))
    dur = [float(x) for x in d["dur"]]
    if len(dur) != len(_DEF_DUR):
        raise RuntimeError(f"{p} berisi {len(dur)} babak, seharusnya {len(_DEF_DUR)}")
    return dur


# ---------------------------------------------------------------- bantu gambar
def _pas_judul(baris, maxw=940, size=88, min_size=54):
    s = size
    while s > min_size and max(tw(b, I.F_BOLD, s) for b in baris) > maxw:
        s -= 2
    return s


def _dasar(kategori=KATEGORI, fakta=None, sumber=None) -> K.Komposisi:
    komp = K.Komposisi(kategori=kategori, fakta=fakta, total=TOTAL_FAKTA)
    K.hud(komp.dasar, kategori)
    if fakta:
        komp.tambah(K.tab_fakta(fakta, TOTAL_FAKTA), W // 2, Z["tab"], 0.02, 0.30,
                    "turun", tengah=True)
    if sumber:
        K.sumber_teks(komp.dasar, sumber, 0.9)
    return komp


def _judul(komp, baris, t0=0.10, size=None, warna=TINTA, sorot=None, d=10.0):
    """Judul besar + stabilo spidol TEPAT di belakang satu kata (gaya acuan)."""
    size = size or _pas_judul(baris)
    lh = int(size * 1.16)
    y0 = Z["headline"]
    for i, b in enumerate(baris):
        y = y0 + i * lh
        if sorot and sorot[0] == i:
            kata = b.split()
            j = sorot[1]
            pre = " ".join(kata[:j])
            lebar_pre = K.ukur(pre, size, I.F_BOLD, -0.6) if pre else 0
            w_pre = K.ukur((pre + " ") if pre else "", size, I.F_BOLD, -0.6)
            x0 = 74 + w_pre - (w_pre - lebar_pre if pre else 0) - 6
            ww = K.ukur(kata[j], size, I.F_BOLD, -0.6) + 14
            # sprite teks dipotong rapat (cap top ≈ 0,05*size, baseline ≈ 0,78*size)
            # stabilo diletakkan di paruh bawah huruf dan melewati garis dasar,
            # jadi tetap terlihat walau katanya pendek ("66", "2", "±500")
            komp.tambah(K.highlighter_spr(int(ww), int(size * 0.52)),
                        x0, y + int(size * 0.46), t0 + 0.30, 0.42, "tulis", alpha=0.95)
        komp.tambah(K.teks(b, warna, size, I.F_BOLD, -0.6), 74, y, t0 + i * 0.07,
                    0.30, "turun")
    return y0 + lh * len(baris)


def _kartu_besar(komp, t0=0.16):
    komp.kartu(70, Z["kartu_y0"], 940, Z["kartu_y1"] - Z["kartu_y0"], 48, KARTU, t0, 0.42)


def _angka(komp, nilai, satuan, ket=None, t0=0.5, warna=CORAL, x=74, y=None):
    """Angka besar + satuan + keterangan (isi strip bawah, pengganti ruang kosong)."""
    y = Z["angka"] if y is None else y
    s = K.teks(nilai, warna, 138, I.F_BOLD, -1.2)
    komp.tambah(s, x, y, t0, 0.36, "pop")
    if satuan:
        u = K.teks(satuan, TINTA, 40, I.F_BOLD, 0.6)
        komp.tambah(u, x + s.shape[1] + 20, y + int(138 * 0.40), t0 + 0.08, 0.30, "kiri")
    if ket:
        g = K.teks(ket, TINTA_2, 32, I.F_MED, 0.2)
        komp.tambah(g, x + 6, y + int(138 * 0.86), t0 + 0.16, 0.30, "fade")
    return s


def _panel_teks(komp, baris, y=None, t0=0.0, warna=TINTA, size=36,
                isi=KARTU_2, maks_w=None):
    """Panel kertas berisi keterangan. Baris dibungkus otomatis supaya tidak
    melewati tepi panel (dulu teks panjang menembus keluar kartu)."""
    y = Z["panel"] if y is None else y
    maks_w = maks_w or (W - 144 - 88)
    size = min(size, 36)
    for _ in range(14):
        if size <= 22:
            break
        potong = [I.wrap(b, I.F_SEMI, size, maks_w) for b in baris]
        if all(len(p2) == 1 for p2 in potong):
            break
        size -= 2
    potong = [I.wrap(b, I.F_SEMI, size, maks_w) for b in baris]
    semua = [x for p2 in potong for x in p2]
    lh = int(size * 1.52)
    hh = 30 + len(semua) * lh
    komp.kartu(72, y, W - 144, hh, 28, isi, t0, 0.34, "pop")
    for i, b in enumerate(semua):
        komp.tambah(K.teks(b, warna, size, I.F_SEMI, 0.2), 112, y + 20 + i * lh,
                    t0 + 0.08 + i * 0.06, 0.28, "kiri")
    return y + hh


def _stiker(komp, t, x, y, t0, jenis="gelap", size=36, rot=0.0, tengah=False, alpha=1.0):
    return komp.tambah(K.stiker(t, jenis, size, rot), x, y, t0, 0.30, "pop",
                       tengah=tengah, alpha=alpha)


def _strip_stiker(komp, t, t0, jenis="koral"):
    """Stiker di sisi kanan strip bawah, sejajar angka besar."""
    spr = K.stiker(t, "coral" if jenis == "koral" else "gelap", 32, -2.0)
    komp.tambah(spr, W - 74 - spr.shape[1], Z["angka"] + 24, t0, 0.30, "pop")


# ================================================================ babak
def _bab1(d):
    """HOOK: ikan berenang di kartu laut, judul besar, stiker pembalik."""
    komp = _dasar(sumber=SUMBER[0])
    _judul(komp, ["IKAN INI SUDAH", "PUNAH 66 JUTA", "TAHUN LALU"], size=84,
           sorot=(1, 1), d=d)
    _kartu_besar(komp)
    komp.tambah(K.kolom_laut(860, 860, atas=(164, 210, 230), bawah=(12, 38, 66),
                             bintang=30), 110, 600, 0.14, 0.44, "fade")
    komp.tambah(K.teks("0 m", (255, 255, 255), 32, I.F_SEMI, 0.8), 138, 618,
                0.30, 0.26, "fade", alpha=0.95)
    komp.tambah(K.teks("500 m", (255, 255, 255), 32, I.F_SEMI, 0.8), 138, 1000,
                0.38, 0.26, "fade", alpha=0.95)
    ikan_spr = K.ikan(660, 330, warna=(28, 60, 92))
    komp.goyang(ikan_spr, 250, 880, t0=0.26, amp=12.0, lam=2.6, fase=0.7, dur=0.40)

    def gerak(k, t):
        if t < 0.26 * d:
            return
        f = clamp((t - 0.26 * d) / 1.0)
        K.tempel(k, ikan_spr, 250 - int(34 * eio(f)), 880 + int(9 * math.sin(t * 1.6)),
                 0.99 * f)
    komp.dinamis.append(gerak)
    _stiker(komp, "SEHARUSNYA PUNAH", 146, 1244, 0.42 * d, "coral", 36, -3)
    _stiker(komp, "TAPI MASIH ADA", 508, 1338, 0.52 * d, "gelap", 36, 2.5)
    _angka(komp, "66", "JUTA TAHUN", "sejak hilang dari catatan fosil", 0.58 * d)
    _strip_stiker(komp, "MASIH ADA", 0.64 * d)
    return komp


def _bab2(d):
    """FAKTA 1: 400 juta tahun, 170 juta tahun sebelum dinosaurus."""
    komp = _dasar(fakta=1, sumber=SUMBER[1])
    _judul(komp, ["LEBIH TUA DARI", "DINOSAURUS"], sorot=(1, 0), d=d)
    _kartu_besar(komp)
    komp.tambah(K.pil("ZAMAN DEVON SAMPAI HARI INI", KARTU_2, TINTA_2, 28, 22, 11,
                      radius=13, garis=KERTAS_3, lebar=2.0), 130, 596, 0.30, 0.26, "pop")
    # garis waktu VERTIKAL (lebih terbaca di 9:16 daripada mendatar)
    x = 232
    komp.tambah(K.raster(10, 800, lambda p: p.rrect(0, 0, 10, 800, 5, fill=KERTAS_3), ss=2),
                x - 5, 640, 0.24, 0.30, "fade")
    titik = ((700, CORAL, "400 JUTA TH", "ikan ini muncul"),
             (1010, TEAL, "230 JUTA TH", "dinosaurus muncul"),
             (1330, NAVY, "66 JUTA TH", "hilang dari fosil"))
    for i, (yy, warna, tebal, ket) in enumerate(titik):
        komp.tambah(K.raster(56, 56, lambda p, w=warna: p.circ(28, 28, 14, fill=w),
                             ss=2), x - 28, yy - 28, 0.34 + i * 0.16, 0.32, "pop")
        komp.tambah(K.teks(tebal, warna, 40, I.F_BOLD, 0.4), 300, yy - 34,
                    0.40 + i * 0.16, 0.26, "kiri")
        komp.tambah(K.teks(ket, TINTA_2, 32, I.F_MED, 0.2), 300, yy + 12,
                    0.46 + i * 0.16, 0.26, "kiri")
    # jarak 170 juta tahun
    komp.tambah(K.panah(110, 74, CORAL, "bawah"), 296, 742, 0.72, 0.28, "fade")
    komp.tambah(K.teks("170 juta tahun", CORAL, 34, I.F_BOLD, 0.4), 392, 772, 0.78, 0.26, "kiri")
    komp.goyang(K.ikan(360, 180, warna=(34, 70, 104)), 560, 1180, t0=0.84,
                amp=7.0, lam=2.6, fase=1.9, dur=0.34)
    _angka(komp, "400", "JUTA TAHUN LALU", "fosil tertua yang pernah ditemukan", 0.34 * d)
    return komp


def _bab3(d):
    """FAKTA 2: 22 Desember 1938, Marjorie, 1,5 meter."""
    komp = _dasar(fakta=2, sumber=SUMBER[2])
    _judul(komp, ["DITEMUKAN DI", "TUMPUKAN IKAN"], sorot=(1, 0), d=d)
    _kartu_besar(komp)
    komp.tambah(K.putar(K.koran(360, 450), 5.0), 118, 606, 0.24, 0.42, "pop", alpha=0.97)
    komp.tambah(K.teks("DESEMBER 1938", TINTA, 30, I.F_BOLD, 1.4), 148, 640, 0.34, 0.24, "fade")
    komp.tambah(K.kaca_pembesar(104, NAVY), 800, 600, 0.62, 0.32, "pop")
    komp.goyang(K.ikan(500, 250, warna=(38, 78, 118)), 430, 900, t0=0.44,
                amp=8.0, lam=2.6, fase=2.6, dur=0.36)
    komp.tambah(K.stiker("1,5 METER", "coral", 40, 4.0), 626, 792, 0.58, 0.30, "pop")
    _stiker(komp, "MARJORIE COURTENAY-LATIMER", 126, 1176, 0.70 * d, "gelap", 31, -1.6)
    komp.tambah(K.teks("kurator museum, 24 tahun", TINTA_2, 32, I.F_MED, 0.3),
                130, 1268, 0.76, 0.26, "fade")
    komp.tambah(K.pil("KAPTEN HENDRIK GOOSEN · 22 DES 1938", KARTU_2, TINTA, 28, 24, 12,
                      radius=14, garis=TINTA_2, lebar=2.0), 126, 1322, 0.82, 0.28, "pop")
    _angka(komp, "1938", "", "East London, Afrika Selatan", 0.36 * d, NAVY)
    return komp


def _bab4(d):
    """FAKTA 3: nama Latin = duri berongga."""
    komp = _dasar(fakta=3, sumber=SUMBER[3])
    _judul(komp, ["NAMANYA BERARTI", "DURI BERONGGA"], sorot=(1, 1), d=d)
    _kartu_besar(komp)
    komp.tambah(K.teks("LATIMERIA", TINTA, 104, I.F_BOLD, -1.2), 126, 616, 0.22, 0.30, "turun")
    komp.tambah(K.teks("CHALUMNAE", CORAL, 104, I.F_BOLD, -1.2), 126, 736, 0.30, 0.30, "turun")
    komp.tambah(K.teks("dari Sungai Chalumna, tempat ia ditemukan", TINTA_2, 32,
                       I.F_MED, 0.2), 130, 864, 0.42, 0.26, "fade")
    for i, (a, b) in enumerate((("KOILOS", "rongga"), ("AKANTHA", "duri"))):
        x = 126 + i * 400
        komp.kartu(x, 930, 356, 160, 26, (238, 233, 222), 0.50 + i * 0.08, 0.30)
        komp.tambah(K.teks(a, TEAL, 44, I.F_BOLD, 0.6), x + 28, 960, 0.56 + i * 0.08, 0.24, "fade")
        komp.tambah(K.teks("= " + b, TINTA_2, 34, I.F_MED, 0.2), x + 28, 1020, 0.62 + i * 0.08, 0.24, "fade")
    komp.tambah(K.pil("PANJANG SAMPAI 2 M · BERAT 90 KG", CORAL, (255, 250, 244),
                      28, 24, 12, radius=14), 126, 1130, 0.70, 0.30, "pop")
    komp.goyang(K.ikan(460, 230, warna=(30, 64, 98)), 470, 1210, t0=0.78,
                amp=7.0, lam=2.6, fase=0.3, dur=0.34)
    _panel_teks(komp, ["Dideskripsikan J.L.B. Smith pada 1939",
                       "Satu-satunya genus Latimeria yang masih hidup"],
                Z["panel"], 0.88 * d, size=36)
    return komp


def _bab5(d):
    """FAKTA 4: Manado 1997, spesies kedua 1999."""
    komp = _dasar(fakta=4, sumber=SUMBER[4])
    _judul(komp, ["SPESIES KEDUA", "LAHIR DI MANADO"], sorot=(1, 2), d=d)
    _kartu_besar(komp)
    komp.tambah(K.peta(820, 500), 130, 600, 0.24, 0.42, "fade")
    komp.tambah(K.pil("KOMORO · 1938", KARTU, NAVY, 27, 22, 11, radius=13, garis=NAVY),
                142, 848, 0.44, 0.26, "pop")
    komp.tambah(K.pil("MANADO · 1997", CORAL, (255, 250, 244), 27, 22, 11, radius=13),
                548, 618, 0.52, 0.26, "pop")
    komp.goyang(K.ikan(300, 150, warna=(34, 70, 104)), 616, 748, t0=0.60,
                amp=7.0, lam=2.6, fase=1.2, dur=0.32)
    _stiker(komp, "1997 · NELAYAN MANADO", 126, 1146, 0.68 * d, "gelap", 31, -1.6)
    komp.tambah(K.pil("1999 · LATIMERIA MENADOENSIS", CORAL, (255, 250, 244), 30, 24, 12,
                      radius=14), 122, 1246, 0.78 * d, 0.28, "pop")
    komp.tambah(K.teks("jarak 8.000 km dari Komoro", TINTA_2, 30, I.F_MED, 0.3),
                130, 1322, 0.84, 0.26, "fade")
    _angka(komp, "2", "SPESIES DI DUNIA", "satu di Komoro, satu di Indonesia",
           0.40 * d, TEAL)
    return komp


def _bab6(d):
    """FAKTA 5: sirip cuping -> kerabat tetrapoda, bukan leluhur langsung."""
    komp = _dasar(fakta=5, sumber=SUMBER[5])
    _judul(komp, ["KERABAT", "HEWAN BERKAKI EMPAT"], sorot=(0, 0), d=d)
    _kartu_besar(komp)
    komp.tambah(K.sirip(370, 330, "lobed"), 128, 606, 0.24, 0.36, "fade")
    komp.tambah(K.sirip(370, 330, "ray"), 566, 606, 0.32, 0.36, "fade")
    komp.tambah(K.panah(90, 64, CORAL, "kanan"), 500, 700, 0.44, 0.26, "fade")
    komp.tambah(K.teks("SIRIP BERDAGING", TEAL, 30, I.F_BOLD, 0.8), 140, 950, 0.48, 0.24, "fade")
    komp.tambah(K.teks("SIRIP BERSIRIP-JARI", TINTA_2, 30, I.F_BOLD, 0.8), 578, 950, 0.54, 0.24, "fade")
    komp.goyang(K.ikan(420, 210, warna=(30, 64, 98)), 132, 1030, t0=0.60,
                amp=8.0, lam=2.6, fase=2.2, dur=0.32)
    komp.tambah(K.manusia(300, (96, 108, 120)), 700, 1010, 0.66, 0.30, "pop")
    komp.tambah(K.teks("tetrapoda\n±375 jt th", TINTA_2, 30, I.F_MED, 0.2),
                760, 1320, 0.72, 0.24, "fade")
    komp.tambah(K.teks("BUKAN LELUHUR LANGSUNG", TINTA, 40, I.F_BOLD, 0.2),
                136, 1290, 0.80 * d, 0.26, "turun")

    def coret(k, t):
        if t < 0.86 * d:
            return
        K.coret(k, 134, 1298, tw("BUKAN LELUHUR LANGSUNG", I.F_BOLD, 40) + 6,
                CORAL, 4.5, clamp((t - 0.86 * d) / 0.45))
    komp.dinamis.append(coret)
    _panel_teks(komp, ["Sirip itu menopang tubuh di dasar laut — bukan untuk berjalan.",
                       "Kesamaan bentuk ≠ garis keturunan langsung."],
                Z["panel"], 0.90 * d, size=32)
    return komp


def _bab7(d):
    """FAKTA 6: mitos 'fosil hidup' + genom + kehamilan."""
    komp = _dasar(fakta=6, sumber=SUMBER[6])
    _judul(komp, ["BUKAN FOSIL", "HIDUP"], sorot=(1, 0), d=d)
    _kartu_besar(komp)
    komp.tambah(K.teks("FOSIL HIDUP", TINTA, 96, I.F_BOLD, -1.0), 126, 606, 0.22, 0.30, "turun")

    def coret(k, t):
        if t < 0.30 * d:
            return
        K.coret(k, 116, 640, tw("FOSIL HIDUP", I.F_BOLD, 96) + 10, CORAL, 6,
                clamp((t - 0.30 * d) / 0.45))
    komp.dinamis.append(coret)
    komp.tambah(K.teks("= SALAH KAPRAH", CORAL, 44, I.F_BOLD, 0.6), 126, 730, 0.36, 0.26, "fade")
    komp.tambah(K.teks("Ia tetap berevolusi — hanya lambat.", TINTA_2, 34, I.F_MED, 0.2),
                128, 800, 0.44, 0.26, "fade")
    for i, (angka, unit, ket) in enumerate((("2,86", "MILIAR HURUF", "genomnya"),
                                           ("±3", "TAHUN", "masa kehamilan"))):
        x = 120 + i * 452
        komp.kartu(x, 880, 410, 250, 30, (238, 233, 222), 0.52 + i * 0.10, 0.32)
        komp.tambah(K.teks(angka, CORAL if i == 0 else TEAL, 88, I.F_BOLD, -1.0),
                    x + 32, 906, 0.58 + i * 0.10, 0.28, "pop")
        komp.tambah(K.teks(unit, TINTA, 28, I.F_BOLD, 1.0), x + 32, 1006, 0.64 + i * 0.10, 0.24, "fade")
        komp.tambah(K.teks(ket, TINTA_2, 28, I.F_MED, 0.2), x + 32, 1050, 0.70 + i * 0.10, 0.24, "fade")
    komp.goyang(K.telur_embrio(360, 180, 5), 340, 1180, t0=0.80,
                amp=6.0, lam=2.6, fase=1.5, dur=0.32)
    komp.goyang(K.ikan(360, 190, warna=(30, 64, 98)), 640, 1170, t0=0.86,
                amp=7.0, lam=2.6, fase=0.9, dur=0.30)
    _panel_teks(komp, ["2,86 miliar huruf — hampir sebesar genom manusia (3,1 miliar).",
                       "Lambat berevolusi, bukan berhenti."], Z["panel"], 0.90 * d, size=32)
    return komp


def _bab8(d):
    """FAKTA 7: populasi menurun, status kritis."""
    komp = _dasar(fakta=7, sumber=SUMBER[7])
    _judul(komp, ["KINI TINGGAL", "RATUSAN SAJA"], sorot=(1, 0), d=d)
    _kartu_besar(komp)
    komp.tambah(K.teks("POPULASI DI KOMORO", TINTA_2, 30, I.F_SEMI, 0.9),
                130, 598, 0.24, 0.24, "fade")
    nilai = (1000.0, 700.0, 520.0, 380.0)
    komp.tambah(K.grafik_batang(500, 320, nilai, CORAL, maks=1000), 130, 650, 0.30, 0.36, "fade")
    for i, lab in enumerate(("1980", "1995", "2005", "kini")):
        komp.tambah(K.teks(lab, TINTA_2, 26, I.F_SEMI, 0.4), 144 + int(i * 114), 980,
                    0.46 + i * 0.06, 0.22, "fade")
    komp.tambah(K.pil("STATUS: KRITIS", CORAL, (255, 250, 244), 34, 26, 12, radius=16),
                646, 690, 0.56, 0.30, "pop")
    komp.tambah(K.teks("critically endangered", TINTA_2, 28, I.F_MED, 0.3),
                652, 756, 0.64, 0.24, "fade")
    komp.tambah(K.teks("IUCN Red List", TINTA_2, 26, I.F_MED, 0.3), 652, 792, 0.70, 0.24, "fade")
    komp.goyang(K.ikan(320, 160, warna=(30, 64, 98)), 646, 860, t0=0.74,
                amp=7.0, lam=2.6, fase=3.0, dur=0.32)
    _stiker(komp, "TERTANGKAP JARING TANPA SENGAJA", 128, 1150, 0.84 * d, "gelap", 30, -1.4)
    komp.tambah(K.teks("bukan diburu, tapi mati karena tidak sengaja", TINTA_2, 30, I.F_MED, 0.3),
                132, 1236, 0.88, 0.26, "fade")
    komp.tambah(K.pil("TURUN ±60% DALAM 40 TAHUN", KARTU_2, CORAL, 30, 24, 12,
                      radius=14, garis=CORAL, lebar=2.4), 128, 1316, 0.92, 0.28, "pop")
    _angka(komp, "±500", "EKOR", "diperkirakan tersisa di Komoro", 0.40 * d)
    return komp


def _bab9(d):
    """PENUTUP: tiga hal + CTA."""
    komp = _dasar(sumber=SUMBER[8])
    _judul(komp, ["INGAT TIGA", "HAL INI"], sorot=(1, 0), d=d)
    _kartu_besar(komp)
    baris = (("1", "LEBIH TUA DARI DINOSAURUS", "400 juta tahun, 170 juta lebih awal", CORAL),
             ("2", "DITEMUKAN DUA KALI", "1938 di Afrika, 1997 di Manado", TEAL),
             ("3", "KINI TERANCAM KRITIS", "tersisa ratusan, tertangkap jaring", GOLD))
    for i, (n, judul, ket, warna) in enumerate(baris):
        y = 612 + i * 186
        komp.goyang(K.raster(64, 64, lambda p, w=warna: p.circ(32, 32, 30, fill=w), ss=2),
                    126, y, t0=0.30 + i * 0.14, amp=5.0, lam=2.9,
                    fase=0.5 + i * 1.1, dur=0.28)
        komp.tambah(K.teks(n, (255, 252, 246), 40, I.F_BOLD, 0.0), 148, y + 8,
                    0.34 + i * 0.14, 0.24, "fade")
        komp.tambah(K.teks(judul, TINTA, 42, I.F_BOLD, 0.2), 214, y + 2,
                    0.38 + i * 0.14, 0.26, "kiri")
        komp.tambah(K.teks(ket, TINTA_2, 32, I.F_MED, 0.2), 214, y + 54,
                    0.44 + i * 0.14, 0.26, "kiri")
    komp.goyang(K.kartu(600, 180, 34, NAVY), 130, 1180, t0=0.62 * d, amp=4.0,
                lam=3.4, fase=0.4, dur=0.36)
    komp.tambah(K.teks("IKUTI KlikTahu", (252, 248, 240), 50, I.F_BOLD, -0.4),
                186, 1204, 0.86 * d, 0.28, "pop")
    komp.tambah(K.teks("satu fakta baru, setiap hari", (204, 218, 232), 30, I.F_MED, 0.3),
                186, 1268, 0.92 * d, 0.24, "fade")
    _stiker(komp, "SIMPAN VIDEO INI", 176, 1408, 0.80 * d, "coral", 34, -2)

    _strip_stiker(komp, "SATU FAKTA BARU", 0.88 * d)
    return komp


_BAB = [_bab1, _bab2, _bab3, _bab4, _bab5, _bab6, _bab7, _bab8, _bab9]


# ================================================================ perakit
_CACHE = {"siap": False, "scenes": [], "komp": [], "total": 0.0}


def siapkan():
    if _CACHE["siap"]:
        return _CACHE
    dur = _muat_durasi()
    t = 0.0
    _CACHE["scenes"] = []
    _CACHE["komp"] = []
    for i, (d, fn) in enumerate(zip(dur, _BAB)):
        _CACHE["scenes"].append({"id": f"B{i + 1}", "nama": BABAK[i][0],
                                 "mulai": t, "dur": d, "fakta": BABAK[i][1]})
        _CACHE["komp"].append(fn(d))
        t += d
    _CACHE["total"] = t
    _CACHE["siap"] = True
    return _CACHE


def daftar():
    c = siapkan()
    return {"total": c["total"], "scenes": c["scenes"], "fps": FPS, "judul": JUDUL}


def naskah():
    return list(NASKAH)


def frame(t: float) -> np.ndarray:
    c = siapkan()
    t = max(0.0, min(t, c["total"] - 1e-4))
    idx = 0
    for i, s in enumerate(c["scenes"]):
        if s["mulai"] <= t < s["mulai"] + s["dur"] or i == len(c["scenes"]) - 1:
            idx = i
            if s["mulai"] <= t < s["mulai"] + s["dur"]:
                break
    s = c["scenes"][idx]
    lt = t - s["mulai"]
    k = c["komp"][idx].frame(lt)
    # sapuan pita pada awal babak (transisi khas acuan)
    if lt < 0.55:
        K.sapuan(k, lt / 0.50, ROSE if idx % 2 == 0 else PASIR, 0.32)
    # kilau kertas melintas di tengah babak: menjaga layar tidak terasa beku
    K.kilau(k, lt, s["dur"] * 0.42, 1.8, 40, 1000, 545, 1420, 0.42)
    # progres segmen di bawah
    fakta = s["fakta"]
    if fakta:
        K.gambar_progres(k, fakta - 1, clamp(lt / s["dur"]), TOTAL_FAKTA)
    else:
        K.gambar_progres(k, 0 if idx == 0 else TOTAL_FAKTA - 1,
                         1.0 if idx else clamp(lt / s["dur"]), TOTAL_FAKTA)
    return k


# ================================================================ pratinjau
def _pratinjau():
    from PIL import Image
    c = siapkan()
    os.makedirs("build_v21/pratinjau", exist_ok=True)
    fs = []
    for i, s in enumerate(c["scenes"]):
        for frac in (0.35, 0.80, 0.97):
            p = f"build_v21/pratinjau/B{i + 1}_{int(frac * 100)}.jpg"
            Image.fromarray(frame(s["mulai"] + s["dur"] * frac)).save(p, quality=92)
            fs.append(p)
    kol = 3
    bar = (len(fs) + kol - 1) // kol
    sheet = Image.new("RGB", (400 * kol, 711 * bar), (0, 0, 0))
    for i, f in enumerate(fs):
        sheet.paste(Image.open(f).resize((400, 711)), ((i % kol) * 400, (i // kol) * 711))
    out = "build_v21/pratinjau/_lembar.jpg"
    sheet.save(out, quality=92)
    print(f"[lembar] {out}  total {c['total']:.2f} s  {len(fs)} frame")


if __name__ == "__main__":
    os.environ.setdefault("KT_SEMENTARA", "1")
    _pratinjau()


# ---------------------------------------------------------------- publikasi
META = dict(
    judul="Ikan Ini Seharusnya Punah 66 Juta Tahun Lalu — Ternyata Masih Hidup",
    judul_pilihan=[
        "Ikan Ini Seharusnya Punah 66 Juta Tahun Lalu — Ternyata Masih Hidup",
        "Ikan yang Dianggap Punah 66 Juta Tahun Lalu, Ditemukan Lagi di Manado",
        "Coelacanth: Ikan Purba 400 Juta Tahun yang Masih Berenang Sampai Sekarang",
    ],
    deskripsi=(
        "Ikan ini sudah ada 400 juta tahun lalu, jauh sebelum dinosaurus. Lalu hilang dari "
        "catatan fosil selama 66 juta tahun dan dianggap punah. Pada 22 Desember 1938, "
        "Marjorie Courtenay-Latimer menemukannya di tumpukan tangkapan nelayan. Enam puluh "
        "tahun kemudian, nelayan Manado menangkap ikan yang sama — dan ilmuwan menamainya "
        "Latimeria menadoensis.\n\n"
        "Di video ini: kenapa ia disebut fosil hidup (dan kenapa sebutan itu keliru), "
        "apa arti namanya, kenapa siripnya penting untuk studi hewan berkaki empat, "
        "berapa besar genomnya, dan kenapa kini statusnya kritis.\n\n"
        "Sumber: Forey 1998; Smith 1939; Pouyaud dkk. 1999; Nature 2013 (genom Latimeria); "
        "IUCN Red List."
    ),
    tag=("coelacanth, ikan purba, latimeria, latimeria menadoensis, manado, hewan purba, "
         "fosil hidup, sains indonesia, ikan langka, evolusi, dinosaurus, fakta hewan, "
         "kliktahu, sains dalam 2 menit"),
)

#: Bingkai untuk thumbnail: (indeks babak, fraksi durasi) — BUKAN detik absolut,
#: supaya thumbnail tetap benar kalau timeline VO berubah (jebakan 6 v20).
THUMB = dict(
    t_bg=(0, 0.97),
    atas=["IKAN INI SUDAH"],
    besar="PUNAH?",
    angka="400",
    ket="JUTA TAHUN, TAPI MASIH ADA",
    t_alt=(1, 0.97),
    alt_atas=["LEBIH TUA DARI"],
    alt_besar="DINOSAURUS",
    alt_kecil=["400 juta tahun, 170 juta lebih awal", "Sudah berenang sebelum pohon pertama"],
)

CATATAN_STRATEGI = [
    "3 detik pertama: klaim besar + angka 66 juta tahun. Tidak ada intro, tidak ada salam.",
    "Sembilan babak, satu ide per layar — pola 7 FAKTA yang terbukti menahan penonton di kanal ini.",
    "Angka diucapkan sebagai kata (empat ratus juta) supaya TTS tidak salah baca.",
    "Setiap babak punya satu ilustrasi vektor baru: laut, garis waktu, koran, sirip, peta, telur.",
    "Koreksi mitos di babak 6 dan 7 memberi alasan menonton sampai habis dan memicu komentar.",
    "Penutup meminta simpan (bukan like saja): simpan = sinyal retensi terkuat di Shorts.",
    "Sudut lokal (Manado) dipakai sebagai pemicu komentar dan kebanggaan penonton Indonesia.",
]
