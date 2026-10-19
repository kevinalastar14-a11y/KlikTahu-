"""Ep43 KUPING BERDENGING - adegan mesin v11 (diimpor oleh mesin_v11).

Beat bernama: KAMUS `B43[visual] = {nama: (fraksi, suara)}`. Fungsi gambar memanggil
`t_(nama)` -> detik muncul; BEATS (untuk SFX) dibangun dari kamus yang sama, jadi animasi
dan suara tidak bisa selisih. Fraksi disetel dari posisi kata kunci di VO (timeline captions).
"""
import math

import diagrams as D
from diagrams import (INK, CREAM, WHITE, MUTED, RED, BLUE, GREEN, AMBER, FB, FS,
                      mix, seg, clamp, esmooth, eob, eo, font, paste_c,
                      rrect_on, line_on, dot_on, ring_on, poly_on, ell)

import mesin_v11 as M
from mesin_v11 import (_stiker11, _label11, _glow11, _panah11, _gelom11, _pancar11, _partikel11,
                       _judul11, _hdr, _orang11, GELAP)

B43 = {
    "intro_kuping43": {"telinga": (0.05, "whoosh"), "nging": (0.10, "nging"), "hilang": (0.40, "swish"),
                       "bukan": (0.55, "impact"), "dalam": (0.80, "riser_end"), "sendiri": (0.84, "impact")},
    "koklea43": {"telinga": (0.04, "whoosh"), "zoom": (0.16, "whoosh"), "sel": (0.33, "pop"),
                 "nada1": (0.58, "tick"), "nada2": (0.63, "tick"), "nada3": (0.68, "tick"),
                 "listrik": (0.78, "zap"), "otak": (0.88, "ding")},
    "salah43": {"sel": (0.05, "pop"), "nyala": (0.20, "zap"), "nging": (0.44, "nging"),
                "pudar": (0.62, "swish"), "aman": (0.80, "ding")},
    "hening43": {"tahun": (0.04, "impact"), "orang": (0.27, "pop"), "pintu": (0.42, "door"),
                 "persen": (0.55, "impact"), "bising": (0.78, "whoosh")},
    "konser43": {"konser": (0.04, "boom"), "lelah": (0.34, "thud"), "pulih": (0.50, "ding"),
                 "rusak": (0.72, "glitch"), "tidak": (0.84, "impact")},
    "otak43": {"piano": (0.05, "pop"), "patah": (0.17, "glitch"), "otak": (0.38, "whoosh"),
               "keras": (0.50, "riser_end"), "dengung": (0.78, "nging")},
    "who43": {"batas": (0.12, "impact"), "tangga1": (0.37, "pop"), "tangga2": (0.47, "pop"),
              "tangga3": (0.53, "pop"), "earphone": (0.62, "whoosh"), "seratus": (0.75, "boom"),
              "menit": (0.87, "tick")},
    "tips43": {"vol": (0.04, "swish"), "enam": (0.18, "ding"), "jeda": (0.30, "pop"),
               "dokter": (0.42, "impact"), "t1": (0.52, "pop"), "t2": (0.66, "pop"), "t3": (0.74, "pop"),
               "t4": (0.84, "pop")},
    "rangkuman43": {"s1": (0.06, "pop"), "s2": (0.19, "pop"), "s3": (0.50, "pop"),
                    "kirim": (0.64, "impact"), "panah": (0.68, "whoosh")},
}
for _k, _v in B43.items():
    M.BEATS[_k] = sorted(_v.values())

KULIT = (236, 190, 160)
KULIT_G = (200, 140, 112)
PINK = (232, 140, 150)


def _t(nama, key, dur):
    return B43[nama][key][0] * dur


# ------------------------------------------------------------------ objek Ep43
def _telinga43(img, cx, cy, s, alpha, tg, nging=0.0, col=None):
    """Daun telinga samping: bentuk C + heliks dalam + lubang; nging = pancaran kuning."""
    if alpha <= 0.01:
        return
    col = col or KULIT
    ell(img, cx - 95 * s, cy - 150 * s, cx + 85 * s, cy + 150 * s, fill=col, alpha=alpha,
        outline=KULIT_G, width=5)
    ell(img, cx - 55 * s, cy - 100 * s, cx + 55 * s, cy + 90 * s, fill=mix(col, KULIT_G, 0.35), alpha=alpha)
    ell(img, cx - 35 * s, cy - 65 * s, cx + 40 * s, cy + 45 * s, fill=col, alpha=alpha)
    ell(img, cx - 38 * s, cy + 70 * s, cx + 20 * s, cy + 150 * s, fill=col, alpha=alpha, outline=KULIT_G, width=4)
    dot_on(img, cx - 5 * s, cy + 5 * s, 20 * s, (70, 40, 40), alpha)
    if nging > 0.02:
        _glow11(img, cx, cy, 170 * s, (255, 220, 110), alpha * nging * 0.55)
        for k in range(3):
            ph = (tg * 1.5 + k / 3.0) % 1.0
            M._busur11(img, cx + 30 * s, cy, (60 + 150 * ph) * s, (240, 170, 40), 7,
                       alpha * nging * (1 - ph), -45, 45)


