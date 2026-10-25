#!/usr/bin/env python3
"""pustaka_v21.py — paket publikasi untuk mesin v21 (gaya kertas).

Beda dengan pustaka_v20
-----------------------
pustaka_v20 menggambar thumbnail dengan primitif gaya "SINEMATIK GELAP"
(scrim gelap, panel kaca, angka emas). Untuk v21 semua itu akan merusak gaya
kertas, jadi modul ini memakai primitif v21 sendiri: kartu krem, tinta navy,
stabilo coral, stiker hitam — sama seperti di dalam video.

Hasil (folder `pustaka/Ep58_Coelacanth/`):
    thumb_utama.jpg       1080x1920 — judul + ikan + angka (tanpa merek ganda)
    thumb_alt.jpg         1080x1920 — versi pembanding A/B
    lembar_pratinjau.jpg  montase satu frame per babak
    subtitle_id.srt       caption per 4-6 kata, waktu dari durasi babak
    METADATA.md           judul/deskripsi/tag siap tempel
    SIAP_TEMPEL.md        ringkasan + checklist unggah
    fakta_sumber.md       daftar klaim + sumber (audit)

Pakai:
    python3 pustaka_v21.py --episode mesin_v21_ep58 --slug Ep58_Coelacanth
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys

import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import mesin_v18_inti as I  # noqa: E402
import mesin_v21_kertas as K  # noqa: E402
import mesin_v21_real as R  # noqa: E402
from mesin_v18_inti import blit  # noqa: E402

W, H = 1080, 1920


def _muat(ep):
    mod = importlib.import_module(ep)
    mod.siapkan()
    return mod


def _kanvas(kategori="HEWAN PURBA"):
    """Kanvas thumbnail kertas + HUD (tanpa elemen dari dalam video)."""
    k = K.kertas_dasar().copy()
    K.hud(k, kategori)
    return k


def _kartu_laut(k, x, y, w, h, r=48, ikan_w=760, dalam=0.50):
    """Kartu laut + ikan (dirakit ulang dari primitif baru, bukan tangkapan layar).

    Memakai pustaka v21.real: panggung bergradasi dengan sinar + partikel, dan
    ikan beranatomi lengkap. Versi lama memakai `K.ikan()` (siluet tunggal)
    yang pada ukuran thumbnail terbaca seperti stiker, bukan hewan.
    """
    import mesin_v21_real as R
    K.kartu_tempel(k, x, y, w, h, r, K.KARTU)
    pad = 24
    iw, ih = int(w - pad * 2), int(h - pad * 2)
    panggung = R.laut_dalam(iw, ih, max(8, r - 12), 0.0, sinar=False, butir=True,
                            siluet=False)
    blit(k, panggung, x + pad, y + pad)
    iw2 = int(min(ikan_w, iw * 0.80))
    ik = R.ikan_real(iw2, int(iw2 * 0.44))
    # 0,50 (tengah) dan 0,50 lebar: dengan 0,86 ujung moncong ikan terpotong
    # tepi kiri kartu pada thumbnail.
    ix = x + pad + int((iw - ik.shape[1]) * 0.50)
    iy = y + pad + int((ih - ik.shape[0]) * 0.46)
    blit(k, R.bayang_kontak(int(ik.shape[1] * 0.6), int(ik.shape[0] * 0.18), 0.24),
         ix + int(ik.shape[1] * 0.06), iy + int(ik.shape[0] * 0.86), 0.85)
    blit(k, ik, ix, iy)
    # Penanda kedalaman dilepas: satu label "0 m" tanpa skala penuh terbaca
    # sebagai teks nyasar di sudut kartu.
    return k


def _sorot(k, spr, x, y, warna=None, alpha=0.95, pad_x=20, atas=0.16, bawah=0.20):
    """Blok stabilo di belakang sprite teks; kembalikan tepi bawah blok (y).

    Tinggi blok mengikuti *tinggi huruf kapital* sprite (mask alpha), bukan
    ukuran font: Poppins punya ruang kosong atas/bawah yang berbeda-beda, jadi
    stabilo berbasis `size` selalu meleset dan terbaca sebagai garis bawah.
    """
    warna = K.CORAL_T if warna is None else warna
    m = spr[..., 3] > 40
    ys, xs = np.nonzero(m)
    kap = int(ys.max() - ys.min() + 1)
    lebar = int(xs.max() - xs.min() + 1) + pad_x * 2
    y0 = y + int(ys.min()) - int(kap * atas)
    # `highlighter_spr` menyisakan 10 % margin atas-bawah di dalam sprite
    hh = int(kap * (1 + atas + bawah) / 0.80)
    y0 -= int(hh * 0.10)
    I.blit(k, K.highlighter_spr(lebar, hh), x + int(xs.min()) - pad_x, y0, alpha)
    return y0 + int(hh * 0.90)


def buat_thumb_utama(mod, t_bg, out, atas, besar, angka, ket, kategori="HEWAN PURBA"):
    """Thumbnail utama: judul + kartu laut + angka (semua digambar baru).

    Dirakit dari primitif v21, bukan tangkapan layar, supaya tidak ada sisa
    elemen video (stiker/angka dari babak ikut terbawa pada versi pertama).
    """
    k = _kanvas(kategori)
    y = 196
    for b in atas:
        I.blit(k, I.spr_text(b, K.TINTA, I.F_BOLD, 74, -0.6), 62, y)
        y += 90
    spr = I.spr_text(besar, K.CORAL, I.F_BOLD, 146, -1.4)
    # stabilo di BELAKANG teks: gambar dulu baru tempel teksnya, dan ukurannya
    # diambil dari mask teks (bukan dari `size`) supaya blok benar-benar
    # menyorot kata, bukan jadi garis bawah.
    yb = _sorot(k, spr, 58, y, pad_x=24, atas=0.16, bawah=0.20)
    I.blit(k, spr, 58, y)
    y = yb + 18
    # kartu laut memenuhi sisa layar sampai angka
    _kartu_laut(k, 56, y, 968, 1000, 48, 880, 0.54)
    st = K.stiker(ket, "gelap", 36, -1.6)
    I.blit(k, st, 78, y + 948)
    ny = y + 1048
    n = I.spr_text(angka, K.NAVY, I.F_BOLD, 168, -2.4)
    I.blit(k, n, 58, ny)
    u = I.spr_text("JUTA TAHUN", K.TINTA, I.F_BOLD, 50, 1.2)
    I.blit(k, u, 66, ny + n.shape[0] + 2)
    bawah = ny + n.shape[0] + u.shape[0] + 30
    # catatan kecil di kaki gambar (mengisi ruang bawah supaya tidak kosong)
    kecil = K.pil(f"SAINS DALAM {mod.daftar()['total'] / 60:.0f} MENIT · 7 FAKTA",
                  K.KARTU_2, K.TINTA_2, 30, 26, 12, radius=14, garis=K.KERTAS_3,
                  lebar=2.0)
    I.blit(k, kecil, 62, min(1790, bawah + 26))
    Image.fromarray(k).save(out, quality=95)
    return out


def buat_thumb_alt(mod, t_bg, out, atas, besar, kecil, kategori="HEWAN PURBA"):
    """Versi A/B: kartu lebih besar + satu pertanyaan, tanpa angka besar."""
    k = _kanvas(kategori)
    y = 210
    for b in atas:
        I.blit(k, I.spr_text(b, K.TINTA, I.F_BOLD, 72, -0.6), 62, y)
        y += 88
    spr = I.spr_text(besar, K.NAVY, I.F_BOLD, 132, -1.2)
    _sorot(k, spr, 58, y, pad_x=22, atas=0.16, bawah=0.20)
    I.blit(k, spr, 58, y)
    y += spr.shape[0] + 34
    _kartu_laut(k, 56, y, 968, 1000, 48, 880, 0.54)
    # teks di bawah kartu dihitung dari tepi bawah kartu (bukan angka tetap):
    # menaikkan tinggi kartu pernah membuat dua baris ini menimpa gambar.
    yy = y + 1000 + 46
    for b in kecil:
        I.blit(k, I.spr_text(b, K.TINTA_2, I.F_SEMI, 44, 0.3), 64, yy)
        yy += 66
    st = K.stiker("DITEMUKAN LAGI · 1938", "coral", 34, 1.8)
    I.blit(k, st, 64, yy + 18)
    kecil_pil = K.pil(f"{mod.daftar()['total'] / 60:.0f} MENIT · 7 FAKTA",
                      K.KARTU_2, K.TINTA_2, 30, 26, 12, radius=14,
                      garis=K.KERTAS_3, lebar=2.0)
    I.blit(k, kecil_pil, 62, 1800)
    Image.fromarray(k).save(out, quality=95)
    return out


def lembar(mod, out, n=9, kol=3):
    d = mod.daftar()
    fs = []
    for i, s in enumerate(d["scenes"]):
        for frac in (0.35, 0.98):
            p = f"/tmp/_pustaka21_{i}_{int(frac * 100)}.jpg"
            Image.fromarray(mod.frame(s["mulai"] + s["dur"] * frac)).save(p, quality=90)
            fs.append(p)
    bar = (len(fs) + kol - 1) // kol
    sheet = Image.new("RGB", (360 * kol, 640 * bar), (0, 0, 0))
    for i, f in enumerate(fs):
        sheet.paste(Image.open(f).resize((360, 640)), ((i % kol) * 360, (i // kol) * 640))
    sheet.save(out, quality=92)
    return out, len(fs)


def _kata_waktu(teks, dur, maks_kata=5):
    """Bagi kalimat jadi potongan <=5 kata dengan waktu proporsional panjang teks."""
    kata = teks.split()
    n = len(kata)
    bobot = np.array([len(w) + 1 for w in kata], np.float32)
    kum = np.concatenate([[0], np.cumsum(bobot)]) / bobot.sum()
    potong, i = [], 0
    while i < n:
        j = min(n, i + maks_kata)
        # hindari potongan ekor 1-2 kata yang hanya berkedip
        if n - j <= 2 and n - j > 0:
            j = n
        potong.append((i, j))
        i = j
    return [(a, b, " ".join(kata[a:b])) for a, b in potong], kum


def buat_srt(mod, keluar, maks_kata=5, ambil=0.94):
    d = mod.daftar()
    naskah = list(mod.NASKAH)
    baris = []
    n = 1
    for s, teks in zip(d["scenes"], naskah):
        potong, kum = _kata_waktu(teks, s["dur"], maks_kata)
        for a, b, isi in potong:
            t0 = s["mulai"] + s["dur"] * float(kum[a]) * ambil
            t1 = s["mulai"] + s["dur"] * float(kum[b]) * ambil
            baris.append([n, t0, min(t1, s["mulai"] + s["dur"] - 0.02), isi])
            n += 1
    # rapikan: akhir tiap baris tidak boleh melewati awal baris berikutnya
    # (versi pertama menambah 0,10 s ke setiap akhir -> subtitle bertumpuk)
    for i in range(len(baris) - 1):
        baris[i][2] = min(baris[i][2], baris[i + 1][1] - 0.02)
        if baris[i][2] <= baris[i][1]:
            baris[i][2] = baris[i][1] + 0.30

    def ts(x):
        h = int(x // 3600)
        m = int((x % 3600) // 60)
        sec = x % 60
        return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")

    with open(keluar, "w") as f:
        for i, a, b, t in baris:
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n\n")
    return keluar, len(baris)


META_BAWAAN = dict(
    kategori="Hewan",
    bahasa="Indonesia",
    visibilitas="Publik",
    hashtag="#KlikTahu #SainsIndonesia #HewanPurba #Coelacanth #IkanPurba",
)


def tulis_metadata(folder, mod, hasil):
    m = dict(META_BAWAAN)
    m.update(getattr(mod, "META", {}))
    p = os.path.join(folder, "METADATA.md")
    with open(p, "w") as f:
        f.write(f"# {m.get('judul')}\n\n")
        f.write("## Judul (pilih satu, maks 100 karakter)\n\n")
        for j in m.get("judul_pilihan", [m.get("judul")]):
            f.write(f"- {j}\n")
        f.write("\n## Deskripsi\n\n")
        f.write(m.get("deskripsi", "") + "\n\n")
        f.write("## Tag (pisahkan koma)\n\n")
        f.write(m.get("tag", "") + "\n\n")
        f.write("## Hashtag\n\n")
        f.write(m.get("hashtag", "") + "\n\n")
        f.write("## Setelan unggah\n\n")
        for k in ("kategori", "bahasa", "visibilitas"):
            f.write(f"- {k}: {m.get(k)}\n")
        f.write("\n## Catatan strategi\n\n")
        for b in getattr(mod, "CATATAN_STRATEGI", []):
            f.write(f"- {b}\n")
        f.write("\n## Berkas\n\n")
        for k, v in hasil.items():
            f.write(f"- {k}: `{v}`\n")
    return p


def tulis_siap_tempel(folder, mod, hasil):
    m = dict(META_BAWAAN)
    m.update(getattr(mod, "META", {}))
    d = mod.daftar()
    p = os.path.join(folder, "SIAP_TEMPEL.md")
    with open(p, "w") as f:
        f.write(f"# Siap tempel — {m.get('judul')}\n\n")
        f.write(f"- Durasi: {d['total']:.2f} s ({d['total'] / 60:.2f} menit)\n")
        f.write(f"- Babak: {len(d['scenes'])}\n")
        f.write(f"- Format: 1080x1920 · 60 fps · H.264 High · AAC 320k\n\n")
        f.write("## Judul\n\n```\n" + m.get("judul") + "\n```\n\n")
        f.write("## Deskripsi\n\n```\n" + m.get("deskripsi", "") + "\n```\n\n")
        f.write("## Tag\n\n```\n" + m.get("tag", "") + "\n```\n\n")
        f.write("## Checklist unggah\n\n")
        for b in ("Unggah MP4 utama", "Tempel judul + deskripsi + tag dari METADATA.md",
                  "Pilih thumbnail (uji A/B: thumb_utama vs thumb_alt)",
                  "Unggah subtitle_id.srt", "Cek putar 3 detik pertama di ponsel",
                  "Bagikan ke komunitas setelah 30 menit tayang"):
            f.write(f"- [ ] {b}\n")
        f.write("\n## Berkas\n\n")
        for k, v in hasil.items():
            f.write(f"- {k}: `{v}`\n")
    return p


def tulis_fakta(folder, mod):
    p = os.path.join(folder, "fakta_sumber.md")
    with open(p, "w") as f:
        f.write(f"# Fakta & sumber — {getattr(mod, 'JUDUL', '')}\n\n")
        for i, b in enumerate(getattr(mod, "NASKAH", []), 1):
            f.write(f"## Babak {i}\n\n")
            f.write(f"Narasi: {b}\n\n")
            sb = getattr(mod, "SUMBER", [])
            if i - 1 < len(sb):
                f.write(f"Sumber di layar: {sb[i - 1]}\n\n")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default="mesin_v21_ep58")
    ap.add_argument("--slug", default="Ep58_Coelacanth")
    ap.add_argument("--video")
    ap.add_argument("--audio")
    ap.add_argument("--folder")
    a = ap.parse_args(argv)

    mod = _muat(a.episode)
    folder = os.path.join(BASE, "pustaka", a.slug)
    os.makedirs(folder, exist_ok=True)
    th = getattr(mod, "THUMB", {})
    d = mod.daftar()
    hasil = {}

    # Thumbnail v21 dirakit dari primitif (bukan tangkapan layar), jadi `t_bg`
    # tidak berpengaruh. Parameter dipertahankan hanya untuk kompatibilitas.
    i_bg, f_bg = th.get("t_bg", (0, 0.95))
    t_bg = d["scenes"][i_bg]["mulai"] + d["scenes"][i_bg]["dur"] * f_bg
    hasil["thumb_utama"] = buat_thumb_utama(
        mod, t_bg, os.path.join(folder, "thumb_utama.jpg"),
        th.get("atas", ["IKAN INI SUDAH"]), th.get("besar", "PUNAH?"),
        th.get("angka", "400"), th.get("ket", "TAPI MASIH HIDUP"),
        getattr(mod, "KATEGORI", "HEWAN PURBA"))
    i2, f2 = th.get("t_alt", (1, 0.95))
    t2 = d["scenes"][i2]["mulai"] + d["scenes"][i2]["dur"] * f2
    hasil["thumb_alt"] = buat_thumb_alt(
        mod, t2, os.path.join(folder, "thumb_alt.jpg"),
        th.get("alt_atas", ["LEBIH TUA DARI"]), th.get("alt_besar", "DINOSAURUS"),
        th.get("alt_kecil", ["400 juta tahun", "Sebelum pohon pertama ada"]),
        getattr(mod, "KATEGORI", "HEWAN PURBA"))
    hasil["lembar"], n = lembar(mod, os.path.join(folder, "lembar_pratinjau.jpg"))
    hasil["srt"], nb = buat_srt(mod, os.path.join(folder, "subtitle_id.srt"))
    hasil["metadata"] = tulis_metadata(folder, mod, hasil)
    hasil["siap_tempel"] = tulis_siap_tempel(folder, mod, hasil)
    hasil["fakta"] = tulis_fakta(folder, mod)
    if a.video:
        hasil["video"] = a.video
    if a.audio:
        hasil["audio"] = a.audio
    with open(os.path.join(folder, "hasil.json"), "w") as f:
        json.dump(hasil, f, indent=1, ensure_ascii=False)
    print(f"[pustaka] {folder}")
    for k, v in hasil.items():
        print(f"   {k:12s} {v}")
    print(f"[pustaka] lembar {n} frame · srt {nb} baris")
    return 0


if __name__ == "__main__":
    sys.exit(main())
