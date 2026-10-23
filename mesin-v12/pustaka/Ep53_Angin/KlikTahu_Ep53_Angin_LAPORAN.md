# LAPORAN PRODUKSI — Ep53 "Ke Mana Angin Pergi Setelah Meniup?"

**Tanggal produksi:** 23 Oktober 2026 · **Mesin:** V15 ILUSTRASI (baru) · **Agen:** Arena
**Branch:** `arena/322bf634-kliktahu` · **Keluaran:** `KlikTahu_Ep53_Angin.mp4`

---

## 1. Ringkasan

| Butir | Nilai |
|---|---|
| Judul | Ke Mana Angin Pergi Setelah Meniup? Ini Perjalanannya |
| Durasi | ±108,99 s (timeline) / 109,58 s audio master |
| Format | 1080×1920 · 60 fps · H.264 high · AAC 256 kbps 48 kHz |
| Naskah | 202 kata, 8 adegan, 92 cue kata, 36 definisi SFX |
| VO | `voice-04` (pria Indonesia, santai–tegas, tidak terlalu dalam) |
| Audio | master **−14,0 LUFS / TP −1,9 dBTP**, ambien angin −32 dB, 49 event SFX, **tanpa musik** |
| Gaya visual | ilustrasi kartun **full-bleed**, dunia berganti tiap babak, gelembung teks putih, angka besar sebagai penanda skala |

---

## 2. Kenapa mesin baru (V15 ILUSTRASI)

Acuan pemilik (23 Okt) adalah video kartun penuh layar: satu dunia ilustrasi yang berubah tahap demi tahap,
tanpa kamera/HUD, teks berupa gelembung putih di sepertiga bawah, angka besar sebagai penanda skala.

Mesin v12/v13/v14 dibangun untuk **diagram** (garis, label teknis, panel). Untuk Ep53 saya menulis pustaka
ilustrasi baru `mesin_v15_ilustrasi.py` dan modul episode `mesin_v15_ep53.py`, **tanpa mengubah mesin lama**
(Ep50–Ep52 tetap bisa dirender ulang). Palet tetap KlikTahu: krem kertas, navy, jingga, teal, pasir, terra, olive.

Fungsi ilustrasi: `grad_v`, `bentuk`, `elips_vol`, `awan`, `gunung`, `bukit`, `laut`, `pasir`, `cahaya_matahari`,
`matahari`, `pohon_kelapa`, `perahu`, `rumah`, `orang`, `layangan`, `angin`, `hujan`, `bintang_laut`,
plus tata letak: `kartu_judul`, `sumber`, `gelembung`, `angka_besar`, `kurva`, `garis_tebal`.

---

## 3. Tiga bug yang ditemukan dan diperbaiki di sesi ini

### 3.1 Bentuk hanya bergaris, tidak berisi (bug alpha)
`bentuk`/`elips_vol`/`awan` melakukan `lay.paste(fill_RGB, (0,0), msk)` pada layer **RGBA**. Paste dengan mask
pada layer RGBA hanya menimpa kanal warna; **alpha tetap 0**, jadi saat layer ditempel ke gambar, yang muncul
hanya garis luarnya. Gunung, pulau, dan awan tampak "kerangka".

Perbaikan: layer dibentuk dari RGB lalu alpha diisi eksplisit.
```python
lay = fill.convert("RGBA")
msk = m.crop(bbox).point(alpha)
lay.putalpha(msk)
img.paste(lay.convert("RGB"), (bbox[0], bbox[1]), lay)
```

### 3.2 Poligon gunung menutup lewat punggung (bug geometri)
Tutup polyline lereng dilakukan ke `(cx ± w/2, base)`, yaitu kaki gunung — sehingga sisi penutup **menyilang
punggung** dan yang terisi hanya irisan tipis di tepi. Perbaikan: tutup ke `(cx, base)` (titik di garis dasar,
di bawah puncak), jadi kedua lereng menjadi dua poligon tertutup yang benar.

### 3.3 VO tidak ditemukan (`TIDAK ADA sumber audio`)
`vo_manusia.py` mencari `<src>/<id_scene>.(wav|flac|m4a|mp3)` — **bukan** `audio_raw/` dan **bukan** nama
`NN_slug`. Berkas `01_intro.m4a … 08_outro.m4a` tidak akan pernah ketemu. Solusi yang dipakai: ganti nama
berkas menjadi id scene (`intro, f1 … f6, outro`) **tetap di `audio_raw/`**; `tools/render_lokal.sh` sudah
menyalin `audio_raw` → `audio` sebelum memanggil `vo_manusia.py`. Tidak ada perubahan kode.

---

## 4. Cara pratinjau yang benar (jangan `render.py --times`)

`render.py --times` menulis frame ke `../build/frames` yang **ephemeral** (hilang setelah proses). Pratinjau
yang dipakai di sesi ini:

```python
import os, json; os.environ["KT_BUILD"]="build"
import render as R, diagrams as D
R.SS = D.SS = 1.5                       # WAJIB disamakan, kalau tidak frame terpotong
tl = json.load(open("timeline.json"))
sc, tot, meta = tl["scenes"], tl["total"], tl["meta"]
for i, s in enumerate(sc):
    R.render_frame(s["start"] + 2.6, tot, sc, meta, f"/tmp/p{i}.png")
```
Hasil: ~1,2 s/frame (hangat). Lembar uji disimpan di `riset-kualitas/ref/v15_prev1…prev11.jpg`.

**Cek "tidak beku"**: dua frame berjarak 0,5 s di tiap adegan diukur beda luma rata-rata. Ep53: **4,8–7,1**
(semua adegan bergerak; target > 2).

---

## 5. Hasil QC

_(diisi setelah render penuh + qc_mp4 + qc_loop)_

---

## 6. Pelajaran untuk episode berikutnya

1. **Jangan `paste(RGB, mask)` pada layer RGBA** kalau mau isian. Pakai `putalpha`.
2. **Polyline yang ingin diisi harus ditutup ke titik di dalam area**, bukan ke titik yang membuat sisi
   penutup menyilang garis luar.
3. **Pratinjau lewat `render_frame`, bukan `--times`.** Selalu samakan `R.SS` dan `D.SS`.
4. **Jangan menaruh bayangan kartu sebagai elips besar** — jadi pita keruh. Pakai pita blur tipis
   (`GaussianBlur` σ≈16 pada 1080×1920 @SS1,5, alpha ±64).
5. **Label di langit, bukan di atas objek.** Semua pil label Ep53 dipindah ke area langit (y≈585–1010) supaya
   tidak menimpa rumah/pohon/perahu.
6. **VO "PERIKSA" pada onset < 100 ms belum tentu terpotong.** Di Ep53 f4/f6/outro onset 60–75 ms, tetapi
   sampel > −40 dBFS baru muncul 68–80 ms dan fade-in 30 ms selesai di −54 dBFS: itu **hening ruangan**,
   bukan fonem hilang. Cek amplitudo sebelum memutuskan render ulang.
