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
    # Pita pembanding di tengah. Tanpa ini, thumbnail dengan gambar kecil di
    # atas + angka di bawah menyisakan ~350 px kosong yang membuatnya terlihat
    # belum jadi (keluhan pada versi Ep56).
    band = getattr(mod, "THUMB", {}).get("band")
    if band:
        # tinggi panel mengikuti isi (dulu 300 px untuk 2 baris -> bawah kosong)
        C.scrim(kk, 780, 1030, (150, 0), (4, 6, 14))
        C.panel(kk, 56, 800, 968, 190, 1.0, aksen=C.VIOLET, radius=28)
        C.label_kecil(kk, band[0], 100, 822, C.TEKS_3, 30, 1.0, "kiri", 3.0)
        C.tulis(kk, band[1], 100, 868, C.VIOLET_L, 56, M.F_BOLD, 1.4)
    if angka:
        C.tulis(kk, angka, 62, 1180, C.GOLD, 236, M.F_BOLD, 2.0)
    if keterangan:
        C.tulis(kk, keterangan, 62, 1470, C.TEKS, 56, M.F_BOLD, 1.6)
    C.label_kecil(kk, f"SAINS DALAM {mod.daftar()['total']:.0f} DETIK · KlikTahu", 62, 1770, C.TEKS_2, 30, 1.0,
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
    # Teks diambil dari THUMB modul episode (dulu ditulis tangan di sini,
    # sehingga thumbnail episode baru tetap berbunyi "KAMU MERASA JATUH?").
    th = getattr(mod, "THUMB", {})
    baris1 = th.get("alt_atas", th.get("atas", "KAMU MERASA JATUH?"))
    baris2 = th.get("alt_besar", "INI SEBABNYA")
    kecil = th.get("alt_kecil", "HYPNIC JERK · 7 DARI 10 ORANG")
    band = th.get("band")
    if band:
        C.scrim(kk, 780, 1030, (150, 0), (4, 6, 14))
        C.panel(kk, 56, 800, 968, 190, 1.0, aksen=C.VIOLET, radius=28)
        C.label_kecil(kk, band[0], 100, 822, C.TEKS_3, 30, 1.0, "kiri", 3.0)
        C.tulis(kk, band[1], 100, 868, C.VIOLET_L, 56, M.F_BOLD, 1.4)
    C.tulis(kk, baris1, 62, 1420, C.TEKS, 78, M.F_BOLD, 1.6)
    C.tulis(kk, baris2, 62, 1524, C.CYAN, 78, M.F_BOLD, 1.6)
    C.label_kecil(kk, kecil, 62, 1680, C.GOLD, 32, 1.0, "kiri", 2.8)
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
        # Pecah jadi kelompok kata (maks 5) supaya terbaca — tetapi jangan
        # tinggalkan potongan ekor pendek ("BEDA" / "HIDUP" sendirian).
        # Kalau sisa kata <= 2 dan durasinya < 2,4 s, gabungkan ke baris
        # sebelumnya: subtitle yang kedip terlalu cepat sulit dibaca.
        kelompok = [kata[j:j + kata_per_baris] for j in range(0, len(kata), kata_per_baris)]
        if len(kelompok) > 1 and len(kelompok[-1]) <= 2:
            j0 = (len(kelompok) - 1) * kata_per_baris
            t_sisa = (s["mulai"] + waktu[min(j0 + len(kelompok[-1]) - 1, len(waktu) - 1)][1]
                      - (s["mulai"] + waktu[j0][0]))
            if t_sisa < 2.4:
                kelompok[-2] = kelompok[-2] + kelompok[-1]
                kelompok.pop()
        j = 0
        for klip in kelompok:
            a = s["mulai"] + waktu[j][0]
            b = s["mulai"] + waktu[min(j + len(klip) - 1, len(waktu) - 1)][1]
            baris.append((n, a, b, " ".join(klip)))
            n += 1
            j += len(klip)

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

CATATAN_STRATEGI = [
    "3 detik pertama: pertanyaan yang langsung dialami penonton (pola hook kanal ini).",
    "Caption karaoke di semua babak: penonton Shorts sering menonton tanpa suara.",
    "Satu ide per layar + panel data bawah supaya tidak ada ruang kosong.",
    "Akhir menyatu ke awal (loop) -> waktu tonton bisa melewati durasi video.",
]

META = dict(
    judul="Kamu Merasa Jatuh Tepat Sebelum Tidur? Ternyata Ini Sebabnya",
    judul_alt=[
        "Kenapa Badan Nyentak Saat Mau Tidur? (Hypnic Jerk)",
        "Rasa Jatuh Sebelum Tidur Itu Refleks 60 Juta Tahun",
        "7 dari 10 Orang Pernah Merasakan Ini Sebelum Tidur",
    ],
    deskripsi="""Kamu pernah merasa seperti jatuh dari ketinggian, lalu badan nyentak tepat sebelum tidur? Itu punya nama: hypnic jerk — dan 7 dari 10 orang pernah mengalaminya.

{daftar_babak}

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


BABAK_VIDEO = [
    "Rasa jatuh yang semua orang kenal",
    "Namanya: hypnic jerk",
    "Seberapa umum (7 dari 10)",
    "Kapan tepatnya terjadi",
    "Apa yang dilakukan batang otak",
    "Teori refleks primata",
    "Dua teori, satu mekanisme",
    "Pemicunya: kurang tidur, kafein, stres",
    "Cara membuatnya lebih jarang",
    "Kenapa tubuhmu masih bereaksi seperti ini",
]


def daftar_babak(ep="mesin_v20_ep56"):
    """Bab waktu untuk deskripsi YouTube — dihitung dari timing.json.

    Ditulis tangan dulu, dan langsung melenceng begitu VO mengubah durasi babak
    (00:00/00:07/00:15 tidak lagi cocok). Sekarang selalu ikut timing asli.
    """
    mod = importlib.import_module(ep)
    teks = list(getattr(mod, "BABAK_VIDEO", BABAK_VIDEO))
    mulai, ak = [], 0.0
    for s in mod.daftar()["scenes"]:
        mulai.append(ak)
        ak += s["dur"]
    baris = [f"{int(t // 60):02d}:{int(t % 60):02d} {judul}"
             for t, judul in zip(mulai, teks)]
    return "Di video ini:\n" + "\n".join(baris)


def tulis_metadata(folder, extra=None, ep="mesin_v20_ep56"):
    # Judul/deskripsi/tag diambil dari META milik modul episode kalau ada
    # (modul Ep56 & seterusnya). Tanpa ini, METADATA.md episode baru akan
    # berisi judul Ep56 — bug yang gampang lolos karena berkasnya tetap "ada".
    mod = importlib.import_module(ep if ep.startswith("mesin_v20_") else f"mesin_v20_{ep}")
    # META episode hanya perlu memuat yang berbeda (judul/deskripsi/tag);
    # sisanya (kategori, bahasa, visibilitas) diwarisi META bawaan.
    m = dict(META)
    m.update(getattr(mod, "META", {}))
    if "{daftar_babak}" in m["deskripsi"]:
        m["deskripsi"] = m["deskripsi"].replace("{daftar_babak}", daftar_babak(ep))
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
    for baris in getattr(mod, "CATATAN_STRATEGI", CATATAN_STRATEGI):
        md.append(f"- {baris}")
    p = os.path.join(folder, "METADATA.md")
    with open(p, "w") as f:
        f.write("\n".join(md))
    return p


def tulis_siap_tempel(folder, ep, hasil):
    mod = importlib.import_module(ep if ep.startswith("mesin_v20_") else f"mesin_v20_{ep}")
    meta = dict(META)
    meta.update(getattr(mod, "META", {}))
    p = os.path.join(folder, "SIAP_TEMPEL.md")
    lines = [f"# Siap Tempel — {ep}\n",
             "## Berkas\n",
             f"- Video: `{hasil.get('video', '-')}`",
             f"- Audio (M4A): `{hasil.get('audio', '-')}`",
             f"- Thumbnail utama: `thumb_utama.jpg`",
             f"- Thumbnail alternatif: `thumb_alt.jpg`",
             f"- Lembar pratinjau: `lembar_pratinjau.jpg`\n",
             "## Judul\n", meta["judul"], "",
             "## Deskripsi singkat (untuk kolom deskripsi)\n",
             meta["deskripsi"].split("\n\n")[0], "",
             "## Tag\n", ", ".join(meta["tag"]), "",
             "## Checklist unggah\n",
             "- [ ] Unggah MP4 (1080x1920, 60 fps, H.264 High, AAC 48 kHz)",
             "- [ ] Tempel judul + deskripsi + tag dari METADATA.md",
             "- [ ] Pilih thumbnail utama (uji A/B dengan thumb_alt bila tersedia)",
             "- [ ] Pastikan durasi < 3 menit (Shorts) dan tidak ada musik berlisensi",
             "- [ ] Tandai bukan konten anak-anak",
             f"- [ ] Komentar pertama disiapkan: {meta.get('komentar_pancing', '...')}",
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

    th = getattr(mod, "THUMB", {})
    t_alt = th.get("t_alt")
    if isinstance(t_alt, tuple):
        # (indeks babak, fraksi durasi) -> bingkai babak itu. Dulu selalu
        # memakai babak ke-2, jadi varian A/B untuk episode lain mengambil
        # bingkai yang salah (kosong karena teksnya disembunyikan).
        i_sc, frac = t_alt
        t_alt = d["scenes"][i_sc]["mulai"] + d["scenes"][i_sc]["dur"] * frac
    elif t_alt is None:
        t_alt = d["scenes"][1]["mulai"] + 1.2
    print("[thumb] utama...")
    buat_thumb_utama(ep, t_bg, th.get("atas", "KAMU MERASA JATUH"),
                     th.get("besar", "TEPAT SEBELUM TIDUR?"), th.get("angka", "7/10"),
                     th.get("keterangan", "ORANG PERNAH MERASAKANNYA"),
                     os.path.join(folder, "thumb_utama.jpg"))
    print("[thumb] alternatif...")
    buat_thumb_alt(ep, t_alt, os.path.join(folder, "thumb_alt.jpg"))
    print("[lembar] pratinjau...")
    lembar(ep, os.path.join(folder, "lembar_pratinjau.jpg"))
    print("[meta] metadata...")
    tulis_metadata(folder, ep=ep)
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
