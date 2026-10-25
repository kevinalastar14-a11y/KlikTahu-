# Analisis Menyeluruh: Gaya Video Short Lama vs Hasil v21

Tanggal: 25 Oktober 2026 · Episode: Ep58 "Ikan yang Seharusnya Punah 66 Juta Tahun Lalu"

## 0. Bahan yang dianalisis

| bahan | cara diperoleh | catatan |
|---|---|---|
| Video short lama kanal | `Megalodon Masih Hidup Giginya yang Menjawab.mp4` diunduh dari Google Drive ke `google_drive/` | 3,43 MB · 144,03 s · 240x426 · 30 fps |
| Hasil v21 (video baru) | `keluaran/KlikTahu_Ep58_Coelacanth_v21.mp4` | 54,67 MB · 124,63 s · 1080x1920 · 60 fps |

Sandbox tidak punya akses langsung ke YouTube/Google (SSL_ERROR_SYSCALL), jadi video acuan
diambil lewat konektor Google Drive. Kalau ada video short lama lain yang ingin dijadikan
acuan (mis. `VIDEO_SHORT_01..03` di Drive), polanya bisa diukur ulang dengan perintah yang
sama (lihat §7).

## 1. Pengukuran kuantitatif acuan

### 1.1 Berkas
- Durasi **144,03 s** → di atas batas "Shorts >1 menit dengan klaim hak cipta diblokir global",
  dan sangat dekat ke batas 3 menit. Ini risiko distribusi, bukan risiko gaya.
- Resolusi **240x426** (0,10 MP), **30 fps**, H.264 **Main**, video **58 kb/s**, total 190 kb/s.
- Audio AAC 44,1 kHz stereo **127 kb/s**, RMS **−14,4 dBFS**, puncak p95 −10 dB,
  bagian hening (< −45 dB) **14,7 %**.

### 1.2 Ritme dan gerak
- Deteksi pergantian visual (Δ frame ≥ 10/255) menemukan **17 titik**, jarak median **10 s**
  (rentang 1–17 s). Artinya: **satu ide per ±10 detik**, bukan potongan cepat.
- Sebaran perubahan per frame: halus (< 2) **15 %**, sedang (2–8) **71 %**, besar (≥ 8) **13 %**.
  → Video ini lebih banyak **bergerak halus** daripada memotong.
- Energi selubung audio pada 1,5–6 Hz (irama suku kata) **47,6 %** → narasi mendominasi;
  tidak ada musik yang menutupi suara.

### 1.3 Palet (diukur dari 12 sampel frame)
- Latar atas rata-rata **(221, 219, 212) s/d (194, 192, 192)** → **krem hangat**, bukan putih.
- Tidak ada satu frame pun yang latarnya gelap → ini video **terang**, kebalikan dari gaya
  "SINEMATIK GELAP" (v19/v20) yang dipakai episode sebelumnya.
- Warna aksen yang muncul: **coral/merah bata** (tab FAKTA, angka penting), **navy** (tinta
  headline, badan ikan), **teal/hijau laut**, **emas** (cincin mata), **pasir** (dasar laut).

### 1.4 Struktur visual (dibaca dari 48 frame tersampel tiap 3 detik)
1. **HUD**: merek `• KlikTahu` kiri atas, label kategori `HEWAN PURBA` kanan atas.
2. **Tab "FAKTA n/7"** di tengah atas, coral, dengan garis putus di kiri-kanan.
3. **Headline** 2–3 baris, huruf besar, tinta navy, satu kata **distabilo coral**.
4. **Kartu ilustrasi** besar bersudut bulat: ilustrasi vektor datar (ikan, peta, kolom laut,
   koran, grafik batang, termometer).
5. **Stiker caption** hitam-putih atau coral (mis. "BENARKAH?", "JARANG JADI FOSIL").
6. **Angka besar** di bawah (mis. `10,03 m`, `16,8 telapak tangan`, `73 persen`).
7. **Bar progres segmen** di tepi bawah.
8. **Sumber** kecil di atas progres.

