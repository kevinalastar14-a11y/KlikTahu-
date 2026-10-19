#!/usr/bin/env python3
"""Rapikan VO TANPA memotong isi kalimat.

Prinsip: hanya membuang keheningan di awal/akhir rekaman (dengan ambang sangat
rendah -50 dB supaya tidak menyentuh bunyi kata), lalu mempercepat sedikit.
Tidak ada loudnorm dinamis (bisa membuat awal kata terdengar aneh) dan tidak ada
pemotongan tengah kalimat seperti versi sebelumnya.

Setelah diproses, QC otomatis memastikan:
  * suara mulai <= 0.30 s dari awal klip
  * akhir klip benar-benar hening (bukan terpotong di tengah kata)
  * tidak ada clipping
"""
import os, subprocess, sys, wave
import numpy as np
import imageio_ffmpeg

BASE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
SPEED = float(os.environ.get("SPEED", "1.15"))
# Kecepatan bicara seragam (kata/detik). Semua klip dijadikan sedatar mungkin:
# klip yang terlalu cepat diperlambat, klip yang lambat dipadatkan. Ini yang
# membuat narasi terdengar santai & rata, bukan sebagian cepat sebagian lambat.
TARGET_WPS = float(os.environ.get("TARGET_WPS", "1.95"))
ATEMPO_MIN, ATEMPO_MAX = float(os.environ.get("ATEMPO_MIN", "0.88")), float(os.environ.get("ATEMPO_MAX", "1.08"))
COMPRESS = os.environ.get("COMPRESS", "1") == "1"     # perataan kenyaringan lembut
BREATH = float(os.environ.get("BREATH", "0.12"))      # tambahan jeda antar kalimat (detik)
BREATH_MIN_GAP = float(os.environ.get("BREATH_MIN_GAP", "0.20"))
# Peredam napas tengah klip: MATI secara bawaan (24 Sep 2026). Voice-00 (TTS Arena) tidak punya
# suara napas; ambang lama -28 dB ternyata meredam ujung kata & konsonan pelan (Ep28-Ep46:
# 20-47 potongan per klip, total ~10 s per episode) -> suara terdengar terpotong-potong.
REDAM_NAPAS = os.environ.get("REDAM_NAPAS", "0") == "1"
# QC keutuhan: isi bersuara yang boleh hilang/teredam >6 dB oleh pemrosesan (ms per klip)
ISI_HILANG_MAKS_MS = float(os.environ.get("ISI_HILANG_MAKS_MS", "30"))
_LAST_CUT = [0, 0]              # (sampel dibuang di awal, panjang sesudah potong) dari potong_napas
_SPEEDS = {}                    # pace khusus per adegan (dari content.json)


def load_speeds():
    """Adegan padat (angka/istilah) boleh dibaca lebih santai lewat field 'speed'."""
    global _SPEEDS
    try:
        import json
        c = json.load(open(os.path.join(BASE, "content.json")))
        for sc in c.get("scenes", []):
            v = sc.get("speed")
            if v:
                _SPEEDS[sc["id"]] = float(v)
    except Exception:
        pass


def scene_factor(fname):
    """Faktor relatif terhadap pace dasar 1,10 (1,07 = lebih santai, 1,13 = lebih rapat)."""
    return _SPEEDS.get(os.path.splitext(fname)[0], 1.10) / 1.10


TARGET_PEAK_DB = -1.5          # batas puncak (anti clipping)
TARGET_RMS_DB = float(os.environ.get("TARGET_RMS", "-20"))  # kenyaringan bicara (mesin v2)
FADE_IN, FADE_OUT = 0.010, 0.020   # fade mikro anti "klik"


def read_wav_mono(p):
    with wave.open(p) as w:
        sr = w.getframerate()
        n = w.getnframes()
        a = np.frombuffer(w.readframes(n), dtype="<i2").reshape(-1, w.getnchannels()).mean(1)
    return a / 32768.0, sr


