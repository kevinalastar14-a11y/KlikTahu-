# Laporan Kualitas — Ep50 vs dua video referensi

**Tanggal:** 19 Oktober 2026
**Objek yang diukur**

| Kode | Berkas | Resolusi | Durasi | Ukuran |
|---|---|---|---|---|
| **EP50** | `KlikTahu_Ep50_Orionid_v2.mp4` | 1080×1920 (9:16) | 123,75 s | 90,0 MB |
| **REF-K** | `sancorp_kosmik_1080p60.mp4` | 1920×1080 (16:9) | 53,97 s | 83,3 MB |
| **REF-M** | `sancorp_mcp_1080p60_v2.mp4` | 1920×1080 (16:9) | 56,00 s | 39,9 MB |

Catatan penting: kedua referensi berformat **16:9 landscape**, bukan Shorts. Yang bisa
dibandingkan adalah **kerajinan gambar** (cahaya, kedalaman, ritme, tipografi), bukan
aspek rasio atau jenis kontennya.

Semua angka di bawah dihasilkan oleh `riset-kualitas/audit_kualitas.py` (bisa diulang).
Video referensi **tidak disimpan di repo** — hanya dipakai sebagai pembanding.

---

## 1. Ringkasan angka

| Metrik | EP50 | REF-K | REF-M | Tafsir |
|---|---:|---:|---:|---|
| Gerak rata-rata / frame | **0,72** | 4,82 | 5,58 | EP50 6–8× lebih tenang |
| Frame nyaris beku (<0,35) | **28,0 %** | 15,6 % | **1,5 %** | 1 dari 4 frame EP50 terasa diam |
| Kejadian gerak per detik | **0,22** | 0,54 | 0,91 | ritme EP50 paling jarang |
| Latar terang polos | **70,3 %** | 2,2 % | 1,9 % | EP50 nyaris selalu "kartu krem" |
| Area gelap (luma<70) | 22,3 % | 78,8 % | 92,2 % | referensi memakai layar penuh |
| Rasio kontras kanvas (p99−p1) | 232 | 146 | 165 | EP50 paling "curam" |
| Grain residual | 5,37 | 2,29 | 2,71 | grain EP50 2× lebih kasar |
| Blok rata 8×8 | 57,0 % | 41,2 % | 43,0 % | EP50 paling banyak bidang datar |
| Akutan tepi (p99) | 110,8 | 29,1 | 52,6 | angka EP50 **menipu** — lihat §3 |
| Colorfulness (Hasler-Süsstrunk) | 26,0 | 20,9 | 38,8 | wajar: palet EP50 memang tenang |

**Audio**

| Metrik | EP50 | REF-K | REF-M |
|---|---:|---:|---:|
| Loudness | **−14,0 LUFS** | — (tidak ada audio) | −12,8 LUFS |
| True peak | **−2,0 dBTP** | — | **+2,4 dBTP (clipping)** |
| LRA (dinamika) | **2,9** | — | 4,2 |
| Korelasi stereo | **1,000** | — | 0,917 |
| Side/Mid | **0,001 (mono)** | — | 0,208 |
| Presence 2–8 kHz | −16,7 dB | — | −21,8 dB |
| Air >8 kHz | **−32,6 dB** | — | −18,5 dB |

Kesimpulan audio yang jujur: **secara standar siaran, audio EP50 lebih benar** daripada
kedua referensi (loudness pas, tidak clipping). Yang kurang justru **lebar stereo (mono)
dan keterbukaan high-end (−32,6 dB)**.

---

## 2. Tujuh masalah yang menahan EP50 dari "terasa premium"

### 2.1 Satu template untuk 124 detik (paling besar)
Latar terang polos rata-rata **70,3 %** di **100 % frame** (rentang 57–77 %). Artinya
komposisinya hampir tidak pernah berubah: cakram langit di tengah, kartu krem di
sekelilingnya. Cakram itu hanya menempati **21,0 %** luas kanvas; **79 %** sisanya latar.
Di REF-K/REF-M latar terang polos hanya **2 %** — gambar memenuhi layar dan berganti
komposisi terus.

Efek yang dirasakan penonton: menit kedua terasa "itu-itu lagi", meski isinya baru.

