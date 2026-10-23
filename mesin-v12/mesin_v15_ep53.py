#!/usr/bin/env python3
"""mesin_v15_ep53.py — Ep53 "Ke Mana Angin Pergi Setelah Meniup?"

Mesin ILUSTRASI penuh layar (v15). Delapan dunia, satu pesawat kertas yang
ditiup angin dari pantai, keliling bumi, lalu kembali ke tangan anak itu.
Palet KlikTahu (krem/navy/terakota/teal/olive) — bukan palet video acuan.

Selftest:  python3 mesin_v15_ep53.py
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
                      font, tw, tlh, paste_c, rrect_on, line_on, dot_on, ring_on, poly_on)
from mesin_v15_ilustrasi import (KREM, LANGIT, LANGIT_2, SENJA, TEAL, TEAL_D, TEAL_L, PASIR,
                                 PASIR_D, TERRA, TERRA_D, OLIVE, OLIVE_D, NAVY, NAVY_D,
                                 LANGIT_MALAM, AMBER_H, grad_v, elips_vol, bentuk, awan,
                                 gunung, bukit, laut, pasir, cahaya_matahari, matahari,
                                 pohon_kelapa, perahu, rumah, orang, layangan, angin, hujan,
                                 tetes, bintang_laut, judul, kartu_judul, sumber, gelembung,
                                 angka_besar, inset, garis_dasar, butir_terbang, kurva,
                                 garis_tebal, S, mask_outline)

SUMBER = "Sumber: NOAA · BMKG · NASA"
Y_KARTU = 1490

# ------------------------------------------------------------------ cache dasar
_BASE = {}
_CACHE_DIR = os.path.join(os.environ.get("KT_BUILD", "build"), "v15base")


def _base(nama, builder):
    """Dasar adegan: cache memori -> cache disk (PNG) -> gambar baru.

    Dasar digambar sekali saja; tiap proses render hanya memuat PNG (±0,3 s),
    bukan menggambar ulang seluruh ilustrasi (10 s).
    """
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


def _copy(im):
    return im.copy()


def latar_bawah(im, tone, y0=1240, butir=70, props=True, seed=3):
    """Isi bidang bawah sampai tepi kanvas: tanah/pasir bergradasi + butir + properti.

    Tujuan: tidak ada pita krem kosong di bawah ilustrasi (acuan selalu penuh layar).
    """
    h = 1920 - y0
    band = grad_v(1080, h, [(0.0, mix(tone, WHITE, 0.30)), (0.55, tone), (1.0, mix(tone, INK, 0.18))], seed=seed)
    im.paste(band, (0, int(round(S(y0)))))
    rng = np.random.default_rng(seed)
    for i in range(butir):                       # butir halus (tekstur tanah)
        x = rng.random() * 1080
        y = y0 + rng.random() * h
        dot_on(im, x, y, 1.4 + rng.random() * 1.8, mix(tone, INK, 0.35), 0.10 + rng.random() * 0.08)
    if props:
        for i in range(9):                       # batu & rumput kecil di tepi bawah
            x = 40 + i * 122 + rng.random() * 30
            y = 1866 + rng.random() * 30
            if i % 3 == 0:
                elips_vol(im, x, y, 14 + rng.random() * 10, 8 + rng.random() * 5,
                          mix(tone, INK, 0.28), outline=mix(tone, INK, 0.55), ow=2.0, light=0.20)
            else:
                for k in range(3):
                    garis_tebal(im, [(x + k * 7, y + 12), (x + k * 7 - 5 + rng.random() * 4, y - 16 - rng.random() * 12)],
                                mix(OLIVE, tone, 0.35), 3.0, 0.55)


def bayangan_kartu(im, y=1618, w=880, alpha=64):
    """Bayangan tipis tepat di bawah kartu judul (kartu terasa duduk di gambar)."""
    lay = Image.new("RGBA", (int(S(1080)), int(S(1920))), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([S(540 - w / 2), S(y), S(540 + w / 2), S(y + 26)],
                                          radius=S(14), fill=(28, 24, 22, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(S(13)))
    im.paste(lay.convert("RGB"), (0, 0), lay)


# ------------------------------------------------------------------ objek khas
def pesawat_kertas(img, x, y, s=1.0, rot=0.0, t=0.0, warna=None):
    """Pesawat kertas: hidung lancip, dua sayap bertone, garis lipatan."""
    warna = warna or mix(CREAM, WHITE, 0.55)
    c, si = math.cos(rot), math.sin(rot)

    def P(px, py):
        return (x + (px * c - py * si) * s, y + (px * si + py * c) * s)

    sayap_atas = [P(-52, 6), P(46, -14), P(58, -2), P(-46, 16)]
    bentuk(img, sayap_atas, warna, ow=3.0, light=0.40)
    sayap_bawah = [P(-46, 16), P(58, -2), P(4, 30), P(-40, 26)]
    bentuk(img, sayap_bawah, mix(warna, NAVY, 0.28), ow=3.0, light=0.24)
    line_on(img, P(-46, 14), P(54, -6), mix(NAVY, INK, 0.5), 2.2, 0.45)


def anak(img, x, y, s=1.0, t=0.0, lengan=0.0):
    """Anak pantai: topi jerami, kaus terakota, celana pendek navy."""
    # kaki
    garis_tebal(img, [(x - 12 * s, y - 6 * s), (x - 14 * s, y + 2 * s)], mix(NAVY, INK, 0.3), 11 * s, 1.0)
    garis_tebal(img, [(x + 12 * s, y - 6 * s), (x + 16 * s, y + 2 * s)], mix(NAVY, INK, 0.3), 11 * s, 1.0)
    # badan
    bentuk(img, [(x - 26 * s, y - 96 * s), (x + 26 * s, y - 96 * s),
                 (x + 22 * s, y - 12 * s), (x - 22 * s, y - 12 * s)],
           mix(TERRA, AMBER_H, 0.25), ow=3.2, light=0.26)
    # celana
    bentuk(img, [(x - 23 * s, y - 24 * s), (x + 23 * s, y - 24 * s),
                 (x + 21 * s, y - 4 * s), (x - 21 * s, y - 4 * s)],
           NAVY, ow=3.0, light=0.22)
    # lengan kanan terangkat memegang pesawat
    garis_tebal(img, [(x + 22 * s, y - 86 * s), (x + (40 + 16 * lengan) * s, y - (92 + 30 * lengan) * s)],
                mix(TERRA, AMBER_H, 0.18), 10 * s, 1.0)
    garis_tebal(img, [(x - 22 * s, y - 86 * s), (x - 40 * s, y - 58 * s)],
                mix(TERRA, AMBER_H, 0.18), 10 * s, 1.0)
    # kepala
    elips_vol(img, x, y - 116 * s, 21 * s, 22 * s, mix(TERRA, AMBER_H, 0.55), ow=3.0, light=0.34)
    # topi jerami
    bentuk(img, [(x - 30 * s, y - 130 * s), (x + 30 * s, y - 130 * s),
                 (x + 18 * s, y - 140 * s), (x - 18 * s, y - 140 * s)],
           mix(AMBER_H, CREAM, 0.35), ow=2.8, light=0.30)
    bentuk(img, [(x - 19 * s, y - 138 * s), (x - 13 * s, y - 158 * s),
                 (x + 13 * s, y - 158 * s), (x + 19 * s, y - 138 * s)],
           mix(AMBER_H, CREAM, 0.45), ow=2.8, light=0.34)
    line_on(img, (x - 30 * s, y - 129 * s), (x + 30 * s, y - 129 * s), mix(TERRA_D, INK, 0.3), 2.4, 0.45)


def gunung_api(img, cx, base, w, h, t=0.0):
    """Gunung berapi: kerucut bergerigi, kawah, asap naik perlahan."""
    bentuk(img, [(cx - w / 2, base), (cx - w * 0.16, base - h * 0.86), (cx - w * 0.05, base - h),
                 (cx + w * 0.07, base - h), (cx + w * 0.18, base - h * 0.84), (cx + w / 2, base)],
           mix(NAVY, TEAL_D, 0.55), ow=3.6, light=0.14)
    bentuk(img, [(cx - w * 0.05, base - h), (cx + w * 0.07, base - h),
                 (cx + w * 0.04, base - h + 26), (cx - w * 0.03, base - h + 22)],
           mix(TERRA, INK, 0.25), ow=2.6, light=0.20)
    for i in range(4):
        yy = base - h - 20 - i * 46 - (t * 16) % 46
        rr = 16 + i * 12
        ring_on(img, cx, yy, rr, mix(CREAM, MUTED, 0.55), 3.0, 0.30 - i * 0.05)


def globe(img, cx, cy, r, t=0.0, benua=None):
    """Bumi kartun: bola bergradasi + benua yang menempel di permukaan (clip bola).

    Urutan lapis: bola -> kilau & bayangan (di BAWAH benua) -> benua.
    Kilau harus lembut; kalau digambar di atas benua ia terbaca sebagai kabut/noda.
    """
    elips_vol(img, cx, cy, r, r, mix(TEAL, TEAL_D, 0.30), outline=mix(NAVY, INK, 0.55), ow=4.2, light=0.34)
    size = int(round(S(2 * r)))
    if size < 8:
        return
    ox, oy = int(round(S(cx - r))), int(round(S(cy - r)))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)

    # 1) kilau (kiri-atas) + bayangan (kanan-bawah), di bawah benua
    lap = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lap)
    dl.ellipse([S(r * 0.02), S(r * 0.02), S(r * 0.92), S(r * 0.80)],
               fill=mix(CREAM, WHITE, 0.55) + (52,))
    dl.ellipse([S(r * 0.42), S(r * 0.36), S(r * 1.62), S(r * 1.72)],
               fill=mix(TEAL_D, INK, 0.45) + (74,))
    lap = lap.filter(ImageFilter.GaussianBlur(S(30)))
    lap.putalpha(Image.fromarray(np.minimum(np.asarray(lap.getchannel("A")), np.asarray(mask))))
    img.paste(lap.convert("RGB"), (ox, oy), lap)

    # 2) benua (menempel di permukaan, ter-clip bola)
    lay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    benua = benua or [(-0.40, -0.38, 0.17, 0.13, -12), (-0.14, -0.20, 0.13, 0.19, 18),
                      (0.26, -0.30, 0.15, 0.12, 6), (0.34, 0.06, 0.19, 0.15, -14),
                      (-0.44, 0.18, 0.13, 0.10, 8), (-0.06, 0.42, 0.22, 0.12, -6)]
    for (dx, dy, rw, rh, rot) in benua:
        w2 = int(S(rw * 2.0 * r)) + 6
        h2 = int(S(rh * 2.0 * r)) + 6
        rr = Image.new("RGBA", (w2, h2), (0, 0, 0, 0))
        dd = ImageDraw.Draw(rr)
        pts = []
        n = 9
        for i in range(n):
            a = i * 2 * math.pi / n
            wob = 0.80 + 0.20 * math.sin(i * 2.1 + dx * 7 + dy * 5)
            pts.append((w2 / 2 + w2 * 0.46 * wob * math.cos(a), h2 / 2 + h2 * 0.46 * wob * math.sin(a)))
        dd.polygon(pts, fill=mix(OLIVE, AMBER_H, 0.20) + (255,),
                   outline=mix(OLIVE_D, INK, 0.30) + (255,), width=max(1, int(S(1.6))))
        rr = rr.rotate(rot, resample=Image.BICUBIC, expand=False)
        lay.alpha_composite(rr, (int((dx + 1) * r * S(1) - w2 / 2), int((dy + 1) * r * S(1) - h2 / 2)))
    lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.getchannel("A")), np.asarray(mask))))
    img.paste(lay.convert("RGB"), (ox, oy), lay)


def uap(img, pts, t, tone=None, alpha=0.55):
    tone = tone or mix(CREAM, WHITE, 0.4)
    for i, p in enumerate(pts):
        ph = t * 1.4 + i * 0.8
        rr = 8 + 6 * math.sin(ph) + i * 1.5
        dot_on(img, p[0] + 6 * math.sin(ph * 0.8), p[1], rr, tone, alpha * (0.9 - i * 0.06))


# ------------------------------------------------------------------ 1 · INTRO (pantai pagi)
def _dunia_intro(im, senja=False):
    a0 = mix(LANGIT, CREAM, 0.25) if not senja else mix(SENJA, CREAM, 0.35)
    a1 = LANGIT_2 if not senja else mix(SENJA, TERRA, 0.22)
    V.langit(im, 0, 1120, a0, a1, seed=53 if not senja else 71)
    cahaya_matahari(im, 800, 300, 110, 0.85 if not senja else 1.0,
                    mix(AMBER_H, WHITE, 0.5) if not senja else mix(TERRA, AMBER_H, 0.4))
    matahari(im, 800, 300, 104, 0.0, mix(TERRA, AMBER_H, 0.5) if not senja else mix(TERRA, TERRA_D, 0.15))
    for (cx, cy, w, h, sd) in ((330, 250, 300, 120, 2), (700, 470, 220, 96, 6), (180, 560, 190, 80, 9)):
        awan(im, cx, cy, w, h, seed=sd)
    laut(im, 1080, 1240, 0.0, mix(TEAL, TEAL_L, 0.18) if not senja else mix(TEAL_D, TEAL, 0.4))
    pasir(im, 1226)
    bukit(im, 1140, 40, mix(PASIR, TERRA, 0.25), seed=13, n=3)
    pohon_kelapa(im, 128, 1300, 1.05, 0.0)
    pohon_kelapa(im, 214, 1322, 0.82, 0.0)
    perahu(im, 840, 1120, 0.9, 0.0)
    bintang_laut(im, 930, 1382, 0.8, rot=0.3)
    for i in range(7):                      # kerang
        dot_on(im, 180 + i * 96, 1330 + (i % 3) * 26, 5, mix(PASIR, TERRA, 0.3), 0.5)
    anak(im, 560, 1352, 1.0, 0.0, lengan=0.6)
    latar_bawah(im, PASIR, y0=1436, butir=60, seed=53)
    bayangan_kartu(im)


def sc_intro(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("intro", _dunia_intro), (0, 0))
    # pesawat kertas lepas dari tangan, tertiup ke kanan-atas
    q = esmooth(clamp((tl - 0.25) / max(0.4, dur - 0.5)))
    px = 560 + 40 + 300 * q
    py = 1180 - 60 - 300 * q + 22 * math.sin(tl * 2.0)
    pesawat_kertas(img, px, py, 1.0, rot=-0.30 + 0.06 * math.sin(tl * 2.4), t=tl)
    # pita angin mendorong dari kiri
    for k in range(3):
        y0 = 980 + k * 90
        pts = kurva((60, y0), (330, y0 - 40 - 14 * k), (760 + 60 * k, y0 - 10 + 18 * math.sin(tl * 1.4 + k)), 20)
        angin(img, pts, tl + k * 0.6, w=6.5 - k, alpha=0.34 - k * 0.06, ekor=2)
    butir_terbang(img, tl, 0, 1080, 700, 1250, 16, mix(CREAM, WHITE, 0.5), seed=5)
    kartu_judul(img, ["ANGIN TIDAK", "PERGI — IA PINDAH"], hl="PINDAH", y=Y_KARTU, fsz=78,
                tab=mix(TERRA, AMBER_H, 0.3), dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 2 · F1 tekanan
def _dunia_tekanan(im):
    V.langit(im, 0, 1080, mix(LANGIT, CREAM, 0.20), LANGIT_2, seed=61)
    cahaya_matahari(im, 540, 190, 130, 0.55)
    for (cx, cy, w, h, sd) in ((250, 250, 260, 104, 3), (820, 320, 220, 92, 8)):
        awan(im, cx, cy, w, h, seed=sd)
    # bukit (tekanan tinggi) kiri, laut (tekanan rendah) kanan
    bentuk(im, [(0, 1080), (0, 760), (150, 640), (300, 700), (470, 600), (560, 720), (560, 1080)],
           mix(OLIVE, TEAL_D, 0.35), ow=3.6, light=0.18)
    bentuk(im, [(560, 1080), (560, 720), (760, 680), (900, 740), (1080, 660), (1080, 1080)],
           mix(PASIR, TERRA, 0.30), ow=3.6, light=0.18)
    laut(im, 860, 1250, 0.0, mix(TEAL, TEAL_L, 0.10))
    pasir(im, 1236)
    pohon_kelapa(im, 180, 700, 0.9, 0.0)
    pohon_kelapa(im, 330, 700, 0.7, 0.0)
    perahu(im, 860, 1150, 0.85, 0.0)
    # label tekanan: kolom udara padat vs longgar
    for i in range(7):
        dot_on(im, 250 + (i % 3) * 44, 800 + (i // 3) * 44, 7.5, mix(CREAM, WHITE, 0.4), 0.34)
    for i in range(4):
        dot_on(im, 860 + (i % 2) * 88, 860 + (i // 2) * 70, 7.0, mix(CREAM, WHITE, 0.4), 0.22)
    latar_bawah(im, mix(PASIR, TEAL, 0.25), y0=1440, butir=50, seed=61)
    bayangan_kartu(im)


def sc_tekanan(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("tekanan", _dunia_tekanan), (0, 0))
    # panah udara: dari bukit ke laut (kanan), mengalir terus
    for k in range(2):
        ph = (tl * 0.55 + k * 0.5) % 1.0
        y0 = 940 + k * 54
        pts = kurva((300, y0), (620, y0 - 40), (940, y0 + 16), 22)
        angin(img, pts, tl + k, w=8.0, alpha=0.62, ekor=3)
        # kepala panah bergerak
        ax = 380 + 520 * ph
        ay = y0 - 18 * math.sin((ax - 300) / 320 * math.pi)
        poly_on(img, [(ax + 16, ay), (ax - 14, ay - 13), (ax - 14, ay + 13)],
                mix(CREAM, WHITE, 0.45), 0.9)
    angka_besar(img, 235, 725, "1013", "hPa", mix(NAVY, INK, 0.05), fsz=76)
    angka_besar(img, 875, 755, "1006", "hPa", mix(NAVY, INK, 0.05), fsz=76)
    butir_terbang(img, tl, 0, 1080, 700, 1100, 12, mix(CREAM, WHITE, 0.4), seed=7)
    kartu_judul(img, ["UDARA PINDAH KE", "TEMPAT YANG LONGGAR"], hl="LONGGAR", y=Y_KARTU,
                fsz=74, tab=mix(TEAL, INK, 0.2), dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 3 · F2 angin laut (siang)
def _dunia_laut_siang(im):
    V.langit(im, 0, 800, mix(LANGIT, CREAM, 0.40), LANGIT_2, seed=67)
    cahaya_matahari(im, 300, 250, 130, 1.0)
    matahari(im, 300, 250, 104, 0.0, mix(AMBER_H, TERRA, 0.28))
    for (cx, cy, w, h, sd) in ((720, 190, 250, 96, 4), (860, 340, 200, 84, 7), (150, 440, 210, 80, 11)):
        awan(im, cx, cy, w, h, seed=sd)
    # bukit jauh (di belakang garis pantai, masih di langit)
    bentuk(im, [(430, 830), (600, 640), (760, 710), (900, 620), (1080, 720), (1080, 830)],
           mix(OLIVE, TEAL_D, 0.45), ow=3.2, light=0.14)
    # laut (kiri) lalu DARAT menimpanya di kanan -> batas pantai miring yang bersih
    laut(im, 800, 1340, 0.0, mix(TEAL, TEAL_L, 0.12))
    bentuk(im, [(350, 1340), (1080, 900), (1080, 1340)], mix(PASIR, TERRA, 0.14), ow=0.0, light=0.20)
    pantai = [(330, 1170), (1080, 900), (1080, 1340), (330, 1340)]
    bentuk(im, pantai, mix(PASIR, WHITE, 0.24), ow=3.0, light=0.26)
    for i in range(4):                       # buih di garis pantai
        t0 = i / 4
        p0 = (348 + (1080 - 348) * t0, 1160 + (900 - 1160) * t0)
        p1 = (348 + (1080 - 348) * min(1.0, t0 + 0.18), 1160 + (900 - 1160) * min(1.0, t0 + 0.18))
        garis_tebal(im, [p0, p1], mix(CREAM, WHITE, 0.5), 6.0, 0.55)
    # rumah panggung di darat, dua ukuran
    rumah(im, 780, 1040, 0.92, 0.0)
    rumah(im, 980, 966, 0.74, 0.0)
    pohon_kelapa(im, 620, 1108, 0.80, 0.0)
    pohon_kelapa(im, 552, 1156, 0.64, 0.0)
    perahu(im, 210, 1120, 0.72, 0.0)
    # panas dari darat: garis getar tipis
    for i in range(5):
        x = 650 + i * 92
        pts = [(x + 8 * math.sin(j * 1.2 + i), 1090 - j * 22) for j in range(9)]
        garis_tebal(im, pts, mix(TERRA, AMBER_H, 0.5), 2.6, 0.16)
    latar_bawah(im, mix(PASIR, TERRA, 0.18), y0=1340, butir=60, seed=67)


def sc_laut_siang(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("laut_siang", _dunia_laut_siang), (0, 0))
    # udara naik di atas darat (gelembung) + angin masuk dari laut
    for i in range(4):
        ph = (tl * 0.42 + i * 0.25) % 1.0
        cx = 660 + i * 110
        cy = 1120 - 520 * ph
        rr = 18 + 26 * ph
        ring_on(img, cx + 14 * math.sin(ph * 5 + i), cy, rr, mix(CREAM, WHITE, 0.45), 3.2, 0.42 * (1 - ph))
    for k in range(2):
        y0 = 1130 + k * 80
        pts = kurva((150, y0), (420, y0 - 60), (700, y0 - 180), 22)
        angin(img, pts, tl + k * 0.8, w=7.0, alpha=0.50, ekor=2)
    gelembung(img, 250, 585, "LAUT · DINGIN", w=344, fsz=33, ekor=None)
    gelembung(img, 845, 585, "DARAT · PANAS", w=356, fsz=33, ekor=None)
    kartu_judul(img, ["ANGIN LAUT", "MASUK KE DARAT"], hl="ANGIN LAUT", y=Y_KARTU, fsz=76,
                tab=mix(TEAL, INK, 0.25), dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 4 · F3 bumi & sel
def _dunia_bumi(im):
    latar = grad_v(1080, 1920, [(0.0, mix(NAVY_D, TEAL_D, 0.40)), (0.50, NAVY_D),
                                (1.0, mix(NAVY, TEAL_D, 0.30))], seed=73)
    im.paste(latar, (0, 0))
    rng = np.random.default_rng(31)
    for i in range(70):                      # bintang latar
        x, y = rng.random() * 1080, rng.random() * 1200
        s = 1.2 + rng.random() * 2.2
        dot_on(im, x, y, s, mix(WHITE, CREAM, 0.2), 0.20 + 0.5 * rng.random())
    globe(im, 540, 520, 288)
    # cincin atmosfer
    for i in range(3):
        ring_on(im, 540, 520, 294 + i * 12, mix(TEAL_L, WHITE, 0.35), 3.0, 0.16 - i * 0.04)
    latar_bawah(im, mix(NAVY, TEAL_D, 0.45), y0=1300, butir=26, props=False, seed=73)


def sc_bumi(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("bumi", _dunia_bumi), (0, 0))
    # garis lintang pada bola (tipis, hanya di dalam bidang bola)
    for i in range(3):
        ry = 520 - 130 + i * 130
        rr = 280 * math.sqrt(max(0.05, 1 - ((ry - 520) / 280.0) ** 2))
        arc = [(540 + rr * math.cos(math.pi + k * math.pi / 22), ry + 24 * math.sin(k * math.pi / 22))
               for k in range(23)]
        garis_tebal(img, arc, mix(TEAL_L, WHITE, 0.45), 3.0, 0.34)
        # ujung panah di sisi kanan pita: arah angin ke timur
        ax, ay = arc[-1]
        tri = [(ax - 26, ay - 17), (ax + 16, ay), (ax - 26, ay + 17)]
        bentuk(img, tri, mix(AMBER_H, CREAM, 0.45), ow=0.0, light=0.30)
    # jalur angin mengelilingi bumi: cincin penuh tipis + ekor terang di belakang pesawat
    def _orbit(a):
        return (540 + 356 * math.cos(a), 560 + 176 * math.sin(a))
    ring = [_orbit(i * 2 * math.pi / 48) for i in range(49)]
    garis_tebal(img, ring, mix(AMBER_H, CREAM, 0.45), 2.6, 0.20, bulge=0.25)
    th = tl * 1.1
    ekor = [_orbit(th - 1.15 + i * 0.085) for i in range(14)]
    garis_tebal(img, ekor, mix(AMBER_H, CREAM, 0.30), 5.2, 0.55, bulge=0.5)
    px, py = _orbit(th)
    pesawat_kertas(img, px, py, 0.60, rot=th + math.pi / 2 + 0.30, t=tl)
    angka_besar(img, 300, 1215, "40.075", "km", mix(CREAM, WHITE, 0.66), fsz=78)
    paste_c(img, 300, 1268, "keliling bumi", font("Poppins-Regular.ttf", 30), mix(CREAM, MUTED, 0.30), 0.72)
    kartu_judul(img, ["ANGIN BISA", "KELILING BUMI"], hl="KELILING BUMI", y=Y_KARTU + 40, fsz=78,
                tab=mix(TERRA, AMBER_H, 0.35), dy=dy)
    sumber(img, SUMBER, y=1692)


# ------------------------------------------------------------------ 5 · F4 angin membawa air
def _dunia_hujan(im):
    V.langit(im, 0, 1000, mix(LANGIT, CREAM, 0.10), mix(LANGIT_2, TEAL_L, 0.30), seed=79)
    for (cx, cy, w, h, sd, tone) in ((280, 300, 300, 130, 4, mix(CREAM, WHITE, 0.35)),
                                     (760, 240, 260, 110, 9, mix(CREAM, MUTED, 0.25)),
                                     (560, 430, 340, 140, 12, mix(CREAM, MUTED, 0.35))):
        awan(im, cx, cy, w, h, tone=tone, seed=sd)
    # gunung + hujan di lereng
    gunung(im, 700, 1180, 620, 520, mix(OLIVE, TEAL_D, 0.35), seed=17, salju=True)
    gunung(im, 330, 1180, 430, 356, mix(OLIVE_D, TEAL_D, 0.45), seed=23, salju=True)
    bukit(im, 1150, 40, mix(OLIVE, TEAL_D, 0.25), seed=41, n=3)
    laut(im, 1180, 1330, 0.0, mix(TEAL, TEAL_L, 0.08))
    pasir(im, 1318)
    perahu(im, 870, 1240, 0.7, 0.0)
    # sungai dari gunung ke laut
    sungai = kurva((690, 1180), (620, 1260), (470, 1300), 22)
    garis_tebal(im, sungai, mix(TEAL_L, WHITE, 0.35), 12, 0.55, bulge=0.3)
    latar_bawah(im, mix(OLIVE_D, PASIR, 0.45), y0=1436, butir=60, seed=79)
    bayangan_kartu(im)


def sc_hujan(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("hujan", _dunia_hujan), (0, 0))
    hujan(img, 420, 900, 180, 1150, tl, mix(CREAM, WHITE, 0.45), n=34, condong=7.0, alpha=0.52)
    # uap naik dari laut
    for i in range(7):
        ph = (tl * 0.30 + i / 7) % 1.0
        x = 220 + i * 110
        y = 1300 - 420 * ph + 18 * math.sin(ph * 6 + i)
        dot_on(img, x, y, 7 + 8 * ph, mix(CREAM, WHITE, 0.45), 0.40 * (1 - ph))
    # awan bergerak tipis
    gelembung(img, 232, 1180, "UAP NAIK", w=300, fsz=32, ekor=None)
    kartu_judul(img, ["ANGIN MEMBAWA AIR", "KELILING BUMI"], hl="AIR", y=Y_KARTU + 30, fsz=72,
                tab=mix(TEAL, INK, 0.2), dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 6 · F5 muson Indonesia
def _dunia_muson(im):
    V.langit(im, 0, 1000, mix(LANGIT, CREAM, 0.20), LANGIT_2, seed=83)
    cahaya_matahari(im, 540, 150, 120, 0.5)
    # peta kepulauan sederhana (bukan peta akurat): tiga gugus pulau
    for (x, y, w, h, sd) in ((300, 960, 330, 140, 3), (700, 1010, 300, 120, 5), (500, 800, 230, 96, 9)):
        bentuk(im, [(x - w / 2, y), (x - w * 0.2, y - h * 0.9), (x + w * 0.25, y - h * 0.6),
                    (x + w / 2, y + h * 0.1), (x + w * 0.1, y + h * 0.4), (x - w * 0.35, y + h * 0.3)],
               mix(OLIVE, AMBER_H, 0.22), ow=3.2, light=0.22)
    laut(im, 1000, 1330, 0.0, mix(TEAL, TEAL_L, 0.10))
    pasir(im, 1320)
    bintang_laut(im, 900, 1380, 0.7, rot=0.2)
    perahu(im, 220, 1240, 0.72, 0.0)
    latar_bawah(im, PASIR, y0=1436, butir=55, seed=83)
    bayangan_kartu(im)


def sc_muson(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("muson", _dunia_muson), (0, 0))
    # dua fase: Januari (dari Asia, basah) & Juli (dari Australia, kering)
    p = clamp((tl - dur * 0.34) / (dur * 0.30))
    fase = "basah" if p < 0.5 else "kering"
    if fase == "basah":
        for k in range(3):
            y0 = 700 + k * 90
            pts = kurva((80, y0 - 120), (400, y0 - 60), (900, y0 + 120), 22)
            angin(img, pts, tl + k, w=7.0, alpha=0.50, ekor=2)
        hujan(img, 200, 900, 620, 1050, tl, mix(CREAM, WHITE, 0.5), n=30, condong=5.0, alpha=0.45)
        gelembung(img, 250, 1010, "JANUARI · DARI ASIA", w=430, fsz=32, ekor=None)
    else:
        for k in range(3):
            y0 = 700 + k * 90
            pts = kurva((980, y0 + 120), (700, y0 + 60), (200, y0 - 120), 22)
            angin(img, pts, tl + k, w=7.0, alpha=0.50, ekor=2)
        gelembung(img, 250, 1010, "JULI · DARI AUSTRALIA", w=470, fsz=32, ekor=None)
    kartu_judul(img, ["MUSON: ANGIN", "GANTI ARAH"], hl="MUSON", y=Y_KARTU + 30, fsz=76,
                tab=mix(OLIVE, INK, 0.2), dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 7 · F6 angin berhenti
def _dunia_berhenti(im):
    V.langit(im, 0, 1000, mix(SENJA, CREAM, 0.35), mix(SENJA, TERRA, 0.15), seed=89)
    cahaya_matahari(im, 830, 320, 130, 1.0, mix(TERRA, AMBER_H, 0.35))
    matahari(im, 830, 320, 96, 0.0, mix(TERRA, TERRA_D, 0.15))
    bukit(im, 1050, 60, mix(OLIVE_D, TERRA_D, 0.35), seed=29, n=3)
    bukit(im, 1140, 50, mix(OLIVE, TERRA_D, 0.25), seed=37, n=3)
    pasir(im, 1180)
    pohon_kelapa(im, 180, 1210, 1.0, 0.0)
    pohon_kelapa(im, 268, 1232, 0.78, 0.0)
    rumah(im, 780, 1210, 1.0, 0.0)
    # angin yang melemah: pusaran kecil
    for i in range(3):
        cx, cy = 520 + i * 60, 980 - i * 40
        ring_on(im, cx, cy, 40 + i * 22, mix(CREAM, WHITE, 0.35), 3.0, 0.30 - i * 0.07)
    latar_bawah(im, mix(PASIR, TERRA, 0.35), y0=1436, butir=55, seed=89)
    bayangan_kartu(im)


def sc_berhenti(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("berhenti", _dunia_berhenti), (0, 0))
    # pita angin melambat lalu berhenti
    sp = 1.0 - 0.75 * clamp((tl - dur * 0.30) / (dur * 0.55))
    for k in range(2):
        y0 = 900 + k * 76
        pts = kurva((80 + 40 * sp, y0), (330 + 120 * (1 - sp), y0 - 50), (760 + 180 * (1 - sp), y0), 20)
        angin(img, pts, tl * sp + k, w=6.0, alpha=0.30 + 0.25 * sp, ekor=2)
    angka_besar(img, 250, 800, "20", "km/jam", mix(CREAM, WHITE, 0.75), fsz=74)
    angka_besar(img, 838, 800, "83", "hari", mix(CREAM, WHITE, 0.75), fsz=74)
    kartu_judul(img, ["ANGIN BERHENTI,", "ENERGINYA PINDAH"], hl="ENERGINYA PINDAH", y=Y_KARTU + 30,
                fsz=70, tab=mix(TERRA, TERRA_D, 0.3), dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ 8 · OUTRO (kembali ke pantai)
def _dunia_outro(im):
    _dunia_intro(im)


def sc_outro(img, d, sc, tl, dur, tg, accent, al, dy):
    img.paste(_base("intro", _dunia_intro), (0, 0))
    # pesawat kembali ke tangan anak, lalu diam (loop ke frame 0)
    q = esmooth(clamp((tl - 0.15) / max(0.4, dur - 1.0)))
    px = 900 - 300 * q
    py = 880 + 300 * q + 18 * math.sin(tl * 2.0) * (1 - q)
    pesawat_kertas(img, px, py, 1.0 - 0.06 * q, rot=-0.28 + 0.30 * q, t=tl)
    for k in range(2):
        y0 = 1000 + k * 90
        pts = kurva((60, y0), (330, y0 - 40), (700, y0 - 10), 20)
        angin(img, pts, tl + k * 0.6, w=6.0 - k, alpha=0.30 - k * 0.06, ekor=2)
    butir_terbang(img, tl, 0, 1080, 700, 1250, 14, mix(CREAM, WHITE, 0.5), seed=5)
    kartu_judul(img, ["ANGIN YANG SAMA", "KEMBALI LAGI"], hl="KEMBALI", y=Y_KARTU, fsz=80,
                tab=mix(TERRA, AMBER_H, 0.3), dy=dy)
    sumber(img, SUMBER)


# ------------------------------------------------------------------ daftar & cue
VISUALS = {
    "angin_intro60": sc_intro,
    "angin_tekanan60": sc_tekanan,
    "angin_laut60": sc_laut_siang,
    "angin_bumi60": sc_bumi,
    "angin_hujan60": sc_hujan,
    "angin_muson60": sc_muson,
    "angin_berhenti60": sc_berhenti,
    "angin_loop60": sc_outro,
}

CUES = {
    "angin_intro60": {"angin": ("Angin", 0.02), "meniup": ("meniup", 0.10), "wajahmu": ("wajahmu", 0.18),
                      "pagi": ("pagi", 0.26), "ini": ("ini", 0.33), "mungkin": ("mungkin", 0.40),
                      "sudah": ("sudah", 0.48), "jauh": ("jauh", 0.56), "sebelum": ("sebelum", 0.66),
                      "kamu": ("kamu", 0.74), "bangun": ("bangun", 0.84), "pesawat": ("pesawat", 0.92)},
    "angin_tekanan60": {"udara": ("Udara", 0.03), "selalu": ("selalu", 0.10), "bergerak": ("bergerak", 0.16),
                        "tekanan": ("tekanan", 0.26), "tinggi": ("tinggi", 0.32), "rendah": ("rendah", 0.40),
                        "padat": ("padat", 0.50), "longgar": ("longgar", 0.58), "angin": ("angin", 0.70),
                        "nama": ("nama", 0.78), "untuk": ("untuk", 0.86), "perbedaan": ("perbedaan", 0.94)},
    "angin_laut60": {"siang": ("Siang", 0.03), "darat": ("darat", 0.12), "lebih": ("lebih", 0.20),
                     "cepat": ("cepat", 0.28), "panas": ("panas", 0.36), "laut": ("laut", 0.46),
                     "dingin": ("dingin", 0.54), "udara": ("udara", 0.64), "naik": ("naik", 0.72),
                     "angin": ("angin", 0.80), "masuk": ("masuk", 0.90)},
    "angin_bumi60": {"bumi": ("Bumi", 0.03), "tiga": ("tiga", 0.12), "sel": ("sel", 0.18),
                     "udara": ("udara", 0.26), "berputar": ("berputar", 0.34), "khatulistiwa": ("khatulistiwa", 0.44),
                     "kutub": ("kutub", 0.52), "empat": ("empat", 0.60), "puluh": ("puluh", 0.66),
                     "ribu": ("ribu", 0.72), "kilometer": ("kilometer", 0.80), "berkeliling": ("berkeliling", 0.90)},
    "angin_hujan60": {"angin": ("Angin", 0.03), "juga": ("juga", 0.08), "membawa": ("membawa", 0.14),
                      "air": ("air", 0.22), "laut": ("laut", 0.30), "uap": ("uap", 0.38),
                      "naik": ("naik", 0.44), "awan": ("awan", 0.52), "hujan": ("hujan", 0.60),
                      "gunung": ("gunung", 0.68), "sungai": ("sungai", 0.76), "kembali": ("kembali", 0.86),
                      "laut": ("laut", 0.94)},
    "angin_muson60": {"indonesia": ("Indonesia", 0.03), "musim": ("musim", 0.12), "angin": ("angin", 0.20),
                      "muson": ("muson", 0.28), "januari": ("Januari", 0.38), "asia": ("Asia", 0.46),
                      "basah": ("basah", 0.54), "juli": ("Juli", 0.62), "australia": ("Australia", 0.70),
                      "kering": ("kering", 0.80), "dua": ("dua", 0.88), "arah": ("arah", 0.94)},
    "angin_berhenti60": {"angin": ("Angin", 0.03), "tidak": ("tidak", 0.09), "hilang": ("hilang", 0.15),
                         "melambat": ("melambat", 0.24), "gesekan": ("gesekan", 0.32),
                         "berubah": ("berubah", 0.40), "panas": ("panas", 0.48), "dua": ("dua", 0.56),
                         "angin": ("angin", 0.62), "bertemu": ("bertemu", 0.70), "berhenti": ("berhenti", 0.80),
                         "energi": ("energi", 0.90)},
    "angin_loop60": {"jadi": ("Jadi", 0.03), "besok": ("besok", 0.10), "angin": ("angin", 0.18),
                     "yang": ("yang", 0.26), "sama": ("sama", 0.34), "kembali": ("kembali", 0.44),
                     "bertiup": ("bertiup", 0.56), "dari": ("dari", 0.66), "arah": ("arah", 0.74),
                     "berbeda": ("berbeda", 0.84)},
}


SFX = {
    "angin_intro60": {"angin": ("angin", 0.60, 0), "meniup": ("whoosh", 0.55, 0), "jauh": ("riser", 0.45, 0),
                      "pesawat": ("pop", 0.55, 0)},
    "angin_tekanan60": {"udara": ("swish", 0.45, 0), "tekanan": ("pop", 0.55, 0),
                        "tinggi": ("ding", 0.45, 0), "rendah": ("thud", 0.50, 0),
                        "perbedaan": ("whoosh", 0.55, 0)},
    "angin_laut60": {"darat": ("pop", 0.50, 0), "panas": ("burn", 0.40, 0), "laut": ("swish", 0.45, 0),
                     "angin": ("angin", 0.55, 0), "masuk": ("whoosh", 0.55, 0)},
    "angin_bumi60": {"bumi": ("impact", 0.45, 0), "berputar": ("angin", 0.55, 0),
                     "khatulistiwa": ("swish", 0.40, 0), "kilometer": ("ding", 0.40, 0)},
    "angin_hujan60": {"air": ("gelembung", 0.45, 0), "uap": ("swish_up", 0.45, 0), "awan": ("pop", 0.50, 0),
                      "hujan": ("guntur", 0.45, 0), "kembali": ("whoosh", 0.50, 0)},
    "angin_muson60": {"muson": ("riser", 0.45, 0), "januari": ("guntur", 0.40, 0), "basah": ("gelembung", 0.40, 0),
                      "juli": ("pop", 0.45, 0), "kering": ("click", 0.45, 0), "arah": ("swish", 0.45, 0)},
    "angin_berhenti60": {"melambat": ("riser", 0.35, 0), "gesekan": ("swish", 0.45, 0),
                         "berhenti": ("thud", 0.55, 0), "energi": ("ding", 0.45, 0)},
    "angin_loop60": {"kembali": ("whoosh", 0.50, 0), "bertiup": ("angin", 0.55, 0), "berbeda": ("pop", 0.45, 0)},
}
BEATS53 = {k: [] for k in CUES}


def events_v12(sc):
    """Event SFX absolut satu adegan -> [(t, jenis, gain)]. Kata-driven, bukan tebakan."""
    vis = sc.get("visual", "")
    if vis not in CUES:
        return []
    c = M.cues(sc, sc["dur"], {k: v for k, v in CUES[vis].items()})
    out = [(sc["start"] + c[nama] + off, jenis, g) for nama, (jenis, g, off) in SFX.get(vis, {}).items()]
    if str(sc.get("trans") or "").lower() == "morph":
        out.append((sc["start"] - 0.08, "morph", 0.55))
    return out


def daftar():
    """Daftarkan visual + beat + event SFX ke registry mesin (dipanggil saat impor)."""
    M11.BEATS.update(BEATS53)
    D.VISUALS.update(VISUALS)
    M.EVENTS12.update({k: events_v12 for k in CUES})
    return sorted(VISUALS)


daftar()


if __name__ == "__main__":
    D.SS = 1.0
    im = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), CREAM)
    for nama, fn in VISUALS.items():
        sc = {"id": nama.split("60")[0].replace("angin_", ""), "visual": nama, "start": 10.0,
              "dur": 14.0, "trans": "morph", "accent": "#A85F3C", "captions": []}
        for tl in (0.0, 0.12, 2.0, 7.0, 13.98):
            fn(im, None, sc, tl, 14.0, 10.0 + tl, (168, 95, 60), 1.0, 0.0)
        assert events_v12(sc), nama
    print(f"selftest ep53: {len(VISUALS)} visual OK ({sum(len(v) for v in CUES.values())} cue, "
          f"{sum(len(v) for v in SFX.values())} SFX)")
