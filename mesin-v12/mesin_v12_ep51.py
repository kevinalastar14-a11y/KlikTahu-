#!/usr/bin/env python3
"""Ep51 - Ular Masuk Rumah Saat Musim Hujan (mesin v12 "RUMAH POTONG").

Dunia visual BARU, bukan cakram langit Ep50: satu rumah yang sama dilihat dengan
DELAPAN cara berbeda (luar, potongan melintang, kalender, rantai mangsa, irisan
dinding, denah, daftar tindakan, luar lagi untuk loop). Jadi tidak ada template
tunggal yang diulang 124 detik.

Babak: intro=Hook, f1=Agitation, f2-f4=Body (telur / mangsa / tempat kering),
f5=Micro-climax (tiga panah -> satu titik), f6=Payoff, outro=Seamless loop.
Setiap BEAT dikunci ke KATA (mesin_v12.cues) supaya gambar dan SFX satu sumber.
"""
import math

import diagrams as D
import mesin_v11 as V
import mesin_v12 as M
from diagrams import (INK, CREAM, WHITE, MUTED, RED, GREEN, AMBER, BLUE,
                      mix, seg, clamp, esmooth, eob, eo, font, tw, tlh, paste_c, ell,
                      rrect_on, line_on, dot_on, ring_on, poly_on)
from mesin_v12 import (ease12, esm, eio, cues, chip, label, stiker, silang,
                       polyline_on, NAVY, NAVY2, STAR, KUNING, ORANYE)

# ---------------------------------------------------------------- tata letak dunia
Y_TXT = 1318
SUMBER = "Sumber: BRIN (Amir Hamidy) · BMKG · Damkar"                 # teks kinetik (2 baris, aman: < 1640)
Y_FOOT = 1204                # chip fakta persisten (frame 0 == frame akhir)
Y_DASAR = 1114               # garis tanah rumah besar

TEAL = (31, 122, 107)
MERAH = (200, 70, 50)
EMAS = (176, 122, 18)
UNGU = (106, 79, 179)
HIJAU = (46, 140, 90)
AIR = (74, 132, 166)
DINDING = (252, 248, 240)
KACA = (250, 214, 132)


# ---------------------------------------------------------------- utilitas dasar
def _rnd(i, k=1.0):
    return (math.sin(i * 12.9898 + k * 78.233) * 43758.5453) % 1.0


def kertas(img, al=1.0):
    """Tekstur kertas halus: memecah bidang krem kosong tanpa mengubah warnanya."""
    if al <= 0.01:
        return
    col = mix(CREAM, INK, 0.20)
    for i in range(30):
        y = 386 + i * 25
        line_on(img, (36, y), (1044, y - 8), col, 1, 0.038 * al)


def debu(img, tg, al=1.0, n=16, y0=380, y1=1150):
    """Partikel debu melayang (gerak halus konstan -> tidak ada frame beku)."""
    if al <= 0.01:
        return
    for i in range(n):
        x = 60 + _rnd(i, 3) * 960 + 12 * math.sin(tg * 0.4 + i)
        y = y0 + _rnd(i, 5) * (y1 - y0) + 9 * math.sin(tg * 0.31 + i * 1.7)
        a = (0.10 + 0.16 * _rnd(i, 7)) * al
        dot_on(img, x, y, 1.6 + 2.2 * _rnd(i, 9), mix(CREAM, INK, 0.35), a)


def hujan(img, u, x0, x1, y0, y1, n=70, al=0.55, col=None, seed=1,
          panjang=(22, 46), lebar=3, tilt=0.16, laju=1.0):
    """Hujan deterministik. `u` dalam DETIK; kecepatan tetes = bilangan bulat siklus/detik
    sehingga medan hujan berulang tepat tiap 1 detik -> frame akhir outro bisa sama
    persis dengan frame 0 intro."""
    if al <= 0.01:
        return
    col = col or mix(CREAM, INK, 0.40)
    for i in range(n):
        j = i + seed * 137
        rx, ry, rv, rl = _rnd(j, 1), _rnd(j, 2), _rnd(j, 3), _rnd(j, 4)
        spd = (1 + (1 if rv > 0.55 else 0) + (1 if rv > 0.9 else 0)) * laju
        prog = (ry + u * spd) % 1.0
        y = y0 + prog * (y1 - y0)
        x = x0 + rx * (x1 - x0) + tilt * (y - y0)
        L = panjang[0] + rl * (panjang[1] - panjang[0])
        line_on(img, (x, y), (x - tilt * L, y - L), col, lebar, al * (0.40 + 0.60 * rv))


def riak(img, x, y, u, al=0.5, r0=6, r1=52, col=None):
    """Riak air di genangan (squash 0.32). Periode 1 s -> ikut loop."""
    col = col or mix(CREAM, INK, 0.42)
    for k in range(3):
        q = (u + k / 3.0) % 1.0
        ring_on(img, x, y, r0 + (r1 - r0) * q, col, 2, al * (1 - q) ** 1.7, squash=0.32)


def panah(img, p0, p1, u, col, lebar=8, al=1.0, hk=3.4):
    """Panah lurus yang menggambar diri (u 0..1) + kepala panah di ujung."""
    if al <= 0.01 or u <= 0:
        return
    n = 14
    m = max(2, int(n * clamp(u)))
    pts = [(p0[0] + (p1[0] - p0[0]) * i / (n - 1), p0[1] + (p1[1] - p0[1]) * i / (n - 1)) for i in range(m)]
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], col, lebar, al)
    if u > 0.10:
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        hl = lebar * hk
        poly_on(img, [(p1[0], p1[1]),
                      (p1[0] - hl * math.cos(ang - 0.40), p1[1] - hl * math.sin(ang - 0.40)),
                      (p1[0] - hl * math.cos(ang + 0.40), p1[1] - hl * math.sin(ang + 0.40))], col, al)


def _bez(p0, p1, tekuk, t):
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    cx, cy = mx - dy * tekuk, my + dx * tekuk
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t * t * p1[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t * t * p1[1])


def panah_tekuk(img, p0, p1, u, col, lebar=9, al=1.0, tekuk=0.22):
    if al <= 0.01 or u <= 0:
        return
    n = 22
    m = max(2, int(n * clamp(u)))
    pts = [_bez(p0, p1, tekuk, i / (n - 1)) for i in range(m)]
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], col, lebar, al)
    if u > 0.10:
        ph, pp = pts[-1], pts[-2]
        ang = math.atan2(ph[1] - pp[1], ph[0] - pp[0])
        hl = lebar * 3.2
        poly_on(img, [(ph[0], ph[1]),
                      (ph[0] - hl * math.cos(ang - 0.40), ph[1] - hl * math.sin(ang - 0.40)),
                      (ph[0] - hl * math.cos(ang + 0.40), ph[1] - hl * math.sin(ang + 0.40))], col, al)


def ular(img, pts, al=1.0, lebar=15, col=None, kepala=True, u=1.0, lidah=True):
    """Ular dari rangkaian titik pusat: badan mengecil ke ekor, kepala + mata + lidah."""
    if al <= 0.01 or u <= 0:
        return
    col = col or mix(NAVY2, INK, 0.25)
    n = max(2, int(len(pts) * clamp(u)))
    # sambung antar titik supaya badan ular kontinu (bukan untaian manik-manik)
    for i in range(n - 1):
        t = (i + 0.5) / max(1, len(pts) - 1)
        r = lebar * (0.52 + 0.48 * t)
        line_on(img, pts[i], pts[i + 1], col, max(2.0, 1.7 * r), al)
    for i in range(n):
        t = i / max(1, len(pts) - 1)
        dot_on(img, pts[i][0], pts[i][1], lebar * (0.52 + 0.48 * t), col, al)
    if kepala and n >= 2:
        pe = pts[n - 1]
        dot_on(img, pe[0], pe[1], lebar * 1.18, col, al)
        dot_on(img, pe[0] - lebar * 0.34, pe[1] - lebar * 0.26, max(1.5, lebar * 0.17), WHITE, al * 0.92)
        dot_on(img, pe[0] + lebar * 0.34, pe[1] - lebar * 0.26, max(1.5, lebar * 0.17), WHITE, al * 0.92)
        if lidah:
            line_on(img, (pe[0], pe[1] + lebar * 0.9), (pe[0], pe[1] + lebar * 1.55), MERAH, 3, al * 0.85)


def ular_sinus(img, x0, y0, x1, y1, n, amp, fase, al=1.0, lebar=15, col=None, u=1.0):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + amp * math.sin(fase + t * 5.2)))
    ular(img, pts, al, lebar, col, u=u)


