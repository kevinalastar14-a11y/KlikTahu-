# LAPORAN PRODUKSI — Ep54 "Mata Minus Tidak Bisa Sembuh — Bola Matanya Sudah Memanjang"

**Tanggal produksi:** 23 Oktober 2026 · **Mesin:** V15 ILUSTRASI · **Agen:** Arena
**Branch:** `arena/322bf634-kliktahu` · **Keluaran:** `KlikTahu_Ep54_MataMinus.mp4`

---

## 1. Ringkasan

| Butir | Nilai |
|---|---|
| Judul | Mata Minus Tidak Bisa Sembuh — Bola Matanya Sudah Memanjang |
| Durasi | ±113,20 s (timeline) / 113,81 s audio master |
| Format | 1080×1920 · 60 fps · H.264 high · AAC 256 kbps 48 kHz |
| Naskah | 206 kata, 8 adegan, 80 cue kata, 25 definisi SFX |
| VO | `voice-04` (pria Indonesia, santai–tegas, tidak terlalu dalam) |
| Audio | master **−14,0 LUFS / TP −1,6 dBTP**, ambien ruang −32 dB, 38 event SFX, **tanpa musik** |
| Gaya visual | ilustrasi kartun **full-bleed**, satu dunia per adegan, kartu judul putih di y=1490, angka besar sebagai penanda skala |
| Pilar | TUBUH (bobot performa 0,81) |

**Posisi terhadap Ep53:** Ep54 bukan sekadar episode baru — ia memakai **tema ber-volume tertinggi di seluruh data**
(90 permintaan) dengan **niat tertinggi** (17 frasa bertanya), dan memindahkan gaya ilustrasi ke **objek yang belum
pernah digambar** (bola mata penampang, fundus retina, bagan Snellen). Ep53 mengandalkan lanskap; Ep54 harus
meyakinkan pada **anatomi**, dan itu menuntut geometri yang jauh lebih ketat.

---

## 2. Kenapa topik ini (bukan feeling)

Antrean tetap dihapus. Pemilihan dilakukan ulang dari `analisis/hasil_mendalam_20261015.json`,
`strategi_v6_20261015.json`, dan `performa.csv`, lalu diverifikasi dengan riset web. Rinciannya di
`analisis/EP54_RISET_23_OKT_2026.md`. Intinya:

