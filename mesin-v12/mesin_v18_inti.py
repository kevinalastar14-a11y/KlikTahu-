#!/usr/bin/env python3
"""mesin_v18_inti.py — INTI RASTER CEPAT untuk KlikTahu v18.

Filosofi
--------
Mesin v11-v17 menggambar ULANG seluruh adegan ke PIL untuk setiap frame. Itu
sebabnya satu frame 1080x1920 butuh 210-430 ms walau gambarnya sederhana:
yang mahal bukan "menggambar hiu", tapi mengulang gradasi, outline, teks, dan
kompresi PNG 6.129 kali.

v18 membalik arsitekturnya:

  1. **Raster sekali, tempel berkali-kali.** Semua yang tidak berubah (latar,
     pita air, pasir, rumput, kartu, teks, diagram) dirasterisasi SEKALI
     menjadi sprite RGBA anti-alias, disimpan di cache. Tiap frame hanya
     menyalin latar (memcpy) lalu menempel beberapa sprite.

  2. **Komposisi numpy + OpenCV.** Alpha blending dilakukan dengan aritmetika
     integer uint16 pada kotak lokal sprite saja (bukan float32 seukuran
     kanvas), memakai cv2 untuk LUT, resize, dan warp yang ber-SIMD.

  3. **Gerak tanpa raster ulang.** Badan hiu/ikan tidak digambar ulang tiap
     frame: sprite lurus digeser per kolom dengan fungsi sinus (`swim`), jadi
     undulasi tubuh, kibasan ekor, dan gelombang badan didapat dari satu
     operasi gather. Ini yang membuat gerakan terasa "hidup" tanpa biaya
     gambar.

  4. **Kamera = pan, bukan warp penuh.** Pan dilakukan dengan slicing
     (gratis); zoom hanya dipakai saat benar-benar perlu (`cam`).

Isi modul
---------
  util      : clamp, lerp, mix, easing, Track, rng
  noise     : value noise, fBm, kaustik laut, tekstur kertas
  font/teks : cache font, mask, sprite teks, paragraf, teks kaya (highlight)
  sprite    : raster() supersample, blit(), tint(), rot(), swim(), bayang()
  kanvas    : Kanvas (fill, gradasi, bentuk, tempel, LUT, JPEG/BGR keluar)
  geometri  : bezier, spline, poligon meruncing, gigi, gelombang
  warna     : ruang OKLab ringan untuk pencampuran warna yang tidak keruh

Selftest:  python3 mesin_v18_inti.py
"""
from __future__ import annotations

import functools
import math
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(BASE, "fonts")

F_BOLD = "Poppins-Bold.ttf"
F_SEMI = "Poppins-SemiBold.ttf"
F_MED = "Poppins-Medium.ttf"
F_REG = "Poppins-Regular.ttf"

# =============================================================== 1. util angka


def clamp(v, a=0.0, b=1.0):
    """Jepit nilai ke rentang [a, b]."""
    return a if v < a else (b if v > b else v)


def lerp(a, b, t):
    """Interpolasi linear."""
    return a + (b - a) * t