def _koklea43(img, cx, cy, r, alpha, tg, col, glow=None, n_tampil=1.0, lebar=18):
    """Spiral rumah siput 2,6 putaran; glow = (u0,u1) bagian spiral yang menyala."""
    if alpha <= 0.01:
        return
    pts = []
    N = 140
    for i in range(int(N * clamp(n_tampil)) + 1):
        u = i / N
        a = u * 2.6 * 2 * math.pi
        rr = r * (1 - 0.82 * u)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.92))
    if len(pts) < 2:
        return
    M._pline(img, pts, mix(col, WHITE, 0.55), lebar + 10, alpha)
    M._pline(img, pts, col, lebar, alpha)
    if glow:
        u0, u1 = glow
        g = [p for i, p in enumerate(pts) if u0 <= i / N <= u1]
        if len(g) > 1:
            M._pline(img, g, (255, 210, 90), lebar + 4, alpha)
            mx = g[len(g) // 2]
            _glow11(img, mx[0], mx[1], 70, (255, 200, 80), alpha * 0.8)


def _selr43(img, x, base, h, alpha, col, goyang=0.0, nyala=0.0, tg=0.0):
    """Satu sel rambut: badan + berkas bulu di atas; nyala = kilau kuning."""
    sway = goyang * math.sin(tg * 9 + x * 0.05) * 10
    rrect_on(img, x - 17, base - h, x + 17, base, 14, mix(col, WHITE, 0.2), alpha)
    dot_on(img, x, base - h * 0.35, 8, mix(col, INK, 0.35), alpha)
    for k in (-1, 0, 1):
        line_on(img, (x + k * 8, base - h), (x + k * 8 + sway * (1 + abs(k) * 0.3), base - h - 34 - (1 - abs(k)) * 10),
                mix(col, INK, 0.3), 4, alpha)
    if nyala > 0.02:
        _glow11(img, x, base - h - 20, 70, (255, 215, 90), alpha * nyala * 0.9)
        dot_on(img, x, base - h - 44, 7, (255, 200, 60), alpha * nyala)


def _earphone43(img, cx, cy, s, alpha, col=WHITE, tg=0.0, dentum=0.0):
    rrect_on(img, cx - 34 * s, cy - 44 * s, cx + 34 * s, cy + 44 * s, 30 * s, col, alpha,
             outline=mix(INK, CREAM, 0.4), width=3)
    rrect_on(img, cx - 10 * s, cy + 30 * s, cx + 10 * s, cy + 110 * s, 10 * s, col, alpha,
             outline=mix(INK, CREAM, 0.4), width=3)
    dot_on(img, cx - 10 * s, cy - 8 * s, 14 * s, mix(INK, CREAM, 0.6), alpha)
    if dentum > 0.02:
        for k in range(2):
            ph = (tg * 2.2 + k * 0.5) % 1.0
            M._busur11(img, cx - 40 * s, cy - 8 * s, (30 + 90 * ph) * s, RED, 6, alpha * dentum * (1 - ph), 150, 210)


def _gelas43(img, cx, base, s, alpha, isi, tg, col=BLUE):
    """Gelas meter (dB): wadah + isian bergelombang."""
    w, h = 90 * s, 260 * s
    rrect_on(img, cx - w / 2, base - h, cx + w / 2, base, 18 * s, WHITE, alpha, outline=GELAP, width=5)
    ih = (h - 16 * s) * clamp(isi)
    if ih > 4:
        rrect_on(img, cx - w / 2 + 8 * s, base - 8 * s - ih, cx + w / 2 - 8 * s, base - 8 * s, 12 * s, col, alpha)


# ------------------------------------------------------------------ adegan
def sc_intro_kuping43(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "intro_kuping43"
    L = sc.get("lines") or ["KUPING TIBA-TIBA", "BERDENGING?"]
    _judul11(img, L[0], INK, tl, al, y=450, fsz=66, t0=0.05)
    _judul11(img, L[1], accent, tl, al, y=555, fsz=84, t0=0.30, hl=L[1])
    q = esmooth(seg(tl, 0.15, 0.7))
    if q <= 0.01:
        return
    t_ng = _t(N, "nging", dur)
    t_hl = _t(N, "hilang", dur)
    ng = esmooth(seg(tl, t_ng, t_ng + 0.25)) * (1 - esmooth(seg(tl, t_hl, t_hl + 1.2)))
    ng2 = esmooth(seg(tl, _t(N, "sendiri", dur), _t(N, "sendiri", dur) + 0.4))
    goy = ng * 6 * math.sin(tg * 40)
    _telinga43(img, 540 + goy, 1120 + dy + (1 - eob(q, 1.4)) * 200, 1.9, al * q, tg, nging=max(ng, ng2 * 0.8))
    # gelombang nada tinggi (sinus rapat) melintas
    if ng > 0.02:
        _gelom11(img, 140, 940, 820 + dy, 26 * ng, 34, tg * 16, (230, 160, 30), 6, al * ng)
    tt = tl - t_ng
    _stiker11(img, 800, 870 + dy, "NGIIING!", al * (1 - esmooth(seg(tl, t_hl, t_hl + 0.8))), tt,
              bg=AMBER, fsz=44, rot=8, tg=tg)
    tt = tl - t_hl
    if tt > 0:
        _label11(img, 800, 950 + dy, "...hilang dalam detik", MUTED, al * clamp(tt / 0.4), fsz=26)
    tt = tl - _t(N, "bukan", dur)
    if tt > 0:
        _stiker11(img, 290, 1480 + dy, "BUKAN DARI LUAR", al, tt, bg=GELAP, fsz=30, rot=-5, tg=tg)
        line_on(img, (170, 1550 + dy), (410, 1550 + dy), RED, 6, al * clamp(tt / 0.3))
    tt = tl - _t(N, "sendiri", dur)
    if tt > 0:
        _panah11(img, (780, 1560 + dy), (620, 1260 + dy), al, clamp(tt / 0.45), accent, width=9, lengkung=0.3)
        _stiker11(img, 790, 1620 + dy, "DARI DALAM!", al, tt, bg=accent, fsz=34, rot=4, tg=tg)


def sc_koklea43(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "koklea43"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "telinga", dur), _t(N, "telinga", dur) + 0.6))
    if q <= 0.01:
        return
    zm = esmooth(seg(tl, _t(N, "zoom", dur), _t(N, "zoom", dur) + 0.9))
    # telinga kiri mengecil, koklea tumbuh di tengah (zoom-in)
    _telinga43(img, 250 - 60 * zm, 900 + dy, 0.9 - 0.3 * zm, al * q * (1 - 0.45 * zm), tg)
    if zm > 0:
        _panah11(img, (330, 880 + dy), (470, 900 + dy), al * (1 - zm * 0.4), clamp(zm * 1.4), MUTED, width=6)
        _koklea43(img, 700, 910 + dy, 210, al, tg, accent, n_tampil=zm)
        _label11(img, 700, 690 + dy, "KOKLEA", mix(accent, INK, 0.3), al * zm, fsz=30, name=FB)
        _label11(img, 700, 1150 + dy, "\"rumah siput\"", MUTED, al * zm, fsz=24)
    # deret sel rambut + penanda nada
    qs = esmooth(seg(tl, _t(N, "sel", dur), _t(N, "sel", dur) + 0.5))
    if qs > 0:
        rrect_on(img, 110, 1225 + dy, 970, 1560 + dy, 36, mix(WHITE, CREAM, 0.3), al * qs,
                 outline=mix(accent, WHITE, 0.6), width=3)
        nada = [("RENDAH", 0), ("SEDANG", 1), ("TINGGI", 2)]
        for i in range(9):
            x = 190 + i * 88
            grup = i // 3
            tn = _t(N, f"nada{grup + 1}", dur)
            ny = esmooth(seg(tl, tn, tn + 0.2)) * (1 - esmooth(seg(tl, tn + 0.9, tn + 1.4)))
            if tl > _t(N, "listrik", dur):
                ny = max(ny, 0.5 + 0.5 * math.sin(tg * 6 + i))
            _selr43(img, x, 1440 + dy, 90, al * qs * clamp((qs * 9 - i) / 2 + 0.3), accent,
                    goyang=0.3 + ny, nyala=ny, tg=tg)
        for nm, g in nada:
            tn = _t(N, f"nada{g + 1}", dur)
            qq = esmooth(seg(tl, tn, tn + 0.3))
            _label11(img, 190 + (g * 3 + 1) * 88, 1500 + dy, nm, mix(accent, INK, 0.2), al * qq, fsz=22, name=FB)
        _label11(img, 540, 1260 + dy, "ribuan sel rambut halus", MUTED, al * qs, fsz=24)
    tt = tl - _t(N, "listrik", dur)
    if tt > 0:
        for k in range(3):
            u = ((tg * 1.2) + k / 3) % 1.0
            x = 900
            y = 1380 + dy - 320 * u
            M.D.star4(img, x, y, 12, (255, 200, 60), al * clamp(tt / 0.3) * (1 - u))
        _stiker11(img, 540, 1615 + dy, "GETARAN -> SINYAL LISTRIK", al, tt, bg=accent, fsz=28, rot=-3, tg=tg)
    tt = tl - _t(N, "otak", dur)
    if tt > 0:
        D._ico5(img, "brain", 900, 1150 + dy, 60, mix(accent, INK, 0.1), al * clamp(tt / 0.3), tg,
                pulse=0.5 + 0.5 * math.sin(tg * 5))