| Sinyal | Tema `mata` | Pesaing terdekat |
|---|---|---|
| Volume permintaan | **90** (#1 dari 55 tema) | perut 74 · gigi 74 · mimpi 75 |
| Niat (frasa bertanya) | **17** (#1) | perut 25 (tapi Ep28 sudah) |
| Pertumbuhan | 224,4 (#2) | gigi 258,3 (Ep30 sudah) |
| Sudut belum dipakai | ya — mekanisme fisik | kedutan (Ep31 sudah) |

Klaster di dalam `mata` yang dipilih: **"mata minus"** — 11 frasa, 6 di posisi ≤5, termasuk autocomplete **#1
"kenapa mata minus"** dan **#2 "kenapa mata minus tidak bisa sembuh"**. Judul episode menjawab frasa #2 secara
harfiah, bukan menggodanya.

**Koreksi data:** dokumen 20 Okt memakai skor mentah `hasil_mendalam` (163,0 dst) yang bukan skor 5 faktor.
Laporan ini memakai angka mentah apa adanya (jml/kuat/niat/tumbuh) dan menyebutnya begitu — supaya tidak
terlihat lebih presisi daripada kenyataannya.

---

## 3. Tiga masalah visual yang ditemukan lewat pratinjau dan cara memperbaikinya

Sesi ini butuh **empat ronde pratinjau** (prev1 → prev4) sebelum render. Yang paling penting:

### 3.1 Dua "balok" di dalam bola mata (f1)
Iris digambar sebagai dua bilah persegi di dinding depan. Pada ukuran 1080 px, bilah itu terbaca sebagai
**sumbatan/penutup lensa**, bukan iris — dan menutupi berkas cahaya. **Perbaikan:** iris dibuang seluruhnya.
Penampang jadi skema optik yang jujur: kornea–lensa–retina, tanpa bagian yang salah baca. Lebih sedikit objek,
lebih cepat dimengerti — pelajaran yang sama seperti "jangan elips besar sebagai bayangan kartu" di Ep53.

### 3.2 Label bertumpuk dengan objek (f1, f3, f4)
Label `"BAYANGAN BURAM"` menempel di tepi bola (terpotong di luar kanvas), label lux menimpa kaki anak di panel
luar, dan gelembung "+40 MENIT DI LUAR" menimpa atap sekolah. **Perbaikan pola:** setiap label yang menunjuk
objek diberi **garis penunjuk dua segmen** dan diletakkan di area kosong (langit/latar), bukan di badan objek.
Ini aturan baru untuk pustaka: *label menunjuk, tidak menempel*.

### 3.3 Bagan Snellen yang menumpuk (f5)
Baris optotipe memakai `yy += fs * 1.9`; pada font 36–22 px jarak itu lebih kecil dari tinggi baris, jadi
"LPED" dan "PECFD" saling tindih. **Perbaikan:** posisi `y` ditulis tetap (306/380/444/502/552/596) — bagan mata
memang punya jarak tetap, jadi ini sekaligus lebih benar secara visual.

Bonus: fundus retina di f6 dirombak dari "bola cokelat dengan bintik" menjadi **pandangan fundus** (diskus optik,
pembuluh menyebar, makula, robekan ladam, tirai gelap menutup dari kiri). Robekan awalnya berbentuk panah —
terbaca seperti panah kursor, bukan robekan; diganti busur ladam.

---

## 4. Hasil QC

```
file     : dist/KlikTahu_Ep54_MataMinus.mp4
durasi   : 113.20 s (timeline 113.20)   ukuran 92,90 MB   bitrate 6565 kb/s
video    : h264 (High) yuv420p 1080x1920 60 fps
audio    : aac (LC) 48000 Hz, 256 kbps
lag audio: +0 ms   korelasi MP4 vs audio_master.wav: 0.9999   selisih level -0,01 dB
peak MP4 : -1,7 dBFS per kanal (L -1,7 / R -1,7)
VO 8/8 OK: intro 9,74 f1 16,88 f2 13,27 f3 13,91 f4 15,97 f5 13,54 f6 17,07 outro 8,17 s
master   : -14,0 LUFS / TP -1,6 dBTP / 113,81 s, 0 sampel clipping
loop     : frame0 vs akhir-0,03 s = 0,9997  -> LOOP OK
tata letak: check_layout "bersih ✔" (8 adegan), audit teks margin 40 px bersih (87 elemen)
gerak    : 4,63–9,15 beda luma per 0,5 s (semua adegan hidup; target > 2)
HASIL QC : SEMUA BERSIH ✔
```

`KT_FULLBLEED=1` menyala sejak awal (gaya ilustrasi penuh layar). Satu-satunya catatan audit adalah f6 yang
latar navy-nya menutup tepi — itu memang desain, bukan cacat.

**VO "PERIKSA" di intro dan f6** bukan potongan: sampel > −40 dBFS baru muncul di 58 ms / 127 ms, dan level
25 ms pertama **−56,3 / −52,8 dBFS** — itu hening ruangan, bukan fonem hilang. Diperiksa dengan mengukur
amplitudo, tidak diputuskan dari label skrip.

---

## 5. Berkas yang diunggah (Drive `KlikTahu_Produksi/Shorts/kliktahu-ep54-mata-minus`)

Folder: `1AVIzZJysxG_P_CW_pkiL0apjhqH-P-2O`

| Berkas | ID |
|---|---|
| KlikTahu_Ep54_MataMinus.mp4 | `1iylOQHZVQamTGQiq2XXEGdXIoiyUCTgR` |
| KlikTahu_Ep54_MataMinus_audio.m4a | `1XP9RlDZZFpe6BH1RoM1dP81PgmTQYS1A` |
| KlikTahu_Ep54_MataMinus_thumb_utama.png | `1gqZmmUyh3WGfNtYNGFJZ1FDfW3ygrjTo` |
| KlikTahu_Ep54_MataMinus_thumb_alt.png | `145pUyqOcrCX6jFsL0HYhr9XIb7NLQbJu` |
| KlikTahu_Ep54_MataMinus_lembar_pratinjau.jpg | `19Rg4Kcuy1gbxzxqH9JBZf5RR5dbkIYM-` |
| KlikTahu_Ep54_MataMinus_content.json | `1fRcWD2Vd4L1X2tUQva2zh24yby2DX7Wo` |
| SIAP_TEMPEL_Ep54.md | `1oaBCJM7hhyb43oYN2qgT8dSRMVj4wBzD` |
| METADATA_Ep54.md | `1NSs2-kVU8fXLnFNgkooYEyVrWz4uzxp1` |
| RISET_Ep54_23Okt2026.md | `1lT9z2P1pV31OsfBXU2bNJeAKKxFLz9Ot` |

---

## 6. Pelajaran untuk episode berikutnya

1. **Objek anatomis tidak punya toleransi.** Pada lanskap, satu pohon miring masih masuk akal; pada bola mata,
   satu bilah salah tempat langsung terbaca sebagai "gambar rusak". Kalau ragu, **buang objeknya** —
   penampang yang lebih sederhana justru lebih jelas.
2. **Label menunjuk, tidak menempel.** Garis penunjuk dua segmen + titik ujung; label selalu di area kosong.
3. **Angka bagan pakai posisi tetap.** Jangan menghitung jarak baris dari ukuran font pada bagan bertingkat.
4. **Pratinjau 4 ronde lebih murah daripada render 2 jam.** Total pratinjau ±1 menit/ronde, render 28 menit/potongan.
5. **Ukur audio, jangan percaya label.** "PERIKSA" dari `vo_manusia.py` adalah ambang heuristik; level 30 ms

   pertama yang menentukan apakah ada fonem hilang.
6. **File >8 MB di Drive bisa gagal lewat `upload_file` pada beberapa tipe**. MP4 92 MB lolos; JPEG 216 KB gagal
   (`file_transfer_failed`) lalu berhasil setelah dikonversi ke PNG. Kalau gagal, ubah format — jangan ulangi
   panggilan identik.
