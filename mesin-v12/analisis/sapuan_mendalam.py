#!/usr/bin/env python3
"""Sapuan MENDALAM v3 — analisis real-time menyeluruh UNTUK PERTUMBUHAN channel.

Perbedaan dengan v2:
  1. Semua sinyal v2 dipertahankan (jml, kuat, niat, yt, sains, bucket A/B/C).
  2. TAMBAHAN sinyal pertumbuhan per tema (dihitung dari teks frasa):
     - rel   : frasa bernuansa pengalaman pribadi/keseharian (aku/sering/selalu/
       padahal/tiba-tiba) -> topik yang bikin orang merasa "ini aku banget".
     - kom   : frasa yang mengundang orang BERCERITA di komentar (aku/anak/kucing/
       pacar/punya) -> komentar cepat = sinyal kuat algoritma Shorts.
     - vis   : fenomena yang bisa DIPERLIHATKAN/didengar (bunyi, warna, keluar,
       getar, api...) -> animasi yang bisa didemonstrasi = retensi + share.
     - ever  : 1 kalau tak ada frasa musiman/event (topik evergreen = tumbuh
       terus, tidak anjlok setelah event lewat).
  3. DUA skor:
     - skor      = jml + kuat*0,7 + niat*0,9 + sains*3 + yt*0,3      (permintaan)
     - skor_tumbuh = skor + rel*1,2 + kom*1,5 + vis*0,8 + ever*3    (pertumbuhan)
     Bobot pertumbuhan = heuristik transparan (kolom ditampilkan penuh di laporan)
     berdasarkan prinsip Shorts: komentar & share menentukan penyebaran, bukan
     cuma volume pencarian.
  4. Tema baru dimasukkan agar pemetaan lebih menyeluruh: kedutan, gusi & rahang,
     kentut, ngiler, mimisan & hidung.

Keluaran (relatif terhadap folder analisis/):
  - hasil_mendalam_<YYYYMMDD>.json  (mentah + skor)
  - HASIL_MENDALAM.md               (laporan siap baca, nama stabil)
"""
import json, os, re, time, urllib.parse, urllib.request
from datetime import date
from collections import defaultdict

# Topik DIBLOKIR TOTAL (perintah user 21 Sep 2026: "hapus semua yang kentut dll" -
# tabu/memalukan; fokus analisis = potensi views besar). Frasa & temanya dibuang
# dari data, peringkat, dan laporan - bukan sekadar disembunyikan. Satu sumber:
# pemeta_peluang.py mewarisi BLOKIR dari sini.
BLOKIR = ("kentut", "ngiler", "keringat & bau badan")

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
JEDA = float(os.environ.get("KT_JEDA", "0.18"))


def sug(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=12) as r:
        txt = r.read().decode("utf-8", "ignore").strip()
    if txt.startswith("window.google.ac.h("):
        txt = txt[len("window.google.ac.h("):]
        txt = txt[: txt.rfind(")")]
    elif txt.startswith(")]}'"):
        txt = txt[4:].lstrip()
    data = json.loads(txt)
    if not isinstance(data, list) or len(data) < 2:
        return []
    out = []
    for i, s in enumerate(data[1]):
        if isinstance(s, str):
            out.append((s, i + 1))
        elif isinstance(s, list) and s and isinstance(s[0], str):
            out.append((s[0], i + 1))
    return out


def _ambil(fn, q):
    time.sleep(JEDA)
    try:
        return fn(q)
    except Exception:
        return []


def g(q):
    return _ambil(lambda x: sug("https://suggestqueries.google.com/complete/search"
                                "?client=firefox&hl=id&gl=id&q=" + urllib.parse.quote(x)), q)


def yt(q):
    return _ambil(lambda x: sug("https://suggestqueries-clients6.youtube.com/complete/search"
                                "?client=youtube&ds=yt&hl=id&gl=id&q=" + urllib.parse.quote(x)), q)


AWALAN = ["lu", "di", "ka", "mi", "or", "ai", "bu", "ke", "ma", "pe",
          "ta", "si", "ha", "ge", "ku", "na"]