### 1.5 Kelemahan yang terukur pada acuan
| kelemahan | bukti |
|---|---|
| resolusi sangat rendah | 240x426 · 58 kb/s → tepi ilustrasi bergerigi, teks kecil pecah |
| 30 fps | gerak patah, terutama saat ilustrasi digeser |
| melewati batas aman durasi | 144 s (di atas 1 menit, dekat batas 3 menit) |
| audio hanya narasi | hening 14,7 %, tidak ada musik/ambience |
| klaim tanpa sumber di layar | tidak ada baris sumber yang terbaca |
| ruang bawah sering kosong | beberapa babak menyisakan ±350 px polos |

## 2. Yang ditiru (identitas gaya)

Kertas krem + gumpalan/cincin samar, tinta navy, coral sebagai aksen tunggal, tab FAKTA n/7,
headline besar dengan satu kata distabilo, kartu ilustrasi vektor, stiker caption, angka besar,
progres segmen, HUD merek + kategori. Semua itu dipertahankan **karena itulah yang membuat
video lama mudah dikenali dan enak diikuti**.

## 3. Yang dinaikkan (semua aspek kecuali resolusi — dan resolusi pun naik sesuai standar)

| aspek | acuan | v21 | cara |
|---|---|---|---|
| resolusi | 240x426 | **1080x1920** | kanvas 2,1 MP |
| fps | 30 | **60** | render 7.478 frame |
| bitrate video | 58 kb/s | **3,2 Mb/s** | CRF 15, preset slow |
| tepi ilustrasi | bergerigi | halus | vektor digambar 2x lalu diperkecil |
| durasi | 144 s | **124,6 s** | 9 babak, aman di bawah batas |
| naskah | klaim umum | **angka + sumber per babak** | 9 baris sumber di layar |
| audio | narasi + hening | **narasi + musik −42 dB + ducking 4,5 dB** | `mesin_v21_musik.py` |
| koreksi mitos | tidak ada | **2 babak** ("fosil hidup" keliru; bukan leluhur langsung) | naskah + visual coret |
| sudut lokal | tidak ada | **Manado / Latimeria menadoensis** | peta + pil label |
| gerak | ganti babak tiap 10 s | **selalu ada gerak**: latar bergeser, debu kertas, kilau melintas, ilustrasi mengapung | `Komposisi.latar()` + `goyang()` |
| ruang kosong | ±350 px di beberapa babak | **zona bawah selalu terisi** (angka/panel/stiker) | zona tetap `Z` |

## 4. Struktur naskah (9 babak, 124,6 s)

| # | babak | durasi VO | inti |
|---|---|---|---|
| 1 | HOOK | 15,6 s | "punah 66 juta tahun… tapi masih ada" |
| 2 | FAKTA 1 | 12,1 s | fosil Devon 400 jt th; 170 jt th sebelum dinosaurus |
| 3 | FAKTA 2 | 15,3 s | 22 Des 1938, Marjorie, 1,5 m |
| 4 | FAKTA 3 | 17,7 s | Latimeria chalumnae = duri berongga (koilos + akantha) |
| 5 | FAKTA 4 | 13,6 s | 1997 Manado → Latimeria menadoensis (1999) |
| 6 | FAKTA 5 | 10,9 s | sirip cuping → kerabat tetrapoda, **bukan** leluhur langsung |
| 7 | FAKTA 6 | 14,0 s | "fosil hidup" keliru; genom 2,86 Gb; hamil ±3 tahun |
| 8 | FAKTA 7 | 11,9 s | populasi ±500, tertangkap jaring, status kritis |
| 9 | PENUTUP | 11,7 s | tiga hal + CTA simpan |