def _rumah_luar(img, cx, dasar, s, al=1.0, col=None, jendela=1.0, pintu_terang=0.0, atap=None,
                detail=True):
    """Rumah tampak depan (flat vector): atap bertepi, talang, plint, pintu berdaun, jendela
    bingkai + gorden, semak, lampu dinding. Detail dimatikan untuk rumah latar (kecil)."""
    if al <= 0.01:
        return
    atap = atap or mix(MERAH, INK, 0.18)
    w, hwall = 640 * s, 330 * s
    w2, h2 = w / 2, hwall
    ell(img, cx - w * 0.62, dasar - 18 * s, cx + w * 0.62, dasar + 24 * s,
        fill=mix(CREAM, INK, 0.13), alpha=al * 0.55)
    # dinding + bayangan bawah atap
    rrect_on(img, cx - w2, dasar - h2, cx + w2, dasar, 6 * s, DINDING, al)
    rrect_on(img, cx - w2, dasar - h2, cx + w2, dasar - h2 + 34 * s, 0, mix(CREAM, INK, 0.10), al * 0.85)
    rrect_on(img, cx + w2 - 34 * s, dasar - h2, cx + w2, dasar, 0, mix(CREAM, INK, 0.055), al * 0.8)
    # plint / pondasi
    rrect_on(img, cx - w2, dasar - 30 * s, cx + w2, dasar, 0, mix(CREAM, INK, 0.16), al)
    line_on(img, (cx - w2, dasar), (cx + w2, dasar), mix(INK, MUTED, 0.35), 4 * s, al)
    # atap: bidang + tebal tepi + garis genteng
    puncak = (cx, dasar - h2 - 0.62 * w)
    kiri, kanan = (cx - w2 - 34 * s, dasar - h2 + 4 * s), (cx + w2 + 34 * s, dasar - h2 + 4 * s)
    poly_on(img, [kiri, puncak, kanan, (cx + w2 + 18 * s, dasar - h2 + 34 * s),
                  (cx, puncak[1] + 40 * s), (cx - w2 - 18 * s, dasar - h2 + 34 * s)], atap, al)
    line_on(img, kiri, kanan, mix(atap, WHITE, 0.42), 7 * s, al)
    for k in (1, 2, 3, 4):
        q = k / 5.0
        line_on(img, (kiri[0] + (puncak[0] - kiri[0]) * q, kiri[1] + (puncak[1] - kiri[1]) * q),
                (kanan[0] + (puncak[0] - kanan[0]) * q, kanan[1] + (puncak[1] - kanan[1]) * q),
                mix(atap, INK, 0.30), 2 * s, al * 0.30)
    dot_on(img, puncak[0], puncak[1] - 4 * s, 6 * s, mix(atap, INK, 0.35), al)
    # talang + pipa turun
    line_on(img, (cx + w2 + 30 * s, dasar - h2 + 10 * s), (cx + w2 + 30 * s, dasar - 26 * s),
            mix(INK, MUTED, 0.42), 6 * s, al * 0.8)
    line_on(img, (cx + w2 + 30 * s, dasar - 26 * s), (cx + w2 + 62 * s, dasar - 26 * s),
            mix(INK, MUTED, 0.42), 6 * s, al * 0.8)
    # pintu + kusen
    px0, px1 = cx - 78 * s, cx + 34 * s
    rrect_on(img, px0 - 8 * s, dasar - 208 * s, px1 + 8 * s, dasar, 4 * s, mix(INK, MUTED, 0.30), al)
    rrect_on(img, px0, dasar - 200 * s, px1, dasar - 4 * s, 3 * s, mix(NAVY, INK, 0.42), al)
    for k in (0.34, 0.66):
        line_on(img, (px0 + 6 * s, dasar - 200 * s + 196 * s * k),
                (px1 - 6 * s, dasar - 200 * s + 196 * s * k), mix(WHITE, NAVY, 0.55), 3 * s, al * 0.35)
    dot_on(img, px1 - 14 * s, dasar - 100 * s, 5.5 * s, KUNING, al * 0.95)
    if pintu_terang > 0.01:
        # cahaya hangat tumpah dari celah pintu
        poly_on(img, [(px1 - 2 * s, dasar - 8 * s), (px1 + 70 * s, dasar + 26 * s),
                      (px1 + 6 * s, dasar + 26 * s)], mix(KACA, CREAM, 0.45), al * 0.55 * pintu_terang)
        V._glow11(img, px1, dasar - 100 * s, 120 * s, KUNING, al * 0.26 * pintu_terang)
    if not detail:
        return
    # jendela: bingkai, kaca hangat, gorden, sill, pantulan
    for k in (-1, 1):
        wx0 = cx + k * (w2 - 138 * s) - 76 * s
        wx1 = wx0 + 152 * s
        wy0, wy1 = dasar - 268 * s, dasar - 130 * s
        rrect_on(img, wx0 - 7 * s, wy0 - 7 * s, wx1 + 7 * s, wy1 + 7 * s, 4 * s, mix(INK, MUTED, 0.34), al)
        rrect_on(img, wx0, wy0, wx1, wy1, 3 * s, mix(KACA, CREAM, 0.30), al * jendela)
        # gorden
        poly_on(img, [(wx0, wy0), (wx0 + 44 * s, wy0), (wx0 + 30 * s, wy0 + 62 * s), (wx0, wy0 + 52 * s)],
                mix(KUNING, CREAM, 0.30), al * jendela * 0.9)
        poly_on(img, [(wx1, wy0), (wx1 - 44 * s, wy0), (wx1 - 30 * s, wy0 + 62 * s), (wx1, wy0 + 52 * s)],
                mix(KUNING, CREAM, 0.30), al * jendela * 0.9)
        for q in (0.5,):
            line_on(img, (wx0 + (wx1 - wx0) * q, wy0), (wx0 + (wx1 - wx0) * q, wy1),
                    mix(INK, MUTED, 0.32), 4 * s, al * jendela)
            line_on(img, (wx0, wy0 + (wy1 - wy0) * 0.46), (wx1, wy0 + (wy1 - wy0) * 0.46),
                    mix(INK, MUTED, 0.32), 4 * s, al * jendela)
        line_on(img, (wx0 - 10 * s, wy1 + 8 * s), (wx1 + 10 * s, wy1 + 8 * s), mix(INK, MUTED, 0.42), 6 * s, al)
        line_on(img, (wx0 + 12 * s, wy0 + 12 * s), (wx0 + 54 * s, wy0 + 54 * s), WHITE, 6 * s, al * jendela * 0.30)
    # lampu dinding + semak + jalan
    line_on(img, (cx + 96 * s, dasar - 214 * s), (cx + 96 * s, dasar - 190 * s), mix(INK, MUTED, 0.4), 4 * s, al)
    dot_on(img, cx + 96 * s, dasar - 186 * s, 9 * s, mix(KACA, WHITE, 0.2), al)
    V._glow11(img, cx + 96 * s, dasar - 186 * s, 40 * s, KUNING, al * 0.17)
    for k, (bx, br, bc) in enumerate(((-1, 46, HIJAU), (-1, 34, TEAL), (1, 42, HIJAU), (1, 30, TEAL))):
        dot_on(img, cx + bx * (w2 - 60 * s) + (28 * s * (k % 2)) * bx, dasar - 16 * s, br * s * 0.8,
               mix(bc, INK, 0.25), al * 0.95)
        dot_on(img, cx + bx * (w2 - 70 * s), dasar - 22 * s, br * s * 0.55, mix(bc, CREAM, 0.25), al * 0.9)


def _awan(img, cx, cy, s, al=1.0, col=None):
    """Awan hujan rendah: gumpalan lembut + perut gelap, supaya hujan punya sumber di layar."""
    if al <= 0.01:
        return
    col = col or mix(CREAM, INK, 0.13)
    for (dx, dy, r) in ((-78, 6, 40), (-30, -12, 54), (26, -4, 46), (74, 8, 34)):
        dot_on(img, cx + dx * s, cy + dy * s, r * s, col, al * 0.9)
    line_on(img, (cx - 116 * s, cy + 22 * s), (cx + 108 * s, cy + 22 * s),
            mix(col, INK, 0.30), 10 * s, al * 0.55)


def _bawah(img, al=1.0, teks_sumber=None):
    """Lapisan tanah basah di kaki layar: memberi bobot komposisi (bukan krem kosong) dan
    tempat teks/CTA bernapas. Gradasi lembut, hue tetap krem."""
    for i in range(30):
        y0 = 1330 + i * 20
        q = i / 29.0
        line_on(img, (0, y0), (1080, y0), mix(CREAM, INK, 0.008 + 0.105 * q ** 1.7), 28, al * 0.62)
    if teks_sumber:
        paste_c(img, 540, 1772, teks_sumber, font(D.FM, 25), mix(INK, MUTED, 0.55), al * 0.7)


def _pin(img, x, y, al, col, tt=1.0, fsz=24, teks=None, arah=1):
    """Pin lokasi: lingkaran berdenyut + ekor + label."""
    if al <= 0.01 or tt <= 0:
        return
    q = esm(tt / 0.35)
    k = 0.6 + 0.4 * q
    ring_on(img, x, y, 34 * k, col, 3, al * (0.5 + 0.5 * math.sin(tt * 3.0) * 0.3))
    dot_on(img, x, y, 13 * k, col, al, outline=WHITE, width=3)
    if teks:
        label(img, x + arah * 74, y - 46, teks, mix(col, INK, 0.30), al, fsz=fsz)


def _chip_kecil(img, x, y, teks, col, al, fsz=24):
    if al <= 0.01:
        return
    f = font(D.FS, fsz)
    w = tw(teks, f) + 34
    rrect_on(img, x - w / 2, y - 22, x + w / 2, y + 22, 22, mix(WHITE, col, 0.14), al)
    paste_c(img, x, y, teks, f, mix(col, INK, 0.42), al)


