# LAPORAN ANALISIS MENDALAM - KlikTahu, 15 Oktober 2026

Dibuat oleh agen Arena (sesi 15 Okt 2026). Sumber: (1) data publik kanal @KlikTahu (36 Shorts, diambil 15 Okt 2026), (2) mesin analisis repo dijalankan LIVE hari ini (`sapuan_mendalam.py` -> `pemeta_peluang.py` -> `mesin_v5.py` -> `mesin_v6.py`; 2.302 frasa autocomplete, 573 permintaan live, Wikipedia pageviews, pesaing YouTube), (3) riset web (BMKG, BRIN, kalender astronomi, perilaku algoritma Shorts 2026).

---

## 1. Kondisi kanal hari ini (fakta, bukan perkiraan)

| Ukuran | Nilai |
|---|---|
| Subscriber | 88 |
| Shorts tayang | 36 (14 Sep - 1 Okt 2026) |
| Video panjang | 0 terlihat |
| Total views | 40.678 |
| Rata-rata per video | 1.130 views |
| Video terbaik | Supermoon 2026: 3.243 views (129,7 views/hari) |
| Video terburuk | Hujan Meteor 21-22 Okt (diunggah 14 Sep): 210 views |

**Pola paling penting:** hampir semua video berhenti di sekitar 1.000 views. Itu tanda khas Shorts 2026: setiap video dapat "uji penonton awal" (~1 rb tayangan), lalu algoritma memutuskan diperluas atau tidak berdasarkan **swipe-away 2 detik pertama**, **persentase ditonton (target >= 70%)**, **tonton ulang/loop**, dan **share/like**. Kanal ini lolos ke uji awal tetapi hampir selalu gagal di tahap perluasan. Artinya: **masalah utamanya bukan topik saja, tetapi retensi & kepuasan di 2 detik pertama dan di tengah video**. Standar produksi baru (v12) dibuat untuk menyerang titik ini.

Catatan: video Drive 7-13 Okt (nyamuk, petir v1-v3, 3-detik-pertama) **tidak terlihat** di @KlikTahu publik. Mungkin diunggah ke kanal lain / private / unlisted. Perlu dipastikan pemilik kanal.

### 1a. Peringkat performa (views/hari, 15 Okt 2026)

| # | Video | Views | Views/hari | Durasi | Suka |
|---:|---|---:|---:|---:|---:|
| 1 | Supermoon 2026 (24 Nov & 24 Des) | 3.243 | 129,7 | 140 s | 22 |
| 2 | Mesin Pesawat Mati di Udara | 1.378 | 91,9 | 119 s | 33 |
| 3 | Es Batu Mencair, Air Tumpah? | 1.290 | 86,0 | 113 s | 27 |
| 4 | Bulan Purnama 26 Sep | 2.741 | 85,7 | 46 s | 21 |
| 5 | Ular Menjulurkan Lidah | 1.195 | 74,7 | 163 s | 3 |
| 6 | Venus Paling Terang | 1.157 | 68,1 | 115 s | 22 |
| 7 | Bulan Berwarna Merah | 1.899 | 67,8 | 89 s | 10 |
| 8 | Jembatan Gantung Bergoyang | 1.219 | 64,2 | - | - |
| 9 | Matahari Diganti Black Hole | 1.125 | 62,5 | - | - |
| 10 | Megalodon Punah | 1.328 | 60,4 | - | - |
| ... | 26 video lain di 14-51 views/hari | | | | |
| 36 | Hujan Meteor 21-22 Okt (terbit 14 Sep) | 210 | 6,6 | 44 s | - |

### 1b. Temuan dari data kanal sendiri

1. **Peristiwa langit bertanggal = 2-3x views** (Supermoon, Bulan Purnama 26 Sep, Bulan Merah). Penonton mencari "jam berapa & cara lihatnya". Syarat: terbit 2-3 hari sebelum peristiwa, bukan 5 minggu sebelumnya (kasus Hujan Meteor 14 Sep = gagal total).
2. **Fisika sehari-hari yang melawan intuisi + ada taruhannya** (mesin pesawat mati, es batu tumpah, jembatan bergoyang) = kluster evergreen terbaik. Pola: benda yang dikenal semua orang + "padahal kamu kira sebaliknya".
3. **Judul yang TIDAK diawali "Kenapa"** rata-rata 59,5 views/hari vs 41,7 untuk judul "Kenapa ...". Judul harus dibuka dengan taruhan/peristiwa/klaim, bukan rumus pertanyaan buku teks.
4. **Pertanyaan buku teks generik** (kenapa hujan turun, perut bunyi, baterai boros, dinosaurus punah) = performa terburuk (14-17 views/hari).
5. **Per pilar** (views/hari | rata suka%): LANGIT 56,3 | 1,31% ; TEKNOLOGI 53,9 | 1,67% ; HEWAN 48,3 | 1,23% ; BUMI & CUACA 41,5 | 1,07% ; TUBUH 34,7 | **2,34%**. Tubuh paling memuaskan (suka tinggi: Mimpi Lupa 3,5%, Kesemutan 2,3%) tetapi jangkauannya paling kecil -> cocok untuk membangun subscriber, bukan untuk views.
6. **Durasi bukan penentu**: >= 110 s rata-rata 51 views/hari, < 60 s 40 views/hari. Durasi 90-120 s aman selama tidak ada "udara kosong".
7. Suka sangat rendah pada "Ular Menjulurkan Lidah" (3 dari 1.195) -> eksekusi videonya tidak memuaskan, bukan topiknya; topik ular tetap kuat di data permintaan.

