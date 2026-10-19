#!/usr/bin/env python3
"""ANALISIS v6 "PAPAN STRATEGI" — dari 'topik apa yang dicari' ke 'topik apa yang MENANG'.

v5 menjawab PERMINTAAN (autocomplete + velocity + kalender). v6 menambahkan empat
lapisan yang menentukan apakah video benar-benar tumbuh:

  1. PESAING YOUTUBE (supply)  — untuk tiap kandidat, hasil pencarian YouTube (filter
     video pendek) dibedah: median views 10 teratas (bukti topik ini BISA meledak),
     jumlah unggahan < 12 bulan (seberapa padat persaingan baru), dan umur video
     juara. CELAH = bukti permintaan besar tapi pemainnya lama/sedikit.
  2. TREN WIKIPEDIA (id)        — pageviews harian 60 hari artikel terkait: level
     rata-rata 30 hari + MOMENTUM (7 hari terakhir vs 23 hari sebelumnya). Sinyal
     permintaan INDEPENDEN dari autocomplete (mencegah salah baca dari satu sumber).
  3. PENAMBANG SUDUT & HOOK     — frasa asli dipilah ke sudut (PADAHAL/paradoks,
     MITOS, BAHAYA, PRIBADI, ANAK, PRAKTIS). Sudut terkuat -> 3 draf hook 2 detik
     pertama dengan pola yang terbukti menahan penonton Shorts.
  4. PILAR NICHE + UMPAN BALIK  — tema dipetakan ke 6 pilar (TUBUH, LANGIT,
     BUMI & CUACA, TEKNOLOGI, MISTERI, HEWAN). Pilar yang baru saja dipakai dapat
     jeda (anti-bosan), pilar yang terbukti ditonton (analisis/performa.csv, diisi
     dari YouTube Studio) mendapat bobot lebih. Hasil: kalender 7 episode.

skor_v6 (0-100) = 34*permintaan + 18*wiki + 18*celah + 10*visual + 10*pilar + 10*momen
(semua komponen dinormalisasi 0-1 & ditampilkan di laporan - transparan, bisa dicek).

Jalan:  python3 analisis/mesin_v6.py          (CI, butuh internet; degradasi anggun)
        python3 analisis/mesin_v6.py --uji    (fixture offline, wajib lulus sebelum push)
Keluaran: analisis/STRATEGI_V6.md + analisis/strategi_v6_<YYYYMMDD>.json
"""
import glob
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

UA = {"User-Agent": "KlikTahuAnalisis/6.0 (github.com/chronoidchannel-stack/KlikTahu-) python-urllib",
      "Accept-Language": "id-ID,id;q=0.9,en;q=0.6"}
UA_WEB = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
          "Accept-Language": "id-ID,id;q=0.9,en;q=0.6"}
JEDA = float(os.environ.get("KT_V6_JEDA", "0.35"))
N_KANDIDAT = int(os.environ.get("KT_V6_KANDIDAT", "18"))

