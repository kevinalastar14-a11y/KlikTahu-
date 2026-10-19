# STANDAR PRODUKSI v12 "KONTINUITAS" - KlikTahu Shorts

Berlaku mulai Ep50 (15 Okt 2026). Menggantikan bagian gaya di `docs/` v11 untuk Shorts; aturan teknis v11 (resolusi, safe zone, pipeline) tetap berlaku kecuali yang diubah di sini. Ditulis oleh agen Arena atas brief pemilik kanal, lalu dilengkapi.

---

## 0. Urutan prioritas (dikoreksi dan dilengkapi)

Brief pemilik: kejelasan -> storytelling -> imersi -> kualitas sinematik -> retensi -> kecanggihan visual.

Koreksi: **retensi bukan lapisan terpisah, ia adalah hasil terukur dari lapisan 1-5**, jadi tidak bisa diletakkan di urutan ke-5; ia harus dirancang sejak naskah (hook, celah rasa ingin tahu, tanpa udara kosong, loop). **Audio** juga hilang dari daftar prioritas, padahal VO yang terpotong/tidak jelas adalah kegagalan paling fatal (penonton tidak paham = swipe). Urutan yang dipakai:

| Prio | Lapisan | Artinya dalam praktik | Diukur dengan |
|---:|---|---|---|
| 1 | **Kejelasan** | 1 ide per adegan, maks 7 kata di layar, terbaca di HP 6 inci, VO jelas | QC layout, uji baca 1 detik |
| 2 | **Cerita & tempo (= rekayasa retensi)** | hook <= 1 s, celah rasa ingin tahu, 5 babak berurutan, tidak ada udara kosong > 0,4 s, micro-climax, loop | swipe-away, persen ditonton, loop rate |
| 3 | **Audio** | VO dulu, SFX tersinkron per BEAT, tekstur ambient halus, -14 LUFS, true peak -1 dBTP, VO tidak pernah tertutup | QC audio otomatis |
| 4 | **Imersi & kontinuitas** | satu sistem visual, morph semantik, match cut, penutup loop | hitung potongan "keras" (target 0) |
| 5 | **Kualitas sinematik** | komposisi, kedalaman/parallax, kamera terkendali, easing dengan antisipasi | tinjauan visual |
| 6 | **Kecanggihan visual** | hanya jika melayani 1-5 | - |

Aturan emas: jika dua lapisan bertabrakan, lapisan bernomor lebih kecil menang. Contoh: morph yang indah tetapi membuat teks tak terbaca 0,5 s -> morph dipotong.

---

## 1. Struktur wajib 5 babak (urutan tidak boleh ditukar)

Anggaran waktu untuk Short 100-120 s (skala proporsional untuk 50-60 s):

| Babak | Durasi | Tujuan | Energi kamera | Aturan khusus |
|---|---:|---|---:|---|
| **1. The Hook** | 0-2,5 s | pertanyaan/klaim yang membuat tidak jadi swipe | 0,6 | kata kunci tampil di layar pada frame 0; VO mulai <= 0,3 s; frame 0 = thumbnail = frame akhir |
| **2. The Agitation / Problem** | 2,5-15 s | "ini menyangkut kamu": taruhan pribadi, bukan definisi | 0,5 | sebut penonton ("rumahmu", "kamu"), tunjukkan akibat dulu, sebab belakangan |
| **3. The Body / Value** | 15-80 s | 3 potong nilai, disingkap bertahap (progressive disclosure) | 0,4 -> 0,7 | satu elemen baru per >= 1,5 s; elemen lama berubah menjadi elemen baru (morph), tidak diganti |
| **4. The Micro-Climax** | 80-100 s | payoff: elemen-elemen babak 3 digabung jadi satu gambar yang menjelaskan semuanya | 1,0 | kesunyian strategis 0,8-1,2 s sebelum payoff, lalu thump rendah + reveal; pertanyaan pemicu komentar |
| **5. Seamless Outro / Loop** | 100-115 s | kalimat penutup yang menyambung ke kalimat pembuka; visual kembali ke frame 0 | 0,3 | tidak ada "subscribe/like" yang memutus; frame terakhir == frame pertama (piksel & fase kamera) |

