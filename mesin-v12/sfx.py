#!/usr/bin/env python3
"""SFX v11 — efek suara SINTETIS (tanpa file sampel, tanpa lisensi, tanpa musik).

Semua bunyi dibuat dengan numpy (derau terfilter, sapuan frekuensi, envelope), lalu
diletakkan tepat pada event dari mesin_v11.events(scenes) — sumber yang SAMA dengan
animasi & dorongan kamera, jadi bunyi selalu jatuh di frame elemen muncul.

Dipanggil oleh master_audio.py SETELAH VO dimaster (-14 LUFS):
  * level SFX dasar -16 dB di bawah skala penuh (terasa, tidak menutupi suara)
  * ducking otomatis: saat narator bicara SFX turun ~7 dB (sidechain envelope VO)
  * limiter puncak akhir supaya tetap <= -1.2 dBFS
Episode lama (tanpa visual/transisi v11) -> tidak ada event -> audio identik seperti dulu.

  python3 sfx.py            # uji: bangkitkan semua bunyi -> build/sfx_katalog.wav
"""
import math, os, wave
import numpy as np

SR = 48000
RNG = np.random.default_rng(42)


def _t(d):
    return np.arange(int(SR * d)) / SR


def _env(n, a=0.004, dec=0.2, curve=1.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(1e-4, a)) * np.exp(-np.maximum(0, t - a) / max(1e-3, dec))
    return e ** curve


def _lp(x, fc):
    """Low-pass 1 kutub (bisa fc berubah per-sampel)."""
    fc = np.broadcast_to(np.asarray(fc, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def _bp(x, fc, q=2.0):
    """Band-pass sederhana: selisih dua low-pass."""
    fc = np.asarray(fc, dtype=float)
    return _lp(x, fc * (1 + 0.5 / q)) - _lp(x, fc * (1 - 0.5 / q))


def _noise(d):
    return RNG.standard_normal(int(SR * d))


def _norm(x, pk=0.9):
    m = np.abs(x).max() + 1e-9
    return x / m * pk


# ------------------------------------------------------------------ katalog bunyi
def whoosh(d=0.42):
    n = int(SR * d)
    u = np.linspace(0, 1, n)
    fc = 300 + 3200 * np.sin(np.pi * u) ** 1.5
    x = _bp(_noise(d), fc, 1.4)
    env = np.sin(np.pi * u ** 0.8) ** 2
    return _norm(x * env, 0.8)


def swish(d=0.22):
    n = int(SR * d)
    u = np.linspace(0, 1, n)
    x = _bp(_noise(d), 1800 + 5200 * u, 1.8)
    return _norm(x * np.sin(np.pi * u) ** 1.5, 0.65)


def swish_up(d=0.30):
    n = int(SR * d)
    u = np.linspace(0, 1, n)
    x = _bp(_noise(d), 900 + 4500 * u ** 2, 2.2)
    tone = np.sin(2 * np.pi * np.cumsum(500 + 900 * u) / SR) * 0.25
    return _norm((x + tone) * np.sin(np.pi * u) ** 2, 0.55)


def pop(d=0.11):
    t = _t(d)
    f = 1100 * np.exp(-t * 38) + 380
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return _norm(x * _env(len(t), 0.001, 0.035), 0.75)


def tick(d=0.05):
    t = _t(d)
    x = np.sin(2 * np.pi * 2400 * t) + 0.4 * _noise(d)
    return _norm(x * _env(len(t), 0.0005, 0.010), 0.5)


def click(d=0.06):
    t = _t(d)
    x = _bp(_noise(d), 3500, 1.2) + 0.6 * np.sin(2 * np.pi * 1600 * t)
    return _norm(x * _env(len(t), 0.0005, 0.012), 0.6)


def impact(d=0.75):
    t = _t(d)
    f = 150 * np.exp(-t * 9) + 42
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.002, 0.28)
    crack = _lp(_noise(d), 2600) * _env(len(t), 0.001, 0.045)
    return _norm(sub + 0.55 * crack, 0.95)


def thud(d=0.35):
    t = _t(d)
    f = 110 * np.exp(-t * 14) + 50
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.002, 0.10)
    x += 0.3 * _lp(_noise(d), 700) * _env(len(t), 0.001, 0.03)
    return _norm(x, 0.8)