def sc_salah43(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "salah43"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "sel", dur), _t(N, "sel", dur) + 0.5))
    if q <= 0.01:
        return
    t_ny = _t(N, "nyala", dur)
    t_pd = _t(N, "pudar", dur)
    ny = esmooth(seg(tl, t_ny, t_ny + 0.3)) * (1 - esmooth(seg(tl, t_pd, t_pd + 2.0)))
    # panggung sel rambut (besar) - 3 sel tengah menyala sendiri
    for i in range(7):
        x = 170 + i * 123
        nyi = ny if i in (2, 3, 4) else 0.0
        _selr43(img, x, 1010 + dy, 150, al * q, accent, goyang=0.15 + nyi, nyala=nyi, tg=tg)
    rrect_on(img, 100, 1010 + dy, 980, 1040 + dy, 12, mix(accent, INK, 0.2), al * q)
    # tanpa suara luar: ikon speaker dicoret
    qa = esmooth(seg(tl, t_ny, t_ny + 0.4))
    if qa > 0:
        sx, sy = 170, 690 + dy
        rrect_on(img, sx - 30, sy - 22, sx - 4, sy + 22, 5, GELAP, al * qa)
        poly_on(img, [(sx - 6, sy - 22), (sx + 26, sy - 46), (sx + 26, sy + 46), (sx - 6, sy + 22)], GELAP, al * qa)
        line_on(img, (sx - 50, sy + 50), (sx + 50, sy - 50), RED, 8, al * qa)
        _label11(img, sx + 190, sy, "tanpa suara luar", MUTED, al * qa, fsz=24)
    # layar osiloskop: nada tinggi lalu memudar
    qo = esmooth(seg(tl, _t(N, "nging", dur) - 0.6, _t(N, "nging", dur)))
    if qo > 0:
        y0 = 1160 + dy
        rrect_on(img, 110, y0, 970, y0 + 280, 30, GELAP, al * qo)
        amp = 70 * clamp(ny * 1.2) + 3
        _gelom11(img, 150, 930, y0 + 140, amp, 38, tg * 14, (120, 230, 170), 5, al * qo,
                 amp_fn=lambda x: 0.35 + 0.65 * math.sin(math.pi * (x - 150) / 780))
        _label11(img, 230, y0 + 36, "NADA TINGGI", (120, 230, 170), al * qo, fsz=22, name=FB)
        # jam detik
        dtk = clamp((tl - t_ny) / max(0.1, (t_pd + 2.0 - t_ny))) * 20
        _label11(img, 850, y0 + 36, f"{int(dtk)} detik", (200, 220, 210), al * qo, fsz=22, name=FB)
    tt = tl - _t(N, "nging", dur)
    _stiker11(img, 760, 700 + dy, "NGIIING", al * (1 - esmooth(seg(tl, t_pd, t_pd + 1.5))), tt, bg=AMBER, fsz=36, rot=6, tg=tg)
    tt = tl - _t(N, "aman", dur)
    if tt > 0:
        D._check5_on(img, 250, 1560 + dy, 46, "check", al, clamp(tt / 0.4), col=GREEN)
        _stiker11(img, 590, 1560 + dy, "UMUM & TIDAK BERBAHAYA", al, tt, bg=GREEN, fsz=28, rot=-3, tg=tg)