Total narasi 1.031 karakter ≈ 176 kata → **±1,4 kata/detik**, kecepatan yang nyaman untuk
bahasa Indonesia dan aman untuk TTS.

## 5. Audit kebenaran (koreksi yang dilakukan saat produksi)

- **Genom:** coelacanth **2,86 Gb**, manusia **±3,1 Gb**. Draf pertama menulis "genomnya lebih
  besar dari genom manusia" — **salah**, dan sudah diganti menjadi "hampir sebesar genom manusia
  (3,1 miliar)" sebelum render final.
- **"Fosil hidup":** dipakai sebagai *istilah yang dikoreksi*, bukan klaim. Coelacanth tetap
  berevolusi; laju evolusinya lambat, bentuknya konservatif.
- **Kekerabatan:** sirip cuping membuatnya kerabat dekat garis tetrapoda, **bukan** nenek moyang
  langsung manusia. Ini ditulis eksplisit di babak 6 dan dicoret di layar.
- **Status:** IUCN *critically endangered* untuk *L. chalumnae*; populasi Komoro diperkirakan
  ratusan (dipakai "±500" dengan tanda ± dan kata "diperkirakan").
- **Angka yang dipakai di layar** semuanya berasal dari publikasi: Forey 1998, Smith 1939,
  Pouyaud dkk. 1999, Nature 2013 (genom), IUCN Red List.

## 6. Hasil QC akhir (24/24 lulus)

| butir | nilai |
|---|---|
| resolusi / fps / profil | 1080x1920 · 60,00 · H.264 High · yuv420p |
| durasi | 124,63 s (audio = video) |
| bitrate | 3,5 Mb/s (ambang 3–60) |
| ukuran | 54,7 MB (batas Shorts 250 MB) |
| loudness / true peak / LRA | −14,0 LUFS · −1,9 dBTP · 3,7 LU |
| faststart | moov@36 < mdat@189084 |
| gambar = mesin (MAE) | 2,28/255 (ambang ≤ 6) |
| HUD & "caption" terbaca | 12/12 |
| loop halus | 22,9/255 (ambang ≤ 26) |
| ada gerak | Δ 0,50 · kotak 17,0 (ambang Δ>0,35 atau kotak>1,2) |

## 7. Cara mengukur ulang acuan lain

```bash
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
# profil
$FF -hide_banner -i ACUAN.mp4 2>&1 | grep -E "Duration|Stream"
# frame tiap 1 detik -> 48x85, hitung delta antar-frame
$FF -v error -i ACUAN.mp4 -vf "fps=1,scale=48:85" -f rawvideo -pix_fmt rgb24 - | python3 -c "
import sys, numpy as np
a=np.frombuffer(sys.stdin.buffer.read(), np.uint8).reshape(-1,85,48,3).astype(np.float32)
d=np.abs(np.diff(a,axis=0)).mean(axis=(1,2,3))
print('median Δ', np.median(d), '| titik ganti', [i+1 for i,v in enumerate(d) if v>=10])"
# warna latar dominan
$FF -v error -i ACUAN.mp4 -vf "fps=1/12,scale=60:107" -f rawvideo -pix_fmt rgb24 - | \
  python3 -c "import sys,numpy as np; a=np.frombuffer(sys.stdin.buffer.read(),np.uint8).reshape(-1,107,60,3); print(a[:,5:20].mean((1,2,3)))"
```

## 8. Kesimpulan

Gaya video short lama bukan "video murah": pola 7 fakta + satu ide per layar + headline besar
adalah alasan video itu ditonton sampai habis. Yang membuatnya terlihat murah adalah **teknis**
(240p, 30 fps, 58 kb/s, tanpa suara latar, tanpa sumber) — bukan gayanya. v21 mempertahankan
polanya, lalu memperbaiki seluruh komponen teknis dan menaikkan mutu isi (angka bersumber,
dua koreksi mitos, sudut lokal Manado), dengan resolusi tetap 1080x1920 @ 60 fps.
