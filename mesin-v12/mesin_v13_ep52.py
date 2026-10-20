#!/usr/bin/env python3
"""Ep52 — "CEGUKAN" (mesin v14). Delapan dunia anatomi: jam, diafragma, saraf, mitos, durasi, janin, tindakan.

Naskah mengikuti RISET ULANG 20 Okt 2026 (analisis/EP52_RISET_ULANG_20_OKT_2026.md):
mekanisme refleks, jalur vagus/frenikus, batas durasi 48 jam / 1 bulan, janin, tindakan aman.
Klaim yang tidak dipakai: "kaget menyembuhkan", angka prevalensi Indonesia.

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
from mesin_v12 import (cues, chip, silang, esm, KUNING, NAVY, ORANYE)

# ---------------------------------------------------------------- tata letak dunia
Y_TXT = 1318
Y_FOOT = 1204
SUMBER = "Sumber: NIH · Cleveland Clinic · Guinness"

TEAL = (38, 106, 96)
TEAL_D = (26, 74, 68)
TERRA = (176, 84, 56)
TERRA_D = (128, 56, 38)
AMBER2 = (198, 142, 54)
OLIVE = (108, 120, 78)
NAVY3 = (22, 34, 52)
ROSE = (186, 106, 96)
ROSE_D = (140, 74, 70)
BONE = (238, 231, 216)
SKIN = (226, 208, 188)
SKY1 = (240, 237, 229)
SKY2 = (208, 214, 210)


# ---------------------------------------------------------------- utilitas dasar
def _rnd(i, k=1.0):
    return (math.sin(i * 12.9898 + k * 78.233) * 43758.5453) % 1.0


def _grad(img, y0, y1, c0, c1, n=110):
    dd = ImageDraw.Draw(img)
    span = max(1.0, y1 - y0)
    for i in range(n):
        q = i / (n - 1.0)
        y = y0 + span * q
        y2 = y0 + span * (i + 1) / (n - 1.0) + 1
        dd.rectangle([0, D.S(y), img.size[0], D.S(y2)], fill=mix(c0, c1, q))


def _speck(img, x0, y0, x1, y1, n, col, al, seed=1, r=(1.0, 2.6)):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    for i in range(n):
        x = x0 + _rnd(i + seed * 131, 1) * (x1 - x0)
        y = y0 + _rnd(i + seed * 131, 2) * (y1 - y0)
        rr = r[0] + _rnd(i + seed * 131, 3) * (r[1] - r[0])
        a = int(255 * al * (0.45 + 0.55 * _rnd(i + seed * 131, 4)))
        dd.ellipse([D.S(x - rr), D.S(y - rr), D.S(x + rr), D.S(y + rr)], fill=col + (a,))
    img.paste(lay, (0, 0), lay)


def _shadow(img, cx, cy, rx, ry, al=0.18, col=(48, 46, 44)):
    for k in range(5):
        q = k / 4.0
        ell(img, cx - rx * (1 - 0.16 * q), cy - ry * (1 - 0.30 * q),
            cx + rx * (1 - 0.16 * q), cy + ry * (1 - 0.30 * q),
            fill=col, alpha=al * (0.30 - 0.05 * k))


_SOLID = {}
_SCRIM = {}
_SCRIM_TOP = {}
_PAPER_MASK = {}
_BASE = {}


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


def _paper_mask(y0=1040, y1=1290):
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
    txt = sc.get("catatan")
    if not txt:
        return
    line_on(img, (540 - 42, 1468), (540 + 42, 1468), mix(accent, INK, 0.10), 2.6, 0.55 * al)
    paste_c(img, 540, 1508, txt, font(D.FS, 33), mix(INK, MUTED, 0.28), al * 0.94)


def _catatan_bahaya(img, qf, al=1.0):
    """Pil merah di zona kertas: tiga tanda bahaya (bukan daftar obat)."""
    if qf <= 0.01:
        return
    yy = 1592 + (1 - qf) * 18
    rrect_on(img, 96, yy - 34, 984, yy + 34, 30, mix(RED, CREAM, 0.86), 0.95 * qf * al)
    ring_on(img, 140, yy, 17, mix(RED, INK, 0.10), 2.4, 0.9 * qf * al)
    silang(img, 140, yy, 9, mix(RED, INK, 0.10), 0.9 * qf * al, 1.0)
    paste_c(img, 566, yy, "Nyeri dada · lemas · sulit bicara", font(D.FS, 26),
            mix(RED, INK, 0.12), qf * al)


def _fit(text, fsz, maxw):
    w = tw(text, font(D.FB, fsz))
    return fsz * min(1.0, maxw / max(1.0, w))


def teks(img, sc, accent, tl, al, t0, text=None, hl=None, fsz=62, y=Y_TXT, maxw=900):
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


def _kartu(img, x, y, w, h, al=1.0, r=26):
    rrect_on(img, x, y + 10, x + w, y + h + 10, r, mix(CREAM, INK, 0.16), 0.32 * al)
    rrect_on(img, x, y, x + w, y + h, r, WHITE, al)
    rrect_on(img, x + 8, y + 8, x + w - 8, y + h - 8, int(r * 0.78), mix(CREAM, WHITE, 0.55), al * 0.55)


def _vignette(img, al=1.0):
    """Bingkai lembut di tepi dunia: mata diarahkan ke tengah, bukan ke tepi kosong."""
    for k in range(6):
        q = k / 5.0
        line_on(img, (0, 0), (1080, 0), mix(CREAM, INK, 0.10), 26 - 4 * k, 0.045 * (1 - q) * al)
        line_on(img, (0, 1030), (1080, 1030), mix(CREAM, INK, 0.10), 26 - 4 * k, 0.030 * (1 - q) * al)


# ================================================================ 1. INTRO · JAM
def _dunia_jam(im):
    """Jam tua besar: waktu sebagai subjek. Tahun 1922-1990 di plakat, denyut di bawahnya."""
    _grad(im, 0, 1100, mix(CREAM, TERRA, 0.10), mix(CREAM, WHITE, 0.30), 90)
    # halo konsentris di belakang jam
    for i in range(9):
        ring_on(im, 540, 430, 300 + i * 34, mix(TERRA, CREAM, 0.72), 2, 0.10 - i * 0.008)
    _shadow(im, 540, 716, 236, 30, 0.16, mix(TERRA_D, INK, 0.25))
    # badan jam
    ring_on(im, 540, 430, 252, mix(TERRA_D, INK, 0.30), 12, 1.0)
    ell(im, 288, 178, 792, 682, fill=mix(CREAM, WHITE, 0.72), alpha=1.0)
    ring_on(im, 540, 430, 234, mix(TERRA_D, INK, 0.20), 2.5, 0.55)
    # 60 goresan menit, 12 besar
    for i in range(60):
        a = -math.pi / 2 + i * math.pi / 30.0
        major = i % 5 == 0
        r0 = 208 if major else 218
        r1 = 232 if major else 226
        w = 5.0 if major else 2.2
        c = mix(INK, TERRA_D, 0.35) if major else mix(INK, CREAM, 0.55)
        line_on(im, (540 + r0 * math.cos(a), 430 + r0 * math.sin(a)),
                (540 + r1 * math.cos(a), 430 + r1 * math.sin(a)), c, w, 1.0 if major else 0.55)
    # angka 12/3/6/9
    for ang, txt in ((-90, "12"), (0, "3"), (90, "6"), (180, "9")):
        a = math.radians(ang)
        paste_c(im, 540 + 176 * math.cos(a), 430 + 176 * math.sin(a), txt,
                font(D.FB, 44), mix(INK, TERRA_D, 0.30), 0.92)
    # jarum jam 10:10 (statis) + jarum detik kecil
    for ang, ln, wd in ((-60, 96, 9), (60, 138, 7)):
        a = math.radians(ang)
        line_on(im, (540, 430), (540 + ln * math.cos(a), 430 + ln * math.sin(a)),
                mix(TERRA_D, INK, 0.20), wd, 0.95)
    dot_on(im, 540, 430, 15, mix(TERRA_D, INK, 0.15), 1.0)
    dot_on(im, 540, 430, 6, CREAM, 0.9)
    # plakat tahun
    rrect_on(im, 300, 742, 780, 848, 26, mix(CREAM, WHITE, 0.30), 0.96,
             outline=mix(TERRA_D, INK, 0.35), width=2.4)
    paste_c(im, 540, 776, "1922 — 1990", font(D.FB, 46), mix(INK, TERRA_D, 0.28), 0.95)
    paste_c(im, 540, 822, "SATU KASUS · BUKAN SEMUA KASUS", font(D.FS, 22),
            mix(INK, MUTED, 0.50), 0.80)
    # 68 titik tahun (2 baris 34) + garis denyut
    for i in range(68):
        cx = 186 + (i % 34) * 21.4
        cy = 890 + (i // 34) * 18
        dot_on(im, cx, cy, 4.2, mix(TERRA, CREAM, 0.35), 0.85)
    line_on(im, (120, 980), (960, 980), mix(INK, CREAM, 0.62), 2.4, 0.55)
    for i in range(5):
        x = 214 + i * 160
        poly_on(im, [(x - 34, 980), (x - 12, 980), (x - 4, 958), (x + 8, 1002), (x + 18, 980), (x + 42, 980)],
                mix(TERRA, INK, 0.20), 0.75)
    _vignette(im)


def _jarum_detik(img, u, al=1.0):
    a = -math.pi / 2 + (u % 60.0) * math.pi / 30.0
    line_on(img, (540, 430), (540 + 196 * math.cos(a), 430 + 196 * math.sin(a)),
            mix(TERRA, INK, 0.25), 3.0, 0.55 * al)


def sc_jam_cegukan(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0
    c = cues(sc, dur, CUES["jam_cegukan60"])
    img.paste(_base("jam", _dunia_jam), (0, 0))
    _jarum_detik(img, tl)
    # denyut "hik" pertama: cincin dari jam
    q = seg(tl, c["cegukan"], c["cegukan"] + 0.55)
    if q > 0:
        for k in range(2):
            qk = (q + k * 0.18) % 1.0
            ring_on(img, 540, 430, 252 + 90 * qk, mix(TERRA, WHITE, 0.35), 3.0,
                    (1 - qk) * 0.45)
    # angka 68 ditegaskan saat kata "delapan"
    q68 = esm((tl - c["delapan"]) / 0.42)
    if q68 > 0.01:
        V._glow11(img, 540, 776, 150, mix(KUNING, WHITE, 0.25), 0.18 * q68)
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.20, fsz=64, y=Y_TXT)


def sc_loop_jam(img, d, sc, tl, dur, tg, accent, al, dy):
    """Frame akhir = frame 0 intro: dunia sama, jarum detik dihitung mundur ke nol."""
    M.set_keluar(tl, dur, ada_lanjutan=False)
    al = 1.0
    c = cues(sc, dur, CUES["loop_jam60"])
    u = tl - dur
    img.paste(_base("jam", _dunia_jam), (0, 0))
    _jarum_detik(img, u)
    # satu detail baru: titik kecil berdenyut di bawah plakat (hadiah untuk yang mengulang)
    qk = esm((tl - c["berhenti"]) / 0.4) * (1 - esm((tl - c["berhenti"] - 0.5) / 0.35))
    if qk > 0.01:
        ring_on(img, 540, 890, 10 + 26 * qk, mix(TERRA, WHITE, 0.30), 2.6, qk * 0.55)
    _paper(img, 1.0, sc.get("src") or SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.24, fsz=64, y=Y_TXT)


# ================================================================ 2. F1 · DIAFRAGMA
def _dunia_diafragma(im):
    """Potongan dada: rusuk di belakang, paru, diafragma sebagai kubah penyangga."""
    _grad(im, 0, 1100, mix(CREAM, TEAL, 0.06), mix(CREAM, WHITE, 0.24), 80)
    for i in range(7):
        ring_on(im, 540, 600, 380 + i * 40, mix(TEAL, CREAM, 0.80), 2, 0.07 - i * 0.008)
    # siluet tubuh (potongan dada) + leher
    rrect_on(im, 296, 250, 784, 1010, 104, mix(CREAM, WHITE, 0.45), 1.0,
             outline=mix(INK, CREAM, 0.52), width=3.2)
    rrect_on(im, 486, 150, 594, 300, 44, mix(CREAM, WHITE, 0.45), 1.0,
             outline=mix(INK, CREAM, 0.52), width=3.2)

    # --- tulang belakang (pendek, berhenti di diafragma) ---
    line_on(im, (540, 306), (540, 690), mix(CREAM, INK, 0.30), 6.0, 0.50)
    for i in range(9):
        y = 330 + i * 40
        line_on(im, (526, y), (554, y), mix(CREAM, INK, 0.34), 2.4, 0.40)

    # --- rusuk: 7 pasang, di luar paru, digambar SEBELUM paru ---
    for i in range(6):
        y = 356 + i * 50
        lebar = 196 + i * 3
        wd = 5.0 - i * 0.30
        for sgn in (-1, 1):
            prev = (540 + sgn * 8, y)
            for k in range(1, 17):
                u = k / 16.0
                bx = ((1 - u) ** 2 * (540 + sgn * 8) + 2 * (1 - u) * u * (540 + sgn * (lebar + 22))
                      + u * u * (540 + sgn * (lebar + 4)))
                by = ((1 - u) ** 2 * y + 2 * (1 - u) * u * (y - 30) + u * u * (y + 54 + i * 4))
                line_on(im, prev, (bx, by), mix(CREAM, INK, 0.42), wd, 0.62)
                prev = (bx, by)

    # --- paru-paru (menutup bagian dalam rusuk) ---
    for sgn in (-1, 1):
        cx = 540 + sgn * 108
        ell(im, cx - 98, 362, cx + 98, 700, fill=mix(ROSE, CREAM, 0.50), alpha=0.62)

    # --- trakea + dua cabang (berhenti di paru) ---
    rrect_on(im, 527, 262, 553, 404, 12, mix(CREAM, INK, 0.20), 0.88)
    for sgn in (-1, 1):
        line_on(im, (540, 400), (540 + sgn * 76, 470), mix(CREAM, INK, 0.24), 13, 0.78)
        line_on(im, (540, 400), (540 + sgn * 76, 470), WHITE, 4, 0.32)
        line_on(im, (540 + sgn * 76, 470), (540 + sgn * 92, 520), mix(CREAM, INK, 0.26), 7, 0.55)
    # pita suara (glotis) di leher: dasar layar
    for sgn in (-1, 1):
        rrect_on(im, 540 + sgn * 10 - (26 if sgn < 0 else 0), 300, 540 + sgn * 10 + (26 if sgn > 0 else 0), 344,
                 6, mix(ROSE_D, INK, 0.18), 0.88)

    # --- dasar panggul tipis ---
    _arc(im, 540, 1010, 250, math.radians(200), math.radians(340), mix(INK, CREAM, 0.55), 3.0, 0.40, 0.34)
    _vignette(im)


def _glotis(img, q, al=1.0):
    """Dua lipatan pita suara yang menutup: q 0 = terbuka, 1 = rapat."""
    gap = 22 * (1 - q) + 3 * q
    for sgn in (-1, 1):
        x = 540 + sgn * gap
        poly_on(img, [(540 + sgn * 46, 300), (x, 300), (x, 344), (540 + sgn * 46, 344)],
                mix(ROSE_D, INK, 0.18), 0.90 * al)
    line_on(img, (540 - gap, 322), (540 + gap, 322), WHITE, 2.0, 0.55 * al)


def _kubah_diafragma(img, q, al=1.0):
    """q 0 = kubah tinggi (istirahat), q 1 = mendatar (kontraksi)."""
    h = 92 - 58 * q
    pts = []
    for i in range(41):
        x = 340 + i * 400 / 40.0
        k = (x - 540) / 200.0
        y = 792 - h * math.sqrt(max(0.0, 1 - k * k))
        pts.append((x, y))
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], mix(TERRA, INK, 0.34), 14, 0.95 * al)
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], mix(TERRA, WHITE, 0.42), 5, 0.62 * al)
    # tendon sentral (pucuk pucat)
    cx, cy = pts[20]
    ell(img, cx - 40, cy - 5, cx + 40, cy + 10, fill=mix(TERRA, CREAM, 0.60), alpha=0.80 * al)
    # pita otot: lengkung tipis mengikuti kubah dalam (bukan bulu)
    for j in range(3):
        off = 12 + j * 11
        prev = None
        for i in range(41):
            x = 340 + i * 400 / 40.0
            k = (x - 540) / 200.0
            if abs(k) > 1:
                continue
            y = 792 - (h - off) * math.sqrt(max(0.0, 1 - k * k))
            if prev is not None:
                line_on(img, prev, (x, y), mix(TERRA_D, INK, 0.40), 2.6, 0.22 * al)
            prev = (x, y)


def sc_diafragma(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0
    c = cues(sc, dur, CUES["diafragma60"])
    img.paste(_base("diafragma", _dunia_diafragma), (0, 0))
    q = esm((tl - c["berkontraksi"]) / 0.42)
    _kubah_diafragma(img, q)
    # paru-paru mengempis sedikit saat diafragma turun
    if q > 0.01:
        for sgn in (-1, 1):
            cx = 540 + sgn * 118
            ell(img, cx - 88, 380 + 10 * q, cx + 88, 640 - 14 * q,
                fill=mix(ROSE, CREAM, 0.62), alpha=0.20 * q)
    qg = esm((tl - c["menutup"]) / 0.30)
    _glotis(img, qg)
    # udara masuk: panah tipis turun dari leher
    qa = seg(tl, c["napas"] - 0.2, c["napas"] + 0.5)
    if 0 < qa < 1:
        y = 250 + 130 * qa
        for sgn in (-1, 1):
            line_on(img, (540 + sgn * 30, y), (540 + sgn * 18, y + 26), mix(TEAL, WHITE, 0.30), 5, 0.55 * (1 - qa))
    # ledakan HIK di sebelah kiri leher
    qh = seg(tl, c["hik"], c["hik"] + 0.65)
    if qh > 0:
        paste_c(img, 322, 236, "HIK", font(D.FB, 40 + 8 * (1 - qh)),
                mix(TEAL_D, INK, 0.25), (1 - qh) * 0.95)
        for k in range(3):
            ring_on(img, 400, 250, 18 + k * 16 + 40 * qh, mix(TEAL, WHITE, 0.30), 3.0,
                    (1 - qh) * (0.55 - k * 0.12))
    # kilau pada diafragma tepat saat kontraksi
    if 0 < q < 1:
        V._glow11(img, 540, 780, 220, mix(TERRA, WHITE, 0.45), 0.10 * math.sin(math.pi * q))
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.22, fsz=62, y=Y_TXT)


# ================================================================ 3. F2 · JALUR SARAF
def _jalur_vagus(q):
    """Kurva kubik dari tenggorokan ke perut (sisi kiri tubuh)."""
    p0, p1, p2, p3 = (604, 286), (664, 470), (600, 690), (474, 806)
    return ((1 - q) ** 3 * p0[0] + 3 * (1 - q) ** 2 * q * p1[0] + 3 * (1 - q) * q * q * p2[0] + q ** 3 * p3[0],
            (1 - q) ** 3 * p0[1] + 3 * (1 - q) ** 2 * q * p1[1] + 3 * (1 - q) * q * q * p2[1] + q ** 3 * p3[1])


def _jalur_frenikus(q):
    p0, p1, p2, p3 = (512, 300), (500, 470), (516, 620), (540, 700)
    return ((1 - q) ** 3 * p0[0] + 3 * (1 - q) ** 2 * q * p1[0] + 3 * (1 - q) * q * q * p2[0] + q ** 3 * p3[0],
            (1 - q) ** 3 * p0[1] + 3 * (1 - q) ** 2 * q * p1[1] + 3 * (1 - q) * q * q * p2[1] + q ** 3 * p3[1])


def _dunia_saraf(im):
    """Tubuh sebagai peta: dua saraf, satu sentakan. Tanpa wajah, tanpa detail yang tak perlu."""
    _grad(im, 0, 1100, mix(CREAM, TEAL, 0.08), mix(CREAM, WHITE, 0.26), 80)
    for i in range(8):
        ring_on(im, 540, 560, 400 + i * 36, mix(TEAL, CREAM, 0.84), 2, 0.06 - i * 0.006)
    # kontur tubuh: hanya garis, supaya saraf jadi fokus
    rrect_on(im, 300, 236, 780, 1010, 104, mix(CREAM, WHITE, 0.30), 0.55,
             outline=mix(TEAL_D, CREAM, 0.55), width=2.6)
    rrect_on(im, 490, 150, 590, 286, 42, mix(CREAM, WHITE, 0.30), 0.55,
             outline=mix(TEAL_D, CREAM, 0.55), width=2.6)
    # paru-paru + perut (bentuk, bukan isi)
    for sgn in (-1, 1):
        cx = 540 + sgn * 112
        ell(im, cx - 88, 372, cx + 88, 606, fill=mix(ROSE, CREAM, 0.64), alpha=0.34)
    _arc(im, 540, 806, 150, math.radians(190), math.radians(350), mix(TERRA, CREAM, 0.45), 3.0, 0.40, 0.62)
    ell(im, 396, 726, 684, 900, fill=mix(TERRA, CREAM, 0.72), alpha=0.30)
    # diafragma dasar
    for i in range(28):
        x = 336 + i * 204 / 27.0
        k = (x - 540) / 204.0
        y = 700 - 44 * math.sqrt(max(0.0, 1 - k * k))
        line_on(im, (x, y), (x, 724), mix(TERRA, INK, 0.34), 8, 0.55)
    _vignette(im)


def _jalur_gambar(img, fn, n, col, w, al, qmax=1.0):
    prev = fn(0.0)
    for i in range(1, int(n * qmax) + 1):
        q = i / n
        p = fn(q)
        line_on(img, prev, p, col, w, al)
        prev = p


def sc_jalur_saraf(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0
    c = cues(sc, dur, CUES["jalur_saraf60"])
    img.paste(_base("saraf", _dunia_saraf), (0, 0))
    # VAGUS (teal): tumbuh dari tenggorokan saat kata "vagus"
    qv = esm((tl - c["vagus"]) / 1.15)
    if qv > 0.01:
        _jalur_gambar(img, _jalur_vagus, 40, mix(TEAL_D, INK, 0.22), 11, 0.92 * al, qv)
        _jalur_gambar(img, _jalur_vagus, 40, mix(TEAL, WHITE, 0.35), 3.4, 0.55 * al, qv)
    # FRENIKUS (amber): tumbuh saat kata "frenikus", bercabang ke dua sisi
    qf = esm((tl - c["frenikus"]) / 1.0)
    if qf > 0.01:
        _jalur_gambar(img, _jalur_frenikus, 32, mix(AMBER2, INK, 0.28), 10, 0.92 * al, qf)
        _jalur_gambar(img, _jalur_frenikus, 32, mix(AMBER2, WHITE, 0.30), 3.2, 0.55 * al, qf)
        qb = esm((tl - c["diafragma"]) / 0.6)
        if qb > 0.01:
            for sgn in (-1, 1):
                line_on(img, (540, 700 + 8), (540 + sgn * 96 * qb, 726 + 8), mix(AMBER2, INK, 0.30), 8, 0.85 * qb)
    # simpul (node) + denyut berjalan
    if qv > 0.9:
        for (px, py) in ((604, 286), (474, 806)):
            dot_on(img, px, py, 15, mix(TEAL, WHITE, 0.30), 0.95)
            ring_on(img, px, py, 21, mix(TEAL_D, INK, 0.30), 3, 0.75)
        for i in range(3):
            q = (tl * 0.42 + i / 3.0) % 1.0
            px, py = _jalur_vagus(q)
            dot_on(img, px, py, 7.5, WHITE, 0.90)
            dot_on(img, px, py, 4.0, mix(TEAL_D, INK, 0.20), 0.95)
    if qf > 0.9:
        dot_on(img, 540, 700, 17, mix(AMBER2, WHITE, 0.35), 0.95)
        ring_on(img, 540, 700, 24 + 6 * math.sin(tg * 4.0), mix(AMBER2, INK, 0.25), 3, 0.70)
        for i in range(2):
            q = (tl * 0.55 + i / 2.0) % 1.0
            px, py = _jalur_frenikus(q)
            dot_on(img, px, py, 7.0, WHITE, 0.90)
            dot_on(img, px, py, 3.6, mix(AMBER2, INK, 0.22), 0.95)
    # label saraf dengan garis penunjuk (bukan menempel di kurva)
    ql = esm((tl - c["sinyal"]) / 0.6)
    if ql > 0.01:
        line_on(img, (330, 520), (586, 512), mix(TEAL_D, CREAM, 0.40), 2.4, 0.75 * ql)
        paste_c(img, 250, 490, "VAGUS", font(D.FB, 34), mix(TEAL_D, INK, 0.20), 0.95 * ql)
        paste_c(img, 250, 528, "dari perut & tenggorokan", font(D.FM, 20), mix(INK, MUTED, 0.55), 0.80 * ql)
    ql2 = esm((tl - c["tenggorokan"]) / 0.6)
    if ql2 > 0.01:
        line_on(img, (738, 430), (566, 470), mix(AMBER2, CREAM, 0.35), 2.4, 0.75 * ql2)
        paste_c(img, 830, 400, "FRENIKUS", font(D.FB, 34), mix(AMBER2, INK, 0.28), 0.95 * ql2)
        paste_c(img, 830, 438, "menuju diafragma", font(D.FM, 20), mix(INK, MUTED, 0.55), 0.80 * ql2)
    # tiga pemicu sebagai chip kecil di bawah
    qp = esm((tl - c["penuh"]) / 0.55)
    if qp > 0.01:
        for i, (txt, cx) in enumerate((("PERUT PENUH", 218), ("MINUM CEPAT", 540), ("UDARA DINGIN", 862))):
            qi = esm((tl - (c["penuh"] + i * 0.30)) / 0.45)
            if qi <= 0.01:
                continue
            wid = tw(txt, font(D.FS, 21)) + 46
            rrect_on(img, cx - wid / 2, 906, cx + wid / 2, 958, 26, mix(CREAM, WHITE, 0.32), 0.95 * qi,
                     outline=mix(accent, INK, 0.30), width=2)
            paste_c(img, cx, 932, txt, font(D.FS, 21), mix(INK, MUTED, 0.25), qi)
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.22, fsz=62, y=Y_TXT)


# ================================================================ 4. F3 · MITOS
def _dunia_mitos(im):
    """Dua kartu: yang bekerja vs yang cuma mitos. Meter CO2 di sisi kiri."""
    _grad(im, 0, 1100, mix(CREAM, OLIVE, 0.07), mix(CREAM, WHITE, 0.26), 80)
    for i in range(7):
        ring_on(im, 540, 560, 380 + i * 38, mix(OLIVE, CREAM, 0.82), 2, 0.06 - i * 0.006)
    _kartu(im, 56, 196, 448, 636, 1.0, 30)
    _kartu(im, 576, 196, 448, 636, 1.0, 30)
    # header kartu
    dot_on(im, 112, 246, 15, mix(GREEN, WHITE, 0.30), 0.95)
    line_on(im, (105, 246), (110, 253), mix(GREEN, INK, 0.25), 3.6, 1.0)
    line_on(im, (110, 253), (121, 238), mix(GREEN, INK, 0.25), 3.6, 1.0)
    paste_c(im, 140 + tw("BEKERJA", font(D.FB, 34)) / 2, 246, "BEKERJA", font(D.FB, 34),
            mix(GREEN, INK, 0.30), 0.95)
    dot_on(im, 632, 246, 15, mix(RED, CREAM, 0.72), 0.95)
    silang(im, 632, 246, 9, mix(RED, INK, 0.10), 0.95, 1.0)
    paste_c(im, 660 + tw("MITOS", font(D.FB, 34)) / 2, 246, "MITOS", font(D.FB, 34),
            mix(RED, INK, 0.15), 0.95)
    line_on(im, (96, 292), (464, 292), mix(CREAM, INK, 0.16), 2, 1.0)
    line_on(im, (616, 292), (1004, 292), mix(CREAM, INK, 0.16), 2, 1.0)
    # kiri: tabung CO2 kosong (diisi per frame) + label
    rrect_on(im, 128, 340, 214, 700, 40, mix(CREAM, INK, 0.10), 1.0)
    rrect_on(im, 138, 350, 204, 690, 30, mix(CREAM, WHITE, 0.55), 1.0)
    paste_c(im, 176, 730, "CO2", font(D.FB, 30), mix(TEAL_D, INK, 0.30), 0.95)
    paste_c(im, 332, 400, "TAHAN", font(D.FB, 30), mix(INK, MUTED, 0.22), 0.92)
    paste_c(im, 332, 436, "NAPAS", font(D.FB, 30), mix(INK, MUTED, 0.22), 0.92)
    paste_c(im, 332, 486, "10-20 detik", font(D.FM, 22), mix(INK, MUTED, 0.55), 0.85)
    # paru-paru kecil di kartu kiri
    for sgn in (-1, 1):
        cx = 332 + sgn * 34
        ell(im, cx - 44, 556, cx + 44, 690, fill=mix(ROSE, CREAM, 0.55), alpha=0.5)
    rrect_on(im, 320, 520, 344, 560, 8, mix(CREAM, INK, 0.22), 0.8)
    # kanan: wajah kaget + tanda seru
    dot_on(im, 800, 430, 74, mix(CREAM, OLIVE, 0.28), 1.0)
    dot_on(im, 776, 418, 8, mix(INK, OLIVE, 0.30), 0.9)
    dot_on(im, 824, 418, 8, mix(INK, OLIVE, 0.30), 0.9)
    ell(im, 786, 462, 814, 486, fill=mix(INK, OLIVE, 0.35), alpha=0.75)
    for k in range(5):
        a = math.radians(-150 + k * 30)
        line_on(im, (800 + 88 * math.cos(a), 430 + 88 * math.sin(a)),
                (800 + 118 * math.cos(a), 430 + 118 * math.sin(a)), mix(OLIVE, INK, 0.40), 4, 0.55)
    paste_c(im, 800, 556, "DIKEJUTKAN", font(D.FB, 28), mix(INK, MUTED, 0.22), 0.92)
    paste_c(im, 800, 596, "tidak terbukti", font(D.FM, 22), mix(INK, MUTED, 0.55), 0.85)
    # label bawah tiap kartu
    paste_c(im, 280, 900, "mekanisme masuk akal", font(D.FM, 21), mix(GREEN, INK, 0.35), 0.80)
    paste_c(im, 800, 900, "hanya kebiasaan", font(D.FM, 21), mix(RED, INK, 0.30), 0.80)
    _vignette(im)


def sc_mitos(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0
    c = cues(sc, dur, CUES["mitos60"])
    img.paste(_base("mitos", _dunia_mitos), (0, 0))
    # CO2 naik: isi tabung bertambah (batas atas 690)
    qco = esm((tl - c["karbon"]) / 1.25)
    if qco > 0.01:
        top = 690 - (690 - 366) * qco
        rrect_on(img, 140, top, 202, 688, 26, mix(TEAL, WHITE, 0.42), 0.62)
        for i in range(4):
            yy = 690 - (i + 1) * 52 * qco
            line_on(img, (148, yy), (194, yy), mix(TEAL_D, WHITE, 0.35), 2.2, 0.35 * qco)
        paste_c(img, 176, 318, f"{int(round(qco * 100))}%", font(D.FB, 22), mix(TEAL_D, INK, 0.25), 0.85 * qco)
    # refleks "melemah": gelombang yang mereda di sisi kiri atas
    qw = seg(tl, c["refleksnya"], c["refleksnya"] + 1.6)
    if 0 < qw < 1:
        for i in range(3):
            qi = clamp(qw * 1.4 - i * 0.18)
            if qi <= 0:
                continue
            line_on(img, (100 + i * 120, 176 - 10 + i * 4), (160 + i * 120, 176 - 10 + i * 4),
                    mix(OLIVE, INK, 0.35), 3.2, (1 - qi) * 0.55)
    # kilat merah pada kartu mitos saat kata "dikejutkan"
    qs = seg(tl, c["dikejutkan"], c["dikejutkan"] + 0.5)
    if qs > 0:
        ring_on(img, 800, 430, 132 + 26 * qs, mix(RED, WHITE, 0.30), 4, (1 - qs) * 0.55)
    # tanda "tidak terbukti" muncul sebagai cap
    qt = esm((tl - c["terbukti"]) / 0.45)
    if qt > 0.01:
        lay = Image.new("RGBA", (300, 84), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        rrect_on(lay, 3, 3, 297, 81, 12, mix(RED, WHITE, 0.82), 0.95, outline=RED, width=3)
        _trk = D.TRACK
        D.TRACK = False
        paste_c(lay, 150, 42, "TIDAK TERBUKTI", font(D.FS, 26), mix(RED, INK, 0.12), 1.0)
        D.TRACK = _trk
        lay = lay.rotate(-7, resample=Image.BICUBIC, expand=True)
        a = lay.getchannel("A").point(lambda v: int(v * qt * al))
        img.paste(lay, (654, 640), a)
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.22, fsz=62, y=Y_TXT)


# ================================================================ 5. F4 · BATAS DURASI
def _dunia_durasi(im):
    """Garis waktu durasi: tiga zona, dua ambang. Angka sebagai tulang cerita."""
    _grad(im, 0, 1100, mix(CREAM, AMBER2, 0.10), mix(CREAM, WHITE, 0.26), 80)
    for i in range(9):
        line_on(im, (0, 150 + i * 106), (1080, 150 + i * 106), mix(CREAM, INK, 0.12), 1.6, 0.30)
    _shadow(im, 540, 690, 470, 26, 0.12)
    # jalur dasar
    rrect_on(im, 100, 606, 980, 674, 34, mix(CREAM, WHITE, 0.30), 1.0)
    # jam kiri, kalender kanan
    ring_on(im, 176, 380, 64, mix(AMBER2, INK, 0.30), 6, 0.95)
    for i in range(12):
        a = -math.pi / 2 + i * math.pi / 6
        line_on(im, (176 + 50 * math.cos(a), 380 + 50 * math.sin(a)),
                (176 + 60 * math.cos(a), 380 + 60 * math.sin(a)), mix(INK, AMBER2, 0.35), 3, 0.75)
    line_on(im, (176, 380), (176, 340), mix(INK, AMBER2, 0.30), 5, 0.9)
    line_on(im, (176, 380), (208, 396), mix(INK, AMBER2, 0.30), 4, 0.9)
    rrect_on(im, 856, 320, 968, 440, 12, mix(CREAM, WHITE, 0.40), 1.0,
             outline=mix(AMBER2, INK, 0.30), width=3)
    rrect_on(im, 856, 320, 968, 356, 12, mix(AMBER2, INK, 0.22), 0.9)
    for r in range(2):
        for cq in range(4):
            dot_on(im, 880 + cq * 24, 380 + r * 28, 5, mix(INK, AMBER2, 0.35), 0.55)
    # ambang: garis putus + label
    for x, txt in ((430, "48 JAM"), (700, "1 BULAN")):
        for k in range(7):
            line_on(im, (x, 560 + k * 14), (x, 566 + k * 14), mix(INK, CREAM, 0.45), 3, 0.55)
        paste_c(im, x, 526, txt, font(D.FB, 30), mix(INK, AMBER2, 0.30), 0.95)
    # label zona
    for x, txt, col in ((264, "BIASA", GREEN), (564, "PERSISTEN", AMBER2), (840, "INTRATABLE", RED)):
        paste_c(im, x, 742, txt, font(D.FB, 26), mix(col, INK, 0.22), 0.92)
    paste_c(im, 264, 778, "< 48 jam", font(D.FM, 20), mix(INK, MUTED, 0.55), 0.80)
    paste_c(im, 564, 778, "> 48 jam", font(D.FM, 20), mix(INK, MUTED, 0.55), 0.80)
    paste_c(im, 840, 778, "> 1 bulan", font(D.FM, 20), mix(INK, MUTED, 0.55), 0.80)
    _vignette(im)


def sc_batas_durasi(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0
    c = cues(sc, dur, CUES["batas_durasi60"])
    img.paste(_base("durasi", _dunia_durasi), (0, 0))
    # isi zona tumbuh berurutan mengikuti kata
    q1 = esm((tl - c["jam"]) / 0.7)
    if q1 > 0.01:
        rrect_on(img, 100, 606, 100 + 330 * q1, 674, 34, mix(GREEN, WHITE, 0.18), 0.92)
    q2 = esm((tl - c["persisten"]) / 0.7)
    if q2 > 0.01:
        rrect_on(img, 430, 606, 430 + 270 * q2, 674, 8, mix(AMBER2, WHITE, 0.12), 0.92)
    q3 = esm((tl - c["intractable"]) / 0.7)
    if q3 > 0.01:
        rrect_on(img, 700, 606, 700 + 280 * q3, 674, 34, mix(RED, WHITE, 0.30), 0.92)
    # penanda berjalan menyusuri garis saat "artinya" disebut
    qm = esm((tl - c["artinya"]) / 0.9)
    if qm > 0.01:
        x = 100 + 880 * qm
        dot_on(img, x, 640, 15, WHITE, 0.95)
        ring_on(img, x, 640, 22, mix(accent, INK, 0.25), 3.4, 0.9)
    # sorot angka 48 saat disebut
    qh = seg(tl, c["delapan"], c["delapan"] + 0.75)
    if qh > 0:
        V._glow11(img, 430, 526, 120, mix(AMBER2, WHITE, 0.35), 0.20 * math.sin(math.pi * qh))
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.22, fsz=62, y=Y_TXT)


# ================================================================ 6. F5 · JANIN
def _tiub(img, pts, r, col, al=1.0, r2=None):
    """Tubuh sebagai rantai lingkaran: ujung membulat, tanpa sendi kotak."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        rr = r if r2 is None else r + (r2 - r) * (i / max(1, len(pts) - 2))
        n = max(2, int(math.dist(a, b) / max(1.0, rr * 0.42)) + 1)
        for k in range(n + 1):
            q = k / n
            cx, cy = a[0] + (b[0] - a[0]) * q, a[1] + (b[1] - a[1]) * q
            dd.ellipse([D.S(cx - rr), D.S(cy - rr), D.S(cx + rr), D.S(cy + rr)],
                       fill=col + (int(255 * al),))
    img.paste(lay, (0, 0), lay)
