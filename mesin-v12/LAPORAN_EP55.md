# LAPORAN PRODUKSI — Ep55 "Megalodon Bukan Hiu Putih Raksasa — Dan Kita Cuma Punya Giginya"

**Tanggal produksi:** 24 Oktober 2026 · **Mesin:** **V16 LAUT DALAM** (baru) · **Agen:** Arena
**Branch:** `arena/322bf634-kliktahu` · **Keluaran:** `KlikTahu_Ep55_Megalodon.mp4`

---

## 1. Ringkasan

| Butir | Nilai |
|---|---|
| Judul | Megalodon Bukan Hiu Putih Raksasa — Dan Kita Cuma Punya Giginya |
| Durasi | ±101,40 s (timeline) / 102,00 s audio master |
| Format | 1080×1920 · 60 fps · H.264 high · AAC 256 kbps 48 kHz |
| Naskah | 202 kata, 8 adegan, 48 cue kata, 28 definisi SFX |
| VO | `voice-05` (pria Indonesia) via `vo_manusia.py` — tanpa potong, tanpa atempo |
| Audio | master **−14,0 LUFS / TP −1,7 dBTP**, 0 sampel clipping, **ambien laut** (bukan musik) + SFX per kata |
| Gaya visual | ilustrasi **bawah laut** penuh layar; satu gradasi kedalaman untuk seluruh episode; kartu judul dengan kicker di dalam kartu |
| Pilar | HEWAN (bobot performa 0,92 — tertinggi kedua, belum pernah dipakai) |

---

## 2. Kenapa topik ini, dan kenapa "fokus ke kode"

**Topik.** Dari data 15 Okt: `mata` (163,0) baru saja dipakai Ep54, `perut` Ep28, `gigi` Ep30, `mimpi`
Ep21/25, `baterai & HP` pilar TEKNOLOGI 0,34. **Megalodon** skornya 76,6 tetapi pilarnya HEWAN (0,92),
pertumbuhannya 176,8, dan **belum pernah disentuh** dalam 16 episode berturut-turut bertema TUBUH.
Klaster frasanya ("megalodon adalah", "megalodon hidup di zaman apa", "apakah nyata") persis pertanyaan yang
dijawab episode ini. Rincian: `analisis/EP55_RISET_24_OKT_2026.md`.

**Acuan.** Dua video dari pemilik (`kitabedah.id` 88,23 s; `bit_wonder` 47,50 s) **tidak bisa diputar** di
sandbox ini: egress ke `lh3.googleusercontent.com` diblokir (`SSL_ERROR_SYSCALL`) dan connector Drive tidak
menyediakan streaming video. Yang terbaca hanya metadata (durasi, 720×1280). Karena itu "lebih mutakhir, fokus
ke kode" saya terjemahkan sebagai **pembangunan mesin baru**, bukan peniruan frame yang tidak bisa diverifikasi.

---

## 3. Mesin v16 — apa yang benar-benar berubah

### 3.1 Akar masalah v15
Setiap bentuk digambar pada **mask seukuran kanvas**: 1620×2880 = 4,7 juta piksel, dan `bentuk()` membuat
tiga bitmap sebesar itu **per bentuk**. Satu adegan butuh puluhan bentuk → 1,1 s/frame, dan gradasi isi
diskalakan ulang sehingga tepinya bisa bergerigi.

### 3.2 Yang diganti
| Komponen | v15 | v16 |
|---|---|---|
| Bentuk | mask kanvas | **bbox-lokal** + cache gradasi (`_grad_isi`) |
| Outline | `MaxFilter` pada bbox besar | **dilasi numpy shift** (`_dilate`) |
| Bayangan kartu | layer seukuran kanvas | **bbox kartu saja** |
| Air | `laut()` datar | **`air()`**: gradasi 6 lapis + pita arus |
| Cahaya | `cahaya_matahari()` | **`sinar()`** volumetrik + **`kaustik()`** numpy |
| Partikel | `butir_terbang()` | **`salju()`** + **`gelembung()`** deterministik |
| Hewan | `orang()`, `perahu()` | **`hiu()`** parametrik, **`paus()`**, **`penyelam()`** (skala meter) |

