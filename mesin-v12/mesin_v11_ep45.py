"""Ep45 LUAR ANGKASA GELAP PADAHAL ADA MATAHARI - adegan mesin v11 (diimpor oleh mesin_v11).

Pola sama dengan mesin_v11_ep43/44: `B45[visual] = {nama: (fraksi, suara)}`; `_t(N, nama, dur)`.
Fraksi disetel dari posisi kata kunci VO (timeline captions, 23 Sep 2026).
Objek: panel angkasa berbintang, matahari berpendar, senter + berkas, molekul penyebar,
pita spektrum, pengukur ketinggian (biru -> hitam), bulan, garis pandang Olbers,
cakrawala cahaya 13,8 miliar tahun, gelombang teregang (redshift), peta sisa cahaya awal.
"""
import math
import random

import diagrams as D
from diagrams import (INK, CREAM, WHITE, MUTED, RED, BLUE, GREEN, AMBER, FB, FS,
                      mix, seg, clamp, esmooth, eob, font, paste_c,
                      rrect_on, line_on, dot_on, ring_on, poly_on, ell)

import mesin_v11 as M
from mesin_v11 import (_stiker11, _label11, _glow11, _panah11, _gelom11, _partikel11, _judul11, _hdr,
                       _orang11, GELAP)

B45 = {
    "intro_langit45": {"matahari": (0.05, "whoosh"), "terang": (0.20, "ding"), "gelap": (0.44, "impact"),
                       "lintas": (0.59, "swish"), "tanya": (0.84, "pop")},
    "senter45": {"mata": (0.04, "pop"), "masuk": (0.12, "zap"), "senter": (0.25, "click"),
                 "samar": (0.40, "swish"), "asap": (0.53, "whoosh"), "jelas": (0.68, "kilau"),
                 "pantul": (0.83, "ding")},
    "biru45": {"sinar": (0.08, "whoosh"), "molekul": (0.12, "pop"), "arah": (0.31, "kilau"),
               "biru": (0.46, "ding"), "orang": (0.70, "pop"), "langit": (0.85, "impact")},
    "tinggi45": {"naik": (0.04, "swish_up"), "tipis": (0.25, "whoosh"), "tua": (0.39, "tick"),
                 "hitam": (0.48, "impact"), "bulan": (0.53, "pop"), "siang": (0.75, "ding")},
    "putih45": {"spektrum": (0.04, "swish"), "sebar": (0.33, "kilau"), "kuning": (0.56, "ding"),
                "astronaut": (0.74, "whoosh"), "putih": (0.89, "impact")},
    "olbers45": {"teka": (0.10, "pop"), "bintang": (0.40, "kilau"), "pandang": (0.50, "swish"),
                 "pasti": (0.65, "tick"), "terang": (0.83, "riser_end")},
    "umur45": {"umur": (0.13, "impact"), "cakrawala": (0.36, "whoosh"), "belum": (0.54, "thud"),
               "regang": (0.69, "swish"), "hilang": (0.90, "glitch")},
    "cmb45": {"tidak": (0.15, "impact"), "sisa": (0.33, "kilau"), "mikro": (0.64, "zap"),
              "mata": (0.74, "pop"), "antena": (0.84, "ding")},
    "rangkuman45": {"s1": (0.06, "pop"), "s2": (0.28, "pop"), "s3": (0.50, "pop"),
                    "kirim": (0.78, "impact")},
}
for _k, _v in B45.items():
    M.BEATS[_k] = sorted(_v.values())

ANGKASA = (12, 16, 34)
KUNING = (255, 200, 70)
SURYA = (255, 226, 150)
LANGIT = (120, 176, 232)
BIRU_T = (40, 70, 150)
MERAH_T = (150, 40, 40)
ABU = (150, 156, 170)


def _t(nama, key, dur):
    return B45[nama][key][0] * dur


def _bintang_acak(seed, n):
    rng = random.Random(seed)
    return [(rng.random(), rng.random(), rng.uniform(0.4, 1.0), rng.uniform(0, 6.28)) for _ in range(n)]


_BINTANG = _bintang_acak(45, 70)
_BINTANG_OLB = _bintang_acak(7, 260)


# ------------------------------------------------------------------ objek Ep45
def _angkasa45(img, x0, y0, x1, y1, alpha, tg, n=40, r=30, col=ANGKASA, terang=1.0):
    """Panel luar angkasa: latar gelap + bintang berkelip."""
    if alpha <= 0.01:
        return
    rrect_on(img, x0, y0, x1, y1, r, col, alpha)
    for (u, v, s, ph) in _BINTANG[:n]:
        x = x0 + 24 + (x1 - x0 - 48) * u
        y = y0 + 24 + (y1 - y0 - 48) * v
        k = 0.55 + 0.45 * math.sin(tg * 2.3 + ph)
        dot_on(img, x, y, 1.6 + 2.2 * s, WHITE, alpha * terang * (0.35 + 0.55 * k * s))


