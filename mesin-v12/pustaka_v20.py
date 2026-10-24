#!/usr/bin/env python3
"""pustaka_v20.py — paket publikasi: thumbnail + judul/deskripsi/tag + siap tempel.

Semua diturunkan dari MESIN GAMBAR YANG SAMA (`frame()`), jadi thumbnail tidak
"beda gaya" dengan videonya — kesalahan yang sering terjadi kalau thumbnail
dibuat terpisah di aplikasi lain.

Hasil (folder `pustaka/Ep56_HypnicJerk/`):
    thumb_utama.jpg     1080x1920, bingkai + judul besar + angka
    thumb_alt.jpg       versi tanpa teks besar (untuk A/B)
    lembar_pratinjau.jpg  montase 10 babak
    METADATA.md         judul, deskripsi, tag, hashtag (siap tempel)
    SIAP_TEMPEL.md      ringkasan satu halaman + checklist unggah

Pakai:
    python3 pustaka_v20.py --episode ep56 --slug Ep56_HypnicJerk
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import mesin_v18_inti as M
import mesin_v20_cahaya as C
from mesin_v18_inti import blit, spr_text, tw

W, H = 1080, 1920


# ============================================================== thumbnail

def _teks_kotak(im, teks, x, y, size, warna, maks_w, baris_maks=3, align="kiri",
                latar=(255, 255, 255, 0), name=None):
    """Tulis teks multi-baris dengan ukuran menyesuaikan lebar."""
    name = name or M.F_BOLD
    s = size
    while s > 24:
        baris = M.wrap(teks, name, s, maks_w)
        if len(baris) <= baris_maks:
            break
        s -= 4
    baris = M.wrap(teks, name, s, maks_w)
    arr = np.array(im.convert("RGB"))
    yy = y
    for b in baris:
        spr = spr_text(b, warna, name, s, tracking=1.0,
                       shadow=(4, 8, 26), shadow_blur=12, shadow_off=(0, 8), shadow_a=160)
        bx = x if align == "kiri" else x - spr.shape[1] // 2
        blit(arr, spr, int(bx), int(yy))
        yy += int(s * 1.16)
    im.paste(Image.fromarray(arr))
    return yy


def buat_thumb_utama(ep, t_bg, judul_atas, judul_besar, angka, keterangan, out):
    """Thumbnail gaya kanal: gambar mesin + judul + angka.

    Aturan (dari kesalahan versi pertama): HUD merek sudah ada di frame mesin,
    jadi thumbnail TIDAK menambah merek kedua. Caption & panel data mesin
    ditutup scrim kuat di sepertiga bawah supaya tidak bertumpuk dengan angka.
    """
    mod = importlib.import_module(ep)
    mod.siapkan()
    if hasattr(mod, "_siap_debu"):
        mod._siap_debu()
    arr = mod.frame(t_bg, bersih=True, tanpa_teks=True).copy()
    kk = C._KanvasDari(arr)
    C.scrim(kk, 0, 470, (140, 0), (4, 6, 14))
    C.scrim(kk, 1040, 1920, (0, 235), (4, 6, 14))
    blit(arr, C.merek_spr("KlikTahu", 38), 58, 84)
    im = Image.fromarray(arr)

    _teks_kotak(im, judul_atas, 62, 168, 64, C.TEKS, 940, 2)
    _teks_kotak(im, judul_besar, 62, 290, 118, C.CYAN, 940, 2)
    arr = np.array(im.convert("RGB"))
    kk = C._KanvasDari(arr)
    if angka:
        C.tulis(kk, angka, 62, 1180, C.GOLD, 236, M.F_BOLD, 2.0)
    if keterangan:
        C.tulis(kk, keterangan, 62, 1470, C.TEKS, 56, M.F_BOLD, 1.6)
        C.tulis(kk, keterangan, 62, 1470, C.TEKS, 56, M.F_BOLD, 1.6) if False else None
    C.label_kecil(kk, "SAINS DALAM 75 DETIK · KlikTahu", 62, 1770, C.TEKS_2, 30, 1.0,
                  "kiri", 3.0)
    # garis aksen kiri
    C._isi(kk, 40, 1180, 46, 1300, C.GOLD)
    Image.fromarray(arr).save(out, quality=94)
    return out


def buat_thumb_alt(ep, t_bg, out):
    """Versi tanpa angka besar (untuk uji A/B): wajah + satu pertanyaan."""
    mod = importlib.import_module(ep)
    mod.siapkan()
    if hasattr(mod, "_siap_debu"):
        mod._siap_debu()
    arr = mod.frame(t_bg, bersih=True, tanpa_teks=True).copy()
    kk = C._KanvasDari(arr)
    C.scrim(kk, 1080, 1920, (0, 238), (4, 6, 14))
    blit(arr, C.merek_spr("KlikTahu", 38), 58, 84)
    C.tulis(kk, "KAMU MERASA JATUH?", 62, 1420, C.TEKS, 78, M.F_BOLD, 1.6)
    C.tulis(kk, "INI SEBABNYA", 62, 1524, C.CYAN, 78, M.F_BOLD, 1.6)
    C.label_kecil(kk, "HYPNIC JERK · 7 DARI 10 ORANG", 62, 1680, C.GOLD, 32, 1.0, "kiri", 2.8)
    Image.fromarray(arr).save(out, quality=94)
    return out


def lembar(ep, out, n=10):
    """Montase satu frame per babak."""
    mod = importlib.import_module(ep)
    mod.siapkan()
    if hasattr(mod, "_siap_debu"):
        mod._siap_debu()
    d = mod.daftar()
    kol, bar = 5, 2
    sheet = Image.new("RGB", (300 * kol, 533 * bar), (0, 0, 0))
    for i, s in enumerate(d["scenes"][:n]):
        fr = mod.frame(s["mulai"] + s["dur"] * 0.66)
        sheet.paste(Image.fromarray(fr).resize((300, 533), Image.LANCZOS),
                    ((i % kol) * 300, (i // kol) * 533))
    sheet.save(out, quality=92)
    return out


# ============================================================== subtitle

def buat_srt(ep, out, kata_per_baris=5):
    """Ekspor caption karaoke sebagai SRT (kata per kata).

    Dipakai untuk subtipe YouTube/Instagram (aksesibilitas + retensi penonton
    yang menonton tanpa suara). Waktu dihitung dengan fungsi yang SAMA dengan
    yang dipakai mesin gambar (`C._waktu_kata`), jadi subtitle tidak pernah
    lebih cepat/lambat dari caption di layar.
    """
    mod = importlib.import_module(ep)
    d = mod.daftar()
    cap = list(getattr(mod, "CAPTION"))
    baris = []
    n = 1
    for i, s in enumerate(d["scenes"]):
        teks = cap[i]
        kata = [w for w in teks.split() if w]
        waktu = C._waktu_kata(kata, s["dur"] * 0.86)
        # pecah jadi kelompok kata (maks 5) supaya terbaca
        for j in range(0, len(kata), kata_per_baris):
            klip = kata[j:j + kata_per_baris]
            a = s["mulai"] + waktu[j][0]
            b = s["mulai"] + waktu[min(j + len(klip) - 1, len(waktu) - 1)][1]
            baris.append((n, a, b, " ".join(klip)))
            n += 1

    def ts(x):
        h = int(x // 3600)
        m = int((x % 3600) // 60)
        sec = x % 60
        return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")

    with open(out, "w") as f:
        for i, a, b, t in baris:
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n\n")
    return out, len(baris)


# ============================================================== metadata

META = dict(
    judul="Kamu Merasa Jatuh Tepat Sebelum Tidur? Ternyata Ini Sebabnya",
    judul_alt=[
        "Kenapa Badan Nyentak Saat Mau Tidur? (Hypnic Jerk)",
        "Rasa Jatuh Sebelum Tidur Itu Refleks 60 Juta Tahun",
        "7 dari 10 Orang Pernah Merasakan Ini Sebelum Tidur",
    ],
    deskripsi="""Kamu pernah merasa seperti jatuh dari ketinggian, lalu badan nyentak tepat sebelum tidur? Itu punya nama: hypnic jerk — dan 7 dari 10 orang pernah mengalaminya.

