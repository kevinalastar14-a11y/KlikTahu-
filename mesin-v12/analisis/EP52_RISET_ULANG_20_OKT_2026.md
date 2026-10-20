# RISET ULANG — Penentuan Ep52 (20 Oktober 2026)

**Perintah pemilik:** batalkan Piramida, **hapus antrean**, analisis ulang dari data, lalu lanjut produksi.
**Status:** antrean 15 Okt **dihapus seluruhnya**. Dokumen ini menggantikannya sebagai dasar pemilihan topik.

---

## 1. Yang dihapus, dan kenapa

Antrean 15 Okt: `Ep52 Piramida → Ep53 Semut → Ep54 Hujan bikin ngantuk → Ep55 Habis nangis → Ep56 Leonid/Supermoon`.

| Alasan hapus | Bukti |
|---|---|
| Piramida **menurun**, bukan naik | momentum Wikipedia **−0,568** (turun 57 % dalam 30 hari); `level30` hanya 1,4 artikel/hari |
| Piramida bukan pilar terkuat kanal | pilar MISTERI; data performa: LANGIT 1,46 · HEWAN 0,92 · BUMI 0,83 · TUBUH 0,81 · TEKNOLOGI 0,34 |
| Antrean tidak pernah divalidasi ulang | disusun 15 Okt dari `hasil_mendalam_20261015`, tidak dicek lagi setelah Ep51 tayang |
| Jadwalnya mengikat ke tanggal yang sudah lewat | slot 17–22 Okt sudah terpakai Ep51 (20 Okt) |
| Satu perintah pemilik | "jangan Piramida, hapus antrean-nya" |

Antrean **tidak diganti antrean baru**. Mulai sekarang topik dipilih per episode dari data terbaru (dokumen ini jadi polanya).

---

## 2. Metode baru (5 faktor, bobot eksplisit)

Sumber: `analisis/hasil_mendalam_20261015.json` (55 tema, 254 permintaan, 1.934 frasa unik) + `analisis/strategi_v6_20261015.json` (pesaing YouTube, 18 tema) + `analisis/performa.csv` (20 episode).

```
inti = 0,42·(tumbuh/90) + 0,24·niat + 0,20·pasar + 0,14·keterbukaan
inti ×= (0,75 + 0,25·kesegaran_pesaing)
skor  = inti × bobot_pilar
```

| Faktor | Definisi | Alasan |
|---|---|---|
| **tumbuh** | `skor_tumbuh` = permintaan × momentum | menunjukkan arah, bukan cuma volume |
| **niat** | `kuat / jml` (frasa bertanya spesifik / total) | penonton yang mencari jawaban, bukan sekadar kata |
| **pasar** | `log10(median views top-10 / 450)` | kanal baseline ±450 views/video; topik tanpa tarikan pasar = sia-sia |
| **keterbukaan** | `1 − judul_cocok/n` | kalau semua judul pesaing sudah persis, kita hanya jadi tiruan |
| **bobot pilar** | performa historis pilar kanal | LANGIT 1,46, HEWAN 0,92, BUMI 0,83, TUBUH 0,81 |

Subjek yang sudah diproduksi (Ep21–Ep51) dan isi antrean lama dikeluarkan dari kolam.

---

## 3. Hasil peringkat

| # | Tema | Pilar | Tumbuh | Niat | Median pesaing | Pesaing | Judul cocok | Skor |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | lubang hitam | LANGIT | 53,6 | 0,00 | 402.942 | 5 | 2 | 0,93 ¹ |
| 2 | aurora | LANGIT | 53,2 | 0,78 | 1.765 | 9 | **0** | 0,86 |
| 3 | matahari | LANGIT | 65,1 | 0,86 | — | — | — | 0,84 ² |
| **4** | **cegukan** | **TUBUH** | **82,4** | **0,85** | **34.388** | **7** | **0** | **0,72** |
| 5 | planet & roket | LANGIT | 49,6 | 0,92 | — | — | — | 0,72 ² |
| 6 | angin & badai | BUMI & CUACA | 54,5 | 0,74 | 38.781 | 6 | 0 | 0,62 |
| 7 | laut dalam | BUMI & CUACA | 46,3 | 0,89 | 19.784 | 3 | 1 | 0,59 ³ |
| 8 | listrik & magnet | TUBUH | 79,9 | 0,93 | — | — | — | 0,55 ² |
| 9 | kuku | TUBUH | 70,6 | 1,00 | — | — | — | 0,51 ² |
| 10 | pelangi | BUMI & CUACA | 66,8 | 0,86 | 4.403 | 12 | 11 | 0,46 |

¹ `niat` 0,00 karena data `kuat` kosong — cacat data, bukan sinyal. Lagi pula `long/v01_lubang_hitam` sudah ada.
² Tanpa data pesaing di `strategi_v6` (hanya 18 tema dipindai) → skor sudah didiskon 25 %. **Belum layak diputuskan tanpa sapuan pesaing baru.**
³ `long/v02_laut_dalam` sudah ada.

---

## 4. Keputusan: **Ep52 = Cegukan**

**Judul kerja:** "Cegukan Bisa Bertahan 68 Tahun — Ini yang Terjadi di Tubuh"

