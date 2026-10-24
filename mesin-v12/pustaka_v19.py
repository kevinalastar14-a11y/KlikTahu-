#!/usr/bin/env python3
"""pustaka_v19.py — aset pustaka (thumbnail + lembar pratinjau) untuk mesin v19.

Semua aset diturunkan dari frame mesin yang SAMA dengan video (bukan komposisi
terpisah), jadi thumbnail tidak menjanjikan hal yang tidak ada di dalam video.
Gaya mengikuti bahasa visual v19: latar gelap bergradasi, objek ber-rim light,
angka besar, pill berwarna, grain + vignette.

Keluaran (folder `pustaka/<Slug>/`):
  ..._thumb_utama.png      1080x1920 · hiu + "24 METER" (angka jadi pemikat)
  ..._thumb_alt.png        1080x1920 · gigi + "CUMA GIGINYA" (sudut rasa ingin tahu)
  ..._lembar_pratinjau.jpg 8 frame berlabel untuk QC visual cepat

Pakai: python3 pustaka_v19.py [--episode ep55] [--slug Ep55_Megalodon]
"""
from __future__ import annotations

import argparse
import os
import sys

import cv2
import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import mesin_v18_inti as M
import mesin_v19_ep55 as E
import mesin_v19_gelap as G

W, H = E.W_, E.H_


def _dasar(i, t=None):
    """Latar babak ke-i (plus aktor pada waktu t bila diberikan), sudah digrade."""
    if t is None:
        return E.latar_scene(i).copy()
    return E.frame(t)


def _teks_besar(k, teks, y, warna=G.TEKS, size=118, pendar=None, alpha=1.0,
                rata="tengah", x=0):
    """Judul tebal + pendar; menyusut sendiri kalau melebihi lebar aman.

    Mengembalikan lebar teks (tanpa padding pendar).
    """
    while size > 40 and M.tw(teks, M.F_BOLD, size) > W - 120:
        size -= 2
    gs, ts, pad = G.teks_pendar(teks, warna, size, M.F_BOLD,
                                pendar_warna=pendar or warna, pendar_kuat=0.32,
                                pendar_r=16, tracking=-2.5, blur=12)
    w_teks = ts.shape[1] - pad * 2
    x_kiri = (W - w_teks) / 2 if rata == "tengah" else x
    M.blit_add(k.a, gs, x_kiri - pad, y - pad, alpha)
    M.blit(k.a, ts, x_kiri - pad, y - pad, alpha)
    return w_teks


def _sela(k, y, warna=G.GOLD, alpha=1.0, w=120, x=None):
    """Garis aksen pendek di bawah judul."""
    x0 = (W - w) / 2 if x is None else x
    cv2.line(k.a, (int(x0), int(y)), (int(x0 + w), int(y)), (*warna[:3], 255), 5, cv2.LINE_AA)


def _kabut_bawah(k, y):
    """Gelapkan bagian bawah supaya teks selalu terbaca di atas latar apa pun."""
    G.kabut_bawah(k, y, H, warna=(5, 7, 16), kuat=0.95)


def thumb_utama():
    """Hiu besar + 'BUKAN HIU PUTIH RAKSASA' + 24 METER; latar babak 1."""
    k = M.Kanvas(W, H, G.BG_1)
    k.a = E.latar_scene(0).copy()

    # hiu ditempel sebagai sprite (BUKAN potongan persegi frame) supaya menyatu
    hiu = E._HIU_TENGAH_KIRI
    M.blit(k.a, hiu, 46, 402, 1.0)
    _kabut_bawah(k, 940)

    mr = G.merek("KlikTahu", size=32)
    M.blit(k.a, mr, 54, 54, 0.95)
    bd = G.badge_babak("LAUT PURBA", warna=G.CYAN, size=24, nomor="EP 55")
    M.blit(k.a, bd, W - 54 - bd.shape[1], 54, 0.95)

    lb = G.label_kecil("MEGALODON · LAUT PURBA", G.GOLD, 28, tracking=3.0)
    M.blit(k.a, lb, (W - lb.shape[1]) / 2, 972, 0.95)
    _teks_besar(k, "BUKAN HIU PUTIH", 1030, G.TEKS, 84, pendar=G.CYAN)
    _teks_besar(k, "RAKSASA", 1128, G.GOLD, 132, pendar=G.GOLD)
    _sela(k, 1288, G.GOLD, w=140)

    G.stat_besar(k, "24,3", "meter", "BATAS ATAS · SHIMADA 2025", 74, 1370,
                 warna=G.GOLD, size=190, alpha=1.0)
    p = E._pil_spr("YANG TERSISA CUMA GIGINYA", G.CORAL)
    M.blit(k.a, p, (W - p.shape[1]) / 2, 1758, 0.96)
    return _akhir(k)