Di video ini:
00:00 Rasa jatuh yang semua orang kenal
00:07 Namanya: hypnic jerk
00:15 Seberapa umum (7 dari 10)
00:22 Kapan tepatnya terjadi
00:30 Apa yang dilakukan batang otak
00:38 Teori refleks primata
00:46 Dua teori, satu mekanisme
00:55 Pemicunya: kurang tidur, kafein, stres
01:02 Cara membuatnya lebih jarang
01:10 Kenapa tubuhmu masih bereaksi seperti ini

Sumber: Sleep Medicine (2016) · American Academy of Sleep Medicine · riset University of Colorado. Ini informasi umum, bukan diagnosis. Kalau sentakan terjadi hampir tiap malam disertai kantuk berat, konsultasikan ke dokter.

#KlikTahu #Sains #Tidur #HypnicJerk #FaktaUnik""",
    tag=[
        "hypnic jerk", "kenapa badan nyentak saat tidur", "kenapa merasa jatuh sebelum tidur",
        "sleep start", "myoclonus", "sains tidur", "fakta tidur", "kliktahu",
        "sains indonesia", "edukasi sains", "kenapa mimpi jatuh", "tidur",
        "fakta unik tubuh", "kesehatan tidur", "insomnia", "batang otak",
    ],
    hashtag=["#KlikTahu", "#Sains", "#Tidur", "#HypnicJerk", "#FaktaUnik"],
    kategori="Pendidikan",
    bahasa="Indonesia",
    visibilitas="Publik · Shorts",
)


