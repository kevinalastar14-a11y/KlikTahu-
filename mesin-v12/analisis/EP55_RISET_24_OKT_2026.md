# RISET — Penentuan Ep55 "Megalodon Bukan Hiu Putih Raksasa" (24 Oktober 2026)

**Perintah pemilik:** "Buat lebih bagus lagi, seperti video ini tapi lebih bagus! … Lebih bagus, lebih
mutakhir, fokus ke kode! Lanjut video short berikutnya!"
**Catatan penting:** dua video acuan (Drive `1FVsOCqUNfPv8ycXQYtYSQnQUE1YgAMUs` — *kitabedah.id*, 88,23 s;
`1D7Y3cWfcbs8fIXSEyxp3kRzvKmziGgKY` — *bit_wonder*, 47,50 s) **tidak bisa diputar di sandbox**: egress ke
`lh3.googleusercontent.com` diblokir (`SSL_ERROR_SYSCALL`), dan connector Drive tidak menyediakan pemutaran
video. Yang terbaca hanya metadata (nama, durasi, 720×1280). Karena itu permintaan "lebih mutakhir / fokus ke
kode" dijawab di sisi **mesin**, bukan dengan meniru frame yang tidak bisa dilihat.

---

## 1. Pemilihan topik (data 15 Okt 2026)

Antrean tetap dihapus. Tema dipilih dari `analisis/hasil_mendalam_20261015.json` + `performa.csv`.

| Tema | Skor mentah | Pilar (bobot) | Sudah dibuat? |
|---|---:|---|---|
| mata | 163,0 | TUBUH (0,81) | **Ep54 — baru** |
| perut & pencernaan | 136,4 | TUBUH | Ep28 |
| gigi & mulut | 133,5 | TUBUH | Ep30 (bau mulut) |
| mimpi & tidur | 124,1 | TUBUH | Ep21 + Ep25 |
| baterai & hp | 104,5 | TEKNOLOGI (0,34) | — |
| **megalodon** | **76,6** | **HEWAN (0,92)** | **belum pernah** |
| kulit | 85,8 | TUBUH | — |

**Kenapa megalodon:** skornya di bawah tema tubuh, tetapi pilar HEWAN punya performa tertinggi kedua (0,92 vs
0,81) dan **belum pernah dipakai sama sekali**; pertumbuhannya **176,8** (tertinggi ketiga di kolam);
persaingannya moderat (bukan jenuh seperti hiu putih/megalodon film). Tema-tema tubuh di atasnya sudah dipakai
(Ep28/30/21/25) atau cepat basi (baterai & HP, pilar 0,34).

**Klaster di dalam megalodon** (data frasa): "megalodon adalah", "megalodon hidup di zaman apa",
"megalodon vs mosasaurus", "megalodon apakah nyata", "megalodon terbesar di dunia". Semua mengarah ke dua
pertanyaan: **sebesar apa** dan **masih ada atau tidak** — keduanya dijawab episode ini.

**Sudut pembeda:** bukan "megalodon vs film", bukan "apakah masih hidup" saja, melainkan **cara ilmuwan tahu
ukurannya dari gigi** — itu yang jarang dibahas kanal Indonesia dan sangat cocok dengan gaya KlikTahu
(mekanisme, bukan mitos).

---

## 2. Hasil riset (angka yang dipakai di VO & layar)

| Klaim | Angka | Sumber | Batas klaim |
|---|---|---|---|
| Panjang maksimum | **24,3 m**; berat ±**94 ton** | Shimada dkk. 2025, *Palaeontologia Electronica* (29 penulis) | disebut "batas atas yang bisa dipertanggungjawabkan", bukan ukuran rata-rata |
| Individu Belgia | **16,4 m** (kepala 1,8 m + tulang belakang 11 m + ekor 3,6 m) | sama | satu individu, bukan spesies |
| Bentuk tubuh | **lebih ramping** dari hiu putih, mirip hiu lemon | sama | rekonstruksi, bukan fosil lengkap |
| Rentang waktu | **20 – 3,6 juta tahun lalu** | NHM | fosil termuda 3,6 juta tahun |
| Tidak ada tulang | tulang rawan tidak memfosil; yang tersisa gigi & tulang belakang langka | NHM | ada vertebra fosil (Belgia, Denmark), disebut "hampir semua dari gigi" |
| Gigi | tinggi sampai **18 cm**, bergerigi, terus berganti → puluhan ribu gigi per individu | NHM, koleksi fosil | "puluhan ribu" = orde besaran |
| Gigitan | jauh lebih kuat dari hiu putih; mangsa paus kecil | *Science Advances* 2022 (pemodelan 3D), Nature Comm. 2022 | angka newton **tidak** diucapkan |
| Pola serangan | ekor dilumpuhkan lebih dulu | PeerJ 2019, bekas luka pada fosil paus | interpretasi dari bekas luka |
| Kepunahan | 3,6 juta tahun lalu; banyak sebab | NHM, Nature Comm. 2022, PeerJ 2019 | **tidak** diklaim satu sebab |
| Sebab | pendinginan samudra, laut dangkal menyempit, paus pindah ke kutub, kompetisi hiu putih | sama | kompetisi = "turut menyumbang", bukan penyebab tunggal |