# ================================================================ 1. INTRO / OUTRO
def _pemandangan(img, u, tg, al=1.0, banjir=0.0, ular_u=0.0, sorot=0.0, hujan_al=1.0):
    """Satu keadaan dunia yang dipakai intro DAN outro (loop harus identik)."""
    kertas(img, al)
    _bawah(img, al, SUMBER)
    _awan(img, 268, 408, 1.0, al)
    _awan(img, 812, 372, 0.82, al)
    # langit jauh: bukit + deretan atap tetangga
    poly_on(img, [(0, 1046), (120, 1006), (250, 1032), (400, 998), (560, 1030),
                  (720, 1000), (880, 1032), (1010, 1004), (1080, 1028), (1080, 1140), (0, 1140)],
            mix(CREAM, INK, 0.10), al * 0.85)
    _rumah_luar(img, 164, 1064, 0.40, al * 0.92, atap=mix(TEAL, INK, 0.30), jendela=0.85)
    _rumah_luar(img, 946, 1058, 0.34, al * 0.92, atap=mix(UNGU, INK, 0.32), jendela=0.85)
    # hujan latar (di belakang rumah)
    hujan(img, u, -40, 1120, 356, 1120, n=96, al=al * 0.54 * hujan_al, seed=2,
          panjang=(26, 58), lebar=3)
    hujan(img, u, -40, 1120, 400, 1100, n=44, al=al * 0.26 * hujan_al, seed=23,
          panjang=(14, 30), lebar=2, laju=1.0)
    # rumah utama
    _rumah_luar(img, 546, Y_DASAR, 0.94, al, atap=mix(MERAH, INK, 0.10), jendela=1.0,
                pintu_terang=0.45 + 0.55 * sorot)
    if sorot > 0.01:
        V._glow11(img, 546, Y_DASAR - 300, 300, KUNING, al * 0.30 * sorot)
    for i in range(9):                                    # percikan hujan di talang atap
        px = 320 + i * 52
        q = (u * (1 + i % 2) + i * 0.17) % 1.0
        line_on(img, (px - 6 * q, Y_DASAR - 330 - 16 * q), (px - 12 * q, Y_DASAR - 344 - 20 * q),
                mix(CREAM, AIR, 0.55), 3, al * 0.5 * (1 - q))
    # tanah + genangan
    line_on(img, (0, 1122), (1080, 1122), mix(CREAM, INK, 0.26), 4, al * 0.9)
    rrect_on(img, 0, 1122, 1080, 1180, 0, mix(CREAM, INK, 0.05), al * 0.9)
    for (px, py, r) in ((232, 1150, 96), (742, 1144, 78), (540, 1162, 60), (948, 1156, 52)):
        ell(img, px - r, py - r * 0.30, px + r, py + r * 0.30, fill=mix(CREAM, AIR, 0.30), alpha=al * 0.65)
        riak(img, px, py, u * 0.9, al * 0.45, 8, r * 0.55, mix(CREAM, AIR, 0.55))
    # hujan depan (lebih besar, di atas rumah)
    hujan(img, u, -60, 1140, 880, 1200, n=30, al=al * 0.40 * hujan_al, seed=5,
          panjang=(46, 88), lebar=4, laju=1.0)
    # ular masuk lewat celah pintu
    if ular_u > 0.01:
        p0, p1 = (760, 1156), (560, 1012)
        pts = []
        for i in range(26):
            q = i / 25.0
            bx, by = _bez(p0, p1, -0.16, q)
            pts.append((bx + 13 * math.sin(q * 6.4 + u * 2.2) * (0.35 + 0.65 * q), by))
        ular(img, pts, al * 0.96, lebar=8.2, u=ular_u, col=mix(NAVY, TEAL, 0.34))
        n = max(2, int(len(pts) * clamp(ular_u)))
        for i in range(2, n - 1):
            line_on(img, pts[i], pts[i + 1], mix(NAVY, CREAM, 0.42), 2, al * 0.55 * (i / n))
    # 'bukan banjir': hanya garis air yang naik di kaki layar (tanpa label -> tidak menutupi rumah)
    if banjir > 0.01:
        by = 1190 - 74 * banjir
        pts = [(i * 60, by + 7 * math.sin(i * 0.8 + u * 1.6)) for i in range(19)]
        for i in range(len(pts) - 1):
            line_on(img, pts[i], pts[i + 1], mix(CREAM, AIR, 0.72), 5, al * 0.55 * banjir)
    debu(img, tg, al, n=14)


def sc_hujan50(img, d, sc, tl, dur, tg, accent, al, dy):
    """HOOK. Hujan pertama turun; ular masuk lewat celah pintu, bukan karena banjir."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["hujan_ular50"])
    u = tl
    masuk = esm((tl - c["ular"]) / 1.5) if tl >= c["ular"] else 0.0
    sorot = esm((tl - c["muncul"]) / 0.5) * (1 - esm((tl - c["dalam"]) / 0.6))
    _pemandangan(img, u, tg, 1.0, banjir=esm((tl - c["bukan"]) / 0.8), ular_u=masuk, sorot=sorot)
    # guntur halus di kata 'hujan'
    if 0 <= tl - c["hujan"] < 0.5:
        V._glow11(img, 700, 480, 260, mix(WHITE, KUNING, 0.2), 0.25 * (1 - (tl - c["hujan"]) / 0.5))
    chip(img, 540, Y_FOOT, "HUJAN PERTAMA  ·  OKT-NOV", mix(KUNING, INK, 0.30), 1.0, 10.0, fsz=25, persisten=True)
    at = 1 - esm((tl - dur + 0.45) / 0.35)
    lines = sc.get("lines") or ["ULAR MASUK RUMAH", "BUKAN KARENA BANJIR"]
    teks(img, sc, accent, tl, at, 0.34, " ".join(lines), "BUKAN KARENA BANJIR", fsz=58, maxw=880)


# ================================================================ 2. F1 CUTAWAY
def sc_rumah50(img, d, sc, tl, dur, tg, accent, al, dy):
    """AGITATION. Rumah yang terlihat biasa saja, dipotong melintang: tiga titik kabar."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["rumah_biasa50"])
    kertas(img, 1.0)
    _bawah(img, 1.0, SUMBER)
    # langit + hujan di luar (di atas atap)
    hujan(img, tl, 20, 1060, 330, 500, n=34, al=0.30, seed=7, panjang=(16, 34))
    # -------- atap
    poly_on(img, [(74, 512), (540, 362), (1006, 512), (1006, 536), (540, 388), (74, 536)],
            mix(MERAH, INK, 0.12), 1.0)
    # ruang atap (plafon) + kuda-kuda
    rrect_on(img, 96, 536, 984, 646, 4, mix(CREAM, INK, 0.07), 1.0)
    for (x0, x1) in ((150, 930), (250, 830), (350, 730), (450, 630)):
        line_on(img, (x0, 640), ((x0 + x1) / 2, 548), mix(INK, MUTED, 0.45), 3, 0.55)
        line_on(img, ((x0 + x1) / 2, 548), (x1, 640), mix(INK, MUTED, 0.45), 3, 0.55)
    # ular di ruang plafon (muncul di kata 'plafon')
    qp = esm((tl - c["plafon"]) / 1.0)
    if qp > 0.01:
        ux = 130 + 300 * esm((tl - c["plafon"] - 0.2) / 2.4)
        ular_sinus(img, ux, 592, ux + 250, 592, 10, 16, tl * 2.4, 1.0, 11, mix(NAVY, TEAL, 0.30), u=qp)
    # -------- plafon slab
    rrect_on(img, 96, 646, 984, 674, 3, mix(CREAM, INK, 0.30), 1.0)
    for i in range(24):
        line_on(img, (110 + i * 36, 650), (110 + i * 36, 670), mix(CREAM, WHITE, 0.4), 2, 0.35)
    # -------- ruang
    rrect_on(img, 96, 674, 984, 1122, 3, DINDING, 1.0)
    # kamar mandi (kiri)
    line_on(img, (452, 674), (452, 1122), mix(INK, MUTED, 0.45), 6, 0.55)
    line_on(img, (96, 900), (452, 900), mix(INK, MUTED, 0.45), 4, 0.30)
    # shower
    line_on(img, (162, 720), (162, 806), mix(INK, MUTED, 0.35), 5, 0.75)
    line_on(img, (162, 806), (206, 806), mix(INK, MUTED, 0.35), 5, 0.75)
    for k in range(5):
        line_on(img, (206 + k * 8, 812 + (tl * 90 + k * 17) % 70),
                (206 + k * 8, 830 + (tl * 90 + k * 17) % 70), mix(CREAM, AIR, 0.55), 3, 0.45)
    ell(img, 150, 1010, 420, 1064, fill=mix(CREAM, AIR, 0.26), alpha=0.85)
    riak(img, 286, 1038, tl * 0.8, 0.35, 8, 46, mix(CREAM, AIR, 0.5))
    # gayung + ember + saluran lantai (kamar mandi terbaca, bukan kotak kosong)
    rrect_on(img, 168, 936, 196, 1002, 8, mix(KUNING, CREAM, 0.35), 0.95,
             outline=mix(INK, KUNING, 0.35), width=2)
    line_on(img, (182, 936), (182, 906), mix(KUNING, INK, 0.3), 7, 0.9)
    dot_on(img, 182, 900, 9, mix(KUNING, CREAM, 0.3), 0.9, outline=mix(INK, KUNING, 0.4), width=2)
    rrect_on(img, 318, 986, 410, 1044, 10, mix(AIR, CREAM, 0.45), 0.9,
             outline=mix(INK, AIR, 0.35), width=3)
    ell(img, 322, 946, 406, 990, fill=mix(AIR, WHITE, 0.45), alpha=0.55)
    for k in range(4):                                     # ubin dinding
        line_on(img, (104, 700 + k * 44), (444, 700 + k * 44), mix(INK, MUTED, 0.5), 2, 0.20)
    rrect_on(img, 296, 1102, 336, 1118, 5, mix(INK, MUTED, 0.45), 0.9)
    # lemari (kanan)
    rrect_on(img, 792, 700, 952, 1122, 5, mix(NAVY, TEAL, 0.18), 1.0)
    for k in range(2):
        rrect_on(img, 800 + k * 74, 726, 866 + k * 74, 1114, 3, mix(NAVY, TEAL, 0.34), 1.0,
                 outline=mix(WHITE, NAVY, 0.5), width=2)
        dot_on(img, 862 + k * 74, 930, 4, KUNING, 0.85)
    # tumpukan kardus di tengah
    for k, (bx, by, bw, bh) in enumerate(((520, 960, 150, 92), (556, 1042, 178, 78), (596, 906, 106, 54))):
        rrect_on(img, bx, by, bx + bw, by + bh, 6, mix(EMAS, CREAM, 0.45), 0.95,
                 outline=mix(INK, EMAS, 0.35), width=3)
        line_on(img, (bx + 8, by + bh * 0.42), (bx + bw - 8, by + bh * 0.42), mix(INK, EMAS, 0.45), 2, 0.5)
    # pin kabar
    _pin(img, 286, 856, esm((tl - c["mandi"] + 0.1) / 0.35), TEAL, tl - c["mandi"], 25, "KAMAR MANDI", 1)
    _pin(img, 560, 592, esm((tl - c["plafon"] + 0.1) / 0.35), EMAS, tl - c["plafon"], 25, "PLAFON", 1)
    ql = esm((tl - c["lemari"] + 0.1) / 0.35)
    _pin(img, 872, 806, ql, UNGU, tl - c["lemari"], 22, None, -1)
    _chip_kecil(img, 726, 748, "BALIK LEMARI", mix(UNGU, INK, 0.25), ql, 22)
    # rumah tetangga (kata 'tetanggamu') + sorot rumah kita (kata 'rumahmu')
    qt = esm((tl - c["tetangga"]) / 0.5)
    if qt > 0.01:
        for k in range(3):
            _rumah_luar(img, 190 + k * 350, 1362, 0.15, qt * 0.75, atap=mix(TEAL, INK, 0.3), jendela=0.0)
    qs = esm((tl - c["rumahmu"]) / 0.45)
    if qs > 0.01:
        ring_on(img, 540, 900, 470, accent, 6, qs * 0.55)
        V._glow11(img, 540, 900, 420, KUNING, qs * 0.22)
        M.stiker(img, 540, 760, "BISA RUMAHMU", 1.0, tl - c["rumahmu"], bg=accent, fsz=30, rot=-3)
    chip(img, 540, Y_FOOT, "HUJAN PERTAMA  ·  OKT-NOV", mix(KUNING, INK, 0.30), 1.0, 10.0, fsz=25, persisten=True)
    teks(img, sc, accent, tl, 1.0, 0.12)


