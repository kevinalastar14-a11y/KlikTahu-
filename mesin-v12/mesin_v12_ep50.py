#!/usr/bin/env python3
"""Ep50 - Hujan Meteor Orionid 21-22 Oktober (mesin v12 "KONTINUITAS").

Satu dunia visual: CAKRAM LANGIT (jendela malam) di atas, teks kinetik di bawahnya, baris alat
(jam -> kompas) di kaki. Metafora: komet -> butir debu -> garis cahaya -> jam & arah -> orbit yang
menyilang -> kembali ke komet (loop). Setiap BEAT dikunci ke KATA (mesin_v12.cues).

Babak: intro=Hook, f1=Agitation, f2-f4=Body (apa / jam / arah), f5=Micro-climax (orbit menyilang),
outro=Seamless loop (state frame akhir == frame 0).
"""
import math

import diagrams as D
import mesin_v11 as V
import mesin_v12 as M
from PIL import Image
from diagrams import (INK, CREAM, WHITE, MUTED, mix, seg, clamp, esmooth, eob, eo, font, paste_c,
                      rrect_on, line_on, dot_on, ring_on, poly_on)
from mesin_v12 import (ease12, esm, eio, t_kata, cues, cakram_langit, garis_meteor, komet, jam, kompas,
                       chip, label, silang, morph, bentuk_lingkaran, bentuk_bintang, bentuk_butir,
                       elips_pts, titik_elips, polyline_on, NAVY, NAVY2, STAR, KUNING, ORANYE)

# ---------------------------------------------------------------- tata letak dunia
CX, CY, R = 540, 770, 372          # cakram langit (y 398..1142)
Y_HOR = CY + 262                   # cakrawala (chord bawah cakram), y 1032
Y_TXT = 1312                       # teks kinetik (2 baris, aman: y < 1640, x < 950)
Y_ALAT = 1535                      # baris alat (jam/kompas/chip); dasar elemen <= 1625
KOMET_P = (448, 690)               # posisi inti komet (intro & outro: sama persis -> loop)
RUMAH = [(300, 22), (372, 30), (430, 18), (650, 26), (712, 34), (770, 20)]   # (x, tinggi) atap kecil
TEAL = (31, 122, 107)
UNGU = (106, 79, 179)
MERAH = (200, 70, 50)
EMAS = (176, 122, 18)
HIJAU = (46, 140, 90)


def _hor_x(y):
    """Lebar separuh chord cakram pada tinggi y."""
    dy = y - CY
    return math.sqrt(max(0.0, R * R - dy * dy))


_PIJAR = {}


def pijar_cakrawala(img, alpha, hw, tinggi=190):
    """Pijar atmosfer hangat yang memudar ke atas dari garis cakrawala (cahaya kota di kejauhan)."""
    if alpha <= 0.01:
        return
    key = (int(hw), int(tinggi), round(D.SS, 3))
    lay = _PIJAR.get(key)
    if lay is None:
        import numpy as np
        w, h = int(D.S(hw * 2)), int(D.S(tinggi))
        yy, xx = np.mgrid[0:h, 0:w].astype("float32")
        v = (yy / h) ** 2.4                                       # terang di bawah (cakrawala), hilang di atas
        u = np.exp(-((xx - w / 2) / (w * 0.32)) ** 2)             # lebih terang di tengah
        u *= np.clip(1 - (np.abs(xx - w / 2) / (w / 2)) ** 3, 0, 1)  # nol di tepi (tanpa garis vertikal)
        lay = Image.fromarray((np.clip(v * u, 0, 1) * 255).astype("uint8"), "L")
        _PIJAR[key] = lay
    m = lay.point(lambda v, a=alpha * 0.22: int(v * a))
    img.paste(Image.new("RGB", lay.size, mix(ORANYE, KUNING, 0.45)), (int(D.S(CX - hw)), int(D.S(Y_HOR)) - lay.size[1]), m)


def cakrawala(img, tg, alpha=1.0, sorot=0.0, orang=0.0, orang_tanya=0.0):
    """Tanah + atap rumah di dasar cakram (dunia penonton). sorot = kilau 'rumahmu'."""
    if alpha <= 0.01:
        return
    hw = _hor_x(Y_HOR)
    pijar_cakrawala(img, alpha, hw)
    # tanah: segmen cakram di bawah cakrawala
    pts = [(CX - hw, Y_HOR)]
    for i in range(1, 24):
        a = math.pi * i / 24
        x = CX - hw * math.cos(a)
        y = CY + math.sqrt(max(0.0, R * R - (x - CX) ** 2)) - 1
        pts.append((x, min(y, CY + R - 1)))
    pts.append((CX + hw, Y_HOR))
    poly_on(img, pts, mix(NAVY, INK, 0.55), alpha)
    line_on(img, (CX - hw, Y_HOR), (CX + hw, Y_HOR), mix(NAVY2, WHITE, 0.25), 3, alpha)
    for (x, h) in RUMAH:
        w = h * 1.5
        poly_on(img, [(x - w / 2, Y_HOR), (x - w / 2, Y_HOR - h * 0.6), (x, Y_HOR - h), (x + w / 2, Y_HOR - h * 0.6),
                      (x + w / 2, Y_HOR)], mix(NAVY, INK, 0.75), alpha)
        if sorot > 0.01:                                   # jendela menyala saat 'rumahmu'
            dot_on(img, x, Y_HOR - h * 0.35, 3.5, mix(KUNING, WHITE, 0.3), alpha * sorot)
    if sorot > 0.01:
        V._glow11(img, 540, Y_HOR - 10, 150, KUNING, alpha * sorot * 0.35)
    if orang > 0.01:                                       # siluet orang menengadah (kanan tanah)
        ox, oy = 556, Y_HOR + 6
        k = max(0.0, ease12(orang, 0.05, 0.05))
        dot_on(img, ox, oy - 40 * k, 9 * k, mix(NAVY2, WHITE, 0.55), alpha)
        line_on(img, (ox, oy - 30 * k), (ox, oy - 4), mix(NAVY2, WHITE, 0.55), 6, alpha * k)
        line_on(img, (ox, oy - 24 * k), (ox + 14 * k, oy - 42 * k), mix(NAVY2, WHITE, 0.55), 5, alpha * k)
        if orang_tanya > 0.01:
            chip(img, ox + 2, oy - 86, "?", MERAH, alpha * orang_tanya, orang_tanya, fsz=26)


def chip_tanggal(img, alpha=1.0, terang=0.0):
    """Chip tanggal persisten (frame 0 == frame akhir)."""
    col = mix(KUNING, INK, 0.25) if terang < 0.5 else mix(KUNING, WHITE, 0.1)
    chip(img, 540, CY + R + 40, "ORIONID  ·  PUNCAK 21-22 OKT", col, alpha, 10.0, fsz=25, persisten=True)
    if terang > 0.01:
        V._glow11(img, 540, CY + R + 40, 170, KUNING, 0.35 * terang)


