# MESIN V20 — "KEDALAMAN" (Short 1080×1920 · 60 fps)

Ringkasan: v20 menaikkan bahasa visual v19 (gelap, bercahaya, ber-HUD) ke
tingkat produksi kelas atas — **tiga lapisan kedalaman**, kabut atmosfer,
bloom selektif, caption karaoke, panel data yang mengisi seluruh layar, gerak
kamera (punch-in + goban tangan + whip), dan rantai audio yang dihitung untuk
telinga manusia, keluar sebagai **M4A 320 kbps** (bukan WAV).

Episode perdana: **Ep56 — "Kamu Merasa Jatuh Tepat Sebelum Tidur"**
(hypnic jerk). 10 babak, 75,9 detik, 4.554 frame.

---

## 1. Berkas

| Berkas | Baris | Isi |
|---|---:|---|
| `mesin_v20_cahaya.py` | 1.110 | bahasa visual: palet, latar (kamar/jatuh/otak/langit), cahaya volumetrik, panel kaca, caption karaoke, grafik, kamera, LUT/grain |
| `mesin_v20_makhluk.py` | 660 | objek & figur: kasur, orang tidur, figur 4 pose, otak, primata, dahan, jam, kabel saraf |
| `mesin_v20_ep56.py` | 820 | episode Ep56: 10 babak, HUD, panel data bawah, tabel scene, `frame()` |
| `mesin_v20_audio.py` | 470 | rantai audio persepsi (EQ biquad, de-esser, kompresor, loudnorm) → M4A |
| `mesin_v20_suara.py` | 390 | TTS edge-tts → rapikan → timing → campur SFX/ambien → master |
| `render_v20.py` | 380 | renderer N proses (pipe rawvideo → x264), concat, mux audio |
| `qc_v20.py` | 300 | 24 pemeriksaan QC (kontainer, audio, gambar-vs-mesin, HUD, caption, loop, gerak) |
| `pustaka_v20.py` | 330 | thumbnail utama/alt, lembar pratinjau, METADATA.md, SIAP_TEMPEL.md |
| **Total** | **4.460** | di luar inti raster v18 (1.173) yang dipakai ulang |

## 2. Palet

```
MALAM_0 (3,5,12)   MALAM_1 (7,11,24)   MALAM_2 (12,19,40)   MALAM_3 (19,29,60)
CYAN (88,212,246)  GOLD (255,196,84)   CORAL (255,112,96)
VIOLET (184,142,255)  GREEN (104,236,178)  BLUE (96,152,255)
TEKS (242,246,255)  TEKS_2 (180,192,216)  TEKS_3 (118,132,160)
```

Satu babak = satu warna aksen. Badge, pill, grafik, dan progres memakai warna
aksen yang sama; tidak ada babak dengan lebih dari dua aksen.

## 3. Zona tata letak (1080×1920)

| y | Isi |
|---|---|
| 46–100 | HUD: merek kiri, badge babak kanan |
| 190–1150 | isi babak (visual utama + teks/data) |
| 1120–1420 | **scrim** (pita gelap) + caption karaoke di y=1256 |
| 1416–1732 | panel data bawah: 3 baris label/nilai |
| 1806 | baris sumber |
| 1886 | progres segmen |

Pelajaran dari pratinjau v19: kalau isi hanya memakai 260–1010, sepertiga layar
kosong. v20 memakai 190–1150 (≈50% tinggi) + panel data bawah sehingga setiap
zona layar membawa informasi.

## 4. Bahasa visual yang dibangun

* **Kedalaman**: latar (jauh, kabur) + objek (tengah, rim light) + debu/bokeh
  (dekat, parallax berbeda). Kabut atmosfer `C.nebula` memakai fBm yang
  di-blur 1/40 tinggi — bukan fBm mentah (yang terbaca "kembang kol").
* **Cahaya**: `berkas` (god ray bermodulasi), `pendar` (glow premultiplied),
  `flare_anamorfik`, `kilau_kaustik`, `sorot_spot`.
* **Tipografi**: `tulis_wipe` (mask reveal), `angka` (nilai + satuan + label),
  `caption_karaoke` (kata menyala mengikuti waktu ucap).
* **Grafik**: `grafik_area` (area bergradasi + garis menyala), `grafik_batang`,
  `piktogram` (7 dari 10), `eeg` (gelombang prosedural).
* **Kamera**: `dorong` (punch-in), `shake` (dua sinus tak selaras), `whip`
  (blur arah saat cut). HUD & caption digambar SETELAH kamera → tetap tajam.
* **Finishing**: LUT filmis (S-curve + lift dingin), vignette, aberasi ringan,
  grain uint8 dua polaritas yang diputar tiap 1/14 detik.

## 5. Audio (permintaan pemilik: "bukan WAV, untuk telinga manusia")

Rantai di `mesin_v20_audio.py` — semuanya numpy sendiri, tanpa plugin ffmpeg
selain loudnorm/limiter:

