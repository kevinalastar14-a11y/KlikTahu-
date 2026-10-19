#!/usr/bin/env python3
"""align_kata.py - waktu tiap KATA naskah di audio VO (standar v12: BEAT dikunci ke kata).

Hasil: build/kata.json = {id_adegan: [[kata_naskah, t_mulai, t_akhir], ...]}
       (detik relatif terhadap AWAL ADEGAN, sudah termasuk lead_in timeline).

Cara kerja:
  1. faster-whisper (CPU, int8) mentranskripsi audio_proc/<id>.wav dengan stempel waktu per kata.
  2. Kata hasil transkripsi dicocokkan ke kata naskah (urutan monoton, difflib) -> kata naskah
     yang tidak terdeteksi diinterpolasi di antara tetangganya.
  3. Kalau faster-whisper tidak tersedia -> fallback heuristik (jeda + bobot huruf, seperti
     long/mesin_long.align) supaya pipeline tetap jalan.

Pakai:  python3 align_kata.py            (butuh timeline.json + audio_proc/)
        python3 align_kata.py --uji      (selftest tanpa audio)
"""
import difflib, json, os, re, sys, wave

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.environ.get("KT_BUILD") or os.path.join(BASE, "build")
MODEL = os.environ.get("KT_WHISPER", "small")


def _norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def _read(path):
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768
        if w.getnchannels() > 1:
            a = a.reshape(-1, w.getnchannels()).mean(axis=1)
    return a, sr


def _heuristik(words, path):
    """Fallback tanpa ASR: bagi waktu bicara menurut bobot huruf, DIJANGKAR pada jeda nyata.

    Versi lama hanya memakai satu rentang bicara (awal..akhir) sehingga aba-aba BEAT bisa
    meleset 0,3-0,5 s saat TTS berhenti di tanda titik. Sekarang setiap jeda >= 135 ms
    dianggap batas segmen: kata dibagi ke segmen sesuai massa huruf, lalu di dalam segmen
    dibagi lagi menurut bobot huruf. Untuk TTS yang bersih ini akurat ~60-100 ms.
    """
    a, sr = _read(path)
    hop = max(1, int(sr * 0.01))
    n = len(a) // hop
    if n < 4:
        return [[w, 0.0, 0.0] for w in words]
    db = 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-9)
    ref = float(np.percentile(db, 95))
    sp = db > ref - 24.0
    # segmen bicara + gabung jeda pendek (< 135 ms) supaya konsonan tak memecah segmen
    runs, i = [], 0
    while i < n:
        if sp[i]:
            j = i
            while j < n and sp[j]:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    if not runs:
        return [[w, 0.0, 0.0] for w in words]
    merged = []
    for r in runs:
        if merged and (r[0] - merged[-1][1]) * hop / sr < 0.135:
            merged[-1][1] = r[1]
        else:
            merged.append(list(r))
    merged = [m for m in merged if (m[1] - m[0]) * hop / sr >= 0.05] or merged
    seg = [(m[0] * hop / sr, m[1] * hop / sr) for m in merged]

    bob = np.array([max(1, len(_norm(w))) + (1.2 if w[-1] in ",.?!;:" else 0.0) for w in words], float)
    cum = np.concatenate([[0.0], np.cumsum(bob)]) / bob.sum()
    mid = (cum[:-1] + cum[1:]) / 2.0
    durs = np.array([b - a_ for a_, b in seg], float)
    bounds = np.cumsum(durs / durs.sum())
    seg_idx = np.clip(np.searchsorted(bounds, mid, side="right"), 0, len(seg) - 1)

    out = [None] * len(words)
    for k in range(len(seg)):
        idxs = np.where(seg_idx == k)[0]
        if len(idxs) == 0:
            continue
        s0, s1 = seg[k]
        sub = bob[idxs]
        edges = np.concatenate([[0.0], np.cumsum(sub)]) / sub.sum()
        for q, wi in enumerate(idxs):
            out[wi] = (s0 + (s1 - s0) * edges[q], s0 + (s1 - s0) * edges[q + 1])
    # kata yang jatuh di luar segmen (jika jumlah segmen < kata) -> interpolasi tetangga
    known = [i for i, v in enumerate(out) if v is not None]
    if not known:
        return [[w, 0.0, 0.0] for w in words]
    for i in range(len(out)):
        if out[i] is None:
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            if prev is None:
                a0 = max(0.0, out[nxt][0] - 0.22 * (nxt - i))
                out[i] = (a0, a0 + 0.20)
            elif nxt is None:
                a0 = out[prev][1] + 0.02 + 0.22 * (i - prev - 1)
                out[i] = (a0, a0 + 0.20)
            else:
                p0, p1 = out[prev][1], out[nxt][0]
                m = nxt - prev
                out[i] = (p0 + (p1 - p0) * (i - prev - 1) / m, p0 + (p1 - p0) * (i - prev) / m)
    return [[w, round(a0, 3), round(b0, 3)] for w, (a0, b0) in zip(words, out)]


