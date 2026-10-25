#!/usr/bin/env python3
"""mesin_v21_real.py — ilustrasi "2D realistis" + motion graphics untuk gaya KERTAS.

Kenapa modul terpisah
---------------------
Keluhan pemilik: "tidak realistis dalam 2D, ini sangat penting karena penonton
bisa membayangkannya dengan mudah". Yang membuat gambar vektor terasa *datar dan
murahan* bukan jumlah detail, melainkan tidak adanya isyarat yang dipakai otak
untuk membaca benda nyata:

  1. **Arah cahaya yang konsisten** — satu sumber (kiri atas), semua benda
     mengikuti: sisi atas terang, sisi bawah gelap, bayangan jatuh ke kanan-bawah.
  2. **Oklusi & kontak** — benda tidak boleh "menempel tanpa jejak"; ada gelap
     tipis di sambungan (sirip ke badan, kartu ke kertas) dan bayangan kontak.
  3. **Kedalaman** — tiga lapis: latar (kabut jauh), tengah (subjek), depan
     (partikel/gelembung) dengan ukuran & kontras berbeda.
  4. **Counter-shading** — punggung gelap, perut terang (hewan air nyata);
     gradasi ini yang paling kuat membuat bentuk terbaca sebagai volume.
  5. **Refleksi/spekular tepat di tepi** — garis tipis terang di tepi atas
     membentuk "highlight" yang membuat permukaan terlihat punya ketebalan.

Isi modul
---------
  `ikan_real()`       coelacanth anatomi lengkap: 8 sirip, ekor 3 cuping,
                      counter-shading, sisik, insang, mata bercincin emas,
                      rim light, oklusi di pangkal sirip
  `laut_dalam()`      panggung laut: gradasi kedalaman, sinar bergerak,
                      partikel paralaks, siluet jauh, kaustik, vignette
  `partikel_laut()`   butir laut (sisa organik) untuk lapis depan
  `sinar_bergerak()`  berkas cahaya permukaan (aditif, bergeser & berdenyut)
  `lensa()`           kaca pembesar yang benar-benar membesarkan isi di bawahnya
  `bayang_kontak()`   elips bayangan lembut (benda menyentuh bidang)
  `gerak_halus()`     kurva gerak (ease in-out + pegas ringan) untuk motion graphics
  `hitung_naik()`     angka yang naik (count-up) dengan lebar digit tetap
  `tulis_jalur()`     garis yang tergambar progresif (untuk peta/garis waktu)

Semua fungsi deterministik terhadap waktu (tidak ada random per frame) supaya
render paralel menghasilkan frame identik.
"""
from __future__ import annotations

import functools
import math
import os
import sys

import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import mesin_v18_inti as I  # noqa: E402
from mesin_v18_inti import (F_BOLD, F_MED, F_SEMI, blit, clamp, mask, mix,  # noqa: E402
                            raster, rng, shade, spr_text, with_a)

W, H = 1080, 1920

# Palet air (dipakai semua ilustrasi laut supaya satu keluarga warna)
AIR_ATAS = (168, 214, 232)
AIR_TENGAH = (58, 122, 158)
AIR_BAWAH = (10, 34, 58)
TINTA_AIR = (8, 24, 40)
IKAN_GELAP = (28, 58, 88)
IKAN_TERANG = (120, 168, 196)
PERUT = (206, 196, 176)


# =============================================================== bantu
def _tinggi_mask(spr) -> tuple[int, int]:
    m = spr[..., 3] > 40
    ys, xs = np.nonzero(m)
    return int(ys.max() - ys.min() + 1), int(xs.max() - xs.min() + 1)