---

## 2. Hasil mesin analisis LIVE (15 Okt 2026)

### 2a. Papan v6 (permintaan + Wikipedia + celah pesaing + visual + pilar + momen)

| # | Tema | Pilar | skor_v6 | Celah pesaing | Median views pesaing | Catatan |
|---:|---|---|---:|---:|---:|---|
| 1 | serangga | HEWAN | 42,2 | 0,25 | 174 | permintaan ada, tapi pesaing kecil = bukti views lemah |
| 2 | **ular & reptil** | HEWAN | 39,6 | **0,59** | **157 rb** | permintaan + bukti views + celah = terbaik |
| 3 | **piramida & mesir** | MISTERI | 36,7 | 0,62 | 223 rb | evergreen kuat, belum pernah dibuat |
| 4 | burung terbang | HEWAN | 34,8 | 0,25 | 969 | lemah |
| 5 | anjing | HEWAN | 34,7 | 0,33 | 3 rb | sudut "najis" sensitif, hindari |
| 6 | lubang hitam | LANGIT | 33,5 | 0,66 | 403 rb | kanal sudah 3x; simpan untuk sudut baru |
| 7 | es & salju | BUMI | 33,3 | 0,25 | 190 | lemah |
| 8 | tekanan darah | TUBUH | 32,8 | 0,47 | 24 rb | praktis, cocok subscriber |
| 9 | pelangi | BUMI | 32,6 | 0,35 | 4 rb | visual bagus, permintaan sedang |
| 10 | cegukan | TUBUH | 32,0 | 0,49 | 34 rb | PRIBADI 13 frasa |

Sekuel yang permintaannya masih naik (velocity): baterai & hp +17,0 ; kucing +14,9 ; perut +14,8 ; hujan & awan +13,6 (momen puncak musim hujan) ; mata +12,6 ; meteor & komet +19,5 (momen Orionid 21-22 Okt).

Segar (belum pernah dibuat) versi v5: menangis & emosi 171 ; es & salju 150 ; piramida 125. Versi pemeta v4: demam & imun 429 ; hujan & awan 408 ; pusing & migrain 319 ; mimisan 299 ; kulit 290.

### 2b. Momentum eksternal (riset web 15 Okt 2026)

- **BMKG**: kemarau berakhir pertengahan Oktober; musim hujan masuk bertahap mulai Oktober (barat dulu), merata November termasuk sebagian besar Jawa; bersamaan El Nino yang bertahan sampai awal 2027 (puncak Des 2026).
- **BRIN (Amir Hamidy)**: telur ular menetas di musim hujan (Nov-Des-Jan), diletakkan 3-4 bulan sebelumnya; anak ular menyusuri tepi/celah; mangsa (tikus, katak, cicak) ramai saat hujan; ular suka tempat gelap-lembap (plafon, pot, WC). Pencegahan: rumah bersih -> tidak ada tikus -> tidak ada ular. -> **dasar ilmiah kuat untuk Ep50**.
- **Kalender langit**: Orionid puncak 21-22 Okt ; Leonid 16-17 Nov ; Geminid 4-17 Des, puncak 14 Des (~150/jam, terbaik setahun) ; Supermoon terakhir 2026: 24 Nov & 23/24 Des (verifikasi tanggal pasti H-5 sebelum produksi). Tidak ada gerhana tersisa di 2026.
- **Algoritma Shorts 2026** (ringkas): uji 30-60 menit ke penonton awal ; sinyal utama = Viewed vs Swiped Away (target swipe < 30-40%), rata-rata persen ditonton >= 70% (85%+ = breakout), loop > 100%, share > 1%, suka > 3% ; udara kosong > 0,3-0,5 s menaikkan swipe ; sebagian besar ditonton awalnya tanpa suara -> kata kunci harus tampil di layar.

---

## 3. Keputusan: peringkat topik berpotensi views besar HARI INI