def _dunia_janin(im):
    """Rahim sebagai ruang: janin meringkuk menghadap kiri, denyut kecil, garis waktu kehamilan."""
    _grad(im, 0, 1100, mix(CREAM, ROSE, 0.16), mix(CREAM, WHITE, 0.26), 80)
    # dinding rahim (dua lapis, tanpa cincin target)
    ell(im, 214, 190, 866, 924, fill=mix(ROSE, CREAM, 0.74), alpha=0.60)
    ell(im, 240, 220, 840, 894, fill=mix(ROSE, WHITE, 0.62), alpha=0.45)
    _arc(im, 540, 557, 322, math.radians(0), math.radians(360), mix(ROSE_D, CREAM, 0.40), 4, 0.45, 1.02)
    # cairan ketuban: bintik halus
    _speck(im, 268, 250, 812, 866, 90, mix(ROSE_D, WHITE, 0.55), 0.16, seed=77, r=(1.0, 3.2))

    # --- plasenta + tali pusat (di belakang tubuh) ---
    _shadow(im, 782, 268, 104, 74, 0.10, mix(ROSE_D, INK, 0.30))
    ell(im, 686, 196, 878, 340, fill=mix(ROSE, ROSE_D, 0.34), alpha=0.62)
    for i in range(9):
        a = i * 0.72
        line_on(im, (782 + 46 * math.cos(a), 268 + 34 * math.sin(a)),
                (782 + 84 * math.cos(a * 1.3), 268 + 62 * math.sin(a * 1.3)),
                mix(ROSE_D, CREAM, 0.30), 3.0, 0.40)
    _tiub(im, [(730, 318), (700, 400), (664, 470), (622, 520)], 14, mix(ROSE_D, CREAM, 0.22), 0.80)
    _tiub(im, [(730, 318), (700, 400), (664, 470), (622, 520)], 6, mix(ROSE, WHITE, 0.30), 0.40)

    # --- tubuh janin: satu kurva punggung, tanpa sendi ---
    _tiub(im, [(618, 500), (548, 546), (508, 620), (516, 700), (566, 752), (634, 764)], 58,
          mix(SKIN, ROSE_D, 0.16), 0.97, r2=44)
    # sorot punggung
    _tiub(im, [(606, 520), (556, 560), (528, 620), (534, 690), (572, 730)], 18,
          mix(SKIN, WHITE, 0.42), 0.42)
    # tungkai terlipat di depan perut
    _tiub(im, [(600, 752), (664, 726), (694, 672)], 30, mix(SKIN, ROSE_D, 0.20), 0.96)
    _tiub(im, [(694, 672), (700, 616)], 22, mix(SKIN, ROSE_D, 0.26), 0.96)
    dot_on(im, 702, 604, 19, mix(SKIN, ROSE_D, 0.30), 0.95)
    # lengan kecil menutup dada
    _tiub(im, [(622, 548), (668, 596), (656, 648)], 20, mix(SKIN, ROSE_D, 0.22), 0.95)
    # kepala (paling akhir, di atas tubuh)
    dot_on(im, 650, 424, 80, mix(SKIN, ROSE_D, 0.12), 1.0)
    _arc(im, 650, 424, 80, math.radians(200), math.radians(340), mix(SKIN, WHITE, 0.45), 10, 0.40, 1.0)
    # telinga + mata terpejam + mulut
    ell(im, 700, 410, 722, 446, fill=mix(SKIN, ROSE_D, 0.34), alpha=0.85)
    _arc(im, 630, 418, 15, math.radians(20), math.radians(160), mix(ROSE_D, INK, 0.30), 4.0, 0.80, 0.75)
    _arc(im, 606, 452, 9, math.radians(30), math.radians(150), mix(ROSE_D, INK, 0.35), 3.0, 0.65, 0.80)

    # --- garis waktu kehamilan (minggu) ---
    rrect_on(im, 120, 942, 960, 1014, 22, mix(CREAM, WHITE, 0.30), 0.95)
    for i in range(9):
        x = 168 + i * 96
        line_on(im, (x, 958), (x, 998), mix(CREAM, INK, 0.24), 2.4, 0.85)
        paste_c(im, x, 984, str(9 + i * 4), font(D.FM, 18), mix(INK, MUTED, 0.55), 0.80)
    _vignette(im)


