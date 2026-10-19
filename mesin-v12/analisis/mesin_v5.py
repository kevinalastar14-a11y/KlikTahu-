#!/usr/bin/env python3
"""ANALISIS v5 REAL-TIME — mesin pertumbuhan KlikTahu (lapisan di atas v4.2).

Kenapa v5: views turun karena (a) pilihan topik statis - tidak ada sinyal NAIK/TURUN,
(b) daftar "sudah dibahas" macet di Ep29 sehingga topik yang sudah dibahas ikut
memborong peringkat, (c) judul/deskripsi/hashtag/tag tidak dibuat dari data.
v5 menutup ketiganya:

  1. SAPUAN LEBIH DALAM: lapis 1-2 v3 + BFS kedalaman-2 (frasa terkuat tiap tema
     diekspansi sekali lagi) -> menangkap long-tail yang tidak muncul di lapis 1.
  2. VELOCITY (baru): bandingkan dengan snapshot sapuan terakhir ->
     `naik` = tema yang permintaannya BERTAMBAH sejak run sebelumnya.
     skor_views v5 = (jml + kuat + yt*2 + vis*0,8 + niat*0,6 + sains*2 + jaring*2)
                     + velocity*4 + momen*6
     Momentum menentukan apakah video "terbang" saat diterbitkan atau mengendap.
  3. SUDAH-DIBAHAS OTOMATIS dari pustaka/ (Ep24-37 semua tercatat) - bug v4.2 tuntas.
  4. KALENDER MOMEN: event datar berjadwal (Geminids, Supermoon, musim hujan, ...)
     dapat boost saat jendela momen dibuka (<45 hari) - terbit TEPAT saat pencarian
     melonjak, bukan setelah gelombang lewat.
  5. PABRIK METADATA (baru): untuk top-3 SEGAR dibuat DRAFT judul/deskripsi/
     hashtag/tag dari frasa autocomplete ASLI (kata pencari, bukan karangan) ->
     analisis/DRAFT_METADATA_<tema>.md

Mode: butuh internet (dijalankan di CI). Tanpa internet -> fallback OFFLINE:
pakai snapshot terakhir untuk velocity & pabrik, laporan diberi label OFFLINE.

Keluaran: HASIL_V5.md, hasil_v5_<tanggal>.json, DRAFT_METADATA_<tema>.md
"""
import glob
import json
import os
import re
import sys
import time
import urllib.parse
from collections import defaultdict
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sapuan_mendalam as sm  # sumber: g(), yt(), TEMA, BLOKIR (satu sumber kebenaran)

BASE = os.path.dirname(os.path.abspath(__file__))

# --- 3. sudah dibahas: peta episode -> tema (UPDATE saat episode baru terbit) ---
SUDAH_EP = {
    "Ep21": "mimpi & tidur", "Ep22": "gempa bumi", "Ep23": "kucing", "Ep24": "bulan",
    "Ep25": "mimpi & tidur", "Ep26": "dinosaurus", "Ep27": "ngorok",
    "Ep28": "perut & pencernaan", "Ep29": "kram & kesemutan", "Ep30": "gigi & mulut",
    "Ep31": "mata", "Ep32": "demam & imun", "Ep33": "hujan & awan",
    "Ep34": "mimisan & hidung", "Ep35": "bulan", "Ep36": "pusing & migrain",
    "Ep37": "kulit", "Ep38": "baterai & hp", "Ep39": "meteor & komet", "Ep40": "gerhana",
    "Ep41": "hantu & supranatural",
    "Ep42": "internet & sinyal",
    "Ep42L": "listrik & magnet",   # dirilis sesi paralel di branch 01a0bf42 (run 66)
    "Ep43": "kuping",
    "Ep44": "situs misteri indonesia",
    "Ep45": "matahari",
    "Ep46": "megalodon",
    "Ep47": "petir",
    "Ep48": "jantung & dada",
    "Ep49": "bintang & galaksi",
}
ANTREAN_LAMA = {"uban & rambut", "petir", "aurora", "situs misteri indonesia",
                "demam & imun", "megalodon", "kapal & mengapung"}

