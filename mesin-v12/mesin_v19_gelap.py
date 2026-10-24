#!/usr/bin/env python3
"""mesin_v19_gelap.py — BAHASA VISUAL SINEMATIK GELAP untuk KlikTahu (v19).

Kenapa modul baru
-----------------
v18 memakai bahasa "kertas krem + ilustrasi terang". Video panjang acuan
KlikTahu (yang dikirim pemilik) memakai bahasa yang sama sekali berbeda:

    latar gelap bergradasi (angkasa / samudra dalam)
    + cahaya volumetrik dari atas
    + debu/partikel berkilau (marine snow)
    + objek ber-rim light (tepi bercahaya, bukan outline tinta)
    + panel kaca tipis dengan border 1 px
    + teks putih + aksen warna (cyan / emas / koral / violet)
    + grafik data berlabel satuan
    + badge babak di kanan atas, bar progres di tepi bawah
    + pill caption berwarna dengan garis tepi menyala

Modul ini menyediakan SEMUA bahan itu. Yang dipertahankan dari v18: mesin
raster cepat (sprite sekali + blit kotak lokal + `np.take` untuk gerak), karena
kecepatan tidak boleh dikorbankan untuk kualitas.

Prinsip "realistis tapi 2D"
---------------------------
Realisme dibangun dari CAHAYA, bukan dari detail objek:
  1. gradient fill (bukan warna datar)  -> volume
  2. rim light + specular highlight     -> bentuk terbaca di latar gelap
  3. atmospheric haze + DOF pada objek jauh -> kedalaman
  4. god rays + caustic + glow          -> sumber cahaya konsisten
  5. grain + vignette + chromatic hint  -> terasa "direkam", bukan digambar
  6. bayangan kontak di bawah objek     -> objek menyentuh bidangnya

Semua fungsi di sini menerima `Kanvas` (dari mesin_v18_inti) atau mengembalikan
sprite RGBA. Tidak ada I/O berkas.

Selftest: python3 mesin_v19_gelap.py
"""
from __future__ import annotations

import functools
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import mesin_v18_inti as M
import mesin_v18_dunia as D18
from mesin_v18_inti import (F_BOLD, F_MED, F_REG, F_SEMI, Kanvas, Pena, blit,
                            blit_add, blit_c, catmull, clamp, eio, eo, gblur,
                            lerp, mask, mix, pangkas, raster, rng, smooth,
                            spr_text, tw)

W_, H_ = 1080, 1920

# ============================================================== 1. PALET

BG_0 = (6, 9, 20)          # paling gelap (pojok)
BG_1 = (10, 15, 32)
BG_2 = (16, 23, 48)
BG_3 = (23, 32, 64)        # puncak gradasi (langit)
NEBULA_A = (42, 58, 122)   # biru indigo
NEBULA_B = (86, 48, 108)   # ungu samar
NEBULA_C = (24, 84, 96)    # teal samar

CYAN = (86, 204, 242)
CYAN_L = (150, 232, 255)
GOLD = (247, 193, 72)
GOLD_L = (255, 220, 140)
CORAL = (240, 98, 92)
CORAL_L = (255, 158, 150)
VIOLET = (176, 132, 250)
GREEN = (94, 226, 168)
BLUE = (92, 148, 255)

TEKS = (240, 244, 252)
TEKS_2 = (176, 187, 210)
TEKS_3 = (120, 132, 158)

PANEL_FILL = (255, 255, 255, 14)
PANEL_FILL_2 = (255, 255, 255, 8)
PANEL_LINE = (255, 255, 255, 40)

# ============================================================== 2. LATAR

_STAR_CACHE = {}


def _bintang_lapisan(w, h, n, seed, rmin=0.6, rmax=1.9, kolom=(255, 255, 255)):
    """Satu lapisan bintang: titik kecil dengan terang bervariasi + halo halus."""
    r = rng(seed)
    spr = np.zeros((h, w, 4), np.uint8)
    ys = r.integers(0, h, n)
    xs = r.integers(0, w, n)
    rr = r.uniform(rmin, rmax, n)
    al = (r.uniform(0.25, 1.0, n) ** 1.7 * 255).astype(np.uint8)
    for i in range(n):
        y, x, rad, a = int(ys[i]), int(xs[i]), float(rr[i]), int(al[i])
        if rad < 1.0:
            spr[y, x, :3] = kolom
            spr[y, x, 3] = max(spr[y, x, 3], a)
        else:
            cv2.circle(spr, (x, y), int(round(rad)), (*kolom, a), -1, cv2.LINE_AA)
    return spr


def bintang(k, n=520, seed=7, y0=0, y1=None, redup=1.0):
    """Taburkan bintang: tiga lapisan (kecil banyak, sedang, besar bercahaya)."""
    y1 = H_ if y1 is None else y1
    h = int(y1 - y0)
    lap = [(int(n * 0.72), 1.2, 0.35), (int(n * 0.22), 2.2, 1.1), (int(n * 0.06), 3.4, 2.0)]
    for i, (nn, rmax, glow) in enumerate(lap):
        spr = _bintang_lapisan(k.w, h, max(1, nn), seed + i * 31, 0.7, rmax)
        spr[..., 3] = (spr[..., 3].astype(np.float32) * redup).astype(np.uint8)
        blit_add(k.a, spr, 0, y0)
        # halo untuk lapisan besar
        if glow > 1.5:
            hz = gblur(spr[..., 3], 2.2)
            halo = np.zeros_like(spr)
            halo[..., :3] = (210, 230, 255)
            halo[..., 3] = (hz.astype(np.float32) * 0.55).astype(np.uint8)
            blit_add(k.a, halo, 0, y0)


def nebula(k, y0=0, y1=None, kuat=1.0, seed=3):
    """Awan nebula: fBm diwarnai tiga arah, di-blend ADD agar terasa cahaya."""
    y1 = H_ if y1 is None else y1
    h = int(y1 - y0)
    w = k.w
    f = M.fbm(h, w, scale=260, octaves=5, seed=seed)
    g = M.fbm(h, w, scale=340, octaves=4, seed=seed + 11)
    lap = np.zeros((h, w, 4), np.uint8)
    a = np.clip((f - 0.42) * 2.6, 0, 1) ** 1.5
    b = np.clip((g - 0.48) * 2.4, 0, 1) ** 1.6
    col = np.zeros((h, w, 3), np.float32)
    col += np.array(NEBULA_A, np.float32) * a[:, :, None]
    col += np.array(NEBULA_B, np.float32) * b[:, :, None]
    col += np.array(NEBULA_C, np.float32) * (a * b)[:, :, None] * 1.6
    lap[..., :3] = np.clip(col * kuat, 0, 255).astype(np.uint8)
    lap[..., 3] = np.clip((a * 0.55 + b * 0.45) * 255 * kuat, 0, 255).astype(np.uint8)
    lap[..., :3] = gblur(lap[..., :3], 9)
    blit_add(k.a, lap, 0, y0)


def latar_gelap(k, y0=0, y1=None, bintang_n=520, nebula_kuat=1.0, seed=5,
                gradasi=None):
    """Latar dasar sinematik: gradasi vertikal + nebula + bintang."""
    y1 = H_ if y1 is None else y1
    gradasi = gradasi or [(0.0, BG_3), (0.35, BG_2), (0.72, BG_1), (1.0, BG_0)]
    k.gradasi_v(y0, y1, gradasi, seed=seed, dither=1.06)
    nebula(k, y0, y1, nebula_kuat, seed=seed + 2)
    bintang(k, bintang_n, seed=seed + 5, y0=y0, y1=y1)


def kedalaman_air(k, y0=0, y1=H_, puncak=(18, 34, 62), dasar=(4, 8, 18)):
    """Gradasi 'samudra dalam': terang di atas (cahaya masuk), hitam di bawah."""
    k.gradasi_v(y0, y1, [(0.0, puncak), (0.28, mix(puncak, dasar, 0.35)),
                         (0.66, mix(puncak, dasar, 0.78)), (1.0, dasar)], seed=23)


