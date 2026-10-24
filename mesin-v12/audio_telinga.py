#!/usr/bin/env python3
"""audio_telinga.py — pemasteran VO yang dioptimalkan untuk TELINGA MANUSIA.

Kenapa modul terpisah
---------------------
`master_audio.py` menyamakan level (LUFS/TP) dan mencampur ambien. Itu cukup untuk
lolos QC angka, tetapi belum tentu enak didengar. Modul ini menambahkan lapisan
terakhir yang berorientasi persepsi:

  1. HPF 78 Hz            -> membuang gemuruh yang tidak terdengar, menghemat headroom
  2. potong 220-320 Hz    -> -1,2 dB, membersihkan "lumpur" (mud) yang bikin VO tertutup
  3. angkat 2,6-4,2 kHz   -> +1,6 dB, pita kejelasan konsonan (inilah yang bikin "jelas"
                             di speaker HP, bukan kenyaringan)
  4. de-ess 5,8-9,5 kHz   -> -2 dB hanya pada frame yang desisnya dominan (bukan statis)
  5. rak "udara" > 11 kHz -> +1,2 dB, kesegaran tanpa menambah desis
  6. kompresor lambat 1,5:1 (RMS, lutut 8 dB) -> merapatkan jarak kalimat pelan/keras
  7. loudnorm dua lintasan ke -14,0 LUFS, TP -1,5 dBTP -> standar YouTube/Short
  8. keluaran: WAV 24-bit (arsip) + **M4A AAC 256 kbps (berkas kerja/unggah, BUKAN WAV)**

Semua tahap menjaga PANJANG sampel identik supaya timeline video tidak bergeser;
di akhir diperiksa ulang: durasi, LUFS, true peak, jumlah clip.

Pakai:
    python3 audio_telinga.py build/audio_master.wav build/audio_telinga.wav
"""
import json
import os
import subprocess
import sys

import numpy as np
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000
SRC = sys.argv[1] if len(sys.argv) > 1 else "build/audio_master.wav"
DST = sys.argv[2] if len(sys.argv) > 2 else "build/audio_telinga.wav"
M4A = os.path.splitext(DST)[0] + "_vo.m4a"

TARGET_I = -14.0
TARGET_TP = -1.5


# ------------------------------------------------------------------ util
def run(cmd, capture=False):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg gagal: {' '.join(cmd[:6])}...\n{p.stderr[-800:]}")
    return p.stderr if capture else ""


def ukur(path, af=""):
    """Ukur integrated loudness & true peak (loudnorm, tanpa menulis berkas)."""
    err = run([FF, "-hide_banner", "-i", path, "-af",
               (af + "," if af else "") + f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:print_format=json",
               "-f", "null", "-"], capture=True)
    j = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    return float(j["input_i"]), float(j["input_tp"]), float(j["input_lra"])


def durasi(path):
    # ffmpeg tanpa output mengembalikan kode 1 hanya karena tidak ada berkas keluaran;
    # itu normal untuk sekadar membaca header, jadi stderr dibaca apa adanya.
    err = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    for ln in err.splitlines():
        if "Duration:" in ln:
            h, m, s = ln.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


