#!/usr/bin/env python3
"""mesin_v21_kertas.py — pustaka visual "KERTAS" (gaya video short lama KlikTahu).

Kenapa pustaka baru
-------------------
Video short lama KlikTahu memakai bahasa visual *buku catatan*: kertas krem
hangat, headline huruf besar berwarna tinta, kartu ilustrasi bersudut bulat,
stiker caption hitam-putih, tab "FAKTA n/7" di atas, dan ilustrasi vektor datar.
Gaya itu terbukti menahan penonton, jadi v21 menirunya — tetapi digambar ulang
dengan kualitas yang jauh lebih tinggi:

  * resolusi 1080x1920 (acuan 240x426) dan 60 fps (acuan 30 fps);
  * tepi vektor anti-alias (supersampling 2x), bukan piksel tangga;
  * animasi masuk ber-jeda (pop/stempel/highlighter) supaya tiap 1-2 detik ada
    sesuatu yang bergerak, bukan potongan patah;
  * tata letak bertingkat: HUD -> tab fakta -> headline -> kartu ilustrasi ->
    angka -> panel -> sumber -> progres, semuanya punya zona tetap sehingga
    tidak ada elemen bertumpuk (jebakan 21 docs/MESIN_V20.md);
  * grain kertas halus supaya bidang krem tidak "berkunang" saat di-encode.

Isi modul
---------
  Palet & latar          : KERTAS, TINTA, ... , `kertas_dasar()`
  Bentuk & teks          : `kartu()`, `teks()`, `pil()`, `stiker()`, `tab()`
  Ilustrasi vektor       : `ikan()`, `manusia()`, `kolom_laut()`, `silsilah()`,
                           `sirip()`, `koran()`, `peta()`, `termometer()`,
                           `kaca_pembesar()`, `panah()`, `garis_waktu()`
  Perakit animasi        : kelas `Komposisi` (dasar statis + lapisan ber-jeda)

Semua ukuran dalam piksel kanvas 1080x1920. Fungsi ilustrasi mengembalikan
sprite RGBA sehingga bisa ditempel, diskalakan, dan dirotasi tanpa merusak latar.
"""
from __future__ import annotations

import functools
import math
import os
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import mesin_v18_inti as I  # noqa: E402
from mesin_v18_inti import (F_BOLD, F_MED, F_REG, F_SEMI, Pena, blit, blit_c,  # noqa: E402
                            blit_s, clamp, eio, eo, lerp, mask, mix, raster,
                            rng, seg, shade, smooth, spr_text, tlh, tw, with_a)

W, H = 1080, 1920

# =============================================================== 1. palet
KERTAS = (223, 217, 207)      # krem hangat (diukur dari acuan: 219,214,206)
KERTAS_2 = (232, 227, 218)    # gumpalan kertas lebih terang
KERTAS_3 = (211, 204, 193)    # gumpalan lebih gelap / cincin samar
KARTU = (249, 246, 239)       # kartu ilustrasi
KARTU_2 = (240, 236, 227)     # kartu sekunder
TINTA = (26, 40, 55)          # tinta navy (headline)
TINTA_2 = (76, 90, 103)       # tinta sekunder
TINTA_3 = (128, 139, 149)     # tinta samar (sumber)
CORAL = (204, 78, 56)
CORAL_T = (232, 168, 152)     # coral muda untuk highlighter
NAVY = (30, 61, 92)
BIRU = (46, 121, 176)
LANGIT = (152, 197, 219)
TEAL = (32, 129, 116)
HIJAU = (58, 146, 84)
GOLD = (222, 160, 34)
PASIR = (212, 187, 139)
ROSE = (203, 121, 121)
ABU = (150, 160, 168)

# zona tata letak (dipakai episode supaya konsisten antar-babak)
Z = dict(
    hud=0, hud_h=118,
    tab=170,            # pusat tab "FAKTA n/7"
    headline=236,       # awal headline
    kartu_y0=545, kartu_y1=1525,
    angka=1590,         # angka besar
    panel=1596,         # panel kertas
    sumber=1836,
    progres=1878,
)


# =============================================================== 2. latar
def _gumpalan(k, cx, cy, r, warna, alpha=0.55):
    """Gumpalan kertas lembut (bukan gradasi — meniru cetakan kertas acuan)."""
    h, w = k.shape[:2]
    spr = raster(int(r * 2), int(r * 2), lambda p: p.circ(r, r, r * 0.94, fill=warna), ss=2)
    blit(k, spr, int(cx - r), int(cy - r), alpha)


def _cincin(k, cx, cy, r, warna, tebal=2.0, alpha=0.30):
    spr = raster(int(r * 2 + 8), int(r * 2 + 8), lambda p: p.circ(
        r + 4, r + 4, r, outline=warna, width=tebal), ss=2)
    blit(k, spr, int(cx - r - 4), int(cy - r - 4), alpha)


@functools.lru_cache(maxsize=4)
def kertas_dasar(noda: bool = True) -> np.ndarray:
    """Latar kertas 1080x1920 (dibuat sekali, dipakai semua babak)."""
    k = np.empty((H, W, 3), np.uint8)
    k[:] = KERTAS
    # gradasi vertikal sangat tipis: atas lebih terang, bawah lebih hangat
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    k = np.clip(k.astype(np.float32) * (1.05 - 0.07 * y) + 6 * y, 0, 255).astype(np.uint8)
    if noda:
        _gumpalan(k, 200, 300, 300, KERTAS_2, 0.55)
        _gumpalan(k, 900, 700, 360, KERTAS_2, 0.40)
        _gumpalan(k, 150, 1500, 420, KERTAS_2, 0.35)
        _gumpalan(k, 980, 1750, 300, KERTAS_3, 0.16)
        for r, a in ((300, 0.13), (300, 0.13), (520, 0.09), (760, 0.06)):
            _cincin(k, 840, 1180, r, KERTAS_3, 1.6, a)
        _cincin(k, 210, 980, 380, KERTAS_3, 1.4, 0.07)
    # grain kertas + serat halus
    g = I.paper_grain(H, W, 3.1, seed=17)
    k = np.clip(k.astype(np.float32) + g, 0, 255).astype(np.uint8)
    return k


