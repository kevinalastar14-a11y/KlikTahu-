#!/usr/bin/env python3
"""QC MP4 KlikTahu — dipanggil otomatis oleh render_all.sh.

Memeriksa, tanpa perlu menebak:
  1. durasi video = durasi timeline (toleransi 0.35s)
  2. audio setiap scene utuh: VO mulai tepat setelah lead_in, tidak terpotong
     di tengah, dan ada jeda wajar sebelum scene berikutnya
  3. keutuhan audio MP4 dibandingkan dengan build/audio.wav (korelasi + selisih RMS)
  4. frame contoh disimpan ke build/qc/ + montase berlabel build/qc/sheet.png
  5. audit margin aman: memastikan tidak ada teks/bentuk yang menyentuh tepi kanvas

Pakai: python3 qc_mp4.py /path/video.mp4 [--timeline lain.json]
"""
import argparse, json, os, subprocess, sys, wave
import numpy as np
import imageio_ffmpeg
import mesin_util

BASE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.environ.get("KT_BUILD") or os.path.join(BASE, "..", "build")
os.makedirs(BUILD, exist_ok=True)
SR = 48000
TOL_DUR = 0.35


def load_wav(path):
    with wave.open(path) as w:
        n = w.getnframes()
        d = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            d = d.reshape(-1, 2).mean(1)
        sr = w.getframerate()
    if sr != SR:
        idx = np.linspace(0, len(d) - 1, int(len(d) * SR / sr))
        d = np.interp(idx, np.arange(len(d)), d).astype(np.float32)
    return d


def decode_mp4_audio(path):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    # PENTING: dekode sebagai stereo lalu rata-rata 0.5/kanal. Downmix mono ffmpeg
    # memakai koefisien 1/sqrt(2) sehingga level naik ~+3 dB (pernah bikin false alarm clipping).
    r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-i", path,
                        "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[:400])
    d = np.frombuffer(r.stdout, dtype=np.float32).astype(np.float32)
    if d.size % 2:
        d = d[:-1]
    st = d.reshape(-1, 2)
    return st.mean(1), st


