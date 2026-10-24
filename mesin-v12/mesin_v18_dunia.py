#!/usr/bin/env python3
"""mesin_v18_dunia.py — DUNIA VISUAL KlikTahu v18: palet, makhluk, kartu, diagram.

Modul ini TIDAK menyentuh timeline. Isinya hanya "bahan gambar": apa yang bisa
diraster sekali lalu ditempel berkali-kali oleh mesin_v18_ep55.py.

Bahasa visual (diwarisi Ep52-Ep55, dipertajam):

    kertas krem  ->  langit senja muda  ->  garis permukaan bergelombang
    -> air teal bertingkat (TERANG, tanpa hitam)  ->  berkas cahaya krem
    -> pasir beroutline + kaustik  ->  biota beroutline tinta 3-4 px
    -> kartu krem beroutline + label kecil + sumber di bawah

Yang baru dibanding v17 (dan sebabnya):

  * `badan()` + `catmull()` -> siluet hewan dari PROFIL, bukan elips+tumpukan.
    Hasilnya punggung berpunuk, perut rata, pangkal ekor sempit: siluet hiu
    yang benar, bukan "ikan balon".
  * `hiu_spr()` punya mulut, insang, garis gurat sisi, dan bercak perut;
    sekali raster, dipakai di 8 scene dengan skala berbeda.
  * `berkas_cahaya()` memakai gradasi alpha vertikal (bukan poligon datar),
    jadi cahaya terasa menyebar dan tidak seperti pita kertas.
  * `kaustik_spr()` memakai ubin interferensi gelombang (bukan noise acak) ->
    pola jaring cahaya seperti pantulan nyata di dasar laut.
  * `kartu_spr()`: bayangan berlapis (kontak + ambient), pita aksen, sudut
    28 px, judul dua baris dengan tracking rapat.
  * `hud_spr()`: merek + lencana episode, digambar sekali per sesi.

Semua fungsi mengembalikan ndarray RGBA (siap `blit`) atau menulis langsung ke
`Kanvas`. Tidak ada I/O berkas, tidak ada dependensi selain mesin_v18_inti.

Selftest:  python3 mesin_v18_dunia.py
"""
from __future__ import annotations

import functools
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw

from mesin_v18_inti import (F_BOLD, F_MED, F_REG, F_SEMI, Kanvas, Pena, pangkas, badan,
                            bayang, belly_mask, blit, blit_add, blit_c, blit_kali,
                            gblur, gigi_kecil, komposit, lapis_rgba, mask_poli, mask_rrect, catmull, clamp, eio, eo, fbm,
                            fit_size, gblur, gelombang_pts, gigi_pts, hexc, lerp,
                            lum, mask, mix, mixer_oklab, rng, raster, siluet,
                            spr_text, tw, tint, with_a, wrap)

# ============================================================== 1. palet

KERTAS = (246, 241, 232)
KERTAS_D = (238, 231, 218)
KREM = (250, 245, 233)
PUTIH = (255, 253, 248)
INK = (24, 24, 31)
INK_2 = (58, 58, 70)
MUTED = (128, 122, 112)

LANGIT_1 = (251, 239, 219)
LANGIT_2 = (250, 228, 197)
LANGIT_3 = (238, 203, 165)
SENJA = (236, 185, 138)
SENJA_2 = (226, 156, 112)
TERRA = (196, 108, 74)
TERRA_D = (156, 78, 54)
AMBER = (245, 176, 66)
AMBER_T = (250, 206, 128)

AIR_1 = (186, 219, 208)
AIR_2 = (150, 197, 184)
AIR_3 = (108, 172, 160)
AIR_4 = (72, 142, 132)
AIR_5 = (56, 122, 114)
AIR_6 = (44, 104, 100)
BUIH = (253, 251, 244)

PASIR = (233, 208, 173)
PASIR_D = (211, 181, 145)
PASIR_T = (243, 226, 197)
BATU = (176, 168, 156)
BATU_D = (142, 134, 124)
RUMPUT = (86, 140, 104)
RUMPUT_D = (58, 108, 82)

HIU = (40, 76, 84)
HIU_D = (28, 54, 62)
HIU_2 = (52, 96, 104)
PERUT = (250, 245, 232)
MOUTH = (96, 44, 44)
GUSI = (186, 104, 92)
GIGI = (252, 248, 236)
GIGI_T = (226, 196, 148)
DARAH = (150, 60, 46)

NAVY = (44, 62, 92)
OLIVE = (110, 122, 74)
UNGU = (108, 84, 140)
KUNING = (238, 190, 78)

SURF = 330          # garis permukaan air
OUTLINE = 3.4       # tebal garis tinta standar


def lebar_outline(skala=1.0):
    """Ketebalan outline yang tetap terbaca setelah sprite diperkecil."""
    return float(np.clip(OUTLINE * skala, 2.0, 5.5))


# ============================================================== 2. langit

def langit(k, t=0.0, awan=True, matahari_x=812, matahari_y=196, senja=0.30,
           tinggi=SURF):
    """Pita langit: kertas -> senja muda, SATU gradasi utuh (tanpa pita terpisah).

    Versi awal memakai dua gradasi bertumpuk + `kabut()`, dan batas keduanya
    muncul sebagai garis horizontal di video. Sekarang seluruh langit satu
    pemanggilan gradasi dengan 4 stop, jadi transisinya mulus tanpa batas.
    """
    k.gradasi_v(0, tinggi, [
        (0.00, mix(KERTAS, PUTIH, 0.62)),
        (0.30, mixer_oklab(LANGIT_1, KERTAS, senja * 0.55)),
        (0.66, mixer_oklab(LANGIT_2, SENJA, senja * 0.55)),
        (0.88, mix(SENJA, PUTIH, 0.30 * senja)),
        (1.00, mixer_oklab(SENJA, PUTIH, 0.42)),
    ], seed=11)
    if matahari_x is not None:
        _matahari(k, matahari_x, matahari_y, 54, t)
    if awan:
        _awan(k, 236, 118, 150, t)
        _awan(k, 640, 74, 108, t, tone=mix(PUTIH, KREM, 0.30))


def _matahari(k, cx, cy, r, t=0.0):
    """Matahari: piringan + halo dua lapis (halo dibuat dari gradasi radial)."""
    yy = np.arange(-3 * r, 3 * r)[:, None]
    xx = np.arange(-3 * r, 3 * r)[None, :]
    d = np.sqrt(xx ** 2 + yy ** 2) / (3.0 * r)
    halo = np.clip(1.0 - d, 0, 1) ** 2.4
    H, W = halo.shape
    spr = np.zeros((H, W, 4), np.uint8)
    spr[..., 0] = 255
    spr[..., 1] = 236
    spr[..., 2] = 198
    spr[..., 3] = (halo * 118).astype(np.uint8)
    k.tempel_add(spr, cx - 3 * r, cy - 3 * r, 0.85)
    # piringan beroutline
    def g(p):
        p.d.ellipse([(0) * p.k, (0) * p.k, 2 * r * p.k, 2 * r * p.k],
                    fill=mix(AMBER, SENJA_2, 0.25), outline=mix(TERRA, INK, 0.35),
                    width=int(3 * p.k))
    spr2 = raster(2 * r + 6, 2 * r + 6, lambda p: g(p) if True else None, ss=3)
    # ulang dengan offset 3 px agar outline tidak terpotong
    def g2(p):
        p.circ(r + 3, r + 3, r - 1, fill=mix(AMBER, SENJA_2, 0.22),
               outline=mix(TERRA, INK, 0.30), width=3.0)
    spr2 = raster(2 * r + 8, 2 * r + 8, g2, ss=3)
    blit_c(k.a, spr2, cx, cy)