def boom(d=1.3):
    t = _t(d)
    f = 70 * np.exp(-t * 3) + 32
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.004, 0.55)
    x += 0.5 * _lp(_noise(d), 380) * _env(len(t), 0.003, 0.35)
    return _norm(x, 0.95)


def riser(d=1.1):
    n = int(SR * d)
    u = np.linspace(0, 1, n)
    x = _bp(_noise(d), 400 + 5000 * u ** 2, 2.5)
    tone = np.sin(2 * np.pi * np.cumsum(220 + 660 * u ** 2) / SR) * 0.35
    return _norm((x + tone) * u ** 2.2 * (1 - np.exp(-(1 - u) * 60)), 0.7)


def ding(d=0.7):
    t = _t(d)
    x = (np.sin(2 * np.pi * 1320 * t) + 0.45 * np.sin(2 * np.pi * 2640 * t) +
         0.2 * np.sin(2 * np.pi * 3960 * t))
    return _norm(x * _env(len(t), 0.002, 0.22), 0.5)


def glitch(d=0.28):
    n = int(SR * d)
    x = np.zeros(n)
    pos = 0
    while pos < n:
        ln = int(RNG.integers(int(SR * 0.008), int(SR * 0.035)))
        f = float(RNG.choice([180, 420, 900, 1800, 3200]))
        seg = np.sign(np.sin(2 * np.pi * f * np.arange(ln) / SR))
        if RNG.random() < 0.35:
            seg = RNG.standard_normal(ln)
        x[pos:pos + ln] = seg[: max(0, min(ln, n - pos))] * (0.3 + 0.7 * RNG.random())
        pos += ln
    x = np.round(x * 6) / 6
    return _norm(_lp(x, 6000), 0.5)


def zap(d=0.35):
    t = _t(d)
    f = 2400 * np.exp(-t * 10) + 200
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + 0.5 * _bp(_noise(d), 2500, 1)
    return _norm(_lp(x, 5000) * _env(len(t), 0.001, 0.12), 0.45)


def door(d=0.5):
    t = _t(d)
    slide = _bp(_noise(d), 900, 1.5) * np.clip(1 - t / 0.35, 0, 1) * 0.5
    hit = np.zeros_like(t)
    k = int(SR * 0.33)
    th = thud(d - 0.33)[: len(t) - k]
    hit[k:k + len(th)] = th
    return _norm(slide + hit, 0.8)


def nging(d=1.6):
    """Tinnitus sebentar: nada tinggi 6,2 kHz naik cepat, sedikit vibrato, memudar pelan."""
    t = _t(d)
    f = 6200 + 40 * np.sin(2 * np.pi * 5.5 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR)
    env = np.minimum(1.0, t / 0.05) * np.exp(-t / 0.55)
    return _norm(x * env, 0.35)


def retak(d=0.9):
    """Retakan menjalar: rentetan klik kering acak yang makin rapat lalu reda (lava/lumpur retak)."""
    n = int(SR * d)
    x = np.zeros(n)
    rng = np.random.default_rng(7)
    t = 0.0
    while t < d - 0.03:
        i = int(t * SR)
        ln = int(SR * rng.uniform(0.004, 0.012))
        c = _bp(rng.standard_normal(ln), float(rng.uniform(1800, 4200)), 1.5) * _env(ln, 0.0003, 0.004)
        x[i:i + ln] += c[: n - i] * rng.uniform(0.4, 1.0)
        t += rng.uniform(0.012, 0.06) * (0.6 + 0.8 * t / d)
    x += 0.25 * _lp(_noise(d), 500) * _env(n, 0.01, 0.3)
    return _norm(x, 0.6)


