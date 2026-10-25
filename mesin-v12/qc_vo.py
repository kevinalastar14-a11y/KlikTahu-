#!/usr/bin/env python3
"""qc_vo.py — pemeriksaan audio VO (bahasa Indonesia) sebelum video dirender.

Masalah yang dijaga (semuanya pernah terjadi / berisiko pada TTS per babak):

  1. klip kurang / lebih dari jumlah babak
  2. klip terpotong di tengah kata (tepi klip tidak sunyi)
  3. ada lubang hening panjang di tengah kalimat (dropout / sintesis gagal)
  4. klip tanpa suara sama sekali (TTS mengembalikan hening)
  5. VO tidak terdengar di salah satu babak pada campuran akhir
  6. VO bertumpuk ke babak berikutnya (tidak ada jeda)
  7. campuran clipping sebelum encode
  8. master meleset dari target loudness / true peak
  9. durasi master tidak sama dengan timeline video (video jadi sepi di ekor)

Pakai:
    python3 qc_vo.py --episode mesin_v20_ep56 --sumber audio/vo/sumber \\
            --audio keluaran/KlikTahu_Ep56_audio.m4a --timing audio/vo/timing.json
    python3 qc_vo.py --episode mesin_v20_ep56 --sumber audio/vo/sumber_kilat \\
            --audio keluaran/KlikTahu_Ep56_audio_kilat.m4a \\
            --timing audio/vo_kilat/timing.json --json /tmp/qc_vo_kilat.json
"""
from __future__ import annotations

import argparse
import glob
import importlib
import json
import os
import subprocess
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import mesin_v20_audio as A
import mesin_v20_suara as S

SR = A.SR


# ------------------------------------------------------------------ util

def _mono(path):
    x = A.baca_wav(path)
    return x, x.mean(1)


def _db(y):
    return 20 * np.log10(np.sqrt((y.astype(np.float64) ** 2).mean()) + 1e-12)


def _bingkai(m, detik=0.01):
    hop = max(1, int(detik * SR))
    n = len(m) // hop
    if n == 0:
        return np.zeros(1), hop
    e = np.sqrt((m[: n * hop].reshape(n, hop).astype(np.float64) ** 2).mean(1) + 1e-12)
    return 20 * np.log10(e + 1e-9), hop


HASIL = []


def cek(nama, ok, nilai):
    HASIL.append((nama, bool(ok), nilai))
    print(f"  [{'OK ' if ok else '!! '}] {nama:44s} {str(nilai)[:46]}")


