#!/usr/bin/env python3
"""Pratinjau cepat satu visual Ep51b -> build/pratinjau/<visual>_tNN.png

pakai: KT_SS=0.7 python3 pratinjau_ep51b.py ambang_hujan60 0.5 3.0 7.0
"""
import json
import os
import sys

from PIL import Image, ImageDraw

import diagrams as D
import mesin_v13_ep51b as E

BASE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(BASE, "episodes", "ep51_ular_rumah", "content.json")
OUT = os.path.join(BASE, "build", "pratinjau")


def main():
    nama = sys.argv[1]
    ts = [float(x) for x in sys.argv[2:] if not x.startswith("dur=")] or [0.5, 3.0, 8.0]
    dur = next((float(x[4:]) for x in sys.argv[2:] if x.startswith("dur=")), 13.5)
    sc_all = json.load(open(CONTENT))["scenes"]
    sc = next(s for s in sc_all if s["visual"] == nama)
    os.makedirs(OUT, exist_ok=True)
    img = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), D.CREAM)
    d = ImageDraw.Draw(img)
    for t in ts:
        fn = E.VISUALS60[nama]
        fn(img, d, sc, t, dur, 20.0 + t, D.hexc(sc["accent"]), 1.0, 0.0)
        p = os.path.join(OUT, f"{nama}_t{t:05.2f}.png")
        img.save(p)
        print(p)


if __name__ == "__main__":
    main()