def tulis_metadata(folder, extra=None):
    m = dict(META)
    if extra:
        m.update(extra)
    os.makedirs(folder, exist_ok=True)
    md = [f"# {m['judul']}\n"]
    md.append("## Judul (pilih satu, maks 100 karakter)\n")
    md.append(f"**Utama:** {m['judul']}\n")
    for i, j in enumerate(m["judul_alt"], 1):
        md.append(f"- Alternatif {i}: {j}")
    md.append("\n## Deskripsi (siap tempel)\n```")
    md.append(m["deskripsi"])
    md.append("```\n")
    md.append("## Tag (tempel di kolom tag, dipisah koma)\n```")
    md.append(", ".join(m["tag"]))
    md.append("```\n")
    md.append("## Hashtag\n" + " ".join(m["hashtag"]) + "\n")
    md.append("## Setelan unggah\n")
    md.append(f"- Kategori: {m['kategori']}")
    md.append(f"- Bahasa: {m['bahasa']}")
    md.append(f"- Visibilitas: {m['visibilitas']}")
    md.append("- Komentar: aktifkan (memicu interaksi awal)")
    md.append("- Buat playlist: \"Tubuh & Sains Sehari-hari\"")
    md.append("- Centang: bukan konten anak-anak\n")
    md.append("## Catatan strategi\n")
    md.append("- 3 detik pertama: rasa jatuh + sentakan (pola paling terbukti di kanal ini).")
    md.append("- Caption karaoke di semua babak: penonton Shorts sering menonton tanpa suara.")
    md.append("- Satu ide per layar + panel data bawah supaya tidak ada ruang kosong.")
    md.append("- Akhir menyatu ke awal (loop) -> waktu tonton bisa melewati durasi video.")
    md.append("- Kolom komentar disiapkan sebagai pancingan: \"jam berapa kamu paling sering nyentak?\"")
    p = os.path.join(folder, "METADATA.md")
    with open(p, "w") as f:
        f.write("\n".join(md))
    return p


