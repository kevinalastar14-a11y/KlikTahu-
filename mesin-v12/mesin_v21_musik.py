#!/usr/bin/env python3
"""mesin_v21_musik.py — lapisan musik latar untuk video gaya kertas (v21).

Kenapa ada lapisan ini
----------------------
Acuan gaya (video short lama) hanya berisi suara narator + jeda hening total.
Jeda hening panjang membuat video terasa "amatir" dan menurunkan retensi.
Lapisan di sini mengisi jeda itu TANPA mengganggu narasi:

  * pad akor lambat (2 akor per 8 detik) pada nada rendah, sangat pelan;
  * denyut halus (pulsa 60 bpm) sebagai penanda waktu, -38 dBFS;
  * ducking otomatis: setiap kali VO aktif, musik turun 4,5 dB (sidechain
    sederhana berbasis selubung amplitudo, tanpa pustaka tambahan);
  * tidak ada ketukan tajam/ritmis: gaya visualnya tenang, jadi musiknya
    juga harus tenang.

Hasil: `keluaran/KlikTahu_Ep58_audio_musik.wav` siap dimaster ulang oleh
`mesin_v20_audio.master()` (loudnorm dua lintasan, target -14 LUFS).

Pakai:
    python3 mesin_v21_musik.py --masuk audio/vo58/campuran.wav \\
        --keluar audio/vo58/campuran_musik.wav --bpm 60 --level -33
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import mesin_v20_audio as A  # noqa: E402

SR = A.SR


def _nada(freq, n, sr=SR, bentuk="sin"):
    t = np.arange(n, dtype=np.float32) / sr
    w = 2 * np.pi * freq * t
    if bentuk == "sin":
        return np.sin(w).astype(np.float32)
    if bentuk == "tri":  # segitiga lembut (~-20 dB harmonik ganjil)
        return (2 / np.pi * np.arcsin(np.sin(w))).astype(np.float32)
    raise ValueError(bentuk)


def _pad(dur, akor, sr=SR, attack=1.6, release=1.6):
    """Satu akor: 3-4 nada, gelombang segitiga + sedikit detune -> tebal."""
    n = int(dur * sr)
    x = np.zeros(n, np.float32)
    for f in akor:
        x += _nada(f, n, sr, "tri") * 0.6
        x += _nada(f * 1.0035, n, sr, "sin") * 0.25   # detune halus (chorus)
        x += _nada(f * 2.0, n, sr, "sin") * 0.08      # oktaf tipis
    # selubung per akor: naik lembut, tahan, turun lembut
    a = int(attack * sr)
    r = int(release * sr)
    env = np.ones(n, np.float32)
    if a > 0:
        env[:a] = np.linspace(0, 1, a) ** 1.6
    if r > 0 and r < n:
        env[-r:] = np.linspace(1, 0, r) ** 1.4
    return x * env / max(1, len(akor))


#: progresi akor minor yang tenang (A minor add9 -> F maj7 -> C -> G)
AKOR = [
    (110.00, 164.81, 261.63, 329.63),   # A2 E3 C4 E4
    (87.31, 130.81, 220.00, 329.63),    # F2 C3 A3 E4
    (130.81, 196.00, 261.63, 392.00),   # C3 G3 C4 G4
    (98.00, 146.83, 246.94, 392.00),    # G2 D3 B3 G4
]


def buat_pad(total, sr=SR, panjang_akor=7.5):
    n = int(total * sr)
    out = np.zeros(n, np.float32)
    i = 0
    k = 0
    while i < n:
        dur = panjang_akor * (1.0 if k % 4 != 3 else 1.25)
        seg = _pad(dur, AKOR[k % len(AKOR)], sr)
        m = min(len(seg), n - i)
        # tumpang tindih 0,9 s dengan akor berikutnya agar tidak ada "jahitan"
        out[i:i + m] += seg[:m]
        i += int((dur - 0.9) * sr)
        k += 1
    return out


def buat_denyut(total, bpm=60.0, sr=SR):
    """Denyut rendah (bukan ketukan tajam): sinus 52 Hz dengan selubung pendek."""
    n = int(total * sr)
    out = np.zeros(n, np.float32)
    jarak = 60.0 / bpm
    t = 0.35
    while t < total - 0.3:
        d = 0.55
        m = int(d * sr)
        env = np.exp(-np.linspace(0, 5.2, m)).astype(np.float32)
        fase = np.cumsum(np.full(m, 2 * np.pi * 52.0 / sr, np.float32))
        seg = np.sin(fase).astype(np.float32) * env
        i = int(t * sr)
        mm = min(m, n - i)
        out[i:i + mm] += seg[:mm]
        t += jarak
    return out


def selubung_vo(x, sr=SR, naik=0.05, turun=0.35):
    """Selubung amplitudo VO -> dipakai untuk ducking musik."""
    mono = np.abs(x).mean(axis=1) if x.ndim > 1 else np.abs(x)
    hop = int(0.02 * sr)
    m = len(mono) // hop
    e = mono[:m * hop].reshape(m, hop).max(axis=1)
    # serangan cepat, pelepasan lambat (meniru kompresor sidechain)
    # normalisasi: amplitudo bicara normal (~0,06) dianggap "aktif penuh".
    # Tanpa ini selubung jarang mencapai 1 dan ducking nyaris tak terdengar
    # (terukur hanya 0,7 dB, seharusnya 4,5 dB).
    e = np.clip(e / 0.060, 0.0, 1.0)
    keluar = np.zeros(m, np.float32)
    v = 0.0
    an = naik / 0.02
    tu = turun / 0.02
    for i, val in enumerate(e):
        target = float(val)
        if target > v:
            v = v + (target - v) * min(1.0, 1.0 / max(1e-3, an))
        else:
            v = v + (target - v) * min(1.0, 1.0 / max(1e-3, tu))
        keluar[i] = v
    # naikkan ke laju audio penuh
    idx = np.clip((np.arange(len(mono)) / hop).astype(int), 0, m - 1)
    return keluar[idx]


def utama(masuk, keluar, level_db=-33.0, bpm=60.0, duck_db=4.5):
    x = A.baca_wav(masuk)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    total = x.shape[0] / SR
    print(f"[musik] {total:.2f} s · pad + denyut {bpm:.0f} bpm · {level_db:.0f} dBFS")
    pad = buat_pad(total)
    denyut = buat_denyut(total, bpm)
    mus = pad * 1.0 + denyut * 0.45
    # normalisasi puncak musik lalu set level
    puncak = float(np.abs(mus).max()) or 1.0
    mus = mus / puncak * (10 ** (level_db / 20.0))
    # ducking
    duck = 1.0 - (10 ** (-duck_db / 20.0) - 1.0) * -1.0 * selubung_vo(x)
    duck = np.clip(duck, 10 ** (-duck_db / 20.0), 1.0)
    stereo = np.stack([mus * duck, np.roll(mus, int(0.011 * SR)) * duck], axis=1)
    # buang bagian ekor yang terlipat roll
    stereo[:int(0.011 * SR), 1] = mus[:int(0.011 * SR)] * duck[:int(0.011 * SR)]
    y = np.clip(x + stereo, -1.0, 1.0)
    A.tulis_wav(keluar, y)
    tes = np.abs(stereo).max()
    print(f"[musik] ditulis {keluar}")
    print(f"        level musik efektif {20 * np.log10(max(1e-9, tes)):.1f} dBFS "
          f"(duck {duck_db} dB saat VO)")
    return keluar


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--masuk", default=os.path.join(BASE, "audio/vo58/campuran.wav"))
    ap.add_argument("--keluar", default=os.path.join(BASE, "audio/vo58/campuran_musik.wav"))
    ap.add_argument("--level", type=float, default=-33.0)
    ap.add_argument("--bpm", type=float, default=60.0)
    ap.add_argument("--duck", type=float, default=4.5)
    a = ap.parse_args(argv)
    utama(a.masuk, a.keluar, a.level, a.bpm, a.duck)
    return 0


if __name__ == "__main__":
    sys.exit(main())
