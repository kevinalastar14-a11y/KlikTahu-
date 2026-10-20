# V15 — apa yang benar-benar diambil dari paket Astra

**Tanggal:** 20 Oktober 2026
**Sumber:** `upgrade_kliktahu_v15.txt` (paket kandidat dari GPT, 23 KB, 4 berkas + 5 patch)
**Status:** **dipakai sebagian** — 6 patch inti diterapkan, 2 modul baru tidak diadopsi.

---

## 1. Isi paket yang diterima

| Berkas | Baris | Isi |
|---|---|---|
| `kt_v15_motion.py` | ~130 | spring analitis, keyframe `Track` (C2), Bezier, trim-path, `camera()` pengganti |
| `kt_v15_compositor.py` | ~150 | layer RGBA, paralaks, contact shadow, bloom emisi, judul kinetik |
| `test_kt_v15.py` | ~50 | 5 unit test ringan |
| `V15_UPGRADE.md` | — | catatan jujur bahwa paket belum diuji render |
| installer | ~570 | dry-run/apply/rollback dengan manifest + sha256 |

Paket **tidak** menyentuh audio, VO, struktur cerita, naskah, atau desain adegan.

## 2. Hasil verifikasi (bukan klaim)

| Uji | Hasil |
|---|---|
| `python upgrade_kliktahu_v15.py <mesin-v12>` (dry-run) | **GAGAL** — `Fungsi tidak unik: _scrim` |
| Penyebab | `mesin_v13_ep51b.py` punya **dua** `def _scrim` (baris 57 versi mati, baris 462 versi aktif); `patch_function()` menolak nama ganda |
| Setelah installer diperbaiki (patch per potongan teks unik) | 4 BARU + 4 UBAH, terpasang bersih |
| `python -m unittest test_kt_v15 -v` | 5/5 OK |

## 3. Yang diadopsi (6 patch, terukur)

| # | Berkas | Perubahan | Bukti |
|---|---|---|---|
| 1 | `mesin_v13_ep51b.py` | `seed=hash(nm) % 97` → `{"jauh":17,"mid":43,"dekat":71}` | 3 proses dengan `PYTHONHASHSEED` 0/1/2: dulu **3 hash berbeda**, sekarang **identik** (`5a644e91…`) |
| 2 | `mesin_v13_ep51b.py` | kunci cache `_base`/`_solid`/`_scrim`/`_scrim_atas`/`_paper_mask` menyertakan `D.SS` | SS 1,0 → 1620 px, 1,5 → 2430 px, kembali 1,0 → 1080 px; tidak ada bitmap salah pakai |
| 3 | `mesin_v13_ep51b.py` | kepala `panah()` memakai `pts[-1]` | kepala menempel di ujung garis yang tumbuh, bukan di titik akhir tetap |
| 4 | `mesin_v12.py` | onset hentakan kamera diberi serangan `esm(d/0.075)` | lompatan zoom/frame **0,0393 → 0,0112** (60 fps) |
| 5 | `render.py` | `_camera()` affine subpiksel, bukan `crop(int)` | ketajaman 19,19 → **20,28** (satu resample), ±269 ms/frame (≈ +6 %) |
| 6 | `long/render_long.py` | `sin(t*0.23 + i)` → `sin(t*0.23)` | fase napas tidak melompat di batas adegan |

Perubahan #1 dan #4 adalah **cacat nyata**, bukan sekadar selera:

- **#1** `hash()` atas `str` diacak per proses. Render Ep51 v2 dipecah 8 chunk → tiap proses memakai seed hujan berbeda, sehingga **seluruh medan hujan berganti mendadak di 7 batas chunk**. Tidak terlihat di pratinjau statis, hanya di gerak.
- **#4** hentakan BEAT dulu langsung penuh di frame pertama (`exp(-0/0.09)=1`), jadi lompatan 3,9 % dalam satu frame — terbaca sebagai *pop*, bukan pukulan.

## 4. Yang tidak diadopsi

| Komponen | Alasan |
|---|---|
| `camera()` pengganti penuh | Mengganti amplitudo seluruh gerak (zoom maks 1,065 → 1,040) dan membuang noise `FX.nois2`. Rasa Ep51 v2 yang sudah lolos QC akan berubah; manfaat utamanya (onset mulus) sudah diambil lewat patch #4 tanpa mengubah karakter gerak. |
| `kt_v15_compositor.py` | Toolkit untuk adegan **baru** (depth, contact shadow, bloom, judul kinetik). Tidak dipakai satu adegan pun di repo ini; menambah kode mati. Disimpan di arsip ZIP bila nanti diperlukan. |
| `kt_v15_motion.py` | Sama: hanya dipakai `camera()` yang tidak diadopsi. `Track`/`spring` berguna untuk episode berikutnya — bisa diambil dari ZIP saat mulai. |
| Mengganti seluruh `kamera()` + installer otomatis | Installer menulis ulang berkas produksi berdasarkan pencocokan teks; rapuh (terbukti gagal). Patch manual + uji lebih aman. |

## 5. Konsekuensi yang harus dicatat

**Ep51 v2 yang sudah diunggah ke Drive memuat cacat #1.** Hujan berganti pola di detik ±12,7 · 25,4 · 38,1 · 50,8 · 63,5 · 76,2 · 88,9 (batas chunk 762 frame). Dampak: kilau halus pada lapisan hujan, bukan kerusakan gambar. Video tetap layak tayang; perbaikan berlaku untuk **Ep52 ke atas**.

Catatan operasional: `build/`, `dist/`, dan `episodes/*/audio_raw/` tidak ikut tersimpan di sandbox (kebijakan snapshot), jadi Ep51 v2 **tidak dapat dirender ulang identik** tanpa membuat VO baru. Master yang tersisa: MP4 + `…_audio.m4a` di Drive.

## 6. Cara memverifikasi ulang

```bash
cd mesin-v12
python3 mesin_v13_ep51b.py                     # selftest 8 visual
python3 -m compileall -q mesin_v12.py render.py mesin_v13_ep51b.py long/render_long.py

# determinisme hujan
for s in 0 1 2; do PYTHONHASHSEED=$s python3 -c "
import hashlib, mesin_v13_ep51b as m
from PIL import Image
im=Image.new('RGB',(int(m.D.S(1080)),int(m.D.S(1920))),(242,236,223)); m._hujan_lapis(im,0.4)
print(hashlib.sha256(im.tobytes()).hexdigest()[:16])"; done   # harus sama
```

## 7. Kesimpulan

Paket Astra adalah **patch mesin, bukan peningkatan tampilan**. Dari ~600 baris, yang benar-benar menaikkan kualitas: 2 perbaikan cacat (#1, #4) dan 2 pengerasan (#2, #5). Sisanya toolkit yang belum dipakai.

Untuk “tingkat mutakhir” yang diminta, yang menentukan tetap kerja per adegan: komposisi, hierarki teks, ritme potong, dan akurasi data — bukan lapisan gerak kamera.
