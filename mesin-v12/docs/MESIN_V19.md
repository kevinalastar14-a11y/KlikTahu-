# MESIN V19 — "SINEMATIK GELAP"

Ringkasan: v19 memindahkan KlikTahu dari gaya *kertas ilustrasi* (v16–v18) ke bahasa visual
**video panjang kanal ini sendiri**: gelap, bercahaya, berlapis, dengan HUD yang konsisten.

Acuan yang dianalisis frame-per-frame: `Apa yang Terjadi Kalau Kamu Masuk ke Lubang Hitam`
(640×360, 9m17s, 10 babak) — diunduh dari Drive, 16 frame + potongan HUD diekstrak, lalu diukur:
tidak ada kartu putih; semua teks putih/berwarna di atas latar gelap; merek kiri atas + badge babak
kanan atas; bar progres segmen di tepi bawah; grafik = batang berlabel di panel kaca; penjelasan
bagian objek = garis pandu; skala = figur manusia kecil; angka besar sebagai penanda.

---

## 1. Berkas

| Berkas | Baris | Isi |
|---|---|---|
| `mesin_v19_gelap.py` | 1.149 | pustaka bahasa visual: palet, latar, cahaya, panel, grafik, ikon, makhluk, efek |
| `mesin_v19_ep55.py` | 935 | episode Ep55: 8 babak, HUD, aktor, tabel scene, API `siapkan()/frame(t)/daftar()` |
| `render_v19.py` | 298 | renderer paralel (pipe rawvideo → x264), concat, remux audio |
| `qc_v19.py` | 335 | 17 pemeriksaan QC (kontainer, audio, loop, gambar vs mesin, cahaya, margin) |
| `pustaka_v19.py` | 175 | thumbnail + lembar pratinjau, diturunkan dari frame mesin yang sama |
| **Total** | **2.892** | di luar inti raster `mesin_v18_inti.py` (1.173) yang dipakai ulang |

## 2. Palet

```
BG_0 (6,9,20)   BG_1 (10,15,32)   BG_2 (16,23,48)   BG_3 (23,32,64)
CYAN (86,204,242)  GOLD (247,193,72)  CORAL (240,98,92)
VIOLET (176,132,250)  GREEN (94,226,168)  BLUE (92,148,255)
TEKS (240,244,252)  TEKS_2 (176,187,210)  TEKS_3 (120,132,158)
```

Setiap babak punya satu warna aksen; badge, pill, grafik, dan progres memakai warna itu.
Tidak ada babak yang memakai lebih dari dua warna aksen sekaligus.

## 3. Zona tata letak (1080×1920)

| y | Isi |
|---|---|
| 0–120 | HUD: merek kiri, badge babak kanan |
| 260–1000 | visual utama (objek besar) |
| 1000–1290 | angka besar / label sekunder |
| 1322 | pill caption (<= 7 kata) |
| 1424–1740 | panel kaca (grafik / kartu / strip angka) |
| 1802 | baris sumber |
| 1890–1910 | progres segmen |

## 4. Bahasa visual yang dibangun

* **Latar**: `latar_gelap` (gradasi + nebula + bintang 3 lapis) dan `kedalaman_air`
  (gradasi air + berkas cahaya + kabut bawah + plankton).
* **Cahaya**: `glow_spr`/`pendar` (aditif, cache), `berkas_atas`, `sorot_spot`, `kilau_kaustik`.
* **Objek**: `hiu_gelap`, `paus_gelap`, `penyelam_gelap`, `gigi_gelap`, `plinth`, `bumi_gelap`.
  Semua memakai pola yang sama: **gradasi hanya pada mask badan**, sirip berwarna sendiri,
  **rim light pada seluruh siluet** → bentuk terbaca tanpa outline.
* **UI**: `panel_spr` (kaca: isi transparan + border 1,6 px + sapuan atas + aksen kiri),
  `pill_spr`, `label_kecil` (tracking lebar), `badge_babak`, `merek`, `progres_bawah`.
* **Grafik**: `bar_chart` (nilai otomatis pindah ke dalam batang bila tidak muat),
  `garis_tren`, `garis_pandu`, `stat_besar`, `kartu_data`, `_strip_angka` (3–4 angka kunci).
* **Efek**: `kilau_bintang`, `cincin`, `partikel_glow`, `debu_add`, `kilat`, `garis_kejut`.

## 5. Pelajaran teknis (jangan diulang)

1. **`cv2.line/fillPoly` pada RGBA menulis RGB mentah dan MENGABAIKAN alpha.** Goresan tipis harus
   lewat lapisan RGBA + `M.komposit` (helper `_lapis`). Versi pertama `gigi_gelap` menggambar garis
   pertumbuhan langsung ke RGBA → muncul garis hitam penuh.
2. **Semua ketebalan cv2 harus int.** `cv2.line(..., 2.6, ...)` gagal dengan pesan menyesatkan
   ("can't parse pt2" / "takes at most 5 arguments"). Bungkus `int(round(...))`.
3. **`panel_spr` wajib di-cache** (`functools.lru_cache`). Tanpa cache, tiap frame meraster ulang
   panel dengan PIL (110 ms/frame) — ini penyebab frame 160 ms.
4. **`Kanvas(w,h,warna)` mengisi 6 MB lalu dibuang** kalau `.a` langsung diganti; pakai
   `object.__new__(Kanvas)`.
5. **Grain jangan lewat float32** (15 ms/frame). Simpan lempeng noise positif & negatif sebagai
   uint8, lalu `cv2.add` + `cv2.subtract` (≈2 ms).
6. **`garis_tren(bayang=True)` memblur seluruh kanvas** (110 ms). Di episode selalu `bayang=False`.
7. **Gradasi pada seluruh sprite membuat sirip melebur** dengan badan. Gradasi hanya pada mask badan.
8. **`garis_pandu` butuh koordinat int** dan warna 3-tuple (`(*warna[:3], 200)`).

## 6. QC v19

Perubahan dari QC v18, karena gaya gelap:

| Pemeriksaan | v18 | v19 |
|---|---|---|
| gambar vs mesin | SSIM ≥ 0,97 | **MAE ≤ 4/255** (SSIM ≥ 0,95 sebagai info) — grain menurunkan SSIM walau mata tidak melihat beda |
| bidang gelap | maks < 35% piksel gelap | **tidak ada frame kosong** (mean < 6 DAN p99,5 < 55) |
| rentang tonal | — | **setiap frame punya cahaya** (p99,5 ≥ 40) |

Hasil Ep55 v19: **17/17 bersih**.

```
python3 render_v19.py --episode ep55 --keluar dist/KlikTahu_Ep55_Megalodon_v19.mp4 \
  --audio pustaka/Ep55_Megalodon/KlikTahu_Ep55_Megalodon_audio.m4a \
  --jobs 2 --fps 60 --preset slow --crf 14

python3 qc_v19.py dist/KlikTahu_Ep55_Megalodon_v19.mp4 --episode ep55 \
  --audio pustaka/Ep55_Megalodon/KlikTahu_Ep55_Megalodon_audio.m4a --json build_v19/qc.json
```

## 7. Hasil Ep55 v19

* 1080×1920 · 60 fps · 102,76 s · 6.166 frame · **67,15 MB** · render **467,7 s** (13,2 fps gabungan)
* Loop: frame akhir = frame 0 (blend 0,9 s terakhir ke `frame(0.0)` yang di-cache) → SSIM 0,9812
* Audio: M4A asli dipakai apa adanya, −14,4 LUFS, TP −1,6 dBTP, korelasi 1,0000 terhadap master