def kecapi(d=1.4):
    """Batu kecapi dipukul: litofon - parsial tak harmonis (batu), serangan keras, gaung pendek."""
    t = _t(d)
    parts = [(440, 1.0, 0.45), (1187, 0.55, 0.25), (2290, 0.30, 0.12), (3710, 0.15, 0.06)]
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / dec) for f, a, dec in parts)
    x += 0.35 * _bp(_noise(d), 2500, 1.2) * _env(len(t), 0.0005, 0.01)
    return _norm(x, 0.6)



def kilau(d=0.9):
    """Kilau cahaya: arpeggio nada tinggi lembut (sparkle) - cahaya menyebar/bintang muncul."""
    t = _t(d)
    x = np.zeros_like(t)
    for i, f in enumerate((2093, 2637, 3136, 3951, 4186)):
        t0 = i * 0.055
        m = t >= t0
        tt = t[m] - t0
        x[m] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.18) * (1 - i * 0.12)
    return _norm(x, 0.45)


def gelembung(d=0.8):
    """Gelembung air: 6 'blup' pendek bernada naik acak (bawah laut)."""
    t = _t(d)
    x = np.zeros_like(t)
    rng = np.random.default_rng(46)
    for i in range(6):
        t0 = i * 0.09 + rng.uniform(0, 0.03)
        f0 = rng.uniform(380, 900)
        m = t >= t0
        tt = t[m] - t0
        f = f0 * (1 + 2.2 * tt / 0.06)
        x[m] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.035) * (1 - i * 0.1)
    return _norm(x, 0.5)


def gigit(d=0.45):
    """Gigitan rahang: dua 'clack' keras (gigi beradu) + denyut rendah pendek."""
    t = _t(d)
    x = np.zeros_like(t)
    for t0, g in ((0.0, 1.0), (0.07, 0.8)):
        m = t >= t0
        tt = t[m] - t0
        x[m] += g * _bp(_noise(d)[: m.sum()], 1800, 1.5) * np.exp(-tt / 0.012)
        x[m] += 0.6 * g * np.sin(2 * np.pi * 110 * tt) * np.exp(-tt / 0.06)
    return _norm(x, 0.8)



def guntur(d=2.2):
    """Guntur: retakan tajam di awal lalu gemuruh rendah bergulung yang memudar pelan."""
    t = _t(d)
    n = len(t)
    crack = _bp(_noise(d), 2400, 1.2) * _env(n, 0.001, 0.05)
    rng = np.random.default_rng(47)
    am = np.ones(n)
    for k in range(7):
        c = rng.uniform(0.1, 1.6)
        am += 0.8 * np.exp(-((t - c) / 0.12) ** 2)
    rumble = _lp(_noise(d), 160) * am * _env(n, 0.06, 0.9)
    x = 0.6 * crack / (np.abs(crack).max() + 1e-9) + rumble / (np.abs(rumble).max() + 1e-9)
    return _norm(x, 0.85)


def detak(d=0.62):
    """Detak jantung 'lub-dub': dua dentum rendah berdekatan (yang kedua lebih pendek & pelan)."""
    t = _t(d)
    n = len(t)
    x = np.zeros(n)
    for t0, f0, amp, dec in ((0.0, 62, 1.0, 0.075), (0.24, 74, 0.7, 0.055)):
        tt = np.clip(t - t0, 0, None)
        on = (t >= t0).astype(float)
        f = f0 * (1 + 0.5 * np.exp(-tt * 40))
        ph = 2 * np.pi * np.cumsum(f * on) / SR
        x += amp * on * np.sin(ph) * np.exp(-tt / dec) * np.minimum(1.0, tt / 0.004)
    x += 0.12 * _lp(_noise(d), 300) * _env(n, 0.002, 0.04)
    return _norm(x, 0.85)



