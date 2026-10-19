#!/usr/bin/env python3
"""PEMETA PELUANG v4 — sistem analisis bercabang milik KlikTahu.

Mengubah sapuan kata kunci dari "daftar frasa" menjadi POHON KEPUTUSAN:
tema -> cabang konteks -> daun (pendalaman), lalu menilai KELUARGA topik
(= semesta seri), bukan cuma frasa tunggal. Tujuan: video berkembang cepat
karena satu keluarga kuat langsung dipecah menjadi RENCANA SERI episode.

Lapisan (bercabang):
  L0  warisan  : frasa dari hasil_mendalam_*.json terbaru (sapuan v3) + skor per tema.
  L1  cabang   : untuk keluarga teratas, buka cabang konteks:
                 "kenapa <inti> <aspek>" (anak/malam/setelah makan/bahaya/...),
                 "apakah <inti> <aspek>", "kapan <inti> bahaya" (autocomplete live).
  L2  pendalam : frasa cabang terkuat (pos kecil, muncul di YouTube) ditelusuri
                 sekali lagi (kedalaman 2).

Skor v4 (transparan, semua kolom dilaporkan):
  poin_daun    = (11 - pos, min 1) + 1,5 (muncul di YouTube) + 1 (<= 4 kata)
  jaring       = jumlah cabang yang daunnya juga kuat (semesta = bisa diseri)
  kedalaman    = jumlah lapis yang menghasilkan frasa baru
  peluang      = andalan panjang (>= 5 kata) -> kompetisi rendah, mudah naik
  skor_keluarga= skor_tumbuh_v3(tema, gabungan frasa) + jaring*2,5
                 + kedalaman*1,5 + peluang*2,0
  momen        = naik/turun dibanding snapshot sebelumnya (keluarga_terakhir.json)

Keluaran (folder analisis/):
  pohon_topik.json      pohon tema -> cabang -> daun (mentah + poin)
  keluarga_terakhir.json snapshot skor keluarga (untuk diff berikutnya)
  PEMETA_PELUANG.md     laporan: peta keluarga + rencana seri + momen naik

Mode:
  python3 pemeta_peluang.py          -> mode penuh (butuh internet; dipakai CI)
  python3 pemeta_peluang.py --uji    -> mode UJI OFFLINE (fixture internal,
                                        tanpa jaringan; validasi logika cepat)
"""
import json
import math
import os
import re
import sys
import time
import urllib.parse
from collections import defaultdict
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import sapuan_mendalam as s3  # noqa: E402  (g, yt, TEMA, NIAT/REL/KOMEN/VIS/EVENT)

ASPEK = ["anak", "bayi", "malam", "pagi", "setelah makan", "terus", "tiap hari",
         "bahaya", "tanda", "sembuh", "saat hujan", "lama"]
# Topik blokir "kentut dll" (perintah user 21 Sep) - SATU SUMBER di sapuan_mendalam.py
# (frasanya sudah dihapus total di sana); di sini lapisan kedua: tak diranking, tak dicabangkan.
BLOKIR = s3.BLOKIR

BUDGET = int(os.environ.get("KT_PETA_BUDGET", "300"))
JEDA = float(os.environ.get("KT_PETA_JEDA", "0.15"))

UJI_FIXTURE = {
    "frasa": {
        "kenapa kentut bau": {"sumber": ["g", "yt"], "pos": 1, "bucket": "B"},
        "kenapa kentut banyak": {"sumber": ["g", "yt"], "pos": 2, "bucket": "B"},
        "kenapa kentut bau banget": {"sumber": ["yt"], "pos": 3, "bucket": "C"},
        "kenapa mata kedutan": {"sumber": ["g", "yt"], "pos": 1, "bucket": "B"},
        "kenapa mata kedutan terus": {"sumber": ["g"], "pos": 4, "bucket": "C"},
        "kenapa pusing pagi": {"sumber": ["g", "yt"], "pos": 2, "bucket": "B"},
        "kenapa pusing dan mual": {"sumber": ["yt"], "pos": 5, "bucket": "C"},
        "misteri gunung padang": {"sumber": ["g", "yt"], "pos": 1, "bucket": "B"},
        "kenapa kentut anak anak": {"sumber": ["g"], "pos": 6, "bucket": "C"},
        "kenapa mata kedutan sebelah kiri": {"sumber": ["g"], "pos": 8, "bucket": "C"},
    },
    "peringkat": [
        {"tema": "kentut", "skor": 72.2, "skor_tumbuh": 97.3, "jml": 33, "kuat": 26},
        {"tema": "mata", "skor": 61.0, "skor_tumbuh": 88.0, "jml": 25, "kuat": 20},
        {"tema": "pusing & migrain", "skor": 55.0, "skor_tumbuh": 82.5, "jml": 20, "kuat": 15},
        {"tema": "situs misteri indonesia", "skor": 50.0, "skor_tumbuh": 79.2, "jml": 18, "kuat": 14},
    ],
}


