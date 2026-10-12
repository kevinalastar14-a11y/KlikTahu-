"""
cinematic_engine.py — KlikTahu Video Engine (YouTube Shorts, 1080x1920 @ 60 fps).

Alur:
    naskah (script_kliktahu.py) + voice-over (narration/) -> timeline
    timeline -> frame (latar hidup, grafis, tipografi sinkron suara)
    frame -> ffmpeg (x264, bitrate dihitung dari target ukuran file) -> mp4

Contoh pemakaian:
    python cinematic_engine.py --still 2.4,9.0 --still-out build/stills
    python cinematic_engine.py --render --target-mb 215
    python cinematic_engine.py --render --preview            # cepat, untuk cek gerak
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

import audio_design as ad
import visuals as vs
from script_kliktahu import (AMBER, BEATS, BG_DEEP, BG_MID, BG_WARM, BRAND,
                             CHAPTER_COLORS, CTA, CYAN, FPS, HEIGHT, MUTED, RED,
                             SAVE_HINT, TAGLINE, VIOLET, WHITE, WIDTH,
                             YOUTUBE_DESCRIPTION, YOUTUBE_TITLE)

ROOT = Path(__file__).resolve().parent
NARRATION_DIR = ROOT / "narration"
BUILD_DIR = ROOT / "build"

LOW_W, LOW_H = WIDTH // 3, HEIGHT // 3          # layer lembut (aurora) dirender kecil
TRANSITION = 0.34                                # durasi transisi antar-beat (detik)

TOKEN_RE = re.compile(r"\S+")
NORM_RE = re.compile(r"[^0-9a-z\-]")


# --------------------------------------------------------------------------- #
#  Timeline
# --------------------------------------------------------------------------- #
def norm_token(s: str) -> str:
    return NORM_RE.sub("", s.lower())


@dataclass
class Beat:
    spec: dict
    index: int
    vo: str
    vo_tokens: list[str]
    screen_words: list[str]
    vo_clip: np.ndarray | None
    vo_dur: float
    lead_in: float
    tail: float
    word_times: list[float]
    start: float = 0.0
    dur: float = 0.0
    estimated: bool = False

    @property
    def key(self) -> str:
        return self.spec["key"]

    @property
    def accent(self) -> tuple[int, int, int]:
        return tuple(self.spec.get("accent_color", CYAN))

    @property
    def text_start(self) -> float:
        return self.lead_in

    @property
    def vo_from(self) -> int:
        """Indeks kata VO yang menjadi kata pertama di layar."""
        return int(self.spec.get("vo_from", 0))

    def word_onset(self, i: int) -> float:
        """Waktu munculnya kata ke-i di LAYAR (dipetakan ke kata VO-nya)."""
        return self.lead_in + self.word_times[self.vo_from + i]

    def active_word(self, t_local: float) -> int | None:
        """Indeks kata LAYAR yang sedang diucapkan pada waktu lokal `t`."""
        idx = None
        for i, onset in enumerate(self.word_times):
            if t_local >= self.lead_in + onset - 0.02:
                idx = i
            else:
                break
        if idx is None:
            return None
        return idx - self.vo_from if idx >= self.vo_from else None


def estimate_duration(text: str) -> float:
    """Perkiraan durasi ucap (chars/detik) saat narasi belum tersedia."""
    return max(1.6, len(text) / 14.2 + 0.35)


def distribute_words(tokens: list[str], dur: float, lead: float = 0.06) -> list[float]:
    """Bagi durasi ucap ke tiap kata menurut panjang karakternya."""
    weights = np.array([len(t) + 2.2 for t in tokens], dtype=np.float64)
    weights /= weights.sum()
    spans = weights * max(0.35, dur - lead)
    return list(np.cumsum(spans) - spans + lead)


def load_narration(beats: list[Beat], verbose: bool = True) -> None:
    """Ambil voice-over dari folder narration/ (mp3/wav) bila ada."""
    found = 0
    for b in beats:
        path = None
        for ext in (".mp3", ".wav", ".m4a", ".opus"):
            p = NARRATION_DIR / f"{b.index + 1:02d}_{b.key}{ext}"
            if p.exists():
                path = p
                break
        if path is None:
            b.vo_dur = estimate_duration(b.vo)
            b.estimated = True
            b.vo_clip = None
            b.word_times = distribute_words(b.vo_tokens, b.vo_dur)
            continue
        audio = ad.decode_audio(str(path))
        audio = ad.trim_silence(audio)
        b.vo_clip = ad.normalize_voice(ad.fade(ad.eq_voice(audio), 6, 16))
        b.vo_dur = len(b.vo_clip) / ad.SR
        b.estimated = False
        found += 1

        timing = path.with_suffix(".json")
        if timing.exists():
            data = json.loads(timing.read_text())
            words = data.get("words") or []
            if len(words) == len(b.vo_tokens):
                b.word_times = [max(0.0, w["offset_ms"] / 1000.0) for w in words]
                continue
        b.word_times = distribute_words(b.vo_tokens, b.vo_dur)
    if verbose:
        print(f"[timeline] narasi ditemukan: {found}/{len(beats)}"
              + ("  (sisanya pakai estimasi durasi)" if found < len(beats) else ""))


def build_timeline(verbose: bool = True) -> list[Beat]:
    beats: list[Beat] = []
    for i, spec in enumerate(BEATS):
        vo = spec["vo"]
        tokens = TOKEN_RE.findall(vo)
        screen = [w for line in spec["lines"] for w in TOKEN_RE.findall(line)]
        vo_from = int(spec.get("vo_from", 0))
        expect = tokens[vo_from: vo_from + len(screen)]
        if len(expect) != len(screen) or any(
                norm_token(a) != norm_token(b) for a, b in zip(expect, screen)):
            raise SystemExit(
                f"[naskah] beat '{spec['key']}': teks layar tidak cocok dengan VO.\n"
                f"  layar : {screen}\n  VO    : {tokens[vo_from:vo_from + len(screen)]}\n"
                "  Pastikan jumlah kata sama (mulai dari indeks vo_from).")
        beats.append(Beat(
            spec=spec, index=i, vo=vo, vo_tokens=tokens, screen_words=screen,
            vo_clip=None, vo_dur=estimate_duration(vo),
            lead_in=float(spec.get("lead_in", 0.2)),
            tail=float(spec.get("tail", 0.5)),
            word_times=[],
        ))

    load_narration(beats, verbose=verbose)

    t = 0.0
    for b in beats:
        b.dur = b.lead_in + b.vo_dur + b.tail
        b.start = t
        t += b.dur
    if verbose:
        print(f"[timeline] total {t:.2f} detik, {len(beats)} beat, {FPS} fps")
    return beats


def timeline_duration(beats: list[Beat]) -> float:
    return beats[-1].start + beats[-1].dur


def beat_at(beats: list[Beat], starts: list[float], t: float) -> Beat:
    i = bisect.bisect_right(starts, t) - 1
    return beats[max(0, min(i, len(beats) - 1))]


# --------------------------------------------------------------------------- #
#  Konteks render
# --------------------------------------------------------------------------- #
@dataclass
class Ctx:
    beat: Beat
    beats: list[Beat]
    t_local: float
    t_global: float
    total: float
    text_alpha: float = 1.0
    shake: tuple[float, float] = (0.0, 0.0)
    text_scale: float = 1.0
    extras: dict = field(default_factory=dict)


# --------------------------------------------------------------------------- #
#  Renderer
# --------------------------------------------------------------------------- #
class Renderer:
    """
    Penyusun frame.

    Falsafah kinerja: semua yang mahal (gradien besar, blur, sprite halo) dibuat
    SEKALI saat inisialisasi. Saat render, yang terjadi hanya menggambar bentuk
    dan menempelkan sprite — operasi yang biayanya sebanding dengan luas sprite,
    bukan luas kanvas.
    """

    def __init__(self, beats: list[Beat], verbose: bool = True):
        self.beats = beats
        self.starts = [b.start for b in beats]
        self.total = timeline_duration(beats)
        self.verbose = verbose

        self.bg_static = self._build_static_bg()
        self.blobs = self._build_blobs()
        self.bokeh = self._build_bokeh()
        self.motes = self._build_motes()
        self.brand = vs.tracked_sprite(BRAND, vs.font("Bold", 34), (188, 202, 232), tracking=11)
        self.progress_strip = self._build_progress_strip()
        self.halos = self._build_halos()
        self.bursts = self._build_bursts()
        self.solids = {c: Image.new("RGB", (WIDTH, HEIGHT), c)
                       for c in (AMBER, CYAN, RED, (255, 255, 255))}
        self.chip_cache: dict[str, Image.Image] = {}

        self.blocks: list[vs.WordBlock] = []
        for b in beats:
            self.blocks.append(vs.WordBlock(
                b.spec["lines"],
                anchor=(WIDTH / 2, b.spec.get("anchor_y", 985)),
                max_width=900,
                max_height=b.spec.get("max_height", 640),
                weight="Black",
                size=b.spec.get("size", 104),
                min_size=44,
                color=WHITE,
                accent=b.accent,
                align=b.spec.get("align", "center"),
            ))

        if verbose:
            print(f"[render] kanvas {WIDTH}x{HEIGHT} @ {FPS}fps — "
                  f"{len(self.blobs)} blob, {len(self.bokeh)} bokeh, "
                  f"{len(self.motes['x'])} partikel, {len(self.halos)} sprite halo")

    # ------------------------------------------------------------- latar statis
    def _build_static_bg(self) -> Image.Image:
        bg = vs.vertical_gradient((WIDTH, HEIGHT), [
            (0.00, BG_DEEP), (0.42, BG_MID), (0.72, BG_WARM), (1.00, BG_DEEP),
        ]).convert("RGBA")
        bg.alpha_composite(vs.dotted_grid((WIDTH, HEIGHT), step=54, radius=1.5,
                                          color=(150, 185, 255), alpha=22))
        bg.alpha_composite(vs.vignette((WIDTH, HEIGHT), strength=0.72, power=2.4))
        d = ImageDraw.Draw(bg)
        d.line([(0, int(HEIGHT * 0.30)), (WIDTH, int(HEIGHT * 0.30))],
               fill=(120, 150, 220, 16), width=2)
        # scrim bawah dibakar langsung ke latar (statis, jadi tidak perlu per frame)
        scrim = np.zeros((520, WIDTH, 4), dtype=np.uint8)
        scrim[..., 0], scrim[..., 1], scrim[..., 2] = BG_DEEP
        scrim[..., 3] = (np.linspace(0, 1, 520) ** 1.7 * 215).astype(np.uint8)[:, None]
        scrim_img = Image.fromarray(scrim, "RGBA")
        bg.alpha_composite(scrim_img, (0, HEIGHT - 520))
        return bg.convert("RGB")

    # ------------------------------------------------------------------ aurora
    def _build_blobs(self):
        """Cahaya latar: sprite radial native (ditempel langsung, tanpa resize)."""
        specs = [
            (VIOLET, 620, 0.62, 0.62, 0.055, 0.00, 0.42),
            (CYAN, 470, 0.44, 0.92, 0.041, 1.70, 0.34),
            ((190, 70, 160), 430, 0.94, 0.28, 0.033, 3.10, 0.30),
            (AMBER, 360, 0.20, 0.36, 0.028, 4.60, 0.26),
        ]
        out = []
        for color, radius, fx, cy, speed, phase, alpha in specs:
            sprite = vs.radial_glow((radius * 2, int(radius * 2.1)), color,
                                    power=2.7, peak=1.0, quality=3)
            out.append(dict(color=color, sprite=sprite,
                            cx=WIDTH * fx, cy=HEIGHT * cy,
                            ax=WIDTH * 0.17, ay=HEIGHT * 0.06,
                            speed=speed, phase=phase, alpha=alpha))
        return out

    def draw_aurora(self, frame: Image.Image, t: float) -> None:
        for b in self.blobs:
            x = b["cx"] + math.sin(t * b["speed"] + b["phase"]) * b["ax"]
            y = b["cy"] + math.cos(t * b["speed"] * 0.77 + b["phase"]) * b["ay"]
            a = b["alpha"] * (0.78 + 0.22 * math.sin(t * 0.9 + b["phase"] * 2))
            spr = b["sprite"].copy()
            spr.putalpha(spr.getchannel("A").point(lambda v, k=a: int(v * k)))
            frame.paste(spr, (int(x - spr.width / 2), int(y - spr.height / 2)), spr)

    def _build_bokeh(self):
        rng = np.random.default_rng(4242)
        out = []
        for _ in range(10):
            r = int(rng.integers(40, 120))
            color = [(150, 190, 255), (190, 160, 255), (255, 210, 160)][int(rng.integers(0, 3))]
            out.append(dict(sprite=vs.radial_glow((r * 3, r * 3), color, power=1.8,
                                                  peak=1.0, quality=2),
                            x=float(rng.uniform(0, WIDTH)), y=float(rng.uniform(0, HEIGHT)),
                            vy=float(rng.uniform(10, 30)), vx=float(rng.uniform(-8, 8)),
                            ph=float(rng.uniform(0, 6.28)), a=float(rng.uniform(0.05, 0.13))))
        return out

    def draw_bokeh(self, frame: Image.Image, t: float) -> None:
        for k in self.bokeh:
            y = (k["y"] - k["vy"] * t) % (HEIGHT + 400) - 200
            x = (k["x"] + k["vx"] * t + 60 * math.sin(t * 0.4 + k["ph"])) % (WIDTH + 300) - 150
            spr = k["sprite"].copy()
            spr.putalpha(spr.getchannel("A").point(lambda v, a=k["a"]: int(v * a)))
            frame.paste(spr, (int(x), int(y)), spr)

    def _build_motes(self):
        rng = np.random.default_rng(2026)
        n = 64
        return dict(
            x=rng.uniform(0, WIDTH, n).astype(np.float32),
            y=rng.uniform(0, HEIGHT, n).astype(np.float32),
            r=rng.uniform(1.4, 4.6, n).astype(np.float32),
            vy=rng.uniform(16, 52, n).astype(np.float32),
            ph=rng.uniform(0, 6.28, n).astype(np.float32),
            amp=rng.uniform(10, 34, n).astype(np.float32),
            a=rng.uniform(28, 96, n).astype(np.float32),
        )

    def overlay_motes(self, ov: Image.Image, t: float) -> None:
        d = ImageDraw.Draw(ov)
        p = self.motes
        ys = (p["y"] - p["vy"] * t) % (HEIGHT + 120) - 60
        xs = p["x"] + p["amp"] * np.sin(t * 0.55 + p["ph"])
        for i in range(len(xs)):
            r = float(p["r"][i])
            a = int(p["a"][i] * (0.55 + 0.45 * math.sin(t * 1.3 + p["ph"][i])))
            x, y = float(xs[i]), float(ys[i])
            d.ellipse([x - r, y - r, x + r, y + r], fill=(226, 236, 255, max(0, a)))

    def _build_progress_strip(self) -> Image.Image:
        arr = np.zeros((12, WIDTH, 4), dtype=np.uint8)
        t = np.linspace(0, 1, WIDTH)
        c0, c1 = np.array(CYAN, dtype=np.float64), np.array(AMBER, dtype=np.float64)
        col = c0[None, :] + (c1 - c0)[None, :] * t[:, None]
        arr[:, :, :3] = col.astype(np.uint8)[None, :, :]
        arr[..., 3] = 255
        arr[:4, :, 3] = 0
        arr[8:, :, 3] = 0
        return Image.fromarray(arr, "RGBA")

    # ------------------------------------------------------- sprite halo (init)
    def _build_halos(self) -> dict:
        """Semua glow dirender sekali di sini — per frame hanya ditempel."""
        halos = {}
        R = 126
        halos["ring"] = vs.prerender_glow(
            (2 * R + 150, 2 * R + 150),
            lambda d, k: d.ellipse([75 * k, 75 * k, (2 * R + 75) * k, (2 * R + 75) * k],
                                   outline=AMBER + (255,), width=max(2, int(10 * k))),
            blur=30, gain=0.85)
        halos["disc_play"] = vs.radial_glow((560, 560), CYAN, power=2.1, peak=1.0, quality=3)
        halos["disc_badge"] = vs.radial_glow((700, 700), CYAN, power=2.1, peak=1.0, quality=3)
        for name, color in (("amb_red", RED), ("amb_amber", AMBER), ("amb_cyan", CYAN)):
            halos[name] = vs.radial_glow((980, 520), color, power=1.7, peak=1.0,
                                         scale=(1.0, 0.58), quality=3)
        return halos

    def _build_bursts(self):
        """Ledakan sinar untuk klimaks: beberapa varian skala (tanpa blur runtime)."""
        rng = np.random.default_rng(99)
        base = np.zeros((760, 760, 4), dtype=np.float32)
        ys, xs = np.mgrid[0:760, 0:760]
        cx = cy = 379.5
        dx, dy = (xs - cx) / 380.0, (ys - cy) / 380.0
        r = np.sqrt(dx ** 2 + dy ** 2)
        th = np.arctan2(dy, dx)
        spokes = (0.42 + 0.58 * np.clip(np.cos(th * 9 + rng.uniform(0, 3)), 0, 1) ** 3)
        radial = np.clip(1.0 - r, 0, 1) ** 1.5
        a = np.clip(spokes * radial, 0, 1)
        base[..., 0], base[..., 1], base[..., 2] = AMBER
        base[..., 3] = a * 190
        img = Image.fromarray(base.astype(np.uint8), "RGBA")
        return [img.resize((int(1100 * s), int(1100 * s)), Image.BICUBIC)
                for s in (0.55, 0.75, 1.0, 1.3, 1.7)]

    # ------------------------------------------------------------------- HUD
    def draw_hud(self, ov: Image.Image, t: float, ctx: Ctx) -> None:
        prog = vs.clamp(t / max(0.01, self.total))
        w = int(WIDTH * prog)
        if w > 6:
            bar = self.progress_strip.crop((0, 0, w, 12))
            ov.paste(bar, (0, 46), bar)
        alpha = 150 if ctx.beat.key != "outro" else 195
        sp = self.brand.copy()
        sp.putalpha(sp.getchannel("A").point(lambda v, a=alpha: int(v * a / 255)))
        ov.paste(sp, ((WIDTH - self.brand.width) // 2, 84), sp)
        chapter = ctx.beat.spec.get("chapter")
        if chapter:
            chip = self.chapter_chip(chapter)
            ov.paste(chip, (52, 168), chip)

    def chapter_chip(self, label: str) -> Image.Image:
        if label in self.chip_cache:
            return self.chip_cache[label]
        f = vs.font("Bold", 26)
        w, h = int(vs.tracked_width(label, f, 5.0)) + 64, 56
        btn = Image.new("RGBA", (w + 14, h + 14), (0, 0, 0, 0))
        d = ImageDraw.Draw(btn)
        accent = CHAPTER_COLORS.get(label, (120, 150, 220))
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2,
                            fill=(18, 22, 40, 178), outline=accent + (120,), width=2)
        d.ellipse([17, h // 2 - 5, 27, h // 2 + 5], fill=accent + (235,))
        sprite = vs.tracked_sprite(label, f, (214, 226, 248), tracking=5.0)
        btn.paste(sprite, ((w - sprite.width) // 2 + 8, (h - sprite.height) // 2), sprite)
        self.chip_cache[label] = btn
        return btn

    def label(self, text: str, size: int = 30, color=MUTED, tracking: float = 7.0,
              weight: str = "Semi") -> Image.Image:
        key = f"{text}|{size}|{color}|{tracking}|{weight}"
        if key not in self.chip_cache:
            self.chip_cache[key] = vs.tracked_sprite(text, vs.font(weight, size), color, tracking)
        return self.chip_cache[key]

    # ---------------------------------------------------------------- scenes
    def scene_graphics(self, ov: Image.Image, ctx: Ctx) -> None:
        name = ctx.beat.spec["scene"]
        fn = getattr(self, f"scene_{name}", None)
        if fn is None:
            raise SystemExit(f"[scene] tipe scene tidak dikenal: {name}")
        fn(ov, ctx)

    # -- 1. hook: hitungan mundur --------------------------------------- #
    def scene_countdown(self, ov: Image.Image, ctx: Ctx) -> None:
        t = ctx.t_local
        cx, cy, R = WIDTH / 2, 462, 126
        draw_t = vs.norm(t, 0.05, 0.95)
        fade = 1.0 - vs.norm(t, 0.78, 1.20)
        d = ImageDraw.Draw(ov)
        if fade > 0.01:
            halo = self.halos["ring"].copy()
            halo.putalpha(halo.getchannel("A").point(
                lambda v, k=fade * min(1.0, 0.25 + draw_t): int(v * k)))
            ov.paste(halo, (int(cx - halo.width / 2), int(cy - halo.height / 2)), halo)
            d.ellipse([cx - R, cy - R, cx + R, cy + R],
                      outline=(255, 255, 255, int(40 * fade)), width=3)
            d.arc([cx - R, cy - R, cx + R, cy + R], start=-90,
                  end=-90 + 360 * vs.ease_out_cubic(draw_t),
                  fill=AMBER + (int(255 * fade),), width=10)
            ang = -90 + 360 * vs.ease_out_cubic(draw_t)
            dx, dy = cx + R * math.cos(math.radians(ang)), cy + R * math.sin(math.radians(ang))
            d.ellipse([dx - 13, dy - 13, dx + 13, dy + 13], fill=AMBER + (int(255 * fade),))
        num_fade = 1.0 - vs.norm(t, 0.74, 1.08)
        if num_fade > 0.01:
            sp = self.label("3", 196, WHITE, 0, "Black")
            sc = 1.0 + 0.42 * (1 - vs.ease_out_elastic(vs.norm(t, 0.04, 0.78)))
            sc *= 1.0 + 0.16 * vs.norm(t, 0.74, 1.08)
            sp = sp.resize((max(2, int(sp.width * sc)), max(2, int(sp.height * sc))), Image.BILINEAR)
            sp = sp.copy()
            sp.putalpha(sp.getchannel("A").point(lambda v, a=num_fade: int(v * a)))
            ov.paste(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2 - 6)), sp)
        scan = int(vs.ease_in_out_cubic(vs.norm(t, 0.0, 1.5)) * HEIGHT)
        d.line([(0, scan), (WIDTH, scan)], fill=(150, 220, 255, 26), width=2)
        d.line([(0, scan - 8), (WIDTH, scan - 8)], fill=(150, 220, 255, 10), width=10)

    # -- 2. pilihan: ditonton vs di-skip --------------------------------- #
    def scene_choice(self, ov: Image.Image, ctx: Ctx) -> None:
        t = ctx.t_local
        cx, cy = WIDTH / 2, 470
        d = ImageDraw.Draw(ov)
        swipe = vs.ease_in_out_cubic(vs.norm(t, 1.02, 1.64))
        if swipe < 0.999:
            a = int(255 * (1 - swipe))
            slide, r = int(swipe * 430), 88
            halo = self.halos["disc_play"].copy()
            halo.putalpha(halo.getchannel("A").point(lambda v, k=(1 - swipe) * 0.85: int(v * k)))
            ov.paste(halo, (int(cx - halo.width / 2 + slide), int(cy - halo.height / 2)), halo)
            d.ellipse([cx - r + slide, cy - r, cx + r + slide, cy + r],
                      fill=(16, 26, 48, int(215 * (1 - swipe))))
            d.ellipse([cx - r + slide, cy - r, cx + r + slide, cy + r],
                      outline=CYAN + (a,), width=6)
            d.polygon([(cx - 24 + slide, cy - 36), (cx - 24 + slide, cy + 36),
                       (cx + 40 + slide, cy)], fill=CYAN + (a,))
        if 0.05 < swipe < 0.999:
            for i in range(5):
                yy = cy - 56 + i * 28
                x0 = cx + 130 + i * 22
                d.line([(x0, yy), (x0 + 80 + 280 * swipe, yy)],
                       fill=(220, 235, 255, int(85 * (1 - swipe))), width=4)
        if t > 1.5:
            a = int(235 * vs.norm(t, 1.5, 1.85))
            for k in range(2):
                ox = cx + 34 + k * 92
                d.line([(ox - 32, cy - 42), (ox + 18, cy), (ox - 32, cy + 42)],
                       fill=(255, 105, 120, a), width=14, joint="curve")
        bx0, bx1, by = 130, 950, 664
        drain = vs.ease_in_out_cubic(vs.norm(t, 0.85, 2.35))
        d.rounded_rectangle([bx0, by, bx1, by + 20], radius=10, fill=(255, 255, 255, 26))
        w = int((bx1 - bx0) * (1 - 0.94 * drain))
        if w > 6:
            col = vs.mix_rgb(CYAN, RED, drain)
            d.rounded_rectangle([bx0, by, bx0 + w, by + 20], radius=10, fill=col + (240,))
        ov.paste(self.label("WATCH TIME", 24, (150, 172, 205), 6), (bx0, by - 46))

    # -- 3. pernyataan minimalis ----------------------------------------- #
    def scene_statement(self, ov: Image.Image, ctx: Ctx) -> None:
        t = ctx.t_local
        accent = ctx.beat.accent
        d = ImageDraw.Draw(ov)
        block = self.blocks[ctx.beat.index]
        half = block.total_h / 2 + 40
        p = vs.ease_out_expo(vs.norm(t, 0.02, 0.62))
        d.rounded_rectangle([58, 940 - half * p, 72, 940 + half * p], radius=7,
                            fill=accent + (215,))
        key = "amb_red" if accent == RED else ("amb_amber" if accent == AMBER else "amb_cyan")
        halo = self.halos[key].copy()
        halo.putalpha(halo.getchannel("A").point(lambda v, k=0.42 * p + 0.20: int(v * k)))
        ov.paste(halo, (int(WIDTH / 2 - halo.width / 2), int(940 - halo.height / 2)), halo)

    # -- 4. kurva retention ---------------------------------------------- #
    def scene_retention(self, ov: Image.Image, ctx: Ctx) -> None:
        t = ctx.t_local
        d = ImageDraw.Draw(ov)
        px0, py0, px1, py1 = 120, 270, 960, 730
        x0, y0, x1, y1 = 168, 340, 912, 690
        d.rounded_rectangle([px0, py0, px1, py1], radius=30, fill=(12, 15, 30, 178),
                            outline=(120, 150, 220, 70), width=2)
        d.line([(x0 - 8, y0 - 30), (x0 - 8, y1)], fill=(120, 150, 220, 95), width=2)
        d.line([(x0 - 8, y1), (x1, y1)], fill=(120, 150, 220, 95), width=2)
        bx = x0 + 152
        d.rectangle([x0, y0 - 30, bx, y1], fill=(255, 90, 110, 30))
        for yy in range(y0 - 24, y1, 46):
            d.line([(x0, yy), (bx, yy)], fill=(255, 90, 110, 26), width=18)
        seg1 = vs.bezier((x0, y0), (x0 + 54, y0 + 8), (x0 + 108, y1 - 66), (bx, y1 - 104), 42)
        seg2 = vs.bezier((bx, y1 - 104), (bx + 180, y1 - 74), (x1 - 150, y1 - 10), (x1, y1 - 4), 42)
        pts = seg1 + seg2
        cut = int(vs.ease_out_cubic(vs.norm(t, 0.25, 1.95)) * len(pts))
        for i in range(cut, len(pts), 3):
            d.ellipse([pts[i][0] - 2, pts[i][1] - 2, pts[i][0] + 2, pts[i][1] + 2],
                      fill=(150, 175, 220, 60))
        if cut > 2:
            d.line(pts[:cut], fill=CYAN + (255,), width=7, joint="curve")
            mx, my = pts[cut - 1]
            d.ellipse([mx - 13, my - 13, mx + 13, my + 13], fill=AMBER + (255,))
            d.ellipse([mx - 5, my - 5, mx + 5, my + 5], fill=(255, 255, 255, 255))
        lab = self.label("RETENTION", 26, (170, 190, 225), 6)
        ov.paste(lab, (px1 - lab.width - 34, py0 + 18))
        ov.paste(self.label("100%", 26, (140, 165, 205), 3), (78, y0 - 14))
        p3 = self.label("3 DETIK", 24, (255, 120, 135), 4)
        ov.paste(p3, (bx - p3.width // 2, py0 + 18))
        vs.dashed_line(d, (bx, py0 + 74), (bx, y1), dash=14, gap=12, width=3,
                       fill=(255, 110, 125, 150))

    # -- 5. kartu aturan -------------------------------------------------- #
    def scene_rule(self, ov: Image.Image, ctx: Ctx) -> None:
        t = ctx.t_local
        b = ctx.beat
        d = ImageDraw.Draw(ov)
        accent = b.accent
        cx, cy, R = WIDTH / 2, 420, 88
        pop = vs.ease_out_back(vs.norm(t, 0.02, 0.46), 2.1)
        if pop > 0.01:
            halo = self.halos["disc_badge"].copy()
            halo.putalpha(halo.getchannel("A").point(lambda v, k=0.5 * pop: int(v * k)))
            ov.paste(halo, (int(cx - halo.width / 2), int(cy - halo.height / 2)), halo)
            rr = int(R * (0.4 + 0.6 * pop))
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(14, 20, 38, 228))
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=accent + (235,), width=6)
            for k in range(2):
                ph = (t * 0.7 + k * 0.5) % 1.0
                rr2 = int(R * (1.0 + ph * 0.9))
                d.ellipse([cx - rr2, cy - rr2, cx + rr2, cy + rr2],
                          outline=accent + (int(95 * (1 - ph)),), width=3)
            sp = self.label(b.spec["rule_no"], 74, WHITE, 2, "Black")
            ov.paste(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2 - 8)), sp)

        px0, py0, px1, py1 = 210, 545, 870, 735
        d.rounded_rectangle([px0, py0, px1, py1], radius=26, fill=(12, 16, 32, 198),
                            outline=(120, 150, 220, 62), width=2)
        key = b.key
        if key == "rule1":
            prog = vs.norm(t, 0.30, 2.60)
            for k in range(26):
                u = prog - k * 0.013
                if 0 <= u <= 1:
                    xx = px0 + 46 + u * (px1 - px0 - 92)
                    yy = (py0 + py1) / 2 + 40 * math.sin(u * 7.0)
                    d.ellipse([xx - 9, yy - 9, xx + 9, yy + 9],
                              fill=accent + (int(200 * (1 - k / 26)),))
            ue = vs.ease_in_out_cubic(prog)
            xx = px0 + 46 + ue * (px1 - px0 - 92)
            yy = (py0 + py1) / 2 + 40 * math.sin(ue * 7.0)
            d.ellipse([xx - 15, yy - 15, xx + 15, yy + 15], fill=WHITE + (255,))
        elif key == "rule2":
            for i, (fx, a) in enumerate([(px0 + 52, 1.0), (px0 + 292, 0.34), (px0 + 532, 0.16)]):
                appear = vs.norm(t, 0.26 + i * 0.15, 0.56 + i * 0.15)
                d.rounded_rectangle([fx, py0 + 36, fx + 186, py1 - 36], radius=18,
                                    outline=(200, 215, 245, int(120 * a * appear)), width=3)
            appear = vs.norm(t, 0.20, 0.60)
            if appear > 0.05:
                s2 = 0.6 + 0.4 * vs.ease_out_back(appear, 1.5)
                rr = int(34 * s2)
                ccx, ccy = px0 + 52 + 93, (py0 + py1) / 2
                d.ellipse([ccx - rr, ccy - rr, ccx + rr, ccy + rr],
                          fill=accent + (int(255 * appear),))
        else:
            base = py0 + 150
            pts = []
            for i in range(101):
                u = i / 100.0
                spike = math.exp(-((u - 0.62) ** 2) / 0.0022) * 152
                pts.append((px0 + 34 + u * (px1 - px0 - 68), base - spike - 6 * math.sin(u * 22)))
            cut = int(vs.ease_out_cubic(vs.norm(t, 0.30, 1.80)) * len(pts))
            if cut > 2:
                d.line(pts[:cut], fill=accent + (240,), width=5, joint="curve")

    # -- 6. klimaks ------------------------------------------------------- #
    def scene_climax(self, ov: Image.Image, ctx: Ctx) -> None:
        t, b = ctx.t_local, ctx.beat
        onset = b.lead_in
        d = ImageDraw.Draw(ov)
        cx, cy = WIDTH / 2, 930
        if t > onset - 0.08:
            grow = vs.ease_out_expo(vs.norm(t, onset, onset + 1.05))
            idx = int(vs.clamp(grow, 0.0, 0.999) * len(self.bursts))
            layer = self.bursts[idx].copy()
            a = int(120 * (1 - vs.norm(t, onset + 0.22, onset + 1.25)))
            layer.putalpha(layer.getchannel("A").point(lambda v, k=max(0, a) / 255: int(v * k)))
            ov.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)), layer)
        if t > onset:
            sweep = vs.ease_out_expo(vs.norm(t, onset + 0.1, onset + 0.85))
            w = int(880 * sweep)
            d.rounded_rectangle([WIDTH / 2 - w / 2, 1216, WIDTH / 2 + w / 2, 1230],
                                radius=7, fill=AMBER + (235,))

    # -- 7. outro + kartu merek ------------------------------------------- #
    def scene_outro(self, ov: Image.Image, ctx: Ctx) -> None:
        t, b = ctx.t_local, ctx.beat
        d = ImageDraw.Draw(ov)
        vo_end = b.lead_in + b.vo_dur
        fade_out = 1.0 - vs.norm(t, b.dur - 0.55, b.dur - 0.04)

        if t < vo_end + 0.30:
            a = int(235 * vs.norm(t, 0.05, 0.5) * (1 - vs.norm(t, vo_end, vo_end + 0.33)))
            if a > 4:
                cx, cy, R = WIDTH / 2, 566, 70
                d.arc([cx - R, cy - R, cx + R, cy + R], start=-55 + t * 42, end=250 + t * 42,
                      fill=AMBER + (a,), width=9)
                ang = math.radians(250 + t * 42)
                vs.arrow_head(d, (cx + R * math.cos(ang), cy + R * math.sin(ang)),
                              math.degrees(ang) + 90, 24, AMBER + (a,))

        card = vs.norm(t, vo_end + 0.25, vo_end + 0.85)
        ctx.text_alpha = 1.0 - vs.norm(t, vo_end + 0.05, vo_end + 0.55)
        if card > 0.01 and fade_out > 0.01:
            alpha = card * fade_out
            dc = ImageDraw.Draw(ov)
            ys = int(30 * (1 - card))
            dc.rounded_rectangle([110, 700 + ys, 970, 1300 + ys], radius=46,
                                 fill=(10, 13, 26, int(195 * alpha)),
                                 outline=(130, 160, 230, int(85 * alpha)), width=2)
            ra = int(255 * alpha)
            dc.arc([WIDTH / 2 - 66, 742 + ys, WIDTH / 2 + 66, 874 + ys],
                   start=-70 + t * 52, end=230 + t * 52, fill=AMBER + (ra,), width=9)
            ang = math.radians(230 + t * 52)
            vs.arrow_head(dc, (WIDTH / 2 + 66 * math.cos(ang), 808 + ys + 66 * math.sin(ang)),
                          math.degrees(ang) + 90, 24, AMBER + (ra,))
            word = vs.tracked_sprite(BRAND, vs.font("Black", 92), WHITE, tracking=14)
            sub = vs.tracked_sprite(TAGLINE, vs.font("Semi", 30), (176, 194, 230), tracking=8)
            save = self.label(SAVE_HINT, 30, AMBER, 6)
            cta = self.label(CTA, 30, (200, 214, 244), 4)
            for sp, (x, y) in ((word, ((WIDTH - word.width) // 2, 892 + ys)),
                               (sub, ((WIDTH - sub.width) // 2, 1012 + ys)),
                               (save, ((WIDTH - save.width) // 2, 1092 + ys)),
                               (cta, ((WIDTH - cta.width) // 2, 1162 + ys))):
                sp = sp.copy()
                sp.putalpha(sp.getchannel("A").point(lambda v, a=alpha: int(v * a)))
                ov.paste(sp, (x, y), sp)

        if fade_out < 0.9999:
            ov.alpha_composite(Image.new("RGBA", ov.size,
                                         BG_DEEP + (int(255 * (1 - fade_out) * 0.9),)))

    # ----------------------------------------------------------------- frame
    def flash_color(self, t: float):
        out = None
        for b in self.beats:
            if b.key == "hook":
                dt = t - b.start
                if -0.02 <= dt < 0.34:
                    out = (CYAN, 0.14 * max(0.0, 1 - max(0.0, dt) / 0.34) ** 2)
            if b.key == "climax":
                dt = t - (b.start + b.lead_in)
                if -0.06 <= dt < 0.55:
                    out = (AMBER, 0.17 * max(0.0, 1 - max(0.0, dt) / 0.5) ** 1.7)
        return out

    def render_beat(self, t: float) -> Image.Image:
        b = beat_at(self.beats, self.starts, t)
        ctx = Ctx(beat=b, beats=self.beats, t_local=t - b.start, t_global=t,
                  total=self.total)
        if b.key == "climax":
            dt = t - (b.start + b.lead_in)
            if -0.05 < dt < 0.75:
                amp = math.exp(-4.2 * max(0.0, dt)) * 24
                ctx.shake = (amp * math.sin(dt * 61), amp * 0.7 * math.sin(dt * 47 + 1.1))
        return self.compose(ctx, t)

    def compose(self, ctx: Ctx, t: float) -> Image.Image:
        b = ctx.beat
        frame = self.bg_static.copy()
        self.draw_aurora(frame, t)
        self.draw_bokeh(frame, t)

        ov = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        self.overlay_motes(ov, t)

        ox, oy = int(ctx.shake[0]), int(ctx.shake[1])
        if (ox, oy) != (0, 0):
            layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            self.scene_graphics(layer, ctx)
            ov.alpha_composite(ImageChops.offset(layer, ox, oy))
        else:
            self.scene_graphics(ov, ctx)

        text_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        block = self.blocks[b.index]
        times = [b.word_onset(i) for i in range(len(block.words))]
        style = b.spec.get("text_style", "reveal")
        strike = {i for i, w in enumerate(b.screen_words)
                  if norm_token(w) in {norm_token(s) for s in b.spec.get("strike", [])}}
        persist = {i for i, w in enumerate(b.screen_words)
                   if norm_token(w) in {norm_token(s) for s in b.spec.get("persist", [])}}
        block.draw(text_layer, ctx.t_local, times, style=style,
                   active_index=b.active_word(ctx.t_local), strike=strike,
                   persist=persist, offset=(ox, oy))
        if ctx.text_alpha < 0.999:
            text_layer.putalpha(text_layer.getchannel("A").point(
                lambda v: int(v * ctx.text_alpha)))
        ov.alpha_composite(text_layer)

        self.draw_hud(ov, t, ctx)
        frame.paste(ov, (0, 0), ov)

        flash = self.flash_color(t)
        if flash:
            frame = Image.blend(frame, self.solids[flash[0]], vs.clamp(flash[1]))
        return self.apply_grain(frame, t)

    def apply_grain(self, frame: Image.Image, t: float) -> Image.Image:
        frames = vs.grain_stack(8, (WIDTH, HEIGHT), 11)
        return ImageChops.add(frame, frames[int(t * FPS) % len(frames)], 1.0, -128)

    # ---------------------------------------------------------------- transisi
    def wipe_mask(self, k: float, direction: int) -> Image.Image:
        w, h = 128, 8
        xs = np.linspace(0, 1, w)
        m = np.clip((xs - (k - 0.22)) / 0.22, 0, 1)
        if direction < 0:
            m = m[::-1]
        arr = np.repeat((m[None, :] * 255).astype(np.uint8), h, axis=0)
        return Image.fromarray(arr, "L").resize((WIDTH, HEIGHT), Image.BILINEAR)

    def frame(self, t: float) -> Image.Image:
        b = beat_at(self.beats, self.starts, t)
        nxt_i = b.index + 1
        if nxt_i < len(self.beats):
            nxt = self.beats[nxt_i]
            if t > nxt.start - TRANSITION:
                k = vs.smoothstep(vs.norm(t, nxt.start - TRANSITION, nxt.start))
                prev_img = self.render_beat(t)
                nxt_img = self.render_beat(min(t, nxt.start + 0.001))
                mask = self.wipe_mask(k, 1 if nxt_i % 2 else -1)
                out = Image.composite(nxt_img, prev_img, mask)
                flash = self.flash_color(t)
                if flash:
                    out = Image.blend(out, self.solids[flash[0]], vs.clamp(flash[1]) * 0.6)
                return out
        return self.render_beat(t)


def clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


# --------------------------------------------------------------------------- #
#  Audio render
# --------------------------------------------------------------------------- #
def build_audio(beats: list[Beat], out_path: Path, verbose: bool = True) -> Path:
    vo_events = []
    sfx_events = []
    for b in beats:
        if b.vo_clip is not None and len(b.vo_clip):
            vo_events.append((b.start + b.lead_in, b.vo_clip))
        keys = b.spec.get("sfx", ())
        if not isinstance(keys, (tuple, list)):
            keys = (keys,)
        for j, key in enumerate(keys):
            if key in ("riser", "riser_short"):
                dur = ad.SFX_BUILDERS[key](ad.SR).size / ad.SR
                sfx_events.append((max(0.0, b.start + b.lead_in - dur + 0.12), key, -12.0, 0.0))
            elif key.startswith("tick"):
                for k in range(3):
                    sfx_events.append((b.start + 0.12 + k * 0.2, "tick", -17.0 + k * 0.5,
                                       -0.6 + k * 0.6))
            elif key in ("impact", "impact_soft", "sub_drop"):
                sfx_events.append((b.start + b.lead_in - 0.03, key, -7.0, 0.0))
            else:
                sfx_events.append((b.start + (0.0 if j else b.lead_in * 0.5), key, -12.0,
                                   0.35 if j % 2 else -0.35))
        # transisi: whoosh tiap potong
        if b.index > 0:
            sfx_events.append((max(0.0, b.start - TRANSITION * 0.55), "whoosh", -15.0,
                               -0.45 if b.index % 2 else 0.45))
    total = timeline_duration(beats)
    mix = ad.build_mix(total, vo_events, sfx_events)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ad.encode_wav(str(out_path), mix)
    if verbose:
        loud = ad.measure_lufs(mix.mean(axis=1))
        print(f"[audio] {out_path.name}: {total:.2f}s, ~{loud:.1f} LUFS (perkiraan), "
              f"peak {np.max(np.abs(mix)):.3f}")
    return out_path


# --------------------------------------------------------------------------- #
#  Encode
# --------------------------------------------------------------------------- #
def render_frames(renderer: Renderer, proc: subprocess.Popen, total: float,
                  timer: list, label: str) -> None:
    n_frames = int(math.ceil(total * FPS))
    t0 = time.time()
    for i in range(n_frames):
        t = i / FPS
        img = renderer.frame(t)
        proc.stdin.write(img.tobytes())
        if i % 30 == 0 or i == n_frames - 1:
            el = time.time() - t0
            fps = (i + 1) / max(1e-6, el)
            eta = (n_frames - i - 1) / max(1e-6, fps)
            print(f"  {label} frame {i + 1}/{n_frames}  {fps:5.1f} fps  ETA {eta:5.0f}s",
                  flush=True)
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise SystemExit(f"[encode] ffmpeg gagal (kode {proc.returncode})")
    timer.append(time.time() - t0)


def encode_video(renderer: Renderer, total: float, audio_path: Path, out_path: Path,
                 target_mb: float | None = None, preset: str = "veryslow",
                 crf: int | None = None, scale: float = 1.0, passes: int = 2,
                 audio_kbps: int = 320, verbose: bool = True) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    dur = total
    if crf is None:
        target = (target_mb or 215.0) * 1024 * 1024
        audio_bits = audio_kbps * 1000 * dur
        v_bps = max(6e6, (target * 8 - audio_bits) / dur)
        v_bps = min(v_bps, 90e6)
        v_kbps = int(v_bps / 1000)
    else:
        v_kbps = None

    w, h = int(WIDTH * scale) // 2 * 2, int(HEIGHT * scale) // 2 * 2
    vf = f"scale={w}:{h}:flags=lanczos" if scale != 1.0 else None

    base = [ad.ffmpeg_exe(), "-y", "-v", "warning",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
            "-r", str(FPS), "-i", "pipe:0"]
    timer: list = []

    for p in range(1, passes + 1):
        cmd = list(base)
        cmd += ["-i", str(audio_path)]
        if vf:
            cmd += ["-vf", vf]
        cmd += ["-c:v", "libx264", "-preset", preset, "-profile:v", "high",
                "-level:v", "5.1", "-pix_fmt", "yuv420p", "-g", str(FPS * 2),
                "-bf", "3", "-x264-params", "force-cfr=1:scenecut=0:rc-lookahead=60",
                "-threads", "0"]
        if crf is not None:
            cmd += ["-crf", str(crf)]
        else:
            cmd += ["-b:v", f"{v_kbps}k", "-maxrate", f"{int(v_kbps * 1.35)}k",
                    "-bufsize", f"{int(v_kbps * 2.4)}k"]
        if p < passes:
            cmd += [f"-pass", str(p), "-passlogfile", str(BUILD_DIR / "x264pass"), "-an", "-f", "null", "/dev/null"]
        else:
            cmd += ["-c:a", "aac", "-b:a", f"{audio_kbps}k", "-ar", str(ad.SR),
                    "-ac", "2", "-movflags", "+faststart", "-shortest", str(out_path)]
        if verbose:
            print(f"[encode] pass {p}/{passes} -> {out_path.name if p == passes else 'stats'}"
                  + (f"  target {v_kbps / 1000:.1f} Mbps" if v_kbps else f"  crf {crf}"))
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        render_frames(renderer, proc, total, timer, f"pass{p}")

    if verbose:
        size = out_path.stat().st_size / 1024 / 1024
        print(f"[encode] selesai: {out_path}  {size:.1f} MB  "
              f"({size * 8 / dur:.1f} Mbps rata-rata, {dur:.2f}s)")
    return out_path


# --------------------------------------------------------------------------- #
#  Stills (untuk QA visual)
# --------------------------------------------------------------------------- #
def dump_stills(renderer: Renderer, times: list[float], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for t in times:
        img = renderer.frame(t)
        p = out_dir / f"still_{t:06.2f}s.png"
        img.save(p)
        print(f"[still] {p} ({img.size[0]}x{img.size[1]})")


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="KlikTahu Cinematic Video Engine")
    ap.add_argument("--render", action="store_true", help="render video penuh")
    ap.add_argument("--preview", action="store_true", help="render cepat (setengah resolusi, crf)")
    ap.add_argument("--still", type=str, default=None,
                    help="daftar waktu detik dipisah koma untuk ekspor PNG (QA)")
    ap.add_argument("--still-out", type=str, default=str(BUILD_DIR / "stills"))
    ap.add_argument("--out", type=str, default=str(ROOT / "KlikTahu_Shorts_1080x1920.mp4"))
    ap.add_argument("--target-mb", type=float, default=235.0,
                    help="target ukuran file akhir (MB), dipakai untuk hitung bitrate 2-pass")
    ap.add_argument("--crf", type=int, default=None, help="pakai CRF alih-alih target ukuran")
    ap.add_argument("--preset", type=str, default="medium")
    ap.add_argument("--audio-kbps", type=int, default=320)
    ap.add_argument("--passes", type=int, default=1,
                    help="1 = ABR sekali jalan (cukup pada bitrate tinggi), 2 = presisi ukuran")
    ap.add_argument("--sample", type=float, default=None,
                    help="batasi render ke N detik pertama (uji kualitas/bitrate)")
    args = ap.parse_args(argv)

    beats = build_timeline()
    renderer = Renderer(beats)
    total = renderer.total

    if args.still:
        times = [float(x) for x in args.still.split(",") if x.strip()]
        dump_stills(renderer, times, Path(args.still_out))
        return 0

    if args.render or args.preview:
        preview = args.preview and not args.render
        if args.sample:
            total = min(total, args.sample)
            beats[:] = [b for b in beats if b.start < total - 0.001]
            renderer.beats = beats
            renderer.starts = [b.start for b in beats]
            renderer.total = total
        audio_path = build_audio(beats, BUILD_DIR / "mix.wav")
        encode_video(
            renderer, total, audio_path, Path(args.out),
            target_mb=None if (preview or args.crf) else args.target_mb,
            preset="veryfast" if preview else args.preset,
            crf=(28 if preview else args.crf),
            scale=0.5 if preview else 1.0,
            passes=1 if preview else args.passes,
            audio_kbps=args.audio_kbps,
        )
        return 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
