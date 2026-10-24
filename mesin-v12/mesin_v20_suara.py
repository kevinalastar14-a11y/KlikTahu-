#!/usr/bin/env python3
"""mesin_v20_suara.py — naskah -> VO -> campuran -> audio telinga (M4A).

Alur
----
  1. baca NASKAH dari modul episode (`mesin_v20_ep56`)
  2. sintesis per babak lewat edge-tts (suara `id-ID-ArdiNeural`)
  3. rapikan tiap klip: buang hening sejati, pra-gulir 120 ms / pasca 320 ms,
     fade raised-cosine 30/180 ms  -> TIDAK memotong kata, TIDAK time-stretch
  4. ukur durasi nyata -> tulis `audio/vo/timing.json` (dipakai mesin gambar)
  5. susun VO pada garis waktu babak + SFX sintetis + ambien kamar
  6. master ke `dist/KlikTahu_Ep56_audio.m4a` lewat `mesin_v20_audio`
     (-14 LUFS, TP -1,5, AAC 320k) — BUKAN WAV

Kenapa SFX di sini, bukan di renderer
-------------------------------------
Renderer hanya mengurus gambar. Semua bunyi (VO, SFX, ambien) dipra-mix jadi
satu berkas, sehingga video dan audio bisa dirender terpisah/paralel tanpa
risiko desinkron.

Pakai
-----
    python3 mesin_v20_suara.py --episode mesin_v20_ep56
    python3 mesin_v20_suara.py --episode mesin_v20_ep56 --tanpa-tts   # pakai WAV yang ada
    python3 mesin_v20_suara.py --episode mesin_v20_ep56 --cek         # cek dependensi saja
"""
from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import math
import os
import subprocess
import sys

import numpy as np

import mesin_v20_audio as A

BASE = os.path.dirname(os.path.abspath(__file__))
SR = A.SR
VOICE = os.environ.get("KT_VOICE", "id-ID-ArdiNeural")
RATE = os.environ.get("KT_RATE", "+6%")
PITCH = os.environ.get("KT_PITCH", "-2Hz")
PRA = 0.12
PASCA = 0.32
MIN_DUR = 4.6          # durasi minimum satu babak (supaya animasi tidak dipotong)
GAP = 0.22             # jeda antar babak
LEAD = 0.42            # jeda di awal video


# ============================================================== 1. TTS

def _edge_ok():
    try:
        import edge_tts  # noqa: F401
    except Exception:
        return False, "paket `edge-tts` belum terpasang (pip install edge-tts)"
    return True, "ok"


async def _tts_satu(teks, keluar_mp3):
    import edge_tts
    c = edge_tts.Communicate(teks, VOICE, rate=RATE, pitch=PITCH)
    await c.save(keluar_mp3)


def sintesis(naskah, folder, ulang=False):
    os.makedirs(folder, exist_ok=True)
    hasil = []
    for i, teks in enumerate(naskah, 1):
        mp3 = os.path.join(folder, f"{i:02d}.mp3")
        wav = os.path.join(folder, f"{i:02d}.wav")
        if ulang or not os.path.exists(wav):
            if not os.path.exists(mp3) or ulang:
                asyncio.run(_tts_satu(teks, mp3))
            A._run([A.FF, "-y", "-v", "error", "-i", mp3, "-ar", str(SR),
                    "-ac", "2", "-c:a", "pcm_s24le", wav])
        hasil.append(wav)
        print(f"  [{i:02d}] {os.path.getsize(wav) / 1024:6.0f} KB  {teks[:46]}...")
    return hasil


# ============================================================== 2. rapikan

def _rms_db(x, hop=240):
    n = len(x) // hop
    fr = x[:n * hop].reshape(n, hop)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-12)


