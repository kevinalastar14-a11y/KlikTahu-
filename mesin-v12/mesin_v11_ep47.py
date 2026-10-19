"""Ep47 KENAPA PETIR SERING MENYAMBAR POHON? - adegan mesin v11 (diimpor oleh mesin_v11).

Pola sama dengan mesin_v11_ep43..46: `B47[visual] = {nama: (fraksi, suara)}`; `_t(N, nama, dur)`.
Fraksi disetel dari posisi kata kunci VO (timeline captions, 24 Sep 2026).
Objek: langit badai + awan + hujan, sambaran bergerigi berpendar (+ kilat layar), pohon (bisa terbelah),
peta Jawa + pin Bogor, kalender 365 hari (322 hari petir), batang suhu matahari vs petir,
gelombang guntur, pemandu bertahap bercabang, percikan penyambut dari benda tinggi,
penampang batang (kulit kayu / lapisan basah / kayu inti), loncatan samping, rumah & mobil aman,
Gedung Empire State disambar berulang.
"""
import math
import random

import diagrams as D
from diagrams import (INK, CREAM, WHITE, MUTED, RED, BLUE, GREEN, AMBER, FB, FS,
                      mix, seg, clamp, esmooth, eob, font, paste_c,
                      rrect_on, line_on, dot_on, ring_on, poly_on, ell)

import mesin_v11 as M
from mesin_v11 import (_stiker11, _label11, _glow11, _panah11, _partikel11, _judul11, _hdr,
                       _orang11, GELAP)

B47 = {
    "intro_petir47": {"awan": (0.03, "guntur"), "sasaran": (0.26, "zap"), "belah": (0.42, "retak"),
                      "ledak": (0.51, "boom"), "tanya": (0.57, "pop"), "teduh": (0.74, "swish"),
                      "bahaya": (0.86, "impact")},
    "bogor47": {"negeri": (0.13, "guntur"), "guinness": (0.24, "pop"), "bogor": (0.35, "ding"),
                "terbanyak": (0.49, "impact"), "hitung": (0.62, "tick"), "hampir": (0.86, "zap")},
    "panas47": {"sambar": (0.07, "zap"), "hitung": (0.25, "tick"), "lima": (0.42, "impact"),
                "matahari": (0.55, "kilau"), "muai": (0.70, "whoosh"), "guntur": (0.87, "guntur")},
    "turun47": {"awan": (0.04, "whoosh"), "rambat": (0.29, "zap"), "kelok": (0.43, "glitch"),
                "raba": (0.52, "tick"), "puluhan": (0.71, "swish"), "tentu": (0.87, "pop")},
    "sambut47": {"kirim": (0.23, "zap"), "sambut": (0.41, "swish_up"), "tinggi": (0.55, "tick"),
                 "cepat": (0.62, "boom"), "pohon": (0.69, "ding"), "menang": (0.92, "impact")},
    "getah47": {"air": (0.12, "gelembung"), "arus": (0.21, "zap"), "basah": (0.38, "swish"),
                "didih": (0.56, "gelembung"), "uap": (0.63, "whoosh"), "ledak": (0.86, "boom")},
    "samping47": {"jangan": (0.10, "impact"), "sambar": (0.22, "zap"), "lompat": (0.34, "glitch"),
                  "orang": (0.48, "thud"), "aman": (0.57, "pop"), "bangunan": (0.72, "ding"),
                  "mobil": (0.86, "ding")},
    "mitos47": {"katanya": (0.04, "pop"), "dua": (0.33, "tick"), "mitos": (0.42, "impact"),
                "gedung": (0.48, "whoosh"), "sambar": (0.68, "zap"), "hitung": (0.79, "guntur")},
    "rangkuman47": {"s1": (0.04, "pop"), "s2": (0.25, "pop"), "s3": (0.50, "pop"),
                    "kirim": (0.70, "impact")},
}
for _k, _v in B47.items():
    M.BEATS[_k] = sorted(_v.values())

LANGIT_A = (44, 52, 78)
LANGIT_B = (92, 104, 132)
AWAN = (70, 78, 100)
KILAT = (255, 250, 222)
UNGU = (190, 170, 255)
DAUN = (60, 130, 80)
KAYU = (120, 84, 56)
KAYU_M = (206, 170, 120)
TANAH = (78, 96, 70)
KUNING = (255, 206, 70)
AIR = (90, 160, 230)


def _t(nama, key, dur):
    return B47[nama][key][0] * dur


# ------------------------------------------------------------------ geometri petir
_ZIG = {}


def _zig(x0, y0, x1, y1, seed, n=11, amp=42):
    """Jalur petir bergerigi (ter-cache) dari (x0,y0) ke (x1,y1)."""
    key = (round(x0), round(y0), round(x1), round(y1), seed, n, amp)
    p = _ZIG.get(key)
    if p is None:
        rng = random.Random(seed)
        p = [(x0, y0)]
        for i in range(1, n):
            u = i / n
            p.append((x0 + (x1 - x0) * u + rng.uniform(-amp, amp) * math.sin(math.pi * u) ** 0.5,
                      y0 + (y1 - y0) * u + rng.uniform(-amp, amp) * 0.25))
        p.append((x1, y1))
        _ZIG[key] = p
    return p


def _potong(pts, f):
    """Ambil fraksi f (0..1) dari polyline (ujung diinterpolasi)."""
    if f >= 1:
        return list(pts)
    if f <= 0:
        return pts[:1]
    L = f * (len(pts) - 1)
    i = int(L)
    u = L - i
    out = list(pts[:i + 1])
    if i + 1 < len(pts):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        out.append((ax + (bx - ax) * u, ay + (by - ay) * u))
    return out


def _petir47(img, pts, alpha, width=9, col=KILAT, glow=True):
    """Sambaran: pendar + garis luar kebiruan + inti putih."""
    if alpha <= 0.01 or len(pts) < 2:
        return
    if glow:
        for (x, y) in pts[::3]:
            _glow11(img, x, y, 70, mix(col, UNGU, 0.4), alpha * 0.45)
    M._pline(img, pts, mix(col, UNGU, 0.55), width * 2.2, alpha * 0.55)
    M._pline(img, pts, col, width, alpha)