Skor gabungan = permintaan (v5/v6) x bukti views pesaing x kecocokan pilar kanal x momen waktu x kecocokan format "taruhan + padahal".

| Prio | Episode | Topik | Kenapa sekarang | Format | Jadwal terbit |
|---:|---|---|---|---|---|
| 1 | **Ep50** | **Ular masuk rumah saat musim hujan** | musim hujan mulai minggu ini; menetas Nov-Jan; permintaan + bukti views 157 rb + celah 0,59; PRAKTIS (disimpan/dibagikan) + BAHAYA (taruhan) | 100-120 s, struktur 5 babak v12, loop hujan | 17-18 Okt |
| 2 | Ep51 | Orionid 21-22 Okt: jam, arah, tanpa teleskop | peristiwa bertanggal = pola views terbaik kanal; video lama gagal hanya karena 5 minggu terlalu awal | 50-60 s cepat, pakai aset Ep39 | 19-20 Okt (maks 20 Okt) |
| 3 | Ep52 | Piramida bukan dibangun budak (bukti desa pekerja & papirus Merer) | v6 #3, 223 rb median, celah 0,62, pilar MISTERI kosong | 110-130 s | 24-25 Okt |
| 4 | Ep53 | Semut tiba-tiba muncul banyak sebelum hujan? | serangga #1 v6 + musiman + PRIBADI ("ini aku banget") + fisika sehari-hari | 90-100 s | 28-29 Okt |
| 5 | Ep54 | Hujan bikin ngantuk - otakmu yang diatur suara hujan | hujan & awan velocity +13,6, momen puncak musim hujan, PRIBADI | 90 s | 1-2 Nov |
| 6 | Ep55 | Habis nangis mata bengkak & kepala pusing - tubuh sedang melakukan ini | menangis & emosi = segar #1 (171), suka% tinggi di pilar TUBUH | 90 s | 5-6 Nov |
| 7 | Ep56 | Leonid 16-17 Nov (jam, arah) lalu Supermoon 24 Nov | peristiwa bertanggal | 50-60 s masing-masing | 13-14 Nov & 20-21 Nov |

Cadangan kuat: cegukan (PRIBADI 13 frasa), tekanan darah (praktis), lubang hitam sudut baru ("kalau Matahari jadi lubang hitam, Bumi tidak tersedot" sudah; sudut baru: "kenapa lubang hitam bisa terlihat padahal hitam" sudah -> cari sudut ke-4: "suara lubang hitam NASA"), kucing sekuel ("kenapa macan takut kucing" - viral folk), baterai HP sekuel ("kenapa baterai boros di HP Oppo/Vivo" - sangat dicari, tapi pilar TEKNOLOGI indeks rendah).

Hindari: anjing "najis" (sensitif), topik terblokir (kentut, ngiler, keringat), sudut "7 fakta" (sudah dipakai pesaing).

### 3a. Judul untuk Ep50 (pilih satu; tidak diawali "Kenapa")

1. **Ular Masuk Rumah Saat Musim Hujan? Bukan Karena Banjir** (utama)
2. Musim Hujan Datang, Ular Mulai Masuk Rumah. Ini Alasannya
3. Rumahmu Dipilih Ular Bulan Depan? Cek 3 Tanda Ini

Kata di layar 2 detik pertama: "ULAR MASUK RUMAH" + "bukan karena banjir". Frame pertama = thumbnail = frame terakhir (loop).

### 3b. Jam unggah

11.30-12.30 WIB atau 18.30-20.30 WIB (penonton Indonesia aktif), balas komentar pertama dalam 60 menit pertama (jendela uji algoritma).

---

## 4. Ukuran keberhasilan yang dipantau per video (dari YouTube Studio)

| Sinyal | Target Ep50+ | Alasan |
|---|---|---|
| Viewed vs Swiped Away | swipe <= 35% | lolos uji 2 detik |
| Rata-rata persen ditonton | >= 70% | syarat perluasan |
| Loop (ditonton ulang) | >= 100% | outro mulus -> ulang |
| Suka | >= 2% | kepuasan |
| Share | >= 1% | nilai praktis |
| Komentar | >= 5 per 1.000 views | pertanyaan pemicu di micro-climax |

Jika Ep50 tembus >= 5.000 views dalam 7 hari: lanjutkan seri "musim hujan" (Ep53, Ep54). Jika tidak: periksa swipe-away dulu (hook) sebelum mengganti topik.

---

_Berkas pendukung: `analisis/STRATEGI_V6.md`, `analisis/HASIL_V5.md`, `analisis/PEMETA_PELUANG.md`, `analisis/HASIL_MENDALAM.md`, `analisis/performa.csv` (data real), `docs/STANDAR_PRODUKSI_V12.md` (standar produksi baru)._