Kesunyian strategis: setelah setiap reveal besar, kamera diam 0,6-1,0 s, VO jeda <= 0,4 s. Eskalasi terkendali: energi kamera naik monoton dari babak 3 ke 4, lalu turun di babak 5.

---

## 2. Aturan naskah (storytelling + beban kognitif)

1. Panjang VO 190-240 kata untuk 100-120 s (1,8-1,9 kata/detik setelah SPEED 1,09).
2. Kalimat <= 14 kata. Satu kalimat = satu gambar.
3. Hook ditulis terakhir, diuji: "kalau ini kalimat pertama, apakah aku berhenti scroll?".
4. Setiap babak diakhiri "umpan" (kalimat yang membuka pertanyaan berikutnya) -> celah rasa ingin tahu berantai.
5. Micro-climax harus berupa **hubungan** antar elemen ("telur Agustus + hujan Oktober + tikus = rumahmu"), bukan fakta baru.
6. Kalimat penutup harus **bisa disambung ke kalimat pembuka** tanpa terasa putus (loop audio): kata terakhir mengarah ke subjek kalimat pertama.
7. Angka maksimal 3 per video; selalu divisualkan (odometer/skala), tidak hanya diucapkan.
8. Fakta wajib punya sumber (ditulis di `METADATA.md` bagian Sumber). Tidak ada klaim medis/keselamatan tanpa lembaga (BRIN, BMKG, WHO, Kemenkes).
9. Kata yang disorot (`hl`) = kata yang sedang diucapkan (sinkron tingkat kata, bukan tebakan fraksi).

---

## 3. Sistem visual: satu dunia, bukan kumpulan adegan

- **Satu latar hidup** (mesh gradient) berjalan terus sepanjang video; fase latar di frame akhir sama dengan frame 0 (durasi total dibulatkan ke kelipatan periode mesh).
- **Elemen fokus bertahan**: setiap adegan baru lahir dari elemen adegan sebelumnya (morph bentuk, atau match cut: posisi & skala elemen keluar = posisi & skala elemen masuk).
- **3 lapis kedalaman**: latar (parallax 0,3x), konten (1,0x), partikel/tekstur depan (1,4x). Gerak kamera kecil (drift <= 12 px/s, punch <= 4%).
- **Transisi punya logika**:
  - `morph` - elemen A berubah jadi B (sebab -> akibat, benda -> diagram).
  - `match` - potongan tanpa wipe, elemen di posisi sama (waktu lompat, tempat berbeda).
  - `tinta`/`cahaya` - pergantian konteks besar (dunia luar -> dalam tubuh); maks 2 per video.
  - `zoomthru` - masuk ke dalam detail; maks 1 per video.
  - `punch`/`glitch` - dilarang kecuali untuk hook (maks 1).
  - Dilarang: zoom berulang, bounce > 1 overshoot, transisi acak/generik, wipe tanpa alasan.
- **Easing**: antisipasi (mundur 6-8% selama 100-140 ms) -> akselerasi -> deselerasi (quintic) -> overshoot <= 8% -> settle. Elemen anak mengikuti elemen induk dengan lag 60-90 ms (secondary motion).
- **Tipografi kinetik**: kata muncul saat diucapkan; kata sorot lebih besar 15% + warna aksen; maks 2 baris, 7 kata; tidak ada teks di y > 1640 atau kolom tombol kanan (x > 950, y 1100-1700).
- **Hierarki**: satu titik fokus per saat; fokus berikutnya muncul <= 25% lebar layar dari fokus sebelumnya, atau dipandu garis/partikel (panduan perhatian).
- **Metafora visual** ditetapkan di naskah per episode (contoh Ep51 ular: tetes hujan -> telur -> kepala ular; contoh Ep50 Orionid: kalender -> jam -> kompas, langit -> peta orbit -> langit).
- **Tanpa animasi dekoratif**: tiap gerakan wajib menjawab "apa fungsinya?" (memandu mata, menunjukkan sebab-akibat, menandai waktu, menegaskan kata). Jika tidak ada jawaban, hapus.

---

## 4. Desain suara (tanpa musik apa pun)

Prioritas: **VO -> SFX sinematik -> tekstur ambient halus**. Tidak ada BGM, instrumen, melodi, drone musikal.