def _kilat47(img, x0, y0, x1, y1, tt, alpha, r=30):
    """Kilat layar: panel memutih sekejap lalu meredup (berkedip dua kali)."""
    if tt < 0 or tt > 0.7:
        return
    a = math.exp(-tt * 7) + 0.5 * math.exp(-abs(tt - 0.18) * 30)
    rrect_on(img, x0, y0, x1, y1, r, WHITE, clamp(alpha * 0.75 * a))


# ------------------------------------------------------------------ objek Ep47
def _langit47(img, x0, y0, x1, y1, alpha, atas=LANGIT_A, bawah=LANGIT_B, r=30):
    if alpha <= 0.01:
        return
    rrect_on(img, x0, y0, x1, y1, r, atas, alpha)
    nb = 14
    h = (y1 - y0 - 2 * r) / nb
    for i in range(nb):
        u = (i + 0.5) / nb
        rrect_on(img, x0, y0 + r + i * h, x1, y0 + r + (i + 1) * h + 1, 0, mix(atas, bawah, u), alpha)
    rrect_on(img, x0, y1 - r * 2, x1, y1, r, bawah, alpha)


def _awan47(img, cx, cy, s, alpha, col=AWAN, tg=0.0):
    if alpha <= 0.01:
        return
    dx = 6 * math.sin(tg * 0.7)
    for (ox, oy, r) in ((-95, 12, 52), (-40, -22, 70), (30, -32, 78), (95, -2, 60), (140, 22, 42),
                        (-140, 26, 38), (0, 20, 64)):
        dot_on(img, cx + (ox + dx) * s, cy + oy * s, r * s, col, alpha)
    for (ox, oy, r) in ((-40, -34, 40), (30, -46, 44)):
        dot_on(img, cx + (ox + dx) * s, cy + oy * s, r * s, mix(col, WHITE, 0.12), alpha * 0.8)


def _hujan47(img, x0, y0, x1, y1, tg, alpha, n=36, col=(170, 190, 230)):
    if alpha <= 0.01:
        return
    H = y1 - y0
    for j in range(n):
        u = (j * 0.618) % 1.0
        v = (j * 0.371 + tg * 1.3) % 1.0
        x = x0 + (x1 - x0 - 30) * u + 15
        y = y0 + H * v
        if y + 34 > y1:
            continue
        line_on(img, (x, y), (x - 8, y + 30), col, 3, alpha * 0.55)


def _pohon47(img, cx, yb, h, alpha, belah=0.0, daun=DAUN, tg=0.0):
    """Pohon: batang + tajuk bulat berlapis; belah 0..1 -> terbelah dua (bagian menjauh + retak terang)."""
    if alpha <= 0.01:
        return
    w = h * 0.13
    yt = yb - h * 0.62
    sw = 3 * math.sin(tg * 1.1)
    off = 26 * eob(belah, 1.4) if belah > 0 else 0
    for sgn in ((-1, 1) if belah > 0 else (0,)):
        ox = sgn * off
        rot = sgn * 6 * belah
        if belah > 0:
            xa, xb_ = (cx - w / 2 + ox, cx + ox) if sgn < 0 else (cx + ox, cx + w / 2 + ox)
            poly_on(img, [(xa, yb), (xb_, yb), (xb_ + rot * 3, yt), (xa + rot * 3, yt)], KAYU, alpha)
        else:
            poly_on(img, [(cx - w / 2, yb), (cx + w / 2, yb), (cx + w * 0.35, yt), (cx - w * 0.35, yt)], KAYU, alpha)
            line_on(img, (cx, yt + h * 0.12), (cx - h * 0.16, yt - h * 0.02), KAYU, max(4, int(w * 0.35)), alpha)
            line_on(img, (cx, yt + h * 0.2), (cx + h * 0.18, yt + h * 0.02), KAYU, max(4, int(w * 0.35)), alpha)
    cyc = yb - h * 0.8
    R = h * 0.26
    lobes = ((-0.9, 0.25, 0.75), (0.9, 0.25, 0.75), (-0.45, -0.35, 0.85), (0.45, -0.35, 0.85), (0, 0.1, 1.0),
             (0, -0.7, 0.7))
    for (ox, oy, rr) in lobes:
        sgn = -1 if ox < 0 else (1 if ox > 0 else 0)
        dx = sgn * off * 1.6 + sw
        dot_on(img, cx + ox * R + dx, cyc + oy * R, R * rr, daun, alpha)
    for (ox, oy, rr) in ((-0.4, -0.45, 0.35), (0.3, -0.8, 0.28)):
        dot_on(img, cx + ox * R + sw, cyc + oy * R, R * rr, mix(daun, WHITE, 0.22), alpha * 0.8)
    if belah > 0:
        pts = _zig(cx, yt - 10, cx, yb, 7, n=9, amp=10)
        M._pline(img, pts, mix(KUNING, WHITE, 0.4), 6, alpha * (1 - 0.6 * belah))


def _rumah47(img, cx, yb, w, alpha, col=(210, 120, 90)):
    h = w * 0.7
    rrect_on(img, cx - w / 2, yb - h, cx + w / 2, yb, 6, (232, 222, 200), alpha)
    poly_on(img, [(cx - w * 0.62, yb - h + 4), (cx, yb - h - w * 0.45), (cx + w * 0.62, yb - h + 4)], col, alpha)
    rrect_on(img, cx - w * 0.12, yb - h * 0.55, cx + w * 0.12, yb, 4, KAYU, alpha)
    rrect_on(img, cx + w * 0.22, yb - h * 0.75, cx + w * 0.42, yb - h * 0.5, 3, (150, 200, 240), alpha)


def _tiang47(img, cx, yb, h, alpha, col=(90, 96, 110)):
    line_on(img, (cx, yb), (cx, yb - h), col, 9, alpha)
    line_on(img, (cx - 34, yb - h + 22), (cx + 34, yb - h + 22), col, 6, alpha)