def sc_hening43(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "hening43"
    _hdr(img, sc, accent, tl, al)
    tt = tl - _t(N, "tahun", dur)
    if tt <= 0:
        return
    _stiker11(img, 540, 740 + dy, "TAHUN 1953", al, tt, bg=GELAP, fsz=34, rot=-3, tg=tg)
    # ruang kedap suara (dinding busa segitiga)
    qr = esmooth(seg(tl, tt * 0 + _t(N, "tahun", dur) + 0.3, _t(N, "tahun", dur) + 1.0))
    x0, y0, x1, y1 = 150, 800 + dy, 930, 1280 + dy
    rrect_on(img, x0, y0, x1, y1, 20, (70, 76, 92), al * qr)
    for i in range(12):
        xx = x0 + 20 + i * 63
        poly_on(img, [(xx, y0 + 16), (xx + 30, y0 + 52), (xx + 60, y0 + 16)], (100, 108, 126), al * qr)
        poly_on(img, [(xx, y1 - 16), (xx + 30, y1 - 52), (xx + 60, y1 - 16)], (100, 108, 126), al * qr)
    rrect_on(img, x0 + 20, y0 + 60, x1 - 20, y1 - 60, 10, (58, 62, 76), al * qr)
    # 80 orang (grid 10x8 mini) muncul
    qo = esmooth(seg(tl, _t(N, "orang", dur), _t(N, "orang", dur) + 1.0))
    t_ps = _t(N, "persen", dur)
    dengar = esmooth(seg(tl, t_ps, t_ps + 1.4))
    for k in range(80):
        r_, c_ = divmod(k, 16)
        x = x0 + 70 + c_ * 42
        y = y0 + 110 + r_ * 62
        muncul = clamp(qo * 80 - k * 0.8 + 2)
        if muncul <= 0:
            continue
        kena = k < int(round(94 * 80 / 100 * dengar))
        col = (255, 205, 80) if kena else (170, 176, 192)
        _orang11(img, x, y, 0.62, col, al * min(1.0, muncul))
    _label11(img, 540, 1315 + dy, "80 orang, pendengaran normal", MUTED, al * qo, fsz=24)
    tt = tl - _t(N, "pintu", dur)
    if 0 < tt < 1.0:
        _stiker11(img, 540, 1000 + dy, "HENING TOTAL", al * (1 - clamp((tt - 0.6) / 0.4)), tt, bg=accent, fsz=34, tg=tg)
    tt = tl - t_ps
    if tt > 0:
        D._hitung_on(img, 330, 1450 + dy, 94, "", al, tl, t0=t_ps, dur=1.2, col=mix(accent, INK, 0.1), fsz=110)
        paste_c(img, 475, 1430 + dy, "%", font(FB, 60), mix(accent, INK, 0.1), al * clamp(tt / 0.3))
        _label11(img, 740, 1420 + dy, "mendengar dengung", INK, al * clamp(tt / 0.4), fsz=28, name=FB)
        _label11(img, 740, 1470 + dy, "atau desis", MUTED, al * clamp(tt / 0.4), fsz=26)
    tt = tl - _t(N, "bising", dur)
    if tt > 0:
        _stiker11(img, 540, 1610 + dy, "SELALU ADA, TERTUTUP BISING", al, tt, bg=accent, fsz=28, rot=-3, tg=tg)


def sc_konser43(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "konser43"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "konser", dur), _t(N, "konser", dur) + 0.4))
    if q <= 0.01:
        return
    t_rk = _t(N, "rusak", dur)
    # panggung konser: speaker berdentum + lampu sorot
    for sx in (200, 880):
        rrect_on(img, sx - 70, 700 + dy, sx + 70, 960 + dy, 14, GELAP, al * q)
        pump = 1 + 0.12 * abs(math.sin(tg * 9))
        dot_on(img, sx, 780 + dy, 42 * pump, (90, 96, 110), al * q)
        dot_on(img, sx, 900 + dy, 28 * pump, (90, 96, 110), al * q)
        _pancar11(img, sx + (80 if sx < 540 else -80), 820 + dy, tg * 2, RED, al * q * 0.8, rmax=110,
                  a0=-40 if sx < 540 else 140, a1=40 if sx < 540 else 220, width=6, kec=1.4)
    _earphone43(img, 540, 800 + dy, 1.3, al * q, tg=tg, dentum=1.0)
    _label11(img, 540, 990 + dy, "110 dB", RED, al * q, fsz=34, name=FB)
    # 5 sel rambut: tegak -> rebah (lelah) -> pulih ; atau patah (rusak)
    ql = esmooth(seg(tl, _t(N, "lelah", dur), _t(N, "lelah", dur) + 0.6))
    qp = esmooth(seg(tl, _t(N, "pulih", dur), _t(N, "pulih", dur) + 0.9))
    qr = esmooth(seg(tl, t_rk, t_rk + 0.3))
    base = 1370 + dy
    if ql > 0:
        rrect_on(img, 110, 1110 + dy, 530, 1480 + dy, 30, WHITE, al * ql, outline=mix(GREEN, WHITE, 0.5), width=3)
        rrect_on(img, 550, 1110 + dy, 970, 1480 + dy, 30, WHITE, al * qr, outline=mix(RED, WHITE, 0.5), width=3)
        for i in range(4):
            x = 180 + i * 95
            rebah = ql * (1 - qp)
            # sel lelah: bulu condong
            rrect_on(img, x - 16, base - 90, x + 16, base, 13, mix(GREEN, WHITE, 0.3), al * ql)
            for k in (-1, 0, 1):
                tipx = x + k * 8 + 34 * rebah
                tipy = base - 90 - 38 * (1 - 0.7 * rebah)
                line_on(img, (x + k * 8, base - 90), (tipx, tipy), mix(GREEN, INK, 0.3), 4, al * ql)
        _label11(img, 320, 1150 + dy, "LELAH", mix(GREEN, INK, 0.3) if qp < 0.5 else GREEN, al * ql, fsz=26, name=FB)
        if qp > 0:
            _stiker11(img, 320, 1435 + dy, "PULIH 1-2 HARI", al, tl - _t(N, "pulih", dur), bg=GREEN, fsz=24, rot=-3, tg=tg)
    if qr > 0:
        for i in range(4):
            x = 620 + i * 95
            ada = i % 2 == 0
            rrect_on(img, x - 16, base - 90 * (1 if ada else 0.35), x + 16, base, 13,
                     mix(RED, WHITE, 0.3) if ada else (190, 180, 180), al * qr)
            if ada:
                for k in (-1, 0, 1):
                    line_on(img, (x + k * 8, base - 90), (x + k * 8 + 30, base - 100), mix(RED, INK, 0.3), 4, al * qr)
        _label11(img, 760, 1150 + dy, "RUSAK BERULANG", RED, al * qr, fsz=26, name=FB)
        _partikel11(img, 760, 1330 + dy, tl - t_rk, RED, al, n=10, jarak=100)
    tt = tl - _t(N, "tidak", dur)
    if tt > 0:
        _stiker11(img, 760, 1435 + dy, "TIDAK TUMBUH LAGI", al, tt, bg=RED, fsz=24, rot=4, tg=tg)


