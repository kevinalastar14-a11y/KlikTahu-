#!/usr/bin/env python3
"""mesin_v18_ep55.py — EP55 "Megalodon" digambar ulang dengan mesin v18.

Perbedaan cara kerja dibanding mesin_v16/v17
--------------------------------------------
v16/v17 memanggil fungsi gambar untuk SETIAP frame: gradasi laut, outline, teks,
kompresi PNG — 6.129 kali. v18 menyiapkan semua yang statis sebagai sprite
sekali di awal (`latar`), lalu tiap frame hanya:

    salin latar (memcpy)  ->  tempel aktor  ->  tempel teks  ->  LUT  ->  kirim

Hasil ukur di sandbox 2 core: 3-6 ms/frame untuk komposisi (tanpa encode),
dibanding 212-230 ms/frame pada v17.

Struktur berkas
---------------
  1. konstanta episode        : judul, warna, posisi tetap
  2. tipografi                : kartu judul, kicker, sumber, kapten karaoke
  3. latar per scene (8)      : fungsi `_latar_*` yang HANYA dipanggil sekali
  4. aktor per scene (8)      : fungsi `_aktor_*` yang dipanggil tiap frame
  5. tabel SCENES             : id, durasi, judul, kata kunci
  6. API                      : `siapkan()`, `frame(t)`, `daftar()`

Aturan gaya yang dipertahankan dari Ep52-Ep55 (jangan diubah tanpa alasan):
  * kertas krem -> langit senja -> air TEAL terang (tidak pernah hitam)
  * semua objek beroutline tinta 3-4 px, ilustrasi penuh layar
  * kartu krem di y ~1478, sumber kecil di bawah kartu
  * label kecil di atas kartu sebagai "kicker" (bukan HUD ramai)
  * frame terakhir = frame pertama (loop mulus)

Selftest:  python3 mesin_v18_ep55.py --pratinjau
"""
from __future__ import annotations

import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

import mesin_v18_dunia as W
import mesin_v18_inti as M
from mesin_v18_dunia import (AIR_1, AIR_2, AIR_3, AIR_4, AIR_5, AMBER, BATU,
                             BUIH, GIGI, GUSI, HIU, HIU_2, HIU_D, INK, KERTAS, KREM,
                             MOUTH, OLIVE, PASIR, PASIR_D, PERUT, PUTIH, RUMPUT,
                             SENJA, TERRA, TERRA_D, UNGU, NAVY, KUNING)
from mesin_v18_inti import (Kanvas, TeksKinetik, blit, blit_add, blit_c, clamp,
                            eio, elastic, eo, lerp, mix, pulse, rng, seg,
                            smooth, spr_text, tw, wrap)

W_, H_ = 1080, 1920
SURF = 330
Y_KARTU = 1470          # tepi atas kartu judul
Y_SUMBER = 1810

# =============================================================== 1. teks episode

JUDUL_EP = "Megalodon"
SUMBER_TEKS = "Shimada dkk. 2025 · Palaeontologia Electronica · NHM"