# --- 4. kalender momen (bulan, hari, tema, label) - zona waktu Indonesia ---
KALENDER = [
    (3, 3, "gerhana", "Gerhana bulan total"),
    (10, 21, "meteor & komet", "Orionids"),
    (11, 17, "meteor & komet", "Leonids"),
    (11, 24, "bulan", "Supermoon Beaver"),
    (12, 14, "meteor & komet", "Geminids"),
    (12, 24, "bulan", "Supermoon terdekat sejak 2019"),
    (11, 1, "hujan & awan", "puncak musim hujan"),
    (12, 15, "batuk flu pilek", "musim flu akhir tahun"),
    (12, 20, "menangis & emosi", "perayaan akhir tahun"),
    (10, 31, "hantu & supranatural", "Halloween"),
]
JENDELA = 45  # hari

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

# tema tambahan berbasis event (tidak ada di v4.2)
TEMA_TAMBAHAN = {
    "meteor & komet": (2.5, r"meteor|komet|geminid|leonid|orionid|perseid",
                       ["kenapa meteor jatuh", "hujan meteor", "geminids"]),
}


def snapshot_terakhir(tanggal_ini):
    """JSON sapuan v3 terakhir SEBELUM hari ini (untuk velocity & fallback)."""
    kandidat = []
    for p in glob.glob(os.path.join(BASE, "hasil_mendalam_*.json")):
        tgl = os.path.basename(p)[len("hasil_mendalam_"):-len(".json")]
        try:
            d = datetime.strptime(tgl, "%Y%m%d").date()
        except ValueError:
            continue
        if d < tanggal_ini:
            kandidat.append((d, p))
    return max(kandidat)[1] if kandidat else None


def baca_baseline(path):
    """{tema: {"jml": n, "frasa": set()}} dari snapshot v3."""
    if not path:
        return {}
    data = json.load(open(path))
    frasa = data.get("frasa", {})
    rx = {t: re.compile(v[1]) for t, v in sm.TEMA.items()}
    per = defaultdict(set)
    for teks in frasa:
        for tema, r in rx.items():
            if r.search(teks):
                per[tema].add(teks)
                break
    return {t: {"jml": len(s), "frasa": s} for t, s in per.items()}


def sapu_langsung():
    """Sapuan v5: lapis 1-2 (gaya v3) + BFS kedalaman-2. Return (frasa, req, hidup)."""
    frasa = {}
    req = [0]

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

    def ambil(fn, q, sumber, bk):
        req[0] += 1
        catat(fn(q), sumber, bk)

    print("== Lapis 1: awalan pendek ==")
    for aw in sm.AWALAN:
        q = "kenapa " + aw
        ambil(lambda x: sm.g(x), q, "g", "A")
        ambil(lambda x: sm.yt(x), q, "yt", "A")
    print("== Lapis 2: seed per tema ==")
    tema_semua = dict(sm.TEMA)
    tema_semua.update(TEMA_TAMBAHAN)
    for tema, (_, _, seeds) in tema_semua.items():
        for s in seeds:
            bk = sm.bucket_seed(s)
            ambil(lambda x: sm.g(x), s, "g", bk)
            ambil(lambda x: sm.yt(x), s, "yt", bk)
    if not frasa:
        return frasa, req[0], False
    print("== Lapis 3: BFS kedalaman-2 (frasa terkuat diekspansi) ==")
    rx = {t: re.compile(v[1]) for t, v in tema_semua.items()}
    per_tema = defaultdict(set)
    for teks in list(frasa):
        for tema, r in rx.items():
            if r.search(teks):
                per_tema[tema].add(teks)
                break
    for tema, fs in per_tema.items():
        terkuat = sorted(fs, key=lambda f: (frasa[f]["bucket"], frasa[f]["pos"], len(f)))[:3]
        for f in terkuat:
            inti = f.replace("kenapa ", "").replace("apa itu ", "").strip()
            for q in (f, "kenapa " + inti):
                if len(q) <= 40:
                    ambil(lambda x: sm.yt(x), q, "yt", "B")
    # buang blokir SEBELUM atribusi akhir (aturan tetap)
    rx_b = [re.compile(tema_semua[t][1]) for t in sm.BLOKIR if t in tema_semua]
    for t in [t for t in list(frasa) if any(r.search(t) for r in rx_b)]:
        del frasa[t]
    return frasa, req[0], True


def momen_kalender(tema, hari_ini):
    for (b, h, t, label) in KALENDER:
        if t != tema:
            continue
        target = date(hari_ini.year, b, h)
        if target < hari_ini:
            target = date(hari_ini.year + 1, b, h)
        delta = (target - hari_ini).days
        if delta <= JENDELA:
            return label, delta
    return None, None