def sc_janin(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0
    c = cues(sc, dur, CUES["janin60"])
    img.paste(_base("janin", _dunia_janin), (0, 0))
    # denyut cegukan: cincin dari perut janin
    qc = esm((tl - c["cegukan"]) / 0.5)
    if qc > 0.01:
        for i in range(4):
            ph = (tl * 0.9 + i * 0.25) % 1.0
            ring_on(img, 566, 700, 34 + 132 * ph, mix(ROSE, WHITE, 0.35), 3.0, (1 - ph) * 0.45 * qc)
        # badan janin berdenyut halus
        dot_on(img, 566, 700, 8, WHITE, 0.30 * qc * (0.5 + 0.5 * math.sin(tl * 7.0)))
    # penanda 9 minggu
    q9 = esm((tl - c["sembilan"]) / 0.6)
    if q9 > 0.01:
        x = 168
        ring_on(img, x, 978, 24 * q9, mix(ROSE_D, INK, 0.30), 4, 0.95 * q9)
        rrect_on(img, x - 62, 874, x + 62, 910, 18, mix(ROSE, WHITE, 0.30), 0.95 * q9,
                 outline=mix(ROSE_D, INK, 0.30), width=2)
        paste_c(img, x, 892, "9 MINGGU", font(D.FS, 19), mix(ROSE_D, INK, 0.25), 0.95 * q9)
    # garis "latihan diafragma" dari janin ke bawah
    ql = esm((tl - c["latihan"]) / 0.8)
    if ql > 0.01:
        for i in range(3):
            yi = 600 + i * 40
            line_on(img, (740, yi), (740 + 40 * ql, yi), mix(ROSE_D, CREAM, 0.35), 3.0, 0.55 * ql)
        paste_c(img, 862, 656, "latihan", font(D.FM, 22), mix(INK, MUTED, 0.52), 0.80 * ql)
        paste_c(img, 862, 686, "diafragma", font(D.FM, 22), mix(INK, MUTED, 0.52), 0.80 * ql)
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.22, fsz=62, y=Y_TXT)