def max_db(p):
    a, _ = read_wav_mono(p)
    return 20 * np.log10(np.abs(a).max() + 1e-9)


def voice_rms_db(p, floor=-45.0, hop=0.01):
    """RMS bagian bersuara saja (mengabaikan keheningan) -> ukuran kenyaringan."""
    a, sr = read_wav_mono(p)
    h = max(1, int(hop * sr))
    fr = a[: len(a) // h * h].reshape(-1, h)
    rms = np.sqrt((fr ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    v = rms[db > floor]
    if v.size == 0:
        return -90.0
    return 20 * np.log10(np.sqrt((v ** 2).mean()) + 1e-9)


def fade_filter():
    """Fade mikro masuk/keluar (tanpa memotong isi): 10 ms awal, 20 ms akhir."""
    return (f"afade=t=in:st=0:d={FADE_IN},"
            f"areverse,afade=t=in:st=0:d={FADE_OUT},areverse")


def naskah_dur(sc_id, words_per_sec=None):
    """Perkiraan durasi naskah (untuk QC: klip tidak jauh lebih pendek/panjang)."""
    try:
        import json, os
        c = json.load(open(os.path.join(BASE, "content.json")))
        for sc in c["scenes"]:
            if sc["id"] == sc_id:
                return len(sc["vo"].split()) / (words_per_sec or TARGET_WPS)
    except Exception:
        pass
    return None


def trim_filter():
    """Potong keheningan saja (ambang rendah, sisa 0.12s), tanpa menyentuh kata."""
    return (
        "highpass=f=80,"
        "silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB:start_silence=0.06,"
        "areverse,"
        "silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB:start_silence=0.12,"
        "areverse"
    )


def speech_span(path):
    """(awal, akhir, durasi_bersuara) sebuah klip — dipakai menghitung kata/detik."""
    a, sr = read_wav_mono(path)
    hop = max(1, int(0.01 * sr))
    n = len(a) // hop
    if n < 2:
        return 0.0, 0.0, 0.0
    fr = a[: n * hop].reshape(n, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1) + 1e-12) + 1e-9)
    v = np.where(db > -45)[0]
    if v.size == 0:
        return 0.0, 0.0, 0.0
    return v[0] * 0.01, v[-1] * 0.01, max(0.05, (v[-1] - v[0]) * 0.01)


def naskah_words(sc_id):
    try:
        import json, os
        c = json.load(open(os.path.join(BASE, "content.json")))
        for sc in c["scenes"]:
            if sc["id"] == sc_id:
                return len(sc["vo"].split())
    except Exception:
        pass
    return None


def add_breath(path, extra=None, min_gap=None, max_pauses=6):
    """Beri ruang napas: jeda alami di dalam klip dipanjangkan sedikit.

    Membuat narasi terdengar santai & bercerita TANPA mengubah kecepatan
    pengucapan satu kata pun (tidak ada kata yang dipercepat/dipotong).
    """
    extra = BREATH if extra is None else extra
    min_gap = BREATH_MIN_GAP if min_gap is None else min_gap
    if extra <= 0:
        return 0
    with wave.open(path) as w:
        sr, nch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype="<i2").reshape(-1, nch)
    mono = a.mean(1) / 32768.0
    hop = max(1, int(0.01 * sr))
    nfr = len(mono) // hop
    db = 20 * np.log10(np.sqrt((mono[: nfr * hop].reshape(nfr, hop) ** 2).mean(1) + 1e-12) + 1e-9)
    quiet = db < -42
    segs, i = [], 0
    while i < nfr:                      # rentetan hening di TENGAH klip saja
        if quiet[i]:
            j = i
            while j < nfr and quiet[j]:
                j += 1
            if i > 2 and j < nfr - 2 and (j - i) * 0.01 >= min_gap:
                segs.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    if not segs:
        return 0
    segs = segs[:max_pauses]
    pad = np.zeros((int(extra * sr), nch), dtype="<i2")
    out, prev = [], 0
    for s0, s1 in segs:
        out.append(a[prev:s1])
        out.append(pad)
        prev = s1
    out.append(a[prev:])
    b = np.concatenate(out).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(nch); w.setsampwidth(sw); w.setframerate(sr)
        w.writeframes(b.tobytes())
    return len(segs)