def _matahari45(img, cx, cy, r, alpha, tg, col=None, sinar=True):
    """Matahari: pendar + cakram + sinar berputar pelan."""
    if alpha <= 0.01:
        return
    col = col or SURYA
    _glow11(img, cx, cy, r * 2.6, mix(col, WHITE, 0.2), alpha * 0.75)
    if sinar:
        for k in range(12):
            a = tg * 0.4 + k * math.pi / 6
            r1, r2 = r * 1.18, r * (1.45 + 0.08 * math.sin(tg * 3 + k))
            line_on(img, (cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
                    (cx + r2 * math.cos(a), cy + r2 * math.sin(a)), col, max(3, int(r * 0.12)), alpha * 0.8)
    dot_on(img, cx, cy, r, col, alpha)
    dot_on(img, cx - r * 0.28, cy - r * 0.3, r * 0.34, mix(col, WHITE, 0.55), alpha * 0.7)


def _mata45(img, cx, cy, s, alpha, col=INK, buka=1.0):
    """Mata besar: kelopak almond + iris + kilau."""
    if alpha <= 0.01:
        return
    w, h = 90 * s, 52 * s * buka
    ell(img, cx - w, cy - h, cx + w, cy + h, fill=WHITE, outline=col, width=max(3, int(6 * s)), alpha=alpha)
    if buka > 0.3:
        dot_on(img, cx, cy, 34 * s * min(1.0, buka), (84, 120, 170), alpha)
        dot_on(img, cx, cy, 16 * s * min(1.0, buka), INK, alpha)
        dot_on(img, cx - 10 * s, cy - 10 * s, 7 * s, WHITE, alpha)


def _senter45(img, x, y, s, alpha, col=(70, 76, 92)):
    """Senter menghadap kanan; ujung kepala di (x + 90s, y)."""
    rrect_on(img, x - 70 * s, y - 16 * s, x + 30 * s, y + 16 * s, 8 * s, col, alpha)
    poly_on(img, [(x + 30 * s, y - 16 * s), (x + 90 * s, y - 30 * s), (x + 90 * s, y + 30 * s), (x + 30 * s, y + 16 * s)],
            mix(col, WHITE, 0.2), alpha)
    rrect_on(img, x + 84 * s, y - 30 * s, x + 94 * s, y + 30 * s, 3, (255, 236, 170), alpha)
    rrect_on(img, x - 30 * s, y - 20 * s, x - 10 * s, y - 14 * s, 2, RED, alpha)


def _berkas45(img, x0, y, x1, lebar, alpha, col=(255, 236, 170)):
    """Berkas cahaya kerucut dari (x0, y) melebar ke x1."""
    if alpha <= 0.01:
        return
    poly_on(img, [(x0, y - 26), (x1, y - lebar), (x1, y + lebar), (x0, y + 26)], col, alpha)


def _spektrum45(img, x0, y, w, h, alpha, lepas_biru=0.0, tg=0.0):
    """Pita spektrum pelangi; lepas_biru 0..1 -> bagian biru/ungu terangkat & memudar."""
    cols = [(150, 80, 200), (70, 90, 220), (60, 160, 230), (70, 190, 90), (250, 220, 60), (250, 150, 50), (230, 60, 50)]
    sw = w / len(cols)
    for i, c in enumerate(cols):
        biru = i <= 2
        off = -34 * eob(lepas_biru, 1.2) * (1 + i * 0.15) if biru else 0
        a = alpha * (1 - 0.85 * lepas_biru if biru else 1)
        rrect_on(img, x0 + i * sw, y - h / 2 + off, x0 + (i + 1) * sw + 1, y + h / 2 + off, 6 if i in (0, 6) else 0, c, a)


def _balon45(img, cx, cy, s, alpha, col=RED):
    ell(img, cx - 34 * s, cy - 44 * s, cx + 34 * s, cy + 30 * s, fill=col, alpha=alpha)
    ell(img, cx - 22 * s, cy - 36 * s, cx - 6 * s, cy - 14 * s, fill=mix(col, WHITE, 0.5), alpha=alpha * 0.8)
    line_on(img, (cx, cy + 30 * s), (cx, cy + 62 * s), INK, 2, alpha)
    rrect_on(img, cx - 12 * s, cy + 60 * s, cx + 12 * s, cy + 78 * s, 3, (170, 120, 70), alpha)


def _bulan45(img, cx, cy, r, alpha):
    dot_on(img, cx, cy, r, (196, 196, 200), alpha)
    for (ox, oy, rr) in ((-0.35, -0.2, 0.22), (0.3, 0.25, 0.16), (0.1, -0.45, 0.12), (-0.15, 0.4, 0.1)):
        dot_on(img, cx + ox * r, cy + oy * r, rr * r, (160, 160, 168), alpha)


def _helm45(img, cx, cy, s, alpha):
    """Helm astronaut dengan kaca gelap."""
    dot_on(img, cx, cy, 54 * s, WHITE, alpha, outline=mix(INK, CREAM, 0.5), width=3)
    ell(img, cx - 36 * s, cy - 26 * s, cx + 36 * s, cy + 22 * s, fill=(30, 44, 80), alpha=alpha)
    ell(img, cx - 26 * s, cy - 18 * s, cx - 6 * s, cy - 4 * s, fill=(120, 150, 210), alpha=alpha * 0.8)
    rrect_on(img, cx - 44 * s, cy + 44 * s, cx + 44 * s, cy + 70 * s, 10 * s, WHITE, alpha, outline=mix(INK, CREAM, 0.5), width=3)


def _antena45(img, cx, cy, s, alpha, col=GELAP):
    """Antena parabola (teleskop radio)."""
    poly_on(img, [(cx - 60 * s, cy - 30 * s), (cx + 60 * s, cy - 70 * s), (cx + 30 * s, cy + 10 * s)],
            mix(col, WHITE, 0.75), alpha, outline=col, width=4)
    line_on(img, (cx, cy - 20 * s), (cx + 40 * s, cy - 70 * s), col, 4, alpha)
    line_on(img, (cx, cy - 10 * s), (cx, cy + 50 * s), col, 7, alpha)
    rrect_on(img, cx - 36 * s, cy + 46 * s, cx + 36 * s, cy + 58 * s, 4, col, alpha)


def _foton45(img, x0, y0, x1, y1, tg, alpha, col=KUNING, n=6, kec=0.6, r=6, samar=False):
    """Butir cahaya berjalan di garis; samar=True -> hanya cincin tipis (tak terlihat)."""
    for k in range(n):
        u = (tg * kec + k / n) % 1.0
        x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
        if samar:
            ring_on(img, x, y, r, col, 2, alpha * 0.55)
        else:
            dot_on(img, x, y, r, col, alpha)


# ------------------------------------------------------------------ adegan
def sc_intro_langit45(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "intro_langit45"
    L = sc.get("lines") or ["LUAR ANGKASA GELAP,", "PADAHAL ADA MATAHARI?"]
    _judul11(img, L[0], INK, tl, al, y=455, fsz=62, t0=0.05)
    _judul11(img, L[1], accent, tl, al, y=555, fsz=56, t0=0.30, hl="MATAHARI?")
    q = esmooth(seg(tl, _t(N, "matahari", dur), _t(N, "matahari", dur) + 0.7))
    if q <= 0.01:
        return
    x0, y0, x1, y1 = 90, 690 + dy, 990, 1540 + dy
    k = eob(q, 1.3)
    _angkasa45(img, x0, y0 + (1 - k) * 120, x1, y1, al * q, tg, n=55)
    _bulan45(img, 880, 1440 + dy, 34, al * q * 0.9)
    tr = esmooth(seg(tl, _t(N, "terang", dur), _t(N, "terang", dur) + 0.6))
    _matahari45(img, 280, 1060 + dy, 90 + 25 * tr, al * q, tg)
    tt = tl - _t(N, "terang", dur)
    if tt > 0:
        _label11(img, 280, 1250 + dy, "sangat terang", KUNING, al * clamp(tt / 0.4), fsz=28, name=FB)
    tt = tl - _t(N, "gelap", dur)
    if tt > 0:
        _stiker11(img, 740, 820 + dy, "TAPI GELAP GULITA", al, tt, bg=GELAP, fsz=32, rot=5, tg=tg)
    tt = tl - _t(N, "lintas", dur)
    if tt > 0:
        a = al * clamp(tt / 0.5)
        for j, yy in enumerate((980, 1060, 1140)):
            _foton45(img, 420, yy + dy, 960, yy + dy, tg + j * 0.2, a, col=KUNING, n=5, kec=0.5, r=7, samar=True)
        _label11(img, 700, 1210 + dy, "cahaya lewat di sini... tak terlihat", (200, 206, 224), a, fsz=24)
    tt = tl - _t(N, "tanya", dur)
    if tt > 0:
        _stiker11(img, 540, 1440 + dy, "KENAPA?", al, tt, bg=accent, fsz=48, rot=-4, tg=tg)


def sc_senter45(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "senter45"
    _hdr(img, sc, accent, tl, al)
    t_se = _t(N, "senter", dur)
    # fase A: cahaya masuk mata = terlihat
    qa = esmooth(seg(tl, _t(N, "mata", dur), _t(N, "mata", dur) + 0.5)) * (1 - esmooth(seg(tl, t_se - 0.2, t_se + 0.3)))
    if qa > 0.01:
        _mata45(img, 700, 1030 + dy, 1.5, al * qa)
        tm = tl - _t(N, "masuk", dur)
        _matahari45(img, 200, 1030 + dy, 50, al * qa, tg, sinar=False)
        if tm > 0:
            _panah11(img, (270, 1030 + dy), (560, 1030 + dy), al * qa, clamp(tm / 0.5), AMBER, width=10, lengkung=0.0)
            _stiker11(img, 540, 1260 + dy, "MASUK KE MATA = TERLIHAT", al * qa, tm, bg=accent, fsz=30, rot=-3, tg=tg)
    # fase B: dua kamar
    qb = esmooth(seg(tl, t_se, t_se + 0.5))
    if qb <= 0.01:
        return
    kamar = [(720, "kamar bersih", "samar", False), (1130, "ada asap / debu", "asap", True)]
    for i, (y0, lbl, kk, debu) in enumerate(kamar):
        tk = _t(N, kk, dur) if i else t_se
        qk = esmooth(seg(tl, tk, tk + 0.5))
        if qk <= 0.01:
            continue
        y0 += dy
        a = al * qk
        rrect_on(img, 110, y0, 970, y0 + 350, 30, (30, 34, 50), a)
        paste_c(img, 250, y0 + 38, lbl, font(FB, 26), (210, 214, 230), a)
        cy = y0 + 190
        _senter45(img, 210, cy, 1.0, a)
        # dinding kanan + titik terang
        rrect_on(img, 900, y0 + 70, 930, y0 + 320, 8, (70, 76, 96), a)
        _glow11(img, 900, cy, 70, (255, 236, 170), a * 0.9)
        if debu:
            je = esmooth(seg(tl, _t(N, "jelas", dur) - 0.6, _t(N, "jelas", dur)))
            _berkas45(img, 300, cy, 900, 95, a * (0.10 + 0.32 * je))
            for j in range(26):
                u = (j * 0.137 + tg * 0.03 * (1 + j % 3)) % 1.0
                v = ((j * 0.311) % 1.0) - 0.5
                x = 320 + 570 * u
                yy = cy + v * 2 * (26 + 69 * u) + 6 * math.sin(tg * 1.3 + j)
                terkena = abs(v) < 0.5
                dot_on(img, x, yy, 4.5, (255, 240, 190) if terkena else (120, 124, 140), a * (0.4 + 0.6 * je))
            tp = tl - _t(N, "pantul", dur)
            if tp > 0:
                _mata45(img, 620, y0 + 420, 0.55, al)
                for j, (px, py) in enumerate(((520, cy + 20), (640, cy - 30), (760, cy + 40))):
                    _panah11(img, (px, py), (600 + j * 20, y0 + 385), al, clamp((tp - j * 0.1) / 0.4), AMBER,
                             width=5, lengkung=0.1, head=14)
                _stiker11(img, 830, y0 + 430, "DIPANTULKAN", al, tp, bg=accent, fsz=26, rot=4, tg=tg)
        else:
            _berkas45(img, 300, cy, 900, 95, a * 0.05)
            ts = tl - _t(N, "samar", dur)
            if ts > 0:
                _label11(img, 600, cy + 120, "berkas hampir tak terlihat", (200, 204, 220), a * clamp(ts / 0.4), fsz=24)
        if debu and tl > _t(N, "jelas", dur):
            _label11(img, 760, y0 + 38, "berkas tampak jelas", KUNING, a * clamp((tl - _t(N, "jelas", dur)) / 0.4),
                     fsz=24, name=FB)


def sc_biru45(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "biru45"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "sinar", dur), _t(N, "sinar", dur) + 0.5))
    if q <= 0.01:
        return
    cx, cy = 560, 1010 + dy
    _matahari45(img, 170, 760 + dy, 55, al * q, tg, sinar=False)
    # sinar putih masuk ke gugus molekul
    ts = clamp((tl - _t(N, "sinar", dur)) / 0.6)
    line_on(img, (220, 790 + dy), (220 + (cx - 60 - 220) * ts, 790 + dy + (cy - 790 - dy) * ts), WHITE, 16, al * q)
    line_on(img, (220, 790 + dy), (220 + (cx - 60 - 220) * ts, 790 + dy + (cy - 790 - dy) * ts), mix(AMBER, WHITE, 0.6), 6, al * q)
    qm = esmooth(seg(tl, _t(N, "molekul", dur), _t(N, "molekul", dur) + 0.5))
    if qm > 0:
        for j, (ox, oy) in enumerate(((-30, -10), (20, -34), (34, 18), (-10, 30), (0, 0))):
            wob = 3 * math.sin(tg * 6 + j)
            dot_on(img, cx + ox + wob, cy + oy, 15 * qm, (90, 110, 150), al)
            dot_on(img, cx + ox + wob + 16, cy + oy + 6, 13 * qm, (110, 130, 170), al)
        _label11(img, cx + 175, cy + 30, "molekul udara", MUTED, al * qm, fsz=24, name=FB)
    # sebaran ke segala arah
    tt = tl - _t(N, "arah", dur)
    if tt > 0:
        biru = esmooth(seg(tl, _t(N, "biru", dur), _t(N, "biru", dur) + 0.6))
        for k in range(12):
            ang = k * math.pi / 6 + 0.26
            L = (120 + 140 * clamp(tt / 0.8)) * (1.0 if k % 3 else 0.55 + 0.45 * (1 - biru))
            col = mix(mix(AMBER, WHITE, 0.3), BLUE, biru if k % 3 else 0.0)
            if k % 3 == 0 and biru > 0:
                col = mix(mix(AMBER, WHITE, 0.3), (240, 150, 60), biru)
            x2, y2 = cx + L * math.cos(ang), cy + L * 0.82 * math.sin(ang)
            _panah11(img, (cx + 40 * math.cos(ang), cy + 40 * math.sin(ang) * 0.82), (x2, y2), al, clamp(tt / 0.5),
                     col, width=7 if k % 3 else 5, lengkung=0.0, head=16)
        if biru > 0:
            _stiker11(img, 640, 770 + dy, "BIRU PALING MUDAH TERPANTUL", al, tl - _t(N, "biru", dur),
                      bg=BLUE, fsz=22, rot=5, tg=tg)
    # orang di bawah kubah langit biru
    to = tl - _t(N, "orang", dur)
    if to > 0:
        k = esmooth(clamp(to / 0.8))
        bx0, by0, bx1, by1 = 150, 1330 + dy, 930, 1560 + dy
        ell(img, bx0, by0, bx1, by1 + 230, fill=mix(LANGIT, WHITE, 0.25 * (1 - k)), alpha=al * k)
        rrect_on(img, bx0 - 10, by1 - 10, bx1 + 10, by1 + 30, 10, (120, 160, 90), al * k)
        _orang11(img, 540, by1 - 40, 2.0, GELAP, al * k)
        for j in range(5):
            ang = math.radians(-160 + j * 35)
            _panah11(img, (540, by1 - 90), (540 + 180 * math.cos(ang), by1 - 90 + 150 * math.sin(ang)), al * 0.8,
                     clamp((to - j * 0.08) / 0.5), mix(BLUE, WHITE, 0.3), width=4, lengkung=0.0, head=12)
    tt = tl - _t(N, "langit", dur)
    if tt > 0:
        _stiker11(img, 540, 1620 + dy, "LANGIT TAMPAK BIRU", al, tt, bg=accent, fsz=32, rot=-3, tg=tg)


def sc_tinggi45(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "tinggi45"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "naik", dur), _t(N, "naik", dur) + 0.5))
    if q <= 0.01:
        return
    x0, x1 = 130, 560
    yb, yt = 1600 + dy, 700 + dy
    H = yb - yt
    naik = esmooth(seg(tl, _t(N, "naik", dur), _t(N, "hitam", dur) + 0.4))
    nb = 28
    for i in range(nb):
        u = i / nb
        if u > naik + 0.04:
            break
        if u < 0.45:
            col = mix(mix(LANGIT, WHITE, 0.25), LANGIT, u / 0.45)
        elif u < 0.72:
            col = mix(LANGIT, BIRU_T, (u - 0.45) / 0.27)
        else:
            col = mix(BIRU_T, ANGKASA, min(1.0, (u - 0.72) / 0.22))
        y2 = yb - H * u
        y1 = yb - H * (u + 1.0 / nb) - 1
        rrect_on(img, x0, y1, x1, y2, 0, col, al * q)
    # bintang muncul di bagian atas yang hitam
    if naik > 0.8:
        for (u, v, s, ph) in _BINTANG[:22]:
            yy = yt + 20 + (H * 0.22) * v
            dot_on(img, x0 + 20 + (x1 - x0 - 40) * u, yy, 1.5 + 2 * s, WHITE, al * clamp((naik - 0.8) * 5) * 0.8)
    # skala km
    for km, u in ((0, 0.0), (10, 0.25), (30, 0.55), (50, 0.78), (100, 0.98)):
        y = yb - H * u
        if u <= naik + 0.02:
            line_on(img, (x1, y), (x1 + 24, y), INK, 3, al * q)
            paste_c(img, x1 + 66, y, f"{km} km", font(FB, 24), INK, al * q)
    # balon naik
    by = yb - 90 - (H - 200) * naik
    _balon45(img, 345, by, 1.1, al * q)
    tt = tl - _t(N, "tipis", dur)
    if tt > 0:
        _label11(img, 345, yb - H * 0.25, "udara makin tipis", INK, al * clamp(tt / 0.4), fsz=26, name=FB)
    tt = tl - _t(N, "tua", dur)
    if tt > 0:
        _label11(img, 345, yb - H * 0.58, "biru tua", WHITE, al * clamp(tt / 0.4), fsz=28, name=FB)
    tt = tl - _t(N, "hitam", dur)
    if tt > 0:
        _stiker11(img, 345, yt + 270, "HITAM", al, tt, bg=GELAP, fsz=40, rot=-4, tg=tg)
    # kartu bulan
    tt = tl - _t(N, "bulan", dur)
    if tt > 0:
        k = eob(clamp(tt / 0.5), 1.6)
        cx0, cy0 = 830, 1150 + dy
        _angkasa45(img, cx0 - 130, cy0 - 200 + (1 - k) * 200, cx0 + 130, cy0 + 200, al * clamp(tt / 0.3), tg, n=12, r=24)
        rrect_on(img, cx0 - 130, cy0 + 110, cx0 + 130, cy0 + 200, 0, (170, 170, 176), al * clamp(tt / 0.3))
        for j in range(4):
            dot_on(img, cx0 - 90 + j * 60, cy0 + 140 + (j % 2) * 20, 12, (140, 140, 148), al * clamp(tt / 0.3))
        _matahari45(img, cx0 + 40, cy0 - 90, 34, al * clamp(tt / 0.3), tg, col=WHITE)
        _label11(img, cx0, cy0 - 245, "di BULAN", INK, al * clamp(tt / 0.3), fsz=28, name=FB)
    tt = tl - _t(N, "siang", dur)
    if tt > 0:
        _stiker11(img, 830, 1420 + dy, "SIANG, LANGIT HITAM", al, tt, bg=accent, fsz=22, rot=4, tg=tg)