# ------------------------------------------------------------------ peta tema
# tema -> (pilar, [artikel id.wikipedia], kueri pesaing YouTube)
PETA = {
    "petir": ("BUMI & CUACA", ["Petir", "Guntur"], "kenapa petir"),
    "pelangi": ("BUMI & CUACA", ["Pelangi"], "kenapa pelangi"),
    "hujan & awan": ("BUMI & CUACA", ["Hujan", "Awan"], "kenapa hujan turun"),
    "angin & badai": ("BUMI & CUACA", ["Puting_beliung", "Angin"], "kenapa ada puting beliung"),
    "gunung api": ("BUMI & CUACA", ["Gunung_berapi"], "kenapa gunung meletus"),
    "gempa bumi": ("BUMI & CUACA", ["Gempa_bumi"], "kenapa gempa terjadi"),
    "air laut & ombak": ("BUMI & CUACA", ["Air_laut", "Pasang_surut"], "kenapa air laut asin"),
    "laut dalam": ("BUMI & CUACA", ["Palung_Mariana", "Laut_dalam"], "misteri laut dalam"),
    "es & salju": ("BUMI & CUACA", ["Salju", "Es"], "kenapa es mengapung"),
    "langit & senja": ("BUMI & CUACA", ["Langit", "Senja"], "kenapa langit biru"),
    "gerhana": ("LANGIT", ["Gerhana_bulan", "Gerhana_matahari"], "kenapa terjadi gerhana"),
    "matahari": ("LANGIT", ["Matahari"], "fakta matahari"),
    "bulan": ("LANGIT", ["Bulan"], "kenapa bulan"),
    "bintang & galaksi": ("LANGIT", ["Bintang", "Galaksi_Bima_Sakti"], "kenapa bintang berkelip"),
    "planet & roket": ("LANGIT", ["Mars", "Roket"], "kenapa mars merah"),
    "lubang hitam": ("LANGIT", ["Lubang_hitam"], "apa itu lubang hitam"),
    "aurora": ("LANGIT", ["Aurora"], "kenapa ada aurora"),
    "meteor & komet": ("LANGIT", ["Meteor", "Komet"], "kenapa meteor jatuh"),
    "ufo & alien": ("MISTERI", ["Objek_terbang_tak_dikenal"], "misteri ufo"),
    "hantu & supranatural": ("MISTERI", ["Hantu"], "sains hantu"),
    "segitiga bermuda": ("MISTERI", ["Segitiga_Bermuda"], "misteri segitiga bermuda"),
    "situs misteri indonesia": ("MISTERI", ["Situs_Gunung_Padang", "Gunung_Lawu"], "misteri gunung padang"),
    "piramida & mesir": ("MISTERI", ["Piramida_Giza"], "misteri piramida"),
    "megalodon": ("HEWAN", ["Megalodon"], "megalodon masih hidup"),
    "dinosaurus": ("HEWAN", ["Dinosaurus"], "kenapa dinosaurus punah"),
    "kucing": ("HEWAN", ["Kucing"], "kenapa kucing"),
    "anjing": ("HEWAN", ["Anjing"], "kenapa anjing"),
    "serangga": ("HEWAN", ["Nyamuk", "Semut"], "kenapa nyamuk suka menggigit"),
    "ular & reptil": ("HEWAN", ["Ular", "Cicak"], "kenapa cicak"),
    "burung terbang": ("HEWAN", ["Burung"], "kenapa burung bisa terbang"),
    "baterai & hp": ("TEKNOLOGI", ["Baterai_litium-ion"], "kenapa baterai cepat habis"),
    "internet & sinyal": ("TEKNOLOGI", ["Internet", "Wi-Fi"], "kenapa sinyal hilang"),
    "listrik & magnet": ("TEKNOLOGI", ["Listrik", "Magnet"], "kenapa listrik bisa menyetrum"),
    "pesawat": ("TEKNOLOGI", ["Pesawat_terbang"], "kenapa pesawat bisa terbang"),
    "kapal & mengapung": ("TEKNOLOGI", ["Kapal"], "kenapa kapal tidak tenggelam"),
}
PILAR_TUBUH = "TUBUH"          # tema lain (default) = tubuh & kesehatan
PILAR_SEMUA = ("TUBUH", "LANGIT", "BUMI & CUACA", "TEKNOLOGI", "MISTERI", "HEWAN")
WIKI_TUBUH = {
    "mata": ["Mata"], "mimpi & tidur": ["Mimpi", "Tidur"], "gigi & mulut": ["Gigi"],
    "perut & pencernaan": ["Lambung"], "kram & kesemutan": ["Kram"], "kulit": ["Jerawat"],
    "pusing & migrain": ["Migrain"], "cegukan": ["Cegukan"], "kuping": ["Tinitus", "Telinga"],
    "jantung & dada": ["Jantung"], "tekanan darah": ["Hipertensi"], "menangis & emosi": ["Menangis", "Stres"],
    "uban & rambut": ["Uban", "Rambut"], "batuk flu pilek": ["Batuk", "Influenza"],
    "demam & imun": ["Demam"], "mimisan & hidung": ["Mimisan"], "kuku": ["Kuku"],
    "gusi & rahang": ["Gingivitis"], "kedutan": ["Kedutan"], "ngorok": ["Mendengkur"],
    "gula & makanan": ["Kafein", "Gula"],
}

# ------------------------------------------------------------------ sudut & hook
SUDUT = [
    ("PADAHAL", r"\bpadahal\b|\btapi\b|\bkok\b|\bmalah\b",
     "Paradoks: jawaban melawan intuisi = rasa penasaran paling kuat"),
    ("MITOS", r"\bmitos\b|\bbenarkah\b|\bapakah benar\b|\bkatanya\b|\bpertanda\b|\bkonon\b",
     "Membongkar mitos = komentar & share (orang ingin mengoreksi temannya)"),
    ("BAHAYA", r"bahaya|berbahaya|\baman\b|\bmati\b(?! (lampu|listrik|total))|\bmeninggal\b|\btewas\b|\bcelaka\b",
     "Taruhan tinggi: penonton bertahan untuk tahu apakah dirinya aman"),
    ("PRIBADI", r"\baku\b|\bsaya\b|\bgue\b|\bsering\b|\bselalu\b|\bterus\b|\btiba[- ]tiba\b",
     "Relevansi pribadi: 'ini aku banget' = tonton ulang & komentar cerita"),
    ("ANAK", r"\banak\b|\bbayi\b|\bbalita\b",
     "Orang tua menonton untuk anaknya = share ke grup keluarga"),
    ("PRAKTIS", r"\bcara\b|\bkapan\b|\bberapa\b|\bharus\b|\bboleh\b",
     "Nilai praktis = disimpan (save) -> sinyal kualitas"),
]

