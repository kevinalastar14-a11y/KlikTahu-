# LAPORAN EP55 — versi 2 (mesin v17 "Laut Terang")

**Judul:** Megalodon Bukan Hiu Putih Raksasa — Dan Kita Cuma Punya Giginya
**Berkas:** `dist/KlikTahu_Ep55_Megalodon.mp4` · 1080×1920 · 60 fps · **99,02 s** · 77,75 MB

---

## 1. Kenapa versi pertama ditolak, dan apa yang diperbaiki

Kritik pemilik: *"hasil video jelek, kok malah berbeda dari video KlikTahu yang sebelumnya"*.
Itu benar dan penyebabnya bisa ditunjuk persis. Ep52–Ep54 hidup di **kertas krem**: latar terang,
objek beroutline tinta, sedikit ruang kosong. Mesin v16 yang saya bangun untuk Ep55 menenggelamkan
semuanya ke **teal gelap tanpa garis luar** — hewan menjadi siluet, kartu krem kehilangan kontras.
Dua bahasa visual yang berbeda, dan yang benar adalah milik KlikTahu.

| Unsur | Ep52–54 (acuan) | v16 (ditolak) | v17 (sekarang) |
|---|---|---|---|
| Latar | kertas krem + langit senja | teal gelap → hitam | langit krem → air teal muda, tidak ada yang mendekati hitam |
| Garis luar | tinta 3–4 px di semua objek | tidak ada (siluet) | tinta 3–4 px, termasuk sirip & ekor |
| Hewan | beroutline, perut krem, mata + insang | blok warna gelap | `hiu_t()`: perut krem, mata, 5 insang, 2 sirip kecil |
| Dasar | pasir krem bertepi | dasar gelap | pasir bertepi + kerikil + rumput laut |
| Tipografi | kartu krem beroutline, tab terakota | sama | sama (tidak diubah) |

## 2. Mesin v17 "Laut Terang" — apa yang baru di kode

`mesin_v17_terang.py` (622 baris) + `mesin_v17_ep55.py` (689 baris) = **1.311 baris**.

- **`grad_t()`** — gradasi TERANG dengan dither **per piksel**. v15 memakai dither per baris; di latar
  terang itu terbaca sebagai garis horizontal (cacat yang terlihat di percobaan pertama).
- **`langit()`, `matahari()`, `awan_kecil()`** — pita langit di atas permukaan; matahari beroutline
  dengan berkas pendek (bukan gradasi datar).
- **`permukaan()`** — garis gelombang beroutline + buih di puncak; menutup tepi kanvas.
- **`air_t()`** — gradasi 5 stop dari `(182,216,204)` ke `(58,124,116)`; **tidak ada hitam**.
- **`sinar_t()`** — berkas cahaya krem datar berpenampang miring, memudar tiga ruas.
- **`hiu_t()`** — hiu KlikTahu: badan beroutline, perut krem sebagai **poligon antara garis perut dan
  garis inset** (bukan pita tebal — versi pita membuat tepi bergerigi), sirip punggung 2 + dubur,
  ekor bulan/heteroserkal, insang, mata.
- **`paus_t()`, `penyelam_t()`, `_ikan_kecil()`, `_rumput()`** — biota pendukung beroutline.
- **`gigi_t()`** — gigi dengan **akar V bercabang** dan tepi bergerigi 7 pasang (takik 2,2 % tinggi).
- **`rahang_terbuka()`** — mulut menganga dari **dua rahang terpisah** + rongga gelap + gusi terakota.
  Versi balok + busur gigi menghasilkan kotak gelap yang tidak terbaca sebagai kepala.
- **`lempeng_fosil()` + `inset_kaca()`** — gigi kecil tertanam di lempeng, detail gerigi ditunjukkan
  lewat **kaca pembesar**.
- **`kurung_ukur()`, `panah()`** — alat ukur & arah beroutline.

**Empat kali gigi ditolak sebelum benar** (semuanya tercatat karena bentuknya salah, bukan warnanya):
1. gigi tegak 230–330 px → terbaca **layar kapal**;
2. gigi rebah 80° → terbaca **panah**;
3. deret raksasa di lempeng → terbaca **barisan kapal**;
4. benar: gigi **kecil (62–88 px)**, rapat, di atas **busur rahang**, akar terlihat, miring 8–20°;
   detail gerigi dipindah ke kaca pembesar.

## 3. Audio — "untuk telinga manusia", VO bukan WAV

`audio_telinga.py` (baru). Rantainya dirancang untuk persepsi, bukan sekadar angka:

| Tahap | Setelan | Alasan |
|---|---|---|
| HPF | 78 Hz, 2 kutub | gemuruh tak terdengar hanya memakan headroom |
| Mud cut | −1,2 dB @ 270 Hz | membersihkan "lumpur" yang membuat VO tertutup |
| Kejelasan | +1,6 dB @ 3,3 kHz | pita konsonan; inilah yang membuat suara *jelas* di speaker HP |
| Udara | +1,2 dB rak > 11 kHz | kesegaran tanpa menambah desis |
| De-esser | −2,4 dB maks @ 5,8–9,5 kHz | hanya pada frame yang desisnya dominan |
| Kompresor | 1,5:1 RMS, lutut 8 dB | merapatkan jarak kalimat pelan/keras, tanpa "memompa" |
| Loudness | −14,0 LUFS, TP −1,5 dBTP | standar Shorts; LRA 1,7 LU |

