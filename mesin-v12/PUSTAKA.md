# Pustaka KlikTahu - video & metadata per episode

> **Catatan 6 Okt 2026 (pindah akun & repo):** video **tidak lagi disimpan di repo ini maupun di
> Releases** — aturan keamanan akun, lihat `AGEN.md` §14. Hasil render diserahkan langsung ke pemilik
> sebagai berkas MP4 (`dist/`). Nama rilis di daftar di bawah (mis. `KlikTahu_Ep49_Bintang-76`) adalah
> riwayat dari repo/akun lama; tautannya tidak aktif di sini.

| apa | di mana |
|---|---|
| **Video** (mp4 siap upload) | diserahkan sebagai berkas — JANGAN di-commit ke repo |
| **Metadata & teks siap tempel** | folder `pustaka/<episode>/` di repo ini |
| **Peta kata kunci real-time** | `analisis/PETA_KATA_KUNCI.md` |

---

## VIDEO PANJANG 16:9

### Long02 - Perjalanan ke Dasar Laut Terdalam di Bumi
- Video: rilis `KlikTahu_Long02_LautDalam-<run>` (Latest) - aset `KlikTahu_Long02_LautDalam.mp4` - 1920x1080 - 30 fps (10:12)
- Thumbnail: aset `thumbnail.jpg` di rilis yang sama (1280x720)
- Teks siap tempel (judul, deskripsi + 10 bab, hashtag, tag): `pustaka/Long02_LautDalam/SIAP_TEMPEL.md`
- Metadata lengkap: `long/v02_laut_dalam/METADATA.md`
- Orisinal: 10 bab (0 m -> 10.935 m -> naik lagi), 1.114 kata VO voice-00, tanpa subtitle, SFX tanpa musik.
  Satu penyelaman tanpa putus: warna air, sinar matahari, salju laut & HUD kedalaman/tekanan/suhu/cahaya
  mengikuti kedalaman yang diucapkan narasi.

### Long01 - Apa yang Terjadi Kalau Kamu Masuk ke Lubang Hitam?
- Video: rilis `KlikTahu_Long01_LubangHitam-1` (Latest) - aset `KlikTahu_Long01_LubangHitam.mp4` - 1920x1080 - 30 fps (9:17)
- Thumbnail: aset `thumbnail.jpg` di rilis yang sama (1280x720)
- Teks siap tempel (judul, deskripsi + 10 bab, hashtag, tag): `pustaka/Long01_LubangHitam/SIAP_TEMPEL.md`
- Metadata lengkap: `long/v01_lubang_hitam/METADATA.md`
- Orisinal (bukan gabungan Shorts): 10 bab, 1.007 kata VO voice-00, tanpa subtitle, SFX tanpa musik. Mesin baru
  `long/mesin_long.py` (16:9) + visual `long/v01_lubang_hitam/visual.py`; animasi dikunci ke kata VO.
---

## Ep58 - Ikan yang Seharusnya Punah 66 Juta Tahun Lalu (coelacanth) — MESIN v21 "KERTAS"
- Video: `keluaran/KlikTahu_Ep58_Coelacanth_v21.mp4` — **1080x1920 · 60 fps** · **124,63 s** ·
  52,2 MB · 3,4 Mb/s (QC 23/23 · ronde 2)
- Gaya: meniru video short lama kanal (kertas krem, headline tinta, stabilo coral blok penuh,
  tab FAKTA n/7, kartu ilustrasi vektor, stiker). Semua aspek selain resolusi dinaikkan:
  sumber per babak, dua koreksi mitos, sudut lokal Manado, musik latar + ducking, selalu ada gerak.
- Ronde 2 (permintaan pemilik): watermark `@KlikTahu` baru (lencana K bergradasi), **bar progres
  segmen dihapus**, kualitas naik lewat kode (bayangan kartu dua lapis, vignette kertas, kaustik
  laut, sinar + gelembung, bayangan kontak, pop/goyang LANCZOS, detail ilustrasi dipotong mask).
- Audio: `keluaran/KlikTahu_Ep58_audio.m4a` — VO pria Indonesia + musik latar, −14,0 LUFS · TP −1,9 · LRA 3,7
- Analisis gaya & kebenaran isi: `pustaka/Ep58_Coelacanth/ANALISIS_GAYA.md` (pengukuran acuan
  240x426 · 30 fps · 58 kb/s · 144 s, dan apa yang diubah)
- Metadata & teks siap tempel: `pustaka/Ep58_Coelacanth/METADATA.md`, `SIAP_TEMPEL.md`,
  `fakta_sumber.md`, `subtitle_id.srt` (46 baris), `thumb_utama.jpg`, `thumb_alt.jpg`,
  `lembar_pratinjau.jpg`