def nilai_tema(frasa, baseline, hari_ini):
    rx = {t: re.compile(v[1]) for t, v in {**sm.TEMA, **TEMA_TAMBAHAN}.items()}
    per_tema = defaultdict(set)
    for teks in frasa:
        for tema, r in rx.items():
            if r.search(teks):
                per_tema[tema].add(teks)
                break
    sudah = set(SUDAH_EP.values())
    baris = []
    for tema in {**sm.TEMA, **TEMA_TAMBAHAN}:
        fs = sorted(per_tema.get(tema, ()))
        if len(fs) < 4:
            continue
        lama = baseline.get(tema, {}).get("frasa", set())
        baru_muncul = sorted(set(fs) - set(lama))
        jml_lama = baseline.get(tema, {}).get("jml", len(fs))
        velocity = round((len(fs) - jml_lama) / max(jml_lama, 1) + 0.5 * len(baru_muncul), 2)
        jml = len(fs)
        kuat = sum(1 for f in fs if len(f.split()) <= 5 and frasa[f]["bucket"] in "AB")
        niat = sum(1 for f in fs if any(k in f for k in NIAT))
        yt_n = sum(1 for f in fs if "yt" in frasa[f]["sumber"])
        sains = {**sm.TEMA, **TEMA_TAMBAHAN}[tema][0]
        rel = sum(1 for f in fs if any(k in f for k in REL))
        kom = sum(1 for f in fs if any(k in f for k in KOMEN))
        vis = sum(1 for f in fs if any(k in f for k in VIS))
        ever = 1.0 if not any(k in f for f in fs for k in EVENT) else 0.3
        dasar = jml + kuat + yt_n * 2 + vis * 0.8 + niat * 0.6 + sains * 2 + kom * 0.5
        label, delta = momen_kalender(tema, hari_ini)
        momen = 6.0 if label and delta is not None and delta <= 14 else (3.0 if label else 0.0)
        skor_v5 = round(dasar + max(velocity, 0) * 4 + momen, 1)
        if tema in sudah:
            status = "SUDAH " + "/".join(sorted(e for e in SUDAH_EP if SUDAH_EP[e] == tema))
        elif tema in ANTREAN_LAMA:
            status = "antrean lama"
        else:
            status = "SEGAR"
        fs_q = sorted(fs, key=lambda f: (not f.startswith(("kenapa", "apa", "bagaimana",
                                                           "misteri")),
                                         frasa[f]["bucket"], frasa[f]["pos"]))
        baris.append({"tema": tema, "jml": jml, "kuat": kuat, "niat": niat, "yt": yt_n,
                      "sains": sains, "rel": rel, "kom": kom, "vis": vis, "ever": ever,
                      "velocity": velocity, "baru": baru_muncul[:8], "momen": label or "",
                      "momen_hari": delta, "skor_dasar": round(dasar, 1),
                      "skor_views": skor_v5, "status": status, "contoh": fs_q[:6]})
    baris.sort(key=lambda b: -b["skor_views"])
    return baris


# ----------------------------- PABRIK METADATA -----------------------------

STOP_HS = {"kenapa", "apa", "itu", "yang", "dan", "di", "ke", "kok", "sih", "gak",
           "tidak", "bisa", "ada", "saya", "aku", "kamu", "boleh", "kena", "sering",
           "selalu", "tiba", "kadang", "bikin", "buat", "pakai", "pake", "sampai",
           "hingga", "kali", "banget", "bener", "benar", "salah", "lagi", "harus"}


def _judul_kandidat(tema, fs):
    """3 kandidat judul dari frasa ASLI autocomplete, diberi skor heuristik.
    Kunci diambil dari frasa terpendek yang paling 'seed' (bukan long-tail)."""
    seeds = [f for f in fs if len(f) <= 30] or list(fs)
    inti = min(seeds, key=len)
    kunci = re.sub(r"^(kenapa|apa itu|misteri)\s+", "", inti).strip()
    kunci = " ".join(w.capitalize() if w.isalpha() else w for w in kunci.split()[:4])
    myth = next((f for f in fs if any(m in f for m in ("bukan", "salah", "mitos", "jangan"))), None)
    kandidat = [
        f"Kenapa {kunci}?"[:60],
        (f"{kunci}? Itu Mitos!" if myth else f"{kunci}? Ini Yang Terjadi")[:60],
        (f"{kunci} - Sainsnya Bikin Kaget" if len(kunci) <= 22 else
         f"{kunci} Ternyata...")[:60],
    ]

    def skor(j):
        s = 0.0
        s += 2.0 if len(j) <= 45 else 1.0 if len(j) <= 55 else 0.2
        s += 1.5 if "?" in j else 0.0
        s += 1.5 if any(w in j.lower() for w in ("jangan", "bukan", "mitos", "ternyata",
                                                 "kaget")) else 0.0
        s += 0.5 if j.lower().startswith("kenapa") else 0.0
        return round(s, 1)

    out = [(j, skor(j)) for j in kandidat]
    out.sort(key=lambda x: -x[1])
    return out


