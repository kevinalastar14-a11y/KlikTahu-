# Ep51 — Ular Masuk Rumah Saat Musim Hujan (produksi v13)

**Status: SELESAI dan lolos QC (19 Oktober 2026).**
Judul: *Ular Masuk Rumah Saat Musim Hujan? Bukan Karena Banjir*
Durasi: **128,47 s** · 1080×1920 · **60 fps** · tanpa musik (SFX sintetis + ambient hujan)
VO: TTS Arena `voice-00` (id-ID, maskulin) → `.m4a` 24 kHz → rantai `vo_manusia.py` (tanpa atempo, tanpa pemotongan kata).

## 0. Berkas jadi (dist/)

| Berkas | Keterangan |
|---|---|
| `KlikTahu_Ep51_Ular_Rumah.mp4` | **104,2 MB**, H.264 6228 kb/s + AAC 256k, 128,47 s |
| `KlikTahu_Ep51_Ular_Rumah_audio.m4a` | **3,19 MB**, AAC 192k 48 kHz stereo, 129,06 s, **−14,0 LUFS / TP −1,6 dBTP / LRA 2,5** |
| `KlikTahu_Ep51_Ular_Rumah_content.json` | timeline + caption + field visual |
| `METADATA.md` | judul/deskripsi/tag/jadwal (unggah **Selasa 20 Okt 2026, 18.30–20.30 WIB**) |
| `SIAP_TEMPEL.md` | teks siap tempel ke YouTube Studio |
| `Ep51_thumbnail.jpg`, `Ep51_pratinjau.jpg` | sampul + lembar 8 adegan |

Disalin juga ke Google Drive `KlikTahu_Produksi/Shorts/kliktahu-ep51-ular-masuk-rumah/`
(folder `1rxdQrxPqVbZ_B3ZFvL76jWIl4T312C3e`), termasuk MP4, audio `.m4a`, metadata, pratinjau.

## 1. Hasil QC akhir

- `qc_mp4.py`: **SEMUA BERSIH ✔** — korelasi audio MP4 vs master 1,0000 (lag 0 ms), selisih level −0,01 dB,
  peak −1,7 dBFS, semua VO utuh (durasi aktif = naskah − 0,47 s, toleransi < 0,01 s), ekor 0,64–0,94 s.
- `qc_loop.py`: **LOOP OK ✔** — frame 0 vs akhir−0,03 s korelasi **0,9994**.
- `check_layout.py`: **tata letak bersih ✔** — 8 adegan, semua elemen teks/pil di dalam margin 40 px.
- `vo_manusia.py`: **8/8 bersih** — onset 90–120 ms, ekor 255–350 ms, −16,0 LUFS, TS ≤ −4,2 dBTP, de-ess ≤ 3 dB,
  0 hening digital.
- `master_audio.py`: −14,0 LUFS, TP −1,6 dBTP, limiter maks 0,5 dB, **0 sampel clipping**, 86 event SFX.

## 2. Yang membuat Ep51 lebih baik dari Ep50

| Aspek | Ep50 | Ep51 |
|---|---|---|
| Dunia visual | satu cakram langit sepanjang 124 s | **8 komposisi** dari satu rumah: pemandangan luar, potongan melintang, kalender 4×3 + sarang telur, rantai mangsa, irisan tanah, denah dari atas, daftar tindakan, luar lagi |
| Finishing | bloom + grade + vinyet + grain | **V13**: halation dari detail → lindung highlight → unsharp 0,12 → vinyet 4 % → dither → grain 2,2 |
| Latar | mesh penuh | mesh **0,34×** → krem/navy/jingga tetap identitas KlikTahu |
| VO | process_audio + atempo 1,09 | TTS baru, **tanpa atempo**, de-esser ≤ 3 dB, limiter TP −2 dB, −16 LUFS per klip |
| Audio | SFX per BEAT | 86 event per KATA + ambient hujan −30 dB |
| Loop | frame akhir = frame 0 | sama, ditambah fase hujan berbasis detik agar tetes identik |

## 3. Bug yang ditemukan & diperbaiki di jalan

1. **`timeline.json` tanpa `meta.mesin="v12"`** → jalur v12 (kamera kontinu, loop, transisi) mati dan render jatuh
   ke jalur v3 yang memudarkan frame terakhir ke krem. Diperbaiki di `build_timeline.py`.
2. **`master_audio.py` tidak memuat modul episode** → `EVENTS12` kosong, SFX tidak pernah berbunyi. Sekarang modul
   dimuat dari `content.json → "modul"`.
3. **`vo_manusia.py`** mengukur onset di −55 dBFS (lebih sensitif dari QC `build_audio.py` −45) → klip dengan napas
   pelan di kepala gagal QC. Ambang diselaraskan ke −44 dBFS.
4. **`align_kata.py`** (tanpa whisper) memakai satu rentang bicara; sekarang dijangkarkan pada jeda ≥ 135 ms.
5. **`sc_kering50` crash** — `rounded_rectangle` dengan `y0 > y1` saat air tanah mulai naik (render berhenti di
   potongan 4). Tinggi air diklem.
6. **`qc_mp4.py` alarm palsu** — ambang relatif-puncak −40 dB terlalu tumpul untuk konsonan pelan, VO utuh terbaca
   0,4 s lebih pendek. Ditambah mode v12: gerbang RMS 5 ms ≥ −44 dBFS (sama dengan rantai VO) → beda ≤ 0,01 s.
7. **`tools/render_lokal.sh`** tidak mengekspor `KT_VO_CHAIN`/`KT_AUDIO_SRC` sebelum QC akhir → QC gagal dan
   metadata tidak tersalin ke `dist/`. Sekarang diekspor.

## 4. Perbaikan visual (iterasi pratinjau)

- Kalender: hanya **SEP–DES** disorot, bracket "3-4 BULAN" di baris ketiga; chip musim dipisah agar tidak bertumpuk.
- Sarang telur: anyaman ranting 34 goresan + serpihan jerami, retak halus hanya pada telur besar.
- Rantai mangsa: katak (kaki terlipat, mata menonjol), cicak (ekor melengkung), tikus (telinga, kumis, ekor);
  ular ikon digambar sebagai gelombang halus; tikus lari ke pintu dan memudar di ambang, ular menyusul di alur
  yang sama dengan tekukan 0,42 agar tidak menimpa atap.
- Irisan rumah: ular plafon digambar sebagai **spiral kontinu** (polyline + dot), bukan bintik terpisah.
- Denah: tiga panah dengan label di luar pelat, penanda "rumah" kecil, chip CELAH PINTU / SEMBUNYI tidak bertumpuk.
- Daftar tindakan: teks rata kiri, ikon & centang di kanan, kartu DAMKAR 113 tidak lagi menabrak chip.
- Kamar mandi f1 diberi gayung/ember/ubin/saluran; chip "BALIK LEMARI" dipindah agar tidak terpotong tepi.

## 5. Struktur 5 babak

Hook (intro) → Agitation (f1) → Body 1 kalender telur (f2) → Body 2 rantai mangsa (f3) → Body 3 kering & hangat (f4)
→ Micro-climax denah tiga panah (f5) → Payoff urutan dibalik (f6) → Loop (outro, frame akhir = frame 0).
