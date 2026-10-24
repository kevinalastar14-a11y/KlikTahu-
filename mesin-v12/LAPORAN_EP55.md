# LAPORAN EP55 — versi 3 (mesin v18 "Sprite Atlas")

**Judul:** Megalodon Bukan Hiu Putih Raksasa — Dan Kita Cuma Punya Giginya
**Berkas final:** `dist/KlikTahu_Ep55_Megalodon_v18.mp4`
**Format:** 1080×1920 · 60 fps · **102,76 s** · 6.166 frame · H.264 High yuv420p + AAC-LC 48 kHz stereo
**Ukuran:** 33,18 MB · **bitrate ~2,6 Mbps** · faststart
**Audio:** master telinga `KlikTahu_Ep55_Megalodon_audio.m4a` (voice-05 → rantai `vo_manusia.py`)
**Mesin:** v18 SPRITE ATLAS — 3.779 baris kode inti (inti 1.173 + dunia 1.152 + episode 651 +
renderer 298 + QC 330 + pustaka 175)

---

## 1. Permintaan yang harus dipenuhi, dan jawabannya

| Permintaan pemilik | Jawaban terukur |
|---|---|
| "render menjadi sangat cepat, tidak buang-buang waktu" | **4 m 00 s** penuh (v17: 24 m 52 s) = **6,2× lebih cepat** |
| "kamu buat sistem sendiri yang membuat render cepat" | arsitektur baru: sprite atlas + `np.take` + pipe x264; dijelaskan di `docs/MESIN_V18.md` |
| "1 video short wajib 2000 kode lebih, bukan omong kosong" | **3.779 baris** modul inti v18 (bukan komentar/placeholder) |
| "VO jangan digenerate lagi" | **tidak ada satu klip pun** yang dibuat ulang; master lama dipakai, korelasi QC 1,0000 |
| "VO yang disaring khusus untuk telinga manusia, tidak terpotong, clear" | master hasil `audio_telinga.py`: -14,4 LUFS · TP -1,6 dBTP · LRA 2,0 · 0 clipping |
| "lebih bagus di tingkat mutakhir" | sprite vektor anti-alias, gerak tubuh sinusoidal, tipografi stabilo, 8 scene digambar ulang |
| "hapus yang usang/jelek" | `build_v18/` uji dihapus, `.gitignore` diperbarui, berkas v18 lama tidak ditinggalkan |

---

## 2. Apa yang berubah dari v17 ke v18 (visual)

| Aspek | v17 | **v18** |
|---|---|---|
| Cara gambar | ulang seluruh adegan tiap frame | sprite dirakit sekali, ditempel per frame |
| Tubuh hiu | elips + tumpukan sirip | profil `catmull` + perut dari mask siluet (punggung berpunuk, pangkal ekor sempit) |
| Gerak berenang | sprite bergeser utuh | `swim()`: undulasi per kolom, amplitudo naik ke ekor |
| Langit | dua gradasi + kabut (muncul garis) | satu gradasi 5 stop, mulus tanpa batas |
| Kaustik | ubin 256 px terlihat sengkar | pola di-gather, memudar ke atas |
| Judul | kartu 2 baris keluar dari pelat | kartu rapi: kicker + 2 baris + stabilo kata kunci |
| Gigi | siluet berlekuk seperti "hantu" | kerucut satu apex + akar dua lobus + enamel |
| Encode | x264 fast, 77,75 MB | x264 **slow CRF 14**, 33,18 MB, SSIM 0,9936 |
| Loop | frame akhir ≈ frame awal (0,74) | fade 1 s ke latar intro → SSIM **0,9868** |

---

## 3. Delapan scene (timing dari audio, bukan tebakan)

| # | id | mulai | dur | isi visual | kartu |
|---:|---|---:|---:|---|---|
| 1 | intro | 0,00 | 10,65 | hiu 980 px menyeberang, halo fokus, deret gigi | HIDUP 24 METER / TERSISA CUMA GIGI |
| 2 | f1 | 10,65 | 11,29 | garis waktu 20 jt → 3,6 jt, hiu hantu pudar | 20 JUTA TAHUN, HILANG 3,6 JUTA LALU |
| 3 | f2 | 21,94 | 13,88 | angka 16,4 m, batang ukur 11 m, penyelam 1,8 m | 16,4 METER DARI 11 METER TULANG |
| 4 | f3 | 35,82 | 12,01 | dua siluet sebanding (putih gempal vs megalodon ramping) | BUKAN HIU PUTIH YANG DIPERBESAR |
| 5 | f4 | 47,83 | 16,40 | gigi raksasa di penggaris 18 cm, hujan gigi kecil | SATU HIU, PULUHAN RIBU GIGI |
| 6 | f5 | 64,23 | 12,66 | megalodon naik menyerang ekor paus, tanda gigitan | YANG DISERANG EKORNYA DULU |
| 7 | f6 | 76,89 | 17,59 | empat sebab kepunahan + panah populasi turun | RAKSASA KALAH OLEH PERUBAHAN |
| 8 | outro | 94,48 | 8,28 | hiu yang sama kembali, deret gigi, fade ke intro | GIGINYA MASIH ADA / HIUNYA TIDAK |