def _inti_tema(tema, seeds):
    """Kata inti untuk membangun cabang: dari seed pertama tanpa 'kenapa'."""
    for s in seeds:
        if s.startswith("kenapa "):
            s = s[len("kenapa "):]
        kata = s.split()
        if kata:
            return " ".join(kata[:2]) if len(kata) >= 2 else kata[0]
    return tema.split()[0]


def _panggil(fn, q, state):
    """Panggil autocomplete dengan anggaran + jeda (mode uji = data tiruan)."""
    if state.get("uji"):
        return state["uji_hasil"].get(q.lower(), [])
    if state["req"] >= BUDGET:
        return []
    state["req"] += 1
    time.sleep(JEDA)
    try:
        return fn(q)
    except Exception:
        return []


def _kumpul(state, daftar, sumber, simpan):
    for teks, pos in daftar:
        teks = teks.strip().lower()
        if not (3 <= len(teks) <= 70):
            continue
        f = simpan.setdefault(teks, {"pos": 99, "sumber": set(), "lapis": set()})
        f["pos"] = min(f["pos"], pos)
        f["sumber"].add(sumber)
        f["lapis"].add(state.get("lapis", "L0"))


# Sinyal teks (milik v4; sinkron dengan heuristik v3)
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


def poin_daun(teks, info):
    p = max(1, 11 - min(10, info["pos"]))
    if "yt" in info["sumber"]:
        p += 1.5
    if len(teks.split()) <= 4:
        p += 1.0
    if any(k in teks for k in EVENT):
        p -= 3.0
    return round(p, 1)


def atribusi(teks):
    for tema, (_, rx, _) in s3.TEMA.items():
        if re.search(rx, teks):
            return tema
    return None