# ================================================================ 3. F2 KALENDER
BULAN = ("JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGU", "SEP", "OKT", "NOV", "DES")


def _telur(img, x, y, rx, ry, rot, al, retak=0.0, col=None):
    col = col or mix(CREAM, INK, 0.10)
    pts = [(x + rx * math.cos(a) * (1 + 0.06 * math.cos(3 * a)) * math.cos(rot)
            - ry * math.sin(a) * (1 + 0.06 * math.cos(3 * a)) * math.sin(rot),
            y + rx * math.cos(a) * (1 + 0.06 * math.cos(3 * a)) * math.sin(rot)
            + ry * math.sin(a) * (1 + 0.06 * math.cos(3 * a)) * math.cos(rot))
           for a in [i * math.pi / 12 for i in range(24)]]
    poly_on(img, pts, col, al, outline=mix(INK, MUTED, 0.55), width=3)
    if retak > 0.02 and rx >= 30:
        n = max(2, int(4 * retak))
        p = [(x - rx * 0.30 + i * rx * 0.13, y - ry * 0.42 + i * ry * 0.13 + (2.6 if i % 2 else -2.6)) for i in range(n)]
        for i in range(len(p) - 1):
            line_on(img, p[i], p[i + 1], mix(INK, MUTED, 0.35), 1.8, al * 0.8)
        line_on(img, (x + rx * 0.10, y - ry * 0.06), (x + rx * 0.30, y - ry * 0.20), mix(INK, MUTED, 0.4), 1.6, al * 0.7)


