"""Ep44 GUNUNG PADANG - adegan mesin v11 (diimpor oleh mesin_v11).

Pola sama dengan mesin_v11_ep43: kamus beat bernama `B44[visual] = {nama: (fraksi, suara)}`;
`_t(N, nama, dur)` -> detik muncul. BEATS untuk SFX dibangun dari kamus yang sama.
Fraksi disetel dari posisi kata kunci VO (timeline captions, 23 Sep 2026).
Objek: bukit berteras, prisma kekar kolom, pola retak heksagonal (lava / lumpur),
dinding susun, batu kecapi, kartu jurnal, penampang lapisan umur, alur uji ilmiah.
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

B44 = {
    "intro_padang44": {"bukit": (0.05, "whoosh"), "teras": (0.17, "pop"), "piramida": (0.33, "impact"),
                       "mesir": (0.52, "whoosh"), "tanya": (0.61, "pop"), "batu": (0.86, "riser_end"),
                       "lup": (0.88, "impact")},
    "teras44": {"pin": (0.09, "pop"), "t1": (0.27, "thud"), "t2": (0.29, "thud"), "t3": (0.31, "thud"),
                "t4": (0.33, "thud"), "t5": (0.35, "thud"), "tangga": (0.51, "swish_up"),
                "hitung": (0.54, "tick"), "besar": (0.80, "impact")},
    "kolom44": {"tiang": (0.09, "pop"), "segi5": (0.18, "tick"), "segi6": (0.23, "tick"),
                "pahat": (0.30, "click"), "padahal": (0.36, "impact"), "lava": (0.47, "whoosh"),
                "dingin": (0.53, "swish"), "retak": (0.66, "retak"), "prisma": (0.78, "pop"),
                "lumpur": (0.84, "swish")},
    "susun44": {"leluhur": (0.10, "pop"), "angkat": (0.26, "whoosh"), "tegak": (0.32, "thud"),
                "r1": (0.40, "thud"), "r2": (0.44, "thud"), "r3": (0.48, "thud"), "teras": (0.55, "ding"),
                "batu": (0.64, "swish"), "pukul": (0.72, "kecapi"), "nama": (0.89, "pop")},
    "klaim44": {"jurnal": (0.05, "whoosh"), "klaim": (0.33, "impact"), "bar": (0.58, "riser_end"),
                "angka": (0.62, "boom"), "giza": (0.88, "pop")},
    "dicabut44": {"kertas": (0.04, "swish"), "cabut": (0.23, "impact"), "tanah": (0.33, "whoosh"),
                  "x1": (0.51, "glitch"), "x2": (0.55, "glitch"), "x3": (0.60, "glitch"),
                  "rumah": (0.68, "pop"), "bukan": (0.83, "thud")},
    "umur44": {"lapis": (0.04, "whoosh"), "arang": (0.07, "pop"), "dua": (0.24, "ding"),
               "tim": (0.35, "swish"), "enam": (0.72, "impact"), "jalan": (0.87, "tick")},
    "uji44": {"s1": (0.11, "pop"), "i1": (0.45, "pop"), "i2": (0.48, "pop"), "i3": (0.55, "pop"),
              "s2": (0.60, "zap"), "s3": (0.68, "pop"), "lolos": (0.89, "impact")},
    "rangkuman44": {"s1": (0.07, "pop"), "s2": (0.20, "pop"), "s3": (0.37, "pop"),
                    "luar": (0.74, "ding"), "kirim": (0.83, "impact")},
}
for _k, _v in B44.items():
    M.BEATS[_k] = sorted(_v.values())

BATU = (112, 122, 114)          # andesit abu kehijauan
BATU_T = (84, 92, 88)
BATU_L = (150, 160, 150)
LAVA = (236, 104, 38)
TANAH = (150, 106, 72)
TANAH_T = (118, 82, 56)
RUMPUT = (112, 150, 82)
LANGIT = (214, 228, 222)
PASIR = (214, 176, 112)
UNGU = (91, 74, 140)


def _t(nama, key, dur):
    return B44[nama][key][0] * dur


# ------------------------------------------------------------------ objek Ep44
def _segi(cx, cy, r, n=5, rot=-90.0, sy=1.0):
    return [(cx + r * math.cos(math.radians(rot + i * 360.0 / n)),
             cy + r * sy * math.sin(math.radians(rot + i * 360.0 / n))) for i in range(n)]


def _prisma_tegak(img, x, base, w, h, alpha, col=BATU, n=5):
    """Tiang kekar kolom berdiri: 3 muka bergradasi + tutup atas segi-n pipih."""
    if alpha <= 0.01 or h <= 2:
        return
    rrect_on(img, x - w / 2, base - h, x + w / 2, base, 4, mix(col, INK, 0.28), alpha)
    rrect_on(img, x - w * 0.22, base - h, x + w * 0.26, base, 3, col, alpha)
    rrect_on(img, x - w * 0.10, base - h, x + w * 0.04, base, 2, mix(col, WHITE, 0.18), alpha * 0.8)
    poly_on(img, _segi(x, base - h, w * 0.56, n, -90, 0.42), mix(col, WHITE, 0.30), alpha,
            outline=mix(col, INK, 0.35), width=2)


def _prisma_rebah(img, x0, y, L, r, alpha, col=BATU, n=5):
    """Tiang rebah (untuk dinding susun): badan horizontal + ujung segi-n menghadap kamera."""
    if alpha <= 0.01:
        return
    rrect_on(img, x0, y - r * 0.86, x0 + L, y + r * 0.86, 4, mix(col, INK, 0.22), alpha)
    rrect_on(img, x0, y - r * 0.86, x0 + L, y - r * 0.25, 3, mix(col, WHITE, 0.12), alpha)
    poly_on(img, _segi(x0, y, r, n, -90), mix(col, WHITE, 0.22), alpha, outline=mix(col, INK, 0.4), width=2)


def _bukit(img, cx, base, w, h, alpha, col=RUMPUT, puncak=0.0):
    """Siluet bukit halus; puncak = lebar dataran atas (untuk teras)."""
    pts = []
    for i in range(41):
        u = i / 40.0
        x = cx - w / 2 + w * u
        k = abs(u - 0.5) * 2
        k2 = max(0.0, (k - puncak) / max(0.01, 1 - puncak))
        y = base - h * (0.5 + 0.5 * math.cos(math.pi * k2))
        pts.append((x, y))
    pts += [(cx + w / 2, base + 4), (cx - w / 2, base + 4)]
    poly_on(img, pts, col, alpha)
    poly_on(img, pts[:21] + [(cx, base + 4), (cx - w / 2, base + 4)], mix(col, INK, 0.08), alpha * 0.5)


def _teras(img, cx, top, alpha, prog, s=1.0, col=BATU, tg=0.0, glow_i=-1):
    """5 teras bertingkat (tampak samping) di puncak bukit; prog 0..5 = jumlah teras muncul."""
    for i in range(5):
        q = clamp(prog - i)
        if q <= 0:
            continue
        w = (440 - i * 70) * s
        hh = 34 * s
        x = cx - 80 * s + i * 40 * s
        y = top - i * hh
        yb = y + (1 - eob(q, 1.6)) * 60 * s
        rrect_on(img, x - w / 2, yb - hh, x + w / 2, yb, 6 * s, mix(col, WHITE, 0.08), alpha * q,
                 outline=mix(col, INK, 0.35), width=2)
        for k in range(int(w / (26 * s))):
            xx = x - w / 2 + 14 * s + k * 26 * s
            line_on(img, (xx, yb - hh + 6 * s), (xx, yb - 5 * s), mix(col, INK, 0.25), max(1, int(3 * s)),
                    alpha * q * 0.8)
        if i == glow_i:
            _glow11(img, x, yb - hh / 2, 120 * s, (255, 215, 110), alpha * 0.7)


def _pola_hex(seed, x0, y0, x1, y1, r, jit):
    """Tepi-tepi pola heksagonal (retak pendinginan) dalam kotak, urutan acak tapi tetap."""
    rng = random.Random(seed)
    tepi = []
    dx = r * math.sqrt(3)
    row = 0
    y = y0
    cen = []
    while y < y1 + r:
        x = x0 + (dx / 2 if row % 2 else 0)
        while x < x1 + dx:
            cen.append((x, y))
            x += dx
        y += r * 1.5
        row += 1
    verts = {}

    def v(x, y):
        k = (round(x / 4), round(y / 4))
        if k not in verts:
            verts[k] = (x + rng.uniform(-jit, jit), y + rng.uniform(-jit, jit))
        return verts[k]

    seen = set()
    for (cx, cy) in cen:
        vs = [v(cx + r * math.cos(math.radians(30 + 60 * i)), cy + r * math.sin(math.radians(30 + 60 * i)))
              for i in range(6)]
        for i in range(6):
            a, b = vs[i], vs[(i + 1) % 6]
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            tepi.append((a, b))
    rng.shuffle(tepi)
    return tepi


_HEX_LAVA = _pola_hex(7, 150, 960, 930, 1250, 62, 9)
_HEX_LUMPUR = _pola_hex(11, 0, 0, 250, 170, 34, 10)


def _retak(img, tepi, ox, oy, prog, col, width, alpha, clip=None):
    n = int(len(tepi) * clamp(prog))
    for (a, b) in tepi[:n]:
        p1, p2 = (a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy)
        if clip:
            x0, y0, x1, y1 = clip
            if not (x0 <= p1[0] <= x1 and x0 <= p2[0] <= x1 and y0 <= p1[1] <= y1 and y0 <= p2[1] <= y1):
                continue
        line_on(img, p1, p2, col, width, alpha)


def _kertas(img, cx, cy, w, h, alpha, judul="JURNAL", tahun="2023", col=BLUE):
    """Kartu artikel jurnal: kop berwarna + baris teks abu."""
    if alpha <= 0.01:
        return
    rrect_on(img, cx - w / 2 + 10, cy - h / 2 + 12, cx + w / 2 + 10, cy + h / 2 + 12, 16, mix(INK, CREAM, 0.75), alpha * 0.5)
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 16, WHITE, alpha, outline=mix(INK, CREAM, 0.6), width=3)
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy - h / 2 + 70, 16, col, alpha)
    fj = font(FB, 26)
    paste_c(img, cx - w / 2 + 30 + D.tw(judul, fj) / 2, cy - h / 2 + 36, judul, fj, WHITE, alpha)
    paste_c(img, cx + w / 2 - 60, cy - h / 2 + 36, tahun, font(FB, 26), WHITE, alpha)
    for i in range(6):
        ww = (w - 80) * (0.95 if i % 3 else 0.6)
        rrect_on(img, cx - w / 2 + 40, cy - h / 2 + 100 + i * 34, cx - w / 2 + 40 + ww, cy - h / 2 + 114 + i * 34,
                 7, mix(INK, CREAM, 0.8), alpha)


def _piramida(img, cx, base, s, alpha, col=PASIR):
    poly_on(img, [(cx - 120 * s, base), (cx, base - 110 * s), (cx + 120 * s, base)], col, alpha)
    poly_on(img, [(cx, base - 110 * s), (cx + 120 * s, base), (cx + 10 * s, base)], mix(col, INK, 0.18), alpha)


def _rumah(img, cx, base, s, alpha, col=(196, 90, 70)):
    rrect_on(img, cx - 70 * s, base - 90 * s, cx + 70 * s, base, 4, (240, 226, 200), alpha, outline=mix(INK, CREAM, 0.5), width=2)
    poly_on(img, [(cx - 90 * s, base - 88 * s), (cx, base - 150 * s), (cx + 90 * s, base - 88 * s)], col, alpha)
    rrect_on(img, cx - 18 * s, base - 50 * s, cx + 18 * s, base, 3, mix(col, INK, 0.3), alpha)
    rrect_on(img, cx + 32 * s, base - 70 * s, cx + 56 * s, base - 46 * s, 2, (150, 190, 220), alpha)


def _arang(img, cx, cy, s, alpha):
    poly_on(img, [(cx - 22 * s, cy + 8 * s), (cx - 12 * s, cy - 14 * s), (cx + 10 * s, cy - 16 * s),
                  (cx + 24 * s, cy + 2 * s), (cx + 8 * s, cy + 16 * s)], (40, 36, 34), alpha)
    dot_on(img, cx - 4 * s, cy - 4 * s, 4 * s, (90, 84, 80), alpha)


def _gerabah(img, cx, cy, s, alpha, col=(190, 104, 60)):
    ell(img, cx - 26 * s, cy - 18 * s, cx + 26 * s, cy + 26 * s, fill=col, alpha=alpha)
    rrect_on(img, cx - 14 * s, cy - 30 * s, cx + 14 * s, cy - 14 * s, 4, mix(col, INK, 0.15), alpha)
    line_on(img, (cx - 22 * s, cy + 2 * s), (cx + 22 * s, cy + 2 * s), mix(col, WHITE, 0.4), max(1, int(3 * s)), alpha)


def _kapak(img, cx, cy, s, alpha):
    poly_on(img, [(cx - 20 * s, cy - 26 * s), (cx + 18 * s, cy - 20 * s), (cx + 24 * s, cy + 22 * s),
                  (cx - 14 * s, cy + 28 * s)], (128, 120, 110), alpha, outline=mix(INK, CREAM, 0.4), width=2)
    line_on(img, (cx - 10 * s, cy - 14 * s), (cx + 12 * s, cy + 14 * s), (160, 152, 140), max(1, int(3 * s)), alpha)


def _lup(img, cx, cy, r, alpha, col=GELAP):
    ring_on(img, cx, cy, r, col, 12, alpha)
    line_on(img, (cx + r * 0.7, cy + r * 0.7), (cx + r * 1.45, cy + r * 1.45), col, 22, alpha)


# ------------------------------------------------------------------ adegan
def sc_intro_padang44(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "intro_padang44"
    L = sc.get("lines") or ["GUNUNG PADANG", "PIRAMIDA TERTUA?"]
    _judul11(img, L[0], INK, tl, al, y=450, fsz=66, t0=0.05)
    _judul11(img, L[1], accent, tl, al, y=555, fsz=74, t0=0.30, hl=L[1])
    q = esmooth(seg(tl, _t(N, "bukit", dur), _t(N, "bukit", dur) + 0.7))
    if q <= 0.01:
        return
    base = 1480 + dy
    # langit lembut + matahari
    _glow11(img, 820, 820 + dy, 170, (255, 214, 140), al * q * 0.6)
    _bukit(img, 540, base + (1 - eob(q, 1.3)) * 220, 1180, 360, al * q, RUMPUT, puncak=0.18)
    _bukit(img, 170, base + 40, 520, 170, al * q * 0.8, mix(RUMPUT, INK, 0.12))
    pt = 5 * clamp((tl - _t(N, "teras", dur)) / 0.8)
    _teras(img, 560, base - 358, al, pt, s=1.0, tg=tg)
    # tangga
    if pt > 4.5:
        for k in range(10):
            x = 250 + k * 26
            y = base - 60 - k * 29
            line_on(img, (x, y), (x + 22, y), mix(BATU, INK, 0.3), 5, al * clamp((tl - _t(N, "teras", dur) - 0.8 - k * 0.04) / 0.2))
    tt = tl - _t(N, "piramida", dur)
    if tt > 0:
        _stiker11(img, 330, 820 + dy, "\"PIRAMIDA TERTUA?\"", al, tt, bg=GELAP, fsz=32, rot=-5, tg=tg)
    tt = tl - _t(N, "mesir", dur)
    if tt > 0:
        k = eob(clamp(tt / 0.5), 1.5)
        _piramida(img, 900, 1210 + dy + (1 - k) * 80, 0.9, al * clamp(tt / 0.3))
        _label11(img, 900, 1090 + dy, "Giza, Mesir", MUTED, al * clamp(tt / 0.4), fsz=24, name=FB)
    tt = tl - _t(N, "tanya", dur)
    if tt > 0:
        _stiker11(img, 800, 960 + dy, "LEBIH TUA?", al * (1 - esmooth(seg(tl, _t(N, "lup", dur) - 0.4, _t(N, "lup", dur)))),
                  tt, bg=AMBER, fsz=34, rot=6, tg=tg)
    tt = tl - _t(N, "lup", dur)
    if tt > 0:
        k = eob(clamp(tt / 0.5), 1.6)
        cx, cy = 560, 1080 + dy
        dot_on(img, cx, cy, 150 * k, (238, 240, 234), al)
        for j, (ox, oy) in enumerate(((-60, 10), (0, -20), (60, 14), (-28, 70), (34, 72))):
            poly_on(img, _segi(cx + ox * k, cy + oy * k, 36 * k, 5, -90 + j * 11), mix(BATU, WHITE, 0.15 + 0.06 * j), al,
                    outline=mix(BATU, INK, 0.45), width=3)
        _lup(img, cx, cy, 150 * k, al)
        _stiker11(img, 560, 1330 + dy, "JAWABANNYA DI BATU", al, tt - 0.2, bg=accent, fsz=32, rot=-3, tg=tg)


def sc_teras44(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "teras44"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, 0.1, 0.7))
    if q <= 0.01:
        return
    # kartu lokasi: siluet pulau Jawa sederhana + pin Cianjur
    tt = tl - _t(N, "pin", dur)
    y = 800 + dy
    rrect_on(img, 110, y - 70, 970, y + 70, 34, WHITE, al * q, outline=mix(accent, WHITE, 0.55), width=3)
    jawa = [(180, y + 10), (260, y - 24), (380, y - 30), (520, y - 16), (680, y - 22), (820, y - 6), (900, y + 18),
            (780, y + 30), (600, y + 28), (430, y + 34), (280, y + 34)]
    poly_on(img, jawa, mix(accent, WHITE, 0.45), al * q)
    if tt > 0:
        k = eob(clamp(tt / 0.4), 1.8)
        px, py = 300, y - 4
        dot_on(img, px, py - 30 * k, 18, RED, al)
        poly_on(img, [(px - 12, py - 24 * k), (px + 12, py - 24 * k), (px, py)], RED, al)
        dot_on(img, px, py - 30 * k, 7, WHITE, al)
        _label11(img, 470, y - 38, "Cianjur, Jawa Barat", INK, al * clamp(tt / 0.3), fsz=26, name=FB)
    # bukit + 5 teras
    base = 1520 + dy
    _bukit(img, 560, base, 1000, 340, al * q, RUMPUT, puncak=0.2)
    t1 = _t(N, "t1", dur)
    pt = 0.0
    for i in range(5):
        pt += esmooth(seg(tl, _t(N, f"t{i + 1}", dur), _t(N, f"t{i + 1}", dur) + 0.35))
    gi = int(pt) - 1 if 0 < pt < 5 else -1
    _teras(img, 580, base - 338, al, pt, s=1.0, tg=tg, glow_i=gi)
    for i in range(5):
        qi = esmooth(seg(tl, _t(N, f"t{i + 1}", dur), _t(N, f"t{i + 1}", dur) + 0.3))
        if qi > 0:
            x = 500 + i * 40 + (440 - i * 70) / 2 + 40
            yy = base - 338 - i * 34 - 17
            dot_on(img, x, yy, 17 * qi, accent, al)
            paste_c(img, x, yy, str(i + 1), font(FB, 20), WHITE, al * qi)
    if tl > t1:
        _label11(img, 850, 900 + dy, "5 teras batu", mix(accent, INK, 0.3), al * clamp((tl - t1) / 0.4), fsz=30, name=FB)
    # tangga menggambar diri + hitung 370
    tt = tl - _t(N, "tangga", dur)
    if tt > 0:
        pr = clamp(tt / 2.2)
        n = int(22 * pr)
        for k in range(n):
            x = 150 + k * 16
            yy = base - 10 - k * 15
            line_on(img, (x, yy), (x + 16, yy), mix(BATU, INK, 0.35), 5, al)
            line_on(img, (x + 16, yy), (x + 16, yy - 15), mix(BATU, INK, 0.35), 3, al)
    tt = tl - _t(N, "hitung", dur)
    if tt > 0:
        D._hitung_on(img, 230, 960 + dy, 370, "anak tangga", al, tl, t0=_t(N, "hitung", dur), dur=1.6,
                     col=mix(accent, INK, 0.15), fsz=70)
    tt = tl - _t(N, "besar", dur)
    if tt > 0:
        _stiker11(img, 540, 1610 + dy, "MEGALITIKUM TERBESAR DI ASIA TENGGARA", al, tt, bg=accent, fsz=26, rot=-3, tg=tg)


def sc_kolom44(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "kolom44"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "tiang", dur), _t(N, "tiang", dur) + 0.6))
    if q <= 0.01:
        return
    t_pd = _t(N, "padahal", dur)
    fase1 = 1 - esmooth(seg(tl, t_pd + 0.4, t_pd + 1.0))     # tiang & segi -> pudar ke lava
    if fase1 > 0.01:
        a1 = al * q * fase1
        for i, (x, h, n) in enumerate(((250, 330, 5), (400, 400, 6), (550, 360, 5), (700, 300, 6))):
            k = eob(clamp((tl - _t(N, "tiang", dur) - i * 0.12) / 0.5), 1.6)
            _prisma_tegak(img, x, 1330 + dy, 92, h * k, a1, BATU, n)
        tt5 = tl - _t(N, "segi5", dur)
        tt6 = tl - _t(N, "segi6", dur)
        if tt5 > 0:
            k = eob(clamp(tt5 / 0.4), 1.8)
            poly_on(img, _segi(870, 900 + dy, 70 * k, 5), mix(accent, WHITE, 0.3), a1, outline=accent, width=5)
            _label11(img, 870, 1000 + dy, "segi 5", mix(accent, INK, 0.3), a1 * clamp(tt5 / 0.3), fsz=26, name=FB)
        if tt6 > 0:
            k = eob(clamp(tt6 / 0.4), 1.8)
            poly_on(img, _segi(870, 1130 + dy, 70 * k, 6, -90), mix(accent, WHITE, 0.3), a1, outline=accent, width=5)
            _label11(img, 870, 1230 + dy, "segi 6", mix(accent, INK, 0.3), a1 * clamp(tt6 / 0.3), fsz=26, name=FB)
        tt = tl - _t(N, "pahat", dur)
        if tt > 0:
            _stiker11(img, 420, 1440 + dy, "DIPAHAT MANUSIA?", a1, tt, bg=GELAP, fsz=30, rot=-4, tg=tg)
    tt = tl - t_pd
    if tt > 0:
        _stiker11(img, 540, 800 + dy, "KEKAR KOLOM = ALAMI", al, tt, bg=accent, fsz=32, rot=-3, tg=tg)
    # lava mendingin -> retak heksagonal -> prisma
    tl_lv = _t(N, "lava", dur)
    ql = esmooth(seg(tl, tl_lv, tl_lv + 0.5))
    if ql > 0.01:
        dingin = esmooth(seg(tl, _t(N, "dingin", dur), _t(N, "dingin", dur) + 1.6))
        col = mix(LAVA, BATU, dingin)
        x0, y0, x1, y1 = 150, 960 + dy, 930, 1250 + dy
        rrect_on(img, x0, y0, x1, y1, 26, col, al * ql)
        if dingin < 0.9:
            for k in range(5):
                u = ((tg * 0.25) + k / 5) % 1.0
                _glow11(img, x0 + 90 + k * 170, y0 + 150 + 40 * math.sin(tg * 2 + k), 110, (255, 170, 60),
                        al * ql * (1 - dingin) * 0.6)
        _label11(img, 540, y0 - 34, "lava panas" if dingin < 0.5 else "lava mendingin & menyusut", MUTED, al * ql, fsz=24)
        # panah menyusut (ke dalam)
        if 0.2 < dingin < 1.0 and tl < _t(N, "retak", dur) + 0.6:
            for (ax, ay, bx, by) in ((x0 - 40, (y0 + y1) / 2, x0 + 40, (y0 + y1) / 2),
                                     (x1 + 40, (y0 + y1) / 2, x1 - 40, (y0 + y1) / 2)):
                line_on(img, (ax, ay), (bx, by), RED, 6, al * ql)
        pr = clamp((tl - _t(N, "retak", dur)) / 1.5)
        if pr > 0:
            _retak(img, _HEX_LAVA, 0, dy, pr, mix(INK, BATU, 0.2), 5, al * ql, clip=(x0 + 6, y0 + 6, x1 - 6, y1 - 6))
        tt = tl - _t(N, "prisma", dur)
        if tt > 0:
            for i in range(6):
                k = eob(clamp((tt - i * 0.08) / 0.5), 1.5)
                _prisma_tegak(img, 250 + i * 116, 1420 + dy, 84, 150 * k, al, BATU, 5 + (i % 2))
            _label11(img, 540, 1450 + dy, "retakan tumbuh jadi tiang prisma", INK, al * clamp(tt / 0.4), fsz=24, name=FB)
    tt = tl - _t(N, "lumpur", dur)
    if tt > 0:
        k = eob(clamp(tt / 0.45), 1.6)
        bx, by = 540 - 180, 1530 + dy
        rrect_on(img, bx - 20, by - 20, bx + 420 * k, by + 130, 22, WHITE, al, outline=mix(TANAH, WHITE, 0.4), width=3)
        rrect_on(img, bx, by, bx + 150, by + 110, 12, mix(TANAH, WHITE, 0.25), al * k)
        _retak(img, _HEX_LUMPUR, bx - 30, by - 20, clamp(tt / 0.8), TANAH_T, 3, al * k, clip=(bx + 3, by + 3, bx + 147, by + 107))
        _label11(img, bx + 290, by + 38, "lumpur kering", INK, al * k, fsz=26, name=FB)
        _label11(img, bx + 290, by + 76, "retak serupa", MUTED, al * k, fsz=22)


def sc_susun44(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "susun44"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "leluhur", dur), _t(N, "leluhur", dur) + 0.5))
    if q <= 0.01:
        return
    # orang-orang leluhur (siluet) + tiang diangkat
    ya = 900 + dy
    for i in range(3):
        _orang11(img, 170 + i * 70, ya + 20, 1.5, mix(accent, INK, 0.25), al * q)
    ta = _t(N, "angkat", dur)
    ka = esmooth(seg(tl, ta, ta + 0.9))
    kt = esmooth(seg(tl, _t(N, "tegak", dur), _t(N, "tegak", dur) + 0.5))
    # tiang dipikul dari kiri lalu ditegakkan
    if ka > 0:
        x = 250 + 220 * ka
        if kt < 1:
            _prisma_rebah(img, x - 120, ya - 40 - 30 * math.sin(math.pi * ka), 240, 24, al * (1 - kt), BATU, 5)
        if kt > 0:
            _prisma_tegak(img, 560, ya + 70, 60, 200 * eob(kt, 1.5), al, BATU, 5)
        _label11(img, 790, ya + 110, "dipindahkan & ditegakkan", MUTED, al * ka, fsz=24)
    # dinding teras disusun dari tiang rebah
    wall_y = 1330 + dy
    rows = [("r1", 0), ("r2", 1), ("r3", 2)]
    for kk, r in rows:
        tt = tl - _t(N, kk, dur)
        if tt <= 0:
            continue
        for j in range(6):
            k = eob(clamp((tt - j * 0.06) / 0.35), 1.4)
            if k <= 0:
                continue
            x0 = 150 + j * 128 + (r % 2) * 40 - (1 - k) * 300
            _prisma_rebah(img, x0, wall_y - r * 48 - (1 - k) * 60, 118, 22, al * clamp(k * 2), mix(BATU, WHITE, 0.04 * j), 5)
    tt = tl - _t(N, "teras", dur)
    if tt > 0:
        rrect_on(img, 130, wall_y - 2 * 48 - 44, 950, wall_y - 2 * 48 - 26, 8, RUMPUT, al * clamp(tt / 0.3))
        _label11(img, 540, wall_y + 60, "dinding penahan teras", INK, al * clamp(tt / 0.4), fsz=26, name=FB)
    # batu kecapi: dipukul -> gelombang bunyi + not
    tb = _t(N, "batu", dur)
    qb = esmooth(seg(tl, tb, tb + 0.5))
    if qb > 0:
        bx, by = 400, 1530 + dy
        tp = _t(N, "pukul", dur)
        gt = math.exp(-max(0, tl - tp) * 3) * (tl > tp)
        goy = 4 * gt * math.sin(tg * 60)
        _prisma_rebah(img, bx - 150 + goy, by, 300, 34, al * qb, mix(BATU, INK, 0.05), 5)
        # pemukul (batu kecil) mengayun
        sw = clamp((tl - (tp - 0.35)) / 0.35)
        ang = math.radians(-60 + 60 * eob(sw, 1.2)) if tl < tp + 0.3 else math.radians(-20)
        hx, hy = bx + 230 + 90 * math.sin(ang), by - 70 - 90 * math.cos(ang) + 60
        dot_on(img, hx, hy, 24, mix(BATU, INK, 0.3), al * qb)
        if gt > 0.02:
            for kk2 in range(3):
                ph = ((tl - tp) * 1.4 + kk2 / 3.0) % 1.0
                M._busur11(img, bx, by, 60 + 170 * ph, accent, 6, al * gt * (1 - ph), -70, 70)
            for kk2 in range(3):
                u = ((tl - tp) * 0.7 + kk2 * 0.33) % 1.0
                nx, ny = bx + 260 + kk2 * 70, by - 40 - 180 * u
                a_ = al * min(1.0, gt * 2) * (1 - u)
                dot_on(img, nx, ny, 13, mix(accent, INK, 0.2), a_)
                line_on(img, (nx + 11, ny), (nx + 11, ny - 42), mix(accent, INK, 0.2), 5, a_)
                line_on(img, (nx + 11, ny - 42), (nx + 28, ny - 30), mix(accent, INK, 0.2), 5, a_)
    tt = tl - _t(N, "nama", dur)
    if tt > 0:
        _stiker11(img, 780, 1600 + dy, "BATU KECAPI", al, tt, bg=accent, fsz=32, rot=4, tg=tg)


def sc_klaim44(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "klaim44"
    _hdr(img, sc, accent, tl, al)
    tt = tl - _t(N, "jurnal", dur)
    if tt <= 0:
        return
    k = eob(clamp(tt / 0.5), 1.5)
    _kertas(img, 540, 1000 + dy + (1 - k) * 260, 620, 330, al * clamp(tt / 0.3), "JURNAL INTERNASIONAL", "2023", BLUE)
    tt = tl - _t(N, "klaim", dur)
    if tt > 0:
        _stiker11(img, 560, 1060 + dy, "PIRAMIDA 27.000 TAHUN?", al, tt, bg=accent, fsz=34, rot=-4, tg=tg)
    # garis waktu: batang tahun lalu
    tb = _t(N, "bar", dur)
    qb = esmooth(seg(tl, tb - 0.3, tb + 0.2))
    if qb > 0:
        y1, y2 = 1330 + dy, 1470 + dy
        x0 = 150
        W = 780
        _label11(img, 600, 1225 + dy, "berapa tahun lalu dibangun?", MUTED, al * qb, fsz=24)
        g = esmooth(seg(tl, _t(N, "angka", dur), _t(N, "angka", dur) + 1.8))
        rrect_on(img, x0, y1 - 30, x0 + W, y1 + 30, 30, mix(CREAM, INK, 0.08), al * qb)
        if g > 0:
            rrect_on(img, x0, y1 - 30, x0 + max(60, W * g), y1 + 30, 30, accent, al)
            val = int(round(27000 * g, -2))
            paste_c(img, x0 + max(60, W * g) - 110, y1, f"{val:,}".replace(",", ".") + " th", font(FB, 30), WHITE, al)
            paste_c(img, 220, y1 - 56, "klaim 2023", font(FB, 24), accent, al)
        tg_ = _t(N, "giza", dur)
        qg = esmooth(seg(tl, tg_, tg_ + 0.6))
        if qg > 0:
            rrect_on(img, x0, y2 - 30, x0 + W * 4500 / 27000 * qg + 40, y2 + 30, 30, PASIR, al)
            _piramida(img, x0 + W * 4500 / 27000 + 110, y2 + 26, 0.42, al * qg)
            paste_c(img, x0 + W * 4500 / 27000 + 300, y2, "Giza  4.500 th", font(FB, 30), INK, al * qg)


def sc_dicabut44(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "dicabut44"
    _hdr(img, sc, accent, tl, al)
    tt = tl - _t(N, "kertas", dur)
    if tt <= 0:
        return
    tc = _t(N, "cabut", dur)
    kecil = esmooth(seg(tl, _t(N, "tanah", dur) - 0.3, _t(N, "tanah", dur) + 0.4))
    cx = 540 - 290 * kecil
    cy = 1000 + dy - 120 * kecil
    s = 1 - 0.45 * kecil
    a = al * clamp(tt / 0.3)
    _kertas(img, cx, cy, 620 * s, 330 * s, a, "JURNAL" if s < 0.8 else "JURNAL INTERNASIONAL", "2023", BLUE)
    if tl > tc:
        line_on(img, (cx - 300 * s, cy + 150 * s), (cx + 300 * s, cy - 150 * s), RED, int(10 * s) + 2,
                a * clamp((tl - tc) / 0.3))
        D._stamp_on(img, cx, cy, "DICABUT 2024", a, tl - tc, col=RED, fsz=int(64 * s), rot=-9)
    # penampang tanah + uji karbon
    tn = _t(N, "tanah", dur)
    qn = esmooth(seg(tl, tn, tn + 0.5))
    if qn > 0:
        x0, x1 = 560, 960
        ytop = 800 + dy
        for i, (c, lbl) in enumerate(((mix(TANAH, WHITE, 0.2), ""), (TANAH, ""), (TANAH_T, "tanah tua"))):
            rrect_on(img, x0, ytop + i * 90, x1, ytop + i * 90 + 90, 10, c, al * qn)
        for kx in range(12):
            dot_on(img, x0 + 20 + (kx * 53) % 380, ytop + 30 + (kx * 37) % 240, 5, mix(TANAH_T, INK, 0.3), al * qn)
        # bor/sampel
        line_on(img, (x1 - 90, ytop - 40), (x1 - 90, ytop + 220 * qn), GELAP, 10, al * qn)
        _label11(img, 760, ytop + 300, "yang diuji: tanah saja", INK, al * qn, fsz=26, name=FB)
        _label11(img, x1 - 90, ytop - 60, "C-14", mix(accent, INK, 0.2), al * qn, fsz=26, name=FB)
    # 3 bukti manusia: tidak ada
    items = [("x1", "arang", _arang), ("x2", "tulang", None), ("x3", "alat", _kapak)]
    for i, (kk, lbl, fn) in enumerate(items):
        ti = tl - _t(N, kk, dur)
        if ti <= 0:
            continue
        x = 250 + i * 290
        y = 1250 + dy
        kx = eob(clamp(ti / 0.35), 1.7)
        rrect_on(img, x - 115, y - 70, x + 115, y + 70, 26, WHITE, al * clamp(ti / 0.2), outline=mix(RED, WHITE, 0.6), width=3)
        if fn:
            fn(img, x - 60, y, 1.3 * kx, al)
        else:
            D._ico5(img, "bone", x - 60, y, 30 * kx, (200, 192, 176), al)
        paste_c(img, x + 42, y, lbl, font(FB, 28), INK, al)
        D._check5_on(img, x - 60, y, 44, "x", al, clamp((ti - 0.15) / 0.3), col=RED)
    # analogi rumah di atas tanah tua
    tr = _t(N, "rumah", dur)
    qr = esmooth(seg(tl, tr, tr + 0.5))
    if qr > 0:
        y = 1490 + dy
        rrect_on(img, 150, y, 930, y + 60, 10, TANAH_T, al * qr)
        rrect_on(img, 150, y - 8, 930, y + 6, 6, RUMPUT, al * qr)
        paste_c(img, 700, y + 32, "tanah 27.000 th", font(FB, 24), WHITE, al * qr)
        _rumah(img, 330, y - 6, 0.85 * eob(qr, 1.6), al * qr)
        _label11(img, 480, y - 40, "rumah baru", INK, al * qr, fsz=24, name=FB)
    tt = tl - _t(N, "bukan", dur)
    if tt > 0:
        _stiker11(img, 720, 1400 + dy, "RUMAH TIDAK IKUT TUA", al, tt, bg=accent, fsz=28, rot=4, tg=tg)


def sc_umur44(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "umur44"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "lapis", dur), _t(N, "lapis", dur) + 0.6))
    if q <= 0.01:
        return
    # penampang: teras di atas, 3 lapisan ke bawah
    x0, x1 = 130, 600
    top = 860 + dy
    _teras(img, 360, top, al * q, 5 * q, s=0.62)
    lap = [(mix(TANAH, WHITE, 0.22), 150), (TANAH, 170), (TANAH_T, 230)]
    y = top + 4
    ys = []
    for i, (c, h) in enumerate(lap):
        rrect_on(img, x0, y, x1, y + h, 8, c, al * q)
        ys.append((y, y + h))
        y += h
    for kx in range(18):
        dot_on(img, x0 + 25 + (kx * 71) % 440, top + 30 + (kx * 53) % 520, 4, mix(TANAH_T, INK, 0.3), al * q * 0.8)
    # penanda 1: arang di bawah dinding teras ~2.000 th (kokoh)
    ta = _t(N, "arang", dur)
    if tl > ta:
        ka = eob(clamp((tl - ta) / 0.4), 1.8)
        _arang(img, 300, ys[0][0] + 50, 1.3 * ka, al)
        _glow11(img, 300, ys[0][0] + 50, 60, (255, 210, 110), al * 0.6 * ka)
    td = _t(N, "dua", dur)
    qd = esmooth(seg(tl, td, td + 0.5))
    if qd > 0:
        yy = ys[0][0] + 50
        line_on(img, (340, yy), (650, yy), GREEN, 5, al * qd)
        rrect_on(img, 650, yy - 58, 970, yy + 58, 24, mix(GREEN, WHITE, 0.88), al * qd, outline=GREEN, width=3)
        paste_c(img, 810, yy - 16, "~2.000 TAHUN", font(FB, 32), mix(GREEN, INK, 0.2), al * qd)
        paste_c(img, 810, yy + 24, "arang di bawah teras", font(FS, 22), MUTED, al * qd)
        D._check5_on(img, 940, yy - 50, 26, "check", al, clamp((tl - td) / 0.4), col=GREEN)
    # penanda 2: tim 2025 ~6.000 SM (masih diteliti, garis putus)
    tm = _t(N, "tim", dur)
    qm = esmooth(seg(tl, tm, tm + 0.5))
    if qm > 0:
        yy = ys[1][0] + 90
        line_on(img, (x0 + 30, yy), (650, yy), AMBER, 5, al * qm, dash=18)
        rrect_on(img, 650, yy - 58, 970, yy + 58, 24, mix(AMBER, WHITE, 0.88), al * qm, outline=AMBER, width=3)
        paste_c(img, 810, yy - 16, "TIM 2025", font(FB, 28), mix(AMBER, INK, 0.35), al * qm)
        te = _t(N, "enam", dur)
        if tl > te:
            D._hitung_on(img, 810, yy + 22, 6000, "", al, tl, t0=te, dur=0.9, col=mix(AMBER, INK, 0.3), fsz=30)
            paste_c(img, 900, yy + 22, "SM", font(FB, 26), mix(AMBER, INK, 0.3), al * clamp((tl - te) / 0.9))
        else:
            paste_c(img, 810, yy + 22, "lapisan lebih tua", font(FS, 22), MUTED, al * qm)
    # penanda 3: 27.000 th dicoret
    if qm > 0:
        yy = ys[2][0] + 150
        a3 = al * esmooth(seg(tl, tm + 0.4, tm + 0.9))
        paste_c(img, 365, yy, "27.000 th", font(FB, 34), CREAM, a3)
        line_on(img, (270, yy + 4), (460, yy - 4), RED, 6, a3)
        _label11(img, 365, yy + 44, "klaim dicabut", (255, 170, 160), a3, fsz=22, name=FB)
    tt = tl - _t(N, "jalan", dur)
    if tt > 0:
        _stiker11(img, 760, 1470 + dy, "MASIH DITELITI", al, tt, bg=accent, fsz=28, rot=-3, tg=tg)
        _lup(img, 760, 1300 + dy, 50, al * clamp(tt / 0.3), mix(accent, INK, 0.2))


def sc_uji44(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "uji44"
    _hdr(img, sc, accent, tl, al)
    langkah = [("s1", "1", "JEJAK MANUSIA", "di lapisan yang sama"),
               ("s2", "2", "UJI UMUR", "arang -> karbon C-14"),
               ("s3", "3", "UJI ULANG", "oleh ilmuwan lain")]
    ys = [860, 1130, 1400]
    for i, (kk, no, a_, b_) in enumerate(langkah):
        tt = tl - _t(N, kk, dur)
        if tt <= 0:
            continue
        k = eob(clamp(tt / 0.45), 1.6)
        y = ys[i] + dy
        a = al * clamp(tt / 0.2)
        rrect_on(img, 110 + (1 - k) * 400, y - 100, 970 + (1 - k) * 400, y + 100, 34, WHITE, a,
                 outline=mix(accent, WHITE, 0.5), width=3)
        dot_on(img, 190, y, 40 * k, accent, a)
        paste_c(img, 190, y, no, font(FB, 38), WHITE, a)
        paste_c(img, 440, y - 30, a_, font(FB, 34), INK, a)
        paste_c(img, 440, y + 22, b_, font(FS, 24), MUTED, a)
        _partikel11(img, 190, y, tt, accent, al, n=8, jarak=70, seed=i + 3)
        if i > 0:
            _panah11(img, (190, ys[i - 1] + dy + 48), (190, y - 48), al, clamp(tt / 0.4), mix(accent, WHITE, 0.3),
                     width=6, lengkung=0.0, head=18)
    # ikon bukti di kartu 1
    for j, (kk, fn) in enumerate((("i1", _arang), ("i2", _gerabah), ("i3", _kapak))):
        ti = tl - _t(N, kk, dur)
        if ti > 0:
            fn(img, 700 + j * 90, ys[0] + dy, 1.2 * eob(clamp(ti / 0.35), 1.8), al)
    tt = tl - _t(N, "s2", dur)
    if tt > 0:
        yy = ys[1] + dy
        for k in range(3):
            u = ((tg * 0.8) + k / 3) % 1.0
            D.star4(img, 760 + k * 70, yy + 20 - 60 * u, 10, (255, 200, 60), al * clamp(tt / 0.3) * (1 - u))
        rrect_on(img, 730, yy - 40, 900, yy + 40, 16, mix(accent, WHITE, 0.85), al * clamp(tt / 0.3), outline=accent, width=3)
        paste_c(img, 815, yy, "LAB", font(FB, 28), accent, al * clamp(tt / 0.3))
    tt = tl - _t(N, "s3", dur)
    if tt > 0:
        yy = ys[2] + dy + 10
        for j in range(3):
            _orang11(img, 740 + j * 70, yy, 1.4, mix(BLUE, INK, 0.1 * j), al * clamp((tt - j * 0.1) / 0.3))
    tt = tl - _t(N, "lolos", dur)
    if tt > 0:
        D._stamp_on(img, 800, 1560 + dy, "LOLOS = SAH", al, tt, col=GREEN, fsz=46, rot=-6)


def sc_rangkuman44(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "rangkuman44"
    _hdr(img, sc, accent, tl, al)
    items = [("s1", "BENTUK BATU = ALAM", "lava retak jadi prisma", BATU_T),
             ("s2", "SUSUNAN = LELUHUR", "teras & dinding batu", GREEN),
             ("s3", "UMUR = BUKTI", "bukan sensasi", accent)]
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
    tt = tl - _t(N, "luar", dur)
    if tt > 0:
        _teras(img, 800, 1440 + dy, al * clamp(tt / 0.3), 5 * clamp(tt / 0.6), s=0.45)
        _stiker11(img, 800, 1490 + dy, "TETAP LUAR BIASA", al, tt, bg=GREEN, fsz=24, rot=4, tg=tg)
    tt = tl - _t(N, "kirim", dur)
    if tt > 0:
        _stiker11(img, 330, 1420 + dy, "KIRIM KE TEMAN", al, tt, bg=accent, fsz=38, rot=-4, tg=tg)
        _label11(img, 330, 1505 + dy, "yang suka misteri", MUTED, al * clamp(tt / 0.3), fsz=26)


VISUALS44 = {
    "intro_padang44": sc_intro_padang44, "teras44": sc_teras44, "kolom44": sc_kolom44,
    "susun44": sc_susun44, "klaim44": sc_klaim44, "dicabut44": sc_dicabut44, "umur44": sc_umur44,
    "uji44": sc_uji44, "rangkuman44": sc_rangkuman44,
}
