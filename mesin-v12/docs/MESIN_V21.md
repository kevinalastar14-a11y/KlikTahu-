# MESIN v21 — gaya "KERTAS" (meniru video short lama KlikTahu, mutu dinaikkan)

Dokumen ini menjelaskan mesin gambar ke-21. Tujuannya satu: **bahasa visual video
short lama KlikTahu ditiru, tetapi seluruh isi dan mutunya dinaikkan** — kecuali
resolusi yang tetap 1080x1920 @ 60 fps sesuai standar produksi.

Berkas:

| berkas | isi |
|---|---|
| `mesin_v21_kertas.py` | pustaka visual: palet, latar kertas, kartu, teks, ilustrasi, komposisi beranimasi |
| `mesin_v21_ep58.py` | episode 58 "Ikan yang Seharusnya Punah 66 Juta Tahun Lalu" (9 babak) |
| `mesin_v21_musik.py` | lapisan musik latar + ducking otomatis |
| `pustaka_v21.py` | thumbnail, SRT, METADATA, SIAP_TEMPEL, fakta & sumber |
| `render_v20.py` | renderer dipakai bersama (sudah menerima nama modul penuh) |
| `qc_v20.py` | QC 23 butir (sudah menerima nama modul penuh) |

---

## 1. Hasil pengukuran video acuan

Acuan: `Megalodon Masih Hidup Giginya yang Menjawab.mp4` (video short lama kanal),
diunduh lewat konektor Google Drive ke `google_drive/`.

| aspek | nilai terukur |
|---|---|
| durasi | 144,03 s |
| resolusi / fps | 240x426 · 30 fps (H.264 Main, 58 kb/s, total 190 kb/s) |
| audio | AAC 44,1 kHz stereo 127 kb/s, RMS −14,4 dBFS, hening 14,7 % |
| latar | krem hangat rata-rata **(219, 214, 206)** + gumpalan & cincin kertas |
| palet | tinta navy, coral **#CC4E38**, teal, emas, kertas krem |
| tipografi | Poppins Bold, headline 3 baris huruf besar, satu kata distabilo coral |
| struktur | tab "FAKTA n/7" di atas, kartu ilustrasi besar, angka besar di bawah |
| ritme | ganti babak tiap **±10 s** (median), gerak halus 60 % frame |
| HUD | merek kiri atas, badge kategori kanan atas, bar progres segmen di bawah |

## 2. Yang ditiru, yang dinaikkan

| aspek | acuan | v21 |
|---|---|---|
| resolusi | 240x426 (0,1 MP) | **1080x1920 (2,1 MP)** |
| fps | 30 | **60** |
| bitrate video | 58 kb/s | **±5 Mb/s** (CRF 15) |
| tepi ilustrasi | bergerigi (kompresi berat) | vektor 2x supersampling, halus |
| durasi | 144 s (di atas batas Shorts 3 menit → rawan) | **124,6 s** (aman) |
| naskah | klaim tanpa sumber | 9 babak, tiap angka dapat dilacak (sumber di layar) |
| audio | VO + hening total | VO + musik latar −42 dB RMS, ducking 4,5 dB saat VO |
| koreksi mitos | tidak ada | 2 babak (fosil hidup, leluhur langsung) |
| sudut lokal | tidak ada | Manado / *Latimeria menadoensis* |

## 3. Palet & zona tata letak

```
KERTAS  (223,217,207)   KARTU  (249,246,239)   KARTU_2 (240,236,227)
TINTA   (26,40,55)      TINTA_2 (76,90,103)    TINTA_3 (128,139,149)
CORAL   (204,78,56)     NAVY (30,61,92)        TEAL (32,129,116)
GOLD    (222,160,34)    LANGIT (152,197,219)   PASIR (212,187,139)
```

Zona tetap (px, kanvas 1080x1920) — dikunci di `mesin_v21_kertas.Z`:

| zona | y | isi |
|---|---|---|
| HUD | 0–118 | merek + badge kategori |
| tab fakta | 170 | "FAKTA n/7" + garis putus |
| headline | 236 | 2–3 baris, 84–92 px |
| kartu ilustrasi | 545–1525 | satu ilustrasi besar per babak |
| angka/panel | 1590–1830 | angka besar + satuan + keterangan |
| sumber | 1836 | baris sumber kecil |
| progres | 1878 | 7 segmen |

Aturan penting: **isi strip 1590–1830 selalu ada** (angka besar, panel kertas, atau
stiker). Versi pertama menyisakan ±400 px kosong di bawah; itu yang membuat frame
terlihat belum jadi (jebakan 22 di `docs/MESIN_V20.md`, versi terang).

## 4. Primitif yang tersedia

```python
import mesin_v21_kertas as K

K.kertas_dasar()            # latar 1080x1920 (cache)
K.Komposisi(kategori=..., fakta=n)   # dasar + hud + tab + sumber
komp.kartu(x, y, w, h, r, isi, t0, dur)      # kartu berbayang
komp.teks(t, x, y, warna, size, font, t0)    # sprite teks beranimasi
komp.tambah(spr, x, y, t0, dur, anim)        # anim: pop/turun/kiri/tulis/fade
komp.goyang(spr, x, y, t0, amp, lam, fase)   # gerak halus terus-menerus
komp.dinamis.append(fn)                      # gambar manual per frame
komp.frame(t_lokal)                          # -> np.uint8 (1920,1080,3)

K.ikan(w, h, warna, ...)    K.manusia(h)      K.kolom_laut(w, h)
K.peta(w, h)                K.sirip(w, h, "lobed"|"ray")
K.koran(w, h)               K.termometer()    K.kaca_pembesar()
K.telur_embrio()            K.grafik_batang() K.garis_waktu()
K.stiker(t, jenis, size, rot)   K.pil(t, isi, warna, size, ...)
K.tab_fakta(n, total)       K.highlighter_spr(w, h)   K.kilau(k, t, t0)
```

## 5. Jebakan baru (jangan diulang)

23. **`blit()` membagi 256 (`>>8`), bukan 255.** Piksel alpha 0 tetap berubah satu
    tingkat warna, jadi setiap sprite tampil sebagai bayangan segi empat samar di
    atas kertas terang. Sudah diperbaiki di `mesin_v18_inti.blit()`; ini juga
    memperhalus semua mesin lama, hanya tidak terlihat di latar gelap.

24. **Gerak beberapa piksel harus sub-piksel.** Goyangan ikan 8 px bisa jatuh pada
    posisi bulat yang sama beberapa frame berturut-turut → layar benar-benar beku
    (QC "ada gerak" = 0,00). Pakai `K.tempel_sub()` untuk sprite yang bergerak.

25. **Δ rata-rata seluruh layar bukan ukuran gerak untuk gaya terang.** Bidang krem
    luas membuat Δ global 0,1 walau jelas bergerak. QC v21 memakai tambahan
    **Δ maksimum per kotak 54x54 px** (ambang 1,2).

26. **Stabilo harus digambar sebelum teksnya.** Urutan salah = teks tertutup
    highlighter. Posisi dan ukurannya **wajib** diukur dari mask kata itu sendiri
    (`K.teks(kata, ...)`, lalu `ys.max() - ys.min()` = tinggi kapital), bukan dari
    `size`: `_pas_judul()` mengecilkan tiap baris berbeda, jadi stabilo berbasis
    `size` bisa meleset 20–30 px dan berubah menjadi garis bawah.
    Blok stabilo juga harus **lebih tinggi dari huruf** (≈1,5 × kapital, karena
    `highlighter_spr()` menyisakan margin 10 % atas-bawah di dalam sprite).
    Kalau tingginya pas setinggi huruf, glif tebal Poppins menutupi seluruh blok
    dan yang terlihat hanya serpihan coral di bawah kata.

27. **Jangan menumpuk teks di atas tangkapan layar untuk thumbnail.** Sisa elemen
    dari dalam video (stiker, angka babak) ikut terbawa. Thumbnail v21 dirakit
    ulang dari primitif.

