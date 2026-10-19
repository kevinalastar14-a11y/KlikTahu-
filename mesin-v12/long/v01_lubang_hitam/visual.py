#!/usr/bin/env python3
"""Visual Long01 - "Apa yang Terjadi Kalau Kamu Masuk ke Lubang Hitam?" (16:9).

Setiap bab = beberapa shot yang dikunci ke KATA narasi (C.w("kata")). BEATS memakai
kata yang sama, jadi SFX & dorongan kamera jatuh tepat saat elemen muncul.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

import mesin_long as L
from mesin_long import (D, S, W, H, mix, clamp, seg, eo, eio, eob, esmooth, teks, judul, kaca, chip,
                        stiker, stempel, angka, callout, panah, centang, partikel, glow, garis_ukur,
                        lubang_hitam, lubang_polos, bintang, bumi, astronot, roket, jam, galaksi,
                        parabola, mata, lebar, FB, FS, FM, TEKS, REDUP, ORANYE, EMAS, SIAN, MERAH,
                        UNGU, HIJAU, PANAS, SP0, KACA, WHITE)

HERE = os.path.dirname(os.path.abspath(__file__))
DRIFT = 1.0


def muncul(C, key, n=1, off=0.0, d=0.45):
    """alpha naik + offset y turun (slide-up) sejak kata."""
    q = C.u(key, d, n, off, ease=eo)
    return q, (1 - q) * 36


def jendela(C, k0, k1, n0=1, n1=1, o0=-0.25, o1=-0.25, fi=0.45, fo=0.45):
    a = C.w(k0, n0, o0) if isinstance(k0, str) else k0
    b = C.w(k1, n1, o1) if isinstance(k1, str) else k1
    return C.win(a, b, fi, fo)


def silang_besar(img, cx, cy, r, tt, alpha=1.0, col=MERAH):
    if tt <= 0 or alpha <= 0.01:
        return
    q = esmooth(clamp(tt / 0.35))
    a = r
    D.line_on(img, (cx - a, cy - a), (cx - a + 2 * a * min(1, q * 2), cy - a + 2 * a * min(1, q * 2)), col, 14, alpha)
    if q > 0.5:
        k = (q - 0.5) * 2
        D.line_on(img, (cx + a, cy - a), (cx + a - 2 * a * k, cy - a + 2 * a * k), col, 14, alpha)


def coret(img, x0, x1, y, tt, alpha=1.0, col=MERAH):
    if tt <= 0:
        return
    q = esmooth(clamp(tt / 0.3))
    D.line_on(img, (x0, y), (x0 + (x1 - x0) * q, y), col, 8, alpha)


def kaca_teks(img, cx, cy, judul_, isi, alpha, acc, w=520, h=150, dy=0.0, fsz=40, isifsz=24):
    kaca(img, cx - w / 2, cy - h / 2 + dy, cx + w / 2, cy + h / 2 + dy, alpha, acc)
    teks(img, cx, cy - (18 if isi else 0) + dy, judul_, fsz, TEKS, alpha, name=FB)
    if isi:
        teks(img, cx, cy + fsz * 0.72 + dy, isi, isifsz, REDUP, alpha, name=FS)


def atom(img, cx, cy, r, alpha, tg, col=SIAN):
    for k in range(3):
        pts = []
        for j in range(41):
            a = j / 40 * 2 * math.pi
            x, y = r * math.cos(a), r * 0.36 * math.sin(a)
            an = math.radians(k * 60 + tg * 8)
            pts.append((cx + x * math.cos(an) - y * math.sin(an), cy + x * math.sin(an) + y * math.cos(an)))
        L.M._pline(img, pts, col, 3, alpha)
        an = tg * 2.2 + k * 2.1
        x, y = r * math.cos(an), r * 0.36 * math.sin(an)
        a2 = math.radians(k * 60 + tg * 8)
        D.dot_on(img, cx + x * math.cos(a2) - y * math.sin(a2), cy + x * math.sin(a2) + y * math.cos(a2), 5, WHITE, alpha)
    D.dot_on(img, cx, cy, r * 0.16, ORANYE, alpha)


def kaca_pembesar(img, cx, cy, r, alpha, col=TEKS):
    D.ring_on(img, cx, cy, r, col, max(3, r * 0.14), alpha)
    D.dot_on(img, cx, cy, r * 0.9, (120, 170, 255), alpha * 0.18)
    a = math.radians(45)
    D.line_on(img, (cx + r * 1.05 * math.cos(a), cy + r * 1.05 * math.sin(a)),
              (cx + r * 2.0 * math.cos(a), cy + r * 2.0 * math.sin(a)), col, max(4, r * 0.24), alpha)


def sinar(img, pts, prog, col=EMAS, width=5, alpha=1.0, kepala=True):
    """Berkas cahaya: polyline yang menggambar diri + kepala bercahaya."""
    if prog <= 0 or alpha <= 0.01 or len(pts) < 2:
        return
    n = max(2, int(len(pts) * clamp(prog)))
    sub = pts[:n]
    L.M._pline(img, sub, col, width, alpha)
    if kepala and prog < 1:
        glow(img, sub[-1][0], sub[-1][1], 26, col, 0.8 * alpha)
        D.dot_on(img, sub[-1][0], sub[-1][1], width * 0.9, WHITE, alpha)


def bez_pts(p0, p1, p2, n=40):
    return [L.M._bez(p0, p1, p2, i / n) for i in range(n + 1)]


def satelit(img, cx, cy, s, alpha):
    D.rrect_on(img, cx - 12 * s, cy - 10 * s, cx + 12 * s, cy + 10 * s, 3 * s, (220, 224, 236), alpha)
    for sgn in (-1, 1):
        x0 = cx + sgn * 16 * s
        x1 = cx + sgn * 52 * s
        D.rrect_on(img, min(x0, x1), cy - 8 * s, max(x0, x1), cy + 8 * s, 2 * s, (60, 110, 200), alpha)
        D.line_on(img, (cx + sgn * 12 * s, cy), (x0, cy), (200, 200, 210), 2, alpha)


def penyedot(img, cx, cy, s, alpha):
    D.rrect_on(img, cx - 70 * s, cy - 10 * s, cx + 30 * s, cy + 60 * s, 26 * s, (120, 130, 160), alpha)
    D.dot_on(img, cx - 44 * s, cy + 62 * s, 16 * s, (60, 64, 84), alpha)
    D.dot_on(img, cx + 8 * s, cy + 62 * s, 16 * s, (60, 64, 84), alpha)
    pts = bez_pts((cx + 30 * s, cy + 10 * s), (cx + 120 * s, cy - 110 * s), (cx + 80 * s, cy - 150 * s), 24)
    L.M._pline(img, pts, (90, 96, 120), 12 * s, alpha)
    D.line_on(img, (cx + 80 * s, cy - 150 * s), (cx + 60 * s, cy + 70 * s), (170, 176, 196), 9 * s, alpha)
    D.rrect_on(img, cx + 30 * s, cy + 64 * s, cx + 100 * s, cy + 80 * s, 5 * s, (170, 176, 196), alpha)


def lubang_tanah(img, cx, cy, s, alpha):
    D.ell(img, cx - 150 * s, cy - 40 * s, cx + 150 * s, cy + 40 * s, fill=(110, 80, 60), alpha=alpha)
    D.ell(img, cx - 120 * s, cy - 28 * s, cx + 120 * s, cy + 30 * s, fill=(20, 14, 12), alpha=alpha)


def sekop_teks_sup(img, x, cy, base, sup, fsz, col, alpha):
    """Teks pangkat: '10' + pangkat kecil terangkat (font tak punya superskrip)."""
    wb = teks(img, x, cy, base, fsz, col, alpha, anchor="l")
    teks(img, x + wb + 4, cy - fsz * 0.45, sup, fsz * 0.55, col, alpha, anchor="l")
    return wb + lebar(sup, fsz * 0.55)


# ============================================================ BAB 0 - PEMBUKA
def v01_intro(img, C):
    tl, tg = C.tl, C.tg
    t_apa = C.w("apa", 1, -0.3)
    t_jwb = C.w("jawabannya", 1, -0.3)
    t_vid = C.w("video", 1, -0.5)
    t_smu = C.w("semuanya", 1, -0.3)
    t_siap = C.w("siap", 1, -0.25)
    t_pl = C.w("pulang")
    # ---- shot A: roket menuju lubang hitam
    aA = C.win(-1, t_apa, 0.01, 0.5)
    if aA > 0.01:
        C.zoom = 1.0 + 0.16 * esmooth(clamp(tl / t_apa))
        C.fx, C.fy = 0.62, 0.5
        lubang_hitam(img, 1330, 520, 118 + 10 * tl / t_apa, tg, aA, tilt=0.2)
        u = eio(clamp((tl + 0.6) / (t_pl + 1.2)))
        p0, p1, p2 = (60, 860), (420, 540), (930, 560)
        x, y = L.M._bez(p0, p1, p2, u)
        xb, yb = L.M._bez(p0, p1, p2, max(0, u - 0.02))
        ang = math.degrees(math.atan2(x - xb, -(y - yb))) if u > 0.01 else 60
        for k in range(12):
            uu = max(0, u - k * 0.012)
            px, py = L.M._bez(p0, p1, p2, uu)
            D.dot_on(img, px, py, 6 - k * 0.4, (255, 190, 120), aA * 0.5 * (1 - k / 12))
        roket(img, x, y, 150, ang, aA, api=1.0, tg=tg)
        callout(img, (1330, 520 - 150), (1520, 250), "LUBANG HITAM", C.tt("hitam", 1), TEKS, ORANYE, 30, aA)
        tp = C.tt("pulang", 1, -0.1)
        if tp > 0:
            pts = bez_pts((900, 600), (650, 820), (240, 720), 30)
            for j in range(0, 30, 2):
                if j / 30 < clamp(tp / 0.6):
                    D.line_on(img, pts[j], pts[j + 1], (200, 210, 235), 4, aA * 0.8)
            silang_besar(img, 560, 760, 34, tp - 0.4, aA)
            stiker(img, 560, 900, "TIDAK ADA JALAN PULANG", tp - 0.2, MERAH, 34, -3, tg, aA)
    # ---- shot B: tiga pertanyaan
    aB = C.win(t_apa, t_jwb, 0.4, 0.4)
    if aB > 0.01:
        lubang_hitam(img, 960, 560, 150, tg, aB * 0.35, tilt=0.2)
        kartu = [("lihat", 1, "Apa yang kamu", "LIHAT?", "mata"), ("rasakan", 1, "Apa yang kamu", "RASAKAN?", "astro"),
                 ("dilihat", 1, "Apa yang dilihat", "TEMANMU?", "dish")]
        for j, (kk, nn, l1, l2, ik) in enumerate(kartu):
            q, dy = muncul(C, kk, nn, -0.35)
            if q <= 0.01:
                continue
            cx = 400 + j * 560
            kaca(img, cx - 250, 310 + dy, cx + 250, 810 + dy, aB * q, [ORANYE, SIAN, UNGU][j])
            if ik == "mata":
                mata(img, cx, 460 + dy, 58, aB * q, tg)
            elif ik == "astro":
                astronot(img, cx, 460 + dy, 190, aB * q, rot=8 * math.sin(tg * 1.3))
            else:
                parabola(img, cx - 50, 480 + dy, 1.9, aB * q)
                astronot(img, cx + 75, 490 + dy, 115, aB * q)
            teks(img, cx, 625 + dy, l1, 34, REDUP, aB * q, name=FS)
            teks(img, cx, 705 + dy, l2, 66, [ORANYE, SIAN, UNGU][j], aB * q, name=FB)
    # ---- shot C: lebih aneh dari fiksi ilmiah
    aC = C.win(t_jwb, t_vid, 0.4, 0.4)
    if aC > 0.01:
        C.zoom = 1.0 + 0.06 * clamp((tl - t_jwb) / 4)
        lubang_hitam(img, 960, 470, 165, tg, aC, tilt=0.2)
        stempel(img, 960, 830, "LEBIH ANEH DARI FIKSI ILMIAH", C.tt("aneh"), UNGU, 50, -4, aC)
    # ---- shot D: peta perjalanan
    aD = C.win(t_vid, t_smu, 0.4, 0.4)
    if aD > 0.01:
        pts = bez_pts((230, 700), (960, 380), (1580, 620), 60)
        pr = C.u("jatuh", 0.9, 1, -0.2)
        for j in range(59):
            if j / 59 < pr:
                D.line_on(img, pts[j], pts[j + 1], (130, 140, 190), 5, aD * 0.9)
        lubang_hitam(img, 1650, 640, 70, tg, aD * pr, tilt=0.22)
        halte = [("tenang", 1, 0.05, "LUAR ANGKASA", "yang tenang", SIAN),
                 ("titik", 1, 0.55, "TITIK TANPA", "JALAN KEMBALI", MERAH),
                 ("dalam", 1, 0.93, "LEBIH DALAM", "lagi...", UNGU)]
        pos_u = 0.0
        for kk, nn, uu, a1, a2, col in halte:
            tt = C.tt(kk, nn, -0.2)
            if tt > 0:
                x, y = pts[int(uu * 60)]
                D.dot_on(img, x, y, 13 * eob(clamp(tt / 0.3), 2), col, aD)
                D.ring_on(img, x, y, 13 + 20 * clamp(tt / 0.6), col, 3, aD * (1 - clamp(tt / 0.6)))
                q = eo(clamp(tt / 0.4))
                teks(img, x, y - 130 + (1 - q) * 20, a1, 44, col, aD * q)
                teks(img, x, y - 80 + (1 - q) * 20, a2, 32, TEKS, aD * q, name=FS)
                pos_u = max(pos_u, uu * esmooth(clamp(tt / 0.8)) + pos_u * (1 - esmooth(clamp(tt / 0.8))))
        x, y = pts[min(60, int(max(pos_u, 0.0) * 60))]
        astronot(img, x, y + 70, 90, aD * pr, rot=10 * math.sin(tg * 1.5))
    # ---- shot E: fisika & teleskop
    aE = C.win(t_smu, t_siap, 0.4, 0.4)
    if aE > 0.01:
        q1, d1 = muncul(C, "fisika", 1, -0.3)
        q2, d2 = muncul(C, "pengamatan", 1, -0.3)
        kaca(img, 250, 300 + d1, 910, 780 + d1, aE * q1, SIAN)
        atom(img, 580, 470 + d1, 110, aE * q1, tg)
        teks(img, 580, 650 + d1, "FISIKA YANG", 44, TEKS, aE * q1)
        teks(img, 580, 705 + d1, "SUDAH DIUJI", 44, SIAN, aE * q1)
        kaca(img, 1010, 300 + d2, 1670, 780 + d2, aE * q2, ORANYE)
        bumi(img, 1340, 480 + d2, 105, aE * q2)
        for j, an in enumerate([-60, -20, 25, 70]):
            a_ = math.radians(an - 90)
            if C.tt("teleskop", 1, -0.3 + j * 0.15) > 0:
                parabola(img, 1340 + 118 * math.cos(a_), 480 + d2 + 118 * math.sin(a_), 0.55, aE * q2, ang=an)
        teks(img, 1340, 650 + d2, "PENGAMATAN", 44, TEKS, aE * q2)
        teks(img, 1340, 705 + d2, "TELESKOP NYATA", 44, ORANYE, aE * q2)
    # ---- shot F: judul video
    aF = C.win(t_siap, C.dur + 1, 0.35, 0.3)
    if aF > 0.01:
        tf = tl - t_siap
        C.zoom = 1.0 + 0.10 * esmooth(clamp(tf / 5))
        lubang_hitam(img, 960, 400, 150 + 8 * tf, tg, aF, tilt=0.2)
        judul(img, 960, 800, "APA YANG TERJADI KALAU KAMU", tf - 0.1, 64, TEKS, alpha=aF, maxw=1700)
        judul(img, 960, 880, "MASUK KE LUBANG HITAM?", tf - 0.45, 76, TEKS, hl=("LUBANG", "HITAM?"),
              hlcol=ORANYE, alpha=aF, maxw=1700)
        stiker(img, 1560, 190, "SIAP?", C.tt("siap"), UNGU, 40, 6, tg, aF)
        tk = C.tt("kencangkan")
        if tk > 0:
            u = eio(clamp(tk / 2.2))
            roket(img, -100 + 1060 * u, 700 - 300 * u, 110 * (1 - 0.6 * u), 70, aF * (1 - clamp((u - 0.85) / 0.15)), tg=tg)


# ============================================================ BAB 1 - APA ITU
def v01_apa(img, C):
    tl, tg = C.tl, C.tg
    t_bkn = C.w("bukan", 1, -0.3)
    t_ia = C.w("ia", 1, -0.3)
    t_coba = C.w("coba", 1, -0.3)
    t_utk = C.w("untuk", 1, -0.3)
    t_skr = C.w("sekarang", 1, -0.3)
    t_kc = C.w("kuncinya", 1, -0.3)
    t_kl = C.w("kalau", 1, -0.3)
    # establishing (di bawah kartu bab)
    a0 = C.win(-1, t_bkn, 0.01, 0.4)
    if a0 > 0.01:
        C.zoom = 1.0 + 0.05 * clamp(tl / t_bkn)
        lubang_hitam(img, 960, 560, 160, tg, a0, tilt=0.2)
    # bukan lubang, bukan penyedot debu
    a1 = C.win(t_bkn, t_ia, 0.35, 0.35)
    if a1 > 0.01:
        q1, d1 = muncul(C, "bukan", 1, -0.2)
        q2, d2 = muncul(C, "bukan", 2, -0.2)
        kaca(img, 250, 260 + d1, 900, 800 + d1, a1 * q1, MERAH)
        lubang_tanah(img, 575, 470 + d1, 1.4, a1 * q1)
        silang_besar(img, 575, 470 + d1, 110, C.tt("lubang", 3, 0.1), a1)
        teks(img, 575, 700 + d1, "BUKAN LUBANG", 50, TEKS, a1 * q1)
        kaca(img, 1020, 260 + d2, 1670, 800 + d2, a1 * q2, MERAH)
        penyedot(img, 1310, 480 + d2, 1.3, a1 * q2)
        silang_besar(img, 1345, 470 + d2, 110, C.tt("penyedot", 1, 0.2), a1)
        teks(img, 1345, 700 + d2, "BUKAN PENYEDOT DEBU", 46, TEKS, a1 * q2)
    # gravitasi sangat kuat, cahaya tidak lolos
    a2 = C.win(t_ia, t_coba, 0.4, 0.4)
    if a2 > 0.01:
        cx, cy = 960, 470
        gq = C.u("gravitasi", 1.0, 1, -0.3)
        for k in range(9):
            rr = 110 + k * 70
            dep = 3200.0 / (rr + 20) * gq
            D.ring_on(img, cx, cy + 90 + dep * 0.6, rr * 1.2, (110, 120, 200), 2.5, a2 * 0.55 * gq, squash=0.28)
        for k in range(16):
            an = k * math.pi / 8
            pts = []
            for j in range(10):
                rr = 110 + j * 70
                dep = 3200.0 / (rr + 20) * gq
                pts.append((cx + rr * 1.2 * math.cos(an), cy + 90 + dep * 0.6 + rr * 1.2 * 0.28 * math.sin(an)))
            L.M._pline(img, pts, (110, 120, 200), 2, a2 * 0.4 * gq)
        lubang_hitam(img, cx, cy + 40, 100, tg, a2, disk=0.5, tilt=0.2)
        chip(img, 960, 190, "GRAVITASI SANGAT KUAT", a2 * C.u("gravitasi", 0.4, 1, -0.1), MERAH, 30)
        tc = C.tt("cahaya", 1, -0.2)
        for j, oy in enumerate((-190, -90, 190)):
            p0 = (160, cy + 40 + oy)
            pts = bez_pts(p0, (cx - 260, cy + 40 + oy * 0.9), (cx + 10 * (1 if oy < 0 else -1), cy + 40 + oy * 0.12), 40)
            sinar(img, pts, clamp((tc - j * 0.25) / 1.3), EMAS, 5, a2)
        stiker(img, 1500, 870, "CAHAYA PUN TIDAK LOLOS", C.tt("lolos", 1, -0.1), ORANYE, 34, -3, tg, a2)
    # lempar bola
    a3 = C.win(t_coba, t_utk, 0.4, 0.4)
    if a3 > 0.01:
        bumi(img, 960, 1900, 1050, a3, atmos=0.8)
        base = (760, 856)
        for j, (kk, nn, hmax, lab) in enumerate([("melempar", 1, 170, "PELAN"), ("kencang", 1, 330, "KENCANG"),
                                                  ("tinggi", 1, 560, "LEBIH KENCANG")]):
            tt = C.tt(kk, nn, -0.2)
            if tt <= 0:
                continue
            T = 1.3 + j * 0.3
            dx = 140 + j * 150
            u = clamp(tt / T)
            n = 30
            pts = [(base[0] + dx * i / n, base[1] - 4 * hmax * (i / n) * (1 - i / n)) for i in range(n + 1)]
            for i in range(0, int(n * u), 2):
                D.dot_on(img, pts[i][0], pts[i][1], 3.5, [SIAN, EMAS, ORANYE][j], a3 * 0.7)
            bx, by = pts[int(n * u)]
            D.dot_on(img, bx, by, 16, [SIAN, EMAS, ORANYE][j], a3)
            if u > 0.4:
                teks(img, base[0] + dx * 0.5, base[1] - hmax - 40, lab, 26, [SIAN, EMAS, ORANYE][j],
                     a3 * clamp((u - 0.4) / 0.2))
        judul(img, 1450, 330, "MAKIN KENCANG, MAKIN TINGGI", C.tt("makin", 1, -0.2), 44, TEKS, hl=("TINGGI",),
              alpha=a3, maxw=700)
    # roket & kecepatan lepas
    a4 = C.win(t_utk, t_skr, 0.4, 0.4)
    if a4 > 0.01:
        bumi(img, 520, 1500, 800, a4, atmos=0.8)
        tr = C.tt("roket", 1, -0.3)
        u = eio(clamp(tr / 3.2))
        roket(img, 520 + 140 * u, 690 - 900 * u * u, 150, 8 * u, a4, api=1.0 if tr > 0 else 0, tg=tg)
        if tr > 0:
            for k in range(14):
                uu = max(0, u - k * 0.025)
                D.dot_on(img, 520 + 140 * uu, 690 - 900 * uu * uu + 100, 10 - k * 0.6, (255, 200, 150),
                         a4 * 0.35 * (1 - k / 14))
        cx, cy, R = 1380, 560, 230
        kaca(img, cx - 330, cy - 300, cx + 330, cy + 250, a4, SIAN)
        pts = [(cx + R * math.cos(math.pi + math.pi * i / 40), cy + 60 + R * math.sin(math.pi + math.pi * i / 40))
               for i in range(41)]
        L.M._pline(img, pts, (80, 90, 130), 16, a4)
        v = 11.2 * eo(clamp(C.tt("sebelas", 1, -0.3) / 1.3))
        f = clamp(v / 16)
        L.M._pline(img, pts[: max(2, int(40 * f) + 1)], SIAN, 16, a4)
        an = math.pi + math.pi * f
        D.line_on(img, (cx, cy + 60), (cx + (R - 40) * math.cos(an), cy + 60 + (R - 40) * math.sin(an)), TEKS, 7, a4)
        D.dot_on(img, cx, cy + 60, 14, TEKS, a4)
        angka(img, cx, cy + 130, 11.2, C.tt("sebelas", 1, -0.3), 76, TEKS, 1.3, des=1, sub="KM PER DETIK", alpha=a4)
        teks(img, cx, cy - 250, "UNTUK LEPAS DARI BUMI", 28, REDUP, a4, name=FS)
        stiker(img, cx, cy + 300, "KECEPATAN LEPAS", C.tt("kecepatan", 1, -0.1), SIAN, 36, -3, tg, a4, fg=SP0)
    # perbandingan kecepatan
    a5 = C.win(t_skr, t_kc, 0.4, 0.4)
    if a5 > 0.01:
        kaca(img, 180, 230, 1740, 800, a5 * 0.9)
        rows = [("BUMI", "11,2 km/detik", 11.2, SIAN, ("sekarang", 1)),
                ("CAHAYA", "300.000 km/detik", 300000, EMAS, ("tiga", 1)),
                ("LUBANG HITAM", "LEBIH DARI CAHAYA", 420000, MERAH, ("melebihi", 1))]
        x0, x1 = 560, 1640
        for j, (nm, val, v, col, (kk, nn)) in enumerate(rows):
            tt = C.tt(kk, nn, -0.2)
            if tt <= 0:
                continue
            y = 350 + j * 170
            q = eo(clamp(tt / 1.2))
            teks(img, 230, y, nm, 38, col, a5 * clamp(tt / 0.3), anchor="l")
            wbar = max(8, (x1 - x0) * min(v, 300000) / 300000 * q)
            if v > 300000:
                wbar = (x1 - x0) * (1 + 0.12 * q) + 12 * math.sin(tg * 6)
                glow(img, x0 + wbar, y, 120, MERAH, 0.4 * a5 * q)
            D.rrect_on(img, x0, y - 24, x0 + wbar, y + 24, 12, col, a5)
            teks(img, x0 + (x1 - x0) * 0.5 if v > 30000 else x0 + wbar + 20, y + 58 if v > 30000 else y,
                 val, 28, TEKS, a5 * clamp((tt - 0.5) / 0.4), name=FS, anchor="m" if v > 30000 else "l")
        stempel(img, 960, 900, "TIDAK ADA YANG BISA KELUAR", C.tt("keluar", 1, -0.1), MERAH, 46, -3, a5)
    # berat vs padat
    a6 = C.win(t_kc, t_kl, 0.35, 0.35)
    if a6 > 0.01:
        q1, d1 = muncul(C, "bukan", 3, -0.2)
        q2, d2 = muncul(C, "tapi", 1, -0.2)
        teks(img, 960, 380 + d1, "BUKAN SEBERAPA BERAT", 70, REDUP, a6 * q1)
        coret(img, 960 - lebar("BUKAN SEBERAPA BERAT", 70) / 2 - 20, 960 + lebar("BUKAN SEBERAPA BERAT", 70) / 2 + 20,
              385 + d1, C.tt("berat", 1, 0.1), a6)
        judul(img, 960, 600, "TAPI SEBERAPA PADAT", C.tt("tapi", 1, -0.2), 92, TEKS, hl=("PADAT",), hlcol=EMAS,
              alpha=a6, maxw=1700)
        tp = C.tt("padat", 1, -0.1)
        if tp > 0:
            k = esmooth(clamp(tp / 0.8))
            D.dot_on(img, 960, 800, 60 - 40 * k, (200, 200, 230), a6)
            for j in range(8):
                an = j * math.pi / 4
                r0 = 150 - 60 * k
                panah(img, (960 + r0 * math.cos(an), 800 + r0 * 0.6 * math.sin(an)),
                      (960 + (r0 - 50) * math.cos(an), 800 + (r0 - 50) * 0.6 * math.sin(an)), EMAS, 5, a6, 1.0, 16)
    # bumi jadi kelereng
    a7 = C.win(t_kl, C.dur + 1, 0.35, 0.3)
    if a7 > 0.01:
        td = C.tt("dipadatkan", 1, -0.1)
        tk = C.w("kelereng") - C.w("dipadatkan", 1, -0.1)
        k = esmooth(clamp(td / max(0.6, tk)))
        r = 240 * (1 - k) + 12 * k
        tb = C.tt("lubang", 4, -0.1)
        C.zoom = 1.0 + 0.25 * esmooth(clamp((td - tk) / 1.2)) if td > tk else 1.0
        if tb < 0:
            bumi(img, 760, 540, r, a7)
            if 0 < td:
                for j in range(10):
                    an = j * math.pi / 5 + 0.3
                    r0 = r + 90 - 30 * math.sin(tg * 5)
                    panah(img, (760 + (r0 + 60) * math.cos(an), 540 + (r0 + 60) * math.sin(an)),
                          (760 + r0 * math.cos(an), 540 + r0 * math.sin(an)), SIAN, 5, a7 * (1 - k * 0.7), 1.0, 16)
        else:
            glow(img, 760, 540, 200, WHITE, 0.6 * a7 * (1 - clamp(tb / 0.4)))
            lubang_hitam(img, 760, 540, 12 + 28 * eob(clamp(tb / 0.5), 1.8), tg, a7, tilt=0.24)
        kaca(img, 1150, 330, 1720, 760, a7, SIAN)
        teks(img, 1435, 400, "BUMI DIPADATKAN", 34, TEKS, a7)
        teks(img, 1435, 500, "Ø 12.742 km", 44, REDUP, a7, name=FS)
        if C.tt("kelereng", 1, -0.2) > 0:
            D.line_on(img, (1300, 560), (1570, 560), REDUP, 3, a7)
        angka(img, 1435, 640, 1.8, C.tt("kelereng", 1, -0.2), 80, EMAS, 0.8, des=1, pre="± ", suf=" cm",
              alpha=a7, sub="SEUKURAN KELERENG")
        stiker(img, 760, 880, "JADI LUBANG HITAM!", C.tt("lubang", 4, 0.1), ORANYE, 38, -3, tg, a7)


# ============================================================ BAB 2 - LAHIR DARI BINTANG MATI
def v01_lahir(img, C):
    tl, tg = C.tl, C.tg
    cx, cy = 720, 540
    t_para = C.w("para", 1, -0.4)
    t_run = C.w("runtuh", 1, -0.1)
    t_led = C.w("meledak", 1, -0.08)
    t_lhr = C.w("lahirlah", 1, -0.1)
    aS = C.win(-1, t_para, 0.01, 0.5)
    if aS > 0.01:
        if tl < t_led:
            k_run = esmooth(clamp((tl - t_run) / max(0.3, t_led - t_run))) if tl > t_run else 0.0
            habis = C.u("habis", 1.6, 1, -0.2)
            col = mix((150, 190, 255), (255, 110, 60), habis)
            r = 215 * (1 - 0.78 * k_run * k_run) * (1 + 0.05 * habis)
            if k_run > 0:
                C.zoom = 1.0 + 0.05 * k_run
            bintang(img, cx, cy, r, col, aS, tg)
            tgv = C.tt("gravitasi", 1, -0.2)
            tnk = C.tt("reaksi", 1, -0.2)
            f_out = 1 - C.u("berhenti", 0.6, 1, -0.1)
            for j in range(8):
                an = j * math.pi / 4 + math.pi / 8
                if tgv > 0:
                    q = eo(clamp((tgv - j * 0.04) / 0.5))
                    r0 = r + 170 + 8 * math.sin(tg * 4)
                    panah(img, (cx + r0 * math.cos(an), cy + r0 * math.sin(an)),
                          (cx + (r + 40) * math.cos(an), cy + (r + 40) * math.sin(an)), MERAH, 9, aS, q, 28)
                an2 = j * math.pi / 4
                if tnk > 0 and f_out > 0.01:
                    q = eo(clamp((tnk - j * 0.04) / 0.5))
                    r1 = r + 20
                    panah(img, (cx + r1 * math.cos(an2), cy + r1 * math.sin(an2)),
                          (cx + (r1 + 110 + 8 * math.sin(tg * 5)) * math.cos(an2),
                           cy + (r1 + 110 + 8 * math.sin(tg * 5)) * math.sin(an2)), EMAS, 9, aS * f_out, q, 28)
            a_info = aS * (1 - k_run)
            q1, d1 = muncul(C, "gravitasi", 1, -0.2)
            if q1 > 0:
                kaca(img, 1180, 250 + d1, 1780, 390 + d1, a_info * q1, MERAH)
                teks(img, 1220, 300 + d1, "GRAVITASI", 42, MERAH, a_info * q1, anchor="l")
                teks(img, 1220, 350 + d1, "menarik semuanya ke dalam", 26, TEKS, a_info * q1, name=FS, anchor="l")
            q2, d2 = muncul(C, "reaksi", 1, -0.2)
            if q2 > 0:
                kaca(img, 1180, 420 + d2, 1780, 560 + d2, a_info * q2 * (0.4 + 0.6 * f_out), EMAS)
                teks(img, 1220, 470 + d2, "REAKSI NUKLIR", 42, EMAS, a_info * q2 * (0.4 + 0.6 * f_out), anchor="l")
                teks(img, 1220, 520 + d2, "mendorong ke luar", 26, TEKS, a_info * q2 * (0.4 + 0.6 * f_out),
                     name=FS, anchor="l")
            q3, d3 = muncul(C, "bahan", 1, -0.2)
            if q3 > 0:
                kaca(img, 1180, 590 + d3, 1780, 720 + d3, a_info * q3, None)
                teks(img, 1220, 628 + d3, "BAHAN BAKAR", 28, REDUP, a_info * q3, name=FS, anchor="l")
                D.rrect_on(img, 1220, 660 + d3, 1740, 690 + d3, 12, (40, 44, 70), a_info * q3)
                wb = 520 * (1 - habis)
                if wb > 4:
                    D.rrect_on(img, 1220, 660 + d3, 1220 + wb, 690 + d3, 12, mix(HIJAU, MERAH, habis), a_info * q3)
                teks(img, 1740, 628 + d3, f"{int(round(100 * (1 - habis)))}%", 28, TEKS, a_info * q3, anchor="r")
            tdp = C.tt("dua", 1, -0.2)
            if tdp > 0:
                q = eo(clamp(tdp / 0.4))
                kaca(img, 1180, 760, 1780, 880, a_info * q, ORANYE)
                bintang(img, 1250, 820, 18, (255, 210, 110), a_info * q, tg, korona=0.5)
                teks(img, 1300, 820, "MASSA > 20 × MATAHARI", 36, TEKS, a_info * q, anchor="l")
        else:
            te = tl - t_led
            if te < 0.5:
                D.rrect_on(img, -10, -10, W + 10, H + 10, 0, (255, 246, 230), 0.75 * (1 - te / 0.5) * aS)
            glow(img, cx, cy, 700, (255, 220, 170), 0.8 * aS * (1 - clamp(te / 1.2)))
            rr = 60 + 950 * eo(clamp(te / 2.6))
            D.ring_on(img, cx, cy, rr, PANAS, max(2, 14 * (1 - clamp(te / 2.6))), aS * (1 - clamp(te / 2.6)))
            rng = random.Random(8)
            for j in range(90):
                an = rng.random() * 6.283
                sp = rng.uniform(0.5, 1.0)
                dist = 30 + 760 * sp * eo(clamp(te / 4.0))
                colj = [ORANYE, UNGU, SIAN, PANAS, MERAH][j % 5]
                D.dot_on(img, cx + dist * math.cos(an), cy + dist * math.sin(an) * 0.9, rng.uniform(3, 8),
                         colj, aS * 0.85 * (1 - clamp((te - 1.5) / 4.0)))
            stiker(img, 1330, 250, "SUPERNOVA!", C.tt("supernova", 1, -0.3), ORANYE, 50, -4, tg, aS * (1 - clamp((te - 5) / 0.5)))
            if tl < t_lhr:
                tr2 = C.tt("runtuh", 2, -0.1)
                rc = 28 * (1 - 0.8 * esmooth(clamp(tr2 / 1.2))) if tr2 > 0 else 28
                bintang(img, cx, cy, rc, (200, 220, 255), aS * clamp((te - 0.15) / 0.4), tg, korona=1.4)
                callout(img, (cx + 20, cy - 20), (1150, 420), "INTI > 3 × MATAHARI", C.tt("tiga", 1, -0.2), TEKS, SIAN, 38, aS)
                tg2 = C.tt("gaya", 1, -0.3)
                if tg2 > 0:
                    for j in range(10):
                        an = j * math.pi / 5
                        r0 = 190 - 40 * ((tg2 * 1.4 + j * 0.1) % 1.0)
                        panah(img, (cx + r0 * math.cos(an), cy + r0 * math.sin(an)),
                              (cx + (r0 - 70) * math.cos(an), cy + (r0 - 70) * math.sin(an)), SIAN, 6,
                              aS * clamp(tg2 / 0.4), 1.0, 20)
                    stiker(img, 1330, 620, "TAK ADA YANG BISA MENAHAN", tg2, MERAH, 32, 3, tg, aS)
            else:
                tb = tl - t_lhr
                glow(img, cx, cy, 420, WHITE, 0.7 * aS * (1 - clamp(tb / 0.5)))
                C.zoom = 1.0 + 0.08 * esmooth(clamp(tb / 2.0))
                lubang_hitam(img, cx, cy, 30 + 90 * eob(clamp(tb / 0.7), 1.6), tg, aS, tilt=0.22)
                stiker(img, cx, 880, "LUBANG HITAM LAHIR!", tb - 0.2, ORANYE, 44, -3, tg, aS)
    aG = C.win(t_para, C.dur + 1, 0.5, 0.3)
    if aG > 0.01:
        C.zoom = 1.0 + 0.06 * clamp((tl - t_para) / 8)
        galaksi(img, 960, 590, 560, tg, aG, tilt=0.48, rot=20, spin=1.2)
        rng = random.Random(4)
        ts = C.tt("seratus", 1, -0.6)
        dim = 1 - 0.8 * C.u("gelap", 0.8, 1, -0.1)
        for j in range(80):
            rr = 520 * math.sqrt(rng.random())
            an = rng.random() * 6.283
            x, y = 960 + rr * math.cos(an), 590 + rr * 0.48 * math.sin(an)
            q = clamp((ts - j * 0.018) / 0.25)
            if q > 0:
                D.dot_on(img, x, y, 7 * q, (0, 0, 0), aG)
                D.ring_on(img, x, y, 8 * q, UNGU, 2.5, aG * dim)
        angka(img, 960, 175, 100000000, ts, 88, TEKS, 1.6, pre="± ", sub="LUBANG HITAM DI GALAKSI KITA", alpha=aG)
        tsul = C.tt("sulit", 1, -0.5)
        if tsul > 0:
            u = esmooth(clamp(tsul / 2.5))
            kaca_pembesar(img, 520 + 880 * u, 600 + 60 * math.sin(u * 6), 70, aG * clamp(tsul / 0.3))
            stiker(img, 960, 950, "SULIT DITEMUKAN", tsul - 0.2, UNGU, 40, -3, tg, aG)


# ============================================================ BAB 3 - WUJUD / PIRINGAN
def v01_piringan(img, C):
    tl, tg = C.tl, C.tg
    cx, cy, r = 960, 530, 150
    C.zoom = 1.0 + 0.14 * clamp(tl / C.dur)
    dsk = C.u("piringan", 2.0, 1, -0.4)
    lns = C.u("belakang", 1.4, 1, -0.3)
    br = C.u("bersinar", 0.5, 1, -0.1) * (1 - C.u("gravitasinya", 1.5, 1, 0))
    tgas = C.w("gas", 1, -0.3)
    lubang_hitam(img, cx, cy, r, tg, 1.0, disk=dsk, lens=lns, glow_a=1.0 + 1.2 * br,
                 photon=max(0.25, dsk), gumpal=dsk, tilt=0.21)
    # gas & debu berpilin masuk
    ag = C.win(tgas, C.w("piringan", 1, 2.5), 0.5, 1.2)
    if ag > 0.01:
        for j in range(110):
            ph = (j * 0.618) % 1.0
            u = (ph + (tl - tgas) * 0.22) % 1.0
            rr = r * (3.4 - 2.2 * u)
            an = j * 2.4 + u * 7.0
            D.dot_on(img, cx + rr * math.cos(an), cy + rr * 0.21 * math.sin(an), 2.5 + 2 * u,
                     mix((255, 170, 90), PANAS, u), ag * 0.8)
    # label awal
    callout(img, (cx - r * 0.7, cy - r * 0.7), (520, 250), "HITAM TOTAL", C.tt("total", 1, -0.2), TEKS, SIAN, 36,
            C.win(0, C.w("gas", 1, 0.3), 0.3, 0.5))
    a_lab = C.win(C.w("piringan", 1, -0.2), C.w("gravitasinya", 1, -0.3), 0.4, 0.4)
    if a_lab > 0.01:
        chip(img, 960, 860, "PIRINGAN AKRESI", a_lab * C.u("piringan", 0.4, 1, -0.2), ORANYE, 30)
        stiker(img, 1480, 250, "PANAS: JUTAAN DERAJAT", C.tt("jutaan", 1, -0.2), MERAH, 36, 4, tg, a_lab)
    # cahaya dibelokkan
    a_ray = C.win(C.w("membelokkan", 1, -0.3), C.w("bahkan", 1, -0.3), 0.4, 0.5)
    if a_ray > 0.01:
        tr = C.tt("membelokkan", 1, -0.3)
        for j, y0 in enumerate((cy - 330, cy - 230, cy + 230, cy + 330)):
            pts = []
            for i in range(61):
                x = 60 + (1800 * i / 60)
                dx = (x - cx) / 260.0
                dfl = -(y0 - cy) * 0.30 / (1 + dx * dx)
                tail = -(y0 - cy) * 0.12 * (0.5 + 0.5 * math.tanh(dx))
                pts.append((x, y0 + dfl + tail))
            sinar(img, pts, clamp((tr - j * 0.2) / 1.6), EMAS, 4, a_ray * 0.9)
        chip(img, 960, 150, "GRAVITASI MEMBELOKKAN CAHAYA", a_ray * clamp(tr / 0.4), EMAS, 28)
    # bintang di belakang bergeser & melengkung (lensa gravitasi)
    a_st = C.win(C.w("bintangbintang", 1, -0.3), C.w("bagian", 2, -0.3), 0.4, 0.5)
    if a_st > 0.01:
        lq = C.u("bergeser", 1.4, 1, -0.2)
        rng = random.Random(12)
        for j in range(34):
            an = rng.random() * 6.283
            rs = r * rng.uniform(1.25, 3.2)
            re_ = r * 1.55
            rd = rs + lq * (re_ * re_ / rs) * 0.8
            ln = lq * 0.35 * (re_ / rs)
            pts = [(cx + rd * math.cos(an + d), cy + rd * math.sin(an + d)) for d in (-ln / 2, 0, ln / 2)]
            if ln > 0.02:
                L.M._pline(img, pts, (230, 236, 255), 2, a_st * 0.45)
            else:
                D.dot_on(img, pts[1][0], pts[1][1], 3, (230, 236, 255), a_st * 0.6)
        tk = C.tt("kaca", 1, -0.3)
        if tk > 0:
            q = eo(clamp(tk / 0.4))
            kaca_pembesar(img, 1560, 800, 58, a_st * q)
            teks(img, 1560, 930, "SEPERTI KACA PEMBESAR", 30, TEKS, a_st * q)
    # cahaya dari belakang piringan dibelokkan ke atas & bawah
    a_bk = C.win(C.w("belakang", 1, -0.3), C.w("bagian", 2, -0.2), 0.4, 0.5)
    if a_bk > 0.01:
        ta = C.tt("atas", 1, -0.2)
        tb = C.tt("bawah", 1, -0.2)
        L.M._panah11(img, (cx + r * 2.6, cy - 12), (cx + r * 0.2, cy - r * 1.62), a_bk, clamp(ta / 0.7), EMAS, 7, -0.35, 24)
        L.M._panah11(img, (cx - r * 2.6, cy + 12), (cx - r * 0.2, cy + r * 1.5), a_bk, clamp(tb / 0.7), EMAS, 7, -0.35, 24)
        chip(img, 960, 150, "CAHAYA DARI BELAKANG PIRINGAN", a_bk * clamp(ta / 0.4 + 0.3), ORANYE, 28)
    # bayangan & mata
    a_sh = C.win(C.w("bayangan", 1, -0.3), C.dur + 1, 0.4, 0.3)
    if a_sh > 0.01:
        tsh = C.tt("bayangan", 1, -0.2)
        n = 40
        for k in range(n):
            if k / n < clamp(tsh / 0.8) and k % 2 == 0:
                a0, a1 = k * 2 * math.pi / n, (k + 1) * 2 * math.pi / n
                D.line_on(img, (cx + r * 0.92 * math.cos(a0), cy + r * 0.92 * math.sin(a0)),
                          (cx + r * 0.92 * math.cos(a1), cy + r * 0.92 * math.sin(a1)), SIAN, 4, a_sh)
        callout(img, (cx + r * 0.5, cy + r * 0.5), (1250, 850), "BAYANGAN", tsh - 0.3, TEKS, SIAN, 38, a_sh,
                sub="cahaya tak bisa kembali")
        tm = C.tt("matamu", 1, -0.6)
        if tm > 0:
            q = eo(clamp(tm / 0.4))
            mata(img, 250, 530, 46, a_sh * q, tg)
            for sgn in (-1, 1):
                p1 = (330, 530)
                p2 = (cx - r * 0.2, cy + sgn * r * 0.98)
                for k in range(12):
                    if k % 2 == 0 and k / 12 < clamp(tm / 0.7):
                        D.line_on(img, (p1[0] + (p2[0] - p1[0]) * k / 12, p1[1] + (p2[1] - p1[1]) * k / 12),
                                  (p1[0] + (p2[0] - p1[0]) * (k + 1) / 12, p1[1] + (p2[1] - p1[1]) * (k + 1) / 12),
                                  (200, 210, 240), 3, a_sh * q)


# ============================================================ BAB 4 - FOTO ASLI
_FT = {}


def _sgra_img(n=420):
    import numpy as np
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = n / 2
    rr = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / n
    an = np.arctan2(yy - c, xx - c)
    ring = np.exp(-((rr - 0.26) / 0.06) ** 2)
    knot = 0.55 + 0.45 * (np.exp(-((np.angle(np.exp(1j * (an - 0.4)))) / 0.5) ** 2)
                          + np.exp(-((np.angle(np.exp(1j * (an - 2.6)))) / 0.5) ** 2)
                          + 0.8 * np.exp(-((np.angle(np.exp(1j * (an + 1.6)))) / 0.5) ** 2))
    v = np.clip(ring * knot, 0, 1)
    rgb = np.stack([np.clip(v * 1.7, 0, 1), np.clip(v * 1.5 - 0.35, 0, 1), np.clip(v * 1.4 - 0.8, 0, 1)], -1)
    im = Image.fromarray((rgb * 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(n * 0.02))
    return im


def foto(img, cx, cy, size, alpha, jenis, tt, label=""):
    if alpha <= 0.01 or tt <= 0:
        return
    key = (jenis, int(size), round(D.SS, 3))
    spr = _FT.get(key)
    if spr is None:
        src = Image.open(os.path.join(HERE, "aset", "m87_eht.png")).convert("RGB") if jenis == "m87" else _sgra_img()
        n = int(S(size))
        b = int(S(10))
        spr = Image.new("RGBA", (n + 2 * b, n + 2 * b), (0, 0, 0, 0))
        ImageDraw.Draw(spr).rounded_rectangle([0, 0, spr.width - 1, spr.height - 1], radius=int(S(14)),
                                              fill=(235, 238, 248, 255))
        spr.paste(src.resize((n, n), Image.LANCZOS), (b, b))
        _FT[key] = spr
    k = eob(clamp(tt / 0.45), 1.8)
    s2 = spr.resize((max(2, int(spr.width * k)), max(2, int(spr.height * k))), Image.BICUBIC) if abs(k - 1) > 0.01 else spr
    L._put_c(img, s2, cx, cy, alpha * clamp(tt / 0.15))
    if 0 < tt < 0.45:
        glow(img, cx, cy, size * 1.2, WHITE, 0.8 * (1 - tt / 0.45) * alpha)
    if label:
        teks(img, cx, cy + size / 2 + 34, label, 20, REDUP, alpha * clamp((tt - 0.4) / 0.3), name=FS)


def v01_foto(img, C):
    tl, tg = C.tl, C.tg
    t_pada = C.w("pada", 1, -0.3)
    t_mrk = C.w("mereka", 1, -0.3)
    t_sas = C.w("sasarannya", 1, -0.3)
    t_has = C.w("hasilnya", 1, -0.3)
    t_tiga = C.w("tiga", 1, -0.3)
    a0 = C.win(-1, t_pada, 0.01, 0.4)
    if a0 > 0.01:
        lubang_hitam(img, 960, 520, 150, tg, a0 * 0.7, tilt=0.2)
        stempel(img, 960, 540, "BUKAN SEKADAR TEORI", C.tt("bukan", 1, -0.1), EMAS, 60, -4, a0)
    a1 = C.win(t_pada, t_mrk, 0.4, 0.4)
    if a1 > 0.01:
        ty = C.tt("dua", 1, -0.3)
        angka(img, 960, 440, 2019, ty, 200, TEKS, 1.4, awal=2000, alpha=a1, ribuan=False)
        glow(img, 960, 440, 500, ORANYE, 0.18 * a1)
        chip(img, 960, 660, "FOTO PERTAMA LUBANG HITAM DALAM SEJARAH", a1 * C.u("foto", 0.4, 1, -0.2), ORANYE, 30)
        tf = C.tt("memamerkan", 1, 0.0)
        if 0 < tf < 0.4:
            D.rrect_on(img, -10, -10, W + 10, H + 10, 0, WHITE, 0.6 * (1 - tf / 0.4) * a1)
    a2 = C.win(t_mrk, t_sas, 0.4, 0.4)
    if a2 > 0.01:
        ex, ey, er = 960, 560, 280
        bumi(img, ex, ey, er, a2)
        pos = [(-0.55, -0.35), (-0.30, 0.10), (-0.62, 0.35), (0.10, -0.55), (0.22, 0.05), (0.55, -0.22),
               (0.42, 0.45), (0.0, 0.66)]
        tt_ = C.tt("teleskop", 1, -0.3)
        tb = C.w("benua") - C.w("teleskop", 1, -0.3)
        pts = [(ex + er * x, ey + er * y) for x, y in pos]
        tj = C.tt("satu", 1, -0.3)
        if tj > 0:
            for j in range(len(pts)):
                for k in range(j + 1, len(pts)):
                    q = clamp((tj - (j + k) * 0.03) / 0.5)
                    if q > 0:
                        D.line_on(img, pts[j], (pts[j][0] + (pts[k][0] - pts[j][0]) * q, pts[j][1] + (pts[k][1] - pts[j][1]) * q),
                                  (255, 200, 120), 2, a2 * 0.45)
        for j, (x, y) in enumerate(pts):
            q = clamp((tt_ - j * tb / 8) / 0.3)
            if q > 0:
                glow(img, x, y, 40, ORANYE, 0.5 * a2 * q)
                parabola(img, x, y, 0.55 * eob(q, 2), a2, ang=-20 + 40 * x / 1920)
        ts = C.tt("seukuran", 1, -0.3)
        if ts > 0:
            q = esmooth(clamp(ts / 0.8))
            arc = [(ex + (er + 40) * math.cos(math.pi * (0.15 + 0.7 * i / 40)),
                    ey + (er + 40) * math.sin(math.pi * (0.15 + 0.7 * i / 40))) for i in range(41)]
            L.M._pline(img, arc[: max(2, int(41 * q))], EMAS, 8, a2)
            stiker(img, 960, 170, "SATU TELESKOP SEUKURAN BUMI", ts, ORANYE, 38, -2, tg, a2)
        chip(img, 960, 960, "EVENT HORIZON TELESCOPE (EHT)", a2 * C.u("event", 0.4, 1, -0.2), EMAS, 30)
    a3 = C.win(t_sas, t_has, 0.4, 0.4)
    if a3 > 0.01:
        bumi(img, 230, 560, 60, a3)
        teks(img, 230, 660, "BUMI", 28, TEKS, a3)
        gx, gy = 1620, 540
        glow(img, gx, gy, 260, (255, 210, 150), 0.55 * a3)
        glow(img, gx, gy, 120, (255, 240, 210), 0.7 * a3)
        panah(img, (gx, gy), (gx + 170, gy - 190), SIAN, 5, a3 * 0.8, 1.0, 16)
        D.dot_on(img, gx, gy, 10, (0, 0, 0), a3)
        teks(img, gx, gy + 180, "GALAKSI M87", 34, TEKS, a3 * C.u("m87", 0.4, 1, -0.2))
        tsk = C.tt("sekitar", 1, -0.3)
        if tsk > 0:
            q = esmooth(clamp(tsk / 1.2))
            x1 = 320 + (1480 - 320) * q
            for k in range(0, int((x1 - 320) / 24)):
                D.line_on(img, (320 + k * 24, 560), (332 + k * 24, 560), REDUP, 3, a3)
        angka(img, 910, 440, 55, C.tt("lima", 1, -0.3), 110, TEKS, 1.1, suf=" JUTA", sub="TAHUN CAHAYA", alpha=a3)
        te = C.tt("enam", 1, -0.3)
        if te > 0:
            q = eo(clamp(te / 0.4))
            kaca(img, gx - 280, 800, gx + 250, 930, a3 * q, ORANYE)
            angka(img, gx - 15, 845, 6.5, te, 44, EMAS, 0.9, des=1, suf=" MILIAR ×", alpha=a3 * q)
            teks(img, gx - 15, 898, "massa Matahari", 26, TEKS, a3 * q, name=FS)
    a4 = C.win(t_has, t_tiga, 0.4, 0.45)
    if a4 > 0.01:
        th = C.tt("hasilnya", 1, -0.2)
        C.zoom = 1.0 + 0.05 * clamp(th / 6)
        foto(img, 960, 520, 520, a4, "m87", th, "Foto: EHT Collaboration (2019)")
        callout(img, (1115, 610), (1420, 300), "CINCIN JINGGA", C.tt("cincin", 1, -0.2), TEKS, ORANYE, 38, a4,
                sub="gas super panas")
        callout(img, (960, 500), (1420, 780), "BAYANGAN GELAP", C.tt("bayangan", 1, -0.2), TEKS, SIAN, 38, a4)
        tei = C.tt("einstein", 1, -0.6)
        if tei > 0:
            q = eo(clamp(tei / 0.4))
            kaca(img, 120, 440, 620, 600, a4 * q, HIJAU)
            centang(img, 200, 520, 42, tei, HIJAU, a4)
            teks(img, 265, 495, "SESUAI RAMALAN", 30, TEKS, a4 * q, anchor="l")
            teks(img, 265, 545, "TEORI EINSTEIN", 30, HIJAU, a4 * q, anchor="l")
    a5 = C.win(t_tiga, C.dur + 1, 0.45, 0.3)
    if a5 > 0.01:
        tt3 = C.tt("tiga", 1, -0.3)
        u = esmooth(clamp(tt3 / 0.8))
        foto(img, 960 - 420 * u, 470, 520 - 140 * u, a5, "m87", 1.0)
        teks(img, 540, 745, "M87*", 44, ORANYE, a5 * u)
        teks(img, 540, 795, "55 juta tahun cahaya", 28, TEKS, a5 * u, name=FS)
        teks(img, 540, 835, "6,5 miliar × Matahari", 28, TEKS, a5 * u, name=FS)
        chip(img, 960, 190, "2022", a5 * C.u("tiga", 0.4, 1, 0), UNGU, 34)
        tsg = C.tt("sagitarius", 1, -0.3)
        foto(img, 1380, 470, 380, a5, "sgra", tsg, "Ilustrasi berdasarkan citra EHT (2022)")
        if tsg > 0:
            teks(img, 1380, 745, "SAGITARIUS A*", 44, UNGU, a5 * clamp(tsg / 0.4))
            teks(img, 1380, 795, "pusat galaksi kita", 26, REDUP, a5 * clamp(tsg / 0.4), name=FS)
        angka(img, 1380, 855, 27000, C.tt("dua", 2, -0.3), 40, TEKS, 1.0, suf=" tahun cahaya", alpha=a5, name=FB)
        angka(img, 1380, 910, 4, C.tt("empat", 1, -0.3), 40, EMAS, 0.6, suf=" juta × Matahari", alpha=a5, name=FB)


# ============================================================ BAB 5 - WAKTU MELAMBAT
def v01_waktu(img, C):
    tl, tg = C.tl, C.tg
    t_mnr = C.w("menurut", 1, -0.3)
    t_ini = C.w("ini", 1, -0.3)
    t_di2 = C.w("di", 2, -0.3)
    t_bg = C.w("bagimu", 1, -0.3)
    a0 = C.win(-1, t_mnr, 0.01, 0.4)
    if a0 > 0.01:
        lubang_hitam(img, 700, 560, 130, tg, a0, tilt=0.2)
        sx = 1 + 0.12 * math.sin(tg * 3.3)
        jam(img, 1300, 520, 130 * sx, tl * (1 + 0.6 * math.sin(tg * 2)), a0, glow_a=1.0)
        stiker(img, 1300, 760, "WAKTU JADI ANEH", C.tt("aneh", 1, -0.1), UNGU, 38, -3, tg, a0)
    a1 = C.win(t_mnr, t_ini, 0.4, 0.4)
    if a1 > 0.01:
        chip(img, 960, 170, "RELATIVITAS UMUM · EINSTEIN, 1915", a1 * C.u("relativitas", 0.4, 1, -0.2), UNGU, 28)
        lubang_hitam(img, 380, 600, 105, tg, a1, tilt=0.2)
        tm = C.tt("memperlambat", 1, -0.4)
        jam(img, 800, 600, 110, tl * 0.25, a1 * C.u("gravitasi", 0.4, 1, -0.2), acc=MERAH, glow_a=0.6)
        jam(img, 1500, 600, 110, tl, a1 * C.u("gravitasi", 0.4, 1, -0.2), acc=HIJAU, glow_a=0.6)
        if tm > 0:
            q = eo(clamp(tm / 0.4))
            teks(img, 800, 780, "DEKAT: LEBIH LAMBAT", 34, MERAH, a1 * q)
            teks(img, 1500, 780, "JAUH: NORMAL", 34, HIJAU, a1 * q)
    a2 = C.win(t_ini, t_di2, 0.4, 0.4)
    if a2 > 0.01:
        stempel(img, 960, 170, "BUKAN KHAYALAN", C.tt("khayalan", 1, -0.2), EMAS, 44, -3, a2)
        ex, ey = 960, 600
        bumi(img, ex, ey, 160, a2)
        rx, ry = 400, 120
        for k in range(48):
            if k % 2 == 0:
                a0_, a1_ = k * math.pi / 24, (k + 1) * math.pi / 24
                D.line_on(img, (ex + rx * math.cos(a0_), ey + ry * math.sin(a0_)),
                          (ex + rx * math.cos(a1_), ey + ry * math.sin(a1_)), (130, 140, 190), 2, a2 * 0.7)
        an = tg * 0.7
        sx_, sy_ = ex + rx * math.cos(an), ey + ry * math.sin(an)
        ts = C.tt("satelit", 1, -0.3)
        if ts > 0:
            satelit(img, sx_, sy_, 1.2, a2 * clamp(ts / 0.3))
            jam(img, sx_, sy_ - 70, 30, tl, a2 * clamp(ts / 0.3))
            chip(img, 1560, 330, "SATELIT GPS", a2 * clamp(ts / 0.3), SIAN, 30)
        tk = C.tt("mengoreksi", 1, -0.3)
        stiker(img, 960, 880, "JAMNYA DIKOREKSI SETIAP HARI", tk, SIAN, 36, -2, tg, a2, fg=SP0)
        if tk > 0.4:
            teks(img, 960, 965, "± 38 mikrodetik per hari", 26, REDUP, a2 * clamp((tk - 0.4) / 0.4), name=FS)
    a3 = C.win(t_di2, t_bg, 0.4, 0.4)
    if a3 > 0.01:
        C.zoom = 1.0 + 0.1 * clamp((tl - t_di2) / 3)
        lubang_hitam(img, 960, 480, 175, tg, a3, tilt=0.2)
        stempel(img, 960, 880, "JAUH LEBIH EKSTREM", C.tt("ekstrem", 1, -0.2), MERAH, 54, -3, a3)
    a4 = C.win(t_bg, C.dur + 1, 0.4, 0.3)
    if a4 > 0.01:
        kaca(img, 90, 150, 930, 930, a4, SIAN)
        teks(img, 510, 215, "KAMU", 44, SIAN, a4)
        teks(img, 510, 262, "yang sedang jatuh", 26, REDUP, a4, name=FS)
        astronot(img, 290, 600, 230, a4, rot=12 * math.sin(tg * 0.9))
        tj = C.tt("jam", 1, -0.3)
        jam(img, 650, 560, 150, tl, a4 * clamp(tj / 0.4), acc=SIAN, glow_a=0.7)
        if C.tt("normal", 1, -0.2) > 0:
            q = eo(clamp(C.tt("normal", 1, -0.2) / 0.4))
            teks(img, 650, 780, "BERDETAK NORMAL", 36, HIJAU, a4 * q)
        tt_ = C.tt("temantemanmu", 1, -0.3)
        if tt_ > 0:
            q = eo(clamp(tt_ / 0.4))
            kaca(img, 990, 150, 1830, 930, a4 * q, UNGU)
            teks(img, 1410, 215, "TEMANMU", 44, UNGU, a4 * q)
            teks(img, 1410, 262, "menonton dari jauh", 26, REDUP, a4 * q, name=FS)
            bx, by = 1560, 640
            lubang_hitam(img, bx, by, 80, tg, a4 * q, tilt=0.22)
            s = max(0.0, tl - C.w("lambat", 1, -1.5))
            p = 1 - math.exp(-s / 2.4)
            ax = 1150 + (bx - 150 - 1150) * p if tl > C.w("lambat", 1, -1.5) else 1150
            ay = 420 + (by - 110 - 420) * p if tl > C.w("lambat", 1, -1.5) else 420
            ax += 30 * (1 - p) * math.sin(tg * 0.8)
            merah = C.u("merah", 1.6, 1, -0.2)
            redup = 1 - 0.7 * C.u("redup", 2.0, 1, -0.2)
            hilang = 1 - C.u("menghilang", 2.4, 1, 0.0)
            aa = a4 * q * redup * hilang
            astronot(img, ax, ay, 150 * (1 - 0.25 * p), aa, rot=20 * (1 - p) * math.sin(tg * 0.9), merah=merah)
            t_l = C.w("lambat", 1, -1.5) - C.w("temantemanmu", 1, -0.3)
            jam(img, ax + 110, ay - 90, 44, min(tt_, t_l) + 2.4 * (1 - math.exp(-s / 2.4)), aa, acc=UNGU)
            for j, (kk, lab, col) in enumerate([("lambat", "MAKIN LAMBAT", EMAS), ("merah", "MAKIN MERAH", MERAH),
                                                ("redup", "MAKIN REDUP", REDUP)]):
                tq = C.tt(kk, 1, -0.2)
                if tq > 0:
                    chip(img, 1030 + j * 262, 870, lab, a4 * q * clamp(tq / 0.3), col, 20, anchor="l")
            stiker(img, 1300, 330, "MEMBEKU!", C.tt("membeku", 1, -0.1), SIAN, 40, -4, tg, a4 * q * hilang ** 0.3, fg=SP0)
            stempel(img, 1410, 560, "TAK PERNAH TERLIHAT MASUK", C.tt("pernah", 1, -0.2), UNGU, 38, -4, a4 * q)


# ============================================================ BAB 6 - HORIZON PERISTIWA
def v01_horizon(img, C):
    tl, tg = C.tl, C.tg
    cx, cy, R = 960, 560, 190
    t_uk = C.w("ukurannya", 1, -0.3)
    t_h2 = C.w("horizon", 2, -0.3)
    t_di = C.w("di", 1, -0.3)
    t_tp = C.w("tapi", 1, -0.3)
    aD = C.win(-1, t_uk, 0.01, 0.45)
    if aD > 0.01:
        th = C.tt("horizon", 1, -0.3)
        flick = 1.0
        ttak = C.tt("tak", 1, -0.2)
        if ttak > 0:
            flick = 1 - 0.6 * esmooth(clamp(ttak / 0.8)) + 0.12 * math.sin(tg * 9)
        lubang_polos(img, cx, cy, R, aD, SIAN, clamp(th / 0.6) * flick, dash=True)
        glow(img, cx, cy, R * 1.3, SIAN, 0.12 * aD * clamp(th / 0.6) * flick)
        a_c = aD * C.win(-1, t_h2, 0.01, 0.4)
        callout(img, (cx + R * 0.71, cy - R * 0.71), (1380, 230), "HORIZON PERISTIWA", th, TEKS, SIAN, 40, a_c)
        stiker(img, 1560, 340, "TITIK TANPA JALAN KEMBALI", C.tt("titik", 1, -0.1), MERAH, 32, 3, tg, a_c)
        a_b = aD * C.win(t_h2, t_di, 0.4, 0.4)
        if a_b > 0.01:
            for j, (kk, lab) in enumerate([("permukaan", "BUKAN PERMUKAAN PADAT"), ("dinding", "TIDAK ADA DINDING"),
                                            ("benturan", "TIDAK ADA BENTURAN")]):
                tq = C.tt(kk, 1, -0.3)
                if tq > 0:
                    q = eo(clamp(tq / 0.4))
                    y = 360 + j * 150
                    kaca(img, 1190, y - 55, 1810, y + 55, a_b * q, MERAH)
                    centang(img, 1250, y, 32, tq, MERAH, a_b, silang=True)
                    teks(img, 1300, y, lab, 32, TEKS, a_b * q, anchor="l")
            if ttak > 0:
                teks(img, cx, cy + R + 70, "BATAS YANG TAK TERLIHAT", 40, SIAN, a_b * clamp(ttak / 0.4))
        a_o = aD * C.win(t_di, t_tp, 0.4, 0.4)
        if a_o > 0.01:
            tk = C.tt("kabur", 1, -0.3)
            u = eio(clamp(tk / 2.0)) if tk > 0 else 0.0
            px, py = cx + 330 + 700 * u, cy - 150 - 360 * u
            roket(img, px, py, 120, 65, a_o * (1 - clamp((u - 0.8) / 0.2)), api=1.0, tg=tg)
            if tk > 0:
                panah(img, (cx + R + 30, cy - 90), (cx + R + 360, cy - 300), HIJAU, 8, a_o, clamp(tk / 0.6), 26)
            kaca_teks(img, 1470, 860, "DI LUAR: MASIH BISA KABUR", "dengan roket yang cukup kuat", a_o, HIJAU, 700, 130, 0, 36)
        a_i = aD * C.win(t_tp, t_uk, 0.4, 0.4)
        if a_i > 0.01:
            ts = C.tt("semua", 1, -0.3)
            qd = esmooth(clamp(ts / 1.4))
            tm = C.tt("mundur", 1, -0.3)
            drift = esmooth(clamp(tm / 3.5)) if tm > 0 else 0.0
            px, py = cx + 110 * (1 - 0.55 * drift), cy - 70 * (1 - 0.55 * drift)
            ang_r = 225 if tm <= 0 else 225 + 180 * esmooth(clamp(tm / 0.6))
            rng = random.Random(3)
            for j in range(8):
                own = rng.random() * 6.283
                tc = math.atan2(cy - py, cx - px)
                d_ = (tc - own + math.pi) % (2 * math.pi) - math.pi
                an = own + d_ * qd
                x0, y0 = px + 105 * math.cos(j * math.pi / 4), py + 105 * math.sin(j * math.pi / 4)
                panah(img, (x0, y0), (x0 + 80 * math.cos(an), y0 + 80 * math.sin(an)), MERAH, 7,
                      a_i * clamp(ts / 0.3), 1.0, 22)
            roket(img, px, py, 100, ang_r, a_i, api=0.8, tg=tg)
            tpu = C.tt("pusat", 1, -0.2)
            if tpu > 0:
                pul = 1 + 0.3 * math.sin(tg * 6)
                glow(img, cx, cy, 60 * pul, MERAH, 0.6 * a_i)
                D.dot_on(img, cx, cy, 10, MERAH, a_i)
                teks(img, cx, cy + 50, "PUSAT", 26, MERAH, a_i * clamp(tpu / 0.3))
            kaca_teks(img, 1470, 860, "DI DALAM: SEMUA ARAH KE PUSAT", "tidak ada jalan keluar", a_i, MERAH, 760, 130, 0, 36)
            stiker(img, 1540, 300, "MUNDUR = TETAP MASUK", tm, MERAH, 34, 3, tg, a_i)
    aS = C.win(t_uk, C.dur + 1, 0.45, 0.3)
    if aS > 0.01:
        chip(img, 960, 140, "UKURAN HORIZON BERGANTUNG PADA MASSA", aS * C.u("ukurannya", 0.4, 1, -0.2), SIAN, 28)
        tl1 = C.tt("sepuluh", 1, -0.4)
        if tl1 > 0:
            q = eo(clamp(tl1 / 0.4))
            kaca(img, 110, 210, 910, 930, aS * q, SIAN)
            teks(img, 510, 270, "10 × MATAHARI", 44, TEKS, aS * q)
            D.skyline(img, 330, 690, 800, (70, 80, 120), aS * q, seed=5, scale=1.0)
            lubang_polos(img, 510, 560, 180, aS * q, SIAN, 1.0, dash=True)
            garis_ukur(img, 330, 690, 860, "± 60 KM", C.tt("enam", 1, -0.3), EMAS, aS, 40)
            teks(img, 510, 350, "selebar kota", 28, REDUP, aS * q * C.u("kota", 0.4, 1, -0.2), name=FS)
        tsg = C.tt("sagitarius", 1, -0.3)
        if tsg > 0:
            q = eo(clamp(tsg / 0.4))
            kaca(img, 1010, 210, 1810, 930, aS * q, UNGU)
            teks(img, 1410, 270, "SAGITARIUS A*", 44, UNGU, aS * q)
            rr = 250 * eo(clamp(tsg / 0.9))
            lubang_polos(img, 1410, 590, rr, aS * q, UNGU, 1.0, dash=True)
            tm = C.tt("matahari", 2, -0.3)
            if tm > 0:
                bintang(img, 1410, 590, 15, (255, 210, 110), aS, tg, korona=0.7)
                callout(img, (1422, 580), (1640, 400), "MATAHARI", tm, TEKS, EMAS, 30, aS)
            teks(img, 1410, 880, "lebar: JUTAAN KM", 34, TEKS, aS * C.u("jutaan", 0.4, 1, -0.2))


# ============================================================ BAB 7 - SPAGETIFIKASI
def v01_spageti(img, C):
    tl, tg = C.tl, C.tg
    t_gr = C.w("gravitasi", 1, -0.3)
    t_p2 = C.w("pada", 2, -0.3)
    a0 = C.win(-1, t_gr, 0.01, 0.4)
    if a0 > 0.01:
        astronot(img, 960, 400, 220, a0, rot=14 * math.sin(tg * 0.8))
        stiker(img, 1220, 250, "SELAMAT?", C.tt("selamat", 1, -0.1), UNGU, 40, 5, tg, a0)
        tu = C.tt("ukuran", 1, -0.3)
        if tu > 0:
            q = eo(clamp(tu / 0.4))
            lubang_hitam(img, 620, 780, 45, tg, a0 * q, tilt=0.22)
            lubang_hitam(img, 1300, 760, 110, tg, a0 * q, tilt=0.22)
            teks(img, 620, 900, "KECIL", 34, TEKS, a0 * q)
            teks(img, 1300, 930, "RAKSASA", 34, TEKS, a0 * q)
    a1 = C.win(t_gr, t_p2, 0.4, 0.4)
    if a1 > 0.01:
        lubang_hitam(img, 960, 1060, 140, tg, a1, tilt=0.2)
        grow = C.u("luar", 1.2, 1, -0.2)
        reg = 1 + 1.5 * C.u("memanjang", 1.6, 1, -0.3)
        tip = 1 / math.sqrt(reg) * (1 - 0.3 * C.u("menipis", 1.0, 1, -0.2))
        hh = 210 * reg
        ay = 450 + 12 * math.sin(tg * 1.2)
        astronot(img, 960, ay, 210, a1, regang=reg, tipis=tip)
        head_y, foot_y = ay - hh / 2 + 30, ay + hh / 2 - 20
        tk = C.tt("kakimu", 1, -0.2)
        th = C.tt("kepalamu", 1, -0.2)
        if tk > 0:
            Lk = 110 + 150 * grow
            panah(img, (1120, foot_y - 40), (1120, foot_y - 40 + Lk), MERAH, 10, a1, clamp(tk / 0.5), 30)
            teks(img, 1160, foot_y - 20, "KAKI: TARIKAN LEBIH KUAT", 32, MERAH, a1 * clamp(tk / 0.4), anchor="l")
        if th > 0:
            Lh = 60 + 30 * grow
            panah(img, (1120, head_y), (1120, head_y + Lh), EMAS, 8, a1, clamp(th / 0.5), 24)
            teks(img, 1160, head_y + 10, "KEPALA: LEBIH LEMAH", 32, EMAS, a1 * clamp(th / 0.4), anchor="l")
        tb = C.tt("bumi", 1, -0.3)
        ab = a1 * C.win(C.w("bumi", 1, -0.3), C.w("tubuhmu", 1, -0.3), 0.4, 0.4)
        if ab > 0.01:
            kaca(img, 110, 300, 640, 620, ab, SIAN)
            bumi(img, 220, 460, 60, ab)
            teks(img, 310, 420, "DI BUMI", 38, SIAN, ab, anchor="l")
            teks(img, 310, 470, "selisihnya", 26, TEKS, ab, name=FS, anchor="l")
            teks(img, 310, 505, "kecil sekali", 26, TEKS, ab, name=FS, anchor="l")
        tm = C.tt("menipis", 1, -0.2)
        if tm > 0:
            for sgn in (-1, 1):
                for yy in (ay - 60, ay + 60):
                    panah(img, (960 + sgn * 170, yy), (960 + sgn * 90, yy), SIAN, 6, a1 * clamp(tm / 0.3), 1.0, 18)
        stiker(img, 450, 760, "SEPERTI MI DITARIK!", C.tt("mi", 1, -0.1), ORANYE, 36, -4, tg, a1)
        judul(img, 960, 120, "SPAGETIFIKASI", C.tt("spagetifikasi", 1, -0.3), 80, TEKS, hl=("SPAGETIFIKASI",),
              hlcol=ORANYE, alpha=a1)
    a2 = C.win(t_p2, C.dur + 1, 0.45, 0.3)
    if a2 > 0.01:
        kaca(img, 110, 190, 910, 930, a2, MERAH)
        teks(img, 510, 250, "LUBANG HITAM KECIL", 40, TEKS, a2)
        teks(img, 510, 296, "10 × Matahari", 26, REDUP, a2, name=FS)
        bx, by = 510, 620
        glow(img, bx, by, 230, MERAH, 0.3 * a2)
        D.ring_on(img, bx, by, 200, MERAH, 3, a2 * 0.7)
        teks(img, bx, by + 225, "ZONA TERCABIK", 24, MERAH, a2, name=FS)
        lubang_polos(img, bx, by, 34, a2, SIAN, 1.0, dash=True)
        ts = C.tt("sebelum", 1, -0.3)
        reg = 1 + 1.8 * esmooth(clamp(ts / 1.2)) if ts > 0 else 1.0
        astronot(img, bx, by - 150 + 20 * (reg - 1), 90, a2, regang=reg, merah=0.4 * (reg - 1))
        if ts > 0:
            teks(img, bx, 880, "TERCABIK SEBELUM HORIZON", 32, MERAH, a2 * clamp(ts / 0.4))
        tr = C.tt("raksasa", 1, -0.3)
        if tr > 0:
            q = eo(clamp(tr / 0.4))
            kaca(img, 1010, 190, 1810, 930, a2 * q, HIJAU)
            teks(img, 1410, 250, "LUBANG HITAM RAKSASA", 40, TEKS, a2 * q)
            teks(img, 1410, 296, "Sagitarius A*", 26, REDUP, a2 * q, name=FS)
            gx, gy = 1410, 690
            lubang_polos(img, gx, gy, 200, a2 * q, SIAN, 1.0, dash=True)
            glow(img, gx, gy, 90, MERAH, 0.35 * a2 * q)
            D.ring_on(img, gx, gy, 70, MERAH, 3, a2 * q * 0.7)
            tm = C.tt("melewati", 2, -0.5)
            u = esmooth(clamp(tm / 2.2)) if tm > 0 else 0.0
            astronot(img, gx, 380 + 190 * u, 90, a2 * q, rot=10 * math.sin(tg))
            ta = C.tt("apaapa", 1, -0.2)
            if ta > 0:
                centang(img, gx + 110, 520, 34, ta, HIJAU, a2)
                teks(img, gx + 160, 520, "UTUH", 32, HIJAU, a2 * clamp(ta / 0.3), anchor="l")
            stiker(img, 1410, 870, "UNTUK SEMENTARA...", C.tt("sementara", 1, -0.1), UNGU, 36, -3, tg, a2)


# ============================================================ BAB 8 - DI DALAM & RADIASI HAWKING
def v01_dalam(img, C):
    tl, tg = C.tl, C.tg
    t_te = C.w("teori", 1, -0.3)
    t_st = C.w("stephen", 1, -0.4)
    t_sg = C.w("sangat", 1, -0.3)
    a0 = C.win(-1, t_te, 0.01, 0.45)
    if a0 > 0.01:
        C.zoom = 1.0 + 0.1 * clamp(tl / t_te)
        lubang_hitam(img, 960, 500, 200, tg, a0, tilt=0.2)
        tq = C.tt("dalamnya", 1, -0.3)
        if tq > 0:
            pul = 1 + 0.06 * math.sin(tg * 4)
            teks(img, 960, 500, "?", 200, UNGU, a0 * clamp(tq / 0.4), scale=pul * eob(clamp(tq / 0.4), 2))
        stiker(img, 960, 880, "TIDAK ADA YANG TAHU PASTI", C.tt("jujur", 1, -0.1), UNGU, 38, -2, tg, a0)
        tc = C.tt("cahaya", 1, -0.2)
        if tc > 0:
            for j, an in enumerate((-2.2, -1.2, -0.3)):
                p0 = (960, 500)
                p2 = (960 + 150 * math.cos(an + 0.9), 500 + 150 * math.sin(an + 0.9))
                p1 = (960 + 320 * math.cos(an), 500 + 320 * math.sin(an))
                sinar(img, bez_pts(p0, p1, p2, 30), clamp((tc - j * 0.15) / 1.2), EMAS, 4, a0 * 0.9)
        tm = C.tt("mengamatinya", 1, -0.4)
        if tm > 0:
            parabola(img, 230, 780, 1.6, a0 * clamp(tm / 0.3), ang=30)
            silang_besar(img, 230, 760, 60, tm - 0.2, a0)
    a1 = C.win(t_te, t_st, 0.45, 0.45)
    if a1 > 0.01:
        cx, cy, R = 960, 540, 300
        lubang_polos(img, cx, cy, R, a1, SIAN, 1.0, dash=True)
        ttr = C.tt("terjepit", 1, -0.5)
        if ttr > -0.5:
            for j in range(46):
                ph = (j * 0.618) % 1.0
                u = (ph + (tl - t_te) * 0.3) % 1.0
                rr = R * 0.95 * (1 - u)
                an = j * 2.39 + u * 3.0
                D.dot_on(img, cx + rr * math.cos(an), cy + rr * math.sin(an), 3 + 2 * (1 - u), (200, 190, 255), a1 * 0.8)
        tsi = C.tt("singularitas", 1, -0.3)
        if tsi > 0:
            pul = 1 + 0.25 * math.sin(tg * 7)
            glow(img, cx, cy, 90 * pul, WHITE, 0.8 * a1)
            D.dot_on(img, cx, cy, 8, WHITE, a1)
            a_cal = a1 * C.win(C.w("singularitas", 1, -0.3), C.w("tapi", 1, -0.3), 0.3, 0.4)
            callout(img, (cx + 8, cy - 8), (1220, 250), "SINGULARITAS", tsi, TEKS, SIAN, 42, a_cal,
                    sub="semua materi terjepit di satu titik")
        tth = C.tt("terhingga", 1, -0.4)
        if tth > 0:
            teks(img, cx, 930, "KEPADATAN: TAK TERHINGGA  ∞", 40, EMAS, a1 * clamp(tth / 0.4))
        th = C.tt("hukum", 1, -0.3)
        if th > 0:
            tb = C.tt("berlaku", 1, -0.2)
            for j, (fx, fy, rumus) in enumerate([(360, 300, "E = mc²"), (1560, 640, "F = m × a"), (380, 760, "g = GM/r²")]):
                q = eo(clamp((th - j * 0.2) / 0.4))
                jit = (8 * math.sin(tg * 40 + j) if tb > 0 else 0)
                kaca(img, fx - 170 + jit, fy - 50, fx + 170 + jit, fy + 50, a1 * q, UNGU)
                teks(img, fx + jit, fy, rumus, 40, TEKS, a1 * q * (1 - 0.5 * clamp(tb / 0.5)))
                if tb > 0:
                    coret(img, fx - 150, fx + 150, fy, tb - j * 0.1, a1)
            stiker(img, 1500, 300, "BUTUH TEORI BARU", C.tt("baru", 1, -0.1), UNGU, 38, 4, tg, a1)
    a2 = C.win(t_st, t_sg, 0.45, 0.45)
    if a2 > 0.01:
        chip(img, 960, 150, "STEPHEN HAWKING · 1974", a2 * C.u("stephen", 0.4, 1, -0.3), SIAN, 30)
        tsu = C.tt("menyusut", 1, -0.3)
        r = 170 * (1 - 0.2 * esmooth(clamp(tsu / 3.0))) if tsu > 0 else 170
        cx, cy = 960, 560
        lubang_polos(img, cx, cy, r, a2, SIAN, 0.8)
        te = C.tt("memancarkan", 1, -0.3)
        if te > 0:
            for j in range(60):
                ph = (j * 0.618) % 1.0
                u = (ph + te * 0.35) % 1.0
                an = j * 2.39996
                rr = r + 10 + 420 * u
                D.dot_on(img, cx + rr * math.cos(an), cy + rr * math.sin(an), 4, (160, 230, 255),
                         a2 * clamp(te / 0.5) * (1 - u))
            callout(img, (cx + r * 0.9, cy - r * 0.45), (1450, 330), "RADIASI HAWKING", te - 0.3, TEKS, SIAN, 38, a2,
                    sub="energi bocor perlahan")
        if tsu > 0:
            teks(img, cx, cy + r + 60, "PERLAHAN MENYUSUT", 36, EMAS, a2 * clamp(tsu / 0.4))
    a3 = C.win(t_sg, C.dur + 1, 0.45, 0.3)
    if a3 > 0.01:
        stempel(img, 960, 190, "SANGAT, SANGAT LAMBAT", C.tt("sangat", 1, -0.2), EMAS, 52, -3, a3)
        tu = C.tt("umur", 1, -0.4)
        tsb = C.tt("seberat", 1, -0.3)
        if tsb > 0 or tu > 0:
            kaca(img, 150, 360, 1770, 900, a3 * max(clamp(tsb / 0.4), clamp(tu / 0.4)))
        if tsb > 0:
            q = eo(clamp(tsb / 0.4))
            teks(img, 210, 480, "LUBANG HITAM SEBERAT MATAHARI MENGUAP", 32, TEKS, a3 * q, anchor="l")
            g = esmooth(clamp((tsb - 0.3) / 3.5))
            wbar = 1500 * g + 30 * math.sin(tg * 5) * g
            D.rrect_on(img, 210, 520, 210 + max(10, wbar), 560, 14, UNGU, a3 * q)
            if g > 0.9:
                panah(img, (1650, 540), (1740, 540), UNGU, 8, a3, 1.0, 26)
            x = 210
            teks(img, x, 610, "±", 40, UNGU, a3 * clamp((tsb - 0.5) / 0.4), anchor="l")
            sekop_teks_sup(img, x + 40, 610, "10", "67", 44, UNGU, a3 * clamp((tsb - 0.5) / 0.4))
            teks(img, x + 170, 612, "tahun", 34, TEKS, a3 * clamp((tsb - 0.5) / 0.4), name=FS, anchor="l")
        if tu > 0:
            q = eo(clamp(tu / 0.4))
            teks(img, 210, 710, "UMUR ALAM SEMESTA", 32, TEKS, a3 * q, anchor="l")
            D.rrect_on(img, 210, 750, 222, 790, 5, EMAS, a3 * q)
            teks(img, 245, 770, "13,8 miliar tahun  (hampir tak terlihat!)", 30, EMAS, a3 * q, name=FS, anchor="l")


# ============================================================ BAB 9 - BUMI AMAN + RANGKUMAN + CTA
def v01_aman(img, C):
    tl, tg = C.tl, C.tg
    t_lh = C.w("lubang", 1, -0.3)
    t_mt = C.w("matahari", 1, -0.3)
    t_mari = C.w("mari", 1, -0.3)
    t_kl = C.w("kalau", 1, -0.3)
    a0 = C.win(-1, t_lh, 0.01, 0.4)
    if a0 > 0.01:
        bumi(img, 960, 540, 200, a0)
        tn = C.tt("tenang", 1, -0.2)
        col = MERAH if tn <= 0 else mix(MERAH, HIJAU, clamp(tn / 0.4))
        pul = 0.5 + 0.5 * math.sin(tg * 5)
        D.ring_on(img, 960, 540, 240 + 12 * pul, col, 6, a0 * (0.6 + 0.4 * pul))
        stiker(img, 1260, 280, "TERANCAM?", C.tt("terancam", 1, -0.2), MERAH, 40, 5, tg, a0 * (1 - clamp(tn / 0.3)))
        if tn > 0:
            centang(img, 1220, 330, 54, tn, HIJAU, a0)
            teks(img, 960, 860, "TENANG SAJA", 50, HIJAU, a0 * clamp(tn / 0.4))
    a1 = C.win(t_lh, t_mt, 0.4, 0.4)
    if a1 > 0.01:
        bumi(img, 250, 560, 70, a1)
        teks(img, 250, 670, "BUMI", 28, TEKS, a1)
        gx, gy = 1640, 540
        lubang_hitam(img, gx, gy, 38, tg, a1, tilt=0.24)
        for k in range(40):
            if k % 2 == 0:
                a0_, a1_ = k * math.pi / 20, (k + 1) * math.pi / 20
                D.line_on(img, (gx + 130 * math.cos(a0_), gy + 44 * math.sin(a0_)),
                          (gx + 130 * math.cos(a1_), gy + 44 * math.sin(a1_)), (150, 150, 190), 2, a1 * 0.7)
        an = tg * 1.1
        bintang(img, gx + 130 * math.cos(an), gy + 44 * math.sin(an), 20, (255, 214, 120), a1, tg, korona=0.6)
        chip(img, gx, 330, "TERDEKAT YANG DIKETAHUI", a1 * C.u("terdekat", 0.4, 1, -0.2), HIJAU, 24)
        tga = C.tt("gaia", 1, -0.3)
        if tga > 0:
            q = eo(clamp(tga / 0.4))
            kaca_teks(img, gx, 780, "GAIA BH1", "± 10 × massa Matahari", a1 * q, UNGU, 440, 140, 0, 42)
        ts = C.tt("seribu", 1, -0.4)
        if ts > 0:
            q = esmooth(clamp(ts / 1.2))
            x1 = 340 + (1480 - 340) * q
            for k in range(0, int((x1 - 340) / 24)):
                D.line_on(img, (340 + k * 24, 560), (352 + k * 24, 560), REDUP, 3, a1)
        angka(img, 920, 450, 1560, ts, 110, TEKS, 1.3, sub="TAHUN CAHAYA", alpha=a1)
    a2 = C.win(t_mt, t_mari, 0.4, 0.4)
    if a2 > 0.01:
        tk = C.tt("katai", 1, -0.3)
        k = esmooth(clamp(tk / 1.2)) if tk > 0 else 0.0
        r = 190 * (1 - k) + 16 * k
        col = mix((255, 200, 100), (215, 228, 255), k)
        bintang(img, 640, 540, r, col, a2, tg, korona=1.0 - 0.3 * k)
        teks(img, 640, 540 + 190 + 60, "MATAHARI", 34, TEKS, a2 * (1 - k))
        tr = C.tt("ringan", 1, -0.3)
        if tr > 0:
            q = eo(clamp(tr / 0.4))
            kaca(img, 1080, 360, 1800, 560, a2 * q, EMAS)
            teks(img, 1440, 420, "TERLALU RINGAN", 46, EMAS, a2 * q)
            teks(img, 1440, 490, "butuh > 20 × massa Matahari", 28, TEKS, a2 * q, name=FS)
        callout(img, (650, 530), (1100, 740), "KATAI PUTIH", tk - 0.6, TEKS, SIAN, 42, a2,
                sub="nasib Matahari miliaran tahun lagi")
    a3 = C.win(t_mari, t_kl, 0.4, 0.4)
    if a3 > 0.01:
        t_c1 = C.w("adalah", 1, -0.4)
        k_ = esmooth(clamp((tl - t_c1) / 0.6))
        tr_ = tl - t_mari
        teks(img, 960, 540 + (150 - 540) * k_, "RANGKUMAN", int(110 - 70 * k_), ORANYE,
             a3 * clamp(tr_ / 0.4) * (1 - k_) + 0.0, scale=eob(clamp(tr_ / 0.5), 2) if tr_ > 0 else 0)
        chip(img, 960, 150, "RANGKUMAN", a3 * k_, ORANYE, 30)
        kartu = [(("adalah", 1), "SANGAT PADAT", "cahaya pun tidak bisa lolos", ORANYE),
                 (("waktu", 1), "WAKTU MELAMBAT", "dari jauh kamu terlihat membeku", UNGU),
                 (("horizon", 1), "HORIZON PERISTIWA", "titik tanpa jalan kembali", SIAN),
                 (("kecil", 1), "YANG KECIL LEBIH BERBAHAYA", "yang raksasa justru lebih ramah", MERAH)]
        for j, ((kk, nn), t1, t2, col) in enumerate(kartu):
            q, dy = muncul(C, kk, nn, -0.4)
            if q <= 0.01:
                continue
            x0 = 140 + (j % 2) * 840
            y0 = 250 + (j // 2) * 330
            kaca(img, x0, y0 + dy, x0 + 800, y0 + 280 + dy, a3 * q, col)
            ix, iy = x0 + 130, y0 + 140 + dy
            if j == 0:
                lubang_hitam(img, ix, iy, 42, tg, a3 * q, tilt=0.24)
            elif j == 1:
                jam(img, ix, iy, 70, tl * 0.3, a3 * q, acc=UNGU)
            elif j == 2:
                lubang_polos(img, ix, iy, 70, a3 * q, SIAN, 1.0, dash=True)
            else:
                astronot(img, ix, iy, 90, a3 * q, regang=2.2, merah=0.3)
            teks(img, x0 + 250, y0 + 110 + dy, t1, 38 if j < 3 else 32, col, a3 * q, anchor="l")
            teks(img, x0 + 250, y0 + 170 + dy, t2, 27, TEKS, a3 * q, name=FS, anchor="l")
            D.dot_on(img, x0 + 760, y0 + 40 + dy, 18, col, a3 * q)
            teks(img, x0 + 760, y0 + 41 + dy, str(j + 1), 22, SP0, a3 * q)
    a4 = C.win(t_kl, C.dur + 1, 0.4, 0.3)
    if a4 > 0.01:
        lubang_hitam(img, 960, 540, 170, tg, a4 * 0.3, tilt=0.2)
        tk = C.tt("kliktahu", 1, -0.5)
        teks(img, 960, 250, "KlikTahu", 90, TEKS, a4 * clamp(tk / 0.4), scale=eob(clamp(tk / 0.5), 2) if tk > 0 else 0)
        if tk > 0:
            q = eo(clamp(tk / 0.4))
            klik = tk - 1.1
            sub = klik > 0
            col = (90, 94, 110) if sub else (230, 40, 40)
            sc_ = 1.0 - 0.08 * math.sin(math.pi * clamp(klik / 0.25)) if klik > 0 else 1.0
            D.rrect_on(img, 960 - 250 * sc_, 440 - 55 * sc_, 960 + 250 * sc_, 440 + 55 * sc_, 55, col, a4 * q)
            teks(img, 960, 440, "SUBSCRIBED" if sub else "SUBSCRIBE", 44, WHITE, a4 * q)
            # kursor
            u = esmooth(clamp((tk - 0.3) / 0.8))
            kx, ky = 1300 - 220 * u, 640 - 180 * u
            D.poly_on(img, [(kx, ky), (kx, ky + 50), (kx + 13, ky + 38), (kx + 24, ky + 60), (kx + 32, ky + 56),
                            (kx + 21, ky + 34), (kx + 38, ky + 34)], WHITE, a4 * q * (1 - clamp((tk - 2.2) / 0.4)),
                      outline=SP0)
            if sub:
                partikel(img, 960, 440, klik, EMAS, a4, n=16, jarak=260)
                bx, by = 1260, 440
                rot = 18 * math.sin(tg * 14) * math.exp(-klik * 1.5)
                pts = D.rot_pts([(bx - 28, by + 22), (bx - 22, by - 12), (bx, by - 32), (bx + 22, by - 12), (bx + 28, by + 22)],
                                bx, by - 30, rot)
                D.poly_on(img, pts, EMAS, a4 * clamp(klik / 0.3))
                D.dot_on(img, bx + 0, by + 30, 8, EMAS, a4 * clamp(klik / 0.3))
        tko = C.tt("komentar", 1, -0.5)
        if tko > 0:
            q, dy = eo(clamp(tko / 0.4)), (1 - eo(clamp(tko / 0.4))) * 30
            kaca(img, 460, 620 + dy, 1460, 880 + dy, a4 * q, ORANYE)
            D.dot_on(img, 550, 700 + dy, 40, ORANYE, a4 * q)
            teks(img, 550, 700 + dy, "K", 36, SP0, a4 * q)
            teks(img, 620, 690 + dy, "Tulis di komentar:", 30, REDUP, a4 * q, name=FS, anchor="l")
            msg = "Topik apa yang ingin kamu jelajahi berikutnya?"
            n = int(len(msg) * clamp((tko - 0.3) / 2.2))
            teks(img, 620, 760 + dy, msg[:n] + ("|" if (tg * 2) % 1 < 0.5 else ""), 32, TEKS, a4 * q, anchor="l")


VIS = {"v01_intro": v01_intro, "v01_apa": v01_apa, "v01_lahir": v01_lahir, "v01_piringan": v01_piringan,
       "v01_foto": v01_foto, "v01_waktu": v01_waktu, "v01_horizon": v01_horizon, "v01_spageti": v01_spageti,
       "v01_dalam": v01_dalam, "v01_aman": v01_aman}

# (kata, kemunculan-ke, offset detik, jenis SFX, gain) - kata sama dengan pemicu visual
BEATS = {
    "v01_intro": [(0.3, 1, 0, "riser", 0.6), ("hitam", 1, 0, "pop", 0.8), ("pulang", 1, 0.2, "impact", 0.8),
                  ("lihat", 1, -0.35, "pop", 0.8), ("rasakan", 1, -0.35, "pop", 0.8), ("dilihat", 1, -0.35, "pop", 0.8),
                  ("aneh", 1, 0, "glitch", 0.9), ("tenang", 1, -0.2, "ding", 0.6), ("titik", 1, -0.2, "ding", 0.6),
                  ("dalam", 1, -0.2, "ding", 0.6), ("fisika", 1, -0.3, "swish", 0.7), ("pengamatan", 1, -0.3, "swish", 0.7),
                  ("siap", 1, -0.25, "impact", 0.9), ("kencangkan", 1, 0, "whoosh", 1.0)],
    "v01_apa": [("bukan", 1, -0.2, "swish", 0.7), ("lubang", 3, 0.1, "thud", 0.8), ("bukan", 2, -0.2, "swish", 0.7),
                ("penyedot", 1, 0.2, "thud", 0.8), ("gravitasi", 1, -0.1, "nging", 0.5), ("cahaya", 1, -0.2, "zap", 0.6),
                ("lolos", 1, -0.1, "pop", 0.8), ("melempar", 1, -0.2, "swish_up", 0.7), ("kencang", 1, -0.2, "swish_up", 0.7),
                ("tinggi", 1, -0.2, "swish_up", 0.8), ("roket", 1, -0.3, "riser", 0.7), ("sebelas", 1, -0.3, "tick", 0.8),
                ("kecepatan", 1, -0.1, "pop", 0.8), ("tiga", 1, -0.2, "tick", 0.8), ("melebihi", 1, -0.2, "zap", 0.8),
                ("keluar", 1, -0.1, "impact", 0.8), ("berat", 1, 0.1, "swish", 0.6), ("tapi", 1, -0.2, "pop", 0.7),
                ("dipadatkan", 1, -0.1, "riser", 0.8), ("kelereng", 1, -0.2, "pop", 0.9), ("lubang", 4, -0.1, "boom", 0.8)],
    "v01_lahir": [("gravitasi", 1, -0.2, "swish", 0.7), ("reaksi", 1, -0.2, "swish", 0.7), ("habis", 1, -0.2, "nging", 0.5),
                  ("berhenti", 1, -0.1, "thud", 0.7), ("dua", 1, -0.2, "pop", 0.7), ("runtuh", 1, -0.1, "riser", 0.8),
                  ("meledak", 1, -0.08, "boom", 1.0), ("supernova", 1, -0.3, "pop", 0.7), ("tiga", 1, -0.2, "pop", 0.7),
                  ("gaya", 1, -0.3, "nging", 0.5), ("lahirlah", 1, -0.1, "impact", 1.0), ("para", 1, -0.4, "whoosh", 0.6),
                  ("seratus", 1, -0.6, "tick", 0.8), ("sulit", 1, -0.5, "swish", 0.6)],
    "v01_piringan": [("total", 1, -0.2, "pop", 0.7), ("gas", 1, -0.3, "whoosh", 0.5), ("piringan", 1, -0.3, "kilau", 0.7),
                     ("jutaan", 1, -0.2, "pop", 0.8), ("bersinar", 1, -0.1, "kilau", 0.7), ("membelokkan", 1, -0.3, "zap", 0.7),
                     ("bergeser", 1, -0.2, "nging", 0.5), ("kaca", 1, -0.3, "pop", 0.7), ("atas", 1, -0.2, "swish", 0.7),
                     ("bawah", 1, -0.2, "swish", 0.7), ("bayangan", 1, -0.2, "thud", 0.7), ("matamu", 1, -0.6, "pop", 0.6)],
    "v01_foto": [("bukan", 1, -0.1, "impact", 0.8), ("dua", 1, -0.3, "tick", 0.8), ("memamerkan", 1, 0, "kilau", 0.8),
                 ("foto", 1, -0.2, "pop", 0.7), ("teleskop", 1, -0.3, "tick", 0.7), ("satu", 1, -0.3, "zap", 0.6),
                 ("seukuran", 1, -0.3, "pop", 0.8), ("event", 1, -0.2, "ding", 0.6), ("sasarannya", 1, -0.3, "whoosh", 0.6),
                 ("lima", 1, -0.3, "tick", 0.8), ("enam", 1, -0.3, "pop", 0.7), ("hasilnya", 1, -0.2, "kilau", 1.0),
                 ("cincin", 1, -0.2, "pop", 0.7), ("bayangan", 1, -0.2, "pop", 0.7), ("einstein", 1, -0.6, "ding", 0.8),
                 ("tiga", 1, -0.3, "whoosh", 0.6), ("sagitarius", 1, -0.3, "kilau", 0.9), ("dua", 2, -0.3, "tick", 0.7),
                 ("empat", 1, -0.3, "tick", 0.7)],
    "v01_waktu": [("aneh", 1, -0.1, "glitch", 0.8), ("relativitas", 1, -0.2, "pop", 0.7), ("memperlambat", 1, -0.4, "nging", 0.6),
                  ("khayalan", 1, -0.2, "impact", 0.8), ("satelit", 1, -0.3, "swish", 0.6), ("mengoreksi", 1, -0.3, "pop", 0.8),
                  ("ekstrem", 1, -0.2, "impact", 0.9), ("jam", 1, -0.3, "tick", 0.8), ("normal", 1, -0.2, "ding", 0.6),
                  ("temantemanmu", 1, -0.3, "swish", 0.7), ("lambat", 1, -0.2, "pop", 0.6), ("merah", 1, -0.2, "pop", 0.6),
                  ("redup", 1, -0.2, "pop", 0.6), ("membeku", 1, -0.1, "retak", 0.8), ("pernah", 1, -0.2, "impact", 0.8)],
    "v01_horizon": [("horizon", 1, -0.3, "nging", 0.6), ("titik", 1, -0.1, "impact", 0.8), ("permukaan", 1, -0.3, "pop", 0.7),
                    ("dinding", 1, -0.3, "pop", 0.7), ("benturan", 1, -0.3, "pop", 0.7), ("tak", 1, -0.2, "glitch", 0.6),
                    ("kabur", 1, -0.3, "whoosh", 0.9), ("semua", 1, -0.3, "nging", 0.6), ("pusat", 1, -0.2, "thud", 0.8),
                    ("mundur", 1, -0.3, "pop", 0.7), ("massa", 1, -0.2, "swish", 0.6), ("sepuluh", 1, -0.4, "pop", 0.7),
                    ("enam", 1, -0.3, "tick", 0.8), ("sagitarius", 1, -0.3, "boom", 0.6), ("matahari", 2, -0.3, "pop", 0.7)],
    "v01_spageti": [("selamat", 1, -0.1, "pop", 0.7), ("ukuran", 1, -0.3, "swish", 0.6), ("kakimu", 1, -0.2, "thud", 0.7),
                    ("kepalamu", 1, -0.2, "pop", 0.6), ("bumi", 1, -0.3, "pop", 0.6), ("luar", 1, -0.2, "nging", 0.6),
                    ("memanjang", 1, -0.3, "riser", 0.8), ("menipis", 1, -0.2, "swish", 0.6), ("mi", 1, -0.1, "pop", 0.9),
                    ("spagetifikasi", 1, -0.3, "impact", 0.9), ("pada", 2, -0.3, "whoosh", 0.6), ("sebelum", 1, -0.3, "retak", 0.8),
                    ("raksasa", 1, -0.3, "swish", 0.6), ("apaapa", 1, -0.2, "ding", 0.8), ("sementara", 1, -0.1, "nging", 0.6)],
    "v01_dalam": [("dalamnya", 1, -0.3, "pop", 0.7), ("jujur", 1, -0.1, "pop", 0.7), ("cahaya", 1, -0.2, "zap", 0.6),
                  ("mengamatinya", 1, -0.2, "thud", 0.7), ("teori", 1, -0.3, "whoosh", 0.6), ("singularitas", 1, -0.3, "impact", 0.9),
                  ("terhingga", 1, -0.4, "nging", 0.6), ("hukum", 1, -0.3, "pop", 0.6), ("berlaku", 1, -0.2, "glitch", 0.9),
                  ("baru", 1, -0.1, "pop", 0.8), ("stephen", 1, -0.3, "swish", 0.6), ("memancarkan", 1, -0.3, "kilau", 0.8),
                  ("menyusut", 1, -0.3, "nging", 0.5), ("sangat", 1, -0.2, "impact", 0.8), ("seberat", 1, -0.3, "riser", 0.7),
                  ("umur", 1, -0.4, "pop", 0.7)],
    "v01_aman": [("terancam", 1, -0.2, "pop", 0.8), ("tenang", 1, -0.2, "ding", 0.8), ("terdekat", 1, -0.2, "pop", 0.6),
                 ("gaia", 1, -0.3, "pop", 0.7), ("seribu", 1, -0.4, "tick", 0.8), ("ringan", 1, -0.3, "pop", 0.7),
                 ("katai", 1, -0.3, "nging", 0.6), ("mari", 1, -0.3, "whoosh", 0.6), ("adalah", 1, -0.4, "pop", 0.8),
                 ("waktu", 1, -0.4, "pop", 0.8), ("horizon", 1, -0.4, "pop", 0.8), ("kecil", 1, -0.4, "pop", 0.8),
                 ("kliktahu", 1, 0.6, "click", 1.0), ("kliktahu", 1, 0.62, "ding", 0.8), ("komentar", 1, -0.5, "pop", 0.8)],
}
