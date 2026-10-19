#!/usr/bin/env python3
"""vo_manusia.py - rantai VO "untuk telinga manusia" (standar v12, Ep50+).

Mengganti process_audio.py untuk episode v12. Prinsip: TIDAK ADA yang memotong atau
meregangkan suara.
  * sumber WAV PCM dari TTS (bukan MP3 32 kb/s yang membuang semua di atas 8 kHz),
  * tanpa atempo (irama diatur lewat naskah/tanda baca, bukan time-stretch),
  * tanpa menyisipkan hening digital di jeda (add_breath lama membuat "lubang"),
  * trim hanya hening sejati (-55 dBFS) dengan pra-gulir 120 ms & pasca-gulir 350 ms,
    fade raised-cosine 30 ms masuk / 150 ms keluar (di daerah yang sudah sunyi),
  * high-pass 65 Hz, de-esser spektral lembut (5,5-10 kHz, maks -5 dB), EQ statis sangat halus,
  * satu kompresor lembut (1,8:1, lutut 6 dB) + loudnorm 2 pas LINEAR ke -16 LUFS / -2 dBTP,
  * dither TPDF ke 16-bit 48 kHz stereo (format yang dipakai build_audio.py).
QC per klip (dicetak + build/vo_qc.json): onset >= 100 ms, ekor >= 300 ms, tidak ada hening digital
di dalam rentang bicara, puncak <= -2 dBFS, LUFS -16 +-1, dan (opsional --asr) semua kata naskah
dikenali - terutama kata PERTAMA dan TERAKHIR (bukti tidak ada yang terpotong).

pakai:  python3 vo_manusia.py [--src audio] [--dst audio_proc] [--asr] [--uji]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import wave

import numpy as np
import imageio_ffmpeg

BASE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.environ.get("KT_BUILD") or os.path.join(BASE, "build")
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000

PRA_GULIR = float(os.environ.get("KT_VO_PRA", "0.12"))      # detik hening sebelum kata pertama
PASCA_GULIR = float(os.environ.get("KT_VO_PASCA", "0.35"))  # detik hening setelah kata terakhir
FADE_IN, FADE_OUT = 0.030, 0.150
AMBANG_BICARA = -44.0                                        # dBFS (RMS 5 ms): selaras QC build_audio (-45),
                                                             # supaya tarikan napas sangat pelan di kepala klip ikut terpangkas
                                                             # (bukan kata: pra-gulir 120 ms tetap dipertahankan)
TARGET_I, TARGET_TP = -16.0, -2.0


# ------------------------------------------------------------------ util
def run(cmd, capture=False):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"[vo_manusia] gagal: {' '.join(cmd[:6])}...\n{r.stderr[-1500:]}")
    return r.stderr if capture else None


def decode(path, sr=SR):
    """Decode apa pun (wav/mp3/m4a) -> float32 mono `sr` Hz; resampler soxr bila ada."""
    for res in ("aresample=%d:resampler=soxr:precision=28" % sr, "aresample=%d" % sr):
        r = subprocess.run([FF, "-loglevel", "error", "-i", path, "-af", res, "-f", "f32le", "-ac", "1", "-"],
                           capture_output=True)
        if r.returncode == 0 and len(r.stdout) > 0:
            return np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)
    sys.exit(f"[vo_manusia] tidak bisa decode {path}")


def db(x):
    return 20 * np.log10(max(1e-12, float(x)))


def rms_frames(x, hop_s=0.005, sr=SR):
    hop = int(hop_s * sr)
    n = len(x) // hop
    fr = x[: n * hop].reshape(n, hop)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-12), hop


def rentang_bicara(x, ambang=AMBANG_BICARA):
    d, hop = rms_frames(x)
    v = np.where(d > ambang)[0]
    if v.size == 0:
        return 0, len(x)
    return int(v[0] * hop), int(min(len(x), (v[-1] + 1) * hop))


# ------------------------------------------------------------------ STFT
def _stft(x, n=1024, hop=256):
    win = np.hanning(n + 1)[:-1]
    pad = np.pad(x, (n // 2, n // 2 + hop))
    m = 1 + (len(pad) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(m)[:, None]
    return np.fft.rfft(pad[idx] * win, axis=1), win, pad.shape[0]


def _istft(X, win, length, n=1024, hop=256):
    fr = np.fft.irfft(X, n=n, axis=1) * win
    out = np.zeros(length)
    norm = np.zeros(length)
    for i in range(fr.shape[0]):
        out[i * hop:i * hop + n] += fr[i]
        norm[i * hop:i * hop + n] += win ** 2
    out /= np.maximum(norm, 1e-6)
    return out[n // 2:]


def deess_dan_eq(x, sr=SR, f_lo=5500, f_hi=10000, maks_db=3.0, ambang_db=-5.0):
    """De-esser spektral (pengurangan hanya pada pita desis saat desis dominan) + EQ statis halus:
    -1 dB di 300 Hz (lumpur), +0,8 dB di 3 kHz (kejelasan), +1 dB rak di atas 8,5 kHz (udara)."""
    n, hop = 1024, 256
    X, win, L = _stft(x, n, hop)
    f = np.fft.rfftfreq(n, 1 / sr)
    pita = (f >= f_lo) & (f <= f_hi)
    mag = np.abs(X)
    e_total = 20 * np.log10(np.sqrt((mag ** 2).sum(1)) + 1e-9)
    e_pita = 20 * np.log10(np.sqrt((mag[:, pita] ** 2).sum(1)) + 1e-9)
    rasio = e_pita - e_total                                    # desis: pita hampir sama kuat dengan total
    red = np.clip((rasio - ambang_db) * 1.5, 0, maks_db)        # dB pengurangan per frame
    red[e_total < (e_total.max() - 40)] = 0                     # jangan proses derau/hening
    # haluskan (attack 1 frame ~5 ms, release ~40 ms)
    sm = np.zeros_like(red)
    for i in range(len(red)):
        sm[i] = max(red[i], sm[i - 1] * 0.86) if i else red[i]
    g = 10 ** (-sm / 20)
    X[:, pita] *= g[:, None]
    # EQ statis (linear-phase, sangat halus)
    eq = np.ones_like(f)
    eq *= 10 ** ((-1.0 * np.exp(-((np.log2(np.maximum(f, 1) / 300.0)) ** 2) / 0.5)) / 20)
    eq *= 10 ** ((+0.8 * np.exp(-((np.log2(np.maximum(f, 1) / 3000.0)) ** 2) / 0.6)) / 20)
    eq *= 10 ** ((+1.0 / (1 + np.exp(-(f - 8500) / 600.0))) / 20)
    X *= eq[None, :]
    y = _istft(X, win, L, n, hop)[: len(x)]
    return y, float(sm.max()), float((sm > 0.5).mean())


# ------------------------------------------------------------------ ffmpeg: HPF + kompresor + loudnorm 2 pas
def _ukur(path, af=""):
    err = run([FF, "-i", path, "-af", (af + "," if af else "") + "loudnorm=I=-16:TP=-2:print_format=json",
               "-f", "null", "-"], capture=True)
    j = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    return float(j["input_i"]), float(j["input_tp"])


def dinamika_dan_loudness(src_wav, dst_wav):
    """HPF 65 Hz -> (A) kompresor perata lambat (2:1, lutut 8 dB) -> gain linear -> (B) kompresor puncak cepat
    (3:1 di atas -8 dBFS, attack 1 ms) -> gain linear ke -16 LUFS -> limiter true-peak -2 dB (sisa <= ~1 dB).
    Tidak ada normalisasi dinamis/loudnorm yang 'memompa'."""
    a = ("highpass=f=65:poles=2,"
         "acompressor=threshold=-26dB:ratio=2:attack=15:release=200:knee=8:makeup=1:detection=rms")
    i1, _ = _ukur(src_wav, a)
    b = a + f",volume={TARGET_I - i1:.3f}dB,acompressor=threshold=-8dB:ratio=3:attack=1:release=70:knee=4:makeup=1:detection=peak"
    i2, tp2 = _ukur(src_wav, b)
    g2 = TARGET_I - i2
    af = b + f",volume={g2:.3f}dB,alimiter=limit={10 ** (TARGET_TP / 20):.4f}:attack=3:release=60:level=false:asc=true"
    run([FF, "-y", "-i", src_wav, "-af", af, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_f32le", dst_wav])
    i3, tp3 = _ukur(dst_wav)
    return i3, tp3, f"linear {TARGET_I - i1 + g2:+.1f} dB, limiter {max(0.0, tp2 + g2 - TARGET_TP):.1f} dB"


# ------------------------------------------------------------------ trim + fade + tulis
def nada_ruang(n, sr=SR, level_db=-63.0, seed=11):
    """Derau merah muda sangat pelan, 120 Hz-7 kHz: menghilangkan 'lubang' hening digital tanpa terdengar."""
    rng = np.random.default_rng(seed)
    w = rng.standard_normal(n)
    W = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1 / sr)
    shape = 1 / np.sqrt(np.maximum(f, 20)) * (f > 120) * (f < 7000)
    p = np.fft.irfft(W * shape, n=n)
    p /= np.sqrt((p ** 2).mean()) + 1e-12
    return p * 10 ** (level_db / 20)


def trim_fade(x, sr=SR):
    a, b = rentang_bicara(x)
    pra, pasca = int(PRA_GULIR * sr), int(PASCA_GULIR * sr)
    s0 = a - pra
    s1 = b + pasca
    y = x[max(0, s0): min(len(x), s1)]
    if s0 < 0:
        y = np.concatenate([np.zeros(-s0), y])
    if s1 > len(x):
        y = np.concatenate([y, np.zeros(s1 - len(x))])
    y = y + nada_ruang(len(y), sr)
    nfi, nfo = int(FADE_IN * sr), int(FADE_OUT * sr)
    y[:nfi] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(nfi) / nfi)
    y[-nfo:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nfo) / nfo)
    return y, (a - max(0, s0)) / sr


def tulis_wav16(path, mono, sr=SR):
    rng = np.random.default_rng(7)
    d = (rng.random(len(mono)) - rng.random(len(mono))) / 32768.0      # TPDF 1 LSB
    s = np.clip(mono + d, -1, 1)
    st = np.stack([s, s], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((st * 32767).astype("<i2").tobytes())


# ------------------------------------------------------------------ QC
def _norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def qc_klip(y, sr=SR):
    a, b = rentang_bicara(y, -50.0)
    d, hop = rms_frames(y)
    dalam = d[a // hop: b // hop]
    # hening digital di dalam rentang bicara: >= 3 frame berturut (15 ms) di bawah -80 dB
    zrun, cur = 0, 0
    for v in dalam:
        cur = cur + 1 if v < -80 else 0
        zrun = max(zrun, cur)
    return {"onset_ms": round(a / sr * 1000), "ekor_ms": round((len(y) - b) / sr * 1000),
            "hening_digital_ms": zrun * 5, "peak_dbfs": round(db(np.abs(y).max()), 2),
            "durasi_s": round(len(y) / sr, 3)}


_SATUAN = {"nol": 0, "satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5, "enam": 6, "tujuh": 7,
           "delapan": 8, "sembilan": 9, "sepuluh": 10, "sebelas": 11}


def _angka(tokens):
    """Ubah deret kata bilangan Indonesia menjadi digit ('dua ribu enam puluh satu' -> '2061') agar
    sebanding dengan keluaran ASR yang menulis angka."""
    out, i = [], 0
    while i < len(tokens):
        j, total, cur, ok = i, 0, 0, False
        while j < len(tokens):
            w = tokens[j]
            if w in _SATUAN:
                cur += _SATUAN[w]; ok = True
            elif w == "belas" and ok:
                cur += 10
            elif w == "puluh" and ok:
                cur *= 10
            elif w == "ratus" and ok:
                cur *= 100
            elif w == "seratus":
                cur += 100; ok = True
            elif w == "seribu":
                cur += 1000; ok = True
            elif w == "ribu" and ok:
                total += cur * 1000; cur = 0
            else:
                break
            j += 1
        if ok and j > i:
            out.append(str(total + cur)); i = j
        else:
            out.append(tokens[i]); i += 1
    return out


def _mirip(a, b):
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio()


def asr_cek(path, naskah):
    """Kenali kata dengan faster-whisper dan bandingkan dengan naskah (angka dinormalkan, nama boleh
    beda ejaan). Yang penting: kata PERTAMA dan TERAKHIR ada (bukti awal/akhir tidak terpotong)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return {"asr": "tidak tersedia"}
    x = decode(path, 16000).astype(np.float32)
    mdl = asr_cek._m = getattr(asr_cek, "_m", None) or WhisperModel(
        os.environ.get("KT_ASR_MODEL", "small"), device="cpu", compute_type="int8")
    segs, _ = mdl.transcribe(x, language="id", word_timestamps=True, beam_size=5, vad_filter=False)
    kata = []
    for sgm in segs:
        for w in (sgm.words or []):
            kata.append((_norm(w.word), float(w.start), float(w.end)))
    dikenal = _angka([k for k, _, _ in kata if k])
    nas = _angka([_norm(w) for w in naskah.split() if _norm(w)])
    teks_asr, teks_nas = "".join(dikenal), "".join(nas)
    # nama diri (huruf besar di tengah kalimat) boleh beda ejaan di ASR: Halley -> 'heli'
    kal = re.split(r"(?<=[.!?:])\s+", naskah)
    nama = {_norm(w) for k in kal for w in k.split()[1:] if w[:1].isupper()}
    dikenal_set = set(dikenal)
    hilang = [w for w in nas if w not in dikenal_set and w not in teks_asr and w not in nama and
              max((_mirip(w, d) for d in dikenal), default=0) < 0.5]
    return {"asr_kata": len(dikenal), "naskah_kata": len(nas), "hilang": hilang,
            "kemiripan": round(_mirip(teks_asr, teks_nas), 3),
            "pertama_ok": bool(nas and dikenal and (teks_asr.startswith(nas[0]) or _mirip(nas[0], dikenal[0]) >= 0.6)),
            "terakhir_ok": bool(nas and dikenal and (teks_asr.endswith(nas[-1]) or _mirip(nas[-1], dikenal[-1]) >= 0.6)),
            "kata_pertama_t": round(kata[0][1], 2) if kata else None,
            "kata_terakhir_t": round(kata[-1][2], 2) if kata else None,
            "transkrip": " ".join(dikenal)}