- Mesin: `mesin_v21_kertas.py` (pustaka visual), `mesin_v21_ep58.py` (episode), `mesin_v21_musik.py`,
  `pustaka_v21.py`; catatan teknis + jebakan 23–32 di `docs/MESIN_V21.md`
- **Drive**: folder `KlikTahu_Produksi/Shorts/kliktahu-ep58-coelacanth`
  (`1T_kesoPZTVR86QnUnlZDErVFec2ahli5`) — video, audio, 2 thumbnail, lembar pratinjau,
  metadata, siap tempel, fakta & sumber, subtitle, analisis gaya. MP4/M4A **tidak** masuk repo.


---

## Ep57 - Kenapa Waktu Terasa Makin Cepat Saat Dewasa? — MESIN v20
- Video: `keluaran/KlikTahu_Ep57_Waktu_v20.mp4` — **1080x1920 · 60 fps** · **90,05 s** · 68,9 MB
  (varian `penuh` 10 babak, QC 24/24)
- Varian pendek: `keluaran/KlikTahu_Ep57_Waktu_v20_kilat.mp4` — **54,44 s** · 42,0 MB
  (6 babak, `KT_VARIAN=kilat`, QC 24/24)
- Audio: `keluaran/KlikTahu_Ep57_audio.m4a` — **VO pria Indonesia** + SFX + ambien,
  AAC 320k 48 kHz, −14,0 LUFS / TP −2,0 dBTP; QC VO 15/16 (klip babak 2 = 12,16 s,
  sedikit di atas batas kewajaran 12 s; isi kalimat utuh, bukan cacat audio)
- Sumber VO: `audio/vo57/sumber/01.mp3 … 10.mp3` + `audio/vo57/timing.json`
  (folder audio KHUSUS Ep57 — jebakan 19); varian kilat `audio/vo57_kilat/`
- Pratinjau 720p: `..._v20_720p.mp4` **8,32 MB** · `..._kilat_720p.mp4` **5,17 MB**
- Teks siap tempel: `pustaka/Ep57_Waktu/METADATA.md` + `SIAP_TEMPEL.md`
- Thumbnail: `pustaka/Ep57_Waktu/thumb_utama.jpg` (angka 2% + pita pembanding)
  + `thumb_alt.jpg` (uji A/B) + `lembar_pratinjau.jpg`
- Subtitle: `pustaka/Ep57_Waktu/subtitle_id.srt` — 13 baris
- 10 babak: jam dipercepat -> teori proporsional (20% vs 2%) -> survei 77% dari 918 orang ->
  otak menghitung dari penanda baru -> efek oddball -> studi 577 orang (Comm. Biology 2025) ->
  mitos memori lama dibantah studi 2026 -> rasa terburu-buru 10% vs usia 1-4% ->
  tiga cara memperlambat waktu -> penutup loop
- Sumber: Communications Biology (Sept 2025, 577 orang 18-88), Memory & Cognition (2026,
  120 dewasa), survei Ruth Ogden (2023, 918 orang), Friedman & Janssen (2010)
- **Drive (tujuan akhir, BUKAN GitHub):** `KlikTahu_Produksi/Shorts/kliktahu-ep57-waktu`
  — folder id `1tB7e9JzkwcAA5anlZOAEMYNXmqu_rUwJ`, 13 berkas: video penuh & kilat
  (+720p), audio M4A terpisah, METADATA.md, SIAP_TEMPEL.md, 2 thumbnail, lembar
  pratinjau, subtitle SRT, dan arsip klip VO per babak. Aturan pemilik (25 Okt 2026):
  video & metadata ke Drive, **tidak** ke GitHub Release dan tidak disimpan di repo.

---

## Ep56 - Kamu Merasa Jatuh Tepat Sebelum Tidur? (Hypnic Jerk) — MESIN v20
- Video: `keluaran/KlikTahu_Ep56_HypnicJerk_v20.mp4` — 1080x1920 · 60 fps · **79,32 s** · 58,3 MB (varian `penuh`, QC 24/24)
- Varian pendek: `keluaran/KlikTahu_Ep56_HypnicJerk_v20_kilat.mp4` — **48,08 s** · 35,8 MB (6 babak, `KT_VARIAN=kilat`, QC 24/24)
- Audio: `keluaran/KlikTahu_Ep56_audio.m4a` — **VO pria Indonesia** + SFX + ambien, AAC 320k 48 kHz,
  −14,1 LUFS / TP −1,9 dBTP; QC VO `qc_vo.py` 16/16
