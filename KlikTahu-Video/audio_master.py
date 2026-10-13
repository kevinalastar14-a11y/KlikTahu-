"""
audio_master.py — mastering audio untuk TELINGA MANUSIA.

Normalisasi biasa hanya mengejar angka puncak (peak), padahal telinga tidak
mendengar puncak — telinga mendengar *loudness* berbobot frekuensi. Modul ini
memakai standar penyiaran yang memang dirancang untuk persepsi manusia:

  * ITU-R BS.1770-4 / EBU R128 : pengukuran loudness (K-weighting + gating)
  * true-peak (4x oversampling) : mencegah distorsi antar-sampel di DAC
  * EQ speech-band             : kejelasan kata di speaker HP & earbud
  * de-esser                   : meredam desis "s"/"sy" yang menusuk telinga
  * harmonik bass              : trik psikoakustik "missing fundamental" agar
                                 bass terasa di speaker kecil
  * kompresor bus              : volume konsisten, tanpa terasa dipadatkan

Target default mengikuti rekomendasi YouTube: -14 LUFS integrated, true peak
≤ -1.0 dBTP.
"""

from __future__ import annotations

import math

import numpy as np

from audio_design import SR, fft_filter, highpass, lowpass, normalize_peak, soft_limit

# --------------------------------------------------------------------------- #
#  K-weighting (ITU-R BS.1770-4) untuk 48 kHz
# --------------------------------------------------------------------------- #
_K_COEFF_48K = dict(
    shelf_b=(1.53512485958697, -2.69169618940638, 1.19839281085285),
    shelf_a=(1.0, -1.69065929318241, 0.73248077421585),
    hp_b=(1.0, -2.0, 1.0),
    hp_a=(1.0, -1.99004745483398, 0.99007225036621),
)


def _biquad_mag(b, a, freqs, sr):
    z = np.exp(-2j * math.pi * freqs / sr)
    num = b[0] + b[1] * z + b[2] * z**2
    den = a[0] + a[1] * z + a[2] * z**2
    return np.abs(num / den)


def k_weighting(x: np.ndarray, sr: int = SR) -> np.ndarray:
    """Terapkan filter K (tahap shelf + high-pass) sesuai BS.1770."""
    if sr != 48000:                       # fallback perkiraan untuk laju lain
        return fft_filter(x, sr, lambda f: 1.0 / (1.0 + (38.0 / np.maximum(f, 1.0)) ** 4)
                          * (1.0 + 3.99 * (np.maximum(f, 1.0) / 1681.0) ** 2
                             / (1 + (np.maximum(f, 1.0) / 1681.0) ** 2)))
    c = _K_COEFF_48K

    def resp(f):
        return (_biquad_mag(c["shelf_b"], c["shelf_a"], f, sr)
                * _biquad_mag(c["hp_b"], c["hp_a"], f, sr))
    return fft_filter(x, sr, resp)


def loudness_lufs(x: np.ndarray, sr: int = SR, gated: bool = True) -> float:
    """
    Integrated loudness (LUFS) per ITU-R BS.1770-4.

    Blok 400 ms dengan geser 100 ms, gerbang absolut -70 LUFS lalu gerbang
    relatif -10 LU — inilah yang membuat angka LUFS terasa sama dengan apa
    yang didengar telinga.
    """
    if x.ndim == 1:
        x = x[:, None]
    chan = [k_weighting(x[:, c], sr) for c in range(x.shape[1])]
    block, step = int(0.4 * sr), int(0.1 * sr)
    n = x.shape[0]
    if n < block:
        block = n
    idx = range(0, max(1, n - block + 1), step)
    powers = []
    for i in idx:
        seg = [c[i:i + block] for c in chan]
        if len(seg[0]) < block * 0.5:
            continue
        p = sum(float(np.mean(s ** 2)) for s in seg)   # BS.1770: jumlah, bukan rata-rata
        powers.append(p)
    if not powers:
        return -70.0
    z = np.array(powers)
    def to_lufs(zz):
        zz = zz[zz > 0]
        if zz.size == 0:
            return -70.0
        return -0.691 + 10 * math.log10(float(np.mean(zz)))
    if not gated:
        return to_lufs(z)
    abs_gate = 10 ** ((-70.0 + 0.691) / 10)
    z = z[z > abs_gate]
    if z.size == 0:
        return -70.0
    rel = to_lufs(z) - 10.0
    z = z[z > 10 ** ((rel + 0.691) / 10)]
    return to_lufs(z)