**Angka terukur (SS=1,5):**

```
gigi(560 px)      71 ms ->  22 ms   (3,2x)
baris_gigi        121 ms ->  53 ms   (2,3x)
kartu judul       276 ms ->  13 ms   (21x)
satu frame        ~1,1 s -> ~0,09 s  (12x)
```

Efek sampingnya penting: karena gambar jauh lebih murah, saya bisa menambah **lapisan** (berkas cahaya,
kaustik, partikel, gerigi bergerak di sepanjang tepi gigi) tanpa melewati anggaran waktu render.

### 3.3 Siluet hewan dari spline, bukan poligon kasar
`hiu()` dibangun dari Catmull-Rom pada sisi atas dan bawah tubuh, dengan parameter `tinggi` (rasio tebal/panjang)
dan `ekor_bulan`. Satu fungsi itu dipakai untuk tiga hal berbeda di episode ini: megalodon ramping (0,148),
hiu putih gempal (0,245), dan siluet raksasa di intro/outro. Tidak ada gambar yang diimpor — semuanya kode.

### 3.4 Gigi: dua kali ditolak sebelum benar
Versi pertama keluar sebagai **segitiga putih lebar** (terbaca seperti gigi hiu mainan); versi kedua, setelah
diberi akar, keluar sebagai **kapal layar**. Yang benar butuh tiga hal sekaligus: rasio tinggi:lebar ≈ 1,7:1,
tepi cembung yang menyempit, dan **takik gerigi nyata** pada tepi (bukan titik cat) + akar bercabang dua yang
pendek. Ini pelajaran yang sama seperti Ep54: objek anatomis tidak punya toleransi.

### 3.5 Audio: bed samudra, bukan musik
`sfx.ambient_laut()` membuat tiga lapis di domain frekuensi: rumble < 80 Hz (tekanan kedalaman), arus
120–600 Hz yang bernapas tiap ~9 s, dan desis partikel 2–6 kHz. RMS dijaga tepat di level yang diminta,
loop aman karena jumlah gelombang dibuat bulat dalam durasi + fade 0,4 s. **Tetap tanpa musik** — hanya tekstur.

---

## 4. Hasil QC

```
file     : dist/KlikTahu_Ep55_Megalodon.mp4
durasi   : 101,40 s (timeline 101,39)  ukuran 83,63 MB  bitrate 6598 kb/s
video    : h264 (High) yuv420p 1080x1920 60 fps
audio    : aac (LC) 48000 Hz, 256 kbps
lag audio: +0 ms   korelasi MP4 vs audio_master.wav: 1,0000   selisih level -0,01 dB
peak MP4 : -1,7 dBFS per kanal (L -1,7 / R -1,7)
VO 8/8 OK: intro 10,04 f1 11,54 f2 12,31 f3 10,93 f4 17,39 f5 12,48 f6 15,68 outro 7,25 s
master   : -14,0 LUFS / TP -1,7 dBTP / 102,00 s, 0 sampel clipping
loop     : frame0 vs akhir-0,03 s = 0,9997  -> LOOP OK
tata letak: check_layout "bersih ✔" (8 adegan), 57 elemen teks di dalam margin 40 px
gerak    : 5,14–7,80 beda luma per 0,5 s (semua adegan hidup; target > 2)
HASIL QC : SEMUA BERSIH ✔
```

`KT_FULLBLEED=1` menyala sejak awal — gaya bawah laut memang menutup seluruh tepi kanvas. Audit kasar
"sentuh tepi" melaporkan 28.000 tinta di setiap sisi untuk hampir semua adegan: itu **desain**, bukan cacat.

**VO f1 ditandai "PERIKSA"** (onset 90 ms). Diukur langsung: level 30 ms pertama **−55,7 dBFS**, sampel
> −40 dBFS baru muncul di 130 ms. Itu hening ruangan, bukan fonem hilang — sama seperti Ep53 dan Ep54.

---

## 5. Pelajaran untuk episode berikutnya