def sc_putih45(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "putih45"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "spektrum", dur), _t(N, "spektrum", dur) + 0.5))
    if q <= 0.01:
        return
    sebar = esmooth(seg(tl, _t(N, "sebar", dur), _t(N, "sebar", dur) + 1.2))
    kuning = esmooth(seg(tl, _t(N, "kuning", dur), _t(N, "kuning", dur) + 0.8))
    # panel kiri: dari Bumi (langit biru)
    lx0, ly0, lx1, ly1 = 110, 700 + dy, 520, 1180 + dy
    rrect_on(img, lx0, ly0, lx1, ly1, 30, mix(LANGIT, WHITE, 0.2 + 0.3 * (1 - sebar)), al * q)
    rrect_on(img, lx0, ly1 - 70, lx1, ly1, 0, (120, 160, 90), al * q)
    rrect_on(img, lx0, ly1 - 30, lx1, ly1, 30, (120, 160, 90), al * q)
    scol = mix(WHITE, KUNING, kuning)
    _matahari45(img, 315, 880 + dy, 70, al * q, tg, col=scol)
    for j in range(14):
        u = (j * 0.173 + tg * 0.25) % 1.0
        ang = j * 0.9
        rr = 90 + 140 * u
        dot_on(img, 315 + rr * math.cos(ang), 880 + dy + rr * 0.8 * math.sin(ang), 6, BLUE, al * sebar * (1 - u))
    paste_c(img, 315, ly1 - 36, "dari BUMI", font(FB, 28), WHITE, al * q)
    if kuning > 0:
        _label11(img, 315, 1000 + dy, "tampak kekuningan", mix(AMBER, INK, 0.3), al * kuning, fsz=24, name=FB)
    # panel kanan: dari luar angkasa
    ta = tl - _t(N, "astronaut", dur)
    if ta > 0:
        k = eob(clamp(ta / 0.5), 1.5)
        rx0, rx1 = 560, 970
        _angkasa45(img, rx0 + (1 - k) * 300, ly0, rx1 + (1 - k) * 300, ly1, al * clamp(ta / 0.3), tg, n=18)
        _matahari45(img, 765 + (1 - k) * 300, 880 + dy, 70, al * clamp(ta / 0.3), tg, col=WHITE)
        _helm45(img, 850 + (1 - k) * 300, 1070 + dy, 0.8, al * clamp(ta / 0.3))
        paste_c(img, 690 + (1 - k) * 300, ly1 - 36, "dari ANGKASA", font(FB, 26), WHITE, al * clamp(ta / 0.3))
    # pita spektrum: biru terangkat
    y = 1330 + dy
    _label11(img, 540, y - 105, "cahaya matahari = semua warna", INK, al * q, fsz=26, name=FB)
    _spektrum45(img, 170, y, 740, 70, al * q, lepas_biru=sebar)
    if sebar > 0.1:
        _label11(img, 340, y + 70, "biru tersebar ke langit", BLUE, al * sebar, fsz=24, name=FB)
        _label11(img, 740, y + 70, "sisanya: kuning", mix(AMBER, INK, 0.3), al * sebar, fsz=24, name=FB)
    tt = tl - _t(N, "putih", dur)
    if tt > 0:
        _stiker11(img, 765, 1560 + dy, "ASLINYA PUTIH!", al, tt, bg=accent, fsz=36, rot=-4, tg=tg)


