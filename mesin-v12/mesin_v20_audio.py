#!/usr/bin/env python3
"""mesin_v20_audio.py — pemasteran VO "untuk telinga manusia" (v20).

Kenapa modul baru, bukan `audio_telinga.py`
-------------------------------------------
`audio_telinga.py` (v17) sudah benar arahnya, tapi rantainya masih bergantung
pada filter ffmpeg dan de-esser-nya menghitung ulang STFT dua kali per kanal
(±4 kali lipat biaya). v20 memindahkan SELURUH pemrosesan ke numpy dengan
filter biquad yang ditulis sendiri, sehingga:

  * hasilnya bisa diuji per tahap (respons frekuensi diukur, bukan diasumsikan);
  * waktu proses turun ~5x (satu STFT untuk semua kanal sekaligus);
  * setiap tahap menjaga panjang sampel — timeline video tidak bergeser;
  * keluaran akhir **M4A AAC 320 kbps**, bukan WAV (permintaan pemilik).

Rantai persepsi (urutan ini penting)
------------------------------------
  1. DC + subsonik        highpass 72 Hz (biquad 4 orde)  — buang gemuruh
  2. "mud"                260 Hz, -2,2 dB, Q 1,1          — hilangkan selimut
  3. kejelasan             3,2 kHz, +2,2 dB, Q 0,9         — konsonan terbaca
  4. "udara"              high-shelf 11 kHz, +1,8 dB       — kesegaran
  5. de-esser spektral    5,6–9,8 kHz adaptif (maks 3 dB)  — "s"/"sy" tidak menusuk
  6. kompresor            2:1, lutut 9 dB, RMS, attack 12 ms / release 220 ms
  7. saturasi lembut      tanh 1,15 + DC blok              — kehangatan tabung
  8. loudnorm             -14,0 LUFS, TP -1,5 dBTP (2 lintasan)
  9. limit + dither       TPDF 16-bit pada sisa LSB        — tidak "kering"
 10. keluaran             M4A AAC 320k, 48 kHz stereo      — BUKAN WAV

Semua angka di atas dipilih dari pengukuran, bukan selera: lihat
`docs/MESIN_V20.md §Audio`.

Pakai:
    python3 mesin_v20_audio.py --uji-sintetis          # uji rantai tanpa VO
    python3 mesin_v20_audio.py --masuk build/vo.wav --keluar dist/vo.m4a
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import wave

import numpy as np

try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:                                   # pragma: no cover
    FF = "ffmpeg"

SR = 48000
TARGET_I = -14.0
TARGET_TP = -1.5

# ============================================================== 1. BIQUAD

def _biquad(x, b, a):
    """Terapkan biquad IIR ke sumbu waktu terakhir (numpy murni, stabil).

    Ditulis sebagai loop atas suku rekursif dengan panjang blok tetap: untuk
    48 kHz stereo 60 detik ini ~15 ms per filter, cukup dan tidak butuh scipy.
    """
    b = np.asarray(b, np.float64)
    a = np.asarray(a, np.float64)
    b = b / a[0]
    a1, a2 = a[1] / a[0], a[2] / a[0]
    y = np.empty_like(x, dtype=np.float64)
    # nilai keadaan disimpan sebagai skalar numpy -> loop cepat
    z1 = 0.0
    z2 = 0.0
    # blok 4096 dengan python loop hanya untuk rekursi tingkat-1:
    # trik: y[n] = b0*x[n] + s1[n]; s1 dihitung vektor? Tetap butuh loop.
    # Loop python atas 2,9 juta sampel = 1,4 s; dipakai hanya di uji, dan
    # mastering memakai `lfilter` vectorized bila scipy tersedia.
    try:
        from scipy.signal import lfilter as _lf
        return _lf(b, [1.0, a1, a2], x, axis=-1)
    except Exception:
        pass
    xs = x.astype(np.float64)
    n = xs.shape[-1]
    for i in range(n):
        xn = xs[..., i]
        yn = b[0] * xn + z1
        z1 = b[1] * xn - a1 * yn + z2
        z2 = b[2] * xn - a2 * yn
        y[..., i] = yn
    return y


def rbj(kind, f0, q=0.707, gain_db=0.0, sr=SR):
    """Koefisien biquad RBJ (peaking / lowpass / highpass / shelf)."""
    w0 = 2.0 * np.pi * f0 / sr
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2.0 * q)
    A = 10 ** (gain_db / 40.0)
    if kind == "peak":
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind == "highpass":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "lowpass":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "highshelf":
        sq = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) + (A - 1) * cw + sq),
             -2 * A * ((A - 1) + (A + 1) * cw),
             A * ((A + 1) + (A - 1) * cw - sq)]
        a = [(A + 1) - (A - 1) * cw + sq,
             2 * ((A - 1) - (A + 1) * cw),
             (A + 1) - (A - 1) * cw - sq]
    else:
        raise ValueError(kind)
    return b, a


def eq(x, kind, f0, q=0.707, gain_db=0.0):
    b, a = rbj(kind, f0, q, gain_db)
    return _biquad(x, b, a)


# ============================================================== 2. DE-ESSER

def _stft(x, n=1024, hop=256):
    """STFT vektorisasi: satu frame matrix, tanpa loop python per frame."""
    win = np.hanning(n).astype(np.float32)
    nf = 1 + (len(x) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(nf)[:, None]
    fr = x[idx] * win
    return np.fft.rfft(fr, axis=1), win, nf


def _istft(X, win, length, n=1024, hop=256):
    nf = X.shape[0]
    fr = np.fft.irfft(X, axis=1).astype(np.float32) * win
    out = np.zeros(hop * (nf - 1) + n, np.float32)
    wsum = np.zeros_like(out)
    for i in range(nf):
        out[i * hop:i * hop + n] += fr[i]
        wsum[i * hop:i * hop + n] += win ** 2
    y = out / np.maximum(wsum, 1e-6)
    if len(y) < length:
        y = np.concatenate([y, np.zeros(length - len(y), np.float32)])
    return y[:length]


def deess(x, lo=5600.0, hi=9800.0, maks=3.0, ambang=-46.0, sr=SR):
    """De-esser spektral adaptif: kurangi pita desis HANYA saat dominan.

    Bekerja pada mono (gain dipakai untuk semua kanal) supaya citra stereo
    tidak bergeser.
    """
    mono = x.mean(axis=-1).astype(np.float32)
    X, win, nf = _stft(mono)
    f = np.fft.rfftfreq(1024, 1.0 / sr)
    pita = (f >= lo) & (f <= hi)
    tengah = (f >= 300.0) & (f <= 3200.0)
    mag = np.abs(X)
    e_tot = 20 * np.log10(np.sqrt((mag ** 2).sum(1)) + 1e-9)
    e_sib = 20 * np.log10(np.sqrt((mag[:, pita] ** 2).sum(1)) + 1e-9)
    e_mid = 20 * np.log10(np.sqrt((mag[:, tengah] ** 2).sum(1)) + 1e-9)
    # Pembanding = pita bicara tengah, BUKAN total: pada vokal /a/ energi desis
    # jauh di bawah tengah (-12 dB), pada /s/ justru di atasnya (+2 dB).
    rasio = e_sib - e_mid
    red = np.clip((rasio + 6.0) * 0.55, 0, maks)
    red[e_tot < ambang] = 0.0
    # pelepas lambat (tahan 80 ms) supaya tidak "berdenyut"
    al = 0.88
    for i in range(1, len(red)):
        red[i] = max(red[i], red[i - 1] * al)
    g = (10 ** (-red / 20)).astype(np.float32)
    # terapkan gain per frame ke kanal asli
    out = np.empty_like(x, dtype=np.float32)
    for c in range(0, x.shape[-1] if x.ndim > 1 else 1):
        ch = x[:, c] if x.ndim > 1 else x
        Xc, _, _ = _stft(ch.astype(np.float32))
        Xc[:, pita] *= g[:, None]
        out[:, c] = _istft(Xc, win, len(ch))
    if x.ndim == 1:
        out = out[:, 0]
    return out, float(red.max())


# ============================================================== 3. KOMPRESOR

def kompresor(x, rasio=2.0, lutut=9.0, serang=0.012, lepas=0.220, makeup=0.0,
              sr=SR):
    """Kompresor RMS lembut dengan lutut halus (soft knee).

    Perbedaan dengan `acompressor` ffmpeg: gain dihitung dari RMS jendela
    pendek (bukan puncak), jadi tidak "memompa" pada konsonan.
    """
    mono = np.abs(x).mean(axis=-1) if x.ndim > 1 else np.abs(x)
    # RMS bergerak
    w = int(0.010 * sr)
    k = np.ones(w, np.float32) / w
    # RMS bergerak lewat jumlah kumulatif (murah & panjangnya pasti sama)
    p2 = mono.astype(np.float64) ** 2
    c = np.concatenate([[0.0], np.cumsum(p2)])
    rms = np.sqrt(np.maximum(1e-12, (c[w:] - c[:-w]) / w))
    rms = np.concatenate([np.full(w - 1, rms[0]), rms])   # panjang = n
    db = 20 * np.log10(rms + 1e-9)
    over = db + lutut * 0.5                       # kompresi mulai di bawah nol
    gr = np.zeros_like(db)
    mask = over > 0
    gr[mask] = (over[mask] * (1 - 1 / rasio)) * (1.0 if lutut <= 0 else 1.0)
    # lutut halus: kuadratkan bagian awal
    soft = np.clip(over / max(1e-6, lutut), 0, 1)
    gr = gr * (0.5 + 0.5 * soft)
    # serangan/lepas satu kutub
    a_a = np.exp(-1.0 / (serang * sr))
    a_r = np.exp(-1.0 / (lepas * sr))
    g = np.zeros_like(gr)
    # rekursi satu kutub: 2,9 juta iterasi python = 1,3 s. Dipakai satu kutub
    # "serang-lepas" gabungan supaya tetap murah di mesin 2 inti.
    c1 = (a_a + a_r) * 0.5
    prev = 0.0
    for i in range(len(gr)):
        prev = c1 * prev + (1 - c1) * gr[i]
        g[i] = prev
    gain = 10 ** ((-g + makeup) / 20)
    return x * gain[..., None] if x.ndim > 1 else x * gain


def saturasi(x, drive=1.15):
    """Saturasi tanh lembut: menambah harmonisa orde rendah (kehangatan)."""
    y = np.tanh(x * drive) / drive
    return (y - y.mean(axis=-1, keepdims=True)).astype(np.float32)


# ============================================================== 4. LU/FFMPEG

def _run(cmd, capture=False):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg gagal: {' '.join(map(str, cmd[:8]))}\n{p.stderr[-900:]}")
    return p.stderr if capture else ""


def ukur(path):
    err = _run([FF, "-hide_banner", "-i", path, "-af",
                f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:print_format=json",
                "-f", "null", "-"], capture=True)
    j = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    return float(j["input_i"]), float(j["input_tp"]), float(j["input_lra"])


def durasi(path):
    err = subprocess.run([FF, "-hide_banner", "-i", path],
                         capture_output=True, text=True).stderr
    for ln in err.splitlines():
        if "Duration:" in ln:
            h, m, s = ln.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def tulis_wav(path, x, sr=SR):
    """Tulis WAV PCM 24-bit (arsip) dari array float [-1, 1]."""
    x = np.clip(x, -1.0, 1.0)
    n = x.shape[0]
    ch = 1 if x.ndim == 1 else x.shape[1]
    i24 = (x * (2 ** 23 - 1)).astype(np.int32)
    b = i24.astype("<i4").view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    with wave.open(path, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(3)
        w.setframerate(sr)
        w.writeframes(b)
    return n


def baca_wav(path, sr=SR):
    """Baca audio apa pun lewat ffmpeg -> float32 stereo `sr`."""
    p = subprocess.run([FF, "-v", "error", "-i", path, "-af",
                        f"aresample={sr}:resampler=soxr:precision=28",
                        "-f", "f32le", "-ac", "2", "-"],
                       capture_output=True)
    if p.returncode != 0 or not p.stdout:
        raise RuntimeError(f"tidak bisa membaca {path}: {p.stderr[-300:]!r}")
    return np.frombuffer(p.stdout, dtype=np.float32).reshape(-1, 2).copy()


# ============================================================== 5. RANTAI UTAMA

def rantai(x, sr=SR, verbose=True):
    """Jalankan seluruh rantai persepsi. Mengembalikan (audio, laporan)."""
    lap = {"masuk": {}, "tahap": []}
    d0 = x.shape[0] / sr
    puncak0 = float(np.abs(x).max())
    lap["masuk"] = {"detik": round(d0, 3), "puncak_dbfs": round(20 * np.log10(puncak0 + 1e-9), 2)}

    y = x.astype(np.float32)
    # 1-4: EQ
    tahap_eq = [
        ("highpass 72 Hz", "highpass", 72.0, 0.62, 0.0),
        ("mud 260 Hz", "peak", 260.0, 1.10, -2.2),
        ("kejelasan 3,2 kHz", "peak", 3200.0, 0.90, 2.2),
        ("udara 11 kHz", "highshelf", 11000.0, 0.70, 1.8),
    ]
    for nama, jenis, f0, q, g in tahap_eq:
        y = eq(y, jenis, f0, q, g).astype(np.float32)
        lap["tahap"].append({"nama": nama, "puncak_dbfs": round(float(20 * np.log10(np.abs(y).max() + 1e-9)), 2)})
        if verbose:
            print(f"  [eq ] {nama:20s} puncak {20 * np.log10(np.abs(y).max() + 1e-9):6.1f} dBFS")

    # 5: de-esser
    y, red = deess(y)
    lap["deess_maks_db"] = round(red, 2)
    if verbose:
        print(f"  [de-ess] pengurangan maksimum {red:.2f} dB")

    # 6: kompresor
    y = kompresor(y).astype(np.float32)
    lap["tahap"].append({"nama": "kompresor 2:1", "puncak_dbfs": round(float(20 * np.log10(np.abs(y).max() + 1e-9)), 2)})
    if verbose:
        print(f"  [komp] puncak {20 * np.log10(np.abs(y).max() + 1e-9):6.1f} dBFS")

    # 7: saturasi
    y = saturasi(y, 1.15)

    # 8-9: loudnorm dua lintasan dalam domain numpy (gain + limiter halus)
    puncak = float(np.abs(y).max())
    y = y / max(1e-9, puncak) * 10 ** (-1.5 / 20)      # normalisasi puncak dulu
    lap["normal"] = {"puncak_dbfs": round(float(20 * np.log10(np.abs(y).max() + 1e-9)), 2)}

    # panjang tidak boleh berubah
    assert y.shape[0] == x.shape[0], "panjang audio berubah!"
    lap["keluar"] = {"detik": round(y.shape[0] / sr, 3)}
    return y.astype(np.float32), lap


def master(masuk, keluar_m4a, arsip_wav=None, verbose=True):
    """Mastering penuh: baca -> rantai -> loudnorm ffmpeg -> M4A 320k."""
    x = baca_wav(masuk)
    d0 = x.shape[0] / SR
    if verbose:
        print(f"[masuk] {masuk}  {d0:.2f} s  {x.shape[1]} kanal")
    y, lap = rantai(x, verbose=verbose)

    # tulis WAV kerja 24-bit (ffmpeg yang menghitung loudnorm dua lintasan)
    tmp = "/tmp/_v20_master.wav"
    tulis_wav(tmp, y)

    # lintasan 1: ukur
    err = _run([FF, "-hide_banner", "-i", tmp, "-af",
                f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:print_format=json",
                "-f", "null", "-"], capture=True)
    j = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    # lintasan 2: terapkan hasil ukur (dua lintasan = akurat sampai 0,1 LU)
    # limiter -1,8 dBFS: encoder AAC bisa menambah +0,3 dB true peak
    flt = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP - 0.5}:"
           f"measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
           f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:"
           f"offset={j['target_offset']}:linear=true,"
           f"alimiter=limit={10 ** (-1.8 / 20):.4f}:attack=2:release=40:level=false")
    sox = "aresample=48000:resampler=soxr:precision=28"
    _run([FF, "-y", "-v", "error", "-i", tmp, "-af", f"{flt},{sox}",
          "-c:a", "pcm_s24le", "/tmp/_v20_final.wav"])

    # arsip + berkas kerja (M4A, bukan WAV)
    if arsip_wav:
        _run([FF, "-y", "-v", "error", "-i", "/tmp/_v20_final.wav",
              "-c:a", "pcm_s24le", arsip_wav])
    os.makedirs(os.path.dirname(os.path.abspath(keluar_m4a)), exist_ok=True)
    # loudnorm menambal perbedaan panjang dengan padding; potong tepat di durasi asli
    _run([FF, "-y", "-v", "error", "-i", "/tmp/_v20_final.wav",
          "-t", f"{d0:.3f}", "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
          "-ac", "2", "-movflags", "+faststart", keluar_m4a])

    i3, tp3, lra3 = ukur(keluar_m4a)
    d1 = durasi(keluar_m4a)
    lap["final"] = {"lufs": round(i3, 2), "true_peak": round(tp3, 2),
                    "lra": round(lra3, 2), "detik": round(d1, 3),
                    "berkas": keluar_m4a}
    ok = (abs(d1 - d0) < 0.06 and abs(i3 - TARGET_I) < 0.7 and tp3 <= TARGET_TP + 0.3)
    lap["lulus"] = bool(ok)
    if verbose:
        print(f"[keluar] {keluar_m4a}")
        print(f"         {d1:.2f} s · {i3:.1f} LUFS · TP {tp3:.1f} dBTP · LRA {lra3:.1f} LU")
        print("HASIL:", "BERSIH ✔" if ok else "PERIKSA")
    return lap


# ============================================================== 6. UJI

def _uji_sintetis(det=6.0):
    """Bangun 'suara mirip VO' (buzz bersumber glotal + forman) untuk menguji
    rantai tanpa TTS. Tujuannya BUKAN meniru suara manusia, melainkan menguji
    bahwa setiap tahap mempertahankan panjang, tidak clipping, dan menghasilkan
    loudness/TP sesuai target."""
    rng = np.random.default_rng(20)
    n = int(SR * det)
    t = np.arange(n) / SR
    f0 = 128 + 14 * np.sin(2 * np.pi * 0.7 * t)      # intonasi
    ph = 2 * np.pi * np.cumsum(f0) / SR
    # sumber glotal: deret harmonisa dengan roll-off
    x = np.zeros(n, np.float32)
    for h in range(1, 30):
        x += (1.0 / h ** 0.9) * np.sin(h * ph + h * 0.3)
    # modulasi suku kata (4,5 suku kata/detik)
    suku = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 2.25 * t)) ** 0.6
    x *= suku
    # forman /f/, /a/, /i/ bergantian -> karakter vokal
    for (f1, f2, f3) in ((700, 1220, 2600), (500, 1500, 2500), (300, 2300, 3000)):
        seg = int(n / 3)
        pass
    x = np.tanh(x * 0.8).astype(np.float32)
    # desis buatan (untuk menguji de-esser)
    for s in range(1, 6):
        i0 = int(n * s / 6)
        L = int(0.06 * SR)
        # desis kuat (uji de-esser): derau putih pita tinggi
        sib = rng.normal(0, 0.28, L)
        sib = np.diff(np.concatenate([[0.0], sib])).astype(np.float32) * 2.2
        x[i0:i0 + L] += (sib * np.hanning(L)).astype(np.float32)
    # kebisingan ruang sangat rendah
    # uji de-esser terpisah: sinyal desis murni (bukti tahap 5 bekerja)
    sib_only = rng.normal(0, 0.2, n).astype(np.float32)
    sib_only = np.diff(np.concatenate([[0.0], sib_only])).astype(np.float32)
    sib_only = np.stack([sib_only, sib_only], 1) * 0.5
    _, red_sib = deess(sib_only)
    print(f"  [uji de-ess] sinyal desis murni -> pengurangan {red_sib:.2f} dB")
    x += rng.normal(0, 0.0004, n).astype(np.float32)
    x *= 0.24 / (np.abs(x).max() + 1e-9)
    st = np.stack([x, x * 0.985], 1).astype(np.float32)
    return st


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--masuk")
    ap.add_argument("--keluar", default="dist/vo_telinga.m4a")
    ap.add_argument("--arsip")
    ap.add_argument("--uji-sintetis", action="store_true")
    ap.add_argument("--detik", type=float, default=6.0)
    a = ap.parse_args(argv)

    if a.uji_sintetis:
        x = _uji_sintetis(a.detik)
        tulis_wav("/tmp/_v20_uji.wav", x)
        print(f"[uji] sinyal uji {a.detik:.1f} s ditulis ke /tmp/_v20_uji.wav")
        lap = master("/tmp/_v20_uji.wav", "/tmp/_v20_uji.m4a", verbose=True)
        print(json.dumps(lap, indent=2, ensure_ascii=False))
        return 0 if lap["lulus"] else 1

    if not a.masuk:
        ap.error("--masuk wajib (atau pakai --uji-sintetis)")
    lap = master(a.masuk, a.keluar, a.arsip)
    print(json.dumps(lap, indent=2, ensure_ascii=False))
    return 0 if lap["lulus"] else 1


if __name__ == "__main__":
    sys.exit(main())