def seg(t, a, b):
    """Posisi t di dalam segmen [a, b] yang dinormalkan ke 0..1."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def smooth(t):
    t = clamp(t)
    return t * t * (3.0 - 2.0 * t)


def eo(t):
    """Ease-out kubik: cepat di awal, lembut di akhir."""
    t = clamp(t)
    return 1.0 - (1.0 - t) ** 3


def ei(t):
    """Ease-in kubik."""
    t = clamp(t)
    return t ** 3


def eio(t):
    """Ease-in-out kubik."""
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def eob(t, c1=1.30):
    """Ease-out-back: sedikit melewati target lalu balik (kenyal, hidup)."""
    t = clamp(t) - 1.0
    c3 = c1 + 1.0
    return 1.0 + c3 * t ** 3 + c1 * t ** 2


def elastic(t, freq=3.0, decay=6.0):
    """Osilasi teredam — dipakai untuk hentakan kartu dan angka."""
    t = clamp(t)
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return 1.0 - math.exp(-decay * t) * math.cos(2 * math.pi * freq * t)


def pulse(t, freq=1.0, lo=0.0, hi=1.0):
    """Gelombang sinus 0..1 untuk denyut halus."""
    return lo + (hi - lo) * (0.5 + 0.5 * math.sin(2 * math.pi * freq * t))


class Track:
    """Timeline nilai berkunci: [(t, nilai, easing), ...] dengan pencarian linear.

    Dipakai untuk gerak kamera dan elemen yang butuh profil khusus. Jumlah kunci
    per track kecil (<8) sehingga pencarian linear lebih cepat daripada bisect.
    """

    __slots__ = ("kunci",)

    def __init__(self, kunci, ease=eio):
        self.kunci = sorted((float(t), float(v), e) for t, v, *rest in
                            [(k[0], k[1], *(k[2:3] or (ease,))) for k in kunci]
                            for e in [rest[0] if rest else ease])

    def at(self, t):
        k = self.kunci
        if not k:
            return 0.0
        if t <= k[0][0]:
            return k[0][1]
        if t >= k[-1][0]:
            return k[-1][1]
        for i in range(1, len(k)):
            t1, v1, e1 = k[i]
            if t <= t1:
                t0, v0, _ = k[i - 1]
                p = e1((t - t0) / max(1e-6, t1 - t0))
                return v0 + (v1 - v0) * p
        return k[-1][1]


def rng(seed):
    """Generator numpy deterministik (hasil render harus sama di setiap proses)."""
    return np.random.default_rng(int(seed) & 0xFFFFFFFF)


# =============================================================== 2. warna


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    """Campur dua warna RGB secara linear (cukup untuk palet datar KlikTahu)."""
    t = clamp(t)
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1[:3], c2[:3]))


def shade(c, f):
    """Terangkan (f>1) atau gelapkan (f<1) warna."""
    return tuple(int(clamp(v * f, 0, 255)) for v in c[:3])


def with_a(c, a):
    """Tambah kanal alpha ke warna RGB."""
    return (int(c[0]), int(c[1]), int(c[2]), int(clamp(a, 0, 1) * 255))


def lum(c):
    """Luminans persepsi ringan (0..255)."""
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def mixer_oklab(c1, c2, t):
    """Campur warna di ruang OKLab — mencegah abu-abu keruh saat mencampur
    kuning dengan biru (dipakai untuk gradasi langit senja)."""
    def to(c):
        r, g, b = [v / 255.0 for v in c[:3]]
        r = r ** 2.2 if r > 0 else 0.0
        g = g ** 2.2 if g > 0 else 0.0
        b = b ** 2.2 if b > 0 else 0.0
        l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
        m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
        s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
        l, m, s = (np.cbrt(max(0.0, v)) for v in (l, m, s))
        return np.array([
            0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
        ])

    def frm(v):
        L, a, b = v
        l_ = L + 0.3963377774 * a + 0.2158037573 * b
        m_ = L - 0.1055613458 * a - 0.0638541728 * b
        s_ = L - 0.0894841775 * a - 1.2914855480 * b
        l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
        r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
        g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
        bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
        out = []
        for v2 in (r, g, bb):
            v2 = max(0.0, v2) ** (1 / 2.2)
            out.append(int(clamp(round(v2 * 255), 0, 255)))
        return tuple(out)

    a, b = to(c1), to(c2)
    return frm(a + (b - a) * clamp(t))


# =============================================================== 3. noise


def gblur(arr, sigma):
    """GaussianBlur dengan ksize ganjil (OpenCV 5 menolak ksize=0)."""
    if sigma <= 0.01:
        return arr
    k = int(2 * math.ceil(3 * sigma) + 1)
    return cv2.GaussianBlur(arr, (k, k), sigma)


def value_noise(h, w, scale=64, seed=1):
    """Value noise halus: grid acak kecil di-upscale bicubic (cepat, tanpa loop)."""
    gh = max(2, int(h / scale) + 2)
    gw = max(2, int(w / scale) + 2)
    g = rng(seed).random((gh, gw)).astype(np.float32)
    up = cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
    return np.clip(up, 0.0, 1.0)


def fbm(h, w, scale=96, octaves=4, seed=1, gain=0.5):
    """Fractal Brownian motion 4 oktaf — awan, tekstur pasir, kabut."""
    out = np.zeros((h, w), np.float32)
    amp, tot, s = 1.0, 0.0, scale
    for i in range(octaves):
        out += amp * value_noise(h, w, max(6, s), seed + i * 17)
        tot += amp
        amp *= gain
        s *= 0.5
    return out / max(1e-6, tot)


def caustic_tile(size=256, seed=7):
    """Ubin kaustik air: pola jaring terang yang bisa di-tile tanpa jahitan.

    Dibuat dari interferensi empat gelombang sinus berfase acak lalu di-ridge,
    sehingga menghasilkan garis lengkung seperti pantulan cahaya di dasar laut.
    """
    r = rng(seed)
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    acc = np.zeros((size, size), np.float32)
    for i in range(4):
        ang = r.uniform(0, math.pi)
        freq = r.uniform(2.0, 5.0) * (2 * math.pi / size)
        phase = r.uniform(0, 2 * math.pi)
        acc += np.sin(x * math.cos(ang) * freq + y * math.sin(ang) * freq + phase)
    acc = np.abs(acc) / 4.0
    ridged = 1.0 - gblur(acc.astype(np.float32), size * 0.012)
    ridged = np.clip((ridged - 0.55) * 4.0, 0, 1)
    soft = gblur(ridged, size * 0.02)
    return (np.clip(soft * 255, 0, 255)).astype(np.uint8)


def paper_grain(h, w, strength=6.0, seed=3):
    """Grain halus untuk kertas krem — memecah bidang datar tanpa biaya encode."""
    n = rng(seed).normal(0, strength, (h, w, 1)).astype(np.float32)
    return n


# =============================================================== 4. font & teks

_FONT_CACHE = {}


@functools.lru_cache(maxsize=512)
def F(name, size):
    """Muat font Poppins pada ukuran tertentu (cache lru)."""
    px = max(4, int(round(size)))
    key = (name, px)
    f = _FONT_CACHE.get(key)
    if f is None:
        f = ImageFont.truetype(os.path.join(FONTS, name), px)
        _FONT_CACHE[key] = f
    return f


def tw(text, name, size):
    """Lebar teks dalam piksel."""
    return F(name, size).getlength(text)


def tlh(name, size):
    """Tinggi baris (ascent+descent) untuk ukuran font."""
    f = F(name, size)
    a, d = f.getmetrics()
    return a + d


_MASK_CACHE = {}


def mask(text, name, size, tracking=0.0):
    """Bitmap alpha teks (uint8) — cache global.

    `tracking` menambah jarak antarhuruf (px) untuk judul besar; dikerjakan
    manual per glyph karena Pillow belum mendukung letter-spacing.
    """
    key = (text, name, int(round(size)), round(tracking, 2))
    m = _MASK_CACHE.get(key)
    if m is not None:
        return m
    f = F(name, size)
    if tracking <= 0.001:
        bbox = f.getbbox(text)
        l, t, r, b = bbox[0], bbox[1], bbox[2], bbox[3]
        w = max(1, r - l) + 8
        h = max(1, b - t) + 8
        im = Image.new("L", (w, h), 0)
        ImageDraw.Draw(im).text((4 - l, 4 - t), text, font=f, fill=255)
    else:
        widths = [f.getlength(ch) for ch in text]
        w = int(math.ceil(sum(widths) + tracking * max(0, len(text) - 1))) + 8
        asc, dsc = f.getmetrics()
        h = asc + dsc + 8
        im = Image.new("L", (max(1, w), max(1, h)), 0)
        d = ImageDraw.Draw(im)
        x = 4.0
        for ch, cw in zip(text, widths):
            d.text((x, 4), ch, font=f, fill=255)
            x += cw + tracking
    arr = np.array(im)
    _MASK_CACHE[key] = arr
    return arr


@functools.lru_cache(maxsize=2048)
def spr_text(text, color, name=F_BOLD, size=64, tracking=0.0, shadow=None,
             shadow_blur=6, shadow_off=(0, 4), shadow_a=105):
    """Sprite RGBA teks + bayangan lembut opsional (bayangan memperkuat kontras)."""
    m = mask(text, name, size, tracking)
    h, w = m.shape
    if shadow is None:
        rgba = np.empty((h, w, 4), np.uint8)
        rgba[..., 0] = color[0]
        rgba[..., 1] = color[1]
        rgba[..., 2] = color[2]
        rgba[..., 3] = m
        return rgba
    pad = int(shadow_blur * 2)
    H, W = h + pad * 2, w + pad * 2
    out = np.zeros((H, W, 4), np.uint8)
    sm = np.zeros((H, W), np.uint8)
    ox, oy = int(shadow_off[0]) + pad, int(shadow_off[1]) + pad
    sm[oy:oy + h, ox:ox + w] = m
    sm = gblur(sm, shadow_blur)
    sm = (sm.astype(np.uint16) * shadow_a // 255).astype(np.uint8)
    out[..., 0] = shadow[0]
    out[..., 1] = shadow[1]
    out[..., 2] = shadow[2]
    out[..., 3] = sm
    # teks di atas bayangan
    ty, tx = pad, pad
    reg = out[ty:ty + h, tx:tx + w]
    a = m[:, :, None].astype(np.uint16)
    base = reg.astype(np.uint16)
    col = np.array(color[:3], np.uint16)
    rgb = (col[None, None, :] * a + base[..., :3] * (255 - a) + 127) >> 8
    reg[..., :3] = rgb.astype(np.uint8)
    reg[..., 3] = np.maximum(reg[..., 3], m)
    return out


def wrap(text, name, size, maxw):
    """Pecah teks menjadi baris yang muat pada lebar maksimum."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if tw(cand, name, size) <= maxw or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_size(text, name, size, maxw, min_size=18):
    """Turunkan ukuran font sampai teks muat pada lebar tertentu."""
    s = size
    while s > min_size and tw(text, name, s) > maxw:
        s -= 2
    return s