# tema: (bobot_sains, regex_atribusi, [seed])  -- urutan atribusi = urutan dict
TEMA = {
    "gerhana": (3.0, r"gerhana", ["apa itu gerhana", "apa itu gerhana matahari", "apa itu gerhana bulan"]),
    "megalodon": (2.5, r"megalodon", ["megalodon", "kenapa megalodon punah", "megalodon masih hidup"]),
    "dinosaurus": (3.0, r"dinosaurus|t[- ]?rex|tyrannosaurus", ["kenapa dinosaurus punah"]),  # Ep26
    "ngorok": (2.0, r"ngorok|mendengkur|dengkuran", ["kenapa ngorok"]),                        # Ep27
    "mimpi & tidur": (2.0, r"mimpi|tidur|begadang|terbangun|menguap|kantuk", ["kenapa mimpi", "kenapa susah tidur"]),  # Ep21/25
    "uban & rambut": (1.5, r"\buban\b|rambut (rontok|tumbuh|kering)|\bketombe\b", ["kenapa uban", "kenapa rambut rontok", "kenapa ketombe"]),
    "gigi & mulut": (2.0, r"gigi|sariawan|bau mulut|gusi", ["kenapa gigi berlubang", "kenapa gigi goyang", "kenapa bau mulut"]),
    "demam & imun": (2.0, r"demam|panas badan|imun|kebal", ["kenapa demam", "kenapa demam anak naik turun"]),
    "batuk flu pilek": (1.5, r"batuk|flu|pilek|bersin|radang tenggorokan|asama|asma", ["kenapa batuk tidak sembuh", "kenapa flu berulang"]),
    "cegukan": (2.0, r"cegukan", ["kenapa cegukan", "kenapa cegukan terus"]),
    "mata": (2.0, r"\bmata\b(?!hari)|rabun|buta warna", ["kenapa mata berair", "kenapa mata kabur", "kenapa mata minus"]),
    "kuping": (2.0, r"kuping|telinga|berdenging", ["kenapa kuping berdenging", "kenapa kuping berasap"]),
    "jantung & dada": (2.0, r"jantung|nyeri dada|dada (berdebar|sesak)", ["kenapa jantung berdebar", "kenapa dada sesak"]),
    "tekanan darah": (2.5, r"darah (tinggi|rendah)|hipertensi|tensi", ["kenapa darah tinggi", "kenapa darah rendah"]),
    "pusing & migrain": (1.5, r"pusing|migrain|puneng", ["kenapa pusing", "kenapa migrain"]),
    "kram & kesemutan": (2.0, r"kram|kesemutan", ["kenapa kram", "kenapa kesemutan"]),  # Ep29
    "kentut": (2.0, r"kentut|buyut|gas (perut|lambung)", ["kenapa kentut", "kenapa kentut bau"]),
    "ngiler": (2.0, r"ngiler|iler|liur", ["kenapa ngiler", "kenapa ngiler saat tidur"]),
    "mimisan & hidung": (2.5, r"mimisan|hidung (berdarah|mampet|tersumbat)|ingus", ["kenapa mimisan", "kenapa hidung berdarah"]),
    "gusi & rahang": (2.0, r"gusi|rahang|gemeretak|bruxism", ["kenapa gusi berdarah", "kenapa rahang bunyi"]),
    "kedutan": (2.0, r"kedutan|kaku otot", ["kenapa kedutan", "kenapa mata kedutan"]),
    "perut & pencernaan": (2.0, r"perut|lambung|maag|kembung|sembelit|mencret|bab|muntah|usus", ["kenapa perut bunyi", "kenapa perut kembung", "kenapa maag kambuh"]),  # Ep28
    "keringat & bau badan": (1.5, r"keringat|ketiak|bau badan", ["kenapa keringat bau", "kenapa badan bau"]),
    "kulit": (1.5, r"jerawat|gatal|eksim|panu|ruam|kurap", ["kenapa jerawat", "kenapa kulit gatal"]),
    "kuku": (1.5, r"kuku", ["kenapa kuku berlubang", "kenapa kuku patah"]),
    "petir": (2.5, r"petir|halilintar|guntur|sambaran", ["kenapa petir", "kenapa petir menyambar"]),
    "pelangi": (2.5, r"pelangi", ["kenapa pelangi", "kenapa pelangi muncul"]),
    "hujan & awan": (2.5, r"hujan|awan|banjir|gerimis", ["kenapa hujan", "kenapa awan putih"]),
    "angin & badai": (2.5, r"angin|puting beliung|badai|topan", ["kenapa ada angin", "kenapa puting beliung"]),
    "gunung api": (2.5, r"gunung (meletus|api)|magma|lava|kawah", ["kenapa gunung meletus"]),
    "gempa bumi": (3.0, r"gempa|tektonik|tsunami|sesar", ["kenapa gempa"]),  # Ep22
    "aurora": (3.0, r"aurora", ["apa itu aurora", "kenapa ada aurora"]),
    "matahari": (3.0, r"matahari|gerhana|cakala", ["kenapa matahari", "apa itu gerhana"]),
    "bulan": (2.5, r"\bbulan\b(?! purnama)|purnama|\bsabit\b", ["kenapa bulan"]),  # Ep24
    "bintang & galaksi": (3.0, r"\bbintang\b|galaksi|bima sakti", ["kenapa bintang", "apa itu galaksi"]),
    "planet & roket": (3.0, r"planet|mars|jupiter|saturnus|roket|satelit|antariksa", ["kenapa mars merah", "bagaimana roket bekerja"]),
    "lubang hitam": (3.0, r"lubang (hitam|putih)|black hole", ["apa itu lubang hitam"]),
    "ufo & alien": (2.0, r"\bufo\b|\balien\b|makhluk asing", ["apa itu ufo", "kenapa alien"]),
    "laut dalam": (2.5, r"laut dalam|palung|hewan laut dalam|biolumines", ["misteri laut dalam", "kenapa laut dalam gelap"]),
    "air laut & ombak": (2.5, r"air laut|laut asin|ombak|pasang surut|arus laut", ["kenapa air laut asin", "kenapa ada ombak"]),
    "kapal & mengapung": (2.5, r"kapal|perahu|mengapung|tenggelam", ["kenapa kapal tidak tenggelam"]),
    "pesawat": (2.5, r"pesawat|turbulensi|jet|helikopter", ["kenapa pesawat bisa terbang", "kenapa pesawat takut turbulensi"]),
    "burung terbang": (2.0, r"burung|merpati|ayam|elang", ["kenapa burung bisa terbang", "kenapa burung terbang malam hari"]),
    "kucing": (2.0, r"kucing", ["kenapa kucing"]),  # Ep23
    "anjing": (2.0, r"anjing", ["kenapa anjing"]),
    "serangga": (2.0, r"nyamuk|semut|lalat|kecoa?k?|laba[- ]laba|kupu[- ]kupu|lebah", ["kenapa nyamuk", "kenapa semut"]),
    "ular & reptil": (2.0, r"ular|buaya|kadal|cicak|tokek|kura[- ]kura", ["kenapa ular"]),
    "es & salju": (2.0, r"\bes\b|salju|beku|embun es", ["kenapa es mengapung", "kenapa salju"]),
    "baterai & hp": (1.5, r"baterai|\bhp\b|ponsel|layar|cas|charg|panas", ["kenapa baterai cepat habis", "kenapa hp cepat panas"]),
    "internet & sinyal": (1.5, r"sinyal|internet|wifi|kuota|lambat|lemot", ["kenapa internet lambat", "kenapa sinyal hilang"]),
    "listrik & magnet": (2.5, r"listrik|magnet|korsleting|mati lampu", ["kenapa listrik berbahaya", "kenapa magnet"]),
    "langit & senja": (2.5, r"langit (biru|merah|gelap)|senja|terbenam", ["kenapa langit biru", "kenapa langit merah"]),
    "piramida & mesir": (2.5, r"piramida|mesir|firaun|sphinx", ["misteri piramida", "kenapa piramida"]),
    "situs misteri indonesia": (2.5, r"gunung padang|gunung lawu|situs|candi|keraton|curses|kutukan", ["misteri gunung padang", "misteri gunung lawu"]),
    "segitiga bermuda": (2.0, r"bermuda|segitiga|kapal hantu", ["misteri segitiga bermuda"]),
    "hantu & supranatural": (2.0, r"hantu|pocong|kuntilanak|arwah|penunggu|keras", ["misteri hantu", "kenapa hantu"]),  # sains: tindihan/pareidolia/infrasonik
    "gula & makanan": (2.0, r"gula|kopi|pedas|bawang|makanan pedas|garam", ["kenapa kopi membuat susah tidur", "kenapa makan pedas"]),
    "menangis & emosi": (2.0, r"menangis|nangis|sedih|stres|cemas|kaget", ["kenapa menangis", "kenapa gampang stres"]),
}