Batas scene dihitung dari jeda hening audio lalu diseimbangkan dengan DP
berbasis laju kata (138/158/179/152/218/158/205/95 karakter) — hasilnya cocok
±0,4 s dengan timeline v17, jadi VO tidak pernah bertabrakan dengan pergantian
scene.

---

## 4. Hasil QC (gerbang `qc_v18.py` — semua lulus)

```
berkas ada            33,18 MB
resolusi              1080x1920
fps                   60.0
video                 h264 High yuv420p · 6.166 frame · 102,76 s
audio                 1 track AAC 48 kHz stereo · -14,4 LUFS · TP -1,6 dBTP
korelasi vs master    1,0000 (selisih level +0,00 dB)  → audio TIDAK bergeser
loop (frame akhir)    SSIM 0,9868 · korelasi 0,9988    → frame akhir = frame awal
gambar vs mesin       SSIM 0,9934 (min 0,9909) dari 8 frame
bidang gelap          maks 3,0 %                       → tidak ada layar hitam
margin aman 40 px     tepi tajam maks 0,16 %           → teks tidak menyentuh tepi
faststart             moov @ 36 byte
HASIL: SEMUA BERSIH ✔
```

---

## 5. Kecepatan: dari mana 20 menit 52 detik itu hilang

| Pemborosan v17 | Biaya v17 | Perlakuan v18 |
|---|---:|---:|
| simpan 6.166 JPEG ke disk lalu baca lagi | ±2,5 menit | **0** (pipe rawvideo ke ffmpeg) |
| latar digambar ulang tiap frame | 6.166 × ~120 ms = 12,3 menit | **0,43 ms/frame** (salin sprite) |
| teks/kartu/label diraster ulang | 6.166 × ~20 ms = 2 menit | sprite di-cache (0,1 ms) |
| PNG/JPEG writer + I/O | 6.166 × 16 ms = 1,6 menit | tidak ada |
| undulasi tubuh | perlu raster ulang | `np.take` 0,6 ms |
| encode x264 | 552 s (slow) | 240 s total termasuk komposisi (slow CRF 14) |

Rincian teknis lengkap: `docs/MESIN_V18.md` §3 dan §6.

---

## 6. Berkas yang diserahkan

| berkas | isi |
|---|---|
| `dist/KlikTahu_Ep55_Megalodon_v18.mp4` | video final (33,18 MB) |
| `pustaka/Ep55_Megalodon/KlikTahu_Ep55_Megalodon_audio.m4a` | master VO telinga (dipakai apa adanya) |
| `pustaka/Ep55_Megalodon/KlikTahu_Ep55_Megalodon_thumb_utama.png` | thumbnail dari mesin v18 |
| `pustaka/Ep55_Megalodon/KlikTahu_Ep55_Megalodon_thumb_alt.png` | thumbnail alternatif (24 meter) |
| `pustaka/Ep55_Megalodon/KlikTahu_Ep55_Megalodon_lembar_pratinjau.jpg` | 8 frame berlabel |
| `pustaka/Ep55_Megalodon/METADATA.md` · `SIAP_TEMPEL.md` | judul, deskripsi, hashtag, tag |
| `mesin_v18_inti.py` · `mesin_v18_dunia.py` · `mesin_v18_ep55.py` | mesin (3.779 baris) |
| `render_v18.py` · `qc_v18.py` · `pustaka_v18.py` | renderer, gerbang QC, aset pustaka |
| `docs/MESIN_V18.md` | dokumen arsitektur + jebakan |

---

## 7. Yang TIDAK dilakukan (sengaja)

- **Tidak** generate VO baru — master telinga sudah ada dan dipertahankan (permintaan eksplisit).
- **Tidak** memakai musik; ambien laut + SFX tetap dari master.
- **Tidak** menurunkan resolusi/fps untuk mengejar kecepatan: justru encode naik ke `slow` CRF 14.
- **Tidak** mengklaim angka tanpa mengukur: setiap klaim di dokumen ini punya angka hasil QC/profil.