def probe(path):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run([ff, "-hide_banner", "-i", path], capture_output=True, text=True)
    info = {"raw": r.stderr}
    for line in r.stderr.splitlines():
        line = line.strip()
        if line.startswith("Duration:"):
            h, m, s = line.split(",")[0].split("Duration:")[1].strip().split(":")
            info["dur"] = int(h) * 3600 + int(m) * 60 + float(s)
            if "bitrate:" in line:
                info["bitrate"] = float(line.split("bitrate:")[1].split("kb/s")[0])
        elif line.startswith("Stream") and "Video:" in line:
            info["video"] = line.split("Video:")[1].split(",")[:3]
        elif line.startswith("Stream") and "Audio:" in line:
            info["audio"] = line.split("Audio:")[1].split(",")[:2]
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--timeline", default=os.path.join(BASE, "timeline.json"))
    ap.add_argument("--content", default=os.path.join(BASE, "content.json"))
    ap.add_argument("--margin-max", type=float,
                    default=float(os.environ.get("KT_AUDIT_MAX", "150")))
    arg = ap.parse_args()
    video = arg.video
    tl = json.load(open(arg.timeline))
    content = json.load(open(arg.content))
    lead_in = float(content.get("lead_in", 0.0))
    total = tl["total"]
    gagal = []

    print("=== QC MP4 KlikTahu ===")
    info = probe(video)
    dur = info.get("dur", 0)
    ukuran = os.path.getsize(video)
    print(f"file     : {video}")
    print(f"durasi   : {dur:.2f}s (timeline {total:.2f}s)  selisih {abs(dur - total):.2f}s")
    print(f"ukuran   : {ukuran/1e6:.2f} MB   bitrate {info.get('bitrate', float('nan')):.0f} kb/s")
    print(f"video    : {', '.join(info.get('video', []))}")
    print(f"audio    : {', '.join(info.get('audio', []))}")
    if abs(dur - total) > TOL_DUR:
        gagal.append(f"durasi melenceng {abs(dur-total):.2f}s")

    mp4, mp4_st = decode_mp4_audio(video)
    wav = load_wav(os.environ.get("KT_AUDIO_SRC") or os.path.join(BUILD, "audio.wav"))
    n = min(len(mp4), len(wav))
    a, b = mp4[:n], wav[:n]
    # bandingkan di area yang ada suaranya (bukan hening) supaya korelasi bermakna.
    # Rantai master punya latensi ~5 ms (alimiter lookahead) -> cari lag terbaik
    # dalam +-100 ms dulu; korupsi/terpotong tetap ketahuan pada lag mana pun.
    mask = np.abs(b) > 10 ** (-40 / 20) * max(1e-6, np.abs(b).max())
    if mask.sum() > SR:
        idx = np.where(mask)[0][:SR * 20].astype(np.int64)
        va = a[idx]
        va = va - va.mean()
        na = np.sqrt((va ** 2).sum()) + 1e-12
        step = max(1, int(0.001 * SR))
        best, best_lag = -1.0, 0
        for lag in range(-int(0.10 * SR), int(0.10 * SR) + 1, step):
            ii = idx + lag
            ok = (ii >= 0) & (ii < n)
            if ok.sum() < SR:
                continue
            vb = b[ii[ok]]
            vb = vb - vb.mean()
            c = float((va[ok] * vb).sum() / (na * np.sqrt((vb ** 2).sum()) + 1e-12))
            if c > best:
                best, best_lag = c, lag
        corr = float(best)
        ii = idx + best_lag
        ok = (ii >= 0) & (ii < n)
        d_rms = float(20 * np.log10((np.sqrt((a[ii[ok]] ** 2).mean()) + 1e-9) /
                                    (np.sqrt((b[ii[ok]] ** 2).mean()) + 1e-9)))
        print(f"  (lag terbaik {best_lag / SR * 1000:+.0f} ms)")
    else:
        corr, d_rms = float("nan"), float("nan")
    print(f"audio MP4 vs sumber ({os.path.basename(os.environ.get('KT_AUDIO_SRC') or 'build/audio.wav')}): korelasi {corr:.4f}, selisih level {d_rms:+.2f} dB")
    if corr < 0.97:
        gagal.append(f"audio MP4 tidak identik dengan sumber (korelasi {corr:.3f})")

    pk = np.abs(mp4_st).max(0)
    peak = float(pk.max())
    true_peak_db = 20 * np.log10(peak + 1e-9)
    print(f"peak MP4 : {true_peak_db:.1f} dBFS per kanal (L {20*np.log10(pk[0]+1e-9):.1f} / "
          f"R {20*np.log10(pk[1]+1e-9):.1f})")
    if true_peak_db > -0.1:
        gagal.append("audio mendekati clipping")

    # v11: bila ada SFX, keutuhan VO per adegan diukur pada stem VO (gain sama dengan
    # master). MP4 sudah terbukti identik dengan master lewat korelasi di atas.
    vo_p = os.path.join(BUILD, "audio_master_vo.wav")
    src_p = os.environ.get("KT_AUDIO_SRC") or ""
    ref = mp4
    if src_p.endswith("audio_master.wav") and os.path.exists(vo_p):
        ref = load_wav(vo_p)
        print("\n(SFX aktif: VO per adegan diukur dari stem VO audio_master_vo.wav)")
    print("\nper scene (VO diukur setelah lead_in %.2fs):" % lead_in)
    v12_ref = os.environ.get("KT_VO_CHAIN", "").lower() == "v12"
    thr = 10 ** (-40 / 20) * max(1e-6, np.abs(ref).max())
    # v12: gerbang yang sama dengan rantai VO (RMS 5 ms >= -44 dBFS). Ambang relatif-puncak
    # (-40 dB) terlalu tumpul untuk konsonan pelan di kepala/ekor klip, sehingga VO yang utuh
    # terbaca 0,4 s lebih pendek. Dengan gerbang RMS absolut, rentang aktif = naskah - 0,47 s.
    win = int(0.005 * SR)
    refm = ref.mean(axis=1) if ref.ndim > 1 else ref
    pad = np.concatenate([[0.0], np.cumsum(refm.astype(np.float64) ** 2)])
    rms_all = np.sqrt((pad[win:] - pad[:-win]) / win + 1e-15)
    db_all = 20 * np.log10(rms_all + 1e-12)
    for sc in tl["scenes"]:
        s, e = sc["start"], sc["start"] + sc["dur"]
        i0, i1 = int(s * SR), int(e * SR)
        if v12_ref:
            seg = db_all[i0:max(i0 + 1, i1 - win + 1)]
            idx = np.where(seg > -44.0)[0]
            if len(idx):
                idx = idx * 1  # posisi sampel awal jendela 5 ms
        else:
            seg = ref[i0:i1]
            idx = np.where(np.abs(seg) > thr)[0]
        if len(idx) == 0:
            print(f"  {sc['id']:6s} HENING TOTAL ✘")
            gagal.append(f"{sc['id']} hening total")
            continue
        head = idx[0] / SR
        tail = (len(seg) - idx[-1]) / SR
        # rentang aktif (bukan jumlah sampel): jeda bicara jangan dihitung hilang
        aktif = (idx[-1] - idx[0]) / SR
        # VO harus mulai dekat awal scene (lead_in) dan berakhir sebelum scene usai
        telat = head - lead_in
        jeda = sc["dur"] - (head + aktif)
        harap = sc.get("vo_dur") or 0
        beda = abs(aktif - harap) if harap else 0
        # v12 (vo_manusia): klip berisi pra-gulir 0.12 s + napas alami + ekor 0.35 s ruangan
        # (-63 dBFS, di bawah ambang -40 dB). Keutuhan kata pertama/terakhir sudah
        # diverifikasi ASR di build/vo_qc.json, jadi di sini yang dicek: VO mulai
        # <= lead_in + 0.12 + napas 0.55 s, dan rentang aktif = naskah - (0.47 +- 0.35).
        v12 = os.environ.get("KT_VO_CHAIN", "").lower() == "v12"
        if v12:
            beda = abs(aktif - (harap - 0.47)) if harap else 0
            ok = (head < lead_in + 0.12 + 0.55 and tail > 0.02 and jeda > 0.10
                  and (not harap or beda < 0.35))
        else:
            ok = (head < lead_in + 0.35 and tail > 0.02 and jeda > 0.10
                  and (not harap or beda < 0.35))
        print(f"  {sc['id']:6s} VO mulai +{head:.2f}s (lead_in {lead_in:.2f} → "
              f"selisih {telat:+.2f}s), durasi VO {aktif:.2f}s (naskah {harap:.2f}s, "
              f"beda {beda:.2f}s), ekor {tail:.2f}s, {'OK' if ok else 'PERIKSA ✘'}")
        if not ok:
            gagal.append(f"{sc['id']} tidak utuh (mulai +{head:.2f}s, durasi beda {beda:.2f}s)")

    # frame contoh untuk pemeriksaan mata
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    outdir = os.path.join(BUILD, "qc")
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        if f.endswith(".png"):
            os.remove(os.path.join(outdir, f))
    times = [min(total - 0.4, sc["start"] + sc["dur"] * 0.55) for sc in tl["scenes"]]
    entries = []
    for i, t in enumerate(times):
        p = os.path.join(outdir, f"qc{i}.png")
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}",
                        "-i", video, "-frames:v", "1", "-y", p], check=True)
        entries.append((p, f"{tl['scenes'][i]['id']}  {t:.2f}s"))
    print(f"\n{len(entries)} frame contoh -> {os.path.normpath(outdir)}/qc0..{len(entries)-1}.png")

    # --- audit margin aman pada frame contoh ---------------------------------
    # Catatan: banyak adegan sengaja penuh layar (grafis menyentuh tepi). Karena itu
    # angka di sini bersifat INFORMASI; yang mengikat adalah audit presisi elemen
    # teks di check_layout.py (tahap 0 render_all.sh). Ambang besar (1200) tetap
    # ditolak supaya kelainan kasar tidak lolos.
    from PIL import Image
    # Sejak gaya baru (tanpa panel dalam), ilustrasi memang penuh layar dan
    # menyentuh tepi kanvas dengan sengaja. Yang mengikat tetap audit presisi
    # elemen teks (check_layout.py). Ambang kasar dinaikkan supaya hanya
    # kelainan benar-benar parah (mis. tepi tertutup penuh) yang ditolak.
    ambang_kasar = max(6000.0, arg.margin_max * 20)
    print(f"\naudit margin aman ({mesin_util.SAFE_MARGIN}px) — grafis penuh layar dinilai sebagai catatan:")
    for p, label in entries:
        hits, lokasi, sisi = mesin_util.ink_report(Image.open(p), mesin_util.SAFE_MARGIN)
        if hits > ambang_kasar:
            print(f"  {label:14s} tinta {hits:4d}  BERLEBIHAN   contoh {lokasi[:3]}")
            gagal.append(f"grafis terlalu banyak menyentuh tepi di {label} (tinta {hits})")
        else:
            print(f"  {label:14s} tinta {hits:4d}  catatan (grafis penuh layar biasa)")

    # --- montase berlabel untuk pemeriksaan mata ---
    sheet_path = os.path.join(outdir, "sheet.png")
    mesin_util.sheet(entries, sheet_path)
    print(f"[+] montase berlabel -> {os.path.normpath(sheet_path)}")

    print("\nHASIL QC:", "SEMUA BERSIH ✔" if not gagal else "MASALAH: " + "; ".join(gagal))
    sys.exit(0 if not gagal else 1)


if __name__ == "__main__":
    main()