# ================================================================ 7. F6 · TINDAKAN
def _ikon_jam(img, cx, cy, r, col, al=1.0):
    ring_on(img, cx, cy, r, col, 5, 0.95 * al)
    line_on(img, (cx, cy), (cx, cy - r * 0.62), col, 5, 0.95 * al)
    line_on(img, (cx, cy), (cx + r * 0.52, cy + r * 0.22), col, 5, 0.95 * al)


def _ikon_gelas(img, cx, cy, s, col, al=1.0):
    poly_on(img, [(cx - 34 * s, cy - 48 * s), (cx + 34 * s, cy - 48 * s),
                  (cx + 22 * s, cy + 46 * s), (cx - 22 * s, cy + 46 * s)], col, 0.30 * al)
    for i in range(5):
        line_on(img, (cx - 30 * s + i * 15 * s, cy - 44 * s), (cx - 22 * s + i * 12 * s, cy + 22 * s),
                col, 3.0, 0.85 * al)
    line_on(img, (cx - 34 * s, cy - 48 * s), (cx + 34 * s, cy - 48 * s), col, 6, 0.95 * al)


def _ikon_hati(img, cx, cy, s, col, al=1.0):
    """Jantung: dua cup + ujung bawah, garis EKG di atasnya."""
    dot_on(img, cx - 21 * s, cy - 14 * s, 29 * s, col, 0.90 * al)
    dot_on(img, cx + 21 * s, cy - 14 * s, 29 * s, col, 0.90 * al)
    poly_on(img, [(cx - 47 * s, cy - 4 * s), (cx + 47 * s, cy - 4 * s),
                  (cx + 14 * s, cy + 40 * s), (cx, cy + 56 * s), (cx - 14 * s, cy + 40 * s)], col, 0.90 * al)
    pts = [(cx - 38 * s, cy + 2 * s), (cx - 14 * s, cy + 2 * s), (cx - 7 * s, cy - 12 * s),
           (cx + 2 * s, cy + 16 * s), (cx + 9 * s, cy + 2 * s), (cx + 38 * s, cy + 2 * s)]
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], WHITE, 4.2, 0.92 * al)


