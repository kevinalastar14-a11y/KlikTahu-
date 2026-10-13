# Deliverables — KlikTahu Short #01

Semua hasil produksi short ini, lengkap dengan lokasi dan spesifikasinya.

## Tautan GitHub

| Apa | Tautan |
|---|---|
| Branch kerja | https://github.com/kevinalastar14-a11y/KlikTahu-/tree/arena/97a5a3a6-kliktahu |
| **Preview 720p (bisa diputar langsung di GitHub)** | https://github.com/kevinalastar14-a11y/KlikTahu-/blob/arena/97a5a3a6-kliktahu/KlikTahu-Video/preview_720p.mp4 |
| Kode mesin video | https://github.com/kevinalastar14-a11y/KlikTahu-/tree/arena/97a5a3a6-kliktahu/KlikTahu-Video |
| Naskah & arahan visual | https://github.com/kevinalastar14-a11y/KlikTahu-/blob/arena/97a5a3a6-kliktahu/KlikTahu-Video/script_kliktahu.py |
| Catatan rilis (release) | https://github.com/kevinalastar14-a11y/KlikTahu-/releases/tag/short-01-v1 |
| Jalankan render di GitHub (Actions) | https://github.com/kevinalastar14-a11y/KlikTahu-/actions/workflows/generate_video.yml |

### Di mana file video 247 MB-nya?

GitHub **menolak berkas > 100 MB** di dalam repositori, dan sandbox produksi hanya
bisa mengunggah lewat `api.github.com` (host `uploads.github.com` yang dipakai
GitHub untuk lampiran rilis diblokir). Karena itu master disediakan lewat
**GitHub Actions**, yang merender di server GitHub sendiri:

1. Buka <https://github.com/kevinalastar14-a11y/KlikTahu-/actions/workflows/generate_video.yml>
2. **Run workflow** → pilih branch `arena/97a5a3a6-kliktahu` → **Run workflow**
3. Setelah selesai (±10–20 menit), unduh **Artifact `kliktahu-short`** —
   di dalamnya ada `KlikTahu_Shorts_1080x1920.mp4` (235,5 MiB, siap unggah ke YouTube).
   Artifact disimpan 14 hari.

Video yang bisa langsung diputar tanpa unduhan ada di `KlikTahu-Video/preview_720p.mp4`
(di-commit ke repo, diputar inline oleh GitHub), dan versi delivery 90 MB ada di
Google Drive di bawah ini.

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