| Alasan | Angka |
|---|---|
| Pertumbuhan permintaan tertinggi di seluruh kolam yang belum diproduksi | **82,4** (peringkat #18 dari 55 tema keseluruhan) |
| Niat tertinggi di antara kandidat ber-data lengkap | **0,85** (23 dari 27 permintaan berupa pertanyaan spesifik) |
| Pasar terbukti, bukan tebakan | median top-10 **34.388 views** = ±76× baseline kanal |
| Pesaing sedikit **dan** tidak ada judul yang mendekat | 7 video, **0 judul cocok** → posisi masih kosong |
| Pilar TUBUH sudah terbukti di kanal | 13 episode (Ep25, 27, 28, 29, 30, 31, 32, 34, 36, 37, 43, 47, 48) |
| Tidak terikat tanggal | evergreen; aman kalau render molor |

**Kenapa bukan yang lain:**

- **Aurora** — skor lebih tinggi, tapi median pesaing 1.765 dan bukan fenomena yang bisa dialami penonton Indonesia; tidak ada kaitannya dengan musim hujan yang sedang berjalan.
- **Angin & badai** — paling musiman (Oktober = puncak cuaca ekstrem), tapi niat lebih rendah (0,74) dan pesaingnya 6 dengan pasar 38 rb. **Simpan sebagai kandidat kuat Ep53.**
- **Pelangi** — paling tersaturasi: 11 dari 12 judul pesaing sudah persis "kenapa ada pelangi". Sudut kita akan tenggelam.
- **Piramida, semut, hujan-ngantuk, nangis** — dihapus sesuai perintah.

---

## 5. Bahan riset (batas klaim dijaga)

| Klaim | Status | Batas |
|---|---|---|
| Cegukan = kontraksi diafragma mendadak + penutupan glotis | **dipakai** | mekanisme standar fisiologi |
| Jalur refleks melibatkan saraf vagus (aferen) dan frenikus (eferen) | **dipakai** | disebut sebagai *jalur*, bukan diagnosis |
| <48 jam akut · 48 jam–1 bulan persisten · >1 bulan intractable | **dipakai** | definisi durasi baku |
| Kasus terlama: Charles Osborne, 1922–1990 (±68 tahun) | **dipakai** | satu kasus, bukan generalisasi |
| Janin cegukan sejak dalam kandungan | **dipakai** | fungsi masih hipotesis → dibilang "sebagian ahli menduga" |
| Menahan napas bekerja karena CO₂ naik | **dipakai** | mekanisme masuk akal; bukti uji klinis lemah → jangan bilang "terbukti" |
| Kaget / minum terbalik menyembuhkan | **ditolak** | tidak ada bukti; masuk segmen mitos |
| Cegukan = tanda asam lambung naik | **dibatasi** | GERD salah satu pemicu, bukan penyebab tunggal |
| Obat cegukan | **tidak diklaim** | klorpromazin hanya untuk kasus membandel, wewenang dokter |

Sumber acuan: NIH/NCBI (definisi & durasi), Cleveland Clinic (ringkasan pasien), Guinness World Records (Osborne), Mayo Clinic (tanda bahaya). Tidak ada angka prevalensi yang diklaim karena tidak ada data Indonesia.

---

## 6. Rancangan 8 adegan (5 babak)

| Adegan | Babak | Isi | Visual |
|---|---|---|---|
| intro | hook | "Cegukan terlama: 68 tahun" | jam tua + diafragma, judul menimpa |
| f1 | agitation | apa yang sebenarnya bergerak | potongan tubuh: diafragma, udara, glotis |
| f2 | body 1 | jalur saraf: vagus & frenikus | diagram saraf dari leher ke diafragma |
| f3 | body 2 | kenapa berhenti sendiri + mitos | dua kolom: bekerja vs mitos + meter CO₂ |
| f4 | body 3 | 48 jam / 1 bulan / tanda bahaya | garis waktu durasi + bendera merah |
| f5 | micro-climax | janin sudah cegukan | rahim + denyut + garis waktu kehamilan |
| f6 | payoff | yang masuk akal + kapan ke dokter | 4 ubin tindakan + catatan medis |
| outro | loop | "yang singkat normal, yang tidak berhenti" | kembali ke jam, frame akhir = frame 0 |

---

## 7. Catatan kejujuran data

- Data permintaan berumur **5 hari** (15 Okt). Tidak ada akses jaringan untuk menyapu ulang YouTube; `median views` adalah potret 15 Okt.
- Tema tanpa baris pesaing (matahari, planet, listrik, kuku, segitiga bermuda) **tidak diputuskan** hanya karena skornya tinggi — tanpa data pesaing, skor itu tidak sebanding.
- Kalau Ep53 diambil dari daftar ini, **jalankan sapuan pesaing dulu** untuk kandidat yang bertanda ².

---

## 8. Yang berubah di repo

- `AGEN.md` §15: blok "Keputusan antrean" diganti penanda **ANTREAN DIHAPUS** + rujukan ke dokumen ini.
- `analisis/STRATEGI_V6.md`: kalender 7 episode dicabut, diganti catatan bahwa kalender tidak lagi mengikat.
- `PUSTAKA.md`: Ep51 ditandai selesai, Ep52 masuk sebagai entri baru.