def main():
    uji = "--uji" in sys.argv
    tgl = date.today().isoformat()
    state = {"req": 0, "uji": uji, "uji_hasil": {
        "kenapa kentut anak": [("kenapa kentut anak jadi banyak", 1), ("kenapa kentut anak bau", 2)],
        "kentut anak bahaya": [("apakah kentut anak bahaya", 1)],
        "kenapa mata kedutan malam": [("kenapa mata kedutan malam hari", 1)],
        "mata kedutan bahaya": [("apakah mata kedutan bahaya", 1)],
        "kenapa pusing pagi": [("kenapa pusing pagi setelah tidur", 1)],
        "pusing malam": [("kenapa pusing malam hari", 1)],
        "misteri gunung padang": [("misteri gunung padang terbaru", 1)],
    }, "lapis": "L0"}

    # ---------- L0: warisan ----------
    if uji:
        frasa_l0 = {k: dict(v, sumber=set(v["sumber"])) for k, v in UJI_FIXTURE["frasa"].items()}
        v3_tema = {r["tema"]: r for r in UJI_FIXTURE["peringkat"]}
    else:
        hasil = sorted(f for f in os.listdir(BASE) if re.match(r"hasil_mendalam_\d+\.json$", f))
        if not hasil:
            print("TIDAK ADA hasil_mendalam_*.json - jalankan sapuan_mendalam.py dulu")
            sys.exit(1)
        data = json.load(open(os.path.join(BASE, hasil[-1])))
        frasa_l0 = {k: {"pos": v["pos"], "sumber": set(v["sumber"])} for k, v in data.get("frasa", {}).items()}
        v3_tema = {r["tema"]: r for r in data.get("peringkat", [])}
    print(f"L0 warisan: {len(frasa_l0)} frasa, {len(v3_tema)} tema dari sapuan v3")

    keluarga_frasa = defaultdict(dict)   # tema -> {teks: info}
    for teks, info in frasa_l0.items():
        t = atribusi(teks)
        if t:
            keluarga_frasa[t][teks] = info

    # ---------- pilih keluarga teratas untuk dibuka cabangnya ----------
    urut = sorted(v3_tema.items(), key=lambda kv: -kv[1].get("skor_tumbuh", 0))
    top = [(t, r) for t, r in urut if r.get("skor_tumbuh", 0) >= 40 and t not in BLOKIR][:14]
    print(f"L1 cabang: membuka cabang untuk {len(top)} keluarga teratas "
          f"(anggaran {BUDGET} panggilan)")

    pohon = {}
    for tema, rank in top:
        seeds = s3.TEMA.get(tema, (0, "", ["kenapa " + tema.split()[0]]))[2]
        inti = _inti_tema(tema, seeds)
        cabang = {}
        queries = []
        for asp in ASPEK[:7]:
            queries += [f"kenapa {inti} {asp}", f"{inti} {asp}"]
        queries += [f"apakah {inti} bahaya", f"kapan {inti} bahaya"]
        for q in queries[:8]:
            state["lapis"] = "L1"
            daun = {}
            _kumpul(state, _panggil(s3.g, q, state), "g", daun)
            _kumpul(state, _panggil(s3.yt, q, state), "yt", daun)
            for teks, info in list(daun.items()):
                t2 = atribusi(teks)
                if t2 == tema:
                    keluarga_frasa[tema][teks] = info
            kuat = {t2: i for t2, i in daun.items() if atribusi(t2) == tema and i["pos"] <= 5}
            if kuat:
                cabang[q] = {t2: i for t2, i in kuat.items()}
        # ---------- L2 pendalaman: dari daun cabang terkuat ----------
        state["lapis"] = "L2"
        daun_semua = [(t2, i2) for c in cabang.values() for t2, i2 in c.items()]
        for teks, info in sorted(daun_semua, key=lambda x: x[1]["pos"])[:2]:
            if len(teks.split()) < 3 or state["req"] >= BUDGET:
                continue
            d2 = {}
            _kumpul(state, _panggil(s3.g, teks, state), "g", d2)
            _kumpul(state, _panggil(s3.yt, teks, state), "yt", d2)
            for t2, i2 in d2.items():
                if atribusi(t2) == tema:
                    keluarga_frasa[tema][t2] = i2
                    cabang.setdefault("pendalam:" + teks, {})[t2] = i2
        if cabang:
            pohon[tema] = {"inti": inti, "skor_tumbuh_v3": rank.get("skor_tumbuh"),
                           "cabang": {q: {t2: {"pos": i2["pos"], "sumber": sorted(i2["sumber"]),
                                               "lapis": sorted(i2["lapis"])}
                                          for t2, i2 in d.items()}
                                      for q, d in cabang.items()}}
    baru = sum(1 for t in keluarga_frasa for k in keluarga_frasa[t] if k not in frasa_l0)
    print(f"L2 pendalam selesai: +{baru} frasa baru, {state['req']} panggilan live"
          + (" (mode UJI: 0)" if uji else ""))

    # ---------- skor keluarga ----------
    snapshot_lama = {}
    sp = os.path.join(BASE, "keluarga_terakhir.json")
    if os.path.exists(sp) and not uji:
        try:
            snapshot_lama = json.load(open(sp)).get("keluarga", {})
        except Exception:
            pass

    baris = []
    for tema, fs in keluarga_frasa.items():
        if len(fs) < (3 if uji else 4) or tema in BLOKIR:
            continue
        jml = len(fs)
        kuat = sum(1 for f in fs if len(f.split()) <= 5 and fs[f]["pos"] <= 6)
        niat = sum(1 for f in fs if any(k in f for k in NIAT))
        yt_n = sum(1 for f in fs if "yt" in fs[f]["sumber"])
        sains = s3.TEMA.get(tema, (0,))[0] or 1.0
        rel = sum(1 for f in fs if any(k in f for k in REL))
        kom = sum(1 for f in fs if any(k in f for k in KOMEN))
        vis = sum(1 for f in fs if any(k in f for k in VIS))
        ever = 1.0 if not any(k in f for f in fs for k in EVENT) else 0.3
        skor = jml + kuat * 0.7 + niat * 0.9 + sains * 3 + yt_n * 0.3
        tumbuh = skor + rel * 1.2 + kom * 1.5 + vis * 0.8 + ever * 3
        if tema in v3_tema:                      # wariskan penguat v3
            tumbuh = max(tumbuh, v3_tema[tema].get("skor_tumbuh", 0))
        # elemen v4
        cab = pohon.get(tema, {}).get("cabang", {})
        cab_aktif = sum(1 for d in cab.values() if len(d) >= 2)
        jaring = cab_aktif
        kedalaman = len({l for f in fs.values() for l in f.get("lapis", {"L0"})})
        panjang = sum(1 for f in fs if len(f.split()) >= 5)
        peluang = round(panjang / max(1, jml), 2)
        skor_kel = round(tumbuh + jaring * 2.5 + (kedalaman - 1) * 1.5 + peluang * 2.0 * jml / 10.0, 1)
        # potensi VIEWS: permintaan luas + sinyal YouTube + kuat kepala + visual + sains + layak seri
        skor_vw = round(jml + kuat * 1.0 + yt_n * 2.0 + vis * 0.8 + niat * 0.6
                        + sains * 2.0 + jaring * 2.0, 1)
        lama = snapshot_lama.get(tema, {}).get("skor_keluarga")
        momen = ("BARU" if lama is None else
                 "NAIK" if skor_kel > lama * 1.05 else
                 "TURUN" if skor_kel < lama * 0.95 else "STABIL")
        SUDAH = {"kucing": "Ep23", "gempa bumi": "Ep22", "mimpi & tidur": "Ep21+25", "bulan": "Ep24",
                 "dinosaurus": "Ep26", "ngorok": "Ep27", "perut & pencernaan": "Ep28",
                 "kram & kesemutan": "Ep29", "gigi & mulut": "Ep30", "mata": "Ep31"}
        status = SUDAH.get(tema, "SEGAR")
        iden = sorted((f for f in fs if f.startswith(("kenapa", "apakah", "bagaimana", "kapan"))),
                      key=lambda f: -poin_daun(f, fs[f]))
        baris.append({"tema": tema, "jml": jml, "kuat": kuat, "jaring": jaring,
                      "kedalaman": kedalaman, "peluang": peluang, "yt": yt_n,
                      "niat": niat, "vis": vis,
                      "skor": round(skor, 1), "tumbuh": round(tumbuh, 1),
                      "skor_keluarga": skor_kel, "skor_views": skor_vw,
                      "momen": momen, "status": status,
                      "rencana_seri": iden[:6]})

    baris.sort(key=lambda b: -b["skor_views"])
    if not uji:
        json.dump({"tanggal": tgl, "keluarga": {b["tema"]: {"skor_keluarga": b["skor_keluarga"]}
                                                for b in baris}},
                  open(sp, "w"), ensure_ascii=False, indent=1)
        json.dump({"tanggal": tgl, "panggilan": state["req"],
                   "pohon": pohon, "keluarga": baris},
                  open(os.path.join(BASE, "pohon_topik.json"), "w"), ensure_ascii=False, indent=1)

    # ---------- laporan ----------
    md = ["# PEMETA PELUANG v4 - Pohon Topik Bercabang (" + tgl + ")" + ("  [MODE UJI]" if uji else ""),
          "",
          f"Keluarga topik dinilai: {len(baris)} | cabang dibuka: {state['req']} panggilan"
          + (" (fixture uji)" if uji else "") + " | pohon: `pohon_topik.json`",
          "",
          "`skor_views` (UTAMA) = jml + kuat + yt*2 + vis*0,8 + niat*0,6 + sains*2 + jaring*2  <- potensi views",
          "`skor_keluarga` = skor_tumbuh(v3) + jaring*2,5 + kedalaman*1,5 + peluang*2,0*(jml/10)  <- semesta seri",
          "- yt = frasa yang muncul di autocomplete YouTube (permintaan tontonan langsung)",
          "- momen = NAIK/TURUN vs snapshot sebelumnya (sinyal tren)",
          f"- topik diblokir (perintah user): {', '.join(BLOKIR)}",
          "",
          "| # | keluarga | jml | kuat | yt | vis | jaring | ked | tumbuh | **skor_views** | skor_keluarga | momen | status |",
          "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for i, b in enumerate(baris, 1):
        md.append(f"| {i} | {b['tema']} | {b['jml']} | {b['kuat']} | {b['yt']} | {b['vis']} | "
                  f"{b['jaring']} | {b['kedalaman']} | {b['tumbuh']} | "
                  f"**{b['skor_views']}** | {b['skor_keluarga']} | {b['momen']} | {b['status']} |")

    md += ["", "## RENCANA SERI (keluarga teratas -> antrian episode cepat)"]
    for b in [x for x in baris if x["status"] == "SEGAR"][:6]:
        md.append(f"### {b['tema']} - skor_keluarga {b['skor_keluarga']} ({b['momen']})")
        for j, idn in enumerate(b["rencana_seri"][:5], 1):
            md.append(f"  {j}. `{idn}`  (poin {poin_daun(idn, keluarga_frasa[b['tema']][idn])})")
        md.append("")
    naik = [b for b in baris if b["momen"] == "NAIK"][:6]
    if naik:
        md += ["## MOMEN NAIK (naik vs sapuan sebelumnya - prioritaskan)"]
        md += [f"- **{b['tema']}** {b['skor_keluarga']} (jaring {b['jaring']}, peluang {b['peluang']})" for b in naik]
    open(os.path.join(BASE, "PEMETA_PELUANG.md"), "w").write("\n".join(md) + "\n")

    print("\nTOP KELUARGA (skor_views = potensi views):")
    for i, b in enumerate(baris[:12], 1):
        print(f" {i:2d}. {b['tema']:26s} {b['skor_views']:6.1f} (yt {b['yt']}, jml {b['jml']}, "
              f"kuat {b['kuat']}, jaring {b['jaring']}) {b['momen']:6s} [{b['status']}]")
    segar = [b for b in baris if b["status"] == "SEGAR"][:6]
    print("\nRENCANA SERI TERATAS:")
    for b in segar:
        print(f" - {b['tema']}: " + " | ".join(b["rencana_seri"][:3]))


if __name__ == "__main__":
    main()