def _hash_tag(tema, fs):
    """Hashtag dari kata yang MUNCUL BERULANG di frasa asli (sinyal permintaan),
    bukan kata sambung/verba generik."""
    freq = {}
    for f in fs:
        for w in re.findall(r"[a-z]+", f):
            if w not in STOP_HS and len(w) > 3:
                freq[w] = freq.get(w, 0) + 1
    urut = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    ht = ["#" + w for w, n in urut if n >= 2][:3]
    for w, _ in urut:
        t = "#" + w
        if t not in ht:
            ht.append(t)
        if len(ht) == 3:
            break
    for umum in ("#sains", "#belajar", "#fakta"):
        if umum not in ht:
            ht.append(umum)
        if len(ht) == 5:
            break
    tag = [re.sub(r"^(kenapa|apa itu)\s+", "", f) for f in fs[:8]]
    tag = [t[:40] for t in tag if 3 < len(t)]
    for umum in ("edukasi sains", "klik tahu", "fakta sains", "short edukasi"):
        tag.append(umum)
    while sum(len(t) + 1 for t in tag) > 480:
        tag.pop()
    return " ".join(ht), ", ".join(tag)


def pabrik_metadata(b, hidup):
    tema = b["tema"]
    slug = re.sub(r"[^a-z0-9]+", "-", tema).strip("-")
    fs = b["contoh"]
    judul = _judul_kandidat(tema, fs)
    ht, tag = _hash_tag(tema, fs)
    baris_isi = "\n".join(f"- {f.capitalize()}?" for f in fs[:4])
    md = [f"# DRAFT METADATA v5 - {tema.upper()}",
          f"_Dibuat {date.today().isoformat()} | skor_views v5 {b['skor_views']} | "
          f"velocity {b['velocity']} | momen {b['momen'] or '-'} | status {b['status']}_",
          "",
          "## Judul (pilih satu - urut skor heuristik)"]
    md += [f"{i}. {j}  _(skor {s})_" for i, (j, s) in enumerate(judul, 1)]
    md += ["", "## Deskripsi (draf - lengkapi jawaban & bab saat produksi)",
           "```", f"{judul[0][0]}",
           "", "Jawaban singkatnya ada di video ini - dibuat dari pertanyaan yang",
           "paling sering diketik orang:", baris_isi, "",
           "Isi video ini:", "00:00 Pembuka", "(isi bab saat produksi)", "",
           "Ikuti KlikTahu untuk fakta sains & misteri tiap hari!", ht, "```",
           "", f"## Hashtag\n{ht}", "", f"## Tag\n{tag}", "",
           "## Frasa sumber (real-time autocomplete)",
           " · ".join("`" + f + "`" for f in fs[:6]),
           "",
           f"_Sumber data: {'sapuan live CI' if hidup else 'snapshot terakhir (OFFLINE)'}_"]
    p = os.path.join(BASE, f"DRAFT_METADATA_{slug}.md")
    open(p, "w").write("\n".join(md) + "\n")
    return p