def _ikon_periksa(img, cx, cy, s, col, al=1.0):
    ring_on(img, cx, cy, 46 * s, col, 5, 0.95 * al)
    line_on(img, (cx - 20 * s, cy), (cx + 20 * s, cy), col, 9, 0.95 * al)
    line_on(img, (cx, cy - 20 * s), (cx, cy + 20 * s), col, 9, 0.95 * al)


def _dunia_tindakan(im):
    _grad(im, 0, 1100, mix(CREAM, GREEN, 0.08), mix(CREAM, WHITE, 0.26), 80)
    for i in range(7):
        ring_on(im, 540, 520, 360 + i * 40, mix(GREEN, CREAM, 0.84), 2, 0.06 - i * 0.006)
    for i, (x, ok) in enumerate(((40, True), (290, True), (540, False), (790, True))):
        rrect_on(im, x, 250, x + 200, 450, 26, mix(CREAM, INK, 0.14), 0.30)
        rrect_on(im, x, 240, x + 200, 440, 26, WHITE, 1.0)
        rrect_on(im, x + 8, 248, x + 192, 432, 20,
                 mix(CREAM, GREEN if ok else RED, 0.11), 0.42)
    _ikon_jam(im, 140, 340, 56, mix(TEAL_D, INK, 0.20))
    _ikon_gelas(im, 390, 346, 1.0, mix(BLUE, INK, 0.25))
    _ikon_hati(im, 640, 336, 1.0, mix(RED, INK, 0.15))
    _ikon_periksa(im, 890, 340, 1.0, mix(GREEN, INK, 0.25))
    for x, t1, t2 in ((140, "TAHAN", "NAPAS"), (390, "MINUM", "PELAN"),
                      (640, "NYERI", "DADA"), (890, "SEGERA", "PERIKSA")):
        paste_c(im, x, 486, t1, font(D.FB, 25), mix(INK, MUTED, 0.22), 0.94)
        paste_c(im, x, 518, t2, font(D.FB, 25), mix(INK, MUTED, 0.22), 0.94)
    # pita bawah: kalau menetap
    rrect_on(im, 120, 632, 960, 712, 30, mix(CREAM, WHITE, 0.30), 0.95,
             outline=mix(GREEN, INK, 0.35), width=2.4)
    paste_c(im, 540, 672, "KALAU MENETAP, JANGAN DITAHAN SENDIRI", font(D.FS, 26),
            mix(INK, MUTED, 0.28), 0.92)
    # panah ke dokter
    for i in range(20):
        line_on(im, (300 + i * 22, 800), (316 + i * 22, 800), mix(GREEN, INK, 0.30), 7, 0.45)
    poly_on(im, [(720, 786), (752, 800), (720, 814)], mix(GREEN, INK, 0.30), 0.55)
    dot_on(im, 800, 800, 30, mix(CREAM, WHITE, 0.30), 0.95)
    ring_on(im, 800, 800, 30, mix(GREEN, INK, 0.30), 3.2, 0.85)
    paste_c(im, 800, 800, "dr", font(D.FB, 26), mix(GREEN, INK, 0.30), 0.95)
    _vignette(im)


