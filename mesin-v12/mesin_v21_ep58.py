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
import mesin_v21_panggung as P  # noqa: E402
import mesin_v21_real as R  # noqa: E402
from mesin_v18_inti import (blit, clamp, eio, eo, lerp, seg, smooth,  # noqa: E402
                            tw)
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

AUDIO_DIR = "vo60"   # satu suara, satu sesi (id-ID); pengganti vo58
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


# ================================================================ tata letak
# Seluruh episode memakai GRID yang sama. Keluhan "banyak elemen tidak
# beraturan" muncul karena versi sebelumnya menaruh elemen dengan koordinat
# manual per babak; sekarang setiap babak WAJIB mengisi slot yang sama:
#
#   HUD      40..118      (watermark kiri, kategori kanan)
#   TAB      122..218     (FAKTA n/7, di tengah)
#   JUDUL    236..520     (2-3 baris, dipusatkan vertikal di slotnya)
#   PANGGUNG 556..1372    (kartu ilustrasi, isi bergerak)
#   CAPTION  1392..1454   (stiker/pil, satu baris)
#   ANGKA    1476..1626   (angka besar + satuan)
#   KETERANGAN 1640..1690
#   SUMBER   1836
#
# `_audit()` memeriksa hasilnya secara terukur (margin aman + tidak ada dua
# teks yang bertumpuk) dan render MENOLAK jalan kalau ada pelanggaran.
MARGIN = 56
BOX = (MARGIN, 556, W - MARGIN * 2, 816)
JUDUL_Y0, JUDUL_Y1 = 236, 520
CAP_Y = 1392
NUM_Y = 1476
KET_Y = 1640
AMAN_BAWAH = H - 78
#: Lama transisi penutup->hook (detik). Lihat `_outro`.
LOOP_DUR = 0.85


def _dasar(kategori=KATEGORI, fakta=None, sumber=None) -> K.Komposisi:
    komp = K.Komposisi(kategori=kategori, fakta=fakta, total=TOTAL_FAKTA)
    K.hud(komp.dasar, kategori)
    if fakta:
        komp.tambah(K.tab_fakta(fakta, TOTAL_FAKTA), W // 2, Z["tab"], 0.02, 0.30,
                    "turun", tengah=True)
    if sumber:
        K.sumber_teks(komp.dasar, sumber, 0.9)
    return komp


def _pusat_judul(baris, size=None, maxw=None):
    """Ukuran font yang membuat SEMUA baris muat dalam lebar slot judul."""
    # 18 px = lekukan kiri tempat teks diletakkan (MARGIN + 18), jadi lebar
    # maksimum harus dikurangi 18 px supaya tepi KANAN tetap di dalam margin.
    maxw = maxw or (W - MARGIN * 2 - 18)
    size = size or 88
    while size > 52 and max(tw(b, I.F_BOLD, size) for b in baris) > maxw:
        size -= 2
    return size


