# KlikTahu Cinematic Video Engine

Mesin pembuat **YouTube Short** (1080×1920, 60 fps) yang menghasilkan video
siap-unggah: latar aurora hidup, tipografi kinetik yang menyala **tepat saat
kata diucapkan**, kartu aturan, kurva retention, efek audio prosedural, dan
akun encoder x264 dengan target ukuran file.

Semua gambar dibuat dari kode — tidak ada stock footage, tidak ada BGM
berlisensi, tidak ada API berbayar.

---

## Hasil

| Item | Nilai |
|---|---|
| Kanvas | 1080 × 1920 (9:16, Shorts) |
| Frame rate | 60 fps (2.048+ frame) |
| Codec | H.264 High @ L4.2, yuv420p, faststart |
| Audio | AAC 320 kbps, stereo, ~-13,5 LUFS |
| Ukuran | **> 200 MB** (target 235 MB, dihitung dari durasi) |
| Durasi | ~34–40 detik |

## Struktur

```
KlikTahu-Video/
├── script_kliktahu.py     # naskah + arahan visual per beat (EDIT FILE INI untuk ganti isi)
├── cinematic_engine.py    # timeline, 7 tipe scene, transisi, encoder
├── visuals.py             # primitif gambar: gradien, sprite glow, teks kinetik, easing
├── audio_design.py        # SFX prosedural, ducking, limiter, normalisasi loudness
├── voice_over.py          # sintesis narasi (edge-tts) -> narration/
├── narration/             # voice-over per beat (01_hook.mp3, 02_choice.mp3, ...)
├── assets/fonts/          # Poppins (SIL Open Font License)
└── tools/
    ├── youtube_upload.py  # upload ke YouTube Data API v3
    ├── get_refresh_token.py
    └── verify_video.py    # cek resolusi/fps/codec/durasi/ukuran sebelum unggah
```

## Alur Produksi

```bash
pip install -r requirements.txt

# 1. (opsional) buat narasi. Butuh internet; narasi yang sudah ada di repo
#    dipakai apa adanya bila langkah ini dilewati.
python voice_over.py

# 2. uji visual cepat (1 detik per frame, langsung jadi PNG)
python cinematic_engine.py --still 1.2,9.0,29.3 --still-out build/stills

# 3. pratinjau gerak (setengah resolusi, CRF, 1 pass) — puluhan detik
python cinematic_engine.py --preview

# 4. render final: 1080x1920 @ 60 fps, target 235 MB
python cinematic_engine.py --render --target-mb 235

# 5. verifikasi & unggah
python tools/verify_video.py KlikTahu_Shorts_1080x1920.mp4
python tools/youtube_upload.py --privacy private
```

## Cara Kerja

**1. Timeline dari naskah.** `script_kliktahu.py` memuat beat: satu kalimat
narasi + satu komposisi visual. Durasi tiap beat = `lead_in + durasi narasi +
tail`. Bila file narasi belum ada, durasi diperkirakan dari panjang kalimat
sehingga video tetap bisa dirender.

**2. Sinkronisasi kata.** Kata pada teks layar dipetakan 1:1 ke kata narasi
(mulai dari `vo_from`). Setiap kata punya sprite sendiri, jadi ia bisa muncul,
membesar, menyala, atau dicoret secara mandiri — sorotan selalu jatuh tepat
saat kata diucapkan. Mesin akan menolak render bila jumlah kata tidak cocok.

**3. Tujuh tipe scene** (`countdown`, `choice`, `statement`, `retention`,
`rule`, `climax`, `outro`) — masing-masing punya tata letak dan animasi sendiri,
sehingga tidak ada dua beat yang terlihat sama.

**4. Latar tidak pernah diam.** Empat blob aurora bergerak mengikuti Lissajous,
bokeh mengapung, 64 partikel melayang, grain film berdenyut per frame. Tidak ada
frame yang identik — inilah yang menjaga retensi.

**5. Audio.** Voice-over di-EQ (buang rumble, dorong kejelasan 3 kHz), SFX
whoosh/impact/riser/tick/pop disintesis prosedural, lalu SFX di-*duck* 62% di
bawah narasi, di-soft-limit, dan dinormalisasi ke ~-13,5 LUFS (standar YouTube).
Tanpa BGM sama sekali.

**6. Ukuran file.** Encoder menghitung bitrate dari target MB dan durasi nyata
(`(target × 8 − audio) ÷ durasi`), lalu 1 pass ABR (di ~48 Mbps kualitas sudah
transparan) atau 2 pass bila butuh presisi ukuran. `--crf` tersedia bila lebih
suka kualitas konstan.

## Otomasi (GitHub Actions)

`.github/workflows/generate_video.yml` menjadwalkan render Senin & Kamis 09:17
WIB, menyimpan MP4 sebagai artifact 14 hari, dan bisa mengunggah ke YouTube
(manual, `workflow_dispatch` + input `upload`). Secret yang dibutuhkan hanya
untuk upload: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.

## Mengubah Isi Video

Cukup edit `script_kliktahu.py`. Contoh menambah beat aturan keempat:

```python
dict(
    key="rule4", chapter="SOLUSI", scene="rule", rule_no="04",
    vo="Empat. Akhiri dengan pertanyaan.",
    lines=["AKHIRI DENGAN", "PERTANYAAN."],
    vo_from=1, persist=["PERTANYAAN."],
    size=104, anchor_y=1000, accent_color=CYAN,
    lead_in=0.20, tail=0.60, sfx=("pop",),
),
```

Lalu jalankan `python voice_over.py --only rule4` (atau biarkan mesin memakai
estimasi durasi) dan render ulang.

## Font

Poppins oleh Indian Type Foundry, lisensi SIL Open Font License 1.1
(`assets/fonts/OFL.txt`) — aman untuk penggunaan komersial.
