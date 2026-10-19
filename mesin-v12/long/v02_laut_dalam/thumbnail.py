#!/usr/bin/env python3
"""Thumbnail Long02 (1280x720 JPG): laut dalam gelap + ikan pemancing bercahaya + teks "11 KM".

  python3 long/v02_laut_dalam/thumbnail.py [--out build/thumbnail.jpg]
"""
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from PIL import Image, ImageEnhance  # noqa: E402
import mesin_long as L  # noqa: E402
import visual as V  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.environ.get("KT_BUILD", "build"), "thumbnail.jpg"))
    a = ap.parse_args()
    L.set_ss(1.25)
    img = V._gradasi(700).copy()
    w, h = img.size
    # dari biru (atas) ke hitam pekat (bawah): kesan "turun ke kegelapan"
    atas = V._gradasi(60).crop((0, 0, w, int(h * 0.35)))
    m = Image.linear_gradient("L").resize((w, int(h * 0.35))).point(lambda v: 255 - v)
    img.paste(atas, (0, 0), m)
    far, near = V._salju_spr()
    for lay in (far, near):
        c = lay.crop((0, 0, w, h))
        img.paste(c, (0, 0), c)
    # jalur turun di kiri
    L.D.line_on(img, (110, 40), (110, 1040), (220, 235, 255), 5, 0.8, dash=22)
    V.penyelam(img, 110, 120, 170, 0.0, 1.0, rot=-80)
    L.teks(img, 140, 1000, "10.935 m", 44, L.EMAS, 1.0, anchor="l", stroke=4, scol=(5, 8, 20))
    # ikan pemancing raksasa
    lx, ly = V.pemancing(img, 1390, 640, 900, 1.2, 1.0, mulut=0.75, lure=1.0)
    L.glow(img, lx, ly, 260, (120, 240, 255), 0.35)
    for k, (x, y, s) in enumerate([(1150, 250, 1.0), (1720, 930, 0.8)]):
        V.mata_gelap(img, x, y, 1.6 * s, 0.3, 0.7, col=(150, 255, 200))
    # teks besar
    L.teks(img, 170, 250, "TURUN", 120, L.WHITE, 1.0, anchor="l", stroke=7, scol=(5, 8, 20))
    L.teks(img, 170, 440, "11 KM", 240, L.EMAS, 1.0, anchor="l", stroke=10, scol=(5, 8, 20))
    L.teks(img, 170, 620, "KE DASAR LAUT", 96, L.WHITE, 1.0, anchor="l", stroke=6, scol=(5, 8, 20))
    L.stiker(img, 520, 820, "APA YANG HIDUP DI SANA?!", 1.0, L.MERAH, 50, -4, 0.0, 1.0)
    out = L.kamera(img, 1.0)
    out = L.akhiri(out, 0, sharpen=60)
    out = ImageEnhance.Color(out).enhance(1.15)
    out = ImageEnhance.Contrast(out).enhance(1.06)
    out = out.resize((1280, 720), Image.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    out.save(a.out, quality=92)
    print("thumbnail ->", a.out, os.path.getsize(a.out) // 1024, "KB")


if __name__ == "__main__":
    main()
