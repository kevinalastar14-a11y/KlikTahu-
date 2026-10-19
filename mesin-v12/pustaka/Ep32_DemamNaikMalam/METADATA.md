# KlikTahu - Ep32 - Metadata + Analisis Kata Kunci
**Judul video:** Kenapa Demam Naik Malam?
**Tanggal produksi:** 21 September 2026 - **Durasi:** 123,3 s - 1080x1920 - 60 fps - VO pria (TTS Arena, voice-00), tanpa subtitle

---

## 1. Ringkasan temuan analisis v4 "Pemeta Peluang" (real-time, 21 Sep 2026)
**Metode:** pohon topik bercabang v4.2 (`analisis/pemeta_peluang.py`, 278 panggilan autocomplete live di
runner CI, 14 keluarga bercabang, 1.932 frasa bebas blokir) + metrik **skor_views**
`jml + kuat + yt*2 + vis*0,8 + niat*0,6 + sains*2 + jaring*2` (fokus potensi views, perintah user).

**Keluarga terpilih: demam & imun - skor_views 434,8 - peringkat #1 di antara keluarga SEGAR** (belum
pernah dibahas; total #4 setelah tiga topik yang sudah naik). Klaster permintaan terbesar (rencana seri
pohon): `kenapa anak demam malam`, `kenapa demam pagi hari`, `kenapa demam anak naik turun`,
`kenapa demam tidak sembuh2`, `kenapa demam tidak turun`. Alasan sudut "naik malam": (1) pertanyaan
paling spesifik & paling dicari orang tua; (2) jawaban mengejutkan (demam = strategi, bukan musuh) ->
share & komentar; (3) mekanisme bisa diperlihatkan dari nol (termostat, sitokin, gigil, keringat) ->
retensi; (4) evergreen musiman (peralihan cuaca).

Runner-up yang mengantre: hujan & awan (420,4), pusing & migrain (325,6), mimisan & hidung (315,8, NAIK).

---

## 2. Judul & deskripsi siap tempel (YouTube)

**Judul (pilih salah satu):**
1. Kenapa Demam Naik Malam?
2. Demam Naik Turun? Ini Maksudnya
3. Demam Itu Bukan Musuh - Ini Sainsnya

**Deskripsi (siap tempel):**
```
Kenapa demam selalu memuncak malam hari? Ini penjelasan paling sederhananya.

Jawaban singkat: demam bukan penyakit, tapi strategi tempur. Saat kuman masuk, sel imun melempar sinyal
sitokin ke hipotalamus (termostat tubuh) dan setelan suhu sengaja dinaikkan dari 37 ke 38+ derajat.
Suhu panas membuat kuman susah berkembang biak, sementara sel imun makin gesit. Puncaknya malam karena
hormon kortisol (peredam peradangan) turun ke titik terendah dan sitokin paling aktif. Menggigil =
pemanas darurat, keringat = radiator saat setelan diturunkan.

Perlu ke dokter: bayi di bawah 3 bulan demam 38 derajat, suhu di atas 40 derajat, atau demam lebih
dari 3 hari. Kejang demam pada anak 6 bulan-5 tahun menakutkan tapi umumnya jinak.

00:00 Demam puncaknya malam?
00:11 Termostat tubuh di otak
00:23 Sinyal sitokin naik ke otak
00:36 Panas = senjata tubuh
00:49 Gigil = pemanas darurat
01:02 Kenapa puncaknya malam?
01:16 Naik turun = perang bergelombang
01:30 Tanda harus ke dokter
01:44 Rangkuman

Ikuti KlikTahu untuk fakta sains & misteri tiap hari!
#demam #sains #kesehatananak #belajar
```

**Tag:** demam, kenapa demam naik malam, demam anak, demam naik turun, termostat tubuh, hipotalamus,
sitokin, kejang demam, kapan demam ke dokter, edukasi sains, klik tahu, fakta sains, kesehatan,
belajar sains, short edukasi

**Pin komentar:** Demam berapa derajat yang bikin panik di rumahmu? Tulis di komentar - nanti kita
bahas cara ukur suhu yang benar.

---

## 3. Peta adegan (waktu dari timeline.json, total 122,0 s)
| mulai | adegan | isi visual (paket v4+v5+v6+v7) |
|---|---|---|
| 0,0 | intro | malam (langit7), tokoh ngantuk + lower3 SI KAMU, termometer merambat naik |
| 10,7 | f1 | otak + hipotalamus diarsir scribble, dial setelan 36-40 naik, punch |
| 23,8 | f2 | flowpath sitokin naik ke otak, dive ke lokasi infeksi (cutaway), sel imun |
| 37,5 | f3 | panel dingin vs panas: kuman lesu, imun gesit (eq), stamp PANAS = SENJATA |
| 50,4 | f4 | tokoh gigil (eq pembuat panas), pembuluh menyempit + panah scribble, stamp |
| 63,4 | f5 | 4 tile pagi-siang-sore-malam + grafik suhu 24 jam, highlight puncak malam |
| 77,3 | f6 | termometer turun + keringat, donut obat 2-3 jam, punch BUKAN KALAH, stamp |
| 91,6 | f7 | 3 kartu tanda bahaya + ikon, stamp KE DOKTER!, pill kejang demam jinak |
| 105,5 | f8 | recap papan rangkuman 4 poin, tokoh senang, konfeti |
| 120,7 | outro | SEKARANG KAMU TAHU + CTA + sumber |

**Fakta inti:** hipotalamus menaikkan set point lewat PGE2 saat sitokin (IL-1, TNF, IL-6) datang;
gigil = produksi panas otot + vasokonstriksi kulit (meriang); malam: kortisol terendah + sitokin aktif
+ ritme sirkadian suhu; keringat = pembuangan panas; obat penurun panas bekerja 2-3 jam; kejang demam
umum 6 bulan-5 tahun dan umumnya jinak; ambang bahaya: <3 bulan +38, >40, >3 hari.

---

## 4. Sumber (dipakai naskah)
- Mayo Clinic - Febrile seizure (symptoms & causes), 2023
- Cleveland Clinic / Connecticut Children's - Fevers in children: when to worry
- healthdirect (AU) - Fever in children (ambang <3 bulan 38C, >40C, >2-3 hari)
- StatPearls - Fever (pyrogen, PGE2, set point hipotalamus)
- LibreTexts Medicine - Fever pathways (COX-2/PGE2)
- Torrinomedica / literatur sirkadian - kortisol rendah malam + sitokin peak (fenomena demam malam)

## 5. Catatan produksi
- Episode pertama yang topiknya dipilih otomatis oleh **analisis v4.2 skor_views** (bebas blokir
  "kentut dll" yang dihapus total dari sistem).
- Take-2: seluruh 10 klip VO direkam ulang (teks identik) + 8 patch presisi visual
  (bulan/label/stamp/panah/ikon dipindah agar nol tumpang tindih; durasi adegan mengikuti VO).
- 10 adegan = 10 klip VO (voice-00, id-ID) - paket mesin penuh: langit7, tokoh7 (ngantuk/mikir/pusing/
  happy), lower3, scribble, cutaway+dive, flowpath, eq, stamp x4, donut, punch, recap, konfetti,
  transisi flash/dive/speed/thud/auto/glint/bands/ambient/iris.
- QC lokal (take-2): process_audio 10/10 OK - build_timeline 123,3 s (sisa 16,7 dari MAXDUR) - check_layout
  bersih - build_audio "AUDIO OK" - master_audio OK.
