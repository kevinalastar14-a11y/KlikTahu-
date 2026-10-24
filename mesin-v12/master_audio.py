#!/usr/bin/env python3
"""Master audio Ep21 — versi "santai": VO tidak dipercepat (agar terasa tenang),
dinamikanya dibuat lebih rata (kompresor + limiter lembut), lalu dinaikkan ke level
broadcast. Output: build/audio_master.wav (48 kHz stereo) + laporan QC.
"""
import json, os, subprocess, sys, wave
import numpy as np
import imageio_ffmpeg

BASE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
BUILD = os.environ.get("KT_BUILD") or os.path.join(BASE, "..", "build")
SRC = os.path.join(BUILD, "audio.wav")          # hasil build_audio.py (VO utuh)
os.makedirs(BUILD, exist_ok=True)
OUT = os.path.join(BUILD, "audio_master.wav")
TARGET_PEAK = -1.2     # dBTP kasar (dBFS) — aman untuk AAC YouTube
TARGET_LUFS = -14.0    # standar YouTube


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read(p):
    with wave.open(p) as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels())
    return a.astype(np.float64) / 32768.0, sr


def db(x):
    return 20 * np.log10(max(1e-9, x))


def tambah_sfx(a, sr):
    """v11: lapisan SFX sintetis (sfx.py) dari event mesin_v11 - hanya episode v11.

    Episode lama tidak punya event -> tidak ada yang ditambahkan (audio identik).
    Nonaktifkan dengan KT_SFX=0.
    """
    if os.environ.get("KT_SFX", "1") != "1":
        return a
    tlp = os.path.join(BASE, "timeline.json")
    if not os.path.exists(tlp):
        return a
    import json
    sys.path.insert(0, BASE)
    try:                                   # modul episode mendaftarkan EVENTS12 (SFX per kata)
        _c = json.load(open(os.path.join(BASE, "content.json")))
        _mod = str(_c.get("modul") or "").strip()
        if _mod:
            __import__(_mod)
    except Exception as _e:                # noqa: BLE001
        print(f"  SFX: modul episode gagal dimuat ({_e.__class__.__name__}: {_e})")
    import mesin_v11, sfx
    tl = json.load(open(tlp))
    ev = mesin_v11.events(tl["scenes"])
    ev = [e for e in ev if e[1] in sfx.KATALOG]
    if not ev or sr != sfx.SR:
        print("  SFX: tidak ada event v11 (episode lama) - dilewati")
        return a
    vo = a.mean(axis=1)
    try:
        _cj = json.load(open(os.path.join(BASE, "content.json")))
    except Exception:                      # noqa: BLE001
        _cj = {}
    _v12 = str(_cj.get("mesin", "")).lower() == "v12"
    # v12: SFX sinematik lebih hadir (-10 dB dasar; impact/thump puncak ~ -18 dBFS), tetap di bawah VO lewat duck -7 dB
    lay = sfx.duck(sfx.lapisan(ev, len(vo) / sr, float(os.environ.get("KT_SFX_DB", "-10" if _v12 else "-16"))), vo)
    lay = lay[: len(vo)]
    if len(lay) < len(vo):
        lay = np.pad(lay, (0, len(vo) - len(lay)))
    out = a.copy()
    out[:, 0] += lay * 0.96
    out[:, 1] += lay * 1.00
    # v12: tekstur ambient halus (angin malam) di bawah segalanya - bukan musik; level sama di awal/akhir
    try:
        cj = json.load(open(os.path.join(BASE, "content.json")))
    except Exception:                      # noqa: BLE001
        cj = {}
    if str(cj.get("mesin", "")).lower() == "v12" and os.environ.get("KT_AMBIENT_BED", "1") == "1":
        _amb = str(cj.get("ambient", "angin")).lower()
        _default = "-30" if _amb == "hujan" else ("-33" if _amb in ("laut", "laut_dalam", "samudra") else "-32")
        _lvl = float(os.environ.get("KT_AMBIENT_DB", _default))
        if _amb == "hujan":
            bed = sfx.ambient_hujan(len(vo) / sr, _lvl)
        elif _amb in ("laut", "laut_dalam", "samudra"):
            bed = sfx.ambient_laut(len(vo) / sr, _lvl)          # v16: bed samudra (bukan musik)
        else:
            bed = sfx.ambient_bed(len(vo) / sr, _lvl)
        bed = bed[: len(vo)]
        if len(bed) < len(vo):
            bed = np.pad(bed, (0, len(vo) - len(bed)))
        out[:, 0] += bed
        out[:, 1] += bed
        print(f"  ambient v12: {_amb} {_lvl:.0f} dB, {len(bed) / sr:.1f} s")
    # limiter lembut: tekan hanya puncak yang melewati -1.2 dBFS
    lim = 10 ** (TARGET_PEAK / 20)
    pk = np.abs(out).max(axis=1)
    over = pk > lim
    if over.any():
        g = np.ones(len(out))
        g[over] = lim / pk[over]
        k = int(sr * 0.004)
        g = np.minimum.accumulate(np.lib.stride_tricks.sliding_window_view(
            np.pad(g, (k, k), constant_values=1.0), 2 * k + 1).min(axis=1)[None, :], axis=0)[0]
        out *= g[:, None]
    r_vo = np.sqrt((a ** 2).mean()); r_sx = np.sqrt((lay ** 2).mean()) + 1e-12
    print(f"  SFX: {len(ev)} event | lapisan {db(r_sx):.1f} dBFS RMS ({db(r_sx) - db(r_vo):+.1f} dB vs VO)")
    return out