def potong_napas(path, pad_awal=0.08, pad_akhir=0.25, ambang=-48.0):
    """Buang TARIKAN NAPAS di awal dan EMBUSAN di akhir klip.

    Napas BUKAN keheningan (energinya di atas ambang trim -50 dB) sehingga lolos
    dari trim biasa dan terdengar seperti 'menghela' sebelum kata pertama. Di sini
    kita deteksi frame ber-energi rendah (di bawah ambang, biasanya -45..-38 dB)
    yang berada SEBELUM frame kata pertama dan SESUDAH kata terakhir, lalu potong
    dengan sedikit pad supaya onset kata tidak terasa limbung. Tengah klip tidak
    disentuh (jeda napas alami antar kalimat memang disengaja).
    """
    with wave.open(path) as w:
        sr, nch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype="<i2").reshape(-1, nch)
    mono = a.mean(1) / 32768.0
    hop = max(1, int(0.005 * sr))
    nfr = len(mono) // hop
    if nfr < 4:
        return 0.0
    fr = mono[: nfr * hop].reshape(nfr, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1) + 1e-9) + 1e-9)
    v = np.where(db > ambang)[0]
    if v.size == 0:
        return 0.0
    i0, i1 = int(v[0]), int(v[-1])
    s0 = max(0, i0 * hop - int(pad_awal * sr))
    s1 = min(len(a), (i1 + 1) * hop + int(pad_akhir * sr))
    _LAST_CUT[0], _LAST_CUT[1] = s0, s1 - s0
    if s0 <= 0 and s1 >= len(a):
        _LAST_CUT[0], _LAST_CUT[1] = 0, len(a)
        return 0.0
    with wave.open(path, "wb") as w:
        w.setnchannels(nch); w.setsampwidth(sw); w.setframerate(sr)
        w.writeframes(a[s0:s1].astype("<i2").tobytes())
    return (i0 * hop) / float(sr)          # detik napas awal yang dibuang


