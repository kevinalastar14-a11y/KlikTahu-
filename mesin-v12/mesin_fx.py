#!/usr/bin/env python3
"""MESIN FX 2026 - lapisan efek bersama untuk Shorts (render.py / mesin_v11) dan video
panjang (long/mesin_long.py). Standar motion design September 2026:

  A. FINISHING SINEMATIK (per frame, di resolusi akhir, numpy + LUT -> murah)
     bloom()        pendar cahaya dua skala (soft-knee): lampu, glow, bintang "bernapas" seperti lensa
     grade()        color grading filmic: kurva S, lift/gain, split-toning (bayangan dingin,
                    sorotan hangat), saturasi - preset "sinema" (gelap) & "krem" (Shorts terang)
     lensa()        aberasi kromatik radial halus (pinggir frame saja, seperti lensa asli)
     grain()        butiran film luma, deterministik per frame (bukan jam dinding)
     vinyet()       vinyet elips lembut
  B. GERAK
     zoom_blur()    motion blur radial (dorongan kamera, transisi zoom-through)
     blur_arah()    motion blur arah (whip pan)
     nois()         derau halus 1D (kamera genggam organik, bukan sinus berulang)
     spring()       pegas teredam (overshoot alami untuk pop-in)
  C. MATERIAL & CAHAYA
     kaca_cair()    LIQUID GLASS: latar di belakang panel diburamkan + dibiaskan (lensa
                    tepi), tint, cahaya tepi atas (specular rim), garis tepi bergradasi,
                    bayangan lembut, kilau menyapu opsional
     bayang()       bayangan lembut (drop shadow) untuk sprite RGBA apa pun (ter-cache)
     kilau()        sapuan cahaya diagonal di dalam bentuk sprite (light sweep)
     bokeh()        partikel bokeh latar depan (kedalaman 2.5D)
  D. TRANSISI (dipecah jadi fase KELUAR + MASUK, sehingga bisa dipakai tanpa frame lain)
     trans_keluar() / trans_masuk()  zoomthru | whip | tinta (wipe bentuk) | iris
     trans_dua()    versi dua-frame untuk Shorts (prev + img): zoomthru, tinta, cahaya

Semua fungsi aman: kalau KT_FX=0 di environment, finishing() mengembalikan gambar apa adanya.
"""
import math
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

AKTIF = os.environ.get("KT_FX", "1") != "0"


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def esmooth(t):
    t = clamp(t)
    return t * t * t * (t * (t * 6 - 15) + 10)