def ukur_lufs(path):
    """Integrated loudness & true-peak (EBU R128) lewat ffmpeg loudnorm pass-1."""
    r = subprocess.run([FF, "-i", path, "-af", "loudnorm=I=-14:TP=-1.5:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    e = r.stderr
    j = json.loads(e[e.rfind("{"):e.rfind("}") + 1])
    return float(j["input_i"]), float(j["input_tp"])


def tulis(path, a, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(a, -1, 1) * 32767.0).astype("<i2").tobytes())


def main_v12():
    """Master v12 'untuk telinga manusia': VO sudah dirapikan vo_manusia.py (-16 LUFS, tanpa pemotongan),
    jadi di sini TIDAK ada kompresor/EQ/loudnorm dinamis lagi. Hanya: HPF 40 Hz -> gain LINEAR VO ke -16 LUFS
    -> + SFX (duck) + ambient -> gain LINEAR campuran ke -14 LUFS -> limiter true-peak -1.5 dBTP."""
    tmp = os.path.join(BUILD, "_master_tmp.wav")
    run([FF, "-y", "-i", SRC, "-af", "highpass=f=40:poles=1", "-ar", "48000", "-ac", "2", tmp])
    i_vo, tp_vo = ukur_lufs(tmp)
    a_vo, sr = read(tmp)
    g_vo = -16.0 - i_vo
    a_vo *= 10 ** (g_vo / 20.0)
    print(f"  v12 VO stem: {i_vo:.1f} LUFS -> gain linear {g_vo:+.1f} dB -> -16 LUFS (TP {tp_vo + g_vo:.1f})")
    a = tambah_sfx(a_vo, sr)
    tulis(tmp, a, sr)
    i_mix, tp_mix = ukur_lufs(tmp)
    g_mix = TARGET_LUFS - i_mix
    lim = 10 ** (-1.7 / 20)          # margin 0,2 dB untuk overshoot antar-sampel -> hasil <= -1,5 dBTP
    run([FF, "-y", "-i", tmp, "-af", f"volume={g_mix:.3f}dB,alimiter=limit={lim:.4f}:attack=3:release=80:level=false:asc=true",
         "-ar", "48000", "-ac", "2", OUT])
    a_out, _ = read(OUT)
    i_out, tp_out = ukur_lufs(OUT)
    # stem VO dengan gain yang sama (tanpa limiter) -> qc_mp4 menilai keutuhan VO per adegan
    tulis(os.path.join(BUILD, "audio_master_vo.wav"), a_vo * 10 ** (g_mix / 20.0), sr)
    print(f"master -> {os.path.normpath(OUT)}")
    print(f"  campuran {i_mix:.1f} LUFS -> gain linear {g_mix:+.1f} dB | hasil {i_out:.1f} LUFS, TP {tp_out:.1f} dBTP, "
          f"limiter bekerja maks {max(0.0, tp_mix + g_mix + 1.5):.1f} dB | panjang {len(a_out) / sr:.2f}s")
    clip = int((np.abs(a_out) >= 0.9995).sum())
    print(f"  sample clipping: {clip}")
    if clip > 40 or abs(i_out - TARGET_LUFS) > 1.0:
        print("PERINGATAN: master v12 di luar toleransi")
        sys.exit(1)
    print("AUDIO MASTER v12 OK ✔")


def main():
    try:
        _cj = json.load(open(os.path.join(BASE, "content.json")))
    except Exception:                      # noqa: BLE001
        _cj = {}
    if str(_cj.get("mesin", "")).lower() == "v12" and os.environ.get("KT_MASTER_V12", "1") == "1":
        return main_v12()
    tmp = os.path.join(BUILD, "_master_tmp.wav")
    # kompresor lembut 2 tahap + limiter: menjaga cerita tetap tenang tapi terdengar penuh
    chain = ("acompressor=threshold=-20dB:ratio=2.4:attack=14:release=260:makeup=2.2,"
             "acompressor=threshold=-12dB:ratio=1.6:attack=24:release=320:makeup=1.0,"
             "equalizer=f=6800:t=q:w=1.3:g=-1.6,"      # redam desis "s" agar tidak menusuk saat naskah padat
             "bass=g=1.0:f=110,"                        # sedikit kehangatan
             "treble=g=0.9:f=5200,"                     # kejernihan secukupnya
             "loudnorm=I=-14:TP=-1.3:LRA=8:print_format=none,"
             "alimiter=limit=0.985:attack=5:release=60")
    run([FF, "-y", "-i", SRC, "-af", chain, "-ar", "48000", "-ac", "2", tmp])
    a, sr = read(tmp)
    a_vo = a.copy()
    a = tambah_sfx(a, sr)
    pk = np.abs(a).max()
    rms = np.sqrt((a ** 2).mean())
    # pastikan puncak tidak melewati target
    g = min(0.0, TARGET_PEAK - db(pk))
    if abs(g) > 0.05:
        a = np.clip(a * (10 ** (g / 20.0)), -1.0, 1.0)
    out = (a * 32767.0).astype("<i2")
    # stem VO saja (gain sama) -> qc_mp4 memeriksa keutuhan VO per adegan tanpa
    # terganggu SFX; keutuhan MP4 tetap dicek dengan korelasi ke master lengkap.
    vo_out = (np.clip(a_vo * (10 ** (g / 20.0)), -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(os.path.join(BUILD, "audio_master_vo.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(vo_out.tobytes())
    with wave.open(OUT, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(out.tobytes())
    pk2 = np.abs(a).max()
    print(f"master -> {os.path.normpath(OUT)}")
    print(f"  panjang {out.shape[0]/sr:.2f}s | RMS {db(rms):.1f} dBFS | puncak {db(pk2):.1f} dBFS "
          f"| gain akhir {g:+.2f} dB")
    # cek tidak ada clipping
    clip = int((np.abs(a) >= 0.9995).sum())
    print(f"  sample clipping: {clip}")
    if clip > 40:
        print("PERINGATAN: clipping terdeteksi")
        sys.exit(1)
    print("AUDIO MASTER OK ✔")


if __name__ == "__main__":
    main()
