#!/usr/bin/env python3
"""Thumbnail Long01 (1280x720 JPG): lubang hitam raksasa + astronot tertarik + teks besar.

  python3 long/v01_lubang_hitam/thumbnail.py [--out build/thumbnail.jpg]
"""
import argparse, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from PIL import Image, ImageEnhance  # noqa: E402
import mesin_long as L  # noqa: E402
from mesin_long import D  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.environ.get("KT_BUILD", "build"), "thumbnail.jpg"))
    a = ap.parse_args()
    L.set_ss(1.25)
    img = L.latar(3.0, 1.0, 1.0)
    cx, cy, r = 1330, 560, 285
    L.glow(img, cx, cy, r * 3.6, (255, 150, 60), 0.35)
    L.lubang_hitam(img, cx, cy, r, 1.3, 1.0, tilt=0.2)
    # astronot di depan, sedang ditarik memanjang ke arah lubang
    L.astronot(img, 930, 700, 230, 1.0, rot=-38, regang=1.6, merah=0.15)
    for k in range(5):
        y = 610 + k * 38
        L.panah(img, (760, y - 60), (860, y - 20), (255, 255, 255), 4, 0.35, 1.0, 12)
    # teks: 3 baris besar, kontras tinggi (terbaca di layar HP)
    L.teks(img, 70, 190, "KALAU KAMU", 104, L.WHITE, 1.0, anchor="l", stroke=6, scol=(10, 10, 20))
    L.teks(img, 70, 330, "MASUK", 170, L.EMAS, 1.0, anchor="l", stroke=8, scol=(10, 10, 20))
    L.teks(img, 70, 480, "SINI?", 170, L.EMAS, 1.0, anchor="l", stroke=8, scol=(10, 10, 20))
    # panah melengkung ke lubang hitam
    L.panah(img, (560, 470), (cx - r - 40, cy - 40), L.MERAH, 18, 1.0, 1.0, 54)
    L.stiker(img, 420, 900, "WAKTU BERHENTI?!", 1.0, L.MERAH, 52, -4, 0.0, 1.0)
    out = L.kamera(img, 1.0)
    out = L.akhiri(out, 0, sharpen=60)
    out = ImageEnhance.Color(out).enhance(1.15)
    out = out.resize((1280, 720), Image.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    out.save(a.out, quality=92)
    print("thumbnail ->", a.out, os.path.getsize(a.out) // 1024, "KB")


if __name__ == "__main__":
    main()