def _awan(k, cx, cy, w, t, tone=None, seed=1):
    """Awan tiga gumpal bergaya kertas tempel — tepi hanya dari blur, tanpa garis."""
    tone = tone or mix(PUTIH, KREM, 0.30)
    h = w * 0.38
    W, H = int(w + 90), int(h + 70)
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    r = rng(seed)
    for i, (fx, fy, fr) in enumerate([(0.20, 0.52, 0.34), (0.44, 0.40, 0.40),
                                      (0.68, 0.50, 0.32), (0.84, 0.58, 0.22)]):
        rr = w * fr * r.uniform(0.92, 1.08)
        d.ellipse([W * fx - rr, H * fy - rr * 0.86, W * fx + rr, H * fy + rr * 0.92],
                  fill=255)
    m = np.array(gblur(np.array(im), 5.0))
    spr = np.zeros((H, W, 4), np.uint8)
    spr[..., :3] = tone
    spr[..., 3] = (m.astype(np.float32) * 0.80).astype(np.uint8)
    blit_c(k.a, spr, cx, cy)


# ============================================================== 3. permukaan air

def permukaan(k, t=0.0, y=SURF, amp=9.0, lam=300.0, sorot=True):
    """Garis permukaan beroutline + buih: dua gelombang yang saling melambat.

    Digambar pada pita kecil (bukan full canvas) memakai `Pena`: ~0,6 ms.
    """
    y = float(y)
    h = int(amp * 4 + 26)
    top = int(y - h * 0.55)
    w = k.w
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    p = Pena(ImageDraw.Draw(im), 1)
    oy = h * 0.45
    g1 = gelombang_pts(0, w, oy, amp, lam, t * 1.15)
    g2 = gelombang_pts(0, w, oy + amp * 0.55, amp * 1.25, lam * 1.7, -t * 0.8 + 1.2)
    # badan air di bawah garis: isi poligon lalu tutup dengan gradasi terang
    isi = g1 + [(w, h), (0, h)]
    p.poly(isi, fill=mix(AIR_1, BUIH, 0.35))
    p.line(g2, with_a(BUIH, 0.55), 4.0)
    p.line(g1, with_a(mix(AIR_3, AIR_2, 0.35), 0.85), 3.0)
    # buih: titik-titik kecil yang naik-turun sepanjang garis
    r = rng(int(t * 60) + 7)
    for i in range(26):
        x = (i * 47 + 13) % w
        gy = oy + amp * math.sin(2 * math.pi * (x) / lam + t * 1.15)
        rr = r.uniform(1.6, 4.2)
        p.circ(x, gy - rr * 1.8 - r.uniform(0, 6), rr, fill=with_a(BUIH, 0.75))
    blit(k.a, np.array(im), 0, top)
    if sorot:
        # kilau tipis di atas garis
        gl = np.zeros((int(amp * 3), w, 4), np.uint8)
        gl[..., :3] = (255, 252, 240)
        gl[..., 3] = 26
        blit_add(k.a, gl, 0, int(top - 2))


# ============================================================== 4. air & cahaya

def air(k, y0=SURF, y1=1920, dalam=1.0):
    """Gradasi air: makin dalam makin tua TAPI tetap terang (tanpa hitam)."""
    k.gradasi_v(y0, y1, [(0.0, mix(AIR_1, BUIH, 0.30)),
                         (0.26, AIR_1),
                         (0.52, AIR_2),
                         (0.74, mix(AIR_3, AIR_4, 0.35 * dalam)),
                         (1.0, mix(AIR_4, AIR_5, 0.55 * dalam))], seed=29)


def berkas_cahaya(k, t=0.0, n=4, x0=0, x1=1080, y0=SURF, y1=1500, kuat=0.085):
    """Berkas cahaya dari permukaan: sprite gradasi alpha, digeser halus.

    Alpha total sengaja kecil (<0,10) dan tepinya diblur: berkas yang terlalu
    kuat terbaca seperti pita kertas, bukan cahaya.
    """
    r = rng(1234)
    for i in range(n):
        cx = x0 + (x1 - x0) * (i + 0.5) / n + r.uniform(-70, 70)
        wtop = r.uniform(40, 78)
        wbot = wtop * r.uniform(2.4, 3.8)
        ay = int((y1 - y0) * r.uniform(0.6, 1.0))
        H = ay + 60
        W = int(wbot * 2 + 120)
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        ww = (wtop + (wbot - wtop) * yy) / 2.0
        xx = np.arange(W, dtype=np.float32)[None, :] - W / 2.0
        d = np.abs(xx) / np.maximum(ww, 1.0)
        prof = np.clip(1.0 - d, 0, 1) ** 2.6
        vert = (1.0 - yy) ** 1.6
        a = np.clip(prof * vert * kuat * 255.0, 0, 255).astype(np.uint8)
        spr = np.zeros((H, W, 4), np.uint8)
        spr[..., 0] = 255
        spr[..., 1] = 249
        spr[..., 2] = 220
        spr[..., 3] = gblur(a, 9)
        drift = math.sin(t * 0.20 + i * 1.7) * 22 + (t * 3.0) % 26
        blit_add(k.a, spr, int(cx - W / 2 + drift), y0)


def kaustik_spr(size=512, seed=7, alpha=0.30):
    """Ubin kaustik (interferensi gelombang) untuk blend ADD di dasar laut."""
    from mesin_v18_inti import caustic_tile
    tile = caustic_tile(size, seed)
    tile = gblur(tile, 1.6)
    spr = np.zeros((size, size, 4), np.uint8)
    spr[..., :3] = (255, 252, 236)
    spr[..., 3] = (tile.astype(np.float32) * alpha).astype(np.uint8)
    return spr


def kaustik_dasar(k, tile, t, y0, y1, alpha=0.40):
    """Kaustik di pita dasar: pola di-GATHER dari ubin (tanpa sambungan kotak).

    Versi blit-per-ubin meninggalkan kotak terang 512 px di pasir. Di sini pola
    diambil sebagai indeks (yy, xx) dari satu ubin, lalu ditambahkan dengan
    pemberat yang memudar ke atas — satu operasi numpy untuk seluruh pita.
    """
    y0, y1 = int(y0), int(y1)
    h = y1 - y0
    if h <= 0:
        return
    T = tile[..., 3].astype(np.float32) / 255.0
    s = T.shape[0]
    oy = int(t * 6) % s
    ox = int(t * 4) % s
    yy = (np.arange(h, dtype=np.int32)[:, None] + oy) % s
    xx = (np.arange(k.w, dtype=np.int32)[None, :] + ox) % s
    pola = T[yy, xx]
    fade = (1.0 - np.arange(h, dtype=np.float32)[:, None] / max(1, h)) ** 1.2
    a = pola * fade * alpha
    reg = k.a[y0:y1].astype(np.float32)
    reg += np.array((255, 252, 236), np.float32) * a[:, :, None]
    k.a[y0:y1] = np.clip(reg, 0, 255).astype(np.uint8)


def kabut_kedalaman(k, y0, y1, warna=None, kuat=0.30):
    """Kabut jarak: makin dalam makin pucat (udara/air perspective)."""
    k.kabut(y0, y1, warna or mix(AIR_1, AIR_2, 0.45), kuat)


# ============================================================== 5. dasar laut