@functools.lru_cache(maxsize=2)
def kertas_pad(pad: int = 30) -> np.ndarray:
    """Kertas versi lebih besar `pad` px di semua sisi.

    Dipakai untuk menggeser latar sedikit setiap frame ("kertas hidup"):
    tanpa ini, babak yang tahan 8 detik terlihat benar-benar beku — terukur
    Δ 0,00 antar-frame pada QC (butir "ada gerak").
    """
    k = kertas_dasar()
    return np.pad(k, ((pad, pad), (pad, pad), (0, 0)), mode="edge")


@functools.lru_cache(maxsize=4)
def debu_spr(r: int = 5, warna=(150, 140, 126), alpha: int = 34) -> np.ndarray:
    """Butir debu kertas (lingkaran lembut) untuk gerak latar."""
    n = int(r * 2 + 6)
    spr = raster(n, n, lambda p: p.circ(n / 2, n / 2, r, fill=warna + (alpha,)), ss=2)
    return spr


# =============================================================== 3. bentuk & teks
@functools.lru_cache(maxsize=64)
def kartu(w: int, h: int, r: int = 44, isi=KARTU, garis=None, lebar=0.0,
          bayang: bool = True) -> np.ndarray:
    """Kartu bersudut bulat + bayangan lembut (sprite RGBA)."""
    pad = 26
    W_, H_ = int(w) + pad * 2, int(h) + pad * 2

    def gambar(p):
        p.rrect(pad, pad, pad + w, pad + h, r, fill=isi, outline=garis,
                width=lebar if garis else 0)
    spr = raster(W_, H_, gambar, ss=2)
    if bayang:
        a = spr[..., 3].astype(np.float32) / 255.0
        sh = I.gblur((a * 255).astype(np.uint8), 11).astype(np.float32) / 255.0 * 0.30
        out = spr.copy()
        out[..., 3] = np.clip(a + sh * 0.9, 0, 1) * 255
        out[..., 0] = np.where(a > 0.4, isi[0], 74)
        out[..., 1] = np.where(a > 0.4, isi[1], 66)
        out[..., 2] = np.where(a > 0.4, isi[2], 58)
    else:
        out = spr
    return out


def kartu_tempel(k, x, y, w, h, r=44, isi=KARTU, alpha=1.0):
    s = kartu(int(w), int(h), r, isi)
    blit(k, s, int(x) - 26, int(y) - 26, alpha)


