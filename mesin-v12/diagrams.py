#!/usr/bin/env python3
"""Diagram gerak penuh layar untuk KlikTahu (menggantikan tumpukan kartu teks).

Tiap fungsi menggambar satu adegan penjelas: potongan melintang bumi, penggaris
kedalaman, gelombang merambat, dsb. Teks dibuat minimal — narasi yang menjelaskan,
gambar yang menunjukkan.

Dipakai oleh render.py lewat kunci `visual` pada content.json.
"""
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
FDIR = os.path.join(BASE, "fonts")
W, H = 1080, 1920
SS = 1.5

CREAM = (246, 241, 232)
INK = (24, 24, 31)
MUTED = (128, 122, 114)
WHITE = (255, 255, 255)
RED = (192, 57, 43)
BLUE = (47, 111, 181)
GREEN = (46, 125, 79)
PURPLE = (122, 63, 196)
AMBER = (194, 118, 27)

FB, FS, FM, FR = "Poppins-Bold.ttf", "Poppins-SemiBold.ttf", "Poppins-Medium.ttf", "Poppins-Regular.ttf"
_F = {}

# --- audit presisi: setiap elemen teks/pil dicatat kotaknya --------------------
# Dipakai check_layout.py: "teks apa yang menyentuh margin aman?" dijawab pasti,
# tanpa menebak dari piksel. TRACK hanya menyala saat audit (nol biaya saat render).
TRACK = False
LAYOUT = []


def _note(kind, x0, y0, x1, y1, text):
    if TRACK:
        LAYOUT.append({"kind": kind, "x0": round(x0, 1), "y0": round(y0, 1),
                       "x1": round(x1, 1), "y1": round(y1, 1), "text": text[:42]})


def S(v):
    return v * SS


TSCALE = float(os.environ.get("KT_TSCALE", "1.16"))    # semua teks diagram diperbesar


def font(name, size):
    k = (name, round(size, 1), round(SS, 3))
    if k not in _F:
        _F[k] = ImageFont.truetype(os.path.join(FDIR, name),
                                   max(8, int(round(size * SS * TSCALE))))
    return _F[k]


def tw(text, f):
    return f.getlength(text) / SS


def tlh(f):
    return (f.getbbox("Hg")[3] - f.getbbox("Hg")[1]) / SS * 1.34


def clamp(v, a=0.0, b=1.0):
    return a if v < a else (b if v > b else v)


def eo(t):
    t = clamp(t); return 1 - (1 - t) ** 3


def eio(t):
    t = clamp(t); return t * t * (3 - 2 * t)


def eob(t, c1=1.35):
    t = clamp(t); return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2


def esmooth(t):
    """Easing sangat halus (smootherstep): tanpa sentakan di awal dan akhir."""
    t = clamp(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


def espring(t, k=6.2, f=9.0):
    """Easing pegas: sedikit melewati batas lalu mendarat halus (terasa hidup)."""
    t = clamp(t)
    if t >= 1.0:
        return 1.0
    return 1 - math.exp(-k * t) * math.cos(f * t)


def amb(t, f=0.25, amp=1.0, ph=0.0):
    """Getaran ambient lambat supaya elemen tidak terlihat beku."""
    return amp * math.sin(t * f * 2 * math.pi + ph)


def seg(t, a, b):
    return clamp((t - a) / max(1e-6, b - a))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if tw(t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w_
    if cur:
        lines.append(cur)
    return lines


# ---------- lapisan & bentuk dasar (versi lokal, agar modul berdiri sendiri) ----------
def _layer(img):
    return Image.new("RGBA", img.size, (0, 0, 0, 0))


def _put(img, lay, alpha=1.0):
    if alpha >= 0.995:
        img.paste(lay, (0, 0), lay)
    else:
        a = lay.getchannel("A").point(lambda v: int(v * clamp(alpha)))
        img.paste(lay.convert("RGB"), (0, 0), a)


_STAGE = {}


def _stage(img, cx, cy, rx, ry, col, alpha=1.0):
    """Nuansa cahaya lembut (gradasi elips) — pengganti kotak panel transparan."""
    if alpha <= 0.01 or rx < 6 or ry < 6:
        return
    rx, ry = int(round(rx)), int(round(ry))
    key = (rx, ry, col)
    lay = _STAGE.get(key)
    if lay is None:
        w_, h_ = int(S(2 * rx)) + 4, int(S(2 * ry)) + 4
        lay = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay, "RGBA")
        n = 24
        for i in range(n, 0, -1):
            k = i / float(n)
            a = int(255 * 0.075)
            dd.ellipse([S(rx) * (1 - k) + 2, S(ry) * (1 - k) + 2,
                        S(rx) * (1 + k) + 2, S(ry) * (1 + k) + 2], fill=col + (a,))
        _STAGE[key] = lay
    _put_at(img, lay, int(S(cx)) - lay.width // 2, int(S(cy)) - lay.height // 2, alpha)


def _stage_rect(img, x0, y0, x1, y1, radius=0, color=None, alpha=1.0, outline=None, width=3):
    """Bekas kotak panel: kini jadi nuansa lembut (tanpa kotak)."""
    if color is None or alpha <= 0.01:
        return
    _stage(img, (x0 + x1) / 2.0, (y0 + y1) / 2.0, (x1 - x0) / 2.0 * 1.04, (y1 - y0) / 2.0 * 1.10,
           color, alpha * 0.6)


def _box(img, x0, y0, x1, y1, pad=8):
    """Kotak piksel (sudah dikali SS) yang dijepit ke dalam kanvas."""
    X0 = max(0, int(S(x0)) - pad)
    Y0 = max(0, int(S(y0)) - pad)
    X1 = min(img.width, int(S(x1)) + pad + 1)
    Y1 = min(img.height, int(S(y1)) + pad + 1)
    if X1 <= X0 or Y1 <= Y0:
        return None
    return X0, Y0, X1, Y1


def _put_at(img, lay, X0, Y0, alpha=1.0):
    if alpha >= 0.995:
        img.paste(lay, (X0, Y0), lay)
    else:
        a = lay.getchannel("A").point(lambda v: int(v * clamp(alpha)))
        img.paste(lay.convert("RGB"), (X0, Y0), a)


def paste_c(img, cx, cy, text, f, fill, alpha=1.0, scale=1.0, dy=0.0):
    if alpha <= 0.01 or not text:
        return
    w_ = tw(text, f)
    h_ = tlh(f)
    _note("teks-c", cx - w_ / 2, cy + dy - h_ / 2, cx + w_ / 2, cy + dy + h_ / 2, text)
    lay = Image.new("RGBA", (int(S(w_ + 40)), int(S(h_ * 1.7))), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    dd.text((lay.width / 2, lay.height / 2), text, font=f, fill=fill + (255,), anchor="mm")
    if scale != 1.0:
        lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.LANCZOS)
    # v12 fix (15 Okt 2026): alpha dulu diabaikan -> teks label "pop" alih-alih memudar; kini diterapkan
    m = lay if alpha >= 0.995 else lay.getchannel("A").point(lambda v: int(v * clamp(alpha)))
    img.paste(lay.convert("RGB") if alpha < 0.995 else lay, (int(S(cx) - lay.width / 2), int(S(cy + dy) - lay.height / 2)), m)


def paste_r(img, x, cy, text, f, fill, alpha=1.0, dy=0.0):
    if alpha <= 0.01 or not text:
        return
    w_ = tw(text, f)
    h_ = tlh(f)
    _note("teks-r", x, cy + dy - h_ / 2, x + w_, cy + dy + h_ / 2, text)
    lay = Image.new("RGBA", (int(S(w_ + 20)), int(S(h_ * 1.7))), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    dd.text((0, lay.height / 2), text, font=f, fill=fill + (255,), anchor="lm")
    m = lay if alpha >= 0.995 else lay.getchannel("A").point(lambda v: int(v * clamp(alpha)))
    img.paste(lay.convert("RGB") if alpha < 0.995 else lay, (int(S(x)), int(S(cy + dy) - lay.height / 2)), m)


def pill(img, x, y, text, f, fill, outline=None, bg=None, alpha=1.0, pad=30, hgt=None, dot=False):
    """Chip berisi teks. x = kiri, y = tengah."""
    if alpha <= 0.01:
        return 0
    hgt = hgt or 56
    dotw = 26 if dot else 0
    w_ = tw(text, f) + pad * 2 + dotw
    _note("pil", x, y - hgt / 2, x + w_, y + hgt / 2, text)
    lay = Image.new("RGBA", (int(S(w_)) + 4, int(S(hgt)) + 4), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([2, 2, int(S(w_)) + 2, int(S(hgt)) + 2], radius=S(hgt / 2),
                         fill=(fill + (255,)) if bg is None else (bg + (255,)),
                         outline=(outline + (255,)) if outline else None,
                         width=max(1, int(S(2.4))))
    if dot:
        dd.ellipse([S(pad - 6), S(hgt / 2 - 7), S(pad + 8), S(hgt / 2 + 7)], fill=outline or fill)
    dd.text((S(pad + dotw), S(hgt / 2)), text, font=f,
            fill=(fill + (255,)) if bg is not None else (WHITE + (255,)), anchor="lm")
    if alpha >= 0.995:
        img.paste(lay, (int(S(x)), int(S(y - hgt / 2))), lay)
    else:
        a = lay.getchannel("A").point(lambda v: int(v * clamp(alpha)))
        img.paste(lay.convert("RGB"), (int(S(x)), int(S(y - hgt / 2))), a)
    return w_


PANEL_LEMBUT = True   # v2026: bayangan ambient lembut pada panel


def panel(img, x0, y0, x1, y1, alpha=1.0, radius=54, shadow=True, fill=WHITE, outline=None, dx=0.0, dy=0.0):
    """Kartu putih dengan bayangan keras (bahasa visual KlikTahu)."""
    if alpha <= 0.01:
        return
    x0, x1, y0, y1 = x0 + dx, x1 + dx, y0 + dy, y1 + dy
    if shadow and PANEL_LEMBUT:
        # v2026: bayangan ambient lembut di bawah bayangan keras (kedalaman seperti UI modern)
        import mesin_fx as _fx
        wv, hv = int(S(x1 - x0)), int(S(y1 - y0))
        if wv > 8 and hv > 8:
            bm, bp = _fx._bayang_rr(wv, hv, S(radius), max(4.0, S(22)), 0.20)
            m = bm if alpha >= 0.995 else bm.point(lambda v: int(v * clamp(alpha)))
            img.paste(mix(CREAM, INK, 0.62), (int(S(x0)) - bp, int(S(y0 + 16)) - bp, int(S(x0)) - bp + bm.width,
                                             int(S(y0 + 16)) - bp + bm.height), m)
    pad = 26
    lay = Image.new("RGBA", (int(S(x1 - x0 + pad * 2)), int(S(y1 - y0 + pad * 2))), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    if shadow:
        dd.rounded_rectangle([S(pad + 9), S(pad + 11), S(pad + (x1 - x0) + 9), S(pad + (y1 - y0) + 11)],
                             radius=S(radius), fill=mix(CREAM, INK, 0.30) + (255,))
    dd.rounded_rectangle([S(pad), S(pad), S(pad + (x1 - x0)), S(pad + (y1 - y0))], radius=S(radius),
                         fill=fill + (255,), outline=(outline + (255,)) if outline else mix(CREAM, INK, 0.12) + (255,),
                         width=max(1, int(S(2.2))))
    if alpha >= 0.995:
        img.paste(lay, (int(S(x0 - pad)), int(S(y0 - pad))), lay)
    else:
        a = lay.getchannel("A").point(lambda v: int(v * clamp(alpha)))
        img.paste(lay.convert("RGB"), (int(S(x0 - pad)), int(S(y0 - pad))), a)



def ell(img, x0, y0, x1, y1, fill=None, outline=None, width=3, alpha=1.0):
    """Elips ber-alpha dengan layer lokal."""
    if alpha <= 0.01:
        return
    bx = _box(img, x0 - width, y0 - width, x1 + width, y1 + width)
    if bx is None:
        return
    X0, Y0, X1b, Y1b = bx
    lay = Image.new("RGBA", (X1b - X0, Y1b - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    ox, oy = X0 / SS, Y0 / SS
    dd.ellipse([S(x0 - ox), S(y0 - oy), S(x1 - ox), S(y1 - oy)],
               fill=(fill + (255,)) if fill else None,
               outline=(outline + (255,)) if outline else None, width=max(1, int(S(width))))
    _put_at(img, lay, X0, Y0, alpha)


def rrect_on(img, x0, y0, x1, y1, radius, color, alpha=1.0, outline=None, width=3):
    """Kotak membulat ber-alpha dengan layer lokal."""
    if alpha <= 0.01:
        return
    bx = _box(img, x0 - width, y0 - width, x1 + width, y1 + width)
    if bx is None:
        return
    X0, Y0, X1b, Y1b = bx
    lay = Image.new("RGBA", (X1b - X0, Y1b - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    ox, oy = X0 / SS, Y0 / SS
    dd.rounded_rectangle([S(x0 - ox), S(y0 - oy), S(x1 - ox), S(y1 - oy)], radius=S(radius),
                         fill=color + (255,),
                         outline=(outline + (255,)) if outline else None, width=max(1, int(S(width))))
    _put_at(img, lay, X0, Y0, alpha)


def _phone(img, cx, cy, w, h, alpha=1.0, screen=WHITE, body=None):
    """HP sederhana: badan + layar."""
    if alpha <= 0.01:
        return
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 46,
             body or mix(CREAM, INK, 0.84), alpha)
    rrect_on(img, cx - w / 2 + 16, cy - h / 2 + 26, cx + w / 2 - 16, cy + h / 2 - 34, 34, screen, alpha)
    rrect_on(img, cx - 40, cy - h / 2 + 12, cx + 40, cy - h / 2 + 22, 6, mix(CREAM, INK, 0.55), alpha * 0.9)


def _bubble(img, cx, cy, w, h, color, alpha=1.0, right=True):
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, h / 2, color, alpha)
    for i in range(3):
        dot_on(img, cx + (i - 1) * 16, cy, 5, mix(color, WHITE, 0.6), alpha)


def _eye(img, cx, cy, r, color, tg, alpha=1.0):
    """Mata mengintip + pancaran."""
    if alpha <= 0.01:
        return
    ell(img, cx - r * 1.5, cy - r * 0.75, cx + r * 1.5, cy + r * 0.75,
        fill=mix(CREAM, WHITE, 0.5), outline=color, width=5, alpha=alpha)
    dot_on(img, cx, cy, r * 0.52, color, alpha)
    dot_on(img, cx, cy, r * 0.22, INK, alpha)
    for i in range(3):
        u = ((tg * 0.8) + i / 3) % 1.0
        ring_on(img, cx, cy, r * (1.7 + 1.5 * u), color, 4, alpha * (1 - u) * 0.6, squash=0.62)


def line_on(img, p1, p2, color, width, alpha=1.0, dash=None):
    if alpha <= 0.01:
        return
    wpad = width * 3 + 12
    bx = _box(img, min(p1[0], p2[0]) - wpad, min(p1[1], p2[1]) - wpad,
              max(p1[0], p2[0]) + wpad, max(p1[1], p2[1]) + wpad)
    if bx is None:
        return
    X0, Y0, X1, Y1 = bx
    lay = Image.new("RGBA", (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    ox, oy = X0 / SS, Y0 / SS
    p1 = (p1[0] - ox, p1[1] - oy)
    p2 = (p2[0] - ox, p2[1] - oy)
    if dash:
        (x1, y1), (x2, y2) = p1, p2
        L = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(L / dash))
        for i in range(n + 1):
            u1, u2 = i / n, min(1.0, i / n + 0.6 / n)
            dd.line([S(x1 + (x2 - x1) * u1), S(y1 + (y2 - y1) * u1),
                     S(x1 + (x2 - x1) * u2), S(y1 + (y2 - y1) * u2)],
                    fill=color + (255,), width=max(1, int(S(width))))
    else:
        dd.line([S(p1[0]), S(p1[1]), S(p2[0]), S(p2[1])], fill=color + (255,), width=max(1, int(S(width))))
    _put_at(img, lay, X0, Y0, alpha)


def dot_on(img, cx, cy, r, color, alpha=1.0, outline=None, width=3):
    if alpha <= 0.01 or r <= 0:
        return
    bx = _box(img, cx - r - width, cy - r - width, cx + r + width, cy + r + width)
    if bx is None:
        return
    X0, Y0, X1, Y1 = bx
    lay = Image.new("RGBA", (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    ox, oy = X0 / SS, Y0 / SS
    dd.ellipse([S(cx - ox - r), S(cy - oy - r), S(cx - ox + r), S(cy - oy + r)], fill=color + (255,),
               outline=(outline + (255,)) if outline else None, width=max(1, int(S(width))))
    _put_at(img, lay, X0, Y0, alpha)


def ring_on(img, cx, cy, r, color, width, alpha=1.0, squash=1.0):
    if alpha <= 0.01 or r <= 1:
        return
    ry = r * squash
    bx = _box(img, cx - r - width, cy - ry - width, cx + r + width, cy + ry + width)
    if bx is None:
        return
    X0, Y0, X1, Y1 = bx
    lay = Image.new("RGBA", (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    ox, oy = X0 / SS, Y0 / SS
    dd.ellipse([S(cx - ox - r), S(cy - oy - ry), S(cx - ox + r), S(cy - oy + ry)],
               outline=color + (255,), width=max(1, int(S(width))))
    _put_at(img, lay, X0, Y0, alpha)


def poly_on(img, pts, color, alpha=1.0, outline=None, width=3):
    if alpha <= 0.01 or not pts:
        return
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    bx = _box(img, min(xs) - width, min(ys) - width, max(xs) + width, max(ys) + width)
    if bx is None:
        return
    X0, Y0, X1, Y1 = bx
    lay = Image.new("RGBA", (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    ox, oy = X0 / SS, Y0 / SS
    dd.polygon([(S(x - ox), S(y - oy)) for x, y in pts], fill=color + (255,),
               outline=(outline + (255,)) if outline else None)
    _put_at(img, lay, X0, Y0, alpha)


def star4(img, cx, cy, r, color, alpha=1.0):
    if alpha <= 0.01 or r <= 0.5:
        return
    pts = []
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 4
        rr = r if i % 2 == 0 else r * 0.34
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    poly_on(img, pts, color, alpha)


def rot_pts(pts, cx, cy, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


# ---------- pola visual yang dipakai berulang ----------
def badge_line(img, text, accent, tl, al, y=470):
    q = seg(tl, 0.10, 0.42)
    if q <= 0:
        return
    f = font(FS, 32)
    k = eob(q)
    pill(img, 110, y, text, f, mix(accent, INK, 0.12), outline=accent, bg=mix(WHITE, accent, 0.10),
         alpha=q * al, dot=True, hgt=56 * (0.9 + 0.1 * k))


def skyline(img, x0, x1, ground, color, alpha=1.0, seed=7, scale=1.0):
    """Siluet gedung kecil di permukaan (memberi skala & konteks kota)."""
    if alpha <= 0.01:
        return
    bx = _box(img, x0, ground - 260 * scale, x1, ground + 6)
    if bx is None:
        return
    X0, Y0, X1, Y1 = bx
    lay = Image.new("RGBA", (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    x = x0 - X0 / SS
    ground = ground - Y0 / SS
    x1 = x1 - X0 / SS
    i = 0
    while x < x1:
        w_ = (34 + ((seed * (i + 3) * 17) % 46)) * scale
        h_ = (40 + ((seed * (i + 5) * 29) % 118)) * scale
        w_ = min(w_, x1 - x)
        dd.rectangle([S(x), S(ground - h_), S(x + w_), S(ground)], fill=color + (255,))
        for j in range(int(h_ / 34)):
            for k in range(max(1, int(w_ / 26))):
                if (i + j + k) % 3 == 0:
                    wx, wy = x + 8 + k * 26, ground - h_ + 12 + j * 34
                    if wx + 9 < x + w_ - 4 and wy + 12 < ground - 4:
                        dd.rectangle([S(wx), S(wy), S(wx + 9), S(wy + 12)], fill=mix(CREAM, color, 0.55) + (255,))
        x += w_ + (10 + ((seed * (i + 11) * 13) % 22)) * scale
        i += 1
    _put_at(img, lay, X0, Y0, alpha)


def house(img, cx, ground, s, color, tilt=0.0, alpha=1.0, roof=None):
    """Rumah sederhana, bisa dimiringkan (untuk menunjukkan guncangan)."""
    if alpha <= 0.01:
        return
    body = [(cx - s * 0.5, ground), (cx + s * 0.5, ground), (cx + s * 0.5, ground - s * 0.62),
            (cx - s * 0.5, ground - s * 0.62)]
    roofp = [(cx - s * 0.60, ground - s * 0.60), (cx + s * 0.60, ground - s * 0.60), (cx, ground - s * 1.02)]
    body = rot_pts(body, cx, ground, tilt)
    roofp = rot_pts(roofp, cx, ground, tilt + 0.6)
    poly_on(img, body, color, alpha)
    poly_on(img, roofp, roof or mix(color, INK, 0.25), alpha)
    win = [(cx - s * 0.26, ground - s * 0.48), (cx - s * 0.02, ground - s * 0.48),
           (cx - s * 0.02, ground - s * 0.24), (cx - s * 0.26, ground - s * 0.24)]
    poly_on(img, rot_pts(win, cx, ground, tilt), mix(CREAM, WHITE, 0.6), alpha)


def waves(img, cx, cy, tg, n=5, period=1.5, rmax=240, color=RED, width=5, alpha=1.0,
          squash=1.0, up_only=False):
    """Gelombang mengembang dari titik gempa."""
    if alpha <= 0.01:
        return
    for i in range(n):
        u = ((tg / period) + i / n) % 1.0
        r = 24 + (rmax - 24) * eo(u)
        a = (1 - u) ** 1.4
        if a <= 0.02:
            continue
        if up_only:
            lay = _layer(img)
            dd = ImageDraw.Draw(lay)
            box = [S(cx - r), S(cy - r * squash), S(cx + r), S(cy + r * squash)]
            dd.arc(box, 180, 360, fill=color + (int(255 * a) if False else 255,), width=max(1, int(S(width))))
            _put(img, lay, alpha * a)
        else:
            ring_on(img, cx, cy, r, color, width, alpha * a, squash)


def depth_scale(y0, y1, km_max):
    """Konversi km -> pixel untuk potongan melintang."""
    def f(km):
        return y0 + (y1 - y0) * (km / km_max)
    return f


# ================= ADEGAN =================
def sc_intro(img, d, sc, tl, dur, tg, accent, al, dy):
    """Pembukaan: dua gempa berkekuatan sama, satu merusak, satu tidak."""
    # judul kinetik
    y = 470
    for i, l in enumerate(sc["lines"]):
        fsz = 150
        while fsz > 62 and tw(l, font(FB, fsz)) > 940:
            fsz -= 4
        f = font(FB, fsz)
        q = seg(tl, 0.05 + i * 0.22, 0.55 + i * 0.22)
        if q <= 0:
            continue
        k = eob(q)
        col = accent if i == 1 else INK
        paste_c(img, W / 2, y + (1 - k) * 40 + dy * 0.5, l, f, col, q * al, scale=0.9 + 0.1 * k)
        y += 150
    # panel dua gempa (isi digambar di dalam bingkai, animasi pakai alpha saja)
    qa = seg(tl, 0.85, 1.35)
    if qa > 0:
        panel(img, 70, 790, 1010, 1122, alpha=qa * al, radius=48)
        gnd = 1040
        line_on(img, (110, gnd), (970, gnd), mix(CREAM, INK, 0.35), 5, qa * al)
        star4(img, 330, gnd + 14, 15 + 3 * math.sin(tg * 9), RED, qa * al)
        waves(img, 330, gnd + 14, tg, n=4, period=1.0, rmax=138, color=RED, width=5,
              alpha=qa * al * 0.85, squash=0.40)
        house(img, 640, gnd, 88, mix(CREAM, INK, 0.72), tilt=6.5 * math.sin(tg * 11.0) * qa, alpha=qa * al)
        house(img, 786, gnd, 68, mix(CREAM, INK, 0.55), tilt=-5.0 * math.sin(tg * 12.4) * qa, alpha=qa * al)
        pill(img, 116, 852, "M 6,5 · KEDALAMAN 10 KM", font(FS, 30), mix(RED, INK, 0.10),
             outline=RED, bg=mix(WHITE, RED, 0.12), alpha=qa * al, pad=26, hgt=52)
        paste_c(img, 690, 1100, "guncangan keras di permukaan", font(FM, 28), mix(RED, INK, 0.28), qa * al)
    qb = seg(tl, 1.55, 2.05)
    if qb > 0:
        panel(img, 70, 1186, 1010, 1518, alpha=qb * al, radius=48)
        gnd = 1290
        line_on(img, (110, gnd), (970, gnd), mix(CREAM, INK, 0.35), 5, qb * al)
        star4(img, 330, 1448, 16 + 3 * math.sin(tg * 5), BLUE, qb * al)
        waves(img, 330, 1448, tg, n=3, period=2.1, rmax=142, color=BLUE, width=5,
              alpha=qb * al * 0.8, up_only=True)
        house(img, 640, gnd, 88, mix(CREAM, INK, 0.72), alpha=qb * al)
        house(img, 786, gnd, 68, mix(CREAM, INK, 0.55), alpha=qb * al)
        line_on(img, (330, gnd + 6), (330, 1436), mix(BLUE, CREAM, 0.40), 3, qb * al, dash=20)
        pill(img, 116, 1248, "M 6,5 · KEDALAMAN 368 KM", font(FS, 30), mix(BLUE, INK, 0.10),
             outline=BLUE, bg=mix(WHITE, BLUE, 0.12), alpha=qb * al, pad=26, hgt=52)
        paste_c(img, 690, 1496, "terasa luas, tapi tidak merusak", font(FM, 28),
                mix(BLUE, INK, 0.28), qb * al)
    q = seg(tl, 2.95, 3.55)
    if q > 0:
        k = eob(q)
        paste_c(img, W / 2, 1610 + (1 - k) * 26, "JAWABANNYA: KEDALAMAN",
                font(FB, 62), mix(accent, INK, 0.15), q * al, scale=0.92 + 0.08 * k)


def sc_cross(img, d, sc, tl, dur, tg, accent, al, dy):
    """Potongan melintang bumi: hiposentrum, episentrum, kedalaman."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.15, 0.62)
    if q <= 0:
        return
    dy2 = (1 - eio(q)) * 70
    al2 = q * al
    gnd = 760
    km = depth_scale(gnd, 1520, 420.0)
    # langit + kota
    skyline(img, 120, 960, gnd, mix(CREAM, INK, 0.30), al2 * 0.9, seed=5)
    line_on(img, (90, gnd), (990, gnd), mix(CREAM, INK, 0.55), 7, al2)
    paste_r(img, 96, gnd - 214, "PERMUKAAN BUMI", font(FM, 26), mix(CREAM, INK, 0.42), al2)
    # tanah berlapis + garis kedalaman
    for depth, lab in ((100, "100 km"), (200, "200 km"), (300, "300 km")):
        y = km(depth) + dy2
        line_on(img, (150, y), (930, y), mix(CREAM, INK, 0.16), 2, al2, dash=26)
        paste_r(img, 942, y, lab, font(FR, 26), mix(CREAM, INK, 0.30), al2)
    # episentrum
    epi_t = seg(tl, 1.0, 1.5)
    if epi_t > 0:
        ring_on(img, 540, gnd, 40 + 60 * eo(epi_t), mix(accent, WHITE, 0.35), 4, al2 * (1 - epi_t) * 0.9, squash=0.22)
        dot_on(img, 540, gnd, 15, accent, al2)
        # label + garis penunjuk
        line_on(img, (566, gnd - 12), (700, gnd - 96), mix(accent, INK, 0.3), 3, al2 * epi_t)
        pill(img, 706, gnd - 108, "EPISENTRUM", font(FS, 31), mix(accent, INK, 0.15), outline=accent,
             bg=mix(WHITE, accent, 0.12), alpha=al2 * epi_t)
        paste_r(img, 706, gnd - 62, "titik di atas gempa", font(FM, 27), MUTED, al2 * epi_t)
    # hiposentrum (titik gempa sebenarnya)
    hip_t = seg(tl, 2.2, 2.8)
    if hip_t > 0:
        hy = km(368) + dy2
        star4(img, 540, hy, 22 + 4 * math.sin(tg * 5.5), accent, al2 * hip_t)
        waves(img, 540, hy, tg, n=3, period=2.2, rmax=210, color=accent, width=5, alpha=al2 * hip_t * 0.75)
        line_on(img, (566, hy), (700, hy), mix(accent, INK, 0.3), 3, al2 * hip_t)
        pill(img, 706, hy, "HIPOSENTRUM", font(FS, 31), mix(accent, INK, 0.15), outline=accent,
             bg=mix(WHITE, accent, 0.12), alpha=al2 * hip_t)
        paste_r(img, 706, hy + 46, "titik gempa di dalam bumi", font(FM, 27), MUTED, al2 * hip_t)
    # garis kedalaman putus-putus + panah ukur
    dep_t = seg(tl, 3.4, 4.1)
    if dep_t > 0:
        line_on(img, (540, gnd), (540, km(368) + dy2), mix(accent, INK, 0.35), 3, al2 * dep_t, dash=22)
        x_ar = 232
        line_on(img, (x_ar, gnd), (x_ar, km(368) + dy2), mix(accent, INK, 0.45), 5, al2 * dep_t)
        for yy, sgn in ((gnd, -1), (km(368) + dy2, 1)):
            poly_on(img, [(x_ar, yy + sgn * 26), (x_ar - 20, yy - sgn * 6), (x_ar + 20, yy - sgn * 6)],
                    mix(accent, INK, 0.45), al2 * dep_t)
        cnt = int(368 * eio(dep_t))
        pill(img, 118, (gnd + km(368) + dy2) / 2, f"{cnt} KM", font(FB, 40), WHITE, bg=accent,
             alpha=al2 * dep_t, pad=34, hgt=76)
    # penutup
    q = seg(tl, dur - 1.7, dur - 1.1)
    if q > 0:
        paste_c(img, W / 2, 1650, "kedalaman diukur dari permukaan", font(FM, 34),
                mix(accent, INK, 0.30), q * al)


def sc_ruler(img, d, sc, tl, dur, tg, accent, al, dy):
    """Penggaris kedalaman: tiga kelas gempa + kekuatan guncangan di permukaan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.15, 0.7)
    if q <= 0:
        return
    al2 = q * al
    y_top, y_bot, km_max = 620, 1560, 400.0
    barx, barw = 176, 74
    km = depth_scale(y_top, y_bot, km_max)
    bands = [(0, 60, RED, "DANGKAL", "< 60 km"),
             (60, 300, AMBER, "MENENGAH", "60–300 km"),
             (300, 400, BLUE, "DALAM", "> 300 km")]
    for a_, b_, col, lab, sub in bands:
        y0, y1 = km(a_), km(b_)
        alpha_band = al2 * (0.42 if a_ > 0 else 0.46)
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([S(barx), S(y0), S(barx + barw), S(y1)], radius=S(14),
                             fill=mix(CREAM, col, alpha_band) + (255,),
                             outline=mix(CREAM, col, 0.75) + (255,), width=max(1, int(S(2.5))))
        _put(img, lay)
    for kmv in (0, 60, 300):
        y = km(kmv)
        line_on(img, (barx - 24, y), (barx + barw + 24, y), mix(CREAM, INK, 0.35), 3, al2)
        paste_r(img, barx - 34, y, f"{kmv}", font(FM, 28), mix(CREAM, INK, 0.45), al2, dy=-2)
    paste_r(img, 62, km(0) - 30, "KEDALAMAN", font(FM, 28), mix(CREAM, INK, 0.42), al2)
    # label kelas: muncul saat penanda masuk
    lab_t = [0.30, 1.55, 2.75]
    for i, (a_, b_, col, lab, sub) in enumerate(bands):
        t0 = lab_t[i]
        qq = seg(tl, t0, t0 + 0.5)
        if qq <= 0:
            continue
        k = eob(qq)
        cy = (km(a_) + km(b_)) / 2
        pill(img, 380, cy - 26, lab, font(FB, 52), mix(col, INK, 0.10), outline=col,
             bg=mix(WHITE, col, 0.14), alpha=qq * al2, pad=36, hgt=86, dot=False)
        paste_r(img, 388, cy + 34, sub, font(FM, 32), mix(col, INK, 0.35), qq * al2)
    # penanda bergerak + kekuatan guncangan
    mv = seg(tl, 0.35, dur - 0.9)
    if mv > 0:
        kmpos = 12 + (km_max - 12) * eio(mv)
        ypos = km(kmpos)
        ring_on(img, barx + barw / 2, ypos, 52, mix(CREAM, INK, 0.35), 3, al2 * 0.5)
        dot_on(img, barx + barw / 2, ypos, 26, INK, al2)
        paste_r(img, barx + barw + 34, ypos, f"{int(kmpos)} km", font(FB, 34), INK, al2)
        # gauge kekuatan di permukaan (berkurang seiring kedalaman)
        gx, gw = 800, 132
        gy0, gy1 = y_top, y_bot
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([S(gx), S(gy0), S(gx + gw), S(gy1)], radius=S(14),
                             fill=mix(CREAM, INK, 0.08) + (255,))
        fill_h = (gy1 - gy0) * (1 - kmpos / km_max) * 0.98
        col_now = RED if kmpos < 60 else (AMBER if kmpos < 300 else BLUE)
        if fill_h > 6:
            dd.rounded_rectangle([S(gx), S(gy1 - fill_h), S(gx + gw), S(gy1)], radius=S(14),
                                 fill=mix(CREAM, col_now, 0.62) + (255,))
        _put(img, lay, al2)
        paste_c(img, gx + gw / 2, gy0 - 42, "GUNCANGAN", font(FS, 28), mix(CREAM, INK, 0.45), al2)
        paste_c(img, gx + gw / 2, gy0 - 10, "DI PERMUKAAN", font(FS, 28), mix(CREAM, INK, 0.45), al2)
    q = seg(tl, dur - 1.5, dur - 0.9)
    if q > 0:
        paste_c(img, W / 2, 1660, "MAKIN DALAM → MAKIN LEMAH DI PERMUKAAN", font(FB, 40),
                mix(accent, INK, 0.20), q * al)


def sc_effects(img, d, sc, tl, dur, tg, accent, al, dy):
    """Dua panel: apa yang terjadi saat gempa dangkal vs gempa dalam."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    for idx, (key, col, t0) in enumerate((("left", RED, 0.25), ("right", BLUE, 1.5))):
        q = seg(tl, t0, t0 + 0.55)
        if q <= 0:
            continue
        blk = sc.get(key, {})
        al2 = q * al
        dy2 = (1 - eio(q)) * 70
        x0 = 66 + idx * 484
        x1 = x0 + 464
        panel(img, x0, 560, x1, 1480, alpha=al2, dy=dy2, radius=46)
        col = hexc(blk.get("color", "#C0392B" if idx == 0 else "#2F6FB5"))
        cx = (x0 + x1) / 2
        pill(img, x0 + 40, 630 + dy2, blk.get("label", ""), font(FS, 30), mix(col, INK, 0.12),
             outline=col, bg=mix(WHITE, col, 0.12), alpha=al2, pad=26, hgt=52)
        # gambar penjelas per panel
        if idx == 0:
            gnd = 1180 + dy2
            line_on(img, (x0 + 40, gnd), (x1 - 40, gnd), mix(CREAM, INK, 0.40), 5, al2)
            star4(img, cx - 60, gnd + 14, 15 + 3 * math.sin(tg * 9), col, al2)
            waves(img, cx - 60, gnd + 14, tg, n=4, period=1.0, rmax=150, color=col, width=5,
                  alpha=al2 * 0.85, squash=0.40)
            house(img, cx + 70, gnd, 86, mix(CREAM, INK, 0.70), tilt=7.0 * math.sin(tg * 11.0) * q, alpha=al2)
            # dasar laut terangkat -> gelombang
            seab = 1380 + dy2
            line_on(img, (x0 + 40, seab), (x1 - 40, seab), mix(CREAM, col, 0.55), 6, al2)
            up = 18 * (0.5 + 0.5 * math.sin(tg * 2.2))
            poly_on(img, [(cx - 130, seab), (cx + 130, seab), (cx + 92, seab - up - 46), (cx - 92, seab - up - 46)],
                    mix(CREAM, col, 0.30), al2)
            poly_on(img, [(cx, seab - up - 92), (cx - 22, seab - up - 52), (cx + 22, seab - up - 52)], col, al2)
            paste_c(img, cx, 1440 + dy2, "TSUNAMI?", font(FB, 40), mix(col, INK, 0.15), al2)
        else:
            gnd = 1000 + dy2
            line_on(img, (x0 + 40, gnd), (x1 - 40, gnd), mix(CREAM, INK, 0.40), 5, al2)
            hy = 1400 + dy2
            star4(img, cx, hy, 16 + 3 * math.sin(tg * 5), col, al2)
            waves(img, cx, hy, tg, n=3, period=2.0, rmax=196, color=col, width=5,
                  alpha=al2 * 0.7, up_only=True)
            house(img, cx - 86, gnd, 78, mix(CREAM, INK, 0.70), alpha=al2)
            house(img, cx + 20, gnd, 86, mix(CREAM, INK, 0.70), alpha=al2)
            paste_c(img, cx, 1440 + dy2, "TIDAK MERUSAK", font(FB, 34), mix(col, INK, 0.15), al2)
        # judul + keterangan
        f = font(FB, 46)
        for j, l in enumerate(wrap(blk.get("title", ""), f, 384)[:2]):
            qq = seg(tl, t0 + 0.2 + j * 0.1, t0 + 0.6 + j * 0.1)
            if qq > 0:
                paste_c(img, cx, 716 + dy2 + j * 56, l, f, INK, qq * al2)
        fb_ = font(FM, 32)
        for j, l in enumerate(wrap(blk.get("body", ""), fb_, 384)[:4]):
            qq = seg(tl, t0 + 0.34 + j * 0.08, t0 + 0.74 + j * 0.08)
            if qq > 0:
                paste_c(img, cx, 1560 + dy2 + j * 46, l, fb_, MUTED, qq * al2)


def sc_energy(img, d, sc, tl, dur, tg, accent, al, dy):
    """Magnitudo = energi: 1 angka naik = 32 kali energi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.2, 0.75)
    if q <= 0:
        return
    al2 = q * al
    dy2 = (1 - eio(q)) * 60
    paste_c(img, W / 2, 580 + dy2, "MAGNITUDO NAIK 1 ANGKA", font(FS, 36), mix(accent, INK, 0.30), al2)
    # angka besar berhitung
    prog = eio(seg(tl, 0.6, 4.2))
    n = max(1, int(round(1 + prog * 31)))
    paste_c(img, W / 2, 700 + dy2, f"{n}×", font(FB, 168), accent, al2, scale=1.0 + 0.03 * math.sin(tg * 4))
    paste_c(img, W / 2, 828 + dy2, "ENERGI", font(FB, 46), mix(accent, INK, 0.15), al2)
    # M5: satu blok
    cell, gap = 62, 16
    gx0, gy0 = 108, 980 + dy2
    panel(img, 84, 930 + dy2, 300, 1240 + dy2, alpha=al2, radius=34, fill=mix(WHITE, INK, 0.02))
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([S(gx0), S(gy0), S(gx0 + cell), S(gy0 + cell)], radius=S(12),
                         fill=mix(accent, INK, 0.55) + (255,))
    _put(img, lay, al2)
    paste_c(img, 192, 1120 + dy2, "M 5", font(FB, 40), INK, al2)
    paste_c(img, 192, 1170 + dy2, "1× energi", font(FM, 30), MUTED, al2)
    # M6: 32 blok mengisi satu per satu (digambar dalam SATU layer agar cepat)
    bx0, by0 = 372, 980 + dy2
    cols, rows = 8, 4
    gridw = cols * (cell + gap) - gap
    gridh = rows * (cell + gap) - gap
    filled = int(round(eio(seg(tl, 1.4, 4.6)) * 32))
    bx = _box(img, bx0, by0, bx0 + gridw, by0 + gridh)
    if bx:
        X0, Y0, X1, Y1 = bx
        lay = Image.new("RGBA", (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        ox, oy = X0 / SS, Y0 / SS
        for i in range(32):
            r_, c_ = divmod(i, cols)
            x = bx0 + c_ * (cell + gap) - ox
            y = by0 + r_ * (cell + gap) - oy
            on = i < filled
            pop = eob(seg(tl, 1.4 + i * 0.09, 1.58 + i * 0.09)) if on else 1.0
            side = cell * (0.72 + 0.28 * pop) if on else cell * 0.86
            cxx, cyy = x + cell / 2, y + cell / 2
            dd.rounded_rectangle([S(cxx - side / 2), S(cyy - side / 2), S(cxx + side / 2), S(cyy + side / 2)],
                                 radius=S(12),
                                 fill=(mix(accent, INK, 0.30) if on else mix(CREAM, INK, 0.10)) + (255,),
                                 outline=(mix(accent, INK, 0.55) + (255,)) if on else None,
                                 width=max(1, int(S(2))))
        _put_at(img, lay, X0, Y0, al2)
    paste_c(img, bx0 + (cols * (cell + gap) - gap) / 2, 1360 + dy2, "M 6", font(FB, 40), INK, al2)
    paste_c(img, bx0 + (cols * (cell + gap) - gap) / 2, 1410 + dy2, "32× energi", font(FM, 30),
            mix(accent, INK, 0.30), al2)
    q = seg(tl, dur - 1.6, dur - 1.0)
    if q > 0:
        pill(img, 210, 1540, "ENERGI ≠ KERUSAKAN", font(FB, 44), WHITE, bg=mix(accent, INK, 0.10),
             alpha=q * al, pad=40, hgt=84)


def sc_mmi(img, d, sc, tl, dur, tg, accent, al, dy):
    """Peta sederhana: satu gempa, kekuatan getaran berbeda di tiap kota (MMI)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.15, 0.7)
    if q <= 0:
        return
    al2 = q * al
    dy2 = (1 - eio(q)) * 60
    # garis pantai lembut
    coast = [(120, 1180), (300, 1130), (520, 1140), (700, 1080), (900, 1090), (980, 1040)]
    line_on(img, (100, 1216), (980, 1216), mix(CREAM, BLUE, 0.35), 8, al2 * 0.8)
    poly_on(img, coast + [(980, 1300), (120, 1300)], mix(CREAM, BLUE, 0.14), al2 * 0.9)
    # pusat gempa + gelombang menjalar
    ex, ey = 420, 1000
    star4(img, ex, ey, 20 + 4 * math.sin(tg * 5), RED, al2)
    for i in range(4):
        u = ((tg / 2.4) + i / 4) % 1.0
        ring_on(img, ex, ey, 60 + 620 * eo(u), mix(RED, CREAM, 0.45), 5, al2 * (1 - u) ** 1.5)
    # kota + tingkat MMI
    cities = [((282, 1252), "VI", "kuat", RED, 0.9, 0.9),
              ((640, 1276), "IV", "sedang", AMBER, 2.0, 0.75),
              ((898, 1176), "II", "lemah", MUTED, 3.1, 0.6)]
    for (cx, cy), mmi, word, col, t0, shake in cities:
        qq = seg(tl, t0, t0 + 0.5)
        if qq <= 0:
            continue
        k = eob(qq)
        al3 = qq * al2
        house(img, cx, cy, 76, mix(CREAM, INK, 0.62), tilt=5.5 * math.sin(tg * 10) * qq * shake, alpha=al3)
        for j in range(2):
            ring_on(img, cx, cy, (60 + j * 28) * (0.8 + 0.2 * k), col, 4, al3 * 0.7)
        # satu chip di atas rumah: "MMI VI · kuat" (tidak menimpa apa pun)
        lab = f"MMI {mmi} · {word}"
        fl = font(FB, 32)
        wid = tw(lab, fl) + 52
        pill(img, cx - wid / 2, cy - 138, lab, fl, WHITE, bg=col, alpha=al3, pad=26, hgt=58)
    # skala MMI
    q = seg(tl, 1.6, 2.2)
    if q > 0:
        al3 = q * al2
        x0, x1, y0, y1 = 120, 960, 1600, 1668
        n = 12
        segw = (x1 - x0) / n
        for i in range(n):
            col = mix(RED, mix(CREAM, INK, 0.12), i / (n - 1))
            lay = _layer(img)
            dd = ImageDraw.Draw(lay)
            dd.rounded_rectangle([S(x0 + i * segw + 3), S(y0), S(x0 + (i + 1) * segw - 3), S(y1)],
                                 radius=S(10), fill=col + (255,))
            _put(img, lay, al3)
            paste_c(img, x0 + (i + 0.5) * segw, y1 + 34, ["I", "II", "III", "IV", "V", "VI", "VII", "VIII",
                                                          "IX", "X", "XI", "XII"][i],
                    font(FM, 26), mix(CREAM, INK, 0.45), al3)
        paste_c(img, W / 2, 1556, "SKALA MMI: 1 SAMPAI 12", font(FS, 34), mix(accent, INK, 0.25), al3)
    q = seg(tl, dur - 1.3, dur - 0.75)
    if q > 0:
        paste_c(img, W / 2, 1750, "satu gempa, kekuatan berbeda di tiap kota", font(FM, 32),
                mix(accent, INK, 0.30), q * al)



def sc_intro_predict(img, d, sc, tl, dur, tg, accent, al, dy):
    """Pembuka: kalender dengan tanggal yang 'diramalkan' lalu dicoret."""
    y = 470
    for i, l in enumerate(sc["lines"]):
        fsz = 150
        while fsz > 60 and tw(l, font(FB, fsz)) > 940:
            fsz -= 4
        f = font(FB, fsz)
        q = seg(tl, 0.05 + i * 0.22, 0.55 + i * 0.22)
        if q <= 0:
            continue
        k = eob(q)
        col = accent if i == len(sc["lines"]) - 1 else INK
        paste_c(img, W / 2, y + (1 - k) * 40, l, f, col, q * al, scale=0.9 + 0.1 * k)
        y += 158
    # kalender
    q = seg(tl, 0.9, 1.5)
    if q > 0:
        k = eob(q)
        al2 = q * al
        x0, y0, x1, y1 = 180, 830, 900, 1300
        panel(img, x0, y0, x1, y1, alpha=al2, radius=44)
        # kepala kalender
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([S(x0 + 22), S(y0 + 22), S(x1 - 22), S(y0 + 116)], radius=S(28),
                             fill=mix(accent, INK, 0.10) + (255,))
        _put(img, lay, al2)
        paste_c(img, (x0 + x1) / 2, y0 + 70, "OKTOBER 2026", font(FB, 42), WHITE, al2)
        # kotak tanggal: 7 kolom x 5 baris (1..31), satu tanggal dicoret
        for i in range(35):
            r_, c_ = divmod(i, 7)
            day = i + 1
            bx = x0 + 44 + c_ * 104
            by = y0 + 158 + r_ * 74
            jadwal = day == 15
            qq = seg(tl, 1.15 + (i % 7) * 0.04 + r_ * 0.10, 1.36 + (i % 7) * 0.04 + r_ * 0.10)
            if qq <= 0 or day > 31:
                continue
            lay = _layer(img)
            dd = ImageDraw.Draw(lay)
            if jadwal:
                dd.rounded_rectangle([S(bx - 22), S(by - 26), S(bx + 62), S(by + 34)], radius=S(16),
                                     fill=mix(WHITE, accent, 0.22) + (255,), outline=accent + (255,),
                                     width=max(1, int(S(3))))
            _put(img, lay, al2 * qq)
            paste_c(img, bx + 20, by + 4, str(day),
                    font(FB if jadwal else FM, 34), accent if jadwal else mix(CREAM, INK, 0.42), al2 * qq)
        # tanda silang besar
        q = seg(tl, 2.6, 3.3)
        if q > 0:
            k2 = eo(q)
            cx, cy = x0 + 44 + 0 * 104 + 20, y0 + 158 + 2 * 74 + 4
            L = 62 * k2
            line_on(img, (cx - L, cy - L), (cx + L, cy + L), accent, 12, al2 * 0.92)
            line_on(img, (cx - L, cy + L), (cx + L, cy - L), accent, 12, al2 * 0.92)
    q = seg(tl, 3.4, 4.0)
    if q > 0:
        paste_c(img, W / 2, 1420, "TANGGAL PASTI = TIDAK MUNGKIN", font(FB, 44),
                mix(accent, INK, 0.15), q * al)
    q = seg(tl, 4.1, 4.7)
    if q > 0:
        paste_c(img, W / 2, 1520, "tapi ada yang BISA dilakukan", font(FM, 36), MUTED, q * al)


def sc_why_not(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kenapa tidak bisa: gempa terjadi jauh di dalam, tak ada alat yang mengintip."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.2, 0.8)
    if q <= 0:
        return
    al2 = q * al
    gnd = 820
    # permukaan + alat pemantau
    line_on(img, (100, gnd), (980, gnd), mix(CREAM, INK, 0.5), 6, al2)
    for i, x in enumerate((190, 330, 470, 610, 750, 890)):
        qq = seg(tl, 0.5 + i * 0.08, 0.8 + i * 0.08)
        if qq <= 0:
            continue
        poly_on(img, [(x, gnd), (x - 26, gnd), (x, gnd - 54)], mix(CREAM, INK, 0.5), al2 * qq)
        circ = dot_on(img, x, gnd - 62, 12, accent, al2 * qq)
    paste_r(img, 100, gnd - 132, "ALAT PEMANTAU DI PERMUKAAN", font(FM, 27), mix(CREAM, INK, 0.42), al2)
    # hiposentrum dalam + tanda tanya
    hy = 1400
    star4(img, 540, hy, 22 + 4 * math.sin(tg * 5), accent, al2)
    waves(img, 540, hy, tg, n=3, period=2.2, rmax=238, color=accent, width=7, alpha=al2 * 0.85)
    paste_c(img, 540, hy + 150, "?", font(FB, 110), mix(accent, INK, 0.25), al2 * (0.6 + 0.4 * abs(math.sin(tg * 2))))
    pill(img, 340, 1180, "SUMBER GEMPA · PULUHAN-RATUSAN KM DI DALAM BUMI", font(FS, 28),
         mix(accent, INK, 0.10), outline=accent, bg=mix(WHITE, accent, 0.12), alpha=al2, pad=28, hgt=54)
    q = seg(tl, 2.0, 2.7)
    if q > 0:
        paste_c(img, W / 2, 1620, "TIDAK ADA ALAT YANG BISA MELIHAT KE SANA", font(FB, 40),
                mix(accent, INK, 0.15), q * al2)
    q = seg(tl, 2.9, 3.5)
    if q > 0:
        paste_c(img, W / 2, 1704, "deteksi baru mungkin SETELAH gempa mulai", font(FM, 34), MUTED, q * al2)


def sc_wave_race(img, d, sc, tl, dur, tg, accent, al, dy):
    """Gelombang P mendahului gelombang S: dasar peringatan dini."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.15, 0.7)
    if q <= 0:
        return
    al2 = q * al
    x_h, y_h = 190, 1180      # hiposentrum
    x_c, y_c = 830, 1180      # kota
    # jalur
    line_on(img, (x_h + 30, y_h), (x_c - 60, y_c), mix(CREAM, INK, 0.16), 3, al2, dash=26)
    star4(img, x_h, y_h, 20 + 3 * math.sin(tg * 6), accent, al2)
    house(img, x_c, y_c + 40, 92, mix(CREAM, INK, 0.70), alpha=al2)
    paste_c(img, x_c, y_c - 120, "KOTA", font(FS, 30), mix(CREAM, INK, 0.45), al2)
    paste_c(img, x_h, y_h + 120, "PUSAT GEMPA", font(FS, 30), mix(CREAM, INK, 0.45), al2)
    # balapan gelombang
    tp = eio(seg(tl, 0.7, 4.6))
    ts_ = eio(seg(tl, 1.9, 6.4))
    xp = x_h + 30 + (x_c - 60 - x_h - 30) * tp
    xs = x_h + 30 + (x_c - 60 - x_h - 30) * ts_
    dot_on(img, xp, y_h, 20, RED, al2)
    paste_c(img, xp, y_h - 74, "P", font(FB, 44), RED, al2)
    if ts_ > 0:
        dot_on(img, xs, y_c, 22, PURPLE, al2)
        paste_c(img, xs, y_c + 86, "S", font(FB, 44), PURPLE, al2)
    # keterangan
    pill(img, 120, 700, "GELOMBANG P · CEPAT, TIDAK MERUSAK", font(FS, 29), WHITE, bg=RED,
         alpha=seg(tl, 0.9, 1.4) * al2, pad=28, hgt=56)
    pill(img, 120, 790, "GELOMBANG S · LAMBAT, MERUSAK", font(FS, 29), WHITE, bg=PURPLE,
         alpha=seg(tl, 2.2, 2.7) * al2, pad=28, hgt=56)
    q = seg(tl, 4.8, 5.5)
    if q > 0:
        paste_c(img, W / 2, 1010, "SELISIH WAKTUNYA DIPAKAI UNTUK PERINGATAN", font(FB, 38),
                mix(accent, INK, 0.15), q * al2)
    q = seg(tl, 5.8, 6.5)
    if q > 0:
        paste_c(img, W / 2, 1520, "inilah cara kerja peringatan dini gempa", font(FM, 34), MUTED, q * al2)


def sc_countdown(img, d, sc, tl, dur, tg, accent, al, dy):
    """Hitung mundur 20 detik + apa yang bisa dilakukan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.15, 0.7)
    if q <= 0:
        return
    al2 = q * al
    # cincin hitung mundur
    cx, cy, r = 540, 900, 250
    prog = eio(seg(tl, 0.7, min(dur - 1.0, 7.0)))
    ring_on(img, cx, cy, r, mix(CREAM, INK, 0.14), 26, al2)
    segs = 60
    for i in range(int(segs * (1 - prog))):
        a0 = -90 + i * (360 / segs)
        a1 = a0 + (360 / segs) * 0.72
        p1 = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
        p2 = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
        line_on(img, p1, p2, accent, 26, al2)
    sisa = max(0, int(round(20 * (1 - prog))))
    paste_c(img, cx, cy - 20, f"{sisa}", font(FB, 210), accent, al2, scale=1 + 0.03 * math.sin(tg * 5))
    paste_c(img, cx, cy + 130, "DETIK", font(FB, 44), mix(accent, INK, 0.25), al2)
    # tiga aksi
    acts = [("MERUNDUK", "jauhi kaca dan benda tinggi", 2.0),
            ("LINDUNGI KEPALA", "tangan atau bantal", 2.9),
            ("CEK INFO RESMI", "BMKG · bukan pesan berantai", 3.8)]
    yy = 1290
    for lab, sub, t0 in acts:
        qq = seg(tl, t0, t0 + 0.5)
        if qq <= 0:
            continue
        k = eob(qq)
        al3 = qq * al2
        dot_on(img, 170, yy, 26 * k, accent, al3)
        line_on(img, (170, yy), (176, yy + 14), WHITE, 9, al3)
        line_on(img, (176, yy + 14), (192, yy - 16), WHITE, 9, al3)
        paste_r(img, 226, yy - 12, lab, font(FB, 42), INK, al3)
        paste_r(img, 226, yy + 32, sub, font(FM, 29), MUTED, al3)
        yy += 118
    paste_c(img, W / 2, 1200, "DALAM HITUNGAN DETIK ITU BISA DILAKUKAN:", font(FS, 30),
            mix(accent, INK, 0.30), seg(tl, 1.8, 2.3) * al2)


def sc_hoax(img, d, sc, tl, dur, tg, accent, al, dy):
    """Klaim tanggal pasti = hoaks; potensi bukan prediksi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.2, 0.8)
    if q <= 0:
        return
    al2 = q * al
    # kartu unggahan
    panel(img, 120, 620, 960, 1120, alpha=al2, radius=44)
    dot_on(img, 190, 700, 26, mix(CREAM, INK, 0.30), al2)
    paste_r(img, 232, 692, "PESAN BERANTAI", font(FS, 30), mix(CREAM, INK, 0.45), al2)
    paste_r(img, 232, 736, "diteruskan 1.204 kali", font(FR, 27), mix(CREAM, INK, 0.35), al2)
    paste_c(img, 540, 850, '"GEMPA BESAR M9 AKAN TERJADI"', font(FB, 44), INK, al2)
    paste_c(img, 540, 930, '"SEBELUM AKHIR 2026 — HARI PASTI!"', font(FB, 40),
            mix(accent, INK, 0.15), al2)
    paste_c(img, 540, 986, "tanggal, kekuatan, dan hari disebut pasti", font(FM, 32), MUTED, al2)
    # cap HOAKS
    q = seg(tl, 1.5, 2.1)
    if q > 0:
        k = eob(q)
        cx, cy = 540, 1146
        L = 360 * k
        ff = font(FB, 150)
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        dd.rounded_rectangle([S(cx - L / 2), S(cy - 78), S(cx + L / 2), S(cy + 78)], radius=S(26),
                             outline=accent + (255,), width=max(1, int(S(12))))
        _put(img, lay, al2 * 0.95 * q)
        paste_c(img, cx, cy, "HOAKS", ff, accent, al2, scale=0.85 + 0.15 * k)
    # potensi vs prediksi
    q = seg(tl, 2.6, 3.4)
    if q > 0:
        al3 = q * al2
        panel(img, 90, 1220, 512, 1560, alpha=al3, radius=40, fill=mix(WHITE, GREEN, 0.06))
        panel(img, 568, 1220, 990, 1560, alpha=al3, radius=40, fill=mix(WHITE, RED, 0.06))
        paste_c(img, 301, 1300, "POTENSI", font(FB, 52), GREEN, al3)
        paste_c(img, 301, 1372, "wilayah punya", font(FM, 32), MUTED, al3)
        paste_c(img, 301, 1414, "sumber gempa", font(FM, 32), MUTED, al3)
        paste_c(img, 301, 1490, "= mitigasi", font(FS, 30), mix(GREEN, INK, 0.2), al3)
        paste_c(img, 779, 1300, "PREDIKSI", font(FB, 52), RED, al3)
        paste_c(img, 779, 1372, "kapan, di mana,", font(FM, 32), MUTED, al3)
        paste_c(img, 779, 1414, "berapa besar", font(FM, 32), MUTED, al3)
        paste_c(img, 779, 1490, "= belum bisa", font(FS, 30), mix(RED, INK, 0.2), al3)
    q = seg(tl, 3.8, 4.5)
    if q > 0:
        paste_c(img, W / 2, 1650, "SKENARIO UNTUK SIAGA BUKAN RAMALAN", font(FB, 40),
                mix(accent, INK, 0.15), q * al2)


def sc_checklist(img, d, sc, tl, dur, tg, accent, al, dy):
    """Yang bisa dilakukan sekarang."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    items = [("CEK KANAL RESMI BMKG", "info gempa & peringatan tsunami", 0.5),
             ("JANGAN SEBAR TANPA BUKTI", "hoaks bikin panik dan korban", 1.5),
             ("SIAPKAN TAS SIAGA", "air, obat, dokumen, senter", 2.5)]
    yy = 760
    for lab, sub, t0 in items:
        q = seg(tl, t0, t0 + 0.55)
        if q <= 0:
            continue
        k = eob(q)
        al2 = q * al
        panel(img, 110, yy - 76, 970, yy + 96, alpha=al2, radius=40)
        dot_on(img, 190, yy + 8, 40, accent, al2)
        line_on(img, (172, yy + 10), (186, yy + 32), WHITE, 12, al2)
        line_on(img, (186, yy + 32), (212, yy - 22), WHITE, 12, al2)
        paste_r(img, 258, yy - 16, lab, font(FB, 44), INK, al2)
        paste_r(img, 258, yy + 40, sub, font(FM, 30), MUTED, al2)
        yy += 230
    q = seg(tl, dur - 1.6, dur - 1.0)
    if q > 0:
        paste_c(img, W / 2, 1540, "GEMPA TIDAK BISA DIRAMAL, TAPI BISA DISIAPKAN", font(FB, 38),
                mix(accent, INK, 0.15), q * al)



def _cloud(img, cx, cy, s, color, alpha=1.0, drops=0, tg=0.0):
    """Awan sederhana + titik hujan di bawahnya."""
    if alpha <= 0.01:
        return
    poly_on(img, [(cx - s * 0.9, cy), (cx - s * 0.55, cy - s * 0.55), (cx - s * 0.05, cy - s * 0.72),
                  (cx + s * 0.5, cy - s * 0.5), (cx + s * 0.92, cy)], color, alpha)
    poly_on(img, [(cx - s * 0.82, cy + s * 0.06), (cx + s * 0.84, cy + s * 0.06),
                  (cx + s * 0.7, cy + s * 0.24), (cx - s * 0.7, cy + s * 0.24)], color, alpha)
    for i in range(drops):
        ph = (tg * 1.6 + i * 0.7) % 1.0
        dx = cx + (i - (drops - 1) / 2) * s * 0.34
        dy = cy + s * 0.4 + ph * s * 1.5
        line_on(img, (dx, dy), (dx - 5, dy + s * 0.34), mix(color, WHITE, 0.35), 6, alpha * (1 - ph * 0.6))


def _sun(img, cx, cy, r, color, tg, alpha=1.0):
    if alpha <= 0.01:
        return
    for i in range(3):
        ring_on(img, cx, cy, r * (1 + i * 0.35), mix(color, CREAM, 0.62), 8, alpha * 0.35)
    dot_on(img, cx, cy, r, mix(color, WHITE, 0.55), alpha)
    for i in range(12):
        a = i * math.pi / 6 + tg * 0.25
        line_on(img, (cx + r * 1.2 * math.cos(a), cy + r * 1.2 * math.sin(a)),
                (cx + (r * 1.5 + 6 * math.sin(tg * 1.6 + i)) * math.cos(a),
                 cy + (r * 1.5 + 6 * math.sin(tg * 1.6 + i)) * math.sin(a)), color, 5, alpha * 0.6)


def _crack(img, x0, y0, x1, color, alpha=1.0, n=7):
    """Tanah retak (zigzag) sebagai lambang kemarau."""
    step = (x1 - x0) / n
    yy = y0
    for i in range(n):
        line_on(img, (x0 + i * step, yy), (x0 + (i + 0.5) * step, yy - 12),
                color, 3, alpha * 0.8)
        line_on(img, (x0 + (i + 0.5) * step, yy - 12), (x0 + (i + 1) * step, yy), color, 3, alpha * 0.8)
        yy = y0 + (6 if i % 2 else -6)


def sc_intro_rain(img, d, sc, tl, dur, tg, accent, al, dy):
    """Pembuka: kemarau kering, tapi ada satu titik hujan deras."""
    y = 470
    for i, l in enumerate(sc["lines"]):
        fsz = 150
        while fsz > 58 and tw(l, font(FB, fsz)) > 950:
            fsz -= 4
        f = font(FB, fsz)
        q = seg(tl, 0.05 + i * 0.22, 0.55 + i * 0.22)
        if q <= 0:
            continue
        k = eob(q)
        col = accent if i == len(sc["lines"]) - 1 else INK
        paste_c(img, W / 2, y + (1 - k) * 40, l, f, col, q * al, scale=0.9 + 0.1 * k)
        y += 158
    q = seg(tl, 0.9, 1.5)
    if q > 0:
        al2 = q * al
        panel(img, 90, 830, 990, 1420, alpha=al2, radius=48)
        gnd = 1300
        line_on(img, (140, gnd), (940, gnd), mix(CREAM, INK, 0.45), 6, al2)
        # tanah retak + matahari terik (kiri)
        _crack(img, 150, gnd + 30, 560, mix(CREAM, INK, 0.52), al2, n=7)
        _sun(img, 260, 1010, 58, AMBER, tg, al2)
        paste_c(img, 268, 1150, "Panas & kering", font(FM, 32), mix(AMBER, INK, 0.30), al2)
        # hujan lokal (kanan)
        _cloud(img, 760, 1010, 122, mix(CREAM, INK, 0.50), al2, drops=7, tg=tg)
        paste_c(img, 782, 1370, "hujan deras sebentar", font(FM, 32), mix(accent, INK, 0.25), al2)
        dot_on(img, 760, gnd, 14, accent, al2)
    q = seg(tl, 2.2, 2.8)
    if q > 0:
        paste_c(img, W / 2, 1520, "bukan tanda musimnya salah", font(FM, 38), MUTED, q * al)


def sc_enso_iod(img, d, sc, tl, dur, tg, accent, al, dy):
    """El Nino + IOD positif = pasokan uap air berkurang."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.2, 0.75)
    if q <= 0:
        return
    al2 = q * al
    cards = [("EL NINO", "laut Pasifik lebih dingin", AMBER, 90, 700),
             ("IOD POSITIF", "Samudra Hindia tak suplai uap", GREEN, 560, 700)]
    for i, (lab, sub, col, x0, y0) in enumerate(cards):
        qq = seg(tl, 0.35 + i * 0.35, 0.85 + i * 0.35)
        if qq <= 0:
            continue
        k = eob(qq)
        al3 = qq * al2
        panel(img, x0, y0, x0 + 430, y0 + 380, alpha=al3, radius=40)
        paste_c(img, x0 + 215, y0 + 62, lab, font(FB, 46), mix(col, INK, 0.10), al3)
        paste_c(img, x0 + 215, y0 + 116, sub, font(FM, 27), MUTED, al3)
        # laut + panah uap menjauh dari Indonesia
        oy = y0 + 230
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        bx0, bx1 = x0 + 36, x0 + 394
        bx = _box(img, bx0, oy - 30, bx1, oy + 46)
        if bx:
            X0, Y0, X1, Y1 = bx
            lay = Image.new("RGBA", (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
            dd = ImageDraw.Draw(lay)
            ox, oy_ = X0 / SS, Y0 / SS
            dd.rounded_rectangle([S(bx0 - ox), S(oy - oy_), S(bx1 - ox), S(oy + 46 - oy_)],
                                 radius=S(20), fill=mix(CREAM, BLUE, 0.30) + (255,))
            _put_at(img, lay, X0, Y0, al3)
        for j in range(3):
            u = ((tg * 0.55) + j / 3) % 1.0
            ax = x0 + 400 - 330 * u
            line_on(img, (ax, oy - 40), (ax - 34, oy - 40), col, 7, al3 * (1 - u * 0.5))
            poly_on(img, [(ax - 44, oy - 40), (ax - 30, oy - 52), (ax - 30, oy - 28)], col, al3 * (1 - u * 0.5))
    # Indonesia + kesimpulan
    q = seg(tl, 1.6, 2.2)
    if q > 0:
        al3 = q * al2
        for i, (bx, bw) in enumerate(((300, 150), (470, 120), (610, 170), (810, 110))):
            ell(img, bx, 1180, bx + bw, 1240, fill=mix(CREAM, INK, 0.28), alpha=al3)
        paste_c(img, 540, 1290, "INDONESIA", font(FS, 30), mix(CREAM, INK, 0.45), al3)
        for j in range(3):
            u = ((tg * 0.5) + j / 3) % 1.0
            line_on(img, (540, 1130 - 60 * u), (540, 1090 - 60 * u), RED, 7, al3 * (1 - u))
            poly_on(img, [(540, 1076 - 60 * u), (526, 1096 - 60 * u), (554, 1096 - 60 * u)], RED, al3 * (1 - u))
    q = seg(tl, 2.9, 3.5)
    if q > 0:
        paste_c(img, W / 2, 1460, "PASOKAN UAP AIR BERKURANG", font(FB, 46), mix(accent, INK, 0.15), q * al2)
        paste_c(img, W / 2, 1540, "inilah sebabnya kemarau jadi lebih kering", font(FM, 32), MUTED, q * al2)


def sc_atmo_waves(img, d, sc, tl, dur, tg, accent, al, dy):
    """Gelombang atmosfer melintas -> awan hujan tumbuh di tengah kemarau."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.15, 0.7)
    if q <= 0:
        return
    al2 = q * al
    base = 1130
    islands = [180, 330, 480, 640, 800, 940]
    for x in islands:
        ell(img, x - 48, base - 22, x + 48, base + 26, fill=mix(CREAM, INK, 0.26), alpha=al2)
    line_on(img, (80, base + 60), (1000, base + 60), mix(CREAM, BLUE, 0.35), 5, al2 * 0.6)
    paste_c(img, 540, base + 130, "INDONESIA", font(FS, 30), mix(CREAM, INK, 0.45), al2)
    waves_ = [("MJO", PURPLE, 0.0, 5.4), ("ROSSBY", GREEN, 1.6, 5.4), ("KELVIN", BLUE, 3.2, 5.4)]
    for lab, col, t0, per in waves_:
        qq = seg(tl, t0, t0 + 0.5)
        if qq <= 0:
            continue
        u = ((tg - t0) / per) % 1.0
        x = 60 + 1010 * u
        pts = []
        for i in range(41):
            xx = x - 190 + i * 9.5
            yy = base - 150 + math.sin(i / 40 * math.pi * 2) * 46 * (1 - abs(i / 40 - 0.5) * 2)
            if 40 < xx < 1040:
                pts.append((xx, yy))
        for i in range(len(pts) - 1):
            line_on(img, pts[i], pts[i + 1], col, 8, al2 * 0.9)
        lx = min(max(x - 62, 96), 1000 - tw(lab, font(FS, 30)) - 48)
        if 60 < x < 1020:
            pill(img, lx, base - 232, lab, font(FS, 30), WHITE, bg=col, alpha=qq * al2, pad=24, hgt=52)
        # awan tumbuh setelah gelombang lewat
        for x_isl in islands:
            if u > (x_isl - 60) / 1010:
                _cloud(img, x_isl, base - 96, 54, mix(CREAM, INK, 0.42), al2 * 0.95, drops=3, tg=tg)
    q = seg(tl, 3.9, 4.5)
    if q > 0:
        al3 = q * al2
        pill(img, 150, 1420, "CONTOH NYATA", font(FS, 30), mix(accent, INK, 0.15), outline=accent,
             bg=mix(WHITE, accent, 0.12), alpha=al3, pad=28, hgt=56)
        paste_c(img, W / 2, 1520, "111,6 MM/JAM DI SUMATERA UTARA", font(FB, 48), INK, al3)
        paste_c(img, W / 2, 1584, "31 Agustus - 2 September 2026 (BMKG)", font(FR, 30),
                mix(CREAM, INK, 0.38), al3)
    q = seg(tl, 5.0, 5.6)
    if q > 0:
        paste_c(img, W / 2, 1670, "HUJAN LEBAT BISA TETAP TERJADI", font(FB, 40),
                mix(accent, INK, 0.15), q * al2)


def sc_local_storm(img, d, sc, tl, dur, tg, accent, al, dy):
    """Hujan lokal & singkat: satu kecamatan basah, sebelahnya kering."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    # panel atas: peta dua kecamatan (tampak dari atas)
    q = seg(tl, 0.25, 0.85)
    if q > 0:
        al2 = q * al
        panel(img, 110, 640, 970, 1080, alpha=al2, radius=44)
        for i, (lab, wet) in enumerate((("SATU KECAMATAN", True), ("SEBELAHNYA", False))):
            x0 = 160 + i * 420
            qq = seg(tl, 0.5 + i * 0.4, 1.0 + i * 0.4)
            if qq <= 0:
                continue
            al3 = qq * al2
            lay = _layer(img)
            dd = ImageDraw.Draw(lay)
            col = mix(CREAM, BLUE, 0.30) if wet else mix(CREAM, AMBER, 0.26)
            bx = _box(img, x0, 700, x0 + 380, 990)
            if bx:
                X0, Y0, X1, Y1 = bx
                lay = Image.new("RGBA", (X1 - X0, Y1 - Y0), (0, 0, 0, 0))
                dd = ImageDraw.Draw(lay)
                ox, oy = X0 / SS, Y0 / SS
                dd.rounded_rectangle([S(x0 + 10 - ox), S(700 + 10 - oy), S(x0 + 380 - ox), S(990 - oy)],
                                     radius=S(26), fill=col + (255,))
                _put_at(img, lay, X0, Y0, al3)
            if wet:
                _cloud(img, x0 + 190, 740, 62, mix(CREAM, INK, 0.45), al3, drops=4, tg=tg)
                paste_c(img, x0 + 190, 1030, "hujan deras", font(FS, 30), mix(BLUE, INK, 0.20), al3)
            else:
                _sun(img, x0 + 190, 790, 44, AMBER, tg, al3 * 0.95)
                paste_c(img, x0 + 190, 1030, "tetap kering", font(FS, 30), mix(AMBER, INK, 0.25), al3)
            paste_c(img, x0 + 190, 950, lab, font(FS, 28), mix(CREAM, INK, 0.42), al3)
    # panel bawah: urutan pembentukan awan
    q = seg(tl, 1.8, 2.4)
    if q > 0:
        al2 = q * al
        panel(img, 110, 1140, 970, 1700, alpha=al2, radius=44)
        gnd = 1600
        line_on(img, (160, gnd), (920, gnd), mix(CREAM, INK, 0.40), 6, al2)
        _sun(img, 250, 1520, 44, AMBER, tg, al2)
        steps = [("SIANG PANAS", 250, 1640), ("UAP AIR NAIK", 470, 1330),
                 ("AWAN HUJAN", 660, 1300), ("SORE-MALAM HUJAN", 800, 1650)]
        for i, (lab, cx, cy) in enumerate(steps):
            qq = seg(tl, 2.1 + i * 0.45, 2.6 + i * 0.45)
            if qq <= 0:
                continue
            al3 = qq * al2
            fs_ = 29 if tw(lab, font(FS, 29)) <= 300 else 25
            paste_c(img, cx, cy, lab, font(FS, fs_), mix(accent, INK, 0.22), al3)
        for j in range(3):
            qq = seg(tl, 2.35 + j * 0.12, 2.75 + j * 0.12)
            if qq <= 0:
                continue
            u = ((tg * 0.9) + j / 3) % 1.0
            x = 340 + 230 * u
            y = gnd - 60 - 220 * u
            line_on(img, (x, y), (x, y - 40), mix(accent, WHITE, 0.25), 7, qq * al2 * (1 - u * 0.55))
            poly_on(img, [(x, y - 52), (x - 14, y - 30), (x + 14, y - 30)], mix(accent, WHITE, 0.25),
                    qq * al2 * (1 - u * 0.55))
        _cloud(img, 700, 1420, 96, mix(CREAM, INK, 0.45), seg(tl, 2.9, 3.4) * al2, drops=5, tg=tg)


def sc_dry_risk(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sisi lain: kekeringan, titik panas, asap karhutla."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.2, 0.75)
    if q <= 0:
        return
    al2 = q * al
    # "peta" sederhana: tiga wilayah (jarak antar elemen dijaga)
    spots = [("KALIMANTAN TENGAH", "2.526", 170, 640, 320, 175),
             ("KALIMANTAN BARAT", "2.102", 600, 640, 300, 155),
             ("SUMATERA SELATAN", "1.180", 300, 940, 340, 150)]
    for i, (lab, n, x0, y0, bw, bh) in enumerate(spots):
        qq = seg(tl, 0.35 + i * 0.45, 0.9 + i * 0.45)
        if qq <= 0:
            continue
        al3 = qq * al2
        ell(img, x0, y0, x0 + bw, y0 + bh, fill=mix(CREAM, GREEN, 0.22), outline=mix(CREAM, INK, 0.20),
            width=3, alpha=al3)
        n_dots = max(5, int(n.replace(".", "")) // 300)
        for j in range(n_dots):
            ang = (j * 2.399)
            rx = x0 + bw / 2 + math.cos(ang) * bw * 0.30 * (0.5 + 0.5 * abs(math.sin(tg * 0.6 + j)))
            ry = y0 + bh / 2 + math.sin(ang) * bh * 0.30 * (0.5 + 0.5 * abs(math.cos(tg * 0.5 + j)))
            dot_on(img, rx, ry, 9 + 3 * abs(math.sin(tg * 2 + j)), RED, al3 * 0.85)
        # nama wilayah di bawah elips, jumlah titik panas di atasnya
        paste_c(img, x0 + bw / 2, y0 + bh + 44, lab, font(FS, 27), mix(CREAM, INK, 0.42), al3)
        pill(img, x0 + bw / 2 - 92, y0 - 44, f"{n} TITIK PANAS", font(FS, 27), WHITE, bg=RED,
             alpha=al3, pad=24, hgt=50)
    # asap
    q = seg(tl, 1.9, 2.5)
    if q > 0:
        al3 = q * al2
        for h in range(4):
            u = ((tg * 0.25) + h / 4) % 1.0
            x = 110 + 880 * u
            ell(img, x, 1195 + h * 26, x + 240, 1250 + h * 26, fill=mix(CREAM, INK, 0.22),
                alpha=al3 * (0.45 * (1 - u) + 0.10))
        paste_c(img, 540, 1330, "ASAP: KUALITAS UDARA TURUN", font(FB, 42), mix(accent, INK, 0.15), al3)
    q = seg(tl, 2.8, 3.4)
    if q > 0:
        al3 = q * al2
        pill(img, 190, 1408, "SUHU HINGGA 38,6 °C · SINTANG, 1 SEPT", font(FS, 28), mix(accent, INK, 0.12),
             outline=accent, bg=mix(WHITE, accent, 0.10), alpha=al3, pad=30, hgt=56)
        paste_c(img, W / 2, 1500, "JANGAN BAKAR LAHAN", font(FB, 54), accent, al3)
        paste_c(img, W / 2, 1570, "satu titik api bisa jadi bencana asap", font(FM, 32), MUTED, al3)


def sc_tips_rain(img, d, sc, tl, dur, tg, accent, al, dy):
    """Yang bisa dilakukan saat kemarau kering tapi tetap bisa hujan lebat."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    items = [("CEK PRAKIRAAN BMKG HARIAN", "hujan lokal cepat berubah", 0.4),
             ("HEMAT AIR", "kemarau masih panjang", 1.2),
             ("JANGAN BAKAR LAHAN", "titik panas memicu karhutla", 2.0),
             ("PAKAI MASKER BILA BERASAP", "lindungi saluran napas", 2.8)]
    yy = 700
    for lab, sub, t0 in items:
        q = seg(tl, t0, t0 + 0.5)
        if q <= 0:
            yy += 200
            continue
        al2 = q * al
        panel(img, 110, yy - 72, 970, yy + 86, alpha=al2, radius=38)
        dot_on(img, 186, yy + 6, 36, accent, al2)
        line_on(img, (170, yy + 8), (183, yy + 28), WHITE, 11, al2)
        line_on(img, (183, yy + 28), (207, yy - 20), WHITE, 11, al2)
        paste_r(img, 250, yy - 14, lab, font(FB, 40), INK, al2)
        paste_r(img, 250, yy + 36, sub, font(FM, 29), MUTED, al2)
        yy += 200
    q = seg(tl, dur - 1.5, dur - 0.9)
    if q > 0:
        paste_c(img, W / 2, 1560, "SIAP, TAPI TIDAK PANIK", font(FB, 48), mix(accent, INK, 0.15), q * al)



def sc_intro_malware(img, d, sc, tl, dur, tg, accent, al, dy):
    """Pembuka berita: chat WhatsApp dan mata yang mengintip."""
    y = 460
    for i, l in enumerate(sc["lines"]):
        fsz = 150
        while fsz > 58 and tw(l, font(FB, fsz)) > 950:
            fsz -= 4
        f = font(FB, fsz)
        q = seg(tl, 0.05 + i * 0.22, 0.55 + i * 0.22)
        if q <= 0:
            continue
        k = eob(q)
        col = accent if i == len(sc["lines"]) - 1 else INK
        paste_c(img, W / 2, y + (1 - k) * 40, l, f, col, q * al, scale=0.9 + 0.1 * k)
        y += 156
    # HP dengan chat
    q = seg(tl, 0.9, 1.5)
    if q > 0:
        al2 = q * al
        k = eio(q)
        cx = 400
        _phone(img, cx, 1150 + (1 - k) * 60, 400, 600, al2)
        rows = [("Halo, sudah bayar?", BLUE, False, 0.0), ("Belum, ini buktinya", GREEN, True, 0.35),
                ("Kode OTP-nya berapa?", AMBER, False, 0.7)]
        for i, (txt, col, right, t0) in enumerate(rows):
            qq = seg(tl, 1.3 + t0, 1.7 + t0)
            if qq <= 0:
                continue
            yy = 990 + i * 120
            w_ = 286
            bxx = cx + 70 if right else cx - 70
            rrect_on(img, bxx - w_ / 2, yy - 40, bxx + w_ / 2, yy + 40, 30, col, qq * al2 * 0.92)
            fbt = font(FS, 23) if tw(txt, font(FS, 23)) <= 240 else font(FS, 19)
            paste_c(img, bxx, yy, txt, fbt, WHITE, qq * al2)
        # mata mengintip
        qq = seg(tl, 1.9, 2.5)
        if qq > 0:
            _eye(img, 790, 900, 62, RED, tg, qq * al2)
            for i in range(3):
                u = ((tg * 1.1) + i / 3) % 1.0
                beam = [(790, 900), (cx + 200 + 60 * u, 1000 + 220 * u), (cx + 200 + 60 * u, 1120 + 220 * u)]
                poly_on(img, beam, mix(RED, CREAM, 0.72), qq * al2 * (0.28 * (1 - u)))
    # pita berita
    q = seg(tl, 2.7, 3.3)
    if q > 0:
        k = eob(q)
        pill(img, 150, 1560, "MALWARE \u201cMANTAX OTAX\u201d · TEMUAN 12 SEPT 2026", font(FB, 34),
             WHITE, bg=mix(accent, INK, 0.10), alpha=q * al, pad=34, hgt=72)


def sc_spread_chain(img, d, sc, tl, dur, tg, accent, al, dy):
    """Alur penyebaran: pesan -> APK -> izin -> HP dikuasai."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    steps = [("1", "PESAN PENIPUAN", "file kurir paket / undangan digital", BLUE),
             ("2", "INSTALL APK LUAR PLAY STORE", "bukan dari toko resmi", AMBER),
             ("3", "MINTA IZIN ADMIN & AKSESIBILITAS", "permintaan berbahaya", PURPLE),
             ("4", "HP DIKUASAI PELAKU", "data dicuri, file bisa dikunci", RED)]
    y0, gap = 690, 208
    for i, (num, lab, sub, col) in enumerate(steps):
        q = seg(tl, 0.3 + i * 0.85, 0.85 + i * 0.85)
        if q <= 0:
            continue
        k = eob(q)
        al2 = q * al
        yy = y0 + i * gap
        panel(img, 130, yy - 78, 950, yy + 78, alpha=al2, radius=38)
        dot_on(img, 196, yy, 44 * k, col, al2)
        paste_c(img, 196, yy, num, font(FB, 44), WHITE, al2, scale=0.8 + 0.2 * k)
        paste_r(img, 268, yy - 18, lab, font(FB, 38), INK, al2)
        paste_r(img, 268, yy + 34, sub, font(FM, 28), MUTED, al2)
        if i < len(steps) - 1:
            qq = seg(tl, 0.85 + i * 0.85, 1.25 + i * 0.85)
            if qq > 0:
                u = eo(qq)
                x = 196
                line_on(img, (x, yy + 50), (x, yy + 50 + 105 * u), mix(CREAM, col, 0.45), 6, al2 * 0.9)
                if u > 0.75:
                    poly_on(img, [(x, yy + 62 + 105 * u), (x - 16, yy + 40 + 105 * u),
                                  (x + 16, yy + 40 + 105 * u)], mix(CREAM, col, 0.45), al2)


def sc_stolen_data(img, d, sc, tl, dur, tg, accent, al, dy):
    """Apa yang bisa dicuri + dikirim ke server pelaku."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.2, 0.75)
    if q <= 0:
        return
    al2 = q * al
    cx = 340
    _phone(img, cx, 1160, 470, 700, al2)
    yy0 = 900
    rows = [("KODE OTP SMS", RED, 0.10), ("CHAT WA & TELEGRAM", RED, 0.28),
            ("PIN LAYAR & POLA", AMBER, 0.56), ("KAMERA DIAM-DIAM", AMBER, 0.84),
            ("LOKASI & KONTAK", BLUE, 1.12), ("REKAMAN LAYAR", BLUE, 1.40)]
    for i, (lab, col, t0) in enumerate(rows):
        qq = seg(tl, 1.0 + t0, 1.4 + t0)
        if qq <= 0:
            continue
        yy = yy0 + i * 88
        rrect_on(img, 176, yy - 28, 504, yy + 28, 26, mix(WHITE, col, 0.20), qq * al2,
                 outline=mix(CREAM, col, 0.55), width=2)
        dot_on(img, 204, yy, 11, col, qq * al2)
        f = font(FM, 25) if tw(lab, font(FM, 25)) <= 268 else font(FM, 21)
        paste_r(img, 224, yy, lab, f, mix(col, INK, 0.25), qq * al2)
    # server pelaku
    q = seg(tl, 1.7, 2.4)
    if q > 0:
        al3 = q * al2
        scx, scy = 810, 1050
        for i in range(3):
            rrect_on(img, scx - 120, scy - 70 + i * 54, scx + 120, scy - 26 + i * 54, 16,
                     mix(WHITE, INK, 0.10), al3, outline=mix(CREAM, INK, 0.28), width=3)
        dot_on(img, scx - 80, scy - 48, 9, RED, al3)
        dot_on(img, scx - 50, scy - 48, 9, AMBER, al3)
        paste_c(img, scx, scy + 130, "SERVER PELAKU", font(FS, 30), mix(CREAM, INK, 0.42), al3)
        for i in range(4):
            u = ((tg * 0.75) + i / 4) % 1.0
            x1 = 540 + (scx - 140 - 540) * u
            y1 = 1000 + (scy - 40 - 1000) * u
            dot_on(img, x1, y1, 11, mix(accent, INK, 0.15), al3 * (0.35 + 0.65 * (1 - u)))
    # catatan OTP
    q = seg(tl, 2.8, 3.4)
    if q > 0:
        pill(img, 150, 1560, "OTP = KUNCI TRANSAKSI BANK", font(FB, 34), WHITE, bg=RED,
             alpha=q * al, pad=32, hgt=66)


def sc_not_cracked(img, d, sc, tl, dur, tg, accent, al, dy):
    """Klarifikasi: enkripsi tidak dibobol, izin aksesibilitas pintunya."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.25, 0.8)
    if q <= 0:
        return
    al2 = q * al
    # panel kiri: enkripsi aman
    panel(img, 70, 640, 520, 1300, alpha=seg(tl, 0.4, 1.0) * al2, radius=44, fill=mix(WHITE, GREEN, 0.06))
    qq = seg(tl, 0.8, 1.4)
    if qq > 0:
        al3 = qq * al2
        # ikon gembok
        rrect_on(img, 250, 800, 340, 890, 18, GREEN, al3)
        ring_on(img, 295, 790, 34, GREEN, 9, al3)
        dot_on(img, 295, 845, 10, WHITE, al3)
        paste_c(img, 295, 950, "ENKRIPSI", font(FB, 44), mix(GREEN, INK, 0.10), al3)
        paste_c(img, 295, 1006, "WHATSAPP", font(FB, 44), mix(GREEN, INK, 0.10), al3)
        paste_c(img, 295, 1090, "TETAP AMAN", font(FB, 50), GREEN, al3)
        paste_c(img, 295, 1150, "pesan terenkripsi di jaringan", font(FM, 27), MUTED, al3)
    # panel kanan: izin aksesibilitas
    panel(img, 560, 640, 1010, 1300, alpha=seg(tl, 1.6, 2.2) * al2, radius=44, fill=mix(WHITE, RED, 0.06))
    qq = seg(tl, 2.0, 2.6)
    if qq > 0:
        al3 = qq * al2
        _phone(img, 785, 880, 330, 400, al3)
        paste_c(img, 785, 800, "Izinkan aksesibilitas?", font(FS, 23), INK, al3)
        rrect_on(img, 700, 890, 870, 936, 23, RED, al3)
        paste_c(img, 785, 913, "IZINKAN", font(FB, 27), WHITE, al3)
        rrect_on(img, 700, 952, 870, 998, 23, mix(CREAM, INK, 0.12), al3)
        paste_c(img, 785, 975, "TOLAK", font(FB, 27), mix(CREAM, INK, 0.45), al3)
        paste_c(img, 785, 1148, "INILAH PINTUNYA", font(FB, 42), RED, al3)
        paste_c(img, 785, 1212, "app membaca yang tampil di layar", font(FM, 25), MUTED, al3)
    q = seg(tl, 3.2, 3.8)
    if q > 0:
        paste_c(img, W / 2, 1420, "JADI: IZIN ITU YANG HARUS DIJAGA", font(FB, 42),
                mix(accent, INK, 0.15), q * al)
        paste_c(img, W / 2, 1500, "bukan sistem WhatsApp-nya yang bocor", font(FM, 32), MUTED, q * al)


def sc_protect_steps(img, d, sc, tl, dur, tg, accent, al, dy):
    """Empat langkah perlindungan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    items = [("JANGAN INSTALL APK LUAR PLAY STORE", "sumber resmi saja", BLUE, 0.3),
             ("TOLAK IZIN AKSESIBILITAS", "kecuali app tepercaya", PURPLE, 0.85),
             ("AKTIFKAN PLAY PROTECT", "pindai app berbahaya", GREEN, 1.4),
             ("UPDATE KEAMANAN ANDROID", "patch terbaru", AMBER, 1.95)]
    for i, (lab, sub, col, t0) in enumerate(items):
        q = seg(tl, t0, t0 + 0.55)
        if q <= 0:
            continue
        k = eob(q)
        al2 = q * al
        x0 = 90 + (i % 2) * 470
        y0 = 700 + (i // 2) * 400
        panel(img, x0, y0, x0 + 430, y0 + 340, alpha=al2, radius=40)
        dot_on(img, x0 + 78, y0 + 84, 46 * k, col, al2)
        line_on(img, (x0 + 56, y0 + 86), (x0 + 72, y0 + 104), WHITE, 11, al2)
        line_on(img, (x0 + 72, y0 + 104), (x0 + 102, y0 + 62), WHITE, 11, al2)
        f = font(FB, 34)
        for j, l in enumerate(wrap(lab, f, 340)[:2]):
            qq = seg(tl, t0 + 0.15 + j * 0.09, t0 + 0.6 + j * 0.09)
            if qq > 0:
                paste_c(img, x0 + 215, y0 + 190 + j * 44, l, f, INK, qq * al2)
        qq = seg(tl, t0 + 0.3, t0 + 0.75)
        if qq > 0:
            paste_c(img, x0 + 215, y0 + 290, sub, font(FM, 28), MUTED, qq * al2)
    q = seg(tl, dur - 1.6, dur - 1.0)
    if q > 0:
        paste_c(img, W / 2, 1560, "PLAY PROTECT SUDAH BISA BLOKIR MALWARE INI", font(FB, 36),
                mix(accent, INK, 0.15), q * al)


def sc_check_now(img, d, sc, tl, dur, tg, accent, al, dy):
    """Cek pengaturan sekarang."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.2, 0.8)
    if q <= 0:
        return
    al2 = q * al
    panel(img, 130, 640, 950, 1420, alpha=al2, radius=44)
    paste_r(img, 180, 720, "PENGATURAN", font(FS, 30), mix(CREAM, INK, 0.45), al2)
    rows = [("Aksesibilitas", "lihat aplikasi dengan izin", 0.5),
            ("Aplikasi tidak dikenal", "hapus bila asing", 1.3)]
    yy = 800
    for lab, sub, t0 in rows:
        qq = seg(tl, t0, t0 + 0.5)
        if qq <= 0:
            yy += 190
            continue
        k = eob(qq)
        al3 = qq * al2
        x0, x1 = 180, 900
        rrect_on(img, x0, yy - 70, x1, yy + 74, 34, mix(CREAM, INK, 0.055), al3)
        # kotak centang bercentang
        dot_on(img, x0 + 66, yy + 2, 34, accent, al3)
        line_on(img, (x0 + 50, yy + 4), (x0 + 62, yy + 22), WHITE, 10, al3)
        line_on(img, (x0 + 62, yy + 22), (x0 + 86, yy - 18), WHITE, 10, al3)
        paste_r(img, x0 + 124, yy - 22, lab, font(FB, 40), INK, al3)
        paste_r(img, x0 + 124, yy + 30, sub, font(FM, 28), MUTED, al3)
        yy += 190
    qq = seg(tl, 2.5, 3.1)
    if qq > 0:
        al3 = qq * al2
        x0, x1 = 180, 900
        y0 = 1180
        rrect_on(img, x0, y0 - 70, x1, y0 + 74, 34, mix(CREAM, INK, 0.055), al3)
        paste_r(img, x0 + 60, y0 - 22, "Play Protect", font(FB, 40), INK, al3)
        paste_r(img, x0 + 60, y0 + 30, "pindai & pembaruan otomatis", font(FM, 28),
                mix(GREEN, INK, 0.2), al3)
        rrect_on(img, x1 - 120, y0 - 20, x1 - 10, y0 + 40, 30, mix(GREEN, INK, 0.15), al3)
        dot_on(img, x1 - 36, y0 + 10, 24, WHITE, al3)
    qq = seg(tl, 3.5, 4.1)
    if qq > 0:
        paste_c(img, W / 2, 1520, "JANGAN PASANG APK ANEH LAGI", font(FB, 42),
                mix(accent, INK, 0.15), qq * al)



# ---------- Ep11: kenapa langit berwarna biru ----------
SKY_PALE = mix(BLUE, WHITE, 0.66)
SKY_MID = mix(BLUE, WHITE, 0.34)
SKY_DARK = mix(BLUE, INK, 0.22)
SPACE_BG = mix(INK, BLUE, 0.16)
SPEC_COLS = [("400", PURPLE), ("450", BLUE), ("490", mix(BLUE, GREEN, 0.45)),
             ("530", GREEN), ("580", AMBER), ("610", (228, 120, 48)), ("700", RED)]


def _pill_c(img, cx, cy, text, f, fill, alpha=1.0, dot=False, pad=36, hgt=None, bg=None):
    """Pil berisi teks, diposisikan tepat di tengah (cx, cy)."""
    if alpha <= 0.01 or not text:
        return
    w_ = tw(text, f)
    h_ = hgt or (tlh(f) + 26)
    ww = w_ + (34 if dot else 0)
    _note("pil-c", cx - ww / 2 - pad, cy - h_ / 2, cx + ww / 2 + pad, cy + h_ / 2, text)
    if bg is None:
        bg = mix(WHITE, fill, 0.13)
    rrect_on(img, cx - (ww / 2 + pad), cy - h_ / 2, cx + (ww / 2 + pad), cy + h_ / 2,
             h_ / 2, bg, alpha)
    if dot:
        dot_on(img, cx - ww / 2 + 3, cy, 9, fill, alpha)
    paste_c(img, cx + (17 if dot else 0), cy, text, f, fill, alpha)


def _ground_edge(x, yc=1000.0, curv=130.0, span=500.0):
    """Lengkung permukaan bumi sederhana (makin ke tepi makin turun)."""
    u = (x - 540.0) / span
    return yc + curv * (u * u)


def _ground(img, yc, curv, fill, alpha, span=520.0, thick=520.0):
    pts = [(x, _ground_edge(x, yc, curv, span)) for x in range(50, 1035, 35)]
    poly = pts + [(1035, yc + thick), (50, yc + thick)]
    poly_on(img, poly, fill, alpha)


def sc_intro_sky(img, d, sc, tl, dur, tg, accent, al, dy):
    """Pembuka: jendela langit biru, matahari, dan cahaya yang terhambur."""
    y = 460
    for i, l in enumerate(sc["lines"]):
        fsz = 150
        while fsz > 58 and tw(l, font(FB, fsz)) > 950:
            fsz -= 4
        f = font(FB, fsz)
        q = seg(tl, 0.05 + i * 0.22, 0.55 + i * 0.22)
        if q <= 0:
            continue
        k = eob(q)
        col = accent if i == len(sc["lines"]) - 1 else INK
        paste_c(img, W / 2, y + (1 - k) * 40, l, f, col, q * al, scale=0.9 + 0.1 * k)
        y += 156
    q = seg(tl, 0.85, 1.45)
    if q <= 0:
        return
    al2 = q * al
    k = eio(q)
    x0, yy0, x1, yy1 = 150, 880 + (1 - k) * 60, 930, 1560 + (1 - k) * 60
    rrect_on(img, x0, yy0, x1, yy1, 46, SKY_MID, al2)
    rrect_on(img, x0 + 12, yy0 + 12, x1 - 12, yy0 + 250, 38, SKY_DARK, al2 * 0.5)
    qq = seg(tl, 1.15, 1.6)
    if qq > 0:
        alk = qq * al2
        sx, sy = 300, yy0 + 165
        for i in range(8):
            a = i * math.pi / 4 + tg * 0.2
            r0, r1 = 76, 112 + 9 * math.sin(tg * 3 + i)
            line_on(img, (sx + r0 * math.cos(a), sy + r0 * math.sin(a)),
                    (sx + r1 * math.cos(a), sy + r1 * math.sin(a)), AMBER, 9, alk * 0.8)
        dot_on(img, sx, sy, 50, AMBER, alk)
        dot_on(img, sx, sy, 24, mix(AMBER, WHITE, 0.8), alk)
    qq = seg(tl, 1.45, 2.05)
    if qq > 0:
        alk = qq * al2
        cx, cy = 645, yy0 + 405
        line_on(img, (368, yy0 + 215), (cx, cy), mix(WHITE, AMBER, 0.18), 13, alk)
        for i in range(3):
            u = ((tg * 0.75) + i / 3.0) % 1.0
            ring_on(img, cx, cy, 46 + 130 * u, BLUE, 6, alk * (1 - u) * 0.75)
        for i in range(18):
            a = i * 2.399
            rr = 130 + ((i * 97) % 300)
            bx = cx + rr * math.cos(a) * 1.1
            by = cy + rr * math.sin(a) * 0.62
            if not (x0 + 40 < bx < x1 - 40 and yy0 + 40 < by < yy1 - 110):
                continue
            dot_on(img, bx, by, 13 + 5 * math.sin(tg * 3 + i), mix(BLUE, WHITE, 0.15), alk * 0.7)
    qq = seg(tl, 1.95, 2.45)
    if qq > 0:
        alk = qq * al2
        poly_on(img, [(x0 + 20, yy1 - 16), (x0 + 220, yy1 - 200), (x0 + 430, yy1 - 16)],
                mix(GREEN, INK, 0.32), alk)
        poly_on(img, [(x0 + 330, yy1 - 16), (x0 + 560, yy1 - 155), (x0 + 790, yy1 - 16)],
                mix(GREEN, INK, 0.5), alk)
        _pill_c(img, W / 2, 1655, "cahaya putih dihamburkan jadi biru", font(FS, 32),
                mix(BLUE, INK, 0.15), alk, dot=True)


def sc_white_light(img, d, sc, tl, dur, tg, accent, al, dy):
    """Cahaya putih adalah campuran warna dengan panjang gelombang berbeda."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.25, 0.8)
    if q <= 0:
        return
    al2 = q * al
    px, py = 300, 930
    qq = seg(tl, 0.5, 1.0)
    if qq > 0:
        line_on(img, (110, 800), (px - 42, py - 62), mix(WHITE, INK, 0.42), 15, qq * al2)
        dot_on(img, 110, 800, 34, mix(WHITE, AMBER, 0.35), qq * al2)
    qq = seg(tl, 0.9, 1.4)
    if qq > 0:
        poly_on(img, [(px, py - 128), (px - 118, py + 118), (px + 118, py + 118)],
                mix(WHITE, BLUE, 0.10), qq * al2 * 0.95,
                outline=mix(CREAM, INK, 0.30), width=4)
    for i, (lab, col) in enumerate(SPEC_COLS):
        t0 = 1.25 + i * 0.13
        qq = seg(tl, t0, t0 + 0.55)
        if qq <= 0:
            continue
        y_mid = 660 + i * 64
        poly_on(img, [(px + 78, py - 16), (px + 128, py + 8), (742, y_mid + 26), (734, y_mid - 26)],
                col, qq * al2 * 0.95)
        paste_r(img, 890, y_mid, lab + " nm", font(FM, 26), mix(col, INK, 0.2), qq * al2)
    qq = seg(tl, 2.3, 2.9)
    if qq > 0:
        alk = qq * al2
        y = 1265
        paste_r(img, 120, y - 62, "panjang gelombang", font(FS, 32), mix(INK, BLUE, 0.25), alk)
        for i, (lab, col) in enumerate(reversed(SPEC_COLS)):
            xx0 = 120 + i * 108
            rrect_on(img, xx0, y, xx0 + 104, y + 62, 12, col, alk)
        paste_r(img, 120, y + 130, "pendek · mudah dihamburkan", font(FM, 27), mix(BLUE, INK, 0.2), alk)
        paste_c(img, 800, y + 130, "panjang", font(FM, 27), mix(RED, INK, 0.2), alk)
        _pill_c(img, W / 2, 1550, "cahaya putih = semua warna pelangi", font(FS, 33),
                mix(PURPLE, INK, 0.12), alk, dot=True)


def sc_air_scatter(img, d, sc, tl, dur, tg, accent, al, dy):
    """Molekul udara menghamburkan gelombang pendek ke segala arah."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    paste_r(img, 110, 660, "gelombang pendek", font(FS, 30), mix(BLUE, INK, 0.15), al2)
    paste_r(img, 110, 706, "terpental ke segala arah", font(FM, 26), MUTED, al2)
    qq = seg(tl, 0.6, 1.15)
    if qq > 0:
        alk = qq * al2
        sx, sy = 165, 980
        for i in range(8):
            a = i * math.pi / 4 + tg * 0.18
            line_on(img, (sx + 68 * math.cos(a), sy + 68 * math.sin(a)),
                    (sx + 96 * math.cos(a), sy + 96 * math.sin(a)), AMBER, 8, alk * 0.8)
        dot_on(img, sx, sy, 44, AMBER, alk)
    qq = seg(tl, 0.9, 1.5)
    if qq > 0:
        line_on(img, (222, 1000), (620, 1050), mix(WHITE, AMBER, 0.18), 13, qq * al2)
    mols = [(560, 940), (620, 1010), (690, 950), (585, 1080), (665, 1110), (725, 1050),
            (540, 1160), (700, 1190), (640, 1240), (770, 1140), (500, 1050), (735, 950)]
    for i, (mx, my) in enumerate(mols):
        qq = seg(tl, 1.0 + i * 0.05, 1.35 + i * 0.05)
        if qq <= 0:
            continue
        dot_on(img, mx, my, 13, mix(BLUE, INK, 0.25), qq * al2 * 0.9)
    qq = seg(tl, 1.3, 1.9)
    if qq > 0:
        alk = qq * al2
        for i in range(3):
            u = ((tg * 0.8) + i / 3.0) % 1.0
            ring_on(img, 645, 1035, 60 + 160 * u, BLUE, 7, alk * (1 - u) * 0.7)
        for i in range(22):
            a = i * 2.399 + 0.4
            rr = 150 + ((i * 83) % 330)
            bx = 645 + rr * math.cos(a) * 1.08
            by = 1035 + rr * math.sin(a) * 0.78
            if not (110 < bx < 990 and 780 < by < 1560):
                continue
            dot_on(img, bx, by, 12 + 5 * math.sin(tg * 3.4 + i), mix(BLUE, WHITE, 0.12), alk * 0.72)
    qq = seg(tl, 1.6, 2.2)
    if qq > 0:
        alk = qq * al2
        line_on(img, (700, 1090), (930, 1420), RED, 11, alk * 0.95)
        paste_r(img, 110, 1440, "gelombang panjang", font(FS, 30), mix(RED, INK, 0.15), alk)
        paste_r(img, 110, 1486, "lurus terus, tidak terhambur", font(FM, 26), MUTED, alk)
        paste_c(img, 800, 1500, "N₂ · O₂", font(FM, 30), mix(INK, BLUE, 0.3), alk)
    qq = seg(tl, 2.1, 2.7)
    if qq > 0:
        alk = qq * al2
        hx, hy = 830, 1600
        rrect_on(img, hx - 92, hy + 44, hx + 92, hy + 160, 46, mix(BLUE, INK, 0.25), alk)
        dot_on(img, hx, hy, 44, mix(CREAM, INK, 0.35), alk)
        for i in range(3):
            line_on(img, (hx - 130 - i * 46, hy - 130 - i * 30), (hx - 40, hy - 40),
                    mix(BLUE, WHITE, 0.25), 8, alk * 0.75)


def sc_not_violet(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kalau ungu gelombangnya lebih pendek, kenapa yang terlihat biru?"""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    y = 620
    for i, (lab, col) in enumerate(SPEC_COLS):
        qq = seg(tl, 0.5 + i * 0.08, 0.9 + i * 0.08)
        if qq <= 0:
            continue
        xx0 = 110 + i * 123
        rrect_on(img, xx0, y, xx0 + 119, y + 74, 10, col, qq * al2 * 0.95)
    paste_r(img, 110, y + 150, "ungu 400 nm", font(FM, 27), mix(PURPLE, INK, 0.2), al2)
    paste_c(img, 540, y + 150, "hijau 530 nm", font(FM, 27), mix(GREEN, INK, 0.25), al2)
    paste_c(img, 890, y + 150, "merah 700 nm", font(FM, 27), mix(RED, INK, 0.2), al2)
    qq = seg(tl, 1.2, 1.8)
    if qq > 0:
        alk = qq * al2
        paste_r(img, 110, 960, "kepekaan mata manusia", font(FS, 32), mix(INK, BLUE, 0.25), alk)
        bars = [("ungu", PURPLE, 300, 1.45), ("biru", BLUE, 690, 1.85)]
        yy = 1050
        for lab, col, w_, t0 in bars:
            q3 = seg(tl, t0, t0 + 0.6)
            if q3 <= 0:
                yy += 150
                continue
            k = eob(q3)
            paste_r(img, 110, yy, lab, font(FS, 30), col, q3 * al2)
            rrect_on(img, 250, yy - 30, 950, yy + 30, 30, mix(CREAM, INK, 0.08), q3 * al2 * 0.8)
            rrect_on(img, 250, yy - 30, 250 + w_ * k, yy + 30, 30, col, q3 * al2)
            yy += 150
    qq = seg(tl, 2.3, 2.9)
    if qq > 0:
        alk = qq * al2
        paste_r(img, 110, 1400, "Mata jauh lebih peka pada biru.", font(FS, 31), INK, alk)
        paste_r(img, 110, 1456, "Sebagian ungu juga diserap lapisan ozon.", font(FS, 31), INK, alk)
        _pill_c(img, W / 2, 1580, "jadi yang dominan terlihat: biru", font(FS, 32),
                mix(BLUE, INK, 0.15), alk, dot=True)


def sc_sunset_red(img, d, sc, tl, dur, tg, accent, al, dy):
    """Matahari rendah: jalur cahaya jauh lebih panjang, biru habis terhambur."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.25, 0.8)
    if q <= 0:
        return
    al2 = q * al
    _ground(img, 1010, 130, mix(GREEN, INK, 0.40), al2)
    _ground(img, 1160, 150, mix(GREEN, INK, 0.22), al2 * 0.75)
    paste_r(img, 110, 640, "siang: jalur pendek", font(FS, 30), mix(INK, BLUE, 0.25), al2)
    qq = seg(tl, 0.6, 1.2)
    if qq > 0:
        alk = qq * al2
        sx, sy = 505, 700
        for i in range(8):
            a = i * math.pi / 4 + tg * 0.2
            line_on(img, (sx + 62 * math.cos(a), sy + 62 * math.sin(a)),
                    (sx + 92 * math.cos(a), sy + 92 * math.sin(a)), AMBER, 9, alk * 0.8)
        dot_on(img, sx, sy, 44, AMBER, alk)
        line_on(img, (sx, sy + 52), (sx + 6, _ground_edge(sx + 6, 1010, 130) - 20),
                mix(WHITE, AMBER, 0.35), 13, alk)
    qq = seg(tl, 1.2, 2.0)
    if qq > 0:
        alk = qq * al2
        k = eio(qq)
        sx = 700 - 520 * k
        sy = _ground_edge(sx, 1010, 130) - 150
        for i in range(8):
            a = i * math.pi / 4 + tg * 0.2
            line_on(img, (sx + 54 * math.cos(a), sy + 54 * math.sin(a)),
                    (sx + 80 * math.cos(a), sy + 80 * math.sin(a)), mix(AMBER, RED, 0.4), 8, alk * 0.75)
        dot_on(img, sx, sy, 38, mix(AMBER, RED, 0.35), alk)
        line_on(img, (sx + 30, sy + 26), (836, _ground_edge(836, 1010, 130) - 60), RED, 12, alk)
        for i in range(7):
            u = 0.25 + i * 0.11
            bx = (sx + 30) + (806) * u
            by = (sy + 26) + (_ground_edge(836, 1010, 130) - 86 - sy) * u
            dot_on(img, bx, by, 11 + 4 * math.sin(tg * 4 + i), BLUE, alk * 0.85)
        rrect_on(img, 100, 1400, 980, 1545, 32, mix(CREAM, WHITE, 0.45), alk * 0.94)
        paste_r(img, 132, 1440, "senja: jalur puluhan kali lebih panjang", font(FS, 29),
                mix(RED, INK, 0.15), alk)
        paste_r(img, 132, 1495, "biru terhambur habis sebelum sampai ke kita", font(FM, 26), MUTED, alk)
    qq = seg(tl, 1.9, 2.5)
    if qq > 0:
        alk = qq * al2
        hx, hy = 870, _ground_edge(870, 1010, 130) - 92
        rrect_on(img, hx - 74, hy + 34, hx + 74, hy + 128, 40, mix(BLUE, INK, 0.25), alk)
        dot_on(img, hx, hy, 38, mix(CREAM, INK, 0.3), alk)
        skyline(img, 560, 1010, _ground_edge(560, 1010, 130) + 4, mix(INK, BLUE, 0.25),
                alk * 0.55, seed=9, scale=0.55)


def sc_space_black(img, d, sc, tl, dur, tg, accent, al, dy):
    """Di luar atmosfer tidak ada yang menghamburkan cahaya, maka langit hitam."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.25, 0.8)
    if q <= 0:
        return
    al2 = q * al
    bands = [("permukaan · biru terang", SKY_MID, 1, INK, 10),
             ("gunung · lebih tua", mix(BLUE, WHITE, 0.42), 2, INK, 7),
             ("pesawat · biru gelap", mix(BLUE, INK, 0.12), 3, WHITE, 4),
             ("luar angkasa · hitam", SPACE_BG, 4, WHITE, 0)]
    yy = 640
    for lab, col, t0, tcol, ndots in bands:
        qq = seg(tl, t0 * 0.28, t0 * 0.28 + 0.5)
        yy += 4
        if qq <= 0:
            yy += 176
            continue
        alk = qq * al2
        rrect_on(img, 150, yy, 930, yy + 170, 34, col, alk)
        paste_r(img, 200, yy + 62, lab, font(FS, 30), tcol, alk)
        if ndots:
            paste_r(img, 200, yy + 118, "molekul udara: " + "•" * ndots, font(FM, 26),
                    mix(tcol, col, 0.4), alk * 0.85)
        if t0 == 1:
            dot_on(img, 850, yy + 55, 30, AMBER, alk)
        elif t0 == 2:
            poly_on(img, [(800, yy + 140), (862, yy + 32), (924, yy + 140)],
                    mix(GREEN, INK, 0.3), alk)
        elif t0 == 3:
            poly_on(img, [(790, yy + 96), (900, yy + 76), (900, yy + 106), (790, yy + 126)],
                    mix(WHITE, INK, 0.25), alk)
        else:
            for i in range(7):
                star4(img, 790 + (i * 47) % 130, yy + 34 + (i * 61) % 110, 13,
                      mix(WHITE, CREAM, 0.2), alk * 0.9)
            dot_on(img, 880, yy + 120, 22, mix(AMBER, WHITE, 0.3), alk)
        yy += 176
    qq = seg(tl, 2.1, 2.7)
    if qq > 0:
        alk = qq * al2
        paste_r(img, 110, 1420, "Tanpa molekul udara, cahaya tidak dihamburkan.", font(FS, 30),
                INK, alk)
        paste_r(img, 110, 1474, "Matahari tetap terang, langit tetap hitam.", font(FS, 30), INK, alk)
        _pill_c(img, W / 2, 1590, "langit berwarna karena cahaya yang terhambur", font(FS, 31),
                mix(BLUE, INK, 0.18), alk, dot=True)



# ---------- Ep13: kenapa HP cepat panas ----------
HOT = (214, 92, 40)
NAVY = (52, 80, 110)


def _wavy(img, x, y0, y1, amp, color, width, alpha, fase=0.0, n=3):
    """Tiga garis gelombang naik (simbol panas)."""
    for k in range(n):
        xx = x + k * 46
        pts = []
        for i in range(13):
            u = i / 12.0
            yy = y0 + (y1 - y0) * u
            pts.append((xx + amp * math.sin(u * math.pi * 2.4 + fase + k * 0.7), yy))
        for i in range(len(pts) - 1):
            line_on(img, pts[i], pts[i + 1], color, width, alpha)


def _thermo(img, x, y0, y1, level, alpha, tanda=None):
    """Termometer vertikal; level 0..1 mengisi bagian bawah."""
    w = 42
    bulb = 58
    rrect_on(img, x - w / 2, y0, x + w / 2, y1 - bulb * 0.8, w / 2, WHITE, alpha,
             outline=mix(CREAM, INK, 0.35), width=4)
    ys = y1 - bulb * 0.8 - (y1 - bulb * 0.8 - y0 - 14) * clamp(level)
    rrect_on(img, x - w / 2 + 8, ys, x + w / 2 - 8, y1 - bulb * 0.8 - 6, (w - 16) / 2,
             mix(HOT, RED, 0.35), alpha)
    dot_on(img, x, y1 - bulb * 0.5, bulb, mix(HOT, RED, 0.35), alpha)
    for i in range(5):
        yy = y0 + 24 + i * (y1 - bulb - y0) / 5.0
        line_on(img, (x + w / 2 + 10, yy), (x + w / 2 + 34, yy), mix(CREAM, INK, 0.3), 4, alpha)
    if tanda:
        paste_r(img, x + w / 2 + 44, y0 + (y1 - bulb - y0) * 0.28, tanda, font(FS, 27),
                mix(RED, INK, 0.1), alpha)


def sc_intro_heat(img, d, sc, tl, dur, tg, accent, al, dy):
    """Pembuka: HP mengeluarkan panas + termometer naik."""
    y = 450
    for i, l in enumerate(sc["lines"]):
        fsz = 150
        while fsz > 58 and tw(l, font(FB, fsz)) > 950:
            fsz -= 4
        f = font(FB, fsz)
        q = seg(tl, 0.05 + i * 0.22, 0.55 + i * 0.22)
        if q <= 0:
            continue
        k = eob(q)
        col = accent if i == len(sc["lines"]) - 1 else INK
        paste_c(img, W / 2, y + (1 - k) * 40, l, f, col, q * al, scale=0.9 + 0.1 * k)
        y += 156
    q = seg(tl, 0.85, 1.45)
    if q <= 0:
        return
    al2 = q * al
    k = eio(q)
    _phone(img, 330, 1180 + (1 - k) * 60, 400, 620, al2)
    qq = seg(tl, 1.2, 2.1)
    if qq > 0:
        alk = qq * al2
        _wavy(img, 250, 830, 1010, 16, HOT, 9, alk * 0.9, fase=tg * 2.2)
        _wavy(img, 330, 800, 1000, 18, mix(HOT, AMBER, 0.4), 9, alk * 0.85, fase=tg * 2.4 + 1)
        paste_c(img, 330, 790, "panas naik", font(FM, 26), mix(HOT, INK, 0.15), alk)
    qq = seg(tl, 1.6, 2.4)
    if qq > 0:
        alk = qq * al2
        lvl = 0.35 + 0.6 * clamp(eio(seg(tl, 1.6, 3.0)))
        _thermo(img, 760, 830, 1290, lvl, alk, tanda="45 °C")
        paste_c(img, 760, 1380, "batas aman", font(FM, 26), MUTED, alk)
        paste_c(img, 760, 1430, "0-35 °C", font(FS, 30), mix(GREEN, INK, 0.2), alk)
    qq = seg(tl, 2.4, 3.0)
    if qq > 0:
        _pill_c(img, W / 2, 1620, "PANAS = MUSUH NOMOR SATU BATERAI", font(FS, 30),
                mix(accent, INK, 0.15), qq * al2, dot=True)


def sc_heat_source(img, d, sc, tl, dur, tg, accent, al, dy):
    """Tiga sumber panas di dalam satu bodi kecil."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    qq = seg(tl, 0.45, 1.0)
    if qq > 0:
        rrect_on(img, 190, 700, 620, 1420, 40, WHITE, qq * al2,
                 outline=mix(CREAM, INK, 0.30), width=4)
    zona = [("PROSESOR", "bekerja keras saat main game", 760, mix(HOT, RED, 0.2), 0.0),
            ("BATERAI", "menghasilkan panas saat cas", 990, mix(AMBER, HOT, 0.35), 0.5),
            ("MODEM", "cari sinyal lebih keras", 1220, mix(BLUE, NAVY, 0.3), 1.0)]
    for i, (judul, sub, yy, col, t0) in enumerate(zona):
        qq = seg(tl, 0.8 + t0, 1.25 + t0)
        if qq <= 0:
            continue
        alk = qq * al2
        rrect_on(img, 215, yy, 595, yy + 170, 26, mix(WHITE, col, 0.16), alk,
                 outline=mix(CREAM, col, 0.5), width=3)
        dot_on(img, 262, yy + 56, 26, col, alk)
        if i == 0:
            line_on(img, (248, yy + 56), (276, yy + 56), WHITE, 6, alk)
            line_on(img, (262, yy + 42), (262, yy + 70), WHITE, 6, alk)
        elif i == 1:
            rrect_on(img, 250, yy + 44, 274, yy + 70, 5, WHITE, alk)
        else:
            for b in range(3):
                hh = 12 + b * 10
                line_on(img, (250 + b * 12, yy + 70), (250 + b * 12, yy + 70 - hh), WHITE, 5, alk)
        paste_r(img, 300, yy + 48, judul, font(FB, 32), mix(col, INK, 0.2), alk)
        paste_r(img, 300, yy + 108, sub, font(FM, 25), MUTED, alk)
        line_on(img, (620, yy + 85), (700, yy + 85), col, 8, alk * 0.8)
        dot_on(img, 716, yy + 85, 12, col, alk)
    qq = seg(tl, 2.1, 2.7)
    if qq > 0:
        alk = qq * al2
        _wavy(img, 740, 900, 1120, 14, HOT, 8, alk * 0.8, fase=tg * 2.0)
        paste_r(img, 830, 960, "panas", font(FS, 30), mix(HOT, INK, 0.15), alk)
        paste_r(img, 830, 1010, "menumpuk", font(FS, 30), mix(HOT, INK, 0.15), alk)
        _pill_c(img, W / 2, 1540, "TIGA SUMBER PANAS DI SATU BODI KECIL", font(FS, 29),
                mix(accent, INK, 0.15), alk, dot=True)
        paste_c(img, W / 2, 1630, "HP tidak punya kipas, jadi panas keluar lewat bodi",
                font(FM, 26), MUTED, alk)


def sc_causes4(img, d, sc, tl, dur, tg, accent, al, dy):
    """Empat kebiasaan yang paling sering memicu HP panas."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    items = [("GAME BERAT", "prosesor kerja penuh", HOT, 0),
             ("CAS SAMBIL MAIN", "dua sumber panas", AMBER, 1),
             ("SINYAL LEMAH", "modem cari jaringan", BLUE, 2),
             ("PANAS & CASING", "panas tidak bisa keluar", PURPLE, 3)]
    for i, (judul, sub, col, t0) in enumerate(items):
        qq = seg(tl, 0.55 + t0 * 0.3, 1.0 + t0 * 0.3)
        if qq <= 0:
            continue
        alk = qq * al2
        x0 = 120 + (i % 2) * 440
        y0 = 720 + (i // 2) * 330
        rrect_on(img, x0, y0, x0 + 400, y0 + 290, 34, mix(WHITE, col, 0.14), alk,
                 outline=mix(CREAM, col, 0.5), width=3)
        # ikon sederhana per kartu
        cx, cy = x0 + 70, y0 + 78
        dot_on(img, cx, cy, 38, col, alk)
        if i == 0:
            line_on(img, (cx - 16, cy), (cx + 16, cy), WHITE, 7, alk)
            line_on(img, (cx, cy - 16), (cx, cy + 16), WHITE, 7, alk)
        elif i == 1:
            rrect_on(img, cx - 10, cy - 20, cx + 10, cy + 20, 6, WHITE, alk)
            line_on(img, (cx, cy + 30), (cx, cy + 14), WHITE, 6, alk)
        elif i == 2:
            for b in range(3):
                hh = 8 + b * 9
                line_on(img, (cx - 14 + b * 14, cy + 18), (cx - 14 + b * 14, cy + 18 - hh), WHITE, 5, alk)
        else:
            dot_on(img, cx, cy, 15, WHITE, alk)
            for a in range(8):
                aa = a * math.pi / 4 + tg * 0.2
                line_on(img, (cx + 22 * math.cos(aa), cy + 22 * math.sin(aa)),
                        (cx + 32 * math.cos(aa), cy + 32 * math.sin(aa)), WHITE, 5, alk * 0.9)
        f = font(FB, 29)
        while tw(judul, f) > 248 and f.size > 17:
            f = font(FB, f.size / SS - 1)
        paste_r(img, x0 + 124, y0 + 62, judul, f, mix(col, INK, 0.2), alk)
        fs2 = font(FM, 25)
        while tw(sub, fs2) > 330 and fs2.size > 16:
            fs2 = font(FM, fs2.size / SS - 1)
        paste_r(img, x0 + 40, y0 + 138, sub, fs2, MUTED, alk)
        # ilustrasi kecil di bawah
        qq2 = seg(tl, 1.0 + t0 * 0.3, 1.4 + t0 * 0.3)
        if qq2 > 0:
            _wavy(img, x0 + 60, y0 + 200, y0 + 258, 10, col, 6, qq2 * alk * 0.75,
                  fase=tg * 2.0 + i, n=4)
    qq = seg(tl, 2.5, 3.1)
    if qq > 0:
        _pill_c(img, W / 2, 1620, "KENALI PEMICUNYA, LALU KURANGI", font(FS, 30),
                mix(accent, INK, 0.15), qq * al2, dot=True)


def sc_throttle(img, d, sc, tl, dur, tg, accent, al, dy):
    """Apa akibatnya: baterai menua lebih cepat & HP jadi lemot."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    # kiri: baterai menua
    qq = seg(tl, 0.5, 1.1)
    if qq > 0:
        alk = qq * al2
        paste_r(img, 110, 700, "BATERAI MENUA LEBIH CEPAT", font(FB, 31), mix(RED, INK, 0.15), alk)
        for i in range(5):
            q3 = seg(tl, 0.8 + i * 0.16, 1.2 + i * 0.16)
            if q3 <= 0:
                continue
            hh = 150 - i * 22
            rrect_on(img, 130 + i * 88, 860 + (150 - hh), 130 + i * 88 + 62, 1010, 12,
                     mix(WHITE, RED, 0.16), q3 * al2, outline=mix(CREAM, RED, 0.5), width=3)
            rrect_on(img, 130 + i * 88 + 8, 860 + (150 - hh) + 8, 130 + i * 88 + 54, 1002, 8,
                     RED, q3 * al2 * 0.85)
        paste_r(img, 110, 1060, "setiap +10 °C, penuaan baterai", font(FM, 26), MUTED, alk)
        paste_r(img, 110, 1112, "jadi sekitar 2 kali lebih cepat", font(FS, 28), mix(RED, INK, 0.1), alk)
    # kanan: performa turun (throttling)
    qq = seg(tl, 1.6, 2.2)
    if qq > 0:
        alk = qq * al2
        paste_r(img, 110, 1230, "HP JADI LEMOT (THROTTLING)", font(FB, 31), mix(AMBER, INK, 0.15), alk)
        rrect_on(img, 130, 1300, 950, 1352, 26, mix(CREAM, INK, 0.10), alk * 0.9)
        k = eio(seg(tl, 1.9, 2.7))
        wpenuh = 820
        rrect_on(img, 130, 1300, 130 + wpenuh * (1.0 - 0.45 * k), 1352, 26, AMBER, alk)
        paste_r(img, 110, 1400, "kecepatan prosesor diturunkan otomatis", font(FM, 26), MUTED, alk)
        paste_r(img, 110, 1452, "supaya tidak makin panas", font(FM, 26), MUTED, alk)
    qq = seg(tl, 2.4, 3.0)
    if qq > 0:
        alk = qq * al2
        _thermo(img, 850, 700, 1010, 0.55 + 0.4 * clamp(eio(seg(tl, 2.4, 3.2))), alk)
        _pill_c(img, W / 2, 1560, "PANAS MEMPERCEPAT BATERAI RUSAK", font(FS, 30),
                mix(accent, INK, 0.15), alk, dot=True)
        paste_c(img, W / 2, 1650, "Kerusakan baterai karena panas tidak bisa kembali",
                font(FM, 26), MUTED, alk)


def sc_normal_not(img, d, sc, tl, dur, tg, accent, al, dy):
    """Mana yang wajar, mana yang perlu diwaspadai."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    kol = [("WAJAR", GREEN, "hangat saat main game",
            ["hangat saat mengisi daya", "hangat saat merekam video",
             "hangat di cuaca panas"], 0.5, 0),
           ("PERLU DIWASPADAI", RED, "panas padahal tidak dipakai",
            ["bodi menggelembung", "HP restart atau mati sendiri",
             "pengisian berhenti sendiri"], 1.0, 1)]
    for judul, col, baris1, baris, t0, idx in kol:
        qq = seg(tl, t0, t0 + 0.5)
        if qq <= 0:
            continue
        alk = qq * al2
        x0 = 110 if idx == 0 else 570
        rrect_on(img, x0, 700, x0 + 400, 1380, 40, mix(WHITE, col, 0.12), alk,
                 outline=mix(CREAM, col, 0.5), width=3)
        paste_c(img, x0 + 200, 780, judul, font(FB, 32), mix(col, INK, 0.15), alk)
        dot_on(img, x0 + 200, 860, 46, col, alk)
        if idx == 0:
            line_on(img, (x0 + 172, 862), (x0 + 196, 888), WHITE, 10, alk)
            line_on(img, (x0 + 196, 888), (x0 + 232, 834), WHITE, 10, alk)
        else:
            line_on(img, (x0 + 178, 838), (x0 + 222, 882), WHITE, 11, alk)
            line_on(img, (x0 + 222, 838), (x0 + 178, 882), WHITE, 11, alk)
        f = font(FS, 26)
        while tw(baris1, f) > 300 and f.size > 16:
            f = font(FS, f.size / SS - 1)
        paste_c(img, x0 + 200, 950, baris1, f, mix(col, INK, 0.25), alk)
        yy = 1030
        for b in baris:
            q3 = seg(tl, t0 + 0.4 + (yy - 1030) / 900, t0 + 0.8 + (yy - 1030) / 900)
            if q3 <= 0:
                yy += 92
                continue
            dot_on(img, x0 + 60, yy, 10, col, q3 * al2 * 0.9)
            f2 = font(FM, 24)
            while tw(b, f2) > 262 and f2.size > 15:
                f2 = font(FM, f2.size / SS - 1)
            paste_r(img, x0 + 84, yy, b, f2, mix(INK, col, 0.25), q3 * al2)
            yy += 92
    qq = seg(tl, 2.2, 2.8)
    if qq > 0:
        _pill_c(img, W / 2, 1500, "PANAS SAAT TIDAK DIPAKAI = BAHAYA", font(FS, 30),
                mix(RED, INK, 0.12), qq * al2, dot=True)
        paste_c(img, W / 2, 1600, "Segera periksa ke service resmi", font(FM, 27), MUTED, qq * al2)


def sc_cool_tips(img, d, sc, tl, dur, tg, accent, al, dy):
    """Lima langkah praktis + satu mitos yang harus ditinggalkan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    tips = [("LEPAS CASING", "saat cas atau main game", GREEN, 0),
            ("JANGAN MAIN SAAT CAS", "dua sumber panas sekaligus", GREEN, 1),
            ("TUTUP APLIKASI LATAR", "dan turunkan kecerahan", BLUE, 2),
            ("JAUH DARI MATAHARI", "dan mobil yang panas", BLUE, 3)]
    yy = 700
    for judul, sub, col, t0 in tips:
        qq = seg(tl, 0.55 + t0 * 0.28, 1.0 + t0 * 0.28)
        yy2 = yy
        yy += 172
        if qq <= 0:
            continue
        alk = qq * al2
        rrect_on(img, 120, yy2, 960, yy2 + 148, 30, mix(WHITE, col, 0.12), alk,
                 outline=mix(CREAM, col, 0.45), width=3)
        dot_on(img, 182, yy2 + 74, 38, col, alk)
        line_on(img, (156, yy2 + 76), (176, yy2 + 98), WHITE, 9, alk)
        line_on(img, (176, yy2 + 98), (208, yy2 + 50), WHITE, 9, alk)
        paste_r(img, 244, yy2 + 58, judul, font(FB, 31), mix(col, INK, 0.2), alk)
        paste_r(img, 244, yy2 + 106, sub, font(FM, 25), MUTED, alk)
    qq = seg(tl, 1.75, 2.35)
    if qq > 0:
        alk = qq * al2
        rrect_on(img, 120, 1410, 960, 1500, 26, mix(WHITE, RED, 0.14), alk,
                 outline=mix(CREAM, RED, 0.55), width=3)
        line_on(img, (162, 1436), (196, 1474), RED, 9, alk)
        line_on(img, (196, 1436), (162, 1474), RED, 9, alk)
        paste_r(img, 224, 1455, "JANGAN MASUKKAN KE KULKAS", font(FB, 28), mix(RED, INK, 0.15), alk)
    qq = seg(tl, 2.2, 2.9)
    if qq > 0:
        alk = qq * al2
        _pill_c(img, W / 2, 1590, "HP TIDAK PUNYA KIPAS, PANAS HARUS KELUAR SENDIRI", font(FS, 27),
                mix(accent, INK, 0.15), alk, dot=True)
        paste_c(img, W / 2, 1670, "Aplikasi pendingin tidak bisa mendinginkan HP",
                font(FM, 25), MUTED, alk)


# ---------- Ep14: aurora ----------
AUR_GREEN = (58, 200, 120)
AUR_TEAL = (54, 170, 190)
AUR_PURPLE = (150, 96, 210)
AUR_RED = (222, 84, 96)


def _aurora_rays(img, x0, x1, ybase, hmax, color, alpha, tg, n=16, fase=0.0):
    """Tirai aurora: deretan 'sinar' vertikal dengan tinggi bergelombang."""
    if alpha <= 0.01:
        return
    for i in range(n):
        u = i / (n - 1.0)
        x = x0 + (x1 - x0) * u
        h = hmax * (0.55 + 0.45 * math.sin(u * math.pi * 3.1 + fase + tg * 0.9)
                    * math.sin(u * math.pi * 1.3 + fase * 0.5))
        h = max(hmax * 0.18, h)
        w = 14 + 10 * math.sin(u * 7.0 + fase)
        a = alpha * (0.55 + 0.45 * math.sin(u * 5.3 + tg * 1.4 + fase))
        poly_on(img, [(x - w / 2, ybase), (x + w / 2, ybase),
                      (x + w * 0.22, ybase - h), (x - w * 0.22, ybase - h)], color, max(0.0, a))


def _glow(img, x0, y0, x1, y1, color, alpha, layers=3):
    """Cahaya lembut BERBENTUK ELIPS — tanpa kotak (sebelumnya kotak membulat
    dan tampak seperti 'ponsel' di layar tegak)."""
    if alpha <= 0.01:
        return
    w_, h_ = (x1 - x0), (y1 - y0)
    for k in range(layers):
        g = (k + 1) / max(1.0, float(layers))
        px, py = w_ * (0.12 + 0.22 * g), h_ * (0.12 + 0.22 * g)
        ell(img, x0 - px, y0 - py, x1 + px, y1 + py, fill=mix(color, WHITE, 0.12),
            alpha=alpha * 0.30 * (1 - 0.20 * k))


def sc_intro_aurora(img, d, sc, tl, dur, tg, accent, al, dy):
    """Pembuka: langit malam dengan tirai aurora di atas pegunungan bersalju."""
    y = 450
    for i, l in enumerate(sc["lines"]):
        fsz = 150
        while fsz > 58 and tw(l, font(FB, fsz)) > 950:
            fsz -= 4
        f = font(FB, fsz)
        q = seg(tl, 0.05 + i * 0.22, 0.55 + i * 0.22)
        if q <= 0:
            continue
        k = eob(q)
        col = accent if i == len(sc["lines"]) - 1 else INK
        paste_c(img, W / 2, y + (1 - k) * 40, l, f, col, q * al, scale=0.9 + 0.1 * k)
        y += 156
    q = seg(tl, 0.85, 1.45)
    if q <= 0:
        return
    al2 = q * al
    k = eio(q)
    x0, yy0, x1, yy1 = 110, 880 + (1 - k) * 50, 970, 1580 + (1 - k) * 50
    rrect_on(img, x0, yy0, x1, yy1, 46, SPACE_BG, al2)
    # bintang
    qq = seg(tl, 1.05, 1.5)
    if qq > 0:
        alk = qq * al2
        for i in range(30):
            sx = x0 + 40 + ((i * 137) % 780)
            sy = yy0 + 30 + ((i * 211) % 480)
            r = 4 + ((i * 53) % 8)
            star4(img, sx, sy, r, mix(WHITE, CREAM, 0.25), alk * (0.5 + 0.5 * math.sin(tg * 2 + i)))
    # tirai aurora
    qq = seg(tl, 1.2, 2.1)
    if qq > 0:
        alk = qq * al2
        _glow(img, x0 + 40, yy0 + 300, x1 - 40, yy0 + 620, AUR_GREEN, alk * 0.5)
        _aurora_rays(img, x0 + 60, x1 - 60, yy0 + 640, 420, AUR_GREEN, alk * 0.85, tg, n=20)
        _aurora_rays(img, x0 + 180, x1 - 140, yy0 + 660, 300, AUR_TEAL, alk * 0.55, tg,
                     n=16, fase=1.7)
        _aurora_rays(img, x0 + 120, x1 - 200, yy0 + 690, 190, AUR_PURPLE, alk * 0.5, tg,
                     n=14, fase=3.1)
        paste_r(img, x0 + 46, yy0 + 250, "tirai cahaya di langit", font(FM, 25),
                mix(AUR_GREEN, WHITE, 0.35), alk)
    # pegunungan bersalju
    qq = seg(tl, 2.0, 2.6)
    if qq > 0:
        alk = qq * al2
        poly_on(img, [(x0 + 10, yy1 - 10), (x0 + 250, yy1 - 330), (x0 + 500, yy1 - 10)],
                mix(INK, BLUE, 0.30), alk)
        poly_on(img, [(x0 + 380, yy1 - 10), (x0 + 640, yy1 - 250), (x0 + 900, yy1 - 10)],
                mix(INK, BLUE, 0.44), alk)
        poly_on(img, [(x0 + 196, yy1 - 268), (x0 + 250, yy1 - 330), (x0 + 306, yy1 - 268)],
                mix(WHITE, CREAM, 0.35), alk * 0.9)
    qq = seg(tl, 2.4, 3.0)
    if qq > 0:
        _pill_c(img, W / 2, 1655, "CAHAYA YANG BUKAN DARI BUMI", font(FS, 30),
                mix(accent, INK, 0.15), qq * al2, dot=True)


def sc_solar_wind(img, d, sc, tl, dur, tg, accent, al, dy):
    """Angin matahari menabrak pelindung magnet Bumi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    # matahari
    qq = seg(tl, 0.45, 1.0)
    if qq > 0:
        alk = qq * al2
        for i in range(10):
            a = i * math.pi / 5 + tg * 0.15
            line_on(img, (170 + 96 * math.cos(a), 800 + 96 * math.sin(a)),
                    (170 + 128 * math.cos(a), 800 + 128 * math.sin(a)), AMBER, 8, alk * 0.8)
        dot_on(img, 170, 800, 74, AMBER, alk)
        paste_r(img, 110, 940, "MATAHARI", font(FB, 30), mix(AMBER, INK, 0.2), alk)
    # bumi + medan magnet
    ex, ey = 830, 1100
    qq = seg(tl, 0.7, 1.3)
    if qq > 0:
        alk = qq * al2
        dot_on(img, ex, ey, 118, mix(BLUE, INK, 0.15), alk)
        dot_on(img, ex - 40, ey - 30, 46, mix(GREEN, INK, 0.25), alk * 0.8)
        dot_on(img, ex + 52, ey + 40, 34, mix(GREEN, INK, 0.25), alk * 0.8)
    qq = seg(tl, 0.95, 1.6)
    if qq > 0:
        alk = qq * al2
        for i, rr in enumerate((190, 250, 315)):
            ell(img, ex - rr * 0.78, ey - rr, ex + rr * 0.78, ey + rr,
                outline=mix(BLUE, WHITE, 0.25), width=4, alpha=alk * (0.75 - i * 0.16))
        paste_c(img, ex, ey - 400, "MEDAN MAGNET BUMI", font(FS, 30), mix(BLUE, INK, 0.2), alk)
    # partikel: sebagian dibelokkan, sebagian ke kutub
    qq = seg(tl, 1.25, 2.1)
    if qq > 0:
        alk = qq * al2
        for i in range(9):
            u = ((tg * 0.32) + i / 9.0) % 1.0
            px = 300 + 470 * u
            py = 830 + 250 * u
            if px < ex - 250:
                dot_on(img, px, py, 11, mix(AMBER, WHITE, 0.35), alk * 0.9)
        for i in range(5):
            u = 0.5 + 0.5 * ((tg * 0.3) + i / 5.0) % 1.0
            bx = ex - 150 + 150 * u
            by = ey - 320 * u + 230 * (1 - u) * 0.4
            dot_on(img, bx, by, 12, mix(AUR_GREEN, WHITE, 0.2), alk * 0.95)
        for i in range(5):
            u = 0.5 + 0.5 * ((tg * 0.3 + 0.5) + i / 5.0) % 1.0
            bx = ex - 150 + 150 * u
            by = ey + 320 * u - 230 * (1 - u) * 0.4
            dot_on(img, bx, by, 12, mix(AUR_GREEN, WHITE, 0.2), alk * 0.95)
        paste_r(img, 260, 1120, "sebagian besar dibelokkan", font(FM, 25), MUTED, alk)
    qq = seg(tl, 1.9, 2.5)
    if qq > 0:
        alk = qq * al2
        paste_c(img, ex, 1512, "PARTIKEL MASUK LEWAT KUTUB", font(FS, 27),
                mix(AUR_GREEN, INK, 0.15), alk)
    qq = seg(tl, 2.3, 2.9)
    if qq > 0:
        alk = qq * al2
        _pill_c(img, W / 2, 1600, "ANGIN MATAHARI + PELINDUNG MAGNET BUMI", font(FS, 29),
                mix(accent, INK, 0.15), alk, dot=True)
        paste_c(img, W / 2, 1690, "Angin matahari bergerak ratusan kilometer per detik",
                font(FM, 25), MUTED, alk)


def sc_collide(img, d, sc, tl, dur, tg, accent, al, dy):
    """Partikel menabrak oksigen & nitrogen, gas bercahaya seperti lampu neon."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    # penggaris ketinggian
    xr, ytop, ybot = 168, 780, 1430
    qq = seg(tl, 0.45, 1.0)
    if qq > 0:
        alk = qq * al2
        line_on(img, (xr, ytop), (xr, ybot), mix(CREAM, INK, 0.35), 6, alk)
        for km in (100, 200, 300, 500):
            yy = ybot - (km / 500.0) * (ybot - ytop)
            line_on(img, (xr - 16, yy), (xr + 16, yy), mix(CREAM, INK, 0.4), 5, alk)
            paste_r(img, xr + 30, yy, f"{km} km", font(FM, 24), MUTED, alk)
    # permukaan bumi
    qq = seg(tl, 0.6, 1.1)
    if qq > 0:
        _ground(img, 1600, 120, mix(INK, BLUE, 0.35), qq * al2, thick=260)
    # garis medan magnet + elektron berputar turun
    qq = seg(tl, 0.8, 1.7)
    if qq > 0:
        alk = qq * al2
        pts = [(620 + 60 * math.sin(u / 9.0 * math.pi), ytop + (ybot - ytop) * u / 9.0)
               for u in range(10)]
        for i in range(len(pts) - 1):
            line_on(img, pts[i], pts[i + 1], mix(BLUE, WHITE, 0.3), 5, alk * 0.85)
        for j in range(3):
            t0 = ((tg * 0.55) + j / 3.0) % 1.0
            for s in range(6):
                u = (t0 + s * 0.03) % 1.0
                bx = 620 + 60 * math.sin(u * math.pi) + 22 * math.cos(u * 22)
                by = ytop + (ybot - ytop - 120) * u
                dot_on(img, bx, by, 10, mix(AUR_GREEN, WHITE, 0.25), alk * (1 - u * 0.6))
    # tiga ledakan cahaya pada ketinggian berbeda
    bursts = [("hijau · oksigen 100-300 km", AUR_GREEN, 300, 0.9, 1180),
              ("merah · oksigen tinggi", AUR_RED, 500, 1.5, 900),
              ("ungu · nitrogen 80-120 km", AUR_PURPLE, 120, 2.1, 1330)]
    for lab, col, km, t0, yy in bursts:
        qq = seg(tl, t0, t0 + 0.6)
        if qq <= 0:
            continue
        alk = qq * al2
        for s in range(6):
            a = s * math.pi / 3 + tg * 0.6
            line_on(img, (790 + 30 * math.cos(a), yy + 30 * math.sin(a)),
                    (790 + 62 * math.cos(a), yy + 62 * math.sin(a)), col, 8, alk * 0.9)
        dot_on(img, 790, yy, 26, col, alk)
        paste_r(img, 640, yy - 62, lab, font(FS, 26), mix(col, INK, 0.2), alk)
    qq = seg(tl, 2.5, 3.1)
    if qq > 0:
        alk = qq * al2
        _pill_c(img, W / 2, 1468, "TABRAKAN MEMBUAT GAS BERCAHAYA", font(FS, 29),
                mix(accent, INK, 0.15), alk, dot=True)
        paste_c(img, W / 2, 1548, "Prosesnya mirip lampu neon, bukan api", font(FM, 25), MUTED, alk)


def sc_colors(img, d, sc, tl, dur, tg, accent, al, dy):
    """Warna aurora ditentukan jenis gas dan ketinggiannya."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    y0km, y500 = 1420.0, 800.0

    def Y(km):
        return y0km - (km / 500.0) * (y0km - y500)

    bands = [("UNGU/BIRU", "nitrogen · 80-120 km", AUR_PURPLE, 80, 120, 0.5),
             ("HIJAU", "oksigen · 100-300 km", AUR_GREEN, 100, 300, 1.1),
             ("MERAH", "oksigen · 300-500 km", AUR_RED, 300, 500, 1.7)]
    for lab, sub, col, km1, km2, t0 in bands:
        qq = seg(tl, t0, t0 + 0.55)
        if qq <= 0:
            continue
        alk = qq * al2
        y1, y2 = Y(km2), Y(km1)
        rrect_on(img, 330, y1, 650, max(y2, y1 + 34), 18, col, alk * 0.9)
        paste_r(img, 100, (y1 + y2) / 2, lab, font(FB, 28), mix(col, INK, 0.25), alk)
        paste_r(img, 690, (y1 + y2) / 2, sub, font(FM, 23), MUTED, alk)
    # sumbu ketinggian
    qq = seg(tl, 2.2, 2.7)
    if qq > 0:
        alk = qq * al2
        line_on(img, (290, Y(0)), (290, Y(500)), mix(CREAM, INK, 0.3), 5, alk)
        for km in (0, 100, 300, 500):
            line_on(img, (276, Y(km)), (304, Y(km)), mix(CREAM, INK, 0.35), 4, alk)
        paste_c(img, 190, Y(500) - 92, "ketinggian", font(FS, 26), mix(INK, BLUE, 0.3), alk)
        paste_c(img, 190, Y(500) - 54, "(kilometer)", font(FM, 23), MUTED, alk)
        for km in (300, 500):
            paste_c(img, 190, Y(km), f"{km} km", font(FM, 23), MUTED, alk)
        paste_c(img, 190, Y(0) + 34, "permukaan", font(FM, 23), MUTED, alk)
    # tirai contoh di kanan (di bawah label, tidak menabrak teks)
    qq = seg(tl, 2.0, 2.9)
    if qq > 0:
        alk = qq * al2
        rrect_on(img, 700, 600, 990, 860, 30, SPACE_BG, alk)
        _aurora_rays(img, 716, 974, 840, 150, AUR_GREEN, alk * 0.9, tg, n=9)
        _aurora_rays(img, 716, 974, 844, 96, AUR_RED, alk * 0.6, tg, n=9, fase=2.0)
        _aurora_rays(img, 716, 974, 846, 62, AUR_PURPLE, alk * 0.7, tg, n=9, fase=3.4)
        paste_c(img, 845, 564, "tirai aurora", font(FM, 24), MUTED, alk)
    qq = seg(tl, 2.6, 3.2)
    if qq > 0:
        _pill_c(img, W / 2, 1600, "WARNA = JENIS GAS + KETINGGIAN", font(FS, 29),
                mix(accent, INK, 0.15), qq * al2, dot=True)


def sc_why_not_indonesia(img, d, sc, tl, dur, tg, accent, al, dy):
    """Cincin aurora di kutub, sementara khatulistiwa terlindungi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    cx, cy, R = 520, 1040, 268
    qq = seg(tl, 0.45, 1.1)
    if qq > 0:
        alk = qq * al2
        dot_on(img, cx, cy, R, mix(SPACE_BG, BLUE, 0.35), alk)
        # garis lintang (efek bola)
        for i, u in enumerate((0.35, 0.62, 0.85)):
            rx = R * math.cos(math.asin(u)) if u < 1 else 0
            ell(img, cx - rx * 1.15, cy - R * u, cx + rx * 1.15, cy - R * u + 26,
                outline=mix(WHITE, BLUE, 0.55), width=3, alpha=alk * 0.35)
            ell(img, cx - rx * 1.15, cy + R * u - 26, cx + rx * 1.15, cy + R * u,
                outline=mix(WHITE, BLUE, 0.55), width=3, alpha=alk * 0.35)
    # cincin aurora di kutub
    for (yy, lab) in ((cy - R * 0.86, "cincin aurora"), (cy + R * 0.86, None)):
        qq = seg(tl, 0.9, 1.5)
        if qq <= 0:
            continue
        alk = qq * al2
        ell(img, cx - R * 0.62, yy - 52, cx + R * 0.62, yy + 52,
            outline=AUR_GREEN, width=9, alpha=alk)
        ell(img, cx - R * 0.40, yy - 32, cx + R * 0.40, yy + 32,
            outline=mix(AUR_GREEN, WHITE, 0.35), width=5, alpha=alk * 0.8)
        if lab:
            paste_r(img, cx + R * 0.66, yy - 20, lab, font(FM, 24), mix(AUR_GREEN, INK, 0.2), alk)
    # indonesia di khatulistiwa
    qq = seg(tl, 1.4, 2.0)
    if qq > 0:
        alk = qq * al2
        dot_on(img, cx, cy, 15, RED, alk)
        line_on(img, (cx, cy - 40), (cx, cy - 96), RED, 6, alk)
        paste_c(img, cx, cy - 128, "INDONESIA", font(FB, 27), RED, alk)
        paste_c(img, cx, cy - 90, "khatulistiwa", font(FM, 22), MUTED, alk)
    # medan magnet hampir sejajar permukaan + partikel dibelokkan
    qq = seg(tl, 1.9, 2.6)
    if qq > 0:
        alk = qq * al2
        for k in range(3):
            yy = cy - 40 + k * 40
            line_on(img, (cx - R - 130, yy), (cx + R + 130, yy + 30), mix(BLUE, WHITE, 0.35),
                    5, alk * 0.8, dash=18)
        for i in range(5):
            u = ((tg * 0.35) + i / 5.0) % 1.0
            px = cx - R - 150 + 120 * u
            py = cy - 30 + 60 * u
            dot_on(img, px, py, 11, mix(AMBER, WHITE, 0.3), alk * 0.9)
        paste_c(img, W / 2, 1430, "medan magnet di ekuator hampir sejajar permukaan",
                font(FM, 25), MUTED, alk)
        paste_c(img, W / 2, 1478, "partikel dibelokkan menjauh, tidak masuk", font(FM, 25),
                MUTED, alk)
    qq = seg(tl, 2.4, 3.0)
    if qq > 0:
        alk = qq * al2
        _pill_c(img, W / 2, 1580, "AURORA HANYA DI LINTANG TINGGI", font(FS, 29),
                mix(accent, INK, 0.15), alk, dot=True)
        paste_c(img, W / 2, 1672, "Badai ekstrem bisa mendorongnya ke sekitar 50 derajat lintang,",
                font(FM, 24), MUTED, alk)
        paste_c(img, W / 2, 1712, "tetapi tidak sampai ke khatulistiwa", font(FM, 24), MUTED, alk)


def sc_watch_tips(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kalau mau melihat aurora: syaratnya + indeks Kp."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    tips = [("CARI LINTANG TINGGI", "Norwegia, Kanada, Selandia Baru", AUR_GREEN, 0),
            ("LANGIT GELAP", "jauh dari kota, hindari bulan penuh", BLUE, 1),
            ("MUSIM GELAP", "September sampai April (belahan utara)", PURPLE, 2)]
    yy = 700
    for judul, sub, col, t0 in tips:
        qq = seg(tl, 0.5 + t0 * 0.28, 0.95 + t0 * 0.28)
        yy2 = yy
        yy += 168
        if qq <= 0:
            continue
        alk = qq * al2
        rrect_on(img, 120, yy2, 960, yy2 + 144, 30, mix(WHITE, col, 0.12), alk,
                 outline=mix(CREAM, col, 0.45), width=3)
        dot_on(img, 182, yy2 + 72, 36, col, alk)
        line_on(img, (158, yy2 + 74), (178, yy2 + 96), WHITE, 9, alk)
        line_on(img, (178, yy2 + 96), (208, yy2 + 48), WHITE, 9, alk)
        paste_r(img, 244, yy2 + 56, judul, font(FB, 30), mix(col, INK, 0.2), alk)
        paste_r(img, 244, yy2 + 104, sub, font(FM, 24), MUTED, alk)
    # indeks Kp
    qq = seg(tl, 1.4, 2.1)
    if qq > 0:
        alk = qq * al2
        paste_r(img, 120, 1220, "INDEKS KP", font(FB, 30), mix(AMBER, INK, 0.2), alk)
        paste_r(img, 380, 1220, "semakin tinggi, aurora makin luas", font(FM, 24), MUTED, alk)
        for i in range(10):
            col = mix(GREEN, AMBER, i / 6.0) if i < 5 else mix(AMBER, RED, (i - 5) / 4.0)
            q3 = seg(tl, 1.6 + i * 0.04, 1.8 + i * 0.04)
            if q3 <= 0:
                continue
            rrect_on(img, 130 + i * 82, 1260, 130 + i * 82 + 74, 1330, 12, col, q3 * al2)
            paste_c(img, 130 + i * 82 + 37, 1300, str(i + 1), font(FM, 22), WHITE, q3 * al2)
        q3 = seg(tl, 2.05, 2.4)
        if q3 > 0:
            line_on(img, (130 + 5 * 82 - 4, 1240), (130 + 5 * 82 - 4, 1350), INK, 6, q3 * al2)
            paste_c(img, 130 + 5 * 82 - 4, 1388, "Kp 5 = badai geomagnetik", font(FS, 25),
                    INK, q3 * al2)
    qq = seg(tl, 2.3, 2.9)
    if qq > 0:
        alk = qq * al2
        _pill_c(img, W / 2, 1500, "SEKARANG PUNCAK SIKLUS MATAHARI KE-25", font(FS, 28),
                mix(accent, INK, 0.15), alk, dot=True)
        paste_c(img, W / 2, 1590, "Jadi aurora lebih sering muncul dan lebih terang",
                font(FM, 25), MUTED, alk)
        paste_c(img, W / 2, 1650, "Kamera HP sering menangkap warna lebih jelas daripada mata",
                font(FM, 25), MUTED, alk)


# ---------- Ep15: Perang Dingin — perang yang tak pernah ditembakkan ----------
WEST = (47, 111, 181)          # blok barat / Amerika Serikat
EAST = (192, 57, 43)           # blok timur / Uni Soviet
ICE = mix(BLUE, WHITE, 0.72)
FROST = mix(BLUE, WHITE, 0.88)
STEEL = (96, 104, 120)


def _frost(img, x0, x1, y, color, alpha, tg=0.0, n=16, amp=26, width=6):
    """Garis retak beku: gelombang tajam sebagai pemisah dua pihak."""
    if alpha <= 0.01:
        return
    pts = [(x0 + (x1 - x0) * i / n,
            y + amp * math.sin(i * 2.3 + tg * 0.7) * (0.4 + 0.6 * math.sin(i * 0.7))) for i in range(n + 1)]
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], color, width, alpha)


def _trail(img, pts, color, alpha, width=10, tail=8):
    """Jejak gerak (motion trail): garis yang memudar di belakang posisi terakhir."""
    if alpha <= 0.01 or len(pts) < 2:
        return
    n = min(tail, len(pts) - 1)
    for k in range(n):
        a = alpha * (1.0 - k / float(n)) ** 1.5
        pw = max(1, int(width * (1.0 - k / float(n))))
        line_on(img, pts[-2 - k], pts[-1 - k], color, pw, a)


def _frost_v(img, x, y0, y1, color, alpha, tg=0.0, n=12, amp=20, width=6):
    """Retakan beku vertikal (pemisah dua blok)."""
    if alpha <= 0.01:
        return
    pts = [(x + amp * math.sin(i * 2.1 + tg * 0.7) * (0.4 + 0.6 * math.sin(i * 0.9)),
            y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], color, width, alpha)


def _arrow_on(img, p1, p2, color, width, alpha=1.0, dash=None, head=26):
    """Garis dengan mata panah di ujung p2."""
    if alpha <= 0.01:
        return
    x0, y0 = p1
    x1, y1 = p2
    dx, dyy = x1 - x0, y1 - y0
    L = math.hypot(dx, dyy) or 1.0
    ux, uy = dx / L, dyy / L
    ex, ey = x1 - ux * head, y1 - uy * head
    line_on(img, (x0, y0), (ex, ey), color, width, alpha, dash)
    px_, py_ = -uy, ux
    poly_on(img, [(x1, y1), (ex + px_ * head * 0.5, ey + py_ * head * 0.5),
                  (ex - px_ * head * 0.5, ey - py_ * head * 0.5)], color, alpha)


def _bomb_icon(img, cx, cy, s, color, alpha, tg=0.0):
    """Rudal sederhana: badan, hidung, sirip, dan nyala api kecil."""
    if alpha <= 0.01:
        return
    rrect_on(img, cx - s * 0.17, cy - s * 0.95, cx + s * 0.17, cy + s * 0.55,
             int(max(6, s * 0.17)), color, alpha)
    poly_on(img, [(cx, cy - s * 1.32), (cx - s * 0.17, cy - s * 0.92),
                  (cx + s * 0.17, cy - s * 0.92)], color, alpha)
    poly_on(img, [(cx - s * 0.17, cy + s * 0.18), (cx - s * 0.52, cy + s * 0.62),
                  (cx - s * 0.17, cy + s * 0.55)], color, alpha)
    poly_on(img, [(cx + s * 0.17, cy + s * 0.18), (cx + s * 0.52, cy + s * 0.62),
                  (cx + s * 0.17, cy + s * 0.55)], color, alpha)
    fl = s * 0.46 * (0.75 + 0.25 * math.sin(tg * 7.0))
    poly_on(img, [(cx - s * 0.11, cy + s * 0.58), (cx + s * 0.11, cy + s * 0.58),
                  (cx, cy + s * 0.58 + fl)], mix(AMBER, WHITE, 0.25), alpha * 0.9)


def _globe_split(img, cx, cy, r, colw, cole, alpha, dash=18):
    """Bumi terbelah dua warna: barat dan timur."""
    if alpha <= 0.01:
        return
    dot_on(img, cx, cy, r, ICE, alpha)
    lw = [(cx, cy - r)] + [(cx + r * math.cos(-math.pi / 2 - math.pi * i / 24.0),
                            cy + r * math.sin(-math.pi / 2 - math.pi * i / 24.0)) for i in range(25)]
    rw = [(cx, cy - r)] + [(cx + r * math.cos(-math.pi / 2 + math.pi * i / 24.0),
                            cy + r * math.sin(-math.pi / 2 + math.pi * i / 24.0)) for i in range(25)]
    for pts, col in ((lw, colw), (rw, cole)):
        for k in range(len(pts) - 1):
            poly_on(img, [(cx, cy), pts[k], pts[k + 1]], col, alpha * 0.9)
    line_on(img, (cx, cy - r), (cx, cy + r), mix(CREAM, INK, 0.4), 5, alpha, dash=dash)
    ring_on(img, cx, cy, r, mix(CREAM, INK, 0.3), 4, alpha)


def _wall(img, x0, y0, x1, y1, color, alpha, collapse=0.0):
    """Tembok bata; collapse 0..1 membuat sebagian bata berjatuhan."""
    if alpha <= 0.01:
        return
    bh, bw = 34, 68
    rows = max(1, int((y1 - y0) // bh))
    for rr in range(rows):
        yy = y0 + rr * bh
        off = 0 if rr % 2 == 0 else bw // 2
        x = x0 - off
        while x < x1:
            xa, xb = max(x0, x + 3), min(x1, x + bw - 3)
            if xb > xa:
                dxx = dyy = 0.0
                if collapse > 0:
                    krow = rr / max(1.0, rows - 1.0)
                    if krow < collapse:
                        k2 = ((int((x - x0) // bw) * 13) % 7) / 7.0
                        dxx = (k2 - 0.45) * 120 * collapse
                        dyy = min(150.0, 120 * collapse * (1.0 + krow) + 40 * k2)
                rrect_on(img, xa + dxx, yy + 3 + dyy, xb + dxx, yy + bh - 3 + dyy, 7,
                         color, alpha)
            x += bw


def sc_intro_cold(img, d, sc, tl, dur, tg, accent, al, dy):
    """Pembuka: dua blok raksasa berhadapan, dipisah garis beku."""
    y = 420
    for i, l in enumerate(sc["lines"]):
        fsz = 132
        while fsz > 54 and tw(l, font(FB, fsz)) > 940:
            fsz -= 4
        q = seg(tl, 0.05 + i * 0.22, 0.55 + i * 0.22)
        if q <= 0:
            continue
        k = eob(q)
        col = accent if i == len(sc["lines"]) - 1 else INK
        paste_c(img, W / 2, y + (1 - k) * 40, l, font(FB, fsz), col, q * al, scale=0.9 + 0.1 * k)
        y += 148
    q = seg(tl, 0.85, 1.45)
    if q <= 0:
        return
    alk = q * al
    k = eio(q)
    ytop = 900 + (1 - k) * 60
    rrect_on(img, 120, ytop, 470, ytop + 560, 40, WEST, alk * 0.92)
    rrect_on(img, 610, ytop, 960, ytop + 560, 40, EAST, alk * 0.92)
    _frost_v(img, 540, ytop + 30, ytop + 530, mix(CREAM, INK, 0.5), alk * 0.9, tg,
             n=14, amp=22, width=7)
    qq = seg(tl, 1.05, 1.6)
    if qq <= 0:
        return
    al2 = qq * al
    paste_c(img, 295, ytop + 620, "AMERIKA", font(FB, 32), mix(WEST, INK, 0.2), al2)
    paste_c(img, 785, ytop + 620, "UNI SOVIET", font(FB, 32), mix(EAST, INK, 0.2), al2)
    paste_c(img, 295, ytop + 668, "1947", font(FM, 26), MUTED, al2)
    paste_c(img, 785, ytop + 668, "1991", font(FM, 26), MUTED, al2)
    qq = seg(tl, 1.7, 2.3)
    if qq > 0:
        _pill_c(img, W / 2, 1700, "44 TAHUN TEGANG, TANPA PERANG LANGSUNG", font(FS, 28),
                mix(accent, INK, 0.15), qq * al, dot=True)


def sc_two_giants(img, d, sc, tl, dur, tg, accent, al, dy):
    """Dunia terbelah: dua negara adidaya dan dua sekutu militernya."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    kartu = [("AMERIKA SERIKAT", "kapitalis", WEST, 110, 0.0),
             ("UNI SOVIET", "komunis", EAST, 570, 0.25)]
    for judul, sub, col, x0, t0 in kartu:
        qq = seg(tl, 0.45 + t0, 1.0 + t0)
        if qq <= 0:
            continue
        alk = qq * al2
        rrect_on(img, x0, 640, x0 + 400, 840, 34, mix(WHITE, col, 0.14), alk,
                 outline=mix(CREAM, col, 0.5), width=3)
        dot_on(img, x0 + 52, 700, 22, col, alk)
        paste_r(img, x0 + 96, 700, judul, font(FB, 30), mix(col, INK, 0.25), alk)
        paste_r(img, x0 + 52, 772, sub, font(FM, 26), MUTED, alk)
    qq = seg(tl, 1.1, 2.0)
    if qq > 0:
        alk = qq * al2
        _globe_split(img, W / 2, 1160, 250, WEST, EAST, alk * 0.9)
        paste_c(img, 415, 1160, "NATO", font(FB, 30), WHITE, alk)
        paste_c(img, 665, 1160, "PAKTA WARSAWA", font(FB, 28), WHITE, alk)
    qq = seg(tl, 2.0, 2.6)
    if qq > 0:
        _pill_c(img, W / 2, 1540, "DUNIA TERBELAH DUA", font(FS, 30),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1630, "NATO berdiri 1949 · Pakta Warsawa 1955", font(FM, 25),
                MUTED, qq * al)


def sc_mad(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kenapa tidak saling menembak: menyerang berarti hancur bersama."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    for col, cx, t0 in ((WEST, 250, 0.0), (EAST, 830, 0.3)):
        qq = seg(tl, 0.45 + t0, 1.0 + t0)
        if qq <= 0:
            continue
        _glow(img, cx - 90, 1000, cx + 90, 1300, col, qq * al2 * 0.35)
        _bomb_icon(img, cx, 1090, 150, col, qq * al2, tg)
    qq = seg(tl, 1.05, 1.9)
    if qq > 0:
        alk = qq * al2
        _arrow_on(img, (340, 1010), (720, 940), mix(WEST, INK, 0.1), 7, alk, dash=16)
        _arrow_on(img, (740, 1180), (360, 1110), mix(EAST, INK, 0.1), 7, alk, dash=16)
    qq = seg(tl, 1.5, 2.2)
    if qq > 0:
        alk = qq * al2
        _glow(img, 470, 780, 610, 920, AMBER, alk * 0.5)
        star4(img, 540, 850, 130, AMBER, alk * 0.95)
        star4(img, 540, 850, 66, mix(AMBER, WHITE, 0.4), alk)
    qq = seg(tl, 1.9, 2.4)
    if qq > 0:
        alk = qq * al2
        paste_c(img, 250, 1330, "AMERIKA", font(FB, 28), mix(WEST, INK, 0.2), alk)
        paste_c(img, 830, 1330, "UNI SOVIET", font(FB, 28), mix(EAST, INK, 0.2), alk)
        paste_c(img, W / 2, 1010, "dua-duanya hancur", font(FB, 30), mix(AMBER, INK, 0.25), alk)
    qq = seg(tl, 2.3, 2.9)
    if qq > 0:
        _pill_c(img, W / 2, 1470, "MENYERANG = BUNUH DIRI BERSAMA", font(FS, 28),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1560, "Karena itu tidak ada yang berani memulai", font(FM, 25),
                MUTED, qq * al)


def sc_proxy(img, d, sc, tl, dur, tg, accent, al, dy):
    """Perang proksi: bertarung lewat negara lain."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    perang = [("KOREA", "1950-1953", 0.0), ("VIETNAM", "1955-1975", 0.3),
              ("AFGHANISTAN", "1979-1989", 0.6)]
    yy = 640
    for nama, tahun, t0 in perang:
        qq = seg(tl, 0.5 + t0, 1.0 + t0)
        yy2 = yy
        yy += 240
        if qq <= 0:
            continue
        alk = qq * al2
        rrect_on(img, 110, yy2, 970, yy2 + 196, 32, mix(WHITE, ICE, 0.5), alk,
                 outline=mix(CREAM, BLUE, 0.35), width=3)
        paste_r(img, 160, yy2 + 70, nama, font(FB, 38), mix(INK, BLUE, 0.15), alk)
        paste_r(img, 160, yy2 + 128, tahun, font(FM, 26), MUTED, alk)
        _arrow_on(img, (640, yy2 + 62), (900, yy2 + 62), WEST, 7, alk)
        _arrow_on(img, (900, yy2 + 142), (640, yy2 + 142), EAST, 7, alk)
        paste_c(img, 760, yy2 + 24, "senjata & dana", font(FM, 22), MUTED, alk)
    qq = seg(tl, 2.2, 2.8)
    if qq > 0:
        _pill_c(img, W / 2, 1470, "DUA RAKSASA TIDAK MENGIRIM TENTARANYA", font(FS, 27),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1560, "Mereka mendukung pihak yang berlawanan di negara lain",
                font(FM, 25), MUTED, qq * al)


def sc_cuba(img, d, sc, tl, dur, tg, accent, al, dy):
    """Krisis rudal Kuba 1962: 13 hari dunia menahan napas."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    qq = seg(tl, 0.45, 1.1)
    if qq > 0:
        alk = qq * al2
        ell(img, 130, 660, 520, 860, fill=mix(WHITE, ICE, 0.35), outline=mix(CREAM, BLUE, 0.4),
            width=4, alpha=alk)
        paste_c(img, 325, 760, "AMERIKA", font(FB, 28), mix(INK, BLUE, 0.2), alk)
        ell(img, 470, 1080, 780, 1240, fill=mix(WHITE, RED, 0.18), outline=mix(CREAM, RED, 0.4),
            width=4, alpha=alk)
        paste_c(img, 625, 1160, "KUBA", font(FB, 28), mix(EAST, INK, 0.2), alk)
        line_on(img, (350, 880), (505, 985), mix(CREAM, INK, 0.45), 5, alk, dash=14)
        paste_c(img, 300, 902, "90 mil", font(FM, 24), MUTED, alk)
    qq = seg(tl, 1.0, 1.6)
    if qq > 0:
        alk = qq * al2
        _bomb_icon(img, 570, 1030, 78, EAST, alk, tg)
        _bomb_icon(img, 690, 1030, 78, EAST, alk, tg)
    qq = seg(tl, 1.5, 2.1)
    if qq > 0:
        alk = qq * al2
        paste_c(img, 820, 700, "13 hari", font(FB, 58), mix(accent, INK, 0.15), alk)
        paste_c(img, 820, 776, "dunia menahan napas", font(FM, 25), MUTED, alk)
        paste_c(img, 820, 828, "rudal akhirnya ditarik", font(FM, 25), MUTED, alk)
    qq = seg(tl, 2.2, 2.8)
    if qq > 0:
        _pill_c(img, W / 2, 1440, "1962: DUNIA DI AMBANG PERANG NUKLIR", font(FS, 27),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1530, "Setelah itu dibuat saluran telepon langsung", font(FM, 25),
                MUTED, qq * al)
        paste_c(img, W / 2, 1584, "antara Washington dan Moskow", font(FM, 25), MUTED, qq * al)


def sc_end_cold(img, d, sc, tl, dur, tg, accent, al, dy):
    """Akhir Perang Dingin: tembok tumbang, Uni Soviet bubar."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    qq = seg(tl, 0.45, 1.5)
    if qq > 0:
        _wall(img, 200, 600, 880, 880, mix(STEEL, WHITE, 0.42), qq * al2,
              collapse=clamp((tl - 0.7) / 1.2))
    qq = seg(tl, 1.3, 1.9)
    if qq > 0:
        alk = qq * al2
        line_on(img, (150, 1190), (930, 1190), mix(CREAM, INK, 0.35), 8, alk)
        titik = [(150, "1947"), (400, "1962"), (690, "1989"), (870, "1991")]
        for x, tahun in titik:
            dot_on(img, x, 1190, 16, mix(INK, BLUE, 0.2), alk)
            paste_c(img, x, 1110, tahun, font(FB, 28), mix(INK, BLUE, 0.2), alk)
        paste_c(img, 275, 1250, "mulai", font(FM, 23), MUTED, alk)
        paste_c(img, 400, 1250, "Kuba", font(FM, 23), MUTED, alk)
        paste_c(img, 690, 1250, "Tembok Berlin", font(FM, 23), MUTED, alk)
        paste_c(img, 890, 1250, "Soviet bubar", font(FM, 23), MUTED, alk)
    qq = seg(tl, 2.0, 2.6)
    if qq > 0:
        _pill_c(img, W / 2, 1440, "BERAKHIR TANPA PERANG LANGSUNG", font(FS, 28),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1530, "44 tahun tegang — dua raksasa itu tidak pernah saling menembak",
                font(FM, 24), MUTED, qq * al)


# ---------- Ep16: AI — kenapa bisa pintar? ----------
NEURAL = PURPLE                     # jaringan saraf / AI
DATA = BLUE                         # data & contoh
LILAC = mix(PURPLE, WHITE, 0.72)
MINT = mix(GREEN, WHITE, 0.72)


def _net(img, cx, cy, s, color, alpha, tg=0.0, ncol=4, nrow=4):
    """Jaringan saraf sederhana: beberapa lapis titik yang saling terhubung."""
    if alpha <= 0.01:
        return
    dx = s * 0.62
    dy = s * 0.52
    for c in range(ncol - 1):
        for i in range(nrow):
            for j in range(nrow):
                a = alpha * (0.16 + 0.20 * math.sin(tg * 1.6 + c * 1.3 + i * 0.7 + j * 0.5))
                line_on(img, (cx + (c - (ncol - 1) / 2.0) * dx, cy + (i - (nrow - 1) / 2.0) * dy),
                        (cx + (c + 1 - (ncol - 1) / 2.0) * dx, cy + (j - (nrow - 1) / 2.0) * dy),
                        color, 3, max(0.0, a))
    for c in range(ncol):
        for i in range(nrow):
            r = 13 + 3 * math.sin(tg * 2.2 + c * 0.9 + i * 0.6)
            dot_on(img, cx + (c - (ncol - 1) / 2.0) * dx, cy + (i - (nrow - 1) / 2.0) * dy,
                   r, mix(color, WHITE, 0.18), alpha)


def _tiles(img, x0, y0, cols, rows, size, gap, alpha, tg=0.0, base=DATA):
    """Kumpulan kotak kecil = contoh data yang dipelajari AI."""
    if alpha <= 0.01:
        return
    for r_ in range(rows):
        for c in range(cols):
            k = (r_ * cols + c)
            a = alpha * (0.55 + 0.45 * math.sin(tg * 1.4 + k * 0.8))
            col = mix(base, WHITE, 0.35 + 0.35 * (k % 4) / 3.0)
            xa = x0 + c * (size + gap)
            ya = y0 + r_ * (size + gap)
            rrect_on(img, xa, ya, xa + size, ya + size, 10, col, max(0.0, a))


def _loop3(img, cx, cy, r, color, alpha, tg=0.0, width=9):
    """Lingkaran tiga tahap (tebak -> bandingkan -> setel ulang)."""
    if alpha <= 0.01:
        return
    for k in range(3):
        a0 = -math.pi / 2 + k * 2 * math.pi / 3 + tg * 0.5
        pts = []
        for i in range(19):
            a = a0 + (i / 18.0) * (2 * math.pi / 3 - 0.35)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        for i in range(len(pts) - 1):
            line_on(img, pts[i], pts[i + 1], color, width, alpha * 0.9)
        ex, ey = pts[-1]
        px_, py_ = -(pts[-1][1] - pts[-2][1]), (pts[-1][0] - pts[-2][0])
        L = math.hypot(px_, py_) or 1.0
        px_, py_ = px_ / L * 22, py_ / L * 22
        poly_on(img, [(ex + px_ * 0.7, ey + py_ * 0.7), (ex - py_ * 0.55, ey + px_ * 0.55),
                      (ex + py_ * 0.55, ey - px_ * 0.55)], color, alpha)


def _knobs(img, cx, cy, n, alpha, tg=0.0, color=NEURAL):
    """Deretan pengatur (bobot) yang sedang disetel ulang."""
    if alpha <= 0.01:
        return
    w = 300
    for i in range(n):
        x = cx - w / 2 + (w / (n - 1.0)) * i
        line_on(img, (x, cy - 54), (x, cy + 54), mix(PURPLE, WHITE, 0.55), 8, alpha * 0.8)
        yy = cy + 22 * math.sin(tg * 1.8 + i * 1.1)
        dot_on(img, x, yy, 15, color, alpha)


def _pbar(img, x0, y, w, h, frac, alpha, color=NEURAL, track=None):
    """Batang probabilitas (0..1)."""
    if alpha <= 0.01:
        return
    track = track or mix(PURPLE, WHITE, 0.82)
    rrect_on(img, x0, y, x0 + w, y + h, h // 2, track, alpha)
    rrect_on(img, x0, y, x0 + max(h, w * frac), y + h, h // 2, color, alpha)


def _gpu(img, x0, y0, w, h, alpha, tg=0.0):
    """Rak komputer latihan: kotak-kotak dengan lampu berkedip."""
    if alpha <= 0.01:
        return
    rrect_on(img, x0, y0, x0 + w, y0 + h, 22, mix(INK, BLUE, 0.35), alpha)
    for i in range(4):
        for j in range(3):
            xa = x0 + 20 + i * (w - 40) / 4.0
            ya = y0 + 18 + j * (h - 36) / 3.0
            rrect_on(img, xa, ya, xa + (w - 40) / 4.0 - 12, ya + (h - 36) / 3.0 - 10, 8,
                     mix(BLUE, WHITE, 0.5), alpha * 0.85)
            dot_on(img, xa + 12, ya + 12, 5 + 2 * math.sin(tg * 5 + i + j),
                   mix(GREEN, WHITE, 0.3), alpha * (0.5 + 0.5 * math.sin(tg * 3.4 + i * 2 + j)))


def sc_intro_ai(img, d, sc, tl, dur, tg, accent, al, dy):
    """Pembuka: jaringan saraf menyala di bawah judul + balon percakapan."""
    y = 430
    for i, l in enumerate(sc["lines"]):
        fsz = 138
        while fsz > 54 and tw(l, font(FB, fsz)) > 940:
            fsz -= 4
        q = seg(tl, 0.05 + i * 0.22, 0.55 + i * 0.22)
        if q <= 0:
            continue
        k = eob(q)
        col = accent if i == len(sc["lines"]) - 1 else INK
        paste_c(img, W / 2, y + (1 - k) * 40, l, font(FB, fsz), col, q * al, scale=0.9 + 0.1 * k)
        y += 154
    q = seg(tl, 0.85, 1.45)
    if q <= 0:
        return
    alk = q * al
    k = eio(q)
    _bubble(img, 380, 1080 + (1 - k) * 40, 480, 300, mix(WHITE, LILAC, 0.55), alk)
    paste_c(img, 380, 1030 + (1 - k) * 40, "?", font(FB, 96), NEURAL, alk)
    paste_r(img, 190, 1130 + (1 - k) * 40, "sebenarnya apa", font(FM, 30), MUTED, alk)
    paste_r(img, 190, 1180 + (1 - k) * 40, "yang terjadi?", font(FM, 30), MUTED, alk)
    qq = seg(tl, 1.15, 1.9)
    if qq > 0:
        _net(img, 740, 1120, 150, NEURAL, qq * al * 0.95, tg)
    qq = seg(tl, 1.8, 2.4)
    if qq > 0:
        _pill_c(img, W / 2, 1560, "BUKAN SIHIR, TAPI POLA", font(FS, 30),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1650, "Jaringan saraf tiruan: banyak angka yang saling terhubung",
                font(FM, 25), MUTED, qq * al)


def sc_examples(img, d, sc, tl, dur, tg, accent, al, dy):
    """AI diajari contoh, bukan diberi aturan."""

    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    # kiri: aturan (dicoret)
    qq = seg(tl, 0.5, 1.1)
    if qq > 0:
        alk = qq * al2
        rrect_on(img, 100, 640, 470, 1180, 34, mix(WHITE, AMBER, 0.12), alk,
                 outline=mix(CREAM, AMBER, 0.4), width=3)
        paste_r(img, 150, 720, "ATURAN", font(FB, 32), mix(AMBER, INK, 0.25), alk)
        paste_r(img, 150, 790, "kalau ada kumis", font(FM, 26), MUTED, alk)
        paste_r(img, 150, 840, "dan telinga lancip", font(FM, 26), MUTED, alk)
        paste_r(img, 150, 890, "berarti kucing", font(FM, 26), MUTED, alk)
        q3 = seg(tl, 1.05, 1.5)
        if q3 > 0:
            a3 = q3 * al2
            line_on(img, (150, 790), (430, 900), mix(RED, INK, 0.1), 7, a3)
            line_on(img, (430, 790), (150, 900), mix(RED, INK, 0.1), 7, a3)
            paste_r(img, 150, 970, "terlalu banyak", font(FM, 25), mix(RED, INK, 0.15), a3)
            paste_r(img, 150, 1018, "kemungkinan", font(FM, 25), mix(RED, INK, 0.15), a3)
    # kanan: contoh
    qq = seg(tl, 0.9, 1.5)
    if qq > 0:
        alk = qq * al2
        rrect_on(img, 540, 640, 980, 1180, 34, mix(WHITE, MINT, 0.35), alk,
                 outline=mix(CREAM, GREEN, 0.4), width=3)
        paste_r(img, 590, 720, "JUTAAN CONTOH", font(FB, 30), mix(GREEN, INK, 0.25), alk)
        _tiles(img, 600, 780, 4, 3, 82, 14, alk, tg)
        q3 = seg(tl, 1.5, 1.9)
        if q3 > 0:
            dot_on(img, 620, 1120, 26, mix(GREEN, INK, 0.1), q3 * al2)
            line_on(img, (604, 1122), (618, 1140), WHITE, 7, q3 * al2)
            line_on(img, (618, 1140), (642, 1102), WHITE, 7, q3 * al2)
            paste_r(img, 664, 1120, "ia cari polanya sendiri", font(FM, 25), MUTED, q3 * al2)
    qq = seg(tl, 2.1, 2.7)
    if qq > 0:
        _pill_c(img, W / 2, 1380, "DIAJARI CONTOH, BUKAN ATURAN", font(FS, 30),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1470, "Semakin banyak contoh, semakin banyak pola yang ia kuasai",
                font(FM, 25), MUTED, qq * al)


def sc_training(img, d, sc, tl, dur, tg, accent, al, dy):
    """Cara belajar: tebak, bandingkan, setel ulang — berulang."""

    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    qq = seg(tl, 0.5, 1.4)
    if qq > 0:
        _loop3(img, W / 2, 1080, 210, mix(NEURAL, WHITE, 0.25), qq * al2, tg)
    langkah = [("1. TEBAK", 540, 748, 0.8), ("2. BANDINGKAN", 890, 1080, 1.0),
               ("3. SETEL ULANG", 190, 1080, 1.2)]
    for teks, x, y, t0 in langkah:
        qq = seg(tl, t0, t0 + 0.5)
        if qq <= 0:
            continue
        _pill_c(img, x, y, teks, font(FS, 24), mix(NEURAL, INK, 0.2), qq * al, dot=True)
    qq = seg(tl, 1.5, 2.2)
    if qq > 0:
        _knobs(img, W / 2, 1080, 6, qq * al2, tg)
        paste_c(img, W / 2, 1218, "angka pengaturan", font(FM, 25), MUTED, qq * al)
    qq = seg(tl, 2.2, 2.8)
    if qq > 0:
        paste_c(img, W / 2, 1470, "Diulang miliaran kali sampai tebakannya makin akurat",
                font(FM, 25), MUTED, qq * al)
        _pill_c(img, W / 2, 1560, "ITULAH PROSES BELAJAR AI", font(FS, 30),
                mix(accent, INK, 0.15), qq * al, dot=True)


def sc_predict(img, d, sc, tl, dur, tg, accent, al, dy):
    """Setelah latihan: menebak lanjutan kalimat dari peluang."""

    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    qq = seg(tl, 0.5, 1.2)
    if qq > 0:
        alk = qq * al2
        _pill_c(img, 280, 700, "SELAMAT", font(FS, 30), mix(DATA, INK, 0.25), alk)
        _pill_c(img, 470, 700, "PAGI", font(FS, 30), mix(DATA, INK, 0.25), alk)
        _pill_c(img, 700, 700, "?", font(FS, 30), mix(MUTED, WHITE, 0.2), alk)
    kandidat = [("SEMUA", 0.62, GREEN, 1.1), ("SAYANG", 0.21, AMBER, 1.3),
                ("DUNIA", 0.09, MUTED, 1.5)]
    baris = 860
    for teks, frac, col, t0 in kandidat:
        qq = seg(tl, t0, t0 + 0.45)
        yy = baris
        baris += 104
        if qq <= 0:
            continue
        alk = qq * al2
        paste_r(img, 150, yy, teks, font(FB, 28), mix(col, INK, 0.25), alk)
        _pbar(img, 420, yy - 18, 480, 36, frac, alk, color=col)
        paste_r(img, 872, yy, f"{int(frac * 100)}%", font(FB, 28), mix(col, INK, 0.25), alk)
    qq = seg(tl, 1.9, 2.5)
    if qq > 0:
        alk = qq * al2
        star4(img, 998, 860, 32, GREEN, alk * 0.9)
        paste_c(img, W / 2, 1180, "ia memilih yang paling mungkin, bukan yang paling benar",
                font(FM, 26), MUTED, alk)
        _pill_c(img, W / 2, 1290, "KARENA ITU AI BISA SALAH DENGAN YAKIN", font(FS, 28),
                mix(accent, INK, 0.15), alk, dot=True)
    qq = seg(tl, 2.6, 3.1)
    if qq > 0:
        paste_c(img, W / 2, 1390, "Tidak ada kamus fakta di dalamnya — hanya pola dari latihan",
                font(FM, 25), MUTED, qq * al)


def sc_scale(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kenapa terasa pintar: skala angka, komputer latihan, dan batasnya."""

    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    qq = seg(tl, 0.5, 1.2)
    if qq > 0:
        alk = qq * al2
        rrect_on(img, 100, 620, 980, 900, 34, mix(WHITE, LILAC, 0.45), alk,
                 outline=mix(CREAM, PURPLE, 0.4), width=3)
        paste_r(img, 160, 700, "Model besar: ratusan miliar angka pengaturan", font(FB, 30),
                mix(NEURAL, INK, 0.25), alk)
        paste_r(img, 160, 780, "Contoh nyata: GPT-3 punya 175 miliar parameter dan dilatih", font(FM, 25),
                MUTED, alk)
        paste_r(img, 160, 828, "dengan puluhan terabita teks dari internet dan buku", font(FM, 25),
                MUTED, alk)
    qq = seg(tl, 1.0, 1.7)
    if qq > 0:
        _gpu(img, 140, 960, 800, 210, qq * al2, tg)
        paste_c(img, 540, 1220, "Latihan butuh berhari-hari di banyak komputer khusus",
                font(FM, 25), MUTED, qq * al)
    qq = seg(tl, 1.7, 2.4)
    if qq > 0:
        alk = qq * al2
        rrect_on(img, 100, 1300, 500, 1560, 30, mix(WHITE, MINT, 0.5), alk,
                 outline=mix(CREAM, GREEN, 0.4), width=3)
        rrect_on(img, 560, 1300, 980, 1560, 30, mix(WHITE, DATA, 0.14), alk,
                 outline=mix(CREAM, DATA, 0.45), width=3)
        paste_c(img, 300, 1360, "AI", font(FB, 30), mix(GREEN, INK, 0.25), alk)
        paste_c(img, 770, 1360, "MANUSIA", font(FB, 30), mix(DATA, INK, 0.2), alk)
        paste_c(img, 300, 1430, "pola dari jutaan contoh", font(FM, 24), MUTED, alk)
        paste_c(img, 300, 1478, "cepat, tetapi tidak mengerti", font(FM, 24), MUTED, alk)
        paste_c(img, 770, 1430, "pengalaman & mengerti", font(FM, 24), MUTED, alk)
        paste_c(img, 770, 1478, "lambat, tetapi menalar", font(FM, 24), MUTED, alk)
    qq = seg(tl, 2.4, 2.9)
    if qq > 0:
        _pill_c(img, W / 2, 1680, "AI PINTAR POLA, BUKAN PINTAR HIKMAH", font(FS, 28),
                mix(accent, INK, 0.15), qq * al, dot=True)


def sc_use_safe(img, d, sc, tl, dur, tg, accent, al, dy):
    """Cara memakai AI dengan bijak."""

    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    tips = [("PERIKSA FAKTA & ANGKA", "AI bisa salah dengan yakin", GREEN, 0),
            ("JANGAN KIRIM DATA PRIBADI", "kata sandi, KTP, nomor rekening", AMBER, 1),
            ("PAKAI UNTUK IDE", "keputusan tetap milikmu", NEURAL, 2)]
    yy = 700
    for judul, sub, col, t0 in tips:
        qq = seg(tl, 0.5 + t0 * 0.28, 0.95 + t0 * 0.28)
        yy2 = yy
        yy += 200
        if qq <= 0:
            continue
        alk = qq * al2
        rrect_on(img, 110, yy2, 970, yy2 + 168, 32, mix(WHITE, col, 0.12), alk,
                 outline=mix(CREAM, col, 0.45), width=3)
        dot_on(img, 180, yy2 + 84, 38, col, alk)
        line_on(img, (156, yy2 + 86), (176, yy2 + 110), WHITE, 9, alk)
        line_on(img, (176, yy2 + 110), (208, yy2 + 58), WHITE, 9, alk)
        paste_r(img, 250, yy2 + 66, judul, font(FB, 30), mix(col, INK, 0.2), alk)
        paste_r(img, 250, yy2 + 118, sub, font(FM, 24), MUTED, alk)
    qq = seg(tl, 1.6, 2.2)
    if qq > 0:
        _pill_c(img, W / 2, 1500, "AI ALAT, BUKAN SUMBER KEBENARAN", font(FS, 30),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1590, "Yang memutuskan tetap manusia", font(FM, 25), MUTED, qq * al)


# ---------- Ep17: Segitiga Bermuda — misteri atau salah paham? ----------
OCEAN = (38, 78, 128)            # laut dalam
OCEAN_L = mix(BLUE, WHITE, 0.62)
OCEAN_P = mix(BLUE, WHITE, 0.82)
TRI = (224, 138, 44)             # garis segitiga
HULL = (48, 58, 78)              # badan kapal/pesawat


def _sea(img, y0, y1, alpha, tg=0.0, color=OCEAN_P, line=OCEAN_L, n=7):
    """Bidang laut: gradasi lembut + garis gelombang yang bergerak."""
    if alpha <= 0.01:
        return
    rrect_on(img, 0, y0, W, y1, 0, color, alpha * 0.85)
    for i in range(n):
        yy = y0 + 40 + (y1 - y0 - 60) * i / (n - 1.0)
        drift = 40 * math.sin(tg * 0.6 + i * 1.3)
        x0 = -60 + drift
        while x0 < W + 60:
            w = 74 + 18 * math.sin(i * 2.1)
            line_on(img, (x0, yy), (x0 + w, yy), line, 5, alpha * 0.5)
            x0 += 150


def _ship(img, cx, cy, s, color, alpha, tilt=0.0, tg=0.0):
    """Siluet kapal sederhana (haluan, kabin, tiang)."""
    if alpha <= 0.01:
        return
    bob = amb(tg, 0.35) * s * 0.06
    yy = cy + bob
    poly_on(img, [(cx - s * 0.62, yy), (cx + s * 0.62, yy),
                  (cx + s * 0.40, yy + s * 0.30), (cx - s * 0.40, yy + s * 0.30)], color, alpha)
    rrect_on(img, cx - s * 0.26, yy - s * 0.30 + tilt * s * 0.2, cx + s * 0.16,
             yy - s * 0.02, 8, color, alpha)
    line_on(img, (cx, yy - s * 0.30), (cx, yy - s * 0.62), color, max(2, int(s * 0.05)), alpha)


def _plane(img, cx, cy, s, color, alpha, ang=0.0):
    """Siluet pesawat: badan + sayap + ekor, bisa diputar."""
    if alpha <= 0.01:
        return
    body = [(s * 0.62, 0), (-s * 0.34, -s * 0.10), (-s * 0.42, 0), (-s * 0.34, s * 0.10)]
    wing = [(s * 0.05, 0), (-s * 0.22, -s * 0.46), (-s * 0.34, -s * 0.44), (-s * 0.10, 0),
            (-s * 0.34, s * 0.44), (-s * 0.22, s * 0.46)]
    tail = [(-s * 0.30, 0), (-s * 0.46, -s * 0.22), (-s * 0.54, -s * 0.20), (-s * 0.42, 0),
            (-s * 0.54, s * 0.20), (-s * 0.46, s * 0.22)]
    ca, sa = math.cos(ang), math.sin(ang)
    for pts, col in ((body, color), (wing, color), (tail, color)):
        tp = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for (x, y) in pts]
        poly_on(img, tp, col, alpha)


def _tri3(img, p1, p2, p3, color, alpha, width=7, prog=1.0, dash=22):
    """Garis segitiga putus-putus yang tumbuh sesuai prog (0..1)."""
    if alpha <= 0.01 or prog <= 0:
        return
    pts = [p1, p2, p3, p1]
    L = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(3)]
    total = sum(L)
    ingin = total * clamp(prog)
    sudah = 0.0
    for i in range(3):
        if sudah >= ingin:
            break
        frac = min(1.0, (ingin - sudah) / max(1e-6, L[i]))
        x1 = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * frac
        y1 = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * frac
        line_on(img, pts[i], (x1, y1), color, width, alpha, dash=dash)
        sudah += L[i]


def _stream(img, cx, cy, w, alpha, tg=0.0, color=OCEAN):
    """Arus laut: tiga panah melengkung yang mengalir."""
    if alpha <= 0.01:
        return
    for k in range(3):
        yo = cy + (k - 1) * 78
        pts = []
        for i in range(13):
            u = i / 12.0
            pts.append((cx - w / 2 + w * u, yo + 26 * math.sin(u * 3.0 + k)))
        for i in range(len(pts) - 1):
            line_on(img, pts[i], pts[i + 1], color, 6, alpha * (0.45 + 0.25 * math.sin(tg + i * 0.4 + k)))
        _arrow_on(img, pts[-3], pts[-1], color, 7, alpha * 0.9, head=22)


def _compass(img, cx, cy, r, alpha, tg=0.0, color=HULL):
    """Kompas dengan jarum yang berputar bingung."""
    if alpha <= 0.01:
        return
    ring_on(img, cx, cy, r, color, max(3, int(r * 0.10)), alpha * 0.9)
    for i in range(8):
        a = i * math.pi / 4
        line_on(img, (cx + r * 0.72 * math.cos(a), cy + r * 0.72 * math.sin(a)),
                (cx + r * 0.92 * math.cos(a), cy + r * 0.92 * math.sin(a)), color, 5, alpha * 0.7)
    a = tg * 2.4 + 0.4 * math.sin(tg * 3.1)
    line_on(img, (cx - r * 0.55 * math.cos(a), cy - r * 0.55 * math.sin(a)),
            (cx + r * 0.62 * math.cos(a), cy + r * 0.62 * math.sin(a)), RED, max(4, int(r * 0.12)), alpha)


def sc_intro_bermuda(img, d, sc, tl, dur, tg, accent, al, dy):
    """Pembuka: laut malam dengan kapal & pesawat yang menghilang."""
    y = 420
    for i, l in enumerate(sc["lines"]):
        fsz = 128
        while fsz > 50 and tw(l, font(FB, fsz)) > 950:
            fsz -= 4
        q = seg(tl, 0.05 + i * 0.22, 0.55 + i * 0.22)
        if q <= 0:
            continue
        k = espring(q)
        col = accent if i == len(sc["lines"]) - 1 else INK
        paste_c(img, W / 2, y + (1 - k) * 54, l, font(FB, fsz), col, q * al,
                scale=0.88 + 0.12 * k)
        y += 148
    q = seg(tl, 0.8, 1.4)
    if q <= 0:
        return
    alk = q * al
    _sea(img, 900, 1660, alk, tg)
    qq = seg(tl, 1.0, 2.1)
    if qq > 0:
        _tri3(img, (540, 980), (250, 1430), (830, 1430), TRI, qq * alk * 0.95,
              prog=esmooth(qq), dash=26)
    # kapal berlayar masuk lalu memudar
    qq = seg(tl, 1.2, 2.6)
    if qq > 0:
        a2 = qq * alk
        fade = 1.0 - eio(seg(qq, 0.72, 1.0))
        x = 250 + 150 * esmooth(qq)
        yy = 1400
        _trail(img, [(x - 40 - i * 26, yy + amb(tg - i * 0.06, 0.5) * 3) for i in range(5)],
               mix(OCEAN_L, WHITE, 0.3), a2 * fade * 0.5, width=7, tail=4)
        _ship(img, x, yy, 96, HULL, a2 * fade, tg=tg)
    # pesawat melintas lalu menghilang
    qq = seg(tl, 1.5, 2.9)
    if qq > 0:
        a2 = qq * alk
        fade = 1.0 - eio(seg(qq, 0.66, 1.0))
        u = esmooth(qq)
        x = 200 + 660 * u
        yy = 1120 - 90 * math.sin(u * 2.2)
        path = [(x - 60 * i, yy + 22 * i) for i in range(6)]
        _trail(img, path, mix(OCEAN, WHITE, 0.55), a2 * fade * 0.55, width=6, tail=5)
        _plane(img, x, yy, 74, HULL, a2 * fade, ang=-0.22 - 0.2 * u)
    qq = seg(tl, 2.2, 2.8)
    if qq > 0:
        _pill_c(img, W / 2, 1560, "50 KAPAL & 20 PESAWAT HILANG", font(FS, 28),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1650, "Angka catatan populer — bukan wilayah resmi", font(FM, 25),
                MUTED, qq * al)


def sc_where(img, d, sc, tl, dur, tg, accent, al, dy):
    """Di mana tepatnya, dan seberapa ramai kawasan itu."""

    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    titik = [("MIAMI", 250, 1000, 0.5), ("BERMUDA", 540, 700, 0.7), ("PUERTO RIKO", 850, 1180, 0.9)]
    for teks, x, y, t0 in titik:
        qq = seg(tl, t0, t0 + 0.45)
        if qq <= 0:
            continue
        k = espring(qq)
        a2 = qq * al2
        ring_on(img, x, y, 30 + 10 * k, mix(OCEAN_L, WHITE, 0.4), 6, a2)
        dot_on(img, x, y, 16, OCEAN, a2)
        paste_c(img, x, y - 62, teks, font(FS, 26), mix(OCEAN, INK, 0.2), a2)
    qq = seg(tl, 1.1, 1.9)
    if qq > 0:
        _tri3(img, (250, 1000), (540, 700), (850, 1180), TRI, qq * al2 * 0.95,
              prog=esmooth(qq), width=6, dash=24)
    # lalu lintas ramai: banyak titik melintas dengan jejak
    qq = seg(tl, 1.6, 3.0)
    if qq > 0:
        a2 = qq * al2
        for i in range(7):
            u = (tg * 0.16 + i / 7.0) % 1.0
            x = 120 + 840 * u
            y = 900 + 150 * math.sin(u * 3.4 + i)
            path = [(x - 26 * k2, y + 10 * k2) for k2 in range(4)]
            _trail(img, path, mix(OCEAN_L, WHITE, 0.15), a2 * 0.75, width=7, tail=3)
            dot_on(img, x, y, 9, OCEAN, a2 * 0.9)
    qq = seg(tl, 2.0, 2.7)
    if qq > 0:
        _pill_c(img, W / 2, 1420, "ANTARA FLORIDA, BERMUDA, PUERTO RIKO", font(FS, 27),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1512, "Sebutan, bukan wilayah resmi — dan termasuk jalur pelayaran",
                font(FM, 24), MUTED, qq * al)
        paste_c(img, W / 2, 1560, "serta penerbangan paling ramai di dunia", font(FM, 24), MUTED, qq * al)


def sc_cases(img, d, sc, tl, dur, tg, accent, al, dy):
    """Dua kasus paling terkenal: Flight 19 dan USS Cyclops."""

    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    kartu = [(0, 104, "1945", "PENERBANGAN 19", "5 pesawat Angkatan Laut\nhilang saat latihan", HULL),
             (1, 556, "1918", "USS CYCLOPS", "306 awak hilang\ntanpa sinyal darurat", OCEAN)]
    for idx, x0, tahun, nama, isi, col in kartu:
        qq = seg(tl, 0.5 + idx * 0.22, 1.05 + idx * 0.22)
        if qq <= 0:
            continue
        k = espring(qq)
        a2 = qq * al2
        _glow(img, x0, 700, x0 + 420, 1180, col, a2 * 0.28)
        rrect_on(img, x0, 700 + (1 - k) * 40, x0 + 420, 1180, 36, mix(WHITE, col, 0.08), a2,
                 outline=mix(CREAM, col, 0.45), width=3)
        paste_r(img, x0 + 46, 782, tahun, font(FB, 54), mix(col, INK, 0.2), a2)
        paste_r(img, x0 + 46, 862, nama, font(FB, 30), mix(col, INK, 0.25), a2)
        for i, baris in enumerate(isi.split("\n")):
            paste_r(img, x0 + 46, 940 + i * 46, baris, font(FM, 25), MUTED, a2)
    # ikon pesawat & kapal di bawah kartu
    qq = seg(tl, 1.4, 2.2)
    if qq > 0:
        a2 = qq * al2
        u = esmooth(qq)
        _trail(img, [(200 - 60 * i + 260 * u, 1290 + 20 * i) for i in range(5)],
               mix(OCEAN, WHITE, 0.55), a2 * 0.5, width=6, tail=4)
        _plane(img, 200 + 260 * u, 1290, 58, HULL, a2, ang=-0.18)
        _ship(img, 640 + 160 * u, 1290, 74, OCEAN, a2, tg=tg)
    qq = seg(tl, 2.2, 2.8)
    if qq > 0:
        _pill_c(img, W / 2, 1460, "DUA KASUS YANG PALING DIBICARAKAN", font(FS, 28),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1552, "Dari sekitar 50 kapal dan 20 pesawat yang tercatat hilang", font(FM, 24),
                MUTED, qq * al)


def sc_reasons(img, d, sc, tl, dur, tg, accent, al, dy):
    """Penjelasan yang nyata: cuaca, gelombang, arus, kesalahan manusia."""

    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    kotak = [("CUACA CEPAT BERUBAH", 110, 640, 0.0), ("GELOMBANG TINGGI", 565, 640, 0.18),
             ("ARUS KUAT MENYAPU SERPIHAN", 110, 1000, 0.36), ("KESALAHAN NAVIGASI", 565, 1000, 0.54)]
    for teks, x0, y0, t0 in kotak:
        qq = seg(tl, 0.5 + t0, 1.0 + t0)
        if qq <= 0:
            continue
        k = espring(qq)
        a2 = qq * al2
        rrect_on(img, x0, y0 + (1 - k) * 30, x0 + 405, y0 + 310, 32, mix(WHITE, OCEAN_L, 0.25), a2,
                 outline=mix(CREAM, OCEAN, 0.35), width=3)
        paste_r(img, x0 + 40, y0 + 62, teks, font(FS, 25), mix(OCEAN, INK, 0.25), a2)
        if "CUACA" in teks:
            _cloud(img, x0 + 200, y0 + 190, 130, mix(OCEAN, WHITE, 0.35), a2, drops=4, tg=tg)
        elif "GELOMBANG" in teks:
            for i in range(3):
                yy = y0 + 165 + i * 46
                drift = amb(tg, 0.5, 26 * (1 + i * 0.2), i)
                for j in range(4):
                    xa = x0 + 60 + j * 86 + drift
                    line_on(img, (xa, yy), (xa + 52, yy), OCEAN, 6, a2 * 0.8)
        elif "ARUS" in teks:
            _stream(img, x0 + 200, y0 + 205, 300, a2, tg)
        else:
            _compass(img, x0 + 200, y0 + 205, 62, a2, tg)
    qq = seg(tl, 2.0, 2.6)
    if qq > 0:
        _pill_c(img, W / 2, 1400, "PENJELASANNYA BIASA SAJA", font(FS, 29),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1490, "Arus Gulf Stream yang kuat bisa mengangkut serpihan jauh dari lokasi,",
                font(FM, 24), MUTED, qq * al)
        paste_c(img, W / 2, 1538, "jadi bangkai kapal sulit ditemukan", font(FM, 24), MUTED, qq * al)


def sc_data(img, d, sc, tl, dur, tg, accent, al, dy):
    """Apa kata data: tidak lebih berbahaya daripada wilayah laut lain."""

    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    lembaga = ["NOAA", "US COAST GUARD", "LLOYD'S OF LONDON"]
    qq = seg(tl, 0.45, 1.1)
    if qq > 0:
        for i, nm in enumerate(lembaga):
            k = espring(seg(qq, i * 0.22, i * 0.22 + 0.7))
            if k <= 0:
                continue
            _pill_c(img, W / 2, 640 + i * 84 - (1 - k) * 24, nm, font(FS, 26),
                    mix(OCEAN, INK, 0.25), qq * al2, dot=True)
    # batang perbandingan: sebanding
    qq = seg(tl, 1.2, 2.1)
    if qq > 0:
        a2 = qq * al2
        u = esmooth(qq)
        paste_r(img, 120, 950, "Segitiga Bermuda", font(FS, 27), mix(OCEAN, INK, 0.25), a2)
        _pbar(img, 120, 990, 800, 40, 0.98 * u, a2, color=OCEAN)
        paste_r(img, 120, 1094, "Wilayah laut padat lain", font(FS, 27), mix(MUTED, INK, 0.2), a2)
        _pbar(img, 120, 1134, 800, 40, 0.98 * u, a2, color=mix(MUTED, WHITE, 0.45))
        paste_c(img, 960, 1010, "sama", font(FS, 25), mix(OCEAN, INK, 0.2), a2)
        paste_c(img, 960, 1154, "sama", font(FS, 25), MUTED, a2)
    qq = seg(tl, 1.9, 2.6)
    if qq > 0:
        k = espring(qq)
        a2 = qq * al2
        rrect_on(img, 150 + (1 - k) * 30, 1270, 930 - (1 - k) * 30, 1370, 26,
                 mix(WHITE, GREEN, 0.18), a2, outline=mix(CREAM, GREEN, 0.45), width=3)
        paste_c(img, W / 2, 1320, "TIDAK LEBIH BERBAHAYA", font(FB, 34), mix(GREEN, INK, 0.2), a2)
        paste_c(img, W / 2, 1420, "Premi asuransi kapal di kawasan ini tidak dinaikkan khusus",
                font(FM, 24), MUTED, a2)
    qq = seg(tl, 2.5, 3.0)
    if qq > 0:
        paste_c(img, W / 2, 1520, "Jumlah kehilangan sebanding dengan lalu lintasnya yang sangat padat",
                font(FM, 24), MUTED, qq * al)


def sc_legend(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kenapa legenda tetap hidup: cerita yang dibesar-besarkan."""

    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.3, 0.9)
    if q <= 0:
        return
    al2 = q * al
    # tumpukan buku sensasional
    qq = seg(tl, 0.45, 1.2)
    if qq > 0:
        for i in range(3):
            k = espring(seg(qq, i * 0.2, i * 0.2 + 0.7))
            if k <= 0:
                continue
            y0 = 1060 - i * 96 - (1 - k) * 30
            rrect_on(img, 100, y0, 500, y0 + 84, 16, mix(WHITE, TRI, 0.16), qq * al2,
                     outline=mix(CREAM, TRI, 0.5), width=3)
            paste_r(img, 132, y0 + 44, ["BUKU 1960-AN", "FILM & DOKUMENTER", "KABAR BESAR-BESARAN"][i],
                    font(FS, 25), mix(TRI, INK, 0.3), qq * al2)
    # klaim yang dilebih-lebihkan, dicoret
    qq = seg(tl, 1.0, 1.7)
    if qq > 0:
        a2 = qq * al2
        rrect_on(img, 545, 748, 975, 1052, 150, mix(WHITE, OCEAN_L, 0.5), a2)
        kata3 = ["alien", "portal waktu", "kekuatan gaib"]
        q3 = seg(tl, 1.5, 2.0)
        for i, kata in enumerate(kata3):
            yy = 830 + i * 70
            fk = font(FS, 28)
            kw = tw(kata, fk)
            paste_r(img, 760 - kw / 2, yy, kata, fk, mix(MUTED, INK, 0.15), a2)
            if q3 > 0:
                line_on(img, (760 - kw / 2 - 12, yy), (760 + kw / 2 + 12, yy),
                        mix(RED, INK, 0.1), 7, q3 * al2)
    # kenapa kita percaya: bias perhatian
    qq = seg(tl, 2.0, 2.6)
    if qq > 0:
        _pill_c(img, W / 2, 1300, "MISTERINYA ADA DI CERITA, BUKAN DI LAUT", font(FS, 27),
                mix(accent, INK, 0.15), qq * al, dot=True)
        paste_c(img, W / 2, 1392, "Kita ingat satu cerita aneh, tapi lupa ribuan pelayaran yang selamat",
                font(FM, 24), MUTED, qq * al)
        paste_c(img, W / 2, 1440, "setiap hari di jalur yang sama", font(FM, 24), MUTED, qq * al)
    qq = seg(tl, 2.7, 3.2)
    if qq > 0:
        star4(img, 540 + 0, 1560, 30, mix(GREEN, WHITE, 0.1), qq * al)
        paste_c(img, W / 2, 1630, "Sains tidak bilang laut itu jinak — hanya tidak ada bukti kekuatan aneh",
                font(FM, 23), MUTED, qq * al)


# ============================================================ mesin v3 (Ep18+)
def _polylines(img, paths, color, width=3.4, alpha=1.0):
    """Banyak polyline sekaligus pada satu layer — untuk guratan rapat (pola sidik jari)."""
    if alpha <= 0.01 or not paths:
        return
    xs = [p[0] for path in paths for p in path]
    ys = [p[1] for path in paths for p in path]
    pad = width * 2 + 10
    bx = _box(img, min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    if bx is None:
        return
    X0, Y0, X1b, Y1b = bx
    lay = Image.new("RGBA", (X1b - X0, Y1b - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    lw = max(1, int(round(S(width))))
    r = lw / 2.0
    for path in paths:
        pts = [(S(p[0]) - X0, S(p[1]) - Y0) for p in path]
        if len(pts) < 2:
            continue
        dd.line(pts, fill=color + (255,), width=lw, joint="curve")
        for (px, py) in (pts[0], pts[-1]):
            dd.ellipse([px - r, py - r, px + r, py + r], fill=color + (255,))
    _put_at(img, lay, X0, Y0, alpha)


def _ridges(img, cx, cy, r, color, alpha=1.0, prog=1.0, kind="loop", rot=0.0,
            n=11, w=3.4, squash=1.22, wob=0.0):
    """Pola sidik jari: busur sepusat dengan inti terbuka (arch / loop / whorl).

    prog < 1 membuat pola tumbuh dari inti keluar — dipakai untuk animasi 'tumbuh'.
    """
    if alpha <= 0.01 or prog <= 0.02 or r <= 2:
        return
    nshow = max(1, int(round(n * clamp(prog))))
    span = {"arch": (200.0, 340.0), "loop": (70.0, 290.0), "whorl": (0.0, 360.0)}.get(kind)
    if span is None:
        span = (70.0, 290.0)
    paths = []
    for i in range(nshow):
        u = i / max(1, n - 1)
        rr = r * (0.17 + 0.83 * u)
        ry = rr * squash
        a0, a1 = math.radians(span[0] + rot), math.radians(span[1] + rot)
        steps = 66
        path = []
        for k in range(steps + 1):
            ang = a0 + (a1 - a0) * k / steps
            jit = 1.0 + (wob * math.sin(ang * 4.0 + i * 0.7))
            path.append((cx + rr * math.cos(ang) * jit, cy + ry * math.sin(ang) * jit))
        paths.append(path)
    _polylines(img, paths, color, w, alpha)


def _soft_shadow(img, x0, y0, x1, y1, r=40, alpha=0.10, spread=20, color=None):
    """Bayangan lembut bertingkat — memberi kedalaman pada panel/kartu."""
    if alpha <= 0.01:
        return
    sh = color or mix(CREAM, INK, 0.34)
    for i in (4, 3, 2, 1):
        g = spread * i / 4.0
        rrect_on(img, x0 - g * 0.45, y0 + g * 0.60, x1 + g * 0.45, y1 + g * 0.95,
                 r + g * 0.55, sh, alpha * (0.26 if i == 4 else 0.40))


def _motes(img, tg, color, alpha=0.40, n=22, spread=0.0):
    """Bintik halus melayang (ambient) — deterministik, tidak berkedip antar frame."""
    if alpha <= 0.01:
        return
    for i in range(n):
        h = (i * 2654435761 + 1013904223) % 4294967296
        fx = ((h >> 7) % 1000) / 1000.0
        fy = ((h >> 17) % 1000) / 1000.0
        sp = 5.0 + ((h >> 3) % 9)
        ph = (h % 628) / 100.0
        x = fx * W + math.sin(tg * 0.18 + ph) * (12 + spread)
        y = (fy * H + tg * sp) % H
        rr = 2.6 + ((h >> 5) % 4) * 1.5
        a = alpha * (0.30 + 0.70 * abs(math.sin(tg * 0.32 + ph)))
        dot_on(img, x, y, rr, color, a)


def counter_c(img, cx, cy, tg, t0, t1, v0, v1, f, fill, alpha=1.0,
              pre="", suf="", dec=0, sep="."):
    """Angka berjalan (count-up) dengan easing halus — untuk statistik di layar."""
    k = esmooth(seg(tg, t0, t1))
    v = v0 + (v1 - v0) * k
    txt = f"{v:,.{dec}f}".replace(",", "\x00").replace(".", sep).replace("\x00", ",")
    paste_c(img, cx, cy, pre + txt + suf, f, fill, alpha)


# ============================================================ EP18 · SIDIK JARI
SKIN = mix(CREAM, (236, 202, 172), 0.60)     # warna kulit lembut
SKIN_D = mix(SKIN, AMBER, 0.42)              # guratan kulit


def _tprint(img, cx, cy, r, color, alpha, prog=1.0, kind="whorl", rot=0.0, w=4.0, wob=0.0, n=None):
    """Sidik jari: busur sepusat + inti kecil. Jumlah guratan menyesuaikan ukuran."""
    if alpha <= 0.01:
        return
    if n is None:
        n = int(max(6, min(20, round(r / 16.0))))
    lw = w * (0.70 if n >= 14 else 0.88)
    _ridges(img, cx, cy, r, color, alpha, prog=prog, kind=kind, rot=rot, n=n, w=lw,
            squash=1.24, wob=wob)
    if prog > 0.45:
        dot_on(img, cx, cy - r * 0.08, max(2.5, r * 0.05), color, alpha)


def _filament(img, x0, x1, y0, amp, color, width, alpha, fase=0.0, freq=0.42, lines=2, spread=34):
    """Berkas garis bergelombang (dipakai untuk sinyal pembentuk pola)."""
    if alpha <= 0.01:
        return
    paths = []
    for k in range(lines):
        pts = []
        n = max(8, int((x1 - x0) / 22))
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            pts.append((x, y0 + k * spread + amp * math.sin(x * freq * 0.06 - fase + k * 1.7)))
        paths.append(pts)
    _polylines(img, paths, color, width, alpha)


def sc_intro_print(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: sidik jari besar tumbuh dari inti, dengan halo dan bintik halus."""
    cx, cy = 540, 1235 + dy
    for k, rr in enumerate((352, 312, 272)):
        ell(img, cx - rr, cy - rr, cx + rr, cy + rr, fill=mix(accent, WHITE, 0.58 + k * 0.055),
            alpha=0.48 * al)
    ring_on(img, cx, cy, 322 + amb(tg, 0.22) * 9, mix(accent, WHITE, 0.40), 3, 0.38 * al)
    _tprint(img, cx, cy, 300, mix(accent, INK, 0.16), al, prog=esmooth(seg(tl, 0.25, 1.75)),
            kind="whorl", rot=-6, w=3.6, wob=0.018, n=22)
    _motes(img, tg, mix(accent, WHITE, 0.45), 0.34 * al, n=24, spread=10)
    q = seg(tl, 1.45, 2.0)
    if q > 0:
        _pill_c(img, cx, 1668 + dy, "SETIAP ORANG · POLA SENDIRI", font(FS, 30),
                mix(accent, INK, 0.10), esmooth(q) * al, dot=True)


def sc_print_what(img, d, sc, tl, dur, tg, accent, al, dy):
    """Apa itu sidik jari: guratan kulit di ujung jari, terbentuk sebelum lahir."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.24, 1.0)
    if q <= 0:
        return
    a = esmooth(q) * al
    cx, cy = 392, 700 + dy
    _soft_shadow(img, cx - 250, cy - 250, cx + 250, cy + 250, 250, 0.10 * a, spread=26)
    ell(img, cx - 246, cy - 246, cx + 246, cy + 246, fill=mix(SKIN, WHITE, 0.30), alpha=a)
    _tprint(img, cx, cy, 196, mix(SKIN_D, INK, 0.24), a, prog=esmooth(seg(tl, 0.34, 1.25)),
            kind="whorl", rot=-6, w=4.4, wob=0.015)
    _motes(img, tg, mix(accent, WHITE, 0.55), 0.22 * a, n=14, spread=6)
    q2 = seg(tl, 0.95, 1.5)
    if q2 > 0:
        a2 = esmooth(q2) * al
        line_on(img, (cx + 150, cy - 96), (cx + 306, cy - 156), mix(MUTED, INK, 0.15), 4, a2)
        paste_r(img, cx + 316, cy - 156, "guratan kulit", font(FM, 27), mix(INK, MUTED, 0.22), a2)
        line_on(img, (cx + 128, cy + 132), (cx + 306, cy + 176), mix(MUTED, INK, 0.15), 4, a2)
        paste_r(img, cx + 316, cy + 176, "lekukannya", font(FM, 27), mix(INK, MUTED, 0.22), a2)
    q3 = seg(tl, 1.55, 2.55)
    if q3 > 0:
        a3 = esmooth(q3) * al
        y0 = 1275 + dy
        line_on(img, (152, y0), (928, y0), mix(MUTED, CREAM, 0.30), 7, a3)
        dot_on(img, 152, y0, 14, accent, a3)
        dot_on(img, 928, y0, 14, accent, a3)
        k = esmooth(seg(tl, 1.85, 2.95))
        mx = 152 + 776 * k
        dot_on(img, mx, y0, 20, mix(accent, WHITE, 0.12), a3)
        paste_c(img, mx, y0 - 62, "terbentuk", font(FM, 24), mix(accent, INK, 0.18), a3)
        paste_r(img, 152, y0 + 66, "minggu ke-13", font(FM, 26), MUTED, a3)
        paste_r(img, 720, y0 + 66, "minggu ke-19", font(FM, 26), MUTED, a3)
    q4 = seg(tl, 2.6, 3.1)
    if q4 > 0:
        _pill_c(img, 540, 1590 + dy, "SUDAH ADA SEBELUM LAHIR", font(FS, 29),
                mix(accent, INK, 0.10), esmooth(q4) * al, dot=True)


def sc_print_how(img, d, sc, tl, dur, tg, accent, al, dy):
    """Bagaimana pola terbentuk: kulit tumbuh sambil didorong cairan & posisi jari."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.24, 1.0)
    if q <= 0:
        return
    a = esmooth(q) * al
    cx, cy = 540, 700 + dy
    ell(img, cx - 330, cy - 292, cx + 330, cy + 292, fill=mix(accent, WHITE, 0.88), alpha=a)
    ring_on(img, cx, cy, 300 + amb(tg, 0.18) * 6, mix(accent, WHITE, 0.52), 3, 0.55 * a)
    # ujung jari kecil di dalam cairan
    ell(img, cx - 104, cy - 104, cx + 104, cy + 104, fill=mix(SKIN, WHITE, 0.25), alpha=a)
    _tprint(img, cx, cy, 78, mix(SKIN_D, INK, 0.22), a, prog=esmooth(seg(tl, 0.5, 1.5)), kind="whorl", w=3.4, wob=0.012)
    # aliran cairan: busur bergerak mendorong jari
    for k, (rr, sp, wd) in enumerate(((196, 1.0, 4), (246, -0.72, 4), (290, 0.55, 4))):
        pts = []
        for i in range(25):
            ang = -2.35 + 4.7 * i / 24
            jig = 1.0 + 0.03 * math.sin(tg * 1.6 * sp + i * 0.6)
            pts.append((cx + rr * jig * math.cos(ang), cy + rr * jig * 0.92 * math.sin(ang)))
        _polylines(img, [pts], mix(accent, WHITE, 0.15), wd, a * 0.75)
        hx, hy = pts[6]
        dot_on(img, hx, hy, 7, mix(accent, INK, 0.05), a * 0.9)
        hx, hy = pts[18]
        dot_on(img, hx, hy, 7, mix(accent, INK, 0.05), a * 0.9)
    q2 = seg(tl, 1.5, 2.1)
    if q2 > 0:
        a2 = esmooth(q2) * al
        paste_c(img, 540, 1092 + dy, "cairan dan posisi jari mendorong kulit", font(FM, 26), MUTED, a2)
        paste_c(img, 540, 1140 + dy, "sewaktu sel-selnya tumbuh", font(FM, 26), MUTED, a2)
    # gelombang sinyal bertemu -> guratan terbentuk
    q3 = seg(tl, 2.1, 3.0)
    if q3 > 0:
        a3 = esmooth(q3) * al
        y0 = 1300 + dy
        _filament(img, 130, 520, y0, 22, mix(accent, INK, 0.12), 5, a3, fase=tg * 2.2, lines=2, spread=40)
        _filament(img, 950, 560, y0, 22, mix(AMBER, INK, 0.15), 5, a3, fase=tg * 2.2 + 1.5, lines=2, spread=40)
        line_on(img, (560, y0 + 20), (620, y0 + 20), mix(MUTED, INK, 0.1), 6, a3)
        dot_on(img, 620, y0 + 20, 12, mix(accent, INK, 0.05), a3)
        _tprint(img, 760, y0 + 12, 96, mix(accent, INK, 0.18), a3,
                prog=esmooth(seg(tl, 2.45, 3.25)), kind="whorl", rot=90, w=3.6)
    q4 = seg(tl, 3.1, 3.6)
    if q4 > 0:
        _pill_c(img, 540, 1620 + dy, "POLA ACALKU BUKAN SATU CETAKAN", font(FS, 29),
                mix(accent, INK, 0.10), esmooth(q4) * al, dot=True)


def sc_print_twins(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kembar identik: DNA hampir sama, sidik jari tetap berbeda."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.24, 1.0)
    if q <= 0:
        return
    a = esmooth(q) * al
    # pita DNA (dua heliks sederhana)
    y0 = 640 + dy
    _filament(img, 250, 830, y0, 26, mix(accent, INK, 0.12), 5, a, fase=tg * 1.4, lines=2, spread=44)
    for i in range(9):
        x = 268 + i * 70
        off = 22 * math.sin(x * 0.03 - tg * 1.4)
        line_on(img, (x, y0 + off), (x, y0 + 44 - off), mix(accent, WHITE, 0.25), 4, a * 0.9)
    paste_c(img, 540, y0 + 118, "DNA hampir sama", font(FM, 26), MUTED, a)
    # dua sidik jari berbeda
    q2 = seg(tl, 0.9, 1.6)
    if q2 > 0:
        a2 = esmooth(q2) * al
        _soft_shadow(img, 150, 856, 500, 1206, 175, 0.10 * a2, spread=22)
        _soft_shadow(img, 580, 856, 930, 1206, 175, 0.10 * a2, spread=22)
        ell(img, 152, 858, 500, 1206, fill=mix(WHITE, accent, 0.05), alpha=a2)
        ell(img, 580, 858, 928, 1206, fill=mix(WHITE, accent, 0.05), alpha=a2)
        _tprint(img, 326, 1032, 138, mix(accent, INK, 0.18), a2,
                prog=esmooth(seg(tl, 1.0, 1.9)), kind="whorl", rot=-4, w=3.8, wob=0.010)
        _tprint(img, 754, 1032, 138, mix(accent, INK, 0.18), a2,
                prog=esmooth(seg(tl, 1.15, 2.05)), kind="whorl", rot=16, w=3.8, wob=0.030)
        paste_c(img, 326, 1260, "kembar A", font(FM, 26), MUTED, a2)
        paste_c(img, 754, 1260, "kembar B", font(FM, 26), MUTED, a2)
        # tanda tidak sama di tengah
        line_on(img, (524, 1006), (556, 1006), mix(RED, INK, 0.12), 6, a2)
        line_on(img, (518, 1058), (562, 1058), mix(RED, INK, 0.12), 6, a2)
    q3 = seg(tl, 2.0, 2.6)
    if q3 > 0:
        a3 = esmooth(q3) * al
        _pill_c(img, 540, 1400 + dy, "DNA SAMA, SIDIK JARI BEDA", font(FS, 29),
                mix(accent, INK, 0.10), a3, dot=True)
        paste_c(img, 540, 1500 + dy, "jari kiri dan jari kanan juga tidak sama", font(FM, 26), MUTED, a3)


def sc_print_patterns(img, d, sc, tl, dur, tg, accent, al, dy):
    """Tiga pola dasar sidik jari beserta porsinya di populasi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    rows = (("LENGKUNG", "loop", 60, -4), ("PUSARAN", "whorl", 30, 0), ("BUSUR", "arch", 5, 0))
    for i, (nama, kind, persen, rot) in enumerate(rows):
        q = seg(tl, 0.3 + i * 0.34, 1.0 + i * 0.34)
        if q <= 0:
            continue
        a = esmooth(q) * al
        y0 = 620 + i * 300 + dy
        _soft_shadow(img, 96, y0 - (1 - q) * 24, 984, y0 + 232, 40, 0.10 * a, spread=20)
        rrect_on(img, 96, y0, 984, y0 + 232, 40, mix(WHITE, accent, 0.05), a,
                 outline=mix(CREAM, accent, 0.30), width=3)
        _tprint(img, 226, y0 + 116, 76, mix(accent, INK, 0.18), a,
                prog=esmooth(seg(q, 0.15, 0.85)), kind=kind, rot=rot, w=3.4)
        paste_r(img, 344, y0 + 92, nama, font(FS, 36), mix(accent, INK, 0.18), a)
        paste_r(img, 344, y0 + 148, ("paling banyak" if i == 0 else ("cukup banyak" if i == 1 else "paling jarang")),
                font(FM, 25), MUTED, a)
        counter_c(img, 872, y0 + 112, tg, 0.5 + i * 0.34, 1.5 + i * 0.34, 0, persen,
                  font(FB, 62), mix(accent, INK, 0.10), a, suf="%")
    q4 = seg(tl, 1.7, 2.3)
    if q4 > 0:
        paste_c(img, 540, 1600 + dy, "angka dari data populasi — bisa berbeda tiap kelompok",
                font(FM, 24), MUTED, esmooth(q4) * al)


def sc_print_uses(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kegunaan guratan kulit: cengkeraman, peraba lebih peka, dan cerita koala."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    # baris 1 — cengkeraman
    q = seg(tl, 0.3, 1.0)
    if q > 0:
        a = esmooth(q) * al
        y0 = 620 + dy
        rrect_on(img, 132, y0 + 76, 948, y0 + 108, 16, mix(accent, WHITE, 0.55), a)
        ell(img, 208, y0 - 24, 420, y0 + 108, fill=mix(SKIN, WHITE, 0.20), alpha=a)
        _tprint(img, 314, y0 + 42, 62, mix(SKIN_D, INK, 0.25), a, prog=1.0, kind="whorl", w=3.0)
        for k in range(3):
            xx = 470 + k * 132
            line_on(img, (xx, y0 + 40), (xx + 74, y0 + 40), mix(accent, INK, 0.06), 8, a)
            poly_on(img, [(xx + 74, y0 + 24), (xx + 100, y0 + 40), (xx + 74, y0 + 56)],
                    mix(accent, INK, 0.06), a)
        paste_r(img, 132, y0 + 186, "cengkeraman makin kuat", font(FS, 32), mix(accent, INK, 0.2), a)
    # baris 2 — peraba lebih peka
    q = seg(tl, 0.85, 1.55)
    if q > 0:
        a = esmooth(q) * al
        y0 = 940 + dy
        ell(img, 208, y0 - 4, 408, y0 + 100, fill=mix(SKIN, WHITE, 0.20), alpha=a)
        _tprint(img, 308, y0 + 48, 62, mix(SKIN_D, INK, 0.25), a, prog=1.0, kind="loop", w=3.0)
        for k in range(3):
            rr = 76 + k * 38 + amb(tg, 0.5 + k * 0.2, 5)
            ring_on(img, 500, y0 + 48, rr, mix(accent, WHITE, 0.25), 4, a * (0.75 - k * 0.16))
        paste_r(img, 132, y0 + 186, "lebih peka merasakan tekstur", font(FS, 32), mix(accent, INK, 0.2), a)
    # baris 3 — koala
    q = seg(tl, 1.4, 2.1)
    if q > 0:
        a = esmooth(q) * al
        y0 = 1260 + dy
        kx, ky = 308, y0 + 48
        ell(img, kx - 74, ky - 60, kx + 74, ky + 88, fill=mix(accent, WHITE, 0.30), alpha=a)
        dot_on(img, kx - 66, ky - 62, 34, mix(accent, WHITE, 0.20), a)
        dot_on(img, kx + 66, ky - 62, 34, mix(accent, WHITE, 0.20), a)
        dot_on(img, kx, ky + 34, 20, mix(INK, accent, 0.35), a)
        paste_c(img, kx, ky + 124, "koala", font(FM, 24), MUTED, a)
        _tprint(img, 560, y0 + 48, 62, mix(accent, INK, 0.16), a, prog=1.0, kind="whorl", rot=6, w=3.0)
        paste_r(img, 672, y0 + 44, "polanya nyaris sama", font(FS, 32), mix(accent, INK, 0.2), a)
    q4 = seg(tl, 2.2, 2.7)
    if q4 > 0:
        _pill_c(img, 540, 1650 + dy, "BUKAN HIASAN — ADA GUNA", font(FS, 29),
                mix(accent, INK, 0.10), esmooth(q4) * al, dot=True)


def sc_print_id(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sidik jari sebagai tanda pengenal: dari kantor polisi sampai ponsel."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = seg(tl, 0.28, 1.0)
    if q <= 0:
        return
    a = esmooth(q) * al
    # kartu arsip 1901
    y0 = 780 + dy
    _soft_shadow(img, 110, y0, 600, y0 + 330, 44, 0.11 * a, spread=22)
    rrect_on(img, 110, y0, 600, y0 + 330, 44, mix(WHITE, accent, 0.05), a)
    paste_r(img, 156, y0 + 74, "1901", font(FB, 52), mix(accent, INK, 0.10), a)
    paste_r(img, 156, y0 + 132, "Scotland Yard mulai", font(FM, 24), MUTED, a)
    paste_r(img, 156, y0 + 168, "mencatat sidik jari", font(FM, 24), MUTED, a)
    _tprint(img, 500, y0 + 232, 68, mix(accent, INK, 0.20), a, prog=esmooth(seg(tl, 0.6, 1.4)),
            kind="whorl", w=3.2)
    # panah ke ponsel
    q2 = seg(tl, 1.0, 1.6)
    if q2 > 0:
        a2 = esmooth(q2) * al
        line_on(img, (640, y0 + 165), (740, y0 + 165), mix(MUTED, INK, 0.12), 7, a2)
        poly_on(img, [(740, y0 + 145), (774, y0 + 165), (740, y0 + 185)], mix(MUTED, INK, 0.12), a2)
    q3 = seg(tl, 1.3, 2.0)
    if q3 > 0:
        a3 = esmooth(q3) * al
        _soft_shadow(img, 806, y0 - 6, 986, y0 + 336, 46, 0.11 * a3, spread=20)
        _phone(img, 896, y0 + 165, 180, 330, a3)
        _tprint(img, 896, y0 + 150, 58, mix(accent, INK, 0.18), a3, prog=esmooth(seg(tl, 1.5, 2.2)),
                kind="whorl", w=3.2)
        ring_on(img, 896, y0 + 150, 74 + amb(tg, 0.4, 7), mix(accent, WHITE, 0.20), 4, a3 * 0.8)
        paste_c(img, 896, y0 + 262, "sensor", font(FM, 24), MUTED, a3)
    q4 = seg(tl, 2.0, 2.7)
    if q4 > 0:
        a4 = esmooth(q4) * al
        _pill_c(img, 540, 1280 + dy, "BELUM PERNAH ADA DUA YANG SAMA", font(FS, 29),
                mix(accent, INK, 0.10), a4, dot=True)
        paste_c(img, 540, 1390 + dy, "peluang dua orang punya pola sama disebut sekitar", font(FM, 25), MUTED, a4)
        counter_c(img, 470, 1462 + dy, tg, 2.1, 3.1, 1, 64, font(FB, 46), mix(accent, INK, 0.10), a4, pre="1 : ")
        paste_r(img, 578, 1462 + dy, "miliar", font(FM, 27), MUTED, a4)


VISUALS = {
    "intro_split": sc_intro,
    "cross_section": sc_cross,
    "depth_ruler": sc_ruler,
    "effects": sc_effects,
    "energy": sc_energy,
    "mmi": sc_mmi,
    "intro_predict": sc_intro_predict,
    "why_not": sc_why_not,
    "wave_race": sc_wave_race,
    "countdown": sc_countdown,
    "hoax": sc_hoax,
    "checklist": sc_checklist,
    "intro_rain": sc_intro_rain,
    "enso_iod": sc_enso_iod,
    "atmo_waves": sc_atmo_waves,
    "local_storm": sc_local_storm,
    "dry_risk": sc_dry_risk,
    "tips_rain": sc_tips_rain,
    "intro_malware": sc_intro_malware,
    "spread_chain": sc_spread_chain,
    "stolen_data": sc_stolen_data,
    "not_cracked": sc_not_cracked,
    "protect_steps": sc_protect_steps,
    "check_now": sc_check_now,
    "intro_sky": sc_intro_sky,
    "white_light": sc_white_light,
    "air_scatter": sc_air_scatter,
    "not_violet": sc_not_violet,
    "sunset_red": sc_sunset_red,
    "space_black": sc_space_black,
    "intro_heat": sc_intro_heat,
    "heat_source": sc_heat_source,
    "causes4": sc_causes4,
    "throttle": sc_throttle,
    "normal_not": sc_normal_not,
    "cool_tips": sc_cool_tips,
    "intro_aurora": sc_intro_aurora,
    "solar_wind": sc_solar_wind,
    "collide": sc_collide,
    "colors": sc_colors,
    "why_not_indonesia": sc_why_not_indonesia,
    "watch_tips": sc_watch_tips,
    "intro_cold": sc_intro_cold,
    "two_giants": sc_two_giants,
    "mad": sc_mad,
    "proxy": sc_proxy,
    "cuba": sc_cuba,
    "end_cold": sc_end_cold,
    "intro_ai": sc_intro_ai,
    "examples": sc_examples,
    "training": sc_training,
"predict": sc_predict,
    "scale": sc_scale,
    "use_safe": sc_use_safe,
    "intro_bermuda": sc_intro_bermuda,
    "where": sc_where,
    "cases": sc_cases,
    "reasons": sc_reasons,
    "data": sc_data,
    "legend": sc_legend,
    "intro_print": sc_intro_print,
    "print_what": sc_print_what,
    "print_how": sc_print_how,
    "print_twins": sc_print_twins,
    "print_patterns": sc_print_patterns,
    "print_uses": sc_print_uses,
    "print_id": sc_print_id,
}
# ---------- Ep19: Lubang hitam — kalau kamu jatuh ke dalamnya ----------
# Palet baru: bola gelap, cakram panas, bintang pucat.
VOID = (17, 17, 25)
HOT = (226, 120, 52)
HOT_L = (246, 198, 132)
STARC = (250, 226, 186)


def _glow_round(img, cx, cy, r, color, alpha, layers=4, squash=1.0):
    """Cahaya lembut BULAT (tanpa sudut kotak): beberapa lapis elips alfa rendah."""
    if alpha <= 0.01:
        return
    for k in range(layers, 0, -1):
        rr = r * (0.45 + 0.55 * k / layers)
        ell(img, cx - rr, cy - rr * squash, cx + rr, cy + rr * squash, fill=color,
            alpha=alpha * (0.16 + 0.10 * (layers - k) / max(1, layers - 1)),
            outline=color, width=2)


def drift(t, speed=0.25, amp=1.0, ph=0.0):
    """Ayunan lambat terus-menerus — gerak ambient yang tidak pernah beku."""
    return amp * math.sin(t * speed * math.tau + ph)


def _dots(img, items, alpha=1.0, pad=16):
    """Banyak titik dalam SATU layer (cepat): bintang, partikel cakram, pecahan."""
    if alpha <= 0.01 or not items:
        return
    xs = [it[0] for it in items]
    ys = [it[1] for it in items]
    bx = _box(img, min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    if bx is None:
        return
    X0, Y0, X1b, Y1b = bx
    lay = Image.new("RGBA", (X1b - X0, Y1b - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    for (x, y, r, col, al) in items:
        if al <= 0.02 or r <= 0.2:
            continue
        px, py = S(x) - X0, S(y) - Y0
        rr = max(1.0, S(r))
        dd.ellipse([px - rr, py - rr, px + rr, py + rr],
                   fill=tuple(col) + (int(255 * clamp(al)),))
    _put_at(img, lay, X0, Y0, alpha)


def path_on(img, pts, color, width=4.0, alpha=1.0):
    """Garis mengikuti jalur (untuk lintasan cahaya/benda yang membelok)."""
    if alpha <= 0.01 or len(pts) < 2:
        return
    p = width * 2 + 10
    xs = [q[0] for q in pts]
    ys = [q[1] for q in pts]
    bx = _box(img, min(xs) - p, min(ys) - p, max(xs) + p, max(ys) + p)
    if bx is None:
        return
    X0, Y0, X1b, Y1b = bx
    lay = Image.new("RGBA", (X1b - X0, Y1b - Y0), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    lw = max(1, int(round(S(width))))
    xy = [(S(q[0]) - X0, S(q[1]) - Y0) for q in pts]
    dd.line(xy, fill=tuple(color) + (255,), width=lw, joint="curve")
    rr = lw / 2.0
    for (px, py) in (xy[0], xy[-1]):
        dd.ellipse([px - rr, py - rr, px + rr, py + rr], fill=tuple(color) + (255,))
    _put_at(img, lay, X0, Y0, alpha)


def trail_on(img, pts, color, alpha=1.0, width=7.0, tail=10):
    """Jejak gerak: makin pudar ke belakang — gerak terasa halus, bukan patah."""
    if alpha <= 0.01 or len(pts) < 2:
        return
    seg_pts = pts[-max(2, tail):]
    n = len(seg_pts)
    for i in range(n - 1):
        k = (i + 1) / (n - 1)
        line_on(img, seg_pts[i], seg_pts[i + 1], color,
                width * (0.30 + 0.70 * k), alpha * (k ** 1.4) * 0.85)


def _stars(img, tg, alpha, n=30, y0=420, y1=1700, color=None):
    """Taburan bintang berkelip sangat perlahan."""
    c = color or mix(CREAM, INK, 0.34)
    items = []
    for i in range(n):
        h = (i * 2246822519 + 374761393) % 4294967296
        x = ((h >> 7) % 1000) / 1000.0 * W
        y = y0 + ((h >> 17) % 1000) / 1000.0 * (y1 - y0)
        rr = 1.5 + ((h >> 5) % 3) * 1.1
        a = alpha * (0.18 + 0.82 * abs(math.sin(tg * 0.5 + (h % 628) / 100.0)))
        items.append((x, y, rr, c, a))
    _dots(img, items, alpha)


def _disk(img, cx, cy, r, alpha, tg, tilt=0.34, n=48, speed=1.0, inner=0.24, color=None):
    """Cakram akresi: partikel mengorbit — makin dekat, makin cepat & makin terang."""
    col = color or HOT
    items = []
    for i in range(n):
        h = (i * 1103515245 + 12345) % 2147483648
        u = inner + ((h >> 7) % 1000) / 1000.0 * (1.15 - inner)
        ph = (h % 6283) / 1000.0
        ang = ph + tg * (1.30 / (u ** 1.25)) * speed
        rr = r * u
        k = clamp(1.0 - (u - inner) / (1.25 - inner))
        items.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang) * tilt,
                      3.4 + 4.6 * k, mix(col, WHITE, 0.10 + 0.46 * k), alpha * (0.34 + 0.66 * k)))
    _dots(img, items, alpha)


def _hole(img, cx, cy, r, alpha, tg=0.0, halo=True):
    """Lubang hitam: bola gelap + cincin cahaya + citra cakram yang dibelokkan."""
    if alpha <= 0.01:
        return
    if halo:
        _glow_round(img, cx, cy, r * 2.0, HOT_L, 0.34 * alpha, layers=4, squash=0.55)
    ring_on(img, cx, cy - r * 0.09, r * 1.50, mix(HOT, WHITE, 0.28), 7, 0.42 * alpha, squash=0.14)
    ring_on(img, cx, cy, r * 1.28, mix(HOT, WHITE, 0.34), 7, 0.60 * alpha)
    ring_on(img, cx, cy, r * 1.10, mix(HOT_L, WHITE, 0.10), 10, 0.92 * alpha)
    ell(img, cx - r, cy - r, cx + r, cy + r, fill=VOID, alpha=alpha)


def _earth(img, cx, cy, r, alpha, tg):
    """Bumi kecil: bola biru dengan benua samar + kilau."""
    ell(img, cx - r, cy - r, cx + r, cy + r, fill=mix(BLUE, WHITE, 0.18), alpha=alpha)
    for (du, dv, rr) in ((-0.30, -0.22, 0.42), (0.28, 0.10, 0.34), (-0.05, 0.45, 0.26)):
        ell(img, cx + du * r - rr * r * 0.5, cy + dv * r - rr * r * 0.30,
            cx + du * r + rr * r * 0.5, cy + dv * r + rr * r * 0.30,
            fill=mix(GREEN, WHITE, 0.22), alpha=alpha * 0.85)
    ring_on(img, cx, cy, r, mix(BLUE, INK, 0.25), 3, alpha * 0.9)


def _probe(img, x, y, r, color, alpha=1.0, tg=0.0):
    """Penanda 'kamu': titik bercahaya dengan denyut halus."""
    r2 = r * (1.0 + 0.10 * math.sin(tg * 3.4))
    dot_on(img, x, y, r2 * 2.3, mix(color, WHITE, 0.5), alpha * 0.30)
    dot_on(img, x, y, r2, color, alpha)


def _infall(u, cx, cy, r0=520.0, r1=205.0, turns=2.3, tilt=0.34, ph0=-1.15):
    """Titik pada spiral jatuh (dipakai untuk jejak + posisi penanda)."""
    rr = r0 + (r1 - r0) * clamp(u)
    ang = ph0 + turns * math.tau * clamp(u)
    return (cx + rr * math.cos(ang), cy + rr * math.sin(ang) * tilt)


def sc_intro_bh(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: lubang hitam dengan cakram berputar + satu titik jatuh berjejak."""
    cx, cy = 540, 1218 + dy
    _stars(img, tg, 0.9 * al, n=36, y0=400, y1=1720)
    q = espring(seg(tl, 0.10, 1.05))
    r = 196 * clamp(q)
    _glow_round(img, cx, cy, r * 2.05, HOT_L, 0.30 * al, layers=4, squash=0.42)
    _disk(img, cx, cy, r * 2.05, al, tg, n=64, speed=1.0)
    _hole(img, cx, cy, r, al * clamp(seg(tl, 0.12, 0.80)), tg, halo=False)
    _disk(img, cx, cy, r * 1.30, al, tg, n=20, speed=1.45, inner=0.80)
    # teks judul
    for i, l in enumerate(sc.get("lines") or []):
        q2 = esmooth(seg(tl, 0.45 + i * 0.22, 1.05 + i * 0.22))
        if q2 <= 0:
            continue
        fsz = 120 if i == 0 else 58
        nm = FB if i == 0 else FS
        f = font(nm, fsz)
        while tw(l, f) > 900 and fsz > 40:
            fsz -= 6
            f = font(nm, fsz)
        paste_c(img, 540, (596 + i * 112) + dy, l, f,
                INK if i == 0 else mix(accent, INK, 0.05), q2 * al)
    # satu titik jatuh berjejak
    k = clamp(seg(tl, 0.85, 4.4))
    if k > 0:
        pts = [_infall(max(0.0, k - 0.30 * (j / 11.0)), cx, cy) for j in range(12)] + \
              [_infall(k, cx, cy)]
        trail_on(img, pts, mix(HOT_L, HOT, 0.55), 0.85 * al, 8, 13)
        px, py = _infall(k, cx, cy)
        _probe(img, px, py, 15, mix(STARC, HOT, 0.30), al, tg)
    q3 = seg(tl, 1.65, 2.25)
    if q3 > 0:
        _pill_c(img, cx, 1680 + dy, "DIHITUNG, BUKAN DIKARANG", font(FS, 29),
                mix(accent, INK, 0.10), esmooth(q3) * al, dot=True)


def sc_bh_what(img, d, sc, tl, dur, tg, accent, al, dy):
    """Apa itu lubang hitam: bintang raksasa runtuh, cahaya tak bisa lepas."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    _stars(img, tg, 0.45 * al, n=14, y0=560, y1=760)
    # kiri: bintang raksasa menyusut jadi titik padat
    cx0, cy0 = 292, 830 + dy
    q = esmooth(seg(tl, 0.20, 1.45))
    if q > 0:
        rr = 118 - 92 * q
        _glow_round(img, cx0, cy0, rr * 1.9, HOT_L, (0.62 - 0.30 * q) * al, layers=3)
        for k in range(8):
            ang = k * math.pi / 4 + 0.2
            L = rr * (1.28 + 0.16 * math.sin(tg * 2.2 + k))
            line_on(img, (cx0 + rr * 0.72 * math.cos(ang), cy0 + rr * 0.72 * math.sin(ang)),
                    (cx0 + L * math.cos(ang), cy0 + L * math.sin(ang)),
                    mix(HOT_L, WHITE, 0.20), 5, al * (0.55 - 0.35 * q))
        ell(img, cx0 - rr, cy0 - rr, cx0 + rr, cy0 + rr, fill=mix(STARC, WHITE, 0.22), alpha=al)
    for j in range(3):
        u = seg(tl, 0.85 + j * 0.30, 1.55 + j * 0.30)
        if u <= 0:
            continue
        ring_on(img, cx0, cy0, 34 + 130 * (1 - esmooth(u)), mix(HOT, INK, 0.30), 5, al * (1 - u) * 0.8)
    if q > 0.75:
        _hole(img, cx0, cy0, 32, al, tg, halo=True)
    a1 = al * clamp(seg(tl, 0.55, 1.05))
    paste_r(img, 110, cy0 + 236, "bintang raksasa", font(FM, 26), MUTED, a1)
    paste_r(img, 110, cy0 + 282, "runtuh & dipadatkan", font(FM, 26), MUTED, al * clamp(seg(tl, 1.05, 1.55)))
    # kanan: cahaya dibelokkan masuk — makin dekat makin tajam
    q2 = esmooth(seg(tl, 1.55, 2.55))
    if q2 > 0:
        hx, hy = 838, 830 + dy
        _hole(img, hx, hy, 56, al, tg, halo=True)
        n = 34
        full = [(660 + 178 * (i / n), 1180 - 350 * ((i / n) ** 2.0)) for i in range(n + 1)]
        keep = full[:max(2, int((n + 1) * q2))]
        path_on(img, keep, mix(HOT, WHITE, 0.22), 6, al)
        _probe(img, keep[-1][0], keep[-1][1], 10, mix(HOT_L, HOT, 0.4), al, tg)
        a2 = al * clamp(seg(tl, 2.1, 2.6))
        paste_r(img, 610, 1228 + dy, "cahaya pun tak bisa lepas", font(FM, 26), MUTED, a2)
    q3 = seg(tl, 2.75, 3.3)
    if q3 > 0:
        _pill_c(img, 540, 1660 + dy, "BUKAN LUBANG, TAPI SANGAT PADAT", font(FS, 28),
                mix(accent, INK, 0.10), esmooth(q3) * al, dot=True)


def sc_bh_horizon(img, d, sc, tl, dur, tg, accent, al, dy):
    """Garis batas: di luar masih bisa kembali, di dalam tidak ada jalan pulang."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    _stars(img, tg, 0.4 * al, n=14, y0=540, y1=740)
    cx, cy = 540, 1050 + dy
    rh = 238
    _disk(img, cx, cy, 152, al * 0.95, tg, n=36, speed=1.3, inner=0.42, tilt=0.30)
    _hole(img, cx, cy, 62, al, tg, halo=True)
    ring_on(img, cx, cy, rh, mix(accent, INK, 0.32), 6, 0.8 * al)
    ring_on(img, cx, cy, rh + 13 + amb(tg, 0.2) * 6, mix(accent, WHITE, 0.45), 2, 0.34 * al)
    # orbit aman di luar batas
    angA = tg * 0.85
    pA = [(cx + 346 * math.cos(angA - 0.075 * j), cy + 346 * math.sin(angA - 0.075 * j) * 0.52)
          for j in range(10)]
    trail_on(img, pA, mix(GREEN, WHITE, 0.15), 0.85 * al, 8, 10)
    _probe(img, pA[-1][0], pA[-1][1], 13, mix(GREEN, INK, 0.05), al, tg)
    # satu titik menembus batas lalu lenyap
    k = clamp(seg(tl, 1.60, 3.40))
    if k > 0:
        u = k
        rk = 346 - 214 * esmooth(u)
        angB = 2.05 - 0.55 * u
        bx, by = cx + rk * math.cos(angB), cy + rk * math.sin(angB) * 0.55
        aB = al * (1 - 0.92 * clamp(seg(tl, 2.75, 3.3)))
        if rk > rh:
            trail_on(img, [(cx + (rk + 26 * (1 - j / 9.0)) * math.cos(angB - 0.06 * j),
                            cy + (rk + 26 * (1 - j / 9.0)) * math.sin(angB - 0.06 * j) * 0.55)
                           for j in range(10)], mix(HOT, WHITE, 0.2), aB * 0.8, 7, 10)
        else:
            ring_on(img, cx, cy, rh, HOT, 7, aB * 0.5)
        _probe(img, bx, by, 12, mix(STARC, HOT, 0.5), aB, tg)
    q = esmooth(seg(tl, 2.0, 2.5))
    _pill_c(img, cx, 1448 + dy, "DI LUAR BATAS — MASIH BISA KEMBALI", font(FS, 27),
            mix(GREEN, INK, 0.12), q * al)
    q2 = esmooth(seg(tl, 2.5, 3.0))
    _pill_c(img, cx, 1530 + dy, "DI DALAM — TIDAK ADA JALAN PULANG", font(FS, 27),
            mix(accent, INK, 0.10), q2 * al)
    q3 = seg(tl, 3.35, 3.85)
    if q3 > 0:
        paste_c(img, cx, 1650 + dy, "sebelum batas: masih bisa berbalik", font(FM, 25), MUTED, esmooth(q3) * al)


def sc_bh_outside(img, d, sc, tl, dur, tg, accent, al, dy):
    """Dilihat dari jauh: tick waktu makin rapat = waktu makin lambat, lalu memudar."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    _stars(img, tg, 0.35 * al, n=12, y0=560, y1=700)
    y = 1010 + dy
    x0, x1 = 132, 838
    hx, hy = 906, y
    line_on(img, (x0, y), (x1, y), mix(MUTED, WHITE, 0.42), 5, 0.85 * al)
    _hole(img, hx, hy, 46, al, tg, halo=True)
    # tick waktu: jarak makin rapat menuju batas (jam melambat bagi pengamat jauh)
    for i in range(15):
        u = (i + 1) / 15.0
        px = x0 + (x1 - x0) * (1 - math.exp(-3.1 * u))
        ah = 0.95 * al * (1 - 0.40 * u)
        line_on(img, (px, y - 18), (px, y - 66), mix(accent, INK, 0.06), 6, ah)
    paste_r(img, x0, y + 48, "tiap garis = satu detik; makin rapat berarti makin lambat", font(FM, 24), MUTED, 0.95 * al)
    # titik yang jatuh: makin lambat, memerah, lalu memudar
    k = clamp(seg(tl, 0.45, 3.5))
    p = 1 - math.exp(-3.1 * k)
    mpx = x0 + (x1 - x0) * p
    mcol = mix(STARC, RED, clamp(seg(k, 0.30, 0.95)))
    malpha = al * (1 - 0.92 * clamp(seg(k, 0.72, 1.0)))
    trail_on(img, [(x0 + (x1 - x0) * (1 - math.exp(-3.1 * max(0.0, k - 0.05 * j))) , y)
                   for j in range(11)], mix(mcol, WHITE, 0.25), malpha * 0.7, 7, 11)
    _probe(img, mpx, y, 13, mcol, malpha, tg)
    a1 = al * clamp(seg(tl, 1.5, 2.0))
    paste_r(img, 132, 1236 + dy, "dari jauh: melambat, memerah, memudar", font(FM, 25), MUTED, a1)
    paste_r(img, 132, 1284 + dy, "dan tidak pernah terlihat masuk", font(FM, 25), MUTED, al * clamp(seg(tl, 2.0, 2.5)))
    q = seg(tl, 2.7, 3.2)
    if q > 0:
        _pill_c(img, 540, 1640 + dy, "YANG JATUH TIDAK MERASA ANEH", font(FS, 28),
                mix(accent, INK, 0.10), esmooth(q) * al, dot=True)


def sc_bh_spaghet(img, d, sc, tl, dur, tg, accent, al, dy):
    """Efek spageti: tarikan di kaki lebih kuat, tubuh memanjang seperti mie."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    _stars(img, tg, 0.4 * al, n=14, y0=560, y1=740)
    hx, hy = 828, 1152 + dy
    _hole(img, hx, hy, 70, al, tg, halo=True)
    # tubuh: kepala di ujung atas, kaki menghadap lubang — diregangkan makin panjang
    k = esmooth(seg(tl, 0.35, 2.6))
    cxb = 396
    yfeet = 1178 + dy
    L = 280 + 240 * k
    n = 46
    ytop = yfeet - L
    for i in range(n):
        u = i / (n - 1)
        y = ytop + L * u
        rr = (27 - 12 * k) * (1 - 0.70 * u) + 2.6
        x = cxb + drift(tg, 0.17, 3.2, i * 0.34) * (0.35 + 1.15 * k) * (0.25 + u)
        col = mix(STARC, mix(HOT, RED, 0.22 * u), 0.24 + 0.62 * u)
        ell(img, x - rr, y - rr, x + rr, y + rr, fill=col, alpha=al)
    hr = 32 - 5 * k
    hcy = ytop - hr - 6
    ell(img, cxb - hr, hcy - hr, cxb + hr, hcy + hr, fill=mix(STARC, WHITE, 0.12),
        outline=mix(HOT, INK, 0.28), width=3, alpha=al)
    paste_r(img, cxb + hr + 20, hcy, "kepala", font(FM, 24), MUTED, al * clamp(seg(tl, 0.7, 1.1)))
    paste_r(img, cxb + 44, yfeet - 6, "kaki", font(FM, 24), MUTED, al * clamp(seg(tl, 0.9, 1.3)))
    # panah: tarikan kaki (dekat lubang) jauh lebih kuat daripada kepala
    axf = cxb + 296
    line_on(img, (axf - 40, 1232 + dy), (hx - 156, hy - 46), mix(HOT, INK, 0.16), 10, al * 0.92)
    line_on(img, (hx - 156, hy - 46), (hx - 208, hy - 96), mix(HOT, INK, 0.16), 10, al * 0.92)
    line_on(img, (hx - 156, hy - 46), (hx - 226, hy - 22), mix(HOT, INK, 0.16), 10, al * 0.92)
    axh = cxb - 104
    line_on(img, (axh, hcy + 150), (axh, hcy - 26), mix(accent, INK, 0.12), 7, al * 0.9)
    line_on(img, (axh, hcy - 26), (axh - 18, hcy + 6), mix(accent, INK, 0.12), 7, al * 0.9)
    line_on(img, (axh, hcy - 26), (axh + 18, hcy + 6), mix(accent, INK, 0.12), 7, al * 0.9)
    a1 = al * clamp(seg(tl, 0.9, 1.4))
    paste_r(img, 150, 1300 + dy, "di kaki, tarikan lebih kuat", font(FM, 25), MUTED, a1)
    paste_c(img, 540, 1470 + dy, "tubuh memanjang seperti mie", font(FM, 26), MUTED,
            al * clamp(seg(tl, 1.4, 1.9)))
    q = seg(tl, 2.05, 2.45)
    if q > 0:
        _pill_c(img, 540, 1600 + dy, "INI DISEBUT EFEK SPAGETI", font(FS, 28),
                mix(accent, INK, 0.10), esmooth(q) * al, dot=True)
    q2 = seg(tl, 2.6, 3.0)
    if q2 > 0:
        _pill_c(img, 540, 1690 + dy, "DI PUSATNYA: SINGULARITAS, MASIH MISTERI", font(FS, 25),
                mix(accent, INK, 0.22), esmooth(q2) * al)


def sc_bh_inside(img, d, sc, tl, dur, tg, accent, al, dy):
    """Di pusatnya: singularitas — tempat hukum fisika yang kita tahu berhenti berlaku."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    _stars(img, tg, 0.5 * al, n=18, y0=540, y1=800)
    cx, cy = 540, 962 + dy
    _disk(img, cx, cy, 300, al, tg, n=40, speed=1.1, inner=0.50)
    _hole(img, cx, cy, 142, al, tg)
    q = seg(tl, 0.35, 1.15)
    if q > 0:
        paste_c(img, cx, cy - 4, "?", font(FB, 140), mix(HOT_L, WHITE, 0.30), esmooth(q) * al)
    # lingkaran kecil di pusat: titik yang dipadatkan
    k = esmooth(seg(tl, 1.3, 2.5))
    if k > 0:
        r_in = 26 - 20 * k
        ring_on(img, cx, cy, 92 - 58 * k, mix(HOT_L, WHITE, 0.35), 3, (1 - k) * 0.7 * al)
        dot_on(img, cx, cy + 120 * (1 - k), r_in, mix(VOID, INK, 0.4), al)
        paste_c(img, cx, cy + 268, "titik pusat: kerapatan tak terbatas", font(FM, 25), MUTED, k * al)
    q2 = seg(tl, 2.5, 3.0)
    if q2 > 0:
        _pill_c(img, cx, 1660 + dy, "BELUM ADA YANG BISA MELIHATNYA", font(FS, 28),
                mix(accent, INK, 0.10), esmooth(q2) * al, dot=True)


def sc_bh_safe(img, d, sc, tl, dur, tg, accent, al, dy):
    """Bumi aman: lubang hitam bukan penyedot, dan yang terdekat sangat jauh."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    _stars(img, tg, 0.45 * al, n=18, y0=540, y1=760)
    cx, cy = 540, 952 + dy
    _hole(img, cx, cy, 76, al, tg, halo=True)
    ring_on(img, cx, cy, 322, mix(MUTED, WHITE, 0.46), 3, 0.55 * al, squash=0.40)
    ang = tg * 0.5 + 0.7
    ex = cx + 322 * math.cos(ang)
    ey = cy + 322 * 0.40 * math.sin(ang)
    trail_on(img, [(cx + 322 * math.cos(ang - 0.06 * j), cy + 322 * 0.40 * math.sin(ang - 0.06 * j))
                   for j in range(10)], mix(BLUE, WHITE, 0.30), 0.7 * al, 6, 10)
    _earth(img, ex, ey, 30, al, tg)
    a1 = al * clamp(seg(tl, 0.9, 1.4))
    paste_c(img, 540, 1232 + dy, "gravitasinya sama seperti benda langit biasa", font(FM, 25), MUTED, a1)
    paste_c(img, 540, 1280 + dy, "Matahari terlalu ringan untuk jadi lubang hitam", font(FM, 25), MUTED,
            al * clamp(seg(tl, 1.4, 1.9)))
    # penggaris jarak: Bumi -> lubang hitam terdekat
    q = esmooth(seg(tl, 1.7, 2.6))
    if q > 0:
        yr = 1580 + dy
        line_on(img, (150, yr), (150 + 780 * q, yr), mix(accent, INK, 0.22), 6, al * 0.9)
        _earth(img, 150, yr - 54, 22, al, tg)
        dot_on(img, 150 + 780 * q, yr, 16, mix(accent, INK, 0.12), al)
        kk = esmooth(seg(tg, 1.7, 2.6))
        angka = f"{int(round(1500 * kk)):,}".replace(",", "\u00a0").replace(",", ".")
        paste_c(img, 540, 1392 + dy, angka.replace("\u00a0", "."), font(FB, 62),
                mix(accent, INK, 0.10), al)
        paste_c(img, 540, 1452 + dy, "tahun cahaya ke lubang hitam terdekat", font(FM, 25), MUTED, al * q)
    q2 = seg(tl, 2.75, 3.25)
    if q2 > 0:
        _pill_c(img, 540, 1650 + dy, "BUMI TIDAK AKAN TERTELAN", font(FS, 28),
                mix(accent, INK, 0.10), esmooth(q2) * al, dot=True)

VISUALS.update({
    "intro_bh": sc_intro_bh,
    "bh_what": sc_bh_what,
    "bh_horizon": sc_bh_horizon,
    "bh_outside": sc_bh_outside,
    "bh_spaghet": sc_bh_spaghet,
    "bh_inside": sc_bh_inside,
    "bh_safe": sc_bh_safe,
})

# ---------- Ep20: Kenapa Indonesia belum maju? ----------
def _capsule(img, p0, p1, w, color, alpha=1.0):
    """Bentuk lonjong (pulau sederhana): garis tebal dengan ujung membulat."""
    line_on(img, p0, p1, color, w, alpha)
    dot_on(img, p0[0], p0[1], w / 2.0, color, alpha)
    dot_on(img, p1[0], p1[1], w / 2.0, color, alpha)


def _map_id(img, x0, y0, s, alpha, color, accent, tg=0.0, res=None):
    """Siluet kepulauan Indonesia (stilir) + titik sumber daya berdenyut."""
    def P(x, y):
        return (x0 + x * s, y0 + y * s)

    _capsule(img, P(168, 58), P(44, 224), 74 * s, color, alpha)                 # Sumatra
    _capsule(img, P(214, 318), P(452, 350), 40 * s, color, alpha)               # Jawa
    _capsule(img, P(302, 138), P(432, 212), 150 * s, color, alpha)              # Kalimantan
    _capsule(img, P(468, 132), P(498, 244), 52 * s, color, alpha)               # Sulawesi (badan)
    _capsule(img, P(500, 190), P(566, 236), 34 * s, color, alpha)               # Sulawesi (lengan)
    _capsule(img, P(638, 176), P(788, 232), 112 * s, color, alpha)              # Papua
    for (bx, by) in ((492, 352), (518, 355), (542, 358)):                       # Bali & Nusa Tenggara
        dot_on(img, P(bx, by)[0], P(bx, by)[1], 9 * s, color, alpha)
    if res:
        for i, (rx, ry, lab) in enumerate(res):
            px, py = P(rx, ry)
            a = alpha * (0.55 + 0.45 * abs(math.sin(tg * 1.1 + i)))
            dot_on(img, px, py, (11 + 3 * math.sin(tg * 1.6 + i)) * max(0.6, s), accent, a)
            dot_on(img, px, py, 26 * max(0.6, s), accent, a * 0.18)
            if lab:
                paste_c(img, px, py - 34 * max(0.6, s), lab, font(FS, 22), mix(accent, INK, 0.25), a)


def _arrow_r(img, x0, y, x1, color, alpha, w=7):
    """Panah ke kanan sederhana."""
    line_on(img, (x0, y), (x1, y), color, w, alpha)
    line_on(img, (x1 - 22, y - 15), (x1, y), color, w, alpha)
    line_on(img, (x1 - 22, y + 15), (x1, y), color, w, alpha)


def _vchain(img, cx, y, items, alpha, accent, w=286, h=168, tg=0.0):
    """Rantai nilai: kotak berisi tahap + nilai tambah makin besar ke kanan."""
    n = len(items)
    gap = 34
    x0 = cx - (n * w + (n - 1) * gap) / 2.0
    for i, (judul, ket, ka) in enumerate(items):
        bx = x0 + i * (w + gap)
        k = ka
        rrect_on(img, bx, y - h / 2, bx + w, y + h / 2, 26, mix(WHITE, accent, 0.05 + 0.10 * i),
                 alpha, outline=mix(accent, WHITE, 0.35), width=3)
        paste_c(img, bx + w / 2, y - 26, judul, font(FS, 27), mix(accent, INK, 0.05 + 0.08 * i), alpha * k)
        paste_c(img, bx + w / 2, y + 30, ket, font(FM, 21), MUTED, alpha * k)
        if i < n - 1:
            _arrow_r(img, bx + w + 8, y, bx + w + gap - 8, mix(accent, INK, 0.30), alpha * 0.9, 6)
            u = (tg * 0.55 + i * 0.5) % 1.0
            dot_on(img, bx + w + 10 + (gap - 20) * u, y, 6.5, mix(accent, INK, 0.12), alpha * 0.9)


def _bar_frac(img, x0, x1, y, frac, color, alpha, label="", sub="", hgt=34):
    """Batang porsi (0..1) dengan label persen."""
    rrect_on(img, x0, y - hgt / 2, x1, y + hgt / 2, hgt / 2, mix(color, WHITE, 0.86), alpha)
    w = (x1 - x0) * clamp(frac)
    if w > 4:
        rrect_on(img, x0, y - hgt / 2, x0 + w, y + hgt / 2, hgt / 2, color, alpha)
    if label:
        paste_c(img, x0 + w / 2, y, label, font(FB, 26), WHITE, alpha) if w > 130 else \
            paste_r(img, x0 + w + 18, y, label, font(FB, 30), mix(color, INK, 0.10), alpha)
    if sub:
        paste_c(img, (x0 + x1) / 2, y + hgt / 2 + 34, sub, font(FM, 23), MUTED, alpha)


def _bars_year(img, x0, y0, x1, y1, bars, alpha, accent, target=None, tg=0.0, t0=0.3, t1=1.6,
               vmax=None):
    """Grafik batang antar-tahun dengan garis target putus-putus (angka di dalam batang)."""
    base = y1
    vmax = vmax or max([b[1] for b in bars] + ([target] if target else [])) * 1.18
    line_on(img, (x0 - 14, base), (x1 + 14, base), mix(MUTED, WHITE, 0.35), 3, alpha * 0.9)
    n = len(bars)
    slot = (x1 - x0) / n
    bw = slot * 0.52
    for i, (lab, val, col) in enumerate(bars):
        cx = x0 + slot * (i + 0.5)
        k = esmooth(seg(tg, t0 + i * 0.30, t1 + i * 0.30))
        hh = (base - y0) * (val / vmax) * k
        if hh > 2:
            rrect_on(img, cx - bw / 2, base - hh, cx + bw / 2, base, min(14, bw / 3), col, alpha * 0.92)
        paste_c(img, cx, base + 40, lab, font(FS, 26), mix(col, INK, 0.20), alpha)
        if k > 0.72 and hh > 90:
            vv = int(round(val * esmooth(seg(tg, t0 + i * 0.30 + 0.25, t1 + i * 0.30 + 0.25))))
            paste_c(img, cx, base - hh + 40, f"{vv}%", font(FB, 34), WHITE, alpha)
    if target:
        ty = base - (base - y0) * (target / vmax)
        line_on(img, (x0 - 24, ty), (x1 + 24, ty), mix(accent, INK, 0.25), 3, alpha * 0.85, dash=18)
        paste_r(img, x1 + 32, ty - 30, f"target: {target}%", font(FM, 23), MUTED, alpha)
        dot_on(img, x1 + 34 + 6 * math.sin(tg * 2.4), ty, 7, mix(accent, INK, 0.15), alpha * 0.9)


def _scale_cmp(img, x0, x1, y, items, alpha, tg, t0=0.4, t1=1.5, lo=300, hi=600):
    """Skala nilai (mis. skor PISA) dengan penanda yang muncul berurutan."""
    line_on(img, (x0, y), (x1, y), mix(MUTED, WHITE, 0.35), 4, alpha * 0.85)
    for v in range(lo, hi + 1, 50):
        px = x0 + (x1 - x0) * (v - lo) / (hi - lo)
        line_on(img, (px, y - 10), (px, y + 10), mix(MUTED, WHITE, 0.30), 3, alpha * 0.8)
        paste_c(img, px, y + 38, str(v), font(FM, 21), MUTED, alpha * 0.9)
    for i, (lab, val, col, up) in enumerate(items):
        px = x0 + (x1 - x0) * (val - lo) / (hi - lo)
        k = esmooth(seg(tg, t0 + i * 0.42, t1 + i * 0.42))
        if k <= 0:
            continue
        ty = y - 96 - (40 if up else 0)
        dot_on(img, px, y, 13, col, alpha * k)
        if i == 0:
            ring_on(img, px, y, 20 + 9 * math.sin(tg * 2.2), col, 4, alpha * k * 0.85)
        line_on(img, (px, y), (px, ty + 24), mix(col, INK, 0.3), 3, alpha * k * 0.8)
        paste_c(img, px, ty, f"{lab} {val}", font(FS, 25), mix(col, INK, 0.15), alpha * k)


def _people_grid(img, cx, cy, alpha, accent, n=100, informal=60, tg=0.0, t0=0.3, t1=2.0, cols=10):
    """Grid 100 orang: sebagian disorot (informal). Menyorot berurutan + berdenyut."""
    size = 30
    gap = 12
    tot = cols * size + (cols - 1) * gap
    x0 = cx - tot / 2.0
    y0 = cy - tot / 2.0
    k = esmooth(seg(tg, t0, t1))
    hit = int(round(n * (informal / n) * k))
    for i in range(n):
        r, c = divmod(i, cols)
        px = x0 + c * (size + gap) + size / 2
        py = y0 + r * (size + gap) + size / 2
        on = (i % 10) * 7 + (i // 10) if i < hit else -1
        if i < hit:
            a = alpha * (0.55 + 0.45 * abs(math.sin(tg * 1.5 + i * 0.35)))
            dot_on(img, px, py, 9.5, accent, a)
        else:
            dot_on(img, px, py, 9.5, mix(MUTED, WHITE, 0.55), alpha * 0.85)
    # kolom sorot menyapu dari kiri ke kanan (menjaga adegan tetap hidup)
    sw = ((tg * 0.22) % 1.0) * tot
    rrect_on(img, x0 + sw - 34, y0 - 12, x0 + sw + 34, y0 + tot + 12, 24,
             mix(accent, WHITE, 0.72), alpha * 0.55)
    return x0, y0, tot


def _gauge(img, cx, cy, r, frac, alpha, accent, label="", caption="", tg=0.0, t0=0.3, t1=1.6,
           label_size=54):
    """Setengah lingkaran penunjuk (0..1) dengan jarum yang bergerak halus."""
    ring_on(img, cx, cy, r, mix(MUTED, WHITE, 0.60), int(14), alpha * 0.9)
    k = esmooth(seg(tg, t0, t1))
    ang = math.pi * (1 - frac * k) + 0.014 * math.sin(tg * 2.6)
    for i in range(46):
        u = i / 45.0
        a2 = math.pi * (1 - frac * u)
        line_on(img, (cx + (r - 9) * math.cos(a2), cy - (r - 9) * math.sin(a2)),
                (cx + (r + 9) * math.cos(a2), cy - (r + 9) * math.sin(a2)),
                accent, 5, alpha * 0.85)
    line_on(img, (cx, cy), (cx + (r - 30) * math.cos(ang), cy - (r - 30) * math.sin(ang)),
            mix(accent, INK, 0.25), 9, alpha)
    dot_on(img, cx, cy, 13, mix(accent, INK, 0.20), alpha)
    if label:
        paste_c(img, cx, cy - 40, label, font(FB, label_size), mix(accent, INK, 0.05), alpha)
    if caption:
        paste_c(img, cx, cy + 62, caption, font(FM, 24), MUTED, alpha)


def _ladder(img, x0, y0, w, tiers, mark, alpha, accent, tg, t0=0.4, t1=1.6):
    """Tangga kelas pendapatan: penanda naik satu tingkat."""
    h, g = 92, 16
    for i, lab in enumerate(tiers):
        y = y0 + (len(tiers) - 1 - i) * (h + g)
        filled = (i == mark)
        k = esmooth(seg(tg, t0 + (len(tiers) - 1 - i) * 0.16, t1 + (len(tiers) - 1 - i) * 0.16))
        rrect_on(img, x0 + i * 26, y, x0 + w + i * 26, y + h, 24,
                 mix(WHITE, accent, 0.26) if filled else mix(WHITE, accent, 0.05),
                 alpha * (0.35 + 0.65 * k),
                 outline=mix(accent, WHITE, 0.30), width=3)
        paste_r(img, x0 + i * 26 + 34, y + h / 2, lab, font(FS, 28 if filled else 26),
                mix(accent, INK, 0.05) if filled else MUTED, alpha * (0.4 + 0.6 * k))
    for j in range(7):
        u = ((tg * 0.30 + j * 0.16) % 1.0)
        dot_on(img, x0 + w + mark * 26 + 30, y0 + (1 - u) * (len(tiers) * (h + g)) - 30,
               5.5, mix(accent, WHITE, 0.25), alpha * 0.75 * (0.4 + 0.6 * abs(math.sin(u * math.pi))))
    ymark = y0 + (len(tiers) - 1 - mark) * (h + g) + h / 2
    dot_on(img, x0 + w + mark * 26 - 26, ymark, 15 + 2.5 * math.sin(tg * 2.0), mix(accent, INK, 0.15), alpha)
    line_on(img, (x0 + w + mark * 26 + 34, ymark), (x0 + w + mark * 26 + 34, ymark + 14),
            mix(accent, INK, 0.30), 4, alpha * 0.9)


def sc_intro_idn(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: peta Indonesia + judul pertanyaan besar."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.25 + i * 0.22, 0.95 + i * 0.22))
        if q <= 0:
            continue
        fsz = 108 if i == 0 else 62
        f = font(FB if i == 0 else FS, fsz)
        while tw(l, f) > 920 and fsz > 40:
            fsz -= 6
            f = font(FB if i == 0 else FS, fsz)
        paste_c(img, 540, (560 + i * 104) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q2 = espring(seg(tl, 0.85, 1.75))
    _dots(img, [(210 + (i * 137) % 700 + 16 * math.sin(tg * 0.55 + i),
                 760 + ((i * 91) % 520) + drift(tg, 0.13, 12, i),
                 2.2, mix(accent, WHITE, 0.55), 0.26 * al) for i in range(30)], al)
    _map_id(img, 108 + 5 * math.sin(tg * 0.37), 792 + dy + 7 * math.sin(tg * 0.5), 1.14, al * q2,
            mix(accent, WHITE, 0.42), accent, tg,
            res=[(360, 176, ""), (500, 250, ""), (120, 150, "")])
    q3 = esmooth(seg(tl, 1.75, 2.35))
    if q3 > 0:
        _pill_c(img, 540, 1240 + dy, "SAWIT · BATU BARA · NIKEL · TIMAH", font(FS, 25),
                mix(accent, INK, 0.10), q3 * al, dot=True)
    q4 = esmooth(seg(tl, 2.35, 2.9))
    if q4 > 0:
        paste_c(img, 540, 1420 + dy, "Kaya sumber daya, tapi", font(FM, 27), MUTED, q4 * al)
        paste_c(img, 540, 1470 + dy, "kenapa belum jadi negara maju?", font(FS, 32), mix(accent, INK, 0.08), q4 * al)
    q5 = seg(tl, 2.9, 3.4)
    if q5 > 0:
        _pill_c(img, 540, 1660 + dy, "EMPAT SEBAB UTAMA", font(FS, 28),
                mix(accent, INK, 0.10), esmooth(q5) * al, dot=True)


def sc_id_raw(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 1: masih menjual bahan mentah — nilai tambah kecil."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    y = 800 + dy
    _vchain(img, 540, y, [
        ("BIJI MENTAH", "dijual mentah", esmooth(seg(tl, 0.20, 0.75))),
        ("DIOLAH", "nilai naik", esmooth(seg(tl, 0.75, 1.30))),
        ("BARANG JADI", "paling mahal", esmooth(seg(tl, 1.30, 1.85))),
    ], al, accent)
    q = esmooth(seg(tl, 1.9, 2.5))
    if q > 0:
        _bar_frac(img, 150, 930, 1130 + dy, 0.65, accent, al * q, label="65%",
                  sub="dari ekspor kita masih terkait komoditas")
    q2 = esmooth(seg(tl, 2.5, 3.0))
    if q2 > 0:
        paste_c(img, 540, 1300 + dy, "yang mengolah jadi barang mahal:", font(FM, 26), MUTED, q2 * al)
        paste_c(img, 540, 1352 + dy, "negara lain", font(FS, 34), mix(accent, INK, 0.08), q2 * al)
        # denyut lembut di ujung batang 65% supaya adegan tidak beku
        dot_on(img, 150 + (930 - 150) * 0.65, 1130 + dy, 14 + 3 * math.sin(tg * 3.1), accent, q2 * al * 0.8)
    q3 = seg(tl, 3.0, 3.5)
    if q3 > 0:
        _pill_c(img, 540, 1660 + dy, "NILAI TAMBAHNYA TINGGAL DI LUAR", font(FS, 27),
                mix(accent, INK, 0.10), esmooth(q3) * al, dot=True)


def sc_id_manu(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 2: industri pengolahan menyusut sebelum negara kaya."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    paste_c(img, 540, 640 + dy, "Sumbangan industri pengolahan ke ekonomi", font(FM, 26), MUTED,
            al * esmooth(seg(tl, 0.25, 0.7)))
    _bars_year(img, 200, 780 + dy, 880, 1230 + dy,
               [("2002", 32, mix(accent, INK, 0.10)), ("2014", 21, mix(accent, WHITE, 0.10)),
                ("2024", 19, mix(accent, WHITE, 0.35))],
               al, accent, target=25, tg=tl, t0=0.7, t1=1.7, vmax=38)
    q = esmooth(seg(tl, 2.2, 2.7))
    if q > 0:
        paste_c(img, 540, 1420 + dy, "industri melemah sebelum kita sempat kaya", font(FM, 26), MUTED, q * al)
    q2 = esmooth(seg(tl, 2.75, 3.25))
    if q2 > 0:
        _pill_c(img, 540, 1560 + dy, "MUNCUL SEBELUM SEMPAT KAYA", font(FS, 28),
                mix(accent, INK, 0.10), q2 * al, dot=True)
        paste_c(img, 540, 1640 + dy, "para ekonom menyebutnya: deindustrialisasi dini", font(FM, 23), MUTED, q2 * al)


def sc_id_sdm(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 3: mutu sumber daya manusia (skor PISA)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    paste_c(img, 540, 660 + dy, "Skor matematika PISA 2022", font(FM, 26), MUTED, al * esmooth(seg(tl, 0.2, 0.65)))
    _scale_cmp(img, 160, 920, 1000 + dy, [
        ("Indonesia", 366, accent, False),
        ("Rata-rata OECD", 472, mix(INK, MUTED, 0.25), True),
        ("Singapura", 575, GREEN, True),
    ], al, tl, t0=0.7, t1=1.8, lo=300, hi=600)
    q = esmooth(seg(tl, 2.1, 2.6))
    if q > 0:
        base = 1330 + dy
        paste_c(img, 540, base - 60, "siswa yang mencapai kemampuan minimum", font(FM, 24), MUTED, q * al)
        _bar_frac(img, 200, 880, base + 20, 0.18, accent, al * q, label="18%", hgt=30)
        _bar_frac(img, 200, 880, base + 130, 0.69, mix(INK, MUTED, 0.30), al * q, label="69%", hgt=30)
        paste_r(img, 200, base + 168, "rata-rata OECD", font(FM, 23), MUTED, al * q)
    q2 = seg(tl, 2.75, 3.25)
    if q2 > 0:
        _pill_c(img, 540, 1690 + dy, "SEKOLAH ADALAH KUNCI NAIK KELAS", font(FS, 27),
                mix(accent, INK, 0.10), esmooth(q2) * al, dot=True)


def sc_id_work(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 4: pekerja informal besar -> pajak kecil -> dana pembangunan terbatas."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    _people_grid(img, 540, 800 + dy, al, accent, informal=60, tg=tl, t0=0.3, t1=1.9)
    q = esmooth(seg(tl, 0.9, 1.5))
    if q > 0:
        paste_r(img, 130, 1030 + dy, "60 dari 100 pekerja kita ada di sektor informal", font(FM, 25), MUTED, q * al)
        paste_r(img, 130, 1080 + dy, "jadi tidak membayar pajak penghasilan", font(FM, 25), MUTED,
                al * esmooth(seg(tl, 1.5, 2.0)))
    q2 = esmooth(seg(tl, 2.0, 2.7))
    if q2 > 0:
        _gauge(img, 540, 1320 + dy, 172, 9 / 25.0, al * q2, accent, label="9%",
               caption="pajak yang dipungut negara, dari ukuran ekonomi", tg=tl, t0=2.0, t1=2.7,
               label_size=78)
    q3 = seg(tl, 3.0, 3.5)
    if q3 > 0:
        _pill_c(img, 540, 1660 + dy, "PAJAK KECIL · DANA PEMBANGUNAN KECIL", font(FS, 26),
                mix(accent, INK, 0.10), esmooth(q3) * al, dot=True)


def sc_id_hope(img, d, sc, tl, dur, tg, accent, al, dy):
    """Penutup: bukan takdir — banyak negara naik kelas; kuncinya jelas."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    _ladder(img, 150, 690 + dy, 520,
            ["pendapatan rendah", "menengah bawah", "menengah atas", "pendapatan tinggi"],
            2, al, accent, tl, t0=0.35, t1=1.5)
    q = esmooth(seg(tl, 1.1, 1.7))
    if q > 0:
        paste_r(img, 150, 620 + dy, "Indonesia di sini sejak 2023", font(FM, 24), MUTED, q * al)
        counter_c(img, 836, 1000 + dy, tl, 1.2, 2.2, 0, 34, font(FB, 92), mix(accent, INK, 0.08), al)
        paste_c(img, 836, 1078 + dy, "negara menengah", font(FM, 23), MUTED, q * al)
        paste_c(img, 836, 1120 + dy, "naik kelas sejak 1990", font(FM, 23), MUTED, q * al)
    q2 = esmooth(seg(tl, 2.2, 2.8))
    if q2 > 0:
        paste_c(img, 540, 1400 + dy, "kuncinya: olah bahan mentah di dalam negeri,", font(FM, 26), MUTED, q2 * al)
        paste_c(img, 540, 1450 + dy, "dan naikkan mutu sekolah", font(FM, 26), MUTED, q2 * al)
    q3 = seg(tl, 2.8, 3.3)
    if q3 > 0:
        _pill_c(img, 540, 1660 + dy, "BUKAN TAKDIR, TAPI PILIHAN", font(FS, 28),
                mix(accent, INK, 0.10), esmooth(q3) * al, dot=True)

# ---------- Ep21: Kenapa mimpi terasa nyata? ----------
NIGHT_T = (26, 30, 68)      # langit malam (atas)
NIGHT_B = (86, 72, 138)     # langit malam (bawah)
DAWN_T = (52, 58, 116)
DAWN_B = (240, 176, 108)
STAR_L = (250, 246, 232)
MOONC = (248, 240, 214)

PROF = [(1 - px, py) for (px, py) in [(0.06, 0.36), (0.12, 0.24), (0.22, 0.15), (0.36, 0.10),
        (0.52, 0.10), (0.66, 0.15), (0.78, 0.24), (0.87, 0.36), (0.93, 0.47), (0.95, 0.55),
        (0.91, 0.60), (0.86, 0.62), (0.89, 0.68), (0.86, 0.72), (0.79, 0.74), (0.72, 0.80),
        (0.64, 0.88), (0.52, 0.94), (0.38, 0.93), (0.26, 0.87), (0.15, 0.77), (0.08, 0.62)]]


def _night_panel(img, x0, y0, x1, y1, r, alpha, top=NIGHT_T, bot=NIGHT_B, steps=None):
    """Panel membulat dengan gradasi vertikal (langit malam / fajar)."""
    if alpha <= 0.01:
        return
    bx = _box(img, x0, y0, x1, y1, pad=4)
    X0, Y0, X1b, Y1b = bx
    w, h = X1b - X0, Y1b - Y0
    if w < 4 or h < 4:
        return
    grad = Image.new("RGB", (w, h))
    dd = ImageDraw.Draw(grad)
    for i in range(h):
        u = i / max(1, h - 1)
        c = tuple(int(round(top[k] + (bot[k] - top[k]) * u)) for k in range(3))
        dd.line([(0, i), (w, i)], fill=c)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=S(r), fill=255)
    if alpha < 0.995:
        mask = mask.point(lambda v: int(v * clamp(alpha)))
    img.paste(grad, (X0, Y0), mask)


def _moon(img, cx, cy, r, alpha, sky=None):
    """Bulan sabit dengan kawah samar."""
    if alpha <= 0.01:
        return
    _glow_round(img, cx, cy, r * 1.5, MOONC, 0.22 * alpha, layers=3)
    ell(img, cx - r, cy - r, cx + r, cy + r, fill=MOONC, alpha=alpha)
    ell(img, cx - r * 0.55 - r * 0.62, cy - r * 1.05, cx + r * 1.05 - r * 0.62, cy + r * 1.05,
        fill=sky or mix(NIGHT_T, NIGHT_B, 0.42), alpha=alpha * 0.97)
    for (du, dv, rr) in ((0.20, -0.28, 0.16), (0.34, 0.10, 0.11), (0.10, 0.34, 0.08)):
        ell(img, cx + du * r - rr * r, cy + dv * r - rr * r, cx + du * r + rr * r, cy + dv * r + rr * r,
            fill=mix(MOONC, NIGHT_T, 0.28), alpha=alpha * 0.9)


def _clouds(img, tg, alpha, y0, y1, color, n=3):
    """Awan lembut melayang perlahan di dalam panel malam."""
    if alpha <= 0.01:
        return
    for i in range(n):
        h = (i * 2654435761 + 977) % 4294967296
        w = 150 + (h >> 5) % 130
        y = y0 + ((h >> 13) % 1000) / 1000.0 * (y1 - y0)
        span = 1180 + w
        x = -w + ((h >> 7) % 1000) / 1000.0 * span + tg * (9 + i * 3)
        x = ((x + w) % span) - w
        a = alpha * (0.16 + 0.10 * abs(math.sin(tg * 0.2 + i)))
        ell(img, x, y, x + w, y + w * 0.34, fill=color, alpha=a)
        ell(img, x + w * 0.22, y - w * 0.10, x + w * 0.78, y + w * 0.22, fill=color, alpha=a)
        ell(img, x + w * 0.44, y - w * 0.18, x + w * 0.92, y + w * 0.16, fill=color, alpha=a)


def _zzz(img, cx, cy, alpha, tg, color=STAR_L):
    """Huruf 'z' kecil naik perlahan (tanda orang tidur)."""
    for i in range(3):
        k = (tg * 0.16 + i * 0.33) % 1.0
        a = alpha * (1 - k) * (0.35 + 0.65 * abs(math.sin(tg * 0.6 + i)))
        paste_c(img, cx + 52 * k + 10 * math.sin(tg * 0.9 + i), cy - 120 * k, "z",
                font(FB, 26 + 14 * k), color, a)


def _sleeper(img, cx, cy, s, alpha, line=STAR_L):
    """Siluet orang berbaring (kepala di bantal + selimut)."""
    if alpha <= 0.01:
        return
    ell(img, cx - 176 * s, cy - 6 * s, cx - 60 * s, cy + 62 * s, fill=mix(line, NIGHT_B, 0.35), alpha=alpha * 0.9)
    ell(img, cx - 152 * s, cy + 4 * s, cx - 82 * s, cy + 56 * s, fill=line, alpha=alpha)
    ell(img, cx - 92 * s, cy + 20 * s, cx + 120 * s, cy + 106 * s, fill=line, alpha=alpha)
    ell(img, cx + 40 * s, cy + 44 * s, cx + 150 * s, cy + 96 * s, fill=mix(line, NIGHT_B, 0.20), alpha=alpha)
    line_on(img, (cx - 176 * s, cy + 96 * s), (cx + 150 * s, cy + 96 * s), mix(line, NIGHT_B, 0.55), 4 * s,
            alpha * 0.55)


def _faller(img, cx, cy, s, alpha, rot=0.0):
    """Figur kecil jatuh (untuk mimpi jatuh)."""
    if alpha <= 0.01:
        return
    dot_on(img, cx, cy - 26 * s, 11 * s, mix(STAR_L, HOT, 0.25), alpha)
    rrect_on(img, cx - 9 * s, cy - 16 * s, cx + 9 * s, cy + 20 * s, 8 * s, mix(STAR_L, HOT, 0.35), alpha)
    for (dx, dy, ex, ey) in ((-13, -12, -30, -30), (13, -12, 30, -32), (-11, 20, -22, 40), (11, 20, 24, 42)):
        line_on(img, (cx + dx * s, cy + dy * s), (cx + ex * s, cy + ey * s), mix(STAR_L, HOT, 0.35),
                5 * s, alpha * 0.95)


def _jolt(img, cx, cy, s, alpha, k):
    """Sentakan: garis ledakan + cincin mengembang + tanda seru."""
    if alpha <= 0.01 or k <= 0:
        return
    a = alpha * clamp(1.15 - k)
    r0 = (40 + 150 * esmooth(k)) * s
    ring_on(img, cx, cy, r0, mix(HOT_L, WHITE, 0.25), 6, 0.55 * a)
    for i in range(10):
        ang = i * math.pi / 5 + 0.25
        r1 = r0 * (1.05 + 0.28 * ((i % 3) / 2.0))
        line_on(img, (cx + r0 * 0.85 * math.cos(ang), cy + r0 * 0.85 * math.sin(ang)),
                (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang)), mix(HOT_L, WHITE, 0.15), 5, a)
    ty = cy - (150 + 120 * esmooth(k)) * s
    rrect_on(img, cx - 10 * s, ty - 60 * s, cx + 10 * s, ty - 8 * s, 9 * s, mix(HOT, RED, 0.20), a)
    dot_on(img, cx, ty + 12 * s, 12 * s, mix(HOT, RED, 0.20), a)


def _hypno(img, x0, x1, y0, y1, alpha, accent, tg, prog=1.0, n_blok=4):
    """Hipnogram: kedalaman tidur sepanjang malam + blok REM yang makin panjang."""
    base = y1
    span = x1 - x0
    def _depth(u):
        d = 0.34 + 0.46 * abs(math.sin(u * math.pi * 2.35 + 0.35))
        d *= 0.72 + 0.42 * math.sin(u * math.pi)
        d += 0.06 * math.sin(u * 26.0)
        return clamp(d)

    kurva = [(x0 + span * (i / 120.0), y0 + (y1 - y0) * _depth(i / 120.0)) for i in range(121)]
    keep = int(len(kurva) * clamp(prog, 0.02, 1.0))
    for i in range(6):
        line_on(img, (x0, y0 + (y1 - y0) * (i / 5.0)), (x1, y0 + (y1 - y0) * (i / 5.0)),
                mix(MUTED, WHITE, 0.55), 2, alpha * 0.45, dash=14)
    pts = kurva[:keep]
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], mix(accent, INK, 0.15), 6, alpha * 0.95)
    # blok REM makin panjang menjelang pagi (ciri khas siklus tidur)
    for b in range(n_blok):
        u0 = 0.14 + b * 0.215
        wl = 0.075 + b * 0.030
        xa, xb = x0 + span * u0, x0 + span * (u0 + wl)
        yc = y0 + (y1 - y0) * min(_depth(u0), _depth(u0 + wl)) - 40
        q = esmooth(seg(tg, 0.5 + b * 0.42, 1.1 + b * 0.42))
        if q <= 0:
            continue
        rrect_on(img, xa, yc, xa + (xb - xa) * q, yc + 34, 17,
                 mix(accent, WHITE, 0.08), alpha * 0.95)
        if q > 0.6:
            paste_c(img, xa + (xb - xa) * q / 2, yc + 17, "REM", font(FM, 20),
                    mix(accent, INK, 0.10), alpha * 0.95)
    if prog >= 0.999:
        px, py = kurva[-1]
        dot_on(img, px, py, 12 + 2 * math.sin(tg * 3.0), mix(accent, INK, 0.10), alpha)
    paste_r(img, x0, y1 + 44, "8 jam tidur", font(FM, 23), MUTED, alpha * 0.95)
    paste_r(img, x0, y0 - 46, "fase REM tiap ±90 menit", font(FS, 24), mix(accent, INK, 0.05), alpha * 0.95)


def _eye_rem(img, cx, cy, s, alpha, tg, accent=BLUE):
    """Sepasang mata dengan bola mata bergerak cepat (ciri fase REM)."""
    for sx in (-1, 1):
        ex = cx + sx * 62 * s
        ell(img, ex - 46 * s, cy - 26 * s, ex + 46 * s, cy + 26 * s, fill=WHITE, alpha=alpha,
            outline=mix(INK, MUTED, 0.45), width=3)
        dx = 22 * s * math.sin(tg * 5.2 + sx * 1.1)
        dy = 7 * s * math.sin(tg * 3.7 + sx * 0.6)
        dot_on(img, ex + dx, cy + dy, 13 * s, mix(accent, INK, 0.30), alpha)
        dot_on(img, ex + dx, cy + dy, 6 * s, INK, alpha)


def _brain_head(img, cx, cy, s, alpha, accent, tg, logic=0.22, vis=0.95):
    """Kepala tampak samping + otak: bagian logika meredup, pengolah gambar menyala."""
    K = 620 * s
    bx, by = cx - 0.01 * K, cy - 0.13 * K
    fx, fy, fr = bx - 0.20 * K, by - 0.03 * K, 0.080 * K
    vx, vy, vr = bx + 0.19 * K, by - 0.02 * K, 0.098 * K
    if alpha <= 0.01:
        return (fx, fy, fr), (vx, vy, vr)
    # kepala: siluet profil menghadap kiri (dengan garis tepi supaya jelas)
    pts = [(cx + (px - 0.5) * K, cy + (py - 0.5) * K) for (px, py) in PROF]
    poly_on(img, pts, mix(CREAM, INK, 0.15), alpha * 0.99, outline=mix(CREAM, INK, 0.55), width=5)
    # otak: gumpalan lingkaran + lipatan korteks
    for (du, dv, rr) in ((-0.20, -0.03, 0.100), (-0.09, -0.12, 0.122), (0.04, -0.14, 0.126),
                         (0.17, -0.08, 0.116), (0.21, 0.03, 0.100), (0.06, 0.08, 0.104),
                         (-0.10, 0.07, 0.094)):
        ell(img, bx + (du - rr) * K, by + (dv - rr) * K, bx + (du + rr) * K, by + (dv + rr) * K,
            fill=mix(WHITE, PURPLE, 0.16), outline=mix(PURPLE, INK, 0.40), width=3, alpha=alpha)
    for i in range(5):
        x = bx + (-0.22 + i * 0.11) * K
        for j in range(3):
            y = by + (-0.11 + j * 0.085) * K
            line_on(img, (x - 0.030 * K, y), (x + 0.040 * K, y + 0.030 * K),
                    mix(PURPLE, INK, 0.36), 3, alpha * 0.45)
    # wilayah logika (depan) — meredup
    ell(img, fx - fr, fy - fr * 0.9, fx + fr, fy + fr * 0.9, fill=mix(MUTED, WHITE, 0.30),
        outline=mix(MUTED, INK, 0.20), width=3, alpha=alpha * (0.55 + 0.45 * logic))
    # wilayah gambar & rasa (belakang) — menyala
    _glow_round(img, vx, vy, vr * 2.0, HOT_L, 0.30 * alpha * vis, layers=3)
    ell(img, vx - vr, vy - vr * 0.92, vx + vr, vy + vr * 0.92, fill=mix(HOT, WHITE, 0.20),
        alpha=alpha * (0.45 + 0.55 * vis))
    # tanda wajah + kantuk
    eyx, eyy = cx - 0.405 * K, cy + 0.02 * K
    line_on(img, (eyx - 14 * s, eyy), (eyx + 14 * s, eyy), mix(INK, MUTED, 0.30), 4, alpha * 0.75)
    line_on(img, (eyx - 26 * s, eyy + 20 * s), (eyx + 6 * s, eyy + 20 * s), mix(INK, MUTED, 0.42), 3,
            alpha * 0.5, dash=8)
    return (fx, fy, fr), (vx, vy, vr)

def _level_bar(img, x0, x1, y, frac, color, alpha, label="", hgt=30, pul=0.0):
    rrect_on(img, x0, y - hgt / 2, x1, y + hgt / 2, hgt / 2, mix(color, WHITE, 0.86), alpha)
    w = (x1 - x0) * clamp(frac)
    if w > 4:
        rrect_on(img, x0, y - hgt / 2, x0 + w, y + hgt / 2, hgt / 2, color, alpha)
    if label:
        paste_r(img, x0, y - hgt / 2 - 30, label, font(FM, 24), MUTED, alpha * 0.95)
    if pul > 0:
        dot_on(img, x0 + w, y, 10 + 3 * math.sin(pul * 3.2), mix(color, INK, 0.15), alpha * 0.9)


def _shard(img, cx, cy, w, h, rot, alpha, kind, color):
    """Kartu ingatan kecil berisi coretan sederhana (diputar sedikit)."""
    if alpha <= 0.01:
        return
    W2, H2 = int(S(w)), int(S(h))
    if W2 < 8 or H2 < 8:
        return
    lay = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([0, 0, W2 - 1, H2 - 1], radius=int(W2 * 0.14),
                         fill=mix(WHITE, color, 0.06) + (255,), outline=color + (255,), width=3)
    c = color + (255,)
    if kind == "kopi":
        dd.polygon([(W2 * 0.28, H2 * 0.40), (W2 * 0.72, H2 * 0.40), (W2 * 0.64, H2 * 0.80),
                    (W2 * 0.36, H2 * 0.80)], fill=c)
        dd.arc([W2 * 0.68, H2 * 0.46, W2 * 0.90, H2 * 0.66], -70, 70, fill=c, width=4)
        for i in range(3):
            x = W2 * (0.40 + i * 0.10)
            dd.line([(x, H2 * 0.34), (x + W2 * 0.03, H2 * 0.18)], fill=c, width=3)
    elif kind == "jalan":
        dd.line([(W2 * 0.24, H2 * 0.82), (W2 * 0.34, H2 * 0.20)], fill=c, width=5)
        dd.line([(W2 * 0.76, H2 * 0.82), (W2 * 0.66, H2 * 0.20)], fill=c, width=5)
        for i in range(4):
            y = H2 * (0.28 + i * 0.16)
            dd.line([(W2 * 0.48, y), (W2 * 0.52, y + H2 * 0.06)], fill=c, width=4)
    elif kind == "kucing":
        dd.ellipse([W2 * 0.28, H2 * 0.36, W2 * 0.72, H2 * 0.78], fill=c)
        dd.polygon([(W2 * 0.30, H2 * 0.44), (W2 * 0.38, H2 * 0.18), (W2 * 0.46, H2 * 0.42)], fill=c)
        dd.polygon([(W2 * 0.70, H2 * 0.44), (W2 * 0.62, H2 * 0.18), (W2 * 0.54, H2 * 0.42)], fill=c)
        for sx in (0.40, 0.60):
            dd.ellipse([W2 * sx - 4, H2 * 0.54 - 4, W2 * sx + 4, H2 * 0.54 + 4], fill=mix(WHITE, color, 0.9) + (255,))
    elif kind == "hujan":
        dd.ellipse([W2 * 0.24, H2 * 0.22, W2 * 0.76, H2 * 0.52], fill=c)
        for i in range(4):
            x = W2 * (0.28 + i * 0.15)
            dd.line([(x, H2 * 0.58), (x - W2 * 0.05, H2 * 0.84)], fill=c, width=3)
    elif kind == "rumah":
        dd.polygon([(W2 * 0.20, H2 * 0.48), (W2 * 0.50, H2 * 0.22), (W2 * 0.80, H2 * 0.48)], fill=c)
        dd.rectangle([W2 * 0.30, H2 * 0.48, W2 * 0.70, H2 * 0.80], fill=c)
    else:  # "lampu"
        dd.ellipse([W2 * 0.30, H2 * 0.24, W2 * 0.70, H2 * 0.66], fill=c)
        dd.rectangle([W2 * 0.42, H2 * 0.66, W2 * 0.58, H2 * 0.80], fill=c)
    if abs(rot) > 0.4:
        lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.995:
        a = lay.getchannel("A").point(lambda v: int(v * clamp(alpha)))
        img.paste(lay.convert("RGB"), (int(S(cx) - lay.width / 2), int(S(cy) - lay.height / 2)), a)
    else:
        img.paste(lay, (int(S(cx) - lay.width / 2), int(S(cy) - lay.height / 2)), lay)


def _mixer(img, cx, cy, r, alpha, accent, tg):
    """Pusat pengaduk ingatan: cincin berputar + pusaran."""
    if alpha <= 0.01:
        return
    _glow_round(img, cx, cy, r * 1.35, mix(accent, WHITE, 0.30), 0.24 * alpha, layers=3)
    for i in range(3):
        ring_on(img, cx, cy, r * (0.55 + 0.22 * i), mix(accent, WHITE, 0.30), 3, alpha * (0.5 - 0.12 * i))
    for i in range(26):
        u = i / 26.0
        ang = u * math.tau + tg * (0.9 + 0.25 * math.sin(u * 6.0))
        rr = r * (0.28 + 0.68 * u)
        dot_on(img, cx + rr * math.cos(ang), cy + rr * math.sin(ang) * 0.9,
               2.6 + 3.2 * (1 - u), mix(accent, INK, 0.15 + 0.3 * u), alpha * (0.35 + 0.6 * u))
    ring_on(img, cx, cy, r, mix(accent, INK, 0.10), 7, alpha * 0.9)


def _dissolve(img, cx, cy, s, alpha, k, color):
    """Awan mimpi yang memudar: titik-titik menyebar lalu hilang."""
    if alpha <= 0.01 or k <= 0:
        return
    a0 = alpha * clamp(1 - k * 0.95)
    ell(img, cx - 150 * s, cy - 96 * s, cx + 150 * s, cy + 96 * s, fill=mix(WHITE, color, 0.16),
        alpha=a0 * 0.85, outline=mix(color, WHITE, 0.35), width=3)
    items = []
    for i in range(34):
        h = (i * 40503 + 21) % 4294967296
        fx = ((h >> 7) % 1000) / 1000.0
        fy = ((h >> 17) % 1000) / 1000.0
        du = ((h >> 3) % 1000) / 1000.0
        rr = (1 - fx) * 300 * s * k
        px = cx + (fx - 0.5) * 300 * s + rr * (0.2 + du)
        py = cy + (fy - 0.5) * 190 * s - 220 * s * k * (0.34 + du)
        items.append((px, py, 4.2 - 2.6 * k, color, a0 * (1 - k) * (0.4 + 0.6 * du)))
    _dots(img, items, a0)


def sc_intro_mimpi(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: jendela malam — orang tidur, mimpi jatuh, lalu tersentak."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.20 + i * 0.20, 0.85 + i * 0.20))
        if q <= 0:
            continue
        fsz = 104 if i == 0 else 62
        f = font(FB if i == 0 else FS, fsz)
        while tw(l, f) > 900 and fsz > 38:
            fsz -= 6
            f = font(FB if i == 0 else FS, fsz)
        paste_c(img, 540, (520 + i * 96) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q1 = seg(tl, 0.55, 0.95)
    if q1 > 0:
        _pill_c(img, 540, 680 + dy, "SAINS DI BALIK MIMPI", font(FS, 26), mix(accent, INK, 0.10),
                esmooth(q1) * al, dot=True)
    # panel langit malam
    px0, py0, px1, py1 = 108, 748, 972, 1560
    q2 = esmooth(seg(tl, 0.35, 1.05))
    _night_panel(img, px0, py0, px1, py1, 46, q2 * al, NIGHT_T, NIGHT_B)
    if q2 <= 0.05:
        return
    _stars(img, tg, 0.95 * al * q2, n=34, y0=py0 + 30, y1=py1 - 60, color=STAR_L)
    _clouds(img, tg, 0.55 * al * q2, py0 + 90, py0 + 300, mix(STAR_L, NIGHT_B, 0.55), n=3)
    _moon(img, 826, 880 + dy, 58, q2 * al)
    # mimpi: figur jatuh + jejak, lalu sentakan
    k = clamp(seg(tl, 1.15, 2.55))
    if k > 0:
        fx = 700 - 250 * esmooth(k)
        fy = 900 + 470 * (esmooth(k) ** 1.35)
        trail = [(fx + 26 * j, fy - (34 + 6 * j) * (j / 9.0) - 46 * (j / 9.0) * 0) for j in range(10)]
        trail = [(700 - 250 * esmooth(max(0.0, k - 0.055 * j)), 900 + 470 * (esmooth(max(0.0, k - 0.055 * j)) ** 1.35))
                 for j in range(10)]
        trail_on(img, trail, mix(STAR_L, HOT, 0.40), 0.75 * al * q2, 7, 10)
        _faller(img, fx, fy, 1.28, q2 * al, 0)
    jk = clamp(seg(tl, 2.5, 3.3))
    if jk > 0:
        _jolt(img, 470, 1300 + dy, 1.18, q2 * al, jk)
    _sleeper(img, 300, 1380 + dy, 1.0, q2 * al * clamp(seg(tl, 0.6, 1.2)))
    _zzz(img, 360, 1330 + dy, q2 * al * clamp(seg(tl, 0.8, 1.4)), tg)
    q3 = esmooth(seg(tl, 2.9, 3.45))
    if q3 > 0:
        _pill_c(img, 540, 1668 + dy, "PERNAH MIMPI JATUH? INI SEBABNYA", font(FS, 26),
                mix(accent, INK, 0.10), q3 * al, dot=True)


def sc_rem(img, d, sc, tl, dur, tg, accent, al, dy):
    """Fase REM: siklus 90 menit, mata bergerak cepat, otak justru sibuk."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.20, 0.70))
    if q > 0:
        paste_c(img, 540, 600 + dy, "kedalaman tidur sepanjang malam", font(FM, 26), MUTED, q * al)
        _hypno(img, 150, 930, 700 + dy, 1080 + dy, al * q, accent, tl,
               prog=esmooth(seg(tl, 0.55, 2.9)))
    # dua kartu kecil: mata & otak
    q2 = esmooth(seg(tl, 1.5, 2.0))
    if q2 > 0:
        rrect_on(img, 132, 1210 + dy, 520, 1500 + dy, 34, mix(WHITE, accent, 0.05), al * q2,
                 outline=mix(accent, WHITE, 0.40), width=3)
        paste_c(img, 326, 1268 + dy, "mata bergerak cepat", font(FS, 26), mix(accent, INK, 0.05), al * q2)
        _eye_rem(img, 326, 1382 + dy, 0.86, al * q2, tg, accent)
    q3 = esmooth(seg(tl, 1.9, 2.4))
    if q3 > 0:
        rrect_on(img, 560, 1210 + dy, 948, 1500 + dy, 34, mix(WHITE, accent, 0.05), al * q3,
                 outline=mix(accent, WHITE, 0.40), width=3)
        paste_c(img, 754, 1268 + dy, "otak justru sibuk", font(FS, 26), mix(accent, INK, 0.05), al * q3)
        for i in range(22):
            x = 604 + i * 15.6
            hgt = 26 + 40 * abs(math.sin(i * 0.9 + tg * 2.6))
            rrect_on(img, x - 4.5, 1440 + dy - hgt, x + 4.5, 1440 + dy, 4.5,
                     mix(accent, INK, 0.10), al * q3 * (0.5 + 0.5 * abs(math.sin(i * 0.7 + tg * 1.9))))
    q4 = esmooth(seg(tl, 2.7, 3.2))
    if q4 > 0:
        _pill_c(img, 540, 1660 + dy, "REM MUNCUL TIAP ±90 MENIT", font(FS, 28),
                mix(accent, INK, 0.10), q4 * al, dot=True)


def sc_logic(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kenapa terasa nyata: pemeriksa logika meredup, pengolah gambar menyala."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.25, 0.85))
    if q <= 0:
        return
    # kartu putih besar sebagai panggung gambar otak (kontras jelas)
    rrect_on(img, 118, 612 + dy, 962, 1468 + dy, 44, mix(WHITE, accent, 0.035), al * q,
             outline=mix(accent, WHITE, 0.55), width=3)
    paste_r(img, 168, 668 + dy, "otak saat kamu bermimpi", font(FS, 25), mix(accent, INK, 0.10), al * q)
    logic = 0.18 + 0.10 * abs(math.sin(tg * 0.9))
    (fx, fy, fr), (vx, vy, vr) = _brain_head(img, 540, 1010 + dy, 1.14, al * q, accent, tg,
                                             logic=logic, vis=0.95)
    qa = esmooth(seg(tl, 1.15, 1.6))
    if qa > 0:
        line_on(img, (fx - fr * 0.4, fy + fr * 0.9), (250, 1392 + dy), mix(MUTED, WHITE, 0.30), 3,
                al * qa * 0.9, dash=14)
        paste_r(img, 168, 1420 + dy, "pemeriksa logika: meredup", font(FS, 26),
                mix(MUTED, INK, 0.10), al * qa)
        line_on(img, (vx + vr * 0.5, vy + vr * 0.9), (905, 1116 + dy), mix(HOT, INK, 0.25), 3,
                al * qa * 0.9, dash=14)
        paste_r(img, 470, 1128 + dy, "pengolah gambar & rasa:", font(FS, 25), mix(HOT, INK, 0.10), al * qa)
        paste_r(img, 470, 1166 + dy, "bekerja penuh", font(FM, 24), MUTED, al * qa)
    q2 = esmooth(seg(tl, 1.95, 2.45))
    if q2 > 0:
        _level_bar(img, 380, 930, 1560 + dy, logic, mix(MUTED, INK, 0.10), al * q2, pul=tg)
        paste_r(img, 380, 1526 + dy, "logika", font(FM, 24), MUTED, al * q2)
        _level_bar(img, 380, 930, 1662 + dy, 0.95, mix(HOT, INK, 0.05), al * q2, pul=tg)
        paste_r(img, 380, 1628 + dy, "gambar & rasa", font(FM, 24), MUTED, al * q2)
    q3 = esmooth(seg(tl, 2.7, 3.2))
    if q3 > 0:
        paste_c(img, 540, 1770 + dy, "karena itu mimpi aneh terasa wajar", font(FS, 26),
                mix(accent, INK, 0.08), q3 * al)


def sc_memory(img, d, sc, tl, dur, tg, accent, al, dy):
    """Mimpi dirajut dari ingatan: potongan hari diaduk jadi cerita baru."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    shards = [("kopi", 210, 880, -9), ("jalan", 190, 1120, 7), ("kucing", 250, 1350, -6),
              ("hujan", 470, 800, 5)]
    kinds = ("kopi", "jalan", "kucing", "hujan", "rumah", "lampu")
    k = esmooth(seg(tl, 0.35, 2.6))
    for i, (kind, x, y, rot) in enumerate(shards):
        q = esmooth(seg(tl, 0.30 + i * 0.16, 0.80 + i * 0.16))
        if q <= 0:
            continue
        # kartu bergerak menuju pengaduk saat adegan berjalan
        tx = x + (620 - x) * k * 0.55
        ty = y + (1030 - y) * k * 0.55
        _shard(img, tx, ty - 6 * math.sin(tg * 0.9 + i), 132, 132,
               rot + 10 * math.sin(tg * 0.7 + i) * (1 - k), al * q, kind,
               mix(accent, WHITE, 0.25 + 0.12 * i))
    q2 = esmooth(seg(tl, 0.9, 1.5))
    if q2 > 0:
        _mixer(img, 660, 1040 + dy, 172, al * q2, accent, tg)
        paste_c(img, 660, 1040 + dy, "ingatan", font(FS, 25), mix(WHITE, STAR_L, 0.35), al * q2 * 0.95)
    # hasil campuran: kartu "kucing di jalan saat hujan"
    q3 = esmooth(seg(tl, 2.1, 2.7))
    if q3 > 0:
        cx3, cy3 = 820, 1330 + dy
        k2 = 1 + 0.06 * math.sin(tg * 1.6)
        _glow_round(img, cx3, cy3, 130 * k2, mix(accent, WHITE, 0.35), 0.28 * al * q3, layers=3)
        _shard(img, cx3, cy3, 190, 190, 6 + 4 * math.sin(tg * 0.8), al * q3, "kucing",
               mix(HOT, WHITE, 0.25))
        for i in range(4):
            x = cx3 - 52 + i * 34
            line_on(img, (x, cy3 + 58), (x - 10, cy3 + 88), mix(BLUE, WHITE, 0.25), 4, al * q3 * 0.9)
        paste_c(img, cx3, cy3 + 128, "kucing", font(FM, 22), MUTED, al * q3)
        paste_c(img, 540, 1620 + dy, "potongan hari dicampur jadi cerita baru", font(FM, 25), MUTED, al * q3)
    q4 = esmooth(seg(tl, 2.8, 3.3))
    if q4 > 0:
        _pill_c(img, 540, 1690 + dy, "BAHAN MIMPINYA: HARI-HARIMU", font(FS, 27),
                mix(accent, INK, 0.10), q4 * al, dot=True)


def sc_forget(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kenapa cepat lupa: bahan kimia penyimpan ingatan masih rendah + fungsi mimpi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    k = clamp(seg(tl, 0.5, 3.0))
    q = esmooth(seg(tl, 0.25, 0.8))
    if q > 0:
        _dissolve(img, 470, 900 + dy, 1.15, al * q, k, accent)
        # isi mimpi yang ikut pudar
        for i, kind in enumerate(("rumah", "lampu", "jalan")):
            a = al * q * clamp(1 - k * 1.1) * (0.9 - 0.2 * i)
            if a > 0.02:
                _shard(img, 470 + (i - 1) * 92, 900 + dy, 104, 104, -6 + i * 6, a, kind, mix(accent, WHITE, 0.30))
        # jam weker: pemicu noradrenalin naik
        ax, ay = 830, 900 + dy
        shake = 5 * math.sin(tg * 22) * clamp(1 - k * 0.85)
        for sx in (-1, 1):
            bx1 = ax + shake + sx * 58
            ell(img, bx1 - 30, ay - 96, bx1 + 30, ay - 44, fill=mix(accent, INK, 0.05), alpha=al * q)
        ell(img, ax - 66 + shake, ay - 66, ax + 66 + shake, ay + 66, fill=mix(WHITE, accent, 0.10),
            outline=mix(accent, INK, 0.22), width=6, alpha=al * q)
        line_on(img, (ax - 44 + shake, ay + 62), (ax - 64 + shake, ay + 104), mix(accent, INK, 0.20), 7, al * q)
        line_on(img, (ax + 44 + shake, ay + 62), (ax + 64 + shake, ay + 104), mix(accent, INK, 0.20), 7, al * q)
        for i in range(12):
            an = i * math.pi / 6
            line_on(img, (ax + shake + 48 * math.cos(an), ay + 48 * math.sin(an)),
                    (ax + shake + 58 * math.cos(an), ay + 58 * math.sin(an)),
                    mix(accent, INK, 0.30), 3, al * q * 0.85)
        line_on(img, (ax + shake, ay), (ax + shake + 34, ay - 24), mix(accent, INK, 0.10), 7, al * q)
        line_on(img, (ax + shake, ay), (ax + shake - 10, ay + 40), mix(accent, INK, 0.10), 7, al * q)
        dot_on(img, ax + shake, ay, 8, mix(accent, INK, 0.10), al * q)
        for i in range(6):
            ang = i * math.pi / 3 + 0.35
            line_on(img, (ax + shake + 84 * math.cos(ang), ay - 16 + 48 * math.sin(ang)),
                    (ax + shake + 126 * math.cos(ang), ay - 16 + 76 * math.sin(ang)),
                    mix(HOT, RED, 0.25), 5, al * q * clamp(k))
        paste_c(img, ax, ay + 150, "bahan penyimpan ingatan", font(FM, 23), MUTED, al * q)
        paste_c(img, ax, ay + 188, "masih rendah saat bangun", font(FM, 23), MUTED, al * q)
    # jejak menit: makin lama makin pudar
    q2 = esmooth(seg(tl, 1.6, 2.1))
    if q2 > 0:
        y = 1230 + dy
        line_on(img, (180, y), (900, y), mix(MUTED, WHITE, 0.40), 4, al * q2)
        for i, lab in enumerate(("bangun", "1 menit", "2 menit", "3 menit")):
            x = 180 + i * 240
            fade = 1 - 0.26 * i
            dot_on(img, x, y, 12, mix(accent, INK, 0.20), al * q2 * fade)
            paste_c(img, x, y + 44, lab, font(FM, 23), MUTED, al * q2 * (0.45 + 0.55 * fade))
            if i:
                _shard(img, x, y - 74, 76, 76, -4 + i * 5, al * q2 * fade * 0.95,
                       ("rumah", "lampu", "jalan", "kopi")[i], mix(accent, WHITE, 0.30))
    # fungsi: otak merapikan ingatan (laci kartu)
    q3 = esmooth(seg(tl, 2.5, 3.0))
    if q3 > 0:
        bx0, by0 = 540, 1583 + dy
        for i, kd in enumerate(("rumah", "lampu", "jalan")):
            _shard(img, bx0 - 100 + i * 100, by0 - 96 - 10 * math.sin(tg * 1.2 + i), 74, 74,
                   -5 + i * 5, al * q3, kd, mix(GREEN, WHITE, 0.25))
            line_on(img, (bx0 - 100 + i * 100, by0 - 52), (bx0 - 150 + i * 58, by0 + 4),
                    mix(GREEN, WHITE, 0.25), 3, al * q3 * 0.8, dash=10)
        rrect_on(img, bx0 - 200, by0 + 4, bx0 + 200, by0 + 96, 26, mix(WHITE, GREEN, 0.12), al * q3,
                 outline=mix(GREEN, WHITE, 0.35), width=3)
        paste_c(img, bx0, by0 + 50, "otak merapikan ingatan", font(FS, 24), mix(GREEN, INK, 0.10), al * q3)
    q4 = esmooth(seg(tl, 3.1, 3.6))
    if q4 > 0:
        _pill_c(img, 540, 1690 + dy, "MIMPI BUKAN SEKADAR BUNGA TIDUR", font(FS, 26),
                mix(accent, INK, 0.10), q4 * al, dot=True)


VISUALS.update({
    "intro_idn": sc_intro_idn,
    "id_raw": sc_id_raw,
    "id_manu": sc_id_manu,
    "id_sdm": sc_id_sdm,
    "id_work": sc_id_work,
    "id_hope": sc_id_hope,
})


# ---------- Ep22: Kenapa gempa bisa terjadi? ----------
ROCK_A = (196, 152, 96)
ROCK_B = (160, 118, 74)
ROCK_C = (214, 176, 122)
MANTLE = (214, 116, 62)
MANTLE_D = (156, 74, 46)
OCEAN_C = (86, 150, 190)
QUAKE_C = (214, 92, 42)


def _shadow_on(img, x0, y0, x1, y1, r, alpha, spread=18, dy=14):
    """Bayangan jatuh lembut di bawah bentuk (memberi kesan berdimensi)."""
    if alpha <= 0.01:
        return
    for i in range(3):
        k = i / 2.0
        ell(img, x0 - spread * (0.4 + k), y0 + dy - spread * 0.2,
            x1 + spread * (0.4 + k), y1 + dy + spread * 0.9,
            fill=mix(INK, ROCK_B, 0.35), alpha=alpha * (0.10 - 0.03 * i))


def _sky_panel(img, x0, y0, x1, y1, r, alpha, top, bot):
    """Panel bergradasi (dipakai untuk langit malam kota)."""
    if alpha <= 0.01:
        return
    bx = _box(img, x0, y0, x1, y1, pad=4)
    X0, Y0, X1b, Y1b = bx
    w, h = X1b - X0, Y1b - Y0
    if w < 4 or h < 4:
        return
    grad = Image.new("RGB", (w, h))
    dd = ImageDraw.Draw(grad)
    for i in range(h):
        u = i / max(1, h - 1)
        c = tuple(int(round(top[k] + (bot[k] - top[k]) * u)) for k in range(3))
        dd.line([(0, i), (w, i)], fill=c)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=S(r), fill=255)
    if alpha < 0.995:
        mask = mask.point(lambda v: int(v * clamp(alpha)))
    img.paste(grad, (X0, Y0), mask)


def _city(img, ground, alpha, tg, shake=0.0, layers=2, span=(60, 1020)):
    """Siluet kota dua lapis (paralaks) dengan jendela menyala; ikut bergoyang saat gempa."""
    rows = [(0.62, mix(INK, OCEAN_C, 0.42), 0.55, 1.0), (1.0, mix(INK, MUTED, 0.20), 1.0, 2.0)]
    for li in range(layers):
        hk, col, ah, sp = rows[li]
        x = span[0]
        i = 0
        while x < span[1]:
            hsh = (i * 2654435761 + li * 7919) % 4294967296
            bw = min(54 + (hsh >> 7) % 66, span[1] - x)
            if bw < 26:
                break
            bh = (110 + (hsh >> 13) % 230) * hk
            off = shake * sp * 2.6 * math.sin(tg * 33.0 + i * 0.7)
            top = ground - bh + off
            rrect_on(img, x + off, top, x + bw + off, ground, 6 * hk, col, alpha * ah)
            if li == 1:
                for wy in range(int(top) + 18, int(ground) - 20, 32):
                    for wx in range(int(x) + 12, int(x + bw) - 14, 26):
                        hh = (wx * 31 + wy * 17) % 100
                        if hh < 46:
                            a = alpha * (0.55 + 0.45 * abs(math.sin(tg * 1.4 + hh)))
                            rrect_on(img, wx + off, wy, wx + 12 + off, wy + 14, 2,
                                     mix(HOT_L, WHITE, 0.25), a * 0.85)
            x += bw + 12 + (hsh >> 3) % 18
            i += 1
        ground -= 6


def _quake_waves(img, cx, cy, alpha, tg, k, n=5, color=QUAKE_C, rmax=620):
    """Gelombang seismik memancar dari pusat gempa (makin keluar makin pudar)."""
    if alpha <= 0.01 or k <= 0:
        return
    for i in range(n):
        p = (k * 1.35 + i / float(n)) % 1.0
        rr = 40 + rmax * p
        a = alpha * (1 - p) * 0.75
        ring_on(img, cx, cy, rr, color, max(2, 7 * (1 - p)), a, squash=0.34)


def _strata(img, x0, x1, y0, y1, alpha, palette, n=5, wob=14, tg=0.0):
    """Lapisan batuan berombak (dengan warna bertingkat) — memberi tekstur kedalaman."""
    if alpha <= 0.01:
        return
    step = (y1 - y0) / n
    for i in range(n):
        top = y0 + i * step
        col = palette[i % len(palette)]
        pts = []
        for j in range(14):
            u = j / 13.0
            pts.append((x0 + (x1 - x0) * u, top + wob * math.sin(u * 5.2 + i * 1.7) + wob * 0.4 * math.sin(tg * 0.6 + i)))
        pts += [(x1, top + step), (x0, top + step)]
        poly_on(img, pts, col, alpha * (0.95 - 0.06 * i))
        for j in range(9):
            u = (j + 0.5) / 9.0
            xx = x0 + (x1 - x0) * u + 14 * math.sin(j * 2.3 + i)
            yy = top + step * (0.38 + 0.3 * math.sin(j * 1.7 + i * 2.0))
            line_on(img, (xx, yy), (xx + 26, yy + 7), mix(col, INK, 0.30), 3, alpha * 0.35)


def _plate_slab(img, pts, alpha, fill, edge=0.55, hatch=True):
    """Lempeng: lempeng batu dengan tepi gelap + garis dalam."""
    if alpha <= 0.01:
        return
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    _shadow_on(img, min(xs), min(ys), max(xs), max(ys), 20, alpha * 0.9, spread=16, dy=18)
    poly_on(img, pts, fill, alpha * 0.99, outline=mix(fill, INK, edge), width=5)
    if hatch:
        for i in range(3):
            a = [(p[0] + 10, p[1] + 16 + i * 26) for p in pts]
            line_on(img, a[0], a[len(a) // 2], mix(fill, INK, 0.35), 3, alpha * 0.28)


def _arrow_motion(img, x, y, dx, dy, alpha, color, width=11, head=34):
    """Panah besar penanda arah gerak lempeng."""
    line_on(img, (x, y), (x + dx, y + dy), color, width, alpha)
    ang = math.atan2(dy, dx)
    for s in (+1, -1):
        a2 = ang + s * 0.42
        line_on(img, (x + dx, y + dy), (x + dx - head * math.cos(a2), y + dy - head * math.sin(a2)),
                color, width, alpha)


# warna jejak seismograf
SEISMO_C = (196, 74, 48)


def _seismo(img, x0, x1, y, alpha, prog, amp=1.0, tg=0.0):
    """Jejak seismograf: garis tenang, lalu P kecil, lalu S besar, lalu mereda."""
    if alpha <= 0.01:
        return
    line_on(img, (x0 - 16, y), (x1 + 16, y), mix(MUTED, WHITE, 0.42), 3, alpha * 0.85)
    n = 150
    pts = []
    for i in range(n):
        u = i / (n - 1.0)
        v = 0.0
        if u > 0.16:
            v += 0.22 * math.sin((u - 0.16) * 150.0) * clamp((u - 0.16) * 8)
        if u > 0.42:
            v += 1.0 * math.sin((u - 0.42) * 46.0) * clamp((u - 0.42) * 6)
        if u > 0.62:
            v *= max(0.0, 1.0 - (u - 0.62) * 2.4)
        pts.append((x0 + (x1 - x0) * u, y - v * 62 * amp))
    keep = max(2, int(n * clamp(prog * 1.02)))
    for i in range(min(keep, n) - 1):
        line_on(img, pts[i], pts[i + 1], SEISMO_C, 5, alpha * 0.95)
    if prog > 0.02:
        px, py = pts[min(keep, n) - 1]
        dot_on(img, px, py, 9 + 2 * math.sin(tg * 5.0), SEISMO_C, alpha)


def _p_wave(img, cx, cy, w, alpha, tg, color):
    """Gelombang P: rapatan dan renggangan (seperti pegas)."""
    n = 22
    for i in range(n):
        u = i / (n - 1.0)
        d = 1.0 + 0.75 * math.sin(u * 9.0 - tg * 6.0)
        x = cx - w / 2 + w * u
        rrect_on(img, x - 3.5, cy - 26 * d, x + 3.5, cy + 26 * d, 3.5, color, alpha * (0.55 + 0.45 * d))


def _s_wave(img, cx, cy, w, alpha, tg, color):
    """Gelombang S: naik-turun seperti tali (lebih merusak)."""
    pts = [(cx - w / 2 + w * (i / 40.0), cy + 30 * math.sin((i / 40.0) * 6.0 - tg * 5.0))
           for i in range(41)]
    for i in range(40):
        line_on(img, pts[i], pts[i + 1], color, 6, alpha)


def _fault_block(img, x0, y0, x1, y1, alpha, fill, zig, flip=False):
    """Blok batuan dengan tepi bergerigi (bidang sesar)."""
    pts = [(x0, y0), (x1, y0)]
    n = 7
    for i in range(n + 1):
        u = i / n
        yy = y0 + (y1 - y0) * u
        xx = x1 + (zig if (i % 2 == 0) else 0) * (1 if not flip else -1)
        pts.append((xx, yy))
    pts += [(x0, y1)]
    poly_on(img, pts, fill, alpha * 0.99, outline=mix(fill, INK, 0.5), width=4)


def _chip_lbl(img, cx, cy, text, f, col, alpha, padx=18, pady=10):
    """Label kecil dengan latar krem: teks tetap terbaca di atas panel berwarna."""
    if alpha <= 0:
        return
    w_, h_ = tw(text, f), (f.size if hasattr(f, "size") else 26)
    rrect_on(img, cx - w_ / 2 - padx, cy - h_ / 2 - pady, cx + w_ / 2 + padx, cy + h_ / 2 + pady,
             int(h_ * 0.55), mix(CREAM, WHITE, 0.45), alpha * 0.96)
    paste_c(img, cx, cy, text, f, col, alpha)


def sc_intro_quake(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: kota malam yang bergoyang, gelombang menjalar dari pusat gempa."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.18 + i * 0.20, 0.82 + i * 0.20))
        if q <= 0:
            continue
        fsz = 100 if i == 0 else 60
        f = font(FB if i == 0 else FS, fsz)
        while tw(l, f) > 900 and fsz > 38:
            fsz -= 6
            f = font(FB if i == 0 else FS, fsz)
        paste_c(img, 540, (516 + i * 96) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q1 = seg(tl, 0.5, 0.9)
    if q1 > 0:
        _pill_c(img, 540, 676 + dy, "SAINS DI BAWAH TANAH KITA", font(FS, 25), mix(accent, INK, 0.10),
                esmooth(q1) * al, dot=True)
    px0, py0, px1, py1 = 96, 748, 984, 1584
    q2 = esmooth(seg(tl, 0.30, 1.0))
    _sky_panel(img, px0, py0, px1, py1, 44, q2 * al, (28, 34, 74), (96, 74, 132))
    if q2 <= 0.05:
        return
    _stars(img, tg, 0.9 * al * q2, n=28, y0=py0 + 26, y1=py0 + 300, color=(250, 246, 232))
    _moon(img, 848, 856 + dy, 46, q2 * al)
    ground = 1420 + dy
    kq = clamp(seg(tl, 1.05, 1.75))
    shake = kq * clamp(1 - seg(tl, 2.4, 3.4)) * 1.0
    _quake_waves(img, 540, ground + 130, 0.85 * al * q2 * kq, tg, clamp(seg(tl, 1.0, 3.2)), n=5, rmax=540)
    _city(img, ground, al * q2, tg, shake=shake, layers=2, span=(116, 962))
    # debu yang beterbangan setelah guncangan
    if shake > 0.05:
        items = []
        for i in range(26):
            h = (i * 40503 + 11) % 4294967296
            u = ((tg * (0.5 + ((h >> 5) % 50) / 100.0) + (h % 100) / 100.0) % 1.0)
            items.append((120 + (h >> 7) % 840 + 18 * math.sin(tg * 2 + i),
                          ground - u * 320, 3.4 * (1 - u) + 2.0, mix(ROCK_C, WHITE, 0.35), (1 - u) * 0.55))
        _dots(img, items, al * q2 * shake)
    q3 = esmooth(seg(tl, 1.9, 2.45))
    if q3 > 0:
        _pill_c(img, 540, 1620 + dy, "PUSAT GEMPA BISA JAUH DI BAWAH TANAH", font(FS, 24),
                mix(accent, INK, 0.10), q3 * al, dot=True)
    # riak yang terus mengalir keluar (menjaga adegan tetap hidup)
    if tl > 3.3:
        _quake_waves(img, 540, ground + 130, 0.30 * al * q2, tg, ((tl - 3.3) * 0.26) % 1.0, n=4, rmax=430)


def sc_plates(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 1: lempeng raksasa bergerak dan bertemu."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    x0, y0, x1, y1 = 96, 700 + dy, 984, 1450 + dy
    q = esmooth(seg(tl, 0.25, 0.9))
    if q <= 0:
        return
    # laut di atas kerak
    rrect_on(img, x0, y0, x1, y0 + 116, 30, mix(OCEAN_C, WHITE, 0.25), al * q * 0.9)
    for i in range(5):
        yy = y0 + 34 + i * 20
        pts = [(x0 + 20 + j * 40, yy + 6 * math.sin(j * 0.8 + tg * 0.9 + i)) for j in range(24)]
        for j in range(len(pts) - 1):
            line_on(img, pts[j], pts[j + 1], mix(OCEAN_C, INK, 0.25), 3, al * q * 0.55)
    # mantel bergradasi
    _sky_panel(img, x0, y0 + 108, x1, y1, 26, al * q * 0.95, (232, 158, 96), (188, 92, 54))
    _strata(img, x0 + 8, x1 - 8, y0 + 180, y0 + 236, al * q * 0.8, [mix(ROCK_A, WHITE, 0.10)], n=1, wob=8, tg=tg)
    # dua lempeng: satu menyusup ke bawah
    k = esmooth(seg(tl, 0.6, 3.0)) + 0.10 * clamp(seg(tl, 3.0, dur - 0.2))
    slide = 44 * k
    left = [(x0 + 4, y0 + 132), (x0 + 470 + slide, y0 + 132), (x0 + 372 + slide, y0 + 268),
            (x0 + 232 + slide, y0 + 470), (x0 + 120, y0 + 470), (x0 + 4, y0 + 300)]
    right = [(x1 - 4, y0 + 132), (x0 + 470 - 26 + slide, y0 + 132), (x0 + 470 - 30 + slide, y0 + 470),
             (x1 - 4, y0 + 470)]
    _plate_slab(img, left, al * q, ROCK_A, edge=0.5)
    _plate_slab(img, right, al * q, ROCK_C, edge=0.45)
    # parit (palung) di titik tumbukan
    _shadow_on(img, x0 + 400 + slide, y0 + 120, x0 + 520 + slide, y0 + 200, 10, al * q * 0.8, spread=10, dy=8)
    # panah gerak
    qa = esmooth(seg(tl, 1.0, 1.6))
    if qa > 0:
        _arrow_motion(img, x0 + 250, y0 + 596, 150, -74, al * qa * 0.9, mix(QUAKE_C, INK, 0.10), 12, 40)
        ft = font(FM, 21)
        tL, tR = "lempeng samudra · naik", "lempeng benua · menahan"
        wL, wR = tw(tL, ft) + 44, tw(tR, ft) + 44
        cxL, cxR = x0 + 14 + wL / 2, x1 - 14 - wR / 2
        _chip_lbl(img, cxL, y0 + 636, tL, ft, mix(QUAKE_C, INK, 0.15), al * qa)
        _chip_lbl(img, cxR, y0 + 636, tR, ft, mix(QUAKE_C, INK, 0.15), al * qa)
        _arrow_motion(img, x1 - 300, y0 + 592, -120, -52, al * qa * 0.8, mix(accent, INK, 0.15), 11, 36)

    q2 = esmooth(seg(tl, 2.1, 2.7))
    if q2 > 0:
        line_on(img, (x0 + 300, y0 + 250), (x0 + 470 + slide, y0 + 250), mix(accent, WHITE, 0.45), 3,
                al * q2 * 0.8, dash=12)
        _chip_lbl(img, x0 + 300 - tw("zona tumbukan", font(FS, 24)) / 2, y0 + 202,
                  "zona tumbukan", font(FS, 24), mix(accent, INK, 0.10), al * q2)
    q3 = esmooth(seg(tl, 2.9, 3.4))
    if q3 > 0:
        _pill_c(img, 540, 1650 + dy, "TEPI LEMPENG SALING MENGUNCI", font(FS, 27),
                mix(accent, INK, 0.10), q3 * al, dot=True)


def sc_snap(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 2: energi menumpuk di batuan terkunci, lalu patah mendadak."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    cx, by = 540, 1420 + dy
    k = clamp(seg(tl, 0.35, 2.5))
    snap = clamp(seg(tl, 2.55, 3.15))
    es = esmooth(snap)
    env = es * (1 - clamp(seg(tl, 3.05, 3.75)))     # burst hanya sesaat
    sh = 34 * es + 9 * clamp(seg(tl, 3.2, dur - 0.3))   # blok kanan terus merayap
    # dua blok batuan bertemu di bidang sesar bergerigi
    _fault_block(img, 130, 820 + dy, 534, by, al, ROCK_B, 26)
    _fault_block(img, 546 + sh, 820 + dy, 950 + sh, by, al, ROCK_A, 26, flip=True)
    # tekstur lapisan batuan (lebih tegas)
    _strata(img, 138, 522, 866 + dy, by - 14, al * 0.72,
            [mix(ROCK_B, INK, 0.15), mix(ROCK_B, WHITE, 0.24)], n=4, wob=10, tg=tg)
    _strata(img, 556 + sh, 942 + sh, 866 + dy, by - 14, al * 0.72,
            [mix(ROCK_A, INK, 0.14), mix(ROCK_A, WHITE, 0.26)], n=4, wob=10, tg=tg)
    # garis bidang sesar yang menyala
    fault = []
    for i in range(8):
        u = i / 7.0
        fault.append((534 + (26 if i % 2 == 0 else 0) + sh * u, 820 + dy + (by - 820 - dy) * u))
    for i in range(len(fault) - 1):
        line_on(img, fault[i], fault[i + 1], mix(accent, WHITE, 0.35), 16, al * (0.10 + 0.14 * es))
        line_on(img, fault[i], fault[i + 1], mix(accent, INK, 0.10), 5, al * (0.55 + 0.45 * es))
    # serpihan tekanan yang menekan ke arah sesar (makin kuat dengan meteran)
    if k > 0.02:
        for i in range(7):
            yy = 880 + dy + i * 78
            jt = 3.4 * k * math.sin(tg * 9.0 + i)
            ln = 30 + 46 * k
            line_on(img, (300 - ln + jt, yy), (300 + jt, yy), mix(QUAKE_C, INK, 0.20), 4, al * k * 0.55)
            line_on(img, (780 + ln - jt, yy), (780 - jt, yy), mix(QUAKE_C, INK, 0.20), 4, al * k * 0.55)
    # dorongan dari kedua sisi
    qa = esmooth(seg(tl, 0.6, 1.3))
    if qa > 0:
        _arrow_motion(img, 120, 1120 + dy, 90, 0, al * qa * 0.9, mix(QUAKE_C, INK, 0.15), 12, 34)
        _arrow_motion(img, 960, 1120 + dy, -90, 0, al * qa * 0.9, mix(QUAKE_C, INK, 0.15), 12, 34)
    # meteran energi yang terisi
    qb = esmooth(seg(tl, 0.9, 2.4))
    if qb > 0:
        rrect_on(img, 240, 700 + dy, 840, 748 + dy, 24, mix(WHITE, QUAKE_C, 0.12), al * qb,
                 outline=mix(QUAKE_C, WHITE, 0.45), width=3)
        rrect_on(img, 246, 706 + dy, 246 + (588 - 12) * qb, 742 + dy, 18, mix(QUAKE_C, INK, 0.10), al * qb)
        paste_c(img, 540, 660 + dy, "energi menumpuk", font(FS, 25), mix(QUAKE_C, INK, 0.10), al * qb)
    # label fase mengunci
    qm = esmooth(seg(tl, 1.15, 1.7)) * (1 - esmooth(seg(tl, 2.35, 2.6)))
    if qm > 0.02:
        _chip_lbl(img, 540 + 180 * (1 - qm), 786 + dy, "BATUAN TERKUNCI", font(FS, 24),
                  mix(ROCK_B, INK, 0.72), al * qm)
    # patah mendadak: burst energi
    if env > 0.02:
        for i in range(14):
            ang = i * math.pi / 7.0 + 0.18
            r0 = 40 + 120 * es
            ln = 60 + 150 * es
            line_on(img, (540 + r0 * 1.55 * math.cos(ang), 1120 + dy + r0 * 0.62 * math.sin(ang)),
                    (540 + (r0 + ln) * 1.55 * math.cos(ang), 1120 + dy + (r0 + ln) * 0.62 * math.sin(ang)),
                    mix(QUAKE_C, RED, 0.30), 8, al * env * 0.95)
        ring_on(img, 540, 1120 + dy, 60 + 300 * es, mix(QUAKE_C, WHITE, 0.28), 8,
                al * (1 - snap) * 0.85, squash=0.5)
        _chip_lbl(img, 540, 786 + dy, "BATUAN PATAH!", font(FS, 24), mix(QUAKE_C, INK, 0.05),
                  al * env)
    # setelah patah: energi menyebar sebagai getaran yang terus mengalir
    if tl > 3.25:
        _quake_waves(img, 540, 1120 + dy, 0.34 * al, tg, ((tl - 3.25) * 0.24) % 1.0, n=4, rmax=420)
    q2 = esmooth(seg(tl, 3.1, 3.6))
    if q2 > 0:
        _pill_c(img, 540, 1620 + dy, "BATUAN PATAH — ENERGI LEPAS", font(FS, 27),
                mix(accent, INK, 0.10), q2 * al, dot=True)
        paste_c(img, 540, 1700 + dy, "gempa adalah energinya", font(FM, 24), MUTED, q2 * al)


def sc_waves(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 3: gelombang P cepat, gelombang S paling merusak."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    # panel P
    q = esmooth(seg(tl, 0.25, 0.75))
    if q > 0:
        rrect_on(img, 118, 640 + dy, 962, 900 + dy, 34, mix(WHITE, accent, 0.05), al * q,
                 outline=mix(accent, WHITE, 0.45), width=3)
        paste_r(img, 158, 690 + dy, "gelombang P", font(FS, 27), mix(accent, INK, 0.05), al * q)
        paste_r(img, 430, 694 + dy, "paling cepat · jarang merusak", font(FM, 23), MUTED, al * q)
        _p_wave(img, 540, 810 + dy, 700, al * q, tg, mix(accent, INK, 0.15))
    # panel S
    q2 = esmooth(seg(tl, 0.85, 1.4))
    if q2 > 0:
        rrect_on(img, 118, 930 + dy, 962, 1190 + dy, 34, mix(WHITE, QUAKE_C, 0.05), al * q2,
                 outline=mix(QUAKE_C, WHITE, 0.45), width=3)
        paste_r(img, 158, 980 + dy, "gelombang S", font(FS, 27), mix(QUAKE_C, INK, 0.05), al * q2)
        paste_r(img, 430, 984 + dy, "datang kemudian · paling merusak", font(FM, 23), MUTED, al * q2)
        _s_wave(img, 540, 1105 + dy, 700, al * q2, tg, mix(QUAKE_C, INK, 0.10))
    # seismograf
    q3 = esmooth(seg(tl, 1.5, 2.1))
    if q3 > 0:
        rrect_on(img, 118, 1230 + dy, 962, 1500 + dy, 34, mix(WHITE, MUTED, 0.10), al * q3,
                 outline=mix(MUTED, WHITE, 0.45), width=3)
        paste_r(img, 158, 1278 + dy, "seismograf mencatat keduanya", font(FS, 25), mix(MUTED, INK, 0.15), al * q3)
        _seismo(img, 200, 900, 1400 + dy, al * q3, esmooth(seg(tl, 1.7, 3.2)), amp=1.0, tg=tg)
    q4 = esmooth(seg(tl, 3.0, 3.5))
    if q4 > 0:
        _pill_c(img, 540, 1650 + dy, "P DULU, S MENYUSUL", font(FS, 28), mix(accent, INK, 0.10), q4 * al, dot=True)


def sc_idn_quake(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 4: Indonesia di pertemuan tiga lempeng + ratusan sesar."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.25, 0.9))
    if q <= 0:
        return
    _map_id(img, 108, 720 + dy, 1.0, al * q, mix(accent, WHITE, 0.44), QUAKE_C, tg,
            res=[(360, 176, ""), (500, 250, ""), (214, 318, ""), (170, 120, "")])
    # busur Cincin Api: melengkung mengikuti tepi barat-daya kepulauan
    qa = esmooth(seg(tl, 1.0, 2.0))
    if qa > 0:
        pts = []
        for i in range(29):
            u = i / 28.0
            pts.append((150 + u * 816, 706 + dy + 452 * math.sin(math.pi * u) ** 0.82
                        + 12 * math.sin(u * 9.0 + tg * 0.6)))
        for i in range(len(pts) - 1):
            line_on(img, pts[i], pts[i + 1], mix(QUAKE_C, INK, 0.25), 6, al * qa * 0.85, dash=20)
        _chip_lbl(img, 300, 616 + dy, "CINCIN API PASIFIK", font(FS, 23), mix(QUAKE_C, INK, 0.10), al * qa)
        # titik-titik gempa yang berdenyut di sepanjang busur
        for i, u in enumerate((0.10, 0.26, 0.41, 0.57, 0.72, 0.88)):
            px = 150 + u * 816
            py = 706 + dy + 452 * math.sin(math.pi * u) ** 0.82
            pl = 0.55 + 0.45 * abs(math.sin(tg * 2.1 + i * 1.3))
            ring_on(img, px, py, 16 + 22 * (1 - pl), mix(QUAKE_C, WHITE, 0.25), 3, al * qa * pl * qa, squash=1.0)
            dot_on(img, px, py, 9, mix(QUAKE_C, INK, 0.10), al * qa)
    # panah tiga lempeng
    qb = esmooth(seg(tl, 1.7, 2.4))
    if qb > 0:
        _arrow_motion(img, 520, 1168 + dy, 0, -104, al * qb * 0.9, mix(QUAKE_C, INK, 0.12), 12, 34)
        _chip_lbl(img, 520, 1252 + dy, "LEMPENG INDO-AUSTRALIA", font(FM, 22), mix(QUAKE_C, INK, 0.18), al * qb)
        _arrow_motion(img, 936, 838 + dy, -124, 8, al * qb * 0.85, mix(accent, INK, 0.15), 11, 32)
        _chip_lbl(img, 884, 776 + dy, "PASIFIK", font(FM, 22), mix(QUAKE_C, INK, 0.18), al * qb)
        _arrow_motion(img, 690, 664 + dy, 86, 96, al * qb * 0.8, mix(accent, INK, 0.20), 10, 30)
        _chip_lbl(img, 786, 616 + dy, "EURASIA", font(FM, 22), mix(QUAKE_C, INK, 0.18), al * qb)
    # jumlah sesar
    q2 = esmooth(seg(tl, 2.4, 3.0))
    if q2 > 0:
        rrect_on(img, 300, 1420 + dy, 780, 1560 + dy, 30, mix(WHITE, accent, 0.06), al * q2,
                 outline=mix(accent, WHITE, 0.45), width=3)
        counter_c(img, 540, 1470 + dy, tl, 2.5, 3.3, 0, 267, font(FB, 62), mix(accent, INK, 0.05), al)
        paste_c(img, 540, 1524 + dy, "segmen sesar sudah terpetakan", font(FM, 23), MUTED, al * q2)
    q3 = esmooth(seg(tl, 3.1, 3.6))
    if q3 > 0:
        _pill_c(img, 540, 1650 + dy, "KITA DI TITIK TEMU TIGA LEMPENG", font(FS, 26),
                mix(accent, INK, 0.10), q3 * al, dot=True)


def sc_predict_quake(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 5: tidak bisa diprediksi, tapi ada peringatan dini beberapa detik."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    # kiri: jam tanpa tanggal
    q = esmooth(seg(tl, 0.25, 0.85))
    if q > 0:
        rrect_on(img, 118, 640 + dy, 520, 1240 + dy, 34, mix(WHITE, accent, 0.05), al * q,
                 outline=mix(accent, WHITE, 0.45), width=3)
        cx, cy = 319, 800 + dy
        ring_on(img, cx, cy, 118, mix(accent, INK, 0.20), 6, al * q)
        for i in range(12):
            an = i * math.pi / 6
            line_on(img, (cx + 96 * math.cos(an), cy + 96 * math.sin(an)),
                    (cx + 112 * math.cos(an), cy + 112 * math.sin(an)), mix(accent, INK, 0.30), 4, al * q * 0.9)
        paste_c(img, cx, cy - 10, "?", font(FB, 120), mix(accent, INK, 0.05), al * q)
        for i in range(3):
            k2 = (tg * 0.35 + i * 0.33) % 1.0
            paste_c(img, cx + 150 + 40 * math.sin(tg * 0.8 + i), cy - 150 * k2, "?",
                    font(FB, 34), mix(accent, INK, 0.10), al * q * (1 - k2))
        paste_c(img, cx, cy + 210, "tanggal gempa belum", font(FS, 25), mix(accent, INK, 0.10), al * q)
        paste_c(img, cx, cy + 252, "bisa diprediksi", font(FS, 25), mix(accent, INK, 0.10), al * q)
    # kanan: peringatan dini
    q2 = esmooth(seg(tl, 1.0, 1.7))
    if q2 > 0:
        rrect_on(img, 560, 640 + dy, 962, 1240 + dy, 34, mix(WHITE, GREEN, 0.06), al * q2,
                 outline=mix(GREEN, WHITE, 0.45), width=3)
        paste_c(img, 761, 700 + dy, "peringatan dini", font(FS, 26), mix(GREEN, INK, 0.08), al * q2)
        # sensor di permukaan + dua gelombang
        gx, gy = 761, 1000 + dy
        rrect_on(img, gx - 90, gy + 90, gx + 90, gy + 104, 8, mix(ROCK_B, INK, 0.20), al * q2)
        line_on(img, (gx, gy + 90), (gx, gy - 30), mix(MUTED, INK, 0.25), 8, al * q2)
        dot_on(img, gx, gy - 44, 14 + 3 * math.sin(tg * 4.0), mix(GREEN, INK, 0.05), al * q2)
        for i in range(4):
            a = 0.35 + 0.35 * abs(math.sin(tg * 1.6 + i))
            ring_on(img, gx, gy - 44, 30 + i * 22, mix(GREEN, WHITE, 0.30), 3, al * q2 * a, squash=0.6)
        # gelombang P mendahului S
        prog = esmooth(seg(tl, 1.5, 2.9))
        pxp = gx - 300 + 430 * prog
        pxs = gx - 380 + 430 * prog * 0.72
        dot_on(img, pxp, gy - 44, 13, mix(GREEN, INK, 0.05), al * q2)
        paste_c(img, pxp, gy - 82, "P", font(FB, 26), mix(GREEN, INK, 0.05), al * q2)
        dot_on(img, pxs, gy - 44, 15, mix(QUAKE_C, INK, 0.10), al * q2)
        paste_c(img, pxs, gy - 86, "S", font(FB, 26), mix(QUAKE_C, INK, 0.10), al * q2)
        q3 = esmooth(seg(tl, 2.1, 2.7))
        if q3 > 0:
            counter_c(img, 761, 1160 + dy, tl, 2.1, 2.7, 0, 8, font(FB, 54), mix(GREEN, INK, 0.05), al, suf=" detik")
            paste_c(img, 761, 1214 + dy, "waktu sebelum gelombang S tiba", font(FM, 22), MUTED, al * q3)
    q4 = esmooth(seg(tl, 3.0, 3.5))
    if q4 > 0:
        _pill_c(img, 540, 1420 + dy, "TIDAK BISA DIPREDIKSI — TAPI BISA DIPERCEPAT PERINGATANNYA", font(FS, 23),
                mix(accent, INK, 0.10), q4 * al, dot=True)
        paste_c(img, 540, 1500 + dy, "yang merusak bukan gempanya, tapi bangunan yang roboh", font(FM, 23),
                MUTED, q4 * al)


def sc_aftershock(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 6: gempa susulan yang makin melemah."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    x0, x1, base = 140, 940, 1240 + dy
    q = esmooth(seg(tl, 0.25, 0.8))
    if q <= 0:
        return
    paste_c(img, 540, 660 + dy, "kekuatan getaran setelah gempa utama", font(FS, 25),
            mix(accent, INK, 0.08), q * al)
    line_on(img, (x0 - 20, base), (x1 + 20, base), mix(MUTED, WHITE, 0.40), 4, al * 0.9)
    n = 12
    for i in range(n):
        k = esmooth(seg(tl, 0.6 + i * 0.14, 1.2 + i * 0.14))
        hgt = (330 * (0.98 ** i)) * k
        x = x0 + (x1 - x0) * (i / (n - 1.0))
        col = mix(QUAKE_C, INK, 0.05 + 0.03 * i) if i < 4 else mix(QUAKE_C, MUTED, 0.35)
        line_on(img, (x, base), (x, base - hgt), col, 13, al * 0.95)
        dot_on(img, x, base - hgt, 9, col, al)
        if i == 0:
            paste_c(img, x, base - hgt - 40, "gempa utama", font(FS, 22), mix(QUAKE_C, INK, 0.05), al * k)
        if i >= 5 and k > 0.9:      # gempa susulan kecil terus muncul
            ph = (tl * 0.42 + i * 0.17) % 1.0
            ring_on(img, x, base - hgt, 12 + 34 * ph, mix(QUAKE_C, WHITE, 0.40), 3,
                    al * (1 - ph) * 0.5, squash=1.0)
            dot_on(img, x, base - hgt, 8 + 2 * math.sin(tg * 6.0 + i), col, al)
    q2 = esmooth(seg(tl, 2.2, 2.8))
    if q2 > 0:
        pts = [(x0 + (x1 - x0) * (i / 40.0), base - 350 * (0.94 ** (i * 1.1))) for i in range(41)]
        for i in range(40):
            line_on(img, pts[i], pts[i + 1], mix(accent, INK, 0.20), 4, al * q2 * 0.85, dash=12)
        paste_r(img, x0 + 40, base - 392, "kekuatannya cenderung menurun", font(FM, 23), MUTED, al * q2)
    q3 = esmooth(seg(tl, 3.0, 3.5))
    if q3 > 0:
        _pill_c(img, 540, 1440 + dy, "GEMPA SUSULAN BISA BERLANGSUNG BERHARI-HARI", font(FS, 24),
                mix(accent, INK, 0.10), q3 * al, dot=True)
        paste_c(img, 540, 1520 + dy, "jumlahnya banyak, tapi makin lemah", font(FM, 24), MUTED, q3 * al)


VISUALS.update({
    "intro_mimpi": sc_intro_mimpi,
    "rem": sc_rem,
    "logic": sc_logic,
    "memory": sc_memory,
    "forget": sc_forget,
})


# ---------- EP23: Kenapa Kucing Mengeong? (bagian 1: helper + 4 adegan) ----------
CAT_D = (98, 102, 130)      # abu-biru (kucing utama)
CAT_G = (216, 142, 74)      # oranye jahe
CAT_C = (246, 242, 234)     # putih krem
NIGHT_B = (34, 40, 84)
NIGHT_T = (112, 90, 152)
WARM_L = (236, 176, 104)
PINKY = (226, 150, 150)
TEAL_C = (31, 122, 107)
MAROON_C = (150, 62, 86)


def _cat(img, cx, base_y, s, alpha, col, tg=0.0, mouth=0.0, wag=0.0, ear=0.0, edge=0.0):
    """Kucing duduk menghadap depan: badan, kepala, telinga, mata, kumis, ekor bergerak."""
    if alpha <= 0.01:
        return
    bw, bh = 152 * s, 118 * s
    by0, by1 = base_y - bh, base_y
    ec = mix(col, INK, 0.30) if edge <= 0 else mix(col, INK, 0.30 + 0.35 * edge)
    ell(img, cx - bw / 2, by0, cx + bw / 2, by1, fill=col, alpha=alpha,
        outline=ec if edge > 0 else None, width=max(3, int(4 * s)))
    if edge > 0:    # kucing berbulu terang: beri lapis kedua agar tidak menyatu dengan latar
        ell(img, cx - bw / 2, by0, cx + bw / 2, by1, fill=col, alpha=alpha * edge * 0.5)
    # ekor melengkung + bergerak
    pts = []
    for i in range(10):
        u = i / 9.0
        pts.append((cx + bw / 2 - 10 * s + 46 * s * u + 16 * s * math.sin(tg * 1.6 + wag) * u,
                    base_y - 12 * s - 74 * s * math.sin(u * 1.45) - 10 * s * math.sin(tg * 1.9 + wag) * u))
    for i in range(9):
        line_on(img, pts[i], pts[i + 1], mix(col, INK, 0.10), max(3, int(13 * s * (1 - 0.45 * i / 9.0))), alpha)
    hw, hh = 76 * s, 66 * s
    hcy = by0 - hh * 0.50
    ell(img, cx - hw, hcy - hh, cx + hw, hcy + hh, fill=col, alpha=alpha,
        outline=ec if edge > 0 else None, width=max(3, int(4 * s)))
    if edge > 0:
        ell(img, cx - hw, hcy - hh, cx + hw, hcy + hh, fill=col, alpha=alpha * edge * 0.5)
    for sgn in (-1, 1):     # telinga
        poly_on(img, [(cx + sgn * hw * 0.74, hcy - hh * 0.52),
                      (cx + sgn * (hw * 0.46 + 6 * s * math.sin(tg * 3.0 + ear)), hcy - hh * 1.62),
                      (cx + sgn * hw * 0.10, hcy - hh * 0.74)], col, alpha,
                outline=ec if edge > 0 else None, width=max(2, int(3 * s)))
    blink = 1.0 if math.sin(tg * 0.85) > -0.93 else 0.12
    for sgn in (-1, 1):     # mata
        ell(img, cx + sgn * 28 * s - 10 * s, hcy - 16 * s - 8 * s * blink,
            cx + sgn * 28 * s + 10 * s, hcy - 16 * s + 8 * s * blink, fill=mix(col, INK, 0.78), alpha=alpha)
    poly_on(img, [(cx - 8 * s, hcy + 10 * s), (cx + 8 * s, hcy + 10 * s), (cx, hcy + 21 * s)], PINKY,
            alpha * 0.9)
    if mouth > 0.02:        # mulut terbuka saat mengeong
        ell(img, cx - 11 * s, hcy + 20 * s, cx + 11 * s, hcy + 20 * s + 20 * s * mouth,
            fill=mix(col, INK, 0.55), alpha=alpha)
    for sgn in (-1, 1):     # kumis
        for k, (d1, d2) in enumerate(((-7, 1), (1, 3), (9, 6))):
            line_on(img, (cx + sgn * hw * 0.55, hcy + 9 * s),
                    (cx + sgn * (hw + 40 * s), hcy + (9 + d1) * s + d2 * s), mix(col, WHITE, 0.62), 2, alpha * 0.85)
    for sgn in (-1, 1):     # kaki depan
        rrect_on(img, cx + sgn * 34 * s - 17 * s, base_y - 18 * s, cx + sgn * 34 * s + 17 * s,
                 base_y + 6 * s, int(9 * s), col, alpha)


def _meow(img, cx, cy, w, amp, alpha, tg, kind="short", col=None):
    """Gelombang meongan: deret batang dengan selubung (envelope) sesuai jenisnya."""
    if alpha <= 0.01:
        return
    col = col or CAT_G
    n = max(8, int(w / 13))
    for i in range(n):
        u = i / (n - 1.0)
        if kind == "short":
            e = math.exp(-((u - 0.5) ** 2) / 0.012)
        elif kind == "long":
            e = 0.35 + 0.65 * math.exp(-((u - 0.5) ** 2) / 0.10)
        elif kind == "repeat":
            e = 0.0
            for c in (0.18, 0.5, 0.82):
                e = max(e, math.exp(-((u - c) ** 2) / 0.006))
        else:                       # purr: riak kecil + lonjakan nada tinggi
            e = 0.16 + 0.10 * math.sin(tg * 7.0 + u * 26.0)
            if abs(u - 0.62) < 0.012:
                e = 1.0
        h = amp * e * (0.86 + 0.14 * abs(math.sin(tg * 5.2 + i * 0.5)))
        if h < 1.0:
            continue
        x = cx - w / 2 + w * u
        line_on(img, (x, cy), (x, cy - h), col, max(3, int(0.16 * w / n * 2.4)), alpha * (0.55 + 0.45 * e))


def _person(img, cx, base_y, s, alpha, col):
    """Siluet orang berdiri (sederhana) — lawan bicara kucing."""
    if alpha <= 0.01:
        return
    r = 26 * s
    ell(img, cx - r, base_y - 300 * s - r, cx + r, base_y - 300 * s + r, fill=col, alpha=alpha)
    poly_on(img, [(cx - 46 * s, base_y - 282 * s), (cx + 46 * s, base_y - 282 * s),
                  (cx + 58 * s, base_y - 96 * s), (cx - 58 * s, base_y - 96 * s)], col, alpha)
    for sgn in (-1, 1):
        line_on(img, (cx + sgn * 56 * s, base_y - 264 * s), (cx + sgn * 74 * s, base_y - 150 * s),
                col, max(6, int(20 * s)), alpha)
        rrect_on(img, cx + sgn * 30 * s - 15 * s, base_y - 100 * s, cx + sgn * 30 * s + 15 * s,
                 base_y, int(9 * s), col, alpha)


def _clock(img, cx, cy, r, hh, mm, alpha, col, accent, tg=0.0):
    """Jam analog kecil (jarum bergerak halus), untuk menandai jam 3 pagi / 5 / 9."""
    if alpha <= 0.01:
        return
    ring_on(img, cx, cy, r, col, max(3, int(r * 0.09)), alpha, squash=1.0)
    ell(img, cx - r * 0.94, cy - r * 0.94, cx + r * 0.94, cy + r * 0.94, fill=mix(CREAM, WHITE, 0.55), alpha=alpha * 0.9)
    for i in range(12):
        a = i * math.pi / 6
        r0, r1 = r * 0.74, r * (0.92 if i % 3 == 0 else 0.86)
        line_on(img, (cx + r0 * math.sin(a), cy - r0 * math.cos(a)), (cx + r1 * math.sin(a), cy - r1 * math.cos(a)),
                mix(col, INK, 0.35), max(2, int(r * 0.05)), alpha)
    ah = (hh % 12) * math.pi / 6 + mm * math.pi / 360
    am = mm * math.pi / 30
    line_on(img, (cx, cy), (cx + r * 0.44 * math.sin(ah), cy - r * 0.44 * math.cos(ah)), mix(col, INK, 0.65),
            max(3, int(r * 0.10)), alpha)
    line_on(img, (cx, cy), (cx + r * 0.72 * math.sin(am), cy - r * 0.72 * math.cos(am)), col,
            max(2, int(r * 0.06)), alpha)


def _window(img, x0, y0, x1, y1, alpha, tg=0.0):
    """Jendela malam: panel gelap + bingkai + bintang + bulan."""
    if alpha <= 0.01:
        return
    _sky_panel(img, x0, y0, x1, y1, 40, alpha, NIGHT_B, NIGHT_T)
    _stars(img, tg, alpha * 0.9, n=26, y0=y0 + 30, y1=y0 + 300, color=(250, 246, 232))
    _moon(img, x1 - 130, y0 + 118, 44, alpha)
    bf = mix(WHITE, CREAM, 0.25)
    line_on(img, ((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1), bf, 10, alpha * 0.95)
    line_on(img, (x0, y0 + (y1 - y0) * 0.52), (x1, y0 + (y1 - y0) * 0.52), bf, 10, alpha * 0.95)
    rrect_on(img, x0, y0, x1, y1, 40, mix(WHITE, CREAM, 0.30), alpha, outline=mix(MUTED, WHITE, 0.35), width=9)


def sc_intro_cat(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: jendela malam, jam tiga pagi, kucing mengeong."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.18 + i * 0.20, 0.82 + i * 0.20))
        if q <= 0:
            continue
        fsz = 100 if i == 0 else 66
        f = font(FB if i == 0 else FS, fsz)
        while tw(l, f) > 900 and fsz > 38:
            fsz -= 6
            f = font(FB if i == 0 else FS, fsz)
        paste_c(img, 540, (516 + i * 96) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q1 = esmooth(seg(tl, 0.5, 0.95))
    if q1 > 0:
        _pill_c(img, 540, 676 + dy, "BAHASA RAHASIA KUCING", font(FS, 25), mix(accent, INK, 0.10), q1 * al, dot=True)
    px0, py0, px1, py1 = 104, 748, 976, 1560
    q2 = esmooth(seg(tl, 0.30, 1.0))
    _window(img, px0, py0, px1, py1, q2 * al, tg)
    if q2 <= 0.05:
        return
    sill = py1 - 150
    rrect_on(img, px0 + 26, sill, px1 - 26, sill + 42, 14, mix(WARM_L, WHITE, 0.15), q2 * al * 0.95)
    _clock(img, px0 + 118, py0 + 150, 62, 3, 0, q2 * al, mix(accent, INK, 0.35), accent, tg)
    _chip_lbl(img, px0 + 118, py0 + 236, "JAM 3 PAGI", font(FS, 22), mix(accent, INK, 0.15), q2 * al)
    # kucing di ambang jendela
    kq = clamp(seg(tl, 0.9, 1.6))
    mo = 0.35 + 0.65 * abs(math.sin(tg * 2.4))
    _cat(img, 620, sill + 6, 1.06, q2 * al * kq, mix(CAT_D, INK, 0.05), tg, mouth=mo * kq, wag=0.0, ear=0.4)
    qw = esmooth(seg(tl, 1.15, 1.8))
    if qw > 0:
        _meow(img, 430, sill - 150, 300, 150, al * q2 * qw, tg, kind="long", col=mix(accent, INK, 0.05))
        for i in range(3):
            ph = (tl * 0.55 + i * 0.34) % 1.0
            ring_on(img, 452, sill - 150, 24 + 92 * ph, mix(accent, WHITE, 0.30), 4,
                    al * q2 * qw * (1 - ph) * 0.40, squash=1.0)
    q3 = esmooth(seg(tl, 2.0, 2.6))
    if q3 > 0:
        _pill_c(img, 540, 1650 + dy, "MEONGAN ITU BUKAN BAHASA KUCING", font(FS, 24),
                mix(accent, INK, 0.10), q3 * al, dot=True)
    if tl > 3.0:    # tetap hidup: gelombang meongan mengalir
        _meow(img, 430, sill - 150, 300, 132, al * q2 * 0.35, tg, kind="long", col=mix(accent, WHITE, 0.10))


def sc_meow_human(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 1: meongan ditujukan ke manusia, bukan ke kucing lain."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    # panel kiri: dua kucing, tanpa suara
    q = esmooth(seg(tl, 0.3, 0.85))
    if q > 0:
        rrect_on(img, 108, 660 + dy, 518, 1170 + dy, 34, mix(WHITE, MUTED, 0.08), al * q,
                 outline=mix(MUTED, WHITE, 0.45), width=3)
        paste_c(img, 313, 712 + dy, "ke kucing lain", font(FS, 25), mix(MUTED, INK, 0.25), al * q)
        _cat(img, 220, 1080 + dy, 0.62, al * q, mix(CAT_D, INK, 0.02), tg, mouth=0.0, wag=0.0)
        _cat(img, 406, 1080 + dy, 0.60, al * q, mix(CAT_C, MUTED, 0.30), tg, mouth=0.0, wag=3.0, ear=1.2, edge=0.8)
        qm = esmooth(seg(tl, 1.0, 1.5))
        if qm > 0:
            _chip_lbl(img, 313, 900 + dy, "HAMPIR TIDAK PERNAH MENGEONG", font(FM, 21),
                      mix(MUTED, INK, 0.45), al * q * qm)
    # panel kanan: kucing mengeong ke orang
    q2 = esmooth(seg(tl, 0.6, 1.15))
    if q2 > 0:
        rrect_on(img, 562, 660 + dy, 972, 1170 + dy, 34, mix(WHITE, accent, 0.07), al * q2,
                 outline=mix(accent, WHITE, 0.45), width=3)
        paste_c(img, 767, 712 + dy, "ke manusia", font(FS, 25), mix(accent, INK, 0.10), al * q2)
        _person(img, 610, 1104 + dy, 0.62, al * q2 * 0.95, mix(MUTED, INK, 0.25))
        mo = 0.3 + 0.7 * abs(math.sin(tg * 2.6))
        _cat(img, 880, 1104 + dy, 0.60, al * q2, mix(CAT_G, INK, 0.05), tg, mouth=mo, wag=0.0, ear=0.5)
        qw = esmooth(seg(tl, 1.2, 1.8))
        if qw > 0:
            _meow(img, 880, 806 + dy, 190, 96, al * q2 * qw, tg, kind="repeat", col=mix(accent, INK, 0.05))
    q3 = esmooth(seg(tl, 2.3, 2.9))
    if q3 > 0:
        _pill_c(img, 540, 1300 + dy, "MEONGAN DISIMPAN KHUSUS UNTUK KITA", font(FS, 26),
                mix(accent, INK, 0.10), q3 * al, dot=True)
        paste_c(img, 540, 1384 + dy, "kucing dewasa lebih banyak bicara lewat bau & gerak tubuh",
                font(FM, 23), MUTED, q3 * al)
    if tl > 3.2:
        _meow(img, 313, 900 + dy, 240, 54, al * 0.28, tg, kind="short", col=mix(MUTED, WHITE, 0.20))


def sc_kitten(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 2: asalnya panggilan bayi kucing -> disimpan sampai dewasa."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    # baris atas: anak kucing memanggil induknya
    q = esmooth(seg(tl, 0.3, 0.9))
    if q > 0:
        rrect_on(img, 108, 640 + dy, 972, 900 + dy, 34, mix(WHITE, accent, 0.06), al * q,
                 outline=mix(accent, WHITE, 0.45), width=3)
        paste_c(img, 540, 690 + dy, "anak kucing memanggil induknya", font(FS, 25), mix(accent, INK, 0.10), al * q)
        _cat(img, 250, 866 + dy, 0.44, al * q, mix(CAT_G, WHITE, 0.25), tg, mouth=0.5 + 0.5 * abs(math.sin(tg * 3.0)), ear=0.6)
        _cat(img, 830, 880 + dy, 0.80, al * q, mix(CAT_D, INK, 0.02), tg, mouth=0.0)
        qw = esmooth(seg(tl, 0.8, 1.4))
        if qw > 0:
            _meow(img, 540, 782 + dy, 300, 78, al * q * qw, tg, kind="long", col=mix(accent, INK, 0.05))
            for i in range(3):
                ph = (tl * 0.5 + i * 0.34) % 1.0
                ring_on(img, 540, 796 + dy, 24 + 96 * ph, mix(accent, WHITE, 0.35), 4, al * q * qw * (1 - ph) * 0.5)
    # panah turun "tumbuh dewasa"
    q2 = esmooth(seg(tl, 1.1, 1.6))
    if q2 > 0:
        _arrow_motion(img, 540, 946 + dy, 0, 118, al * q2 * 0.9, mix(accent, INK, 0.18), 12, 38)
        _chip_lbl(img, 540, 1000 + dy, "TUMBUH DEWASA", font(FM, 22), mix(accent, INK, 0.25), al * q2)
    # dua cabang
    q3 = esmooth(seg(tl, 1.6, 2.2))
    if q3 > 0:
        rrect_on(img, 108, 1100 + dy, 518, 1440 + dy, 34, mix(WHITE, MUTED, 0.10), al * q3,
                 outline=mix(MUTED, WHITE, 0.45), width=3)
        paste_c(img, 313, 1150 + dy, "kucing liar", font(FS, 25), mix(MUTED, INK, 0.25), al * q3)
        _cat(img, 313, 1382 + dy, 0.52, al * q3 * 0.95, mix(CAT_C, MUTED, 0.34), tg, mouth=0.0, ear=0.0, edge=0.9)
        qs = esmooth(seg(tl, 2.2, 2.7))
        if qs > 0:
            ring_on(img, 313, 1300 + dy, 54, mix(MAROON_C, WHITE, 0.30), 5, al * q3 * qs * 0.8)
            for sgn in (-1, 1):
                line_on(img, (313 - 40, 1300 + dy - 40 * sgn), (313 + 40, 1300 + dy + 40 * sgn),
                        mix(MAROON_C, INK, 0.12), 8, al * q3 * qs)
            _chip_lbl(img, 313, 1204 + dy, "PENGGILAN ITU HILANG", font(FM, 20), mix(MAROON_C, INK, 0.25), al * q3 * qs)
    q4 = esmooth(seg(tl, 1.9, 2.5))
    if q4 > 0:
        rrect_on(img, 562, 1100 + dy, 972, 1440 + dy, 34, mix(WHITE, accent, 0.08), al * q4,
                 outline=mix(accent, WHITE, 0.45), width=3)
        paste_c(img, 767, 1150 + dy, "kucing rumahan", font(FS, 25), mix(accent, INK, 0.10), al * q4)
        _cat(img, 700, 1382 + dy, 0.52, al * q4, mix(CAT_G, INK, 0.04), tg,
             mouth=0.35 + 0.65 * abs(math.sin(tg * 2.8)), ear=0.6)
        _person(img, 880, 1400 + dy, 0.5, al * q4 * 0.9, mix(MUTED, INK, 0.30))
        qw2 = esmooth(seg(tl, 2.5, 3.0))
        if qw2 > 0:
            _meow(img, 796, 1310 + dy, 150, 54, al * q4 * qw2, tg, kind="short", col=mix(accent, INK, 0.05))
            _chip_lbl(img, 767, 1256 + dy, "MEONGAN DIPERTAHANKAN", font(FM, 20), mix(accent, INK, 0.20), al * q4 * qw2)
    q5 = esmooth(seg(tl, 3.3, 3.9))
    if q5 > 0:
        _pill_c(img, 540, 1580 + dy, "KITA JADI PENGGANTI INDUKNYA", font(FS, 26),
                mix(accent, INK, 0.10), q5 * al, dot=True)


def sc_dialect(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 3: tiap kucing punya 'dialek' sendiri hasil latihan ke majikannya."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    rows = [(1010 + dy, CAT_G, "kucing A", accent), (1330 + dy, CAT_D, "kucing B", mix(accent, INK, 0.18))]
    kinds = ("short", "repeat")
    for i, (y, cc, nm, ac) in enumerate(rows):
        q = esmooth(seg(tl, 0.3 + i * 0.45, 0.85 + i * 0.45))
        if q <= 0:
            continue
        rrect_on(img, 108, y - 130, 972, y + 130, 34, mix(WHITE, ac, 0.05), al * q,
                 outline=mix(ac, WHITE, 0.55), width=3)
        _cat(img, 210, y + 92, 0.46, al * q, mix(cc, INK, 0.04), tg, mouth=0.4 + 0.6 * abs(math.sin(tg * 2.6 + i)))
        _meow(img, 470, y + 40, 210, 96, al * q, tg, kind=kinds[i], col=mix(ac, INK, 0.08))
        _person(img, 790, y + 96, 0.42, al * q * 0.9, mix(MUTED, INK, 0.30))
        _chip_lbl(img, 660, y - 78, nm.upper(), font(FM, 21), mix(ac, INK, 0.20), al * q)
        if i == 1:
            _chip_lbl(img, 470, y - 78, "POLA BERBEDA", font(FM, 21), mix(ac, INK, 0.20), al * q)
    q2 = esmooth(seg(tl, 1.6, 2.2))
    if q2 > 0:
        _chip_lbl(img, 540, 1180 + dy, "KAMU YANG MENGAJARINYA — DENGAN MERESPONS", font(FM, 22),
                  mix(accent, INK, 0.20), al * q2)
    q3 = esmooth(seg(tl, 2.6, 3.2))
    if q3 > 0:
        _pill_c(img, 540, 1520 + dy, "ORANG LAIN TIDAK TAHU ARTINYA", font(FS, 26),
                mix(accent, INK, 0.10), q3 * al, dot=True)
        paste_c(img, 540, 1600 + dy, "tidak ada kamus meongan yang berlaku untuk semua kucing",
                font(FM, 23), MUTED, q3 * al)
    if tl > 3.4:
        _meow(img, 470, 1010 + dy + 40, 210, 42, al * 0.30, tg, kind="short", col=mix(accent, WHITE, 0.05))


# ---------- EP23 bagian 2: adegan 5-7 (arti meongan, jam 3 pagi, kucing tua) ----------

def _purr_spec(img, x0, y0, x1, y1, alpha, tg, accent):
    """Spektrum purr: riak rendah + lonjakan nada tinggi ~380 Hz (mirip tangisan bayi)."""
    if alpha <= 0.01:
        return
    base = y1
    line_on(img, (x0, base), (x1, base), mix(MUTED, WHITE, 0.40), 4, alpha * 0.9)
    n = 46
    for i in range(n):
        u = i / (n - 1.0)
        h = (y1 - y0) * (0.10 + 0.05 * abs(math.sin(tg * 6.0 + i * 0.9)))
        if u < 0.34:
            h = (y1 - y0) * (0.30 + 0.05 * abs(math.sin(tg * 7.0 + i)))
        if 0.44 < u < 0.62:
            h = (y1 - y0) * (0.04 + 0.03 * abs(math.sin(tg * 8.0 + i)))
        if abs(u - 0.68) < 0.016:
            h = (y1 - y0) * 1.0
        elif abs(u - 0.68) < 0.048:
            h = (y1 - y0) * 0.42
        x = x0 + (x1 - x0) * u
        col = mix(accent, INK, 0.10) if abs(u - 0.68) < 0.034 else mix(MUTED, INK, 0.15)
        line_on(img, (x, base), (x, base - h), col, 7, alpha * (0.95 if abs(u - 0.68) < 0.034 else 0.7))
    # pita frekuensi tangisan bayi (300-600 Hz): kolom bertanda
    bx0 = x0 + (x1 - x0) * 0.635
    bx1 = x0 + (x1 - x0) * 0.725
    rrect_on(img, bx0, y0, bx1, base, 12, mix(MAROON_C, WHITE, 0.80), alpha * 0.75,
             outline=mix(MAROON_C, WHITE, 0.35), width=3)
    _chip_lbl(img, (bx0 + bx1) / 2, y0 - 4, "±380 Hz", font(FM, 21), mix(MAROON_C, INK, 0.20), alpha)
    _chip_lbl(img, (x0 + x1) / 2 - (x1 - x0) * 0.10, base - 28, "MIRIP TANGISAN BAYI",
              font(FM, 20), mix(MAROON_C, INK, 0.20), alpha)


def _activity(img, x0, x1, y0, y1, alpha, tg, accent):
    """Kurva aktivitas 24 jam: dua puncak (05.00 & 21.00) + pita jam tidur manusia."""
    if alpha <= 0.01:
        return
    base = y1
    # pita tidur manusia: 23.00 - 06.00
    rrect_on(img, x0 + (x1 - x0) * (23 / 24.0), y0, x1, base, 0, mix(MUTED, WHITE, 0.55), alpha * 0.55)
    rrect_on(img, x0, y0, x0 + (x1 - x0) * (6 / 24.0), base, 0, mix(MUTED, WHITE, 0.55), alpha * 0.55)
    line_on(img, (x0, base), (x1, base), mix(MUTED, WHITE, 0.40), 4, alpha * 0.9)
    pts = []
    for i in range(97):
        u = i / 96.0
        h = 0.14 + 0.62 * math.exp(-((u - 5 / 24.0) ** 2) / 0.0035) + 0.86 * math.exp(-((u - 21 / 24.0) ** 2) / 0.0042)
        pts.append((x0 + (x1 - x0) * u, base - (base - y0) * min(1.0, h)))
    for i in range(96):
        line_on(img, pts[i], pts[i + 1], mix(accent, INK, 0.10), 6, alpha * 0.95)
    for u, lbl in ((5 / 24.0, "05.00"), (21 / 24.0, "21.00")):
        px, py = x0 + (x1 - x0) * u, base - (base - y0) * (0.14 + (0.62 if lbl == "05.00" else 0.86))
        dot_on(img, px, py, 9 + 2 * math.sin(tg * 4.0), mix(accent, INK, 0.05), alpha)
        _chip_lbl(img, px, py - 44, lbl, font(FM, 21), mix(accent, INK, 0.20), alpha)
    # penanda jam 3 pagi
    px3 = x0 + (x1 - x0) * (3 / 24.0)
    for i in range(10):
        yy = base - (base - y0) * (0.04 + i * 0.105)
        line_on(img, (px3, yy), (px3, yy + (base - y0) * 0.055), mix(MAROON_C, WHITE, 0.30), 3, alpha * 0.75, dash=9)
    _chip_lbl(img, px3 + 108, base - (base - y0) * 0.52, "JAM 3 PAGI", font(FM, 21),
              mix(MAROON_C, INK, 0.20), alpha)
    paste_r(img, x0, y0 - 42, "kucing paling aktif saat fajar & menjelang malam", font(FM, 22),
            mix(accent, INK, 0.20), alpha)
    paste_c(img, x0 + (x1 - x0) * 0.145, y0 + 26, "kita tidur", font(FM, 20), mix(MUTED, INK, 0.30), alpha * 0.9)


def sc_meaning(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 4: arti meongan berbeda-beda + purr minta makan dengan nada tinggi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    cards = [("pendek", "sapaan", "short"), ("panjang", "minta sesuatu", "long"),
             ("berulang", "cari perhatian", "repeat")]
    for i, (nm, arti, kind) in enumerate(cards):
        q = esmooth(seg(tl, 0.25 + i * 0.28, 0.75 + i * 0.28))
        if q <= 0:
            continue
        x0 = 108 + i * 296
        rrect_on(img, x0, 640 + dy, x0 + 272, 990 + dy, 30, mix(WHITE, accent, 0.05), al * q,
                 outline=mix(accent, WHITE, 0.55), width=3)
        paste_c(img, x0 + 136, 696 + dy, nm, font(FS, 27), mix(accent, INK, 0.05), al * q)
        _meow(img, x0 + 136, 890 + dy, 210, 120, al * q, tg, kind=kind, col=mix(accent, INK, 0.08))
        _chip_lbl(img, x0 + 136, 936 + dy, arti.upper(), font(FM, 20), mix(accent, INK, 0.20), al * q)
    q2 = esmooth(seg(tl, 1.2, 1.8))
    if q2 > 0:
        rrect_on(img, 108, 1050 + dy, 972, 1470 + dy, 34, mix(WHITE, MAROON_C, 0.05), al * q2,
                 outline=mix(MAROON_C, WHITE, 0.60), width=3)
        paste_r(img, 150, 1104 + dy, "purr saat minta makan", font(FS, 26), mix(MAROON_C, INK, 0.05), al * q2)
        paste_r(img, 560, 1110 + dy, "ada nada tinggi terselip di dalamnya", font(FM, 22), MUTED, al * q2)
        q3 = esmooth(seg(tl, 2.0, 2.8))
        if q3 > 0:
            _purr_spec(img, 190, 1196 + dy, 890, 1396 + dy, al * q2 * q3, tg, MAROON_C)
    q4 = esmooth(seg(tl, 3.3, 3.9))
    if q4 > 0:
        _pill_c(img, 540, 1600 + dy, "MAKANYA SUSAH SEKALI DIABAIKAN", font(FS, 26),
                mix(accent, INK, 0.10), q4 * al, dot=True)


def sc_night(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 5: kenapa tengah malam — jadwal aktivitas + sebab-sebabnya + tips."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.3, 0.9))
    if q > 0:
        rrect_on(img, 108, 660 + dy, 972, 1200 + dy, 34, mix(WHITE, accent, 0.05), al * q,
                 outline=mix(accent, WHITE, 0.50), width=3)
        qq = esmooth(seg(tl, 0.7, 1.6))
        if qq > 0:
            _activity(img, 200, 900, 900 + dy, 1130 + dy, al * q * qq, tg, accent)
    reasons = ("LAPAR", "BOSAN", "KEBIASAAN YANG BERHASIL")
    for i, r in enumerate(reasons):
        q2 = esmooth(seg(tl, 1.5 + i * 0.25, 2.0 + i * 0.25))
        if q2 <= 0:
            continue
        _chip_lbl(img, 250 + i * 292, 1290 + dy, r, font(FM, 21), mix(accent, INK, 0.20), al * q2)
    tips = [("MAIN AKTIF", "30 menit sebelum tidur"), ("MAKAN TERJADWAL", "biar tidak menagih jam 3 pagi")]
    for i, (t1, t2) in enumerate(tips):
        q3 = esmooth(seg(tl, 2.2 + i * 0.3, 2.7 + i * 0.3))
        if q3 <= 0:
            continue
        x0 = 108 + i * 448
        rrect_on(img, x0, 1360 + dy, x0 + 424, 1520 + dy, 28, mix(WHITE, TEAL_C, 0.06), al * q3,
                 outline=mix(TEAL_C, WHITE, 0.55), width=3)
        dot_on(img, x0 + 44, 1420 + dy, 13, mix(TEAL_C, INK, 0.05), al * q3)
        paste_r(img, x0 + 76, 1404 + dy, t1, font(FS, 23), mix(TEAL_C, INK, 0.05), al * q3)
        paste_r(img, x0 + 76, 1452 + dy, t2, font(FM, 20), MUTED, al * q3)
    q4 = esmooth(seg(tl, 3.4, 4.0))
    if q4 > 0:
        _pill_c(img, 540, 1620 + dy, "JADWALNYA TABRAKAN DENGAN JAM TIDUR KITA", font(FS, 24),
                mix(accent, INK, 0.10), q4 * al, dot=True)
    if tl > 4.2:
        _meow(img, 880, 1200 + dy, 170, 40, al * 0.26, tg, kind="short", col=mix(accent, WHITE, 0.05))


def sc_senior(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 6: kucing tua yang mengeong malam -> cek dokter, bukan dimarahi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.3, 0.9))
    if q > 0:
        rrect_on(img, 108, 660 + dy, 500, 1180 + dy, 34, mix(WHITE, accent, 0.06), al * q,
                 outline=mix(accent, WHITE, 0.50), width=3)
        _cat(img, 304, 1130 + dy, 0.86, al * q, mix(CAT_C, MUTED, 0.36), tg,
             mouth=0.25 + 0.35 * abs(math.sin(tg * 1.7)), wag=1.2, ear=0.3, edge=0.9)
        _chip_lbl(img, 304, 726 + dy, "10+ TAHUN", font(FM, 22), mix(accent, INK, 0.20), al * q)
        qk = esmooth(seg(tl, 0.9, 1.5))
        if qk > 0:
            _meow(img, 452, 872 + dy, 120, 62, al * q * qk, tg, kind="long", col=mix(accent, INK, 0.08))
    signs = ("TURUN BERAT BADAN", "GELISAH & MONDAR-MANDIR", "MENABRAK BENDA", "MENGEONG TERUS")
    for i, s in enumerate(signs):
        q2 = esmooth(seg(tl, 1.0 + i * 0.28, 1.55 + i * 0.28))
        if q2 <= 0:
            continue
        y = 700 + (i // 2) * 200 + (i % 2) * 100 + dy
        x0 = 560
        rrect_on(img, x0, y - 46, x0 + 412, y + 46, 24, mix(WHITE, MAROON_C, 0.07), al * q2,
                 outline=mix(MAROON_C, WHITE, 0.60), width=3)
        dot_on(img, x0 + 40, y, 12, mix(MAROON_C, INK, 0.05), al * q2)
        paste_r(img, x0 + 66, y - 12, s, font(FS, 22), mix(MAROON_C, INK, 0.10), al * q2)
        paste_r(img, x0 + 66, y + 24, "tanda yang perlu dicek", font(FM, 19), MUTED, al * q2 * 0.9)
    q3 = esmooth(seg(tl, 2.6, 3.2))
    if q3 > 0:
        rrect_on(img, 108, 1260 + dy, 972, 1440 + dy, 30, mix(WHITE, accent, 0.08), al * q3,
                 outline=mix(accent, WHITE, 0.50), width=3)
        paste_c(img, 540, 1310 + dy, "bisa jadi hipertiroid · tekanan darah tinggi", font(FM, 22),
                mix(accent, INK, 0.15), al * q3)
        paste_c(img, 540, 1364 + dy, "nyeri sendi · penurunan fungsi otak", font(FM, 22),
                mix(accent, INK, 0.15), al * q3)
        paste_c(img, 540, 1408 + dy, "bukan sekadar cari perhatian", font(FR, 21), MUTED, al * q3)
    q4 = esmooth(seg(tl, 3.6, 4.2))
    if q4 > 0:
        _pill_c(img, 540, 1600 + dy, "JANGAN DIMARAHI — PERIKSA KE DOKTER HEWAN", font(FS, 24),
                mix(accent, INK, 0.10), q4 * al, dot=True)
    if tl > 4.4:
        _meow(img, 452, 872 + dy, 120, 40, al * 0.24, tg, kind="long", col=mix(accent, WHITE, 0.05))


VISUALS.update({
    "intro_quake": sc_intro_quake,
    "plates": sc_plates,
    "snap": sc_snap,
    "waves": sc_waves,
    "idn_quake": sc_idn_quake,
"predict": sc_predict_quake,
    "aftershock": sc_aftershock,
})


# ---------- EP24: Kenapa Bulan Berwarna Merah? (bagian 1: helper + 4 adegan) ----------
MOON_W = (246, 240, 226)     # bulan terang
MOON_R = (208, 96, 58)       # bulan merah tembaga
MOON_D = (146, 48, 40)       # merah pekat
DUSK_T = (34, 38, 78)        # langit senja (atas)
DUSK_B = (196, 116, 96)      # langit senja (bawah, dekat ufuk)
ATM_B = (118, 168, 232)      # pita atmosfer biru
ATM_R = (228, 122, 82)       # pita atmosfer merah


def _big_moon(img, cx, cy, r, alpha, col, tg=0.0, glow=0.6, craters=True):
    """Bulan besar: piringan + kawah + lingkaran cahaya (glow)."""
    if alpha <= 0.01 or r < 4:
        return
    for i in range(4):
        ring_on(img, cx, cy, r * (1.07 + i * 0.13), mix(col, WHITE, 0.30), max(2, int(r * 0.07 - i * 2)),
                alpha * glow * (0.13 - i * 0.025), squash=1.0)
    ell(img, cx - r, cy - r, cx + r, cy + r, fill=col, alpha=alpha,
        outline=mix(col, INK, 0.28) if r > 26 else None, width=max(2, int(r * 0.055)))
    if craters and r > 40:
        for (u, v, s, a) in ((-0.34, -0.22, 0.20, 0.10), (0.22, -0.42, 0.13, 0.08),
                            (0.36, 0.30, 0.17, 0.09), (-0.14, 0.44, 0.12, 0.07), (0.02, 0.05, 0.09, 0.06)):
            rr = r * s
            ell(img, cx + r * u - rr, cy + r * v - rr, cx + r * u + rr, cy + r * v + rr,
                fill=mix(col, INK, 0.16), alpha=alpha)


def _sky_dusk(img, x0, y0, x1, y1, r, alpha, tg=0.0, stars=True):
    """Panel langit senja bergradasi + bintang tipis di bagian atas."""
    if alpha <= 0.01:
        return
    _sky_panel(img, x0, y0, x1, y1, r, alpha, DUSK_T, DUSK_B)
    if stars:
        _stars(img, tg, alpha * 0.55, n=22, y0=y0 + 26, y1=y0 + 240, color=(250, 246, 232))


def _arc_y(cx, cy, R, x):
    """Tinggi permukaan lengkung Bumi pada posisi x."""
    dx = min(abs(x - cx), R * 0.999)
    return cy - math.sqrt(max(0.0, R * R - dx * dx))


def _atm_curve(img, cx, cy, R, alpha, tg, accent, tl=0.0):
    """Bulan tinggi (jalur pendek) vs bulan di ufuk (jalur panjang lewat atmosfer tebal)."""
    if alpha <= 0.01:
        return
    x0, x1 = 118, 962
    y_top = 760
    # atmosfer: beberapa lapis terang mengikuti lengkung Bumi
    for i in range(5):
        rr = R + 16 + i * 26
        pts = []
        for j in range(37):
            x = x0 - 30 + (x1 - x0 + 60) * j / 36.0
            pts.append((x, _arc_y(cx, cy, rr, x)))
        for j in range(len(pts) - 1):
            line_on(img, pts[j], pts[j + 1], mix(ATM_B, WHITE, 0.10 + i * 0.10), 10 - i,
                    alpha * (0.34 - i * 0.05))
    # badan Bumi
    pts = [(x0 - 40, _arc_y(cx, cy, R, x0 - 40))]
    for j in range(37):
        x = x0 - 40 + (x1 - x0 + 80) * j / 36.0
        pts.append((x, _arc_y(cx, cy, R, x)))
    pts += [(x1 + 40, y_top + 900), (x0 - 40, y_top + 900)]
    poly_on(img, pts, mix(OCEAN_C, INK, 0.40), alpha * 0.95)
    # pengamat kiri: bulan tinggi -> jalur pendek
    ox, oy = 320, int(_arc_y(cx, cy, R, 320)) + 6
    _person(img, ox, oy, 0.40, alpha * 0.95, mix(INK, MUTED, 0.35))
    _big_moon(img, ox, y_top + 110, 46, alpha, MOON_W, tg, glow=0.35, craters=False)
    line_on(img, (ox, oy - 128), (ox, y_top + 168), mix(GREEN, INK, 0.10), 4, alpha * 0.75, dash=13)
    _lbl(img, ox + 176, y_top + 196, "JALUR PENDEK", font(FM, 24), mix(GREEN, INK, 0.15), alpha)
    # pengamat kanan: bulan rendah di ufuk -> jalur panjang
    rx = 790
    ry = int(_arc_y(cx, cy, R, rx)) + 6
    _big_moon(img, rx + 96, ry - 92, 46, alpha, MOON_R, tg, glow=0.55, craters=False)
    pts = []
    for j in range(21):
        aa = 0.46 - 0.78 * j / 20.0
        rr = R + 46
        pts.append((cx + rr * math.sin(aa), cy - rr * math.cos(aa)))
    for j in range(len(pts) - 1):
        line_on(img, pts[j], pts[j + 1], mix(ATM_R, INK, 0.12), 5, alpha * 0.9, dash=15)
    _lbl(img, 640, y_top + 262, "JALUR PANJANG", font(FM, 24), mix(ATM_R, INK, 0.12), alpha)
    _lbl(img, 300, y_top + 470, "ATMOSFER LEBIH TEBAL", font(FM, 24), mix(ATM_B, INK, 0.22), alpha)



def _scatter_beam(img, x, y, w, alpha, tg, accent):
    """Sinar putih masuk atmosfer: biru tersebar ke samping, merah terus lewat."""
    if alpha <= 0.01:
        return
    # matahari kecil di kiri
    ell(img, x - 46, y - 46, x + 46, y + 46, fill=mix(HOT_L, WHITE, 0.10), alpha=alpha)
    paste_c(img, x, y, "cahaya", font(FM, 24), mix(accent, INK, 0.10), alpha)
    # berkas utama
    for i in range(4):
        yy = y - 22 + i * 15
        line_on(img, (x + 52, yy), (x + 52 + w * 0.42, yy - 4), mix(MOON_W, INK, 0.15), 8, alpha * 0.9)
    # zona hamburan
    zx = x + 52 + w * 0.30
    rrect_on(img, zx, y - 130, zx + 170, y + 130, 26, mix(ATM_B, WHITE, 0.82), alpha * 0.55,
             outline=mix(ATM_B, WHITE, 0.40), width=3)
    _lbl(img, zx + 85, y - 158, "ATMOSFER", font(FM, 24), mix(ATM_B, INK, 0.20), alpha)
    for i in range(16):     # hamburan biru ke segala arah
        ph = (tg * 0.7 + i * 0.14) % 1.0
        ang = i * math.pi / 8 + ph * 0.6
        r0 = 30 + 120 * ph
        dot_on(img, zx + 85 + r0 * math.cos(ang), y + r0 * 0.55 * math.sin(ang),
               5 + 3 * (1 - ph), mix(ATM_B, INK, 0.10), alpha * (1 - ph) * 0.85)
    # keluar: merah
    for i in range(4):
        yy = y - 16 + i * 11
        line_on(img, (zx + 170, yy), (zx + 170 + w * 0.36, yy + 6), mix(ATM_R, INK, 0.12), 8, alpha * 0.95)
    _lbl(img, x + w + 96, y - 92, "YANG LOLOS: MERAH", font(FM, 24), mix(ATM_R, INK, 0.12), alpha)


def _align_eclipse(img, alpha, tg, accent, mx=1010):
    """Matahari - Bumi - Bulan sejajar: umbra/penumbra + bulan berubah merah."""
    if alpha <= 0.01:
        return
    sy, sx = 900, 150
    ell(img, sx - 74, sy - 74, sx + 74, sy + 74, fill=mix(HOT_L, WHITE, 0.12), alpha=alpha)
    for i in range(3):
        ring_on(img, sx, sy, 86 + i * 26, mix(HOT_L, WHITE, 0.20), 7 - i, alpha * (0.30 - i * 0.07), squash=1.0)
    ell(img, 500 - 92, sy - 92, 500 + 92, sy + 92, fill=mix(OCEAN_C, INK, 0.35), alpha=alpha)
    ring_on(img, 500, sy, 106, mix(ATM_B, WHITE, 0.35), 12, alpha * 0.45, squash=1.0)
    # kerucut bayangan
    poly_on(img, [(560, sy - 74), (560, sy + 74), (mx, sy + 12), (mx, sy - 12)],
            mix(INK, OCEAN_C, 0.30), alpha * 0.55)
    poly_on(img, [(560, sy - 132), (560, sy + 132), (max(mx + 30, 1040), sy + 52),
                  (max(mx + 30, 1040), sy - 52)],
            mix(INK, MUTED, 0.45), alpha * 0.20)
    _big_moon(img, mx, sy, 74, alpha, MOON_R, tg, glow=0.7)
    _lbl(img, 700, sy - 168, "BAYANGAN INTI BUMI (UMBRA)", font(FM, 24), mix(INK, MUTED, 0.55), alpha)
    _lbl(img, min(mx, 840), sy + 152, "BULAN MEMERAH", font(FM, 25), mix(ATM_R, INK, 0.15), alpha)
    paste_c(img, sx, sy + 128, "Matahari", font(FM, 24), mix(accent, INK, 0.20), alpha)
    paste_c(img, 500, sy + 132, "Bumi", font(FM, 24), mix(accent, INK, 0.20), alpha)
    # cahaya yang dibelokkan atmosfer ke bulan
    for sgn in (-1, 1):
        for i in range(3):
            y0 = sy + sgn * (78 + i * 18)
            line_on(img, (596, y0), (mx - 70, sy + sgn * (18 + i * 7)), mix(ATM_R, INK, 0.15), 5,
                    alpha * (0.55 - i * 0.10), dash=13)


def sc_intro_redmoon(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: bulan merah besar terbit di ufuk malam."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.18 + i * 0.20, 0.82 + i * 0.20))
        if q <= 0:
            continue
        fsz = 100 if i == 0 else 66
        f = font(FB if i == 0 else FS, fsz)
        while tw(l, f) > 900 and fsz > 38:
            fsz -= 6
            f = font(FB if i == 0 else FS, fsz)
        paste_c(img, 540, (516 + i * 96) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q1 = esmooth(seg(tl, 0.5, 0.95))
    if q1 > 0:
        _pill_c(img, 540, 676 + dy, "DUA SEBAB, SATU JAWABAN", font(FS, 30), mix(accent, INK, 0.10), q1 * al, dot=True)
    px0, py0, px1, py1 = 104, 748, 976, 1584
    q2 = esmooth(seg(tl, 0.30, 1.0))
    _sky_dusk(img, px0, py0, px1, py1, 44, q2 * al, tg)
    if q2 <= 0.05:
        return
    # ufuk: garis laut + siluet bukit
    hy = py1 - 250
    rrect_on(img, px0 + 10, hy, px1 - 10, py1 - 10, 30, mix(OCEAN_C, INK, 0.45), q2 * al * 0.75)
    for i in range(5):
        pts = [(px0 + 40 + j * 220, hy + 26 + i * 22 + 7 * math.sin(j * 0.8 + tg * 0.7 + i)) for j in range(5)]
        for j in range(4):
            line_on(img, pts[j], pts[j + 1], mix(MOON_R, WHITE, 0.45), 4, q2 * al * 0.35)
    # bulan merah terbit + pantulan
    km = esmooth(seg(tl, 0.7, 1.9))
    if km > 0:
        mcy = hy - 190 + 150 * (1 - km)
        # makin tinggi, makin tipis atmosfer yang dilalui -> merahnya berkurang
        colm = mix(MOON_D, MOON_R, clamp((km - 0.18) / 0.82))
        _big_moon(img, 540, mcy, 150, q2 * al * km, colm, tg, glow=0.85)
        for i in range(7):
            w_ = 150 * (1 - i / 8.0)
            line_on(img, (540 - w_, hy + 34 + i * 26), (540 + w_, hy + 34 + i * 26),
                    mix(MOON_R, WHITE, 0.55), 6, q2 * al * km * (0.30 - i * 0.03))
    # garis ufuk + label
    q3 = esmooth(seg(tl, 1.6, 2.2))
    if q3 > 0:
        line_on(img, (px0 + 20, hy), (px1 - 20, hy), mix(MOON_W, WHITE, 0.20), 4, q2 * al * q3 * 0.75, dash=18)
        _lbl(img, 300, hy - 268, "UFUK", font(FM, 25), mix(MOON_R, INK, 0.20), q2 * al * q3)
    q4 = esmooth(seg(tl, 2.4, 3.0))
    if q4 > 0:
        _pill_c(img, 540, 1660 + dy, "BULANNYA TIDAK BERUBAH WARNA", font(FS, 29),
                mix(accent, INK, 0.10), q4 * al, dot=True)
    if tl > 3.2:
        for i in range(2):
            ph = (tl * 0.4 + i * 0.5) % 1.0
            ring_on(img, 540, hy - 190, 150 + 90 * ph, mix(MOON_R, WHITE, 0.35), 4,
                    al * q2 * (1 - ph) * 0.30, squash=1.0)


def sc_horizon(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 1: bulan rendah di ufuk -> cahaya menembus atmosfer lebih tebal."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.3, 0.9))
    if q > 0:
        _stage_rect(img, 108, 640 + dy, 972, 1240 + dy, 34, mix(WHITE, accent, 0.05), al * q,
                 outline=mix(accent, WHITE, 0.50), width=3)
        qq = esmooth(seg(tl, 0.6, 1.5))
        if qq > 0:
            _atm_curve(img, 540, 1700 + dy, 700, al * q * qq, tg, accent, tl=tl)
    q2 = esmooth(seg(tl, 1.7, 2.4))
    if q2 > 0:
        _stage_rect(img, 108, 1256 + dy, 972, 1396 + dy, 30, mix(WHITE, ATM_R, 0.07), al * q2,
                 outline=mix(ATM_R, WHITE, 0.55), width=3)
        paste_c(img, 540, 1306 + dy, "makin rendah bulan, makin tebal udara yang dilaluinya",
                font(FM, 26), mix(ATM_R, INK, 0.12), al * q2)
        paste_c(img, 540, 1356 + dy, "biru tersebar habis — sisa jingga & merah", font(FM, 26),
                mix(ATM_R, INK, 0.12), al * q2)
    q1b = esmooth(seg(tl, 2.5, 3.1))
    if q1b > 0:     # angka pembanding: massa udara di ufuk vs di atas kepala
        _stage_rect(img, 148, 1416 + dy, 932, 1524 + dy, 26, mix(WHITE, ATM_R, 0.09), al * q1b,
                 outline=mix(ATM_R, WHITE, 0.55), width=3)
        counter_c(img, 320, 1470 + dy, tl, 2.5, 3.5, 1, 38, font(FB, 65), mix(ATM_R, INK, 0.06),
                  al, suf="×")
        paste_r(img, 424, 1456 + dy, "lebih tebal", font(FM, 26), mix(ATM_R, INK, 0.15), al * q1b)
        paste_r(img, 424, 1494 + dy, "dibanding bulan tepat di atas kepala", font(FM, 24), MUTED, al * q1b)
    q3 = esmooth(seg(tl, 3.1, 3.7))
    if q3 > 0:
        _pill_c(img, 540, 1604 + dy, "SAMA SEPERTI MATAHARI SAAT TERBENAM", font(FS, 29),
                mix(accent, INK, 0.10), q3 * al, dot=True)
    if tl > 3.4:    # awan tipis mengalir, menjaga adegan tetap hidup
        for i in range(3):
            u = ((tl * 0.10 + i * 0.35) % 1.0)
            ax = 130 + 700 * u
            line_on(img, (ax, 690 + dy + i * 30), (ax + 150, 690 + dy + i * 30 + 6),
                    mix(WHITE, ATM_R, 0.35), 9, al * 0.30 * (1 - abs(u - 0.5) * 1.6))


def sc_rayleigh(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab cahaya: hamburan Rayleigh — biru tersebar, merah lolos."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.3, 0.9))
    if q > 0:
        _stage_rect(img, 108, 660 + dy, 972, 1180 + dy, 34, mix(WHITE, ATM_B, 0.05), al * q,
                 outline=mix(ATM_B, WHITE, 0.55), width=3)
        paste_c(img, 540, 712 + dy, "hamburan Rayleigh", font(FS, 31), mix(ATM_B, INK, 0.10), al * q)
        qq = esmooth(seg(tl, 0.7, 1.6))
        if qq > 0:
            _scatter_beam(img, 190, 960 + dy, 560, al * q * qq, tg, accent)
    q2 = esmooth(seg(tl, 1.9, 2.6))
    if q2 > 0:
        rows = [("SIANG", "matahari tinggi · langit biru", ATM_B, True),
                ("SENJA", "matahari rendah · memerah", ATM_R, False)]
        for i, (t1, t2, cc, tinggi) in enumerate(rows):
            x0 = 108 + i * 448
            _stage_rect(img, x0, 1220 + dy, x0 + 424, 1480 + dy, 28, mix(WHITE, cc, 0.07), al * q2,
                     outline=mix(cc, WHITE, 0.55), width=3)
            # panel langit kecil
            sx0, sy0, sx1, sy1 = x0 + 26, 1258 + dy, x0 + 398, 1372 + dy
            _sky_panel(img, sx0, sy0, sx1, sy1, 18, al * q2,
                       mix(ATM_B, WHITE, 0.22) if tinggi else mix(ATM_B, INK, 0.16),
                       mix(ATM_B, WHITE, 0.58) if tinggi else mix(ATM_R, WHITE, 0.22))
            sy = sy0 + 26 if tinggi else sy1 - 20
            ell(img, sx0 + 74 - 20, sy - 20, sx0 + 74 + 20, sy + 20, fill=mix(HOT_L, WHITE, 0.10),
                alpha=al * q2)
            for k in range(12):     # hamburan sesuai ketinggian matahari
                aa = k * math.pi / 6 + tg * 0.25
                rr0 = 26 + 30 * ((k % 3) / 2.0)
                dot_on(img, sx0 + 74 + rr0 * math.cos(aa), sy + rr0 * 0.5 * math.sin(aa), 4,
                       mix(cc, WHITE, 0.35), al * q2 * (0.45 if tinggi else 0.8))
            paste_r(img, x0 + 26, 1404 + dy, t1, font(FS, 28), mix(cc, INK, 0.08), al * q2)
            paste_r(img, x0 + 26, 1444 + dy, t2, font(FM, 24), MUTED, al * q2)
    q3 = esmooth(seg(tl, 2.9, 3.5))
    if q3 > 0:
        _pill_c(img, 540, 1540 + dy, "SATU FISIKA UNTUK LANGIT & BULAN", font(FS, 30),
                mix(accent, INK, 0.10), q3 * al, dot=True)
    if tl > 3.7:
        _scatter_beam(img, 190, 960 + dy, 560, al * 0.25, tg, accent)


def sc_eclipse(img, d, sc, tl, dur, tg, accent, al, dy):
    """Sebab 2: gerhana bulan total — atmosfer Bumi membelokkan cahaya merah ke bulan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.3, 0.9))
    if q > 0:
        _stage_rect(img, 108, 640 + dy, 972, 1220 + dy, 34, mix(WHITE, accent, 0.04), al * q,
                 outline=mix(accent, WHITE, 0.50), width=3)
        qq = esmooth(seg(tl, 0.7, 1.7))
        if qq > 0:
            mx = 1040 - 86 * clamp(seg(tl, 2.6, 7.0))     # bulan merayap masuk umbra
            _align_eclipse(img, al * q * qq, tg, accent, mx=mx)
    q2 = esmooth(seg(tl, 2.0, 2.7))
    if q2 > 0:
        _pill_c(img, 540, 1330 + dy, "SEOLAH SEMUA SENJA DI BUMI DIPROYEKSIKAN KE BULAN", font(FS, 26),
                mix(accent, INK, 0.10), q2 * al, dot=True)
        paste_c(img, 540, 1414 + dy, "tanpa atmosfer, bulan akan benar-benar gelap", font(FM, 26),
                MUTED, q2 * al)
    q3 = esmooth(seg(tl, 3.0, 3.6))
    if q3 > 0:
        _stage_rect(img, 206, 1470 + dy, 874, 1600 + dy, 28, mix(WHITE, MOON_R, 0.10), al * q3,
                 outline=mix(MOON_R, WHITE, 0.50), width=3)
        paste_c(img, 540, 1524 + dy, "bulan tidak berubah warna — cahaya kita yang tersaring",
                font(FM, 26), mix(MOON_R, INK, 0.12), al * q3)
    q4 = esmooth(seg(tl, 3.7, 4.3))
    if q4 > 0:      # fakta durasi: gerhana 3 Maret 2026 (BMKG)
        _lbl(img, 540, 1640 + dy, "TOTALITAS BISA ±59 MENIT · 3 MARET 2026", font(FM, 25),
                  mix(MOON_D, INK, 0.15), al * q4)
    if tl > 3.8:    # sinar merah yang dibelokkan atmosfer ikut berdenyut
        for i in range(3):
            ph = (tl * 0.4 + i * 0.33) % 1.0
            line_on(img, (300 + 40 * math.sin(tg * 1.2 + i), 1188 + dy + i * 30),
                    (760, 1188 + dy + i * 30), mix(ATM_R, WHITE, 0.30), 4,
                    al * (1 - ph) * 0.5, dash=16)
    if tl > 7.5:      # warnanya makin pekat makin dalam masuk bayangan
        kk = clamp(seg(tl, 7.5, 11.0))
        rmx = 1040 - 86 * kk
        ring_on(img, rmx, 900 + dy, 96 + 16 * math.sin(tg * 2.2), mix(MOON_D, WHITE, 0.25), 6,
                al * kk * 0.45, squash=1.0)


# ---------- EP24 bagian 2: adegan 5-7 (cincin merah, warna bervariasi, kapan lagi) ----------

def _earth_ring(img, cx, cy, r, alpha, tg):
    """Dilihat dari bulan: Bumi gelap dengan cincin atmosfer merah."""
    if alpha <= 0.01:
        return
    ell(img, cx - r, cy - r, cx + r, cy + r, fill=mix(INK, OCEAN_C, 0.22), alpha=alpha)
    for i in range(4):      # cincin merah
        ring_on(img, cx, cy, r + 12 + i * 13, mix(ATM_R, WHITE, 0.10 + i * 0.06), max(3, 12 - i * 2),
                alpha * (0.55 - i * 0.10), squash=1.0)
    # cahaya matahari dibelokkan mengelilingi Bumi
    for sgn in (-1, 1):
        pts = [(cx + sgn * (r + 30) * math.sin(math.pi * (0.12 + 0.76 * i / 13.0)),
                cy - (r + 30) * math.cos(math.pi * (0.12 + 0.76 * i / 13.0))) for i in range(14)]
        for i in range(len(pts) - 1):
            line_on(img, pts[i], pts[i + 1], mix(ATM_R, WHITE, 0.25), 5, alpha * 0.55, dash=11)
    _lbl(img, cx, cy + r + 96, "CINCIN MERAH DI KELILING BUMI", font(FM, 24), mix(ATM_R, INK, 0.15), alpha)


def _danjon_row(img, y, alpha, tg):
    """Skala Danjon 0-4: merah bulan bisa berbeda tiap gerhana."""
    if alpha <= 0.01:
        return
    cols = [mix(INK, MOON_D, 0.35), mix(MOON_D, INK, 0.25), MOON_D, MOON_R, mix(MOON_R, WARM_L, 0.35)]
    for i, c in enumerate(cols):
        x = 176 + i * 182
        _big_moon(img, x, y, 52, alpha, c, tg, glow=0.30, craters=False)
        paste_c(img, x, y + 96, str(i), font(FM, 25), mix(MUTED, INK, 0.25), alpha)
    _lbl(img, 812, y - 96, "SKALA DANJON", font(FM, 24), mix(MOON_R, INK, 0.20), alpha)


def sc_earthring(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 4: dari sisi bulan — Bumi gelap dengan cincin merah."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.3, 0.9))
    if q > 0:
        _stage_rect(img, 108, 660 + dy, 972, 1240 + dy, 34, mix(WHITE, accent, 0.05), al * q,
                 outline=mix(accent, WHITE, 0.50), width=3)
        qq = esmooth(seg(tl, 0.7, 1.6))
        if qq > 0:
            _earth_ring(img, 540, 940 + dy, 158, al * q * qq, tg)
    q2 = esmooth(seg(tl, 1.8, 2.5))
    if q2 > 0:
        _stage_rect(img, 108, 1290 + dy, 972, 1440 + dy, 30, mix(WHITE, ATM_R, 0.07), al * q2,
                 outline=mix(ATM_R, WHITE, 0.55), width=3)
        paste_c(img, 540, 1342 + dy, "yang kamu lihat adalah seluruh matahari terbit", font(FM, 26),
                mix(ATM_R, INK, 0.12), al * q2)
        paste_c(img, 540, 1396 + dy, "dan terbenam di Bumi, sekaligus", font(FM, 26),
                mix(ATM_R, INK, 0.12), al * q2)
    q3 = esmooth(seg(tl, 2.7, 3.3))
    if q3 > 0:
        _pill_c(img, 540, 1544 + dy, "TANPA ATMOSFER, BULAN AKAN HITAM TOTAL", font(FS, 29),
                mix(accent, INK, 0.10), q3 * al, dot=True)
    q4 = esmooth(seg(tl, 3.4, 4.0))
    if q4 > 0:      # bukti sejarah: Surveyor 3 memotret cincin ini dari bulan
        _stage_rect(img, 300, 1600 + dy, 780, 1680 + dy, 24, mix(WHITE, accent, 0.08), al * q4,
                 outline=mix(accent, WHITE, 0.55), width=3)
        dot_on(img, 356, 1640 + dy, 11, mix(accent, INK, 0.10), al * q4)
        paste_r(img, 384, 1626 + dy, "SURVEYOR 3 MEMOTRETNYA DARI BULAN", font(FM, 24),
                mix(accent, INK, 0.15), al * q4)
        paste_c(img, 540, 1700 + dy, "24 April 1967 · NASA", font(FR, 24), MUTED, al * q4 * 0.9)
    if tl > 3.5:    # cincin atmosfer berdenyut pelan
        for i in range(3):
            ph = (tl * 0.30 + i * 0.34) % 1.0
            ring_on(img, 540, 940 + dy, 208 + 62 * ph, mix(ATM_R, WHITE, 0.30), 3,
                    al * (1 - ph) * 0.20, squash=1.0)


def sc_colorvar(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 5: merahnya bisa beda tiap gerhana — debu, asap, abu vulkanik."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.3, 0.9))
    if q > 0:
        _stage_rect(img, 108, 660 + dy, 972, 1180 + dy, 34, mix(WHITE, MOON_R, 0.05), al * q,
                 outline=mix(MOON_R, WHITE, 0.55), width=3)
        paste_c(img, 540, 712 + dy, "warna merahnya bisa berbeda tiap gerhana", font(FS, 30),
                mix(MOON_R, INK, 0.10), al * q)
        qq = esmooth(seg(tl, 0.7, 1.5))
        if qq > 0:
            _danjon_row(img, 940 + dy, al * q * qq, tg)
    items = (("DEBU", "letusan gunung"), ("ASAP", "kebakaran besar"), ("POLUSI", "udara kota"))
    for i, (t1, t2) in enumerate(items):
        q2 = esmooth(seg(tl, 1.7 + i * 0.25, 2.2 + i * 0.25))
        if q2 <= 0:
            continue
        x0 = 108 + i * 296
        _stage_rect(img, x0, 1250 + dy, x0 + 272, 1400 + dy, 28, mix(WHITE, MUTED, 0.10), al * q2,
                 outline=mix(MUTED, WHITE, 0.45), width=3)
        dot_on(img, x0 + 40, 1300 + dy, 12, mix(MAROON_C, INK, 0.10), al * q2)
        paste_r(img, x0 + 66, 1284 + dy, t1, font(FS, 26), mix(MAROON_C, INK, 0.10), al * q2)
        paste_r(img, x0 + 66, 1338 + dy, t2, font(FM, 23), MUTED, al * q2)
    q3 = esmooth(seg(tl, 2.9, 3.5))
    if q3 > 0:
        _pill_c(img, 540, 1540 + dy, "MAKIN BANYAK PARTIKEL, MAKIN PEKAT MERAHNYA", font(FS, 28),
                mix(accent, INK, 0.10), q3 * al, dot=True)
    if tl > 3.7:    # kelima contoh warna berdenyut bergantian
        for i in range(5):
            ph = (tl * 0.55 + i * 0.2) % 1.0
            ring_on(img, 176 + i * 182, 940 + dy, 52 + 26 * ph, mix(MOON_R, WHITE, 0.30), 3,
                    al * (1 - ph) * 0.42, squash=1.0)


def sc_nextmoon(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 6: kapan lagi + aman dilihat mata telanjang."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.3, 0.95))
    if q > 0:
        _stage_rect(img, 108, 660 + dy, 972, 1080 + dy, 34, mix(WHITE, accent, 0.06), al * q,
                 outline=mix(accent, WHITE, 0.50), width=3)
        paste_c(img, 540, 718 + dy, "gerhana bulan total berikutnya dari Indonesia", font(FM, 26),
                mix(accent, INK, 0.15), al * q)
        qq = esmooth(seg(tl, 0.75, 1.5))
        if qq > 0:
            paste_c(img, 540, 838 + dy, "31 DESEMBER 2028", font(FB, 74), mix(accent, INK, 0.05), al * q * qq)
            _lbl(img, 540, 936 + dy, "CATAT TANGGALNYA", font(FM, 25), mix(accent, INK, 0.20), al * q * qq)
    rows = (("GERHANA BULAN", "aman dilihat mata telanjang", GREEN),
            ("GERHANA MATAHARI", "wajib pakai kacamata khusus", MAROON_C))
    for i, (t1, t2, cc) in enumerate(rows):
        q2 = esmooth(seg(tl, 1.7 + i * 0.35, 2.3 + i * 0.35))
        if q2 <= 0:
            continue
        y = 1180 + i * 170 + dy
        _stage_rect(img, 108, y - 66, 972, y + 66, 30, mix(WHITE, cc, 0.07), al * q2,
                 outline=mix(cc, WHITE, 0.55), width=3)
        dot_on(img, 156, y, 13, mix(cc, INK, 0.05), al * q2)
        paste_r(img, 190, y - 16, t1, font(FS, 29), mix(cc, INK, 0.08), al * q2)
        paste_r(img, 190, y + 26, t2, font(FM, 25), MUTED, al * q2)
        if i == 0:
            _big_moon(img, 880, y, 38, al * q2, MOON_R, tg, glow=0.30, craters=False)
            ring_on(img, 880, y, 44, mix(MOON_D, INK, 0.25), 3, al * q2 * 0.8, squash=1.0)
        else:
            ell(img, 842, y - 38, 918, y + 38, fill=mix(HOT_L, WHITE, 0.12), alpha=al * q2,
                outline=mix(HOT_L, INK, 0.25), width=4)
            for k in range(8):
                aa = k * math.pi / 4
                line_on(img, (880 + 46 * math.cos(aa), y + 46 * math.sin(aa)),
                        (880 + 62 * math.cos(aa), y + 62 * math.sin(aa)), mix(HOT_L, INK, 0.20), 4,
                        al * q2 * 0.85)
    q3 = esmooth(seg(tl, 2.9, 3.5))
    if q3 > 0:
        _pill_c(img, 540, 1570 + dy, "JADI KAPAN BULAN MERAH LAGI?", font(FS, 30),
                mix(accent, INK, 0.10), q3 * al, dot=True)
    if tl > 3.7:    # bulan merah kecil di samping pil penutup, ikut berdenyut
        _big_moon(img, 262, 1570 + dy, 34, al * 0.9, MOON_R, tg, glow=0.45, craters=False)
        ring_on(img, 262, 1570 + dy, 40 + 10 * abs(math.sin(tg * 2.0)), mix(MOON_D, INK, 0.25), 3,
                al * 0.75, squash=1.0)
        for i in range(2):
            ph = (tl * 0.45 + i * 0.5) % 1.0
            ring_on(img, 540, 838 + dy, 110 + 130 * ph, mix(accent, WHITE, 0.40), 4,
                    al * (1 - ph) * 0.35, squash=0.55)


VISUALS.update({
    "intro_cat": sc_intro_cat,
    "meow_human": sc_meow_human,
    "kitten": sc_kitten,
    "dialect": sc_dialect,
    "meaning": sc_meaning,
    "night": sc_night,
    "senior": sc_senior,
})


VISUALS.update({
    "intro_redmoon": sc_intro_redmoon,
    "horizon": sc_horizon,
    "rayleigh": sc_rayleigh,
    "eclipse": sc_eclipse,
    "earthring": sc_earthring,
    "colorvar": sc_colorvar,
    "nextmoon": sc_nextmoon,
})


# =============================================================================
#  EP25 — "Kenapa Mimpi Cepat Lupa?"  (7 adegan visual)
# =============================================================================
NIGHT = (26, 32, 58)
def _nop_panel(*a, **k):
    """Panel/kotak transparan lama — dinonaktifkan (bentuknya seperti handphone)."""
    return None


def _lbl(img, cx, cy, text, f, col, alpha=1.0):
    """Label polos: teks langsung di atas bidang — tanpa kotak transparan."""
    if alpha > 0.02:
        paste_c(img, cx, cy, text, f, col, alpha)


SOFT = (238, 242, 250)


def _fit_line(text, name, size, maxw=900):
    """Kecilkan ukuran font sampai teks muat di lebar aman."""
    while size > 30:
        f = font(name, size)
        if tw(text, f) <= maxw:
            return f
        size -= 6
    return font(name, size)


def sc_intro_dream(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: orang tertidur — gelembung mimpi naik lalu menguap satu per satu."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.18 + i * 0.20, 0.82 + i * 0.20))
        if q <= 0:
            continue
        f = _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66)
        paste_c(img, 540, (516 + i * 96) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q1 = esmooth(seg(tl, 0.5, 0.95))
    if q1 > 0:
        _pill_c(img, 540, 676 + dy, "MIMPI PUNYA MASA SIMPAN", font(FS, 30), mix(accent, INK, 0.10),
                q1 * al, dot=True)
    px0, py0, px1, py1 = 104, 748, 976, 1584
    q2 = esmooth(seg(tl, 0.30, 1.0))
    if q2 <= 0.02:
        return
    rrect_on(img, px0, py0, px1, py1, 46, NIGHT, q2 * al)
    for k in range(26):     # bintang halus di langit kamar
        sx = px0 + 40 + ((k * 151) % 872)
        sy = py0 + 34 + ((k * 197) % 300)
        tw_ = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(tg * 1.7 + k * 1.7))
        dot_on(img, sx, sy, 3.2, mix(NIGHT, WHITE, 0.78), q2 * al * tw_ * 0.85)
    # --- orang tidur: bantal, kepala, selimut yang naik-turun saat bernapas ---
    fx, fy = 470, py1 - 150
    rrect_on(img, fx - 268, fy - 74, fx - 140, fy + 6, 22, mix(NIGHT, WHITE, 0.17), q2 * al)
    ell(img, fx - 138, fy - 104, fx - 14, fy + 20, fill=mix(NIGHT, WHITE, 0.20), alpha=q2 * al,
        outline=mix(NIGHT, WHITE, 0.34), width=3)
    for sgn in (-1, 1):     # mata terpejam
        line_on(img, (fx - 76 + sgn * 17 - 15, fy - 42), (fx - 76 + sgn * 17 + 15, fy - 42),
                mix(NIGHT, WHITE, 0.62), 4, q2 * al * 0.9)
    br = 1 + 0.03 * math.sin(tg * 1.5)     # napas
    hgt = 74 * br
    pts = [(fx - 20, fy + 26)]
    for j in range(25):
        u = j / 24.0
        pts.append((fx - 20 + u * 330, fy + 26 - hgt * math.sin(u * math.pi * 0.92)))
    pts.append((fx + 310, fy + 26))
    pts += [(fx + 310, fy + 96), (fx - 20, fy + 96)]
    poly_on(img, pts, mix(NIGHT, WHITE, 0.13), q2 * al, outline=mix(NIGHT, WHITE, 0.30), width=3)
    rrect_on(img, fx - 330, fy + 96, fx + 330, fy + 132, 18, mix(NIGHT, WHITE, 0.09), q2 * al)
    # --- gelembung mimpi naik dari kepala lalu menguap ---
    for k in range(5):
        ph = (tl * 0.32 + k * 0.2) % 1.0
        bx = (fx - 76) - 40 + k * 82 + 26 * math.sin(tg * 0.8 + k)
        by = (fy - 150) - ph * 330
        life = 1 - ph
        rad = 30 + 9 * (k % 3)
        col = mix(NIGHT, WHITE, 0.55) if k % 2 else mix(accent, WHITE, 0.62)
        ell(img, bx - rad * 0.78, by - rad * 0.78, bx + rad * 0.78, by + rad * 0.78, fill=col,
            alpha=q2 * al * life * 0.32, outline=mix(NIGHT, WHITE, 0.42), width=3)
        if k % 2 == 0:
            star4(img, bx, by, rad * 0.5, mix(NIGHT, WHITE, 0.9), q2 * al * life * 0.85)
        else:
            dot_on(img, bx, by, rad * 0.24, mix(NIGHT, WHITE, 0.9), q2 * al * life * 0.85)
        if ph > 0.7:        # pecah jadi serpihan kecil = lupa
            for j in range(7):
                aa = j * 0.9 + tl * 1.3
                dot_on(img, bx + rad * 1.3 * math.cos(aa), by + rad * 1.3 * math.sin(aa), 3.4,
                       mix(NIGHT, WHITE, 0.7), q2 * al * (1 - (ph - 0.7) / 0.3) * 0.75)
    # --- jam: masa simpan lima menit ---
    cxp, cyp = px1 - 116, py1 - 116
    ring_on(img, cxp, cyp, 54, mix(NIGHT, WHITE, 0.44), 4, q2 * al * 0.9)
    ang = -math.pi / 2 + (tl % 5.0) / 5.0 * 2 * math.pi
    line_on(img, (cxp, cyp), (cxp + 34 * math.cos(ang), cyp + 34 * math.sin(ang)),
            mix(NIGHT, WHITE, 0.88), 4, q2 * al * 0.9)
    line_on(img, (cxp, cyp), (cxp + 22 * math.cos(-1.1), cyp + 22 * math.sin(-1.1)),
            mix(NIGHT, WHITE, 0.88), 3, q2 * al * 0.9)
    _lbl(img, cxp, cyp - 92, "5 MENIT", font(FR, 24), mix(NIGHT, WHITE, 0.85), q2 * al * 0.9)
    q4 = esmooth(seg(tl, 3.0, 3.6))
    if q4 > 0:
        _pill_c(img, 540, 1660 + dy, "OTAK SENGAJA MELUPAKAN", font(FS, 29), mix(accent, INK, 0.10),
                q4 * al, dot=True)


def sc_rem_sleep(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 1: satu malam tidur — gelombang otak & fase REM yang makin panjang."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.25, 0.9))
    if q <= 0.02:
        return
    x0, x1, base = 250, 930, 1300
    _stage_rect(img, 130, 830 + dy, 950, 1560 + dy, 40, mix(WHITE, accent, 0.05), al * q * 0.95,
             outline=mix(accent, WHITE, 0.55), width=3)
    # legenda fase (kolom kiri, tidak menutupi batang)
    _lbl(img, 190, 1006 + dy, "REM", font(FS, 25), mix(accent, INK, 0.08), al * q)
    _lbl(img, 300, 1480 + dy, "NYENYAK", font(FS, 26), mix(BLUE, INK, 0.08), al * q * 0.95)
    # gelombang otak sepanjang malam (amplitudo besar di fase REM)
    rem_u = [0.12 + i * 0.185 for i in range(5)]
    pts = []
    for j in range(97):
        u = j / 96.0
        x = x0 + u * (x1 - x0)
        amp = 20
        for ru in rem_u:
            amp += 70 * math.exp(-((u - ru) ** 2) / 0.0014)
        y = 930 + dy - amp * (0.55 * math.sin(u * 26.0 + tg * 3.2) + 0.45)
        pts.append((x, y))
    for j in range(len(pts) - 1):
        line_on(img, pts[j], pts[j + 1], mix(accent, INK, 0.10), 4, al * q * 0.85)
    # batang tidur nyenyak (biru, makin pendek) + REM (aksen, makin panjang)
    for i in range(5):
        bx = x0 + 8 + i * 136
        qq = esmooth(seg(tl, 0.5 + i * 0.12, 1.1 + i * 0.12))
        if qq <= 0:
            continue
        hh = (240 - i * 32) * qq
        rrect_on(img, bx, base + 96 + dy - hh, bx + 104, base + 96 + dy, 22, mix(BLUE, WHITE, 0.55),
                 al * q * qq * 0.9, outline=mix(BLUE, INK, 0.25), width=3)
        hR = (54 + i * 28) * qq
        rrect_on(img, bx, base - 30 + dy - hR, bx + 104, base - 30 + dy, 22, mix(accent, WHITE, 0.22),
                 al * q * qq, outline=mix(accent, INK, 0.18), width=3)
        paste_c(img, bx + 52, base - 40 + dy - hR + 26, f"{i+1}", font(FS, 26),
                mix(accent, INK, 0.20), al * q * qq)
    # mata bergerak cepat saat REM berlangsung
    act = int((tg * 0.42) % 5)
    ex = x0 + 60 + act * 136
    qe = esmooth(seg(tl, 0.9 + act * 0.12, 1.4 + act * 0.12))
    if qe > 0:
        _eye(img, ex, 900 + dy, 26, mix(accent, INK, 0.05), tg, al * q * qe)
        dot_on(img, ex + 15 * math.sin(tg * 9.0), 900 + dy, 9, mix(accent, INK, 0.05), al * q * qe)
    q3 = esmooth(seg(tl, 2.2, 2.8))
    if q3 > 0:
        _lbl(img, 540, 1500 + dy, "REM TIAP ± 90 MENIT", font(FS, 25), mix(accent, INK, 0.10),
                  al * q * q3)
    q4 = esmooth(seg(tl, 2.8, 3.4))
    if q4 > 0:
        _pill_c(img, 540, 1640 + dy, "OTAK AKTIF · TUBUH LUMPUH", font(FS, 29), mix(accent, INK, 0.10),
                q4 * al, dot=True)


def sc_two_stores(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 2: hipokampus (sementara) -> korteks (permanen); pintunya ditutup saat REM."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.25, 0.9))
    if q <= 0.02:
        return
    y0, y1 = 1020 + dy, 1360 + dy
    for bx0, bx1, t1, t2, cc in ((140, 470, "HIPOKAMPUS", "gudang sementara", BLUE),
                                 (610, 940, "KORTEKS", "gudang permanen", GREEN)):
        _stage_rect(img, bx0, y0, bx1, y1, 34, mix(WHITE, cc, 0.10), al * q,
                 outline=mix(cc, WHITE, 0.45), width=3)
        paste_c(img, (bx0 + bx1) / 2, y0 + 118, t1, font(FS, 31), mix(cc, INK, 0.06), al * q)
        paste_c(img, (bx0 + bx1) / 2, y0 + 214, t2, font(FM, 25), MUTED, al * q)
        for k in range(6):      # isi gudang
            dot_on(img, bx0 + 40 + k * 52, y0 + 62, 11, mix(cc, WHITE, 0.35), al * q * 0.9)
    _lbl(img, 540, y0 - 74, "PINTU MEMORI", font(FS, 25), mix(accent, INK, 0.12), al * q)
    gate = esmooth(seg(tl, 2.4, 3.0))
    col_ar = mix(GREEN, INK, 0.05) if gate < 0.5 else mix(MUTED, INK, 0.12)
    for yy in (y0 + 120, y0 + 250):
        _arrow_on(img, (478, yy), (602, yy), col_ar, 6, al * q * 0.9)
    for k in range(4):      # paket memori
        ph = (tl * 0.55 + k * 0.25) % 1.0
        if gate < 0.5:
            dot_on(img, 478 + ph * 124, y0 + 120, 12, mix(GREEN, INK, 0.05), al * q * 0.95)
        else:
            xx = 478 + min(ph, 0.55) * 124
            dot_on(img, xx, y0 + 120, 12, mix(MUTED, WHITE, 0.25),
                   al * q * (1 - max(0.0, (ph - 0.55) / 0.45)) * 0.85)
    if gate > 0:        # palang turun menutup jalur memori
        hh = 176 * gate
        rrect_on(img, 512, y0 + 186 - hh / 2, 568, y0 + 186 + hh / 2, 16, mix(accent, INK, 0.12),
                 al * q * gate, outline=mix(accent, WHITE, 0.32), width=3)
        for k in range(3):
            yy = y0 + 186 - hh / 2 + (k + 1) * hh / 4.0
            line_on(img, (520, yy), (560, yy), mix(WHITE, accent, 0.35), 5, al * q * gate * 0.9)
        _lbl(img, 540, y0 + 350, "JALUR DIMATIKAN", font(FS, 25), mix(accent, INK, 0.12), al * q * gate)
    else:
        _lbl(img, 540, y0 + 350, "SIANG: TERSAMBUNG", font(FS, 25), mix(GREEN, INK, 0.10), al * q)
    q4 = esmooth(seg(tl, 3.2, 3.8))
    if q4 > 0:
        _pill_c(img, 540, 1640 + dy, "TANPA PEMINDAHAN, TIDAK ADA INGATAN", font(FS, 28),
                mix(accent, INK, 0.10), q4 * al, dot=True)


def sc_mch_msg(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 3: neuron MCH menahan gudang memori; noradrenalin nyaris nol saat REM."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.25, 0.9))
    if q <= 0.02:
        return
    cx, cy = 428, 1148 + dy
    # --- siluet otak: lingkaran berombak + otak kecil + batang otak ---
    pts = []
    for j in range(73):
        th = 2 * math.pi * j / 72
        rr = 246 * (0.93 + 0.09 * math.sin(3 * th + 0.4) + 0.05 * math.sin(5 * th + 1.1))
        pts.append((cx + rr * math.cos(th) * 1.04, cy + rr * math.sin(th) * 0.84 - 10 * math.cos(th)))
    poly_on(img, pts, mix(WHITE, accent, 0.09), al * q * 0.96, outline=mix(accent, WHITE, 0.38), width=5)
    ell(img, cx + 52, cy + 112, cx + 190, cy + 224, fill=mix(WHITE, accent, 0.15), alpha=al * q * 0.92,
        outline=mix(accent, WHITE, 0.45), width=4)
    poly_on(img, [(cx - 34, cy + 160), (cx + 22, cy + 160), (cx + 10, cy + 282), (cx - 20, cy + 282)],
            mix(WHITE, accent, 0.13), al * q * 0.92, outline=mix(accent, WHITE, 0.45), width=4)
    for k in range(5):      # lekuk permukaan otak
        yy = cy - 150 + k * 62
        wpts = [(cx - 172 + j * 34, yy - 10 + 9 * math.sin(j * 1.1 + k)) for j in range(11)]
        for j in range(len(wpts) - 1):
            line_on(img, wpts[j], wpts[j + 1], mix(accent, WHITE, 0.60), 3, al * q * 0.45)
    # --- hippocampus: pita melengkung (gudang memori), menyala lalu meredup ---
    dim = 1 - 0.5 * esmooth(seg(tl, 1.8, 3.0))
    hpts = []
    for j in range(19):
        u = j / 18.0
        hpts.append((cx - 150 + 288 * u, cy + 34 - 16 * u + 44 * math.sin(math.pi * u)))
    for j in range(len(hpts) - 1):
        line_on(img, hpts[j], hpts[j + 1], mix(BLUE, WHITE, 0.10 + 0.16 * (1 - dim)), 24,
                al * q * dim * 0.95)
    _lbl(img, cx - 40, cy + 150, "GUDANG MEMORI", font(FS, 24), mix(BLUE, INK, 0.15), al * q * dim)
    # --- neuron MCH di bawah otak, akson menuju hippocampus ---
    nx, ny = cx - 104, cy + 268
    ax_pts = []
    for j in range(25):
        u = j / 24.0
        ax_pts.append((nx + 214 * u + 16 * math.sin(u * 5.0 + tg * 0.6),
                       ny - 226 * u + 18 * math.sin(u * 4.0)))
    for j in range(len(ax_pts) - 1):
        line_on(img, ax_pts[j], ax_pts[j + 1], mix(accent, INK, 0.10), 6, al * q * 0.85)
    for k in range(4):      # sinyal "lupakan" berjalan ke hippocampus
        ph = (tl * 0.40 + k * 0.25) % 1.0
        px, py = ax_pts[int(ph * 24)]
        dot_on(img, px, py, 9, mix(accent, WHITE, 0.12), al * q * 0.95)
    dot_on(img, nx, ny, 30, mix(accent, INK, 0.05), al * q)
    _lbl(img, nx - 4, ny + 70, "NEURON MCH", font(FS, 25), mix(accent, INK, 0.15), al * q)
    # --- meter noradrenalin (kanan) ---
    mx, my0, my1 = 872, 1010 + dy, 1330 + dy
    _lbl(img, mx, my0 - 62, "NORADRENALIN", font(FS, 20), mix(accent, INK, 0.15), al * q)
    _stage_rect(img, mx - 40, my0, mx + 40, my1, 26, mix(WHITE, accent, 0.06), al * q,
             outline=mix(accent, WHITE, 0.5), width=3)
    lvl = 0.94 - 0.88 * esmooth(seg(tl, 1.2, 2.6))
    _thermo(img, mx, my0, my1, lvl, al * q * 0.98)
    qq = esmooth(seg(tl, 2.4, 3.0))
    if qq > 0:
        counter_c(img, mx, my1 + 66, tl, 2.4, 3.2, 100, 0, font(FB, 53), mix(accent, INK, 0.05), al * qq,
                  suf="%")
        _lbl(img, mx, my1 + 124, "SAAT REM", font(FR, 23), mix(accent, INK, 0.15), al * q * qq)
    _lbl(img, 540, 898 + dy, "PENELITIAN - JURNAL SCIENCE 2019", font(FS, 25), mix(accent, INK, 0.15),
              al * q * 0.9)


def sc_minutes5(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 4: 50% isi mimpi hilang dalam 5 menit, 90% dalam 10 menit."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.25, 0.9))
    if q <= 0.02:
        return
    # awan mimpi yang memudar di atas
    fade = 1 - 0.75 * esmooth(seg(tl, 1.0, 3.6))
    for k in range(4):
        r = 42 + k * 34
        ell(img, 300 - r, 930 + dy - r * 0.55, 300 + r, 930 + dy + r * 0.55,
            fill=mix(accent, WHITE, 0.74), alpha=al * q * fade * (0.45 - k * 0.08))
    _lbl(img, 300, 930 + dy, "MIMPI", font(FS, 25), mix(accent, INK, 0.12), al * q * fade)
    for i, (cx_, frac, lab) in enumerate(((330, 0.50, "50%"), (750, 0.90, "90%"))):
        qq = esmooth(seg(tl, 0.6 + i * 0.5, 1.4 + i * 0.5))
        if qq <= 0:
            continue
        cy_ = 1220 + dy
        R = 148
        ell(img, cx_ - R, cy_ - R, cx_ + R, cy_ + R, fill=mix(accent, WHITE, 0.84), alpha=al * q * qq)
        f = frac * qq
        pts = [(cx_, cy_)]
        for j in range(int(2 + f * 64) + 1):
            aa = -math.pi / 2 + (j / 64.0) * 2 * math.pi * f
            pts.append((cx_ + R * math.cos(aa), cy_ + R * math.sin(aa)))
        poly_on(img, pts, mix(accent, INK, 0.05), al * q * qq)
        ell(img, cx_ - R * 0.62, cy_ - R * 0.62, cx_ + R * 0.62, cy_ + R * 0.62, fill=WHITE,
            alpha=al * q * qq)
        paste_c(img, cx_, cy_ - 8, lab, font(FB, 62), mix(accent, INK, 0.05), al * q * qq)
        paste_c(img, cx_, cy_ + 46, "hilang", font(FM, 26), MUTED, al * q * qq)
        _lbl(img, cx_, cy_ + R + 66, "5 MENIT" if i == 0 else "10 MENIT", font(FS, 25),
                  mix(accent, INK, 0.12), al * q * qq)
    line_on(img, (170, 1520 + dy), (910, 1520 + dy), mix(accent, WHITE, 0.5), 5, al * q * 0.7, dash=16)
    for i, yy in enumerate((1580 + dy, 1665 + dy)):
        qq = esmooth(seg(tl, 2.4 + i * 0.4, 3.0 + i * 0.4))
        if qq <= 0:
            continue
        if i == 0:
            _pill_c(img, 540, yy, "BANGUN DARI REM: MASIH INGAT", font(FS, 28), mix(GREEN, INK, 0.10),
                    qq * al, dot=True)
        else:
            _pill_c(img, 540, yy, "BANGUN DARI TIDUR DALAM: LENYAP", font(FS, 28), mix(MUTED, INK, 0.12),
                    qq * al, dot=True)


def sc_why_forget(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 5: penyaring — yang penting disimpan, sisanya dibuang, emosi dilembutkan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.25, 0.9))
    if q <= 0.02:
        return
    top, neck, bot = 940 + dy, 1290 + dy, 1400 + dy
    wall_l = [(268, top), (452, neck), (470, bot)]
    wall_r = [(812, top), (628, neck), (610, bot)]
    poly_on(img, [(268, top), (812, top), (628, neck), (452, neck)], mix(WHITE, accent, 0.07),
            al * q * 0.95)
    line_on(img, (268, top), (812, top), mix(accent, INK, 0.18), 7, al * q * 0.9)
    for a, b in ((wall_l[0], wall_l[1]), (wall_l[1], wall_l[2])):
        line_on(img, a, b, mix(accent, INK, 0.20), 8, al * q * 0.9)
    for a, b in ((wall_r[0], wall_r[1]), (wall_r[1], wall_r[2])):
        line_on(img, a, b, mix(accent, INK, 0.20), 8, al * q * 0.9)
    rrect_on(img, 448, neck, 632, neck + 26, 12, mix(accent, WHITE, 0.55), al * q * 0.9,
             outline=mix(accent, INK, 0.18), width=3)
    # butiran: sebagian besar menabrak dinding lalu menguap, yang penting lolos ke bak
    for k in range(38):
        seed = ((k * 97) % 997) / 997.0
        penting = (k % 5 == 0)
        ph = (tl * (0.34 + seed * 0.30) + seed) % 1.0
        yy = 860 + dy + ph * 520
        span = max(46.0, 262 * (1 - (yy - top) / max(1.0, neck - top))) if yy < neck else 52
        xx = 540 + (seed - 0.5) * 2 * span * (0.30 if penting else 1.0)
        if penting:
            dot_on(img, xx, yy, 13, mix(AMBER, INK, 0.05), al * q * 0.95)
        else:
            inside = top < yy < neck
            dot_on(img, xx, yy, 8, mix(accent, WHITE, 0.55), al * q * (0.85 if inside else 0.30))
    # bak "disimpan"
    q2 = esmooth(seg(tl, 1.7, 2.3))
    if q2 > 0:
        _stage_rect(img, 380, 1440 + dy, 700, 1546 + dy, 26, mix(WHITE, GREEN, 0.14), al * q * q2,
                 outline=mix(GREEN, WHITE, 0.45), width=3)
        paste_c(img, 540, 1478 + dy, "YANG PENTING DISIMPAN", font(FS, 25), mix(GREEN, INK, 0.06),
                al * q * q2)
        for k in range(4):
            dot_on(img, 466 + k * 50, 1518 + dy, 11, mix(GREEN, INK, 0.10), al * q * q2 * 0.95)
    # debu sisanya keluar ke kanan
    q3 = esmooth(seg(tl, 2.2, 2.8))
    if q3 > 0:
        for k in range(11):
            aa = k * 0.58 + tl * 0.5
            dot_on(img, 760 + 70 * math.cos(aa) + 40 * k * 0.4, 1180 + dy + 54 * math.sin(aa * 1.3), 7,
                   mix(MUTED, WHITE, 0.35), al * q * q3 * 0.7)
        _lbl(img, 884, 990 + dy, "SISANYA DIBUANG", font(FR, 23), mix(MUTED, INK, 0.15), al * q * q3)
    # emosi dilembutkan: gelombang yang makin rata
    q4 = esmooth(seg(tl, 2.7, 3.3))
    if q4 > 0:
        damp = 1 - 0.8 * esmooth(seg(tl, 3.0, 4.4))
        amp0 = 30 * damp
        for i in range(3):
            pts = [(200 + j * 34, 1700 + dy + amp0 * math.sin(j * 0.9 + tl * 2.0 + i * 0.7)) for j in range(21)]
            for j in range(len(pts) - 1):
                line_on(img, pts[j], pts[j + 1], mix(accent, INK, 0.12), 5, al * q * q4 * (0.75 - i * 0.18))
        _lbl(img, 540, 1620 + dy, "BEBAN EMOSI DILEMBUTKAN", font(FS, 24), mix(accent, INK, 0.15),
                  al * q * q4)


def sc_recall_tips(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 6: tiga langkah mengingat mimpi + grafik latihan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.25, 0.9))
    if q <= 0.02:
        return
    steps = ((1, "mata tetap tutup, jangan bergerak", "eye"),
             (2, "ulangi satu kata kunci mimpi", "echo"),
             (3, "tulis cepat satu menit pertama", "note"))
    for i, (no, txt, ic) in enumerate(steps):
        qq = esmooth(seg(tl, 0.6 + i * 0.55, 1.2 + i * 0.55))
        if qq <= 0:
            continue
        y = 950 + i * 182 + dy
        _stage_rect(img, 130, y - 72, 950, y + 72, 30, mix(WHITE, accent, 0.06), al * q * qq,
                 outline=mix(accent, WHITE, 0.5), width=3)
        rrect_on(img, 154, y - 52, 262, y + 52, 24, mix(accent, WHITE, 0.22), al * q * qq,
                 outline=mix(accent, INK, 0.12), width=3)
        if ic == "eye":     # mata terpejam
            ell(img, 182, y - 19, 234, y + 19, outline=mix(accent, INK, 0.10), width=4, alpha=al * q * qq)
            line_on(img, (186, y), (230, y), mix(accent, INK, 0.10), 4, al * q * qq)
        elif ic == "echo":  # busur konsentris
            for k in range(3):
                ring_on(img, 208, y, 13 + k * 15, mix(accent, INK, 0.10), 4, al * q * qq * (0.9 - k * 0.22))
        else:               # buku catatan
            _stage_rect(img, 184, y - 32, 234, y + 32, 10, mix(WHITE, accent, 0.35), al * q * qq,
                     outline=mix(accent, INK, 0.15), width=3)
            for k in range(3):
                line_on(img, (194, y - 18 + k * 18), (224, y - 18 + k * 18), mix(accent, INK, 0.25), 3,
                        al * q * qq)
        paste_r(img, 292, y, txt, font(FM, 28), mix(accent, INK, 0.10), al * q * qq)
        _lbl(img, 884, y, f"{no}", font(FS, 26), mix(accent, INK, 0.12), al * q * qq)
    q4 = esmooth(seg(tl, 2.6, 3.2))
    if q4 > 0:
        for i, (h, lab) in enumerate(((86, "jarang"), (164, "kadang"), (250, "rutin"))):
            qq = esmooth(seg(tl, 2.8 + i * 0.25, 3.3 + i * 0.25))
            if qq <= 0:
                continue
            x = 210 + i * 180
            base = 1780 + dy
            rrect_on(img, x, base - h * qq, x + 104, base, 20, mix(accent, WHITE, 0.30), al * q * qq,
                     outline=mix(accent, INK, 0.12), width=3)
            paste_c(img, x + 52, base + 38, lab, font(FR, 24), MUTED, al * q * qq)
        _lbl(img, 822, 1660 + dy, "MAKIN SERING DICATAT", font(FR, 23), mix(GREEN, INK, 0.12),
                  al * q * q4)


VISUALS.update({
    "intro_dream": sc_intro_dream,
    "rem_sleep": sc_rem_sleep,
    "two_stores": sc_two_stores,
    "mch_msg": sc_mch_msg,
    "minutes5": sc_minutes5,
    "why_forget": sc_why_forget,
    "recall_tips": sc_recall_tips,
})


def _selftest():
    """Adegan baru harus ada di registry dan bisa dipanggil tanpa galat."""
    names = ["intro_dream", "rem_sleep", "two_stores", "mch_msg", "minutes5", "why_forget", "recall_tips"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA MIMPI", "CEPAT LUPA?"], "accent": "#3B4E8C"}
    for n in names:
        for tl in (0.5, 2.0, 3.5, 4.6):
            VISUALS[n](img, d, sc, tl, 5.0, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep25: 7 adegan OK")


if __name__ == "__main__":
    _selftest()


# =============================================================================
#  EP26 v2 — "Kenapa Dinosaurus Punah?"
#  Perubahan besar sesuai permintaan:
#   * TIDAK ada kotak/panel putih transparan (yang tampak seperti ponsel)
#   * semua elemen jauh LEBIH BESAR, mengisi layar 9:16 (x 60..1020, y 700..1700)
#   * lebih banyak elemen visual per adegan (timeline, globe, peta, pohon keluarga)
#   * animasi berkelanjutan (tidak ada bagian adegan yang beku)
# =============================================================================
SPACE = (18, 22, 38)
ROCK = (96, 90, 84)
LAVA = (206, 92, 40)
ASH = (120, 112, 104)
STAGE = mix(WHITE, CREAM, 0.35)      # warna "panggung" lembut (bukan kotak)


def _dw(tl, dur, a, b):
    """Jendela animasi relatif terhadap durasi adegan."""
    return seg(tl, a * dur, b * dur)


def _dust(img, x0, y0, x1, y1, n, tg, al, col, up=False, wob=14):
    """Partikel halus melayang — penjaga gerak agar adegan tidak pernah beku."""
    for k in range(n):
        sd = ((k * 137) % 991) / 991.0
        ph = (tg * (0.035 + sd * 0.03) + sd) % 1.0
        px = x0 + sd * (x1 - x0) + wob * math.sin(tg * 0.8 + k)
        py = (y1 - ph * (y1 - y0)) if up else (y0 + ph * (y1 - y0))
        dot_on(img, px, py, 3.5 + (k % 3) * 2.2, col, al * (1 - ph) * 0.75)


def _person_scale(img, x, y, h, col, alpha):
    """Siluet manusia kecil — pembanding ukuran."""
    hr = h * 0.17
    dot_on(img, x, y - h + hr, hr, col, alpha)
    line_on(img, (x, y - h + hr * 2.1), (x, y - h * 0.42), col, max(2, int(h * 0.13)), alpha)
    line_on(img, (x, y - h * 0.42), (x - h * 0.20, y), col, max(2, int(h * 0.10)), alpha)
    line_on(img, (x, y - h * 0.42), (x + h * 0.20, y), col, max(2, int(h * 0.10)), alpha)
    line_on(img, (x - h * 0.24, y - h * 0.74), (x + h * 0.24, y - h * 0.74), col,
            max(2, int(h * 0.08)), alpha)


def _tree(img, x, ybase, h, col, alpha, tg=0.0, k=0):
    sway = 8 * math.sin(tg * 0.8 + k)
    line_on(img, (x, ybase), (x + sway, ybase - h), col, max(3, int(h * 0.10)), alpha)
    for j in range(5):
        aa = -1.25 + j * 0.62
        line_on(img, (x + sway, ybase - h * 0.60),
                (x + sway + h * 0.72 * math.cos(aa), ybase - h * 0.60 - h * 0.46), col,
                max(2, int(h * 0.07)), alpha * 0.9)


def _dino_long(img, x, y, s, col, al, tg=0.0):
    """Siluet dinosaurus leher panjang (untuk skala & suasana)."""
    if al <= 0.02:
        return
    line_on(img, (x - 0.10 * s, y - 0.42 * s), (x, y - 0.62 * s), col, int(0.10 * s), al)
    ell(img, x - 0.07 * s, y - 0.72 * s, x + 0.07 * s, y - 0.58 * s, fill=col, alpha=al)
    ell(img, x - 0.04 * s, y - 0.62 * s, x - 0.015 * s, y - 0.595 * s, fill=mix(col, WHITE, 0.55),
        alpha=al * 0.9)
    ell(img, x - 0.26 * s, y - 0.44 * s, x + 0.22 * s, y - 0.20 * s, fill=col, alpha=al)
    line_on(img, (x - 0.22 * s, y - 0.30 * s), (x - 0.40 * s, y - 0.18 * s - 0.05 * s * math.sin(tg * 0.8)), col,
            int(0.07 * s), al)
    for k in range(4):
        kx = x - 0.18 * s + k * 0.12 * s
        line_on(img, (kx, y - 0.20 * s), (kx, y), col, int(0.07 * s), al)


def _dino_big(img, x, y, s, col, al, tg=0.0):
    """Siluet dinosaurus pemangsa (untuk skala & suasana)."""
    if al <= 0.02:
        return
    ell(img, x - 0.30 * s, y - 0.42 * s, x + 0.26 * s, y - 0.16 * s, fill=col, alpha=al)
    ell(img, x + 0.16 * s, y - 0.52 * s, x + 0.40 * s, y - 0.26 * s, fill=col, alpha=al)
    poly_on(img, [(x + 0.36 * s, y - 0.34 * s), (x + 0.52 * s, y - 0.30 * s), (x + 0.38 * s, y - 0.24 * s)],
            col, al)
    for k in range(4):
        poly_on(img, [(x + 0.30 * s + k * 0.045 * s, y - 0.28 * s), (x + 0.325 * s + k * 0.045 * s, y - 0.36 * s),
                      (x + 0.35 * s + k * 0.045 * s, y - 0.28 * s)], mix(WHITE, col, 0.25), al)
    line_on(img, (x - 0.28 * s, y - 0.34 * s), (x - 0.52 * s, y - 0.46 * s - 0.04 * s * math.sin(tg * 1.1)), col,
            int(0.09 * s), al)
    for k in range(2):
        kx = x - 0.06 * s + k * 0.20 * s
        line_on(img, (kx, y - 0.18 * s), (kx, y - 0.02 * s), col, int(0.09 * s), al)


def sc_intro_asteroid(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: batu raksasa membelah langit purba, lalu menghantam ufuk."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.18 + i * 0.20, 0.82 + i * 0.20))
        if q <= 0:
            continue
        f = _fit_line(l, FB if i == 0 else FS, 118 if i == 0 else 68, 1000)
        paste_c(img, 540, (500 + i * 104) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q1 = esmooth(seg(tl, 0.6, 1.2))
    if q1 > 0:
        _pill_c(img, 540, 676 + dy, "66 JUTA TAHUN LALU", font(FS, 26), mix(accent, INK, 0.10), q1 * al,
                dot=True)
    q2 = esmooth(_dw(tl, dur, 0.05, 0.14))
    if q2 <= 0.02:
        return
    # ---- langit penuh lebar: pita gradasi (bukan kotak) ----
    sky_top, sky_bot = 820, 1500
    for i in range(14):
        k0 = i / 14.0
        yy0 = sky_top + (sky_bot - sky_top) * k0
        yy1 = sky_top + (sky_bot - sky_top) * (i + 1) / 14.0
        cc = mix(SPACE, LAVA, 0.06 + 0.42 * k0) if k0 > 0.55 else mix(SPACE, INK, 0.05 * k0)
        rrect_on(img, 0, yy0, 1080, yy1 + 4, 0, cc, q2 * al * 0.98)
    for i in range(9):                      # tepi atas langit melebur ke latar
        rrect_on(img, 0, sky_top - 90 + i * 10, 1080, sky_top - 80 + i * 10, 0, SPACE,
                 q2 * al * 0.11 * (i + 1) / 9.0)
    for k in range(34):                     # bintang berkelip
        sx = 30 + ((k * 157) % 1020)
        sy = sky_top + 20 + ((k * 173) % 380)
        tw_ = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(tg * 1.8 + k * 1.6))
        dot_on(img, sx, sy, 3.4, mix(SPACE, WHITE, 0.85), q2 * al * tw_ * 0.9)
    hy = sky_bot - 200                      # garis ufuk
    for i in range(12):                     # tanah: makin ke bawah makin gelap, sampai tepi bawah
        yy0 = hy + (1770 - hy) * i / 12.0
        rrect_on(img, 0, yy0, 1080, hy + (1770 - hy) * (i + 1) / 12.0 + 4, 0,
                 mix(SPACE, INK, 0.30 + 0.03 * i), q2 * al * 0.98)
    for i in range(9):                      # tepi bawah melebur ke latar
        rrect_on(img, 0, 1770 + i * 18, 1080, 1788 + i * 18, 0, mix(SPACE, INK, 0.60),
                 q2 * al * 0.10 * (1 - i / 9.0))
    for k in range(7):                      # hutan purba
        _tree(img, 90 + k * 150, hy + 16, 150 + (k % 3) * 60, mix(SPACE, WHITE, 0.24), q2 * al, tg, k)
    prog = esmooth(_dw(tl, dur, 0.12, 0.42))
    ax = 1010 - prog * 700
    ay = sky_top + 150 + prog * (hy - sky_top - 230)
    if prog > 0.001:
        tail = [(ax + 32 * j, ay - 19 * j + 6 * math.sin(tg * 2 + j)) for j in range(11)]
        _trail(img, tail, mix(LAVA, WHITE, 0.35), q2 * al * 0.8, width=32, tail=10)
        for i in range(3):                  # selubung api (lebih rapat)
            rr = 96 - i * 20
            ell(img, ax - rr, ay - rr, ax + rr, ay + rr, fill=mix(LAVA, WHITE, 0.26 + i * 0.22),
                alpha=q2 * al * (0.12 + i * 0.13))
        ell(img, ax - 74, ay - 74, ax + 74, ay + 74, fill=mix(ROCK, WHITE, 0.34), alpha=q2 * al,
            outline=mix(LAVA, WHITE, 0.55), width=7)
        for i in range(4):                  # kawah & retakan pijar
            aa = i * 1.6 + tg * 0.4
            line_on(img, (ax + 44 * math.cos(aa), ay + 44 * math.sin(aa)),
                    (ax - 40 * math.cos(aa), ay - 40 * math.sin(aa)), mix(LAVA, WHITE, 0.40), 4,
                    q2 * al * 0.85)
        dot_on(img, ax - 34, ay - 30, 26, mix(ROCK, INK, 0.22), q2 * al * 0.8)
        dot_on(img, ax + 30, ay + 26, 17, mix(ROCK, INK, 0.22), q2 * al * 0.8)
    q3 = esmooth(_dw(tl, dur, 0.42, 0.50)) * (1 - esmooth(_dw(tl, dur, 0.56, 0.68)))
    if q3 > 0:                              # kilatan tumbukan di ufuk
        ell(img, ax - 240 * q3, hy - 130 * q3, ax + 240 * q3, hy + 80 * q3,
            fill=mix(LAVA, WHITE, 0.45), alpha=q2 * al * q3 * 0.6)
        for i in range(3):
            rrect_on(img, ax - 420 * q3, hy - 6 + i * 14, ax + 420 * q3, hy + 10 + i * 14, 10,
                     mix(LAVA, WHITE, 0.35), q2 * al * q3 * (0.30 - i * 0.08))
        ring_on(img, ax, hy, 120 + 420 * (1 - q3), mix(LAVA, WHITE, 0.30), 7, q2 * al * q3 * 0.5, squash=0.42)
    qa = esmooth(_dw(tl, dur, 0.46, 0.62))
    if qa > 0:                              # abu & bara naik sampai akhir
        for k in range(30):
            sd = ((k * 137) % 991) / 991.0
            ph = (tg * (0.03 + sd * 0.03) + sd) % 1.0
            ex = ax - 220 + sd * 1000
            ey = hy + 30 - ph * 470
            cc = mix(LAVA, ASH, 0.30 + 0.5 * sd) if k % 3 else mix(ASH, WHITE, 0.40)
            dot_on(img, ex + 22 * math.sin(tg * 0.7 + k), ey, 5 + (k % 3) * 3.5, cc,
                   q2 * al * qa * (1 - ph) * 0.8)
        for i in range(4):                  # awan abu lonjong
            yy = hy - 170 - i * 72 + 12 * math.sin(tg * 0.5 + i)
            ex = 240 + i * 190 + 36 * math.sin(tg * 0.35 + i)
            ell(img, ex - 210, yy - 22, ex + 210, yy + 22, fill=mix(ASH, SPACE, 0.42),
                alpha=q2 * al * (0.24 - i * 0.04) * qa)
    # ---- strip garis waktu (elemen baru) ----
    q4 = esmooth(_dw(tl, dur, 0.58, 0.74))
    if q4 > 0:
        y0 = 1620
        line_on(img, (90, y0), (990, y0), mix(accent, INK, 0.25), 6, q4 * al, dash=18)
        dot_on(img, 90, y0, 16, mix(LAVA, INK, 0.10), q4 * al)
        dot_on(img, 990, y0, 16, mix(accent, INK, 0.05), q4 * al)
        _lbl(img, 250, y0 - 58, "TUMBUKAN", font(FS, 24), mix(LAVA, INK, 0.10), q4 * al)
        _lbl(img, 880, y0 - 58, "SEKARANG", font(FS, 24), mix(accent, INK, 0.05), q4 * al)
        _lbl(img, 540, y0 + 62, "66 JUTA TAHUN", font(FM, 26), MUTED, q4 * al)


def sc_rock_scale(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 1: seberapa besar & seberapa cepat batu itu (elemen diperbesar)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    qa = esmooth(_dw(tl, dur, 0.08, 0.26))
    bx, by, R = 300, 1030 + dy, 178
    if qa > 0:
        _glow(img, bx - R * 1.7, by - R * 1.7, bx + R * 1.7, by + R * 1.7, mix(accent, WHITE, 0.35),
              q * qa * 0.35, layers=3)
        ell(img, bx - R, by - R, bx + R, by + R, fill=mix(ROCK, WHITE, 0.34), alpha=q * qa,
            outline=mix(ROCK, INK, 0.34), width=7)
        for k in range(6):                  # kawah permukaan
            aa = k * 1.15 + tg * 0.3
            rr = 34 + (k % 3) * 40
            rr2 = 26 + (k % 2) * 20
            ell(img, bx + rr * math.cos(aa) - rr2, by + rr * math.sin(aa) - rr2,
                bx + rr * math.cos(aa) + rr2, by + rr * math.sin(aa) + rr2,
                fill=mix(ROCK, INK, 0.30), alpha=q * qa * 0.92)
        _lbl(img, bx, by + R + 66, "BATU 10–15 KM", font(FS, 27), mix(accent, INK, 0.06), q * qa)
        ph = ((tl * 0.42) % 1.0)            # gelombang energi
        ring_on(img, bx, by, R + 20 + 220 * ph, mix(accent, WHITE, 0.35), 4, q * qa * (1 - ph) * 0.5)
        _person_scale(img, 520, 1130 + dy, 80, mix(INK, MUTED, 0.35), q * qa * 0.95)
        _lbl(img, 520, 1192 + dy, "MANUSIA 1,8 M", font(FM, 22), MUTED, q * qa * 0.95)
    qb = esmooth(_dw(tl, dur, 0.22, 0.40))
    if qb > 0:
        gx, gy, gh = 860, 1130 + dy, 520 * qb
        poly_on(img, [(gx - 190, gy), (gx, gy - gh), (gx + 190, gy)], mix(ASH, WHITE, 0.52), q * qb,
                outline=mix(ASH, INK, 0.22), width=5)
        poly_on(img, [(gx - 34, gy - gh * 0.97), (gx + 12, gy - gh * 0.90), (gx + 40, gy - gh * 0.83),
                      (gx + 62, gy - gh * 0.90), (gx + 96, gy - gh * 0.97)], mix(WHITE, ASH, 0.30),
                q * qb * 0.95)
        _lbl(img, gx, gy + 62, "EVEREST 8,8 KM", font(FS, 26), mix(accent, INK, 0.10), q * qb)
        for i in range(3):                  # awan melintas
            cx3 = gx - 260 + ((tl * 30 + i * 170) % 520)
            rrect_on(img, cx3, gy - 400 + i * 46, cx3 + 170, gy - 378 + i * 46, 14,
                     mix(WHITE, ASH, 0.35), q * qb * 0.32)
    qc = esmooth(_dw(tl, dur, 0.40, 0.56))
    if qc > 0:                              # pita kecepatan penuh lebar
        yy = 1440 + dy
        line_on(img, (70, yy), (1010, yy), mix(accent, WHITE, 0.45), 6, q * qc, dash=20)
        for k in range(6):
            xx = 70 + k * 188
            line_on(img, (xx, yy - 22), (xx, yy + 22), mix(accent, WHITE, 0.45), 5, q * qc * 0.9)
        for d0 in (0.0, 0.34, 0.68):        # tiga batu melesat
            sx = 70 + ((tl * 0.5 + d0) % 1.0) * 940
            _trail(img, [(sx - 34 * j, yy) for j in range(6)], mix(accent, INK, 0.10), q * qc * 0.8,
                   width=16, tail=6)
            dot_on(img, sx, yy, 13, mix(accent, INK, 0.05), q * qc)
        _lbl(img, 700, yy - 104, "20 KM / DETIK", font(FS, 31), mix(accent, INK, 0.05), q * qc)
        _lbl(img, 700, yy - 56, "= 72.000 KM / JAM", font(FM, 23), MUTED, q * qc)
    qd = esmooth(_dw(tl, dur, 0.60, 0.78))
    if qd > 0:                              # batang energi besar (elemen baru)
        yy = 1600 + dy
        _lbl(img, 340, yy - 62, "ENERGI TUMBUKAN", font(FS, 24), mix(accent, INK, 0.10), q * qd)
        rrect_on(img, 70, yy - 22, 1010, yy + 22, 22, mix(CREAM, INK, 0.10), q * qd)
        k = eo(_dw(tl, dur, 0.62, 0.86))
        rrect_on(img, 70, yy - 22, 70 + 940 * k, yy + 22, 22, mix(LAVA, INK, 0.05), q * qd)
        _lbl(img, 540, yy + 86, "100 JUTA MEGATON TNT", font(FS, 28), mix(LAVA, INK, 0.08), q * qd * k)


def sc_impact_cross(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 2: potongan melintang laut — batu menghujam, kawah raksasa, tsunami."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    sea, floor = 1160 + dy, 1500 + dy
    rrect_on(img, 0, sea, 1080, floor + 120, 0, mix(accent, WHITE, 0.70), q * al * 0.80)
    rrect_on(img, 0, floor, 1080, 1700, 0, mix(ROCK, WHITE, 0.62), q * al * 0.9)
    _lbl(img, 250, sea - 46, "LAUT DANGKAL", font(FS, 24), mix(accent, INK, 0.12), q * al * 0.95)
    for j in range(42):                     # riak laut
        xx = 10 + j * 26
        line_on(img, (xx, sea + 8 + 8 * math.sin(tg * 1.3 + j * 0.6)),
                (xx + 26, sea + 8 + 8 * math.sin(tg * 1.3 + (j + 1) * 0.6)),
                mix(accent, WHITE, 0.40), 3, q * al * 0.55)
    _dust(img, 60, sea + 40, 1020, floor - 30, 20, tg, q * al * 0.6, mix(accent, WHITE, 0.85), up=True, wob=14)
    ix = 640
    qi = esmooth(_dw(tl, dur, 0.10, 0.28))
    if qi > 0:
        p1 = (ix + 420 - 420 * qi, sea - 420 + 420 * qi)
        _trail(img, [(p1[0] + 38 * j, p1[1] - 30 * j) for j in range(8)], mix(LAVA, WHITE, 0.30),
               q * al * qi * 0.85, width=24, tail=8)
        dot_on(img, p1[0], p1[1], 22, mix(ROCK, INK, 0.22), q * al * qi)
    qe = esmooth(_dw(tl, dur, 0.28, 0.42))
    if qe > 0:
        for i in range(3):
            ph = ((tl - 0.28 * dur) * 0.55 + i * 0.33) % 1.0
            ring_on(img, ix, sea, 70 + 300 * ph, mix(LAVA, WHITE, 0.35), 5, q * al * (1 - ph) * 0.5, squash=0.5)
        ell(img, ix - 130 * qe, sea - 210 * qe, ix + 130 * qe, sea + 60 * qe,
            fill=mix(LAVA, WHITE, 0.42), alpha=q * al * qe * 0.4)
        for k in range(9):                  # batuan terlempar (di dalam laut)
            aa = -0.55 - k * 0.24
            rr = 190 + k * 52 + 14 * math.sin(tg * 1.3 + k)
            px2 = min(max(ix + rr * math.cos(aa), 90), 1000)
            py2 = min(max(sea + rr * math.sin(aa), sea - 480), floor - 40)
            dot_on(img, px2, py2, 11, mix(LAVA, INK, 0.15), q * al * qe * 0.9)
    qk = esmooth(_dw(tl, dur, 0.42, 0.60))
    if qk > 0:                              # cekungan kawah raksasa
        w = 330 * qk
        poly_on(img, [(540 - w, floor + 4), (540 - w * 0.70, floor + 34 * qk), (540 - w * 0.34, floor + 62 * qk),
                      (540 + w * 0.34, floor + 62 * qk), (540 + w * 0.70, floor + 34 * qk), (540 + w, floor + 4)],
                mix(ROCK, INK, 0.34), q * al * qk, outline=mix(ROCK, INK, 0.18), width=5)
        poly_on(img, [(540 - w * 0.70, floor + 18), (540 - w * 0.34, floor + 50), (540 + w * 0.34, floor + 50),
                      (540 + w * 0.70, floor + 18)], mix(LAVA, WHITE, 0.50), q * al * qk * 0.7)
        line_on(img, (540 - w * 1.35, floor + 34), (540 + w * 1.35, floor + 34), mix(accent, INK, 0.16), 6,
                q * al * qk * 0.9)
        _lbl(img, 540, floor + 146, "KAWAH 180 KM", font(FS, 28), mix(accent, INK, 0.06), q * al * qk)
    qt = esmooth(_dw(tl, dur, 0.58, 0.80))
    if qt > 0:                              # tsunami menjalar
        for i in range(3):
            pts = []
            for j in range(42):
                pts.append((10 + j * 26, sea - 10 - 56 * math.exp(-((j - 12 - i * 5 - (tl * 7) % 26) ** 2) / 16)))
            for j in range(len(pts) - 1):
                line_on(img, pts[j], pts[j + 1], mix(accent, INK, 0.05), 6, q * al * qt * 0.85)
        _lbl(img, 300, floor + 214, "YUCATAN · MEKSIKO", font(FS, 24), MUTED, q * al * qt)
    # ---- inset globe (elemen baru) ----
    qg = esmooth(_dw(tl, dur, 0.12, 0.30))
    if qg > 0:
        gx, gy, gr = 830, 900 + dy, 118
        ell(img, gx - gr, gy - gr, gx + gr, gy + gr, fill=mix(OCEAN_C, WHITE, 0.30), alpha=q * al * qg * 0.85,
            outline=mix(OCEAN_C, INK, 0.30), width=5)
        for k in range(3):                  # garis lintang + benua kasar
            yy = gy - 40 + k * 40
            line_on(img, (gx - math.sqrt(max(0, gr * gr - (yy - gy) ** 2)), yy),
                    (gx + math.sqrt(max(0, gr * gr - (yy - gy) ** 2)), yy), mix(OCEAN_C, INK, 0.25), 2,
                    q * al * qg * 0.7)
        poly_on(img, [(gx - 60, gy - 12), (gx - 18, gy - 30), (gx + 16, gy - 4), (gx - 26, gy + 26)],
                mix(GREEN, WHITE, 0.35), q * al * qg * 0.95)
        dot_on(img, gx + 22, gy + 18, 13 + 3 * math.sin(tg * 3.0), mix(LAVA, INK, 0.05), q * al * qg)
        _lbl(img, gx, gy + gr + 42, "TITIK TUMBUKAN", font(FS, 23), mix(accent, INK, 0.08), q * al * qg)


def sc_impact_winter(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 3: debu menahan matahari — siang jadi gelap, suhu jatuh."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    dark = esmooth(_dw(tl, dur, 0.08, 0.72))
    for i in range(12):                     # langit penuh lebar makin gelap
        k0 = i / 12.0
        c1 = mix(CREAM, SPACE, 0.10 + 0.72 * dark)
        rrect_on(img, 0, 780 + k0 * 620, 1080, 780 + (k0 + 1) * 620 + 4, 0,
                 mix(c1, accent, 0.08 * (1 - k0)), q * al * 0.96)
    sx, sy = 360, 1010 + dy
    _sun(img, sx, sy, 152, mix(LAVA, WHITE, 0.18), tg, q * al * (1 - 0.72 * dark))
    ell(img, sx - 112, sy - 112, sx + 112, sy + 112, fill=mix(LAVA, WHITE, 0.42),
        alpha=q * al * (0.30 + 0.40 * dark))
    for i in range(3):                      # lapisan debu di depan matahari
        ring_on(img, sx, sy, 150 + i * 34, mix(LAVA, WHITE, 0.55 - i * 0.10), 6 - i,
                q * al * dark * (0.45 - i * 0.10))
    qd = esmooth(_dw(tl, dur, 0.10, 0.44))
    if qd > 0:                              # tabir debu & sulfur
        for k in range(90):
            sd = ((k * 131) % 997) / 997.0
            ph = (tg * (0.02 + sd * 0.03) + sd) % 1.0
            px = 20 + ((k * 89) % 1040)
            py = 800 + dy + ph * 640
            dot_on(img, px + 22 * math.sin(tg * 0.6 + k), py, 3.5 + (k % 3) * 2.6,
                   mix(ASH, WHITE, 0.30 + 0.3 * (k % 3) / 2), q * al * qd * 0.6)
        for i in range(4):                  # lapisan debu tebal
            yy = 880 + dy + i * 120 + 14 * math.sin(tg * 0.5 + i)
            rrect_on(img, -20, yy, 1100, yy + 26, 13, mix(ASH, SPACE, 0.30), q * al * qd * (0.20 - i * 0.03))
    qth = esmooth(_dw(tl, dur, 0.22, 0.52))
    if qth > 0:                             # termometer besar
        lvl = 0.88 - 0.74 * esmooth(_dw(tl, dur, 0.30, 0.82))
        _thermo(img, 930, 900 + dy, 1480 + dy, lvl, q * al)
        line_on(img, (930, 1400), (930, 1400 - 470 * lvl), mix(LAVA, INK, 0.05), 16, q * al * 0.95)
        _lbl(img, 720, 900 + dy, "SUHU BUMI", font(FS, 25), mix(WHITE, accent, 0.30), q * al)
        for k in range(4):
            line_on(img, (902, 960 + k * 130), (950, 960 + k * 130), mix(WHITE, accent, 0.35), 4,
                    q * al * 0.6)
    qt1 = esmooth(_dw(tl, dur, 0.44, 0.60))
    if qt1 > 0:
        _lbl(img, 380, 1560 + dy, "DEBU & SULFUR MENAHAN CAHAYA", font(FS, 25), mix(WHITE, accent, 0.35),
             q * al * qt1)
    # ---- garis waktu kegelapan (elemen baru) ----
    qt2 = esmooth(_dw(tl, dur, 0.60, 0.80))
    if qt2 > 0:
        y0 = 1660
        line_on(img, (90, y0), (990, y0), mix(accent, INK, 0.25), 6, q * al * qt2, dash=18)
        for k in range(4):
            xx = 90 + k * 300
            line_on(img, (xx, y0 - 14), (xx, y0 + 14), mix(accent, INK, 0.25), 5, q * al * qt2)
            _lbl(img, xx + (40 if k == 0 else 0), y0 + 52, f"{k * 5} THN" if k else "MULAI",
                 font(FM, 22), MUTED, q * al * qt2)
        kd = eo(_dw(tl, dur, 0.62, 0.92))
        rrect_on(img, 90, y0 - 8, 90 + 900 * kd, y0 + 8, 8, mix(LAVA, INK, 0.08), q * al * qt2)
        _lbl(img, 540, y0 - 66, "SIANG JADI SEPERTI MALAM · ± 15 TAHUN", font(FS, 24),
             mix(WHITE, accent, 0.30), q * al * qt2)


def sc_chain_collapse(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 4: rantai makanan runtuh dari bawah ke atas (baris penuh lebar)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    # cahaya matahari yang meredup
    ql = esmooth(_dw(tl, dur, 0.05, 0.20))
    if ql > 0:
        dim = 1 - 0.88 * esmooth(_dw(tl, dur, 0.45, 0.90))
        cxs = 540
        for j in range(7):
            line_on(img, (cxs, 790 + dy), (cxs + (j - 3) * 92, 950 + dy), mix(LAVA, WHITE, 0.35), 8,
                    q * al * ql * dim * 0.85)
        _lbl(img, cxs, 760 + dy, "CAHAYA MATAHARI", font(FS, 23), mix(LAVA, INK, 0.10), q * al * ql * dim)
    rows = (("TUMBUHAN", "berhenti berfotosintesis", GREEN, "leaf"),
            ("PEMAKAN TUMBUHAN", "kehabisan makanan", AMBER, "herb"),
            ("PEMANGSA", "kehabisan mangsa", RED, "carn"))
    for i, (t1, t2, cc, ic) in enumerate(rows):
        qa = esmooth(_dw(tl, dur, 0.08 + i * 0.07, 0.22 + i * 0.07))
        if qa <= 0:
            continue
        qb = 1 - esmooth(_dw(tl, dur, 0.58 + i * 0.07, 0.78 + i * 0.07))
        y = 1060 + i * 190 + dy
        rrect_on(img, 60, y - 84, 1020, y + 84, 30, mix(WHITE, cc, 0.12),
                 q * al * qa * (0.35 + 0.65 * qb) * (0.92 + 0.08 * math.sin(tg * 1.7 + i)),
                 outline=mix(cc, WHITE, 0.42), width=4)
        rrect_on(img, 88, y - 62, 214, y + 62, 26, mix(cc, WHITE, 0.55), q * al * qa * (0.55 + 0.45 * qb))
        aa_ = q * al * qa * (0.45 + 0.55 * qb)
        if ic == "leaf":
            poly_on(img, [(106, y + 16), (150, y - 46), (196, y + 8), (150, y + 40)], mix(cc, INK, 0.35), aa_)
            line_on(img, (150, y - 46), (150, y + 46), mix(cc, INK, 0.30), 4, aa_)
            for k in range(3):
                line_on(img, (150, y - 16 + k * 18), (186, y - 30 + k * 18), mix(cc, INK, 0.22), 3, aa_)
        elif ic == "herb":
            ell(img, 100, y - 20, 196, y + 26, fill=mix(cc, INK, 0.35), alpha=aa_)
            line_on(img, (188, y - 14), (222, y - 50), mix(cc, INK, 0.40), 13, aa_)
            ell(img, 210, y - 66, 252, y - 26, fill=mix(cc, INK, 0.45), alpha=aa_)
            for k in range(4):
                line_on(img, (108 + k * 24, y + 20), (108 + k * 24, y + 56), mix(cc, INK, 0.30), 6, aa_)
        else:
            poly_on(img, [(98, y + 24), (116, y - 32), (156, y - 12), (182, y - 38), (216, y + 6), (188, y + 28)],
                    mix(cc, INK, 0.35), aa_)
            for k in range(4):
                poly_on(img, [(148 + k * 16, y + 2), (156 + k * 16, y + 22), (140 + k * 16, y + 22)],
                        mix(WHITE, cc, 0.25), aa_)
            line_on(img, (100, y + 2), (58, y - 26), mix(cc, INK, 0.28), 9, aa_)
        paste_r(img, 250, y - 26, t1, font(FS, 27), mix(cc, INK, 0.06), q * al * qa * (0.35 + 0.65 * qb))
        paste_r(img, 250, y + 28, t2, font(FM, 23), MUTED, q * al * qa * (0.30 + 0.70 * qb))
        for k in range(9):                  # mata rantai meredup + berdenyut
            pul = 0.55 + 0.45 * math.sin(tg * 2.4 + k * 0.9 + i)
            dot_on(img, 700 + k * 36, y, 12, mix(cc, WHITE, 0.30), q * al * qa * qb * pul * 0.9)
    _dust(img, 80, 960 + dy, 1000, 1500 + dy, 26, tg, q * al * 0.5, mix(MUTED, WHITE, 0.55), wob=20)
    # ---- hasil: 75% (elemen baru) ----
    qz = esmooth(_dw(tl, dur, 0.80, 0.94))
    if qz > 0:
        y0 = 1660
        _lbl(img, 540, y0 - 66, "75% SPESIES HILANG", font(FB, 34), mix(RED, INK, 0.10), qz * al)
        rrect_on(img, 60, y0 - 26, 1020, y0 + 26, 20, mix(RED, WHITE, 0.88), qz * al)
        k = eo(_dw(tl, dur, 0.82, 0.98))
        rrect_on(img, 60, y0 - 26, 60 + (960 * 0.75 + 60) * k, y0 + 26, 20, mix(RED, INK, 0.05), qz * al * 0.92)


def sc_evidence(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 5: bukti di batuan — iridium, butiran asteroid, kawah Chicxulub."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    lx0, lx1 = 70, 600
    qa = esmooth(_dw(tl, dur, 0.08, 0.26))
    layers = ((120, mix(CREAM, AMBER, 0.18)), (104, mix(CREAM, WHITE, 0.32)), (30, mix(INK, accent, 0.35)),
              (104, mix(CREAM, WHITE, 0.16)), (128, mix(CREAM, AMBER, 0.30)))
    yy = 900 + dy
    for hh, cc in layers:
        if qa > 0:
            rrect_on(img, lx0, yy, lx1, yy + hh * qa - 6, 10, cc, q * al * 0.96,
                     outline=mix(cc, INK, 0.25), width=3)
        yy += (hh * qa)
    key_y = 900 + dy + (120 + 104) * qa + 16 * qa
    qb = esmooth(_dw(tl, dur, 0.18, 0.34))
    if qb > 0:                              # lapisan iridium berkilau
        for k in range(22):
            px = lx0 + 22 + ((k * 71) % (lx1 - lx0 - 44))
            tw_ = 0.45 + 0.55 * math.sin(tg * 3.2 + k * 1.3)
            dot_on(img, px, key_y + 7 * math.sin(k * 2.1), 4 + 3 * tw_, mix(WHITE, accent, 0.35),
                   q * al * qb * (0.5 + 0.5 * tw_))
        _lbl(img, 335, key_y - 76, "LAPISAN IRIDIUM", font(FS, 25), mix(accent, INK, 0.05), q * al * qb)
        _lbl(img, 335, key_y + 96, "66 JUTA TAHUN", font(FM, 23), MUTED, q * al * qb)
    scan = 900 + dy + ((tg * 60) % 460)     # pita pemindai
    for i in range(5):
        rrect_on(img, lx0 - 20, scan + i * 13, lx1 + 20, scan + 13 + i * 13, 7, mix(accent, WHITE, 0.45),
                 q * al * (0.15 - i * 0.024))
    qc = esmooth(_dw(tl, dur, 0.36, 0.54))
    if qc > 0:                              # kaca pembesar besar
        mx, my = 820, 1010 + dy
        mr = 168 + 6 * math.sin(tg * 1.4)
        ring_on(img, mx, my, mr, mix(accent, INK, 0.10), 11, q * al * qc)
        ell(img, mx - mr + 10, my - mr + 10, mx + mr - 10, my + mr - 10, fill=mix(CREAM, WHITE, 0.45),
            alpha=q * al * qc * 0.92)
        for k in range(14):
            aa = k * 2.399 + tg * 0.85
            rr = 30 + (k % 4) * 34
            dot_on(img, mx + rr * math.cos(aa), my + rr * math.sin(aa) * 0.72, 9,
                   mix(accent, WHITE, 0.30), q * al * qc)
        line_on(img, (mx - mr, my + mr * 0.62), (lx1 + 6, key_y), mix(accent, INK, 0.20), 5, q * al * qc * 0.85)
        _lbl(img, mx, my - mr - 46, "BUTIRAN DARI ASTEROID", font(FS, 23), mix(accent, INK, 0.08), q * al * qc)
    qe = esmooth(_dw(tl, dur, 0.58, 0.76))
    if qe > 0:                              # kawah Chicxulub + skala
        cx2, cy2 = 350, 1580 + dy
        ring_on(img, cx2, cy2, 132, mix(accent, INK, 0.12), 7, q * al * qe)
        ring_on(img, cx2, cy2, 86, mix(accent, INK, 0.16), 5, q * al * qe * 0.85)
        dot_on(img, cx2, cy2, 22, mix(accent, INK, 0.05), q * al * qe)
        ph2 = ((tl * 0.5) % 1.0)
        ring_on(img, cx2, cy2, 46 + 150 * ph2, mix(accent, WHITE, 0.40), 4, q * al * qe * (1 - ph2) * 0.55)
        _lbl(img, cx2, cy2 + 176, "KAWAH CHICXULUB", font(FS, 22), mix(accent, INK, 0.06), q * al * qe)
    qf = esmooth(_dw(tl, dur, 0.74, 0.90))
    if qf > 0:                              # sebaran temuan di banyak titik (elemen baru)
        base_y = 1620 + dy
        _lbl(img, 760, base_y - 96, "IRIDIUM DITEMUKAN DI EROPA, ASIA,", font(FM, 21), MUTED, q * al * qf)
        _lbl(img, 760, base_y - 62, "AMERIKA, AFRIKA · SELURUH DUNIA", font(FM, 21), MUTED, q * al * qf)
        for k in range(7):
            xx = 600 + k * 68
            tw_ = 0.5 + 0.5 * math.sin(tg * 2.6 + k)
            dot_on(img, xx, base_y, 12, mix(accent, WHITE, 0.35), q * al * qf * (0.5 + 0.5 * tw_))


def sc_survivors(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 6: siapa yang bertahan — dan burung = dinosaurus yang hidup."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    qa = esmooth(_dw(tl, dur, 0.05, 0.24))
    if qa > 0:                              # donat 75% besar
        cx2, cy2, R = 300, 1130 + dy, 210
        ell(img, cx2 - R, cy2 - R, cx2 + R, cy2 + R, fill=mix(RED, WHITE, 0.84), alpha=q * al * qa)
        pts = [(cx2, cy2)]
        for j in range(int(2 + 0.75 * qa * 72) + 1):
            aa = -math.pi / 2 + (j / 72.0) * 2 * math.pi * 0.75 * qa
            pts.append((cx2 + R * math.cos(aa), cy2 + R * math.sin(aa)))
        poly_on(img, pts, mix(RED, INK, 0.05), q * al * qa)
        ell(img, cx2 - R * 0.50, cy2 - R * 0.50, cx2 + R * 0.50, cy2 + R * 0.50, fill=WHITE,
            alpha=q * al * qa)
        paste_c(img, cx2, cy2 - 12, "75%", font(FB, 66), mix(RED, INK, 0.05), q * al * qa)
        paste_c(img, cx2, cy2 + 52, "spesies punah", font(FM, 23), MUTED, q * al * qa)
        ring_on(img, cx2, cy2, R + 14 + 18 * (0.5 + 0.5 * math.sin(tg * 1.3)), mix(RED, WHITE, 0.55), 4,
                q * al * qa * 0.45)
        phb = ((tl * 0.45) % 1.0)
        ring_on(img, cx2, cy2, 60 + 230 * phb, mix(RED, WHITE, 0.30), 4, q * al * (1 - phb) * 0.45)
    qb = esmooth(_dw(tl, dur, 0.18, 0.38))
    if qb > 0:                              # burung mengepak (lebih besar)
        for k in range(5):
            bx = 620 + k * 82 + 40 * math.sin(tg * 0.45 + k * 1.1)
            byb = 900 + dy + 30 * math.sin(tg * 1.4 + k)
            flap = 0.45 + 0.55 * math.sin(tg * 3.4 + k)
            line_on(img, (bx - 62, byb), (bx - 8, byb - 30 * flap), mix(accent, INK, 0.10), 8, q * al * qb)
            line_on(img, (bx - 8, byb - 30 * flap), (bx + 48, byb), mix(accent, INK, 0.10), 8, q * al * qb)
        _lbl(img, 780, 990 + dy, "BURUNG", font(FS, 25), mix(accent, INK, 0.06), q * al * qb)
        for k in range(3):                  # mamalia kecil
            mx = 660 + k * 130
            my = 1150 + dy + 12 * math.sin(tg * 1.6 + k)
            ell(img, mx - 52, my - 32, mx + 34, my + 22, fill=mix(accent, INK, 0.14), alpha=q * al * qb)
            ell(img, mx + 28, my - 46, mx + 76, my - 2, fill=mix(accent, INK, 0.20), alpha=q * al * qb)
            ell(img, mx + 36, my - 62, mx + 56, my - 40, fill=mix(accent, INK, 0.22), alpha=q * al * qb)
            ell(img, mx + 60, my - 64, mx + 80, my - 42, fill=mix(accent, INK, 0.22), alpha=q * al * qb)
            dot_on(img, mx + 48, my - 28, 4.5, mix(WHITE, accent, 0.35), q * al * qb)
            for j in range(3):
                line_on(img, (mx - 30 + j * 24, my + 18), (mx - 30 + j * 24, my + 52),
                        mix(accent, INK, 0.22), 6, q * al * qb)
            line_on(img, (mx - 50, my - 4), (mx - 92 + 10 * math.sin(tg * 2.6 + k), my + 24),
                    mix(accent, INK, 0.22), 5, q * al * qb)
        _lbl(img, 780, 1348 + dy, "MAMALIA KECIL · KURA-KURA · BUAYA", font(FS, 22),
             mix(accent, INK, 0.08), q * al * qb)
    _dust(img, 120, 900 + dy, 1000, 1400 + dy, 26, tg, q * al * 0.42, mix(accent, WHITE, 0.78), wob=22)
    # ---- pohon keluarga: dinosaurus -> burung (elemen baru) ----
    qc = esmooth(_dw(tl, dur, 0.44, 0.64))
    if qc > 0:
        y0 = 1450 + dy
        line_on(img, (200, y0), (560, y0), mix(accent, INK, 0.30), 7, q * al * qc)
        line_on(img, (560, y0), (830, y0 - 90), mix(accent, INK, 0.30), 7, q * al * qc)
        dot_on(img, 200, y0, 15, mix(MUTED, INK, 0.20), q * al * qc)
        dot_on(img, 830, y0 - 90, 17, mix(accent, INK, 0.05), q * al * qc)
        _lbl(img, 210, y0 + 62, "DINOSAURUS PURBA", font(FS, 22), MUTED, q * al * qc)
        _lbl(img, 850, y0 - 150, "BURUNG", font(FS, 24), mix(accent, INK, 0.05), q * al * qc)
        _lbl(img, 560, y0 + 62, "satu garis keturunan", font(FM, 21), MUTED, q * al * qc)
        kk = eo(_dw(tl, dur, 0.48, 0.72))
        dot_on(img, 200 + 630 * kk, y0 - 90 * kk, 12, mix(accent, WHITE, 0.30), q * al * qc * 0.9)
    qd = esmooth(_dw(tl, dur, 0.66, 0.84))
    if qd > 0:
        _pill_c(img, 540, 1660 + dy, "BURUNG = DINOSAURUS YANG MASIH HIDUP", font(FS, 25),
                mix(accent, INK, 0.10), qd * al, dot=True)



def sc_impact_timeline(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan: garis waktu satu hari (bara, tsunami, gelap, beku) - elemen besar 9:16."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.04, 0.14))
    if q <= 0.02:
        return
    ATM_B2 = ATM_B if "ATM_B" in globals() else (70, 120, 190)
    stops = (("MENIT 1", "batuan panas dari langit", LAVA, "fire"),
             ("JAM 1", "tsunami setinggi gedung", ATM_B2, "wave"),
             ("HARI 1", "langit gelap", ASH, "dark"),
             ("TAHUN 1", "dunia mendingin", SPACE, "ice"))
    lx = 140
    ys = [980, 1180, 1380, 1580]
    ql = esmooth(_dw(tl, dur, 0.06, 0.26))
    if ql > 0:          # garis waktu tebal tumbuh dari atas ke bawah
        line_on(img, (lx, ys[0]), (lx, ys[0] + (ys[-1] - ys[0]) * ql), mix(accent, INK, 0.20), 12, al * q * 0.95)
        for k in range(4):
            line_on(img, (lx - 34, ys[k]), (lx + 34, ys[k]), mix(accent, INK, 0.30), 5, al * q * ql * 0.7)
    for i, (nm, ket, cc, ic) in enumerate(stops):
        qa = esmooth(_dw(tl, dur, 0.12 + i * 0.10, 0.28 + i * 0.10))
        if qa <= 0:
            continue
        cy = ys[i] + dy
        dot_on(img, lx, cy, 34, mix(cc, WHITE, 0.12), al * q * qa, outline=mix(cc, INK, 0.15), width=5)
        ring_on(img, lx, cy, 56 + 12 * (0.5 + 0.5 * math.sin(tg * 1.6 + i)), mix(cc, INK, 0.10), 4,
                al * q * qa * 0.55)
        paste_r(img, 210, cy - 52, nm, font(FB, 36), mix(cc, INK, 0.06), al * q * qa)
        paste_r(img, 210, cy + 10, ket, font(FS, 27), mix(INK, MUTED, 0.22), al * q * qa * 0.95)
        # ---- ilustrasi BESAR di sisi kanan (mengisi lebar layar) ----
        ix2, iy2 = 830, cy
        if ic == "fire":
            ell(img, ix2 - 190, iy2 + 30, ix2 + 190, iy2 + 96, fill=mix(LAVA, INK, 0.25),
                alpha=al * q * qa * 0.55)          # dasar pijar
            for k in range(22):                     # kerucut bara naik & makin lebar
                sd = ((k * 137) % 991) / 991.0
                ph = ((tg * 0.8 + sd) % 1.0)
                wdt = 40 + 150 * (1 - ph)
                dot_on(img, ix2 + (sd - 0.5) * 2 * wdt, iy2 + 50 - ph * 220,
                       5 + 9 * ph, mix(LAVA, WHITE, 0.20 + 0.5 * ph), al * q * qa * (0.30 + 0.7 * (1 - ph)))
            for k in range(4):                      # batuan panas melesat
                aa = -1.1 + k * 0.5 + 0.15 * math.sin(tg * 1.2)
                st = 150 + 40 * math.sin(tg + k)
                _trail(img, [(ix2 + 60 * math.sin(aa) - 22 * j, iy2 + 40 - (st + 20 * j) * math.cos(aa) * 0.2)
                             for j in range(6)], mix(LAVA, WHITE, 0.40), al * q * qa * 0.65, width=16, tail=6)
        elif ic == "wave":
            for i2 in range(3):
                pts = []
                for j in range(24):
                    xx = ix2 - 150 + j * 13
                    yy = iy2 + 30 - 90 * math.exp(-((j - 8 - (tl * 6) % 14) ** 2) / 26) + i2 * 16
                    pts.append((xx, yy))
                for j in range(len(pts) - 1):
                    line_on(img, pts[j], pts[j + 1], mix(cc, INK, 0.08), 11 - i2 * 3, al * q * qa * 0.95)
            _stage(img, ix2, iy2 - 20, 165, 78, mix(cc, WHITE, 0.30), al * q * qa * 1.1)
        elif ic == "dark":
            for k in range(6):
                rrect_on(img, ix2 - 170, iy2 - 70 + k * 26, ix2 + 170, iy2 - 48 + k * 26, 12,
                         mix(cc, INK, 0.22), al * q * qa * (0.45 - k * 0.05))
            for k in range(12):
                sd = ((k * 151) % 983) / 983.0
                dot_on(img, ix2 - 160 + sd * 320, iy2 - 40 + ((tg * 22 + k * 37) % 110), 5,
                       mix(ASH, WHITE, 0.45), al * q * qa * 0.5)
        else:
            for k in range(6):                      # kepingan salju
                aa = k * (math.pi / 3) + tg * 0.20
                ex_, ey_ = ix2 + 118 * math.cos(aa), iy2 + 118 * math.sin(aa)
                line_on(img, (ix2, iy2), (ex_, ey_), mix(cc, WHITE, 0.55), 7, al * q * qa * 0.95)
                for u in (0.55, 0.8):
                    bx_, by_ = ix2 + 118 * u * math.cos(aa), iy2 + 118 * u * math.sin(aa)
                    line_on(img, (bx_, by_), (bx_ + 34 * math.cos(aa + 1.0), by_ + 34 * math.sin(aa + 1.0)),
                            mix(cc, WHITE, 0.55), 5, al * q * qa * 0.85)
                    line_on(img, (bx_, by_), (bx_ + 34 * math.cos(aa - 1.0), by_ + 34 * math.sin(aa - 1.0)),
                            mix(cc, WHITE, 0.55), 5, al * q * qa * 0.85)
            ring_on(img, ix2, iy2, 132, mix(cc, WHITE, 0.40), 4, al * q * qa * 0.4)
    _dust(img, 120, 940 + dy, 1010, 1700 + dy, 30, tg, al * q * 0.6, mix(accent, WHITE, 0.70), wob=24)
    qz = esmooth(_dw(tl, dur, 0.80, 0.94))
    if qz > 0:
        _pill_c(img, 540, 1745 + dy, "DALAM SEHARI, DUNIA SUDAH BERUBAH TOTAL", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


VISUALS["impact_timeline"] = sc_impact_timeline

VISUALS.update({
    "intro_asteroid": sc_intro_asteroid,
    "rock_scale": sc_rock_scale,
    "impact_cross": sc_impact_cross,
    "impact_winter": sc_impact_winter,
    "chain_collapse": sc_chain_collapse,
    "evidence": sc_evidence,
    "survivors": sc_survivors,
})


def _selftest26():
    """Uji cepat adegan Ep26 v2 sebelum dipakai render."""
    names = ["intro_asteroid", "rock_scale", "impact_cross", "impact_winter", "chain_collapse",
             "evidence", "survivors"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "DINOSAURUS PUNAH?"], "accent": "#8C4A2F"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep26 v2: 7 adegan OK (tanpa kotak, elemen besar)")


if __name__ == "__main__":
    _selftest26()


# ====================== Ep27: Kenapa Orang Ngorok? ======================

NIGHT27 = mix(NIGHT, BLUE, 0.18)          # langit kamar malam
WARN27 = (176, 58, 46)                    # merah peringatan


def _icon_scale27(img, cx, cy, s, col, alpha):
    """Ikon timbangan badan (busur + jarum) — berat badan."""
    if alpha <= 0.01:
        return
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.arc([S(cx - 30 * s), S(cy - 26 * s), S(cx + 30 * s), S(cy + 26 * s)], 180, 360,
           fill=col + (255,), width=max(1, int(S(6 * s))))
    _put(img, lay, alpha)
    ang = math.radians(35)
    line_on(img, (cx, cy), (cx + 24 * s * math.cos(ang), cy - 20 * s * math.sin(ang)), col, 4, alpha)
    line_on(img, (cx - 30 * s, cy), (cx + 30 * s, cy), col, 5, alpha)


def _icon_glass27(img, cx, cy, s, col, alpha):
    """Ikon gelas (alkohol)."""
    if alpha <= 0.01:
        return
    poly_on(img, [(cx - 20 * s, cy - 22 * s), (cx + 20 * s, cy - 22 * s),
                  (cx + 11 * s, cy + 12 * s), (cx - 11 * s, cy + 12 * s)],
            mix(col, WHITE, 0.55), alpha, outline=col, width=3)
    line_on(img, (cx, cy + 12 * s), (cx, cy + 24 * s), col, 4, alpha)
    line_on(img, (cx - 14 * s, cy + 24 * s), (cx + 14 * s, cy + 24 * s), col, 4, alpha)


def _icon_droplet27(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon ingus/sumbatan: titik cair + badan tetes."""
    if alpha <= 0.01:
        return
    poly_on(img, [(cx, cy - 26 * s), (cx + 16 * s, cy - 2 * s), (cx + 10 * s, cy + 14 * s),
                  (cx - 10 * s, cy + 14 * s), (cx - 16 * s, cy - 2 * s)],
            mix(col, WHITE, 0.30), alpha, outline=col, width=3)
    for i in range(2):
        ph = ((tg * 0.6 + i * 0.5) % 1.0)
        dot_on(img, cx - 22 * s - i * 10 * s, cy - 20 * s + ph * 26 * s, 4 * s,
               mix(col, WHITE, 0.45), alpha * (1 - ph) * 0.9)


def _icon_cig27(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon rokok: batang + bara + asap mengepul."""
    if alpha <= 0.01:
        return
    rrect_on(img, cx - 26 * s, cy - 7 * s, cx + 20 * s, cy + 7 * s, 6 * s,
             mix(col, WHITE, 0.65), alpha, outline=col, width=3)
    rrect_on(img, cx + 20 * s, cy - 7 * s, cx + 27 * s, cy + 7 * s, 4 * s,
             mix(col, INK, 0.15), alpha)
    dot_on(img, cx + 29 * s, cy, 4 * s, mix(AMBER, WHITE, 0.25), alpha * (0.7 + 0.3 * math.sin(tg * 6.0)))
    for k in range(3):
        ph = ((tg * 0.45 + k * 0.33) % 1.0)
        dot_on(img, cx + 27 * s + 8 * s * math.sin(ph * 6.0), cy - 12 * s - ph * 26 * s,
               3.4 * s + ph * 2 * s, mix(MUTED, WHITE, 0.30), alpha * (1 - ph) * 0.8)


def _icon_back27(img, cx, cy, s, col, alpha):
    """Ikon tidur telentang: tubuh membaring + kepala menghadap atas."""
    if alpha <= 0.01:
        return
    line_on(img, (cx - 22 * s, cy + 8 * s), (cx + 18 * s, cy + 8 * s), col, 7 * s, alpha)
    line_on(img, (cx - 12 * s, cy + 8 * s), (cx - 24 * s, cy - 6 * s), col, 5 * s, alpha)
    line_on(img, (cx + 4 * s, cy + 8 * s), (cx + 18 * s, cy - 6 * s), col, 5 * s, alpha)
    dot_on(img, cx - 32 * s, cy + 6 * s, 9 * s, col, alpha)


def _icon_heart27(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon jantung berdenyut."""
    if alpha <= 0.01:
        return
    k = 1.0 + 0.10 * max(0.0, math.sin(tg * 6.0))
    w_, h_ = 30 * s * k, 26 * s * k
    ell(img, cx - w_, cy - h_, cx, cy, fill=col, alpha=alpha)
    ell(img, cx, cy - h_, cx + w_, cy, fill=col, alpha=alpha)
    poly_on(img, [(cx - w_, cy - h_ * 0.45), (cx + w_, cy - h_ * 0.45), (cx, cy + h_ * 1.25)],
            col, alpha)


def _icon_o227(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon oksigen: bulatan O2 + panah turun."""
    if alpha <= 0.01:
        return
    ell(img, cx - 24 * s, cy - 24 * s, cx + 24 * s, cy + 24 * s, fill=mix(col, WHITE, 0.62),
        alpha=alpha, outline=col, width=4)
    paste_c(img, cx, cy, "O2", font(FB, 22 * s), mix(col, INK, 0.20), alpha)
    ay = cy + 40 * s + 6 * s * math.sin(tg * 3.0)
    line_on(img, (cx, cy + 34 * s), (cx, ay + 14 * s), col, 5, alpha)
    poly_on(img, [(cx - 9 * s, ay + 6 * s), (cx + 9 * s, ay + 6 * s), (cx, ay + 20 * s)], col, alpha)


def _icon_tired27(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon lelah siang hari: mata terpejam + mulut menguap."""
    if alpha <= 0.01:
        return
    ell(img, cx - 26 * s, cy - 26 * s, cx + 26 * s, cy + 26 * s, fill=mix(col, WHITE, 0.60),
        alpha=alpha, outline=col, width=4)
    for sgn in (-1, 1):
        xx = cx + sgn * 12 * s
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        dd.arc([S(xx - 8 * s), S(cy - 12 * s), S(xx + 8 * s), S(cy - 1 * s)], 0, 180,
               fill=col + (255,), width=max(1, int(S(4))))
        _put(img, lay, alpha)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.arc([S(cx - 8 * s), S(cy + 2 * s), S(cx + 8 * s), S(cy + 18 * s)], 0, 180,
           fill=col + (255,), width=max(1, int(S(4))))
    _put(img, lay, alpha)


def _icon_nose27(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon hidung + semprotan hidung."""
    if alpha <= 0.01:
        return
    line_on(img, (cx - 16 * s, cy - 20 * s), (cx - 16 * s, cy + 6 * s), col, 5, alpha)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.arc([S(cx - 24 * s), S(cy - 2 * s), S(cx + 2 * s), S(cy + 20 * s)], 0, 130,
           fill=col + (255,), width=max(1, int(S(5))))
    _put(img, lay, alpha)
    line_on(img, (cx - 24 * s, cy + 18 * s), (cx - 16 * s, cy + 6 * s), col, 5, alpha)
    rrect_on(img, cx + 8 * s, cy - 4 * s, cx + 24 * s, cy + 18 * s, 4 * s,
             mix(col, WHITE, 0.55), alpha, outline=col, width=3)
    for i in range(3):
        ph = ((tg * 0.9 + i * 0.33) % 1.0)
        dot_on(img, cx - 2 * s - ph * 14 * s, cy + 6 * s - 3 * s * i, 2.6 * s,
               mix(col, WHITE, 0.35), alpha * (1 - ph) * 0.9)


def _snore_arcs27(img, cx, cy, alpha, tg, col):
    """Busur dengkuran: mengembang mengikuti irama ngorok (~2,2 detik)."""
    if alpha <= 0.01:
        return
    for i in range(3):
        u = ((tg / 2.2) + i / 3.0) % 1.0
        r = 26 + 92 * eo(u)
        a = alpha * (1 - u) ** 1.3
        if a <= 0.02:
            continue
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        dd.arc([S(cx - r), S(cy - r * 0.82), S(cx + r), S(cy + r * 0.82)], 200, 340,
               fill=col + (255,), width=max(1, int(S(6 - i))))
        _put(img, lay, a)


def sc_intro_ngorok(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: kamar malam — orang tidur pulas, dengkuran berirama."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.18 + i * 0.20, 0.82 + i * 0.20))
        if q <= 0:
            continue
        f = _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66)
        paste_c(img, 540, (516 + i * 96) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q1 = esmooth(seg(tl, 0.5, 0.95))
    if q1 > 0:
        _pill_c(img, 540, 676 + dy, "BUKAN DARI HIDUNG, TAPI TENGGOROKAN", font(FS, 26),
                mix(accent, INK, 0.10), q1 * al, dot=True)
    px0, py0, px1, py1 = 104, 748, 976, 1584
    q2 = esmooth(seg(tl, 0.30, 1.0))
    if q2 <= 0.02:
        return
    rrect_on(img, px0, py0, px1, py1, 46, NIGHT27, q2 * al)
    for k in range(24):                     # bintang berkelip
        sx = px0 + 40 + ((k * 151) % 872)
        sy = py0 + 30 + ((k * 197) % 250)
        tw_ = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(tg * 1.7 + k * 1.7))
        dot_on(img, sx, sy, 3.2, mix(NIGHT27, WHITE, 0.80), q2 * al * tw_ * 0.8)
    mx, my = px1 - 118, py0 + 104           # bulan sabit + halo berdenyut
    _glow_round(img, mx + 4, my - 4, 62, mix(NIGHT27, WHITE, 0.92),
                q2 * al * (0.10 + 0.06 * (0.5 + 0.5 * math.sin(tg * 1.1))))
    ell(img, mx - 44, my - 44, mx + 44, my + 44, fill=mix(NIGHT27, WHITE, 0.88), alpha=q2 * al * 0.95)
    ell(img, mx - 10, my - 52, mx + 52, my + 10, fill=NIGHT27, alpha=q2 * al)
    ph_s = (tg % 7.0) / 7.0                 # v3: bintang jatuh berkala di jendela malam
    if 0.05 < ph_s < 0.27:
        u2 = (ph_s - 0.05) / 0.22
        hx2 = px0 + 130 + u2 * 430
        hy2 = py0 + 84 + u2 * 170
        _trail(img, [(hx2 - 24 * j2, hy2 - 11 * j2) for j2 in range(7)],
               mix(NIGHT27, WHITE, 0.88), q2 * al * math.sin(math.pi * u2), width=8, tail=6)
    _dust(img, px0 + 30, py0 + 320, px1 - 30, py1 - 40, 10, tg, q2 * al * 0.5, mix(NIGHT27, WHITE, 0.45))
    # ---- orang tidur: bantal, kepala, selimut bernapas ----
    fx, fy = 470, py1 - 150
    rrect_on(img, fx - 268, fy - 74, fx - 140, fy + 6, 22, mix(NIGHT27, WHITE, 0.23), q2 * al)
    ell(img, fx - 138, fy - 104, fx - 14, fy + 20, fill=mix(NIGHT27, WHITE, 0.27), alpha=q2 * al,
        outline=mix(NIGHT27, WHITE, 0.46), width=3)
    for sgn in (-1, 1):                     # mata terpejam
        line_on(img, (fx - 76 + sgn * 17 - 15, fy - 42), (fx - 76 + sgn * 17 + 15, fy - 42),
                mix(NIGHT27, WHITE, 0.62), 4, q2 * al * 0.9)
    br = 1 + 0.03 * math.sin(tg * 1.5)
    hgt = 74 * br
    pts = [(fx - 20, fy + 26)]
    for j in range(25):
        u = j / 24.0
        pts.append((fx - 20 + u * 330, fy + 26 - hgt * math.sin(u * math.pi * 0.92)))
    pts.append((fx + 310, fy + 26))
    pts += [(fx + 310, fy + 96), (fx - 20, fy + 96)]
    poly_on(img, pts, mix(NIGHT27, WHITE, 0.13), q2 * al, outline=mix(NIGHT27, WHITE, 0.30), width=3)
    rrect_on(img, fx - 330, fy + 96, fx + 330, fy + 132, 18, mix(NIGHT27, WHITE, 0.09), q2 * al)
    # ---- dengkuran: busur dari mulut + kilau berirama ----
    hx, hy = fx - 44, fy - 96
    pulse = 0.5 + 0.5 * math.sin(tg * math.pi * 2 / 2.2)
    _glow_round(img, hx, hy, 40 + 22 * pulse, mix(accent, WHITE, 0.45), q2 * al * (0.10 + 0.16 * pulse))
    _snore_arcs27(img, hx, hy, q2 * al * 0.9, tg, mix(NIGHT27, WHITE, 0.86))
    # ---- meter suara di kanan bawah panel ----
    for i in range(6):
        hh = (0.22 + 0.78 * abs(math.sin(tg * 3.1 + i * 0.75))) * 150 * (0.35 + 0.65 * pulse)
        cc = mix(NIGHT27, WHITE, 0.42 + 0.30 * i / 6.0)
        rrect_on(img, 862 + i * 17, 1516 - hh, 872 + i * 17, 1516, 5, cc, q2 * al)
    _lbl(img, 912, 1546, "SUARA", font(FS, 20), mix(NIGHT27, WHITE, 0.60), q2 * al)
    q4 = esmooth(seg(tl, 2.6, 3.2))
    if q4 > 0:
        _pill_c(img, 540, 1660 + dy, "NYARIS 4 DARI 10 DEWASA PERNAH MENDENGKUR", font(FS, 27),
                mix(accent, INK, 0.10), q4 * al, dot=True)


def sc_vibrate(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 1: udara dipaksa lewat celah sempit -> jaringan lunak bergetar."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    ty, by = 880 + dy, 1100 + dy
    line_on(img, (70, ty), (300, ty), mix(accent, INK, 0.20), 9, q * al)
    line_on(img, (780, ty), (1010, ty), mix(accent, INK, 0.20), 9, q * al)
    line_on(img, (70, by), (1010, by), mix(accent, INK, 0.20), 9, q * al)
    qa = esmooth(_dw(tl, dur, 0.08, 0.22))          # jaringan lunak bergetar
    amp = 26 * qa
    pts = [(300, ty)]
    for j in range(1, 17):
        u = j / 16.0
        pts.append((300 + u * 480, ty + amp * math.sin(u * math.pi) * math.sin(tg * 10.0)))
    pts.append((780, ty))
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], mix(accent, INK, 0.05), 11, q * al)
    _lbl(img, 190, ty - 100, "JARINGAN LUNAK", font(FS, 27), mix(accent, INK, 0.05), q * al)
    _lbl(img, 190, ty - 56, "BERGETAR", font(FS, 27), mix(accent, INK, 0.02), q * al * qa)
    qb = esmooth(_dw(tl, dur, 0.16, 0.34))          # udara melesat lewat celah
    for k in range(14):
        u = (tg * (0.55 + 0.40 * qa) + k / 14.0) % 1.0
        xx = 70 + u * 940
        sempit = 300 <= xx <= 780
        yy = ty + 44 + ((by - ty) - 88) * ((k % 3) / 2.0)
        dot_on(img, xx, yy + 6 * math.sin(tg * 3 + k), 8 if sempit else 6,
               mix(accent, WHITE, 0.32) if sempit else mix(accent, MUTED, 0.40),
               q * al * qb * (0.95 if sempit else 0.5))
    _lbl(img, 900, ty - 56, "UDARA", font(FS, 26), mix(accent, INK, 0.05), q * al * qb)
    _lbl(img, 900, ty - 12, "DIPAKSA LEWAT", font(FS, 26), mix(accent, INK, 0.05), q * al * qb)
    qc = esmooth(_dw(tl, dur, 0.38, 0.55))          # bentuk gelombang dengkuran
    wy = 1430 + dy
    line_on(img, (70, wy), (1010, wy), mix(MUTED, WHITE, 0.42), 3, qc * al, dash=16)
    pts = []
    for j in range(161):
        u = j / 160.0
        x = 70 + u * 940
        env = 0.30 + 0.70 * (0.5 + 0.5 * math.sin((tg - (1.0 - u) * 2.4) * 3.2))
        pts.append((x, wy - env * 100 * math.sin(u * 2 * math.pi * 22)))
    for i in range(len(pts) - 1):
        line_on(img, pts[i], pts[i + 1], mix(accent, INK, 0.04), 5, qc * al)
    _lbl(img, 540, wy - 178, "BENTUK GELOMBANG DENGKURAN", font(FS, 28), mix(accent, INK, 0.04), qc * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "PULUHAN GETARAN SETIAP DETIK", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_airway(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 2: bangun = lebar; tidur dalam = menyempit karena lidah jatuh."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    qa = esmooth(_dw(tl, dur, 0.05, 0.18))          # baris 1: saat bangun
    y1a, y1b = 840 + dy, 1000 + dy
    _lbl(img, 540, y1a - 62, "SAAT BANGUN: JALAN NAPAS LEBAR", font(FS, 27),
         mix(accent, INK, 0.02), qa * al)
    line_on(img, (70, y1a), (1010, y1a), mix(accent, INK, 0.22), 9, qa * al)
    line_on(img, (70, y1b), (1010, y1b), mix(accent, INK, 0.22), 9, qa * al)
    for k in range(9):
        u = (tg * 0.42 + k / 9.0) % 1.0
        dot_on(img, 70 + u * 940, (y1a + y1b) / 2 + 12 * math.sin(tg * 1.2 + k), 8,
               mix(accent, WHITE, 0.30), qa * al)
    for k in range(4):                              # tanda otot penjaga
        xx = 180 + k * 240
        line_on(img, (xx, y1a - 32), (xx + 20, y1a - 10), mix(GREEN, INK, 0.30), 5, qa * al)
    qb = esmooth(_dw(tl, dur, 0.24, 0.38))          # baris 2: saat tidur dalam
    y2a, y2b = 1240 + dy, 1400 + dy
    _lbl(img, 540, y2a - 62, "SAAT TIDUR DALAM: MENYEMPIT", font(FS, 27),
         mix(accent, INK, 0.02), qb * al)
    line_on(img, (70, y2a), (1010, y2a), mix(accent, INK, 0.22), 9, qb * al)
    line_on(img, (70, y2b), (1010, y2b), mix(accent, INK, 0.22), 9, qb * al)
    tx = 620
    ell(img, tx - 160, y2b - 66, tx + 180, y2b + 70, fill=mix(accent, INK, 0.30), alpha=qb * al)
    _lbl(img, 780, y2b + 96, "LIDAH JATUH KE BELAKANG", font(FS, 24), mix(accent, INK, 0.06), qb * al)
    for k in range(14):                             # udara terjepit
        u = (tg * 1.05 + k / 14.0) % 1.0
        xx = 70 + u * 940
        yy = y2a + 42 + ((y2b - y2a) - 96) * ((k % 3) / 2.0)
        if abs(xx - tx) < 170:
            yy = y2a + 24
        dot_on(img, xx, yy + 5 * math.sin(tg * 4 + k), 7, mix(accent, WHITE, 0.30), qb * al)
    for k in range(6):                              # tanda getar di dinding atas
        xx = 140 + k * 160 + 8 * math.sin(tg * 9 + k)
        line_on(img, (xx, y2a - 18), (xx + 24, y2a - 42), mix(accent, INK, 0.10), 5, qb * al)
    qc = esmooth(_dw(tl, dur, 0.46, 0.60))
    _lbl(img, 540, 1552 + dy, "SEMPIT = UDARA MAKIN KENCANG", font(FS, 30),
         mix(accent, INK, 0.03), qc * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "GETARAN JUGA IKUT MAKIN KENCANG", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_triggers(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 3: lima pemicu yang membuat dengkuran makin besar."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    items = ["BERAT BADAN BERLEBIH", "ALKOHOL SEBELUM TIDUR", "HIDUNG TERSUMBAT",
             "ROKOK", "TIDUR TELENTANG"]
    q0 = esmooth(_dw(tl, dur, 0.03, 0.12))
    y0 = 800 + dy
    gap = 148
    line_on(img, (150, y0 - 12), (150, y0 + gap * 4 + 12), mix(accent, WHITE, 0.30), 5,
            q0 * al, dash=14)
    for i, txt in enumerate(items):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.085, 0.20 + i * 0.085))
        if qi <= 0.01:
            continue
        yy = y0 + i * gap
        dot_on(img, 150, yy, 42, mix(WHITE, accent, 0.14), qi * al, outline=accent, width=4)
        if i == 0:
            _icon_scale27(img, 150, yy, 1.0, mix(accent, INK, 0.15), qi * al)
        elif i == 1:
            _icon_glass27(img, 150, yy, 1.05, mix(accent, INK, 0.15), qi * al)
        elif i == 2:
            _icon_droplet27(img, 150, yy, 1.0, mix(accent, INK, 0.15), qi * al, tg)
        elif i == 3:
            _icon_cig27(img, 144, yy, 1.0, mix(accent, INK, 0.15), qi * al, tg)
        else:
            _icon_back27(img, 148, yy, 1.1, mix(accent, INK, 0.15), qi * al)
        paste_r(img, 236, yy, txt, font(FS, 33), mix(accent, INK, 0.04), qi * al)
    qz = esmooth(_dw(tl, dur, 0.56, 0.72))
    if qz > 0:
        _pill_c(img, 540, 1660 + dy, "SEMUA MENGECILKAN JALAN NAPAS", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def _flow27(u):
    """Kurva aliran napas: normal - blok - sentakan, berulang."""
    segs = [(0.00, 0.20, "n"), (0.20, 0.33, "b"), (0.33, 0.39, "g"),
            (0.39, 0.57, "n"), (0.57, 0.70, "b"), (0.70, 0.76, "g"),
            (0.76, 1.00, "n")]
    for a, b, kind in segs:
        if a <= u < b or (u >= 1.0 and kind == "n"):
            v = clamp((u - a) / (b - a))
            if kind == "n":
                return 66 * math.sin(v * math.pi * 3.0) * (0.72 + 0.28 * math.sin(v * 9.0)), kind
            if kind == "b":
                return 0.0, kind
            return 168 * math.sin(v * math.pi), kind
    return 0.0, "n"


def sc_apnea(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 4: kurva aliran napas — blok total lalu sentakan (apnea)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    base = 1240 + dy
    line_on(img, (70, base), (1010, base), mix(MUTED, WHITE, 0.40), 4, q * al)
    _lbl(img, 152, base + 46, "ALIRAN NAPAS", font(FS, 24), MUTED, q * al)
    qa0 = esmooth(_dw(tl, dur, 0.05, 0.16))       # fakta frekuensi di atas
    _lbl(img, 540, 724 + dy, "BISA 5 SAMPAI 30 KALI", font(FS, 40), mix(accent, INK, 0.02), qa0 * al)
    _lbl(img, 540, 788 + dy, "DALAM SATU JAM TIDUR", font(FS, 27), MUTED, qa0 * al)
    # sorot dua zona blok
    qb = esmooth(_dw(tl, dur, 0.14, 0.28))
    for (u0, u1) in ((0.20, 0.33), (0.57, 0.70)):
        rrect_on(img, 70 + u0 * 940, base - 200, 70 + u1 * 940, base + 26, 16,
                 mix(WARN27, WHITE, 0.86), qb * al * 0.85, outline=mix(WARN27, WHITE, 0.45), width=3)
    _lbl(img, 320, base - 248, "NAPAS BERHENTI", font(FS, 27), mix(WARN27, INK, 0.05), qb * al)
    _lbl(img, 320, base - 206, "LEBIH DARI 10 DETIK", font(FS, 24), mix(WARN27, INK, 0.10), qb * al)
    # kurva menggambar sendiri kiri -> kanan
    prog = eo(_dw(tl, dur, 0.20, 0.66))
    N = 280
    prev = None
    for j in range(int(N * prog) + 1):
        u = j / float(N)
        if u > 1.0:
            break
        x = 70 + u * 940
        f, kind = _flow27(u)
        y = base - f
        if prev is not None:
            cc = mix(WARN27, INK, 0.05) if kind != "n" else mix(accent, INK, 0.08)
            line_on(img, prev, (x, y), cc, 6, al * q)
        prev = (x, y)
    qg = esmooth(_dw(tl, dur, 0.40, 0.54))
    if qg > 0:                                       # label sentakan
        gx = 70 + 0.36 * 940
        _arrow_on(img, (gx + 118, base - 208), (gx + 12, base - 138), mix(WARN27, INK, 0.05), 5, qg * al)
        _lbl(img, gx + 210, base - 224, "TERSENTAK", font(FS, 27), mix(WARN27, INK, 0.05), qg * al)
        _lbl(img, gx + 210, base - 182, "MENCARI UDARA", font(FS, 24), mix(WARN27, INK, 0.10), qg * al)
    qz = esmooth(_dw(tl, dur, 0.68, 0.82))
    if qz > 0:
        _pill_c(img, 540, 1660 + dy, "NAMA NYA: APNEA TIDUR OBSTRUKTIF", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_body_effect(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 5: rantai efek ke tubuh — oksigen, jantung, otak, kantuk."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    steps = ["OKSIGEN DALAM DARAH TURUN", "JANTUNG BEKERJA MAKIN KERAS",
             "OTAK TERBANGUN SEBENTAR", "SIANG HARINYA: LELAH"]
    y0, gap = 812 + dy, 236
    for i, txt in enumerate(steps):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.11, 0.22 + i * 0.11))
        if qi <= 0.01:
            continue
        yy = y0 + i * gap
        col = mix(accent, INK, 0.12)
        if i == 0:
            _icon_o227(img, 170, yy, 1.15, col, qi * al, tg)
        elif i == 1:
            _icon_heart27(img, 170, yy, 1.25, mix(accent, INK, 0.10), qi * al, tg)
        elif i == 2:
            ell(img, 134, yy - 40, 210, yy + 40, fill=mix(col, WHITE, 0.60), alpha=qi * al,
                outline=col, width=4)
            for k in range(3):
                xx = 146 + k * 22
                lay = _layer(img)
                dd = ImageDraw.Draw(lay)
                dd.arc([S(xx), S(yy - 24), S(xx + 26), S(yy + 4)], 90, 270,
                       fill=col + (255,), width=max(1, int(S(4))))
                _put(img, lay, qi * al)
            for k in range(3):
                aa = -0.8 + k * 0.8
                line_on(img, (222 + 14 * math.cos(aa), yy - 26 + 14 * math.sin(aa)),
                        (240 + 22 * math.cos(aa), yy - 40 + 22 * math.sin(aa)),
                        mix(accent, INK, 0.05), 5, qi * al * (0.6 + 0.4 * math.sin(tg * 5 + k)))
        else:
            _icon_tired27(img, 170, yy, 1.2, col, qi * al, tg)
        paste_r(img, 268, yy, txt, font(FS, 31), mix(accent, INK, 0.04), qi * al)
        if i < 3:                                    # panah antarlangkah
            qa = esmooth(_dw(tl, dur, 0.16 + i * 0.11, 0.28 + i * 0.11))
            _arrow_on(img, (170, yy + 56), (170, yy + gap - 56), mix(accent, WHITE, 0.22), 5, qa * al)
    qz = esmooth(_dw(tl, dur, 0.60, 0.76))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "JANTUNG LAMA-LAMA IKUT LELAH", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_fixes(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 6: empat cara meredakan ngorok biasa."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    pos = [(300, 920), (780, 920), (300, 1330), (780, 1330)]
    labels = ["TIDUR MIRING", "JAGA BERAT BADAN", "JAUHI ALKOHOL MALAM", "RAWAT HIDUNG TERSUMBAT"]
    col = mix(accent, INK, 0.12)
    for i, ((cx, cy), txt) in enumerate(zip(pos, labels)):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.10, 0.22 + i * 0.10))
        if qi <= 0.01:
            continue
        if i == 0:                                   # orang tidur miring
            _sleeper(img, cx + 10, cy - 30, 0.78, qi * al, line=mix(accent, INK, 0.25))
            for k in range(2):
                u = ((tg * 0.5 + k * 0.5) % 1.0)
                paste_c(img, cx + 120 + 30 * u, cy - 60 - 60 * u, "z", font(FB, 20 + 8 * u),
                        mix(accent, WHITE, 0.35), qi * al * (1 - u) * 0.8)
        elif i == 1:
            _icon_scale27(img, cx, cy - 40, 1.5, col, qi * al)
        elif i == 2:
            _icon_glass27(img, cx + 40, cy - 40, 1.5, col, qi * al)
            for sgn in ((-1, -1), (1, 1)):
                line_on(img, (cx - 34 + sgn[0] * 8, cy - 62 + sgn[1] * 8),
                        (cx + 34 + sgn[0] * 8, cy + 6 + sgn[1] * 8),
                        mix(accent, INK, 0.10), 6, qi * al)
        else:
            _icon_nose27(img, cx, cy - 40, 1.6, col, qi * al, tg)
        _pill_c(img, cx, cy + 118, txt, font(FS, 27), mix(accent, INK, 0.08), qi * al)
    qz = esmooth(_dw(tl, dur, 0.56, 0.72))
    if qz > 0:
        _pill_c(img, 540, 1660 + dy, "PEMICU BERKURANG, DENGKURAN IKUT MENGECIL", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_doctor(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 7: tanda bahaya + pemeriksaan tidur."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    signs = ["TERCEKIK SAAT TIDUR", "NAPAS BERHENTI BERULANG", "KANTUK SIANG BERLEBIHAN"]
    for i, txt in enumerate(signs):
        qi = esmooth(_dw(tl, dur, 0.05 + i * 0.09, 0.18 + i * 0.09))
        if qi <= 0.01:
            continue
        yy = 796 + i * 104 + dy
        dot_on(img, 118, yy, 10, mix(WARN27, INK, 0.05), qi * al * (0.7 + 0.3 * math.sin(tg * 4 + i)))
        _pill_c(img, 540, yy, txt, font(FS, 28), mix(WARN27, INK, 0.10), qi * al, dot=False,
                bg=mix(WHITE, WARN27, 0.08))
    qa = esmooth(_dw(tl, dur, 0.36, 0.48))
    if qa > 0:
        _arrow_on(img, (540, 1120 + dy), (540, 1200 + dy), mix(accent, INK, 0.12), 6, qa * al)
        _lbl(img, 540, 1240 + dy, "YANG BIASA DILAKUKAN DOKTER", font(FS, 27),
             mix(accent, INK, 0.03), qa * al)
    qb = esmooth(_dw(tl, dur, 0.48, 0.60))
    if qb > 0.02:                                    # bantai tidur + perekam
        rrect_on(img, 150, 1330 + dy, 700, 1470 + dy, 26, mix(accent, WHITE, 0.72), qb * al)
        ell(img, 210, 1352 + dy, 320, 1428 + dy, fill=mix(accent, INK, 0.28), alpha=qb * al)
        rrect_on(img, 330, 1368 + dy, 660, 1436 + dy, 20, mix(accent, INK, 0.18), qb * al)
        for k in range(3):                           # kabel sensor
            line_on(img, (300 + k * 40, 1380 + dy), (760 + k * 30, 1310 + dy),
                    mix(accent, INK, 0.15), 3, qb * al * 0.9)
        rrect_on(img, 760, 1284 + dy, 950, 1392 + dy, 16, mix(accent, INK, 0.12), qb * al,
                 outline=mix(accent, INK, 0.25), width=3)
        for j in range(40):                          # layar perekam: gelombang
            u = j / 39.0
            xx = 780 + u * 150
            yy = 1318 + dy - 16 * math.sin(u * 18.0) * (0.4 + 0.6 * math.sin(tg * 2.0 + u * 6))
            dot_on(img, xx, yy, 3, mix(WHITE, GREEN, 0.55), qb * al * 0.9)
        _lbl(img, 855, 1424 + dy, "PEMERIKSAAN TIDUR", font(FS, 24), mix(accent, INK, 0.06), qb * al)
    qc = esmooth(_dw(tl, dur, 0.60, 0.72))
    if qc > 0.02:                                    # rekaman semalaman
        line_on(img, (70, 1544 + dy), (1010, 1544 + dy), mix(MUTED, WHITE, 0.42), 3, qc * al, dash=16)
        prev = None
        for j in range(101):
            u = j / 100.0
            x = 70 + u * 940
            blk = (0.25 < u < 0.32) or (0.62 < u < 0.69)
            y = 1544 + dy - (0 if blk else 34 * abs(math.sin(u * 40.0)))
            if prev is not None:
                line_on(img, prev, (x, y), mix(WARN27, INK, 0.08) if blk else mix(accent, INK, 0.10),
                        4, qc * al)
            prev = (x, y)
        _lbl(img, 540, 1596 + dy, "REKAMAN NAPAS SEMALAM", font(FS, 22), MUTED, qc * al)
    qz = esmooth(_dw(tl, dur, 0.72, 0.86))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "JANGAN DITUNDA SAMPAI JANTUNG IKUT SAKIT", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


VISUALS.update({
    "intro_ngorok": sc_intro_ngorok,
    "vibrate": sc_vibrate,
    "airway": sc_airway,
    "triggers": sc_triggers,
    "apnea": sc_apnea,
    "body_effect": sc_body_effect,
    "fixes": sc_fixes,
    "doctor": sc_doctor,
})


def _selftest27():
    """Uji cepat adegan Ep27 sebelum dipakai render."""
    names = ["intro_ngorok", "vibrate", "airway", "triggers", "apnea", "body_effect",
             "fixes", "doctor"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "ORANG NGOROK?"], "accent": "#1F4E79"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep27: 8 adegan OK")


if __name__ == "__main__":
    _selftest27()


# ====================== Ep28: Kenapa Perut Bunyi? ======================

def _icon_jam28(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon jam dinding (untuk makan teratur / interval)."""
    if alpha <= 0.01:
        return
    ell(img, cx - 26 * s, cy - 26 * s, cx + 26 * s, cy + 26 * s, fill=mix(col, WHITE, 0.62),
        alpha=alpha, outline=col, width=4)
    aa = -math.pi / 2 + (tg % 4.0) / 4.0 * 2 * math.pi
    line_on(img, (cx, cy), (cx + 15 * s * math.cos(aa), cy + 15 * s * math.sin(aa)), col, 4, alpha)
    line_on(img, (cx, cy), (cx + 10 * s, cy - 10 * s), col, 3, alpha)


def _icon_soda28(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon gelas bersoda: gelembung naik terus."""
    if alpha <= 0.01:
        return
    poly_on(img, [(cx - 18 * s, cy - 24 * s), (cx + 18 * s, cy - 24 * s),
                  (cx + 13 * s, cy + 22 * s), (cx - 13 * s, cy + 22 * s)],
            mix(col, WHITE, 0.60), alpha, outline=col, width=3)
    for k in range(4):
        ph = ((tg * 0.55 + k * 0.25) % 1.0)
        dot_on(img, cx - 8 * s + 5 * s * math.sin(ph * 7.0 + k * 2.0), cy + 18 * s - ph * 36 * s,
               2.6 * s, mix(col, WHITE, 0.30), alpha * (1 - ph) * 0.95)


def _icon_milk28(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon kotak susu."""
    if alpha <= 0.01:
        return
    poly_on(img, [(cx - 17 * s, cy - 12 * s), (cx - 6 * s, cy - 24 * s),
                  (cx + 17 * s, cy - 24 * s), (cx + 17 * s, cy + 22 * s),
                  (cx - 17 * s, cy + 22 * s)],
            mix(col, WHITE, 0.66), alpha, outline=col, width=3)
    line_on(img, (cx - 17 * s, cy - 2 * s), (cx + 17 * s, cy - 2 * s), col, 3, alpha)


def _icon_kopi28(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon cangkir kopi dengan uap."""
    if alpha <= 0.01:
        return
    poly_on(img, [(cx - 16 * s, cy - 10 * s), (cx + 16 * s, cy - 10 * s),
                  (cx + 12 * s, cy + 18 * s), (cx - 12 * s, cy + 18 * s)],
            mix(col, WHITE, 0.60), alpha, outline=col, width=3)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.arc([S(cx + 14 * s), S(cy - 6 * s), S(cx + 26 * s), S(cy + 8 * s)], -60, 120,
           fill=col + (255,), width=max(1, int(S(3))))
    _put(img, lay, alpha)
    for k in (-1, 1):
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        xx = cx + k * 7 * s
        dd.arc([S(xx - 4 * s), S(cy - 30 * s + abs(k) * 0), S(xx + 4 * s), S(cy - 18 * s)], 0, 180,
               fill=col + (255,), width=max(1, int(S(3))))
        _put(img, lay, alpha * (0.6 + 0.4 * math.sin(tg * 3.0 + k)))


def _icon_fork28(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon garpu + garis kecepatan (makan cepat)."""
    if alpha <= 0.01:
        return
    line_on(img, (cx, cy - 24 * s), (cx, cy + 24 * s), col, 5, alpha)
    for k in (-1, 0, 1):
        line_on(img, (cx + k * 7 * s, cy - 24 * s), (cx + k * 7 * s, cy - 6 * s), col, 4, alpha)
    for k in (0, 1):
        line_on(img, (cx - 30 * s + k * 4 * s, cy - 8 * s + k * 10 * s),
                (cx - 12 * s + k * 4 * s, cy - 8 * s + k * 10 * s),
                mix(col, WHITE, 0.35), 4, alpha * (0.6 + 0.4 * math.sin(tg * 6 + k)))


def _icon_water28(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon gelas air dengan permukaan bergelombang."""
    if alpha <= 0.01:
        return
    poly_on(img, [(cx - 18 * s, cy - 22 * s), (cx + 18 * s, cy - 22 * s),
                  (cx + 13 * s, cy + 22 * s), (cx - 13 * s, cy + 22 * s)],
            mix(col, WHITE, 0.70), alpha, outline=col, width=3)
    pts = []
    for j in range(13):
        u = j / 12.0
        xx = cx - 16 * s + u * 32 * s
        pts.append((xx, cy - 2 * s + 2.5 * s * math.sin(u * 6.0 + tg * 3.0)))
    for j in range(len(pts) - 1):
        line_on(img, pts[j], pts[j + 1], col, 3, alpha)


def _icon_walk28(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon orang berjalan ringan."""
    if alpha <= 0.01:
        return
    dot_on(img, cx, cy - 22 * s, 8 * s, col, alpha)
    ph = math.sin(tg * 5.0)
    line_on(img, (cx, cy - 14 * s), (cx, cy + 4 * s), col, 6 * s, alpha)
    line_on(img, (cx, cy + 4 * s), (cx - 10 * s + ph * 6 * s, cy + 24 * s), col, 5 * s, alpha)
    line_on(img, (cx, cy + 4 * s), (cx + 10 * s - ph * 6 * s, cy + 24 * s), col, 5 * s, alpha)
    line_on(img, (cx, cy - 8 * s), (cx - 12 * s, cy + 2 * s - ph * 4 * s), col, 4 * s, alpha)
    line_on(img, (cx, cy - 8 * s), (cx + 12 * s, cy + 2 * s + ph * 4 * s), col, 4 * s, alpha)


def _icon_steto28(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon stetoskop."""
    if alpha <= 0.01:
        return
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.arc([S(cx - 30 * s), S(cy - 26 * s), S(cx + 2 * s), S(cy + 18 * s)], 90, 270,
           fill=col + (255,), width=max(1, int(S(5))))
    dd.arc([S(cx - 2 * s), S(cy - 26 * s), S(cx + 30 * s), S(cy + 18 * s)], 270, 90,
           fill=col + (255,), width=max(1, int(S(5))))
    _put(img, lay, alpha)
    line_on(img, (cx + 28 * s, cy - 4 * s), (cx + 28 * s, cy + 22 * s), col, 5, alpha)
    ell(img, cx + 20 * s, cy + 22 * s, cx + 36 * s, cy + 38 * s, fill=mix(col, WHITE, 0.5),
        alpha=alpha, outline=col, width=3)


def _icon_cross28(img, cx, cy, s, col, alpha):
    """Tanda silang besar (mitos)."""
    if alpha <= 0.01:
        return
    ell(img, cx - 34 * s, cy - 34 * s, cx + 34 * s, cy + 34 * s, fill=mix(col, WHITE, 0.88),
        alpha=alpha, outline=col, width=4)
    for sgn in (-1, 1):
        line_on(img, (cx - 16 * s * sgn, cy - 16 * s), (cx + 16 * s * sgn, cy + 16 * s), col, 7, alpha)


def _icon_check28(img, cx, cy, s, col, alpha):
    """Tanda centang besar (fakta)."""
    if alpha <= 0.01:
        return
    ell(img, cx - 34 * s, cy - 34 * s, cx + 34 * s, cy + 34 * s, fill=mix(col, WHITE, 0.86),
        alpha=alpha, outline=col, width=4)
    line_on(img, (cx - 15 * s, cy + 2 * s), (cx - 4 * s, cy + 14 * s), col, 7, alpha)
    line_on(img, (cx - 4 * s, cy + 14 * s), (cx + 18 * s, cy - 12 * s), col, 7, alpha)


def sc_intro_perut(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: suasana sunyi, perut tiba-tiba bunyi — busur suara + gelembung."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.18 + i * 0.20, 0.82 + i * 0.20))
        if q <= 0:
            continue
        f = _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66)
        paste_c(img, 540, (516 + i * 96) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q1 = esmooth(seg(tl, 0.5, 0.95))
    if q1 > 0:
        _pill_c(img, 540, 676 + dy, "PUNYA NAMA ILMIAH: BORBORYGMUS", font(FS, 28),
                mix(accent, INK, 0.10), q1 * al, dot=True)
    px0, py0, px1, py1 = 104, 748, 976, 1584
    q2 = esmooth(seg(tl, 0.30, 1.0))
    if q2 <= 0.02:
        return
    pang = mix(CREAM, mix(accent, INK, 0.30), 0.24)
    rrect_on(img, px0, py0, px1, py1, 46, pang, q2 * al)
    rrect_on(img, px0, py1 - 128, px1, py1, 46, mix(pang, INK, 0.16), q2 * al)   # lantai
    _dust(img, px0 + 30, py0 + 60, px1 - 30, py1 - 150, 8, tg, q2 * al * 0.45, mix(pang, WHITE, 0.55))
    # ---- meja + karakter duduk (tampak samping) ----
    fx, fy = 430, py1 - 128
    rrect_on(img, fx - 320, fy - 26, fx + 330, fy + 26, 14, mix(pang, WHITE, 0.42), q2 * al)
    rrect_on(img, fx - 260, fy + 26, fx - 236, fy + 96, 10, mix(pang, WHITE, 0.30), q2 * al)
    rrect_on(img, fx + 236, fy + 26, fx + 260, fy + 96, 10, mix(pang, WHITE, 0.30), q2 * al)
    hx, hy = fx - 130, fy - 150
    rrect_on(img, hx - 46, hy, hx + 46, fy + 20, 24, mix(pang, WHITE, 0.30), q2 * al)   # badan
    ell(img, hx - 40, hy - 92, hx + 40, hy - 12, fill=mix(pang, WHITE, 0.36), alpha=q2 * al)
    pulse0 = 0.5 + 0.5 * math.sin(tg * math.pi * 2 / 1.9)
    if pulse0 > 0.62:                        # v2: mata membelalak saat dengkuran menguat
        for sgn in (-1, 1):
            ex = hx + sgn * 11
            ell(img, ex - 5, hy - 66, ex + 5, hy - 54, fill=mix(pang, INK, 0.30), alpha=q2 * al)
    else:
        line_on(img, (hx - 16, hy - 60), (hx - 6, hy - 60), mix(pang, INK, 0.30), 4, q2 * al)  # mata
        line_on(img, (hx + 6, hy - 60), (hx + 16, hy - 60), mix(pang, INK, 0.30), 4, q2 * al)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.arc([S(hx - 12), S(hy - 46), S(hx + 12), S(hy - 30)], 0, 180, fill=mix(pang, INK, 0.30) + (255,),
           width=max(1, int(S(4))))
    _put(img, lay, q2 * al)
    bx, by = hx + 20, fy - 90                # area perut
    ell(img, bx - 44, by - 44, bx + 44, by + 44, fill=mix(WHITE, mix(accent, WHITE, 0.40), 0.55),
        alpha=q2 * al * 0.95, outline=mix(accent, INK, 0.15), width=4)
    pulse = 0.5 + 0.5 * math.sin(tg * math.pi * 2 / 1.9)
    _glow_round(img, bx, by, 52 + 26 * pulse, mix(accent, WHITE, 0.5), q2 * al * (0.12 + 0.18 * pulse))
    for i in range(3):                       # busur suara mengembang dari perut
        u = ((tg / 1.9) + i / 3.0) % 1.0
        r = 40 + 120 * eo(u)
        a = q2 * al * (1 - u) ** 1.3 * 0.9
        if a <= 0.02:
            continue
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        dd.arc([S(bx - r), S(by - r), S(bx + r), S(by + r)], -70, 110,
               fill=mix(accent, INK, 0.05) + (255,), width=max(1, int(S(7 - i))))
        _put(img, lay, a)
    u_ring = (tg / 1.9) % 1.0                # v2: cincin denyut penuh dari perut
    ring_on(img, bx, by, 52 + 74 * eo(u_ring), mix(accent, WHITE, 0.55), 5,
            q2 * al * (1 - u_ring) * 0.55)
    for k in range(5):                       # gelembung gas naik dari perut
        ph = ((tg * 0.30 + k * 0.2) % 1.0)
        dot_on(img, bx - 20 + k * 10 + 8 * math.sin(tg * 1.2 + k * 2.0), by - ph * 190,
               3.5 + 3 * (k % 3), mix(accent, WHITE, 0.55), q2 * al * (1 - ph) * 0.8)
    for k in range(3):                       # tanda kaget di kepala
        u = ((tg * 0.7 + k / 3.0) % 1.0)
        star4(img, hx + 60 + 30 * u, hy - 80 - 40 * u, 6 + 8 * u, mix(accent, WHITE, 0.60),
              q2 * al * (1 - u) * 0.9)
    # meter suara di kanan bawah
    for i in range(6):
        hh = (0.22 + 0.78 * abs(math.sin(tg * 3.4 + i * 0.8))) * 130 * (0.35 + 0.65 * pulse)
        cc = mix(pang, WHITE, 0.40 + 0.30 * i / 6.0)
        rrect_on(img, 838 + i * 17, py1 - 150 - hh, 848 + i * 17, py1 - 150, 5, cc, q2 * al)
    _lbl(img, 890, py1 - 120, "SUARA", font(FS, 20), mix(pang, WHITE, 0.62), q2 * al)
    q4 = esmooth(seg(tl, 2.6, 3.2))
    if q4 > 0:
        _pill_c(img, 540, 1660 + dy, "SEMUA ORANG MENGALAMINYA BEBERAPA KALI SEHARI", font(FS, 27),
                mix(accent, INK, 0.10), q4 * al, dot=True)


def sc_peristaltik(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 1: saluran cerna berkelok, otot polos mengontraksi, makanan terdorong."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return

    def pusat(t):
        x = 70 + t * 940
        y = 1070 + dy + 150 * math.sin(t * math.pi * 2.0)
        return x, y

    qb = esmooth(_dw(tl, dur, 0.05, 0.20))
    N = 90
    atas = [pusat(i / N) for i in range(N + 1)]
    bawah = [(x, y + 128) for (x, y) in atas]
    for i in range(N):
        line_on(img, atas[i], atas[i + 1], mix(accent, INK, 0.22), 9, qb * al)
        line_on(img, bawah[i], bawah[i + 1], mix(accent, INK, 0.22), 9, qb * al)
    _lbl(img, 280, 830 + dy, "OTOT POLOS", font(FS, 30), mix(accent, INK, 0.03), qb * al)
    _lbl(img, 280, 882 + dy, "BERKONTRAKSI BERGELOMBANG", font(FS, 25), MUTED, qb * al)
    for k in range(3):                       # cincin kontraksi merambat
        u = ((tg * 0.14 + k / 3.0) % 1.0)
        x, y = pusat(u)
        qc = esmooth(seg(tl, 0.5 + k * 0.3, 0.9 + k * 0.3))
        ell(img, x - 26, y - 10, x + 26, y + 138, fill=None,
            outline=mix(accent, INK, 0.02), width=7, alpha=qb * al * qc * (0.55 + 0.45 * math.sin(tg * 4 + k)))
    for k in range(7):                       # v2: partikel makanan mengalir terus
        u2 = ((tg * 0.05 + k / 7.0) % 1.0)
        x2, y2 = pusat(u2)
        dot_on(img, x2 + 12 * math.sin(tg * 2.0 + k * 2.1), y2 + 34 + 34 * math.sin(k * 1.7 + tg * 0.8),
               6 + (k % 3) * 2.5, mix(WHITE, mix(accent, WHITE, 0.35), 0.75),
               qb * al * (0.55 + 0.45 * math.sin(tg * 1.3 + k)))
    _lbl(img, 130, atas[0][1] - 70, "PERUT", font(FS, 25), MUTED, qb * al)
    _lbl(img, 950, atas[-1][1] - 70, "USUS", font(FS, 25), MUTED, qb * al)
    qa = esmooth(_dw(tl, dur, 0.14, 0.30))   # bolus makanan terdorong
    ub = ((tg * 0.14 + 0.10) % 1.0)
    x, y = pusat(ub)
    for (dx, dyy, r) in ((-14, -26, 12), (6, -18, 14), (-4, 4, 15), (10, 20, 11), (-12, 26, 10)):
        dot_on(img, x + dx, y + 58 + dyy, r, mix(WHITE, mix(accent, WHITE, 0.35), 0.8), qa * al)
    _lbl(img, x + 150, y + 150, "MAKANAN + CAIRAN + GAS", font(FS, 25), mix(accent, INK, 0.05), qa * al)
    _arrow_on(img, (836, atas[-1][1] + 214), (966, atas[-1][1] + 214), mix(accent, WHITE, 0.30), 5, qa * al)
    _lbl(img, 900, atas[-1][1] + 262, "LANJUT KE USUS", font(FS, 23), MUTED, qa * al)
    for k in range(3):                       # panah arah dorongan
        uu = ub + 0.06 + k * 0.05
        if uu > 0.97:
            continue
        xa, ya = pusat(uu)
        _arrow_on(img, (xa - 16, ya + 52), (xa + 34, ya + 52), mix(accent, WHITE, 0.28), 5, qa * al)
    qz = esmooth(_dw(tl, dur, 0.60, 0.76))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "BENTURAN ITULAH YANG TERDENGAR", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_mmc(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 2: mode sapu bersih saat lapar — gelombang besar tiap 1-2 jam."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    base = 1240 + dy
    qa0 = esmooth(_dw(tl, dur, 0.04, 0.15))
    _lbl(img, 540, 742 + dy, "MODE SAPU BERSIH", font(FS, 44), mix(accent, INK, 0.02), qa0 * al)
    _lbl(img, 540, 806 + dy, "NYALA SAAT PERUT KOSONG", font(FS, 27), MUTED, qa0 * al)
    _icon_jam28(img, 952, 764 + dy, 1.15, mix(accent, INK, 0.12), qa0 * al, tg)   # v2: siklus jam
    _lbl(img, 952, 826 + dy, "1-2 JAM", font(FS, 21), MUTED, qa0 * al)
    line_on(img, (70, base), (1010, base), mix(MUTED, WHITE, 0.40), 4, q * al)
    _lbl(img, 152, base + 46, "WAKTU", font(FS, 24), MUTED, q * al)
    prog = eo(_dw(tl, dur, 0.16, 0.62))
    N = 260

    def amplitudo(u):
        g1 = math.exp(-((u - 0.30) ** 2) / (2 * 0.035 ** 2))
        g2 = math.exp(-((u - 0.72) ** 2) / (2 * 0.04 ** 2))
        return 200 * g1 + 250 * g2 + 16 * abs(math.sin(u * 40.0))

    prev = None
    for j in range(int(N * prog) + 1):
        u = j / float(N)
        x = 70 + u * 940
        y = base - amplitudo(u)
        if prev is not None:
            kuat = amplitudo(u) > 120
            line_on(img, prev, (x, y), mix(accent, INK, 0.02) if kuat else mix(accent, MUTED, 0.35),
                    6 if kuat else 4, q * al)
        prev = (x, y)
    qb = esmooth(_dw(tl, dur, 0.34, 0.48))
    if qb > 0:                               # label gelombang besar
        gx = 70 + 0.30 * 940
        _arrow_on(img, (gx + 26, base - 300), (gx + 4, base - 236), mix(accent, INK, 0.08), 5, qb * al)
        _lbl(img, gx + 170, base - 316, "KONTRAKSI BESAR", font(FS, 27), mix(accent, INK, 0.03), qb * al)
        _lbl(img, gx + 170, base - 274, "TIAP 1 SAMPAI 2 JAM", font(FS, 24), MUTED, qb * al)
    qc = esmooth(_dw(tl, dur, 0.48, 0.60))
    if qc > 0:                               # sapuan menyapu sepanjang garis
        u = (tg * 0.11) % 1.0
        x = 70 + u * 940
        y = base - amplitudo(u)
        _trail(img, [(x - 18 * j, base - amplitudo(max(0.0, u - 0.006 * j))) for j in range(7)],
               mix(accent, WHITE, 0.35), qc * al, width=12, tail=6)
        line_on(img, (x, y + 6), (x - 26, y - 44), mix(accent, INK, 0.10), 7, qc * al)
        line_on(img, (x - 26, y - 44), (x - 44, y - 66), mix(WHITE, AMBER, 0.45), 10, qc * al)
        _lbl(img, 836, base - 320, "SISA MAKANAN", font(FS, 24), MUTED, qc * al)
        _lbl(img, 836, base - 280, "DISAPU BERSIH", font(FS, 24), mix(accent, INK, 0.06), qc * al)
    for uc in (0.30, 0.72):                  # v2: puncak gelombang berpendar
        xg = 70 + uc * 940
        yg = base - (200 if uc < 0.5 else 250)
        _glow_round(img, xg, yg - 10, 30 + 8 * math.sin(tg * 2.4 + uc * 5.0),
                    mix(accent, WHITE, 0.55),
                    q * al * (0.14 + 0.10 * (0.5 + 0.5 * math.sin(tg * 2.4 + uc * 5.0))))
    qz = esmooth(_dw(tl, dur, 0.66, 0.80))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "GELOMBANG KUAT + GAS = BUNYI TERKERAS", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_gas(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 3: dua sumber gas — udara tertelan & fermentasi bakteri."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    ty, by = 940 + dy, 1250 + dy
    line_on(img, (70, ty), (1010, ty), mix(accent, INK, 0.22), 9, q * al)
    line_on(img, (70, by), (1010, by), mix(accent, INK, 0.22), 9, q * al)
    rrect_on(img, 70, ty + 6, 1010, by - 6, 10, mix(accent, WHITE, 0.78), q * al * 0.55)  # cairan
    qa = esmooth(_dw(tl, dur, 0.08, 0.22))   # gelembung naik + pecah di permukaan
    for k in range(16):
        sd = ((k * 137) % 991) / 991.0
        ph = ((tg * (0.10 + sd * 0.05) + sd) % 1.0)
        x = 92 + sd * 890
        y = by - 16 - ph * (by - ty - 60)
        r = 5 + 8 * ((k * 3) % 4) / 3.0
        ell(img, x - r, y - r, x + r, y + r, fill=mix(WHITE, accent, 0.18), alpha=qa * al * (1 - ph * 0.25),
            outline=mix(accent, INK, 0.18), width=3)
        if ph > 0.93:                        # pecah di permukaan
            lay = _layer(img)
            dd = ImageDraw.Draw(lay)
            dd.arc([S(x - r * 2), S(ty - r), S(x + r * 2), S(ty + r * 2)], 200, 340,
                   fill=mix(accent, INK, 0.05) + (255,), width=max(1, int(S(4))))
            _put(img, lay, qa * al * (1.0 - ph) * 8.0)
            for j in range(3):               # v2: percikan kecil saat pecah
                aa2 = j * 2.1 + tg * 1.3
                star4(img, x + r * 1.7 * math.cos(aa2), ty - 2 - r * 0.7 * abs(math.sin(aa2)),
                      3.5 + 2.5 * j, mix(accent, WHITE, 0.55), qa * al * (1.0 - ph) * 6.0)
    _lbl(img, 540, 880 + dy, "KRUCUK = GELEMBUNG MELEWATI CAIRAN", font(FS, 29),
         mix(accent, INK, 0.03), qa * al)
    qb = esmooth(_dw(tl, dur, 0.24, 0.38))   # sumber 1: udara tertelan
    _icon_water28(img, 190, 1460 + dy, 1.5, mix(accent, INK, 0.12), qb * al, tg)
    for k in range(3):
        ph = ((tg * 0.8 + k * 0.33) % 1.0)
        dot_on(img, 190 - 6 + ph * 12, 1430 + dy - ph * 40, 3.5, mix(accent, WHITE, 0.45), qb * al * (1 - ph))
    _lbl(img, 190, 1556 + dy, "UDARA TERTELAN", font(FS, 26), mix(accent, INK, 0.06), qb * al)
    _lbl(img, 190, 1600 + dy, "SAAT MAKAN & MINUM", font(FS, 22), MUTED, qb * al)
    _arrow_on(img, (300, 1470 + dy), (392, 1330 + dy), mix(accent, WHITE, 0.30), 5, qb * al)
    qc = esmooth(_dw(tl, dur, 0.40, 0.54))   # sumber 2: fermentasi bakteri
    bx0 = 880
    ell(img, bx0 - 90, 1352 + dy, bx0 + 90, 1470 + dy, fill=mix(accent, INK, 0.16), alpha=qc * al)
    for k in range(5):
        aa = k * 1.25 + tg * 0.3
        dot_on(img, bx0 + 56 * math.cos(aa), 1410 + dy + 30 * math.sin(aa), 9,
               mix(WHITE, accent, 0.30), qc * al)
        line_on(img, (bx0 + 56 * math.cos(aa) + 8, 1410 + dy + 30 * math.sin(aa) - 6),
                (bx0 + 56 * math.cos(aa) + 20, 1410 + dy + 30 * math.sin(aa) - 14),
                mix(accent, INK, 0.10), 3, qc * al)
    _lbl(img, bx0, 1556 + dy, "FERMENTASI BAKTERI", font(FS, 26), mix(accent, INK, 0.06), qc * al)
    _lbl(img, bx0, 1600 + dy, "DI USUS BESAR", font(FS, 22), MUTED, qc * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "NORMAL: GAS INI MEMANG HARUS KELUAR JALAN", font(FS, 27),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_pemicu(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 4: kebiasaan yang membuat perut bunyi lebih sering."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    items = ["MAKAN TERLAMBAT", "MINUMAN BERSODA", "SUSU DI PERUT KOSONG",
             "KOPI TANPA SARAPAN", "MAKAN TERLALU CEPAT"]
    q0 = esmooth(_dw(tl, dur, 0.03, 0.12))
    y0 = 800 + dy
    gap = 148
    line_on(img, (150, y0 - 12), (150, y0 + gap * 4 + 12), mix(accent, WHITE, 0.30), 5, q0 * al, dash=14)
    for i, txt in enumerate(items):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.085, 0.20 + i * 0.085))
        if qi <= 0.01:
            continue
        yy = y0 + i * gap
        col = mix(accent, INK, 0.15)
        dot_on(img, 150, yy, 42, mix(WHITE, accent, 0.14), qi * al, outline=accent, width=4)
        if i == 0:
            _icon_jam28(img, 150, yy, 1.0, col, qi * al, tg)
        elif i == 1:
            _icon_soda28(img, 150, yy, 1.05, col, qi * al, tg)
        elif i == 2:
            _icon_milk28(img, 146, yy, 1.05, col, qi * al, tg)
        elif i == 3:
            _icon_kopi28(img, 150, yy, 1.05, col, qi * al, tg)
        else:
            _icon_fork28(img, 150, yy, 1.0, col, qi * al, tg)
        star4(img, 150, yy, 44 + 8 * math.sin(tg * 3.0 + i * 1.3), mix(accent, WHITE, 0.60),
              qi * (1 - qi) * 3.0 * al)   # v2: kilat saat item mendarat
        paste_r(img, 236, yy, txt, font(FS, 32), mix(accent, INK, 0.04), qi * al)
    qz = esmooth(_dw(tl, dur, 0.56, 0.72))
    if qz > 0:
        _pill_c(img, 540, 1660 + dy, "UDARA EKSTRA = BUNYI EKSTRA", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_mitos(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 5: dua mitos dibongkar + satu kebenaran."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    colx = mix(WARN27, INK, 0.05)
    colc = mix(accent, INK, 0.08)
    qa = esmooth(_dw(tl, dur, 0.06, 0.20))
    _icon_cross28(img, 300, 880 + dy, 1.15, colx, qa * al)
    _lbl(img, 300, 990 + dy, "PERUT BUNYI =", font(FS, 30), colx, qa * al)
    _lbl(img, 300, 1040 + dy, "PASTI LAPAR?", font(FS, 30), colx, qa * al)
    _lbl(img, 300, 1120 + dy, "PENCERNAAN TETAP", font(FS, 25), MUTED, qa * al)
    _lbl(img, 300, 1162 + dy, "BEKERJA SAAT KENYANG", font(FS, 25), MUTED, qa * al)
    qs1 = esmooth(_dw(tl, dur, 0.15, 0.27))  # v2: coretan merah pada mitos 1
    if qs1 > 0:
        wd1 = 158 * eo(qs1)
        line_on(img, (300 - wd1, 1015 + dy), (300 + wd1, 1015 + dy), mix(WARN27, INK, 0.10), 7, qs1 * al)
    qb = esmooth(_dw(tl, dur, 0.22, 0.36))
    _icon_cross28(img, 780, 880 + dy, 1.15, colx, qb * al)
    _lbl(img, 780, 990 + dy, "BUNYI PERUT =", font(FS, 30), colx, qb * al)
    _lbl(img, 780, 1040 + dy, "BUKTI CACINGAN?", font(FS, 30), colx, qb * al)
    _lbl(img, 780, 1120 + dy, "TIDAK ADA HUBUNGAN", font(FS, 25), MUTED, qb * al)
    _lbl(img, 780, 1162 + dy, "YANG LANGSUNG", font(FS, 25), MUTED, qb * al)
    qs2 = esmooth(_dw(tl, dur, 0.31, 0.43))  # v2: coretan merah pada mitos 2
    if qs2 > 0:
        wd2 = 158 * eo(qs2)
        line_on(img, (780 - wd2, 1015 + dy), (780 + wd2, 1015 + dy), mix(WARN27, INK, 0.10), 7, qs2 * al)
    qc = esmooth(_dw(tl, dur, 0.44, 0.58))
    _icon_check28(img, 540, 1330 + dy, 1.3, colc, qc * al)
    _lbl(img, 540, 1448 + dy, "BUNYI PERUT ITU NORMAL", font(FS, 31), mix(accent, INK, 0.03), qc * al)
    _lbl(img, 540, 1498 + dy, "TERJADI BEBERAPA KALI SEHARI PADA SIAPA SAJA", font(FS, 24), MUTED, qc * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1660 + dy, "TAK PERLU MALU, SEMUA ORANG SAMA", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_redakan(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 6: empat kebiasaan yang meredakan bunyi perut."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    pos = [(300, 950), (780, 950), (300, 1330), (780, 1330)]
    labels = ["MAKAN TERATUR", "KUNYAH PELAN", "JAUHI SODA & PERMEN", "AIR PUTIH CUKUP"]
    col = mix(accent, INK, 0.12)
    for i, ((cx, cy), txt) in enumerate(zip(pos, labels)):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.10, 0.22 + i * 0.10))
        if qi <= 0.01:
            continue
        yo = 7 * math.sin(tg * 1.4 + i * 1.6)    # v2: ikon melayang halus
        if i == 0:
            _icon_jam28(img, cx, cy - 40 + yo, 1.5, col, qi * al, tg)
        elif i == 1:
            _icon_fork28(img, cx, cy - 40 + yo, 1.5, col, qi * al, tg)
        elif i == 2:
            _icon_soda28(img, cx + 12, cy - 48 + yo, 1.4, col, qi * al, tg)
            line_on(img, (cx - 34, cy - 84 + yo), (cx + 52, cy - 6 + yo), mix(WARN27, INK, 0.05), 7, qi * al)
        else:
            _icon_water28(img, cx, cy - 40 + yo, 1.5, col, qi * al, tg)
        _pill_c(img, cx, cy + 108, txt, font(FS, 26), mix(accent, INK, 0.08), qi * al)
    qm = esmooth(_dw(tl, dur, 0.46, 0.58))
    if qm > 0:
        _icon_walk28(img, 214, 1560 + dy, 1.2, col, qm * al, tg)
        _lbl(img, 560, 1560 + dy, "JALAN RINGAN SESUDAH MAKAN", font(FS, 29),
             mix(accent, INK, 0.03), qm * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.76))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "GAS TIDAK MENGGENANG, BUNYI MEREDA", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_waspada(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 7: tanda bahaya + ajakan periksa."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    signs = ["NYERI HEBAT YANG TIDAK WAJAR", "DIARE BERHARI-HARI",
             "BERAT BADAN TERUS TURUN", "RASA TERSEDAK / TERSENBAT"]
    for i, txt in enumerate(signs):
        qi = esmooth(_dw(tl, dur, 0.05 + i * 0.085, 0.18 + i * 0.085))
        if qi <= 0.01:
            continue
        yy = 780 + i * 106 + dy
        dot_on(img, 118, yy, 10, mix(WARN27, INK, 0.05), qi * al * (0.7 + 0.3 * math.sin(tg * 4 + i)))
        _pill_c(img, 540, yy, txt, font(FS, 28), mix(WARN27, INK, 0.10), qi * al, bg=mix(WHITE, WARN27, 0.08))
    qa = esmooth(_dw(tl, dur, 0.42, 0.54))
    if qa > 0:
        _arrow_on(img, (540, 1230 + dy), (540, 1300 + dy), mix(accent, INK, 0.12), 6, qa * al)
    qb = esmooth(_dw(tl, dur, 0.52, 0.64))
    if qb > 0:
        _icon_steto28(img, 320, 1430 + dy, 1.7, mix(accent, INK, 0.12), qb * al, tg)
        ring_on(img, 368, 1481 + dy, 26 + 7 * math.sin(tg * 3.0), mix(accent, WHITE, 0.55), 4,
                qb * al * 0.75)   # v2: denyut di kepala stetoskop
        _lbl(img, 640, 1420 + dy, "PERIKSA KE DOKTER", font(FS, 33), mix(accent, INK, 0.03), qb * al)
        _lbl(img, 640, 1478 + dy, "PENCERNAAN DIPERIKSA LANGSUNG", font(FS, 25), MUTED, qb * al)
    qz = esmooth(_dw(tl, dur, 0.70, 0.84))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "JANGAN DITUNDA SAMPAI MEMBURUK", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


VISUALS.update({
    "intro_perut": sc_intro_perut,
    "peristaltik": sc_peristaltik,
    "mmc": sc_mmc,
    "gas": sc_gas,
    "pemicu": sc_pemicu,
    "mitos": sc_mitos,
    "redakan": sc_redakan,
    "waspada": sc_waspada,
})


def _selftest28():
    """Uji cepat adegan Ep28 sebelum dipakai render."""
    names = ["intro_perut", "peristaltik", "mmc", "gas", "pemicu", "mitos", "redakan", "waspada"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "PERUT BUNYI?"], "accent": "#3E7A4E"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep28: 8 adegan OK")


if __name__ == "__main__":
    _selftest28()


# ====================== Ep29: Kram & Kesemutan ======================

def _icon_dumbel29(img, cx, cy, s, col, alpha):
    """Ikon dumbel (otot lelah)."""
    if alpha <= 0.01:
        return
    line_on(img, (cx - 16 * s, cy), (cx + 16 * s, cy), col, 6 * s, alpha)
    for sgn in (-1, 1):
        rrect_on(img, cx + sgn * 20 * s - 6 * s, cy - 16 * s, cx + sgn * 20 * s + 6 * s, cy + 16 * s,
                 5 * s, mix(col, WHITE, 0.35), alpha, outline=col, width=3)


def _icon_moon29(img, cx, cy, s, col, alpha):
    """Ikon bulan sabit (malam/dingin)."""
    if alpha <= 0.01:
        return
    ell(img, cx - 20 * s, cy - 20 * s, cx + 20 * s, cy + 20 * s, fill=mix(col, WHITE, 0.55), alpha=alpha)
    ell(img, cx - 4 * s, cy - 26 * s, cx + 30 * s, cy + 8 * s, fill=mix(CREAM, WHITE, 0.55), alpha=alpha)


def _icon_kaki29(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon kaki menunjuk + panah tarik ke atas (kram betis)."""
    if alpha <= 0.01:
        return
    poly_on(img, [(cx - 14 * s, cy + 22 * s), (cx + 10 * s, cy + 22 * s),
                  (cx + 16 * s, cy + 6 * s), (cx + 2 * s, cy - 12 * s), (cx - 14 * s, cy - 12 * s)],
            mix(col, WHITE, 0.60), alpha, outline=col, width=3)
    for k in range(3):
        dot_on(img, cx + 2 * s - k * 5 * s, cy + 18 * s, 2.6 * s, col, alpha)
    ay = cy - 24 * s + 3 * s * math.sin(tg * 3.0)
    line_on(img, (cx + 2 * s, cy - 14 * s), (cx + 2 * s, ay), col, 5, alpha)
    poly_on(img, [(cx - 6 * s, ay + 7 * s), (cx + 10 * s, ay + 7 * s), (cx + 2 * s, ay - 6 * s)],
            col, alpha)


def _icon_stretch29(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon orang merenggangkan tangan ke atas."""
    if alpha <= 0.01:
        return
    dot_on(img, cx, cy - 22 * s, 8 * s, col, alpha)
    line_on(img, (cx, cy - 14 * s), (cx, cy + 6 * s), col, 6 * s, alpha)
    yo = 2 * s * math.sin(tg * 2.2)
    line_on(img, (cx, cy - 8 * s), (cx - 14 * s, cy - 26 * s + yo), col, 4.5 * s, alpha)
    line_on(img, (cx, cy - 8 * s), (cx + 14 * s, cy - 26 * s + yo), col, 4.5 * s, alpha)
    line_on(img, (cx, cy + 6 * s), (cx - 11 * s, cy + 24 * s), col, 5 * s, alpha)
    line_on(img, (cx, cy + 6 * s), (cx + 11 * s, cy + 24 * s), col, 5 * s, alpha)


def _icon_pijat29(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon pijat: lingkaran tekan berdenyut."""
    if alpha <= 0.01:
        return
    for k in range(3):
        u = ((tg * 0.7 + k / 3.0) % 1.0)
        ring_on(img, cx, cy, 6 * s + 18 * s * u, mix(col, WHITE, 0.40), 4, alpha * (1 - u) * 0.9)
    dot_on(img, cx, cy, 8 * s, col, alpha)


def sc_intro_kaki(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: karakter memegang betis kram; sensasi jarum di kaki."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.18 + i * 0.20, 0.82 + i * 0.20))
        if q <= 0:
            continue
        f = _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66)
        paste_c(img, 540, (516 + i * 96) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q1 = esmooth(seg(tl, 0.5, 0.95))
    if q1 > 0:
        _pill_c(img, 540, 676 + dy, "PUNYA NAMA ILMIAH: PARESTESIA", font(FS, 28),
                mix(accent, INK, 0.10), q1 * al, dot=True)
    px0, py0, px1, py1 = 104, 748, 976, 1584
    q2 = esmooth(seg(tl, 0.30, 1.0))
    if q2 <= 0.02:
        return
    pang = mix(CREAM, mix(accent, INK, 0.30), 0.24)
    rrect_on(img, px0, py0, px1, py1, 46, pang, q2 * al)
    rrect_on(img, px0, py1 - 120, px1, py1, 46, mix(pang, INK, 0.16), q2 * al)   # lantai
    _dust(img, px0 + 30, py0 + 60, px1 - 30, py1 - 140, 8, tg, q2 * al * 0.4, mix(pang, WHITE, 0.55))
    hx, fy = 540, py1 - 120
    kol = mix(pang, WHITE, 0.34)
    ell(img, hx - 42, 942, hx + 42, 1026, fill=kol, alpha=q2 * al)               # kepala
    rrect_on(img, hx - 46, 1040, hx + 46, 1250, 26, kol, q2 * al)                # badan
    line_on(img, (hx - 20, 1250), (hx - 34, fy - 4), kol, 12, q2 * al)           # kaki kiri
    line_on(img, (hx + 20, 1250), (hx + 62, 1352), kol, 12, q2 * al)             # kaki kanan menekuk
    line_on(img, (hx + 62, 1352), (hx + 6, 1344), kol, 12, q2 * al)
    line_on(img, (hx - 40, 1080), (hx + 52, 1310), kol, 10, q2 * al)             # tangan memegang betis
    line_on(img, (hx + 40, 1080), (hx + 80, 1268), kol, 10, q2 * al)
    for sgn in (-1, 1):                                                          # mata menyipit sakit
        line_on(img, (hx - 18 + sgn * 14, 976), (hx - 4 + sgn * 14, 976), mix(pang, INK, 0.35), 4, q2 * al)
    lay = _layer(img)                                                            # mulut "ssst"
    dd = ImageDraw.Draw(lay)
    dd.arc([S(hx - 8), S(1000), S(hx + 8), S(1014)], 0, 180, fill=mix(pang, INK, 0.35) + (255,),
           width=max(1, int(S(4))))
    _put(img, lay, q2 * al)
    bxk, byk = hx + 56, 1308                # betis yang kram
    pulse = 0.5 + 0.5 * math.sin(tg * math.pi * 2 / 1.6)
    _glow_round(img, bxk, byk, 40 + 18 * pulse, mix(accent, WHITE, 0.5), q2 * al * (0.12 + 0.16 * pulse))
    for i in range(3):                       # kilat kecil sensasi jarum
        u = ((tg * 0.9 + i / 3.0) % 1.0)
        aa = -0.9 + i * 0.9 + 0.25 * math.sin(tg * 3.0 + i)
        r0 = 26 + 16 * eo(u)
        line_on(img, (bxk + r0 * 0.5 * math.cos(aa), byk + r0 * 0.5 * math.sin(aa)),
                (bxk + r0 * math.cos(aa), byk + r0 * math.sin(aa)),
                mix(accent, WHITE, 0.55), 6, q2 * al * (1 - u) * 0.9)
    star4(img, bxk + 34, byk - 30, 7 + 5 * pulse, mix(accent, WHITE, 0.75), q2 * al * (0.5 + 0.5 * pulse))
    for i in range(6):                       # meter sensasi
        hh = (0.22 + 0.78 * abs(math.sin(tg * 3.6 + i * 0.85))) * 130 * (0.35 + 0.65 * pulse)
        cc = mix(pang, WHITE, 0.40 + 0.30 * i / 6.0)
        rrect_on(img, 838 + i * 17, py1 - 150 - hh, 848 + i * 17, py1 - 150, 5, cc, q2 * al)
    _lbl(img, 890, py1 - 120, "SENSASI", font(FS, 20), mix(pang, WHITE, 0.62), q2 * al)
    q4 = esmooth(seg(tl, 2.6, 3.2))
    if q4 > 0:
        _pill_c(img, 540, 1660 + dy, "DATANG SAAT JONGKOK ATAU BANGUN TIDUR", font(FS, 25),
                mix(accent, INK, 0.10), q4 * al, dot=True)


def sc_saraf(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 1: saraf sebagai kabel - tertekan -> sinyal kacau -> kesemutan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return

    def jalur(t):
        return 540 + 165 * math.sin(t * math.pi * 2.1), 880 + 640 * t

    N = 90
    pts = [jalur(i / N) for i in range(N + 1)]
    qb = esmooth(_dw(tl, dur, 0.05, 0.18))
    for i in range(N):
        line_on(img, pts[i], pts[i + 1], mix(accent, INK, 0.22), 10, qb * al)
    ell(img, 470, 790, 610, 880, fill=mix(accent, WHITE, 0.66), alpha=qb * al, outline=mix(accent, INK, 0.15), width=4)
    _lbl(img, 540, 834, "OTAK", font(FS, 27), mix(accent, INK, 0.05), qb * al)
    ex, ey = pts[-1]
    poly_on(img, [(ex - 34, ey - 4), (ex + 30, ey - 4), (ex + 44, ey + 44), (ex - 20, ey + 44)],
            mix(accent, INK, 0.18), qb * al, outline=mix(accent, INK, 0.10), width=4)
    _lbl(img, ex, ey + 84, "KAKI", font(FS, 26), MUTED, qb * al)
    qa = esmooth(_dw(tl, dur, 0.14, 0.28))   # sinyal mengalir
    for k in range(9):
        u = ((tg * 0.10 + k / 9.0) % 1.0)
        x, y = jalur(u)
        dot_on(img, x + 3 * math.sin(tg * 4 + k), y, 7, mix(accent, WHITE, 0.42), qa * al)
    _lbl(img, 185, 1030, "SINYAL LISTRIK", font(FS, 24), mix(accent, INK, 0.06), qa * al)
    _lbl(img, 185, 1072, "MENGALIR LANCAR", font(FS, 24), MUTED, qa * al)
    qb2 = esmooth(_dw(tl, dur, 0.30, 0.44))  # titik tekan
    tx, ty = jalur(0.55)
    for sgn in (-1, 1):
        poly_on(img, [(tx + sgn * 210, ty - 96), (tx + sgn * 118, ty - 20), (tx + sgn * 118, ty + 46),
                      (tx + sgn * 210, ty + 78)],
                mix(WHITE, accent, 0.30), qb2 * al, outline=accent, width=4)
        for k in range(4):
            yk = ty - 60 + k * 34
            line_on(img, (tx + sgn * 196, yk), (tx + sgn * 132, yk), mix(accent, INK, 0.10), 4, qb2 * al)
    _lbl(img, tx, ty - 130, "JONGKOK / SILA LAMA", font(FS, 25), mix(accent, INK, 0.05), qb2 * al)
    _lbl(img, tx, ty - 88 + 232, "SARAF TERTEKAN", font(FS, 26), mix(accent, INK, 0.04), qb2 * al)
    qc = esmooth(_dw(tl, dur, 0.46, 0.60))   # sinyal kacau sesudah titik tekan
    for k in range(7):
        u = 0.60 + ((tg * 0.22 + k / 7.0) % 1.0) * 0.40
        x, y = jalur(min(1.0, u))
        x += 26 * math.sin(tg * 9.0 + k * 2.2)
        dot_on(img, x, y, 7, mix(WARN27, WHITE, 0.45), qc * al)
    for k in range(4):                       # percikan di kaki
        u = ((tg * 1.1 + k / 4.0) % 1.0)
        star4(img, ex + 40 * math.sin(tg * 2 + k * 1.7), ey + 20 - 26 * u, 5 + 6 * u,
              mix(WARN27, WHITE, 0.55), qc * al * (1 - u))
    _lbl(img, ex - 250, ey - 70, "SINYAL KACAU = KESEMUTAN", font(FS, 27), mix(WARN27, INK, 0.05), qc * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "POSISI DIUBAH, SINYAL LANGSUNG NORMAL", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_ototkram(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 2: serat otot menggenggam keras dan menolak lepas."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    cxm, cym = 540, 1150 + dy
    qk = esmooth(_dw(tl, dur, 0.14, 0.30))   # 0 = rileks, 1 = menggenggam
    kusk = 1.0 - 0.26 * qk
    w2, h2 = 330 * kusk, 165 * (1.0 + 0.16 * qk)
    poly_on(img, [(cxm - w2, cym), (cxm - w2 * 0.62, cym - h2), (cxm + w2 * 0.62, cym - h2),
                  (cxm + w2, cym), (cxm + w2 * 0.62, cym + h2), (cxm - w2 * 0.62, cym + h2)],
            mix(WHITE, accent, 0.22), q * al, outline=mix(accent, INK, 0.10), width=5)
    qa = esmooth(_dw(tl, dur, 0.08, 0.20))
    for k in range(6):                       # serat otot
        u = (k + 0.5) / 6.0
        y0 = cym - h2 + 2 * h2 * u
        ym = cym + (y0 - cym) * 0.55
        line_on(img, (cxm - w2 * 0.92, cym), (cxm - w2 * 0.45, y0), mix(accent, INK, 0.14), 5, qa * al)
        line_on(img, (cxm - w2 * 0.45, y0), (cxm + w2 * 0.45, ym), mix(accent, INK, 0.14), 5, qa * al)
        line_on(img, (cxm + w2 * 0.45, ym), (cxm + w2 * 0.92, cym), mix(accent, INK, 0.14), 5, qa * al)
    _lbl(img, 210, 900 + dy, "OTOT BETIS", font(FS, 30), mix(accent, INK, 0.04), q * al)
    _lbl(img, 210, 952 + dy, "TAMPILAN SERAT", font(FS, 22), MUTED, q * al)
    if qk > 0.35:                            # indikator menggenggam
        qb = esmooth(_dw(tl, dur, 0.30, 0.44))
        _lbl(img, 540, cym - h2 - 120, "MENGGENGAM KERAS, MENOLAK LEPAS", font(FS, 29),
             mix(accent, INK, 0.04), qb * al)
        for k in range(5):
            aa = tg * 1.8 + k * 1.26
            star4(img, cxm + (w2 + 54) * math.cos(aa), cym + (h2 + 40) * math.sin(aa) * 0.8,
                  6 + 7 * qk, mix(WARN27, WHITE, 0.55), qb * al * (0.55 + 0.45 * math.sin(tg * 3 + k)))
        qc = esmooth(_dw(tl, dur, 0.44, 0.56))
        gx, gy = cxm + w2 + 130, cym - 60
        _arrow_on(img, (gx, gy + 70), (gx, gy + 6), mix(WARN27, INK, 0.08), 6, qc * al)
        line_on(img, (gx - 46, gy), (gx + 46, gy), mix(WARN27, INK, 0.12), 8, qc * al)
        _lbl(img, gx, gy + 118, "TERHENTI", font(FS, 24), mix(WARN27, INK, 0.08), qc * al)
        _lbl(img, gx, gy + 160, "PULUHAN DETIK", font(FS, 24), MUTED, qc * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "SAKIT TAJAM SAMPAI SERAT RELAKS SENDIRI", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_mineral(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 3: empat elektrolit menjaga sinyal & otot; keringat membawanya pergi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    minr = [("Na", "NATRIUM"), ("K", "KALIUM"), ("Mg", "MAGNESIUM"), ("Ca", "KALSIUM")]
    for i, (simb, nama) in enumerate(minr):
        qi = esmooth(_dw(tl, dur, 0.05 + i * 0.055, 0.17 + i * 0.055))
        if qi <= 0.01:
            continue
        xx = 210 + i * 220
        yo = 6 * math.sin(tg * 1.5 + i * 1.4)
        ell(img, xx - 46, 880 + yo - 46, xx + 46, 880 + yo + 46, fill=mix(WHITE, accent, 0.16),
            alpha=qi * al, outline=accent, width=4)
        paste_c(img, xx, 880 + yo, simb, font(FB, 40), mix(accent, INK, 0.10), qi * al)
        _lbl(img, xx, 966 + yo, nama, font(FS, 19), MUTED, qi * al)
    qa = esmooth(_dw(tl, dur, 0.30, 0.42))
    if qa > 0:
        _lbl(img, 540, 1090, "TUGAS: SINYAL SARAF LANCAR + OTOT RILEKS", font(FS, 27),
             mix(accent, INK, 0.04), qa * al)
        for k in range(3):                   # sinyal rapi
            line_on(img, (170 + k * 260, 1160), (250 + k * 260, 1160), mix(accent, INK, 0.12), 5, qa * al)
            line_on(img, (250 + k * 260, 1160), (300 + k * 260, 1130), mix(accent, INK, 0.12), 5, qa * al)
            line_on(img, (300 + k * 260, 1130), (340 + k * 260, 1160), mix(accent, INK, 0.12), 5, qa * al)
        qb = esmooth(_dw(tl, dur, 0.42, 0.56))
        if qb > 0:                           # keringat membawa mineral pergi
            _icon_droplet29(img, 540, 1320, 2.0, mix(BLUE, INK, 0.05), qb * al, tg)
            for k in range(4):
                ph = ((tg * 0.5 + k * 0.25) % 1.0)
                dot_on(img, 540 - 60 + k * 40 + 6 * math.sin(ph * 6.0), 1340 + ph * 90, 4.5,
                       mix(accent, WHITE, 0.40), qb * al * (1 - ph) * 0.9)
            _lbl(img, 540, 1470, "BERKERINGAT LAMA TANPA MENGGANTI = CADANGAN BERKURANG",
                 font(FS, 26), mix(WARN27, INK, 0.05), qb * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "ISI ULANG: AIR + BUAH + MAKANAN BERGARAM", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def _icon_droplet29(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon tetes besar (keringat)."""
    if alpha <= 0.01:
        return
    poly_on(img, [(cx, cy - 30 * s), (cx + 20 * s, cy + 2 * s), (cx + 12 * s, cy + 22 * s),
                  (cx - 12 * s, cy + 22 * s), (cx - 20 * s, cy + 2 * s)],
            mix(col, WHITE, 0.42), alpha, outline=col, width=4)
    for k in range(2):
        ph = ((tg * 0.6 + k * 0.5) % 1.0)
        dot_on(img, cx - 30 * s - k * 8 * s, cy - 16 * s + ph * 26 * s, 4.5 * s,
               mix(col, WHITE, 0.45), alpha * (1 - ph) * 0.9)


def sc_malam(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 4: rantai penyebab kram malam hari."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    steps = [("OTOT LELAH SETELAH AKTIVITAS", "dumbel"), ("CAIRAN & MINERAL BERKURANG", "tetes"),
             ("TUBUH MENDINGIN SAAT TIDUR", "bulan"), ("KAKI MENUNJUK SAAT BERBARING", "kaki")]
    y0, gap = 812 + dy, 236
    col = mix(accent, INK, 0.12)
    for i, (txt, ik) in enumerate(steps):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.11, 0.22 + i * 0.11))
        if qi <= 0.01:
            continue
        yy = y0 + i * gap
        if ik == "dumbel":
            _icon_dumbel29(img, 170, yy, 1.35, col, qi * al)
        elif ik == "tetes":
            _icon_droplet29(img, 170, yy, 1.1, col, qi * al, tg)
        elif ik == "bulan":
            _icon_moon29(img, 170, yy, 1.5, col, qi * al)
        else:
            _icon_kaki29(img, 170, yy, 1.5, col, qi * al, tg)
        paste_r(img, 268, yy, txt, font(FS, 31), mix(accent, INK, 0.04), qi * al)
        if i < 3:
            qa = esmooth(_dw(tl, dur, 0.16 + i * 0.11, 0.28 + i * 0.11))
            _arrow_on(img, (170, yy + 56), (170, yy + gap - 56), mix(accent, WHITE, 0.22), 5, qa * al)
    qz = esmooth(_dw(tl, dur, 0.60, 0.76))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "BETIS = TEMPAT FAVORIT KRAM MALAM", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_atasi(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 5: cara langsung mengatasi kesemutan dan kram."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    col = mix(accent, INK, 0.12)
    qa = esmooth(_dw(tl, dur, 0.06, 0.18))   # kolom kesemutan
    _pill_c(img, 300, 840 + dy, "KESEMUTAN", font(FS, 31), mix(accent, INK, 0.10), qa * al)
    for i, (ikon, txt) in enumerate((("walk", "UBAH POSISI"), ("walk", "GERAKKAN KAKI"))):
        qi = esmooth(_dw(tl, dur, 0.12 + i * 0.06, 0.24 + i * 0.06))
        yy = 960 + i * 130 + dy
        _icon_walk29(img, 170, yy, 1.4, col, qi * al, tg + i * 1.6)
        _lbl(img, 360, yy, txt, font(FS, 24), mix(accent, INK, 0.05), qi * al)
    qn = esmooth(_dw(tl, dur, 0.24, 0.34))
    _lbl(img, 300, 1245 + dy, "SINYAL KEMBALI", font(FS, 20), MUTED, qn * al)
    _lbl(img, 300, 1281 + dy, "DALAM BEBERAPA DETIK", font(FS, 20), MUTED, qn * al)
    qb = esmooth(_dw(tl, dur, 0.32, 0.44))   # kolom kram
    _pill_c(img, 780, 840 + dy, "KRAM", font(FS, 31), mix(accent, INK, 0.10), qb * al)
    for i, (ikon, txt) in enumerate((("kaki", "TARIK UJUNG KAKI"), ("pijat", "PIJAT PELAN"),
                                     ("air", "MINUM AIR"))):
        qi = esmooth(_dw(tl, dur, 0.38 + i * 0.06, 0.50 + i * 0.06))
        yy = 960 + i * 130 + dy
        if ikon == "kaki":
            _icon_kaki29(img, 650, yy, 1.5, col, qi * al, tg)
        elif ikon == "pijat":
            _icon_pijat29(img, 650, yy, 1.2, col, qi * al, tg)
        else:
            _icon_water28(img, 650, yy, 1.3, col, qi * al, tg)
        _lbl(img, 855, yy, txt, font(FS, 24), mix(accent, INK, 0.05), qi * al)
    qm = esmooth(_dw(tl, dur, 0.56, 0.66))
    _lbl(img, 780, 1375 + dy, "PEGANG SAMPAI OTOT RELAKS", font(FS, 20), MUTED, qm * al)
    qz = esmooth(_dw(tl, dur, 0.66, 0.80))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "JANGAN DIPAKSA BERGERAK KERAS SAAT OTOT KUNO", font(FS, 27),
                mix(accent, INK, 0.10), qz * al, dot=True)


def _icon_walk29(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon orang berjalan (gerak)."""
    if alpha <= 0.01:
        return
    dot_on(img, cx, cy - 22 * s, 8 * s, col, alpha)
    ph = math.sin(tg * 5.0)
    line_on(img, (cx, cy - 14 * s), (cx, cy + 4 * s), col, 6 * s, alpha)
    line_on(img, (cx, cy + 4 * s), (cx - 10 * s + ph * 6 * s, cy + 24 * s), col, 5 * s, alpha)
    line_on(img, (cx, cy + 4 * s), (cx + 10 * s - ph * 6 * s, cy + 24 * s), col, 5 * s, alpha)
    line_on(img, (cx, cy - 8 * s), (cx - 12 * s, cy + 2 * s - ph * 4 * s), col, 4 * s, alpha)
    line_on(img, (cx, cy - 8 * s), (cx + 12 * s, cy + 2 * s + ph * 4 * s), col, 4 * s, alpha)


def sc_cegah(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 6: pencegahan sehari-hari."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    pos = [(300, 950), (780, 950), (300, 1330), (780, 1330)]
    labels = ["AIR CUKUP TIAP HARI", "BUAH & MAKANAN BERGARAM", "PEREGANGKAN SEBELUM TIDUR",
              "JANGAN SATU POSISI LAMA"]
    col = mix(accent, INK, 0.12)
    for i, ((cx, cy), txt) in enumerate(zip(pos, labels)):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.10, 0.22 + i * 0.10))
        if qi <= 0.01:
            continue
        yo = 7 * math.sin(tg * 1.4 + i * 1.6)
        if i == 0:
            _icon_water28(img, cx, cy - 40 + yo, 1.5, col, qi * al, tg)
        elif i == 1:
            for j, simb in enumerate(("K", "Na", "Mg")):
                xx = cx - 62 + j * 62
                ell(img, xx - 24, cy - 64 + yo, xx + 24, cy - 16 + yo, fill=mix(WHITE, accent, 0.16),
                    alpha=qi * al, outline=col, width=3)
                paste_c(img, xx, cy - 40 + yo, simb, font(FB, 22), mix(col, INK, 0.10), qi * al)
        elif i == 2:
            _icon_stretch29(img, cx, cy - 40 + yo, 1.6, col, qi * al, tg)
        else:
            _icon_jam28(img, cx, cy - 40 + yo, 1.5, col, qi * al, tg)
        _pill_c(img, cx, cy + 108, txt, font(FS, 24), mix(accent, INK, 0.08), qi * al)
    qz = esmooth(_dw(tl, dur, 0.56, 0.72))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "MURAH, SEDERHANA, DAN TERBUKTI", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_waspada_kaki(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 7: tanda harus ke dokter."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    signs = ["KESEMUTAN TANPA SEBAB, TERUS-MENERUS", "MATI RASA / KELEMUHAN BERKEPANJANGAN",
             "KRAM HAMPIR TIAP MALAM"]
    for i, txt in enumerate(signs):
        qi = esmooth(_dw(tl, dur, 0.05 + i * 0.09, 0.18 + i * 0.09))
        if qi <= 0.01:
            continue
        yy = 840 + i * 116 + dy
        dot_on(img, 118, yy, 10, mix(WARN27, INK, 0.05), qi * al * (0.7 + 0.3 * math.sin(tg * 4 + i)))
        _pill_c(img, 540, yy, txt, font(FS, 27), mix(WARN27, INK, 0.10), qi * al, bg=mix(WHITE, WARN27, 0.08))
    qa = esmooth(_dw(tl, dur, 0.38, 0.50))
    if qa > 0:
        _arrow_on(img, (540, 1230 + dy), (540, 1300 + dy), mix(accent, INK, 0.12), 6, qa * al)
    qb = esmooth(_dw(tl, dur, 0.48, 0.60))
    if qb > 0:
        _icon_steto28(img, 320, 1420 + dy, 1.7, mix(accent, INK, 0.12), qb * al, tg)
        ring_on(img, 368, 1471 + dy, 26 + 7 * math.sin(tg * 3.0), mix(accent, WHITE, 0.55), 4, qb * al * 0.75)
        _lbl(img, 640, 1408 + dy, "PERIKSA KE DOKTER", font(FS, 33), mix(accent, INK, 0.03), qb * al)
        _lbl(img, 640, 1466 + dy, "SARAF & KADAR ELEKTROLIT DIPERIKSA", font(FS, 25), MUTED, qb * al)
    qz = esmooth(_dw(tl, dur, 0.68, 0.82))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "BISA TANDA GANGGUAN SARAF ATAU DIABETES", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


VISUALS.update({
    "intro_kaki": sc_intro_kaki,
    "saraf": sc_saraf,
    "ototkram": sc_ototkram,
    "mineral": sc_mineral,
    "malam": sc_malam,
    "atasi": sc_atasi,
    "cegah": sc_cegah,
    "waspada_kaki": sc_waspada_kaki,
})


def _selftest29():
    """Uji cepat adegan Ep29 sebelum dipakai render."""
    names = ["intro_kaki", "saraf", "ototkram", "mineral", "malam", "atasi", "cegah", "waspada_kaki"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "KRAM & KESEMUTAN?"], "accent": "#1F7A6B"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep29: 8 adegan OK")


if __name__ == "__main__":
    _selftest29()

# ====================== Ep30: Bau Mulut ======================

def _gigi30(img, cx, cy, s, col, alpha, lobang=0.0):
    """Ikon gigi (kunci: lobus 0..1 = gigi berlubang)."""
    if alpha <= 0.01:
        return
    poly_on(img, [(cx - 20 * s, cy - 26 * s), (cx + 20 * s, cy - 26 * s), (cx + 22 * s, cy - 4 * s),
                  (cx + 14 * s, cy + 26 * s), (cx + 5 * s, cy + 2 * s), (cx - 5 * s, cy + 2 * s),
                  (cx - 14 * s, cy + 26 * s), (cx - 22 * s, cy - 4 * s)],
            mix(col, WHITE, 0.55), alpha, outline=col, width=3)
    if lobang > 0:
        ell(img, cx - 7 * s, cy - 16 * s, cx + 7 * s, cy - 2 * s, fill=mix(col, INK, 0.55),
            alpha=alpha * lobang)


def _sikat30(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon sikat gigi miring + busa kecil."""
    if alpha <= 0.01:
        return
    dx, dyv = 16 * s, -10 * s
    line_on(img, (cx - dx, cy + dyv), (cx + dx * 0.4, cy - dyv * 0.6), col, 5 * s, alpha)
    rrect_on(img, cx + dx * 0.3, cy - dyv * 0.5 - 6 * s, cx + dx * 1.05, cy - dyv * 0.5 + 6 * s,
             4 * s, mix(col, WHITE, 0.5), alpha, outline=col, width=3)
    for k in range(4):
        x0 = cx + dx * 0.38 + k * 5.2 * s
        y0 = cy - dyv * 0.5 - 8 * s - (k % 2) * 2 * s
        line_on(img, (x0, y0), (x0 + 2 * s, y0 - 5 * s), col, 2.4 * s, alpha)
    if tg:
        ph = ((tg * 0.8) % 1.0)
        dot_on(img, cx + dx * 0.7 + 8 * s * math.sin(ph * 6.0), cy - dyv * 0.5 - 14 * s - ph * 10 * s,
               3.5 * s, mix(col, WHITE, 0.45), alpha * (1 - ph) * 0.8)


def _garuk30(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon alat garuk lidah (U shape)."""
    if alpha <= 0.01:
        return
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    hw, hh = 26 * s, 18 * s
    dd.arc([S(cx - hw), S(cy - hh), S(cx + hw), S(cy + hh * 0.8)], 200, 340,
           fill=mix(col, INK, 0.10) + (255,), width=max(1, int(S(7 * s))))
    _put(img, lay, alpha)
    line_on(img, (cx - hw, cy - hh * 0.45), (cx - hw, cy + 22 * s), col, 5 * s, alpha)
    line_on(img, (cx + hw, cy - hh * 0.45), (cx + hw, cy + 22 * s), col, 5 * s, alpha)
    line_on(img, (cx, cy + 24 * s), (cx, cy + 40 * s), col, 6 * s, alpha)


def _bakteri30(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon bakteri: blob + silia bergetar."""
    if alpha <= 0.01:
        return
    wab = 2.0 * s * math.sin(tg * 4.0 + cx * 0.1)
    ell(img, cx - 13 * s, cy - 9 * s, cx + 13 * s, cy + 9 * s, fill=mix(col, WHITE, 0.40),
        alpha=alpha, outline=mix(col, INK, 0.10), width=3)
    for k in range(4):
        aa = -0.8 + k * 0.55
        x0, y0 = cx + 12 * s * math.cos(aa), cy + 8 * s * math.sin(aa)
        line_on(img, (x0, y0), (x0 + 8 * s * math.cos(aa) + wab, y0 + 8 * s * math.sin(aa)),
                mix(col, INK, 0.12), 2.6 * s, alpha)
    for k in range(3):
        dot_on(img, cx - 5 * s + k * 5 * s, cy, 2.2 * s, mix(col, INK, 0.25), alpha)


def _bau30(img, cx, cy, s, col, alpha, tg=0.0):
    """Ikon kipas bau: 3 garis berombak naik."""
    if alpha <= 0.01:
        return
    for k in range(3):
        ph = ((tg * 0.9 + k / 3.0) % 1.0)
        yy = cy - ph * 26 * s
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        pts = [(S(cx + (k - 1) * 9 * s + 5 * s * math.sin(ph * 9.0 + k)), S(yy + j * 6 * s))
               for j in range(5)]
        dd.line(pts, fill=mix(col, WHITE, 0.30) + (255,), width=max(1, int(S(3.4 * s))))
        _put(img, lay, alpha * (1 - ph) * 0.9)


def sc_intro_mulut(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: bicara dekat teman, teman mundur; napas bau bergelombang."""
    for i, l in enumerate(sc.get("lines") or []):
        q = esmooth(seg(tl, 0.18 + i * 0.20, 0.82 + i * 0.20))
        if q <= 0:
            continue
        f = _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66)
        paste_c(img, 540, (516 + i * 96) + dy, l, f, INK if i == 0 else mix(accent, INK, 0.05), q * al)
    q1 = esmooth(seg(tl, 0.5, 0.95))
    if q1 > 0:
        _pill_c(img, 540, 676 + dy, "PUNYA NAMA ILMIAH: HALITOSIS", font(FS, 28),
                mix(accent, INK, 0.10), q1 * al, dot=True)
    q2 = esmooth(seg(tl, 0.30, 1.0))
    if q2 <= 0.02:
        return
    pang = mix(CREAM, mix(accent, INK, 0.30), 0.24)
    rrect_on(img, 104, 748 + dy, 976, 1584 + dy, 46, pang, q2 * al)
    rrect_on(img, 104, 1464 + dy, 976, 1584 + dy, 46, mix(pang, INK, 0.16), q2 * al)
    _dust(img, 134, 808 + dy, 946, 1420 + dy, 8, tg, q2 * al * 0.4, mix(pang, WHITE, 0.55))
    # kiri: orang bicara (mulut terbuka + kipas bau ke kanan)
    hx, hy = 300, 1080 + dy
    kol = mix(pang, WHITE, 0.34)
    ell(img, hx - 42, hy - 86, hx + 42, hy - 2, fill=kol, alpha=q2 * al)
    rrect_on(img, hx - 46, hy + 12, hx + 46, hy + 190, 26, kol, q2 * al)
    lay = _layer(img)                       # mulut terbuka
    dd = ImageDraw.Draw(lay)
    dd.ellipse([S(hx - 12), S(hy - 48), S(hx + 14), S(hy - 26)], fill=mix(pang, INK, 0.40) + (255,))
    _put(img, lay, q2 * al)
    for k in range(3):                      # gelombang napas ke kanan
        ph = ((tg * 0.8 + k / 3.0) % 1.0)
        xx = hx + 70 + ph * 150
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        pts = [(S(xx + j * 7), S(hy - 40 + 13 * math.sin(ph * 8.0 + j * 1.4 + k))) for j in range(6)]
        dd.line(pts, fill=mix(WARN27, WHITE, 0.40) + (255,), width=max(1, int(S(4))))
        _put(img, lay, q2 * al * (1 - ph) * 0.9)
    _bau30(img, hx + 190, hy - 70, 1.2, mix(WARN27, INK, 0.05), q2 * al * 0.8, tg)
    # kanan: teman condong menjauh
    fx, fy = 740, 1100 + dy
    lean = 26 * esmooth(seg(tl, 1.2, 2.0))
    line_on(img, (fx - lean * 0.4, fy - 60), (fx + lean, fy + 60), kol, 12, q2 * al)
    ell(img, fx + lean - 30 - 42, fy - 118 - 40, fx + lean - 30 + 42, fy - 118 + 44,
        fill=kol, alpha=q2 * al)
    line_on(img, (fx + lean, fy + 60), (fx - 10, fy + 150), kol, 11, q2 * al)
    line_on(img, (fx + lean, fy + 60), (fx + 60, fy + 150), kol, 11, q2 * al)
    _arrow_on(img, (fx + 90, fy - 40), (fx + 150, fy - 70), mix(WARN27, INK, 0.10), 6,
              q2 * al * esmooth(seg(tl, 1.2, 2.0)))
    ell(img, fx + lean + 30, fy - 130, fx + lean + 46, fy - 114, fill=BLUE, alpha=q2 * al * 0.8)  # keringat
    _lbl(img, 300, 1380 + dy, "KAMU BICARA", font(FS, 24), mix(pang, INK, 0.10), q2 * al)
    _lbl(img, 740, 1380 + dy, "TEMANMU MUNDUR", font(FS, 24), mix(pang, INK, 0.10), q2 * al)
    q4 = esmooth(seg(tl, 2.6, 3.2))
    if q4 > 0:
        _pill_c(img, 540, 1660 + dy, "RAJIN SIKAT GIGI TAPI TETAP BAU? INI SAINS", font(FS, 25),
                mix(accent, INK, 0.10), q4 * al, dot=True)


def sc_sumberbau(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 1: bakteri mencerna sisa protein -> gas belerang."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    # profil mulut: deretan gigi atas + lidah
    qx, qy = 540, 1290 + dy
    rrect_on(img, 150, qy - 250, 930, qy + 210, 60, mix(WHITE, accent, 0.14), q * al,
             outline=mix(accent, INK, 0.10), width=4)
    for k in range(8):                       # gigi atas
        gx = 208 + k * 72
        rrect_on(img, gx, qy - 250, gx + 52, qy - 172, 14, mix(WHITE, accent, 0.55), q * al,
                 outline=mix(accent, INK, 0.08), width=3)
    ell(img, 200, qy - 60, 880, qy + 190, fill=mix(accent, INK, 0.14), alpha=q * al)  # lidah
    for r in range(3):                       # papila (karpet kecil)
        for k in range(10):
            xx = 250 + k * 64 + (r % 2) * 30
            yy = qy + 30 + r * 44
            arc_ = mix(WHITE, accent, 0.35)
            dot_on(img, xx, yy, 5, arc_, q * al)
    _lbl(img, 540, qy + 232, "LIDAH", font(FS, 24), MUTED, q * al)
    qa = esmooth(_dw(tl, dur, 0.12, 0.26))   # sisa makanan jatuh ke lidah
    for k in range(4):
        ph = ((tg * 0.5 + k * 0.25) % 1.0)
        dot_on(img, 300 + k * 130, qy - 140 + ph * 120, 5, mix(WARN27, WHITE, 0.30),
               qa * al * (0.4 + 0.6 * (1 - ph)))
    _lbl(img, 540, qy - 300, "SISA MAKANAN + PROTEIN", font(FS, 26), mix(accent, INK, 0.04), qa * al)
    qb = esmooth(_dw(tl, dur, 0.26, 0.40))   # bakteri berjejak
    for k in range(7):
        bx = 280 + (k % 4) * 150 + (k // 4) * 60
        by = qy + 60 + (k // 4) * 70
        _bakteri30(img, bx, by, 1.1 + 0.25 * math.sin(tg * 3 + k), mix(accent, INK, 0.05), qb * al, tg + k)
    _lbl(img, 175, qy - 60, "MILIARAN", font(FS, 25), mix(accent, INK, 0.06), qb * al)
    _lbl(img, 175, qy - 16, "BAKTERI", font(FS, 25), mix(accent, INK, 0.06), qb * al)
    qc = esmooth(_dw(tl, dur, 0.44, 0.60))   # gas belerang naik ke hidung
    for k in range(3):
        ph = ((tg * 0.7 + k / 3.0) % 1.0)
        xx = 480 + k * 60 + 10 * math.sin(ph * 7.0)
        yy = qy - 250 - ph * 190
        dot_on(img, xx, yy, 6 - 2 * ph, mix(WARN27, WHITE, 0.35), qc * al * (1 - ph))
    nx, ny = 540, 830 + dy
    poly_on(img, [(nx - 26, ny - 20), (nx + 10, ny - 26), (nx + 30, ny + 16), (nx - 6, ny + 22)],
            mix(accent, INK, 0.12), qc * al, outline=mix(accent, INK, 0.08), width=4)
    _lbl(img, nx, ny - 58, "HIDUNG", font(FS, 22), MUTED, qc * al)
    _lbl(img, 820, 950 + dy, "GAS BELERANG", font(FS, 26), mix(WARN27, INK, 0.05), qc * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "BAUNYA KHAS BELERANG - SAMA SEPERTI TELUR BUSUK", font(FS, 26),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_pagihari(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 2: malam hari air liur berkurang -> bakteri berpesta."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    _icon_moon29(img, 180, 900 + dy, 1.6, mix(accent, INK, 0.12), q * al)
    _lbl(img, 180, 984 + dy, "SAAT TIDUR", font(FS, 25), mix(accent, INK, 0.05), q * al)
    stages = [(420, "22.00"), (700, "02.00"), (940, "06.00")]
    for i, (xx, jam) in enumerate(stages):
        qi = esmooth(_dw(tl, dur, 0.08 + i * 0.12, 0.22 + i * 0.12))
        if qi <= 0.01:
            continue
        _icon_jam28(img, xx, 880 + dy, 0.8, mix(accent, INK, 0.10), qi * al, tg)
        _lbl(img, xx, 952 + dy, jam, font(FS, 23), MUTED, qi * al)
        ss = 1.9 - i * 0.55                     # tetes air liur mengecil
        _icon_droplet29(img, xx, 1140 + dy, ss, mix(accent, INK, 0.10), qi * al, tg)
        _lbl(img, xx, 1216 + dy, "AIR LIUR", font(FS, 20), mix(accent, INK, 0.06), qi * al)
        n = 2 + i * 3                           # bakteri makin banyak
        for k in range(n):
            _bakteri30(img, xx - 66 + (k % 3) * 44, 1330 + dy + (k // 3) * 52,
                       0.9 + 0.1 * math.sin(tg * 3 + k), mix(accent, INK, 0.05), qi * al, tg + k)
        _lbl(img, xx, 1452 + dy, ("MULAI TIDUR", "BAKTERI NAIK", "BERPESTA")[i],
             font(FS, 23), mix(WARN27, INK, 0.06) if i == 2 else MUTED, qi * al)
        if i < 2:
            qa = esmooth(_dw(tl, dur, 0.18 + i * 0.12, 0.30 + i * 0.12))
            _arrow_on(img, (xx + 90, 1140 + dy), (stages[i + 1][0] - 90, 1140 + dy),
                      mix(accent, WHITE, 0.22), 5, qa * al)
    qz = esmooth(_dw(tl, dur, 0.60, 0.76))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "AIR LIUR = PENCUCI ALAMI MULUT", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_lidah(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 3: mitos 'sikat gigi cukup' dibongkar - markas di lidah."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.14))
    if q <= 0.02:
        return
    cx0, cy0 = 540, 1180 + dy
    poly_on(img, [(cx0 - 300, cy0 - 150), (cx0 + 300, cy0 - 150), (cx0 + 250, cy0 + 120),
                  (cx0, cy0 + 190), (cx0 - 250, cy0 + 120)],
            mix(accent, INK, 0.16), q * al, outline=mix(accent, INK, 0.10), width=5)
    qa = esmooth(_dw(tl, dur, 0.10, 0.24))
    for r in range(4):                          # tekstur karpet papila
        for k in range(12):
            xx = cx0 - 260 + k * 47 + (r % 2) * 22
            yy = cy0 - 100 + r * 78
            if -240 < xx - cx0 < 240:
                dot_on(img, xx, yy, 7, mix(WHITE, accent, 0.30), qa * al)
    _lbl(img, cx0, cy0 + 236, "PERMUKAAN LIDAH BERKARPET", font(FS, 26),
         mix(accent, INK, 0.05), qa * al)
    qb = esmooth(_dw(tl, dur, 0.26, 0.40))
    for k in range(6):                          # bakteri terperangkap (diterangi)
        bx = cx0 - 180 + (k % 3) * 180
        by = cy0 - 40 + (k // 3) * 110
        pulse = 0.5 + 0.5 * math.sin(tg * 3.0 + k)
        ring_on(img, bx, by, 22 + 8 * pulse, mix(WARN27, WHITE, 0.45), 4, qb * al * (0.5 + 0.5 * pulse))
        _bakteri30(img, bx, by, 1.2, mix(WARN27, INK, 0.05), qb * al, tg + k)
    _lbl(img, cx0, cy0 - 220, "MARKAS UTAMA BAKTERI BAU", font(FS, 29), mix(WARN27, INK, 0.04), qb * al)
    _sikat30(img, 250, 830 + dy, 1.6, mix(accent, INK, 0.12), esmooth(_dw(tl, dur, 0.40, 0.52)) * al, tg)
    _lbl(img, 250, 906 + dy, "Sikat gigi: bersih", font(FS, 22), MUTED,
         esmooth(_dw(tl, dur, 0.40, 0.52)) * al)
    qc = esmooth(_dw(tl, dur, 0.48, 0.60))
    if qc > 0:                                   # coretan merah pada mitos
        lx = 540
        line_on(img, (lx - 260, 800 + dy), (lx + 260, 852 + dy), WARN27, 9,
                qc * al * esmooth(_dw(tl, dur, 0.48, 0.56)))
        _lbl(img, lx, 770 + dy, "\"SIKAT GIGI ITU CUKUP\"", font(FS, 30), MUTED, qc * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "SEPERTI MENYAPU LANTAI TANPA CUCI KARPET", font(FS, 26),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_pemicu_mulut(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 4: pemicu tambahan yang mendarat satu per satu."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    col = mix(accent, INK, 0.12)
    pos = [(300, 900), (780, 900), (300, 1250), (780, 1250)]
    labels = ["GIGI BERLUBANG", "SARIWAN LAMA", "BATU AMANDEL", "KURANG MINUM"]
    for i, ((cx, cy), txt) in enumerate(zip(pos, labels)):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.11, 0.22 + i * 0.11))
        if qi <= 0.01:
            continue
        yo = 7 * math.sin(tg * 1.4 + i * 1.6)
        if i == 0:
            _gigi30(img, cx, cy - 40 + yo, 1.7, col, qi * al, lobang=1.0)
        elif i == 1:
            ell(img, cx - 34, cy - 60 + yo, cx + 34, cy - 8 + yo, fill=mix(WHITE, col, 0.35),
                alpha=qi * al, outline=col, width=3)
            ell(img, cx - 8, cy - 46 + yo, cx + 10, cy - 28 + yo, fill=mix(WARN27, WHITE, 0.45),
                alpha=qi * al)
        elif i == 2:
            ell(img, cx - 30, cy - 70 + yo, cx + 30, cy + 40 + yo, fill=mix(col, WHITE, 0.55),
                alpha=qi * al, outline=col, width=3)
            for k in range(3):
                ell(img, cx - 12 + k * 10, cy - 20 + k * 12, cx - 2 + k * 10, cy - 10 + k * 12,
                    fill=mix(WARN27, INK, 0.20), alpha=qi * al)
            _bau30(img, cx + 34, cy - 60 + yo, 1.0, col, qi * al, tg)
        else:
            _icon_droplet29(img, cx, cy - 40 + yo, 1.5, col, qi * al, tg)
            line_on(img, (cx - 34, cy - 84 + yo), (cx + 34, cy + 4 + yo), WARN27, 7, qi * al)
        _pill_c(img, cx, cy + 106, txt, font(FS, 25), mix(accent, INK, 0.08), qi * al)
    qn = esmooth(_dw(tl, dur, 0.48, 0.60))
    if qn > 0:
        _pill_c(img, 540, 1450 + dy, "ROKOK - KOPI - TERLALU LAMA LAPAR", font(FS, 26),
                mix(accent, INK, 0.08), qn * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "SEMUA ITU TEMPAT BAKTERI BERTAMBAH", font(FS, 27),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_atasi_mulut(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 5: tiga langkah cepat mengatasi bau."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    col = mix(accent, INK, 0.12)
    steps = [(240, "garuk", "GARUK LIDAH", "01"), (540, "air", "MINUM AIR", "02"),
             (840, "permen", "PERMEN BEBAS GULA", "03")]
    for i, (xx, ik, txt, nom) in enumerate(steps):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.12, 0.22 + i * 0.12))
        if qi <= 0.01:
            continue
        yo = 7 * math.sin(tg * 1.4 + i * 1.6)
        if ik == "garuk":
            ell(img, xx - 46, 950 + yo, xx + 46, 1080 + yo, fill=mix(accent, INK, 0.14), alpha=qi * al)
            for k in range(3):
                dot_on(img, xx - 20 + k * 20, 1000 + yo, 5, mix(WHITE, accent, 0.30), qi * al)
            _garuk30(img, xx, 948 + yo, 1.5, col, qi * al, tg)
        elif ik == "air":
            _icon_water28(img, xx, 1000 + yo, 1.6, col, qi * al, tg)
        else:
            rrect_on(img, xx - 40, 960 + yo, xx + 40, 1024 + yo, 22, mix(WHITE, col, 0.45),
                     qi * al, outline=col, width=3)
            star4(img, xx + 48, 952 + yo, 8 + 4 * math.sin(tg * 3 + i), mix(col, WHITE, 0.5), qi * al)
        _pill_c(img, xx, 830 + dy, nom, font(FB, 30), mix(accent, INK, 0.10), qi * al)
        _pill_c(img, xx, 1196 + dy, txt, font(FS, 24), mix(accent, INK, 0.08), qi * al)
        if i < 2:
            qa = esmooth(_dw(tl, dur, 0.20 + i * 0.12, 0.32 + i * 0.12))
            _arrow_on(img, (xx + 96, 1010 + dy), (steps[i + 1][0] - 96, 1010 + dy),
                      mix(accent, WHITE, 0.22), 5, qa * al)
    qz = esmooth(_dw(tl, dur, 0.56, 0.72))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "PERMEN KARET MEMBUAT AIR LIUR MENGALIR LAGI", font(FS, 26),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_cegah_mulut(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 6: rutinitas pencegahan harian."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    pos = [(300, 950), (780, 950), (300, 1330), (780, 1330)]
    labels = ["SIKAT GIGI 2X SEHARI", "BERSIHKAN LIDAH JUGA", "AIR CUKUP TIAP HARI",
              "MAKAN TERATUR"]
    col = mix(accent, INK, 0.12)
    for i, ((cx, cy), txt) in enumerate(zip(pos, labels)):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.10, 0.22 + i * 0.10))
        if qi <= 0.01:
            continue
        yo = 7 * math.sin(tg * 1.4 + i * 1.6)
        if i == 0:
            _sikat30(img, cx, cy - 40 + yo, 1.9, col, qi * al, tg)
        elif i == 1:
            ell(img, cx - 40, cy - 80 + yo, cx + 40, cy + 30 + yo, fill=mix(accent, INK, 0.14),
                alpha=qi * al)
            for k in range(4):
                dot_on(img, cx - 24 + k * 16, cy - 20 + yo, 5, mix(WHITE, accent, 0.30), qi * al)
            _garuk30(img, cx, cy - 86 + yo, 1.3, col, qi * al, tg)
        elif i == 2:
            _icon_water28(img, cx, cy - 40 + yo, 1.6, col, qi * al, tg)
        else:
            ell(img, cx - 44, cy - 60 + yo, cx + 44, cy - 12 + yo, fill=mix(WHITE, col, 0.45),
                alpha=qi * al, outline=col, width=3)
            ell(img, cx - 22, cy - 48 + yo, cx + 22, cy - 24 + yo, fill=mix(col, WHITE, 0.60),
                alpha=qi * al)
            _icon_jam28(img, cx + 54, cy - 76 + yo, 0.8, col, qi * al, tg)
        _pill_c(img, cx, cy + 108, txt, font(FS, 24), mix(accent, INK, 0.08), qi * al)
    qz = esmooth(_dw(tl, dur, 0.56, 0.72))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "KURANGI ROKOK DAN KOPI BERLEBIHAN", font(FS, 27),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_dokter_gigi(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 7: tanda harus ke dokter gigi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(_dw(tl, dur, 0.03, 0.12))
    if q <= 0.02:
        return
    signs = ["BAU TIDAK HILANG WALAU MULUT BERSIH", "GUSI BENGKAK ATAU SERING BERDARAH",
             "GIGI NYERI ATAU ADA LUBANG"]
    for i, txt in enumerate(signs):
        qi = esmooth(_dw(tl, dur, 0.05 + i * 0.09, 0.18 + i * 0.09))
        if qi <= 0.01:
            continue
        yy = 840 + i * 116 + dy
        dot_on(img, 118, yy, 10, mix(WARN27, INK, 0.05), qi * al * (0.7 + 0.3 * math.sin(tg * 4 + i)))
        _pill_c(img, 540, yy, txt, font(FS, 27), mix(WARN27, INK, 0.10), qi * al, bg=mix(WHITE, WARN27, 0.08))
    qa = esmooth(_dw(tl, dur, 0.38, 0.50))
    if qa > 0:
        _arrow_on(img, (540, 1230 + dy), (540, 1300 + dy), mix(accent, INK, 0.12), 6, qa * al)
    qb = esmooth(_dw(tl, dur, 0.48, 0.60))
    if qb > 0:
        _gigi30(img, 300, 1400 + dy, 2.4, mix(accent, INK, 0.10), qb * al)
        pulse = 0.5 + 0.5 * math.sin(tg * 3.0)
        ring_on(img, 300, 1400 + dy, 64 + 14 * pulse, mix(accent, WHITE, 0.55), 4, qb * al * 0.6)
        _icon_steto28(img, 386, 1452 + dy, 1.2, mix(accent, INK, 0.12), qb * al, tg)
        _lbl(img, 650, 1408 + dy, "PERIKSA KE DOKTER GIGI", font(FS, 31), mix(accent, INK, 0.03), qb * al)
        _lbl(img, 650, 1466 + dy, "LUBANG, SARIAWAN LAMA, ATAU GUSI", font(FS, 24), MUTED, qb * al)
    qz = esmooth(_dw(tl, dur, 0.68, 0.82))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "BAU DARI HIDUNG PADA ANAK = SEGERA PERIKSA", font(FS, 26),
                mix(accent, INK, 0.10), qz * al, dot=True)


VISUALS.update({
    "intro_mulut": sc_intro_mulut,
    "sumberbau": sc_sumberbau,
    "pagihari": sc_pagihari,
    "lidah": sc_lidah,
    "pemicu_mulut": sc_pemicu_mulut,
    "atasi_mulut": sc_atasi_mulut,
    "cegah_mulut": sc_cegah_mulut,
    "doktergigi": sc_dokter_gigi,
})


def _selftest30():
    """Uji cepat adegan Ep30 sebelum dipakai render."""
    names = ["intro_mulut", "sumberbau", "pagihari", "lidah", "pemicu_mulut",
             "atasi_mulut", "cegah_mulut", "doktergigi"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "MULUT BAU?"], "accent": "#8C4A2F"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep30: 8 adegan OK")


if __name__ == "__main__":
    _selftest30()

# ====================== Paket gerak v4 (animasi populer) + Ep31: Mata Kedutan ======================

def _pop_pill(img, cx, cy, text, fsz, fill, alpha, tt, fg=None, dot=False):
    """Kinetic typography: pil pop-in dengan overshoot (bounce) ala Shorts."""
    if alpha <= 0.01 or tt <= 0 or not text:
        return
    f = font(FS, fsz)
    w_ = tw(text, f) + 56
    h_ = tlh(f) + 30
    scale = 0.55 + 0.45 * eob(min(1.0, tt), 1.8)
    lay = Image.new("RGBA", (int(S(w_ + 8)), int(S(h_ + 8))), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([S(4), S(4), S(4 + w_), S(4 + h_)], radius=S(h_ / 2), fill=fill + (255,))
    fg2 = fg or mix(fill, INK, 0.40)
    if dot:
        dd.ellipse([S(26), S(4 + h_ / 2 - 7), S(40), S(4 + h_ / 2 + 7)], fill=fg2 + (255,))
    dd.text((S(4 + w_ / 2), S(4 + h_ / 2)), text, font=f, fill=fg2 + (255,), anchor="mm")
    lw = max(1, int(lay.width * scale))
    lh = max(1, int(lay.height * scale))
    lay = lay.resize((lw, lh), Image.LANCZOS)
    pos = (int(S(cx) - lw / 2), int(S(cy) - lh / 2))
    if alpha < 0.995:
        a = lay.getchannel("A").point(lambda v: int(v * clamp(alpha)))
        img.paste(lay.convert("RGB"), pos, a)
    else:
        img.paste(lay, pos, lay)


def _pop_txt(img, cx, cy, text, f, fill, alpha, tt, dy=0.0):
    """Teks pop-in memakai scale overshoot paste_c."""
    if alpha <= 0.01 or tt <= 0 or not text:
        return
    paste_c(img, cx, cy, text, f, fill, alpha * min(1.0, tt * 2.0),
            scale=0.55 + 0.45 * eob(min(1.0, tt), 1.8), dy=dy)


def _shine_on(img, x0, y0, x1, y1, tt, alpha, col=None):
    """Sweep kilau diagonal di dalam kotak (populer untuk kartu/pil)."""
    if alpha <= 0.01 or tt <= 0:
        return
    from PIL import ImageChops
    col = col or mix(WHITE, CREAM, 0.10)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    sx = x0 - 160 + (x1 - x0 + 320) * clamp(tt)
    dd.polygon([(S(sx), S(y0)), (S(sx + 70), S(y0)), (S(sx - 200), S(y1)), (S(sx - 270), S(y1))],
               fill=col + (255,))
    mask = Image.new("L", lay.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=S(28), fill=255)
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), mask))
    _put(img, lay, alpha * 0.55)


def _meter_on(img, cx, cy, r, frac, col, alpha, needle=None):
    """Gauge 180 derajat: busur isi + jarum (untuk pemicu/level)."""
    if alpha <= 0.01:
        return
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    bb = [S(cx - r), S(cy - r), S(cx + r), S(cy + r)]
    dd.arc(bb, 180, 360, fill=mix(col, CREAM, 0.55) + (255,), width=max(2, int(S(12))))
    if frac > 0.01:
        dd.arc(bb, 180, 180 + 180 * clamp(frac), fill=col + (255,), width=max(2, int(S(12))))
    for k in range(5):
        aa = math.radians(180 + 180 * k / 4.0)
        dd.line([S(cx + (r + 14) * math.cos(aa)), S(cy + (r + 14) * math.sin(aa)),
                 S(cx + (r + 22) * math.cos(aa)), S(cy + (r + 22) * math.sin(aa))],
                fill=mix(col, INK, 0.15) + (255,), width=max(1, int(S(3))))
    aa = math.radians(180 + 180 * clamp(frac))
    dd.line([S(cx), S(cy), S(cx + (r - 16) * math.cos(aa)), S(cy + (r - 16) * math.sin(aa))],
            fill=(needle or mix(col, INK, 0.30)) + (255,), width=max(2, int(S(6))))
    dd.ellipse([S(cx - 8), S(cy - 8), S(cx + 8), S(cy + 8)], fill=mix(col, INK, 0.30) + (255,))
    _put(img, lay, alpha)


def _bar_on(img, x, y, w, h, frac, col, alpha, tg=0.0):
    """Bar level dengan garis kecepatan berjalan."""
    if alpha <= 0.01:
        return
    rrect_on(img, x, y, x + w, y + h, h / 2, mix(col, CREAM, 0.55), alpha)
    fw = w * clamp(frac)
    if fw <= h / 2:
        return
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([S(x), S(y), S(x + w), S(y + h)], radius=S(h / 2), fill=col + (255,))
    for k in range(int(w / 24) + 2):
        xx = x + ((k * 24 + tg * 26) % max(1.0, w))
        dd.line([S(xx), S(y + 3), S(xx - h * 0.6), S(y + h - 3)],
                fill=mix(col, WHITE, 0.30) + (255,), width=max(1, int(S(4))))
    mask = Image.new("L", lay.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([S(x), S(y), S(x + fw), S(y + h)], radius=S(h / 2), fill=255)
    from PIL import ImageChops
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), mask))
    _put(img, lay, alpha)


def _ripple_on(img, cx, cy, r, col, alpha, tg, n=3, squash=1.0):
    """Ripple: cincin melebar berulang."""
    if alpha <= 0.01:
        return
    for k in range(n):
        ph = ((tg * 0.8 + k / float(n)) % 1.0)
        ring_on(img, cx, cy, r * (0.25 + 0.75 * ph), col, max(2, int(S(4))), alpha * (1 - ph), squash=squash)


def _swarm_on(img, cx, cy, t, col, alpha, n=10, sp=90.0, spread=1.0):
    """Swarm partikel keluar dari titik (kilat sensasi)."""
    if alpha <= 0.01:
        return
    for k in range(n):
        ph = ((t * 0.9 + k / float(n)) % 1.0)
        aa = k * 2.399963 + 0.6 * math.sin(t + k)
        rr = sp * ph * spread
        dot_on(img, cx + rr * math.cos(aa), cy + rr * 0.62 * math.sin(aa),
               1.2 + 3.6 * (1 - ph), mix(col, WHITE, 0.35), alpha * (1 - ph))


def _tile_rot(img, cx, cy, tw_, th_, drawfn, ang, alpha):
    """Ikon dari tile kecil yang bisa dirotasi (ko dalam drawfn: ruang tile)."""
    if alpha <= 0.01:
        return
    tile = Image.new("RGBA", (max(2, int(S(tw_))), max(2, int(S(th_)))), (0, 0, 0, 0))
    dd = ImageDraw.Draw(tile)
    drawfn(dd, tile.size)
    if ang:
        tile = tile.rotate(ang, resample=Image.BICUBIC, expand=True)
    pos = (int(S(cx) - tile.width / 2), int(S(cy) - tile.height / 2))
    if alpha < 0.995:
        a = tile.getchannel("A").point(lambda v: int(v * clamp(alpha)))
        img.paste(tile.convert("RGB"), pos, a)
    else:
        img.paste(tile, pos, tile)


def _mata31(dd, sz, col, blink=0.0, iris=True):
    """Gambar mata almond dalam tile (dipakai intro & rule)."""
    w, h = sz
    cxm, cym = w / 2, h / 2
    hw, hh = w * 0.40, h * 0.26
    dd.ellipse([cxm - hw, cym - hh, cxm + hw, cym + hh], fill=(246, 240, 226, 255),
               outline=col + (255,), width=max(2, int(w * 0.045)))
    if iris:
        rr = w * 0.13
        dd.ellipse([cxm - rr, cym - rr, cxm + rr, cym + rr], fill=col + (255,))
        rr2 = w * 0.06
        dd.ellipse([cxm - rr2, cym - rr2, cxm + rr2, cym + rr2], fill=(40, 34, 30, 255))
        rr3 = w * 0.03
        dd.ellipse([cxm - rr * 0.45 - rr3, cym - rr * 0.45 - rr3,
                    cxm - rr * 0.45 + rr3, cym - rr * 0.45 + rr3], fill=(255, 255, 255, 255))
    if blink > 0.02:
        lid = hh * 2 * clamp(blink)
        dd.rectangle([cxm - hw - 6, cym - hh - 6, cxm + hw + 6, cym - hh - 6 + lid],
                     fill=(246, 240, 226, 255))
        dd.line([cxm - hw, cym - hh, cxm + hw, cym - hh], fill=col + (255,),
                width=max(2, int(w * 0.045)))


def sc_intro_kedut(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: mata besar berkedip + otot kelopak berkedut (tik-tik)."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    q1 = seg(tl, 0.55, 1.0)
    if q1 > 0:
        _pop_pill(img, 540, 700 + dy, "BUKAN PERTANDA, INI OTOT", 26, mix(accent, INK, 0.10), q1 * al, q1)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    pang = mix(CREAM, mix(accent, INK, 0.30), 0.24)
    rrect_on(img, 104, 776 + dy, 976, 1596 + dy, 46, pang, q2 * al)
    rrect_on(img, 104, 1476 + dy, 976, 1596 + dy, 46, mix(pang, INK, 0.16), q2 * al)
    _dust(img, 134, 836 + dy, 946, 1432 + dy, 8, tg, q2 * al * 0.4, mix(pang, WHITE, 0.55))
    # mata besar berkedip
    ex, ey = 440, 1130 + dy
    blink = max(0.0, math.sin(tg * 2.6)) ** 8
    _tile_rot(img, ex, ey, 340, 190, lambda dd, sz: _mata31(dd, sz, mix(pang, INK, 0.35), blink), 0, q2 * al)
    # titik kedut di bawah mata: jitters saat beat + swarm + label TIK
    beat_f = (tg % 1.7) / 1.7
    beat = max(0.0, 1.0 - beat_f * 3.2)
    jx = 6 * espring(min(1.0, beat_f * 2.4)) * math.sin(tg * 46) * beat
    tx, ty = ex + 118, ey + 84 + dy
    line_on(img, (tx - 26 + jx, ty), (tx + 26 + jx, ty), mix(accent, INK, 0.10), 9, q2 * al * (0.5 + 0.5 * beat))
    if beat > 0.05:
        _swarm_on(img, tx + jx, ty, tg, mix(accent, WHITE, 0.30), q2 * al * beat, n=8, sp=54)
        _pop_txt(img, tx + 8, ty - 54, "TIK!", font(FB, 34), mix(WARN27, INK, 0.05),
                 q2 * al * beat, beat * 1.4)
    _ripple_on(img, ex, ey, 150, mix(pang, WHITE, 0.35), q2 * al * 0.35, tg, n=2, squash=0.62)
    _lbl(img, 440, 1345 + dy, "KELOPAK BERKEDUT SENDIRI", font(FS, 24), mix(pang, INK, 0.10), q2 * al)
    q4 = seg(tl, 2.6, 3.2)
    if q4 > 0:
        _pop_pill(img, 540, 1660 + dy, "KAU PASTI PERAH - INI SAINS", 24, mix(accent, INK, 0.10), q4 * al, q4)


def sc_ototkelopa(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 1: kedutan = serat otot menyusut sendiri (bukan pertanda)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    ex, ey = 360, 1120 + dy
    rrx, rry = 300, 150
    rrect_on(img, ex - rrx, ey - rry, ex + rrx, ey + rry, 40, mix(WHITE, accent, 0.14), q * al,
             outline=mix(accent, INK, 0.10), width=4)
    beat_f = (tg % 1.5) / 1.5
    beat = max(0.0, 1.0 - beat_f * 3.0)
    blink = max(0.0, math.sin(tg * 2.2)) ** 8
    squeeze = 1.0 - 0.10 * beat
    tile_w, tile_h = 380, 220
    def _draw_eye(dd, sz):
        _mata31(dd, sz, mix(accent, INK, 0.20), blink)
    tile = Image.new("RGBA", (int(S(tile_w)), int(S(tile_h))), (0, 0, 0, 0))
    _draw_eye(ImageDraw.Draw(tile), tile.size)
    tile = tile.resize((int(tile.width * squeeze), int(tile.height * (2.0 - squeeze))), Image.LANCZOS)
    pos = (int(S(ex) - tile.width / 2), int(S(ey) - tile.height / 2))
    a2 = tile.getchannel("A").point(lambda v: int(v * clamp(q * al)))
    img.paste(tile.convert("RGB"), pos, a2)
    for k in range(14):                        # serat otot di sekeliling mata menyala bergiliran
        aa = math.radians(200 + k * (140 / 13.0))
        lit = (int(tg * 4.5) % 14) == k
        r0, r1 = rrx - 26, rrx - 2
        c1 = (ex + r0 * math.cos(aa), ey + r1 * 1.18 * math.sin(aa))
        c2 = (ex + r1 * math.cos(aa), ey + r1 * 1.18 * math.sin(aa))
        line_on(img, c1, c2, mix(WARN27, WHITE, 0.30) if lit else mix(accent, INK, 0.14),
                8 if lit else 6, q * al)
    _lbl(img, ex, ey + rry + 40, "OTOT ORBICULARIS", font(FS, 26), mix(accent, INK, 0.04), q * al)
    _lbl(img, ex, ey + rry + 84, "MENYUSUT SENDIRI TANPA PERINTAH", font(FS, 23), MUTED, q * al)
    qa = esmooth(seg(tl, 0.3, 0.5))            # gelombang impuls hidup
    if qa > 0:
        wx0, wy0, w1 = 740, 940 + dy, 220
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        pts = []
        for j in range(44):
            xx = wx0 + j * (w1 / 43.0)
            ph = tg * 7.0 + j * 0.55
            spike = math.exp(-((j % 11) - 5) ** 2 / 3.0)
            yy = wy0 - spike * (52 + 30 * math.sin(tg * 9.0)) * (0.55 + 0.45 * math.sin(ph))
            pts.append((S(xx), S(yy)))
        dd.line(pts, fill=mix(accent, INK, 0.08) + (255,), width=max(2, int(S(5))))
        _put(img, lay, qa * al)
        line_on(img, (wx0 - 14, wy0 + 70), (wx0 + w1 + 14, wy0 + 70), mix(accent, INK, 0.16), 4, qa * al)
        _lbl(img, wx0 + w1 / 2, wy0 + 112, "IMPULS LISTRIK OTOT", font(FS, 25),
             mix(accent, INK, 0.05), qa * al)
    qb = esmooth(seg(tl, 0.5, 0.66))
    if qb > 0:
        for k in range(3):
            qk = seg(tl, 0.5 + k * 0.05, 0.62 + k * 0.05)
            _pop_pill(img, 855, (1250 + k * 96) + dy, ("CEPAT", "KECIL", "BERULANG")[k], 24,
                      mix(accent, INK, 0.08), qk * al, qk)
    qz = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "KEDUTAN = OTOT, BUKAN PERTANDA", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_pemicu_mata(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 2: empat pemicu dengan meter/jarum beranimasi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    col = mix(accent, INK, 0.12)
    cards = [(300, 1030, "KAFFEIN BERLEBIH", 0.82, "kopi"),
             (780, 1030, "KURANG TIDUR", 0.74, "bulan"),
             (300, 1430, "STRES", 0.70, "stres"),
             (780, 1430, "LAYAR TERLALU LAMA", 0.86, "layar")]
    for i, (cx, cy, txt, frac, ik) in enumerate(cards):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.10, 0.24 + i * 0.10))
        if qi <= 0.01:
            continue
        rrect_on(img, cx - 190, cy - 200, cx + 190, cy + 160, 34, mix(WHITE, accent, 0.14), qi * al,
                 outline=mix(accent, INK, 0.10), width=4)
        if ik == "kopi":
            _icon_kopi28(img, cx, cy - 118, 1.0, col, qi * al)
        elif ik == "bulan":
            _icon_moon29(img, cx, cy - 118, 1.1, col, qi * al)
        elif ik == "stres":
            _ripple_on(img, cx, cy - 118, 34, col, qi * al, tg, n=3)
            dot_on(img, cx, cy - 118, 9, col, qi * al)
        else:
            rrect_on(img, cx - 30, cy - 148, cx + 30, cy - 84, 10, mix(col, WHITE, 0.5), qi * al,
                     outline=col, width=3)
            line_on(img, (cx - 12, cy - 164 + 3 * math.sin(tg * 3)), (cx + 12, cy - 160), col, 4, qi * al)
        fq = qi * frac
        _meter_on(img, cx, cy + 62, 86, fq, mix(accent, INK, 0.06), qi * al)
        _pop_pill(img, cx, cy + 122, txt, 22, mix(accent, INK, 0.08), qi * al, qi * 1.3)
    qn = esmooth(_dw(tl, dur, 0.50, 0.62))
    if qn > 0:
        _pop_pill(img, 540, 1660 + dy, "MAKIN BANYAK PEMICU = MAKIN SERING KEDUTAN", 25,
                  mix(accent, INK, 0.10), qn * al, qn)
    qz = esmooth(_dw(tl, dur, 0.60, 0.72))
    if qz > 0:
        _shine_on(img, 110, 830 + dy, 970, 1590 + dy, seg(tl, 0.60, 0.78), qz * al)


def sc_impuls(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 3 (dari nol): impuls saraf -> otot; magnesium = rem alami."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    ax0, ax1, ay = 200, 700, 1050 + dy
    dot_on(img, ax0 - 40, ay, 26, mix(accent, INK, 0.10), q * al)   # badan saraf
    for k in range(3):
        aa = math.radians(120 + k * 60 + 10 * math.sin(tg * 2 + k))
        line_on(img, (ax0 - 40 + 20 * math.cos(aa), ay + 20 * math.sin(aa)),
                (ax0 - 40 + 52 * math.cos(aa), ay + 52 * math.sin(aa)), mix(accent, INK, 0.12), 6, q * al)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    pts = []
    for j in range(25):
        xx = ax0 + j * (ax1 - ax0) / 24.0
        yy = ay + 34 * math.sin(j * 0.9)
        pts.append((S(xx), S(yy)))
    dd.line(pts, fill=mix(accent, INK, 0.14) + (255,), width=max(2, int(S(9))))
    _put(img, lay, q * al)
    _lbl(img, (ax0 + ax1) / 2, ay + 96, "SARAF KE OTOT", font(FS, 23), MUTED, q * al)
    # gate magnesium di tengah jalur
    gx, gy = (ax0 + ax1) / 2, ay - 8 + dy
    qg = esmooth(_dw(tl, dur, 0.28, 0.44))
    if qg > 0:
        rrect_on(img, gx - 40, gy - 74, gx + 40, gy - 18, 12, mix(WHITE, accent, 0.35), qg * al,
                 outline=mix(accent, INK, 0.10), width=3)
        _lbl(img, gx, gy - 96, "MAGNESIUM = REM ALAMI", font(FS, 23), mix(accent, INK, 0.05), qg * al)
        for k in range(3):
            dot_on(img, gx - 18 + k * 18, gy - 46 + 3 * math.sin(tg * 3 + k), 8,
                   mix((108, 170, 90), WHITE, 0.3), qg * al)
    # impuls berjalan; saat lewat gerbang longgar -> swarm di otot
    mx, my = 840, ay + dy
    qm = esmooth(_dw(tl, dur, 0.16, 0.32))
    if qm > 0:
        rrect_on(img, mx - 40, my - 90, mx + 40, my + 90, 18, mix(WHITE, accent, 0.20), qm * al,
                 outline=mix(accent, INK, 0.10), width=4)
        for k in range(5):
            line_on(img, (mx - 30, my - 66 + k * 33), (mx + 30, my - 66 + k * 33),
                    mix(accent, INK, 0.12), 6, qm * al)
        _lbl(img, mx, my + 128, "OTOT", font(FS, 25), MUTED, qm * al)
        leak = (math.sin(tg * 0.9) > 0.45)
        for k in range(4):
            ph = ((tg * 0.8 + k / 4.0) % 1.0)
            j = ph * 24
            xx = ax0 + j * (ax1 - ax0) / 24.0
            yy = ay + 34 * math.sin(j * 0.9)
            if leak:
                yy += 8 * math.sin(tg * 12 + k)
            dot_on(img, xx, yy, 7, mix(WARN27, WHITE, 0.35) if leak else mix(accent, WHITE, 0.40), qm * al)
            if 0.45 < ph < 0.5:
                dot_on(img, xx - 10, yy, 4, mix(WARN27, WHITE, 0.2), qm * al * 0.6)
        if leak:
            _swarm_on(img, mx, my, tg, mix(WARN27, INK, 0.02), qm * al, n=12, sp=120)
            _lbl(img, mx, my - 130, "KEDUT!", font(FB, 34), mix(WARN27, INK, 0.05),
                 qm * al * (0.5 + 0.5 * math.sin(tg * 6)))
        else:
            _lbl(img, mx, my - 130, "TENANG", font(FS, 26), mix(accent, INK, 0.06), qm * al * 0.85)
    qz = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "LELAH + MINERAL BERKURANG = OTOT MUDAH TERPACU", font(FS, 26),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_mitos_kedut(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 4: mitos ramalan dibongkar (koin putar + coretan + shine)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    # kartu mitos kiri: koin ramalan berputar
    rrect_on(img, 120, 850 + dy, 500, 1430 + dy, 40, mix(WHITE, WARN27, 0.08), q * al,
             outline=mix(WARN27, INK, 0.12), width=4)
    ccx, ccy = 310, 1090 + dy
    ell(img, ccx - 86, ccy - 86, ccx + 86, ccy + 86, fill=mix(WHITE, WARN27, 0.25), alpha=q * al,
        outline=mix(WARN27, INK, 0.10), width=4)
    ang = tg * 260.0
    _tile_rot(img, ccx, ccy, 60, 60,
              lambda dd, sz: (dd.line([sz[0] * 0.2, sz[1] * 0.5, sz[0] * 0.8, sz[1] * 0.5],
                                      fill=mix(WARN27, INK, 0.20) + (255,), width=8),
                              dd.line([sz[0] * 0.5, sz[1] * 0.2, sz[0] * 0.5, sz[1] * 0.8],
                                      fill=mix(WARN27, INK, 0.20) + (255,), width=8)),
              ang, q * al)
    _ripple_on(img, ccx, ccy, 108, mix(WARN27, INK, 0.10), q * al * 0.5, tg, n=2)
    _lbl(img, ccx, 1268 + dy, "KANAN = REZEKI?", font(FS, 27), mix(WARN27, INK, 0.08), q * al)
    _lbl(img, ccx, 1316 + dy, "KIRI = SIAL?", font(FS, 27), mix(WARN27, INK, 0.08), q * al)
    qc = esmooth(_dw(tl, dur, 0.34, 0.5))
    if qc > 0:                                   # coretan besar
        line_on(img, (150, 1040 + dy), (470, 1200 + dy), WARN27, 12, qc * al)
        _pop_pill(img, 310, 1390 + dy, "TIDAK ADA RAMALANNYA", 24, mix(WARN27, INK, 0.10), qc * al, qc * 1.2)
    # kartu sains kanan
    qk = esmooth(_dw(tl, dur, 0.22, 0.4))
    rrect_on(img, 580, 850 + dy, 960, 1430 + dy, 40, mix(WHITE, accent, 0.14), qk * al,
             outline=mix(accent, INK, 0.10), width=4)
    _icon_check28(img, 770, 1030 + dy, 1.6, mix(accent, INK, 0.10), qk * al)
    _lbl(img, 770, 1210 + dy, "OTOT YANG CAPEK", font(FS, 27), mix(accent, INK, 0.05), qk * al)
    _lbl(img, 770, 1258 + dy, "MENYUSUT SENDIRI", font(FS, 27), mix(accent, INK, 0.05), qk * al)
    _pop_pill(img, 770, 1330 + dy, "SISI KANAN/KIRI = KEBETULAN POSISI", 21,
              mix(accent, INK, 0.08), esmooth(_dw(tl, dur, 0.44, 0.56)) * al,
              esmooth(_dw(tl, dur, 0.44, 0.56)))
    qz = esmooth(_dw(tl, dur, 0.52, 0.66))
    if qz > 0:
        _shine_on(img, 580, 850 + dy, 960, 1430 + dy, seg(tl, 0.52, 0.68), qz * al)
    qp = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qp > 0:
        _pill_c(img, 540, 1690 + dy, "KEDUTAN TIDAK MERAMALKAN APA PUN", font(FS, 28),
                mix(accent, INK, 0.10), qp * al, dot=True)


def sc_atasi_kedut(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 5: tiga langkah atasi dengan pil pop berurutan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    col = mix(accent, INK, 0.12)
    steps = [(240, "KOMPRES HANGAT", "kompres"), (540, "TIDUR CUKUP", "tidur"),
             (840, "KURANGI KAFFEIN", "kopi")]
    for i, (cx, txt, ik) in enumerate(steps):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.13, 0.26 + i * 0.13))
        if qi <= 0.01:
            continue
        yo = 7 * math.sin(tg * 1.4 + i * 1.7)
        rrect_on(img, cx - 130, 930 + yo, cx + 130, 1240 + yo, 36, mix(WHITE, accent, 0.14), qi * al,
                 outline=mix(accent, INK, 0.10), width=4)
        _pop_pill(img, cx, 860 + dy, "0" + str(i + 1), 30, mix(accent, INK, 0.10), qi * al, qi * 1.2)
        if ik == "kompres":
            rrect_on(img, cx - 56, 1060 + yo, cx + 56, 1130 + yo, 20, mix(col, WHITE, 0.45), qi * al,
                     outline=col, width=3)
            for k in range(3):
                ph = ((tg * 0.7 + k / 3.0) % 1.0)
                lay = _layer(img)
                dd = ImageDraw.Draw(lay)
                xx = cx - 30 + k * 30
                pts = [(S(xx + 6 * math.sin(ph * 8 + k)), S(1040 + yo - ph * 60 + j * 8)) for j in range(5)]
                dd.line(pts, fill=mix(col, WHITE, 0.35) + (255,), width=max(1, int(S(4))))
                _put(img, lay, qi * al * (1 - ph) * 0.9)
        elif ik == "tidur":
            _icon_moon29(img, cx, 1090 + yo, 1.3, col, qi * al)
            for k, zx in enumerate(("z", "z", "Z")):
                ph = ((tg * 0.5 + k * 0.33) % 1.0)
                paste_c(img, cx + 44 + ph * 26, 1040 + yo - ph * 70, zx, font(FB, 22 + k * 8),
                        mix(col, WHITE, 0.30), qi * al * (1 - ph))
        else:
            _icon_kopi28(img, cx - 26, 1080 + yo, 1.1, col, qi * al)
            _bar_on(img, cx + 24, 1050 + yo, 90, 20, 0.8 - 0.62 * (0.5 + 0.5 * math.sin(tg * 1.1)),
                    WARN27, qi * al, tg)
        _pill_c(img, cx, 1320 + dy, txt, font(FS, 24), mix(accent, INK, 0.08), qi * al)
        if i < 2:
            qa = esmooth(_dw(tl, dur, 0.24 + i * 0.13, 0.36 + i * 0.13))
            _arrow_on(img, (cx + 150, 1085 + dy), (steps[i + 1][0] - 150, 1085 + dy),
                      mix(accent, WHITE, 0.22), 5, qa * al)
    qz = esmooth(_dw(tl, dur, 0.60, 0.76))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "KEDUTAN BIASANYA PERGI DALAM HITUNGAN HARI", font(FS, 26),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_rule2020(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 6: aturan 20-20-20 dengan ring timer + angka count-up."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    ccx, ccy = 540, 1060 + dy
    prog = (tg * 0.11) % 1.0
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    bb = [S(ccx - 190), S(ccy - 190), S(ccx + 190), S(ccy + 190)]
    dd.arc(bb, -90, 270, fill=mix(accent, CREAM, 0.55) + (255,), width=max(3, int(S(20))))
    dd.arc(bb, -90, -90 + 360 * prog, fill=accent + (255,), width=max(3, int(S(20))))
    ah = math.radians(-90 + 360 * prog)
    dd.ellipse([S(ccx + 190 * math.cos(ah) - 12), S(ccy + 190 * math.sin(ah) - 12),
                S(ccx + 190 * math.cos(ah) + 12), S(ccy + 190 * math.sin(ah) + 12)],
               fill=mix(accent, WHITE, 0.45) + (255,))
    _put(img, lay, q * al)
    blink = max(0.0, math.sin(tg * 2.4)) ** 8
    _tile_rot(img, ccx, ccy, 220, 130, lambda dd, sz: _mata31(dd, sz, mix(accent, INK, 0.16), blink),
              0, q * al)
    cards20 = [(20, "TIAP 20 MENIT"), (20, "LIHAT 20 DETIK"), (6, "SEJAUH 6 METER")]
    for i, (tgt, txt) in enumerate(cards20):
        qi = esmooth(_dw(tl, dur, 0.14 + i * 0.12, 0.32 + i * 0.12))
        if qi <= 0.01:
            continue
        aa = math.radians(-90 + i * 120 + 30)
        px, py = ccx + 330 * math.cos(aa), ccy + 240 * math.sin(aa) + dy
        rrect_on(img, px - 140, py - 74, px + 140, py + 74, 30, mix(WHITE, accent, 0.16), qi * al,
                 outline=mix(accent, INK, 0.10), width=4)
        val = int(round(tgt * eo(seg(tl, 0.14 + i * 0.12, 0.5 + i * 0.12))))
        paste_c(img, px, py - 24, str(val), font(FB, 52), mix(accent, INK, 0.04), qi * al)
        _pop_pill(img, px, py + 30, txt, 20, mix(accent, INK, 0.08), qi * al, qi * 1.3)
    qn = esmooth(_dw(tl, dur, 0.52, 0.66))
    if qn > 0:                                   # magnesium: pisang, kacang, sayur hijau
        _pop_pill(img, 540, 1450 + dy, "TAMBAH MAGNESIUM: PISANG - KACANG - SAYUR HIJAU", 23,
                  mix(accent, INK, 0.10), qn * al, qn)
        for k, fxc in enumerate(("pisang", "kacang", "sayur")):
            xx = 330 + k * 210
            yo = 6 * math.sin(tg * 1.5 + k * 1.5)
            if fxc == "pisang":
                poly_on(img, [(xx - 44, 1508 + yo), (xx + 30, 1530 + yo), (xx + 44, 1552 + yo),
                              (xx + 8, 1544 + yo), (xx - 40, 1524 + yo)],
                        (240, 200, 90), qn * al, outline=mix((240, 200, 90), INK, 0.25), width=3)
            elif fxc == "kacang":
                for j in range(3):
                    ell(img, xx - 30 + j * 24, 1518 + yo + (j % 2) * 12, xx - 6 + j * 24,
                        1544 + yo + (j % 2) * 12, fill=(196, 150, 96), alpha=qn * al,
                        outline=mix((196, 150, 96), INK, 0.25), width=3)
            else:
                poly_on(img, [(xx, 1500 + yo), (xx + 34, 1526 + yo), (xx + 6, 1556 + yo),
                              (xx - 28, 1530 + yo)],
                        (96, 160, 90), qn * al, outline=mix((96, 160, 90), INK, 0.25), width=3)
    qz = esmooth(_dw(tl, dur, 0.64, 0.78))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "MATA REHAT = OTOT KELPAK REHAT", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_waspada_mata(img, d, sc, tl, dur, tg, accent, al, dy):
    """Adegan 7: tanda perlu ke dokter - checklist centang tergambar."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    signs = ["KEDUTAN BERHARI-HARI TIDAK PERGI", "BERAT SAMPAI MENUTUP MATA",
             "MENYEBAR KE SISI WAJAH"]
    for i, txt in enumerate(signs):
        qi = esmooth(_dw(tl, dur, 0.05 + i * 0.10, 0.20 + i * 0.10))
        if qi <= 0.01:
            continue
        yy = 880 + i * 128 + dy
        rrect_on(img, 150, yy - 44, 930, yy + 44, 30, mix(WHITE, WARN27, 0.08), qi * al,
                 outline=mix(WARN27, INK, 0.12), width=3)
        ck = esmooth(_dw(tl, dur, 0.12 + i * 0.10, 0.24 + i * 0.10))
        if ck > 0:
            ex0, ey0 = 200, yy
            p1 = (ex0, ey0 + 2)
            p2 = (ex0 + 22, ey0 + 22)
            p3 = (ex0 + 58, ey0 - 22)
            if ck < 0.5:
                q1 = ck / 0.5
                line_on(img, p1, (p1[0] + (p2[0] - p1[0]) * q1, p1[1] + (p2[1] - p1[1]) * q1),
                        mix(WARN27, INK, 0.05), 8, qi * al)
            else:
                line_on(img, p1, p2, mix(WARN27, INK, 0.05), 8, qi * al)
                q2 = (ck - 0.5) / 0.5
                line_on(img, p2, (p2[0] + (p3[0] - p2[0]) * q2, p2[1] + (p3[1] - p2[1]) * q2),
                        mix(WARN27, INK, 0.05), 8, qi * al)
        _pill_c(img, 590, yy, txt, font(FS, 25), mix(WARN27, INK, 0.10), qi * al)
    qa = esmooth(_dw(tl, dur, 0.40, 0.52))
    if qa > 0:
        _arrow_on(img, (540, 1300 + dy), (540, 1368 + dy), mix(accent, INK, 0.12), 6, qa * al)
    qb = esmooth(_dw(tl, dur, 0.50, 0.64))
    if qb > 0:
        pulse = 0.5 + 0.5 * math.sin(tg * 3.0)
        _icon_steto28(img, 300, 1462 + dy, 1.6, mix(accent, INK, 0.12), qb * al, tg)
        ring_on(img, 348, 1513 + dy, 26 + 8 * pulse, mix(accent, WHITE, 0.55), 4, qb * al * 0.8)
        _lbl(img, 650, 1436 + dy, "PERIKSA KE DOKTER", font(FS, 31), mix(accent, INK, 0.03), qb * al)
        _lbl(img, 650, 1494 + dy, "BISA BLEFAROSPASME / SPASME FASIAL", font(FS, 24), MUTED, qb * al)
    qz = esmooth(_dw(tl, dur, 0.68, 0.82))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "JARANG - TAPI PENTING DIKENALI", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


VISUALS.update({
    "intro_kedut": sc_intro_kedut,
    "ototkelopa": sc_ototkelopa,
    "pemicu_mata": sc_pemicu_mata,
    "impuls": sc_impuls,
    "mitos_kedut": sc_mitos_kedut,
    "atasi_kedut": sc_atasi_kedut,
    "rule2020": sc_rule2020,
    "waspada_mata": sc_waspada_mata,
})


def _selftest31():
    """Uji cepat adegan Ep31 sebelum dipakai render."""
    names = ["intro_kedut", "ototkelopa", "pemicu_mata", "impuls", "mitos_kedut",
             "atasi_kedut", "rule2020", "waspada_mata"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "MATA KEDUTAN?"], "accent": "#2E6E8C"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep31: 8 adegan OK")


# ====================================================================
# MESIN v5 - PAKET PENJELAS (21 Sep): elemen generik lintas-topik agar
# penonton bisa MEMBAYANGKAN proses: ikon organ/objek, kaca pembesar,
# anotasi menunjuk, alur proses, perbandingan, sorotan, garis waktu.
# WAJIB dipakai di episode baru (selain elemen v4).
# ====================================================================


def _ico5(img, nama, cx, cy, r, col, alpha, tg=0.0, pulse=0.0):
    """Ikon vektor generik v5. nama: heart brain lung stomach tooth eye
    bone germ clock thermo flame snow drop bolt moon shield.
    pulse: 0..1 -> ikon membesar sedikit (denyut)."""
    if alpha <= 0.01 or nama not in _ICO5:
        return
    rr = r * (1.0 + 0.07 * pulse)
    _ICO5[nama](img, cx, cy, rr, col, alpha, tg)


def _i5_heart(img, cx, cy, r, col, alpha, tg):
    beat = 1.0 + 0.06 * math.sin(tg * 5.2)
    r2 = r * beat
    ell(img, cx - 0.52 * r2, cy - 0.55 * r2, cx + 0.06 * r2, cy + 0.02 * r2, fill=col, alpha=alpha)
    ell(img, cx - 0.06 * r2, cy - 0.55 * r2, cx + 0.52 * r2, cy + 0.02 * r2, fill=col, alpha=alpha)
    poly_on(img, [(cx - 0.55 * r2, cy - 0.22 * r2), (cx, cy + 0.62 * r2), (cx + 0.55 * r2, cy - 0.22 * r2)],
            col, alpha)
    ell(img, cx - 0.30 * r2, cy - 0.36 * r2, cx - 0.10 * r2, cy - 0.16 * r2, fill=mix(col, WHITE, 0.55), alpha=alpha)


def _i5_brain(img, cx, cy, r, col, alpha, tg):
    ell(img, cx - 0.62 * r, cy - 0.52 * r, cx + 0.62 * r, cy + 0.45 * r, fill=mix(col, WHITE, 0.30), alpha=alpha,
        outline=col, width=4)
    for k, dx in enumerate((-0.30, 0.10)):
        yy = cy - 0.28 * r
        for j in range(3):
            x0 = cx + dx * r + (j % 2) * 0.16 * r
            _wavy(img, x0, yy, yy + 0.34 * r, 0.05 * r, col, 3, alpha, fase=tg * 0.8 + j + k, n=2)
            yy += 0.30 * r
    line_on(img, (cx, cy + 0.45 * r), (cx, cy + 0.72 * r), col, 5, alpha)


def _i5_lung(img, cx, cy, r, col, alpha, tg):
    line_on(img, (cx, cy - 0.55 * r), (cx, cy - 0.10 * r), col, 6, alpha)
    line_on(img, (cx - 0.18 * r, cy - 0.22 * r), (cx - 0.34 * r, cy - 0.10 * r), col, 5, alpha)
    line_on(img, (cx + 0.18 * r, cy - 0.22 * r), (cx + 0.34 * r, cy - 0.10 * r), col, 5, alpha)
    sw = 0.03 * r * math.sin(tg * 3.4)
    ell(img, cx - 0.62 * r + sw, cy - 0.10 * r, cx - 0.10 * r + sw, cy + 0.60 * r, fill=mix(col, WHITE, 0.45),
        alpha=alpha, outline=col, width=3)
    ell(img, cx + 0.10 * r - sw, cy - 0.10 * r, cx + 0.62 * r - sw, cy + 0.60 * r, fill=mix(col, WHITE, 0.45),
        alpha=alpha, outline=col, width=3)


def _i5_stomach(img, cx, cy, r, col, alpha, tg):
    ell(img, cx - 0.45 * r, cy - 0.30 * r, cx + 0.55 * r, cy + 0.62 * r, fill=mix(col, WHITE, 0.45), alpha=alpha,
        outline=col, width=4)
    line_on(img, (cx - 0.12 * r, cy - 0.62 * r), (cx - 0.05 * r, cy - 0.30 * r), col, 6, alpha)
    line_on(img, (cx + 0.40 * r, cy + 0.28 * r), (cx + 0.62 * r, cy + 0.05 * r), col, 6, alpha)
    for k in range(3):
        ph = (tg * 0.9 + k / 3.0) % 1.0
        dot_on(img, cx - 0.05 * r + 0.40 * r * ph, cy + 0.12 * r + 0.08 * r * math.sin(ph * 6.3),
               0.06 * r, col, alpha * (1.0 - ph) * 0.9)


def _i5_tooth(img, cx, cy, r, col, alpha, tg):
    poly_on(img, [(cx - 0.55 * r, cy - 0.50 * r), (cx + 0.55 * r, cy - 0.50 * r),
                  (cx + 0.50 * r, cy + 0.10 * r), (cx + 0.28 * r, cy + 0.58 * r),
                  (cx + 0.10 * r, cy + 0.10 * r), (cx - 0.10 * r, cy + 0.58 * r),
                  (cx - 0.28 * r, cy + 0.10 * r)],
            mix(col, WHITE, 0.62), alpha, outline=col, width=4)
    ell(img, cx - 0.22 * r, cy - 0.32 * r, cx - 0.02 * r, cy - 0.12 * r, fill=mix(col, WHITE, 0.80), alpha=alpha)


def _i5_eye(img, cx, cy, r, col, alpha, tg):
    line_on(img, (cx - 0.70 * r, cy), (cx - 0.30 * r, cy - 0.34 * r), col, 5, alpha)
    line_on(img, (cx - 0.30 * r, cy - 0.34 * r), (cx + 0.30 * r, cy - 0.34 * r), col, 5, alpha)
    line_on(img, (cx + 0.30 * r, cy - 0.34 * r), (cx + 0.70 * r, cy), col, 5, alpha)
    line_on(img, (cx - 0.70 * r, cy), (cx - 0.30 * r, cy + 0.34 * r), col, 5, alpha)
    line_on(img, (cx - 0.30 * r, cy + 0.34 * r), (cx + 0.30 * r, cy + 0.34 * r), col, 5, alpha)
    line_on(img, (cx + 0.30 * r, cy + 0.34 * r), (cx + 0.70 * r, cy), col, 5, alpha)
    ir = 0.26 * r * (1.0 + 0.05 * math.sin(tg * 2.1))
    ell(img, cx - ir, cy - ir, cx + ir, cy + ir, fill=col, alpha=alpha)
    dot_on(img, cx, cy, 0.10 * r, INK, alpha)


def _i5_bone(img, cx, cy, r, col, alpha, tg):
    ang = math.radians(-32)
    ca, sa = math.cos(ang), math.sin(ang)
    line_on(img, (cx - 0.42 * r * ca, cy + 0.42 * r * sa), (cx + 0.42 * r * ca, cy - 0.42 * r * sa), col, 10, alpha)
    for sx in (-1, 1):
        bx, by = cx + sx * 0.42 * r * ca, cy - sx * 0.42 * r * sa
        for dxy in ((-0.14, -0.14), (0.14, 0.14), (-0.14, 0.14), (0.14, -0.14)):
            ell(img, bx + dxy[0] * r - 0.14 * r, by + dxy[1] * r - 0.14 * r,
                bx + dxy[0] * r + 0.14 * r, by + dxy[1] * r + 0.14 * r, fill=mix(col, WHITE, 0.45),
                alpha=alpha, outline=col, width=3)


def _i5_germ(img, cx, cy, r, col, alpha, tg):
    rot = tg * 0.6
    for k in range(7):
        aa = rot + k * 2.399963
        x1 = cx + 0.52 * r * math.cos(aa)
        y1 = cy + 0.52 * r * math.sin(aa)
        x2 = cx + 0.80 * r * math.cos(aa)
        y2 = cy + 0.80 * r * math.sin(aa)
        line_on(img, (x1, y1), (x2, y2), col, 4, alpha)
        dot_on(img, x2, y2, 0.07 * r, col, alpha)
    ell(img, cx - 0.52 * r, cy - 0.52 * r, cx + 0.52 * r, cy + 0.52 * r, fill=mix(col, WHITE, 0.40), alpha=alpha,
        outline=col, width=4)
    for k in range(3):
        dot_on(img, cx + (k - 1) * 0.20 * r, cy + 0.05 * r * math.sin(tg * 2.0 + k), 0.08 * r, col, alpha * 0.9)


def _i5_clock(img, cx, cy, r, col, alpha, tg):
    ell(img, cx - 0.62 * r, cy - 0.62 * r, cx + 0.62 * r, cy + 0.62 * r, fill=WHITE, alpha=alpha, outline=col,
        width=5)
    aa = -1.2 + 1.1 * math.sin(tg * 0.9)
    line_on(img, (cx, cy), (cx + 0.42 * r * math.cos(aa), cy + 0.42 * r * math.sin(aa)), col, 5, alpha)
    bb = 2.1 + 0.8 * math.sin(tg * 0.35)
    line_on(img, (cx, cy), (cx + 0.58 * r * math.cos(bb), cy + 0.58 * r * math.sin(bb)), mix(col, INK, 0.25), 4,
            alpha)
    dot_on(img, cx, cy, 0.08 * r, col, alpha)


def _i5_thermo(img, cx, cy, r, col, alpha, tg):
    line_on(img, (cx, cy - 0.62 * r), (cx, cy + 0.30 * r), mix(col, WHITE, 0.30), 12, alpha)
    lvl = 0.55 + 0.25 * math.sin(tg * 1.4)
    ly = cy + 0.42 * r - (0.72 * r) * lvl
    line_on(img, (cx, cy + 0.30 * r), (cx, ly), col, 6, alpha)
    ell(img, cx - 0.26 * r, cy + 0.28 * r, cx + 0.26 * r, cy + 0.72 * r, fill=col, alpha=alpha)
    for k in range(4):
        yy = cy - 0.45 * r + k * 0.24 * r
        line_on(img, (cx + 0.16 * r, yy), (cx + 0.38 * r, yy), mix(col, INK, 0.25), 3, alpha)


def _i5_flame(img, cx, cy, r, col, alpha, tg):
    wob = 0.05 * r * math.sin(tg * 6.0)
    poly_on(img, [(cx, cy - 0.75 * r + wob), (cx + 0.42 * r, cy + 0.10 * r),
                  (cx + 0.24 * r, cy + 0.55 * r), (cx - 0.24 * r, cy + 0.55 * r),
                  (cx - 0.42 * r, cy + 0.10 * r)], mix(col, (255, 170, 60), 0.55), alpha)
    poly_on(img, [(cx, cy - 0.30 * r), (cx + 0.18 * r, cy + 0.16 * r),
                  (cx - 0.18 * r, cy + 0.16 * r)], mix(col, WHITE, 0.72), alpha)


def _i5_snow(img, cx, cy, r, col, alpha, tg):
    rot = tg * 0.35
    for k in range(6):
        aa = rot + k * math.pi / 3.0
        x2 = cx + 0.72 * r * math.cos(aa)
        y2 = cy + 0.72 * r * math.sin(aa)
        line_on(img, (cx, cy), (x2, y2), col, 4, alpha)
        for tt2 in (0.55, 0.80):
            bx, by = cx + tt2 * 0.72 * r * math.cos(aa), cy + tt2 * 0.72 * r * math.sin(aa)
            for sgn in (-1, 1):
                aa2 = aa + sgn * 0.6
                line_on(img, (bx, by), (bx + 0.16 * r * math.cos(aa2), by + 0.16 * r * math.sin(aa2)), col, 3,
                        alpha)


def _i5_drop(img, cx, cy, r, col, alpha, tg):
    poly_on(img, [(cx, cy - 0.72 * r), (cx + 0.42 * r, cy + 0.12 * r),
                  (cx + 0.20 * r, cy + 0.58 * r), (cx - 0.20 * r, cy + 0.58 * r),
                  (cx - 0.42 * r, cy + 0.12 * r)], mix(col, WHITE, 0.30), alpha, outline=col, width=3)
    ell(img, cx - 0.18 * r, cy + 0.02 * r, cx - 0.02 * r, cy + 0.28 * r, fill=mix(col, WHITE, 0.70), alpha=alpha)


def _i5_bolt(img, cx, cy, r, col, alpha, tg):
    flick = alpha * (0.80 + 0.20 * math.sin(tg * 7.3))
    poly_on(img, [(cx + 0.16 * r, cy - 0.72 * r), (cx - 0.40 * r, cy + 0.10 * r),
                  (cx - 0.04 * r, cy + 0.10 * r), (cx - 0.16 * r, cy + 0.72 * r),
                  (cx + 0.40 * r, cy - 0.06 * r), (cx + 0.02 * r, cy - 0.06 * r)],
            mix(col, (255, 210, 80), 0.50), flick, outline=col, width=3)


def _i5_moon(img, cx, cy, r, col, alpha, tg):
    ell(img, cx - 0.55 * r, cy - 0.55 * r, cx + 0.55 * r, cy + 0.55 * r, fill=mix(col, WHITE, 0.55), alpha=alpha)
    ell(img, cx - 0.05 * r, cy - 0.72 * r, cx + 0.85 * r, cy + 0.18 * r, fill=mix(CREAM, WHITE, 0.55), alpha=alpha)


def _i5_shield(img, cx, cy, r, col, alpha, tg):
    poly_on(img, [(cx, cy - 0.70 * r), (cx + 0.55 * r, cy - 0.45 * r),
                  (cx + 0.50 * r, cy + 0.20 * r), (cx, cy + 0.72 * r),
                  (cx - 0.50 * r, cy + 0.20 * r), (cx - 0.55 * r, cy - 0.45 * r)],
            mix(col, WHITE, 0.42), alpha, outline=col, width=4)
    ck = clamp((tg % 2.4) / 1.0)
    p1 = (cx - 0.24 * r, cy)
    p2 = (cx - 0.05 * r, cy + 0.24 * r)
    p3 = (cx + 0.30 * r, cy - 0.24 * r)
    if ck < 0.5:
        q1 = ck / 0.5
        line_on(img, p1, (p1[0] + (p2[0] - p1[0]) * q1, p1[1] + (p2[1] - p1[1]) * q1), col, 7, alpha)
    else:
        line_on(img, p1, p2, col, 7, alpha)
        q2 = (ck - 0.5) / 0.5
        line_on(img, p2, (p2[0] + (p3[0] - p2[0]) * q2, p2[1] + (p2[1] - p2[1]) * q2 + (p3[1] - p2[1]) * q2),
                col, 7, alpha)


_ICO5 = {
    "heart": _i5_heart, "brain": _i5_brain, "lung": _i5_lung, "stomach": _i5_stomach,
    "tooth": _i5_tooth, "eye": _i5_eye, "bone": _i5_bone, "germ": _i5_germ,
    "clock": _i5_clock, "thermo": _i5_thermo, "flame": _i5_flame, "snow": _i5_snow,
    "drop": _i5_drop, "bolt": _i5_bolt, "moon": _i5_moon, "shield": _i5_shield,
}


def _loupe_on(img, mx, my, tx, ty, rr, alpha, tt, zoom=2.2):
    """Kaca pembesar: perbesar area (mx,my) dari frame saat ini, tampilkan
    di (tx,ty) dalam lingkaran + gagang. Pop-in via tt (0..1).
    Hanya lensa yang ditempel - frame lain tidak tersentuh."""
    if alpha <= 0.01 or tt <= 0:
        return
    W2, H2 = img.size
    R = int(S(rr))
    cw, ch = int(S(rr * 1.5)), int(S(rr * 1.5 * 0.78))
    cx0 = int(clamp(S(mx) - cw / 2, 0, W2 - cw))
    cy0 = int(clamp(S(my) - ch / 2, 0, H2 - ch))
    crop = img.crop((cx0, cy0, cx0 + cw, cy0 + ch))
    sc = (0.55 + 0.45 * eob(min(1.0, tt), 1.7)) * zoom
    big = crop.resize((max(2, int(cw * sc)), max(2, int(ch * sc))), Image.LANCZOS)
    lens = Image.new("RGB", (2 * R, 2 * R), CREAM)
    lens.paste(big, ((2 * R - big.width) // 2, (2 * R - big.height) // 2))
    mask = Image.new("L", (2 * R, 2 * R), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 2 * R - 1, 2 * R - 1], fill=255)
    if alpha < 0.995:
        mask = mask.point(lambda v: int(v * clamp(alpha)))
    img.paste(lens, (int(S(tx)) - R, int(S(ty)) - R), mask)
    ring_on(img, S(tx), S(ty), R, mix(BLUE, INK, 0.10), max(3, int(S(9))), alpha)
    ring_on(img, S(tx), S(ty), R * 1.10, mix(WHITE, CREAM, 0.30), max(2, int(S(4))), alpha * 0.9)
    hx = S(tx) + R * 0.72
    hy = S(ty) + R * 0.72
    line_on(img, (hx, hy), (hx + R * 0.52, hy + R * 0.52), mix(BLUE, INK, 0.10), 14, alpha)
    ring_on(img, hx + R * 0.60, hy + R * 0.60, S(12), mix(BLUE, INK, 0.10), 6, alpha)


def _callout_on(img, px, py, tx, ty, text, alpha, tt, fsz=25, col=None):
    """Anotasi menunjuk: titik di target + garis penunjuk + pil label."""
    if alpha <= 0.01 or tt <= 0:
        return
    col = col or mix(BLUE, INK, 0.05)
    q = esmooth(min(1.0, tt))
    dot_on(img, px, py, 8, col, alpha * q)
    ring_on(img, px, py, 8 + 10 * (1.0 - q) + 4 * math.sin(tt * 6.0), col, 3, alpha * q)
    ex = px + (tx - px) * 0.62
    ey = py + (ty - py) * 0.62
    line_on(img, (px, py), (ex, ey), col, 4, alpha * q)
    _pop_pill(img, tx, ty, text, fsz, mix(col, WHITE, 0.88), alpha * esmooth(clamp((tt - 0.30) / 0.70)),
              clamp((tt - 0.30) / 0.70) * 1.4, fg=mix(col, INK, 0.30))


def _flow_on(img, y, steps, alpha, tg, t0=0.2, dt=0.9, col=None, fsz=22):
    """Alur proses: chip ikon + label muncul berurutan, panah antar chip
    menyala progresif (cerita sebab-akibat kiri ke kanan).
    steps: [(nama_ikon, "LABEL"), ...] maks 4."""
    if alpha <= 0.01 or not steps:
        return
    col = col or DATA
    n = len(steps)
    gap = 250
    x0 = 540 - gap * (n - 1) / 2.0
    for i, (ic, lab) in enumerate(steps):
        tsi = t0 + i * dt
        qi = esmooth(seg(tg, tsi, tsi + 0.45))
        if qi <= 0:
            continue
        cxi = x0 + i * gap
        ring_on(img, cxi, y - 4, 62 + 4 * math.sin(tg * 2.2 + i), mix(col, CREAM, 0.35), 5, alpha * qi)
        _ico5(img, ic, cxi, y - 4, 40, col, alpha * qi, tg)
        _pop_pill(img, cxi, y + 86, lab, fsz, mix(col, WHITE, 0.90), alpha * qi,
                  clamp((tg - tsi - 0.15) / 0.45) * 1.5, fg=mix(col, INK, 0.30))
        if i < n - 1:
            qa = esmooth(seg(tg, tsi + 0.40, tsi + 0.85))
            if qa > 0:
                ax0, ax1 = cxi + 74, cxi + gap - 74
                dash = [ax0 + (ax1 - ax0) * qa, y - 4]
                _arrow_on(img, (ax0, y - 4), (dash[0], dash[1]), mix(col, INK, 0.12), 6, alpha * qa)
                px2 = ax0 + ((tg * 130.0) % max(1.0, ax1 - ax0))
                if px2 < ax1:
                    dot_on(img, px2, y - 4, 5, mix(col, WHITE, 0.40), alpha * qa)


def _versus_on(img, cy, kiri, kanan, alpha, tg, t0=0.3, col=None):
    """Perbandingan dua sisi: panel ikon + label kiri/kanan + lencana VS.
    kiri/kanan: (nama_ikon, "LABEL", warna)."""
    if alpha <= 0.01:
        return
    qk = esmooth(seg(tg, t0, t0 + 0.45))
    qn = esmooth(seg(tg, t0 + 0.25, t0 + 0.70))
    for side, item, q in ((-1, kiri, qk), (1, kanan, qn)):
        if q <= 0:
            continue
        ic, lab, c2 = item
        cx = 540 + side * 262
        w_, h_ = 440, 470
        panel(img, cx - w_ / 2, cy - h_ / 2, cx + w_ / 2, cy + h_ / 2, alpha * q, radius=44,
              fill=mix(WHITE, c2, 0.06))
        _ico5(img, ic, cx, cy - 60, 96, c2, alpha * q, tg)
        _pop_pill(img, cx, cy + 150, lab, 24, mix(c2, WHITE, 0.88), alpha * esmooth(seg(tg, t0 + 0.45, t0 + 0.85)),
                  clamp((tg - t0 - 0.45) / 0.5) * 1.5, fg=mix(c2, INK, 0.30))
    qv = esmooth(seg(tg, t0 + 0.55, t0 + 0.95))
    if qv > 0:
        sc_q = 0.55 + 0.45 * eob(min(1.0, (tg - t0 - 0.55) / 0.45), 1.8)
        _pop_pill(img, 540, cy, "VS", 40, col or INK, alpha * qv, (tg - t0 - 0.55) * 2.0,
                  fg=WHITE)


def _spotlight_on(img, cx, cy, rr, alpha, tt, dim=0.40):
    """Sorotan: gelapkan seluruh frame KECUALI lingkaran fokus + ring."""
    if alpha <= 0.01 or dim <= 0.01:
        return
    lay = Image.new("RGBA", img.size, INK + (255,))
    mask = Image.new("L", img.size, 255)
    md = ImageDraw.Draw(mask)
    md.ellipse([S(cx - rr), S(cy - rr), S(cx + rr), S(cy + rr)], fill=0)
    a = mask.point(lambda v: int(dim * 255 * v / 255.0))
    if alpha < 0.995:
        a = a.point(lambda v: int(v * clamp(alpha)))
    img.paste(lay, (0, 0), a)
    ring_on(img, cx, cy, rr * (0.92 + 0.05 * math.sin(tt * 3.0)), mix(WHITE, CREAM, 0.25), 6, alpha)
    ring_on(img, cx, cy, rr * 1.06, mix(WHITE, CREAM, 0.10), 3, alpha * 0.8)


def _fan_on(img, cx, cy, ang, alpha, tg, n=5, span=64.0, ln=120.0, col=None, width=7):
    """Kipas panah arah: menunjukkan gerak/penyebaran ke suatu arah."""
    if alpha <= 0.01:
        return
    col = col or mix(DATA, INK, 0.10)
    for k in range(n):
        fr = k / float(n - 1) if n > 1 else 0.5
        aa = math.radians(ang - span / 2 + span * fr)
        ph = (tg * 1.1 + fr * 0.35) % 1.0
        L = ln * (0.55 + 0.45 * ph)
        x2 = cx + L * math.cos(aa)
        y2 = cy + L * math.sin(aa)
        line_on(img, (cx + 0.30 * L * math.cos(aa), cy + 0.30 * L * math.sin(aa)), (x2, y2), col, width,
                alpha * (0.30 + 0.70 * (1 - ph)))
        poly_on(img, [(x2 - 16 * math.cos(aa) + 9 * math.sin(aa), y2 - 16 * math.sin(aa) - 9 * math.cos(aa)),
                      (x2 - 16 * math.cos(aa) - 9 * math.sin(aa), y2 - 16 * math.sin(aa) + 9 * math.cos(aa)),
                      (x2 + 10 * math.cos(aa), y2 + 10 * math.sin(aa))], col, alpha * (1.0 - ph * 0.6))


def _timeline_on(img, x0, x1, y, marks, alpha, tg, t0=0.3, dt=0.5, col=None, fsz=22):
    """Garis waktu: garis terisi progresif + titik/label muncul berurutan."""
    if alpha <= 0.01 or not marks:
        return
    col = col or DATA
    base = mix(col, CREAM, 0.55)
    line_on(img, (x0, y), (x1, y), base, 8, alpha)
    fill = esmooth(seg(tg, t0, t0 + dt * (len(marks) - 1) + 0.4))
    if fill > 0:
        line_on(img, (x0, y), (x0 + (x1 - x0) * fill, y), col, 8, alpha)
    n = len(marks)
    for i, m in enumerate(marks):
        mx = x0 + (x1 - x0) * (i / float(n - 1) if n > 1 else 0.5)
        qi = esmooth(seg(tg, t0 + i * dt, t0 + i * dt + 0.4))
        if qi <= 0:
            continue
        dot_on(img, mx, y, 11, col, alpha * qi)
        ring_on(img, mx, y, 11 + 8 * (1 - qi), col, 3, alpha * qi)
        paste_c(img, mx, y + 46, m, font(FS, fsz), mix(col, INK, 0.20), alpha * qi)
    ph = clamp((tg - t0) / max(0.4, dt * (n - 1)))
    if 0 < ph < 1:
        px3 = x0 + (x1 - x0) * ph
        dot_on(img, px3, y, 8, mix(col, WHITE, 0.50), alpha)


def _tanya_on(img, cx, cy, text, alpha, tt, w=600, fsz=27, col=None):
    """Balon bicara pertanyaan: memancing rasa penasaran sebelum jawaban."""
    if alpha <= 0.01 or tt <= 0 or not text:
        return
    col = col or BLUE
    f = font(FS, fsz)
    lines = wrap(text, f, w - 70)
    h_ = 46 + len(lines) * tlh(f)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    sc = 0.55 + 0.45 * eob(min(1.0, tt), 1.8)
    bw, bh = int(S(w * sc)), int(S(h_ * sc))
    bx, by = int(S(cx) - bw / 2), int(S(cy) - bh / 2)
    dd.rounded_rectangle([bx, by, bx + bw, by + bh], radius=S(34 * sc), fill=mix(col, WHITE, 0.92) + (255,),
                         outline=col + (255,), width=max(2, int(S(4))))
    tx2 = int(S(cx) - 22 * sc)
    dd.polygon([(tx2 - 26 * sc, by + bh - 2), (tx2 + 26 * sc, by + bh - 2), (tx2 - 6 * sc, by + bh + 30 * sc)],
               fill=mix(col, WHITE, 0.92) + (255,))
    yy = by + bh / 2 - (len(lines) - 1) * tlh(f) * 0.5
    for ln2 in lines:
        dd.text((bx + bw / 2, yy), ln2, font=f, fill=mix(col, INK, 0.30) + (255,), anchor="mm")
        yy += tlh(f)
    img.paste(lay, (0, 0), lay if alpha >= 0.995 else lay.getchannel("A").point(
        lambda v: int(v * clamp(alpha))))


def _check5_on(img, cx, cy, r, kind, alpha, tt, col=None):
    """Centang / silang BESAR digambar progresif (fakta vs mitos, benar-salah)."""
    if alpha <= 0.01 or tt <= 0:
        return
    col = col or (mix(BLUE, INK, 0.05) if kind == "check" else RED)
    ck = clamp(tt)
    if kind == "check":
        p1 = (cx - 0.52 * r, cy + 0.02 * r)
        p2 = (cx - 0.12 * r, cy + 0.42 * r)
        p3 = (cx + 0.58 * r, cy - 0.44 * r)
    else:
        p1 = (cx - 0.48 * r, cy - 0.48 * r)
        p2 = (cx + 0.48 * r, cy + 0.48 * r)
        p3 = (cx + 0.48 * r, cy - 0.48 * r)
        p4 = (cx - 0.48 * r, cy + 0.48 * r)
    if kind == "check":
        if ck < 0.5:
            q1 = ck / 0.5
            line_on(img, p1, (p1[0] + (p2[0] - p1[0]) * q1, p1[1] + (p2[1] - p1[1]) * q1), col, 16, alpha)
        else:
            line_on(img, p1, p2, col, 16, alpha)
            q2 = (ck - 0.5) / 0.5
            line_on(img, p2, (p2[0] + (p3[0] - p2[0]) * q2, p2[1] + (p3[1] - p2[1]) * q2), col, 16, alpha)
    else:
        if ck < 0.5:
            q1 = ck / 0.5
            line_on(img, p1, (p1[0] + (p2[0] - p1[0]) * q1, p1[1] + (p2[1] - p1[1]) * q1), col, 15, alpha)
        else:
            line_on(img, p1, p2, col, 15, alpha)
            q2 = (ck - 0.5) / 0.5
            line_on(img, p3, (p3[0] + (p4[0] - p3[0]) * q2, p3[1] + (p4[1] - p3[1]) * q2), col, 15, alpha)


def _burst_on(img, cx, cy, r, col, alpha, tg, n=10):
    """Burst sinar penekanan: momen 'poin penting' muncul di sekitar objek."""
    if alpha <= 0.01:
        return
    for k in range(n):
        aa = k * 2.399963 + tg * 0.35
        ph = (tg * 1.25 + k / float(n)) % 1.0
        r0 = r * (0.55 + 0.55 * ph)
        x1 = cx + r0 * math.cos(aa)
        y1 = cy + r0 * 0.9 * math.sin(aa)
        x2 = cx + (r0 + r * 0.22) * math.cos(aa)
        y2 = cy + (r0 + r * 0.22) * 0.9 * math.sin(aa)
        line_on(img, (x1, y1), (x2, y2), mix(col, WHITE, 0.35), 6, alpha * (1.0 - ph))


def _selftest_v5():
    """Uji cepat seluruh paket v5 sebelum render."""
    names = ["heart", "brain", "lung", "stomach", "tooth", "eye", "bone", "germ",
             "clock", "thermo", "flame", "snow", "drop", "bolt", "moon", "shield"]
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    for k, n in enumerate(names):
        _ico5(img, n, 150 + (k % 8) * 110, 420 + (k // 8) * 170, 46, BLUE, 1.0, tg=1.2, pulse=0.5)
    for tl in (0.2, 1.0, 2.4, 4.0):
        _loupe_on(img, 540, 900, 300, 1000, 90, 1.0, tl, zoom=2.2)
        _callout_on(img, 620, 860, 850, 700, "BAGIAN INI", 1.0, tl)
        _flow_on(img, 1250, [("germ", "MASUK"), ("lung", "PARU"), ("bolt", "REAKSI")], 1.0, tl)
        _versus_on(img, 1000, ("shield", "AMAN", BLUE), ("flame", "BAHAYA", RED), 1.0, tl)
        _spotlight_on(img, 540, 900, 240, 1.0, tl, dim=0.30)
        _fan_on(img, 540, 1500, -90, 1.0, tl)
        _timeline_on(img, 140, 940, 1600, ["H-3", "HARI INI", "BESOK"], 1.0, tl)
        _tanya_on(img, 540, 700, "KENAPA BISA BEGINI?", 1.0, tl)
        _check5_on(img, 240, 1600, 60, "check", 1.0, tl)
        _check5_on(img, 840, 1600, 60, "x", 1.0, tl)
        _burst_on(img, 540, 900, 200, WARN27, 1.0, tl)
    print("selftest v5: 16 ikon + 10 elemen penjelas OK")


# ====================================================================
# MESIN v6 - SINEMA (21 Sep):
# caption karaoke kata-per-kata, stempel kata, donut, equalizer,
# punch kamera, confetti, balon pikir. Gaya orisinal KlikTahu.
# ====================================================================

CONFETTI6 = [(192, 57, 43), (47, 111, 181), (241, 196, 15), (39, 174, 96), (155, 89, 182)]




def _pikir_on(img, cx, cy, text, alpha, tt, col=None, w=540, fsz=24):
    """Balon pikir (awan + gelembung ekor) berisi teks - pop masuk."""
    if alpha <= 0.01 or tt <= 0 or not text:
        return
    col = col or BLUE
    f = font(FS, fsz)
    lines = wrap(text, f, w - 90)
    h_ = 40 + len(lines) * tlh(f)
    sc = 0.55 + 0.45 * eob(min(1.0, tt), 1.8)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    bw, bh = int(S(w * sc)), int(S(h_ * sc))
    bx, by = int(S(cx) - bw / 2), int(S(cy) - bh / 2)
    fill = mix(col, WHITE, 0.92) + (255,)
    dd.ellipse([bx, by, bx + int(S(46 * sc)), by + bh], fill=fill, outline=col + (255,), width=max(2, int(S(3))))
    dd.ellipse([bx + bw - int(S(46 * sc)), by, bx + bw, by + bh], fill=fill, outline=col + (255,),
               width=max(2, int(S(3))))
    dd.rounded_rectangle([bx + int(S(20 * sc)), by, bx + bw - int(S(20 * sc)), by + bh],
                         radius=int(S(bh / 2)), fill=fill)
    dd.line([bx + int(S(20 * sc)), by + bh // 2, bx + bw - int(S(20 * sc)), by + bh // 2],
            fill=col + (255,), width=max(2, int(S(3))))
    # gelembung ekor ke bawah-kiri (arah kepala tokoh)
    dd.ellipse([bx - int(S(10 * sc)), by + bh - int(S(4 * sc)), bx + int(S(26 * sc)), by + bh + int(S(16 * sc))],
               fill=fill, outline=col + (255,), width=max(2, int(S(3))))
    dd.ellipse([bx - int(S(30 * sc)), by + bh + int(S(16 * sc)), bx - int(S(8 * sc)), by + bh + int(S(36 * sc))],
               fill=fill, outline=col + (255,), width=max(2, int(S(3))))
    yy = by + bh / 2 - (len(lines) - 1) * tlh(f) * 0.5
    for ln2 in lines:
        dd.text((bx + bw / 2, yy), ln2, font=f, fill=mix(col, INK, 0.30) + (255,), anchor="mm")
        yy += tlh(f)
    img.paste(lay, (0, 0), lay if alpha >= 0.995 else lay.getchannel("A").point(
        lambda v: int(v * clamp(alpha))))


def _karaoke_on(img, cx, cy, teks, f, col, alpha, tg, t0=0.0, wps=2.6, hi=None, maxw=880):
    """Caption karaoke: kata muncul satu per satu, kata AKTIF dapat pil warna.
    (Standar caption Shorts 2026 - penonton mengikuti ritme bicara.)"""
    if alpha <= 0.01 or not teks:
        return
    hi = hi or mix(col, INK, 0.05)
    words = teks.split()
    spw = [tw(w2 + " ", f) for w2 in words]
    lw = [tw(w2, f) for w2 in words]
    lh_ = tlh(f)
    lines, cur, curw = [], [], 0
    for i, w2 in enumerate(words):
        add = spw[i] if cur else lw[i]
        if cur and curw + add > maxw:
            lines.append(cur)
            cur, curw = [], 0
            add = lw[i]
        cur.append(i)
        curw += add
    if cur:
        lines.append(cur)
    y0 = cy - (len(lines) - 1) * lh_ / 2.0
    for li, row in enumerate(lines):
        total = sum(spw[i] for i in row) - spw[row[-1]]
        xx = cx - total / 2.0
        yy = y0 + li * lh_
        for i in row:
            tk = t0 + i / float(wps)
            ap = clamp((tg - tk) / 0.12)
            sc = 0.60 + 0.40 * eob(clamp((tg - tk) / 0.20), 1.7)
            aktif = tk <= tg < tk + 1.7 / wps
            if aktif:
                rrect_on(img, xx - 12, yy + lh_ * 0.10, xx + lw[i] + 12, yy + lh_ * 0.92,
                         (lh_ * 0.40), hi, alpha * ap)
            warna = WHITE if aktif else (col if ap > 0.99 else mix(col, CREAM, 0.45))
            lay = Image.new("RGBA", (int(S(lw[i] + 6)), int(S(lh_ + 6))), (0, 0, 0, 0))
            dd = ImageDraw.Draw(lay)
            dd.text((int(S(lw[i] / 2 + 3)), int(S(lh_ / 2 + 3))), words[i], font=f,
                    fill=tuple(warna) + (255,), anchor="mm")
            if sc < 0.995:
                lay = lay.resize((max(2, int(lay.width * sc)), max(2, int(lay.height * sc))), Image.LANCZOS)
            pos = (int(S(xx + lw[i] / 2) - lay.width / 2), int(S(yy + lh_ / 2) - lay.height / 2))
            if ap < 0.995:
                a2 = lay.getchannel("A").point(lambda v: int(v * clamp(alpha * ap)))
                img.paste(lay.convert("RGB"), pos, a2)
            else:
                img.paste(lay, pos, lay)
            xx += spw[i]


def _stamp_on(img, cx, cy, text, alpha, tt, col=None, fsz=64, rot=-7.0):
    """Stempel kata (BAM!): menghantam masuk besar lalu mengunci + garis impak."""
    if alpha <= 0.01 or tt <= 0 or not text:
        return
    col = col or RED
    f = font(FB, fsz)
    sc = 2.1 - 1.1 * eob(clamp(tt / 0.30), 2.2)
    lay = Image.new("RGBA", (int(S(tw(text, f) + 60)), int(S(tlh(f) + 50))), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    dd.text((lay.width / 2, lay.height / 2), text, font=f, fill=col + (255,), anchor="mm")
    if abs(rot) > 0.1:
        lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
    if sc < 0.995:
        lay = lay.resize((max(2, int(lay.width * sc)), max(2, int(lay.height * sc))), Image.LANCZOS)
    pos = (int(S(cx) - lay.width / 2), int(S(cy) - lay.height / 2))
    ap = clamp(tt / 0.10)
    if ap < 0.995:
        a2 = lay.getchannel("A").point(lambda v: int(v * clamp(alpha * ap)))
        img.paste(lay.convert("RGB"), pos, a2)
    else:
        img.paste(lay, pos, lay)
    if tt < 0.40:
        qa = 1.0 - tt / 0.40
        for k in range(6):
            aa = k * math.pi / 3.0 + 0.4
            r0 = 0.62 * max(lay.width, lay.height) * 0.5 / S(1) * (0.9 + 0.5 * qa)
            p1 = (cx + r0 * math.cos(aa), cy + r0 * 0.7 * math.sin(aa))
            p2 = (cx + (r0 + 46 * qa) * math.cos(aa), cy + (r0 + 46 * qa) * 0.7 * math.sin(aa))
            line_on(img, p1, p2, mix(col, WHITE, 0.35), 6, alpha * qa)


def _donut_on(img, cx, cy, r, frac, col, alpha, tg=0.0, label=None, unit="%"):
    """Donut proses: cincin terisi animasi + angka % di tengah (data jadi gambar)."""
    if alpha <= 0.01:
        return
    fill = eob(clamp(tg / 0.9), 1.4)
    fr = clamp(frac) * fill
    ring_on(img, cx, cy, r, mix(col, CREAM, 0.55), max(3, int(S(13))), alpha, squash=1.0)
    if fr > 0.005:
        lay = _layer(img)
        dd = ImageDraw.Draw(lay)
        bb = [S(cx - r), S(cy - r), S(cx + r), S(cy + r)]
        dd.arc(bb, -90, -90 + 360 * fr, fill=col + (255,), width=max(3, int(S(13))))
        _put(img, lay, alpha)
        aa = math.radians(-90 + 360 * fr)
        dot_on(img, cx + r * math.cos(aa), cy + r * math.sin(aa), S(7), col, alpha)
    paste_c(img, cx, cy - 4, str(int(round(fr * 100))) + unit, font(FB, max(20, int(r * 0.52))),
            mix(col, INK, 0.20), alpha)
    if label:
        paste_c(img, cx, cy + r + 30, label, font(FS, 21), MUTED, alpha)


def _eq_on(img, x0, x1, y, col, alpha, tg, n=9, fr=None, hmax=120, label=None):
    """Bar equalizer hidup: level/perbandingan yang berdenyut (bukan angka mati)."""
    if alpha <= 0.01 or n < 1:
        return
    gap = (x1 - x0) / n
    bw = gap * 0.58
    for k in range(n):
        v = fr[k] if fr else clamp(0.34 + 0.30 * math.sin(tg * 3.1 + k * 1.15) +
                                   0.22 * math.sin(tg * 5.7 + k * 2.3))
        h2 = hmax * (0.18 + 0.82 * clamp(v))
        xx = x0 + gap * (k + 0.5)
        rrect_on(img, xx - bw / 2, y - h2, xx + bw / 2, y, bw / 2, mix(col, CREAM, 0.30), alpha)
        rrect_on(img, xx - bw / 2, y - h2, xx + bw / 2, y, bw / 2, col, alpha * 0.85)
        dot_on(img, xx, y - h2 - 7, 3.4, col, alpha * 0.8)
    line_on(img, (x0 - 14, y), (x1 + 14, y), mix(col, INK, 0.20), 4, alpha)
    if label:
        paste_c(img, (x0 + x1) / 2, y + 26, label, font(FS, 21), MUTED, alpha)


def _punch_on(img, cx, cy, rr, alpha, tt, dur=0.55, kmax=0.10):
    """Punch kamera: zoom mendadak ke subjek lalu mengunci (pukulan ritme).
    Dipakai di beat penting; area luar tetap asli (tepi dihaluskan)."""
    if alpha <= 0.01 or tt <= 0 or tt >= dur:
        return
    k = kmax * (1.0 - (1.0 - clamp(tt / dur)) ** 3)
    W2, H2 = img.size
    cw = int(W2 / (1.0 + k))
    ch = int(H2 / (1.0 + k))
    x0 = int(clamp(S(cx) - cw / 2, 0, W2 - cw))
    y0 = int(clamp(S(cy) - ch / 2, 0, H2 - ch))
    big = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W2, H2), Image.BICUBIC)
    from PIL import ImageFilter
    mask = Image.new("L", (W2, H2), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([S(cx - rr * 1.25), S(cy - rr * 1.25), S(cx + rr * 1.25), S(cy + rr * 1.25)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(int(S(40))))
    mask = mask.point(lambda v: int(v * clamp(alpha)))
    img.paste(big, (0, 0), mask)


def _confetti_on(img, tg, alpha, n=24, y1=None):
    """Hujan confetti berputar - momen jawaban terungkap / perayaan tips."""
    if alpha <= 0.01:
        return
    Hf = float(y1 or H)
    for i in range(n):
        ph = ((tg * (0.24 + 0.13 * (i % 4)) + i * 0.61803) % 1.4)
        if ph > 1.0:
            continue
        x = 70 + ((i * 173.0) % max(1.0, W - 140)) + 26 * math.sin(tg * 1.4 + i)
        y = ph * (Hf + 140) - 70
        w2, h2 = 15 + (i % 3) * 5, 9 + (i % 2) * 4
        ang = math.degrees(tg * (2.2 + 0.6 * (i % 5)) + i)
        col2 = CONFETTI6[i % len(CONFETTI6)]
        lay = Image.new("RGBA", (int(S(w2)) + 4, int(S(h2)) + 4), (0, 0, 0, 0))
        ImageDraw.Draw(lay).rounded_rectangle([2, 2, lay.width - 2, lay.height - 2], radius=3,
                                              fill=col2 + (255,))
        lay = lay.rotate(ang, resample=Image.BICUBIC, expand=True)
        fade = alpha * clamp(min(ph * 6.0, (1.0 - ph) * 4.0))
        if fade < 0.02:
            continue
        img.paste(lay, (int(S(x)) - lay.width // 2, int(S(y)) - lay.height // 2),
                  lay.getchannel("A").point(lambda v: int(v * clamp(fade))))


def _selftest_v6():
    """Uji cepat seluruh paket v6."""
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    _pikir_on(img, 540, 760, "KENAPA YA...", 1.0, 1.0)
    _karaoke_on(img, 540, 1000, "INI DIA PENJELASAN KUNCINYA UNTUK KAMU", font(FB, 34), BLUE, 1.0, 1.35, t0=0.2)
    _stamp_on(img, 540, 1160, "PENTING!", 1.0, 0.9, col=RED)
    _donut_on(img, 210, 1420, 80, 0.72, BLUE, 1.0, tg=1.2, label="SERAPAN")
    _eq_on(img, 400, 880, 1500, DATA, 1.0, 1.1, n=9, label="LEVEL")
    _punch_on(img, 540, 1420, 220, 1.0, 0.12)
    _confetti_on(img, 1.05, 1.0, n=22, y1=1800)
    print("selftest v6: pikir + karaoke + stamp + donut + eq + punch + confetti OK")


# ====================================================================
# MESIN v7 - IMAJINASI (21 Sep): anotasi tangan yang menggambar progresif,
# tokoh dengan kaki + mode jalan, kontainer tembus pandang (is-in),
# partikel mengalir di jalur, latar suasana waktu, papan rangkuman,
# label tokoh (lower-third). Semua bantu penonton MEMBAYANGKAN.
# ====================================================================



def _scribble_on(img, cx, cy, rr, alpha, tg, t0=0.0, dur=0.9, kind="circle", p2=None,
                 col=None, width=7):
    """Anotasi gaya tangan yang MENGGAMBAR sendiri di depan penonton:
    circle = mengelilingi objek (1,15 putaran dengan goyangan tangan),
    underline = garis bergelombang di bawah, arrow = panah melengkung ke p2."""
    if alpha <= 0.01:
        return
    col = col or mix(BLUE, INK, 0.05)
    prog = esmooth(seg(tg, t0, t0 + dur))
    if prog <= 0.01:
        return
    pts = []
    if kind == "circle":
        laps = 1.15
        for i in range(27):
            u = (i / 26.0) * prog * laps
            aa = -1.2 + u * 6.283
            wob = 1.0 + 0.035 * math.sin(i * 7.3) + 0.02 * math.sin(i * 3.1)
            pts.append((cx + rr * wob * math.cos(aa), cy + rr * 0.86 * wob * math.sin(aa)))
    elif kind == "underline":
        for i in range(23):
            u = (i / 22.0) * prog
            x = cx - rr + 2 * rr * u
            y = cy + 5.5 * math.sin(u * 5.2) + 1.5 * math.sin(i * 4.7)
            pts.append((x, y))
    else:  # arrow (kurva kuadratik p1->ctrl->p2)
        ex, ey = p2 if p2 else (cx + rr, cy - rr)
        mx, my = (cx + ex) / 2 + 0.22 * (ey - cy), (cy + ey) / 2 + 0.22 * (cx - ex)
        for i in range(25):
            u = (i / 24.0) * prog
            pts.append(((1 - u) ** 2 * cx + 2 * (1 - u) * u * mx + u * u * ex,
                        (1 - u) ** 2 * cy + 2 * (1 - u) * u * my + u * u * ey))
    if len(pts) >= 2:
        path_on(img, pts, col, width, alpha)
    if kind == "arrow" and prog > 0.97:
        ex, ey = p2 if p2 else (cx + rr, cy - rr)
        aa = math.atan2(ey - pts[-2][1], ex - pts[-2][0])
        poly_on(img, [(ex - 17 * math.cos(aa) + 10 * math.sin(aa), ey - 17 * math.sin(aa) - 10 * math.cos(aa)),
                      (ex - 17 * math.cos(aa) - 10 * math.sin(aa), ey - 17 * math.sin(aa) + 10 * math.cos(aa)),
                      (ex + 6 * math.cos(aa), ey + 6 * math.sin(aa))], col, alpha)


def _cutaway_on(img, x0, y0, x1, y1, fill_frac, col, alpha, tg, label=None, bubbles=True):
    """Tembus pandang 'masuk ke dalam': dinding kontainer + isian cair dengan
    permukaan bergelombang + gelembung naik (isi lambung/kaleh/baterai dsb.)."""
    if alpha <= 0.01:
        return
    fr = clamp(fill_frac) * eob(clamp(tg / 0.8), 1.4)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    r_ = S(34)
    dd.rounded_rectangle([S(x0), S(y0), S(x1), S(y1)], radius=r_, outline=col + (255,),
                         width=max(3, int(S(6))))
    _put(img, lay, alpha * 0.95)
    if fr > 0.02:
        ysurf = (y1 - 10) - (y1 - y0 - 20) * fr
        lay2 = _layer(img)
        dd2 = ImageDraw.Draw(lay2)
        dd2.rounded_rectangle([S(x0 + 6), S(y0 + 6), S(x1 - 6), S(y1 - 6)], radius=r_ - S(5),
                              fill=mix(col, WHITE, 0.72) + (255,))
        pts = [(S(x0 + 6), S(y1 - 6))]
        for i in range(21):
            xx = x0 + 6 + (x1 - x0 - 12) * (i / 20.0)
            pts.append((S(xx), S(ysurf + 6.5 * math.sin(tg * 2.4 + i * 0.9))))
        pts.append((S(x1 - 6), S(y1 - 6)))
        dd2.polygon(pts, fill=col + (230,))
        if bubbles:
            for k in range(5):
                ph = (tg * 0.5 + k * 0.197) % 1.0
                by = (y1 - 14) - (y1 - 14 - ysurf) * ph
                bx = x0 + 26 + ((k * 97) % max(1, int(x1 - x0 - 52)))
                dd2.ellipse([S(bx - 6), S(by - 6), S(bx + 6), S(by + 6)],
                            outline=mix(col, WHITE, 0.55) + (200,), width=max(1, int(S(2))))
        from PIL import ImageChops
        mclip = Image.new("L", lay2.size, 0)
        ImageDraw.Draw(mclip).rounded_rectangle([S(x0 + 6), S(y0 + 6), S(x1 - 6), S(y1 - 6)],
                                                radius=r_ - S(5), fill=255)
        lay2.putalpha(ImageChops.multiply(lay2.getchannel("A"), mclip))
        _put(img, lay2, alpha)


def _flowpath_on(img, pts, col, alpha, tg, n=6, speed=0.22, size=5.0):
    """Partikel mengalir di sepanjang jalur (udara ke paru, makanan ke usus,
    sinyal ke otak) - jalur pipa + butir bergerak dengan ekor kecil."""
    if alpha <= 0.01 or len(pts) < 2:
        return
    seglen = []
    tot = 0.0
    for i in range(len(pts) - 1):
        d2 = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        seglen.append(d2)
        tot += d2
    path_on(img, pts, mix(col, CREAM, 0.62), 10, alpha * 0.85)
    for k in range(n):
        u = ((tg * speed + k / float(n)) % 1.0)
        target = u * tot
        acc = 0.0
        for i in range(len(seglen)):
            if acc + seglen[i] >= target:
                f = (target - acc) / max(0.001, seglen[i])
                px = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
                py = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
                ux = (pts[i + 1][0] - pts[i][0]) / max(0.001, seglen[i])
                uy = (pts[i + 1][1] - pts[i][1]) / max(0.001, seglen[i])
                dot_on(img, px - ux * 9, py - uy * 9, size * 0.55, mix(col, WHITE, 0.45), alpha * 0.6)
                dot_on(img, px, py, size, col, alpha)
                break
            acc += seglen[i]


_MOODS7 = {
    "pagi": ((255, 236, 200), (188, 226, 240)),
    "siang": ((166, 214, 244), (214, 240, 250)),
    "sore": ((255, 190, 130), (255, 226, 180)),
    "malam": ((38, 52, 92), (74, 92, 130)),
}


def _langit7(img, x0, y0, x1, y1, alpha, tg, mood="siang", sun=None):
    """Latar suasana waktu (pagi/siang/sore/malam): gradasi langit + matahari/
    bulan + awan drift - penonton langsung tahu kapan cerita terjadi."""
    if alpha <= 0.01:
        return
    top, bot = _MOODS7.get(mood, _MOODS7["siang"])
    steps = 16
    for i in range(steps):
        f = i / float(steps - 1)
        c2 = mix(top, bot, f)
        line_on(img, (x0, y0 + (y1 - y0) * i / steps), (x1, y0 + (y1 - y0) * (i + 1) / steps), c2,
                max(2, (y1 - y0) // steps + 2), alpha)
    cx = 540 if sun is None else sun[0]
    cy = (y0 + y1) * 0.30 if sun is None else sun[1]
    if mood == "malam":
        _i5_moon(img, cx, cy, 46, mix((255, 255, 255), top, 0.2), alpha, tg)
        for k in range(9):
            sx = x0 + 30 + ((k * 173) % max(1, int(x1 - x0 - 60)))
            sy = y0 + 20 + ((k * 97) % max(1, int((y1 - y0) * 0.5)))
            dot_on(img, sx, sy, 2.2 + (k % 2), mix(WHITE, top, 0.15), alpha * (0.5 + 0.5 * math.sin(tg * 1.3 + k)))
    else:
        col_s = (255, 210, 90) if mood != "sore" else (255, 150, 80)
        _glow(img, cx - 46, cy - 46, cx + 46, cy + 46, col_s, alpha)
        ell(img, cx - 30, cy - 30, cx + 30, cy + 30, fill=col_s, alpha=alpha)
    for k in range(2):
        # pusat awan dikunci di dalam panel (awannya melebar +-110px; margin QC aman)
        span = max(1.0, (x1 - x0) - 260)
        wx = x0 + 130 + ((tg * (14 + 6 * k) + k * 470) % span)
        wy = y0 + 60 + k * 66
        _cloud(img, wx, wy, 1.0 + 0.2 * k, mix(WHITE, bot, 0.25), alpha * 0.9)


def _recap_on(img, items, alpha, tg, t0=0.4, dt=0.65, col=None):
    """Papan rangkuman akhir: kartu ikon + poin pop berurutan (retensi)."""
    if alpha <= 0.01 or not items:
        return
    col = col or BLUE
    y = 1120
    for i, (ic, txt) in enumerate(items):
        qi = esmooth(seg(tg, t0 + i * dt, t0 + i * dt + 0.45))
        if qi <= 0:
            continue
        yy = y + i * 165
        panel(img, 120, yy - 62, 960, yy + 62, alpha * qi, radius=40, fill=mix(WHITE, col, 0.05))
        ring_on(img, 210, yy, 44, mix(col, CREAM, 0.30), 5, alpha * qi)
        _ico5(img, ic, 210, yy, 30, col, alpha * qi, tg)
        for j, ln2 in enumerate(wrap(txt, font(FS, 27), 640)[:2]):
            paste_c(img, 600, yy - 14 + j * 34, ln2, font(FS, 27), mix(col, INK, 0.15), alpha * qi)
        dot_on(img, 922, yy, 7, col, alpha * qi * (0.6 + 0.4 * math.sin(tg * 3 + i)))


def _lower3_on(img, name, alpha, tt, col=None, y=1750):
    """Label nama tokoh (lower-third): pill masuk meluncur dari kiri."""
    if alpha <= 0.01 or tt <= 0 or not name:
        return
    col = col or BLUE
    f = font(FS, 24)
    w_ = tw(name, f) + 74
    slide = (1.0 - eob(min(1.0, tt), 1.6)) * (w_ + 120)
    lay = Image.new("RGBA", (int(S(w_ + 6)), int(S(56 + 6))), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([S(3), S(3), S(3 + w_), S(3 + 56)], radius=S(28), fill=mix(col, WHITE, 0.90) + (255,))
    dd.ellipse([S(20), S(16 + 3), S(44), S(40 + 3)], fill=col + (255,))
    dd.text((S(3 + 58 + tw(name, f) / 2), S(3 + 28)), name, font=f, fill=mix(col, INK, 0.25) + (255,),
            anchor="mm")
    pos = (int(S(52) - slide), int(S(y)))
    if alpha < 0.995:
        img.paste(lay.convert("RGB"), pos, lay.getchannel("A").point(lambda v: int(v * clamp(alpha))))
    else:
        img.paste(lay, pos, lay)


def _selftest_v7():
    """Uji cepat seluruh paket v7."""
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    _langit7(img, 60, 420, 1020, 900, 1.0, 1.2, mood="sore")
    _lower3_on(img, "SI KAMU", 1.0, 1.0, col=RED, y=700)
    for tl in (0.2, 0.6, 1.0):
        _scribble_on(img, 540, 1060, 150, 1.0, tl, t0=0.0, kind="circle")
        _scribble_on(img, 540, 1240, 220, 1.0, tl, t0=0.2, kind="underline")
        _scribble_on(img, 540, 1300, 0, 1.0, tl, t0=0.1, kind="arrow", p2=(850, 1150))
    _cutaway_on(img, 150, 1380, 520, 1700, 0.62, ORANGE if "ORANGE" in globals() else RED, 1.0, 1.3,
                bubbles=True)
    _flowpath_on(img, [(560, 1400), (700, 1480), (840, 1440), (950, 1560)], DATA, 1.0, 1.2)
    _recap_on(img, [("heart", "Jantung memompa lebih kuat"), ("lung", "Paru menyerap oksigen"),
                    ("bolt", "Sinyal sampai ke otak")], 1.0, 1.6, t0=0.0)
    print("selftest v7: anotasi tangan + cutaway + flowpath + langit + recap + lower3 OK")


# ====================== Ep32: Kenapa Demam Naik Malam? ======================

AMBER32 = (176, 90, 40)                    # panas
DINGIN32 = (74, 90, 140)                   # dingin


def _virus32(img, cx, cy, s, col, alpha, tg=0.0, lesu=0.0):
    """Kuman bulat berduri; lesu 0..1 = gerak melemah & wajah layu."""
    if alpha <= 0.01:
        return
    wob = 1.0 - 0.55 * lesu
    rr = s * (1.0 + 0.05 * wob * math.sin(tg * 3.0))
    ell(img, cx - rr, cy - rr * 0.92, cx + rr, cy + rr * 0.92, fill=mix(col, WHITE, 0.58), alpha=alpha,
        outline=col, width=3)
    for k in range(6):
        aa = k / 6.0 * 6.283 + 0.4
        l2 = rr * (1.12 + 0.10 * wob * math.sin(tg * 4.0 + k * 2.1))
        line_on(img, (cx + rr * 0.92 * math.cos(aa), cy + rr * 0.92 * math.sin(aa)),
                (cx + l2 * math.cos(aa), cy + l2 * math.sin(aa)), col, 4, alpha)
    for k, (dx, dy2) in enumerate(((-0.30, -0.15), (0.12, -0.20), (0.30, 0.05))):
        ex = cx + dx * rr
        ell(img, ex - 2.6 * s, cy + dy2 * rr - 2.6 * s, ex + 2.6 * s, cy + dy2 * rr + 2.6 * s,
            fill=mix(col, INK, 0.25), alpha=alpha * wob)
    ell(img, cx - rr * 0.16, cy + rr * 0.30, cx + rr * 0.16, cy + rr * 0.52,
        fill=mix(col, INK, 0.30), alpha=alpha * (1.0 - 0.5 * lesu))


def _selimun32(img, cx, cy, s, col, alpha, tg=0.0):
    """Sel imun: blob amuba berinti yang berdenyut dan menjulur."""
    if alpha <= 0.01:
        return
    rr = s * (1.0 + 0.07 * math.sin(tg * 2.6))
    for k in range(10):
        aa = k / 10.0 * 6.283 + 0.2 * math.sin(tg * 1.7)
        l2 = rr * (1.0 + 0.16 * math.sin(tg * 3.1 + k * 1.9))
        dot_on(img, cx + l2 * math.cos(aa), cy + l2 * math.sin(aa), rr * 0.30, col, alpha * 0.8)
    ell(img, cx - rr, cy - rr * 0.88, cx + rr, cy + rr * 0.88, fill=mix(col, WHITE, 0.30), alpha=alpha)
    dot_on(img, cx + 3 * math.sin(tg * 2.2), cy - rr * 0.10, rr * 0.26, mix(col, INK, 0.22), alpha)


def _dial32(img, cx, cy, r, frac, alpha, tg, col, label=None):
    """Gauge setelan suhu 36-40: busur atas + jarum pada frac 0..1."""
    if alpha <= 0.01:
        return
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.arc([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], 180, 360,
           fill=mix(col, INK, 0.25) + (255,), width=max(2, int(S(7))))
    for k in range(9):
        aa = math.pi + (k / 8.0) * math.pi
        dd.line([S(cx + (r + 12) * math.cos(aa)), S(cy + (r + 12) * math.sin(aa)),
                 S(cx + (r + 26) * math.cos(aa)), S(cy + (r + 26) * math.sin(aa))],
                fill=mix(col, INK, 0.20) + (255,), width=max(2, int(S(4))))
    _put(img, lay, alpha)
    for k, tk in enumerate(("36", "38", "40")):
        aa = math.pi + (k / 4.0) * math.pi
        paste_c(img, cx + (r + 54) * math.cos(aa), cy + (r + 52) * math.sin(aa), tk,
                font(FS, 24), MUTED, alpha)
    aa = math.pi + clamp(frac) * math.pi
    line_on(img, (cx, cy), (cx + (r - 18) * math.cos(aa), cy + (r - 18) * math.sin(aa)), col, 8, alpha)
    dot_on(img, cx, cy, 12, col, alpha)
    if label:
        paste_c(img, cx, cy + 42, label, font(FS, 24), mix(col, INK, 0.15), alpha)


def sc_intro_demam(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: malam panas, termometer merambat naik, tokoh meriang."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    q1 = seg(tl, 0.55, 1.0)
    if q1 > 0:
        _pop_pill(img, 540, 700 + dy, "BUKAN MUSUH - INI STRATEGI", 26, mix(accent, INK, 0.10), q1 * al, q1)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    pang = mix(CREAM, mix(accent, INK, 0.30), 0.24)
    rrect_on(img, 104, 776 + dy, 976, 1596 + dy, 46, pang, q2 * al)
    _langit7(img, 118, 790 + dy, 962, 1582 + dy, q2 * al, tg, mood="malam", sun=(886, 1130))
    _papan9_on(img, 330, 1250 + dy, 1.1, q2 * al, tg, ikon="thermo", col=mix(accent, INK, 0.30))
    _lower3_on(img, "SI KAMU", q2 * al * seg(tl, 1.6, 2.0), tl, col=mix(accent, INK, 0.30), y=1424)
    lvl = clamp(0.22 + 0.10 * tl * (0.6 + 0.4 * math.sin(tg * 0.9)))
    _thermo(img, 790, 950 + dy, 1510 + dy, lvl, q2 * al)
    val = 36.0 + 3.0 * lvl
    paste_c(img, 790, 905 + dy, f"{val:.1f}".replace(".", ",") + " DERAJAT", font(FB, 38),
            WARN27 if lvl > 0.6 else mix(pang, INK, 0.10), q2 * al)
    _lbl(img, 330, 1530 + dy, "DEMET: PANAS + GIGIL", font(FS, 24), mix(pang, INK, 0.10), q2 * al)
    q4 = seg(tl, 2.6, 3.2)
    if q4 > 0:
        _pop_pill(img, 540, 1660 + dy, "TERMOSTAT TUBUH - INI SAINS", 24, mix(accent, INK, 0.10), q4 * al, q4)


def sc_termostat(img, d, sc, tl, dur, tg, accent, al, dy):
    """f1: otak + hipotalamus = termostat; setelan 37 sengaja dinaikkan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    hx, hy = 330, 1150 + dy
    ell(img, hx - 210, hy - 230, hx + 210, hy + 190, fill=mix(WHITE, accent, 0.10), alpha=q * al,
        outline=mix(accent, INK, 0.15), width=5)
    _ico5(img, "brain", hx, hy - 15, 125, mix(accent, INK, 0.15), q * al, tg)
    hpx, hpy = hx + 30, hy + 110
    dot_on(img, hpx, hpy, 16, WARN27, q * al)
    _scribble_on(img, hpx, hpy, 46, q * al, tg, t0=0.8, dur=1.0, kind="circle", col=WARN27, width=6)
    _scribble_on(img, hpx, hpy + 60, 0, q * al, tg, t0=2.0, kind="arrow", p2=(600, 1000 + dy),
                 col=WARN27, width=6)
    _lbl(img, hpx - 40, hpy + 92, "HIPOTALAMUS", font(FS, 26), WARN27, q * al)
    frac = clamp(0.25 + 0.018 * tl)
    _dial32(img, 790, 1170 + dy, 165, frac, q * al, tg, mix(accent, INK, 0.10), label="SETELAN SUHU")
    val = 36.0 + 4.0 * frac
    naik = frac > 0.32
    paste_c(img, 790, 880 + dy, ("SETELAN " if naik else "NORMAL ") + f"{val:.1f}".replace(".", ","),
            font(FB, 48), WARN27 if naik else mix(accent, INK, 0.12), q * al)
    if naik and seg(tl, 2.2, 2.8) > 0:
        _punch_on(img, 790, 905 + dy, 150, seg(tl, 2.2, 2.8), tg, dur=0.5)
    _lbl(img, 790, 1410 + dy, "NORMAL 37 - NAIK KE 38,5", font(FS, 24), MUTED, q * al)
    _papan9_on(img, 540, 1590 + dy, 0.9, q * al, tg, tanya=True, col=mix(accent, INK, 0.20))


def sc_sinyal(img, d, sc, tl, dur, tg, accent, al, dy):
    """f2: sel imun melempar sitokin, naik lewat pembuluh ke hipotalamus."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ico5(img, "brain", 540, 700 + dy, 110, mix(accent, INK, 0.15), q * al, tg)
    dot_on(img, 540, 815 + dy, 14, WARN27, q * al)
    _lbl(img, 790, 700 + dy, "HIPOTALAMUS", font(FS, 25), WARN27, q * al)
    _flowpath_on(img, [(540, 1500), (520, 1280), (565, 1050), (540, 845 + dy)], DATA, q * al, tg,
                 n=7, speed=0.16, size=7.0)
    _pop_pill(img, 710, 1160 + dy, "SITOKIN", 26, mix(accent, INK, 0.10), q * al, q)
    qa = esmooth(seg(tl, 0.5, 0.9))
    _cutaway_on(img, 150, 1380, 930, 1680, 0.55, mix(accent, INK, 0.10), qa * al, tg, bubbles=True)
    _lbl(img, 540, 1330 + dy, "LOKASI INFEKSI (TENGGOROKAN)", font(FS, 23), mix(accent, INK, 0.10), qa * al)
    for k in range(3):
        vx = 300 + k * 150 + 14 * math.sin(tg * 1.3 + k * 2.0)
        _virus32(img, vx, 1572 + dy, 28, mix(accent, INK, 0.12), qa * al, tg + k)
    _selimun32(img, 300 + ((tg * 120) % 460), 1612 + dy, 44, GREEN, qa * al, tg)
    _lbl(img, 620, 1690 + dy, "SEL IMUN BURU KUMAN", font(FS, 23), mix(accent, INK, 0.10), qa * al)
    beat_f = (tg % 2.2) / 2.2
    beat = max(0.0, 1.0 - beat_f * 3.0)
    if beat > 0.05 and tl > 1.2:
        _pop_txt(img, 540, 560 + dy, "SETELAN NAIK!", font(FB, 40), WARN27, q * al * beat, beat * 1.2)


def sc_baktempur(img, d, sc, tl, dur, tg, accent, al, dy):
    """f3: panel dingin vs panel panas - kuman lemas, imun gesit."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    rrect_on(img, 90, 830 + dy, 510, 1560 + dy, 40, mix(DINGIN32, WHITE, 0.72), q * al,
             outline=mix(DINGIN32, INK, 0.10), width=4)
    _thermo(img, 160, 900 + dy, 1290 + dy, 0.22, q * al)
    _lbl(img, 300, 940 + dy, "TANPA DEMAM", font(FS, 26), mix(DINGIN32, INK, 0.15), q * al)
    for k in range(3):
        vx = 340 + (k % 2) * 115
        vy = 1100 + (k // 2) * 140
        _virus32(img, vx + 16 * math.sin(tg * 1.1 + k), vy, 30, mix(DINGIN32, INK, 0.15), q * al, tg + k)
    _eq_on(img, 220, 470, 1450 + dy, DINGIN32, q * al, tg * 0.5, n=6, hmax=70, label="KUMAN: BEBAS")
    rrect_on(img, 570, 830 + dy, 990, 1560 + dy, 40, mix(AMBER32, WHITE, 0.72), q * al,
             outline=mix(AMBER32, INK, 0.10), width=4)
    _thermo(img, 640, 900 + dy, 1290 + dy, 0.78, q * al)
    _lbl(img, 790, 940 + dy, "SAAT DEMAM", font(FS, 26), mix(AMBER32, INK, 0.15), q * al)
    for k in range(3):
        vx = 815 + (k % 2) * 105
        vy = 1100 + (k // 2) * 140
        _virus32(img, vx, vy + 3 * math.sin(tg * 9 + k), 30, mix(AMBER32, INK, 0.10),
                 q * al * (0.55 + 0.2 * math.sin(tg * 2 + k)), tg + k, lesu=0.8)
    _selimun32(img, 780 + 70 * math.sin(tg * 2.4), 1240 + dy, 40, GREEN, q * al, tg * 1.6)
    _eq_on(img, 700, 950, 1450 + dy, mix(AMBER32, GREEN, 0.35), q * al, tg * 2.2, n=6, hmax=100,
           label="IMUN: GESIT")
    qs = esmooth(_dw(tl, dur, 0.55, 0.7))
    if qs > 0:
        _stamp_on(img, 540, 1650 + dy, "PANAS = SENJATA", qs * al, qs, col=accent, fsz=58, rot=-6)


def sc_gigil(img, d, sc, tl, dur, tg, accent, al, dy):
    """f4: suhu belum sampai setelan baru -> gigil (pemanas) + meriang."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    beat_f = (tg % 0.9) / 0.9
    beat = max(0.0, 1.0 - beat_f * 3.4)
    jx = 5.0 * math.sin(tg * 42.0) * (0.35 + 0.65 * beat)
    _papan9_on(img, 300 + jx, 1150 + dy, 1.05, q * al, tg, ikon="snow", col=mix(accent, INK, 0.25))
    _lbl(img, 300 + jx, 1420 + dy, "OTOT KONTRAKSI CEPAT", font(FS, 24), mix(accent, INK, 0.10), q * al)
    _eq_on(img, 180, 430, 1500 + dy, accent, q * al, tg * 3.0, n=7, hmax=90, label="PENCIPTA PANAS")
    if beat > 0.05:
        _swarm_on(img, 300 + jx, 1000 + dy, tg, mix(accent, WHITE, 0.20), q * al * beat * 0.8, n=7, sp=40)
        _pop_txt(img, 300 + jx, 920 + dy, "GIGIL!", font(FB, 40), accent, q * al * beat, beat * 1.3)
    qv = esmooth(seg(tl, 1.2, 1.6))
    if qv > 0:
        vx0, vx1, vy = 620, 990, 1120 + dy
        squeeze = 0.5 + 0.5 * math.sin(tg * 2.0)
        gap = 64 - 30 * squeeze
        line_on(img, (vx0, vy - gap), (vx1, vy - gap), mix(DINGIN32, INK, 0.15), 9, qv * al)
        line_on(img, (vx0, vy + gap), (vx1, vy + gap), mix(DINGIN32, INK, 0.15), 9, qv * al)
        _lbl(img, 805, vy - 128, "PEMBULUH KULIT MENYEMPIT", font(FS, 24), mix(DINGIN32, INK, 0.12), qv * al)
        _pop_pill(img, 805, vy + 182, "KULIT MERAHANG - MERIANG", 24, mix(DINGIN32, INK, 0.08), qv * al, qv * 1.2)
        for k, sgn in ((0, -1), (1, 1)):
            _scribble_on(img, 805, vy + sgn * (gap + 86), 0, qv * al, tg, t0=1.5 + 0.3 * k,
                         kind="arrow", p2=(805, vy + sgn * (gap + 18)), col=DINGIN32, width=6)
    qt = esmooth(seg(tl, 2.0, 2.4))
    if qt > 0:
        _thermo(img, 805, 1400 + dy, 1640 + dy, clamp(0.30 + 0.04 * tl), qt * al)
        _lbl(img, 805, 1378 + dy, "SUHU MENUJU SETELAN BARU", font(FS, 22), MUTED, qt * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _stamp_on(img, 540, 1745 + dy, "GIGIL = PEMANAS", qz * al, qz, col=accent, fsz=50, rot=-5)


def sc_malam(img, d, sc, tl, dur, tg, accent, al, dy):
    """f5: jawaban hook - pita 24 jam + grafik suhu memuncak malam."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    moods = ("pagi", "siang", "sore", "malam")
    labels = ("PAGI", "SIANG", "SORE", "MALAM")
    for k in range(4):
        x0 = 110 + k * 218
        _langit7(img, x0, 830 + dy, x0 + 200, 1010 + dy, q * al, tg, mood=moods[k],
                 sun=(x0 + 100, 892))
        _lbl(img, x0 + 100, 1042 + dy, labels[k], font(FS, 23),
             accent if k == 3 else MUTED, q * al * (1.0 if k == 3 else 0.75))
    qb = esmooth(seg(tl, 0.7, 1.1))
    if qb > 0.02:
        rrect_on(img, 110, 1100 + dy, 970, 1560 + dy, 36, mix(WHITE, accent, 0.10), qb * al,
                 outline=mix(accent, INK, 0.12), width=4)
        gx0, gx1, gy0, gy1 = 170, 910, 1160 + dy, 1500 + dy
        rrect_on(img, gx0 + (gx1 - gx0) * 0.60, gy0 - 14, gx0 + (gx1 - gx0) * 0.95, gy1 + 8, 18,
                 mix(accent, WHITE, 0.78), qb * al * 0.55)
        pts = []
        for j in range(41):
            u = j / 40.0
            xx = gx0 + (gx1 - gx0) * u
            dasar = 0.30 + 0.16 * math.sin((u - 0.15) * math.pi)
            puncak = 0.34 * math.exp(-((u - 0.78) ** 2) / 0.018)
            yy = gy1 - (gy1 - gy0) * clamp(dasar + puncak)
            pts.append((xx, yy))
        path_on(img, pts, WARN27, 8, qb * al)
        dot_on(img, pts[31][0], pts[31][1], 11, WARN27, qb * al)
        _pop_txt(img, pts[31][0] - 26, max(pts[31][1] - 58, gy0 + 44), "PUNCAK!", font(FB, 36), WARN27, qb * al, 1.2)
        for tk, uu in (("PAGI", 0.06), ("SIANG", 0.35), ("SORE", 0.62), ("MALAM", 0.83)):
            paste_c(img, gx0 + (gx1 - gx0) * uu, gy1 + 34, tk, font(FS, 22), MUTED, qb * al)
        _lbl(img, 330, gy0 + 18, "SUHU TUBUH 24 JAM", font(FS, 25), mix(accent, INK, 0.12), qb * al)
    qc = esmooth(_dw(tl, dur, 0.62, 0.74))
    if qc > 0:
        _pop_pill(img, 540, 1620 + dy, "KORTISOL PEREDAM PERADANGAN TURUN", 24,
                  mix(DINGIN32, INK, 0.08), qc * al, qc)
        _pop_pill(img, 540, 1695 + dy, "SITOKIN PALING AKTIF MALAM", 24, mix(WARN27, INK, 0.06), qc * al, qc)


def sc_naiturun(img, d, sc, tl, dur, tg, accent, al, dy):
    """f6: setelan turun -> keringat; obat hanya 2-3 jam; bukan kalah."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    lvl = clamp(0.55 + 0.26 * math.sin(tg * 1.1))
    _thermo(img, 300, 900 + dy, 1600 + dy, lvl, q * al)
    naik = lvl > 0.66
    val = 36.5 + 3.2 * lvl
    paste_c(img, 300, 855 + dy, f"{val:.1f}".replace(".", ","), font(FB, 48),
            WARN27 if naik else mix(accent, INK, 0.12), q * al)
    if naik:
        _pop_txt(img, 300, 790 + dy, "PERANG!", font(FB, 34), WARN27, q * al, 1.1)
    else:
        for k in range(5):
            ph = (tg * 0.9 + k * 0.2) % 1.0
            _ico5(img, "drop", 254 + (k % 2) * 26, 960 + ph * 300 + dy, 13, DATA,
                  q * al * (1.0 - ph * 0.4), tg)
        _lbl(img, 300, 1650 + dy, "KERINGAT = RADIATOR", font(FS, 25), mix(accent, INK, 0.12), q * al)
    qd = esmooth(seg(tl, 1.0, 1.4))
    if qd > 0:
        _donut_on(img, 760, 1150 + dy, 118, 0.34, accent, qd * al, tg, label="OBAT: 2-3 JAM", unit="")
        _lbl(img, 760, 1330 + dy, "SETELAN NAIK LAGI BELAKANGAN", font(FS, 23), MUTED, qd * al)
        for k in range(3):
            qq = seg(tl, 1.5 + k * 0.4, 1.75 + k * 0.4)
            if qq > 0:
                _ico5(img, "clock", 760, 976 + dy, 20, accent, qq * al * (0.6 + 0.4 * math.sin(tg * 3 + k)), tg)
    beat_f = (tg % 2.4) / 2.4
    beat = max(0.0, 1.0 - beat_f * 3.0)
    if beat > 0.05 and tl > 1.8:
        _punch_on(img, 760, 1500 + dy, 130, beat * q * al, tg, dur=0.5)
        _pop_txt(img, 760, 1500 + dy, "BUKAN KALAH", font(FB, 38), mix(accent, INK, 0.10), beat * q * al, beat * 1.2)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _stamp_on(img, 540, 1740 + dy, "PERANG BERGELOMBANG", qz * al, qz, col=accent, fsz=48, rot=-5)


def sc_batas(img, d, sc, tl, dur, tg, accent, al, dy):
    """f7: tanda wajib ke dokter + catatan kejang demam umumnya jinak."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    rrect_on(img, 90, 830 + dy, 990, 1620 + dy, 44, mix(accent, WHITE, 0.80), q * al,
             outline=accent, width=5)
    kartu = (("heart", "BAYI DI BAWAH 3 BULAN", "DEMET 38 DERAJAT = LANGSUNG DOKTER"),
             ("flame", "SUHU LEWAT 40 DERAJAT", "SEGERA DIPERIKSA"),
             ("clock", "LEBIH DARI 3 HARI", "PERLU DIPERIKSA JUGA"))
    for k, (ik, judul, sub) in enumerate(kartu):
        qi = esmooth(_dw(tl, dur, 0.10 + k * 0.16, 0.30 + k * 0.16))
        if qi <= 0.01:
            continue
        yy = 1010 + k * 200 + dy
        rrect_on(img, 140, yy - 78, 940, yy + 78, 34, mix(WHITE, accent, 0.14), qi * al,
                 outline=mix(accent, INK, 0.10), width=3)
        _ico5(img, ik, 230, yy, 44, accent, qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 600, yy - 26, judul, font(FB, 36), mix(accent, INK, 0.15), qi * al)
        paste_c(img, 600, yy + 28, sub, font(FS, 26), MUTED, qi * al)

    qs = esmooth(seg(tl, 4.2, 4.8)) * esmooth(seg(dur - tl, 0.1, 0.4))
    if qs > 0:
        _stamp_on(img, 540, 1555 + dy, "KE DOKTER!", qs * al, qs, col=accent, fsz=62, rot=-6)
    qn = esmooth(_dw(tl, dur, 0.60, 0.74))
    if qn > 0:
        _pop_pill(img, 540, 1700 + dy, "KEJANG DEMAM: MENAKUTKAN, UMUMNYA JINAK", 24,
                  mix(accent, INK, 0.08), qn * al, qn)


def sc_rangkuman(img, d, sc, tl, dur, tg, accent, al, dy):
    """f8: papan rangkuman v7 + tokoh senang + konfeti."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _recap_on(img, [("thermo", "Termostat otak sengaja dinaikkan"),
                    ("germ", "Kuman lemas, sel imun makin gesit"),
                    ("moon", "Malam: kortisol turun, sitokin naik"),
                    ("drop", "Keringat = radiator saat menang")], q * al, tg, t0=0.5, dt=0.7, col=accent)
    _papan9_on(img, 250, 930 + dy, 1.0, q * al, tg, ikon="heart", col=mix(accent, INK, 0.25))
    qr = esmooth(seg(tl, 0.9, 1.3))
    if qr > 0:
        _stamp_on(img, 770, 930 + dy, "BUKAN MUSUH!", qr * al, qr, col=accent, fsz=60, rot=-6)
    qc = esmooth(_dw(tl, dur, 0.55, 0.72))
    if qc > 0:
        _confetti_on(img, tg, qc * al, n=26)


VISUALS.update({
    "intro_demam": sc_intro_demam,
    "termostat": sc_termostat,
    "sinyal": sc_sinyal,
    "baktempur": sc_baktempur,
    "gigil": sc_gigil,
    "malam": sc_malam,
    "naiturun": sc_naiturun,
    "batas": sc_batas,
    "rangkuman": sc_rangkuman,
})


def _selftest32():
    """Uji cepat adegan Ep32 sebelum dipakai render."""
    names = ["intro_demam", "termostat", "sinyal", "baktempur", "gigil", "malam",
             "naiturun", "batas", "rangkuman"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "DEMAM NAIK MALAM?"], "accent": "#B03A2E"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep32: 9 adegan OK")


# ====================== MESIN v8: ELEMEN PEMAHAMAN ======================
# Tujuan v8: penonton LEBIH CEPAT Membayangkan apa yang dijelaskan -
# ukuran presisi (_ukur), perbandingan skala (_skala), kartu detail (_detail),
# sebelum/sesudah (_slider), angka besar berhitung (_hitung), proses
# bernomor (_tangga), sorot perhatian (_sorot), dan latar grafik (_kisi).


def _kisi_on(img, x0, y0, x1, y1, alpha, step=60, col=None):
    """Kertas grafik halus: garis kisi + garis tiap 5 langkah lebih tebal
    (latar data yang bikin grafik/skala terasa presisi)."""
    if alpha <= 0.01:
        return
    col = col or mix(BLUE, CREAM, 0.55)
    xx, k = x0, 0
    while xx <= x1 + 0.1:
        line_on(img, (xx, y0), (xx, y1), col, 2 if k % 5 == 0 else 1, alpha * 0.8)
        xx += step
        k += 1
    yy, k = y0, 0
    while yy <= y1 + 0.1:
        line_on(img, (x0, yy), (x1, yy), col, 2 if k % 5 == 0 else 1, alpha * 0.8)
        yy += step
        k += 1


def _ukur_on(img, p1, p2, teks, alpha, tg, t0=0.0, dur=0.7, col=None, fsz=24, off=64.0):
    """Garis ukur dua panah + label pill di tengah: menunjukkan ukuran,
    jarak, atau perbedaan dengan presisi (menggambar dari tengah)."""
    if alpha <= 0.01:
        return
    col = col or mix(BLUE, INK, 0.10)
    q = esmooth(seg(tg, t0, t0 + dur))
    if q <= 0.01:
        return
    (x1, y1), (x2, y2) = p1, p2
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    a = (x1 + nx * off, y1 + ny * off)
    b = (x2 + nx * off, y2 + ny * off)
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    hx, hy = (mx - a[0]) * 0.5 * q, (my - a[1]) * 0.5 * q
    aa = math.atan2(b[1] - a[1], b[0] - a[0])
    for sgn in (-1, 1):
        ex, ey = mx + sgn * hx, my + sgn * hy
        line_on(img, (mx, my), (ex, ey), col, 5, alpha)
        d2 = aa if sgn > 0 else aa + math.pi
        poly_on(img, [(ex + 16 * math.cos(d2), ey + 16 * math.sin(d2)),
                      (ex - 8 * math.cos(d2) + 8 * math.sin(d2), ey - 8 * math.sin(d2) - 8 * math.cos(d2)),
                      (ex - 8 * math.cos(d2) - 8 * math.sin(d2), ey - 8 * math.sin(d2) + 8 * math.cos(d2))],
                col, alpha)
    for (px, py) in (a, b):
        line_on(img, (px - 8 * math.cos(aa + 1.57), py - 8 * math.sin(aa + 1.57)),
                (px + 8 * math.cos(aa + 1.57), py + 8 * math.sin(aa + 1.57)), col, 5, alpha)
    f = font(FS, fsz)
    w = tw(teks, f) + 36
    rrect_on(img, mx - w / 2, my - 24, mx + w / 2, my + 24, 20, mix(col, WHITE, 0.88), alpha)
    paste_c(img, mx, my, teks, f, mix(col, INK, 0.15), alpha)


def _skala_on(img, x0, x1, ybase, item, alpha, tg, t0=0.0, dt=0.35, col=None, hmax=380):
    """Perbandingan skala: batang tinggi bertumbuh berurutan + nilai + label.
    item: [(label, frac 0..1, "NILAI"), ...] - ukuran langsung kebayang."""
    if alpha <= 0.01 or not item:
        return
    col = col or BLUE
    line_on(img, (x0 - 20, ybase), (x1 + 20, ybase), mix(col, INK, 0.20), 5, alpha)
    n = len(item)
    gap = (x1 - x0) / n
    for i, it in enumerate(item):
        lbl, fr, vtxt = it[0], it[1], it[2]
        qi = esmooth(seg(tg, t0 + i * dt, t0 + i * dt + 0.5))
        if qi <= 0.01:
            continue
        cx = x0 + gap * (i + 0.5)
        h = hmax * clamp(fr) * qi
        bw = gap * 0.42
        rrect_on(img, cx - bw / 2, ybase - h, cx + bw / 2, ybase, bw / 2, mix(col, WHITE, 0.35), qi * alpha)
        rrect_on(img, cx - bw / 2, ybase - h, cx + bw / 2, ybase, bw / 2, col, qi * alpha * 0.85)
        paste_c(img, cx, ybase - h - 30, vtxt, font(FB, 27), mix(col, INK, 0.12), qi * alpha)
        paste_c(img, cx, ybase + 30, lbl, font(FS, 23), MUTED, qi * alpha)


def _detail_on(img, px, py, tx, ty, judul, sub, alpha, tg, t0=0.0, col=None, w=330):
    """Kartu detail v8: titik sumber - garis siku menggambar sendiri - kartu
    judul + sub. Lebih informatif daripada pil callout v6 untuk penjelasan."""
    if alpha <= 0.01:
        return
    col = col or mix(BLUE, INK, 0.10)
    q = esmooth(seg(tg, t0, t0 + 0.6))
    if q <= 0.01:
        return
    dot_on(img, px, py, 7, col, alpha * q)
    _ripple_on(img, px, py, 24, col, alpha * q, tg, n=2)
    cor = (tx, ty + 58)
    qx, qy = seg(q, 0.0, 0.5), seg(q, 0.35, 0.8)
    line_on(img, (px, py), (px + (cor[0] - px) * qx, py), col, 4, alpha)
    line_on(img, (cor[0], py), (cor[0], py + (cor[1] - py) * qy), col, 4, alpha)
    qc = esmooth(seg(tg, t0 + 0.3, t0 + 0.7))
    if qc <= 0.01:
        return
    x0, x1, y0, y1 = tx - w / 2, tx + w / 2, ty - 58, ty + 58
    rrect_on(img, x0, y0, x1, y1, 22, mix(col, WHITE, 0.90), qc * alpha, outline=col, width=3)
    paste_c(img, tx, ty - 22, judul, font(FB, 27), mix(col, INK, 0.15), qc * alpha)
    for j, ln in enumerate(wrap(sub, font(FS, 22), w - 44)[:2]):
        paste_c(img, tx, ty + 12 + j * 28, ln, font(FS, 22), MUTED, qc * alpha)


def _slider_on(img, x0, y0, x1, y1, frac, alpha, tg, label_a=None, label_b=None, col=None):
    """Gagang sebelum/sesudah: garis pembagi + gagang bulat dua arah + label.
    Pemanggil menggambar isi kiri (frac<fx) dan kanan (frac>=fx) sendiri."""
    if alpha <= 0.01:
        return
    col = col or mix(BLUE, INK, 0.10)
    fx = x0 + (x1 - x0) * clamp(frac)
    line_on(img, (fx, y0 - 14), (fx, y1 + 14), mix(col, WHITE, 0.90), 8, alpha)
    cyc = (y0 + y1) / 2
    ell(img, fx - 26, cyc - 26, fx + 26, cyc + 26, fill=mix(col, WHITE, 0.92), alpha=alpha,
        outline=col, width=4)
    for sgn in (-1, 1):
        line_on(img, (fx + sgn * 8, cyc), (fx + sgn * 17, cyc), col, 4, alpha)
    if label_a:
        paste_c(img, x0 + 74, y0 + 26, label_a, font(FS, 23), MUTED, alpha)
    if label_b:
        paste_c(img, x1 - 74, y0 + 26, label_b, font(FS, 23), MUTED, alpha)


def _hitung_on(img, cx, cy, nilai_akhir, unit, alpha, tg, t0=0.0, dur=1.2, col=None, fsz=64):
    """Angka besar count-up dengan pemisah ribuan + unit di bawah:
    data besar jadi terasa nyata (contoh: 505.000 KM3 per tahun)."""
    if alpha <= 0.01:
        return
    col = col or mix(BLUE, INK, 0.10)
    q = esmooth(seg(tg, t0, t0 + dur))
    if q <= 0.01:
        return
    val = nilai_akhir * q
    if nilai_akhir >= 1000:
        teks = f"{int(round(val)):,}".replace(",", ".")
    elif float(nilai_akhir).is_integer():
        teks = str(int(round(val)))
    else:
        teks = f"{val:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    sc = 0.9 + 0.1 * eob(q)
    paste_c(img, cx, cy, teks, font(FB, int(fsz * sc)), col, alpha)
    if unit:
        paste_c(img, cx, cy + fsz * 0.72, unit, font(FS, max(20, fsz // 2)), MUTED, alpha)


def _tangga_on(img, pts, alpha, tg, t0=0.0, dt=0.55, col=None, r=26):
    """Jalur langkah bernomor 1->2->3->... : garis menggambar progresif antar
    stasiun bernomor. pts: [(x, y) atau (x, y, "LABEL"), ...] - proses jelas."""
    if alpha <= 0.01 or len(pts) < 2:
        return
    col = col or mix(BLUE, INK, 0.10)
    for i in range(len(pts) - 1):
        qi = esmooth(seg(tg, t0 + i * dt, t0 + i * dt + 0.4))
        if qi <= 0.01:
            continue
        (x1, y1), (x2, y2) = pts[i][:2], pts[i + 1][:2]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        line_on(img, (x1, y1), (mx + (x2 - mx) * qi, my + (y2 - my) * qi), col, 5, alpha * 0.85)
    for i, p in enumerate(pts):
        qi = esmooth(seg(tg, t0 + i * dt, t0 + i * dt + 0.35))
        if qi <= 0.01:
            continue
        cx, cy = p[0], p[1]
        ell(img, cx - r, cy - r, cx + r, cy + r, fill=mix(col, WHITE, 0.88), alpha=qi * alpha,
            outline=col, width=4)
        paste_c(img, cx, cy, str(i + 1), font(FB, 26), mix(col, INK, 0.15), qi * alpha)
        if len(p) > 2:
            paste_c(img, cx, cy + r + 24, p[2], font(FS, 22), MUTED, qi * alpha)


def _sorot_on(img, cx, cy, rr, alpha, tg, t0=0.0, dur=0.8, gelap=0.60):
    """Sorot: cincin gelap mengelilingi target + kilau lembut di dalamnya -
    perhatian penonton langsung ke titik yang dimaksud. Sengaja TIDAK
    menggelapkan seluruh layar: kamera/ambient memangkas ~55px tepi, jadi
    bidang gelap penuh-layar membuat margin krem hilang (QC tinta gagal)."""
    if alpha <= 0.01:
        return
    from PIL import ImageFilter
    q = esmooth(seg(tg, t0, t0 + dur))
    if q <= 0.01:
        return
    A = int(255 * gelap * q * clamp(alpha))
    if A <= 2:
        return
    band = 250                                  # lebar cincin gelap (design px)
    m = Image.new("L", (int(W * SS), int(H * SS)), 0)
    dd = ImageDraw.Draw(m)
    dd.ellipse([S(cx - rr - band), S(cy - rr - band), S(cx + rr + band), S(cy + rr + band)], fill=A)
    dd.ellipse([S(cx - rr * 0.96), S(cy - rr * 0.96), S(cx + rr * 0.96), S(cy + rr * 0.96)], fill=0)
    m = m.filter(ImageFilter.GaussianBlur(S(9)))
    lay = Image.new("RGBA", m.size, (18, 20, 30, 0))
    lay.putalpha(m)
    img.paste(lay.convert("RGB"), (0, 0), lay.getchannel("A"))
    ring_on(img, cx, cy, rr + 10, mix(WHITE, CREAM, 0.30), 5, clamp(alpha) * q * (0.75 + 0.25 * math.sin(tg * 3)))


def _selftest_v8():
    """Uji cepat seluruh paket v8."""
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    _kisi_on(img, 120, 900, 960, 1560, 1.0, step=60)
    _ukur_on(img, (200, 980), (880, 980), "JARAK 60 CM", 1.0, 1.2, t0=0.0)
    _skala_on(img, 220, 860, 1500, [("BUTIRAN", 0.06, "0,02"), ("TETES", 1.0, "2,0")], 1.0, 1.4, t0=0.2)
    _detail_on(img, 300, 700, 700, 560, "SERPIHAN DEBU", "tempat uap air menempel", 1.0, 1.6, t0=0.0)
    _slider_on(img, 150, 1200, 930, 1500, 0.4 + 0.2 * math.sin(1.0), 1.0, 1.0, "TIPIS", "TEBAL")
    _hitung_on(img, 540, 300, 505000, "KM KUBIK / TAHUN", 1.0, 1.0, t0=0.0)
    _tangga_on(img, [(180, 1100, "MENGEMBUN"), (450, 1250), (720, 1100), (900, 1250, "JATUH")], 1.0, 1.2, t0=0.0)
    _sorot_on(img, 540, 700, 170, 0.8, 1.8, t0=0.0, gelap=0.45)
    print("selftest v8: kisi + ukur + skala + detail + slider + hitung + tangga + sorot OK")


# ====================== Ep33: Kenapa Hujan Bisa Turun? ======================

HUJAN32 = (46, 110, 140)                    # biru hujan (sama nuansa mata)
ABU32 = (108, 116, 128)                     # awan gelap


def _awan33(img, cx, cy, s, col, alpha, tg=0.0, gelap=0.0):
    """Awan dari gugus butiran: deretan lingkaran lembut bergoyang pelan."""
    if alpha <= 0.01:
        return
    base = mix(WHITE, ABU32, gelap)
    for k, (dx, dy2, rr) in enumerate(((-1.5, 0.10, 0.52), (-0.7, -0.18, 0.72), (0.2, -0.30, 0.86),
                                       (1.1, -0.10, 0.68), (1.8, 0.12, 0.46))):
        wob = 1.0 + 0.03 * math.sin(tg * 1.6 + k * 1.3)
        ell(img, cx + dx * s * rr - rr * s * wob, cy + dy2 * s - rr * s * wob,
            cx + dx * s * rr + rr * s * wob, cy + dy2 * s + rr * s * wob,
            fill=mix(base, WHITE, 0.12 + 0.10 * math.sin(tg * 1.2 + k)), alpha=alpha)


def _hujan33(img, x0, y0, x1, y1, alpha, tg, n=26, col=None, miring=0.10):
    """Garis-garis hujan jatuh (loop) + percikan kecil di bawah."""
    if alpha <= 0.01:
        return
    col = col or mix(HUJAN32, WHITE, 0.25)
    for k in range(n):
        ph = ((tg * (0.55 + 0.10 * (k % 3)) + k * 0.173) % 1.0)
        xx = x0 + ((k * 137) % max(1, int(x1 - x0)))
        yy = y0 + (y1 - y0) * ph
        ln = 26 + 14 * (k % 2)
        line_on(img, (xx, yy), (xx + ln * miring, yy + ln), col, 3, alpha * 0.85)
        if ph > 0.96:
            _ripple_on(img, xx, y1, 10, col, alpha * (1 - ph) * 4, tg, n=1)


def _tetes33(img, cx, cy, r, col, alpha, tg=0.0, rata=0.0):
    """Tetes air: rata 0 = butiran bulat kecil; rata 1 = kubah hujan (bawah rata)."""
    if alpha <= 0.01:
        return
    if rata <= 0.05:
        ell(img, cx - r, cy - r, cx + r, cy + r, fill=mix(col, WHITE, 0.55), alpha=alpha,
            outline=col, width=3)
        return
    ry = r * (1.0 + 0.25 * rata)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.pieslice([S(cx - r), S(cy - ry), S(cx + r), S(cy + ry)], 180, 360,
                fill=mix(col, WHITE, 0.55) + (255,), outline=col + (255,), width=max(2, int(S(3))))
    dd.rounded_rectangle([S(cx - r), S(cy - r * 0.05), S(cx + r), S(cy + r * 0.55)],
                         radius=S(r * 0.3), fill=mix(col, WHITE, 0.55) + (255,))
    dd.arc([S(cx - r), S(cy - ry), S(cx + r), S(cy + ry)], 0, 180, fill=col + (255,),
           width=max(2, int(S(3))))
    _put(img, lay, alpha)


def sc_intro_hujan(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: jendela hujan malam, tokoh bawah payung, pertanyaan besar."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    q1 = seg(tl, 0.55, 1.0)
    if q1 > 0:
        _pop_pill(img, 540, 700 + dy, "DARI MANA AIRNYA?", 26, mix(accent, INK, 0.10), q1 * al, q1)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    pang = mix(CREAM, mix(accent, INK, 0.30), 0.24)
    rrect_on(img, 104, 776 + dy, 976, 1596 + dy, 46, pang, q2 * al)
    _langit7(img, 118, 790 + dy, 962, 1582 + dy, q2 * al * 0.9, tg, mood="malam", sun=(860, 920))
    _hujan33(img, 140, 860 + dy, 940, 1540 + dy, q2 * al, tg, n=30)
    _awan33(img, 540, 900 + dy, 130, mix(WHITE, INK, 0.25), q2 * al, tg, gelap=0.55)
    _papan9_on(img, 300, 1400 + dy, 1.05, q2 * al, tg, ikon="drop", col=mix(accent, INK, 0.25))
    poly_on(img, [(300 - 96, 1332 + dy), (300 + 96, 1332 + dy), (300, 1242 + dy)],
            mix(WHITE, accent, 0.35), q2 * al, outline=mix(accent, INK, 0.20), width=6)
    line_on(img, (300, 1244 + dy), (300, 1318 + dy), mix(accent, INK, 0.20), 6, q2 * al)
    _lower3_on(img, "SI KAMU", q2 * al * seg(tl, 1.6, 2.0), tl, col=mix(accent, INK, 0.30), y=1560)
    _lbl(img, 660, 1400 + dy, "TETES YANG SAMA", font(FS, 24), mix(pang, INK, 0.10), q2 * al)
    _lbl(img, 660, 1440 + dy, "DENGAN KEMARIN", font(FS, 24), mix(pang, INK, 0.10), q2 * al)
    q4 = seg(tl, 2.6, 3.2)
    if q4 > 0:
        _pop_pill(img, 540, 1660 + dy, "SIKLUS AIR - INI SAINS", 24, mix(accent, INK, 0.10), q4 * al, q4)


def sc_uap(img, d, sc, tl, dur, tg, accent, al, dy):
    """f1: laut + matahari, partikel uap naik (flowpath), counter 505.000 km3."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _langit7(img, 110, 830 + dy, 970, 1240 + dy, q * al, tg, mood="pagi", sun=(240, 950 + dy))
    _cutaway_on(img, 110, 1240 + dy, 970, 1420 + dy, 0.62, HUJAN32, q * al, tg, bubbles=True)
    _lbl(img, 540, 1452 + dy, "LAUT", font(FS, 24), mix(accent, INK, 0.10), q * al)
    _flowpath_on(img, [(260, 1360 + dy), (300, 1150 + dy), (420, 980 + dy), (560, 880 + dy)],
                 mix(accent, INK, 0.10), q * al, tg, n=6, speed=0.16, size=6.0)
    _flowpath_on(img, [(700, 1370 + dy), (720, 1160 + dy), (680, 1000 + dy), (620, 900 + dy)],
                 mix(accent, INK, 0.10), q * al, tg + 0.5, n=5, speed=0.14, size=5.0)
    _lbl(img, 540, 848 + dy, "UAP AIR NAIK", font(FS, 25), mix(accent, INK, 0.12), q * al)
    qh = esmooth(seg(tl, 0.9, 1.2))
    if qh > 0:
        rrect_on(img, 130, 1480 + dy, 950, 1680 + dy, 34, mix(WHITE, accent, 0.10), qh * al,
                 outline=mix(accent, INK, 0.12), width=4)
        _hitung_on(img, 400, 1530 + dy, 505000, "", qh * al, tg, t0=0.1, fsz=56, col=accent)
        _lbl(img, 400, 1636 + dy, "KM KUBIK / TAHUN MENGUAP", font(FS, 22), MUTED, qh * al)
        _pop_pill(img, 790, 1596 + dy, "AIR LAUT + SUNGAI + TANAH", 20, mix(accent, INK, 0.08), qh * al, qh)


def sc_embun(img, d, sc, tl, dur, tg, accent, al, dy):
    """f2: kolom udara makin tinggi makin dingin (ukur) + callout debu + awan lahir."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kisi_on(img, 360, 830 + dy, 700, 1620 + dy, q * al * 0.5, step=66, col=mix(accent, CREAM, 0.45))
    _ukur_on(img, (530, 880 + dy), (530, 1580 + dy), "6,5 DERAJAT / KM", q * al, tg, t0=0.5,
             col=DINGIN32, fsz=24, off=-74)
    _flowpath_on(img, [(420, 1580 + dy), (450, 1350 + dy), (480, 1120 + dy), (500, 950 + dy)],
                 mix(accent, INK, 0.10), q * al, tg, n=5, speed=0.15, size=6.0)
    _lbl(img, 240, 1590 + dy, "HANGAT (BAWAH)", font(FS, 22), MUTED, q * al)
    _lbl(img, 240, 900 + dy, "DINGIN (ATAS)", font(FS, 22), DINGIN32, q * al)
    dot_on(img, 500, 1010 + dy, 6, mix(accent, INK, 0.25), q * al)
    _detail_on(img, 500, 1010 + dy, 830, 1060 + dy, "SERPIHAN DEBU", "tempat uap menempel & mengembun",
               q * al * seg(tl, 1.0, 1.4), tg, col=accent)
    qa = esmooth(seg(tl, 2.0, 2.5))
    if qa > 0:
        _awan33(img, 300, 900 + dy, 120, WHITE, qa * al, tg, gelap=0.0)
        _awan33(img, 760, 880 + dy, 90, WHITE, qa * al, tg + 2, gelap=0.15)
        _pop_pill(img, 300, 1020 + dy, "AWAN LAHIR", 26, mix(accent, INK, 0.10), qa * al, qa)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _pill_c(img, 540, 1690 + dy, "KONDENSASI: UAP JADI BUTIRAN", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_putihgelap(img, d, sc, tl, dur, tg, accent, al, dy):
    """f3: slider tipis(putih) vs tebal(gelap) - gagang bergerak, awan dua sisi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    x0, x1c, y0, y1 = 130, 950, 900 + dy, 1520 + dy
    fx = x0 + (x1c - x0) * (0.5 + 0.16 * math.sin(tg * 0.9))
    rrect_on(img, x0, y0, x1c, y1, 40, mix(WHITE, accent, 0.10), q * al, outline=mix(accent, INK, 0.12), width=4)
    lay = _layer(img)
    dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([S(int(fx)), S(y0 + 6), S(x1c - 6), S(y1 - 6)], radius=S(34),
                         fill=mix(mix(WHITE, INK, 0.35), CREAM, 0.10) + (255,))
    _put(img, lay, q * al)
    _awan33(img, (x0 + min(fx, x1c - 80)) / 2 + 40, y0 + 330, 150, WHITE, q * al, tg, gelap=0.0)
    _awan33(img, min(fx + 190, x1c - 150), y0 + 300, 170, WHITE, q * al, tg + 3, gelap=0.62)
    _awan33(img, min(fx + 150, x1c - 260), y0 + 470, 120, WHITE, q * al, tg + 5, gelap=0.70)
    for k in range(3):
        _hujan33(img, fx + 60, y0 + 520, fx + 260, y1 - 20, q * al * seg(tl, 1.6, 2.0), tg + k * 0.3,
                 n=5, col=mix(ABU32, INK, 0.10))
    _slider_on(img, x0, y0, x1c, y1, (fx - x0) / (x1c - x0), q * al, tg, col=accent)
    paste_c(img, x0 + 150, y0 + 30, "TIPIS: PUTIH", font(FS, 23), MUTED, q * al)
    paste_c(img, x1c - 150, y0 + 30, "TEBAL: GELAP", font(FS, 23), ABU32, q * al)
    qs = esmooth(seg(tl, 0.8, 1.2))
    if qs > 0:
        _lbl(img, (x0 + fx) / 2, y1 + 52, "SEMUA WARNA DIPANTUL", font(FS, 23), MUTED, qs * al * (1 if fx > x0 + 350 else 0))
        _lbl(img, (fx + x1c) / 2, y1 + 52, "CAHAYA TERSANGKUT", font(FS, 23), ABU32, qs * al * (1 if fx < x1c - 350 else 0))
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _pill_c(img, 540, 1700 + dy, "AWAN GELAP = TANDA HUJAN DEKAT", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_gabung(img, d, sc, tl, dur, tg, accent, al, dy):
    """f4: butiran bertabrakan bergabung membesar + tangga proses 4 langkah."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    ph = (tg * 0.35) % 1.0
    n = 3 + int(ph * 5)
    for k in range(n):
        aa = k / 6.0 * 6.283 + tg * 0.4
        rr = 12 + 26 * ph
        _tetes33(img, 300 + 90 * math.cos(aa) * (1 - ph * 0.6), 1060 + dy + 60 * math.sin(aa) * (1 - ph * 0.6),
                 max(6, 26 * (1 - ph) + 6), HUJAN32, q * al * (1.0 - ph * 0.9), tg)
    _tetes33(img, 300, 1060 + dy, 22 + 44 * ph, HUJAN32, q * al, tg, rata=0.0 if ph < 0.7 else 0.5)
    _lbl(img, 300, 920 + dy, "BERGABUNG = MEMBESAR", font(FS, 25), mix(accent, INK, 0.12), q * al)
    qa = esmooth(seg(tl, 0.9, 1.3))
    if qa > 0:
        _detail_on(img, 300, 1060 + dy, 640, 1000 + dy, "SEJUTA KALI", "lebih besar dari butiran awal",
                   qa * al, tg, col=accent, w=300)
    _tangga_on(img, [(170, 1360 + dy, "MENGEMBUN"), (400, 1480 + dy, "BERGABUNG"),
                     (650, 1360 + dy, "KEBERATAN"), (880, 1480 + dy, "JATUH")], q * al, tg, t0=1.6, dt=0.5)
    beat_f = (tg % 2.0) / 2.0
    beat = max(0.0, 1.0 - beat_f * 3.0)
    if beat > 0.05 and tl > 3.0:
        _pop_txt(img, 880, 1330 + dy, "JATUH!", font(FB, 40), accent, q * al * beat, beat * 1.2)


def sc_skala(img, d, sc, tl, dur, tg, accent, al, dy):
    """f5: latar kisi + perbandingan skala butiran vs tetes + ukur 100x."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kisi_on(img, 120, 900 + dy, 960, 1520 + dy, q * al * 0.55, step=62, col=mix(accent, CREAM, 0.40))
    _skala_on(img, 240, 840, 1460 + dy, [("BUTIRAN AWAN", 0.08, "0,02 MM"), ("TETES HUJAN", 1.0, "2 MM")],
              q * al, tg, t0=0.4, col=HUJAN32, hmax=300)
    _pop_pill(img, 400, 985 + dy, "TETES = 100X BUTIRAN", 24, mix(accent, INK, 0.10),
              q * al * seg(tl, 1.6, 2.0), 1.0)
    _tetes33(img, 330, 1030 + dy, 7, HUJAN32, q * al, tg)
    _tetes33(img, 700, 1030 + dy, 60, HUJAN32, q * al, tg, rata=0.85)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _stamp_on(img, 540, 1660 + dy, "GRAVITASI MENANG", qz * al, qz, col=accent, fsz=54, rot=-5)


def sc_bentuk(img, d, sc, tl, dur, tg, accent, al, dy):
    """f6: sorot tetes - bentuk kubah bukan air mata - tekanan udara + kecepatan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    cx, cy = 540, 1130 + dy
    f_fade = 1.0 - seg(tl, dur - 2.4, dur - 1.6)
    _sorot_on(img, cx, cy, 230, q * al * seg(tl, 0.5, 1.1), tg, t0=0.6, gelap=0.52 * f_fade)
    _tetes33(img, cx, cy, 130, HUJAN32, q * al, tg, rata=1.0)
    for k, sgn in ((0, -1), (1, 1)):
        _scribble_on(img, cx, cy, 0, q * al, tg, t0=1.6 + 0.3 * k, kind="arrow",
                     p2=(cx + sgn * 200, cy + 120), col=mix(AMBER32, INK, 0.05), width=6)
    _pop_pill(img, cx, cy + 205, "TEKANAN UDARA MENEKAN BAWAH SAMPAI RATA", 23,
              mix(WHITE, accent, 0.10), q * al * seg(tl, 2.0, 2.4), 1.0)
    _lbl(img, cx, cy - 215, "BUKAN AIR MATA", font(FB, 40), mix(accent, INK, 0.05), q * al * seg(tl, 1.2, 1.6))
    _ukur_on(img, (850, cy - 90), (850, cy + 90), "S.D. 9 M/DETIK", q * al * seg(tl, 2.6, 3.0),
             tg, t0=2.8, col=accent, fsz=22, off=58)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _pop_pill(img, 540, 1690 + dy, "KUBAH KECIL YANG JATUH CEPAT", 25, mix(accent, INK, 0.10), qz * al, qz)


def sc_siklus(img, d, sc, tl, dur, tg, accent, al, dy):
    """f7: lingkaran siklus 4 stasiun + aliran partikel muter + fakta dinosaurus."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    cx, cy, R = 540, 1170 + dy, 300
    _flowpath_on(img, [(cx, cy - R), (cx + R, cy), (cx, cy + R), (cx - R, cy), (cx, cy - R)],
                 mix(accent, INK, 0.10), q * al, tg, n=8, speed=0.13, size=6.0)
    stasiun = ((cx, cy - R, "UAP NAIK"), (cx + R, cy, "AWAN"), (cx, cy + R, "HUJAN"), (cx - R, cy, "LAUT"))
    for i, (sx, sy, lab) in enumerate(stasiun):
        qi = esmooth(seg(tg, 0.4 + i * 0.35, 0.7 + i * 0.35))
        if qi <= 0.01:
            continue
        ell(img, sx - 24, sy - 24, sx + 24, sy + 24, fill=mix(WHITE, accent, 0.12), alpha=qi * q * al,
            outline=accent, width=4)
        paste_c(img, sx, sy, str(i + 1), font(FB, 24), mix(accent, INK, 0.15), qi * q * al)
        _lbl(img, sx, sy + 52, lab, font(FS, 23), mix(accent, INK, 0.12), qi * q * al)
    _awan33(img, cx + R, cy - 40, 70, WHITE, q * al, tg, gelap=0.1)
    _hujan33(img, cx + R - 60, cy + 70, cx + R + 60, cy + 150, q * al, tg, n=4, miring=0.0)
    qa = esmooth(seg(tl, 1.8, 2.2))
    _papan9_on(img, cx, cy + 60, 0.8, qa * al, tg, ikon="drop", col=accent)


def sc_rangkuman33(img, d, sc, tl, dur, tg, accent, al, dy):
    """f8: papan rangkuman + tokoh senang + konfeti + awan hias."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _recap_on(img, [("drop", "Matahari menguapkan air jadi uap"),
                    ("thermo", "Dingin di atas: uap jadi awan"),
                    ("germ", "Butiran bergabung jadi tetes"),
                    ("bolt", "Tetes berat jatuh: hujan!")], q * al, tg, t0=0.5, dt=0.7, col=accent)
    _papan9_on(img, 250, 930 + dy, 1.0, q * al, tg, ikon="heart", col=mix(accent, INK, 0.25))
    _awan33(img, 800, 900 + dy, 90, WHITE, q * al, tg, gelap=0.15)
    qr = esmooth(seg(tl, 0.9, 1.3))
    if qr > 0:
        _stamp_on(img, 800, 1060 + dy, "GANTI TEMPAT", qr * al, qr, col=accent, fsz=50, rot=-6)
    qc = esmooth(_dw(tl, dur, 0.55, 0.72))
    if qc > 0:
        _confetti_on(img, tg, qc * al, n=24)


VISUALS.update({
    "intro_hujan": sc_intro_hujan,
    "uap": sc_uap,
    "embun": sc_embun,
    "putihgelap": sc_putihgelap,
    "gabung": sc_gabung,
    "skala": sc_skala,
    "bentuk": sc_bentuk,
    "siklus": sc_siklus,
    "rangkuman": sc_rangkuman33,
})


def _selftest33():
    """Uji cepat adegan Ep33 sebelum dipakai render."""
    names = ["intro_hujan", "uap", "embun", "putihgelap", "gabung", "skala", "bentuk",
             "siklus", "rangkuman"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "HUJAN BISA TURUN?"], "accent": "#2E6E8C"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep33: 9 adegan OK")


# ====================== Ep34: Kenapa Mimisan? ======================


def _selaput34(img, cx, cy, w2, h2, alpha, tg, merah=0.0):
    """Selaput mukosa: bidang muda yang memerah sedikit bila iritasi."""
    if alpha <= 0.01:
        return
    base = mix(mix((252, 226, 214), (238, 148, 128), merah), WHITE, 0.10)
    rrect_on(img, cx - w2 / 2, cy - h2 / 2, cx + w2 / 2, cy + h2 / 2, 26, base, alpha,
             outline=mix((176, 58, 46), INK, 0.10), width=3)
    for k in range(4):
        xx = cx - w2 / 2 + w2 * (0.16 + 0.22 * k)
        line_on(img, (xx, cy - h2 * 0.30), (xx + 10, cy + h2 * 0.30),
                mix((238, 148, 128), WHITE, 0.35), 3, alpha * 0.7)


def sc_intro_mimisan(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: kamar pagi, tokoh kaget, tetes kecil dari hidung."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    q1 = seg(tl, 0.55, 1.0)
    if q1 > 0:
        _pop_pill(img, 540, 700 + dy, "HAMPIR SELALU JINAK", 26, mix(accent, INK, 0.10), q1 * al, q1)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    pang = mix(CREAM, mix(accent, INK, 0.30), 0.24)
    rrect_on(img, 104, 776 + dy, 976, 1596 + dy, 46, pang, q2 * al)
    _langit7(img, 118, 790 + dy, 962, 1582 + dy, q2 * al * 0.85, tg, mood="pagi", sun=(840, 950))
    _papan9_on(img, 360, 1290 + dy, 1.1, q2 * al, tg, ikon="drop", col=mix(accent, INK, 0.25))
    _lower3_on(img, "SI KAMU", q2 * al * seg(tl, 1.6, 2.0), tl, col=mix(accent, INK, 0.30), y=1560)
    beat_f = (tg % 1.9) / 1.9
    beat = max(0.0, 1.0 - beat_f * 3.0)
    if beat > 0.05:
        _ico5(img, "drop", 434, 1128 + dy, 15, RED, q2 * al * beat, tg)
        _ripple_on(img, 434, 1180 + dy, 12, mix(accent, INK, 0.15), q2 * al * beat * 0.8, tg, n=1)
    _lbl(img, 700, 1120 + dy, "TENANG DULU", font(FS, 26), mix(pang, INK, 0.10), q2 * al)
    _lbl(img, 700, 1162 + dy, "INI SAINS", font(FB, 32), accent, q2 * al)
    q4 = seg(tl, 2.6, 3.2)
    if q4 > 0:
        _pop_pill(img, 540, 1660 + dy, "TITIK RAPUH - INI SAINS", 24, mix(accent, INK, 0.10), q4 * al, q4)


def sc_anatomi(img, d, sc, tl, dur, tg, accent, al, dy):
    """f1: lubang hidung melintang, sorot titik Kiesselbach, 4 pembuluh bertemu."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _cutaway_on(img, 170, 900 + dy, 910, 1380 + dy, 0.22, mix(accent, INK, 0.10), q * al, tg,
                bubbles=False)
    _selaput34(img, 540, 1140 + dy, 700, 430, q * al * 0.85, tg, merah=0.15)
    line_on(img, (540, 910 + dy), (540, 1370 + dy), mix(accent, INK, 0.10), 14, q * al)
    _lbl(img, 330, 935 + dy, "LUBANG KIRI", font(FS, 22), MUTED, q * al)
    _lbl(img, 750, 935 + dy, "LUBANG KANAN", font(FS, 22), MUTED, q * al)
    kx, ky = 540, 1250 + dy
    for aa in (2.2, 2.9, 0.4, 1.1):
        sx = kx + 300 * math.cos(aa)
        sy2 = ky + 200 * math.sin(aa)
        _flowpath_on(img, [(sx, sy2), (kx + 110 * math.cos(aa), ky + 90 * math.sin(aa)), (kx, ky)],
                     mix(accent, INK, 0.10), q * al * seg(tl, 0.8, 1.2), tg, n=4, speed=0.2, size=5.0)
    f_fade = 1.0 - seg(tl, dur - 2.4, dur - 1.6)
    _sorot_on(img, kx, ky, 130, q * al * seg(tl, 0.5, 1.1), tg, t0=0.6, gelap=0.45 * f_fade)
    dot_on(img, kx, ky, 12, RED, q * al)
    _detail_on(img, kx, ky, 810, 1010 + dy, "PLEKSUS KIESSELBACH",
               "4 pembuluh bertemu, selaput paling tipis", q * al * seg(tl, 1.2, 1.6), tg, col=accent, w=330)
    _lbl(img, 230, 1490 + dy, "SEPTUM (DINDING TENGAH)", font(FS, 22), MUTED, q * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _stamp_on(img, 300, 1600 + dy, "9 DARI 10 MIMISAN", qz * al, qz, col=accent, fsz=46, rot=-6)


def sc_penyebab(img, d, sc, tl, dur, tg, accent, al, dy):
    """f2: empat pemicu sehari-hari dengan meter."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    col = mix(accent, INK, 0.12)
    cards = [(300, 1040, "UDARA KERING", 0.80, "thermo"),
             (780, 1040, "MENCOLEK HIDUNG", 0.88, "drop"),
             (300, 1430, "FLU / ALERGI", 0.68, "germ"),
             (780, 1430, "BERSIN TERLALU KERAS", 0.62, "bolt")]
    for i, (cx, cy, txt, frac, ik) in enumerate(cards):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.10, 0.24 + i * 0.10))
        if qi <= 0.01:
            continue
        rrect_on(img, cx - 190, cy - 190, cx + 190, cy + 150, 34, mix(WHITE, accent, 0.14), qi * al,
                 outline=mix(accent, INK, 0.10), width=4)
        _ico5(img, ik, cx, cy - 105, 40, col, qi * al, tg, pulse=0.4 + 0.3 * math.sin(tg * 3 + i))
        fq = qi * frac
        _meter_on(img, cx, cy + 35, 80, fq, mix(accent, INK, 0.06), qi * al)
        _pop_pill(img, cx, cy + 92, txt, 21, mix(accent, INK, 0.08), qi * al, qi * 1.3)
    qn = esmooth(_dw(tl, dur, 0.50, 0.62))
    if qn > 0:
        _pop_pill(img, 540, 1660 + dy, "ANAK PALING SERING: SELAPUT TIPIS + JARI LINCAH", 24,
                  mix(accent, INK, 0.10), qn * al, qn)


def sc_tengadah(img, d, sc, tl, dur, tg, accent, al, dy):
    """f3: gagang mitos - tengadah (salah) vs tunduk (benar)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    x0, x1c, y0, y1 = 130, 950, 900 + dy, 1500 + dy
    rrect_on(img, x0, y0, x1c, y1, 40, mix(WHITE, accent, 0.10), q * al,
             outline=mix(accent, INK, 0.12), width=4)
    _slider_on(img, x0, y0, x1c, y1, 0.5 + 0.14 * math.sin(tg * 1.1), q * al, tg, col=accent)
    paste_c(img, x0 + 150, y0 + 30, "TENGADAH: SALAH", font(FS, 23), mix(accent, INK, 0.15), q * al)
    paste_c(img, x1c - 150, y0 + 30, "TUNDUK: BENAR", font(FS, 23), mix(GREEN, INK, 0.10), q * al)
    _papan9_on(img, x0 + 200, y0 + 360, 0.9, q * al, tg, ikon="bolt", col=mix(accent, INK, 0.20))
    _scribble_on(img, x0 + 200, y0 + 430, 0, q * al, tg, t0=1.0, kind="arrow",
                 p2=(x0 + 210, y0 + 560), col=mix(accent, INK, 0.15), width=6)
    _lbl(img, x0 + 200, y0 + 520, "DARAH MASUK TENGGOROKAN", font(FS, 21), mix(accent, INK, 0.10), q * al)
    _lbl(img, x0 + 200, y0 + 552, "MUAL, MUNTAH, TAK BERHENTI", font(FS, 21), MUTED, q * al)
    _papan9_on(img, x1c - 200, y0 + 360, 0.9, q * al, tg, ikon="shield", col=GREEN)
    _ico5(img, "drop", x1c - 176, y0 + 470, 12, RED, q * al, tg)
    _lbl(img, x1c - 200, y0 + 520, "DARAH KELUAR, AMAN", font(FS, 21), mix(GREEN, INK, 0.10), q * al)
    _lbl(img, x1c - 200, y0 + 552, "MUDAH DIKENDALIKAN", font(FS, 21), MUTED, q * al)
    qs = esmooth(seg(tl, 1.6, 2.2))
    if qs > 0:
        _stamp_on(img, 540, 1600 + dy, "MITOS!", qs * al, qs, col=accent, fsz=72, rot=-8)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _pill_c(img, 540, 1700 + dy, "POSISI MENENTUKAN ARAH DARAH", font(FS, 28),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_carabenar(img, d, sc, tl, dur, tg, accent, al, dy):
    """f4: tangga 4 langkah + ukur 10 menit + tokoh tunduk."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _papan9_on(img, 250, 1100 + dy, 1.0, q * al, tg, ikon="clock", col=mix(accent, INK, 0.20))
    dot_on(img, 292, 998 + dy, 8, RED, q * al)
    _lbl(img, 250, 1295 + dy, "KEPALA CONDONG KE DEPAN", font(FS, 22), mix(accent, INK, 0.10), q * al)
    _tangga_on(img, [(560, 1310 + dy, "DUDUK"), (680, 1180 + dy, "CONDONG"),
                     (800, 1310 + dy, "CUBIT LUNAK"), (900, 1150 + dy, "NAPAS MULUT")],
               q * al, tg, t0=0.6, dt=0.5)
    qp = esmooth(_dw(tl, dur, 0.42, 0.56))
    if qp > 0:
        _ico5(img, "clock", 185, 1510 + dy, 30, accent, qp * al * (0.6 + 0.4 * math.sin(tg * 2.5)), tg)
        _pop_pill(img, 570, 1510 + dy, "CUBIT 10 MENIT PENUH - JANGAN DILEPAS", 26,
                  mix(accent, INK, 0.10), qp * al, qp)
    qk = esmooth(_dw(tl, dur, 0.56, 0.68))
    if qk > 0:
        _ico5(img, "drop", 230, 1620 + dy, 22, DATA, qk * al, tg)
        _pop_pill(img, 570, 1620 + dy, "KOMPRES DINGIN: PEMBULUH MENGECIL", 23,
                  mix(accent, INK, 0.06), qk * al, qk)


def sc_angka(img, d, sc, tl, dur, tg, accent, al, dy):
    """f5: kisi data + skala depan vs belakang + hitung besar."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kisi_on(img, 120, 880 + dy, 960, 1520 + dy, q * al * 0.55, step=62, col=mix(accent, CREAM, 0.40))
    _skala_on(img, 240, 840, 1440 + dy, [("DARI TITIK DEPAN", 0.9, "9 DARI 10"),
                                         ("BELAKANG (LANGKA)", 0.1, "1 DARI 10")],
              q * al, tg, t0=0.4, col=accent, hmax=280)
    _hitung_on(img, 540, 960 + dy, 90, "PERSEN MIMISAN BIASA (JINAK)", q * al, tg, t0=1.6,
               fsz=64, col=accent)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _pill_c(img, 540, 1620 + dy, "CUBITAN BENAR + HIDUNG LEMBAP = BERHENTI", font(FS, 27),
                mix(accent, INK, 0.10), qz * al, dot=True)


def sc_cegah(img, d, sc, tl, dur, tg, accent, al, dy):
    """f6: tiga kebiasaan pencegah + satu musuh."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    col = mix(accent, INK, 0.10)
    kartu = (("drop", "LUMASI: VASELIN TIPIS", "sebelum tidur"),
             ("thermo", "JAGA LEMBAP KAMAR", "AC jangan terlalu kering"),
             ("shield", "KUKU ANAK PENDEK", "colek = musuh utama"))
    for k, (ik, judul, sub) in enumerate(kartu):
        qi = esmooth(_dw(tl, dur, 0.08 + k * 0.14, 0.28 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 960 + k * 200 + dy
        rrect_on(img, 140, yy - 78, 800, yy + 78, 34, mix(WHITE, accent, 0.12), qi * al,
                 outline=mix(accent, INK, 0.10), width=4)
        _ico5(img, ik, 240, yy, 42, GREEN, qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 540, yy - 22, judul, font(FB, 34), mix(accent, INK, 0.15), qi * al)
        paste_c(img, 540, yy + 26, sub, font(FS, 24), MUTED, qi * al)
    qa = esmooth(seg(tl, 1.8, 2.2))
    if qa > 0:
        _ico5(img, "germ", 880, 960 + dy, 34, RED, qa * al, tg)
        _scribble_on(img, 880, 1080 + dy, 0, qa * al, tg, t0=2.0, kind="arrow",
                     p2=(880, 1200 + dy), col=accent, width=6)
        _pop_pill(img, 880, 1260 + dy, "JANGAN!", 30, mix(RED, WHITE, 0.75), qa * al, qa)


def sc_batas34(img, d, sc, tl, dur, tg, accent, al, dy):
    """f7: tanda wajib dokter."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    rrect_on(img, 90, 830 + dy, 990, 1560 + dy, 44, mix(accent, WHITE, 0.80), q * al,
             outline=accent, width=5)
    kartu = (("clock", "CUBIT 2 X 10 MENIT", "masih mengalir = periksa"),
             ("heart", "DARAH BANYAK + PUSING LEMAS", "jangan tunggu"),
             ("bolt", "SETELAH BENTURAN KEPALA", "langsung ke IGD"))
    for k, (ik, judul, sub) in enumerate(kartu):
        qi = esmooth(_dw(tl, dur, 0.10 + k * 0.14, 0.28 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 990 + k * 180 + dy
        rrect_on(img, 140, yy - 70, 940, yy + 70, 32, mix(WHITE, accent, 0.14), qi * al,
                 outline=mix(accent, INK, 0.10), width=3)
        _ico5(img, ik, 230, yy, 40, accent, qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 600, yy - 22, judul, font(FB, 33), mix(accent, INK, 0.15), qi * al)
        paste_c(img, 600, yy + 24, sub, font(FS, 24), MUTED, qi * al)
    qn = esmooth(_dw(tl, dur, 0.58, 0.72))
    if qn > 0:
        _pop_pill(img, 540, 1630 + dy, "SERING TIAP HARI / OBAT PENGENCER DARAH = KE DOKTER", 23,
                  mix(accent, INK, 0.08), qn * al, qn)
    qs = esmooth(seg(tl, 4.2, 4.8)) * esmooth(seg(dur - tl, 0.1, 0.4))
    if qs > 0:
        _stamp_on(img, 540, 1495 + dy, "KE DOKTER!", qs * al, qs, col=accent, fsz=54, rot=-6)


def sc_rangkuman34(img, d, sc, tl, dur, tg, accent, al, dy):
    """f8: papan rangkuman + tokoh tenang + konfeti."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _recap_on(img, [("drop", "Titik rapuh di depan hidung penyebabnya"),
                    ("bolt", "Tengadah itu mitos - tunduk saja"),
                    ("clock", "Cubit bagian lunak 10 menit penuh"),
                    ("thermo", "Jaga hidung lembap, jangan dicolek")], q * al, tg, t0=0.5, dt=0.7, col=accent)
    _papan9_on(img, 250, 930 + dy, 1.0, q * al, tg, ikon="heart", col=mix(accent, INK, 0.25))
    qr = esmooth(seg(tl, 0.9, 1.3))
    if qr > 0:
        _stamp_on(img, 770, 930 + dy, "JINAK!", qr * al, qr, col=accent, fsz=64, rot=-6)
    qc = esmooth(_dw(tl, dur, 0.55, 0.72))
    if qc > 0:
        _confetti_on(img, tg, qc * al, n=24)


VISUALS.update({
    "intro_mimisan": sc_intro_mimisan,
    "anatomi": sc_anatomi,
    "penyebab": sc_penyebab,
    "tengadah": sc_tengadah,
    "carabenar": sc_carabenar,
    "angka": sc_angka,
    "cegah": sc_cegah,
    "batas34": sc_batas34,
    "rangkuman34": sc_rangkuman34,
})


def _selftest34():
    """Uji cepat adegan Ep34 sebelum dipakai render."""
    names = ["intro_mimisan", "anatomi", "penyebab", "tengadah", "carabenar", "angka",
             "cegah", "batas34", "rangkuman34"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "MIMISAN?"], "accent": "#8C2F39"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep34: 9 adegan OK")


# ====================================================================
# MESIN v9 - GERAK & KACA (22 Sep 2026): tanpa karakter - penuh objek,
# data & gerak. Kartu kaca + bayang lembut, orbit elips, grafik garis,
# tipografi kinetis, gelombang, panah aliran, kartu flip. Gaya 2026.
# ====================================================================


def _bayang_on(img, x0, y0, x1, y1, alpha, blur=10, off=8):
    """v9: bayangan lembut untuk kedalaman (koordinat desain, aman QC)."""
    if alpha <= 0.02:
        return
    lay = Image.new("L", img.size, 0)
    dd = ImageDraw.Draw(lay)
    dd.rounded_rectangle([int(S(x0)) + int(S(off)), int(S(y0)) + int(S(off * 1.4)),
                          int(S(x1)) + int(S(off)), int(S(y1)) + int(S(off * 1.4))],
                         radius=int(S(30)), fill=int(255 * clamp(alpha) * 0.13))
    lay = lay.filter(ImageFilter.GaussianBlur(S(blur)))
    img.paste(Image.new("RGB", img.size, (96, 94, 104)), (0, 0), lay)


def _kartu9_on(img, x0, y0, x1, y1, alpha, tg=0.0, aksen=None, r=34, bayang=True):
    """v9: kartu kaca (panel putih susu + tepi terang + bayang)."""
    if alpha <= 0.01:
        return
    ak = aksen or INK
    if bayang:
        _bayang_on(img, x0 + 8, y0 + 12, x1 + 8, y1 + 12, alpha)
    rrect_on(img, x0, y0, x1, y1, r, mix(WHITE, CREAM, 0.16), alpha,
             outline=mix(ak, WHITE, 0.55), width=3)
    line_on(img, (x0 + r * 0.7, y0 + 9), (x1 - r * 0.7, y0 + 9), mix(ak, WHITE, 0.35), 2, alpha * 0.55)


def _papan9_on(img, cx, cy, s=1.0, alpha=1.0, tg=0.0, ikon=None, col=None, tanya=False):
    """v9: papan kaca melayang + ikon (pengganti visual karakter)."""
    if alpha <= 0.01:
        return
    col = col or INK
    cy += math.sin(tg * 1.7) * 7
    w2 = 120 * s
    _kartu9_on(img, cx - w2, cy - w2, cx + w2, cy + w2, alpha, tg, aksen=mix(col, WHITE, 0.3))
    if tanya:
        paste_c(img, cx, cy - 6, "?", font(FB, int(105 * s)), mix(col, INK, 0.08), alpha)
        dot_on(img, cx + 46 * s, cy - 52 * s, 8 * s, col, alpha)
    else:
        _ico5(img, ikon or "moon", cx, cy, 56 * s, col, alpha, tg,
              pulse=0.25 + 0.25 * math.sin(tg * 2.3))


def _garis9(img, pts, col, width, alpha):
    """v9: poligon-garis (stroke polyline)."""
    for j in range(len(pts) - 1):
        line_on(img, pts[j], pts[j + 1], col, width, alpha)


def _orbit_on(img, cx, cy, R, alpha, tg, n=3, squash=0.38, col=None, nucleus=30, kemiringan=0.5):
    """v9: sistem orbit elips + satelit bergerak dengan kedalaman."""
    if alpha <= 0.01:
        return
    col = col or INK
    for k in range(n):
        rot = kemiringan + k * 0.9
        rr = R * (0.62 + 0.19 * k)
        ph = tg * (0.10 + 0.03 * k) + k * 2.1
        pts = []
        for j in range(25):
            a = 6.2832 * j / 24
            x, y = math.cos(a) * rr, math.sin(a) * rr * squash
            pts.append((cx + x * math.cos(rot) - y * math.sin(rot),
                        cy + x * math.sin(rot) + y * math.cos(rot)))
        _garis9(img, pts, mix(col, WHITE, 0.52), 3, alpha * 0.7)
        a = 6.2832 * (ph % 1.0)
        x, y = math.cos(a) * rr, math.sin(a) * rr * squash
        xr = x * math.cos(rot) - y * math.sin(rot)
        yr = x * math.sin(rot) + y * math.cos(rot)
        kedalaman = 0.5 + 0.5 * math.sin(a)
        dot_on(img, cx + xr, cy + yr, 11, mix(col, WHITE, 0.30 - 0.42 * kedalaman), alpha)
    ell(img, cx - nucleus, cy - nucleus, cx + nucleus, cy + nucleus, fill=col, alpha=alpha,
        outline=mix(col, WHITE, 0.4), width=3)


def _graf_on(img, x0, y0, x1, y1, poin, alpha, tg, t0=0.0, col=None, isi=0.16):
    """v9: grafik garis halus (Catmull-Rom) digambar progresif + area + titik denyut."""
    col = col or INK
    n = len(poin)
    if n < 2 or alpha <= 0.01:
        return
    for g in range(1, 4):
        yy = y1 - (y1 - y0) * g / 4
        line_on(img, (x0, yy), (x1, yy), mix(col, CREAM, 0.55), 2, alpha * 0.35)
    q = esmooth(seg(tg, t0, t0 + 1.15))
    if q <= 0.01:
        return

    def P(i):
        return (x0 + (x1 - x0) * i / (n - 1), y1 - clamp(poin[i]) * (y1 - y0))

    def CR(p0, p1, p2, p3, t):
        t2, t3 = t * t, t * t * t
        return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                      + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
    semua = []
    for i in range(n - 1):
        p0, p1, p2, p3 = P(max(0, i - 1)), P(i), P(i + 1), P(min(n - 1, i + 2))
        for j in range(12):
            t = j / 12
            semua.append((CR(p0[0], p1[0], p2[0], p3[0], t), CR(p0[1], p1[1], p2[1], p3[1], t)))
    semua.append(P(n - 1))
    m = max(2, int(len(semua) * q))
    pts = semua[:m]
    if isi > 0 and q > 0.2:
        poly_on(img, [(pts[0][0], y1)] + pts + [(pts[-1][0], y1)], mix(col, CREAM, 0.80),
                alpha * isi)
    _garis9(img, pts, col, 6, alpha)
    dot_on(img, pts[-1][0], pts[-1][1], 10 * (1.0 + 0.25 * math.sin(tg * 5.0)),
           mix(col, WHITE, 0.25), alpha)


def _kinesis_on(img, cx, cy, kata, alpha, tg, t0=0.0, dt=0.24, fsz=46, col=None):
    """v9: tipografi kinetis - kata muncul urut dengan overshoot + rotasi ringan."""
    if alpha <= 0.01:
        return
    col = col or INK
    kata = kata.split()
    f = font(FB, fsz)
    dd = ImageDraw.Draw(img)
    sp = S(12)
    lebars = [dd.textlength(w, font=f) for w in kata]
    total = sum(lebars) + sp * (len(kata) - 1)
    x = cx * S(1) - total / 2
    ygel = math.sin(tg * 2.0) * S(4)
    for i, wd in enumerate(kata):
        lw = lebars[i]
        qi = seg(tg, t0 + i * dt, t0 + i * dt + 0.38)
        if qi > 0:
            sc = 0.55 + 0.45 * eob(qi)
            lay = Image.new("RGBA", (int(lw) + 24, int(S(fsz)) + 30), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            ld.text((lw / 2 + 12, lay.size[1] / 2), wd, font=f,
                    fill=mix(col, INK, 0.05) + (int(255 * alpha),), anchor="mm")
            lay = lay.rotate(math.sin(i * 1.9) * 5 * (1 - esmooth(qi)), resample=Image.BICUBIC)
            lay2 = lay.resize((max(1, int(lay.size[0] * sc)), max(1, int(lay.size[1] * sc))))
            img.paste(lay2, (int(x - (lay2.size[0] - lw) / 2),
                             int(cy * S(1) - lay2.size[1] / 2 + ygel)), lay2)
        x += lw + sp


def _gelombang_on(img, x0, y0, x1, y1, alpha, tg, n=3, col=None):
    """v9: tumpukan gelombang sinus berjalan (air/gelombang/frekuensi)."""
    col = col or INK
    if alpha <= 0.01:
        return
    h = y1 - y0
    for k in range(n):
        amp = h * (0.16 + 0.05 * k)
        ph = tg * (0.9 + 0.25 * k) + k * 1.3
        pts = []
        for i in range(37):
            xx = x0 + (x1 - x0) * i / 36
            yy = (y0 + y1) / 2 + math.sin(6.2832 * ((2.0 + 0.9 * k) * i / 36 - ph)) * amp
            pts.append((xx, yy))
        _garis9(img, pts, mix(col, WHITE, 0.25 * k), 5, alpha * (1.0 - 0.28 * k))


def _panah_flow_on(img, p1, p2, alpha, tg, col=None, lengkung=0.22, lebar=7):
    """v9: panah lengkung dengan putus-putus mengalir (arah proses)."""
    col = col or INK
    if alpha <= 0.01:
        return
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    panjang = math.hypot(dx, dy) or 1
    nx, ny = -dy / panjang, dx / panjang
    qx, qy = mx + nx * panjang * lengkung, my + ny * panjang * lengkung

    def B(t):
        u = 1 - t
        return (u * u * p1[0] + 2 * u * t * qx + t * t * p2[0],
                u * u * p1[1] + 2 * u * t * qy + t * t * p2[1])
    ph = (tg * 0.9) % 1.0
    for d in range(6):
        t0 = (ph + d * 0.17) % 1.0
        t1 = t0 + 0.085
        if t1 > 1.0:
            continue
        seg_pts = [B(t0 + (t1 - t0) * j / 6) for j in range(7)]
        _garis9(img, seg_pts, col, lebar, alpha * 0.9)
    _garis9(img, [B(j / 26) for j in range(27)], mix(col, CREAM, 0.35), 2, alpha * 0.5)
    tip = B(1.0)
    uj = B(0.955)
    for sisi in (-1, 1):
        a = math.atan2(tip[1] - uj[1], tip[0] - uj[0]) + sisi * 0.5
        line_on(img, tip, (tip[0] - 26 * math.cos(a), tip[1] - 26 * math.sin(a)), col, lebar + 2, alpha)


def _flip_on(img, cx, cy, w, h, frac, alpha, tg, ikon_a="moon", ikon_b="eye", col=None):
    """v9: kartu flip 3D palsu - ikon bertukar di tengah putaran."""
    col = col or INK
    if alpha <= 0.01 or frac <= 0:
        return
    sx = max(0.05, abs(math.cos(math.pi * clamp(frac))))
    w2 = w / 2 * sx
    if sx > 0.9:
        _bayang_on(img, cx - w2 + 8, cy - h / 2 + 12, cx + w2 + 8, cy + h / 2 + 12, alpha)
    rrect_on(img, cx - w2, cy - h / 2, cx + w2, cy + h / 2, 30, mix(WHITE, col, 0.08), alpha,
             outline=mix(col, WHITE, 0.42), width=4)
    if sx > 0.22:
        _ico5(img, ikon_a if frac < 0.5 else ikon_b, cx, cy, min(w, h) * 0.30, col, alpha, tg)


def _selftest_v9():
    """Uji cepat seluruh paket v9."""
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    _kartu9_on(img, 80, 120, 460, 420, 1.0, 1.2, aksen=BLUE)
    _papan9_on(img, 700, 270, 1.0, 1.0, 1.3, ikon="moon", col=BLUE)
    _papan9_on(img, 940, 270, 0.8, 1.0, 1.5, tanya=True, col=RED)
    _orbit_on(img, 250, 700, 170, 1.0, 1.2, n=3, col=INK)
    _graf_on(img, 480, 560, 990, 860, [0.2, 0.55, 0.4, 0.85, 0.7], 1.0, 1.4, t0=0.0, col=BLUE)
    _kinesis_on(img, 540, 1010, "BULAN RAKSASA ITU ILUSI", 1.0, 1.6, t0=0.0, fsz=44)
    _gelombang_on(img, 90, 1100, 990, 1320, 1.0, 1.1, n=3, col=BLUE)
    _panah_flow_on(img, (150, 1450), (700, 1450), 1.0, 1.2, col=GREEN)
    _flip_on(img, 850, 1450, 300, 220, 0.35, 1.0, 1.3, "moon", "eye", col=RED)
    for tl in (0.2, 0.6, 1.1):
        _papan9_on(img, 300, 1700, 0.9, 1.0, tl, ikon="heart", col=RED)
    print("selftest v9: kartu kaca + papan + orbit + graf + kinesis + gelombang + panah flow + flip OK")


# ====================== Ep35: Supermoon & Ilusi Bulan ======================


def _bulan35(img, cx, cy, r, alpha, tg, col=None, hangat=0.35):
    """v9: piringan bulan krem-hangat + kawah lembut + halo tipis."""
    col = col or (216, 186, 120)
    _glow(img, cx - r * 1.25, cy - r * 1.25, cx + r * 1.25, cy + r * 1.25,
          mix((250, 238, 200), col, 0.4), alpha * 0.5)
    ell(img, cx - r, cy - r, cx + r, cy + r, fill=mix((250, 240, 205), col, hangat), alpha=alpha,
        outline=mix(col, INK, 0.15), width=3)
    for (dx, dy, rr) in ((-0.42, -0.30, 0.16), (0.36, 0.05, 0.22), (-0.12, 0.48, 0.13),
                         (0.10, -0.55, 0.10), (-0.60, 0.25, 0.09)):
        ell(img, cx + dx * r - rr * r, cy + dy * r - rr * r,
            cx + dx * r + rr * r, cy + dy * r + rr * r,
            fill=mix((250, 240, 205), col, hangat + 0.25), alpha=alpha * 0.8)


def _kota35(img, x0, x1, ybase, alpha, col):
    """v9: siluet kota garis (outline saja - aman QC) untuk horizon."""
    import random as _r
    rng = _r.Random(35)
    xx = x0
    while xx < x1 - 40:
        w = rng.randint(46, 92)
        h = rng.randint(40, 150)
        x2 = min(xx + w, x1)
        line_on(img, (xx, ybase), (xx, ybase - h), col, 4, alpha)
        line_on(img, (xx, ybase - h), (x2, ybase - h), col, 4, alpha)
        line_on(img, (x2, ybase - h), (x2, ybase), col, 4, alpha)
        for j in range(max(1, h // 46)):
            line_on(img, (xx + 10, ybase - h + 22 + j * 30), (x2 - 10, ybase - h + 22 + j * 30),
                    mix(col, CREAM, 0.45), 2, alpha * 0.6)
        xx = x2 + rng.randint(8, 26)


def sc_intro_super(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: bulan emas terbit di horizon kota - SUPERMOON 2026."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    _kartu9_on(img, 110, 790 + dy, 970, 1590 + dy, q2 * al, tg, aksen=accent, r=40)
    _langit7(img, 126, 806 + dy, 954, 1574 + dy, q2 * al * 0.92, tg, mood="malam", sun=(250, 960))
    yh = 1355 + dy
    qb = esmooth(seg(tl, 0.9, 1.7))
    if qb > 0:
        _bulan35(img, 540, yh - 120, 185, qb * al, tg, hangat=0.42)
    _kota35(img, 140, 940, yh, q2 * al * seg(tl, 0.7, 1.2), mix(accent, INK, 0.18))
    _lbl(img, 200, 870 + dy, "HORIZON", font(FS, 22), mix(CREAM, WHITE, 0.4), q2 * al)
    qk = esmooth(seg(tl, 1.9, 2.3))
    if qk > 0:
        _kinesis_on(img, 540, 1655 + dy, "24 NOV + 24 DES 2026", qk * al, tg, t0=1.9, fsz=40, col=accent)
    qp = esmooth(seg(tl, 2.6, 3.0))
    if qp > 0:
        _papan9_on(img, 850, 950 + dy, 0.62, qp * al, tg, tanya=True, col=accent)


def sc_jarak(img, d, sc, tl, dur, tg, accent, al, dy):
    """f1: orbit elips Bumi-Bulan + skala dekat/jauh + selisih 50 ribu km."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 870 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _orbit_on(img, 335, 1215 + dy, 210, q * al, tg, n=2, col=mix(accent, INK, 0.05), nucleus=40)
    _lbl(img, 335, 1290 + dy, "BUMI", font(FB, 26), mix(accent, INK, 0.05), q * al)
    dot_on(img, 470, 1055 + dy, 16, mix((216, 186, 120), INK, 0.05), q * al)
    _lbl(img, 505, 1022 + dy, "BULAN", font(FS, 22), MUTED, q * al)
    qh = esmooth(_dw(tl, dur, 0.10, 0.26))
    if qh > 0:
        _hitung_on(img, 760, 970 + dy, 384400, "KM - JARAK RATA-RATA", qh * al, tg, t0=0.3, fsz=54, col=accent)
    qs = esmooth(_dw(tl, dur, 0.30, 0.50))
    if qs > 0:
        _skala_on(img, 640, 940, 1500 + dy, [("TERDEKAT", 0.876, "356.500 KM"),
                                             ("TERJAUH", 1.0, "406.700 KM")],
                  qs * al, tg, t0=0.4, col=accent, hmax=330)
    qd = esmooth(_dw(tl, dur, 0.55, 0.68))
    if qd > 0:
        _detail_on(img, 500, 1430 + dy, 790, 1400 + dy, "SELISIH 50.000 KM",
                   "lebih dari keliling Bumi", qd * al, tg, col=accent, w=330)
    qz = esmooth(_dw(tl, dur, 0.66, 0.78))
    if qz > 0:
        _pop_pill(img, 740, 1630 + dy, "ELIPS = ADA TITIK TERDEKAT & TERJAUH", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_ukuran(img, d, sc, tl, dur, tg, accent, al, dy):
    """f2: purnama terdekat vs terjauh - 14% lebih besar, 30% lebih terang."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 830 + dy, 970, 1500 + dy, q * al, tg, aksen=accent, r=40)
    q1 = esmooth(seg(tl, 0.4, 0.9))
    if q1 > 0:
        _bulan35(img, 340, 1165 + dy, 175, q1 * al, tg, hangat=0.55)
        _lbl(img, 340, 1430 + dy, "TERDEKAT - 356.500 KM", font(FS, 23), mix(accent, INK, 0.05), q1 * al)
    q2 = esmooth(seg(tl, 0.7, 1.2))
    if q2 > 0:
        _bulan35(img, 740, 1165 + dy, 153, q2 * al, tg, hangat=0.18)
        _lbl(img, 740, 1430 + dy, "TERJAUH - 406.700 KM", font(FS, 23), MUTED, q2 * al)
    qu = esmooth(seg(tl, 1.3, 1.8))
    if qu > 0:
        _ukur_on(img, (560, 1000 + dy), (560, 1330 + dy), "+14% LEBAR", qu * al, tg,
                 t0=1.3, col=accent, fsz=23, off=-64)
    qh = esmooth(_dw(tl, dur, 0.35, 0.52))
    if qh > 0:
        _hitung_on(img, 760, 930 + dy, 30, "PERSEN LEBIH TERANG", qh * al, tg, t0=0.4, fsz=54, col=accent)
    qsl = esmooth(_dw(tl, dur, 0.52, 0.66))
    if qsl > 0:
        _slider_on(img, 170, 1600 + dy, 910, 1600 + dy, 0.5 + 0.34 * math.sin(tg * 0.9), qsl * al, tg, col=accent)
        _lbl(img, 170, 1648 + dy, "JAUH", font(FS, 21), MUTED, qsl * al)
        _lbl(img, 910, 1648 + dy, "DEKAT", font(FS, 21), mix(accent, INK, 0.05), qsl * al)


def sc_ilusi(img, d, sc, tl, dur, tg, accent, al, dy):
    """f3: moon illusion - ukuran sama, otak membesar-besarkan di horizon."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 830 + dy, 970, 1230 + dy, q * al, tg, aksen=accent, r=36)
    _kartu9_on(img, 110, 1290 + dy, 970, 1560 + dy, q * al, tg, aksen=mix(accent, CREAM, 0.25), r=36)
    q1 = esmooth(seg(tl, 0.3, 0.8))
    if q1 > 0:
        _bulan35(img, 300, 1090 + dy, 140, q1 * al, tg, hangat=0.5)
        line_on(img, (150, 1190 + dy), (930, 1190 + dy), mix(accent, INK, 0.12), 4, q1 * al)
        _lbl(img, 690, 1075 + dy, "DI HORIZON", font(FB, 27), mix(accent, INK, 0.05), q1 * al)
        _lbl(img, 690, 1112 + dy, "TAMPAK SAMPAI 3X LEBIH BESAR", font(FS, 22), MUTED, q1 * al)
    q2 = esmooth(seg(tl, 0.6, 1.1))
    if q2 > 0:
        _bulan35(img, 300, 1425 + dy, 140, q2 * al, tg, hangat=0.2)
        _lbl(img, 690, 1400 + dy, "DI ATAS KEPALA", font(FB, 27), mix(accent, INK, 0.05), q2 * al)
        _lbl(img, 690, 1437 + dy, "UKURAN SEBENARNYA SAMA", font(FS, 22), MUTED, q2 * al)
    qe = esmooth(seg(tl, 1.4, 1.9))
    if qe > 0:
        _ico5(img, "eye", 815, 1520 + dy, 34, accent, qe * al, tg)
        _panah_flow_on(img, (850, 1520 + dy), (955, 1480 + dy), qe * al, tg, col=accent, lengkung=0.25, lebar=6)
        _lbl(img, 815, 1585 + dy, "OTAK MENILAI HORIZON", font(FS, 20), MUTED, qe * al)
        _lbl(img, 815, 1612 + dy, "SEBAGAI JAUH", font(FS, 20), MUTED, qe * al)
    qk = esmooth(_dw(tl, dur, 0.42, 0.56))
    if qk > 0:
        _kinesis_on(img, 540, 1650 + dy, "FOTO AJA: HASILNYA SAMA", qk * al, tg, t0=0.0, fsz=40, col=accent)


def sc_supermoon(img, d, sc, tl, dur, tg, accent, al, dy):
    """f4: kalender 2 supermoon - 24 Nov & 24 Des (terdekat sejak 2019)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kisi_on(img, 110, 860 + dy, 970, 1500 + dy, q * al * 0.5, step=64, col=mix(accent, CREAM, 0.45))
    for k, (cx, tgl, jar, sub) in enumerate(((340, "24 NOV", 358300, "SUPERMOON PERTAMA"),
                                             (740, "24 DES", 356700, "TERDEKAT SEJAK 2019"))):
        qi = esmooth(_dw(tl, dur, 0.08 + k * 0.14, 0.26 + k * 0.14))
        if qi <= 0.01:
            continue
        _kartu9_on(img, cx - 185, 890 + dy, cx + 185, 1470 + dy, qi * al, tg, aksen=accent, r=36)
        _bulan35(img, cx, 1030 + dy, 92, qi * al, tg, hangat=0.45 + 0.15 * k)
        paste_c(img, cx, 1205 + dy, tgl, font(FB, 52), mix(accent, INK, 0.05), qi * al)
        _hitung_on(img, cx, 1320 + dy, jar, "KM DARI BUMI", qi * al * seg(tl, 1.0 + k * 0.6, 1.4 + k * 0.6),
                   tg, t0=1.0 + k * 0.6, fsz=34, col=accent)
        paste_c(img, cx, 1420 + dy, sub, font(FS, 21), MUTED, qi * al)
    qs = esmooth(_dw(tl, dur, 0.52, 0.66))
    if qs > 0:
        _stamp_on(img, 740, 940 + dy, "TANDAI!", qs * al, qs, col=accent, fsz=46, rot=-7)
    qz = esmooth(_dw(tl, dur, 0.66, 0.78))
    if qz > 0:
        _pop_pill(img, 540, 1600 + dy, "PURNAMA + TITIK TERDEKAT ORBIT = SUPERMOON", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_aman(img, d, sc, tl, dur, tg, accent, al, dy):
    """f5: bukan bencana - gravitasi nyaris sama, pasang naik senti."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    q1 = esmooth(seg(tl, 0.3, 0.8))
    if q1 > 0:
        _bulan35(img, 260, 1030 + dy, 110, q1 * al, tg, hangat=0.4)
        _panah_flow_on(img, (260, 1150 + dy), (260, 1360 + dy), q1 * al, tg, col=mix(BLUE, INK, 0.05),
                       lengkung=0.12, lebar=6)
        _lbl(img, 315, 1258 + dy, "TARIKAN PASANG", font(FS, 20), MUTED, q1 * al)
    _gelombang_on(img, 130, 1400 + dy, 950, 1540 + dy, q * al, tg, n=3, col=BLUE)
    line_on(img, (130, 1400 + dy), (950, 1400 + dy), mix(BLUE, INK, 0.10), 4, q * al)
    _lbl(img, 540, 1585 + dy, "LAUT TETAP AMAN", font(FS, 22), MUTED, q * al)
    for k, (ik, judul, sub) in enumerate((("shield", "BUKAN PENANDA BENCANA", "gravitasi: nyaris sama"),
                                          ("drop", "PASANG NAIK SENTI SAJA", "beda tipis dari biasa"))):
        qi = esmooth(_dw(tl, dur, 0.14 + k * 0.16, 0.32 + k * 0.16))
        if qi <= 0.01:
            continue
        yy = 950 + k * 190 + dy
        _kartu9_on(img, 440, yy - 80, 950, yy + 80, qi * al, tg, aksen=accent, r=30)
        _ico5(img, ik, 530, yy, 44, GREEN, qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 2.6 + k))
        paste_c(img, 750, yy - 22, judul, font(FB, 25), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 750, yy + 26, sub, font(FS, 21), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.60, 0.72))
    if qz > 0:
        _pop_pill(img, 540, 1670 + dy, "SUPERMOON ITU NORMAL - SETIAP ADA", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_tips(img, d, sc, tl, dur, tg, accent, al, dy):
    """f6: 4 kartu cara menikmati supermoon."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    kartu = ((340, 1030, "clock", "PUKUL ~18.45", "hadap timur: bulan terbit"),
             (740, 1030, "moon", "SAAT DI HORIZON", "paling raksasa di mata"),
             (340, 1370, "drop", "GENANGAN AIR", "refleksi bulan gratis"),
             (740, 1370, "eye", "BINOKULAR BIASA", "kawah langsung terlihat"))
    for k, (cx, cy, ik, judul, sub) in enumerate(kartu):
        qi = esmooth(_dw(tl, dur, 0.06 + k * 0.10, 0.24 + k * 0.10))
        if qi <= 0.01:
            continue
        _kartu9_on(img, cx - 190, cy - 155, cx + 190, cy + 145, qi * al, tg, aksen=accent, r=34)
        _ico5(img, ik, cx, cy - 62, 44, accent, qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 2.8 + k))
        paste_c(img, cx, cy + 18, judul, font(FB, 27), mix(accent, INK, 0.05), qi * al)
        paste_c(img, cx, cy + 66, sub, font(FS, 21), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.52, 0.66))
    if qz > 0:
        _pop_pill(img, 540, 1630 + dy, "KOTA PUN BISA: CUKUP LIHAT KE TIMUR", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_rangkuman35(img, d, sc, tl, dur, tg, accent, al, dy):
    """f7: papan rangkuman + bulan emas + konfeti."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _recap_on(img, [("moon", "Orbit bulan itu elips: 356 - 407 ribu km"),
                    ("bolt", "Supermoon = purnama di titik terdekat"),
                    ("eye", "Bulan raksasa di horizon itu ilusi otak")], q * al, tg, t0=0.5, dt=0.7, col=accent)
    qs = esmooth(seg(tl, 0.9, 1.3))
    if qs > 0:
        _stamp_on(img, 800, 915 + dy, "SUPERMOON!", qs * al, qs, col=accent, fsz=44, rot=-6)
    qk = esmooth(seg(tl, 1.4, 1.8))
    if qk > 0:
        _kinesis_on(img, 540, 1660 + dy, "24 NOV + 24 DES 2026!", qk * al, tg, t0=0.0, fsz=42, col=accent)
    qc = esmooth(_dw(tl, dur, 0.55, 0.72))
    if qc > 0:
        _confetti_on(img, tg, qc * al, n=22)


VISUALS.update({
    "intro_super": sc_intro_super,
    "jarak": sc_jarak,
    "ukuran": sc_ukuran,
    "ilusi": sc_ilusi,
    "supermoon": sc_supermoon,
    "aman": sc_aman,
    "tips": sc_tips,
    "rangkuman35": sc_rangkuman35,
})


def _selftest35():
    """Uji cepat adegan Ep35 sebelum dipakai render."""
    names = ["intro_super", "jarak", "ukuran", "ilusi", "supermoon", "aman", "tips",
             "rangkuman35"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["SUPERMOON", "2026!"], "accent": "#1C2E5E"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep35: 8 adegan OK")


# ====================== Ep36: Kenapa Migrain? ======================


def _denyut36(img, cx, cy, alpha, tg, col):
    """v9: cincin denyut nyeri - mengembang lalu pudar."""
    for k in range(3):
        f = (tg * 0.55 + k / 3.0) % 1.0
        rr = 60 + f * 120
        ell(img, cx - rr, cy - rr, cx + rr, cy + rr,
            outline=mix(col, WHITE, f * 0.5), width=max(2, int(S(5 * (1.0 - f)))),
            alpha=alpha * (1.0 - f) * 0.9)


def sc_intro_migrain(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: otak besar + denyut nyeri + tanda tanda migrain."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    _kartu9_on(img, 110, 790 + dy, 970, 1590 + dy, q2 * al, tg, aksen=accent, r=40)
    _ico5(img, "brain", 380, 1190 + dy, 200, mix(accent, INK, 0.10), q2 * al, tg)
    _denyut36(img, 480, 1190 + dy, q2 * al, tg, accent)
    for k, (txt, c) in enumerate((("SATU SISI", accent), ("BERDENYUT", accent),
                                  ("TAK TAHAN CAHAYA", accent))):
        qp = esmooth(seg(tl, 1.0 + k * 0.25, 1.4 + k * 0.25))
        if qp > 0:
            _pop_pill(img, 790, 950 + k * 120 + dy, txt, 23, mix(c, WHITE, 0.78), qp * al, qp)
    qk = esmooth(seg(tl, 1.9, 2.3))
    if qk > 0:
        _kinesis_on(img, 540, 1660 + dy, "BUKAN SAKIT KEPALA BIASA", qk * al, tg, t0=1.9,
                    fsz=40, col=accent)


def sc_gelombang36(img, d, sc, tl, dur, tg, accent, al, dy):
    """f1: otak hiper-reaktif + gelombang CSD menyapu."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 860 + dy, 620, 1560 + dy, q * al, tg, aksen=accent)
    _ico5(img, "brain", 365, 1210 + dy, 190, mix(accent, INK, 0.10), q * al, tg)
    sx = 200 + ((tg * 0.30) % 1.0) * 330
    _glow(img, sx - S(26), 990 + dy, sx + S(26), 1430 + dy, mix(accent, WHITE, 0.35), q * al * 0.7)
    line_on(img, (sx, 990 + dy), (sx, 1430 + dy), accent, 6, q * al)
    _lbl(img, 365, 1510 + dy, "GELOMBANG MENYAPU PELAN", font(FS, 22), mix(accent, INK, 0.05), q * al)
    _detail_on(img, sx, 1200 + dy, 700, 1000 + dy, "CSD - CORTICAL SPREADING DEPRESSION",
               "gelombang listrik yang merambat", q * al * seg(tl, 0.8, 1.2), tg, col=accent, w=340)
    qk = esmooth(_dw(tl, dur, 0.30, 0.44))
    if qk > 0:
        _kinesis_on(img, 780, 1310 + dy, "OTAK HIPER-REAKTIF", qk * al, tg, t0=0.0, fsz=40, col=accent)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _pop_pill(img, 780, 1430 + dy, "SEKALI TERPICA, GELOMBANG LAHIR", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_aura36(img, d, sc, tl, dur, tg, accent, al, dy):
    """f2: aura zigzag + 1 dari 3 + jendela 5-60 menit."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 830 + dy, 970, 1280 + dy, q * al, tg, aksen=accent, r=38)
    qa = esmooth(seg(tl, 0.3, 0.9))
    if qa > 0:
        pts = [(180 + i * 44, 1160 + dy + (i % 2) * 46 - i * 7) for i in range(15)]
        _garis9(img, pts, accent, 8, qa * al)
        _ico5(img, "eye", 855, 1000 + dy, 46, mix(accent, INK, 0.08), qa * al, tg)
        _panah_flow_on(img, (855, 1055 + dy), (760, 1130 + dy), qa * al, tg, col=accent,
                       lengkung=0.3, lebar=6)
        _lbl(img, 480, 1240 + dy, "KILATAN - ZIGZAG - BAYANGAN BUTA", font(FS, 23),
             mix(accent, INK, 0.05), qa * al)
    q2 = esmooth(seg(tl, 0.6, 1.1))
    if q2 > 0:
        paste_c(img, 540, 1360 + dy, "1 DARI 3 PENDERITA", font(FB, 56), mix(accent, INK, 0.05), q2 * al)
        _lbl(img, 540, 1420 + dy, "MERASAKAN AURA SEBELUM SAKIT", font(FS, 23), MUTED, q2 * al)
    qu = esmooth(seg(tl, 1.3, 1.7))
    if qu > 0:
        _ukur_on(img, (220, 1520 + dy), (860, 1520 + dy), "5 - 60 MENIT", qu * al, tg,
                 t0=1.3, col=accent, fsz=25, off=58)
    qz = esmooth(_dw(tl, dur, 0.60, 0.72))
    if qz > 0:
        _pop_pill(img, 540, 1660 + dy, "ADA JUGA KESEMUTAN SAMPAI BICARA PELO", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_cgrp36(img, d, sc, tl, dur, tg, accent, al, dy):
    """f3: rantai CSD -> trigeminus -> CGRP -> pembuluh membesar + loop."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 860 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _ico5(img, "brain", 335, 1080 + dy, 150, mix(accent, INK, 0.10), q * al, tg)
    _panah_flow_on(img, (335, 1250 + dy), (335, 1420 + dy), q * al, tg, col=accent, lengkung=0.1)
    _pop_pill(img, 335, 1480 + dy, "SARAF TRIGEMINUS", 24, mix(accent, INK, 0.10), q * al * seg(tl, 0.5, 0.9), q)
    dot_on(img, 335, 1330 + dy, 12, RED, q * al)
    for k, (cx, judul, sub) in enumerate(((760, "CGRP TERLEPAS", "molekul pembuluh darah"),
                                          (760, "PEMBULUH MEMBESAR", "selaput otak meradang"),
                                          (760, "NYERI BERDENYUT", "satu sisi kepala"))):
        qi = esmooth(_dw(tl, dur, 0.16 + k * 0.14, 0.32 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 990 + k * 200 + dy
        _kartu9_on(img, 620, yy - 74, 950, yy + 74, qi * al, tg, aksen=accent, r=28)
        paste_c(img, 790, yy - 20, judul, font(FB, 28), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 790, yy + 26, sub, font(FS, 21), MUTED, qi * al)
        if k == 1:
            wv = 52 + 9 * math.sin(tg * 2.6)
            ell(img, 660 - wv * 0.4, yy - 11, 660 + wv * 0.4, yy + 11,
                fill=mix(RED, WHITE, 0.45), alpha=qi * al, outline=mix(accent, INK, 0.1), width=3)
    qf = esmooth(seg(tl, 1.6, 2.0))
    if qf > 0:
        _panah_flow_on(img, (900, 1080 + dy), (620, 920 + dy), qf * al, tg, col=mix(accent, CREAM, 0.25),
                       lengkung=-0.28, lebar=5)
        _lbl(img, 795, 895 + dy, "LOOP: MAKIN SAKIT", font(FS, 20), MUTED, qf * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _stamp_on(img, 760, 1650 + dy, "KUNCI: CGRP", qz * al, qz, col=accent, fsz=48, rot=-6)


def sc_pemicu36(img, d, sc, tl, dur, tg, accent, al, dy):
    """f4: empat pemicu harian dengan meter."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    col = mix(accent, INK, 0.12)
    cards = [(300, 1040, "STRES", 0.84, "bolt"),
             (780, 1040, "TIDUR KACAU", 0.74, "moon"),
             (300, 1430, "LEWAT MAKAN", 0.66, "stomach"),
             (780, 1430, "CAHAYA KEDIP", 0.60, "eye")]
    for i, (cx, cy, txt, frac, ik) in enumerate(cards):
        qi = esmooth(_dw(tl, dur, 0.06 + i * 0.10, 0.24 + i * 0.10))
        if qi <= 0.01:
            continue
        rrect_on(img, cx - 190, cy - 190, cx + 190, cy + 150, 34, mix(WHITE, accent, 0.14), qi * al,
                 outline=mix(accent, INK, 0.10), width=4)
        _ico5(img, ik, cx, cy - 105, 40, col, qi * al, tg, pulse=0.4 + 0.3 * math.sin(tg * 3 + i))
        _meter_on(img, cx, cy + 35, 80, qi * frac, mix(accent, INK, 0.06), qi * al)
        _pop_pill(img, cx, cy + 92, txt, 21, mix(accent, INK, 0.08), qi * al, qi * 1.3)
    qn = esmooth(_dw(tl, dur, 0.50, 0.62))
    if qn > 0:
        _pop_pill(img, 540, 1660 + dy, "SEBELUM HAID: HORMON TURUN - PEMICU KUAT", 24,
                  mix(accent, INK, 0.10), qn * al, qn)
    qo = esmooth(_dw(tl, dur, 0.62, 0.74))
    if qo > 0:
        _lbl(img, 540, 1610 + dy, "BEDA ORANG, BEDA PEMICU", font(FS, 22), MUTED, qo * al)


def sc_angka36(img, d, sc, tl, dur, tg, accent, al, dy):
    """f5: skala 3x wanita + genetik 50% + beban disabilitas 90%."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kisi_on(img, 110, 860 + dy, 970, 1500 + dy, q * al * 0.5, step=64, col=mix(accent, CREAM, 0.45))
    _hitung_on(img, 760, 990 + dy, 50, "PERSEN RISIKO DARI ORANGTUA", q * al, tg, t0=1.2,
               fsz=56, col=accent)
    qw = esmooth(seg(tl, 0.4, 0.8))
    if qw > 0:
        _kartu9_on(img, 150, 1130 + dy, 540, 1430 + dy, qw * al, tg, aksen=accent, r=30)
        dot_on(img, 255, 1280 + dy, 24, mix(accent, CREAM, 0.30), qw * al)
        paste_c(img, 415, 1250 + dy, "1X", font(FB, 42), MUTED, qw * al)
        paste_c(img, 345, 1370 + dy, "PRIA", font(FS, 24), MUTED, qw * al)
    q3 = esmooth(seg(tl, 0.6, 1.0))
    if q3 > 0:
        _kartu9_on(img, 580, 1130 + dy, 970, 1430 + dy, q3 * al, tg, aksen=accent, r=30)
        dot_on(img, 670, 1280 + dy, 42, mix(accent, INK, 0.05), q3 * al)
        paste_c(img, 835, 1250 + dy, "3X", font(FB, 54), mix(accent, INK, 0.05), q3 * al)
        paste_c(img, 775, 1370 + dy, "WANITA", font(FS, 24), mix(accent, INK, 0.05), q3 * al)
    q9 = esmooth(seg(tl, 2.4, 2.8))
    if q9 > 0:
        _pop_pill(img, 540, 1560 + dy, "90% BEBAN DISABILITAS SAKIT KEPALA DUNIA", 23,
                  mix(accent, INK, 0.10), q9 * al, q9)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _pop_pill(img, 540, 1650 + dy, "WANITA 3X - SETELAH PUBERTAS (HORMON)", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_tangani36(img, d, sc, tl, dur, tg, accent, al, dy):
    """f6: tangga penanganan + jebakan obat berlebih."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _tangga_on(img, [(300, 1330 + dy, "OBAT DI FASE AWAL"), (540, 1210 + dy, "RUANG GELAP SEPI"),
                     (780, 1330 + dy, "AIR YANG CUKUP")], q * al, tg, t0=0.5, dt=0.5)
    _hitung_on(img, 780, 990 + dy, 22, "PERSEN BEBAN DARI OBAT", q * al, tg, t0=0.8,
               fsz=50, col=accent)
    qf = esmooth(_dw(tl, dur, 0.30, 0.44))
    if qf > 0:
        frac = 0.5 + 0.5 * math.sin(tg * 0.85)
        _flip_on(img, 330, 1620 + dy, 340, 190, frac, qf * al, tg, "drop", "bolt", col=accent)
        _lbl(img, 160, 1620 + dy, "WAJAR", font(FS, 22), mix(GREEN, INK, 0.05), qf * al)
        _lbl(img, 505, 1620 + dy, "BERLEBIHAN", font(FS, 22), mix(RED, INK, 0.05), qf * al)
        _lbl(img, 330, 1745 + dy, "PEREDA -> BISA MEMICU SAKIT KEPALA BARU", font(FS, 21),
             MUTED, qf * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _stamp_on(img, 800, 1560 + dy, "JANGAN BERLEBIH!", qz * al, qz, col=accent, fsz=44, rot=-6)


def sc_batas36(img, d, sc, tl, dur, tg, accent, al, dy):
    """f7: tanda wajib dokter."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    rrect_on(img, 90, 830 + dy, 990, 1560 + dy, 44, mix(accent, WHITE, 0.80), q * al,
             outline=accent, width=5)
    kartu = (("bolt", "DATANG SEPERTI GUNTUR", "terburuk seumur hidup"),
             ("germ", "DEMAM + KAKU LEHER", "tanda infeksi serius"),
             ("brain", "LUMPUH / PELO MENDADAK", "tanda stroke - IGD"))
    for k, (ik, judul, sub) in enumerate(kartu):
        qi = esmooth(_dw(tl, dur, 0.10 + k * 0.14, 0.28 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 990 + k * 180 + dy
        rrect_on(img, 140, yy - 70, 940, yy + 70, 32, mix(WHITE, accent, 0.14), qi * al,
                 outline=mix(accent, INK, 0.10), width=3)
        _ico5(img, ik, 230, yy, 40, accent, qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 600, yy - 22, judul, font(FB, 32), mix(accent, INK, 0.15), qi * al)
        paste_c(img, 600, yy + 24, sub, font(FS, 24), MUTED, qi * al)
    qn = esmooth(_dw(tl, dur, 0.58, 0.72))
    if qn > 0:
        _pop_pill(img, 540, 1630 + dy, "SETELAH BENTURAN KEPALA - SAKIT BARU DI ATAS 50 TAHUN", 23,
                  mix(accent, INK, 0.08), qn * al, qn)
    qs = esmooth(seg(tl, 4.2, 4.8)) * esmooth(seg(dur - tl, 0.1, 0.4))
    if qs > 0:
        _stamp_on(img, 540, 1495 + dy, "KE DOKTER!", qs * al, qs, col=accent, fsz=54, rot=-6)


def sc_rangkuman36(img, d, sc, tl, dur, tg, accent, al, dy):
    """f8: papan rangkuman + stamp + konfeti."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _recap_on(img, [("bolt", "Migrain mulai dari gelombang di otak"),
                    ("eye", "Aura: peringatan awal 5 - 60 menit"),
                    ("drop", "CGRP: molekul kuncinya"),
                    ("shield", "Obat berlebih = jebakan sakit baru")], q * al, tg, t0=0.5, dt=0.7, col=accent)
    qs = esmooth(seg(tl, 1.0, 1.4))
    if qs > 0:
        _stamp_on(img, 800, 915 + dy, "BUKAN NGADAT!", qs * al, qs, col=accent, fsz=42, rot=-6)
    qk = esmooth(seg(tl, 1.5, 1.9))
    if qk > 0:
        _kinesis_on(img, 540, 1650 + dy, "MIGRAIN ITU NYATA", qk * al, tg, t0=0.0, fsz=42, col=accent)
    qc = esmooth(_dw(tl, dur, 0.55, 0.72))
    if qc > 0:
        _confetti_on(img, tg, qc * al, n=22)


VISUALS.update({
    "intro_migrain": sc_intro_migrain,
    "gelombang36": sc_gelombang36,
    "aura36": sc_aura36,
    "cgrp36": sc_cgrp36,
    "pemicu36": sc_pemicu36,
    "angka36": sc_angka36,
    "tangani36": sc_tangani36,
    "batas36": sc_batas36,
    "rangkuman36": sc_rangkuman36,
})


def _selftest36():
    """Uji cepat adegan Ep36 sebelum dipakai render."""
    names = ["intro_migrain", "gelombang36", "aura36", "cgrp36", "pemicu36", "angka36",
             "tangani36", "batas36", "rangkuman36"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "MIGRAIN?"], "accent": "#3A2E6E"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep36: 9 adegan OK")


# ====================== Ep37: Kenapa Jerawat Muncul? ======================


def _kulit37(img, x0, y0, x1, y1, alpha, tg, merah_at=None):
    """v9: tekstur kulit makro - grid titik pori yang bernapas."""
    if alpha <= 0.01:
        return
    for gy in range(6):
        for gx in range(10):
            if (gx + gy) % 2:
                continue
            xx = x0 + (x1 - x0) * (gx + 0.5) / 10
            yy = y0 + (y1 - y0) * (gy + 0.5) / 6
            nap = 1.0 + 0.10 * math.sin(tg * 1.6 + gx * 0.7 + gy * 1.1)
            ell(img, xx - 7 * nap, yy - 7 * nap, xx + 7 * nap, yy + 7 * nap,
                fill=mix(CREAM, INK, 0.09), alpha=alpha * 0.8)
    if merah_at:
        _denyut36(img, merah_at[0], merah_at[1], alpha * 0.9, tg, RED)


def _folikel37(img, cx, cy, h, alpha, tg, sebum=0.0, sumbat=0.0, merah=0.0):
    """v9: potongan folikel: tabung + rambut + kelenjar minyak + isi."""
    if alpha <= 0.01:
        return
    w = 150
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, w / 2,
             mix(WHITE, CREAM, 0.30), alpha, outline=mix(INK, CREAM, 0.45), width=4)
    line_on(img, (cx, cy - h / 2), (cx, cy + h * 0.05), mix((96, 66, 46), CREAM, 0.15), 5, alpha)
    if sebum > 0:
        hh = (h * 0.34) * clamp(sebum)
        rrect_on(img, cx - w / 2 + 10, cy + h / 2 - 10 - hh, cx + w / 2 - 10, cy + h / 2 - 10,
                 12, mix((250, 214, 120), CREAM, 0.05), alpha)
    if sumbat > 0:
        bw = (w - 24) * clamp(sumbat)
        rrect_on(img, cx - bw / 2, cy - h / 2 + 8, cx + bw / 2, cy - h / 2 + 34, 13,
                 mix((70, 60, 55), CREAM, 0.10), alpha)
    if merah > 0:
        for k in range(2):
            f = (tg * 0.6 + k / 2.0) % 1.0
            rr = w * 0.72 + f * 26
            ell(img, cx - rr, cy - 10 - rr, cx + rr, cy - 10 + rr,
                outline=mix(RED, WHITE, f * 0.5), width=max(2, int(S(4 * (1.0 - f)))),
                alpha=alpha * merah * (1.0 - f))
    _lbl(img, cx + w / 2 + 96, cy + h / 2 - 44, "KELENJAR MINYAK", font(FS, 20), MUTED, alpha)
    line_on(img, (cx + 30, cy + h / 2 - 40), (cx + w / 2 + 18, cy + h / 2 - 44),
            MUTED, 2, alpha * 0.7)


def sc_intro_jerawat(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: tekstur kulit makro + kaca pembesar di pori meradang."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 66),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    _kartu9_on(img, 110, 790 + dy, 970, 1590 + dy, q2 * al, tg, aksen=accent, r=40)
    _kulit37(img, 126, 806 + dy, 954, 1574 + dy, q2 * al * 0.9, tg, merah_at=(600, 1190 + dy))
    _folikel37(img, 380, 1190 + dy, 320, q2 * al * 0.9, tg, sebum=0.4)
    ql = esmooth(seg(tl, 0.8, 1.3))
    if ql > 0:
        ell(img, 600 - S(150), 1190 + dy - S(150), 600 + S(150), 1190 + dy + S(150),
            fill=None, outline=mix(accent, INK, 0.15), width=8, alpha=ql * al)
        ell(img, 600 - S(150) + S(18), 1190 + dy - S(150) + S(18), 600 - S(110), 1190 + dy - S(110),
            fill=mix(WHITE, CREAM, 0.2), alpha=ql * al * 0.5)
        line_on(img, (600 + 104, 1190 + dy + 104), (690, 1280 + dy), mix(accent, INK, 0.15), 10, ql * al)
    qn = esmooth(seg(tl, 1.4, 1.8))
    if qn > 0:
        _pop_pill(img, 250, 950 + dy, "9 DARI 10 REMAJA", 24, mix(accent, INK, 0.10), qn * al, qn)
    qk = esmooth(seg(tl, 1.9, 2.3))
    if qk > 0:
        _kinesis_on(img, 540, 1660 + dy, "BUKAN WAJAH KOTOR", qk * al, tg, t0=1.9, fsz=40, col=accent)


def sc_peta37(img, d, sc, tl, dur, tg, accent, al, dy):
    """f1: peta pori - folikel + kelenjar minyak + 4 langkah."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 860 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _kulit37(img, 126, 876 + dy, 544, 1544 + dy, q * al * 0.4, tg)
    _folikel37(img, 335, 1210 + dy, 420, q * al, tg, sebum=0.35)
    _lbl(img, 335, 985 + dy, "PORI", font(FB, 26), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1560 + dy, "FOLIKEL: JALUR KELUAR MINYAK", font(FS, 20), MUTED,
         q * al * seg(tl, 0.7, 1.1))
    for k, (t, ik) in enumerate((("1 HORMON", "thermo"), ("2 SUMBAT", "bolt"),
                                 ("3 BAKTERI", "germ"), ("4 MERADANG", "drop"))):
        qi = esmooth(_dw(tl, dur, 0.30 + k * 0.09, 0.42 + k * 0.09))
        if qi <= 0.01:
            continue
        yy = 950 + k * 170 + dy
        _kartu9_on(img, 640, yy - 62, 950, yy + 62, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 710, yy, 36, mix(accent, INK, 0.08), qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 850, yy, t, font(FB, 27), mix(accent, INK, 0.05), qi * al)
    qz = esmooth(_dw(tl, dur, 0.68, 0.78))
    if qz > 0:
        _pop_pill(img, 790, 1640 + dy, "EMPAT LANGKAH DI PORI KECIL", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_sebum37(img, d, sc, tl, dur, tg, accent, al, dy):
    """f2: pubertas -> androgen -> sebum membanjiri pori."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 860 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _folikel37(img, 335, 1210 + dy, 420, q * al, tg, sebum=0.55 + 0.35 * esmooth(seg(tl, 0.8, 1.8)))
    qh = esmooth(_dw(tl, dur, 0.10, 0.24))
    if qh > 0:
        _ico5(img, "thermo", 760, 990 + dy, 46, mix(accent, INK, 0.08), qh * al, tg,
              pulse=0.4 + 0.4 * math.sin(tg * 2.6))
        _panah_flow_on(img, (760, 1045 + dy), (335, 1450 + dy), qh * al, tg, col=accent,
                       lengkung=0.25, lebar=6)
        _lbl(img, 760, 1060 + dy, "ANDROGEN NAIK", font(FB, 26), mix(accent, INK, 0.05), qh * al)
        _lbl(img, 760, 1095 + dy, "SAAT PUBERTAS", font(FS, 21), MUTED, qh * al)
    qs = esmooth(_dw(tl, dur, 0.40, 0.54))
    if qs > 0:
        _meter_on(img, 780, 1310 + dy, 110, 0.55 + 0.35 * math.sin(tg * 0.7), mix(accent, INK, 0.06), qs * al)
        _lbl(img, 780, 1400 + dy, "LEVEL MINYAK", font(FS, 21), MUTED, qs * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _pop_pill(img, 540, 1640 + dy, "SEBUM BANJIRI PORI DARI BAWAH", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_sumbat37(img, d, sc, tl, dur, tg, accent, al, dy):
    """f3: sel mati menyumbat; komedo hitam = oksidasi, bukan kotoran."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _folikel37(img, 335, 1195 + dy, 420, q * al, tg, sebum=0.75,
               sumbat=0.4 + 0.6 * esmooth(seg(tl, 0.7, 1.5)))
    _detail_on(img, 335, 1060 + dy, 650, 950 + dy, "SUMBATAN TERJADI",
               "sel kulit mati + minyak", q * al * seg(tl, 0.7, 1.1), tg, col=accent, w=290)
    qh = esmooth(seg(tl, 1.1, 1.5))
    if qh > 0:
        _kartu9_on(img, 640, 1080 + dy, 950, 1400 + dy, qh * al, tg, aksen=accent, r=30)
        _hitung_on(img, 795, 1170 + dy, 100, "PERSEN: MINYAK + SEL MATI", qh * al, tg,
                   t0=1.1, fsz=44, col=accent)
        _lbl(img, 795, 1300 + dy, "BUKAN KOTORAN YANG MENEMPEL", font(FS, 21), MUTED, qh * al)
    qz = esmooth(_dw(tl, dur, 0.55, 0.70))
    if qz > 0:
        _stamp_on(img, 790, 1520 + dy, "OKSIDASI!", qz * al, qz, col=accent, fsz=52, rot=-6)
        _lbl(img, 790, 1595 + dy, "HITAM = MINYAK KENA UDARA", font(FS, 21), MUTED, qz * al)


def sc_bakteri37(img, d, sc, tl, dur, tg, accent, al, dy):
    """f4: C. acnes makan sebum -> imun menyerang -> meradang."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 860 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _folikel37(img, 335, 1210 + dy, 420, q * al, tg, sebum=0.85, merah=esmooth(seg(tl, 1.4, 1.9)))
    _kisi_on(img, 126, 876 + dy, 544, 1544 + dy, q * al * 0.3, step=56, col=mix(accent, CREAM, 0.4))
    for k in range(3):
        qi = esmooth(_dw(tl, dur, 0.10 + k * 0.10, 0.24 + k * 0.10))
        if qi <= 0.01:
            continue
        _ico5(img, "germ", 265 + k * 70, 1085 + dy - k * 12, 26 + k * 7, mix(accent, INK, 0.08),
              qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 4 + k))
    _lbl(img, 335, 990 + dy, "CUTIBACTERIUM ACNES MAKAN MINYAK", font(FS, 19),
         mix(accent, INK, 0.08), q * al)
    qi2 = esmooth(_dw(tl, dur, 0.42, 0.56))
    if qi2 > 0:
        _ico5(img, "shield", 780, 1060 + dy, 48, GREEN, qi2 * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3.4))
        _panah_flow_on(img, (730, 1105 + dy), (430, 1180 + dy), qi2 * al, tg, col=GREEN,
                       lengkung=0.22, lebar=6)
        _lbl(img, 800, 1140 + dy, "SISTEM IMUN MENYERANG", font(FB, 25), mix(GREEN, INK, 0.05), qi2 * al)
        _lbl(img, 800, 1175 + dy, "PORI MERADANG: MERAH + BENGKAK", font(FS, 21), MUTED, qi2 * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _pop_pill(img, 540, 1640 + dy, "JADILAH JERAWAT MERAH BENGKAK", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_mitos37(img, d, sc, tl, dur, tg, accent, al, dy):
    """f5: mitos kulit kotor + cokelat; yang memicu = gula."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    for k, (yy, txt) in enumerate(((960, "KULIT KOTOR = JERAWAT"), (1170, "COKELAT = JERAWAT"))):
        qi = esmooth(_dw(tl, dur, 0.06 + k * 0.12, 0.20 + k * 0.12))
        if qi <= 0.01:
            continue
        rrect_on(img, 130, yy - 66, 950, yy + 66, 30, mix(WHITE, accent, 0.14), qi * al,
                 outline=mix(accent, INK, 0.10), width=3)
        paste_c(img, 500, yy, txt, font(FB, 33), mix(accent, INK, 0.10), qi * al)
        qs = esmooth(seg(tl, 0.5 + k * 0.5, 0.9 + k * 0.5))
        if qs > 0:
            _stamp_on(img, 850, yy, "MITOS", qs * al, qs, col=RED, fsz=48, rot=-8)
    _lbl(img, 540, 1255 + dy, "CUCI WAJAH TERLALU SERING = KULIT MAKIN MARAH", font(FS, 22),
         MUTED, q * al * seg(tl, 1.3, 1.7))
    kata = [("GULA", 880, 1360), ("INSULIN", 740, 1430), ("ANDROGEN", 580, 1480), ("MINYAK+", 400, 1500)]
    for k, (t, cx, cy) in enumerate(kata):
        qi = esmooth(seg(tl, 1.8 + k * 0.18, 2.1 + k * 0.18))
        if qi <= 0.01:
            continue
        _pop_pill(img, cx, cy + dy, t, 23, mix(accent, INK, 0.10), qi * al, qi)
        if k < 3:
            _panah_flow_on(img, (cx - 70, cy - 22 + dy), (kata[k + 1][1] + 70, kata[k + 1][2] - 30 + dy),
                           qi * al, tg, col=accent, lengkung=0.2, lebar=5)
    qz = esmooth(_dw(tl, dur, 0.62, 0.75))
    if qz > 0:
        _pop_pill(img, 540, 1660 + dy, "BIANGNYA GULA BERLEBIH - BUKAN COKELATNYA", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_pencet37(img, d, sc, tl, dur, tg, accent, al, dy):
    """f6: bahaya memencet - bakteri masuk, menyebar, cekungan permanen."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _folikel37(img, 335, 1195 + dy, 420, q * al, tg, sebum=0.8, merah=1.0)
    qp = esmooth(seg(tl, 0.5, 0.9))
    if qp > 0:
        _panah_flow_on(img, (170, 1140 + dy), (260, 1195 + dy), qp * al, tg, col=RED,
                       lengkung=-0.15, lebar=8)
        _panah_flow_on(img, (170, 1250 + dy), (260, 1195 + dy), qp * al, tg, col=RED,
                       lengkung=0.15, lebar=8)
        _lbl(img, 168, 1052 + dy, "TEKANAN", font(FB, 23), RED, qp * al)
    for k, (yy, ik, t) in enumerate(((1105, "germ", "BAKTERI MASUK LEBIH DALAM"),
                                     (1250, "drop", "MENULAR KE PORI SEKITAR"),
                                     (1395, "bolt", "CEKUNGAN PERMANEN"))):
        qi = esmooth(_dw(tl, dur, 0.14 + k * 0.12, 0.28 + k * 0.12))
        if qi <= 0.01:
            continue
        _kartu9_on(img, 620, yy - 62, 950, yy + 62, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 690, yy, 36, RED, qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 3.2 + k))
        paste_c(img, 830, yy - 14, t, font(FB, 22), mix(accent, INK, 0.05), qi * al)
    qt = esmooth(_dw(tl, dur, 0.52, 0.64))
    if qt > 0:
        for a, b in (((640, 1470 + dy), (930, 1470 + dy)), ((930, 1470 + dy), (785, 1620 + dy)),
                     ((785, 1620 + dy), (640, 1470 + dy))):
            line_on(img, a, b, mix(accent, INK, 0.15), 4, qt * al)
        _lbl(img, 785, 1540 + dy, "ZONA HIDUNG-BIBIR", font(FS, 21), mix(accent, INK, 0.08), qt * al)
        _lbl(img, 785, 1570 + dy, "TERHUBUNG KE PEMBULUH OTAK", font(FS, 20), MUTED, qt * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.76))
    if qz > 0:
        _stamp_on(img, 400, 1660 + dy, "STOP DIPENCET!", qz * al, qz, col=RED, fsz=52, rot=-7)


def sc_benar37(img, d, sc, tl, dur, tg, accent, al, dy):
    """f7: empat langkah perawatan benar."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    kartu = ((340, 1030, "drop", "CUCI LEMBUT 2X/HARI", "sabun lembut, jangan digosok"),
             (740, 1030, "germ", "BENZOIL PEROKSIDA", "atau asam salisilat"),
             (340, 1370, "thermo", "KOMPRES HANGAT", "bantu sumbat melunak"),
             (740, 1370, "shield", "PIMPLE PATCH", "melindungi dari tangan"))
    for k, (cx, cy, ik, judul, sub) in enumerate(kartu):
        qi = esmooth(_dw(tl, dur, 0.06 + k * 0.10, 0.24 + k * 0.10))
        if qi <= 0.01:
            continue
        _kartu9_on(img, cx - 190, cy - 155, cx + 190, cy + 145, qi * al, tg, aksen=accent, r=34)
        _ico5(img, ik, cx, cy - 62, 44, GREEN, qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 2.8 + k))
        paste_c(img, cx, cy + 18, judul, font(FB, 26), mix(accent, INK, 0.05), qi * al)
        paste_c(img, cx, cy + 66, sub, font(FS, 20), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.50, 0.64))
    if qz > 0:
        _pop_pill(img, 540, 1590 + dy, "PILIH PRODUK NON-KOMEDOGENIK", 24,
                  mix(accent, INK, 0.10), qz * al, qz)
    qn = esmooth(_dw(tl, dur, 0.60, 0.72))
    if qn > 0:
        _lbl(img, 540, 1650 + dy, "JERAWAT BATU / MENETAP DEWASA = DOKTER KULIT", font(FS, 22),
             MUTED, qn * al)


def sc_rangkuman37(img, d, sc, tl, dur, tg, accent, al, dy):
    """f8: papan rangkuman + stamp + konfeti."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _recap_on(img, [("thermo", "Hormon menaikkan minyak"),
                    ("bolt", "Sumbatan: bukan kotoran"),
                    ("germ", "Bakteri makan minyak, imun meradang")],
              q * al, tg, t0=0.5, dt=0.7, col=accent)
    qs = esmooth(seg(tl, 1.0, 1.4))
    if qs > 0:
        _stamp_on(img, 800, 915 + dy, "9/10 REMAJA!", qs * al, qs, col=accent, fsz=42, rot=-6)
    qk = esmooth(seg(tl, 1.5, 1.9))
    if qk > 0:
        _kinesis_on(img, 540, 1655 + dy, "JANGAN DIPENCET - RAWAT BENAR!", qk * al, tg, t0=0.0,
                    fsz=40, col=accent)
    qc = esmooth(_dw(tl, dur, 0.55, 0.72))
    if qc > 0:
        _confetti_on(img, tg, qc * al, n=22)


VISUALS.update({
    "intro_jerawat": sc_intro_jerawat,
    "peta37": sc_peta37,
    "sebum37": sc_sebum37,
    "sumbat37": sc_sumbat37,
    "bakteri37": sc_bakteri37,
    "mitos37": sc_mitos37,
    "pencet37": sc_pencet37,
    "benar37": sc_benar37,
    "rangkuman37": sc_rangkuman37,
})


def _selftest37():
    """Uji cepat adegan Ep37 sebelum dipakai render."""
    names = ["intro_jerawat", "peta37", "sebum37", "sumbat37", "bakteri37", "mitos37",
             "pencet37", "benar37", "rangkuman37"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "JERAWAT?"], "accent": "#8C3A2E"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep37: 9 adegan OK")


# ================================================================ Ep38: baterai
# Tema: baterai & hp - "Kenapa Baterai Cepat Habis Padahal Nggak Dipakai?"
# Fakta: Kompas · Merdeka/Liputan6 · cekhape · netcellindo · IDN Times (riset 22 Sep).


def _hp38(img, cx, cy, w, h, alpha, tg, baterai=0.8, panas=0.0, gelap=0.0, kabel=0.0, lompat=False):
    """Ep38: HP tampak depan - layar + indikator baterai; panas = gelombang uap;
    kabel = charger; lompat = persen indikator melompat-lompat (baterai tua)."""
    if alpha <= 0.01:
        return
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 34,
             mix(INK, CREAM, 0.12), alpha, outline=mix(INK, CREAM, 0.35), width=5)
    sx0, sy0, sx1, sy1 = cx - w / 2 + 14, cy - h / 2 + 18, cx + w / 2 - 14, cy + h / 2 - 18
    layar = mix(INK, WHITE, 0.12) if gelap > 0.5 else WHITE
    rrect_on(img, sx0, sy0, sx1, sy1, 22, mix(layar, CREAM, 0.04), alpha)
    line_on(img, (cx - 34, sy0 + 14), (cx + 34, sy0 + 14), mix(INK, CREAM, 0.45), 5, alpha)
    bw = (sx1 - sx0) * 0.58
    bx0, by = cx - bw / 2, cy - h * 0.16
    bh = h * 0.22
    rrect_on(img, bx0 - 8, by - 8, bx0 + bw + 8, by + bh + 8, 14,
             mix(layar, INK, 0.08), alpha, outline=mix(INK, CREAM, 0.4), width=4)
    warna = GREEN if baterai > 0.4 else ((250, 166, 60) if baterai > 0.2 else RED)
    isi = bw * clamp(baterai)
    if isi > 2:
        rrect_on(img, bx0, by, bx0 + isi, by + bh, 9, warna, alpha)
    persen = int(round(clamp(baterai) * 100))
    if lompat:
        persen = (43, 71, 12, 88)[int(tg * 2.0) % 4]
        warna = RED
    paste_c(img, cx, by + bh + 52, str(persen) + "%", font(FB, 44), mix(warna, INK, 0.15), alpha)
    if panas > 0:
        for k in range(3):
            xo = cx + (k - 1) * w * 0.30
            for i in range(4):
                f = (tg * 0.8 + i / 4.0 + k * 0.2) % 1.0
                yy = sy0 - 14 - f * 54
                half = 15 * (1.0 - f * 0.4)
                line_on(img, (xo - half, yy), (xo + half, yy - 10), RED,
                        5, alpha * panas * (1.0 - f) * 0.9)
        ell(img, cx - w * 0.42, cy - h * 0.52 - 34, cx + w * 0.42, cy - h * 0.52 + 22,
            outline=mix(RED, CREAM, 0.35), width=4, alpha=alpha * panas * (0.55 + 0.45 * math.sin(tg * 3.1)))
    if kabel > 0:
        px = cx + w * 0.42
        line_on(img, (px + 40, cy + h / 2 + 60), (px, cy + h / 2 - 4),
                mix(INK, CREAM, 0.25), 7, alpha * clamp(kabel))
        rrect_on(img, px - 8, cy + h / 2 - 16, px + 8, cy + h / 2 + 2, 4,
                 mix(INK, CREAM, 0.2), alpha * clamp(kabel))
        _ico5(img, "bolt", px + 52, cy + h / 2 + 78, 30, GREEN, alpha * clamp(kabel), tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3.4))


def _sel38(img, cx, cy, w, h, alpha, tg, arah=1.0):
    """Ep38: sel lithium-ion - dua elektroda + ion berpindah (arah 1 = mengisi)."""
    if alpha <= 0.01:
        return
    rrect_on(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 24,
             mix(WHITE, CREAM, 0.2), alpha, outline=mix(INK, CREAM, 0.4), width=4)
    for xx, kol in ((cx - w / 2 + 22, (96, 66, 46)), (cx + w / 2 - 22, (43, 108, 140))):
        rrect_on(img, xx - 11, cy - h / 2 + 16, xx + 11, cy + h / 2 - 16, 8,
                 mix(kol, CREAM, 0.15), alpha)
    for k in range(4):
        f = (tg * 0.35 + k / 4.0) % 1.0
        pos = f if arah > 0 else 1.0 - f
        ix = cx - w / 2 + 44 + (w - 88) * pos
        iy = cy - h * 0.28 + h * 0.56 * (0.5 + 0.45 * math.sin(tg * 2.2 + k * 1.9))
        rr = 9 + 2 * math.sin(tg * 4 + k)
        ell(img, ix - rr, iy - rr, ix + rr, iy + rr, fill=(250, 196, 70), alpha=alpha)
    _lbl(img, cx - w / 2 + 24, cy + h / 2 + 30, "ANODA", font(FS, 19), MUTED, alpha)
    _lbl(img, cx + w / 2 - 24, cy + h / 2 + 30, "KATODA", font(FS, 19), MUTED, alpha)


def sc_intro_bat(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: HP ditaruh doang - persen baterai turun sendiri."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 62),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    _kartu9_on(img, 110, 790 + dy, 970, 1590 + dy, q2 * al, tg, aksen=accent, r=40)
    bat = 0.78 - 0.62 * esmooth(seg(tl, 0.9, 2.6)) * (0.9 + 0.1 * math.sin(tg * 1.3))
    _hp38(img, 360, 1180 + dy, 250, 470, q2 * al, tg, baterai=max(0.08, bat), lompat=False)
    _lbl(img, 360, 1490 + dy, "HP DITARUH. DIAM. GAK DIPAKAI.", font(FS, 22), MUTED,
         q2 * al * seg(tl, 1.2, 1.6))
    qp = esmooth(_dw(tl, dur, 0.5, 0.66))
    if qp > 0:
        _pop_pill(img, 790, 980 + dy, "TAPI PERSEN TURUN?!", 27, mix(accent, INK, 0.10), qp * al, qp)
        _ico5(img, "bolt", 790, 1160 + dy, 46, mix(accent, INK, 0.08), qp * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 2.6))
    qn = esmooth(_dw(tl, dur, 0.68, 0.80))
    if qn > 0:
        _pop_pill(img, 790, 1360 + dy, "ADA PENYEDOT DIAM-DIAM", 24,
                  mix(accent, INK, 0.10), qn * al, qn)
    qk = esmooth(seg(tl, 2.5, 2.9))
    if qk > 0:
        _kinesis_on(img, 540, 1660 + dy, "EMPAT FAKTA BATERAI HP", qk * al, tg, t0=2.5, fsz=40, col=accent)


def sc_ion38(img, d, sc, tl, dur, tg, accent, al, dy):
    """f1: cara kerja lithium-ion + siklus = aus; umur ~500 siklus."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    arah = 1.0 if (tg % 6.0) < 3.0 else -1.0
    _sel38(img, 335, 1120 + dy, 380, 260, q * al, tg, arah=arah)
    _lbl(img, 335, 1420 + dy, "ION LITIUM BOLAK-BALIK", font(FB, 24), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1462 + dy, "ISI = KE KANAN  ·  PAKAI = KE KIRI", font(FS, 19), MUTED,
         q * al * seg(tl, 0.9, 1.3))
    qh = esmooth(_dw(tl, dur, 0.10, 0.24))
    if qh > 0:
        _stamp_on(img, 795, 1010 + dy, "±500 SIKLUS", qh * al, qh, col=accent, fsz=54, rot=-5)
        _lbl(img, 795, 1105 + dy, "UMUR STANDAR BATERAI HP", font(FS, 21), MUTED, qh * al)
    for k, (t, sub) in enumerate((("SETIAP SIKLUS = AUS", "kapasitas turun dikit"),
                                  ("MULAI TUA: TURUN CEPAT", "makin gampang drop"))):
        qi = esmooth(_dw(tl, dur, 0.30 + k * 0.13, 0.44 + k * 0.13))
        if qi <= 0.01:
            continue
        yy = 1290 + k * 170 + dy
        _kartu9_on(img, 630, yy - 56, 960, yy + 56, qi * al, tg, aksen=accent, r=26)
        _ico5(img, "clock", 686, yy, 30, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 852, yy - 12, t, font(FB, 22), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 852, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.74))
    if qz > 0:
        _pop_pill(img, 795, 1620 + dy, "20% -> 80% = CUMA 0,6 SIKLUS", 21,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_sedot38(img, d, sc, tl, dur, tg, accent, al, dy):
    """f2: penyedot diam-diam saat HP tidak dipakai."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _hp38(img, 335, 1150 + dy, 220, 420, q * al, tg, baterai=0.62, gelap=1.0)
    _lbl(img, 335, 1450 + dy, "LAYAR MATI, TAPI...", font(FB, 24), mix(accent, INK, 0.05), q * al)
    for k, (t, ik) in enumerate((("APLIKASI LATAR", "germ"), ("GPS & LOKASI", "eye"),
                                 ("NOTIFIKASI", "bolt"), ("SINYAL LEMAH", "flame"))):
        qi = esmooth(_dw(tl, dur, 0.08 + k * 0.11, 0.22 + k * 0.11))
        if qi <= 0.01:
            continue
        yy = 950 + k * 152 + dy
        _kartu9_on(img, 630, yy - 55, 960, yy + 55, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 33, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3.1 + k))
        paste_c(img, 840, yy, t, font(FB, 25), mix(accent, INK, 0.05), qi * al)
    qz = esmooth(_dw(tl, dur, 0.56, 0.70))
    if qz > 0:
        _stamp_on(img, 770, 1600 + dy, "SINYAL LEMAH = LEBIH BOROS!", qz * al, qz,
                  col=accent, fsz=32, rot=-5)
        _lbl(img, 770, 1672 + dy, "mode pesawat di tempat sinyal nggak keluar", font(FS, 19),
             MUTED, qz * al)


def sc_panas38(img, d, sc, tl, dur, tg, accent, al, dy):
    """f3: panas = musuh utama baterai."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _hp38(img, 335, 1150 + dy, 220, 420, q * al, tg, baterai=0.5,
          panas=esmooth(seg(tl, 0.5, 1.2)) * (0.8 + 0.2 * math.sin(tg * 2.4)))
    _lbl(img, 335, 1450 + dy, "PANAS MEMPERCEPAT TUA", font(FB, 24), mix(RED, INK, 0.15), q * al)
    for k, (t, ik) in enumerate((("CAS + GAME BERAT", "bolt"), ("ATAS KASUR / BANTAL", "moon"),
                                 ("MOBIL TERIK MATAHARI", "flame"))):
        qi = esmooth(_dw(tl, dur, 0.10 + k * 0.12, 0.24 + k * 0.12))
        if qi <= 0.01:
            continue
        yy = 950 + k * 150 + dy
        _kartu9_on(img, 630, yy - 56, 960, yy + 56, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 33, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3.2 + k))
        paste_c(img, 840, yy, t, font(FB, 24), mix(accent, INK, 0.05), qi * al)
    qz = esmooth(_dw(tl, dur, 0.50, 0.62))
    if qz > 0:
        _stamp_on(img, 795, 1420 + dy, "PANAS = MUSUH #1", qz * al, qz, col=RED, fsz=44, rot=-6)
        _lbl(img, 795, 1500 + dy, "LEPAS CASING TEBAL SAAT HP HANGAT", font(FS, 20), MUTED, qz * al)


def sc_mitos38(img, d, sc, tl, dur, tg, accent, al, dy):
    """f4: mitos cas semalaman - auto cut-off; risikonya 100% terus + hangat."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    qi = esmooth(_dw(tl, dur, 0.06, 0.20))
    if qi > 0:
        rrect_on(img, 130, 890 + dy - 66, 950, 890 + dy + 66, 30, mix(WHITE, accent, 0.14),
                 qi * al, outline=mix(accent, INK, 0.10), width=3)
        paste_c(img, 500, 890 + dy, "CAS SEMALAMAN MERUSAK BATERAI", font(FB, 29),
                mix(accent, INK, 0.10), qi * al)
        qs = esmooth(seg(tl, 0.5, 0.9))
        if qs > 0:
            _stamp_on(img, 905, 894 + dy, "MITOS", qs * al, qs, col=RED, fsz=44, rot=-8)
    qf = esmooth(_dw(tl, dur, 0.22, 0.36))
    if qf > 0:
        _kartu9_on(img, 630, 1030 + dy - 60, 960, 1030 + dy + 60, qf * al, tg, aksen=accent, r=26)
        _ico5(img, "shield", 688, 1030 + dy, 34, GREEN, qf * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3.0))
        paste_c(img, 858, 1010 + dy, "HP BERHENTI SENDIRI", font(FB, 22),
                mix(accent, INK, 0.05), qf * al)
        paste_c(img, 858, 1048 + dy, "DI 100% (AUTO CUT-OFF)", font(FS, 20), MUTED, qf * al)
    qt = esmooth(_dw(tl, dur, 0.38, 0.52))
    if qt > 0:
        _kartu9_on(img, 630, 1200 + dy - 60, 960, 1200 + dy + 60, qt * al, tg, aksen=accent, r=26)
        _ico5(img, "flame", 688, 1200 + dy, 34, RED, qt * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3.4))
        paste_c(img, 858, 1180 + dy, "DIPAKSA 100% TERUS =", font(FB, 22),
                mix(accent, INK, 0.05), qt * al)
        paste_c(img, 858, 1218 + dy, "TEGANGAN TINGGI + HANGAT", font(FS, 20), MUTED, qt * al)
    qb = esmooth(_dw(tl, dur, 0.52, 0.66))
    if qb > 0:
        x0, x1, yb = 630, 960, 1400 + dy
        rrect_on(img, x0 - 6, yb - 16, x1 + 6, yb + 16, 16, mix(WHITE, INK, 0.06), qb * al,
                 outline=mix(INK, CREAM, 0.4), width=3)
        zx0 = x0 + (x1 - x0) * 0.20
        zx1 = x0 + (x1 - x0) * 0.80
        rrect_on(img, zx0, yb - 12, zx1, yb + 12, 12, GREEN, qb * al)
        mx = x0 + (x1 - x0) * (0.2 + 0.6 * (0.5 + 0.5 * math.sin(tg * 1.1)))
        ell(img, mx - 10, yb - 26, mx + 10, yb + 26, fill=INK, alpha=qb * al)
        paste_c(img, 795, 1460 + dy, "ZONA AMAN: JAGA 20-80%", font(FB, 25), GREEN, qb * al)
    qz = esmooth(_dw(tl, dur, 0.66, 0.78))
    if qz > 0:
        _pop_pill(img, 795, 1600 + dy, "SESIONAL 100% MASIH WAJAR", 22,
                  mix(accent, INK, 0.10), qz * al, qz)
        _lbl(img, 795, 1668 + dy, "dihindari: sering habis total", font(FS, 19),
             MUTED, qz * al)


def sc_hantu38(img, d, sc, tl, dur, tg, accent, al, dy):
    """f5: persen melompat / mati mendadak = indikator bohong (baterai tua)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _hp38(img, 335, 1120 + dy, 220, 420, q * al, tg, baterai=0.35, lompat=True)
    _lbl(img, 335, 1420 + dy, "PERSEN MELOMPAT-LOMPAT", font(FB, 24), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1462 + dy, "PADAHAL BARU DIISI", font(FS, 20), MUTED, q * al * seg(tl, 0.8, 1.2))
    for k, (t, sub, ik) in enumerate((("KALIBRASI MELESET", "indikator gak akurat", "clock"),
                                      ("RESISTANSI NAIK", "baterai mulai tua", "thermo"))):
        qi = esmooth(_dw(tl, dur, 0.12 + k * 0.14, 0.26 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1000 + k * 200 + dy
        _kartu9_on(img, 630, yy - 70, 960, yy + 70, qi * al, tg, aksen=accent, r=28)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 20, t, font(FB, 24), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 845, yy + 22, sub, font(FS, 20), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.48, 0.60))
    if qz > 0:
        _pop_pill(img, 795, 1440 + dy, "MATI MENDADAK = TANDA KLASIK", 23,
                  mix(RED, WHITE, 0.2), qz * al, qz)
        _lbl(img, 795, 1512 + dy, "persen nggak akurat di baterai tua", font(FS, 21), MUTED, qz * al)


def sc_hemat38(img, d, sc, tl, dur, tg, accent, al, dy):
    """f6: yang benar-benar menghemat baterai."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    kartu = ((340, 1030, "bolt", "MODE HEMAT BATRE", "paling gampang, langsung"),
             (740, 1030, "moon", "LAYAR REDUP + DARK", "layar = pemakan terbesar"),
             (340, 1370, "eye", "GPS HANYA SAAT PAKAI", "lokasi real-time = rakus"),
             (740, 1370, "germ", "TUTUP APLIKASI LATAR", "cek setelan baterai HP"))
    for k, (cx, cy, ik, judul, sub) in enumerate(kartu):
        qi = esmooth(_dw(tl, dur, 0.06 + k * 0.10, 0.24 + k * 0.10))
        if qi <= 0.01:
            continue
        _kartu9_on(img, cx - 190, cy - 155, cx + 190, cy + 145, qi * al, tg, aksen=accent, r=34)
        _ico5(img, ik, cx, cy - 62, 44, GREEN, qi * al, tg, pulse=0.5 + 0.5 * math.sin(tg * 2.8 + k))
        paste_c(img, cx, cy + 18, judul, font(FB, 24), mix(accent, INK, 0.05), qi * al)
        paste_c(img, cx, cy + 66, sub, font(FS, 20), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.50, 0.62))
    if qz > 0:
        _pop_pill(img, 540, 1630 + dy, "UPDATE SISTEM = EFISIENSI BATERAI NAIK", 24,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_ganti38(img, d, sc, tl, dur, tg, accent, al, dy):
    """f7: tanda baterai harus diganti."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    kartu = ((340, 1030, "clock", "KAPASITAS DI BAWAH 80%", "cek menu kesehatan baterai"),
             (740, 1030, "bolt", "MATI MENDADAK", "padahal indikator masih ada"),
             (340, 1370, "drop", "BOROS SEJAK BANGUN", "turun puluhan persen semalam"),
             (740, 1370, "flame", "BENTUK MENGGEMBUNG", "bahaya! ganti segera"))
    for k, (cx, cy, ik, judul, sub) in enumerate(kartu):
        qi = esmooth(_dw(tl, dur, 0.06 + k * 0.10, 0.24 + k * 0.10))
        if qi <= 0.01:
            continue
        _kartu9_on(img, cx - 190, cy - 155, cx + 190, cy + 145, qi * al, tg, aksen=accent, r=34)
        _ico5(img, ik, cx, cy - 62, 44, RED if k == 3 else mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 2.8 + k))
        paste_c(img, cx, cy + 18, judul, font(FB, 23), mix(accent, INK, 0.05), qi * al)
        paste_c(img, cx, cy + 66, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.50, 0.62))
    if qz > 0:
        _stamp_on(img, 540, 1630 + dy, "KEMBUNG = GANTI SEGERA!", qz * al, qz, col=RED, fsz=42, rot=-6)


def sc_rangkuman38b(img, d, sc, tl, dur, tg, accent, al, dy):
    """rangkuman: papan 3 fakta + stamp + konfeti."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _recap_on(img, [("germ", "Penyedot diam-diam: latar, GPS, sinyal lemah"),
                    ("flame", "Panas = musuh utama umur baterai"),
                    ("shield", "Cas semalaman aman - jaga zona 20-80%")],
              q * al, tg, t0=0.5, dt=0.7, col=accent)
    qs = esmooth(seg(tl, 1.0, 1.4))
    if qs > 0:
        _pop_pill(img, 540, 1585 + dy, "PERSEN MELOMPAT = TANDA BATERAI TUA", 24,
                  mix(accent, INK, 0.10), qs * al, qs)
    qk = esmooth(seg(tl, 1.5, 1.9))
    if qk > 0:
        _kinesis_on(img, 540, 1655 + dy, "BATERAI AWET, HP JUGA AWET!", qk * al, tg, t0=0.0,
                    fsz=40, col=accent)
    qc = esmooth(_dw(tl, dur, 0.55, 0.72))
    if qc > 0:
        _confetti_on(img, tg, qc * al, n=22)


VISUALS.update({
    "intro_bat": sc_intro_bat,
    "ion38": sc_ion38,
    "sedot38": sc_sedot38,
    "panas38": sc_panas38,
    "mitos38": sc_mitos38,
    "hantu38": sc_hantu38,
    "hemat38": sc_hemat38,
    "ganti38": sc_ganti38,
    "rangkuman38b": sc_rangkuman38b,
})


def _selftest38b():
    """Uji cepat adegan Ep38 baterai sebelum dipakai render."""
    names = ["intro_bat", "ion38", "sedot38", "panas38", "mitos38",
             "hantu38", "hemat38", "ganti38", "rangkuman38b"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["KENAPA", "BATRE CEPAT HABIS?"], "accent": "#9A5B1F"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep38b: 9 adegan OK")



# ================================================================ MESIN v10
# Upgrade Sep 2026: anti-zona-kosong - setiap adegan punya lapisan ambien
# (bokeh + plus melayang) dan elemen mengisi seluruh bidang kanvas.


def _ambien10(img, x0, y0, x1, y1, alpha, tg, col=None, n=12, seed=1):
    """v10: lapisan ambien - bokeh + plus kecil melayang pelan mengisi area kosong.
    Deterministik (seed) supaya stabil antar frame; selalu di dalam kotak aman."""
    if alpha <= 0.01:
        return
    col = col or mix(INK, CREAM, 0.48)
    span = max(50, y1 - y0)
    for k in range(n):
        fx = ((k * 127 + seed * 31) % 97) / 97.0
        fy = ((k * 211 + seed * 17) % 89) / 89.0
        sp = 0.10 + 0.16 * ((k * 53 + seed) % 7) / 7.0
        xx = x0 + (x1 - x0) * fx + math.sin(tg * sp + k) * 14
        yy = y0 + ((fy * span - tg * 16.0 * sp) % span)
        rr = 3 + 3 * ((k + seed) % 4)
        a = alpha * (0.48 + 0.17 * math.sin(tg * 1.3 + k * 1.7))
        if a <= 0.01:
            continue
        if k % 5 == 0:
            line_on(img, (xx - rr, yy), (xx + rr, yy), col, 3, a)
            line_on(img, (xx, yy - rr), (xx, yy + rr), col, 3, a)
        else:
            ell(img, xx - rr, yy - rr, xx + rr, yy + rr, fill=col, alpha=a)


def _langit39(img, x0, y0, x1, y1, alpha, tg, streak=1.0, r=26):
    """v10: langit malam dalam kartu - bintang berkelip + meteor streak melintas.
    streak = fase lintasan 0..1; digambar DI DALAM kotak (bukan overlay layar)."""
    if alpha <= 0.01:
        return
    rrect_on(img, x0, y0, x1, y1, r, (30, 42, 66), alpha,
             outline=mix((30, 42, 66), WHITE, 0.35), width=4)
    for k in range(26):
        fx = ((k * 89 + 13) % 101) / 101.0
        fy = ((k * 173 + 47) % 97) / 97.0
        sx = x0 + 24 + (x1 - x0 - 48) * fx
        sy = y0 + 20 + (y1 - y0 - 40) * fy * 0.92
        tw = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(tg * (1.1 + 0.5 * (k % 5)) + k * 2.1))
        rr = 2.4 + 1.6 * (k % 3)
        ell(img, sx - rr, sy - rr, sx + rr, sy + rr, fill=(240, 244, 250), alpha=alpha * tw)
    if streak > 0:
        f = clamp(streak)
        sx = x0 + 60 + (x1 - x0 - 200) * f
        sy = y0 + 40 + (y1 - y0 - 170) * (1.0 - f) * 0.75
        for i in range(9):
            back = i * 17.0
            a = alpha * (1.0 - i / 9.0) * 0.95
            w = max(2, int(6 - i * 0.55))
            line_on(img, (sx - back, sy + back * 0.62), (sx - back - 16, sy + back * 0.62 + 10),
                    mix((255, 244, 200), (120, 190, 225), i / 9.0), w, a)
        hd = 8 + 3 * math.sin(tg * 9)
        ell(img, sx - hd, sy - hd, sx + hd, sy + hd, fill=(255, 248, 214), alpha=alpha)
        ell(img, sx - hd * 0.4, sy - hd * 0.4, sx + hd * 0.4, sy + hd * 0.4, fill=WHITE, alpha=alpha)
        glow = 22 + 5 * math.sin(tg * 7)
        ell(img, sx - glow, sy - glow, sx + glow, sy + glow,
            outline=(255, 240, 180), width=3, alpha=alpha * 0.5)


def _komet39(img, cx, cy, rr, alpha, tg, arah=1.0):
    """v10: komet - bola es debu + ekor partikel menjauhi matahari."""
    if alpha <= 0.01:
        return
    for i in range(7):
        f = i / 7.0
        xx = cx - arah * (rr + 14 + f * rr * 2.6)
        yy = cy + math.sin(tg * 2.0 + i) * 6 - f * 6
        pr = rr * 0.22 * (1.0 - f * 0.5)
        ell(img, xx - pr, yy - pr, xx + pr, yy + pr,
            fill=mix((150, 200, 230), WHITE, 0.3), alpha=alpha * (1.0 - f) * 0.85)
    ell(img, cx - rr, cy - rr, cx + rr, cy + rr, fill=mix((126, 168, 196), CREAM, 0.12), alpha=alpha)
    ell(img, cx - rr * 0.55, cy - rr * 0.55, cx + rr * 0.25, cy + rr * 0.15,
        fill=mix(WHITE, (126, 168, 196), 0.3), alpha=alpha * 0.8)


# ================================================================ Ep39: meteor
# Tema: meteor & komet - "Itu Bukan Bintang Jatuh" + hujan meteor Orionids 21-22 Okt.
# Fakta: Kompas/BRIN (meteor hijau Yogya Jul 2026) · NASA via Media Indonesia · IDN Times.


def sc_intro_meteor(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: langit malam + meteor melintas - itu bukan bintang jatuh."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 62),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    _ambien10(img, 60, 620, 1020, 760, al * esmooth(seg(tl, 0.3, 0.9)), tg, seed=5, n=8)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    _kartu9_on(img, 110, 790 + dy, 970, 1560 + dy, q2 * al, tg, aksen=accent, r=40)
    _langit39(img, 126, 806 + dy, 954, 1544 + dy, q2 * al, tg,
              streak=(tg * 0.24) % 1.6 if tg > 1.0 else 0.0)
    qp = esmooth(_dw(tl, dur, 0.5, 0.66))
    if qp > 0:
        _pop_pill(img, 400, 1480 + dy, "BUKAN BINTANG. BUKAN RAMALAN.", 25,
                  mix(WHITE, CREAM, 0.15), qp * al, qp, fg=mix(INK, accent, 0.2))
    qn = esmooth(_dw(tl, dur, 0.66, 0.78))
    if qn > 0:
        _pop_pill(img, 770, 900 + dy, "KERIKIL SEUKURAN PASIR", 23,
                  mix(WHITE, CREAM, 0.15), qn * al, qn, fg=mix(INK, accent, 0.2))
    qk = esmooth(seg(tl, 2.5, 2.9))
    if qk > 0:
        _kinesis_on(img, 540, 1660 + dy, "KENAPA BISA JATUH & MENYALA?", qk * al, tg, t0=2.5,
                    fsz=40, col=accent)


def sc_jalur39(img, d, sc, tl, dur, tg, accent, al, dy):
    """f1: tiga nama: meteoroid -> meteor -> meteorit."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=2, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _langit39(img, 126, 846 + dy, 544, 1330 + dy, q * al, tg, streak=(tg * 0.3) % 1.4, r=20)
    ell(img, 236, 1420 + dy - 66, 434, 1420 + dy + 66, fill=mix((126, 168, 120), CREAM, 0.35), alpha=q * al)
    ell(img, 236, 1420 + dy - 66, 434, 1420 + dy + 66, outline=mix(INK, CREAM, 0.3), width=4, alpha=q * al)
    _lbl(img, 335, 1420 + dy, "BUMI", font(FB, 22), mix(INK, CREAM, 0.1), q * al)
    for k, (t, sub, ik) in enumerate((("METEOROID", "di angkasa", "moon"),
                                      ("METEOR", "menyala di atmosfer", "bolt"),
                                      ("METEORIT", "sampai ke tanah", "bone"))):
        qi = esmooth(_dw(tl, dur, 0.14 + k * 0.14, 0.28 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 950 + k * 190 + dy
        _kartu9_on(img, 630, yy - 66, 960, yy + 66, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 848, yy - 18, t, font(FB, 27), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 848, yy + 24, sub, font(FS, 20), MUTED, qi * al)
        if k < 2:
            _panah_flow_on(img, (795, yy + 72), (795, yy + 112), qi * al, tg, col=accent,
                           lengkung=0.0, lebar=5)
    qz = esmooth(_dw(tl, dur, 0.62, 0.74))
    if qz > 0:
        _pop_pill(img, 795, 1620 + dy, "SEUKURAN BUTIR PASIR - BUKAN BINTANG", 22,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_nyala39(img, d, sc, tl, dur, tg, accent, al, dy):
    """f2: kenapa menyala - menukik 66 km/dtk, udara diimpres, habis di ~50 km."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=7, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    for k in range(3):
        f = (tg * 0.5 + k / 3.0) % 1.0
        mx = 230 + 200 * f
        my = 900 + dy + 480 * f * f
        for i in range(5):
            back = i * 13.0
            line_on(img, (mx - back, my - back * 0.62), (mx - back - 12, my - back * 0.62 - 7),
                    mix((255, 244, 200), (120, 190, 225), i / 5.0), max(2, int(5 - i)), q * al * (1 - i / 5.0))
        ell(img, mx - 7, my - 7, mx + 7, my + 7, fill=(255, 248, 214), alpha=q * al)
    line_on(img, (150, 985 + dy), (520, 985 + dy), MUTED, 2, q * al * 0.8)
    _lbl(img, 335, 960 + dy, "120 KM: MULAI MENYALA", font(FS, 20), MUTED, q * al)
    line_on(img, (150, 1470 + dy), (520, 1470 + dy), MUTED, 2, q * al * 0.8)
    _lbl(img, 335, 1500 + dy, "±50 KM: UMUMNYA HABIS", font(FS, 20), MUTED, q * al)
    qh = esmooth(_dw(tl, dur, 0.10, 0.24))
    if qh > 0:
        _hitung_on(img, 795, 1000 + dy, 66, "KECEPATAN MENUKIK", qh * al, tg,
                   t0=0.1, fsz=56, col=accent)
    for k, (t, sub, ik) in enumerate((("UDARA DIMPRES", "terkompresi, panas luar biasa", "thermo"),
                                      ("BATU TERKIKIS", "menyala jadi garis cahaya", "flame"))):
        qi = esmooth(_dw(tl, dur, 0.32 + k * 0.14, 0.46 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1250 + k * 175 + dy
        _kartu9_on(img, 630, yy - 62, 960, yy + 62, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 35, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 848, yy - 16, t, font(FB, 25), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 848, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.76))
    if qz > 0:
        _pop_pill(img, 795, 1620 + dy, "BUKAN DISEKAT - DIMPRES SAMA UDARA", 22,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_warna39(img, d, sc, tl, dur, tg, accent, al, dy):
    """f3: warna = unsur kimia (kembang api alam) + kasus meteor hijau Yogya."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1620, q * al * 0.7, tg, seed=4, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    for k, warna in enumerate(((86, 214, 130), (255, 176, 76), (214, 116, 106), (120, 190, 225))):
        f = (tg * 0.5 + k / 4.0) % 1.0
        sx = 190 + f * 400
        sy = 960 + dy + k * 40 + 300 * f
        for i in range(5):
            back = i * 12.0
            line_on(img, (sx - back, sy - back * 0.5), (sx - back - 11, sy - back * 0.5 - 6),
                    warna, max(2, int(5 - i)), q * al * (1 - i / 5.0))
        ell(img, sx - 6, sy - 6, sx + 6, sy + 6, fill=warna, alpha=q * al)
    _lbl(img, 335, 1470 + dy, "SATU LANGIT, EMPAT WARNA", font(FB, 24), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1512 + dy, "SETIAP UNSUR PUNYA SPEKTRUM", font(FS, 20), MUTED, q * al)
    for k, (w, t, sub) in enumerate((((86, 214, 130), "MAGNESIUM", "hijau terang"),
                                     ((255, 176, 76), "BESI", "kuning-oranye"),
                                     ((214, 116, 106), "KALSIUM", "oranye kemerahan"),
                                     ((120, 190, 225), "NIKEL", "hijau kebiruan"))):
        qi = esmooth(_dw(tl, dur, 0.10 + k * 0.11, 0.24 + k * 0.11))
        if qi <= 0.01:
            continue
        yy = 950 + k * 128 + dy
        rrect_on(img, 636, yy - 42, 716, yy + 42, 20, w, qi * al)
        paste_c(img, 856, yy - 12, t, font(FB, 25), mix(w, INK, 0.25), qi * al)
        paste_c(img, 856, yy + 26, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.58, 0.70))
    if qz > 0:
        _stamp_on(img, 795, 1530 + dy, "MIRIP KEMBANG API!", qz * al, qz, col=accent, fsz=38, rot=-5)
        _lbl(img, 795, 1605 + dy, "meteor hijau Yogya = kaya magnesium", font(FS, 19),
             MUTED, qz * al)


def sc_hujan39(img, d, sc, tl, dur, tg, accent, al, dy):
    """f4: hujan meteor - bumi menyeberangi jejak debu komet; ORIONIDS dari Halley."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=9, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    ell(img, 150, 1290 + dy - 84, 330, 1290 + dy + 84, fill=mix((126, 168, 120), CREAM, 0.35), alpha=q * al)
    ell(img, 150, 1290 + dy - 84, 330, 1290 + dy + 84, outline=mix(INK, CREAM, 0.3), width=4, alpha=q * al)
    _lbl(img, 240, 1290 + dy, "BUMI", font(FB, 22), mix(INK, CREAM, 0.1), q * al)
    for k in range(9):
        f = (tg * 0.4 + k / 9.0) % 1.0
        px = 400 + f * 140
        py = 950 + dy + f * 480
        pr = 5 - 2 * f
        ell(img, px - pr, py - pr, px + pr, py + pr, fill=(150, 200, 230), alpha=q * al * (1 - f))
    _komet39(img, 470, 950 + dy, 26, q * al * seg(tl, 0.7, 1.2), tg, arah=1.0)
    _lbl(img, 470, 900 + dy, "JEJAK DEBU KOMET", font(FS, 19), MUTED, q * al * seg(tl, 0.9, 1.3))
    qh = esmooth(_dw(tl, dur, 0.10, 0.24))
    if qh > 0:
        _hitung_on(img, 795, 1000 + dy, 20, "METEOR PER JAM PUNCAK", qh * al, tg,
                   t0=0.1, fsz=58, col=accent)
    for k, (t, sub, ik) in enumerate((("ORIONIDS", "puncak 21-22 Oktober", "flame"),
                                      ("INDUK: KOMET HALLEY", "jejak debu 76 tahunan", "moon"))):
        qi = esmooth(_dw(tl, dur, 0.32 + k * 0.14, 0.46 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1250 + k * 175 + dy
        _kartu9_on(img, 630, yy - 62, 960, yy + 62, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 35, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 848, yy - 16, t, font(FB, 25), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 848, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.76))
    if qz > 0:
        _pop_pill(img, 795, 1620 + dy, "BULAN INI PUNCAKNYA - NONTON!", 23,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_beda39(img, d, sc, tl, dur, tg, accent, al, dy):
    """f5: komet vs asteroid vs meteor - jangan tertukar."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 80, 830, 1000, 1620, q * al * 0.6, tg, seed=6, n=9)
    kartu = ((340, 1010, "KOMET", "bola es + debu", "punya ekor saat dekat matahari", "moon"),
             (740, 1010, "ASTEROID", "batu raksasa", "kebanyakan di sabuk Mars-Jupiter", "bone"),
             (540, 1380, "METEOR", "kilatan cahaya", "bukan benda, tapi peristiwa", "bolt"))
    for k, (cx, cy, t, s1, s2, ik) in enumerate(kartu):
        qi = esmooth(_dw(tl, dur, 0.06 + k * 0.11, 0.24 + k * 0.11))
        if qi <= 0.01:
            continue
        _kartu9_on(img, cx - 190, cy - 128, cx + 190, cy + 122, qi * al, tg, aksen=accent, r=34)
        _ico5(img, ik, cx, cy - 52, 42, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 2.8 + k))
        paste_c(img, cx, cy + 12, t, font(FB, 30), mix(accent, INK, 0.05), qi * al)
        paste_c(img, cx, cy + 54, s1, font(FB, 21), MUTED, qi * al)
        paste_c(img, cx, cy + 84, s2, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.55, 0.68))
    if qz > 0:
        _pop_pill(img, 540, 1600 + dy, "YANG MELINTAS DI LANGIT: METEOR (PERISTIWA)", 23,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_mitos39(img, d, sc, tl, dur, tg, accent, al, dy):
    """f6: mitos ramalan bintang jatuh - dibongkar."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 80, 830, 1000, 1620, q * al * 0.6, tg, seed=8, n=9)
    qi = esmooth(_dw(tl, dur, 0.06, 0.20))
    if qi > 0:
        rrect_on(img, 130, 890 + dy - 66, 950, 890 + dy + 66, 30, mix(WHITE, accent, 0.14),
                 qi * al, outline=mix(accent, INK, 0.10), width=3)
        paste_c(img, 500, 890 + dy, "BINTANG JATUH = RAMALAN?", font(FB, 33),
                mix(accent, INK, 0.10), qi * al)
        qs = esmooth(seg(tl, 0.5, 0.9))
        if qs > 0:
            _stamp_on(img, 905, 894 + dy, "MITOS", qs * al, qs, col=RED, fsz=44, rot=-8)
    for k, (t, sub, ik) in enumerate((("BINTANG", "gas raksasa bertahun-cahaya", "moon"),
                                      ("METEOR", "kerikil pasir yang terbakar", "bolt"))):
        qi2 = esmooth(_dw(tl, dur, 0.24 + k * 0.14, 0.38 + k * 0.14))
        if qi2 <= 0.01:
            continue
        yy = 1070 + k * 200 + dy
        _kartu9_on(img, 630, yy - 70, 960, yy + 70, qi2 * al, tg, aksen=accent, r=28)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi2 * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 848, yy - 20, t, font(FB, 26), mix(accent, INK, 0.05), qi2 * al)
        paste_c(img, 848, yy + 22, sub, font(FS, 19), MUTED, qi2 * al)
    qp = esmooth(_dw(tl, dur, 0.54, 0.66))
    if qp > 0:
        _pop_pill(img, 540, 1490 + dy, "KEINGINAN BOLEH - RAMALANNYA ENGGAK ADA", 24,
                  mix(accent, INK, 0.10), qp * al, qp, fg=WHITE)
        _lbl(img, 540, 1560 + dy, "yang lewat malam ini bisa jadi debu Halley usia ribuan tahun", font(FS, 19),
             MUTED, qp * al)


def sc_nonton39(img, d, sc, tl, dur, tg, accent, al, dy):
    """f7: panduan nonton Orionids 21-22 Okt."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    kartu = ((340, 1010, "clock", "21-22 OKTOBER", "puncak Orionids 2026", "jam terbaik tengah malam-subuh"),
             (740, 1010, "eye", "CARI TEMPAT GELAP", "jauh dari lampu kota", "langit makin gelap makin banyak"),
             (340, 1390, "moon", "MATA ISTIRAHAT 20 MENIT", "biar adaptasi gelap", "jangan sibuk megang hp"),
             (740, 1390, "bolt", "CUKUP MATA TELANJANG", "tanpa alat", "hadap timur, punggung ke bulan"))
    for k, (cx, cy, ik, t, s1, s2) in enumerate(kartu):
        qi = esmooth(_dw(tl, dur, 0.06 + k * 0.10, 0.24 + k * 0.10))
        if qi <= 0.01:
            continue
        _kartu9_on(img, cx - 190, cy - 148, cx + 190, cy + 142, qi * al, tg, aksen=accent, r=34)
        _ico5(img, ik, cx, cy - 58, 42, GREEN if k > 1 else mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 2.8 + k))
        paste_c(img, cx, cy + 6, t, font(FB, 23), mix(accent, INK, 0.05), qi * al)
        paste_c(img, cx, cy + 48, s1, font(FS, 19), MUTED, qi * al)
        paste_c(img, cx, cy + 78, s2, font(FS, 17), MUTED, qi * al)
    _ambien10(img, 80, 830, 1000, 940, q * al * 0.8, tg, seed=3, n=6)
    qz = esmooth(_dw(tl, dur, 0.50, 0.62))
    if qz > 0:
        _stamp_on(img, 540, 1620 + dy, "ORIONID: TERCEPAT 66 KM/DTK!", qz * al, qz, col=accent, fsz=36, rot=-5)


def sc_rangkuman39b(img, d, sc, tl, dur, tg, accent, al, dy):
    """rangkuman: papan 3 fakta + stamp + konfeti + ambien."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 80, 830, 1000, 1620, q * al * 0.8, tg, seed=11, n=10)
    _recap_on(img, [("moon", "Bintang jatuh = kerikil angkasa menyala"),
                    ("thermo", "Udara diimpres, warna dari unsur kimia"),
                    ("bolt", "Orionids: jejak Halley, puncak 21-22 Okt")],
              q * al, tg, t0=0.5, dt=0.7, col=accent)
    qs = esmooth(seg(tl, 1.0, 1.4))
    if qs > 0:
        _pop_pill(img, 540, 1585 + dy, "PATUT DILIHAT, BUKAN DITAKUTI", 24,
                  mix(accent, INK, 0.10), qs * al, qs)
    qk = esmooth(seg(tl, 1.5, 1.9))
    if qk > 0:
        _kinesis_on(img, 540, 1655 + dy, "MALAM INI, ALIHKAN PANDANGAN KE ATAS!", qk * al, tg,
                    t0=0.0, fsz=38, col=accent)
    qc = esmooth(_dw(tl, dur, 0.55, 0.72))
    if qc > 0:
        _confetti_on(img, tg, qc * al, n=22)


VISUALS.update({
    "intro_meteor": sc_intro_meteor,
    "jalur39": sc_jalur39,
    "nyala39": sc_nyala39,
    "warna39": sc_warna39,
    "hujan39": sc_hujan39,
    "beda39": sc_beda39,
    "mitos39": sc_mitos39,
    "nonton39": sc_nonton39,
    "rangkuman39b": sc_rangkuman39b,
})


def _selftest39():
    """Uji cepat adegan Ep39 sebelum dipakai render."""
    names = ["intro_meteor", "jalur39", "nyala39", "warna39", "hujan39",
             "beda39", "mitos39", "nonton39", "rangkuman39b"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["ITU BUKAN", "BINTANG JATUH"], "accent": "#2C4A6E"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep39: 9 adegan OK")

# ================================================================ Ep40: gerhana
# Tema: "Gerhana Bukan Kiamat" - bayangan bulan & bumi, bulan darah, keselamatan mata.
# Fakta: NU/BRIN (gerhana bulan total 3 Mar 2026) · CNBC (jadwal GMT: cincin 2031,
# total 2042 utk Indonesia) · sains klasik: umbra/penumbra, Rayleigh, retinopati.


def _sun40(img, cx, cy, r, alpha, tg):
    """Matahari mini: cakram hangat + sinar berdenyut."""
    if alpha <= 0.01:
        return
    for k in range(10):
        a = tg * 0.9 + k * 0.6283
        x1 = cx + (r + 8) * math.cos(a)
        y1 = cy + (r + 8) * math.sin(a)
        rr = r * (1.16 + 0.08 * math.sin(tg * 3 + k))
        line_on(img, (x1, y1), (cx + rr * math.cos(a), cy + rr * math.sin(a)),
                (255, 196, 92), 4, alpha * 0.85)
    ell(img, cx - r, cy - r, cx + r, cy + r, fill=(255, 214, 120), alpha=alpha)
    ell(img, cx - r * 0.62, cy - r * 0.62, cx + r * 0.18, cy + r * 0.05,
        fill=(255, 238, 190), alpha=alpha * 0.8)


def _earth40(img, cx, cy, r, alpha, tg, lbl="BUMI"):
    """Bumi mini (sama gaya Ep39) + label opsional."""
    if alpha <= 0.01:
        return
    ell(img, cx - r, cy - r, cx + r, cy + r, fill=mix((126, 168, 120), CREAM, 0.35), alpha=alpha)
    ell(img, cx - r, cy - r, cx + r, cy + r, outline=mix(INK, CREAM, 0.3), width=4, alpha=alpha)
    ell(img, cx - r * 0.5, cy - r * 0.4, cx - r * 0.05, cy + 0.1 * r,
        fill=mix((150, 200, 230), WHITE, 0.2), alpha=alpha * 0.7)
    if lbl:
        _lbl(img, cx, cy, lbl, font(FB, 20), mix(INK, CREAM, 0.1), alpha)


def _moon40(img, cx, cy, r, alpha, tg, ecl=0.0, red=0.0, sky=(30, 42, 66)):
    """Bulan mini. ecl 0..1 = cakupan bayangan bumi; red 0..1 = fase merah darah."""
    if alpha <= 0.01:
        return
    col = mix((242, 236, 214), (168, 62, 44), clamp(red))
    ell(img, cx - r, cy - r, cx + r, cy + r, fill=col, alpha=alpha)
    for dx, dy, cr in ((-0.34, -0.22, 0.16), (0.2, 0.18, 0.12), (-0.05, 0.38, 0.1)):
        px, py, pr = cx + dx * r, cy + dy * r, cr * r
        ell(img, px - pr, py - pr, px + pr, py + pr,
            fill=mix(col, INK, 0.12), alpha=alpha * (0.6 - 0.3 * clamp(red)))
    if ecl > 0.01:
        sxx = cx + r * (2.6 - 2.6 * clamp(ecl / 0.92) * 2.0 / 2.0 * (clamp(ecl / 0.92)))
        sxx = cx + r * (2.6 - 5.2 * clamp(ecl / 0.92)) * 0.5 + r * 1.3 - r * 2.6 * clamp(ecl / 0.92)
        sxx = cx + r * 2.6 - r * 5.2 * clamp(ecl / 0.92)
        ell(img, sxx - r * 1.05, cy - r * 1.05, sxx + r * 1.05, cy + r * 1.05,
            fill=sky, alpha=alpha * clamp(ecl * 1.8))


def _umbra40(img, x_tip, y_tip, x_awal, y_c, r_bumi, r_ujung, alpha, warna=(26, 34, 52)):
    """Kerucut bayangan inti (umbra) dari tepi bumi menuju titik ujung."""
    if alpha <= 0.01:
        return
    poly_on(img, [(x_awal, y_c - r_bumi), (x_tip, y_tip), (x_awal, y_c + r_bumi)],
            warna, alpha * 0.9)


def sc_intro_gerhana(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: bulan tertutup bayangan perlahan - gerhana bukan kiamat."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 62),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    _ambien10(img, 60, 620, 1020, 760, al * esmooth(seg(tl, 0.3, 0.9)), tg, seed=5, n=8)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    _kartu9_on(img, 110, 790 + dy, 970, 1560 + dy, q2 * al, tg, aksen=accent, r=40)
    _langit39(img, 126, 806 + dy, 954, 1544 + dy, q2 * al, tg, streak=0.0)
    e = (tg * 0.13) % 1.25
    _moon40(img, 540, 1160 + dy, 150, q2 * al, tg, ecl=e,
            red=clamp((e - 0.8) / 0.45), sky=(30, 42, 66))
    qp = esmooth(_dw(tl, dur, 0.5, 0.66))
    if qp > 0:
        _pop_pill(img, 540, 1480 + dy, "INI CUMA SOAL BAYANGAN", 25,
                  mix(WHITE, CREAM, 0.15), qp * al, qp, fg=mix(INK, accent, 0.2))
    qk = esmooth(seg(tl, 2.5, 2.9))
    if qk > 0:
        _kinesis_on(img, 540, 1660 + dy, "SIAPA YANG 'MEMAKAN' BULAN?", qk * al, tg, t0=2.5,
                    fsz=40, col=accent)


def sc_segil40(img, d, sc, tl, dur, tg, accent, al, dy):
    """f1: gerhana bulan - matahari, bumi, bulan segaris; bumi yang membuat bayangan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=2, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _sun40(img, 190, 1195 + dy, 74, q * al, tg)
    line_on(img, (300, 1195 + dy), (520, 1195 + dy), (255, 214, 130), 5, q * al * 0.6)
    _earth40(img, 400, 1195 + dy, 52, q * al, tg, lbl="")
    _umbra40(img, 560, 1195 + dy, 452, 1195 + dy, 52, 0, q * al)
    _moon40(img, 528, 1195 + dy, 22, q * al, tg, ecl=0.55, red=0.15, sky=mix(WHITE, CREAM, 0.4))
    _lbl(img, 335, 1500 + dy, "MATAHARI - BUMI - BULAN", font(FB, 23), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1400 + dy, "SEGARIS DI LANGIT", font(FS, 20), MUTED, q * al)
    for k, (t, sub, ik) in enumerate((("MATAHARI", "sumber cahaya", "flame"),
                                      ("BUMI", "membuat bayangan", "shield"),
                                      ("BULAN", "masuk ke bayangan", "moon"))):
        qi = esmooth(_dw(tl, dur, 0.14 + k * 0.14, 0.28 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 950 + k * 190 + dy
        _kartu9_on(img, 630, yy - 66, 960, yy + 66, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 18, t, font(FB, 26), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 845, yy + 24, sub, font(FS, 20), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.74))
    if qz > 0:
        _pop_pill(img, 795, 1620 + dy, "GERHANA BULAN: BUMI DI TENGAH", 22,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_dua40(img, d, sc, tl, dur, tg, accent, al, dy):
    """f2: dua arah gerhana - bulan di tengah (matahari) vs bumi di tengah (bulan)."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 80, 830, 1000, 1620, q * al * 0.6, tg, seed=6, n=9)
    for k, (cx, judul, sub, ik) in enumerate((
            (340, "GERHANA BULAN", "bumi di tengah, malam hari", "moon"),
            (740, "GERHANA MATAHARI", "bulan di tengah, siang hari", "flame"))):
        qi = esmooth(_dw(tl, dur, 0.06 + k * 0.12, 0.24 + k * 0.12))
        if qi <= 0.01:
            continue
        _kartu9_on(img, cx - 190, 880 + dy, cx + 190, 1140 + dy, qi * al, tg, aksen=accent, r=34)
        _sun40(img, cx - 120, 950 + dy, 24, qi * al, tg)
        if k == 0:
            _earth40(img, cx + 6, 950 + dy, 28, qi * al, tg, lbl="")
            _moon40(img, cx + 110, 950 + dy, 14, qi * al, tg, ecl=0.5,
                    sky=mix(WHITE, CREAM, 0.4))
        else:
            _moon40(img, cx + 6, 950 + dy, 22, qi * al, tg, sky=mix(WHITE, CREAM, 0.4))
            _earth40(img, cx + 120, 950 + dy, 17, qi * al, tg, lbl="")
        paste_c(img, cx, 1035 + dy, judul, font(FB, 26), mix(accent, INK, 0.05), qi * al)
        paste_c(img, cx, 1080 + dy, sub, font(FS, 19), MUTED, qi * al)
    qi = esmooth(_dw(tl, dur, 0.34, 0.5))
    if qi > 0.01:
        _kartu9_on(img, 290, 1230 + dy, 790, 1430 + dy, qi * al, tg, aksen=accent, r=30)
        _ico5(img, "eye", 380, 1330 + dy, 40, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 2.8))
        paste_c(img, 640, 1288 + dy, "BAYANGAN BULAN ITU SEMPIT", font(FB, 24), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 640, 1333 + dy, "cuma jalur kecil yang kebagian gelap", font(FS, 19), MUTED, qi * al)
        paste_c(img, 640, 1372 + dy, "sisa wilayah tetap terang", font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.6, 0.72))
    if qz > 0:
        _pop_pill(img, 540, 1540 + dy, "SAMA-SAMA CUMA BAYANGAN", 23,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_bay40(img, d, sc, tl, dur, tg, accent, al, dy):
    """f3: umbra vs penumbra -> total, sebagian, cincin."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=4, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _earth40(img, 230, 1190 + dy, 62, q * al, tg, lbl="")
    _umbra40(img, 520, 1190 + dy, 292, 1190 + dy, 62, 0, q * al)
    poly_on(img, [(292, 1190 + dy - 62), (520, 1190 + dy - 118), (520, 1190 + dy + 118),
                  (292, 1190 + dy + 62)], mix((26, 34, 52), WHITE, 0.55), q * al * 0.5)
    _moon40(img, 496, 1190 + dy, 20, q * al, tg, sky=mix(WHITE, CREAM, 0.4))
    _lbl(img, 335, 960 + dy, "UMBRA: INTI GELAP", font(FB, 22), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1490 + dy, "PENUMBRA: SAMAR", font(FB, 22), MUTED, q * al)
    for k, (t, sub, ik) in enumerate((("TOTAL", "masuk bayangan inti", "moon"),
                                      ("SEBAGIAN", "hanya bayangan samar", "drop"),
                                      ("CINCIN", "bulan jauh, inti tak sampai", "bolt"))):
        qi = esmooth(_dw(tl, dur, 0.12 + k * 0.13, 0.26 + k * 0.13))
        if qi <= 0.01:
            continue
        yy = 980 + k * 190 + dy
        _kartu9_on(img, 630, yy - 66, 960, yy + 66, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 18, t, font(FB, 26), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 845, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.6, 0.72))
    if qz > 0:
        _pop_pill(img, 795, 1620 + dy, "JENISNYA TETNTUAN POSISI KITA", 22,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_darah40(img, d, sc, tl, dur, tg, accent, al, dy):
    """f4: bulan darah - atmosfer bumi menyaring biru, merah lolos."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=7, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    g = seg(tl, 0.6, 3.2)
    _moon40(img, 400, 1150 + dy, 100, q * al, tg, ecl=0.35, red=g, sky=mix(WHITE, CREAM, 0.4))
    for k in range(6):
        f = k / 5.0
        yy = 950 + dy + f * 60
        line_on(img, (180, yy), (280 + f * 60, 1120 + dy - 30 + f * 40),
                mix((200, 225, 250), (255, 150, 90), f), 5, q * al * (0.5 + 0.5 * f))
    ell(img, 150, 1290 + dy - 84, 330, 1290 + dy + 84, outline=(150, 190, 230), width=6, alpha=q * al * 0.8)
    _lbl(img, 240, 1290 + dy, "ATMOSFER", font(FB, 20), mix(INK, CREAM, 0.1), q * al)
    _lbl(img, 335, 1470 + dy, "MERAH LOLOS, BIRU DITELAN", font(FB, 22), mix(accent, INK, 0.05), q * al)
    for k, (t, sub, ik) in enumerate((("FILTER ALAMI", "menyaring cahaya matahari", "drop"),
                                      ("SEKALIGUS", "pantulan sunset seluruh dunia", "flame"))):
        qi = esmooth(_dw(tl, dur, 0.12 + k * 0.14, 0.26 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1010 + k * 190 + dy
        _kartu9_on(img, 630, yy - 66, 960, yy + 66, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 18, t, font(FB, 26), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 845, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.56, 0.68))
    if qz > 0:
        _stamp_on(img, 795, 1500 + dy, "BULAN DARAH!", qz * al, qz, col=accent, fsz=40, rot=-6)
        _lbl(img, 795, 1580 + dy, "tetap aman dilihat mata telanjang", font(FS, 19),
             MUTED, qz * al)


def sc_aman40(img, d, sc, tl, dur, tg, accent, al, dy):
    """f5: gerhana matahari bahaya dilihat langsung; gerhana bulan aman."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=9, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _ico5(img, "eye", 335, 1150 + dy, 86, mix(accent, INK, 0.08), q * al, tg,
          pulse=0.5 + 0.5 * math.sin(tg * 2.4))
    for k in range(5):
        f = k / 4.0
        line_on(img, (150, 1060 + dy + f * 180), (270, 1150 + dy),
                (255, 176, 76), 4, q * al * 0.75)
    line_on(img, (270, 1150 + dy), (300, 1150 + dy), (214, 116, 106), 7, q * al)
    ell(img, 292, 1142 + dy, 308, 1158 + dy, fill=(214, 116, 106), alpha=q * al)
    _lbl(img, 335, 1300 + dy, "RETINA TERFOKUS", font(FB, 24), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1350 + dy, "TERBAKAR TANPA TERASA", font(FB, 22), mix(RED, INK, 0.2), q * al)
    for k, (t, sub, ik, aman) in enumerate((("GERHANA BULAN: AMAN", "boleh mata telanjang", "moon", True),
                                            ("GERHANA MATAHARI", "pakai pelindung khusus", "shield", False))):
        qi = esmooth(_dw(tl, dur, 0.12 + k * 0.14, 0.26 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1030 + k * 200 + dy
        _kartu9_on(img, 630, yy - 70, 960, yy + 70, qi * al, tg, aksen=accent, r=28)
        _ico5(img, ik, 700, yy, 36, GREEN if aman else mix(RED, INK, 0.15), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 20, t, font(FB, 24), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 845, yy + 22, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.56, 0.68))
    if qz > 0:
        _pop_pill(img, 795, 1560 + dy, "KACAMATA HITAM BIASA TIDAK CUKUP", 22,
                  mix(RED, INK, 0.2), qz * al, qz, fg=WHITE)


def sc_jarang40(img, d, sc, tl, dur, tg, accent, al, dy):
    """f6: orbit bulan miring 5 derajat - bayangan biasanya meleset."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=8, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _earth40(img, 335, 1210 + dy, 56, q * al, tg, lbl="")
    a = tg * 1.1
    mx, my = 335 + 165 * math.cos(a), 1210 + dy + 58 * math.sin(a) + 34 * math.cos(a)
    ell(img, 170, 1210 + dy - 58, 500, 1210 + dy + 58, outline=MUTED, width=3, alpha=q * al * 0.55)
    ell(img, 170, 1210 + dy - 92, 500, 1210 + dy + 24, outline=accent, width=4, alpha=q * al * 0.85)
    _moon40(img, mx, my, 16, q * al, tg, sky=mix(WHITE, CREAM, 0.4))
    for nx in (213, 457):
        ell(img, nx - 9, 1210 + dy - 9, nx + 9, 1210 + dy + 9, fill=accent, alpha=q * al)
    _lbl(img, 335, 960 + dy, "ORBIT BULAN MIRING 5 DERAJAT", font(FB, 21), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1490 + dy, "TITIK TEMU = TEMPAT GERHANA", font(FS, 20), MUTED, q * al)
    qh = esmooth(_dw(tl, dur, 0.10, 0.24))
    if qh > 0:
        _hitung_on(img, 795, 1000 + dy, 5, "DERAJAT KEMIRINGAN", qh * al, tg,
                   t0=0.1, fsz=60, col=accent)
    for k, (t, sub, ik) in enumerate((("BAYANGAN MELESET", "biasanya meleset lewat atas", "bone"),
                                      ("TIAP BULAN?", "tidak - harus di titik temu", "clock"))):
        qi = esmooth(_dw(tl, dur, 0.32 + k * 0.14, 0.46 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1250 + k * 175 + dy
        _kartu9_on(img, 630, yy - 62, 960, yy + 62, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 35, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 16, t, font(FB, 24), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 845, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.76))
    if qz > 0:
        _pop_pill(img, 795, 1620 + dy, "MAKANYA GERHANA ITU JARANG", 22,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_mitos40(img, d, sc, tl, dur, tg, accent, al, dy):
    """f7: mitos gerhana dibongkar + jadwal Indonesia."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 80, 830, 1000, 1620, q * al * 0.6, tg, seed=8, n=9)
    qi = esmooth(_dw(tl, dur, 0.06, 0.20))
    if qi > 0:
        rrect_on(img, 130, 890 + dy - 66, 950, 890 + dy + 66, 30, mix(WHITE, accent, 0.14),
                 qi * al, outline=mix(accent, INK, 0.10), width=3)
        paste_c(img, 500, 890 + dy, "GERHANA = PERTANDA BURUK?", font(FB, 33),
                mix(accent, INK, 0.10), qi * al)
        qs = esmooth(seg(tl, 0.5, 0.9))
        if qs > 0:
            _stamp_on(img, 905, 894 + dy, "MITOS", qs * al, qs, col=RED, fsz=44, rot=-8)
    for k, (t, sub, ik) in enumerate((("RAKSASA TELAN MATAHARI", "cerita lama, tidak ada buktinya", "eye"),
                                      ("BAHAYA UNTUK IBU HAMIL", "tidak ada dasar medisnya", "heart"))):
        qi2 = esmooth(_dw(tl, dur, 0.24 + k * 0.14, 0.38 + k * 0.14))
        if qi2 <= 0.01:
            continue
        yy = 1070 + k * 190 + dy
        _kartu9_on(img, 630, yy - 66, 960, yy + 66, qi2 * al, tg, aksen=accent, r=28)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi2 * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 20, t, font(FB, 22), mix(accent, INK, 0.05), qi2 * al)
        paste_c(img, 845, yy + 22, sub, font(FS, 19), MUTED, qi2 * al)
    qp = esmooth(_dw(tl, dur, 0.54, 0.66))
    if qp > 0:
        _pop_pill(img, 540, 1470 + dy, "GERHANA CUMA GEOMETRI LANGIT", 24,
                  mix(accent, INK, 0.10), qp * al, qp)
        _lbl(img, 540, 1545 + dy, "Indonesia berikutnya: cincin 2031, total 2042", font(FS, 19),
             MUTED, qp * al)


def sc_rangkuman40b(img, d, sc, tl, dur, tg, accent, al, dy):
    """rangkuman: papan 3 fakta + stamp + konfeti + ambien."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 80, 830, 1000, 1620, q * al * 0.8, tg, seed=11, n=10)
    _recap_on(img, [("moon", "Gerhana = bayangan saat langit segaris"),
                    ("drop", "Bulan merah = pantulan sunset dunia"),
                    ("shield", "Gerhana matahari wajib pelindung mata")],
              q * al, tg, t0=0.5, dt=0.7, col=accent)
    qs = esmooth(seg(tl, 1.0, 1.4))
    if qs > 0:
        _pop_pill(img, 540, 1585 + dy, "BUKAN KIAMAT - CUMA GEOMETRI", 24,
                  mix(accent, INK, 0.10), qs * al, qs)
    qk = esmooth(seg(tl, 1.5, 1.9))
    if qk > 0:
        _kinesis_on(img, 540, 1655 + dy, "CATAT: CINCIN 2031, TOTAL 2042!", qk * al, tg,
                    t0=0.0, fsz=38, col=accent)
    qc = esmooth(_dw(tl, dur, 0.55, 0.72))
    if qc > 0:
        _confetti_on(img, tg, qc * al, n=22)


VISUALS.update({
    "intro_gerhana": sc_intro_gerhana,
    "segil40": sc_segil40,
    "dua40": sc_dua40,
    "bay40": sc_bay40,
    "darah40": sc_darah40,
    "aman40": sc_aman40,
    "jarang40": sc_jarang40,
    "mitos40": sc_mitos40,
    "rangkuman40b": sc_rangkuman40b,
})


def _selftest40():
    """Uji cepat adegan Ep40 sebelum dipakai render."""
    names = ["intro_gerhana", "segil40", "dua40", "bay40", "darah40",
             "aman40", "jarang40", "mitos40", "rangkuman40b"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["GERHANA,", "BUKAN KIAMAT"], "accent": "#2C4A6E"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep40: 9 adegan OK")

# ================================================================ Ep41: hantu
# Tema: "Itu Bukan Hantu, Itu Otakmu" - sains di balik penampakan.
# Fakta: CNN Indonesia/Halodoc/IDN Times (sleep paralysis REM atonia) · Vic Tandy 1998
# 19 Hz · Frontiers 2026 via Ars Technica (kortisol naik saat infrasonik) · kumparan (pareidolia).


def _figur41(img, cx, cy, s, alpha, tg):
    """Ilustrasi tindihan: orang terlentang + mata terbuka + kunci REM + Zzz."""
    if alpha <= 0.01:
        return
    rrect_on(img, cx - 170 * s, cy + 10 * s, cx + 170 * s, cy + 92 * s, 26 * s,
             mix((214, 200, 168), CREAM, 0.35), alpha, outline=mix(INK, CREAM, 0.3), width=3)
    r = 26 * s
    ell(img, cx - 150 * s - r, cy - 14 * s - r, cx - 150 * s + r, cy - 14 * s + r,
        fill=mix((232, 190, 150), CREAM, 0.25), alpha=alpha)
    rrect_on(img, cx - 120 * s, cy - 16 * s, cx + 90 * s, cy + 22 * s, 20 * s,
             mix((110, 140, 180), WHITE, 0.2), alpha)
    for k in range(2):
        ell(img, cx - 156 * s + k * 20 * s - 3 * s, cy - 20 * s - 3 * s,
            cx - 156 * s + k * 20 * s + 3 * s, cy - 20 * s + 3 * s, fill=INK, alpha=alpha)
    paste_c(img, cx - 40 * s, cy + 2 * s, "KUNCI REM: AKTIF", font(FB, 15 * max(1, s)),
            mix(INK, CREAM, 0.05), alpha)
    for k in range(3):
        zz = "Z" * (1 + k)
        paste_c(img, cx + 120 * s + k * 20 * s, cy - 30 * s - k * 26 * s + math.sin(tg * 2 + k) * 3,
                zz, font(FB, int(20 * s + k * 4)), MUTED, alpha * (0.9 - k * 0.25))


def _gel41(img, cx, cy, alpha, tg, col):
    """Gelombang infrasonik: bar vertikal berdenyut + kipas sumber."""
    if alpha <= 0.01:
        return
    for k in range(13):
        h = 26 + 30 * (0.5 + 0.5 * math.sin(tg * 1.4 + k * 0.9))
        x = cx - 180 + k * 30
        line_on(img, (x, cy - h), (x, cy + h), mix(col, INK, 0.1), 7, alpha * 0.85)
    a = tg * 2.2
    ell(img, cx + 150 - 30, cy - 30 - 40, cx + 150 + 30, cy + 30 - 40,
        outline=MUTED, width=4, alpha=alpha)
    for k in range(3):
        ang = a + k * 2.094
        line_on(img, (cx + 150, cy - 40), (cx + 150 + 26 * math.cos(ang), cy - 40 + 26 * math.sin(ang)),
                MUTED, 5, alpha)
    _lbl(img, cx + 150, cy + 4 - 40, "KIPAS", font(FS, 15), MUTED, alpha)


def sc_intro_hantu(img, d, sc, tl, dur, tg, accent, al, dy):
    """Intro: kartu malam + sosok samar yang sebenarnya gorden - itu otakmu."""
    for i, l in enumerate(sc.get("lines") or []):
        q = seg(tl, 0.15 + i * 0.22, 0.62 + i * 0.22)
        if q <= 0:
            continue
        _pop_txt(img, 540, (500 + i * 104) + dy, l, _fit_line(l, FB if i == 0 else FS, 100 if i == 0 else 62),
                 INK if i == 0 else mix(accent, INK, 0.05), al, q, dy=0)
    _ambien10(img, 60, 620, 1020, 760, al * esmooth(seg(tl, 0.3, 0.9)), tg, seed=5, n=8)
    q2 = esmooth(seg(tl, 0.35, 1.0))
    if q2 <= 0.02:
        return
    _kartu9_on(img, 110, 790 + dy, 970, 1560 + dy, q2 * al, tg, aksen=accent, r=40)
    _langit39(img, 126, 806 + dy, 954, 1544 + dy, q2 * al, tg, streak=0.0)
    qf = esmooth(seg(tl, 0.9, 1.4))
    if qf > 0:
        sx = 640 + math.sin(tg * 0.7) * 16
        for i in range(6):
            f = i / 5.0
            ww = 70 - f * 34
            ell(img, sx - ww, 1210 + dy - 10 - f * 130, sx + ww, 1210 + dy + 24 - f * 130,
                fill=mix((30, 42, 66), WHITE, 0.10 + f * 0.05), alpha=qf * al * (0.85 - f * 0.4))
        ell(img, sx - 20, 1136 + dy - 9, sx + 20, 1136 + dy + 9, fill=(240, 244, 250), alpha=qf * al * 0.75)
    qp = esmooth(_dw(tl, dur, 0.5, 0.66))
    if qp > 0:
        _pop_pill(img, 540, 1480 + dy, "TAPI KENAPA TERASA NYATA?", 25,
                  mix(WHITE, CREAM, 0.15), qp * al, qp, fg=mix(INK, accent, 0.2))
    qk = esmooth(seg(tl, 2.5, 2.9))
    if qk > 0:
        _kinesis_on(img, 540, 1660 + dy, "SAINS PUNYA JAWABANNYA", qk * al, tg, t0=2.5,
                    fsz=40, col=accent)


def sc_tindih41(img, d, sc, tl, dur, tg, accent, al, dy):
    """f1: tindihan = paralisis tidur; otak bangun, badan masih dikunci REM."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=2, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _figur41(img, 335, 1150 + dy, 1.0, q * al, tg)
    _lbl(img, 335, 1330 + dy, "SADAR, TAPI TAK BISA GERAK", font(FB, 20), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1470 + dy, "BEDETIK-MENIT, HILANG SENDIRI", font(FS, 18), MUTED, q * al)
    qh = esmooth(_dw(tl, dur, 0.10, 0.24))
    if qh > 0:
        _hitung_on(img, 795, 1000 + dy, 7.6, "PERSEN PERNAH ALAMI", qh * al, tg,
                   t0=0.1, fsz=56, col=accent)
    for k, (t, sub, ik) in enumerate((("OTAK SUDAH BANGUN", "badan masih dikunci REM", "moon"),
                                      ("HALUSINASI SISA MIMPI", "sosok + dada terasa ditekan", "eye"))):
        qi = esmooth(_dw(tl, dur, 0.32 + k * 0.14, 0.46 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1250 + k * 175 + dy
        _kartu9_on(img, 630, yy - 62, 960, yy + 62, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 35, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 848, yy - 16, t, font(FB, 24), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 848, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.76))
    if qz > 0:
        _pop_pill(img, 795, 1620 + dy, "BIOLOGI BIASA - TIDAK BERBAHAYA", 22,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_wajah41(img, d, sc, tl, dur, tg, accent, al, dy):
    """f2: pareidolia - detektor wajah otak terlalu rajin."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=4, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    for j, (bx, by) in enumerate(((220, 1120 + dy), (450, 1120 + dy), (335, 1400 + dy))):
        rrect_on(img, bx - 95, by - 80, bx + 95, by + 80, 24, mix(WHITE, CREAM, 0.4), q * al,
                 outline=mix(INK, CREAM, 0.25), width=3)
        if j == 0:
            for k in range(6):
                line_on(img, (bx - 70 + k * 26, by - 55), (bx - 70 + k * 26, by + 55), MUTED, 4, q * al)
        elif j == 1:
            poly_on(img, [(bx - 60, by - 55), (bx, by + 10), (bx + 60, by - 55)], MUTED, q * al * 0.85)
            poly_on(img, [(bx - 60, by + 55), (bx, by + 6), (bx + 60, by + 55)], MUTED, q * al * 0.5)
        else:
            ell(img, bx - 30, by - 34, bx + 30, by + 26, fill=MUTED, alpha=q * al * 0.6)
            rrect_on(img, bx - 52, by + 30, bx + 52, by + 52, 10, MUTED, q * al * 0.5)
        qq = seg(tl, 1.0 + j * 0.5, 1.5 + j * 0.5)
        if qq > 0:
            ell(img, bx - 44, by - 40, bx + 44, by + 36, outline=mix(RED, WHITE, 0.15), width=4, alpha=qq * al)
            for ex in (-20, 20):
                ell(img, bx + ex - 5, by - 26 - 5, bx + ex + 5, by - 26 + 5, fill=RED, alpha=qq * al)
            ell(img, bx - 8, by + 2, bx + 8, by + 14, outline=RED, width=3, alpha=qq * al)
    _lbl(img, 335, 1530 + dy, "OTAK MELAHIRKAN WAJAH", font(FB, 20), mix(accent, INK, 0.05), q * al)
    for k, (t, sub, ik) in enumerate((("DETEKTOR WAJAH OTAK", "terlalu rajin bekerja", "eye"),
                                      ("POLA BIASA JADI WAJAH", "gorden, jaket, colokan", "brain"))):
        qi = esmooth(_dw(tl, dur, 0.10 + k * 0.14, 0.24 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1010 + k * 190 + dy
        _kartu9_on(img, 630, yy - 66, 960, yy + 66, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 18, t, font(FB, 24), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 845, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.44, 0.56))
    if qz > 0:
        _stamp_on(img, 795, 1450 + dy, "PAREIDOLIA!", qz * al, qz, col=accent, fsz=40, rot=-6)
        _lbl(img, 795, 1530 + dy, "otak membentak: ini wajah!", font(FS, 19), MUTED, qz * al)


def sc_dengar41(img, d, sc, tl, dur, tg, accent, al, dy):
    """f3: infrasonik 19 Hz - merinding tanpa sebab punya tersangka fisika."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    accent_g = accent
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=7, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _gel41(img, 320, 1180 + dy, q * al, tg, accent)
    _lbl(img, 320, 1330 + dy, "TAK TERDENGAR, TAPI DIRASAKAN", font(FB, 19), mix(accent, INK, 0.05), q * al)
    _lbl(img, 320, 1470 + dy, "LAB 'BERHANTU' VIC TANDY, 1998", font(FS, 18), MUTED, q * al)
    qh = esmooth(_dw(tl, dur, 0.10, 0.24))
    if qh > 0:
        _hitung_on(img, 795, 1000 + dy, 19, "HZ: DI BAWAH DENGARAN", qh * al, tg,
                   t0=0.1, fsz=58, col=accent)
    for k, (t, sub, ik) in enumerate((("GELISAH + HORMON STRES", "naik saat infrasonik nyala", "thermo"),
                                      ("MATA IKUT BERGETAR", "sosok samar di sudut mata", "eye"))):
        qi = esmooth(_dw(tl, dur, 0.32 + k * 0.14, 0.46 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1250 + k * 175 + dy
        _kartu9_on(img, 630, yy - 62, 960, yy + 62, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 35, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 848, yy - 16, t, font(FB, 23), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 848, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.64, 0.76))
    if qz > 0:
        _pop_pill(img, 795, 1620 + dy, "SUMBER: KIPAS, PIPA, TRAFIK", 22,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_gelap41(img, d, sc, tl, dur, tg, accent, al, dy):
    """f4: gelap = data berkurang; amigdala menyala duluan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=9, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _ico5(img, "eye", 260, 1120 + dy, 62, mix(accent, INK, 0.08), q * al, tg,
          pulse=0.5 + 0.5 * math.sin(tg * 2.2))
    line_on(img, (200, 1180 + dy), (320, 1180 + dy), MUTED, 4, q * al)
    _lbl(img, 260, 1220 + dy, "DATA: MINIM", font(FB, 20), MUTED, q * al)
    for k in range(4):
        xx = 320 + k * 45
        a2 = tg * 3 + k
        line_on(img, (xx, 1120 + dy - 10 - 20 * abs(math.sin(a2))), (xx, 1120 + dy + 10 + 20 * abs(math.sin(a2))),
                mix(RED, accent, 0.3), 6, q * al * 0.8)
    _ico5(img, "brain", 430, 1120 + dy, 62, mix(RED, accent, 0.25), q * al, tg,
          pulse=0.5 + 0.5 * math.sin(tg * 3.1))
    _lbl(img, 335, 1330 + dy, "GELAP = ALARM OTAK", font(FB, 22), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1470 + dy, "AMIGDALA: PUSAT RASA TAKUT", font(FS, 18), MUTED, q * al)
    for k, (t, sub, ik) in enumerate((("GELAP = DATA MINIM", "otak isi dugaan terburuk", "moon"),
                                      ("AMIGDALA DULUAN", "takut dulu, mikir kemudian", "brain"))):
        qi = esmooth(_dw(tl, dur, 0.10 + k * 0.14, 0.24 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1010 + k * 190 + dy
        _kartu9_on(img, 630, yy - 66, 960, yy + 66, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 18, t, font(FB, 24), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 845, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.44, 0.56))
    if qz > 0:
        _pop_pill(img, 795, 1450 + dy, "MEKANISME SELAMAT - BUKAN HANTU", 22,
                  mix(accent, INK, 0.10), qz * al, qz)
        _lbl(img, 795, 1530 + dy, "yang waspada, yang selamat", font(FS, 19), MUTED, qz * al)


def sc_sugest41(img, d, sc, tl, dur, tg, accent, al, dy):
    """f5: sugesti menular; rekaman 'suara hantu' dibacakan sesuai instruksi."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=6, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    rrect_on(img, 250, 1010 + dy, 420, 1330 + dy, 28, mix((30, 42, 66), WHITE, 0.12), q * al,
             outline=mix(INK, CREAM, 0.3), width=4)
    _ico5(img, "germ", 335, 1170 + dy, 44, mix((30, 42, 66), WHITE, 0.4), q * al, tg,
          pulse=0.5 + 0.5 * math.sin(tg * 2.6))
    for k in range(4):
        f = (tg * 0.5 + k / 4.0) % 1.0
        px = 430 + f * 110
        py = 1060 + k * 70 + 10 * math.sin(tg * 3 + k)
        ell(img, px - 7 - f * 4, py - 7 - f * 4, px + 7 + f * 4, py + 7 + f * 4,
            fill=accent, alpha=q * al * (1 - f))
    _lbl(img, 335, 1390 + dy, "CERITA MENULAR", font(FB, 22), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1470 + dy, "OTAK MENANDAI TEMPAT 'BERBAHAYA'", font(FS, 17), MUTED, q * al)
    for k, (t, sub, ik) in enumerate((("CERITA MENANDAI TEMPAT", "bunyi kecil jadi 'bukti'", "germ"),
                                      ("REKAMAN 'SUARA HANTU'", "dibacakan sesuai instruksi", "bolt"))):
        qi = esmooth(_dw(tl, dur, 0.10 + k * 0.14, 0.24 + k * 0.14))
        if qi <= 0.01:
            continue
        yy = 1010 + k * 190 + dy
        _kartu9_on(img, 630, yy - 66, 960, yy + 66, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 18, t, font(FB, 23), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 845, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.44, 0.56))
    if qz > 0:
        _pop_pill(img, 795, 1450 + dy, "DENGAR DULU BARU MENAFSIR = PRASANGKA", 21,
                  mix(accent, INK, 0.10), qz * al, qz)
        _lbl(img, 795, 1530 + dy, "rumah tua + cerita seram", font(FS, 19), MUTED, qz * al)


def sc_tes41(img, d, sc, tl, dur, tg, accent, al, dy):
    """f6: cek sendiri - sumber rumah, jam tidur, trik ujung jari."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 620, 800, 980, 1600, q * al * 0.7, tg, seed=8, n=7)
    _kartu9_on(img, 110, 830 + dy, 560, 1560 + dy, q * al, tg, aksen=accent)
    _ico5(img, "shield", 335, 1120 + dy, 74, GREEN, q * al, tg,
          pulse=0.5 + 0.5 * math.sin(tg * 2.4))
    for k, txt in enumerate(("KIPAS & PIPA", "JAM TIDUR", "UJUNG JARI")):
        yy = 1280 + dy + k * 62
        line_on(img, (200, yy), (214, yy + 14), GREEN, 5, q * al * seg(tl, 0.6 + k * 0.3, 1.0 + k * 0.3))
        line_on(img, (214, yy + 14), (240, yy - 16), GREEN, 5, q * al * seg(tl, 0.7 + k * 0.3, 1.1 + k * 0.3))
        paste_c(img, 395, yy - 4, txt, font(FB, 22), mix(accent, INK, 0.05), q * al)
    _lbl(img, 335, 1530 + dy, "CEK DULU, KESIMPULAN BELAKANGAN", font(FS, 18), MUTED, q * al)
    for k, (t, sub, ik) in enumerate((("TELUSURI SUMBERNYA", "kipas, pipa, instalasi listrik", "shield"),
                                      ("JAGA JAM TIDUR", "kurang tidur = mudah tindihan", "moon"),
                                      ("TINDIHAN? UJUNG JARI", "gerak kecil = kunci lepas", "bolt"))):
        qi = esmooth(_dw(tl, dur, 0.10 + k * 0.11, 0.24 + k * 0.11))
        if qi <= 0.01:
            continue
        yy = 960 + k * 190 + dy
        _kartu9_on(img, 630, yy - 66, 960, yy + 66, qi * al, tg, aksen=accent, r=26)
        _ico5(img, ik, 700, yy, 36, GREEN if k else mix(accent, INK, 0.08), qi * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 18, t, font(FB, 23), mix(accent, INK, 0.05), qi * al)
        paste_c(img, 845, yy + 24, sub, font(FS, 19), MUTED, qi * al)
    qz = esmooth(_dw(tl, dur, 0.62, 0.74))
    if qz > 0:
        _pop_pill(img, 795, 1620 + dy, "SEBAGIAN BESAR ADA JAWABANNYA", 22,
                  mix(accent, INK, 0.10), qz * al, qz)


def sc_mitos41(img, d, sc, tl, dur, tg, accent, al, dy):
    """f7: takut itu warisan yang menyelamatkan; video beredar sering editan."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 80, 830, 1000, 1620, q * al * 0.6, tg, seed=8, n=9)
    qi = esmooth(_dw(tl, dur, 0.06, 0.20))
    if qi > 0:
        rrect_on(img, 130, 890 + dy - 66, 950, 890 + dy + 66, 30, mix(WHITE, accent, 0.14),
                 qi * al, outline=mix(accent, INK, 0.10), width=3)
        paste_c(img, 500, 890 + dy, "HANTU ITU ADA, DONG?", font(FB, 34),
                mix(accent, INK, 0.10), qi * al)
        qs = esmooth(seg(tl, 0.5, 0.9))
        if qs > 0:
            _stamp_on(img, 905, 894 + dy, "BELUM BUKTI", qs * al, qs, col=RED, fsz=34, rot=-8)
    for k, (t, sub, ik) in enumerate((("TAKUT ITU WARISAN", "penyelamat nenek moyang", "heart"),
                                      ("VIDEO PENAMPAKAN", "seringnya hasil editan", "bolt"))):
        qi2 = esmooth(_dw(tl, dur, 0.24 + k * 0.14, 0.38 + k * 0.14))
        if qi2 <= 0.01:
            continue
        yy = 1070 + k * 190 + dy
        _kartu9_on(img, 630, yy - 66, 960, yy + 66, qi2 * al, tg, aksen=accent, r=28)
        _ico5(img, ik, 700, yy, 36, mix(accent, INK, 0.08), qi2 * al, tg,
              pulse=0.5 + 0.5 * math.sin(tg * 3 + k))
        paste_c(img, 845, yy - 18, t, font(FB, 24), mix(accent, INK, 0.05), qi2 * al)
        paste_c(img, 845, yy + 24, sub, font(FS, 19), MUTED, qi2 * al)
    qp = esmooth(_dw(tl, dur, 0.54, 0.66))
    if qp > 0:
        _pop_pill(img, 540, 1470 + dy, "TAKUT BOLEH - TERTIPU JANGAN", 24,
                  mix(accent, INK, 0.10), qp * al, qp)
        _lbl(img, 540, 1545 + dy, "yang penting sumbernya dicek dulu", font(FS, 19),
             MUTED, qp * al)


def sc_rangkuman41b(img, d, sc, tl, dur, tg, accent, al, dy):
    """rangkuman: papan 3 fakta + pill + kinesis + konfeti."""
    badge_line(img, sc.get("badge", ""), accent, tl, al)
    q = esmooth(seg(tl, 0.05, 0.2)) * esmooth(seg(dur - tl, 0.1, 0.45))
    if q <= 0.02:
        return
    _ambien10(img, 80, 830, 1000, 1620, q * al * 0.8, tg, seed=11, n=10)
    _recap_on(img, [("moon", "Tindihan = kunci mimpi yang lupa dibuka"),
                    ("eye", "Wajah misterius = pareidolia otak"),
                    ("bolt", "Merinding bisa jadi infrasonik 19 Hz")],
              q * al, tg, t0=0.5, dt=0.7, col=accent)
    qs = esmooth(seg(tl, 1.0, 1.4))
    if qs > 0:
        _pop_pill(img, 540, 1585 + dy, "RUMAH PALING 'BERHANTU': OTAKMU", 23,
                  mix(accent, INK, 0.10), qs * al, qs)
    qk = esmooth(seg(tl, 1.5, 1.9))
    if qk > 0:
        _kinesis_on(img, 540, 1655 + dy, "BAGIKAN KE YANG PALING PENAKUT!", qk * al, tg,
                    t0=0.0, fsz=38, col=accent)
    qc = esmooth(_dw(tl, dur, 0.55, 0.72))
    if qc > 0:
        _confetti_on(img, tg, qc * al, n=22)


VISUALS.update({
    "intro_hantu": sc_intro_hantu,
    "tindih41": sc_tindih41,
    "wajah41": sc_wajah41,
    "dengar41": sc_dengar41,
    "gelap41": sc_gelap41,
    "sugest41": sc_sugest41,
    "tes41": sc_tes41,
    "mitos41": sc_mitos41,
    "rangkuman41b": sc_rangkuman41b,
})


def _selftest41():
    """Uji cepat adegan Ep41 sebelum dipakai render."""
    names = ["intro_hantu", "tindih41", "wajah41", "dengar41", "gelap41",
             "sugest41", "tes41", "mitos41", "rangkuman41b"]
    for n in names:
        assert n in VISUALS, n
    img = Image.new("RGB", (int(W * SS), int(H * SS)), CREAM)
    d = ImageDraw.Draw(img)
    sc = {"badge": "UJI", "lines": ["ITU BUKAN HANTU,", "ITU OTAKMU"], "accent": "#5B4A8C"}
    for n in names:
        for tl in (0.5, 3.0, 7.0, 12.0):
            VISUALS[n](img, d, sc, tl, 14.5, tl, hexc(sc["accent"]), 1.0, 0.0)
    print("selftest Ep41: 9 adegan OK")
if __name__ == "__main__":
    _selftest31()
    _selftest_v5()
    _selftest_v6()
    _selftest_v7()
    _selftest_v8()
    _selftest_v9()
    _selftest33()
    _selftest34()
    _selftest35()
    _selftest36()
    _selftest37()
    _selftest38b()
    _selftest39()
    _selftest40()
    _selftest41()



    _selftest32()