**Klaim yang ditolak / tidak dipakai:**
- "Megalodon masih hidup di palung Mariana" — tidak ada bukti; fosil termuda 3,6 juta tahun.
- Angka gigitan dalam newton / ton — variasinya besar dan mudah salah kutip; diganti "jauh lebih kuat".
- "Megalodon sebesar bus" — perbandingan usang; diganti angka meter dan penyelam 1,8 m.
- "Megalodon penyebab kepunahan paus besar" — dibalik: paus justru bermigrasi dan megalodon kehilangan mangsa.

---

## 3. Yang "lebih mutakhir" di sisi kode (inti permintaan)

Bukan menambah animasi, tapi **membangun mesin baru v16** karena v15 punya dua kelemahan mendasar:

1. **Setiap bentuk digambar pada mask seukuran kanvas.** Pada SS=1,5 itu 1620×2880 = 4,7 juta piksel per
   poligon. `bentuk()` v15 mengalokasikan 3 gambar penuh *per bentuk*.
   → v16 `bentuk2/elips2` memotong ke **bbox bentuk itu sendiri**, dan gradasi isi **di-cache** per ukuran+warna.
2. **Tidak ada sistem air.** v15 hanya punya langit/laut datar.
   → v16 punya `air()` (gradasi kedalaman + pita arus), `sinar()` (berkas volumetrik), `kaustik()` (jaring
   cahaya di dasar, numpy), `salju()` (partikel laut), `gelembung()`.

**Hasil pengukuran (SS=1,5, kanvas 1620×2880):**

| Primitif | v15 / sebelum optimasi | v16 sesudah | Faktor |
|---|---:|---:|---:|
| `gigi(tinggi=560)` | 71 ms | **22 ms** | 3,2× |
| `baris_gigi` | 121 ms | **53 ms** | 2,3× |
| `kartu_judul/kartu2` | 276 ms | **13 ms** | 21× |
| satu adegan penuh (frame) | ~1,1 s | **~0,09 s** | 12× |

Kuncinya: (a) bbox-lokal, (b) cache gradasi, (c) dilasi mask dengan numpy shift menggantikan
`ImageFilter.MaxFilter` (MaxFilter pada bbox besar = operasi O(n·k²) di C, ~50 ms; numpy shift ~4 ms),
(d) bayangan kartu dibatasi ke bbox kartu.

**Tambahan audio:** `sfx.ambient_laut()` — bed samudra tiga lapis (rumble < 80 Hz, napas arus 120–600 Hz,
desis partikel 2–6 kHz), dibuat di domain frekuensi, level RMS dijaga tepat, loop aman (jumlah gelombang
bulat + fade 0,4 s). **Ini bukan musik** — hanya tekstur ruang, sesuai aturan "tanpa musik".

---

## 4. Rancangan 8 adegan

| Adegan | Isi | Dunia |
|---|---|---|
| intro | 24 m, hanya gigi yang tersisa | hiu utuh + gigi sebesar telapak tangan di dasar |
| f1 | 20 → 3,6 juta tahun; tulang rawan tidak memfosil | garis waktu dengan gigi-gigi fosil |
| f2 | 16,4 m dari 11 m tulang belakang; batas 24,3 m / 94 t | satu tubuh utuh + kurung per bagian + penyelam |
| f3 | bukan hiu putih yang diperbesar; lebih ramping | dua siluet panjang sama, tinggi badan beda |
| f4 | gigi bergerigi, 18 cm, puluhan ribu | potongan rahang 5 gigi + penggaris + serpihan gigi |
| f5 | gigitan; ekor dulu | mulut menganga + paus kecil + bekas luka |
| f6 | punah 3,6 juta tahun lalu, banyak sebab | air mendingin, paus migrasi, hiu putih kecil |
| outro | giginya ada, hiunya tidak | vitrin museum + siluet raksasa di belakang |

Kontinuitas: **air yang sama** di seluruh episode (satu gradasi kedalaman, satu sumber cahaya dari atas),
siluet raksasa yang sama muncul di intro dan outro (loop), dan warna aksen berubah per babak
(#2E7068 → #7ECAC0 → #B55839 → #3E6478).

---

## 5. Kejujuran data

- Jumlah permintaan per tema di `hasil_mendalam` tersimpan sebagai `jml` yang **kosong** untuk 16 tema teratas
  (0), jadi keputusan ini memakai **skor mentah + kuat + niat + pertumbuhan + status**, bukan jumlah mentah.
- Data permintaan berumur 9 hari dan tidak bisa disapu ulang dari sandbox (tidak ada akses YouTube).
- Dua video acuan tidak bisa ditonton; klaim "seperti video ini" dijawab lewat peningkatan mesin, bukan
  peniruan visual yang tidak terverifikasi.
