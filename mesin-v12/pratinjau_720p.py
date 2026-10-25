#!/usr/bin/env python3
"""Pratinjau 720x1280 dari video Shorts 1080x1920.

Kenapa ada berkas ini: versi 720p dulu dibuat dengan perintah ffmpeg yang
diketik tangan, sehingga angkanya (crf 26, lanczos, `-c:a copy`) hanya hidup di
catatan sesi dan mudah melenceng antar-episode. Semua parameter sekarang di
satu tempat, dan tiap hasil langsung diperiksa (resolusi, durasi, audio utuh,
ukuran) sebelum dilaporkan.

Pakai:
    python3 pratinjau_720p.py keluaran/KlikTahu_Ep56_HypnicJerk_v20.mp4
    python3 pratinjau_720p.py keluaran/*.mp4 --crf 27

Keluaran ditulis di sebelah berkas sumber dengan akhiran `_720p.mp4`.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

try:
    import imageio_ffmpeg

    FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:  # pragma: no cover - ffmpeg dari PATH
    FF = "ffmpeg"


def ffprobe_json(path: str) -> dict:
    """Info stream lewat `ffmpeg -i` (di sandbox tidak ada ffprobe)."""
    out = subprocess.run(
        [FF, "-hide_banner", "-i", path], capture_output=True, text=True
    ).stderr
    info = {"durasi": None, "lebar": None, "tinggi": None, "audio": False}
    for baris in out.splitlines():
        b = baris.strip()
        if b.startswith("Duration:"):
            jam, menit, sisa = b.split()[1].rstrip(",").split(":")
            info["durasi"] = int(jam) * 3600 + int(menit) * 60 + float(sisa)
        elif "Video:" in b and "x" in b:
            for bagian in b.split(","):
                bagian = bagian.strip()
                if "x" in bagian and bagian.replace("x", "").isdigit():
                    lebar, tinggi = bagian.split("x")
                    info["lebar"], info["tinggi"] = int(lebar), int(tinggi)
                    break
        elif "Audio:" in b:
            info["audio"] = True
    return info


def jadikan(path: str, crf: float = 26, preset: str = "slow") -> str:
    keluar = os.path.splitext(path)[0] + "_720p.mp4"
    sementara = keluar + ".tmp.mp4"
    perintah = [
        FF, "-hide_banner", "-loglevel", "error", "-y",
        "-i", path,
        # 720 lebar, tinggi mengikuti rasio asli (1080x1920 -> 720x1280).
        "-vf", "scale=720:-2:flags=lanczos",
        "-c:v", "libx264", "-crf", str(crf), "-preset", preset,
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-c:a", "copy", "-movflags", "+faststart",
        sementara,
    ]
    subprocess.run(perintah, check=True)
    os.replace(sementara, keluar)
    return keluar


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("berkas", nargs="+", help="MP4 1080x1920 sumber")
    ap.add_argument("--crf", type=float, default=26)
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--json")
    a = ap.parse_args(argv)

    laporan = []
    for path in a.berkas:
        asal = ffprobe_json(path)
        keluar = jadikan(path, a.crf, a.preset)
        hasil = ffprobe_json(keluar)
        butir = {
            "sumber": path,
            "keluaran": keluar,
            "mb": round(os.path.getsize(keluar) / 1e6, 2),
            "resolusi": f"{hasil['lebar']}x{hasil['tinggi']}",
            "durasi": hasil["durasi"],
            "audio": hasil["audio"],
        }
        butir["lulus"] = (
            hasil["lebar"] == 720
            and hasil["audio"]
            and asal["durasi"] is not None
            and hasil["durasi"] is not None
            and abs(hasil["durasi"] - asal["durasi"]) < 0.1
        )
        laporan.append(butir)
        tanda = "OK " if butir["lulus"] else "GAGAL"
        print(
            f"[{tanda}] {os.path.basename(keluar)} · {butir['resolusi']} · "
            f"{butir['durasi']:.2f} s · {butir['mb']:.2f} MB"
        )

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(laporan, f, ensure_ascii=False, indent=2)
        print(f"-> {a.json}")
    return 0 if all(x["lulus"] for x in laporan) else 1


if __name__ == "__main__":
    sys.exit(main())