HOOK_POLA = {
    "PADAHAL": ["{Inti}? Padahal jawabannya bukan yang kamu kira.",
                "Semua orang pernah mengalami {inti}. Hampir tidak ada yang tahu kenapa.",
                "Kelihatannya sepele: {inti}. Tapi yang terjadi di baliknya luar biasa."],
    "MITOS": ["Kamu pasti pernah dengar mitos soal {inti}. Ternyata sainsnya berkata lain.",
              "Satu hal tentang {inti} yang diajarkan dari kecil ternyata keliru.",
              "Benarkah {inti} seperti kata orang tua? Mari kita buktikan."],
    "BAHAYA": ["{Inti}: kapan aman, kapan berbahaya? Tiga puluh detik pertama ini penting.",
               "Ini yang sebenarnya terjadi saat {inti}, dan kenapa kamu perlu tahu.",
               "Satu kesalahan kecil soal {inti} bisa berakibat fatal."],
    "PRIBADI": ["Pernah mengalami {inti}? Ini yang terjadi di dalam tubuhmu.",
                "Kalau kamu sering {inti}, video ini untukmu.",
                "{Inti} bukan kebetulan. Ada mekanismenya."],
    "ANAK": ["Anak bertanya kenapa {inti}? Ini jawaban yang bisa kamu jelaskan dalam satu menit.",
             "Pertanyaan anak kecil yang bikin orang dewasa bingung: kenapa {inti}?",
             "Jelaskan {inti} ke anakmu dengan cara ini."],
    "PRAKTIS": ["Semua yang perlu kamu tahu soal {inti}, dalam satu menit.",
                "{Inti}: tiga hal yang jarang dijelaskan.",
                "Simpan video ini sebelum kamu mengalami {inti}."],
}


# ------------------------------------------------------------------ jaringan
def _get(url, headers, timeout=15):
    time.sleep(JEDA)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def wiki_pageviews(artikel, hari_ini):
    """Pageviews harian 60 hari (id.wikipedia, user). Return list int atau None."""
    akhir = hari_ini - timedelta(days=1)
    awal = akhir - timedelta(days=59)
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/id.wikipedia/"
           f"all-access/user/{urllib.parse.quote(artikel)}/daily/"
           f"{awal:%Y%m%d}00/{akhir:%Y%m%d}00")
    try:
        data = json.loads(_get(url, UA))
        return [int(it.get("views", 0)) for it in data.get("items", [])]
    except Exception:
        return None


def cari_judul_wiki(q):
    """Judul artikel id.wikipedia yang benar untuk kata kunci (opensearch)."""
    url = ("https://id.wikipedia.org/w/api.php?action=opensearch&limit=1&namespace=0&format=json"
           "&redirects=resolve&search=" + urllib.parse.quote(q))
    try:
        data = json.loads(_get(url, UA))
        if len(data) > 1 and data[1]:
            return data[1][0].replace(" ", "_")
    except Exception:
        pass
    return None


def wiki_tema(artikel, hari_ini):
    """Pageviews tiap artikel; kalau judul tidak ada, cari judul yang benar lalu ulangi."""
    seri, dipakai = [], []
    for a in artikel:
        s = wiki_pageviews(a, hari_ini)
        if s is None:
            alt = cari_judul_wiki(a.replace("_", " "))
            if alt and alt != a:
                s = wiki_pageviews(alt, hari_ini)
                a = alt
        if s:
            seri.append(s)
            dipakai.append(a)
    w = ringkas_wiki(seri)
    if w:
        w["artikel"] = dipakai
    return w


def ringkas_wiki(seri_list):
    """Gabungkan beberapa artikel -> level (rata 30 hari) & momentum (7 vs 23 hari)."""
    seri = [s for s in seri_list if s]
    if not seri:
        return None
    n = min(len(s) for s in seri)
    if n < 30:
        return None
    total = [sum(s[-n:][i] for s in seri) for i in range(n)]
    t30 = total[-30:]
    level = sum(t30) / 30.0
    a7 = sum(t30[-7:]) / 7.0
    b23 = sum(t30[:23]) / 23.0
    mom = (a7 / b23 - 1.0) if b23 > 0 else 0.0
    return {"level30": round(level, 1), "momentum": round(mom, 3), "hari": n,
            "puncak7": max(t30[-7:])}


_RX_ANGKA = re.compile(r"([\d][\d.,]*)\s*([KMB]|rb|jt|ribu|juta|miliar)?", re.I)


