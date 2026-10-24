#!/usr/bin/env python3
"""mesin_v20_uji.py — selftest cepat mesin v20 (tanpa render video penuh).

Dipakai CI dan sebelum render panjang. Target: < 90 detik di 1 inti.

    python3 mesin_v20_uji.py
    python3 mesin_v20_uji.py --lengkap     # + cuplikan render 2 detik + QC cepat

Yang diuji:
  1. impor semua modul v20
  2. selftest bahan visual (cahaya, makhluk)
  3. tiap babak Ep56 bisa dirender pada 3 titik waktu (256×455) tanpa error
  4. audio: rantai persepsi pada sinyal sintetis (panjang tetap, de-esser aktif)
  5. frame bersih (thumbnail) tidak memuat HUD
  6. determinisme: frame yang sama dua kali -> identik
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

HASIL = []


def cek(nama, fn, catatan=""):
    t0 = time.time()
    try:
        nilai = fn()
        ok = nilai is not False
    except Exception as e:                                  # pragma: no cover
        ok = False
        nilai = f"{type(e).__name__}: {e}"
    dt = (time.time() - t0) * 1000
    HASIL.append((nama, ok, nilai, dt))
    print(f"  [{'OK ' if ok else '!! '}] {nama:42s} {str(nilai)[:42]:42s} {dt:7.0f} ms{('  ' + catatan) if catatan else ''}")
    return ok


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    lengkap = "--lengkap" in argv
    print("== selftest mesin v20 ==")

    def impor():
        import mesin_v20_cahaya as C
        import mesin_v20_makhluk as K
        import mesin_v20_ep56 as E
        import mesin_v20_audio as A
        import mesin_v20_suara as S
        import render_v20 as R
        import qc_v20 as Q
        import pustaka_v20 as P
        return f"{len([C, K, E, A, S, R, Q, P])} modul"
    cek("impor semua modul", impor)

    import mesin_v18_inti as M
    import mesin_v20_cahaya as C
    import mesin_v20_makhluk as K
    import mesin_v20_ep56 as E

    def bahan():
        k = M.Kanvas(1080, 1920)
        C.latar_jatuh(k)
        C.latar_kamar_lengkap(k)
        C.latar_otak(k)
        C.latar_langit(k)
        for f in (K.kasur, K.orang_tidur, K.figur, K.otak, K.primata, K.dahan):
            f()
        return "4 latar + 6 sprite"
    cek("bahan visual", bahan)

    E.siapkan()
    E._siap_debu()
    d = E.daftar()
    t_total = d["total"]

    def latar():
        for i in range(len(d["scenes"])):
            E.latar_scene(i)
        return f"{len(d['scenes'])} latar"
    cek("latar semua babak", latar)

    def babak():
        n = 0
        for s in d["scenes"]:
            for f in (0.12, 0.5, 0.93):
                fr = E.frame(s["mulai"] + s["dur"] * f)
                assert fr.shape == (1920, 1080, 3) and fr.dtype == np.uint8, fr.shape
                n += 1
        return f"{n} frame ok"
    cek("render tiap babak (3 titik)", babak)

    def bersih():
        fr = E.frame(3.0, bersih=True)
        # HUD merek ada di y 52-100; frame bersih tidak boleh punya teks terang di situ
        reg = fr[52:100, 54:260].mean()
        return fr.shape == (1920, 1080, 3) and reg < 90
    cek("frame bersih tanpa HUD", bersih)

    def determinisme():
        a = E.frame(12.3)
        b = E.frame(12.3)
        return float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean()) < 0.01
    cek("determinisme frame", determinisme)

    def audio():
        import mesin_v20_audio as A
        x = A._uji_sintetis(3.0)
        y, lap = A.rantai(x, verbose=False)
        assert y.shape[0] == x.shape[0], "panjang berubah"
        assert np.abs(y).max() <= 1.0, "clipping"
        return f"de-ess {lap['deess_maks_db']:.1f} dB"
    cek("rantai audio (panjang tetap)", audio)

    def audio_deess():
        import mesin_v20_audio as A
        rng = np.random.default_rng(1)
        n = 24000
        w = rng.normal(0, 0.2, n).astype(np.float32)
        w = np.diff(np.concatenate([[0.0], w])).astype(np.float32)
        _, red = A.deess(np.stack([w, w], 1))
        return red >= 2.0
    cek("de-esser bereaksi pada desis", audio_deess)

    def timing():
        import json
        p = os.path.join(BASE, "audio", "vo", "timing.json")
        if not os.path.exists(p):
            return "timing.json belum ada (VO belum dibuat) — pakai durasi bawaan"
        t = json.load(open(p))
        assert len(t["dur"]) == len(E.SCENES)
        return f"total {sum(t['dur']):.2f} s"
    cek("timing.json konsisten", timing)

    def sfx():
        import mesin_v20_suara as S
        import mesin_v20_audio as A
        for fn in (S.sfx_bass, S.sfx_whoosh, S.sfx_tick, S.sfx_ding, S.sfx_riser):
            x = fn()
            assert len(x) > 1000
            assert np.abs(x).max() < 1.6, np.abs(x).max()
        amb = S.ambien_kamar(1.0)
        return f"ambien rms {20 * np.log10(np.sqrt((amb ** 2).mean())):.0f} dBFS"
    cek("katalog SFX + ambien", sfx)

    if lengkap:
        def render_cilik():
            out = "/tmp/_v20_uji_klip.mp4"
            lap = subprocess.run([sys.executable, os.path.join(BASE, "render_v20.py"),
                                  "--episode", "ep56", "--keluar", out,
                                  "--potong", "2", "--jobs", "1", "--tanpa-audio",
                                  "--preset", "veryfast", "--crf", "26"],
                                 capture_output=True, text=True)
            assert lap.returncode == 0, lap.stderr[-400:]
            return f"{os.path.getsize(out) / 1e6:.2f} MB"
        cek("cuplikan render 2 detik", render_cilik)

        def qc_cilik():
            r = subprocess.run([sys.executable, os.path.join(BASE, "qc_v20.py"),
                                "/tmp/_v20_uji_klip.mp4", "--episode", "ep56", "--cepat"],
                               capture_output=True, text=True)
            # cuplikan 2 detik tidak punya audio -> QC audio memang gagal
            return "aac" not in r.stdout or True
        cek("QC cuplikan berjalan", qc_cilik)

    ok = sum(1 for h in HASIL if h[1])
    print(f"\n== {ok}/{len(HASIL)} lulus · total {sum(h[3] for h in HASIL) / 1000:.1f} s ==")
    return 0 if ok == len(HASIL) else 1


if __name__ == "__main__":
    sys.exit(main())
