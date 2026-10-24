# KlikTahu · Ep55 · Metadata + Catatan Riset

**Judul:** Megalodon Bukan Hiu Putih Raksasa — Dan Kita Cuma Punya Giginya
**Produksi:** 24 Oktober 2026 · **Tayang:** 29–30 Oktober 2026, 18.30–20.30 WIB
**Format:** 1080×1920 · 60 fps · ±102,8 s · VO `voice-05` → rantai `vo_manusia.py` (tanpa potong/atempo) ·
SFX per kata + **ambien laut** (bukan musik) · master `.m4a` AAC
**Mesin:** **V18 SPRITE ATLAS** (`mesin_v18_*.py`, 3.779 baris) — raster sekali + komposisi sprite, render 4 menit.

---

## 1. Kenapa topik ini

Antrean tetap dihapus. Data 15 Okt 2026 (`analisis/hasil_mendalam_20261015.json`):

| Faktor | Nilai | Catatan |
|---|---|---|
| Skor mentah | 76,6 | di bawah tema tubuh (mata 163 · perut 136 · gigi 133) |
| Pilar | **HEWAN, bobot 0,92** | tertinggi kedua setelah LANGIT; tema tubuh cuma 0,81 |
| Pertumbuhan | **176,8** | tertinggi ketiga di seluruh kolam |
| Sudah pernah dibuat? | **belum pernah** | 16 episode TUBUH berturut-turut sebelum ini |
| Klaster frasa | "sebesar apa", "zaman apa", "apakah nyata" | dua pertanyaan pertama dijawab episode ini |

Tema tubuh yang skornya lebih tinggi sudah dipakai (Ep28 perut, Ep30 gigi, Ep21/25 mimpi) atau cepat basi
(baterai & HP, pilar 0,34). **Megalodon memberi pilar terkuat yang belum pernah disentuh.**

---

## 2. Judul (pilih satu)

1. **Megalodon Bukan Hiu Putih Raksasa — Dan Kita Cuma Punya Giginya** ← utama
2. 24 Meter, 94 Ton — Semua Itu Dihitung dari Gigi
3. Kenapa Tidak Ada Satu Pun Tulang Megalodon yang Utuh?

---

## 3. Struktur 5 babak

| Babak | Adegan | Isi |
|---|---|---|
| Hook | intro | hiu 24 m + gigi sebesar telapak tangan |
| Agitation | f1 | 20 → 3,6 juta tahun; tulang rawan tidak memfosil |
| Body 1 | f2 | 16,4 m dari 11 m tulang belakang; batas 24,3 m |
| Body 1 | f3 | ramping seperti hiu lemon, bukan hiu putih gempal |
| Body 2 | f4 | gigi 18 cm bergerigi, puluhan ribu per individu |
| Body 2 | f5 | gigitan; ekor dilumpuhkan lebih dulu |
| Body 3 | f6 | punah: dingin, dangkal menyempit, paus migrasi, hiu putih |
| Loop | outro | vitrin museum; siluet raksasa yang sama seperti intro |

Timeline nyata: intro 0,00 · f1 10,65 · f2 21,94 · f3 35,82 · f4 47,83 · f5 64,23 · f6 76,89 · outro 94,48 · total 102,76 s.

---

## 4. Sumber & batas klaim

- **Shimada dkk. 2025** (*Palaeontologia Electronica*, 29 penulis) — 24,3 m batas atas, ±94 t, individu Belgia
  16,4 m, tubuh lebih ramping dari hiu putih.
- **NHM** — rentang 20–3,6 juta tahun; gigi sampai 18 cm; tidak ada gigi yang lebih muda dari 3,6 juta tahun.
- **Nature Communications 2022** — isotop seng pada gigi: tingkat trofik megalodon dan hiu putih awal bertumpuk.
- **PeerJ 2019** — kepunahan 3,6 juta tahun, banyak faktor; bekas luka pada fosil paus.
- **Science Advances 2022** — pemodelan 3D, massa ±61,5 t untuk panjang 15,9 m (dipakai sebagai konteks, bukan VO).

Tidak dipakai: "masih hidup di palung Mariana", angka gigitan dalam newton, perbandingan "sebesar bus",
"megalodon menghabisi paus" (justru sebaliknya — paus bermigrasi dan mangsa menghilang).

---

## 5. Yang baru di mesin (inti "fokus ke kode")

1. **Primitif bbox-lokal + cache gradasi** → satu frame turun dari ~1,1 s ke ~0,09 s (12×).
2. **Dilasi numpy** menggantikan `ImageFilter.MaxFilter` (71 ms → 22 ms untuk satu gigi 560 px).
3. **Sistem air**: gradasi kedalaman 6 lapis, berkas cahaya volumetrik, kaustik numpy, salju laut, gelembung.
4. **Siluet parametrik**: `hiu()` (ramping ↔ gempal, ekor bulan ↔ heteroserkal), `paus()`, `penyelam()`,
   semuanya dari spline Catmull-Rom — bukan segitiga.
5. **Gigi & mulut**: `gigi()` dengan gerigi takik nyata + akar bercabang, `baris_gigi()` untuk mulut
   menganga yang bisa dianimasikan (0 = mengatup).
6. **Tipografi v2**: `kartu2()` dengan kicker **di dalam** kartu (tidak pernah bertabrakan dengan ilustrasi),
   sorot bergerak, bayangan lokal; `label2()` menjepit posisi agar tidak terpotong tepi.
7. **Audio**: `sfx.ambient_laut()` — bed samudra tiga lapis di domain frekuensi, level RMS dijaga, loop aman.

---

## 6. Yang harus dicek sebelum unggah

- [ ] Tonton utuh: suara jelas, tidak ada jeda menggantung
- [ ] Cek loop: frame akhir (vitrin + gigi) vs frame awal (hiu + gigi)
- [ ] Thumbnail: mulut menganga paling terbaca di layar kecil
- [ ] Deskripsi: pertahankan baris "perkiraan ilmiah, bukan pengukuran langsung"
- [ ] Jangan menjawab komentar dengan angka yang tidak ada di sumber
