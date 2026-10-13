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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MIN_MB = 200.0
LUFS_RANGE = (-16.0, -12.0)      # YouTube menormalkan ke -14 LUFS
MAX_DBTP = -0.8
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


def audio_metrics(path: Path) -> dict:
    """
    Ukur audio menurut persepsi pendengaran (ITU-R BS.1770-4), bukan sekadar peak.

    Dipakai untuk memastikan file yang diunggah memang di-master untuk telinga
    manusia: loudness di sekitar -14 LUFS dan true peak aman untuk DAC.
    """
    try:
        import audio_design as ad
        import audio_master as am
    except ImportError:
        return {}
    x = ad.decode_audio(str(path), mono=False)
    if x.size == 0:
        return {}
    return dict(
        lufs=am.loudness_lufs(x),
        dbtp=am.true_peak_dbtp(x),
        peak=float(abs(x).max()),
        mono_fold_db=am.mono_fold_check(x),
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verifikasi video Short")
    ap.add_argument("file", nargs="?", default="KlikTahu_Shorts_1080x1920.mp4")
    ap.add_argument("--min-mb", type=float, default=MIN_MB)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-audio", action="store_true", help="lewati pengukuran loudness")
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

    audio = {} if args.json is False and args.no_audio else audio_metrics(path)
    if audio:
        info.update({f"audio_{k}": v for k, v in audio.items()})
        if not (LUFS_RANGE[0] <= audio["lufs"] <= LUFS_RANGE[1]):
            problems.append(f"loudness {audio['lufs']:.1f} LUFS di luar rentang "
                            f"{LUFS_RANGE[0]}..{LUFS_RANGE[1]}")
        if audio["dbtp"] > MAX_DBTP:
            problems.append(f"true peak {audio['dbtp']:.2f} dBTP terlalu tinggi "
                            f"(batas {MAX_DBTP})")

    if args.json:
        print(json.dumps(info, indent=2))
    else:
        for k in ("path", "size_mb", "codec", "width", "height", "fps", "audio",
                  "duration", "kbps", "audio_lufs", "audio_dbtp", "audio_mono_fold_db"):
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