def thumb_alt():
    """Gigi raksasa + 'CUMA GIGINYA'; latar babak 5 (sorot emas)."""
    k = M.Kanvas(W, H, G.BG_1)
    k.a = E.latar_scene(4).copy()

    mr = G.merek("KlikTahu", size=32)
    M.blit(k.a, mr, 54, 54, 0.95)
    bd = G.badge_babak("GIGI", warna=G.GOLD, size=24, nomor="EP 55")
    M.blit(k.a, bd, W - 54 - bd.shape[1], 54, 0.95)

    g = E._GIGI_BESAR
    skala = 0.92
    gg = cv2.resize(g, (int(g.shape[1] * skala), int(g.shape[0] * skala)),
                    interpolation=cv2.INTER_AREA)
    M.blit(k.a, gg, 44, 618, 1.0)
    G.pendar(k, 44 + gg.shape[1] * 0.5, 618 + gg.shape[0] * 0.55, 330,
             (255, 220, 150), 0.16, 2.6)

    _kabut_bawah(k, 1180)
    _teks_besar(k, "CUMA", 690, G.TEKS, 96, pendar=G.TEKS, rata="kiri", x=320)
    _teks_besar(k, "GIGINYA", 790, G.GOLD, 140, pendar=G.GOLD, rata="kiri", x=318)
    _sela(k, 968, G.GOLD, w=110, x=322)
    lb = G.label_kecil("18 CM · BERGERIGI SEPERTI GERGAJI", G.TEKS_2, 26, tracking=1.4)
    M.blit(k.a, lb, 322, 1000, 0.95)

    G.stat_besar(k, "3,6", "juta tahun", "SEJAK IA HILANG", 78, 1270,
                 warna=G.CYAN, size=168, alpha=1.0)
    p = E._pil_spr("HIUNYA TIDAK PERNAH MUNCUL LAGI", G.CORAL)
    M.blit(k.a, p, (W - p.shape[1]) / 2, 1690, 0.96)
    return _akhir(k)


def _akhir(k):
    """Grade akhir: LUT + vignette + grain, sama seperti video."""
    out = cv2.LUT(k.a, E._LUT)
    out = cv2.multiply(out, E._VIGNETTE, scale=1.0 / 255.0)
    gi = np.random.default_rng(7).integers(0, len(E._GRAIN_POS))
    return cv2.subtract(cv2.add(out, E._GRAIN_POS[gi]), E._GRAIN_NEG[gi])


def lembar(keluar):
    """Lembar pratinjau 4x2: satu frame wakil dari tiap babak."""
    d = E.daftar()
    ims = []
    for i, sc in enumerate(d["scenes"]):
        t = sc["mulai"] + sc["dur"] * 0.58
        im = Image.fromarray(E.frame(t)).resize((432, 768))
        ims.append(im)
    sheet = Image.new("RGB", (432 * 4, 768 * 2), (0, 0, 0))
    for i, im in enumerate(ims[:8]):
        sheet.paste(im, ((i % 4) * 432, (i // 4) * 768))
    sheet.save(keluar, quality=90)
    return keluar


def main(argv=None):
    ap = argparse.ArgumentParser(description="Aset pustaka KlikTahu v19")
    ap.add_argument("--slug", default="Ep55_Megalodon")
    a = ap.parse_args(argv)
    E.siapkan()
    out = os.path.join(BASE, "pustaka", a.slug)
    os.makedirs(out, exist_ok=True)

    tu = os.path.join(out, "KlikTahu_Ep55_Megalodon_thumb_utama.png")
    ta = os.path.join(out, "KlikTahu_Ep55_Megalodon_thumb_alt.png")
    lp = os.path.join(out, "KlikTahu_Ep55_Megalodon_lembar_pratinjau.jpg")
    Image.fromarray(thumb_utama()).save(tu)
    Image.fromarray(thumb_alt()).save(ta)
    lembar(lp)
    for p in (tu, ta, lp):
        print(f"-> {p}  ({os.path.getsize(p)/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
