# Arsip — workflow render GitHub Actions (TIDAK AKTIF)

Folder ini menyimpan **salinan** workflow lama yang dulu merender video di
GitHub Actions. Workflow tersebut **sudah dipindahkan keluar dari
`.github/workflows/`** dan tidak akan jalan lagi.

## Kenapa dinonaktifkan

Akun GitHub sebelumnya (`elthsi09-ZERO-X`) di-flag GitHub sekitar 24 Sep 2026:
profil/repo 404, API 404, dan pesan *"Actions has been disabled for this user"*.
Dugaan pemicu: beban Actions besar (12-16 runner paralel per render video,
puluhan rilis berisi video 130 MB, analisis terjadwal tiap 6 jam, dan push
beruntun dari aplikasi pihak ketiga).

Aturan GitHub: runner gratis hanya untuk **membangun/menguji perangkat lunak**,
bukan komputasi umum seperti merender video. Karena itu, sejak 6 Okt 2026:

- Render video dijalankan **lokal** lewat `tools/render_lokal.sh`
  (sandbox agen atau komputer sendiri) — lihat `AGEN.md` §14.
- GitHub hanya menyimpan kode (version control) + menjalankan uji ringan
  (`.github/workflows/selftest.yml`).
- MP4 tidak disimpan di repo maupun di Releases.

## Isi arsip

| berkas | fungsi aslinya |
|---|---|
| `workflows/render.yml` | render Shorts paralel (prep → render N potongan → merge → Release) |
| `workflows/render_long.yml` | render video panjang 16:9 paralel |
| `workflows/preview.yml` | pratinjau cepat 8 frame + montase |
| `workflows/metadata.yml` | menimpa aset METADATA.md di rilis tanpa render ulang |
| `workflows/analisis.yml` | riset kata kunci terjadwal + commit hasil oleh bot |

Berguna sebagai rujukan kalau nanti mau dihidupkan lagi — tetapi pikirkan dulu
kuota Actions dan riwayat flag di atas. Alur kerjanya sudah dipindahkan ke
`tools/render_lokal.sh` (render penuh) dan dijalankan manual dari sandbox.
