#!/usr/bin/env python3
"""mesin_v21_panggung.py — panggung ilustrasi per babak (gaya KERTAS, 2D realistis).

Satu fungsi = satu babak. Masing-masing menggambar DI DALAM kotak `box`
(x, y, w, h) yang ditentukan episode, sehingga tata letak seluruh video diatur
di satu tempat dan panggung tidak pernah "menggeser" elemen lain.

Aturan yang dipakai semua panggung
----------------------------------
1. Kartu kertas (radius 44) + bayangan kontak, isi dipotong ke bentuk kartu.
2. Satu sumber cahaya (kiri-atas) — semua gradasi & bayangan mengikuti.
3. Kedalaman tiga lapis: latar (kabut), subjek, partikel depan.
4. Setiap label ditempel pada "pelat" (pil/pita) sehingga tidak pernah
   menabrak ilustrasi — inilah yang membuat tata letak terlihat beraturan.
5. Semua gerak dihitung dari waktu `t` (deterministik, aman untuk render
   paralel).

`gambar(nama, k, box, t)` adalah pintu masuk yang dipakai episode.
"""
from __future__ import annotations

import functools
import math
import os
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import mesin_v18_inti as I  # noqa: E402
import mesin_v21_kertas as K  # noqa: E402
import mesin_v21_real as R  # noqa: E402
from mesin_v18_inti import F_BOLD, F_MED, F_SEMI, blit, clamp, mix, raster  # noqa: E402

W, H = 1080, 1920
TINTA, TINTA_2, CORAL, NAVY, TEAL, GOLD, KARTU = (K.TINTA, K.TINTA_2, K.CORAL,
                                                  K.NAVY, K.TEAL, K.GOLD, K.KARTU)


# =============================================================== bantu
def _halus(pts, n=6):
    """Catmull-Rom (lengkung mulus) — dipakai bentuk daratan/pulau."""
    return R._halus(pts, n)


def _kartu(k, box, isi=KARTU, r=44, bayang=True):
    x, y, w, h = box
    if bayang:
        K.kartu_tempel(k, x, y, w, h, r, isi)
    else:
        spr = raster(w, h, lambda p: p.rrect(0.5, 0.5, w - 0.5, h - 0.5, r, fill=isi), ss=2)
        blit(k, spr, x, y)


def _potong_ke_kartu(k, box, gambar_fn, r=44):
    """Gambar isi panggung ke kanvas sementara, lalu tempel dengan topeng kartu."""
    x, y, w, h = box
    lap = np.zeros((h, w, 3), np.uint8)
    lap[:] = KARTU
    gambar_fn(lap)
    m = K.mask_rounded(w, h, r)
    H_, W_ = k.shape[:2]
    x1, y1 = min(W_, x + w), min(H_, y + h)
    x0, y0 = max(0, x), max(0, y)
    reg = k[y0:y1, x0:x1]
    sub = lap[y0 - y:y1 - y, x0 - x:x1 - x]
    mk = m[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)[..., None] / 255.0
    k[y0:y1, x0:x1] = np.clip(reg * (1 - mk) + sub * mk, 0, 255).astype(np.uint8)


def _pelat(k, teks, x, y, warna_isi=(33, 40, 48), warna_teks=(252, 249, 242),
           size=30, jenis="pil", alpha=1.0):
    """Tempel label pada pelat gelap/terang. Mengembalikan (spr, w, h)."""
    if jenis == "pil":
        spr = K.pil(teks, warna_isi, warna_teks, size, 22, 11)
    else:
        spr = K.stiker(teks, "gelap" if warna_isi == (33, 40, 48) else "coral", size, 0)
    blit(k, spr, int(x), int(y), alpha)
    return spr


_LATAR = {}


def _latar(key, w, h, fn) -> np.ndarray:
    """Lapis latar statis (peta, dermaga, sumbu) dihitung SEKALI lalu dipakai ulang.

    Tanpa cache, polygon besar dirasterisasi ulang 7.000 kali sehingga render
    melambat 3-4x tanpa satu pun piksel berbeda.
    """
    k = (key, int(w), int(h))
    if k not in _LATAR:
        lap = np.zeros((int(h), int(w), 3), np.uint8)
        lap[:] = (250, 247, 241)
        fn(lap, int(w), int(h))
        _LATAR[k] = lap
    return _LATAR[k].copy()


def _t(t: float, t0: float, dur: float = 0.45) -> float:
    """Progres masuk (0..1) dengan ease-out; 0 kalau belum mulai."""
    p = clamp((t - t0) / max(1e-3, dur))
    return 1 - (1 - p) ** 3


def _angin(t: float) -> float:
    return math.sin(t * 0.5)


# =============================================================== 1. LAUT
_PG = {}


def _panggung(nama, w, h, seed=7, **kw):
    """Cache panggung per (nama, ukuran) — dasar pra-render, bukan tiap frame."""
    key = (nama, w, h, tuple(sorted(kw.items())))
    if key not in _PG:
        _PG[key] = R.Panggung(w, h, 44, seed=seed, **kw)
    return _PG[key]