def _mobil47(img, cx, yb, w, alpha, col=(200, 60, 60)):
    h = w * 0.28
    rrect_on(img, cx - w / 2, yb - h - 24, cx + w / 2, yb - 24, 18, col, alpha)
    poly_on(img, [(cx - w * 0.3, yb - h - 20), (cx - w * 0.18, yb - h - w * 0.22), (cx + w * 0.18, yb - h - w * 0.22),
                  (cx + w * 0.32, yb - h - 20)], col, alpha)
    poly_on(img, [(cx - w * 0.24, yb - h - 24), (cx - w * 0.15, yb - h - w * 0.19), (cx + w * 0.15, yb - h - w * 0.19),
                  (cx + w * 0.24, yb - h - 24)], (170, 210, 240), alpha)
    for sx in (-0.3, 0.3):
        dot_on(img, cx + sx * w, yb - 24, w * 0.1, GELAP, alpha)
        dot_on(img, cx + sx * w, yb - 24, w * 0.045, (180, 180, 190), alpha)


def _gedung47(img, cx, yb, h, alpha, col=(14, 16, 30), lampu=(250, 220, 120), tg=0.0):
    """Siluet Gedung Empire State: badan bertingkat mundur + menara + antena. Kembalikan titik ujung antena."""
    u = h / 100.0
    tiers = ((34, 0, 52), (26, 52, 66), (20, 66, 76), (13, 76, 82), (8, 82, 88))
    for (hw, a0, a1) in tiers:
        rrect_on(img, cx - hw * u, yb - a1 * u, cx + hw * u, yb - a0 * u, 2, col, alpha)
    line_on(img, (cx, yb - 88 * u), (cx, yb - 100 * u), col, max(3, int(1.4 * u)), alpha)
    rng = random.Random(5)
    for j in range(46):
        a = rng.uniform(4, 74)
        hw = 30 if a < 52 else (22 if a < 66 else 16)
        x = cx + rng.uniform(-hw, hw) * u
        on = (math.sin(tg * 0.8 + j) > -0.3)
        rrect_on(img, x - 3, yb - a * u - 4, x + 3, yb - a * u + 4, 1, lampu, alpha * (0.85 if on else 0.25))
    return cx, yb - 100 * u


def _jawa47(img, x0, y0, w, h, alpha, col=(120, 170, 110)):
    """Siluet Pulau Jawa sederhana (x barat->timur, y utara->selatan)."""
    P = [(0.0, 0.62), (0.03, 0.42), (0.07, 0.22), (0.11, 0.06), (0.18, 0.09), (0.27, 0.13), (0.36, 0.22),
         (0.47, 0.26), (0.55, 0.20), (0.63, 0.28), (0.71, 0.31), (0.79, 0.25), (0.86, 0.35), (0.93, 0.33),
         (1.0, 0.46), (0.99, 0.70), (0.94, 0.80), (0.84, 0.86), (0.72, 0.82), (0.60, 0.91), (0.48, 0.88),
         (0.36, 0.81), (0.24, 0.76), (0.14, 0.73), (0.05, 0.79)]
    poly_on(img, [(x0 + w * x, y0 + h * y) for (x, y) in P], col, alpha, outline=mix(col, INK, 0.3), width=3)


