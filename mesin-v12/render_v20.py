#!/usr/bin/env python3
"""render_v20.py — renderer KlikTahu v20 (pipe langsung ke x264, N proses).

Kenapa renderer terpisah
------------------------
Menulis 4.500 file PNG/JPEG lalu membacanya lagi untuk encode membuang
±2,5 menit I/O. v20 menulis frame mentah (`rawvideo rgb24`) langsung ke stdin
ffmpeg per proses, lalu menggabungkan potongan dengan `concat` (tanpa encode
ulang) dan menyisipkan audio dengan `-c:a copy`.

Skema
-----
    proses 0: frame [0, k)        -> ffmpeg -> build_v20/parts/part_00.mp4 ┐
    proses 1: frame [k, 2k)       -> ffmpeg -> build_v20/parts/part_01.mp4 ├ concat
    proses 2: ...                 -> ...                                   ┘  + audio

Animasi dihitung dari waktu absolut (`t = i / fps`), jadi hasil render
terpotong-potong identik dengan render satu proses penuh (deterministik).

Pemakaian
---------
    python3 render_v20.py --episode ep56 --keluar dist/KlikTahu_Ep56.mp4 \
            --audio dist/KlikTahu_Ep56_audio.m4a --jobs 2 --preset slow --crf 16
    python3 render_v20.py --episode ep56 --pratinjau 4
    python3 render_v20.py --episode ep56 --potong 5 --tanpa-audio
    python3 render_v20.py --episode ep56 --ukur
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
W, H = 1080, 1920
BUILD = os.environ.get("KT_BUILD") or os.path.join(BASE, "build_v20")


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def muat_episode(nama):
    """`ep56` / `mesin_v20_ep56` / path modul -> modul python."""
    m = nama
    if m.endswith(".py"):
        m = os.path.basename(m)[:-3]
    if not m.startswith("mesin_v20_"):
        m = f"mesin_v20_{m}"
    return importlib.import_module(m)


# ============================================================ worker

def render_potongan(mod, lo, hi, fps, keluar, crf=16, preset="slow",
                    tune="animation", bitrate=None, jobs_tag="", verbose=True):
    """Render frame [lo, hi) -> mp4 tanpa audio."""
    mod.siapkan()
    if hasattr(mod, "_siap_debu"):
        mod._siap_debu()
    ff = ffmpeg()
    cmd = [ff, "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", preset, "-tune", tune,
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
           "-g", str(fps * 2), "-threads", "2"]
    if bitrate:
        cmd += ["-b:v", bitrate, "-maxrate", "14000k", "-bufsize", "20000k"]
    else:
        cmd += ["-crf", str(crf), "-x264-params", "aq-mode=3:aq-strength=0.95"]
    cmd += [keluar]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    t0 = time.time()
    n = hi - lo
    step = max(1, n // 8)
    try:
        for i in range(lo, hi):
            fr = mod.frame(i / float(fps))
            p.stdin.write(np.ascontiguousarray(fr).tobytes())
            if verbose and (i - lo) % step == 0:
                el = time.time() - t0
                sisa = el / max(1, i - lo + 1) * (hi - i - 1)
                print(f"    [{jobs_tag}] {i - lo + 1:4d}/{n}  {el:6.1f}s  "
                      f"sisa {sisa:6.1f}s", flush=True)
    finally:
        try:
            p.stdin.close()
        except BrokenPipeError:
            pass
        err = p.stderr.read().decode("utf-8", "replace")
        rc = p.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg gagal (potongan {lo}-{hi}, kode {rc}):\n{err[-700:]}")
    return time.time() - t0


def jalankan_worker(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True)
    ap.add_argument("--lo", type=int, required=True)
    ap.add_argument("--hi", type=int, required=True)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--crf", type=float, default=16)
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--bitrate")
    ap.add_argument("--keluar", required=True)
    ap.add_argument("--tag", default="")
    a = ap.parse_args(argv)
    mod = muat_episode(a.episode)
    dt = render_potongan(mod, a.lo, a.hi, a.fps, a.keluar, a.crf, a.preset,
                         "animation", a.bitrate, a.tag)
    print(f"    [{a.tag}] selesai {a.hi - a.lo} frame dalam {dt:.1f}s "
          f"({(a.hi - a.lo) / max(1e-6, dt):.1f} fps)", flush=True)
    return 0


# ============================================================ orkestrasi

def _bagi(total, n):
    """Bagi rentang frame jadi n potongan seimbang."""
    dasar = total // n
    sisa = total % n
    out = []
    lo = 0
    for i in range(n):
        d = dasar + (1 if i < sisa else 0)
        out.append((lo, lo + d))
        lo += d
    return out


def render_penuh(episode, keluar, audio=None, jobs=2, fps=60, crf=16,
                 preset="slow", bitrate=None, potong=None, verbose=True):
    mod = muat_episode(episode)
    info = mod.daftar()
    total_s = float(potong) if potong else info["total"]
    total_f = int(round(total_s * fps))
    os.makedirs(BUILD, exist_ok=True)
    parts_dir = os.path.join(BUILD, "parts")
    shutil.rmtree(parts_dir, ignore_errors=True)
    os.makedirs(parts_dir, exist_ok=True)

    if verbose:
        print(f"[episode] {episode} · {len(info['scenes'])} babak · {total_s:.2f} s "
              f"· {total_f} frame @ {fps} fps")
        print(f"[render ] {jobs} proses · preset {preset} · crf {crf}")

    t0 = time.time()
    rentang = _bagi(total_f, jobs)
    procs = []
    for i, (lo, hi) in enumerate(rentang):
        if hi <= lo:
            continue
        out = os.path.join(parts_dir, f"part_{i:02d}.mp4")
        cmd = [sys.executable, os.path.abspath(__file__), "--worker",
               "--episode", episode, "--lo", str(lo), "--hi", str(hi),
               "--fps", str(fps), "--crf", str(crf), "--preset", preset,
               "--keluar", out, "--tag", f"P{i}"]
        if bitrate:
            cmd += ["--bitrate", bitrate]
        procs.append((subprocess.Popen(cmd), out, lo, hi))
        if verbose:
            print(f"    mulai P{i}: frame {lo}-{hi}", flush=True)
    for p, out, lo, hi in procs:
        p.wait()
    gagal = [o for p, o, _, _ in procs if p.returncode != 0 or not os.path.exists(o)]
    if gagal:
        raise RuntimeError("ada potongan gagal: " + ", ".join(os.path.basename(g) for g in gagal))
    dt_render = time.time() - t0

    # ---- gabung potongan (tanpa encode ulang)
    daftar = os.path.join(parts_dir, "daftar.txt")
    with open(daftar, "w") as f:
        for _, out, _, _ in procs:
            f.write(f"file '{out}'\n")
    ff = ffmpeg()
    video_only = os.path.join(BUILD, "video_only.mp4")
    subprocess.run([ff, "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", daftar, "-c", "copy", video_only], check=True)

    os.makedirs(os.path.dirname(os.path.abspath(keluar)), exist_ok=True)
    t1 = time.time()
    if audio and os.path.exists(audio):
        subprocess.run([ff, "-y", "-v", "error", "-i", video_only, "-i", audio,
                        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                        "-c:a", "copy", "-shortest", "-movflags", "+faststart",
                        keluar], check=True)
    else:
        subprocess.run([ff, "-y", "-v", "error", "-i", video_only,
                        "-c", "copy", "-movflags", "+faststart", keluar], check=True)
    dt_mux = time.time() - t1

    if not os.environ.get("KT_SIMPAN_PARTS"):
        shutil.rmtree(parts_dir, ignore_errors=True)
        try:
            os.remove(video_only)
        except OSError:
            pass

    ukuran = os.path.getsize(keluar) / 1e6
    if verbose:
        print(f"[selesai] {keluar}")
        print(f"          render {dt_render:.1f}s · gabung+mux {dt_mux:.1f}s "
              f"· total {time.time() - t0:.1f}s")
        print(f"          {ukuran:.2f} MB · {total_f} frame · "
              f"{(total_f / max(1e-6, dt_render)):.1f} fps efektif/inti")
    return {"keluar": keluar, "detik": total_s, "frame": total_f,
            "render_s": round(dt_render, 2), "mux_s": round(dt_mux, 2),
            "mb": round(ukuran, 2)}


# ============================================================ pratinjau/ukur

def pratinjau(episode, n=4):
    from PIL import Image
    mod = muat_episode(episode)
    mod.siapkan()
    if hasattr(mod, "_siap_debu"):
        mod._siap_debu()
    d = mod.daftar()
    out = os.path.join(BUILD, "pratinjau")
    os.makedirs(out, exist_ok=True)
    for s in d["scenes"]:
        for frac in np.linspace(0.15, 0.88, n):
            t = s["mulai"] + s["dur"] * float(frac)
            p = os.path.join(out, f"{s['id']}_{frac:.2f}.jpg")
            Image.fromarray(mod.frame(t)).save(p, quality=90)
            print(f"  {s['id']:9s} t={t:6.2f} -> {p}")
    # lembar kontak
    import glob
    fs = sorted(glob.glob(os.path.join(out, "*.jpg")))
    kol = 5
    bar = (len(fs) + kol - 1) // kol
    sheet = Image.new("RGB", (360 * kol, 640 * bar), (0, 0, 0))
    for i, f in enumerate(fs):
        sheet.paste(Image.open(f).resize((360, 640)), ((i % kol) * 360, (i // kol) * 640))
    sp = os.path.join(out, "_lembar.jpg")
    sheet.save(sp, quality=90)
    print(f"[lembar] {sp}  ({len(fs)} frame)")
    return sp


def ukur(episode):
    mod = muat_episode(episode)
    t0 = time.time()
    mod.siapkan()
    if hasattr(mod, "_siap_debu"):
        mod._siap_debu()
    print(f"siapkan: {(time.time() - t0) * 1000:.0f} ms")
    d = mod.daftar()
    t1 = time.time()
    for s in d["scenes"]:
        mod.latar_scene(list(d["scenes"]).index(s))
    print(f"latar {len(d['scenes'])}: {(time.time() - t1) * 1000:.0f} ms")
    hasil = []
    for i, s in enumerate(d["scenes"]):
        # pemanasan cache dulu, baru ukur (penting: sprite dibuat sekali)
        for f in (0.1, 0.3, 0.5, 0.95):
            mod.frame(s["mulai"] + s["dur"] * f)
        t2 = time.time()
        n = 8
        for j in range(n):
            mod.frame(s["mulai"] + s["dur"] * (0.25 + 0.7 * j / n))
        ms = (time.time() - t2) / n * 1000
        hasil.append((s["id"], ms))
        print(f"  {s['id']:9s} {ms:6.2f} ms/frame")
    rata = sum(h[1] for h in hasil) / len(hasil)
    print(f"rata-rata {rata:.2f} ms/frame -> 1 inti {1000 / rata:.1f} fps, "
          f"{rata * d['total'] / 1000:.0f} s untuk {d['total']:.0f} s video")
    return hasil


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--worker" in argv:
        argv = [a for a in argv if a != "--worker"]
        return jalankan_worker(argv)

    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default="ep56")
    ap.add_argument("--keluar", default=os.path.join(BASE, "dist", "KlikTahu_Ep56_v20.mp4"))
    ap.add_argument("--audio")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--crf", type=float, default=16)
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--bitrate")
    ap.add_argument("--potong", type=float)
    ap.add_argument("--tanpa-audio", action="store_true")
    ap.add_argument("--pratinjau", type=int, default=0)
    ap.add_argument("--ukur", action="store_true")
    a = ap.parse_args(argv)

    if a.ukur:
        ukur(a.episode)
        return 0
    if a.pratinjau:
        pratinjau(a.episode, a.pratinjau)
        return 0
    audio = None if a.tanpa_audio else a.audio
    lap = render_penuh(a.episode, a.keluar, audio, a.jobs, a.fps, a.crf,
                       a.preset, a.bitrate, a.potong)
    with open(os.path.join(BUILD, "render.json"), "w") as f:
        json.dump(lap, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