def bucket_seed(q):
    n = len(q.replace("kenapa ", "").split())
    if len(q.replace("kenapa ", "")) <= 4:
        return "A"
    return "B" if n <= 3 else "C"


def main():
    frasa = {}   # teks -> dict(sumber set, pos min, bucket terbaik)
    req = 0

    def catat(daftar, sumber, bk):
        for teks, pos in daftar:
            teks = teks.strip().lower()
            if not (3 <= len(teks) <= 70):
                continue
            f = frasa.setdefault(teks, {"sumber": set(), "pos": 99, "bucket": "C"})
            f["sumber"].add(sumber)
            f["pos"] = min(f["pos"], pos)
            if bk < f["bucket"]:
                f["bucket"] = bk

    print("== Lapis 1: awalan pendek (permintaan volume besar) ==")
    for aw in AWALAN:
        q = "kenapa " + aw
        bk = "A"
        catat(g(q), "g", bk); req += 1
        catat(yt(q), "yt", bk); req += 1

    print("== Lapis 2: pola seed per tema ==")
    for tema, (_, _, seeds) in TEMA.items():
        for s in seeds:
            bk = bucket_seed(s)
            catat(g(s), "g", bk); req += 1
            catat(yt(s), "yt", bk); req += 1

    # HAPUS TOTAL topik blokir ("kentut dll"): buang frasanya SEBELUM atribusi -
    # tidak pernah masuk per_tema, peringkat, JSON, maupun laporan.
    rx_b = [re.compile(TEMA[t][1]) for t in BLOKIR if t in TEMA]
    buang = {t for t in list(frasa) if any(r.search(t) for r in rx_b)}
    for t in buang:
        del frasa[t]

    # atribusi tema (urutan dict: spesifik -> umum)
    per_tema = defaultdict(set)
    lain = set()
    for teks, f in frasa.items():
        for tema, (_, rx, _) in TEMA.items():
            if re.search(rx, teks):
                per_tema[tema].add(teks)
                break
        else:
            lain.add(teks)

    SUDAH = {"kucing": "Ep23", "gempa bumi": "Ep22", "mimpi & tidur": "Ep21+Ep25",
             "bulan": "Ep24", "dinosaurus": "Ep26", "ngorok": "Ep27", "perut & pencernaan": "Ep28",
             "kram & kesemutan": "Ep29"}
    ANTREAN_LAMA = {"uban & rambut", "petir", "aurora", "situs misteri indonesia",
                    "demam & imun", "megalodon", "kapal & mengapung"}
    NIAT = ("hari ini", "malam ini", "sekarang", "berbahaya", "bahaya", "aman", "kapan",
            "berapa", "cara", "apakah", "padahal", "tiba-tiba", "terus")
    # sinyal pertumbuhan (v3): dihitung dari TEKS frasa
    REL = ("aku", "gue", "lu", "lo", "saya", "ane", "sering", "selalu", "padahal",
           "tiba-tiba", "terus", "pas ", "waktu ", "karena")
    KOMEN = ("aku", "gue", "lu", "lo", "saya", "ane", "punya", "anak", "kucing",
             "ibu", "pacar", "adik", "orang rumah")
    VIS = ("bunyi", "suara", "warna", "tampak", "keluar", "getar", "goyang", "pecah",
           "menyala", "asap", "api", "merah", "biru", "kuning", "berdenyut", "gerak",
           "naik", "turun", "bergelembung", "kilau")
    EVENT = ("hari ini", "2026", "2027", "lebaran", "imlek", "tahun baru", "piala",
             "pemilu", "kemerdekaan", "ramadan", "puasa")

    baris = []
    for tema, (_, rx, _) in TEMA.items():
        fs = sorted(per_tema.get(tema, ()))
        if len(fs) < 4:
            continue
        jml = len(fs)
        kuat = sum(1 for f in fs if len(f.split()) <= 5 and frasa[f]["bucket"] in "AB")
        niat = sum(1 for f in fs if any(k in f for k in NIAT))
        yt_n = sum(1 for f in fs if "yt" in frasa[f]["sumber"])
        sains = TEMA[tema][0]
        skor = jml + kuat * 0.7 + niat * 0.9 + sains * 3 + yt_n * 0.3
        rel = sum(1 for f in fs if any(k in f for k in REL))
        kom = sum(1 for f in fs if any(k in f for k in KOMEN))
        vis = sum(1 for f in fs if any(k in f for k in VIS))
        ever = 1.0 if not any(k in f for f in fs for k in EVENT) else 0.3
        skor_tumbuh = skor + rel * 1.2 + kom * 1.5 + vis * 0.8 + ever * 3
        status = SUDAH.get(tema, "")
        if not status:
            status = "antrean lama" if tema in ANTREAN_LAMA else "SEGAR"
        baris.append({"tema": tema, "jml": jml, "kuat": kuat, "niat": niat,
                      "yt": yt_n, "sains": sains, "skor": round(skor, 1),
                      "rel": rel, "kom": kom, "vis": vis, "ever": ever,
                      "skor_tumbuh": round(skor_tumbuh, 1),
                      "status": status, "contoh": fs[:6]})

    baris.sort(key=lambda b: -b["skor_tumbuh"])
    tgl = date.today().isoformat()
    out = {"tanggal": tgl, "jumlah_permintaan": req, "frasa_unik": len(frasa),
           "di_luar_tema": len(lain), "peringkat": baris, "frasa": {k: {"sumber": sorted(v["sumber"]),
           "pos": v["pos"], "bucket": v["bucket"]} for k, v in frasa.items()}}
    jp = os.path.join(BASE, f"hasil_mendalam_{tgl.replace('-', '')}.json")
    json.dump(out, open(jp, "w"), ensure_ascii=False, indent=1)

    md = ["# KlikTahu - Analisis Mendalam Real-Time v3 (" + tgl + ")",
          "",
          f"**Permintaan:** {req} panggilan autocomplete (Google hl=id + YouTube ds=yt, gl=id)",
          f"**Frasa unik:** {len(frasa)} ({len(lain)} di luar tema) - sumber: {jp.split('/')[-1]}",
          "",
          "- `skor` = jml + kuat*0,7 + niat*0,9 + sains*3 + yt*0,3 (yt = frasa yang muncul di YouTube = ada yang mencari DAN menonton)",
          "- `skor_tumbuh` = skor + rel*1,2 + kom*1,5 + vis*0,8 + ever*3",
          "  - rel = frasa pengalaman pribadi/keseharian (relatabilitas), kom = frasa yang mengundang bercerita (komentar cepat),",
          "  - vis = fenomena yang bisa diperlihatkan (retensi & share), ever = 1 kalau bebas frasa musiman (evergreen).",
          "- Urutan tabel: skor_tumbuh (sinyal pertumbuhan channel), bukan volume semata.",
          "",
          "| # | tema | jml | kuat | niat | yt | sains | rel | kom | vis | ever | skor | skor_tumbuh | status | contoh terkuat |",
          "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for i, b in enumerate(baris, 1):
        md.append(f"| {i} | {b['tema']} | {b['jml']} | {b['kuat']} | {b['niat']} | {b['yt']} | "
                  f"{b['sains']} | {b['rel']} | {b['kom']} | {b['vis']} | {b['ever']} | "
                  f"{b['skor']} | **{b['skor_tumbuh']}** | {b['status']} | " +
                  " · ".join("`" + c + "`" for c in b["contoh"][:3]) + " |")
    kandidat = [b for b in baris if b["status"] == "SEGAR" and b["sains"] >= 2.0][:8]
    md += ["", "## Kandidat segar teratas (belum dibahas, bukan antrean lama, cocok sains) — urut skor_tumbuh"]
    for i, b in enumerate(kandidat, 1):
        md.append(f"{i}. **{b['tema']}** - skor_tumbuh {b['skor_tumbuh']} (skor {b['skor']}; jml {b['jml']}, kuat {b['kuat']}, "
                  f"yt {b['yt']}, rel {b['rel']}, kom {b['kom']}, vis {b['vis']}, ever {b['ever']}) - contoh: " +
                  ", ".join("`" + c + "`" for c in b["contoh"][:4]))
    open(os.path.join(BASE, "HASIL_MENDALAM.md"), "w").write("\n".join(md) + "\n")

    print(f"\nfrasa unik: {len(frasa)} | tema terisi: {sum(1 for b in baris if b['jml']>=4)}")
    print("\nTOP 15 (skor_tumbuh):")
    for i, b in enumerate(baris[:15], 1):
        print(f" {i:2d}. {b['tema']:26s} tumbuh {b['skor_tumbuh']:6.1f} (skor {b['skor']:6.1f}, jml {b['jml']}, "
              f"kuat {b['kuat']}, niat {b['niat']}, yt {b['yt']}, rel {b['rel']}, kom {b['kom']}, vis {b['vis']}) [{b['status']}]")
    print("\nKANDIDAT SEGAR (belum dibahas + sains >= 2, urut skor_tumbuh):")
    for i, b in enumerate(kandidat, 1):
        print(f" {i}. {b['tema']:26s} tumbuh {b['skor_tumbuh']:6.1f}")


if __name__ == "__main__":
    main()
