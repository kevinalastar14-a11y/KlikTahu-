#!/usr/bin/env python3
"""mesin_v20_cahaya.py — BAHASA VISUAL KlikTahu V20 ("KEDALAMAN").

Kenapa ada v20
--------------
v19 sudah benar arahnya: gelap, bercahaya, ber-HUD, seperti video panjang kanal.
Yang masih kurang dibanding produksi kelas atas:

  1. **Kedalaman** — v19 menumpuk objek di satu bidang. v20 menyusun tiga
     lapisan (jauh / tengah / dekat) dengan kabut atmosfer, ukuran berbeda,
     dan parallax yang berbeda per lapisan.
  2. **Cahaya** — v20 menambah berkas volumetrik bermodulasi waktu, bloom
     selektif, flare anamorfik, bokeh berparallax, dan bayangan kontak.
     Semua additif dihitung pada kotak lokal; tidak ada blur sekanvas.
  3. **Tipografi** — v20 memakai *mask reveal* (teks tersapu), angka yang
     dihitung naik, dan caption karaoke per kata (penonton menonton tanpa
     suara — ini penentu retensi Shorts).
  4. **Grafik data** — grafik area bergradasi, batang berlabel, piktogram
     titik, dan EEG prosedural. Semua animasi punya nilai awal & akhir yang
     dibaca dari data, bukan dari angka acak.
  5. **Gerak kamera** — rig kamera dengan dorongan (punch-in) halus, goyangan
     tangan, dan transisi cambuk (whip) ber-blur arah. Tidak ada cut mati.
  6. **Warna** — LUT filmis dua sumbu (teal-orange terukur), vignette, grain
     dua polaritas, dan dither gradasi supaya tidak muncul pita (banding)
     saat di-encode YouTube.

Aturan keras (dipelajari dari v18/v19)
--------------------------------------
  * `cv2` pada RGBA mengabaikan alpha -> selalu lewat lapisan + `komposit`.
  * semua ketebalan cv2 harus int.
  * sprite yang digambar tiap frame WAJIB di-cache (panel, pill, teks, glow).
  * `Kanvas()` jangan dipakai untuk frame (mengisi 6 MB lalu dibuang).
  * grain jangan lewat float32 (15 ms); pakai lempeng uint8 + add/subtract.

Modul ini hanya menyediakan BAHAN. Adegan ada di `mesin_v20_ep*.py`.

Selftest: python3 mesin_v20_cahaya.py
"""
from __future__ import annotations

import functools
import math
import os
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

import mesin_v18_inti as M
from mesin_v18_inti import (F_BOLD, F_MED, F_REG, F_SEMI, Kanvas, Pena, blit,
                            blit_add, blit_c, blit_kali, blit_s, clamp, eio, eo,
                            gblur, lerp, mask, mix, pangkas, raster, rng, smooth,
                            spr_text, tw)

W, H = 1080, 1920
FPS = 60

# ============================================================== 1. PALET

MALAM_0 = (3, 5, 12)        # hitam biru (pojok)
MALAM_1 = (7, 11, 24)
MALAM_2 = (12, 19, 40)
MALAM_3 = (19, 29, 60)      # langit atas

KAMAR_0 = (5, 7, 14)
KAMAR_1 = (12, 16, 30)
KAMAR_2 = (21, 27, 48)

CYAN = (88, 212, 246)
CYAN_L = (170, 240, 255)
GOLD = (255, 196, 84)
GOLD_L = (255, 226, 158)
CORAL = (255, 112, 96)
CORAL_L = (255, 168, 156)
VIOLET = (184, 142, 255)
VIOLET_L = (216, 190, 255)
GREEN = (104, 236, 178)
BLUE = (96, 152, 255)
PINK = (255, 138, 196)
PUTIH = (255, 255, 255)

TEKS = (242, 246, 255)
TEKS_2 = (180, 192, 216)
TEKS_3 = (118, 132, 160)

PANEL_FILL = (255, 255, 255, 15)
PANEL_LINE = (255, 255, 255, 44)
PANEL_LINE_2 = (255, 255, 255, 26)

# ============================================================== 2. DASAR

_GLOW = {}
_BG_CACHE = {}


def _uji_warna(c):
    return tuple(int(v) for v in c[:3])


def gradasi(k, y0, y1, stops, dither=0.85, seed=11):
    """Gradasi vertikal ber-dither (anti-banding) pada pita y0..y1.

    Ditulis dengan broadcast 1D supaya tidak membuat array float32 penuh
    berisi 3 kanal (v19 membuat 6 MB tiap panggilan).
    """
    y0, y1 = int(y0), int(y1)
    y0 = max(0, min(H, y0))
    y1 = max(0, min(H, y1))
    h = y1 - y0
    if h <= 0:
        return k
    ys = np.linspace(0.0, 1.0, h, dtype=np.float32)
    pos = np.array([s[0] for s in stops], np.float32)
    ramp = np.empty((h, 3), np.float32)
    for c in range(3):
        ramp[:, c] = np.interp(ys, pos, np.array([s[1][c] for s in stops], np.float32))
    if dither > 0:
        ramp += rng(seed).normal(0.0, dither, (h, 1)).astype(np.float32)
    k.a[y0:y1] = np.clip(np.broadcast_to(ramp[:, None, :], (h, k.w, 3)), 0, 255).astype(np.uint8)
    return k