def kabut_bawah(k, y0, y1, warna=(12, 20, 40), kuat=0.85):
    """Kabut tebal di dasar frame: menyembunyikan ujung objek (kedalaman)."""
    y0, y1 = int(y0), min(int(y1), k.h)
    if y1 <= y0:
        return
    h = y1 - y0
    a = (np.linspace(0, 1, h, dtype=np.float32) ** 1.5 * kuat)[:, None]
    reg = k.a[y0:y1].astype(np.float32)
    reg += (np.array(warna, np.float32) - reg) * a[:, :, None]
    k.a[y0:y1] = np.clip(reg, 0, 255).astype(np.uint8)


# ============================================================== 3. CAHAYA

_GLOW_CACHE = {}


def glow_spr(r, warna=CYAN, kuat=1.0, keras=2.0, inti=0.0):
    """Sprite pendar radial (cache). `keras` mengatur sebaran; `inti` menambah titik terang."""
    key = (int(r), tuple(warna[:3]), round(kuat, 2), round(keras, 2), round(inti, 2))
    s = _GLOW_CACHE.get(key)
    if s is not None:
        return s
    rr = int(r)
    yy = np.arange(-rr, rr + 1, dtype=np.float32)[:, None]
    xx = np.arange(-rr, rr + 1, dtype=np.float32)[None, :]
    d = np.sqrt(xx * xx + yy * yy) / max(1.0, rr)
    a = np.clip(1.0 - d, 0, 1) ** keras
    if inti > 0:
        a = np.clip(a + np.clip(1.0 - d * 3.2, 0, 1) ** 1.6 * inti, 0, 1)
    out = np.zeros((2 * rr + 1, 2 * rr + 1, 4), np.uint8)
    out[..., :3] = warna[:3]
    out[..., 3] = np.clip(a * 255 * kuat, 0, 255).astype(np.uint8)
    _GLOW_CACHE[key] = out
    return out


def pendar(k, cx, cy, r, warna=CYAN, kuat=0.8, keras=2.0, inti=0.0):
    """Tempel pendar additif (dipakai untuk cahaya, bukan hiasan)."""
    blit_add(k.a, glow_spr(r, warna, kuat, keras, inti), cx - r, cy - r)


def berkas_atas(k, t=0.0, n=5, y0=0, y1=None, warna=(150, 210, 255), kuat=0.16,
                lebar=(30, 90), miring=0.22):
    """Berkas cahaya dari atas (god ray): sprite gradasi alpha, bergeser halus."""
    y1 = H_ if y1 is None else y1
    h = int(min(y1 - y0, 1500))
    r = rng(4242)
    for i in range(n):
        cx = (i + 0.5) / n * k.w + r.uniform(-50, 50)
        wt = r.uniform(*lebar)
        wb = wt * r.uniform(2.4, 4.2)
        ay = int(h * r.uniform(0.55, 1.0))
        HH = ay
        WW = int(wb * 2 + 80)
        yy = np.linspace(0, 1, HH, dtype=np.float32)[:, None]
        ww = (wt + (wb - wt) * yy) / 2
        xx = np.arange(WW, dtype=np.float32)[None, :] - WW / 2
        xx = xx - yy * WW * miring * 0.30
        dd = np.abs(xx) / np.maximum(ww, 1)
        prof = np.clip(1.0 - dd, 0, 1) ** 2.4
        vert = (1.0 - yy) ** 1.5
        a = np.clip(prof * vert * kuat * 255, 0, 255).astype(np.uint8)
        spr = np.zeros((HH, WW, 4), np.uint8)
        spr[..., :3] = warna
        spr[..., 3] = gblur(a, 11)
        drift = math.sin(t * 0.16 + i * 1.9) * 18
        blit_add(k.a, spr, int(cx - WW / 2 + drift), int(y0))


def sorot_spot(k, cx, cy, r, warna=GOLD, kuat=0.55, sudut=-90, sebar=38):
    """Kerucut lampu sorot dari atas (museum / panggung)."""
    h = int(r * 1.9)
    WW = int(r * 2.6)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    ww = r * 0.12 + r * 0.92 * yy ** 1.15
    xx = np.arange(WW, dtype=np.float32)[None, :] - WW / 2
    d = np.abs(xx) / np.maximum(ww, 1)
    prof = np.clip(1 - d, 0, 1) ** 1.8
    vert = (1 - yy * 0.55) ** 1.2
    a = np.clip(prof * vert * kuat * 255, 0, 255).astype(np.uint8)
    spr = np.zeros((h, WW, 4), np.uint8)
    spr[..., :3] = warna
    spr[..., 3] = gblur(a, 13)
    blit_add(k.a, spr, int(cx - WW / 2), int(cy - h))
    # kolam cahaya di lantai
    pendar(k, cx, cy, int(r * 0.9), warna, kuat * 0.55, 2.4)


def kilau_kaustik(k, t, y0, y1, warna=(120, 200, 255), kuat=0.10):
    """Pita kaustik halus (cahaya air) — dipakai di scene bawah laut."""
    tile = D18.kaustik_spr(512, 7, 0.45)
    D18.kaustik_dasar(k, tile, t, y0, y1, kuat)


# ============================================================== 4. UI PANEL

@functools.lru_cache(maxsize=128)
def panel_spr(w, h, radius=28, fill=PANEL_FILL, garis=PANEL_LINE,
              aksen=None, tebal_aksen=3, kilau=True, dasi=True):
    """Panel kaca: isi transparan, border 1-2 px, sapuan cahaya di tepi atas.

    Ini elemen yang membuat grafik terasa "UI sinematik" seperti referensi,
    bukan kotak kertas.
    """
    w, h = int(w), int(h)
    pad = 3
    W, H = w + pad * 2, h + pad * 2
    out = np.zeros((H, W, 4), np.uint8)

    def g(p):
        p.rrect(0, 0, w, h, radius, fill=fill, outline=None)
    isi = raster(w, h, g, ss=3)
    # sapuan atas: sedikit lebih terang
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    sheen = np.clip(1 - ys / 0.55, 0, 1) ** 1.4
    m = isi[..., 3].astype(np.float32) / 255.0
    add = (sheen * 10 * m).astype(np.uint8)
    isi[..., :3] = np.clip(isi[..., :3].astype(np.int16) + add[:, :, None], 0, 255).astype(np.uint8)
    blit(out, isi, pad, pad)

    def g2(p):
        p.rrect(0, 0, w, h, radius, outline=garis, width=1.6)
    blit(out, raster(w, h, g2, ss=3), pad, pad)

    if aksen is not None:
        def g3(p):
            p.rrect(0, 0, 6, h * 0.34, 3, fill=aksen)
        blit(out, raster(6, int(h * 0.34) + 2, g3, ss=3), pad, pad + int(h * 0.12))
    return out


def panel(k, x, y, w, h, alpha=1.0, **kw):
    s = panel_spr(int(w), int(h), **kw)
    blit(k.a, s, x - 3, y - 3, alpha)
    return s


def pill_spr(teks, warna=CYAN, isi=None, size=34, pad_x=26, pad_y=14,
             radius=None, name=F_SEMI, glow=0.55, ikon=True, tebal=2.2):
    """Pill caption berwarna (gaya referensi: teks berwarna + border menyala)."""
    f = size
    tw_ = tw(teks, name, f)
    w = int(tw_ + pad_x * 2 + (26 if ikon else 0))
    h = int(f * 1.62 + pad_y * 0.4)
    radius = h / 2 if radius is None else radius
    isi = isi if isi is not None else (10, 14, 26, 168)

    def g(p):
        p.rrect(0, 0, w, h, radius, fill=isi, outline=(*warna[:3], 235), width=tebal)
    spr = raster(w, h, g, ss=3)
    m = mask(teks, name, f)
    hh, ww = m.shape
    t = np.zeros((hh, ww, 4), np.uint8)
    t[..., :3] = warna[:3]
    t[..., 3] = m
    blit(spr, t, pad_x + (24 if ikon else 0) + (w - (pad_x * 2 + (24 if ikon else 0)) - ww) / 2,
         (h - hh) / 2 - 2)
    if ikon:
        # titik kecil bercahaya di kiri (penanda kategori)
        pendar_s = glow_spr(12, warna, 0.9, 2.0, 0.5)
        blit(spr, pendar_s, pad_x - 2, h / 2 - 12)
    return spr


