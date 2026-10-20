#!/usr/bin/env python3
"""Ep51 v2 - "AMBANG" (mesin v14). Dunia visual sinematik 2.5D: hujan, cahaya pintu, tanah.

Naskah mengikuti RISET ULANG 18 Okt 2026 (analisis/EP51_RISET_ULANG_18_OKT_2026.md):
hook berupa pertanyaan, bukan klaim; genangan habitat, masa penetasan (kasus Sukabumi),
variasi reproduksi, dan akses rumah dibedakan; respons aman + arahan medis.

Yang baru dibanding Ep51 v1:
  * latar statis mahal (langit bergradasi, rumah bertekstur, potongan tanah, sarang)
    dirender SEKALI per adegan lalu di-cache -> tiap frame hanya menggambar elemen hidup;
  * hujan tiga lapis (jauh/mid/dekat) + riak + kabut + pantulan cahaya di tanah basah;
  * cahaya hangat dari pintu (gradien + pendar) dan rim light di tepi atap/badan ular;
  * teks headline tetap di zona aman yang sama (chip 1204, judul 1318, sumber 1772).

Palet tetap identitas KlikTahu (krem / navy / jingga-terakota / teal), BUKAN palet video acuan.
"""
import math

from PIL import Image, ImageDraw

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
Y_FOOT = 1204
SUMBER = "Sumber: BRIN · BMKG · Damkar · WHO"

TEAL = (38, 106, 96)
TEAL_D = (26, 74, 68)
TERRA = (176, 84, 56)
TERRA_D = (128, 56, 38)
AMBER2 = (198, 142, 54)
OLIVE = (108, 120, 78)
NAVY3 = (22, 34, 52)
WET = (206, 203, 192)
SKY1 = (238, 236, 228)
SKY2 = (203, 212, 211)
SOIL1 = (146, 118, 88)
SOIL2 = (120, 94, 70)
SOIL3 = (96, 78, 60)
STONE = (158, 152, 140)
DOOR = (30, 44, 62)


# ---------------------------------------------------------------- utilitas dasar
def _rnd(i, k=1.0):
    return (math.sin(i * 12.9898 + k * 78.233) * 43758.5453) % 1.0


