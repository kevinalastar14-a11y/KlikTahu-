#!/usr/bin/env python3
"""mesin_v15_ep54.py — Ep54 "Mata Minus Tidak Bisa Sembuh — Bola Matanya Sudah Memanjang"

Mesin ILUSTRASI penuh layar (v15). Delapan dunia: kelas buram, penampang bola mata,
tiga tahap memanjang, jendela dalam-vs-luar, halaman sekolah, ruang periksa mata,
retina yang tertarik, lalu kembali ke kelas.

Satu anak yang sama muncul di kelas, di jendela sebelah dalam, dan di halaman —
kontinuitas karakter yang tidak ada di Ep53.

Selftest:  python3 mesin_v15_ep54.py
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import diagrams as D
import mesin_v11 as M11
import mesin_v12 as M
import mesin_v15_ilustrasi as V
from diagrams import (INK, CREAM, WHITE, MUTED, mix, clamp, seg, esmooth, eo,
                      font, tw, tlh, paste_c, paste_r, rrect_on, line_on, dot_on,
                      ring_on, poly_on)
from mesin_v15_ilustrasi import (KREM, LANGIT, LANGIT_2, SENJA, TEAL, TEAL_D, TEAL_L,
                                 PASIR, PASIR_D, TERRA, TERRA_D, OLIVE, OLIVE_D, NAVY,
                                 NAVY_D, LANGIT_MALAM, AMBER_H, grad_v, elips_vol, bentuk,
                                 awan, gunung, bukit, laut, pasir, cahaya_matahari,
                                 matahari, pohon_kelapa, perahu, rumah, orang, layangan,
                                 angin, hujan, tetes, bintang_laut, judul, kartu_judul,
                                 sumber, gelembung, angka_besar, inset, garis_dasar,
                                 butir_terbang, kurva, garis_tebal, S, mask_outline)

SUMBER = "Sumber: WHO · IMI · AAO · Kemenkes"
Y_KARTU = 1490

# ------------------------------------------------------------------ cache dasar
_BASE = {}
_CACHE_DIR = os.path.join(os.environ.get("KT_BUILD", "build"), "v15base")


def _base(nama, builder):
    """Dasar adegan: cache memori -> cache disk (PNG) -> gambar baru."""
    key = (nama, round(D.SS, 6))
    im = _BASE.get(key)
    if im is not None:
        return im
    path = os.path.join(_CACHE_DIR, f"{nama}_{int(round(D.SS * 1000))}.png")
    if os.path.exists(path):
        try:
            im = Image.open(path).convert("RGB")
            im.load()
            _BASE[key] = im
            return im
        except Exception:
            pass
    im = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), CREAM)
    builder(im)
    _BASE[key] = im
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        im.save(path)
    except Exception:
        pass
    return im


def latar_bawah(im, tone, y0=1240, butir=70, props=True, seed=54):
    """Isi bidang bawah sampai tepi kanvas (tidak ada pita kosong)."""
    h = 1920 - y0
    band = grad_v(1080, h, [(0.0, mix(tone, WHITE, 0.26)), (0.55, tone), (1.0, mix(tone, INK, 0.16))], seed=seed)
    im.paste(band, (0, int(round(S(y0)))))
    rng = np.random.default_rng(seed)
    for i in range(butir):
        x = rng.random() * 1080
        y = y0 + rng.random() * h
        dot_on(im, x, y, 1.3 + rng.random() * 1.7, mix(tone, INK, 0.35), 0.09 + rng.random() * 0.07)
    if props:
        for i in range(9):
            x = 40 + i * 122 + rng.random() * 30
            y = 1866 + rng.random() * 30
            if i % 3 == 0:
                elips_vol(im, x, y, 13 + rng.random() * 9, 7 + rng.random() * 5,
                          mix(tone, INK, 0.28), outline=mix(tone, INK, 0.55), ow=2.0, light=0.20)
            else:
                for k in range(3):
                    garis_tebal(im, [(x + k * 7, y + 12), (x + k * 7 - 5 + rng.random() * 4, y - 15 - rng.random() * 11)],
                                mix(OLIVE, tone, 0.35), 3.0, 0.5)


def bayangan_kartu(im, y=1618, w=880, alpha=64):
    lay = Image.new("RGBA", (int(S(1080)), int(S(1920))), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([S(540 - w / 2), S(y), S(540 + w / 2), S(y + 26)],
                                          radius=S(14), fill=(28, 24, 22, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(S(13)))
    im.paste(lay.convert("RGB"), (0, 0), lay)


def _blur_area(im, box, r):
    """Kaburkan satu bidang (mata minus: yang jauh buram, yang dekat tajam)."""
    x0, y0, x1, y1 = [int(round(S(v))) for v in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(im.size[0], x1), min(im.size[1], y1)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return
    reg = im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(max(1, int(round(S(r))))))
    im.paste(reg, (x0, y0))


# ------------------------------------------------------------------ objek khas
def kacamata(img, x, y, s=1.0, rot=0.0, tone=None, al=1.0):
    """Kacamata kartun: dua lensa membulat + jembatan + tangkai."""
    tone = tone or INK
    w, h = 96 * s, 74 * s
    for sgn in (-1, 1):
        cx = x + sgn * (w * 0.62)
        rrect_on(img, cx - w / 2, y - h / 2, cx + w / 2, y + h / 2, h * 0.42,
                 mix(TEAL_L, WHITE, 0.55), 0.30 * al, outline=tone, width=max(2.0, 4.2 * s))
        ring_on(img, cx, y, h * 0.42, tone, max(1.6, 3.0 * s), 0.95 * al, squash=h / (2 * h * 0.42))
    garis_tebal(img, [(x - w * 0.16, y - h * 0.06), (x, y - h * 0.12), (x + w * 0.16, y - h * 0.06)],
                tone, max(2.0, 3.4 * s), 0.95 * al)
    for sgn in (-1, 1):
        garis_tebal(img, [(x + sgn * w * 1.12, y - h * 0.10), (x + sgn * w * 1.32, y - h * 0.30)],
                    tone, max(2.0, 3.2 * s), 0.9 * al)


def anak_belakang(img, x, y, s=1.0, t=0.0, baju=None, rambut=None, lengan_kanan=0.0):
    """Anak duduk, dilihat dari BELAKANG (untuk POV kelas). y = garis bahu."""
    baju = baju or mix(TERRA, AMBER_H, 0.25)
    rambut = rambut or mix(NAVY, INK, 0.25)
    # badan (punggung)
    bentuk(img, [(x - 168 * s, y + 250 * s), (x - 140 * s, y + 30 * s), (x - 74 * s, y - 14 * s),
                 (x + 74 * s, y - 14 * s), (x + 140 * s, y + 30 * s), (x + 168 * s, y + 250 * s)],
           baju, ow=3.6, light=0.24)
    # kerah kemeja
    bentuk(img, [(x - 40 * s, y - 16 * s), (x, y + 22 * s), (x + 40 * s, y - 16 * s)],
           mix(baju, WHITE, 0.30), ow=2.6, light=0.3)
    # leher
    rrect_on(img, x - 34 * s, y - 52 * s, x + 34 * s, y + 6 * s, 18 * s, mix(PASIR, TERRA, 0.22), 1.0)
    # kepala
    elips_vol(img, x, y - 104 * s, 96 * s, 104 * s, mix(PASIR, TERRA, 0.16), ow=3.8, light=0.30)
    # rambut menutupi belakang kepala
    bentuk(img, [(x - 98 * s, y - 96 * s), (x - 92 * s, y - 168 * s), (x - 40 * s, y - 208 * s),
                 (x + 40 * s, y - 208 * s), (x + 92 * s, y - 168 * s), (x + 98 * s, y - 96 * s),
                 (x + 60 * s, y - 118 * s), (x - 60 * s, y - 118 * s)],
           rambut, ow=3.4, light=0.26)
    # telinga
    for sgn in (-1, 1):
        elips_vol(img, x + sgn * 96 * s, y - 92 * s, 15 * s, 22 * s, mix(PASIR, TERRA, 0.24), ow=2.6, light=0.3)
    # lengan kanan terangkat (outro: memasang kacamata)
    if lengan_kanan > 0.01:
        ax = x + 120 * s
        ay = y + 40 * s
        hx = x + 210 * s
        hy = y - 150 * s * lengan_kanan
        garis_tebal(img, [(ax, ay), (ax + 60 * s, ay - 40 * s * lengan_kanan), (hx, hy)],
                    baju, 34 * s, 1.0, bulge=0.15)
        elips_vol(img, hx, hy, 20 * s, 18 * s, mix(PASIR, TERRA, 0.16), ow=2.6, light=0.3)


def anak_kecil(img, x, y, s=1.0, t=0.0, hadap=1, kacamata_on=False, lari=0.0, baju=None):
    """Anak berdiri/berlari, dilihat dari depan-samping (untuk halaman & jendela)."""
    baju = baju or mix(TERRA, AMBER_H, 0.25)
    ph = t * 4.0
    # kaki
    for i, sgn in enumerate((-1, 1)):
        swing = lari * 26 * math.sin(ph + i * math.pi)
        garis_tebal(img, [(x - 12 * s, y + 96 * s), (x - 12 * s + sgn * 16 * s + swing * s, y + 168 * s)],
                    mix(NAVY, INK, 0.25), 16 * s, 1.0)
        elips_vol(img, x - 12 * s + sgn * 16 * s + swing * s, y + 172 * s, 14 * s, 8 * s,
                  mix(INK, NAVY, 0.5), ow=2.2, light=0.2)
    # badan
    bentuk(img, [(x - 44 * s, y + 104 * s), (x - 50 * s, y + 16 * s), (x - 30 * s, y - 18 * s),
                 (x + 30 * s, y - 18 * s), (x + 50 * s, y + 16 * s), (x + 44 * s, y + 104 * s)],
           baju, ow=3.2, light=0.26)
    # lengan
    for i, sgn in enumerate((-1, 1)):
        swing = lari * 30 * math.sin(ph + i * math.pi + 0.6)
        garis_tebal(img, [(x + sgn * 40 * s, y + 18 * s),
                          (x + sgn * (58 * s + swing * s * sgn * 0.3), y + 74 * s + swing * s * 0.5)],
                    baju, 18 * s, 1.0)
        elips_vol(img, x + sgn * (58 * s + swing * s * sgn * 0.3), y + 78 * s + swing * s * 0.5,
                  10 * s, 10 * s, mix(PASIR, TERRA, 0.16), ow=2.2, light=0.3)
    # kepala
    elips_vol(img, x, y - 62 * s, 48 * s, 52 * s, mix(PASIR, TERRA, 0.16), ow=3.2, light=0.3)
    # rambut
    bentuk(img, [(x - 50 * s, y - 66 * s), (x - 44 * s, y - 104 * s), (x - 12 * s, y - 118 * s),
                 (x + 22 * s, y - 112 * s), (x + 48 * s, y - 80 * s), (x + 50 * s, y - 62 * s),
                 (x + 20 * s, y - 76 * s), (x - 20 * s, y - 76 * s)],
           mix(NAVY, INK, 0.28), ow=2.8, light=0.24)
    # mata
    for sgn in (-1, 1):
        dot_on(img, x + sgn * 17 * s, y - 64 * s, 4.6 * s, mix(INK, NAVY, 0.4), 0.9)
    if kacamata_on:
        kacamata(img, x, y - 64 * s, s * 0.34, tone=mix(INK, NAVY, 0.4))
    # senyum
    garis_tebal(img, [(x - 10 * s, y - 48 * s), (x, y - 42 * s), (x + 10 * s, y - 48 * s)],
                mix(TERRA_D, INK, 0.35), 2.6 * s, 0.75)


def pohon_bulat(img, x, y, s=1.0, tone=None, t=0.0):
    """Pohon rindang sederhana (bukan kelapa)."""
    tone = tone or mix(OLIVE, TEAL_D, 0.35)
    garis_tebal(img, [(x, y), (x - 4 * s, y - 96 * s)], mix(TERRA_D, INK, 0.35), 22 * s, 1.0, bulge=0.25)
    for (dx, dy, rr) in ((-46, -140, 62), (44, -150, 58), (0, -196, 70), (-6, -128, 54)):
        elips_vol(img, x + dx * s, y + dy * s, rr * s, rr * 0.86 * s, tone, ow=3.0, light=0.30)


def mata_ikon(img, cx, cy, r, tone=None, retina_geser=0.0):
    """Ikon bola mata kecil (untuk kartu tahap)."""
    tone = tone or mix(TEAL, TEAL_D, 0.25)
    elips_vol(img, cx, cy, r, r * 0.94, mix(CREAM, WHITE, 0.55), outline=mix(NAVY, INK, 0.5), ow=3.4, light=0.30)
    elips_vol(img, cx + r * 0.14, cy, r * 0.74, r * 0.70, mix(TEAL_L, CREAM, 0.55), outline=None, ow=0, light=0.3, alpha=0.55)
    arc = [(cx + r * 0.80 * math.cos(a), cy + r * 0.80 * math.sin(a)) for a in np.linspace(-1.15, 1.15, 16)]
    garis_tebal(img, arc, TERRA, max(3.0, r * 0.14), 0.95)
    # kornea
    bentuk(img, [(cx - r * 0.94, cy - r * 0.34), (cx - r * 1.16, cy - r * 0.06),
                 (cx - r * 1.16, cy + r * 0.10), (cx - r * 0.94, cy + r * 0.38)],
           mix(TEAL_L, WHITE, 0.45), ow=2.6, alpha=0.85, light=0.3)
    elips_vol(img, cx - r * 0.34, cy, r * 0.16, r * 0.42, mix(AMBER_H, TERRA, 0.30), ow=2.4, light=0.35)
    if retina_geser > 0:
        garis_tebal(img, [(cx + r * 0.92, cy - r * 0.56), (cx + r * 0.92, cy + r * 0.56)],
                    mix(AMBER_H, CREAM, 0.4), 2.4, 0.55, bulge=0.0)


def mata_penampang(img, cx, cy, rx, ry, t=0.0, fokus_offset=86, label=True):
    """Penampang bola mata: sklera, kornea, lensa, retina, dan tiga berkas cahaya."""
    # sklera
    elips_vol(img, cx, cy, rx, ry, mix(CREAM, WHITE, 0.62), outline=mix(NAVY, INK, 0.45), ow=5.0, light=0.30)
    # vitreus (gel)
    elips_vol(img, cx + rx * 0.10, cy, rx * 0.80, ry * 0.82, mix(TEAL_L, CREAM, 0.62),
              outline=None, ow=0, light=0.34, alpha=0.55)
    # koroid + retina di dinding kanan
    arc_o = [(cx + rx * 0.90 * math.cos(a), cy + ry * 0.90 * math.sin(a)) for a in np.linspace(-1.22, 1.22, 22)]
    garis_tebal(img, arc_o, mix(TEAL_D, INK, 0.15), 22, 0.85)
    arc_i = [(cx + rx * 0.83 * math.cos(a), cy + ry * 0.83 * math.sin(a)) for a in np.linspace(-1.22, 1.22, 22)]
    garis_tebal(img, arc_i, TERRA, 14, 0.95)
    # saraf optik
    bentuk(img, [(cx + rx * 0.86, cy + ry * 0.24), (cx + rx * 1.16, cy + ry * 0.34),
                 (cx + rx * 1.16, cy + ry * 0.56), (cx + rx * 0.84, cy + ry * 0.44)],
           mix(PASIR, TERRA, 0.35), ow=3.0, light=0.25)
    # kornea (tonjolan kiri, tembus pandang)
    bentuk(img, [(cx - rx * 0.96, cy - ry * 0.50), (cx - rx * 1.14, cy - ry * 0.20),
                 (cx - rx * 1.17, cy + ry * 0.06), (cx - rx * 1.12, cy + ry * 0.30),
                 (cx - rx * 0.96, cy + ry * 0.52)],
           mix(TEAL_L, WHITE, 0.40), ow=3.0, alpha=0.72, light=0.35)

    # lensa
    elips_vol(img, cx - rx * 0.44, cy, rx * 0.115, ry * 0.30, mix(AMBER_H, WHITE, 0.30),
              outline=mix(TERRA_D, INK, 0.2), ow=3.0, light=0.40)
    # tiga berkas cahaya paralel -> menyempit di kornea -> fokus -> melebar ke retina
    fx = cx + rx * 0.90 - fokus_offset
    r_x = cx + rx * 0.83
    for dy in (-0.26, 0.0, 0.26):
        y0 = cy + ry * dy
        p = [(cx - rx * 1.55, y0),
             (cx - rx * 1.10, cy + ry * dy * 0.72),
             (cx - rx * 0.44, cy + ry * dy * 0.36),
             (fx, cy)]
        garis_tebal(img, p, mix(AMBER_H, WHITE, 0.25), 5.2, 0.92, bulge=0.10)
        # setelah fokus: melebar ke retina
        garis_tebal(img, [(fx, cy), (r_x, cy + ry * dy * 1.55)],
                    mix(AMBER_H, WHITE, 0.15), 3.6, 0.60, bulge=0.0)
    # titik fokus
    ring_on(img, fx, cy, 13, mix(AMBER_H, WHITE, 0.15), 3.0, 0.75)
    dot_on(img, fx, cy, 6.5, mix(WHITE, CREAM, 0.2), 1.0)
    # lingkaran buram di retina
    by = ry * 0.42
    garis_tebal(img, [(r_x + 4, cy - by), (r_x + 18, cy - by * 0.5), (r_x + 18, cy + by * 0.5), (r_x + 4, cy + by)],
                mix(TERRA_D, INK, 0.15), 4.0, 0.85)
    if label:
        f = font("Poppins-SemiBold.ttf", 25)
        tone_l = mix(NAVY, MUTED, 0.30)
        # label + garis penunjuk: diletakkan di luar bola, bukan di atasnya
        for (tx, ty, ax, ay, txt) in (
                (128, 372, cx - rx * 1.06, cy - ry * 0.30, "kornea"),
                (392, 946, cx - rx * 0.44, cy + ry * 0.30, "lensa"),
                (884, 372, cx + rx * 0.62, cy - ry * 0.66, "retina")):
            garis_tebal(img, [(tx, ty), (ax, ay)], tone_l, 2.2, 0.55)
            dot_on(img, ax, ay, 4.0, tone_l, 0.8)
            paste_c(img, tx, ty, txt, f, tone_l, 0.9)
        paste_c(img, fx, cy - 40, "fokus", font("Poppins-SemiBold.ttf", 23), mix(TERRA_D, INK, 0.2), 0.9)
    return fx


def sekolah(img, x, y, w=560, h=400):
    """Bangunan sekolah: badan krem, atap terakota, jendela, pintu."""
    bentuk(img, [(x, y), (x + w * 0.5, y - h * 0.26), (x + w, y), (x + w, y + h * 0.62), (x, y + h * 0.62)],
           mix(CREAM, PASIR, 0.35), ow=3.6, light=0.20)
    bentuk(img, [(x - 18, y + 6), (x + w * 0.5, y - h * 0.34), (x + w + 18, y + 6), (x + w + 6, y + 26), (x - 6, y + 26)],
           mix(TERRA, TERRA_D, 0.25), ow=3.4, light=0.24)
    # jendela
    for r in range(2):
        for c in range(5):
            wx = x + 34 + c * (w - 70) / 4.6
            wy = y + 62 + r * 92
            rrect_on(img, wx, wy, wx + 62, wy + 62, 6, mix(TEAL_L, CREAM, 0.35), 1.0,
                     outline=mix(NAVY, INK, 0.35), width=3.0)
            line_on(img, (wx + 31, wy), (wx + 31, wy + 62), mix(NAVY, INK, 0.3), 2.0, 0.5)
    # pintu
    rrect_on(img, x + w * 0.44, y + h * 0.30, x + w * 0.56, y + h * 0.62, 6,
             mix(TERRA, TERRA_D, 0.45), 1.0, outline=mix(NAVY, INK, 0.35), width=3.0)


def bendera(img, x, y_top, y_bottom, t=0.0):
    garis_tebal(img, [(x, y_top), (x, y_bottom)], mix(NAVY, INK, 0.35), 7, 0.95)
    wave = [y_top + 10 + 8 * math.sin(t * 2.2 + i * 0.5) for i in range(2)]
    bentuk(img, [(x, y_top + 8), (x + 86, y_top + 14), (x + 86, y_top + 40), (x, y_top + 40)],
           mix(TERRA, (198, 48, 44), 0.55), ow=2.2, light=0.2)
    bentuk(img, [(x, y_top + 40), (x + 86, y_top + 40), (x + 86, y_top + 66), (x, y_top + 66)],
           mix(CREAM, WHITE, 0.7), ow=2.2, light=0.2)


def tetes_mata(img, x, y, s=1.0):
    """Botol tetes mata."""
    bentuk(img, [(x - 30 * s, y - 46 * s), (x + 30 * s, y - 46 * s), (x + 34 * s, y + 34 * s),
                 (x - 34 * s, y + 34 * s)], mix(TEAL, TEAL_D, 0.20), ow=3.0, light=0.28)
    rrect_on(img, x - 12 * s, y - 74 * s, x + 12 * s, y - 46 * s, 4 * s, mix(NAVY, INK, 0.35), 1.0)
    rrect_on(img, x - 34 * s, y - 12 * s, x + 34 * s, y + 22 * s, 3, mix(CREAM, WHITE, 0.6), 0.55)
    dot_on(img, x + 12 * s, y + 44 * s, 7 * s, mix(TEAL_L, WHITE, 0.3), 0.9)


def lensa_kontak(img, x, y, r=40, tone=None):
    tone = tone or mix(TEAL_L, WHITE, 0.3)
    ring_on(img, x, y, r, tone, 8.0, 0.95)
    ring_on(img, x, y, r - 9, mix(CREAM, WHITE, 0.6), 2.4, 0.5)
    elips_vol(img, x, y, r * 0.92, r * 0.42, mix(TEAL_L, CREAM, 0.5), outline=None, ow=0, light=0.4, alpha=0.30)


def jendela(img, x0, y0, x1, y1, tone_sky=None, tone_frame=None):
    tone_frame = tone_frame or mix(CREAM, PASIR, 0.25)
    rrect_on(img, x0 - 16, y0 - 16, x1 + 16, y1 + 16, 10, tone_frame, 1.0,
             outline=mix(NAVY, INK, 0.35), width=4.0)
    rrect_on(img, x0, y0, x1, y1, 4, mix(LANGIT, WHITE, 0.3), 1.0)


def papan_tulis(img, x0, y0, x1, y1, blur=7.5):
    """Papan tulis berkapur; isinya SENGAJA diburamkan (mata minus)."""
    rrect_on(img, x0 - 14, y0 - 14, x1 + 14, y1 + 14, 10, mix(TERRA_D, INK, 0.25), 1.0,
             outline=mix(INK, NAVY, 0.4), width=4.0)
    lay = Image.new("RGB", (int(S(x1 - x0)), int(S(y1 - y0))), mix(TEAL_D, INK, 0.18))
    dd = ImageDraw.Draw(lay)
    # judul kapur + tiga baris "tulisan"
    dd.rounded_rectangle([S(34), S(34), S(300), S(72)], radius=S(6), fill=mix(CREAM, WHITE, 0.5))
    rng = np.random.default_rng(54)
    for r in range(3):
        yy = 118 + r * 92
        ln = int(150 + rng.random() * 260)
        dd.rounded_rectangle([S(38), S(yy), S(38 + ln), S(yy + 20)], radius=S(6),
                             fill=mix(CREAM, TEAL_L, 0.35))
        dd.rounded_rectangle([S(38), S(yy + 34), S(38 + ln * 0.62), S(yy + 52)], radius=S(6),
                             fill=mix(CREAM, TEAL_L, 0.45))
    lay = lay.filter(ImageFilter.GaussianBlur(max(1, int(round(S(blur))))))
    img.paste(lay, (int(round(S(x0))), int(round(S(y0)))))


# ------------------------------------------------------------------ 1 · INTRO (kelas, buram)
def _dunia_kelas(im, senja=False, lengan=0.0):
    if senja:
        wall = grad_v(1080, 1080, [(0.0, mix(SENJA, CREAM, 0.45)), (0.55, mix(LANGIT, SENJA, 0.35)),
                                   (1.0, mix(PASIR, TERRA, 0.22))], seed=71)
    else:
        wall = grad_v(1080, 1080, [(0.0, mix(LANGIT, CREAM, 0.55)), (0.55, mix(LANGIT, CREAM, 0.35)),
                                   (1.0, mix(PASIR, CREAM, 0.55))], seed=54)
    im.paste(wall, (0, 0))
    # papan tulis (buram: benda jauh)
    papan_tulis(im, 74, 232, 690, 726, blur=8.0)
    # jendela kanan
    jendela(im, 764, 214, 1016, 646)
    sky = grad_v(252, 432, [(0.0, mix(LANGIT, WHITE, 0.20)), (1.0, mix(LANGIT_2, SENJA, 0.45))], seed=7)
    im.paste(sky, (int(round(S(764))), int(round(S(214)))))
    matahari(im, 950, 316, 56, 0.0, mix(AMBER_H, TERRA, 0.22))
    awan(im, 850, 270, 120, 46, seed=4)
    bentuk(im, [(764, 560), (830, 500), (900, 540), (960, 480), (1016, 520), (1016, 646), (764, 646)],
           mix(OLIVE, TEAL_D, 0.35), ow=3.0, light=0.16)
    pohon_bulat(im, 800, 600, 0.55, tone=mix(OLIVE, TEAL_D, 0.45))
    # poster kecil di dinding
    rrect_on(im, 790, 760, 1000, 940, 8, mix(CREAM, WHITE, 0.55), 1.0,
             outline=mix(NAVY, INK, 0.3), width=3.0)
    for i in range(3):
        line_on(im, (812, 792 + i * 40), (978, 792 + i * 40), mix(TEAL, CREAM, 0.55), 5.0, 0.5)
    # lantai kayu
    lantai = grad_v(1080, 260, [(0.0, mix(PASIR, TERRA, 0.18)), (1.0, mix(PASIR_D, TERRA, 0.30))], seed=9)
    im.paste(lantai, (0, int(round(S(1020)))))
    for i in range(4):
        line_on(im, (0, 1052 + i * 46), (1080, 1036 + i * 46), mix(TERRA_D, INK, 0.3), 2.4, 0.18)
    # anak duduk (punggung) + meja depan
    anak_belakang(im, 400, 1128, 1.0, 0.0, lengan_kanan=lengan)
    bentuk(im, [(0, 1332), (1080, 1288), (1080, 1436), (0, 1436)],
           mix(PASIR, TERRA, 0.22), ow=3.6, light=0.22)
    line_on(im, (0, 1332), (1080, 1288), mix(TERRA_D, INK, 0.35), 3.0, 0.5)
    # buku + pensil + kacamata di meja
    rrect_on(im, 116, 1352, 300, 1410, 6, mix(CREAM, WHITE, 0.6), 1.0,
             outline=mix(NAVY, INK, 0.35), width=2.6)
    line_on(im, (140, 1372), (276, 1372), mix(TEAL, CREAM, 0.5), 2.6, 0.45)
    line_on(im, (140, 1388), (246, 1388), mix(TEAL, CREAM, 0.5), 2.6, 0.35)
    garis_tebal(im, [(330, 1396), (392, 1372)], mix(AMBER_H, TERRA, 0.4), 7.0, 0.9)
    kacamata(im, 806, 1382, 0.92, tone=mix(INK, NAVY, 0.25))
    latar_bawah(im, mix(PASIR, TERRA, 0.26), y0=1436, butir=40, props=False, seed=54)
    bayangan_kartu(im)


def _dunia_intro(im):
    _dunia_kelas(im, senja=False)


def sc_intro(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("intro54", _dunia_intro), (0, 0))
    # berkas cahaya dari jendela (debu di udara)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(S(780), S(240)), (S(1016), S(240)), (S(700), S(1180)), (S(300), S(1180))],
                                fill=(255, 236, 200, 26))
    lay = lay.filter(ImageFilter.GaussianBlur(S(26)))
    img.paste(lay.convert("RGB"), (0, 0), lay)
    butir_terbang(img, tl, 240, 1000, 300, 1200, 18, mix(CREAM, WHITE, 0.5), seed=11)
    # kilau kacamata di meja
    g = 0.5 + 0.5 * math.sin(tl * 2.6)
    ring_on(img, 806 + 26, 1378, 6 + 3 * g, mix(WHITE, CREAM, 0.2), 2.2, 0.35 + 0.3 * g)
    kartu_judul(img, ["DUNIA JADI BURAM", "BUKAN SALAH LENSA"], hl="BURAM", y=Y_KARTU, fsz=74,
                tab=mix(TERRA, AMBER_H, 0.3), al=al, dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 2 · F1 penampang bola mata
def _dunia_optik(im):
    bg = grad_v(1080, 1436, [(0.0, mix(CREAM, WHITE, 0.35)), (0.62, mix(KREM, PASIR, 0.22)),
                             (1.0, mix(PASIR, TERRA, 0.18))], seed=83)
    im.paste(bg, (0, 0))
    # cincin konsentris tipis (pelat medis)
    for i in range(5):
        ring_on(im, 540, 640, 300 + i * 62, mix(TEAL, CREAM, 0.72), 1.8, 0.16)
    for i in range(24):
        a = i * math.pi / 12
        line_on(im, (540 + 250 * math.cos(a), 640 + 250 * math.sin(a)),
                (540 + 268 * math.cos(a), 640 + 268 * math.sin(a)), mix(TEAL, CREAM, 0.60), 1.6, 0.18)
    mata_penampang(im, 540, 640, 300, 268, 0.0)
    # penggaris 24 mm
    y = 1112
    garis_tebal(im, [(210, y), (892, y)], mix(NAVY, MUTED, 0.35), 4.0, 0.55)
    for x in (210, 892):
        garis_tebal(im, [(x, y - 26), (x, y + 26)], mix(NAVY, MUTED, 0.35), 4.0, 0.8)
    angka_besar(im, 551, y - 74, "24", "mm", mix(NAVY, INK, 0.05), fsz=72)
    paste_c(im, 551, y + 56, "panjang bola mata", font("Poppins-Regular.ttf", 26),
            mix(NAVY, MUTED, 0.45), 0.72)
    latar_bawah(im, mix(PASIR, TERRA, 0.20), y0=1436, butir=50, props=False, seed=83)
    bayangan_kartu(im)


def sc_optik(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("optik54", _dunia_optik), (0, 0))
    # denyut cahaya menembus lensa -> fokus
    for k in range(3):
        ph = (tl * 0.55 + k / 3.0) % 1.0
        x = 120 + ph * (790 - 120)
        y = 640 + 74 * math.sin(math.pi * ph * 0.9) * (1 if k % 2 == 0 else -1) * (1 - ph)
        dot_on(img, x, y, 6.5, mix(WHITE, AMBER_H, 0.20), 0.55 + 0.35 * math.sin(tl * 3 + k))
    # fokus berdenyut + lingkaran buram bernapas
    p = 0.5 + 0.5 * math.sin(tl * 2.4)
    ring_on(img, 706, 640, 16 + 7 * p, mix(AMBER_H, WHITE, 0.35), 2.6, 0.45 + 0.3 * p)
    by = 112 + 10 * p
    garis_tebal(img, [(792, 640 - by), (806, 640 - by * 0.5), (806, 640 + by * 0.5), (792, 640 + by)],
                mix(TERRA_D, INK, 0.1), 4.4, 0.55 + 0.25 * p)
    paste_c(img, 660, 300, "BAYANGAN BURAM", font("Poppins-SemiBold.ttf", 22),
            mix(TERRA_D, INK, 0.15), 0.9)
    garis_tebal(img, [(756, 314), (826, 560), (806, 690)], mix(TERRA_D, INK, 0.15), 2.0, 0.45)
    butir_terbang(img, tl, 0, 1080, 200, 1200, 12, mix(CREAM, WHITE, 0.4), seed=13)
    kartu_judul(img, ["CAHAYA JATUH", "DI DEPAN RETINA"], hl="DI DEPAN RETINA", y=Y_KARTU, fsz=72,
                tab=mix(TEAL, INK, 0.18), al=al, dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 3 · F2 tiga tahap memanjang
def _kartu_tahap(im, cx, cy, w, h, label_atas, angka, bawah, tone):
    rrect_on(im, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 26, mix(CREAM, WHITE, 0.50), 0.97,
             outline=mix(NAVY, INK, 0.30), width=3.6)
    rrect_on(im, cx - w / 2 + 22, cy - h / 2 - 6, cx - w / 2 + 22 + 66, cy - h / 2 + 8, 7, tone, 0.95)
    paste_c(im, cx, cy - h / 2 + 54, label_atas, font("Poppins-Regular.ttf", 30), mix(NAVY, MUTED, 0.4), 0.85)
    mata_ikon(im, cx, cy - 44, 74, tone=mix(TEAL, tone, 0.35))
    paste_c(im, cx, cy + 96, angka, font("Poppins-Bold.ttf", 96), mix(NAVY, INK, 0.10), 1.0)
    paste_c(im, cx, cy + 168, bawah, font("Poppins-SemiBold.ttf", 26), mix(tone, INK, 0.35), 0.9)


def _dunia_panjang(im):
    bg = grad_v(1080, 1436, [(0.0, mix(LANGIT, CREAM, 0.50)), (0.60, mix(CREAM, PASIR, 0.30)),
                             (1.0, mix(PASIR, TERRA, 0.22))], seed=91)
    im.paste(bg, (0, 0))
    # garis skala halus
    for i in range(12):
        line_on(im, (0, 180 + i * 96), (1080, 180 + i * 96), mix(TEAL, CREAM, 0.72), 1.6, 0.10)
    _kartu_tahap(im, 190, 620, 292, 470, "24 mm", "−1", "ringan", mix(AMBER_H, TERRA, 0.30))
    _kartu_tahap(im, 540, 620, 292, 470, "25 mm", "−4", "sedang", mix(TERRA, TERRA_D, 0.25))
    _kartu_tahap(im, 890, 620, 292, 470, "26 mm", "−7", "tinggi", mix(TERRA_D, INK, 0.15))
    # panah antar kartu
    for x in (366, 716):
        garis_tebal(im, [(x, 620), (x + 46, 620)], mix(NAVY, MUTED, 0.35), 5.0, 0.65)
        poly_on(im, [(x + 58, 620), (x + 40, 608), (x + 40, 632)], mix(NAVY, MUTED, 0.35), 0.8)
    # garis dasar + label
    garis_tebal(im, [(120, 980), (960, 980)], mix(NAVY, MUTED, 0.45), 3.0, 0.35)
    paste_c(im, 540, 1030, "1 milimeter ≈ 3 minus · mata tidak menyusut lagi",
            font("Poppins-SemiBold.ttf", 27), mix(NAVY, MUTED, 0.35), 0.85)
    latar_bawah(im, mix(PASIR, TERRA, 0.24), y0=1436, butir=50, props=False, seed=91)
    bayangan_kartu(im)


def sc_panjang(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("panjang54", _dunia_panjang), (0, 0))
    # kartu ketiga "berdenyut" (mata terus memanjang)
    p = 0.5 + 0.5 * math.sin(tl * 2.2)
    ring_on(img, 890, 620, 150 + 6 * p, mix(TERRA_D, CREAM, 0.35), 2.4, 0.16 + 0.14 * p)
    # titik bergerak di garis dasar
    for i in range(3):
        x = 120 + ((tl * 60 + i * 280) % 840)
        dot_on(img, x, 980, 4.4, mix(TERRA, INK, 0.2), 0.35)
    butir_terbang(img, tl, 0, 1080, 220, 1100, 10, mix(CREAM, WHITE, 0.4), seed=17)
    kartu_judul(img, ["TAMBAH 1 MILIMETER,", "MINUS BERTAMBAH"], hl="1 MILIMETER", y=Y_KARTU, fsz=64,
                tab=mix(TERRA, AMBER_H, 0.25), al=al, dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 4 · F3 dalam vs luar
def _dunia_ruang(im):
    """Dua panel: DI DALAM (redup) vs DI LUAR (terang) - perbandingan yang bisa dilihat sekilas."""
    im.paste(grad_v(1080, 1436, [(0.0, mix(CREAM, PASIR, 0.18)), (1.0, mix(PASIR, TERRA, 0.22))], seed=33), (0, 0))

    # ---------------- panel kiri: DI DALAM (redup)
    L0, L1 = 26, 520
    im.paste(grad_v(L1 - L0, 1180, [(0.0, mix(NAVY, TEAL_D, 0.42)), (0.55, mix(NAVY_D, TEAL_D, 0.32)),
                                    (1.0, mix(NAVY_D, INK, 0.22))], seed=41),
             (int(round(S(L0))), int(round(S(90)))))
    # dinding + papan kecil
    rrect_on(im, 62, 150, 300, 320, 8, mix(NAVY, TEAL_D, 0.55), 0.55, outline=mix(CREAM, TEAL_D, 0.6), width=2.4)
    for i in range(3):
        line_on(im, (80, 186 + i * 42), (270 - i * 30, 186 + i * 42), mix(CREAM, TEAL_L, 0.55), 4.0, 0.35)
    # meja
    bentuk(im, [(L0, 980), (L1, 980), (L1, 1064), (L0, 1064)], mix(TERRA_D, INK, 0.40), ow=3.0, light=0.16)
    garis_tebal(im, [(90, 1064), (90, 1180)], mix(TERRA_D, INK, 0.45), 13, 1.0)
    garis_tebal(im, [(460, 1064), (460, 1180)], mix(TERRA_D, INK, 0.45), 13, 1.0)
    # lampu meja + pendar
    garis_tebal(im, [(180, 980), (180, 872)], mix(TERRA_D, INK, 0.45), 7, 1.0)
    bentuk(im, [(140, 872), (220, 872), (202, 834), (158, 834)], mix(AMBER_H, TERRA, 0.22), ow=3.0, light=0.35)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(S(158), S(842)), (S(202), S(842)), (S(330), S(980)), (S(60), S(980))],
                                fill=(255, 210, 145, 92))
    lay = lay.filter(ImageFilter.GaussianBlur(S(20)))
    im.paste(lay.convert("RGB"), (0, 0), lay)
    # anak duduk membaca (menghadap meja, dari samping)
    anak_kecil(im, 340, 856, 0.94, 0.0, kacamata_on=True, baju=mix(TERRA, INK, 0.20))
    rrect_on(im, 246, 926, 404, 972, 6, mix(CREAM, PASIR, 0.55), 0.95,
             outline=mix(INK, NAVY, 0.45), width=2.4)
    line_on(im, (262, 946), (388, 946), mix(NAVY, MUTED, 0.5), 2.4, 0.35)

    # ---------------- panel kanan: DI LUAR (terang)
    R0, R1 = 560, 1054
    im.paste(grad_v(R1 - R0, 1180, [(0.0, mix(LANGIT, WHITE, 0.28)), (0.52, mix(LANGIT, LANGIT_2, 0.42)),
                                    (1.0, mix(LANGIT_2, SENJA, 0.30))], seed=43),
             (int(round(S(R0))), int(round(S(90)))))
    cahaya_matahari(im, 880, 250, 96, 0.80)
    matahari(im, 880, 250, 78, 0.0, mix(AMBER_H, TERRA, 0.18))
    awan(im, 680, 236, 150, 58, seed=6)
    # tanah + bukit + pohon + anak berlari + layangan
    bentuk(im, [(R0, 1000), (700, 900), (860, 950), (980, 880), (R1, 930), (R1, 1180), (R0, 1180)],
           mix(OLIVE, TEAL_D, 0.28), ow=3.2, light=0.18)
    bentuk(im, [(R0, 1080), (R1, 1020), (R1, 1180), (R0, 1180)],
           mix(OLIVE, AMBER_H, 0.40), ow=3.0, light=0.22)
    pohon_bulat(im, 640, 940, 0.66)
    pohon_bulat(im, 1012, 936, 0.56, tone=mix(OLIVE, TEAL_D, 0.5))
    anak_kecil(im, 830, 892, 0.80, 0.0, lari=0.7)
    layangan(im, 930, 620, 0.86, tilt=0.2, t=0.0, tone=mix(TERRA, AMBER_H, 0.3))
    garis_tebal(im, kurva((930, 640), (886, 790), (846, 950), 16), mix(INK, NAVY, 0.4), 1.8, 0.45)

    # ---------------- pembatas + VS
    garis_tebal(im, [(540, 110), (540, 1180)], mix(PASIR_D, TERRA, 0.30), 8, 0.9)
    elips_vol(im, 540, 700, 44, 44, mix(CREAM, WHITE, 0.55), outline=mix(NAVY, INK, 0.3), ow=3.4, light=0.3)
    paste_c(img := im, 540, 700, "VS", font("Poppins-Bold.ttf", 34), mix(NAVY, INK, 0.15), 1.0)

    latar_bawah(im, mix(PASIR, TERRA, 0.28), y0=1200, butir=40, props=False, seed=33)
    bayangan_kartu(im)


def sc_ruang(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("ruang54", _dunia_ruang), (0, 0))
    # label panel + angka lux di dalam panel (bukan menimpa ilustrasi)
    for (cx, label, angka, unit, tone_bg, tone_txt) in (
            (273, "DI DALAM RUANGAN", "300", "lux", mix(NAVY_D, INK, 0.25), mix(CREAM, WHITE, 0.5)),
            (807, "DI LUAR, SIANG", "100.000", "lux", mix(CREAM, WHITE, 0.45), mix(NAVY, INK, 0.1))):
        rrect_on(img, cx - 214, 1090, cx + 214, 1186, 20, tone_bg, 0.72)
    paste_c(img, 273, 1116, "DI DALAM RUANGAN", font("Poppins-SemiBold.ttf", 23), mix(CREAM, WHITE, 0.5), 0.95)
    paste_c(img, 807, 1116, "DI LUAR, SIANG", font("Poppins-SemiBold.ttf", 23), mix(NAVY, INK, 0.1), 0.95)
    angka_besar(img, 273, 1160, "300", "lux", mix(CREAM, WHITE, 0.55), fsz=40)
    angka_besar(img, 807, 1160, "100.000", "lux", mix(NAVY, INK, 0.05), fsz=36)
    # pita pengali
    p = 0.5 + 0.5 * math.sin(tl * 2.0)
    gelembung(img, 540, 986, "±300× LEBIH TERANG", w=470, fsz=31, ekor=None)
    ring_on(img, 540, 700, 52 + 5 * p, mix(AMBER_H, WHITE, 0.4), 2.6, 0.25 + 0.2 * p)
    butir_terbang(img, tl, 570, 1040, 300, 900, 9, mix(CREAM, WHITE, 0.5), seed=23)
    kartu_judul(img, ["TERLALU DEKAT,", "TERLALU REDUP"], hl="TERLALU REDUP", y=Y_KARTU, fsz=70,
                tab=mix(OLIVE, INK, 0.2), al=al, dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 5 · F4 halaman sekolah (bukti)
def _dunia_bukti(im):
    im.paste(grad_v(1080, 1200, [(0.0, mix(LANGIT, WHITE, 0.20)), (0.55, mix(LANGIT, LANGIT_2, 0.35)),
                                 (1.0, mix(LANGIT_2, SENJA, 0.30))], seed=57), (0, 0))
    cahaya_matahari(im, 862, 250, 120, 0.85)
    matahari(im, 862, 250, 92, 0.0, mix(AMBER_H, TERRA, 0.20))
    for (cx, cy, w, h, sd) in ((180, 210, 230, 88, 5), (620, 190, 170, 66, 9), (940, 340, 190, 74, 12)):
        awan(im, cx, cy, w, h, seed=sd)
    # lapangan
    bentuk(im, [(0, 980), (1080, 950), (1080, 1436), (0, 1436)], mix(OLIVE, AMBER_H, 0.42), ow=3.4, light=0.20)
    for i in range(7):
        garis_tebal(im, [(i * 170, 1436), (i * 170 + 40, 1000)], mix(OLIVE_D, INK, 0.2), 2.6, 0.12)
    # sekolah (turun supaya angka di atas punya ruang) + bendera di kanan jauh
    sekolah(im, 40, 792, 520, 300)
    garis_tebal(im, [(1006, 640), (1006, 1010)], mix(NAVY, INK, 0.35), 8, 0.95)
    bendera(im, 1006, 640, 1010, 0.0)
    # pohon + anak bermain
    pohon_bulat(im, 700, 1000, 0.85)
    anak_kecil(im, 300, 1060, 0.9, 0.0, lari=0.8)
    anak_kecil(im, 470, 1090, 0.82, 1.1, lari=0.6, baju=mix(TEAL, TEAL_D, 0.25))
    anak_kecil(im, 620, 1040, 0.86, 2.2, lari=0.9, baju=mix(AMBER_H, TERRA, 0.35))
    layangan(im, 420, 720, 1.0, tilt=0.25, t=0.0)
    garis_tebal(im, kurva((420, 740), (380, 860), (340, 960), 14), mix(INK, NAVY, 0.4), 1.8, 0.4)
    latar_bawah(im, mix(OLIVE, AMBER_H, 0.45), y0=1436, butir=60, props=True, seed=57)
    bayangan_kartu(im)


def sc_bukti(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("bukti54", _dunia_bukti), (0, 0))
    # dua angka: dengan vs tanpa tambahan 40 menit (kartu transparan supaya tetap terbaca di langit)
    p = clamp(tl / 1.1)
    for cx, num, cap, tc in ((260, "30,4", "DENGAN 40 MENIT DI LUAR", mix(NAVY, INK, 0.05)),
                             (820, "39,5", "TANPA TAMBAHAN", mix(TERRA_D, INK, 0.10))):
        rrect_on(img, cx - 214, 246, cx + 214, 424, 26, mix(CREAM, WHITE, 0.55), 0.86 * p,
                 outline=mix(NAVY, INK, 0.28), width=3.0)
        angka_besar(img, cx, 320, num, "%", tc, fsz=76, al=p)
        paste_c(img, cx, 394, cap, font("Poppins-SemiBold.ttf", 22),
                mix(tc, INK, 0.15), 0.92 * p)
    gar_mid = 540
    garis_tebal(img, [(gar_mid, 296), (gar_mid, 372)], mix(OLIVE_D, INK, 0.25), 5.0, 0.5 * p)
    poly_on(img, [(gar_mid, 388), (gar_mid - 13, 365), (gar_mid + 13, 365)], mix(OLIVE_D, INK, 0.25), 0.85 * p)
    gelembung(img, 540, 528, "+40 MENIT DI LUAR", w=430, fsz=29, ekor=None, al=eo(seg(tl, 0.5, 1.1)))
    butir_terbang(img, tl, 0, 1080, 200, 900, 10, mix(CREAM, WHITE, 0.5), seed=29)
    kartu_judul(img, ["40 MENIT DI LUAR,", "BEDA 9 PERSEN"], hl="40 MENIT", y=Y_KARTU, fsz=68,
                tab=mix(TERRA, AMBER_H, 0.3), al=al, dy=dy)
    sumber(img, "Sumber: JAMA (uji Guangzhou) · meta-analisis 2026")


# ------------------------------------------------------------------ 6 · F5 koreksi vs perlambat
def _dunia_koreksi(im):
    im.paste(grad_v(1080, 1436, [(0.0, mix(CREAM, LANGIT, 0.30)), (0.6, mix(CREAM, WHITE, 0.25)),
                                 (1.0, mix(PASIR, CREAM, 0.45))], seed=61), (0, 0))
    # kartu Snellen di kiri
    rrect_on(im, 96, 214, 404, 700, 10, mix(CREAM, WHITE, 0.60), 1.0,
             outline=mix(NAVY, INK, 0.30), width=3.4)
    baris = [("E", 62, 306), ("F P", 50, 380), ("T O Z", 40, 444),
             ("L P E D", 30, 502), ("P E C F D", 24, 552), ("E D F C Z P", 19, 596)]
    for txt, fs, yy in baris:
        paste_c(im, 250, yy, txt, font("Poppins-Bold.ttf", fs), mix(NAVY, INK, 0.15), 0.95)
    paste_c(im, 250, 660, "tes mata", font("Poppins-Regular.ttf", 22), mix(NAVY, MUTED, 0.4), 0.7)
    # bola mata kanan: panjang tetap walau fokus dibetulkan
    mata_ikon(im, 760, 430, 132, tone=mix(TEAL, TEAL_D, 0.3))
    garis_tebal(im, [(640, 590), (884, 590)], mix(NAVY, MUTED, 0.4), 3.4, 0.5)
    for x in (640, 884):
        garis_tebal(im, [(x, 574), (x, 606)], mix(NAVY, MUTED, 0.4), 3.4, 0.8)
    paste_c(im, 762, 622, "26 mm — tetap", font("Poppins-SemiBold.ttf", 25), mix(NAVY, MUTED, 0.35), 0.85)
    # tiga lencana
    cxs = (196, 540, 884)
    for cx in cxs:
        elips_vol(im, cx, 830, 86, 86, mix(CREAM, WHITE, 0.55), outline=mix(NAVY, INK, 0.30), ow=3.4, light=0.28)
    # 1) matahari
    matahari(im, 196, 812, 46, 0.0, mix(AMBER_H, TERRA, 0.22))
    # 2) tetes
    tetes_mata(im, 540, 812, 1.0)
    # 3) lensa
    lensa_kontak(im, 884, 818, 38)
    for cx, label in ((196, "2 JAM DI LUAR"), (540, "ATROPIN"), (884, "LENSA KHUSUS")):
        gelembung(im, cx, 968, label, w=310, fsz=25, ekor=None)
    # meja bawah + kotak kacamata
    bentuk(im, [(0, 1110), (1080, 1080), (1080, 1436), (0, 1436)],
           mix(PASIR, TERRA, 0.22), ow=3.4, light=0.22)
    kacamata(im, 300, 1210, 1.15, tone=mix(INK, NAVY, 0.2))
    rrect_on(im, 780, 1160, 990, 1250, 14, mix(TERRA, TERRA_D, 0.45), 1.0,
             outline=mix(INK, NAVY, 0.4), width=3.0)
    line_on(im, (790, 1200), (980, 1200), mix(CREAM, TERRA, 0.4), 2.6, 0.5)
    latar_bawah(im, mix(PASIR, TERRA, 0.26), y0=1436, butir=40, props=False, seed=61)
    bayangan_kartu(im)


def sc_koreksi(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("koreksi54", _dunia_koreksi), (0, 0))
    # tiga lencana menyala bergantian
    for i, cx in enumerate((196, 540, 884)):
        p = 0.5 + 0.5 * math.sin(tl * 2.0 - i * 1.1)
        ring_on(img, cx, 830, 92 + 6 * p, mix(AMBER_H, WHITE, 0.35), 2.8, 0.18 + 0.22 * p)
    # kilau lensa kacamata di meja
    g = 0.5 + 0.5 * math.sin(tl * 3.0 + 1.0)
    ring_on(img, 300 + 54, 1204, 5 + 3 * g, mix(WHITE, CREAM, 0.2), 2.0, 0.3 + 0.3 * g)
    butir_terbang(img, tl, 0, 1080, 220, 1050, 10, mix(CREAM, WHITE, 0.4), seed=31)
    kartu_judul(img, ["DIPERLAMBAT,", "BUKAN DIBATALKAN"], hl="DIPERLAMBAT", y=Y_KARTU, fsz=70,
                tab=mix(TEAL, INK, 0.15), al=al, dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 7 · F6 retina & tanda bahaya
def _dunia_retina(im):
    """Pandangan fundus: retina bundar dengan pembuluh, robekan, dan tirai yang menutup."""
    im.paste(grad_v(1080, 1436, [(0.0, mix(NAVY_D, TEAL_D, 0.28)), (0.55, mix(NAVY, TEAL_D, 0.40)),
                                 (1.0, mix(NAVY_D, INK, 0.30))], seed=67), (0, 0))

    cx, cy, r = 372, 640, 300
    # dinding retina (cakram fundus) - merah-tua, dengan cincin luar
    ring_on(im, cx, cy, r + 16, mix(CREAM, TERRA, 0.55), 3.0, 0.25)
    elips_vol(im, cx, cy, r, r, mix(TERRA_D, TERRA, 0.42), outline=mix(INK, NAVY, 0.5), ow=4.6, light=0.20)
    # tekstur retina (butir halus)
    rng = np.random.default_rng(53)
    for i in range(120):
        a = rng.random() * 2 * math.pi
        rr = r * math.sqrt(rng.random()) * 0.98
        dot_on(im, cx + rr * math.cos(a), cy + rr * math.sin(a), 1.2 + rng.random() * 2.4,
               mix(TERRA, INK, 0.30), 0.10 + rng.random() * 0.12)
    # pembuluh darah: dari diskus optik (kiri) menyebar ke kanan
    for i in range(9):
        a0 = -1.15 + i * 0.29
        pts = [(cx - r * 0.72, cy + 26)]
        for k in range(1, 6):
            t = k / 5.0
            ang = a0 + 0.22 * math.sin(k * 1.7 + i)
            pts.append((cx - r * 0.72 + t * r * 1.48 * math.cos(ang) * 0.9,
                        cy + 26 + t * r * 1.30 * math.sin(ang)))
        garis_tebal(im, pts, mix(TERRA_D, INK, 0.35), 5.0 - i * 0.3, 0.55, bulge=0.45)
    # diskus optik
    elips_vol(im, cx - r * 0.72, cy + 26, 44, 52, mix(AMBER_H, CREAM, 0.35),
              outline=mix(TERRA_D, INK, 0.3), ow=3.0, light=0.35)
    # makula (bintik gelap di kanan tengah)
    elips_vol(im, cx + r * 0.34, cy + 40, 52, 46, mix(TERRA_D, INK, 0.45), outline=None, ow=0, light=0.1, alpha=0.55)
    # robekan retina (tear) di kanan-atas: lubang gelap + flap
    tear = []
    for i in range(13):
        a = i / 12.0 * 2 * math.pi
        rr = 0.42 + 0.16 * math.sin(i * 2.3 + 1.0)
        tear.append((cx + r * 0.50 + r * 0.20 * rr * math.cos(a), cy - r * 0.36 + r * 0.16 * rr * math.sin(a)))
    bentuk(im, tear, mix(INK, NAVY_D, 0.35), outline=mix(CREAM, TERRA, 0.4), ow=3.0, light=0.10)
    flap = [(cx + r * 0.50 + r * 0.26 * math.cos(a), cy - r * 0.36 + r * 0.22 * math.sin(a))
            for a in np.linspace(0.55, 5.35, 15)]
    garis_tebal(im, flap, mix(CREAM, TERRA, 0.32), 7.0, 0.85, bulge=0.10)

    # tirai gelap menutup dari kiri (gejala "tirai")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(S(0), S(1436)), (S(0), S(210)), (S(150), S(430)),
                                 (S(196), S(1436))], fill=(8, 10, 18, 190))
    lay = lay.filter(ImageFilter.GaussianBlur(S(26)))
    im.paste(lay.convert("RGB"), (0, 0), lay)
    # kilatan di sudut kiri-atas
    for k in range(6):
        a = k * math.pi / 3
        garis_tebal(im, [(120, 168), (120 + 62 * math.cos(a), 168 + 62 * math.sin(a))],
                    mix(WHITE, AMBER_H, 0.25), 2.6, 0.55)
    dot_on(im, 120, 168, 7.0, mix(WHITE, CREAM, 0.2), 0.9)

    latar_bawah(im, mix(NAVY_D, INK, 0.35), y0=1436, butir=36, props=False, seed=67)
    bayangan_kartu(im)


def sc_retina(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("retina54", _dunia_retina), (0, 0))
    cx, cy, r = 372, 640, 300
    # bayangan terbang (floaters) melayang pelan di depan retina
    rng = np.random.default_rng(41)
    for i in range(8):
        px = rng.random(); py = rng.random()
        x = cx + (px - 0.5) * r * 1.5 + 18 * math.sin(tl * 0.5 + i)
        y = cy + (py - 0.5) * r * 1.5 + 16 * math.cos(tl * 0.42 + i * 1.3)
        rr = 5 + rng.random() * 7
        lay = Image.new("RGBA", (int(S(rr * 6)), int(S(rr * 6))), (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse([S(rr), S(rr * 0.6), S(rr * 5), S(rr * 3.4)], fill=(16, 14, 20, 175))
        lay = lay.filter(ImageFilter.GaussianBlur(S(2.4)))
        img.paste(lay.convert("RGB"), (int(round(S(x - rr * 3))), int(round(S(y - rr * 3)))), lay)
    # kilatan berdenyut
    p = 0.5 + 0.5 * math.sin(tl * 3.2)
    for k in range(6):
        a = k * math.pi / 3 + tl * 0.15
        garis_tebal(img, [(120, 168), (120 + (46 + 22 * p) * math.cos(a), 168 + (46 + 22 * p) * math.sin(a))],
                    mix(WHITE, AMBER_H, 0.25), 2.4, 0.20 + 0.45 * p)
    dot_on(img, 120, 168, 6 + 3 * p, mix(WHITE, CREAM, 0.15), 0.9)
    # cincin robekan berdenyut (fokus perhatian)
    ring_on(img, cx + r * 0.52, cy - r * 0.36, 92 + 9 * p, mix(CREAM, AMBER_H, 0.3), 2.6, 0.18 + 0.2 * p)
    # tiga tanda bahaya di kolom kanan (tidak menimpa retina)
    for i, (label, y) in enumerate((("BAYANGAN BERTAMBAH", 330), ("ADA KILATAN", 452), ("SEPERTI TIRAI MENUTUP", 574))):
        w = 396
        rrect_on(img, 812 - w / 2, y - 40, 812 + w / 2, y + 40, 30,
                 mix(CREAM, WHITE, 0.55), 0.95, outline=mix(TERRA_D, INK, 0.35), width=2.6)
        paste_c(img, 812, y, label, font("Poppins-SemiBold.ttf", 23), mix(TERRA_D, INK, 0.15), 0.95)
    kartu_judul(img, ["DI ATAS MINUS 6,", "RISIKO NAIK"], hl="MINUS 6", y=Y_KARTU, fsz=70,
                tab=mix(TERRA_D, TERRA, 0.3), al=al, dy=dy)
    sumber(img, "Sumber: IMI · AAO · meta-analisis retina")


# ------------------------------------------------------------------ 8 · OUTRO (kelas lagi, hangat)
def _dunia_outro(im):
    _dunia_kelas(im, senja=True, lengan=1.0)


def sc_outro(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("outro54", _dunia_outro), (0, 0))
    # layang-layang lewat di luar jendela (janji: main di luar)
    q = esmooth(clamp(tl / max(0.6, dur - 0.4)))
    lx = 800 + 150 * q
    ly = 470 - 90 * q + 14 * math.sin(tl * 1.8)
    layangan(img, lx, ly, 0.62, tilt=0.2, t=tl, tone=mix(TERRA, AMBER_H, 0.3))
    # berkas cahaya senja
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(S(780), S(240)), (S(1016), S(240)), (S(700), S(1180)), (S(300), S(1180))],
                                fill=(255, 206, 150, 34))
    lay = lay.filter(ImageFilter.GaussianBlur(S(26)))
    img.paste(lay.convert("RGB"), (0, 0), lay)
    butir_terbang(img, tl, 240, 1000, 300, 1200, 16, mix(CREAM, SENJA, 0.4), seed=19)
    kartu_judul(img, ["DUA JAM DI BAWAH", "LANGIT TERBUKA"], hl="DUA JAM", y=Y_KARTU, fsz=68,
                tab=mix(TERRA, AMBER_H, 0.35), al=al, dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ daftar & cue
VISUALS = {
    "mata_intro60": sc_intro,
    "mata_optik60": sc_optik,
    "mata_panjang60": sc_panjang,
    "mata_ruang60": sc_ruang,
    "mata_bukti60": sc_bukti,
    "mata_koreksi60": sc_koreksi,
    "mata_retina60": sc_retina,
    "mata_loop60": sc_outro,
}

CUES = {
    "mata_intro60": {"coba": ("Coba", 0.02), "lepas": ("lepas", 0.09), "kacamatamu": ("kacamatamu", 0.17),
                     "dunia": ("dunia", 0.28), "buram": ("buram", 0.36), "bukan": ("bukan", 0.46),
                     "lensa": ("lensa", 0.54), "salah": ("salah", 0.61), "bola": ("bola", 0.70),
                     "matamu": ("matamu", 0.77), "memanjang": ("memanjang", 0.86), "kembali": ("kembali", 0.95)},
    "mata_optik60": {"bola": ("Bola", 0.02), "normal": ("normal", 0.08), "24": ("24", 0.15),
                     "milimeter": ("milimeter", 0.20), "cahaya": ("cahaya", 0.28), "kornea": ("kornea", 0.35),
                     "lensa": ("lensa", 0.40), "jatuhtepat": ("jatuh", 0.47), "retina": ("retina", 0.54),
                     "memanjang": ("memanjang", 0.64), "mundur": ("mundur", 0.72), "buram": ("buram", 0.86)},
    "mata_panjang60": {"setiap": ("Setiap", 0.02), "tambahan": ("tambahan", 0.08), "satu": ("satu", 0.15),
                       "milimeter": ("milimeter", 0.20), "tiga": ("tiga", 0.30), "minus": ("minus", 0.36),
                       "memanjang": ("memanjang", 0.48), "menyusut": ("menyusut", 0.58), "otot": ("otot", 0.70),
                       "lelah": ("lelah", 0.76), "dibatalkan": ("dibatalkan", 0.90)},
    "mata_ruang60": {"lingkungan": ("lingkungan", 0.06), "dekat": ("dekat", 0.18), "ruangan": ("ruangan", 0.25),
                     "redup": ("redup", 0.32), "matahari": ("matahari", 0.44), "terang": ("terang", 0.55),
                     "lampu": ("lampu", 0.62), "kamar": ("kamar", 0.67), "menahan": ("menahan", 0.88)},
    "mata_bukti60": {"guangzhou": ("Guangzhou", 0.03), "anak": ("anak", 0.10), "40": ("40", 0.17),
                     "menit": ("menit", 0.21), "luar": ("luar", 0.27), "miopia": ("miopia", 0.38),
                     "30": ("30", 0.44), "persen": ("persen", 0.49), "39": ("39", 0.56),
                     "dua": ("dua", 0.72), "jam": ("jam", 0.76), "seperempat": ("seperempat", 0.90)},
    "mata_koreksi60": {"kacamata": ("Kacamata", 0.02), "melemahkan": ("melemahkan", 0.11),
                       "lasik": ("LASIK", 0.26), "fokus": ("fokus", 0.35), "panjang": ("panjang", 0.44),
                       "memperlambat": ("memperlambat", 0.60), "luar": ("luar", 0.72),
                       "atropin": ("atropin", 0.82), "lensa": ("lensa", 0.92)},
    "mata_retina60": {"minus": ("minus", 0.06), "enam": ("enam", 0.11), "retina": ("retina", 0.26),
                      "lepas": ("lepas", 0.35), "glaukoma": ("glaukoma", 0.44), "bayangan": ("bayangan", 0.58),
                      "kilatan": ("kilatan", 0.70), "tirai": ("tirai", 0.78), "periksa": ("periksa", 0.92)},
    "mata_loop60": {"kacamata": ("Kacamata", 0.03), "melihat": ("melihat", 0.15), "dua": ("dua", 0.36),
                    "jam": ("jam", 0.41), "langit": ("langit", 0.50), "memanjang": ("memanjang", 0.85)},
}

SFX = {
    "mata_intro60": {"coba": ("pop", 0.45, 0), "buram": ("swish", 0.40, 0), "memanjang": ("riser", 0.35, 0)},
    "mata_optik60": {"cahaya": ("ding", 0.45, 0), "retina": ("pop", 0.45, 0), "buram": ("swish", 0.40, 0)},
    "mata_panjang60": {"tambahan": ("pop", 0.45, 0), "minus": ("click", 0.45, 0), "menyusut": ("thud", 0.45, 0)},
    "mata_ruang60": {"dekat": ("pop", 0.40, 0), "matahari": ("ding", 0.40, 0), "menahan": ("swish", 0.40, 0)},
    "mata_bukti60": {"guangzhou": ("pop", 0.40, 0), "30": ("click", 0.40, 0), "39": ("click", 0.40, 0),
                     "seperempat": ("riser", 0.35, 0)},
    "mata_koreksi60": {"melemahkan": ("thud", 0.40, 0), "fokus": ("click", 0.40, 0), "memperlambat": ("ding", 0.40, 0)},
    "mata_retina60": {"lepas": ("thud", 0.45, 0), "glaukoma": ("riser", 0.35, 0), "periksa": ("ding", 0.40, 0)},
    "mata_loop60": {"kacamata": ("pop", 0.40, 0), "langit": ("ding", 0.40, 0), "memanjang": ("swish", 0.40, 0)},
}
BEATS54 = {k: [] for k in CUES}


def events_v12(sc):
    vis = sc.get("visual", "")
    if vis not in CUES:
        return []
    c = M.cues(sc, sc["dur"], {k: v for k, v in CUES[vis].items()})
    out = [(sc["start"] + c[nama] + off, jenis, g) for nama, (jenis, g, off) in SFX.get(vis, {}).items()]
    if str(sc.get("trans") or "").lower() == "morph":
        out.append((sc["start"] - 0.08, "morph", 0.55))
    return out


def daftar():
    M11.BEATS.update(BEATS54)
    D.VISUALS.update(VISUALS)
    M.EVENTS12.update({k: events_v12 for k in CUES})
    return sorted(VISUALS)


daftar()


if __name__ == "__main__":
    D.SS = 1.0
    im = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), CREAM)
    for nama, fn in VISUALS.items():
        sc = {"id": nama.split("60")[0].replace("mata_", ""), "visual": nama, "start": 10.0,
              "dur": 14.0, "trans": "morph", "accent": "#A85F3C", "captions": []}
        for tl in (0.0, 0.12, 2.0, 7.0, 13.98):
            fn(im, None, sc, tl, 14.0, 10.0 + tl, (168, 95, 60), 1.0, 0.0)
        assert events_v12(sc), nama
    print(f"selftest ep54: {len(VISUALS)} visual OK ({sum(len(v) for v in CUES.values())} cue, "
          f"{sum(len(v) for v in SFX.values())} SFX)")