def laut(k, box, t, d=10.0):
    """HOOK: laut dalam + coelacanth berenang + skala kedalaman."""
    x, y, w, h = box
    pg = _panggung("laut", w, h, 11)
    pg.gambar(k, x, y, t)
    # ----- ikan berenang (posisi & irama dari waktu)
    # Ikan adalah SUBJEK babak ini: 0,78 lebar kartu (bukan 0,60 — pada 0,60
    # ikan terlihat kecil dan separuh kartu menjadi air kosong), dan pusatnya
    # diletakkan tepat di penanda "500 m" (kedalaman coelacanth sebenarnya).
    ik = R.ikan_real(int(w * 0.78), int(w * 0.78 * 0.44))
    cx = x + w * 0.07 + 26 * math.sin(t * 0.42)
    cy = y + h * 0.30 + 14 * math.sin(t * 0.61 + 1.1)
    putar = 1.8 * math.sin(t * 0.42 - 0.6)
    from PIL import Image as _Im
    sp = np.array(_Im.fromarray(ik, "RGBA").rotate(putar, resample=_Im.BICUBIC, expand=True))
    blit(k, R.bayang_kontak(int(sp.shape[1] * 0.55), int(sp.shape[0] * 0.14), 0.22),
         int(cx + sp.shape[1] * 0.06), int(cy + sp.shape[0] * 0.92), 0.8)
    blit(k, sp, int(cx), int(cy))
    # ----- skala kedalaman (garis + label, di sisi kanan dalam kartu)
    sx = x + w - 74
    garis = raster(6, int(h * 0.78), lambda p: p.rrect(0, 0, 6, h * 0.78, 3,
                                                       fill=(210, 232, 242, 120)), ss=2)
    blit(k, garis, sx, y + int(h * 0.10), 0.85)
    for f, lab in ((0.10, "0 m"), (0.40, "500 m"), (0.76, "4.000 m")):
        yy = y + int(h * f)
        blit(k, raster(26, 6, lambda p: p.rrect(0, 0, 26, 6, 3,
                                                fill=(226, 240, 248, 190)), ss=2),
             sx - 26, yy - 3, 0.9)
        s = K.teks(lab, (232, 244, 250), 26, I.F_SEMI, 0.6)
        blit(k, s, sx - 30 - s.shape[1], yy - s.shape[0] // 2, 0.92)
    # ----- gelembung dari mulut ikan (bukan gelembung acak)
    for i in range(9):
        f = i / 8
        yy = (cy + sp.shape[0] * 0.30) - ((t * (36 + 18 * f) + f * 140) % 420)
        xx = cx + sp.shape[1] * 0.06 + 26 * math.sin(t * 1.2 + i)
        if yy > y + 10:
            blit(k, K.gelembung_spr(3 + (i % 3)), int(xx), int(yy), 0.45)


# =============================================================== 2. UMUR
def umur(k, box, t, d=12.0):
    """FAKTA 1: garis waktu vertikal dengan tiga tonggak + ikan berskala."""
    x, y, w, h = box
    _kartu(k, box)
    _potong_ke_kartu(k, box, lambda lap: _umur_isi(lap, w, h, t))


def _umur_isi(lap, w, h, t):
    def dasar(l, w2, h2):
        ax = int(w2 * 0.22)
        blit(l, raster(8, int(h2 * 0.80), lambda p: p.rrect(0, 0, 8, h2 * 0.80, 4,
                                                            fill=(206, 198, 186)), ss=2),
             ax - 4, int(h2 * 0.10))
    lap[:] = _latar("umur_dasar", w, h, dasar)
    ax = int(w * 0.22)
    titik = ((0.17, CORAL, "400 JUTA TH", "ikan ini muncul"),
             (0.50, TEAL, "230 JUTA TH", "dinosaurus muncul"),
             (0.81, NAVY, "66 JUTA TH", "hilang dari catatan fosil"))
    for i, (f, warna, judul, ket) in enumerate(titik):
        yy = int(h * f)
        p = _t(t, 0.20 + i * 0.26, 0.5)
        if p <= 0:
            continue
        blit(lap, raster(46, 46, lambda q, c=warna: q.circ(23, 23, 13, fill=c), ss=3),
             ax - 23, yy - 23, p)
        blit(lap, raster(46, 46, lambda q, c=warna: q.circ(23, 23, 20, outline=c, width=2),
                         ss=3), ax - 23, yy - 23, 0.35 * p)
        s1 = K.teks(judul, warna, 38, F_BOLD, 0.3)
        blit(lap, s1, ax + 62, yy - 40, p)
        s2 = K.teks(ket, (86, 99, 111), 30, F_MED, 0.2)
        blit(lap, s2, ax + 62, yy + 6, p * 0.95)
    # ikan berskala: satu ikan per tonggak, ukurannya naik (bukan bertumpuk)
    for f, skala, al in ((0.20, 0.26, 0.50), (0.53, 0.32, 0.70), (0.80, 0.38, 1.0)):
        p = _t(t, 0.42, 0.7)
        ik = R.ikan_real(int(w * skala), int(w * skala * 0.42))
        blit(lap, ik, int(w * 0.585), int(h * f) - ik.shape[0] // 2, p * al)
    # jarak 170 juta tahun (kurung + label)
    p = _t(t, 0.75, 0.5)
    if p > 0:
        y1, y2 = int(h * 0.17) + 26, int(h * 0.50) - 26
        blit(lap, raster(14, y2 - y1, lambda q: q.rrect(0, 0, 14, y2 - y1, 7,
                                                        fill=(204, 78, 56)), ss=2),
             int(w * 0.075), y1, p)
        s = K.teks("170 juta tahun", (204, 78, 56), 30, F_BOLD, 0.3)
        blit(lap, s, int(w * 0.075) + 24, (y1 + y2) // 2 - s.shape[0] // 2, p)


# =============================================================== 3. TEMUAN 1938
def temuan(k, box, t, d=15.0):
    """FAKTA 2: dermaga pagi 1938 — perahu, jaring, ikan di atas geladak."""
    x, y, w, h = box
    _kartu(k, box)
    _potong_ke_kartu(k, box, lambda lap: _temuan_isi(lap, w, h, t))


def _temuan_isi(lap, w, h, t):
    """Adegan 1938: dermaga, perahu di garis ufuk, ikan tergeletak di geladak.

    Versi sebelumnya menaruh ikan DI ATAS laut dan perahu menempel di ufuk —
    keduanya terbaca melayang. Sekarang ruang dibagi tiga bidang yang jelas:
    langit (0-0,40), laut (0,40-0,68), geladak dermaga (0,68-1,0). Ikan ada di
    geladak (bidang terdekat), perahu di laut (bidang tengah), matahari di
    langit (bidang jauh). Itu yang membuat adegan terbaca sebagai ruang, bukan
    tempelan.
    """
    def dasar(l, w2, h2):
        # langit pagi
        yy = np.linspace(0, 1, int(h2 * 0.42), dtype=np.float32)[:, None, None]
        l[:int(h2 * 0.42)] = np.clip(
            np.array((252, 228, 200), np.float32) * (1 - yy) +
            np.array((206, 220, 228), np.float32) * yy, 0, 255).astype(np.uint8)
        # laut
        yl = np.linspace(0, 1, h2 - int(h2 * 0.42), dtype=np.float32)[:, None, None]
        l[int(h2 * 0.42):] = np.clip(
            np.array((104, 148, 162), np.float32) * (1 - yl * 0.55) +
            np.array((22, 52, 72), np.float32) * (yl * 0.55), 0, 255).astype(np.uint8)
        # matahari rendah + jalur pantul di air
        blit(l, raster(210, 210, lambda q: q.circ(105, 105, 68,
                                                  fill=(255, 240, 214, 215)), ss=3),
             int(w2 * 0.62), int(h2 * 0.06))
        for i2 in range(10):
            fw = int(w2 * (0.10 + 0.03 * i2))
            blit(l, raster(fw, 5, lambda q, ww=fw: q.rrect(0, 0, ww, 5, 2,
                                                           fill=(255, 236, 204, 60)), ss=2),
                 int(w2 * 0.735) - fw // 2, int(h2 * (0.44 + 0.028 * i2)), 0.8)
        # geladak dermaga (bidang terdekat): papan kayu dengan perspektif
        def geladak(q):
            q.poly([(0, h2 * 0.665), (w2, h2 * 0.705), (w2, h2), (0, h2)],
                   fill=(128, 104, 84))
            for i2 in range(9):
                fy = 0.70 + i2 * 0.036
                q.line([(0, h2 * fy), (w2, h2 * (fy + 0.012))],
                       (104, 84, 68, 150), 2.0)
            q.poly([(0, h2 * 0.665), (w2, h2 * 0.705), (w2, h2 * 0.725), (0, h2 * 0.685)],
                   fill=(96, 76, 60))
        blit(l, raster(w2, h2, geladak, ss=2), 0, 0)
    lap[:] = _latar("temuan_dasar2", w, h, dasar)

    # riak laut bergerak
    for i2 in range(7):
        f = i2 / 7
        ww = int(w * (0.18 + 0.42 * f))
        blit(lap, raster(ww, 4, lambda q, w2=ww: q.rrect(0, 0, w2, 4, 2,
                                                         fill=(230, 244, 248, 80)), ss=2),
             int(w * 0.06) + int(11 * math.sin(t * 0.7 + i2)),
             int(h * (0.45 + 0.030 * i2)), 0.85)

    # perahu di garis ufuk (kecil = jauh), mengangguk
    bw, bh = int(w * 0.30), int(h * 0.16)
    def kapal(q):
        q.poly([(0, bh * 0.62), (bw * 0.10, bh * 0.44), (bw * 0.92, bh * 0.44),
                (bw * 0.84, bh * 0.86), (bw * 0.14, bh * 0.86)], fill=(48, 62, 74))
        q.poly([(0, bh * 0.62), (bw * 0.10, bh * 0.44), (bw * 0.92, bh * 0.44),
                (bw * 0.92, bh * 0.52), (0, bh * 0.70)], fill=(72, 92, 106))
        q.rect(bw * 0.28, bh * 0.16, bw * 0.58, bh * 0.46, fill=(60, 78, 92))
        q.rect(bw * 0.32, bh * 0.22, bw * 0.44, bh * 0.32, fill=(126, 150, 164))
        q.rect(bw * 0.40, 0, bw * 0.44, bh * 0.18, fill=(40, 54, 66))
    from PIL import Image as _Im
    bp = raster(bw, bh, kapal, ss=2)
    bp = np.array(_Im.fromarray(bp, "RGBA").rotate(1.2 * math.sin(t * 0.8),
                                                   resample=_Im.BICUBIC, expand=True))
    blit(lap, bp, int(w * 0.64), int(h * 0.33))

    # ikan TERGELETAK di geladak (bidang terdekat) + bayangan kontak
    ik = R.ikan_real(int(w * 0.62), int(w * 0.62 * 0.44))
    ix, iy = int(w * 0.14), int(h * 0.70)
    blit(lap, R.bayang_kontak(int(ik.shape[1] * 0.92), int(ik.shape[0] * 0.30), 0.55),
         ix + int(ik.shape[1] * 0.05), iy + int(ik.shape[0] * 0.72), 0.95)
    ik2 = np.array(_Im.fromarray(ik, "RGBA").rotate(-3.5 + 1.2 * math.sin(t * 0.6),
                                                  resample=_Im.BICUBIC, expand=True))
    blit(lap, ik2, ix, iy)

    # pelat label: tanggal (kiri atas), ukuran (dekat ikan)
    s = K.pil("22 DESEMBER 1938 · EAST LONDON", (33, 40, 48), (252, 249, 242), 25, 18, 9)
    blit(lap, s, int(w * 0.045), int(h * 0.04), 0.96)
    s2 = K.pil("1,5 METER", (204, 78, 56), (255, 252, 246), 26, 17, 8)
    # diletakkan tepat di atas punggung ikan (geladak, bukan di laut): pelat
    # yang mengapung di tengah laut terbaca sebagai label nyasar.
    pil_x, pil_y = int(w * 0.56), int(h * 0.628)
    blit(lap, s2, pil_x, pil_y, 0.96 * _t(t, 0.42, 0.45))
    # garis ukur dari pelat ke ikan
    p = _t(t, 0.55, 0.45)
    if p > 0:
        _penunjuk(lap, pil_x + s2.shape[1] // 2, pil_y + s2.shape[0],
                  ix + int(ik.shape[1] * 0.58), iy + int(ik.shape[0] * 0.34), 0.85 * p)


# =============================================================== 4. NAMA
def nama(k, box, t, d=17.0):
    """FAKTA 3: etimologi — pelat KOILOS & AKANTHA dihubungkan ke tubuh ikan."""
    x, y, w, h = box
    _kartu(k, box)
    _potong_ke_kartu(k, box, lambda lap: _nama_isi(lap, w, h, t))


def _nama_isi(lap, w, h, t):
    lap[:] = (250, 247, 241)
    ik = R.ikan_real(int(w * 0.86), int(w * 0.86 * 0.44))
    ix, iy = int(w * 0.07), int(h * 0.36)
    blit(lap, ik, ix, iy, _t(t, 0.10, 0.6))
    # pelat kata
    p1 = _t(t, 0.30, 0.45)
    if p1 > 0:
        spr = K.pil("KOILOS = RONGGA", (32, 129, 116), (255, 252, 246), 30, 22, 11)
        blit(lap, spr, int(w * 0.05), int(h * 0.06), p1)
        # garis penunjuk dari pelat ke rongga (di dalam badan ikan)
        _penunjuk(lap, int(w * 0.05) + spr.shape[1] // 2, int(h * 0.06) + spr.shape[0],
                  ix + int(ik.shape[1] * 0.46), iy + int(ik.shape[0] * 0.44), 0.55 * p1)
    p2 = _t(t, 0.52, 0.45)
    if p2 > 0:
        spr = K.pil("AKANTHA = DURI", (204, 78, 56), (255, 252, 246), 30, 22, 11)
        blit(lap, spr, int(w * 0.52), int(h * 0.06), p2)
        _penunjuk(lap, int(w * 0.52) + spr.shape[1] // 2, int(h * 0.06) + spr.shape[0],
                  ix + int(ik.shape[1] * 0.40), iy + int(ik.shape[0] * 0.10), 0.55 * p2)
    # nama ilmiah
    p3 = _t(t, 0.70, 0.5)
    s = K.teks("Latimeria chalumnae", (26, 40, 55), 40, F_SEMI, 0.4)
    blit(lap, s, int(w * 0.05), int(h * 0.86), p3)
    s2 = K.teks("Smith, 1939", (128, 139, 149), 28, F_MED, 0.4)
    blit(lap, s2, int(w * 0.05) + s.shape[1] + 18, int(h * 0.86) + 12, p3)


def _penunjuk(lap, x0, y0, x1, y1, al=0.6):
    """Garis penunjuk tipis (annotation leader) dengan titik di ujung."""
    n = max(6, int(math.dist((x0, y0), (x1, y1)) / 6))
    for i in range(n):
        f = i / n
        if i % 3 == 0:
            x = int(x0 + (x1 - x0) * f)
            y = int(y0 + (y1 - y0) * f)
            blit(lap, raster(5, 5, lambda q: q.circ(2.5, 2.5, 2, fill=(90, 102, 114, 220)),
                             ss=2), x, y, al)
    blit(lap, raster(14, 14, lambda q: q.circ(7, 7, 5, fill=(90, 102, 114, 240)), ss=2),
         x1 - 7, y1 - 7, al)


# =============================================================== 5. PETA
def peta(k, box, t, d=13.0):
    """FAKTA 4: peta Samudra Hindia -> Manado, rute bergerak."""
    x, y, w, h = box
    _kartu(k, box)
    _potong_ke_kartu(k, box, lambda lap: _peta_isi(lap, w, h, t))


def _peta_isi(lap, w, h, t):
    def dasar(l, w2, h2):
        yy = np.linspace(0, 1, h2, dtype=np.float32)[:, None, None]
        laut = (np.array((154, 198, 216), np.float32)[None, None, :] * (1 - yy * 0.72) +
                np.array((26, 78, 108), np.float32)[None, None, :] * (yy * 0.72))
        l[:] = np.clip(laut, 0, 255).astype(np.uint8)
        # grid samar (tanpa mengganggu rute)
        for i2 in range(1, 6):
            blit(l, raster(w2, 2, lambda q, ww=w2: q.rect(0, 0, ww, 2,
                                                          fill=(236, 246, 250, 46)), ss=1),
                 0, int(h2 * i2 / 6), 0.9)
            blit(l, raster(2, h2, lambda q, hh=h2: q.rect(0, 0, 2, hh,
                                                          fill=(236, 246, 250, 46)), ss=1),
                 int(w2 * i2 / 6), 0, 0.9)

        # ---- Afrika Timur (pantai berlekuk, bukan kotak)
        def afrika(q):
            q.poly(_halus([(0, 0), (w2 * 0.34, 0), (w2 * 0.30, h2 * 0.10),
                           (w2 * 0.24, h2 * 0.20), (w2 * 0.27, h2 * 0.30),
                           (w2 * 0.21, h2 * 0.40), (w2 * 0.23, h2 * 0.52),
                           (w2 * 0.17, h2 * 0.62), (w2 * 0.20, h2 * 0.74),
                           (w2 * 0.13, h2 * 0.86), (w2 * 0.16, h2 * 1.0), (0, h2)], n=5),
                   fill=(146, 158, 112))
        blit(l, raster(w2, h2, afrika, ss=2), 0, 0)
        # garis pantai (tepi lebih terang) + daratan lebih gelap di barat
        def pantai(q):
            q.line(_halus([(w2 * 0.34, 0), (w2 * 0.30, h2 * 0.10), (w2 * 0.24, h2 * 0.20),
                           (w2 * 0.27, h2 * 0.30), (w2 * 0.21, h2 * 0.40),
                           (w2 * 0.23, h2 * 0.52), (w2 * 0.17, h2 * 0.62),
                           (w2 * 0.20, h2 * 0.74), (w2 * 0.13, h2 * 0.86),
                           (w2 * 0.16, h2 * 1.0)], n=5), (232, 226, 190, 190), 3.0)
        blit(l, raster(w2, h2, pantai, ss=2), 0, 0)

        # ---- Indonesia: Sumatra, Jawa, Kalimantan, Sulawesi (bentuk kasar benar)
        def nusantara(q):
            # Sumatra (memanjang barat-laut -> tenggara)
            q.poly(_halus([(w2 * 0.62, h2 * 0.10), (w2 * 0.68, h2 * 0.16),
                           (w2 * 0.66, h2 * 0.26), (w2 * 0.72, h2 * 0.34),
                           (w2 * 0.69, h2 * 0.40), (w2 * 0.63, h2 * 0.32),
                           (w2 * 0.60, h2 * 0.20)], n=5), fill=(150, 162, 116))
            # Jawa (memanjang mendatar)
            q.poly(_halus([(w2 * 0.70, h2 * 0.42), (w2 * 0.80, h2 * 0.40),
                           (w2 * 0.88, h2 * 0.43), (w2 * 0.86, h2 * 0.47),
                           (w2 * 0.76, h2 * 0.46)], n=5), fill=(150, 162, 116))
            # Kalimantan (bulat besar)
            q.poly(_halus([(w2 * 0.74, h2 * 0.22), (w2 * 0.84, h2 * 0.18),
                           (w2 * 0.90, h2 * 0.24), (w2 * 0.88, h2 * 0.34),
                           (w2 * 0.79, h2 * 0.36), (w2 * 0.73, h2 * 0.30)], n=6),
                   fill=(150, 162, 116))
            # Sulawesi (bentuk K khas)
            q.poly(_halus([(w2 * 0.90, h2 * 0.30), (w2 * 0.95, h2 * 0.24),
                           (w2 * 0.98, h2 * 0.30), (w2 * 0.94, h2 * 0.38),
                           (w2 * 0.99, h2 * 0.44), (w2 * 0.96, h2 * 0.48),
                           (w2 * 0.90, h2 * 0.42)], n=5), fill=(150, 162, 116))
            # Halmahera & Papua (potongan tepi kanan)
            q.ell(w2 * 0.965, h2 * 0.55, w2 * 1.02, h2 * 0.62, fill=(150, 162, 116))
            q.poly([(w2 * 0.995, h2 * 0.62), (w2 * 1.02, h2 * 0.60),
                    (w2 * 1.02, h2 * 0.80), (w2 * 0.99, h2 * 0.78)], fill=(150, 162, 116))
        blit(l, raster(w2, h2, nusantara, ss=2), 0, 0)
    lap[:] = _latar("peta_dasar", w, h, dasar)
    # rute Komoro -> Manado (progresif, dengan ujung menyala)
    a = (w * 0.205, h * 0.55)
    b = (w * 0.896, h * 0.355)
    p = _t(t, 0.22, 1.2)
    _kurva_putus(lap, a, b, p, (232, 96, 72), 0.95)
    # denyar di ujung rute selama berjalan
    if 0.02 < p < 0.995:
        f = p
        px = (1 - f) ** 2 * a[0] + 2 * (1 - f) * f * ((a[0] + b[0]) / 2) + f ** 2 * b[0]
        py = (1 - f) ** 2 * a[1] + 2 * (1 - f) * f * (min(a[1], b[1]) - 90) + f ** 2 * b[1]
        blit(lap, raster(30, 30, lambda q: q.circ(15, 15, 8, fill=(255, 214, 190, 235)), ss=3),
             int(px) - 15, int(py) - 15, 0.9)
    # pin + pelat
    for (px, py), lab, warna, t0 in ((a, "KOMORO · 1938", (33, 40, 48), 0.10),
                                     (b, "MANADO · 1997", (204, 78, 56), 0.85)):
        al = _t(t, t0, 0.4)
        s = K.pil(lab, warna, (255, 252, 246), 25, 18, 9)
        lx = max(6, min(w - s.shape[1] - 6, int(px - s.shape[1] * 0.5)))
        ly = int(py - s.shape[0] - 24)
        blit(lap, s, lx, max(6, ly), al)
        blit(lap, raster(22, 22, lambda q: q.circ(11, 11, 6, fill=(255, 252, 246)), ss=2),
             int(px) - 11, int(py) - 11, al)
    s = K.pil("8.000 KM", (33, 40, 48), (252, 249, 242), 24, 16, 8)
    blit(lap, s, int(w * 0.44), int(h * 0.30), 0.9 * p)
    # ikan kecil dekat Manado
    ik = R.ikan_real(int(w * 0.22), int(w * 0.22 * 0.44))
    blit(lap, ik[:, ::-1], int(w * 0.74 + 7 * math.sin(t * 0.6)), int(h * 0.52), 0.95)


def _kurva_putus(lap, a, b, p, warna, al=0.5):
    """Garis putus-putus melengkung (rute). Progresif mengikuti `p`."""
    if p <= 0:
        return
    cx = (a[0] + b[0]) / 2
    cy = min(a[1], b[1]) - 90
    n = 60
    for i in range(int(n * p)):
        f0, f1 = i / n, (i + 1) / n
        if i % 3:
            continue
        x0 = (1 - f0) ** 2 * a[0] + 2 * (1 - f0) * f0 * cx + f0 ** 2 * b[0]
        y0 = (1 - f0) ** 2 * a[1] + 2 * (1 - f0) * f0 * cy + f0 ** 2 * b[1]
        x1 = (1 - f1) ** 2 * a[0] + 2 * (1 - f1) * f1 * cx + f1 ** 2 * b[0]
        y1 = (1 - f1) ** 2 * a[1] + 2 * (1 - f1) * f1 * cy + f1 ** 2 * b[1]
        xx, yy = int(min(x0, x1)), int(min(y0, y1))
        ww = max(4, int(abs(x1 - x0)) + 8)
        hh = max(4, int(abs(y1 - y0)) + 8)
        spr = raster(ww, hh, lambda q: q.line([(x0 - xx + 3, y0 - yy + 3),
                                               (x1 - xx + 3, y1 - yy + 3)],
                                              warna + (int(255 * al),), 3.4), ss=3)
        blit(lap, spr, xx - 3, yy - 3)


# =============================================================== 6. SIRIP
def sirip(k, box, t, d=11.0):
    """FAKTA 5: sirip berdaging vs bersirip-jari + pembanding manusia."""
    x, y, w, h = box
    _kartu(k, box)
    _potong_ke_kartu(k, box, lambda lap: _sirip_isi(lap, w, h, t))


def _sirip_isi(lap, w, h, t):
    lap[:] = (250, 247, 241)
    p = _t(t, 0.15, 0.6)
    lob = R.sirip_real(int(w * 0.30), int(h * 0.42), "lobed")
    ray = R.sirip_real(int(w * 0.30), int(h * 0.42), "ray")
    blit(lap, lob, int(w * 0.07), int(h * 0.10), p)
    blit(lap, ray, int(w * 0.41), int(h * 0.10), p)
    # panah di antara keduanya
    blit(lap, K.panah(120, 66, (204, 78, 56), "kanan"), int(w * 0.335), int(h * 0.28), p)
    s1 = K.pil("SIRIP BERDAGING", (32, 129, 116), (255, 252, 246), 28, 20, 10)
    blit(lap, s1, int(w * 0.06), int(h * 0.58), p)
    s2 = K.pil("BERSIRIP-JARI", (33, 40, 48), (252, 249, 242), 28, 20, 10)
    blit(lap, s2, int(w * 0.38), int(h * 0.58), p)
    # pembanding manusia + ikan (kiri bawah)
    p2 = _t(t, 0.52, 0.6)
    ik = R.ikan_real(int(w * 0.34), int(w * 0.34 * 0.44))
    blit(lap, ik, int(w * 0.06), int(h * 0.72), p2)
    man = K.manusia(int(h * 0.24), (120, 132, 142))
    blit(lap, man, int(w * 0.80), int(h * 0.70), p2)
    s3 = K.teks("tetrapoda ±375 juta tahun", (76, 90, 103), 26, F_MED, 0.3)
    blit(lap, s3, int(w * 0.60), int(h * 0.94), p2)


# =============================================================== 7. MITOS
def mitos(k, box, t, d=14.0):
    """FAKTA 6: 'fosil hidup' keliru + genom & masa kehamilan."""
    x, y, w, h = box
    _kartu(k, box)
    _potong_ke_kartu(k, box, lambda lap: _mitos_isi(lap, w, h, t))


def _mitos_isi(lap, w, h, t):
    lap[:] = (250, 247, 241)
    s = K.teks("FOSIL HIDUP", (26, 40, 55), 62, F_BOLD, -0.6)
    px, py = int(w * 0.06), int(h * 0.06)
    blit(lap, s, px, py, _t(t, 0.10, 0.5))
    p = _t(t, 0.45, 0.5)
    if p > 0:
        K.coret(lap, px - 6, py + int(s.shape[0] * 0.52), s.shape[1] + 12,
                (204, 78, 56), 6.0, p)
    s2 = K.teks("= SALAH KAPRAH", (204, 78, 56), 40, F_BOLD, 0.2)
    blit(lap, s2, px, py + s.shape[0] + 6, p)
    # dua batang ukur: genom coelacanth vs manusia (2,86 vs 3,1 Gb)
    p3 = _t(t, 0.62, 0.7)
    dasar_y = int(h * 0.52)
    for i, (lab, nilai, warna, maks) in enumerate((("COELACANTH", 2.86, (32, 129, 116), 3.2),
                                                   ("MANUSIA", 3.10, (76, 90, 103), 3.2))):
        yy = dasar_y + i * int(h * 0.15)
        bl = K.teks(lab, (76, 90, 103), 26, F_BOLD, 0.4)
        blit(lap, bl, int(w * 0.06), yy - 34, p3)
        panjang = int((w * 0.62) * (nilai / maks) * p3)
        blit(lap, raster(max(4, panjang), 26, lambda q: q.rrect(0, 0, panjang, 26, 13,
                                                                fill=warna), ss=2),
             int(w * 0.06), yy, p3)
        nl = K.teks(f"{nilai:.2f}".replace(".", ",") + " miliar huruf", (26, 40, 55),
                    28, F_SEMI, 0.2)
        blit(lap, nl, int(w * 0.06) + max(4, panjang) + 14, yy - 2, p3)
    # masa kehamilan: tiga lingkaran bertingkat (bulan -> tahun), bukan cincin kosong
    p4 = _t(t, 0.78, 0.7)
    if p4 > 0:
        cx, cy = int(w * 0.80), int(h * 0.28)
        for i2, (rr, warna2, al) in enumerate((
                (int(min(w, h) * 0.115), (204, 78, 56), 1.0),
                (int(min(w, h) * 0.082), (222, 160, 34), 0.9),
                (int(min(w, h) * 0.050), (32, 129, 116), 0.85))):
            pp = _t(t, 0.78 + i2 * 0.10, 0.45)
            blit(lap, raster(rr * 2 + 8, rr * 2 + 8,
                             lambda q, r2=rr, c=warna2: q.circ(r2 + 4, r2 + 4, r2,
                                                               outline=c + (220,),
                                                               width=6), ss=2),
                 cx - rr - 4, cy - rr - 4, pp * al)
        n = K.teks("±3", (26, 40, 55), 54, F_BOLD, -1.0)
        blit(lap, n, cx - n.shape[1] // 2, cy - n.shape[0] // 2, p4)
        ket = K.teks("tahun", (76, 90, 103), 24, F_MED, 0.4)
        blit(lap, ket, cx - ket.shape[1] // 2, cy + n.shape[0] // 2 - 12, p4)


# =============================================================== 8. ANCAMAN
def ancaman(k, box, t, d=12.0):
    """FAKTA 7: populasi menurun + status kritis."""
    x, y, w, h = box
    _kartu(k, box)
    _potong_ke_kartu(k, box, lambda lap: _ancaman_isi(lap, w, h, t))


def _ancaman_isi(lap, w, h, t):
    lap[:] = (250, 247, 241)
    # --- zona kiri: grafik batang menurun (populasi 1980 -> kini)
    nilai = (1.00, 0.72, 0.46, 0.26)
    label = ("1980", "1995", "2005", "kini")
    # dasar 0,58h menyisakan separuh kartu kosong di bawah grafik. Batang
    # dibuat setinggi 0,62h dengan dasar 0,80h supaya komposisi seimbang.
    dasar = int(h * 0.80)
    grafik_w = w * 0.52
    for i2, (n, lab) in enumerate(zip(nilai, label)):
        p = _t(t, 0.16 + i2 * 0.12, 0.5)
        bh = int(h * 0.62 * n * p)
        bx = int(w * 0.06 + i2 * (grafik_w / 4.4))
        bw2 = int(grafik_w / 5.4)
        warna = (204, 78, 56) if i2 < 3 else (150, 44, 32)
        blit(lap, raster(bw2, max(4, bh),
                         lambda q, ww=bw2, hh=max(4, bh), c=warna:
                         q.rrect(0, 0, ww, hh, 9, fill=c), ss=2),
             bx, dasar - bh, p)
        s = K.teks(lab, (76, 90, 103), 24, F_SEMI, 0.3)
        blit(lap, s, bx + (bw2 - s.shape[1]) // 2, dasar + 12, p)
    blit(lap, raster(int(grafik_w + w * 0.06), 3,
                     lambda q, ww=int(grafik_w + w * 0.06): q.rect(0, 0, ww, 3,
                                                                   fill=(206, 198, 186)), ss=1),
         int(w * 0.045), dasar, 1.0)
    # --- zona kanan: pelat status + inset jaring (tidak menabrak grafik)
    p = _t(t, 0.62, 0.5)
    s = K.pil("KRITIS", (150, 44, 32), (255, 250, 244), 28, 20, 10)
    blit(lap, s, int(w * 0.62), int(h * 0.06), p)
    s2 = K.teks("critically endangered", (76, 90, 103), 22, F_MED, 0.2)
    blit(lap, s2, int(w * 0.62), int(h * 0.06) + s.shape[0] + 4, p)
    s3 = K.teks("IUCN Red List", (128, 139, 149), 22, F_MED, 0.2)
    blit(lap, s3, int(w * 0.62), int(h * 0.06) + s.shape[0] + 30, p)
    pj = _t(t, 0.74, 0.6)
    if pj > 0:
        ix, iy = int(w * 0.62), int(h * 0.26)
        iw, ih = int(w * 0.32), int(h * 0.26)
        blit(lap, raster(iw, ih, lambda q: q.rrect(0, 0, iw, ih, 14,
                                                   fill=(233, 238, 236)), ss=2),
             ix, iy, pj)
        ik = R.ikan_real(int(iw * 0.84), int(iw * 0.84 * 0.44))
        blit(lap, ik[:, ::-1], ix + int(iw * 0.08), iy + int(ih * 0.24), pj)
        for i2 in range(8):
            f = i2 / 7
            blit(lap, raster(int(iw * 0.86), 2,
                             lambda q, ww=int(iw * 0.86): q.rect(0, 0, ww, 2,
                                                                 fill=(104, 116, 126, 120)),
                             ss=1), ix + int(iw * 0.07), iy + int(ih * (0.20 + 0.60 * f)), pj)
        for i2 in range(6):
            f = i2 / 5
            blit(lap, raster(2, int(ih * 0.66),
                             lambda q, hh=int(ih * 0.66): q.rect(0, 0, 2, hh,
                                                                 fill=(104, 116, 126, 120)),
                             ss=1), ix + int(iw * (0.16 + 0.66 * f)), iy + int(ih * 0.16), pj)
        lab = K.pil("TERJARING", (33, 40, 48), (252, 249, 242), 20, 12, 6)
        blit(lap, lab, ix + int(iw * 0.04), iy + int(ih * 0.03), pj)


# =============================================================== pintu masuk
_FN = {"laut": laut, "umur": umur, "temuan": temuan, "nama": nama, "peta": peta,
       "sirip": sirip, "mitos": mitos, "ancaman": ancaman}


def gambar(nama: str, k, box, t: float, d: float = 10.0):
    fn = _FN.get(nama)
    if fn is None:
        raise KeyError(f"panggung '{nama}' tidak ada (pilihan: {sorted(_FN)})")
    fn(k, box, t, d)
