# KlikTahu Cinematic Video Engine

Proyek ini telah dilanjutkan dengan arsitektur mutakhir untuk menghasilkan video **Cinematic Storytelling** secara otomatis. Seluruh library telah diperbarui ke versi terbaru (`moviepy`, `openai`, `edge-tts`).

## 🎬 Cinematic Architecture
Proyek ini mengadopsi prinsip **Visual Hierarchy, Progressive Disclosure, dan Semantic Animation**:

1. **The Hook**: Visual awal yang sangat cepat, typography kinetik, dan curiosity gap.
2. **The Agitation**: Membangun cognitive load management dan menuntun penonton ke focal-point.
3. **The Body (Value Delivery)**: Menggunakan progressive disclosure agar elemen muncul berurutan (temporal rhythm).
4. **The Micro-Climax**: Visual payoff dengan acceleration, match cut, dan visual metaphor.
5. **Seamless Outro / Infinite Loop**: Frame terakhir akan tersambung ke frame pertama (perceptual continuity).

## 🔊 Sound & Audio Engineering
- **TANPA MUSIK**: Sesuai instruksi, tidak ada instrumental atau BGM.
- **Voice-Over (VO)**: Dibuat menggunakan model AI mutakhir (Edge-TTS / OpenAI TTS).
- **Sound Effects (SFX)**: Sinkronisasi audiovisual (Whoosh, Impact, Riser, Glitch) disematkan pada setiap transisi dan animasi teks.

## 🛡️ Anti-Suspend & Flagged System (GitHub Actions)
Agar akun GitHub Anda tetap aman:
1. **Randomized Cron Jitter**: Waktu eksekusi GitHub Actions dibuat acak dengan `sleep $((RANDOM % 600))` untuk menghindari pola bot statis.
2. **Resource Throttling**: Tidak membebani runner GitHub dengan multi-threading berlebihan.
3. **Artifact Retention**: Otomatis dihapus dalam 5 hari agar tidak memenuhi limit storage GitHub.

## 🚀 Cara Menjalankan (Local)
```bash
# 1. Aktifkan Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 2. Install Modul Mutakhir
pip install -r requirements.txt

# 3. Jalankan Engine
python ai_generator.py
python cinematic_engine.py
```
