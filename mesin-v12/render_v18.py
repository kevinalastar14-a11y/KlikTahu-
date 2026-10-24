#!/usr/bin/env python3
"""render_v18.py — renderer cepat KlikTahu v18 (pipe langsung ke x264).

Kenapa renderer terpisah
------------------------
`tools/render_lokal.sh` menulis 6.129 file JPEG ke disk lalu membacanya lagi
untuk di-encode: 6.129 x (16 ms tulis + 8 ms baca) = ~2,5 menit terbuang, belum
termasuk I/O dan risiko disk penuh. v18 tidak menyentuh disk untuk frame:
setiap proses merender rentang frame lalu menulis PIPELINE `rawvideo` ke stdin
ffmpeg, yang langsung meng-encode H.264.

Alur
----
    proses 0: frame 0..k    -> ffmpeg -> parts/part_0.mp4  ┐
    proses 1: frame k..2k   -> ffmpeg -> parts/part_1.mp4  ├─ concat -> remux audio
    proses N: ...           -> ffmpeg -> parts/part_N.mp4  ┘

Setiap proses memakai satu inti; jumlah proses = jumlah inti (bisa dioverride).
Karena animasi dihitung dari waktu absolut (`frame -> t = i/fps`), hasil render
per potongan identik dengan render satu proses penuh (deterministik, tanpa state).

Pemakaian
---------
    python3 render_v18.py --episode ep55 --keluar dist/out.mp4 --audio audio.m4a
    python3 render_v18.py --episode ep55 --pratinjau 3      # 3 frame uji
    python3 render_v18.py --episode ep55 --ukur             # profil kecepatan

Opsi penting
------------
    --jobs N     jumlah proses paralel (bawaan: jumlah inti)
    --fps        bawaan 60
    --crf        bawaan 19 (kualitas x264; makin kecil makin bagus)
    --preset     bawaan "fast" (slow/medium/fast/veryfast)
    --potong S   hanya render S detik pertama (uji cepat)
    --tanpa-audio  hasil video saja (untuk QC gambar)
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


def ffmpeg():
    """Cari binary ffmpeg (PATH dulu, lalu imageio-ffmpeg)."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def muat_episode(nama):
    """Impor modul episode: `ep55` -> `mesin_v18_ep55`."""
    mod = nama if nama.startswith("mesin_v18_") else f"mesin_v18_{nama}"
    return importlib.import_module(mod)


def info(mod):
    d = mod.daftar()
    return d["total"], d["scenes"]


# ============================================================ worker