def bulan(img, x, y, r, alpha, terang=1.0):
    if alpha <= 0.01:
        return
    V._glow11(img, x, y, r * 3.2, mix(WHITE, KUNING, 0.25), alpha * 0.55 * terang)
    dot_on(img, x, y, r, mix(WHITE, CREAM, 0.3), alpha)
    for (dx, dy, rr) in ((-r * 0.3, -r * 0.2, r * 0.16), (r * 0.25, r * 0.1, r * 0.12), (-r * 0.05, r * 0.4, r * 0.09)):
        dot_on(img, x + dx, y + dy, rr, mix(CREAM, MUTED, 0.35), alpha * 0.8)


def meteor_acak(img, tg, t0, t1, laju, alpha, radiant=None, seed=1, panjang=150, col=STAR):
    """Meteor acak deterministik dalam cakram antara t0..t1 (laju = meteor/detik)."""
    if alpha <= 0.01 or laju <= 0:
        return
    if tg < t0 or tg > t1 + 1.0:
        return
    periode = 1.0 / laju
    k0 = int((tg - t0) / periode) - 1
    for k in range(max(0, k0 - 1), k0 + 2):
        ts = t0 + k * periode + 0.37 * periode * math.sin(k * 7.3 + seed)
        u = (tg - ts) / 0.62
        if u <= 0 or u >= 1.6:
            continue
        rnd = (math.sin(k * 12.9 + seed * 3.1) * 43758.5) % 1.0
        rnd2 = (math.sin(k * 7.1 + seed * 1.7) * 12345.6) % 1.0
        if radiant:
            ang = rnd * 2 * math.pi
            r0 = 60 + 110 * rnd2
            p0 = (radiant[0] + r0 * math.cos(ang), radiant[1] + r0 * math.sin(ang))
            L = panjang * (0.5 + rnd2) * 0.8
            p1 = (p0[0] + L * math.cos(ang), p0[1] + L * math.sin(ang))
        else:
            p0 = (CX - 240 + 480 * rnd, CY - 300 + 200 * rnd2)
            p1 = (p0[0] + panjang * 0.9, p0[1] + panjang * 0.55)
        # hanya di dalam cakram & di atas cakrawala
        if math.hypot(p1[0] - CX, p1[1] - CY) > R - 10 or p1[1] > Y_HOR - 8:
            continue
        if u <= 1.0:
            garis_meteor(img, p0, p1, u, col, 3, alpha * (0.7 + 0.3 * u))
        else:                                                   # jejak persisten (train) memudar 0,37 s
            garis_meteor(img, p0, p1, u, col, 3, alpha * 0.8, train=True, train_dur=0.6)


def teks(img, sc, accent, tl, al, t0, text=None, hl=None, fsz=58, y=Y_TXT, maxw=820):
    V._judul11(img, text if text is not None else sc.get("badge", ""), accent, tl, al * M.KELUAR[0], y=y,
               hl=hl if hl is not None else sc.get("hl", ""), fsz=fsz, t0=t0, maxw=maxw)


# ================================================================ CUE (kata -> waktu) & SFX
CUES = {
    "komet50": {"halley": ("Halley", 0.06), "tahun": ("tahun", 0.18), "tapi": ("Tapi", 0.39),
                "kamis": ("Kamis", 0.44), "oktober": ("Oktober", 0.61), "terbakar": ("terbakar", 0.80),
                "rumahmu": ("rumahmu", 0.91)},
    "salahjam50": {"orionid": ("Orionid", 0.08), "malam": ("malam", 0.22), "gagal": ("gagal", 0.36),
                   "mendung": ("mendung", 0.50), "jam": ("jam", 0.66), "salah": ("salah", 0.72),
                   "bulan": ("Bulan", 0.84), "terang": ("terang", 0.92)},
    "debu50": {"bukan": ("bukan", 0.08), "butiran": ("butiran", 0.20), "pasir": ("pasir", 0.28),
               "halley": ("Halley", 0.38), "menabrak": ("menabrak", 0.56), "enam1": ("enam", 0.67, 1),
               "puluh": ("puluh", 0.69), "enam2": ("enam", 0.71, 2), "terbakar": ("terbakar", 0.85),
               "cahaya": ("cahaya", 0.94)},
    "jam50": {"jamnya": ("Jamnya:", 0.02), "rabu": ("Rabu", 0.08), "terbenam": ("terbenam", 0.30),
              "tengah": ("tengah", 0.36), "terbaik": ("terbaik", 0.46), "wib": ("WIB,", 0.58),
              "wita": ("WITA.", 0.66), "gelap": ("gelap,", 0.76), "meteor": ("meteor", 0.88),
              "perjam": ("jam.", 0.95)},
    "arah50": {"timur": ("timur,", 0.02), "tinggi": ("tinggi", 0.10), "orion": ("Orion,", 0.24),
               "tiga": ("tiga", 0.29), "bintang": ("bintang", 0.31), "sejajar": ("sejajar.", 0.34),
               "jangan": ("jangan", 0.42), "samping": ("samping,", 0.56), "panjang": ("panjang.", 0.70),
               "teleskop": ("teleskop.", 0.80), "hp": ("HP", 0.90), "menit": ("menit.", 0.97)},
    "orbit50": {"satukan": ("satukan", 0.04), "halley": ("Halley", 0.14), "matahari": ("Matahari", 0.19),
                "sekali": ("sekali,", 0.27), "sungai": ("sungai", 0.36), "setiap": ("Setiap", 0.46),
                "menyeberangi": ("menyeberangi", 0.59), "kebetulan": ("kebetulan.", 0.71),
                "oktober": ("Oktober.", 0.85), "kota": ("kota", 0.93)},
    "loop50": {"terbakar": ("terbakar", 0.18), "komet": ("komet", 0.42), "sama": ("sama.", 0.52),
               "kembali": ("kembali...", 0.66), "satu": ("satu.", 0.85)},
}
# SFX per cue: nama_cue -> (jenis, gain, offset detik)
SFX = {
    "komet50": {"halley": ("kilau", 0.7, 0), "tahun": ("tick", 0.8, 0), "tapi": ("pop", 0.7, 0),
                "kamis": ("swish_up", 0.6, 0), "oktober": ("pop", 0.6, 0), "terbakar": ("burn", 1.0, -0.05),
                "rumahmu": ("thud", 0.8, 0)},
    "salahjam50": {"orionid": ("pop", 0.7, 0), "malam": ("tick", 0.9, 0), "gagal": ("pop", 0.7, 0),
                   "mendung": ("tick", 0.8, 0), "jam": ("swish", 0.6, 0), "salah": ("thud", 0.9, 0),
                   "bulan": ("kilau", 0.8, 0)},
    "debu50": {"bukan": ("swish", 0.7, 0), "butiran": ("morph", 0.8, 0), "pasir": ("pop", 0.6, 0),
               "halley": ("pop", 0.6, 0), "menabrak": ("impact", 0.9, 0), "enam1": ("tick", 0.9, 0),
               "puluh": ("tick", 0.9, 0), "enam2": ("tick", 0.9, 0), "terbakar": ("burn", 1.0, -0.05),
               "cahaya": ("kilau", 0.7, 0)},
    "jam50": {"jamnya": ("morph", 0.8, 0), "rabu": ("pop", 0.6, 0), "terbenam": ("swish", 0.7, 0),
              "tengah": ("tick", 0.8, 0), "terbaik": ("pop", 0.8, 0), "wib": ("pop", 0.7, 0),
              "wita": ("pop", 0.7, 0), "gelap": ("kilau", 0.7, 0), "meteor": ("burn", 0.8, 0),
              "perjam": ("pop", 0.7, 0)},
    "arah50": {"timur": ("morph", 0.8, 0), "tinggi": ("whoosh", 0.6, 0), "orion": ("pop", 0.7, 0),
               "tiga": ("tick", 0.9, 0), "bintang": ("tick", 0.9, 0), "sejajar": ("tick", 0.9, 0),
               "jangan": ("swish", 0.7, 0), "samping": ("swish", 0.7, 0), "panjang": ("burn", 0.9, 0),
               "teleskop": ("tick", 0.8, 0), "hp": ("pop", 0.6, 0), "menit": ("pop", 0.7, 0)},
    "orbit50": {"satukan": ("swish", 0.8, 0), "matahari": ("pop", 0.7, 0), "halley": ("riser", 0.6, 0),
                "sekali": ("tick", 0.8, 0), "sungai": ("kilau", 0.8, 0), "setiap": ("tick", 0.8, 0),
                "menyeberangi": ("thump", 1.0, 0), "kebetulan": ("pop", 0.7, 0), "oktober": ("tick", 0.8, 0),
                "kota": ("pop", 0.8, 0)},
    "loop50": {"terbakar": ("burn", 0.8, 0), "komet": ("kilau", 0.7, 0), "sama": ("swish_up", 0.6, 0),
               "satu": ("tick", 0.7, 0)},
}
# BEATS fraksi (hanya penanda keanggotaan v11/v12 untuk render.events; waktu nyata dari CUES)
BEATS50 = {k: [] for k in CUES}