# ------------------------------------------------------------------ utama

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default="mesin_v20_ep56")
    ap.add_argument("--sumber", default=os.path.join(BASE, "audio", "vo", "sumber"))
    ap.add_argument("--audio", default=os.path.join(BASE, "keluaran", "KlikTahu_Ep56_audio.m4a"))
    ap.add_argument("--timing", default=os.path.join(BASE, "audio", "vo", "timing.json"))
    ap.add_argument("--target-lufs", type=float, default=-14.0)
    ap.add_argument("--json")
    a = ap.parse_args(argv)

    mod = importlib.import_module(a.episode)
    naskah = list(mod.NASKAH)
    print(f"== QC VO {os.path.basename(a.episode)} ({len(naskah)} babak) ==")

    ext = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")
    berkas = sorted(p for p in glob.glob(os.path.join(a.sumber, "*"))
                    if p.lower().endswith(ext))
    cek("klip sesuai jumlah babak", len(berkas) == len(naskah),
        f"{len(berkas)} berkas / {len(naskah)} babak")
    if len(berkas) != len(naskah):
        return _tutup(a, None)

    # ---- per klip
    teks_masalah, tepi_buruk, bolong, bisu, durasi, durasi_vo = [], [], [], [], [], []
    for i, p in enumerate(berkas, 1):
        x, m = _mono(p)
        d = len(m) / SR
        durasi.append(d)
        # panjang yang MASUK ke timeline = hasil rapikan() (hening dibuang),
        # bukan panjang berkas mentah — berkas mentah selalu lebih panjang
        # karena hening 0,1-0,4 s di kedua ujung.
        durasi_vo.append(S.rapikan(p)[1])
        db, hop = _bingkai(m)
        bicara = db[db > -45]
        med = float(np.median(bicara)) if bicara.size else -100.0
        kepala, ekor = _db(m[: int(0.08 * SR)]), _db(m[-int(0.08 * SR):])
        if med < -45:
            bisu.append(i)
        if kepala > -45 or ekor > -45:
            tepi_buruk.append(f"{i:02d}({kepala:.0f}/{ekor:.0f} dB)")
        # lubang hening > 1,2 s di tengah klip
        uc = db > (med - 22)
        j, panjang = 0, None
        while j < len(uc):
            if not uc[j]:
                k = j
                while k < len(uc) and not uc[k]:
                    k += 1
                if (k - j) * hop / SR > 1.2 and 0 < j and k < len(uc):
                    panjang = round((k - j) * hop / SR, 2)
                j = k
            else:
                j += 1
        if panjang:
            bolong.append(f"{i:02d}:{panjang}s")
        if not (4.0 <= d <= 12.0):
            teks_masalah.append(f"{i:02d}:{d:.1f}s")

    cek("tidak ada klip bisu", not bisu, "semua berbunyi" if not bisu else f"bisu: {bisu}")
    cek("tepi klip sunyi (tidak terpotong)", not tepi_buruk,
        "kepala & ekor < -45 dBFS" if not tepi_buruk else ", ".join(tepi_buruk))
    cek("tidak ada lubang hening > 1,2 s", not bolong,
        "jeda hanya antar-kalimat" if not bolong else ", ".join(bolong))
    cek("durasi klip wajar (4-12 s)", not teks_masalah,
        f"{min(durasi):.2f}-{max(durasi):.2f} s" if not teks_masalah else ", ".join(teks_masalah))

    # ---- timing
    if not os.path.exists(a.timing):
        cek("timing.json ada", False, a.timing)
        return _tutup(a, None)
    t = json.load(open(a.timing))
    dur = [float(v) for v in t["dur"]]
    lead = float(t.get("lead", 0.0))
    total = float(t["total"])
    cek("timing sesuai jumlah babak", len(dur) == len(naskah), f"{len(dur)} durasi")
    pendek = [f"{i + 1:02d}(babak {d:.2f} < VO {v:.2f})"
              for i, (d, v) in enumerate(zip(dur, durasi_vo)) if v > d + 0.02]
    cek("VO muat di babaknya (tidak terpotong)", not pendek,
        "setiap babak >= panjang VO" if not pendek else ", ".join(pendek))

    mulai, ak = [], lead
    for d in dur:
        mulai.append(round(ak, 3))
        ak += d
    cek("timeline konsisten", abs(mulai[-1] + dur[-1] - total) < 0.02,
        f"total {total:.2f} s · VO mulai {mulai[0]:.2f} s")

    # ---- master
    if not os.path.exists(a.audio):
        cek("berkas audio ada", False, a.audio)
        return _tutup(a, None)
    x, m = _mono(a.audio)
    dm = len(m) / SR
    cek("durasi audio = timeline video", abs(dm - total) <= 0.08,
        f"{dm:.2f} s vs {total:.2f} s")
    puncak = float(np.abs(x).max())
    cek("tidak clipping", puncak < 0.985, f"puncak {20 * np.log10(puncak + 1e-9):.2f} dBFS")

    # VO terdengar di setiap babak: jendela 0,4-2,6 s setelah mulai masih di dalam VO
    hilang = []
    for i, (ms, vd) in enumerate(zip(mulai, durasi_vo)):
        w0 = int((ms + 0.35) * SR)
        w1 = int((ms + min(vd - 0.05, 2.4)) * SR)
        seg = m[w0:w1]
        if seg.size == 0 or _db(seg) < -34:
            hilang.append(f"{i + 1:02d}({_db(seg):.0f} dB)")
    cek("VO terdengar di semua babak", not hilang,
        "semua babak > -34 dBFS" if not hilang else ", ".join(hilang))

    # ---- fase & mono: kesalahan saturasi (axis=-1) pernah membuat kanal
    # berkorelasi -1,0 sehingga audio nyaris hilang di speaker ponsel.
    k = float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]) if x[:, 0].std() > 1e-6 else 1.0
    mono = m
    selisih = _db(x) - _db(mono)
    cek("kanal sefase (tidak saling hapus)", k > 0.9, f"korelasi {k:+.3f}")
    cek("mono-sum tidak kehilangan level", abs(selisih) < 1.0, f"selisih {selisih:+.2f} dB")

    lufs, tp, lra = A.ukur(a.audio)          # ukur() -> (LUFS, true peak, LRA)
    cek("loudness sesuai target", abs(lufs - a.target_lufs) <= 0.6, f"{lufs:.1f} LUFS")
    cek("true peak aman", tp <= -1.4, f"{tp:.1f} dBTP")
    cek("format master", dm > 0,
        f"{len(x) / dm / 1000:.1f} kHz · {x.shape[1]} ch · {os.path.getsize(a.audio) / 1e6:.2f} MB")

    return _tutup(a, {"durasi": [round(d, 3) for d in durasi_vo],
                      "durasi_berkas": [round(d, 3) for d in durasi], "total": total,
                      "lufs": lufs, "tp": tp, "mulai": mulai})


def _tutup(a, ekstra):
    lulus = sum(1 for _, ok, _ in HASIL if ok)
    print(f"\nQC VO: {lulus}/{len(HASIL)} lulus")
    if a.json:
        with open(a.json, "w") as f:
            json.dump({"lulus": lulus, "total": len(HASIL),
                       "butir": [{"nama": n, "lulus": ok, "nilai": str(v)}
                                 for n, ok, v in HASIL], **(ekstra or {})}, f, indent=1)
        print(f"-> {a.json}")
    return 0 if lulus == len(HASIL) else 1


if __name__ == "__main__":
    sys.exit(main())