def sc_olbers45(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "olbers45"
    _hdr(img, sc, accent, tl, al)
    tt = tl - _t(N, "teka", dur)
    if tt <= 0:
        return
    x0, y0, x1, y1 = 90, 690 + dy, 990, 1520 + dy
    terang = esmooth(seg(tl, _t(N, "terang", dur), _t(N, "terang", dur) + 1.2))
    _angkasa45(img, x0, y0, x1, y1, al * clamp(tt / 0.4), tg, n=0, col=mix(ANGKASA, (255, 236, 180), terang))
    ox, oy = 540, 1480 + dy
    qb = esmooth(seg(tl, _t(N, "bintang", dur) - 0.8, _t(N, "bintang", dur) + 1.4))
    nb = int(len(_BINTANG_OLB) * qb)
    for (u, v, s, ph) in _BINTANG_OLB[:nb]:
        x = x0 + 20 + (x1 - x0 - 40) * u
        y = y0 + 20 + (y1 - y0 - 110) * v
        jauh = 1 - v
        r = (1.2 + 3.4 * s) * (1.0 - 0.5 * jauh)
        dot_on(img, x, y, r, mix(WHITE, KUNING, 0.3 * s), al * (0.5 + 0.5 * s))
    tp = tl - _t(N, "pandang", dur)
    if tp > 0:
        for k in range(9):
            ang = math.radians(-160 + k * 17.5)
            L = 780 * clamp((tp - k * 0.04) / 0.8)
            x2, y2 = ox + L * math.cos(ang), oy + L * math.sin(ang)
            x2 = max(x0 + 20, min(x1 - 20, x2))
            y2 = max(y0 + 20, y2)
            line_on(img, (ox, oy), (x2, y2), mix(KUNING, WHITE, 0.4), 3, al * 0.6)
            if tl > _t(N, "pasti", dur):
                ph = clamp((tl - _t(N, "pasti", dur) - k * 0.06) / 0.3)
                D.star4(img, x2, y2, 16 * ph, KUNING, al * ph)
    _orang11(img, ox, oy - 10, 1.6, WHITE, al * clamp(tt / 0.4))
    if terang > 0:
        _glow11(img, 540, 1100 + dy, 520, (255, 246, 210), al * terang * 0.8)
        _stiker11(img, 540, 1000 + dy, "SEHARUSNYA SETERANG MATAHARI", al, tl - _t(N, "terang", dur),
                  bg=accent, fsz=26, rot=-3, tg=tg)
    _stiker11(img, 860, 760 + dy, "?", al * (1 - terang), tt, bg=AMBER, fsz=56, rot=8, tg=tg)


def sc_umur45(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "umur45"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, 0.1, 0.6))
    if q <= 0.01:
        return
    x0, y0, x1, y1 = 90, 690 + dy, 990, 1250 + dy
    _angkasa45(img, x0, y0, x1, y1, al * q, tg, n=0)
    cx, cy = 540, 970 + dy
    tu = tl - _t(N, "umur", dur)
    if tu > 0:
        D._hitung_on(img, 540, 1385 + dy, 13.8, "miliar tahun", al, tl, t0=_t(N, "umur", dur), dur=1.0,
                     col=mix(accent, INK, 0.1), fsz=72)
        _label11(img, 540, 1300 + dy, "umur alam semesta", MUTED, al * clamp(tu / 0.4), fsz=24, name=FB)
    # cakrawala: lingkaran jangkauan cahaya
    tc = _t(N, "cakrawala", dur)
    R = 225 * esmooth(seg(tl, tc - 0.6, tc + 0.8))
    if R > 2:
        dot_on(img, cx, cy, R, (40, 50, 90), al * 0.55)
        ring_on(img, cx, cy, R, mix(KUNING, WHITE, 0.3), 4, al)
    rng = random.Random(3)
    tb = _t(N, "belum", dur)
    for j in range(34):
        a = rng.uniform(0, 6.28)
        rr = rng.uniform(40, 420)
        x, y = cx + rr * math.cos(a), cy + rr * 0.68 * math.sin(a)
        if not (x0 + 20 < x < x1 - 20 and y0 + 20 < y < y1 - 20):
            continue
        dalam = rr * math.hypot(math.cos(a), 0.68 * math.sin(a)) < 225
        a_ = al * q * (1.0 if dalam or R < 2 else 0.35)
        dot_on(img, x, y, 3.5 if dalam else 3, WHITE if dalam or R < 2 else ABU, a_)
        if not dalam and tl > tb and j % 3 == 0:
            u = ((tl - tb) * 0.35 + j * 0.13) % 1.0
            px, py = x + (cx - x) * u * 0.35, y + (cy - y) * u * 0.35
            dot_on(img, px, py, 4, KUNING, al * (1 - u))
    dot_on(img, cx, cy, 16, (70, 140, 220), al * q)
    dot_on(img, cx - 5, cy - 4, 6, (120, 200, 120), al * q)
    if tl > tc:
        _label11(img, cx, cy - R - 26 if R > 60 else cy - 60, "cahaya sempat sampai", KUNING, al * clamp((tl - tc) / 0.4), fsz=22, name=FB)
    if tl > tb:
        _stiker11(img, 830, 1215 + dy, "BELUM SAMPAI", al, tl - tb, bg=GELAP, fsz=24, rot=4, tg=tg)
    # gelombang teregang
    tr = _t(N, "regang", dur)
    qr = esmooth(seg(tl, tr, tr + 0.5))
    if qr > 0:
        y = 1590 + dy
        g = esmooth(seg(tl, tr, _t(N, "hilang", dur)))
        lam = 30 + 110 * g
        col = mix(mix(BLUE, RED, min(1.0, g * 1.6)), ABU, max(0.0, g - 0.7) / 0.3)
        rrect_on(img, 110, y - 70, 970, y + 70, 30, WHITE, al * qr, outline=mix(INK, CREAM, 0.7), width=2)
        _gelom11(img, 150, 930, y, 34, lam, tg * 6, col, 6, al * qr)
        lbl = "biru" if g < 0.25 else ("merah" if g < 0.7 else "tak terlihat mata")
        _label11(img, 830, y - 48, lbl, col, al * qr, fsz=22, name=FB)
        _label11(img, 260, y - 48, "cahaya teregang", INK, al * qr, fsz=22, name=FB)


