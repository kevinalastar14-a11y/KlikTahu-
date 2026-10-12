"""
script_kliktahu.py — naskah & arahan visual Short KlikTahu.

Seluruh teks yang diucapkan (voice-over) dan yang tampil di layar hidup di
file ini. Engine tidak menyimpan teks apa pun di dalam kode, jadi naskah bisa
diganti tanpa menyentuh mesin render.

BEAT: satu unit cerita = satu kalimat VO + satu komposisi visual.

Aturan yang divalidasi engine:
  * `lines` (teks di layar) harus memuat kata-kata VO mulai dari indeks
    `vo_from` sampai habis. Kata ke-i di layar = kata ke-(vo_from + i) di VO.
    Ini yang membuat sorotan kata selalu jatuh tepat saat kata itu diucapkan.
"""

BRAND = "KLIKTAHU"
TAGLINE = "TONTON. PAHAM. DALAM 1 MENIT."
CTA = "Ikuti untuk tips berikutnya"
SAVE_HINT = "SIMPAN  •  TONTON ULANG"

# Ukuran kanvas (YouTube Shorts: 9:16)
WIDTH, HEIGHT, FPS = 1080, 1920, 60

# Palet
BG_DEEP = (7, 9, 18)
BG_MID = (13, 11, 30)
BG_WARM = (26, 14, 38)
INK = (8, 10, 22)
WHITE = (240, 244, 255)
MUTED = (150, 160, 190)
CYAN = (86, 226, 255)
VIOLET = (139, 108, 255)
AMBER = (255, 190, 60)
RED = (255, 92, 110)
GREEN = (110, 240, 170)

# Nama suara edge-tts untuk produksi (voice_over.py / GitHub Actions).
# VO video yang disertakan di repo dibuat dengan suara narator pria Indonesia.
VOICE_ID = "id-ID-ArdiNeural"
VOICE_FALLBACK = "id-ID-GadisNeural"

# Judul untuk metadata upload (dipakai tools/youtube_upload.py)
YOUTUBE_TITLE = "3 Detik Pertama Menentukan Video Kamu Ditonton atau Di-skip"
YOUTUBE_DESCRIPTION = """Kenapa video kamu di-skip di detik ke-3?

Bukan karena kontennya jelek — tapi karena videonya membosankan sejak frame pertama.
Tiga aturan yang dipakai editor profesional:

1. Gerakkan sesuatu di setiap detik.
2. Satu ide untuk satu frame.
3. Kejutkan sebelum penonton bosan.

Retention bukan keberuntungan. Retention adalah desain.

Follow @KlikTahu untuk tips editing 1 menit setiap minggu.
#shorts #editing #youtubeshorts #retention #videoediting
"""