| # | Tahap | Nilai | Alasan |
|---|---|---|---|
| 1 | highpass | 72 Hz, Q 0,62 | membuang gemuruh ruangan, menghemat headroom |
| 2 | mud | 260 Hz, −2,2 dB, Q 1,1 | menghilangkan "selimut" yang menutupi konsonan |
| 3 | kejelasan | 3,2 kHz, +2,2 dB, Q 0,9 | pita yang membuat suara jelas di speaker HP |
| 4 | udara | high-shelf 11 kHz, +1,8 dB | kesegaran tanpa menambah desis |
| 5 | de-esser | 5,6–9,8 kHz, adaptif, maks 3 dB | rasio desis dibanding **pita tengah 300–3200 Hz** |
| 6 | kompresor | 2:1, lutut 9 dB, RMS | merapatkan jarak kalimat pelan/keras tanpa memompa |
| 7 | saturasi | tanh 1,15 + DC blok | kehangatan harmonisa orde rendah |
| 8 | loudnorm | −14,0 LUFS, TP −1,5 (2 lintasan) | standar YouTube/Shorts |
| 9 | limiter | −1,8 dBFS | AAC menambah +0,3 dB true peak saat encode |
| 10 | keluaran | **M4A AAC 320 kbps**, 48 kHz stereo | berkas kerja yang diunggah, bukan WAV |

Panjang sampel diperiksa di setiap tahap; `master()` memotong tepat di durasi
sumber setelah loudnorm (loudnorm menambal padding).

### Tiga cara mengisi jalur VO

| Jalur | Perintah | Catatan |
|---|---|---|
| TTS edge-tts | `python3 mesin_v20_suara.py --episode mesin_v20_ep56` | butuh jaringan |
| **VO rekaman manusia** | `python3 mesin_v20_suara.py --episode mesin_v20_ep56 --dari-berkas vo.m4a` | satu berkas; dipotong **pada jeda**, bukan rata `len/n` |
| Tanpa VO (bed saja) | `... --bed-only --target-lufs=-20` | dipakai kalau TTS & rekaman belum ada |

`batas_jeda()` mendeteksi jeda dengan RMS 20 ms (ambang adaptif persentil 15 +
7 dB) lalu memilih jeda yang paling dekat dengan posisi proporsional naskah,
dijaga tetap menaik dan berjarak minimal 0,15 s. Hasilnya `timing.json` — mesin
video otomatis mengikuti durasi baru tanpa menyentuh kode episode.

**Uji:** `python3 mesin_v20_audio.py --uji-sintetis` membangun sinyal mirip VO
(glotal + forman + desis buatan) lalu memverifikasi: panjang tidak berubah,
de-esser bekerja (desis murni → −3,0 dB), loudness −14,1 LUFS, TP −1,86 dBTP.

## 6. Render

```bash
# 1) audio (butuh jaringan untuk edge-tts)
python3 mesin_v20_suara.py --episode mesin_v20_ep56

# 2) render gambar + mux audio
python3 render_v20.py --episode ep56 \
    --keluar dist/KlikTahu_Ep56_HypnicJerk_v20.mp4 \
    --audio dist/KlikTahu_Ep56_audio.m4a --jobs 2 --preset slow --crf 16

# 3) QC
python3 qc_v20.py dist/KlikTahu_Ep56_HypnicJerk_v20.mp4 --episode ep56 \
    --audio dist/KlikTahu_Ep56_audio.m4a --json build_v20/qc.json

# 4) paket publikasi
python3 pustaka_v20.py --episode ep56 --slug Ep56_HypnicJerk
```

`--ukur` menampilkan biaya per babak; `--pratinjau 4` menulis 4 frame per babak
+ lembar kontak; `--potong 6` merender 6 detik pertama untuk uji cepat.

## 7. Jebakan yang ditemui (jangan diulang)

1. **Kanvas v18 menyimpan RGB, bukan RGBA.** `k.a[y0:y1, x0:x1] = (255,255,255,20)`
   gagal dengan pesan broadcast yang membingungkan. Selalu pakai `C._isi()`.
2. **`cv2.*` pada RGBA mengabaikan alpha** — gambar lewat lapisan + `blit`/`komposit`.
3. **`blit_add` v18 lambat** (16 ms untuk berkas cahaya 1200×460). Simpan sprite
   dalam bentuk **premultiplied** dan tambahkan dengan `cv2.add` → 3,9 ms.
4. **Jangan membuat lapisan sekanvas** (1920×1080×4 = 8 MB per panggilan, 20 ms).
   Semua goresan cv2 dibuat pada kotak lokal lalu ditempel.
5. **`cv2.multiply` butuh citra 3 kanal**: vignette 1 kanal → `np.repeat`.
6. **Grain jangan float32**: simpan lempeng uint8 positif/negatif (≈2 ms/frame).
7. **Ukur setelah pemanasan.** `--ukur` tanpa pemanasan melaporkan 300 ms/frame
   karena sprite & latar baru dibuat pada frame pertama.