def _judul(komp, baris, t0=0.10, size=None, warna=TINTA, sorot=None, d=10.0):
    """Judul 2-3 baris + satu kata distabilo. Blok dipusatkan di slot judul."""
    size = _pusat_judul(baris, size)
    lh = int(size * 1.16)
    blok = lh * len(baris)
    y0 = JUDUL_Y0 + max(0, (JUDUL_Y1 - JUDUL_Y0 - blok) // 2)
    for i, b in enumerate(baris):
        y = y0 + i * lh
        spr = K.teks(b, warna, size, I.F_BOLD, -0.6)
        if sorot and sorot[0] == i:
            # ukuran stabilo dari MASK kata itu sendiri (bukan `size`), dan
            # tingginya ±1,48 x tinggi huruf supaya terbaca sebagai blok
            # spidol, bukan garis bawah (lihat docs/MESIN_V21.md jebakan 26).
            kata = b.split()
            j = sorot[1]
            pre = " ".join(kata[:j])
            x_kata = MARGIN + 18 + (K.ukur(pre + " ", size, I.F_BOLD, -0.6) if pre else 0)
            sk = K.teks(kata[j], warna, size, I.F_BOLD, -0.6)
            m = sk[..., 3] > 40
            ys, xs = np.nonzero(m)
            kap = int(ys.max() - ys.min() + 1)
            hh = int(kap * 1.48)
            top = y + int(ys.min()) - int(kap * 0.25)
            ww = int(xs.max() - xs.min() + 1) + 20
            xx = x_kata + int(xs.min()) - 10
            komp.tambah(K.highlighter_spr(ww, max(12, hh)),
                        xx, top, t0 + 0.30, 0.42, "tulis", alpha=0.95,
                        jenis="dekor")
        komp.tambah(spr, MARGIN + 18, y, t0 + i * 0.07, 0.30, "turun")
    return y0 + blok


def _panggung(komp, nama, d):
    """Daftarkan panggung ilustrasi sebagai lapis PRA (di belakang teks).

    Kartu panggung sendiri dibuat di sini (statis), sedangkan isinya bergerak
    lewat `komp.pra` sehingga z-order tetap benar: latar -> panggung -> teks.
    """
    komp.pra.append(lambda k, t, n=nama: P.gambar(n, k, BOX, t, d))
    return BOX


def _caption(komp, teks, t0, jenis="gelap", rot=0.0, ikon=True):
    """Satu baris keterangan pada pelat, selalu di slot CAPTION."""
    size = 34
    while size > 22 and K.ukur(teks, size, I.F_BOLD, 0.2) > BOX[2] - 20:
        size -= 2
    spr = K.stiker(teks, jenis, size, rot)
    komp.tambah(spr, MARGIN + 6, CAP_Y, t0, 0.30, "pop")
    return spr


def _naik(nilai, t, t0, dur=0.75, desimal=0, ribu="."):
    """Angka yang naik (count-up). Mengembalikan string terformat."""
    p = clamp((t - t0) / max(1e-3, dur))
    p = 1 - (1 - p) ** 2.2
    v = nilai * p
    if desimal:
        return f"{v:.{desimal}f}".replace(".", ",")
    return f"{int(round(v)):,}".replace(",", ribu)


def _angka(komp, akhir, satuan, ket=None, t0=0.55, warna=CORAL, desimal=0, ribu=".",
           size=150):
    """Angka besar di slot ANGKA + satuan + keterangan (count-up, lebar tetap).

    Lebar digit dikunci dengan memakai string angka terpanjang yang mungkin
    sebagai pengukur, sehingga blok tidak bergeser saat angka naik.
    """
    def gambar_angka(k, t):
        teks_now = _naik(akhir, t, t0, desimal=desimal, ribu=ribu)
        teks_penuh = _naik(akhir, 99, t0, desimal=desimal, ribu=ribu)
        spr = K.teks(teks_now, warna, size, I.F_BOLD, -1.4)
        lebar = K.teks(teks_penuh, warna, size, I.F_BOLD, -1.4).shape[1]
        blit(k, spr, MARGIN + 16 + lebar - spr.shape[1], NUM_Y, clamp((t - t0) * 6))
        if satuan:
            u = K.teks(satuan, TINTA, 40, I.F_BOLD, 0.6)
            blit(k, u, MARGIN + 16 + lebar + 22, NUM_Y + int(size * 0.40),
                 clamp((t - t0 - 0.25) * 4))
        if ket:
            g = K.teks(ket, TINTA_2, 30, I.F_MED, 0.2)
            blit(k, g, MARGIN + 20, KET_Y, clamp((t - t0 - 0.45) * 4))
    komp.dinamis.append(gambar_angka)


def _audit(komp, nama="babak", ketat=True):
    """Periksa tata letak: margin aman + tidak ada dua kotak teks bertumpuk."""
    T = R.Tata()
    for l in komp.lapis:
        # Kotak yang diperiksa adalah PIXEL TERLIHAT (alpha > 8), bukan kanvas
        # sprite. Sprite teks selalu membawa padding, dan pita tab selebar
        # layar; memakai ukuran kanvas membuat audit menuduh elemen yang
        # sebenarnya jauh di dalam margin.
        m = l.spr[..., 3] > 8 if l.spr.ndim == 3 else np.ones(l.spr.shape[:2], bool)
        if not m.any():
            continue
        ys, xs = np.nonzero(m)
        bx, by = int(l.x + xs.min()), int(l.y + ys.min())
        bw, bh = int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
        jenis = getattr(l, "jenis", "teks")
        T.daftar(f"{nama}:{len(T.kotak)}", bx, by, bw, bh, jenis)
    salah = T.periksa()
    if salah and ketat:
        raise RuntimeError(f"tata letak {nama} tidak lulus audit:\n  - " + "\n  - ".join(salah))
    return salah


# ================================================================ babak
def _bab1(d):
    """HOOK: laut dalam, ikan berenang, stiker pembalik.

    Berbeda dari babak lain, hook TIDAK boleh punya frame kosong: pemirsa
    memutuskan berhenti/menonton dalam 1-3 detik pertama. Karena itu judul,
    stiker, dan angka sudah dalam keadaan MATANG di t=0 (t0 negatif), bukan
    beranimasi masuk. Ini juga yang membuat frame terakhir bisa disamakan
    persis dengan frame pertama (loop mulus).
    """
    komp = _dasar(sumber=SUMBER[0])
    _judul(komp, ["IKAN INI SUDAH", "PUNAH 66 JUTA", "TAHUN LALU"], size=84,
           sorot=(1, 1), d=d, t0=-1.0)
    _panggung(komp, "laut", d)
    _caption(komp, "SEHARUSNYA PUNAH 66 JUTA TAHUN LALU", -1.0, "coral", -1.2)
    _angka(komp, 66, "JUTA TAHUN", "sejak hilang dari catatan fosil", -1.0)
    return komp


def _bab2(d):
    """FAKTA 1: 400 juta tahun, 170 juta tahun sebelum dinosaurus."""
    komp = _dasar(fakta=1, sumber=SUMBER[1])
    _judul(komp, ["LEBIH TUA DARI", "DINOSAURUS"], sorot=(1, 0), d=d)
    _panggung(komp, "umur", d)
    _caption(komp, "SELISIH 170 JUTA TAHUN", 0.50 * d, "gelap", -1.0)
    _angka(komp, 400, "JUTA TAHUN LALU", "fosil tertua yang pernah ditemukan", 0.58 * d)
    return komp


def _bab3(d):
    """FAKTA 2: 22 Desember 1938, Marjorie melihat ikan di tumpukan nelayan."""
    komp = _dasar(fakta=2, sumber=SUMBER[2])
    _judul(komp, ["DITEMUKAN DI", "TUMPUKAN IKAN"], sorot=(1, 0), d=d)
    _panggung(komp, "temuan", d)
    _caption(komp, "MARJORIE COURTENAY-LATIMER · 24 TAHUN", 0.46 * d, "gelap", 1.0)
    _angka(komp, 1938, "", "East London, Afrika Selatan · 22 Desember", 0.56 * d)
    return komp


def _bab4(d):
    """FAKTA 3: nama = duri berongga; 2 m, 90 kg."""
    komp = _dasar(fakta=3, sumber=SUMBER[3])
    _judul(komp, ["NAMANYA BERARTI", "DURI BERONGGA"], sorot=(1, 1), d=d)
    _panggung(komp, "nama", d)
    _caption(komp, "DIDESKRIPSIKAN J.L.B. SMITH · 1939", 0.52 * d, "gelap", -0.8)
    _angka(komp, 2, "METER · 90 KG", "satu-satunya genus Latimeria yang masih hidup",
           0.58 * d)
    return komp


def _bab5(d):
    """FAKTA 4: spesies kedua di Manado, 1997/1999."""
    komp = _dasar(fakta=4, sumber=SUMBER[4])
    _judul(komp, ["SPESIES KEDUA", "LAHIR DI MANADO"], sorot=(1, 2), d=d)
    _panggung(komp, "peta", d)
    _caption(komp, "NELAYAN MANADO · 1997 · MENADOENSIS 1999", 0.50 * d, "coral", 0.8)
    _angka(komp, 2, "SPESIES DI DUNIA", "satu di Komoro, satu di Indonesia", 0.60 * d)
    return komp


def _bab6(d):
    """FAKTA 5: sirip cuping -> kerabat tetrapoda, bukan leluhur langsung."""
    komp = _dasar(fakta=5, sumber=SUMBER[5])
    _judul(komp, ["KERABAT", "HEWAN BERKAKI EMPAT"], sorot=(0, 0), d=d)
    _panggung(komp, "sirip", d)
    _caption(komp, "KEMIRIPAN BENTUK BUKAN GARIS KETURUNAN", 0.50 * d, "gelap", -0.9)
    _angka(komp, 375, "JUTA TAHUN LALU", "perkiraan kemunculan tetrapoda", 0.58 * d)
    return komp


def _bab7(d):
    """FAKTA 6: 'fosil hidup' keliru; genom 2,86 Gb; hamil ±3 tahun."""
    komp = _dasar(fakta=6, sumber=SUMBER[6])
    _judul(komp, ["BUKAN FOSIL", "HIDUP"], sorot=(1, 0), d=d)
    _panggung(komp, "mitos", d)
    _caption(komp, "EVOLUSINYA LAMBAT, TAPI TIDAK BERHENTI", 0.50 * d, "gelap", 0.9)
    _angka(komp, 286, "MILIAR HURUF", "genom 2,86 Gb · masa kehamilan ±3 tahun",
           0.58 * d, desimal=0, size=150)
    return komp


def _bab8(d):
    """FAKTA 7: populasi tinggal ratusan, status kritis."""
    komp = _dasar(fakta=7, sumber=SUMBER[7])
    _judul(komp, ["KINI TINGGAL", "RATUSAN SAJA"], sorot=(1, 0), d=d)
    _panggung(komp, "ancaman", d)
    _caption(komp, "TERTANGKAP JARING TANPA SENGAJA", 0.50 * d, "coral", -1.1)
    _angka(komp, 500, "EKOR", "perkiraan populasi di Komoro", 0.58 * d)
    return komp


def _bab9(d):
    """PENUTUP: tiga hal + ajakan menyimpan."""
    komp = _dasar(sumber=SUMBER[8])
    _judul(komp, ["INGAT TIGA", "HAL INI"], sorot=(1, 0), d=d)
    # kartu ringkasan mengisi slot panggung
    komp.kartu(BOX[0], BOX[1], BOX[2], 560, 44, KARTU, 0.16, 0.42)
    baris = (("1", "LEBIH TUA DARI DINOSAURUS", "400 juta tahun, 170 juta lebih awal", CORAL),
             ("2", "DITEMUKAN DUA KALI", "1938 di Afrika, 1997 di Manado", TEAL),
             ("3", "KINI TERANCAM KRITIS", "tersisa ratusan, tertangkap jaring", GOLD))
    for i, (n, judul, ket, warna) in enumerate(baris):
        y = BOX[1] + 62 + i * 172
        komp.goyang(K.raster(64, 64, lambda p, w=warna: p.circ(32, 32, 30, fill=w), ss=2),
                    BOX[0] + 56, y, t0=0.30 + i * 0.14, amp=4.0, lam=2.9,
                    fase=0.5 + i * 1.1, dur=0.28)
        komp.tambah(K.teks(n, (255, 252, 246), 38, I.F_BOLD, 0.0), BOX[0] + 74, y + 8,
                    0.34 + i * 0.14, 0.24, "fade")
        komp.tambah(K.teks(judul, TINTA, 40, I.F_BOLD, 0.2), BOX[0] + 136, y + 2,
                    0.38 + i * 0.14, 0.26, "kiri")
        komp.tambah(K.teks(ket, TINTA_2, 30, I.F_MED, 0.2), BOX[0] + 136, y + 52,
                    0.44 + i * 0.14, 0.26, "kiri")
    # ajakan: kartu navy + stiker
    kartu = K.kartu(BOX[2] - 60, 168, 34, NAVY)
    komp.goyang(kartu, BOX[0] + 30 - 34, 1152 - 34, t0=0.62 * d, amp=3.4, lam=3.4,
                fase=0.4, dur=0.36)
    komp.tambah(K.teks("IKUTI KlikTahu", (252, 248, 240), 48, I.F_BOLD, -0.4),
                BOX[0] + 76, 1176, 0.86 * d, 0.28, "pop")
    komp.tambah(K.teks("satu fakta baru, setiap hari", (216, 230, 243), 30, I.F_MED, 0.3),
                BOX[0] + 76, 1240, 0.92 * d, 0.24, "fade")
    _caption(komp, "SIMPAN VIDEO INI", 0.78 * d, "coral", -1.6)
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
        komp = fn(d)
        # Audit tata letak dijalankan untuk SETIAP babak. Kalau ada elemen
        # keluar margin atau dua kotak teks bertumpuk, render menolak jalan
        # (ketat=True) — tidak ada lagi cacat tata letak yang lolos diam-diam.
        _audit(komp, f"B{i + 1}:{BABAK[i][0]}")
        _CACHE["komp"].append(komp)
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
    # ---- penutup = awal (loop mulus)
    # Shorts diputar berulang. Kalau frame terakhir berbeda jauh dari frame
    # pertama, penonton melihat "potongan" setiap kali video mengulang, dan
    # itu menurunkan rasio tonton-ulang. Jadi 0,85 detik terakhir kartu
    # ringkasan ditutup "tirai kertas", isinya ditukar ke frame HOOK, lalu
    # tirainya dibuka — frame terakhir identik dengan frame pertama.
    if idx == len(c["scenes"]) - 1:
        sisa = s["dur"] - lt
        if sisa <= LOOP_DUR:
            q = 1.0 - max(0.0, sisa) / LOOP_DUR           # 0 .. 1
            k = _outro(k, q)
    return k


def _hook_frame() -> np.ndarray:
    """Frame pertama episode (komposisi hook), dibuat sekali.

    Mengembalikan SALINAN. `_tirai()` menggambar di atas array yang diberikan;
    kalau yang dikembalikan adalah array cache, tirai akan tercetak permanen ke
    dalam cache dan frame terakhir jadi tirai yang tidak pernah terbuka
    (bug nyata: QC "loop halus" 57,6/255 padahal uji mesin 0,12).
    """
    if _CACHE.get("hook") is None:
        _CACHE["hook"] = _CACHE["komp"][0].frame(0.0)
    return _CACHE["hook"].copy()


def _tirai(k: np.ndarray, s: float) -> np.ndarray:
    """Tirai kertas: kotak krem membesar menutup layar (s=1) lalu mengecil.

    Dipakai transisi penutup -> hook. Kartu krem MENUTUP seluruh layar pada
    s=1, jadi isi layar bisa ditukar di baliknya tanpa pernah terlihat
    sebagai dua tata letak yang saling tembus (versi pertama memakai wipe
    silang: judul hook dan kartu ringkasan terlihat bersamaan — terbaca
    sebagai gambar ganda, bukan transisi).
    """
    if s <= 0.004:
        return k
    w = int((W + 260) * s)
    h = int((H + 260) * s)
    spr = _tirai_spr(w, h)
    blit(k, spr, (W - w) // 2, (H - h) // 2)
    # Saat layar tertutup penuh, tampilkan penanda kanal di tengah: jeda satu
    # warna datar selalu terbaca sebagai "video macet", penanda merek tidak.
    if s > 0.5:
        m = _cap_besar()
        a = clamp((s - 0.5) / 0.4)
        blit(k, m, (W - m.shape[1]) // 2, (H - m.shape[0]) // 2, a)
    return k


_TIRAI = {}
_CAP = {}


def _cap_besar() -> np.ndarray:
    """Watermark `@KlikTahu` diperbesar 2,4x untuk penutup (di-cache)."""
    m = _CAP.get("spr")
    if m is None:
        from PIL import Image
        wm = K.watermark()
        m = np.asarray(Image.fromarray(wm).resize(
            (int(wm.shape[1] * 2.4), int(wm.shape[0] * 2.4)), Image.LANCZOS))
        _CAP["spr"] = m
    return m


def _tirai_spr(w: int, h: int) -> np.ndarray:
    kunci = (w, h)
    spr = _TIRAI.get(kunci)
    if spr is None:
        r = int(min(w, h) * 0.05) + 8
        spr = K.raster(w, h, lambda p: p.rrect(0, 0, w, h, r, fill=KERTAS_3), ss=1)
        _TIRAI[kunci] = spr
    return spr


def _outro(k: np.ndarray, q: float) -> np.ndarray:
    """Penutup -> hook dalam 0..1 detik transisi (q=0 kartu, q=1 hook)."""
    if q < 0.50:
        s = I.eob(q / 0.50)                 # 0 -> 1 : tirai menutup
    else:
        s = 1.0 - I.eob((q - 0.50) / 0.50)  # 1 -> 0 : tirai membuka
    isi = _hook_frame() if q >= 0.50 else k
    return _tirai(isi, s)


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
