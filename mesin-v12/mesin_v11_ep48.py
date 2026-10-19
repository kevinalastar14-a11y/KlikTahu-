"""Mesin v11 - modul visual Ep48 "Kenapa Jantung Tiba-tiba Berdebar Kencang?".

Pola sama dengan mesin_v11_ep43..47: `B48[visual] = {nama: (fraksi, suara)}`; `_t(N, nama, dur)`.
Fraksi disetel dari posisi kata kunci VO (timeline captions, 24 Sep 2026).
Objek: jantung anatomis berdenyut (lobus, aorta, vena, sekat, simpul pemacu SA bercahaya),
garis EKG bergulir yang detaknya SINKRON dengan denyut jantung (bpm bisa naik/turun mulus),
tubuh + otak beralarm + ginjal & kelenjar adrenal + aliran adrenalin di pembuluh darah,
ikon pemicu (kopi, teh, minuman energi, kurang tidur, kurang minum), kamar siang->malam,
penampang dada (jantung mendekat ke dinding dada saat miring kiri), monitor detak ekstra + jeda,
lingkaran napas 4-6 detik, daftar tanda bahaya + ikon rumah sakit.
SFX baru: `detak` (lub-dub) di sfx.py.
"""
import math
import random

import diagrams as D
from diagrams import (INK, CREAM, WHITE, MUTED, RED, BLUE, GREEN, AMBER, FB, FS,
                      mix, seg, clamp, esmooth, eob, font, paste_c,
                      rrect_on, line_on, dot_on, ring_on, poly_on, ell)

import mesin_v11 as M
from mesin_v11 import (_stiker11, _label11, _glow11, _panah11, _partikel11, _judul11, _hdr,
                       GELAP)

B48 = {
    "intro_debar48": {"santai": (0.09, "swish"), "debar": (0.22, "detak"), "dag": (0.30, "thud"),
                      "dig": (0.34, "thud"), "dug": (0.38, "thud"), "leher": (0.51, "pop"),
                      "lari": (0.66, "whoosh"), "tanya": (0.90, "pop")},
    "pemacu48": {"pemacu": (0.10, "whoosh"), "sel": (0.18, "ding"), "serambi": (0.30, "tick"),
                 "sinyal": (0.43, "zap"), "enam": (0.49, "pop"), "seratus": (0.58, "impact"),
                 "istirahat": (0.73, "tick"), "sehari": (0.80, "swish"), "ribu": (0.91, "detak")},
    "alarm48": {"kaget": (0.06, "impact"), "takut": (0.15, "tick"), "alarm": (0.25, "nging"),
                "kelenjar": (0.32, "pop"), "adrenalin": (0.48, "swish_up"), "darah": (0.58, "whoosh"),
                "cepat": (0.78, "detak"), "kuat": (0.94, "impact")},
    "pemicu48": {"bukan": (0.07, "impact"), "kafein": (0.21, "pop"), "kopi": (0.29, "pop"),
                 "teh": (0.33, "pop"), "energi": (0.45, "zap"), "terpacu": (0.65, "detak"),
                 "tidur": (0.72, "thud"), "minum": (0.82, "gelembung")},
    "diam48": {"diam": (0.19, "impact"), "malam": (0.23, "swish"), "sepi": (0.28, "kilau"),
               "otak": (0.41, "pop"), "detak": (0.52, "detak"), "miring": (0.72, "whoosh"),
               "dekat": (0.85, "thud"), "dinding": (0.91, "tick")},
    "lompat48": {"lompat": (0.17, "swish_up"), "ekstra": (0.31, "tick"), "cepat": (0.43, "pop"),
                 "jeda": (0.50, "click"), "keras": (0.72, "detak"), "umum": (0.81, "ding"),
                 "aman": (0.93, "pop")},
    "tenang48": {"cemas": (0.14, "tick"), "tarik": (0.17, "riser"), "buang": (0.30, "whoosh"),
                 "lambat": (0.47, "kilau"), "siaga": (0.66, "ding"), "kafein": (0.73, "pop"),
                 "tidur": (0.81, "pop"), "air": (0.89, "gelembung")},
    "waspada48": {"segera": (0.07, "impact"), "medis": (0.19, "ding"), "nyeri": (0.34, "pop"),
                  "sesak": (0.40, "pop"), "pusing": (0.46, "pop"), "pingsan": (0.57, "thud"),
                  "periksa": (0.61, "swish"), "sering": (0.79, "tick"), "berhenti": (0.92, "tick")},
    "rangkuman48": {"s1": (0.04, "pop"), "s2": (0.27, "pop"), "s3": (0.47, "pop"),
                    "kirim": (0.73, "impact")},
}
for _k, _v in B48.items():
    M.BEATS[_k] = sorted(_v.values())

JANTUNG = (206, 58, 70)
JANTUNG_G = (150, 34, 46)
VENA = (84, 110, 180)
KUNING = (255, 206, 70)
KULIT = (234, 214, 196)
MALAM_A = (26, 32, 58)
MALAM_B = (52, 60, 98)
SIANG_A = (190, 222, 244)
SIANG_B = (236, 244, 250)
EKG = (70, 230, 150)
MONITOR = (16, 30, 30)
ADRENALIN = (255, 170, 40)


def _t(nama, key, dur):
    return B48[nama][key][0] * dur


# ------------------------------------------------------------------ EKG & denyut
def _gelombang(p):
    """Bentuk satu detak EKG (P, QRS, T) untuk fase p dalam 0..1."""
    return (0.13 * math.exp(-((p - 0.15) / 0.03) ** 2)
            - 0.14 * math.exp(-((p - 0.285) / 0.009) ** 2)
            + 1.00 * math.exp(-((p - 0.31) / 0.011) ** 2)
            - 0.28 * math.exp(-((p - 0.335) / 0.011) ** 2)
            + 0.26 * math.exp(-((p - 0.56) / 0.05) ** 2))


def _fase(tt, b0, b1=None, ta=0.0, tb=1.0):
    """Jumlah detak kumulatif sampai waktu tt; bpm naik/turun linear dari b0 ke b1 antara ta..tb."""
    if b1 is None or b1 == b0:
        return tt * b0 / 60.0
    if tt <= ta:
        return tt * b0 / 60.0
    base = ta * b0 / 60.0
    if tt <= tb:
        u = tt - ta
        return base + (b0 * u + (b1 - b0) * u * u / (2 * (tb - ta))) / 60.0
    return base + (b0 + b1) / 2 * (tb - ta) / 60.0 + (tt - tb) * b1 / 60.0


def _bpm_pada(tt, b0, b1=None, ta=0.0, tb=1.0):
    if b1 is None:
        return b0
    return b0 + (b1 - b0) * clamp((tt - ta) / max(1e-3, tb - ta))


def _denyut(fase, kuat=1.0):
    """0..1 lonjakan denyut, puncak tepat saat gelombang R (sinkron dengan EKG)."""
    p = fase % 1.0
    return kuat * (math.exp(-((p - 0.32) / 0.05) ** 2) + 0.35 * math.exp(-((p - 0.58) / 0.06) ** 2))


