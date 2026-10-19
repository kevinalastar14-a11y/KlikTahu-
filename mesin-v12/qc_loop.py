#!/usr/bin/env python3
"""QC loop v12: bandingkan frame terakhir dengan frame pertama MP4 (korelasi >= 0,98 = loop mulus).

pakai: python3 qc_loop.py dist/NAMA.mp4 [--min 0.98]
Juga mencetak korelasi frame 0 vs frame-0,5 s dari akhir supaya terlihat arah 'mendarat'-nya loop.
"""
import argparse, subprocess, sys, json
import numpy as np
from PIL import Image
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()


def frame_at(path, t, size=(270, 480)):
    cmd = [FF, "-loglevel", "error", "-ss", f"{max(0.0, t):.3f}", "-i", path, "-frames:v", "1",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(size[1], size[0], 3).astype(float)


def durasi(path):
    out = subprocess.run([FF.replace("ffmpeg", "ffprobe") if False else FF, "-i", path], capture_output=True, text=True).stderr
    for ln in out.splitlines():
        if "Duration:" in ln:
            h, m, s = ln.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def korelasi(a, b):
    a = a - a.mean(); b = b - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4")
    ap.add_argument("--min", type=float, default=0.98)
    a = ap.parse_args()
    d = durasi(a.mp4)
    f0 = frame_at(a.mp4, 0.0)
    hasil = {}
    for dt in (0.03, 0.5, 1.0, 2.0):
        hasil[dt] = korelasi(f0, frame_at(a.mp4, d - dt))
    print(f"durasi {d:.2f} s")
    for dt, k in hasil.items():
        print(f"  frame0 vs akhir-{dt:.2f}s : korelasi {k:.4f}")
    ok = hasil[0.03] >= a.min
    print("LOOP OK ✔" if ok else f"LOOP BELUM MULUS ✘ (butuh >= {a.min})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