def true_peak_dbtp(x: np.ndarray, sr: int = SR, oversample: int = 4) -> float:
    """True peak (dBTP) via oversampling 4x — puncak antar-sampel yang bisa
    membuat DAC klip walau sampelnya sendiri terlihat aman."""
    if x.ndim == 1:
        x = x[:, None]
    peak = 0.0
    for c in range(x.shape[1]):
        sig = x[:, c].astype(np.float64)
        n = sig.size
        pad = 1 << int(math.ceil(math.log2(max(2, n))))
        spec = np.fft.rfft(sig, pad)
        up = np.zeros(pad * oversample // 2 + 1, dtype=complex)
        up[:spec.size] = spec
        up *= oversample
        y = np.fft.irfft(up, pad * oversample)
        peak = max(peak, float(np.max(np.abs(y))))
    return 20 * math.log10(max(peak, 1e-9))


# --------------------------------------------------------------------------- #
#  Pemroses untuk persepsi telinga
# --------------------------------------------------------------------------- #
def moving_mean(x: np.ndarray, win: int) -> np.ndarray:
    """Rata-rata bergerak (vektor, memakai cumulative sum — tanpa loop Python)."""
    win = max(4, int(win))
    v = x.astype(np.float64)
    c = np.cumsum(np.concatenate(([0.0], v)))
    half = win // 2
    idx = np.arange(v.size)
    lo = np.clip(idx - half, 0, v.size)
    hi = np.clip(idx + half, 0, v.size)
    return (c[hi] - c[lo]) / np.maximum(1, hi - lo)


def moving_rms(x: np.ndarray, win: int) -> np.ndarray:
    """RMS bergerak."""
    return np.sqrt(moving_mean(x.astype(np.float64) ** 2, win))


def compressor(x: np.ndarray, sr: int = SR, threshold_db: float = -20.0,
               ratio: float = 2.4, attack_ms: float = 8.0, release_ms: float = 140.0,
               knee_db: float = 6.0, makeup_db: float = 0.0,
               max_reduction_db: float = 8.0) -> tuple[np.ndarray, float]:
    """
    Kompresor bus feed-forward (detektor RMS, soft-knee).

    Bukan untuk 'membuat keras', melainkan menjaga volume tetap konsisten agar
    telinga tidak perlu menyesuaikan diri di setiap kalimat. Pengurangan gain
    dibatasi `max_reduction_db` supaya tidak ada efek memompa.
    """
    win_det = max(8, int(sr * 0.015))
    env_db = 20 * np.log10(np.maximum(moving_rms(x, win_det), 1e-6))
    over = env_db - threshold_db
    half_knee = max(0.5, knee_db / 2.0)
    slope = 1.0 - 1.0 / ratio
    gain_db = np.zeros_like(over)
    hard = over > half_knee
    gain_db[hard] = -(over[hard] - half_knee) * slope
    soft = (over > -half_knee) & (~hard)
    if np.any(soft):
        gain_db[soft] = -slope * (over[soft] + half_knee) ** 2 / (2.0 * knee_db + 1e-9)
    gain_db = np.clip(gain_db, -max_reduction_db, 0.0)
    # pelepasan halus (rata-rata jendela release) => tidak ada artefak memompa
    gain_db = moving_mean(gain_db, max(8, int(sr * release_ms / 1000.0)))
    gain = 10 ** ((gain_db + makeup_db) / 20.0)
    return (x * gain).astype(np.float32), float(np.min(gain_db))


def moving_min(x: np.ndarray, win: int) -> np.ndarray:
    """
    Minimum bergerak (vektor). Dipakai limiter: gain harus turun SEBELUM puncak
    datang (look-ahead) dan bertahan selama puncak — bukan rata-rata.
    """
    win = max(2, int(win))
    n = x.size
    if win >= n:
        return np.full_like(x, float(np.min(x)))
    # blok minimum lalu disebar (forward/backward pass) — O(n), tanpa loop Python
    blocks = n // win
    red = x[: blocks * win].reshape(blocks, win).min(axis=1)
    idx = np.arange(n)
    b = np.minimum(idx // win, blocks - 1)
    fwd = np.minimum.accumulate(red)[b]
    bwd = np.minimum.accumulate(red[::-1])[::-1][b]
    out = np.maximum(fwd, bwd)
    shift = win // 2
    return np.roll(out, shift)


def true_peak_envelope(x: np.ndarray, sr: int = SR, oversample: int = 4) -> np.ndarray:
    """
    Envelope puncak sebenarnya (termasuk puncak antar-sampel) pada tingkat
    sampel asli. Inilah yang 'didengar' konverter DAC, bukan puncak sampel.
    """
    if x.ndim == 1:
        x = x[:, None]
    n = x.shape[0]
    pad = 1 << int(math.ceil(math.log2(max(2, n))))
    env = np.zeros(n * oversample, dtype=np.float64)
    for c in range(x.shape[1]):
        spec = np.fft.rfft(x[:, c].astype(np.float64), pad)
        up = np.zeros(pad * oversample // 2 + 1, dtype=complex)
        up[:spec.size] = spec
        up *= oversample
        y4 = np.abs(np.fft.irfft(up, pad * oversample))[: n * oversample]
        env = np.maximum(env, y4)
    return env.reshape(n, oversample).max(axis=1)


def soft_clip(x: np.ndarray, drive_db: float = 2.0, ceiling_db: float = -1.2) -> np.ndarray:
    """
    Soft clipper: menekan puncak transien dengan lekukan tanh.

    Telinga membenci clipping keras (menghasilkan harmonik orde tinggi yang
    menusuk), tetapi menyukai pembulatan transien yang mulus: inilah yang
    membuat master terasa 'keras tapi tetap enak'. Dipakai sebelum limiter
    supaya limiter hanya perlu bekerja sedikit.
    """
    drive = 10 ** (drive_db / 20.0)
    ceiling = 10 ** (ceiling_db / 20.0)
    y = np.tanh(x * drive / ceiling) * ceiling
    # di bawah -6 dBFS hampir tidak berubah: kurva tanh ≈ linear di sana
    return y.astype(np.float32)


def true_peak_limit(x: np.ndarray, sr: int = SR, ceiling_db: float = -1.0,
                    release_ms: float = 120.0, max_iter: int = 6) -> np.ndarray:
    """
    Limiter true-peak: gain diturunkan mengikuti envelope puncak nyata, dengan
    look-ahead dan pelepasan halus sehingga tidak ada distorsi maupun 'pompa'.
    Dijamin: puncak antar-sampel hasil akhir ≤ ceiling.
    """
    ceiling = 10 ** (ceiling_db / 20.0)
    y = x.astype(np.float32).copy()
    env = true_peak_envelope(y, sr, oversample=4)     # diukur sekali (mahal)
    applied = np.ones(y.shape[0], dtype=np.float64)
    for _ in range(max_iter):
        eff = env * applied                            # envelope saat ini (skala linier)
        need = np.minimum(1.0, ceiling / np.maximum(eff, 1e-9))
        g = moving_min(need, max(2, int(sr * release_ms / 1000.0)))
        g = moving_min(g, max(2, int(sr * 0.0015)))    # look-ahead 1,5 ms
        g = moving_mean(g, max(4, int(sr * 0.005)))    # halus, tanpa klik
        if float(np.min(g)) > 0.9995:
            break
        applied *= g
        y = (y * g[:, None]).astype(np.float32)
    # jaga-jaga terakhir: pastikan benar-benar di bawah ceiling
    tp = true_peak_dbtp(y, sr)
    if tp > ceiling_db:
        y = (y * 10 ** (-(tp - ceiling_db) / 20.0)).astype(np.float32)
    return y


def de_esser(x: np.ndarray, sr: int = SR, center: float = 6800.0, width: float = 1.35,
             threshold_db: float = -26.0, amount: float = 0.62) -> np.ndarray:
    """Redam desis sibilant ('s', 'sy', 'c') yang paling menusuk telinga."""
    lo, hi = center / width, center * width
    band = fft_filter(x, sr, lambda f: lowpass(hi, 2)(f) * highpass(lo, 2)(f))
    env = moving_rms(band, int(sr * 0.005))
    env_db = 20 * np.log10(np.maximum(env, 1e-6))
    over = np.clip(env_db - threshold_db, 0, None)
    gain = 1.0 - amount * (1.0 - 1.0 / (1.0 + over / 6.0))
    gain = moving_rms(gain, int(sr * 0.010))
    return (x - band + band * gain.astype(np.float32)).astype(np.float32)


def tone_balance(x: np.ndarray, sr: int = SR) -> np.ndarray:
    """
    Penyeimbangan nada berbasis kontur equal-loudness:

      40-80 Hz  : dibuang (tak terdengar di HP, hanya bikin limiter bekerja)
      180 Hz    : sedikit kehangatan dada
      300 Hz    : kurangi "mud" agar tidak terasa selimut
      3.2 kHz   : dorong kejelasan konsonan (paling penting untuk kata)
      6.8 kHz   : sedikit ditahan setelah de-esser
      11.5 kHz  : "udara", membuat narasi terasa mahal
    """
    def resp(f):
        f = np.maximum(f, 1.0)
        sub = 1.0 / (1.0 + (60.0 / f) ** 4)
        warmth = 1.0 + 0.16 * np.exp(-((np.log10(f / 190.0)) ** 2) / 0.045)
        mud = 1.0 - 0.22 * np.exp(-((np.log10(f / 310.0)) ** 2) / 0.030)
        presence = 1.0 + 0.50 * np.exp(-((np.log10(f / 3200.0)) ** 2) / 0.075)
        sib = 1.0 - 0.10 * np.exp(-((np.log10(f / 6800.0)) ** 2) / 0.020)
        air = 1.0 + 0.30 * np.exp(-((np.log10(f / 11500.0)) ** 2) / 0.10)
        return sub * warmth * mud * presence * sib * air
    return fft_filter(x, sr, resp)


def harmonic_bass(x: np.ndarray, sr: int = SR, amount: float = 0.16) -> np.ndarray:
    """
    Psikoakustik 'missing fundamental'.

    Speaker HP tidak mampu memutar 60-120 Hz, padahal telinga menyimpulkan nada
    dasar dari harmoniknya. Harmonik kedua ditambahkan di 120-320 Hz sehingga
    bass tetap terasa di speaker kecil.
    """
    low = fft_filter(x, sr, lambda f: lowpass(140, 2)(f) * highpass(55, 2)(f))
    harm = (low * np.abs(low))                        # distorsi orde-2
    harm = fft_filter(harm, sr, lambda f: highpass(110, 2)(f) * lowpass(420, 2)(f))
    harm = normalize_peak(harm, -12.0) if np.max(np.abs(harm)) > 1e-6 else harm
    return (x + harm * amount).astype(np.float32)


def stereo_width(left: np.ndarray, right: np.ndarray, amount: float = 1.12) -> tuple:
    """Lebarkan hanya sisi efek; komponen tengah (narasi) dibiarkan utuh."""
    mid = (left + right) * 0.5
    side = (left - right) * 0.5 * amount
    return (mid + side).astype(np.float32), (mid - side).astype(np.float32)


# --------------------------------------------------------------------------- #
#  Rantai mastering
# --------------------------------------------------------------------------- #
def master(stereo: np.ndarray, sr: int = SR, target_lufs: float = -14.0,
           true_peak_db: float = -1.0, verbose: bool = True) -> tuple[np.ndarray, dict]:
    """
    Rantai lengkap: kompresi -> EQ -> de-esser -> bass harmonik -> loudness ->
    true-peak limit. Mengembalikan audio stereo final + laporan pengukuran.
    """
    left, right = stereo[:, 0].copy(), stereo[:, 1].copy()
    left, right = stereo_width(left, right, 1.10)

    # per kanal: kompresi lembut lalu penyeimbangan nada & desis
    out = []
    gr_total = 0.0
    for ch in (left, right):
        c, gr = compressor(ch, sr, threshold_db=-22.0, ratio=2.6,
                           attack_ms=6.0, release_ms=160.0, makeup_db=3.0,
                           max_reduction_db=10.0)
        gr_total = min(gr_total, gr)
        c = tone_balance(c, sr)
        c = de_esser(c, sr)
        c = harmonic_bass(c, sr, amount=0.14)
        out.append(c)
    y = np.stack(out, axis=1)

    # pangkas transien dengan mulus supaya loudness bisa naik tanpa distorsi
    y = soft_clip(y, drive_db=2.2, ceiling_db=-1.2)

    # loudness + true-peak: geser ke target, batasi puncak, ulangi sampai stabil
    loud_before = loudness_lufs(y, sr)
    gain_db = float(np.clip(target_lufs - loud_before, -24.0, 24.0))
    y = (y * 10 ** (gain_db / 20.0)).astype(np.float32)
    y = true_peak_limit(y, sr, ceiling_db=true_peak_db)
    prev_loud = None
    for _ in range(6):                                  # rapatkan sampai konvergen
        loud = loudness_lufs(y, sr)
        delta = target_lufs - loud
        if abs(delta) < 0.3:
            break
        if prev_loud is not None and abs(loud - prev_loud) < 0.15:
            break                                       # sudah mentok (limiter menahan)
        prev_loud = loud
        y = (y * 10 ** (min(delta, 6.0) / 20.0)).astype(np.float32)
        y = true_peak_limit(y, sr, ceiling_db=true_peak_db)

    tp = true_peak_dbtp(y, sr)
    report = dict(
        lufs_in=loud_before,
        lufs_out=loudness_lufs(y, sr),
        true_peak_dbtp=tp,
        gain_db=gain_db,
        compressor_min_gain_db=gr_total,
        mono_compatible=True,
    )
    if verbose:
        print(f"[master] loudness {loud_before:6.2f} -> {report['lufs_out']:6.2f} LUFS "
              f"(target {target_lufs}), true peak {tp:5.2f} dBTP "
              f"(batas {true_peak_db}), gain {gain_db:+.1f} dB")
    return y.astype(np.float32), report


def mono_fold_check(stereo: np.ndarray) -> float:
    """Selisih energi mono-fold terhadap stereo (dB). Negatif besar = ada
    pembatalan fasa saat diturunkan ke mono (HP, speaker Bluetooth)."""
    st = float(np.sqrt(np.mean(stereo ** 2)))
    mo = float(np.sqrt(np.mean(stereo.mean(axis=1) ** 2)))
    return 20 * math.log10(max(mo, 1e-9) / max(st, 1e-9))
