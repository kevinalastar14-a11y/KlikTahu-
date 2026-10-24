#!/usr/bin/env python3
"""pustaka_v18.py — bikin aset pustaka (thumbnail + lembar pratinjau) dari mesin v18.

Semua aset diturunkan dari frame mesin yang SAMA dengan video, jadi apa yang
dilihat calon penonton di thumbnail identik dengan isi video (tidak ada
"thumbnail menjanjikan, video tidak").

Keluaran (folder `pustaka/Ep55_Megalodon/`):
  KlikTahu_Ep55_Megalodon_thumb_utama.png   1080x1920, judul besar, hiu dominan
  KlikTahu_Ep55_Megalodon_thumb_alt.png     1080x1920, versi angka (16,4 m)
  KlikTahu_Ep55_Megalodon_lembar_pratinjau.jpg  8 frame berlabel (QC visual)

Pakai: python3 pustaka_v18.py [--episode ep55] [--slug Ep55_Megalodon]
"""
from __future__ import annotations

import argparse
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import mesin_v18_dunia as W
import mesin_v18_inti as M


def _judul_thumb(k, baris, y, warna, ukuran=104, sorot=(), aksen=M.mix(W.AMBER, W.TERRA, 0.2),
                 margin=56):
    """Judul thumbnail: tebal, rapat, dengan stabilo untuk kata kunci.

    `margin` (px) memastikan teks tidak menyentuh tepi kanvas — judul yang
    terpotong di thumbnail langsung menurunkan CTR.
    """
    lebar_maks = 1080 - margin * 2
    while ukuran > 40 and max(M.tw(b, M.F_BOLD, ukuran) for b in baris) > lebar_maks:
        ukuran -= 2
    lh = ukuran * 1.10
    idx = 0
    for r, teks in enumerate(baris):
        kata = teks.split()
        spasi = M.tw(" ", M.F_BOLD, ukuran)
        total = sum(M.tw(w, M.F_BOLD, ukuran) for w in kata) + spasi * (len(kata) - 1)
        x = (1080 - total) / 2
        for w in kata:
            sp_w = M.tw(w, M.F_BOLD, ukuran)
            if w.strip(".,!?").lower() in sorot:
                y0 = int(y + r * lh + lh * 0.62)
                hh = int(ukuran * 0.34)
                reg = k.a[y0:y0 + hh, int(x - 6):int(x + sp_w + 6)].astype(np.float32)
                reg += (np.array(aksen, np.float32) - reg) * 0.85
                k.a[y0:y0 + hh, int(x - 6):int(x + sp_w + 6)] = np.clip(reg, 0, 255).astype(np.uint8)
            spr = M.spr_text(w, warna, M.F_BOLD, ukuran, tracking=-2.0,
                             shadow=M.mix(W.PUTIH, W.KREM, 0.3), shadow_blur=0,
                             shadow_off=(0, 0), shadow_a=0)
            M.blit(k.a, spr, x, y + r * lh, 1.0)
            x += sp_w + spasi
        idx += 1


def thumb_utama(mod):
    """Thumbnail utama: hiu besar dari bawah, judul di atas, gigi di bawah."""
    k = M.Kanvas(1080, 1920, W.KERTAS)
    W.langit(k, 0.0, awan=True, matahari_x=None, senja=0.34, tinggi=250)
    W.air(k, 250, 1920, dalam=1.0)
    W.berkas_cahaya(k, 0.0, n=4, y0=250, y1=1300, kuat=0.10)
    W.dasar_laut(k, 1720)
    W.kaustik_dasar(k, W.kaustik_spr(512, 7, 0.45), 0.0, 1770, 1920, 0.22)
    # hiu besar, dilihat sedikit dari bawah
    M.blit(k.a, M.swim(mod._HIU_BESAR, amp=6, lam=320, phase=1.2), 60, 420, 1.0)
    # deret gigi
    for i, sp in enumerate(mod._DERET):
        M.blit(k.a, sp, mod._DERET_X[i] + 40, 1590 - sp.shape[0] * 0.5)
    # judul
    _judul_thumb(k, ["GIGINYA SEBESAR", "TELAPAK TANGAN"], 170, W.INK, ukuran=88,
                 sorot=("telapak",))
    out = cv2.LUT(k.a, mod._LUT)
    out = cv2.multiply(out, mod._VIGNETTE, scale=1.0 / 255.0)
    return out