def eo(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def spring(t, zeta=0.42, omega=15.0):
    """Pegas teredam: 0 -> melewati 1 sedikit -> mendarat 1. t dalam detik."""
    if t <= 0:
        return 0.0
    if t > 2.5:
        return 1.0
    wd = omega * math.sqrt(1 - zeta * zeta)
    return 1 - math.exp(-zeta * omega * t) * (math.cos(wd * t) + zeta * omega / wd * math.sin(wd * t))


# ================================================================== derau halus
_PERM = np.random.default_rng(2026).permutation(512).astype(np.float64)


def nois(t, seed=0):
    """Value-noise 1D halus (-1..1), periode panjang - untuk kamera genggam organik."""
    x = t + seed * 17.13
    i = math.floor(x)
    f = x - i
    a = (_PERM[int(i) % 512] / 255.5) - 1.0
    b = (_PERM[int(i + 1) % 512] / 255.5) - 1.0
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u


def nois2(t, seed=0):
    """Dua oktaf derau (lebih organik)."""
    return 0.7 * nois(t, seed) + 0.3 * nois(t * 2.3, seed + 5)


_C = {}


def _cache_get(key, fn, limit=600):
    v = _C.get(key)
    if v is None:
        if len(_C) > limit:
            _C.clear()
        v = fn()
        _C[key] = v
    return v


# ================================================================== A. finishing
def _lut_bloom(thr):
    return [int(255 * clamp((v / 255.0 - thr) / max(1e-3, 1 - thr)) ** 1.6) for v in range(256)]


def bloom(img, thr=0.66, kuat=0.55, r1=0.0045, r2=0.018, tint=None, adaptif=True):
    """Pendar cahaya dua skala. thr = ambang kecerahan (0..1) pada kanal TERTERANG (warna jenuh
    ikut berpendar), kuat = intensitas, r1/r2 = radius relatif lebar frame. Semua operasi C (PIL)."""
    if kuat <= 0.01:
        return img
    w, h = img.size
    small = img.reduce(4) if w >= 64 and h >= 64 else img.resize((max(8, w // 4), max(8, h // 4)))
    sw, sh = small.size
    if adaptif:
        # adegan terang (langit, air dangkal, latar krem) -> ambang naik & pendar turun: tidak silau
        mean = sum(small.reduce(8).convert("L").getdata()) / max(1, (sw // 8) * (sh // 8)) / 255.0
        terang = clamp((mean - 0.22) / 0.33)
        thr = thr + (0.95 - thr) * 0.75 * terang
        kuat = kuat * (1 - 0.8 * terang)
        if kuat <= 0.01:
            return img
    r_, g_, b_ = small.split()
    lum = ImageChops.lighter(r_, ImageChops.lighter(g_, b_))
    wg = lum.point(_cache_get(("lb", round(thr, 3)), lambda: _lut_bloom(thr)))
    hi = ImageChops.multiply(small, Image.merge("RGB", (wg, wg, wg)))
    if tint is not None:
        hi = Image.blend(hi, ImageChops.multiply(Image.new("RGB", hi.size, tint), Image.merge("RGB", (wg, wg, wg))), 0.3)
    b1 = hi.filter(ImageFilter.GaussianBlur(max(1.0, w * r1 / 4)))
    s2 = hi.resize((max(4, sw // 4), max(4, sh // 4)), Image.BILINEAR)
    b2 = s2.filter(ImageFilter.GaussianBlur(max(1.0, w * r2 / 16))).resize((sw, sh), Image.BILINEAR)
    k1, k2 = kuat * 0.9, kuat * 1.25
    comb = ImageChops.add(b1.point(_cache_get(("lk", round(k1, 3)), lambda: [int(min(255, v * k1)) for v in range(256)] * 3)),
                          b2.point(_cache_get(("lk", round(k2, 3)), lambda: [int(min(255, v * k2)) for v in range(256)] * 3)))
    return ImageChops.add(img, comb.resize((w, h), Image.BILINEAR))


_PRESET = {
    # gelap/antariksa/laut: kontras filmic, bayangan sedikit biru-teal, sorotan hangat
    "sinema": dict(kontras=0.20, lift=0.012, gain=1.02, gamma=0.98,
                   bayang=(-0.010, 0.006, 0.030), sorot=(0.028, 0.012, -0.020), sat=1.07),
    # Shorts krem terang: hangat lembut, kontras halus, hitam tidak pecah
    "krem": dict(kontras=0.10, lift=0.0, gain=1.0, gamma=1.0,
                 bayang=(0.004, 0.0, 0.016), sorot=(0.010, 0.004, -0.010), sat=1.06),
    "netral": dict(kontras=0.0, lift=0.0, gain=1.0, gamma=1.0, bayang=(0, 0, 0), sorot=(0, 0, 0), sat=1.0),
}


def _lut(nama):
    p = _PRESET[nama]
    x = np.arange(256, dtype=np.float64) / 255.0
    s = x * x * (3 - 2 * x)
    v = x + (s - x) * p["kontras"] * 2.0
    v = np.clip(v, 0, 1) ** p["gamma"]
    v = p["lift"] + v * (p["gain"] - p["lift"])
    out = []
    for ch in range(3):
        c = v + p["bayang"][ch] * (1 - v) ** 2 * 4 * v + p["sorot"][ch] * v * v
        out.append(np.clip(c * 255 + 0.5, 0, 255).astype(np.uint8))
    return np.concatenate(out).tolist()


def grade(img, nama="sinema"):
    lut = _cache_get(("lut", nama), lambda: _lut(nama))
    out = img.point(lut)
    sat = _PRESET[nama]["sat"]
    if abs(sat - 1) > 0.005:
        g = out.convert("L")
        out = Image.blend(Image.merge("RGB", (g, g, g)), out, sat)
    return out


def lensa(img, px=1.6):
    """Aberasi kromatik radial: kanal merah sedikit membesar, biru sedikit mengecil (pusat tetap
    tajam, pinggir frame berpinggiran warna halus)."""
    if px <= 0.2:
        return img
    w, h = img.size
    r, g, b = img.split()

    def z(ch, d):
        k = 1 + 2 * d / w
        cw, chh = w / k, h / k
        x0, y0 = (w - cw) / 2, (h - chh) / 2
        return ch.resize((w, h), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + chh))

    return Image.merge("RGB", (z(r, px), g, _zkecil(b, px)))


def _zkecil(ch, d):
    w, h = ch.size
    k = 1 - 2 * d / w
    nw, nh = int(round(w * k)), int(round(h * k))
    sm = ch.resize((nw, nh), Image.BILINEAR)
    out = ch.copy()
    out.paste(sm, ((w - nw) // 2, (h - nh) // 2))
    return out


def vinyet(img, kuat=0.30, awal=0.55, warna=(0, 0, 0)):
    w, h = img.size

    def mk():
        yy, xx = np.mgrid[0:h // 4, 0:w // 4].astype(np.float32)
        d = np.sqrt(((xx - w / 8) / (w / 8)) ** 2 + ((yy - h / 8) / (h / 8)) ** 2)
        m = np.clip((d - awal) / (1.45 - awal), 0, 1) ** 1.7 * kuat
        return Image.fromarray((m * 255).astype(np.uint8), "L").resize((w, h), Image.BILINEAR)

    m = _cache_get(("vin", w, h, kuat, awal), mk)
    gel = _cache_get(("gel", w, h, warna), lambda: Image.new("RGB", (w, h), warna))
    return Image.composite(gel, img, m)


def grain(img, k, kuat=5.0, ukuran=1.0):
    """Butiran film luma (monokrom, gaussian), 8 varian bergilir per frame (deterministik)."""
    if kuat <= 0.1:
        return img
    w, h = img.size
    v = int(k) % 8

    def mk():
        rng = np.random.default_rng(900 + v)
        sw, sh = int(w / ukuran), int(h / ukuran)
        n = rng.normal(0, kuat, (sh, sw)).astype(np.float32) + 128
        im = Image.fromarray(np.clip(n, 0, 255).astype(np.uint8), "L")
        if (sw, sh) != (w, h):
            im = im.resize((w, h), Image.BILINEAR)
        return Image.merge("RGB", (im, im, im))

    g = _cache_get(("grain", w, h, v, kuat, ukuran), mk, limit=800)
    # overlay: hasil = img + (g - 128)
    return ImageChops.add(img, g, 1.0, -128)


def finishing(img, k, preset="sinema", bloom_kuat=0.55, bloom_thr=0.66, ca=0.0, vin=0.30, grain_kuat=5.0,
              tint=None):
    """Rantai finishing lengkap (urutan seperti kamera + grading): bloom -> grade -> lensa ->
    vinyet -> grain."""
    if not AKTIF:
        return img
    if bloom_kuat > 0.01:
        img = bloom(img, thr=bloom_thr, kuat=bloom_kuat, tint=tint)
    img = grade(img, preset)
    if ca > 0.2:
        img = lensa(img, ca)
    if vin > 0.01:
        img = vinyet(img, vin)
    return grain(img, k, grain_kuat)


# ================================================================== B. gerak
def zoom_blur(img, kuat, cx=0.5, cy=0.5, n=4):
    """Motion blur radial (kuat = perbesaran maks, mis. 0.06). Dihitung di 1/2 resolusi (blur
    memang lembut) lalu dicampur ke gambar asli."""
    if kuat <= 0.004:
        return img
    w, h = img.size
    hw, hh = max(2, w // 2), max(2, h // 2)
    sm = img.resize((hw, hh), Image.BILINEAR)
    acc = None
    for j in range(n):
        k = 1 + kuat * (j + 1) / n
        cw, ch = hw / k, hh / k
        x0 = (hw - cw) * cx
        y0 = (hh - ch) * cy
        z = sm.resize((hw, hh), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
        acc = z if acc is None else Image.blend(acc, z, 1.0 / (j + 1))
    return Image.blend(img, acc.resize((w, h), Image.BILINEAR), 0.8)


def blur_arah(img, px, vertikal=False):
    """Motion blur arah murah: perkecil sumbu gerak -> perbesar kembali + blend geser."""
    if px < 1.5:
        return img
    w, h = img.size
    f = max(1.0, px / 3.0)
    if vertikal:
        sm = img.resize((w, max(2, int(h / f))), Image.BILINEAR).resize((w, h), Image.BILINEAR)
    else:
        sm = img.resize((max(2, int(w / f)), h), Image.BILINEAR).resize((w, h), Image.BILINEAR)
    return sm


# ================================================================== C. material & cahaya
def _rr_mask(w, h, r, ss=1):
    def mk():
        m = Image.new("L", (w * ss, h * ss), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=int(r * ss), fill=255)
        return m.resize((w, h), Image.LANCZOS) if ss > 1 else m
    return _cache_get(("rrm", w, h, int(r), ss), mk)


def _bayang_rr(w, h, r, blur, opa):
    def mk():
        pad = int(blur * 3)
        m = Image.new("L", (w + pad * 2, h + pad * 2), 0)
        ImageDraw.Draw(m).rounded_rectangle([pad, pad, pad + w, pad + h], radius=int(r), fill=int(255 * opa))
        return m.filter(ImageFilter.GaussianBlur(blur)), pad
    return _cache_get(("brr", w, h, int(r), int(blur), round(opa, 2)), mk)


def _rim(w, h, r, tint, terang, acc):
    """Lapisan RGBA: cahaya tepi atas (specular), garis tepi bergradasi, bayang dalam bawah,
    bilah aksen opsional."""
    def mk():
        ss = 2
        W2, H2 = w * ss, h * ss
        lay = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
        # gradasi specular atas: putih 0.20 -> 0 pada 45% tinggi
        g = np.zeros((H2, W2), np.float32)
        yy = np.arange(H2, dtype=np.float32)[:, None] / H2
        xx = np.arange(W2, dtype=np.float32)[None, :] / W2
        g += np.clip(1 - yy / 0.45, 0, 1) ** 2 * (0.16 * terang)
        g += np.clip(1 - yy / 0.06, 0, 1) * (0.10 * terang)
        # kilap sudut kiri atas
        g += np.clip(1 - np.sqrt((xx / 0.35) ** 2 + (yy / 0.5) ** 2), 0, 1) ** 2 * 0.10 * terang
        spec = Image.fromarray(np.clip(g * 255, 0, 255).astype(np.uint8), "L")
        m = _rr_mask(W2, H2, r * ss)
        spec = ImageChops.multiply(spec, m)
        lay.paste(Image.new("RGBA", (W2, H2), (255, 255, 255, 255)), (0, 0), spec)
        dd = ImageDraw.Draw(lay)
        # garis tepi: terang di atas, redup di bawah (gradasi via dua garis bertumpuk + mask)
        edge = Image.new("L", (W2, H2), 0)
        ImageDraw.Draw(edge).rounded_rectangle([1, 1, W2 - 2, H2 - 2], radius=int(r * ss), outline=255,
                                               width=max(2, int(1.3 * ss)))
        grad = Image.fromarray((np.clip(0.62 - yy * 0.48 + 0 * xx, 0.10, 0.62) * 255).astype(np.uint8), "L")
        edge = ImageChops.multiply(edge, grad)
        lay.paste(Image.new("RGBA", (W2, H2), (255, 255, 255, 255)), (0, 0), edge)
        # bayang dalam bawah (memberi ketebalan)
        inner = Image.new("L", (W2, H2), 0)
        ImageDraw.Draw(inner).rounded_rectangle([2, 2, W2 - 3, H2 - 3], radius=int(r * ss), outline=90,
                                                width=max(2, int(3 * ss)))
        inner = ImageChops.multiply(inner, Image.fromarray((np.clip((yy - 0.55) / 0.45, 0, 1) * 255 + 0 * xx)
                                                          .astype(np.uint8), "L"))
        lay.paste(Image.new("RGBA", (W2, H2), (0, 0, 0, 255)), (0, 0), inner)
        if acc:
            dd.rounded_rectangle([0, int(r * ss * 0.75), int(7 * ss), H2 - int(r * ss * 0.75)],
                                 radius=int(3 * ss), fill=acc + (255,))
        return lay.resize((w, h), Image.LANCZOS)
    return _cache_get(("rim", w, h, int(r), tint, round(terang, 2), acc), mk)


def kaca_cair(img, X0, Y0, X1, Y1, r, tint=(16, 18, 42), pekat=0.58, alpha=1.0, acc=None,
              blur=None, refraksi=0.045, terang=1.0, bayang_opa=0.45, sapu=None):
    """LIQUID GLASS dalam piksel kanvas. Latar di bawah panel: diburamkan (blur besar murah via
    downscale), dibiaskan (lensa: diperbesar sedikit ke tengah), diberi tint, lalu cahaya tepi.
    sapu = 0..1 posisi kilau diagonal (None = tanpa)."""
    if alpha <= 0.01:
        return
    X0, Y0, X1, Y1 = int(X0), int(Y0), int(X1), int(Y1)
    w, h = X1 - X0, Y1 - Y0
    if w < 6 or h < 6:
        return
    iw, ih = img.size
    blur = blur or max(6.0, min(w, h) * 0.10)
    # 1) bayangan lembut
    if bayang_opa > 0.01:
        bm, pad = _bayang_rr(w, h, r, max(4.0, min(w, h) * 0.06), bayang_opa)
        oy = int(max(3, h * 0.035))
        m = bm if alpha >= 0.995 else bm.point(lambda v: int(v * alpha))
        img.paste(_cache_get(("hitam", bm.size), lambda: Image.new("RGB", bm.size, (0, 0, 0))),
                  (X0 - pad, Y0 - pad + oy), m)
    # 2) latar terbias + buram
    mg = int(max(w, h) * refraksi) + 2
    bx0, by0 = max(0, X0 - mg), max(0, Y0 - mg)
    bx1, by1 = min(iw, X1 + mg), min(ih, Y1 + mg)
    if bx1 - bx0 < 4 or by1 - by0 < 4:
        return
    crop = img.crop((bx0, by0, bx1, by1))
    f = max(2, int(blur / 2.2))
    sm = crop.resize((max(2, crop.width // f), max(2, crop.height // f)), Image.BILINEAR)
    sm = sm.filter(ImageFilter.GaussianBlur(max(1.0, blur / f)))
    # lensa: area crop (lebih besar dari panel) dipetakan ke ukuran panel -> latar tampak diperkecil
    # sedikit di tengah & "membengkok" di tepi, seperti kaca tebal
    back = sm.resize((w, h), Image.BILINEAR)
    tint_im = _cache_get(("tint", w, h, tint), lambda: Image.new("RGB", (w, h), tint))
    back = Image.blend(back, tint_im, pekat)
    m = _rr_mask(w, h, r)
    if alpha < 0.995:
        m = m.point(lambda v: int(v * alpha))
    img.paste(back, (X0, Y0), m)
    # 3) cahaya tepi + garis + bayang dalam (+ aksen)
    rim = _rim(w, h, r, tint, terang, acc)
    ra = rim.getchannel("A")
    if alpha < 0.995:
        ra = ra.point(lambda v: int(v * alpha))
    img.paste(rim.convert("RGB"), (X0, Y0), ra)
    # 4) kilau menyapu
    if sapu is not None and 0 < sapu < 1:
        _sapu_rr(img, X0, Y0, w, h, r, sapu, alpha * 0.55)


def _sapu_rr(img, X0, Y0, w, h, r, u, alpha):
    bw = max(10, int(w * 0.16))
    x = int(-bw * 2 + (w + bw * 4) * u)

    def band():
        H2 = h
        g = Image.new("L", (bw * 2, H2 * 2), 0)
        arr = np.clip(1 - np.abs(np.linspace(-1, 1, bw * 2)), 0, 1) ** 2
        g = Image.fromarray(np.tile((arr * 255).astype(np.uint8), (H2 * 2, 1)), "L")
        return g.rotate(-18, resample=Image.BICUBIC, expand=False)

    b = _cache_get(("band", bw, h), band)
    m = Image.new("L", (w, h), 0)
    m.paste(b, (x - bw, -h // 2))
    m = ImageChops.multiply(m, _rr_mask(w, h, r))
    m = m.point(lambda v: int(v * alpha))
    img.paste(_cache_get(("putih", w, h), lambda: Image.new("RGB", (w, h), (255, 255, 255))), (X0, Y0), m)


def bayang(lay, blur, opa=0.5, key=None, warna=(0, 0, 0)):
    """Bayangan lembut untuk sprite RGBA -> (sprite_bayang RGBA, pad). Ter-cache via key."""
    def mk():
        pad = int(blur * 2.5) + 2
        a = lay.getchannel("A")
        big = Image.new("L", (lay.width + pad * 2, lay.height + pad * 2), 0)
        big.paste(a, (pad, pad))
        big = big.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * opa))
        out = Image.new("RGBA", big.size, warna + (0,))
        out.putalpha(big)
        return out, pad
    if key is None:
        return mk()
    return _cache_get(("bay", key, int(blur), round(opa, 2), warna), mk, limit=1500)


def kilau(lay, u, lebar=0.22, kuat=0.75, sudut=20):
    """Sapuan cahaya di dalam alpha sprite. u 0..1 (posisi). Mengembalikan sprite baru."""
    if u <= 0 or u >= 1:
        return lay
    w, h = lay.size
    bw = max(6, int(w * lebar))
    x = int(-bw + (w + bw * 2) * u)
    arr = np.clip(1 - np.abs(np.linspace(-1, 1, bw)), 0, 1) ** 1.8
    band = Image.fromarray(np.tile((arr * 255 * kuat).astype(np.uint8), (h * 2, 1)), "L")
    band = band.rotate(-sudut, resample=Image.BICUBIC, expand=True)
    m = Image.new("L", (w, h), 0)
    m.paste(band, (x - band.width // 2, (h - band.height) // 2))
    m = ImageChops.multiply(m, lay.getchannel("A"))
    out = lay.copy()
    out.paste(Image.new("RGBA", (w, h), (255, 255, 255, 255)), (0, 0), m)
    out.putalpha(lay.getchannel("A"))
    return out


def _disk(r, blur, col):
    def mk():
        pad = int(blur * 2.5) + 2
        n = int(r * 2 + pad * 2)
        m = Image.new("L", (n, n), 0)
        ImageDraw.Draw(m).ellipse([pad, pad, pad + 2 * r, pad + 2 * r], fill=255)
        if blur > 0.5:
            m = m.filter(ImageFilter.GaussianBlur(blur))
        out = Image.new("RGBA", (n, n), col + (0,))
        out.putalpha(m)
        return out
    return _cache_get(("disk", int(r), int(blur), col), mk)


def bokeh(img, t, n=10, col=(255, 255, 255), alpha=0.10, seed=7, rmin=10, rmax=46, kec=0.018,
          area=None):
    """Partikel bokeh besar & buram yang melayang pelan (lapisan terdekat ke kamera)."""
    if alpha <= 0.01:
        return
    iw, ih = img.size
    x0, y0, x1, y1 = area or (0, 0, iw, ih)
    rng = np.random.default_rng(seed)
    for j in range(n):
        sx, sy, sr, sp, sa = rng.random(5)
        r = rmin + (rmax - rmin) * sr
        ph = (sy - t * kec * (0.6 + sp)) % 1.0
        x = x0 + (x1 - x0) * ((sx + 0.03 * math.sin(t * 0.3 + j)) % 1.0)
        y = y0 + (y1 - y0 + 2 * r) * ph - r
        tw_ = 0.55 + 0.45 * math.sin(t * (0.6 + sp) + j * 1.7)
        spr = _disk(float(r), float(r) * 0.35, col)
        a = alpha * (0.4 + 0.6 * sa) * tw_
        if a <= 0.004:
            continue
        m = spr.getchannel("A").point(lambda v: int(v * a))
        img.paste(spr.convert("RGB"), (int(x - spr.width / 2), int(y - spr.height / 2)), m)


# ================================================================== D. transisi
def _tinta_mask(w, h, u, seed=3, arah=1):
    """Masker 'tinta'/bentuk menyapu diagonal bertepi bergelombang (0 = belum, 255 = tertutup)."""
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    tot = w + h * 0.6
    x = -h * 0.6 + tot * u * 1.02
    pts = []
    nseg = 14
    for j in range(nseg + 1):
        yy = h * j / nseg
        wob = math.sin(j * 1.9 + seed) * h * 0.035 + math.sin(j * 0.7 + seed * 2) * h * 0.02
        pts.append((x + (h - yy) * 0.6 + wob, yy))
    poly = [(-10, -10)] + [(p[0], p[1]) for p in pts] + [(-10, h + 10)]
    d.polygon(poly, fill=255)
    if arah < 0:
        m = m.transpose(Image.FLIP_LEFT_RIGHT)
    return m


def trans_keluar(out, u, jenis, acc, gelap=(4, 5, 14)):
    """Fase keluar (u 0 -> 1 di akhir adegan)."""
    w, h = out.size
    if jenis == "zoomthru":
        e = u * u
        out = zoom_blur(out, 0.10 + 0.35 * e)
        out = out.resize((w, h), Image.BILINEAR, box=_box_zoom(w, h, 1 + 0.45 * e))
        return Image.blend(out, Image.new("RGB", (w, h), mix(acc, (255, 255, 255), 0.75)), 0.85 * e ** 1.5)
    if jenis == "whip":
        e = u ** 2.2
        dx = int(-w * 0.35 * e)
        out = blur_arah(out, 90 * e)
        sh = Image.new("RGB", (w, h), gelap)
        sh.paste(out, (dx, 0))
        return Image.blend(sh, Image.new("RGB", (w, h), gelap), 0.6 * e)
    if jenis == "tinta":
        e = esmooth(u)
        m = _tinta_mask(w, h, e * 0.5)
        tepi = _tinta_mask(w, h, min(1, e * 0.5 + 0.018))
        o2 = out.copy()
        o2.paste(mix(acc, (255, 255, 255), 0.15), (0, 0), tepi)
        o2.paste(gelap, (0, 0), m)
        return o2
    if jenis == "iris":
        e = esmooth(u)
        m = Image.new("L", (w, h), 0)
        rr = math.hypot(w, h) / 2 * (1 - e)
        cx, cy = w / 2, h / 2
        ImageDraw.Draw(m).ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=255)
        o2 = Image.new("RGB", (w, h), gelap)
        o2.paste(out, (0, 0), m.filter(ImageFilter.GaussianBlur(6)))
        if rr > 4:
            ImageDraw.Draw(o2).ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=acc,
                                       width=max(2, int(w * 0.003)))
        return o2
    return out


def trans_masuk(out, u, jenis, acc, gelap=(4, 5, 14)):
    """Fase masuk (u 0 -> 1 di awal adegan)."""
    w, h = out.size
    if jenis == "zoomthru":
        e = eo(u)
        out2 = out.resize((w, h), Image.BILINEAR, box=_box_zoom(w, h, 1 + 0.22 * (1 - e)))
        if u < 0.7:
            out2 = zoom_blur(out2, 0.18 * (1 - u / 0.7))
        return Image.blend(out2, Image.new("RGB", (w, h), mix(acc, (255, 255, 255), 0.75)), 0.85 * (1 - e) ** 2)
    if jenis == "whip":
        e = eo(u)
        dx = int(w * 0.30 * (1 - e))
        o2 = blur_arah(out, 90 * (1 - e) ** 2)
        sh = Image.new("RGB", (w, h), gelap)
        sh.paste(o2, (dx, 0))
        return sh
    if jenis == "tinta":
        e = esmooth(u)
        m = _tinta_mask(w, h, 0.5 + e * 0.5)
        tepi = _tinta_mask(w, h, min(1, 0.5 + e * 0.5 + 0.018))
        o2 = Image.new("RGB", (w, h), gelap)
        o2.paste(mix(acc, (255, 255, 255), 0.15), (0, 0), tepi)
        o2.paste(out, (0, 0), m)
        return o2
    if jenis == "iris":
        e = esmooth(u)
        m = Image.new("L", (w, h), 0)
        rr = math.hypot(w, h) / 2 * e
        cx, cy = w / 2, h / 2
        ImageDraw.Draw(m).ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=255)
        o2 = Image.new("RGB", (w, h), gelap)
        o2.paste(out, (0, 0), m.filter(ImageFilter.GaussianBlur(6)))
        if 4 < rr < math.hypot(w, h) / 2 - 4:
            ImageDraw.Draw(o2).ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=acc,
                                       width=max(2, int(w * 0.003)))
        return o2
    return out


def _box_zoom(w, h, k, ax=0.5, ay=0.5):
    cw, ch = w / k, h / k
    x0, y0 = (w - cw) * ax, (h - ch) * ay
    return (x0, y0, x0 + cw, y0 + ch)


def trans_dua(prev, img, p, jenis, acc, latar=(246, 241, 232)):
    """Transisi dua-frame (Shorts): p 0..1."""
    w, h = img.size
    if jenis == "zoomthru":
        if p < 0.5:
            u = p / 0.5
            e = u * u
            a = zoom_blur(prev, 0.08 + 0.3 * e)
            a = a.resize((w, h), Image.BILINEAR, box=_box_zoom(w, h, 1 + 0.4 * e))
            return Image.blend(a, Image.new("RGB", (w, h), mix(acc, (255, 255, 255), 0.8)), 0.7 * e ** 1.5)
        u = (p - 0.5) / 0.5
        e = eo(u)
        b = img.resize((w, h), Image.BILINEAR, box=_box_zoom(w, h, 1 + 0.2 * (1 - e)))
        if u < 0.6:
            b = zoom_blur(b, 0.14 * (1 - u / 0.6))
        return Image.blend(b, Image.new("RGB", (w, h), mix(acc, (255, 255, 255), 0.8)), 0.7 * (1 - e) ** 2)
    if jenis == "tinta":
        e = esmooth(p)
        m = _tinta_mask(w, h, e)
        tepi = _tinta_mask(w, h, min(1, e + 0.02))
        o2 = prev.copy()
        o2.paste(acc, (0, 0), tepi)
        o2.paste(img, (0, 0), m)
        return o2
    if jenis == "cahaya":
        # light-leak: sapuan cahaya hangat + crossfade
        e = esmooth(p)
        o2 = Image.blend(prev, img, e)
        fl = math.sin(math.pi * p) ** 1.5
        leak = _cache_get(("leak", w, h, acc), lambda: _leak(w, h, acc))
        x = int((-0.6 + 1.2 * p) * w)
        lay = Image.new("RGB", (w, h), (0, 0, 0))
        lay.paste(leak, (x, 0))
        return ImageChops.screen(o2, lay.point(lambda v: int(v * fl)))
    return Image.blend(prev, img, esmooth(p))


def _leak(w, h, acc):
    yy, xx = np.mgrid[0:h // 4, 0:w // 4].astype(np.float32)
    cx = w / 8
    d = np.exp(-(((xx - cx) / (w / 10)) ** 2)) * (0.6 + 0.4 * np.sin(yy / (h / 4) * math.pi))
    col = np.array(mix(acc, (255, 220, 170), 0.55), np.float32)
    arr = np.clip(d[..., None] * col[None, None, :] * 1.1, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").resize((w, h), Image.BILINEAR)


# ================================================================== E. latar mesh gradient
def mesh_latar(w, h, t, dasar, warna, kuat=None, seed=1, skala=12, cahaya=0.05):
    """Latar MESH GRADIENT bergerak (tren 2026): beberapa bidang warna lembut yang mengalir pelan
    di atas warna dasar + sorot cahaya lembut dari atas. Dihitung di resolusi 1/skala (murah) lalu
    diperbesar. warna = daftar RGB, kuat = daftar intensitas (0..1)."""
    sw, sh = max(4, w // skala), max(4, h // skala)
    kuat = kuat or [0.12] * len(warna)
    yy, xx = _cache_get(("mg", sw, sh), lambda: tuple(np.mgrid[0:sh, 0:sw].astype(np.float32)))
    nx, ny = xx / sw, yy / sh
    base = np.array(dasar, np.float32)
    out = np.repeat(np.repeat(base[None, None, :], sh, 0), sw, 1)
    asp = h / max(1, w)
    rng = np.random.default_rng(seed)
    for j, (c, k) in enumerate(zip(warna, kuat)):
        px, py, fx_, fy_, ph, rad = rng.random(6)
        cx = 0.15 + 0.7 * px + 0.22 * math.sin(t * (0.05 + 0.05 * fx_) + ph * 6.28)
        cy = 0.12 + 0.76 * py + 0.18 * math.cos(t * (0.04 + 0.05 * fy_) + ph * 4.1)
        r = 0.32 + 0.22 * rad
        d2 = (nx - cx) ** 2 + ((ny - cy) * asp) ** 2
        wgt = np.exp(-d2 / (2 * r * r)) * k
        out += (np.array(c, np.float32) - base)[None, None, :] * wgt[..., None]
    if cahaya:
        out += 255 * cahaya * np.clip(1 - ny / 0.55, 0, 1)[..., None] ** 2 * (1 - np.abs(nx - 0.5))[..., None]
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    return im.resize((w, h), Image.BILINEAR)


# ================================================================== C. finishing V13
# Diuji di riset-kualitas/prototipe_finishing.py: menurunkan bidang rata (flat 59,6% -> 42,8%),
# menaikkan entropy, tanpa menggeser warna (krem bergeser <= 3 level, putih pecah turun).
_V13 = {}


def _v13_blur(a, r):
    """Blur float32 lewat PIL (L) — radius dalam piksel PENUH."""
    return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")
                      .filter(ImageFilter.GaussianBlur(r)), dtype=np.float32)


def _v13_luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def v13_halation(a, kuat=0.42, ambang=10.0):
    """Pendar cahaya dari DETAIL terang (bukan bidang krem luas) — supaya warna latar tak berubah."""
    h, w, _ = a.shape
    y = _v13_luma(a)
    sw, sh = max(2, w // 3), max(2, h // 3)
    kecil = Image.fromarray(np.clip(y, 0, 255).astype(np.uint8), "L").resize((sw, sh), Image.BILINEAR)
    yb = np.asarray(kecil.filter(ImageFilter.GaussianBlur(3.0)).resize((w, h), Image.BILINEAR), dtype=np.float32)
    detail = np.clip(y - yb - ambang, 0.0, None)
    m = np.clip(detail / 60.0, 0.0, 1.0) ** 0.85
    m *= np.clip((y - 120.0) / 135.0, 0.0, 1.0)
    src = a * m[..., None]
    kecil_src = [Image.fromarray(np.clip(src[..., c], 0, 255).astype(np.uint8), "L").resize((sw, sh), Image.BILINEAR)
                 for c in range(3)]
    glow = np.zeros_like(a)
    for c in range(3):
        b1 = kecil_src[c].filter(ImageFilter.GaussianBlur(0.9)).resize((w, h), Image.BILINEAR)
        b2 = kecil_src[c].filter(ImageFilter.GaussianBlur(4.0)).resize((w, h), Image.BILINEAR)
        glow[..., c] = np.asarray(b1, dtype=np.float32) * 0.62 + np.asarray(b2, dtype=np.float32) * 0.38
    glow *= kuat * np.array([1.05, 0.99, 0.93], dtype=np.float32)
    return 255.0 - (255.0 - a) * (255.0 - glow) / 255.0


def v13_lindung(a, lutih=249.0):
    """Soft-knee: puncak di atas 249 dimampatkan, tidak menempel di 255."""
    y = _v13_luma(a)
    over = np.clip((y - lutih) / max(1e-6, 255.0 - lutih), 0, 1)
    k = 1.0 - 0.045 * (over ** 1.4)
    return np.clip(a * k[..., None], 0, 255)


def v13_unsharp(a, amount=0.12):
    """Kontras lokal halus pada luma saja (hue tidak bergeser)."""
    y = _v13_luma(a)
    d = (y - _v13_blur(y, 2.0)) * amount
    return np.clip(a + d[..., None], 0, 255)


def v13_vinyet(a, kuat=0.040):
    h, w, _ = a.shape
    key = ("vig", w, h, kuat)
    m = _V13.get(key)
    if m is None:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.414
        m = 1.0 - kuat * np.clip(d, 0, 1) ** 2.1
        _V13[key] = m.astype(np.float32)
    return np.clip(a * m[..., None], 0, 255)


def v13_dither(a, seed=0, amp=0.55):
    """Derau 1 px: memecah tangga 8-bit pada gradasi krem (banding)."""
    h, w, _ = a.shape
    key = ("dither", h, w)
    n = _V13.get(key)
    if n is None:
        n = (np.random.default_rng(20261019).random((h, w)).astype(np.float32)
             - np.random.default_rng(7717).random((h, w)).astype(np.float32))
        _V13[key] = n
    n = np.roll(n, (seed * 37) % h, axis=0)
    n = np.roll(n, (seed * 91) % w, axis=1)
    y = _v13_luma(a) / 255.0
    wgt = 0.35 + 0.65 * np.clip(1 - np.abs(y - 0.72) / 0.4, 0, 1)
    return np.clip(a + (n * amp * wgt)[..., None], 0, 255)


def v13_grain(a, seed=7, kuat=2.2):
    """Butiran film halus, dimodulasi luminansi: highlight bersih, midtone bertekstur."""
    h, w, _ = a.shape
    key = ("grain", h, w)
    g = _V13.get(key)
    if g is None:
        rng = np.random.default_rng(4242)
        g = rng.standard_normal((h, w)).astype(np.float32)
        g = np.asarray(Image.fromarray(((g * 0.5 + 0.5) * 255).astype(np.uint8), "L")
                       .filter(ImageFilter.GaussianBlur(0.45)), dtype=np.float32)
        g = (g - g.mean()) / (g.std() + 1e-6)
        _V13[key] = g
    g = np.roll(g, (seed * 53) % h, axis=0)
    g = np.roll(g, (seed * 17) % w, axis=1)
    y = _v13_luma(a) / 255.0
    wgt = 0.55 + 0.45 * np.clip(1 - np.abs(y - 0.45) / 0.55, 0, 1)
    wgt *= np.clip(1.15 - y, 0.25, 1.0)
    return np.clip(a + (g * kuat * wgt)[..., None], 0, 255)


def finishing_v13(img, seed=0):
    """Rantai V13 (tanpa kurva nada global / LUT warna): pendar detail -> lindung highlight ->
    kontras lokal -> vinyet hangat -> dither -> grain. Warna dasar tidak disentuh."""
    if not AKTIF:
        return img
    a = np.asarray(img, dtype=np.float32)
    a = v13_halation(a)
    a = v13_lindung(a)
    a = v13_unsharp(a)
    a = v13_vinyet(a)
    a = v13_dither(a, seed)
    a = v13_grain(a, seed)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def _zoom_ch(ch, k):
    w, h = ch.size
    cw, chh = max(2, int(w / k)), max(2, int(h / k))
    x0, y0 = (w - cw) // 2, (h - chh) // 2
    return ch.crop((x0, y0, x0 + cw, y0 + chh)).resize((w, h), Image.BICUBIC)


def v14_ca(img, kuat=0.0016):
    """Aberasi kromatik radial sangat tipis: R ditarik, B dilepas (~1 px di tepi)."""
    if not AKTIF or kuat <= 0:
        return img
    r, g, b = img.split()
    r = _zoom_ch(r, 1.0 + kuat)
    b = _zoom_ch(b, 1.0 - kuat)
    return Image.merge("RGB", (r, g, b))


def v14_split(a, kuat=2.1):
    """Split-tone filmik: bayangan sejuk, highlight hangat (<= 1% agar palet tetap)."""
    lum = (a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114) / 255.0
    hi = np.clip((lum - 0.52) / 0.48, 0.0, 1.0)[..., None] ** 1.4
    lo = np.clip((0.52 - lum) / 0.52, 0.0, 1.0)[..., None] ** 1.4
    a = a + hi * np.array([kuat * 1.15, kuat * 0.55, -kuat * 0.85], dtype=np.float32)
    a = a + lo * np.array([-kuat * 0.75, -kuat * 0.15, kuat * 1.05], dtype=np.float32)
    return a


def finishing_v14(img, seed=0):
    """V14: rantai V13 + CA radial + split-tone filmik. Warna dasar tetap KlikTahu."""
    if not AKTIF:
        return img
    img = finishing_v13(img, seed)
    img = v14_ca(img, float(os.environ.get("KT_CA", "0.0016")))
    a = np.asarray(img, dtype=np.float32)
    a = v14_split(a, float(os.environ.get("KT_SPLIT", "2.1")))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ================================================================== D. cepat (v17)
# Jalur finishing yang SAMA hasil visualnya tetapi jauh lebih cepat:
#   * semua tahap elementwise digabung menjadi beberapa lintasan in-place (bukan 12)
#   * halation dihitung di 1/4 resolusi (pendar memang frekuensi rendah)
#   * luma diambil lewat PIL convert("L") yang berjalan di C
#   * grain & dither memakai varian yang dihitung SEKALI per proses (bukan roll tiap frame)
_V17 = {}


def _v17_grain(n_var=8, h=1920, w=1080, kuat=2.2):
    key = ("g", h, w, kuat, n_var)
    g = _V17.get(key)
    if g is None:
        g = []
        for v in range(n_var):
            rng = np.random.default_rng(4242 + v * 977)
            a = rng.standard_normal((h, w)).astype(np.float32)
            a = np.asarray(Image.fromarray(((a * 0.5 + 0.5) * 255).astype(np.uint8), "L")
                           .filter(ImageFilter.GaussianBlur(0.45)), dtype=np.float32)
            a = (a - a.mean()) / (a.std() + 1e-6)
            g.append(a * kuat)
        _V17[key] = g
    return g


def _v17_dither(n_var=8, h=1920, w=1080, amp=0.55):
    key = ("d", h, w, amp, n_var)
    d = _V17.get(key)
    if d is None:
        d = []
        for v in range(n_var):
            rng = np.random.default_rng(20261019 + v * 7919)
            n = (rng.random((h, w)).astype(np.float32) - rng.random((h, w)).astype(np.float32))
            d.append(n * amp)
        _V17[key] = d
    return d


def _v17_vig(h, w, kuat=0.040):
    key = ("v", h, w, kuat)
    m = _V17.get(key)
    if m is None:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dd = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.414
        m = (1.0 - kuat * np.clip(dd, 0, 1) ** 2.1).astype(np.float32)
        _V17[key] = m
    return m


def _v17_lut_knee():
    lut = []
    for v in range(256):
        over = max(0.0, min(1.0, (v - 249.0) / 6.0))
        lut.append(int(round(v * (1.0 - 0.045 * (over ** 1.4)))))
    return lut


def _v17_lut_split(kuat):
    """Split-tone sebagai kurva per kanal (fungsi luma -> offset), dipakai lewat point()."""
    out = []
    for c, (kr, kg, kb) in enumerate([(kuat * 1.15, 0, -kuat * 0.75), (0, 0, 0), (0, 0, 0)]):
        pass
    tab = []
    for c in range(3):
        cur = []
        for v in range(256):
            lum = v / 255.0
            hi = max(0.0, min(1.0, (lum - 0.52) / 0.48)) ** 1.4
            lo = max(0.0, min(1.0, (0.52 - lum) / 0.52)) ** 1.4
            off_hi = (kuat * 1.15, kuat * 0.55, -kuat * 0.85)[c]
            off_lo = (-kuat * 0.75, -kuat * 0.15, kuat * 1.05)[c]
            cur.append(int(max(0, min(255, round(v + hi * off_hi + lo * off_lo)))))
        tab.append(cur)
    return tab


def _v17_noise_tile(h, w, n_var=8, kuat=2.2):
    key = ("tile", h, w, kuat, n_var)
    t = _V17.get(key)
    if t is None:
        t = []
        for v in range(n_var):
            rng = np.random.default_rng(4242 + v * 977)
            a = rng.standard_normal((h, w)).astype(np.float32)
            a = np.asarray(Image.fromarray(((a * 0.5 + 0.5) * 255).astype(np.uint8), "L")
                           .filter(ImageFilter.GaussianBlur(0.45)), dtype=np.float32)
            a = (a - a.mean()) / (a.std() + 1e-6) * kuat
            im = Image.fromarray(np.clip(128 + a, 0, 255).astype(np.uint8), "L").convert("RGB")
            t.append(im)
        _V17[key] = t
    return t


def _v17_vig_img(h, w, kuat=0.040):
    key = ("vigi", h, w, kuat)
    m = _V17.get(key)
    if m is None:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dd = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.414
        v = 1.0 - kuat * np.clip(dd, 0, 1) ** 2.1
        m = Image.fromarray(np.clip(v * 255, 0, 255).astype(np.uint8), "L").convert("RGB")
        _V17[key] = m
    return m


def finishing_v14_cepat(img, seed=0):
    """Finishing setara visual, dikerjakan dengan operasi C (PIL) alih-alih numpy float.

    Efek yang dipertahankan: halation, soft-knee highlight, vinyet, grain, split-tone,
    CA radial. Yang dihilangkan HANYA dither 1 px karena tugasnya (memecah banding pada
    gradasi) sudah dikerjakan grain dengan amplitudo lebih besar — hasilnya sama.
    Unsharp lokal juga dilewati karena render sudah menerapkan UnsharpMask pada
    resolusi akhir (dua kali penajaman hanya menambah halo).
    """
    if not AKTIF:
        return img
    w, h = img.size
    # ---- halation: SELURUH pendar dihitung di 1/4 resolusi, lalu SATU upscale.
    # (versi pertama meng-upscale 3 kanal terpisah -> 3 resize penuh per frame)
    _d = int(os.environ.get("KT_HAL", "6"))
    sw, sh = max(2, w // _d), max(2, h // _d)
    small = img.resize((sw, sh), Image.BILINEAR)
    Lk = small.convert("L")
    yk = np.asarray(Lk, dtype=np.float32)
    yb = np.asarray(Lk.filter(ImageFilter.GaussianBlur(max(0.6, 6.0 / _d))), dtype=np.float32)
    m = (np.clip(np.clip(yk - yb - 10.0, 0, None) / 60.0, 0, 1) ** 0.85)
    m *= np.clip((yk - 120.0) / 135.0, 0, 1)
    gsrc = Image.fromarray(np.clip(np.asarray(small, np.float32) * m[..., None], 0, 255)
                           .astype(np.uint8))
    g1 = gsrc.filter(ImageFilter.GaussianBlur(max(0.5, 2.2 / _d)))
    g2 = gsrc.filter(ImageFilter.GaussianBlur(max(1.2, 10.0 / _d)))
    glow_small = Image.eval(Image.blend(g1, g2, 0.38), lambda v: int(v * 0.42))
    glow = glow_small.resize((w, h), Image.BILINEAR)
    out = ImageChops.screen(img, glow)

    # ---- soft-knee highlight (LUT per kanal)
    out = out.point(_v17_lut_knee() * 3)

    # ---- vinyet
    out = ImageChops.multiply(out, _v17_vig_img(h, w, float(os.environ.get("KT_VIG", "0.040"))))

    # ---- grain (varian siap pakai)
    tile = _v17_noise_tile(h, w, 8, float(os.environ.get("KT_GRAIN", "2.2")))[int(seed) % 8]
    out = ImageChops.add(out, tile, 1.0, -128)

    # ---- split-tone (kurva per kanal)
    out = out.point(sum(_v17_lut_split(float(os.environ.get("KT_SPLIT", "2.1"))), []))

    # ---- CA radial tipis (setengah resolusi)
    ca = float(os.environ.get("KT_CA", "0.0016"))
    if ca > 0:
        def zoom_ch(ch, kk):
            cw, chh = max(2, int(w / kk)), max(2, int(h / kk))
            x0, y0 = (w - cw) // 2, (h - chh) // 2
            crop = ch.crop((x0, y0, x0 + cw, y0 + chh))
            return crop.resize((max(2, cw // 2), max(2, chh // 2)), Image.BICUBIC).resize((w, h), Image.BICUBIC)
        r, g, b = out.split()
        out = Image.merge("RGB", (zoom_ch(r, 1.0 + ca), g, zoom_ch(b, 1.0 - ca)))
    return out