### 2.2 Gerak terlalu tipis
Gerak 0,72 vs 4,82/5,58. **28 %** frame hampir beku. Standar produksi v12 sendiri
melarang "udara kosong > 0,4 s" dan mewajibkan "gerakkan sesuatu di setiap detik" —
EP50 belum memenuhi aturannya sendiri.

### 2.3 Grain terlalu kasar untuk palet terang
Grain residual 5,37 (vs 2,3–2,7). Di latar gelap, grain = tekstur film. Di latar
**krem terang**, grain = noise yang mengotori bidang bersih. Ini menjelaskan kenapa EP50
terlihat "sedikit kotor" saat di-zoom di HP.

### 2.4 Banding pada gradasi krem
**57 %** blok 8×8 nyaris rata. Pada panel krem, 200×200 px hanya berisi **22–38 tingkat
luma** — gradasi bertingkat (posterisasi) yang paling terlihat justru di area terang.

### 2.5 Tepi cakram aliased
Lompatan luma **158 level dalam 1 piksel** di tepi cakram. Inilah sebabnya "akutan tepi"
EP50 mencetak 110,8 — bukan karena tajam, tapi karena tepinya bergerigi. Cakram
digambar pada resolusi akhir, tidak ikut supersampling.

### 2.6 Tipografi sekunder terlalu kecil
Tinggi glyph pada 1080 px:

| Elemen | Tinggi | Di HP 6" (lebar 68 mm) |
|---|---:|---:|
| Chip "ORIONID · PUNCAK 21–22 OKT" | 17 px | **1,1 mm** |
| Baris kecil "OKTOBER 2026 · …" | 16 px | **1,0 mm** |
| Judul utama (2 baris) | 48–49 px | 3,0–3,1 mm |

Batas baca nyaman di HP ±2,5 mm. **Chip dan baris kecil praktis tidak terbaca** —
padahal 85 % penonton awal menonton tanpa suara.

### 2.7 Bintang tanpa atmosfer
Bintang digambar sebagai blob 2–3 px dengan halo rendah. Di REF-K bintang punya
difraksi + glow berlapis sehingga langit terasa "dalam". Kontribusi ke kesan premium
besar, biayanya hampir nol.

---

## 3. Yang sudah benar dan **jangan** diubah

- **Palet.** Krem hangat + navy + aksen jingga adalah identitas KlikTahu. Semua
  rekomendasi di bawah **tidak menyentuh hue**.
- **Keterbacaan teks utama.** Rasio kontras judul **6,94 : 1** — lolos WCAG AA.
- **Zona aman Shorts.** 0,00 % piksel di area berbahaya (y > 1640). Disiplin bagus.
- **Disiplin audio.** −14,0 LUFS / −2,0 dBTP, tanpa clipping, tanpa musik.
- **Loop & struktur 5 babak.** Sudah sesuai standar v12.

---

## 4. Bukti konsep: rantai finishing "V13" pada frame asli

Diterapkan pada 2 frame asli 1080×1920 (`riset-kualitas/prototipe_finishing.py`).
Prinsip: **hanya cahaya dan tekstur yang berubah, warna dasar dikunci**.

| Metrik | Frame 96 s sebelum | sesudah | Δ |
|---|---:|---:|---:|
| Blok rata 8×8 | 59,6 % | **42,8 %** | −16,8 poin (banding turun) |
| Entropy tonal | 4,027 | **4,124** | +0,10 |
| Grain | 3,36 | 3,36 | sama (bukan ditambah) |
| Piksel putih pecah | 0,26 % | **0,18 %** | membaik |
| Luma rata-rata | 182,72 | 180,83 | −1,9 (nyaris sama) |
| Warna krem (patch tengah) | 248,6·237,4·224,1 | 245,7·234,6·221,0 | geser ≤ 3 level (tak terlihat) |
| Rentang dinamis | 234,6 | 231,9 | −2,7 (tidak dipepetkan) |

Hasil visual: `riset-kualitas/hasil/perbandingan_ep50_096_sisi.jpg` (kiri asli, kanan V13).

Rantai yang dipakai: pendar cahaya dari **detail** terang (bukan dari bidang krem) →
pengaman highlight → kontras lokal halus → vinyet bersuhu 4 % → dither → grain halus.