def sc_tindakan(img, d, sc, tl, dur, tg, accent, al, dy):
    M.set_keluar(tl, dur, ada_lanjutan=True)
    al = 1.0
    c = cues(sc, dur, CUES["tindakan60"])
    img.paste(_base("tindakan", _dunia_tindakan), (0, 0))
    # ubin muncul satu per satu mengikuti kata
    for i, key in enumerate(("menahan", "minum", "nyeri", "segera")):
        q = esm((tl - c[key]) / 0.42)
        if q <= 0.01:
            continue
        x = 40 + i * 250
        yy = 240 + (1 - q) * 30
        rrect_on(img, x, yy, x + 200, yy + 200, 26, mix(WHITE, CREAM, 1 - q), q * 0.55)
    # kilat merah pada ubin nyeri dada
    qn = seg(tl, c["nyeri"], c["dada"] + 0.8)
    if qn > 0:
        ring_on(img, 640, 340, 108 + 22 * qn, mix(RED, WHITE, 0.30), 5, (1 - qn) * 0.60)
    _paper(img, 1.0, SUMBER)
    _chip(sc, accent, img, 1.0)
    _catatan(sc, accent, img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.22, fsz=62, y=Y_TXT)
    qb = esm((tl - c["periksa"]) / 0.5)
    _catatan_bahaya(img, qb, 1.0)