def _ekg48(img, x0, x1, yb, amp, tl, fase_fn, alpha, col=EKG, pxps=300, width=5, ekstra=None):
    """Garis EKG bergulir; kepala garis di x1 = waktu sekarang. fase_fn(t) = detak kumulatif."""
    if alpha <= 0.01:
        return
    pts = []
    x = x0
    while x <= x1:
        tt = tl - (x1 - x) / pxps
        pts.append((x, yb - amp * _gelombang(fase_fn(tt) % 1.0)))
        x += 3
    M._pline(img, pts, col, width, alpha)
    _glow11(img, pts[-1][0], pts[-1][1], 26, col, alpha)
    dot_on(img, pts[-1][0], pts[-1][1], 7, mix(col, WHITE, 0.5), alpha)


# ------------------------------------------------------------------ jantung anatomis
_HATI = []
for _i in range(72):
    _a = 2 * math.pi * _i / 72
    _HATI.append((16 * math.sin(_a) ** 3,
                  -(13 * math.cos(_a) - 5 * math.cos(2 * _a) - 2 * math.cos(3 * _a) - math.cos(4 * _a)) - 2.5))


def _rot(x, y, deg):
    r = math.radians(deg)
    return x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)


def _jantung48(img, cx, cy, s, alpha, k=1.0, col=JANTUNG, sa=0.0, tg=0.0, sinyal=0.0, detail=True):
    """Jantung bergaya anatomis. s = skala (1 -> lebar ~200 px). k = denyut (1 = diam).
    sa = kecerahan simpul pemacu SA (0..1). sinyal = 0..1 gelombang listrik menyebar dari SA."""
    if alpha <= 0.01:
        return
    u = 6.4 * s * k
    if detail:
        # pembuluh di belakang: vena cava (biru, kiri penonton), aorta (lengkung), arteri paru
        vx = cx - 7.5 * u
        rrect_on(img, vx - 2.2 * u, cy - 21 * u, vx + 2.2 * u, cy - 6 * u, 1.6 * u, VENA, alpha)
        rrect_on(img, cx + 2.5 * u, cy - 19 * u, cx + 7.5 * u, cy - 6 * u, 2.2 * u, mix(col, INK, 0.12), alpha)
        pts = []
        for j in range(19):
            a = math.pi * j / 18
            pts.append((cx - 1.0 * u + 5.2 * u * math.cos(a) * -1, cy - 13 * u - 6.5 * u * math.sin(a)))
        M._pline(img, pts, mix(col, INK, 0.05), 4.2 * u, alpha)
        for dx in (-3.2, 0.3, 3.4):
            a0 = cx - 1.0 * u + dx * u
            line_on(img, (a0, cy - 18.5 * u), (a0 + dx * 0.25 * u, cy - 23.5 * u), mix(col, INK, 0.05),
                    max(2, int(1.6 * u)), alpha)
    pts = [(cx + a, cy + b) for (a, b) in (_rot(x * u, y * u, -14) for (x, y) in _HATI)]
    poly_on(img, pts, col, alpha, outline=mix(col, INK, 0.35), width=max(2, int(0.5 * u)))
    if detail:
        # sekat (garis bilik) + kilap
        sp = [(cx + a, cy + b) for (a, b) in (_rot(x * u, y * u, -14) for (x, y) in
                                             ((1.5, -9.5), (2.4, -4.0), (2.0, 2.0), (0.8, 8.0), (0.0, 13.0)))]
        M._pline(img, sp, mix(col, INK, 0.3), max(2, 0.45 * u), alpha * 0.7)
        ell(img, cx - 10.5 * u, cy - 9 * u, cx - 5.5 * u, cy - 5.2 * u, fill=mix(col, WHITE, 0.55), alpha=alpha * 0.45)
    sx, sy = cx - 8.6 * u, cy - 7.4 * u
    if sinyal > 0:
        R = 26 * u * sinyal
        ring_on(img, sx, sy, R, mix(KUNING, WHITE, 0.3), max(3, int(0.7 * u)), alpha * (1 - sinyal) * 0.9)
    if sa > 0:
        _glow11(img, sx, sy, 5.5 * u, KUNING, alpha * sa)
        dot_on(img, sx, sy, 1.5 * u, mix(KUNING, WHITE, 0.3), alpha * min(1.0, sa * 1.5))


def _sa_xy(cx, cy, s, k=1.0):
    u = 6.4 * s * k
    return cx - 8.6 * u, cy - 7.4 * u


# ------------------------------------------------------------------ tubuh & organ
def _tubuh48(img, cx, top, h, alpha, col=None):
    """Siluet tubuh atas (kepala, leher, bahu, dada) setinggi h."""
    col = col or mix(CREAM, INK, 0.10)
    r = 0.13 * h
    dot_on(img, cx, top + r, r, col, alpha)
    rrect_on(img, cx - 0.06 * h, top + 1.8 * r, cx + 0.06 * h, top + 2.6 * r, 8, col, alpha)
    y0 = top + 2.45 * r
    poly_on(img, [(cx - 0.12 * h, y0), (cx + 0.12 * h, y0), (cx + 0.36 * h, y0 + 0.07 * h),
                  (cx + 0.42 * h, y0 + 0.2 * h), (cx + 0.36 * h, top + h), (cx - 0.36 * h, top + h),
                  (cx - 0.42 * h, y0 + 0.2 * h), (cx - 0.36 * h, y0 + 0.07 * h)], col, alpha)


def _otak48(img, cx, cy, s, alpha, nyala=0.0, tg=0.0):
    base = mix((236, 170, 180), RED, 0.35 * nyala)
    if nyala > 0:
        _glow11(img, cx, cy, 120 * s, RED, alpha * nyala * (0.6 + 0.4 * math.sin(tg * 14) ** 2))
    for (dx, dy_, r) in ((-30, -8, 34), (0, -20, 38), (30, -8, 34), (-18, 16, 30), (18, 16, 30)):
        dot_on(img, cx + dx * s, cy + dy_ * s, r * s, base, alpha, outline=mix(base, INK, 0.3), width=2)
    line_on(img, (cx, cy - 50 * s), (cx, cy + 36 * s), mix(base, INK, 0.35), 3, alpha)


def _ginjal48(img, cx, cy, s, alpha, sisi=1, adrenal=0.0):
    col = (168, 78, 74)
    ell(img, cx - 20 * s, cy - 34 * s, cx + 20 * s, cy + 34 * s, fill=col, alpha=alpha,
        outline=mix(col, INK, 0.3), width=2)
    dot_on(img, cx - sisi * 14 * s, cy, 9 * s, mix(CREAM, INK, 0.10), alpha)
    ac = mix(AMBER, KUNING, 0.3 + 0.5 * adrenal)
    if adrenal > 0:
        _glow11(img, cx + sisi * 2 * s, cy - 42 * s, 40 * s, ADRENALIN, alpha * adrenal)
    poly_on(img, [(cx - 16 * s, cy - 30 * s), (cx + 18 * s, cy - 32 * s), (cx + sisi * 4 * s, cy - 58 * s)],
            ac, alpha, outline=mix(ac, INK, 0.3), width=2)


def _bpm48(img, cx, cy, val, alpha, tg=0.0, col=None, fase=0.0, w=270):
    """Layar kecil detak/menit dengan ikon jantung berdenyut sinkron."""
    col = col or EKG
    rrect_on(img, cx - w / 2, cy - 78, cx + w / 2, cy + 78, 26, MONITOR, alpha, outline=mix(col, MONITOR, 0.5), width=3)
    kk = 1 + 0.25 * _denyut(fase)
    D._icon_heart27(img, cx - w / 2 + 52, cy - 16, 0.9 * kk, JANTUNG, alpha)
    paste_c(img, cx + 34, cy - 12, str(int(round(val))), font(FB, 70), col, alpha)
    paste_c(img, cx + 10, cy + 50, "detak / menit", font(FS, 22), mix(col, WHITE, 0.4), alpha)


