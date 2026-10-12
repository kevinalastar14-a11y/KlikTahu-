# KlikTahu-

Proyek ini menghasilkan video pendek vertikal dengan motion design sinematik berwarna amber hangat, narasi bertahap, voice-over Bahasa Indonesia, serta sound effects sinkron tanpa musik.

Mulai dari dokumentasi proyek di [`KlikTahu-Video/README.md`](KlikTahu-Video/README.md). Untuk render lokal:

```bash
cd KlikTahu-Video
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python cinematic_engine.py
```

GitHub Actions berjalan manual saja. Tidak ada cron atau mekanisme penghindaran deteksi; lihat dokumentasi keamanan sebelum menjalankan workflow AI.
