#!/usr/bin/env python3
"""mesin_v21_vo_rapi.py — penjaga konsistensi NADA VO antar-babak.

Masalah yang diperbaiki
-----------------------
Keluhan pemilik: "VO tiba-tiba berganti suaranya, dari biasa saja ke suara dalam".
Penyebabnya bukan timbre (forman F1/F2/F3 antar babak hampir identik) melainkan
**register nada dasar yang bergeser**. Dengan alat ukur yang sudah lulus uji
(lihat "Alat ukur" di bawah), VO Ep58 lama terukur:

    146,7 Hz (babak 4) ... 188,2 Hz (babak 7)  =  4,32 semitone

Empat semitone lebih tinggi/rendah pada pembicara yang sama, didengar sebagai
"orang lain" — persis keluhan itu.

Alat ukur (dan kenapa bukan yang pertama)
-----------------------------------------
Dua estimator sebelumnya GAGAL uji kontrol dan sudah dibuang:

  1. YIN dengan ambang CMND 0,15 — galat sampai +1,9 semitone pada klip yang
     sama setelah di-re-encode mp3.
  2. Cepstrum pada log-spektrum — pada suara nyata puncak kepsrum hampir rata
     (0,074 vs 0,096), sehingga argmax melompat antar-quefrency dan hasilnya
     "diam" walau klip digeser 3 semitone.

Yang dipakai sekarang: **autokorelasi ternormalisasi pada sinyal yang
di-bandpass 70-420 Hz, hanya pada frame vokal (energi >= median), dengan
koreksi oktaf**. Diuji dengan kontrol kebenaran yang tidak bisa dibantah
(`asetrate` menggeser nada dengan rasio pasti, bukan perkiraan):

    kontrol +2,00 st -> terukur +2,00 st
    kontrol -2,00 st -> terukur -1,85 st
    kontrol +1,00 st -> terukur +0,97 st

Jebakan yang sempat menipu: berkas TTS adalah **24 kHz**, bukan 44,1 kHz.
`asetrate=44100*r` pada berkas 24 kHz menggeser nada 2,06x (bukan r), dan
percobaan pertama tampak "gagal" padahal alat ukurnya benar.

Koreksi loop tertutup
---------------------
Geseran dihitung, diterapkan, lalu **diukur ulang**; kalau sisa galat > 0,1
semitone, digeser lagi (maks 3 putaran). Yang penting bukan akurasi absolut
alat ukur, tetapi bahwa semua klip berakhir pada NILAI TERUKUR yang sama —
itulah yang membuat pendengar mendengar satu suara.

Batas total geser ±4 semitone (rubberband + formant=preserved masih bersih).
Klip yang butuh lebih dari itu ditandai agar dibuat ulang, bukan dipaksa.

Status penggeseran nada (penting)
--------------------------------
Koreksi nada BELUM dipakai untuk produksi. Estimator yang dipakai di sini lulus
kontrol pada klip 01, 03, 06, 08 tetapi GAGAL pada 02, 04, 05, 07, 09 (kontrol
`asetrate` ±2 st tidak kembali ±2 st). Artinya alat ukur ini belum layak dipakai
untuk menggeser suara: memaksakannya berarti menebak. Modul ini karena itu
dijalankan sebagai **pengukur + montase** (untuk memeriksa konsistensi dengan
telinga), dan `--geser` tidak dipakai sampai kontrol lulus di semua klip.

Penyebab keluhan "suara berganti" yang terbukti: VO edisi lama dirakit dari
beberapa sesi/suara berbeda (setiap audisi menghasilkan suara baru). Perbaikannya
struktural: SATU suara, SATU sesi, sembilan klip — bukan penambalan filter.

Pakai
-----
    python3 mesin_v21_vo_rapi.py --sumber audio/vo60/sumber --keluar audio/vo60/rapi
    python3 mesin_v21_vo_rapi.py --sumber audio/vo60/sumber --keluar /tmp/x --uji
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

SR = 16000          # cukup untuk F0 65-350 Hz
FMIN, FMAX = 65.0, 350.0
BATAS_ST = 4.0      # total geser maksimum per klip (semitone)
TOLERANSI = 0.10    # sisa galat yang diterima (semitone)
EXT = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")


def ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


FF = ffmpeg()


# =============================================================== 1. alat ukur
def baca(path: str) -> np.ndarray:
    """Dekode apa pun -> mono float32 @ SR."""
    pr = subprocess.run([FF, "-v", "error", "-i", path, "-f", "f32le",
                         "-ac", "1", "-ar", str(SR), "-"], capture_output=True)
    if pr.returncode != 0 or not pr.stdout:
        raise RuntimeError(f"gagal mendekode {path}: {pr.stderr[-300:]!r}")
    return np.frombuffer(pr.stdout, np.float32).copy()


def _bandpass(y: np.ndarray, lo=70.0, hi=420.0) -> np.ndarray:
    """Sisakan pita nada dasar; forman dibuang supaya autokorelasi bersih."""
    S = np.fft.rfft(y)
    f = np.fft.rfftfreq(len(y), 1 / SR)
    m = ((f >= lo) & (f <= hi)).astype(np.float32)
    m = np.convolve(m, np.ones(9) / 9.0, mode="same")   # tepi landai, tanpa dering
    return np.fft.irfft(S * m, len(y)).astype(np.float32)


def f0_klip(y: np.ndarray, N=1024, hop=256, rmin=0.55) -> np.ndarray:
    """F0 per frame (autokorelasi ternormalisasi + koreksi oktaf)."""
    y = _bandpass(y)
    lo, hi = max(2, int(SR / FMAX)), min(int(SR / FMIN), N // 2 - 1)
    frame = []
    for i in range(0, max(1, len(y) - N), hop):
        x = y[i:i + N]
        e = float(np.sqrt((x ** 2).mean()))
        if e >= 0.004:
            frame.append((e, x))
    if not frame:
        return np.empty(0)
    amb = float(np.median([e for e, _ in frame]))
    out = []
    for e, x in frame:
        if e < amb:                     # hanya vokal keras (bukan desis/napas)
            continue
        x = x - x.mean()
        ac = np.correlate(x, x, "full")[N - 1:]
        ac = ac / (ac[0] + 1e-12)
        seg = ac[lo:hi]
        k = int(np.argmax(seg))
        best = float(seg[k])
        if best < rmin:
            continue
        for j in range(0, k + 1):       # hindari 2x / 3x periode
            if seg[j] >= 0.88 * best:
                k = j
                break
        tau = lo + k
        a, b, c = ac[tau - 1], ac[tau], ac[tau + 1]
        tau = tau + 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
        out.append(SR / tau)
    return np.array(out)


def f0_median(y: np.ndarray) -> float:
    f = f0_klip(y)
    if not len(f):
        raise RuntimeError("klip tanpa bagian bersuara")
    return float(np.median(f))


# =============================================================== 2. penggeser
def ada_rubberband() -> bool:
    pr = subprocess.run([FF, "-hide_banner", "-filters"], capture_output=True, text=True)
    return "rubberband" in pr.stdout


def geser_nada(masuk: str, keluar: str, semitone: float):
    """Geser nada; forman dipertahankan, durasi tetap. Keluaran WAV 48 kHz."""
    rasio = 2.0 ** (semitone / 12.0)
    af = (f"rubberband=pitch={rasio:.6f}:formant=preserved:"
          f"transients=smooth:pitchq=quality,aresample=48000")
    pr = subprocess.run([FF, "-y", "-v", "error", "-i", masuk, "-af", af,
                         "-c:a", "pcm_s24le", keluar], capture_output=True, text=True)
    if pr.returncode != 0:
        raise RuntimeError(pr.stderr[-400:])
    return keluar


def durasi_s(path: str) -> float:
    pr = subprocess.run([FF, "-v", "error", "-i", path, "-f", "null", "-"],
                        capture_output=True, text=True)
    return 0.0


# =============================================================== 3. alur utama
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sumber", required=True)
    ap.add_argument("--keluar", required=True)
    ap.add_argument("--uji", action="store_true", help="ukur saja, tidak menulis berkas")
    ap.add_argument("--geser", action="store_true",
                    help="(jangan dipakai dulu) terapkan koreksi nada; lihat catatan "
                         "di docstring: estimator masih gagal kontrol pada 5/9 klip")
    a = ap.parse_args(argv)

    if a.geser and not a.uji and not ada_rubberband():
        print("[GAGAL] ffmpeg tanpa filter `rubberband`; penjagaan nada tidak bisa "
              "dijalankan. Pasang ffmpeg dengan librubberband.")
        return 4

    berkas = sorted(f for f in os.listdir(a.sumber) if f.lower().endswith(EXT))
    if not berkas:
        print(f"[GAGAL] tidak ada klip audio di {a.sumber}")
        return 3

    y = {f: baca(os.path.join(a.sumber, f)) for f in berkas}
    f0 = {f: f0_median(v) for f, v in y.items()}
    target = float(np.median(list(f0.values())))
    print(f"[vo] {len(berkas)} klip · target nada (median) {target:.1f} Hz")
    print(f"{'klip':10} {'F0 awal':>8} {'st awal':>8} {'total':>7} {'F0 akhir':>9} {'sisa':>6}")

    os.makedirs(a.keluar, exist_ok=True)
    laporan = {"target_hz": round(target, 2), "batas_st": BATAS_ST, "klip": {}}
    perlu_ulang = []
    for f in berkas:
        asal = os.path.join(a.sumber, f)
        nama = os.path.splitext(f)[0] + ".wav"
        keluar = os.path.join(a.keluar, nama)
        awal = f0[f]
        total = 0.0
        akhir = awal
        if a.uji or not a.geser:
            total = 12 * np.log2(target / awal)
        else:
            # loop tertutup: geser -> ukur -> koreksi sisa, maks 3 putaran
            kerja = asal
            for putaran in range(3):
                st = 12 * np.log2(target / akhir)
                if abs(st) <= TOLERANSI:
                    break
                if abs(total + st) > BATAS_ST:
                    st = float(np.sign(st) * max(0.0, BATAS_ST - abs(total)))
                    if abs(st) <= TOLERANSI:
                        break
                tmp = keluar if putaran == 0 else keluar + ".tmp.wav"
                geser_nada(kerja, tmp, st)
                if putaran > 0:
                    os.replace(tmp, keluar)
                kerja = keluar
                total += st
                akhir = f0_median(baca(keluar))
        sisa = 12 * np.log2(target / akhir)
        if abs(sisa) > 0.35:
            perlu_ulang.append(f)
        laporan["klip"][f] = {"f0_awal": round(awal, 2), "geser_st": round(total, 2),
                              "f0_akhir": round(akhir, 2), "sisa_st": round(sisa, 2)}
        print(f"{f:10} {awal:8.1f} {12*np.log2(awal/target):+8.2f} {total:+7.2f} "
              f"{akhir:9.1f} {sisa:+6.2f}")

    akhir_semua = [v["f0_akhir"] for v in laporan["klip"].values()]
    sebar = 12 * np.log2(max(akhir_semua) / min(akhir_semua))
    awal_semua = [v["f0_awal"] for v in laporan["klip"].values()]
    sebar0 = 12 * np.log2(max(awal_semua) / min(awal_semua))
    laporan["sebaran_st_awal"] = round(float(sebar0), 2)
    laporan["sebaran_st_akhir"] = round(float(sebar), 2)
    print(f"[vo] sebaran nada: {sebar0:.2f} st -> {sebar:.2f} st "
          f"({min(akhir_semua):.1f}-{max(akhir_semua):.1f} Hz)")
    if perlu_ulang:
        print(f"[vo] PERHATIAN: {', '.join(perlu_ulang)} menyimpang > 0,35 st, "
              f"pertimbangkan membuat ulang klip itu")
    if not a.uji:
        with open(os.path.join(a.keluar, "nada.json"), "w") as fh:
            json.dump(laporan, fh, indent=1, ensure_ascii=False)
    return 0 if not perlu_ulang else 1


if __name__ == "__main__":
    raise SystemExit(main())