def _gelas48(img, cx, base, h, alpha, isi=0.8, tg=0.0):
    w0, w1 = 0.62 * h, 0.48 * h
    top = base - h
    yi = base - h * isi * 0.92
    if isi > 0.01:
        f = (base - yi) / h
        wi = w1 + (w0 - w1) * (1 - f)
        wob = 3 * math.sin(tg * 5)
        poly_on(img, [(cx - wi / 2, yi + wob), (cx + wi / 2, yi - wob), (cx + w1 / 2, base - 4), (cx - w1 / 2, base - 4)],
                mix(BLUE, WHITE, 0.35), alpha)
    M._pline(img, [(cx - w0 / 2, top), (cx - w1 / 2, base), (cx + w1 / 2, base), (cx + w0 / 2, top)],
             mix(INK, CREAM, 0.35), 5, alpha)


def _kaleng48(img, cx, cy, s, alpha):
    rrect_on(img, cx - 34 * s, cy - 64 * s, cx + 34 * s, cy + 64 * s, 14 * s, (40, 44, 60), alpha)
    rrect_on(img, cx - 30 * s, cy - 70 * s, cx + 30 * s, cy - 58 * s, 5 * s, (170, 176, 190), alpha)
    poly_on(img, [(cx + 8 * s, cy - 40 * s), (cx - 16 * s, cy + 6 * s), (cx - 1 * s, cy + 6 * s), (cx - 10 * s, cy + 42 * s),
                  (cx + 18 * s, cy - 8 * s), (cx + 3 * s, cy - 8 * s)], KUNING, alpha)


def _bulan48(img, cx, cy, r, alpha, bg):
    dot_on(img, cx, cy, r, (250, 236, 180), alpha)
    dot_on(img, cx + 0.45 * r, cy - 0.25 * r, 0.9 * r, bg, alpha)


def _kasur48(img, cx, yb, w, alpha, selimut=(96, 120, 190), kulit=KULIT, miring=0.0):
    """Tempat tidur tampak samping + orang berbaring berselimut."""
    rrect_on(img, cx - w / 2, yb - 0.16 * w, cx + w / 2, yb, 14, (120, 86, 60), alpha)
    rrect_on(img, cx - w / 2 - 12, yb - 0.36 * w, cx - w / 2 + 16, yb + 20, 10, (100, 70, 50), alpha)
    rrect_on(img, cx - w / 2 + 10, yb - 0.24 * w, cx + w / 2 - 10, yb - 0.14 * w, 16, (240, 240, 246), alpha)
    rrect_on(img, cx - w / 2 + 24, yb - 0.33 * w, cx - w / 2 + 0.26 * w, yb - 0.22 * w, 22, WHITE, alpha)
    hx, hy = cx - w / 2 + 0.17 * w, yb - 0.31 * w
    dot_on(img, hx, hy, 0.075 * w, kulit, alpha)
    dot_on(img, hx - 0.02 * w, hy - 0.03 * w, 0.06 * w, (60, 44, 36), alpha)
    rrect_on(img, cx - w / 2 + 0.26 * w, yb - 0.33 * w - miring * 0.04 * w, cx + w / 2 - 20, yb - 0.17 * w, 40,
             selimut, alpha)
    return hx, hy


def _rs48(img, cx, cy, s, alpha):
    rrect_on(img, cx - 60 * s, cy - 60 * s, cx + 60 * s, cy + 60 * s, 24 * s, WHITE, alpha,
             outline=mix(RED, WHITE, 0.3), width=5)
    rrect_on(img, cx - 14 * s, cy - 42 * s, cx + 14 * s, cy + 42 * s, 5 * s, RED, alpha)
    rrect_on(img, cx - 42 * s, cy - 14 * s, cx + 42 * s, cy + 14 * s, 5 * s, RED, alpha)


def _baris_bahaya(img, x0, x1, y, teks, col, a, k, ikon="!"):
    rrect_on(img, x0, y - 44, x1, y + 44, 22, mix(WHITE, col, 0.08), a, outline=mix(col, WHITE, 0.5), width=3)
    dot_on(img, x0 + 58, y, 30 * k, col, a)
    paste_c(img, x0 + 58, y, ikon, font(FB, 36), WHITE, a)
    paste_c(img, (x0 + 100 + x1) / 2, y, teks, font(FB, 34), INK, a, scale=0.9 + 0.1 * k)


