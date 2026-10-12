# KlikTahu — Cinematic Storytelling Engine

Mesin video pendek vertikal yang melanjutkan konsep awal proyek menjadi satu cerita visual yang utuh: **satu titik fokus berkembang menjadi informasi yang tertata, lalu kembali ke frame pembuka.** Art direction tetap hangat—amber, kuning madu, dan burnt orange di atas cokelat gelap. Tidak ada neon, aset stok, atau transisi dekoratif.

## Struktur cerita

Urutan narasi selalu dipertahankan:

1. **The Hook** — “Semua sekaligus?” membuka curiosity gap dengan satu elemen fokus.
2. **The Agitation / The Problem** — elemen fokus berkembang menjadi tumpukan judul, angka, dan penjelasan yang berebut perhatian.
3. **The Body / The Value Delivery** — tiga langkah dibuka satu per satu: satu ide, langkah berikutnya, lalu jeda.
4. **The Micro-Climax** — ketiga langkah tersambung menjadi satu alur, sehingga informasi berubah menjadi pemahaman.
5. **Seamless Outro / The Infinite Loop** — alur menyusut kembali ke titik fokus dan pertanyaan pembuka. Frame awal dan akhir dirancang sama.

Pergerakan memiliki fungsi naratif: tumpukan terurai menjadi kartu, kartu menjadi jalur, lalu jalur kembali menjadi titik fokus. Mask transisi mengikuti bentuk elemen yang sedang berubah; tipografi dan kartu memakai gerakan singkat yang terkendali, lalu diberi waktu untuk dibaca. Parallax dan perubahan framing sangat halus agar fokus tetap pada pesan.

## Audio: voice-over dan SFX saja

- **Tidak ada musik, BGM, soundtrack, beat, instrumen, atau nada latar.**
- Voice-over Bahasa Indonesia menjadi lapisan utama. Klip dibagi per bagian agar mudah disejajarkan dengan visual.
- Sound design dibuat secara prosedural dari Foley non-tonal: soft click untuk reveal, air sweep untuk perpindahan, tick untuk langkah yang tersambung, dan muted impact untuk payoff.
- Tekstur ambience berupa noise udara yang sangat pelan dan tidak bernada—bukan musik atau drone.
- SFX diturunkan saat voice-over berbicara; campuran diakhiri dengan fade lembut.

Klip voice-over contoh berada di `audio/vo_*.wav`. Semuanya dapat diganti melalui generator AI atau diganti dengan rekaman narator sendiri; nama file harus mengikuti daftar scene yang dijelaskan di bawah.

## Modul

Versi PyPI dipatok ke rilis stabil terbaru yang dicek pada **12 Oktober 2026**:

- Pillow 12.3.0 — tipografi dan komposisi frame.
- NumPy 2.4.6 — background procedural dan sound design non-tonal.
- imageio-ffmpeg 0.6.0 — FFmpeg terbundel untuk encoding H.264/AAC; tidak perlu mengubah policy ImageMagick atau memasang binary sistem secara manual.
- OpenAI Python SDK 3.29.0 — opsional untuk pembuatan naskah dan TTS melalui API.

Versi Python yang disarankan: **3.12**.

## Menjalankan secara lokal

```bash
cd KlikTahu-Video
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Render film 1080 × 1920, 30 fps
python cinematic_engine.py

# Salinan review 540 × 960, 12 fps
python cinematic_engine.py --preview
```

Output master: `KlikTahu_Cinematic.mp4`. Background, card, garis, glow lembut, dan efek suara dibentuk oleh kode; render normal tidak mengunduh aset stok.

### Menggunakan model AI (opsional)

Tidak ada permintaan jaringan atau biaya API pada render default. Jika ingin membuat cerita serta suara baru, berikan API key hanya melalui environment variable/secret—jangan taruh token di kode, commit, log, atau chat:

```bash
# OPENAI_API_KEY must already be available in your protected shell environment.
python ai_generator.py --ai --voiceover --topic "Topik video"
python cinematic_engine.py
```

Model teks default diatur sebagai `gpt-6-astra`, TTS `gpt-4o-mini-tts`, dan suara `echo` (maskulin, santai, dan tegas). Ketersediaan model bergantung pada akun/API; pilih model yang tersedia dengan `OPENAI_MODEL`, `OPENAI_TTS_MODEL`, dan `OPENAI_TTS_VOICE`. Pembuatan naskah dan TTS hanya terjadi ketika flag `--ai`/`--voiceover` dipakai secara eksplisit.

Untuk membuat ulang suara saja dari `story.json`:

```bash
python ai_generator.py --voiceover
```

Klip hasilnya: `audio/vo_hook.wav`, `vo_agitation.wav`, `vo_body_1.wav`, `vo_body_2.wav`, `vo_body_3.wav`, `vo_micro_climax.wav`, dan `vo_outro.wav`. Render tetap dapat berjalan tanpa klip tersebut, tetapi hasilnya tentu tidak memiliki narasi; SFX non-musikal tetap dibuat.

## GitHub Actions dan keamanan akun

Workflow `.github/workflows/generate_video.yml` **hanya berjalan lewat `workflow_dispatch`**. AI generation juga opt-in. Workflow memakai izin `contents: read`, tidak mengubah repo, tidak melakukan commit/push, dan menyimpan artifact selama lima hari.

Tidak ada cara yang dapat menjamin akun GitHub pasti tidak pernah ditandai atau disuspend. Karena itu proyek ini tidak memakai cron, random delay/jitter, penyamaran aktivitas, atau trik untuk menghindari deteksi. Gunakan Actions sesuai Terms of Service, batasi pemicu yang tidak diperlukan, simpan secret dengan benar, dan tinjau penggunaan API/biaya sebelum memilih `use_ai`.

## Pemeriksaan

```bash
python -m unittest discover -s tests -v
```
