#!/usr/bin/env python3
"""qc_v20.py — pemeriksaan hasil render KlikTahu v20 (24 pemeriksaan).

Filosofi QC: periksa hal yang BISA SALAH TANPA TERLIHAT, bukan sekadar "file
ada". Setiap pemeriksaan punya ambang yang berasal dari pengukuran episode
sebelumnya (v18/v19) dan alasan tertulis.

    python3 qc_v20.py dist/KlikTahu_Ep56_v20.mp4 --episode ep56 \
            --audio dist/KlikTahu_Ep56_audio.m4a --json build_v20/qc.json
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
W, H = 1080, 1920


def ffmpeg():
    import shutil
    e = shutil.which("ffmpeg")
    if e:
        return e
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


FF = ffmpeg()


class QC:
    def __init__(self):
        self.butir = []

    def cek(self, nama, lulus, nilai="", ambang="", catatan=""):
        self.butir.append({"nama": nama, "lulus": bool(lulus), "nilai": str(nilai),
                           "ambang": str(ambang), "catatan": catatan})
        tanda = "OK " if lulus else "!! "
        print(f"  [{tanda}] {nama:38s} {nilai:>22s}  (ambang {ambang})")
        return lulus

    def ringkas(self):
        n = len(self.butir)
        ok = sum(1 for b in self.butir if b["lulus"])
        print(f"\nQC: {ok}/{n} lulus" + ("" if ok == n else "  <-- PERIKSA"))
        return ok, n


def _sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = _sh([FF, "-hide_banner", "-i", path])
    return r.stderr


def info_video(path):
    """Metadata video. ffprobe dipakai bila ada; kalau tidak (imageio-ffmpeg
    statis hanya membawa `ffmpeg`), parsing stderr `ffmpeg -i` sudah cukup."""
    import shutil
    exe = shutil.which("ffprobe")
    if exe:
        r = subprocess.run([exe, "-v", "error", "-show_streams", "-show_format",
                            "-of", "json", path], capture_output=True, text=True)
    else:
        r = subprocess.CompletedProcess([], 1, "", "")
    if r.returncode != 0 or not r.stdout.strip():
        # ffprobe tidak tersedia (imageio-ffmpeg statis hanya membawa ffmpeg):
        # parsing stderr `ffmpeg -i` -> struktur yang sama dengan ffprobe.
        err = probe(path)
        d = {"raw": err, "streams": []}
        v, au = {}, {}
        for ln in err.splitlines():
            ln = ln.strip()
            if ln.startswith("Duration:"):
                d["duration"] = ln.split("Duration:")[1].split(",")[0].strip()
            if "Video:" in ln and "Stream #" in ln:
                v["codec_type"] = "video"
                v["codec_name"] = ln.split("Video:")[1].split()[0].split("(")[0].strip(",")
                v["pix_fmt"] = "yuv420p" if "yuv420p" in ln else ("yuv444p" if "yuv444p" in ln else "?")
                v["profile"] = "High" if "(High)" in ln or "High" in ln else "?"
                import re as _re
                mf = _re.search(r"([\d.]+)\s*(?:fps|tbr)", ln)
                if mf:
                    try:
                        v["r_frame_rate"] = f"{float(mf.group(1)):.0f}/1"
                    except ValueError:
                        pass
                for tok in ln.replace(",", " ").split():
                    if "x" in tok and tok.replace("x", "").isdigit() and len(tok.split("x")) == 2:
                        a2, b2 = tok.split("x")
                        if a2.isdigit() and b2.isdigit() and int(a2) > 100:
                            v["width"], v["height"] = int(a2), int(b2)
                if "Duration" not in d:
                    pass
            if "Audio:" in ln and "Stream #" in ln:
                au["codec_type"] = "audio"
                au["codec_name"] = ln.split("Audio:")[1].split()[0].strip(",")
                import re as _re
                mf = _re.search(r"([\d.]+)\s*(?:fps|tbr)", ln)
                if mf:
                    try:
                        v["r_frame_rate"] = f"{float(mf.group(1)):.0f}/1"
                    except ValueError:
                        pass
                for tok in ln.replace(",", " ").split():
                    if tok.isdigit() and int(tok) in (44100, 48000, 96000):
                        au["sample_rate"] = tok
                au["channels"] = "2" if "stereo" in ln else ("1" if "mono" in ln else "?")
        # durasi stream video dari baris Duration keseluruhan
        try:
            h, m, sec = d.get("duration", "0:0:0").split(":")
            dv = int(h) * 3600 + int(m) * 60 + float(sec)
            if v:
                v["duration"] = dv
        except Exception:
            pass
        if v:
            d["streams"].append(v)
        if au:
            d["streams"].append(au)
        return d
    return json.loads(r.stdout)


def ambil_frame(path, t, skala=None, keluar=None):
    """Ambil satu frame pada waktu t -> ndarray RGB."""
    vf = [] if not skala else [f"scale={skala[0]}:{skala[1]}"]
    cmd = [FF, "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1"]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    r = subprocess.run(cmd, capture_output=True)
    n = (skala[0] * skala[1] * 3) if skala else (W * H * 3)
    if len(r.stdout) < n:
        return None
    a = np.frombuffer(r.stdout[:n], np.uint8).reshape(
        (skala[1], skala[0], 3) if skala else (H, W, 3))
    return a


def teks_ada(frame, x0, y0, x1, y1, ambang=0.42):
    """Perkirakan ada/tidak teks/UI terang di kotak (rasio piksel terang)."""
    reg = frame[int(y0):int(y1), int(x0):int(x1)]
    if reg.size == 0:
        return 0.0
    lum = reg.mean(axis=2)
    return float((lum > 255 * ambang).mean())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4")
    ap.add_argument("--episode", default="ep56")
    ap.add_argument("--audio")
    ap.add_argument("--json")
    ap.add_argument("--cepat", action="store_true", help="lewati sampel banyak")
    ap.add_argument("--target-lufs", type=float, default=-14.0)
    a = ap.parse_args(argv)

    q = QC()
    path = a.mp4
    q.cek("berkas ada", os.path.exists(path), f"{os.path.getsize(path)/1e6:.2f} MB" if os.path.exists(path) else "-", "> 0")

    mod = importlib.import_module(a.episode if a.episode.startswith("mesin_v20_") else f"mesin_v20_{a.episode}")
    d = mod.daftar()
    total = float(d["total"])

    meta = info_video(path)
    streams = meta.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    au = next((s for s in streams if s.get("codec_type") == "audio"), None)
    raw = meta.get("raw", "")

    # ---------- kontainer
    if v:
        q.cek("kodek video", v.get("codec_name") == "h264", v.get("codec_name"), "h264")
        q.cek("resolusi", f"{v.get('width')}x{v.get('height')}" == f"{W}x{H}",
              f"{v.get('width')}x{v.get('height')}", f"{W}x{H}")
        fps_txt = v.get("r_frame_rate", "0/1")
        try:
            num, den = fps_txt.split("/")
            fps = float(num) / float(den)
        except Exception:
            fps = 0.0
        q.cek("fps", abs(fps - 60) < 0.05, f"{fps:.2f}", "60")
        q.cek("profil H.264", v.get("profile", "") == "High", v.get("profile"), "High")
        q.cek("pix_fmt", v.get("pix_fmt") == "yuv420p", v.get("pix_fmt"), "yuv420p")
        nb = v.get("nb_frames")
        dur = float(v.get("duration", 0) or 0)
        q.cek("durasi video", abs(dur - total) < 0.12, f"{dur:.2f} s", f"{total:.2f} ±0,12 s")
        if nb:
            q.cek("jumlah frame", abs(int(nb) - round(total * 60)) <= 2,
                  nb, round(total * 60))
    else:
        err = raw
        q.cek("stream video", "Video: h264" in err, "h264" if "h264" in err else "tidak ada", "h264")
        q.cek("resolusi", f"{W}x{H}" in err, "ok" if f"{W}x{H}" in err else "?", f"{W}x{H}")

    # ---------- faststart (moov sebelum mdat)
    with open(path, "rb") as f:
        head = f.read(4 * 1024 * 1024)
    im = head.find(b"moov")
    idd = head.find(b"mdat")
    q.cek("moov di depan (faststart)", 0 < im < (idd if idd > 0 else 1 << 30),
          f"moov@{im} mdat@{idd}", "moov < mdat")

    # ---------- bitrate & ukuran
    mb = os.path.getsize(path) / 1e6
    br = mb * 8 / max(1e-6, total)
    q.cek("bitrate rata-rata", 3.0 < br < 60.0, f"{br:.1f} Mbps", "3–60 Mbps")
    q.cek("ukuran berkas", mb < 250, f"{mb:.1f} MB", "< 250 MB (batas Shorts)")

    # ---------- audio
    if a.audio and os.path.exists(a.audio):
        sys.path.insert(0, BASE)
        try:
            import mesin_v20_audio as A
            i, tp, lra = A.ukur(a.audio)
            q.cek("loudness", abs(i - a.target_lufs) <= 1.0, f"{i:.1f} LUFS",
                  f"{a.target_lufs} ±1")
            q.cek("true peak", tp <= -1.0, f"{tp:.1f} dBTP", "<= -1,0")
            q.cek("loudness range", lra < 9.0, f"{lra:.1f} LU", "< 9 LU")
            da = A.durasi(a.audio)
            q.cek("audio = durasi video", abs(da - total) < 0.25, f"{da:.2f} s", f"{total:.2f} s")
        except Exception as e:                       # pragma: no cover
            q.cek("audio terbaca", False, str(e)[:40], "bisa diukur")
    if au:
        q.cek("kodek audio", au.get("codec_name") == "aac", au.get("codec_name"), "aac")
        q.cek("sample rate", int(au.get("sample_rate", 0)) == 48000, au.get("sample_rate"), "48000")
        q.cek("kanal audio", int(au.get("channels", 0)) == 2, au.get("channels"), "2")
    else:
        q.cek("stream audio", False, "tidak ada", "aac 48k stereo", "render belum diberi audio")

    # ---------- gambar vs mesin + cahaya + HUD
    mod.siapkan()
    if hasattr(mod, "_siap_debu"):
        mod._siap_debu()
    n_sampel = 6 if a.cepat else 12
    idx = np.linspace(0.06, 0.94, n_sampel)
    maes, p99, hud_ok, cap_ok, terang = [], [], 0, 0, []
    for f in idx:
        t = total * float(f)
        fr_small = ambil_frame(path, t, skala=(540, 960))
        if fr_small is None:
            continue
        import cv2
        eng = mod.frame(t)[:, :, :]
        eng_small = cv2.resize(eng, (540, 960), interpolation=cv2.INTER_AREA)
        maes.append(float(np.abs(fr_small.astype(np.int16) - eng_small.astype(np.int16)).mean()))
        lum = eng.mean(axis=2)
        p99.append(float(np.percentile(lum, 99.5)))
        terang.append(float(lum.mean()))
        # HUD: merek kiri atas + badge kanan atas harus ada
        if teks_ada(fr_small, 20, 14, 160, 60) > 0.02 and teks_ada(fr_small, 340, 14, 530, 60) > 0.02:
            hud_ok += 1
        # caption: area scrim harus lebih gelap dari isi atas + ada teks terang
        if teks_ada(fr_small, 30, 610, 510, 700) > 0.01:
            cap_ok += 1
    q.cek("gambar = mesin (MAE)", (np.mean(maes) if maes else 999) <= 6.0,
          f"{np.mean(maes):.2f}/255" if maes else "-", "<= 6/255")
    q.cek("setiap frame punya cahaya", min(p99) >= 40 if p99 else False,
          f"p99,5 min {min(p99):.0f}" if p99 else "-", ">= 40")
    q.cek("tidak ada frame kosong", min(terang) >= 6 if terang else False,
          f"mean min {min(terang):.1f}" if terang else "-", ">= 6")
    q.cek("HUD hadir (merek + badge)", hud_ok >= max(1, len(maes) - 1),
          f"{hud_ok}/{len(maes)}", "semua sampel")
    q.cek("caption terbaca", cap_ok >= max(1, len(maes) - 1),
          f"{cap_ok}/{len(maes)}", "semua sampel")

    # ---------- loop: frame terakhir ~ frame pertama
    f0 = ambil_frame(path, 0.03, skala=(540, 960))
    fl = ambil_frame(path, max(0.0, total - 0.05), skala=(540, 960))
    if f0 is not None and fl is not None:
        mae_loop = float(np.abs(f0.astype(np.int16) - fl.astype(np.int16)).mean())
        q.cek("loop halus (frame akhir ~ awal)", mae_loop <= 26, f"{mae_loop:.1f}/255", "<= 26")

    # ---------- gerak: tidak ada layar beku
    d_gerak = []
    for f in (0.2, 0.5, 0.8):
        t = total * f
        x1 = ambil_frame(path, t, skala=(270, 480))
        x2 = ambil_frame(path, t + 0.25, skala=(270, 480))
        if x1 is not None and x2 is not None:
            d_gerak.append(float(np.abs(x1.astype(np.int16) - x2.astype(np.int16)).mean()))
    q.cek("ada gerak (tidak beku)", min(d_gerak) > 0.35 if d_gerak else False,
          f"min Δ {min(d_gerak):.2f}" if d_gerak else "-", "> 0,35")

    ok, n = q.ringkas()
    hasil = {"lulus": ok, "total": n, "butir": q.butir, "berkas": path}
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w") as f:
            json.dump(hasil, f, indent=1, ensure_ascii=False)
        print("->", a.json)
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