28. **Baris panjang harus dibungkus otomatis.** `I.wrap()` dipakai dengan pengecilan
    ukuran bertahap; teks 80+ karakter pernah menembus tepi kartu.

29. **`tempel_sub()` tidak boleh menempel sprite yang sama 4× dengan bobot mentah.**
    Empat tempelan berbobot 1/4 menghasilkan cakupan 0,68 (bukan 1), jadi sprite
    tampak pucat dan latar menembus: kartu navy CTA terbaca abu-abu (85,108,129)
    alih-alih (30,61,92). Bobot harus diubah menjadi alpha berurutan
    (`k / sisa`, `sisa -= k`) supaya totalnya 1.

30. **`kartu()` mengembalikan sprite + bantalan 34 px.** Kalau sprite itu ditempel
    lewat `komp.goyang()`/`blit()` langsung, koordinatnya harus dikurangi 34
    (`x-34, y-34`); kalau tidak, badan kartu meleset 34 px ke bawah dan menutupi
    judul di dalamnya. `komp.kartu()` sudah menangani ini otomatis.

31. **Snapshot `self.basis` di `Komposisi.__init__` membuang HUD.** Watermark, tab,
    dan sumber digambar episode setelah `Komposisi` dibuat; basis harus *lazy*.

32. **`ffmpeg` tidak ada di PATH sandbox.** `render_v20.ffmpeg()` sudah jatuh ke
    `imageio_ffmpeg.get_ffmpeg_exe()`; untuk perintah manual pakai
    `/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2`.


## 6. Alur produksi episode v21

```bash
# 1. naskah + tata letak (durasi cadangan)
KT_SEMENTARA=1 python3 mesin_v21_ep58.py          # -> build_v21/pratinjau/_lembar.jpg

# 2. VO pria Indonesia, satu klip per babak  -> audio/voNN/sumber/NN.mp3
#    (lewat generate_speech, voice-01)

# 3. campur + master
python3 mesin_v20_suara.py --episode mesin_v21_ep58 \
        --dari-klip audio/vo58/sumber \
        --keluar keluaran/KlikTahu_Ep58_audio.m4a --target-lufs=-14
python3 mesin_v21_musik.py --level -24        # campuran_musik.wav
python3 -c "import mesin_v20_audio as A; A.master('audio/vo58/campuran_musik.wav',
            'keluaran/KlikTahu_Ep58_audio.m4a')"

# 4. render 1080x1920 @ 60 fps
python3 render_v20.py --episode mesin_v21_ep58 \
        --keluar keluaran/KlikTahu_Ep58_Coelacanth_v21.mp4 \
        --audio keluaran/KlikTahu_Ep58_audio.m4a --jobs 2 --preset slow --crf 15

# 5. QC 23 butir
python3 qc_v20.py keluaran/KlikTahu_Ep58_Coelacanth_v21.mp4 --episode mesin_v21_ep58 \
        --audio keluaran/KlikTahu_Ep58_audio.m4a --json build_v21/qc.json

# 6. paket publikasi
python3 pustaka_v21.py --episode mesin_v21_ep58 --slug Ep58_Coelacanth \
        --video keluaran/KlikTahu_Ep58_Coelacanth_v21.mp4 \
        --audio keluaran/KlikTahu_Ep58_audio.m4a
```

Hasil akhir **tidak masuk repo**: MP4, M4A, dan thumbnail diunggah ke Google Drive
(folder `KlikTahu_Produksi/Shorts/...`). Repo hanya menyimpan mesin, naskah, klip VO,
dan teks metadata — sesuai `AGEN.md` §14.

## 7. Biaya render (terukur di sandbox 2 inti)

| tahap | waktu |
|---|---|
| frame mesin (v21) | ±35 ms/frame/inti (28 fps/inti) |
| 7.478 frame, 2 proses, preset slow, CRF 15 | ±5,5 menit |
| audio (9 klip → campur → musik → master) | ±1 menit |

Rasio aman untuk perencanaan: **1 detik video akhir ≈ 2,7 detik render** di 2 inti.


---

## 8. Ilustrasi 2D realistis & motion graphics (ronde 3)