def thumb_alt(mod):
    """Thumbnail alternatif: angka besar 24,3 m + siluet penyelam pembanding."""
    k = M.Kanvas(1080, 1920, W.KERTAS)
    W.langit(k, 0.0, awan=False, matahari_x=860, matahari_y=250, senja=0.22, tinggi=300)
    W.air(k, 300, 1920, dalam=1.1)
    W.berkas_cahaya(k, 0.0, n=3, y0=300, y1=1500, kuat=0.09)
    W.dasar_laut(k, 1760)
    # siluet hiu + penyelam pembanding
    M.blit(k.a, M.tint(M.swim(mod._HIU_BESAR, amp=5, lam=330, phase=0.4), W.AIR_2, 0.15),
           30, 640, 0.86)
    M.blit(k.a, mod._SELAM, 700, 1180, 1.0)
    # garis ukur 1,8 m vs 24,3 m
    cv2.line(k.a, (100, 1560), (980, 1560), W.INK, 6, cv2.LINE_AA)
    _judul_thumb(k, ["SEPANJANG", "24 METER"], 128, W.INK, ukuran=88, sorot=())
    _judul_thumb(k, ["HIUNYA HILANG"], 1668, W.INK, ukuran=84, sorot=("hilang",))
    out = cv2.LUT(k.a, mod._LUT)
    out = cv2.multiply(out, mod._VIGNETTE, scale=1.0 / 255.0)
    return out


def lembar(mod, path):
    """Lembar pratinjau 8 frame (2 kolom x 4 baris) dengan label waktu."""
    keping = []
    for i, sc in enumerate(mod.SCENES):
        t = mod.MULAI[i] + sc["dur"] * 0.5
        fr = mod.frame(t)
        im = Image.fromarray(fr).resize((540, 960), Image.LANCZOS).convert("RGB")
        d = ImageDraw.Draw(im)
        f = M.F(M.F_SEMI, 26)
        lab = f"{sc['id']} · {t:05.1f}s"
        d.rounded_rectangle([14, 14, 30 + M.tw(lab, M.F_SEMI, 26), 58], radius=10,
                            fill=(24, 24, 31))
        d.text((22, 22), lab, font=f, fill=(250, 245, 233))
        keping.append(im)
    sheet = Image.new("RGB", (540 * 2, 960 * 4), (255, 255, 255))
    for i, im in enumerate(keping):
        sheet.paste(im, ((i % 2) * 540, (i // 2) * 960))
    sheet.save(path, quality=90, subsampling=0, optimize=True)
    return sheet.size


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default="ep55")
    ap.add_argument("--slug", default="Ep55_Megalodon")
    a = ap.parse_args(argv)
    import importlib
    mod = importlib.import_module(f"mesin_v18_{a.episode}")
    mod.siapkan()
    out = os.path.join(BASE, "pustaka", a.slug)
    os.makedirs(out, exist_ok=True)
    Image.fromarray(thumb_utama(mod)).save(
        os.path.join(out, "KlikTahu_Ep55_Megalodon_thumb_utama.png"), optimize=True)
    Image.fromarray(thumb_alt(mod)).save(
        os.path.join(out, "KlikTahu_Ep55_Megalodon_thumb_alt.png"), optimize=True)
    ukuran = lembar(mod, os.path.join(out, "KlikTahu_Ep55_Megalodon_lembar_pratinjau.jpg"))
    for f in sorted(os.listdir(out)):
        p = os.path.join(out, f)
        print(f"  {f:52s} {os.path.getsize(p)/1024:8.0f} KB")
    print("lembar pratinjau:", ukuran)


if __name__ == "__main__":
    main()
