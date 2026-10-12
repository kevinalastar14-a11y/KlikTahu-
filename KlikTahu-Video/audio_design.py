"""
audio_design.py — tata suara KlikTahu Video Engine.

Isi:
  * decode audio (mp3/wav) -> numpy lewat ffmpeg
  * pembuat sound-effect prosedural (whoosh, impact, riser, tick, pop, sub-drop)
    sehingga proyek tidak butuh file SFX berlisensi apa pun
  * penyusun mix: voice-over + SFX, sidechain ducking, soft-limiter, dan
    normalisasi loudness kira-kira -14 LUFS (standar YouTube)
"""

from __future__ import annotations

import math
import struct
import subprocess
import wave

import imageio_ffmpeg
import numpy as np

SR = 48_000


def clamp01(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if x < lo else hi if x > hi else x


def ffmpeg_exe() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


# --------------------------------------------------------------------------- #
#  I/O & utilitas sinyal
# --------------------------------------------------------------------------- #
def decode_audio(path: str, sr: int = SR, mono: bool = True) -> np.ndarray:
    """Decode file audio apa pun menjadi float32 [-1, 1] (mono) atau (n, 2) stereo."""
    cmd = [ffmpeg_exe(), "-v", "error", "-i", str(path),
           "-ac", "1" if mono else "2", "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype="<f4").astype(np.float32)
    if not mono:
        x = x.reshape(-1, 2)
    return x


def encode_wav(path: str, stereo: np.ndarray, sr: int = SR) -> None:
    """Tulis WAV 16-bit (PCM) dari array (n, 2) float."""
    data = np.clip(stereo, -1.0, 1.0)
    pcm = (data * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def silence_bounds(x: np.ndarray, sr: int = SR, thresh_db: float = -46.0,
                   guard_ms: float = 25.0) -> tuple[int, int]:
    """Cari batas awal/akhir non-silence (untuk memangkas jeda TTS)."""
    if x.size == 0:
        return 0, 0
    win = max(1, int(sr * 0.010))
    n = x.size // win * win
    frames = np.abs(x[:n]).reshape(-1, win).max(axis=1)
    thr = 10 ** (thresh_db / 20.0)
    idx = np.nonzero(frames > thr)[0]
    if idx.size == 0:
        return 0, x.size
    guard = int(sr * guard_ms / 1000.0)
    start = max(0, int(idx[0]) * win - guard)
    end = min(x.size, (int(idx[-1]) + 1) * win + guard)
    return start, end


def trim_silence(x: np.ndarray, sr: int = SR, thresh_db: float = -46.0) -> np.ndarray:
    a, b = silence_bounds(x, sr, thresh_db)
    return x[a:b]


def fade(x: np.ndarray, ms_in: float = 6.0, ms_out: float = 12.0, sr: int = SR) -> np.ndarray:
    y = x.copy()
    n_in = min(int(sr * ms_in / 1000), y.size)
    n_out = min(int(sr * ms_out / 1000), y.size)
    if n_in:
        y[:n_in] *= np.linspace(0, 1, n_in, dtype=np.float32)
    if n_out:
        y[-n_out:] *= np.linspace(1, 0, n_out, dtype=np.float32)
    return y


def _env_ar(n: int, attack: int, release: int) -> np.ndarray:
    """Envelope attack/release (one-pole) untuk ducking."""
    a = 1.0 - math.exp(-1.0 / max(1, attack))
    r = 1.0 - math.exp(-1.0 / max(1, release))
    out = np.empty(n, dtype=np.float32)
    e = 0.0
    for i in range(n):
        e += (a if 1.0 > e else r) * (1.0 - e)
        out[i] = e
    return out


def smooth_envelope(x: np.ndarray, sr: int, attack_ms: float = 25.0,
                    release_ms: float = 220.0) -> np.ndarray:
    """Envelope amplitudo untuk sidechain ducking (vektor, pakai maximum_filter)."""
    win = max(1, int(sr * 0.02))
    n = x.size // win * win
    if n == 0:
        return np.zeros_like(x)
    peak = np.abs(x[:n]).reshape(-1, win).max(axis=1)
    a = math.exp(-1.0 / (sr / win * attack_ms / 1000.0))
    r = math.exp(-1.0 / (sr / win * release_ms / 1000.0))
    env = np.empty_like(peak)
    e = 0.0
    for i in range(peak.size):
        c = a if peak[i] > e else r
        e = c * e + (1 - c) * peak[i]
        env[i] = e
    env = np.repeat(env, win)[: x.size]
    if env.size < x.size:
        env = np.pad(env, (0, x.size - env.size), mode="edge")
    return env


# --------------------------------------------------------------------------- #
#  Filter (domain frekuensi — tanpa dependensi scipy)
# --------------------------------------------------------------------------- #
def fft_filter(x: np.ndarray, sr: int, response) -> np.ndarray:
    """Terapkan respons magnitudo `response(freq_hz) -> gain` pada sinyal."""
    n = 1 << int(math.ceil(math.log2(max(2, x.size))))
    spec = np.fft.rfft(x, n)
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    spec *= response(freqs)
    y = np.fft.irfft(spec, n)[: x.size]
    return y.astype(np.float32)


def bandpass(low: float, high: float, order: float = 2.0):
    def resp(f):
        f = np.maximum(f, 1.0)
        hp = 1.0 / (1.0 + (low / f) ** (2 * order))
        lp = 1.0 / (1.0 + (f / high) ** (2 * order))
        return hp * lp
    return resp


def lowpass(fc: float, order: float = 2.0):
    return lambda f: 1.0 / (1.0 + (np.maximum(f, 1.0) / fc) ** (2 * order))


def highpass(fc: float, order: float = 2.0):
    return lambda f: 1.0 / (1.0 + (fc / np.maximum(f, 1.0)) ** (2 * order))


def eq_voice(x: np.ndarray, sr: int = SR) -> np.ndarray:
    """
    Ekolalisasi voice-over: buang rumble, tambah kejelasan 3 kHz,
    dan sedikit 'air' di 9 kHz supaya narasi terdengar mahal.
    """
    def resp(f):
        f = np.maximum(f, 1.0)
        rumble = 1.0 / (1.0 + (95.0 / f) ** 4)                     # high-pass 95 Hz
        mud = 1.0 - 0.30 * np.exp(-((np.log10(f / 260.0)) ** 2) / 0.05)   # -3 dB @260
        presence = 1.0 + 0.55 * np.exp(-((np.log10(f / 3200.0)) ** 2) / 0.09)
        air = 1.0 + 0.25 * np.exp(-((np.log10(f / 9500.0)) ** 2) / 0.10)
        return rumble * mud * presence * air
    return fft_filter(x, sr, resp)


def normalize_peak(x: np.ndarray, target_db: float = -1.0) -> np.ndarray:
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak <= 1e-9:
        return x
    return x * (10 ** (target_db / 20.0) / peak)


def measure_lufs(x: np.ndarray, sr: int = SR) -> float:
    """Perkiraan integrated loudness (ITU-R BS.1770 tanpa gating)."""
    if x.size == 0:
        return -70.0
    k = fft_filter(x, sr, lambda f: (1.0 / (1.0 + (38.0 / np.maximum(f, 1.0)) ** 4))
                   * (1.0 + 0.4 * (np.maximum(f, 1.0) / 1500.0) ** 2 / (1 + (np.maximum(f, 1.0) / 1500.0) ** 2)))
    block = max(1, int(sr * 0.4))
    n = k.size // block
    if n == 0:
        return -70.0
    ms = np.mean(k[: n * block].reshape(n, block) ** 2, axis=1)
    ms = ms[ms > 1e-10]
    if ms.size == 0:
        return -70.0
    return float(-0.691 + 10 * math.log10(float(np.mean(ms))))


def soft_limit(x: np.ndarray, threshold: float = 0.72) -> np.ndarray:
    """Soft-knee limiter: di bawah ambang linier, di atasnya tanh mulus."""
    t = threshold
    a = np.abs(x)
    over = a > t
    if not np.any(over):
        return x
    y = x.copy()
    mag = t + (1.0 - t) * np.tanh((a[over] - t) / (1.0 - t))
    y[over] = np.sign(x[over]) * mag
    return y


# --------------------------------------------------------------------------- #
#  Pembuat SFX prosedural
# --------------------------------------------------------------------------- #
def _noise(n: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).normal(0, 1, n).astype(np.float32)


def _noise_sweep(dur: float, f0: float, f1: float, q: float = 1.1, seed: int = 0,
                 sr: int = SR) -> np.ndarray:
    """Noise dengan band tengah yang bergerak f0 -> f1 (whoosh/riser)."""
    n = int(dur * sr)
    noise = _noise(n, seed)
    seg = max(256, n // 24)
    out = np.zeros(n, dtype=np.float32)
    win = np.hanning(seg * 2).astype(np.float32)
    prev = np.zeros(seg * 2, dtype=np.float32)
    for i in range(0, n, seg):
        t = i / n
        fc = f0 * (f1 / f0) ** t
        band = bandpass(fc / q, fc * q)(np.fft.rfftfreq(seg * 2, 1 / sr))
        chunk = noise[i:i + seg * 2]
        if chunk.size < seg * 2:
            chunk = np.pad(chunk, (0, seg * 2 - chunk.size))
        y = np.fft.irfft(np.fft.rfft(chunk) * band, seg * 2).astype(np.float32)
        out[i:i + seg] = (y[:seg] * win[:seg] + prev[:seg])
        prev = y[seg:] * win[seg:]
    return out


def sfx_whoosh(dur: float = 0.42, f0: float = 2600.0, f1: float = 260.0,
               seed: int = 11, sr: int = SR) -> np.ndarray:
    n = int(dur * sr)
    x = _noise_sweep(dur, f0, f1, q=0.9, seed=seed, sr=sr)
    x += 0.25 * _noise_sweep(dur, f0 * 1.6, f1 * 1.2, q=1.4, seed=seed + 5, sr=sr)
    env = np.exp(-np.linspace(0, 4.2, n)) * np.sin(np.linspace(0, math.pi, n)) ** 0.7
    x = x * env.astype(np.float32)
    return normalize_peak(x, -8.0)


def sfx_impact(dur: float = 1.1, sub: float = 1.0, seed: int = 3, sr: int = SR) -> np.ndarray:
    n = int(dur * sr)
    t = np.arange(n) / sr
    # sub-bass turun cepat: 120 -> 42 Hz
    f = 120 * (42 / 120) ** (t / dur)
    phase = np.cumsum(2 * math.pi * f / sr)
    body = np.sin(phase) * np.exp(-t * 3.4)
    click = _noise(int(0.05 * sr), seed) * np.exp(-np.arange(int(0.05 * sr)) / (0.006 * sr))
    burst = fft_filter(_noise(n, seed + 1), sr, lowpass(700)) * np.exp(-t * 12.0) * 0.5
    x = np.zeros(n, dtype=np.float32)
    x[: click.size] += click * 0.6
    x += (body * 0.95 * sub + burst).astype(np.float32)
    return normalize_peak(x, -7.0)


def sfx_thud(dur: float = 0.5, seed: int = 21, sr: int = SR) -> np.ndarray:
    n = int(dur * sr)
    t = np.arange(n) / sr
    x = fft_filter(_noise(n, seed), sr, lowpass(220)) * np.exp(-t * 9.0)
    x += (np.sin(2 * math.pi * 78 * t) * np.exp(-t * 8.0)).astype(np.float32) * 0.7
    return normalize_peak(x.astype(np.float32), -9.0)


def sfx_tick(dur: float = 0.06, freq: float = 2400.0, seed: int = 5, sr: int = SR) -> np.ndarray:
    n = int(dur * sr)
    t = np.arange(n) / sr
    x = np.sin(2 * math.pi * freq * t) * np.exp(-t * 90.0)
    x += 0.35 * _noise(n, seed) * np.exp(-t * 160.0)
    return normalize_peak(x.astype(np.float32), -12.0)


def sfx_pop(dur: float = 0.28, seed: int = 9, sr: int = SR) -> np.ndarray:
    n = int(dur * sr)
    t = np.arange(n) / sr
    f = 520 * np.exp(-t * 12.0) + 150
    x = np.sin(np.cumsum(2 * math.pi * f / sr)) * np.exp(-t * 14.0)
    x += 0.4 * _noise(n, seed) * np.exp(-t * 55.0)
    x = fft_filter(x.astype(np.float32), sr, lowpass(6000))
    return normalize_peak(x, -8.0)


def sfx_riser(dur: float = 1.2, f0: float = 220.0, f1: float = 3400.0,
              seed: int = 13, sr: int = SR) -> np.ndarray:
    n = int(dur * sr)
    t = np.arange(n) / sr
    x = _noise_sweep(dur, f0, f1, q=0.8, seed=seed, sr=sr)
    sweep = np.sin(np.cumsum(2 * math.pi * (f0 * (f1 / f0) ** (t / dur)) / sr)).astype(np.float32)
    env = (t / dur) ** 1.6
    x = x * (0.35 + 0.9 * env) + sweep * env * 0.22
    ramp = np.clip(t / 0.02, 0, 1)
    return normalize_peak((x * ramp).astype(np.float32), -10.0)


def sfx_sub_drop(dur: float = 1.3, seed: int = 17, sr: int = SR) -> np.ndarray:
    n = int(dur * sr)
    t = np.arange(n) / sr
    f = 180 * (33 / 180) ** (t / dur)
    x = np.sin(np.cumsum(2 * math.pi * f / sr)) * np.exp(-t * 1.9)
    x[: int(0.03 * sr)] *= np.linspace(0, 1, int(0.03 * sr))
    return normalize_peak(x.astype(np.float32), -6.0)


SFX_BUILDERS = {
    "whoosh": lambda sr: sfx_whoosh(0.45, 2400, 240, 11, sr),
    "whoosh_soft": lambda sr: sfx_whoosh(0.55, 1500, 200, 31, sr) * 0.6,
    "swipe": lambda sr: sfx_whoosh(0.34, 4200, 600, 41, sr) * 0.8,
    "impact": lambda sr: sfx_impact(1.2, 1.0, 3, sr),
    "impact_soft": lambda sr: sfx_impact(0.9, 0.7, 7, sr) * 0.75,
    "thud": lambda sr: sfx_thud(0.5, 21, sr),
    "tick": lambda sr: sfx_tick(0.06, 2400, 5, sr),
    "tick_tick": lambda sr: np.concatenate([sfx_tick(0.05, 1500, 5, sr),
                                            np.zeros(int(0.055 * sr), np.float32),
                                            sfx_tick(0.05, 2100, 6, sr),
                                            np.zeros(int(0.045 * sr), np.float32),
                                            sfx_tick(0.06, 2900, 7, sr)]),
    "pop": lambda sr: sfx_pop(0.28, 9, sr),
    "riser": lambda sr: sfx_riser(1.4, 180, 3600, 13, sr),
    "riser_short": lambda sr: sfx_riser(0.6, 260, 2600, 23, sr) * 0.8,
    "sub_drop": lambda sr: sfx_sub_drop(1.3, 17, sr),
}


# --------------------------------------------------------------------------- #
#  Penyusun mix
# --------------------------------------------------------------------------- #
def build_mix(total_dur: float, vo_events, sfx_events, sr: int = SR,
              target_lufs: float = -13.5) -> np.ndarray:
    """
    Susun audio final stereo (n, 2).

    vo_events : [(start_detik, np.array mono)]  — sudah di-EQ & dinormalisasi
    sfx_events: [(start_detik, key, gain_db, pan)]
    """
    n = int(math.ceil((total_dur + 0.25) * sr))
    vo = np.zeros(n, dtype=np.float32)
    for start, clip in vo_events:
        i = int(start * sr)
        j = min(n, i + clip.size)
        if j > i:
            vo[i:j] += clip[: j - i]

    # level VO: -1.5 dBFS peak, lalu EQ kejelasan
    vo = normalize_peak(vo, -1.5)
    duck = smooth_envelope(vo, sr, attack_ms=18, release_ms=260)
    duck = np.clip(duck / (np.percentile(duck, 99.5) + 1e-6), 0, 1)
    duck_gain = (1.0 - 0.62 * duck).astype(np.float32)

    left = np.zeros(n, dtype=np.float32)
    right = np.zeros(n, dtype=np.float32)
    cache: dict[tuple[str, int], np.ndarray] = {}
    for start, key, gain_db, pan in sfx_events:
        ck = (key, sr)
        if ck not in cache:
            cache[ck] = SFX_BUILDERS[key](sr)
        clip = cache[ck]
        g = 10 ** (gain_db / 20.0)
        i = int(start * sr)
        j = min(n, i + clip.size)
        if j <= i:
            continue
        seg = clip[: j - i] * g
        # panning konstan-power: SFX tersebar di bidang stereo, VO tetap di tengah
        a = clamp01((pan + 1) / 2) * math.pi / 2
        left[i:j] += seg * math.cos(a)
        right[i:j] += seg * math.sin(a)

    left *= duck_gain
    right *= duck_gain

    mix = np.stack([vo + left, vo + right], axis=1)
    mix = soft_limit(mix * 0.92, 0.68)
    mix = normalize_peak(mix, -1.2)

    loud = measure_lufs(mix.mean(axis=1), sr)
    # koreksi menuju target, dibatasi maksimum 12 dB agar tidak 'meledak'
    gain = 10 ** (max(-12.0, min(12.0, target_lufs - loud)) / 20.0)
    mix = soft_limit(mix * gain, 0.75)
    mix = normalize_peak(mix, -0.8)
    return mix.astype(np.float32)
