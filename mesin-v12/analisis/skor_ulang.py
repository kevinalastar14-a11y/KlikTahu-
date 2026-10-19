#!/usr/bin/env python3
"""Hitung ULANG skor dari hasil_mendalam_<tanggal>.json TANPA sapuan baru.

Dipakai saat atribusi tema diperbaiki (regex \b, tema baru) supaya data mentah
yang sudah mahal (ratusan panggilan autocomplete) tidak dibuang.
"""
import json, os, re, sys
from collections import defaultdict
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else None
if not src:
    kandidat = sorted(f for f in os.listdir(BASE) if f.startswith("hasil_mendalam_") and f.endswith(".json"))
    src = os.path.join(BASE, kandidat[-1])

# ---- salin struktur TEMA dari sapuan_mendalam.py (sudah diperbaiki) ----
import importlib.util
spec = importlib.util.spec_from_file_location("sm", os.path.join(BASE, "sapuan_mendalam.py"))
sm = importlib.util.module_from_spec(spec)
import types
# muat hanya konstanta TEMA tanpa menjalankan main()
kode = open(os.path.join(BASE, "sapuan_mendalam.py")).read()
pohon = ast_module = __import__("ast")
tree = pohon.parse(kode)
ns = {}
for node in tree.body:
    if isinstance(node, pohon.Assign) and getattr(node.targets[0], "id", "") == "TEMA":
        ns["TEMA"] = pohon.literal_eval(node.value)
TEMA = ns["TEMA"]

D = json.load(open(src))
frasa = {k.lower(): v for k, v in D["frasa"].items()}

per_tema = defaultdict(set)
lain = set()
for teks in frasa:
    for tema, (_, rx, _) in TEMA.items():
        if re.search(rx, teks):
            per_tema[tema].add(teks)
            break
    else:
        lain.add(teks)

SUDAH = {"kucing": "Ep23", "gempa bumi": "Ep22", "mimpi & tidur": "Ep21+Ep25",
         "bulan": "Ep24", "dinosaurus": "Ep26", "ngorok": "Ep27",
         "perut & pencernaan": "Ep28", "kram & kesemutan": "Ep29"}
ANTREAN_LAMA = {"uban & rambut", "petir", "aurora", "situs misteri indonesia",
                "demam & imun", "megalodon", "kapal & mengapung"}
NIAT = ("hari ini", "malam ini", "sekarang", "berbahaya", "bahaya", "aman", "kapan",
        "berapa", "cara", "apakah", "padahal", "tiba-tiba", "terus")

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
for tema, (_, _, _) in TEMA.items():
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


print(f"== SKOR ULANG (atribusi diperbaiki) | sumber: {os.path.basename(src)} ==")
print(f"frasa: {len(frasa)} | di luar tema: {len(lain)}")
print("\nTOP 20:")
for i, b in enumerate(baris[:20], 1):
    print(f" {i:2d}. {b['tema']:26s} tumbuh {b['skor_tumbuh']:6.1f} (skor {b['skor']:6.1f}, jml {b['jml']:3d}, "
          f"kuat {b['kuat']:3d}, niat {b['niat']:2d}, yt {b['yt']:2d}, rel {b['rel']:2d}, kom {b['kom']:2d}, vis {b['vis']:2d}) [{b['status']}]")
    print("      " + " | ".join(b["contoh"][:4]))

kand = [b for b in baris if b["status"] == "SEGAR" and b["sains"] >= 2.0][:10]
print("\nKANDIDAT SEGAR (sains >= 2):")
for i, b in enumerate(kand, 1):
    print(f" {i}. {b['tema']:26s} tumbuh {b['skor_tumbuh']:6.1f} (skor {b['skor']:6.1f}, yt {b['yt']}, kom {b['kom']})")

json.dump({"dari": os.path.basename(src), "peringkat": baris},
          open(os.path.join(BASE, "skor_ulang_terbaru.json"), "w"), ensure_ascii=False, indent=1)
print("\n-> analisis/skor_ulang_terbaru.json")