def sc_otak43(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "otak43"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "piano", dur), _t(N, "piano", dur) + 0.5))
    if q <= 0.01:
        return
    t_pt = _t(N, "patah", dur)
    patah = esmooth(seg(tl, t_pt, t_pt + 0.25))
    keras = esmooth(seg(tl, _t(N, "keras", dur), _t(N, "keras", dur) + 1.2))
    # "piano" nada = equalizer 11 batang: batang 5-7 hilang, tetangga membengkak
    x0, base = 150, 1010 + dy
    for i in range(11):
        x = x0 + i * 72
        hilang = i in (5, 6) and patah > 0
        tet = i in (4, 7) and keras > 0
        tet2 = i in (3, 8) and keras > 0
        h = 110 + 40 * math.sin(tg * 3 + i) * 0.3
        if hilang:
            rrect_on(img, x, base - 40, x + 52, base, 10, (205, 200, 196), al * q)
            continue
        h *= 1 + (0.9 * keras if tet else 0.45 * keras if tet2 else 0)
        c = mix(accent, RED, keras * (1.0 if tet else 0.5 if tet2 else 0))
        rrect_on(img, x, base - h, x + 52, base, 12, c, al * q * clamp((q * 11 - i) / 2 + 0.3))
    _label11(img, 540, 1060 + dy, "nada rendah  ->  nada tinggi", MUTED, al * q, fsz=24)
    if patah > 0:
        rrect_on(img, x0 + 5 * 72 - 10, base - 190, x0 + 7 * 72 - 10, base + 8, 14, RED, al * patah * 0.12)
        _stiker11(img, x0 + 6 * 72 - 10, base - 230, "SEL RUSAK", al, tl - t_pt, bg=RED, fsz=24, rot=-4, tg=tg)
    # otak besar di bawah: saraf mengeras (garis menyala) mengisi kekosongan
    qo = esmooth(seg(tl, _t(N, "otak", dur), _t(N, "otak", dur) + 0.6))
    if qo > 0:
        cx, cy = 540, 1330 + dy
        _glow11(img, cx, cy, 250, mix(accent, WHITE, 0.5), al * qo * (0.3 + 0.4 * keras))
        D._ico5(img, "brain", cx, cy, 190, mix(accent, INK, 0.1), al * qo, tg, pulse=keras * (0.5 + 0.5 * math.sin(tg * 7)))
        _panah11(img, (x0 + 6 * 72 + 16, base + 40), (cx + 40, cy - 110), al * qo, clamp(qo * 1.3), MUTED, width=6, lengkung=-0.2)
        if keras > 0:
            for k in range(6):
                a = k * math.pi / 3 + tg * 0.8
                r0 = 150 + 30 * math.sin(tg * 5 + k)
                line_on(img, (cx + 60 * math.cos(a), cy + 50 * math.sin(a)),
                        (cx + r0 * math.cos(a), cy + r0 * 0.8 * math.sin(a)), (240, 170, 40), 5, al * keras)
            _stiker11(img, 280, 1190 + dy, "SARAF DIKERASKAN", al, tl - _t(N, "keras", dur), bg=accent, fsz=22, rot=-5, tg=tg)
    tt = tl - _t(N, "dengung", dur)
    if tt > 0:
        _gelom11(img, 180, 900, 1580 + dy, 18, 30, tg * 16, (230, 160, 30), 6, al * clamp(tt / 0.4))
        _stiker11(img, 800, 1560 + dy, "DENGUNG MENETAP", al, tt, bg=RED, fsz=28, rot=4, tg=tg)