1. **Ukur dulu, optimalkan kemudian.** Profil 10 baris (`time.time()` per primitif) menunjukkan 3 fungsi
   menghabiskan 80 % waktu; menebak akan salah sasaran.
2. **`MaxFilter` bukan alat untuk bbox besar.** Dilasi numpy `np.maximum` pada shift window 4 ms vs 50 ms.
3. **Cache gradasi harus berukuran piksel**, bukan unit dunia — kalau tidak, gambar ter-cache salah ukuran
   (bug pertama yang muncul: `ValueError: images do not match`).
4. **Kartu judul memang harus punya kicker di dalam**; pil melayang di atas kartu akan selalu bertabrakan
   dengan ilustrasi begitu komposisinya berubah.
5. **Siluet hewan gunakan spline.** Segitiga dan trapesium akan selalu terbaca "kertas".
6. **Ambien baru harus diuji RMS-nya**, bukan hanya didengar: target −33 dB tercapai tepat (−33,1) dan
   peak −18,8 dBFS, jadi tidak akan menutupi VO.
7. **Jangan mengklaim meniru video yang tidak bisa ditonton.** Jujur soal batas ini lebih berguna daripada
   menebak isi frame-nya.

---

## 6. Berkas di Google Drive

**Folder:** `KlikTahu_Produksi/Shorts/kliktahu-ep55-megalodon`
<https://drive.google.com/drive/folders/18gLnIwOVZG5JrkcHOEhfCOtTRhFVdeFY>

| Berkas | Ukuran (byte) | Tautan |
|---|---:|---|
| `KlikTahu_Ep55_Megalodon.mp4` | 83.633.512 | <https://drive.google.com/file/d/1N4rr5ZJL5ug8xZwvCxuLmOFlCJF4AG7-/view> |
| `KlikTahu_Ep55_Megalodon_audio.m4a` | 3.291.504 | <https://drive.google.com/file/d/1Gmw53s6Qw5VLK3oDIhR10hZVNG5lJN3F/view> |
| `KlikTahu_Ep55_Megalodon_thumb_utama.png` | 811.745 | <https://drive.google.com/file/d/111V_G1rDoSntf7_2ewzXDNL0b_xsDwl6/view> |
| `KlikTahu_Ep55_Megalodon_thumb_alt.png` | 939.329 | <https://drive.google.com/file/d/16G-qfWLIIvuT3YvjU_2azztjiLtPoTSr/view> |
| `KlikTahu_Ep55_Megalodon_lembar_pratinjau.jpg` | 250.981 | <https://drive.google.com/file/d/1B3YdpPE_xAeQn5u6dDFwtKYs7Ifn1Mmj/view> |
| `KlikTahu_Ep55_Megalodon_content.json` | 6.320 | <https://drive.google.com/file/d/1Mcx1H4KpEIAPI9gNasQuhidOLu-MvHGE/view> |
| `SIAP_TEMPEL.md` | 2.699 | <https://drive.google.com/file/d/1Oz7w3R9BgSoqaQOopFIQBc0leFTFfgc6/view> |
| `METADATA.md` | 4.454 | <https://drive.google.com/file/d/1o4ABKDRzSQwCdsnRdUBSpN5sCxb9U3Z3/view> |

Ukuran MP4 di Drive **sama persis** dengan hasil render (83.633.512 byte), dicek lewat `list_files`.

> **Catatan penting — akun Drive berganti.** Saat konektor disambungkan ulang, Drive yang aktif ternyata
> **akun lain** dari yang dipakai Ep52–Ep54: folder induk lama `1yGe6zxru2uF-lLhC8LEKxihEqGFbWbcc` sekarang
> 404, pencarian `name contains 'KlikTahu'` mengembalikan 0 hasil, dan tidak ada shared drive. Struktur
> `KlikTahu_Produksi/Shorts` dibuat ulang di akun ini, jadi **Ep55 berada di akun berbeda dari episode
> sebelumnya**. Kalau akun produksi lama yang dimaksud, sambungkan ulang akun itu lalu unggah ulang dari
> `pustaka/Ep55_Megalodon/` + `dist/` (8 berkas, ±86 MB, tanpa perlu render).