- Sumber VO: `audio/vo/sumber/01.mp3 … 10.mp3` (satu klip per babak) + `audio/vo/timing.json`
  (timeline INDUK 10 babak; varian kilat memakai `audio/vo_kilat/timing.json` — lihat jebakan 18
  di `docs/MESIN_V20.md`, berkas ini pernah tertimpa dan membuat render 75,9 s)
- Pratinjau 720p: `..._v20_720p.mp4` **7,15 MB** · `..._kilat_720p.mp4` **4,44 MB**
  (dibuat dengan `pratinjau_720p.py`, bukan perintah ffmpeg ketik tangan)
- Teks siap tempel: `pustaka/Ep56_HypnicJerk/METADATA.md` + `SIAP_TEMPEL.md`
- Thumbnail: `pustaka/Ep56_HypnicJerk/thumb_utama.jpg` (angka 7/10) + `thumb_alt.jpg` (uji A/B)
- Subtitle: `pustaka/Ep56_HypnicJerk/subtitle_id.srt` — 12 baris, waktu diambil dari fungsi
  yang sama dengan caption karaoke (tidak mungkin melenceng dari teks di layar)
- Analisis & alasan desain: `analisis/EP56_V20_ANALISIS.md` · mesin: `docs/MESIN_V20.md`
- 10 babak: sentakan -> nama -> sebaran 7/10 -> waktu N1 -> batang otak -> leluhur primata ->
  dua teori -> pemicu -> cara -> penutup (loop ke awal)

---

## Ep50 - Hujan Meteor Orionid 21-22 Oktober: Jam Berapa & Arah Mana (Tanpa Teleskop)
- Video: `KlikTahu_Ep50_Orionid.mp4` - 1080x1920 - 60 fps (116.8 s) - diserahkan via Google Drive
  `KlikTahu_Produksi/Shorts/kliktahu-ep50-orionid-2026/` (mp4 + thumbnail.jpg + audio master .m4a + SIAP_TEMPEL.md)
- Teks siap tempel (judul, deskripsi, hashtag, tag, struktur 5 babak, catatan unggah): `pustaka/Ep50_Orionid/SIAP_TEMPEL.md`
- Metadata ringkas: `episodes/ep50_orionid/METADATA.md`; naskah + cue visual: `episodes/ep50_orionid/content.json`
- Orisinal: episode pertama **mesin v12 KONTINUITAS** (`mesin_v12.py` + `mesin_v12_ep50.py`): satu sistem visual
  (cakram langit + cakrawala + chip tanggal) dari frame 0 sampai akhir, transisi morph (kalender -> jam -> kompas,
  langit -> peta orbit -> langit), 70 SFX dikunci ke kata (faster-whisper), ambient angin malam, loop frame akhir = frame 0.
- Jadwal terbit: Senin 19 Okt 2026 18.30-20.30 WIB (puncak Orionid malam Rabu 21 -> Kamis 22 Okt).

## Ep55 - Megalodon Bukan Hiu Putih Raksasa — Dan Kita Cuma Punya Giginya (SIAP, terbit 29-30 Okt 2026)
- Video: `KlikTahu_Ep55_Megalodon.mp4` - 1080x1920 - 60 fps - 101,40 s - 83,63 MB.
- QC: `qc_mp4` **SEMUA BERSIH** (audio korelasi 1,0000, lag +0 ms, VO 8/8, peak -1,7 dBFS, -14,0 LUFS / TP -1,7 dBTP, 0 clipping); `qc_loop` **0,9997**; `check_layout` bersih (57 elemen teks, margin 40 px).
- Pilar HEWAN (bobot performa 0,92 - tertinggi kedua, **belum pernah dipakai** dalam 16 episode TUBUH berturut-turut). Skor mentah 76,6, pertumbuhan 176,8. Rincian: `analisis/EP55_RISET_24_OKT_2026.md`.
- Sudut pembeda: **cara ilmuwan tahu ukuran dari gigi** - 16,4 m individu Belgia (1,8 + 11 + 3,6), batas 24,3 m / 94 t (Shimada dkk. 2025), tubuh lebih ramping dari hiu putih, gigi 18 cm bergerigi.
- **Mesin baru V16 LAUT DALAM** (`mesin_v16_laut.py` + `mesin_v16_ep55.py`): primitif bbox-lokal + cache gradasi (frame 1,1 s -> 0,09 s), dilasi numpy, sistem air (gradasi kedalaman, sinar volumetrik, kaustik), siluet parametrik hiu/paus/penyelam dari spline, gigi bergerigi takik + `baris_gigi`.
- Audio: **`sfx.ambient_laut()`** (baru) - bed samudra tiga lapis, level RMS dijaga (-33,1 dB), loop aman. Tetap **tanpa musik**.
- Drive: `KlikTahu_Produksi/Shorts/kliktahu-ep55-megalodon` = `18gLnIwOVZG5JrkcHOEhfCOtTRhFVdeFY` (8 berkas, MP4 83.633.512 B).
- Teks siap tempel: `pustaka/Ep55_Megalodon/SIAP_TEMPEL.md`; laporan: `LAPORAN_EP55.md`; catatan mesin: `AGEN.md` 21.