| Lapisan | Level | Aturan |
|---|---:|---|
| VO | -16 LUFS per klip; puncak -2 dBTP | TTS voice-00 **sumber .wav (PCM)**, rantai `vo_manusia.py`: tanpa atempo, tanpa hening sisipan, pra-gulir 120 ms / pasca 350 ms, nada ruang -63 dBFS; QC ASR kata pertama & terakhir |
| SFX | -16 dB dasar, duck -7 dB di bawah VO | satu SFX per BEAT: transisi, reveal, impact, gerak, penekanan kata; jenis mengikuti arah & materi gerak |
| Ambient | -30 s.d. -34 dB | tekstur halus sesuai dunia episode (hujan ringan, angin, ruang); fade 20 ms zero-crossing di awal & akhir agar loop tanpa klik |
| Master | -14 LUFS integrated, true peak -1 dBTP | `master_audio.py`; tidak ada clipping |

Katalog SFX v12 (semua disintesis di `sfx.py`, tanpa unduhan berlisensi): whoosh kiri/kanan/atas/bawah (arah = arah gerak), reveal shimmer, morph slide (noise sweep + glide sinus), type tick (sangat halus, untuk kata), thump rendah 60-80 Hz (micro-climax), riser halus 2-3 s (eskalasi, hanya 1 per video), tetes air, retak (telur/es), desir hujan, angin, room tone. SFX yang bersifat "musik" (nada berulang, akor) dilarang.

Sinkron: BEAT dikunci ke **kata** (hasil `align()`), bukan ke fraksi adegan. Toleransi sinkron +- 40 ms.

Format audio: TTS **diminta sebagai .wav PCM** (sumber lebar pita penuh; `.mp3` dari TTS hanya 32 kb/s dan terdengar terpotong), diproses sebagai WAV 48 kHz **hanya sebagai perantara internal** di pipeline. Deliverable audio di Drive = **.m4a (AAC 256k)**. **Tidak pernah mengirim WAV ke pemilik.**

---

## 5. Loop tanpa sambungan (Seamless Outro)

1. Visual: adegan outro merender ulang state frame 0 (posisi elemen, fase mesh, fase kamera) pada 0,6 s terakhir; perpindahan dari micro-climax ke state itu memakai morph, bukan fade.
2. Audio: ambient di 0,3 s terakhir == ambient 0,3 s pertama; tidak ada SFX yang melewati batas akhir; VO penutup selesai >= 0,25 s sebelum akhir; VO pembuka mulai 0,25-0,3 s setelah frame 0 -> jeda loop terasa 0,5 s (alami).
3. Naskah: kalimat terakhir menyerahkan ke kalimat pertama (lihat §2.6).
4. QC: `qc_mp4.py --loop` membandingkan frame terakhir vs frame 0 (korelasi >= 0,98) dan RMS audio 300 ms awal vs akhir (selisih <= 2 dB).

---

## 6. Gerbang QC (wajib lulus sebelum unggah)

| Gerbang | Alat | Lulus jika |
|---|---|---|
| Layout | `check_layout.py` | 0 teks di zona terlarang; <= 7 kata per layar |
| Beban kognitif | `check_layout.py --beban` (baru) | <= 1 elemen baru per 1,5 s di babak 3 |
| Audio | `qc_audio.py` (baru, pisahan dari master) | -14 LUFS +-0,5; TP <= -1; VO utuh; SFX count == BEAT count |
| Sinkron | `qc_sync.py` (baru) | selisih onset SFX vs BEAT <= 40 ms |
| Video | `qc_mp4.py` | korelasi chunk >= 0,97; durasi == timeline; 60 fps konstan |
| Loop | `qc_mp4.py --loop` | §5.4 |
| Mata manusia | tonton di HP 1x tanpa suara + 1x dengan suara | paham tanpa suara? tidak ada momen "nganggur"? |
| Frame 0 | ekspor `thumb.jpg` dari frame 0 | kata kunci judul terbaca di ukuran 1/4 layar |

---

## 7. Metadata & unggah