# ------------------------------------------------------------------ adegan
def sc_intro_debar48(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "intro_debar48"
    L = sc.get("lines") or ["JANTUNG TIBA-TIBA", "BERDEBAR KENCANG?"]
    _judul11(img, L[0], INK, tl, al, y=455, fsz=66, t0=0.05)
    _judul11(img, L[1], accent, tl, al, y=555, fsz=66, t0=0.30, hl="KENCANG?")
    q = esmooth(seg(tl, _t(N, "santai", dur) - 0.6, _t(N, "santai", dur) + 0.2))
    if q <= 0.01:
        return
    td = _t(N, "debar", dur)
    b1 = 64 if tl < td else 64
    fase_fn = lambda tt: _fase(tt, 64, 128, td, td + 0.8)
    bpm = _bpm_pada(tl, 64, 128, td, td + 0.8)
    fz = fase_fn(tl)
    kuat = 0.35 + 0.65 * clamp((tl - td) / 0.8)
    # tubuh + jantung di dada
    top = 690 + dy + (1 - eob(q, 1.3)) * 160
    _tubuh48(img, 540, top, 860, al * q)
    hk = 1 + 0.10 * _denyut(fz, kuat)
    hx, hy = 590, top + 580
    if tl > td:
        _glow11(img, hx, hy, 210 * hk, JANTUNG, al * 0.45 * _denyut(fz, kuat))
    _jantung48(img, hx, hy, 1.25, al * q, k=hk, tg=tg)
    # garis getar di sekitar dada saat berdebar
    if tl > td:
        p = _denyut(fz, kuat)
        for j, sg in enumerate((-1, 1)):
            for m in range(2):
                R = 190 + 40 * m + 30 * p
                x = hx + sg * R
                line_on(img, (x, hy - 40 - 12 * m), (x + sg * 18, hy - 70 - 12 * m), mix(JANTUNG, WHITE, 0.2),
                        6, al * p)
    # EKG di bawah
    _ekg48(img, 130, 950, 1560 + dy, 110, tl, fase_fn, al * q, col=mix(JANTUNG, INK, 0.1), pxps=260, width=6)
    if tl > td:
        _stiker11(img, 790, 1420 + dy, f"{int(round(bpm))} bpm", al, tl - td, bg=GELAP, fsz=30, rot=4, tg=tg)
    # santai
    ts = tl - _t(N, "santai", dur)
    if 0 < ts and tl < td + 0.2:
        _stiker11(img, 280, 800 + dy, "LAGI SANTAI...", al * clamp(1 - (tl - td) / 0.2), ts, bg=mix(BLUE, INK, 0.1),
                  fsz=30, rot=-4, tg=tg)
    for j, (kk, teks, x, y, r) in enumerate((("dag", "DAG!", 230, 1060, -10), ("dig", "DIG!", 850, 960, 8),
                                            ("dug", "DUG!", 250, 1290, 6))):
        tt = tl - _t(N, kk, dur)
        fade = clamp(1 - (tl - _t(N, "leher", dur) + 0.2) / 0.3)
        if tt > 0 and fade > 0:
            D._stamp_on(img, x, y + dy, teks, al * fade, tt, col=JANTUNG, fsz=68, rot=r)
    tt = tl - _t(N, "leher", dur)
    if tt > 0:
        ny = top + 0.13 * 860 * 2.2
        p = _denyut(fz, kuat)
        ring_on(img, 540, ny, 70 + 30 * p, mix(JANTUNG, WHITE, 0.3), 5, al * clamp(tt / 0.3) * (0.4 + 0.6 * p))
        _label11(img, 800, ny - 10, "sampai terasa di leher", mix(JANTUNG, INK, 0.3), al * clamp(tt / 0.4), fsz=26, name=FB)
    tt = tl - _t(N, "lari", dur)
    if tt > 0:
        _stiker11(img, 310, 1430 + dy, "PADAHAL TIDAK LARI", al, tt, bg=accent, fsz=30, rot=-5, tg=tg)
    tt = tl - _t(N, "tanya", dur)
    if tt > 0:
        _stiker11(img, 830, 1110 + dy, "KENAPA?", al, tt, bg=RED, fsz=40, rot=5, tg=tg)


def sc_pemacu48(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "pemacu48"
    _hdr(img, sc, accent, tl, al)
    tp = _t(N, "pemacu", dur)
    q = esmooth(seg(tl, tp - 0.4, tp + 0.4))
    if q <= 0.01:
        return
    fase_fn = lambda tt: _fase(tt, 72)
    fz = fase_fn(tl)
    hk = 1 + 0.07 * _denyut(fz)
    hx, hy = 520, 1010 + dy
    s = 1.35 * (0.8 + 0.2 * eob(q, 1.4))
    ts = _t(N, "sel", dur)
    tsi = _t(N, "sinyal", dur)
    sa = clamp((tl - ts) / 0.4)
    if tl > ts:
        sa *= 0.7 + 0.3 * _denyut(fz)
    sig = (fz - 0.12) % 1.0 if tl > tsi else 0.0
    _jantung48(img, hx, hy, s, al * q, k=hk, sa=sa, tg=tg, sinyal=sig)
    sx, sy = _sa_xy(hx, hy, s, hk)
    if tl > ts:
        a = al * clamp((tl - ts) / 0.4)
        ring_on(img, sx, sy, 34 + 6 * math.sin(tg * 6), KUNING, 4, a)
        line_on(img, (sx - 30, sy - 10), (230, 780 + dy), mix(INK, CREAM, 0.4), 3, a)
        _label11(img, 230, 750 + dy, "pemacu alami", mix(AMBER, INK, 0.3), a, fsz=28, name=FB)
    tt = tl - _t(N, "serambi", dur)
    if tt > 0:
        a = al * clamp(tt / 0.4)
        line_on(img, (sx - 10, sy + 60), (200, 1180 + dy), mix(INK, CREAM, 0.4), 3, a)
        dot_on(img, sx - 10, sy + 60, 6, INK, a)
        _label11(img, 200, 1210 + dy, "serambi kanan", INK, a, fsz=26, name=FB)
    if tl > tsi:
        a = al * clamp((tl - tsi) / 0.4)
        _label11(img, 840, 760 + dy, "sinyal listrik", mix(AMBER, INK, 0.3), a, fsz=26, name=FB)
        for j in range(3):
            x = 700 + j * 40
            M._pline(img, [(x, 800 + dy), (x + 14, 820 + dy), (x - 6, 836 + dy), (x + 10, 858 + dy)], KUNING, 5, a)
    # EKG + angka
    _ekg48(img, 130, 950, 1380 + dy, 70, tl, fase_fn, al * q, col=mix(JANTUNG, INK, 0.1), pxps=240, width=5)
    te = tl - _t(N, "enam", dur)
    tsr = tl - _t(N, "seratus", dur)
    tsh = tl - _t(N, "sehari", dur)
    if te > 0:
        a = al * clamp(te / 0.3) * (1 - clamp((tsh - 0.0) / 0.4) if tsh > 0 else 1)
        rrect_on(img, 150, 1450 + dy, 930, 1640 + dy, 30, WHITE, a, outline=mix(INK, CREAM, 0.7), width=2)
        k = eob(clamp(te / 0.4), 1.8)
        txt = "60" if tsr <= 0 else "60 - 100"
        paste_c(img, 540, 1520 + dy, txt, font(FB, 84), mix(JANTUNG, INK, 0.15), a, scale=0.85 + 0.15 * k)
        ti = tl - _t(N, "istirahat", dur)
        sub = "kali per menit" + (" - saat istirahat" if ti > 0 else "")
        paste_c(img, 540, 1596 + dy, sub, font(FS, 28), MUTED, a)
    if tsh > 0:
        a = al * clamp(tsh / 0.4)
        rrect_on(img, 150, 1450 + dy, 930, 1640 + dy, 30, mix(WHITE, JANTUNG, 0.06), a, outline=mix(JANTUNG, WHITE, 0.5), width=3)
        paste_c(img, 540, 1478 + dy, "dalam 1 hari", font(FB, 26), MUTED, a)
        tr = _t(N, "ribu", dur)
        if tl > tr - 0.9:
            D._hitung_on(img, 540, 1545 + dy, 100000, "", al, tl, t0=tr - 0.9, dur=1.0, col=mix(JANTUNG, INK, 0.15), fsz=78)
            paste_c(img, 540, 1606 + dy, "detak", font(FS, 26), MUTED, a * clamp((tl - tr + 0.2) / 0.3))
    tt = tl - _t(N, "ribu", dur)
    if tt > 0.2:
        _stiker11(img, 800, 1440 + dy, "TANPA ISTIRAHAT", al, tt - 0.2, bg=RED, fsz=24, rot=5, tg=tg)


def sc_alarm48(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "alarm48"
    _hdr(img, sc, accent, tl, al)
    tk = _t(N, "kaget", dur)
    q = esmooth(seg(tl, tk - 0.4, tk + 0.3))
    if q <= 0.01:
        return
    tc = _t(N, "cepat", dur)
    fase_fn = lambda tt: _fase(tt, 72, 124, tc - 0.4, tc + 1.0)
    fz = fase_fn(tl)
    bpm = _bpm_pada(tl, 72, 124, tc - 0.4, tc + 1.0)
    tkuat = tl - _t(N, "kuat", dur)
    kuat = 1.0 + 0.8 * clamp(tkuat / 0.4) if tkuat > 0 else 1.0
    bx = 340
    top = 690 + dy
    _tubuh48(img, bx, top, 950, al * q)
    # otak
    ta = tl - _t(N, "alarm", dur)
    ny = clamp(ta / 0.3) if ta > 0 else 0.0
    _otak48(img, bx, top + 125, 1.0, al * q, nyala=ny, tg=tg)
    if ta > 0:
        for j in range(3):
            u = ((ta * 0.9) + j / 3) % 1.0
            ring_on(img, bx, top + 120, 90 + 150 * u, RED, 5, al * (1 - u) * 0.8)
        _stiker11(img, bx, top - 10, "ALARM!", al, ta, bg=RED, fsz=30, rot=-5, tg=tg)
    # jantung
    hk = 1 + 0.08 * _denyut(fz, kuat)
    hx, hy = bx + 40, top + 520
    if tkuat > 0:
        _glow11(img, hx, hy, 150, JANTUNG, al * 0.5 * _denyut(fz))
    _jantung48(img, hx, hy, 0.62, al * q, k=hk, tg=tg, detail=True)
    # ginjal + adrenal
    tkel = tl - _t(N, "kelenjar", dur)
    tad = tl - _t(N, "adrenalin", dur)
    adr = clamp(tkel / 0.4) if tkel > 0 else 0.0
    gy = top + 790
    _ginjal48(img, bx - 90, gy, 1.0, al * q, sisi=1, adrenal=adr)
    _ginjal48(img, bx + 90, gy, 1.0, al * q, sisi=-1, adrenal=adr)
    if tkel > 0:
        a = al * clamp(tkel / 0.4)
        line_on(img, (bx + 96, gy - 50), (720, gy - 70), mix(INK, CREAM, 0.4), 3, a)
        dot_on(img, bx + 96, gy - 50, 6, INK, a)
        _label11(img, 850, gy - 90, "kelenjar adrenal", mix(AMBER, INK, 0.3), a, fsz=24, name=FB)
        _label11(img, 850, gy - 56, "(di atas ginjal)", MUTED, a, fsz=22)
    # pembuluh darah + aliran adrenalin
    tdr = tl - _t(N, "darah", dur)
    p0, p1, p2 = (bx + 20, gy - 60), (bx + 170, top + 640), (hx + 50, hy + 40)
    if tad > 0:
        pts = [M._bez(p0, p1, p2, j / 20) for j in range(21)]
        M._pline(img, pts, mix(JANTUNG, WHITE, 0.15), 12, al * clamp(tad / 0.4) * (0.6 + 0.4 * clamp(tdr / 0.3) if tdr > 0 else 0.6))
        for j in range(9):
            u = ((tad * 0.55) + j / 9) % 1.0
            x, y = M._bez(p0, p1, p2, u)
            dot_on(img, x, y, 9, ADRENALIN, al * clamp(tad / 0.4))
        _stiker11(img, 790, gy + 20, "ADRENALIN", al, tad, bg=AMBER, fsz=32, rot=4, tg=tg)
    if tdr > 0:
        _label11(img, 800, gy + 100, "masuk ke dalam darah", mix(JANTUNG, INK, 0.3), al * clamp(tdr / 0.4), fsz=24, name=FB)
    # kaget / takut
    t1 = tl - tk
    if t1 > 0 and ta < 0.6:
        _stiker11(img, 790, 820 + dy, "KAGET!", al * clamp(1 - (ta - 0.3) / 0.3 if ta > 0.3 else 1), t1, bg=GELAP,
                  fsz=34, rot=6, tg=tg)
    t2 = tl - _t(N, "takut", dur)
    if t2 > 0 and ta < 0.6:
        _stiker11(img, 800, 930 + dy, "CEMAS / TAKUT", al * clamp(1 - (ta - 0.3) / 0.3 if ta > 0.3 else 1), t2,
                  bg=mix(BLUE, INK, 0.2), fsz=26, rot=-4, tg=tg)
    # monitor bpm (kanan atas)
    if ta > 0.4:
        a = al * clamp((ta - 0.4) / 0.4)
        _bpm48(img, 800, 880 + dy, bpm, a, tg=tg, fase=fz, col=EKG if bpm < 100 else mix(EKG, KUNING, 0.8))
    tt = tl - tc
    if tt > 0:
        _stiker11(img, 800, 1000 + dy, "LEBIH CEPAT", al, tt, bg=RED, fsz=26, rot=5, tg=tg)
    if tkuat > 0:
        D._stamp_on(img, hx + 170, hy - 60, "KUAT!", al, tkuat, col=JANTUNG, fsz=50, rot=-8)


def sc_pemicu48(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "pemicu48"
    _hdr(img, sc, accent, tl, al)
    tb = _t(N, "bukan", dur)
    q = esmooth(seg(tl, tb - 0.3, tb + 0.4))
    if q <= 0.01:
        return
    ttp = _t(N, "terpacu", dur)
    fase_fn = lambda tt: _fase(tt, 70, 112, ttp - 0.3, ttp + 0.9)
    fz = fase_fn(tl)
    bpm = _bpm_pada(tl, 70, 112, ttp - 0.3, ttp + 0.9)
    hx, hy = 540, 1170 + dy
    hk = 1 + 0.09 * _denyut(fz)
    tpc = tl - ttp
    if tpc > 0:
        _glow11(img, hx, hy, 170, JANTUNG, al * 0.45 * _denyut(fz))
    _jantung48(img, hx, hy, 0.8, al * q, k=hk, tg=tg)
    if tpc > 0:
        _stiker11(img, hx, hy + 185, f"{int(round(bpm))} bpm", al, tpc, bg=GELAP, fsz=30, rot=-3, tg=tg)
    # hantu/takut dicoret
    t0 = tl - tb
    if t0 > 0:
        a = al * clamp(t0 / 0.3) * (1 - clamp((tl - _t(N, "kafein", dur)) / 0.4))
        if a > 0.01:
            rrect_on(img, 330, 760 + dy, 750, 880 + dy, 30, WHITE, a, outline=mix(INK, CREAM, 0.6), width=2)
            paste_c(img, 540, 820 + dy, "rasa takut", font(FB, 40), INK, a)
            line_on(img, (350, 850 + dy), (730, 790 + dy), RED, 9, a)
    # baris atas: kafein
    tk = tl - _t(N, "kafein", dur)
    if tk > 0:
        _stiker11(img, 540, 700 + dy, "KAFEIN", al, tk, bg=mix(AMBER, INK, 0.2), fsz=32, rot=-3, tg=tg)
    ic = [("kopi", 250, "kopi"), ("teh", 540, "teh pekat"), ("energi", 830, "minuman energi")]
    for (kk, x, lab) in ic:
        tt = tl - _t(N, kk, dur)
        if tt <= 0:
            continue
        k = eob(clamp(tt / 0.4), 1.8)
        a = al * clamp(tt / 0.2)
        y = 870 + dy
        dot_on(img, x, y, 88 * k, WHITE, a, outline=mix(AMBER, WHITE, 0.4), width=4)
        if kk == "kopi":
            D._icon_kopi28(img, x - 6, y + 4, 2.4 * k, (110, 70, 40), a, tg=tg)
        elif kk == "teh":
            D._icon_kopi28(img, x - 6, y + 4, 2.4 * k, (170, 100, 40), a, tg=tg + 1)
        else:
            _kaleng48(img, x, y, 0.95 * k, a)
        _label11(img, x, y + 118, lab, INK, a, fsz=24, name=FB)
        if tpc > 0:
            _panah11(img, (x, y + 150), (hx + (x - hx) * 0.25, hy - 150), al * clamp(tpc / 0.4), clamp(tpc / 0.5),
                     mix(AMBER, INK, 0.1), width=6, lengkung=0.15, head=16)
    # baris bawah
    tt = tl - _t(N, "tidur", dur)
    if tt > 0:
        k = eob(clamp(tt / 0.4), 1.8)
        a = al * clamp(tt / 0.2)
        x, y = 230, 1460 + dy
        dot_on(img, x, y, 90 * k, MALAM_A, a)
        _bulan48(img, x - 10, y - 10, 34 * k, a, MALAM_A)
        paste_c(img, x + 40, y - 40, "z", font(FB, 30), WHITE, a)
        paste_c(img, x + 58, y - 64, "z", font(FB, 24), WHITE, a)
        line_on(img, (x - 60, y + 60), (x + 60, y - 60), RED, 8, a)
        _label11(img, x, y + 120, "kurang tidur", INK, a, fsz=26, name=FB)
    tt = tl - _t(N, "minum", dur)
    if tt > 0:
        k = eob(clamp(tt / 0.4), 1.8)
        a = al * clamp(tt / 0.2)
        x, y = 850, 1460 + dy
        dot_on(img, x, y, 90 * k, WHITE, a, outline=mix(BLUE, WHITE, 0.4), width=4)
        _gelas48(img, x, y + 55, 110 * k, a, isi=0.14, tg=tg)
        _label11(img, x, y + 120, "kurang minum", INK, a, fsz=26, name=FB)


def sc_diam48(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "diam48"
    _hdr(img, sc, accent, tl, al)
    tdm = _t(N, "diam", dur)
    q = esmooth(seg(tl, tdm - 0.9, tdm - 0.2))
    if q <= 0.01:
        return
    tm = _t(N, "malam", dur)
    mn = esmooth(seg(tl, tm - 0.1, tm + 0.8))
    x0, y0, x1, y1 = 110, 690 + dy, 970, 1240 + dy
    atas = mix(SIANG_A, MALAM_A, mn)
    bawah = mix(SIANG_B, MALAM_B, mn)
    rrect_on(img, x0, y0, x1, y1, 30, bawah, al * q)
    rrect_on(img, x0, y0, x1, y0 + 300, 30, atas, al * q)
    rrect_on(img, x0, y0 + 200, x1, y0 + 320, 0, mix(atas, bawah, 0.5), al * q * 0.6)
    # jendela
    wx0, wy0 = 640, y0 + 50
    rrect_on(img, wx0, wy0, wx0 + 250, wy0 + 200, 14, mix((250, 250, 255), (20, 26, 50), mn), al * q,
             outline=mix(WHITE, (90, 100, 140), mn), width=8)
    if mn > 0:
        _bulan48(img, wx0 + 170, wy0 + 70, 36, al * mn, mix((250, 250, 255), (20, 26, 50), mn))
        rng = random.Random(4)
        for j in range(9):
            sx, sy = x0 + rng.uniform(40, 480), y0 + rng.uniform(40, 220)
            dot_on(img, sx, sy, 3 + 2 * math.sin(tg * 3 + j), WHITE, al * mn * 0.8)
    else:
        dot_on(img, wx0 + 180, wy0 + 70, 34, (255, 214, 90), al * q)
    # kebisingan siang (memudar saat malam)
    if mn < 1:
        a = al * q * (1 - mn)
        for j, (x, y, t_) in enumerate(((230, y0 + 90, "tin tin!"), (470, y0 + 150, "notif!"), (260, y0 + 210, "ramai"))):
            rrect_on(img, x - 80, y - 28, x + 80, y + 28, 24, WHITE, a, outline=mix(INK, CREAM, 0.6), width=2)
            paste_c(img, x, y, t_, font(FB, 26), INK, a)
    yb = y1 - 40
    hx, hy = _kasur48(img, 470, yb, 640, al * q, miring=0.0)
    fase_fn = lambda tt: _fase(tt, 74)
    fz = fase_fn(tl)
    tt_d = tl - tdm
    fo = clamp(1 - (tl - _t(N, "otak", dur) + 0.2) / 0.3)
    if tt_d > 0 and fo > 0:
        _stiker11(img, 430, y0 + 130, "SAAT DIAM", al * fo, tt_d, bg=accent, fsz=30, rot=-5, tg=tg)
    ts = tl - _t(N, "sepi", dur)
    if ts > 0:
        _label11(img, 210, y0 + 50, "sepi...", WHITE, al * clamp(ts / 0.4), fsz=30, name=FB)
    to = tl - _t(N, "otak", dur)
    cx_, cy_ = hx + 180, hy - 190
    if to > 0:
        a = al * clamp(to / 0.4)
        for j, (dx_, r) in enumerate(((40, 10), (80, 16))):
            dot_on(img, hx + dx_, hy - 40 - dx_ * 0.8, r, WHITE, a)
        rrect_on(img, cx_ - 120, cy_ - 70, cx_ + 120, cy_ + 70, 60, WHITE, a)
        kk = 1 + 0.3 * _denyut(fz)
        D._icon_heart27(img, cx_ - 50, cy_ - 4, 1.2 * kk, JANTUNG, a)
        paste_c(img, cx_ + 44, cy_, "dug..", font(FB, 32), JANTUNG, a)
    tdk = tl - _t(N, "detak", dur)
    if tdk > 0:
        p = _denyut(fz)
        cxp, cyp = hx + 190, yb - 150
        for m in range(3):
            ring_on(img, cxp, cyp, 30 + 40 * m + 25 * p, mix(JANTUNG, WHITE, 0.3), 4, al * clamp(tdk / 0.4) * p * (1 - m * 0.25))
        _label11(img, 800, y0 + 290, "detak jadi terasa", mix(JANTUNG, WHITE, 0.55), al * clamp(tdk / 0.4), fsz=24, name=FB)
    # penampang dada (miring kiri)
    tmr = tl - _t(N, "miring", dur)
    if tmr > 0:
        a = al * clamp(tmr / 0.4)
        py0, py1 = 1280 + dy, 1650 + dy
        rrect_on(img, x0, py0, x1, py1, 30, WHITE, a, outline=mix(INK, CREAM, 0.7), width=2)
        paste_c(img, 300, py0 + 38, "tidur miring ke kiri", font(FB, 26), INK, a)
        ccx, ccy = 380, py0 + 205
        ell(img, ccx - 190, ccy - 125, ccx + 190, ccy + 125, fill=mix(KULIT, WHITE, 0.3), alpha=a,
            outline=mix(KULIT, INK, 0.35), width=10)
        # tulang belakang (kanan penampang) & kasur di sisi kiri tubuh (bawah)
        dot_on(img, ccx, ccy + 95, 22, mix(CREAM, INK, 0.2), a)
        rrect_on(img, ccx - 250, ccy + 140, ccx + 250, ccy + 160, 10, (120, 86, 60), a)
        dk = tl - _t(N, "dekat", dur)
        geser = esmooth(clamp(dk / 0.8)) if dk > 0 else 0.0
        jx = ccx + 20 - 0 * geser
        jy = ccy - 10 + 70 * geser
        kk = 1 + 0.10 * _denyut(fz)
        _jantung48(img, jx, jy, 0.42, a, k=kk, detail=False)
        paste_c(img, ccx + 300, py0 + 110, "sisi kiri", font(FS, 22), MUTED, a)
        _panah11(img, (ccx + 300, py0 + 140), (ccx + 200, ccy + 150), a, clamp(tmr / 0.6), MUTED, width=4, lengkung=0.2, head=12)
        if dk > 0:
            p = _denyut(fz)
            ring_on(img, jx, ccy + 125, 30 + 20 * p, JANTUNG, 4, a * p)
            _stiker11(img, 790, py0 + 220, "LEBIH DEKAT", al, dk, bg=JANTUNG, fsz=28, rot=4, tg=tg)
        tdd = tl - _t(N, "dinding", dur)
        if tdd > 0:
            _label11(img, 790, py0 + 300, "ke dinding dada", mix(JANTUNG, INK, 0.3), al * clamp(tdd / 0.3), fsz=26, name=FB)


def sc_lompat48(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "lompat48"
    _hdr(img, sc, accent, tl, al)
    tlp = _t(N, "lompat", dur)
    q = esmooth(seg(tl, tlp - 0.5, tlp + 0.2))
    if q <= 0.01:
        return
    x0, y0, x1, y1 = 110, 700 + dy, 970, 1180 + dy
    rrect_on(img, x0, y0, x1, y1, 30, MONITOR, al * q, outline=mix(EKG, MONITOR, 0.6), width=4)
    for gx in range(x0 + 40, x1, 60):
        line_on(img, (gx, y0 + 20), (gx, y1 - 20), mix(MONITOR, EKG, 0.12), 1, al * q)
    for j in range(7):
        gy = y0 + 40 + 60 * j
        line_on(img, (x0 + 20, gy), (x1 - 20, gy), mix(MONITOR, EKG, 0.12), 1, al * q)
    # jalur statis: 3 detak normal, 1 detak ekstra (dini), jeda panjang, detak keras
    base = y0 + 330
    beats = [(170, 1.0, 1.0), (330, 1.0, 1.0), (490, 1.0, 1.0), (590, 0.75, 0.8), (840, 1.45, 1.25)]
    te = _t(N, "ekstra", dur)
    tk = _t(N, "keras", dur)
    tj_ = _t(N, "jeda", dur)
    kf = [(tlp - 0.4, x0 + 30), (te + 0.25, 640), (tj_ + 0.2, 700), (tk - 0.05, 830), (tk + 0.6, x1 - 30)]
    if tl <= kf[0][0]:
        xh = kf[0][1]
    elif tl >= kf[-1][0]:
        xh = kf[-1][1]
    else:
        for (ta_, xa), (tb_, xb) in zip(kf, kf[1:]):
            if ta_ <= tl <= tb_:
                xh = xa + (xb - xa) * (tl - ta_) / max(1e-3, tb_ - ta_)
                break
    pts = []
    x = x0 + 30
    while x <= xh:
        y = 0.0
        for (bx, amp, wd) in beats:
            p = (x - bx) / (140 * wd) + 0.31
            if 0 <= p <= 1:
                y += amp * _gelombang(p)
        pts.append((x, base - 210 * y))
        x += 3
    if len(pts) > 1:
        M._pline(img, pts, EKG, 6, al * q)
        _glow11(img, pts[-1][0], pts[-1][1], 26, EKG, al * q)
    # label
    tt = tl - te
    if tt > 0 and xh > 560:
        a = al * clamp(tt / 0.4)
        ring_on(img, 590, base - 150, 60, KUNING, 5, a)
        _label11(img, 590, y0 + 50, "detak ekstra", KUNING, a, fsz=26, name=FB)
    tt = tl - _t(N, "cepat", dur)
    if tt > 0:
        _label11(img, 590, y0 + 86, "datang terlalu cepat", mix(KUNING, WHITE, 0.4), al * clamp(tt / 0.4), fsz=22, name=FB)
    tt = tl - _t(N, "jeda", dur)
    if tt > 0 and xh > 650:
        a = al * clamp(tt / 0.4)
        line_on(img, (640, base + 30), (790, base + 30), WHITE, 4, a)
        line_on(img, (640, base + 14), (640, base + 46), WHITE, 4, a)
        line_on(img, (790, base + 14), (790, base + 46), WHITE, 4, a)
        _label11(img, 715, base + 66, "jeda", WHITE, a, fsz=26, name=FB)
    tt = tl - tk
    if tt > 0:
        a = al * clamp(tt / 0.3)
        ring_on(img, 840, base - 200, 70, mix(JANTUNG, WHITE, 0.3), 5, a)
        _label11(img, 800, y1 - 30, "detak lebih keras", mix(JANTUNG, WHITE, 0.45), a, fsz=24, name=FB)
    # jantung melompat di bawah
    tj = tl - tlp
    yj = 1400 + dy
    lomp = 0.0
    if tj > 0:
        lomp = math.exp(-((tj - 0.25) / 0.18) ** 2)
    kk = 1.0
    if tt > 0:
        kk = 1 + 0.22 * math.exp(-((tt - 0.1) / 0.15) ** 2) + 0.05 * _denyut(_fase(tl, 70))
    else:
        kk = 1 + 0.05 * _denyut(_fase(tl, 70))
    _jantung48(img, 330, yj - 120 * lomp, 0.72, al * q, k=kk, tg=tg)
    if tj > 0:
        _stiker11(img, 330, 1590 + dy, "SEPERTI MELOMPAT", al, tj, bg=accent, fsz=26, rot=-4, tg=tg)
    tu = tl - _t(N, "umum", dur)
    if tu > 0:
        _stiker11(img, 760, 1330 + dy, "SANGAT UMUM", al, tu, bg=GELAP, fsz=30, rot=4, tg=tg)
    ta = tl - _t(N, "aman", dur)
    if ta > 0:
        a = al * clamp(ta / 0.3)
        rrect_on(img, 580, 1420 + dy, 960, 1620 + dy, 28, WHITE, a, outline=mix(GREEN, WHITE, 0.4), width=4)
        D._check5_on(img, 650, 1520 + dy, 60, "check", a, clamp(ta / 0.5), col=GREEN)
        paste_c(img, 810, 1495 + dy, "biasanya", font(FB, 28), INK, a)
        paste_c(img, 810, 1545 + dy, "tidak berbahaya", font(FB, 26), mix(GREEN, INK, 0.2), a)


def sc_tenang48(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "tenang48"
    _hdr(img, sc, accent, tl, al)
    tc = _t(N, "cemas", dur)
    q = esmooth(seg(tl, tc - 0.4, tc + 0.3))
    if q <= 0.01:
        return
    tr = _t(N, "tarik", dur)
    tlb = _t(N, "lambat", dur)
    fase_fn = lambda tt: _fase(tt, 112, 74, tlb - 0.5, tlb + 3.0)
    fz = fase_fn(tl)
    bpm = _bpm_pada(tl, 112, 74, tlb - 0.5, tlb + 3.0)
    cx, cy = 540, 1000 + dy
    # siklus napas: tarik 4 dtk, buang 6 dtk
    napas = 0.0
    fasa = ""
    if tl > tr:
        u = (tl - tr) % 10.0
        if u < 4.0:
            napas = esmooth(u / 4.0); fasa = "tarik..."
        else:
            napas = 1 - esmooth((u - 4.0) / 6.0); fasa = "buang..."
    R = 130 + 120 * napas
    col = mix(accent, WHITE, 0.72)
    dot_on(img, cx, cy, 270, mix(CREAM, accent, 0.06), al * q)
    ring_on(img, cx, cy, 270, mix(accent, WHITE, 0.5), 4, al * q)
    dot_on(img, cx, cy, R, col, al * q)
    ring_on(img, cx, cy, R, accent, 6, al * q)
    if fasa:
        paste_c(img, cx, cy - 20, fasa, font(FB, 46), mix(accent, INK, 0.3), al * q)
        u = (tl - tr) % 10.0
        n = int(4 - u) + 1 if u < 4 else int(10 - u) + 1
        paste_c(img, cx, cy + 40, str(n), font(FB, 40), mix(accent, INK, 0.1), al * q)
    else:
        _jantung48(img, cx, cy, 0.7, al * q, k=1 + 0.1 * _denyut(fz), tg=tg)
    tt = tl - tc
    if tt > 0 and tl < tr + 0.2:
        _stiker11(img, 800, 760 + dy, "CEMAS?", al, tt, bg=GELAP, fsz=30, rot=5, tg=tg)
    tt = tl - tr
    if tt > 0:
        _label11(img, 240, 760 + dy, "tarik 4 detik", mix(accent, INK, 0.3), al * clamp(tt / 0.4), fsz=26, name=FB)
    tt = tl - _t(N, "buang", dur)
    if tt > 0:
        _label11(img, 840, 1240 + dy, "buang 6 detik", mix(accent, INK, 0.3), al * clamp(tt / 0.4), fsz=26, name=FB)
        _stiker11(img, 240, 1240 + dy, "LEBIH PANJANG", al, tt, bg=accent, fsz=24, rot=-4, tg=tg)
    tt = tl - tlb
    if tt > 0:
        a = al * clamp(tt / 0.4)
        _bpm48(img, 800, 830 + dy, bpm, a, tg=tg, fase=fz, w=250)
    tt = tl - _t(N, "siaga", dur)
    if tt > 0:
        a = al * clamp(tt / 0.4)
        rrect_on(img, 190, 1310 + dy, 890, 1380 + dy, 35, WHITE, a, outline=mix(INK, CREAM, 0.7), width=2)
        paste_c(img, 330, 1345 + dy, "mode siaga", font(FB, 28), RED, a)
        _panah11(img, (450, 1345 + dy), (610, 1345 + dy), a, clamp(tt / 0.5), INK, width=5, lengkung=0.0, head=14)
        paste_c(img, 740, 1345 + dy, "tenang", font(FB, 28), GREEN, a)
    items = [("kafein", 250, "kurangi kafein"), ("tidur", 540, "cukup tidur"), ("air", 830, "cukup minum")]
    for (kk, x, lab) in items:
        tt = tl - _t(N, kk, dur)
        if tt <= 0:
            continue
        k = eob(clamp(tt / 0.4), 1.8)
        a = al * clamp(tt / 0.2)
        y = 1500 + dy
        dot_on(img, x, y, 76 * k, WHITE, a, outline=mix(accent, WHITE, 0.4), width=4)
        if kk == "kafein":
            D._icon_kopi28(img, x - 4, y + 2, 2.0 * k, (110, 70, 40), a, tg=tg)
            dot_on(img, x + 50, y - 50, 18, RED, a)
            rrect_on(img, x + 40, y - 53, x + 60, y - 47, 2, WHITE, a)
        elif kk == "tidur":
            dot_on(img, x, y, 60 * k, MALAM_A, a)
            _bulan48(img, x - 6, y - 4, 30 * k, a, MALAM_A)
        else:
            _gelas48(img, x, y + 46, 92 * k, a, isi=0.8, tg=tg)
        _label11(img, x, y + 106, lab, INK, a, fsz=24, name=FB)


def sc_waspada48(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "waspada48"
    _hdr(img, sc, accent, tl, al)
    ts = _t(N, "segera", dur)
    q = esmooth(seg(tl, ts - 0.3, ts + 0.3))
    if q <= 0.01:
        return
    k0 = eob(q, 1.6)
    _rs48(img, 210, 740 + dy, 0.9 * k0, al * q)
    tm = tl - _t(N, "medis", dur)
    _stiker11(img, 600, 740 + dy, "SEGERA KE DOKTER", al, tl - ts, bg=RED, fsz=34, rot=-3, tg=tg)
    if tm > 0:
        _label11(img, 600, 815 + dy, "kalau debaran disertai:", MUTED, al * clamp(tm / 0.4), fsz=26, name=FB)
    rows = [("nyeri", "nyeri dada"), ("sesak", "sesak napas"), ("pusing", "pusing berat"), ("pingsan", "pingsan")]
    for i, (kk, teks) in enumerate(rows):
        tt = tl - _t(N, kk, dur)
        if tt <= 0:
            continue
        k = eob(clamp(tt / 0.4), 1.8)
        a = al * clamp(tt / 0.2)
        y = 910 + i * 104 + dy
        _baris_bahaya(img, 150, 930, y, teks, RED, a, k)
    tp = tl - _t(N, "periksa", dur)
    if tp > 0:
        a = al * clamp(tp / 0.4)
        y0 = 1350 + dy
        rrect_on(img, 150, y0, 930, y0 + 290, 30, mix(WHITE, AMBER, 0.06), a, outline=mix(AMBER, WHITE, 0.4), width=3)
        paste_c(img, 540, y0 + 45, "periksakan juga kalau:", font(FB, 28), mix(AMBER, INK, 0.3), a)
        for j, (kk, teks) in enumerate((("sering", "makin sering"), ("berhenti", "tidak kunjung berhenti"))):
            tt = tl - _t(N, kk, dur)
            if tt <= 0:
                continue
            k = eob(clamp(tt / 0.4), 1.8)
            y = y0 + 125 + j * 100
            dot_on(img, 230, y, 26 * k, AMBER, a)
            paste_c(img, 230, y, "!", font(FB, 30), WHITE, a)
            paste_c(img, 560, y, teks, font(FB, 32), INK, a * clamp(tt / 0.2))


def sc_rangkuman48(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "rangkuman48"
    _hdr(img, sc, accent, tl, al)
    items = [("s1", "DEBARAN = ADRENALIN", "alarm tubuh, biasanya tidak berbahaya", JANTUNG),
             ("s2", "KAFEIN & KURANG TIDUR", "bisa jadi pemicunya", AMBER),
             ("s3", "NYERI DADA / PINGSAN?", "segera ke dokter", RED)]
    for i, (kk, a_, b_, col) in enumerate(items):
        tt = tl - _t(N, kk, dur)
        if tt <= 0:
            continue
        k = eob(clamp(tt / 0.4), 1.8)
        y = 800 + i * 190 + dy
        a = al * clamp(tt / 0.15)
        rrect_on(img, 110, y - 74, 970, y + 74, 32, mix(WHITE, col, 0.07), a, outline=mix(col, WHITE, 0.45), width=3)
        dot_on(img, 195, y, 46 * k, col, a)
        paste_c(img, 195, y, str(i + 1), font(FB, 40), WHITE, a)
        paste_c(img, 590, y - 20, a_, font(FB, 32), INK, a, scale=0.85 + 0.15 * k)
        paste_c(img, 590, y + 26, b_, font(FS, 24), MUTED, a)
        _partikel11(img, 195, y, tt, col, al, n=8, jarak=70, seed=i)
    tt = tl - _t(N, "kirim", dur)
    if tt > 0:
        _stiker11(img, 400, 1420 + dy, "KIRIM KE TEMAN", al, tt, bg=accent, fsz=38, rot=-4, tg=tg)
        _label11(img, 400, 1505 + dy, "yang jantungnya suka dag dig dug", MUTED, al * clamp(tt / 0.3), fsz=24)
        k = eob(clamp(tt / 0.4), 1.8)
        fz = _fase(tl, 90)
        _jantung48(img, 830, 1470 + dy, 0.55 * k, al, k=1 + 0.1 * _denyut(fz), tg=tg)


VISUALS48 = {
    "intro_debar48": sc_intro_debar48, "pemacu48": sc_pemacu48, "alarm48": sc_alarm48,
    "pemicu48": sc_pemicu48, "diam48": sc_diam48, "lompat48": sc_lompat48, "tenang48": sc_tenang48,
    "waspada48": sc_waspada48, "rangkuman48": sc_rangkuman48,
}