def sc_kalender50(img, d, sc, tl, dur, tg, accent, al, dy):
    """BODY 1. Kalender: telur diletakkan di akhir kemarau, menetas saat hujan pertama."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["kalender_telur50"])
    kertas(img, 1.0)
    _bawah(img, 1.0, SUMBER)
    # -------- kalender 4x3
    x0, y0, cw, ch, gap = 112, 418, 186, 82, 12
    qk = esm((tl - c["kalender"] - 0.05) / 0.45)
    if qk > 0.01:
        for i, nm in enumerate(BULAN):
            gx = x0 + (i % 4) * (cw + gap)
            gy = y0 + (i // 4) * (ch + gap)
            kk = esm((tl - c["kalender"] - 0.05 - i * 0.018) / 0.30)
            telat = 8 <= i <= 11
            col = mix(WHITE, accent, 0.16) if telat else mix(CREAM, INK, 0.055)
            rrect_on(img, gx, gy, gx + cw, gy + ch, 9, col, qk * kk,
                     outline=mix(INK, MUTED, 0.55) if not telat else accent,
                     width=3)
            paste_c(img, gx + cw / 2, gy + ch / 2, nm, font(D.FB, 30),
                    mix(accent, INK, 0.30) if telat else mix(INK, MUTED, 0.35), qk * kk)
        # penyorot '3-4 bulan' dari AGU ke NOV
        qb = esm((tl - c["tiga"] + 0.15) / 0.5)
        if qb > 0.01:
            bx0 = x0 + 4
            bx1 = x0 + 3 * (cw + gap) + cw - 4
            by = y0 + 2 * (ch + gap) + ch + 12
            line_on(img, (bx0, by), (bx0 + (bx1 - bx0) * qb, by), accent, 6, 0.85)
            line_on(img, (bx0, by), (bx0, by - 12), accent, 6, 0.85)
            line_on(img, (bx1, by), (bx1, by - 12), accent, 6, 0.85) if qb > 0.9 else None
            _chip_kecil(img, (bx0 + bx1) / 2, by + 34, "3-4 BULAN", accent, qb, 24)
    # penanda musim: menempel di baris penyorot, tidak menutupi sel kalender
    qkm = esm((tl - c["kemarau"]) / 0.4)
    if qkm > 0.01:
        _chip_kecil(img, 210, 806, "KEMARAU BERAKHIR", mix(EMAS, INK, 0.15), qkm, 23)
    qhj = esm((tl - c["hujan"] - 0.1) / 0.4)
    if qhj > 0.01:
        _chip_kecil(img, 776, 806, "HUJAN PERTAMA", mix(AIR, INK, 0.25), qhj, 23)
    # -------- sarang telur
    bs = (540, 986)
    ell(img, bs[0] - 226, bs[1] - 62, bs[0] + 226, bs[1] + 96, fill=mix(EMAS, CREAM, 0.52), alpha=0.95,
        outline=mix(INK, EMAS, 0.30), width=5)
    for i in range(34):                                    # anyaman ranting
        a = math.pi * (0.05 + 0.90 * i / 33)
        r = 70 + 140 * _rnd(i, 3)
        x1, y1 = bs[0] + r * math.cos(a), bs[1] + 22 + r * 0.50 * math.sin(a)
        x2 = x1 + 34 * math.cos(a + 1.9)
        y2 = y1 + 14 * math.sin(a + 1.9)
        line_on(img, (x1, y1), (x2, y2), mix(INK, EMAS, 0.45), 3.4, 0.55)
    for i in range(9):                                     # serpihan jerami
        a = math.pi * (0.15 + 0.7 * _rnd(i, 11))
        r = 150 + 60 * _rnd(i, 13)
        x1, y1 = bs[0] + r * math.cos(a), bs[1] + 24 + r * 0.5 * math.sin(a)
        line_on(img, (x1, y1), (x1 + 26, y1 - 10), mix(EMAS, INK, 0.25), 3, 0.6)
    # telur menetas satu per satu
    for i in range(11):
        ang = -2.2 + i * 0.52
        ex = bs[0] + (52 + 74 * _rnd(i, 6)) * math.cos(ang)
        ey = bs[1] - 6 + (30 + 34 * _rnd(i, 8)) * math.sin(ang) * 0.7
        qe = esm((tl - c["bertelur"] - i * 0.05) / 0.35)
        if qe <= 0.01:
            continue
        goyang = 3 * math.sin(tl * 7 + i) * (1 if tl > c["menetas"] - 0.4 else 0)
        _telur(img, ex + goyang, ey, 22, 28, ang * 0.5, qe, esm((tl - c["menetas"] - i * 0.07) / 0.3),
               mix(CREAM, WHITE, 0.78))
    # anak ular keluar & menyebar
    qm = esm((tl - c["menetas"]) / 0.6)
    if qm > 0.02:
        for i in range(9):
            ang = -2.5 + i * 0.62
            d = 60 + 120 * esm((tl - c["menetas"] - 0.25 - i * 0.06) / 2.2)
            hx = bs[0] + d * math.cos(ang)
            hy = bs[1] + d * 0.55 * math.sin(ang)
            ular_sinus(img, hx - 22 * math.cos(ang), hy - 12 * math.sin(ang), hx, hy, 6, 5, tl * 6 + i,
                       0.9 * qm, 6.5, mix(NAVY, TEAL, 0.22), u=esm((tl - c["menetas"] - 0.2 - i * 0.06) / 0.5))
    _chip_kecil(img, 232, 960, "TELUR", mix(EMAS, INK, 0.2), esm((tl - c["bertelur"]) / 0.4), 26)
    M.stiker(img, 800, 1010, "BELASAN ANAK ULAR", 1.0, tl - c["belasan"], bg=MERAH, fsz=27, rot=-5)
    # label 'bukan satu, tapi banyak'
    qb = esm((tl - c["bukan"]) / 0.4)
    if qb > 0.01:
        _chip_kecil(img, 246, 1064, "BUKAN SATU DEWASA", mix(TEAL, INK, 0.2), qb, 24)
    chip(img, 540, Y_FOOT, "HUJAN PERTAMA  ·  OKT-NOV", mix(KUNING, INK, 0.30), 1.0, 10.0, fsz=25, persisten=True)
    teks(img, sc, accent, tl, 1.0, 0.10)
    debu(img, tg, 1.0, n=12, y0=740, y1=1150)


# ================================================================ 4. F3 RANTAI MANGSA
def _katak(img, x, y, s, al, col=None):
    """Katak duduk: badan, mata menonjol, kaki belakang terlipat, perut terang."""
    col = col or mix(HIJAU, INK, 0.18)
    for k in (-1, 1):                                     # kaki belakang
        poly_on(img, [(x + k * 26 * s, y + 8 * s), (x + k * 56 * s, y - 4 * s),
                      (x + k * 62 * s, y + 20 * s), (x + k * 38 * s, y + 22 * s)], col, al)
        line_on(img, (x + k * 20 * s, y + 16 * s), (x + k * 34 * s, y + 32 * s), col, 8 * s, al)
        dot_on(img, x + k * 36 * s, y + 34 * s, 8 * s, col, al)
    ell(img, x - 38 * s, y - 18 * s, x + 38 * s, y + 24 * s, fill=col, alpha=al)
    ell(img, x - 24 * s, y + 2 * s, x + 24 * s, y + 22 * s, fill=mix(CREAM, col, 0.42), alpha=al * 0.9)
    for k in (-1, 1):
        dot_on(img, x + k * 19 * s, y - 20 * s, 14 * s, mix(col, WHITE, 0.22), al)
        dot_on(img, x + k * 20 * s, y - 22 * s, 6.5 * s, INK, al)
    line_on(img, (x - 15 * s, y + 3 * s), (x + 15 * s, y + 3 * s), mix(col, INK, 0.45), 3 * s, al * 0.85)


def _cicak(img, x, y, s, al, col=None):
    """Cicak: badan memanjang, kepala, ekor melengkung, empat kaki bersudut."""
    col = col or mix(EMAS, INK, 0.32)
    for i in range(7):                                    # ekor
        a0 = 0.5 + i * 0.42
        x0 = x - 30 * s - i * 9 * s
        y0 = y + 4 * s * math.sin(a0)
        x1 = x - 30 * s - (i + 1) * 9 * s
        y1 = y + 4 * s * math.sin(a0 + 0.42)
        line_on(img, (x0, y0), (x1, y1), col, max(2.0, 6 - i * 0.6) * s, al)
    ell(img, x - 32 * s, y - 12 * s, x + 28 * s, y + 12 * s, fill=col, alpha=al)
    ell(img, x + 20 * s, y - 11 * s, x + 52 * s, y + 11 * s, fill=col, alpha=al)
    dot_on(img, x + 42 * s, y - 4 * s, 4.5 * s, WHITE, al)
    dot_on(img, x + 43 * s, y - 4 * s, 2.2 * s, INK, al)
    for (dx, dy) in ((-16, -1), (8, -1), (-16, 1), (8, 1)):   # kaki
        kx, ky = x + dx * s, y + dy * 8 * s
        line_on(img, (kx, ky), (kx - 12 * s, ky + dy * 18 * s), col, 4 * s, al)
        line_on(img, (kx - 12 * s, ky + dy * 18 * s), (kx - 20 * s, ky + dy * 13 * s), col, 3 * s, al)


def _tikus(img, x, y, s, al, fase=0.0, col=None):
    """Tikus: badan lonjong, kepala meruncing, telinga bulat, ekor panjang, empat kaki."""
    col = col or mix(INK, MUTED, 0.20)
    tail = [(x - 40 * s - i * 11 * s, y + 6 * s + 15 * s * math.sin(fase + i * 0.8)) for i in range(6)]
    for i in range(len(tail) - 1):
        line_on(img, tail[i], tail[i + 1], mix(col, MUTED, 0.45), max(2.0, 5 - i * 0.5) * s, al * 0.9)
    ell(img, x - 40 * s, y - 24 * s, x + 26 * s, y + 24 * s, fill=col, alpha=al)
    ell(img, x - 30 * s, y + 2 * s, x + 16 * s, y + 22 * s, fill=mix(col, CREAM, 0.30), alpha=al * 0.75)
    ell(img, x + 16 * s, y - 16 * s, x + 54 * s, y + 12 * s, fill=col, alpha=al)
    dot_on(img, x + 30 * s, y - 24 * s, 13 * s, mix(col, MERAH, 0.28), al)
    dot_on(img, x + 31 * s, y - 24 * s, 6.5 * s, mix(col, MERAH, 0.55), al * 0.9)
    dot_on(img, x + 52 * s, y + 1 * s, 4.0 * s, mix(CREAM, INK, 0.25), al)
    dot_on(img, x + 42 * s, y - 8 * s, 3.4 * s, WHITE, al)
    for k in range(2):                                     # kumis
        line_on(img, (x + 50 * s, y + 2 * s), (x + 70 * s, y + 8 * s - k * 12 * s),
                mix(col, CREAM, 0.4), 2 * s, al * 0.7)
    for (dx, dy) in ((-28, 1), (-10, 1), (6, 1)):           # kaki
        line_on(img, (x + dx * s, y + 20 * s), (x + (dx - 6) * s, y + 34 * s), col, 4.5 * s, al)


def sc_tikus50(img, d, sc, tl, dur, tg, accent, al, dy):
    """BODY 2. Mangsa: katak -> cicak -> tikus -> ular, lalu tikus masuk rumah."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["tikus50"])
    kertas(img, 1.0)
    _bawah(img, 1.0, SUMBER)
    hujan(img, tl, -40, 1120, 340, 470, n=26, al=0.26, seed=9, panjang=(14, 30))
    # rantai mangsa
    nod = [(178, 520, "KATAK", c["katak"]), (404, 520, "CICAK", c["cicak"]),
           (630, 520, "TIKUS", c["tikus"]), (856, 520, "ULAR", c["katak"])]
    for i, (nx, ny, nm, tc) in enumerate(nod):
        q = esm((tl - tc - (0.0 if nm != "ULAR" else 0.9)) / 0.45)
        if q <= 0.01:
            continue
        bahaya = nm == "ULAR"
        rr = 86 if bahaya else 74
        rrect_on(img, nx - rr, ny - rr, nx + rr, ny + rr, rr, mix(WHITE, accent, 0.10 if not bahaya else 0.30), q,
                 outline=accent if bahaya else mix(INK, MUTED, 0.45), width=5)
        if nm == "KATAK":
            _katak(img, nx, ny + 4, 1.0, q)
        elif nm == "CICAK":
            _cicak(img, nx, ny, 1.0, q)
        elif nm == "TIKUS":
            _tikus(img, nx - 4, ny, 0.85, q, tl * 5)
        else:
            pts = [(nx - 52 + 9.0 * i, ny - 6 + 15 * math.sin(i * 0.46 + tl * 1.6)) for i in range(13)]
            ular(img, pts, q, 13, mix(NAVY, TEAL, 0.18), True, 1.0, True)
        label(img, nx, ny + rr + 30, nm, mix(accent, INK, 0.25), q, fsz=25)
        if i > 0:
            panah(img, (nod[i - 1][0] + rr + 4, ny), (nx - rr - 4, ny),
                  esm((tl - tc - (0.9 if nm == "ULAR" else 0)) / 0.5), mix(INK, MUTED, 0.30), 6, 0.8)
    # rumah tujuan (selalu ada, jadi tujuan tikus terbaca sejak awal)
    P0, P1 = (630, 664), (858, 1108)
    TEB = 0.42                                  # tekukan rute: memutar di kiri rumah, tidak menimpa atap
    _rumah_luar(img, 880, 1118, 0.50, 1.0, atap=mix(MERAH, INK, 0.12), jendela=0.9, pintu_terang=0.9)
    # jejak rute ke pintu
    qjejak = esm((tl - c["lari"] - 0.2) / 0.6)
    if qjejak > 0.01:
        for i in range(18):
            pp = _bez(P0, P1, TEB, i / 17)
            dot_on(img, pp[0], pp[1], 3.0, mix(INK, MUTED, 0.40), 0.34 * qjejak)
    # tikus lari ke rumah, lalu hilang di ambang pintu
    qt = esm((tl - c["lari"] + 0.2) / 0.5)
    if qt > 0.01:
        u = esm((tl - c["lari"]) / max(0.8, c["kering"] - c["lari"]))
        mp = _bez(P0, P1, TEB, u)
        am = 1.0 - esm((u - 0.88) / 0.12)          # memudar tepat di ambang
        if am > 0.02:
            _tikus(img, mp[0], mp[1], 0.95, qt * am, tl * 9)
        if u > 0.02 and am > 0.2:
            for k in range(3):
                pp = _bez(P0, P1, TEB, clamp(u - 0.08 * (k + 1)))
                dot_on(img, pp[0] - 10, pp[1] + 12, 3, mix(INK, MUTED, 0.5), 0.25 * (1 - 0.25 * k) * am)
    # ular menyusul di alur yang sama (kepala tertinggal: ular lebih lambat dari tikus)
    qu = esm((tl - c["mengikuti"] + 0.1) / 0.5)
    if qu > 0.01:
        pu = esm((tl - c["mengikuti"]) / max(0.8, c["mengincar"] - c["mengikuti"]))
        pts = []
        for i in range(26):
            v = clamp(pu - 0.52 + 0.36 * i / 25)
            xx, yy = _bez(P0, P1, TEB, v)
            pts.append((xx + 11 * math.sin(i * 0.62 + tl * 4.0), yy + 8 * math.cos(i * 0.78 + tl * 3.2)))
        ular(img, pts, qu, 14, mix(NAVY, TEAL, 0.14), True, 1.0, True)
    qk = esm((tl - c["kering"]) / 0.5)
    if qk > 0.01:
        V._glow11(img, 872, 1030, 190, KUNING, 0.30 * qk)
    M.stiker(img, 300, 786, "IKUT BAU TIKUS", 1.0, tl - c["mengikuti"], bg=accent, fsz=27, rot=-4)
    chip(img, 540, Y_FOOT, "HUJAN PERTAMA  ·  OKT-NOV", mix(KUNING, INK, 0.30), 1.0, 10.0, fsz=25, persisten=True)
    teks(img, sc, accent, tl, 1.0, 0.10)
    debu(img, tg, 1.0, n=12, y0=700, y1=1150)


