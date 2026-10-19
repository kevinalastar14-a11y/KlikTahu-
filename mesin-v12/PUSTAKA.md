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

## Ep50 - Hujan Meteor Orionid 21-22 Oktober: Jam Berapa & Arah Mana (Tanpa Teleskop)
- Video: `KlikTahu_Ep50_Orionid.mp4` - 1080x1920 - 60 fps (116.8 s) - diserahkan via Google Drive
  `KlikTahu_Produksi/Shorts/kliktahu-ep50-orionid-2026/` (mp4 + thumbnail.jpg + audio master .m4a + SIAP_TEMPEL.md)
- Teks siap tempel (judul, deskripsi, hashtag, tag, struktur 5 babak, catatan unggah): `pustaka/Ep50_Orionid/SIAP_TEMPEL.md`
- Metadata ringkas: `episodes/ep50_orionid/METADATA.md`; naskah + cue visual: `episodes/ep50_orionid/content.json`
- Orisinal: episode pertama **mesin v12 KONTINUITAS** (`mesin_v12.py` + `mesin_v12_ep50.py`): satu sistem visual
  (cakram langit + cakrawala + chip tanggal) dari frame 0 sampai akhir, transisi morph (kalender -> jam -> kompas,
  langit -> peta orbit -> langit), 70 SFX dikunci ke kata (faster-whisper), ambient angin malam, loop frame akhir = frame 0.
- Jadwal terbit: Senin 19 Okt 2026 18.30-20.30 WIB (puncak Orionid malam Rabu 21 -> Kamis 22 Okt).

## Ep51 (antre) - Ular Masuk Rumah Saat Musim Hujan? Bukan Karena Banjir
- VO 8 klip sudah jadi (`episodes/ep51_ular_rumah/audio_raw/`), naskah `content.json`, teks `pustaka/Ep51_Ular_Rumah/SIAP_TEMPEL.md`.
- Belum dirender; butuh `mesin_v12_ep51.py`. Target terbit 24-26 Okt 2026.

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
