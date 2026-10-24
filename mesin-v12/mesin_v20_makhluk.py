#!/usr/bin/env python3
"""mesin_v20_makhluk.py — OBJEK & FIGUR untuk KlikTahu V20.

Semua yang bergerak di layar digambar di sini sebagai sprite RGBA, lalu
ditempel oleh modul episode. Aturan yang dipakai semua fungsi:

  1. **Cahaya lebih penting daripada detail.** Siluet gelap di latar gelap hanya
     terbaca kalau ada rim light (tepi yang menghadap sumber cahaya) — jadi
     setiap figur mendapat `_rim` dari arah lampu yang sama (kiri atas).
  2. **Gradasi hanya pada mask badan.** Kalau gradasi diterapkan ke seluruh
     sprite, lengan/ekor melebur dan bentuknya hilang (pelajaran v19).
  3. **Detail (mata, kabel, lipatan) diklip ke mask badan.**
  4. **Semua koordinat dalam piksel sprite**, bukan kanvas. Penelepon yang
     mengatur posisi & skala.

Selftest: python3 mesin_v20_makhluk.py
"""
from __future__ import annotations

import functools
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw

import mesin_v18_inti as M
from mesin_v18_inti import (F_BOLD, F_MED, F_SEMI, Pena, blit, catmull, clamp,
                            gblur, lerp, mask, mask_poli, mix, pangkas, raster,
                            rng, spr_text, tw)
from mesin_v20_cahaya import (CYAN, CYAN_L, GOLD, GOLD_L, PUTIH, TEKS, CORAL,
                              premul)

W_, H_ = 1080, 1920


