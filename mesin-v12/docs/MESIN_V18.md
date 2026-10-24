# MESIN v18 — ARSITEKTUR RENDER CEPAT (24 Okt 2026)

> Dokumen ini menjelaskan **mengapa** mesin v18 bisa merender 102,76 detik video
> 1080×1920 @ 60 fps dalam **4 menit** di mesin 2 inti, sedangkan v17 butuh
> **24 menit 52 detik** — dengan kualitas visual yang LEBIH baik, bukan lebih
> rendah. Baca ini sebelum mengubah `mesin_v18_*.py` atau `render_v18.py`.

---

## 1. Angka hasil

| | v17 "Laut Terang" | **v18 "Sprite Atlas"** |
|---|---:|---:|
| Render penuh (2 inti) | 24 m 52 s | **4 m 00 s** |
| Frame/detik | 4,1 | **25,7** |
| Komposisi per frame | 212–230 ms | **25–52 ms** |
| Encode | x264 `fast` | x264 **`slow` + CRF 14** |
| Kualitas encode (SSIM vs sumber) | 0,9893 | **0,9936** |
| Ukuran berkas | 77,75 MB | **33,18 MB** |
| Halaman kode inti | 1.311 | **3.274** |

Perhatikan kombinasi terakhir: v18 **lebih cepat 6×**, tapi memakai preset
encode yang **lebih lambat dan CRF lebih rendah** (kualitas lebih tinggi) dan
menghasilkan berkas **56 % lebih kecil**. Itu bukti bahwa yang dihemat adalah
pemborosan rasterisasi, bukan mutu.

---

## 2. Masalah v11–v17

Setiap frame, mesin lama memanggil fungsi gambar untuk **seluruh adegan**:

```
frame → gradasi laut (float32 1080×1920) → outline tiap objek → teks ulang
      → grain → simpan PNG/JPEG → (nanti) baca lagi untuk encode
```

Biaya terukur satu frame v17 (diukur di sesi v17):

| tahap | waktu |
|---|---:|
| simpan frame | 947 ms (PNG) / 16 ms (JPEG) |
| finishing v14 | 133 ms |
| penajaman | 8–77 ms |
| kamera | 22 ms |
| gradasi + outline + teks | ~50 ms |
| **total** | **212–230 ms** |

Yang mahal **bukan** "menggambar hiu", tapi **mengulang hal yang sama 6.166
kali**. Semua elemen statis (langit, air, pasir, rumput, kartu, sumber, HUD,
diagram) identik di setiap frame pada scene yang sama.

---

## 3. Gagasan inti v18

> **Raster sekali, tempel berkali-kali. Gerakkan dengan indeks, bukan gambar ulang.**

Tiga pilar:

### 3.1 Sprite atlas per scene
`latar_scene(i)` membangun latar scene ke-i **satu kali** (1,3 s untuk 8 scene)
lalu menyimpannya sebagai array RGB. Setiap frame mulai dari `latar.copy()`
(**0,43 ms**, memcpy 6 MB).

### 3.2 Gerak tanpa raster ulang
Badan ikan tidak digambar ulang. Sprite lurus digeser **per kolom** dengan fungsi
sinus (`swim()`), menghasilkan undulasi tubuh, kibasan ekor, dan napas dada:

```
dx = amp · p^1.7 · sin(2πx/λ − ωt)
sprite_baru = np.take(sprite, x − dx, axis=1)     # 0,6 ms untuk sprite 932×479
```

`np.take` 8× lebih cepat daripada fancy-indexing Python (`sprite[:, idx]` →
4,83 ms; `np.take(..., axis=1)` → 0,60 ms).

### 3.3 Komposisi integer pada kotak lokal
`blit()` hanya menyentuh kotak sprite (bukan seluruh kanvas), memakai aritmetika
`uint16` (bukan float32), dengan jalur cepat bila sprite sepenuhnya opak.
Sprite dipangkas dulu (`pangkas()`) sehingga kotak blit 44 % lebih kecil.

### 3.4 Pipe langsung ke x264
v17 menulis 6.166 berkas JPEG lalu membacanya lagi (≈2,5 menit terbuang + I/O).
v18 menulis frame mentah ke **stdin ffmpeg** (`rawvideo rgb24`), yang langsung
meng-encode H.264. Tidak ada berkas frame sama sekali.

---

## 4. Peta modul

| berkas | baris | isi |
|---|---:|---|
| `mesin_v18_inti.py` | 1.173 | angka/util, warna OKLab, noise, font & teks, sprite (raster/blit/swim), geometri, `Kanvas`, LUT |
| `mesin_v18_dunia.py` | 1.152 | palet, langit, air, cahaya, kaustik, pasir, hiu, paus, penyelam, gigi, kartu, label, HUD, diagram |
| `mesin_v18_ep55.py` | 651 | 8 scene Ep55: latar (sekali) + aktor (tiap frame), kartu judul, tabel `SCENES` |
| `render_v18.py` | 298 | renderer paralel, pipe ffmpeg, remux audio, profil kecepatan |
| `qc_v18.py` | 330 | gerbang mutu: kontainer, audio, loop, gambar, margin, faststart |
| `pustaka_v18.py` | 175 | thumbnail utama/alt + lembar pratinjau dari mesin yang sama |
| **total** | **3.779** | |