def main():
    hari_ini = date.today()
    base_path = snapshot_terakhir(hari_ini)
    baseline = baca_baseline(base_path)
    frasa, req, hidup = sapu_langsung()
    if not hidup:
        print("[v5] OFFLINE: network gagal -> pakai snapshot", base_path)
        if not baseline:
            print("[v5] tidak ada snapshot -> keluar")
            return
        frasa = {}
        for t, d in baseline.items():
            for f in d["frasa"]:
                frasa.setdefault(f, {"sumber": {"g"}, "pos": 5, "bucket": "B"})
        req = 0
    baris = nilai_tema(frasa, baseline, hari_ini)
    segar = [b for b in baris if b["status"] == "SEGAR" and b["sains"] >= 2.0]

    tgl = hari_ini.isoformat()
    json.dump({"tanggal": tgl, "mode": "live" if hidup else "offline",
               "permintaan": req, "frasa_unik": len(frasa),
               "baseline": os.path.basename(base_path) if base_path else "",
               "peringkat": baris},
              open(os.path.join(BASE, f"hasil_v5_{tgl.replace('-', '')}.json"), "w"),
              ensure_ascii=False, indent=1)

    md = ["# ANALISIS v5 REAL-TIME (" + tgl + ")",
          "",
          f"Mode: **{'LIVE (sapuan autocomplete Google+YouTube, BFS kedalaman-2)'}**"
          if hidup else "Mode: **OFFLINE (fallback snapshot)**",
          f"Permintaan: {req} | Frasa unik: {len(frasa)} | Baseline velocity: "
          f"{os.path.basename(base_path) if base_path else '-'}",
          "",
          "`skor_views v5` = dasar v4.2 (jml+kuat+yt*2+vis*0,8+niat*0,6+sains*2+kom*0,5)",
          "**+ velocity*4** (permintaan bertambah sejak snapshot terakhir; frasa baru dihitung)",
          "**+ momen** (6 kalau event kalender <=14 hari; 3 kalau <=45 hari)",
          "Status SEGAR otomatis dari pustaka/ (Ep21-37) - bug 'sudah dibahas' v4.2 tuntas.",
          "",
          "| # | tema | jml | kuat | yt | velocity | frasa BARU | momen | skor_views v5 | status |",
          "|---:|---|---:|---:|---:|---:|---:|---|---:|---|"]
    for i, b in enumerate(baris[:20], 1):
        md.append(f"| {i} | {b['tema']} | {b['jml']} | {b['kuat']} | {b['yt']} | "
                  f"{'▲' if b['velocity'] > 0 else '▼' if b['velocity'] < 0 else '='}"
                  f"{abs(b['velocity'])} | {len(b['baru'])} | {b['momen'] or '-'} | "
                  f"**{b['skor_views']}** | {b['status']} |")
    md += ["", "## TOP 3 SEGAR (kandidat episode berikutnya)"]
    for i, b in enumerate(segar[:3], 1):
        p = pabrik_metadata(b, hidup)
        md.append(f"{i}. **{b['tema']}** - skor_views v5 {b['skor_views']} "
                  f"(velocity {b['velocity']}, momen {b['momen'] or '-'}) -> draf: "
                  f"`{os.path.basename(p)}`")
        md.append(f"   contoh frasa: " + " · ".join("`" + c + "`" for c in b["contoh"][:4]))
    penguat = [b for b in baris if b["velocity"] > 0][:5]
    if penguat:
        md += ["", "## VELOCITY - permintaan NAIK sejak snapshot terakhir (terbitkan cepat)"]
        md += [f"- {b['tema']}: {b['velocity']:+} (frasa baru: " +
               ", ".join("`" + x + "`" for x in b["baru"][:4]) + ")" for b in penguat]
    jendela = [(b["tema"], b["momen"], b["momen_hari"]) for b in baris
               if b["momen"] and b["momen_hari"] is not None]
    if jendela:
        md += ["", "## JENDELA MOMEN TERBUKA (<=45 hari)"]
        md += [f"- {t}: {m} ({d} hari lagi)" for t, m, d in jendela]
    open(os.path.join(BASE, "HASIL_V5.md"), "w").write("\n".join(md) + "\n")

    print(f"\n[v5] frasa {len(frasa)} | permintaan {req} | mode "
          f"{'LIVE' if hidup else 'OFFLINE'}")
    print("\nTOP 12 (skor_views v5):")
    for i, b in enumerate(baris[:12], 1):
        print(f" {i:2d}. {b['tema']:26s} {b['skor_views']:6.1f} "
              f"(vel {b['velocity']:+.1f}, momen {b['momen'] or '-'}) [{b['status']}]")
    print("\nTOP 3 SEGAR + draf metadata:")
    for i, b in enumerate(segar[:3], 1):
        p = pabrik_metadata(b, hidup)
        print(f" {i}. {b['tema']:26s} {b['skor_views']:6.1f} -> {os.path.basename(p)}")


if __name__ == "__main__":
    main()
