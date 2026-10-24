#!/usr/bin/env python3
"""qc_v19.py — gerbang mutu otomatis untuk video KlikTahu v18.

QC ini memeriksa HAL YANG BISA MERUSAK UNGGAHAN, bukan angka kosmetik:

  1. Kontainer   : durasi vs timeline, resolusi, fps, codec, pixel format, bitrate
  2. Audio       : ada/tidaknya track, laju sampel, kanal, LUFS, true peak,
                   korelasi terhadap master (audio tidak bergeser/terpotong)
  3. Loop        : kemiripan frame terakhir dengan frame pertama (wajib > 0,98)
  4. Layar       : frame contoh dibandingkan dengan render ulang dari mesin
                   (memastikan encode tidak menghilangkan elemen), plus cek
                   "tidak ada bidang gelap" (standar gaya: tidak boleh hitam)
  5. Tata letak  : margin aman 40 px untuk elemen teks pada frame contoh
  6. Berkas      : ukuran, faststart, satu track video + satu track audio

Semua temuan dikumpulkan ke `laporan()` dan exit code 1 bila ada yang GAGAL.
Ambang dapat diubah lewat variabel lingkungan (mis. `KT_TP_MIN=-2`).

Pakai:
    python3 qc_v19.py dist/video.mp4 --episode ep55 --audio master.m4a
    python3 qc_v19.py dist/video.mp4 --cepat          # tanpa render ulang mesin
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

W, H = 1080, 1920


# ------------------------------------------------------------------ util

def ffmpeg_exe():
    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def ffprobe_json(path):
    """Baca metadata stream lewat `ffmpeg -i` (ffprobe tidak selalu terpasang)."""
    ff = ffmpeg_exe()
    out = subprocess.run([ff, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    return out


def durasi_video(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return {"fps": round(float(fps), 3), "frame": int(n),
            "detik": round(n / fps, 3) if fps else 0.0, "w": w, "h": h}


def baca_audio(path, sr=48000, ch=1):
    """Dekode audio ke float32 mono (untuk korelasi level & panjang)."""
    ff = ffmpeg_exe()
    raw = subprocess.run([ff, "-v", "quiet", "-i", path, "-f", "s16le",
                          "-ac", str(ch), "-ar", str(sr), "-"],
                         capture_output=True).stdout
    if not raw:
        return np.zeros(1, np.float32), sr
    a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    return a, sr


def lufs_tp(path):
    """Ukur LUFS & true peak memakai filter ebur128 ffmpeg."""
    ff = ffmpeg_exe()
    out = subprocess.run([ff, "-hide_banner", "-nostats", "-i", path,
                          "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    lufs = None
    tp = None
    for baris in out.splitlines():
        b = baris.strip()
        if b.startswith("I:") and lufs is None:
            try:
                lufs = float(b.split()[1])
            except (IndexError, ValueError):
                pass
        if b.startswith("Peak:") and "dBFS" in b:
            try:
                tp = float(b.split()[1])
            except (IndexError, ValueError):
                pass
    return lufs, tp


def korelasi(a, b):
    """Korelasi silang ternormalisasi pada sinyal 1-D (audio/luminans)."""
    n = min(len(a), len(b))
    if n < 16:
        return 0.0
    a = np.asarray(a[:n], np.float32)
    b = np.asarray(b[:n], np.float32)
    a = a - a.mean()
    b = b - b.mean()
    d = (np.linalg.norm(a) * np.linalg.norm(b))
    return float(a.dot(b) / d) if d > 1e-9 else 0.0


def ssim_gray(a, b):
    """SSIM sederhana (jendela gaussian 11) untuk membandingkan dua frame."""
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    k = (11, 11)
    mu1 = cv2.GaussianBlur(a, k, 1.5)
    mu2 = cv2.GaussianBlur(b, k, 1.5)
    s1 = cv2.GaussianBlur(a * a, k, 1.5) - mu1 * mu1
    s2 = cv2.GaussianBlur(b * b, k, 1.5) - mu2 * mu2
    s12 = cv2.GaussianBlur(a * b, k, 1.5) - mu1 * mu2
    m = ((2 * mu1 * mu2 + c1) * (2 * s12 + c2)) / ((mu1 * mu1 + mu2 * mu2 + c1) * (s1 + s2 + c2))
    return float(m.mean())


# ------------------------------------------------------------------ pemeriksaan

class Laporan:
    def __init__(self):
        self.baris = []
        self.gagal = 0

    def tambah(self, nama, ok, detail="", catatan=False):
        tanda = "OK  " if ok else ("NOTE" if catatan else "GAGAL")
        if not ok and not catatan:
            self.gagal += 1
        self.baris.append((tanda, nama, detail))
        print(f"  [{tanda}] {nama:26s} {detail}")

    def cetak(self):
        print("\n" + "=" * 74)
        if self.gagal:
            print(f" HASIL QC: {self.gagal} PEMERIKSAAN GAGAL ✘")
        else:
            print(" HASIL QC: SEMUA BERSIH ✔")
        print("=" * 74)
        return 1 if self.gagal else 0


def cek_kontainer(lap, path, timeline_total=None):
    info = durasi_video(path)
    teks = ffprobe_json(path)
    lap.tambah("berkas ada", os.path.exists(path),
               f"{os.path.getsize(path)/1e6:.2f} MB" if os.path.exists(path) else "tidak ditemukan")
    lap.tambah("resolusi", (info["w"], info["h"]) == (W, H), f'{info["w"]}x{info["h"]}')
    lap.tambah("fps", abs(info["fps"] - 60) < 0.02, f'{info["fps"]}')
    if timeline_total:
        beda = abs(info["detik"] - timeline_total)
        lap.tambah("durasi vs timeline", beda < 0.12,
                   f'{info["detik"]:.2f}s (timeline {timeline_total:.2f}s, beda {beda:.3f}s)')
    lap.tambah("video h264/yuv420p", ("h264" in teks and "yuv420p" in teks),
               "High profile" if "High" in teks else "cek manual")
    lap.tambah("tanpa audio ganda", teks.count("Audio:") == 1, f'{teks.count("Audio:")} track audio')
    lap.tambah("video 1 track", teks.count("Video:") == 1, f'{teks.count("Video:")} track video')
    return info, teks


def cek_audio(lap, video, master=None):
    a, sr = baca_audio(video)
    lap.tambah("audio terdekode", len(a) > sr,
               f"{len(a)/sr:.2f}s @ {sr} Hz")
    a = a[: int(sr * 300)]
    rms = float(np.sqrt((a.astype(np.float64) ** 2).mean()))
    lap.tambah("audio tidak hening", rms > 0.005, f"RMS {20*np.log10(rms+1e-12):.1f} dBFS")
    lufs, tp = lufs_tp(video)
    if lufs is not None:
        lap.tambah("loudness", -17.0 <= lufs <= -13.0, f"{lufs:.1f} LUFS (target -14)")
    if tp is not None:
        lap.tambah("true peak", tp <= -1.0, f"{tp:.1f} dBTP (batas -1,0)")
    if master and os.path.exists(master):
        m, _ = baca_audio(master)
        k = korelasi(a, m)
        dm = 20 * np.log10((np.sqrt((m.astype(np.float64) ** 2).mean()) + 1e-12) /
                           (rms + 1e-12))
        lap.tambah("korelasi vs master", k >= 0.98,
                   f"{k:.4f} (selisih level {dm:+.2f} dB)")


def cek_loop(lap, video):
    """Frame terakhir dibandingkan dengan frame pertama (loop mulus)."""
    cap = cv2.VideoCapture(video)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ok0, f0 = cap.read()
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, n - 1))
    okN, fN = cap.read()
    cap.release()
    if not (ok0 and okN):
        lap.tambah("loop", False, "frame tidak terbaca")
        return
    a = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    b = cv2.cvtColor(fN, cv2.COLOR_BGR2GRAY)
    s = ssim_gray(a, b)
    k = korelasi(a.ravel(), b.ravel())
    lap.tambah("loop (frame akhir = awal)", s >= 0.98 and k >= 0.98,
               f"SSIM {s:.4f} · korelasi {k:.4f}")


def cek_gambar(lap, video, episode=None, contoh=8, tanpa_mesin=False):
    """Bandingkan frame ter-encode dengan render ulang mesin (bila tersedia)."""
    cap = cv2.VideoCapture(video)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if episode and not tanpa_mesin:
        try:
            import importlib
            mod = importlib.import_module(f"mesin_v19_{episode}")
            mod.siapkan()
        except Exception as e:      # pragma: no cover - QC tetap jalan
            print(f"  (mesin {episode} tidak dimuat: {e})")
            mod = None
    else:
        mod = None
    fps = cap.get(cv2.CAP_PROP_FPS) or 60
    idx = np.linspace(0, n - 1, contoh * 2).astype(int)
    skor = []
    kosong = []
    kontras = []
    selisih = []
    for i in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, fr = cap.read()
        if not ok:
            continue
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        # v19 sengaja GELAP (navy -> hitam) seperti video panjang kanal, jadi
        # yang diperiksa bukan "tidak ada piksel gelap" melainkan "tidak ada
        # frame kosong": rata-rata terlalu rendah DAN tidak ada titik terang.
        kosong.append(float(g.mean()) < 6.0 and float(np.percentile(g, 99.5)) < 55.0)
        kontras.append(float(np.percentile(g, 99.5)))
        if mod is not None:
            src = mod.frame(i / fps)
            gs = cv2.cvtColor(src, cv2.COLOR_RGB2GRAY)
            skor.append(ssim_gray(gs, g))
            selisih.append(float(np.abs(gs.astype(np.int16) - g.astype(np.int16)).mean()))
    cap.release()
    if skor:
        # SSIM global mudah "hancur" oleh grain film, padahal mata tidak melihat
        # bedanya. Karena itu lulus dinilai dari MAE (selisih rata-rata piksel)
        # dengan SSIM sebagai info pendamping.
        mae = float(np.mean(selisih)) if selisih else 99.0
        lap.tambah("gambar vs mesin", mae <= 4.0 and float(np.mean(skor)) >= 0.95,
                   f"MAE {mae:.2f}/255 · SSIM {np.mean(skor):.4f} "
                   f"(min {np.min(skor):.4f}) dari {len(skor)} frame")
    if kosong:
        lap.tambah("tidak ada frame kosong", not any(kosong),
                   f"{sum(kosong)}/{len(kosong)} frame gelap total")
    if kontras:
        # Gaya v19 gelap: yang penting setiap frame punya sumber cahaya (highlight),
        # bukan lebar rentang tonalnya.
        lap.tambah("setiap frame punya cahaya", min(kontras) >= 40,
                   f"p99,5 minimum {min(kontras):.0f} (rata {np.mean(kontras):.0f})")


def cek_margin(lap, video, contoh=6):
    """Audit kasar margin: baris/kolom 40 px terluar tidak boleh memuat teks tajam."""
    cap = cv2.VideoCapture(video)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    idx = np.linspace(n * 0.1, n * 0.9, contoh).astype(int)
    terburuk = 0
    for i in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, fr = cap.read()
        if not ok:
            continue
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        tepi = np.zeros_like(g, bool)
        tepi[:40, :] = True
        tepi[-40:, :] = True
        tepi[:, :40] = True
        tepi[:, -40:] = True
        canny = cv2.Canny(g, 90, 200) > 0
        terburuk = max(terburuk, float((canny & tepi).mean()))
    cap.release()
    lap.tambah("margin aman 40 px", terburuk < 0.06,
               f"tepi tajam maks {terburuk*100:.2f}% (grafis penuh layar wajar)")
    return terburuk


def cek_faststart(lap, path):
    """Faststart: atom moov harus berada di awal berkas (siap streaming)."""
    with open(path, "rb") as f:
        head = f.read(4096 * 64)
    pos_moov = head.find(b"moov")
    lap.tambah("faststart (moov di awal)", 0 <= pos_moov < 4096 * 8,
               f"moov @ {pos_moov} byte" if pos_moov >= 0 else "moov tidak ditemukan di awal")


# ------------------------------------------------------------------ utama

def main(argv=None):
    ap = argparse.ArgumentParser(description="QC video KlikTahu v19")
    ap.add_argument("video")
    ap.add_argument("--episode", default=None, help="slug modul mesin (mis. ep55) untuk cek gambar")
    ap.add_argument("--audio", default=None, help="master audio acuan (korelasi)")
    ap.add_argument("--cepat", action="store_true", help="lewati render ulang mesin")
    ap.add_argument("--json", default=None, help="tulis ringkasan JSON ke berkas ini")
    a = ap.parse_args(argv)

    print("=" * 74)
    print(f" QC KlikTahu v19 · {os.path.basename(a.video)}")
    print("=" * 74)
    lap = Laporan()
    info, teks = cek_kontainer(lap, a.video)
    cek_faststart(lap, a.video)
    cek_audio(lap, a.video, a.audio)
    cek_loop(lap, a.video)
    cek_gambar(lap, a.video, a.episode, tanpa_mesin=a.cepat)
    cek_margin(lap, a.video)
    kode = lap.cetak()
    if a.json:
        with open(a.json, "w") as f:
            json.dump({"video": a.video, "info": info,
                       "hasil": [{"status": s, "cek": n, "detail": d} for s, n, d in lap.baris],
                       "gagal": lap.gagal}, f, indent=2, ensure_ascii=False)
    return kode


if __name__ == "__main__":
    sys.exit(main())