def _halus(pts, n=6):
    """Catmull-Rom: poligon jadi lengkung mulus (dipakai siluet ikan)."""
    P = list(pts)
    m = len(P)
    out = []
    for i in range(m):
        p0, p1, p2, p3 = P[(i - 1) % m], P[i], P[(i + 1) % m], P[(i + 2) % m]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append((0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t
                               + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                               + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                        0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t
                               + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                               + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    return out


# =============================================================== anatomi ikan
#: Proporsi diambil dari foto spesimen museum (coelacanth dewasa, sisi kiri):
#:   panjang total (moncong->ujung ekor) = 1,00
#:   mata pada 0,17 · pangkal sirip punggung I 0,46 · punggung II 0,64
#:   pangkal ekor 0,86 · ekor (kipas 3 cuping) 0,86-1,00
#:   tinggi badan 0,36 dari panjang (ikan INI memang dalam, bukan torpedo)
#: Koordinat y dinormalkan pada KOTAK sprite (0 atas, 1 bawah).
_BADAN = [
    (0.000, 0.430),   # ujung moncong, tepi atas mulut
    (0.030, 0.372),
    (0.080, 0.330),
    (0.140, 0.300),   # ubun-ubun
    (0.220, 0.276),
    (0.300, 0.246),
    (0.380, 0.256),
    (0.460, 0.262),   # pangkal sirip punggung I
    (0.540, 0.244),
    (0.630, 0.250),   # pangkal sirip punggung II
    (0.700, 0.268),
    (0.760, 0.298),
    (0.812, 0.340),
    (0.856, 0.386),   # pangkal ekor (masih tebal)
    (0.868, 0.436),
    (0.856, 0.500),
    (0.812, 0.556),
    (0.760, 0.600),
    (0.700, 0.638),   # pangkal sirip dubur
    (0.630, 0.668),
    (0.540, 0.690),
    (0.460, 0.702),   # perut terdalam
    (0.380, 0.706),
    (0.300, 0.700),
    (0.230, 0.686),
    (0.170, 0.660),
    (0.110, 0.620),
    (0.060, 0.570),
    (0.022, 0.516),
]

_PUNGGUNG = [  # (x0, x1, puncak_x, puncak_y, lebar_dasar)
    (0.452, 0.556, 0.500, 0.038, 1.00),   # sirip punggung I: tinggi, membulat
    (0.622, 0.712, 0.664, 0.128, 0.92),   # sirip punggung II: lebih pendek
]
_EKOR = (0.846, 0.306, 0.180, 0.716)      # x pangkal, y atas, tengah, bawah


@functools.lru_cache(maxsize=16)
def _sirip_bulat(w: int, h: int, warna, arah: str = "atas", cuping: int = 1,
                 lengkung: float = 0.0) -> np.ndarray:
    """Sirip sebagai bentuk MEMBULAT (paddle), bukan segitiga tajam.

    `cuping` > 1 membuat kipas ekor bertingkat. `lengkung` menggeser puncak ke
    samping supaya sirip tampak "meniup" ke belakang, seperti di foto.
    """
    def gambar(p):
        if cuping == 1:
            p.poly(_halus([(0.06 * w, 0.98 * h), (0.16 * w, 0.44 * h),
                           (0.42 * w, 0.06 * h), (0.62 * w, 0.04 * h),
                           (0.86 * w, 0.34 * h), (0.92 * w, 0.72 * h),
                           (0.78 * w, 0.98 * h)], n=6), fill=warna)
        else:
            # kipas ekor: tiga cuping membulat (atas, tengah, bawah)
            p.poly(_halus([(0.04 * w, 0.50 * h),
                           (0.30 * w, 0.16 * h), (0.66 * w, 0.06 * h),
                           (0.92 * w, 0.20 * h), (0.98 * w, 0.34 * h),
                           (0.80 * w, 0.44 * h), (0.96 * w, 0.50 * h),
                           (0.98 * w, 0.66 * h), (0.92 * w, 0.80 * h),
                           (0.66 * w, 0.94 * h), (0.30 * w, 0.84 * h),
                           (0.04 * w, 0.50 * h)], n=6), fill=warna)
    spr = raster(w, h, gambar, ss=3)
    # tulang sirip di dalam bentuk (tidak mencuat keluar)
    def tulang(p):
        n = 7 if cuping == 1 else 9
        for i in range(n):
            f = (i + 0.5) / n
            x0 = (0.10 + 0.10 * f) * w
            y0 = (0.92 - 0.10 * f) * h
            x1 = (0.30 + 0.55 * f) * w
            y1 = (0.20 + 0.62 * abs(f - 0.5) * 1.6) * h
            p.line([(x0, y0), (x1, y1)], mix(warna, (255, 255, 255), 0.40) + (110,),
                   max(1.0, h * 0.016))
    t = raster(w, h, tulang, ss=2)
    M = spr[..., 3].astype(np.float32) / 255.0
    t[..., 3] = (t[..., 3].astype(np.float32) * (M > 0.6)).astype(np.uint8)
    a = t[..., 3:4].astype(np.float32) / 255.0
    spr[..., :3] = (t[..., :3].astype(np.float32) * a +
                    spr[..., :3].astype(np.float32) * (1 - a))
    # pencahayaan dalam sirip: pangkal lebih gelap, puncak lebih terang
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    spr[..., :3] = np.clip(spr[..., :3].astype(np.float32) *
                           (0.86 + 0.30 * (1 - yy))[..., None], 0, 255)
    return spr.astype(np.uint8)


@functools.lru_cache(maxsize=8)
def _ekor_tiga_cuping(w: int, h: int, warna) -> np.ndarray:
    """Kipas ekor coelacanth: tiga cuping membulat dengan dua lekuk.

    Bentuk ini yang paling khas dan paling sering salah digambar: ekor
    coelacanth TIDAK bercabang seperti tuna, melainkan kipas membulat dengan
    cuping atas, cuping tengah kecil, dan cuping bawah.
    """
    def gambar(p):
        p.poly(_halus([(0.00 * w, 0.50 * h),
                       (0.30 * w, 0.20 * h),
                       (0.70 * w, 0.02 * h),   # cuping atas (besar, membulat)
                       (0.94 * w, 0.10 * h),
                       (0.86 * w, 0.30 * h),
                       (0.62 * w, 0.40 * h),   # lekuk atas DALAM
                       (0.94 * w, 0.48 * h),   # cuping tengah
                       (0.99 * w, 0.55 * h),
                       (0.62 * w, 0.62 * h),   # lekuk bawah dalam
                       (0.88 * w, 0.72 * h),
                       (0.94 * w, 0.90 * h),
                       (0.70 * w, 0.98 * h),   # cuping bawah
                       (0.30 * w, 0.80 * h)], n=6), fill=warna)
    spr = raster(w, h, gambar, ss=3)

    def tulang(p):
        for i in range(9):
            f = (i + 0.5) / 9
            y = (0.10 + 0.80 * f) * h
            p.line([(0.06 * w, 0.50 * h), (0.72 * w, y)],
                   mix(warna, (255, 255, 255), 0.42) + (110,), max(1.0, h * 0.012))
    t = raster(w, h, tulang, ss=2)
    M = spr[..., 3].astype(np.float32) / 255.0
    t[..., 3] = (t[..., 3].astype(np.float32) * (M > 0.6)).astype(np.uint8)
    a = t[..., 3:4].astype(np.float32) / 255.0
    spr[..., :3] = (t[..., :3].astype(np.float32) * a +
                    spr[..., :3].astype(np.float32) * (1 - a))
    xx = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    spr[..., :3] = np.clip(spr[..., :3].astype(np.float32) *
                           (1.05 - 0.22 * xx)[..., None], 0, 255)
    return spr.astype(np.uint8)


@functools.lru_cache(maxsize=8)
def ikan_real(w: int = 620, h: int = 340, warna=IKAN_GELAP, perut=PERUT,
              bintik: bool = True, nyala: float = 1.0) -> np.ndarray:
    """Coelacanth vektor: anatomi + pencahayaan yang masuk akal.

    Disusun MODULAR (bukan satu siluet): ekor, dua sirip punggung, sirip dubur,
    sirip dada & perut sebagai bentuk terpisah, lalu badan. Tujuannya bukan
    kerapian kode, tetapi oklusi: setiap sirip punya garis gelap tipis di
    pangkalnya, dan itu yang membuat mata membacanya sebagai benda yang
    menempel pada badan — bukan guntingan kertas.

    Isyarat "realistis 2D": satu arah cahaya (kiri-atas), counter-shading,
    bercak putih tak beraturan khas coelacanth, sisik belah ketupat, mata besar
    dengan iris pucat, mulut terbuka ke bawah, spekular tipis di punggung.
    Catatan bug: versi pertama mengalikan intensitas spekular (0..1) dengan
    nilai piksel 0..255 sehingga tepi badan menjadi putih pekat.
    """
    w, h = int(w), int(h)
    spr = np.zeros((h, w, 4), np.uint8)
    gelap = shade(warna, 0.70)

    def ox(x):  # koordinat x relatif -> piksel
        return int(round(x * w))

    def oy(y):
        return int(round(y * h))

    # ---- 1. ekor tiga cuping (paling belakang, menempel di pangkal ekor)
    ex, ey0, _, ey1 = _EKOR
    tw_, th_ = int(w * 0.200), int(h * (ey1 - ey0))
    ekor = _ekor_tiga_cuping(tw_, th_, shade(warna, 0.90))
    # 0,255 (bukan 0,16): dengan 0,16 ujung ekor melewati tepi kanvas dan
    # terpotong — sirip ekor hilang 1-2% di semua panggung.
    blit(spr, ekor, ox(ex) - int(tw_ * 0.255), oy(ey0))

    # ---- 2. dua sirip punggung + sirip dubur
    for (x0, x1, px, py, _l) in _PUNGGUNG:
        fw, fh = int(w * (x1 - x0) * 1.55), int(h * 0.270)
        fin = _sirip_bulat(fw, fh, shade(warna, 0.86), "atas")
        # digeser TURUN supaya pangkalnya masuk ke dalam badan lalu tertutup
        # badan (oklusi). Menaruhnya pas di garis punggung menyisakan celah.
        blit(spr, fin, ox(px) - fw // 2, oy(py) - fh // 12)
    aw, ah = int(w * 0.090), int(h * 0.150)
    blit(spr, _sirip_bulat(aw, ah, shade(warna, 0.84), "bawah"),
         ox(0.672), oy(0.594))

    # ---- 3. badan
    badan_pts = _halus([(x * w, y * h) for x, y in _BADAN], n=5)
    badan = raster(w, h, lambda p: p.poly(badan_pts, fill=warna), ss=2)
    M = badan[..., 3].astype(np.float32) / 255.0

    # ---------------------------------------------------------------- 3a. volume
    # Badan diberi bentuk TIGA DIMENSI maya: untuk setiap kolom diukur jarak
    # dari garis punggung dan garis perut, lalu dipakai penampang bulat
    # (u = -1 punggung .. +1 perut, z = sqrt(1-u^2)). Dengan itu warna dihitung
    # dari NORMAL permukaan dan satu arah cahaya (kiri-atas), bukan dari gradasi
    # vertikal lurus.
    #
    # Kenapa ini penting: gradasi lurus selalu terbaca sebagai gambar datar
    # yang diberi pita warna (keluhan "tidak realistis"). Penampang bulat
    # memberi isyarat bentuk yang sama dengan foto asli: terang di punggung,
    # gelap di peralihan, lalu terang kembali karena pantulan dari dasar laut.
    m = M > 0.5
    ada = m.any(axis=0)
    atas_ = np.argmax(m, axis=0).astype(np.float32)
    bawah_ = (h - 1 - np.argmax(m[::-1], axis=0)).astype(np.float32)
    bawah_ = np.where(ada, bawah_, atas_)
    cy_ = (atas_ + bawah_) / 2.0
    hh_ = np.maximum(1.0, (bawah_ - atas_) / 2.0)
    Y = np.arange(h, dtype=np.float32)[:, None]
    u = np.clip((Y - cy_[None, :]) / hh_[None, :], -1.0, 1.0)
    z = np.sqrt(np.clip(1.0 - u * u, 0.0, 1.0))
    # arah cahaya (x, y, z) = (-0.34, -0.60, 0.72) -> sinar dari kiri-atas-depan
    lam = np.clip(-0.60 * u + 0.72 * z, 0.0, 1.0)
    X = np.arange(w, dtype=np.float32)[None, :] / max(1, w)
    # cahaya datang dari kiri: makin ke ekor makin redup (0,12 lebih gelap)
    arah_x = 1.02 - 0.26 * X
    terang = (0.40 + 0.72 * lam) * arah_x
    # pantulan dari dasar (bounce) di sisi perut: membuat perut tidak mati
    bounce = np.clip(u, 0, 1) ** 2 * 0.22
    rgb = (np.array(warna, np.float32)[None, None, :] *
           (terang + bounce)[..., None])
    # perut lebih terang dan lebih hangat, tetapi tetap melalui `u` (bentuk),
    # bukan lewat garis batas mendatar
    beli = np.clip((u - 0.15) / 0.85, 0, 1) ** 1.5
    rgb = rgb * (1 - beli[..., None] * 0.55) + \
        np.array(perut, np.float32)[None, None, :] * (beli * 0.52 * (0.55 + 0.6 * lam))[..., None]
    # kilau memanjang di punggung (specular lebar, bukan titik)
    spec = np.exp(-((u + 0.62) ** 2) / 0.045) * np.clip(z, 0, 1)
    rgb = rgb + (spec * 26.0)[..., None] * np.array((0.85, 0.93, 1.0), np.float32)
    # butir halus: mematahkan permukaan rata (satu-satunya tekstur acak di sini)
    rr_n = rng(11)
    noise = rr_n.normal(0, 3.6, (h, w)).astype(np.float32)
    noise = (noise + np.roll(noise, 1, axis=0) + np.roll(noise, -1, axis=0)) / 3.0
    rgb = rgb + noise[..., None]
    badan[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)

    def detail(p):
        terang2 = mix(warna, (255, 255, 255), 0.48)
        # sisik belah ketupat (dua arah busur)
        for baris in range(10):
            y0 = 0.300 + baris * 0.033
            for i in range(12):
                cx = (0.120 + i * 0.048 + (baris % 2) * 0.024) * w
                cy = (y0 + 0.008 * math.sin(i * 0.7)) * h
                r = 0.021 * w
                p.arc(cx - r, cy - r * 0.65, cx + r, cy + r * 0.65, 205, 335,
                      gelap + (55,), 1.0)
                p.arc(cx - r, cy - r * 0.65, cx + r, cy + r * 0.65, 25, 155,
                      terang2 + (30,), 0.9)
        # bercak putih: tidak beraturan, lebih kecil, menggerombol
        if bintik:
            # Bercak coelacanth itu KECIL dan pudar. Versi sebelumnya memakai
            # bintik putih alpha 140..210 sebesar 3-4 px: hasilnya terbaca
            # sebagai cipratan cat, bukan bercak kulit.
            rr = rng(59)
            for _ in range(22):
                gx = rr.uniform(0.16, 0.78)
                gy = 0.330 + 0.050 * gx + rr.uniform(-0.014, 0.026)
                for _k in range(int(rr.integers(1, 4))):
                    bx = (gx + rr.uniform(-0.020, 0.020)) * w
                    by = (gy + rr.uniform(-0.014, 0.014)) * h
                    rx = h * rr.uniform(0.0032, 0.0072)
                    wy = rx * rr.uniform(0.7, 1.3)
                    p.ell(bx - rx, by - wy, bx + rx, by + wy,
                          fill=(238, 236, 226, int(rr.uniform(70, 125))))
        # gurat sisi: satu garis tipis memanjang — penanda "kulit", bukan pola
        p.line([(0.235 * w, 0.462 * h), (0.420 * w, 0.452 * h),
                (0.610 * w, 0.450 * h), (0.760 * w, 0.462 * h)],
               gelap + (70,), max(1.0, h * 0.006))
        # penutup insang besar (pelat membulat)
        # Batas insang: busur PENDEK yang berhenti di punggung perut, bukan
        # garis tipis panjang sampai ke perut (terbaca seperti goresan).
        p.line([(0.198 * w, 0.302 * h), (0.186 * w, 0.400 * h),
                (0.196 * w, 0.492 * h), (0.212 * w, 0.556 * h)],
               gelap + (150,), h * 0.015)
        p.line([(0.212 * w, 0.318 * h), (0.200 * w, 0.400 * h),
                (0.210 * w, 0.470 * h)], terang2 + (80,), h * 0.006)
        # mulut terbuka ke bawah (baji gelap + bibir atas tebal)
        # Mulut coelacanth: celah melengkung di bawah moncong, bukan blok
        # hitam persegi di ujung kepala (versi lama terbaca seperti "paruh").
        p.line([(0.042 * w, 0.462 * h), (0.072 * w, 0.472 * h),
                (0.102 * w, 0.490 * h)],
               shade(warna, 0.24) + (235,), h * 0.020)
        p.line([(0.044 * w, 0.458 * h), (0.074 * w, 0.468 * h),
                (0.100 * w, 0.485 * h)],
               mix(warna, (255, 255, 255), 0.34) + (95,), h * 0.006)
        p.line([(0.046 * w, 0.474 * h), (0.074 * w, 0.484 * h),
                (0.098 * w, 0.500 * h)],
               mix(perut, warna, 0.50) + (130,), h * 0.005)
        # Mata. Kesalahan versi sebelumnya: cincin pucat 1,16x + iris pucat
        # 0,60x membentuk donat putih — mata ikan jadi terbaca seperti
        # "goggles". Urutan yang benar: kelopak tipis -> iris gelap -> pupil
        # lebih gelap -> SATU kilau kecil. Dua kilau membuat mata seperti kaca.
        ex_, ey_, er = 0.168 * w, 0.400 * h, h * 0.045
        p.circ(ex_, ey_, er * 1.10, fill=(172, 188, 198, 120))   # kelopak
        p.circ(ex_, ey_, er, fill=(46, 66, 84))                  # iris
        p.circ(ex_ - er * 0.06, ey_ + er * 0.10, er * 0.86, fill=(30, 45, 60))
        p.circ(ex_, ey_, er * 0.56, fill=(10, 15, 22))           # pupil
        p.circ(ex_ - er * 0.26, ey_ - er * 0.30, er * 0.15, fill=(250, 249, 244))
        p.arc(ex_ - er * 0.9, ey_ - er * 0.9, ex_ + er * 0.9, ey_ + er * 0.9,
              30, 150, (210, 226, 234, 110), max(1.0, er * 0.16))  # pantul bawah

    det = raster(w, h, detail, ss=2)
    mk = (M > 0.55)
    det[..., 3] = (det[..., 3].astype(np.float32) * mk).astype(np.uint8)
    a = det[..., 3:4].astype(np.float32) / 255.0
    badan[..., :3] = (det[..., :3].astype(np.float32) * a +
                      badan[..., :3].astype(np.float32) * (1 - a)).astype(np.uint8)
    blit(spr, badan, 0, 0)

    # ---- 4. sirip dada & perut DI DEPAN badan (menempel, ada oklusi)
    # Sirip dada coelacanth = DAYUNG berdaging, bukan duri. Versi lama
    # (0,185w x 0,150h, putar -24°) menyempit jadi bentuk seperti kumis.
    dw, dh = int(w * 0.215), int(h * 0.205)
    dada = _sirip_bulat(dw, dh, shade(warna, 0.94), "kanan")
    dada = np.array(Image.fromarray(dada, "RGBA").rotate(-34, expand=True,
                                                         resample=Image.BICUBIC))
    blit(spr, bayang_kontak(int(dw * 0.80), int(dh * 0.26), 0.30),
         ox(0.264), oy(0.664))
    blit(spr, dada, ox(0.232), oy(0.596))
    pw, ph = int(w * 0.110), int(h * 0.088)
    perut_fin = _sirip_bulat(pw, ph, shade(warna, 0.90), "kanan")
    perut_fin = np.array(Image.fromarray(perut_fin, "RGBA").rotate(-18, expand=True,
                                                                 resample=Image.BICUBIC))
    blit(spr, bayang_kontak(int(pw * 0.95), int(ph * 0.30), 0.32),
         ox(0.452), oy(0.672))
    blit(spr, perut_fin, ox(0.438), oy(0.648))

    # ---- 5. cahaya: rim atas + spekular (intensitas 0..1, bukan 0..255)
    # Rim hanya memakai mask BADAN (bukan seluruh sprite): kalau sirip ikut
    # dihitung, setiap sirip mendapat garis terang di tepinya dan terbaca
    # sebagai tempelan terpisah dengan garis luar.
    M2 = M.copy()
    gs = 5
    bawah = np.zeros_like(M2)          # mask yang digeser TURUN
    bawah[gs:] = M2[:-gs]
    atas = np.zeros_like(M2)           # mask yang digeser NAIK
    atas[:-gs] = M2[gs:]
    # Rim light hanya di tepi yang menghadap cahaya (tepi atas). Versi lama
    # menambahkan terang di SEMUA tepi, hasilnya ikan berbingkai cahaya
    # seperti stiker — isyarat paling kuat yang membuat gambar terasa palsu.
    yy = np.linspace(0, 1, M2.shape[0], dtype=np.float32)[:, None]
    arah = np.clip(1.25 - yy * 1.10, 0, 1)          # kuat di punggung, nol di perut
    rim = np.clip(M2 - bawah, 0, 1) * arah
    spr[..., :3] = np.clip(spr[..., :3].astype(np.float32) +
                           (rim * 0.26 * nyala)[..., None] *
                           np.array((150, 190, 220), np.float32), 0, 255).astype(np.uint8)
    # oklusi tepi bawah: garis gelap tipis supaya perut tidak menyatu dengan air
    gel = np.clip(M2 - atas, 0, 1) * (1 - arah)
    spr[..., :3] = np.clip(spr[..., :3].astype(np.float32) *
                           (1.0 - 0.16 * gel)[..., None], 0, 255).astype(np.uint8)
    return spr


@functools.lru_cache(maxsize=8)
def sirip_real(w: int, h: int, jenis: str = "lobed", warna=IKAN_GELAP) -> np.ndarray:
    """Sirip tunggal: cuping BERDAGING (paddle) vs sirip BERSIRIP-JARI (kipas).

    Bentuk "lobed" punya tangkai sempit lalu bilah lebar dan membulat — proporsi
    itu yang membuatnya terbaca seperti anggota badan. Versi pertama terlalu
    membulat merata sehingga tampak seperti telur.
    """
    def gambar(p):
        if jenis == "lobed":
            p.poly(_halus([(0.40 * w, 0.99 * h),      # tangkai (sempit)
                           (0.44 * w, 0.74 * h),
                           (0.26 * w, 0.52 * h),      # bilah melebar
                           (0.20 * w, 0.30 * h),
                           (0.32 * w, 0.14 * h),
                           (0.52 * w, 0.06 * h),
                           (0.72 * w, 0.14 * h),
                           (0.80 * w, 0.32 * h),
                           (0.72 * w, 0.54 * h),
                           (0.56 * w, 0.74 * h),
                           (0.52 * w, 0.99 * h)], n=6), fill=warna)
        else:
            # kipas tipis: pangkal sempit, ujung melebar, jari-jari menonjol
            p.poly(_halus([(0.46 * w, 0.99 * h),
                           (0.50 * w, 0.62 * h),
                           (0.34 * w, 0.20 * h),
                           (0.50 * w, 0.04 * h),
                           (0.68 * w, 0.18 * h),
                           (0.54 * w, 0.62 * h),
                           (0.56 * w, 0.99 * h)], n=5),
                   fill=mix(warna, (255, 255, 255), 0.36))
    spr = raster(w, h, gambar, ss=3)
    M = spr[..., 3].astype(np.float32) / 255.0

    def detail(p):
        if jenis == "lobed":
            # sisik pada bilah + gelap di tangkai
            for baris in range(5):
                for i in range(4):
                    cx = (0.30 + i * 0.13 + (baris % 2) * 0.055) * w
                    cy = (0.20 + baris * 0.12) * h
                    p.arc(cx - 0.048 * w, cy - 0.035 * h, cx + 0.048 * w, cy + 0.035 * h,
                          200, 340, shade(warna, 0.58) + (110,), 1.5)
            p.line([(0.43 * w, 0.96 * h), (0.50 * w, 0.72 * h)],
                   shade(warna, 0.55) + (150,), h * 0.030)
        else:
            for i in range(7):
                tt = i / 6
                p.line([((0.47 + 0.06 * tt) * w, 0.96 * h),
                        ((0.36 + 0.28 * tt) * w, (0.12 + 0.30 * abs(0.5 - tt)) * h)],
                       shade(warna, 0.50) + (230,), h * 0.013)
    d = raster(w, h, detail, ss=2)
    d[..., 3] = (d[..., 3].astype(np.float32) * (M > 0.55)).astype(np.uint8)
    a = d[..., 3:4].astype(np.float32) / 255.0
    spr[..., :3] = (d[..., :3].astype(np.float32) * a +
                    spr[..., :3].astype(np.float32) * (1 - a)).astype(np.uint8)
    # cahaya kiri-atas
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    cahaya = 0.82 + 0.40 * np.clip((1 - yy) * 0.55 + (1 - xx) * 0.45, 0, 1)
    spr[..., :3] = np.clip(spr[..., :3].astype(np.float32) * cahaya[..., None], 0, 255)
    return spr.astype(np.uint8)


# =============================================================== panggung laut
@functools.lru_cache(maxsize=6)
def _gradasi_laut(w: int, h: int, atas=AIR_ATAS, tengah=AIR_TENGAH,
                  bawah=AIR_BAWAH) -> np.ndarray:
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    a = np.array(atas, np.float32)[None, None, :]
    b = np.array(tengah, np.float32)[None, None, :]
    c = np.array(bawah, np.float32)[None, None, :]
    t = yy[..., None]
    img = np.where(t < 0.45, a + (b - a) * (t / 0.45),
                   b + (c - b) * ((t - 0.45) / 0.55))
    # cahaya dari kiri atas
    img = img * (1.05 - 0.11 * xx)[..., None]
    # kabut kedalaman di dasar
    img = img + np.clip((yy - 0.72) / 0.28, 0, 1)[..., None] * np.array((8, 26, 44), np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


@functools.lru_cache(maxsize=32)
def partikel_laut(n: int = 40, w: int = 900, h: int = 900, seed: int = 7,
                  lapis: str = "depan") -> list:
    """Butir laut (marine snow): (x, y, r, fase, kecepatan, alfa).

    Deterministik: dipanggil sekali, digerakkan episode dengan rumus waktu.
    """
    rr = rng(seed)
    if lapis == "depan":
        r_lo, r_hi, al = 2.4, 5.6, 0.55
    else:
        r_lo, r_hi, al = 1.2, 2.6, 0.32
    return [(rr.uniform(0, w), rr.uniform(0, h), rr.uniform(r_lo, r_hi),
             rr.uniform(0, 6.28), rr.uniform(0.5, 1.4), al) for _ in range(n)]


@functools.lru_cache(maxsize=64)
def _butir(r: int, alfa: float) -> np.ndarray:
    n = int(r * 2 + 6)
    return raster(n, n, lambda p: p.circ(n / 2, n / 2, r, fill=(236, 246, 250,
                                                               int(255 * alfa))), ss=2)


def partikel_tempel(k, daftar, t: float, w: int, h: int, geser_x: float = 0.0):
    """Tempel butir laut yang naik/turun halus — memberi kedalaman (paralaks)."""
    for (x, y, r, fase, sp, al) in daftar:
        yy = (y + t * 9.0 * sp) % (h + 40) - 20
        xx = (x + 11.0 * math.sin(t * 0.22 * sp + fase) + geser_x) % (w + 40) - 20
        blit(k, _butir(int(round(r)), al), int(xx), int(yy), al * 0.9)


@functools.lru_cache(maxsize=8)
def _sinar_spr(w: int = 620, h: int = 1100) -> np.ndarray:
    """Satu berkas cahaya permukaan (gradien lembut, ujung mengecil)."""
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    lebar = 0.55 + 0.45 * yy                      # makin dalam makin lebar
    # profil "plato lembut" (bukan Gaussian sempit): berkas lebar yang saling
    # menimpa, sehingga tidak terbaca sebagai deretan garis
    inten = np.clip(1.0 - np.abs(xx) / lebar, 0, 1) ** 1.5
    inten = inten * np.clip(1 - yy * 0.75, 0, 1) ** 1.2
    rgb = np.array((226, 244, 255), np.float32)[None, None, :] * inten[..., None]
    spr = np.zeros((h, w, 4), np.uint8)
    spr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    spr[..., 3] = (np.clip(inten, 0, 1) * 255 * 0.55).astype(np.uint8)
    return spr


def sinar_bergerak(k, t: float, x0: float, x1: float, y: float, h: int = 1000,
                   n: int = 4, alfa: float = 1.0, miring: float = 0.16):
    """Berkas cahaya permukaan: lebar, lembut, dan saling menimpa.

    Pelajaran dari versi pertama: berkas sempit berjarak sama terbaca sebagai
    pola "barcode" di layar. Sekarang tiap berkas lebih lebar dari jarak antar
    berkas sehingga yang terlihat hanya bidang cahaya yang bergeser pelan.
    """
    spr = _sinar_spr()
    for i in range(n):
        f = i / max(1, n - 1)
        x = x0 + (x1 - x0) * f
        geser = 34.0 * math.sin(t * 0.22 + i * 1.9) + 16.0 * math.sin(t * 0.09 + i)
        denyut = 0.70 + 0.30 * math.sin(t * 0.34 + i * 2.1)
        blit(k, spr, int(x + geser + (y * miring)), int(y), alfa * denyut * 0.30)


def laut_dalam(w: int, h: int, r: int = 40, t: float = 0.0, *, dalam: bool = True,
               sinar: bool = True, butir: bool = True, siluet: bool = True,
               kaca: bool = False) -> np.ndarray:
    """Kartu panggung laut: gradasi + sinar + partikel + siluet jauh.

    `t` = waktu lokal; semua gerak dihitung dari `t` sehingga render paralel
    identik dan pratinjau sama dengan hasil akhir.
    """
    w, h = int(w), int(h)
    spr = raster(w, h, lambda p: p.rrect(0.5, 0.5, w - 0.5, h - 0.5, r, fill=(0, 0, 0, 255)),
                 ss=2)
    img = _gradasi_laut(w, h)
    mask_r = spr[..., 3].astype(np.float32) / 255.0
    kanvas = img.astype(np.float32)
    # siluet ikan/benda jauh (kabut) — memberi skala & kedalaman
    if siluet:
        for i, (fx, fy, fs, fa) in enumerate(((0.30, 0.30, 0.16, 0.16),
                                              (0.72, 0.20, 0.11, 0.12),
                                              (0.84, 0.62, 0.20, 0.10))):
            ik = ikan_real(int(w * fs), int(w * fs * 0.55),
                           warna=mix(AIR_TENGAH, (14, 44, 70), 0.45))
            ik = ik[:, ::-1] if i == 2 else ik
            kx = int(w * fx + 8 * math.sin(t * 0.16 + i))
            ky = int(h * fy)
            a = (ik[..., 3:4].astype(np.float32) / 255.0) * fa
            hh = min(h - ky, ik.shape[0])
            ww = min(w - kx, ik.shape[1])
            if hh > 0 and ww > 0:
                reg = kanvas[ky:ky + hh, kx:kx + ww]
                kanvas[ky:ky + hh, kx:kx + ww] = (
                    ik[:hh, :ww, :3].astype(np.float32) * a[:hh, :ww] +
                    reg * (1 - a[:hh, :ww]))
    out = np.zeros((h, w, 3), np.uint8)
    out[:] = np.clip(kanvas, 0, 255).astype(np.uint8)
    if sinar:
        sinar_bergerak(out, t, w * 0.05, w * 0.72, -40, h=int(h * 0.92), n=5, alfa=0.55)
    if butir:
        partikel_tempel(out, partikel_laut(46, w, h, 11, "belakang"), t, w, h, 6)
        partikel_tempel(out, partikel_laut(26, w, h, 23, "depan"), t * 1.25, w, h, 18)
    # vignette dalam kartu: tepi gelap tipis supaya bentuk kartu terbaca
    yy = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    r2 = np.clip((xx * 0.9) ** 2 + (yy * 0.75) ** 2, 0, 1.5)
    out = np.clip(out.astype(np.float32) * (1 - 0.20 * r2)[..., None], 0, 255)
    # (kaustik periodik DIHAPUS dari sini: sin(xx*26) pada dasar statis
    # menghasilkan deretan garis tegak rapi — terbaca seperti "barcode".
    # Kaustik sekarang hanya digambar di lapis gerak `Panggung.gambar()`
    # dengan dua frekuensi berbeda, jadi tidak pernah membentuk pola teratur.)
    hasil = np.zeros((h, w, 4), np.uint8)
    hasil[..., :3] = out
    hasil[..., 3] = (mask_r * 255).astype(np.uint8)
    return hasil


# =============================================================== alat bantu 2D
def lensa(k, isi, cx: float, cy: float, r: int = 120, zoom: float = 2.1,
          rot: float = -8.0, t: float = 0.0):
    """Kaca pembesar yang BENAR membesarkan isi kanvas di bawahnya.

    Versi lama hanya menggambar lingkaran + pegangan (tidak membesarkan apa pun)
    sehingga terlihat seperti stiker. Di sini potongan kanvas di sekitar (cx, cy)
    diperbesar `zoom` kali, dipotong lingkaran, lalu diberi pantulan kaca.
    """
    x0, y0 = int(cx - r / zoom), int(cy - r / zoom)
    x1, y1 = x0 + int(2 * r / zoom), y0 + int(2 * r / zoom)
    H_, W_ = k.shape[:2]
    x0c, y0c = max(0, x0), max(0, y0)
    x1c, y1c = min(W_, x1), min(H_, y1)
    if x1c - x0c < 8 or y1c - y0c < 8:
        return
    potong = k[y0c:y1c, x0c:x1c]
    im = Image.fromarray(potong).resize((int(2 * r), int(2 * r)), Image.LANCZOS)
    im = im.rotate(rot, resample=Image.BICUBIC, expand=False)
    bulat = np.array(im)
    # topeng lingkaran + tepi kaca
    n = bulat.shape[0]
    yy = np.arange(n, dtype=np.float32)[:, None] - n / 2
    xx = np.arange(n, dtype=np.float32)[None, :] - n / 2
    d = np.sqrt(xx ** 2 + yy ** 2)
    topeng = np.clip((r - d) / 2.0, 0, 1)
    rgba = np.zeros((n, n, 4), np.uint8)
    rgba[..., :3] = np.clip(bulat.astype(np.float32) * 1.06 + 8, 0, 255).astype(np.uint8)
    rgba[..., 3] = (topeng * 255).astype(np.uint8)
    # pantulan kaca: busur terang di kiri-atas
    refl = np.clip(1.0 - np.abs(d - r * 0.72) / (r * 0.16), 0, 1) * \
        np.clip((-xx - yy) / (r * 1.4), 0, 1)
    rgba[..., :3] = np.clip(rgba[..., :3].astype(np.float32) +
                            (refl * 150)[..., None], 0, 255).astype(np.uint8)
    blit(k, rgba, int(cx - n / 2), int(cy - n / 2))
    # cincin logam + pegangan
    ring = raster(2 * r + 16, 2 * r + 16,
                  lambda p: p.circ(r + 8, r + 8, r + 4,
                                   outline=(58, 72, 86, 235), width=7), ss=3)
    blit(k, ring, int(cx - r - 8), int(cy - r - 8))
    gagang = raster(int(r * 1.1), int(r * 0.30),
                    lambda p: p.rrect(0, 0, r * 1.1, r * 0.30, r * 0.14,
                                      fill=(58, 72, 86)), ss=3)
    gagang = np.array(Image.fromarray(gagang, "RGBA").rotate(rot + 45, expand=True,
                                                            resample=Image.BICUBIC))
    blit(k, gagang, int(cx + r * 0.62), int(cy + r * 0.62))


@functools.lru_cache(maxsize=64)
def bayang_kontak(w: int, h: int, kuat: float = 0.30) -> np.ndarray:
    """Elips bayangan kontak (benda menyentuh bidang) — gradien, bukan blok."""
    w, h = max(4, int(w)), max(4, int(h))
    yy = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    d = np.sqrt(xx ** 2 + yy ** 2)
    a = np.clip(1 - d, 0, 1) ** 1.6
    spr = np.zeros((h, w, 4), np.uint8)
    spr[..., :3] = (46, 40, 34)
    spr[..., 3] = (a * 255 * kuat).astype(np.uint8)
    return spr


def gerak_halus(t: float, dur: float = 0.5, amp: float = 1.0) -> float:
    """Kurva gerak masuk: ease-out kubik + sedikit pegas (tidak "melompat")."""
    p = clamp(t / max(1e-3, dur))
    e = 1 - (1 - p) ** 3
    if p < 1:
        return amp * e
    sisa = clamp((t - dur) / 0.55)
    return amp * (1 + 0.06 * math.sin(sisa * 18) * (1 - sisa) ** 2)


@functools.lru_cache(maxsize=256)
def hitung_naik(angka: float, desimal: int = 0, warna=(26, 40, 55), size: int = 168,
                name: str = F_BOLD, tracking: float = -2.4, ribu: str = ".") -> tuple:
    """Siapkan sprite angka 0..angka untuk count-up (lebar digit tetap).

    Dikembalikan sebagai tuple (tidak bisa di-cache sebagai list). Lebar setiap
    sprite disamakan dengan angka terbesar supaya angka tidak bergeser saat naik
    (penyebab umum "angka goyang" di motion graphics amatir).
    """
    out = []
    for i in range(int(angka) + 1):
        t = f"{i:,}".replace(",", ribu) if ribu else str(i)
        if desimal:
            t = f"{i / 10 ** desimal:.{desimal}f}".replace(".", ",")
        out.append(spr_text(t, warna, name, size, tracking))
    wmaks = max(s.shape[1] for s in out)
    hasil = []
    for s in out:
        if s.shape[1] < wmaks:
            pad = np.zeros((s.shape[0], wmaks, 4), np.uint8)
            pad[:, wmaks - s.shape[1]:] = s        # rata kanan (digit satuan tetap)
            s = pad
        hasil.append(s)
    return tuple(hasil)


def tulis_jalur(k, pts, prog: float, warna=(204, 78, 56), tebal: float = 6.0,
                putus: bool = False):
    """Gambar jalur (peta/garis waktu) secara progresif mengikuti `prog`."""
    prog = clamp(prog)
    if prog <= 0 or len(pts) < 2:
        return
    # panjang kumulatif
    seg = []
    total = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        d = math.dist(a, b)
        seg.append((a, b, total, d))
        total += d
    batas = total * prog
    for a, b, mulai, d in seg:
        if mulai > batas:
            break
        f = 1.0 if mulai + d <= batas else (batas - mulai) / max(1e-6, d)
        bx = a[0] + (b[0] - a[0]) * f
        by = a[1] + (b[1] - a[1]) * f
        n = max(2, int(math.dist(a, (bx, by))))
        if putus:
            for i in range(n):
                if (i // 9) % 2 == 0:
                    t0, t1 = i / n, min(1.0, (i + 5) / n)
                    blit(k, _garis(int(math.dist(a, (bx, by))), tebal, warna, t0, t1),
                         int(a[0]), int(a[1]))
        else:
            x0, y0 = int(min(a[0], bx)), int(min(a[1], by))
            ww = max(2, int(abs(bx - a[0])) + 8)
            hh = max(2, int(abs(by - a[1])) + 8)
            spr = raster(ww, hh, lambda p: p.line(
                [(a[0] - x0 + 4, a[1] - y0 + 4), (bx - x0 + 4, by - y0 + 4)],
                warna, tebal), ss=3)
            blit(k, spr, x0 - 4, y0 - 4)


def _garis(panjang: int, tebal: float, warna, t0: float, t1: float) -> np.ndarray:
    """Potongan garis lurus sepanjang `panjang` (dipakai `tulis_jalur` putus)."""
    panjang = max(2, int(panjang))
    return raster(panjang, int(tebal * 3 + 4), lambda p: p.line(
        [(0, tebal * 1.5 + 2), (panjang, tebal * 1.5 + 2)], warna, tebal), ss=3)


# =============================================================== tata letak
class Tata:
    """Tata letak terukur: setiap elemen mendaftarkan kotaknya.

    Keluhan pemilik "banyak elemen yang tidak beraturan" diselesaikan dengan
    aturan yang BISA DIPERIKSA, bukan dengan perasaan:
      * margin aman 56 px kiri/kanan, 40 px atas, 78 px bawah (Shorts);
      * setiap kotak teks wajib berada di dalam margin;
      * dua kotak TEKS tidak boleh bertumpuk (diperiksa berpasangan);
      * jarak antar-baris konsisten (grid 8 px).
    `periksa()` mengembalikan daftar pelanggaran sehingga render bisa menolak
    jalan kalau tata letak salah — bukan ditemukan setelah video jadi.
    """

    AMAN_X = 56
    AMAN_ATAS = 40
    AMAN_BAWAH = 78

    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.kotak = []

    def daftar(self, nama, x, y, w, h, jenis="teks"):
        """Daftarkan kotak. `jenis="dekor"` (kartu, pita, lingkaran) diberi
        toleransi 18 px di tepi karena bayangan lembut kartu memang menyembul
        sedikit keluar margin — itu bayangan, bukan isi."""
        self.kotak.append({"nama": nama, "x": int(x), "y": int(y),
                           "w": int(w), "h": int(h), "jenis": jenis})
        return self.kotak[-1]

    def periksa(self, ketat=True):
        salah = []
        for b in self.kotak:
            # 34 px = jari-jari sebaran bayangan kartu (PAD_KARTU): bayangan
            # lembut boleh menyentuh tepi luar margin, isi tidak.
            tol = 0 if b["jenis"] == "teks" else 34
            if b["x"] < self.AMAN_X - tol or b["x"] + b["w"] > self.w - self.AMAN_X + tol:
                salah.append(f"{b['nama']}: keluar margin horizontal "
                             f"({b['x']}..{b['x'] + b['w']})")
            if b["y"] < self.AMAN_ATAS or b["y"] + b["h"] > self.h - self.AMAN_BAWAH:
                salah.append(f"{b['nama']}: keluar margin vertikal "
                             f"({b['y']}..{b['y'] + b['h']})")
        teks = [b for b in self.kotak if b["jenis"] == "teks"]
        for i in range(len(teks)):
            for j in range(i + 1, len(teks)):
                a, b = teks[i], teks[j]
                ox = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
                oy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
                if ox > 4 and oy > 4:
                    salah.append(f"teks '{a['nama']}' bertumpuk dengan "
                                 f"'{b['nama']}' ({ox}x{oy} px)")
        return salah if ketat else salah


class Panggung:
    """Kartu panggung ilustrasi: dasar pra-render + lapis gerak per frame.

    Kenapa kelas, bukan fungsi: bagian statis (kartu, gradasi, siluet jauh)
    dihitung SEKALI, sedangkan sinar/partikel/kaustik bergerak tiap frame.
    Tanpa pemisahan ini, render 60 fps akan menghabiskan waktu di gradasi yang
    sama 7.000 kali.
    """

    def __init__(self, w: int, h: int, r: int = 44, *, sinar: bool = True,
                 butir: bool = True, siluet: bool = True, dalam: bool = True,
                 seed: int = 7):
        self.w, self.h, self.r = int(w), int(h), int(r)
        self.sinar_on, self.butir_on = sinar, butir
        self.dasar = laut_dalam(self.w, self.h, r, 0.0, dalam=dalam,
                                sinar=False, butir=False, siluet=siluet)
        self.butir_belakang = partikel_laut(46, self.w, self.h, seed + 4, "belakang")
        self.butir_depan = partikel_laut(24, self.w, self.h, seed + 9, "depan")
        # topeng sudut bulat, dipakai untuk memotong lapis gerak
        self.topeng = raster(self.w, self.h,
                             lambda p: p.rrect(0.5, 0.5, self.w - 0.5,
                                               self.h - 0.5, self.r,
                                               fill=(0, 0, 0, 255)), ss=2)[..., 3]

    def gambar(self, k, x: int, y: int, t: float, alpha: float = 1.0):
        """Tempel panggung pada kanvas di (x, y) dengan gerak waktu `t`.

        Lapis gerak (sinar + partikel + kaustik) digambar pada resolusi SETENGAH
        lalu diperbesar: biaya piksel turun 4x, dan karena isinya gradien lembut
        hasilnya tidak bisa dibedakan pada video akhir. Terukur: 79 ms/frame ->
        24 ms/frame untuk kartu 940x860.
        """
        blit(k, self.dasar, x, y, alpha)
        setengah = 0.5
        sw, sh = int(self.w * setengah), int(self.h * setengah)
        lap = np.zeros((sh, sw, 4), np.uint8)
        if self.sinar_on:
            sinar_bergerak(lap, t, sw * 0.02, sw * 0.62, -14, h=int(sh * 0.92),
                           n=4, alfa=0.34, miring=0.10)
        if self.butir_on:
            partikel_tempel(lap, self.butir_belakang, t, sw, sh, 3)
            partikel_tempel(lap, self.butir_depan, t * 1.2, sw, sh, 8)
        yy = np.linspace(-1, 1, sh, dtype=np.float32)[:, None]
        xx = np.linspace(-1, 1, sw, dtype=np.float32)[None, :]
        # kaustik: dua gelombang berfrekuensi berbeda supaya TIDAK terbaca
        # sebagai pola garis teratur (versi pertama menghasilkan "stripe").
        ka = (np.sin(xx * 6.1 + yy * 2.3 + t * 0.35) +
              0.6 * np.sin(xx * 9.7 - yy * 3.1 - t * 0.21)) * 0.5
        ka = np.clip(ka, 0, 1) ** 2.4 * np.clip(0.30 - yy, 0, 0.30) * 2.6
        lap[..., :3] = np.clip(lap[..., :3].astype(np.float32) +
                               (ka * 34)[..., None], 0, 255).astype(np.uint8)
        lap = np.array(Image.fromarray(lap).resize((self.w, self.h), Image.BILINEAR))
        lap[..., 3] = np.minimum(lap[..., 3], self.topeng)
        blit(k, lap, x, y, alpha)


class IkanBerenang:
    """Ikan yang berenang di dalam panggung: gerak halus + sudut mengangguk.

    Gerak "berenang" bukan goyang sinus sederhana: badan naik-turun pelan,
    sedikit berguling mengikuti arah, dan ekor mendorong (dibaca dari
    perubahan sudut). Semua dari satu parameter waktu supaya deterministik.
    """

    def __init__(self, spr, x: float, y: float, *,
                 amp_x: float = 26.0, amp_y: float = 12.0,
                 lam_x: float = 7.4, lam_y: float = 5.1, fase: float = 0.0,
                 putar: float = 2.6):
        self.spr, self.x0, self.y0 = spr, x, y
        self.ax, self.ay = amp_x, amp_y
        self.lx, self.ly = lam_x, lam_y
        self.fase, self.putar = fase, putar
        # bayangan kontak di bawah ikan (menyatukan dengan bidang)
        self.bayang = bayang_kontak(int(spr.shape[1] * 0.62),
                                    int(spr.shape[0] * 0.16), 0.26)

    def gambar(self, k, t: float, alpha: float = 1.0, dx: float = 0.0, dy: float = 0.0):
        p = t + self.fase
        x = self.x0 + dx + self.ax * math.sin(2 * math.pi * p / self.lx)
        y = self.y0 + dy + self.ay * math.sin(2 * math.pi * p / self.ly)
        putar = self.putar * math.sin(2 * math.pi * p / self.lx - 0.7)
        bx = x + self.spr.shape[1] * 0.05
        by = y + self.spr.shape[0] * 0.90
        blit(k, self.bayang, int(bx), int(by), 0.85 * alpha)
        if abs(putar) > 0.12:
            from PIL import Image as _Im
            s = np.array(_Im.fromarray(self.spr, "RGBA").rotate(
                putar, resample=_Im.BICUBIC, expand=True))
            x -= (s.shape[1] - self.spr.shape[1]) / 2
            y -= (s.shape[0] - self.spr.shape[0]) / 2
        else:
            s = self.spr
        blit(k, s, int(x), int(y), alpha)