## Ep54 - Mata Minus Tidak Bisa Sembuh — Bola Matanya Sudah Memanjang (SIAP, terbit 27-28 Okt 2026)
- Video: `KlikTahu_Ep54_MataMinus.mp4` - 1080x1920 - 60 fps - 113,20 s - 92,90 MB (Drive `KlikTahu_Produksi/Shorts/kliktahu-ep54-mata-minus`, folder id `1AVIzZJysxG_P_CW_pkiL0apjhqH-P-2O`, 9 berkas).
- QC: `qc_mp4` **SEMUA BERSIH** (audio korelasi 0,9999, lag +0 ms, VO 8/8, peak -1,7 dBFS, -14,0 LUFS / TP -1,6 dBTP, 0 clipping); `qc_loop` **0,9997**; `check_layout` bersih (87 elemen teks, margin 40 px).
- Pilar TUBUH. Dipilih dari data 15 Okt: tema `mata` **volume #1 (90 permintaan)** dan **niat #1 (17 frasa bertanya)** dari 55 tema; klaster `mata minus` 11 frasa, 6 di posisi <=5 (autocomplete #1 "kenapa mata minus", #2 "kenapa mata minus tidak bisa sembuh"). Rincian: `analisis/EP54_RISET_23_OKT_2026.md`.
- Sudut pembeda: **fisik, bukan tips** - bola mata sudah memanjang (23-24 mm; +1 mm ~ 3 dioptri) dan tidak menyusut. Uji acak Guangzhou: +40 menit di luar/hari, 30,4% vs 39,5%. Tanda bahaya retina di atas minus 6.
- Mesin V15 ILUSTRASI (`mesin_v15_ilustrasi.py` + `mesin_v15_ep54.py`), 8 dunia baru: kelas POV buram, penampang bola mata + penggaris 24 mm, tiga kartu 24/25/26 mm, jendela terbelah 300 vs 100.000 lux, halaman sekolah, ruang periksa + bagan Snellen, fundus retina, kelas senja loop.
- VO `voice-04` via `vo_manusia.py` tanpa potong/atempo (206 kata); tanpa musik, ambien ruang -32 dB + 38 event SFX.
- Teks siap tempel: `pustaka/Ep54_MataMinus/SIAP_TEMPEL.md`; laporan: `LAPORAN_EP54.md`; catatan mesin: `AGEN.md` 20.

## Ep53 - Ke Mana Angin Pergi Setelah Meniup? Ini Perjalanannya (SIAP, terbit 25-26 Okt 2026)
- Video: `KlikTahu_Ep53_Angin.mp4` - 1080x1920 - 60 fps - 108,98 s - 89,62 MB (Drive `KlikTahu_Produksi/Shorts/kliktahu-ep53-angin`, folder id `1sDvBjXN4c3zOMYsFPhQzOWBAOOAhcQpx`, 9 berkas).
- QC: `qc_mp4` **SEMUA BERSIH** (audio korelasi 1.0000, VO 8/8, peak -2,0 dBFS, -14,0 LUFS / TP -1,9 dBTP); `qc_loop` **0,9996**; `check_layout` bersih.
- **Mesin baru V15 ILUSTRASI** (`mesin_v15_ilustrasi.py` + `mesin_v15_ep53.py`): ilustrasi kartun penuh layar, 8 dunia berganti (pantai, dua bukit tekanan, pantai siang, bumi, gunung+hujan, kepulauan muson, senja, kembali ke pantai), gelembung teks putih, angka 40.075 km sebagai penanda skala. Palet tetap KlikTahu; mesin v12-v14 tidak diubah.
- Gaya mengikuti acuan pemilik 23 Okt 2026 (Drive `1yH4LjYOJAdChg4P2yZLtZfbeXWzrhPLF`) - **gaya/komposisi**, bukan warnanya.
- VO `voice-04` (pria Indonesia) via `vo_manusia.py` tanpa potong/atempo; tanpa musik, ambien angin + SFX per kata.
- Teks siap tempel: `pustaka/Ep53_Angin/SIAP_TEMPEL.md`; laporan: `LAPORAN_EP53.md`; catatan mesin: `AGEN.md` 19.

