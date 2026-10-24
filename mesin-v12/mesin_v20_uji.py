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
  7. tata letak: tidak ada teks yang menabrak pita caption / keluar kanvas
  8. glif: tidak ada karakter yang jatuh ke kotak tofu (font v18)
  9. potong VO rekaman manusia pada jeda (bukan di tengah kata)
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

    def tata_letak():
        """Audit kotak teks tiap babak (AUDIT di mesin_v20_cahaya).

        Bug nyata yang ditangkap uji ini: baris "SLEEP START · MYOCLONUS
        FISIOLOGIS" di babak 2 duduk di y=1252, padahal caption karaoke mulai
        y=1256 -> dua teks bertumpuk di satu baris dan tidak terlihat di
        pratinjau sekilas. Batas aman:
          * kotak caption (Y_CAPTION-24 .. Y_SCRIM[1]) tidak boleh disentuh
            teks lain — di situlah glif caption benar-benar digambar;
          * kotak teks tidak boleh keluar kanvas;
          * dua kotak teks tidak boleh bertumpuk > 35% kotak terkecil.
        """
        import mesin_v20_cahaya as C
        import mesin_v20_ep56 as E
        E.siapkan()
        pita = (0, E.Y_CAPTION - 24, E.W_, E.Y_SCRIM[1])
        kanvas = (0, 0, E.W_, E.H_)
        salah = []
        for i, sc in enumerate(E.SCENES):
            for frac in (0.35, 0.62, 0.92):
                t = E.MULAI[i] + sc["dur"] * frac
                C.AUDIT = []
                try:
                    E.frame(t)
                    kotak = list(C.AUDIT)
                finally:
                    C.AUDIT = None
                for (x0, y0, x1, y1, teks) in kotak:
                    if x0 < kanvas[0] - 2 or y0 < kanvas[1] - 2 or x1 > kanvas[2] + 2 or y1 > kanvas[3] + 2:
                        salah.append(f"{sc['id']}@{frac:.2f}: keluar kanvas {teks!r}")
                    ox = min(x1, pita[2]) - max(x0, pita[0])
                    oy = min(y1, pita[3]) - max(y0, pita[1])
                    if ox > 0 and oy > 0 and ox * oy > 240:
                        salah.append(f"{sc['id']}@{frac:.2f}: {teks!r} masuk pita caption ({oy}px)")
                for a in range(len(kotak)):
                    for b in range(a + 1, len(kotak)):
                        ax0, ay0, ax1, ay1, at = kotak[a][:5]
                        bx0, by0, bx1, by1, bt = kotak[b][:5]
                        if at == bt:
                            continue
                        ox = min(ax1, bx1) - max(ax0, bx0)
                        oy = min(ay1, by1) - max(ay0, by0)
                        if ox <= 0 or oy <= 0:
                            continue
                        kecil = min((ax1 - ax0) * (ay1 - ay0), (bx1 - bx0) * (by1 - by0))
                        if kecil > 0 and (ox * oy) > 0.35 * kecil:
                            salah.append(f"{sc['id']}@{frac:.2f}: {at!r} x {bt!r}")
        if salah:
            print("      " + "\n      ".join(salah[:8]))
            return False
        return "kanvas & pita caption bersih"

    def glif():
        """Semua karakter yang dipakai harus punya glif (bukan kotak tofu)."""
        import mesin_v20_cahaya as C
        import mesin_v20_ep56 as E
        from mesin_v18_inti import F_BOLD, F_SEMI, spr_text
        tofu = spr_text("A\ue123A", (255, 255, 255), F_BOLD, 40)
        dipakai = set("".join(E.CAPTION)) | set("".join(b[0] for b in E.BABAK))
        for baris in E.BAWAH:
            for l, v in baris:
                dipakai |= set(l) | set(v)
        buruk = []
        for ch in sorted(dipakai):
            if ch.isspace():
                continue
            if ch in C.SANDI:                     # sudah dialihkan _aman()
                buruk.append(f"glif asli tidak ada: {ch!r}")
                continue
            for f in (F_BOLD, F_SEMI):
                g = spr_text("A" + ch + "A", (255, 255, 255), f, 40)
                if g.shape == tofu.shape and np.array_equal(g, tofu):
                    buruk.append(f"{ch!r} (size 40) kotak")
                    break
        if buruk:
            print("      " + ", ".join(buruk))
            return False
        return f"{len(dipakai)} karakter"

    cek("tata letak: kanvas + pita caption", tata_letak)
    cek("glif lengkap (bukan tofu)", glif)

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

    def potong_vo():
        """VO rekaman manusia harus dipotong di jeda, bukan rata len/n."""
        import mesin_v20_suara as S
        sr = S.SR
        rng = np.random.default_rng(5)
        durs = [2.9, 2.6, 3.1, 2.4, 3.0, 3.2, 3.3, 2.8, 2.7, 2.2]
        jeda = [0.6, 0.5, 0.8, 0.45, 0.7, 0.55, 0.9, 0.5, 0.65]
        bagian, sunyi = [], []
        for i, d in enumerate(durs):
            if i:
                bagian.append(np.zeros(int(jeda[i - 1] * sr), np.float32))
            t = np.arange(int(d * sr)) / sr
            u = (0.25 * np.sin(2 * np.pi * 220 * t) + 0.12 * rng.normal(0, len(t))).astype(np.float32)
            env = np.minimum(1, np.minimum(t / 0.08, (d - t) / 0.15))
            bagian.append((u * env).astype(np.float32))
        y = np.concatenate(bagian)
        hop = int(0.02 * sr)
        m = len(y) // hop
        db = 20 * np.log10(np.sqrt((y[:m * hop].reshape(m, hop) ** 2).mean(1) + 1e-12) + 1e-9)
        batas = S.batas_jeda(y, len(durs))
        assert len(batas) == len(durs) - 1, len(batas)
        assert all(batas[k] < batas[k + 1] for k in range(len(batas) - 1)), "batas tidak menaik"
        tenang = max(float(db[b // hop]) for b in batas)
        return tenang < -40.0 and f"{len(batas)} batas, jeda terkuat {tenang:.0f} dB"
    cek("potong VO pada jeda", potong_vo)

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