8. **Thumbnail jangan memakai frame ber-HUD**: teks mesin bertumpuk dengan teks
   thumbnail. Pakai `frame(t, bersih=True)`.
9. **Rasio de-esser harus dibanding pita tengah**, bukan total. Pada vokal /a/
   energi 5,6–9,8 kHz hanya −12 dB dari puncak, sehingga ambang "total" tidak
   pernah memicu de-esser (terukur 0,00 dB sebelum diperbaiki).
10. **Font v18 tidak punya panah.** `→ ↓ ↑ ▸ ▶ ✓` dirender sebagai **kotak
    tofu**. Satu `→` sempat lolos ke render Ep56 (ikon kartu "OTAK SALAH BACA"
    dan "KEJUT"). Sekarang: `C.SANDI` mengalihkan karakter itu di `_aman()`
    (dipanggil semua jalur teks) dan panah besar digambar `C.panah()` dengan cv2.
    Selftest butir **glif lengkap** memeriksa setiap karakter yang dipakai.
11. **Kotak sprite ≠ kotak tinta.** Sprite teks membawa padding bayangan
    7–10 px; memakai kotak sprite untuk audit tabrakan menghasilkan alarm palsu.
    `C._catat()` memakai ambang alpha 24 sehingga yang diukur piksel yang benar-
    benar terbaca.
12. **Teks di bawah `Y_SCRIM` (1120) akan diredupkan scrim caption.** Bukan
    sekadar soal enak dilihat: text 1120–1416 digambar SEBELUM scrim, jadi
    kontrasnya turun dan caption bisa menimpanya. Selftest butir **tata letak**
    menolak teks apa pun di pita `Y_CAPTION-24 … Y_SCRIM[1]`.
13. **Blend loop ke `frame(0)` penuh menghasilkan hantu teks.** Selama 0,85 s
    terakhir, caption penutup ("...CUKUP TIDUR TERATUR") tembus dengan caption
    pembuka ("MERASA JATUH...") — terlihat seperti dua tulisan bertumpuk.
    Sekarang caption penutup diredupkan (`caption_karaoke(alpha=1-f)`) dan dasar
    blend memakai `frame(0, tanpa_caption=True)`; frame terakhir tetap identik
    dengan frame 0 (MAE 0,0), jadi loop masih mulus.
14. **`bersih=True` tidak menghapus tipografi adegan.** HUD/caption/panel hilang,
    tapi teks besar milik aktor tetap ada — thumbnail jadi teks-di-atas-teks.
    `frame(t, bersih=True, tanpa_teks=True)` membungkam semua tipografi
    (`C.TANPA_TEKS`) sementara panel/grafis/art tetap digambar.
15. **`susun()` pernah tidak bisa dijalankan sama sekali.** Buffer dibuat
    `int(total*SR)+SR` sampel, sedangkan ambien `int(total*SR)` — penjumlahan
    numpy melempar `ValueError: operands could not be broadcast`. Jalur VO tidak
    pernah dipakai sampai `--dari-berkas` diuji, jadi bug ini tidur lama.
    Buffer sekarang tepat `total*SR` dan hasil campuran di-clip ±1,0.

## 8. Audit tata letak otomatis

`mesin_v20_uji.py` butir 7 merekam setiap kotak teks (`C.AUDIT` diisi oleh
`tulis`, `tulis_wipe`, `label_kecil`, `panah`), lalu memeriksa tiga hal pada
tiap babak di 3 titik waktu (0,35 / 0,62 / 0,92 durasi):

1. kotak keluar kanvas 1080×1920;
2. kotak menyentuh pita caption (`Y_CAPTION-24`…`Y_SCRIM[1]`) > 240 px²;
3. dua kotak teks bertumpuk > 35 % kotak terkecil.

Uji ini menemukan **enam** tabrakan nyata di Ep56 yang tidak terlihat pada
lembar kontak (teks di bawah scrim, "SLEEP START" menimpa caption babak 2,
panel teori primata melewati pita caption, CTA penutup menabrak caption).

## 9. Hasil Ep56 v20

| Metrik | Nilai |
|---|---|
| Durasi | 75,90 s (4.554 frame @ 60 fps) |
| Ukuran | 1080×1920 · H.264 High · yuv420p · AAC 320k 48 kHz |
| Render | ±10 menit (2 inti, `slow`, CRF 16) |
| Biaya mesin | 56 ms/frame rata-rata → 17,8 fps per inti |
| Audio | −14 LUFS · TP −1,5 dBTP (target) |

Catatan transparan: pada sesi ini **TTS tidak dapat dijangkau** dari sandbox
(edge-tts butuh `speech.platform.bing.com`, yang tidak ada di daftar host
keluar). Video dirender dengan **bed audio** (SFX + ambien, −20 LUFS) dan
`naskah()`/`CAPTION[]` sudah siap; jalankan `mesin_v20_suara.py` di mesin yang
punya jaringan (lokal/Colab) lalu render ulang — timeline otomatis mengikuti
`audio/vo/timing.json`.