## Ep52 - Cegukan Bisa Bertahan 68 Tahun — Ini yang Terjadi di Tubuh (SIAP, terbit 22-23 Okt 2026)
- Video: `KlikTahu_Ep52_Cegukan.mp4` - 1080x1920 - 60 fps - 104,80 s - 85,5 MB (Drive `KlikTahu_Produksi/Shorts/kliktahu-ep52-cegukan`, folder id `1LvhgfFUUnwmDDvfAWmet9EzJUfAevcKZ`).
- QC: `qc_mp4` SEMUA BERSIH (audio 0,9999, VO 8/8, peak -1,8 dBFS), -14,0 LUFS / TP -1,7 dBTP; loop 0,9679 mentah karena grain acak per frame, **0,9998 setelah denoise** (jarum 12:00 di kedua ujung).
- Dipilih dari riset ulang 20 Okt 2026 (`analisis/EP52_RISET_ULANG_20_OKT_2026.md`); antrean lama dihapus.
- Mesin V13 + finishing V14, 8 adegan, modul `mesin_v13_ep52.py`; VO `voice-04` (pria Indonesia) via `vo_manusia.py` tanpa potong/atempo.
- Teks siap tempel: `pustaka/Ep52_Cegukan/SIAP_TEMPEL.md`; laporan produksi: `LAPORAN_EP52.md`; thumbnail + lembar pratinjau: `pustaka/Ep52_Cegukan/`.

## Ep51 - Ular Masuk Rumah Saat Hujan? Bukan Cuma Banjir (v2, TERBIT 20 Okt 2026)
- Video: `KlikTahu_Ep51_Ular_Rumah_v2.mp4` - 1080x1920 - 60 fps - 101,53 s - 83,5 MB (Drive `KlikTahu_Produksi/Shorts/kliktahu-ep51-v2-riset-ulang`).
- QC: `qc_mp4` SEMUA BERSIH (audio 0,9999, VO 8/8), loop 0,9995, -14,0 LUFS / TP -1,6 dBTP.
- Teks siap tempel: `pustaka/Ep51_Ular_Rumah_v2/SIAP_TEMPEL.md`.

## Ep49 - Kenapa Bintang Berkedip, Tapi Planet Tidak?
- Video: rilis `KlikTahu_Ep49_Bintang-76` (Latest, run 36022773282) - aset `KlikTahu_Ep49_Bintang.mp4` - 1080x1920 - 60 fps (158.8 s)
- Teks siap tempel (judul, deskripsi, tag, komentar): `pustaka/Ep49_Bintang/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep49_bintang/METADATA.md`
- Topik #1 PAPAN STRATEGI v6 (bintang & galaksi 48,2), sudut pembeda "planet tidak berkedip" + momen Saturnus
  oposisi 4 Okt 2026. Episode pertama MESIN FX 2026 (`mesin_v11_ep49.py`): panel langit bergradasi terklip,
  bintang berkedip + paku difraksi, kantong udara membelokkan cahaya, titik vs piringan + grafik rata-rata,
  lintasan cakrawala, Sirius warna-warni + prisma, laser 90 km + cermin lentur. SFX baru `laser`, `angin`.