def tulis_siap_tempel(folder, ep, hasil):
    p = os.path.join(folder, "SIAP_TEMPEL.md")
    lines = [f"# Siap Tempel — {ep}\n",
             "## Berkas\n",
             f"- Video: `{hasil.get('video', '-')}`",
             f"- Audio (M4A): `{hasil.get('audio', '-')}`",
             f"- Thumbnail utama: `thumb_utama.jpg`",
             f"- Thumbnail alternatif: `thumb_alt.jpg`",
             f"- Lembar pratinjau: `lembar_pratinjau.jpg`\n",
             "## Judul\n", META["judul"], "",
             "## Deskripsi singkat (untuk kolom deskripsi)\n",
             META["deskripsi"].split("\n\n")[0], "",
             "## Tag\n", ", ".join(META["tag"]), "",
             "## Checklist unggah\n",
             "- [ ] Unggah MP4 (1080x1920, 60 fps, H.264 High, AAC 48 kHz)",
             "- [ ] Tempel judul + deskripsi + tag dari METADATA.md",
             "- [ ] Pilih thumbnail utama (uji A/B dengan thumb_alt bila tersedia)",
             "- [ ] Pastikan durasi < 3 menit (Shorts) dan tidak ada musik berlisensi",
             "- [ ] Tandai bukan konten anak-anak",
             "- [ ] Komentar pertama disiapkan: \"Jam berapa kamu paling sering nyentak?\"",
             "- [ ] Tambahkan ke playlist seri \"Tubuh & Sains Sehari-hari\"", ""]
    with open(p, "w") as f:
        f.write("\n".join(lines))
    return p


# ============================================================== utama

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", default="mesin_v20_ep56")
    ap.add_argument("--slug", default="Ep56_HypnicJerk")
    ap.add_argument("--t-bg", type=float, default=None)
    ap.add_argument("--video")
    ap.add_argument("--audio")
    a = ap.parse_args(argv)

    ep = a.episode if a.episode.startswith("mesin_v20_") else f"mesin_v20_{a.episode}"
    folder = os.path.join(BASE, "pustaka", a.slug)
    os.makedirs(folder, exist_ok=True)

    mod = importlib.import_module(ep)
    d = mod.daftar()
    # waktu latar thumbnail: babak hook saat sentakan (paling "menjual")
    # waktu latar: 0,62 s setelah sentakan (cincin kejut sudah hilang, wajah kaget masih ada)
    t_bg = a.t_bg if a.t_bg is not None else d["scenes"][0]["dur"] * 0.62 + 0.62

    print("[thumb] utama...")
    buat_thumb_utama(ep, t_bg, "KAMU MERASA JATUH",
                     "TEPAT SEBELUM TIDUR?", "7/10",
                     "ORANG PERNAH MERASAKANNYA", os.path.join(folder, "thumb_utama.jpg"))
    print("[thumb] alternatif...")
    buat_thumb_alt(ep, d["scenes"][1]["mulai"] + 1.2, os.path.join(folder, "thumb_alt.jpg"))
    print("[lembar] pratinjau...")
    lembar(ep, os.path.join(folder, "lembar_pratinjau.jpg"))
    print("[meta] metadata...")
    tulis_metadata(folder)
    tulis_siap_tempel(folder, ep, {"video": a.video or "-", "audio": a.audio or "-"})
    print("[srt] subtitle Indonesia...")
    srt, nbaris = buat_srt(ep, os.path.join(folder, "subtitle_id.srt"))
    print(f"   {nbaris} baris -> {os.path.basename(srt)}")
    print(f"-> {folder}")
    for f in sorted(os.listdir(folder)):
        p = os.path.join(folder, f)
        print(f"   {f:28s} {os.path.getsize(p) / 1024:8.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
