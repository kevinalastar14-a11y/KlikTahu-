# Deliverables — KlikTahu Short #01

## Tautan GitHub

- **Repo, branch kerja:** https://github.com/kevinalastar14-a11y/KlikTahu-/tree/arena/97a5a3a6-kliktahu
- **Preview MP4 720p:** https://github.com/kevinalastar14-a11y/KlikTahu-/blob/arena/97a5a3a6-kliktahu/KlikTahu-Video/preview_720p.mp4
  - 720×1280, 60 fps, 38,82 detik, sekitar 2,1 MB. Buka halaman file lalu pilih **Raw** atau **Download raw file**.
- **Kode project:** https://github.com/kevinalastar14-a11y/KlikTahu-/tree/arena/97a5a3a6-kliktahu/KlikTahu-Video
- **Naskah:** https://github.com/kevinalastar14-a11y/KlikTahu-/blob/arena/97a5a3a6-kliktahu/KlikTahu-Video/script_kliktahu.py
- **Catatan rilis:** https://github.com/kevinalastar14-a11y/KlikTahu-/releases/tag/short-01-v1 (catatan saja; file video tidak terlampir).

### Batas file GitHub

Preview 720p adalah file video yang tersedia langsung di repo. **Master 1080p 235,5 MiB (246,9 MB) tidak terlampir di GitHub**: batas satu file dalam repo GitHub adalah 100 MB, dan upload lampiran release dari lingkungan produksi ini tidak dapat menjangkau host upload GitHub. File master dapat dibuat ulang dari kode di bawah ini.

Versi **1080×1920 @ 60 fps, 90,1 MB** tersedia di Google Drive untuk dibuka, diunduh, atau dikirim:
<https://drive.google.com/drive/folders/10VaNur2P7hCileWW995SDJtjQZ5d4Brn>

## Lokasi di Google Drive

**Folder:** `KlikTahu_Produksi / Shorts / kliktahu-3-detik-pertama`

| Berkas | Ukuran | Keterangan |
|---|---:|---|
| `kliktahu-3-detik-pertama_final_v1_60fps.mp4` | 90,1 MB | Video delivery 1080×1920 @ 60 fps |
| `kliktahu-3-detik-pertama_audio-master_-14LUFS.m4a` | 1,05 MB | Audio master AAC 320 kbps |
| `kliktahu-3-detik-pertama_thumbnail.jpg` | 275 KB | Thumbnail 1080×1920 (frame hook) |
| `kliktahu-3-detik-pertama_metadata.json` | 2,7 KB | Judul, deskripsi, tag, struktur beat |
| `kliktahu-3-detik-pertama_README.md` | — | Catatan produksi di Google Docs |

## Dua versi video

| | Master (render ulang dari kode) | Delivery (Drive) |
|---|---|---|
| Ukuran | 235,5 MiB (246,9 MB) | 90,1 MB |
| Bitrate video | 50,5 Mbps | 18,6 Mbps |
| Audio | AAC-LC, di-copy tanpa encode ulang | AAC-LC, identik dengan master |
| Kegunaan | Unggahan YouTube kualitas maksimum | Unduh, kirim, atau arsip praktis |

Keduanya memiliki visual dan audio yang sama; versi Drive hanya menggunakan bitrate video lebih rendah. YouTube akan meng-encode ulang video saat diunggah, sehingga master berbitrate tinggi disarankan untuk kualitas terbaik.

## Spesifikasi

- Kanvas 1080×1920 (9:16), 60 fps, H.264 High @ Level 4.2, yuv420p, `+faststart`
- Durasi 38,82 detik (2.329 frame)
- Audio AAC-LC 320 kbps dalam MP4 — **bukan WAV/PCM**
- Loudness **-14,0 LUFS** integrated (ITU-R BS.1770-4, K-weighting + gating)
- True peak **-1,6 dBTP** (oversampling 4×), mono-fold -0,00 dB
- Tanpa musik latar; hanya narasi + SFX prosedural

## Render dan verifikasi master

```bash
cd KlikTahu-Video
pip install -r requirements.txt
python cinematic_engine.py --render --target-mb 235
python tools/verify_video.py KlikTahu_Shorts_1080x1920.mp4
```