def render_potongan(mod, lo, hi, fps, keluar, crf=19, preset="fast", tune="animation",
                    bitrate=None, verbose=True):
    """Render frame [lo, hi) lalu pipe ke ffmpeg -> `keluar` (mp4 tanpa audio)."""
    mod.siapkan()
    ff = ffmpeg()
    cmd = [ff, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", preset, "-tune", tune,
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
           "-g", str(fps * 2), "-threads", "2"]
    if bitrate:
        cmd += ["-b:v", bitrate, "-maxrate", "11000k", "-bufsize", "16000k"]
    else:
        cmd += ["-crf", str(crf)]
    cmd += [keluar]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    n = hi - lo
    try:
        for i in range(lo, hi):
            fr = mod.frame(i / float(fps))
            p.stdin.write(fr.tobytes())
            if verbose and (i - lo) % max(1, n // 6) == 0:
                el = time.time() - t0
                sisa = el / max(1, i - lo + 1) * (hi - i - 1)
                print(f"    [{lo:5d}-{hi:5d}] {i - lo + 1}/{n}  {el:5.1f}s  sisa {sisa:5.1f}s",
                      flush=True)
    finally:
        try:
            p.stdin.close()
        except BrokenPipeError:
            pass
        rc = p.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg gagal pada potongan {lo}-{hi} (kode {rc})")
    return time.time() - t0


def jalankan_worker(argv):
    """Mode internal: satu proses mengerjakan satu potongan."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True)
    ap.add_argument("--lo", type=int, required=True)
    ap.add_argument("--hi", type=int, required=True)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--keluar", required=True)
    ap.add_argument("--crf", type=float, default=19)
    ap.add_argument("--preset", default="fast")
    ap.add_argument("--tune", default="animation")
    ap.add_argument("--bitrate", default=None)
    a = ap.parse_args(argv)
    mod = muat_episode(a.episode)
    dt = render_potongan(mod, a.lo, a.hi, a.fps, a.keluar, a.crf, a.preset,
                         a.tune, a.bitrate)
    print(f"    selesai {a.lo}-{a.hi} dalam {dt:.1f}s", flush=True)
    return 0


# ============================================================ orkestrasi

def render_penuh(episode, keluar, audio=None, jobs=2, fps=60, crf=19,
                 preset="fast", tune="animation", bitrate=None, potong=None,
                 kerja=None, simpan_potongan=False):
    """Render seluruh episode secara paralel lalu gabungkan dengan audio."""
    mod = muat_episode(episode)
    total_s, scenes = info(mod)
    if potong:
        total_s = min(total_s, potong)
    total_frame = int(round(total_s * fps))
    kerja = kerja or os.path.join(BASE, "build_v18")
    os.makedirs(kerja, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(keluar)) or ".", exist_ok=True)

    print("=" * 74)
    print(f" KlikTahu v18 · {episode} · {total_frame} frame @ {fps} fps "
          f"({total_s:.2f} s) · {jobs} proses")
    print(f" preset {preset} · crf {crf} · tune {tune} · resolusi {W}x{H}")
    print("=" * 74)

    # --- bagi rentang frame ---
    n = max(1, jobs)
    per = (total_frame + n - 1) // n
    tugas = []
    for i in range(n):
        lo = i * per
        hi = min(total_frame, lo + per)
        if lo < hi:
            tugas.append((i, lo, hi))

    parts = []
    proses = []
    t_mulai = time.time()
    for i, lo, hi in tugas:
        keluar_part = os.path.join(kerja, f"part_{i:02d}.mp4")
        parts.append(keluar_part)
        cmd = [sys.executable, os.path.abspath(__file__), "--worker",
               "--episode", episode, "--lo", str(lo), "--hi", str(hi),
               "--fps", str(fps), "--keluar", keluar_part, "--crf", str(crf),
               "--preset", preset, "--tune", tune]
        if bitrate:
            cmd += ["--bitrate", bitrate]
        proses.append((subprocess.Popen(cmd), i, lo, hi))

    for p, i, lo, hi in proses:
        rc = p.wait()
        if rc != 0:
            raise RuntimeError(f"proses potongan {i} gagal (kode {rc})")

    t_render = time.time() - t_mulai
    print(f"[render] {total_frame} frame dalam {t_render:.1f}s "
          f"({t_render / total_frame * 1000:.1f} ms/frame/proses)")

    # --- gabung video ---
    daftar = os.path.join(kerja, "gabung.txt")
    with open(daftar, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    video = os.path.join(kerja, "video.mp4")
    ff = ffmpeg()
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", daftar, "-c", "copy", video], check=True)

    # --- remux audio (tanpa re-encode, audio sudah dimastering) ---
    if audio and os.path.exists(audio):
        subprocess.run([ff, "-y", "-loglevel", "error",
                        "-i", video, "-i", audio,
                        "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-c:a", "copy",
                        "-shortest", "-movflags", "+faststart", keluar], check=True)
    else:
        subprocess.run([ff, "-y", "-loglevel", "error", "-i", video,
                        "-c", "copy", "-movflags", "+faststart", keluar], check=True)

    if not simpan_potongan:
        for p in parts:
            try:
                os.remove(p)
            except OSError:
                pass

    ukuran = os.path.getsize(keluar)
    t_total = time.time() - t_mulai
    print("=" * 74)
    print(f" SELESAI · {keluar}")
    print(f"   {ukuran / 1e6:.2f} MB · {total_s:.2f} s · render {t_total:.1f}s "
          f"({t_total / 60:.2f} menit)")
    print(f"   kecepatan: {total_frame / t_total:.1f} frame/detik")
    print("=" * 74)
    return {"keluar": keluar, "ukuran": ukuran, "detik": t_total, "frame": total_frame}


def profil(episode, n_frame=24):
    """Ukur waktu per frame untuk tiap scene (tanpa encode)."""
    mod = muat_episode(episode)
    total_s, scenes = info(mod)
    t0 = time.time()
    mod.siapkan()
    print(f"siapkan (semua sprite): {(time.time() - t0) * 1000:.0f} ms")
    t0 = time.time()
    for i in range(len(scenes)):
        mod.latar_scene(i)
    print(f"latar {len(scenes)} scene: {(time.time() - t0) * 1000:.0f} ms")
    hasil = []
    for i, sc in enumerate(scenes):
        t = sc["mulai"] + sc["dur"] * 0.42
        t1 = time.time()
        for _ in range(n_frame):
            mod.frame(t)
        ms = (time.time() - t1) / n_frame * 1000
        hasil.append((sc["id"], ms))
        print(f"  {sc['id']:6s} {ms:6.2f} ms/frame")
    rata = sum(h[1] for h in hasil) / len(hasil)
    total_frame = int(round(total_s * 60))
    print(f"rata-rata {rata:.2f} ms/frame -> 1 proses {total_frame * rata / 1000:.0f}s, "
          f"2 proses {total_frame * rata / 2000:.0f}s (komposisi saja)")
    return hasil


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--worker" in argv:
        return jalankan_worker([a for a in argv if a != "--worker"])
    ap = argparse.ArgumentParser(description="Renderer cepat KlikTahu v18")
    ap.add_argument("--episode", default="ep55")
    ap.add_argument("--keluar", default=os.path.join(BASE, "dist", "v18.mp4"))
    ap.add_argument("--audio", default=None)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--crf", type=float, default=19)
    ap.add_argument("--preset", default="fast")
    ap.add_argument("--tune", default="animation")
    ap.add_argument("--bitrate", default=None)
    ap.add_argument("--potong", type=float, default=None, help="render S detik pertama")
    ap.add_argument("--ukur", action="store_true", help="profil kecepatan, tanpa encode")
    ap.add_argument("--pratinjau", type=int, default=0, help="simpan N frame contoh")
    a = ap.parse_args(argv)
    if a.ukur:
        profil(a.episode)
        return 0
    if a.pratinjau:
        from PIL import Image
        mod = muat_episode(a.episode)
        mod.siapkan()
        total_s, scenes = info(mod)
        out = os.path.join(BASE, "build_v18", "pratinjau")
        os.makedirs(out, exist_ok=True)
        for i, sc in enumerate(scenes):
            t = sc["mulai"] + sc["dur"] * 0.45
            fr = mod.frame(t)
            Image.fromarray(fr).save(os.path.join(out, f"{i:02d}_{sc['id']}.jpg"), quality=90)
            print(f"  {sc['id']:6s} t={t:6.2f} -> {out}/{i:02d}_{sc['id']}.jpg")
        print("total detik:", round(total_s, 2))
        return 0
    render_penuh(a.episode, a.keluar, a.audio, a.jobs, a.fps, a.crf, a.preset,
                 a.tune, a.bitrate, a.potong)
    return 0


if __name__ == "__main__":
    sys.exit(main())
