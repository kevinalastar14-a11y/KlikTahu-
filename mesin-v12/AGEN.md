# AGEN.md — WAJIB DIBACA DULU oleh AI/agen baru

> **Kalau chat lama error/tidak bisa dibuka:** mulai chat baru, lalu suruh agen membaca file ini.
> File ini = memori jangka panjang project. Perbarui setiap kali ada perubahan besar.

---

## 1. Apa ini
Repo **kliktahu-shorts** = mesin produksi channel YouTube **KlikTahu** (Shorts edukasi sains & misteri
bahasa Indonesia, format 1080x1920 - 60 fps). Semua dikerjakan agen (AI) end-to-end: riset topik dari data
pencarian real-time -> naskah -> diagram animasi -> voice over TTS -> render paralel di GitHub Actions ->
rilis otomatis -> pustaka teks siap-tempel.

- **Repo GitHub:** `chronoidchannel-stack/KlikTahu-`. Jangan sentuh repo lain milik pemilik.
- **Branch kerja:** `main` (repo baru 6 Okt 2026; di repo/akun lama namanya `arena/01a0cc99-kliktahu-shorts`).
- **GitHub hanya menyimpan kode + uji ringan.** Render video TIDAK di Actions — jalankan lokal lewat
  `tools/render_lokal.sh`. Baca §14 (aturan keamanan akun) sebelum mengubah apa pun soal workflow.
- **Hasil video diserahkan langsung** ke pemilik sebagai berkas MP4 (folder `dist/`), bukan lewat Release.

## 2. Status terkini (perbarui baris ini setiap selesai episode)

> **MULAI DARI SINI:** keadaan terbaru proyek ada di **§15 (15 Okt 2026 — data kanal nyata, standar produksi v12,
> keputusan Ep50)** dan **§14 (6 Okt 2026 — pindah akun & repo, render tidak lagi di GitHub Actions)**.
> Catatan rilis Ep24-Ep49 di bawah tetap berlaku sebagai riwayat isi episode.

### ATURAN KERAS (pelajaran 22 Sep, user marah)
1. **1 episode = 1 render = 1 rilis.** SEMUA aset (naskah, VO, visual, METADATA.md, pustaka)
   WAJIB lengkap di push PERTAMA yang memicu render. DILARANG commit "METADATA.md" belakangan
   hanya demi memperbarui aset rilis - itu me-render ulang seluruh video (terlanjur 4x boros).
2. **METADATA.md setiap episode WAJIB memuat 4 blok sejak awal:** Judul (3 pilihan),
   Deskripsi (blok penuh siap salin), **Hashtag** (terpisah), **Tag**. Template ada di
   `pustaka/Ep37_Jerawat/SIAP_TEMPEL.md` + `episodes/ep37_jerawat/METADATA.md`.
