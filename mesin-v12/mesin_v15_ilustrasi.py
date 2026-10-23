#!/usr/bin/env python3
"""mesin_v15_ilustrasi.py — MESIN ILUSTRASI penuh layar (Ep53+).

Gaya acuan (dari pemilik, 23 Okt 2026): video ilustrasi kartun 9:16 — dunia penuh
layar yang berganti-ganti, objek yang bercerita (perahu, layang-layang, awan,
gunung), angka skala besar, dan gelembung teks pendek.

Yang DIAMBIL dari acuan: komposisi penuh layar, ilustrasi kartun beroutline,
lapisan kedalaman, gerak terus-menerus, angka/skala besar, gelembung teks.
Yang TIDAK diambil: palet biru-cyan acuan. Warna tetap identitas KlikTahu
(krem, navy, terakota, teal, olive) — lihat AGEN.md & LAPORAN_KUALITAS.md.

Selftest:  python3 mesin_v15_ilustrasi.py
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import diagrams as D
from diagrams import (INK, CREAM, WHITE, MUTED, mix, clamp, seg, esmooth, eo,
                      font, tw, tlh, paste_c, rrect_on, line_on, dot_on, ring_on,
                      poly_on, S)

# ------------------------------------------------------------------ palet KlikTahu
KERTAS = (246, 241, 232)
KREM = (252, 246, 235)
LANGIT = (250, 233, 208)
LANGIT_2 = (245, 216, 186)
SENJA = (236, 185, 138)
TEAL = (46, 112, 104)
TEAL_D = (27, 73, 69)
TEAL_L = (126, 182, 168)
PASIR = (229, 202, 165)
PASIR_D = (203, 170, 132)
TERRA = (181, 88, 57)
TERRA_D = (135, 57, 37)
OLIVE = (112, 128, 78)
OLIVE_D = (78, 92, 56)
NAVY = (30, 40, 56)
NAVY_D = (17, 25, 37)
LANGIT_MALAM = (44, 62, 84)

F_HEAD = "Poppins-Bold.ttf"
F_SUB = "Poppins-SemiBold.ttf"

# ------------------------------------------------------------------ utilitas
def L(w, h):
    """Layer RGBA pada skala supersampling."""
    return Image.new("RGBA", (max(1, int(round(S(w)))), max(1, int(round(S(h))))), (0, 0, 0, 0))


def _put(base, lay, x=0, y=0, alpha=1.0):
    a = lay.getchannel("A")
    if alpha < 0.999:
        a = a.point(lambda v: int(v * alpha))
    base.paste(lay.convert("RGB"), (int(round(S(x))), int(round(S(y)))), a)


def grad_v(w, h, stops, seed=1, dither=1.6):
    """Gradasi vertikal multi-stop + dither halus (anti-banding). stops=[(pos,(r,g,b))]."""
    hh, ww = max(2, int(round(S(h)))), max(2, int(round(S(w))))
    ys = np.linspace(0.0, 1.0, hh, dtype=np.float32)
    pos = np.array([s[0] for s in stops], dtype=np.float32)
    cols = np.array([s[1] for s in stops], dtype=np.float32)
    out = np.empty((hh, ww, 3), dtype=np.float32)
    for c in range(3):
        out[:, :, c] = np.interp(ys, pos, cols[:, c])[:, None]
    if dither > 0:
        rng = np.random.default_rng(seed + 7)
        out += rng.normal(0.0, dither, (hh, 1, 1)).astype(np.float32)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def mask_outline(mask, width, color, alpha=1.0):
    """Garis luar dari sebuah mask. Bekerja pada potongan bbox (jauh lebih cepat)."""
    bb = mask.getbbox()
    if not bb:
        return None
    k = max(1, int(round(width)))
    pad = 2 * k + 2
    x0, y0 = max(0, bb[0] - pad), max(0, bb[1] - pad)
    x1, y1 = min(mask.size[0], bb[2] + pad), min(mask.size[1], bb[3] + pad)
    crop = mask.crop((x0, y0, x1, y1))
    dil = crop.filter(ImageFilter.MaxFilter(2 * k + 1))
    edge = Image.fromarray(np.clip(np.asarray(dil, dtype=np.int16) - np.asarray(crop, dtype=np.int16), 0, 255).astype(np.uint8))
    lay = Image.new("RGBA", (x1 - x0, y1 - y0), color + (int(255 * alpha),))
    lay.putalpha(edge)
    return lay, (x0, y0)


def _grad_fill(size, tone, light=0.34, dark=0.20):
    """Isi bentuk: terang di atas -> tone -> gelap di bawah (volume kartun)."""
    w, h = size
    top = mix(tone, WHITE, light)
    mid = tone
    bot = mix(tone, INK, dark)
    return grad_v(w, h, [(0.0, top), (0.52, mid), (1.0, bot)], seed=abs(hash(tone)) % 997, dither=0.8)


def bentuk(img, pts, tone, outline=INK, ow=4.0, alpha=1.0, light=0.22, shadow=0.0, sd=(6, 12)):
    """Polygon kartun: isi bergradasi + outline bersih + bayangan lembut opsional."""
    w, h = img.size
    mx = max(p[0] for p in pts) + 40
    my = max(p[1] for p in pts) + 40
    x0 = min(p[0] for p in pts) - 30
    y0 = min(p[1] for p in pts) - 30
    if shadow > 0:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).polygon([(S(p[0]) + S(sd[0]), S(p[1]) + S(sd[1])) for p in pts],
                                   fill=mix(tone, INK, 0.55) + (int(120 * shadow),))
        sh = sh.filter(ImageFilter.GaussianBlur(S(7)))
        img.paste(sh.convert("RGB"), (0, 0), sh)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(S(p[0]), S(p[1])) for p in pts], fill=255)
    bbox = m.getbbox()
    if not bbox:
        return
    ww, hh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    fill = _grad_fill((ww / max(0.5, S(1)), hh / max(0.5, S(1))), tone, light)
    lay = fill.convert("RGBA")
    msk = m.crop(bbox)
    if alpha < 0.999:
        msk = msk.point(lambda v: int(v * alpha))
    lay.putalpha(msk)
    img.paste(lay.convert("RGB"), (bbox[0], bbox[1]), lay)
    if outline is not None and ow > 0:
        o = mask_outline(m, max(2, int(round(ow * D.SS * 0.5))), outline, 0.92)
        if o:
            oimg, (ox, oy) = o
            img.paste(oimg.convert("RGB"), (ox, oy), oimg)


def elips_vol(img, cx, cy, rx, ry, tone, outline=INK, ow=3.6, light=0.26, alpha=1.0):
    """Elips kartun dengan gradasi + outline (bola/awan/badan)."""
    w, h = img.size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([S(cx - rx), S(cy - ry), S(cx + rx), S(cy + ry)], fill=255)
    bbox = m.getbbox()
    if not bbox:
        return
    ww, hh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    fill = _grad_fill((ww / max(0.5, S(1)), hh / max(0.5, S(1))), tone, light)
    lay = fill.convert("RGBA")
    msk = m.crop(bbox)
    if alpha < 0.999:
        msk = msk.point(lambda v: int(v * alpha))
    lay.putalpha(msk)
    img.paste(lay.convert("RGB"), (bbox[0], bbox[1]), lay)
    if outline is not None and ow > 0:
        o = mask_outline(m, max(2, int(round(ow * D.SS * 0.5))), outline, 0.88)
        if o:
            oimg, (ox, oy) = o
            img.paste(oimg.convert("RGB"), (ox, oy), oimg)


def garis_tebal(img, pts, col, wpx, alpha=1.0, bulge=0.0):
    """Polyline menebal-mengecil (kesan kuas). Murah: hanya garis + 2 ujung bulat."""
    n = len(pts)
    if n < 2:
        return
    for i in range(n - 1):
        t = i / max(1, n - 2)
        ww = wpx * (1.0 - bulge * t)
        line_on(img, pts[i], pts[i + 1], col, ww, alpha)
    dot_on(img, pts[0][0], pts[0][1], wpx * 0.5, col, alpha)
    dot_on(img, pts[-1][0], pts[-1][1], wpx * 0.5 * (1.0 - bulge), col, alpha)


def kurva(p0, p1, p2, n=24):
    """Kurva kuadratik -> daftar titik."""
    out = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        out.append((x, y))
    return out


# ------------------------------------------------------------------ dunia
def langit(img, y0=0, y1=1300, a=None, b=None, seed=3):
    """Panel langit penuh lebar (menutup tepi kanvas = full-bleed)."""
    a = a or LANGIT
    b = b or LANGIT_2
    sky = grad_v(1080, y1 - y0, [(0.0, a), (0.55, mix(a, b, 0.55)), (1.0, b)], seed=seed)
    img.paste(sky, (0, int(round(S(y0)))))


def cahaya_matahari(img, cx, cy, r, al=0.55, hue=None):
    """Pendar lembut + cincin cahaya (bukan gradasi datar)."""
    hue = hue or mix(SENJA, WHITE, 0.35)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(9):
        rr = r * (2.6 - i * 0.19)
        a = int(16 * al * (1 - i / 10.0))
        d.ellipse([S(cx - rr), S(cy - rr), S(cx + rr), S(cy + rr)], fill=hue + (a,))
    lay = lay.filter(ImageFilter.GaussianBlur(S(18)))
    img.paste(lay.convert("RGB"), (0, 0), lay)


def matahari(img, cx, cy, r, t=0.0, warna=None):
    warna = warna or mix(TERRA, AMBER_H, 0.45)
    cahaya_matahari(img, cx, cy, r, 0.7, mix(warna, WHITE, 0.45))
    elips_vol(img, cx, cy, r, r, warna, outline=mix(TERRA_D, INK, 0.35), ow=2.2, light=0.34)
    for i in range(12):                       # berkas berputar pelan
        a = t * 0.22 + i * math.pi / 6
        r0, r1 = r * 1.24, r * 1.52 + 8 * math.sin(t * 1.6 + i)
        line_on(img, (cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
                (cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
                mix(warna, CREAM, 0.35), 5.0, 0.22)


AMBER_H = (232, 168, 92)


def awan_bentuk(cx, cy, w, h, tone, seed=1):
    """Daftar elips pembentuk awan (deterministik)."""
    rng = np.random.default_rng(seed)
    n = 6
    pts = []
    for i in range(n):
        u = (i + 0.5) / n
        x = cx + (u - 0.5) * w * 0.86
        yy = cy - h * 0.16 * math.sin(math.pi * u) + (rng.random() - 0.5) * h * 0.10
        r = h * (0.30 + 0.22 * math.sin(math.pi * u)) * (0.9 + 0.2 * rng.random())
        pts.append((x, yy, r * 1.25, r))
    pts.append((cx, cy + h * 0.10, w * 0.42, h * 0.30))
    return pts


def awan(img, cx, cy, w, h, tone=None, seed=1, outline=INK, ow=3.2, light=0.30, alpha=1.0):
    """Awan kartun: gundukan elips menyatu + isi bergradasi + outline bersih."""
    tone = tone or mix(CREAM, WHITE, 0.45)
    pts = awan_bentuk(cx, cy, w, h, tone, seed)
    w_img, h_img = img.size
    m = Image.new("L", (w_img, h_img), 0)
    dm = ImageDraw.Draw(m)
    for (x, y, rx, ry) in pts:
        dm.ellipse([S(x - rx), S(y - ry), S(x + rx), S(y + ry)], fill=255)
    bbox = m.getbbox()
    if not bbox:
        return
    ww, hh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    fill = _grad_fill((ww / max(0.5, S(1)), hh / max(0.5, S(1))), tone, light)
    lay = fill.convert("RGBA")
    msk = m.crop(bbox)
    if alpha < 0.999:
        msk = msk.point(lambda v: int(v * alpha))
    lay.putalpha(msk)
    img.paste(lay.convert("RGB"), (bbox[0], bbox[1]), lay)
    if outline is not None and ow > 0:
        o = mask_outline(m, max(2, int(round(ow * D.SS * 0.5))), outline, 0.86)
        if o:
            oimg, (ox, oy) = o
            img.paste(oimg.convert("RGB"), (ox, oy), oimg)


def gunung(img, cx, base, w, h, tone, seed=5, salju=False, outline=INK):
    """Gunung bergerigi: dua lereng simetris, tiap lereng ditutup ke garis dasar."""
    rng = np.random.default_rng(seed)
    n = 8
    kiri, kanan = [], []
    for i in range(n + 1):
        u = i / n
        x = cx - w / 2 + w * u
        y = base - h * (1 - abs(u - 0.5) * 2) ** 1.18
        y += (rng.random() - 0.5) * h * 0.030
        if u < 0.5:
            kiri.append((x, y))
        else:
            kanan.append((x, y))
    puncak = (cx, base - h)
    kiri = kiri + [puncak]
    kanan = [puncak] + kanan
    # lereng kiri: dari kaki kiri -> puncak -> garis dasar
    bentuk(img, [(cx - w / 2, base)] + kiri + [(cx, base)], tone, outline=outline, ow=3.0, light=0.14)
    # lereng kanan (lebih gelap = bayangan)
    bentuk(img, kanan + [(cx + w / 2, base), (cx, base)], mix(tone, INK, 0.20),
           outline=outline, ow=3.0, light=0.18)
    if salju:
        hh = h * 0.20
        sk = [(cx - hh * 0.95, base - h + hh * 0.35), (cx + hh * 0.98, base - h + hh * 0.42),
              (cx + hh * 0.52, base - h + hh * 0.95), (cx + hh * 0.16, base - h + hh * 0.62),
              (cx - hh * 0.22, base - h + hh * 0.98), (cx - hh * 0.66, base - h + hh * 0.55)]
        bentuk(img, sk, mix(CREAM, WHITE, 0.72), outline=outline, ow=2.6, light=0.30)


def bukit(img, y, amp, tone, seed=7, n=4, outline=INK):
    rng = np.random.default_rng(seed)
    pts = [(0, 1920)]
    for i in range(n + 1):
        x = 1080 * i / n
        yy = y + math.sin(i * 1.7 + seed) * amp * 0.5 + (rng.random() - 0.5) * amp * 0.3
        pts.append((x, yy))
    pts.append((1080, 1920))
    bentuk(img, pts, tone, outline=outline, ow=2.6, light=0.14)


def laut(img, y0, y1, t=0.0, tone=None, dalam=None, glitter=True):
    """Bidang laut + lapisan ombak + kilau bergerak."""
    tone = tone or TEAL
    dalam = dalam or TEAL_D
    sea = grad_v(1080, y1 - y0, [(0.0, mix(tone, WHITE, 0.30)), (0.45, tone), (1.0, dalam)], seed=11)
    img.paste(sea, (0, int(round(S(y0)))))
    for k in range(3):
        yy = y0 + (y1 - y0) * (0.22 + k * 0.26)
        for i in range(9):
            x = (i * 132 + (t * (16 + k * 9) * (1 if k % 2 == 0 else -1))) % 1200 - 60
            amp = 5 + k * 2
            pts = [(x + j * 4, yy + amp * math.sin(j * 0.5 + t * 1.4 + i)) for j in range(14)]
            garis_tebal(img, pts, mix(CREAM, WHITE, 0.4), 3.2 - k * 0.5, 0.30 - k * 0.06)
    if glitter:
        rng = np.random.default_rng(9)
        for i in range(22):
            x = 40 + rng.random() * 1000
            yy = y0 + 14 + rng.random() * (y1 - y0) * 0.7
            s = 2 + 2 * (0.5 + 0.5 * math.sin(t * 2.0 + i * 1.7))
            dot_on(img, x, yy, s, mix(STARW, CREAM, 0.2), 0.35 + 0.35 * (0.5 + 0.5 * math.sin(t * 1.7 + i)))


STARW = (255, 250, 238)


def pasir(img, y0, tone=None):
    tone = tone or PASIR
    sand = grad_v(1080, 1920 - y0, [(0.0, mix(tone, WHITE, 0.35)), (1.0, mix(tone, TERRA, 0.18))], seed=17)
    img.paste(sand, (0, int(round(S(y0)))))
    rng = np.random.default_rng(4)
    for i in range(90):                        # butir pasir
        x = rng.random() * 1080
        yy = y0 + rng.random() * (1920 - y0)
        dot_on(img, x, yy, 1.6 + rng.random() * 1.6, mix(tone, TERRA_D, 0.35), 0.16)


def pohon_kelapa(img, x, y, s=1.0, t=0.0):
    """Pohon kelapa: batang melengkung beruas + 6 pelepah berdaun (bukan garis)."""
    pts = kurva((x, y), (x + 18 * s, y - 132 * s), (x + 4 * s, y - 244 * s), 16)
    garis_tebal(img, pts, mix(OLIVE_D, INK, 0.28), 17 * s, 1.0, bulge=0.42)
    for i in range(1, 7):                       # ruas batang
        px, py = pts[int(i * 2.4)]
        line_on(img, (px - 7 * s, py - 4 * s), (px + 7 * s, py + 4 * s), mix(OLIVE_D, INK, 0.5), 2.0, 0.35)
    tx, ty = pts[-1]
    for i in range(6):
        a = math.radians(-172 + i * 33) + 0.06 * math.sin(t * 1.1 + i)
        p1 = (tx + 74 * s * math.cos(a), ty + 30 * s * math.sin(a))
        p2 = (tx + 136 * s * math.cos(a * 0.94), ty + 84 * s * math.sin(a * 0.94) + 34 * s)
        spine = kurva((tx, ty), p1, p2, 12)
        # bilah daun: dua sisi menyempit ke ujung
        for sgn in (-1, 1):
            bilah = []
            for k, p in enumerate(spine):
                u = k / (len(spine) - 1)
                wgt = (1 - u) * 16 * s + 2 * s
                off = sgn * wgt
                bilah.append((p[0] - off * math.sin(a), p[1] + off * math.cos(a) * 0.55))
            for k in range(len(spine) - 1, -1, -1):
                u = k / (len(spine) - 1)
                bilah.append((spine[k][0], spine[k][1]))
            bentuk(img, bilah, mix(OLIVE, TEAL, 0.22), ow=2.4, light=0.30)
        garis_tebal(img, spine, mix(OLIVE_D, INK, 0.30), 4.0 * s, 0.75, bulge=0.5)


def perahu(img, x, y, s=1.0, t=0.0):
    """Perahu layar kecil (badan + layar segitiga + tiang)."""
    bob = 3 * math.sin(t * 1.1)
    y = y + bob
    badan = [(x - 62 * s, y), (x + 62 * s, y), (x + 40 * s, y + 30 * s), (x - 42 * s, y + 30 * s)]
    bentuk(img, badan, mix(TERRA, TERRA_D, 0.35), ow=2.6, light=0.26)
    line_on(img, (x, y), (x, y - 94 * s), mix(NAVY, INK, 0.2), 4.0, 0.9)
    layar = [(x + 3 * s, y - 92 * s), (x + 3 * s, y - 16 * s), (x + 58 * s, y - 22 * s)]
    bentuk(img, layar, mix(CREAM, WHITE, 0.55), ow=2.2, light=0.32)
    line_on(img, (x - 2 * s, y - 88 * s), (x - 2 * s, y - 14 * s), mix(TERRA, INK, 0.2), 3.0, 0.55)


def rumah(img, x, y, s=1.0, t=0.0):
    """Rumah panggung sederhana: badan + atap pelana + jendela hangat."""
    bentuk(img, [(x - 46 * s, y), (x + 46 * s, y), (x + 46 * s, y - 62 * s), (x - 46 * s, y - 62 * s)],
           mix(CREAM, WHITE, 0.35), ow=2.4, light=0.20)
    bentuk(img, [(x - 62 * s, y - 60 * s), (x, y - 112 * s), (x + 62 * s, y - 60 * s)],
           mix(TERRA, TERRA_D, 0.30), ow=2.6, light=0.24)
    r = 9 * s
    rrect_on(img, x - 14 * s - r, y - 44 * s, x + 14 * s - r, y - 16 * s, 3 * s, mix(AMBER_H, WHITE, 0.15), 0.9)


def orang(img, x, y, s=1.0, t=0.0, tone=None, hadap=1):
    """Sosok orang kartun (dipakai di pantai): silhouette berwarna, bukan hitam."""
    tone = tone or mix(NAVY, TEAL_D, 0.25)
    elips_vol(img, x, y - 118 * s, 17 * s, 19 * s, tone, outline=mix(tone, INK, 0.4), ow=2.0, light=0.30)
    bentuk(img, [(x - 15 * s, y - 96 * s), (x + 15 * s, y - 96 * s), (x + 20 * s, y - 34 * s), (x - 20 * s, y - 34 * s)],
           tone, ow=2.2, light=0.26)
    garis_tebal(img, [(x - 8 * s, y - 34 * s), (x - 8 * s, y)], tone, 9 * s, 1.0)
    garis_tebal(img, [(x + 8 * s, y - 34 * s), (x + 8 * s, y)], tone, 9 * s, 1.0)
    garis_tebal(img, [(x + 12 * s * hadap, y - 86 * s), (x + 44 * s * hadap, y - 96 * s)], tone, 7 * s, 1.0)


def layangan(img, x, y, s=1.0, tilt=0.0, t=0.0, tone=None):
    """Layang-layang belah ketupat + ekor bergoyang."""
    tone = tone or mix(TERRA, AMBER_H, 0.45)
    c, si = math.cos(tilt), math.sin(tilt)
    raw = [(0, -34), (26, 0), (0, 40), (-26, 0)]
    pts = [(x + (px * c - py * si) * s, y + (px * si + py * c) * s) for px, py in raw]
    bentuk(img, pts, tone, ow=2.6, light=0.34)
    for k in range(2):
        a = tilt + k * math.pi
        line_on(img, (x - 26 * s * math.cos(a), y - 26 * s * math.sin(a)),
                (x + 26 * s * math.cos(a), y + 26 * s * math.sin(a)), mix(INK, tone, 0.5), 2.2, 0.55)
    tail = []
    for i in range(7):
        u = i / 6
        tail.append((x - math.sin(tilt) * (40 + u * 150) * s + 9 * math.sin(t * 2.4 + u * 5) * s,
                     y + math.cos(tilt) * (40 + u * 150) * s))
    garis_tebal(img, tail, mix(tone, INK, 0.35), 3.0 * s, 0.75)
    for i in (2, 4):
        dot_on(img, *tail[i], 3.2 * s, mix(CREAM, WHITE, 0.4), 0.8)


def angin(img, pts, t, tone=None, w=6.0, alpha=0.85, ekor=3):
    """Pita angin: garis utama bergelombang + garis tipis pengikut + pusaran kecil."""
    tone = tone or mix(CREAM, WHITE, 0.15)
    garis_tebal(img, pts, tone, w, alpha, bulge=0.6)
    for k in range(ekor):
        off = (k + 1) * (12 + 4 * k)
        q = [(p[0], p[1] + off + 3 * math.sin(t * 2.0 + k)) for p in pts]
        garis_tebal(img, q, tone, max(1.6, w - 2.4 * (k + 1)), alpha * (0.42 - k * 0.10))
    # pusaran di ujung
    ex, ey = pts[-1]
    for k in range(2):
        rr = (16 + 9 * k) * (0.9 + 0.1 * math.sin(t * 3 + k))
        start = t * 2.4 + k * 2.0
        arc = [(ex + rr * math.cos(start + i * 0.5), ey - 6 - rr * math.sin(start + i * 0.5)) for i in range(7)]
        garis_tebal(img, arc, tone, max(1.4, w - 2.0 * k), alpha * (0.55 - k * 0.2))


def hujan(img, x0, x1, y0, y1, t, tone=None, n=46, condong=6.0, alpha=0.75):
    tone = tone or mix(CREAM, WHITE, 0.35)
    rng = np.random.default_rng(23)
    for i in range(n):
        bx = x0 + ((i * 137.3) % (x1 - x0))
        sp = 520 + (i % 5) * 90
        y = y0 + ((rng.random() * 0.9 * (y1 - y0)) + t * sp) % (y1 - y0)
        ln = 26 + (i % 4) * 7
        line_on(img, (bx, y), (bx - condong, y + ln), tone, 3.0, alpha * (0.5 + 0.3 * ((i % 3) / 2)))


def tetes(img, x, y, r, tone=None, alpha=0.9):
    tone = tone or mix(CREAM, WHITE, 0.5)
    bentuk(img, [(x, y - r * 1.6), (x + r, y), (x, y + r * 0.85), (x - r, y)], tone,
           outline=mix(TEAL, INK, 0.3), ow=1.8, light=0.35)


def bintang_laut(img, x, y, s=1.0, tone=None, rot=0.0):
    tone = tone or mix(TERRA, AMBER_H, 0.35)
    pts = []
    for i in range(10):
        a = rot + i * math.pi / 5 - math.pi / 2
        rr = (26 if i % 2 == 0 else 11) * s
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    bentuk(img, pts, tone, ow=2.2, light=0.28)


# ------------------------------------------------------------------ teks & UI
def judul(img, lines, hl=None, y=1372, fsz=88, maks=960, tone=None, hl_tone=None):
    """Judul 2 baris: bold, rapat, dengan blok sorot di kata kunci."""
    tone = tone or mix(NAVY, INK, 0.15)
    hl_tone = hl_tone or mix(TERRA, CREAM, 0.55)
    y = y
    for ln in lines:
        f = font(F_HEAD, fsz)
        while tw(ln, f) > maks and fsz > 50:
            fsz -= 4
            f = font(F_HEAD, fsz)
        if hl and hl.upper() in ln.upper():
            pre = ln.upper().split(hl.upper())[0]
            wpre = tw(pre, f)
            whl = tw(hl.upper(), f)
            rrect_on(img, 540 - tw(ln, f) / 2 + wpre - 8, y - fsz * 0.42,
                     540 - tw(ln, f) / 2 + wpre + whl + 8, y + fsz * 0.40, 10, hl_tone, 0.55)
        paste_c(img, 540, y, ln, f, tone, 1.0)
        y += fsz * 1.06
    return y


def kartu_judul(img, lines, hl=None, y=1490, fsz=86, maks=920, tab=None, al=1.0, dy=0.0):
    """Kartu judul: krem beroutline ink + tab aksen + judul bold 2 baris."""
    tab = tab or TERRA
    f = font(F_HEAD, fsz)
    while max(tw(l, f) for l in lines) > maks and fsz > 46:
        fsz -= 4
        f = font(F_HEAD, fsz)
    lh = fsz * 1.03
    wid = max(tw(l, f) for l in lines) + 96
    hgt = lh * len(lines) + 62
    cy = y + dy
    shl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shl).rounded_rectangle([S(540 - wid / 2 + 4), S(cy - hgt / 2 + 14),
                                           S(540 + wid / 2 + 4), S(cy + hgt / 2 + 18)],
                                          radius=S(min(38, hgt / 2)), fill=(26, 22, 20, int(90 * al)))
    shl = shl.filter(ImageFilter.GaussianBlur(S(16)))
    img.paste(shl.convert("RGB"), (0, 0), shl)
    rrect_on(img, 540 - wid / 2, cy - hgt / 2, 540 + wid / 2, cy + hgt / 2, min(38, hgt / 2),
             mix(CREAM, WHITE, 0.55), 0.96 * al, outline=mix(INK, NAVY, 0.4), width=4.0)
    rrect_on(img, 540 - wid / 2 + 26, cy - hgt / 2 - 7, 540 - wid / 2 + 26 + 74, cy - hgt / 2 + 7, 7, tab, 0.95 * al)
    yy = cy - (len(lines) - 1) * lh / 2 + 4
    for ln in lines:
        paste_c(img, 540, yy, ln, f, mix(NAVY, INK, 0.25), al)
        yy += lh
    return cy + hgt / 2


def sumber(img, text, y=1692, tone=None, al=0.62):
    paste_c(img, 540, y, text, font("Poppins-Regular.ttf", 27), tone or mix(NAVY, MUTED, 0.55), al)


def gelembung(img, cx, cy, text, w=None, fsz=40, tone=None, bg=None, ekor="bawah", al=1.0, seed=0):
    """Gelembung teks pendek ala komik (1–2 baris), dengan ekor."""
    tone = tone or mix(NAVY, INK, 0.10)
    bg = bg or mix(CREAM, WHITE, 0.55)
    f = font(F_SUB, fsz)
    w = w or (tw(text, f) + 74)
    lines = [text]
    if tw(text, f) + 74 > (w or 1e9):
        lines = D.wrap(text, f, w - 70)
    lh = tlh(f) * 1.18
    hgt = lh * len(lines) + 40
    rrect_on(img, cx - w / 2, cy - hgt / 2, cx + w / 2, cy + hgt / 2, min(30, hgt / 2),
             bg, 0.97, outline=mix(tone, INK, 0.55), width=2.4)
    if ekor == "bawah":
        bentuk(img, [(cx - 16, cy + hgt / 2 - 2), (cx + 8, cy + hgt / 2 - 2), (cx - 6, cy + hgt / 2 + 22)],
               bg, outline=mix(tone, INK, 0.55), ow=2.4, light=0.4)
    for i, l in enumerate(lines):
        paste_c(img, cx, cy + (i - (len(lines) - 1) / 2) * lh, l, f, tone, al)


def angka_besar(img, x, y, num, unit, tone=None, unit_tone=None, fsz=104, al=1.0):
    """Angka skala besar ala acuan: angka tebal + satuan kecil di kanan."""
    tone = tone or mix(CREAM, WHITE, 0.55)
    f = font(F_HEAD, fsz)
    fu = font(F_SUB, int(fsz * 0.40))
    wn, wu = tw(num, f), tw(unit, fu)
    tot = wn + wu + 14
    paste_c(img, x - tot / 2 + wn / 2 + 6, y + 3, num, f, mix(TEAL_D, INK, 0.4), 0.28 * al)   # bayangan
    paste_c(img, x - tot / 2 + wn / 2, y, num, f, tone, al)
    paste_c(img, x - tot / 2 + wn + 14 + wu / 2, y + fsz * 0.16, unit, fu, unit_tone or tone, al * 0.92)


def inset(img, cx, cy, r, gambar, ring_col=None, al=1.0, latar=None):
    """Kaca pembesar bulat (trik acuan): isi digambar terpisah lalu di-clip."""
    size = int(round(S(2 * r)))
    lay = Image.new("RGB", (size, size), latar or mix(CREAM, WHITE, 0.5))
    gambar(lay)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    img.paste(lay, (int(round(S(cx - r))), int(round(S(cy - r)))), mask)
    ring_on(img, cx, cy, r, ring_col or mix(NAVY, INK, 0.3), 4.2, 0.9)
    ring_on(img, cx, cy, r + 7, mix(CREAM, WHITE, 0.4), 2.0, 0.35)


def garis_dasar(img, y, al=0.10, tone=None):
    line_on(img, (0, y), (1080, y), tone or mix(NAVY, CREAM, 0.55), 2.0, al)


def butir_terbang(img, t, x0=0, x1=1080, y0=200, y1=1200, n=26, tone=None, seed=3):
    """Debu/butir melayang (mengisi frame agar tak pernah beku)."""
    tone = tone or mix(CREAM, WHITE, 0.4)
    rng = np.random.default_rng(seed)
    for i in range(n):
        sd = rng.random()
        sp = 26 + sd * 44
        x = (x0 + (sd * (x1 - x0) + t * sp * 1.6) % (x1 - x0))
        y = (y0 + ((i * 97.3) % (y1 - y0)) + 16 * math.sin(t * 1.1 + i)) % (y1 - y0) + y0
        dot_on(img, x, y, 1.8 + 2.4 * sd, tone, 0.20 + 0.24 * sd)


# ------------------------------------------------------------------ selftest
def _contoh():
    im = Image.new("RGB", (int(S(1080)), int(S(1920))), CREAM)
    langit(im, 0, 1000)
    cahaya_matahari(im, 780, 360, 90, 0.8)
    matahari(im, 780, 360, 92, 0.0)
    laut(im, 1000, 1320, 1.0)
    pasir(im, 1310)
    awan(im, 430, 250, 300, 130, seed=2)
    awan(im, 820, 470, 210, 96, seed=6)
    pohon_kelapa(im, 150, 1320, 1.0, 0.4)
    orang(im, 700, 1330, 1.0, hadap=-1)
    layangan(im, 560, 620, 1.0, tilt=0.28, t=1.0)
    angin(im, kurva((80, 900), (400, 840), (760, 930), 22), 1.0)
    judul(im, ["KE MANA ANGIN", "PERGI?"], hl="ANGIN", y=1460, fsz=96)
    gelembung(im, 540, 1215, "satu embusan, satu perjalanan", w=720, fsz=38)
    sumber(im, "Sumber: NOAA · USGS · BMKG")
    return im


if __name__ == "__main__":
    im = _contoh()
    im.resize((540, 960), Image.LANCZOS).save("/tmp/v15_contoh.jpg", quality=90)
    print("selftest v15: contoh 1080x1920 -> /tmp/v15_contoh.jpg")