def _audio16k(path):
    """Audio float32 16 kHz mono via ffmpeg (tanpa PyAV: versi av di sandbox tidak cocok)."""
    import subprocess, imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    raw = subprocess.run([ff, "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768


def _whisper_words(path, model):
    segs, _ = model.transcribe(_audio16k(path), language="id", word_timestamps=True, beam_size=5,
                               vad_filter=False, condition_on_previous_text=False)
    out = []
    for s in segs:
        for w in (s.words or []):
            out.append((_norm(w.word), float(w.start), float(w.end)))
    return [w for w in out if w[0]]


def _cocokkan(words, det):
    """Petakan kata naskah -> (t0, t1) dari kata terdeteksi, monoton; celah diinterpolasi."""
    nw = [_norm(w) for w in words]
    nd = [d[0] for d in det]
    sm = difflib.SequenceMatcher(a=nw, b=nd, autojunk=False)
    t = [None] * len(words)
    for tag, i0, i1, j0, j1 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i1 - i0):
                t[i0 + k] = (det[j0 + k][1], det[j0 + k][2])
        elif tag == "replace" and (i1 - i0) == (j1 - j0):
            for k in range(i1 - i0):           # angka vs kata angka, ejaan beda: tetap sejajar
                t[i0 + k] = (det[j0 + k][1], det[j0 + k][2])
        elif tag == "replace" and j1 > j0:
            ta, tb = det[j0][1], det[j1 - 1][2]
            m = i1 - i0
            for k in range(m):
                t[i0 + k] = (ta + (tb - ta) * k / m, ta + (tb - ta) * (k + 1) / m)
    # interpolasi kata yang belum punya waktu
    known = [i for i, v in enumerate(t) if v is not None]
    if not known:
        return None
    for i in range(len(t)):
        if t[i] is None:
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            if prev is None:
                ta = max(0.0, t[nxt][0] - 0.28 * (nxt - i)); t[i] = (ta, ta + 0.25)
            elif nxt is None:
                ta = t[prev][1] + 0.03 + 0.28 * (i - prev - 1); t[i] = (ta, ta + 0.25)
            else:
                span0, span1 = t[prev][1], t[nxt][0]
                m = nxt - prev
                t[i] = (span0 + (span1 - span0) * (i - prev - 1) / m, span0 + (span1 - span0) * (i - prev) / m)
    return [[w, round(a, 3), round(b, 3)] for w, (a, b) in zip(words, t)]


def jalankan(tl_path, adir, out_path, lead_default=0.3):
    tl = json.load(open(tl_path))
    lead = float(tl.get("lead_in", lead_default))
    model = None
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(MODEL, device="cpu", compute_type="int8")
        mode = f"faster-whisper {MODEL}"
    except Exception as e:                         # noqa: BLE001
        mode = f"heuristik (whisper tidak tersedia: {e.__class__.__name__})"
    hasil, laporan = {}, []
    for sc in tl["scenes"]:
        words = sc["vo"].split()
        path = os.path.join(adir, sc["id"] + ".wav")
        if not os.path.exists(path):
            continue
        off = float(sc.get("vo_at", sc["start"] + lead)) - float(sc["start"])
        kata = None
        if model is not None:
            try:
                det = _whisper_words(path, model)
                kata = _cocokkan(words, det)
                nd = set(x[0] for x in det)
                cocok = sum(1 for w in words if _norm(w) in nd)
                laporan.append(f"  {sc['id']:6s} naskah {len(words):3d} kata | terdeteksi {len(det):3d} | kata naskah dikenali {cocok}")
            except Exception as e:                 # noqa: BLE001
                laporan.append(f"  {sc['id']:6s} whisper gagal ({e.__class__.__name__}: {str(e)[:60]}) -> heuristik")
                kata = None
        if kata is None:
            kata = _heuristik(words, path)
            laporan.append(f"  {sc['id']:6s} heuristik")
        hasil[sc["id"]] = [[w, round(a + off, 3), round(b + off, 3)] for w, a, b in kata]
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(hasil, open(out_path, "w"), ensure_ascii=False, indent=0)
    print(f"[align_kata] mode: {mode}")
    print("\n".join(laporan))
    print(f"[align_kata] -> {out_path} ({sum(len(v) for v in hasil.values())} kata)")
    return hasil


def _uji():
    words = "Komet Halley baru kembali tahun dua ribu enam puluh satu.".split()
    det = [("komet", 0.3, 0.6), ("halley", 0.6, 1.0), ("baru", 1.0, 1.2), ("kembali", 1.2, 1.6),
           ("tahun", 1.6, 1.9), ("2061", 1.9, 2.8)]
    k = _cocokkan(words, det)
    assert k and len(k) == len(words) and k[0][1] == 0.3 and k[-1][2] >= 2.8, k
    assert all(k[i][1] <= k[i + 1][1] + 1e-6 for i in range(len(k) - 1)), k
    print("selftest align_kata OK")


if __name__ == "__main__":
    if "--uji" in sys.argv:
        _uji(); sys.exit(0)
    jalankan(os.path.join(BASE, "timeline.json"), os.path.join(BASE, "audio_proc"),
             os.path.join(BUILD, "kata.json"))
