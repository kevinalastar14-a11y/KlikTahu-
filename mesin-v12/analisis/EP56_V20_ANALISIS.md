# ANALISIS EP56 — "Kamu Merasa Jatuh Tepat Sebelum Tidur" (v20)

Dokumen ini menjelaskan **kenapa** episode ini dibuat seperti ini: pilihan topik,
desain retensi per detik, alasan teknis tiap keputusan visual/audio, dan rencana
uji agar peluang views-nya terukur — bukan tebakan.

---

## 1. Metode & batas yang jujur

| Yang diminta | Yang bisa dilakukan | Status |
|---|---|---|
| Meniru video Drive `1Mkz5HjQNlqiisEbFDhOfB8eblCEnbp64` 100% | Video Drive **tidak bisa diunduh** dari sandbox ini (daftar host keluar hanya GitHub/PyPI/npm; `drive.google.com` diblokir) | **tidak dikerjakan** |
| Menganalisis gaya video lama kanal | Repo ini sudah menyimpan hasil analisis frame-per-frame video panjang kanal (`docs/MESIN_V19.md`): latar gelap bergradasi, merek kiri atas + badge babak kanan atas, progres segmen bawah, panel kaca bergrafik, garis pandu, pill caption, figur manusia sebagai skala | dipakai sebagai acuan |
| "Lebih cepat dapat banyak views" | Riset algoritma Shorts 2026 (lihat §3) + data riset internal kanal (`analisis/PEMETA_PELUANG.md`) | dikerjakan |

Karena video acuan tidak bisa ditonton, **tidak ada klaim "100% mirip"**. Yang
dilakukan: memakai bahasa visual KlikTahu yang sudah terdokumentasi di repo
(v19) dan menaikkannya (v20), lalu memilih topik dari data kanal sendiri.

> Kalau pemilik mengunggah video acuan ke GitHub (repo privat) atau memberi
> tautan yang bisa diunduh, saya bisa mengukur ulang: durasi per babak, tempo
> potongan, palet (histogram), ukuran tipografi, dan posisi HUD — lalu
> menyamakan parameternya secara terukur.

---

## 2. Pemilihan topik (dari data kanal, bukan selera)

Sumber: `mesin-v12/analisis/PEMETA_PELUANG.md` (55 keluarga topik, 278 cabang)
dan `peringkat_topik.json`.

| # | Keluarga | skor_views | Status di kanal |
|---:|---|---:|---|
| 1 | mimpi & tidur | **540,8** | Ep21 + Ep25 (mimpi cepat lupa) |
| 2 | kucing | 494,0 | Ep23 |
| 3 | perut & pencernaan | 468,4 | Ep28 |
| 4 | demam & imun | 429,0 | SEGAR |
| 5 | mata | 424,4 | Ep31 |

Keluarga **mimpi & tidur** adalah peringkat 1 dan baru dipakai untuk "kenapa mimpi
cepat lupa" (Ep25). Turunannya yang belum dibuat dan punya permintaan pencarian
tinggi: *badan nyentak saat tidur*, *merasa jatuh sebelum tidur*.

Empat alasan memilih **hypnic jerk**:

1. **Universal & personal.** 60–70% orang mengalaminya (Sleep Medicine 2016);
   penonton langsung merasa "ini saya". Itu bahan bakar komentar.
2. **Payoff cepat.** Jawabannya bisa diberikan di 8 detik pertama
   ("bukan mimpi, namanya hypnic jerk") → hook + nilai sekaligus.
3. **Aman.** Bukan penyakit, bukan diagnosis, tidak menakut-nakuti → tidak
   kena pembatasan "medical misinformation". Video tetap memberi rujukan.
4. **Visualnya bisa digambar tanpa stock.** Kamar malam, jam, otak, dahan,
   figur jatuh — semuanya bisa dibuat mesin sendiri (tidak ada risiko hak cipta
   footage, yang bisa memblokir Shorts > 1 menit).

Topik yang **dihindari** (sudah diblokir pemilik di data riset): kentut, ngiler,
keringat & bau badan.

---

## 3. Apa yang dinilai algoritma Shorts (2026) — dan bagaimana video ini menjawabnya

Ringkasan dari sumber publik terbaru:

* **Swipe-away di 1–3 detik pertama adalah sinyal dominan 2026**, bukan views.
  Ambang sehat: swipe-away < 15% (istimewa), 15–25% (sehat), > 35% = hook rusak.
  [[1]](https://retensis.com/blog/youtube-shorts-analytics-metrics-explained)
  [[2]](https://www.usefastlane.ai/blog/youtube-shorts-algorithm-2026)
* **Retensi (average percentage viewed) ≈ 70%** adalah ambang "bagus"; di bawah
  30% distribusi berhenti. [[3]](https://nexora-ai.org/blog/youtube-shorts-algorithm-2026)
  [[4]](https://gyre.pro/blog/youtube-shorts-view-count-update-impact-strategy-what-to-do-next)
* **Pita durasi 22–45 detik** konsisten mengalahkan ekstrem lain; 30–60 detik
  "sweet spot" untuk kebanyakan kreator. [[2]](https://www.usefastlane.ai/blog/youtube-shorts-algorithm-2026)
  [[5]](https://www.hashtagnetwork.net/youtube-seo/shorts-seo)
* **Loop & replay dihitung sebagai views** (sejak Maret 2025); frame akhir yang
  menyambung ke frame pertama adalah salah satu sinyal "sebar lebih luas".
  [[6]](https://aibrify.com/blog/youtube-shorts-retention-curve-playbook)
  [[7]](https://fliki.ai/blog/youtube-shorts-algorithm-explained)
* **Batas 3 menit** (sejak 15 Okt 2024). Shorts > 1 menit yang punya klaim hak
  cipta **diblokir global** → karena itu video ini memakai SFX sintetis tanpa
  musik pihak ketiga. [[8]](https://support.google.com/youtube/answer/15424877)
* Monetisasi Shorts: 1.000 sub + 10 juta views Shorts/90 hari
  (naik jadi 20 juta per Feb 2027). [[9]](https://vidiq.com/blog/post/youtube-shorts-monetization/)

### Konsekuensi desain

| Temuan | Keputusan di Ep56 |
|---|---|
| 1–3 detik menentukan | Frame 0 sudah berisi manusia tidur + teks "KAMU MERASA JATUH"; sentakan terjadi di detik 4,6 (bukan di akhir) |
| Butuh retensi ~70% | 10 babak, potongan/ganti komposisi ±7,5 detik sekali; tidak ada jeda > 0,5 detik tanpa gerak |
| 22–45 s lebih baik | tersedia **varian `kilat` (45,6 s, 6 babak)** selain `penuh` (75,9 s) |
| Loop menambah views | 0,85 detik terakhir menyatu ke frame 0 (`_frame0()`), frame akhir = frame awal |
| Tanpa suara sering ditonton | caption karaoke per kata di semua babak |
| Klaim hak cipta mematikan Shorts > 1 menit | 100% gambar & bunyi sintetis, tidak ada musik |

---

## 4. Desain retensi per detik (varian penuh, 75,9 s)

| Waktu | Babak | Fungsi retensi |
|---:|---|---|
| 0,0–7,4 | SENTAKAN | membuka dengan pengalaman penonton; sentakan + kilat + cincin di 4,6 s |
| 7,4–14,6 | NAMANYA | payoff: memberi nama ("hypnic jerk") → rasa dapat sesuatu |
| 14,6–22,8 | SEBARAN | piktogram 7/10 → validasi sosial ("bukan cuma saya") |
| 22,8–29,8 | WAKTUNYA | jam + pita N1/N2 → ketegangan "kapan tepatnya" |
| 29,8–37,8 | OTAK | mekanisme + EEG: jawaban ilmiah |
| 37,8–46,1 | LELUHUR | teori primata: bagian yang paling banyak dibagikan |
| 46,1–54,5 | DUA TEORI | dua kartu + "BUKAN PENYAKIT" (menenangkan = alasan like) |
| 54,5–62,1 | PEMICU | grafik batang: relatable, memancing komentar |
| 62,1–69,5 | CARA | tiga langkah: nilai simpan (save) |
| 69,5–75,9 | PENUTUP | ringkasan 3 detik + CTA simpan + loop ke awal |

**Pola yang dipakai di setiap babak** (konsisten, tidak membuat mata lelah):

1. label kecil kiri atas (isi babak, bukan HUD),
2. satu visual utama besar,
3. satu panel kaca berisi data/penjelasan,
4. caption karaoke + panel data bawah,
5. satu gerak kamera pelan (punch-in 1,5–5%) + goyangan tangan 2 px.

Setiap cut diberi **whip blur 0,42 detik** supaya mata tidak "dipukul" oleh
potongan mendadak (cut keras adalah penyebab swipe pada detik 3–6).

---

## 5. Keputusan audio (permintaan: "VO bukan WAV, untuk telinga manusia")

Lihat `docs/MESIN_V20.md §5` untuk tabel lengkap. Ringkas alasannya:

* **Bukan WAV** → keluaran kerja **M4A AAC 320 kbps, 48 kHz stereo** (yang
  diunggah). WAV 24-bit hanya arsip.
* **Untuk telinga** → 4 filter yang meniru cara telinga mempersepsi kejelasan
  (highpass 72 Hz, potong "lumpur" 260 Hz, angkat kejelasan 3,2 kHz, "udara"
  11 kHz), de-esser adaptif yang membandingkan pita desis dengan **pita bicara
  tengah** (bukan total), kompresor RMS 2:1 supaya kalimat pelan tidak
  tenggelam, saturasi tanh halus, loudnorm 2 lintasan ke −14 LUFS / TP −1,5.
* Diuji dengan sinyal sintetis: panjang tidak berubah (0 ms geser), de-esser
  terbukti bekerja (desis murni −3,0 dB), hasil −14,1 LUFS / TP −1,86 dBTP.

**Batas sesi ini:** edge-tts butuh `speech.platform.bing.com` yang tidak ada di
daftar host keluar sandbox. Jadi video dirender dengan **bed audio** (SFX +
ambien, −20 LUFS). Naskah VO 10 babak sudah ada di `mesin_v20_ep56.NASKAH`;
di mesin berjaringan, satu perintah menghasilkan VO + timing yang langsung
menggeser timeline:

```bash
python3 mesin_v20_suara.py --episode mesin_v20_ep56     # VO + timing.json
python3 render_v20.py --episode ep56 --keluar dist/... --audio dist/KlikTahu_Ep56_audio.m4a
```

---

## 6. Metadata & thumbnail

* Judul utama: **"Kamu Merasa Jatuh Tepat Sebelum Tidur? Ternyata Ini Sebabnya"**
  (pertanyaan + janji jawaban; 58 karakter, aman di feed).
* 3 alternatif judul disiapkan untuk uji A/B (`METADATA.md`).
* Deskripsi memuat **timestamp babak** (membantu retensi di versi panjang) dan
  rujukan sumber + disclaimer ("bukan diagnosis").
* 16 tag + 5 hashtag, termasuk frasa pencarian bahasa Indonesia
  ("kenapa badan nyentak saat tidur", "kenapa merasa jatuh sebelum tidur").
* Thumbnail dibuat dari **frame mesin yang sama** (`frame(t, bersih=True)`),
  bukan aplikasi lain → gaya tidak pecah. Dua versi: dengan angka **7/10**
  (utama) dan versi teks pertanyaan saja (uji A/B).

Aturan thumbnail yang dipakai (hasil koreksi dua percobaan):
teks ≤ 6 kata besar, angka besar sebagai jangkar mata, kontras gelap–terang,
tidak ada logo ganda, tidak ada teks mesin yang bertumpuk.

---

## 7. Rencana uji (biar "banyak views" bisa diukur, bukan diklaim)

| Uji | Versi A | Versi B | Metrik yang dibaca |
|---|---|---|---|
| Panjang | `kilat` 45,6 s | `penuh` 75,9 s | average % viewed, swipe-away 3 s |
| Thumbnail | `thumb_utama` (angka 7/10) | `thumb_alt` (pertanyaan) | CTR dari halaman channel |
| Judul | judul utama | alternatif #1 | CTR + retensi 3 s |
| Hook | sentakan di 4,6 s (versi ini) | sentakan di 1,2 s (ubah `sentak`) | swipe-away 3 s |

Cara membaca hasil (dari sumber §3): **swipe-away < 25%** dan
**average % viewed > 70% (untuk 45 s) / > 55% (untuk 76 s)** = layak
dilanjutkan; kalau retensi turun tajam di satu detik tertentu, lihat babak
yang sedang berjalan pada detik itu (tabel §4) dan perbaiki babak itu saja.

Jadwal yang disarankan: 2 Shorts/minggu (Selasa & Jumat, 19.00–21.00 WIB),
karena akun baru butuh **konsistensi 90 hari** untuk mengejar 10 juta views
jalur monetisasi Shorts.

---

## 8. Risiko & kepatuhan

| Risiko | Mitigasi |
|---|---|
| Dianggap konten medis/misleading | semua klaim bersumber (Sleep Medicine 2016, AASM, ICDS-3), ada disclaimer "bukan diagnosis", tidak menyarankan obat |
| Klaim hak cipta (mematikan Shorts > 1 menit) | 100% sintetis: gambar digambar kode, SFX dibuat numpy, tidak ada musik |
| Repetisi massal (kebijakan 2026) | setiap episode punya naskah, komposisi, dan palet berbeda; mesin sama, isi berbeda |
| Naskah "hard claim" yang salah | semua angka di video bisa dilacak ke sumber; klaim teori ditandai "BELUM TERBUKTI" |
| Penonton Indonesia jenuh istilah Inggris | istilah asing selalu diberi padanan Indonesia (hypnic jerk = sentakan tidur) |

---

## 9. Yang belum dikerjakan & langkah berikutnya

1. **VO bahasa Indonesia** (butuh jaringan) → jalankan `mesin_v20_suara.py`.
   Setelah itu `timing.json` otomatis menggeser batas babak dan `NASKAH` dipakai
   penuh; subtitle karaoke tetap memakai `CAPTION` yang lebih pendek.
2. **Analisis kuantitatif video acuan** (kalau berkasnya tersedia): histogram
   warna per detik, tempo potongan, ukuran tipografi → samakan parameternya.
3. **Varian `kilat`** sudah dirender: 45,60 s · 83,77 MB · QC 24/24.
4. **Subtitle**: `pustaka_v20.buat_srt()` sudah mengekspor `subtitle_id.srt`
   dari `CAPTION` dengan waktu yang sama seperti caption karaoke.
5. **Uji A/B nyata**: unggah `penuh` dan `kilat` sebagai dua video terpisah
   (bukan dua kali unggah video yang sama), bandingkan swipe-away 1–3 detik dan
   retensi 50% — ini satu-satunya angka yang menentukan pita durasi berikutnya.