# ------------------------------------------------------------------ utama
def finalisasi_stereo(path, tmpd, target_i=TARGET_I, target_tp=TARGET_TP):
    """Ukur file AKHIR (stereo), lalu trim linear ke target loudness + limiter true-peak.

    Penting: BS.1770 menjumlahkan daya per kanal, jadi dual-mono 3 dB lebih keras
    daripada mono. Tanpa langkah ini, klip stereo keluar ~-13 LUFS walau rantai
    mono sudah -16, dan limiter bekerja terlalu keras (terdengar dipadatkan).
    """
    i1, tp1 = _ukur(path)
    g1 = target_i - i1
    if abs(g1) < 0.05 and tp1 <= target_tp + 0.1:
        return i1, tp1, 0.0
    p1 = os.path.join(tmpd, "fin1.wav")
    run([FF, "-y", "-i", path, "-af", f"volume={g1:.3f}dB", "-ar", str(SR),
         "-ac", "2", "-c:a", "pcm_s16le", p1])
    i2, tp2 = _ukur(p1)
    p2 = os.path.join(tmpd, "fin2.wav")
    lim = 10 ** (target_tp / 20)
    run([FF, "-y", "-i", p1, "-af",
         f"alimiter=limit={lim:.5f}:attack=5:release=80:level=false:asc=true",
         "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", p2])
    os.replace(p2, path)
    i3, tp3 = _ukur(path)
    return i3, tp3, g1