def _angka47(img, cx, cy, nilai, unit, al, tl, t0, dur=0.8, col=None, fsz=64):
    D._hitung_on(img, cx, cy, nilai, "", al, tl, t0=t0, dur=dur, col=col, fsz=fsz)
    if unit and tl > t0:
        _label11(img, cx, cy + fsz * 0.95, unit, MUTED, al * clamp((tl - t0) / 0.3), fsz=max(20, fsz // 3), name=FB)


def _percik47(img, x0, y0, x1, y1, f, seed, alpha, col=UNGU):
    """Percikan penyambut (streamer) tipis berkedip dari (x0,y0) menuju (x1,y1), panjang fraksi f."""
    if f <= 0.01 or alpha <= 0.01:
        return
    pts = _potong(_zig(x0, y0, x1, y1, seed, n=7, amp=16), f)
    fl = 0.6 + 0.4 * math.sin(seed * 3.1 + f * 40)
    M._pline(img, pts, mix(col, WHITE, 0.4), 4, alpha * fl)
    _glow11(img, pts[-1][0], pts[-1][1], 26, col, alpha * 0.8)


# ------------------------------------------------------------------ adegan
def sc_intro_petir47(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "intro_petir47"
    L = sc.get("lines") or ["KENAPA PETIR SUKA", "MENYAMBAR POHON?"]
    _judul11(img, L[0], INK, tl, al, y=455, fsz=66, t0=0.05)
    _judul11(img, L[1], accent, tl, al, y=560, fsz=66, t0=0.30, hl="POHON?")
    q = esmooth(seg(tl, _t(N, "awan", dur), _t(N, "awan", dur) + 0.7))
    if q <= 0.01:
        return
    x0, y0, x1, y1 = 90, 690 + dy, 990, 1560 + dy
    k = eob(q, 1.3)
    _langit47(img, x0, y0 + (1 - k) * 120, x1, y1, al * q)
    _awan47(img, 380, 800 + dy, 1.25, al * q, tg=tg)
    _awan47(img, 800, 770 + dy, 0.9, al * q, tg=tg + 2)
    _hujan47(img, x0 + 10, 860 + dy, x1 - 10, y1 - 150, tg, al * q)
    # bukit + pohon
    poly_on(img, [(x0, y1 - 140), (300, y1 - 210), (560, y1 - 200), (x1, y1 - 120), (x1, y1 - 30), (x1 - 30, y1),
                  (x0 + 30, y1), (x0, y1 - 30)], TANAH, al * q)
    ts = _t(N, "sasaran", dur)
    belah = esmooth(seg(tl, _t(N, "belah", dur), _t(N, "belah", dur) + 0.5))
    tx, tyb = 440, y1 - 200
    _pohon47(img, tx, tyb, 520, al * q, belah=belah, tg=tg)
    tt = tl - ts
    if tt > 0:
        a = clamp(1 - (tt - 0.5) / 0.4) if tt > 0.5 else 1.0
        pts = _zig(410, 860 + dy, tx, tyb - 520 * 0.95, 11, n=12, amp=46)
        _petir47(img, _potong(pts, clamp(tt / 0.12)), al * a, width=10)
        _kilat47(img, x0, y0, x1, y1, tt, al)
    tl_ = tl - _t(N, "ledak", dur)
    if tl_ > 0:
        _partikel11(img, tx, tyb - 200, tl_, KUNING, al, n=16, jarak=220, seed=4)
        rng = random.Random(9)
        for j in range(8):
            ang = rng.uniform(-2.8, -0.3)
            dd = 60 + 260 * eob(clamp(tl_ / 0.6), 1.2)
            x, y = tx + dd * math.cos(ang), tyb - 200 + dd * math.sin(ang) + 300 * clamp(tl_ / 1.5) ** 2
            if y < y1 - 30:
                rrect_on(img, x - 12, y - 5, x + 12, y + 5, 3, KAYU, al * clamp(1 - tl_ / 2.5))
    tt = tl - _t(N, "tanya", dur)
    if tt > 0:
        _stiker11(img, 760, 1010 + dy, "KENAPA POHON?", al, tt, bg=accent, fsz=36, rot=4, tg=tg)
    tt = tl - _t(N, "teduh", dur)
    if tt > 0:
        k2 = eob(clamp(tt / 0.5), 1.4)
        _orang11(img, 560 + (1 - k2) * 200, tyb - 40, 2.2, (230, 230, 240), al * clamp(tt / 0.3))
    tt = tl - _t(N, "bahaya", dur)
    if tt > 0:
        _stiker11(img, 720, 1240 + dy, "BERBAHAYA?", al, tt, bg=RED, fsz=40, rot=-4, tg=tg)


def sc_bogor47(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "bogor47"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "negeri", dur) - 0.5, _t(N, "negeri", dur) + 0.3))
    if q <= 0.01:
        return
    # peta Jawa
    px0, py0, px1, py1 = 110, 700 + dy, 970, 980 + dy
    rrect_on(img, px0, py0, px1, py1, 30, (180, 214, 236), al * q)
    jx, jy, jw, jh = 150, 745 + dy, 780, 200
    _jawa47(img, jx, jy, jw, jh, al * q)
    bx, by = jx + jw * 0.17, jy + jh * 0.26
    tb = tl - _t(N, "bogor", dur)
    if tb > 0:
        k = eob(clamp(tb / 0.4), 1.8)
        _glow11(img, bx, by, 60, KUNING, al * 0.8)
        pin_y = by - 46 * k
        dot_on(img, bx, pin_y, 20, RED, al)
        poly_on(img, [(bx - 14, pin_y + 10), (bx + 14, pin_y + 10), (bx, by)], RED, al)
        dot_on(img, bx, pin_y, 7, WHITE, al)
        _stiker11(img, bx + 190, by - 30, "BOGOR", al, tb, bg=GELAP, fsz=28, rot=-4, tg=tg)
        if int(tg * 2.5) % 3 == 0:
            _petir47(img, _zig(bx + 10, py0 + 10, bx, by - 60, int(tg * 2.5), n=5, amp=14), al * 0.9, width=5, glow=False)
    tg_ = tl - _t(N, "guinness", dur)
    if tg_ > 0:
        _stiker11(img, 790, 930 + dy, "GUINNESS WORLD RECORDS", al, tg_, bg=accent, fsz=22, rot=3, tg=tg)
    # kalender 365 hari
    tt = tl - _t(N, "terbanyak", dur)
    if tt > 0:
        a = al * clamp(tt / 0.3)
        cx0, cy0 = 125, 1040 + dy
        cols, pitch = 25, 33.2
        rrect_on(img, 110, 1020 + dy, 970, 1540 + dy, 28, WHITE, a, outline=mix(INK, CREAM, 0.7), width=2)
        paste_c(img, 540, 1050 + dy, "1 tahun = 365 hari", font(FB, 24), INK, a)
        th = _t(N, "hitung", dur)
        fill = esmooth(seg(tl, th, th + 2.2))
        rng = random.Random(322)
        petir = set(rng.sample(range(365), 322))
        order = sorted(petir)
        nlit = int(round(322 * fill))
        lit = set(order[:nlit])
        for i in range(365):
            r, c = divmod(i, cols)
            x = cx0 + 12 + c * pitch
            y = cy0 + 50 + r * pitch
            if i in lit:
                rrect_on(img, x, y, x + pitch - 6, y + pitch - 6, 5, KUNING, a)
                if i == order[max(0, nlit - 1)] and fill < 1:
                    _glow11(img, x + 13, y + 13, 30, KUNING, a)
            else:
                rrect_on(img, x, y, x + pitch - 6, y + pitch - 6, 5, mix(CREAM, INK, 0.1), a)
        if tl > th:
            _angka47(img, 400, 1600 + dy, 322, "hari petir / tahun", al, tl, t0=th, dur=2.2,
                     col=mix(AMBER, INK, 0.25), fsz=72)
    tt = tl - _t(N, "hampir", dur)
    if tt > 0:
        _stiker11(img, 790, 1605 + dy, "HAMPIR TIAP HARI!", al, tt, bg=RED, fsz=26, rot=-4, tg=tg)


def sc_panas47(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "panas47"
    _hdr(img, sc, accent, tl, al)
    tsm = _t(N, "sambar", dur)
    q = esmooth(seg(tl, tsm - 0.3, tsm + 0.3))
    if q <= 0.01:
        return
    # panel atas: batang suhu
    rrect_on(img, 110, 700 + dy, 970, 1170 + dy, 30, WHITE, al * q, outline=mix(INK, CREAM, 0.7), width=2)
    th = _t(N, "hitung", dur)
    bx0, bw = 150, 700
    y_p = 820 + dy
    paste_c(img, 300, y_p - 62, "sambaran petir", font(FB, 26), INK, al * q, dy=0)
    fr = esmooth(seg(tl, th, th + 1.2))
    rrect_on(img, bx0, y_p - 30, bx0 + bw, y_p + 30, 30, mix(CREAM, INK, 0.08), al * q)
    if fr > 0:
        rrect_on(img, bx0, y_p - 30, bx0 + max(60, bw * fr), y_p + 30, 30, mix(KUNING, RED, 0.25), al)
        _glow11(img, bx0 + bw * fr, y_p, 60, KUNING, al * 0.7)
    if tl > th:
        _angka47(img, 700, 940 + dy, 30000, "derajat Celsius", al, tl, t0=th, dur=1.2,
                 col=mix(RED, INK, 0.1), fsz=72)
    tm = tl - _t(N, "matahari", dur)
    tl5 = tl - _t(N, "lima", dur)
    if tl5 > 0:
        y_s = 1085 + dy
        a = al * clamp(tl5 / 0.3)
        paste_c(img, 300, y_s - 58, "permukaan matahari", font(FB, 24), INK, a)
        ws = bw * 5500 / 30000.0 * esmooth(clamp(tl5 / 0.6))
        rrect_on(img, bx0, y_s - 24, bx0 + max(48, ws), y_s + 24, 24, AMBER, a)
        _label11(img, bx0 + ws + 110, y_s, "5.500 derajat", MUTED, a, fsz=22, name=FB)
        dot_on(img, 900, y_s - 16, 34, KUNING, a)
        _glow11(img, 900, y_s - 16, 70, KUNING, a * 0.5)
    if tm > 0:
        _stiker11(img, 330, 900 + dy, "5X LEBIH PANAS", al, tm, bg=RED, fsz=32, rot=-4, tg=tg)
    # panel bawah: guntur
    tmu = tl - _t(N, "muai", dur)
    if tl > tsm:
        y0, y1 = 1230 + dy, 1640 + dy
        _langit47(img, 110, y0, 970, y1, al * q)
        cxb = 540
        pts = _zig(cxb - 20, y0 + 10, cxb + 10, y1 - 10, 3, n=9, amp=24)
        fl = 0.55 + 0.45 * math.sin(tg * 23) ** 2
        _petir47(img, pts, al * (1.0 if tl < tsm + 0.4 else fl), width=8)
        if tmu > 0:
            for j in range(4):
                u = ((tmu * 0.7) + j * 0.25) % 1.0
                R = 40 + 360 * u
                ring_on(img, cxb, (y0 + y1) / 2, R, mix(UNGU, WHITE, 0.4), 5, al * (1 - u) * 0.9, squash=0.45)
            _label11(img, 540, y0 + 38, "udara memuai mendadak", WHITE, al * clamp(tmu / 0.4), fsz=22, name=FB)
        tgt = tl - _t(N, "guntur", dur)
        if tgt > 0:
            D._stamp_on(img, 780, 1440 + dy, "DUARR!", al, tgt, col=KUNING, fsz=76, rot=-8)
    if tl > tsm and tl < tsm + 0.6:
        _kilat47(img, 110, 700 + dy, 970, 1640 + dy, tl - tsm, al * 0.6)


def sc_turun47(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "turun47"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "awan", dur) - 0.2, _t(N, "awan", dur) + 0.5))
    if q <= 0.01:
        return
    x0, y0, x1, y1 = 110, 700 + dy, 970, 1640 + dy
    _langit47(img, x0, y0, x1, y1, al * q)
    yg = y1 - 110
    rrect_on(img, x0, yg, x1, y1, 30, TANAH, al * q)
    rrect_on(img, x0, yg, x1, yg + 30, 0, TANAH, al * q)
    _pohon47(img, 280, yg + 6, 330, al * q, tg=tg)
    _rumah47(img, 560, yg + 4, 150, al * q)
    _tiang47(img, 820, yg + 4, 230, al * q)
    _awan47(img, 540, 800 + dy, 1.35, al * q, tg=tg)
    tr = _t(N, "rambat", dur)
    tp = _t(N, "puluhan", dur)
    ytip = yg - 260
    main = _zig(520, 860 + dy, 560, ytip, 21, n=14, amp=70)
    f = seg(tl, tr, tp)
    nstep = 14
    fq = math.floor(f * nstep + 1e-6) / nstep + (0.4 / nstep) * clamp(((f * nstep) % 1.0) / 0.3)
    fq = clamp(fq)
    if f > 0:
        path = _potong(main, fq)
        M._pline(img, path, mix(UNGU, WHITE, 0.5), 5, al)
        _glow11(img, path[-1][0], path[-1][1], 40, UNGU, al)
        for (i0, sd) in ((3, 1), (6, 2), (9, 3), (11, 4)):
            if fq * 14 > i0 + 1:
                bxy = main[i0]
                br = _zig(bxy[0], bxy[1], bxy[0] + (110 if sd % 2 else -120), bxy[1] + 130, 40 + sd, n=5, amp=24)
                M._pline(img, _potong(br, clamp((fq * 14 - i0 - 1) / 2)), mix(UNGU, WHITE, 0.3), 3, al * 0.8)
    tt = tl - tr
    if tt > 0:
        _stiker11(img, 800, 1000 + dy, "BERTAHAP", al, tt, bg=accent, fsz=28, rot=5, tg=tg)
    tt = tl - _t(N, "raba", dur)
    if tt > 0:
        _label11(img, 290, 1000 + dy, "meraba jalan...", WHITE, al * clamp(tt / 0.4), fsz=26, name=FB)
    tt = tl - tp
    if tt > 0:
        a = al * clamp(tt / 0.4)
        line_on(img, (x0 + 20, ytip), (x1 - 20, ytip), mix(KUNING, WHITE, 0.3), 3, a, dash=12)
        _panah11(img, (930, ytip + 10), (930, yg - 10), a, clamp(tt / 0.4), KUNING, width=5, lengkung=0.0, head=14)
        _label11(img, 700, ytip - 34, "tinggal puluhan meter", KUNING, a, fsz=22, name=FB)
    tt = tl - _t(N, "tentu", dur)
    if tt > 0:
        for j, (cx, cy) in enumerate(((200, yg - 400), (470, yg - 190), (760, yg - 150))):
            _stiker11(img, cx, cy, "?", al, tt - j * 0.12, bg=AMBER, fsz=40, rot=6 - j * 5, tg=tg)