def events_v12(sc):
    """Event SFX absolut untuk satu adegan timeline (start, dur) -> [(t, jenis, gain)]."""
    vis = sc.get("visual", "")
    if vis not in CUES:
        return []
    c = cues(sc, sc["dur"], CUES[vis])
    out = []
    for nama, (jenis, g, off) in SFX.get(vis, {}).items():
        out.append((sc["start"] + c[nama] + off, jenis, g))
    tr = str(sc.get("trans") or "").lower()
    if tr == "morph":
        out.append((sc["start"] - 0.08, "morph", 0.55))
    return out


# ================================================================ adegan
def sc_komet50(img, d, sc, tl, dur, tg, accent, al, dy):
    """HOOK. Komet Halley (2061) -> butir debu lepas -> terbakar di atas rumahmu."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["komet50"])
    cakram_langit(img, CX, CY, R, tg, 1.0, 1.0, 1.0)
    # komet penuh (state frame 0)
    flare = 1.0 + 0.35 * math.sin(math.pi * clamp((tl - c["halley"]) / 0.6)) if 0 < tl - c["halley"] < 0.6 else 1.0
    komet(img, KOMET_P[0], KOMET_P[1], 1.0, tg, 1.0, (-0.8, -0.6), flare)
    # label 2061 saat 'tahun'
    q = esm((tl - c["tahun"]) / 0.35)
    if q > 0 and tl < c["tapi"] + 1.2:
        a = q * (1 - esm((tl - c["tapi"] - 0.6) / 0.6))
        chip(img, KOMET_P[0] + 200, KOMET_P[1] + 112, "KEMBALI 2061", KUNING, a, tl - c["tahun"], fsz=26)
        line_on(img, (KOMET_P[0] + 24, KOMET_P[1] + 18), (KOMET_P[0] + 120, KOMET_P[1] + 92), mix(KUNING, WHITE, 0.3), 3, a)
    # butir debu lepas dari ekor ('Tapi') -> melayang -> terbakar ('terbakar')
    t_lepas, t_bakar = c["tapi"], c["terbakar"]
    p_lepas = (KOMET_P[0] - 120, KOMET_P[1] - 90)
    p_jatuh = (CX + 40, CY - 40)
    p_akhir = (CX + 250, Y_HOR - 60)
    if t_lepas <= tl < t_bakar:
        u = esm((tl - t_lepas) / max(0.1, (t_bakar - t_lepas)))
        gx = p_lepas[0] + (p_jatuh[0] - p_lepas[0]) * u + 14 * math.sin(tl * 3.0)
        gy = p_lepas[1] + (p_jatuh[1] - p_lepas[1]) * u
        pts = bentuk_butir(gx, gy, 7 + 4 * u, 3)
        poly_on(img, pts, mix(KUNING, WHITE, 0.5), 0.95)
        if tl - t_lepas < 0.5:
            V._partikel11(img, p_lepas[0], p_lepas[1], tl - t_lepas, KUNING, 0.7, n=8, jarak=50)
    if tl >= t_bakar:
        u = clamp((tl - t_bakar) / 0.55)
        garis_meteor(img, p_jatuh, p_akhir, u, mix(WHITE, KUNING, 0.25), 6, 1.0 if u < 1 else max(0.0, 1 - (tl - t_bakar - 0.55) / 0.5))
        if u < 0.35:
            V._glow11(img, p_jatuh[0] + (p_akhir[0] - p_jatuh[0]) * u, p_jatuh[1] + (p_akhir[1] - p_jatuh[1]) * u,
                      90, KUNING, 0.5 * (1 - u / 0.35))
    sorot = esm((tl - c["rumahmu"]) / 0.4) * (1 - esm((tl - dur + 0.5) / 0.4))
    cakrawala(img, tg, 1.0, sorot=sorot)
    chip_tanggal(img, 1.0, esm((tl - c["oktober"]) / 0.3) * (1 - esm((tl - c["oktober"] - 1.4) / 0.5)))
    # teks hook: baris 1 saat 'Kamis', baris 2 saat 'terbakar'; keluar sebelum akhir (loop: frame akhir tanpa teks)
    at = 1 - esm((tl - dur + 0.45) / 0.35)
    lines = sc.get("lines") or ["SERPIHAN KOMET HALLEY", "TERBAKAR KAMIS DINI HARI"]
    # hook di layar <= 0,35 s (penonton tanpa suara tetap tahu janjinya); 2 baris, satu blok
    teks(img, sc, accent, tl, at, 0.35, " ".join(lines), "TERBAKAR", fsz=58, y=Y_TXT, maxw=860)


def sc_salahjam50(img, d, sc, tl, dur, tg, accent, al, dy):
    """AGITATION. Bulan terang + jam salah = tidak lihat apa-apa."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["salahjam50"])
    mb = esm((tl - c["bulan"]) / 0.9)                       # bulan naik
    gelap = 1.0 - 0.3 * mb
    cakram_langit(img, CX, CY, R, tg, gelap, 1.0, 1.0 - 0.55 * mb)
    komet(img, KOMET_P[0], KOMET_P[1], 1.0, tg, 1.0 - 0.7 * esm(tl / 1.2), (-0.8, -0.6), 1.0)
    # meteor samar yang 'hilang' saat bulan terang
    meteor_acak(img, tg, sc["start"] + 1.0, sc["start"] + dur - 0.5, 0.55, 0.75 * (1 - 0.8 * mb), seed=2)
    # bulan
    by = CY - 60 - 60 * mb
    bulan(img, CX + 190, by + 120 * (1 - mb), 46, mb, 1.0)
    M.bab(img, sc, accent, tl, 1.0)
    # kalender strip: 19..25 Okt, 21-22 disorot saat 'malam'
    q = esm((tl - c["malam"] + 0.25) / 0.4)
    if q > 0:
        x0, wbox, gap = 540 - (7 * 60 + 6 * 8) / 2, 60, 8
        for k in range(7):
            hari = 19 + k
            xx = x0 + k * (wbox + gap)
            on = hari in (21, 22)
            kk = esm((tl - c["malam"] + 0.25 - 0.03 * k) / 0.3)
            rrect_on(img, xx, Y_ALAT - 34 * kk, xx + wbox, Y_ALAT + 34 * kk, 10,
                     mix(accent, WHITE, 0.1) if on and tl >= c["malam"] else mix(CREAM, INK, 0.08), kk * M.KELUAR[0])
            paste_c(img, xx + wbox / 2, Y_ALAT, str(hari), font(D.FB, 26), WHITE if on and tl >= c["malam"] else INK, kk * M.KELUAR[0])
        label(img, 540, Y_ALAT - 62, "OKTOBER 2026 · PUNCAK SATU MALAM", mix(INK, CREAM, 0.2), q, fsz=22)
    # orang menengadah + '?' saat 'gagal'
    cakrawala(img, tg, 1.0, orang=esm((tl - c["gagal"] + 0.3) / 0.5), orang_tanya=esm((tl - c["gagal"]) / 0.3))
    # awan 'mendung' lalu dicoret ('bukan karena mendung')
    qa = esm((tl - c["mendung"] + 0.35) / 0.3) * (1 - esm((tl - c["jam"] + 0.1) / 0.3))
    if qa > 0:
        ax, ay = CX - 200, CY - 150
        for (ddx, ddy, rr) in ((-40, 10, 34), (0, -12, 44), (44, 8, 36), (0, 20, 30)):
            dot_on(img, ax + ddx, ay + ddy, rr, mix(WHITE, CREAM, 0.5), qa * 0.9)
        silang(img, ax, ay, 46, MERAH, qa, clamp((tl - c["mendung"]) / 0.35))
    # jam salah: 21.00 + stiker SALAH
    qj = esm((tl - c["jam"] + 0.2) / 0.4)
    if qj > 0:
        jam(img, 250, Y_ALAT, 78, 21.0, qj, accent, tg, label="MASIH 21.00")
        M.stiker(img, 250 + 92, Y_ALAT - 40, "SALAH", 1.0, tl - c["salah"], bg=MERAH, fsz=28, rot=-8)
    chip_tanggal(img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.10)


