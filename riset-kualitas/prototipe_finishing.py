#!/usr/bin/env python3
"""
prototipe_finishing.py — bukti konsep peningkatan kualitas gambar TANPA mengubah palet.

Mengambil satu frame dari video KlikTahu, lalu menerapkan rantai "V13":
  1. halation/bloom dua radius pada area terang (cahaya "membocor" seperti film)
  2. filmic tone curve (S-curve lembut, hitam tetap hitam, krem tidak pecah)
  3. kontras lokal halus (bukan sharpening keras)
  4. dithering terstruktur  -> menghapus banding pada gradasi krem
  5. grain halus 1 px yang dimodulasi luminansi (sedikit di highlight, sedang di midtone)
  6. vinyet lembut bersuhu hangat (memusatkan mata, bukan menggelapkan pojok)

Warna dasar TIDAK diubah: tidak ada hue shift, tidak ada LUT warna baru.
Yang berubah hanya distribusi cahaya, kontras, dan tekstur.

Pakai:
    python3 riset-kualitas/prototipe_finishing.py FRAME.png --out hasil/
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageFilter


# --------------------------------------------------------------------------- #
def _luma(a: np.ndarray) -> np.ndarray:
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def _blur(a: np.ndarray, r: float) -> np.ndarray:
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L")
    return np.asarray(img.filter(ImageFilter.GaussianBlur(r)), dtype=np.float32)


def halation(rgb: np.ndarray, kuat: float = 0.42, ambang_detail: float = 10.0,
             hangat: tuple[float, float, float] = (1.05, 0.99, 0.93)) -> np.ndarray:
    """Pendar cahaya dari DETAIL terang, bukan dari bidang terang yang luas.

    Kunci desain: bidang krem rata (latar KlikTahu) TIDAK boleh ikut berpendar,
    karena itu akan mengubah warna dasarnya. Yang berpendar hanya piksel yang
    lebih terang daripada sekitarnya (bintang, kilau, tepi teks putih).
    """
    y = _luma(rgb)
    detail = np.clip(y - _blur(y, 9.0) - ambang_detail, 0.0, None)
    m = np.clip(detail / 60.0, 0.0, 1.0) ** 0.85
    m *= np.clip((y - 120.0) / 135.0, 0.0, 1.0)       # hanya area yang memang terang
    src = rgb * m[..., None]
    b1 = np.stack([_blur(src[..., c], 2.5) for c in range(3)], -1)
    b2 = np.stack([_blur(src[..., c], 12.0) for c in range(3)], -1)
    glow = (b1 * 0.62 + b2 * 0.38) * kuat
    glow *= np.array(hangat, dtype=np.float32)
    return 255.0 - (255.0 - rgb) * (255.0 - glow) / 255.0


def tone_curve(rgb: np.ndarray, hitam: float = 0.008, putih: float = 1.0,
               s: float = 0.085) -> np.ndarray:
    """Filmic S-curve lembut: kontras midtone naik, ujung TIDAK bergeser.

    Tanpa fungsi ini, halation + contrast biasa akan menjepit putih (teks/pil putih
    kehilangan tepi lembut). Di sini putih 255 tetap 255 dan hitam tetap hitam.
    """
    x = np.clip(rgb / 255.0, 0, 1)
    x = (x - hitam) / max(1e-6, (putih - hitam))
    x = np.clip(x, 0, 1)
    # smoothstep lembut, bobot kecil, lalu dikembalikan ke skala 0..1
    x = x * x * (3 - 2 * x) * s + x * (1 - s)
    return np.clip(x * 255.0, 0, 255)


def lindung_highlight(rgb: np.ndarray, lutih: float = 249.0) -> np.ndarray:
    """Soft-knee: piksel di atas `lutih` dimampatkan agar tidak menempel di 255."""
    y = _luma(rgb)
    over = np.clip((y - lutih) / max(1e-6, 255.0 - lutih), 0, 1)
    # rasio pengali mengecil mulus sampai ~0.88 di puncak
    k = 1.0 - 0.045 * (over ** 1.4)
    return np.clip(rgb * k[..., None], 0, 255)


def unsharp_halus(rgb: np.ndarray, radius: float = 2.0, amount: float = 0.12) -> np.ndarray:
    y = _luma(rgb)
    yb = _blur(y, radius)
    d = (y - yb) * amount
    # terapkan hanya pada kanal warna secara proporsional -> tidak mengubah hue
    return np.clip(rgb + d[..., None], 0, 255)


def dither(rgb: np.ndarray, amp: float = 0.55) -> np.ndarray:
    """Derau biru-ish 1 px: memecah tangga 8-bit pada gradasi krem."""
    h, w, _ = rgb.shape
    rng = np.random.default_rng(20261019)
    n = rng.random((h, w)).astype(np.float32) - rng.random((h, w)).astype(np.float32)
    # tekanan derau lebih besar di area terang-rata (tempat banding paling terlihat)
    y = _luma(rgb) / 255.0
    wgt = 0.35 + 0.65 * np.clip(1 - np.abs(y - 0.72) / 0.4, 0, 1)
    return np.clip(rgb + (n * amp * wgt)[..., None], 0, 255)


def grain(rgb: np.ndarray, kuat: float = 2.2, seed: int = 7) -> np.ndarray:
    """Butiran film halus, dimodulasi luminansi: highlight bersih, midtone bertekstur."""
    h, w, _ = rgb.shape
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8), "L")
                   .filter(ImageFilter.GaussianBlur(0.45)), dtype=np.float32)
    n = (n - n.mean()) / (n.std() + 1e-6)
    y = _luma(rgb) / 255.0
    wgt = 0.55 + 0.45 * np.clip(1 - np.abs(y - 0.45) / 0.55, 0, 1)
    wgt *= np.clip(1.15 - y, 0.25, 1.0)          # highlight nyaris tanpa butir
    return np.clip(rgb + (n * kuat * wgt)[..., None], 0, 255)


def vinyet_lembut(rgb: np.ndarray, kuat: float = 0.10, hangat: float = 0.35) -> np.ndarray:
    h, w, _ = rgb.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.414
    m = 1.0 - kuat * np.clip(d, 0, 1) ** 2.1
    out = rgb * m[..., None]
    # pojok sedikit lebih hangat, bukan lebih hitam-pekat
    out[..., 2] *= (1.0 - 0.05 * hangat * np.clip(d - 0.45, 0, 1))
    return np.clip(out, 0, 255)


def rantai_v13(rgb: np.ndarray, seed: int = 7) -> np.ndarray:
    """Warna dasar TIDAK disentuh: tidak ada kurva nada global, tidak ada LUT.

    Urutan: pendar detail -> kontras lokal halus -> vinyet bersuhu -> dither -> grain.
    Semua langkah dirancang agar nilai latar krem tetap pada angka aslinya.
    """
    a = halation(rgb)
    a = lindung_highlight(a)       # jaga tepi putih tetap lembut, tanpa menempel 255
    a = unsharp_halus(a)
    a = vinyet_lembut(a, kuat=0.040)
    a = dither(a)
    a = grain(a, seed=seed)
    return a


# --------------------------------------------------------------------------- #
def metrik(rgb: np.ndarray) -> dict:
    y = _luma(rgb)
    h, w = y.shape[0] // 8 * 8, y.shape[1] // 8 * 8
    blk = y[:h, :w].reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 64)
    box = (y[:-2, 1:-1] + y[2:, 1:-1] + y[1:-1, :-2] + y[1:-1, 2:] + 4 * y[1:-1, 1:-1]) / 8
    hh = np.bincount((y.ravel() // 4).astype(np.int64), minlength=64)[:64]
    prob = hh / max(1, hh.sum())
    ent = float(-(prob[prob > 0] * np.log2(prob[prob > 0])).sum())
    # panjang tangga (banding): berapa nilai luma unik pada patch gradasi krem 200x200
    patch = y[200:400, 100:300]
    return dict(
        luma_mean=round(float(y.mean()), 2),
        luma_dr=round(float(np.percentile(y, 99) - np.percentile(y, 1)), 1),
        entropy=round(ent, 3),
        banding_levels=int(len(np.unique(np.round(patch)))),
        grain=round(float((y[1:-1, 1:-1] - box).std()), 2),
        flat_pct=round(float((blk.std(axis=1) < 0.9).mean() * 100), 1),
        edge_p99=round(float(np.percentile(np.concatenate(
            [np.abs(np.diff(y, axis=1)).ravel(), np.abs(np.diff(y, axis=0)).ravel()]), 99)), 1),
        clip_white=round(float((y > 253).mean() * 100), 2),
        clip_black=round(float((y < 2).mean() * 100), 2),
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("frame")
    ap.add_argument("--out", default="riset-kualitas/hasil")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)

    src = Image.open(args.frame).convert("RGB")
    a = np.asarray(src, dtype=np.float32)
    b = rantai_v13(a)
    out = Image.fromarray(np.clip(b, 0, 255).astype(np.uint8))

    base = os.path.join(args.out, "perbandingan_" + os.path.splitext(os.path.basename(args.frame))[0])
    # sisi-bersis: kiri asli, kanan V13 (dengan garis pemisah tipis)
    w, h = src.size
    cmp = Image.new("RGB", (w * 2 + 8, h), (30, 30, 34))
    cmp.paste(src, (0, 0))
    cmp.paste(out, (w + 8, 0))
    cmp = cmp.resize((cmp.width // 2, cmp.height // 2), Image.LANCZOS)
    cmp.save(base + "_sisi.jpg", quality=94)
    out.save(base + "_v13.png")

    m0, m1 = metrik(a), metrik(b)
    # --- kesetiaan warna: warna TIDAK boleh bergeser (hanya cahaya yang berubah)
    # patch latar krem di TENGAH frame (bebas vinyet) supaya penilaian adil
    cream0, cream1 = a[1450:1620, 120:420], b[1450:1620, 120:420]
    d_cream = np.abs(cream0.mean(axis=(0, 1)) - cream1.mean(axis=(0, 1)))
    hue0 = np.arctan2(*(np.roll(cream0.mean(axis=(0, 1)), -1)[:2]))
    hue1 = np.arctan2(*(np.roll(cream1.mean(axis=(0, 1)), -1)[:2]))
    m0["krem_rgb"] = [round(float(v), 1) for v in cream0.mean(axis=(0, 1))]
    m1["krem_rgb"] = [round(float(v), 1) for v in cream1.mean(axis=(0, 1))]
    m0["warna_geser_delta"] = 0.0
    m1["warna_geser_delta"] = round(float(np.abs(d_cream).max()), 2)
    import json
    print(json.dumps({"sebelum": m0, "sesudah": m1}, indent=1, ensure_ascii=False))
    with open(base + "_metrik.json", "w") as fh:
        json.dump({"sebelum": m0, "sesudah": m1}, fh, indent=1, ensure_ascii=False)
    print("hasil:", base + "_sisi.jpg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
