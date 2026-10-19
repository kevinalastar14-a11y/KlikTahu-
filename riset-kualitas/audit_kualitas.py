#!/usr/bin/env python3
"""
audit_kualitas.py — Audit kualitas video KlikTahu secara terukur (bukan selera).

Menjawab pertanyaan: "video ini terasa lebih hidup/premium atau tidak, dan
kenapa?" dengan angka yang bisa dibandingkan antar-versi dan antar-referensi.

Metrik VISUAL (satu lintasan baca frame, hemat memori):
  motion_mean/p10/p50/p90/p99   selisih luma antar-frame berurutan -> energi gerak
  static_pct                    % frame dengan gerak < 0.35 (terasa beku)
  event_density                 jumlah lonjakan gerak per detik (ritme)
  luma_mean/std/p1/p99/dr       nada & rentang dinamis
  clip_black/clip_white         % piksel terjepit
  entropy                       kekayaan tonal (bit)
  grain                         amplitudo residual frekuensi tinggi (tekstur)
  flat_pct                      % blok 8x8 nyaris rata (risiko banding)
  edge_p99                      ketajaman tepi (akutan)
  colorfulness                  metrik Hasler-Süsstrunk
  palette                       warna dominan (kuantisasi 4 bit)

Metrik AUDIO:
  lufs, true peak, LRA, RMS, noise floor
  stereo_corr, side_mid         lebar stereo (1.000 / 0.00 = mono)
  bands                         energi per pita (deteksi "muffled"/"boxy")

Pakai:
    python3 riset-kualitas/audit_kualitas.py VIDEO [VIDEO ...] --out hasil/
    python3 riset-kualitas/audit_kualitas.py --banding v1.mp4 v2.mp4
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys

import numpy as np

try:
    import imageio_ffmpeg
except ImportError:                                        # pragma: no cover
    sys.exit("butuh imageio-ffmpeg:  pip install imageio-ffmpeg")

FF = imageio_ffmpeg.get_ffmpeg_exe()

# Resolusi analisis: cukup untuk statistik global, cukup kecil untuk memori.
AW, AH = 270, 480          # abu-abu (metrik luma/gerak/tepi)
CW, CH = 90, 160           # warna (colorfulness + palet)
FPS_ANALISIS = 12.0

BANDS = [(0, 80), (80, 120), (120, 300), (300, 1000), (1000, 2000),
         (2000, 4000), (4000, 8000), (8000, 16000), (16000, 24000)]
BAND_LABEL = ["<80", "80-120", "120-300", "300-1k", "1-2k", "2-4k", "4-8k", "8-16k", "16-24k"]


# --------------------------------------------------------------------------- #
#  Probe kontainer
# --------------------------------------------------------------------------- #
def probe(path: str) -> dict:
    out = subprocess.run([FF, "-hide_banner", "-i", path],
                         capture_output=True, text=True).stderr
    info: dict = {"file": os.path.basename(path),
                  "size_mb": round(os.path.getsize(path) / 1048576, 2)}
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    if m:
        info["duration_s"] = round(int(m.group(1)) * 3600 + int(m.group(2)) * 60
                                   + float(m.group(3)), 3)
    m = re.search(r"bitrate: (\d+) kb/s", out)
    if m:
        info["kbps"] = int(m.group(1))
    v = re.search(r"Video: (\w+).*?, (\d+)x(\d+).*?, (\d+(?:\.\d+)?) fps", out)
    if v:
        info.update(vcodec=v.group(1), width=int(v.group(2)), height=int(v.group(3)),
                    fps=float(v.group(4)))
        info["ar"] = "9:16" if abs(int(v.group(2)) / int(v.group(3)) - 9 / 16) < 0.02 else \
                     "16:9" if abs(int(v.group(2)) / int(v.group(3)) - 16 / 9) < 0.02 else "lain"
    a = re.search(r"Audio: (\w+)", out)
    info["audio_codec"] = a.group(1) if a else None
    s = re.search(r"Audio: .*?, (\d+) Hz, (mono|stereo|[\d.]+\(.*?\))", out)
    if s:
        info["audio_layout"] = s.group(2)
    return info


# --------------------------------------------------------------------------- #
#  Visual
# --------------------------------------------------------------------------- #
def _blocks(lum: np.ndarray, b: int = 8) -> np.ndarray:
    h, w = (lum.shape[0] // b) * b, (lum.shape[1] // b) * b
    v = lum[:h, :w].reshape(h // b, b, w // b, b).transpose(0, 2, 1, 3)
    return v.reshape(-1, b * b)


def visual_metrics(path: str) -> dict:
    cmd = [FF, "-v", "error", "-i", path, "-vf",
           f"fps={FPS_ANALISIS},scale={AW}:{AH}:flags=area", "-f", "rawvideo",
           "-pix_fmt", "gray", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    fs = AW * AH
    prev = None
    diffs, luma_means, p1s, p99s = [], [], [], []
    black, white, mid, sharp, grain, flat, edge = [], [], [], [], [], [], []
    hist = np.zeros(64, dtype=np.float64)
    n = 0
    while True:
        raw = proc.stdout.read(fs)
        if len(raw) < fs:
            break
        lum = np.frombuffer(raw, dtype=np.uint8).reshape(AH, AW).astype(np.float32)
        n += 1
        luma_means.append(float(lum.mean()))
        p1s.append(float(np.percentile(lum, 1)))
        p99s.append(float(np.percentile(lum, 99)))
        black.append(float((lum < 2).mean() * 100))
        white.append(float((lum > 253).mean() * 100))
        mid.append(float(((lum > 32) & (lum < 224)).mean() * 100))
        hist += np.bincount((lum.ravel() // 4).astype(np.int64), minlength=64)[:64]
        # residual frekuensi tinggi (grain / detail mikro)
        box = (lum[:-2, 1:-1] + lum[2:, 1:-1] + lum[1:-1, :-2] + lum[1:-1, 2:]
               + 4 * lum[1:-1, 1:-1]) / 8.0
        grain.append(float((lum[1:-1, 1:-1] - box).std()))
        # laplacian
        l = -4 * lum
        l[1:-1, 1:-1] += lum[:-2, 1:-1] + lum[2:, 1:-1] + lum[1:-1, :-2] + lum[1:-1, 2:]
        sharp.append(float(l[1:-1, 1:-1].var()))
        blk = _blocks(lum)
        flat.append(float((blk.std(axis=1) < 0.9).mean() * 100))
        g = np.concatenate([np.abs(np.diff(lum, axis=1)).ravel(),
                            np.abs(np.diff(lum, axis=0)).ravel()])
        edge.append(float(np.percentile(g, 99)))
        if prev is not None:
            diffs.append(float(np.abs(lum - prev).mean()))
        prev = lum
    proc.stdout.close()
    proc.wait()

    d = np.array(diffs if diffs else [0.0])
    h = hist / max(1.0, hist.sum())
    ent = float(-(h[h > 0] * np.log2(h[h > 0])).sum())
    return dict(
        frames=n,
        motion_mean=round(float(d.mean()), 3),
        motion_p10=round(float(np.percentile(d, 10)), 3),
        motion_p50=round(float(np.percentile(d, 50)), 3),
        motion_p90=round(float(np.percentile(d, 90)), 3),
        motion_p99=round(float(np.percentile(d, 99)), 3),
        static_pct=round(float((d < 0.35).mean() * 100), 2),
        event_density=round(float((d > max(3.0, np.percentile(d, 90) * 1.6)).sum()
                                  / max(1e-6, n / FPS_ANALISIS)), 2),
        luma_mean=round(float(np.mean(luma_means)), 2),
        luma_p1=round(float(np.mean(p1s)), 2),
        luma_p99=round(float(np.mean(p99s)), 2),
        luma_dr=round(float(np.mean(p99s) - np.mean(p1s)), 2),
        clip_black=round(float(np.mean(black)), 2),
        clip_white=round(float(np.mean(white)), 2),
        midtone_pct=round(float(np.mean(mid)), 2),
        entropy=round(ent, 3),
        grain=round(float(np.mean(grain)), 3),
        flat_pct=round(float(np.mean(flat)), 2),
        edge_p99=round(float(np.mean(edge)), 2),
        sharpness=round(float(np.mean(sharp)), 1),
    )


def color_metrics(path: str) -> dict:
    cmd = [FF, "-v", "error", "-i", path, "-vf",
           f"fps=2,scale={CW}:{CH}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    fs = CW * CH * 3
    rg, yb, sat, quants = [], [], [], {}
    while True:
        raw = p.stdout.read(fs)
        if len(raw) < fs:
            break
        fr = np.frombuffer(raw, dtype=np.uint8).reshape(CH, CW, 3).astype(np.float32)
        R, G, B = fr[..., 0], fr[..., 1], fr[..., 2]
        rg.append((R - G).ravel())
        yb.append((0.5 * (R + G) - B).ravel())
        mx, mn = fr.max(-1), fr.min(-1)
        sat.append(np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0).ravel())
        q = (fr // 32).astype(np.int32)
        key = (q[..., 0] * 64 + q[..., 1] * 8 + q[..., 2]).ravel()
        vals, cnts = np.unique(key, return_counts=True)
        for v, c in zip(vals, cnts):
            quants[int(v)] = quants.get(int(v), 0) + int(c)
    p.stdout.close()
    p.wait()
    rg = np.concatenate(rg)
    yb = np.concatenate(yb)
    sat = np.concatenate(sat)
    colorfulness = (math.sqrt(rg.std() ** 2 + yb.std() ** 2)
                    + 0.3 * math.sqrt(rg.mean() ** 2 + yb.mean() ** 2))
    tot = max(1, sum(quants.values()))
    top = sorted(quants.items(), key=lambda kv: -kv[1])[:5]
    pal = []
    for k, c in top:
        r, g, b = (k // 64) * 32 + 16, ((k // 8) % 8) * 32 + 16, (k % 8) * 32 + 16
        pal.append({"hex": f"#{r:02X}{g:02X}{b:02X}", "pct": round(c / tot * 100, 1)})
    return dict(colorfulness=round(float(colorfulness), 2),
                saturation_pct=round(float(sat.mean() * 100), 2),
                palette=pal)


# --------------------------------------------------------------------------- #
#  Audio
# --------------------------------------------------------------------------- #
def audio_metrics(path: str) -> dict | None:
    p = subprocess.run([FF, "-v", "error", "-i", path, "-vn", "-f", "f32le",
                        "-ac", "2", "-ar", "48000", "-"], capture_output=True)
    if p.returncode != 0 or not p.stdout:
        return {"has_audio": False}
    x = np.frombuffer(p.stdout, dtype="<f4").reshape(-1, 2).astype(np.float32)
    if x.size == 0:
        return {"has_audio": False}
    sr = 48000
    m = x.mean(axis=1)
    rms = 20 * math.log10(float(np.sqrt((m ** 2).mean())) + 1e-12)
    w = int(sr * 0.05)
    k = len(m) // w
    fdb = 20 * np.log10(np.sqrt((m[:k * w].reshape(k, w) ** 2).mean(axis=1)) + 1e-12)
    l, r = x[:, 0], x[:, 1]
    corr = float(np.corrcoef(l, r)[0, 1]) if l.std() > 0 else 1.0
    side = float(np.sqrt(((l - r) ** 2).mean()) / (np.sqrt(((l + r) ** 2).mean()) + 1e-12))
    n = 1 << int(math.ceil(math.log2(len(m))))
    f = np.fft.rfftfreq(n, 1 / sr)
    P = np.abs(np.fft.rfft(m, n)) ** 2
    tot = P[f > 20].sum() + 1e-12
    bands = [round(float(10 * math.log10(P[(f >= a) & (f < b)].sum() / tot + 1e-12)), 1)
             for a, b in BANDS]
    loud = subprocess.run([FF, "-hide_banner", "-i", path, "-af",
                           "loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    mm = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", loud, re.S)
    L = json.loads(mm.group(0)) if mm else {}
    presence = round((bands[5] + bands[6]) / 2, 1)
    air = round((bands[7] + bands[8]) / 2, 1)
    low = round(float(10 * math.log10(sum(10 ** (v / 10) for v in bands[:3]) + 1e-12)), 1)
    return dict(
        has_audio=True,
        lufs=round(float(L.get("input_i", float("nan"))), 2),
        true_peak_dbtp=round(float(L.get("input_tp", float("nan"))), 2),
        lra=round(float(L.get("input_lra", float("nan"))), 2),
        rms_dbfs=round(rms, 2),
        noise_floor_db=round(float(np.percentile(fdb, 10)), 1),
        speech_p95_db=round(float(np.percentile(fdb, 95)), 1),
        stereo_corr=round(corr, 3),
        side_mid=round(side, 4),
        bands_db=dict(zip(BAND_LABEL, bands)),
        presence_2_8k=presence,
        air_8_24k=air,
        low_lt300=low,
    )


# --------------------------------------------------------------------------- #
def audit(path: str) -> dict:
    info = probe(path)
    print(f"[audit] {os.path.basename(path)}  visual...", flush=True)
    info.update(visual_metrics(path))
    print(f"[audit] {os.path.basename(path)}  warna...", flush=True)
    info.update(color_metrics(path))
    print(f"[audit] {os.path.basename(path)}  audio...", flush=True)
    a = audio_metrics(path)
    if a:
        info["audio"] = a
    return info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Audit kualitas video KlikTahu")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default=None, help="folder keluaran JSON/CSV")
    ap.add_argument("--json", action="store_true", help="cetak JSON ke stdout")
    args = ap.parse_args(argv)

    rows = [audit(f) for f in args.files]
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        for r in rows:
            with open(os.path.join(args.out, r["file"] + ".json"), "w") as fh:
                json.dump(r, fh, indent=1, ensure_ascii=False)
        with open(os.path.join(args.out, "ringkasan.json"), "w") as fh:
            json.dump(rows, fh, indent=1, ensure_ascii=False)
        cols = ["file", "duration_s", "ar", "motion_mean", "static_pct", "event_density",
                "luma_mean", "luma_dr", "clip_black", "entropy", "grain", "flat_pct",
                "edge_p99", "colorfulness", "saturation_pct"]
        with open(os.path.join(args.out, "ringkasan.csv"), "w") as fh:
            fh.write(",".join(cols) + "\n")
            for r in rows:
                fh.write(",".join(str(r.get(c, "")) for c in cols) + "\n")
    if args.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return 0

    # tabel ringkas
    print("\n" + "=" * 108)
    hdr = f'{"file":34s} {"ar":>5s} {"motion":>7s} {"static%":>8s} {"event/s":>8s} ' \
          f'{"luma":>6s} {"DR":>6s} {"grain":>6s} {"flat%":>6s} {"edge":>6s} {"colf":>6s}'
    print(hdr)
    print("-" * 108)
    for r in rows:
        print(f'{r["file"]:34s} {r.get("ar",""):>5s} {r["motion_mean"]:7.2f} '
              f'{r["static_pct"]:8.1f} {r["event_density"]:8.2f} {r["luma_mean"]:6.1f} '
              f'{r["luma_dr"]:6.1f} {r["grain"]:6.2f} {r["flat_pct"]:6.1f} '
              f'{r["edge_p99"]:6.1f} {r["colorfulness"]:6.1f}')
    print("-" * 108)
    for r in rows:
        a = r.get("audio") or {}
        if a.get("has_audio"):
            print(f'{r["file"]:34s} audio: {a["lufs"]:+.1f} LUFS  TP {a["true_peak_dbtp"]:+.1f}  '
                  f'LRA {a["lra"]:.1f}  corr {a["stereo_corr"]:.3f}  side/mid {a["side_mid"]:.3f}  '
                  f'presence {a["presence_2_8k"]:+.1f} dB  air {a["air_8_24k"]:+.1f} dB')
        else:
            print(f'{r["file"]:34s} audio: (tidak ada)')
    return 0


if __name__ == "__main__":
    sys.exit(main())