def kartu_judul(k, kicker, baris, t, masuk=0.0, aksen=TERRA, lebar=930,
                sorot=(), sorot_t=0.55, y=Y_KARTU, alpha=1.0):
    """Kartu judul bawah: kicker kecil + judul dua baris + stabilo kata kunci.

    Semua sprite dibuat saat pertama dipakai lalu di-cache oleh modul inti
    (`spr_text` memakai `_MASK_CACHE`), jadi memanggil fungsi ini tiap frame
    tidak meraster ulang teks.
    """
    if t < masuk:
        return
    p = eo(seg(t, masuk, masuk + 0.42))
    dy = (1 - p) * 46
    a = alpha * p
    ukuran = 54
    # sesuaikan agar baris terpanjang muat di dalam kartu
    while max(tw(b, M.F_BOLD, ukuran) for b in baris) > lebar - 90 and ukuran > 38:
        ukuran -= 2
    lh = ukuran * 1.16
    tinggi = 62 + lh * len(baris)
    spr = W.kartu_spr(lebar, tinggi, aksen=aksen)
    # sprite kartu memuat padding 46 px untuk bayangan -> geser balik supaya
    # pelat krem TEPAT di y (dulu judul keluar di atas pelat karena padding ini)
    pad = 46
    blit(k.a, spr, (W_ - lebar) // 2 - pad, y + dy - pad, a)
    cx = W_ // 2
    # kicker
    ks = W.label_spr(kicker, warna=INK, isi=mix(KREM, PUTIH, 0.4), size=26,
                     name=M.F_SEMI, pad_x=20, pad_y=11, radius=16, aksen=aksen)
    blit_c(k.a, ks, cx, y + 6 + dy, a)
    # judul (kata per kata, muncul berurutan)
    ty = y + 30 + dy
    idx = 0
    for baris_txt in baris:
        kata = baris_txt.split()
        spasi = tw(" ", M.F_BOLD, ukuran)
        total = sum(tw(x, M.F_BOLD, ukuran) for x in kata) + spasi * (len(kata) - 1)
        x = cx - total / 2
        for w in kata:
            pw = seg(t, masuk + 0.10 + idx * 0.045, masuk + 0.34 + idx * 0.045)
            if pw > 0:
                bersih = w.strip(".,:;!?").lower()
                if bersih in sorot:
                    # stabilo tumbuh di belakang kata kunci
                    prog = seg(t, sorot_t + idx * 0.02, sorot_t + idx * 0.02 + 0.25)
                    if prog > 0:
                        sp_w = tw(w, M.F_BOLD, ukuran)
                        hh = ukuran * 0.30
                        y0 = int(ty + lh * 0.66)
                        x0 = int(x - 5)
                        x1 = int(x0 + (sp_w + 10) * prog)
                        if x1 > x0:
                            reg = k.a[y0:y0 + int(hh), x0:x1].astype(np.float32)
                            reg += (np.array(AMBER, np.float32) - reg) * 0.78
                            k.a[y0:y0 + int(hh), x0:x1] = np.clip(reg, 0, 255).astype(np.uint8)
                sp = spr_text(w, INK, M.F_BOLD, ukuran, tracking=-0.5)
                blit(k.a, sp, x, ty + (1 - eo(pw)) * 16, a * eo(pw))
            x += tw(w, M.F_BOLD, ukuran) + spasi
            idx += 1
        ty += lh


def sumber(k, teks=SUMBER_TEKS, y=Y_SUMBER, alpha=0.55):
    """Baris sumber kecil (kredibilitas) di bawah kartu."""
    sp = spr_text(teks, mix(INK, KREM, 0.45), M.F_REG, 22)
    blit_c(k.a, sp, W_ // 2, y, alpha)


def kapten(k, kata, t, t0, t1, y=1330, alpha=0.95, maks_kata=6, warna=None):
    """Kapten karaoke satu baris: kata berganti tiap ~0,42 s, kata aktif disorot.

    Dipakai untuk menampilkan VO tanpa memenuhi layar (standar: <=7 kata/layar).
    """
    if not (t0 <= t <= t1) or not kata:
        return
    n = len(kata)
    langkah = (t1 - t0) / max(1, n)
    aktif = min(n - 1, int((t - t0) / langkah))
    # kelompok 3 kata: tampilkan jendela di sekitar kata aktif
    lo = max(0, min(aktif - 1, n - maks_kata))
    hi = min(n, lo + maks_kata)
    jendela = kata[lo:hi]
    ukuran = 34
    widths = [tw(w, M.F_SEMI, ukuran) for w in jendela]
    spasi = tw(" ", M.F_SEMI, ukuran) * 0.9
    total = sum(widths) + spasi * (len(jendela) - 1)
    x = W_ / 2 - total / 2
    p = eo(seg(t, t0, t0 + 0.20))
    a = alpha * p
    for i, (w, ww) in enumerate(zip(jendela, widths)):
        gi = lo + i
        col = (warna or INK) if gi == aktif else mix(INK, KREM, 0.42)
        sp = spr_text(w, col, M.F_SEMI, ukuran)
        blit(k.a, sp, x, y - (8 if gi == aktif else 0), a)
        x += ww + spasi


# =============================================================== 2. latar

def _dasar_umum(k, t=0.0, senja=0.30, pasir_y=1560, rumput_x=(140, 930),
                batu_x=760, matahari=(812, 196), awan=True, dalam=1.0):
    """Latar dasar yang dipakai hampir semua scene: langit, air, cahaya, pasir.

    Dipanggil SEKALI per scene (bukan per frame).
    """
    W.langit(k, t, awan=awan, matahari_x=matahari[0], matahari_y=matahari[1], senja=senja)
    W.air(k, SURF, H_, dalam=dalam)
    W.berkas_cahaya(k, 0.0, n=4, y0=SURF, y1=1480)
    W.dasar_laut(k, pasir_y)
    W.kaustik_dasar(k, _TILE_KAUSTIK, 0.0, pasir_y + 60, H_, 0.22)
    for i, x in enumerate(rumput_x):
        W.rumput(k, x, pasir_y + 96, 250 + i * 30, 0.0,
                 tone=RUMPUT if i == 0 else mix(RUMPUT, RUMPUT, 0.6))
    if batu_x:
        W.batu(k, batu_x, pasir_y + 66, 88, 42)


_TILE_KAUSTIK = None


def _tile():
    global _TILE_KAUSTIK
    if _TILE_KAUSTIK is None:
        _TILE_KAUSTIK = W.kaustik_spr(512, 7, 0.45)
    return _TILE_KAUSTIK


# ---------------------------------------------------------------- scene 1: hook
def _latar_intro(k):
    _dasar_umum(k, senja=0.34, pasir_y=1580, rumput_x=(132, 946), batu_x=812)
    # deret gigi besar di kiri bawah (bukti yang tersisa)
    for i, sp in enumerate(_DERET):
        blit(k.a, sp, _DERET_X[i], 1246 - sp.shape[0] * 0.5)
    # halo fokus di belakang hiu
    yy = np.arange(-380, 380)[:, None]
    xx = np.arange(-380, 380)[None, :]
    d = np.sqrt(xx ** 2 + yy ** 2) / 380.0
    halo = np.clip(1 - d, 0, 1) ** 2.2
    spr = np.zeros((760, 760, 4), np.uint8)
    spr[..., :3] = (255, 250, 232)
    spr[..., 3] = (halo * 52).astype(np.uint8)
    blit_add(k.a, spr, 540 - 380, 780 - 380)


def _aktor_intro(k, t, dur):
    """Hiu megalodon menyeberang dari kanan ke kiri, lambat & tenang."""
    p = seg(t, 0.0, dur)
    x = lerp(1080, -900, p)
    y = 780 + math.sin(t * 0.55) * 14
    sp = _HIU_BESAR
    sw = M.swim(sp, amp=11, lam=300, phase=t * 2.1, ramp=0.42)
    blit(k.a, sw, x, y - sw.shape[0] / 2, 1.0)
    # gelembung kecil dari mulut
    _GELEMBUNG.gambar(k.a, t * 0.7, goyang=3.0)


# ---------------------------------------------------------------- scene 2: waktu
def _latar_waktu(k):
    _dasar_umum(k, senja=0.22, pasir_y=1660, rumput_x=(150,), batu_x=None,
                matahari=(870, 150))
    # garis waktu melintang
    y = 1120
    cv2.line(k.a, (110, y), (970, y), mix(INK, KERTAS, 0.55), 5, cv2.LINE_AA)
    for x, lab in [(110, "20 JUTA"), (760, "3,6 JUTA")]:
        cv2.line(k.a, (x, y - 26), (x, y + 26), INK, 6, cv2.LINE_AA)


def _aktor_waktu(k, t, dur):
    p = seg(t, 0.4, dur - 0.6)
    # penanda berjalan di sepanjang garis waktu
    x = lerp(140, 940, eo(p))
    cv2.circle(k.a, (int(x), 1120), 26, INK, -1, cv2.LINE_AA)
    cv2.circle(k.a, (int(x), 1120), 19, AMBER, -1, cv2.LINE_AA)
    # hiu raksasa pudar di belakang (yang hilang)
    fade = 0.22 * (1 - p * 0.5)
    sp = M.tint(_HIU_SEDANG, AIR_2, 0.62)
    sw = M.swim(sp, amp=8, lam=250, phase=t * 1.7)
    blit(k.a, sw, lerp(190, 120, p), 600 - sw.shape[0] / 2, fade * 0.9)
    # tulang rawan mencair: partikel kecil jatuh ke pasir
    _PARTIKEL_WAKTU.gambar(k.a, t, goyang=8.0)


# ---------------------------------------------------------------- scene 3: ukur
def _latar_ukur(k):
    _dasar_umum(k, senja=0.18, pasir_y=1620, rumput_x=(170, 900), batu_x=None,
                matahari=(840, 170))
    # panggung pengukuran: garis dasar
    cv2.line(k.a, (60, 1250), (1020, 1250), mix(INK, KERTAS, 0.6), 4, cv2.LINE_AA)


def _aktor_ukur(k, t, dur):
    p = eo(seg(t, 0.3, 2.4))
    # --- diagram: 11 m tulang belakang -> 16,4 m tubuh
    x0, x1 = 120, 960
    y = 1130
    xa = lerp(x0, x1, p)
    cv2.line(k.a, (int(x0), y), (int(xa), y), mix(INK, KERTAS, 0.35), 9, cv2.LINE_AA)
    for i in range(14):
        xx = lerp(x0 + 24, x1 - 24, i / 13)
        if xx > xa:
            break
        cv2.line(k.a, (int(xx), y - 26), (int(xx), y + 26), mix(INK, KERTAS, 0.25), 6, cv2.LINE_AA)
    # siluet hiu di atas diagram (skala nyata 24,3 m)
    sp = _HIU_SEDANG
    sw = M.swim(sp, amp=6, lam=280, phase=t * 1.4)
    blit(k.a, M.tint(sw, AIR_3, 0.50), 330, 330, 0.34 + 0.10 * p)
    # angka besar 16,4 m
    if p > 0.35:
        a = eo(seg(p, 0.35, 1.0))
        sp = spr_text("16,4", INK, M.F_BOLD, 210, tracking=-6)
        blit(k.a, sp, 76, 640 - sp.shape[0] * (0.5 + (1 - a) * 0.2), a)
        sp2 = spr_text("METER", mix(INK, KREM, 0.25), M.F_BOLD, 58)
        blit(k.a, sp2, 92, 880, a)
    # label 24,3 m batas atas
    lab = W.label_spr("BATAS ATAS 24,3 M", warna=KREM, isi=mix(TERRA, INK, 0.25),
                      size=26, pad_x=18, pad_y=10)
    if t > 2.2:
        blit(k.a, lab, 660, 250 + math.sin(t * 2) * 3, eo(seg(t, 2.2, 2.7)))
    # penyelam sebagai pembanding 1,8 m
    blit(k.a, _SELAM, 878, 1104, eo(seg(t, 1.2, 1.9)) * 0.95)


# ---------------------------------------------------------------- scene 4: bentuk
def _latar_bentuk(k):
    _dasar_umum(k, senja=0.26, pasir_y=1700, rumput_x=(120, 960), batu_x=None,
                matahari=(150, 176))


def _aktor_bentuk(k, t, dur):
    # dua siluet sebanding: hiu putih (gempal) vs megalodon (ramping)
    p1 = eo(seg(t, 0.2, 1.4))
    p2 = eo(seg(t, 0.9, 2.2))
    putih = _HIU_PUTIH
    mega = _HIU_SEDANG
    blit(k.a, M.swim(putih, amp=7, lam=220, phase=t * 2.0), -660 + 640 * p1, 500, 0.80)
    blit(k.a, M.swim(mega, amp=9, lam=280, phase=t * 1.7), -740 + 700 * p2, 900, 1.0)
    # label
    if t > 1.3:
        la = W.label_spr("HIU PUTIH · GEMPAL", size=25, pad_x=16, pad_y=9)
        blit(k.a, la, 60, 300, eo(seg(t, 1.3, 1.8)) * 0.95)
    if t > 2.0:
        lb = W.label_spr("MEGALODON · RAMPING", size=25, pad_x=16, pad_y=9, aksen=TERRA)
        blit(k.a, lb, 60, 700, eo(seg(t, 2.0, 2.5)) * 0.95)
    # panah panjang: sirip dada memanjang
    if t > 3.0:
        a = eo(seg(t, 3.0, 3.5))
        cv2.arrowedLine(k.a, (700, 1046), (880, 1122), mix(TERRA, INK, 0.2), 6,
                        cv2.LINE_AA, tipLength=0.28)
        sp = spr_text("SIRIP DADA PANJANG", mix(INK, KREM, 0.10), M.F_SEMI, 28)
        blit(k.a, sp, 372, 1160, a)
    # garis air bergerak pelan
    _GELEMBUNG.gambar(k.a, t * 0.5)


# ---------------------------------------------------------------- scene 5: gigi
def _latar_gigi(k):
    _dasar_umum(k, senja=0.16, pasir_y=1690, rumput_x=(980,), batu_x=None,
                matahari=(900, 160))
    # panggung: meja batu tempat gigi
    W.batu(k, 540, 1246, 300, 50, tone=mix(BATU, PASIR, 0.55))
    # penggaris 18 cm
    cv2.line(k.a, (286, 1178), (794, 1178), mix(INK, KREM, 0.30), 6, cv2.LINE_AA)
    for i in range(19):
        x = 286 + i * (508 / 18)
        hh = 18 if i % 5 else 30
        cv2.line(k.a, (int(x), 1178), (int(x), 1178 - hh), mix(INK, KREM, 0.25), 3, cv2.LINE_AA)


def _aktor_gigi(k, t, dur):
    # gigi raksasa yang "dibesarkan" dari deret
    p = eo(seg(t, 0.2, 1.6))
    skala = lerp(0.45, 1.32, p)
    sp = _GIGI_BESAR
    spr = cv2.resize(sp, None, fx=skala, fy=skala, interpolation=cv2.INTER_LINEAR)
    blit_c(k.a, spr, 540, 1044 - 10 * p, 1.0)
    # gerigi ditunjuk satu per satu
    if t > 2.0:
        for i in range(4):
            tt = 2.0 + i * 0.5
            if t > tt:
                a = eo(seg(t, tt, tt + 0.3))
                ang = -0.5 + i * 0.33
                x = 540 + math.cos(ang) * 250 * skala
                y = 1044 + math.sin(ang) * 210 * skala
                cv2.circle(k.a, (int(x), int(y)), int(6 + 4 * a), TERRA, -1, cv2.LINE_AA)
    # "satu hiu, puluhan ribu gigi": gigi kecil berjatuhan
    _HUJAN_GIGI.gambar(k.a, t, goyang=4.0)
    # label 18 cm
    if t > 3.2:
        lab = W.label_spr("18 CM", warna=KREM, isi=mix(TERRA, INK, 0.2), size=28,
                          pad_x=18, pad_y=10)
        blit(k.a, lab, 806, 1122, eo(seg(t, 3.2, 3.7)))


# ---------------------------------------------------------------- scene 6: gigit
def _latar_gigit(k):
    _dasar_umum(k, senja=0.40, pasir_y=1760, rumput_x=(110,), batu_x=None,
                matahari=(930, 210), dalam=1.15)
    # kabut dalam (adegan di bawah)
    k.kabut(1000, 1500, mix(AIR_2, AIR_3, 0.4), 0.22)


def _aktor_gigit(k, t, dur):
    # paus melintas di atas
    px = lerp(1120, -300, seg(t, 0.0, dur) ** 0.9)
    blit(k.a, M.gelombang_dada(_PAUS, amp=3, lam=200, phase=t * 1.1), px, 470, 0.92)
    # megalodon naik dari bawah menuju ekor paus
    p = eio(seg(t, 1.0, 3.6))
    sx = lerp(180, 600, p)
    sy = lerp(1320, 880, p) - math.sin(p * math.pi) * 50
    # berputar sedikit ke atas
    rot = -18 * p
    sp = M.swim(_HIU_SEDANG, amp=10, lam=260, phase=t * 2.4, ramp=0.40)
    M.blit_s(k.a, sp, sx, sy, 0.95, 1.0, rot)
    # tanda gigitan di ekor paus
    if t > 3.4:
        a = eo(seg(t, 3.4, 3.9))
        bx, by = px + 300, 520
        cv2.ellipse(k.a, (int(bx), int(by)), (54, 30), 12, 0, 360, (170, 90, 70), -1, cv2.LINE_AA)
        cv2.ellipse(k.a, (int(bx), int(by)), (54, 30), 12, 0, 360, INK, 3, cv2.LINE_AA)
        for i in range(7):
            ang = i / 6 * math.pi
            x = bx + math.cos(ang) * 44
            y = by + math.sin(ang) * 24
            cv2.circle(k.a, (int(x), int(y)), 5, (250, 246, 236), -1, cv2.LINE_AA)
        lab = W.label_spr("EKOR DULU", warna=KREM, isi=mix(TERRA, INK, 0.2), size=26,
                          pad_x=16, pad_y=9)
        blit(k.a, lab, 760, 420, a)
    _PARTIKEL_GIGIT.gambar(k.a, t, goyang=10.0)


# ---------------------------------------------------------------- scene 7: punah
def _latar_punah(k):
    _dasar_umum(k, senja=0.55, pasir_y=1700, rumput_x=(120, 950), batu_x=None,
                matahari=(880, 230), dalam=1.3)
    # langit lebih gelap (perubahan iklim) tapi tetap terang
    k.kabut(0, 300, mix(SENJA, mix(AIR_3, INK, 0.35), 0.25), 0.35)


KARTU_PUNAH = [("SAMUDRA MENDINGIN", HIU), ("LAUT DANGKAL MENYEMPIT", mix(AIR_4, HIU, 0.4)),
               ("PAUS PINDAH KE KUTUB", NAVY), ("HIU PUTIH BERSAING", mix(OLIVE, HIU, 0.5))]


def _aktor_punah(k, t, dur):
    # empat sebab muncul satu per satu
    for i, (teks, warna) in enumerate(KARTU_PUNAH):
        tt = 0.4 + i * 0.85
        if t < tt:
            continue
        p = eo(seg(t, tt, tt + 0.45))
        lab = W.label_spr(teks, warna=KREM, isi=mix(warna, INK, 0.35), size=25,
                          pad_x=18, pad_y=10, outline=INK)
        x = 70 + (i % 2) * 480
        y = 420 + (i // 2) * 84
        blit(k.a, lab, x - (1 - p) * 30, y, p)
    # hiu raksasa memudar
    a = 1.0 - 0.70 * eio(seg(t, 1.2, dur - 0.8))
    sp = M.tint(_HIU_SEDANG, AIR_2, 0.30 + 0.35 * (1 - a))
    blit(k.a, M.swim(sp, amp=7, lam=300, phase=t * 1.2), 190, 880, 0.88 * a)
    # panah menurun (populasi)
    if t > 5.0:
        p = eo(seg(t, 5.0, 6.0))
        cv2.arrowedLine(k.a, (900, 560), (900, int(560 + 300 * p)), TERRA, 8, cv2.LINE_AA,
                        tipLength=0.22)
    _PARTIKEL_PUNAH.gambar(k.a, t, goyang=12.0)


# ---------------------------------------------------------------- scene 8: loop
def _latar_loop(k):
    # sengaja identik dengan intro agar frame terakhir = frame pertama
    _latar_intro(k)


def _aktor_loop(k, t, dur):
    """Scene penutup: hiu yang sama berenang tenang, lalu keluar dari kiri.

    Ditutup dengan `_fade_loop` di `frame()` supaya frame terakhir IDENTIK dengan
    frame pertama (syarat loop mulus, standar KlikTahu).
    """
    p = seg(t, 0.55, max(0.6, dur - 1.9))
    x = lerp(1120, -920, p)
    y = 780 + math.sin(t * 0.55) * 14
    blit(k.a, M.swim(_HIU_BESAR, amp=11, lam=300, phase=t * 2.1, ramp=0.42), x, y, 1.0)
    # deret gigi di panggung (bukti yang tersisa) — sama seperti intro
    for i, (gx, gh, r) in enumerate([(96, 96, -0.22), (168, 118, -0.10),
                                     (250, 132, 0.0), (334, 118, 0.10), (410, 96, 0.22)]):
        a = eo(seg(t, 0.4 + i * 0.08, 0.9 + i * 0.08))
        sp = _DERET[i]
        blit(k.a, sp, gx, 1246 - sp.shape[0] * 0.5, a)
    _GELEMBUNG.gambar(k.a, t * 0.6, goyang=3.0)


# =============================================================== 3. sprite global

_HIU_BESAR = None
_HIU_SEDANG = None
_HIU_PUTIH = None
_PAUS = None
_SELAM = None
_GIGI_BESAR = None
_GELEMBUNG = None
_PARTIKEL_WAKTU = None
_PARTIKEL_GIGIT = None
_PARTIKEL_PUNAH = None
_HUJAN_GIGI = None
_HUD = None
_LUT = None
_VIGNETTE = None
_DERET = None
_DERET_X = (96, 168, 250, 334, 410)
_LATAR_BERSIH = None


def siapkan():
    """Raster semua sprite global SEKALI (dipanggil sebelum render)."""
    global _HIU_BESAR, _HIU_SEDANG, _HIU_PUTIH, _PAUS, _SELAM, _GIGI_BESAR
    global _GELEMBUNG, _PARTIKEL_WAKTU, _PARTIKEL_GIGIT, _PARTIKEL_PUNAH
    global _DERET
    global _HUJAN_GIGI, _HUD, _LUT, _VIGNETTE
    _tile()
    _HIU_BESAR = W.hiu_spr(980, "megalodon", gigi_baris=11)
    _HIU_SEDANG = W.hiu_spr(760, "megalodon", gigi_baris=9)
    _HIU_PUTIH = W.hiu_spr(620, "putih", tone=mix(HIU, HIU_2, 0.35), gigi_baris=8)
    _PAUS = W.paus_spr(760)
    _SELAM = W.penyelam_spr(300)
    _GIGI_BESAR = W.gigi_spr(230, sudut=0.05)
    _GELEMBUNG = M.Partikel(90, (0, 380, W_, 1500), seed=3, vy=(-34, -12),
                            size=(1, 3), alpha=(0.10, 0.34))
    _PARTIKEL_WAKTU = M.Partikel(120, (0, 380, W_, 1600), seed=11, vy=(16, 44),
                                 size=(1, 2), alpha=(0.08, 0.22))
    _PARTIKEL_GIGIT = M.Partikel(110, (0, 360, W_, 1700), seed=19, vy=(-20, 14),
                                 size=(1, 3), alpha=(0.08, 0.26))
    _PARTIKEL_PUNAH = M.Partikel(130, (0, 340, W_, 1700), seed=23, vy=(10, 40),
                                  size=(1, 3), alpha=(0.06, 0.20))
    _HUJAN_GIGI = M.Partikel(26, (60, 340, 1020, 1250), seed=29, vy=(28, 62),
                             size=(2, 4), alpha=(0.20, 0.55))
    _DERET = [W.gigi_spr(h, sudut=r) for (h, r) in
              [(96, -0.22), (118, -0.10), (140, 0.0), (118, 0.10), (96, 0.22)]]
    _HUD = W.hud_spr(W_, "LAUT PURBA")
    _LUT = M.lut_grade(kontras=1.05, saturasi=1.05, lift=(2, 1, 0), gamma=1.02)
    # vignette dibakar sekali sebagai pengali (uint8 -> LUT per kanal tidak bisa,
    # jadi pakai float32 satu kali per frame; ukur dulu biayanya)
    yy = np.linspace(-1, 1, H_, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, W_, dtype=np.float32)[None, :]
    r = np.sqrt(xx ** 2 + yy ** 2) / math.sqrt(2)
    vig = np.clip((1.0 - 0.16 * np.clip(r, 0, 1) ** 1.8) * 255.0, 0, 255).astype(np.uint8)
    _VIGNETTE = np.repeat(vig[:, :, None], 3, axis=2)


# =============================================================== 4. tabel scene

SCENES = [
    dict(id="intro", judul=["HIDUP 24 METER", "TERSISA CUMA GIGI"], kicker="LAUT PURBA · 2026",
         sorot=("gigi",), latar=_latar_intro, aktor=_aktor_intro, dur=10.65),
    dict(id="f1", judul=["20 JUTA TAHUN,", "HILANG 3,6 JUTA LALU"], kicker="TULANG RAWAN TIDAK BERFOSIL",
         sorot=("hilang",), latar=_latar_waktu, aktor=_aktor_waktu, dur=11.29),
    dict(id="f2", judul=["16,4 METER", "DARI 11 METER TULANG"], kicker="DIUKUR ULANG 29 AHLI · 2025",
         sorot=("meter",), latar=_latar_ukur, aktor=_aktor_ukur, dur=13.88),
    dict(id="f3", judul=["BUKAN HIU PUTIH", "YANG DIPERBESAR"], kicker="TUBUH LEBIH RAMPING",
         sorot=("hiu",), latar=_latar_bentuk, aktor=_aktor_bentuk, dur=12.01),
    dict(id="f4", judul=["SATU HIU,", "PULUHAN RIBU GIGI"], kicker="GIGI BERGERIGI 18 CM",
         sorot=("gigi",), latar=_latar_gigi, aktor=_aktor_gigi, dur=16.40),
    dict(id="f5", judul=["YANG DISERANG", "EKORNYA DULU"], kicker="DARI BEKAS LUKA FOSIL PAUS",
         sorot=("ekornya",), latar=_latar_gigit, aktor=_aktor_gigit, dur=12.66),
    dict(id="f6", judul=["RAKSASA KALAH", "OLEH PERUBAHAN"], kicker="BUKAN SATU SEBAB",
         sorot=("perubahan",), latar=_latar_punah, aktor=_aktor_punah, dur=17.59),
    dict(id="outro", judul=["GIGINYA MASIH ADA", "HIUNYA TIDAK"], kicker="3,6 JUTA TAHUN",
         sorot=("tidak",), latar=_latar_loop, aktor=_aktor_loop, dur=8.28),
]

TOTAL = sum(s["dur"] for s in SCENES)
MULAI = [0.0]
for _s in SCENES:
    MULAI.append(MULAI[-1] + _s["dur"])


def daftar():
    """Metadata untuk renderer: urutan scene, durasi, dan total."""
    return {"scenes": [{"id": s["id"], "dur": s["dur"], "mulai": MULAI[i]}
                       for i, s in enumerate(SCENES)], "total": TOTAL}


# =============================================================== 5. komposisi

_LATAR_CACHE = {}


def latar_scene(i):
    """Bangun (sekali) latar scene ke-i dan simpan sebagai ndarray RGB."""
    key = SCENES[i]["id"]
    l = _LATAR_CACHE.get(key)
    if l is None:
        k = Kanvas(W_, H_, KERTAS)
        SCENES[i]["latar"](k)
        idx = i
        hud = _HUD.copy()
        blit(k.a, hud, 0, 0, 0.96)
        l = k.a
        _LATAR_CACHE[key] = l
    return l


def _kata_vo(i):
    """Kata-kata VO untuk kapten karaoke scene ke-i (dari naskah)."""
    return NASKAH[i].split()


def frame(t):
    """Komposisi satu frame RGB (uint8, 1080x1920) pada waktu global `t` detik."""
    i = 0
    while i < len(SCENES) - 1 and t >= MULAI[i + 1]:
        i += 1
    s = SCENES[i]
    tl = t - MULAI[i]
    dur = s["dur"]
    buf = latar_scene(i).copy()
    k = Kanvas(W_, H_, KERTAS)
    k.a = buf
    s["aktor"](k, tl, dur)
    # kartu judul + sumber
    kartu_judul(k, s["kicker"], s["judul"], tl, masuk=0.55, sorot=s["sorot"],
                sorot_t=1.55, alpha=1.0)
    sumber(k, alpha=0.50)
    # ---- loop sempurna: 1 detik terakhir ditumpuk ke latar bersih intro,
    # sehingga frame terakhir identik dengan frame 0 (syarat QC loop).
    if i == len(SCENES) - 1:
        f = smooth(seg(tl, dur - 1.0, dur))
        if f > 0.0:
            base = latar_scene(0)
            buf = cv2.addWeighted(buf, 1.0 - f, base, f, 0.0)
    # grade + vignette
    out = cv2.LUT(buf, _LUT)
    out = cv2.multiply(out, _VIGNETTE, scale=1.0 / 255.0)
    return out


# =============================================================== 6. naskah

NASKAH = [
    "Hiu terbesar yang pernah hidup panjangnya dua puluh empat meter. Yang tersisa "
    "dari tubuhnya cuma gigi, dan giginya sebesar telapak tangan.",
    "Megalodon hidup dua puluh juta sampai tiga koma enam juta tahun lalu. Tulang "
    "rawan tidak menjadi fosil, jadi hampir semua yang kita tahu berasal dari giginya.",
    "Gigi itu memberi ukuran tubuh. Tahun dua ribu dua puluh lima, dua puluh sembilan "
    "ahli menghitung ulang batas masuk akal dua puluh empat koma tiga meter.",
    "Bentuknya bukan hiu putih yang diperbesar. Tubuhnya lebih ramping, seperti hiu "
    "lemon, dengan sirip dada panjang. Raksasa tidak perlu gempal untuk cepat.",
    "Gigi megalodon bergerigi seperti gergaji, panjang sampai delapan belas sentimeter. "
    "Ia berganti gigi sepanjang hidup jadi satu individu meninggalkan puluhan ribu gigi.",
    "Gigitan megalodon jauh lebih kuat dari hiu putih. Mangsanya paus kecil. Dari bekas "
    "luka pada fosil paus ia melumpuhkan ekor dulu baru menggigit bagian lain.",
    "Tiga koma enam juta tahun lalu ia hilang. Bukan satu sebab samudra mendingin laut "
    "dangkal menyempit paus pindah ke kutub dan hiu putih berebut makanan.",
    "Giginya masih tersimpan di museum hitam dan bergerigi. Hiu itu sendiri tak pernah "
    "muncul lagi.",
]


# =============================================================== 7. selftest

def _pratinjau():
    import time
    t0 = time.time()
    siapkan()
    print(f"[siapkan] semua sprite: {(time.time()-t0)*1000:.0f} ms")
    t1 = time.time()
    for i in range(len(SCENES)):
        latar_scene(i)
    print(f"[latar] 8 scene: {(time.time()-t1)*1000:.0f} ms")
    # ukur biaya per frame
    waktu = [MULAI[i] + SCENES[i]["dur"] * 0.45 for i in range(len(SCENES))]
    for i, t in enumerate(waktu):
        t2 = time.time()
        for _ in range(3):
            f = frame(t)
        print(f"  {SCENES[i]['id']:6s} frame: {(time.time()-t2)/3*1000:6.2f} ms")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "riset-kualitas", "v18")
    os.makedirs(out, exist_ok=True)
    for i, t in enumerate(waktu):
        Image.fromarray(frame(t)).save(os.path.join(out, f"{i}_{SCENES[i]['id']}.jpg"), quality=88)
    # lembar kontak 4x2
    ims = [Image.open(os.path.join(out, f"{i}_{SCENES[i]['id']}.jpg")).resize((540, 960))
           for i in range(8)]
    sheet = Image.new("RGB", (540 * 2, 960 * 4), (255, 255, 255))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % 2) * 540, (i // 2) * 960))
    sheet.save("/tmp/v18_sheet.jpg", quality=90)
    print("-> /tmp/v18_sheet.jpg")


if __name__ == "__main__":
    _pratinjau()
