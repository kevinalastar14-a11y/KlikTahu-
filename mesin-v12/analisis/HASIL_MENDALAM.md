# KlikTahu - Analisis Mendalam Real-Time v3 (2026-10-15)

**Permintaan:** 254 panggilan autocomplete (Google hl=id + YouTube ds=yt, gl=id)
**Frasa unik:** 1934 (292 di luar tema) - sumber: hasil_mendalam_20261015.json

- `skor` = jml + kuat*0,7 + niat*0,9 + sains*3 + yt*0,3 (yt = frasa yang muncul di YouTube = ada yang mencari DAN menonton)
- `skor_tumbuh` = skor + rel*1,2 + kom*1,5 + vis*0,8 + ever*3
  - rel = frasa pengalaman pribadi/keseharian (relatabilitas), kom = frasa yang mengundang bercerita (komentar cepat),
  - vis = fenomena yang bisa diperlihatkan (retensi & share), ever = 1 kalau bebas frasa musiman (evergreen).
- Urutan tabel: skor_tumbuh (sinyal pertumbuhan channel), bukan volume semata.

| # | tema | jml | kuat | niat | yt | sains | rel | kom | vis | ever | skor | skor_tumbuh | status | contoh terkuat |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | gigi & mulut | 74 | 49 | 7 | 43 | 2.0 | 40 | 38 | 21 | 1.0 | 133.5 | **258.3** | SEGAR | `kenapa anak bau mulut` · `kenapa bau mulut` · `kenapa bau mulut anak tidak enak` |
| 2 | mata | 90 | 55 | 17 | 44 | 2.0 | 29 | 12 | 7 | 1.0 | 163.0 | **224.4** | SEGAR | `kenapa air mata keluar sendiri padahal tidak menangis` · `kenapa bulu mata sering rontok` · `kenapa di kelopak mata ada benjolan kecil` |
| 3 | perut & pencernaan | 74 | 33 | 25 | 36 | 2.0 | 28 | 7 | 22 | 1.0 | 136.4 | **201.1** | Ep28 | `apa penyebab maag kambuh` · `kenapa anjing dan babi haram bagi islam` · `kenapa bayi menangis terus tanpa sebab` |
| 4 | megalodon | 36 | 31 | 5 | 23 | 2.5 | 36 | 36 | 0 | 1.0 | 76.6 | **176.8** | antrean lama | `apakah megalodon masih hidup di indonesia` · `apakah megalodon masih hidup di palung mariana` · `apakah megalodon masih hidup sampai sekarang` |
| 5 | mimpi & tidur | 75 | 32 | 10 | 39 | 2.0 | 19 | 11 | 1 | 1.0 | 124.1 | **167.2** | Ep21+Ep25 | `kenapa anak susah tidur malam` · `kenapa anak susah tidur siang` · `kenapa bangun tidur bau mulut` |
| 6 | baterai & hp | 61 | 24 | 11 | 41 | 1.5 | 13 | 3 | 2 | 1.0 | 104.5 | **129.2** | SEGAR | `kenapa baterai cepat habis` · `kenapa baterai cepat habis dan panas` · `kenapa baterai cepat habis iphone` |
| 7 | kulit | 46 | 32 | 5 | 28 | 1.5 | 13 | 7 | 2 | 1.0 | 85.8 | **116.5** | SEGAR | `kenapa bulu kemaluan gatal` · `kenapa di area kemaluan wanita ada benjolan seperti jerawat` · `kenapa di kemaluan ada benjolan seperti jerawat dan gatal` |
| 8 | kucing | 26 | 23 | 1 | 21 | 2.0 | 12 | 26 | 0 | 1.0 | 55.3 | **111.7** | Ep23 | `kenapa anjing takut kucing` · `kenapa anjing takut sama kucing` · `kenapa badan kucing bau busuk` |
| 9 | kram & kesemutan | 43 | 38 | 4 | 25 | 2.0 | 14 | 1 | 0 | 1.0 | 86.7 | **108.0** | Ep29 | `kenapa badan sering kesemutan` · `kenapa bisa kesemutan` · `kenapa bisa kram kaki` |
| 10 | demam & imun | 29 | 11 | 5 | 14 | 2.0 | 7 | 15 | 18 | 1.0 | 51.4 | **99.7** | antrean lama | `demam anak naik turun selama 7 hari` · `kenapa anak demam sering kaget` · `kenapa darah rendah tidak boleh makan timun` |
| 11 | pusing & migrain | 40 | 35 | 5 | 21 | 1.5 | 11 | 1 | 0 | 1.0 | 79.8 | **97.5** | SEGAR | `kenapa bisa migrain` · `kenapa bisa terjadi migrain` · `kenapa kepala pusing sebelah kiri` |
| 12 | hujan & awan | 36 | 30 | 3 | 19 | 2.5 | 5 | 2 | 14 | 0.3 | 72.9 | **94.0** | SEGAR | `google kenapa awan warna putih` · `kenapa ada awan` · `kenapa ada awan putih dan hitam` |
| 13 | hantu & supranatural | 37 | 32 | 0 | 25 | 2.0 | 5 | 5 | 3 | 1.0 | 72.9 | **91.8** | SEGAR | `kenapa hantu` · `kenapa hantu banyak perempuan` · `kenapa hantu berbeda di setiap negara` |
| 14 | mimisan & hidung | 30 | 27 | 4 | 14 | 2.5 | 9 | 6 | 3 | 1.0 | 64.2 | **89.4** | SEGAR | `kenapa anak mimisan tiba tiba` · `kenapa anak sering mimisan` · `kenapa bisa mimisan` |
| 15 | uban & rambut | 46 | 29 | 2 | 30 | 1.5 | 2 | 0 | 0 | 1.0 | 81.6 | **87.0** | antrean lama | `kenapa ada uban di usia muda` · `kenapa banyak uban di usia muda` · `kenapa ketombe ada` |
| 16 | situs misteri indonesia | 39 | 31 | 0 | 29 | 2.5 | 1 | 2 | 0 | 1.0 | 76.9 | **84.1** | antrean lama | `apa misteri gunung lawu` · `apa misteri gunung padang` · `cerita misteri gunung lawu` |
| 17 | internet & sinyal | 38 | 22 | 11 | 23 | 1.5 | 7 | 0 | 0 | 0.3 | 74.7 | **84.0** | SEGAR | `kenapa di laptop tidak muncul wifi` · `kenapa internet cepat habis` · `kenapa internet indonesia lambat` |
| 18 | cegukan | 27 | 23 | 12 | 16 | 2.0 | 11 | 1 | 0 | 1.0 | 64.7 | **82.4** | SEGAR | `kenapa bayi cegukan` · `kenapa bayi cegukan dan cara mengatasinya` · `kenapa bayi cegukan setelah minum asi` |
| 19 | listrik & magnet | 28 | 26 | 10 | 13 | 2.5 | 4 | 4 | 2 | 0.3 | 66.6 | **79.9** | SEGAR | `kenapa belut listrik berbahaya` · `kenapa genset tidak keluar listrik` · `kenapa listrik berbahaya` |
| 20 | bintang & galaksi | 31 | 20 | 0 | 18 | 3.0 | 4 | 5 | 1 | 1.0 | 59.4 | **75.5** | SEGAR | `apa itu galaksi` · `apa itu galaksi andromeda` · `apa itu galaksi bima sakti` |
| 21 | gerhana | 39 | 14 | 3 | 25 | 3.0 | 1 | 2 | 2 | 0.3 | 68.0 | **74.7** | SEGAR | `apa arti gerhana bulan darah` · `apa arti gerhana bulan merah` · `apa arti gerhana matahari` |
| 22 | ngorok | 24 | 24 | 3 | 16 | 2.0 | 3 | 6 | 1 | 1.0 | 54.3 | **70.7** | Ep27 | `kenapa anak tidur ngorok` · `kenapa ayam bisa ngorok` · `kenapa ayam ngorok` |
| 23 | kuku | 20 | 20 | 1 | 4 | 1.5 | 10 | 10 | 0 | 1.0 | 40.6 | **70.6** | SEGAR | `kenapa kuku bergelombang` · `kenapa kuku berlubang` · `kenapa kuku berlubang kecil` |
| 24 | serangga | 30 | 18 | 0 | 20 | 2.0 | 3 | 5 | 2 | 1.0 | 54.6 | **70.3** | SEGAR | `kenapa nyamuk aktif di malam hari` · `kenapa nyamuk banyak di malam hari` · `kenapa nyamuk bisa menembus kulit` |
| 25 | petir | 26 | 23 | 0 | 17 | 2.5 | 3 | 2 | 5 | 1.0 | 54.7 | **68.3** | antrean lama | `kenapa gunung meletus ada petir` · `kenapa gunung meletus keluar petir` · `kenapa hujan ada petir` |
| 26 | pelangi | 29 | 25 | 1 | 15 | 2.5 | 1 | 0 | 4 | 1.0 | 59.4 | **66.8** | SEGAR | `kenapa bisa terjadi pelangi` · `kenapa pelangi` · `kenapa pelangi ada 2` |
| 27 | piramida & mesir | 31 | 27 | 0 | 16 | 2.5 | 0 | 1 | 0 | 1.0 | 62.2 | **66.7** | SEGAR | `buku misteri piramida dan sphinx` · `doraemon misteri piramida mesir sub indo` · `kenapa piramida ada dimana mana` |
| 28 | batuk flu pilek | 25 | 13 | 2 | 10 | 1.5 | 7 | 7 | 0 | 1.0 | 43.4 | **65.3** | SEGAR | `kenapa anak flu berulang` · `kenapa batuk gak sembuh sembuh` · `kenapa batuk tidak kunjung sembuh` |
| 29 | kuping | 24 | 19 | 2 | 14 | 2.0 | 5 | 3 | 3 | 1.0 | 49.3 | **65.2** | SEGAR | `kenapa kuping berdenging` · `kenapa kuping berdenging kanan kiri` · `kenapa kuping berdenging menurut islam` |
| 30 | matahari | 22 | 19 | 1 | 16 | 3.0 | 3 | 3 | 5 | 1.0 | 50.0 | **65.1** | SEGAR | `kenapa harus takut pada matahari` · `kenapa luar angkasa gelap padahal ada matahari` · `kenapa matahari` |
| 31 | air laut & ombak | 33 | 16 | 0 | 18 | 2.5 | 2 | 1 | 1 | 1.0 | 57.1 | **64.8** | SEGAR | `asal usul kenapa air laut asin` · `kenapa ada ombak` · `kenapa ada ombak di danau` |
| 32 | tekanan darah | 26 | 15 | 2 | 11 | 2.5 | 5 | 2 | 3 | 1.0 | 49.1 | **63.5** | SEGAR | `darah tinggi disebabkan oleh apa` · `kenapa bisa darah rendah` · `kenapa darah rendah` |
| 33 | menangis & emosi | 25 | 19 | 1 | 14 | 2.0 | 4 | 4 | 0 | 1.0 | 49.4 | **63.2** | SEGAR | `gampang stres kenapa` · `keinginanmu kenapa menangis` · `kenapa bayi menangis terus tiap malam` |
| 34 | jantung & dada | 27 | 16 | 3 | 14 | 2.0 | 3 | 2 | 0 | 1.0 | 51.1 | **60.7** | SEGAR | `kenapa dada sesak` · `kenapa dada sesak dan jantung berdebar` · `kenapa dada sesak dan sakit` |
| 35 | ular & reptil | 19 | 12 | 1 | 15 | 2.0 | 4 | 8 | 0 | 1.0 | 38.8 | **58.6** | SEGAR | `kenapa ular` · `kenapa ular berbisa` · `kenapa ular bisa berjalan` |
| 36 | gempa bumi | 19 | 14 | 2 | 13 | 3.0 | 7 | 1 | 0 | 1.0 | 43.5 | **56.4** | Ep22 | `kenapa ada gempa bumi` · `kenapa bisa gempa` · `kenapa bisa gempa bumi` |
| 37 | angin & badai | 23 | 17 | 1 | 12 | 2.5 | 3 | 1 | 2 | 0.3 | 46.9 | **54.5** | SEGAR | `kenapa ac tidak ada anginnya` · `kenapa ada angin` · `kenapa ada angin dalam badan` |
| 38 | es & salju | 25 | 19 | 0 | 16 | 2.0 | 0 | 0 | 5 | 0.3 | 49.1 | **54.0** | SEGAR | `apa yang terjadi jika es kutub mencair` · `kenapa 2026 turun salju` · `kenapa ada musim salju` |
| 39 | lubang hitam | 11 | 0 | 0 | 3 | 3.0 | 11 | 11 | 0 | 1.0 | 20.9 | **53.6** | SEGAR | `apa isi lubang hitam` · `apa itu lubang hitam` · `apa itu lubang hitam atau black hole` |
| 40 | aurora | 23 | 18 | 0 | 7 | 3.0 | 1 | 1 | 1 | 1.0 | 46.7 | **53.2** | antrean lama | `apa itu aurora` · `apa itu aurora australis` · `apa itu aurora borealis` |
| 41 | burung terbang | 24 | 6 | 1 | 9 | 2.0 | 4 | 3 | 3 | 1.0 | 37.8 | **52.5** | SEGAR | `burung terbang malam hari` · `burung terbang malam hari pertanda apa` · `kenapa air radiator keluar dari selang pembuangan` |
| 42 | bulan | 21 | 13 | 1 | 14 | 2.5 | 1 | 1 | 5 | 0.3 | 42.7 | **50.3** | Ep24 | `kenapa bulan berbentuk sabit` · `kenapa bulan bercahaya` · `kenapa bulan berwarna merah` |
| 43 | planet & roket | 12 | 11 | 0 | 5 | 3.0 | 4 | 4 | 7 | 1.0 | 30.2 | **49.6** | SEGAR | `bagaimana roket bekerja` · `bagaimana roket kembali ke bumi` · `bagaimana roket mendarat ke bumi` |
| 44 | gusi & rahang | 12 | 8 | 1 | 4 | 2.0 | 5 | 4 | 11 | 1.0 | 25.7 | **49.5** | SEGAR | `kenapa rahang berbunyi saat membuka mulut` · `kenapa rahang bunyi` · `kenapa rahang bunyi ketika membuka mulut` |
| 45 | anjing | 20 | 10 | 0 | 12 | 2.0 | 3 | 3 | 1 | 1.0 | 36.6 | **48.5** | SEGAR | `kenapa anjing alpha ditakuti` · `kenapa anjing alpha ditakuti anjing lain` · `kenapa anjing bisa kawin dengan manusia` |
| 46 | kapal & mengapung | 19 | 13 | 3 | 9 | 2.5 | 3 | 0 | 0 | 1.0 | 41.0 | **47.6** | antrean lama | `kenapa es batu mengapung` · `kenapa es batu mengapung di air` · `kenapa es mengapung` |
| 47 | langit & senja | 14 | 7 | 2 | 2 | 2.5 | 3 | 2 | 14 | 0.3 | 28.8 | **47.5** | SEGAR | `google kenapa langit biru` · `kenapa langit biru` · `kenapa langit biru di siang hari` |
| 48 | segitiga bermuda | 19 | 17 | 1 | 14 | 2.0 | 0 | 0 | 3 | 1.0 | 42.0 | **47.4** | SEGAR | `apa misteri segitiga bermuda` · `apakah misteri segitiga bermuda sudah terpecahkan` · `buku misteri segitiga bermuda` |
| 49 | laut dalam | 18 | 16 | 0 | 13 | 2.5 | 1 | 1 | 0 | 1.0 | 40.6 | **46.3** | SEGAR | `kenapa laut dalam gelap` · `kenapa laut dalam gelap di dunia` · `kisah misteri laut dalam` |
| 50 | pesawat | 16 | 7 | 3 | 9 | 2.5 | 4 | 1 | 0 | 1.0 | 33.8 | **43.1** | SEGAR | `kenapa pesawat berat bisa terbang` · `kenapa pesawat bisa terbang` · `kenapa pesawat bisa terbang di udara` |
| 51 | ufo & alien | 17 | 13 | 0 | 6 | 2.0 | 1 | 1 | 3 | 1.0 | 33.9 | **42.0** | SEGAR | `apa itu ufo` · `apa itu ufo dan alien` · `apa itu ufo indonesia` |
| 52 | dinosaurus | 14 | 11 | 0 | 5 | 3.0 | 2 | 1 | 0 | 1.0 | 32.2 | **39.1** | Ep26 | `alasan kenapa dinosaurus punah` · `kenapa dinosaurus bisa punah` · `kenapa dinosaurus harus punah` |
| 53 | gunung api | 10 | 10 | 2 | 2 | 2.5 | 0 | 0 | 1 | 1.0 | 26.9 | **30.7** | SEGAR | `kenapa bisa terjadi gunung meletus` · `kenapa gunung meletus` · `kenapa gunung meletus ada apinya` |
| 54 | gula & makanan | 14 | 7 | 0 | 10 | 2.0 | 0 | 0 | 1 | 0.3 | 27.9 | **29.6** | SEGAR | `kenapa gula darah bisa rendah` · `kenapa gula darah bisa tinggi` · `kenapa gula darah puasa tinggi` |
| 55 | kedutan | 5 | 5 | 2 | 5 | 2.0 | 2 | 0 | 0 | 1.0 | 17.8 | **23.2** | SEGAR | `kenapa alis kiri kedutan terus` · `kenapa bibir atas kedutan` · `kenapa pipi kiri kedutan terus` |