Keluhan pemilik: *"tidak realistis dalam 2D, ini sangat penting karena penonton bisa
membayangkannya"* dan *"banyak elemen tidak beraturan"*. Dua jawaban terpisah:

### 8.1 `mesin_v21_real.py` — isyarat yang membuat 2D terbaca sebagai benda nyata
Bukan menambah detail, tetapi menambahkan isyarat persepsi:

| isyarat | implementasi | kenapa penting |
|---|---|---|
| satu sumber cahaya (kiri-atas) | semua gradasi, rim light, spekular, bayangan mengikuti arah yang sama | otak membaca konsistensi arah cahaya sebagai bentuk 3D |
| counter-shading | punggung gelap → perut lebih terang, pita peralihan mengikuti bentuk badan | pola universal hewan air; tanpa ini bentuk terbaca datar |
| oklusi di sambungan | gelap tipis di pangkal setiap sirip + bayangan kontak | benda "menempel" bukan "mengapung"/"digunting" |
| kedalaman tiga lapis | latar berkabut + subjek + partikel depan (ukuran/kecepatan beda) | memberi skala ruang, bukan bidang datar |
| anatomi benar | 8 sirip, ekor tiga cuping membulat, mulut terbuka ke bawah, mata besar | penonton yang tahu ikannya langsung percaya |

Contoh terukur: `R.ikan_real()` menyusun ekor, dua sirip punggung, sirip dubur,
sirip dada & perut sebagai BENTUK TERPISAH (bukan satu siluet), lalu badan di
atasnya. Siluet tunggal selalu terlihat seperti guntingan kertas karena tidak ada
oklusi antar-bagian.

### 8.2 `mesin_v21_panggung.py` + grid tata letak — menghapus "tidak beraturan"
- Sembilan panggung (`laut`, `umur`, `temuan`, `nama`, `peta`, `sirip`, `mitos`,
  `ancaman`) semuanya menggambar di dalam kotak yang sama `BOX=(56, 556, 968, 816)`.
- Slot tetap: HUD 40–118 · tab 122–218 · judul 236–520 · panggung 556–1372 ·
  caption 1392 · angka 1476 · keterangan 1640 · sumber 1836.
- Judul dipusatkan vertikal di slotnya; stabilo diukur dari mask kata; caption satu
  baris dengan ukuran font menyusut otomatis agar selalu muat.
- Angka memakai **count-up** dengan lebar digit dikunci (tidak bergeser saat naik).
- Gerak panggung dihitung dari waktu (`Panggung.gambar`, `IkanBerenang`), jadi
  deterministik untuk render paralel.

### 8.3 Performa
| bagian | sebelum | sesudah | cara |
|---|---|---|---|
| panggung 940x860 | 79 ms/frame | 24 ms/frame | lapis gerak digambar ½ resolusi lalu diperbesar |
| babak umur (frame ke-2 dst.) | 451 ms | 86 ms | latar statis di-cache (`_latar`), ikan berskala tidak bertumpuk |
| seluruh video (7.823 frame, 2 proses) | — | ±5 menit | — |

### 8.4 Jebakan baru (lanjutan penomoran)
33. **Intensitas cahaya 0..1, bukan 0..255.** `rim * 255` membuat tepi badan
    menjadi PUTIH pekat (terlihat sebagai pita putih melintang di punggung).
34. **Pola periodik di latar statis = "barcode".** `sin(x*26)` untuk kaustik
    menghasilkan deretan garis tegak rapi. Kaustik harus dua frekuensi berbeda dan
    hanya digambar di lapis gerak.
35. **Pita sinar sempit berjarak sama juga "barcode".** Berkas cahaya harus lebih
    lebar dari jarak antar-berkas (profil plato, bukan Gaussian sempit).
36. **Bidang dalam satu kartu harus dibagi jelas** (langit / laut / geladak).
    Ikan yang ditaruh "di atas laut" dan perahu yang menempel di garis ufuk
    terbaca melayang — bukan masalah gambar, masalah penataan bidang.
37. **Jangan menaruh label di dalam bentuk kecil.** Ring "±3 tahun" pada 210 px
    membuat label tumpang tindih; label harus di luar bentuk, atau bentuknya
    diperbesar.