# --------------------------------------------------------------------------- #
#  BEAT — inti video
# --------------------------------------------------------------------------- #
#  key       : nama file narasi (narration/01_hook.mp3)
#  scene     : komposisi visual (lihat scene_* di cinematic_engine.py)
#  vo        : kalimat yang diucapkan
#  lines     : teks di layar; jumlah kata harus sama dengan VO
#  vo_from   : kata VO pertama yang ditampilkan (bila awal kalimat tidak perlu tampil)
#  persist   : kata yang tetap menyala setelah diucapkan (penekanan)
#  strike    : kata yang dicoret (visual "dibuang")
#  anchor_y  : titik pusat vertikal blok teks
BEATS = [
    dict(
        key="hook",
        chapter="HOOK",
        scene="countdown",
        vo="Tiga detik pertama menentukan segalanya.",
        lines=["TIGA DETIK", "PERTAMA", "MENENTUKAN", "SEGALANYA"],
        persist=["SEGALANYA"],
        size=98,
        anchor_y=972,
        max_height=580,
        accent_color=AMBER,
        lead_in=0.30,
        tail=0.45,
        sfx=("impact_soft", "tick_tick"),
    ),
    dict(
        key="choice",
        chapter="HOOK",
        scene="choice",
        vo="Ditonton atau di-skip?",
        lines=["DITONTON,", "ATAU  DI-SKIP."],
        persist=["DITONTON,"],
        strike=["DI-SKIP."],
        size=124,
        anchor_y=1010,
        accent_color=CYAN,
        lead_in=0.18,
        tail=0.40,
        sfx=("swipe",),
    ),
    dict(
        key="pain",
        chapter="MASALAH",
        scene="statement",
        vo="Masalahnya bukan kontenmu jelek.",
        lines=["MASALAHNYA", "BUKAN KONTENMU", "JELEK."],
        persist=["BUKAN"],
        size=104,
        anchor_y=950,
        accent_color=RED,
        lead_in=0.16,
        tail=0.35,
        sfx=("thud",),
    ),
    dict(
        key="boring",
        chapter="MASALAH",
        scene="retention",
        vo="Masalahnya, videomu membosankan sejak frame pertama.",
        lines=["MEMBOSANKAN", "SEJAK FRAME", "PERTAMA."],
        vo_from=2,
        persist=["MEMBOSANKAN"],
        size=98,
        anchor_y=1015,
        accent_color=RED,
        lead_in=0.22,
        tail=0.75,
        sfx=("riser_short",),
    ),
    dict(
        key="rule1",
        chapter="SOLUSI",
        scene="rule",
        rule_no="01",
        vo="Satu. Gerakkan sesuatu di setiap detik.",
        lines=["GERAKKAN", "SESUATU", "DI SETIAP DETIK."],
        vo_from=1,
        persist=["SESUATU"],
        size=100,
        anchor_y=1000,
        accent_color=CYAN,
        lead_in=0.20,
        tail=0.60,
        sfx=("pop",),
    ),
    dict(
        key="rule2",
        chapter="SOLUSI",
        scene="rule",
        rule_no="02",
        vo="Dua. Satu ide untuk satu frame.",
        lines=["SATU IDE", "UNTUK SATU", "FRAME."],
        vo_from=1,
        persist=["FRAME."],
        size=104,
        anchor_y=1000,
        accent_color=CYAN,
        lead_in=0.20,
        tail=0.60,
        sfx=("pop",),
    ),
    dict(
        key="rule3",
        chapter="SOLUSI",
        scene="rule",
        rule_no="03",
        vo="Tiga. Kejutkan sebelum penonton bosan.",
        lines=["KEJUTKAN", "SEBELUM PENONTON", "BOSAN."],
        vo_from=1,
        persist=["KEJUTKAN"],
        size=100,
        anchor_y=1015,
        accent_color=CYAN,
        lead_in=0.20,
        tail=0.60,
        sfx=("pop",),
    ),
    dict(
        key="notluck",
        chapter="KUNCI",
        scene="statement",
        vo="Retention bukan keberuntungan.",
        lines=["RETENTION BUKAN", "KEBERUNTUNGAN."],
        persist=["RETENTION"],
        strike=["KEBERUNTUNGAN."],
        size=112,
        anchor_y=940,
        accent_color=RED,
        lead_in=0.18,
        tail=0.55,
        sfx=("riser",),
    ),
    dict(
        key="climax",
        chapter="KUNCI",
        scene="climax",
        vo="Retention adalah desain.",
        lines=["RETENTION", "ADALAH DESAIN."],
        persist=["DESAIN."],
        size=140,
        anchor_y=940,
        accent_color=AMBER,
        lead_in=0.10,
        tail=0.90,
        sfx=("impact", "sub_drop"),
    ),
    dict(
        key="outro",
        chapter="PENUTUP",
        scene="outro",
        vo="Simpan video ini, dan tonton ulang dari awal.",
        lines=["SIMPAN VIDEO INI,", "DAN TONTON ULANG", "DARI AWAL."],
        persist=["SIMPAN"],
        size=96,
        anchor_y=1020,
        accent_color=AMBER,
        lead_in=0.22,
        tail=3.10,
        sfx=("whoosh_soft", "pop"),
    ),
]

# Warna aksen per bab (dipakai tools/editor & validasi kontras)
CHAPTER_COLORS = {
    "HOOK": CYAN,
    "MASALAH": RED,
    "SOLUSI": CYAN,
    "KUNCI": AMBER,
    "PENUTUP": AMBER,
}