def rapikan(path, ambang=-48.0):
    """Buang hening sejati + fade lembut. Panjang bicara TIDAK diubah."""
    x = A.baca_wav(path)
    mono = x.mean(1)
    db = _rms_db(mono)
    v = np.where(db > ambang)[0]
    hop = 240
    if len(v) == 0:
        return x, len(x) / SR
    a = max(0, int(v[0] * hop) - int(PRA * SR))
    b = min(len(x), int((v[-1] + 1) * hop) + int(PASCA * SR))
    y = x[a:b].copy()
    nf_in = min(len(y), int(0.030 * SR))
    nf_out = min(len(y), int(0.180 * SR))
    if nf_in:
        y[:nf_in] *= (0.5 - 0.5 * np.cos(np.linspace(0, math.pi, nf_in)))[:, None]
    if nf_out:
        y[-nf_out:] *= (0.5 + 0.5 * np.cos(np.linspace(0, math.pi, nf_out)))[:, None]
    return y, len(y) / SR


# ============================================================== 3. SFX

def _env(n, a=0.004, d=0.12, s=0.0, r=0.2, sr=SR):
    t = np.arange(n) / sr
    e = np.ones(n)
    na, nd = max(1, int(a * sr)), max(1, int(d * sr))
    e[:na] = np.linspace(0, 1, na)
    e[na:na + nd] *= np.linspace(1, s if s else 0.25, min(nd, max(0, n - na)))
    nr = max(1, int(r * sr))
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def sfx_bass(dur=0.55, f=52.0):
    """Dentuman rendah (impact) — untuk sentakan."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t * (1 - 0.35 * t / dur)) * np.exp(-t * 7.0)
    x += 0.4 * np.sin(2 * np.pi * f * 2.02 * t) * np.exp(-t * 11.0)
    sub = np.sin(2 * np.pi * 28 * t) * np.exp(-t * 5.0) * 0.5
    return (0.9 * (x + sub)).astype(np.float32)


def sfx_whoosh(dur=0.42, naik=True):
    """Sapuan angin (transisi) — derau yang disaring band-pass bergerak."""
    n = int(dur * SR)
    rng = np.random.default_rng(int(dur * 1000) % 9999)
    w = rng.normal(0, 1, n).astype(np.float32)
    # band-pass sederhana: beda dua lowpass satu kutub pada cutoff bergerak
    out = np.zeros(n, np.float32)
    lp1 = lp2 = 0.0
    for i in range(n):
        f = (400 + 6000 * (i / n)) if naik else (6000 - 5400 * (i / n))
        c = 1.0 - math.exp(-2 * math.pi * f / SR)
        lp1 += c * (w[i] - lp1)
        c2 = 1.0 - math.exp(-2 * math.pi * max(120.0, f * 0.32) / SR)
        lp2 += c2 * (lp1 - lp2)
        out[i] = lp1 - lp2
    e = np.sin(np.linspace(0, np.pi, n)) ** 1.6
    return (out * e * 0.5).astype(np.float32)


def sfx_tick(dur=0.10, f=2100.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 60) * 0.5).astype(np.float32)


def sfx_ding(dur=1.1, f=880.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t * 3.2) +
         0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 5.0) +
         0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 8.0))
    return (x * 0.4).astype(np.float32)


def sfx_riser(dur=1.6):
    """Riser halus sebelum babak penting (bukan musik: hanya tekstur)."""
    n = int(dur * SR)
    rng = np.random.default_rng(77)
    w = rng.normal(0, 1, n).astype(np.float32)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * (180 + 900 * (t / dur) ** 2) * t) * 0.25
    e = (t / dur) ** 2.2
    lp = 0.0
    out = np.zeros(n, np.float32)
    for i in range(n):
        c = 1.0 - math.exp(-2 * math.pi * (300 + 7000 * (i / n)) / SR)
        lp += c * (w[i] - lp)
        out[i] = lp
    out = out / (np.abs(out).max() + 1e-9)
    return ((out * 0.5 + tone) * e * 0.5).astype(np.float32)


def ambien_kamar(dur, sr=SR, kuat=1.0):
    """Ruangan malam: derau sangat rendah + dengung kulkas + napas jauh."""
    n = int(dur * sr)
    rng = np.random.default_rng(5)
    w = rng.normal(0, 1, n).astype(np.float32)
    # lowpass 6 kutub (derau coklat)
    x = w
    for _ in range(3):
        c = 1.0 - math.exp(-2 * math.pi * 180 / sr)
        y = np.empty_like(x)
        acc = 0.0
        for i in range(len(x)):
            acc += c * (x[i] - acc)
            y[i] = acc
        x = y
    x = x / (np.abs(x).max() + 1e-9)
    hum = 0.25 * np.sin(2 * np.pi * 50 * np.arange(n) / sr) * 0.05
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * np.arange(n) / sr)
    y = (x * 0.5 + hum) * lfo
    y = y / (np.abs(y).max() + 1e-9)
    return (y * 0.045 * kuat).astype(np.float32)


# ============================================================== 4. susun

def _taruh(buf, x, at, gain=1.0):
    """Tempel satu SFX ke buffer stereo (mono otomatis diduplikasi)."""
    i0 = int(at * SR)
    if i0 < 0 or i0 >= len(buf):
        return
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    n = min(len(x), len(buf) - i0)
    buf[i0:i0 + n] += x[:n] * gain


def bed_only(total, keluar_wav):
    """Bed audio desain (SFX + ambien) tanpa VO.

    Dipakai saat TTS tidak tersedia (sandbox tanpa jaringan): video tetap punya
    tata suara yang utuh, dan begitu VO tersedia cukup jalankan mode normal.
    Level sengaja -26 dBFS RMS supaya tidak menutupi VO saat digabung.
    """
    n = int(total * SR)
    buf = np.zeros((n, 2), np.float32)
    amb = ambien_kamar(total, kuat=1.0)
    buf[:, 0] += amb
    buf[:, 1] += amb
    rng = np.random.default_rng(9)
    # struktur: dentum di hook, sapuan tiap ~7,5 detik, denyut tiap 4 detik
    _taruh(buf, sfx_bass(), 4.2, 0.45)
    _taruh(buf, sfx_whoosh(0.5), 4.1, 0.25)
    t = 7.0
    i = 1
    while t < total - 1.0:
        _taruh(buf, sfx_whoosh(0.38), t - 0.1, 0.18)
        if i % 3 == 2:
            _taruh(buf, sfx_tick(0.08, 1600 + rng.integers(0, 900)), t + 0.6, 0.08)
        t += 7.4
        i += 1
    _taruh(buf, sfx_riser(1.5), total * 0.72, 0.16)
    _taruh(buf, sfx_ding(1.0), total - 4.0, 0.20)
    A.tulis_wav(keluar_wav, buf)
    return keluar_wav


def susun(klip, durasi, total, keluar, ambien=True):
    """Tempatkan VO + SFX pada garis waktu babak -> WAV stereo."""
    buf = np.zeros((int(total * SR) + SR, 2), np.float32)
    mulai = []
    t = LEAD
    for i, (y, d) in enumerate(zip(klip, durasi)):
        mulai.append(t)
        _taruh(buf, y if y.ndim > 1 else y[:, None], t, 1.0)
        t += max(MIN_DUR, d + GAP)
    total_vo = t

    sfx = np.zeros_like(buf)
    # dentuman pada sentakan di babak 1 (0,62 durasi babak)
    _taruh(sfx, sfx_bass(), mulai[0] + durasi[0] * 0.62, 0.55)
    _taruh(sfx, sfx_whoosh(0.5), mulai[0] + durasi[0] * 0.60, 0.30)
    # sapuan pada setiap cut
    for i in range(1, len(mulai)):
        _taruh(sfx, sfx_whoosh(0.38), mulai[i] - 0.12, 0.20)
    # denyut lembut di babak primata & teori
    _taruh(sfx, sfx_riser(1.4), mulai[5] - 0.8, 0.20)
    _taruh(sfx, sfx_riser(1.2), mulai[8] - 0.7, 0.16)
    # klik kecil saat angka piktogram muncul di babak 3
    for j in range(7):
        _taruh(sfx, sfx_tick(0.06, 1800 + j * 120), mulai[2] + 0.9 + j * 0.07, 0.10)
    # ding di babak kesimpulan
    _taruh(sfx, sfx_ding(0.9), mulai[9] + 0.5, 0.22)
    # ambien sepanjang video (sangat pelan, di bawah VO 25 dB)
    if ambien:
        amb = ambien_kamar(total)
        sfx[:, 0] += amb
        sfx[:, 1] += amb
    campur = buf + sfx
    campur = campur[:int(total * SR)]
    A.tulis_wav(keluar, campur)
    return mulai, total


# ============================================================== 5. utama

def jalankan(modul_nama, tanpa_tts=False, ulang=False, keluar_m4a=None):
    mod = importlib.import_module(modul_nama)
    naskah = list(mod.NASKAH)
    folder = os.path.join(BASE, "audio", "vo")
    os.makedirs(folder, exist_ok=True)
    print(f"[episode] {modul_nama}: {len(naskah)} babak")

    if tanpa_tts:
        klip_path = [os.path.join(folder, f"{i:02d}.wav") for i in range(1, len(naskah) + 1)]
        hilang = [p for p in klip_path if not os.path.exists(p)]
        if hilang:
            print("[GAGAL] WAV VO tidak lengkap:", ", ".join(os.path.basename(h) for h in hilang))
            return 3
    else:
        ok, pesan = _edge_ok()
        if not ok:
            print(f"[GAGAL] {pesan}")
            print("        Jalankan `pip install edge-tts`, lalu ulangi.")
            return 3
        klip_path = sintesis(naskah, folder, ulang)

    klip, durasi = [], []
    for p in klip_path:
        y, d = rapikan(p)
        klip.append(y)
        durasi.append(d)
        print(f"  rapikan {os.path.basename(p)}  {d:5.2f} s")

    total = max(LEAD + sum(max(MIN_DUR, d + GAP) for d in durasi), sum(durasi) + LEAD)
    timing = {"dur": [round(max(MIN_DUR, d + GAP), 3) for d in durasi],
              "vo": [round(d, 3) for d in durasi],
              "lead": LEAD, "total": round(total, 3)}
    with open(os.path.join(folder, "timing.json"), "w") as f:
        json.dump(timing, f, indent=1)
    print(f"[timing] total {total:.2f} s -> audio/vo/timing.json")

    wav_mix = os.path.join(folder, "campuran.wav")
    mulai, total2 = susun(klip, durasi, total, wav_mix)
    print(f"[campur] {wav_mix}  {total2:.2f} s  VO mulai: " +
          ", ".join(f"{m:.2f}" for m in mulai))

    out = keluar_m4a or os.path.join(BASE, "dist", "KlikTahu_Ep56_audio.m4a")
    lap = A.master(wav_mix, out)
    with open(os.path.join(folder, "master.json"), "w") as f:
        json.dump(lap, f, indent=1, ensure_ascii=False)
    return 0 if lap.get("lulus") else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default="mesin_v20_ep56")
    ap.add_argument("--tanpa-tts", action="store_true")
    ap.add_argument("--ulang", action="store_true")
    ap.add_argument("--keluar")
    ap.add_argument("--cek", action="store_true")
    ap.add_argument("--bed-only", action="store_true",
                    help="hanya SFX + ambien (dipakai bila TTS belum tersedia)")
    ap.add_argument("--target-lufs", type=float, default=-14.0)
    a = ap.parse_args(argv)
    if a.bed_only:
        mod = importlib.import_module(a.episode)
        total = float(mod.daftar()["total"])
        wav = os.path.join(BASE, "audio", "vo", "bed.wav")
        os.makedirs(os.path.dirname(wav), exist_ok=True)
        bed_only(total, wav)
        print(f"[bed] {wav}  {total:.2f} s")
        A.TARGET_I = a.target_lufs
        lap = A.master(wav, a.keluar or os.path.join(BASE, "dist", "KlikTahu_Ep56_audio.m4a"))
        with open(os.path.join(BASE, "audio", "vo", "master.json"), "w") as f:
            json.dump(lap, f, indent=1, ensure_ascii=False)
        return 0 if lap.get("lulus") else 1
    if a.cek:
        ok, pesan = _edge_ok()
        print("edge-tts:", "siap" if ok else f"TIDAK SIAP ({pesan})")
        print("ffmpeg :", A.FF)
        print("suara  :", VOICE, RATE, PITCH)
        return 0 if ok else 3
    return jalankan(a.episode, a.tanpa_tts, a.ulang, a.keluar)


if __name__ == "__main__":
    sys.exit(main())