def sc_sambut47(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "sambut47"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.5))
    if q <= 0.01:
        return
    x0, y0, x1, y1 = 110, 700 + dy, 970, 1640 + dy
    tc = _t(N, "cepat", dur)
    _langit47(img, x0, y0, x1, y1, al * q)
    yg = y1 - 110
    rrect_on(img, x0, yg, x1, y1, 30, TANAH, al * q)
    rrect_on(img, x0, yg, x1, yg + 30, 0, TANAH, al * q)
    _awan47(img, 540, 790 + dy, 1.3, al * q, tg=tg)
    tree_x, tree_h = 290, 460
    tree_top = (tree_x, yg + 6 - tree_h * 1.02)
    house_top = (570, yg + 4 - 150 * 0.7 - 150 * 0.45)
    man_top = (820, yg - 60)
    _pohon47(img, tree_x, yg + 6, tree_h, al * q, tg=tg)
    _rumah47(img, 570, yg + 4, 150, al * q)
    _orang11(img, 820, yg - 30, 2.0, (230, 230, 240), al * q)
    tip = (400, tree_top[1] - 150)
    leader = _zig(520, 850 + dy, tip[0], tip[1], 31, n=10, amp=50)
    if tl < tc:
        M._pline(img, leader, mix(UNGU, WHITE, 0.5), 5, al * q * (0.7 + 0.3 * math.sin(tg * 17) ** 2))
        _glow11(img, tip[0], tip[1], 40, UNGU, al * q)
    tk = _t(N, "kirim", dur)
    if tl > tk:
        T = {"pohon": tc - tk, "rumah": (tc - tk) * 1.6, "orang": (tc - tk) * 1.9}
        for j, (nm, (ox, oy)) in enumerate((("pohon", tree_top), ("rumah", house_top), ("orang", man_top))):
            f = clamp((tl - tk) / T[nm])
            if nm != "pohon":
                f = min(f, 0.62) if tl > tc else f
            if tl > tc + 0.6 and nm != "pohon":
                continue
            _percik47(img, ox, oy, tip[0], tip[1], f * (1.0 if nm == "pohon" else 0.9), 50 + j, al)
        if tl < tc + 0.3:
            _label11(img, 700, 1030 + dy, "percikan menyambut ke atas", WHITE, al * clamp((tl - tk) / 0.4), fsz=22, name=FB)
    tt = tl - _t(N, "sambut", dur)
    if tt > 0 and tl < tc:
        for (ox, oy) in (tree_top, house_top, man_top):
            _panah11(img, (ox + 40, oy - 10), (ox + 40, oy - 80), al * 0.8, clamp(tt / 0.4), KUNING, width=4,
                     lengkung=0.0, head=12)
    tt = tl - tc
    if tt > 0:
        full = leader + _zig(tip[0], tip[1], tree_top[0], tree_top[1], 33, n=4, amp=14)[1:]
        a = 1.0 if tt < 0.6 else 0.55 + 0.45 * math.sin(tg * 19) ** 2
        _petir47(img, full, al * a, width=10)
        _kilat47(img, x0, y0, x1, y1, tt, al)
    tt = tl - _t(N, "tinggi", dur)
    if tt > 0:
        a = al * clamp(tt / 0.4)
        line_on(img, (x1 - 60, yg), (x1 - 60, tree_top[1]), KUNING, 4, a)
        line_on(img, (x1 - 76, tree_top[1]), (x1 - 44, tree_top[1]), KUNING, 4, a)
        line_on(img, (tree_x + 80, tree_top[1]), (x1 - 76, tree_top[1]), mix(KUNING, WHITE, 0.4), 2, a, dash=10)
    tt = tl - _t(N, "pohon", dur)
    if tt > 0:
        _stiker11(img, 700, 1180 + dy, "TINGGI & SENDIRIAN", al, tt, bg=GELAP, fsz=26, rot=4, tg=tg)
    tt = tl - _t(N, "menang", dur)
    if tt > 0:
        _stiker11(img, 540, 1450 + dy, "YANG TERTINGGI MENANG", al, tt, bg=accent, fsz=32, rot=-3, tg=tg)