3. Kalau metadata perlu diperbarui SETELAH rilis: push akan memicu
   `.github/workflows/metadata.yml` (paths: episodes/*/METADATA.md, pustaka/**) yang HANYA
   menimpa aset METADATA.md di rilis terbarus tiap episode (--clobber, TANPA render).
4. Rencana (bungkus dengan push pertama episode berikutnya, jangan sendiri): tambah negasi
   path `!episodes/<slug>/METADATA.md` di render.yml agar perubahan metadata saja tidak
   pernah memicu render.

- **PERHATIAN NOMOR EPISODE (23 Sep):** ada DUA "Ep42" dari dua sesi paralel:
  `KlikTahu_Ep42_Listrik-66` (branch lama 01a0bf42, listrik & magnet, 177,3 s) dan
  `KlikTahu_Ep42_Sinyal-67` (branch 01a0cc99, internet & sinyal, 158,0 s, Latest). Episode berikutnya = **Ep43**.
  Branch lama juga punya ATEMPO_EXTRA di process_audio.py (commit c496e19) - belum digabung ke 01a0cc99.
- **[24 Sep, sesi 01a0cc99] AUDIO v5 - PERBAIKAN "SUARA TERPOTONG"** (keluhan user di Ep45). Penyebab: `redam_napas()`
  (Audio v4, 20 Sep, dibuat utk suara TTS lama yg bernapas) ambang -28 dB meredam -40 dB ujung kata & konsonan pelan:
  20-47 potongan per klip, ~13,7 s isi suara teredam di Ep45. Kena SEMUA episode Ep28-Ep46. Perbaikan: `REDAM_NAPAS=0`
  bawaan (voice-00 tidak punya napas), `potong_napas` aman (-48 dB, pad 80/250 ms), QC baru "isi hilang" (bandingkan
  hasil vs referensi sebelum potong; >30 ms isi bersuara teredam = GAGAL, exit 3). Ep45 (rilis -72) & Ep46 dirender ulang (rilis baru
  Ep45_Langit, durasi 147,2 s, bab sama). JANGAN nyalakan lagi REDAM_NAPAS; jangan tambah gate/expander pada VO.
  render.yml sementara menunjuk ep46_megalodon (bab Ep46 geser: 0:26, 1:33; durasi 144,0 s) -> saat Ep47 siap: sed ep46_megalodon -> ep47_petir.
- **[24 Sep, sesi 01a0cc99] Ep49 BINTANG** - "Kenapa Bintang Berkedip, Tapi Planet Tidak?" (v6 LIVE #1 bintang & galaksi
  48,2; sudut pembeda planet = piringan; momen Saturnus oposisi 4 Okt 2026). 158,8 s, 9 VO voice-00 (audio v5, 0 ms
  hilang), episode PERTAMA mesin FX 2026. `mesin_v11_ep49.py`: `_langit49` panel gradasi + `_klip` (area simpan
  diperluas 170 px -> isi yang meluber ikut terpotong sudut membulat; gambar teks di luar panel SESUDAH `_klip`),
  `kedip()` kecerahan bintang, `_bintang49`, `_jupiter49`, `_saturnus49` (cincin depan/belakang), `_bumi49`,
  `_lintasan` (berkas dibelokkan kantong udara), `_grafik`. SFX baru `laser`, `angin` (24 bunyi). Transisi eksplisit
  zoomthru/tinta/cahaya. check_layout bersih, sapuan 80 frame OK. Rilis `KlikTahu_Ep49_Bintang-76` (run 36022773282, Latest, mp4 133 MB).
  Berikut (kalender v6): piramida, lubang hitam, ular, aurora, es & salju.
- **[24 Sep, sesi 01a0cc99] VIDEO PANJANG 16:9 - Long02 LAUT DALAM** ("Perjalanan ke Dasar Laut Terdalam di Bumi",
  permintaan user "Video panjang kedua!", aturan sama dengan Long01). 612,4 s (10:12), 10 bab, 10 VO voice-00
  (SPEED 1.09, `export ATEMPO_MIN=0.85` di config.env karena naskah padat angka -> tanpa itu atempo dijepit ke 0,88
  dan b07 kena peringatan tempo; override SPEED_<ID> saja TIDAK cukup). Rilis `KlikTahu_Long02_LautDalam-<run>`.
  - `visual.py` punya `latar(t, C)` sendiri (render_long.py kini memakai `mod.latar` bila ada, jika tidak `L.latar`)
    + `overlay(img, C)` (HUD kedalaman, digambar tajam SS=1 sebelum hud). Fungsi `dalam()` = kedalaman per adegan
    dikunci ke kata -> latar (gradasi per kedalaman, berkas sinar, salju laut 2 lapis gulir sqrt(kedalaman), kelip
    bioluminesensi, garis kecepatan) & HUD memakai angka yang sama.
  - Pustaka makhluk sprite (supersample 3x, fase kibasan ter-cache): ikan, kawanan, ikan_lentera, ubur, udang,
    pemancing (mulut bisa "hap"), paus_sperma, cumi, ikan_siput, amfipoda, kepiting, cacing_tabung; objek: kapal,
    penyelam, titanic, gelas styrofoam (keriput), cerobong + asap, everest, mobil, jari, trieste, deepsea_challenger,
    kapal_selam (remuk), kantong_plastik, bulan, matahari, termometer, profil_zona, sorot (kerucut lampu).
  - `glow` lokal (numpy, tepi = 0): glow bawaan mesin_v11 punya TEPI KOTAK samar pada radius besar -> di video
    panjang pakai glow versi visual.py. `D.line_on(dash=)` harus int, bukan tuple.
  - render_long.yml: default slug v02_laut_dalam, nama rilis dari OUT_NAME, SIAP_TEMPEL diambil dari
    `pustaka/${OUT_NAME#KlikTahu_}/`.
- **[24 Sep, sesi 01a0cc99] VIDEO PANJANG 16:9 - Long01 LUBANG HITAM** ("Apa yang Terjadi Kalau Kamu Masuk ke
  Lubang Hitam?", permintaan user: orisinal, topik dipilih agen, durasi bebas, gaya sama Shorts = tanpa subtitle,
  SFX saja tanpa musik). 557,3 s (9:17), 10 bab, rilis `KlikTahu_Long01_LubangHitam-1` (run 35949992540, 16 potongan ~8 menit), 10 VO voice-00 (SPEED 1.09). Sistem terpisah dari Shorts:
  - `long/mesin_long.py` = mesin 16:9 (1920x1080, SS 1.25, 30 fps): `align()` = penyelarasan kata DP (jeda audio <->
    tanda baca) -> `Ctx.w("kata", n, off)` memberi waktu kata ke-n dalam adegan (KeyError kalau kata tidak ada);
    komponen: lubang_hitam (piringan Doppler + lensa + cincin foton), bintang, bumi, astronot (regang/merah), jam,
    galaksi, parabola, roket, callout/chip/stiker/stempel/angka/kaca, kartu_bab, hud, kamera, transisi.
  - `long/render_long.py --slug <folder> [--align|--check|--sheet t,..|--range LO:HI --out x.mp4]`.
  - `long/<slug>/visual.py` = VIS (fungsi per adegan) + BEATS (SFX dikunci ke kata) ; `long/audio_long.py` =
    master VO + lapisan SFX (duck, limiter puncak saja, QC "VO tidak turun").
  - `long/<slug>/thumbnail.py` -> thumbnail.jpg 1280x720 ikut rilis.
  - Workflow `.github/workflows/render_long.yml` (push `long/**` kecuali METADATA.md): prep (pipeline audio root
    TANPA mengubah skrip root) -> 16 potongan paralel -> merge + QC wajib -> rilis `KlikTahu_Long01_LubangHitam-<run>`.
  - Video panjang berikutnya: salin folder `long/v01_lubang_hitam` -> `long/v02_<topik>`, ganti VIS/BEATS, ubah
    default slug di render_long.yml. Glyph Poppins TIDAK punya centang/bintang/superskrip -> gambar sebagai bentuk.
- **[SELESAI 24 Sep, sesi 01a0cc99] Ep48 JANTUNG** - "Kenapa Jantung Tiba-tiba Berdebar Kencang?" (v6 LIVE #1
  jantung & dada 45,8; frasa `kenapa jantung berdebar kencang tiba-tiba`). 153,6 s, 10 VO voice-00 (audio v5, 0 ms
  hilang), `mesin_v11_ep48.py` (9 adegan; helper `_jantung48`, `_ekg48` + `_fase`/`_denyut` = EKG & denyut sinkron,
  bpm naik/turun mulus), SFX baru `detak` (22 bunyi). Topik kesehatan: sumber NHS/Cleveland/BHF/AHA/U-M, kalimat
  "bukan pengganti dokter". Rilis `KlikTahu_Ep48_Jantung-75`. Berikut (papan 24 Sep): lubang hitam, ular, aurora,
  uban, piramida, cegukan.
- **[SELESAI 24 Sep, sesi 01a0cc99] Ep47 PETIR** - "Kenapa Petir Sering Menyambar Pohon?" (v6 LIVE #1 petir 42,6;
  frasa asli `kenapa petir sering menyambar pohon`). 139,2 s, 10 VO voice-00 (f4/f5 direkam belakangan), audio v5
  (0 ms isi hilang semua klip), `mesin_v11_ep47.py` (fraksi B47 dari caption), SFX `guntur`, check_layout bersih,
  qc_mp4 audio OK. METADATA + SIAP_TEMPEL + PUSTAKA + mesin_v5 "Ep47": "petir" dalam SATU push -> rilis
  `KlikTahu_Ep47_Petir-74`. Kalender berikut: uban, pelangi, jantung, es, cegukan, kapal.
  Sumber: NOAA NESDIS (30.000 C, 5x permukaan matahari; muatan naik ke benda tinggi), NSSL/NWS (pemandu bertahap,
  percikan penyambut, loncatan samping), UMD Extension (getah mendidih -> kulit kayu meledak), Guinness/IPB (Bogor
  322 hari petir), NWS (Empire State ~20-25 sambaran/tahun).
- **[TUNTAS 23 Sep, sesi 01a0cc99] Ep46 MEGALODON** - rilis `KlikTahu_Ep46_Megalodon-71` (run 35892371225,
  Latest, mp4 + content.json + METADATA.md), 143.5 s.
  Sudut: "Megalodon Masih Hidup? Giginya yang Menjawab" (v6 LIVE #1 megalodon 44,9; pesaing hanya bertanya).
  Modul `mesin_v11_ep46.py` (gigi bergerigi + penggaris + telapak tangan + pisau roti, siluet hiu mengibas,
  skala manusia/hiu putih/16 m/24 m, sabuk gigi berganti & gigi jatuh menumpuk, kolom batuan 0-23 juta th,
  termometer 27 C + laut dalam, paus pindah, TV + stempel FIKSI + pie 73%). SFX baru `gelembung`, `gigit` (20 bunyi).
  QC lokal: VO 10/10 BERSIH, check_layout bersih, audio master OK, qc_mp4 uji korelasi 1,0000.
  CATATAN: sandbox bisa ter-reset ke commit dasar di antara giliran -> file yang belum di-commit HILANG.
  Setelah reset: `git fetch origin main && git reset --hard FETCH_HEAD` + pip install -r requirements.txt.
  Episode berikutnya = **Ep49** (Ep48 jantung selesai). Papan v6 LIVE setelah Ep46: #1 petir 42,6,
  #2 uban & rambut 42,3, #3 jantung & dada 42,1, #4 pelangi 41,2, #5 cegukan 39,3.
- **[TUNTAS 23 Sep, sesi 01a0cc99] Ep45 LANGIT GELAP (matahari)** - rilis `KlikTahu_Ep45_Langit-70` (run 35832816444,
  Latest, mp4 121 MB + content.json + METADATA.md), 147.1 s
  (v6 LIVE #1 matahari 47,8; sudut PADAHAL "kenapa luar angkasa gelap padahal ada matahari" = judul).
  Modul `mesin_v11_ep45.py` (panel angkasa berbintang, senter + debu, molekul penyebar biru, kolom ketinggian
  biru->hitam + balon, matahari kuning vs putih + spektrum, garis pandang Olbers, cakrawala 13,8 M th,
  gelombang teregang, peta sisa cahaya awal). SFX baru `kilau` (18 bunyi).
  QC lokal: VO 10/10 BERSIH, check_layout bersih, qc_mp4 uji korelasi 1,0000, SFX -28 dB vs VO.
  Episode berikutnya = **Ep46** (modul `mesin_v11_ep46.py`, impor di mesin_v11 dengan pola yang sama).
- **[TUNTAS 23 Sep, sesi 01a0cc99] Ep44 GUNUNG PADANG** - rilis `KlikTahu_Ep44_Padang-69` (run 35830969396, Latest,
  mp4 130 MB + content.json + METADATA.md), 156,1 s
  (v6 LIVE #1 situs misteri indonesia 46,9; pilar MISTERI). Sudut DETEKTIF BUKTI: kekar kolom alami vs susunan
  leluhur vs umur dari bukti (retraksi 2024, arang ~2.000 th, tim 2025 ~6.000 SM "masih diteliti") - netral,
  menghormati leluhur. Modul `mesin_v11_ep44.py` (bukit berteras, prisma, retak heksagonal, dinding susun,
  batu kecapi, kartu jurnal + stempel DICABUT, penampang lapisan). SFX baru `retak` & `kecapi` (17 bunyi).
  QC lokal: VO 10/10 BERSIH, check_layout bersih, qc_mp4 uji korelasi 0,9999, SFX -26,8 dB vs VO.
  Episode berikutnya = **Ep45** (modul `mesin_v11_ep45.py`, impor di mesin_v11 dengan pola yang sama).
- **[TUNTAS 23 Sep, sesi 01a0cc99] Ep43 KUPING BERDENGING** - rilis `KlikTahu_Ep43_Kuping-68` (run 35826662293, Latest,
  mp4 126 MB + content.json + METADATA.md), 153,4 s
  (v6 LIVE #1 kuping 45,1; sudut PRIBADI "kenapa kuping berdenging tiba tiba/terus"). Adegan di modul BARU
  **`mesin_v11_ep43.py`** (pola per episode: `mesin_v11_epNN.py` berisi fungsi adegan + `B43` beat bernama
  `{nama: (fraksi, sfx)}` + `_t()`; mesin_v11 mengimpornya HANYA bila `__name__ != "__main__"` - hindari
  impor melingkar; `__main__` mengimpor ulang diri sebagai modul lalu `_selftest`). SFX baru `nging` (6,2 kHz).
  QC lokal: VO 10/10 BERSIH, check_layout bersih, qc_mp4 uji korelasi 1,0000, SFX -27 dB vs VO.
  Episode berikutnya = **Ep44** (buat modul `mesin_v11_ep44.py`, impor di mesin_v11 dengan pola yang sama).
  Kalender v6 berikutnya: megalodon, situs misteri indonesia, ular & reptil, cegukan, matahari, jantung.
- **[TUNTAS 23 Sep, sesi 01a0cc99] Ep42 INTERNET & SINYAL** - rilis `KlikTahu_Ep42_Sinyal-67` (run 35824486263,
  157,98 s, Latest; aset mp4 132 MB + content.json + METADATA.md). (v6 LIVE #1 skor 49,2) - episode PERTAMA
  mesin v11 "EDITOR" + SFX. Push pertama berisi semua aset (naskah, VO 10 klip voice-00, METADATA 4 blok,
  pustaka, render.yml ep42_sinyal). QC lokal: VO 10/10 BERSIH, timeline 158,0 s, check_layout bersih,
  qc_mp4 uji (video dummy + audio_master) korelasi 1,0000 + VO per adegan OK. Setelah render: cek run
  `gh run list`, pastikan rilis KlikTahu_Ep42_Sinyal Latest, lalu ubah baris ini jadi TUNTAS.
  Kalender v6 berikutnya: cegukan, megalodon, jantung & dada, kuping, anjing (listrik & magnet SUDAH).

- **[SELESAI] Ep41 HANTU & SUPRANATURAL** (SEGAR #1 84,1 + momen Halloween 31 Okt): mesin 9 adegan
  SUDAH di diagrams.py (selftest41 OK, qa ronde-1 9/9 penuh; label "wasir" sudah dibetulkan "waspada");
  analisis: SUDAH_EP +Ep40, KALENDER +Halloween, bobot sains hantu 2.0. content.json = NASKAH FINAL
  take-2 (~260 kata, semua kalimat mengalir). PELAJARAN KERAS: JANGAN memotong-potong audio WAV untuk
  memangkas naskah (multi-round trim merusak raw asli - audio_raw tertimpa sebelum commit, build/audio.wav
  terkontaminasi) -> VO WAJIB REKAM ULANG TAKE-2 penuh 10 klip (voice-00) dari vo content.json, lalu
  process SPEED=1.09 TARGET_WPS=1.90 -> timeline MAXDUR=178 (target total ~143 s) -> audit -> probe ->
  METADATA 4 blok + SIAP_TEMPEL -> render.yml ep41_hantu (JANGAN patch render.yml sebelum episode+audio
  lengkap, push memicu render) -> 1 commit+push. Sumber fakta sudah tervalidasi: sleep paralysis REM
  atonia 7,6% (PSU 2011), pareidolia (kumparan), infrasonik 19 Hz Vic Tandy 1998 + Frontiers 2026
  (kortisol naik), sugesti (kumparan).

- **Rilis terbaru: Ep41 "Itu Bukan Hantu, Itu Otakmu" TUNTAS** (run 64, 143,04 s, Latest; aset mp4+content.json+METADATA.md) - 23 Sep 2026. Topik #1 SEGAR
  (84,1 + momen Halloween 31 Okt). VO voice-00 take-2 10/10 BERSIH 133,8 s. QA: layout normal+ketat
  bersih (5 teks dipangkas), probe 10 titik ink worst 974. Sumber: Frontiers 2026 (kortisol naik saat
  infrasonik 17-19 Hz), Vic Tandy 1998, PSU 2011 (7,6%), CNN/Halodoc/IDN Times.
- **Sebelumnya: Ep40 "Gerhana Bukan Pertanda Kiamat" TUNTAS** (run 62, 158,53 s, Latest; aset mp4+content.json+METADATA.md) - 23 Sep 2026. Topik #1 SEGAR (gerhana,
  CI 214,4). Mesin Ep40 (9 adegan) sudah ada di diagrams.py; VO voice-00 take-1 langsung 10/10 BERSIH
  (naskah mengalir 260 kata; TARGET_WPS=1,90). Layout normal+ketat bersih; ink worst 1466.
- **Sebelumnya: Ep39 "Bintang Jatuh Itu Bukan Bintang" (Meteor & Komet) TUNTAS (run 61, 154,86 s)** (run 61, 154,86 s, Latest; aset mp4+content.json+METADATA.md) - 23 Sep 2026.
  **[ATURAN BARU USER: DURASI BEBAS - jangan dibatasi 140 s!]** -> config.env MAXDUR=178 (aman status Shorts <=180 s);
  pace santai TARGET_WPS=1.90 di config.env (render.yml mengekspor, default 1.95). VO take-4 = final:
  naskah 256 kata kalimat mengalir (bukan patah-patah), 10/10 BERSIH 145,7 s @1,70-1,79 kata/s;
  **f7 chronic-fast** (TTS selalu buru-buru di naskah itu) -> perlambat PRA-REKAM `atempo=0.82` single-pass
  (bukan jeda sisip - take-2/3 masih kelihatan patah). Kata rawan TTS hindari: terimpres, keoranyean, "Orionids"(s).
  Timeline 154,9 s; layout normal+ketat bersih; ink worst 474.
  **[SIAP] Ep40 GERHANA #1 SEGAR** (lokal 82,0 / CI penuh ~214): blok mesin 9 adegan MASUK diagrams.py
  (_sun40/_earth40/_moon40/_umbra40 + intro_gerhana/segil40/dua40/bay40/darah40/aman40/jarang40/mitos40/
  rangkuman40b; selftest40 OK; qa ronde-1: bug kartu dua40 y-terbalik SUDAH diperbaiki) - naskah/config belum;
  SUDAH_EP mesin_v5 +Ep39; fakta: bulan darah = sunset dunia; retina bakar tanpa rasa; orbit miring 5 deg;
  Indonesia: cincin 21 Mei 2031, total 20 Apr 2042; mitos pertanda buruk = tidak ada dasar. [RENDER ULANG feedback user: ambien v10 anti-memudar (floor alpha 0.48, warna lebih pekat, bintang tak terlalu redup), fade-out keluar adegan dipangkas 0.36s/70px -> 0.22s/46px (render.py, berlaku semua episode), VO take-3 10/10 + f7 denda jeda alami (teknik sisip silence -> tempo <=2,1 kata/s) - pelajaran: kata rawan TTS = "terimpres/keoranyean/Orionids". Run 58 gagal audit CI (teks borderline 2-14px di atas ambang lokal), run 59 sukses, run 60 = final.] Topik #1 SEGAR
  (meteor & komet 222,4; velocity 20,5 tercepat; momen Orionids 21-22 Okt pas jendela 45 hari).
  **MESIN v10 ANTI-ZONA-KOSONG:** `_ambien10` (bokeh + plus melayang di SEMUA adegan), `_langit39`
  (langit malam bintang berkelip + meteor streak), `_komet39` (komet es-debu); 9 adegan: jalur
  meteoroid-meteor-meteorit, 66 km/dtk + udara diimpres, kode warna unsur Mg/Fe/Ca/Ni (+bolide hijau
  Yogya), Orionids jejak Halley, komet vs asteroid vs meteor, mitos ramalan, panduan nonton.
  QA: selftest + probe 45 frame + probe timeline 10 titik (ink worst 263) + layout BERSIH ronde 3;
  VO voice-00 take-2 10/10 (126,6 s; pelajaran: voice-00 ~1,8 kata/s -> naskah 215 kata).
- **Sebelumnya: Ep38 "Kenapa Baterai Cepat Habis Padahal Nggak Dipakai?" TUNTAS** (run 57, 139,8 s, Latest) -
  22 Sep 2026. Topik #1 SEGAR (baterai & hp 315,2->326,6, velocity +14,4/+14,9 tercepat; ganti topik dari
  mata karena kedutan = Ep31). MESIN: `_hp38` (HP + indikator, uap panas, charger, persen lompat) +
  `_sel38` (sel Li-ion); mitos cas semalaman + slider zona 20-80%; VO voice-03 take-1 10/10 bersih.
  Aset rilis: mp4 + METADATA.md + content.json (metadata.yml ikut menyinkronkan).
- **Rilis sebelumnya: Ep37 "Kenapa Jerawat Muncul?" TUNTAS** (run 54/55/56, 119,4 s) -
  22 Sep 2026. Topik #2 antrean SEGAR (kulit ~296). MESIN v9: helper `_kulit37` (tekstur pori
  bernapas) + `_folikel37` (folikel 4-keadaan: sebum/sumbat/merah) dipakai lintas adegan;
  intro kaca pembesar; segitiga zona hidung-bibir; 2 baris mitos + stamp. VO take-1 10/10
  bersih (111,0 s), total 119,4 s (sisa 20,6 dari 140). QA menangkap 5 hal: 2 detail
  menabrak kartu, typo "CUTIBACTACTERIUM", label tertimpa ring denyut, teks kartu menembus
  margin kanan 4px (font 24->22). Bab: 0:00 intro - 0:13 f1 - 0:25 f2 - 0:37 f3 - 0:49 f4 -
  1:03 f5 - 1:16 f6 - 1:30 f7 - 1:43 f8 - 1:56 outro. Fakta: 4 langkah pori (androgen,
  sumbat, C. acnes, peradangan), komedo hitam = oksidasi, 9/10 remaja, gula bukan cokelat,
  bahaya memencet + zona otak.
- **Ep36 "Kenapa Migrain?"** (run 52/53, 133,7 s) - 22 Sep 2026.
  Topik #1 antrean SEGAR (pusing & migrain 325,6). MESIN v9 penuh. QC: take-1 over 18 s
  (TTS giliran lambat 149,6 s VO) -> naskah dipangkas + re-record 9 klip -> VO 125,3 s
  (aturan SPEED 1,07-1,13 tidak dilanggar); `_skala_on` menghasilkan blob di f5 (angka 3X)
  -> diganti 2 kartu perbandingan v9; probe 10/10 tinta maks 415; layout bersih; 133,7 s
  (sisa 6,3 dari 140). Bab: 0:00 intro - 0:12 f1 - 0:25 f2 - 0:38 f3 - 0:55 f4 - 1:08 f5 -
  1:22 f6 - 1:40 f7 - 1:58 f8 - 2:10 outro. Fakta: CSD->aura, trigeminus->CGRP, wanita 3x,
  risiko 50%, 90% beban disabilitas, >22% beban = kebanyakan obat (GBD 2023).
- **Ep35 "Supermoon 2026 & Ilusi Bulan Raksasa"** (run 50/51, 139,6 s) - 22 Sep 2026. Topik: analisis ulang Sep 2026 memilih event langit (supermoon 24 Nov
  & 24 Des - purnama terdekat sejak 2019, +-356.700 km) + moon illusion.
  **KARAKTER DIHAPUS TOTAL dari mesin** (def _tokoh/_tokoh7 + 16 titik panggil; pengganti:
  papan kaca v9). **MESIN v9 "GERAK & KACA"**: kartu kaca+bayang, papan, orbit elips,
  graf Catmull-Rom, tipografi kinetis, gelombang, panah flow, flip; transisi baru "whip".
  QC: VO 9/9 take-1, tinta maks 295, layout bersih, master 0 clipping, 139,6 s.
  Bab: 0:00 intro - 0:21 f1 - 0:39 f2 - 0:54 f3 - 1:15 f4 - 1:33 f5 - 1:44 f6 - 2:00 f7 -
  2:16 outro. Insiden run 49: config kurang MAXRATE/BUFSIZE + `set -u` -> semua chunk gagal;
  config dilengkapi (JANGAN hapus field encode dari config.env).
- **Ep34 "Kenapa Mimisan?"** (`KlikTahu_Ep34_Mimisan-48`, 138,6 s) - 21 Sep 2026.
  Topik: mimisan & hidung 315,8 - satu-satunya kelas berat yang NAIK. Episode kedua dengan
  **MESIN v8** penuh. QC: VO 10/10 bersih take-1 (SPEED 1,08-1,13), tinta render_frame maks 895
  (f4 didesain ulang: ukur+label menumpuk -> tangga + pil berurutan), layout bersih 10/10,
  master 0 clipping, timeline 138,6 s (sisa 1,4 dari MAXDUR 140).
  Bab: 0:00 intro - 0:11 f1 - 0:30 f2 - 0:47 f3 - 1:01 f4 - 1:18 f5 - 1:31 f6 - 1:46 f7 -
  2:03 f8 - 2:15 outro.
  Patch permanen baru: `process_audio.py` memberi ekor hening min 0,15 s per klip (apad) -
  akar QC "ekor terpotong" intro/outro di build_audio (run 46 gagal karena CI menjalankan
  build_audio di prep; klip pendek ber-ekor 0,02-0,04 s < ambang 0,045).
- **Ep33 "Kenapa Hujan Bisa Turun?"** (`KlikTahu_Ep33_HujanAwan-45`, run 45, 139,8 s) - 21 Sep 2026.
  Topik #2 SEGAR berpotensi views (hujan & awan 420,4). Episode pertama **MESIN v8 ELEMEN PEMAHAMAN**.
  QC: VO 10/10 bersih (take-2/3; f4 take-3 karena napas ekor keras), knob episode lead_in 0,3 +
  tail_fact 0,8, build_audio AUDIO OK 10/10 (jeda 0,56-0,63 s), layout bersih, QC video CI lolos.
  Bab: 0:00 intro - 0:11 f1 - 0:27 f2 - 0:43 f3 - 0:59 f4 - 1:13 f5 - 1:29 f6 - 1:44 f7 - 2:00 f8 - 2:17 outro.
  Pelajaran QC (permanen): (1) qc_mp4 kini cari LAG +-100 ms sebelum korelasi (alimiter master punya
  latensi ~5 ms); (2) elemen yang menggelapkan seluruh layar TERLARANG - kamera+ambient memangkas
  ~55px tepi sehingga margin krem hilang -> tinta QC meledak; `_sorot_on` kini CINCIN gelap sekitar
  target (tervalidasi render_frame asli 10/10, tinta maks 1.322); (3) `_langit7` awan & `_confetti_on`
  dikunci di dalam area aman.
- Episode selesai: Ep24 Bulan Merah, Ep25 Lupa Mimpi, Ep26 Dinosaurus Punah, Ep27 Ngorok, Ep28 Perut Bunyi,
  Ep29 Kram & Kesemutan, Ep30 Bau Mulut, Ep31 Mata Kedutan, Ep32 Demam Naik Malam, Ep33 Hujan Bisa Turun, Ep34 Mimisan,
  Ep35 Supermoon, Ep36 Migrain, Ep37 Jerawat, Ep38 Baterai, Ep39 Meteor & Komet, Ep40 Gerhana, Ep41 Hantu.
- **Episode aktif di pemicu render:** `ep40_gerhana` (fallback `inputs.episode` di `.github/workflows/render.yml`
  dan paths push + negasi `!episodes/*/METADATA.md` & `!pustaka/**` sudah TERPASANG).
- Mesin visual **v3 + animasi v4** (21 Sep): kamera 2 fase + napas, transisi variatif, streak + kilat, PLUS
  paket gerak v4 di diagrams.py (`_pop_pill`, `_pop_txt`, `_shine_on`, `_meter_on`, `_bar_on`, `_ripple_on`,
  `_swarm_on`, `_tile_rot`) — PAKAI di semua episode baru supaya gerak makin kaya (permintaan user:
  "animasi bergerak yang populer di YouTube").
- **MESIN v5 - PAKET PENJELAS (21 Sep, permintaan user "lebih banyak animasi & elemen yang membantu
  membayangkan"):** di diagrams.py ekor: (1) 16 IKON GENERIK `_ico5` (heart, brain, lung, stomach,
  tooth, eye, bone, germ, clock, thermo, flame, snow, drop, bolt, moon, shield — semuanya bergerak:
  jantung berdenyut, paru mengembang, bakteri berputar, termometer naik-turun, dll.); (2) 10 ELEMEN
  PENJELAS: `_loupe_on` kaca pembesar (zoom area frame), `_callout_on` anotasi menunjuk, `_flow_on`
  alur proses ikon+panah, `_versus_on` perbandingan VS, `_spotlight_on` sorot gelap-terang, `_fan_on`
  kipas arah penyebaran, `_timeline_on` garis waktu, `_tanya_on` balon pertanyaan, `_check5_on`
  centang/silang besar progresif, `_burst_on` sinar penekanan. SELFTEST: `python3 diagrams.py` =
  selftest Ep30+Ep31+v5 (16 ikon + 10 elemen) — WAJIB lolos sebelum render. SEMUA WAJIB dipakai di
  episode baru (gabungkan dengan paket v4). Catatan bug: `_loupe_on` TIDAK BOLEH komposit full-frame
  (pernah menimpa frame) - hanya lensa yang dipaste.
- **MESIN v6 - KARAKTER & SINEMA (21 Sep, permintaan "upgrade lebih-lebih, mutakhir"):**
  (a) diagrams.py: `_tokoh` karakter kartun ekspresif 7 emosi (netral/happy/kaget/sedih/mikir/
  pusing/ngantuk; napas-kedip-pandang otomatis; talk=mulut bicara; gestur=tangan melambai; flip) +
  `_pikir_on` balon pikir + `_karaoke_on` caption KARAOKE kata-per-kata (kata aktif dapat pil
  warna - standar caption Shorts; pakai di hook) + `_stamp_on` stempel kata BAM + `_donut_on`
  donut persen + `_eq_on` bar equalizer hidup + `_punch_on` punch-kamera beat + `_confetti_on`
  hujan confetti. (b) render.py: 4 TRANSISI BARU `speed` (pita kecepatan variabel), `glint`
  (kilat menyapu), `split` (panel bertemu), `thud` (guncang+blur, untuk beat dramatis) + mode
  `ambient` (crossfade panjang halus) + KT_AMBIENT=1 default: seluruh frame bernapas drift
  pelan (tidak pernah beku). Semua selftest: `python3 diagrams.py` (Ep30/31/v5/v6). PAKAI di
  semua episode baru: tokoh sebagai pemandu, karaoke di hook, transisi variatif, beat dengan
  stamp/punch/confetti, data dengan donut/eq.
- **MESIN v7 - IMAJINASI (21 Sep, "penonton membayangkan lebih jelas"):**
  (a) diagrams.py: `_tokoh7` tokoh BERKAKI + mode jalan (badan naik-turun mengikuti langkah;
  bungkus `_tokoh` v6) + `_scribble_on` anotasi gaya TANGAN yang menggambar progresif di depan
  penonton (circle=lingkari objek, underline, arrow panah melengkung) + `_cutaway_on` kontainer
  tembus pandang "masuk ke dalam" (isian cair permukaan gelombang + gelembung naik) +
  `_flowpath_on` partikel mengalir di jalur pipa (udara->paru, makanan->usus) + `_langit7`
  latar suasana waktu (pagi/siang/sore/malam: gradasi + matahari/bulan + bintang + awan drift) +
  `_recap_on` papan rangkuman akhir (kartu ikon+poin pop berurutan) + `_lower3_on` label nama
  tokoh lower-third. (b) render.py: TRANSISI `dive` (zoom-through menyelam MASUK ke objek;
  set posisi dengan "dive_at": [x,y] di content.json) + trans "auto" = rotasi otomatis 10
  transisi per adegan (tanpa konfigurasi). Selftest: `python3 diagrams.py` = Ep30/31/v5/v6/v7.
  PAKAI di semua episode baru: tokoh berjalan antar objek, lingkari-panahi detail penting,
  masuk-ke-dalam organ lewat dive, cerita pagi/siang/malam, rangkuman recap di outro.
  (pernah menimpa frame) — hanya lensa yang dipaste.
- **Audio prosesing v4** (20 Sep, tidak berubah): TARGET_WPS 1,95; ATEMPO 0,88-1,10; potong_napas + redam_napas
  (pulau -28 dB, redam -40 dB). Verifikasi napas pakai QC skrip, bukan replikasi manual.
- **MESIN v8 "ELEMEN PEMAHAMAN"** (21 Sep, Ep33): diagram.py `_kisi_on` (kertas grafik), `_ukur_on`
  (garis ukur dua panah + label, menggambar dari tengah), `_skala_on` (perbandingan batang bertumbuh),
  `_detail_on` (kartu judul+sub via garis siku - versi informatif callout), `_slider_on` (gagang
  sebelum/sesudah), `_hitung_on` (angka count-up pemisah ribuan + unit), `_tangga_on` (jalur langkah
  bernomor 1-2-3), `_sorot_on` (gelapkan frame kecuali lingkaran target, tepi blur + cincin denyut).
  Tujuan: penonton LEBIH CEPAT Membayangkan (ukuran/skala/proses/sebelum-sesudah). Selftest v8 wajib OK.
  Pakai minimal 3 elemen v8 per episode baru. Konvensi: teks DI DALAM area sorot = terang; di luar =
  warna gelap; fade sorot mulai 2,4 s sebelum adegan berakhir.
- **Analisis v3** (21 Sep): skor_tumbuh = skor + rel*1,2 + kom*1,5 + vis*0,8 + ever*3 (detail §8).
- **BLOKIR topik (perintah user 21 Sep, FINAL)**: kentut, ngiler, keringat & bau badan (= "kentut dll",
  tabu/memalukan) — JANGAN usulkan lagi; `BLOKIR` di pemeta_peluang.py menyaringnya dari ranking/cabang/laporan.
- **Kandidat Ep32+ = urutan `skor_views` keluarga SEGAR (FINAL run-5 CI 21 Sep, bebas blokir)**:
  demam & imun 434,8 · hujan & awan 420,4 · pusing & migrain 325,6 · mimisan & hidung 315,8 · kulit 295,8 ·
  uban & rambut 280,4 · baterai & hp 264,8 · megalodon 261,4. MOMEN NAIK: perut & pencernaan (445,6,
  tapi Ep28), cegukan, listrik & magnet, batuk flu pilek, kapal & mengapung, langit & senja. Rencana seri
  5 judul per keluarga siap tempel di `analisis/PEMETA_PELUANG.md`.

## 3. Peta file penting
| file/folder | fungsi |
|---|---|
| `episodes/<slug>/content.json` | naskah 9 adegan (intro, f1, f2, f2b, f3, f4, f5, f6, outro) + visual + accent + trans + speed per adegan |
| `episodes/<slug>/config.env` | OUT_NAME, FPS 60, SS 1.5, SHARPEN 52, SPEED 1.10, MAXDUR 140, encode, CHUNKS 12 JOBS 4 |
| `episodes/<slug>/audio_raw/*.wav` | 9 klip VO TTS (nama persis: intro, f1, f2, f2b, f3, f4, f5, f6, outro) |
| `episodes/<slug>/METADATA.md` | analisis + judul/deskripsi/tag + peta adegan + fakta+sumber |
| `render.py` / `diagrams.py` | mesin frame (kamera, transisi, HUD, latar) / diagram per adegan (selftest: `python3 diagrams.py`) |
| `process_audio.py` -> `build_timeline.py` -> `build_audio.py` -> `master_audio.py` | rantai audio & timeline (urutan wajib) |
| `check_layout.py` | audit margin 40px — HARUS bersih sebelum render |
| `analisis/sapuan_mendalam.py` + `skor_ulang.py` | riset kata kunci real-time (±1.900 frasa bersih blokir, 55 tema); laporan: `analisis/HASIL_MENDALAM.md` |
| `analisis/pemeta_peluang.py` | ANALISIS v4 pohon topik bercabang -> pohon_topik.json + PEMETA_PELUANG.md (rencana seri; detail §9) |
| `pustaka/<Episode>/SIAP_TEMPEL.md` | teks siap tempel YouTube (judul, deskripsi, tag, komentar) |
| `PUSTAKA.md` | indeks semua episode |

## 4. Resep episode baru (urutan persis)
1. Pilih topik: baca `analisis/PEMETA_PELUANG.md` (rencana seri bercabang, momen NAIK) dulu, lalu
   `analisis/HASIL_MENDALAM.md` (status SEGAR, sains >= 2, klaster spesifik kuat, banyak frasa YouTube).
   Jalankan ulang analisis: push perubahan `analisis/**` (atau gh workflow run) — bot commit hasil ke branch.
2. Buat `episodes/epNN_slug/{content.json, config.env, METADATA.md}` — salin pola episode terakhir.
3. Tambah 8 fungsi diagram di `diagrams.py` (gaya: label polos tanpa kotak, tanpa panel; elemen besar; gerak
   selalu ada). Daftarkan di `VISUALS.update({...})` + selftest. `python3 diagrams.py` harus lulus.
4. Ganti fallback episode + paths di `.github/workflows/render.yml` ke slug baru.
5. Rekam 9 klip VO: TTS Arena **`voice-00`** (pria, id-ID) — suara channel, JANGAN diganti. Simpan ke
   `episodes/<slug>/audio_raw/`. (Batasi 9 panggilan per giliran karena cap 10/giliran. Kalau harus rekam ulang
   1-2 klip, JANGAN ubah panjang teks jauh: teks lebih pendek dari take asli bisa lolos jadi terlalu cepat
   (QC "masih cepat >2,10 kata/s") dan menggeser jeda antara adegan (ekor <0,25 s = QC "jeda sempit").
   Kalau kuota habis, catat di status mana klip yang belum sinkron dengan naskah — JANGAN push dulu.)
6. Pipeline lokal:
   ```bash
   source episodes/<slug>/config.env
   cp episodes/<slug>/content.json . && mkdir -p audio audio_proc build
   cp episodes/<slug>/audio_raw/*.wav audio/
   export KT_BUILD=build
   SPEED=$SPEED python3 process_audio.py          # QC: SEMUA KLIP BERSIH
   MAXDUR=$MAXDUR python3 build_timeline.py       # harus < MAXDUR (exit 2 kalau lewat)
   SPEED=$SPEED python3 build_audio.py && python3 master_audio.py
   python3 check_layout.py                        # HARUS: tata letak bersih
   python3 render.py --times auto --ss 1.0 --sharpen 0 --sheet --outdir build/preview  # cek mata montase
   ```
7. Perbarui waktu bab di METADATA.md & SIAP_TEMPEL.md dari `timeline.json` (start tiap adegan -> menit:detik).
8. Commit + push -> render jalan sendiri -> `gh run watch <id> --exit-status` -> cek Release terbit (Latest).
9. Buat `pustaka/<Episode>/{SIAP_TEMPEL.md, METADATA.md}` + tambah bagian di `PUSTAKA.md`.
10. Perbarui bagian "Status terkini" di file ini.

## 5. Aturan tetap channel
- Metadata YouTube **ASCII saja** (tanpa emoji/panah/simbol aneh). Baris pertama deskripsi = kata kunci utama.
- MAXDUR 178 s (durasi BEBAS, jangan dibatasi 140); VO santai tapi TIDAK seret (audio v2: output +-1,8-1,9 kata/detik).
- Tanpa subtitle/caption di video (fitur caption ada, default mati — biarkan). Keputusan user 23 Sep: TETAP tanpa caption.
- Audio: VO + **SFX saja, TANPA musik latar** (keputusan user 23 Sep). SFX = sfx.py (sintetis).
- 1 topik = 1 arah, penjelasan dari nol, penutup memuaskan; sumber kredibel di outro & deskripsi.
- Sensitif: jawab sainsnya tuntas, tidak menyerang keyakinan (ada pola kueri "menurut islam" di Indonesia).

## 6. Kandidat episode berikutnya (data 20 Sep 2026, perbarui dari analisis terbaru)
1. Kram & kesemutan (skor 83,1) 2. Hujan & awan putih (80,0) 3. Listrik & magnet (66,9) 4. Cegukan (65,5)
5. Antrean lama yang masih kuat: uban (91,1), megalodon (76,4), Gunung Padang/Lawu (79,2), petir (54,7), aurora (46,0).

## 7. Perintah cepat (keadaan baru: render LOKAL, bukan Actions)
```bash
pip install -r requirements.txt                    # sekali per sandbox
tools/render_lokal.sh shorts ep49_bintang prep     # cek cepat: audio + timeline + tata letak
tools/render_lokal.sh shorts ep49_bintang          # render penuh -> dist/
tools/render_lokal.sh long v02_laut_dalam          # video panjang 16:9
python mesin_v11.py && python diagrams.py && python sfx.py   # selftest mesin
git add -A && git commit -m "..." && git push origin main    # simpan kode (tanpa MP4)
gh run list --limit 3                              # lihat uji ringan (selftest.yml)
```
Catatan lingkungan sandbox: `suggestqueries` Google/YouTube diblokir -> sapuan analisis real-time harus
dijalankan di mesin yang punya internet penuh (atau pakai alat web search agen); `ffprobe` tidak ada, pakai
ffmpeg dari `imageio_ffmpeg.get_ffmpeg_exe()`; jaringan sandbox ber-allowlist (GitHub/PyPI/npm saja).

## 8. Masalah & jebakan yang pernah terjadi (jangan diulang)
- **Reset sandbox bisa menggulung .git lokal** (terjadi saat Ep29, 21 Sep): HEAD kembali ke commit dasar clone
  padahal file kerja utuh. SOLUSI: `git fetch origin arena/01a0cc99-kliktahu-shorts` -> `git reset --mixed
  FETCH_HEAD` (working tree diselamatkan, riwayat kembali dari remote) -> commit ulang. Cek `git log --oneline -3`
  SEBELUM commit; kalau parent = 5860a95 (bukan commit terakhir yang kupush), itu tanda .git sudah direset.
- Patch python via heredoc dengan f-string ber-escape (`\"""`) -> SyntaxError; pakai string pengganti sederhana + assert.
- Saat memperbaiki tail diagrams.py jangan buang/menduplikasi blok `if __name__ == "__main__"` (pernah bikin
  `t29()` liar -> NameError).
- redam_napas: JANGAN naikkan mulai_redam dari -28.5; verifikasi napas pakai QC skrip, bukan replikasi manual
  (lihat catatan di bagian Status).
- Push non-fast-forward: bot analisis.yml bisa commit duluan -> SELALU `git pull --rebase` sebelum push.
- `gh workflow run render.yml` -> 403 (tanpa actions:write) — push = satu-satunya pemicu.
- ffprobe tidak ada; pakai `imageio_ffmpeg.get_ffmpeg_exe()`. `isLatest` bukan field valid `gh release view`;
  cek "Latest" lewat `gh release list`.

## 8. Analisis v3 & keputusan topik (21 Sep 2026) — konteks Ep30
User minta topik yang "membuat video berkembang lebih pesat" dengan analisis real-time mendalam. Yang dilakukan:
1. **Sapuan v2 -> v3** (`analisis/sapuan_mendalam.py`): sinyal permintaan lama dipertahankan + 4 sinyal
   pertumbuhan baru dari TEKS frasa: rel (pengalaman pribadi: aku/sering/padahal/terus...), kom (mengundang
   bercerita: punya/anak/kucing/pacar...), vis (bisa diperlihatkan: bunyi/warna/keluar/api...), ever (bebas
   frasa musiman). `skor_tumbuh = skor + rel*1.2 + kom*1.5 + vis*0.8 + ever*3`. Tema baru: kedutan, gusi &
   rahang, kentut, ngiler, mimisan & hidung. `analisis/skor_ulang.py` diselaraskan.
   Alasan bobot: riset 2025-2026 - Shorts didistribusikan oleh share & completion & komentar (bukan CTR);
   niche konsisten tumbuh 3-5x (Shopify/VidIQ/Conbersa 2026).
2. **Sapuan real-time dijalankan di CI** (internet penuh hanya di runner): push analisis -> 254 panggilan
   autocomplete -> `analisis/hasil_mendalam_20260921.json` (2.004 frasa) + `HASIL_MENDALAM.md`.
3. **Pemenang: gigi & mulut (tumbuh 257.0)** - unggul SEMUA komponen (jml 73, kuat 58, yt 44, rel 39, kom 37,
   vis 18, ever). Mata (211.0) kuat permintaan tapi kalah rel/kom. Sub-sudut dipilih "bau mulut" (halitosis):
   15 frasa spesifik + head phrase "kenapa bau mulut" + sudut anak (orang tua) + mitos "sikat gigi cukup"
   yang bisa dibongkar = umpan share/komentar terbaik. Prior sains tema gigi dinaikkan 1.5 -> 2.0 (biofilm +
   senyawa sulfur VSC sainsnya kuat).
4. Ep30 diproduksi penuh mengikuti resep 10 langkah (lihat status di §2).
Jangan hapus bagian ini sebelum Ep30 rilis — ini jejak keputusan kalau chat error.

## 9. Mesin animasi v4 (21 Sep, Ep31) — paket gerak populer ala YouTube
Permintaan user: "animasi bergerak yang populer di YouTube". Helper baru di diagrams.py (semua alpha-aware,
skala S()/SS, aman margin lewat audit teks):
- `_pop_pill(img,cx,cy,text,fsz,fill,alpha,tt,fg,dot)` — pil muncul dengan scale overshoot `eob` (bounce).
- `_pop_txt(img,cx,cy,text,f,fill,alpha,tt,dy)` — teks pop-in memakai paste_c scale.
- `_shine_on(img,x0,y0,x1,y1,tt,alpha)` — sweep kilau diagonal ter-clipping rounded-rect (butuh PIL ImageChops).
- `_meter_on(img,cx,cy,r,frac,col,alpha)` — gauge 180° + ticks + jarum (level pemicu).
- `_bar_on(img,x,y,w,h,frac,col,alpha,tg)` — bar dengan garis kecepatan berjalan di dalam fill.
- `_ripple_on(img,cx,cy,r,col,alpha,tg,n,squash)` — cincin melebar berulang.
- `_swarm_on(img,cx,cy,t,col,alpha,n,sp,spread)` — swarm partikel keluar (sensasi kedut/kilat).
- `_tile_rot(img,cx,cy,tw,th,drawfn,ang,alpha)` — render tile kecil lalu rotate (koin berputar, mata berkedip).
- `_mata31(dd,sz,col,blink,iris)` — mata almond tile dengan kelopak kedip (blink = 0..1).
Pola pemakaian: muncul bertahap pakai `_dw(tl,dur,a,b)`; beat periodik pakai `beat = max(0,1-((tg%T)/T)*3)`;
label sensasi (TIK!/KEDUT!) pop pakai `_pop_txt` dengan alpha=beat. Jangan hapus helper ini — dipakai episode
berikutnya. Gunakan minimal 3-4 helper baru per episode agar gerak makin kaya (standar baru channel).

## 9. Analisis v4 "Pemeta Peluang" (21 Sep 2026) — pohon topik bercabang
Upgrade analisis atas permintaan user ("menyeluruh, mendalam, bercabang, sistem sendiri, mutakhir").
Sistem milik sendiri (bukan fork): membangun **POHON TOPIK** 3 lapis dari data sapuan v3.
- **L0 warisan**: muat `analisis/hasil_mendalam_*.json` TERBARU (semua frasa terkurasi sapuan v3 + skor_tumbuh).
- **L1 cabang**: untuk 14 keluarga teratas, buka cabang konteks via autocomplete: `kenapa <inti> <aspek>`
  (aspek: anak, bayi, malam, pagi, setelah makan, terus, tiap hari, bahaya, tanda, sembuh, saat hujan, lama)
  + `apakah/kapan <inti> bahaya` — 8 query/keluarga, atribusi regex TEMA v3.
- **L2 pendalaman**: 2 daun terkuat (frasa "kenapa/apakah/kapan/bagaimana", pos <= 5, >= 3 kata) disapu ulang.
- **Skor**: `poin_daun = (11-pos, min 1) + 1.5*yt + 1(jika <=4 kata) - 3(event)`; per frasa digabung per keluarga:
  `skor_keluarga = skor_tumbuh + jaring*2.5 + (kedalaman-1)*1.5 + peluang*2.0*jml/10`
  (jaring = cabang aktif >= 2 daun; peluang = porsi frasa >= 5 kata). Transparan: semua komponen dilaporkan.
- **Momen**: NAIK/TURUN/STABIL/BARU vs `keluarga_terakhir.json` snapshot sebelumnya (ambang ±5%) — deteksi
  topik yang sedang menaik SEBELUM meledak.
- **v4.1-v4.2 (perintah user "hapus SEMUA yang kentut dll, cari yang potensi views besar")**: `BLOKIR =
  ("kentut", "ngiler", "keringat & bau badan")` — SATU SUMBER di sapuan_mendalam.py; frasa blokir DIHAPUS
  TOTAL dari data SEBELUM atribusi (bug run-4: purge sesudah atribusi -> KeyError frasa first-match tema
  lain; fix run-5). pemeta v4 mewarisi + lapis kedua (tak diranking/tak dicabangkan). Metrik UTAMA:
  **`skor_views` = jml + kuat + yt*2 + vis*0,8 + niat*0,6 + sains*2 + jaring*2**; laporan diurut
  skor_views; skor_keluarga tetap dilaporkan; semua komponen jadi kolom tabel (transparan).
- **Output** `analisis/`: `pohon_topik.json` (pohon penuh), `keluarga_terakhir.json` (snapshot momen),
  `PEMETA_PELUANG.md` (tabel keluarga + RENCANA SERI 3 episode/keluarga + MOMEN NAIK).
- **Uji offline**: `python3 analisis/pemeta_peluang.py --uji` (fixture, tanpa jaringan — wajib lulus sebelum push).
  Env: `KT_PETA_BUDGET` (default 300 panggilan), `KT_PETA_JEDA` (default 0.15 s). Degradasi anggun: bila
  autocomplete gagal, pohon tetap dibangun dari L0 (tanpa cabang) — tidak pernah crash.
- **CI**: `analisis.yml` = sapuan v3 dulu -> pemeta v4 -> bot commit `analisis/*.json + HASIL_MENDALAM.md +
  PEMETA_PELUANG.md` [skip ci]. `suggestqueries` diblokir di sandbox -> percabangan nyata hanya di runner.
- **Riwayat run CI**: run-1 gagal (set tak serialkan-able -> fix); run-2 sukses (278 panggilan, snapshot
  momen resmi); run-3 = v4.1 (blokir + skor_views); run-4 gagal (purge sesudah atribusi -> KeyError);
  run-5 = v4.2 FINAL bersih (1.932 frasa, 0 frasa blokir di semua artefak). Hasil acuan terbaru selalu di
  `analisis/PEMETA_PELUANG.md`.


## 10. Analisis v6 "PAPAN STRATEGI" (23 Sep 2026, sesi 01a0cc99)
`analisis/mesin_v6.py` - lapis strategi di atas v5 (v5 tetap jalan duluan di CI).
- **skor_v6 (0-100)** = 34 permintaan (skor v5 dinormalisasi) + 18 Wikipedia (pageview id.wikipedia 60 hari,
  tren 30 vs 30 hari; judul artikel dicari lewat opensearch resolver) + 18 celah (1 - kejenuhan pesaing
  YouTube: jumlah/umur/median views) + 10 visual + 10 pilar channel + 10 momen (kalender).
- **Sudut miner**: frasa KENAPA/PADAHAL/APAKAH per tema -> usulan sudut yang beda dari judul pesaing.
- **Hook generator** dengan `HOOK_HINDARI` (buang benih haram/halal/agama/dosa/mahal/harga/brand/ml/game
  dan benih > 5 kata) - mencegah hook ngawur seperti "Pernah mengalami anjing haram?".
- **Loop performa**: `analisis/performa.csv` (isi views/retensi dari YouTube Studio per episode) -> bobot pilar
  menyesuaikan otomatis. Kosong = netral.
- Output: `analisis/STRATEGI_V6.md` (ranking + kalender 7 episode + sekuel) & `strategi_v6_<tgl>.json`.
- `python3 analisis/mesin_v6.py --uji` WAJIB lulus sebelum push. Offline (sandbox) komponen wiki/pesaing
  netral -> ranking lokal tidak bermakna; pakai hasil CI (bot commit "analisis v6 real-time [skip ci]").

## 11. Mesin v11 "EDITOR" + SFX (23 Sep 2026, Ep42) - motion setara channel besar
File baru: **`mesin_v11.py`** (adegan + transisi + beat) dan **`sfx.py`** (bunyi sintetis). Episode lama
(Ep24-41) TIDAK berubah: event hanya muncul bila content.json memakai visual ber-BEATS atau trans v11.
- **Tipografi kinetik**: `_judul11` kata jatuh satu per satu (pegas) + sapuan STABILO di kata kunci
  (field `hl` per adegan di content.json). `_stiker11` stiker tebal outline putih + bayangan keras, pop
  overshoot + goyang. `_bab11` penanda "FAKTA n/7" + segmen progres (retensi).
- **Gerak & cahaya**: `_glow11` (sprite radial ter-cache), `_panah11` panah bezier menggambar diri,
  `_gelom11` gelombang berjalan (+peredaman), `_pancar11` busur sinyal, `_partikel11` ledakan saat muncul.
- **Objek**: `_hp11`, `_menara11`, `_router11`, `_micro11`, `_orang11`, `_baterai11`, `_dinding11`.
- **Transisi baru** (field `trans`): `punch` (zoom-through + kilat + blur arah), `slide` (whip elastis +
  blur gerak), `glitch` (irisan RGB). Semua + aberasi kromatik.
- **BEATS = satu sumber kebenaran**: `BEATS[visual] = [(fraksi_durasi, jenis_suara)]`; fungsi gambar memakai
  fraksi yang sama (`_b(N, i)`), `events(scenes)` -> sfx + `punch_kamera` (dorongan kamera di impact/boom).
- **Zona**: konten fakta v11 digeser naik 70 px (GESER) supaya zona kosong y 150-650 terisi & jauh dari UI
  Shorts bawah; teks penting jangan di y > 1640 atau kolom tombol kanan (x > 950, y 1100-1700).
- **SFX** (`sfx.py`): 14 bunyi (whoosh, swish, swish_up, pop, tick, click, impact, thud, boom, riser, ding,
  glitch, zap, door). `master_audio.py` menambah lapisan SETELAH loudnorm VO: dasar -16 dB (KT_SFX_DB),
  ducking -7 dB saat VO bicara, limiter puncak -1,2 dBFS. `KT_SFX=0` mematikan. Uji: `python3 sfx.py`.
- **QC**: master juga menulis `build/audio_master_vo.wav` (stem VO, gain sama). `qc_mp4.py` memakai stem
  itu untuk cek VO per adegan (SFX tidak bikin gagal palsu); korelasi MP4 vs audio_master tetap >= 0,97.
  render.yml mengunggah stem ini di artefak audio.
- **Episode v11 baru**: set `"mesin": "v11"`, tulis 9 fungsi `sc_*NN` di mesin_v11.py (pakai `_hdr`, `_b`),
  isi BEATS, daftarkan di VISUALS11, `python3 mesin_v11.py` + `python3 diagrams.py` harus lulus.
- Biaya render: ~0,9 s/frame di SS 1,5 lokal (2 vCPU) - setara mesin lama; transisi hanya 0,52 s/adegan.

## 12. Mesin FX 2026 "MUTAKHIR" (24 Sep 2026) - semua elemen video Long + Shorts
Tujuan: tampilan setara motion design September 2026 (tren: kinetic typography tegas tapi terbaca,
Liquid Glass ala iOS 26, soft depth 2D/3D, tekstur taktil/grain, transisi sinkron SFX).
Modul bersama **`mesin_fx.py`** (numpy + PIL, tanpa dependensi baru) dipakai `render.py`, `mesin_v11.py`,
`diagrams.py`, `long/mesin_long.py`, `long/render_long.py`.

**Finishing sinematik (tiap frame):** `bloom` ADAPTIF (adegan terang -> ambang naik, kekuatan turun; tidak
pernah membakar putih) -> `grade` (preset `sinema` Long / `krem` Shorts / `netral`) -> `lensa` (aberasi tipis)
-> `vinyet` -> `grain` film bergerak. Long: `FINISH` di mesin_long. Shorts: `_finish` di render.py.
**Kamera:** drift handheld organik (`nois2`, bukan sinus), `zoom_blur` saat punch-in, `spring()` untuk pop.
**Elemen:**
- Long: teks berbayang lembut (`BAYANG_TEKS`), panel `KACA_CAIR` (latar diburamkan+dibiaskan, kilap tepi
  spekular + sapuan kilau), judul v2 (kata muncul bertahap + blur gerak), stiker v2 (gradien + kilau), stempel,
  chip, callout, glow, `ODOMETER` (angka bergulir per digit, digit cepat diburamkan, jendela terukur 1.0*fsz),
  kartu bab v2 (latar blur + angka outline samar), bokeh partikel depan.
- Shorts: latar **mesh gradient** bergerak (`mesh_latar`: aksen adegan + hangat + sejuk, gantikan blob datar),
  judul `KINETIK_2026` (kata terangkat dari balik garis/mask + spring + blur vertikal + bayangan hangat),
  stiker gloss + pop spring + sapuan kilau, panel `PANEL_LEMBUT` (bayangan ambient lembut).
**Transisi baru:** Long `TRANSISI_POOL = zoomthru, tinta, whip, iris` (bergilir per bab).
Shorts `zoomthru` (blur radial menembus), `tinta` (sapuan tinta tepi bergelombang + garis aksen),
`cahaya` (light leak hangat). Pool otomatis Shorts: zoomthru, tinta, speed, cahaya, glint, split, zoom, bands, iris, rise.
Bisa dipakai eksplisit lewat `"trans": "tinta"` di content.json.

**Saklar:** `KT_FX=0` -> kembali ke mesin lama (cadangan darurat). `KT_BLOOM=0.34` (kekuatan bloom Shorts).
Flag modul: `BAYANG_TEKS`, `KACA_CAIR`, `ODOMETER`, `FINISH`, `TRANSISI_POOL` (mesin_long), `KINETIK_2026`
(mesin_v11), `PANEL_LEMBUT` (diagrams).
**Biaya render (terukur):** Long 0.22 s/frame (sebelumnya 0.17) - CI tetap ~10-13 menit. Shorts 0.62 s/frame
di SS 1.0. Uji lolos: `--check` Long02 1228 frame, sapuan 61 frame Shorts Ep48, thumbnail v01/v02, mode KT_FX=0.
**Jebakan:** bloom non-adaptif membakar langit/krem; jendela odometer < tinggi glyph memotong digit (glyph
Poppins-Bold = 0.87*fsz, pusat visual 0.025*fsz di atas anchor mm); ImageChops.screen lambat -> pakai add/blend;
radius GaussianBlur harus float() biasa.

## 13. Keamanan & HEMAT ACTIONS (24 Sep 2026) - WAJIB setelah akun GitHub di-flag

> Sebagian isi bagian ini sudah digantikan oleh **§14** (6 Okt 2026): render video tidak lagi di GitHub
> Actions dan workflow render sudah dipindah ke `docs/arsip/workflows/`. Bagian ini tetap penting sebagai
> riwayat penyebab akun lama di-flag.
Kejadian: 24 Sep ~23.00 WIB akun `elthsi09-ZERO-X` di-flag GitHub (profil/repo 404 publik, API 404,
"Actions has been disabled for this user"); git push/pull tetap jalan. User mengajukan tiket ke GitHub Support.
Dugaan pemicu: beban Actions besar (12-16 runner paralel per render + analisis tiap 6 jam + commit bot) dan
aplikasi AI pihak ketiga (branch `feat/longform-motion-upgrade`, 4 commit identik dalam 3 menit) - sudah diputus user.
Aturan sejak ini:
- Render Shorts: potongan bawaan **6** (dulu 12), `max-parallel: 6`. Long: `CHUNKS=8` (dulu 16), `max-parallel: 8`.
- Analisis terjadwal **sekali sehari** 21.00 UTC (04.00 WIB), dulu tiap 6 jam.
- Izin workflow minimum: `contents: read` di tingkat workflow; hanya job `merge` (buat Release) yang `write`.
- Jangan push beruntun; kumpulkan perubahan lalu satu push. Selalu `[skip ci]` kecuali memang mau render.
- `tools/gh_control.sh` dihapus (skrip lama yang meminta PAT dan membuat repo PUBLIK).
- `.gitignore` menolak pola rahasia (.env, *.pem, *.key, credentials*.json, .netrc, dll). Pindai rahasia: bersih.
- Kalau repo dijadikan PRIVAT: Actions memakai kuota menit (paket Free 2.000 menit/bulan). Perkiraan: render
  Shorts ~60-90 menit-runner, Long ~100-140, analisis harian ~5 -> +-15 render/bulan masih muat.

---

## 14. PINDAH AKUN & REPO — RENDER TIDAK LAGI DI GITHUB ACTIONS (6 Okt 2026)

**Alasan:** akun GitHub lama `elthsi09-ZERO-X` sudah di-flag (lihat §13). Pemilik membuat akun baru
`chronoidchannel-stack` dan repo baru **`chronoidchannel-stack/KlikTahu-`**. Seluruh mesin (kode, naskah,
metadata, data analisis) dipindahkan ke repo ini; yang TIDAK ikut: audio mentah 192 MiB dan semua video.

**Aturan baru yang WAJIB dipatuhi (ini yang menjaga akun tidak di-flag lagi):**
1. **Render video tidak di GitHub Actions.** Render lokal: `tools/render_lokal.sh <shorts|long> <slug>`.
   Runner gratis GitHub hanya untuk membangun/menguji perangkat lunak, bukan komputasi umum.
2. **Jangan simpan MP4** di repo maupun di Releases. `.gitignore` sudah memblokir `*.mp4`, `dist/`,
   `build/`, `frames*/`, `parts/`, `/timeline.json`, `/content.json`, `audio*_proc/`.
3. **Actions hanya uji ringan** (< 5 menit, tanpa render frame, tanpa cron):
   `.github/workflows/selftest.yml` (selftest mesin + analisis `--uji` + cek berkas wajib).
   Workflow render lama ada di `docs/arsip/workflows/` — JANGAN dihidupkan kembali tanpa izin pemilik.
4. **Jangan simpan rahasia apa pun** di repo/chat: token, kunci API, `.env` asli, kredensial.
   `.gitignore` menolak `.env*`, `*.pem`, `*.key`, `*secret*`, `credentials*.json`, `.netrc`.
5. **Jangan hubungkan aplikasi AI pihak ketiga** lain ke repo ini (aplikasi bot yang push beruntun
   termasuk pemicu flag sebelumnya).
6. **Jangan push beruntun**; kumpulkan perubahan jadi satu commit bermakna. Pakai `[skip ci]` untuk
   perubahan yang tidak perlu diuji.
7. **Audio mentah tidak di repo** (268 WAV = 192 MiB). Daftar berkas + ukurannya: `docs/audio-manifest.md`.
   Salinan asli: arsip Google Drive `kliktahu.zip` -> kembalikan ke `episodes/<slug>/audio_raw/` sebelum render.
8. **Sandbox bisa ter-reset:** perbarui AGEN.md + commit tiap tahap selesai. Jangan menunggu akhir.

**Keadaan mesin di repo ini (per 6 Okt 2026):**
- Struktur mengikuti cetak biru §4 prompt pemilik: mesin di akar repo, `episodes/` (26 episode Ep24-Ep49),
  `pustaka/` (teks siap tempel), `long/` (Long01 lubang hitam, Long02 laut dalam), `analisis/` (v3-v6 + data),
  `fonts/` (Poppins + OFL), `docs/` (prompt proyek, manifest audio, atribusi, arsip workflow).
- Dependensi dinaikkan ke versi mutakhir dan **sudah diuji lulus** bersama kode ini:
  pillow 12.3.0, numpy 2.4.6 (2.5.3 di Python 3.12+), imageio-ffmpeg 0.6.0. Batasnya ada di `requirements.txt`.
- Uji yang sudah dijalankan (lulus): `mesin_v11.py` (71 adegan, 6 transisi, 19 event), `diagrams.py`
  (selftest semua visual), `sfx.py` (24 bunyi), `analisis/{pemeta_peluang,mesin_v5,mesin_v6,sapuan_mendalam}.py --uji`.
- Lisensi repo: hak cipta dilindungi (`LICENSE`). Atribusi pihak ketiga: font Poppins (SIL OFL 1.1) dan
  citra M87* EHT (CC BY 4.0) -> `docs/ATTRIBUSI.md`.
- **(Usang, lihat §15-16: Ep50 Orionid diproduksi 15 Okt 2026 dengan mesin v12.)** Episode berikutnya: **Ep51** (Shorts) dan **Long03**,
  topik dari antrean analisis (piramida, lubang hitam Shorts, ular, aurora, es & salju, uban, cegukan, pelangi).
  Tunggu perintah pemilik; untuk episode baru buat `episodes/ep50_<slug>/` + `mesin_v11_ep50.py` (pola Ep43-49)
  lalu render lokal.

---

## 15. SESI 15 OKT 2026 — DATA KANAL NYATA, STANDAR v12, KEPUTUSAN Ep50 (agen Arena)

**Cara kerja agen sekarang (perintah pemilik, wajib):**
1. **Tidak memakai workspace chat** sebagai tempat kerja. Clone repo ke direktori sementara di luar
   workspace (mis. `/tmp/kt/repo`), kerjakan, commit, push. Kalau sandbox reset -> clone ulang dari GitHub.
2. **Hasil jadi (MP4, thumbnail, audio master .m4a, metadata, laporan) dikirim ke Google Drive**
   folder `KlikTahu_Produksi/` (Shorts/<slug>/, Project_Docs/, Metadata/, Thumbnails/). GitHub hanya kode,
   naskah, data analisis, dokumen. Token GitHub hanya di `~/.netrc` (tidak pernah di repo/chat).
3. Video dibuat **dengan mesin repo** (numpy+PIL), **bukan** generator gambar AI.
4. **Audio ke pemilik tidak pernah WAV**: TTS -> .m4a/.mp3; WAV 48 kHz hanya perantara internal pipeline;
   deliverable audio = `.m4a` AAC 256k. VO harus utuh (cek integritas), jelas, tanpa potongan.
5. **Tanpa musik/BGM/instrumental apa pun.** Prioritas audio: VO -> SFX sinematik per BEAT -> ambient halus.
6. Struktur video wajib 5 babak berurutan: Hook -> Agitation -> Body -> Micro-Climax -> Seamless Loop Outro
   (frame akhir = frame 0). Rincian lengkap + urutan prioritas yang sudah dikoreksi: **`docs/STANDAR_PRODUKSI_V12.md`**.
7. Suara VO sesi ini: **voice-00** (sudah dipilih pemilik lewat audisi).

**Data kanal publik @KlikTahu per 15 Okt 2026** (sumber laporan lengkap: `analisis/LAPORAN_15_OKT_2026.md`):
88 subscriber, 36 Shorts (14 Sep-1 Okt), 40.678 views, rata-rata 1.130/video, 0 video panjang. Tiap video
berhenti di ~1 rb (lolos uji awal, gagal perluasan) -> masalah retensi 2 detik pertama & tengah video.
Terbaik: Supermoon 3.243 (129,7/hari), Pesawat mati 1.378 (91,9), Es batu 1.290 (86,0), Bulan Purnama 26 Sep
2.741 (85,7). Terburuk: Hujan meteor 21-22 Okt yang terbit 14 Sep = 210 views (terlalu awal 5 minggu).
Temuan: (a) peristiwa langit bertanggal 2-3x views bila terbit H-2/H-3; (b) fisika sehari-hari melawan
intuisi + taruhan = evergreen terbaik; (c) judul TANPA awalan "Kenapa" 59,5 vs 41,7 views/hari; (d) pertanyaan
buku teks generik terburuk; (e) pilar: LANGIT 56,3/hari, TEKNOLOGI 53,9, HEWAN 48,3, BUMI 41,5, TUBUH 34,7
(tapi suka% tertinggi 2,34). `analisis/performa.csv` kini berisi data nyata (views/hari x10, suka).
Episode repo yang TIDAK ada di kanal: Ep27, 31, 34, 36, 37, 41, 42, 42L, 43, 44; video Drive 7-13 Okt juga
tidak tampak di kanal publik (tanyakan pemilik: kanal lain / unlisted?).

**Analisis LIVE 15 Okt** (`analisis/STRATEGI_V6.md`, `HASIL_V5.md`, `PEMETA_PELUANG.md`, `HASIL_MENDALAM.md`,
json bertanggal 20261015): papan v6: serangga 42,2 (pesaing lemah), **ular & reptil 39,6 (celah 0,59, median
pesaing 157 rb)**, piramida 36,7 (223 rb), burung 34,8, anjing 34,7 (sudut najis -> hindari), lubang hitam 33,5
(403 rb, kanal sudah 3x), es & salju 33,3, tekanan darah 32,8, pelangi 32,6, cegukan 32,0. Velocity naik:
baterai +17, kucing +14,9, perut +14,8, hujan & awan +13,6 (momen musim hujan), meteor +19,5 (Orionid).
Segar: menangis & emosi 171, demam & imun 429 (pemeta), mimisan 299.

**Momentum luar:** BMKG musim hujan mulai pertengahan Okt (merata Nov, El Nino sampai awal 2027);
BRIN: telur ular menetas Nov-Jan, anak ular masuk rumah, mangsa ramai saat hujan; langit: Orionid 21-22 Okt,
Leonid 16-17 Nov, Geminid puncak 14 Des, Supermoon 24 Nov & 23/24 Des (verifikasi H-5).

**Keputusan antrean (terbit):** **Ep50 = Ular masuk rumah saat musim hujan** (judul utama: "Ular Masuk Rumah
Saat Musim Hujan? Bukan Karena Banjir"; 17-18 Okt) -> Ep51 Orionid 21-22 Okt (50-60 s, pakai aset Ep39; terbit
19-20 Okt) -> Ep52 Piramida bukan budak (24-25 Okt) -> Ep53 Semut muncul sebelum hujan (28-29 Okt) -> Ep54 Hujan
bikin ngantuk (1-2 Nov) -> Ep55 Habis nangis mata bengkak (5-6 Nov) -> Ep56 Leonid lalu Supermoon (13-14 & 20-21 Nov).
Target per video: swipe-away <= 35%, persen ditonton >= 70%, loop >= 100%, suka >= 2%, share >= 1%.

**REVISI 15 Okt (malam, keputusan pemilik "Ya! Ubah judul/topik!"):** **Ep50 = Hujan Meteor Orionid 21-22 Okt**
(terbit Senin 19 Okt 18.30-20.30 WIB) dan **Ep51 = Ular masuk rumah** (VO sudah jadi, folder `episodes/ep51_ular_rumah/`,
terbit 24-26 Okt). Alasan: peristiwa bertanggal H-2 bernilai 2-3x views; Orionid 14 Sep gagal karena 5 minggu terlalu dini.

## 16. SESI 15 OKT 2026 (lanjutan) — MESIN v12 KONTINUITAS DIBANGUN, Ep50 ORIONID DIPRODUKSI

**Berkas baru (semua punya selftest `python3 <file>`):**
- `mesin_v12.py` — inti v12: `t_kata/cues` (cue kata dari `build/kata.json`), `ease12/follow/esm/eio`, `morph`+`bentuk_*`,
  `kamera()` kontinu (nol di t=0 & t=total -> loop), `aksen_pada()` (warna aksen dicampur melintasi adegan),
  `loop_blend(meta)`, primitif `cakram_langit/garis_meteor/komet/jam/kompas/chip/label/silang/elips_pts/polyline_on`,
  registry `EVENTS12` (visual -> fungsi event SFX).
- `mesin_v12_ep50.py` — 7 adegan Ep50 (`komet50, salahjam50, debu50, jam50, arah50, orbit50, loop50`), dict `CUES`
  (kata kunci per adegan), `SFX` (bunyi per kata), `BEATS50`, `events_v12(sc)`, `daftar()` (mendaftar sendiri ke
  `mesin_v11.BEATS`, `diagrams.VISUALS`, `mesin_v12.EVENTS12`; aman terhadap impor melingkar).
- `align_kata.py` — faster-whisper `small` (CPU) -> `build/kata.json` (waktu kata per adegan, sudah ditambah lead_in).
  WAJIB memberi array numpy float32 16 kHz (PyAV yang terpasang menolak `transcribe(path)`). `pip install faster-whisper`
  dilakukan di sandbox (tidak masuk requirements.txt agar Actions tetap ringan; render_lokal.sh memanggilnya hanya untuk v12).
- `qc_loop.py` — korelasi frame terakhir vs frame 0 (>= 0,98).
- `sfx.py` +`morph`, `burn`, `thump`, `angin_malam`/`ambient_bed` (bed ambient, bukan musik).

**Perubahan mesin lama (kompatibel mundur, hanya aktif bila `content.json` punya `"mesin": "v12"`):**
`render.py`: `_is_v12(meta)`; mesh seed tetap + `aksen_pada`; tidak ada dorongan zoom per adegan; `_finish` memakai
`mesin_v12.kamera`; `draw_outro` memanggil `VISUALS[sc.visual]` bila ada; transisi `match/morph/hold` = tanpa crossfade;
akhir video tanpa fade krem, diganti `loop_blend` ke frame 0; meta `mesin`/`v12` diteruskan dari content.json.
`mesin_v11.events()`: adegan v12 memakai `EVENTS12` (semua SFX dari cue kata). `master_audio.py`: v12 -> dasar SFX -10 dB
(impact/thump puncak ~ -18 dBFS sebelum duck) + bed ambient -32 dB (`KT_AMBIENT_BED=0` untuk mematikan).
`tools/render_lokal.sh`: menjalankan `align_kata.py` setelah `build_timeline.py` untuk v12.

**Pelajaran Ep50:** TTS voice-00 dengan `TARGET_WPS=2.05 ATEMPO_MIN=0.93` (1.90 membuat VO terseret); hook teks harus
tampil <= 0,35 s; glyph `→`/`≈` tidak ada di Poppins (pakai kata); elemen baris alat Y_ALAT 1535 agar dasar <= 1625;
label jam di ATAS jam; orbit di luar cakram harus diklip; kontinuitas antar adegan dicek dengan nilai alpha/gelap/bintang
yang sama persis di akhir adegan N dan awal adegan N+1 (atau di-ease 0,6-1,0 s).

**Pelajaran render Ep50 (3x render ulang, 75 menit per render di sandbox 2 vCPU):**
1. `render._finish` memanggil `draw_streak()` = tiga pita miring generik di SETIAP batas adegan -> kini dimatikan untuk v12.
   Selalu periksa frame -0,08 s / +0,08 s di tiap batas adegan SEBELUM render penuh (`build/qc/batas.jpg`).
2. `ease12()` punya antisipasi NEGATIF -> jangan dipakai langsung sebagai radius/alpha (`max(0, ...)`/`clamp`);
   `diagrams.dot_on/ring_on` kini menolak r <= 0. Uji cepat semua frame per 0,25 s pada SS 0,5 (5 menit) sebelum render.
3. `_glow11` lama: `radial_gradient` bernilai 128 di tepi sisi -> alpha tidak nol -> kotak terlihat di latar gelap (diperbaiki).
4. Ekor komet = sprite gradasi ter-cache (bukan rangkaian titik).
5. Elemen non-persisten WAJIB keluar sebelum batas adegan: `mesin_v12.set_keluar(tl, dur)` di awal fungsi adegan +
   pembungkus `chip/label/stiker/bab/jam/kompas/silang/teks` mengalikan `KELUAR[0]`; primitif mentah dikalikan manual;
   `chip(..., persisten=True)` untuk elemen yang memang tetap (chip tanggal). `meteor_acak` berhenti 0,5 s sebelum batas.

**Mesin v12 (rencana awal, sebagian sudah terwujud di atas):** `morph()`, `anchor_out/anchor_in` + transisi `match`,
`depth` parallax 3 lapis, `ease_v12` (antisipasi/overshoot <= 8%/settle) + `follow()`, BEAT tingkat kata (port
`align()` Long), `energi` per babak, `hold`, `sc_outro_loop`, SFX tambahan (whoosh berarah, reveal, morph, tick,
thump, riser, tetes, retak, hujan, angin, room tone), QC baru (`qc_audio.py`, `qc_sync.py`, `check_layout --beban`,
`qc_mp4 --loop`). Semua wajib punya `--uji`; render tetap lokal di sandbox (background), bukan Actions.


## 17. SESI 15 OKT 2026 (malam) — Ep50 DIBUAT ULANG (v2): VO "UNTUK TELINGA MANUSIA" + visual kedalaman

**Keluhan pemilik atas v1:** VO terdengar "terpotong". **Akar masalah yang terbukti (diukur, bukan ditebak):**
1. **Sumber TTS diminta sebagai `.mp3` = 32 kb/s mono 24 kHz** -> semua di atas ~8 kHz hilang (pita 8-11 kHz -37 dB vs
   -14 dB pada WAV) + artefak codec yang terdengar "berkedip/terpotong" setelah dinaikkan +9 dB dan diberi treble boost.
   **WAJIB: minta TTS sebagai `.wav`** (PCM 16-bit 24 kHz, lebar pita penuh). Jangan pernah lagi `.mp3` untuk sumber VO.
2. `process_audio.py` (rantai lama): `add_breath` menyisipkan **hening digital murni** (120 ms nol) di jeda -> "lubang";
   `silenceremove -50 dB` + `potong_napas` (-48 dB, fade 10/20 ms) memakan onset lembut (S/H) dan ekor vokal;
   `atempo 0.93` (WSOLA) menambah tekstur patah. Klip TTS sendiri juga punya hening digital 300-700 ms di dalam jeda.
3. Master lama: 2 kompresor + EQ + treble + `loudnorm` dinamis + limiter di atas VO yang sudah diproses -> "memompa".

**Solusi (dipakai semua episode v12 mulai Ep50 v2):** `vo_manusia.py` menggantikan `process_audio.py` bila
`content.json` `"mesin": "v12"` (otomatis di `tools/render_lokal.sh`; paksa lama dengan `KT_VO_CHAIN=lama`):
decode 48 kHz (soxr) -> de-esser spektral lembut (5,5-10 kHz, maks 4 dB, hanya saat desis dominan) + EQ statis sangat
halus (-1 dB @300 Hz, +0,8 dB @3 kHz, +1 dB rak >8,5 kHz) -> HPF 65 Hz -> kompresor perata 2:1 (lutut 8 dB) -> gain
LINEAR -> kompresor puncak 3:1 (>-8 dBFS, attack 1 ms) -> gain LINEAR ke -16 LUFS -> limiter TP -2 dB (hanya menyentuh
1-2 ms transien per klip) -> trim HANYA hening sejati (-55 dBFS) dengan pra-gulir 120 ms / pasca-gulir 350 ms + fade
raised-cosine 30/150 ms -> **nada ruang merah muda -63 dBFS** di seluruh klip (menghapus "vakum" digital) -> dither
TPDF 16-bit. **Tanpa atempo, tanpa hening sisipan, tanpa silenceremove.** QC per klip: onset >= 100 ms, ekor >= 300 ms,
0 ms hening digital, puncak <= -2 dBFS, -16 LUFS +-1, dan `--asr` (faster-whisper small): kata PERTAMA & TERAKHIR
dikenali + kemiripan transkrip >= 0,9 (angka dinormalkan: "dua ribu enam puluh satu" == "2061"; nama diri boleh beda
ejaan). Laporan: `build/vo_qc.json`. `master_audio.py` v12 (`main_v12`): HPF 40 Hz -> gain linear VO ke -16 LUFS -> +SFX
(duck) + ambient -> gain linear campuran ke -14 LUFS -> limiter TP -1,5 dB; **tidak ada kompresor/EQ lagi** (matikan
dengan `KT_MASTER_V12=0`). `build_audio.py`: batas "awal lambat" 0,55 s untuk `vo_chain: v12` (napas alami disimpan).
Irama VO diatur dari **naskah** (elipsis/koma/titik dua), bukan time-stretch. Parameter timeline v2: `lead_in` 0,2,
`tail_intro` 0,45, `tail_fact` 0,5, `tail_outro` 0,9 (jeda antar babak ~1,0-1,1 s termasuk napas).

**Visual v2 (mesin_v12 + ep50):** `cakram_langit` kini punya kedalaman: bintang 3 lapis (jauh/tengah/dekat) dengan
paralaks berbeda, 5 bintang terang berwarna (oranye Betelgeuse / biru Rigel) dengan glint, pita Bima Sakti samar (derau
numpy + pita Gaussian + celah gelap, ter-cache); `komet` punya **ekor ion kebiruan lurus** di belakang ekor debu hangat;
`garis_meteor(train=True)` = **jejak persisten** memudar 0,37 s (ciri Orionid 66 km/s) dipakai `meteor_acak`;
`pijar_cakrawala` = pijar hangat memudar ke atas dari garis cakrawala (nol di tepi, bukan kotak); micro-climax: kilat
langit 0,16 s + riak ganda (3 cincin, tunda 0/0,14/0,30 s) + butir sungai debu berdenyut. Grain diturunkan `KT_GRAIN=2.4`
(lebih bersih setelah re-encode YouTube). Sweep 0,25 s SS 0,5 bersih; frame batas diperiksa.

**Batas alat:** `generate_speech` maksimal 10 klip per giliran -> untuk 7 klip + uji format, sisa klip dibuat di giliran
berikutnya. Simpan WAV sumber ke Drive (zip) segera setelah dibuat (sandbox bisa reset).

**Keamanan akun GitHub (diterapkan 15 Okt malam):** workflow `selftest.yml` kini **hanya `workflow_dispatch`** (tidak ada
pemicu push/PR -> 0 menit Actions otomatis); semua commit beridentitas pemilik (`chronoidchannel-stack@users.noreply.github.com`),
satu commit per sesi dengan `[skip ci]`, tidak ada biner/audio/video/rahasia di repo (`.gitignore` `episodes/*/audio_raw/*`),
hasil produksi hanya di Google Drive. Disarankan repo dijadikan **private** (Settings -> Danger zone) - perlu pemilik.
Token PAT: scope minimal `repo` (contents), masa berlaku pendek, kirim lewat file `token.txt` di workspace, dihapus setelah
dipakai, dan **dicabut** di GitHub setelah sesi.

**RUNBOOK lanjutan Ep50 v2 (giliran berikutnya, urut):**
1. Pulihkan sandbox bila reset: `git clone` repo -> unduh bundle Drive (Project_Docs) -> `git fetch <bundle> main:ep50v2 &&
   git reset --hard ep50v2` -> `pip install -r requirements.txt faster-whisper` -> unduh `Ep50_VO_v2_wav_bagian1.zip`
   (Drive/Shorts/Ep50) ke `episodes/ep50_orionid/audio_raw/`.
2. `generate_speech` voice-00 **format .wav** untuk `f1, f2, f3, outro` dengan teks PERSIS `content.json` `vo` -> taruh di
   `audio_raw/` -> zip `Ep50_VO_v2_wav_bagian2.zip` ke Drive.
3. `tools/render_lokal.sh shorts ep50_orionid prep` (vo_manusia --asr harus "SEMUA BERSIH", build_audio "AUDIO OK",
   master v12 OK, check_layout bersih).
4. Spot-check frame batas +-0,08 s + sweep 0,25 s SS 0,5 (lihat §16) -> `start_process` render penuh (~80-90 menit;
   poll `build/render.log`, sleep <= 600 s) -> `qc_mp4.py`, `qc_loop.py` (>= 0,98), lembar frame akhir.
5. Thumbnail dari frame render (`render.py --times`) -> Drive; mp4 (< 100 MB) + m4a master + SIAP_TEMPEL ke Drive
   `Shorts/Ep50_Orionid/` (nama `_v2`), salinan thumbnail/metadata ke folder Thumbnails/Metadata; v1 dipindah ke
   subfolder `arsip_v1`.
6. Commit `[skip ci]` (identitas pemilik) + bundle baru ke Drive; push hanya bila `token.txt` tersedia; ingatkan cabut token.

**Pelajaran render v2 (15 Okt malam):** (a) `diagrams.paste_c/paste_r` **mengabaikan alpha** sejak awal proyek -> semua
label teks polos "pop" alih-alih memudar (termasuk saat KELUAR). Diperbaiki: alpha kini diterapkan ke kanal A. Episode
lama tidak perlu dirender ulang. (b) Elemen yang sengaja persisten melintasi batas adegan (stiker "TULIS KOTAMU" f5 ->
outro) harus digambar dengan primitif mentah (`V._stiker11`) tanpa faktor KELUAR, kalau tidak ia memudar lalu muncul
lagi (kedip). (c) Durasi v2 123,7 s -> VBITRATE 5900k agar mp4 < 100 MB (batas `upload_file`); di atas itu perlu
`initiate_resumable_upload`. (d) Semua 62 CUE kata terselesaikan dari `kata.json` (periksa dengan skrip kecil: tidak boleh
ada fallback fraksi sebelum render).
(e) `qc_mp4.py` kini sadar v12 (`KT_VO_CHAIN=v12`): kepala VO boleh sampai lead_in + 0,12 + 0,55 s (napas alami
dipertahankan, kata pertama diverifikasi ASR) dan rentang aktif dibanding naskah - 0,47 s (pra/pasca-gulir ruangan
-63 dBFS tidak terdeteksi ambang -40 dB). Tanpa ini render v12 selalu "PERIKSA" palsu dan `render_lokal.sh` keluar 1
meski mp4 sudah ada di `dist/`. **Ep50 v2 FINAL 15 Okt 17.00 UTC:** 123,75 s, 94,4 MB (6104 kb/s), korelasi audio
0,9999, peak -2,0 dBFS, loop 0,988, QC SEMUA BERSIH; Drive `KlikTahu_Ep50_Orionid_v2.mp4` + `_master.m4a` +
`Ep50_SIAP_TEMPEL_v2.md`; v1 dipindah ke `Ep50_Orionid/arsip_v1/`.