def laser(d=0.9):
    """Laser pemandu: dengung sinus menyapu turun + harmonik tipis + denyut cepat (sci-fi halus)."""
    t = _t(d)
    f = 1400 * np.exp(-t * 2.2) + 380
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3.01 * ph)
    x *= (0.75 + 0.25 * np.sin(2 * np.pi * 38 * t)) * _env(len(t), 0.01, d * 0.55)
    return _norm(x, 0.5)


def angin(d=1.2):
    """Hembusan angin: derau bandpass yang naik-turun pelan (udara bergerak)."""
    t = _t(d)
    n = _noise(d)
    x = _bp(n, 700, 1.2) * 0.7 + _lp(n, 350) * 0.5
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5 * (0.8 + 0.2 * np.sin(2 * np.pi * 2.3 * t))
    return _norm(x * env, 0.6)


# ------------------------------------------------------------------ v12 (standar KONTINUITAS)
def morph(d=0.46):
    """Perubahan bentuk: sapuan derau halus + glide sinus 320->620 Hz (bukan nada musikal, sekali lewat)."""
    t = _t(d)
    u = t / d
    f = 320 + 300 * np.sin(np.pi * u / 2) ** 1.5
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = 0.55 * np.sin(ph) * np.exp(-((u - 0.45) / 0.30) ** 2)
    x += 0.7 * _bp(_noise(d), 900 + 1800 * np.sin(np.pi * u), 1.1) * np.sin(np.pi * u) ** 1.4
    return _norm(x, 0.7)


def burn(d=0.62):
    """Meteor terbakar: desis derau band-pass turun 7 kHz -> 1,2 kHz dengan ekor memudar."""
    t = _t(d)
    u = t / d
    fc = 1200 + 5800 * (1 - u) ** 1.6
    x = _bp(_noise(d), fc, 1.6)
    env = np.minimum(1.0, t / 0.02) * (1 - u) ** 1.3
    return _norm(x * env, 0.8)


def thump(d=0.55):
    """Hentakan rendah 70 -> 48 Hz (payoff micro-climax) + klik transien halus."""
    t = _t(d)
    f = 48 + 22 * np.exp(-t / 0.09)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.16)
    x += 0.25 * _lp(_noise(d), 1800) * np.exp(-t / 0.012)
    return _norm(x, 0.9)


def angin_malam(d=8.0, seed=5):
    """Tekstur ambient malam (bukan musik): derau sangat lembut yang bernapas pelan, untuk bed -32 dB."""
    rng = np.random.default_rng(seed)
    n = int(SR * d)
    t = np.arange(n) / SR
    x = _lp(rng.standard_normal(n), 420) * 0.8 + _bp(rng.standard_normal(n), 900, 0.9) * 0.25
    napas = 0.75 + 0.25 * np.sin(2 * np.pi * 0.09 * t) * np.sin(2 * np.pi * 0.031 * t + 1.0)
    return _norm(x * napas, 0.6)


def ambient_bed(total, db=-32.0, fade=0.02, seed=5):
    """Bed ambient sepanjang `total` detik: potongan 8 s disambung crossfade 0,5 s; level sama di
    awal & akhir (loop mulus), fade zero-ish 20 ms di kedua ujung."""
    seg_ = angin_malam(8.0, seed)
    n = int(SR * total)
    out = np.zeros(n + len(seg_))
    xf = int(SR * 0.5)
    pos = 0
    k = 0
    while pos < n:
        chunk = seg_.copy() if k % 2 == 0 else seg_[::-1].copy()
        if pos > 0:
            ramp = np.linspace(0, 1, xf)
            chunk[:xf] *= ramp
            out[pos:pos + xf] *= (1 - ramp)
        out[pos:pos + len(chunk)] += chunk
        pos += len(chunk) - xf
        k += 1
    out = out[:n] * (10 ** (db / 20))
    nf = int(SR * fade)
    out[:nf] *= np.linspace(0, 1, nf)
    out[-nf:] *= np.linspace(1, 0, nf)
    return out