def sc_getah47(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "getah47"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.5))
    if q <= 0.01:
        return
    # penampang batang (potongan memanjang)
    x0, x1, y0, y1 = 150, 530, 720 + dy, 1620 + dy
    bark, sap = 34, 70
    tl_ = _t(N, "ledak", dur)
    lk = esmooth(seg(tl, tl_, tl_ + 0.6))
    for side in (-1, 1):
        bx0 = x0 if side < 0 else x1 - bark
        off = side * 160 * eob(lk, 1.2) if lk > 0 else 0
        if lk < 0.98:
            rrect_on(img, bx0 + off, y0, bx0 + bark + off, y1, 10, (96, 64, 42), al * q * (1 - 0.8 * lk))
            for j in range(8):
                yy = y0 + 40 + j * 110
                line_on(img, (bx0 + 8 + off, yy), (bx0 + bark - 8 + off, yy + 30), (70, 46, 30), 3, al * q * (1 - lk))
    rrect_on(img, x0 + bark, y0, x0 + bark + sap, y1, 0, mix(KAYU_M, AIR, 0.3), al * q)
    rrect_on(img, x1 - bark - sap, y0, x1 - bark, y1, 0, mix(KAYU_M, AIR, 0.3), al * q)
    rrect_on(img, x0 + bark + sap, y0, x1 - bark - sap, y1, 0, mix(KAYU_M, KAYU, 0.45), al * q)
    for j in range(5):
        xx = x0 + bark + sap + 25 + j * 36
        line_on(img, (xx, y0 + 10), (xx + 6, y1 - 10), mix(KAYU, INK, 0.2), 2, al * q * 0.5)
    ta = _t(N, "air", dur)
    td = _t(N, "didih", dur)
    didih = esmooth(seg(tl, td, td + 0.8))
    for side in (0, 1):
        lx0 = x0 + bark if side == 0 else x1 - bark - sap
        for j in range(12):
            u = (j * 0.29 + tg * 0.15) % 1.0
            x = lx0 + 14 + (sap - 28) * ((j * 0.53) % 1.0)
            y = y0 + 20 + (y1 - y0 - 40) * u
            r = 6 + 10 * didih * (0.5 + 0.5 * math.sin(tg * 6 + j))
            if tl > ta:
                if didih > 0.05:
                    ring_on(img, x, y, r, WHITE, 3, al * clamp((tl - ta) / 0.4))
                else:
                    dot_on(img, x, y, 6, AIR, al * clamp((tl - ta) / 0.4))
    tar = _t(N, "arus", dur)
    if tl > tar and tl < tl_ + 0.8:
        for side in (0, 1):
            lx = x0 + bark + sap / 2 if side == 0 else x1 - bark - sap / 2
            for j in range(5):
                u = ((tl - tar) * 0.9 + j / 5) % 1.0
                y = y0 + (y1 - y0) * u
                pts = _zig(lx, y - 40, lx, y + 40, j + side * 7, n=4, amp=10)
                M._pline(img, pts, KUNING, 6, al * 0.95)
                _glow11(img, lx, y, 34, KUNING, al * 0.6)
        pts = _zig(x0 + bark + sap / 2, 690 + dy, x0 + bark + sap / 2, y0 + 20, 3, n=3, amp=8)
        _petir47(img, pts, al * clamp((tl - tar) / 0.2), width=7, glow=False)
    tu = tl - _t(N, "uap", dur)
    if tu > 0:
        for j in range(7):
            u = ((tu * 0.5) + j / 7) % 1.0
            side = -1 if j % 2 else 1
            cx = (x0 + bark + 30) if side < 0 else (x1 - bark - 30)
            dot_on(img, cx + side * 60 * u, y0 + 200 + j * 100 - 120 * u, 22 + 30 * u, (236, 238, 244), al * (1 - u) * 0.9)
    if lk > 0:
        rng = random.Random(12)
        for j in range(14):
            side = -1 if j % 2 else 1
            sx = (x0 + bark / 2) if side < 0 else (x1 - bark / 2)
            sy = y0 + 60 + j * 60
            dd = 280 * eob(lk, 1.1)
            ang = rng.uniform(-0.5, 0.3)
            xx = sx + side * dd * math.cos(ang)
            yy = sy + dd * math.sin(ang) + 200 * lk * lk
            rrect_on(img, xx - 16, yy - 7, xx + 16, yy + 7, 3, (96, 64, 42), al * (1 - 0.7 * lk))
        _partikel11(img, (x0 + x1) / 2, (y0 + y1) / 2, tl - tl_, KUNING, al, n=14, jarak=260, seed=8)
    # label kanan
    lab = [(y0 + 80, "kulit kayu", (96, 64, 42), 0.0), (y0 + 300, "lapisan basah (getah)", AIR, _t(N, "basah", dur)),
           (y0 + 520, "kayu inti", KAYU, _t(N, "basah", dur) + 0.3)]
    for (yy, txt, col, t0) in lab:
        if tl > t0 and lk < 0.5:
            a = al * clamp((tl - t0) / 0.4) * (1 - 2 * lk)
            tx = (x1 - bark / 2) if txt == "kulit kayu" else ((x1 - bark - sap / 2) if "basah" in txt else (x0 + x1) / 2)
            line_on(img, (tx, yy), (620, yy), mix(INK, CREAM, 0.4), 3, a)
            dot_on(img, tx, yy, 7, INK, a)
            _label11(img, 790, yy, txt, mix(col, INK, 0.3), a, fsz=26, name=FB)
    if tl > td:
        a = al * clamp((tl - td) / 0.4)
        rrect_on(img, 600, 1320 + dy, 970, 1670 + dy, 28, WHITE, a, outline=mix(INK, CREAM, 0.7), width=2)
        paste_c(img, 785, 1360 + dy, "air jadi uap", font(FB, 26), INK, a)
        dot_on(img, 680, 1510 + dy, 14, AIR, a)
        _panah11(img, (710, 1510 + dy), (760, 1510 + dy), a, 1.0, INK, width=4, lengkung=0.0, head=12)
        k = esmooth(clamp((tl - td - 0.3) / 1.0))
        dot_on(img, 870, 1510 + dy, 20 + 70 * k, (226, 230, 238), a)
        _label11(img, 785, 1625 + dy, "1.700 kali lebih besar", MUTED, a * k, fsz=22, name=FB)
    tt = tl - tl_
    if tt > 0:
        _stiker11(img, 700, 1160 + dy, "KULIT KAYU MELEDAK", al, tt, bg=RED, fsz=28, rot=-4, tg=tg)