def dasar_laut(k, y0=1520, seed=5, pasir=PASIR, tinggi=1920):
    """Bukit pasir beroutline + kerikil + kilau — ditempel sekali di latar.

    Siluet memakai `catmull` sehingga tepi pasir melengkung seperti bukit, bukan
    garis datar. `y0` = titik tertinggi pasir.
    """
    w = k.w
    H = tinggi - int(y0) + 10
    im = Image.new("RGBA", (w, H), (0, 0, 0, 0))
    p = Pena(ImageDraw.Draw(im), 2)
    oy = 10.0
    r = rng(seed)
    kunci = [(0, 96), (140, 70), (300, 96), (470, 62), (660, 88),
             (840, 58), (990, 84), (1080, 66)]
    atas = [(x, y + oy) for x, y in catmull(kunci, n=8)]
    isi = atas + [(w, H), (0, H)]
    p.poly(isi, fill=pasir)
    # pita pasir lebih terang di puncak
    for i in range(0, len(atas) - 1, 1):
        x0, ya = atas[i]
        x1, yb = atas[i + 1]
        p.line([(x0, ya + 12), (x1, yb + 12)], with_a(mix(PASIR_T, PUTIH, 0.45), 0.50), 6)
    p.poly(isi, outline=mix(INK, pasir, 0.42), width=4)
    # kerikil & batu kecil
    for i in range(30):
        x = r.uniform(20, w - 20)
        yy = oy + r.uniform(46, min(H - 40, 420))
        rr = r.uniform(2.5, 9.0)
        col = mix(BATU, pasir, r.uniform(0.35, 0.80))
        p.circ(x, yy, rr, fill=col, outline=mix(INK, col, 0.30), width=1.5)
    for i in range(8):
        x = r.uniform(30, w - 30)
        yy = oy + r.uniform(70, min(H - 60, 380))
        rx, ry = r.uniform(10, 24), r.uniform(6, 13)
        col = mix(BATU_D, BATU, r.uniform(0.25, 0.70))
        p.ell(x - rx, yy - ry, x + rx, yy + ry, fill=col,
              outline=mix(INK, col, 0.32), width=2.0)
        p.arc(x - rx * 0.72, yy - ry * 0.9, x + rx * 0.72, yy + ry * 0.45,
              200, 340, with_a(PUTIH, 0.35), 2.2)
    blit(k.a, np.array(im), 0, int(y0) - 10)


def rumput(k, x, y, tinggi, t=0.0, n=4, tone=None, ayun=0.0):
    """Rumpun rumput laut: bilah meruncing yang bergoyang dengan arus."""
    tone = tone or RUMPUT
    tone2 = mix(tone, RUMPUT_D, 0.55)
    r = rng(int(x) * 7 + int(y))
    im = Image.new("RGBA", (int(tinggi * 0.9) + 24, int(tinggi) + 16), (0, 0, 0, 0))
    p = Pena(ImageDraw.Draw(im), 2)
    cx = im.size[0] / 2.0
    base = im.size[1] - 6
    for i in range(n):
        hh = tinggi * r.uniform(0.55, 1.0)
        dx = (i - (n - 1) / 2) * (tinggi * 0.13) + r.uniform(-3, 3)
        sway = math.sin(t * 1.5 + i * 1.1 + ayun) * tinggi * 0.10
        pts = [(cx + dx, base), (cx + dx + sway * 0.4, base - hh * 0.45),
               (cx + dx + sway, base - hh)]
        pol = badan(pts, [tinggi * 0.035, tinggi * 0.026, 1.2])
        col = mix(tone, tone2, r.uniform(0, 0.6))
        p.poly(pol, fill=col, outline=mix(INK, col, 0.30), width=1.8)
    blit(k.a, np.array(im), int(x - im.size[0] / 2), int(y - im.size[1] + 4))


def batu(k, cx, cy, rx, ry, tone=None, rot=-0.2):
    """Bongkahan batu beroutline + kilau atas."""
    tone = tone or BATU
    im = Image.new("RGBA", (int(rx * 2 + 20), int(ry * 2 + 20)), (0, 0, 0, 0))
    p = Pena(ImageDraw.Draw(im), 2)
    pts = []
    n = 9
    r = rng(int(cx) * 3 + int(cy))
    for i in range(n):
        a = 2 * math.pi * i / n + rot
        rr = 1.0 + r.uniform(-0.12, 0.10)
        pts.append((rx + 10 + math.cos(a) * rx * rr, ry + 10 + math.sin(a) * ry * rr))
    p.poly(pts, fill=tone, outline=mix(INK, tone, 0.25), width=2.2)
    p.arc(rx * 0.45, ry * 0.55, rx * 1.55, ry * 1.35, 190, 330, with_a(PUTIH, 0.30), 2.5)
    blit_c(k.a, np.array(im), cx, cy)


# ============================================================== 6. hiu

def _profil_hiu(macam="megalodon"):
    """Profil tubuh: daftar (x, y) pada kotak 1.0 x 1.0 (hidung di kanan).

    Dikalibrasi ke rekonstruksi 2025: tubuh memanjang, punggung berpunuk di
    belakang kepala, pangkal ekor sempit, moncong tumpul (megalodon/lemon) atau
    meruncing (hiu putih).
    """
    if macam == "lemon":
        top = [(0.060, 0.48), (0.115, 0.33), (0.235, 0.20), (0.40, 0.11),
               (0.55, 0.07), (0.70, 0.09), (0.845, 0.19), (0.94, 0.32)]
        bot = [(0.955, 0.41), (0.895, 0.53), (0.76, 0.64), (0.58, 0.72),
               (0.42, 0.755), (0.27, 0.735), (0.14, 0.645), (0.060, 0.555)]
    elif macam == "putih":
        top = [(0.055, 0.49), (0.115, 0.32), (0.235, 0.17), (0.42, 0.08),
               (0.60, 0.045), (0.755, 0.095), (0.875, 0.21), (0.960, 0.345)]
        bot = [(0.965, 0.425), (0.905, 0.515), (0.78, 0.625), (0.62, 0.715),
               (0.45, 0.755), (0.30, 0.745), (0.16, 0.655), (0.055, 0.555)]
    else:   # megalodon: gagah, moncong tumpul, punggung tebal
        top = [(0.050, 0.47), (0.115, 0.30), (0.245, 0.185), (0.415, 0.095),
               (0.565, 0.055), (0.715, 0.105), (0.845, 0.225), (0.935, 0.345)]
        bot = [(0.950, 0.435), (0.890, 0.555), (0.765, 0.665), (0.60, 0.745),
               (0.435, 0.785), (0.285, 0.765), (0.145, 0.665), (0.050, 0.555)]
    return top, bot