def _angka_views(teks):
    if not teks:
        return None
    t = teks.replace("\u00a0", " ").strip()
    if re.search(r"no views|tidak ada", t, re.I):
        return 0
    m = _RX_ANGKA.search(t)
    if not m:
        return None
    raw, suf = m.group(1), (m.group(2) or "").lower()
    if suf:
        num = float(raw.replace(",", "."))
        mult = {"k": 1e3, "rb": 1e3, "ribu": 1e3, "m": 1e6, "jt": 1e6, "juta": 1e6,
                "b": 1e9, "miliar": 1e9}[suf]
        return int(num * mult)
    return int(re.sub(r"[.,]", "", raw) or 0)


def _umur_bulan(teks):
    if not teks:
        return None
    t = teks.lower()
    m = re.search(r"(\d+)\s*(second|minute|hour|day|week|month|year|detik|menit|jam|hari|minggu|bulan|tahun)", t)
    if not m:
        return None
    n = int(m.group(1))
    u = m.group(2)
    faktor = {"second": 0, "minute": 0, "hour": 0, "detik": 0, "menit": 0, "jam": 0,
              "day": 1 / 30, "hari": 1 / 30, "week": 0.23, "minggu": 0.23,
              "month": 1, "bulan": 1, "year": 12, "tahun": 12}[u]
    return round(n * faktor, 2)


def _jalan(node, keluar):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("videoRenderer", "reelItemRenderer") and isinstance(v, dict):
                keluar.append((k, v))
            else:
                _jalan(v, keluar)
    elif isinstance(node, list):
        for v in node:
            _jalan(v, keluar)


def _teks(o):
    if not isinstance(o, dict):
        return ""
    if "simpleText" in o:
        return o["simpleText"]
    return "".join(r.get("text", "") for r in o.get("runs", []))