@functools.lru_cache(maxsize=96)
def teks_pendar(teks, warna=TEKS, size=64, name=F_BOLD, pendar_warna=None,
                pendar_kuat=0.55, pendar_r=14, tracking=-0.5, blur=10):
    """Teks + pendar lembut di belakangnya (dua sprite; gambar glow lalu teks)."""
    gl_c = pendar_warna or warna
    m = mask(teks, name, size, tracking)
    hh, ww = m.shape
    pad = int(pendar_r * 2.4)
    glow = np.zeros((hh + pad * 2, ww + pad * 2), np.uint8)
    glow[pad:pad + hh, pad:pad + ww] = m
    glow = gblur(glow, blur)
    gs = np.zeros((glow.shape[0], glow.shape[1], 4), np.uint8)
    gs[..., :3] = gl_c[:3]
    gs[..., 3] = np.clip(glow.astype(np.float32) * pendar_kuat * 1.6, 0, 255).astype(np.uint8)
    ts = np.zeros((hh + pad * 2, ww + pad * 2, 4), np.uint8)
    ts[..., :3] = warna[:3]
    ts[..., 3] = 0
    ts[pad:pad + hh, pad:pad + ww, 3] = m
    return gs, ts, pad


def tulis_pendar(k, teks, x, y, warna=TEKS, size=64, name=F_BOLD, alpha=1.0, **kw):
    gs, ts, pad = teks_pendar(teks, warna, size, name, **kw)
    blit_add(k.a, gs, x - pad, y - pad, alpha)
    blit(k.a, ts, x - pad, y - pad, alpha)
    return ts.shape[1] - pad * 2, ts.shape[0] - pad * 2


def label_kecil(teks, warna=TEKS_2, size=26, name=F_MED, tracking=1.2):
    """Label mikro huruf besar berspasi (kicker, satuan, sumber)."""
    return spr_text(teks.upper(), warna, name, size, tracking=tracking)


def badge_babak(teks, warna=CYAN, size=24, nomor="01"):
    """Badge kanan atas: titik berwarna + nomor babak + judul babak."""
    teks = teks.upper()
    f = size
    tw_ = tw(f"{nomor}  ·  {teks}", F_SEMI, f)
    w = int(tw_ + 74)
    h = int(f * 1.9)
    def g(p):
        p.rrect(0, 0, w, h, h / 2, fill=(8, 12, 24, 150),
                outline=(255, 255, 255, 46), width=1.4)
    spr = raster(w, h, g, ss=3)
    pendar_s = glow_spr(9, warna, 0.95, 2.0, 0.65)
    blit(spr, pendar_s, 18, h / 2 - 9)
    t = np.zeros((mask(f"{nomor}  ·  {teks}", F_SEMI, f).shape[0],
                  mask(f"{nomor}  ·  {teks}", F_SEMI, f).shape[1], 4), np.uint8)
    m = mask(f"{nomor}  ·  {teks}", F_SEMI, f)
    t[..., :3] = TEKS
    t[..., 3] = m
    blit(spr, t, 38, (h - m.shape[0]) / 2 - 1)
    return spr


def merek(teks="KlikTahu", size=34, warna=TEKS, warna_ikon=GOLD):
    """Merek kiri atas: belah ketupat kecil + nama kanal (gaya referensi)."""
    m = mask(teks, F_SEMI, size)
    w = int(m.shape[1] + 46)
    h = int(size * 1.8)
    spr = np.zeros((h, w, 4), np.uint8)
    cx, cy = 14, h / 2
    d = 9
    def g(p):
        p.poly([(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)], fill=warna_ikon)
    blit(spr, raster(28, 28, g, ss=3), 0, int(cy - 14))
    t = np.zeros((m.shape[0], m.shape[1], 4), np.uint8)
    t[..., :3] = warna
    t[..., 3] = m
    blit(spr, t, 32, (h - m.shape[0]) / 2 - 1)
    return spr


def progres_bawah(k, frac, warna=CYAN, tinggi=5, segmen=8, aktif=None,
                  y=None, x0=0, x1=None):
    """Bar progres di tepi bawah: segmen tipis, segmen lewat berwarna, sisanya redup."""
    y = (k.h - tinggi - 6) if y is None else y
    x1 = k.w if x1 is None else x1
    lebar = (x1 - x0) / segmen
    for i in range(segmen):
        a0 = x0 + i * lebar + 2
        a1 = a0 + lebar - 4
        kalau_lewat = i < (aktif if aktif is not None else 0)
        if i == (aktif if aktif is not None else 0):
            c = warna
            al = 0.95
        elif kalau_lewat:
            c = mix(GOLD, CYAN, 0.35)
            al = 0.75
        else:
            c = (255, 255, 255)
            al = 0.14
        cv2.line(k.a, (int(a0), int(y + tinggi / 2)), (int(a1), int(y + tinggi / 2)),
                 c, tinggi, cv2.LINE_AA)
    # kepala progres halus di dalam segmen aktif
    if aktif is not None:
        a0 = x0 + aktif * lebar + 2
        a1 = a0 + (lebar - 4) * clamp(frac)
        cv2.line(k.a, (int(a0), int(y + tinggi / 2)), (int(max(a0, a1)), int(y + tinggi / 2)),
                 warna, tinggi, cv2.LINE_AA)


# ============================================================== 5. GRAFIK DATA