---

## 5. Keputusan desain yang MAHAL kalau dilanggar

1. **Jangan menyentuh `belly_mask` tanpa uji visual.** Perut harus dihitung dari
   mask siluet (bukan kurva terpisah), kalau tidak muncul "pita krem melayang"
   atau perut bocor keluar badan (bug nyata v18 awal).
2. **Semua detail (mata, insang, mulut, gurat sisi) WAJIB diklip** ke mask badan.
   Tanpa klip, garis keluar dari siluet — terlihat jelas pada video.
3. **Kartu judul: sprite punya padding 46 px** untuk bayangan. Saat menempel,
   kurangi 46 dari x dan y, kalau tidak judul keluar dari pelat krem.
4. **Langit satu gradasi utuh.** Dua gradasi bertumpuk + `kabut()` meninggalkan
   garis horizontal yang terlihat di video (bug nyata).
5. **Kaustik di-gather dari ubin, jangan di-blit per kotak.** Blit per ubin
   meninggalkan sengkar 512 px yang terlihat seperti ubin kamar mandi.
6. **`swim` memakai `np.take`**, bukan indexing (`spr[:, idx]`).
7. **Sprite wajib `pangkas()`** setelah diraster; jangan blit sprite 1.156 px
   untuk hiu selebar 932 px.
8. **`cv2.GaussianBlur` di OpenCV 5 menolak `ksize=(0,0)`** → pakai `gblur()`
   yang menghitung ksize ganjil.
9. **Vignette pakai `cv2.multiply` uint8** (1,5 ms), bukan float32 (13,7 ms).
10. **`blit()` harus aman untuk kanvas 3-kanal maupun 4-kanal** — sprite
    dikomposit di atas RGBA sebelum dipakai (lihat `komposit()`).

---

## 6. Kalau mau lebih cepat lagi

Urutan yang terbukti dari pengukuran (jangan menebak):

1. **Turunkan resolusio supersampling** `raster(ss=3) → 2` pada sprite kecil
   (hemat 0,4 s di `siapkan()`; tidak terlihat pada video final).
2. **`--jobs` 2 → 2** (mesin ini 2 inti; menambah proses TIDAK menolong).
3. **`--preset medium --crf 15`** → 21,9 s/600 frame (vs 24,5 s `slow` crf 14);
   SSIM turun 0,0007. Hanya dipakai kalau batas waktu sangat ketat.
4. **Matikan `_PARTIKEL_PUNAH`** (130 partikel) → hemat ~0,4 ms/frame.

Yang **tidak** menolong (sudah diuji): menambah `JOBS`/`CHUNKS`, menaikkan
`--jobs` di atas jumlah inti, mematikan vignette/grade (biayanya < 4 ms).

---

## 7. Perintah baku

```bash
# render penuh + audio (audio TIDAK di-encode ulang, hanya di-remux)
python3 render_v18.py --episode ep55 \
        --keluar dist/KlikTahu_Ep55_Megalodon_v18.mp4 \
        --audio pustaka/Ep55_Megalodon/KlikTahu_Ep55_Megalodon_audio.m4a \
        --jobs 2 --preset slow --crf 14

# gerbang mutu (wajib lulus sebelum unggah)
python3 qc_v18.py dist/KlikTahu_Ep55_Megalodon_v18.mp4 \
        --episode ep55 --audio pustaka/Ep55_Megalodon/KlikTahu_Ep55_Megalodon_audio.m4a

# aset pustaka (thumbnail + lembar pratinjau)
python3 pustaka_v18.py --episode ep55 --slug Ep55_Megalodon

# profil kecepatan tanpa encode
python3 render_v18.py --ukur --episode ep55
```

---

## 8. Struktur satu scene di `mesin_v18_ep55.py`

```python
def _latar_intro(k):        # SEKALI: langit, air, pasir, deret gigi, halo
    ...

def _aktor_intro(k, t, dur):  # TIAP FRAME: hiu + gelembung
    ...

SCENES = [dict(id="intro", judul=[...], kicker=..., sorot=(...),
               latar=_latar_intro, aktor=_aktor_intro, dur=10.65), ...]
```

`frame(t)` mencari scene dari `MULAI` (daftar kumulatif), menyalin latar,
memanggil aktor, menempel kartu + sumber, lalu grade LUT + vignette.
Scene terakhir menambahkan `_fade_loop` 1 detik ke latar intro supaya
**frame terakhir = frame pertama** (SSIM loop 0,987).

---

## 9. Hasil QC final (berkas yang diunggah)

```
durasi        102,76 s (timeline 102,76 s, 6.166 frame @ 60 fps)
resolusi      1080x1920 · h264 High yuv420p · faststart (moov @ 36 byte)
audio         AAC 48 kHz stereo · -14,4 LUFS · TP -1,6 dBTP
korelasi      vs master 1,0000 (selisih level +0,00 dB)
loop          SSIM 0,9868 · korelasi 0,9988
gambar        SSIM 0,9934 (min 0,9909) vs render ulang mesin
gelap         maks 3,0 % piksel gelap (tidak ada bidang gelap)
margin        tepi tajam maks 0,16 % (grafis penuh layar, wajar)
ukuran        33,18 MB
```
