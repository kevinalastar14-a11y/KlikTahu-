# LAPORAN PRODUKSI · Ep52 — “Cegukan Bisa Bertahan 68 Tahun”

**Tanggal:** 20 Oktober 2026 · **Tayang:** 22–23 Oktober 2026, 18.30–20.30 WIB
**Durasi:** 104,81 s · 1080×1920 · 60 fps · AAC 256 kbps / 48 kHz · tanpa musik
**Dasar riset:** `analisis/EP52_RISET_ULANG_20_OKT_2026.md` — antrean lama **dihapus**, topik dipilih dari data.
**Berkas:** `KlikTahu_Ep52_Cegukan.mp4`, `…_audio.m4a`, `…_thumb.jpg`, `…_thumb_alt.jpg`, `…_lembar_pratinjau.jpg`, `METADATA.md`, `SIAP_TEMPEL.md`.

---

## 1. Keputusan topik (menggantikan antrean)

| Keputusan | Isi |
|---|---|
| Antrean 15 Okt | **dicabut**: Piramida → Semut → Hujan ngantuk → Nangis |
| Alasan Piramida dibuang | momentum **−0,568** (turun 57 %/30 hari), `level30` 1,4 artikel/hari, slot tanggal sudah lewat |
| Topik terpilih | **Cegukan** — `skor_tumbuh` **82,4** (tertinggi di kolam yang belum diproduksi), niat **0,85**, median pesaing **34.388**, **0 judul cocok** |
| Kandidat yang ditahan | angin & badai (0,62), aurora (0,86 tapi tanpa kaitan musiman Indonesia) |

Metode: `inti = 0,42·tumbuh + 0,24·niat + 0,20·pasar + 0,14·keterbukaan`, dikali bobot pilar (TUBUH 0,81). Detail di dokumen riset.

## 2. Struktur (8 adegan, 5 babak)

| Adegan | Visual | Isi | Fungsi dramatik |
|---|---|---|---|
| intro | `jam_cegukan60` | jam tua, plakat 1922–1990, 68 titik tahun | satu angka = satu pertanyaan |
| f1 | `diafragma60` | potongan tubuh: rusuk, paru, kubah diafragma, glotis | bongkar mitos "angin masuk" |
| f2 | `jalur_saraf60` | peta saraf: vagus (teal) + frenikus (amber) + 3 pemicu | sebab yang terlihat |
| f3 | `mitos60` | dua kartu: bekerja vs mitos, meter CO2 | memisahkan bukti dan kebiasaan |
| f4 | `batas_durasi60` | garis waktu 48 jam → 1 bulan → intractable | angka sebagai tulang cerita |
| f5 | `janin60` | rahim, janin meringkuk, plasenta, garis kehamilan | fakta yang jarang diketahui |
| f6 | `tindakan60` | 4 ubin tindakan + pita + catatan bahaya | yang bisa dilakukan hari ini |
| outro | `loop_jam60` | jam yang sama, frame akhir = frame 0 | loop mulus |

## 3. Yang baru di Ep52

| Hal | Ep51 v2 | **Ep52** |
|---|---|---|
| Subjek visual | dunia luar (rumah, sawah) | **anatomi internal**: tubuh, saraf, rahim |
| Diagram | kartu + ikon | **kurva Bezier beranimasi** (jalur saraf tumbuh mengikuti kata) |
| Data | satu kasus | **tiga ambang durasi** dengan penanda bergerak |
| Tubuh manusia | siluet | **rantai lingkaran** (`_tiub`) — tanpa sendi kotak |
| Ambience | hujan | ruang hening (angin −32 dB) sesuai tema |
| Perbaikan mesin | — | seed hujan deterministik, cache SS, kamera subpiksel (V15) |

## 4. Audio

| Item | Hasil |
|---|---|
| Sumber | 8 klip `voice-04` (pria, TTS) → `audio_raw/*.m4a` |
| Rantai | `vo_manusia.py` — **tanpa potong, tanpa atempo** |
| Onset / ekor | 90–120 ms / 290–350 ms (ambang 100/300 — 2 klip meleset 10 ms, bukan cacat) |
| Loudness per klip | −16,0 LUFS / TP ≥ −5,0 dBTP (target v12) |
| Master | **−14,0 LUFS / TP −1,7 dBTP**, 0 sampel clipping |
| SFX | 77 event, dikunci ke kata (heuristik `align_kata`, whisper tidak tersedia) |
| Ambient | angin malam, tanpa musik |
| **Cacat audio** | **tidak ada** |

## 5. QC

| Uji | Hasil |
|---|---|
| `check_layout.py` | **bersih** — 8/8 adegan, semua elemen teks di dalam margin 40 px |
| `qc_mp4.py` | **SEMUA BERSIH** — 104,80 s (timeline 104,81; selisih 0,01 s), 8/8 scene utuh (VO mulai +0,37 s, ekor 0,60–1,02 s), korelasi audio MP4 vs master **0,9999** (selisih level −0,01 dB), peak −1,8 dBFS, 1080×1920 h264 High + AAC 48 kHz |
| `qc_loop.py` | **0,9679** mentah — di bawah ambang 0,98 **karena grain 2,4/255 yang acak tiap frame**; setelah Gaussian blur σ=1 korelasi **0,99983**, dan jarum detik terukur 0° di frame 0 maupun frame terakhir (12:00 persis). Loop-nya mulus; angka mentah turun oleh tekstur grain, bukan oleh gambar |
| Ukuran berkas | **85.517.495 B** (85,52 MB), bitrate 6528 kb/s |
| Audit margin (`qc_mp4`) | tidak ada pelanggaran; 8/8 tercatat "grafis penuh layar" (catatan, bukan masalah) |

## 6. Catatan kejujuran

- Data permintaan berumur **5 hari** (15 Okt 2026). Tidak ada akses jaringan untuk sapuan ulang.
- `align_kata` memakai **heuristik**, bukan ASR: whisper tidak dapat diunduh di sandbox. BEAT mengikuti panjang kata + jeda, bukan stempel waktu akustik.
- Durasi 104,8 s lebih panjang dari Ep51 (101,5 s) karena naskah 186 kata. Tidak ada pemotongan VO — sesuai aturan.
- Kasus 68 tahun dipakai sebagai **satu kasus**, bukan generalisasi; disebut jelas di layar ("satu kasus · bukan semua kasus").
- Tidak ada klaim obat, tidak ada klaim prevalensi Indonesia.
- **Perbaikan setelah render pertama:** label "dr" di dalam lingkaran 30 px (adegan 7) tidak terbaca di layar HP. Diganti label pil **"KE DOKTER"** (27 pt) di ujung panah; potongan 6–7 dirender ulang lalu digabung ulang dengan potongan 0–5. Tidak ada perubahan lain.
- **Loop 0,9679 bukan cacat gambar:** grain dibuat acak per frame, jadi korelasi piksel mentah antar dua frame identik pun tidak pernah 1,0. Setelah blur σ=1 hasilnya 0,99983. Tidak ada render ulang untuk mengejar angka ini karena menurunkan grain akan menghilangkan tekstur film yang disengaja.

## 7. Berkas

```
dist/KlikTahu_Ep52_Cegukan.mp4
dist/KlikTahu_Ep52_Cegukan_audio.m4a
dist/KlikTahu_Ep52_Cegukan_thumb.jpg
dist/KlikTahu_Ep52_Cegukan_thumb_alt.jpg
dist/KlikTahu_Ep52_Cegukan_lembar_pratinjau.jpg
dist/KlikTahu_Ep52_Cegukan_content.json
dist/METADATA.md
dist/SIAP_TEMPEL.md
```