def sc_cmb45(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "cmb45"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, 0.1, 0.6))
    if q <= 0.01:
        return
    x0, y0, x1, y1 = 90, 690 + dy, 990, 1260 + dy
    _angkasa45(img, x0, y0, x1, y1, al * q, tg, n=30)
    cx, cy, rx, ry = 540, 975 + dy, 400, 230
    ts = _t(N, "sisa", dur)
    sw = esmooth(seg(tl, _t(N, "tidak", dur), ts + 1.0))
    if sw > 0:
        xs = cx - rx + 2 * rx * sw
        rng = random.Random(21)
        for j in range(240):
            u, v = rng.uniform(-1, 1), rng.uniform(-1, 1)
            if u * u + v * v > 1:
                continue
            x, y = cx + u * rx, cy + v * ry
            if x > xs:
                continue
            h = rng.random()
            col = mix((60, 110, 220), (240, 120, 50), h)
            col = mix(col, (250, 210, 90), 0.5 * max(0.0, 1 - abs(h - 0.5) * 3))
            dot_on(img, x, y, rng.uniform(16, 30), col, al * 0.55)
        ring_on(img, cx, cy, rx, WHITE, 3, al * sw, squash=ry / rx)
        if sw < 1:
            line_on(img, (xs, cy - ry - 10), (xs, cy + ry + 10), (120, 255, 180), 5, al)
    tt = tl - ts
    if tt > 0:
        _label11(img, 540, y1 - 36, "sisa cahaya awal alam semesta", WHITE, al * clamp(tt / 0.4), fsz=26, name=FB)
    tt = tl - _t(N, "tidak", dur)
    if tt > 0:
        _stiker11(img, 800, 760 + dy, "TIDAK GELAP!", al, tt, bg=accent, fsz=30, rot=5, tg=tg)
    tt = tl - _t(N, "mikro", dur)
    if tt > 0:
        y = 1360 + dy
        _gelom11(img, 170, 910, y, 22, 150, tg * 3, mix(accent, WHITE, 0.1), 6, al * clamp(tt / 0.4))
        _stiker11(img, 540, y + 5, "GELOMBANG MIKRO", al, tt, bg=GELAP, fsz=28, rot=-3, tg=tg)
    tt = tl - _t(N, "mata", dur)
    if tt > 0:
        k = eob(clamp(tt / 0.4), 1.6)
        rrect_on(img, 110, 1450 + dy, 520, 1640 + dy, 30, WHITE, al * clamp(tt / 0.2), outline=mix(RED, WHITE, 0.6), width=3)
        _mata45(img, 250, 1545 + dy, 0.7 * k, al)
        D._check5_on(img, 250, 1545 + dy, 60, "x", al, clamp((tt - 0.2) / 0.3), col=RED)
        paste_c(img, 420, 1545 + dy, "mata", font(FB, 30), INK, al)
    tt = tl - _t(N, "antena", dur)
    if tt > 0:
        k = eob(clamp(tt / 0.4), 1.6)
        rrect_on(img, 560, 1450 + dy, 970, 1640 + dy, 30, WHITE, al * clamp(tt / 0.2), outline=mix(GREEN, WHITE, 0.5), width=3)
        _antena45(img, 680, 1545 + dy, 0.9 * k, al)
        D._check5_on(img, 900, 1500 + dy, 34, "check", al, clamp((tt - 0.2) / 0.3), col=GREEN)
        paste_c(img, 850, 1580 + dy, "teleskop radio", font(FB, 24), INK, al)