# ================================================================ CUE & SFX
CUES = {
    "jam_cegukan60": {"cegukan": ("Cegukan", 0.02), "paling": ("paling", 0.10), "lama": ("lama", 0.18),
                      "dunia": ("dunia", 0.30), "enam": ("enam", 0.60), "puluh": ("puluh", 0.70),
                      "delapan": ("delapan", 0.80), "tahun": ("tahun", 0.94)},
    "diafragma60": {"cegukan": ("Cegukan", 0.02), "angin": ("angin", 0.10), "diafragma": ("Diafragma", 0.20),
                    "otot": ("otot", 0.28), "napas": ("napas", 0.36), "berkontraksi": ("berkontraksi", 0.46),
                    "mendadak": ("mendadak", 0.56), "pita": ("pita", 0.66), "menutup": ("menutup", 0.76),
                    "hik": ("hik", 0.86), "pendek": ("pendek", 0.94)},
    "jalur_saraf60": {"pemicunya": ("Pemicunya", 0.01), "jalur": ("jalur", 0.08), "saraf": ("saraf", 0.14),
                      "vagus": ("Vagus", 0.22), "sinyal": ("sinyal", 0.30), "perut": ("perut", 0.38),
                      "tenggorokan": ("tenggorokan", 0.46), "frenikus": ("Frenikus", 0.56),
                      "diafragma": ("diafragma", 0.64), "penuh": ("penuh", 0.74), "minum": ("minum", 0.80),
                      "dingin": ("dingin", 0.88), "mengganggu": ("mengganggu", 0.95)},
    "mitos60": {"berhenti": ("berhenti", 0.03), "refleksnya": ("refleksnya", 0.12), "melemah": ("melemah", 0.18),
                "menit": ("menit", 0.26), "menahan": ("Menahan", 0.32), "napas": ("napas", 0.38),
                "karbon": ("karbon", 0.46), "dioksida": ("dioksida", 0.54), "naik": ("naik", 0.60),
                "dikejutkan": ("Dikejutkan", 0.70), "terbukti": ("terbukti", 0.86), "bekerja": ("bekerja", 0.94)},
    "batas_durasi60": {"durasi": ("Durasi", 0.01), "artinya": ("artinya", 0.07), "bawah": ("bawah", 0.14),
                       "delapan": ("delapan", 0.20), "jam": ("jam", 0.26), "biasa": ("biasa", 0.34),
                       "persisten": ("persisten", 0.46), "sebulan": ("sebulan", 0.56),
                       "intractable": ("intractable", 0.64), "angka": ("Angka", 0.74),
                       "membedakan": ("membedakan", 0.82), "diperiksa": ("diperiksa", 0.94)},
    "janin60": {"jarang": ("jarang", 0.03), "janin": ("janin", 0.11), "cegukan": ("cegukan", 0.17),
                "kandungan": ("kandungan", 0.29), "kadang": ("kadang", 0.38), "usia": ("usia", 0.44),
                "sembilan": ("sembilan", 0.52), "minggu": ("minggu", 0.60), "ahli": ("ahli", 0.68),
                "latihan": ("latihan", 0.80), "bernapas": ("bernapas", 0.90)},
    "tindakan60": {"masuk": ("masuk", 0.01), "menahan": ("menahan", 0.06), "napas": ("napas", 0.11),
                   "detik": ("detik", 0.20), "minum": ("minum", 0.28), "pelan": ("pelan", 0.34),
                   "nyeri": ("nyeri", 0.48), "dada": ("dada", 0.53), "lemas": ("lemas", 0.58),
                   "sulit": ("sulit", 0.64), "bicara": ("bicara", 0.69), "segera": ("segera", 0.76),
                   "periksa": ("periksa", 0.82), "biarkan": ("biarkan", 0.90)},
    "loop_jam60": {"cegukan": ("Cegukan", 0.02), "singkat": ("singkat", 0.08), "normal": ("normal", 0.16),
                   "waspadai": ("diwaspadai", 0.32), "tidak": ("tidak", 0.46), "berhenti": ("berhenti", 0.56)},
}

