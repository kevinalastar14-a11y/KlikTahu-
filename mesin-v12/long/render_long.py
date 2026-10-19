#!/usr/bin/env python3
"""Render video panjang 16:9 (mesin_long).

Pemakaian:
  python3 long/render_long.py --slug v01_lubang_hitam --align          # isi waktu kata ke timeline.json
  python3 long/render_long.py --slug v01_lubang_hitam --check          # uji semua adegan (kata kunci ada?)
  python3 long/render_long.py --slug v01_lubang_hitam --sheet 5,20,33 --out sheet.png
  python3 long/render_long.py --slug v01_lubang_hitam --range 0:900 --out part_0.mp4
Frame dikirim langsung (rawvideo) ke ffmpeg - tanpa PNG perantara.
"""
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from PIL import Image  # noqa: E402
import mesin_long as L  # noqa: E402

G = {}


def load(slug, timeline):
    tl = json.load(open(timeline))
    p = os.path.join(HERE, slug, "visual.py")
    spec = importlib.util.spec_from_file_location("visual_" + slug, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return tl, mod


def init(slug, timeline, ss, fps):
    L.set_ss(ss)
    tl, mod = load(slug, timeline)
    G.update(tl=tl, mod=mod, fps=fps, ev=L.events(tl, mod.BEATS))


def scene_at(tl, t):
    sc = tl["scenes"]
    for i, s in enumerate(sc):
        if t < s["start"] + s["dur"]:
            return i
    return len(sc) - 1


def frame(t, k=0):
    tl, mod = G["tl"], G["mod"]
    scenes = tl["scenes"]
    i = scene_at(tl, t)
    sc = scenes[i]
    lt = t - sc["start"]
    C = L.Ctx(sc, lt, t, i, len(scenes))
    if hasattr(mod, "latar"):
        img = mod.latar(t, C)          # latar khusus video (mis. laut dalam berubah per kedalaman)
    else:
        img = L.latar(t, drift=getattr(mod, "DRIFT", 1.0), bintang=1.0)
    mod.VIS[sc["visual"]](img, C)
    # FX 2026: bokeh latar depan (kedalaman 2.5D) - bisa dimatikan per video (BOKEH = 0)
    bk = getattr(mod, "BOKEH", 1.0)
    if bk > 0:
        L.FX.bokeh(img, t, n=7, col=L.mix(C.acc, L.WHITE, 0.55), alpha=0.075 * bk, seed=11 + i,
                   rmin=L.S(14), rmax=L.S(52))
    # kamera: napas halus + gerak genggam organik (derau) + dorong beat berat + zoom adegan
    napas = 1.012 + 0.010 * math.sin(t * 0.23 + i)
    pk = L.punch(t, G["ev"])
    z = C.zoom * napas * (1 + pk)
    hx = 3.2 * L.FX.nois2(t * 0.45, 1)
    hy = 2.4 * L.FX.nois2(t * 0.45, 2)
    out = L.kamera(img, z, C.fx, C.fy, hx, hy)
    if pk > 0.008:                                   # blur gerak radial saat hentakan
        out = L.FX.zoom_blur(out, pk * 1.4, n=3)
    nxt = scenes[i + 1] if i + 1 < len(scenes) else sc
    out = L.transisi(out, lt, sc["dur"], i == 0, i == len(scenes) - 1, i=i, acc=C.acc,
                     acc_next=L.hexc(nxt.get("accent", "#F2994A")))
    ss = L.D.SS
    L.set_ss(1.0)
    try:
        if i > 0:
            L.kartu_bab(out, i, sc.get("bab", ""), lt, C.acc)
        if hasattr(mod, "overlay"):
            mod.overlay(out, C)
        L.hud(out, tl, i, t, C.acc, lt)
    finally:
        L.set_ss(ss)
    return L.akhiri(out, k)


def _one(k):
    fps = G["fps"]
    return frame(k / fps, k).tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--timeline", default=os.path.join(ROOT, "timeline.json"))
    ap.add_argument("--audio", default=os.path.join(ROOT, "audio_proc"))
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--ss", type=float, default=1.25)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--range", default="")
    ap.add_argument("--sheet", default="")
    ap.add_argument("--png", default="")
    ap.add_argument("--align", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--vb", default="9000k")
    ap.add_argument("--maxrate", default="14000k")
    ap.add_argument("--bufsize", default="20000k")
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--tune", default="animation")
    a = ap.parse_args()

    if a.align:
        tl = json.load(open(a.timeline))
        L.align(tl, a.audio)
        json.dump(tl, open(a.timeline, "w"), ensure_ascii=False, indent=1)
        for sc in tl["scenes"]:
            print(f"  {sc['id']}: {len(sc['words'])} kata, pertama {sc['words'][0][1]:.2f}s, "
                  f"terakhir {sc['words'][-1][1]:.2f}s / dur {sc['dur']:.2f}s")
        return

    init(a.slug, a.timeline, a.ss, a.fps)
    tl = G["tl"]

    if a.check:
        n = 0
        t0 = time.time()
        for sc in tl["scenes"]:
            k = 0.0
            while k < sc["dur"]:
                frame(sc["start"] + k)
                n += 1
                k += 0.5
        print(f"CEK OK: {n} frame uji di {len(tl['scenes'])} adegan ({(time.time()-t0)/n:.2f} s/frame)")
        print(f"event SFX: {len(G['ev'])}")
        return

    if a.sheet:
        ts = [float(x) for x in a.sheet.split(",") if x.strip()]
        cols = 3 if len(ts) > 4 else len(ts)
        rows = (len(ts) + cols - 1) // cols
        tw_, th_ = 640, 360
        sheet = Image.new("RGB", (cols * tw_, rows * (th_ + 26)), (0, 0, 0))
        from PIL import ImageDraw
        d = ImageDraw.Draw(sheet)
        for j, t in enumerate(ts):
            im = frame(t, j).resize((tw_, th_), Image.LANCZOS)
            x, y = (j % cols) * tw_, (j // cols) * (th_ + 26)
            sheet.paste(im, (x, y + 26))
            d.text((x + 8, y + 5), f"t={t:.2f}s", fill=(255, 255, 0))
        sheet.save(a.out or "sheet.png")
        print("sheet ->", a.out or "sheet.png")
        return

    if a.png:
        frame(float(a.png)).save(a.out or "frame.png")
        return

    total = int(round(tl["total"] * a.fps))
    lo, hi = 0, total
    if a.range:
        lo, hi = [int(x) for x in a.range.split(":")]
        hi = min(hi, total)
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{L.W}x{L.H}",
           "-r", str(a.fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", a.preset, "-tune", a.tune,
           "-b:v", a.vb, "-maxrate", a.maxrate, "-bufsize", a.bufsize, "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-level", "4.2", "-g", str(int(a.fps * 2)), a.out or "out.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    ks = list(range(lo, hi))
    if a.jobs > 1:
        import multiprocessing as mp
        ctx = mp.get_context("fork")
        with ctx.Pool(a.jobs) as pool:
            for j, buf in enumerate(pool.imap(_one, ks, chunksize=2)):
                p.stdin.write(buf)
                if j % 300 == 0:
                    print(f"  frame {lo + j}/{hi}  {(time.time()-t0)/(j+1):.3f} s/frame", flush=True)
    else:
        for j, k in enumerate(ks):
            p.stdin.write(_one(k))
    p.stdin.close()
    rc = p.wait()
    print(f"selesai {hi - lo} frame dalam {time.time()-t0:.0f}s -> {a.out} (rc {rc})")
    sys.exit(rc)


if __name__ == "__main__":
    main()
