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
