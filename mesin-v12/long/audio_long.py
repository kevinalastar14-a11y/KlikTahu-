#!/usr/bin/env python3
"""Audio video panjang (16:9): master VO (hasil master_audio.py) + lapisan SFX dari BEATS.

VO tidak pernah dipotong/dipercepat: SFX hanya DITAMBAHKAN di atas VO, di-duck saat
VO bersuara, lalu limiter lembut hanya menekan puncak > -1.2 dBFS.

  python3 long/audio_long.py --slug v01_lubang_hitam [--timeline timeline.json]
         [--master build/audio_master.wav] [--out build/audio_long.wav]
"""
import argparse, importlib.util, json, os, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import sfx                      # noqa: E402
import mesin_long as L          # noqa: E402

TARGET_PEAK = -1.2


def db(x):
    return 20 * np.log10(max(1e-12, x))


def baca(p):
    with wave.open(p) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, ch)
    a = a.astype(np.float64) / 32768.0
    if ch == 1:
        a = np.repeat(a, 2, axis=1)
    return a, sr


def tulis(p, a, sr):
    with wave.open(p, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(a, -1, 1) * 32767.0).astype("<i2").tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--timeline", default=os.path.join(ROOT, "timeline.json"))
    bdir = os.environ.get("KT_BUILD") or os.path.join(ROOT, "build")
    ap.add_argument("--master", default=os.path.join(bdir, "audio_master.wav"))
    ap.add_argument("--out", default=os.path.join(bdir, "audio_long.wav"))
    ap.add_argument("--sfx-db", type=float, default=float(os.environ.get("KT_SFX_DB", "-16")))
    ar = ap.parse_args()

    spec = importlib.util.spec_from_file_location("vis", os.path.join(HERE, ar.slug, "visual.py"))
    vis = importlib.util.module_from_spec(spec); spec.loader.exec_module(vis)
    tl = json.load(open(ar.timeline))
    ev = [e for e in L.events(tl, getattr(vis, "BEATS", {})) if e[1] in sfx.KATALOG]

    a, sr = baca(ar.master)
    assert sr == sfx.SR, f"sample rate {sr} != {sfx.SR}"
    vo = a.mean(axis=1)
    lay = sfx.duck(sfx.lapisan(ev, len(vo) / sr, ar.sfx_db), vo)[: len(vo)]
    if len(lay) < len(vo):
        lay = np.pad(lay, (0, len(vo) - len(lay)))
    out = a.copy()
    out[:, 0] += lay * 0.96
    out[:, 1] += lay * 1.00
    # limiter lembut: hanya puncak yang melewati target (lookahead 4 ms, tanpa memotong kata)
    lim = 10 ** (TARGET_PEAK / 20)
    pk = np.abs(out).max(axis=1)
    over = pk > lim
    if over.any():
        g = np.ones(len(out))
        g[over] = lim / pk[over]
        k = int(sr * 0.004)
        g = np.lib.stride_tricks.sliding_window_view(np.pad(g, (k, k), constant_values=1.0), 2 * k + 1).min(axis=1)
        out *= g[:, None]
    tulis(ar.out, out, sr)

    # QC: VO utuh -> korelasi tinggi dengan master VO, tidak ada bagian VO yang hilang
    r = np.corrcoef(out.mean(axis=1), vo)[0, 1]
    blk = int(sr * 0.5)
    n = len(vo) // blk
    e_in = np.sqrt((vo[: n * blk].reshape(n, blk) ** 2).mean(axis=1))
    e_out = np.sqrt((out.mean(axis=1)[: n * blk].reshape(n, blk) ** 2).mean(axis=1))
    bicara = e_in > 10 ** (-40 / 20)
    turun = int(((e_out < e_in * 10 ** (-1.5 / 20)) & bicara).sum())
    clip = int((np.abs(out) >= 0.9995).sum())
    print(f"audio_long -> {ar.out}")
    print(f"  {len(ev)} SFX | panjang {len(out)/sr:.2f}s | puncak {db(np.abs(out).max()):.1f} dBFS "
          f"| SFX {db(np.sqrt((lay**2).mean())) - db(np.sqrt((vo**2).mean())):+.1f} dB vs VO")
    print(f"  korelasi VO {r:.4f} | blok VO turun >1.5 dB: {turun} | clipping {clip}")
    if r < 0.97 or turun > 0 or clip > 40:
        print("AUDIO LONG GAGAL QC"); sys.exit(1)
    print("AUDIO LONG OK")


if __name__ == "__main__":
    main()
