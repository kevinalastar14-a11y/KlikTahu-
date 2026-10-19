# KlikTahu - Ep34 - Metadata + Analisis Kata Kunci
**Judul video:** Kenapa Mimisan? Jangan Tengadah Dulu
**Tanggal produksi:** 21 September 2026 - **Durasi:** 138,6 s - 1080x1920 - 60 fps - VO pria (TTS Arena, voice-00), tanpa subtitle

---

## 1. Ringkasan temuan analisis (21 Sep 2026)
**Keluarga terpilih: mimisan & hidung - skor_views 315,8 - satu-satunya kelas berat yang NAIK**
pada pemetaan terakhir (pusing & migrain 325,6 lebih tinggi tapi datar; kulit 296; megalodon
260). Alasan sudut "kenapa mimisan": (1) kebiasaan keliru yang diwariskan (tengadah) = koreksi
miskonsepsi -> komentar dan share; (2) takut darah universal tapi kasusnya jinak -> penonton
bertahan sampai "angka menenangkan"; (3) P3K 4 langkah mudah dibayangkan -> disimpan sebagai
video "penyelamat"; (4) audiens orang tua muda (anak paling sering) -> foot2 arahan simpan-
bagikan.

Antrean berikutnya: pusing & migrain (325,6), kulit (296), megalodon (260, fakta terkunci).

---

## 2. Judul & deskripsi siap tempel (YouTube)
Lihat: `pustaka/Ep34_Mimisan/SIAP_TEMPEL.md` (ASCII-only, siap salin).

---

## 3. Bab video (dari timeline.json, total 138,64 s)
| Waktu | Adegan | Isi |
|-------|--------|-----|
| 0:00 | intro | Hidung menetes darah - tenang, ini sains |
| 0:11 | f1 | Pleksus Kiesselbach: 4 pembuluh bertemu, selaput tipis, 9/10 |
| 0:30 | f2 | 4 pemicu: AC kering, colek hidung, flu/alergi, meniup keras |
| 0:47 | f3 | Tengadah = mitos: darah ke tenggorokan, mual, tak berhenti |
| 1:01 | f4 | Cara benar: duduk, tunduk, cubit lunak 10 menit, kompres dingin |
| 1:18 | f5 | Angka menenangkan: 9/10 dari titik depan, mayoritas jinak |
| 1:31 | f6 | Cegah: vaselin tipis/semprot salin, kamar lembap, kuku pendek |
| 1:46 | f7 | Batas ke dokter: 2x10 menit, banyak+pusing, trauma kepala, harian |
| 2:03 | f8 | Rangkuman 4 poin |
| 2:15 | outro | CTA + sumber |

---

## 4. Fakta terkunci (sumber di outro: KidsHealth, TeachMeSurgery, Lecturio, Medanta)
- **Pleksus Kiesselbach / Little's area** (Little 1879, Kiesselbach 1884): septum naso
  antero-inferior; anastomosis 4-5 arteri (etmoidalis anterior dan posterior, sfenopalatina,
  palatina mayor, septal labialis superior); ~90% mimisan berasal dari sini; mukosa tipis dan
  langsung terpapar udara kering; tersering anak/dewasa muda.
- **P3K benar:** duduk, kepala sedikit tunduk; cubit bagian LUNAK tepat di bawah tulang
  10 menit penuh tanpa dilepas; napas mulut; kompres dingin membantu (vasokonstriksi);
  belum berhenti -> ronde kedua 10 menit.
- **Tengadah = mitos:** darah mengalir ke tenggorokan -> mual/muntah -> jumlah darah tak
  terlihat -> pendarahan tak tertangani.
- **Ke dokter/UGD:** >20 menit, darah banyak/lemas/pucat, setelah trauma kepala, peminum
  pengencer darah, kambuh hampir tiap hari.
- **Cegah:** vaselin tipis/semprot salin, kelembapan kamar, potong kuku anak, jangan colek
  hidung.

---

## 5. Produksi
- Paket mesin **v4+v5+v6+v7+v8** (kisi, ukur, skala, detail, slider, hitung, tangga, sorot-
  cincin) - visual: intro_mimisan, anatomi, penyebab, tengadah, carabenar, angka, cegah,
  batas34, rangkuman34.
- VO: 10 klip voice-00, SPEED per adegan 1,08-1,13 (intro 1,12, outro 1,13); lead_in 0,3 s.
- **Patch permanen baru:** `process_audio.py` kini memberi ekor hening minimum 0,15 s per klip
  (apad) - menutup QC "ekor terpotong" intro/outro di build_audio (akar kegagalan run 46).
- QA sebelum render: tinta `render_frame` maks 895 (ambang 6.000); f4 didesain ulang (ukur+
  label menumpuk -> tangga + pil berurutan); `check_layout` bersih 10/10 adegan.
- Audio master: RMS -19,9 dBFS, puncak -2,2 dBFS, 0 clipping; total pipeline 138,6 s
  (MAXDUR 140, sisa 1,4 s).
- Rilis: `KlikTahu_Ep34_Mimisan-47` (run 47, 21 Sep 2026 17:02 UTC); run 48 menambahkan aset
  METADATA.md.