KATALOG = {"whoosh": whoosh, "swish": swish, "swish_up": swish_up, "pop": pop, "tick": tick,
           "click": click, "impact": impact, "thud": thud, "boom": boom, "riser": riser,
           "ding": ding, "glitch": glitch, "zap": zap, "door": door, "nging": nging,
           "retak": retak, "kecapi": kecapi, "kilau": kilau,
           "gelembung": gelembung, "gigit": gigit, "guntur": guntur, "detak": detak,
           "laser": laser, "angin": angin,
           "morph": morph, "burn": burn, "thump": thump}
# level relatif (dB) supaya campuran seimbang
LEVEL = {"whoosh": -3, "swish": -4, "swish_up": -8, "pop": -5, "tick": -9, "click": -7,
         "impact": 0, "thud": -3, "boom": -1, "riser": -6, "ding": -8, "glitch": -7,
         "zap": -9, "door": -4, "nging": -14, "retak": -8, "kecapi": -6, "kilau": -7,
         "gelembung": -9, "gigit": -4, "guntur": -3, "detak": -2,
         "laser": -9, "angin": -8,
         "morph": -7, "burn": -4, "thump": 0}
_CACHE = {}


def bunyi(nama):
    if nama not in _CACHE:
        _CACHE[nama] = KATALOG[nama]().astype(np.float64)
    return _CACHE[nama]


def lapisan(events, total, base_db=-16.0):
    """Array mono float (panjang total detik) berisi semua SFX."""
    n = int(SR * (total + 1.5))
    out = np.zeros(n)
    for t, nama, g in events:
        if nama not in KATALOG:
            continue
        s = bunyi(nama) * (10 ** ((base_db + LEVEL.get(nama, -6)) / 20)) * g
        i = int(t * SR)
        if i >= n or i + len(s) <= 0:
            continue
        a, b = max(0, i), min(n, i + len(s))
        out[a:b] += s[a - i:b - i]
    return out


def duck(sfx, vo, depth_db=-7.0, win=0.12):
    """Sidechain: turunkan SFX saat VO bersuara (envelope RMS VO)."""
    m = min(len(sfx), len(vo))
    k = int(SR * win)
    e = np.sqrt(np.convolve(vo[:m] ** 2, np.ones(k) / k, mode="same"))
    aktif = np.clip((20 * np.log10(e + 1e-9) + 42) / 12, 0, 1)      # 0 hening .. 1 bicara
    g = 10 ** (depth_db * aktif / 20)
    sfx = sfx.copy()
    sfx[:m] *= g
    return sfx