def sc_debu50(img, d, sc, tl, dur, tg, accent, al, dy):
    """BODY 1. Bukan bintang jatuh: butir debu Halley menabrak udara 66 km/detik -> garis cahaya."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["debu50"])
    k0 = esm(tl / 1.0)
    cakram_langit(img, CX, CY, R, tg, 0.7 + 0.2 * k0, 1.0, 0.45 + 0.15 * k0)
    bulan(img, CX + 190, CY - 120, 46, 1.0 - 0.5 * k0, 1.0 - 0.4 * k0)
    komet(img, KOMET_P[0], KOMET_P[1], 1.0, tg, 0.3, (-0.8, -0.6), 1.0)
    M.bab(img, sc, accent, tl, 1.0)
    # busur atmosfer ('udara') di dasar cakram, muncul sebelum 'menabrak'
    qa = esm((tl - c["menabrak"] + 0.9) / 0.5)
    if qa > 0:
        pts = elips_pts(CX, Y_HOR + 520, 560, 560, n=90)
        pts = [p for p in pts if p[1] < Y_HOR - 10 and math.hypot(p[0] - CX, p[1] - CY) < R - 6]
        pts.sort(key=lambda p: p[0])
        polyline_on(img, pts, mix(TEAL, WHITE, 0.4), 3, qa * 0.9, tutup=False)
        label(img, CX - 205, Y_HOR - 62, "UDARA (±100 KM)", mix(TEAL, WHITE, 0.5), qa, fsz=22)
    # bintang (bukan) -> morph butir debu ('butiran') di tengah cakram
    px, py = CX, CY - 60
    qs = esm((tl - c["bukan"] + 0.6) / 0.35)
    u_m = esm((tl - c["butiran"]) / 0.6)
    t_tabrak = c["menabrak"]
    if qs > 0 and tl < t_tabrak:
        if u_m <= 0:
            pts = bentuk_bintang(px, py, 54)
            poly_on(img, pts, KUNING, qs)
            silang(img, px, py, 70, MERAH, qs, clamp((tl - c["bukan"]) / 0.35))
        else:
            # turun menuju busur udara menjelang tabrakan (antisipasi lalu akselerasi)
            uj = ease12(clamp((tl - (t_tabrak - 0.7)) / 0.7), 0.10, 0.0) if tl > t_tabrak - 0.7 else 0.0
            gy = py + (Y_HOR - 118 - py) * uj
            r_b = 54 - 30 * u_m
            pts = morph(bentuk_bintang(px, py, 54), bentuk_butir(px, gy, r_b, 3), u_m)
            poly_on(img, pts, mix(KUNING, ORANYE, u_m * 0.5), 1.0)
            if u_m > 0.6:
                ql = esm((tl - c["pasir"]) / 0.3)
                chip(img, px + 150, py - 40, "SEUKURAN PASIR", EMAS, ql * (1 - uj), tl - c["pasir"], fsz=24)
                line_on(img, (px + 28, py - 12), (px + 80, py - 30), mix(EMAS, WHITE, 0.3), 3, ql * (1 - uj))
    # komet kecil + panah ('Halley')
    qk = esm((tl - c["halley"]) / 0.4) * (1 - esm((tl - t_tabrak + 0.5) / 0.3))
    if qk > 0:
        V._panah11(img, (KOMET_P[0] - 60, KOMET_P[1] - 40), (px - 40, py - 30), qk * 0.9, clamp((tl - c["halley"]) / 0.5), mix(KUNING, WHITE, 0.4), width=5, lengkung=-0.2)
        chip(img, KOMET_P[0] - 120, KOMET_P[1] - 120, "SISA HALLEY, RATUSAN TAHUN", EMAS, qk, tl - c["halley"], fsz=22)
    # tabrakan -> garis cahaya ('terbakar')
    if tl >= t_tabrak:
        ut = clamp((tl - t_tabrak) / 0.25)
        V._partikel11(img, px, Y_HOR - 118, tl - t_tabrak, mix(ORANYE, WHITE, 0.3), 0.9, n=14, jarak=140)
        V._glow11(img, px, Y_HOR - 118, 140, ORANYE, 0.6 * (1 - esm((tl - t_tabrak) / 1.2)))
        ub = esm((tl - c["terbakar"]) / 0.7)
        if ub > 0:
            p0 = (px - 10, Y_HOR - 125)
            p1 = (px + 230 * ub, Y_HOR - 125 - 170 * ub)
            # butir memanjang jadi garis (morph semantik: titik -> garis cahaya)
            garis_meteor(img, p0, p1, 1.0, mix(WHITE, KUNING, 0.2), 7, M.KELUAR[0], ekor=0.95)
            V._glow11(img, p1[0], p1[1], 80, KUNING, 0.6 * M.KELUAR[0])
        else:
            dot_on(img, px, Y_HOR - 118, 22 * (1 - ut) + 12, mix(ORANYE, WHITE, 0.5), M.KELUAR[0])
        qc = esm((tl - c["cahaya"]) / 0.3)
        chip(img, px + 120, Y_HOR - 330, "GARIS CAHAYA", KUNING, qc, tl - c["cahaya"], fsz=24)
    # odometer 66 KM/DETIK
    qo = esm((tl - c["enam1"] + 0.1) / 0.3)
    if qo > 0:
        n = 0
        for key, val in (("enam1", 6), ("puluh", 60), ("enam2", 66)):
            if tl >= c[key]:
                n = val
        f = font(D.FB, 60)
        paste_c(img, 300, Y_ALAT - 10, f"{n}", f, accent, qo * M.KELUAR[0])
        label(img, 300, Y_ALAT + 42, "KM / DETIK", mix(INK, CREAM, 0.2), qo, fsz=22)
        qj = esm((tl - c["enam2"] - 0.4) / 0.35)
        chip(img, 690, Y_ALAT, "SEKITAR 240.000 KM/JAM", accent, qj, tl - c["enam2"] - 0.4, fsz=24)
    cakrawala(img, tg, 1.0, orang=1.0)
    chip_tanggal(img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.10)


def _jam_pada(tl, c):
    """Jarum jam 21.00 -> 00.30 ('terbenam' .. 'tengah'), lalu 02.00 -> 05.00 ('terbaik' .. 'wita')."""
    if tl < c["terbenam"]:
        return 21.0
    if tl < c["tengah"] + 0.4:
        return 21.0 + 3.5 * esm((tl - c["terbenam"]) / max(0.3, c["tengah"] + 0.4 - c["terbenam"]))
    if tl < c["terbaik"]:
        return 24.5
    return 24.5 + 4.5 * esm((tl - c["terbaik"]) / max(0.5, c["wita"] - c["terbaik"]))


def sc_jam50(img, d, sc, tl, dur, tg, accent, al, dy):
    """BODY 2. Kalender -> jam: tunggu Bulan terbenam; 02.00-05.00 WIB."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["jam50"])
    h = _jam_pada(tl, c)
    turun = esm((tl - c["terbenam"]) / max(0.4, c["tengah"] + 0.3 - c["terbenam"]))
    gelap = 0.9 + 0.1 * turun
    cakram_langit(img, CX, CY, R, tg, gelap, 1.0, 0.6 + 0.4 * turun)
    komet(img, KOMET_P[0], KOMET_P[1], 1.0, tg, 0.25, (-0.8, -0.6), 1.0)
    # bulan terbenam: turun melewati cakrawala
    by = CY - 120 + (Y_HOR + 90 - (CY - 120)) * turun
    if by < Y_HOR + 40:
        bulan(img, CX + 190 - 60 * turun, by, 46, 0.5 + 0.5 * esm(tl / 0.5), 0.6 + 0.4 * (1 - turun))
    # meteor mulai ramai setelah gelap
    meteor_acak(img, tg, sc["start"] + c["gelap"] - 0.5, sc["start"] + dur - 0.5, 1.1, 0.95 * turun, seed=3)
    M.bab(img, sc, accent, tl, 1.0)
    cakrawala(img, tg, 1.0, orang=1.0)
    # kalender (kotak 21) -> jam (morph) saat 'Jamnya'
    um = esm((tl - c["jamnya"]) / 0.6)
    if um < 1:
        kotak = [(250 - 30, Y_ALAT - 34), (250 + 30, Y_ALAT - 34), (250 + 30, Y_ALAT + 34), (250 - 30, Y_ALAT + 34)]
        pts = morph(kotak, bentuk_lingkaran(250, Y_ALAT, 78), um)
        poly_on(img, pts, mix(accent, WHITE, 0.1), 1.0)
        paste_c(img, 250, Y_ALAT, "21", font(D.FB, 26), WHITE, 1 - um)
    else:
        lab = f"{int(h % 24):02d}.{int((h % 1) * 60):02d}"
        ket = "RABU MALAM" if tl < c["terbenam"] else ("BULAN TERBENAM" if tl < c["terbaik"] else "WAKTU TERBAIK")
        jam(img, 250, Y_ALAT, 78, h, 1.0, accent, tg, label=f"{ket} · {lab}")
    # chip jam terbaik
    chip(img, 660, Y_ALAT - 36, "02.00 - 05.00 WIB", accent, esm((tl - c["wib"] + 0.3) / 0.3), tl - c["wib"] + 0.3, fsz=27)
    chip(img, 660, Y_ALAT + 34, "03.00 - 06.00 WITA", mix(accent, INK, 0.2), esm((tl - c["wita"] + 0.2) / 0.3), tl - c["wita"] + 0.2, fsz=25)
    # penanda puncak di dalam cakram (kecil, informatif)
    qp = esm((tl - c["tengah"]) / 0.4)
    chip(img, CX - 150, CY - 250, "PUNCAK ± 01.00 WIB", KUNING, qp, tl - c["tengah"], fsz=22)
    # penghitung ~20/jam
    qh = esm((tl - c["perjam"] + 0.4) / 0.3)
    chip(img, CX + 170, CY - 250, "SEKITAR 20 METEOR/JAM", STAR, qh, tl - c["perjam"] + 0.4, fsz=22)
    chip_tanggal(img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.10)