def redam_napas(path, atas=-28.0, mulai_redam=-28.5, bawah=-55.0, redam_db=-40.0,
                min_gap=0.06, halus=0.010):
    """Redam sisa napas DI TENGAH klip (versi gain per-frame).

    Pulau suara dideteksi pada ambang -28 dB (napas puncaknya -30..-35 dB sengaja
    TIDAK dianggap suara). Setiap frame dalam celah antar pulau diberi gain:
      penuh `redam_db` bila energinya <= -28,5 dB (ambang hampir sama dengan
    ambang pulau suara sehingga napas sekuat apa pun di celah ikut teredam).
    Interpolasi linear antar frame 10 ms sudah cukup bebas klik pada sinyal
    selevel napas. Kata dan konsonan pelan di dalam pulau suara tidak disentuh.
    """
    with wave.open(path) as w:
        sr, nch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype="<i2").reshape(-1, nch).astype(np.float32)
    mono = a.mean(1) / 32768.0
    hop = max(1, int(0.01 * sr))
    nfr = len(mono) // hop
    if nfr < 6:
        return 0, 0.0
    fr = mono[: nfr * hop].reshape(nfr, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1) + 1e-9) + 1e-9)
    voiced = db > atas
    pulau, i = [], 0
    while i < nfr:
        if voiced[i]:
            j = i
            while j < nfr and (voiced[j] or (j + 3 < nfr and voiced[j + 1:j + 4].any())):
                j += 1
            pulau.append((i, j)); i = j
        else:
            i += 1
    gain = np.ones(nfr, dtype=np.float32)
    red = 10.0 ** (redam_db / 20.0)
    nred, det = 0, 0.0
    for k in range(len(pulau) - 1):
        e0, e1 = pulau[k][1], pulau[k + 1][0]
        if (e1 - e0) * 0.01 < min_gap:
            continue
        sel = np.arange(e0, e1)
        g = np.ones(e1 - e0, dtype=np.float32)
        z1 = (db[e0:e1] <= mulai_redam) & (db[e0:e1] > bawah)
        z2 = (db[e0:e1] > mulai_redam) & (db[e0:e1] <= atas)
        g[z1] = red
        if z2.any():
            g[z2] = red + (1.0 - red) * ((db[e0:e1][z2] - mulai_redam) / (atas - mulai_redam))
        gain[e0:e1] = np.minimum(gain[e0:e1], g)
        nred += 1
        det += (e1 - e0) * 0.01
    if nred == 0:
        return 0, 0.0
    # haluskan kurva gain (rata-rata bergerak) -> tanpa klik
    nh = max(1, int(halus * sr) // hop)
    kernel = np.ones(nh, dtype=np.float32) / nh
    pad = np.concatenate([np.full(nh // 2, 1.0, np.float32), gain, np.full(nh - nh // 2 - 1, 1.0, np.float32)])
    gain_sm = np.convolve(pad, kernel, mode="valid")[:nfr]
    # terapkan per sampel (interpolasi antar frame)
    idx = np.arange(len(mono)) / float(hop)
    i0 = np.clip(idx.astype(np.int64), 0, nfr - 1)
    i1 = np.clip(i0 + 1, 0, nfr - 1)
    w2 = (idx - i0).astype(np.float32)
    g_samp = (1.0 - w2) * gain_sm[i0] + w2 * gain_sm[i1]
    a *= g_samp[:, None]
    with wave.open(path, "wb") as w:
        w.setnchannels(nch); w.setsampwidth(sw); w.setframerate(sr)
        w.writeframes(np.clip(a, -32768, 32767).astype("<i2").tobytes())
    return nred, det


def isi_hilang_ms(ref, sr, path, cut0, hop_s=0.01, turun_db=6.0):
    """QC keutuhan: berapa ms isi BERSUARA di referensi yang hilang/teredam >6 dB di hasil.

    Bersuara = frame > max(-50 dB, median bicara - 32 dB) (ujung kata & konsonan pelan ikut dihitung).
    Bagian yang dibuang di awal/akhir juga dihitung bila bersuara. Hasil disejajarkan lewat `cut0`.
    """
    out, _ = read_wav_mono(path)
    h = max(1, int(hop_s * sr))
    def fdb(x):
        n = len(x) // h
        return 20 * np.log10(np.sqrt((x[: n * h].reshape(n, h) ** 2).mean(1) + 1e-12) + 1e-9)
    dr = fdb(ref)
    if dr.size == 0:
        return 0.0
    med = np.median(dr[dr > -45]) if (dr > -45).any() else -30.0
    amb = max(-50.0, med - 32.0)
    al = np.zeros(len(ref))
    k = min(len(out), len(ref) - cut0)
    al[cut0:cut0 + k] = out[:k]
    do = fdb(al)
    n = min(len(dr), len(do))
    hilang = (dr[:n] > amb) & ((dr[:n] - do[:n]) > turun_db)
    return float(hilang.sum() * hop_s * 1000)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:]); sys.exit(1)
    return r


def main():
    ind = os.path.join(BASE, "audio")
    outd = os.path.join(BASE, "audio_proc")
    tmpd = os.path.join(BASE, "audio_tmp")
    os.makedirs(outd, exist_ok=True); os.makedirs(tmpd, exist_ok=True)
    tot_in = tot_out = 0.0
    load_speeds()
    if _SPEEDS:
        print("pace per adegan:", ", ".join(f"{k}={v:.2f}" for k, v in sorted(_SPEEDS.items())))
    rows = []
    for f in sorted(os.listdir(ind)):
        if not f.endswith(".wav"):
            continue
        src = os.path.join(ind, f)
        tmp = os.path.join(tmpd, f)
        dst = os.path.join(outd, f)
        # 1) trim keheningan (tetap kecepatan asli) — untuk mengukur irama bicara
        run([FF, "-y", "-i", src, "-af", trim_filter(), "-ar", "48000", "-ac", "2", tmp])
        # 2) hitung atempo klip ini supaya irama bicaranya seragam & santai
        st, en, sp = speech_span(tmp)
        w = naskah_words(f[:-4])
        env_key = "SPEED_" + f[:-4].upper()
        if env_key in os.environ:
            at = float(os.environ[env_key])
            wps_in = (w / sp) if (w and sp > 0.2) else 0.0
        elif w and sp > 0.2:
            wps_in = w / sp
            at = min(ATEMPO_MAX, max(ATEMPO_MIN, TARGET_WPS / wps_in))
        else:
            wps_in, at = 0.0, SPEED
        fac = scene_factor(f)                       # pace khusus adegan
        at = max(ATEMPO_MIN, min(1.10, at * fac))
        wps_out = wps_in * at if wps_in else 0.0
        # 3) kenyaringan + perataan + atempo + fade
        pk = max_db(tmp)
        rms = voice_rms_db(tmp)
        g_rms = TARGET_RMS_DB - rms                 # dorongan menuju kenyaringan seragam
        g_rms_old = g_rms
        comp = "acompressor=threshold=-18dB:ratio=2.5:attack=8:release=140:makeup=1," if COMPRESS else ""
        tmp2 = os.path.join(tmpd, "c_" + f)
        run([FF, "-y", "-i", tmp, "-af", comp.rstrip(",") or "anull", "-ar", "48000", "-ac", "2", tmp2])
        pk = max_db(tmp2); rms = voice_rms_db(tmp2)          # ukur SETELAH perataan
        g = min(TARGET_RMS_DB - rms, TARGET_PEAK_DB - pk)
        run([FF, "-y", "-i", tmp2, "-af",
             f"volume={g:.2f}dB,alimiter=limit=0.98,atempo={at:.4f},{fade_filter()}",
             "-ar", "48000", "-ac", "2", dst])
        ref_a, ref_sr = read_wav_mono(dst)                   # referensi: sebelum potong/redam
        _LAST_CUT[0], _LAST_CUT[1] = 0, len(ref_a)
        napas_awal = potong_napas(dst)                       # buang hening/napas di ujung klip saja
        nred, det_red = redam_napas(dst) if REDAM_NAPAS else (0, 0.0)
        isi_hilang = isi_hilang_ms(ref_a, ref_sr, dst, _LAST_CUT[0])
        nbreath = add_breath(dst)                            # ruang napas antar kalimat
        # ekor hening minimum: jaga QC "ekor tak terpotong" di build_audio
        tmp_pad = dst + ".pad.wav"
        run([FF, "-y", "-i", dst, "-af", "apad=pad_dur=0.15", "-ar", "48000", "-ac", "2", tmp_pad])
        os.replace(tmp_pad, dst)
        di = wave.open(src).getnframes() / wave.open(src).getframerate()
        do = wave.open(dst).getnframes() / wave.open(dst).getframerate()
        tot_in += di; tot_out += do
        do = wave.open(dst).getnframes() / wave.open(dst).getframerate()
        rows.append((f, di, do, g, pk, rms, g_rms_old, at, wps_in, wps_out, nbreath, napas_awal, nred, det_red,
                     isi_hilang))

    print(f"{'klip':12s} {'asli':>7s} {'proses':>7s} {'gain':>7s} {'RMS':>7s} {'akhir':>7s}   QC")
    ok_all = True
    for f, di, do, g, pk, rms_in, g_rms, at, wps_in, wps_out, nbreath, napas_awal, nred, det_red, isi_hilang in rows:
        a, sr = read_wav_mono(os.path.join(outd, f))
        hop = int(0.01 * sr)
        n = len(a) // hop
        rms = np.sqrt(np.array([(a[i * hop:(i + 1) * hop] ** 2).mean() for i in range(n)]) + 1e-12)
        db = 20 * np.log10(rms + 1e-9)
        voiced = np.where(db > -38)[0]
        start = voiced[0] * 0.01
        end = voiced[-1] * 0.01
        tail = do - end
        peak = 20 * np.log10(np.abs(a).max() + 1e-9)
        rms_out = voice_rms_db(os.path.join(outd, f))
        # QC: suara mulai cepat, ekor hening (tidak terpotong), tanpa clipping,
        #     dan kenyaringan mendekati target seragam
        qc = []
        if start > 0.30: qc.append(f"awal lambat({start:.2f}s)")
        if tail < 0.045: qc.append(f"EKOR TERPOTONG({tail:.2f}s)")
        if peak > -0.2: qc.append("clipping")
        if isi_hilang > ISI_HILANG_MAKS_MS: qc.append(f"ISI SUARA HILANG {isi_hilang:.0f}ms")
        if rms_out < TARGET_RMS_DB - 1.2: qc.append(f"kurang nyaring({rms_out:.1f}dB)")
        wps_end = (naskah_words(f[:-4]) / do) if naskah_words(f[:-4]) else 0.0
        if wps_end > TARGET_WPS + 0.15: qc.append(f"masih cepat({wps_end:.2f} kata/s)")
        # QC durasi hanya untuk naskah yang cukup panjang (klip pendek seperti
        # "Ikuti KlikTahu." punya jeda wajar, rasionya tidak bermakna)
        est = naskah_dur(f[:-4])
        if est and est >= 3.0:
            rasio = do / est
            if rasio < 0.70 or rasio > 1.62:      # klip lambat = wajar (narasi santai)
                qc.append(f"durasi {rasio:.2f}x naskah")
        ok_all &= not qc
        print(f"{f:12s} {di:6.2f}s {do:6.2f}s {g:+6.1f}dB {rms_in:6.1f} {rms_out:6.1f} "
              f"atempo {at:.2f} ({wps_in:.2f}->{wps_end:.2f} kata/s, {nbreath} jeda, "
              f"napas awal {napas_awal:.2f}s dibuang, {nred} celah diredam {det_red:.2f}s, isi hilang {isi_hilang:.0f}ms)   "
              f"{'OK (mulai %.2fs, ekor %.2fs, peak %.1f dB)' % (start, tail, peak) if not qc else '>>> ' + ', '.join(qc)}")
    print(f"TOTAL {tot_in:.1f}s -> {tot_out:.1f}s  pacing TARGET {TARGET_WPS:.2f} kata/s + napas {BREATH*1000:.0f}ms "
          f"(atempo {ATEMPO_MIN}-{ATEMPO_MAX})  RMS {TARGET_RMS_DB:.0f}dB peak {TARGET_PEAK_DB:.1f}dB "
          f"fade {FADE_IN*1000:.0f}/{FADE_OUT*1000:.0f}ms  kompresi={'on' if COMPRESS else 'off'}")
    print(f"peredam napas tengah klip: {'NYALA' if REDAM_NAPAS else 'MATI'} | QC keutuhan isi: maks "
          f"{ISI_HILANG_MAKS_MS:.0f} ms isi bersuara boleh teredam per klip")
    print("QC:", "SEMUA KLIP BERSIH ✔" if ok_all else "ADA MASALAH ✘")
    if not ok_all and os.environ.get("KT_QC_KERAS", "1") == "1" and any(r[-1] > ISI_HILANG_MAKS_MS for r in rows):
        print("GAGAL: ada isi suara yang terpotong/teredam - pemrosesan dihentikan"); sys.exit(3)


if __name__ == "__main__":
    main()