def _tulis(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    bdir = os.environ.get("KT_BUILD") or os.path.join(base, "build")
    os.makedirs(bdir, exist_ok=True)
    ev = [(0.3 + i * 1.1, k, 1.0) for i, k in enumerate(KATALOG)]
    x = lapisan(ev, 0.3 + len(KATALOG) * 1.1, base_db=-6)
    _tulis(os.path.join(bdir, "sfx_katalog.wav"), x)
    for k in KATALOG:
        s = bunyi(k)
        assert np.isfinite(s).all() and np.abs(s).max() <= 1.0 and len(s) > 100, k
    print(f"katalog SFX: {len(KATALOG)} bunyi OK -> {bdir}/sfx_katalog.wav")


def ambient_hujan(total, level_db=-30.0, seed=5):
    """Bed HUJAN (bukan musik): derau merah berfilter + tetes-tetes pendek acak.

    Dibuat di domain frekuensi (cepat untuk 2-3 menit) lalu di-fade 0,45 s di kedua ujung
    supaya tidak ada klik saat loop video. Level RMS dijaga persis `level_db`.
    """
    n = int(SR * max(0.05, total))
    if n < 64:
        return np.zeros(max(1, n))
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    H = np.clip(f / 260.0, 0.0, 1.0) ** 0.28 * np.exp(-(f / 5200.0) ** 2)
    H *= 1.0 - 0.65 * np.exp(-(f / 90.0) ** 2)              # buang gerumuh sangat rendah
    h = np.fft.irfft(np.fft.rfft(x) * H, n)
    h /= (np.sqrt((h ** 2).mean()) + 1e-9)
    # tetes: klik pendek (10 ms) bertumpuk, jumlah ~7 per detik
    nd = int(7 * total)
    pos = rng.integers(0, max(1, n - 600), nd)
    amp = rng.uniform(0.15, 1.0, nd) ** 2
    for k, p0 in enumerate(pos):
        m = int(SR * 0.010)
        env = np.exp(-np.arange(m) / (SR * 0.0022)) * amp[k]
        h[p0:p0 + m] += rng.standard_normal(m) * env * 0.55
    h /= (np.sqrt((h ** 2).mean()) + 1e-9)
    h *= 10 ** (level_db / 20.0)
    fade = int(SR * 0.45)
    if len(h) > 2 * fade:
        h[:fade] *= np.linspace(0, 1, fade) ** 1.6
        h[-fade:] *= np.linspace(1, 0, fade) ** 1.6
    return h


def ambient_laut(total, level_db=-31.0, seed=13):
    """Bed LAUT DALAM (bukan musik): gerumuh tekanan rendah + napas arus lambat + desis partikel.

    Dibuat di domain frekuensi supaya murah untuk 2-3 menit. Tiga lapis:
      1) rumble < 80 Hz  (tekanan kedalaman)
      2) arus 120-600 Hz yang menguat-mengecil tiap ~7 s (napas samudra)
      3) desis 2-6 kHz sangat tipis (partikel / gelembung jauh)
    Loop aman: pakai jumlah gelombang bulat dalam durasi, fade 0,4 s di ujung.
    """
    n = int(SR * max(0.05, total))
    if n < 64:
        return np.zeros(max(1, n))
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    # spektrum dasar: turun ~1/f^0.9 (derau coklat laut) + puncak tipis di 55 Hz
    H = (np.clip(f, 18.0, None) / 100.0) ** -0.9
    H[f < 18] = 0.0
    H *= 1.0 + 0.55 * np.exp(-((f - 55.0) / 16.0) ** 2)
    H *= np.exp(-(f / 4200.0) ** 2)                      # buang hiss tinggi
    laut = np.fft.irfft(np.fft.rfft(x) * H, n)
    laut /= (np.sqrt((laut ** 2).mean()) + 1e-9)
    # napas arus: gelombang utuh dalam durasi (loop mulus)
    k1 = max(1, round(total / 9.0))
    k2 = max(1, round(total / 23.0))
    napas = (0.78 + 0.16 * np.sin(2 * np.pi * k1 * t / max(total, 1e-6) - 0.6)
             + 0.06 * np.sin(2 * np.pi * k2 * t / max(total, 1e-6) + 1.7))
    # desis gelembung: derau band-pass pendek yang jarang
    hiss = np.zeros(n)
    nb = int(1.6 * total)
    pos = rng.integers(0, max(1, n - int(SR * 0.05)), nb)
    for p0 in pos:
        m = int(SR * rng.uniform(0.02, 0.05))
        if p0 + m >= n:
            continue
        env = np.exp(-np.arange(m) / (SR * 0.010))
        hiss[p0:p0 + m] += rng.standard_normal(m) * env * rng.uniform(0.05, 0.16)
    laut = laut * napas + hiss * 0.35
    laut /= (np.sqrt((laut ** 2).mean()) + 1e-9)
    laut *= 10 ** (level_db / 20.0)
    fade = int(SR * 0.40)
    if n > 2 * fade:
        laut[:fade] *= np.linspace(0, 1, fade) ** 1.4
        laut[-fade:] *= np.linspace(1, 0, fade) ** 1.4
    return laut