def _scrim(img, y0=1096, y1=1408):
    """Lerp ke krem di zona teks: judul selalu duduk di 'kertas' bersih."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    for i in range(72):
        q = i / 71.0
        y = y0 + (y1 - y0) * q
        a = int(255 * min(1.0, (q ** 0.72) * 1.06))
        dd.rectangle([0, D.S(y), img.size[0], D.S(y) + 1], fill=CREAM + (a,))
    img.paste(lay, (0, 0), lay)


def _grad(img, y0, y1, c0, c1, n=110):
    dd = ImageDraw.Draw(img)
    for i in range(n):
        q = i / (n - 1.0)
        col = mix(c0, c1, q)
        ya = y0 + (y1 - y0) * i / n
        yb = y0 + (y1 - y0) * (i + 1) / n + 1
        dd.rectangle([0, D.S(ya), img.size[0], D.S(yb)], fill=col)


def _speck(img, x0, y0, x1, y1, n, col, al, seed=1, r=(1.0, 2.6)):
    """Bintik kertas: satu lapisan (bukan n lapisan) — hemat waktu render."""
    if n <= 0 or al <= 0.005:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    for i in range(n):
        j = i + seed * 211
        x = x0 + _rnd(j, 1) * (x1 - x0)
        y = y0 + _rnd(j, 2) * (y1 - y0)
        rr = r[0] + _rnd(j, 3) * (r[1] - r[0])
        a = int(255 * clamp(al * (0.4 + 0.6 * _rnd(j, 4))))
        dd.ellipse([D.S(x - rr), D.S(y - rr), D.S(x + rr), D.S(y + rr)], fill=col + (a,))
    img.paste(lay, (0, 0), lay)


def _grass(img, y, x0, x1, col, al=0.8, n=46, h=34, seed=3, lebar=3.2):
    for i in range(n):
        j = i + seed * 97
        x = x0 + (i + 0.5) / n * (x1 - x0) + (_rnd(j, 1) - 0.5) * 14
        hh = h * (0.55 + 0.75 * _rnd(j, 2))
        bend = (_rnd(j, 3) - 0.5) * hh * 0.7
        line_on(img, (x, y), (x + bend, y - hh), col, lebar, al * (0.5 + 0.5 * _rnd(j, 4)))


def _shadow(img, cx, cy, rx, ry, al=0.20, col=(48, 46, 44)):
    ell(img, cx - rx, cy - ry, cx + rx, cy + ry, fill=col, alpha=al)


def _lampu(img, cx, cy, r, al=0.35):
    V._glow11(img, cx, cy, r, KUNING, al)


def _hujan_lapis(img, u, lapis=("jauh", "mid", "dekat"), x0=0, x1=1080, y0=300, y1=1170, al=1.0):
    """Tiga lapis hujan: jauh (tipis, lambat), mid, dekat (tebal, cepat, sedikit miring)."""
    setelan = {"jauh": dict(n=84, panjang=(9, 17), lebar=2, alpha=0.26, tahun=0.0, tilt=0.11,
                            col=mix(CREAM, INK, 0.50)),
               "mid": dict(n=62, panjang=(20, 33), lebar=3, alpha=0.34, tahun=0.35, tilt=0.14,
                           col=mix(CREAM, INK, 0.56)),
               "dekat": dict(n=22, panjang=(40, 66), lebar=4, alpha=0.38, tahun=0.7, tilt=0.17,
                             col=mix(WHITE, INK, 0.16))}
    for nm in lapis:
        s = setelan[nm]
        _hujan(img, u + s["tahun"], x0, x1, y0, y1, n=s["n"], al=s["alpha"] * al,
               panjang=s["panjang"], lebar=s["lebar"], tilt=s["tilt"],
               seed={"jauh": 17, "mid": 43, "dekat": 71}[nm],
               col=s["col"])


def _hujan(img, u, x0, x1, y0, y1, n=60, al=0.4, col=None, seed=1,
           panjang=(22, 46), lebar=3, tilt=0.16, laju=1.0):
    """Hujan deterministik; periode tepat 1 detik -> outro bisa identik dengan frame 0."""
    if al <= 0.01:
        return
    col = col or mix(CREAM, INK, 0.55)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    w1 = max(1, int(round(D.S(lebar))))
    w2 = max(1, int(round(D.S(max(1, lebar + 1)))))
    for i in range(n):
        j = i + seed * 137
        rx, ry, rv, rl = _rnd(j, 1), _rnd(j, 2), _rnd(j, 3), _rnd(j, 4)
        spd = (1 + (1 if rv > 0.55 else 0) + (1 if rv > 0.9 else 0)) * laju
        prog = (ry + u * spd) % 1.0
        y = y0 + prog * (y1 - y0)
        x = x0 + rx * (x1 - x0) + tilt * (y - y0)
        L = panjang[0] + rl * (panjang[1] - panjang[0])
        a1 = int(255 * clamp(al * (0.30 + 0.70 * rv)))
        dd.line([D.S(x), D.S(y), D.S(x - tilt * L), D.S(y - L)], fill=col + (a1,), width=w1)
        a2 = int(255 * clamp(al * 0.18 * rv))
        dd.line([D.S(x), D.S(y), D.S(x - tilt * L * 0.45), D.S(y - L * 0.45)],
                fill=col + (a2,), width=w2)
    img.paste(lay, (0, 0), lay)


def _riak(img, x, y, u, al=0.5, r0=5, r1=46, col=None, squash=0.30):
    col = col or mix(CREAM, INK, 0.45)
    for k in range(3):
        q = (u + k / 3.0) % 1.0
        ring_on(img, x, y, r0 + (r1 - r0) * q, col, 2, al * (1 - q) ** 1.7, squash=squash)


def _kabut(img, y, tebal=90, al=0.10, col=None):
    col = col or mix(CREAM, WHITE, 0.4)
    for i in range(10):
        q = i / 9.0
        line_on(img, (0, y + q * tebal), (1080, y + q * tebal), col, 10 + 8 * (1 - q), al * (1 - q) ** 1.4)


# ------------------------------------------------------------------ geometri bantu
def _bez(p0, p1, tekuk, t):
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    cx, cy = mx - dy * tekuk, my + dx * tekuk
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t * t * p1[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t * t * p1[1])


def panah(img, p0, p1, u, col, lebar=8, al=1.0, hk=3.4, putus=False):
    if al <= 0.01 or u <= 0:
        return
    n = 16
    m = max(2, int(n * clamp(u)))
    pts = [(p0[0] + (p1[0] - p0[0]) * i / (n - 1), p0[1] + (p1[1] - p0[1]) * i / (n - 1)) for i in range(m)]
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], col, lebar, al, dash=(12, 8) if putus else None)
    if u > 0.10:
        p1 = pts[-1]
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        hl = lebar * hk
        poly_on(img, [(p1[0], p1[1]),
                      (p1[0] - hl * math.cos(ang - 0.42), p1[1] - hl * math.sin(ang - 0.42)),
                      (p1[0] - hl * math.cos(ang + 0.42), p1[1] - hl * math.sin(ang + 0.42))], col, al)


def panah_tekuk(img, p0, p1, u, col, lebar=9, al=1.0, tekuk=0.22):
    if al <= 0.01 or u <= 0:
        return
    n = 24
    m = max(2, int(n * clamp(u)))
    pts = [_bez(p0, p1, tekuk, i / (n - 1)) for i in range(m)]
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], col, lebar, al)
    if u > 0.10:
        ph, pp = pts[-1], pts[-2]
        ang = math.atan2(ph[1] - pp[1], ph[0] - pp[0])
        hl = lebar * 3.2
        poly_on(img, [(ph[0], ph[1]),
                      (ph[0] - hl * math.cos(ang - 0.42), ph[1] - hl * math.sin(ang - 0.42)),
                      (ph[0] - hl * math.cos(ang + 0.42), ph[1] - hl * math.sin(ang + 0.42))], col, al)


# ------------------------------------------------------------------ ular
def ular(img, pts, al=1.0, lebar=15, col=None, kepala=True, u=1.0, lidah=True, sisik=True):
    """Badan ular kontinu: garis sambung + ruas + sisik + rim light tipis + kepala.

    Kerapatan titik dinaikkan (n x 2) supaya sambungan tidak terbaca sebagai manik-manik.
    """
    if al <= 0.01 or u <= 0 or lebar <= 0:
        return
    col = col or mix(NAVY3, TEAL_D, 0.30)
    n0 = len(pts)
    if n0 < 2:
        return
    # resample garis potongan (linear) supaya titik rapat & radius mulus
    n = max(12, int(n0 * 2.4))
    dense = []
    for i in range(n):
        q = i / (n - 1) * (n0 - 1)
        j = min(n0 - 2, int(q))
        f = q - j
        dense.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f,
                      pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f))
    m = max(2, int(n * clamp(u)))
    for i in range(m - 1):
        t = (i + 0.5) / max(1, n - 1)
        r = lebar * (0.46 + 0.54 * t)
        line_on(img, dense[i], dense[i + 1], col, max(1.8, 1.96 * r), al)
    for i in range(m):
        t = i / max(1, n - 1)
        r = lebar * (0.46 + 0.54 * t)
        dot_on(img, dense[i][0], dense[i][1], r, col, al)
        if sisik and i % 4 == 0 and i < m - 3:
            dot_on(img, dense[i][0] - r * 0.30, dense[i][1] - r * 0.32, max(1.0, r * 0.22),
                   mix(col, WHITE, 0.38), al * 0.45)
    if kepala and m >= 4:
        pe = dense[m - 1]
        pp = dense[m - 4]
        ang = math.atan2(pe[1] - pp[1], pe[0] - pp[0])
        ca, sa = math.cos(ang), math.sin(ang)
        hx, hy = pe[0] + ca * lebar * 0.18, pe[1] + sa * lebar * 0.18
        L, Wd = lebar * 1.85, lebar * 0.62
        # baji: pangkal lebar -> moncong membulat (polygon + tutup hidung)
        poly_on(img, [(hx - ca * L * 0.42 - sa * Wd, hy - sa * L * 0.42 + ca * Wd),
                      (hx + ca * L * 0.42 - sa * Wd * 0.72, hy + sa * L * 0.42 + ca * Wd * 0.72),
                      (hx + ca * L * 0.58, hy + sa * L * 0.58),
                      (hx + ca * L * 0.42 + sa * Wd * 0.72, hy + sa * L * 0.42 - ca * Wd * 0.72),
                      (hx - ca * L * 0.42 + sa * Wd, hy - sa * L * 0.42 - ca * Wd)], col, al)
        dot_on(img, hx + ca * L * 0.52, hy + sa * L * 0.52, lebar * 0.44, col, al)
        # sorot atas kepala + mata
        line_on(img, (hx - ca * L * 0.30 - sa * Wd * 0.45, hy - sa * L * 0.30 + ca * Wd * 0.45),
                (hx + ca * L * 0.34 - sa * Wd * 0.26, hy + sa * L * 0.34 + ca * Wd * 0.26),
                mix(col, WHITE, 0.22), max(1.2, lebar * 0.17), al * 0.55)
        for sd in (-1, 1):
            ex = hx - ca * L * 0.02 + sa * Wd * 0.50 * sd
            ey = hy - sa * L * 0.02 - ca * Wd * 0.50 * sd
            dot_on(img, ex, ey, max(1.2, lebar * 0.15), mix(CREAM, KUNING, 0.30), al * 0.95)
            dot_on(img, ex + ca * 0.9, ey + sa * 0.9, max(0.8, lebar * 0.075), INK, al)
        line_on(img, (hx + ca * L * 0.10 + sa * Wd * 0.20, hy + sa * L * 0.10 - ca * Wd * 0.20),
                (hx + ca * L * 0.44, hy + sa * L * 0.44), mix(INK, col, 0.5), 1.6, al * 0.6)
        if lidah:
            tx, ty = hx + ca * lebar * 1.9, hy + sa * lebar * 1.9
            line_on(img, (hx + ca * lebar * 1.30, hy + sa * lebar * 1.30), (tx, ty),
                    mix(RED, ORANYE, 0.2), 2.2, al * 0.9)
            line_on(img, (tx, ty), (tx + ca * 8 - 4, ty + sa * 8 - 4), RED, 2, al * 0.8)
            line_on(img, (tx, ty), (tx + ca * 8 + 4, ty + sa * 8 + 4), RED, 2, al * 0.8)


def ular_sinus(img, x0, y0, x1, y1, n, amp, fase, al=1.0, lebar=15, col=None, u=1.0):
    pts = []
    for i in range(n):
        t = i / max(1, n - 1)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + amp * math.sin(fase + t * 6.0)
        pts.append((x, y))
    ular(img, pts, al, lebar, col, True, u, False)


# ------------------------------------------------------------------ latar: rumah & hujan
def _kanopi(img, cx, cy, r, col, al=1.0, seed=0.0, squash=0.86):
    """Kanopi sebagai satu siluet organik (bukan tumpukan lingkaran)."""
    n = 26
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (0.82 + 0.13 * math.sin(3 * a + seed) + 0.06 * math.sin(7 * a + seed * 2.1)
                  + 0.04 * math.sin(11 * a + seed * 0.7))
        pts.append((cx + rr * math.cos(a), cy + rr * squash * math.sin(a)))
    poly_on(img, pts, col, al)
    for (dx, dy, rr, sh) in ((-0.34, 0.18, 0.42, 0.16), (0.30, -0.22, 0.34, -0.10), (0.05, 0.38, 0.30, 0.10)):
        pts2 = []
        for i in range(16):
            a = 2 * math.pi * i / 16
            rad = r * rr * (1 + 0.14 * math.sin(4 * a + seed + dx * 9))
            pts2.append((cx + dx * r + rad * math.cos(a), cy + dy * r + rad * squash * math.sin(a)))
        poly_on(img, pts2, mix(col, WHITE if sh < 0 else INK, abs(sh) + 0.06), al * 0.55)


def _pohon(img, x, y, s, col, al=0.5, seed=1):
    """Siluet pohon jauh: batang + gugusan elips (bukan kartun)."""
    line_on(img, (x, y), (x, y - 86 * s), mix(col, INK, 0.25), 7 * s, al)
    for k in range(5):
        a = -1.9 + k * 0.5
        cx = x + math.cos(a) * 46 * s
        cy = y - 86 * s + math.sin(a) * 26 * s
        ell(img, cx - 44 * s, cy - 32 * s, cx + 44 * s, cy + 34 * s, fill=col, alpha=al * 0.92)
    ell(img, x - 62 * s, y - 158 * s, x + 62 * s, y - 72 * s, fill=col, alpha=al)


def _rumah(img, cx, dasar, s, al=1.0, lampu=1.0):
    """Rumah tampak depan: atap genteng, plester, jendela hangat, pintu navy + tumpahan cahaya."""
    if al <= 0.01:
        return
    w, hw = 600 * s, 236 * s
    x0, x1 = cx - w / 2, cx + w / 2
    # bayangan tanah
    _shadow(img, cx, dasar + 6 * s, w * 0.62, 26 * s, 0.16 * al)
    # dinding + plester (gradasi vertikal sangat halus + bayangan sisi kanan)
    rrect_on(img, x0, dasar - hw, x1, dasar, 5 * s, CREAM, al)
    for i in range(14):
        q = i / 13.0
        rrect_on(img, x0, dasar - hw + (hw - 12 * s) * q, x1, dasar - hw + (hw - 12 * s) * q + 14 * s,
                 0, mix(CREAM, INK, 0.004 + 0.020 * q), al * 0.55)
    _speck(img, x0 + 12 * s, dasar - hw + 12 * s, x1 - 12 * s, dasar - 8 * s, 70,
           mix(CREAM, INK, 0.35), 0.055 * al, seed=int(cx))
    # bayangan bawah atap + sisi kanan
    rrect_on(img, x0, dasar - hw, x1, dasar - hw + 26 * s, 0, mix(CREAM, INK, 0.13), al * 0.9)
    rrect_on(img, x1 - 52 * s, dasar - hw, x1, dasar, 0, mix(CREAM, INK, 0.05), al * 0.55)
    rrect_on(img, x0, dasar - hw, x0 + 16 * s, dasar, 0, mix(WHITE, CREAM, 0.2), al * 0.5)
    # plint
    rrect_on(img, x0, dasar - 18 * s, x1, dasar, 0, mix(CREAM, INK, 0.17), al)
    # atap
    puncak = (cx, dasar - hw - 150 * s)
    kiri = (x0 - 34 * s, dasar - hw + 6 * s)
    kanan = (x1 + 34 * s, dasar - hw + 6 * s)
    poly_on(img, [kiri, puncak, kanan, (x1, dasar - hw + 34 * s), (cx, puncak[1] + 34 * s),
                  (x0, dasar - hw + 34 * s)], TERRA, al)
    poly_on(img, [kiri, puncak, (cx, puncak[1] + 30 * s), (x0, dasar - hw + 30 * s)], TERRA_D, al * 0.55)
    line_on(img, kiri, kanan, mix(TERRA, WHITE, 0.45), 7 * s, al)
    line_on(img, kiri, puncak, mix(TERRA, WHITE, 0.22), 3 * s, al * 0.7)
    for k in (1, 2, 3, 4):
        q = k / 5.0
        line_on(img, (kiri[0] + (puncak[0] - kiri[0]) * q, kiri[1] + (puncak[1] - kiri[1]) * q),
                (kanan[0] + (puncak[0] - kanan[0]) * q, kanan[1] + (puncak[1] - kanan[1]) * q),
                mix(TERRA_D, INK, 0.30), 2 * s, al * 0.30)
    dot_on(img, puncak[0], puncak[1] - 3 * s, 5 * s, mix(TERRA_D, INK, 0.25), al)
    # talang + pipa
    line_on(img, (kiri[0] + 6 * s, kiri[1] + 4 * s), (kanan[0] - 6 * s, kanan[1] + 4 * s),
            mix(INK, MUTED, 0.45), 5 * s, al * 0.55)
    line_on(img, (x1 + 26 * s, dasar - hw + 10 * s), (x1 + 26 * s, dasar - 20 * s),
            mix(INK, MUTED, 0.50), 4 * s, al * 0.55)
    # jendela
    for (wx, ww) in ((x0 + 62 * s, 118 * s), (x1 - 62 * s - 118 * s, 118 * s)):
        wy0, wy1 = dasar - hw + 44 * s, dasar - 58 * s
        rrect_on(img, wx - 11 * s, wy0 - 11 * s, wx + ww + 11 * s, wy1 + 11 * s, 4 * s,
                 mix(CREAM, WHITE, 0.45), al)
        rrect_on(img, wx - 6 * s, wy0 - 6 * s, wx + ww + 6 * s, wy1 + 6 * s, 3 * s,
                 mix(INK, MUTED, 0.25), al)
        rrect_on(img, wx - 15 * s, wy1 + 6 * s, wx + ww + 15 * s, wy1 + 15 * s, 3 * s,
                 mix(CREAM, INK, 0.14), al)
        rrect_on(img, wx, wy0, wx + ww, wy1, 2 * s, mix(KUNING, WHITE, 0.22), al)
        rrect_on(img, wx, wy0, wx + ww, wy0 + (wy1 - wy0) * 0.55, 2 * s, mix(KUNING, WHITE, 0.38), al * 0.85)
        line_on(img, (wx + ww / 2, wy0), (wx + ww / 2, wy1), mix(INK, MUTED, 0.30), 3 * s, al * 0.75)
        line_on(img, (wx, (wy0 + wy1) / 2), (wx + ww, (wy0 + wy1) / 2), mix(INK, MUTED, 0.30), 3 * s, al * 0.75)
        poly_on(img, [(wx + ww * 0.08, wy1), (wx + ww * 0.40, wy0), (wx + ww * 0.56, wy0),
                      (wx + ww * 0.24, wy1)], mix(WHITE, KUNING, 0.35), al * 0.22)
        # gorden
        poly_on(img, [(wx + 2 * s, wy0 + 2 * s), (wx + 26 * s, wy0 + 2 * s),
                      (wx + 16 * s, wy1 - 2 * s), (wx + 2 * s, wy1 - 2 * s)], mix(TEAL_D, CREAM, 0.35), al * 0.35)
    # pintu + cahaya
    dx0, dx1 = cx - 56 * s, cx + 56 * s
    dy0, dy1 = dasar - 196 * s, dasar
    rrect_on(img, dx0 - 13 * s, dy0 - 12 * s, dx1 + 13 * s, dy1, 4 * s, mix(CREAM, WHITE, 0.35), al)
    rrect_on(img, dx0 - 5 * s, dy0 - 5 * s, dx1 + 5 * s, dy1, 3 * s, mix(INK, MUTED, 0.28), al)
    rrect_on(img, dx0, dy0, dx1, dy1, 2 * s, DOOR, al)
    for px_ in (dx0 + 12 * s, dx0 + 64 * s):
        for py_ in (dy0 + 18 * s, dy0 + 104 * s):
            rrect_on(img, px_, py_, px_ + 42 * s, py_ + 70 * s, 3 * s, mix(DOOR, WHITE, 0.045), al)
            rrect_on(img, px_, py_, px_ + 42 * s, py_ + 70 * s, 3 * s, mix(DOOR, INK, 0.35), al * 0.9,
                     outline=None)
    for k in (0.33, 0.66):
            line_on(img, (dx0 + 6 * s, dy0 + (dy1 - dy0) * k), (dx1 - 6 * s, dy0 + (dy1 - dy0) * k),
                mix(INK, WHITE, 0.45), 2 * s, al * 0.20)
    line_on(img, (dx0 + 6 * s, dy1 - 26 * s), (dx1 - 6 * s, dy1 - 26 * s), mix(KUNING, WHITE, 0.30), 3 * s, al * 0.35)
    dot_on(img, dx1 - 14 * s, dy1 - 96 * s, 4.4 * s, KUNING, al * 0.95)
    if lampu > 0.01:
        # tumpahan cahaya dari bawah pintu + kolam cahaya di tanah basah
        for k in range(4):
            q = k / 3.0
            ell(img, cx - (86 + 28 * k) * s, dy1 + (2 + 12 * k) * s,
                cx + (86 + 28 * k) * s, dy1 + (46 + 16 * k) * s,
                fill=mix(KUNING, WHITE, 0.34), alpha=al * (0.10 - 0.02 * k) * lampu)
        ell(img, cx - 118 * s, dy1 + 12 * s, cx + 118 * s, dy1 + 66 * s,
            fill=mix(KUNING, CREAM, 0.45), alpha=al * 0.24 * lampu)
        V._glow11(img, cx, dy1 + 8 * s, 120 * s, KUNING, 0.28 * lampu)
    # lampu dinding
    dot_on(img, cx, dy0 - 22 * s, 7 * s, mix(INK, KUNING, 0.45), al)
    V._glow11(img, cx, dy0 - 22 * s, 52 * s, KUNING, 0.32 * al * lampu)
    # semak berdaun + pot terakota
    for (bx, bs) in ((x0 + 54 * s, 1.0), (x1 - 54 * s, 0.88)):
        _semak(img, bx, dasar - 2 * s, bs * s, al)
    # anak tangga
    rrect_on(img, dx0 - 24 * s, dy1 - 12 * s, dx1 + 24 * s, dy1 + 10 * s, 3 * s, mix(CREAM, INK, 0.24), al)


def _semak(img, x, y, s=1.0, al=1.0, col=None):
    """Semak berdaun meruncing dalam pot terakota (bukan tumpukan lingkaran)."""
    col = col or mix(OLIVE, TEAL_D, 0.30)
    rrect_on(img, x - 32 * s, y - 44 * s, x + 32 * s, y, 6 * s, mix(TERRA, INK, 0.20), al)
    rrect_on(img, x - 38 * s, y - 54 * s, x + 38 * s, y - 40 * s, 5 * s, mix(TERRA, WHITE, 0.18), al)
    line_on(img, (x - 30 * s, y - 52 * s), (x + 30 * s, y - 52 * s), mix(TERRA, INK, 0.35), 2 * s, al * 0.6)
    d = ImageDraw.Draw(img)
    for i in range(14):
        a = -2.62 + i * 0.245
        ln = (44 + 26 * _rnd(i, 2)) * s
        bx, by = x + math.cos(a) * 9 * s, y - 56 * s
        tipx, tipy = bx + math.cos(a) * ln * 0.72, by + math.sin(a) * ln
        wx, wy = -math.sin(a) * ln * 0.26, math.cos(a) * ln * 0.26
        mx, my = bx + math.cos(a) * ln * 0.52, by + math.sin(a) * ln * 0.52
        tone = mix(col, WHITE if i % 3 == 0 else INK, 0.05 + 0.09 * _rnd(i, 4))
        poly_on(img, [(bx, by), (mx + wx, my + wy), (tipx, tipy), (mx - wx, my - wy)], tone, al)
        dot_on(img, tipx, tipy, ln * 0.10, mix(tone, WHITE, 0.10), al)
        line_on(img, (bx, by), (tipx, tipy), mix(tone, INK, 0.18), max(1.0, 1.1 * s), al * 0.35)


def _sawah(img, y, al=1.0):
    """Tanah basah: paving + genangan + pantulan cahaya (statis)."""
    rrect_on(img, 0, y, 1080, y + 420, 0, WET, al)
    rrect_on(img, 0, y, 1080, y + 26, 0, mix(WET, INK, 0.10), al * 0.9)
    for i in range(9):
        yy = y + 40 + i * 34
        line_on(img, (0, yy), (1080, yy - 6), mix(WET, INK, 0.18), 2, al * 0.18)
    for i in range(6):
        x = 90 + i * 190
        line_on(img, (x, y + 40), (x + 4, y + 380), mix(WET, INK, 0.16), 2, al * 0.16)
    # genangan
    for (px, py, rx, ry) in ((300, y + 88, 120, 18), (760, y + 132, 96, 15), (176, y + 210, 74, 12)):
        ell(img, px - rx, py - ry, px + rx, py + ry, fill=mix(WET, SKY2, 0.55), alpha=al * 0.75)
        line_on(img, (px - rx * 0.8, py - ry * 0.5), (px + rx * 0.2, py - ry * 0.62),
                mix(WHITE, KUNING, 0.35), 3, al * 0.35)


# ------------------------------------------------------------------ kertas & teks
_SOLID = {}
_SCRIM = {}


def _solid(col):
    key = (col, round(D.SS, 6))
    im = _SOLID.get(key)
    if im is None:
        im = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), col)
        _SOLID[key] = im
    return im


def _scrim(y0, y1, peak=1.0, gamma=1.15):
    key = (round(y0), round(y1), round(peak, 3), gamma, round(D.SS, 6))
    m = _SCRIM.get(key)
    if m is None:
        import numpy as np
        h, w = int(D.S(1920)), int(D.S(1080))
        ys = np.arange(h, dtype="float32") / D.SS
        t = np.clip((ys - y0) / float(y1 - y0), 0.0, 1.0) ** gamma
        arr = (t * 255.0 * peak).astype("uint8")[:, None].repeat(w, axis=1)
        m = Image.fromarray(arr, "L")
        _SCRIM[key] = m
    return m


_SCRIM_TOP = {}


def _scrim_atas(y1=210, peak=0.60):
    key = (round(y1), round(peak, 3), round(D.SS, 6))
    m = _SCRIM_TOP.get(key)
    if m is None:
        import numpy as np
        h, w = int(D.S(1920)), int(D.S(1080))
        ys = np.arange(h, dtype="float32") / D.SS
        t = np.clip(1.0 - ys / float(y1), 0.0, 1.0) ** 1.25
        arr = (t * 255.0 * peak).astype("uint8")[:, None].repeat(w, axis=1)
        m = Image.fromarray(arr, "L")
        _SCRIM_TOP[key] = m
    return m


_PAPER_MASK = {}


def _paper_mask(y0=1040, y1=1290):
    """Mask kertas: tepi atas bergelombang (sobek halus), bukan garis lurus."""
    key = (round(y0), round(y1), round(D.SS, 6))
    m = _PAPER_MASK.get(key)
    if m is None:
        import numpy as np
        h, w = int(D.S(1920)), int(D.S(1080))
        xs = np.arange(w, dtype="float32") / D.SS
        ys = np.arange(h, dtype="float32")[:, None] / D.SS
        edge = (y0 + 5.0 * np.sin(xs / 88.0) + 2.6 * np.sin(xs / 31.0 + 2.1)
                + 1.4 * np.sin(xs / 13.0 + 0.7))[None, :]
        t = np.clip((ys - edge) / float(y1 - y0), 0.0, 1.0) ** 1.18
        m = Image.fromarray((t * 255.0).astype("uint8"), "L")
        _PAPER_MASK[key] = m
    return m


def _paper(img, al=1.0, sumber=SUMBER, y0=1040, y1=1290):
    """Zona teks: dunia melunasi diri ke kertas krem (tepi sobek) + bobot bawah + sumber."""
    img.paste(_solid(CREAM), (0, 0), _paper_mask(y0, y1))
    # garis bayangan tipis tepat di bawah tepi kertas -> terasa seperti lembaran fisik
    prev = None
    for i in range(0, 1081, 9):
        yy = y0 + 5.0 * math.sin(i / 88.0) + 2.6 * math.sin(i / 31.0 + 2.1) + 1.4 * math.sin(i / 13.0 + 0.7)
        if prev is not None:
            line_on(img, prev, (i, yy + 4.0), mix(INK, CREAM, 0.55), 3.0, 0.13 * al)
        prev = (i, yy + 4.0)
    _speck(img, 12, y0 + 18, 1068, 1880, 150, mix(INK, CREAM, 0.42), 0.055 * al, seed=21, r=(0.8, 2.0))
    img.paste(_solid(mix(CREAM, INK, 0.09)), (0, 0), _scrim(1470, 1920, peak=0.85))
    img.paste(_solid(CREAM), (0, 0), _scrim_atas())
    if sumber:
        paste_c(img, 540, 1768, sumber, font(D.FM, 25), mix(INK, MUTED, 0.58), 0.70 * al)


def _catatan(sc, accent, img, al=1.0):
    """Satu baris penjelas di bawah judul: mengisi bidang kertas + menambah kejelasan."""
    txt = sc.get("catatan")
    if not txt:
        return
    yy = 1508
    line_on(img, (540 - 42, 1468), (540 + 42, 1468), mix(accent, INK, 0.10), 2.6, 0.55 * al)
    paste_c(img, 540, yy, txt, font(D.FS, 33), mix(INK, MUTED, 0.28), al * 0.94)


def _catatan_medis(img, qf, al=1.0):
    """Catatan merah di zona kertas: tiga tindakan yang justru berbahaya."""
    if qf <= 0.01:
        return
    yy = 1592 + (1 - qf) * 18
    rrect_on(img, 96, yy - 34, 984, yy + 34, 30, mix(RED, CREAM, 0.86), 0.95 * qf * al)
    ring_on(img, 140, yy, 17, mix(RED, INK, 0.10), 2.4, 0.9 * qf * al)
    silang(img, 140, yy, 9, mix(RED, INK, 0.10), 0.9 * qf * al, 1.0)
    paste_c(img, 566, yy, "Torniket ketat · sayatan · isapan", font(D.FS, 26),
            mix(RED, INK, 0.12), qf * al)


def _fit(text, fsz, maxw):
    w = tw(text, font(D.FB, fsz))
    return fsz * min(1.0, maxw / max(1.0, w))


def teks(img, sc, accent, tl, al, t0, text=None, hl=None, fsz=62, y=Y_TXT, maxw=900):
    """Judul dua baris yang benar-benar dua baris (ukuran disamakan, muat 900 px)."""
    lines = text if text is not None else (sc.get("lines") or [sc.get("badge", "")])
    if isinstance(lines, str):
        lines = [lines]
    hl = hl if hl is not None else sc.get("hl", "")
    size = min(_fit(ln, fsz, maxw) for ln in lines)
    size = max(38.0, size)
    lh = tlh(font(D.FB, size)) * 1.02
    n = len(lines)
    for i, ln in enumerate(lines):
        yy = y - (n - 1) * lh * 0.5 + i * lh
        h_i = hl if any(w.upper().strip(",.:?!") in hl.upper().split() for w in ln.split()) else ""
        V._judul11(img, ln, accent, tl, al * M.KELUAR[0], y=yy, hl=h_i, fsz=size,
                   t0=t0 + i * 0.12, maxw=maxw)


def _chip(sc, accent, img, al=1.0):
    chip(img, 540, Y_FOOT, sc.get("badge", ""), mix(accent, INK, 0.14), al, 10.0,
         fsz=25, persisten=True)


# ------------------------------------------------------------------ dunia luar
def _langit(img, hor=690, al=1.0):
    _grad(img, 0, hor + 12, SKY1, SKY2, 96)
    # awan: pita tipis berlapis (bukan elips gemuk) + inti lebih terang
    for (cx, cy, rx, ry, a) in ((760, 246, 300, 30, 0.34), (250, 168, 250, 22, 0.26),
                                (980, 402, 230, 20, 0.20), (150, 398, 200, 18, 0.18),
                                (600, 104, 340, 26, 0.18), (430, 300, 260, 16, 0.14),
                                (900, 300, 210, 14, 0.12)):
        for k in range(3):
            q = k / 2.0
            ell(img, cx - rx * (1 - 0.12 * q), cy - ry * (1 - 0.45 * q),
                cx + rx * (1 - 0.12 * q), cy + ry * (1 - 0.45 * q),
                fill=mix(SKY2, WHITE, 0.35 + 0.35 * q), alpha=a * (0.55 - 0.18 * q) * al)
    # kabut horizon
    for i in range(9):
        q = i / 8.0
        line_on(img, (0, hor - 120 + i * 16), (1080, hor - 120 + i * 16),
                mix(SKY2, WHITE, 0.55), 22 - 2 * i, 0.05 * al)
    V._glow11(img, 812, 236, 230, mix(KUNING, WHITE, 0.45), 0.12 * al)


def _bukit(img, hor=690, al=1.0):
    for lapis, (col, amp, base, nd) in enumerate(((mix(TEAL, SKY2, 0.78), 20, -8, 0.0042),
                                                  (mix(TEAL, SKY2, 0.58), 30, 26, 0.0061))):
        pts = [(0, hor + 200)]
        for i in range(29):
            x = i * 40
            y = hor - base - amp * math.sin(x * nd + 1.3 * lapis) - 9 * math.sin(x * 0.021 + lapis)
            pts.append((x, y))
        pts += [(1080, hor + 200)]
        poly_on(img, pts, col, 0.9 * al)
    # siluet pohon di garis horizon
    for i, (x, s) in enumerate(((60, 0.34), (128, 0.26), (240, 0.30), (700, 0.24), (790, 0.32),
                                (900, 0.26), (1010, 0.36))):
        _pohon(img, x, hor + 6, s, mix(TEAL, SKY2, 0.42), 0.52 * al, seed=i)
    for i in range(14):
        x = 40 + i * 78
        dot_on(img, x, hor + 4, 2.4, mix(TEAL, WHITE, 0.30), 0.35 * al)


def _tanah(img, y=1084, al=1.0, col=None, lebar_genang=(210, 820)):
    col = col or WET
    rrect_on(img, -10, y, 1090, 1240, 0, col, al)
    rrect_on(img, -10, y, 1090, y + 30, 0, mix(col, INK, 0.09), al * 0.9)
    for i in range(11):
        yy = y + 30 + i * 17
        line_on(img, (-10, yy), (1090, yy - 4), mix(col, INK, 0.20), 2, al * 0.16)
    for i in range(9):
        x = -10 + i * 132
        line_on(img, (x, y + 26), (x + 5, y + 170), mix(col, INK, 0.16), 2, al * 0.14)
    # genangan + pantulan cahaya langit
    for (px, py, rx, ry) in ((lebar_genang[0], y + 46, 130, 16), (lebar_genang[1], y + 84, 104, 13),
                             (470, y + 128, 150, 14)):
        ell(img, px - rx, py - ry, px + rx, py + ry, fill=mix(col, SKY2, 0.50), alpha=al * 0.8)
        line_on(img, (px - rx * 0.72, py - ry * 0.45), (px + rx * 0.18, py - ry * 0.62),
                mix(WHITE, KUNING, 0.28), 3, al * 0.30)


def _titisan_genteng(img, u, xs=(214, 372, 668, 834), y_atap=730, y_tanah=1076, al=1.0):
    """Air jatuh dari tepi atap: tetes + cipratan, fase berbeda; periodik 1 s (loop-safe)."""
    for i, x in enumerate(xs):
        q = (u * 1.0 + i * 0.27) % 1.0
        y = y_atap + (y_tanah - y_atap) * (q ** 1.55)
        line_on(img, (x, y - 20), (x, y), mix(CREAM, INK, 0.45), 3, al * (0.30 + 0.4 * (1 - q)))
        if q > 0.94:
            k = (q - 0.94) / 0.06
            for j in range(3):
                a = -1.9 + j * 0.9
                line_on(img, (x, y_tanah), (x + math.cos(a) * 14 * k, y_tanah + math.sin(a) * 10 * k),
                        mix(CREAM, INK, 0.35), 2, al * 0.35 * (1 - k))


_BASE = {}


def _base(nama, builder):
    key = (nama, round(D.SS, 6))
    im = _BASE.get(key)
    if im is None:
        im = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), CREAM)
        builder(im)
        _BASE[key] = im
    return im


def _arc(img, cx, cy, r, a0, a1, col, w=6, alpha=1.0, squash=1.0):
    if alpha <= 0.01 or abs(a1 - a0) < 0.01:
        return
    n = max(2, int(abs(a1 - a0) / 0.070))
    prev = (cx + r * math.cos(a0), cy + r * squash * math.sin(a0))
    for i in range(1, n + 1):
        a = a0 + (a1 - a0) * i / n
        p = (cx + r * math.cos(a), cy + r * squash * math.sin(a))
        line_on(img, prev, p, col, w, alpha)
        prev = p


# ================================================================ 1. INTRO · AMBANG
def _dunia_ambang(im):
    _langit(im, 690)
    _bukit(im, 690)
    # pohon tinggi di tepi kanan (memotong langit kosong, memberi bingkai)
    line_on(im, (1016, 1104), (1032, 470), mix(SOIL3, INK, 0.30), 18, 0.95)
    line_on(im, (1024, 700), (912, 566), mix(SOIL3, INK, 0.30), 9, 0.9)
    line_on(im, (1030, 830), (1082, 700), mix(SOIL3, INK, 0.30), 8, 0.9)
    _kanopi(im, 1000, 470, 150, mix(TEAL_D, INK, 0.34), 0.96, seed=1.7)
    _kanopi(im, 900, 566, 92, mix(TEAL_D, INK, 0.30), 0.85, seed=3.1)
    _kanopi(im, 1052, 640, 86, mix(TEAL_D, INK, 0.26), 0.75, seed=5.4)
    # kabel listrik melengkung + burung
    for (x1, y1, x2, y2, sag) in ((0, 522, 1016, 486, 54), (0, 548, 1016, 512, 44)):
        for i in range(40):
            q0, q1 = i / 40.0, (i + 1) / 40.0
            p0 = (x1 + (x2 - x1) * q0, y1 + (y2 - y1) * q0 + sag * math.sin(math.pi * q0))
            p1 = (x1 + (x2 - x1) * q1, y1 + (y2 - y1) * q1 + sag * math.sin(math.pi * q1))
            line_on(im, p0, p1, mix(INK, MUTED, 0.45), 2, 0.30)
    for (bx, by, bs) in ((306, 470, 1.0), (352, 448, 0.8), (398, 466, 0.7)):
        line_on(im, (bx - 12 * bs, by), (bx, by - 5 * bs), mix(INK, MUTED, 0.4), 2.4, 0.55)
        line_on(im, (bx, by - 5 * bs), (bx + 12 * bs, by), mix(INK, MUTED, 0.4), 2.4, 0.55)
    # tanah + rumah (skala 1,12 supaya subjek mengisi frame)
    _tanah(im, 1084, 1.0, WET, (250, 812))
    _rumah(im, 540, 1084, 1.12, 1.0, 1.0)
    # tong air hujan + tanaman (pengganti kerucut)
    rrect_on(im, 74, 1004, 148, 1100, 8, mix(TEAL_D, INK, 0.20), 0.92)
    rrect_on(im, 74, 1004, 148, 1022, 8, mix(TEAL_D, WHITE, 0.16), 0.9)
    for k in range(3):
        line_on(im, (82, 1030 + k * 24), (140, 1030 + k * 24), mix(CREAM, TEAL_D, 0.45), 2, 0.35)
    _semak(im, 186, 1100, 0.86, 1.0)
    # pagar rendah kanan (di belakang pagar pohon)
    for i in range(3):
        x = 892 + i * 58
        rrect_on(im, x, 1012, x + 12, 1092, 3, mix(CREAM, INK, 0.33), 0.9)
        poly_on(im, [(x - 4, 1016), (x + 6, 998), (x + 16, 1016)], mix(CREAM, INK, 0.33), 0.9)
    line_on(im, (876, 1042), (1084, 1038), mix(CREAM, INK, 0.30), 8, 0.85)
    line_on(im, (876, 1070), (1084, 1066), mix(CREAM, INK, 0.30), 6, 0.7)


def sc_ambang_hujan(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0   # dunia digambar penuh: match/morph = potongan murni, tanpa kilat krem
    c = cues(sc, dur, CUES["ambang_hujan60"])
    base = _base("ambang", _dunia_ambang)
    img.paste(base, (0, 0))
    u = tl
    # hujan + kabut + riak
    _hujan_lapis(img, u, ("jauh", "mid"), 0, 1080, 150, 1060, 0.95 * al)
    _hujan_lapis(img, u, ("dekat",), 0, 1080, 120, 1090, 0.85 * al)
    _titisan_genteng(img, u, (214, 372, 668, 834), 730, 1068, al)
    _riak(img, 250, 1128, u * 0.8, 0.45 * al, 4, 40)
    _riak(img, 812, 1122, u * 0.8 + 0.5, 0.42 * al, 4, 34)
    _kabut(img, 986, 120, 0.085 * al)
    # cahaya pintu bernapas (fase lokal -> loop aman)
    lampu = 0.86 + 0.14 * math.sin(u * 1.7)
    V._glow11(img, 540, 1006, 92, KUNING, 0.20 * lampu * al)
    # ular masuk dari kanan ke ambang pintu
    prog = esm((tl - c["ular"]) / 2.35)
    if prog > 0.01:
        s_head = 0.06 + 0.88 * prog
        n = 26
        pts = []
        for i in range(n):
            s = s_head - (n - 1 - i) * 0.0135
            s = clamp(s, 0.0, 1.0)
            x = 1250 + (508 - 1250) * s
            y = 1078 - 12 * math.sin(s * 3.6) - 16 * esm((s - 0.62) / 0.34)
            y += 6 * math.sin(s * 26.0 + u * 4.4) * (0.25 + 0.75 * s)
            pts.append((x, y))
        ular(img, pts, al * 0.98, lebar=13.5, u=1.0, lidah=(math.sin(tl * 3.1) > 0.55))
    # burung/daun jatuh pelan (gerak halus konstan)
    for i in range(3):
        q = (u * 0.15 + i * 0.34) % 1.0
        x = 760 + i * 90 + 30 * math.sin(u * 0.6 + i)
        y = 760 + q * 300
        line_on(img, (x, y), (x + 9, y - 6), mix(OLIVE, TEAL_D, 0.4), 3, 0.35 * al * (1 - q))
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    at = 1.0   # judul bertahan sampai potongan (tanpa kedip kosong)
    teks(img, sc, accent, tl, at, 0.22, fsz=64, y=Y_TXT)
    if 0 <= tl - c["hujan"] < 0.45:
        k = 1 - (tl - c["hujan"]) / 0.45
        V._glow11(img, 806, 240, 300, mix(WHITE, KUNING, 0.30), 0.22 * k)


# ================================================================ 2. F1 · HABITAT TERGENANG
def _dunia_genang(im):
    """Sawah terendam: air dangkal, pagar tenggelam, bank tanah berlubang + batang berongga."""
    _grad(im, 0, 612, SKY1, mix(SKY2, TEAL, 0.16), 64)
    for (cx, cy, rx, ry, a) in ((700, 190, 260, 26, 0.30), (250, 128, 200, 20, 0.22),
                                (960, 320, 190, 18, 0.16)):
        for k in range(3):
            q = k / 2.0
            ell(im, cx - rx, cy - ry * (1 - 0.4 * q), cx + rx, cy + ry * (1 - 0.4 * q),
                fill=mix(SKY2, WHITE, 0.35 + 0.3 * q), alpha=a * (0.5 - 0.15 * q))
    for i in range(24):
        _pohon(im, 2 + i * 48 + 12 * _rnd(i, 1), 596 + 10 * math.sin(i * 2.3) - 16 * _rnd(i, 5),
               0.13 + 0.15 * _rnd(i, 4), mix(TEAL, SKY2, 0.52 + 0.10 * _rnd(i, 6)), 0.50, seed=i)
    for i in range(8):
        line_on(im, (0, 528 + i * 11), (1080, 528 + i * 11), mix(SKY2, WHITE, 0.5), 18, 0.055)
    # air
    _grad(im, 606, 1052, mix(TEAL, SKY2, 0.60), mix(TEAL, SKY2, 0.26), 80)
    for i in range(16):
        y = 620 + i * 26
        line_on(im, (-10, y), (1090, y - 3 + 3 * math.sin(i * 1.3)),
                mix(TEAL, SKY2, 0.72 if i % 2 else 0.54), 2, 0.20)
    # pantulan langit + pita air depan yang lebih gelap (kedalaman)
    _grad(im, 760, 890, mix(TEAL, WHITE, 0.10), mix(TEAL, SKY2, 0.34), 40)
    for i in range(14):
        x = 20 + _rnd(i, 9) * 1040
        w = 60 + _rnd(i, 10) * 150
        yy = 792 + _rnd(i, 11) * 86
        line_on(im, (x, yy), (x + w, yy + 2), mix(WHITE, SKY2, 0.30), 2.0,
                0.16 + 0.12 * _rnd(i, 12))
    _grad(im, 838, 892, mix(TEAL, SKY2, 0.34), mix(TEAL_D, TEAL, 0.30), 30)
    # pagar tenggelam (hanya rail atas yang tampak)
    for i in range(6):
        x = 560 + i * 92
        ytop = 596 + 5 * math.sin(i * 1.7)
        rrect_on(im, x, ytop, x + 9, 700, 3, mix(SOIL3, INK, 0.20), 0.92)
        rrect_on(im, x, 690, x + 9, 786, 3, mix(SOIL3, TEAL_D, 0.30), 0.42)
    line_on(im, (548, 614), (1084, 602), mix(SOIL3, INK, 0.22), 8, 0.86)
    line_on(im, (548, 600), (1084, 588), mix(SOIL3, WHITE, 0.25), 3, 0.45)
    # gumuk kanan jauh
    poly_on(im, [(690, 700), (762, 664), (872, 662), (946, 694), (900, 720), (742, 720)],
            mix(SOIL1, TEAL_D, 0.44), 0.90)
    _grass(im, 668, 748, 918, mix(OLIVE, TEAL_D, 0.30), 0.85, n=14, h=52, seed=6)
    # bank tanah depan (potongan) + lubang galian
    poly_on(im, [(-10, 1032), (60, 1000), (210, 992), (360, 1012), (430, 1036), (1084, 1046),
                 (1084, 1130), (-10, 1130)], mix(SOIL2, INK, 0.16), 1.0)
    for i in range(26):
        x = -10 + i * 42
        line_on(im, (x, 1044 + 6 * math.sin(i * 1.9)), (x + 5, 1128), mix(SOIL3, INK, 0.25), 2, 0.12)
    _grass(im, 1006, 30, 300, mix(OLIVE, TEAL_D, 0.20), 0.9, n=20, h=60, seed=3)
    # lubang di bank (air masuk) + akar
    poly_on(im, [(96, 1044), (100, 1020), (126, 1006), (170, 1006), (198, 1022), (200, 1044),
                 (178, 1056), (120, 1056)], mix(SOIL3, INK, 0.62), 0.97)
    ell(im, 108, 1018, 190, 1054, fill=mix(SOIL3, INK, 0.30), alpha=0.55)
    line_on(im, (100, 1020), (126, 1006), mix(SOIL1, WHITE, 0.30), 4, 0.55)
    line_on(im, (126, 1006), (170, 1006), mix(SOIL1, WHITE, 0.30), 4, 0.45)
    for k in range(5):
        line_on(im, (96 + k * 24, 1034), (86 + k * 26, 1006 - 16 * (k % 2)),
                mix(SOIL3, INK, 0.30), 3, 0.5)
    # genangan masuk ke lubang
    for k in range(3):
        line_on(img_ := im, (96, 1024 + k * 4), (150 + k * 12, 1030 + k * 5),
                mix(TEAL, SKY2, 0.55), 3, 0.55)
    # pancang ukur
    rrect_on(im, 966, 608, 982, 940, 5, mix(CREAM, INK, 0.55), 0.95)
    for i in range(9):
        y = 628 + i * 34
        line_on(im, (982, y), (1008, y), mix(CREAM, INK, 0.45), 3.4, 0.9)
    rrect_on(im, 961, 700, 987, 718, 3, mix(KUNING, INK, 0.16), 0.95)
    # batang kayu rebah (tempat telur): serat kayu + rongga kecil di ujung kiri
    rrect_on(im, 356, 988, 786, 1034, 22, mix(SOIL2, INK, 0.10), 1.0)
    rrect_on(im, 356, 988, 786, 1004, 15, mix(SOIL1, WHITE, 0.26), 0.95)
    rrect_on(im, 360, 1012, 786, 1032, 10, mix(SOIL3, INK, 0.28), 0.35)
    for k in range(7):
        yy = 996 + k * 5
        line_on(im, (374 + 12 * math.sin(k), yy), (770 - 12 * math.sin(k * 1.7), yy + 2),
                mix(SOIL3, INK, 0.20), 1.8, 0.30)
    ell(im, 366, 1000, 448, 1030, fill=mix(SOIL3, INK, 0.62), alpha=0.92)
    ell(im, 372, 1003, 442, 1024, fill=mix(SOIL3, INK, 0.30), alpha=0.55)
    _grass(im, 1016, 690, 790, mix(OLIVE, TEAL_D, 0.22), 0.55, n=8, h=26, seed=11)
    _grass(im, 1000, 780, 1070, mix(OLIVE, TEAL_D, 0.24), 0.8, n=10, h=54, seed=9)


def sc_habitat_tergenang(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0   # dunia digambar penuh: match/morph = potongan murni, tanpa kilat krem
    c = cues(sc, dur, CUES["habitat_tergenang60"])
    img.paste(_base("genang", _dunia_genang), (0, 0))
    u = tl
    _hujan_lapis(img, u, ("jauh", "mid"), 0, 1080, 110, 980, 0.95 * al)
    _hujan_lapis(img, u, ("dekat",), 0, 1080, 520, 1010, 0.50 * al)
    # riak hujan
    for i in range(9):
        x = 40 + _rnd(i, 1) * 1000
        y = 620 + _rnd(i, 2) * 340
        _riak(img, x, y, (u * 0.8 + i * 0.17) % 1.0, 0.42 * al, 3, 40 + i * 4, squash=0.14)
    # ular berenang (seluruh badan di dalam frame)
    sw = esm((tl - c["berpindah"]) / 2.3)
    if sw > 0.005:
        hx = 300 + (700 - 300) * sw
        hy = 852 + 9 * math.sin(u * 1.35)
        n = 22
        pts = []
        for i in range(n):
            s2 = i / (n - 1)
            pts.append((hx - 300 * s2 * (0.55 + 0.45 * sw), hy + 10 * s2 + 8 * math.sin(s2 * 4.6 + u * 2.4) * s2))
        for i in range(n - 1):
            if i % 2 == 0:
                line_on(img, (pts[i][0], pts[i][1] + 11), (pts[i + 1][0], pts[i + 1][1] + 11),
                        mix(TEAL, SKY2, 0.62), 5, 0.26 * al)
        ular(img, pts, al * 0.96, lebar=12.5, col=mix(NAVY3, TEAL_D, 0.22),
             lidah=(math.sin(tl * 2.7) > 0.55))
        for k in range(3):
            line_on(img, (hx - 18, hy + 10 + k * 8), (hx - 92 - k * 40, hy + 24 + k * 9),
                    mix(WHITE, SKY2, 0.38), 3, (0.32 - k * 0.08) * al)
    # penanda tinggi air
    naik = 872 - 54 * esm(tl / max(1.0, dur))
    line_on(img, (956, naik), (1012, naik), mix(accent, WHITE, 0.30), 5, 0.95 * al)
    dot_on(img, 1012, naik, 6.5, accent, 0.95 * al)
    rrect_on(img, 806, naik - 58, 962, naik - 20, 8, mix(CREAM, WHITE, 0.35), 0.88 * al)
    paste_c(img, 884, naik - 39, "AIR NAIK", font(D.FS, 22), mix(accent, INK, 0.25), 0.95 * al)
    line_on(img, (962, naik - 39), (982, naik), mix(accent, INK, 0.25), 2.2, 0.7 * al)
    # daun hanyut
    for i in range(4):
        x = 120 + i * 230 + 20 * math.sin(u * 0.45 + i * 1.7)
        y = 700 + i * 70 + 5 * math.cos(u * 0.4 + i)
        line_on(img, (x, y), (x + 24, y - 4), mix(OLIVE, TEAL_D, 0.25), 4, 0.40 * al)
    # telur terungkap (out-anchor 540,1010)
    q = esm((tl - (dur - 1.15)) / 0.9)
    if q > 0.01:
        V._glow11(img, 556, 1020, 84, mix(KUNING, WHITE, 0.4), 0.20 * q * al)
        for (ex, ey, rx) in ((506, 1016, 17), (546, 1008, 18), (586, 1018, 16),
                             (526, 1034, 15), (566, 1034, 15)):
            ell(img, ex - rx, ey - rx * 0.80, ex + rx, ey + rx * 0.80,
                fill=mix(CREAM, KUNING, 0.20), alpha=q * al * 0.98)
            dot_on(img, ex - rx * 0.34, ey - rx * 0.40, rx * 0.22, WHITE, q * al * 0.55)
            line_on(img, (ex - rx * 0.55, ey + rx * 0.22), (ex + rx * 0.45, ey + rx * 0.36),
                    mix(SOIL2, INK, 0.2), 2, q * al * 0.45)
    _paper(img, 1.0, SUMBER, y0=1042, y1=1300)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    at = 1.0   # judul bertahan sampai potongan (tanpa kedip kosong)
    teks(img, sc, accent, tl, at, 0.20, fsz=64, y=Y_TXT)


# ================================================================ 3. F2 · 22 ANAK SANCA
def _dunia_anakan(im):
    """Tanah lembap dari atas: serasah, cangkang, dan sarang — bidang penuh (bukan langit)."""
    _grad(im, 0, 1200, mix(SOIL2, INK, 0.16), mix(SOIL1, INK, 0.02), 90)
    for i in range(70):
        x = _rnd(i, 1) * 1080
        y = _rnd(i, 2) * 1160
        r = 12 + 34 * _rnd(i, 3)
        ell(im, x - r, y - r * 0.34, x + r, y + r * 0.34,
            fill=mix(SOIL2, OLIVE if i % 3 else AMBER2, 0.14 + 0.26 * _rnd(i, 4)),
            alpha=0.30 + 0.28 * _rnd(i, 5))
    for i in range(16):
        x = _rnd(i, 6) * 1040 + 20
        y = 60 + _rnd(i, 7) * 1080
        line_on(im, (x, y), (x + 30 + 50 * _rnd(i, 8), y - 10 + 20 * _rnd(i, 9)),
                mix(SOIL3, INK, 0.20), 3, 0.45)
    for (px, py, rx, ry) in ((250, 300, 150, 40), (820, 700, 190, 44), (420, 980, 160, 30)):
        ell(im, px - rx, py - ry, px + rx, py + ry, fill=mix(SOIL3, SKY2, 0.30), alpha=0.35)
    # cangkang pecah di sarang (kiri-tengah)
    for (ex, ey, rot) in ((300, 900, 0.3), (352, 926, -0.5), (392, 884, 1.1), (330, 860, 2.0)):
        poly_on(im, [(ex + 22 * math.cos(rot), ey + 16 * math.sin(rot)),
                     (ex + 18 * math.cos(rot + 1.1), ey + 14 * math.sin(rot + 1.1)),
                     (ex + 4 * math.cos(rot + 2.4), ey + 10 * math.sin(rot + 2.4)),
                     (ex + 2 * math.cos(rot + 3.9), ey + 8 * math.sin(rot + 3.9)),
                     (ex + 16 * math.cos(rot + 5.0), ey + 12 * math.sin(rot + 5.0))],
                mix(CREAM, KUNING, 0.22), 0.95)
    _grass(im, 1140, 40, 300, mix(OLIVE, TEAL_D, 0.30), 0.5, n=14, h=54, seed=5)
    _grass(im, 1150, 820, 1060, mix(OLIVE, TEAL_D, 0.30), 0.5, n=12, h=44, seed=8)


_ANAK = []
for _i in range(22):
    _a = -2.2 + (_i / 21.0) * 4.6          # busur mengelilingi sarang
    _r = 150 + 46 * ((_i * 3) % 5) / 4.0
    _ANAK.append((392 + math.cos(_a) * _r, 900 + math.sin(_a) * _r * 0.80, _a))


def sc_anakan_sanca(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0   # dunia digambar penuh: match/morph = potongan murni, tanpa kilat krem
    c = cues(sc, dur, CUES["anakan_sanca60"])
    img.paste(_base("anakan", _dunia_anakan), (0, 0))
    u = tl
    _hujan_lapis(img, u, ("jauh", "mid"), 0, 1080, 40, 1120, 0.55 * al)
    # cipratan hujan di tanah (riak kecil)
    for i in range(10):
        _riak(img, 40 + _rnd(i, 3) * 1000, 80 + _rnd(i, 1) * 1000,
              (u * 0.9 + i * 0.21) % 1.0, 0.26 * al, 3, 26, squash=0.42)
    # sarang telur (hadir sejak frame 0; memudar saat anakan keluar)
    qe = 1 - esm((tl - (c["dua"] - 0.35)) / 1.1)
    if qe > 0.01:
        for i, (ex, ey) in enumerate(((392, 895), (362, 916), (421, 919), (391, 943), (438, 890))):
            _shadow(img, ex + 3, ey + 24, 17, 5, 0.22 * qe)
            ell(img, ex - 15, ey - 23, ex + 15, ey + 23, fill=mix(CREAM, KUNING, 0.26), alpha=0.98 * qe * al)
            ell(img, ex - 15, ey - 23, ex + 15, ey + 23, outline=mix(SOIL2, CREAM, 0.35), width=2,
                alpha=0.55 * qe * al)
            dot_on(img, ex - 5, ey - 9, 3.6, WHITE, 0.45 * qe * al)
        V._glow11(img, 396, 916, 92, mix(KUNING, WHITE, 0.4), 0.10 * qe * al)
    # 22 anakan muncul satu per satu (data sebagai gerak)
    t0 = c["dua"]
    muncul = 0
    for i, (ax, ay, ang) in enumerate(_ANAK):
        tq = (tl - (t0 + i * 0.085)) / 0.42
        if tq <= 0:
            continue
        q = esm(tq)
        muncul += 1
        ln = 74 * q
        wig = 9 * math.sin(u * 4.4 + i * 1.3)
        hx, hy = ax + math.cos(ang) * ln, ay + math.sin(ang) * ln * 0.7
        pts = []
        for j in range(6):
            s3 = j / 5.0
            wob = wig * s3 * math.sin(s3 * 5.2 + i * 0.7)
            pts.append((ax + math.cos(ang) * ln * s3 - math.sin(ang) * wob,
                        ay + math.sin(ang) * ln * 0.70 * s3 + math.cos(ang) * wob * 0.5))
        ular(img, pts, 0.95 * al, lebar=5.4, col=mix(NAVY3, TEAL_D, 0.18), lidah=False, sisik=False)
    # penghitung 22 + cincin progres
    kq = seg(tl, t0, t0 + 0.5)
    if kq > 0:
        k = eob(kq)
        cx, cy = 800, 470
        ring_on(img, cx, cy, 150, mix(accent, WHITE, 0.55), 4, 0.30 * al)
        _arc(img, cx, cy, 150, -math.pi / 2, -math.pi / 2 + 2 * math.pi * (muncul / 22.0),
             accent, 9, 0.9 * al)
        paste_c(img, cx, cy - 10, str(muncul), font(D.FB, 150 * (0.86 + 0.14 * k)),
                mix(CREAM, WHITE, 0.30), al, scale=1.0)
        paste_c(img, cx, cy + 92, "ANAK SANCA", font(D.FS, 27), mix(CREAM, KUNING, 0.30), 0.92 * al)
    _paper(img, 1.0, SUMBER, y0=1052, y1=1300)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    at = 1.0   # judul bertahan sampai potongan (tanpa kedip kosong)
    teks(img, sc, accent, tl, at, 0.20, fsz=62, y=Y_TXT)


# ================================================================ 4. F3 · DUA CARA
def _ikon_telur(img, cx, cy, r, col, al=1.0):
    for (dx, dy, rr) in ((-1.5, 0.4, 0.70), (-0.2, -0.5, 0.86), (1.3, 0.5, 0.74), (0.6, 1.0, 0.62)):
        ell(img, cx + dx * r - r * rr * 0.78, cy + dy * r - r * rr, cx + dx * r + r * rr * 0.78,
            cy + dy * r + r * rr, fill=col, alpha=al)
        dot_on(img, cx + dx * r - r * rr * 0.28, cy + dy * r - r * rr * 0.42, r * 0.12, WHITE, al * 0.5)


def _ikon_ular_kecil(img, cx, cy, ln, ang, col, al=1.0):
    pts = []
    for i in range(5):
        s2 = i / 4.0
        pts.append((cx + math.cos(ang) * ln * (s2 - 0.5) - math.sin(ang) * 5 * math.sin(s2 * 6.0),
                    cy + math.sin(ang) * ln * (s2 - 0.5) + math.cos(ang) * 5 * math.sin(s2 * 6.0)))
    ular(img, pts, al, lebar=max(3.2, ln * 0.11), col=col, lidah=False)


def _dunia_dua(im):
    _langit(im, 640)
    _bukit(im, 640)
    # kartu kertas besar
    rrect_on(im, 92, 250, 988, 862, 46, mix(CREAM, INK, 0.10), 1.0)
    rrect_on(im, 78, 236, 974, 848, 46, WHITE, 1.0)
    line_on(im, (540, 276), (540, 812), mix(CREAM, INK, 0.16), 3, 1.0)
    for (cx, lbl) in ((306, "BERTELUR"), (774, "MELAHIRKAN")):
        paste_c(im, cx, 300, lbl, font(D.FS, 32), mix(INK, MUTED, 0.20), 1.0)
    paste_c(im, 306, 756, "telur di sarang", font(D.FM, 24), mix(INK, MUTED, 0.55), 1.0)
    paste_c(im, 774, 756, "anak lahir langsung", font(D.FM, 24), mix(INK, MUTED, 0.55), 1.0)
    # garis waktu 12 bulan (di atas tepi kertas)
    rrect_on(im, 78, 874, 974, 1016, 26, WHITE, 0.98)
    for i in range(12):
        x = 132 + i * 70
        line_on(im, (x, 908), (x, 962), mix(CREAM, INK, 0.20), 2, 0.9)
        paste_c(im, x, 986, "JFMAMJJASOND"[i], font(D.FM, 20), mix(INK, MUTED, 0.55), 0.9)
    line_on(im, (110, 930), (944, 930), mix(CREAM, INK, 0.24), 3, 0.9)


def sc_dua_cara(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0   # dunia digambar penuh: match/morph = potongan murni, tanpa kilat krem
    c = cues(sc, dur, CUES["dua_cara60"])
    img.paste(_base("dua", _dunia_dua), (0, 0))
    _hujan_lapis(img, tl, ("jauh",), 0, 1080, 60, 1060, 0.45 * al)
    # KIRI: bertelur — kumparan + telur
    q1 = 0.62 + 0.38 * esm((tl - c["bertelur"]) / 0.6)
    if q1 > 0.01:
        pts = []
        for i in range(46):
            tq = i / 45.0 * q1
            ang = -1.2 + tq * 7.4
            rr = 34 + 116 * tq
            pts.append((300 + rr * math.cos(ang), 520 + rr * 0.92 * math.sin(ang)))
        ular(img, pts, 0.92 * al, lebar=15, col=mix(TEAL_D, INK, 0.22), lidah=False, sisik=False)
        _ikon_telur(img, 300, 520, 44, mix(CREAM, KUNING, 0.30), q1 * al)
        for i in range(3):
            ring_on(img, 300, 520, 96 + i * 16, mix(KUNING, WHITE, 0.4), 2,
                    q1 * al * (0.30 + 0.2 * math.sin(tg * 2.4 + i)))
    # KANAN: melahirkan — induk + 3 anakan keluar
    q2 = 0.62 + 0.38 * esm((tl - c["melahirkan"]) / 0.6)
    if q2 > 0.01:
        pts = []
        for i in range(20):
            s2 = i / 19.0
            pts.append((636 + 190 * s2, 470 + 52 * math.sin(s2 * 3.1) + 46 * s2))
        ular(img, pts, 0.92 * q2 * al, lebar=16, col=mix(NAVY3, TEAL_D, 0.20), lidah=False)
        dot_on(img, 636 + 190, 470 + 46 + 52 * math.sin(3.1), 7, mix(NAVY3, INK, 0.3), 0.9 * al)
        for i, (ang, ln) in enumerate(((0.66, 98), (1.08, 76), (1.58, 60))):
            tq = esm((tl - (0.55 + i * 0.28)) / 0.55)
            if tq > 0:
                bx, by = 818 + i * 6, 522 + i * 10
                _ikon_ular_kecil(img, bx + math.cos(ang) * 46 * tq, by + math.sin(ang) * 46 * tq,
                                 ln * tq, ang, mix(NAVY3, TEAL_D, 0.25), al * 0.95)
    # garis waktu: dua pola berbeda
    for i in range(4):
        x = 132 + (1 + i) * 70
        q = seg(tl, c["berbiak"] + i * 0.10, c["berbiak"] + 0.4 + i * 0.1)
        if q > 0:
            dot_on(img, x, 910, 10 * q, mix(accent, INK, 0.20), al)
    for i, m in enumerate((3, 5, 9)):
        xx = 132 + m * 70
        q = seg(tl, c["menetas"] + i * 0.12, c["menetas"] + 0.45 + i * 0.12)
        if q > 0:
            ring_on(img, xx, 950, 12 * q, mix(AMBER2, INK, 0.25), 5, al)
    # cap "TIDAK SEREMPAK"
    qs = esm((tl - c["serempak"]) / 0.5)
    if qs > 0.01:
        lay = Image.new("RGBA", (360, 110), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        rrect_on(lay, 4, 4, 356, 106, 14, mix(accent, WHITE, 0.55), 0.95, outline=accent, width=3)
        _trk = D.TRACK
        D.TRACK = False          # koordinat lokal layer: jangan dicatat sebagai teks kanvas
        paste_c(lay, 180, 55, "TIDAK SEREMPAK", font(D.FS, 30), mix(accent, INK, 0.25), 1.0)
        D.TRACK = _trk
        lay = lay.rotate(-6, resample=Image.BICUBIC, expand=True)
        a = lay.getchannel("A").point(lambda v: int(v * qs * al))
        img.paste(lay, (300, 1050), a)
    _paper(img, 1.0, SUMBER, y0=1088, y1=1320)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    at = 1.0   # judul bertahan sampai potongan (tanpa kedip kosong)
    teks(img, sc, accent, tl, at, 0.20, fsz=62, y=Y_TXT)


# ================================================================ 5. F4 · JALUR MASUK
def _dunia_jalur(im):
    """Denah rumah dari atas (potongan): dinding tebal, ruang, perabot, titik masuk."""
    _grad(im, 0, 1200, mix(SOIL1, INK, 0.10), mix(SOIL1, CREAM, 0.30), 70)
    for i in range(40):
        x, y = _rnd(i, 1) * 1080, _rnd(i, 2) * 1180
        ell(im, x - 10, y - 5, x + 10, y + 5, fill=mix(SOIL1, OLIVE, 0.35), alpha=0.35)
    # bayangan + dinding
    rrect_on(im, 186, 316, 906, 986, 26, mix(SOIL3, INK, 0.35), 0.55)
    rrect_on(im, 170, 300, 890, 970, 24, mix(CREAM, WHITE, 0.30), 1.0)
    rrect_on(im, 198, 328, 862, 942, 12, WHITE, 1.0)
    rrect_on(im, 198, 328, 862, 942, 12, mix(CREAM, INK, 0.10), 1.0, outline=None)
    rrect_on(im, 210, 340, 850, 930, 8, mix(CREAM, WHITE, 0.55), 1.0)
    # dinding dalam
    line_on(im, (560, 340), (560, 700), mix(CREAM, INK, 0.30), 16, 1.0)
    line_on(im, (210, 700), (560, 700), mix(CREAM, INK, 0.30), 16, 1.0)
    # celah: pintu (bawah), ventilasi (atas), saluran (kanan)
    rrect_on(im, 492, 916, 600, 966, 4, mix(SOIL2, INK, 0.10), 1.0)
    rrect_on(im, 492, 940, 600, 966, 4, mix(CREAM, KUNING, 0.30), 0.95)
    rrect_on(im, 328, 292, 378, 340, 3, mix(SOIL2, INK, 0.10), 1.0)
    for i in range(3):
        line_on(im, (334 + i * 14, 300), (334 + i * 14, 334), mix(CREAM, INK, 0.35), 3, 0.7)
    rrect_on(im, 888, 792, 918, 830, 3, mix(SOIL2, INK, 0.10), 1.0)
    # saluran pembuangan di kanan
    rrect_on(im, 850, 792, 926, 828, 8, mix(INK, MUTED, 0.35), 0.95)
    for i in range(4):
        line_on(im, (868 + i * 14, 800), (868 + i * 14, 820), mix(CREAM, WHITE, 0.5), 3, 0.8)
    # perabot: sofa, meja, tumpukan karung
    rrect_on(im, 250, 400, 470, 500, 18, mix(TEAL, CREAM, 0.55), 1.0)
    rrect_on(im, 262, 412, 458, 470, 12, mix(TEAL, CREAM, 0.35), 1.0)
    ell(im, 330, 630, 470, 690, fill=mix(SOIL2, CREAM, 0.55), alpha=1.0)
    for k in range(3):
        ell(im, 336, 636 + k * 14, 464, 664 + k * 14, outline=mix(SOIL2, CREAM, 0.20), width=2,
            alpha=0.45)
    # kehangatan dalam rumah (lampu meja) + kesan kering
    V._glow11(im, 690, 470, 220, KUNING, 0.16)
    rrect_on(im, 596, 470, 700, 486, 5, mix(SOIL2, INK, 0.10), 0.85)
    rrect_on(im, 640, 486, 656, 560, 4, mix(SOIL2, INK, 0.10), 0.85)
    poly_on(im, [(618, 470), (678, 470), (658, 424), (638, 424)], mix(CREAM, KUNING, 0.35), 0.95)
    for i in range(3):
        rrect_on(im, 640 + i * 26, 600 + i * 8, 730 + i * 26, 690 + i * 8, 8,
                 mix(AMBER2, CREAM, 0.45), 1.0)
    # tikus (mangsa) di luar dekat saluran: badan + telinga + ekor
    ell(im, 968, 726, 1006, 752, fill=mix(NAVY3, MUTED, 0.25), alpha=0.92)
    dot_on(im, 978, 728, 5.5, mix(NAVY3, MUTED, 0.15), 0.95)
    ell(im, 968, 716, 984, 730, fill=mix(NAVY3, MUTED, 0.20), alpha=0.9)
    dot_on(im, 1002, 736, 2.4, mix(CREAM, KUNING, 0.3), 0.9)
    for k in range(7):
        line_on(im, (964 - k * 7, 746 + 3 * math.sin(k * 0.8)), (970 - k * 7, 744 + 3 * math.sin(k * 0.8 + 0.6)),
                mix(NAVY3, MUTED, 0.30), 2.6, 0.7)
    # rumput & genangan di luar
    _grass(im, 986, 60, 420, mix(OLIVE, TEAL_D, 0.35), 0.5, n=18, h=44, seed=4)
    for (px, py, rx) in ((140, 1000, 90), (940, 1020, 70)):
        ell(im, px - rx, py - 12, px + rx, py + 12, fill=mix(WET, SKY2, 0.45), alpha=0.7)


def sc_jalur_masuk(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0   # dunia digambar penuh: match/morph = potongan murni, tanpa kilat krem
    c = cues(sc, dur, CUES["jalur_masuk60"])
    img.paste(_base("jalur", _dunia_jalur), (0, 0))
    _hujan_lapis(img, tl, ("jauh",), 0, 168, 40, 1180, 0.34 * al)
    _hujan_lapis(img, tl, ("mid",), 900, 1080, 260, 1180, 0.30 * al)
    AMB = mix(AMBER2, INK, 0.10)
    GRY = mix(INK, MUTED, 0.35)
    # Semua jalur sudah terbaca sejak frame pertama; beat hanya MENEGASKAN.
    def qq(t0, hadir=0.62):
        return hadir + (1.0 - hadir) * esm((tl - t0) / 0.5)

    # 1 celah pintu (bawah)
    q = qq(c["celah"])
    panah_tekuk(img, (700, 1078), (566, 962), q, AMB, 10, (0.55 + 0.45 * q) * al, -0.20)
    _nomor(img, 566, 946, "1", AMB, q * al)

    # 2 saluran pembuangan (kanan)
    q = qq(c["saluran"], 0.55)
    panah_tekuk(img, (1058, 878), (924, 818), q, mix(TEAL, INK, 0.15), 9, (0.5 + 0.5 * q) * al, 0.2)
    _nomor(img, 900, 874, "2", mix(TEAL, INK, 0.15), q * al)

    # 3 ventilasi (atas)
    q = qq(c["pembuangan"], 0.55)
    panah_tekuk(img, (300, 150), (346, 292), q, mix(NAVY, TEAL, 0.25), 9, (0.5 + 0.5 * q) * al, 0.16)
    _nomor(img, 352, 300, "3", mix(NAVY, TEAL, 0.25), q * al)

    # 4 tumpukan barang
    q = qq(c["tumpukan"], 0.55)
    ring_on(img, 700, 640, 62 * eob(q) + 30, mix(AMBER2, INK, 0.15), 3, 0.55 * q * al)
    _nomor(img, 790, 600, "4", mix(AMBER2, INK, 0.20), q * al)

    # 5 mangsa (tikus)
    q = qq(c["tikus"], 0.55)
    ring_on(img, 990, 726, 44 * eob(q) + 18, GRY, 3, 0.5 * q * al)

    # legenda nomor: plan tetap bersih, keterangan dibaca sekali jalan
    _legenda(img, 540, 1018, (("1", "CELAH PINTU", AMB), ("2", "SALURAN", mix(TEAL, INK, 0.15)),
                              ("3", "VENTILASI", mix(NAVY, TEAL, 0.25)), ("4", "TUMPUKAN", mix(AMBER2, INK, 0.20)),
                              ("5", "MANGSA", GRY)), al)
    # hujan masuk ke celah pintu (garis air)
    if tl > c["celah"]:
        for i in range(3):
            line_on(img, (528 + i * 16, 1010), (532 + i * 16, 970), mix(SKY2, TEAL, 0.35), 3, 0.5 * al)
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    at = 1.0   # judul bertahan sampai potongan (tanpa kedip kosong)
    teks(img, sc, accent, tl, at, 0.20, fsz=60, y=Y_TXT)


# ================================================================ 6. F5 · TIGA SKENARIO
def _ikon_air(img, cx, cy, r, col, al=1.0):
    for k in range(3):
        pts = []
        for i in range(11):
            x = cx - r + 2 * r * i / 10.0
            pts.append((x, cy - r * 0.28 + k * r * 0.34 + r * 0.12 * math.sin(i * 0.9 + k)))
        for i in range(len(pts) - 1):
            line_on(img, pts[i], pts[i + 1], col, max(2.0, r * 0.10), al)


def _ikon_pintu(img, cx, cy, r, col, al=1.0):
    rrect_on(img, cx - r * 0.66, cy - r * 0.90, cx + r * 0.66, cy + r * 0.90, 3, col, al, outline=None)
    rrect_on(img, cx - r * 0.50, cy - r * 0.74, cx + r * 0.50, cy + r * 0.74, 2,
             mix(CREAM, WHITE, 0.45), al * 0.30)
    dot_on(img, cx + r * 0.30, cy + r * 0.08, r * 0.08, col, al)
    # celah di bawah pintu (jalur masuk)
    rrect_on(img, cx - r * 0.50, cy + r * 0.74, cx + r * 0.50, cy + r * 0.90, 2,
             mix(AMBER2, INK, 0.10), al * 0.95)


# singkatan supaya kompatibel bila modul lama mengimpor nama ini
def _kartu(img, x, y, w, h, al=1.0, lift=1.0):
    rrect_on(img, x, y + 10, x + w, y + h + 10, 26, mix(CREAM, INK, 0.16), 0.35 * al)
    rrect_on(img, x, y, x + w, y + h, 26, WHITE, al)
    rrect_on(img, x + 8, y + 8, x + w - 8, y + h - 8, 20, mix(CREAM, WHITE, 0.55), al * 0.55)


def _legenda(img, cx, cy, items, al=1.0):
    f = font(D.FS, 21)
    widths = [tw(t, f) + 46 for _, t, _ in items]
    gap = 12
    total = sum(widths) + gap * (len(items) - 1)
    x = cx - total / 2.0
    rrect_on(img, x - 16, cy - 30, x + total + 16, cy + 30, 30, mix(CREAM, WHITE, 0.30), 0.94 * al,
             outline=mix(CREAM, INK, 0.18), width=2)
    for (num, txt, col), w in zip(items, widths):
        dot_on(img, x + 17, cy, 13, mix(col, WHITE, 0.55), 0.95 * al)
        paste_c(img, x + 17, cy - 1, num, font(D.FB, 15), mix(col, INK, 0.25), al)
        paste_c(img, x + 38 + tw(txt, f) / 2, cy, txt, f, mix(INK, MUTED, 0.18), 0.95 * al)
        x += w + gap


def _nomor(img, cx, cy, txt, col, al=1.0):
    """Lingkaran nomor jalur: tegas dibaca di layar tegak."""
    dot_on(img, cx, cy, 25, mix(CREAM, WHITE, 0.35), 0.95 * al)
    ring_on(img, cx, cy, 25, col, 3.2, 0.9 * al)
    paste_c(img, cx, cy - 1, txt, font(D.FB, 27), col, al)


def _dunia_tiga(im):
    """Halaman basah: langit, bukit jauh, tanah sampai tepi kertas (tanpa sambungan)."""
    _grad(im, 0, 520, SKY1, mix(SKY2, TEAL, 0.14), 60)
    for (cx, cy, rx, ry, a) in ((720, 180, 280, 24, 0.26), (240, 128, 210, 20, 0.18)):
        for k in range(3):
            q = k / 2.0
            ell(im, cx - rx, cy - ry * (1 - 0.4 * q), cx + rx, cy + ry * (1 - 0.4 * q),
                fill=mix(SKY2, WHITE, 0.35 + 0.3 * q), alpha=a * (0.5 - 0.15 * q))
    _bukit(im, 520)
    _tanah(im, 560, 1.0, mix(WET, SKY2, 0.26), (120, 900))
    for k in range(5):
        ell(im, 120 + k * 210, 700 + 40 * math.sin(k * 1.7), 120 + k * 210 + 150,
            762 + 40 * math.sin(k * 1.7), fill=mix(SKY2, TEAL, 0.55), alpha=0.16)
    for i in range(46):
        x = _rnd(i, 3) * 1080
        y = 600 + _rnd(i, 4) * 420
        line_on(im, (x, y), (x + 16 + 20 * _rnd(i, 5), y - 3), mix(OLIVE, TEAL_D, 0.30), 2.4, 0.22)


def sc_tiga_skenario(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0   # dunia digambar penuh: match/morph = potongan murni, tanpa kilat krem
    c = cues(sc, dur, CUES["tiga_skenario60"])
    img.paste(_base("tiga", _dunia_tiga), (0, 0))
    _hujan_lapis(img, tl, ("jauh", "mid"), 0, 1080, 40, 1040, 0.75 * al)
    W3, H3 = 272, 296
    kartu = (("1", "GENANGAN", c["genangan"], _ikon_air, mix(TEAL, INK, 0.18), "air naik"),
             ("2", "PENETASAN", c["penetasan"], None, mix(TERRA, INK, 0.16), "anakan muncul"),
             ("3", "AKSES", c["celah"], _ikon_pintu, mix(OLIVE, INK, 0.22), "celah & mangsa"))
    for i, (num, lbl, t0, ikon, col, ket) in enumerate(kartu):
        q = 0.30 + 0.70 * esm((tl - t0 + 0.25) / 0.55)
        k = eob(min(1.0, q / 0.99))
        x = 62 + i * 318
        y = 300 + (1 - k) * 54
        _kartu(img, x, y, W3, H3, al, k)
        cx, cy = x + W3 / 2, y + 118
        dot_on(img, x + 34, y + 34, 17, mix(col, WHITE, 0.60), 0.95 * al)
        paste_c(img, x + 34, y + 33, num, font(D.FB, 19), mix(col, INK, 0.20), al)
        if ikon:
            ikon(img, cx, cy, 44, col, min(1.0, q * 1.5) * al)
        else:
            _ikon_telur(img, cx, cy, 44, mix(CREAM, KUNING, 0.26), min(1.0, q * 1.5) * al)
        paste_c(img, cx, y + 212, lbl, font(D.FB, 25), mix(col, INK, 0.24), 0.94 * al)
        paste_c(img, cx, y + 248, ket, font(D.FM, 21), mix(INK, MUTED, 0.48), 0.90 * al)
        # garis turun ke titik temu
        qq = 1.0
        if qq > 0.01:
            p0 = (cx, y + H3 + 6)
            p1 = (540 + (cx - 540) * 0.10, 780)
            for j in range(16):
                s0, s1 = j / 16.0, (j + 1) / 16.0
                if s1 > qq:
                    break
                a0 = _bez(p0, p1, 0.09, s0)
                a1 = _bez(p0, p1, 0.09, s1)
                line_on(img, a0, a1, mix(col, INK, 0.10), 5, (0.42 + 0.42 * esm((tl - (t0 + 0.15)) / 0.6)) * al)
    # titik temu: berlian + tanda tanya
    qd = 0.30 + 0.70 * esm((tl - c["tiga"]) / 0.55)
    if qd > 0.01:
        k = eob(qd)
        cy = 872
        rr = 92 * k
        poly_on(img, [(540, cy - rr), (540 + rr, cy), (540, cy + rr), (540 - rr, cy)],
                mix(accent, INK, 0.12), 0.96 * al)
        poly_on(img, [(540, cy - rr), (540 + rr * 0.32, cy - rr * 0.30), (540 + rr, cy)],
                mix(accent, WHITE, 0.20), 0.5 * al)
        paste_c(img, 540, cy - 6, "?", font(D.FB, 104 * (0.7 + 0.3 * k)), WHITE, 0.95 * al)
        for i in range(3):
            ph = (tg * 0.45 + i / 3.0) % 1.0
            ring_on(img, 540, cy, rr + 24 + 34 * ph, mix(accent, WHITE, 0.35), 3, 0.32 * al * (1 - ph))
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    at = 1.0   # judul bertahan sampai potongan (tanpa kedip kosong)
    teks(img, sc, accent, tl, at, 0.20, fsz=62, y=Y_TXT)


# ================================================================ 7. F6 · AMAN
def _orang(img, x, y, s, col, al=1.0):
    """Siluet orang dewasa (kepala, bahu, badan, dua kaki) — sederhana, tanpa detail wajah."""
    dot_on(img, x, y - 152 * s, 26 * s, col, al)
    rrect_on(img, x - 30, y - 128 * s, x + 30, y - 118 * s, 5 * s, mix(col, CREAM, 0.20), al * 0.8)
    poly_on(img, [(x - 34 * s, y - 118 * s), (x + 34 * s, y - 118 * s), (x + 44 * s, y - 24 * s),
                  (x - 44 * s, y - 24 * s)], col, al)
    rrect_on(img, x - 38 * s, y - 128 * s, x - 10 * s, y - 20 * s, 12 * s, col, al)
    rrect_on(img, x + 10 * s, y - 128 * s, x + 38 * s, y - 20 * s, 12 * s, col, al)
    line_on(img, (x, y - 116 * s), (x, y - 30 * s), mix(col, CREAM, 0.28), 2.0, al * 0.55)
    rrect_on(img, x - 34 * s, y - 30 * s, x - 6 * s, y, 8 * s, mix(col, INK, 0.10), al)
    rrect_on(img, x + 6 * s, y - 30 * s, x + 34 * s, y, 8 * s, mix(col, INK, 0.10), al)


def _tile(img, x, y, s, ok, col, al):
    rrect_on(img, x, y, x + s, y + s, 24, WHITE, al)
    rrect_on(img, x + 7, y + 7, x + s - 7, y + s - 7, 19, mix(CREAM, col, 0.10), al * 0.40)
    if not ok:
        silang(img, x + s - 30, y + 30, 15, mix(RED, INK, 0.08), al * 0.95, 1.0)
    else:
        dot_on(img, x + s - 30, y + 30, 15, mix(GREEN, WHITE, 0.35), al * 0.95)
        line_on(img, (x + s - 37, y + 30), (x + s - 32, y + 36), mix(GREEN, INK, 0.25), 3.4, al)
        line_on(img, (x + s - 32, y + 36), (x + s - 22, y + 23), mix(GREEN, INK, 0.25), 3.4, al)


def _dunia_aman(im):
    """Halaman basah setelah hujan: horizon rendah, pagar jauh, tanah sampai tepi kertas."""
    _grad(im, 0, 470, SKY1, mix(SKY2, TEAL, 0.16), 60)
    for (cx, cy, rx, ry, a) in ((760, 160, 260, 22, 0.26), (260, 104, 200, 18, 0.18)):
        for k in range(3):
            q = k / 2.0
            ell(im, cx - rx, cy - ry * (1 - 0.4 * q), cx + rx, cy + ry * (1 - 0.4 * q),
                fill=mix(SKY2, WHITE, 0.35 + 0.3 * q), alpha=a * (0.5 - 0.15 * q))
    _bukit(im, 470)
    _tanah(im, 528, 1.0, mix(WET, SKY2, 0.28), (170, 900))
    for i in range(7):
        x = 20 + i * 168
        rrect_on(im, x, 548, x + 9, 636, 3, mix(SOIL2, INK, 0.34), 0.55)
    line_on(im, (8, 570), (1074, 564), mix(SOIL2, INK, 0.34), 4, 0.45)
    line_on(im, (8, 598), (1074, 592), mix(SOIL2, INK, 0.34), 3, 0.35)
    _grass(im, 706, 0, 1080, mix(OLIVE, TEAL_D, 0.36), 0.62, n=46, h=58, seed=7)
    _semak(im, 1016, 700, 0.70, 0.9)
    for k in range(4):
        ell(im, 60 + k * 280, 760 + 34 * math.sin(k * 1.4), 220 + k * 280, 806 + 34 * math.sin(k * 1.4),
            fill=mix(WET, SKY2, 0.55), alpha=0.55)
    for (bx, by, bs) in ((322, 300, 1.0), (368, 278, 0.8), (412, 296, 0.7)):
        line_on(im, (bx - 12 * bs, by), (bx, by - 5 * bs), mix(INK, MUTED, 0.45), 2.4, 0.40)
        line_on(im, (bx, by - 5 * bs), (bx + 12 * bs, by), mix(INK, MUTED, 0.45), 2.4, 0.40)


def sc_aman_ular(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0   # dunia digambar penuh: match/morph = potongan murni, tanpa kilat krem
    c = cues(sc, dur, CUES["aman_ular60"])
    img.paste(_base("aman", _dunia_aman), (0, 0))
    _hujan_lapis(img, tl, ("jauh",), 0, 1080, 40, 700, 0.34 * al)
    # orang + ular berjarak (jarak sebagai pesan utama)
    qo = 0.20 + 0.80 * esm((tl - c["melihat"] + 0.3) / 0.5)
    if qo > 0.01:
        _shadow(img, 232, 700, 52, 10, 0.16 * qo * al)
        _orang(img, 232, 700, 0.86, mix(NAVY3, TEAL_D, 0.16), qo * al)
    qs = 0.20 + 0.80 * esm((tl - c["menjauh"] + 0.3) / 0.6)
    if qs > 0.01:
        pts = []
        for i in range(18):
            s2 = i / 17.0
            pts.append((700 + 112 * s2, 700 - 58 * math.sin(s2 * 1.9) + 6 * math.sin(tg * 1.4 + s2 * 4)))
        ular(img, pts, qs * al * 0.96, lebar=13, col=mix(NAVY3, TEAL_D, 0.20),
             lidah=(math.sin(tl * 3.3) > 0.6))
    # pita jarak + label
    qj = 0.25 + 0.75 * esm((tl - c["jauhkan"] + 0.25) / 0.7)
    if qj > 0.01:
        x0, x1, yy = 318, 660, 654
        line_on(img, (x0, yy), (x0 + (x1 - x0) * qj, yy), mix(accent, INK, 0.22), 4, 0.9 * al)
        for i in range(9):
            xx = x0 + (x1 - x0) * i / 8.0
            if xx > x0 + (x1 - x0) * qj:
                break
            line_on(img, (xx, yy - 8), (xx, yy + 8), mix(accent, INK, 0.22), 3, 0.8 * al)
        paste_c(img, 489, 620, "JAUH", font(D.FS, 25), mix(accent, INK, 0.22), 0.95 * al)
    # peringatan pertolongan pertama (digambar SETELAH _paper, di zona kertas)
    qf = esm((tl - c["torniket"]) / 0.45)
    # empat tindakan: satu baris penuh
    items = (("JANGAN", "PUKUL", c["melihat"] + 0.55, "pukul", False),
             ("JANGAN", "TANGKAP", c["melihat"] + 0.85, "tangkap", False),
             ("HUBUNGI", "DAMKAR", c["hubungi"], "telp", True),
             ("SEGERA KE", "FASKES", c["fasilitas"], "medis", True))
    for i, (l1, l2, t0, ikon, ok) in enumerate(items):
        q = 0.35 + 0.65 * esm((tl - t0 + 0.55) / 0.45)
        if q <= 0.01:
            continue
        col = mix(GREEN, INK, 0.20) if ok else mix(RED, INK, 0.10)
        s_ = 196
        x = 40 + i * 250
        y = 828 + (1 - eob(min(1.0, q))) * 22
        _tile(img, x, y, s_, ok, col, min(1.0, q * 1.4) * al)
        cx, cy = x + s_ / 2, y + 74
        k = min(1.0, q * 1.5)
        if ikon == "telp":
            rrect_on(img, cx - 17, cy - 30, cx + 17, cy + 26, 7, col, k * al)
            rrect_on(img, cx - 12, cy - 23, cx + 12, cy + 15, 4, mix(CREAM, WHITE, 0.4), 0.9 * k * al)
            dot_on(img, cx, cy + 20, 3.0, mix(CREAM, WHITE, 0.3), k * al)
        elif ikon == "medis":
            rrect_on(img, cx - 8, cy - 30, cx + 8, cy + 30, 4, col, k * al)
            rrect_on(img, cx - 30, cy - 8, cx + 30, cy + 8, 4, col, k * al)
        elif ikon == "pukul":
            rrect_on(img, cx - 4, cy - 34, cx + 8, cy + 6, 4, col, k * al)
            ell(img, cx - 21, cy - 2, cx + 9, cy + 24, fill=col, alpha=k * al)
        else:
            for j in range(4):
                _arc(img, cx, cy, 18 + j * 6, 0, math.pi, col, 3, k * al * 0.55)
            line_on(img, (cx - 24, cy + 4), (cx + 24, cy + 24), col, 4, k * al)
        paste_c(img, cx, y + 132, l1, font(D.FS, 22), mix(col, INK, 0.28), k * al)
        paste_c(img, cx, y + 162, l2, font(D.FS, 22), mix(col, INK, 0.28), k * al)
    _paper(img, 1.0, SUMBER)
    _catatan_medis(img, qf, al)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    at = 1.0   # judul bertahan sampai potongan (tanpa kedip kosong)
    teks(img, sc, accent, tl, at, 0.20, fsz=60, y=Y_TXT)


# ================================================================ 8. OUTRO · LOOP AMBANG
def sc_loop_ambang(img, d, sc, tl, dur, tg, accent, al, dy):
    """Frame akhir = frame 0 intro: dunia sama, tanpa ular, fase hujan dihitung mundur ke nol."""
    M.set_keluar(tl, dur, ada_lanjutan=False)
    al = 1.0
    c = cues(sc, dur, CUES["loop_ambang60"])
    img.paste(_base("ambang", _dunia_ambang), (0, 0))
    u = tl - dur                      # di tl == dur -> 0 (identik dengan intro t=0)
    _hujan_lapis(img, u, ("jauh", "mid"), 0, 1080, 150, 1060, 0.95 * al)
    _hujan_lapis(img, u, ("dekat",), 0, 1080, 120, 1090, 0.85 * al)
    _titisan_genteng(img, u, (214, 372, 668, 834), 730, 1068, al)
    _riak(img, 250, 1128, u * 0.8, 0.45 * al, 4, 40)
    _riak(img, 812, 1122, u * 0.8 + 0.5, 0.42 * al, 4, 34)
    _kabut(img, 986, 120, 0.085 * al)
    lampu = 0.86 + 0.14 * math.sin(u * 1.7)
    V._glow11(img, 540, 1006, 92, KUNING, 0.20 * lampu * al)
    # katak kecil di undakan: satu-satunya gerak baru (hadiah untuk yang mengulang)
    q = esm((tl - c["muncul"]) / 0.35) * (1 - esm((tl - c["muncul"] - 0.55) / 0.30))
    if q > 0.01:
        fx, fy = 604 + 26 * esm((tl - c["muncul"] - 0.55) / 0.30), 1064
        ell(img, fx - 15, fy - 13, fx + 15, fy, fill=mix(OLIVE, TEAL_D, 0.35), alpha=q * al)
        dot_on(img, fx - 7, fy - 10, 2.6, INK, q * al)
        dot_on(img, fx + 7, fy - 10, 2.6, INK, q * al)
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    teks(img, sc, accent, tl, al, 0.24, fsz=64, y=Y_TXT)


# ================================================================ CUE & SFX
CUES = {
    "ambang_hujan60": {"hujan": ("hujan", 0.04), "ular": ("Ular", 0.02), "masuk": ("masuk", 0.14),
                       "rumah": ("rumah", 0.26), "selalu": ("selalu", 0.66), "banjir": ("banjir", 0.80)},
    "habitat_tergenang60": {"tergenang": ("tergenang", 0.10), "berpindah": ("berpindah", 0.30),
                            "perlindungan": ("perlindungan", 0.42), "terlihat": ("terlihat", 0.58),
                            "rumahmu": ("rumahmu", 0.68), "banjir": ("banjir", 0.82),
                            "kemungkinan": ("kemungkinan", 0.97)},
    "anakan_sanca60": {"anakan": ("Anakan", 0.03), "sukabumi": ("Sukabumi", 0.14),
                       "dua": ("dua", 0.22), "sanca": ("sanca", 0.31), "ditemukan": ("ditemukan", 0.40),
                       "desember": ("Desember", 0.52), "brin": ("BRIN", 0.64),
                       "penetasan": ("penetasan", 0.76), "bukti": ("bukti", 0.86), "hujan": ("hujan", 0.96)},
    "dua_cara60": {"bertelur": ("bertelur", 0.10), "melahirkan": ("melahirkan", 0.22),
                   "waktu": ("Waktu", 0.34), "berbiak": ("berbiak", 0.40), "menetas": ("menetas", 0.47),
                   "berbeda": ("berbeda", 0.55), "hujan": ("hujan", 0.66), "tombol": ("tombol", 0.74),
                   "spesies": ("spesies", 0.86), "serempak": ("serempak", 0.96)},
    "jalur_masuk60": {"jalur": ("Jalur", 0.03), "lingkungan": ("lingkungan", 0.12),
                      "celah": ("Celah", 0.24), "pintu": ("pintu", 0.28), "saluran": ("saluran", 0.36),
                      "pembuangan": ("pembuangan", 0.42), "tumpukan": ("tumpukan", 0.51),
                      "barang": ("barang", 0.56), "mangsa": ("mangsa", 0.64),
                      "tikus": ("Tikus", 0.76), "kemungkinan": ("kemungkinan", 0.92)},
    "tiga_skenario60": {"rangkai": ("Rangkai", 0.02), "genangan": ("Genangan", 0.08),
                        "habitat": ("habitat", 0.14), "penetasan": ("penetasan", 0.25),
                        "anakan": ("anakan", 0.34), "celah": ("Celah", 0.42), "akses": ("akses", 0.49),
                        "tiga": ("Tiga", 0.55), "aturan": ("aturan", 0.66),
                        "rumahmu": ("rumahmu", 0.78), "ditutup": ("ditutup", 0.90), "aman": ("aman", 0.97)},
    "aman_ular60": {"melihat": ("melihat", 0.03), "menjauh": ("menjauh", 0.09),
                    "jauhkan": ("Jauhkan", 0.16), "peliharaan": ("peliharaan", 0.26),
                    "dekati": ("dekati", 0.36), "pukul": ("pukul", 0.42),
                    "menangkapnya": ("menangkapnya", 0.48), "hubungi": ("Hubungi", 0.57),
                    "damkar": ("Damkar", 0.61), "penyelamat": ("penyelamat", 0.66),
                    "tergigit": ("tergigit", 0.76), "fasilitas": ("fasilitas", 0.82),
                    "torniket": ("torniket", 0.91), "menyayat": ("menyayat", 0.95),
                    "mengisap": ("mengisap", 0.98)},
    "loop_ambang60": {"jadi": ("Jadi", 0.02), "menentukan": ("menentukan", 0.10),
                      "ular": ("ular", 0.20), "muncul": ("muncul", 0.28),
                      "rumah": ("rumah", 0.36), "hujan": ("hujan", 0.45)},
}
SFX = {
    "ambang_hujan60": {"hujan": ("guntur", 0.40, -0.15), "ular": ("swish", 0.75, -0.12),
                       "masuk": ("tick", 0.75, 0), "rumah": ("pop", 0.60, 0),
                       "selalu": ("tick", 0.65, 0), "banjir": ("thud", 0.95, 0)},
    "habitat_tergenang60": {"tergenang": ("gelembung", 0.65, 0), "berpindah": ("swish", 0.80, 0),
                            "perlindungan": ("pop", 0.55, 0), "terlihat": ("tick", 0.75, 0),
                            "rumahmu": ("thud", 0.70, 0), "banjir": ("whoosh", 0.75, 0),
                            "kemungkinan": ("riser", 0.55, -0.3)},
    "anakan_sanca60": {"anakan": ("morph", 0.70, 0), "sukabumi": ("tick", 0.75, 0),
                       "dua": ("tick", 0.85, 0), "sanca": ("pop", 0.70, 0),
                       "ditemukan": ("thud", 0.80, 0), "desember": ("tick", 0.70, 0),
                       "brin": ("click", 0.70, 0), "penetasan": ("retak", 0.95, -0.05),
                       "bukti": ("swish", 0.65, 0), "hujan": ("angin", 0.60, 0)},
    "dua_cara60": {"bertelur": ("pop", 0.80, 0), "melahirkan": ("pop", 0.85, 0),
                   "waktu": ("tick", 0.70, 0), "berbiak": ("swish", 0.55, 0),
                   "menetas": ("retak", 0.85, 0), "berbeda": ("tick", 0.75, 0),
                   "hujan": ("angin", 0.55, 0), "tombol": ("click", 0.80, 0),
                   "spesies": ("pop", 0.55, 0), "serempak": ("swish", 0.60, 0)},
    "jalur_masuk60": {"jalur": ("whoosh", 0.75, 0), "lingkungan": ("tick", 0.70, 0),
                      "celah": ("door", 0.80, 0), "pintu": ("tick", 0.70, 0),
                      "saluran": ("pop", 0.65, 0), "pembuangan": ("gelembung", 0.55, 0),
                      "tumpukan": ("thud", 0.85, 0), "barang": ("tick", 0.60, 0),
                      "mangsa": ("pop", 0.70, 0), "tikus": ("swish", 0.75, 0),
                      "kemungkinan": ("riser", 0.50, -0.25)},
    "tiga_skenario60": {"rangkai": ("morph", 0.80, 0), "genangan": ("pop", 0.75, 0),
                        "habitat": ("tick", 0.60, 0), "penetasan": ("retak", 0.75, 0),
                        "anakan": ("tick", 0.65, 0), "celah": ("door", 0.80, 0),
                        "akses": ("tick", 0.70, 0), "tiga": ("thump", 1.00, 0),
                        "aturan": ("swish", 0.65, 0), "rumahmu": ("tick", 0.75, 0),
                        "ditutup": ("whoosh", 0.65, 0), "aman": ("kilau", 0.75, 0)},
    "aman_ular60": {"melihat": ("tick", 0.75, 0), "menjauh": ("swish", 0.85, 0),
                    "jauhkan": ("pop", 0.60, 0), "peliharaan": ("tick", 0.60, 0),
                    "dekati": ("tick", 0.70, 0), "pukul": ("gigit", 0.55, 0),
                    "menangkapnya": ("thud", 0.85, 0), "hubungi": ("click", 0.80, 0),
                    "damkar": ("ding", 0.85, 0), "penyelamat": ("tick", 0.60, 0),
                    "tergigit": ("gigit", 0.70, 0), "fasilitas": ("pop", 0.65, 0),
                    "torniket": ("tick", 0.70, 0), "menyayat": ("swish", 0.70, 0),
                    "mengisap": ("swish_up", 0.60, 0)},
    "loop_ambang60": {"jadi": ("morph", 0.60, 0), "menentukan": ("tick", 0.60, 0),
                      "ular": ("swish", 0.55, 0), "muncul": ("pop", 0.55, 0),
                      "rumah": ("thud", 0.65, 0), "hujan": ("angin", 0.60, 0)},
}
BEATS60 = {k: [] for k in CUES}


def events_v12(sc):
    """Event SFX absolut satu adegan -> [(t, jenis, gain)]. Kata-driven, bukan tebakan."""
    vis = sc.get("visual", "")
    if vis not in CUES:
        return []
    c = cues(sc, sc["dur"], CUES[vis])
    out = [(sc["start"] + c[nama] + off, jenis, g) for nama, (jenis, g, off) in SFX.get(vis, {}).items()]
    if str(sc.get("trans") or "").lower() == "morph":
        out.append((sc["start"] - 0.08, "morph", 0.55))
    return out


# === REGISTRY ===
VISUALS60 = {"ambang_hujan60": sc_ambang_hujan, "habitat_tergenang60": sc_habitat_tergenang,
             "anakan_sanca60": sc_anakan_sanca, "dua_cara60": sc_dua_cara,
             "jalur_masuk60": sc_jalur_masuk, "tiga_skenario60": sc_tiga_skenario,
             "aman_ular60": sc_aman_ular, "loop_ambang60": sc_loop_ambang}


def _selftest():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), CREAM)
    d = ImageDraw.Draw(img)
    for n, fn in VISUALS60.items():
        sc = {"id": "intro" if n.startswith(("ambang", "loop")) else "f1", "visual": n, "start": 10.0,
              "dur": 14.0, "badge": "HUJAN PERTAMA", "hl": "HUJAN", "lines": ["ULAR MASUK RUMAH", "SAAT HUJAN?"]}
        for tl in (0.0, 0.12, 0.5, 2.0, 5.0, 8.0, 12.0, 13.5, 13.98):
            fn(img, d, sc, tl, 14.0, 10.0 + tl, D.hexc("#2F6F63"), 1.0, 0.0)
        assert events_v12(sc), n
    print(f"selftest ep51b: {len(VISUALS60)} visual OK ({sum(len(v) for v in CUES.values())} cue, "
          f"{sum(len(v) for v in SFX.values())} SFX)")


def daftar():
    V.BEATS.update(BEATS60)
    D.VISUALS.update(VISUALS60)
    M.EVENTS12.update({k: events_v12 for k in CUES})


daftar()


if __name__ == "__main__":
    _selftest()
