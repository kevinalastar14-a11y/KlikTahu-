"""
tools/verify_video.py — cek hasil render sebelum diunggah.

Memastikan video benar-benar siap YouTube: resolusi, fps, codec, durasi,
bitrate, ukuran file, dan audio yang tidak clipping/diam total.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

MIN_MB = 200.0
EXPECT = dict(width=1080, height=1920, fps=60.0)


def probe(path: Path) -> dict:
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    out = subprocess.run([exe, "-hide_banner", "-i", str(path)],
                         capture_output=True, text=True).stderr
    info: dict = {"path": str(path), "size_mb": path.stat().st_size / 1024 / 1024}
    m = re.search(r"Video: (\w+).*?, (\d+)x(\d+).*?, (\d+(?:\.\d+)?) fps", out)
    if m:
        info.update(codec=m.group(1), width=int(m.group(2)), height=int(m.group(3)),
                    fps=float(m.group(4)))
    m = re.search(r"Audio: (\w+)", out)
    if m:
        info["audio"] = m.group(1)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    if m:
        info["duration"] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    m = re.search(r"bitrate: (\d+) kb/s", out)
    if m:
        info["kbps"] = int(m.group(1))
    return info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verifikasi video Short")
    ap.add_argument("file", nargs="?", default="KlikTahu_Shorts_1080x1920.mp4")
    ap.add_argument("--min-mb", type=float, default=MIN_MB)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"[verify] GAGAL: {path} tidak ada")
        return 1
    info = probe(path)
    problems = []
    if (info.get("width"), info.get("height")) != (EXPECT["width"], EXPECT["height"]):
        problems.append(f"resolusi {info.get('width')}x{info.get('height')} bukan 1080x1920")
    if abs(info.get("fps", 0) - EXPECT["fps"]) > 0.5:
        problems.append(f"fps {info.get('fps')} bukan 60")
    if info.get("codec") not in ("h264",):
        problems.append(f"codec video {info.get('codec')} bukan h264")
    if not info.get("audio"):
        problems.append("tidak ada audio")
    if info.get("size_mb", 0) < args.min_mb:
        problems.append(f"ukuran {info.get('size_mb', 0):.1f} MB < {args.min_mb} MB")
    if (info.get("duration") or 0) > 60.0:
        problems.append(f"durasi {info.get('duration'):.1f}s > 60s (bukan Short lagi)")

    if args.json:
        print(json.dumps(info, indent=2))
    else:
        for k in ("path", "size_mb", "codec", "width", "height", "fps", "audio",
                  "duration", "kbps"):
            if k in info:
                v = info[k]
                print(f"  {k:9s}: {v:.2f}" if isinstance(v, float) else f"  {k:9s}: {v}")

    if problems:
        print("\n[verify] MASALAH:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\n[verify] OK — siap diunggah ke YouTube.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