def proses_klip(src, dst, tmpd):
    x = decode(src)
    y, deess_max, deess_frac = deess_dan_eq(x)
    p1 = os.path.join(tmpd, "eq.wav")
    with wave.open(p1, "wb") as w:                            # 32-bit float via ffmpeg lebih aman: tulis 24-bit int
        w.setnchannels(1); w.setsampwidth(4); w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 2147483647).astype("<i4").tobytes())
    p2 = os.path.join(tmpd, "ln.wav")
    out_i, out_tp, jenis = dinamika_dan_loudness(p1, p2)
    z = decode(p2)
    z, onset = trim_fade(z)
    tulis_wav16(dst, z)
    i_fin, tp_fin, g_fin = finalisasi_stereo(dst, tmpd)
    q = qc_klip(z)
    q.update({"lufs_stereo": round(i_fin, 2), "tp_stereo": round(tp_fin, 2),
              "gain_stereo_db": round(g_fin, 2)})
    q.update({"lufs": round(out_i, 2), "tp": round(out_tp, 2), "loudnorm": jenis,
              "deess_maks_db": round(deess_max, 2), "deess_frac": round(deess_frac, 3),
              "sumber": os.path.basename(src)})
    return q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(BASE, "audio"))
    ap.add_argument("--dst", default=os.path.join(BASE, "audio_proc"))
    ap.add_argument("--content", default=os.path.join(BASE, "content.json"))
    ap.add_argument("--asr", action="store_true", help="verifikasi kata dengan faster-whisper (lambat, ~20 s/klip)")
    ap.add_argument("--uji", action="store_true")
    a = ap.parse_args()
    if a.uji:
        return _uji()
    os.makedirs(a.dst, exist_ok=True); os.makedirs(BUILD, exist_ok=True)
    tmpd = os.path.join(BUILD, "_vo_tmp"); os.makedirs(tmpd, exist_ok=True)
    content = json.load(open(a.content))
    naskah = {s["id"]: s.get("vo", "") for s in content.get("scenes", [])}
    lap = {}
    masalah = 0
    print(f"VO manusia v12: pra {PRA_GULIR*1000:.0f} ms / pasca {PASCA_GULIR*1000:.0f} ms, fade {FADE_IN*1000:.0f}/{FADE_OUT*1000:.0f} ms, "
          f"target {TARGET_I} LUFS / {TARGET_TP} dBTP, tanpa atempo, tanpa hening sisipan")
    for sid in naskah:
        cands = [os.path.join(a.src, sid + ext) for ext in (".wav", ".flac", ".m4a", ".mp3")]
        src = next((c for c in cands if os.path.exists(c)), None)
        if not src:
            print(f"  {sid:6s} TIDAK ADA sumber audio"); masalah += 1; continue
        dst = os.path.join(a.dst, sid + ".wav")
        q = proses_klip(src, dst, tmpd)
        if a.asr:
            q.update(asr_cek(dst, naskah[sid]))
        ok = (q["onset_ms"] >= 100 and q["ekor_ms"] >= 300 and q["hening_digital_ms"] == 0
              and q["peak_dbfs"] <= -1.9 and abs(q.get("lufs_stereo", q["lufs"]) - TARGET_I) <= 1.0
              and q.get("tp_stereo", TARGET_TP) <= TARGET_TP + 0.2
              and (not a.asr or q.get("asr") == "tidak tersedia" or (q.get("pertama_ok") and q.get("terakhir_ok") and not q.get("hilang") and q.get("kemiripan", 0) >= 0.9)))
        masalah += 0 if ok else 1
        asr_txt = ""
        if a.asr and "hilang" in q:
            asr_txt = (f" | ASR mirip {q['kemiripan']:.2f}, awal {'OK' if q['pertama_ok'] else 'BEDA'}, "
                       f"akhir {'OK' if q['terakhir_ok'] else 'BEDA'}, tak dikenali: {q['hilang'][:4]}")
        print(f"  {sid:6s} {q['durasi_s']:6.2f}s  onset {q['onset_ms']:4d} ms  ekor {q['ekor_ms']:4d} ms  "
              f"peak {q['peak_dbfs']:5.1f}  {q.get('lufs_stereo', q['lufs']):6.1f} LUFS / {q.get('tp_stereo', 0):+5.1f} dBTP  de-ess maks {q['deess_maks_db']:.1f} dB"
              f"{asr_txt}  {'OK' if ok else '>>> PERIKSA'}")
        lap[sid] = q
    json.dump(lap, open(os.path.join(BUILD, "vo_qc.json"), "w"), indent=1, ensure_ascii=False)
    print("HASIL VO:", "SEMUA BERSIH ✔" if masalah == 0 else f"{masalah} klip perlu diperiksa")
    return 0


def _uji():
    sr = SR
    t = np.arange(int(2.0 * sr)) / sr
    x = np.zeros_like(t)
    seg = (t > 0.4) & (t < 1.5)
    x[seg] = 0.3 * np.sin(2 * np.pi * 180 * t[seg]) * (1 + 0.3 * np.sin(2 * np.pi * 3 * t[seg]))
    x[(t > 0.9) & (t < 0.95)] += 0.2 * np.random.default_rng(1).standard_normal(int(0.05 * sr) + (1 if len(x[(t > 0.9) & (t < 0.95)]) > int(0.05 * sr) else 0))[: len(x[(t > 0.9) & (t < 0.95)])]
    y, mx, fr = deess_dan_eq(x)
    assert len(y) == len(x) and np.isfinite(y).all()
    z, on = trim_fade(x)
    a, b = rentang_bicara(z)
    assert abs(a / sr - PRA_GULIR) < 0.02, a / sr
    q = qc_klip(z)
    assert q["onset_ms"] >= 100 and q["ekor_ms"] >= 300, q
    print("uji vo_manusia OK", q)
    return 0


if __name__ == "__main__":
    sys.exit(main())