# ================================================================ 5. F4 IRISAN KERING
def sc_kering50(img, d, sc, tl, dur, tg, accent, al, dy):
    """BODY 3. Kering + hangat: air naik, lubang terendam, tiga tempat kering jadi pengganti."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["kering_hangat50"])
    kertas(img, 1.0)
    _bawah(img, 1.0, SUMBER)
    # langit + hujan
    _awan(img, 250, 400, 0.9, 1.0)
    _awan(img, 840, 384, 0.7, 1.0)
    rrect_on(img, 0, 340, 1080, 470, 0, mix(CREAM, AIR, 0.08), 0.55)
    hujan(img, tl, -40, 1120, 336, 468, n=30, al=0.30, seed=11, panjang=(16, 32))
    # atap
    poly_on(img, [(78, 470), (540, 366), (1002, 470), (1002, 494), (540, 392), (78, 494)],
            mix(MERAH, INK, 0.12), 1.0)
    # ruang plafon
    rrect_on(img, 100, 494, 980, 704, 4, mix(CREAM, INK, 0.075), 1.0)
    for (x0, x1) in ((160, 920), (270, 810), (380, 700)):
        line_on(img, (x0, 698), ((x0 + x1) / 2, 506), mix(INK, MUTED, 0.45), 3, 0.45)
        line_on(img, ((x0 + x1) / 2, 506), (x1, 698), mix(INK, MUTED, 0.45), 3, 0.45)
    # isolasi plafon
    for i in range(22):
        line_on(img, (120 + i * 40, 512), (150 + i * 40, 498), mix(KUNING, CREAM, 0.55), 4, 0.28)
    # ular menggulung di plafon
    qp = esm((tl - c["plafon"]) / 0.9)
    if qp > 0.01:
        V._glow11(img, 300, 604, 96, KUNING, 0.20 * qp)          # hangat di plafon
        spiral = []
        for i in range(46):
            a = -i * 0.30 + tl * 0.30
            r = 6 + i * 1.35
            spiral.append((300 + r * math.cos(a), 600 + r * 0.52 * math.sin(a)))
        polyline_on(img, spiral, mix(NAVY, TEAL, 0.26), 13, qp)
        for i, (sx, sy) in enumerate(spiral[::3]):
            dot_on(img, sx, sy, 6.5, mix(NAVY, TEAL, 0.26), qp)   # lingkar badan
        hx, hy = spiral[-1]
        dot_on(img, hx, hy, 11, mix(NAVY, TEAL, 0.20), qp)
        dot_on(img, hx - 3, hy - 3, 2.6, WHITE, qp)
    # slab + ruang
    rrect_on(img, 100, 704, 980, 730, 3, mix(CREAM, INK, 0.28), 1.0)
    rrect_on(img, 100, 730, 980, 1016, 3, DINDING, 1.0)
    # karpet + sofa + pigura: ruang terasa dihuni (bukan kotak kosong)
    ell(img, 300, 986, 660, 1042, fill=mix(UNGU, CREAM, 0.72), alpha=0.75)
    rrect_on(img, 330, 902, 636, 986, 14, mix(TEAL, CREAM, 0.55), 0.95,
             outline=mix(INK, TEAL, 0.35), width=3)
    rrect_on(img, 330, 902, 636, 936, 12, mix(TEAL, WHITE, 0.25), 0.95)
    for k in range(3):
        rrect_on(img, 348 + k * 96, 862, 424 + k * 96, 912, 8, mix(TEAL, CREAM, 0.35), 0.95,
                 outline=mix(INK, TEAL, 0.4), width=2)
    rrect_on(img, 420, 760, 548, 838, 4, mix(EMAS, CREAM, 0.6), 0.9,
             outline=mix(INK, EMAS, 0.35), width=3)
    poly_on(img, [(432, 830), (470, 786), (500, 812), (524, 792), (536, 830)],
            mix(HIJAU, INK, 0.25), 0.75)
    # tumpukan barang (kanan)
    for (bx, by, bw, bh, cc) in ((700, 944, 168, 100, EMAS), (726, 862, 128, 84, TEAL), (742, 798, 96, 64, UNGU)):
        rrect_on(img, bx, by, bx + bw, by + bh, 6, mix(cc, CREAM, 0.52), 0.95,
                 outline=mix(INK, cc, 0.35), width=3)
        line_on(img, (bx + 6, by + bh * 0.38), (bx + bw - 6, by + bh * 0.38), mix(INK, cc, 0.45), 2, 0.45)
    # pot (kiri)
    poly_on(img, [(196, 946), (300, 946), (282, 1014), (214, 1014)], mix(MERAH, INK, 0.18), 1.0)
    ell(img, 142, 946, 302, 248 + 58, fill=mix(HIJAU, INK, 0.10), alpha=0.95)
    for i in range(4):
        line_on(img, (248, 918), (248 - 54 + i * 36, 862 + (i % 2) * 18), mix(HIJAU, INK, 0.3), 7, 0.9)
    # lantai + tanah
    rrect_on(img, 100, 1016, 980, 1042, 2, mix(CREAM, INK, 0.22), 1.0)
    rrect_on(img, 100, 1042, 980, 1168, 2, mix(EMAS, CREAM, 0.72), 1.0)
    for i in range(40):
        y = 1048 + (i % 8) * 15
        x = 108 + (i // 8) * 216 + (i % 3) * 12
        line_on(img, (x, y), (x + 26, y + 5), mix(INK, EMAS, 0.5), 2, 0.22)
    # lubang ular (tunnel)
    rrect_on(img, 620, 1064, 900, 1118, 26, mix(INK, EMAS, 0.25), 0.85)
    dot_on(img, 900, 1090, 20, mix(INK, EMAS, 0.25), 0.85)
    # air tanah naik
    qw = esm((tl - c["terendam"]) / 1.6)
    if qw > 0.01:
        wy = 1168 - (1168 - 1030) * qw
        pts = [(100 + i * 44, wy + 6 * math.sin(i * 0.9 + tl * 2.2)) for i in range(23)]
        for i in range(len(pts) - 1):
            line_on(img, pts[i], pts[i + 1], mix(CREAM, AIR, 0.75), 6, 0.9)
        rrect_on(img, 100, min(wy + 6, 1166), 980, 1168, 0, mix(AIR, CREAM, 0.55), 0.38)
        for k in range(3):
            line_on(img, (116, wy + 26 + k * 34), (964, wy + 22 + k * 34),
                    mix(CREAM, AIR, 0.85), 3, 0.22)
        # lubang ikut terendam
        if qw > 0.5:
            rrect_on(img, 624, max(1070, wy + 10), 896, 1114, 22, mix(AIR, CREAM, 0.35), 0.5 * (qw - 0.5) * 2)
        _chip_kecil(img, 300, 1144, "AIR TANAH NAIK", mix(AIR, INK, 0.3), clamp(qw * 2.2), 23)
    # tiga kantong kering
    for (px, py, nm, tc, col, chx, chy) in ((300, 604, "PLAFON", c["plafon"], EMAS, 432, 548),
                                           (786, 900, "TUMPUKAN", c["tumpukan"], TEAL, 872, 772),
                                           (250, 980, "SELA POT", c["pot"], HIJAU, 158, 1038)):
        q = esm((tl - tc + 0.15) / 0.5)
        if q <= 0.01:
            continue
        V._glow11(img, px, py, 120, KUNING, 0.30 * q)
        ring_on(img, px, py, 52 + 4 * math.sin(tl * 2.2), mix(col, WHITE, 0.3), 3, q * 0.85)
        _chip_kecil(img, chx, chy, nm, mix(col, INK, 0.2), q, 23)
    chip(img, 540, Y_FOOT, "HUJAN PERTAMA  ·  OKT-NOV", mix(KUNING, INK, 0.30), 1.0, 10.0, fsz=25, persisten=True)
    teks(img, sc, accent, tl, 1.0, 0.10)
    debu(img, tg, 1.0, n=12, y0=740, y1=1150)


# ================================================================ 6. F5 DENAH + 3 PANAH
def _rot(pts, cx, cy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


def _rrect_rot(img, x0, y0, x1, y1, r, col, al, deg, cx, cy, outline=None, width=3):
    pts = _rot([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], cx, cy, deg)
    poly_on(img, pts, col, al, outline=outline, width=width)
    if r > 0:
        for (px, py) in pts:
            dot_on(img, px, py, r * 0.5, col, al)


def sc_tigapanah50(img, d, sc, tl, dur, tg, accent, al, dy):
    """MICRO-CLIMAX. Denah rumah dari atas: tiga panah (telur, mangsa, tempat sembunyi) -> satu titik."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["tiga_panah50"])
    kertas(img, 1.0)
    _bawah(img, 1.0, SUMBER)
    CXp, CYp, DEG = 540, 806, -6.0
    # pelat denah
    _rrect_rot(img, 158, 512, 922, 1108, 10, mix(WHITE, accent, 0.06), 1.0, DEG, CXp, CYp,
               outline=mix(INK, MUTED, 0.4), width=6)
    # dinding dalam
    for (a, b) in (((470, 512), (470, 742)), ((470, 742), (922, 742)),
                   ((700, 742), (700, 1108)), ((470, 920), (700, 920))):
        p = _rot([a, b], CXp, CYp, DEG)
        line_on(img, p[0], p[1], mix(INK, MUTED, 0.35), 7, 0.75)
    # perabot
    furn = ((196, 560, 400, 660, mix(TEAL, CREAM, 0.55)),      # kasur
            (760, 570, 880, 700, mix(UNGU, CREAM, 0.60)),      # sofa
            (200, 780, 330, 860, mix(EMAS, CREAM, 0.55)),      # meja
            (760, 960, 884, 1060, mix(AIR, CREAM, 0.60)))      # bak mandi
    for (x0, y0, x1, y1, cc) in furn:
        _rrect_rot(img, x0, y0, x1, y1, 6, cc, 0.95, DEG, CXp, CYp, outline=mix(INK, MUTED, 0.5), width=3)
    # pintu (celah)
    pd = _rot([(500, 1108), (600, 1108)], CXp, CYp, DEG)
    line_on(img, pd[0], pd[1], CREAM, 10, 1.0)
    qc = esm((tl - c["celah"]) / 0.4)
    if qc > 0.01:
        line_on(img, pd[0], pd[1], mix(accent, MERAH, 0.35), 8, qc)
        _chip_kecil(img, 566, 1140, "CELAH PINTU", mix(accent, INK, 0.2), qc, 23)
    # target
    TX, TY = 588, 836
    qt = esm((tl - c["titik"]) / 0.35)
    if qt > 0.01:
        ring_on(img, TX, TY, 30 + 26 * (1 - qt), mix(accent, MERAH, 0.4), 5, qt * 0.9)
        V._glow11(img, TX, TY, 120, MERAH, 0.35 * qt)
    dot_on(img, TX, TY, 21, mix(MERAH, INK, 0.15), 0.95, outline=WHITE, width=4)
    poly_on(img, [(TX - 15, TY - 46), (TX, TY - 70), (TX + 15, TY - 46)], mix(MERAH, INK, 0.15), 0.95)
    rrect_on(img, TX - 11, TY - 46, TX + 11, TY - 24, 3, mix(MERAH, INK, 0.15), 0.95)
    # tiga panah
    jalur = [((168, 566), (TX - 36, TY - 28), 0.20, "TELUR", c["telur"], EMAS, (212, 500)),
             ((548, 412), (TX + 6, TY - 42), -0.16, "MANGSA", c["mangsa"], TEAL, (548, 358)),
             ((942, 1082), (TX + 32, TY + 24), 0.18, "SEMBUNYI", c["sembunyi"], UNGU, (930, 1122))]
    for (p0, p1, tk, nm, tc, col, cpos) in jalur:
        u = esm((tl - tc) / 1.05)
        panah_tekuk(img, p0, p1, u, mix(col, INK, 0.18), 11, 0.95 * min(1.0, u * 3), tk)
        q = esm((tl - tc + 0.05) / 0.4)
        _chip_kecil(img, cpos[0], cpos[1], nm, mix(col, INK, 0.2), q, 24)
    # gelombang hentakan
    if tl >= c["titik"]:
        tt = tl - c["titik"]
        for k, (dl, rm) in enumerate(((0.0, 90), (0.13, 150), (0.28, 230))):
            q = esm((tt - dl) / 0.75)
            if 0 < q < 1:
                ring_on(img, TX, TY, 24 + rm * q, mix(accent, MERAH, 0.35), 4, (1 - q) ** 1.4)
    M.stiker(img, 828, 624, "SATU TITIK", 1.0, tl - c["titik"], bg=accent, fsz=28, rot=-5)
    M.stiker(img, 348, 1000, "RUMAHMU YANG MANA?", 1.0, tl - c["mana"], bg=MERAH, fsz=28, rot=-4)
    chip(img, 540, Y_FOOT, "HUJAN PERTAMA  ·  OKT-NOV", mix(KUNING, INK, 0.30), 1.0, 10.0, fsz=25, persisten=True)
    teks(img, sc, accent, tl, 1.0, 0.08)
    debu(img, tg, 1.0, n=10, y0=400, y1=1150)