def sc_samping47(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "samping47"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.5))
    if q <= 0.01:
        return
    x0, y0, x1, y1 = 110, 700 + dy, 970, 1150 + dy
    _langit47(img, x0, y0, x1, y1, al * q)
    yg = y1 - 60
    rrect_on(img, x0, yg, x1, y1, 30, TANAH, al * q)
    rrect_on(img, x0, yg, x1, yg + 30, 0, TANAH, al * q)
    _hujan47(img, x0 + 10, y0 + 10, x1 - 10, yg - 10, tg, al * q, n=24)
    tx = 380
    _pohon47(img, tx, yg + 4, 360, al * q, tg=tg)
    _orang11(img, tx + 120, yg - 30, 2.0, (230, 230, 240), al * q)
    ts = _t(N, "sambar", dur)
    tt = tl - ts
    if tt > 0:
        a = 1.0 if tt < 0.5 else 0.5 + 0.5 * math.sin(tg * 21) ** 2
        _petir47(img, _zig(300, y0 + 10, tx, yg - 360, 5, n=7, amp=30), al * a, width=8)
        M._pline(img, _zig(tx, yg - 280, tx, yg, 6, n=6, amp=8), KUNING, 6, al * a)
        _kilat47(img, x0, y0, x1, y1, tt, al)
    tt = tl - _t(N, "lompat", dur)
    if tt > 0:
        pts = _zig(tx + 20, yg - 110, tx + 110, yg - 70, int(tg * 12) % 5 + 60, n=5, amp=18)
        _petir47(img, _potong(pts, clamp(tt / 0.2)), al, width=6, glow=True)
        _label11(img, 760, y0 + 50, "arus melompat ke samping", WHITE, al * clamp(tt / 0.4), fsz=22, name=FB)
    tt = tl - _t(N, "orang", dur)
    if tt > 0:
        D._check5_on(img, tx + 120, yg - 90, 70, "x", al, clamp(tt / 0.35), col=RED)
        _stiker11(img, 780, 880 + dy, "JANGAN!", al, tt, bg=RED, fsz=40, rot=5, tg=tg)
    tj = tl - _t(N, "jangan", dur)
    if tj > 0 and tl < _t(N, "orang", dur):
        _stiker11(img, 780, 880 + dy, "BERTEDUH DI SINI?", al, tj, bg=GELAP, fsz=24, rot=4, tg=tg)
    tt = tl - _t(N, "aman", dur)
    if tt > 0:
        _stiker11(img, 540, 1215 + dy, "TEMPAT AMAN", al, tt, bg=GREEN, fsz=30, rot=-3, tg=tg)
    for (key, cx0, lbl) in (("bangunan", 110, "di dalam bangunan"), ("mobil", 560, "mobil beratap logam")):
        tt = tl - _t(N, key, dur)
        if tt <= 0:
            continue
        k = eob(clamp(tt / 0.4), 1.5)
        a = al * clamp(tt / 0.25)
        rrect_on(img, cx0, 1290 + dy, cx0 + 410, 1640 + dy, 28, WHITE, a, outline=mix(GREEN, WHITE, 0.5), width=3)
        cx = cx0 + 205
        if key == "bangunan":
            _rumah47(img, cx, 1530 + dy, 170 * k, a)
            _orang11(img, cx - 40, 1500 + dy, 1.2, GELAP, a)
        else:
            _mobil47(img, cx, 1540 + dy, 260 * k, a)
            pts = _zig(cx - 20, 1300 + dy, cx, 1400 + dy, 9, n=4, amp=12)
            _petir47(img, pts, a * (0.6 + 0.4 * math.sin(tg * 15) ** 2), width=5, glow=False)
            for j in range(6):
                u = ((tt * 0.8) + j / 6) % 1.0
                side = -1 if j % 2 else 1
                x = cx + side * (40 + 90 * u)
                y = 1410 + dy + 110 * u
                dot_on(img, x, y, 6, KUNING, a * (1 - u * 0.5))
        D._check5_on(img, cx0 + 360, 1335 + dy, 30, "check", a, clamp((tt - 0.2) / 0.3), col=GREEN)
        paste_c(img, cx, 1600 + dy, lbl, font(FB, 24), INK, a)