ORION = [(0.00, -0.62), (0.34, -0.52), (-0.36, -0.46), (-0.10, 0.00), (0.02, 0.06), (0.14, 0.12),
         (0.40, 0.60), (-0.44, 0.58)]      # Betelgeuse, Bellatrix, Meissa-ish, sabuk x3, Saiph, Rigel (relatif)
ORION_L = [(0, 3), (1, 4), (3, 4), (4, 5), (5, 7), (3, 6), (0, 1)]


def sc_arah50(img, d, sc, tl, dur, tg, accent, al, dy):
    """BODY 3. Jam -> kompas: timur, Orion, lihat ke samping, tanpa teleskop, HP mati."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["arah50"])
    cakram_langit(img, CX, CY, R, tg, 1.0, 1.0, 1.0)
    komet(img, KOMET_P[0], KOMET_P[1], 1.0, tg, 0.22, (-0.8, -0.6), 1.0)
    # radiant naik dari timur (kanan cakrawala) ke tinggi ('tinggi')
    un = esm((tl - c["tinggi"] + 0.2) / 2.2)
    rad = (CX + 250 - 170 * un, Y_HOR - 60 - 420 * un)
    meteor_acak(img, tg, sc["start"] + 0.5, sc["start"] + dur - 0.5, 1.2, 0.9, radiant=rad, seed=4)
    # jejak lintasan radiant (panah naik)
    V._panah11(img, (CX + 250, Y_HOR - 40), (rad[0], rad[1] - 10), esm((tl - c["tinggi"]) / 0.4) * 0.6 * M.KELUAR[0], un, mix(UNGU, WHITE, 0.5), width=4, lengkung=-0.18)
    # Orion menggambar diri ('Orion'), sabuk disorot pada 'tiga','bintang','sejajar'
    qo = esm((tl - c["orion"]) / 0.5) * M.KELUAR[0]
    if qo > 0:
        sk = 185
        P = [(rad[0] + x * sk - 20, rad[1] + y * sk + 95) for (x, y) in ORION]
        for k, (i, j) in enumerate(ORION_L):
            uu = esm((tl - c["orion"] - 0.06 * k) / 0.35)
            if uu > 0:
                q1 = (P[i][0] + (P[j][0] - P[i][0]) * uu, P[i][1] + (P[j][1] - P[i][1]) * uu)
                line_on(img, P[i], q1, mix(STAR, UNGU, 0.3), 2, qo * 0.8)
        for k, p in enumerate(P):
            sab = k in (3, 4, 5)
            sor = esm((tl - c[("tiga", "bintang", "sejajar")[k - 3]]) / 0.25) if sab else 0.0
            dot_on(img, p[0], p[1], 4 + 4 * sor, mix(STAR, KUNING, sor), qo)
            if sor > 0:
                V._glow11(img, p[0], p[1], 40, KUNING, qo * sor * 0.7)
        label(img, P[0][0] + 70, P[0][1] - 30, "ORION", mix(STAR, UNGU, 0.2), qo, fsz=24)
        # titik pancar (radiant)
        ring_on(img, rad[0], rad[1], 16 + 4 * math.sin(tg * 4), mix(UNGU, WHITE, 0.5), 3, qo)
    # jangan menatap tepat: mata dicoret di radiant; lihat ke samping: kerucut pandang bergeser
    qj = esm((tl - c["jangan"]) / 0.3) * (1 - esm((tl - c["samping"] - 0.2) / 0.3))
    if qj > 0:
        silang(img, rad[0], rad[1], 26, MERAH, qj, clamp((tl - c["jangan"]) / 0.3))
    qs = esm((tl - c["samping"]) / 0.5) * M.KELUAR[0]
    if qs > 0:
        ang = math.radians(-35)
        tx, ty = rad[0] - 210 * qs, rad[1] + 40 * qs
        ring_on(img, tx, ty, 90, mix(HIJAU, WHITE, 0.3), 4, qs)
        label(img, tx, ty - 112, "LIHAT KE SINI", mix(HIJAU, WHITE, 0.5), qs, fsz=22)
        up = esm((tl - c["panjang"]) / 0.6)
        if up > 0:
            garis_meteor(img, (tx + 60, ty - 50), (tx - 70 + 0 * ang, ty + 60), up, mix(WHITE, KUNING, 0.2), 5, M.KELUAR[0], ekor=0.9)
            chip(img, tx, ty + 124, "EKOR PALING PANJANG", KUNING, esm((tl - c["panjang"] - 0.2) / 0.3), tl - c["panjang"] - 0.2, fsz=22)
    M.bab(img, sc, accent, tl, 1.0)
    cakrawala(img, tg, 1.0, orang=1.0)
    # jam -> kompas (morph) saat 'timur'
    um = esm((tl - c["timur"]) / 0.6)
    if um < 1:
        jam(img, 250, Y_ALAT, 78, 5.0, 1 - um, TEAL, tg)
        kompas(img, 250, Y_ALAT, 78, um, accent, -20.0 * (1 - um))
    else:
        kompas(img, 250, Y_ALAT, 78, 1.0, accent, 0.0)
    label(img, 250, Y_ALAT - 112, "TIMUR, LALU MAKIN TINGGI", mix(INK, CREAM, 0.15), esm((tl - c["timur"]) / 0.4), fsz=22)
    # tanpa teleskop, HP mati 20 menit
    qt = esm((tl - c["teleskop"] + 0.3) / 0.3) * M.KELUAR[0]
    if qt > 0:
        tx0, ty0 = 560, Y_ALAT
        line_on(img, (tx0 - 36, ty0 + 26), (tx0 + 36, ty0 - 26), mix(INK, CREAM, 0.3), 12, qt)
        line_on(img, (tx0 + 22, ty0 - 2), (tx0 + 10, ty0 + 40), mix(INK, CREAM, 0.3), 6, qt)
        silang(img, tx0, ty0, 44, MERAH, qt, clamp((tl - c["teleskop"]) / 0.3))
        label(img, tx0, ty0 + 72, "TANPA TELESKOP", mix(INK, CREAM, 0.2), qt, fsz=20)
    qh = esm((tl - c["hp"] + 0.2) / 0.3) * M.KELUAR[0]
    if qh > 0:
        hx, hy = 790, Y_ALAT
        gel = esm((tl - c["hp"]) / 0.5)
        rrect_on(img, hx - 28, hy - 48, hx + 28, hy + 48, 10, mix(WHITE, INK, 0.1 + 0.8 * gel), qh, outline=INK, width=3)
        chip(img, hx - 20, hy - 86, "LAYAR MATI 20 MENIT", accent, esm((tl - c["menit"] + 0.3) / 0.3), tl - c["menit"] + 0.3, fsz=22)
    chip_tanggal(img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.10)


def sc_orbit50(img, d, sc, tl, dur, tg, accent, al, dy):
    """MICRO-CLIMAX. Cakram jadi peta orbit: Matahari, orbit Bumi, elips Halley + sungai debu;
    Bumi menyeberangi sungai itu di tanggal yang sama setiap tahun."""
    M.set_keluar(tl, dur, ada_lanjutan=True)
    c = cues(sc, dur, CUES["orbit50"])
    masuk = ease12(clamp(tl / 1.0), 0.05, 0.04)
    # kilat payoff: seluruh langit menyala sesaat tepat pada 'menyeberangi' (sinkron thump), lalu pulih
    tc0 = tl - c["menyeberangi"]
    kilat = math.exp(-tc0 / 0.16) if tc0 >= 0 else 0.0
    cakram_langit(img, CX, CY, R, tg, 1.0 - 0.45 * kilat, 1.0, 1.0 - 0.2 * esm(tl / 0.8))
    komet(img, KOMET_P[0], KOMET_P[1], 1.0, tg, 0.22 * (1 - esm(tl / 0.6)), (-0.8, -0.6), 1.0)
    cakrawala(img, tg, 1 - esm(tl / 0.6), orang=1.0)
    s = 0.25 + 0.75 * clamp(masuk)
    sun = (CX, CY + 20)
    rb = 150 * s                                    # orbit Bumi
    a_h, b_h, rot = 300 * s, 112 * s, math.radians(-28)
    # pusat elips Halley digeser supaya Matahari di fokus
    cc = math.sqrt(max(0.0, a_h * a_h - b_h * b_h))
    hc = (sun[0] - cc * math.cos(rot), sun[1] - cc * math.sin(rot))
    # 'satukan': cincin orbit tergambar; Matahari pada 'Matahari'
    qs = esm((tl - c["satukan"] + 0.3) / 0.6)
    ring_on(img, sun[0], sun[1], rb, mix(STAR, NAVY2, 0.35), 2, qs)
    el = elips_pts(hc[0], hc[1], a_h, b_h, n=96, rot=rot)
    _dalam = lambda p: math.hypot(p[0] - CX, p[1] - CY) < R - 6          # noqa: E731
    for i in range(len(el)):
        p0_, p1_ = el[i], el[(i + 1) % len(el)]
        if _dalam(p0_) and _dalam(p1_):
            line_on(img, p0_, p1_, mix(KUNING, NAVY2, 0.45), 2, qs)
    qm = esm((tl - c["matahari"]) / 0.35)
    V._glow11(img, sun[0], sun[1], 70, KUNING, 0.6 * qm)
    dot_on(img, sun[0], sun[1], 16 * eob(qm, 1.6), mix(KUNING, WHITE, 0.3), qm)
    label(img, sun[0], sun[1] + 36, "MATAHARI", mix(KUNING, WHITE, 0.5), qm, fsz=18)
    # komet berkeliling ('Halley' .. 'sekali')
    uk = esm((tl - c["halley"]) / max(1.0, c["sekali"] - c["halley"] + 0.6))
    # posisi menyilang orbit Bumi: titik di elips yang jaraknya ~rb dari Matahari
    best, u_cross = None, 0.0
    for i in range(0, 400):
        u = i / 400
        p = titik_elips(hc[0], hc[1], a_h, b_h, u, rot)
        dd = abs(math.hypot(p[0] - sun[0], p[1] - sun[1]) - rb)
        if best is None or dd < best:
            best, u_cross = dd, u
    pc = titik_elips(hc[0], hc[1], a_h, b_h, u_cross, rot)
    # sungai debu di sepanjang elips ('sungai')
    qd = esm((tl - c["sungai"]) / 0.8)
    if qd > 0:
        for i in range(0, 96, 2):
            p = el[i]
            if not _dalam(p):
                continue
            jit = 9 * math.sin(i * 1.7) * s
            dot_on(img, p[0] + jit, p[1] - jit * 0.6, 3.0 + 1.5 * ((i * 7) % 3), mix(KUNING, WHITE, 0.3), qd * 0.55)
        label(img, CX - 120, CY - 175, "SUNGAI DEBU HALLEY", mix(KUNING, WHITE, 0.4), qd, fsz=20)
    if uk > 0:
        pk = titik_elips(hc[0], hc[1], a_h, b_h, (u_cross + 0.02 + uk * 1.0) % 1.0, rot)
        dx_, dy_ = pk[0] - sun[0], pk[1] - sun[1]
        if _dalam(pk):
            komet(img, pk[0], pk[1], 0.35 * s, tg, 1.0, (dx_, dy_), 0.7)
        chip(img, pk[0] + 110, pk[1] - 40, "76 TAHUN SEKALI", KUNING, esm((tl - c["sekali"]) / 0.3) * (1 - esm((tl - c["setiap"]) / 0.3)), tl - c["sekali"], fsz=22)
    # Bumi berkeliling ('Setiap') -> tiba di persilangan tepat saat 'menyeberangi'
    t_mulai, t_cross = c["setiap"] - 0.4, c["menyeberangi"]
    ang_cross = math.atan2(pc[1] - sun[1], pc[0] - sun[0])
    if tl >= t_mulai:
        ue = esm((tl - t_mulai) / max(0.6, t_cross - t_mulai))
        if tl > t_cross:
            ue = 1.0 + 0.06 * esm((tl - t_cross) / 3.0)      # terus berjalan pelan setelah persilangan
        ang = ang_cross - 2 * math.pi * 0.75 * (1 - ue) if ue <= 1 else ang_cross + 2 * math.pi * (ue - 1)
        pe = (sun[0] + rb * math.cos(ang), sun[1] + rb * math.sin(ang))
        V._glow11(img, pe[0], pe[1], 36, (120, 180, 255), 0.6)
        dot_on(img, pe[0], pe[1], 9, (90, 150, 240), 1.0, outline=WHITE, width=2)
        label(img, pe[0], pe[1] + 28, "BUMI", mix(WHITE, NAVY2, 0.1), 1.0, fsz=16)
    # persilangan: kesunyian sebelum (kamera diam), lalu payoff (thump) - meteor berhamburan dari Bumi
    if tl >= t_cross:
        tt = tl - t_cross
        V._partikel11(img, pc[0], pc[1], tt, mix(KUNING, WHITE, 0.4), 1.0, n=16, jarak=160)
        V._glow11(img, pc[0], pc[1], 150, KUNING, 0.6 * (1 - esm(tt / 1.5)) + 0.18)
        # riak ganda (gelombang kejut) + riak ketiga lebar & samar: payoff yang terbaca sampai ke tepi cakram
        for (tunda, rmax, wd) in ((0.0, 70, 3), (0.14, 120, 2), (0.30, 230, 2)):
            q = esm((tt - tunda) / 0.8)
            if 0 < q < 1:
                ring_on(img, pc[0], pc[1], 22 + rmax * q, KUNING, wd, (1 - q) ** 1.3)
        # sungai debu 'tersentuh': butir di sekitar persilangan berdenyut terang lalu tenang
        for i in range(0, 96, 2):
            p = el[i]
            if _dalam(p) and math.hypot(p[0] - pc[0], p[1] - pc[1]) < 150 * s:
                jit = 9 * math.sin(i * 1.7) * s
                dot_on(img, p[0] + jit, p[1] - jit * 0.6, 4.0, WHITE, 0.6 * math.exp(-tt / 0.5))
        for k in range(6):
            a = ang_cross + 0.4 + k * 0.5
            uu = esm((tt - 0.1 * k) / 0.6)
            if 0 < uu < 1:
                garis_meteor(img, pc, (pc[0] + 110 * math.cos(a), pc[1] + 110 * math.sin(a)), uu, STAR, 3, 0.9)
        chip(img, pc[0] - 40, pc[1] + 64, "21-22 OKTOBER", KUNING, esm(tt / 0.3), tt, fsz=24)
    qk = esm((tl - c["kebetulan"]) / 0.3)
    M.stiker(img, CX, CY - 300, "BUKAN KEBETULAN", 1.0, tl - c["kebetulan"], bg=accent, fsz=28, rot=-4)
    # tahun-tahun berulang ('Oktober')
    qt = esm((tl - c["oktober"]) / 0.3)
    if qt > 0:
        for k, th in enumerate(("2024", "2025", "2026", "2027")):
            kk = esm((tl - c["oktober"] - 0.12 * k) / 0.25)
            chip(img, 300 + k * 160, Y_ALAT - 44, th, KUNING if th == "2026" else mix(INK, CREAM, 0.2), kk, tl - c["oktober"] - 0.12 * k, fsz=24)
        label(img, 540, Y_ALAT + 6, "SETIAP OKTOBER, TANGGAL YANG SAMA", mix(INK, CREAM, 0.15), qt, fsz=22)
    # pemicu komentar
    # persisten melintasi batas ke outro (outro menggambarnya lagi di posisi sama) -> TANPA faktor KELUAR
    V._stiker11(img, 540, Y_ALAT + 62, "TULIS KOTAMU DI KOMENTAR", 1.0, tl - c["kota"], bg=HIJAU, fsz=26, rot=-3)
    M.bab(img, sc, accent, tl, 1.0)
    chip_tanggal(img, 1.0)
    teks(img, sc, accent, tl, 1.0, 0.10)


def sc_loop50(img, d, sc, tl, dur, tg, accent, al, dy):
    """SEAMLESS LOOP. Garis cahaya -> butir kembali ke komet -> state frame 0 (komet penuh, tanpa teks)."""
    M.set_keluar(tl, dur, ada_lanjutan=False)
    c = cues(sc, dur, CUES["loop50"])
    kel = esm(tl / 1.1)                                 # peta orbit menyusut, langit kembali
    cakram_langit(img, CX, CY, R, tg, 1.0, 1.0, 0.8 + 0.2 * kel)
    cakrawala(img, tg, kel)
    if kel < 1:
        s = 1.0 - 0.75 * kel
        sun = (CX, CY + 20)
        ring_on(img, sun[0], sun[1], 150 * s, mix(STAR, NAVY2, 0.35), 2, 1 - kel)
        el = elips_pts(sun[0] - 278 * s * math.cos(math.radians(-28)), sun[1] - 278 * s * math.sin(math.radians(-28)), 300 * s, 112 * s, n=72, rot=math.radians(-28))
        for i in range(len(el)):
            p0_, p1_ = el[i], el[(i + 1) % len(el)]
            if math.hypot(p0_[0] - CX, p0_[1] - CY) < R - 6 and math.hypot(p1_[0] - CX, p1_[1] - CY) < R - 6:
                line_on(img, p0_, p1_, mix(KUNING, NAVY2, 0.45), 2, 1 - kel)
        dot_on(img, sun[0], sun[1], 16 * s, mix(KUNING, WHITE, 0.3), 1 - kel)
    # stiker ajakan komentar diteruskan dari f5 (payoff engagement), memudar sebelum teks penutup
    M.stiker(img, 540, Y_ALAT + 62, "TULIS KOTAMU DI KOMENTAR", 1 - esm((tl - 2.3) / 0.5), 10.0, bg=HIJAU, fsz=26, rot=-3)
    # komet tumbuh ke posisi & skala frame 0
    kk = ease12(clamp((tl - 0.3) / 1.3), 0.0, 0.03)
    komet(img, KOMET_P[0], KOMET_P[1], 0.35 + 0.65 * kk, tg, clamp(0.25 + 0.75 * kk), (-0.8, -0.6), 1.0)
    # garis cahaya ('terbakar') lalu 'mundur' jadi butir yang kembali ke ekor komet ('komet')
    p_jatuh, p_akhir = (CX + 40, CY - 40), (CX + 250, Y_HOR - 60)
    t_b, t_k = c["terbakar"], c["komet"]
    if t_b <= tl < t_k:
        u = clamp((tl - t_b) / 0.55)
        garis_meteor(img, p_jatuh, p_akhir, u, mix(WHITE, KUNING, 0.25), 6, 1.0 if u < 1 else max(0.0, 1 - (tl - t_b - 0.55) / 0.6))
    if t_k <= tl < t_k + 1.1:
        u = esm((tl - t_k) / 1.1)
        gx = p_akhir[0] + (KOMET_P[0] - 120 - p_akhir[0]) * u
        gy = p_akhir[1] + (KOMET_P[1] - 90 - p_akhir[1]) * u
        poly_on(img, bentuk_butir(gx, gy, 9 * (1 - u) + 2, 3), mix(KUNING, WHITE, 0.5), 1 - u * 0.5)
        garis_meteor(img, p_akhir, (gx, gy), 1.0, mix(KUNING, WHITE, 0.3), 3, 0.5 * (1 - u), ekor=0.3)
    chip_tanggal(img, 1.0)
    # teks: muncul 'sama' & 'kembali', hilang sebelum 0,8 s terakhir (frame akhir == frame 0)
    at = 1 - esm((tl - dur + 0.95) / 0.35)
    lines = sc.get("lines") or ["KOMET YANG SAMA", "KEMBALI 2061"]
    teks(img, sc, accent, tl, at, c["sama"], " ".join(lines), "2061", fsz=58, y=Y_TXT, maxw=860)


VISUALS50 = {"komet50": sc_komet50, "salahjam50": sc_salahjam50, "debu50": sc_debu50, "jam50": sc_jam50,
             "arah50": sc_arah50, "orbit50": sc_orbit50, "loop50": sc_loop50}


def _selftest():
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (int(1080 * D.SS), int(1920 * D.SS)), CREAM)
    d = ImageDraw.Draw(img)
    for n, fn in VISUALS50.items():
        sc = {"id": {"komet50": "intro", "loop50": "outro"}.get(n, "f1"), "visual": n, "start": 10.0, "dur": 16.0,
              "badge": "TUNGGU BULAN TERBENAM: 02.00-05.00 WIB", "hl": "02.00-05.00",
              "lines": ["SERPIHAN KOMET HALLEY", "TERBAKAR KAMIS DINI HARI"], "trans": "morph"}
        for tl in (0.0, 0.4, 2.0, 5.0, 8.0, 11.0, 14.0, 15.9):
            fn(img, d, sc, tl, 16.0, 10.0 + tl, D.hexc("#1F2A5A"), 1.0, 0.0)
        ev = events_v12(sc)
        assert ev and all(e[1] for e in ev), n
    print(f"selftest ep50 v12: {len(VISUALS50)} adegan OK")


def daftar():
    """Daftarkan visual, beat, dan event Ep50 ke mesin (idempoten; dipanggil saat impor)."""
    V.BEATS.update(BEATS50)
    D.VISUALS.update(VISUALS50)
    M.EVENTS12.update({k: events_v12 for k in CUES})


daftar()


if __name__ == "__main__":
    _selftest()
