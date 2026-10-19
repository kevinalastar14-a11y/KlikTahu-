"""Ep46 MEGALODON MASIH HIDUP? GIGINYA YANG MENJAWAB - adegan mesin v11 (diimpor oleh mesin_v11).

Pola sama dengan mesin_v11_ep43/44/45: `B46[visual] = {nama: (fraksi, suara)}`; `_t(N, nama, dur)`.
Fraksi disetel dari posisi kata kunci VO (timeline captions, 23 Sep 2026).
Objek: gigi megalodon bergerigi (akar V + bourlette), siluet hiu sisi (megalodon / hiu putih),
laut bergradasi, sabuk gigi berganti (conveyor), kolom lapisan batuan 0-23 juta tahun,
termometer, paus, TV dokumenter, diagram lingkaran 73%.
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

B46 = {
    "intro_mega46": {"laut": (0.04, "gelembung"), "mega": (0.13, "whoosh"), "sembunyi": (0.31, "swish"),
                     "benar": (0.49, "impact"), "benda": (0.65, "pop"), "mana": (0.85, "kilau"),
                     "gigi": (0.91, "gigit")},
    "gigi46": {"gigi": (0.14, "gigit"), "tinggi": (0.31, "swish_up"), "cm": (0.45, "tick"),
               "tangan": (0.60, "pop"), "gerigi": (0.81, "zap"), "roti": (0.89, "ding")},
    "ukuran46": {"rawan": (0.12, "thud"), "fosil": (0.26, "glitch"), "ruas": (0.37, "pop"),
                 "belgia": (0.50, "ding"), "enam": (0.65, "impact"), "besar": (0.80, "swish"),
                 "dua4": (0.88, "boom")},
    "ganti46": {"lapis": (0.15, "pop"), "lepas": (0.39, "swish"), "ganti": (0.47, "swish_up"),
                "ribuan": (0.81, "tick"), "dasar": (0.91, "thud")},
    "berhenti46": {"temu": (0.15, "pop"), "batuan": (0.22, "swish"), "dua": (0.28, "tick"),
                   "tiga": (0.44, "impact"), "muda": (0.62, "thud"), "segar": (0.81, "glitch"),
                   "kini": (0.92, "impact")},
    "dalam46": {"sembunyi": (0.07, "swish"), "dalam": (0.21, "gelembung"), "hangat": (0.29, "ding"),
                "suhu": (0.46, "tick"), "makan": (0.60, "pop"), "dingin": (0.78, "thud"),
                "miskin": (0.90, "glitch")},
    "punah46": {"dingin": (0.13, "whoosh"), "turun": (0.28, "swish"), "paus": (0.37, "pop"),
                "pindah": (0.45, "swish"), "hiu": (0.61, "whoosh"), "rebut": (0.82, "impact")},
    "palsu46": {"percaya": (0.12, "pop"), "tahun": (0.19, "tick"), "tv": (0.35, "click"),
                "aktor": (0.45, "glitch"), "fiksi": (0.53, "impact"), "jajak": (0.58, "pop"),
                "persen": (0.70, "riser_end"), "punah": (0.91, "ding")},
    "rangkuman46": {"s1": (0.05, "pop"), "s2": (0.27, "pop"), "s3": (0.59, "pop"),
                    "kirim": (0.70, "impact")},
}
for _k, _v in B46.items():
    M.BEATS[_k] = sorted(_v.values())

LAUT_A = (96, 176, 206)
LAUT_B = (10, 34, 70)
PASIR = (206, 184, 136)
MEGA = (64, 84, 104)
HIU_P = (128, 140, 152)
PAUS = (72, 96, 140)
MAHKOTA = (74, 80, 94)
AKAR = (150, 112, 74)
TULANG = (236, 226, 204)
DINGIN = (120, 190, 240)


def _t(nama, key, dur):
    return B46[nama][key][0] * dur


def _tf(pts, cx, cy, s, rot=0.0, flip=1):
    """Titik satuan -> layar: skala s, cermin flip (x), putar rot derajat."""
    c, n = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for (x, y) in pts:
        x, y = x * s * flip, y * s
        out.append((cx + x * c - y * n, cy + x * n + y * c))
    return out


# ------------------------------------------------------------------ objek Ep46
def _gigi46(img, cx, cy, h, alpha, rot=0.0, col=MAHKOTA, akar=AKAR, gerigi=True):
    """Gigi megalodon (ujung ke bawah saat rot=0), tinggi h px: akar V, bourlette, mahkota bergerigi."""
    if alpha <= 0.01 or h < 4:
        return
    root = [(-0.46, -0.16), (0.46, -0.16), (0.42, -0.36), (0.14, -0.47), (0.0, -0.36), (-0.14, -0.47), (-0.42, -0.36)]
    poly_on(img, _tf(root, cx, cy, h, rot), akar, alpha)
    kiri, kanan = [], []
    n = 14
    for i in range(n + 1):
        u = i / n
        bow = 0.035 * math.sin(math.pi * u)
        z = (0.010 if (i % 2 and gerigi and 0 < i < n) else 0.0)
        kiri.append((-0.40 * (1 - u) - bow - z, -0.20 + 0.70 * u))
        kanan.append((0.40 * (1 - u) + bow + z, -0.20 + 0.70 * u))
    crown = kiri + list(reversed(kanan))
    poly_on(img, _tf(crown, cx, cy, h, rot), col, alpha)
    kilap = [(-0.26, -0.12), (-0.12, -0.12), (-0.03, 0.34), (-0.08, 0.34)]
    poly_on(img, _tf(kilap, cx, cy, h, rot), mix(col, WHITE, 0.35), alpha * 0.8)
    band = [(-0.43, -0.23), (0.43, -0.23), (0.40, -0.15), (0.0, -0.09), (-0.40, -0.15)]
    poly_on(img, _tf(band, cx, cy, h, rot), mix(col, INK, 0.45), alpha)


_HIU = [(0.50, 0.01), (0.44, -0.045), (0.32, -0.075), (0.18, -0.09), (0.12, -0.093), (0.00, -0.215),
        (-0.035, -0.21), (-0.045, -0.088), (-0.18, -0.06), (-0.32, -0.035), (-0.40, -0.02),
        (-0.47, -0.13), (-0.53, -0.175), (-0.50, -0.08), (-0.46, 0.0), (-0.51, 0.12), (-0.475, 0.125),
        (-0.40, 0.022), (-0.32, 0.035), (-0.18, 0.06), (0.06, 0.08), (0.02, 0.195), (0.06, 0.19),
        (0.16, 0.078), (0.30, 0.075), (0.42, 0.05), (0.48, 0.03)]


def _hiu46(img, cx, cy, L, alpha, col=MEGA, arah=1, tg=0.0, mata=True, garis=None, isi=1.0):
    """Siluet hiu dari samping (menghadap kanan bila arah=1), panjang L px; ekor mengibas."""
    if alpha <= 0.01 or L < 8:
        return
    pts = []
    for (x, y) in _HIU:
        if x < -0.25:
            y += 0.03 * ((-0.25 - x) / 0.28) * math.sin(tg * 5.0)
        pts.append((x, y))
    P = _tf(pts, cx, cy, L, 0.0, arah)
    poly_on(img, P, col, alpha * isi, outline=garis, width=4)
    if isi > 0.5:
        perut = [(0.44, 0.035), (0.30, 0.066), (0.00, 0.075), (-0.20, 0.052), (-0.20, 0.035), (0.30, 0.03)]
        poly_on(img, _tf(perut, cx, cy, L, 0.0, arah), mix(col, WHITE, 0.35), alpha * isi * 0.8)
        for k in range(3):
            x = 0.27 - k * 0.028
            (a,), (b,) = _tf([(x, -0.035)], cx, cy, L, 0, arah), _tf([(x - 0.012, 0.03)], cx, cy, L, 0, arah)
            line_on(img, a, b, mix(col, INK, 0.4), max(2, int(L * 0.006)), alpha * isi)
    if mata:
        (e,) = _tf([(0.40, -0.022)], cx, cy, L, 0, arah)
        dot_on(img, e[0], e[1], max(2.5, L * 0.011), INK if isi > 0.5 else col, alpha)


def _paus46(img, cx, cy, L, alpha, col=PAUS, arah=1, tg=0.0):
    """Paus dari samping, panjang L px (kepala ke kanan bila arah=1)."""
    if alpha <= 0.01:
        return
    sw = 0.03 * math.sin(tg * 3.0)
    body = [(0.50, 0.0), (0.46, -0.10), (0.30, -0.14), (0.05, -0.13), (-0.10, -0.12), (-0.08, -0.17),
            (-0.14, -0.11), (-0.30, -0.06), (-0.40, -0.02 + sw), (-0.50, -0.10 + sw), (-0.53, -0.06 + sw),
            (-0.45, 0.01 + sw), (-0.53, 0.07 + sw), (-0.50, 0.10 + sw), (-0.40, 0.03 + sw), (-0.30, 0.06),
            (-0.05, 0.12), (0.10, 0.13), (0.30, 0.12), (0.46, 0.07)]
    poly_on(img, _tf(body, cx, cy, L, 0, arah), col, alpha)
    perut = [(0.46, 0.06), (0.30, 0.11), (0.05, 0.12), (0.05, 0.07), (0.30, 0.05)]
    poly_on(img, _tf(perut, cx, cy, L, 0, arah), mix(col, WHITE, 0.4), alpha * 0.8)
    sirip = [(0.18, 0.08), (0.02, 0.22), (0.10, 0.10)]
    poly_on(img, _tf(sirip, cx, cy, L, 0, arah), mix(col, INK, 0.2), alpha)
    (e,) = _tf([(0.36, -0.02)], cx, cy, L, 0, arah)
    dot_on(img, e[0], e[1], max(2.5, L * 0.014), INK, alpha)


def _laut46(img, x0, y0, x1, y1, alpha, tg, atas=LAUT_A, bawah=LAUT_B, r=30, pasir=0, ombak=True):
    """Panel laut bergradasi (terang atas -> gelap bawah) + ombak + gelembung + dasar pasir (px)."""
    if alpha <= 0.01:
        return
    ym = (y0 + y1) / 2
    rrect_on(img, x0, y0, x1, ym + r, r, atas, alpha)
    rrect_on(img, x0, ym - r, x1, y1, r, bawah, alpha)
    nb = 16
    h = (y1 - y0 - 2 * r) / nb
    for i in range(nb):
        u = (i + 0.5) / nb
        rrect_on(img, x0, y0 + r + i * h, x1, y0 + r + (i + 1) * h + 1, 0, mix(atas, bawah, u ** 0.9), alpha)
    if ombak:
        _gelom11(img, x0 + 30, x1 - 30, y0 + 26, 6, 90, tg * 3, mix(atas, WHITE, 0.55), 4, alpha * 0.8)
    for j in range(10):
        u = (j * 0.173 + tg * 0.06 * (1 + j % 3)) % 1.0
        x = x0 + 40 + (x1 - x0 - 80) * ((j * 0.37) % 1.0) + 8 * math.sin(tg * 2 + j)
        y = y1 - pasir - 30 - (y1 - y0 - pasir - 80) * u
        ring_on(img, x, y, 4 + (j % 3) * 2, mix(atas, WHITE, 0.6), 2, alpha * 0.5 * (1 - u))
    if pasir > 0:
        rrect_on(img, x0, y1 - pasir, x1, y1, r, mix(PASIR, bawah, 0.35), alpha)
        rrect_on(img, x0, y1 - pasir, x1, y1 - pasir + r, 0, mix(PASIR, bawah, 0.35), alpha)


def _tangan46(img, cx, cy, s, alpha, col=(234, 192, 152)):
    """Telapak tangan terbuka (jari ke atas); pusat telapak (cx, cy)."""
    if alpha <= 0.01:
        return
    gar = mix(col, INK, 0.35)
    for i, (dx, hh) in enumerate(((-39, 92), (-13, 108), (13, 104), (39, 84))):
        rrect_on(img, cx + (dx - 12) * s, cy - (50 + hh) * s, cx + (dx + 12) * s, cy - 30 * s, 12 * s, col, alpha,
                 outline=gar, width=3)
    poly_on(img, [(cx - 50 * s, cy - 10 * s), (cx - 96 * s, cy - 70 * s), (cx - 110 * s, cy - 58 * s),
                  (cx - 72 * s, cy + 30 * s)], col, alpha, outline=gar, width=3)
    rrect_on(img, cx - 54 * s, cy - 56 * s, cx + 54 * s, cy + 70 * s, 34 * s, col, alpha, outline=gar, width=3)
    rrect_on(img, cx - 40 * s, cy + 60 * s, cx + 40 * s, cy + 120 * s, 10 * s, col, alpha)


def _pisau46(img, x0, cy, L, alpha):
    """Pisau roti horizontal: gagang kiri, bilah bergerigi bawah."""
    rrect_on(img, x0, cy - 16, x0 + L * 0.3, cy + 16, 12, (120, 76, 46), alpha)
    xb0, xb1 = x0 + L * 0.3, x0 + L
    pts = [(xb0, cy - 22), (xb1 - 20, cy - 22), (xb1, cy - 10)]
    n = 16
    for i in range(n + 1):
        x = xb1 - (xb1 - xb0) * i / n
        pts.append((x, cy + 22 + (7 if i % 2 else 0)))
    poly_on(img, pts, (200, 206, 214), alpha, outline=(120, 126, 136), width=2)


def _ruas46(img, cx, cy, r, alpha):
    """Ruas tulang punggung hiu (tampak depan): cakram berlapis cincin."""
    dot_on(img, cx, cy, r, TULANG, alpha, outline=mix(TULANG, INK, 0.45), width=3)
    ring_on(img, cx, cy, r * 0.62, mix(TULANG, INK, 0.3), 2, alpha)
    ring_on(img, cx, cy, r * 0.30, mix(TULANG, INK, 0.3), 2, alpha)


def _termo46(img, cx, y0, y1, frac, alpha, col=RED):
    """Termometer tegak: tabung y0..y1, bola di bawah; frac 0..1 tinggi cairan."""
    rrect_on(img, cx - 24, y0, cx + 24, y1, 24, WHITE, alpha, outline=mix(INK, CREAM, 0.45), width=4)
    dot_on(img, cx, y1 + 22, 40, WHITE, alpha, outline=mix(INK, CREAM, 0.45), width=4)
    dot_on(img, cx, y1 + 22, 30, col, alpha)
    top = y1 - (y1 - y0 - 30) * clamp(frac)
    rrect_on(img, cx - 12, top, cx + 12, y1 + 10, 12, col, alpha)
    for k in range(6):
        y = y0 + 30 + (y1 - y0 - 50) * k / 5
        line_on(img, (cx + 26, y), (cx + 44, y), mix(INK, CREAM, 0.45), 3, alpha)


def _ikan46(img, cx, cy, s, alpha, col=(250, 170, 80), arah=1):
    ell(img, cx - 22 * s, cy - 11 * s, cx + 22 * s, cy + 11 * s, fill=col, alpha=alpha)
    poly_on(img, _tf([(-0.9, 0), (-1.5, -0.6), (-1.5, 0.6)], cx, cy, 22 * s, 0, arah), col, alpha)
    (e,) = _tf([(0.5, -0.12)], cx, cy, 22 * s, 0, arah)
    dot_on(img, e[0], e[1], 2.5 * s, INK, alpha)


def _tv46(img, cx, cy, w, h, alpha, tg, isi=1.0):
    """TV layar datar: bingkai gelap, layar laut + hiu berenang, lampu LIVE."""
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    line_on(img, (cx - 90, y1), (cx - 130, y1 + 50), GELAP, 10, alpha)
    line_on(img, (cx + 90, y1), (cx + 130, y1 + 50), GELAP, 10, alpha)
    rrect_on(img, x0, y0, x1, y1, 34, GELAP, alpha)
    _laut46(img, x0 + 24, y0 + 24, x1 - 24, y1 - 24, alpha * isi, tg, r=18, ombak=False)
    hx = cx - 60 + 120 * math.sin(tg * 0.5)
    _hiu46(img, hx, cy + 20, w * 0.52, alpha * isi, col=mix(MEGA, LAUT_B, 0.2),
           arah=1 if math.cos(tg * 0.5) > 0 else -1, tg=tg)
    dot_on(img, x1 - 70, y0 + 56, 11, RED, alpha * isi * (0.5 + 0.5 * (math.sin(tg * 5) > 0)))
    paste_c(img, x1 - 110, y0 + 56, "LIVE", font(FB, 22), WHITE, alpha * isi)


def _pie46(img, cx, cy, r, frac, col, alpha, sisa=None):
    """Diagram lingkaran: irisan frac (mulai jam 12, searah jarum jam)."""
    dot_on(img, cx, cy, r, sisa or mix(CREAM, INK, 0.12), alpha)
    if frac > 0.005:
        n = max(3, int(64 * frac))
        pts = [(cx, cy)] + [(cx + r * math.sin(2 * math.pi * frac * i / n), cy - r * math.cos(2 * math.pi * frac * i / n))
                            for i in range(n + 1)]
        poly_on(img, pts, col, alpha)
    dot_on(img, cx, cy, r * 0.42, WHITE, alpha)


def _angka46(img, cx, cy, nilai, unit, al, tl, t0, dur=0.8, col=None, fsz=64):
    """Angka count-up + satuan dengan jarak lega (unit bawaan _hitung_on terlalu rapat)."""
    D._hitung_on(img, cx, cy, nilai, "", al, tl, t0=t0, dur=dur, col=col, fsz=fsz)
    if unit and tl > t0:
        _label11(img, cx, cy + fsz * 0.95, unit, MUTED, al * clamp((tl - t0) / 0.3), fsz=max(20, fsz // 3), name=FB)


# ------------------------------------------------------------------ adegan
def sc_intro_mega46(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "intro_mega46"
    L = sc.get("lines") or ["MEGALODON", "MASIH HIDUP?"]
    _judul11(img, L[0], INK, tl, al, y=455, fsz=74, t0=0.05)
    _judul11(img, L[1], accent, tl, al, y=560, fsz=70, t0=0.30, hl="HIDUP?")
    q = esmooth(seg(tl, _t(N, "laut", dur), _t(N, "laut", dur) + 0.7))
    if q <= 0.01:
        return
    x0, y0, x1, y1 = 90, 690 + dy, 990, 1560 + dy
    k = eob(q, 1.3)
    _laut46(img, x0, y0 + (1 - k) * 120, x1, y1, al * q, tg, pasir=90)
    tm = _t(N, "mega", dur)
    qm = esmooth(seg(tl, tm - 0.3, tm + 0.5))
    if qm > 0:
        sb = esmooth(seg(tl, _t(N, "sembunyi", dur), _t(N, "sembunyi", dur) + 1.4))
        pud = esmooth(seg(tl, _t(N, "benda", dur) - 0.3, _t(N, "benda", dur) + 0.4))
        hx = 560 - 260 * (1 - eob(qm, 1.2)) + 30 * math.sin(tg * 0.6)
        hy = 960 + dy + 230 * sb
        col = mix(MEGA, LAUT_B, 0.55 * sb)
        _hiu46(img, hx, hy, 660 - 120 * sb, al * qm * (1 - 0.6 * sb) * (1 - 0.75 * pud), col=col, tg=tg)
        if sb > 0.2:
            ex = hx + (660 - 120 * sb) * 0.40
            _glow11(img, ex, hy - 14, 34, (255, 230, 150), al * sb * (1 - pud) * 0.9)
    tt = tl - _t(N, "benar", dur)
    if tt > 0:
        _stiker11(img, 540, 800 + dy, "BENARKAH?", al, tt, bg=GELAP, fsz=44, rot=-4, tg=tg)
    tb = tl - _t(N, "benda", dur)
    if tb > 0:
        kb = eob(clamp(tb / 0.5), 1.8)
        _glow11(img, 540, 1140 + dy, 200, (255, 240, 200), al * 0.55 * clamp(tb / 0.4))
        _gigi46(img, 540, 1140 + dy, 250 * kb, al, rot=8 * math.sin(tg * 1.2))
    tmn = tl - _t(N, "mana", dur)
    if tmn > 0:
        rng = random.Random(46)
        for j in range(9):
            x = 150 + j * 97 + rng.uniform(-20, 20)
            kj = eob(clamp((tmn - j * 0.05) / 0.35), 2.0)
            _gigi46(img, x, 1512 + dy + rng.uniform(-10, 10), 60 * kj, al, rot=rng.uniform(-60, 60))
    tt = tl - _t(N, "gigi", dur)
    if tt > 0:
        _stiker11(img, 790, 1350 + dy, "GIGINYA!", al, tt, bg=accent, fsz=44, rot=5, tg=tg)


def sc_gigi46(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "gigi46"
    _hdr(img, sc, accent, tl, al)
    tg0 = _t(N, "gigi", dur)
    q = clamp((tl - tg0 + 0.3) / 0.5)
    if q <= 0.01:
        return
    H = 400
    gx, gy = 320, 1080 + dy
    yb, yt = gy + H * 0.5, gy - H * 0.47
    _glow11(img, gx, gy, 260, (255, 244, 214), al * q * 0.6)
    _gigi46(img, gx, gy, H * eob(q, 1.6), al)
    tt = tl - tg0
    if tt > 0:
        _stiker11(img, 540, 760 + dy, "MEGA = BESAR  ODON = GIGI", al, tt, bg=accent, fsz=26, rot=-3, tg=tg)
    tr = _t(N, "tinggi", dur)
    qr = esmooth(seg(tl, tr, tr + 0.9))
    if qr > 0:
        rx = 560
        top = yb - (yb - yt) * qr
        line_on(img, (rx, yb), (rx, top), INK, 5, al)
        ppc = (yb - yt) / 16.8
        for c in range(17):
            y = yb - c * ppc
            if y < top:
                break
            wdt = 26 if c % 5 == 0 else 14
            line_on(img, (rx, y), (rx + wdt, y), INK, 3, al)
            if c % 5 == 0 and c:
                _label11(img, rx + 52, y, str(c), MUTED, al, fsz=20, name=FB)
        line_on(img, (gx - 40, yb), (rx, yb), mix(INK, CREAM, 0.5), 2, al * qr, dash=8)
        line_on(img, (gx - 40, yt), (rx, yt), mix(INK, CREAM, 0.5), 2, al * esmooth(seg(qr, 0.9, 1.0)), dash=8)
    if tl > _t(N, "cm", dur):
        _angka46(img, 560, 1370 + dy, 16.8, "cm", al, tl, t0=_t(N, "cm", dur), dur=0.8,
                 col=mix(accent, INK, 0.15), fsz=64)
    th = tl - _t(N, "tangan", dur)
    if th > 0:
        k = eob(clamp(th / 0.5), 1.6)
        _tangan46(img, 820, 1150 + dy - (1 - k) * 60, 1.55, al * clamp(th / 0.3))
        _label11(img, 820, 1370 + dy, "telapak tangan", MUTED, al * clamp(th / 0.4), fsz=24, name=FB)
    tz = tl - _t(N, "gerigi", dur)
    if tz > 0:
        a = al * clamp(tz / 0.3)
        rrect_on(img, 110, 1460 + dy, 970, 1640 + dy, 30, WHITE, a, outline=mix(INK, CREAM, 0.7), width=2)
        zx, zy = 250, 1550 + dy
        line_on(img, (gx + 120, gy + 40), (zx, zy - 70), mix(INK, CREAM, 0.45), 3, a, dash=10)
        dot_on(img, zx, zy, 70, mix(MAHKOTA, WHITE, 0.15), a)
        pts = []
        for i in range(13):
            x = zx - 60 + i * 10
            pts.append((x, zy - 6 + (10 if i % 2 else -4)))
        pts += [(zx + 60, zy + 60), (zx - 60, zy + 60)]
        poly_on(img, pts, MAHKOTA, a)
        ring_on(img, zx, zy, 72, accent, 6, a)
        _label11(img, 420, zy, "bergerigi", INK, a, fsz=28, name=FB)
    tp = tl - _t(N, "roti", dur)
    if tp > 0:
        k = eob(clamp(tp / 0.4), 1.6)
        _pisau46(img, 560 + (1 - k) * 200, 1530 + dy, 380, al * clamp(tp / 0.25))
        _label11(img, 750, 1600 + dy, "seperti pisau roti", MUTED, al * clamp(tp / 0.3), fsz=22, name=FB)


def sc_ukuran46(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "ukuran46"
    _hdr(img, sc, accent, tl, al)
    tr = _t(N, "rawan", dur)
    q = esmooth(seg(tl, tr - 0.4, tr + 0.3))
    if q <= 0.01:
        return
    y0, y1 = 700 + dy, 1030 + dy
    rrect_on(img, 110, y0, 970, y1, 30, WHITE, al * q, outline=mix(INK, CREAM, 0.7), width=2)
    fos = esmooth(seg(tl, _t(N, "fosil", dur), _t(N, "fosil", dur) + 0.8))
    cy = 880 + dy
    _hiu46(img, 560, cy, 560, al * q, col=mix(MEGA, WHITE, 0.55 + 0.3 * fos), tg=tg * 0.6,
           isi=1.0 - 0.55 * fos, garis=mix(MEGA, CREAM, 0.3), mata=fos < 0.5)
    line_on(img, (330, cy - 8), (780, cy - 20), mix(TULANG, INK, 0.25), 8, al * q * (1 - fos) * 0.8)
    tt = tl - tr
    if tt > 0:
        _label11(img, 540, y1 - 34, "kerangka dari tulang rawan", INK, al * clamp(tt / 0.4) * (1 - fos), fsz=24, name=FB)
    tf = tl - _t(N, "fosil", dur)
    if tf > 0:
        _stiker11(img, 540, y1 - 30, "JARANG JADI FOSIL", al, tf, bg=GELAP, fsz=28, rot=-3, tg=tg)
    tv = tl - _t(N, "ruas", dur)
    if tv > 0:
        for j in range(11):
            u = j / 10
            kj = eob(clamp((tv - j * 0.07) / 0.35), 2.0)
            _ruas46(img, 350 + 420 * u, cy - 8 - 12 * u, 17 * kj, al)
    tb = tl - _t(N, "belgia", dur)
    if tb > 0:
        _stiker11(img, 250, 745 + dy, "FOSIL BELGIA", al, tb, bg=accent, fsz=24, rot=-5, tg=tg)
    ppm, x0 = 32.0, 140
    te = _t(N, "enam", dur)
    qa = esmooth(seg(tl, te - 1.2, te - 0.5))
    if qa > 0:
        ya = 1115 + dy
        _orang11(img, 160, ya + 8, 1.7, GELAP, al * qa)
        _hiu46(img, 230 + 3 * ppm, ya, 6 * ppm, al * qa, col=HIU_P, tg=tg)
        _label11(img, 560, ya, "hiu putih: 6 m", MUTED, al * qa, fsz=24, name=FB)
        _label11(img, 160, ya + 78, "manusia", MUTED, al * qa, fsz=18)
    tb2 = _t(N, "besar", dur)
    qg = esmooth(seg(tl, tb2, tb2 + 0.9))
    yb = 1335 + dy
    if qg > 0:
        L = 24 * ppm * (0.67 + 0.33 * eob(qg, 1.3))
        _hiu46(img, x0 + L / 2, yb, L, al * qg, col=mix(accent, WHITE, 0.6), tg=tg * 0.5, isi=0.35,
               garis=accent, mata=False)
    qe = esmooth(seg(tl, te - 0.3, te + 0.6))
    if qe > 0:
        L = 6 * ppm + 10 * ppm * eob(qe, 1.2)
        _hiu46(img, x0 + L / 2, yb, L, al, col=MEGA, tg=tg)
        _angka46(img, 330, 1560 + dy, 16, "meter (Belgia)", al, tl, t0=te, dur=0.8,
                 col=mix(MEGA, INK, 0.2), fsz=64)
    t4 = _t(N, "dua4", dur)
    if tl > t4:
        _angka46(img, 760, 1560 + dy, 24, "meter (terbesar)", al, tl, t0=t4, dur=0.8,
                 col=mix(accent, INK, 0.1), fsz=64)


def sc_ganti46(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "ganti46"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, 0.1, 0.6))
    if q <= 0.01:
        return
    x0, y0, x1, y1 = 110, 700 + dy, 970, 1630 + dy
    _laut46(img, x0, y0, x1, y1, al * q, tg, pasir=80, atas=mix(LAUT_A, WHITE, 0.1))
    sea = y1 - 70
    gy = 960 + dy
    rrect_on(img, 180, gy, 840, gy + 70, 35, (214, 120, 130), al * q)
    rrect_on(img, 180, gy + 40, 840, gy + 70, 0, (190, 96, 108), al * q)
    tl_ = _t(N, "lepas", dur)
    tr_ = _t(N, "ribuan", dur)
    ph = 0.0
    if tl > tl_:
        ph = 0.9 * (tl - tl_)
    if tl > tr_:
        ph += 2.6 * (tl - tr_) ** 2
    ql = esmooth(seg(tl, _t(N, "lapis", dur) - 0.3, _t(N, "lapis", dur) + 0.4))
    gap, xb = 130, 250
    jmin = int(-ph) - 2
    jatuh = []
    for j in range(jmin, 5):
        p = j + ph
        if p < 0:
            continue
        if p <= 4.4:
            x = xb + gap * p
            rot = 180 - 85 * (1 - clamp(p / 3.6))
            s = 70 + 40 * clamp(p / 3.6)
            a = al * ql * clamp(p / 0.4)
            _gigi46(img, x, gy - s * 0.42 + 10 * (1 - clamp(p / 3.6)), s, a, rot=rot)
        else:
            jatuh.append((j, (p - 4.4) / 1.3))

    def rng_x(j):
        return 200 + ((j * 7919) % 680)

    ndasar = 0
    for (j, f) in jatuh:
        if f < 1:
            x = xb + gap * 4.4 + (rng_x(j) - xb - gap * 4.4) * f
            y = gy - 50 + (sea - gy + 50) * f * f
            _gigi46(img, x, y, 90, al, rot=180 + 300 * f)
        else:
            ndasar += 1
            if ndasar <= 70:
                _gigi46(img, rng_x(j) + ((j * 31) % 17), sea + ((j * 13) % 26) - 8, 44, al,
                        rot=((j * 57) % 140) - 70)
    tt = tl - _t(N, "lapis", dur)
    if tt > 0:
        _label11(img, 300, gy + 115, "gigi cadangan", WHITE, al * clamp(tt / 0.4), fsz=24, name=FB)
        _label11(img, 740, gy + 115, "gigi depan", WHITE, al * clamp(tt / 0.4), fsz=24, name=FB)
        _stiker11(img, 330, 780 + dy, "BERLAPIS-LAPIS", al, tt, bg=accent, fsz=28, rot=-4, tg=tg)
    tgn = tl - _t(N, "ganti", dur)
    if tgn > 0:
        _panah11(img, (300, gy + 175), (700, gy + 175), al, clamp(tgn / 0.5), AMBER, width=8, lengkung=0.0)
        _label11(img, 500, gy + 225, "maju menggantikan", mix(AMBER, WHITE, 0.3), al * clamp(tgn / 0.4), fsz=22, name=FB)
    if tl > tl_:
        _label11(img, 780, 780 + dy, f"gigi lepas: {len(jatuh)}", WHITE, al * clamp((tl - tl_) / 0.4), fsz=28, name=FB)
    tt = tl - tr_
    if tt > 0:
        _stiker11(img, 540, 1380 + dy, "RIBUAN SEUMUR HIDUP", al, tt, bg=GELAP, fsz=32, rot=3, tg=tg)
    tt = tl - _t(N, "dasar", dur)
    if tt > 0:
        _label11(img, 540, y1 - 30, "menumpuk di dasar laut", WHITE, al * clamp(tt / 0.4), fsz=24, name=FB)


def sc_berhenti46(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "berhenti46"
    _hdr(img, sc, accent, tl, al)
    tb = _t(N, "batuan", dur)
    q = esmooth(seg(tl, _t(N, "temu", dur) - 0.4, _t(N, "temu", dur) + 0.4))
    if q <= 0.01:
        return
    cx0, cx1 = 110, 430
    ytop, ybot = 740 + dy, 1590 + dy
    ppj = (ybot - ytop) / 23.0
    lap = [(0, 2), (2, 5), (5, 9), (9, 14), (14, 19), (19, 23)]
    for i, (a0, a1) in enumerate(lap):
        col = mix(PASIR, (150, 118, 84), 0.15 + 0.14 * i)
        r = 24 if i in (0, len(lap) - 1) else 0
        y_a, y_b = ytop + a0 * ppj, ytop + a1 * ppj
        rrect_on(img, cx0, y_a, cx1, y_b + (0 if i == len(lap) - 1 else 1), r, col, al * q)
        if i == 0:
            rrect_on(img, cx0, y_a + 24, cx1, y_b + 1, 0, col, al * q)
        if i == len(lap) - 1:
            rrect_on(img, cx0, y_a, cx1, y_b - 24, 0, col, al * q)
    for (lbl, age) in (("sekarang", 0), ("3,6 juta th", 3.6), ("10 juta th", 10), ("20 juta th", 20)):
        y = ytop + age * ppj + (14 if age == 0 else 0)
        if age == 3.6 and tl < _t(N, "tiga", dur):
            continue
        line_on(img, (cx1, y), (cx1 + 18, y), INK, 3, al * q)
        _label11(img, cx1 + 85, y, lbl, INK if age == 3.6 else MUTED, al * q, fsz=22, name=FB)
    sw = esmooth(seg(tl, tb, _t(N, "tiga", dur) + 0.2))
    rng = random.Random(8)
    for j in range(26):
        age = rng.uniform(3.9, 22.2)
        x = rng.uniform(cx0 + 40, cx1 - 40)
        rot = rng.uniform(-80, 80)
        u = (22.2 - age) / (22.2 - 3.9)
        kj = eob(clamp((sw - u * 0.9) / 0.1), 2.0) if sw > 0 else 0
        if kj > 0:
            _gigi46(img, x, ytop + age * ppj, 46 * kj, al, rot=rot)
    tt = tl - _t(N, "dua", dur)
    if tt > 0:
        _stiker11(img, 800, 1470 + dy, "ADA GIGI", al, tt, bg=GREEN, fsz=28, rot=-3, tg=tg)
    y36 = ytop + 3.6 * ppj
    tt = tl - _t(N, "tiga", dur)
    if tt > 0:
        k = esmooth(clamp(tt / 0.5))
        line_on(img, (cx0 - 10, y36), (cx0 - 10 + (cx1 - cx0 + 20) * k, y36), RED, 6, al, dash=14)
        _stiker11(img, 790, y36 + 10, "TERMUDA", al, tt, bg=RED, fsz=32, rot=4, tg=tg)
    tt = tl - _t(N, "muda", dur)
    if tt > 0:
        a = al * clamp(tt / 0.4)
        rrect_on(img, cx0 + 8, ytop + 8, cx1 - 8, y36 - 8, 18, mix(RED, WHITE, 0.75), a * 0.85)
        paste_c(img, (cx0 + cx1) / 2, (ytop + y36) / 2 + 4, "0 GIGI", font(FB, 38), RED, a)
    ts = tl - _t(N, "segar", dur)
    if ts > 0:
        k = eob(clamp(ts / 0.5), 1.5)
        a = al * clamp(ts / 0.3)
        lx0, lx1, ly0, ly1 = 640 + (1 - k) * 200, 970 + (1 - k) * 200, 1080 + dy, 1340 + dy
        _laut46(img, lx0, ly0, lx1, ly1, a, tg, pasir=50, r=24)
        paste_c(img, (lx0 + lx1) / 2, ly0 + 50, "laut hari ini", font(FB, 26), WHITE, a)
        gx = (lx0 + lx1) / 2 + 60 * math.sin(tg * 1.5)
        ring_on(img, gx, ly1 - 90, 44, WHITE, 5, a)
        line_on(img, (gx + 31, ly1 - 59), (gx + 62, ly1 - 28), WHITE, 8, a)
    tk = tl - _t(N, "kini", dur)
    if tk > 0:
        D._check5_on(img, 805, 1210 + dy, 70, "x", al, clamp(tk / 0.35), col=RED)
        _label11(img, 805, 1385 + dy, "gigi segar: TIDAK ADA", RED, al * clamp(tk / 0.3), fsz=24, name=FB)


def sc_dalam46(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "dalam46"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.5))
    if q <= 0.01:
        return
    x0, x1, y0, y1 = 110, 530, 700 + dy, 1620 + dy
    _laut46(img, x0, y0, x1, y1, al * q, tg, bawah=(4, 14, 34))
    for (lbl, yy) in (("0 m", 750), ("200 m", 900), ("1.000 m", 1150), ("4.000 m", 1570)):
        _label11(img, x0 + 70, yy + dy, lbl, WHITE, al * q * 0.85, fsz=20, name=FB)
    ts, tdl = _t(N, "sembunyi", dur), _t(N, "dalam", dur)
    k = esmooth(seg(tl, ts, tdl + 0.8))
    dg = esmooth(seg(tl, _t(N, "dingin", dur), _t(N, "dingin", dur) + 0.8))
    jit = 4 * math.sin(tg * 40) * dg
    _hiu46(img, 350 + jit, 860 + dy + 520 * k, 300, al * q, col=mix(MEGA, DINGIN, 0.5 * dg), tg=tg)
    if tl > ts + 0.4:
        _stiker11(img, 440, 1250 + dy, "?", al * (1 - dg), tl - ts - 0.4, bg=AMBER, fsz=56, rot=8, tg=tg)
    th = tl - _t(N, "hangat", dur)
    if th > 0:
        a = al * clamp(th / 0.3)
        _stiker11(img, 770, 745 + dy, "BERDARAH HANGAT", al, th, bg=RED, fsz=26, rot=-3, tg=tg)
        fr = 0.25 + 0.55 * esmooth(seg(tl, _t(N, "suhu", dur) - 0.6, _t(N, "suhu", dur) + 0.4))
        _termo46(img, 650, 830 + dy, 1110 + dy, fr, a)
    tu = tl - _t(N, "suhu", dur)
    if tu > 0:
        _angka46(img, 840, 930 + dy, 27, "derajat C", al, tl, t0=_t(N, "suhu", dur), dur=0.7,
                 col=RED, fsz=80)
        _label11(img, 840, 1080 + dy, "suhu tubuh", MUTED, al * clamp(tu / 0.4), fsz=22, name=FB)
    tm = tl - _t(N, "makan", dur)
    if tm > 0:
        a = al * clamp(tm / 0.3)
        bx0, bx1 = 590, 970
        rrect_on(img, bx0, 1230 + dy, bx1, 1620 + dy, 28, WHITE, a, outline=mix(INK, CREAM, 0.7), width=2)
        paste_c(img, 780, 1275 + dy, "butuh makan", font(FB, 24), INK, a)
        w = (bx1 - bx0 - 60) * esmooth(clamp(tm / 0.8))
        rrect_on(img, bx0 + 30, 1305 + dy, bx0 + 30 + max(24, w), 1345 + dy, 20, accent, a)
        for j in range(4):
            _ikan46(img, bx0 + 70 + j * 80, 1395 + dy, 0.9, al * clamp((tm - j * 0.12) / 0.3))
    tdg = tl - _t(N, "dingin", dur)
    if tdg > 0:
        a = al * clamp(tdg / 0.4)
        _label11(img, 320, 1480 + dy, "air 2-4 derajat", DINGIN, a, fsz=26, name=FB)
        for j in range(5):
            D.star4(img, 170 + j * 80, 1530 + dy + 10 * math.sin(tg + j), 10, DINGIN, a * 0.8)
    tk = tl - _t(N, "miskin", dur)
    if tk > 0:
        a = al * clamp(tk / 0.3)
        paste_c(img, 780, 1465 + dy, "makanan di laut dalam", font(FB, 22), INK, a)
        rrect_on(img, 620, 1495 + dy, 620 + 60 * esmooth(clamp(tk / 0.6)) + 24, 1535 + dy, 20, RED, a)
        _stiker11(img, 800, 1580 + dy, "TIDAK CUKUP", al, tk, bg=GELAP, fsz=24, rot=-3, tg=tg)


def sc_punah46(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "punah46"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.5))
    if q <= 0.01:
        return
    x0, x1, y0, y1 = 110, 970, 700 + dy, 1150 + dy
    dg = esmooth(seg(tl, _t(N, "dingin", dur), _t(N, "dingin", dur) + 1.0))
    tu = esmooth(seg(tl, _t(N, "turun", dur), _t(N, "turun", dur) + 1.0))
    rrect_on(img, x0, y0, x1, y1, 30, mix((250, 226, 180), (214, 228, 242), dg), al * q)
    yw = 800 + dy + 90 * tu
    air = mix((70, 170, 190), (40, 90, 170), dg)
    poly_on(img, [(x0, yw), (x1, yw), (x1, y1 - 30), (x1 - 30, y1), (x0 + 30, y1), (x0, y1 - 30)], air, al * q)
    _gelom11(img, x0 + 20, x1 - 20, yw, 5, 80, tg * 3, mix(air, WHITE, 0.5), 4, al * q)
    darat = [(x0, 790 + dy), (250, 800 + dy), (380, 900 + dy), (560, 930 + dy), (700, 1060 + dy), (x1, 1090 + dy),
             (x1, y1 - 30), (x1 - 30, y1), (x0 + 30, y1), (x0, y1 - 30)]
    poly_on(img, darat, (184, 150, 104), al * q)
    tt = tl - _t(N, "dingin", dur)
    if tt > 0:
        _stiker11(img, 790, 760 + dy, "LAUT MENDINGIN", al, tt, bg=BLUE, fsz=26, rot=4, tg=tg)
        for j in range(4):
            D.star4(img, 640 + j * 90, 850 + dy + 8 * math.sin(tg * 2 + j), 12, WHITE, al * dg)
    tt = tl - _t(N, "turun", dur)
    if tt > 0:
        _panah11(img, (230, 740 + dy), (230, 790 + dy + 90 * tu), al, clamp(tt / 0.5), RED, width=7,
                 lengkung=0.0, head=18)
        _label11(img, 440, 1110 + dy, "laut dangkal menyusut", WHITE, al * clamp(tt / 0.4), fsz=24, name=FB)
    by0, by1 = 1220 + dy, 1630 + dy
    tp = tl - _t(N, "paus", dur)
    if tp > 0:
        _laut46(img, x0, by0, x1, by1, al * clamp(tp / 0.3), tg, pasir=40)
        tpi = tl - _t(N, "pindah", dur)
        mv = esmooth(clamp(tpi / 1.4)) if tpi > 0 else 0
        _paus46(img, 540 + 330 * mv, 1320 + dy - 40 * mv, 280 * (1 - 0.45 * mv),
                al * clamp(tp / 0.3) * (1 - 0.6 * mv), tg=tg)
        if tpi > 0:
            _label11(img, 700, 1420 + dy, "paus pindah ke air dingin", WHITE, al * clamp(tpi / 0.4), fsz=22, name=FB)
    th = tl - _t(N, "hiu", dur)
    if th > 0:
        k = eob(clamp(th / 0.6), 1.3)
        _hiu46(img, 290 - (1 - k) * 120, 1515 + dy, 300, al * clamp(th / 0.3), col=MEGA, tg=tg)
        _hiu46(img, 800 + (1 - k) * 120, 1515 + dy, 220, al * clamp(th / 0.3), col=HIU_P, arah=-1, tg=tg + 1)
        for j in range(3):
            _ikan46(img, 520 + j * 30, 1500 + dy + (j % 2) * 26 + 5 * math.sin(tg * 3 + j), 0.8,
                    al * clamp(th / 0.3), arah=-1)
        _label11(img, 290, 1590 + dy, "megalodon", WHITE, al * clamp(th / 0.4), fsz=22, name=FB)
        _label11(img, 800, 1590 + dy, "hiu putih", WHITE, al * clamp(th / 0.4), fsz=22, name=FB)
    tt = tl - _t(N, "rebut", dur)
    if tt > 0:
        _stiker11(img, 540, 1275 + dy, "BEREBUT MANGSA", al, tt, bg=accent, fsz=30, rot=-3, tg=tg)


def sc_palsu46(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "palsu46"
    _hdr(img, sc, accent, tl, al)
    tp = tl - _t(N, "percaya", dur)
    if tp <= 0:
        return
    ttv = tl - _t(N, "tv", dur)
    if ttv > 0:
        kt = eob(clamp(ttv / 0.5), 1.5)
        _tv46(img, 540, 960 + dy + (1 - kt) * 80, 700, 400, al * clamp(ttv / 0.3), tg)
        paste_c(img, 540, 1112 + dy, "DOKUMENTER?", font(FB, 28), WHITE, al * clamp(ttv / 0.3))
    else:
        _stiker11(img, 540, 960 + dy, "KENAPA PERCAYA?", al, tp, bg=GELAP, fsz=36, rot=-3, tg=tg)
    tt = tl - _t(N, "tahun", dur)
    if tt > 0:
        _stiker11(img, 220, 745 + dy, "2013", al, tt, bg=accent, fsz=34, rot=-6, tg=tg)
    ta = tl - _t(N, "aktor", dur)
    if ta > 0:
        k = eob(clamp(ta / 0.4), 1.6)
        px, py = 330, 1040 + dy
        a = al * clamp(ta / 0.25)
        dot_on(img, px, py - 70 * k, 24 * k, (234, 192, 152), a)
        rrect_on(img, px - 34 * k, py - 44 * k, px + 34 * k, py + 30 * k, 14, WHITE, a)
        line_on(img, (px, py - 44 * k), (px, py + 30 * k), mix(INK, CREAM, 0.5), 3, a)
        _stiker11(img, 800, 1180 + dy, "AKTOR", al, ta, bg=GELAP, fsz=28, rot=5, tg=tg)
    tf = tl - _t(N, "fiksi", dur)
    if tf > 0:
        D._stamp_on(img, 560, 900 + dy, "FIKSI", al, tf, col=RED, fsz=96, rot=-10)
    tj = tl - _t(N, "jajak", dur)
    if tj > 0:
        a = al * clamp(tj / 0.3)
        rrect_on(img, 110, 1290 + dy, 970, 1640 + dy, 30, WHITE, a, outline=mix(INK, CREAM, 0.7), width=2)
        paste_c(img, 540, 1335 + dy, "jajak pendapat penonton", font(FB, 26), INK, a)
        tpc = _t(N, "persen", dur)
        fr = 0.73 * esmooth(seg(tl, tpc, tpc + 0.9))
        _pie46(img, 290, 1490 + dy, 110, fr, accent, a)
        if tl > tpc:
            _angka46(img, 660, 1450 + dy, 73, "persen", al, tl, t0=tpc, dur=0.9,
                     col=mix(accent, INK, 0.1), fsz=88)
    tk = tl - _t(N, "punah", dur)
    if tk > 0:
        _label11(img, 660, 1605 + dy, "mengira masih hidup", RED, al * clamp(tk / 0.3), fsz=24, name=FB)


def sc_rangkuman46(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "rangkuman46"
    _hdr(img, sc, accent, tl, al)
    items = [("s1", "HIU MELEPAS RIBUAN GIGI", "seumur hidupnya", BLUE),
             ("s2", "GIGINYA BERHENTI MUNCUL", "sejak 3,6 juta tahun lalu", AMBER),
             ("s3", "MEGALODON SUDAH PUNAH", "bukan bersembunyi di laut dalam", RED)]
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
        _label11(img, 400, 1505 + dy, "yang masih percaya", MUTED, al * clamp(tt / 0.3), fsz=26)
        _gigi46(img, 830, 1450 + dy, 150 * eob(clamp(tt / 0.4), 1.8), al, rot=10 * math.sin(tg * 1.5))


VISUALS46 = {
    "intro_mega46": sc_intro_mega46, "gigi46": sc_gigi46, "ukuran46": sc_ukuran46,
    "ganti46": sc_ganti46, "berhenti46": sc_berhenti46, "dalam46": sc_dalam46, "punah46": sc_punah46,
    "palsu46": sc_palsu46, "rangkuman46": sc_rangkuman46,
}