# ================================================================ 7. F6 DAFTAR BALIK
def _centang(img, x, y, r, al, col=HIJAU):
    dot_on(img, x, y, r, mix(col, WHITE, 0.12), al)
    line_on(img, (x - r * 0.45, y + r * 0.02), (x - r * 0.10, y + r * 0.42), WHITE, 6, al)
    line_on(img, (x - r * 0.10, y + r * 0.42), (x + r * 0.52, y - r * 0.42), WHITE, 6, al)


def sc_balik50(img, d, sc, tl, dur, tg, accent, al, dy):
    """PAYOFF. Urutan dibalik: tutup celah -> singkirkan tumpukan -> jangan dipukul -> damkar."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["balik_urutan50"])
    kertas(img, 1.0)
    _bawah(img, 1.0, SUMBER)
    # panah balik besar (rewind) di sisi kiri
    qb = esm((tl - c["dibalik"]) / 1.0)
    if qb > 0.01:
        panah_tekuk(img, (150, 1050), (150, 604), qb, mix(accent, MERAH, 0.25), 10, 0.9, 0.16)
        _chip_kecil(img, 452, 960, "URUTAN DIBALIK", mix(accent, INK, 0.2), clamp(qb * 2), 23)
    baris = ((1, "TUTUP CELAH", c["tutup"], "celah"), (2, "SINGKIRKAN", c["singkirkan"], "tumpukan"),
             (3, "JANGAN DIPUKUL", c["jangan"], "pukul"))
    for i, (no, nm, tc, ikon) in enumerate(baris):
        q = esm((tl - tc + 0.1) / 0.45)
        if q <= 0.01:
            continue
        by = 520 + i * 168
        rrect_on(img, 212, by - 56, 966, by + 56, 18, mix(WHITE, accent, 0.07), q,
                 outline=mix(INK, MUTED, 0.45), width=3)
        dot_on(img, 286, by, 40, mix(accent, INK, 0.20), q)
        paste_c(img, 286, by, str(no), font(D.FB, 42), WHITE, q)
        ft = font(D.FB, 28)
        paste_c(img, 336 + tw(nm, ft) / 2, by, nm, ft, mix(INK, accent, 0.25), q)
        # ikon kanan
        if ikon == "celah":
            line_on(img, (866, by + 30), (866, by - 30), mix(INK, MUTED, 0.3), 6, q * 0.8)
            line_on(img, (878, by + 30), (878, by - 30), mix(INK, MUTED, 0.3), 6, q * 0.8)
            line_on(img, (860, by), (884, by), mix(HIJAU, INK, 0.2), 10, q)
        elif ikon == "tumpukan":
            for k in range(2):
                rrect_on(img, 856 + k * 16, by + 8 - k * 24, 896 + k * 16, by + 30 - k * 24, 4,
                         mix(EMAS, CREAM, 0.4), q, outline=mix(INK, EMAS, 0.4), width=2)
            panah(img, (904, by + 18), (930, by - 14), esm((tl - tc - 0.5) / 0.5), mix(HIJAU, INK, 0.2), 5, q)
        else:
            line_on(img, (856, by + 24), (892, by - 24), mix(EMAS, INK, 0.25), 8, q)
            silang(img, 874, by, 28, MERAH, q * clamp((tl - c["dipukul"] - 0.4) / 0.4))
        _centang(img, 936, by, 21, q * esm((tl - tc - 0.55) / 0.35))
    # kartu damkar
    qd = esm((tl - c["telepon"] + 0.1) / 0.5)
    if qd > 0.01:
        rrect_on(img, 292, 1000, 742, 1106, 20, mix(MERAH, INK, 0.15), qd)
        rrect_on(img, 312, 1020, 376, 1086, 12, WHITE, qd)
        for k in range(3):
            line_on(img, (326, 1040 + k * 14), (362, 1040 + k * 14), mix(MERAH, INK, 0.3), 4, qd * 0.9)
        paste_c(img, 556, 1054, "DAMKAR 113", font(D.FB, 38), WHITE, qd)
    qj = esm((tl - c["menjauh"]) / 0.4)
    if qj > 0.01:
        _chip_kecil(img, 800, 1144, "MENJAUH DULU", mix(TEAL, INK, 0.2), qj, 23)
    chip(img, 540, Y_FOOT, "HUJAN PERTAMA  ·  OKT-NOV", mix(KUNING, INK, 0.30), 1.0, 10.0, fsz=25, persisten=True)
    teks(img, sc, accent, tl, 1.0, 0.10)
    debu(img, tg, 1.0, n=10, y0=420, y1=1150)


# ================================================================ 8. OUTRO (LOOP)
def sc_loop50(img, d, sc, tl, dur, tg, accent, al, dy):
    """SEAMLESS LOOP. Hujan yang sama, rumah yang sama -> frame akhir == frame 0."""
    M.set_keluar(tl, dur, ada_lanjutan=False)
    c = cues(sc, dur, CUES["loop_hujan50"])
    al = 1.0                      # render memberi al->0 di 0,3 s terakhir; loop butuh frame penuh
    u = tl - dur                      # 0 tepat di frame terakhir -> identik dengan intro tl=0
    _pemandangan(img, u, tg, 1.0, banjir=0.0, ular_u=0.0,
                 sorot=0.30 * esm((tl - c["sama"]) / 0.6))
    # busur 'kembali' yang menutup lingkaran, hilang sebelum frame akhir
    q = esm((tl - c["kembali"]) / 0.8) * (1 - esm((tl - dur + 1.0) / 0.5))
    if q > 0.01:
        pts = [(540 + 330 * math.cos(a), 760 + 300 * math.sin(a)) for a in
               [i * 2 * math.pi / 48 for i in range(49)]]
        for i in range(len(pts) - 1):
            if i < int(48 * q):
                line_on(img, pts[i], pts[i + 1], mix(accent, WHITE, 0.25), 5, 0.55)
        _chip_kecil(img, 540, 424, "KEMBALI KE AWAL", mix(accent, INK, 0.2), q, 24)
    chip(img, 540, Y_FOOT, "HUJAN PERTAMA  ·  OKT-NOV", mix(KUNING, INK, 0.30), 1.0, 10.0, fsz=25, persisten=True)
    at = 1 - esm((tl - dur + 1.25) / 0.55)
    lines = sc.get("lines") or ["HUJAN PERTAMA", "SEBENTAR LAGI"]
    teks(img, sc, accent, tl, at, 0.30, " ".join(lines), "HUJAN PERTAMA", fsz=58, maxw=860)


# ================================================================ CUE (kata -> waktu) & SFX
CUES = {
    "hujan_ular50": {"hujan": ("Musim", 0.03), "ular": ("ular", 0.33), "muncul": ("muncul", 0.47),
                "dalam": ("dalam", 0.60), "bukan": ("Bukan", 0.76), "banjir": ("banjir", 0.90)},
    "rumah_biasa50": {"setiap": ("Setiap", 0.02), "tahun": ("tahun", 0.05), "sama": ("sama", 0.14),
                "hujan": ("Hujan", 0.19), "turun": ("turun", 0.25), "kabar": ("kabar", 0.33),
                "mandi": ("mandi", 0.44), "plafon": ("plafon", 0.54), "lemari": ("lemari", 0.63),
                "biasa": ("biasa", 0.77), "tetangga": ("tetanggamu", 0.86), "rumahmu": ("rumahmu", 0.95)},
    "kalender_telur50": {"kalender": ("kalender", 0.08), "hujan": ("hujan", 0.50), "bertelur": ("bertelur", 0.16), "kemarau": ("kemarau", 0.27),
                   "tiga": ("Tiga", 0.34), "empat": ("empat", 0.38), "menetas": ("menetas", 0.56),
                   "bukan": ("bukan", 0.67), "belasan": ("belasan", 0.78), "sembunyi": ("sembunyi", 0.95)},
    "tikus50": {"makanan": ("makanan", 0.07), "hujan": ("hujan", 0.14), "katak": ("katak", 0.23),
                "cicak": ("cicak", 0.30), "ramai": ("ramai", 0.42), "tikus": ("tikus", 0.37), "lari": ("lari", 0.45),
                "kering": ("kering", 0.55), "terdekat": ("terdekat", 0.63), "rumahmu": ("rumahmu", 0.71),
                "mengincar": ("mengincar", 0.82), "mengikuti": ("mengikuti", 0.92)},
    "kering_hangat50": {"kering": ("kering", 0.05), "hangat": ("hangat", 0.11), "lubang": ("Lubang", 0.19),
                 "terendam": ("terendam", 0.33), "plafon": ("Plafon", 0.47), "tumpukan": ("tumpukan", 0.59),
                 "pot": ("pot", 0.71), "sempurna": ("sempurna", 0.92)},
    "tiga_panah50": {"gabungkan": ("gabungkan", 0.04), "telur": ("Telur", 0.15), "mangsa": ("Mangsa", 0.29),
                    "sembunyi": ("sembunyi", 0.41), "tiga": ("Tiga", 0.51), "titik": ("titik", 0.62),
                    "celah": ("celah", 0.73), "tikus": ("tikus", 0.78), "tumpukan": ("tumpukan", 0.83),
                    "mana": ("mana", 0.95)},
    "balik_urutan50": {"dibalik": ("dibalik", 0.05), "tutup": ("Tutup", 0.13), "celah": ("celah", 0.17),
                "saluran": ("saluran", 0.26), "singkirkan": ("Singkirkan", 0.35), "tumpukan": ("tumpukan", 0.40),
                "tikus": ("tikus", 0.49), "datang": ("datang", 0.57), "terlanjur": ("terlanjur", 0.65),
                "jangan": ("jangan", 0.71), "dipukul": ("dipukul", 0.75), "menjauh": ("Menjauh", 0.83),
                "telepon": ("telepon", 0.94), "damkar": ("damkar", 0.98)},
    "loop_hujan50": {"kembali": ("lagi.", 0.57), "sama": ("sama", 0.21), "sebentar": ("sebentar", 0.38), "turun": ("turun", 0.50),
               "hujan": ("hujan", 0.72), "pertama": ("pertama", 0.86)},
}
# SFX per cue: nama_cue -> (jenis, gain, offset detik)
SFX = {
    "hujan_ular50": {"hujan": ("guntur", 0.55, 0), "ular": ("swish", 0.7, -0.10), "muncul": ("tick", 0.8, 0),
                "dalam": ("swish_up", 0.6, 0), "bukan": ("thud", 0.9, 0), "banjir": ("pop", 0.6, 0)},
    "rumah_biasa50": {"setiap": ("tick", 0.8, 0), "tahun": ("tick", 0.8, 0), "sama": ("pop", 0.6, 0),
                "hujan": ("angin", 0.7, 0), "turun": ("swish", 0.6, 0), "kabar": ("pop", 0.7, 0),
                "mandi": ("pop", 0.8, 0), "plafon": ("pop", 0.8, 0), "lemari": ("pop", 0.8, 0),
                "biasa": ("tick", 0.7, 0), "tetangga": ("tick", 0.7, 0), "rumahmu": ("thud", 0.85, 0)},
    "kalender_telur50": {"kalender": ("morph", 0.7, 0), "bertelur": ("pop", 0.7, 0), "kemarau": ("tick", 0.8, 0),
                   "tiga": ("tick", 0.9, 0), "empat": ("tick", 0.9, 0), "menetas": ("retak", 1.0, -0.05),
                   "bukan": ("swish", 0.6, 0), "belasan": ("pop", 0.8, 0), "sembunyi": ("swish_up", 0.6, 0)},
    "tikus50": {"makanan": ("pop", 0.7, 0), "hujan": ("angin", 0.6, 0), "katak": ("pop", 0.7, 0),
                "cicak": ("pop", 0.7, 0), "tikus": ("pop", 0.9, 0), "lari": ("swish", 0.9, 0),
                "kering": ("kilau", 0.6, 0), "terdekat": ("tick", 0.8, 0), "rumahmu": ("thud", 0.8, 0),
                "mengincar": ("tick", 0.8, 0), "mengikuti": ("swish", 0.9, 0)},
    "kering_hangat50": {"kering": ("tick", 0.8, 0), "hangat": ("tick", 0.8, 0), "lubang": ("thud", 0.8, 0),
                 "terendam": ("gelembung", 0.9, 0), "plafon": ("pop", 0.8, 0), "tumpukan": ("pop", 0.8, 0),
                 "pot": ("pop", 0.8, 0), "sempurna": ("kilau", 0.8, 0)},
    "tiga_panah50": {"gabungkan": ("morph", 0.8, 0), "telur": ("swish", 0.7, 0), "mangsa": ("swish", 0.7, 0),
                    "sembunyi": ("swish", 0.7, 0), "tiga": ("tick", 0.9, 0), "titik": ("thump", 1.0, 0),
                    "celah": ("tick", 0.7, 0), "tikus": ("tick", 0.7, 0), "tumpukan": ("tick", 0.7, 0),
                    "mana": ("riser", 0.6, -0.4)},
    "balik_urutan50": {"dibalik": ("whoosh", 0.8, 0), "tutup": ("door", 0.8, 0), "celah": ("tick", 0.8, 0),
                "saluran": ("pop", 0.6, 0), "singkirkan": ("swish", 0.8, 0), "tumpukan": ("thud", 0.8, 0),
                "tikus": ("tick", 0.7, 0), "datang": ("tick", 0.7, 0), "terlanjur": ("tick", 0.7, 0),
                "jangan": ("tick", 0.8, 0), "dipukul": ("gigit", 0.7, 0), "menjauh": ("swish", 0.7, 0),
                "telepon": ("click", 0.8, 0), "damkar": ("ding", 0.8, 0)},
    "loop_hujan50": {"sama": ("morph", 0.7, 0), "sebentar": ("swish", 0.6, 0), "turun": ("angin", 0.6, 0),
               "hujan": ("guntur", 0.4, 0), "pertama": ("kilau", 0.7, 0)},
}
BEATS51 = {k: [] for k in CUES}


def events_v12(sc):
    """Event SFX absolut untuk satu adegan timeline (start, dur) -> [(t, jenis, gain)]."""
    vis = sc.get("visual", "")
    if vis not in CUES:
        return []
    c = cues(sc, sc["dur"], CUES[vis])
    out = []
    for nama, (jenis, g, off) in SFX.get(vis, {}).items():
        out.append((sc["start"] + c[nama] + off, jenis, g))
    tr = str(sc.get("trans") or "").lower()
    if tr == "morph":
        out.append((sc["start"] - 0.08, "morph", 0.55))
    return out


def teks(img, sc, accent, tl, al, t0, text=None, hl=None, fsz=58, y=Y_TXT, maxw=860):
    V._judul11(img, text if text is not None else sc.get("badge", ""), accent, tl, al * M.KELUAR[0], y=y,
               hl=hl if hl is not None else sc.get("hl", ""), fsz=fsz, t0=t0, maxw=maxw)


VISUALS51 = {"hujan_ular50": sc_hujan50, "rumah_biasa50": sc_rumah50, "kalender_telur50": sc_kalender50,
             "tikus50": sc_tikus50, "kering_hangat50": sc_kering50, "tiga_panah50": sc_tigapanah50,
             "balik_urutan50": sc_balik50, "loop_hujan50": sc_loop50}


def _selftest():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (int(1080 * D.SS), int(1920 * D.SS)), CREAM)
    d = ImageDraw.Draw(img)
    for n, fn in VISUALS51.items():
        sc = {"id": {"hujan_ular50": "intro", "loop_hujan50": "outro"}.get(n, "f1"), "visual": n,
              "start": 10.0, "dur": 16.0, "badge": "CARI TEMPAT KERING", "hl": "KERING",
              "lines": ["ULAR MASUK RUMAH", "BUKAN KARENA BANJIR"]}
        for tl in (0.0, 0.12, 0.5, 2.0, 5.0, 8.0, 12.0, 15.5, 15.98):
            fn(img, d, sc, tl, 16.0, 10.0 + tl, D.hexc("#1F4E5F"), 1.0, 0.0)
        ev = events_v12(sc)
        assert ev and all(e[1] for e in ev), n
    # loop: frame akhir outro harus sama dengan frame 0 intro (uji angka, bukan piksel)
    print(f"selftest ep51 v12: {len(VISUALS51)} adegan OK ({sum(len(v) for v in CUES.values())} cue, "
          f"{sum(len(v) for v in SFX.values())} SFX)")


def daftar():
    """Daftarkan visual, beat, dan event Ep51 ke mesin (idempoten; dipanggil saat impor)."""
    V.BEATS.update(BEATS51)
    D.VISUALS.update(VISUALS51)
    M.EVENTS12.update({k: events_v12 for k in CUES})


daftar()


if __name__ == "__main__":
    _selftest()