def hiu_spr(L=900, macam="megalodon", tone=HIU, perut=PERUT, mulut=True,
            gigi_baris=0, ekor="bulan", insang=True, skala_outline=1.0):
    """Raster satu hiu lengkap (badan, sirip, ekor, mata, insang, mulut).

    Kembalian: sprite RGBA dengan hidung di KANAN. Tinggi sprite ~0,62 x L.
    Perut dicat dengan MASK badan, jadi tidak pernah melewati siluet — bug ini
    yang membuat v18 awal terlihat "berparuh putih".
    """
    Hc = L * 0.38
    W = int(L * 1.18)
    H = int(L * 0.70)
    cx0 = L * 0.10
    cy0 = H * 0.50
    ow = lebar_outline(skala_outline)
    ink = mix(INK, tone, 0.16)
    top, bot = _profil_hiu(macam)

    def x_of(u):
        return cx0 + u * L

    def y_of(v):
        return cy0 + (v - 0.44) * Hc

    def g(p):
        # ---------------- ekor
        if ekor == "bulan":
            ek = [(x_of(0.135), y_of(0.46)), (x_of(0.010), y_of(0.10)),
                  (x_of(0.075), y_of(0.455)), (x_of(0.018), y_of(0.80)),
                  (x_of(0.135), y_of(0.545))]
        else:
            ek = [(x_of(0.12), y_of(0.42)), (x_of(-0.03), y_of(-0.06)),
                  (x_of(0.05), y_of(0.44)), (x_of(0.01), y_of(0.70)),
                  (x_of(0.12), y_of(0.58))]
        p.poly(catmull(ek, 7, closed=True), fill=mix(tone, INK, 0.12),
               outline=ink, width=ow)
        # ---------------- sirip punggung
        punggung = [(x_of(0.555), y_of(0.16)), (x_of(0.60), y_of(-0.30)),
                    (x_of(0.655), y_of(-0.05)), (x_of(0.715), y_of(0.16))]
        p.poly(catmull(punggung, 9, closed=True), fill=mix(tone, INK, 0.04),
               outline=ink, width=ow)
        d2 = [(x_of(0.250), y_of(0.235)), (x_of(0.268), y_of(0.085)),
              (x_of(0.318), y_of(0.225))]
        p.poly(d2, fill=mix(tone, INK, 0.06), outline=ink, width=ow * 0.8)
        # ---------------- sirip dada
        dada = [(x_of(0.760), y_of(0.54)), (x_of(0.665), y_of(0.90)),
                (x_of(0.632), y_of(0.93)), (x_of(0.672), y_of(0.70)),
                (x_of(0.716), y_of(0.58))]
        p.poly(catmull(dada, 8, closed=True), fill=mix(tone, HIU_D, 0.32),
               outline=ink, width=ow)
        p.poly([(x_of(0.475), y_of(0.755)), (x_of(0.452), y_of(0.875)),
                (x_of(0.522), y_of(0.775))], fill=tone, outline=ink, width=ow * 0.75)
        p.poly([(x_of(0.335), y_of(0.755)), (x_of(0.318), y_of(0.865)),
                (x_of(0.385), y_of(0.775))], fill=tone, outline=ink, width=ow * 0.75)
        # ---------------- badan
        atas = catmull([(x_of(u), y_of(v)) for u, v in top], n=9)
        bawah = catmull([(x_of(u), y_of(v)) for u, v in bot], n=9)
        body = atas + bawah
        p.poly(body, fill=tone, outline=ink, width=ow)
    spr = raster(W, H, g, ss=2)

    # ---------------- perut: belly_mask (menempel tepi bawah, anti melayang)
    mask_badan = mask_poli(W, H, [catmull([(x_of(u), y_of(v)) for u, v in top], n=9) +
                                  catmull([(x_of(u), y_of(v)) for u, v in bot], n=9)], ss=1)
    bm = belly_mask(mask_badan, frac=0.60)
    lap = np.zeros((H, W, 4), np.uint8)
    lap[..., :3] = mix(perut, tone, 0.04)
    lap[..., 3] = bm
    komposit(spr, lap)
    # garis batas perut: ikuti tepi atas belly_mask, tapi hanya segmen tengah
    tepi = np.zeros((H, W), np.uint8)
    for x in range(W):
        ys = np.where(bm[:, x] > 8)[0]
        if len(ys):
            tepi[ys[0], x] = 255

    # ---------------- detail di atas perut
    def g2(p):
        if insang:
            for i in range(5):
                gx = x_of(0.655 - i * 0.024)
                p.arc(gx - 4.5, y_of(0.30) + i * 1.6, gx + 4.5, y_of(0.50) + i * 1.6,
                      255, 465, with_a(mix(tone, INK, 0.50), 0.50), 1.9)
        ex, ey = x_of(0.892), y_of(0.375)
        p.circ(ex, ey, L * 0.0155, fill=PUTIH, outline=ink, width=1.5)
        p.circ(ex + L * 0.0008, ey, L * 0.0090, fill=INK)
        p.circ(ex - L * 0.0030, ey - L * 0.0035, L * 0.0032, fill=with_a(PUTIH, 0.95))
        if mulut:
            mx0, my0 = x_of(0.978), y_of(0.515)
            mx1, my1 = x_of(0.835), y_of(0.585)
            p.line([(mx0, my0), (lerp(mx0, mx1, 0.40), my0 + L * 0.026),
                    (mx1, my1)], with_a(INK, 0.92), 3.4)
            if gigi_baris:
                for i in range(gigi_baris):
                    f = i / max(1, gigi_baris - 1)
                    gx = lerp(mx0 - L * 0.006, mx1 + L * 0.004, f)
                    gy = lerp(my0 + L * 0.002, my1 - L * 0.002, f) + L * 0.004
                    hg = L * 0.0150
                    p.poly([(gx - hg * 0.52, gy), (gx + hg * 0.52, gy),
                            (gx, gy + hg * 1.15)], fill=mix(GIGI, PUTIH, 0.5),
                           outline=mix(INK, GIGI, 0.55), width=1.2)
        p.line(catmull([(x_of(0.905), y_of(0.495)), (x_of(0.62), y_of(0.462)),
                        (x_of(0.30), y_of(0.492)), (x_of(0.14), y_of(0.515))], n=9),
               with_a(mix(tone, PUTIH, 0.35), 0.30), 1.5)
    det = raster(W, H, g2, ss=2)
    # KLIP: semua detail wajib berada di dalam siluet badan (v18 awal: garis
    # perut dan mulut keluar badan karena tidak diklip)
    det[..., 3] = (det[..., 3].astype(np.uint16) * mask_badan.astype(np.uint16) // 255).astype(np.uint8)
    komposit(spr, det)
    return pangkas(spr)


def hiu_bayi_spr(L=200, tone=None):
    """Ikan kecil / hiu muda untuk latar (lebih sederhana, tetap beroutline)."""
    tone = tone or mix(HIU, AIR_3, 0.35)
    W, H = int(L * 1.2), int(L * 0.62)
    ink = mix(INK, tone, 0.35)

    def g(p):
        p.poly([(L * 0.10, H * 0.52), (L * 0.0, H * 0.22), (L * 0.035, H * 0.52),
                (L * 0.0, H * 0.80)], fill=tone, outline=ink, width=2.0)
        p.poly([(L * 0.52, H * 0.34), (L * 0.60, H * 0.06), (L * 0.68, H * 0.36)],
               fill=tone, outline=ink, width=2.0)
        p.ell(L * 0.06, H * 0.24, L * 1.02, H * 0.84, fill=tone, outline=ink, width=2.2)
        p.circ(L * 0.86, H * 0.44, L * 0.028, fill=PUTIH)
        p.circ(L * 0.865, H * 0.44, L * 0.016, fill=INK)
    return raster(W, H, g, ss=3)


def paus_spr(L=620, tone=(62, 86, 106), perut=None):
    """Paus (mangsa megalodon): tubuh torpedo ramping, ekor MENDATAR, alur perut.

    Profil dibangun dari `catmull` pada 10 titik seperti hiu, jadi tidak pernah
    terlihat seperti oval. Ekor digambar sebagai dua lobus horizontal (bukan
    ekor ikan) — pembeda visual paling jelas antara paus dan hiu.
    """
    perut = perut or mix((238, 240, 232), tone, 0.08)
    W, H = int(L * 1.26), int(L * 0.52)
    ink = mix(INK, tone, 0.20)
    cx0, cy0 = L * 0.14, H * 0.50
    Hc = L * 0.36

    def x_of(u):
        return cx0 + u * L

    def y_of(v):
        return cy0 + (v - 0.44) * Hc

    top = [(0.03, 0.46), (0.10, 0.34), (0.24, 0.25), (0.44, 0.20),
           (0.62, 0.19), (0.78, 0.22), (0.90, 0.29), (0.985, 0.40)]
    bot = [(0.985, 0.49), (0.92, 0.60), (0.76, 0.70), (0.56, 0.76),
           (0.36, 0.77), (0.20, 0.72), (0.09, 0.61), (0.03, 0.53)]
    atas = catmull([(x_of(u), y_of(v)) for u, v in top], n=9)
    bawah = catmull([(x_of(u), y_of(v)) for u, v in bot], n=9)

    def g(p):
        # ekor horizontal (dua lobus)
        fl = [(x_of(0.04), y_of(0.44)), (x_of(-0.075), y_of(0.16)),
              (x_of(-0.035), y_of(0.44)), (x_of(-0.075), y_of(0.74)),
              (x_of(0.045), y_of(0.52))]
        p.poly(catmull(fl, 7, closed=True), fill=mix(tone, INK, 0.10),
               outline=ink, width=3.2)
        # sirip punggung kecil melengkung
        p.poly(catmull([(x_of(0.585), y_of(0.22)), (x_of(0.615), y_of(0.06)),
                        (x_of(0.665), y_of(0.24))], 7, closed=True),
               fill=mix(tone, INK, 0.06), outline=ink, width=3.0)
        # sirip dada panjang
        p.poly(catmull([(x_of(0.700), y_of(0.62)), (x_of(0.585), y_of(0.88)),
                        (x_of(0.640), y_of(0.66))], 7, closed=True),
               fill=mix(tone, INK, 0.16), outline=ink, width=3.0)
        p.poly(atas + bawah, fill=tone, outline=ink, width=3.4)
    spr = raster(W, H, g, ss=2)

    # perut: belly_mask menempel tepi bawah siluet
    mask_badan = mask_poli(W, H, [atas + bawah], ss=1)
    bm = belly_mask(mask_badan, frac=0.56)
    lap = np.zeros((H, W, 4), np.uint8)
    lap[..., :3] = perut
    lap[..., 3] = bm
    komposit(spr, lap)

    det = raster(W, H, g2, ss=2)
    # KLIP: semua detail wajib berada di dalam siluet badan (v18 awal: garis
    # perut dan mulut keluar badan karena tidak diklip)
    det[..., 3] = (det[..., 3].astype(np.uint16) * mask_badan.astype(np.uint16) // 255).astype(np.uint8)
    komposit(spr, det)
    return pangkas(spr)


def hiu_bayi_spr(L=200, tone=None):
    """Ikan kecil / hiu muda untuk latar (lebih sederhana, tetap beroutline)."""
    tone = tone or mix(HIU, AIR_3, 0.35)
    W, H = int(L * 1.2), int(L * 0.62)
    ink = mix(INK, tone, 0.35)

    def g(p):
        p.poly([(L * 0.10, H * 0.52), (L * 0.0, H * 0.22), (L * 0.035, H * 0.52),
                (L * 0.0, H * 0.80)], fill=tone, outline=ink, width=2.0)
        p.poly([(L * 0.52, H * 0.34), (L * 0.60, H * 0.06), (L * 0.68, H * 0.36)],
               fill=tone, outline=ink, width=2.0)
        p.ell(L * 0.06, H * 0.24, L * 1.02, H * 0.84, fill=tone, outline=ink, width=2.2)
        p.circ(L * 0.86, H * 0.44, L * 0.028, fill=PUTIH)
        p.circ(L * 0.865, H * 0.44, L * 0.016, fill=INK)
    return raster(W, H, g, ss=3)


def paus_spr(L=620, tone=(62, 86, 106), perut=None):
    """Paus (mangsa megalodon): tubuh torpedo ramping, ekor MENDATAR, alur perut.

    Profil dibangun dari `catmull` pada 10 titik seperti hiu, jadi tidak pernah
    terlihat seperti oval. Ekor digambar sebagai dua lobus horizontal (bukan
    ekor ikan) — pembeda visual paling jelas antara paus dan hiu.
    """
    perut = perut or mix((238, 240, 232), tone, 0.08)
    W, H = int(L * 1.26), int(L * 0.52)
    ink = mix(INK, tone, 0.20)
    cx0, cy0 = L * 0.14, H * 0.50
    Hc = L * 0.36

    def x_of(u):
        return cx0 + u * L

    def y_of(v):
        return cy0 + (v - 0.44) * Hc

    top = [(0.03, 0.46), (0.10, 0.34), (0.24, 0.25), (0.44, 0.20),
           (0.62, 0.19), (0.78, 0.22), (0.90, 0.29), (0.985, 0.40)]
    bot = [(0.985, 0.49), (0.92, 0.60), (0.76, 0.70), (0.56, 0.76),
           (0.36, 0.77), (0.20, 0.72), (0.09, 0.61), (0.03, 0.53)]
    atas = catmull([(x_of(u), y_of(v)) for u, v in top], n=9)
    bawah = catmull([(x_of(u), y_of(v)) for u, v in bot], n=9)

    def g(p):
        # ekor horizontal (dua lobus)
        fl = [(x_of(0.04), y_of(0.44)), (x_of(-0.075), y_of(0.16)),
              (x_of(-0.035), y_of(0.44)), (x_of(-0.075), y_of(0.74)),
              (x_of(0.045), y_of(0.52))]
        p.poly(catmull(fl, 7, closed=True), fill=mix(tone, INK, 0.10),
               outline=ink, width=3.2)
        # sirip punggung kecil melengkung
        p.poly(catmull([(x_of(0.585), y_of(0.22)), (x_of(0.615), y_of(0.06)),
                        (x_of(0.665), y_of(0.24))], 7, closed=True),
               fill=mix(tone, INK, 0.06), outline=ink, width=3.0)
        # sirip dada panjang
        p.poly(catmull([(x_of(0.700), y_of(0.62)), (x_of(0.585), y_of(0.88)),
                        (x_of(0.640), y_of(0.66))], 7, closed=True),
               fill=mix(tone, INK, 0.16), outline=ink, width=3.0)
        p.poly(atas + bawah, fill=tone, outline=ink, width=3.4)
    spr = raster(W, H, g, ss=2)

    # perut + alur (throat grooves): belly_mask menempel tepi bawah siluet
    mask_badan = mask_poli(W, H, [atas + bawah], ss=1)
    bm = belly_mask(mask_badan, frac=0.58)
    bm_alur = bm.copy()
    r = rng(21)
    for i in range(4):
        y0a = int(H * (0.60 + i * 0.055))
        bm_alur[y0a:y0a + 2, :] = np.where(bm[y0a:y0a + 2, :] > 0, 0, 0)
    lap = np.zeros((H, W, 4), np.uint8)
    lap[..., :3] = perut
    lap[..., 3] = bm
    komposit(spr, lap)

    det = raster(W, H, g2, ss=2)
    # KLIP: semua detail wajib berada di dalam siluet badan (v18 awal: garis
    # perut dan mulut keluar badan karena tidak diklip)
    det[..., 3] = (det[..., 3].astype(np.uint16) * mask_badan.astype(np.uint16) // 255).astype(np.uint8)
    komposit(spr, det)
    return pangkas(spr)


def hiu_bayi_spr(L=200, tone=None):
    """Ikan kecil / hiu muda untuk latar (lebih sederhana, tetap beroutline)."""
    tone = tone or mix(HIU, AIR_3, 0.35)
    W, H = int(L * 1.2), int(L * 0.62)
    ink = mix(INK, tone, 0.35)

    def g(p):
        p.poly([(L * 0.10, H * 0.52), (L * 0.0, H * 0.22), (L * 0.035, H * 0.52),
                (L * 0.0, H * 0.80)], fill=tone, outline=ink, width=2.0)
        p.poly([(L * 0.52, H * 0.34), (L * 0.60, H * 0.06), (L * 0.68, H * 0.36)],
               fill=tone, outline=ink, width=2.0)
        p.ell(L * 0.06, H * 0.24, L * 1.02, H * 0.84, fill=tone, outline=ink, width=2.2)
        p.circ(L * 0.86, H * 0.44, L * 0.028, fill=PUTIH)
        p.circ(L * 0.865, H * 0.44, L * 0.016, fill=INK)
    return raster(W, H, g, ss=3)


def paus_spr(L=620, tone=(62, 86, 106), perut=None):
    """Paus (mangsa megalodon): tubuh torpedo ramping, ekor MENDATAR, alur perut.

    Profil dibangun dari `catmull` pada 10 titik seperti hiu, jadi tidak pernah
    terlihat seperti oval. Ekor digambar sebagai dua lobus horizontal (bukan
    ekor ikan) — pembeda visual paling jelas antara paus dan hiu.
    """
    perut = perut or mix((238, 240, 232), tone, 0.08)
    W, H = int(L * 1.26), int(L * 0.52)
    ink = mix(INK, tone, 0.20)
    cx0, cy0 = L * 0.14, H * 0.50
    Hc = L * 0.36

    def x_of(u):
        return cx0 + u * L

    def y_of(v):
        return cy0 + (v - 0.44) * Hc

    top = [(0.03, 0.46), (0.10, 0.34), (0.24, 0.25), (0.44, 0.20),
           (0.62, 0.19), (0.78, 0.22), (0.90, 0.29), (0.985, 0.40)]
    bot = [(0.985, 0.49), (0.92, 0.60), (0.76, 0.70), (0.56, 0.76),
           (0.36, 0.77), (0.20, 0.72), (0.09, 0.61), (0.03, 0.53)]
    atas = catmull([(x_of(u), y_of(v)) for u, v in top], n=9)
    bawah = catmull([(x_of(u), y_of(v)) for u, v in bot], n=9)

    def g(p):
        # ekor horizontal (dua lobus)
        fl = [(x_of(0.04), y_of(0.44)), (x_of(-0.075), y_of(0.16)),
              (x_of(-0.035), y_of(0.44)), (x_of(-0.075), y_of(0.74)),
              (x_of(0.045), y_of(0.52))]
        p.poly(catmull(fl, 7, closed=True), fill=mix(tone, INK, 0.10),
               outline=ink, width=3.2)
        # sirip punggung kecil melengkung
        p.poly(catmull([(x_of(0.585), y_of(0.22)), (x_of(0.615), y_of(0.06)),
                        (x_of(0.665), y_of(0.24))], 7, closed=True),
               fill=mix(tone, INK, 0.06), outline=ink, width=3.0)
        # sirip dada panjang
        p.poly(catmull([(x_of(0.700), y_of(0.62)), (x_of(0.585), y_of(0.88)),
                        (x_of(0.640), y_of(0.66))], 7, closed=True),
               fill=mix(tone, INK, 0.16), outline=ink, width=3.0)
        p.poly(atas + bawah, fill=tone, outline=ink, width=3.4)
    spr = raster(W, H, g, ss=2)

    # perut + alur (throat grooves) diklip mask badan
    mask_badan = mask_poli(W, H, [atas + bawah], ss=1)
    lap = np.zeros((H, W, 4), np.uint8)
    im2 = Image.new("L", (W, H), 0)
    d2 = ImageDraw.Draw(im2)
    belly = [(x, y) for x, y in bawah]
    naik = [(x, y - Hc * 0.24) for x, y in belly]
    d2.polygon(belly + naik[::-1], fill=255)
    for i in range(4):
        d2.line(catmull([(x_of(0.93), y_of(0.54) + i * Hc * 0.032),
                         (x_of(0.74), y_of(0.63) + i * Hc * 0.026),
                         (x_of(0.55), y_of(0.665) + i * Hc * 0.018)], n=6),
                fill=0, width=2)
    m = (np.array(im2).astype(np.uint16) * mask_badan.astype(np.uint16) // 255).astype(np.uint8)
    lap[..., :3] = perut
    lap[..., 3] = m
    komposit(spr, lap)

    def g2(p):
        # mata
        p.circ(x_of(0.905), y_of(0.425), L * 0.0115, fill=PUTIH, outline=ink, width=1.4)
        p.circ(x_of(0.907), y_of(0.425), L * 0.0068, fill=INK)
        # mulut lebar khas paus
        p.line(catmull([(x_of(0.985), y_of(0.505)), (x_of(0.90), y_of(0.545)),
                        (x_of(0.80), y_of(0.552))], n=7), with_a(INK, 0.72), 2.6)
        # lubang sembur
        p.arc(x_of(0.86) - 6, y_of(0.235) - 5, x_of(0.86) + 6, y_of(0.235) + 5,
              190, 350, with_a(INK, 0.55), 2.2)
        # bercak punggung
        r = rng(77)
        for i in range(7):
            p.circ(x_of(r.uniform(0.30, 0.80)), y_of(r.uniform(0.26, 0.40)),
                   r.uniform(1.6, 3.4), fill=with_a(mix(tone, PUTIH, 0.35), 0.35))
    det = raster(W, H, g2, ss=2)
    det[..., 3] = (det[..., 3].astype(np.uint16) * mask_badan.astype(np.uint16) // 255).astype(np.uint8)
    komposit(spr, det)
    return pangkas(spr)


def sembur_spr(h=150, tone=None):
    """Semburan air dari lubang sembur (partikel V) untuk paus yang berenang naik."""
    tone = tone or (250, 250, 244)
    W = int(h * 0.8)
    def g(p):
        for i in range(9):
            f = i / 8.0
            x = W / 2 + (f - 0.5) * W * 0.85
            y = h - f * h * 0.95 - 6
            r = 5.5 * (1 - f * 0.55)
            p.circ(x, y, r, fill=with_a(tone, 0.55 + 0.35 * (1 - f)))
    return raster(W, h, g, ss=3)


def penyelam_spr(H=360, tone=(48, 66, 96), masker=TERRA):
    """Penyelam (pembanding skala 1,8 m): figur beroutline, bukan stik.

    Dibangun dari sendi: kepala + masker, tabung oksigen, torso meruncing,
    dua lengan (satu ke depan), dua kaki dengan sirip. Arah hadap KE KANAN.
    """
    W = int(H * 0.52)
    ink = mix(INK, tone, 0.22)
    kulit = (226, 190, 160)
    sirip = mix(AMBER, TERRA, 0.30)

    def g(p):
        # tabung oksigen (di punggung = kiri)
        p.rrect(W * 0.10, H * 0.20, W * 0.26, H * 0.46, W * 0.07,
                fill=mix(AMBER, PUTIH, 0.15), outline=ink, width=2.0)
        p.line([(W * 0.11, H * 0.26), (W * 0.25, H * 0.26)], with_a(INK, 0.35), 1.6)
        # kepala
        p.circ(W * 0.44, H * 0.12, H * 0.070, fill=kulit, outline=ink, width=2.0)
        # masker
        p.rrect(W * 0.40, H * 0.085, W * 0.56, H * 0.145, H * 0.022,
                fill=mix(NAVY, PUTIH, 0.18), outline=ink, width=1.6)
        # snorkel
        p.line([(W * 0.40, H * 0.105), (W * 0.33, H * 0.02), (W * 0.38, H * 0.01)],
               mix(TERRA, INK, 0.15), 4.0)
        # torso (meruncing ke pinggang)
        torso = [(W * 0.40, H * 0.18), (W * 0.50, H * 0.19), (W * 0.50, H * 0.34),
                 (W * 0.44, H * 0.44), (W * 0.34, H * 0.44), (W * 0.33, H * 0.34)]
        p.poly(catmull(torso, 8, closed=True), fill=tone, outline=ink, width=2.2)
        # sabuk
        p.line([(W * 0.34, H * 0.40), (W * 0.50, H * 0.395)], mix(TERRA, INK, 0.2), 3.0)
        # lengan kanan ke depan (mengayuh)
        p.line(catmull([(W * 0.49, H * 0.22), (W * 0.62, H * 0.19),
                        (W * 0.72, H * 0.24)], n=6), tone, 8.0, joint="curve")
        p.circ(W * 0.73, H * 0.245, H * 0.022, fill=kulit, outline=ink, width=1.4)
        # lengan kiri ke bawah
        p.line(catmull([(W * 0.36, H * 0.23), (W * 0.26, H * 0.32),
                        (W * 0.30, H * 0.42)], n=6), tone, 8.0, joint="curve")
        p.circ(W * 0.30, H * 0.43, H * 0.021, fill=kulit, outline=ink, width=1.4)
        # kaki + sirip
        p.line(catmull([(W * 0.42, H * 0.44), (W * 0.46, H * 0.62),
                        (W * 0.52, H * 0.78)], n=6), tone, 9.0, joint="curve")
        p.line(catmull([(W * 0.36, H * 0.44), (W * 0.32, H * 0.62),
                        (W * 0.30, H * 0.80)], n=6), tone, 9.0, joint="curve")
        p.poly([(W * 0.50, H * 0.77), (W * 0.78, H * 0.86), (W * 0.50, H * 0.87)],
               fill=sirip, outline=ink, width=1.8)
        p.poly([(W * 0.30, H * 0.79), (W * 0.10, H * 0.90), (W * 0.30, H * 0.90)],
               fill=sirip, outline=ink, width=1.8)
    return raster(W, H, g, ss=3)


def gelembung_spr(n=7, w=70, h=190, seed=4):
    """Kolom gelembung naik dari penyelam (sprite berulang, tanpa state)."""
    r = rng(seed)
    out = np.zeros((h, w, 4), np.uint8)

    def g(p):
        for i in range(n):
            x = r.uniform(w * 0.2, w * 0.8)
            y = h - (i + 0.5) * h / n + r.uniform(-6, 6)
            rr = r.uniform(2.5, 6.5) * (1 - i / (n * 1.6))
            p.circ(x, y, rr, fill=with_a((255, 255, 250), 0.72),
                   outline=with_a((255, 255, 255), 0.95), width=1.4)
    return raster(w, h, g, ss=3)


TONE_OUT = (146, 118, 76)


def gigi_spr(h=120, tone=GIGI, akar=True, gerigi=True, sudut=0.0, outline=True,
             lebar_r=0.64):
    """Satu gigi hiu beroutline — kerucut dengan satu apex + akar dua lobus.

    Sisi dihitung dari satu fungsi radius monoton (bukan spline bebas) supaya
    siluet tidak pernah melebar di tengah. Akar dibuat dua lobus turun dengan
    takik V naik di antaranya. Semua garis tekstur diklip ke siluet, jadi tidak
    ada goresan yang keluar badan gigi.
    """
    w = h * lebar_r
    W, H = int(w * 1.6) + 16, int(h * 1.62) + 16
    ink = mix(INK, GIGI_T, 0.28)
    cx = W / 2.0
    pangkal = H * 0.80
    apex_y = pangkal - h
    s2 = w / 2.0

    def sisi(arah):
        out = []
        for i in range(9):
            f = i / 8.0
            r = s2 * (1.0 - f) ** 0.74      # sedikit cembung: mahkota, bukan segitiga kaku
            out.append((cx + arah * max(r, 1.4), pangkal - h * f))
        return out

    kanan, kiri = sisi(+1), sisi(-1)
    if akar:
        dasar = [(cx + s2 * 0.98, pangkal + h * 0.02),
                 (cx + s2 * 0.62, pangkal + h * 0.21),
                 (cx + s2 * 0.20, pangkal + h * 0.19),
                 (cx, pangkal + h * 0.10),
                 (cx - s2 * 0.20, pangkal + h * 0.19),
                 (cx - s2 * 0.62, pangkal + h * 0.21),
                 (cx - s2 * 0.98, pangkal + h * 0.02)]
    else:
        dasar = [(cx + s2 * 0.60, pangkal + h * 0.05),
                 (cx, pangkal + h * 0.09),
                 (cx - s2 * 0.60, pangkal + h * 0.05)]
    pts = kanan + [(cx, apex_y)] + kiri[::-1] + dasar
    if sudut:
        cr, sr = math.cos(sudut), math.sin(sudut)
        pts = [(cx + (x - cx) * cr - (y - pangkal) * sr,
                pangkal + (x - cx) * sr + (y - pangkal) * cr) for x, y in pts]

    def gb(p):
        p.poly(pts, fill=tone, outline=(TONE_OUT if outline else None), width=2.8)
    spr = raster(W, H, gb, ss=3)
    mask = (spr[..., 3] > 6)

    if gerigi:
        def gd(p):
            # enamel: gradasi lembut dari pangkal (tanpa tepi keras)
            p.poly([(cx - s2 * 1.04, pangkal + h * 0.04),
                    (cx - s2 * 0.86, pangkal - h * 0.18),
                    (cx + s2 * 0.86, pangkal - h * 0.18),
                    (cx + s2 * 1.04, pangkal + h * 0.04)],
                   fill=with_a(mix(tone, GIGI_T, 0.42), 0.26))
            p.line([(cx - s2 * 0.34, pangkal - h * 0.22), (cx - s2 * 0.12, pangkal - h * 0.66)],
                   with_a(PUTIH, 0.55), 3.0)
        det = raster(W, H, gd, ss=3)
        det[..., :3] = gblur(det[..., :3], 2.2)
        det[..., 3] = (det[..., 3] * mask).astype(np.uint8)
        komposit(spr, det)
    return pangkas(spr)


def deret_gigi(n=7, h=86, jarak=0.66, sudut=(-0.10, 0.10), tone=GIGI):
    """Deret gigi rahang: n gigi berselang-seling miring, seperti busur rahang."""
    sp = [gigi_spr(h, tone=tone, sudut=lerp(sudut[0], sudut[1], i / max(1, n - 1)))
          for i in range(n)]
    W = int(n * sp[0].shape[1] * jarak + sp[0].shape[1] * 0.4) + 8
    H = int(h * 1.5) + 8
    out = np.zeros((H, W, 4), np.uint8)
    x = 4.0
    for i, s in enumerate(sp):
        blit(out, s, x, 4 + h * 0.10 * math.sin(i * 1.1))
        x += s.shape[1] * jarak
    return out


# ============================================================== 7. kartu & HUD

@functools.lru_cache(maxsize=64)
def kartu_spr(w, h, aksen=TERRA, sudut=30, isi=KREM, bayang=True, pita=True,
              sheen=0.55, garis=2.6):
    """Kartu krem beroutline dengan bayangan berlapis + pita aksen.

    Susunan: bayangan (kontak + ambient) -> pelat krem -> sapuan kertas ->
    outline tinta -> pita aksen. Semua lapisan DIGABUNG dengan aturan "over",
    jadi tidak ada bagian yang tembus pandang karena `rounded_rectangle` PIL
    menimpa alpha (bug v18 awal: kartu bolong).
    """
    pad = 46 if bayang else 5
    w, h = int(w), int(h)
    W, H = w + pad * 2, h + pad * 2
    out = np.zeros((H, W, 4), np.uint8)
    if bayang:
        kontak = np.zeros((H, W), np.uint8)
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).rounded_rectangle([pad + 1, pad + 11, pad + w, pad + h + 9],
                                            radius=sudut, fill=64)
        ambient = Image.new("L", (W, H), 0)
        ImageDraw.Draw(ambient).rounded_rectangle([pad - 2, pad + 2, pad + w + 2, pad + h + 30],
                                                  radius=sudut, fill=46)
        sh = np.maximum(np.array(gblur(np.array(im), 6)), np.array(gblur(np.array(ambient), 22)))
        out[..., :3] = (20, 36, 42)
        out[..., 3] = (sh.astype(np.float32) * 0.90).astype(np.uint8)

    # pelat krem
    m = mask_rrect(w, h, sudut)
    pelat = np.zeros((h, w, 4), np.uint8)
    pelat[..., :3] = isi
    pelat[..., 3] = m
    # sapuan kertas di bagian atas (gradasi putih -> transparan)
    ys = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    sa = (np.clip(1.0 - ys / 0.55, 0, 1) ** 1.3) * sheen * 255
    sheen_l = np.zeros((h, w, 4), np.uint8)
    sheen_l[..., :3] = mix(isi, PUTIH, 0.85)
    sheen_l[..., 3] = (sa * (m.astype(np.float32) / 255)).astype(np.uint8)
    komposit(pelat, sheen_l)
    blit(out, pelat, pad, pad)

    # outline + pita
    def g(p):
        p.rrect(0, 0, w, h, sudut, outline=INK, width=garis)
    garis_spr = raster(w, h, g, ss=3)
    blit(out, garis_spr, pad, pad)
    if pita:
        def g2(p):
            p.rrect(0, 0, w, 13, 6.5, fill=aksen)
            p.rrect(sudut * 0.5, 0, w - sudut * 0.5, 13, 0, fill=aksen)
        pita_spr = raster(w, 13, g2, ss=3)
        # klip pita ke bentuk kartu (sudut atas membulat)
        pm = mask_rrect(w, 13, 6.5)
        pita_spr[..., 3] = (pita_spr[..., 3].astype(np.uint16) *
                            np.minimum(pm, 255).astype(np.uint16) // 255).astype(np.uint8)
        blit(out, pita_spr, pad, pad)
    return out


@functools.lru_cache(maxsize=512)
def label_spr(teks, warna=INK, isi=None, outline=None, size=27, name=F_SEMI,
              pad_x=18, pad_y=10, radius=14, aksen=None):
    """Label pil: teks kecil dengan latar krem / aksen (untuk anotasi angka)."""
    f = fit_size(teks, name, size, 520)
    tw_ = tw(teks, name, f)
    th_ = f * 1.42
    w = int(tw_ + pad_x * 2)
    h = int(th_ + pad_y * 0.7)
    isi = isi if isi is not None else mix(KREM, PUTIH, 0.35)
    def g(p):
        p.rrect(0, 0, w, h, radius, fill=isi,
                outline=outline if outline is not None else mix(INK, isi, 0.15), width=2.2)
        if aksen:
            p.circ(pad_x * 0.55, h / 2, 4.5, fill=aksen)
    spr = raster(w, h, g, ss=3)
    m = mask(teks, name, f)
    hh, ww = m.shape
    rgba = np.zeros((hh, ww, 4), np.uint8)
    rgba[..., :3] = warna
    rgba[..., 3] = m
    blit(spr, rgba, (w - ww) / 2, (h - hh) / 2)
    return spr


def angka_spr(teks, size=150, warna=INK, name=F_BOLD, tracking=-2):
    """Angka besar dengan outline putih tipis (kontras di atas air)."""
    return spr_text(teks, warna, name, size, tracking=tracking,
                    shadow=mix(PUTIH, KREM, 0.4), shadow_blur=0, shadow_off=(0, 0),
                    shadow_a=0)


def hud_spr(w=1080, episode="LAUT PURBA"):
    """Merek + lencana episode di bagian atas (digambar sekali per sesi)."""
    H = 96
    spr = np.zeros((H, w, 4), np.uint8)
    # titik merek
    def g(p):
        p.circ(54, 46, 7, fill=TERRA)
        p.rrect(72, 30, 214, 62, 10, fill=None)
    m = mask("KlikTahu", F_BOLD, 40)
    tt = np.zeros((m.shape[0], m.shape[1], 4), np.uint8)
    tt[..., :3] = INK
    tt[..., 3] = m
    blit(spr, tt, 72, 44 - m.shape[0] / 2)
    # lencana episode (kanan)
    lab = label_spr(episode, warna=KREM, isi=mix(INK, HIU, 0.25), outline=INK, size=26,
                    name=F_BOLD, pad_x=20, pad_y=9, radius=22)
    blit(spr, lab, w - lab.shape[1] - 46, (H - lab.shape[0]) / 2)
    return spr


def progres_spr(n, aktif, warna=TERRA, nonaktif=None):
    """Titik progres scene (8 titik) — penanda babak yang halus, bukan HUD ramai."""
    nonaktif = nonaktif or mix(INK, KREM, 0.62)
    W, H = n * 26 + 10, 22
    def g(p):
        for i in range(n):
            c = warna if i <= aktif else nonaktif
            r = 5.0 if i == aktif else 4.0
            p.circ(12 + i * 26, H / 2, r, fill=c)
    return raster(W, H, g, ss=3)


# ============================================================== 8. diagram

def panah_spr(panjang=220, tebal=9, warna=TERRA, kepala=26):
    """Panah datar dengan kepala segitiga (untuk penanda arah & sebab-akibat)."""
    W, H = int(panjang + kepala * 1.6), int(kepala * 2.2)
    def g(p):
        y = H / 2
        p.rrect(2, y - tebal / 2, panjang, y + tebal / 2, tebal / 2, fill=warna)
        p.poly([(panjang - 2, y - kepala), (panjang + kepala * 1.5, y),
                (panjang - 2, y + kepala)], fill=warna)
    return raster(W, H, g, ss=3)


def kurung_spr(panjang=200, tebal=6, warna=INK):
    """Kurung ukur (|----|) dengan ujung tegak, untuk jarak dan panjang."""
    W, H = int(panjang + 16), 46
    def g(p):
        p.line([(10, H / 2), (panjang + 6, H / 2)], warna, tebal)
        p.line([(10, 6), (10, H - 6)], warna, tebal)
        p.line([(panjang + 6, 6), (panjang + 6, H - 6)], warna, tebal)
    return raster(W, H, g, ss=3)


def garis_ukur(k, x0, x1, y, warna=INK, tebal=4, ujung=16):
    """Garis ukur dengan ujung tegak, digambar langsung ke kanvas."""
    cv2.line(k.a, (int(x0), int(y)), (int(x1), int(y)), warna, tebal, cv2.LINE_AA)
    for x in (x0, x1):
        cv2.line(k.a, (int(x), int(y - ujung)), (int(x), int(y + ujung)), warna, tebal, cv2.LINE_AA)


def gumpal(k, cx, cy, r, warna, alpha=0.9):
    """Bulatan warnya untuk penanda timeline (dengan outline tinta)."""
    cv2.circle(k.a, (int(cx), int(cy)), int(r + 2.5), INK, -1, cv2.LINE_AA)
    cv2.circle(k.a, (int(cx), int(cy)), int(r), warna, -1, cv2.LINE_AA)


def silang(k, cx, cy, r, warna=TERRA, tebal=7):
    """Tanda silang (untuk 'bukan ini')."""
    d = r * 0.72
    cv2.line(k.a, (int(cx - d), int(cy - d)), (int(cx + d), int(cy + d)), warna, tebal, cv2.LINE_AA)
    cv2.line(k.a, (int(cx + d), int(cy - d)), (int(cx - d), int(cy + d)), warna, tebal, cv2.LINE_AA)


def centang(k, cx, cy, r, warna=RUMPUT, tebal=8):
    """Tanda centang (untuk 'ini yang benar')."""
    cv2.line(k.a, (int(cx - r * 0.7), int(cy)), (int(cx - r * 0.1), int(cy + r * 0.6)), warna, tebal, cv2.LINE_AA)
    cv2.line(k.a, (int(cx - r * 0.1), int(cy + r * 0.6)), (int(cx + r * 0.8), int(cy - r * 0.7)), warna, tebal, cv2.LINE_AA)


# ============================================================== 9. selftest

def _selftest():
    import time
    from mesin_v18_inti import lut_grade
    k = Kanvas(1080, 1920, KERTAS)
    t0 = time.time()
    langit(k, senja=0.34)
    air(k)
    permukaan(k, 0.0)
    berkas_cahaya(k, 0.0)
    dasar_laut(k)
    kaustik_dasar(k, kaustik_spr(), 0.0, 1740, 1920, 0.25)
    rumput(k, 150, 1840, 300, 0.0)
    rumput(k, 930, 1850, 250, 0.0, tone=RUMPUT_D)
    batu(k, 700, 1790, 80, 40)
    blit(k.a, hiu_spr(720, "megalodon", gigi_baris=9), 150, 660)
    blit(k.a, paus_spr(520), 330, 1250, 0.95)
    blit(k.a, penyelam_spr(300), 830, 980)
    blit(k.a, deret_gigi(7, 82), 80, 380)
    kartu = kartu_spr(860, 240, aksen=TERRA)
    blit(k.a, kartu, 110, 1400)
    blit(k.a, spr_text("HIDUP 20 JUTA TAHUN", INK, F_BOLD, 58, tracking=-0.5), 175, 1480)
    blit(k.a, hud_spr(), 0, 0)
    print(f"latar+figur: {(time.time()-t0)*1000:.0f} ms")
    t1 = time.time()
    lut = lut_grade()
    for i in range(20):
        k2 = k.salin()
        k2.lut(lut)
    print(f"salin+LUT: {(time.time()-t1)/20*1000:.2f} ms/frame")
    Image.fromarray(k.a).save("/tmp/v18_dunia.png")
    Image.fromarray(hiu_spr(900, "megalodon", gigi_baris=11)).save("/tmp/v18_hiu2.png")
    Image.fromarray(paus_spr(600)).save("/tmp/v18_paus.png")
    Image.fromarray(penyelam_spr(420)).save("/tmp/v18_selam.png")
    Image.fromarray(deret_gigi(7, 90)).save("/tmp/v18_gigi.png")
    Image.fromarray(kartu_spr(700, 220)).save("/tmp/v18_kartu.png")
    print("-> /tmp/v18_dunia.png + detail")


if __name__ == "__main__":
    _selftest()
