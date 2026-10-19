#!/usr/bin/env python3
"""Pasca-produksi Ep51 v2: QC loop, master .m4a, thumbnail, lembar pratinjau.

pakai:  python3 tools/pasca_ep51b.py
Hasil masuk ke dist/ (MP4 + _audio.m4a + _thumb.jpg + _lembar_pratinjau.jpg).
"""
import os
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "KlikTahu_Ep51_Ular_Rumah_v2"
MP4 = os.path.join(ROOT, "dist", f"{NAME}.mp4")
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def frame(t, size=(W, H)):
    cmd = [FF, "-loglevel", "error", "-ss", f"{t:.3f}", "-i", MP4, "-frames:v", "1",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return Image.frombytes("RGB", size, raw)


def main():
    if not os.path.exists(MP4):
        sys.exit(f"tidak ada {MP4}")

    print("=== QC loop ===")
    subprocess.run([sys.executable, os.path.join(ROOT, "qc_loop.py"), MP4], check=False)

    print("=== master audio .m4a ===")
    src = os.path.join(ROOT, "build", "audio_master.wav")
    out_m4a = os.path.join(ROOT, "dist", f"{NAME}_audio.m4a")
    run([FF, "-y", "-loglevel", "error", "-i", src, "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-movflags", "+faststart", out_m4a])
    print("  ->", out_m4a, os.path.getsize(out_m4a), "B")

    print("=== thumbnail ===")
    th = frame(2.2)
    th.save(os.path.join(ROOT, "dist", f"{NAME}_thumb.jpg"), quality=92)
    alt = frame(15.34)          # 22 anak sanca (angka 22 penuh)
    alt.save(os.path.join(ROOT, "dist", f"{NAME}_thumb_alt.jpg"), quality=92)

    print("=== lembar pratinjau ===")
    times = [2.2, 7.7, 20.5, 31.5, 37.4, 47.0, 60.5, 69.0, 82.0, 90.0, 96.5, 100.6]
    tw, thh = 270, 480
    cols, rows = 4, 3
    pad, top = 12, 52
    sheet = Image.new("RGB", (cols * tw + pad * (cols + 1), top + rows * (thh + 26) + pad * (rows + 1)),
                      (242, 236, 223))
    d = ImageDraw.Draw(sheet)
    d.text((pad + 4, 18), "KlikTahu · Ep51 v2 · lembar pratinjau (1080x1920 · 60 fps · 101,5 s)",
           fill=(32, 40, 52))
    for i, t in enumerate(times):
        c, r = i % cols, i // cols
        x = pad + c * (tw + pad)
        y = top + pad + r * (thh + 26 + pad)
        sheet.paste(frame(t, (tw, thh)), (x, y))
        d.text((x + 4, y + thh + 6), f"{int(t // 60)}:{t % 60:04.1f}", fill=(90, 96, 104))
    out = os.path.join(ROOT, "dist", f"{NAME}_lembar_pratinjau.jpg")
    sheet.save(out, quality=90)
    print("  ->", out, os.path.getsize(out), "B")


if __name__ == "__main__":
    main()
