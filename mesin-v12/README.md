# KlikTahu — Mesin Produksi Video (Shorts 1080×1920 & Long 16:9)

Repo ini adalah **mesin produksi** channel YouTube **KlikTahu**: fakta sains &
misteri bahasa Indonesia. Dari data episode (naskah VO + diagram) mesin
menghasilkan video jadi: gambar animasi 60 fps, audio narasi yang dirapikan,
efek suara sintetis, QC otomatis, sampai teks siap tempel untuk YouTube.

> **AI/agen baru yang membuka chat?** Baca **[AGEN.md](AGEN.md)** dulu — di situ
> ada memori jangka panjang proyek, status terakhir, resep episode baru, dan
> aturan yang tidak boleh dilanggar. Semua pekerjaan bisa dilanjutkan dari sana
> tanpa perlu chat lama.

---

## Aturan penting (pelajaran akun lama di-flag)

1. **Render video TIDAK dijalankan di GitHub Actions.** Render dilakukan lokal
   di sandbox agen / komputer sendiri lewat `tools/render_lokal.sh`.
   GitHub hanya untuk menyimpan kode + menjalankan uji ringan.
2. **MP4 tidak disimpan di repo maupun di Releases.**
3. **Repo ini tidak boleh menyimpan rahasia** (token, kunci API, `.env` asli).
4. Workflow di repo ini hanya uji `< 5 menit` tanpa render, tanpa jadwal cron.
5. Perubahan dikumpulkan: **satu commit bermakna per langkah**, jangan push
   beruntun berkali-kali dalam hitungan menit.

Rinciannya di [AGEN.md §14](AGEN.md) dan [docs/arsip/README.md](docs/arsip/README.md).

---

## Struktur repo

```
AGEN.md                    memori jangka panjang proyek (wajib diperbarui)
PUSTAKA.md                 indeks semua episode + judul & status rilis
LICENSE                    hak cipta (all rights reserved)
requirements.txt           pillow, numpy, imageio-ffmpeg — tidak ada lainnya
fonts/                     Poppins Bold/SemiBold/Medium/Regular + OFL.txt

render.py                  renderer Shorts (frame, kamera, transisi, HUD, finishing)
diagrams.py                primitif gambar + registry VISUALS + selftest
mesin_v11.py               paket motion "EDITOR" (tipografi kinetik, stiker, BEATS/SFX)
mesin_v11_epNN.py          modul adegan per episode (sc_*NN + tabel beat)
mesin_fx.py                lapisan FX 2026 (finishing sinematik, material, transisi)
mesin_util.py              preview_times, ink_report, sheet (montase)
process_audio.py           rapikan VO tanpa memotong isi + QC keutuhan
build_timeline.py          timeline.json + cek durasi MAXDUR
build_audio.py             menyusun VO terjadwal jadi satu trek
master_audio.py            master −14 LUFS + lapisan SFX (ducking) + limiter
sfx.py                     katalog 24 bunyi sintetis (numpy)
check_layout.py            audit tata letak/margin sebelum render
qc_mp4.py                  QC hasil akhir MP4

episodes/<slug>/           content.json · config.env · audio_raw/*.wav · METADATA.md
pustaka/<EpNN_Nama>/       SIAP_TEMPEL.md (judul, deskripsi, hashtag, tag)
long/mesin_long.py         mesin 16:9 (penyelarasan kata, komponen, kamera, bab, HUD)
long/render_long.py        CLI render video panjang
long/audio_long.py         master audio Long (VO + SFX)
long/<slug>/               content.json · config.env · visual.py · thumbnail.py · METADATA.md
analisis/                  mesin riset topik & metadata (v3-v6) + data hasil
tools/render_lokal.sh      render penuh di komputer sendiri / sandbox
docs/                      dokumen teknik, prompt proyek, manifest audio, atribusi
docs/arsip/                salinan workflow Actions lama (tidak aktif)
```

## Cara render

```bash
pip install -r requirements.txt

# Shorts — cek cepat dulu (audio, timeline, tata letak), tanpa render frame
tools/render_lokal.sh shorts ep49_bintang prep

# Shorts — render penuh (hasil di dist/)
tools/render_lokal.sh shorts ep49_bintang

# Video panjang 16:9
tools/render_lokal.sh long v02_laut_dalam
```

Setelan opsional: `CHUNKS=12` (potongan, menjaga pemakaian disk),
`JOBS=4` (proses paralel). Perkiraan waktu di 2 vCPU: Shorts ±0,6–0,9
detik/frame, Long ±0,22 detik/frame — jalankan sebagai proses latar
(±60–75 menit untuk satu Shorts).

## Uji

```bash
python mesin_v11.py                  # selftest paket motion v11
python diagrams.py                   # selftest semua visual adegan
python sfx.py                        # katalog bunyi -> build/sfx_katalog.wav
python analisis/mesin_v6.py --uji    # uji offline mesin analisis (v5/v6/pemeta/sapuan)
```

Semua uji di atas juga dijalankan otomatis oleh
[`.github/workflows/selftest.yml`](.github/workflows/selftest.yml) setiap push
ke `main` dan setiap Pull Request.

## Audio mentah tidak ada di repo

268 berkas WAV (192 MiB) sengaja **tidak** disimpan di sini supaya repo tetap
ringan dan akun aman. Daftar lengkap berkas + ukurannya ada di
**[docs/audio-manifest.md](docs/audio-manifest.md)**. Salinan aslinya ada di
arsip Google Drive `kliktahu.zip`; letakkan kembali di
`episodes/<slug>/audio_raw/` sebelum render (skrip render akan mengingatkan
kalau kosong).

## Hasil yang sudah ada

Daftar episode, judul, durasi, dan tautan videonya ada di
**[PUSTAKA.md](PUSTAKA.md)**.

## Lisensi & atribusi

Kode dan isi repo ini **hak milik pemilik channel KlikTahu** (all rights
reserved) — lihat [LICENSE](LICENSE). Komponen pihak ketiga diatur terpisah:
font Poppins (SIL OFL 1.1) dan citra lubang hitam M87* (EHT Collaboration,
CC BY 4.0) — lihat [docs/ATTRIBUSI.md](docs/ATTRIBUSI.md).