@functools.lru_cache(maxsize=32)
def _fbm_plasma(w, h, skala=8, oktaf=5, seed=3):
    """Awan fBm resolusi rendah lalu diperbesar (dipakai nebula & tekstur)."""
    kecil = M.fbm(max(8, h // skala), max(8, w // skala), scale=6, octaves=oktaf,
                  seed=seed, gain=0.55)
    kecil = (kecil - kecil.min()) / max(1e-6, kecil.max() - kecil.min())
    besar = cv2.resize(kecil.astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    return np.clip(besar, 0, 1)


def nebula(k, y0=0, y1=H, warna=MALAM_3, kuat=1.0, seed=5, skala=10):
    """Kabut nebula: fBm halus + blur besar, alpha rendah.

    Pelajaran v20: fBm resolusi rendah tanpa blur terbaca seperti kembang kol.
    Kuncinya dua: (1) frekuensi lebih halus, (2) blur 1/40 tinggi, (3) alpha
    rendah supaya hanya menambah kedalaman, bukan tekstur.
    """
    y1 = min(H, y1 if y1 else H)
    h = int(y1 - int(y0))
    if h <= 0:
        return k
    a = _fbm_plasma(k.w, h, max(2, int(skala * 0.55)), 4, seed)
    a = gblur(a, max(6.0, h / 40.0))
    a = (a - a.min()) / max(1e-6, a.max() - a.min())
    lap = (a ** 3.0 * 150 * kuat).astype(np.uint8)
    spr = np.zeros((h, k.w, 4), np.uint8)
    spr[..., :3] = _uji_warna(warna)
    spr[..., 3] = lap
    blit_add(k.a, spr, 0, int(y0))
    return k


@functools.lru_cache(maxsize=24)
def bintang_spr(w, h, n=420, seed=7, terang=1.0):
    """Lapisan bintang (sprite sekali, ditempel additif)."""
    r = rng(seed)
    spr = np.zeros((h, w, 4), np.uint8)
    ys = r.integers(0, h, n)
    xs = r.integers(0, w, n)
    al = (r.uniform(0.18, 1.0, n) ** 1.8 * 255 * terang).astype(np.uint8)
    rad = r.choice([0, 1, 1, 2], n)
    for i in range(n):
        y, x, a, rr = int(ys[i]), int(xs[i]), int(al[i]), int(rad[i])
        if rr == 0:
            spr[y, x] = (255, 255, 255, a)
        else:
            cv2.circle(spr, (x, y), rr, (235, 245, 255, a), -1, cv2.LINE_AA)
    return spr


def bintang(k, n=420, seed=7, y0=0, y1=None, terang=1.0):
    y1 = H if y1 is None else y1
    spr = bintang_spr(k.w, int(y1 - y0), n, seed, terang)
    blit_add(k.a, spr, 0, int(y0))
    return k




def _isi(k, x0, y0, x1, y1, warna, alpha=255):
    """Isi kotak dengan warna + alpha (blend ke isi yang sudah ada).

    Kanvas v18 menyimpan RGB (bukan RGBA), jadi semua penulisan transparan
    harus dicampur manual di sini — kalau tidak, numpy menolak 4-tuple.
    """
    x0, y0 = max(0, int(x0)), max(0, int(y0))
    x1, y1 = min(k.w, int(x1)), min(k.h, int(y1))
    if x1 <= x0 or y1 <= y0:
        return
    c = np.array(_uji_warna(warna), np.int16)
    if alpha >= 255:
        k.a[y0:y1, x0:x1] = c.astype(np.uint8)
        return
    reg = k.a[y0:y1, x0:x1].astype(np.int16)
    k.a[y0:y1, x0:x1] = ((reg * (255 - alpha) + c * alpha) // 255).astype(np.uint8)

# ============================================================== 3. LATAR

def latar_jatuh(k, t=0.0):
    """Ruang kosong tempat 'jatuh' — pusat terang, tepi hitam, debu melaju."""
    h, w = k.h, k.w
    yy = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    d = np.sqrt((xx * 0.62) ** 2 + yy ** 2)
    inti = np.clip(1.0 - d * 0.85, 0, 1) ** 2.2
    base = np.empty((h, w, 3), np.float32)
    for c in range(3):
        base[..., c] = MALAM_0[c] + (MALAM_3[c] - MALAM_0[c]) * inti * 0.9
    base += rng(99).normal(0, 0.9, (h, w, 1)).astype(np.float32)
    k.a[:] = np.clip(base, 0, 255).astype(np.uint8)
    nebula(k, 0, h, (52, 74, 150), 0.70, seed=21, skala=9)
    nebula(k, int(h * 0.40), h, (96, 46, 108), 0.50, seed=33, skala=13)
    bintang(k, 360, 5, 0, h, 0.85)
    # berkas melaju dari pusat (kecepatan jatuh) — sprite statis, digeser aktor
    return k


def latar_kamar_lengkap(k):
    """Kamar tidur malam (versi final, dipakai episode)."""
    gradasi(k, 0, 1332, [(0, (18, 23, 44)), (0.5, (12, 16, 32)), (1, (7, 9, 20))], 0.7)
    gradasi(k, 1332, H, [(0, (8, 9, 16)), (1, (4, 5, 10))], 0.6, seed=17)

    tex = (_fbm_plasma(k.w, 900, 22, 4, 9) * 10).astype(np.int16)
    reg = k.a[:900].astype(np.int16)
    k.a[:900] = np.clip(reg + tex[..., None] - 5, 0, 255).astype(np.uint8)

    jx0, jy0, jx1, jy1 = 678, 246, 1012, 712
    # cahaya bulan di sekitar jendela
    pendar(k, (jx0 + jx1) // 2, (jy0 + jy1) // 2, 470, (70, 110, 190), 0.30, 2.6)
    # kaca
    kaca = np.zeros((jy1 - jy0, jx1 - jx0, 4), np.uint8)
    yy = np.linspace(0, 1, jy1 - jy0, dtype=np.float32)[:, None]
    for c in range(3):
        kaca[..., c] = np.clip((28, 50, 98)[c] * (1 - yy) + (12, 22, 52)[c] * yy, 0, 255).astype(np.uint8)
    kaca[..., 3] = 255
    # bintang di kaca
    bs = bintang_spr(jx1 - jx0, jy1 - jy0, 90, 31, 0.9)
    blit_add(k.a, bs, jx0, jy0)
    blit(k.a, kaca, jx0, jy0)
    blit_add(k.a, bs, jx0, jy0)
    # bulan
    mx, my, mr = 912, 358, 46
    pendar(k, mx, my, 190, (150, 190, 255), 0.42, 2.4)
    blit_add(k.a, _bulan_spr(mr), mx - mr, my - mr)
    # bingkai jendela
    def bingkai(p):
        p.rrect(jx0, jy0, jx1, jy1, 10, outline=(74, 92, 128), width=7)
        p.line([(jx0 + (jx1 - jx0) / 2, jy0), (jx0 + (jx1 - jx0) / 2, jy1)], (60, 76, 108), 5)
        p.line([(jx0, jy0 + (jy1 - jy0) * 0.52), (jx1, jy0 + (jy1 - jy0) * 0.52)], (60, 76, 108), 5)
    blit(k.a, raster(k.w, H, bingkai, ss=1), 0, 0)
    # kusen bawah + ambang
    def ambang(p):
        p.rect(jx0 - 26, jy1, jx1 + 26, jy1 + 20, fill=(26, 32, 52))
        p.rect(jx0 - 26, jy1, jx1 + 26, jy1 + 6, fill=(48, 58, 88))
    blit(k.a, raster(k.w, H, ambang, ss=1), 0, 0)
    # tirai kiri & kanan
    for x0, x1, s in ((jx0 - 150, jx0 + 6, 1), (jx1 - 6, jx1 + 150, -1)):
        tirai = _tirai_spr(int(x1 - x0), int(jy1 - jy0 + 120), s)
        blit(k.a, tirai, x0, jy0 - 40)
    # berkas cahaya bulan jatuh ke lantai
    _kolam_bulan(k, jx0, jy0, jx1, jy1, 1400)
    return k


@functools.lru_cache(maxsize=8)
def _bulan_spr(r):
    d = 2 * r + 1
    yy = np.arange(d, dtype=np.float32)[:, None] - r
    xx = np.arange(d, dtype=np.float32)[None, :] - r
    dist = np.sqrt(xx ** 2 + yy ** 2)
    disk = np.clip((r - dist) / 1.6, 0, 1)
    kawah = _fbm_plasma(d, d, 3, 4, 77)
    shade = 0.82 + 0.18 * kawah
    out = np.zeros((d, d, 4), np.uint8)
    for c in range(3):
        out[..., c] = np.clip((228, 236, 255)[c] * shade, 0, 255).astype(np.uint8)
    out[..., 3] = (disk * 255).astype(np.uint8)
    return out


@functools.lru_cache(maxsize=4)
def _tirai_spr(w, h, sisi):
    """Tirai bergelombang: siluet gelap dengan tepi terkena cahaya bulan."""
    spr = np.zeros((h, w, 4), np.uint8)
    xs = np.arange(w, dtype=np.float32)[None, :]
    ys = np.arange(h, dtype=np.float32)[:, None]
    fold = 0.5 + 0.5 * np.sin(xs / (w / 7.0) * math.pi + (0 if sisi > 0 else 1.6))
    body = fold ** 0.7
    alpha = np.clip(body * 255 * 0.94, 0, 255).astype(np.uint8)
    # tepi menipis di bawah
    fade = np.clip(1.0 - (ys / h) ** 3.4, 0, 1)
    alpha = (alpha.astype(np.float32) * fade).astype(np.uint8)
    base = np.array((10, 13, 26), np.float32)[None, None, :]
    tint = np.array((34, 46, 78), np.float32)[None, None, :] * (fold[..., None] ** 2)
    rgb = np.clip(base + tint, 0, 255).astype(np.uint8)
    spr[..., :3] = np.broadcast_to(rgb, (h, w, 3))
    spr[..., 3] = alpha
    return spr


def _kolam_bulan(k, jx0, jy0, jx1, jy1, y_lantai):
    """Berkas cahaya bulan dari jendela ke lantai (poligon aditif ber-blur)."""
    h = int(y_lantai - jy1)
    if h <= 0:
        return
    wA = jx1 - jx0
    W2 = int(wA * 3.4)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    lebar = wA * 0.5 + wA * 1.5 * yy
    xx = np.arange(W2, dtype=np.float32)[None, :] - W2 * 0.42
    xx = xx + yy * W2 * 0.30
    dd = np.abs(xx) / np.maximum(lebar, 1)
    prof = np.clip(1 - dd, 0, 1) ** 2.0
    vert = (1 - yy) ** 0.55
    a = np.clip(prof * vert * 46, 0, 255).astype(np.uint8)
    spr = np.zeros((h, W2, 4), np.uint8)
    spr[..., :3] = (120, 160, 240)
    spr[..., 3] = gblur(a, 22)
    blit_add(k.a, spr, int(jx0 - (W2 - wA) * 0.42), int(jy1))
    # pantulan di lantai
    pendar(k, (jx0 + jx1) // 2 - 40, y_lantai + 40, 300, (60, 90, 160), 0.20, 3.0)


def latar_otak(k, seed=5):
    """Ruang abstrak 'dalam kepala': gelap hangat + kabut + bintang redup."""
    gradasi(k, 0, H, [(0, (14, 10, 26)), (0.45, (9, 8, 22)), (1, (4, 4, 12))], 0.7)
    nebula(k, 0, H, (74, 52, 140), 0.65, seed, 9)
    nebula(k, int(H * 0.4), H, (30, 70, 120), 0.45, seed + 4, 12)
    bintang(k, 240, seed + 9, 0, H, 0.6)
    return k


def latar_langit(k, seed=7):
    """Langit malam untuk babak primata: gradasi + bintang + bulan."""
    gradasi(k, 0, H, [(0, (12, 18, 44)), (0.5, (8, 12, 30)), (1, (3, 5, 12))], 0.8)
    nebula(k, 0, int(H * 0.8), (40, 60, 130), 0.70, seed, 10)
    bintang(k, 460, seed + 3, 0, H, 1.0)
    pendar(k, 220, 330, 240, (140, 175, 255), 0.35, 2.6)
    blit_add(k.a, _bulan_spr(58), 220 - 58, 330 - 58)
    return k




# ---------------------------------------------------------------- blit cepat
def premul(spr):
    """Kembalikan sprite dengan RGB sudah dikali alpha (untuk blit additif SIMD).

    `blit_add` v18 mengubah seluruh kotak ke uint16 tiap panggilan (~16 ms untuk
    berkas cahaya 1200x460). Dengan RGB ter-premultiply, penambahan cahaya cukup
    satu `cv2.add` — 3-4x lebih murah dan hasilnya identik.
    """
    out = spr.copy()
    a = out[..., 3]
    out[..., :3] = ((out[..., :3].astype(np.uint16) * a[:, :, None]) >> 8).astype(np.uint8)
    return out


def blit_add_c(dst, pre, x, y, alpha=1.0):
    """Tempel additif dari sprite ter-premultiply (`premul`), cepat."""
    h, w = pre.shape[:2]
    x, y = int(round(x)), int(round(y))
    H2, W2 = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W2, x + w), min(H2, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sx0, sy0 = x0 - x, y0 - y
    sub = pre[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0), :3]
    reg = dst[y0:y1, x0:x1]
    if alpha >= 0.999:
        dst[y0:y1, x0:x1] = cv2.add(reg, sub)
    else:
        dst[y0:y1, x0:x1] = cv2.addWeighted(reg, 1.0, sub, float(alpha), 0.0)

# ============================================================== 4. CAHAYA

def glow_spr(r, warna=CYAN, kuat=1.0, keras=2.0, inti=0.0):
    """Pendar radial (cache). `inti` menambah titik terang di tengah."""
    key = (int(r), tuple(_uji_warna(warna)), round(kuat, 2), round(keras, 2), round(inti, 2))
    s = _GLOW.get(key)
    if s is not None:
        return s
    rr = max(1, int(r))
    yy = np.arange(-rr, rr + 1, dtype=np.float32)[:, None]
    xx = np.arange(-rr, rr + 1, dtype=np.float32)[None, :]
    d = np.sqrt(xx * xx + yy * yy) / rr
    a = np.clip(1.0 - d, 0, 1) ** keras
    if inti > 0:
        a = np.clip(a + np.clip(1.0 - d * 3.4, 0, 1) ** 1.5 * inti, 0, 1)
    out = np.zeros((2 * rr + 1, 2 * rr + 1, 4), np.uint8)
    out[..., :3] = _uji_warna(warna)
    out[..., 3] = np.clip(a * 255 * kuat, 0, 255).astype(np.uint8)
    out = premul(out)
    if len(_GLOW) > 420:
        _GLOW.clear()
    _GLOW[key] = out
    return out


def pendar(k, cx, cy, r, warna=CYAN, kuat=0.8, keras=2.0, inti=0.0):
    s = glow_spr(r, warna, kuat, keras, inti)
    blit_add_c(k.a, s, cx - r, cy - r)


@functools.lru_cache(maxsize=64)
def berkas_spr(h, w_atas, w_bawah, warna, kuat, keras=2.2, blur=13):
    """Satu berkas cahaya volumetrik (sprite) — dipakai berulang tiap frame."""
    h = int(h)
    W2 = int(max(w_atas, w_bawah) * 2 + 60)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    ww = (w_atas + (w_bawah - w_atas) * yy) / 2.0
    xx = np.arange(W2, dtype=np.float32)[None, :] - W2 / 2.0
    dd = np.abs(xx) / np.maximum(ww, 1.0)
    prof = np.clip(1.0 - dd, 0, 1) ** keras
    vert = (1.0 - yy) ** 1.15
    a = np.clip(prof * vert * kuat * 255, 0, 255).astype(np.uint8)
    spr = np.zeros((h, W2, 4), np.uint8)
    spr[..., :3] = _uji_warna(warna)
    spr[..., 3] = gblur(a, blur)
    return premul(spr)


def berkas(k, cx, y0, panjang, w_atas=40, w_bawah=180, warna=(150, 205, 255),
           kuat=0.20, t=0.0, fase=0.0, miring=0.0):
    """Berkas cahaya dari atas dengan kedipan halus (modulasi, bukan sprite baru)."""
    spr = berkas_spr(int(panjang), int(w_atas), int(w_bawah), tuple(_uji_warna(warna)),
                     round(kuat, 3))
    mod = 0.82 + 0.18 * math.sin(t * 0.55 + fase)
    dx = int(math.sin(t * 0.21 + fase) * 26 + miring)
    blit_add_c(k.a, spr, cx - spr.shape[1] // 2 + dx, int(y0), mod)
    return spr


def flare_anamorfik(k, cx, cy, panjang=420, warna=(120, 180, 255), kuat=0.55, tebal=7):
    """Garis cahaya horizontal (ciri lensa anamorfik) + inti."""
    p = int(panjang)
    hh = max(3, int(tebal))
    m = np.linspace(-1, 1, p, dtype=np.float32)[None, :]
    vert = np.exp(-(np.linspace(-1, 1, hh, dtype=np.float32)[:, None] ** 2) * 6.0)
    a = (np.exp(-(m ** 2) * 5.0) * vert * kuat * 255).astype(np.uint8)
    spr = np.zeros((hh, p, 4), np.uint8)
    spr[..., :3] = _uji_warna(warna)
    spr[..., 3] = a
    blit_add_c(k.a, premul(spr), int(cx - p / 2), int(cy - hh / 2))
    pendar(k, cx, cy, int(tebal * 7), warna, kuat * 0.55, 2.2, 0.8)


@functools.lru_cache(maxsize=8)
def partikel_spr(r, warna):
    """Butir bokeh lembut (cache per radius kecil)."""
    d = 2 * int(r) + 1
    yy = np.arange(d, dtype=np.float32)[:, None] - r
    xx = np.arange(d, dtype=np.float32)[None, :] - r
    dist = np.sqrt(xx ** 2 + yy ** 2) / max(1.0, r)
    a = np.clip(1 - dist, 0, 1) ** 1.6
    ring = np.clip(1 - np.abs(dist - 0.72) * 7.0, 0, 1) * 0.45
    out = np.zeros((d, d, 4), np.uint8)
    out[..., :3] = _uji_warna(warna)
    out[..., 3] = np.clip((a * 0.7 + ring) * 255, 0, 255).astype(np.uint8)
    return premul(out)


def bokeh(k, P, t, skala=1.0, parallax=(0.0, 0.0), alpha=1.0):
    """Butir debu/bokeh berparallax. `P` = array (x, y, r, fase, kecepatan)."""
    for i in range(len(P)):
        x, y, r, fasa, kec = P[i]
        xx = (x + t * kec * 12 + parallax[0] * (r / 6.0)) % (W + 200) - 100
        yy = (y - t * kec * 26 + parallax[1] * (r / 6.0)) % (H + 200) - 100
        rr = max(1, int(r * skala))
        fl = 0.55 + 0.45 * math.sin(t * 1.6 + fasa)
        s = partikel_spr(rr, (188, 220, 255))
        blit_add_c(k.a, s, int(xx), int(yy), fl * alpha)


def kilat(k, cx=W // 2, cy=H // 2, r=520, warna=(255, 240, 214), kuat=0.85):
    pendar(k, cx, cy, int(r * 0.55), warna, kuat, 2.0)
    pendar(k, cx, cy, int(r), warna, kuat * 0.35, 3.2)


def cincin(k, cx, cy, r, warna=CYAN, tebal=3.0, alpha=1.0, dash=0, glow=0.55):
    r = max(1, int(r))
    d = 2 * r + 3
    spr = np.zeros((d, d, 4), np.uint8)
    cv2.circle(spr, (r, r), r, (*_uji_warna(warna), int(255 * alpha)),
               max(1, int(round(tebal))), cv2.LINE_AA)
    if glow > 0:
        spr[..., 3] = np.clip(spr[..., 3].astype(np.float32) * 1.0 +
                              gblur(spr[..., 3], 4).astype(np.float32) * glow, 0, 255).astype(np.uint8)
    blit_add_c(k.a, premul(spr), cx - r, cy - r)


# ============================================================== 5. UI

@functools.lru_cache(maxsize=256)
def panel_spr(w, h, radius=26, aksen=None, garis=PANEL_LINE, isi=PANEL_FILL,
              tebal=1.6, sudut=True):
    """Panel kaca: isi transparan + border tipis + sapuan atas + sudut aksen."""
    w, h = int(w), int(h)
    pad = 4
    W2, H2 = w + pad * 2, h + pad * 2
    out = np.zeros((H2, W2, 4), np.uint8)

    def g(p):
        p.rrect(0, 0, w, h, radius, fill=isi)
    isi_spr = raster(w, h, g, ss=3)
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    sheen = np.clip(1 - ys / 0.62, 0, 1) ** 1.5
    m = isi_spr[..., 3].astype(np.float32) / 255.0
    isi_spr[..., :3] = np.clip(isi_spr[..., :3].astype(np.float32) +
                               sheen[:, :, None] * 12 * m[..., None], 0, 255).astype(np.uint8)
    blit(out, isi_spr, pad, pad)

    def g2(p):
        p.rrect(0, 0, w, h, radius, outline=garis, width=tebal)
    blit(out, raster(w, h, g2, ss=3), pad, pad)

    if aksen is not None:
        def g3(p):
            p.rrect(0, 0, 5, max(10, int(h * 0.30)), 3, fill=aksen)
        blit(out, raster(5, max(12, int(h * 0.30)), g3, ss=3), pad, pad + int(h * 0.16))
    if sudut:
        def g4(p):
            L = 16
            for (x, y, dx, dy) in ((0, 0, 1, 1), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)):
                p.line([(x + dx * 2, y + dy * L), (x + dx * 2, y + dy * 2),
                        (x + dx * L, y + dy * 2)], (*_uji_warna(aksen or CYAN), 190), 2.0)
        blit(out, raster(w, h, g4, ss=3), pad, pad)
    return out


def panel(k, x, y, w, h, alpha=1.0, **kw):
    s = panel_spr(int(w), int(h), **kw)
    blit(k.a, s, int(x) - 4, int(y) - 4, alpha)
    return s


@functools.lru_cache(maxsize=128)
def pill_spr(teks, warna=CYAN, size=34, pad_x=26, pad_y=13, name=F_SEMI,
             glow=0.65, tebal=2.0):
    """Pill caption: teks + border menyala + titik aksen."""
    warna = _uji_warna(warna)
    tw_ = int(tw(teks, name, size))
    w = tw_ + pad_x * 2 + 22
    h = int(size * 1.72) + pad_y * 2
    pad = 10
    out = np.zeros((h + pad * 2, w + pad * 2, 4), np.uint8)
    r = h / 2

    def g_body(p):
        p.rrect(0, 0, w, h, r, fill=(*warna, 26))
    blit(out, raster(w, h, g_body, ss=3), pad, pad)

    def g_line(p):
        p.rrect(0, 0, w, h, r, outline=(*warna, 235), width=tebal)
    garis = raster(w, h, g_line, ss=3)
    if glow > 0:
        halo = np.zeros_like(garis)
        halo[..., :3] = garis[..., :3]
        halo[..., 3] = (gblur(garis[..., 3], 5).astype(np.float32) * glow).astype(np.uint8)
        blit(out, halo, pad, pad)
    blit(out, garis, pad, pad)
    # titik aksen
    def g_dot(p):
        p.circ(pad_x * 0.55 + 4, h / 2, 5, fill=warna)
    blit(out, raster(int(pad_x * 0.55 + 12), h, g_dot, ss=3), pad, pad)
    txt = spr_text(teks, TEKS, name, size, tracking=0.2)
    blit(out, txt, pad + pad_x + 16, pad + (h - txt.shape[0]) // 2)
    return out


# ---------------------------------------------------------------- glif aman
# Font v18 (F_BOLD/F_SEMI) TIDAK memuat panah. Kalau "→" dipaksa masuk, FreeType
# menggambar kotak tofu — ini pernah lolos ke render Ep56 sebelum ketahuan.
# Semua teks episode lewat _aman() supaya tidak ada kotak yang sampai ke video.
SANDI = {"→": "»", "↑": "»", "↓": "»", "▸": "›", "▶": "›", "▲": "›", "✓": "√"}

# `TANPA_TEKS` = mode "art only": semua tipografi dibungkam (panel & grafis tetap).
# Dipakai pembuat thumbnail supaya teks di dalam adegan tidak bertumpuk dengan
# teks thumbnail — `bersih=True` saja tidak cukup karena tipografi besar digambar
# oleh aktor, bukan oleh HUD.
TANPA_TEKS = False

# `AUDIT` diisi list oleh selftest tata letak; setiap teks mencatat kotaknya
# supaya tabrakan antar-teks / teks-vs-caption bisa diperiksa tanpa HDMI mata.
AUDIT = None


def _aman(teks):
    for a, b in SANDI.items():
        if a in teks:
            teks = teks.replace(a, b)
    return teks


def _catat(spr, x, y, teks):
    """Catat kotak TINTA (bukan kotak sprite) untuk audit tata letak.

    Sprite teks membawa padding bayangan 7-10 px; kalau yang dicatat kotak
    sprite, dua teks yang sebenarnya berjarak 6 px terlihat "bertabrakan".
    Jadi ambang alpha 24 dipakai: hanya piksel yang benar-benar terbaca.
    """
    if AUDIT is None:
        return
    a = spr[..., 3]
    ys = np.flatnonzero((a > 24).any(1))
    xs = np.flatnonzero((a > 24).any(0))
    if len(xs) == 0 or len(ys) == 0:
        AUDIT.append((int(x), int(y), int(x + spr.shape[1]), int(y + spr.shape[0]), teks))
        return
    AUDIT.append((int(x) + int(xs[0]), int(y) + int(ys[0]),
                  int(x) + int(xs[-1]) + 1, int(y) + int(ys[-1]) + 1, teks))


def panah(k, x, y, arah="kanan", warna=GOLD, size=46, alpha=1.0):
    """Panah digambar dengan cv2 — bukan glif font (lihat SANDI)."""
    if TANPA_TEKS:
        return
    warna = _uji_warna(warna)
    L = int(size)
    t = max(3, int(size * 0.14))
    pad = t + 4
    lap = np.zeros((L + pad * 2, L + pad * 2, 4), np.uint8)
    c0, c1 = pad, pad + L
    mid = pad + L // 2
    hd = int(L * 0.34)
    if arah in ("kanan", "kiri"):
        a, b = (c0, c1) if arah == "kanan" else (c1, c0)
        cv2.line(lap, (a, mid), (b, mid), (*warna, 255), t, cv2.LINE_AA)
        base = b - hd if arah == "kanan" else b + hd
        cv2.line(lap, (b, mid), (base, mid - hd // 2), (*warna, 255), t, cv2.LINE_AA)
        cv2.line(lap, (b, mid), (base, mid + hd // 2), (*warna, 255), t, cv2.LINE_AA)
    else:
        a, b = (c0, c1) if arah == "bawah" else (c1, c0)
        cv2.line(lap, (mid, a), (mid, b), (*warna, 255), t, cv2.LINE_AA)
        base = b - hd if arah == "bawah" else b + hd
        cv2.line(lap, (mid, b), (mid - hd // 2, base), (*warna, 255), t, cv2.LINE_AA)
        cv2.line(lap, (mid, b), (mid + hd // 2, base), (*warna, 255), t, cv2.LINE_AA)
    blit(k.a, lap, int(x), int(y), alpha)
    _catat(lap, x, y, f"panah:{arah}")


def tulis(k, teks, x, y, warna=TEKS, size=44, name=F_SEMI, tracking=0.0,
          alpha=1.0, shadow=True, align="kiri"):
    """Tulis teks dengan bayangan lembut (kontras di latar gelap)."""
    if TANPA_TEKS:
        return 0
    teks = _aman(teks)
    sh = (3, 6, 16) if shadow else None
    s = spr_text(teks, _uji_warna(warna), name, size, tracking=tracking,
                 shadow=sh, shadow_blur=7, shadow_off=(0, 5), shadow_a=120) if shadow \
        else spr_text(teks, _uji_warna(warna), name, size, tracking=tracking)
    if align == "tengah":
        x = x - s.shape[1] / 2
    elif align == "kanan":
        x = x - s.shape[1]
    blit(k.a, s, int(x), int(y), alpha)
    _catat(s, x, y, teks)
    return s.shape[1]


def tulis_wipe(k, teks, x, y, prog, warna=TEKS, size=44, name=F_SEMI,
               tracking=0.0, align="kiri", arah="kiri", warna_tepi=None, shadow=True):
    """Teks tersapu (mask reveal) dengan tepi cahaya — tipografi kinetik v20."""
    if prog <= 0.001 or TANPA_TEKS:
        return 0
    teks = _aman(teks)
    sh = (3, 6, 16) if shadow else None
    s = (spr_text(teks, _uji_warna(warna), name, size, tracking=tracking,
                  shadow=sh, shadow_blur=7, shadow_off=(0, 5), shadow_a=120)
         if shadow else spr_text(teks, _uji_warna(warna), name, size, tracking=tracking)).copy()
    hh, ww = s.shape[:2]
    p = clamp(prog)
    if align == "tengah":
        x = x - ww / 2
    elif align == "kanan":
        x = x - ww
    if arah == "kiri":
        n = int(ww * p)
        if n <= 0:
            return 0
        s[:, n:] = 0
        tepi = n
        tebal = 3
        if warna_tepi is not None and n < ww:
            s[:, max(0, tepi - tebal):tepi, :3] = _uji_warna(warna_tepi)
    elif arah == "bawah":
        n = int(hh * p)
        if n <= 0:
            return 0
        s[: hh - n] = 0
    else:  # tengah
        r = p * 0.5
        a0, a1 = int(ww * (0.5 - r)), int(ww * (0.5 + r))
        mask_ = np.zeros(ww, np.uint8)
        mask_[a0:a1] = 255
        s[..., 3] = (s[..., 3].astype(np.uint16) * mask_[None, :] // 255).astype(np.uint8)
    blit(k.a, s, int(x), int(y))
    _catat(s, x, y, teks)
    return ww


def angka(k, nilai, x, y, warna=GOLD, size=170, satuan="", label="", align="kiri",
          alpha=1.0, desimal=1):
    """Angka besar + satuan + label kecil (pola HUD referensi)."""
    teks = f"{nilai:,.{desimal}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    s = spr_text(teks, _uji_warna(warna), F_BOLD, size, tracking=-1.5,
                 shadow=(4, 8, 20), shadow_blur=10, shadow_off=(0, 7), shadow_a=130)
    ww = s.shape[1]
    if align == "tengah":
        x = x - ww / 2
    elif align == "kanan":
        x = x - ww
    blit(k.a, s, int(x), int(y), alpha)
    yy = y + s.shape[0] - int(size * 0.10)
    if satuan:
        tulis(k, satuan, x, yy, warna, int(size * 0.24), F_BOLD, 2.0, alpha)
    if label:
        tulis(k, label, x, yy + int(size * 0.30), TEKS_3, int(size * 0.15), F_SEMI,
              2.2, alpha)
    return ww


def label_kecil(k, teks, x, y, warna=TEKS_3, size=25, alpha=1.0, align="kiri",
                tracking=2.0):
    if TANPA_TEKS:
        return 0
    teks = _aman(teks)
    s = spr_text(teks, _uji_warna(warna), F_SEMI, size, tracking=tracking)
    if align == "tengah":
        x = x - s.shape[1] / 2
    elif align == "kanan":
        x = x - s.shape[1]
    blit(k.a, s, int(x), int(y), alpha)
    _catat(s, x, y, teks)
    return s.shape[1]


@functools.lru_cache(maxsize=64)
def badge_spr(teks, warna=CYAN, nomor="01", size=25):
    warna = _uji_warna(warna)
    isi = f"{nomor}  ·  {teks}"
    tw_ = int(tw(isi, F_SEMI, size)) + 30
    h = 54
    w = tw_ + 36
    out = np.zeros((h + 6, w + 6, 4), np.uint8)

    def g(p):
        p.rrect(0, 0, w, h, h / 2, fill=(*warna, 22), outline=(*warna, 200), width=1.6)
        p.circ(20, h / 2, 5.5, fill=warna)
    blit(out, raster(w, h, g, ss=3), 3, 3)
    t = spr_text(isi, _uji_warna(TEKS), F_SEMI, size, tracking=0.6)
    blit(out, t, 3 + 36, 3 + (h - t.shape[0]) // 2)
    return out


@functools.lru_cache(maxsize=8)
def merek_spr(teks="KlikTahu", size=33):
    """Merek kiri atas: ikon segitiga + wordmark."""
    tw_ = int(tw(teks, F_BOLD, size))
    w, h = tw_ + 54, int(size * 1.7)
    out = np.zeros((h + 4, w + 4, 4), np.uint8)

    def g(p):
        p.poly([(6, 24), (22, 24), (14, 9)], fill=GOLD)
        p.poly([(10, 27), (26, 27), (18, 41)], fill=(*GOLD, 120))
    blit(out, raster(34, 48, g, ss=3), 3, 3)
    t = spr_text(teks, _uji_warna(TEKS), F_BOLD, size, tracking=0.4,
                 shadow=(0, 0, 0), shadow_blur=6, shadow_off=(0, 3), shadow_a=90)
    blit(out, t, 3 + 40, 3 + (h - t.shape[0]) // 2)
    return out


def progres(k, frac, warna=CYAN, y=1886, x0=62, x1=None, tinggi=5, segmen=9, aktif=None):
    """Bar progres segmen di tepi bawah (gaya HUD video panjang)."""
    x1 = (W - 62) if x1 is None else x1
    frac = clamp(frac)
    # jalur
    _isi(k, x0, y, x1, y + tinggi, (255, 255, 255), 22)
    isi = int((x1 - x0) * frac)
    if isi > 0:
        _isi(k, x0, y, x0 + isi, y + tinggi, warna)
        pendar(k, x0 + isi, y + tinggi // 2, 26, warna, 0.35, 2.6)
    if segmen > 1:
        for i in range(1, segmen):
            xx = x0 + (x1 - x0) * i // segmen
            _isi(k, xx, y - 4, xx + 2, y + tinggi + 4, (6, 8, 14))


def hud(k, merek_teks, babak_nama, babak_warna, nomor, frac, sumber=None):
    """HUD lengkap: merek, badge babak, progres, baris sumber."""
    blit(k.a, merek_spr(merek_teks), 54, 52)
    s = badge_spr(babak_nama, babak_warna, nomor)
    blit(k.a, s, W - s.shape[1] - 52, 46)
    progres(k, frac, babak_warna)
    if sumber:
        label_kecil(k, sumber.upper(), W / 2, 1826, (96, 108, 134), 20, 0.9, "tengah", 2.4)


# ============================================================== 6. CAPTION KARAOKE

def _pecah_kata(teks):
    return [w for w in teks.split() if w]


def _waktu_kata(kata, total):
    """Bagi durasi menurut panjang kata (+ jeda tanda baca) — tanpa file alignment."""
    bobot = []
    for w in kata:
        b = len(w) + 1.4
        if w[-1] in ",;:":
            b += 1.6
        if w[-1] in ".!?":
            b += 3.2
        bobot.append(b)
    tot = sum(bobot)
    akum, out = 0.0, []
    for b in bobot:
        a = akum
        akum += b / tot * total
        out.append((a, akum))
    return out


@functools.lru_cache(maxsize=512)
def caption_spr(teks, aktif, warna=CYAN, size=46, maxw=904):
    """Caption dua baris dengan kata aktif menyala — sprite di-cache per kata aktif."""
    kata = _pecah_kata(teks)
    if not kata:
        return np.zeros((4, 4, 4), np.uint8)
    name = F_BOLD
    baris, cur = [], []
    for w in kata:
        cand = " ".join(cur + [w])
        if cur and tw(cand, name, size) > maxw:
            baris.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        baris.append(cur)

    spasi = tw(" ", name, size)
    tinggi = int(size * 1.30)
    total_h = tinggi * len(baris) + 8
    out_w = int(maxw) + 8
    out = np.zeros((total_h, out_w, 4), np.uint8)
    idx = 0
    for bi, baris_kata in enumerate(baris):
        lebar = sum(tw(w, name, size) for w in baris_kata) + spasi * (len(baris_kata) - 1)
        x = (out_w - lebar) / 2
        for w in baris_kata:
            on = idx == aktif
            lewat = idx < aktif
            if on:
                s = spr_text(w, _uji_warna(warna), name, size,
                             shadow=(0, 0, 0), shadow_blur=8, shadow_off=(0, 3), shadow_a=170)
            else:
                c = TEKS if lewat else (150, 160, 182)
                s = spr_text(w, c, name, size,
                             shadow=(0, 0, 0), shadow_blur=8, shadow_off=(0, 3), shadow_a=150)
            blit(out, s, int(x), bi * tinggi + 4)
            if on:
                # garis bawah menyala
                yy = bi * tinggi + 4 + s.shape[0] - 6
                cv2.line(out, (int(x) + 2, yy), (int(x + tw(w, name, size)) - 2, yy),
                         (*_uji_warna(warna), 230), 3, cv2.LINE_AA)
            x += tw(w, name, size) + spasi
            idx += 1
    return pangkas(out, ambang=1, tepi=2)


def caption_karaoke(k, teks, t, dur, warna=CYAN, y=1392, size=46, maxw=904,
                    alpha=1.0):
    """Caption karaoke: kata menyala mengikuti waktu ucap (estimasi panjang kata).

    `alpha` dipakai babak terakhir: caption diredupkan selama blend loop supaya
    tidak ada dua teks berbeda yang saling tembus (hantu teks di penutup).
    """
    if alpha <= 0.003:
        return
    kata = _pecah_kata(teks)
    if not kata:
        return
    waktu = _waktu_kata(kata, max(0.4, dur))
    aktif = len(kata) - 1
    for i, (a, b) in enumerate(waktu):
        if t < b:
            aktif = i
            break
    aktif = max(0, min(len(kata) - 1, aktif))
    s = caption_spr(teks, aktif, _uji_warna(warna), size, maxw)
    blit(k.a, s, (W - s.shape[1]) // 2, int(y), alpha)



def scrim(k, y0, y1, alpha=(0, 150), warna=(4, 6, 14)):
    """Pita gelap bergradasi di belakang caption.

    Shorts selalu ditonton tanpa suara, jadi caption harus terbaca di atas
    gambar apa pun. Scrim murah (satu operasi numpy per frame).
    """
    y0, y1 = max(0, int(y0)), min(k.h, int(y1))
    if y1 <= y0:
        return k
    a = np.linspace(alpha[0], alpha[1], y1 - y0, dtype=np.float32)[:, None]
    reg = k.a[y0:y1].astype(np.float32)
    c = np.array(_uji_warna(warna), np.float32)[None, None, :]
    k.a[y0:y1] = np.clip(reg * (1 - a[..., None] / 255.0) + c * (a[..., None] / 255.0),
                         0, 255).astype(np.uint8)
    return k

# ============================================================== 7. GRAFIK

def grafik_area(k, x0, y0, w, h, data, warna=CYAN, prog=1.0, garis_tebal=4,
                isi=True, grid=4, label_y=None, tebal_grid=1):
    """Grafik area bergradasi dengan sumbu & garis menyala.

    `data` = list nilai 0..1 dari kiri ke kanan. `prog` menyapu kurva.
    """
    prog = clamp(prog)
    n = len(data)
    if n < 2:
        return
    xs = np.linspace(x0, x0 + w, n)
    ys = y0 + h - np.array(data, np.float32) * h
    # grid horizontal
    for i in range(grid + 1):
        yy = int(y0 + h * i / grid)
        _isi(k, x0, yy, x0 + w, yy + tebal_grid, (255, 255, 255), 20)
    potong = max(2, int(n * prog))
    # area bergradasi (alpha menurun ke bawah)
    if isi and potong > 1:
        pad_i = 2
        lw, lh = int(w + pad_i * 2), int(h + pad_i * 2)
        m = np.zeros((lh, lw), np.uint8)
        pol = [(int(xs[0] - x0 + pad_i), int(y0 + h - y0 + pad_i))]
        pol += [(int(xs[i] - x0 + pad_i), int(ys[i] - y0 + pad_i)) for i in range(potong)]
        pol += [(int(xs[potong - 1] - x0 + pad_i), int(y0 + h - y0 + pad_i))]
        cv2.fillPoly(m, [np.array(pol, np.int32)], 255, cv2.LINE_AA)
        yy = np.linspace(0, 1, lh, dtype=np.float32)[:, None]
        lap = np.zeros((lh, lw, 4), np.uint8)
        for c in range(3):
            lap[..., c] = np.clip(np.array(_uji_warna(warna), np.float32)[c] * (1 - yy * 0.25), 0, 255).astype(np.uint8)
        lap[..., 3] = (m.astype(np.float32) * (0.40 - 0.34 * yy)).astype(np.uint8)
        blit_add_c(k.a, premul(lap), int(x0) - pad_i, int(y0) - pad_i)
    # garis
    pts = [(int(xs[i] - x0 + 8), int(ys[i] - y0 + 8)) for i in range(potong)]
    if len(pts) > 1:
        lw, lh = int(w + 16), int(h + 16)
        lap = np.zeros((lh, lw, 4), np.uint8)
        cv2.polylines(lap, [np.array(pts, np.int32)], False,
                      (*_uji_warna(warna), 255), int(garis_tebal), cv2.LINE_AA)
        halo = np.zeros_like(lap)
        halo[..., :3] = lap[..., :3]
        halo[..., 3] = (gblur(lap[..., 3], 6).astype(np.float32) * 0.75).astype(np.uint8)
        blit_add_c(k.a, premul(halo), int(x0) - 8, int(y0) - 8)
        blit_add_c(k.a, premul(lap), int(x0) - 8, int(y0) - 8)
        pendar(k, int(xs[potong - 1]), int(ys[potong - 1]), 22, warna, 0.6, 2.2, 0.7)
    if label_y:
        for teks, v in label_y:
            yy = int(y0 + h - v * h)
            label_kecil(k, teks, x0 + w + 10, yy - 12, TEKS_3, 20)


def grafik_batang(k, x0, y0, w, baris, prog=1.0, tinggi_bar=30, jarak=58,
                  warna=CYAN, label_w=190, nilai=True):
    """Batang horizontal berlabel; nilai otomatis pindah ke luar kalau sempit."""
    prog = clamp(prog)
    maks = max(1e-6, max(abs(v) for _, v, _ in baris))
    for i, (nama, v, ket) in enumerate(baris):
        yy = int(y0 + i * jarak)
        label_kecil(k, nama.upper(), x0, yy + 2, TEKS_2, 22, 1.0, "kiri", 1.4)
        xa = x0 + label_w
        xb = x0 + w
        _isi(k, xa, yy + tinggi_bar // 2 - 1, xb, yy + tinggi_bar // 2 + 1, (255, 255, 255), 18)
        p = clamp(prog * 1.15 - i * 0.08)
        panjang = int((xb - xa) * (abs(v) / maks) * p)
        c = _uji_warna(warna if v >= 0 else CORAL)
        if panjang > 2:
            _isi(k, xa, yy + 4, xa + panjang, yy + tinggi_bar - 4, c)
            _isi(k, xa, yy + 4, xa + panjang, yy + 6, mix(c, (255, 255, 255), 0.35))
            pendar(k, xa + panjang, yy + tinggi_bar // 2, 18, c, 0.30, 2.4)
        if nilai:
            label_kecil(k, ket or f"{v:.0f}", xb + 12, yy + 4, TEKS_3, 21)
    return


def piktogram(k, x0, y0, kolom, baris, isi, warna=CYAN, prog=1.0, r=9, jarak=22):
    """Grid titik: `isi` dari total menyala (untuk 70% dari 100 orang)."""
    total = kolom * baris
    prog = clamp(prog)
    nyala = int(total * clamp(isi) * prog)
    for i in range(total):
        cx = int(x0 + (i % kolom) * jarak)
        cy = int(y0 + (i // kolom) * jarak)
        if i < nyala:
            cv2.circle(k.a, (cx, cy), r, _uji_warna(warna), -1, cv2.LINE_AA)
        else:
            cv2.circle(k.a, (cx, cy), r, (150, 165, 195), 1, cv2.LINE_AA)


def eeg(k, x0, y0, w, h, t, warna=CYAN, amp=1.0, laju=7.0, n=None):
    """Gelombang EEG prosedural (jumlah sampel mengikuti lebar)."""
    n = n or max(24, int(w / 6))
    xs = np.linspace(x0, x0 + w, n)
    tt = np.linspace(t, t + 1.4, n)
    y = (np.sin(tt * laju) * 0.5 +
         np.sin(tt * laju * 2.31 + 1.2) * 0.28 +
         np.sin(tt * laju * 0.47 + 0.4) * 0.44 +
         np.sin(tt * 31.0) * 0.10)
    y = y / np.max(np.abs(y)) * amp
    ys = y0 + h / 2 - y * (h / 2)
    pad = 10
    lw, lh = int(w + pad * 2), int(h + pad * 2)
    pts = np.stack([xs - x0 + pad, ys - y0 + pad], 1).astype(np.int32)
    lap = np.zeros((lh, lw, 4), np.uint8)
    cv2.polylines(lap, [pts], False, (*_uji_warna(warna), 235), 3, cv2.LINE_AA)
    halo = np.zeros_like(lap)
    halo[..., :3] = lap[..., :3]
    halo[..., 3] = (gblur(lap[..., 3], 6).astype(np.float32) * 0.8).astype(np.uint8)
    blit_add_c(k.a, premul(halo), int(x0) - pad, int(y0) - pad)
    blit_add_c(k.a, premul(lap), int(x0) - pad, int(y0) - pad)


def garis_pandu(k, titik, teks, warna=TEKS, arah="kanan", size=26, alpha=1.0, prog=1.0):
    """Garis pandu: dari objek ke label, dengan titik jangkar."""
    x, y = int(titik[0]), int(titik[1])
    prog = clamp(prog)
    if prog <= 0.01:
        return
    dx = 1 if arah == "kanan" else -1
    L = 90
    ex = x + dx * L
    pad = 16
    if dx > 0:
        x0 = x - pad
    else:
        x0 = ex - 140
    y0 = y - 34 - pad
    lw, lh = int(abs(L) + 160), int(34 + pad * 2)
    lap = np.zeros((lh, lw, 4), np.uint8)
    seg = [(x - x0, y - y0), (x - x0 + dx * 26, y - y0 - 34), (ex - x0, y - y0 - 34)]
    cv2.polylines(lap, [np.array(seg, np.int32)], False, (*_uji_warna(warna), 210), 2, cv2.LINE_AA)
    cv2.circle(lap, (x - x0, y - y0), 5, (*_uji_warna(warna), 255), -1, cv2.LINE_AA)
    if prog < 1:
        cut = int((x - x0) + dx * (L + 4) * prog)
        if dx > 0:
            lap[:, max(0, cut):] = 0
        else:
            lap[:, :max(0, cut)] = 0
    blit_add(k.a, lap, int(x0), int(y0))
    tx = ex + 12 if dx > 0 else ex - 12
    label_kecil(k, teks.upper(), tx, y - 52, warna, size, alpha, "kiri" if dx > 0 else "kanan", 1.4)


# ============================================================== 8. EFEK & KAMERA

def shake(t, amp=10.0, laju=2.1, seed=3):
    """Goyangan kamera tangan (bukan acak murni: dua sinus tak selaras)."""
    return (math.sin(t * laju + seed) * amp + math.sin(t * laju * 2.37 + 1.7) * amp * 0.4,
            math.cos(t * laju * 1.31 + 0.4) * amp * 0.8 + math.sin(t * laju * 3.1) * amp * 0.3)


def dorong(k, pusat=(W / 2, H / 2), skala=1.0, geser=(0, 0)):
    """Zoom/punch pada frame (cv2.resize kotak tengah) — 1 operasi per frame."""
    if abs(skala - 1.0) < 0.004 and abs(geser[0]) < 1 and abs(geser[1]) < 1:
        return k.a
    h, w = k.h, k.w
    cw, ch = int(w / skala), int(h / skala)
    cx = int(clamp(pusat[0] + geser[0], cw / 2, w - cw / 2))
    cy = int(clamp(pusat[1] + geser[1], ch / 2, h - ch / 2))
    crop = k.a[cy - ch // 2:cy - ch // 2 + ch, cx - cw // 2:cx - cw // 2 + cw]
    return cv2.resize(crop, (w, h), interpolation=cv2.INTER_LINEAR)


def whip(k, prog, arah="kanan", kuat=1.0):
    """Blur arah (whip pan): turunkan resolusi horizontal lalu kembalikan."""
    p = math.sin(math.pi * clamp(prog)) * kuat
    if p < 0.02:
        return k.a
    f = max(1, int(1 + p * 7))
    if arah in ("kanan", "kiri"):
        small = cv2.resize(k.a, (max(8, k.w // f), k.h), interpolation=cv2.INTER_AREA)
        out = cv2.resize(small, (k.w, k.h), interpolation=cv2.INTER_LINEAR)
    else:
        small = cv2.resize(k.a, (k.w, max(8, k.h // f)), interpolation=cv2.INTER_AREA)
        out = cv2.resize(small, (k.w, k.h), interpolation=cv2.INTER_LINEAR)
    return out


def aberasi(k, geser=2):
    """Aberasi kromatik ringan di tepi (RGB shift) — 1 operasi cv2."""
    if geser < 1:
        return k.a
    out = k.a.copy()
    out[:, geser:, 0] = k.a[:, :-geser, 0]
    out[:, :-geser, 2] = k.a[:, geser:, 2]
    return out


@functools.lru_cache(maxsize=2)
def _vignette():
    h, w = H, W
    yy = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    r = np.sqrt(xx ** 2 + yy ** 2) / math.sqrt(2)
    m = 1.0 - 0.30 * np.clip(r, 0, 1) ** 1.9
    return np.repeat(np.clip(m * 255, 0, 255).astype(np.uint8)[..., None], 3, axis=2)


def grade_lut(kontras=1.055, saturasi=1.05, lift=(3, 4, 8), gamma=1.005,
              teal=(1, 1, 2), orange=(2, 0, -3)):
    """LUT filmis: S-curve halus + lift warna dingin di bayangan."""
    x = np.arange(256, dtype=np.float32) / 255.0
    y = np.clip((x - 0.5) * kontras + 0.5, 0, 1) ** gamma
    lut = np.zeros((1, 256, 3), np.uint8)
    for c in range(3):
        v = y * 255 + lift[c]
        lut[0, :, c] = np.clip(v, 0, 255).astype(np.uint8)
    # saturasi + tint sumbu (teal/orange) di ruang kasar
    lut[0, :, 0] = np.clip(lut[0, :, 0].astype(np.float32) + orange[0] * (x ** 2), 0, 255)
    lut[0, :, 2] = np.clip(lut[0, :, 2].astype(np.float32) + teal[2] * (1 - x) ** 2 * 2, 0, 255)
    return lut


@functools.lru_cache(maxsize=1)
def grain_plates(n=8, kuat=2.0, seed=5):
    """Lempeng grain uint8 positif & negatif (bukan float32 — 2 ms vs 15 ms)."""
    pos, neg = [], []
    for i in range(n):
        r = rng(seed + i * 17)
        g = r.normal(0, kuat, (H, W, 1))
        pos.append(np.repeat(np.clip(g, 0, 255).astype(np.uint8), 3, axis=2))
        neg.append(np.repeat(np.clip(-g, 0, 255).astype(np.uint8), 3, axis=2))
    return pos, neg


def finishing(k, t, lut=None, vignette=True, grain=(2.0, 5), aberasi_px=0):
    """Rangkaian akhir semua frame: LUT -> vignette -> aberasi -> grain."""
    out = cv2.LUT(k.a, lut) if lut is not None else k.a
    if vignette:
        out = cv2.multiply(out, _vignette(), scale=1.0 / 255.0)
    if aberasi_px >= 1:
        out = aberasi(_KanvasDari(out), aberasi_px)
    if grain:
        kuat, seed = grain
        pos, neg = grain_plates(int(os.environ.get('KT_GRAIN_FRAMES', 6)), kuat, seed)
        i = int(t * 14.0) % len(pos)
        out = cv2.subtract(cv2.add(out, pos[i]), neg[i])
    return out


class _KanvasDari:
    """Pembungkus ringan supaya fungsi yang butuh `Kanvas` bisa memakai array."""
    __slots__ = ("a", "h", "w")

    def __init__(self, a):
        self.a = a
        self.h, self.w = a.shape[:2]


# ============================================================== 9. SELFTEST

def _selftest():
    t0 = time.time()
    k = Kanvas(W, H)
    latar_jatuh(k)
    print(f"latar_jatuh: {(time.time() - t0) * 1000:.0f} ms")

    t0 = time.time()
    k2 = Kanvas(W, H)
    latar_kamar_lengkap(k2)
    print(f"latar_kamar : {(time.time() - t0) * 1000:.0f} ms")

    t0 = time.time()
    for i in range(20):
        kk = object.__new__(Kanvas)
        kk.w, kk.h = W, H
        kk.a = k.a.copy()
        berkas(kk, 300, 0, 1200, 40, 200, (150, 205, 255), 0.16, i * 0.05, 1.1)
        pendar(kk, 540, 700, 300, CYAN, 0.5, 2.2, 0.3)
        panel(kk, 80, 1300, 920, 300, aksen=CYAN)
        caption_spr("KAMU MERASA JATUH TEPAT SEBELUM TIDUR", 3, CYAN)
        caption_karaoke(kk, "KAMU MERASA JATUH TEPAT SEBELUM TIDUR", i * 0.1, 3.0, CYAN)
        grafik_area(kk, 140, 1000, 760, 220, np.linspace(0.9, 0.1, 40), CYAN, i / 20)
        eeg(kk, 140, 300, 760, 120, i * 0.1, VIOLET)
        out = finishing(kk, i * 0.05)
    dt = (time.time() - t0) / 20 * 1000
    print(f"komposisi   : {dt:.2f} ms/frame")
    Image.fromarray(out).save("/tmp/v20_selftest.jpg", quality=92)
    Image.fromarray(k2.a).save("/tmp/v20_kamar.jpg", quality=92)
    print("-> /tmp/v20_selftest.jpg /tmp/v20_kamar.jpg")


if __name__ == "__main__":
    _selftest()