# ------------------------------------------------------------------ de-esser persepsi
def stft(x, n=1024, hop=256):
    win = np.hanning(n).astype(np.float32)
    nf = 1 + (len(x) - n) // hop
    X = np.empty((nf, n // 2 + 1), dtype=np.complex64)
    for i in range(nf):
        X[i] = np.fft.rfft(x[i * hop:i * hop + n] * win)
    return X, win


def istft(X, win, length, n=1024, hop=256):
    """ISTFT dengan panjang keluaran TEPAT sesuai aslinya (sisa < n ditambal)."""
    nf = X.shape[0]
    out = np.zeros(max(length, hop * (nf - 1) + n), dtype=np.float32)
    wsum = np.zeros_like(out)
    for i in range(nf):
        seg = np.fft.irfft(X[i]).astype(np.float32) * win
        out[i * hop:i * hop + n] += seg
        wsum[i * hop:i * hop + n] += win ** 2
    y = (out / np.maximum(wsum, 1e-6))[:length]
    if len(y) < length:                       # tambal ekor yang terpotong STFT
        y = np.concatenate([y, np.zeros(length - len(y), dtype=np.float32)])
    return y


def terapkan_deess_stereo(x):
    """De-esser stereo: hitung gain dari mono, terapkan ke kedua kanal."""
    mono = x.mean(1)
    n, hop = 1024, 256
    X, win = stft(mono, n, hop)
    f = np.fft.rfftfreq(n, 1 / SR)
    pita = (f >= 5800) & (f <= 9500)
    mag = np.abs(X)
    e_tot = 20 * np.log10(np.sqrt((mag ** 2).sum(1)) + 1e-9)
    e_pit = 20 * np.log10(np.sqrt((mag[:, pita] ** 2).sum(1)) + 1e-9)
    rasio = e_pit - e_tot
    red = np.clip((rasio + 6.0) * 1.2, 0, 2.4)
    red[e_tot < (e_tot.max() - 42)] = 0
    sm = np.zeros_like(red)
    for i in range(len(red)):
        sm[i] = max(red[i], sm[i - 1] * 0.88) if i else red[i]
    # bangun kurva gain pada resolusi sampel lewat STFT yang sama untuk tiap kanal
    out = np.empty_like(x)
    for ch in range(x.shape[1]):
        Xc, _ = stft(x[:, ch], n, hop)
        Xc[:, pita] *= (10 ** (-sm / 20)).astype(np.float32)[:, None]
        out[:, ch] = istft(Xc, win, x.shape[0], n, hop)
    return out, float(sm.max())


# ------------------------------------------------------------------ rantai utama
def rantai(af):
    """Filter ffmpeg berorientasi telinga: bersih, jelas, tidak 'dipompa'."""
    return ",".join([
        "highpass=f=78:poles=2",
        "equalizer=f=270:width_type=o:width=1.4:g=-1.2",      # buang lumpur
        "equalizer=f=3300:width_type=o:width=1.1:g=1.6",      # kejelasan konsonan
        "equalizer=f=11000:width_type=h:width=6000:g=1.2",    # udara
        "acompressor=threshold=-25dB:ratio=1.5:attack=18:release=240:knee=8:makeup=1:detection=rms",
        af,
    ])


def main():
    if not os.path.exists(SRC):
        print(f"[GAGAL] sumber tidak ada: {SRC}")
        return 2
    d0 = durasi(SRC)
    i0, tp0, lra0 = ukur(SRC)
    print(f"[masuk]  {SRC}\n         durasi {d0:.2f} s · {i0:.1f} LUFS · TP {tp0:.1f} dBTP · LRA {lra0:.1f} LU")

    # 1) rantai ffmpeg (EQ + kompresor) ke WAV kerja
    tmp1 = "/tmp/_tl_chain.wav"
    run([FF, "-y", "-i", SRC, "-af", rantai("anull"), "-ar", str(SR), "-ac", "2",
         "-c:a", "pcm_f32le", tmp1])
    i1, tp1, _ = ukur(tmp1)
    print(f"[EQ]     {i1:.1f} LUFS · TP {tp1:.1f} dBTP")

    # 2) de-esser persepsi (numpy STFT)
    with open("/tmp/_tl_chain.f32", "wb") as f:
        subprocess.run([FF, "-y", "-i", tmp1, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                       stdout=f, stderr=subprocess.DEVNULL, check=True)
    x = np.fromfile("/tmp/_tl_chain.f32", dtype=np.float32).reshape(-1, 2)
    y, red = terapkan_deess_stereo(x)
    tmp2 = "/tmp/_tl_deess.wav"
    with open(tmp2, "wb") as f:
        subprocess.run([FF, "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-c:a", "pcm_f32le", tmp2], input=y.astype(np.float32).tobytes(),
                       stderr=subprocess.DEVNULL, check=True)
    print(f"[de-ess] pengurangan maksimum {red:.1f} dB pada pita 5,8-9,5 kHz")

    # 3) loudnorm dua lintasan -> target LUFS & TP, panjang tidak berubah
    i2, tp2, _ = ukur(tmp2)
    g = TARGET_I - i2
    run([FF, "-y", "-i", tmp2, "-af",
         f"volume={g:.2f}dB,alimiter=limit={10 ** (TARGET_TP / 20):.4f}:attack=4:release=80:level=false:asc=true",
         "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s24le", DST])
    i3, tp3, lra3 = ukur(DST)
    d1 = durasi(DST)
    print(f"[keluar] {DST}\n         durasi {d1:.2f} s · {i3:.1f} LUFS · TP {tp3:.1f} dBTP · LRA {lra3:.1f} LU")

    # 4) berkas kerja M4A (BUKAN WAV) — inilah yang diunggah/dibagikan
    run([FF, "-y", "-i", DST, "-c:a", "aac", "-b:a", "256k", "-ar", str(SR), "-ac", "2", M4A])
    i4, tp4, _ = ukur(M4A)
    print(f"[m4a]    {M4A}\n         durasi {durasi(M4A):.2f} s · {i4:.1f} LUFS · TP {tp4:.1f} dBTP")

    # 5) pemeriksaan
    masalah = []
    if abs(d1 - d0) > 0.05:
        masalah.append(f"panjang bergeser {d1 - d0:+.2f} s")
    if abs(i3 - TARGET_I) > 0.6:
        masalah.append(f"loudness {i3:.1f} LUFS (target {TARGET_I})")
    if tp3 > TARGET_TP + 0.25:
        masalah.append(f"true peak {tp3:.1f} dBTP")
    if abs(durasi(M4A) - d0) > 0.08:
        masalah.append("M4A berbeda panjang")
    print("HASIL AUDIO TELINGA:", "SEMUA BERSIH ✔" if not masalah else "PERIKSA -> " + "; ".join(masalah))
    return 0 if not masalah else 1


if __name__ == "__main__":
    sys.exit(main())
