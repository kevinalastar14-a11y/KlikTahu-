"""Mesin v11 - modul visual Ep49 "Kenapa Bintang Berkedip, Tapi Planet Tidak?".

Pola sama dengan mesin_v11_ep43..48: `B49[visual] = {nama: (fraksi, suara)}`; `_t(N, nama, dur)`.
Fraksi disetel dari posisi kata kunci VO (timeline captions, 24 Sep 2026).
Objek (FX 2026): panel langit bergradasi yang MEMOTONG isinya (klip sudut membulat), bintang dengan pendar +
paku difraksi yang berkedip (kedip = jumlah sinus, sinkron per bintang), planet piringan (Jupiter berpita,
Saturnus bercincin depan/belakang), bumi melengkung + selubung atmosfer, kantong udara panas/dingin yang
membelokkan berkas cahaya (lintasan dihitung dari posisi kantong), kolam + koin bergoyang, teropong (titik
melompat), grafik kecerahan (bergerigi vs rata = rata-rata banyak titik), prisma pelangi, observatorium +
laser pemandu 90 km + cermin adaptif berdenyut.
SFX baru: `laser`, `angin` di sfx.py.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw

import diagrams as D
from diagrams import (INK, CREAM, WHITE, MUTED, RED, BLUE, GREEN, AMBER, FB, FS,
                      mix, seg, clamp, esmooth, eob, font, paste_c,
                      rrect_on, line_on, dot_on, ring_on, poly_on, ell)

import mesin_v11 as M
from mesin_v11 import (_stiker11, _label11, _glow11, _panah11, _partikel11, _judul11, _hdr,
                       _orang11, _chip11, GELAP)
from mesin_v11_ep45 import _matahari45, _helm45

B49 = {
    "intro_kedip49": {"langit": (0.10, "swish"), "semua": (0.21, "kilau"), "kedip": (0.28, "tick"),
                      "satu": (0.42, "ding"), "tenang": (0.59, "pop"), "bukan": (0.80, "impact"),
                      "beda": (0.94, "pop")},
    "stabil49": {"fakta": (0.03, "whoosh"), "benar": (0.12, "impact"), "stabil": (0.25, "pop"),
                 "menyala": (0.30, "kilau"), "luar": (0.35, "swish"), "astronot": (0.41, "pop"),
                 "diam": (0.50, "ding"), "udara": (0.69, "angin"), "atmosfer": (0.72, "tick"),
                 "dilewati": (0.82, "whoosh"), "mata": (0.95, "kilau")},
    "udara49": {"diam": (0.16, "angin"), "kantong": (0.20, "pop"), "panas": (0.26, "tick"),
                "dingin": (0.30, "tick"), "angin": (0.45, "angin"), "belok": (0.54, "swish"),
                "beda": (0.65, "tick"), "koin": (0.72, "ding"), "kolam": (0.77, "gelembung"),
                "goyang": (0.85, "swish"), "riak": (0.95, "gelembung")},
    "titik49": {"jauh": (0.14, "whoosh"), "terdekat": (0.19, "ding"), "matahari": (0.25, "pop"),
                "empat": (0.38, "impact"), "tahun": (0.40, "tick"), "km": (0.47, "pop"),
                "titik": (0.58, "click"), "kecil": (0.63, "tick"), "belok": (0.69, "angin"),
                "lompat": (0.79, "glitch"), "redup": (0.84, "tick"), "detik": (0.95, "pop")},
    "piringan49": {"dekat": (0.10, "whoosh"), "piringan": (0.21, "pop"), "bukan": (0.27, "tick"),
                   "banyak": (0.42, "kilau"), "sekaligus": (0.50, "tick"), "kiri": (0.63, "swish"),
                   "kanan": (0.70, "swish"), "tutup": (0.81, "riser"), "tenang": (0.95, "impact")},
    "cakrawala49": {"paling": (0.07, "whoosh"), "cakrawala": (0.19, "pop"), "tebal": (0.40, "thud"),
                    "sirius": (0.53, "kilau"), "merah": (0.65, "pop"), "biru": (0.68, "pop"),
                    "hijau": (0.72, "pop"), "prisma": (0.84, "ding"), "putih": (0.95, "kilau")},
    "laser49": {"musuh": (0.14, "impact"), "raksasa": (0.21, "thud"), "chili": (0.25, "pop"),
                "laser": (0.33, "laser"), "buatan": (0.42, "kilau"), "sembilan": (0.49, "tick"),
                "cermin": (0.59, "whoosh"), "bentuk": (0.71, "glitch"), "seribu": (0.77, "impact"),
                "hapus": (0.88, "kilau")},
    "rangkuman49": {"s1": (0.03, "pop"), "s2": (0.17, "pop"), "s3": (0.33, "pop"),
                    "saturnus": (0.51, "swish_up"), "cari": (0.66, "ding"), "kirim": (0.81, "impact")},
}
for _k, _v in B49.items():
    M.BEATS[_k] = sorted(_v.values())

MALAM_A = (14, 20, 48)
MALAM_B = (40, 46, 96)
SENJA_A = (34, 40, 92)
SENJA_B = (214, 132, 110)
BINTANG = (255, 250, 236)
KUNING = (255, 214, 120)
PLANET = (236, 190, 120)
PLANET_G = (196, 132, 74)
PANAS = (255, 150, 96)
DINGIN = (110, 170, 255)
LASER = (255, 196, 64)
ATMOS = (96, 160, 240)
BUMI = (46, 92, 90)
SIRIUS = [(255, 90, 90), (110, 150, 255), (90, 230, 140), (255, 255, 255)]


def _t(nama, key, dur):
    return B49[nama][key][0] * dur


def _S(v):
    return v * D.SS


# ------------------------------------------------------------------ util panel (klip sudut membulat)
_CACHE = {}


def _mask_rr(w, h, r):
    key = ("m", w, h, r)
    m = _CACHE.get(key)
    if m is None:
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
        _CACHE[key] = m
    return m


def _box(P):
    x0, y0, x1, y1 = P
    return (int(_S(x0)), int(_S(y0)), int(_S(x1)), int(_S(y1)))


def _langit49(img, P, alpha, top=MALAM_A, bot=MALAM_B, r=44):
    """Panel langit bergradasi vertikal (ter-cache) + kembalikan penanda klip."""
    b = _box(P)
    w, h = b[2] - b[0], b[3] - b[1]
    if w < 4 or h < 4 or alpha <= 0.01:
        return None
    rr = int(_S(r))
    key = ("g", w, h, top, bot)
    g = _CACHE.get(key)
    if g is None:
        v = np.linspace(0, 1, h, dtype=np.float32)[:, None, None] ** 1.3
        arr = np.array(top, np.float32)[None, None] * (1 - v) + np.array(bot, np.float32)[None, None] * v
        g = Image.fromarray(np.repeat(arr, w, 1).clip(0, 255).astype(np.uint8), "RGB")
        _CACHE[key] = g
    # area simpan diperluas: isi yang meluber keluar panel (bukit, awan, kantong udara) ikut terpotong
    mg = int(_S(170))
    E = (max(0, b[0] - mg), max(0, b[1] - mg), min(img.width, b[2] + mg), min(img.height, b[3] + mg))
    keep = img.crop(E)
    m = _mask_rr(w, h, rr)
    if alpha < 0.995:
        m = m.point(lambda x: int(x * alpha))
    img.paste(g, b[:2], m)
    return (E, keep, (b[0] - E[0], b[1] - E[1], w, h, rr), alpha)


def _klip(img, k):
    """Pulihkan area di luar sudut membulat -> semua isi panel terpotong rapi di dalam panel.
    Isi yang digambar dengan alpha panel ikut memudar karena latar asli dikembalikan sebagian."""
    if not k:
        return
    b, keep, geo, alpha = k
    key = ("inv", keep.size, geo)
    inv = _CACHE.get(key)
    if inv is None:
        ox, oy, w, h, rr = geo
        inv = Image.new("L", keep.size, 255)
        inv.paste(_mask_rr(w, h, rr).point(lambda x: 255 - x), (ox, oy))
        _CACHE[key] = inv
    img.paste(keep, b[:2], inv)
    if alpha < 0.995:
        cur = img.crop(b)
        img.paste(Image.blend(keep, cur, alpha), b[:2])


def _bintang_acak(seed, n, x0, y0, x1, y1):
    rng = random.Random(seed)
    return [(x0 + (x1 - x0) * rng.random(), y0 + (y1 - y0) * rng.random(), rng.uniform(0.35, 1.0),
             rng.uniform(0, 6.28)) for _ in range(n)]


def kedip(tg, ph, kuat=1.0):
    """Kecerahan bintang berkedip 0..1 (jumlah sinus tak sebanding -> acak alami, ~2-4 Hz)."""
    v = (0.5 * math.sin(tg * 12.7 + ph) + 0.3 * math.sin(tg * 21.3 + ph * 2.1)
         + 0.2 * math.sin(tg * 33.1 + ph * 3.7))
    return clamp(1.0 - kuat * (0.5 - 0.5 * v) * 0.95)


def _bintang49(img, x, y, r, alpha, k=1.0, col=BINTANG, paku=True, glow=True):
    """Bintang: pendar + inti + paku difraksi 4 arah; k = kecerahan sesaat (kedip)."""
    if alpha <= 0.01:
        return
    if glow:
        _glow11(img, x, y, r * (3.2 + 2.2 * k), col, alpha * (0.25 + 0.45 * k))
    if paku and k > 0.25:
        L = r * (1.4 + 2.6 * k)
        for (dx, dy_) in ((1, 0), (0, 1)):
            line_on(img, (x - dx * L, y - dy_ * L), (x + dx * L, y + dy_ * L), col, max(2, int(r * 0.22)),
                    alpha * 0.55 * k)
    dot_on(img, x, y, r * (0.45 + 0.35 * k), mix(col, WHITE, 0.5), alpha * (0.5 + 0.5 * k))


def _latar_bintang(img, pts, alpha, tg, kuat=0.8, rmul=1.0):
    for (x, y, s, ph) in pts:
        k = kedip(tg, ph, kuat)
        if s > 0.8:
            _bintang49(img, x, y, 7 * s * rmul, alpha, k)
        else:
            dot_on(img, x, y, (1.8 + 2.6 * s) * rmul, BINTANG, alpha * (0.25 + 0.7 * k * s))


def _jupiter49(img, cx, cy, r, alpha, tg=0.0):
    """Planet berpita (piringan) + bayangan terminator lembut."""
    if alpha <= 0.01:
        return
    _glow11(img, cx, cy, r * 1.9, mix(PLANET, WHITE, 0.3), alpha * 0.35)
    dot_on(img, cx, cy, r, PLANET, alpha)
    for (v, hh, c) in ((-0.62, 0.10, PLANET_G), (-0.30, 0.13, mix(PLANET_G, WHITE, 0.25)),
                       (0.05, 0.16, PLANET_G), (0.38, 0.11, mix(PLANET_G, WHITE, 0.3)), (0.66, 0.08, PLANET_G)):
        y0, y1 = cy + (v - hh / 2) * r, cy + (v + hh / 2) * r
        yy = min(abs(y0 - cy), abs(y1 - cy))
        if yy >= r:
            continue
        hw = math.sqrt(max(0.0, r * r - yy * yy)) * 0.98
        rrect_on(img, cx - hw, y0, cx + hw, y1, int((y1 - y0) / 2), c, alpha * 0.75)
    ell(img, cx + r * 0.18, cy + r * 0.12, cx + r * 0.46, cy + r * 0.30, fill=(190, 96, 70), alpha=alpha * 0.8)
    dot_on(img, cx - r * 0.35, cy - r * 0.38, r * 0.28, mix(PLANET, WHITE, 0.55), alpha * 0.35)


def _cincin_pts(cx, cy, rx, ry, a0, a1, n=28):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def _saturnus49(img, cx, cy, r, alpha, col=None):
    """Saturnus: cincin belakang -> piringan -> cincin depan (setengah bawah)."""
    if alpha <= 0.01:
        return
    col = col or (238, 206, 140)
    cin = mix(col, WHITE, 0.25)
    rx, ry = r * 2.1, r * 0.55
    w = max(3, int(r * 0.22))
    M._pline(img, _cincin_pts(cx, cy, rx, ry, math.pi, 2 * math.pi), mix(cin, INK, 0.2), w, alpha * 0.9)
    dot_on(img, cx, cy, r, col, alpha)
    rrect_on(img, cx - r * 0.92, cy - r * 0.18, cx + r * 0.92, cy - r * 0.02, int(r * 0.08),
             mix(col, (170, 120, 60), 0.5), alpha * 0.6)
    dot_on(img, cx - r * 0.35, cy - r * 0.4, r * 0.3, mix(col, WHITE, 0.55), alpha * 0.4)
    M._pline(img, _cincin_pts(cx, cy, rx, ry, 0, math.pi), cin, w, alpha)


def _busur(cx, cy, R, x0, x1, n=40):
    out = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        dx = x - cx
        out.append((x, cy - math.sqrt(max(0.0, R * R - dx * dx))))
    return out


def _bumi49(img, P, cx, cy, R, atm, alpha, tebal_atm=0.5):
    """Bumi melengkung (klip oleh panel) + selubung atmosfer biru transparan setebal atm."""
    x0, _, x1, y1 = P
    if atm > 0:
        luar = _busur(cx, cy, R + atm, x0 - 10, x1 + 10)
        dalam = _busur(cx, cy, R, x1 + 10, x0 - 10)
        poly_on(img, luar + dalam, ATMOS, alpha * 0.22 * (0.6 + 0.8 * tebal_atm))
        M._pline(img, luar, mix(ATMOS, WHITE, 0.4), 3, alpha * 0.55)
    top = _busur(cx, cy, R, x0 - 10, x1 + 10)
    poly_on(img, top + [(x1 + 10, y1 + 10), (x0 - 10, y1 + 10)], BUMI, alpha)
    M._pline(img, top, mix(BUMI, WHITE, 0.35), 4, alpha)


def _grafik(img, x0, y0, x1, y1, fn, alpha, col, width=5, n=90, prog=1.0):
    """Garis grafik: fn(u) -> 0..1 (1 = atas). prog = bagian yang sudah tergambar."""
    if alpha <= 0.01 or prog <= 0.005:
        return
    m = max(2, int(n * prog))
    pts = [(x0 + (x1 - x0) * prog * i / m, y1 - (y1 - y0) * clamp(fn(prog * i / m))) for i in range(m + 1)]
    M._pline(img, pts, col, width, alpha)
    dot_on(img, pts[-1][0], pts[-1][1], width * 1.3, col, alpha)


def _orang_lihat(img, cx, cy, s, alpha, col=GELAP):
    """Orang kecil menengadah (kepala condong ke atas)."""
    _orang11(img, cx, cy, s, col, alpha)


def _kubah49(img, cx, yb, s, alpha, buka=0.0):
    """Observatorium: bangunan + kubah + celah terbuka."""
    col = (206, 212, 226)
    rrect_on(img, cx - 90 * s, yb - 70 * s, cx + 90 * s, yb, 6, mix(col, INK, 0.25), alpha)
    ell(img, cx - 96 * s, yb - 170 * s, cx + 96 * s, yb - 0 * s - 26 * s, fill=col, alpha=alpha)
    if buka > 0.01:
        wv = 20 * s * buka
        poly_on(img, [(cx - wv, yb - 168 * s), (cx + wv, yb - 168 * s), (cx + wv * 0.8, yb - 90 * s),
                      (cx - wv * 0.8, yb - 90 * s)], (20, 24, 40), alpha)
    rrect_on(img, cx - 96 * s, yb - 100 * s, cx + 96 * s, yb - 70 * s, 4, mix(col, INK, 0.12), alpha)


def _gunung(img, P, yb, alpha, col=(22, 26, 46), seed=5, h=150):
    x0, _, x1, y1 = P
    rng = random.Random(seed)
    pts = [(x0 - 20, y1 + 10)]
    n = 9
    for i in range(n + 1):
        x = x0 - 20 + (x1 - x0 + 40) * i / n
        pts.append((x, yb - h * (0.35 + 0.65 * rng.random()) * (0.6 + 0.4 * math.sin(i * 1.3))))
    pts.append((x1 + 20, y1 + 10))
    poly_on(img, pts, col, alpha)


# ------------------------------------------------------------------ adegan
def sc_intro_kedip49(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "intro_kedip49"
    L = sc.get("lines") or ["BINTANG BERKEDIP,", "PLANET TIDAK?"]
    _judul11(img, L[0], INK, tl, al, y=455, fsz=68, t0=0.05)
    _judul11(img, L[1], accent, tl, al, y=555, fsz=68, t0=0.30, hl="TIDAK?")
    q = esmooth(seg(tl, _t(N, "langit", dur) - 0.7, _t(N, "langit", dur) + 0.2))
    if q <= 0.01:
        return
    P = (90, 690 + (1 - eob(q, 1.3)) * 120, 990, 1520)
    k = _langit49(img, P, al * q)
    kk = 0.25 + 0.75 * clamp((tl - _t(N, "kedip", dur) + 0.4) / 0.6)
    pts = _bintang_acak(49, 34, 130, P[1] + 40, 950, 1280)
    _latar_bintang(img, pts, al * q, tg, kuat=kk)
    # titik terang tenang (planet) - tumbuh jadi Saturnus saat "bukan"
    ts = tl - _t(N, "satu", dur)
    px, py = 700, 930
    if ts > 0:
        a = al * q * clamp(ts / 0.3)
        tb = tl - _t(N, "bukan", dur)
        g = eob(clamp(tb / 0.6), 1.5) if tb > 0 else 0.0
        if g < 0.99:
            _glow11(img, px, py, 70, KUNING, a * 0.55 * (1 - g))
            dot_on(img, px, py, 11, mix(KUNING, WHITE, 0.4), a * (1 - g))
        if g > 0.01:
            _saturnus49(img, px, py, 18 + 34 * g, a * g)
        if ts < 0.9:
            ring_on(img, px, py, 20 + 90 * ts, mix(KUNING, WHITE, 0.3), 4, a * (1 - ts / 0.9))
        _label11(img, px, py - 80 - 20 * g, "cahayanya tenang", mix(KUNING, WHITE, 0.3), a * clamp((tl - _t(N, "tenang", dur)) / 0.4),
                 fsz=26, name=FB)
    # label bintang berkedip
    tk = tl - _t(N, "kedip", dur)
    if tk > 0:
        bx, by = pts[0][0], pts[0][1]
        for (x, y, s, ph) in pts:
            if s > 0.8 and x < 520:
                bx, by = x, y
                break
        a = al * q * clamp(tk / 0.4)
        ring_on(img, bx, by, 34, WHITE, 3, a * (0.4 + 0.6 * kedip(tg, 1.0)))
        _label11(img, bx + 10, by + 62, "berkedip", WHITE, a, fsz=26, name=FB)
        _partikel11(img, bx, by, tk, WHITE, al, n=8, jarak=70, seed=2)
    # bukit + orang menengadah
    _gunung(img, P, 1500, al * q, col=(18, 22, 40), h=120)
    _orang_lihat(img, 250, 1400, 2.0, al * q, col=(10, 12, 24))
    # grafik mini: bintang bergerigi vs titik tenang
    tt = tl - _t(N, "tenang", dur)
    if tt > 0:
        a = al * q * clamp(tt / 0.4)
        rrect_on(img, 470, 1180, 950, 1330, 26, (255, 255, 255), a * 0.12, outline=mix(WHITE, MALAM_B, 0.5), width=2)
        _label11(img, 560, 1222, "bintang", WHITE, a, fsz=22, name=FB)
        _label11(img, 560, 1290, "titik terang", KUNING, a, fsz=22, name=FB)
        pr = clamp(tt / 0.8)
        _grafik(img, 660, 1196, 920, 1250, lambda u: 0.5 + 0.45 * math.sin(u * 40 + tg * 9) * math.sin(u * 13 + tg * 3),
                a, WHITE, width=4, prog=pr)
        _grafik(img, 660, 1266, 920, 1312, lambda u: 0.55, a, KUNING, width=5, prog=pr)
    tb = tl - _t(N, "bukan", dur)
    if tb > 0:
        D._stamp_on(img, 700, 1080, "BUKAN BINTANG", al, tb, col=RED, fsz=50, rot=-6)
    _klip(img, k)
    tt = tl - _t(N, "beda", dur)
    if tt > 0:
        _stiker11(img, 300, 780, "KENAPA?", al, tt, bg=RED, fsz=44, rot=-6, tg=tg)


def sc_stabil49(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "stabil49"
    _hdr(img, sc, accent, tl, al)
    tf = _t(N, "fakta", dur)
    q = esmooth(seg(tl, tf - 0.3, tf + 0.5))
    if q <= 0.01:
        return
    P = (90, 720 + dy, 990, 1600 + dy)
    k = _langit49(img, P, al * q, top=(8, 12, 30), bot=(26, 30, 70))
    _latar_bintang(img, _bintang_acak(11, 26, 120, P[1] + 30, 960, P[3] - 40), al * q * 0.7, tg, kuat=0.0, rmul=0.8)
    tl_ = _t(N, "luar", dur)
    fb = esmooth(seg(tl, tl_ - 0.2, tl_ + 0.5))       # 0 -> fase A (grafik), 1 -> fase B (bumi)
    # bintang utama: stabil, bergerak ke atas di fase B
    sx = 540
    sy = (930 + dy) * (1 - fb) + (800 + dy) * fb
    r = 30 * (1 - fb) + 20 * fb
    tn = tl - _t(N, "menyala", dur)
    pulse = 0.25 * math.exp(-max(0.0, tn) * 3) if tn > 0 else 0.0
    _bintang49(img, sx, sy, r * (1 + pulse), al * q, 1.0)
    # fase A: grafik kecerahan rata
    if fb < 0.99:
        a = al * q * (1 - fb)
        gx0, gx1, gy0, gy1 = 190, 890, 1190 + dy, 1430 + dy
        line_on(img, (gx0, gy1), (gx1, gy1), mix(WHITE, MALAM_B, 0.4), 3, a)
        line_on(img, (gx0, gy0), (gx0, gy1), mix(WHITE, MALAM_B, 0.4), 3, a)
        _label11(img, gx0 + 90, gy0 - 30, "kecerahan", mix(WHITE, MALAM_B, 0.3), a, fsz=24, name=FB)
        pr = clamp((tl - tf) / 3.0)
        _grafik(img, gx0 + 10, gy0 + 20, gx1, gy1 - 10, lambda u: 0.62, a, KUNING, width=7, prog=pr)
        ts = tl - _t(N, "stabil", dur)
        if ts > 0:
            _chip11(img, 760, gy0 + 20, "STABIL", GREEN, a, ts, fsz=26)
    tb = tl - _t(N, "benar", dur)
    if tb > 0 and fb < 0.5:
        _stiker11(img, 800, 800 + dy, "ILUSI!", al * (1 - fb * 2), tb, bg=RED, fsz=40, rot=6, tg=tg)
    # fase B: bumi + atmosfer, astronot vs orang di tanah
    if fb > 0.01:
        a = al * q * fb
        cy_b = 1470 + dy + 1500
        top_atm = 1470 + dy - 150
        tu = tl - _t(N, "udara", dur)
        _bumi49(img, P, 540, cy_b, 1500, 150, a, tebal_atm=clamp(tu / 0.5) if tu > 0 else 0.0)
        ta = tl - _t(N, "astronot", dur)
        hx, hy = 290, 1110 + dy
        if ta > 0:
            aa = a * clamp(ta / 0.4)
            line_on(img, (sx, sy), (hx + 20, hy - 40), mix(KUNING, WHITE, 0.3), 4, aa)
            _helm45(img, hx, hy + (1 - eob(clamp(ta / 0.5), 1.5)) * 60, 1.0, aa)
            td = tl - _t(N, "diam", dur)
            if td > 0:
                _label11(img, hx, hy + 110, "diam, tanpa kedip", WHITE, a * clamp(td / 0.4), fsz=24, name=FB)
        ox, oy = 740, 1470 + dy - 8
        _orang_lihat(img, ox, oy - 30, 1.8, a, col=(12, 14, 28))
        if tu > 0:
            aa = a * clamp(tu / 0.4)
            pts = [(sx, sy)]
            n = 18
            for i in range(1, n + 1):
                u = i / n
                x = sx + (ox - sx) * u
                y = sy + (oy - 70 - sy) * u
                if y > top_atm:
                    x += 26 * math.sin(tg * 9 + u * 17) * clamp((y - top_atm) / 40)
                pts.append((x, y))
            M._pline(img, pts, mix(KUNING, WHITE, 0.3), 5, aa)
            tat = tl - _t(N, "atmosfer", dur)
            if tat > 0:
                _label11(img, 250, top_atm + 60, "atmosfer", mix(ATMOS, WHITE, 0.5), a * clamp(tat / 0.4), fsz=28, name=FB)
            tdl = tl - _t(N, "dilewati", dur)
            if tdl > 0:
                for j in range(4):
                    u = (tg * 0.8 + j / 4) % 1.0
                    idx = min(len(pts) - 1, int(u * (len(pts) - 1)))
                    dot_on(img, pts[idx][0], pts[idx][1], 8, KUNING, aa)
            tm = tl - _t(N, "mata", dur)
            if tm > 0:
                kx = kedip(tg, 0.4, 1.0)
                D.star4(img, ox + 60, oy - 120, 16 + 20 * kx, WHITE, a * clamp(tm / 0.3) * (0.3 + 0.7 * kx))
    _klip(img, k)
    tm = tl - _t(N, "mata", dur)
    if tm > 0:
        _stiker11(img, 740, 1300 + dy, "ULAH UDARA!", al, tm, bg=accent, fsz=34, rot=-5, tg=tg)


def _kantong(tg, tl, dur, N):
    """Posisi kantong udara (x, y, rx, ry, panas?) - bergeser tertiup angin."""
    ta = _t(N, "angin", dur)
    geser = 0.0 if tl < ta else (tl - ta) * 55 + 18 * (tl - ta) ** 1.2
    out = []
    rng = random.Random(8)
    for i in range(8):
        x = 120 + ((i * 131 + rng.random() * 60 + geser * (0.8 + 0.4 * (i % 3) / 2)) % 860)
        y = 820 + (i % 4) * 78 + rng.uniform(-14, 14)
        out.append((x + 10 * math.sin(tg * 0.9 + i), y, 90 + rng.random() * 50, 34 + rng.random() * 14, i % 2 == 0))
    return out


def _lintasan(x0, y0, y1, kan, n=26, skala=1.0):
    pts = [(x0, y0)]
    x = x0
    dx = 0.0
    for i in range(1, n + 1):
        y = y0 + (y1 - y0) * i / n
        for (kx, ky, rx, ry, panas) in kan:
            g = math.exp(-(((x - kx) / rx) ** 2 + ((y - ky) / ry) ** 2))
            dx += (1.3 if panas else -1.3) * g * skala
        x += dx
        pts.append((x, y))
    return pts


def sc_udara49(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "udara49"
    _hdr(img, sc, accent, tl, al)
    td = _t(N, "diam", dur)
    q = esmooth(seg(tl, td - 0.6, td + 0.2))
    if q <= 0.01:
        return
    P = (90, 700 + dy, 990, 1190 + dy)
    k = _langit49(img, P, al * q, top=(18, 24, 60), bot=(60, 70, 130))
    _bintang49(img, 540, 740 + dy, 14, al * q, kedip(tg, 2.0, 0.9 if tl > _t(N, "belok", dur) else 0.2))
    kan = [(x, y + dy, rx, ry, p) for (x, y, rx, ry, p) in _kantong(tg, tl, dur, N)]
    tk = tl - _t(N, "kantong", dur)
    if tk > 0:
        tp, tdg = tl - _t(N, "panas", dur), tl - _t(N, "dingin", dur)
        for i, (x, y, rx, ry, panas) in enumerate(kan):
            a = al * q * clamp((tk - i * 0.05) / 0.4)
            hl = clamp(tp / 0.3) if panas else clamp(tdg / 0.3)
            col = PANAS if panas else DINGIN
            ell(img, x - rx, y - ry, x + rx, y + ry, fill=col, alpha=a * (0.22 + 0.18 * hl))
            ell(img, x - rx * 0.6, y - ry * 0.55, x + rx * 0.6, y + ry * 0.55, fill=col, alpha=a * (0.15 + 0.15 * hl))
        if tp > 0:
            _label11(img, 240, 880 + dy + 250, "udara panas", mix(PANAS, WHITE, 0.25), al * q * clamp(tp / 0.4), fsz=26, name=FB)
        if tdg > 0:
            _label11(img, 830, 880 + dy + 250, "udara dingin", mix(DINGIN, WHITE, 0.3), al * q * clamp(tdg / 0.4), fsz=26, name=FB)
    ta = tl - _t(N, "angin", dur)
    if ta > 0:
        a = al * q * clamp(ta / 0.4)
        for j in range(7):
            u = (tg * 0.9 + j * 0.37) % 1.0
            x = 100 + 900 * u
            y = 800 + dy + (j * 53) % 300
            line_on(img, (x - 70, y), (x, y), mix(WHITE, MALAM_B, 0.3), 3, a * math.sin(math.pi * u))
    tb = tl - _t(N, "belok", dur)
    if tb > 0:
        a = al * q * clamp(tb / 0.4)
        prog = clamp(tb / 0.8)
        xs = [540] if tl < _t(N, "beda", dur) else [400, 540, 680]
        for j, x0 in enumerate(xs):
            pts = _lintasan(x0, 760 + dy, 1170 + dy, kan)
            m = max(2, int(len(pts) * prog))
            M._pline(img, pts[:m], mix(KUNING, WHITE, 0.2 + 0.2 * j), 5, a)
            # garis lurus bayangan (seharusnya)
            line_on(img, (x0, 760 + dy), (x0, 1170 + dy), mix(WHITE, MALAM_B, 0.5), 2, a * 0.5, dash=14)
    _klip(img, k)
    # kolam + koin
    tk = tl - _t(N, "koin", dur)
    if tk > 0:
        a = al * clamp(tk / 0.4)
        P2 = (90, 1230 + dy, 990, 1620 + dy)
        k2 = _langit49(img, P2, a, top=(236, 244, 250), bot=(206, 226, 240))
        wy = 1320 + dy
        tr = tl - _t(N, "riak", dur)
        amp = 6 + 10 * clamp((tl - _t(N, "goyang", dur)) / 0.5) + 10 * clamp(tr / 0.4)
        pts = [(x, wy + amp * math.sin(x * 0.03 + tg * 5)) for x in range(80, 1011, 20)]
        poly_on(img, pts + [(1010, 1640 + dy), (80, 1640 + dy)], (70, 150, 220), a * 0.75)
        M._pline(img, pts, mix((70, 150, 220), WHITE, 0.5), 5, a)
        cx, cy = 600, 1540 + dy
        ell(img, cx - 60, cy - 16, cx + 60, cy + 16, outline=mix(AMBER, INK, 0.2), width=3, alpha=a * 0.5)
        tg2 = tl - _t(N, "goyang", dur)
        wob = (14 * math.sin(tg * 7) + 8 * math.sin(tg * 11.3)) * clamp(tg2 / 0.4) if tg2 > 0 else 0.0
        ax = cx - 40 + wob
        ell(img, ax - 60, cy - 50 - 16, ax + 60, cy - 50 + 16, fill=(236, 184, 60), outline=mix(AMBER, INK, 0.3),
            width=3, alpha=a)
        ell(img, ax - 30, cy - 50 - 7, ax + 10, cy - 50 + 3, fill=(255, 226, 140), alpha=a * 0.8)
        # mata pengamat + garis pandang terbelok di permukaan
        ex, ey = 210, 1260 + dy
        ell(img, ex - 40, ey - 22, ex + 40, ey + 22, fill=WHITE, outline=INK, width=3, alpha=a)
        dot_on(img, ex + 6, ey + 4, 13, INK, a)
        line_on(img, (ex + 40, ey + 10), (ax - 60, wy + 20), mix(INK, CREAM, 0.4), 3, a, dash=12)
        line_on(img, (ax - 60, wy + 20), (ax, cy - 50), mix(INK, CREAM, 0.4), 3, a, dash=12)
        tp = tl - _t(N, "kolam", dur)
        if tp > 0:
            _label11(img, 860, 1590 + dy, "koin asli", MUTED, a * clamp(tp / 0.4), fsz=22, name=FB)
        if tr > 0:
            for j in range(3):
                u = (tr * 0.8 + j / 3) % 1.0
                ring_on(img, 760, wy, 20 + 120 * u, WHITE, 3, a * (1 - u) * 0.8, squash=0.25)
        _klip(img, k2)
        if tg2 > 0:
            _stiker11(img, 790, 1420 + dy, "TAMPAK BERGOYANG", al, tg2, bg=accent, fsz=26, rot=4, tg=tg)


def sc_titik49(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "titik49"
    _hdr(img, sc, accent, tl, al)
    tj = _t(N, "jauh", dur)
    q = esmooth(seg(tl, tj - 0.6, tj + 0.2))
    if q <= 0.01:
        return
    P = (90, 700 + dy, 990, 1000 + dy)
    k = _langit49(img, P, al * q, top=(10, 14, 36), bot=(24, 28, 64), r=40)
    y = 840 + dy
    tm = tl - _t(N, "matahari", dur)
    _matahari45(img, 180, y, 40, al * q, tg)
    dot_on(img, 262, y, 9, (80, 150, 230), al * q)
    pr = clamp((tl - tj) / 1.0)
    if pr > 0:
        x1 = 262 + (880 - 262) * eob(pr, 1.1)
        line_on(img, (284, y), (x1, y), mix(WHITE, MALAM_B, 0.3), 4, al * q, dash=16)
    tt = tl - _t(N, "terdekat", dur)
    if tt > 0:
        a = al * q * clamp(tt / 0.3)
        _bintang49(img, 890, y, 12, a, kedip(tg, 5.0, 0.3), col=(255, 176, 140))
        _label11(img, 800, y + 70, "bintang terdekat", mix((255, 176, 140), WHITE, 0.3), a, fsz=24, name=FB)
        _partikel11(img, 890, y, tt, (255, 176, 140), al, n=8, jarak=60, seed=1)
    if tm > 0:
        _label11(img, 200, y + 70, "Matahari", KUNING, al * q * clamp(tm / 0.3), fsz=24, name=FB)
        _label11(img, 262, y - 40, "Bumi", mix(WHITE, MALAM_B, 0.2), al * q * clamp(tm / 0.3), fsz=20, name=FB)
    te = _t(N, "empat", dur)
    if tl > te - 0.9:
        a = al * q
        _klip(img, k)
        k = None
        D._hitung_on(img, 540, 1090 + dy, 4.2, "", al, tl, t0=te - 0.9, dur=1.0, col=mix(accent, INK, 0.2), fsz=96)
        ty = tl - _t(N, "tahun", dur)
        if ty > 0:
            _label11(img, 540, 1165 + dy, "tahun cahaya", MUTED, al * clamp(ty / 0.3), fsz=30, name=FB)
        tk = tl - _t(N, "km", dur)
        if tk > 0:
            _stiker11(img, 820, 1080 + dy, "40 TRILIUN KM", al, tk, bg=accent, fsz=26, rot=6, tg=tg)
    _klip(img, k)
    # teropong: satu titik yang melompat
    tt = tl - _t(N, "titik", dur)
    if tt > 0:
        a = al * clamp(tt / 0.4)
        cx, cy, R = 540, 1400 + dy, 180
        k2 = _langit49(img, (cx - R, cy - R, cx + R, cy + R), a, top=(6, 8, 22), bot=(16, 20, 44), r=R)
        tb = tl - _t(N, "belok", dur)
        if tb > 0:
            for j in range(4):
                yy = cy - R + 40 + j * 95
                M._gelom11(img, cx - R, cx + R, yy, 10, 160, tg * 3 + j, mix(ATMOS, WHITE, 0.3), 3,
                           a * 0.35 * clamp(tb / 0.4))
        tlp = tl - _t(N, "lompat", dur)
        jx = jy = 0.0
        if tlp > 0:
            n = int(tg * 12)
            rr = random.Random(n)
            s = clamp(tlp / 0.3)
            jx, jy = rr.uniform(-38, 38) * s, rr.uniform(-38, 38) * s
            rp = random.Random(n - 1)
            dot_on(img, cx + rp.uniform(-38, 38) * s, cy + rp.uniform(-38, 38) * s, 5, WHITE, a * 0.3)
        trd = tl - _t(N, "redup", dur)
        kk = kedip(tg, 0.7, 1.0 * clamp(trd / 0.3)) if trd > 0 else 1.0
        _bintang49(img, cx + jx, cy + jy, 7, a, kk, paku=True)
        _klip(img, k2)
        ring_on(img, cx, cy, R, mix(GELAP, CREAM, 0.2), 14, a)
        tk = tl - _t(N, "kecil", dur)
        if tk > 0:
            _label11(img, 830, 1320 + dy, "satu titik", INK, a * clamp(tk / 0.3), fsz=30, name=FB)
            _panah11(img, (800, 1350 + dy), (600, 1395 + dy), a, clamp(tk / 0.5), accent, width=7, lengkung=0.3)
    td = tl - _t(N, "detik", dur)
    if td > 0:
        _stiker11(img, 260, 1500 + dy, "BERKALI-KALI / DETIK", al, td, bg=RED, fsz=26, rot=-5, tg=tg)


def sc_piringan49(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "piringan49"
    _hdr(img, sc, accent, tl, al)
    td = _t(N, "dekat", dur)
    q = esmooth(seg(tl, td - 0.6, td + 0.3))
    if q <= 0.01:
        return
    P = (90, 700 + dy, 990, 1180 + dy)
    k = _langit49(img, P, al * q, top=(12, 16, 40), bot=(34, 38, 84))
    _latar_bintang(img, _bintang_acak(3, 18, 120, P[1] + 30, 960, P[3] - 30), al * q * 0.6, tg, kuat=0.6, rmul=0.7)
    px, py, R = 680, 940 + dy, 170 * (0.55 + 0.45 * eob(q, 1.4))
    _jupiter49(img, px, py, R, al * q, tg)
    tb = tl - _t(N, "banyak", dur)
    tki, tka = tl - _t(N, "kiri", dur), tl - _t(N, "kanan", dur)
    if tb > 0:
        rng = random.Random(4)
        i = 0
        for gy in range(-4, 5):
            for gx in range(-4, 5):
                x, y = gx * 36 + (gy % 2) * 18, gy * 36
                if x * x + y * y > (R - 18) ** 2:
                    continue
                i += 1
                a = al * q * clamp((tb - i * 0.012) / 0.3)
                ph = rng.uniform(0, 6.28)
                kk = kedip(tg, ph, 0.9) if tl > _t(N, "sekaligus", dur) else 0.9
                ox = 0.0
                if tki > 0 and i % 2 == 0:
                    ox = -10 * math.sin(tg * 8 + ph) * clamp(tki / 0.3)
                if tka > 0 and i % 2 == 1:
                    ox = 10 * math.sin(tg * 8 + ph) * clamp(tka / 0.3)
                dot_on(img, px + x + ox, py + y, 4 + 3 * kk, WHITE, a * (0.35 + 0.55 * kk))
    tp = tl - _t(N, "piringan", dur)
    if tp > 0:
        _label11(img, px, py + R + 32, "piringan", KUNING, al * q * clamp(tp / 0.3), fsz=28, name=FB)
    tbk = tl - _t(N, "bukan", dur)
    if tbk > 0:
        a = al * q * clamp(tbk / 0.3)
        _bintang49(img, 270, py, 10, a, kedip(tg, 3.3, 1.0))
        _label11(img, 270, py + R + 32, "titik", WHITE, a, fsz=28, name=FB)
        _label11(img, 440, py, "vs", mix(WHITE, MALAM_B, 0.4), a, fsz=34, name=FB)
    if tki > 0:
        _panah11(img, (px - 40, py - R - 20), (px - 150, py - R - 20), al * q, clamp(tki / 0.4), DINGIN, width=6, lengkung=0.0, head=18)
    if tka > 0:
        _panah11(img, (px + 40, py - R - 20), (px + 150, py - R - 20), al * q, clamp(tka / 0.4), PANAS, width=6, lengkung=0.0, head=18)
    _klip(img, k)
    # grafik: bintang bergerigi vs planet (banyak garis -> rata-rata datar)
    tt = tl - _t(N, "tutup", dur)
    ts = tl - _t(N, "banyak", dur)
    if ts > 0:
        a = al * clamp(ts / 0.4)
        rrect_on(img, 90, 1220 + dy, 520, 1520 + dy, 30, WHITE, a, outline=mix(INK, CREAM, 0.75), width=2)
        rrect_on(img, 560, 1220 + dy, 990, 1520 + dy, 30, WHITE, a, outline=mix(INK, CREAM, 0.75), width=2)
        _label11(img, 305, 1262 + dy, "bintang: 1 titik", INK, a, fsz=24, name=FB)
        _label11(img, 775, 1262 + dy, "planet: banyak titik", INK, a, fsz=24, name=FB)
        f1 = lambda u: 0.5 + 0.42 * math.sin(u * 37 + tg * 10) * math.sin(u * 11 - tg * 4)
        _grafik(img, 120, 1300 + dy, 490, 1490 + dy, f1, a, mix(accent, INK, 0.2), width=5)
        for j in range(4):
            fj = (lambda j: (lambda u: 0.5 + 0.35 * math.sin(u * (29 + j * 7) + tg * (8 + j) + j * 2)))(j)
            _grafik(img, 590, 1300 + dy, 960, 1490 + dy, fj, a * (0.35 if tt > 0 else 0.6),
                    [DINGIN, PANAS, GREEN, (170, 120, 220)][j], width=3)
        if tt > 0:
            _grafik(img, 590, 1300 + dy, 960, 1490 + dy, lambda u: 0.5, al, mix(accent, INK, 0.1), width=9,
                    prog=clamp(tt / 0.8))
            _label11(img, 775, 1500 + dy - 28, "saling menutupi = rata", MUTED, al * clamp(tt / 0.4), fsz=20, name=FB)
    tn = tl - _t(N, "tenang", dur)
    if tn > 0:
        D._stamp_on(img, 775, 1360 + dy, "TENANG", al, tn, col=GREEN, fsz=50, rot=-7)


def sc_cakrawala49(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "cakrawala49"
    _hdr(img, sc, accent, tl, al)
    tp = _t(N, "paling", dur)
    q = esmooth(seg(tl, tp - 0.5, tp + 0.3))
    if q <= 0.01:
        return
    P = (90, 720 + dy, 990, 1600 + dy)
    k = _langit49(img, P, al * q, top=(10, 14, 38), bot=(44, 48, 104))
    tsi = _t(N, "sirius", dur)
    f2 = esmooth(seg(tl, tsi - 0.5, tsi + 0.1))
    if f2 < 0.99:
        a = al * q * (1 - f2)
        ox, oy = 540, 1480 + dy
        R, atm = 1300, 190
        _bumi49(img, P, 540, oy + R, R, atm, a, tebal_atm=1.0)
        _orang_lihat(img, ox, oy - 34, 1.7, a, col=(12, 14, 28))
        s1 = (540, 800 + dy)
        s2 = (955, 1250 + dy)
        tc = tl - _t(N, "cakrawala", dur)
        _bintang49(img, s1[0], s1[1], 14, a, kedip(tg, 1.1, 0.2))
        _bintang49(img, s2[0], s2[1], 14, a, kedip(tg, 2.7, 1.0 if tl > tp else 0.3))
        tt = tl - _t(N, "tebal", dur)
        for (s, lab, lx, ly, col) in ((s1, "tipis", 610, oy - atm / 2 - 30, (120, 230, 170)),
                                      (s2, "tebal", 800, 1395 + dy, (255, 120, 110))):
            line_on(img, s, (ox, oy - 70), mix(KUNING, WHITE, 0.3), 4, a * 0.9)
            if tt > 0:
                # bagian lintasan di dalam atmosfer disorot
                pts = []
                for i in range(41):
                    u = i / 40
                    x, y = s[0] + (ox - s[0]) * u, s[1] + (oy - 70 - s[1]) * u
                    if math.hypot(x - 540, y - (oy + R)) < R + atm:
                        pts.append((x, y))
                if len(pts) > 1:
                    M._pline(img, pts, col, 10, a * clamp(tt / 0.4))
                _label11(img, lx, ly, lab, col, a * clamp(tt / 0.4), fsz=30, name=FB)
        if tc > 0:
            _label11(img, 820, 1180 + dy, "dekat cakrawala", WHITE, a * clamp(tc / 0.4), fsz=26, name=FB)
            ring_on(img, s2[0], s2[1], 36, WHITE, 3, a * clamp(tc / 0.4) * (0.4 + 0.6 * kedip(tg, 2.7)))
    if f2 > 0.01:
        a = al * q * f2
        _latar_bintang(img, _bintang_acak(21, 20, 120, 760 + dy, 960, 1180 + dy), a * 0.6, tg, kuat=0.7, rmul=0.7)
        # Sirius: warna bergonta-ganti
        n = int(tg * 9)
        c0, c1 = SIRIUS[n % 4], SIRIUS[(n + 1) % 4]
        u = tg * 9 - n
        col = mix(c0, c1, esmooth(u))
        kk = kedip(tg, 0.2, 0.8)
        _bintang49(img, 540, 960 + dy, 34, a, 0.6 + 0.4 * kk, col=col)
        _label11(img, 540, 1080 + dy, "Sirius", WHITE, a, fsz=32, name=FB)
        for (kk_, teks, x, c) in (("merah", "MERAH", 290, SIRIUS[0]), ("biru", "BIRU", 540, SIRIUS[1]),
                                  ("hijau", "HIJAU", 790, SIRIUS[2])):
            tk = tl - _t(N, kk_, dur)
            if tk > 0:
                D._pop_pill(img, x, 1170 + dy, teks, 28, c, a, tk, fg=WHITE if kk_ != "hijau" else INK)
        tr = tl - _t(N, "prisma", dur)
        if tr > 0:
            b = a * clamp(tr / 0.4)
            cx, cy = 540, 1380 + dy
            tri = [(cx, cy - 110), (cx - 100, cy + 70), (cx + 100, cy + 70)]
            line_on(img, (130, cy + 20), (cx - 55, cy - 10), WHITE, 9, b)
            spk = [(150, 80, 200), (70, 90, 220), (60, 160, 230), (70, 190, 90), (250, 220, 60), (250, 150, 50), (230, 60, 50)]
            pr = clamp(tr / 0.6)
            for i, c in enumerate(spk):
                ye = cy - 60 + i * 26
                xe = cx + 50 + (380 - 50) * pr
                line_on(img, (cx + 45, cy - 5 + i * 3), (xe, ye + 40 * pr), c, 8, b)
            poly_on(img, tri, (200, 226, 250), b * 0.55, outline=WHITE, width=4)
            tw = tl - _t(N, "putih", dur)
            if tw > 0:
                _label11(img, 250, cy + 110, "cahaya putih", WHITE, b * clamp(tw / 0.3), fsz=24, name=FB)
                _label11(img, 830, cy + 150, "semua warna", WHITE, b * clamp(tw / 0.3), fsz=24, name=FB)
    _klip(img, k)


def sc_laser49(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "laser49"
    _hdr(img, sc, accent, tl, al)
    tm = _t(N, "musuh", dur)
    q = esmooth(seg(tl, tm - 0.9, tm - 0.1))
    if q <= 0.01:
        return
    P = (90, 700 + dy, 990, 1600 + dy)
    k = _langit49(img, P, al * q, top=(8, 10, 30), bot=(40, 36, 80))
    _latar_bintang(img, _bintang_acak(17, 26, 120, P[1] + 30, 960, 1250 + dy), al * q * 0.6, tg, kuat=0.8, rmul=0.7)
    # bintang target: kabur berbintik -> tajam saat "hapus"
    th = tl - _t(N, "hapus", dur)
    tajam = eob(clamp(th / 0.6), 1.3) if th > 0 else 0.0
    sx, sy = 700, 850 + dy
    n = int(tg * 14)
    rr = random.Random(n)
    for j in range(6):
        ox, oy = rr.uniform(-40, 40) * (1 - tajam), rr.uniform(-40, 40) * (1 - tajam)
        dot_on(img, sx + ox, sy + oy, 6 + 4 * (1 - tajam), WHITE, al * q * (0.25 + 0.3 * rr.random()) * (1 - tajam))
    _glow11(img, sx, sy, 90 * (1 - 0.4 * tajam), (200, 210, 255), al * q * 0.35)
    if tajam > 0:
        _bintang49(img, sx, sy, 16, al * q * tajam, 1.0)
    # gunung + observatorium
    _gunung(img, P, 1570 + dy, al * q, col=(24, 22, 44), seed=9, h=140)
    trk = tl - _t(N, "raksasa", dur)
    kx, kyb = 380, 1540 + dy
    if trk > -0.3:
        up = eob(clamp((trk + 0.3) / 0.6), 1.4)
        poly_on(img, [(kx - 200, 1610 + dy), (kx - 40, kyb - 10), (kx + 40, kyb - 10), (kx + 200, 1610 + dy)],
                (30, 28, 52), al * q)
        _kubah49(img, kx, kyb + (1 - up) * 150, 1.0, al * q * up, buka=clamp((tl - _t(N, "laser", dur) + 0.4) / 0.4))
    # laser pemandu
    tla = tl - _t(N, "laser", dur)
    lx, ly = 470, 800 + dy
    if tla > 0:
        pr = eob(clamp(tla / 0.35), 1.1)
        x0, y0 = kx, kyb - 150
        x1, y1 = x0 + (lx - x0) * pr, y0 + (ly - y0) * pr
        a = al * q * (0.85 + 0.15 * math.sin(tg * 30))
        line_on(img, (x0, y0), (x1, y1), mix(LASER, WHITE, 0.1), 16, a * 0.35)
        line_on(img, (x0, y0), (x1, y1), mix(LASER, WHITE, 0.4), 6, a)
        tb = tl - _t(N, "buatan", dur)
        if tb > 0:
            b = al * q * clamp(tb / 0.3)
            _glow11(img, lx, ly, 70, LASER, b * 0.8)
            dot_on(img, lx, ly, 10, mix(LASER, WHITE, 0.6), b)
            _label11(img, lx - 160, ly - 20, "bintang buatan", mix(LASER, WHITE, 0.4), b, fsz=26, name=FB)
            _partikel11(img, lx, ly, tb, LASER, al, n=10, jarak=80, seed=4)
    ts = tl - _t(N, "sembilan", dur)
    if ts > 0:
        a = al * q * clamp(ts / 0.3)
        line_on(img, (150, kyb - 10), (150, ly), mix(WHITE, MALAM_B, 0.3), 4, a)
        for j in range(6):
            yy = kyb - 10 + (ly - kyb + 10) * j / 5
            line_on(img, (140, yy), (162, yy), mix(WHITE, MALAM_B, 0.3), 3, a)
        D._hitung_on(img, 250, 1080 + dy, 90, "", al * q, tl, t0=_t(N, "sembilan", dur) - 0.3, dur=0.8,
                     col=mix(LASER, WHITE, 0.2), fsz=72)
        _label11(img, 250, 1140 + dy, "km", mix(LASER, WHITE, 0.3), a, fsz=28, name=FB)
    tc = tl - _t(N, "cermin", dur)
    _klip(img, k)
    if tc > 0:
        a = al * clamp(tc / 0.4)
        cx0, cy0, cx1, cy1 = 560, 1040 + dy, 960, 1420 + dy
        rrect_on(img, cx0, cy0, cx1, cy1, 30, WHITE, a * 0.95, outline=mix(INK, CREAM, 0.7), width=2)
        _label11(img, (cx0 + cx1) / 2, cy0 + 38, "cermin lentur", INK, a, fsz=24, name=FB)
        tbn = tl - _t(N, "bentuk", dur)
        amp = 16 * clamp(tbn / 0.3) if tbn > 0 else 3
        pts = []
        for i in range(41):
            u = i / 40
            x = cx0 + 30 + (cx1 - cx0 - 60) * u
            y = cy0 + 150 - 40 * (1 - (2 * u - 1) ** 2) + amp * math.sin(u * 14 + tg * 20) * math.sin(u * 5 - tg * 7)
            pts.append((x, y))
        M._pline(img, pts, (150, 170, 200), 12, a)
        M._pline(img, pts, (230, 240, 255), 4, a)
        for i in range(0, 41, 5):
            x, y = pts[i]
            line_on(img, (x, y + 8), (x, cy0 + 230), mix(INK, CREAM, 0.45), 4, a)
            rrect_on(img, x - 8, cy0 + 222, x + 8, cy0 + 240, 3, mix(accent, INK, 0.2), a)
        t1k = tl - _t(N, "seribu", dur)
        if t1k > -0.8:
            D._hitung_on(img, (cx0 + cx1) / 2, cy0 + 296, 1000, "", al, tl, t0=_t(N, "seribu", dur) - 0.8, dur=0.8,
                         col=mix(accent, INK, 0.25), fsz=52)
        if t1k > 0:
            _label11(img, (cx0 + cx1) / 2, cy0 + 346, "kali per detik", MUTED, a * clamp(t1k / 0.3), fsz=20, name=FB)
    if th > 0:
        _stiker11(img, 790, 760 + dy, "JADI TAJAM!", al, th, bg=GREEN, fsz=30, rot=6, tg=tg)
    tmu = tl - tm
    if tmu > 0 and th < 0:
        D._stamp_on(img, 790, 960 + dy, "MUSUH", al * clamp(1 - (tl - _t(N, "raksasa", dur) - 1.4) / 0.4), tmu,
                    col=RED, fsz=48, rot=-6)
    tch = tl - _t(N, "chili", dur)
    if tch > 0:
        _chip11(img, 390, 1470 + dy, "CHILI - GURUN TINGGI", accent, al, tch, fsz=22)


def sc_rangkuman49(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "rangkuman49"
    _hdr(img, sc, accent, tl, al)
    items = [("s1", "KEDIPAN = ULAH UDARA", "bintangnya sendiri bersinar stabil", DINGIN),
             ("s2", "BINTANG = SATU TITIK", "mudah dibelokkan udara, jadi berkedip", mix(accent, WHITE, 0.2)),
             ("s3", "PLANET = PIRINGAN", "banyak titik saling menutupi, jadi tenang", PLANET_G)]
    for i, (kk, a_, b_, col) in enumerate(items):
        tt = tl - _t(N, kk, dur)
        if tt <= 0:
            continue
        kq = eob(clamp(tt / 0.4), 1.8)
        y = 790 + i * 160 + dy
        a = al * clamp(tt / 0.15)
        rrect_on(img, 110, y - 64, 970, y + 64, 32, mix(WHITE, col, 0.07), a, outline=mix(col, WHITE, 0.45), width=3)
        dot_on(img, 190, y, 42 * kq, col, a)
        if i == 0:
            _bintang49(img, 190, y, 9, a, kedip(tg, 0.3, 0.9), glow=False)
        elif i == 1:
            dot_on(img, 190, y, 7, WHITE, a)
        else:
            dot_on(img, 190, y, 22, PLANET, a)
        paste_c(img, 590, y - 18, a_, font(FB, 32), INK, a, scale=0.85 + 0.15 * kq)
        paste_c(img, 590, y + 26, b_, font(FS, 23), MUTED, a)
        _partikel11(img, 190, y, tt, col, al, n=8, jarak=70, seed=i)
    tsa = tl - _t(N, "saturnus", dur)
    if tsa > 0:
        a = al * clamp(tsa / 0.4)
        P = (110, 1270 + dy, 970, 1540 + dy)
        k = _langit49(img, P, a, top=SENJA_A, bot=SENJA_B, r=32)
        naik = eob(clamp(tsa / 1.6), 1.2)
        sx, sy = 700, 1480 + dy - 150 * naik
        tc = tl - _t(N, "cari", dur)
        _latar_bintang(img, _bintang_acak(31, 10, 140, 1290 + dy, 940, 1420 + dy), a * 0.6, tg, kuat=0.9, rmul=0.7)
        _saturnus49(img, sx, sy, 20, a)
        if tc > 0:
            ring_on(img, sx, sy, 60 + 6 * math.sin(tg * 3), WHITE, 3, a * clamp(tc / 0.3))
            _label11(img, 520, sy + 56, "tidak berkedip", WHITE, a * clamp(tc / 0.4), fsz=24, name=FB)
        _gunung(img, P, 1540 + dy, a, col=(40, 30, 50), seed=12, h=50)
        _label11(img, 700, 1515 + dy, "TIMUR", WHITE, a, fsz=22, name=FB)
        _label11(img, 290, 1310 + dy, "Saturnus, senja", WHITE, a, fsz=24, name=FB)
        _klip(img, k)
    tt = tl - _t(N, "kirim", dur)
    if tt > 0:
        _stiker11(img, 330, 1580 + dy, "KIRIM KE TEMAN", al, tt, bg=accent, fsz=34, rot=-4, tg=tg)


VISUALS49 = {
    "intro_kedip49": sc_intro_kedip49, "stabil49": sc_stabil49, "udara49": sc_udara49,
    "titik49": sc_titik49, "piringan49": sc_piringan49, "cakrawala49": sc_cakrawala49,
    "laser49": sc_laser49, "rangkuman49": sc_rangkuman49,
}