# ============================================================== util
def rim(mask_arr, arah=(-1, -1), radius=3.2, kekuatan=0.9, warna=CYAN_L, pita=None):
    """Cincin cahaya pada tepi siluet yang menghadap sumber cahaya."""
    m = (mask_arr > 60).astype(np.float32)
    gx = cv2.Sobel(m, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(m, cv2.CV_32F, 0, 1, ksize=3)
    dx, dy = arah
    hadap = np.clip(-(gx * dx + gy * dy), 0, None)
    hadap = np.clip(hadap / (hadap.max() + 1e-6), 0, 1)
    r = gblur((hadap * m * 255).astype(np.uint8), radius)
    r = (r.astype(np.float32) * kekuatan).astype(np.uint8)
    out = np.zeros((mask_arr.shape[0], mask_arr.shape[1], 4), np.uint8)
    out[..., :3] = tuple(int(v) for v in warna[:3])
    out[..., 3] = r
    if pita:
        out[..., 3] = np.maximum(out[..., 3], (m * pita).astype(np.uint8))
    return out


def isi_mask(spr, mask_arr, warna_fn=None):
    """Warnai seluruh siluet dengan gradasi vertikal (mask badan saja)."""
    h = spr.shape[0]
    ys = np.arange(h, dtype=np.float32)[:, None] / max(1, h - 1)
    rgb = np.empty((h, spr.shape[1], 3), np.float32)
    for c in range(3):
        rgb[..., c] = warna_fn(ys, c)
    spr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    spr[..., 3] = mask_arr
    return spr


def _poli(pts, n=10):
    return catmull(pts, n=n, closed=True)


# ============================================================== 1. TEMPAT TIDUR

@functools.lru_cache(maxsize=4)
def kasur(w=1080, tinggi=430, kayu=(38, 32, 42), kain=(52, 62, 94),
          seprai=(34, 42, 68), bantal=(62, 74, 110)):
    """Tempat tidur tampak samping: kepala kasur, rangka, kasur tebal, bantal.

    Proporsi yang dipakai (dari uji pratinjau): tinggi total 430 px untuk lebar
    1080, kasur 42% tinggi (180 px) supaya terbaca sebagai kasur, bukan meja.
    """
    W2, H2 = int(w), int(tinggi)
    spr = np.zeros((H2, W2, 4), np.uint8)

    def g(p):
        # kaki
        p.rect(W2 * 0.05, H2 * 0.80, W2 * 0.095, H2 * 0.98, fill=mix(kayu, (0, 0, 0), 0.45))
        p.rect(W2 * 0.815, H2 * 0.80, W2 * 0.86, H2 * 0.98, fill=mix(kayu, (0, 0, 0), 0.45))
        # rangka (balok)
        p.rect(W2 * 0.04, H2 * 0.72, W2 * 0.90, H2 * 0.82, fill=kayu)
        # kasur tebal (dengan sudut membulat)
        p.rrect(W2 * 0.03, H2 * 0.44, W2 * 0.90, H2 * 0.74, 30, fill=kain)
        # kepala kasur
        p.rrect(W2 * 0.87, H2 * 0.02, W2 * 0.995, H2 * 0.80, 20, fill=kayu)
        p.rrect(W2 * 0.875, H2 * 0.06, W2 * 0.955, H2 * 0.30, 16, fill=mix(kayu, (80, 74, 96), 0.45))
        # selimut: menutup permukaan kasur sampai menggantung di sisi kiri
        sel = [(0.03, 0.46), (0.20, 0.445), (0.40, 0.455), (0.58, 0.445),
               (0.72, 0.455), (0.74, 0.52), (0.72, 0.70), (0.60, 0.725),
               (0.40, 0.735), (0.20, 0.73), (0.06, 0.715), (0.02, 0.66)]
        p.poly([(x * W2, y * H2) for x, y in _poli(sel, 8)], fill=seprai)
        # lipatan selimut
        for fx in (0.16, 0.31, 0.46, 0.61):
            p.d.line([(fx * W2 * p.k, 0.47 * H2 * p.k), (fx * W2 * p.k, 0.70 * H2 * p.k)],
                     fill=mix(seprai, (0, 0, 0), 0.30), width=max(1, int(3 * p.k)))
        # bantal
        p.rrect(W2 * 0.66, H2 * 0.20, W2 * 0.90, H2 * 0.46, 26, fill=mix(bantal, (0, 0, 0), 0.20))
        p.rrect(W2 * 0.655, H2 * 0.24, W2 * 0.895, H2 * 0.47, 26, fill=bantal)
    blit(spr, raster(W2, H2, g, ss=2), 0, 0)

    m = spr[..., 3]
    ys = np.arange(H2, dtype=np.float32)[:, None] / H2
    xs = np.arange(W2, dtype=np.float32)[None, :] / W2
    caf = np.clip(0.70 + 0.50 * (1.0 - ys) + 0.20 * xs, 0, 1.85)
    gspr = np.zeros_like(spr)
    for c in range(3):
        gspr[..., c] = np.clip(spr[..., c].astype(np.float32) * caf, 0, 255).astype(np.uint8)
    gspr[..., 3] = m
    spr = gspr
    blit(spr, rim(m, (0.35, -1), 3.4, 0.85, (150, 190, 255)), 0, 0)
    return pangkas(spr)


def selimut_bergelombang(w, h, fase, warna=(30, 40, 70), tinggi=1.0):
    """Selimut yang bernapas: gelombang sinus horizontal dipotong ke bentuk."""
    W2, H2 = int(w), int(h)
    xs = np.arange(W2, dtype=np.float32)[None, :]
    ys = np.arange(H2, dtype=np.float32)[:, None]
    atas = H2 * (0.16 + 0.10 * np.sin(xs / W2 * math.pi * 2.1 + fase)
                 + 0.05 * np.sin(xs / W2 * math.pi * 5.3 + fase * 1.7))
    m = np.clip((ys - atas) / 2.0, 0, 1) * (ys < H2 * 0.98)
    alpha = (m * 255).astype(np.uint8)
    spr = np.zeros((H2, W2, 4), np.uint8)
    grad = np.clip(np.array(warna, np.float32)[None, None, :] *
                   (1.0 + 0.5 * (1 - ys / H2))[:, :, None], 0, 255).astype(np.uint8)
    spr[..., :3] = np.broadcast_to(grad, (H2, W2, 3))
    spr[..., 3] = alpha
    blit(spr, rim(alpha, (-0.5, -1), 3.0, 0.75, (140, 180, 240)), 0, 0)
    return pangkas(spr)


# ============================================================== 2. ORANG TIDUR

@functools.lru_cache(maxsize=16)
def orang_tidur(skala=1.0, mata="tutup", warna_kulit=(206, 168, 142),
                warna_rambut=(34, 27, 32), kaos=(38, 50, 80), dewasa=True):
    """Kepala + bahu orang tidur, tampak samping menghadap KIRI.

    Anatomi profil (kunci agar tidak terbaca seperti bebek):
      dahi -> pangkal hidung turun landai -> ujung hidung 10 px -> bibir atas
      masuk -> bibir bawah -> dagu mundur -> leher. Rambut = massa yang
      menutup tengkorak dan tengkuk, BUKAN topi.

    `mata`: "tutup" | "buka" | "kaget".
    """
    S = 2
    w, h = max(80, int(300 * skala)), max(80, int(320 * skala))
    kul = tuple(int(v) for v in warna_kulit)
    rmb = tuple(int(v) for v in warna_rambut)
    def P(pts):
        return [(x / 300.0 * w, y / 320.0 * h) for x, y in pts]

    def g(p):
        # ---- bahu & dada di bawah selimut (kaos)
        p.poly(_poli(P([(120, 268), (150, 232), (200, 222), (262, 232), (292, 262),
                        (298, 320), (104, 320)])), fill=kaos)
        # ---- leher
        p.poly(_poli(P([(196, 196), (232, 200), (238, 238), (200, 240)])),
               fill=mix(kul, (120, 84, 74), 0.30))
        # ---- kepala: tengkorak belakang -> ubun-ubun -> dahi -> hidung -> dagu
        profil = [(206, 214),   # ujung dagu
                  (196, 200),   # bibir bawah turun
                  (192, 192),   # bibir atas
                  (176, 186),   # filtrum
                  (168, 176),   # ujung hidung
                  (160, 168),   # pangkal hidung
                  (150, 150),   # mata
                  (140, 128),   # dahi bawah
                  (136, 106),   # dahi atas
                  (146, 84),    # ubun-ubun depan
                  (172, 66),    # ubun-ubun
                  (208, 62),
                  (244, 74),
                  (266, 96),    # belakang kepala
                  (272, 128),
                  (268, 162),
                  (256, 192),   # tengkuk
                  (236, 206)]
        p.poly(_poli(P(profil), 10), fill=kul)
        # ---- telinga (kecil, di tengah kepala)
        p.ell(w * 0.72, h * 0.40, w * 0.82, h * 0.50, fill=mix(kul, (140, 96, 84), 0.25))
        p.ell(w * 0.745, h * 0.425, w * 0.80, h * 0.475, fill=mix(kul, (90, 60, 56), 0.35))
        # ---- rambut: menutup tengkorak, turun ke tengkuk, dengan poni
        rambut = [(138, 108), (132, 92), (144, 74), (170, 60), (208, 54), (246, 66),
                  (270, 88), (278, 116), (276, 150), (268, 182), (258, 196),
                  (250, 168), (252, 132), (244, 104), (222, 84), (186, 80),
                  (156, 88), (146, 104)]
        p.poly(_poli(P(rambut), 9), fill=rmb)
    spr = raster(w, h, g, ss=S)

    # ---- shading lembut (cahaya dari kanan atas) + rim
    lap = np.zeros_like(spr)
    ys = np.arange(h, dtype=np.float32)[:, None] / h
    xs = np.arange(w, dtype=np.float32)[None, :] / w
    caf = np.clip(1.0 + 0.16 * xs - 0.20 * ys, 0.6, 1.4)
    for c in range(3):
        lap[..., c] = np.clip(spr[..., c].astype(np.float32) * caf, 0, 255).astype(np.uint8)
    lap[..., 3] = spr[..., 3]
    spr = lap
    blit(spr, rim(spr[..., 3], (0.5, -1), 3.0, 0.95, (215, 236, 255)), 0, 0)
    blit(spr, rim(spr[..., 3], (-1, 0.2), 2.6, 0.30, (110, 150, 215)), 0, 0)

    # ---- mata
    ex, ey = 0.545 * w, 0.455 * h
    if mata == "tutup":
        lap = np.zeros((h, w, 4), np.uint8)
        # kelopak menutup: busur cembung ke bawah + bulu mata
        cv2.ellipse(lap, (int(ex), int(ey - 8 * skala)),
                    (int(19 * skala), int(13 * skala)), 0, 20, 160,
                    (38, 26, 26, 245), max(2, int(4 * skala)), cv2.LINE_AA)
        for i in range(4):
            fx = ex + (i - 1.5) * 8 * skala
            cv2.line(lap, (int(fx), int(ey + 1 * skala)),
                     (int(fx - 4 * skala), int(ey + 7 * skala)),
                     (38, 26, 26, 190), max(1, int(2 * skala)), cv2.LINE_AA)
        blit(spr, lap, 0, 0)
    else:
        r = (16 if mata == "buka" else 20) * skala
        lap = np.zeros((h, w, 4), np.uint8)
        cv2.ellipse(lap, (int(ex), int(ey)), (int(18 * skala), int(r)), -8, 0, 360,
                    (246, 248, 252, 255), -1, cv2.LINE_AA)
        cv2.circle(lap, (int(ex - 4 * skala), int(ey + 2 * skala)), int(r * 0.55),
                   (48, 38, 42, 255), -1, cv2.LINE_AA)
        cv2.circle(lap, (int(ex - 8 * skala), int(ey - 4 * skala)), max(1, int(r * 0.22)),
                   (255, 255, 255, 240), -1, cv2.LINE_AA)
        blit(spr, lap, 0, 0)
        if mata == "kaget":
            al = np.zeros((h, w, 4), np.uint8)
            cv2.line(al, (int(ex - 22 * skala), int(ey - 30 * skala)),
                     (int(ex + 16 * skala), int(ey - 40 * skala)),
                     (rmb[0], rmb[1], rmb[2], 255), max(3, int(6 * skala)), cv2.LINE_AA)
            blit(spr, al, 0, 0)
    return pangkas(spr)


# ============================================================== 3. FIGUR MANUSIA

def _anggota(p, titik, tebal, skala, warna):
    """Gambar satu anggota badan sebagai rangkaian segmen bertaper + sendi bulat.

    Titik = daftar (x, y) di koordinat normalisasi figur. `tebal` = daftar
    radius per titik (piksel sprite). Sendi digambar sebagai lingkaran supaya
    siku/lutut tidak menyudut.
    """
    n = len(titik)
    for i in range(n - 1):
        x0, y0 = titik[i][0] * skala[0], titik[i][1] * skala[1]
        x1, y1 = titik[i + 1][0] * skala[0], titik[i + 1][1] * skala[1]
        w0 = tebal[i] if i < len(tebal) else tebal[-1]
        w1 = tebal[i + 1] if i + 1 < len(tebal) else tebal[-1]
        t = (w0 + w1) / 2.0
        p.d.line([(x0 * p.k, y0 * p.k), (x1 * p.k, y1 * p.k)], fill=warna,
                 width=max(1, int(t * 2 * p.k)))
    for i, (x, y) in enumerate(titik):
        r = tebal[min(i, len(tebal) - 1)]
        p.circ(x * skala[0], y * skala[1], r, fill=warna)


@functools.lru_cache(maxsize=12)
def figur(tinggi=560, pose="berdiri", warna=(58, 72, 104), rim_warna=CYAN_L,
          rim_arah=(-1, -1), rim_kuat=1.0, tebal_badan=0.075):
    """Siluet manusia penuh dengan anggota bertaper, sendi bulat, dan rim light.

    pose:
      "berdiri"  — untuk skala perbandingan
      "jatuh"    — badan diagonal, tangan ke atas, kaki menekuk (dipakai hook)
      "kaget"    — badan tertekuk, tangan menahan di depan
      "tidur"    — berbaring miring (fetal)
    Satuan koordinat: 1.0 = tinggi figur.
    """
    W2 = int(tinggi * 0.72)
    H2 = int(tinggi)
    sk = (W2, H2)
    tb = tebal_badan * H2

    POSES = {
        "berdiri": dict(
            badan=[(0.50, 0.21), (0.50, 0.34), (0.50, 0.50), (0.50, 0.56)],
            tebal_badan=[tb * 1.12, tb * 1.02, tb * 0.94, tb * 0.88],
            lengan_k=[(0.425, 0.23), (0.395, 0.38), (0.375, 0.52)],
            lengan_d=[(0.575, 0.23), (0.605, 0.38), (0.625, 0.52)],
            kaki_k=[(0.462, 0.53), (0.452, 0.74), (0.445, 0.93)],
            kaki_d=[(0.538, 0.53), (0.552, 0.74), (0.560, 0.93)],
            kepala=(0.50, 0.10)),
        "jatuh": dict(
            badan=[(0.45, 0.24), (0.50, 0.36), (0.53, 0.48), (0.54, 0.57)],
            tebal_badan=[tb * 1.12, tb * 1.02, tb * 0.96, tb * 0.88],
            lengan_k=[(0.41, 0.26), (0.28, 0.17), (0.17, 0.06)],
            lengan_d=[(0.52, 0.27), (0.66, 0.19), (0.79, 0.11)],
            kaki_k=[(0.51, 0.57), (0.36, 0.68), (0.24, 0.80)],
            kaki_d=[(0.56, 0.58), (0.66, 0.74), (0.72, 0.90)],
            kepala=(0.43, 0.15)),
        "kaget": dict(
            badan=[(0.53, 0.24), (0.51, 0.37), (0.49, 0.49), (0.48, 0.56)],
            tebal_badan=[tb * 1.12, tb * 1.02, tb * 0.94, tb * 0.88],
            lengan_k=[(0.45, 0.26), (0.30, 0.32), (0.17, 0.30)],
            lengan_d=[(0.58, 0.26), (0.74, 0.32), (0.87, 0.29)],
            kaki_k=[(0.45, 0.55), (0.38, 0.74), (0.34, 0.93)],
            kaki_d=[(0.52, 0.55), (0.62, 0.73), (0.68, 0.92)],
            kepala=(0.55, 0.14)),
        "tidur": dict(
            badan=[(0.58, 0.42), (0.44, 0.46), (0.30, 0.50), (0.22, 0.53)],
            tebal_badan=[tb * 0.90, tb * 1.02, tb * 1.02, tb * 0.92],
            lengan_k=[(0.44, 0.52), (0.34, 0.58), (0.26, 0.60)],
            lengan_d=[(0.46, 0.44), (0.36, 0.40), (0.28, 0.42)],
            kaki_k=[(0.24, 0.54), (0.16, 0.66), (0.08, 0.74)],
            kaki_d=[(0.22, 0.50), (0.12, 0.58), (0.04, 0.62)],
            kepala=(0.62, 0.40)),
    }
    P = POSES.get(pose, POSES["berdiri"])
    r_lengan = [tb * 0.42, tb * 0.34, tb * 0.26]
    r_kaki = [tb * 0.50, tb * 0.40, tb * 0.28]

    def g(p):
        # torso: rantai segmen tebal (bukan poligon tipis) + bahu & pinggul
        _anggota(p, P["badan"], P["tebal_badan"], sk, warna)
        _anggota(p, P["kaki_k"], r_kaki, sk, mix(warna, (0, 0, 0), 0.22))
        _anggota(p, P["kaki_d"], r_kaki, sk, mix(warna, (0, 0, 0), 0.12))
        _anggota(p, P["lengan_k"], r_lengan, sk, mix(warna, (0, 0, 0), 0.18))
        _anggota(p, P["lengan_d"], r_lengan, sk, mix(warna, (0, 0, 0), 0.06))
        # bahu (garis tebal antar ujung lengan) + leher + kepala
        (ax, ay), (bx, by) = P["lengan_k"][0], P["lengan_d"][0]
        p.d.line([(ax * sk[0] * p.k, ay * sk[1] * p.k), (bx * sk[0] * p.k, by * sk[1] * p.k)],
                 fill=warna, width=max(1, int(tb * 1.5 * p.k)))
        kx, ky = P["kepala"]
        p.d.line([(sk[0] * kx * p.k, sk[1] * (ky + 0.055) * p.k),
                  (sk[0] * kx * p.k, sk[1] * (ky + 0.10) * p.k)],
                 fill=warna, width=max(2, int(tb * 1.0 * p.k)))
        rk = 0.082
        p.ell(sk[0] * (kx - rk), sk[1] * (ky - rk * 1.12),
              sk[0] * (kx + rk), sk[1] * (ky + rk * 1.12), fill=warna)
    spr = raster(W2, H2, g, ss=2)
    m = spr[..., 3]
    ys = np.arange(H2, dtype=np.float32)[:, None] / H2
    gspr = np.zeros_like(spr)
    for c in range(3):
        gspr[..., c] = np.clip(warna[c] * (1.30 - ys * 0.55), 0, 255).astype(np.uint8)
    blit(spr, gspr, 0, 0)
    blit(spr, rim(m, rim_arah, 3.2, rim_kuat, rim_warna), 0, 0)
    return pangkas(spr)


# ============================================================== 4. OTAK

@functools.lru_cache(maxsize=8)
def otak(lebar=760, warna=(78, 96, 146), warna2=(52, 66, 104), sorot=None,
         aksen=CYAN, detail=True):
    """Otak tampak samping (menghadap KIRI): lobus frontal, temporal, oksipital,
    serebelum, dan batang otak. `sorot`: "batang" | "korteks" | "vestibular"."""
    W2 = int(lebar)
    H2 = int(lebar * 0.70)
    sk = (W2, H2)

    def g(p):
        # --- serebelum (belakang bawah) dulu, agar tertutup sebagian
        p.ell(0.70 * W2, 0.52 * H2, 0.94 * W2, 0.80 * H2, fill=mix(warna, (0, 0, 0), 0.20))
        # --- batang otak turun dari tengah bawah
        p.poly([(x * W2, y * H2) for x, y in
                _poli([(0.56, 0.56), (0.68, 0.58), (0.70, 0.86), (0.62, 0.92), (0.55, 0.72)], 8)],
               fill=warna2)
        # --- serebrum: frontal (kiri, meruncing) -> vertex -> oksipital -> temporal
        pts = [(0.06, 0.50), (0.05, 0.40), (0.11, 0.31), (0.22, 0.24),
               (0.36, 0.18), (0.52, 0.16), (0.66, 0.18), (0.76, 0.24),
               (0.83, 0.33), (0.85, 0.44), (0.82, 0.53), (0.73, 0.56),
               (0.64, 0.54), (0.60, 0.62), (0.50, 0.66), (0.38, 0.65),
               (0.28, 0.62), (0.18, 0.60), (0.10, 0.57)]
        p.poly([(x * W2, y * H2) for x, y in _poli(pts, 10)], fill=warna)
    spr = raster(W2, H2, g, ss=2)
    m = spr[..., 3]

    if detail:
        lap = np.zeros_like(spr)
        # fisura lateral (memisahkan lobus temporal)
        lat = catmull([(0.14 * W2, 0.52 * H2), (0.34 * W2, 0.56 * H2),
                       (0.52 * W2, 0.55 * H2), (0.66 * W2, 0.50 * H2)], n=10)
        cv2.polylines(lap, [np.array(lat, np.int32)], False, (16, 22, 42, 165), 4, cv2.LINE_AA)
        # sulkus: busur sejajar permukaan korteks
        r = rng(12)
        for i in range(15):
            t0 = r.uniform(0.10, 0.62)
            y0 = r.uniform(0.24, 0.48)
            L = r.uniform(0.10, 0.20)
            ang = r.uniform(-0.35, 0.35)
            pts = []
            for j in range(9):
                tt = j / 8.0
                pts.append(((t0 + tt * L) * W2,
                            (y0 + math.sin(tt * math.pi * 1.1) * 0.055 + tt * ang * 0.10) * H2))
            cv2.polylines(lap, [np.array(pts, np.int32)], False, (20, 26, 48, 140), 4, cv2.LINE_AA)
        lap[..., 3] = (lap[..., 3].astype(np.float32) * (m > 60) * 0.9).astype(np.uint8)
        blit(spr, lap, 0, 0)

    # volume + rim
    gspr = np.zeros_like(spr)
    ys = np.arange(H2, dtype=np.float32)[:, None] / H2
    for c in range(3):
        gspr[..., c] = np.clip(warna[c] * (1.32 - ys * 0.70), 0, 255).astype(np.uint8)
    blit(spr, gspr, 0, 0, 0.9)
    blit(spr, rim(m, (-0.55, -1), 3.2, 0.95, (170, 212, 255)), 0, 0)

    lap = np.zeros_like(spr)
    if sorot in ("batang", None):
        for i in range(10):
            yy = H2 * (0.60 + i * 0.030)
            cv2.circle(lap, (int(W2 * 0.635 + math.sin(i * 0.9) * 3), int(yy)), 3,
                       (*aksen, 215), -1, cv2.LINE_AA)
    if sorot == "korteks":
        for i in range(18):
            t = i / 17.0
            x = W2 * (0.14 + t * 0.62)
            y = H2 * (0.26 + 0.09 * math.sin(t * 6.6))
            cv2.circle(lap, (int(x), int(y)), 4, (*aksen, 225), -1, cv2.LINE_AA)
    if sorot == "vestibular":
        cv2.circle(lap, (int(W2 * 0.80), int(H2 * 0.64)), 7, (*aksen, 240), -1, cv2.LINE_AA)
    blit(spr, lap, 0, 0)
    return pangkas(spr)


# ============================================================== 5. PRIMATA & DAHAN

@functools.lru_cache(maxsize=4)
def primata(tinggi=340, warna=(30, 33, 46), rim_warna=(150, 190, 255)):
    """Primata bergelantungan: dua lengan ke atas, badan, dua kaki, ekor melingkar.

    Anatomi: lengan ~40% tinggi (primata bergelantungan punya lengan panjang),
    badan oval, kepala bulat kecil di bahu, ekor keluar dari belakang.
    """
    W2 = int(tinggi * 0.95)
    H2 = int(tinggi)
    sk = (W2, H2)
    tb = H2 * 0.075

    def g(p):
        # ekor (paling belakang)
        ekor = [(0.52, 0.62), (0.74, 0.56), (0.88, 0.66), (0.86, 0.82), (0.72, 0.88)]
        pts = catmull([(x * W2, y * H2) for x, y in ekor], n=8)
        for i in range(len(pts) - 1):
            rr = max(2, int(H2 * 0.026 * (1 - i / len(pts) * 0.6)))
            p.d.line([(pts[i][0] * p.k, pts[i][1] * p.k),
                      (pts[i + 1][0] * p.k, pts[i + 1][1] * p.k)],
                     fill=warna, width=max(1, int(rr * 2 * p.k)))
        # kaki menggantung
        _anggota(p, [(0.44, 0.62), (0.40, 0.78), (0.34, 0.92)],
                 [tb * 0.5, tb * 0.36, tb * 0.24], sk, warna)
        _anggota(p, [(0.56, 0.62), (0.60, 0.78), (0.65, 0.92)],
                 [tb * 0.5, tb * 0.36, tb * 0.24], sk, mix(warna, (0, 0, 0), 0.15))
        # badan
        p.poly([(x * W2, y * H2) for x, y in
                _poli([(0.50, 0.24), (0.61, 0.33), (0.62, 0.50), (0.56, 0.63),
                       (0.44, 0.63), (0.38, 0.50), (0.39, 0.33)])], fill=warna)
        # lengan panjang ke atas (memegang dahan)
        _anggota(p, [(0.41, 0.30), (0.33, 0.16), (0.30, 0.02)],
                 [tb * 0.46, tb * 0.34, tb * 0.26], sk, warna)
        _anggota(p, [(0.59, 0.30), (0.67, 0.16), (0.70, 0.02)],
                 [tb * 0.46, tb * 0.34, tb * 0.26], sk, mix(warna, (0, 0, 0), 0.15))
        # tangan mencengkeram
        p.circ(0.30 * W2, 0.02 * H2, tb * 0.30, fill=warna)
        p.circ(0.70 * W2, 0.02 * H2, tb * 0.30, fill=mix(warna, (0, 0, 0), 0.15))
        # kepala + moncong
        p.ell(0.42 * W2, 0.09 * H2, 0.58 * W2, 0.26 * H2, fill=warna)
        p.ell(0.40 * W2, 0.15 * H2, 0.50 * W2, 0.23 * H2, fill=mix(warna, (70, 58, 54), 0.45))
        p.circ(0.405 * W2, 0.145 * H2, tb * 0.10, fill=(18, 18, 24))
        p.circ(0.53 * W2, 0.125 * H2, tb * 0.09, fill=(18, 18, 24))
    spr = raster(W2, H2, g, ss=2)
    m = spr[..., 3]
    blit(spr, rim(m, (-0.5, -1), 2.6, 0.95, rim_warna), 0, 0)
    return pangkas(spr)


@functools.lru_cache(maxsize=4)
def dahan(panjang=760, warna=(26, 22, 24), rim_warna=(120, 160, 220), melengkung=0.18):
    """Dahan malam: batang melengkung + dedaunan sebagai massa gelap."""
    W2 = int(panjang)
    H2 = int(panjang * 0.34)

    def g(p):
        pts = [(0, H2 * 0.52), (W2 * 0.25, H2 * 0.46 + H2 * melengkung),
               (W2 * 0.55, H2 * 0.52), (W2 * 0.80, H2 * 0.42), (W2, H2 * 0.40)]
        dasar = [(x, y + H2 * 0.075) for x, y in pts]
        p.poly(catmull(pts, 10) + catmull(dasar, 10)[::-1], fill=warna)
        # dedaunan: rumpun membulat (bukan segitiga) supaya terbaca sebagai kanopi
        r = rng(21)
        for i in range(20):
            t = r.uniform(0.04, 0.96)
            x = lerp(0, W2, t)
            y = H2 * lerp(0.50, 0.42, t) + math.sin(t * 4) * 8
            L = r.uniform(0.035, 0.075) * W2
            ang = r.uniform(-2.9, -0.4)
            cx2 = x + math.cos(ang) * L * 0.8
            cy2 = y + math.sin(ang) * L * 0.8
            p.ell(cx2 - L, cy2 - L * 0.72, cx2 + L, cy2 + L * 0.72,
                  fill=mix(warna, (26, 46, 54), r.uniform(0.10, 0.45)))
    spr = raster(W2, H2, g, ss=2)
    m = spr[..., 3]
    blit(spr, rim(m, (-0.4, -1), 2.6, 0.7, rim_warna), 0, 0)
    return pangkas(spr)


# ============================================================== 6. JAM & WAKTU

@functools.lru_cache(maxsize=4)
def jam(r=150, warna=CYAN, gelap=(20, 26, 44)):
    """Muka jam: cincin, 12 tanda, jarum (statis — jarum ditambahkan aktor)."""
    d = int(r * 2 + 6)
    spr = np.zeros((d, d, 4), np.uint8)
    cx = cy = d / 2
    cv2.circle(spr, (int(cx), int(cy)), int(r), (*gelap, 210), -1, cv2.LINE_AA)
    cv2.circle(spr, (int(cx), int(cy)), int(r), (*warna, 190), max(2, int(r * 0.02)), cv2.LINE_AA)
    for i in range(12):
        a = i / 12 * math.tau - math.pi / 2
        r0 = r * (0.86 if i % 3 else 0.80)
        x0, y0 = cx + math.cos(a) * r0, cy + math.sin(a) * r0
        x1, y1 = cx + math.cos(a) * r * 0.96, cy + math.sin(a) * r * 0.96
        cv2.line(spr, (int(x0), int(y0)), (int(x1), int(y1)),
                 (*warna, 220), max(2, int(r * (0.030 if i % 3 == 0 else 0.018))), cv2.LINE_AA)
    return spr


def jarum_jam_spr(r, sudut_deg, panjang=0.74, warna=(255, 255, 255), tebal=0.045):
    d = int(r * 2 + 6)
    spr = np.zeros((d, d, 4), np.uint8)
    cx = cy = d / 2
    a = math.radians(sudut_deg - 90)
    x1, y1 = cx + math.cos(a) * r * panjang, cy + math.sin(a) * r * panjang
    cv2.line(spr, (int(cx), int(cy)), (int(x1), int(y1)), (*warna, 240),
             max(2, int(r * tebal)), cv2.LINE_AA)
    cv2.circle(spr, (int(cx), int(cy)), max(3, int(r * 0.05)), (*warna, 255), -1, cv2.LINE_AA)
    return spr


# ============================================================== 7. KABEL / SARAF

def kabel_saraf(panjang, amp=26, n=120, warna=(120, 200, 255), tebal=5, fase=0.0):
    """Garis saraf/iskemik: gelombang dengan pulsa terang yang berjalan."""
    W2 = int(panjang)
    H2 = int(amp * 2 + tebal * 4 + 8)
    xs = np.linspace(0, 1, n)
    ys = 0.5 + 0.30 * np.sin(xs * math.tau * 1.6 + fase) * np.sin(xs * math.pi)
    pts = np.stack([xs * W2, ys * H2], 1).astype(np.int32)
    spr = np.zeros((H2, W2, 4), np.uint8)
    cv2.polylines(spr, [pts], False, (*warna, 90), max(1, tebal * 3), cv2.LINE_AA)
    cv2.polylines(spr, [pts], False, (*warna, 235), int(tebal), cv2.LINE_AA)
    # pulsa
    for k in range(3):
        t = ((fase * 0.12 + k / 3.0) % 1.0)
        i = int(t * (n - 1))
        cv2.circle(spr, (int(pts[i][0]), int(pts[i][1])), max(3, int(tebal * 1.4)),
                   (235, 250, 255, 255), -1, cv2.LINE_AA)
    return premul(spr)


# ============================================================== 8. SELFTEST

def _selftest():
    import time
    from PIL import Image
    t0 = time.time()
    items = [
        ("kasur", kasur(1080, 210)),
        ("tidur", orang_tidur(1.0, "tutup")),
        ("kaget", orang_tidur(1.0, "kaget")),
        ("figur", figur(520, "jatuh")),
        ("otak", otak(700)),
        ("primata", primata(300)),
        ("dahan", dahan(700)),
        ("jam", jam(150)),
    ]
    print(f"sprite: {(time.time() - t0) * 1000:.0f} ms")
    sheet = Image.new("RGB", (1080, 1400), (10, 12, 22))
    x = 10
    y = 10
    row_h = 0
    for nama, s in items:
        im = Image.fromarray(s, "RGBA")
        if x + im.width > 1070:
            x = 10
            y += row_h + 10
            row_h = 0
        sheet.paste(im, (x, y), im)
        x += im.width + 10
        row_h = max(row_h, im.height)
        print(f"  {nama:8s} {s.shape[1]:4d}x{s.shape[0]:4d}")
    sheet.save("/tmp/v20_makhluk.jpg", quality=92)
    print("-> /tmp/v20_makhluk.jpg")


if __name__ == "__main__":
    _selftest()