SFX = {
    "jam_cegukan60": {"cegukan": ("detak", 0.70, 0), "lama": ("tick", 0.70, 0), "dunia": ("whoosh", 0.60, 0),
                      "delapan": ("thump", 0.85, 0), "tahun": ("tick", 0.60, 0)},
    "diafragma60": {"cegukan": ("tick", 0.60, 0), "angin": ("swish", 0.55, 0), "diafragma": ("pop", 0.70, 0),
                    "otot": ("tick", 0.60, 0), "napas": ("angin", 0.50, 0), "berkontraksi": ("thud", 0.85, 0),
                    "mendadak": ("impact", 0.80, 0), "menutup": ("click", 0.70, 0), "hik": ("gigit", 0.55, 0),
                    "pendek": ("tick", 0.60, 0)},
    "jalur_saraf60": {"pemicunya": ("morph", 0.55, 0), "jalur": ("whoosh", 0.65, 0), "saraf": ("tick", 0.70, 0),
                      "vagus": ("pop", 0.65, 0), "sinyal": ("tick", 0.60, 0), "perut": ("gelembung", 0.55, 0),
                      "tenggorokan": ("tick", 0.60, 0), "frenikus": ("pop", 0.70, 0),
                      "diafragma": ("thud", 0.75, 0), "penuh": ("thump", 0.70, 0),
                      "minum": ("gelembung", 0.50, 0), "dingin": ("swish", 0.55, 0),
                      "mengganggu": ("riser", 0.50, -0.25)},
    "mitos60": {"berhenti": ("tick", 0.65, 0), "refleksnya": ("swish", 0.60, 0), "melemah": ("thud", 0.70, 0),
                "menahan": ("pop", 0.65, 0), "karbon": ("gelembung", 0.60, 0), "naik": ("riser", 0.45, -0.2),
                "dikejutkan": ("impact", 0.75, 0), "terbukti": ("tick", 0.70, 0), "bekerja": ("click", 0.65, 0)},
    "batas_durasi60": {"durasi": ("tick", 0.70, 0), "artinya": ("pop", 0.60, 0), "delapan": ("thump", 0.85, 0),
                       "jam": ("tick", 0.70, 0), "biasa": ("pop", 0.60, 0), "persisten": ("thud", 0.75, 0),
                       "sebulan": ("thud", 0.80, 0), "intractable": ("impact", 0.70, 0),
                       "angka": ("tick", 0.70, 0), "membedakan": ("swish", 0.55, 0),
                       "diperiksa": ("ding", 0.60, 0)},
    "janin60": {"jarang": ("swish", 0.50, 0), "janin": ("pop", 0.65, 0), "cegukan": ("detak", 0.80, 0),
                "kandungan": ("whoosh", 0.55, 0), "usia": ("tick", 0.60, 0), "sembilan": ("thump", 0.75, 0),
                "minggu": ("tick", 0.60, 0), "ahli": ("tick", 0.60, 0), "latihan": ("gelembung", 0.50, 0),
                "bernapas": ("angin", 0.45, 0)},
    "tindakan60": {"masuk": ("morph", 0.55, 0), "menahan": ("pop", 0.60, 0), "detik": ("tick", 0.60, 0),
                   "minum": ("gelembung", 0.50, 0), "pelan": ("swish", 0.50, 0), "nyeri": ("thump", 0.75, 0),
                   "dada": ("tick", 0.65, 0), "lemas": ("swish", 0.55, 0), "sulit": ("tick", 0.60, 0),
                   "bicara": ("tick", 0.60, 0), "segera": ("thud", 0.85, 0), "periksa": ("ding", 0.75, 0),
                   "biarkan": ("angin", 0.45, 0)},
    "loop_jam60": {"cegukan": ("detak", 0.55, 0), "singkat": ("tick", 0.55, 0), "normal": ("pop", 0.55, 0),
                   "waspadai": ("tick", 0.55, 0), "tidak": ("thud", 0.60, 0), "berhenti": ("ding", 0.55, 0)},
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
VISUALS60 = {"jam_cegukan60": sc_jam_cegukan, "diafragma60": sc_diafragma,
             "jalur_saraf60": sc_jalur_saraf, "mitos60": sc_mitos,
             "batas_durasi60": sc_batas_durasi, "janin60": sc_janin,
             "tindakan60": sc_tindakan, "loop_jam60": sc_loop_jam}


def _selftest():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (int(D.S(1080)), int(D.S(1920))), CREAM)
    d = ImageDraw.Draw(img)
    for n, fn in VISUALS60.items():
        sc = {"id": "intro" if n.startswith(("jam", "loop")) else "f1", "visual": n, "start": 10.0,
              "dur": 14.0, "badge": "TUBUH · REFLEKS", "hl": "68",
              "lines": ["CEGUKAN 68 TAHUN", "INI SEBABNYA"]}
        for tl in (0.0, 0.12, 0.5, 2.0, 5.0, 8.0, 12.0, 13.5, 13.98):
            fn(img, d, sc, tl, 14.0, 10.0 + tl, D.hexc("#8A5F44"), 1.0, 0.0)
        assert events_v12(sc), n
    print(f"selftest ep52: {len(VISUALS60)} visual OK ({sum(len(v) for v in CUES.values())} cue, "
          f"{sum(len(v) for v in SFX.values())} SFX)")


def daftar():
    V.BEATS.update(BEATS60)
    D.VISUALS.update(VISUALS60)
    M.EVENTS12.update({k: events_v12 for k in CUES})


daftar()


if __name__ == "__main__":
    _selftest()