@functools.lru_cache(maxsize=512)
def teks(t: str, warna=TINTA, size: int = 64, name: str = F_BOLD,
         tracking: float = 0.0, rata: str = "kiri") -> np.ndarray:
    """Sprite teks (cache). `t` boleh berisi '\\n'."""
    baris = t.split("\n")
    if len(baris) == 1:
        spr = spr_text(t, warna, name, size, tracking)
        if rata == "tengah":
            pass
        return spr
    luas = [tw(b, name, size) for b in baris]
    w = int(max(luas)) + 8
    lh = int(tlh(name, size) * 1.16)
    h = lh * len(baris) + 8
    out = np.zeros((h, w, 4), np.uint8)
    for i, b in enumerate(baris):
        s = spr_text(b, warna, name, size, tracking)
        x = (w - s.shape[1]) // 2 if rata == "tengah" else 0
        blit_c(out.astype(np.uint8), s, x + s.shape[1] // 2, i * lh + s.shape[0] // 2)
        # blit_c butuh kanvas RGB; lakukan manual
    # ulang dengan cara benar (RGBA di atas RGBA)
    out = np.zeros((h, w, 4), np.uint8)
    for i, b in enumerate(baris):
        s = spr_text(b, warna, name, size, tracking)
        x = 0 if rata != "tengah" else (w - s.shape[1]) // 2
        y = i * lh
        hh, ww = s.shape[0], s.shape[1]
        hh = min(hh, h - y)
        ww = min(ww, w - x)
        if hh <= 0 or ww <= 0:
            continue
        a = s[:hh, :ww, 3:4].astype(np.float32) / 255.0
        dst = out[y:y + hh, x:x + ww].astype(np.float32)
        dst[..., :3] = s[:hh, :ww, :3] * a + dst[..., :3] * (1 - a)
        dst[..., 3:4] = np.maximum(dst[..., 3:4], s[:hh, :ww, 3:4].astype(np.float32))
        out[y:y + hh, x:x + ww] = dst.astype(np.uint8)
    return out


@functools.lru_cache(maxsize=256)
def pil(t: str, isi=KARTU, warna=TINTA, size: int = 34, pad_x: int = 30,
        pad_y: int = 14, radius: int = None, garis=None, lebar: float = 3.0,
        font: str = F_BOLD) -> np.ndarray:
    """Label berbentuk pil (dipakai tab FAKTA, label laut, tanda tangan)."""
    m = mask(t, font, size, 0.4)
    th, tw_ = m.shape
    w = tw_ + pad_x * 2
    h = th + pad_y * 2
    r = radius if radius is not None else h // 2
    spr = raster(w, h, lambda p: p.rrect(0.5, 0.5, w - 0.5, h - 0.5, r,
                                         fill=isi, outline=garis,
                                         width=lebar if garis else 0), ss=2)
    t2 = spr_text(t, warna, font, size, 0.4)
    blit(spr, t2, (w - t2.shape[1]) // 2, (h - t2.shape[0]) // 2)
    return spr


@functools.lru_cache(maxsize=128)
def stiker(t: str, jenis: str = "gelap", size: int = 38, rot: float = 0.0) -> np.ndarray:
    """Stiker caption: hitam-putih (acuan) atau kertas-garis (varian halus)."""
    if jenis == "gelap":
        isi, warna, garis = (33, 40, 48), (252, 249, 242), None
    elif jenis == "coral":
        isi, warna, garis = CORAL, (255, 252, 246), None
    elif jenis == "teal":
        isi, warna, garis = TEAL, (255, 252, 246), None
    else:  # "kertas"
        isi, warna, garis = KARTU, TINTA, TINTA
    spr = pil(t, isi, warna, size, 26, 13, radius=16, garis=garis, lebar=3.0)
    if abs(rot) > 0.01:
        spr = putar(spr, rot)
    return spr


def ukur(t: str, size: int, name: str = F_BOLD, tracking: float = 0.0) -> int:
    """Lebar teks yang SEBENARNYA (mask tight), bukan perkiraan tw().

    Dipakai untuk menempatkan stabilo tepat di belakang satu kata: `tw()`
    mengabaikan tracking sehingga stabilo bergeser beberapa piksel.
    """
    return mask(t, name, size, tracking).shape[1]


def putar(spr: np.ndarray, derajat: float) -> np.ndarray:
    """Rotasi sprite RGBA dengan tepi anti-alias (via PIL)."""
    from PIL import Image
    im = Image.fromarray(spr, "RGBA").rotate(derajat, resample=Image.BICUBIC, expand=True)
    return np.array(im)


@functools.lru_cache(maxsize=16)
def tab_fakta(n: int, total: int = 7) -> np.ndarray:
    """Tab 'FAKTA n/7' + deretan penanda kemajuan (acuan: pil + garis putus)."""
    w, h = 1080, 96
    spr = np.zeros((h, w, 4), np.uint8)
    label = pil(f"FAKTA {n}/{total}", KARTU, CORAL, 36, 34, 13, radius=20,
                garis=CORAL, lebar=3.2)
    cx = w // 2
    blit_c_rgba(spr, label, cx, h // 2)
    # garis putus kiri & kanan tab
    tepi_kiri = cx - label.shape[1] // 2 - 18
    tepi_kanan = cx + label.shape[1] // 2 + 18
    seg_spr = raster(40, 8, lambda p: p.rrect(0, 2, 40, 6, 2, fill=CORAL), ss=2)
    x = tepi_kiri - 52
    while x > 40:
        blit(spr, seg_spr, x, h // 2 - 4, 0.55)
        x -= 56
    x = tepi_kanan + 12
    while x < w - 80:
        blit(spr, seg_spr, x, h // 2 - 4, 0.55)
        x += 56
    return spr


def blit_c_rgba(dst: np.ndarray, spr: np.ndarray, cx: int, cy: int, alpha: float = 1.0):
    """Tempel sprite RGBA di tengah (cx, cy) pada kanvas RGBA/RGB apa pun."""
    h, w = spr.shape[:2]
    x = int(cx - w // 2)
    y = int(cy - h // 2)
    H_, W_ = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W_, x + w), min(H_, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    a = (s[..., 3:4].astype(np.float32) / 255.0) * alpha
    d = dst[y0:y1, x0:x1]
    if d.shape[2] == 4:
        da = d[..., 3:4].astype(np.float32) / 255.0
        out_a = a + da * (1 - a)
        rgb = (s[..., :3].astype(np.float32) * a +
               d[..., :3].astype(np.float32) * da * (1 - a)) / np.maximum(out_a, 1e-6)
        d[..., :3] = np.clip(rgb, 0, 255)
        d[..., 3:4] = np.clip(out_a * 255, 0, 255)
    else:
        d[:] = (s[..., :3].astype(np.float32) * a +
                d.astype(np.float32) * (1 - a)).astype(np.uint8)


def tempel(dst, spr, x, y, alpha=1.0):
    """blit dengan posisi kiri-atas (bungkus inti.blit agar seragam)."""
    blit(dst, spr, int(x), int(y), alpha)


def tempel_sub(dst, spr, x: float, y: float, alpha: float = 1.0):
    """Tempel sprite pada posisi PECAHAN (anti-getar).

    Tanpa ini, gerak halus seperti goyangan ikan (beberapa piksel per detik)
    dibulatkan ke piksel bulat dan hasilnya bisa benar-benar diam selama
    beberapa frame — terukur Δ 0,00 pada QC "ada gerak".
    """
    x0, y0 = int(np.floor(x)), int(np.floor(y))
    fx, fy = x - x0, y - y0
    if fx < 0.02 and fy < 0.02:
        blit(dst, spr, x0, y0, alpha)
        return
    w = [(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy]
    for (dx, dy, k) in ((0, 0, w[0]), (1, 0, w[1]), (0, 1, w[2]), (1, 1, w[3])):
        if k > 0.004:
            blit(dst, spr, x0 + dx, y0 + dy, alpha * k)


def tempel_c(dst, spr, cx, cy, alpha=1.0):
    blit_c(dst, spr, int(cx), int(cy), alpha)


# =============================================================== 4. HUD
@functools.lru_cache(maxsize=8)
def merek() -> np.ndarray:
    """Wordmark 'KlikTahu' + titik coral (kiri atas)."""
    t = spr_text("KlikTahu", TINTA, F_BOLD, 38, 0.2)
    w, h = t.shape[1] + 40, t.shape[0]
    spr = np.zeros((h, w, 4), np.uint8)
    blit(spr, raster(18, 18, lambda p: p.circ(9, 9, 7, fill=CORAL), ss=2), 2, h // 2 - 9)
    blit(spr, t, 28, 0)
    return spr


@functools.lru_cache(maxsize=32)
def label_kategori(kat: str) -> np.ndarray:
    return pil(kat, NAVY, (250, 247, 240), 28, 26, 11, radius=14, font=F_SEMI)


def hud(k, kategori: str, alpha: float = 1.0):
    """Merek kiri atas + label kategori kanan atas (seperti acuan)."""
    m = merek()
    blit(k, m, 66, 44, alpha)
    lb = label_kategori(kategori)
    blit(k, lb, W - 66 - lb.shape[1], 40, alpha)


@functools.lru_cache(maxsize=8)
def progres_spr(total: int = 7) -> np.ndarray:
    """Bar progres segmen (bawah layar): 7 kotak, aktif jadi coral penuh."""
    w, h = 1080, 24
    spr = np.zeros((h, w, 4), np.uint8)
    n = total
    x0, x1 = 72, w - 72
    gap = 12
    bw = (x1 - x0 - gap * (n - 1)) / n
    for i in range(n):
        x = x0 + i * (bw + gap)
        s = raster(int(bw), 8, lambda p, i=i: p.rrect(0, 0, bw, 8, 4, fill=KERTAS_3), ss=2)
        blit(spr, s, int(x), 8, 0.55)
    return spr


def gambar_progres(k, indeks: int, frac: float, total: int = 7):
    """Segmen progres: yang sudah lewat terisi coral, yang aktif terisi sebagian."""
    n = total
    x0, x1 = 72, W - 72
    gap = 12
    bw = (x1 - x0 - gap * (n - 1)) / n
    for i in range(n):
        x = x0 + i * (bw + gap)
        if i < indeks:
            f = 1.0
        elif i == indeks:
            f = clamp(frac)
        else:
            f = 0.0
        # dasar
        s = raster(int(bw), 8, lambda p: p.rrect(0, 0, bw, 8, 4, fill=KERTAS_3), ss=2)
        blit(k, s, int(x), Z["progres"], 0.85)
        if f > 0.01:
            wf = max(8, bw * f)
            s2 = raster(int(bw), 8, lambda p: p.rrect(0, 0, wf, 8, 4, fill=CORAL), ss=2)
            blit(k, s2, int(x), Z["progres"], 1.0)


def sumber_teks(k, t: str, alpha: float = 1.0):
    s = teks(t, TINTA_3, 26, F_MED)
    if s.shape[1] > W - 144:
        s = teks(t, TINTA_3, 23, F_MED)
    blit(k, s, 72, Z["sumber"], alpha)


# =============================================================== 5. headline
def headline(k, baris, y=None, size=88, warna=TINTA, sorot=None, prog=1.0,
             baris_sorot=None, alpha=1.0):
    """Headline huruf besar rata kiri.

    `sorot` = teks kata yang diberi highlighter coral (dicari di `baris_sorot`).
    """
    y = Z["headline"] if y is None else y
    lh = int(size * 1.20)
    for i, b in enumerate(baris):
        s = spr_text(b, warna, F_BOLD, size, -0.6)
        blit(k, s, 74, y + i * lh, alpha)
    return y + lh * len(baris)


@functools.lru_cache(maxsize=128)
def highlighter_spr(w: int, h: int, warna=CORAL_T) -> np.ndarray:
    """Stabilo spidol: badan membulat + dua ujung yang tidak rata."""
    w, h = max(6, int(w)), max(6, int(h))

    def gambar(p):
        p.rrect(0, h * 0.10, w, h * 0.90, h * 0.40, fill=warna)
        # ujung spidol sedikit melebar/menyempit
        p.ell(-w * 0.02, h * 0.16, w * 0.10, h * 0.84, fill=warna)
        p.ell(w * 0.90, h * 0.14, w * 1.02, h * 0.86, fill=warna)
    return raster(w, h, gambar, ss=2)


def highlighter(k, x, y, w, h, warna=CORAL_T, prog=1.0, rot=0.0, alpha=0.85):
    """Stabilo coral di belakang kata (dipakai langsung pada kanvas)."""
    wp = max(4, int(w))
    spr = highlighter_spr(wp, int(h), warna)
    n = max(2, int(spr.shape[1] * clamp(prog)))
    blit(k, spr[:, :n], int(x), int(y), alpha)


def coret(k, x, y, w, warna=CORAL, tebal=5.0, prog=1.0, naik=0.06):
    """Garis coret (tangan) untuk membatalkan klaim — tipis, sedikit miring."""
    wp = max(4, int(w * clamp(prog)))
    dy = int(w * naik)
    hh = abs(dy) + int(tebal * 3)
    y0 = tebal * 1.5 + (0 if dy >= 0 else -dy)
    spr = raster(int(wp), int(hh), lambda p: p.line(
        [(2, y0 + dy), (wp - 2, y0)], warna, tebal), ss=2)
    blit(k, spr, int(x), int(y))


# =============================================================== 6. ilustrasi
def _warna(c, a=255):
    return (int(c[0]), int(c[1]), int(c[2]), a)


def _bentuk(p, pts, warna, halus=0.0, outline=None):
    """Isi poligon; `halus` > 0 mempertebal garis tepi warna sama sehingga
    sudutnya membulat (trik PIL: line dengan joint="curve")."""
    p.poly(pts, fill=warna, outline=outline)
    if halus > 0:
        p.line(list(pts) + [pts[0]], warna, halus)


def _haluskan(pts, n=6):
    """Resample jalur dengan Catmull-Rom (poligon jadi lengkung mulus)."""
    P = list(pts)
    m = len(P)
    out = []
    for i in range(m):
        p0, p1, p2, p3 = P[(i - 1) % m], P[i], P[(i + 1) % m], P[(i + 2) % m]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    return out


#: Siluet coelacanth (menghadap kiri). Sirip punggung & dada MENYATU di jalur
#: ini — percobaan dengan sirip sebagai bentuk terpisah membuatnya tampak
#: seperti batu menempel. Koordinat relatif 0..1.
_SILUET = [
    (0.020, 0.500), (0.028, 0.420), (0.072, 0.345), (0.150, 0.303),
    (0.232, 0.288),
    (0.256, 0.286), (0.286, 0.108), (0.330, 0.152), (0.360, 0.208),
    (0.376, 0.288),
    (0.452, 0.296), (0.512, 0.312),
    (0.534, 0.314), (0.560, 0.196), (0.594, 0.238), (0.612, 0.322),
    (0.664, 0.360), (0.716, 0.408), (0.746, 0.436),
    # ekor tiga cuping
    (0.800, 0.318), (0.884, 0.170), (0.958, 0.222), (0.888, 0.412),
    (0.924, 0.472), (0.952, 0.500), (0.924, 0.528), (0.888, 0.588),
    (0.958, 0.778), (0.884, 0.830), (0.800, 0.682), (0.746, 0.564),
    # perut + sirip dada menyatu
    (0.700, 0.596), (0.652, 0.652),
    (0.638, 0.660), (0.646, 0.792), (0.596, 0.806), (0.588, 0.700),
    (0.532, 0.742), (0.470, 0.788),
    (0.452, 0.792), (0.406, 0.930), (0.352, 0.958), (0.322, 0.892),
    (0.344, 0.820),
    (0.300, 0.862), (0.216, 0.842), (0.136, 0.786), (0.066, 0.694),
    (0.030, 0.596),
]


def ikan(w=560, h=300, warna=NAVY, perut=None, bintik=True,
         mata_emas=True, sisik=False) -> np.ndarray:
    """Coelacanth vektor (menghadap kiri) — satu siluet mulus, sirip menyatu.

    Tiga lapis: (1) siluet, (2) perut terang lewat gradasi yang dipotong alpha
    siluet (cara ini tidak pernah menghasilkan tepi patah seperti poligon
    perut manual), (3) detail mata/mulut/insang/bintik di atasnya.
    Digambar 2x lalu diperkecil sehingga tepi halus pada 1080p.
    """
    w, h = int(w), int(h)
    if perut is None:
        perut = mix(warna, (250, 247, 238), 0.42)

    def siluet(p):
        p.poly(_haluskan([(x * w, y * h) for x, y in _SILUET], n=5), fill=warna)

    def detail(p):
        p.line([(w * 0.228, h * 0.410), (w * 0.246, h * 0.700)],
               shade(warna, 0.72), h * 0.014)
        p.line([(w * 0.050, h * 0.552), (w * 0.136, h * 0.582)], TINTA, h * 0.017)
        p.circ(w * 0.152, h * 0.432, h * 0.055, fill=GOLD if mata_emas else perut)
        p.circ(w * 0.152, h * 0.432, h * 0.029, fill=TINTA)
        p.circ(w * 0.144, h * 0.416, h * 0.010, fill=(252, 250, 244))
        if sisik:
            for i in range(7):
                for j in range(3):
                    cx = w * (0.28 + i * 0.052)
                    cy2 = h * (0.44 + j * 0.055)
                    p.arc(cx, cy2, cx + w * 0.05, cy2 + h * 0.05, 200, 340,
                          shade(warna, 0.80), h * 0.006)
        if bintik:
            rr = rng(31)
            for i in range(16):
                bx = w * rr.uniform(0.19, 0.60)
                by = h * (0.315 + 0.070 * (bx / w)) + h * rr.uniform(0.0, 0.05)
                p.circ(bx, by, h * rr.uniform(0.006, 0.010), fill=(250, 247, 238, 190))

    badan = raster(w, h, siluet, ss=2)
    M = badan[..., 3].astype(np.float32) / 255.0
    yy = np.arange(h, dtype=np.float32)[:, None] / max(1, h)
    xx = np.arange(w, dtype=np.float32)[None, :] / max(1, w)
    g = np.clip((yy - 0.575) / 0.185, 0.0, 1.0) ** 0.9 * 0.72
    g = np.broadcast_to(g, (h, w)).copy() * M
    # hanya badan (bukan cuping ekor) yang ikut memucat
    g *= np.clip((0.735 - xx) / 0.045, 0.0, 1.0)
    rgb = badan[..., :3].astype(np.float32)
    for c in range(3):
        rgb[..., c] = rgb[..., c] * (1 - g) + perut[c] * g
    badan[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    det = raster(w, h, detail, ss=2)
    a = det[..., 3:4].astype(np.float32) / 255.0
    badan[..., :3] = (det[..., :3].astype(np.float32) * a +
                      badan[..., :3].astype(np.float32) * (1 - a)).astype(np.uint8)
    badan[..., 3] = np.maximum(badan[..., 3], det[..., 3])
    return badan


def manusia(h=520, warna=(96, 108, 118), tinggi_label=None) -> np.ndarray:
    """Siluet manusia datar untuk pembanding skala."""
    w = int(h * 0.34)

    def gambar(p):
        cx = w * 0.5
        p.circ(cx, h * 0.085, h * 0.075, fill=warna)
        # badan
        p.poly([(cx - w * 0.30, h * 0.18), (cx + w * 0.30, h * 0.18),
                (cx + w * 0.24, h * 0.56), (cx - w * 0.24, h * 0.56)], fill=warna)
        # lengan
        p.poly([(cx - w * 0.30, h * 0.20), (cx - w * 0.40, h * 0.50),
                (cx - w * 0.30, h * 0.53), (cx - w * 0.20, h * 0.24)], fill=warna)
        p.poly([(cx + w * 0.30, h * 0.20), (cx + w * 0.40, h * 0.50),
                (cx + w * 0.30, h * 0.53), (cx + w * 0.20, h * 0.24)], fill=warna)
        # kaki
        p.poly([(cx - w * 0.24, h * 0.55), (cx - w * 0.05, h * 0.55),
                (cx - w * 0.08, h * 0.98), (cx - w * 0.26, h * 0.98)], fill=warna)
        p.poly([(cx + w * 0.05, h * 0.55), (cx + w * 0.24, h * 0.55),
                (cx + w * 0.26, h * 0.98), (cx + w * 0.08, h * 0.98)], fill=warna)
    return raster(w, h, gambar, ss=2)


def kolom_laut(w=420, h=760, atas=(178, 214, 230), bawah=(16, 44, 74),
               bintang=0, jarak_label=(), t=0.0, kedalaman=()):
    """Kolom kedalaman laut: gradasi + garis kedalaman + ikan kecil.

    `kedalaman` = daftar (fraksi_kedalaman, teks) untuk label meter (mis. 200 m).
    """
    def gambar(p):
        # gradasi bertingkat (flat banding halus, bukan blur)
        n = 46
        for i in range(n):
            f = i / (n - 1)
            c = mix(atas, bawah, f ** 0.85)
            p.rect(0, h * i / n, w, h * (i + 1) / n + 1, fill=c)
        # permukaan bergelombang
        p.rect(0, 0, w, h * 0.02, fill=(235, 246, 250))
        for i, (f, _lab) in enumerate(kedalaman):
            yy = h * f
            p.line([(0, yy), (w, yy)], (255, 255, 255, 90), 2.0)
        for i in range(bintang):
            r = rng(100 + i)
            x = float(r.uniform(0.05, 0.95) * w)
            y = float(r.uniform(0.15, 0.95) * h)
            p.circ(x, y, 2.2, fill=(255, 255, 255, 110))
    spr = raster(w, h, gambar, ss=2)
    # mask sudut membulat
    m = mask_rounded(w, h, 26)
    spr[..., 3] = (spr[..., 3].astype(np.uint16) * m // 255).astype(np.uint8)
    return spr


def mask_rounded(w, h, r):
    spr = raster(w, h, lambda p: p.rrect(0, 0, w, h, r, fill=(255, 255, 255, 255)), ss=2)
    return spr[..., 3]


def sirip(w=440, h=360, jenis="lobed") -> np.ndarray:
    """Diagram sirip: "lobed" (berdaging, bertulang) vs "ray" (bersirip-jari)."""
    def gambar(p):
        # potongan badan ikan di atas
        p.rrect(0, 0, w, h * 0.34, 18, fill=NAVY if jenis == "lobed" else (44, 92, 132))
        p.rrect(0, h * 0.30, w, h * 0.36, 12, fill=NAVY if jenis == "lobed" else (44, 92, 132))
        if jenis == "lobed":
            # cuping berdaging: pangkal tebal, ujung membulat
            pts = [(w * 0.30, h * 0.30), (w * 0.20, h * 0.62), (w * 0.28, h * 0.92),
                   (w * 0.46, h * 0.99), (w * 0.62, h * 0.90), (w * 0.66, h * 0.60),
                   (w * 0.60, h * 0.30)]
            _bentuk(p, _haluskan(pts, 7), TEAL, h * 0.012)
            # tulang di dalam cuping
            for i in range(4):
                p.line([(w * (0.34 + i * 0.02), h * 0.40),
                        (w * (0.30 + i * 0.085), h * 0.90)], (250, 247, 238), h * 0.016)
            p.line([(w * 0.42, h * 0.46), (w * 0.55, h * 0.44)], (250, 247, 238), h * 0.014)
        else:
            # sirip bersirip-jari: kipas tipis
            pts = [(w * 0.34, h * 0.30), (w * 0.18, h * 0.86), (w * 0.40, h * 0.99),
                   (w * 0.66, h * 0.92), (w * 0.70, h * 0.34)]
            _bentuk(p, _haluskan(pts, 7), LANGIT, h * 0.010)
            for i in range(6):
                p.line([(w * (0.40 + i * 0.045), h * 0.36),
                        (w * (0.24 + i * 0.082), h * 0.92)], (38, 78, 118), h * 0.012)
    return raster(int(w), int(h), gambar, ss=2)


def koran(w=430, h=520, judul="DESEMBER 1938") -> np.ndarray:
    """Potongan koran tua (untuk babak penemuan 1938)."""
    def gambar(p):
        p.rrect(0, 0, w, h, 6, fill=(244, 240, 229))
        p.rect(0, 0, w, h * 0.13, fill=(232, 226, 212))
        p.line([(w * 0.06, h * 0.13), (w * 0.94, h * 0.13)], (150, 145, 132), 2.0)
        # kolom teks palsu
        rr = rng(9)
        y = h * 0.20
        while y < h * 0.94:
            x = w * 0.07
            while x < w * 0.93:
                bw = float(rr.uniform(0.10, 0.26) * w)
                if x + bw > w * 0.93:
                    break
                p.rect(x, y, x + bw, y + h * 0.012, fill=(176, 170, 156))
                x += bw + w * 0.022
            y += h * 0.032
        # bingkai foto
        p.rect(w * 0.10, h * 0.30, w * 0.90, h * 0.66, fill=(208, 202, 190))
    return raster(w, h, gambar, ss=2)


def peta(w=820, h=520, rute=True) -> np.ndarray:
    """Laut + dua gugusan pulau + rute putus-putus (Komoro -> Manado)."""
    def gambar(p):
        p.rrect(0, 0, w, h, 22, fill=(214, 232, 240))
        # garis lintang samar
        for i in range(6):
            p.line([(0, h * (0.14 + i * 0.15)), (w, h * (0.14 + i * 0.15))],
                   (255, 255, 255, 110), 2.0)
        # daratan besar (kiri: Afrika Timur) + pulau-pulau
        p.poly([(0, 0), (w * 0.20, 0), (w * 0.24, h * 0.22), (w * 0.17, h * 0.46),
                (w * 0.21, h * 0.72), (w * 0.15, h), (0, h)], fill=(196, 206, 168))
        pulau = [(0.30, 0.42, 0.055, 0.09), (0.36, 0.55, 0.045, 0.05),
                 (0.42, 0.36, 0.035, 0.07), (0.55, 0.26, 0.075, 0.05),
                 (0.62, 0.36, 0.055, 0.04), (0.70, 0.22, 0.10, 0.07),
                 (0.74, 0.44, 0.07, 0.05), (0.66, 0.56, 0.05, 0.04),
                 (0.52, 0.66, 0.06, 0.04)]
        for (fx, fy, fw, fh) in pulau:
            p.ell(w * (fx - fw / 2), h * (fy - fh / 2), w * (fx + fw / 2),
                  h * (fy + fh / 2), fill=(170, 190, 140))
        if rute:
            # busur putus-putus
            for i in range(26):
                t0 = i / 26
                t1 = t0 + 0.018
                def busur(t):
                    x = w * (0.24 + (0.70 - 0.24) * t)
                    y = h * (0.46 - 0.24 * t - 0.28 * math.sin(math.pi * t))
                    return x, y
                p.line([busur(t0), busur(t1)], CORAL, 4.0)
        # penanda
        p.circ(w * 0.24, h * 0.46, 13, fill=CORAL)
        p.circ(w * 0.24, h * 0.46, 6, fill=(255, 250, 244))
        p.circ(w * 0.70, h * 0.22, 16, fill=NAVY)
        p.circ(w * 0.70, h * 0.22, 7, fill=(255, 250, 244))
    return raster(int(w), int(h), gambar, ss=2)


def termometer(w=120, h=420, frac=0.32, warna=CORAL) -> np.ndarray:
    def gambar(p):
        p.rrect(w * 0.34, 0, w * 0.66, h * 0.86, w * 0.16, fill=(250, 248, 242),
                outline=(196, 190, 178), width=3)
        p.circ(w * 0.5, h * 0.88, w * 0.30, fill=(250, 248, 242),
               outline=(196, 190, 178), width=3)
        p.circ(w * 0.5, h * 0.88, w * 0.22, fill=warna)
        y = h * (0.84 - 0.74 * frac)
        p.rrect(w * 0.40, y, w * 0.60, h * 0.88, w * 0.10, fill=warna)
        for i in range(7):
            yy = h * (0.08 + i * 0.10)
            p.line([(w * 0.66, yy), (w * 0.80, yy)], (188, 182, 170), 2.4)
    return raster(w, h, gambar, ss=2)


def kaca_pembesar(r=120, warna=NAVY) -> np.ndarray:
    def gambar(p):
        p.circ(r, r, r * 0.72, fill=(232, 244, 248), outline=warna, width=7)
        p.circ(r, r, r * 0.72, outline=(255, 255, 255), width=2)
        p.line([(r * 1.50, r * 1.50), (r * 1.92, r * 1.92)], warna, 16)
    return raster(int(r * 2), int(r * 2), gambar, ss=2)


def panah(w=160, h=90, warna=CORAL, arah="kanan", tebal=10) -> np.ndarray:
    def gambar(p):
        if arah == "kanan":
            p.line([(0, h * 0.5), (w * 0.78, h * 0.5)], warna, tebal)
            p.poly([(w * 0.70, h * 0.16), (w, h * 0.5), (w * 0.70, h * 0.84)], fill=warna)
        elif arah == "bawah":
            p.line([(w * 0.5, 0), (w * 0.5, h * 0.72)], warna, tebal)
            p.poly([(w * 0.18, h * 0.66), (w * 0.5, h), (w * 0.82, h * 0.66)], fill=warna)
        else:  # "kiri"
            p.line([(w, h * 0.5), (w * 0.22, h * 0.5)], warna, tebal)
            p.poly([(w * 0.30, h * 0.16), (0, h * 0.5), (w * 0.30, h * 0.84)], fill=warna)
    return raster(w, h, gambar, ss=2)


def garis_waktu(w=880, h=300, tahun=(), aktif=0, warna=CORAL) -> np.ndarray:
    """Garis waktu mendatar dengan penanda tahun (untuk 400 juta tahun)."""
    def gambar(p):
        p.line([(w * 0.04, h * 0.60), (w * 0.96, h * 0.60)], TINTA_2, 5)
        for i, x in enumerate(tahun):
            xx = w * (0.06 + 0.88 * x)
            p.line([(xx, h * 0.44), (xx, h * 0.60)], TINTA_2, 4)
            p.circ(xx, h * 0.60, 9 if i != aktif else 15,
                   fill=warna if i == aktif else KARTU, outline=TINTA_2, width=3)
        # panah "kini"
        p.poly([(w * 0.955, h * 0.50), (w * 0.995, h * 0.60), (w * 0.955, h * 0.70)], fill=TINTA_2)
    return raster(w, h, gambar, ss=2)


def grafik_batang(w=420, h=280, nilai=(), warna=CORAL, maks=None) -> np.ndarray:
    """Batang sederhana (untuk perbandingan jumlah)."""
    def gambar(p):
        n = max(1, len(nilai))
        mm = maks or max(nilai)
        bw = w / (n * 1.6)
        for i, v in enumerate(nilai):
            x = w * (i + 0.30) * (1.0 / n) + (w / n - bw) / 2
            hh = (v / mm) * h * 0.82
            p.rrect(x, h * 0.92 - hh, x + bw, h * 0.92, 8, fill=warna)
    return raster(w, h, gambar, ss=2)


def telur_embrio(w=360, h=200, n=5) -> np.ndarray:
    """Telur berisi embrio (untuk babak kehamilan 3 tahun)."""
    def gambar(p):
        for i in range(n):
            cx = w * (0.12 + i * 0.19)
            r = h * (0.30 - i * 0.02)
            p.circ(cx, h * 0.55, r, fill=(244, 232, 210), outline=(206, 184, 150), width=3)
            if i < n - 1:
                p.ell(cx - r * 0.42, h * 0.55 - r * 0.30, cx + r * 0.42, h * 0.55 + r * 0.30,
                      fill=(176, 132, 92))
    return raster(w, h, gambar, ss=2)


# =============================================================== 7. komposisi beranimasi
class Lapis:
    """Satu elemen yang muncul pada waktu tertentu di dalam babak.

    anim  : "pop"   skala 0,72 -> 1 dengan lenting halus
            "turun" geser dari atas 26 px
            "kiri"  geser dari kiri 34 px
            "fade"  hanya alpha
            "tulis" muncul dari kiri seperti ditulis (potong lebar)
    """
    __slots__ = ("spr", "x", "y", "t0", "dur", "anim", "cx", "cy", "rot", "alpha",
                 "amp", "lam", "fase")

    def __init__(self, spr, x=0, y=0, t0=0.0, dur=0.34, anim="pop",
                 tengah=False, rot=0.0, alpha=1.0):
        self.spr = spr
        self.amp, self.lam, self.fase = 7.0, 3.6, 0.0
        self.t0, self.dur, self.anim = t0, max(0.05, dur), anim
        self.alpha = alpha
        self.rot = rot
        if tengah:
            self.cx, self.cy = x, y
            self.x = int(x - spr.shape[1] // 2)
            self.y = int(y - spr.shape[0] // 2)
        else:
            self.x, self.y = int(x), int(y)
            self.cx = self.x + spr.shape[1] // 2
            self.cy = self.y + spr.shape[0] // 2


class Komposisi:
    """Dasar statis (kertas + kartu + ilustrasi) + lapisan ber-jeda."""

    def __init__(self, dasar=None, kategori="HEWAN PURBA", fakta=None, total=7,
                 hidup: bool = True):
        self.dasar = kertas_dasar().copy() if dasar is None else dasar.copy()
        self.pad = 30 if hidup else 0
        self.hidup = hidup
        # butir debu: posisi & fase deterministik supaya render paralel identik
        rr = rng(97)
        self.debu = [(float(rr.uniform(0, W)), float(rr.uniform(0, H)),
                      float(rr.uniform(2.0, 5.0)), float(rr.uniform(0, 6.28)),
                      float(rr.uniform(0.6, 1.6))) for _ in range(14)]
        self.kategori = kategori
        self.fakta = fakta
        self.total = total
        self.lapis = []
        self.dinamis = []   # daftar fn(kanvas, t_lokal) untuk gerak kontinu

    def tambah(self, spr, x=0, y=0, t0=0.0, dur=0.34, anim="pop",
              tengah=False, rot=0.0, alpha=1.0) -> Lapis:
        l = Lapis(spr, x, y, t0, dur, anim, tengah, rot, alpha)
        self.lapis.append(l)
        return l

    def teks(self, t, x, y, warna=TINTA, size=54, name=F_BOLD, t0=0.0,
             dur=0.34, anim="pop", tengah=False, tracking=0.0, alpha=1.0):
        return self.tambah(teks(t, warna, size, name, tracking), x, y, t0, dur,
                           anim, tengah, 0.0, alpha)

    def kartu(self, x, y, w, h, r=44, isi=KARTU, t0=0.0, dur=0.42, anim="pop"):
        return self.tambah(kartu(int(w), int(h), r, isi), x - 26, y - 26, t0, dur, anim)

    def goyang(self, spr, x, y, t0=0.0, amp=7.0, lam=3.6, fase=0.0, dur=0.40,
               alpha=1.0, putar_kecil=0.0):
        """Lapisan yang terus bergerak halus setelah muncul (naik-turun lembut)."""
        l = Lapis(spr, x, y, t0, dur, "goyang", False, putar_kecil, alpha)
        l.amp, l.lam, l.fase = amp, lam, fase
        self.lapis.append(l)
        return l

    def latar(self, lokal_t: float) -> np.ndarray:
        """Ambil latar; kalau `hidup`, geser sedikit supaya tidak beku."""
        if not self.hidup:
            return self.dasar.copy()
        pad = self.pad
        ox = int(round(pad + 6.0 * math.sin(lokal_t * 0.35)))
        oy = int(round(pad + 5.0 * math.cos(lokal_t * 0.28)))
        k = kertas_pad(pad)[oy:oy + H, ox:ox + W].copy()
        # debu kertas melayang (gerak sangat lambat, 1-2 px/detik)
        for (bx, by, r, fase, sp) in self.debu:
            dx = 14.0 * math.sin(lokal_t * 0.19 * sp + fase)
            dy = 10.0 * math.cos(lokal_t * 0.15 * sp + fase * 1.7) - lokal_t * 2.2 * sp
            yy = (by + dy) % (H + 40) - 20
            xx = (bx + dx) % (W + 40) - 20
            spr = debu_spr(int(round(r)))
            blit(k, spr, int(xx), int(yy), 0.55)
        return k

    def frame(self, lokal_t: float, hemat: bool = False) -> np.ndarray:
        k = self.latar(lokal_t)
        for l in self.lapis:
            if lokal_t < l.t0:
                continue
            p = clamp((lokal_t - l.t0) / l.dur)
            a = l.alpha
            x, y = l.x, l.y
            if l.anim == "pop":
                s = 0.72 + 0.28 * I.eob(p)
                spr = l.spr
                if p < 0.999:
                    # skala sprite murah: potong/regangkan lewat PIL hanya saat animasi
                    from PIL import Image
                    im = Image.fromarray(spr, "RGBA")
                    nw, nh = max(1, int(spr.shape[1] * s)), max(1, int(spr.shape[0] * s))
                    im = im.resize((nw, nh), Image.BILINEAR)
                    spr = np.array(im)
                    x = int(l.cx - nw // 2)
                    y = int(l.cy - nh // 2)
                a = a * clamp(p * 3.2)
                blit(k, spr, x, y, a)
            elif l.anim == "turun":
                dy = int(26 * (1 - I.eo(p)))
                blit(k, l.spr, l.x, l.y + dy, a * clamp(p * 2.4))
            elif l.anim == "kiri":
                dx = int(34 * (1 - I.eo(p)))
                blit(k, l.spr, l.x + dx, l.y, a * clamp(p * 2.4))
            elif l.anim == "tulis":
                n = max(2, int(l.spr.shape[1] * I.eo(p)))
                blit(k, l.spr[:, :n], l.x, l.y, a)
            elif l.anim == "goyang":
                dy = l.amp * math.sin(2 * math.pi * lokal_t / l.lam + l.fase)
                s = 0.86 + 0.14 * I.eob(p)
                spr = l.spr
                if p < 0.999:
                    from PIL import Image
                    im = Image.fromarray(spr, "RGBA")
                    nw, nh = max(1, int(spr.shape[1] * s)), max(1, int(spr.shape[0] * s))
                    im = im.resize((nw, nh), Image.BILINEAR)
                    spr = np.array(im)
                tempel_sub(k, spr,
                           l.x + (l.spr.shape[1] - spr.shape[1]) / 2,
                           l.y + dy + (l.spr.shape[0] - spr.shape[0]) / 2,
                           a * clamp(p * 2.2))
            else:  # fade
                blit(k, l.spr, l.x, l.y, a * p)
        for fn in self.dinamis:
            fn(k, lokal_t)
        return k


def kartu_ukuran(w, h, r=44, isi=KARTU) -> np.ndarray:
    return kartu(int(w), int(h), r, isi)


# =============================================================== 8. transisi
def sapuan(k, prog: float, warna=ROSE, alpha: float = 0.30, lebar: int = 120):
    """Pita warna tipis menyapu layar pada awal babak (transisi halus).

    Dibuat sempit dan miring supaya terbaca sebagai gerakan, bukan blok warna;
    versi pertama (260 px, tegak) tampak seperti panel pink menempel.
    """
    if not (0.0 < prog < 1.0):
        return
    x = int(-lebar * 2 + (W + lebar * 4) * I.eio(prog))
    hh = int(H * 1.12)
    spr = raster(lebar, hh, lambda p: p.poly(
        [(lebar * 0.30, 0), (lebar, 0), (lebar * 0.70, hh), (0, hh)], fill=warna), ss=1)
    blit(k, spr, x, -80, alpha * math.sin(math.pi * clamp(prog)) ** 0.7)


@functools.lru_cache(maxsize=8)
def kilau_spr(w: int = 260, h: int = 900) -> np.ndarray:
    """Pita cahaya diagonal (untuk kilau yang melintas di atas kartu)."""
    spr = np.zeros((h, w, 4), np.uint8)
    x = np.linspace(-1, 1, w, dtype=np.float32)[None, :]
    a = np.exp(-(x ** 2) * 5.0)
    a = (a * 46).astype(np.uint8)
    spr[..., :3] = 255
    spr[..., 3] = np.broadcast_to(a, (h, w))
    return spr


def kilau(k, t, t0, dur=1.6, x0=60, x1=1020, y0=520, y1=1420, alpha=0.5):
    """Kilau melintas kiri->kanan (dipakai sekali per babak, di tengah)."""
    if t < t0 or t > t0 + dur:
        return
    p = clamp((t - t0) / dur)
    spr = kilau_spr()
    x = int(x0 + (x1 - x0) * I.eio(p))
    blit(k, spr, x, y0, alpha * math.sin(math.pi * p) ** 0.6)


def siapkan_teks_aman(teks_list, maxw=940, size=88, name=F_BOLD):
    """Pecah teks jadi baris dengan batas lebar (memakai inti.wrap)."""
    return I.wrap(teks_list, name, size, maxw)
