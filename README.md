# KlikTahu — Short Video Engine

Mesin pembuat **YouTube Short** otomatis: 1080×1920 (9:16), **60 fps**, H.264
High @ L4.2 + AAC 320 kbps, durasi ~39 detik, ukuran file digerakkan menuju
**235 MB** (jauh di atas 200 MB) tanpa bitrate sampah — detailnya dari gerak
kamera, aurora, partikel, dan film grain yang memang ada di setiap frame.

Seluruh isi video digambar dengan kode. Tidak ada stock footage, tidak ada BGM
berlisensi, tidak ada API berbayar, tidak ada kode mati.

```bash
cd KlikTahu-Video
pip install -r requirements.txt
python cinematic_engine.py --render --target-mb 235
```

Hasil: `KlikTahu-Video/KlikTahu_Shorts_1080x1920.mp4`

## Isi video (10 beat, 38,8 detik)

| # | Beat | Visual |
|---|---|---|
| 1 | Hook | Cincin hitung mundur + angka "3" elastis, garis pemindai |
| 2 | Pilihan | Tombol play tersapu keluar, chevron skip, bar "WATCH TIME" yang terkuras |
| 3 | Masalah | Bilah aksen merah, teks raksasa "MASALAHNYA BUKAN KONTENMU JELEK." |
| 4 | Agitasi | Grafik penurunan retention dengan zona "3 DETIK" merah |
| 5–7 | Solusi | Kartu aturan 01/02/03 dengan lencana bernomor + diagram per aturan |
| 8 | Kunci | "RETENTION BUKAN KEBERUNTUNGAN." dengan kata dicoret |
| 9 | Klimaks | Ledakan sinar + guncangan kamera + flash, "RETENTION ADALAH DESAIN." |
| 10 | Penutup | Kartu merek, CTA simpan, memudar ke latar gelap (loop mulus) |

## Mesin v20 "KEDALAMAN" (terbaru)

Episode perdana v20: **Ep56 — "Kamu Merasa Jatuh Tepat Sebelum Tidur"** (hypnic jerk),
1080×1920 · 60 fps · 75,9 detik, 10 babak, QC 24 butir, audio M4A 320 kbps.

```bash
cd mesin-v12
python3 mesin_v20_uji.py                                    # selftest 35 detik
python3 mesin_v20_audio.py --uji-sintetis                   # uji rantai audio telinga
python3 mesin_v20_suara.py --episode mesin_v20_ep56         # VO (butuh jaringan)
python3 render_v20.py --episode ep56 --jobs 2 --preset slow --crf 16 \
        --keluar dist/KlikTahu_Ep56_HypnicJerk_v20.mp4 --audio dist/KlikTahu_Ep56_audio.m4a
python3 qc_v20.py dist/KlikTahu_Ep56_HypnicJerk_v20.mp4 --episode ep56 --audio dist/KlikTahu_Ep56_audio.m4a
python3 pustaka_v20.py --episode ep56 --slug Ep56_HypnicJerk
```

| Dokumen | Isi |
|---|---|
| [`mesin-v12/docs/MESIN_V20.md`](mesin-v12/docs/MESIN_V20.md) | arsitektur v20, palet, tata letak, rantai audio, jebakan |
| [`mesin-v12/analisis/EP56_V20_ANALISIS.md`](mesin-v12/analisis/EP56_V20_ANALISIS.md) | riset algoritma Shorts 2026, desain retensi per detik, rencana uji A/B |
| [`mesin-v12/pustaka/Ep56_HypnicJerk/`](mesin-v12/pustaka/Ep56_HypnicJerk/) | judul, deskripsi, tag, thumbnail, lembar pratinjau |

## Dokumentasi

Selengkapnya ada di [`KlikTahu-Video/README.md`](KlikTahu-Video/README.md):
arsitektur mesin, cara mengganti naskah, alur produksi, dan otomasi GitHub Actions.

## Struktur

```
KlikTahu-Video/
├── script_kliktahu.py     # naskah + arahan visual (edit di sini untuk ganti isi)
├── cinematic_engine.py    # timeline, 7 tipe scene, transisi, encoder x264
├── visuals.py             # primitif grafis & easing, tipografi kinetik
├── audio_design.py        # SFX prosedural, ducking, limiter, loudness
├── voice_over.py          # narasi edge-tts -> narration/
├── narration/             # voice-over per beat
├── assets/fonts/          # Poppins (SIL OFL 1.1)
└── tools/                 # verifikasi video, upload YouTube, refresh token
```

## Isi Proyek

| Bagian | Berkas |
|---|---|
| Naskah & arahan visual | `KlikTahu-Video/script_kliktahu.py` |
| Mesin render (timeline, 7 scene, transisi, encoder) | `KlikTahu-Video/cinematic_engine.py` |
| Primitif visual & tipografi kinetik | `KlikTahu-Video/visuals.py` |
| Tata suara (SFX prosedural, ducking, limiter) | `KlikTahu-Video/audio_design.py` |
| Narasi (edge-tts) | `KlikTahu-Video/voice_over.py` |
| Upload & verifikasi YouTube | `KlikTahu-Video/tools/` |
| Otomasi render terjadwal | `KlikTahu-Video/.github/workflows/generate_video.yml` |

Dokumentasi lengkap ada di [`KlikTahu-Video/README.md`](KlikTahu-Video/README.md)
(arsitektur, cara kerja sinkronisasi kata, dan cara mengganti isi video).

## Catatan Versi Ini

- Seluruh kode MoviePy 1.x yang usang dan kode mati sudah dibuang; renderer
  sekarang memakai Pillow + numpy + ffmpeg statis (`imageio-ffmpeg`), tanpa
  dependensi sistem.
- **Prompt GPT-4o sudah dihapus** beserta `ai_generator.py` — naskah sekarang
  ditulis langsung di `script_kliktahu.py`.
- Diganti dengan pipeline deterministik: frame dirender ulang dengan hasil
  identik, tanpa biaya API.