## Ep48 - Kenapa Jantung Tiba-tiba Berdebar Kencang?
- Video: rilis `KlikTahu_Ep48_Jantung-75` (Latest) - aset `KlikTahu_Ep48_Jantung.mp4` - 1080x1920 - 60 fps (153.6 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep48_Jantung/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep48_jantung/METADATA.md`
- Topik #1 PAPAN STRATEGI v6 (jantung & dada 45,8). Mesin v11 + SFX detak: jantung anatomis dengan simpul pemacu,
  EKG bergulir sinkron denyut, otak beralarm + adrenal + aliran adrenalin, kamar siang->malam, penampang dada,
  monitor detak ekstra + jeda, lingkaran napas 4-6 detik, daftar tanda bahaya.

## Ep47 - Kenapa Petir Sering Menyambar Pohon?
- Video: rilis `KlikTahu_Ep47_Petir-74` - aset `KlikTahu_Ep47_Petir.mp4` - 1080x1920 - 60 fps (139.2 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep47_Petir/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep47_petir/METADATA.md`
- Topik #1 PAPAN STRATEGI v6 (petir 42,6). Mesin v11 + SFX guntur: peta Jawa + Bogor 322 hari, batang suhu
  30.000 C vs matahari, pemandu bertahap, percikan penyambut, penampang batang (getah mendidih), loncatan samping,
  Empire State. Audio v5 (VO utuh, tanpa peredam napas).

## Ep46 - Megalodon Masih Hidup? Giginya yang Menjawab
- Video: rilis `KlikTahu_Ep46_Megalodon-73` - aset `KlikTahu_Ep46_Megalodon.mp4` - 1080x1920 - 60 fps (144.0 s, audio v5 VO utuh; -71 jangan dipakai)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep46_Megalodon/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep46_megalodon/METADATA.md`
- Topik #1 PAPAN STRATEGI v6 (megalodon 44,9; pesaing hanya bertanya, Ep46 menjawab). Mesin v11 + SFX: gigi
  bergerigi vs telapak tangan & pisau roti, skala 16/24 m, sabuk gigi berganti, lapisan batuan 3,6 juta th, 73%.

## Ep45 - Kenapa Luar Angkasa Gelap Padahal Ada Matahari?
- Video: rilis `KlikTahu_Ep45_Langit-72` - aset `KlikTahu_Ep45_Langit.mp4` - 1080x1920 - 60 fps (147.2 s, audio v5 VO utuh; -70 jangan dipakai)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep45_Langit/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep45_langit/METADATA.md`
- Topik #1 PAPAN STRATEGI v6 (matahari 47,8; sudut PADAHAL). Mesin v11 + SFX: senter di kamar bersih vs berdebu,
  langit biru dari molekul udara, balon naik sampai langit hitam, matahari putih, paradoks Olbers, 13,8 M tahun.

## Ep44 - Gunung Padang Piramida Tertua di Dunia? Ini Kata Buktinya
- Video: rilis `KlikTahu_Ep44_Padang-69` (Latest) - aset `KlikTahu_Ep44_Padang.mp4` - 1080x1920 - 60 fps (156.1 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep44_Padang/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep44_padang/METADATA.md`
- Topik #1 PAPAN STRATEGI v6 (situs misteri indonesia 46,9; pilar MISTERI). Mesin v11 + SFX: bukit 5 teras +
  370 tangga, lava retak jadi prisma, dinding disusun, batu kecapi berbunyi, stempel DICABUT 2024, lapisan umur.

## Ep43 - Kuping Tiba-Tiba Berdenging? Itu Suara dari Dalam Telingamu
- Video: rilis `KlikTahu_Ep43_Kuping-68` (Latest) - aset `KlikTahu_Ep43_Kuping.mp4` - 1080x1920 - 60 fps (153,4 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep43_Kuping/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep43_kuping/METADATA.md`
- Topik #1 PAPAN STRATEGI v6 (kuping 45,1; sudut PRIBADI). Mesin v11 + SFX: telinga NGIIING, zoom ke
  koklea + sel rambut, eksperimen ruang hening 1953 (94%), equalizer otak, grafik batas aman WHO, slider 60%.

## Ep42 - Sinyal Penuh Tapi Internet Lemot? Ini Sebabnya
- Video: rilis `KlikTahu_Ep42_Sinyal-67` - aset `KlikTahu_Ep42_Sinyal.mp4` - 1080x1920 - 60 fps (158,0 s)
- Catatan: "Ep42 Listrik & Magnet" (rilis -66) dibuat sesi paralel di branch lama; nomor berikutnya Ep43
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep42_Sinyal/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep42_sinyal/METADATA.md`
- Topik #1 PAPAN STRATEGI v6 (internet & sinyal 49,2; sudut PADAHAL/KENAPA). EPISODE PERTAMA MESIN v11
  "EDITOR": judul kinetik + stabilo, stiker pop, penanda FAKTA n/7, transisi punch/slide/glitch, dorongan
  kamera di beat, + SFX sintetis (88 event, tanpa musik). VO voice-00 10/10 BERSIH.

## Ep41 - Itu Bukan Hantu, Itu Otakmu
- Video: rilis terbaru - aset `KlikTahu_Ep41_Hantu.mp4` - 1080x1920 - 60 fps (143,0 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep41_Hantu/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep41_hantu/METADATA.md`
- Topik #1 SEGAR (hantu & supranatural 84,1 + momen Halloween 31 Okt); MESIN: `_figur41` (orang
  terlentang + kunci REM), trio pareidolia (gorden/colokan/jaket), `_gel41` (gelombang 19 Hz + kipas
  Vic Tandy), kamera sugesti, checklist hijau, banner "HANTU ITU ADA, DONG?" + stamp "BELUM BUKTI";
  VO voice-00 take-2 10/10 BERSIH (133,8 s @1,67-1,79 kata/s); timeline 143,0 s; ink worst 974

## Ep40 - Gerhana Bukan Pertanda Kiamat
- Video: rilis terbaru - aset `KlikTahu_Ep40_Gerhana.mp4` - 1080x1920 - 60 fps (158,5 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep40_Gerhana/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep40_gerhana/METADATA.md`
- Topik #1 SEGAR (gerhana; CI penuh 214,4); MESIN: `_sun40` (matahari sinar denyut), `_earth40`,
  `_moon40` (cakupan bayangan progresif + fase merah), `_umbra40` (kerucut bayangan + penumbra);
  9 adegan: segaris matahari-bumi-bulan, dua arah gerhana, umbra/penumbra, bulan darah (sunset dunia),
  aman vs bahaya (retina), orbit miring 5 derajat, mitos + jadwal 2031/2042; VO voice-00 take-1
  10/10 BERSIH (149,3 s @1,76-1,83 kata/s); durasi bebas (MAXDUR 178, TARGET_WPS 1,90)

## Ep39 - Bintang Jatuh Itu Bukan Bintang (Meteor & Komet)
- Video: rilis terbaru - aset `KlikTahu_Ep39_Meteor_Komet.mp4` - 1080x1920 - 60 fps (135,8 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep39_Meteor_Komet/SIAP_TEMPEL.md`
- Metadata lengkap: `episodes/ep39_meteor_komet/METADATA.md`
- Topik #1 SEGAR (meteor & komet 222,4; velocity 20,5 tercepat; momen Orionids 21-22 Okt);
  **MESIN v10 (anti-zona-kosong):** `_ambien10` (bokeh + plus melayang di SEMUA adegan),
  `_langit39` (langit malam + bintang berkelip + meteor streak), `_komet39` (komet es-debu);
  9 adegan: jalur meteoroid-meteor-meteorit, 66 km/dtk, kode warna unsur (Mg/Fe/Ca/Ni),
  Orionids-Halley, komet vs asteroid vs meteor, mitos ramalan, panduan nonton;
  VO voice-00 take-2 10/10 bersih (126,6 s), tata letak bersih, ink worst 263

## Ep38 - Kenapa Baterai Cepat Habis Padahal Nggak Dipakai?
- Video: rilis terbaru - aset `KlikTahu_Ep38_Baterai.mp4` - 1080x1920 - 60 fps (139,8 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep38_Baterai/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep38_Baterai/METADATA.md`
- Topik #1 SEGAR (baterai & hp 315,2; velocity +14,4 tercepat); MESIN: `_hp38` (HP + indikator
  baterai, uap panas, charger, persen lompat) + `_sel38` (sel Li-ion ion bolak-balik); mitos
  cas semalaman + slider zona 20-80%; VO voice-03 take-1 10/10 bersih (123,2 s mentah)

## Ep37 - Kenapa Jerawat Muncul?
- Video: rilis terbaru - aset `KlikTahu_Ep37_Jerawat.mp4` - 1080x1920 - 60 fps (119,4 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep37_Jerawat/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep37_Jerawat/METADATA.md`
- Topik #2 antrean SEGAR (keluarga kulit ~296); MESIN v9 (folikel 4-keadaan, tekstur pori,
  kaca pembesar); VO take-1 10/10 bersih; episode terpendek sejak Ep30

## Ep36 - Kenapa Migrain?
- Video: rilis terbaru - aset `KlikTahu_Ep36_Migrain.mp4` - 1080x1920 - 60 fps (133,7 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep36_Migrain/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep36_Migrain/METADATA.md`
- Topik #1 antrean SEGAR (pusing & migrain 325,6); MESIN v9 penuh (CSD wave, CGRP loop,
  flip obat) - episode pertama yang naskahnya direkam ulang karena TTS lambat (149,6 -> 125,3 s)

## Ep35 - Supermoon 2026 & Ilusi Bulan Raksasa
- Video: rilis terbaru - aset `KlikTahu_Ep35_Supermoon.mp4` - 1080x1920 - 60 fps (139,6 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep35_Supermoon/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep35_Supermoon/METADATA.md`
- Topik dipilih analisis ulang Sep 2026: 2 event langit besar (supermoon 24 Nov & 24 Des -
  purnama terdekat sejak 2019) + miskonsepsi moon illusion
- **Episode pertama MESIN v9 (kartu kaca/orbit/graf/kinesis/gelombang/flow/flip + trans whip)
  dan TANPA KARAKTER** (semua karakter dihapus dari mesin, diganti papan kaca v9)

## Ep34 - Kenapa Mimisan?
- Video: rilis terbaru - aset `KlikTahu_Ep34_Mimisan.mp4` - 1080x1920 - 60 fps (138,6 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep34_Mimisan/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep34_Mimisan/METADATA.md`
- Topik dipilih analisis: mimisan & hidung 315,8 - satu-satunya kelas berat yang NAIK
- Patch permanen: ekor hening min 0,15 s per klip VO (`process_audio.py` apad)

---

## Ep33 - Kenapa Hujan Bisa Turun?
- Video: rilis terbaru - aset `KlikTahu_Ep33_HujanAwan.mp4` - 1080x1920 - 60 fps (139,8 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep33_HujanBisaTurun/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep33_HujanBisaTurun/METADATA.md`
- Episode pertama dengan **MESIN v8 ELEMEN PEMAHAMAN** (kisi/ukur/skala/detail/slider/hitung/tangga/sorot)

---

## Ep32 - Kenapa Demam Naik Malam?
- Video: rilis terbaru - aset `KlikTahu_Ep32_DemamImun.mp4` - 1080x1920 - 60 fps (123,3 s)
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep32_DemamNaikMalam/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep32_DemamNaikMalam/METADATA.md`
- Topik dipilih otomatis analisis v4.2 `skor_views` (demam & imun 434,8 - #1 SEGAR, bebas blokir)

---

## Ep31 - Kenapa Mata Kedutan?
- Video: rilis terbaru - aset `KlikTahu_Ep31_MataKedutan.mp4` - 1080x1920 - 60 fps
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep31_MataKedutan/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep31_MataKedutan/METADATA.md`

---

## Ep30 - Kenapa Mulut Bau Padahal Rajin Sikat Gigi?
- Video: rilis terbaru - aset `KlikTahu_Ep30_BauMulut.mp4` - 1080x1920 - 60 fps
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep30_BauMulut/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep30_BauMulut/METADATA.md`

---

## Ep29 - Kenapa Kaki Sering Kesemutan dan Kram?
- Video: rilis terbaru - aset `KlikTahu_Ep29_KramKesemutan.mp4` - 1080x1920 - 60 fps
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep29_KramKesemutan/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep29_KramKesemutan/METADATA.md`

---

## Ep28 - Kenapa Perut Bunyi?
- Video: rilis terbaru - aset `KlikTahu_Ep28_KenapaPerutBunyi.mp4` - 1080x1920 - 60 fps
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep28_KenapaPerutBunyi/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep28_KenapaPerutBunyi/METADATA.md`
- Isi: borborygmus (peristaltik otot polos), mode sapu bersih saat lapar (MMC), sumber gas, pemicu, mitos, cara meredakan, tanda bahaya
- Topik dipilih dari sapuan mendalam real-time 1.854 frasa: klaster "perut bunyi" terkuat di antara tema SEGAR

---

## Ep27 - Kenapa Orang Ngorok?
- Video: rilis terbaru - aset `KlikTahu_Ep27_KenapaOrangNgorok.mp4` - 1080x1920 - 60 fps
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep27_KenapaOrangNgorok/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep27_KenapaOrangNgorok/METADATA.md`
- Isi: dengkuran = getaran jaringan lunak saat jalan napas menyempit, pemicu utama, kapan bahaya (apnea tidur obstruktif), cara meredakan, tanda harus ke dokter

---

## Ep26 - Kenapa Dinosaurus Punah?
- Video: rilis terbaru - aset `KlikTahu_Ep26_KenapaDinosaurusPunah.mp4` - 1080x1920 - 60 fps
- Teks siap tempel (judul, deskripsi, tag): `pustaka/Ep26_KenapaDinosaurusPunah/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep26_KenapaDinosaurusPunah/METADATA.md`
- Isi: asteroid 10-15 km, debu menahan matahari sekitar 15 tahun, 75 persen spesies punah, burung = dinosaurus yang masih hidup

---

## Ep25 - Kenapa Mimpi Cepat Lupa Saat Bangun?
- Video: rilis terbaru - aset `KlikTahu_Ep25_KenapaMimpiCepatLupa.mp4` - 1080x1920 - 60 fps
- Teks siap tempel: `pustaka/Ep25_KenapaMimpiCepatLupa/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep25_KenapaMimpiCepatLupa/METADATA.md`

---

## Ep24 - Kenapa Bulan Berwarna Merah?
- Video: rilis terbaru - aset `KlikTahu_Ep24_KenapaBulanBerwarnaMerah.mp4` - 1080x1920 - 60 fps
- Teks siap tempel: `pustaka/Ep24_KenapaBulanBerwarnaMerah/SIAP_TEMPEL.md`
- Metadata lengkap: `pustaka/Ep24_KenapaBulanBerwarnaMerah/METADATA.md`

---

_Dikelola otomatis oleh agen KlikTahu. Setiap episode baru menambah satu bagian di atas._


---

_Analisis kata kunci terbaru (977 frasa, 16 awalan + 26 topik): `analisis/HASIL_ANALISIS_TERBARU.md`._