class TeksKinetik:
    """Satu baris teks yang dipecah per kata, masing-masing sprite terpisah.

    Dipakai untuk tipografi kinetik: kata muncul satu per satu (geser + fade),
    lalu kata kunci diberi sorotan stabilo. Semua sprite dibuat sekali.
    """

    def __init__(self, baris, name=F_BOLD, size=64, warna=(30, 32, 40),
                 tinggi=None, rata="kiri", maxw=None, tracking=0.0,
                 sorot=None, sorot_warna=None, sorot_t=0.0):
        self.baris = baris
        self.name = name
        self.size = size
        self.warna = warna
        self.tinggi = tinggi or int(tlh(name, size) * 1.02)
        self.maxw = maxw
        self.tracking = tracking
        self.sorot = set((sorot or "").lower().split())
        self.sorot_warna = sorot_warna or (245, 176, 66)
        self.kata = []          # (sprite, x, y, idx, disorot)
        idx = 0
        for r, baris_txt in enumerate(self.baris if isinstance(self.baris, list) else [self.baris]):
            kata = baris_txt.split()
            lebar = [tw(k, name, size) for k in kata]
            spasi = tw(" ", name, size)
            total = sum(lebar) + spasi * max(0, len(kata) - 1)
            x = 0.0 if rata == "kiri" else (-total / 2 if rata == "tengah" else -total)
            for k, w in zip(kata, lebar):
                sorot = k.strip(".,:;!?—").lower() in self.sorot
                sp = spr_text(k, warna, name, size, self.tracking)
                self.kata.append((sp, x, r * self.tinggi, idx, sorot))
                x += w + spasi
                idx += 1
        self.n = idx
        self.lebar = max((tw(" ".join(b.split()), name, size) for b in
                          (self.baris if isinstance(self.baris, list) else [self.baris])),
                         default=0)

    def gambar(self, kanvas, x, y, t, masuk=0.0, per_kata=0.045, alpha=1.0,
               sorot_prog=None, geser=18):
        """Gambar semua kata. `t` = waktu lokal; kata ke-i muncul pada
        masuk + i*per_kata. `sorot_prog` (0..1) mengisi stabilo kata kunci."""
        for sp, kx, ky, i, sorot in self.kata:
            p = clamp((t - masuk - i * per_kata) / 0.28)
            if p <= 0.0:
                continue
            e = eo(p)
            a = alpha * e
            dy = (1 - e) * geser
            if sorot and sorot_prog is not None and sorot_prog > 0:
                self._stabilo(kanvas, x + kx, y + ky, sp, sorot_prog, alpha)
            blit(kanvas, sp, x + kx, y + ky + dy, a)

    def _stabilo(self, kanvas, x, y, sp, prog, alpha):
        """Sorotan stabilo yang tumbuh dari kiri ke kanan di belakang kata."""
        h, w = sp.shape[:2]
        lebar = int(w * clamp(prog))
        if lebar <= 2:
            return
        y0 = int(y + h * 0.62)
        hh = max(3, int(h * 0.30))
        c = self.sorot_warna
        x0 = int(x)
        y0c, y1c = max(0, y0), min(kanvas.shape[0], y0 + hh)
        x0c, x1c = max(0, x0), min(kanvas.shape[1], x0 + lebar)
        if y1c <= y0c or x1c <= x0c:
            return
        reg = kanvas[y0c:y1c, x0c:x1c].astype(np.float32)
        reg += (np.array(c, np.float32) - reg) * (0.72 * alpha)
        kanvas[y0c:y1c, x0c:x1c] = np.clip(reg, 0, 255).astype(np.uint8)


# =============================================================== 5. sprite

def raster(w, h, fn, ss=2):
    """Rasterisasi gambar vektor ke sprite RGBA anti-alias.

    `fn(pena)` menggambar pada koordinat 1x; pena mengalikan sendiri dengan
    `ss` lalu hasilnya diperkecil (supersampling). Ini memberi tepi sehalus
    vektor tanpa perlu SIMD sendiri.
    """
    w, h = max(1, int(w)), max(1, int(h))
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    pena = Pena(ImageDraw.Draw(im), ss)
    fn(pena)
    if ss != 1:
        im = im.resize((w, h), Image.LANCZOS)
    return np.array(im)