Yang **tidak** dipakai: kurva nada global, LUT, hue shift, saturasi boost. Percobaan
pertama dengan S-curve sempat menggeser krem **8–13 level** dan memecahkan putih
0,26 %→1,79 %; itu ditolak karena melanggar "tetap seperti KlikTahu".

---

## 5. Rencana peningkatan (V13), urut dampak

### Lapis A — komposisi & gerak (dampak terbesar, ±70 % perbaikan terasa)
1. **Full-bleed bertahap.** Cakram langit melebar keluar layar (bukan selalu bulat
   utuh): minimal 3 adegan memakai langit penuh sampai tepi kanvas.
2. **Komposisi berganti per babak**: porthole → horizon penuh → diagram penuh →
   close-up → kembali ke porthole (loop).
3. **Gerak terus-menerus**: drift kamera 0,6–1,2 %/s + parallax 3 lapis, nol frame
   beku. Target: frame beku < 5 %.
4. **Ritme**: satu kejadian visual per 1,5–2 s (target 0,5–0,9 kejadian/detik).

### Lapis B — cahaya & optik (yang membuat referensi terasa "film")
5. **Halation dua radius** dari sumber terang saja (matahari, kilau, bintang terang).
6. **Bloom ambang tinggi** (0,72 sudah dipakai; naikkan ke 0,80 agar krem tidak ikut).
7. **Bintang berlapis**: inti + glow + spike difraksi 4 arah untuk 6–10 bintang terang.
8. **Grain adaptif**: 2,0–2,4 di area terang, 3,5–4,0 di area gelap (sekarang rata 5,4).
9. **Dither terstruktur** pada gradasi krem → hilangkan banding.
10. **Tepi cakram di-supersample** (render @2× lalu downscale) → hilangkan gerigi.

### Lapis C — tipografi & UI
11. **Skala ulang**: judul 48→72–80 px; chip 17→30 px; baris kecil 16→28 px
    (semua ≥ 2,5 mm di HP 6").
12. **Hierarki 3 tingkat** yang konsisten: judul / label / mikro.
13. **Chip & tanggal** diberi bentuk sendiri (bukan teks kecil mengambang).

### Lapis D — audio (kecil tapi terasa)
14. **Lebar stereo**: VO tetap center, SFX/ambient dipan 25–40 % → side/mid 0,10–0,20.
15. **Air >8 kHz**: naikkan rak halus +1,5–2 dB di 9–12 kHz agar tidak "muffled".
16. **Dinamika**: LRA 2,9 → 4–5 dengan jeda strategis (bukan kompresi tambahan).

### Lapis E — encoder
17. Naikkan VBITRATE 5.900k → 8.000–9.000k untuk 1080p60 dengan grain halus
    (batas 100 MB per berkas Drive; 124 s × 8 Mbps ≈ 124 MB → perlu potong durasi
    atau pakai `initiate_resumable_upload`).

---

## 6. Target terukur setelah V13

| Metrik | Sekarang | Target |
|---|---:|---:|
| Frame beku | 28,0 % | < 8 % |
| Gerak rata-rata | 0,72 | 1,6–2,2 |
| Kejadian/detik | 0,22 | 0,50–0,90 |
| Latar terang polos | 70,3 % | < 55 % |
| Blok rata 8×8 | 57,0 % | < 45 % |
| Grain | 5,37 | 2,4–3,0 |
| Glyph terkecil | 16 px | ≥ 28 px |
| Side/Mid audio | 0,001 | 0,10–0,20 |
| True peak | −2,0 dBTP | ≤ −1,5 dBTP |
| Loudness | −14,0 LUFS | −14,0 ±0,5 |

Semua target di atas bisa diperiksa ulang dengan skrip audit yang sama.

---

## 7. Berkas

| Berkas | Isi |
|---|---|
| `audit_kualitas.py` | pengukur 20+ metrik visual/audio, bisa diulang |
| `prototipe_finishing.py` | rantai V13 + pembanding sebelum/sesudah |
| `hasil/ringkasan.csv` / `.json` | angka ketiga video |
| `hasil/*.mp4.json` | detail per video (termasuk palet dominan) |
| `hasil/perbandingan_*_sisi.jpg` | bukti visual sebelum/sesudah |