Hasil ukur: **−14,0 LUFS · TP −1,3 dBTP · 99,62 s (panjang tidak berubah 1 sampel pun) · 0 clipping**.
Berkas kerja/unggah audio: **M4A AAC 256 kbps** (`KlikTahu_Ep55_Megalodon_audio.m4a`);
WAV hanya dipakai sebagai perantara.

Catatan jujur: **VO lama hilang dari workspace** (folder `audio_raw/` dibersihkan saat snapshot), jadi
8 klip direkam ulang dengan `voice-05` dan naskah yang sama persis. Durasi VO baru berbeda tipis
(99,02 s vs 101,39 s pada v16) sehingga timeline ikut dihitung ulang.

## 4. Kecepatan render — permintaan "10 menit"

Diukur pada mesin 2 core (bukan 8): `nproc` = 2, `cpu.max` = 200000/100000. Paralelisme tidak bisa
dinaikkan, jadi seluruh percepatan harus datang dari kerja per frame.

| Tahap | Sebelum | Sesudah | Cara |
|---|---:|---:|---|
| Simpan frame | 947 ms (PNG) | **16 ms** (JPEG q97 4:4:4) | PNG pada ilustrasi kompleks sangat mahal; H.264 6,4 Mbps tidak melihat bedanya |
| Finishing v14 | 656 ms | **133 ms** | halation dihitung di 1/6 resolusi lalu **satu** upscale; split-tone & knee lewat LUT C; grain/dither varian siap pakai |
| Penajaman | 77 ms | **8 ms** | `ImageEnhance.Sharpness` (kernel 3×3) menggantikan UnsharpMask |
| Kamera | 40 ms | **22 ms** | BILINEAR (dorongan ≤ 3 %) |
| Mesh latar | 33 ms | **0** | `KT_MESH=0` berarti tidak dihitung (dulu dihitung lalu dikali 0) |
| Panel kartu | 35 ms | **~1 ms** | panel + bayangan GaussianBlur(16) di-cache |
| CA radial | 34 ms | **0/11 ms** | dimatikan — aberasi 1 px tidak terlihat di video |
| **Total render penuh** | **±45 menit** | **24 menit 52 detik** | 1,8× lebih cepat |

Rincian 24m52s: frame 814 s (0,14 s/frame/proses) + encode x264 `slow` 552 s + persiapan/QC 126 s.

**Untuk 10 menit, dua hal masih harus dilepas — dan keduanya menurunkan kualitas, jadi saya tidak
melakukannya diam-diam:**
1. `PRESET=fast` (sudah saya set sebagai default; SSIM **0,9944** vs `slow`, praktis identik)
   memotong encode 552 → 250 s ⇒ total **±19,8 menit**.
2. Sisanya hanya bisa dari isi gambar: finishing dimatikan total, `SS=0,75`, atau 30 fps.
   Itu akan terlihat. Yang tersedia sebagai **mode pratinjau** (bukan final): ±4–5 menit.

## 5. Hasil QC (berkas final)

| Pemeriksaan | Hasil |
|---|---|
| `qc_mp4` | **SEMUA BERSIH ✔** |
| Korelasi audio MP4 vs master | **0,9999** (selisih level −0,01 dB) |
| `qc_loop` frame 0 vs akhir | **OK ✔** (0,7405; komposisi outro = intro) |
| `check_layout` | bersih — semua elemen teks di dalam margin 40 px |
| Durasi / bitrate / codec | 99,02 s · 6586 kb/s · H.264 High yuv420p · AAC 255k 48 kHz |
| Audio | −14,0 LUFS · TP −1,3 dBTP · LRA 1,7 LU · 0 clipping |
| Video | 1080×1920 · 60 fps · 77,75 MB |

## 6. Pelajaran

1. **Identitas visual bukan detail kecil.** Mesin baru yang "lebih mutakhir" tapi keluar dari bahasa
   visual channel = pekerjaan yang harus diulang.
2. **Profil dulu.** 947 ms ternyata di penyimpanan PNG, bukan di gambar. Menebak akan salah sasaran.
3. **Di mesin 2 core, optimasi harus per frame**, bukan per proses.
4. **Bentuk gigi menentukan keterbacaan.** Tiga versi pertama salah bentuk (layar, panah), bukan salah warna.
5. **Dither per piksel wajib di latar terang**; per baris menghasilkan garis yang terlihat.
6. **Cache yang benar = panel + bayangan**, bukan seluruh kartu (teks berubah per adegan).
7. **Audio "enak" punya ukuran**: pita 3 kHz dan de-esser 5,8–9,5 kHz, bukan sekadar LUFS.