def sc_rangkuman45(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "rangkuman45"
    _hdr(img, sc, accent, tl, al)
    items = [("s1", "TERLIHAT = MEMANTUL KE MATA", "tanpa pantulan, cahaya tak tampak", BLUE),
             ("s2", "TANPA UDARA = LANGIT HITAM", "walau matahari bersinar", GELAP),
             ("s3", "ALAM SEMESTA PUNYA UMUR", "13,8 miliar tahun", accent)]
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
        paste_c(img, 590, y - 20, a_, font(FB, 30), INK, a, scale=0.85 + 0.15 * k)
        paste_c(img, 590, y + 26, b_, font(FS, 24), MUTED, a)
        _partikel11(img, 195, y, tt, col, al, n=8, jarak=70, seed=i)
    tt = tl - _t(N, "kirim", dur)
    if tt > 0:
        _stiker11(img, 400, 1420 + dy, "KIRIM KE TEMAN", al, tt, bg=accent, fsz=38, rot=-4, tg=tg)
        _label11(img, 400, 1505 + dy, "yang suka menatap langit", MUTED, al * clamp(tt / 0.3), fsz=26)
        _matahari45(img, 830, 1450 + dy, 46, al * clamp(tt / 0.3), tg)


VISUALS45 = {
    "intro_langit45": sc_intro_langit45, "senter45": sc_senter45, "biru45": sc_biru45,
    "tinggi45": sc_tinggi45, "putih45": sc_putih45, "olbers45": sc_olbers45, "umur45": sc_umur45,
    "cmb45": sc_cmb45, "rangkuman45": sc_rangkuman45,
}