class Pena:
    """Pembungkus ImageDraw yang bekerja pada koordinat 1x (skala internal ss)."""

    __slots__ = ("d", "k")

    def __init__(self, d, k):
        self.d = d
        self.k = k

    def _p(self, xy):
        k = self.k
        return [(x * k, y * k) for x, y in xy]

    def _box(self, x0, y0, x1, y1):
        k = self.k
        return [x0 * k, y0 * k, x1 * k, y1 * k]

    def rrect(self, x0, y0, x1, y1, r, fill=None, outline=None, width=1.0):
        self.d.rounded_rectangle(self._box(x0, y0, x1, y1), radius=r * self.k,
                                 fill=fill, outline=outline,
                                 width=max(1, int(round(width * self.k))))

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1.0):
        self.d.rectangle(self._box(x0, y0, x1, y1), fill=fill, outline=outline,
                         width=max(1, int(round(width * self.k))))

    def ell(self, x0, y0, x1, y1, fill=None, outline=None, width=1.0):
        self.d.ellipse(self._box(x0, y0, x1, y1), fill=fill, outline=outline,
                       width=max(1, int(round(width * self.k))))

    def circ(self, cx, cy, r, fill=None, outline=None, width=1.0):
        self.ell(cx - r, cy - r, cx + r, cy + r, fill, outline, width)

    def poly(self, pts, fill=None, outline=None, width=1.0):
        p = self._p(pts)
        if fill is not None:
            self.d.polygon(p, fill=fill)
        if outline is not None:
            p2 = list(p) + [p[0]]
            self.d.line(p2, fill=outline, width=max(1, int(round(width * self.k))),
                        joint="curve")

    def line(self, pts, color, width=2.0, joint="curve"):
        p = self._p(pts)
        self.d.line(p, fill=color, width=max(1, int(round(width * self.k))), joint=joint)

    def arc(self, x0, y0, x1, y1, a0, a1, color, width=2.0):
        self.d.arc(self._box(x0, y0, x1, y1), a0, a1, fill=color,
                   width=max(1, int(round(width * self.k))))

    def pie(self, x0, y0, x1, y1, a0, a1, fill=None, outline=None, width=1.0):
        self.d.pieslice(self._box(x0, y0, x1, y1), a0, a1, fill=fill,
                        outline=outline, width=max(1, int(round(width * self.k))))