def parse_youtube(html):
    """Ambil daftar video dari ytInitialData (hasil pencarian YouTube)."""
    m = re.search(r"var ytInitialData\s*=\s*(\{.*?\});\s*</script>", html, re.S)
    if not m:
        m = re.search(r"ytInitialData\"\]\s*=\s*(\{.*?\});", html, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except Exception:
        return []
    items = []
    _jalan(data, items)
    out = []
    for jenis, v in items:
        if jenis == "videoRenderer":
            judul = _teks(v.get("title"))
            views = _angka_views(_teks(v.get("viewCountText")))
            umur = _umur_bulan(_teks(v.get("publishedTimeText")))
            kanal = _teks(v.get("ownerText"))
        else:
            judul = _teks(v.get("headline"))
            views = _angka_views(_teks(v.get("viewCountText")))
            umur, kanal = None, ""
        if judul:
            out.append({"judul": judul, "views": views, "umur_bln": umur, "kanal": kanal})
    return out


def pesaing_youtube(kueri):
    """Bedah 20 hasil teratas pencarian YouTube (filter durasi < 4 menit)."""
    url = ("https://www.youtube.com/results?search_query=" + urllib.parse.quote(kueri)
           + "&sp=EgIYAQ%253D%253D&hl=en&gl=ID&persist_hl=1&persist_gl=1")
    try:
        vids = parse_youtube(_get(url, UA_WEB, timeout=20))
    except Exception:
        vids = []
    return ringkas_pesaing(vids, kueri)


def ringkas_pesaing(vids, kueri):
    vids = [v for v in vids if v.get("judul")][:20]
    if not vids:
        return None
    top = [v for v in vids[:10] if v.get("views") is not None]
    vs = sorted(v["views"] for v in top) or [0]
    med = vs[len(vs) // 2]
    baru = sum(1 for v in vids if v.get("umur_bln") is not None and v["umur_bln"] <= 12)
    tua = [v["umur_bln"] for v in vids[:10] if v.get("umur_bln") is not None]
    inti = re.sub(r"^(kenapa|apa itu|misteri|fakta|sains)\s+", "", kueri).split()
    cocok = sum(1 for v in vids if all(w in v["judul"].lower() for w in inti[:2]))
    juara = max(top, key=lambda v: v["views"]) if top else vids[0]
    return {"n": len(vids), "median_views_top10": med, "unggahan_12bln": baru,
            "umur_median_bln": sorted(tua)[len(tua) // 2] if tua else None,
            "judul_cocok": cocok,
            "juara": {"judul": juara["judul"][:90], "views": juara.get("views"),
                      "umur_bln": juara.get("umur_bln"), "kanal": juara.get("kanal", "")},
            "judul_top": [v["judul"][:80] for v in vids[:6]]}


# ------------------------------------------------------------------ skor
def _norm(v, lo, hi):
    if v is None:
        return 0.0
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (v - lo) / (hi - lo)))


def skor_celah(p):
    """Celah = bukti permintaan (views juara besar) / padatnya pemain baru."""
    if not p:
        return None
    bukti = math.log10(1 + (p["median_views_top10"] or 0))           # 0..7
    padat = p["unggahan_12bln"] / max(1, p["n"])                      # 0..1
    tua = min(1.0, (p["umur_median_bln"] or 0) / 36.0)               # video juara lama = celah
    return round(_norm(bukti, 3.0, 6.5) * 0.55 + (1 - padat) * 0.25 + tua * 0.20, 3)


def sudut_tema(frasa):
    hit = defaultdict(list)
    for f in frasa:
        for nama, rx, _ in SUDUT:
            if re.search(rx, f):
                hit[nama].append(f)
    urut = sorted(hit.items(), key=lambda kv: -len(kv[1]))
    return [(k, len(v), v[:3]) for k, v in urut]


HOOK_HINDARI = re.compile(r"\b(haram|halal|islam|kristen|agama|dosa|mahal|murah|harga|tarif|bayar|"
                          r"oppo|vivo|infinix|realme|samsung|iphone|xiaomi|ml|ff|game)\b")


def buat_hook(tema, frasa, sudut):
    seeds = sorted([f for f in frasa if f.startswith("kenapa ") and not HOOK_HINDARI.search(f)
                    and len(f.split()) <= 5], key=len)
    inti = seeds[0][len("kenapa "):] if seeds else tema.split(" & ")[0]
    inti = inti.strip()
    nama = sudut[0][0] if sudut else "PADAHAL"
    return [p.format(inti=inti, Inti=inti[:1].upper() + inti[1:]) for p in HOOK_POLA[nama]]


def pilar_tema(tema):
    return PETA[tema][0] if tema in PETA else PILAR_TUBUH


def riwayat_pilar(sudah_ep):
    urut = sorted(sudah_ep.items(), key=lambda kv: int(re.sub(r"\D", "", kv[0]) or 0))
    return [(ep, pilar_tema(t)) for ep, t in urut]


def baca_performa():
    """analisis/performa.csv: episode,views_48jam,rata_ditonton_persen,suka,komentar,share.
    Baris kosong diabaikan. Return {pilar: indeks_relatif} (1.0 = rata-rata channel)."""
    p = os.path.join(BASE, "performa.csv")
    if not os.path.exists(p):
        return {}, 0
    import mesin_v5 as v5
    per = defaultdict(list)
    n = 0
    for baris in open(p, encoding="utf-8"):
        baris = baris.strip()
        if not baris or baris.startswith("#") or baris.lower().startswith("episode"):
            continue
        kol = [k.strip() for k in baris.split(",")]
        if len(kol) < 2 or not kol[1]:
            continue
        try:
            views = float(kol[1].replace(".", ""))
        except ValueError:
            continue
        tema = v5.SUDAH_EP.get(kol[0])
        if not tema:
            continue
        per[pilar_tema(tema)].append(views)
        n += 1
    if not per:
        return {}, 0
    semua = [v for vs in per.values() for v in vs]
    rata = sum(semua) / len(semua)
    return {k: round((sum(v) / len(v)) / rata, 2) for k, v in per.items()}, n


def skor_pilar(pilar, riwayat, perf):
    terakhir = [p for _, p in riwayat[-3:]]
    jeda = 1.0
    if terakhir and terakhir[-1] == pilar:
        jeda = 0.15
    elif pilar in terakhir:
        jeda = 0.55
    bobot = perf.get(pilar, 1.0)
    return round(max(0.0, min(1.0, jeda * min(1.4, bobot))), 3)


# ------------------------------------------------------------------ inti
def muat_v5():
    kand = sorted(glob.glob(os.path.join(BASE, "hasil_v5_*.json")))
    if not kand:
        return None, None
    return json.load(open(kand[-1])), os.path.basename(kand[-1])


def frasa_per_tema():
    """Semua frasa terbaru per tema (dari snapshot v3 terakhir) untuk penambang sudut."""
    import sapuan_mendalam as sm
    kand = sorted(glob.glob(os.path.join(BASE, "hasil_mendalam_*.json")))
    if not kand:
        return {}
    data = json.load(open(kand[-1])).get("frasa", {})
    rx = {t: re.compile(v[1]) for t, v in sm.TEMA.items()}
    per = defaultdict(list)
    for teks in data:
        for tema, r in rx.items():
            if r.search(teks):
                per[tema].append(teks)
                break
    return per


def analisis(v5, frasa_tema, hari_ini, online=True, fixture=None):
    import mesin_v5 as m5
    sudah_ep = dict(m5.SUDAH_EP)
    riwayat = riwayat_pilar(sudah_ep)
    perf, n_perf = baca_performa()
    sudah = set(sudah_ep.values())
    baris = v5["peringkat"]
    maks_v5 = max(b["skor_views"] for b in baris) or 1.0
    kandidat = [b for b in baris if b["tema"] not in sudah and b["tema"] not in m5_blokir()]
    kandidat = sorted(kandidat, key=lambda b: -b["skor_views"])[:N_KANDIDAT]
    sekuel = [b for b in baris if b["tema"] in sudah and b.get("velocity", 0) >= 8][:5]

    hasil = []
    wiki_levels = []
    for b in kandidat:
        tema = b["tema"]
        artikel = PETA[tema][1] if tema in PETA else WIKI_TUBUH.get(tema, [])
        if not artikel:
            artikel = [w.strip().capitalize() for w in tema.split("&")]
        if fixture is not None:
            w = fixture.get("wiki", {}).get(tema)
            p = ringkas_pesaing(fixture.get("yt", {}).get(tema, []), PETA.get(tema, ("", [], tema))[2])
        elif online:
            w = wiki_tema(artikel, hari_ini)
            kueri = PETA[tema][2] if tema in PETA else ("kenapa " + (b["contoh"][0].replace("kenapa ", "")
                                                                  if b.get("contoh") else tema))
            p = pesaing_youtube(kueri)
        else:
            w, p = None, None
        if w:
            wiki_levels.append(w["level30"])
        fr = frasa_tema.get(tema, []) or b.get("contoh", [])
        sd = sudut_tema(fr)
        hasil.append({"tema": tema, "pilar": pilar_tema(tema), "v5": b, "wiki": w,
                      "pesaing": p, "sudut": sd, "hook": buat_hook(tema, fr, sd),
                      "artikel": artikel})

    lv_max = max([math.log10(1 + x) for x in wiki_levels] or [1.0])
    for h in hasil:
        b = h["v5"]
        k_perm = _norm(b["skor_views"], 0, maks_v5)
        if h["wiki"]:
            k_wiki = 0.7 * _norm(math.log10(1 + h["wiki"]["level30"]), 1.0, lv_max) + \
                0.3 * _norm(h["wiki"]["momentum"], -0.3, 0.5)
        else:
            k_wiki = 0.35                                    # netral bila data tidak ada
        c = skor_celah(h["pesaing"])
        k_celah = c if c is not None else 0.4
        k_vis = _norm(b.get("vis", 0) * 0.8 + b.get("sains", 2) * 6, 8, 30)
        k_pilar = skor_pilar(h["pilar"], riwayat, perf)
        k_momen = 1.0 if (b.get("momen_hari") is not None and b["momen_hari"] <= 14) else \
            0.6 if b.get("momen") else 0.0
        skor = 34 * k_perm + 18 * k_wiki + 18 * k_celah + 10 * k_vis + 10 * k_pilar + 10 * k_momen
        h["komponen"] = {"permintaan": round(k_perm, 3), "wiki": round(k_wiki, 3),
                         "celah": round(k_celah, 3), "visual": round(k_vis, 3),
                         "pilar": round(k_pilar, 3), "momen": round(k_momen, 3)}
        h["skor_v6"] = round(skor, 1)
    hasil.sort(key=lambda h: -h["skor_v6"])
    return {"hasil": hasil, "riwayat": riwayat, "perf": perf, "n_perf": n_perf,
            "sekuel": sekuel}


def m5_blokir():
    import sapuan_mendalam as sm
    return set(sm.BLOKIR)


def kalender(hasil, riwayat, hari_ini, n=7):
    """Susun 7 episode: skor tertinggi, tapi pilar yang sama tidak boleh beruntun."""
    sisa = list(hasil)
    jadwal = []
    pilar_akhir = riwayat[-1][1] if riwayat else None
    for i in range(n):
        if not sisa:
            break
        pilih = next((h for h in sisa if h["pilar"] != pilar_akhir), sisa[0])
        sisa.remove(pilih)
        tgl = hari_ini + timedelta(days=i + 1)
        jadwal.append((tgl, pilih))
        pilar_akhir = pilih["pilar"]
    return jadwal


def _fmt_views(v):
    if v is None:
        return "-"
    if v >= 1e6:
        return f"{v/1e6:.1f} jt"
    if v >= 1e3:
        return f"{v/1e3:.0f} rb"
    return str(int(v))


def tulis_laporan(res, v5, v5_nama, hari_ini, mode):
    H = res["hasil"]
    md = [f"# PAPAN STRATEGI v6 - KlikTahu ({hari_ini.isoformat()})", "",
          f"Mode: **{mode}** | dasar permintaan: `{v5_nama}` (v5, {v5.get('frasa_unik', '?')} frasa) | "
          f"kandidat dianalisis: {len(H)} | data performa: "
          f"{res['n_perf']} episode" + (" (isi `analisis/performa.csv` agar bobot pilar belajar dari views nyata)"
                                          if not res["n_perf"] else ""),
          "",
          "`skor_v6` (0-100) = 34 x permintaan + 18 x wiki + 18 x celah + 10 x visual + 10 x pilar + 10 x momen",
          "",
          "| # | tema | pilar | skor_v6 | permintaan | wiki (lvl/mom) | celah pesaing | median views top10 | unggahan <12bln | sudut terkuat |",
          "|---:|---|---|---:|---:|---|---:|---:|---:|---|"]
    for i, h in enumerate(H, 1):
        w = h["wiki"]
        p = h["pesaing"]
        k = h["komponen"]
        wtxt = f"{w['level30']:.0f}/hari {w['momentum']*100:+.0f}%" if w else "-"
        md.append(f"| {i} | **{h['tema']}** | {h['pilar']} | **{h['skor_v6']}** | {k['permintaan']:.2f} | "
                  f"{wtxt} | {k['celah']:.2f} | {_fmt_views(p['median_views_top10']) if p else '-'} | "
                  f"{p['unggahan_12bln'] if p else '-'} | "
                  f"{(h['sudut'][0][0] + ' (' + str(h['sudut'][0][1]) + ')') if h['sudut'] else '-'} |")
    if H:
        top = H[0]
        md += ["", f"## REKOMENDASI UTAMA: {top['tema'].upper()} (skor_v6 {top['skor_v6']})", ""]
        k = top["komponen"]
        alasan = sorted(k.items(), key=lambda kv: -kv[1])[:3]
        md.append("Unggul di: " + ", ".join(f"{a} {b:.2f}" for a, b in alasan) + ".")
        if top["pesaing"]:
            j = top["pesaing"]["juara"]
            md.append(f"Video juara pesaing: \"{j['judul']}\" - {_fmt_views(j['views'])} views"
                      + (f", umur {j['umur_bln']:.0f} bulan" if j.get("umur_bln") else "")
                      + ". Bedakan sudut & visual dari judul-judul ini:")
            md += [f"- {t}" for t in top["pesaing"]["judul_top"][:5]]
        if top["sudut"]:
            md += ["", "**Sudut yang terbukti dicari (dari frasa asli):**"]
            for nama, n, contoh in top["sudut"][:3]:
                ket = next(x[2] for x in SUDUT if x[0] == nama)
                md.append(f"- {nama} ({n} frasa) - {ket}. Contoh: " + ", ".join(f"`{c}`" for c in contoh))
        md += ["", "**Draf hook 2 detik pertama:**"] + [f"{i}. {x}" for i, x in enumerate(top["hook"], 1)]

    md += ["", "## KALENDER 7 EPISODE (rotasi pilar anti-bosan)", "",
           "| hari | tanggal | tema | pilar | skor_v6 | hook pembuka |", "|---|---|---|---|---:|---|"]
    hari_id = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    for tgl, h in kalender(H, res["riwayat"], hari_ini):
        md.append(f"| {hari_id[tgl.weekday()]} | {tgl:%d-%m-%Y} | {h['tema']} | {h['pilar']} | "
                  f"{h['skor_v6']} | {h['hook'][0]} |")
    md += ["", "Jam unggah yang disarankan (heuristik penonton Indonesia, uji A/B dari Studio): "
           "**11.30-12.30 WIB** (istirahat siang) atau **18.30-20.30 WIB** (santai malam)."]

    if res["sekuel"]:
        md += ["", "## PELUANG SEKUEL (tema sudah dibahas, permintaan masih melonjak)", ""]
        for b in res["sekuel"]:
            md.append(f"- **{b['tema']}** ({b['status']}) velocity {b['velocity']:+} - frasa baru: "
                      + ", ".join(f"`{x}`" for x in b.get("baru", [])[:3]))

    md += ["", "## PORTOFOLIO PILAR NICHE", "",
           "| pilar | episode terbit | 3 episode terakhir | indeks performa |", "|---|---:|---|---:|"]
    hit = defaultdict(int)
    for _, p in res["riwayat"]:
        hit[p] += 1
    tiga = [p for _, p in res["riwayat"][-3:]]
    for p in PILAR_SEMUA:
        md.append(f"| {p} | {hit[p]} | {'ya' if p in tiga else '-'} | "
                  f"{res['perf'].get(p, '-') if res['perf'] else '-'} |")
    md += ["", "## CARA MEMBACA & BERTINDAK",
           "1. Ambil rekomendasi utama kecuali ada momen kalender yang lebih dekat.",
           "2. Pakai sudut terkuat sebagai kerangka naskah; hook dari daftar di atas (ubah seperlunya).",
           "3. Lihat judul pesaing: jangan meniru, ambil sisi yang BELUM mereka jawab.",
           "4. Setelah 48 jam, isi `analisis/performa.csv` (views, % ditonton) - bobot pilar menyesuaikan otomatis.",
           "", f"_Dibuat otomatis oleh analisis/mesin_v6.py - {datetime.utcnow():%Y-%m-%d %H:%M} UTC_"]
    open(os.path.join(BASE, "STRATEGI_V6.md"), "w").write("\n".join(md) + "\n")


def simpan_json(res, hari_ini, mode):
    out = {"tanggal": hari_ini.isoformat(), "mode": mode,
           "peringkat": [{k: v for k, v in h.items() if k != "v5"} | {"skor_views_v5": h["v5"]["skor_views"]}
                         for h in res["hasil"]],
           "perf": res["perf"]}
    p = os.path.join(BASE, f"strategi_v6_{hari_ini:%Y%m%d}.json")
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
    return p


# ------------------------------------------------------------------ uji offline
def _uji():
    html = ('<script>var ytInitialData = {"contents":{"x":[{"videoRenderer":{"title":{"runs":[{"text":'
            '"Kenapa Petir Menyambar?"}]},"viewCountText":{"simpleText":"1,234,567 views"},'
            '"publishedTimeText":{"simpleText":"3 years ago"},"ownerText":{"runs":[{"text":"Sains"}]}}},'
            '{"videoRenderer":{"title":{"runs":[{"text":"petir itu apa"}]},"viewCountText":'
            '{"simpleText":"45K views"},"publishedTimeText":{"simpleText":"2 months ago"}}}]}};</script>')
    vids = parse_youtube(html)
    assert len(vids) == 2 and vids[0]["views"] == 1234567 and vids[1]["views"] == 45000, vids
    assert vids[0]["umur_bln"] == 36 and vids[1]["umur_bln"] == 2
    assert _angka_views("1,2 jt x ditonton") == 1200000
    assert _angka_views("12 rb x ditonton") == 12000
    p = ringkas_pesaing(vids, "kenapa petir")
    assert p and p["unggahan_12bln"] == 1 and p["judul_cocok"] >= 1
    assert 0 <= skor_celah(p) <= 1
    w = ringkas_wiki([[100] * 53 + [200] * 7])
    assert w and w["momentum"] > 0.9, w
    sd = sudut_tema(["kenapa petir menyambar padahal tidak hujan", "apakah petir berbahaya",
                     "mitos petir menyambar dua kali"])
    assert {s[0] for s in sd} >= {"PADAHAL", "BAHAYA", "MITOS"}, sd
    hk = buat_hook("petir", ["kenapa petir", "kenapa petir menyambar"], sd)
    assert len(hk) == 3 and all("petir" in x.lower() for x in hk), hk
    hk2 = buat_hook("anjing", ["kenapa anjing haram", "kenapa anjing menggonggong"], [])
    assert all("haram" not in x for x in hk2), hk2
    v5, _ = muat_v5()
    assert v5, "hasil_v5_*.json tidak ada"
    fixture = {"wiki": {}, "yt": {}}
    for b in v5["peringkat"][:40]:
        fixture["wiki"][b["tema"]] = ringkas_wiki([[50 + len(b["tema"])] * 60])
        fixture["yt"][b["tema"]] = vids
    res = analisis(v5, frasa_per_tema(), date.today(), online=False, fixture=fixture)
    assert res["hasil"] and all(0 <= h["skor_v6"] <= 100 for h in res["hasil"])
    kal = kalender(res["hasil"], res["riwayat"], date.today())
    for (a, b) in zip(kal, kal[1:]):
        assert a[1]["pilar"] != b[1]["pilar"] or len({h["pilar"] for h in res["hasil"]}) == 1
    print(f"UJI v6 LULUS: parser YouTube, wiki momentum, sudut, hook, skor ({len(res['hasil'])} kandidat), kalender")


def main():
    if "--uji" in sys.argv:
        _uji()
        return
    hari_ini = date.today()
    v5, v5_nama = muat_v5()
    if not v5:
        print("[v6] hasil_v5 tidak ada - jalankan mesin_v5.py dulu")
        return
    # cek jaringan sekali: kalau mati, laporan tetap dibuat (label OFFLINE)
    online = wiki_pageviews("Petir", hari_ini) is not None
    mode = "LIVE (Wikipedia pageviews + pesaing YouTube + autocomplete v5)" if online else \
        "OFFLINE (tanpa wiki/pesaing - komponen netral)"
    print("[v6]", mode)
    res = analisis(v5, frasa_per_tema(), hari_ini, online=online)
    tulis_laporan(res, v5, v5_nama, hari_ini, mode)
    p = simpan_json(res, hari_ini, mode)
    print(f"[v6] laporan -> analisis/STRATEGI_V6.md | data -> {os.path.basename(p)}")
    for i, h in enumerate(res["hasil"][:10], 1):
        pz = h["pesaing"]
        print(f" {i:2d}. {h['tema']:24s} {h['skor_v6']:5.1f}  pilar {h['pilar']:13s} "
              f"wiki {h['wiki']['level30'] if h['wiki'] else '-'}  "
              f"pesaing med {_fmt_views(pz['median_views_top10']) if pz else '-'}")


if __name__ == "__main__":
    main()
