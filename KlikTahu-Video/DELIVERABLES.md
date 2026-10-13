# Deliverables — KlikTahu Short #01

Semua hasil produksi short ini, lengkap dengan lokasi dan spesifikasinya.

## Lokasi di Google Drive

**Folder:** `KlikTahu_Produksi / Shorts / kliktahu-3-detik-pertama`
<https://drive.google.com/drive/folders/10VaNur2P7hCileWW995SDJtjQZ5d4Brn>

| Berkas | Ukuran | Keterangan |
|---|---|---|
| `kliktahu-3-detik-pertama_final_v1_60fps.mp4` | 90,1 MB | Video delivery 1080×1920 @ 60 fps |
| `kliktahu-3-detik-pertama_audio-master_-14LUFS.m4a` | 1,05 MB | Audio master AAC 320 kbps |
| `kliktahu-3-detik-pertama_thumbnail.jpg` | 275 KB | Thumbnail 1080×1920 (frame hook) |
| `kliktahu-3-detik-pertama_metadata.json` | 2,7 KB | Judul, deskripsi, tag, struktur beat |
| `kliktahu-3-detik-pertama_README.md` | — | Catatan produksi (Google Docs) |

## Dua versi video (sengaja, bukan duplikat)

| | Master | Delivery (Drive) |
|---|---|---|
| Berkas | `KlikTahu_Shorts_1080x1920.mp4` (di repo, `build/` diabaikan git) | `..._final_v1_60fps.mp4` |
| Ukuran | 235,5 MiB (247 MB desimal) | 90,1 MB |
| Bitrate video | 50,5 Mbps | 18,6 Mbps |
| Audio | **Identik** (di-copy, bukan encode ulang) | **Identik** |
| Kegunaan | unggah ke YouTube (kualitas maksimum) | arsip, kirim, dibuka di HP |

Alasannya: YouTube meng-encode ulang setiap unggahan, jadi semakin tinggi
bitrate sumbernya semakin sedikit kerusakan yang tersisa. Untuk berbagi/arsip,
bitrate 18,6 Mbps pada konten yang sama sudah transparan dan jauh lebih praktis.

## Spesifikasi teknis (kedua versi sama)

- Kanvas 1080×1920 (9:16), 60 fps, H.264 High @ Level 4.2, yuv420p, `+faststart`
- Durasi 38,82 s (2.329 frame)
- Audio **AAC-LC 320 kbps** dalam MP4 — **bukan WAV/PCM**
- Loudness **-14,0 LUFS** integrated (ITU-R BS.1770-4, K-weighting + gating)
- **True peak -1,6 dBTP** (diukur dengan oversampling 4×), mono-fold -0,00 dB
- Tanpa BGM; hanya narasi + SFX prosedural

## Cara membuat ulang

```bash
cd KlikTahu-Video
pip install -r requirements.txt

python cinematic_engine.py --render --target-mb 235   # master (YouTube)
python cinematic_engine.py --render --target-mb 90 \
    --out build/KlikTahu_Short01_1080x1920_60fps.mp4  # delivery (Drive/arsip)
python cinematic_engine.py --audio-only               # hanya master audio .m4a

python tools/verify_video.py KlikTahu_Shorts_1080x1920.mp4
```