### 8.5 Volume, bukan gradasi (perbaikan terakhir `ikan_real`)
Gradasi vertikal lurus selalu terbaca "gambar datar yang diberi pita warna".
Yang dipakai sekarang: bentuk tiga dimensi maya. Untuk setiap kolom badan
diukur garis punggung dan garis perut, lalu dipakai penampang bulat
`z = sqrt(1 - u^2)`, dan warna dihitung dari NORMAL permukaan dengan satu arah
cahaya kiri-atas `(-0.34, -0.60, 0.72)`. Tambahan: pantulan dasar laut di sisi
perut, kilau memanjang di punggung, dan butir halus (deterministik) yang
mematahkan permukaan rata.

### 8.6 Empat jebakan yang ditemukan sesudah itu
38. **Rim light harus memakai mask BADAN, bukan seluruh sprite.** Kalau sirip
    ikut dihitung, setiap sirip mendapat garis terang di tepinya dan ikan
    terbaca seperti stiker berbingkai cahaya.
39. **Rim light hanya di tepi yang menghadap cahaya.** Tepi atas = terang,
    tepi bawah = garis gelap tipis (oklusi). Terang di semua tepi = palsu.
40. **Mata: jangan cincin pucat + iris pucat.** Kombinasi itu membentuk donat
    putih ("goggles"). Urutan benar: kelopak tipis → iris gelap → pupil lebih
    gelap → SATU kilau.
41. **Bercak putih harus kecil dan pudar** (alpha 70–125, radius 0,003–0,007 h).
    Bintik alpha 210 sebesar 4 px terbaca sebagai cipratan cat.
42. **Jangan pernah menggambar di atas array yang disimpan di cache.**
    `_hook_frame()` mengembalikan frame hook dari cache; `_tirai()` menempelkan
    tirai langsung ke array itu, sehingga tirai tercetak PERMANEN ke dalam
    cache. Akibatnya frame terakhir tidak pernah terbuka penuh: uji mesin
    menunjukkan MAE 0,12/255, tetapi QC video 57,6/255. Sekarang `_hook_frame()`
    mengembalikan `.copy()`.

### 8.7 Loop mulus (Shorts diputar berulang)
Frame terakhir dibuat **identik** dengan frame pertama:
`_outro()` menutup layar dengan "tirai kertas" (kotak krem membesar) sambil
menampilkan penanda kanal, menukar isi layar ke frame hook di balik tirai, lalu
membukanya kembali. Kontrol: MAE(frame 0,03 s, frame terakhir) = **0,12/255**
(ambang QC ≤ 26). Versi pertama memakai wipe silang dan gagal karena judul hook
serta kartu ringkasan terlihat bersamaan — gambar ganda, bukan transisi.
Konsekuensinya babak 1 memakai `t0` NEGATIF: judul, stiker, dan angka sudah
matang di t=0 (pemirsa memutuskan dalam 1–3 detik pertama). Semua fungsi
animasi memakai `clamp`, jadi `t0` negatif aman.

### 8.8 Audit tata letak sekarang MENOLAK render
`siapkan()` memanggil `_audit()` untuk kesembilan babak dengan `ketat=True`.
Kotak yang diperiksa adalah **piksel terlihat** (alpha > 8), bukan kanvas
sprite, dan tiap lapis punya `jenis` (`teks`/`dekor`); hanya kotak teks yang
diperiksa tumpang-tindihnya, sedangkan dekor (kartu, pita, lingkaran) diberi
toleransi 34 px di tepi karena bayangannya memang menyembul. Kontrol positif
dijalankan: dua kotak teks bertumpuk memang dilaporkan.

**Bug nyata yang ditemukan audit ini:** `Komposisi.kartu()` menempelkan sprite
kartu pada offset **-26** padahal padding sprite-nya **34** (`PAD_KARTU`).
Akibatnya setiap kartu bergeser 8 px dari grid dan tepinya keluar margin.
Sekarang offset memakai `PAD_KARTU` yang sama dengan padding.