def bar_chart(k, x, y, w, baris, alpha=1.0, tinggi_bar=34, jarak=56,
              label_w=250, anim=1.0, ukuran_label=30):
    """Grafik batang berlabel (nama + nilai + satuan), gaya referensi.

    `baris` = [(nama, nilai 0..1, teks_nilai, warna), ...]
    """
    for i, (nama, v, teks, warna) in enumerate(baris):
        yy = y + i * jarak
        # nama
        nm = spr_text(nama, warna, F_SEMI, ukuran_label)
        blit(k.a, nm, x, yy + (tinggi_bar - nm.shape[0]) / 2, alpha)
        # lintasan redup
        trk_x0 = x + label_w
        trk_x1 = x + w
        cv2.line(k.a, (int(trk_x0), int(yy + tinggi_bar / 2)),
                 (int(trk_x1), int(yy + tinggi_bar / 2)),
                 mix(TEKS_3, BG_2, 0.45), tinggi_bar, cv2.LINE_AA)
        # batang
        ww = max(0.0, (trk_x1 - trk_x0) * clamp(v * anim))
        if ww > 4:
            x0, x1 = int(trk_x0), int(trk_x0 + ww)
            y0, y1 = int(yy), int(yy + tinggi_bar)
            reg = k.a[y0:y1, x0:x1].astype(np.float32)
            grad = np.linspace(0, 1, x1 - x0, dtype=np.float32)[None, :, None]
            c1 = np.array(warna[:3], np.float32)
            c2 = np.array(mix(warna, (255, 255, 255), 0.42)[:3], np.float32)
            base = c1 * (1 - grad) + c2 * grad
            reg += (base - reg) * (alpha * 0.92)
            k.a[y0:y1, x0:x1] = np.clip(reg, 0, 255).astype(np.uint8)
            # ujung menyala
            pendar(k, x1, (y0 + y1) // 2, 26, warna, 0.35 * alpha, 2.2)
        # nilai: di kanan batang kalau muat, kalau tidak di dalam batang
        if teks:
            vs = spr_text(teks, TEKS, F_SEMI, ukuran_label - 2)
            lebar_teks = vs.shape[1]
            sisa = (x + w) - (trk_x0 + ww)
            if ww > 4 and sisa < lebar_teks + 24:
                tx = x + w - lebar_teks - 16
                vs2 = np.array(vs, copy=True)
                vs2[..., :3] = mix(TEKS, BG_0, 0.72)
                blit(k.a, vs2, tx, yy + (tinggi_bar - vs.shape[0]) / 2, alpha * 0.95)
            elif ww > 4:
                blit(k.a, vs, trk_x0 + ww + 14, yy + (tinggi_bar - vs.shape[0]) / 2, alpha)
            else:
                blit(k.a, vs, trk_x0 + 14, yy + (tinggi_bar - vs.shape[0]) / 2, alpha)


def garis_tren(k, x0, y0, x1, y1, warna=CORAL, tebal=6, alpha=1.0, titik=True,
               anim=1.0, bayang=True):
    """Garis tren menurun/naik dengan ujung menyala + area di bawahnya."""
    n = max(2, int(abs(x1 - x0) / 12))
    xs = np.linspace(x0, x1, n)
    ys = np.linspace(y0, y1, n)
    ys = ys + np.sin(np.linspace(0, 2.2, n)) * (y1 - y0) * 0.045
    k_n = max(2, int(n * clamp(anim)))
    xs, ys = xs[:k_n], ys[:k_n]
    pts = np.array([[int(a), int(b)] for a, b in zip(xs, ys)], np.int32)
    if bayang and len(pts) > 2:
        area = np.vstack([pts, [[int(xs[-1]), int(y1 + 40)], [int(xs[0]), int(y1 + 40)]]])
        lap = np.zeros_like(k.a)
        cv2.fillPoly(lap, [area], warna)
        lap = gblur(lap.astype(np.float32), 26)
        k.a = np.clip(k.a.astype(np.float32) + lap * 0.12 * alpha, 0, 255).astype(np.uint8)
    cv2.polylines(k.a, [pts], False, warna, tebal, cv2.LINE_AA)
    if titik and len(pts):
        pendar(k, int(xs[-1]), int(ys[-1]), 26, warna, 0.7 * alpha, 2.0, 0.35)


def garis_pandu(k, titik, teks, warna=TEKS, arah="kanan", size=28, alpha=1.0,
                anim=1.0, jarak=26):
    """Garis pandu (leader line) dari objek ke label — khas diagram sinematik."""
    tx, ty = titik
    pw = tw(teks, F_SEMI, size)
    if arah == "kanan":
        x1, x2 = tx + jarak, tx + jarak + 60
        y2 = ty - 34
        x3 = x2 + pw + 18
    else:
        x1, x2 = tx - jarak, tx - jarak - 60
        y2 = ty - 34
        x3 = x2 - pw - 18
    a = clamp(anim)
    # garis patah bertahap
    p1 = (int(lerp(tx, x1, min(1, a * 2))), int(ty))
    p2 = (int(lerp(x1, x2, max(0, min(1, a * 2 - 1)))), int(lerp(ty, y2, max(0, min(1, a * 2 - 1)))))
    cv2.line(k.a, (int(tx), int(ty)), p1, (*warna[:3], 200), 2, cv2.LINE_AA)
    if a > 0.5:
        cv2.line(k.a, p1, p2, (*warna[:3], 200), 2, cv2.LINE_AA)
    if a > 0.95:
        cv2.circle(k.a, (int(tx), int(ty)), 5, warna, -1, cv2.LINE_AA)
        cv2.circle(k.a, (int(p1[0]), int(p1[1])), 3, warna, -1, cv2.LINE_AA)
        blit(k.a, spr_text(teks, warna, F_SEMI, size),
             (x2 + 8) if arah == "kanan" else (x2 - pw - 8), y2 - size * 0.9, alpha)


def stat_besar(k, nilai, satuan, label, x, y, warna=GOLD, size=190, alpha=1.0,
               anim=1.0, rata="kiri", label_warna=None):
    """Angka besar + satuan + label kecil (pola utama referensi)."""
    vs = spr_text(nilai, warna, F_BOLD, size, tracking=-6)
    us = spr_text(satuan.upper(), mix(warna, (255, 255, 255), 0.45), F_SEMI, 46, tracking=2)
    ls = label_kecil(label, label_warna or TEKS_3, 26)
    total_w = max(vs.shape[1], us.shape[1], ls.shape[1])
    x0 = x if rata != "tengah" else x - total_w / 2
    blit_add(k.a, glow_spr(int(size * 0.62), warna, 0.20 * alpha * anim, 2.2),
             x0 + vs.shape[1] / 2 - size * 0.62, y + vs.shape[0] / 2 - size * 0.62)
    blit(k.a, vs, x0, y + (1 - eo(anim)) * 26, alpha)
    if anim > 0.4:
        blit(k.a, us, x0 + 6, y + vs.shape[0] - 18, alpha * eo((anim - 0.4) / 0.6))
        blit(k.a, ls, x0 + 8, y + vs.shape[0] + 46, alpha * eo((anim - 0.4) / 0.6))
    return total_w


def kartu_data(k, x, y, w, h, judul, nilai, satuan, warna=CYAN, alpha=1.0,
               anim=1.0, ikon=None):
    """Kartu data kecil: judul mikro, angka, satuan; border kiri berwarna."""
    panel(k, x, y, w, h, alpha=alpha, aksen=warna, radius=22)
    blit(k.a, label_kecil(judul, TEKS_3, 24), x + 26, y + 22, alpha)
    n = spr_text(nilai, warna, F_BOLD, 76, tracking=-3)
    blit(k.a, n, x + 24, y + 56, alpha * eo(anim))
    if satuan:
        blit(k.a, spr_text(satuan, TEKS_2, F_MED, 26), x + 28, y + 56 + n.shape[0] - 6, alpha)


# ============================================================== 6. IKON

def ikon(nama, ukuran=90, warna=CYAN, tebal=5.0):
    """Ikon garis sederhana (konsisten tebal) untuk kartu sebab/gejala."""
    s = ukuran
    pad = 8

    def g(p):
        c = warna
        if nama == "salju":
            for i in range(3):
                a = i * math.pi / 3
                p.line([(s / 2 - math.cos(a) * s * 0.42, s / 2 - math.sin(a) * s * 0.42),
                        (s / 2 + math.cos(a) * s * 0.42, s / 2 + math.sin(a) * s * 0.42)],
                       c, tebal)
        elif nama == "gelombang":
            for k2 in range(3):
                yy = s * (0.30 + k2 * 0.20)
                pts = [(s * (0.12 + 0.76 * i / 20),
                        yy + math.sin(i / 20 * 2 * math.pi * 1.5) * s * 0.06) for i in range(21)]
                p.line(pts, c, tebal)
        elif nama == "paus":
            p.ell(s * 0.10, s * 0.34, s * 0.74, s * 0.70, outline=c, width=tebal)
            p.poly([(s * 0.74, s * 0.52), (s * 0.94, s * 0.36), (s * 0.94, s * 0.62)], outline=c, width=tebal)
        elif nama == "hiu":
            p.poly([(s * 0.08, s * 0.52), (s * 0.34, s * 0.34), (s * 0.62, s * 0.40),
                    (s * 0.86, s * 0.30), (s * 0.94, s * 0.50), (s * 0.62, s * 0.62),
                    (s * 0.26, s * 0.66)], outline=c, width=tebal)
        elif nama == "termometer":
            p.rrect(s * 0.44, s * 0.12, s * 0.56, s * 0.62, s * 0.06, outline=c, width=tebal)
            p.circ(s * 0.50, s * 0.72, s * 0.13, outline=c, width=tebal)
            p.line([(s * 0.50, s * 0.34), (s * 0.50, s * 0.64)], c, tebal * 1.4)
        elif nama == "gigi":
            p.poly([(s * 0.22, s * 0.24), (s * 0.78, s * 0.24), (s * 0.62, s * 0.80),
                    (s * 0.50, s * 0.62), (s * 0.38, s * 0.80)], outline=c, width=tebal)
        elif nama == "bumi":
            p.circ(s / 2, s / 2, s * 0.36, outline=c, width=tebal)
            p.arc(s * 0.20, s * 0.26, s * 0.80, s * 0.74, 20, 160, c, tebal * 0.8)
            p.arc(s * 0.22, s * 0.40, s * 0.78, s * 0.86, 200, 340, c, tebal * 0.8)
        elif nama == "waktu":
            p.circ(s / 2, s / 2, s * 0.38, outline=c, width=tebal)
            p.line([(s / 2, s / 2), (s / 2, s * 0.26)], c, tebal)
            p.line([(s / 2, s / 2), (s * 0.66, s * 0.58)], c, tebal)
        elif nama == "ukuran":
            p.line([(s * 0.14, s * 0.70), (s * 0.86, s * 0.70)], c, tebal)
            p.line([(s * 0.14, s * 0.58), (s * 0.14, s * 0.82)], c, tebal)
            p.line([(s * 0.86, s * 0.58), (s * 0.86, s * 0.82)], c, tebal)
            p.line([(s * 0.30, s * 0.28), (s * 0.70, s * 0.28)], c, tebal * 0.8)
        else:
            p.circ(s / 2, s / 2, s * 0.34, outline=c, width=tebal)
    return raster(s + pad * 2, s + pad * 2, g, ss=3)


def panah_glow(panjang=170, warna=CYAN, tebal=8, kepala=20):
    W = int(panjang + kepala * 2)
    H = int(kepala * 3)
    def g(p):
        y = H / 2
        p.line([(4, y), (panjang, y)], warna, tebal)
        p.poly([(panjang - 2, y - kepala), (panjang + kepala * 1.6, y), (panjang - 2, y + kepala)],
               fill=warna)
    spr = raster(W, H, g, ss=3)
    return spr


# ============================================================== 7. MAKHLUK (rim light)

def _rim(mask_arr, arah=(-1, -1), radius=3.0, kekuatan=0.85, warna=CYAN_L):
    """Cincin cahaya di tepi siluet, berasal dari satu arah (rim light).

    Dicari dari gradien mask: piksel tepi yang menghadap sumber cahaya diberi
    warna terang. Ini yang membuat siluet gelap tetap terbaca di latar gelap.
    """
    m = (mask_arr > 60).astype(np.float32)
    # gradien tepi
    gx = cv2.Sobel(m, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(m, cv2.CV_32F, 0, 1, ksize=3)
    dx, dy = arah
    hadap = -(gx * dx + gy * dy)
    hadap = np.clip(hadap, 0, None)
    hadap = np.clip(hadap / (hadap.max() + 1e-6), 0, 1)
    rim = gblur((hadap * m * 255).astype(np.uint8), radius)
    rim = (rim.astype(np.float32) * kekuatan).astype(np.uint8)
    out = np.zeros((mask_arr.shape[0], mask_arr.shape[1], 4), np.uint8)
    out[..., :3] = warna
    out[..., 3] = rim
    return out


def hiu_gelap(L=900, macam="megalodon", warna=(26, 46, 64), perut=(104, 140, 166),
              rim_warna=CYAN_L, rim_kuat=1.0, gigi=True, skala_outline=0.0):
    """Hiu sinematik: badan bergradasi + rim light menyala + mata & gigi bercahaya.

    Pelajaran dari uji pertama: kalau gradasi diterapkan pada SELURUH sprite,
    sirip punggung melebur dengan badan dan siluetnya hilang di latar gelap.
    Solusinya: gradasi hanya pada badan (mask badan), sirip diberi warna sendiri
    yang lebih gelap, lalu rim light dipasang pada SELURUH siluet (termasuk
    sirip) supaya bentuknya terbaca.
    """
    Hc = L * 0.38
    W = int(L * 1.18)
    H = int(L * 0.70)
    cx0, cy0 = L * 0.10, H * 0.50
    top, bot = D18._profil_hiu(macam)

    def x_of(u):
        return cx0 + u * L

    def y_of(v):
        return cy0 + (v - 0.44) * Hc

    fin_terang = mix(warna, (130, 178, 208), 0.28)
    fin_gelap = mix(warna, (0, 0, 0), 0.20)

    def g(p):
        ek = [(x_of(0.135), y_of(0.46)), (x_of(0.010), y_of(0.10)),
              (x_of(0.075), y_of(0.455)), (x_of(0.018), y_of(0.80)),
              (x_of(0.135), y_of(0.545))]
        p.poly(catmull(ek, 7, closed=True), fill=fin_gelap)
        punggung = [(x_of(0.555), y_of(0.16)), (x_of(0.60), y_of(-0.30)),
                    (x_of(0.655), y_of(-0.05)), (x_of(0.715), y_of(0.16))]
        p.poly(catmull(punggung, 9, closed=True), fill=mix(fin_terang, warna, 0.35))
        p.poly([(x_of(0.250), y_of(0.235)), (x_of(0.268), y_of(0.085)),
                (x_of(0.318), y_of(0.225))], fill=mix(fin_terang, warna, 0.5))
        dada = [(x_of(0.760), y_of(0.54)), (x_of(0.665), y_of(0.90)),
                (x_of(0.632), y_of(0.93)), (x_of(0.672), y_of(0.70)),
                (x_of(0.716), y_of(0.58))]
        p.poly(catmull(dada, 8, closed=True), fill=mix(fin_terang, perut, 0.45))
        p.poly([(x_of(0.475), y_of(0.755)), (x_of(0.452), y_of(0.875)),
                (x_of(0.522), y_of(0.775))], fill=mix(fin_terang, perut, 0.35))
        p.poly([(x_of(0.335), y_of(0.755)), (x_of(0.318), y_of(0.865)),
                (x_of(0.385), y_of(0.775))], fill=mix(fin_terang, perut, 0.30))
        atas = catmull([(x_of(u), y_of(v)) for u, v in top], n=9)
        bawah = catmull([(x_of(u), y_of(v)) for u, v in bot], n=9)
        p.poly(atas + bawah, fill=warna)
    spr = raster(W, H, g, ss=2)

    mask_badan = mask_poli_safe(W, H, [catmull([(x_of(u), y_of(v)) for u, v in top], n=9) +
                                       catmull([(x_of(u), y_of(v)) for u, v in bot], n=9)])
    seg = mask_badan > 40
    atas_y = np.argmax(seg, axis=0).astype(np.float32)
    bawah_y = (H - 1 - np.argmax(seg[::-1], axis=0)).astype(np.float32)
    tinggi = np.maximum(1.0, bawah_y - atas_y)
    ys = np.arange(H, dtype=np.float32)[:, None]
    t = np.clip((ys - atas_y[None, :]) / tinggi[None, :], 0, 1)

    # 3 pita warna: punggung terang (kena cahaya) -> badan -> perut
    c_top = np.array(mix(warna, (150, 200, 226), 0.55)[:3], np.float32)
    c_mid = np.array(warna[:3], np.float32)
    c_bot = np.array(mix(perut, (0, 0, 0), 0.15)[:3], np.float32)
    tt = t[:, :, None]
    grad = np.where(tt < 0.34,
                    c_top + (c_mid - c_top) * (tt / 0.34),
                    c_mid + (c_bot - c_mid) * np.clip((tt - 0.34) / 0.66, 0, 1))
    a = (mask_badan.astype(np.float32) / 255.0)[:, :, None]
    reg = spr[..., :3].astype(np.float32)
    spr[..., :3] = np.clip(reg * (1 - a) + grad * a, 0, 255).astype(np.uint8)

    # rim pada SELURUH siluet (badan + sirip) -> bentuk terbaca
    sil = spr[..., 3]
    rim = _rim(sil, arah=(0.25, -1.0), radius=2.2, kekuatan=rim_kuat, warna=rim_warna)
    M.komposit(spr, rim)
    rim_b = _rim(sil, arah=(-0.2, 1.0), radius=2.8, kekuatan=0.30, warna=(120, 160, 195))
    M.komposit(spr, rim_b)

    # specular: pita tipis sepanjang punggung
    det = np.zeros((H, W, 4), np.uint8)
    # pita specular: garis tebal -> diblur -> jadi kilau lembut (bukan kawat)
    pita = np.zeros((H, W), np.uint8)
    spec = catmull([(x_of(0.84), y_of(0.285)), (x_of(0.68), y_of(0.180)),
                    (x_of(0.46), y_of(0.160)), (x_of(0.28), y_of(0.235)),
                    (x_of(0.185), y_of(0.330))], n=9)
    cv2.polylines(pita, [np.array([[int(a_), int(b_)] for a_, b_ in spec], np.int32)],
                  False, 255, max(3, int(L * 0.012)), cv2.LINE_AA)
    pita = gblur(pita, max(2.0, L * 0.008))
    det[..., :3] = (196, 236, 255)
    det[..., 3] = (pita.astype(np.float32) * 0.55).astype(np.uint8)
    # mata & gigi
    ex, ey = int(x_of(0.890)), int(y_of(0.380))
    p_s = glow_spr(16, (215, 250, 255), 1.0, 2.0, 0.8)
    _tempel_ke(det, p_s, ex, ey)
    if gigi:
        for i in range(9):
            f = i / 8
            gx = int(lerp(x_of(0.955), x_of(0.850), f))
            gy = int(lerp(y_of(0.500), y_of(0.545), f))
            cv2.line(det, (gx, gy), (gx + 1, gy + int(L * 0.008)),
                     (240, 250, 255, 210), 1, cv2.LINE_AA)
    # insang: busur tipis yang mengumpul ke arah mulut
    for i in range(5):
        u0 = 0.700 - i * 0.022
        busur = catmull([(x_of(u0), y_of(0.275)), (x_of(u0 - 0.004), y_of(0.365)),
                         (x_of(u0 - 0.012), y_of(0.455))], n=5)
        cv2.polylines(det, [np.array([[int(a_), int(b_)] for a_, b_ in busur], np.int32)],
                      False, (145, 200, 232, 96), 2, cv2.LINE_AA)
    det[..., 3] = (det[..., 3].astype(np.uint16) * mask_badan.astype(np.uint16) // 255).astype(np.uint8)
    # mata boleh sedikit keluar mask (pendar)
    M.komposit(spr, det)
    return pangkas(spr)


def _tempel_ke(dst, spr, cx, cy):
    """Tempel sprite (dengan alpha) ke kanvas RGBA di posisi tengah, klip aman."""
    h, w = spr.shape[:2]
    H, W = dst.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x1, y1 = min(W, x0 + w), min(H, y0 + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = spr[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    M.komposit(dst[max(0, y0):y1, max(0, x0):x1], sub)


def _lapis(dst, warna, alpha_mask):
    """Komposit warna solid dengan alpha mask ke RGBA (aman untuk goresan tipis)."""
    lap = np.zeros(dst.shape, np.uint8)
    lap[..., :3] = warna[:3]
    lap[..., 3] = alpha_mask
    return M.komposit(dst, lap)


def mask_poli_safe(w, h, daftar):
    return M.mask_poli(int(w), int(h), daftar, ss=1)


def paus_gelap(L=760, warna=(30, 44, 66), rim_warna=(176, 220, 255), rim_kuat=0.85):
    """Paus sinematik: badan bergradasi (punggung terang -> perut pucat) + rim.

    Seperti `hiu_gelap`, gradasi hanya diterapkan pada mask BADAN; sirip diberi
    warna sendiri supaya siluetnya tidak melebur. Rim dipasang pada seluruh
    sprite (badan + sirip) agar bentuknya terbaca dari cahaya.
    """
    Hc = L * 0.36
    W, H = int(L * 1.26), int(L * 0.52)
    cx0, cy0 = L * 0.14, H * 0.50
    top = [(0.03, 0.46), (0.10, 0.34), (0.24, 0.25), (0.44, 0.20),
           (0.62, 0.19), (0.78, 0.22), (0.90, 0.29), (0.985, 0.40)]
    bot = [(0.985, 0.49), (0.92, 0.60), (0.76, 0.70), (0.56, 0.76),
           (0.36, 0.77), (0.20, 0.72), (0.09, 0.61), (0.03, 0.53)]

    def x_of(u):
        return cx0 + u * L

    def y_of(v):
        return cy0 + (v - 0.44) * Hc

    atas = catmull([(x_of(u), y_of(v)) for u, v in top], n=9)
    bawah = catmull([(x_of(u), y_of(v)) for u, v in bot], n=9)
    sirip = mix(warna, (0, 0, 0), 0.18)

    def g(p):
        fl = [(x_of(0.06), y_of(0.44)), (x_of(-0.115), y_of(0.10)),
              (x_of(-0.045), y_of(0.44)), (x_of(-0.115), y_of(0.78)),
              (x_of(0.065), y_of(0.54))]
        p.poly(catmull(fl, 7, closed=True), fill=sirip)
        p.poly(catmull([(x_of(0.585), y_of(0.22)), (x_of(0.615), y_of(0.04)),
                        (x_of(0.675), y_of(0.24))], 7, closed=True), fill=sirip)
        p.poly(catmull([(x_of(0.715), y_of(0.60)), (x_of(0.585), y_of(0.90)),
                        (x_of(0.650), y_of(0.66))], 7, closed=True), fill=sirip)
        p.poly(atas + bawah, fill=warna)
    spr = raster(W, H, g, ss=2)

    mb = mask_poli_safe(W, H, [atas + bawah])
    seg_ = mb > 40
    atas_y = np.argmax(seg_, axis=0).astype(np.float32)
    bawah_y = (H - 1 - np.argmax(seg_[::-1], axis=0)).astype(np.float32)
    tinggi = np.maximum(1.0, bawah_y - atas_y)
    ys = np.arange(H, dtype=np.float32)[:, None]
    t = np.clip((ys - atas_y[None, :]) / tinggi[None, :], 0, 1)[:, :, None]

    c_top = np.array(mix(warna, (120, 168, 205), 0.62)[:3], np.float32)
    c_mid = np.array(warna[:3], np.float32)
    c_bot = np.array(mix((104, 132, 160), (255, 255, 255), 0.10)[:3], np.float32)
    grad = np.where(t < 0.40, c_top + (c_mid - c_top) * (t / 0.40),
                    c_mid + (c_bot - c_mid) * np.clip((t - 0.40) / 0.60, 0, 1))
    aa = (mb.astype(np.float32) / 255.0)[:, :, None]
    spr[..., :3] = np.clip(spr[..., :3].astype(np.float32) * (1 - aa) + grad * aa, 0, 255).astype(np.uint8)

    sil = spr[..., 3]
    rim = _rim(sil, arah=(0.2, -1.0), radius=2.4, kekuatan=rim_kuat, warna=rim_warna)
    M.komposit(spr, rim)
    rim2 = _rim(sil, arah=(-0.1, 1.0), radius=2.6, kekuatan=0.22, warna=(140, 175, 205))
    M.komposit(spr, rim2)

    # alur perut + mata
    det = np.zeros((H, W, 4), np.uint8)
    for i in range(4):
        pts = catmull([(x_of(0.93), y_of(0.55) + i * Hc * 0.035),
                       (x_of(0.74), y_of(0.64) + i * Hc * 0.028),
                       (x_of(0.55), y_of(0.68) + i * Hc * 0.018)], n=6)
        cv2.polylines(det, [np.array([[int(a), int(b)] for a, b in pts], np.int32)],
                      False, (150, 200, 235, 90), 2, cv2.LINE_AA)
    # garis mulut: dari moncong ke bawah rahang
    mulut = catmull([(x_of(0.972), y_of(0.470)), (x_of(0.905), y_of(0.520)),
                     (x_of(0.820), y_of(0.548))], n=7)
    cv2.polylines(det, [np.array([[int(a), int(b)] for a, b in mulut], np.int32)],
                  False, (120, 160, 195, 120), 2, cv2.LINE_AA)
    ex, ey = int(x_of(0.925)), int(y_of(0.415))
    _tempel_ke(det, glow_spr(11, (215, 245, 255), 0.95, 2.0, 0.7), ex, ey)
    det[..., 3] = (det[..., 3].astype(np.uint16) * mb.astype(np.uint16) // 255).astype(np.uint8)
    M.komposit(spr, det)
    return pangkas(spr)


def penyelam_gelap(H=330, warna=(210, 226, 245), rim_warna=(150, 220, 255)):
    """Figur penyelam putih bercahaya (pembanding skala) — gaya referensi."""
    W = int(H * 0.50)
    def g(p):
        # kepala + masker
        p.circ(W * 0.46, H * 0.10, H * 0.062, fill=warna)
        p.rrect(W * 0.40, H * 0.068, W * 0.56, H * 0.125, H * 0.02,
                fill=(40, 70, 110), outline=rim_warna, width=2.0)
        # tabung
        p.rrect(W * 0.16, H * 0.16, W * 0.30, H * 0.42, W * 0.06,
                fill=(60, 90, 130), outline=rim_warna, width=1.6)
        # badan
        p.poly(catmull([(W * 0.40, H * 0.17), (W * 0.52, H * 0.18), (W * 0.52, H * 0.35),
                        (W * 0.46, H * 0.44), (W * 0.34, H * 0.44), (W * 0.33, H * 0.32)],
                       8, closed=True), fill=warna)
        # lengan
        p.line(catmull([(W * 0.50, H * 0.21), (W * 0.64, H * 0.18), (W * 0.74, H * 0.24)], 6),
               warna, 7)
        p.line(catmull([(W * 0.36, H * 0.22), (W * 0.25, H * 0.31), (W * 0.29, H * 0.41)], 6),
               warna, 7)
        # kaki + sirip
        p.line(catmull([(W * 0.43, H * 0.44), (W * 0.47, H * 0.62), (W * 0.53, H * 0.78)], 6),
               warna, 8)
        p.line(catmull([(W * 0.37, H * 0.44), (W * 0.33, H * 0.62), (W * 0.31, H * 0.80)], 6),
               warna, 8)
        p.poly([(W * 0.51, H * 0.77), (W * 0.80, H * 0.85), (W * 0.51, H * 0.87)], fill=(120, 190, 230))
        p.poly([(W * 0.31, H * 0.79), (W * 0.08, H * 0.89), (W * 0.31, H * 0.90)], fill=(120, 190, 230))
    return pangkas(raster(W, H, g, ss=3))


def gigi_gelap(h=300, warna=(244, 238, 222), enamel=(216, 232, 246),
               rim_warna=(255, 226, 160), rim_kuat=0.55):
    """Gigi megalodon: mahkota meruncing, akar dua lobus, gerigi halus.

    Catatan teknis: `cv2.line`/`fillPoly` pada array RGBA menulis RGB mentah dan
    MENGABAIKAN alpha, jadi semua goresan transparan harus lewat lapisan
    RGBA terpisah + `komposit` (lihat `_lapis`). Versi pertama fungsi ini
    menggambar garis pertumbuhan langsung ke RGBA sehingga muncul garis hitam
    penuh — jangan diulang.
    """
    w = int(h * 0.60)
    pad = int(h * 0.11)
    W, H = w + pad * 2, h + pad * 2

    def P(u, v):
        return (pad + u * (w - 1), pad + v * (h - 1))

    tepi_kanan = [P(0.500, 0.020), P(0.596, 0.180), P(0.696, 0.380),
                  P(0.784, 0.590), P(0.836, 0.758)]
    akar_kanan = [P(0.828, 0.900), P(0.742, 0.978), P(0.628, 0.944), P(0.548, 0.868)]
    lekuk = [P(0.500, 0.838)]
    akar_kiri = [P(0.452, 0.868), P(0.372, 0.944), P(0.258, 0.978), P(0.172, 0.900)]
    tepi_kiri = [P(0.164, 0.758), P(0.216, 0.590), P(0.304, 0.380), P(0.404, 0.180)]
    sil = (catmull(tepi_kanan, 7) + catmull(akar_kanan, 6) + lekuk +
           catmull(akar_kiri, 6) + catmull(tepi_kiri, 7))
    mask_g = M.mask_poli(W, H, [sil], ss=3)
    mask_g = gblur(mask_g, max(0.5, h * 0.0012))

    ys = np.arange(H, dtype=np.float32)[:, None]
    xs = np.arange(W, dtype=np.float32)[None, :]
    v = np.clip((ys - pad) / max(1.0, h - 1), 0, 1)
    u = np.clip((xs - pad) / max(1.0, w - 1), 0, 1)

    ujung = np.array(enamel[:3], np.float32)
    pangkal = np.array(mix(warna, (208, 194, 168), 0.45)[:3], np.float32)
    akar_c = np.array(mix(warna, (166, 148, 118), 0.60)[:3], np.float32)
    grad = ujung * (1 - v[:, :, None]) + pangkal * v[:, :, None]
    w_akar = np.clip((v - 0.78) / 0.12, 0, 1)[:, :, None]
    grad = grad * (1 - w_akar) + akar_c * w_akar
    shade = (1.04 - 0.36 * u)[:, :, None] * (1.0 - 0.12 * np.clip(v - 0.5, 0, 1)[:, :, None])
    rgb = np.clip(grad * shade, 0, 255)

    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = rgb.astype(np.uint8)
    out[..., 3] = mask_g

    # ---- gerigi: duri kecil KELUAR dari tepi asli (diambil dari baris mask,
    # jadi selalu menempel di siluet walau tepinya melengkung)
    ser = np.zeros_like(mask_g)
    rows = np.where((mask_g > 128).any(axis=1))[0]
    if len(rows) > 8:
        y0, y1 = int(rows[0] + h * 0.06), int(rows[-1] - h * 0.30)
        N_SER = 20
        langkah = max(4, (y1 - y0) // N_SER)
        for sisi in (-1, 1):
            for i in range(N_SER):
                yy = int(y0 + i * (y1 - y0) / max(1, N_SER - 1))
                baris = np.where(mask_g[yy] > 128)[0]
                if len(baris) < 2:
                    continue
                xe = int(baris.max()) if sisi > 0 else int(baris.min())
                dd = max(2, int(h * 0.0065))
                tri = np.array([[xe, yy - langkah // 2], [xe + sisi * dd, yy],
                                [xe, yy + langkah // 2]], np.int32)
                cv2.fillPoly(ser, [tri], 255)
    mask_g = np.maximum(mask_g, ser)
    mask_g = gblur(mask_g, max(0.5, h * 0.0010))
    out[..., 3] = mask_g

    # ---- kilau memanjang di sisi kiri mahkota (lapisan transparan)
    kil = np.zeros((H, W), np.uint8)
    cv2.ellipse(kil, (int(pad + w * 0.36), int(pad + h * 0.36)),
                (max(2, int(w * 0.05)), max(4, int(h * 0.24))), -5, 0, 360, 255, -1)
    kil = gblur(kil, max(1.0, h * 0.016))
    _lapis(out, (255, 253, 244), (kil * (mask_g > 20) * 0.34).astype(np.uint8))

    # ---- pita bourlette (garis hangat melintang di pangkal mahkota)
    pita = np.zeros((H, W), np.uint8)
    cv2.ellipse(pita, (int(pad + w * 0.5), int(pad + h * 0.775)),
                (int(w * 0.40), max(3, int(h * 0.022))), 0, 0, 360, 255, -1)
    pita = gblur(pita, max(1.0, h * 0.01))
    _lapis(out, (198, 176, 140), (pita * (mask_g > 20) * 0.30).astype(np.uint8))

    # ---- rim hangat dari kiri atas (cahaya vitrin)
    rim = _rim(mask_g, arah=(-0.5, -1.0), radius=max(1.6, h * 0.0042),
               kekuatan=rim_kuat, warna=rim_warna)
    rim = np.minimum(rim, np.repeat(mask_g[:, :, None], 4, axis=2))
    M.komposit(out, rim)
    return pangkas(out)


def plinth(w=560, h=120, warna=(24, 30, 48), atas=(46, 58, 86)):
    """Landasan/vitrin: permukaan berkilau + bayangan kontak (objek menyentuh)."""
    pad = 30
    W, H = w + pad * 2, h + pad * 2
    out = np.zeros((H, W, 4), np.uint8)
    # bayangan bawah
    sh = np.zeros((H, W), np.uint8)
    ImageDraw.Draw(Image.fromarray(sh)).ellipse(
        [pad + 20, pad + h - 20, pad + w - 20, pad + h + 26], fill=120)
    sh = gblur(sh, 18)
    s = np.zeros((H, W, 4), np.uint8)
    s[..., :3] = (0, 0, 0)
    s[..., 3] = (sh.astype(np.float32) * 0.55).astype(np.uint8)
    blit(out, s, 0, 0)
    # pelat atas (elips) + sisi
    def g(p):
        p.ell(pad, pad, pad + w, pad + h * 0.42, fill=atas)
        p.rect(pad, pad + h * 0.21, pad + w, pad + h * 0.72, fill=warna)
        p.ell(pad, pad + h * 0.52, pad + w, pad + h * 0.94, fill=mix(warna, (0, 0, 0), 0.35))
        p.ell(pad, pad, pad + w, pad + h * 0.42, outline=mix(atas, (255, 255, 255), 0.25), width=2)
    blit(out, raster(w, h, g, ss=2), pad, pad)
    return out


def bumi_gelap(r=300, warna_air=(30, 92, 180), warna_darat=(58, 150, 96)):
    """Bumi bergaya referensi: bola bergradasi + benua blob + rim cahaya."""
    S = int(r * 2.3)
    c = S / 2
    spr = np.zeros((S, S, 4), np.uint8)

    def g(p):
        p.circ(c, c, r, fill=warna_air)
    spr = raster(S, S, g, ss=2)
    # gradasi bola (terang kiri-atas)
    yy = np.arange(S, dtype=np.float32)[:, None]
    xx = np.arange(S, dtype=np.float32)[None, :]
    d = np.sqrt((xx - c * 0.55) ** 2 + (yy - c * 0.45) ** 2) / (r * 1.7)
    sh = np.clip(d, 0, 1)[:, :, None]
    base = np.array(warna_air, np.float32)
    hi = np.array(mix(warna_air, (255, 255, 255), 0.55)[:3], np.float32)
    lo = np.array(mix(warna_air, (0, 0, 0), 0.72)[:3], np.float32)
    col = hi * (1 - sh) + lo * sh
    m = (spr[..., 3] > 10)
    spr[..., :3] = np.where(m[:, :, None], col, spr[..., :3])
    # benua
    rnd = rng(11)
    benua = np.zeros((S, S, 4), np.uint8)
    for i in range(14):
        bx = c + rnd.uniform(-r * 0.72, r * 0.72)
        by = c + rnd.uniform(-r * 0.72, r * 0.72)
        br = rnd.uniform(r * 0.10, r * 0.30)
        cv2.circle(benua, (int(bx), int(by)), int(br), (*warna_darat, 255), -1, cv2.LINE_AA)
    benua[..., 3] = (benua[..., 3].astype(np.float32) * 0.92).astype(np.uint8)
    benua = gblur(benua, 3)
    M.komposit(spr, benua)
    # awan
    awan = np.zeros((S, S, 4), np.uint8)
    for i in range(10):
        bx = c + rnd.uniform(-r * 0.8, r * 0.8)
        by = c + rnd.uniform(-r * 0.8, r * 0.8)
        br = rnd.uniform(r * 0.08, r * 0.20)
        cv2.ellipse(awan, (int(bx), int(by)), (int(br * 1.7), int(br * 0.6)),
                    0, 0, 360, (255, 255, 255, 120), -1, cv2.LINE_AA)
    awan = gblur(awan, 7)
    M.komposit(spr, awan)
    # rim cahaya
    rim = _rim(spr[..., 3], arah=(-1, -1), radius=3.0, kekuatan=0.95, warna=(170, 225, 255))
    M.komposit(spr, rim)
    return pangkas(spr)


# ============================================================== 8. EFEK

def kilau_bintang(k, cx, cy, r=16, warna=(255, 255, 255), alpha=1.0, rot=0.0):
    """Kilau bintang empat sisi (sparkle) — dipakai di gigi dan data penting."""
    def g(p):
        for a in (rot, rot + math.pi / 2):
            p.line([(r + 10 + math.cos(a) * -r, r + 10 + math.sin(a) * -r),
                    (r + 10 + math.cos(a) * r, r + 10 + math.sin(a) * r)], warna, 2.6)
    spr = raster(r * 2 + 20, r * 2 + 20, g, ss=3)
    blit_c(k.a, spr, cx, cy, alpha)
    pendar(k, cx, cy, int(r * 2.2), warna, 0.45 * alpha, 2.4, 0.25)


def cincin(k, cx, cy, r, warna=CYAN, tebal=3.0, alpha=1.0, dash=0, glow=0.5):
    """Cincin penanda (fokus) dengan pendar opsional; `dash` > 0 membuat putus-putus."""
    if glow > 0:
        pendar(k, cx, cy, int(r * 1.5), warna, glow * 0.35 * alpha, 2.6)
    tebal = int(round(tebal))
    r = int(round(r))
    if dash:
        n = 26
        for i in range(n):
            if i % 2:
                continue
            a0 = i / n * 2 * math.pi
            a1 = (i + 1) / n * 2 * math.pi
            cv2.ellipse(k.a, (int(cx), int(cy)), (int(r), int(r)), 0,
                        math.degrees(a0), math.degrees(a1), warna, tebal, cv2.LINE_AA)
    else:
        cv2.circle(k.a, (int(cx), int(cy)), int(r), warna, int(tebal), cv2.LINE_AA)


def partikel_glow(n=90, area=(0, 0, 1080, 1920), seed=3, warna=(170, 220, 255),
                  vy=(-18, -4), vx=(-4, 4), size=(1, 3), alpha=(0.10, 0.45)):
    """Debu/plankton bercahaya (sprite titik dengan pendar, digambar additif)."""
    P = M.Partikel(n, area, seed=seed, vx=vx, vy=vy, size=size, alpha=alpha, warna=warna)
    return P


def debu_add(dst, P, t, goyang=5.0):
    """Gambar partikel sebagai titik aditif (bukan warna solid)."""
    return P.gambar(dst, t, goyang=goyang)


def kilat(k, cx, cy, r=420, warna=(255, 236, 200), alpha=0.85):
    """Kedipan cahaya singkat (impact) — dipakai saat gigitan/reveal."""
    if alpha <= 0.01:
        return
    s = glow_spr(int(r), warna, alpha, 2.0, 0.6)
    blit_add(k.a, s, cx - r, cy - r)


def garis_kejut(k, cx, cy, r, warna=(255, 255, 255), alpha=0.55, tebal=4.0):
    """Gelombang kejut: cincin tipis yang memudar."""
    if alpha <= 0.01 or r < 4:
        return
    cv2.circle(k.a, (int(cx), int(cy)), int(r), warna, int(tebal), cv2.LINE_AA)


# ============================================================== 9. SELFTEST

def _selftest():
    import time
    k = Kanvas(W_, H_, BG_0)
    t0 = time.time()
    latar_gelap(k, bintang_n=620)
    kedalaman_air(k, 0, H_)
    berkas_atas(k, 0.0, n=4, kuat=0.14)
    print(f"latar: {(time.time()-t0)*1000:.0f} ms")
    t1 = time.time()
    hiu = hiu_gelap(900)
    print(f"hiu_gelap: {(time.time()-t1)*1000:.0f} ms  {hiu.shape}")
    t2 = time.time()
    blit(k.a, M.swim(hiu, amp=10, lam=300, phase=0.4), 60, 620)
    print(f"swim+blit: {(time.time()-t2)*1000:.2f} ms")
    panel(k, 70, 1180, 940, 300, aksen=CYAN)
    bar_chart(k, 100, 1240, 880, [("BUMI", 0.02, "11,2 km/detik", CYAN),
                                  ("CAHAYA", 0.75, "300.000 km/detik", GOLD),
                                  ("MEGALODON", 1.0, "24,3 meter", CORAL)],
              tinggi_bar=34, jarak=86)
    blit(k.a, pill_spr("LEBIH ANEH DARI FIKSI ILMIAH", VIOLET), 90, 1560)
    blit(k.a, badge_babak("LAUT PURBA", CYAN), 560, 40)
    blit(k.a, merek(), 44, 36)
    progres_bawah(k, 0.4, CYAN, segmen=8, aktif=0)
    stat_besar(k, "24,3", "meter", "BATAS ATAS", 90, 900, GOLD, 150)
    blit(k.a, pp := plinth(520, 110), 280, 1450)
    blit(k.a, gg := gigi_gelap(240), 420, 1290)
    kilau_bintang(k, 700, 1320, 18)
    t3 = time.time()
    for i in range(20):
        f = k.a.copy()
        blit(f, M.swim(hiu, amp=10, lam=300, phase=i * 0.3), 60, 620)
        pendar(k, 150, 400, 120, CYAN, 0.25, 2.2)
    print(f"komposisi (salin+hiu+pendar): {(time.time()-t3)/20*1000:.2f} ms/frame")
    Image.fromarray(k.a).save("/tmp/v19_selftest.png")
    print("-> /tmp/v19_selftest.png")


if __name__ == "__main__":
    _selftest()
