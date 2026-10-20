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
| `qc_mp4.py` | _diisi setelah render_ |
| `qc_loop.py` | _diisi setelah render_ |
| Ukuran berkas | _diisi setelah render_ |

## 6. Catatan kejujuran

- Data permintaan berumur **5 hari** (15 Okt 2026). Tidak ada akses jaringan untuk sapuan ulang.
- `align_kata` memakai **heuristik**, bukan ASR: whisper tidak dapat diunduh di sandbox. BEAT mengikuti panjang kata + jeda, bukan stempel waktu akustik.
- Durasi 104,8 s lebih panjang dari Ep51 (101,5 s) karena naskah 186 kata. Tidak ada pemotongan VO — sesuai aturan.
- Kasus 68 tahun dipakai sebagai **satu kasus**, bukan generalisasi; disebut jelas di layar ("satu kasus · bukan semua kasus").
- Tidak ada klaim obat, tidak ada klaim prevalensi Indonesia.

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