## Kandidat segar teratas (belum dibahas, bukan antrean lama, cocok sains) — urut skor_tumbuh
1. **gigi & mulut** - skor_tumbuh 258.3 (skor 133.5; jml 74, kuat 49, yt 43, rel 40, kom 38, vis 21, ever 1.0) - contoh: `kenapa anak bau mulut`, `kenapa bau mulut`, `kenapa bau mulut anak tidak enak`, `kenapa bau mulut busuk`
2. **mata** - skor_tumbuh 224.4 (skor 163.0; jml 90, kuat 55, yt 44, rel 29, kom 12, vis 7, ever 1.0) - contoh: `kenapa air mata keluar sendiri padahal tidak menangis`, `kenapa bulu mata sering rontok`, `kenapa di kelopak mata ada benjolan kecil`, `kenapa kedutan di bawah mata kanan`
3. **hujan & awan** - skor_tumbuh 94.0 (skor 72.9; jml 36, kuat 30, yt 19, rel 5, kom 2, vis 14, ever 0.3) - contoh: `google kenapa awan warna putih`, `kenapa ada awan`, `kenapa ada awan putih dan hitam`, `kenapa ada awan putih di malam hari`
4. **hantu & supranatural** - skor_tumbuh 91.8 (skor 72.9; jml 37, kuat 32, yt 25, rel 5, kom 5, vis 3, ever 1.0) - contoh: `kenapa hantu`, `kenapa hantu banyak perempuan`, `kenapa hantu berbeda di setiap negara`, `kenapa hantu bisa ada`
5. **mimisan & hidung** - skor_tumbuh 89.4 (skor 64.2; jml 30, kuat 27, yt 14, rel 9, kom 6, vis 3, ever 1.0) - contoh: `kenapa anak mimisan tiba tiba`, `kenapa anak sering mimisan`, `kenapa bisa mimisan`, `kenapa hidung berdarah`
6. **cegukan** - skor_tumbuh 82.4 (skor 64.7; jml 27, kuat 23, yt 16, rel 11, kom 1, vis 0, ever 1.0) - contoh: `kenapa bayi cegukan`, `kenapa bayi cegukan dan cara mengatasinya`, `kenapa bayi cegukan setelah minum asi`, `kenapa bisa cegukan terus`
7. **listrik & magnet** - skor_tumbuh 79.9 (skor 66.6; jml 28, kuat 26, yt 13, rel 4, kom 4, vis 2, ever 0.3) - contoh: `kenapa belut listrik berbahaya`, `kenapa genset tidak keluar listrik`, `kenapa listrik berbahaya`, `kenapa listrik berbahaya bagi manusia`
8. **bintang & galaksi** - skor_tumbuh 75.5 (skor 59.4; jml 31, kuat 20, yt 18, rel 4, kom 5, vis 1, ever 1.0) - contoh: `apa itu galaksi`, `apa itu galaksi andromeda`, `apa itu galaksi bima sakti`, `apa itu galaksi bima sakti dan bagaimana bentuknya`