def blit(dst, spr, x, y, alpha=1.0):
    """Tempel sprite RGBA ke kanvas RGB pada (x, y) — sudut kiri atas.

    Aritmetika integer uint16 pada kotak sprite saja; jalur cepat dipakai bila
    sprite sepenuhnya opak (salin langsung).
    """
    h, w = spr.shape[:2]
    x, y = int(round(x)), int(round(y))
    H, W = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sx0, sy0 = x0 - x, y0 - y
    sub = spr[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    a = sub[..., 3]
    if alpha < 0.999:
        a = (a.astype(np.uint16) * int(alpha * 255) // 255).astype(np.uint8)
    if a.min() == 255:
        dst[y0:y1, x0:x1] = sub[..., :3]
        return
    ai = a[:, :, None].astype(np.uint16)
    reg = dst[y0:y1, x0:x1]
    # Bagi 255, BUKAN 256 (>>8). Versi lama memakai >>8 sehingga piksel dengan
    # alpha 0 pun ikut berubah 1 tingkat: kotak sprite jadi terlihat sebagai
    # bayangan segi empat samar di atas latar terang (ketahuan di mesin v21).
    out = (sub[..., :3].astype(np.uint16) * ai +
           reg[..., :3].astype(np.uint16) * (255 - ai) + 127) // 255
    reg[..., :3] = out.astype(np.uint8)
    if reg.shape[2] == 4:
        reg[..., 3] = np.maximum(reg[..., 3], a)



def blit_add(dst, spr, x, y, alpha=1.0):
    """Tempel ADDITIF (cahaya): src*a + dst. Dipakai berkas cahaya & kaustik."""
    h, w = spr.shape[:2]
    x, y = int(round(x)), int(round(y))
    H, W = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sx0, sy0 = x0 - x, y0 - y
    sub = spr[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    a = sub[..., 3].astype(np.uint16) * int(alpha * 255) // 255
    add = (sub[..., :3].astype(np.uint16) * a[:, :, None]) >> 8
    reg = dst[y0:y1, x0:x1].astype(np.uint16)
    dst[y0:y1, x0:x1] = np.clip(reg + add, 0, 255).astype(np.uint8)


def blit_kali(dst, spr, x, y, alpha=1.0):
    """Tempel MULTIPLY (bayangan lembut): dst * (1 - a) + src*a."""
    h, w = spr.shape[:2]
    x, y = int(round(x)), int(round(y))
    H, W = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sx0, sy0 = x0 - x, y0 - y
    sub = spr[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    a = (sub[..., 3].astype(np.uint16) * int(alpha * 255) // 255)[:, :, None]
    reg = dst[y0:y1, x0:x1].astype(np.uint16)
    out = (reg * (255 - a) + sub[..., :3].astype(np.uint16) * a) >> 8
    dst[y0:y1, x0:x1] = out.astype(np.uint8)


def komposit(dasar, lapis):
    """Gabung lapis RGBA di atas dasar RGBA dengan aturan "over" yang benar."""
    a = lapis[..., 3:4].astype(np.uint16)
    da = dasar[..., 3:4].astype(np.uint16)
    out_a = a + (da * (255 - a) >> 8)
    rgb = (lapis[..., :3].astype(np.uint16) * a +
           dasar[..., :3].astype(np.uint16) * (da * (255 - a) >> 8)) // np.maximum(out_a, 1)
    dasar[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    dasar[..., 3] = np.clip(out_a[..., 0], 0, 255).astype(np.uint8)
    return dasar


def mask_poli(w, h, daftar_pts, ss=2):
    """Mask alpha uint8 dari satu atau beberapa poligon (untuk klip lapisan)."""
    im = Image.new("L", (int(w * ss), int(h * ss)), 0)
    d = ImageDraw.Draw(im)
    for pts in daftar_pts:
        d.polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    if ss != 1:
        im = im.resize((int(w), int(h)), Image.LANCZOS)
    return np.array(im)


def mask_rrect(w, h, r, ss=2):
    """Mask alpha uint8 kotak bersudut bulat."""
    im = Image.new("L", (int(w * ss), int(h * ss)), 0)
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1],
                                        radius=r * ss, fill=255)
    if ss != 1:
        im = im.resize((int(w), int(h)), Image.LANCZOS)
    return np.array(im)


def lapis_rgba(w, h, warna=(255, 255, 255), alpha=1.0):
    """Kanvas RGBA kosong berwarna (untuk lapisan efek yang dikomposit)."""
    out = np.zeros((int(h), int(w), 4), np.uint8)
    out[..., :3] = warna[:3]
    return out


def belly_mask(mask, frac=0.62):
    """Mask bagian PERUT dari siluet: tiap kolom dipotong pada frac tinggi badan.

    Menghitung baris pertama & terakhir yang berisi alpha per kolom, lalu
    menyimpan baris di bawah `frac` — hasilnya selalu menempel ke tepi bawah
    siluet apa pun bentuk tubuhnya. Ini menghilangkan pita krem "melayang"
    yang muncul bila batas perut dihitung dari kurva terpisah.
    """
    m = mask > 8
    h, w = m.shape
    ada = m.any(axis=0)
    atas = np.argmax(m, axis=0)
    bawah = h - 1 - np.argmax(m[::-1], axis=0)
    # ratakan tepi (jendela 9 px) supaya batas perut tidak bergerigi per kolom
    kern = np.ones(9, dtype=np.float32) / 9.0
    atas = np.convolve(atas.astype(np.float32), kern, mode="same")
    bawah = np.convolve(bawah.astype(np.float32), kern, mode="same")
    thr = atas + (bawah - atas) * float(frac)
    baris = np.arange(h, dtype=np.float32)[:, None]
    sel = (baris >= thr[None, :]) & m
    return (sel.astype(np.uint8) * 255)


def gigi_kecil(w, h, n=6):
    """Deret takik gigi untuk mulut (dipakai sebagai mask, bukan sprite)."""
    im = Image.new("L", (int(w), int(h)), 0)
    d = ImageDraw.Draw(im)
    step = w / max(1, n)
    for i in range(n):
        x0 = i * step
        d.polygon([(x0, 0), (x0 + step, 0), (x0 + step * 0.5, h)], fill=255)
    return np.array(im)


def pangkas(spr, ambang=2, tepi=2):
    """Pangkas pinggiran sprite yang transparan (memperkecil kotak blit).

    Sprite vektor menyisakan banyak ruang kosong di sekitar bentuk; memangkasnya
    memotong biaya `blit` hampir separuh. `tepi` menyisakan beberapa piksel agar
    tepi anti-alias tidak terpotong.
    """
    a = spr[..., 3]
    baris = np.where(a.max(axis=1) > ambang)[0]
    kolom = np.where(a.max(axis=0) > ambang)[0]
    if len(baris) == 0 or len(kolom) == 0:
        return spr
    y0 = max(0, baris[0] - tepi)
    y1 = min(spr.shape[0], baris[-1] + 1 + tepi)
    x0 = max(0, kolom[0] - tepi)
    x1 = min(spr.shape[1], kolom[-1] + 1 + tepi)
    return np.ascontiguousarray(spr[y0:y1, x0:x1])

def blit_c(dst, spr, cx, cy, alpha=1.0):
    """Tempel dengan titik jangkar di TENGAH sprite."""
    blit(dst, spr, cx - spr.shape[1] / 2.0, cy - spr.shape[0] / 2.0, alpha)


def blit_s(dst, spr, cx, cy, skala, alpha=1.0, rot=0.0):
    """Tempel sprite dengan skala/rotasi (cv2 warp pada kotak sprite, bukan kanvas)."""
    if abs(skala - 1.0) < 0.004 and abs(rot) < 0.05:
        blit_c(dst, spr, cx, cy, alpha)
        return
    h, w = spr.shape[:2]
    ns = max(1, int(round(w * skala)))
    nh = max(1, int(round(h * skala)))
    if abs(rot) > 0.05:
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, skala)
        cos, sin = abs(M[0, 0]), abs(M[0, 1])
        nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
        M[0, 2] += nw / 2 - w / 2
        M[1, 2] += nh / 2 - h / 2
        out = cv2.warpAffine(spr, M, (nw, nh), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    else:
        out = cv2.resize(spr, (ns, nh), interpolation=cv2.INTER_AREA if skala < 1 else cv2.INTER_LINEAR)
    blit_c(dst, out, cx, cy, alpha)


def tint(spr, color, amount):
    """Campur warna sprite ke arah `color` (untuk kabut kedalaman / siluet jauh)."""
    if amount <= 0.001:
        return spr
    out = spr.copy()
    a = out[..., 3:4].astype(np.float32)
    rgb = out[..., :3].astype(np.float32)
    rgb += (np.array(color, np.float32) - rgb) * clamp(amount)
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    out[..., 3] = a[..., 0].astype(np.uint8)
    return out


def siluet(spr, color, alpha=255):
    """Ubah sprite menjadi siluet satu warna (untuk bayangan / figur jauh)."""
    out = spr.copy()
    out[..., 0] = color[0]
    out[..., 1] = color[1]
    out[..., 2] = color[2]
    out[..., 3] = (out[..., 3].astype(np.uint16) * alpha // 255).astype(np.uint8)
    return out


def bayang(spr, blur=10, alpha=0.32, warna=(20, 34, 40), skala_y=0.28):
    """Bayangan elips di bawah sprite (kontak dengan tanah = kedalaman)."""
    h, w = spr.shape[:2]
    m = spr[..., 3]
    rows = np.where(m.max(axis=1) > 8)[0]
    if len(rows) == 0:
        return np.zeros((2, 2, 4), np.uint8)
    bw = int(w * 0.86)
    bh = max(6, int(h * skala_y))
    im = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(im).ellipse([0, 0, bw - 1, bh - 1], fill=int(255 * alpha))
    arr = np.array(im.filter(ImageFilter.GaussianBlur(blur)))
    out = np.zeros((arr.shape[0], arr.shape[1], 4), np.uint8)
    out[..., :3] = warna
    out[..., 3] = arr
    return out


def swim(spr, amp=14.0, lam=260.0, phase=0.0, ramp=0.45, kuasa=1.7):
    """Undulasi tubuh ikan: geser tiap KOLOM secara horizontal mengikuti sinus.

    Amplitudo naik dari kepala ke ekor (`ramp` = titik mulai, `kuasa` = kelengkungan),
    menghasilkan gelombang berjalan yang terlihat seperti otot ikan, bukan sekadar
    sprite yang bergoyang. Satu operasi gather pada sumbu x — sangat cepat.
    """
    h, w = spr.shape[:2]
    xs = np.arange(w, dtype=np.float32)
    p = np.clip((xs / max(1.0, w) - ramp) / max(1e-3, 1.0 - ramp), 0.0, 1.0)
    a = amp * p ** kuasa
    dx = (a * np.sin(2 * math.pi * (xs / lam) - phase)).astype(np.int32)
    idx = np.clip(np.arange(w) - dx, 0, w - 1)
    # np.take jauh lebih cepat daripada fancy indexing untuk sprite besar (8x)
    return np.take(spr, idx, axis=1)


def gelombang_dada(spr, amp=5.0, lam=180.0, phase=0.0):
    """Napas dada: geser tiap BARIS vertikal sedikit (dipakai paus/penyu)."""
    h, w = spr.shape[:2]
    ys = np.arange(h, dtype=np.float32)
    dy = (amp * np.sin(2 * math.pi * ys / lam - phase)).astype(np.int32)
    idx = np.clip(np.arange(h) - dy, 0, h - 1)
    return np.take(spr, idx, axis=0)


# =============================================================== 6. geometri


def bezier(p0, p1, p2, p3, n=24):
    """Kurva Bezier kubik → daftar titik."""
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.array(p, np.float32) for p in (p0, p1, p2, p3))
    pts = ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    return [tuple(map(float, p)) for p in pts]


def catmull(points, n=16, closed=False):
    """Spline Catmull-Rom melalui titik — untuk profil tubuh hewan yang halus."""
    pts = [tuple(map(float, p)) for p in points]
    if len(pts) < 3:
        return pts
    if closed:
        ext = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        ext = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(len(ext) - 3):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if not closed:
        out.append(tuple(pts[-1]))
    return out


def badan(points, tebal, perut=0.0):
    """Poligon tubuh dari garis punggung + ketebalan per titik.

    `tebal` boleh skalar atau list sepanjang `points`. `perut` menambah
    asimetri (perut lebih cembung daripada punggung) sehingga siluet terasa
    organik, bukan pipa.
    """
    n = len(points)
    if not isinstance(tebal, (list, tuple, np.ndarray)):
        tebal = [tebal] * n
    atas, bawah = [], []
    for i, ((x, y), t) in enumerate(zip(points, tebal)):
        if i == 0:
            dx, dy = points[1][0] - x, points[1][1] - y
        elif i == n - 1:
            dx, dy = x - points[-2][0], y - points[-2][1]
        else:
            dx, dy = points[i + 1][0] - points[i - 1][0], points[i + 1][1] - points[i - 1][1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        atas.append((x + nx * t, y + ny * t))
        bawah.append((x - nx * t * (1.0 + perut), y - ny * t * (1.0 + perut)))
    return atas + bawah[::-1]


def gigi_pts(cx, cy, tinggi, lebar_r=0.56, rot=0.0, akar=True, gerigi=True, n_gerigi=5):
    """Siluet gigi hiu: mahkota meruncing + gerigi samping + akar V.

    Parameter disesuaikan hasil uji v17: tinggi 62-104 px pada kanvas 1080 px,
    kemiringan 8-20 derajat, lebar mahkota 0.56 x tinggi.
    """
    h = float(tinggi)
    w = h * lebar_r
    pts = []
    if akar:
        pts += [(-w * 0.52, h * 0.30), (-w * 0.22, h * 0.14), (0.0, h * 0.24)]
        pts += [(w * 0.22, h * 0.14), (w * 0.52, h * 0.30)]
    else:
        pts += [(-w * 0.30, h * 0.22)]
    # sisi kanan naik ke ujung
    if gerigi:
        for i in range(n_gerigi):
            f = i / max(1, n_gerigi - 1)
            y = lerp(h * 0.10, -h * 0.86, f)
            xx = w * (0.46 * (1 - f) ** 0.72 + 0.02)
            pts.append((xx, y))
            pts.append((xx * 0.80, y - h * 0.035))
    else:
        pts.append((w * 0.42, h * 0.06))
    pts.append((0.0, -h * 0.62))
    # sisi kiri turun
    if gerigi:
        for i in range(n_gerigi - 1, -1, -1):
            f = i / max(1, n_gerigi - 1)
            y = lerp(h * 0.10, -h * 0.86, f)
            xx = -w * (0.46 * (1 - f) ** 0.72 + 0.02)
            pts.append((xx * 0.80, y - h * 0.035))
            pts.append((xx, y))
    else:
        pts.append((-w * 0.42, h * 0.06))
    cr, sr = math.cos(rot), math.sin(rot)
    return [(cx + x * cr - y * sr, cy + x * sr + y * cr) for x, y in pts]


def gelombang_pts(x0, x1, y, amp, lam, phase, n=None, naik=0.0):
    """Garis gelombang air permukaan (dipakai berlapis untuk buih)."""
    n = n or max(12, int((x1 - x0) / 8))
    out = []
    for i in range(n + 1):
        x = lerp(x0, x1, i / n)
        yy = y + amp * math.sin(2 * math.pi * (x - x0) / lam + phase) + naik * (x - x0) / max(1.0, x1 - x0)
        out.append((x, yy))
    return out


# =============================================================== 7. kanvas

class Kanvas:
    """Kanvas RGB uint8 dengan operasi cepat (tempel sprite, gradasi, grade)."""

    __slots__ = ("a", "h", "w")

    def __init__(self, w, h, isi=(240, 236, 226)):
        self.w, self.h = int(w), int(h)
        self.a = np.empty((self.h, self.w, 3), np.uint8)
        self.a[:, :] = isi[:3]

    # --- dasar -------------------------------------------------------------
    def isi(self, warna):
        self.a[:, :] = warna[:3]
        return self

    def salin(self):
        k = Kanvas(self.w, self.h)
        k.a = self.a.copy()
        return k

    def dari(self, arr):
        self.a = arr
        return self

    def tempel(self, spr, x, y, alpha=1.0):
        blit(self.a, spr, x, y, alpha)
        return self

    def tempel_c(self, spr, cx, cy, alpha=1.0):
        blit_c(self.a, spr, cx, cy, alpha)
        return self


    def tempel_add(self, spr, x, y, alpha=1.0):
        blit_add(self.a, spr, x, y, alpha)
        return self

    def tempel_kali(self, spr, x, y, alpha=1.0):
        blit_kali(self.a, spr, x, y, alpha)
        return self

    def tempel_s(self, spr, cx, cy, skala=1.0, alpha=1.0, rot=0.0):
        blit_s(self.a, spr, cx, cy, skala, alpha, rot)
        return self

    # --- gradasi -----------------------------------------------------------
    def gradasi_v(self, y0, y1, stops, seed=1, dither=0.9):
        """Gradasi vertikal dengan dither per piksel (anti-banding).

        `stops` = [(pos 0..1, warna), ...]. Hanya menulis pada pita y0..y1.
        """
        y0, y1 = int(y0), int(y1)
        h = max(1, y1 - y0)
        ys = np.linspace(0.0, 1.0, h, dtype=np.float32)
        pos = np.array([s[0] for s in stops], np.float32)
        cols = np.array([s[1][:3] for s in stops], np.float32)
        band = np.empty((h, self.w, 3), np.float32)
        for c in range(3):
            band[:, :, c] = np.interp(ys, pos, cols[:, c])[:, None]
        if dither > 0:
            band += rng(seed + 91).normal(0.0, dither, (h, self.w, 1)).astype(np.float32)
        self.a[max(0, y0):max(0, y0) + h] = np.clip(band, 0, 255).astype(np.uint8)
        return self

    def gradasi_h(self, y0, y1, x0, x1, c1, c2):
        """Gradasi horizontal pada kotak (untuk panel kaca, kartu, dsb)."""
        x0, x1, y0, y1 = int(x0), int(x1), int(y0), int(y1)
        if x1 <= x0 or y1 <= y0:
            return self
        xs = np.linspace(0, 1, x1 - x0, dtype=np.float32)[None, :, None]
        band = np.array(c1[:3], np.float32)[None, None, :] * (1 - xs) + \
            np.array(c2[:3], np.float32)[None, None, :] * xs
        self.a[y0:y1, x0:x1] = np.clip(np.broadcast_to(band, (y1 - y0, x1 - x0, 3)), 0, 255).astype(np.uint8)
        return self

    # --- cuplikan / kamera -------------------------------------------------
    def potong(self, x, y, w, h):
        """Ambil kotak (tanpa salin bila memungkinkan) — dasar kamera pan."""
        x, y = int(round(x)), int(round(y))
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + int(w)), min(self.h, y + int(h))
        if x1 <= x0 or y1 <= y0:
            return np.zeros((max(1, int(h)), max(1, int(w)), 3), np.uint8)
        sub = self.a[y0:y1, x0:x1]
        if (y1 - y0) == h and (x1 - x0) == w and x0 == x and y0 == y:
            return sub
        out = np.full((int(h), int(w), 3), 235, np.uint8)
        out[y0 - y:y0 - y + (y1 - y0), x0 - x:x0 - x + (x1 - x0)] = sub
        return out

    def skala(self, w, h, interp=cv2.INTER_LINEAR):
        return cv2.resize(self.a, (int(w), int(h)), interpolation=interp)

    # --- efek --------------------------------------------------------------
    def lut(self, lut):
        """Terapkan LUT warna 3x256 (grade filmis) — cv2.LUT ber-SIMD."""
        self.a = cv2.LUT(self.a, lut)
        return self

    def vignette(self, kekuatan=0.22, lembut=1.6):
        """Vignette lembut yang dibakar langsung (bukan per frame)."""
        h, w = self.h, self.w
        yy = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
        xx = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
        r = np.sqrt(xx ** 2 + yy ** 2) / math.sqrt(2)
        m = 1.0 - kekuatan * np.clip(r, 0, 1) ** lembut
        self.a = np.clip(self.a.astype(np.float32) * m[:, :, None], 0, 255).astype(np.uint8)
        return self

    def grain(self, strength=4.0, seed=5):
        """Grain statis (sekali di latar) — tidak menambah biaya encode tiap frame."""
        n = rng(seed).normal(0, strength, (self.h, self.w, 1)).astype(np.float32)
        self.a = np.clip(self.a.astype(np.float32) + n, 0, 255).astype(np.uint8)
        return self

    def blur(self, sigma=2.0):
        self.a = gblur(self.a, sigma)
        return self

    def kabut(self, y0, y1, warna, kuat=0.35):
        """Selubung kabut (kedalaman) pada pita y — dipakai untuk air jauh."""
        y0, y1 = max(0, int(y0)), min(self.h, int(y1))
        if y1 <= y0:
            return self
        reg = self.a[y0:y1].astype(np.float32)
        reg += (np.array(warna[:3], np.float32) - reg) * kuat
        self.a[y0:y1] = np.clip(reg, 0, 255).astype(np.uint8)
        return self

    # --- keluaran ----------------------------------------------------------
    def bgr(self):
        """Konversi ke BGR (format yang ditunggu ffmpeg)."""
        return cv2.cvtColor(self.a, cv2.COLOR_RGB2BGR)


def lut_grade(kontras=1.06, saturasi=1.06, lift=(2, 2, 0), gamma=1.02,
              dingin=0.02):
    """Bangun LUT grade filmis: kontras-S, saturasi, lift hangat, gamma.

    Dibuat sekali per sesi dan dipakai `cv2.LUT` di setiap frame — jauh lebih
    murah daripada operasi float pada 6,2 juta piksel.
    """
    x = np.arange(256, dtype=np.float32) / 255.0
    y = np.clip((x - 0.5) * kontras + 0.5, 0, 1)
    y = y ** (1.0 / gamma)
    y = y * (1 - 0.10) + 0.10 * y ** 0.82       # angkat bayangan (tidak pekat)
    y = np.clip(y, 0, 1)
    base = y * 255.0
    lut = np.empty((1, 256, 3), np.uint8)
    # saturasi bekerja pada selisih antar kanal
    r = base + lift[0]
    g = base + lift[1]
    b = base + lift[2]
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    r = gray + (r - gray) * (saturasi + dingin * 0.4)
    g = gray + (g - gray) * saturasi
    b = gray + (b - gray) * (saturasi - dingin)
    lut[0, :, 0] = np.clip(r, 0, 255).astype(np.uint8)
    lut[0, :, 1] = np.clip(g, 0, 255).astype(np.uint8)
    lut[0, :, 2] = np.clip(b, 0, 255).astype(np.uint8)
    return lut


# =============================================================== 8. partikel

class Partikel:
    """Sistem partikel analitik tanpa penyimpanan status per frame.

    Posisi dihitung langsung dari waktu (`x0 + vx*t`, `y0 + vy*t`), jadi render
    deterministik dan bisa diparalelkan per potongan frame tanpa saling
    bergantung. Dipakai untuk salju laut, gelembung, dan percikan pasir.
    """

    def __init__(self, n, area, seed=1, vx=(-6, 6), vy=(-26, -8), size=(1, 3),
                 alpha=(0.20, 0.55), warna=(255, 255, 250)):
        r = rng(seed)
        self.n = int(n)
        self.x0 = r.uniform(area[0], area[2], self.n).astype(np.float32)
        self.y0 = r.uniform(area[1], area[3], self.n).astype(np.float32)
        self.vx = r.uniform(*vx, self.n).astype(np.float32)
        self.vy = r.uniform(*vy, self.n).astype(np.float32)
        self.sz = r.integers(size[0], size[1] + 1, self.n)
        self.alpha = r.uniform(*alpha, self.n).astype(np.float32)
        self.fase = r.uniform(0, 2 * math.pi, self.n).astype(np.float32)
        self.warna = warna
        self.area = area

    def gambar(self, dst, t, goyang=6.0):
        """Gambar semua partikel — hanya kotak 1-3 px, satu operasi per partikel."""
        x = (self.x0 + self.vx * t + goyang * np.sin(0.6 * t + self.fase)) % (self.area[2] - self.area[0])
        y = (self.y0 + self.vy * t) % (self.area[3] - self.area[1])
        x = (x + self.area[0]).astype(np.int32)
        y = (y + self.area[1]).astype(np.int32)
        H, W = dst.shape[:2]
        for i in range(self.n):
            s = int(self.sz[i])
            xi, yi = int(x[i]), int(y[i])
            if xi < 0 or yi < 0 or xi + s >= W or yi + s >= H:
                continue
            reg = dst[yi:yi + s, xi:xi + s]
            a = float(self.alpha[i])
            reg[:] = (reg.astype(np.float32) * (1 - a) +
                      np.array(self.warna, np.float32) * a).astype(np.uint8)


# =============================================================== 9. selftest

def _selftest():
    import time

    k = Kanvas(1080, 1920, (246, 241, 232))
    k.gradasi_v(0, 330, [(0, (250, 236, 214)), (1, (246, 214, 178))])
    k.gradasi_v(330, 1920, [(0, (182, 216, 204)), (0.5, (146, 194, 181)), (1, (66, 136, 126))])
    t0 = time.time()
    teks = spr_text("MEGALODON", (24, 24, 31), F_BOLD, 96, tracking=2, shadow=(255, 255, 255),
                    shadow_blur=0, shadow_off=(0, 0), shadow_a=0)
    print("spr_text 96px:", teks.shape, f"{(time.time()-t0)*1000:.1f} ms")
    blit(k.a, teks, 60, 120)
    hiu = raster(600, 240, lambda p: (p.ell(0, 60, 600, 200, fill=(38, 74, 82)),
                                      p.poly([(470, 110), (600, 40), (585, 150)], fill=(38, 74, 82))))
    for i in range(60):
        sw = swim(hiu, amp=12, lam=240, phase=i * 0.4)
        f = k.a.copy()
        blit(f, sw, 200 + i * 2, 700)
        blit(f, np.flipud(sw), 200, 1100, 0.4)
    t1 = time.time()
    N = 60
    for i in range(N):
        sw = swim(hiu, amp=12, lam=240, phase=i * 0.4)
        f = k.a.copy()
        blit(f, sw, 200, 700)
    print(f"60 frame (salin+swim+blit): {(time.time()-t1)/N*1000:.2f} ms/frame")
    P = Partikel(140, (0, 330, 1080, 1800), seed=2)
    t2 = time.time()
    for i in range(30):
        f = k.a.copy()
        P.gambar(f, i * 0.05)
    print(f"partikel 140: {(time.time()-t2)/30*1000:.2f} ms/frame")
    lut = lut_grade()
    t3 = time.time()
    for i in range(20):
        g = cv2.LUT(k.a, lut)
    print(f"grade LUT: {(time.time()-t3)/20*1000:.2f} ms")
    k.tempel(teks, 60, 120)
    Image.fromarray(k.a).save("/tmp/v18_selftest.png")
    print("selftest -> /tmp/v18_selftest.png")


if __name__ == "__main__":
    _selftest()
