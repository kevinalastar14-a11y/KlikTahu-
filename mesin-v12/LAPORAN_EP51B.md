# LAPORAN PRODUKSI · Ep51 v2 — “Ular Masuk Rumah Saat Hujan?”

**Tanggal:** 19–20 Oktober 2026 · **Tayang:** Selasa, 20 Oktober 2026, 18.30–20.30 WIB
**Durasi:** 101,53 s · 1080×1920 · 60 fps · AAC 256 kbps / 48 kHz · tanpa musik
**Dasar riset:** `analisis/EP51_RISET_ULANG_18_OKT_2026.md` (commit `6324e12`) — analisis ulang, **bukan** analisis AI sebelumnya.
**Berkas:** `KlikTahu_Ep51_Ular_Rumah_v2.mp4`, `…_audio.m4a`, `…_thumb.jpg`, `…_thumb_alt.jpg`, `…_lembar_pratinjau.jpg`, `METADATA.md`, `SIAP_TEMPEL.md`.

---

## 1. Apa yang berubah dari draf Ep51 sebelumnya

| Aspek | Ep51 v13 (arsip) | **Ep51 v2 (ini)** |
|---|---|---|
| Klaim inti | “bukan karena banjir” | “bukan **cuma** banjir” — tiga jalur dipisah |
| Struktur | rumah → telur → mangsa → jalur | genangan → kasus 22 anak sanca → dua cara berbiak → lima jalur masuk → tiga petunjuk → tindakan aman |
| Data | BRIN + BMKG + kasus | + rilis BMKG 2 Okt 2026, kasus Sukabumi (Kompas 10 Des 2025), prosedur Damkar Cirebon, panduan WHO |
| Visual | flat card, teks di kertas | dunia penuh + tepi kertas sobek, legenda nomor, kartu bukti, diagram jarak, catatan medis |
| Finishing | V13 | **V14**: halation + lindung highlight + CA radial + split-tone + dither + grain |
| Layout | global card | 8 dunia berbeda, semua teks lolos audit margin 40 px |

## 2. Alur cerita (5 babak + loop)

| Waktu | Adegan | Isi | Visual |
|---|---|---|---|
| 0,00–4,72 | intro | “Ular masuk rumah saat hujan. Apa selalu karena banjir?” | rumah saat hujan, ular menyusur ke ambang, lampu pintu bernapas |
| 4,72–15,21 | f1 | Genangan mengusik habitat — satu kemungkinan, bukan satu-satunya | sawah terendam, air naik (pancang ukur), ular berenang, lubang galian |
| 15,21–30,02 | f2 | 22 anak sanca Sukabumi (Des 2025): satu kasus lokal | tanah dari atas, sarang telur, 22 anakan muncul satu per satu + penghitung 22 |
| 30,02–42,17 | f3 | Dua cara berbiak: bertelur vs melahirkan; waktu tidak serempak | kartu dua kolom + garis waktu 12 bulan + cap “TIDAK SEREMPAK” |
| 42,17–54,62 | f4 | Lima jalur masuk yang bisa diperiksa | denah rumah potongan + 5 nomor + legenda |
| 54,62–74,94 | f5 | Tiga petunjuk → tiga skenario, bukan satu aturan | tiga kartu bukti → satu berlian “?” |
| 74,94–95,89 | f6 | Jaga jarak, hubungi petugas, pertama bantu (WHO) | diagram jarak + 4 kartu tindakan + catatan merah “torniket · sayat · isap” |
| 95,89–101,53 | outro | Kembali ke ambang pintu | frame akhir = frame 0 |

## 3. Audio

- VO `voice-00` (TTS) → **`vo_manusia.py`**: pra 120 ms / pasca 350 ms, fade 30/150 ms, target −16 LUFS per klip, **tanpa atempo, tanpa pemotongan, tanpa hening sisipan**, de-ess maks 3 dB.
- QC keutuhan: semua 8 klip utuh, tidak bertabrakan, tidak melewati batas adegan; dua klip ditandai “PERIKSA” oleh heuristik onset/ekor, diperiksa manual: hanya noise-floor TTS sebelum kata pertama (bukan klip terpotong).
- SFX sintetis 88 event, ambient hujan halus (tanpa musik).
- Master: **−14,0 LUFS · TP −1,6 dBTP · 0 sampel clipping** · 102,13 s.
- Master audio diserahkan sebagai `.m4a` AAC 192 kbps / 48 kHz (bukan WAV).

## 4. Visual & QC tata letak

- 8 visual kode (Pillow), palet KlikTahu: krem `#F2ECDF`, navy, jingga; aksen per babak.
- `check_layout.py`: **tata letak bersih ✔** — intro 4, f1 5, f2 6, f3 4, f4 18, f5 14, f6 14, outro 8 elemen teks/pil, semuanya ≥40 px dari tepi.
- Warna: mesh ditahan `KT_MESH=0.30` agar krem tidak bergeser; highlight tinta tetap navy/aksen.
- Animasi: hujan 3 lapis, riak, cahaya pintu, gerak ular, penghitung data, kartu masuk berurutan, denyut hub “?”.

## 5. QC akhir

| Uji | Hasil |
|---|---|
| `qc_mp4.py` | **SEMUA BERSIH ✔** — durasi 101,53 s (selisih 0,00 s), audio MP4 vs master korelasi 0,9999, selisih level −0,01 dB, peak −1,6 dBFS/kanal |
| VO per adegan | 8/8 OK — mulai +0,37 s (lead-in 0,24 s), durasi tiap adegan beda ≤0,01 s dari naskah, ekor 0,60–1,02 s |
| `qc_loop.py` | **0,9995** (frame 0 vs akhir−0,03 s) → LOOP OK ✔ |
| Ukuran berkas | 83.496.943 B (83,50 MB) · bitrate 6579 kb/s · 1080×1920 60 fps · H.264 High |
| Loudness | −14,0 LUFS / TP −1,6 dBTP · 0 sampel clipping |
| Audio master | `…_audio.m4a` AAC 192 kbps · 48 kHz · 2.464.435 B |

## 6. Batas klaim (penting)

- Yang **tidak** diklaim: “ular selalu masuk karena banjir”, “semua telur menetas saat hujan”, angka populasi nasional, migrasi massal.
- Kasus 22 anak sanca = **satu kasus lokal**, bukan generalisasi.
- Pertolongan pertama mengikuti WHO: jangan torniket ketat, jangan menyayat, jangan mengisap; segera ke fasilitas kesehatan.
- Video edukasi, bukan pengganti petugas satwa atau tenaga medis.

## 7. Sumber

- BMKG — prakiraan awal musim hujan 2026/2027 (rilis 2 Oktober 2026).
- BRIN / Amir Hamidy — masa penetasan sanca (Mongabay, 7 April 2024).
- Kompas, 10 Desember 2025 — 22 anak sanca ditemukan di Sukabumi.
- Damkar Cirebon, 19 November 2025 — prosedur penanganan ular.
- WHO — pertolongan pertama gigitan ular.

## 8. Catatan produksi

- Render lokal (`tools/render_lokal.sh`), bukan GitHub Actions; MP4 tidak masuk repo.
- `vo_manusia.py`, `mesin_fx.py` (V14), `render.py` (modul episode otomatis) ikut diperbarui pada sesi ini.
- Optimasi render: hujan & bintik kertas digambar dalam satu lapisan (bukan ratusan lapisan kecil) → waktu per bingkai turun ±40%.
