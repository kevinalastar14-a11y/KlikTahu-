# KlikTahu — Video Short Otomatis untuk YouTube

KlikTahu memproduksi **YouTube Short 1080×1920 @ 60 fps** sepenuhnya dari kode:
naskah → voice-over → animasi sinematik → encode → (opsional) upload YouTube.

Hasil terbaru ada di [`KlikTahu-Video/KlikTahu_Shorts_1080x1920.mp4`](KlikTahu-Video/KlikTahu_Shorts_1080x1920.mp4)
(40 detik, 60 fps, ~235 MB, audio AAC 320 kbps).

```bash
cd KlikTahu-Video
pip install -r requirements.txt
python cinematic_engine.py --render --target-mb 235   # hasilkan video
python tools/verify_video.py                          # cek siap-unggah
python tools/youtube_upload.py --privacy private      # unggah ke YouTube
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