_TANGGA = [(80, "40 jam"), (85, "12,5 jam"), (90, "4 jam"), (95, "75 mnt"), (100, "20 mnt")]


def sc_who43(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "who43"
    _hdr(img, sc, accent, tl, al)
    tt = tl - _t(N, "batas", dur)
    if tt <= 0:
        return
    # grafik tangga: tiap +3~5 dB waktu aman terpotong
    x0, base = 140, 1260 + dy
    names = ["batas", "tangga1", "tangga2", "tangga3", "seratus"]
    maxh = 390
    for i, (db_, jam) in enumerate(_TANGGA):
        tn = _t(N, names[i], dur)
        qq = eob(clamp((tl - tn) / 0.45), 1.6)
        if qq <= 0:
            continue
        x = x0 + i * 165
        jam_h = {0: 1.0, 1: 0.55, 2: 0.30, 3: 0.14, 4: 0.05}[i]
        h = maxh * jam_h * qq
        col = mix(GREEN, RED, i / 4)
        rrect_on(img, x, base - h, x + 120, base, 16, col, al)
        _label11(img, x + 60, base + 36, f"{db_} dB", INK, al * clamp(qq), fsz=24, name=FB)
        _label11(img, x + 60, base - h - 30, jam, mix(col, INK, 0.35), al * clamp(qq), fsz=24, name=FB)
    _label11(img, 540, base + 84, "waktu aman per minggu", MUTED, al, fsz=24)
    _stiker11(img, 330, 720 + dy, "80 dB = 40 JAM/MINGGU", al, tt, bg=GREEN, fsz=28, rot=-3, tg=tg)
    tt2 = tl - _t(N, "tangga1", dur)
    if tt2 > 0:
        _stiker11(img, 760, 800 + dy, "+3 dB = WAKTU SEPARUH", al, tt2, bg=AMBER, fsz=24, rot=4, tg=tg)
    tt = tl - _t(N, "earphone", dur)
    if tt > 0:
        _earphone43(img, 880, 1070 + dy - (1 - eob(clamp(tt / 0.5))) * 200, 1.0, al, tg=tg,
                    dentum=esmooth(seg(tl, _t(N, "seratus", dur), _t(N, "seratus", dur) + 0.3)))
    tt = tl - _t(N, "seratus", dur)
    if tt > 0:
        _stiker11(img, 540, 1500 + dy, "VOLUME PENUH = 100 dB", al, tt, bg=RED, fsz=30, rot=-3, tg=tg)
    tt = tl - _t(N, "menit", dur)
    if tt > 0:
        _label11(img, 540, 1590 + dy, "aman cuma 20 menit seminggu", RED, al * clamp(tt / 0.3), fsz=30, name=FB)


def sc_tips43(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "tips43"
    _hdr(img, sc, accent, tl, al)
    q = esmooth(seg(tl, _t(N, "vol", dur), _t(N, "vol", dur) + 0.5))
    if q <= 0.01:
        return
    # slider volume turun ke 60%
    y = 700 + dy
    t6 = _t(N, "enam", dur)
    v = 0.95 - 0.35 * esmooth(seg(tl, t6 - 0.5, t6 + 0.3))
    rrect_on(img, 180, y - 14, 900, y + 14, 14, mix(CREAM, INK, 0.15), al * q)
    rrect_on(img, 180, y - 14, 180 + 720 * v, y + 14, 14, mix(GREEN, RED, clamp((v - 0.6) / 0.35)), al * q)
    dot_on(img, 180 + 720 * v, y, 30, WHITE, al * q, outline=GELAP, width=4)
    _label11(img, 180 + 720 * v, y - 56, f"{int(round(v * 100))}%", INK, al * q, fsz=30, name=FB)
    _earphone43(img, 110, y, 0.55, al * q, tg=tg)
    tt = tl - t6
    if tt > 0:
        D._check5_on(img, 960, y, 30, "check", al, clamp(tt / 0.35), col=GREEN)
    tt = tl - _t(N, "jeda", dur)
    if tt > 0:
        _stiker11(img, 540, 800 + dy, "+ BERI TELINGA JEDA", al, tt, bg=GREEN, fsz=26, rot=-3, tg=tg)
    # kartu dokter THT + 4 tanda
    tt = tl - _t(N, "dokter", dur)
    if tt > 0:
        k = eob(clamp(tt / 0.45), 1.5)
        rrect_on(img, 100, 900 + dy + (1 - k) * 200, 980, 1640 + dy + (1 - k) * 200, 36, WHITE,
                 al * clamp(tt / 0.2), outline=mix(RED, WHITE, 0.4), width=4)
        yy = 960 + dy + (1 - k) * 200
        dot_on(img, 180, yy + 10, 40, mix(RED, WHITE, 0.8), al)
        rrect_on(img, 172, yy - 12, 188, yy + 32, 3, RED, al)
        rrect_on(img, 158, yy + 2, 202, yy + 18, 3, RED, al)
        paste_c(img, 560, yy + 10, "KE DOKTER THT BILA:", font(FB, 34), RED, al)
        tanda = [("t1", "berhari-hari tak hilang", "clock"), ("t2", "hanya di satu telinga", "eye"),
                 ("t3", "berdenyut seirama jantung", "heart"), ("t4", "disertai pusing berputar", "brain")]
        for i, (kk, txt, ik) in enumerate(tanda):
            ti = tl - _t(N, kk, dur)
            if ti <= 0:
                continue
            kx = eob(clamp(ti / 0.4), 1.6)
            y2 = yy + 140 + i * 132
            x_off = (1 - kx) * 500
            rrect_on(img, 150 + x_off, y2 - 52, 930 + x_off, y2 + 52, 26, mix(WHITE, RED, 0.06),
                     al * clamp(ti / 0.2), outline=mix(RED, WHITE, 0.7), width=2)
            if ik == "eye":
                _telinga43(img, 220 + x_off, y2, 0.26, al * clamp(ti / 0.2), tg)
            else:
                D._ico5(img, ik, 220 + x_off, y2, 34, RED, al * clamp(ti / 0.2), tg,
                        pulse=(0.5 + 0.5 * math.sin(tg * 6)) if ik == "heart" else 0.0)
            paste_c(img, 580 + x_off, y2, txt, font(FS, 30), INK, al * clamp(ti / 0.2))


def sc_rangkuman43(img, d, sc, tl, dur, tg, accent, al, dy):
    N = "rangkuman43"
    _hdr(img, sc, accent, tl, al)
    items = [("s1", "NGING SEBENTAR = NORMAL", "sel rambut salah tembak", GREEN),
             ("s2", "DENGUNG = PERINGATAN", "setelah konser / earphone", AMBER),
             ("s3", "SEL RAMBUT TAK TUMBUH", "jaga volume 60%", RED)]
    for i, (kk, a_, b_, col) in enumerate(items):
        tt = tl - _t(N, kk, dur)
        if tt <= 0:
            continue
        k = eob(clamp(tt / 0.4), 1.8)
        y = 800 + i * 190 + dy
        a = al * clamp(tt / 0.15)
        rrect_on(img, 110, y - 74, 970, y + 74, 32, mix(WHITE, col, 0.07), a, outline=mix(col, WHITE, 0.45), width=3)
        dot_on(img, 195, y, 46 * k, col, a)
        paste_c(img, 195, y, str(i + 1), font(FB, 40), WHITE, a)
        paste_c(img, 590, y - 20, a_, font(FB, 32), INK, a, scale=0.85 + 0.15 * k)
        paste_c(img, 590, y + 26, b_, font(FS, 24), MUTED, a)
        _partikel11(img, 195, y, tt, col, al, n=8, jarak=70, seed=i)
    tt = tl - _t(N, "kirim", dur)
    if tt > 0:
        _stiker11(img, 450, 1420 + dy, "KIRIM KE TEMAN", al, tt, bg=accent, fsz=40, rot=-4, tg=tg)
        _label11(img, 450, 1510 + dy, "yang earphone-nya selalu kencang", MUTED, al * clamp(tt / 0.3), fsz=26)
        _earphone43(img, 860, 1460 + dy, 0.9, al * clamp(tt / 0.3), tg=tg, dentum=1.0)


VISUALS43 = {
    "intro_kuping43": sc_intro_kuping43, "koklea43": sc_koklea43, "salah43": sc_salah43,
    "hening43": sc_hening43, "konser43": sc_konser43, "otak43": sc_otak43, "who43": sc_who43,
    "tips43": sc_tips43, "rangkuman43": sc_rangkuman43,
}