- Judul <= 60 karakter, **tidak diawali "Kenapa"** (data kanal: 59,5 vs 41,7 views/hari), mengandung taruhan atau peristiwa + kata kunci pencarian.
- Baris pertama deskripsi = kalimat kata kunci; baris kedua = pertanyaan pemicu komentar; sumber di baris akhir.
- Hashtag 3-5 (#Shorts + 2-4 kata kunci), tag <= 15.
- Thumbnail = frame 0 (konsisten dengan hook).
- Jam unggah 11.30-12.30 atau 18.30-20.30 WIB; balas komentar pertama dalam 60 menit.
- Pantau di Studio pada 1 jam, 24 jam, 7 hari: swipe-away, persen ditonton, loop, suka, share (target di `analisis/LAPORAN_15_OKT_2026.md` §4).

---

## 8. Tambahan mesin yang diperlukan (spesifikasi v12 untuk `mesin_fx.py` / `mesin_v11.py` -> `mesin_v12.py`)

| Fitur | Implementasi | Dipakai untuk |
|---|---|---|
| `morph(a, b, t)` | interpolasi titik poligon (resample N=256 titik, pasangkan berdasar sudut) + crossfade alpha untuk bentuk kompleks | transformasi semantik antar adegan |
| `anchor_out` / `anchor_in` di `content.json` | render.py meneruskan posisi & skala elemen fokus keluar ke adegan masuk; transisi `match` | match cut tanpa wipe |
| `depth` per elemen | multiplier parallax 0,3 / 1,0 / 1,4 terhadap drift kamera | kedalaman nyata |
| `ease_v12(t, antisipasi=0.07, overshoot=0.06)` + `follow(t, lag_ms)` | kurva quintic dengan antisipasi & settle; anak elemen lag | gerak hidup, bukan bounce |
| `BEATS` tingkat kata | port `align()` dari mesin Long ke Shorts; BEAT = `("kata", jenis)` selain `(fraksi, jenis)` | sinkron AV tepat |
| `energi` per babak | skala drift/punch/partikel dari tabel §1 | eskalasi terkendali |
| `hold` per adegan | kamera diam N detik setelah reveal | kesunyian strategis |
| `sc_outro_loop` | merender state frame 0 di akhir; durasi total = kelipatan periode mesh | loop mulus |
| SFX v12 | tambahan katalog §4 di `sfx.py`; ambient generator (hujan/angin/ruang) | suara per BEAT + tekstur |
| QC baru | `qc_audio.py`, `qc_sync.py`, `check_layout.py --beban`, `qc_mp4.py --loop` | gerbang §6 |

Semua tambahan disertai `--uji` (selftest) sesuai aturan repo; tidak ada render di GitHub Actions.

---

## 9. Yang ditambahkan dibanding brief pemilik (agar rencana lengkap)

1. Zona aman UI Shorts (teks tidak tertutup tombol/judul).
2. Akurasi fakta + sumber lembaga per episode.
3. Frame 0 = thumbnail = frame akhir (koherensi hook-judul-loop).
4. Loop **audio**, bukan hanya visual (level ambient, jeda VO, kalimat sambung).
5. Pertanyaan pemicu komentar di micro-climax/outro (sinyal komentar dalam jendela uji).
6. Kata kunci di layar karena 85% penonton awal tanpa suara (tanpa subtitle penuh; kinetik 7 kata).
7. Gerbang QC otomatis yang bisa diulang, bukan penilaian rasa.
8. Judul tidak diawali "Kenapa" (bukti data kanal sendiri).
9. Durasi rekomendasi 90-120 s untuk uji format loop (aturan durasi bebas <= 178 s tetap berlaku).
10. Target angka retensi per video dan aturan keputusan (lanjut seri / perbaiki hook).

### Tambahan 15 Okt 2026 (malam) - hasil remake Ep50 v2
- Napas alami sebelum kalimat pertama **dipertahankan** (0,1-0,5 s setelah pra-gulir). Jangan dipangkas: inilah yang
  membuat VO terdengar manusiawi; QC keutuhan kata = ASR (`build/vo_qc.json`), bukan ambang energi.
- Setiap label teks harus memudar bersama elemen induknya (alpha `paste_c/paste_r` kini berfungsi); elemen yang
  memang persisten lintas adegan digambar tanpa faktor KELUAR.
- Sebelum render penuh: (1) semua CUE terselesaikan dari `kata.json`; (2) lembar batas +-0,08 s di 6 batas;
  (3) sapuan 1/3 s SS 0,5 tanpa error; (4) proyeksi ukuran = bitrate x durasi < 100 MB.