def sc_mitos47(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "mitos47"
    _hdr(img, sc, accent, tl, al)
    tk = tl - _t(N, "katanya", dur)
    if tk <= 0:
        return
    tg_ = _t(N, "gedung", dur)
    if tl < tg_:
        _stiker11(img, 540, 900 + dy, "TIDAK MENYAMBAR", al, tk, bg=GELAP, fsz=34, rot=-3, tg=tg)
        tt = tl - _t(N, "dua", dur)
        if tt > 0:
            _stiker11(img, 540, 1010 + dy, "DUA KALI?", al, tt, bg=accent, fsz=40, rot=3, tg=tg)
        tt = tl - _t(N, "mitos", dur)
        if tt > 0:
            D._stamp_on(img, 540, 1200 + dy, "MITOS!", al, tt, col=RED, fsz=110, rot=-9)
        return
    q = esmooth(seg(tl, tg_, tg_ + 0.6))
    x0, y0, x1, y1 = 110, 700 + dy, 970, 1640 + dy
    _langit47(img, x0, y0, x1, y1, al * q, atas=(44, 54, 96), bawah=(96, 110, 150))
    for j in range(24):
        rng = random.Random(j)
        dot_on(img, x0 + 30 + rng.random() * 800, y0 + 30 + rng.random() * 300, 2.5, WHITE, al * q * 0.6)
    for j, (bx, bh, bw) in enumerate(((180, 260, 70), (270, 190, 60), (760, 300, 80), (870, 220, 70))):
        rrect_on(img, bx - bw / 2, y1 - 40 - bh, bx + bw / 2, y1 - 40, 4, (30, 36, 56), al * q)
    rrect_on(img, x0, y1 - 60, x1, y1, 30, (26, 30, 46), al * q)
    ax, ay = _gedung47(img, 520, y1 - 50, 760 * (0.85 + 0.15 * eob(q, 1.3)), al * q, tg=tg)
    _stiker11(img, 250, 790 + dy, "MITOS", al * 0.9, tl - tg_, bg=RED, fsz=26, rot=-6, tg=tg)
    _label11(img, 760, 790 + dy, "Empire State, New York", WHITE, al * q, fsz=24, name=FB)
    ts = _t(N, "sambar", dur)
    if tl > ts:
        k = int((tl - ts) / 0.55)
        tt = (tl - ts) - k * 0.55
        if tt < 0.3:
            pts = _zig(ax + (-120 if k % 2 else 140), y0 + 10, ax, ay, 70 + k, n=7, amp=30)
            _petir47(img, pts, al * (1 - tt / 0.3), width=8)
            _kilat47(img, x0, y0, x1, y1, tt, al * 0.6)
    th = _t(N, "hitung", dur)
    if tl > th:
        a = al * clamp((tl - th) / 0.3)
        rrect_on(img, 610, 1290 + dy, 950, 1560 + dy, 26, WHITE, a)
        _angka47(img, 780, 1380 + dy, 20, "", al, tl, t0=th, dur=0.7, col=mix(accent, INK, 0.1), fsz=96)
        paste_c(img, 862, 1360 + dy, "+", font(FB, 60), mix(accent, INK, 0.1), a)
        _label11(img, 780, 1490 + dy, "kali setiap tahun", MUTED, a, fsz=26, name=FB)


def sc_rangkuman47(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "rangkuman47"
    _hdr(img, sc, accent, tl, al)
    items = [("s1", "BENDA TINGGI DISAMBAR DULU", "pohon, tiang, gedung", BLUE),
             ("s2", "GETAH MENDIDIH, POHON MELEDAK", "lima kali panas matahari", AMBER),
             ("s3", "DENGAR GUNTUR? MASUK!", "bangunan atau mobil, bukan pohon", RED)]
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
        _label11(img, 400, 1505 + dy, "yang suka berteduh di bawah pohon", MUTED, al * clamp(tt / 0.3), fsz=24)
        k = eob(clamp(tt / 0.4), 1.8)
        _pohon47(img, 850, 1560 + dy, 230 * k, al, tg=tg)
        if int(tg * 1.5) % 2 == 0:
            _petir47(img, _zig(820, 1250 + dy, 850, 1560 + dy - 230 * k, int(tg * 1.5), n=5, amp=18), al, width=5)


VISUALS47 = {
    "intro_petir47": sc_intro_petir47, "bogor47": sc_bogor47, "panas47": sc_panas47,
    "turun47": sc_turun47, "sambut47": sc_sambut47, "getah47": sc_getah47, "samping47": sc_samping47,
    "mitos47": sc_mitos47, "rangkuman47": sc_rangkuman47,
}
