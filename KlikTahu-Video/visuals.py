"""
visuals.py — primitif gambar & gerak untuk KlikTahu Video Engine.

Prinsip: setiap fungsi murni dan deterministik. Diberi `t` yang sama, hasilnya
selalu sama, sehingga frame bisa dirender ulang kapan pun tanpa drift dan tanpa
menyimpan frame ke disk (hemat disk, hemat RAM).
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
FONT_FILES = {
    "Black": "Poppins-ExtraBold.ttf",
    "Bold": "Poppins-Bold.ttf",
    "Semi": "Poppins-SemiBold.ttf",
    "Medium": "Poppins-Medium.ttf",
}

RGB = tuple[int, int, int]


# --------------------------------------------------------------------------- #
#  Easing & matematika
# --------------------------------------------------------------------------- #
def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if x < lo else hi if x > hi else x


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def norm(t: float, start: float, end: float) -> float:
    """Normalisasi `t` ke 0..1 di dalam rentang [start, end]."""
    if end <= start:
        return 1.0 if t >= end else 0.0
    return clamp((t - start) / (end - start))


def smoothstep(x: float) -> float:
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out_cubic(x: float) -> float:
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_cubic(x: float) -> float:
    return clamp(x) ** 3


def ease_out_quint(x: float) -> float:
    x = clamp(x)
    return 1 - (1 - x) ** 5


def ease_out_expo(x: float) -> float:
    x = clamp(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def ease_in_out_cubic(x: float) -> float:
    x = clamp(x)
    return 4 * x**3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_back(x: float, s: float = 1.70158) -> float:
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def ease_out_elastic(x: float) -> float:
    x = clamp(x)
    if x in (0.0, 1.0):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1


def pulse(t: float, period: float, sharpness: float = 2.0) -> float:
    """Denyut periodik 0..1 (1 pada awal tiap periode)."""
    p = (t % period) / period
    return (1 - p) ** sharpness


def bezier(p0, p1, p2, p3, n: int = 64):
    """Sampling kurva bezier kubik -> list[(x, y)]."""
    ts = np.linspace(0.0, 1.0, n)
    omt = 1 - ts
    x = omt**3 * p0[0] + 3 * omt**2 * ts * p1[0] + 3 * omt * ts**2 * p2[0] + ts**3 * p3[0]
    y = omt**3 * p0[1] + 3 * omt**2 * ts * p1[1] + 3 * omt * ts**2 * p2[1] + ts**3 * p3[1]
    return list(zip(x.tolist(), y.tolist()))


def bezier_point(p0, p1, p2, p3, t: float):
    omt = 1 - t
    x = omt**3 * p0[0] + 3 * omt**2 * t * p1[0] + 3 * omt * t**2 * p2[0] + t**3 * p3[0]
    y = omt**3 * p0[1] + 3 * omt**2 * t * p1[1] + 3 * omt * t**2 * p2[1] + t**3 * p3[1]
    return x, y


def mix_rgb(a: RGB, b: RGB, t: float) -> RGB:
    return tuple(int(round(lerp(a[i], b[i], clamp(t)))) for i in range(3))


# --------------------------------------------------------------------------- #
#  Font
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=None)
def font(weight: str = "Bold", size: int = 64) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / FONT_FILES[weight]), int(size))


def tracked_width(text: str, fnt: ImageFont.FreeTypeFont, tracking: float) -> float:
    return sum(fnt.getlength(c) for c in text) + tracking * max(0, len(text) - 1)


# --------------------------------------------------------------------------- #
#  Tekstur latar
# --------------------------------------------------------------------------- #
def vertical_gradient(size: tuple[int, int], stops) -> Image.Image:
    """`stops` = [(posisi 0..1, (r,g,b)), ...] -> gambar gradien vertikal."""
    w, h = size
    pos = np.array([s[0] for s in stops], dtype=np.float64)
    cols = np.array([s[1] for s in stops], dtype=np.float64)
    ys = np.linspace(0.0, 1.0, h)
    chans = [np.interp(ys, pos, cols[:, c]) for c in range(3)]
    col = np.stack(chans, axis=1).astype(np.uint8)          # (h, 3)
    arr = np.repeat(col[:, None, :], w, axis=1)             # (h, w, 3)
    return Image.fromarray(arr, "RGB")


def radial_glow(size: tuple[int, int], color: RGB, power: float = 2.4,
                peak: float = 1.0, scale: tuple[float, float] = (1.0, 1.0),
                quality: int = 4) -> Image.Image:
    """Sprite cahaya radial RGBA (dibuat kecil lalu diperbesar -> cepat)."""
    w, h = max(8, size[0] // quality), max(8, size[1] // quality)
    ys, xs = np.mgrid[0:h, 0:w]
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = np.sqrt(((xs - cx) / (w / 2 * scale[0])) ** 2 + ((ys - cy) / (h / 2 * scale[1])) ** 2)
    a = np.clip(1.0 - d, 0.0, 1.0) ** power * peak
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = color
    rgba[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA").resize(size, Image.BICUBIC)


def dotted_grid(size: tuple[int, int], step: int = 54, radius: float = 1.6,
                color: RGB = (150, 180, 255), alpha: int = 26) -> Image.Image:
    """Grid titik halus — memberi kesan 'presisi teknis' pada latar."""
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = radius
    for y in range(0, h + step, step):
        for x in range(0, w + step, step):
            a = int(alpha * (0.45 + 0.55 * (x / w) * (y / h) * 2))
            d.ellipse([x - r, y - r, x + r, y + r], fill=color + (min(alpha, a),))
    return img


def vignette(size: tuple[int, int], strength: float = 0.55,
             power: float = 2.2) -> Image.Image:
    w, h = size
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    d = np.sqrt(((xs - cx) / cx) ** 2 + ((ys - cy) / cy) ** 2) / math.sqrt(2)
    a = np.clip(d, 0, 1) ** power * strength
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


@lru_cache(maxsize=2)
def grain_stack(count: int, size: tuple[int, int], amplitude: int, seed: int = 7):
    """Tumpukan grain film (siap dipakai ImageChops.add offset=-128)."""
    rng = np.random.default_rng(seed)
    w, h = size
    out = []
    for i in range(count):
        n = rng.integers(-amplitude, amplitude + 1, (h, w, 3), dtype=np.int16).astype(np.int16)
        n = np.asarray(Image.fromarray((n + 128).astype(np.uint8), "RGB")
                       .filter(ImageFilter.GaussianBlur(0.4)))
        out.append(Image.fromarray(n, "RGB"))
    return tuple(out)


# --------------------------------------------------------------------------- #
#  Sprite teks
# --------------------------------------------------------------------------- #
def text_sprite(text: str, fnt: ImageFont.FreeTypeFont, color: RGB,
                pad: int = 28, shadow: bool = True, shadow_alpha: int = 170,
                glow: RGB | None = None, glow_alpha: int = 120,
                stroke: int = 0, stroke_fill: RGB = (0, 0, 0),
                baseline: bool = True) -> Image.Image:
    """
    Render satu kata menjadi sprite RGBA (bayangan + glow di-bake agar murah
    saat render). Sprite memakai anchor baseline supaya semua kata duduk rata
    pada garis yang sama walau tinggi hurufnya berbeda.
    """
    ascent, descent = fnt.getmetrics()
    adv = fnt.getlength(text)
    w = int(math.ceil(adv)) + pad * 2 + stroke * 2
    h = int(math.ceil(ascent + descent)) + pad * 2 + stroke * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bx, by = pad + stroke, pad + stroke

    if glow is not None:
        halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(halo).text((bx, by), text, font=fnt, fill=glow + (glow_alpha,),
                                  anchor="la", stroke_width=stroke, stroke_fill=glow + (glow_alpha,))
        img = Image.alpha_composite(img, halo.filter(ImageFilter.GaussianBlur(18)))

    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((bx + 4, by + 7), text, font=fnt, fill=(4, 6, 16, shadow_alpha),
                                anchor="la", stroke_width=stroke, stroke_fill=(4, 6, 16, shadow_alpha))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(9)))

    d = ImageDraw.Draw(img)
    d.text((bx, by), text, font=fnt, fill=color + (255,), anchor="la",
           stroke_width=stroke, stroke_fill=stroke_fill + (255,))
    _ = descent
    return img


def strike_sprite(width: int, height: int, color: RGB, thickness: int = 9,
                  alpha: int = 235, angle: float = -3.0) -> Image.Image:
    """Garis coret (untuk kata yang 'dibuang' — mis. DI-SKIP)."""
    img = Image.new("RGBA", (width + 40, height + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dy = math.tan(math.radians(angle)) * width / 2
    d.line([(20, 20 + height / 2 + dy), (20 + width, 20 + height / 2 - dy)],
           fill=color + (alpha,), width=thickness)
    return img


def tracked_sprite(text: str, fnt: ImageFont.FreeTypeFont, color: RGB,
                   tracking: float = 8.0, pad: int = 20) -> Image.Image:
    """Teks dengan jarak antar-huruf (wordmark)."""
    w = int(math.ceil(tracked_width(text, fnt, tracking))) + pad * 2
    ascent, descent = fnt.getmetrics()
    h = int(ascent + descent) + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = pad
    for ch in text:
        d.text((x, pad), ch, font=fnt, fill=color + (255,), anchor="la")
        x += fnt.getlength(ch) + tracking
    return img


class WordBlock:
    """
    Blok teks kinetik.

    Setiap kata punya sprite sendiri sehingga bisa muncul, membesar, menyala,
    atau dicoret secara mandiri — sinkron dengan suara (word-synced typography).
    """

    def __init__(self, lines, anchor, max_width: int = 950, max_height: int = 900,
                 weight: str = "Black", size: int = 96, min_size: int = 46,
                 color: RGB = (240, 244, 255), accent: RGB = (255, 190, 60),
                 align: str = "center", line_gap: float = 1.16,
                 glow: bool = True, max_scale_hint: float = 1.0):
        self.lines = [ln.split() for ln in lines]
        self.words = [w for ln in self.lines for w in ln]
        self.anchor = anchor
        self.align = align
        self.color = color
        self.accent = accent
        self.line_gap = line_gap

        size = self._fit(lines, weight, size, min_size, max_width, max_height)
        self.size = size
        self.fnt = font(weight, size)
        ascent, descent = self.fnt.getmetrics()
        self.line_h = int((ascent + descent) * line_gap)

        pad = 36
        self.pad = pad
        self.sprites: list[dict] = []
        self.geom: list[tuple[float, float, float]] = []   # (pen-x rel. tepi baris, 0, advance)

        space = self.fnt.getlength(" ") * 1.02
        self.space = space
        self.row_w: list[float] = []
        for line in self.lines:
            widths = [self.fnt.getlength(w) for w in line]
            self.row_w.append(sum(widths) + space * max(0, len(line) - 1))
            x = 0.0
            for w, adv in zip(line, widths):
                sp = {
                    "normal": text_sprite(w, self.fnt, color, pad=pad, glow=None),
                    "accent": text_sprite(w, self.fnt, accent, pad=pad,
                                          glow=accent if glow else None),
                }
                self.sprites.append(sp)
                self.geom.append((x, 0.0, adv))
                x += adv + space

        self._row_of = []
        for r, line in enumerate(self.lines):
            self._row_of.extend([r] * len(line))

        self.total_h = self.line_h * len(self.lines)

    @staticmethod
    def _fit(lines, weight, size, min_size, max_width, max_height) -> int:
        for s in range(int(size), int(min_size) - 1, -2):
            f = font(weight, s)
            sp_w = f.getlength(" ") * 1.02
            widest = max(sum(f.getlength(w) for w in ln.split())
                         + sp_w * max(0, len(ln.split()) - 1) for ln in lines)
            ascent, descent = f.getmetrics()
            height = (ascent + descent) * 1.16 * len(lines)
            if widest <= max_width and height <= max_height:
                return s
        return int(min_size)

    # -- geometri ---------------------------------------------------------- #
    def row_left_edge(self, row: int, ax: float) -> float:
        total = self.row_w[row]
        if self.align == "center":
            return ax - total / 2
        if self.align == "right":
            return ax - total
        return ax

    def row_start(self, row: int) -> int:
        return sum(len(l) for l in self.lines[:row])

    def block_height(self) -> float:
        return self.total_h

    # -- render ------------------------------------------------------------ #
    def draw(self, ov: Image.Image, t: float, times, style: str = "reveal",
             active_index: int | None = None, scale_active: float = 1.07,
             strike: set[int] | None = None, persist: set[int] | None = None,
             offset=(0.0, 0.0)):
        """
        Tempel blok ke layer `ov` (RGBA) untuk waktu lokal `t`.

        `times`  : waktu onset tiap kata (detik, lokal beat).
        `style`  : "reveal"    -> kata muncul satu per satu mengikuti suara
                   "highlight" -> semua kata tampil, kata aktif menyala
        """
        strike = strike or set()
        persist = persist or set()
        ax, ay = self.anchor[0] + offset[0], self.anchor[1] + offset[1]
        ascent = self.fnt.getmetrics()[0]
        top = ay - self.total_h / 2

        for i, spr in enumerate(self.sprites):
            onset = times[i] if i < len(times) else 0.0
            local = t - onset
            if style == "reveal" and local < 0:
                continue
            appear = ease_out_back(clamp(local / 0.20), 1.9) if local < 0.20 else 1.0
            alpha = clamp(local / 0.14) if local < 0.14 else 1.0
            is_active = (active_index == i)
            key = "accent" if (is_active or i in persist) else "normal"
            img = spr[key]
            scale = 1.0 + 0.16 * (1 - appear)
            if is_active and style == "highlight":
                scale *= scale_active
                if local > 0.3:
                    scale *= 1.0 + 0.012 * math.sin((local - 0.3) * 9.0)

            row = self._row_of[i]
            px = self.row_left_edge(row, ax) + self.geom[i][0] - self.pad
            py = top + row * self.line_h - self.pad

            if abs(scale - 1.0) > 1e-3:
                nw, nh = max(2, int(img.width * scale)), max(2, int(img.height * scale))
                img = img.resize((nw, nh), Image.BILINEAR)
                px -= (nw - spr[key].width) / 2
                py -= (nh - spr[key].height) / 2
                if is_active and style == "highlight":
                    py -= 6
            if alpha < 1.0:
                img = img.copy()
                img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))

            ov.paste(img, (int(px), int(py)), img)

            if i in strike:
                width = int(self.geom[i][2]) + 30
                thickness = max(6, self.size // 11)
                line = strike_sprite(width, int(self.size * 0.78), (255, 92, 110),
                                     thickness=thickness)
                ov.paste(line, (int(px) + self.pad - 15,
                                int(py) + self.pad + int(ascent * 0.30)), line)


# --------------------------------------------------------------------------- #
#  Komponen grafis kecil
# --------------------------------------------------------------------------- #
def rounded_panel(size, radius: int, fill, outline=None, width: int = 3, alpha: int = 255):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    box = [0, 0, size[0] - 1, size[1] - 1]
    d.rounded_rectangle(box, radius=radius, fill=fill + (alpha,),
                        outline=outline + (255,) if outline else None, width=width)
    return img


def glow_bar(size, frac: float, radius: int, fg: RGB, bg: RGB = (255, 255, 255),
             bg_alpha: int = 40) -> Image.Image:
    """Bar progres (dipakai untuk retention / progress video)."""
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=bg + (bg_alpha,))
    fw = int(clamp(frac) * w)
    if fw > 2:
        d.rounded_rectangle([0, 0, max(2, fw), h - 1], radius=radius, fill=fg + (255,))
    return img


def dashed_line(d: ImageDraw.ImageDraw, p0, p1, dash: float = 18, gap: float = 14,
                width: int = 4, fill=(255, 255, 255, 120)):
    x0, y0 = p0
    x1, y1 = p1
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 1:
        return
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    pos = 0.0
    while pos < length:
        seg = min(dash, length - pos)
        d.line([(x0 + ux * pos, y0 + uy * pos), (x0 + ux * (pos + seg), y0 + uy * (pos + seg))],
               fill=fill, width=width)
        pos += dash + gap


def arrow_head(d: ImageDraw.ImageDraw, tip, angle: float, size: float, fill):
    a = math.radians(angle)
    left = (tip[0] - size * math.cos(a - 0.45), tip[1] - size * math.sin(a - 0.45))
    right = (tip[0] - size * math.cos(a + 0.45), tip[1] - size * math.sin(a + 0.45))
    d.polygon([tip, left, right], fill=fill)


def arc_ring(d: ImageDraw.ImageDraw, center, radius: float, start: float, end: float,
             width: int, fill):
    box = [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius]
    d.arc(box, start=start, end=end, fill=fill, width=width)


def stroke_curve(d: ImageDraw.ImageDraw, points, color, width: int, closed: bool = False):
    d.line(points, fill=color, width=width, joint="curve")
    if closed:
        d.line([points[-1], points[0]], fill=color, width=width, joint="curve")


def prerender_glow(size, draw_fn, blur: float = 20, quality: int = 3,
                   gain: float = 1.0) -> Image.Image:
    """
    Sprite halo ber-blur, dibuat SEKALI saat inisialisasi.

    Digambar kecil (1/quality), diblur kecil, lalu diperbesar — biaya mahal
    hanya dibayar sekali, bukan tiap frame. `draw_fn(draw, k)` menggambar pada
    kanvas kecil, dengan `k` sebagai pengali koordinat (k = 1/quality).
    """
    w, h = max(2, int(size[0] // quality)), max(2, int(size[1] // quality))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(img), 1.0 / quality)
    img = img.filter(ImageFilter.GaussianBlur(max(0.8, blur / quality)))
    if gain != 1.0:
        img.putalpha(img.getchannel("A").point(lambda v: min(255, int(v * gain))))
    return img.resize((int(size[0]), int(size[1])), Image.BICUBIC)


def add_glow_layer(base: Image.Image, layer: Image.Image, blur: float = 18,
                   gain: float = 1.0) -> Image.Image:
    """Tempel `layer` beserta halo blur-nya (untuk efek neon)."""
    halo = layer.filter(ImageFilter.GaussianBlur(blur))
    if gain != 1.0:
        a = halo.getchannel("A").point(lambda v: min(255, int(v * gain)))
        halo.putalpha(a)
    base.alpha_composite(halo)
    base.alpha_composite(layer)
    return base
