"""KlikTahu's warm, story-led 9:16 motion-design renderer.

Frames are drawn procedurally with Pillow and encoded by the FFmpeg binary
bundled with imageio-ffmpeg. The scene order is intentional: Hook → Problem →
three progressive value beats → Micro-Climax → visual return to the Hook.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import subprocess
import tempfile
from typing import Any

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from audio_engine import build_audio_mix, read_wav_duration

ROOT = Path(__file__).resolve().parent
DEFAULT_STORY = ROOT / "story.json"
DEFAULT_OUTPUT = ROOT / "KlikTahu_Cinematic.mp4"
VOICE_DIR = ROOT / "audio"

DESIGN_W, DESIGN_H = 1080, 1920
FPS = 30
SAMPLE_RATE = 48_000
TRANSITION_SECONDS = 0.64

# A restrained, warm editorial palette: amber, toasted orange, paper and umber.
BG_TOP = (34, 25, 20)
BG_BOTTOM = (46, 31, 23)
CARD = (54, 39, 30)
CARD_LIFT = (65, 46, 34)
CREAM = (245, 233, 211)
PAPER = (225, 209, 183)
AMBER = (224, 164, 79)
AMBER_LIGHT = (243, 194, 111)
BURNT = (161, 91, 49)
MUTED = (169, 144, 117)
HAIRLINE = (104, 76, 53)
DIM = (77, 58, 45)

STAGE_LABELS = (
    "THE HOOK",
    "THE PROBLEM",
    "THE VALUE",
    "MICRO-CLIMAX",
    "THE LOOP",
)
FONT_CANDIDATES = {
    "sans": (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/Library/Fonts/Arial.ttf",
    ),
    "sans_bold": (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ),
    "serif": (
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
        "/Library/Fonts/Georgia.ttf",
    ),
    "serif_bold": (
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
        "/Library/Fonts/Georgia Bold.ttf",
    ),
    "mono": (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
    ),
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def ease(value: float) -> float:
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def _read_story(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        story = json.load(stream)
    validate_story(story)
    return story


def validate_story(story: dict[str, Any]) -> None:
    """Fail early on incomplete or oversized copy that would break the layout."""
    if not isinstance(story, dict):
        raise ValueError("Story must be a JSON object.")
    required = ("topic", "hook", "agitation", "body", "micro_climax", "outro")
    missing = [key for key in required if key not in story]
    if missing:
        raise ValueError(f"Story is missing required sections: {', '.join(missing)}")
    if not isinstance(story["body"], list) or len(story["body"]) != 3:
        raise ValueError("The story must contain exactly three progressive body beats.")
    for section in ("hook", "agitation", "micro_climax", "outro"):
        if not isinstance(story[section], dict):
            raise ValueError(f"Section '{section}' must be an object.")
        if not isinstance(story[section].get("narration"), str) or not story[section]["narration"].strip():
            raise ValueError(f"Section '{section}' needs a narration line.")
        if not isinstance(story[section].get("caption"), str) or not story[section]["caption"].strip():
            raise ValueError(f"Section '{section}' needs a concise subtitle.")
        if len(story[section]["narration"]) > 600 or len(story[section]["caption"]) > 90:
            raise ValueError(f"Section '{section}' copy is too long for a short-form film.")
    for section in ("hook", "agitation"):
        if len(story[section].get("headline", [])) != 2:
            raise ValueError(f"Section '{section}' must have two headline lines.")
    if len(story["micro_climax"].get("headline", [])) != 3:
        raise ValueError("The Micro-Climax must have three headline lines.")
    for index, point in enumerate(story["body"], start=1):
        if not isinstance(point, dict):
            raise ValueError(f"Body beat {index} must be an object.")
        for key in ("title", "support", "narration", "caption"):
            if not isinstance(point.get(key), str) or not point[key].strip():
                raise ValueError(f"Body beat {index} needs '{key}'.")
        if len(point["title"]) > 32 or len(point["support"]) > 58 or len(point["caption"]) > 90:
            raise ValueError(f"Body beat {index} is too long for the on-screen card.")
    if len(story["hook"].get("headline", [])) != 2:
        raise ValueError("The hook must have two headline lines.")
    if len(story["agitation"].get("labels", [])) != 3:
        raise ValueError("The problem scene must have three visual labels.")
    if len(story["micro_climax"].get("nodes", [])) != 3:
        raise ValueError("The Micro-Climax must connect the three ideas introduced earlier.")


@lru_cache(maxsize=128)
def _font(family: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = FONT_CANDIDATES.get(family, FONT_CANDIDATES["sans"])
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow before the size-aware default font API.
        return ImageFont.load_default()


@lru_cache(maxsize=12)
def _background() -> np.ndarray:
    """A quiet, static warm gradient with restrained paper grain and vignette."""
    x = np.linspace(-1.0, 1.0, DESIGN_W, dtype=np.float32)[None, :, None]
    y = np.linspace(0.0, 1.0, DESIGN_H, dtype=np.float32)[:, None, None]
    top = np.asarray(BG_TOP, dtype=np.float32)[None, None, :]
    bottom = np.asarray(BG_BOTTOM, dtype=np.float32)[None, None, :]
    gradient = np.broadcast_to(top * (1.0 - y) + bottom * y,
                               (DESIGN_H, DESIGN_W, 3)).copy()
    distance = np.sqrt((x * 0.88) ** 2 + ((y - 0.53) * 0.93) ** 2)
    warm_light = np.maximum(0.0, 1.0 - distance) ** 2 * 8.5
    gradient += warm_light * np.asarray([1.0, 0.62, 0.28], dtype=np.float32)[None, None, :]
    vignette = np.clip(1.0 - 0.12 * np.maximum(0.0, distance - 0.34), 0.82, 1.0)
    gradient *= vignette
    grain = np.random.default_rng(44).normal(0.0, 0.66, (DESIGN_H, DESIGN_W, 1)).astype(np.float32)
    result = np.clip(gradient + grain, 0, 255).astype(np.uint8)
    result.setflags(write=False)
    return result


@lru_cache(maxsize=16)
def _glow_sprite(radius: int, color: tuple[int, int, int]) -> Image.Image:
    radius = max(18, int(radius))
    size = radius * 4
    coords = np.arange(size, dtype=np.float32) - (size - 1) / 2.0
    xx, yy = np.meshgrid(coords, coords)
    distance = np.sqrt(xx * xx + yy * yy)
    sigma = radius * 0.95
    alpha = (45.0 * np.exp(-(distance * distance) / (2.0 * sigma * sigma))).astype(np.uint8)
    rgb = np.empty((size, size, 4), dtype=np.uint8)
    rgb[..., :3] = np.asarray(color, dtype=np.uint8)
    rgb[..., 3] = alpha
    return Image.fromarray(rgb, "RGBA")


def _draw_glow(canvas: Image.Image, center: tuple[float, float], radius: int = 70,
               color: tuple[int, int, int] = AMBER, strength: float = 1.0) -> None:
    if strength <= 0:
        return
    sprite = _glow_sprite(radius, color).copy()
    alpha = sprite.getchannel("A").point(lambda value: int(value * clamp(strength, 0.0, 1.0)))
    sprite.putalpha(alpha)
    left = int(center[0] - sprite.width / 2)
    top = int(center[1] - sprite.height / 2)
    canvas.alpha_composite(sprite, (left, top))


def _text_width(text: str, font: ImageFont.ImageFont) -> float:
    box = font.getbbox(text)
    return float(box[2] - box[0])


def _fit_font(text: str, family: str, base_size: int, max_width: int,
              minimum: int = 38) -> ImageFont.ImageFont:
    size = base_size
    while size > minimum and _text_width(text, _font(family, size)) > max_width:
        size -= 2
    return _font(family, size)


def _draw_text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str,
               font: ImageFont.ImageFont, color: tuple[int, int, int], alpha: float = 1.0,
               anchor: str | None = None) -> None:
    fill = (*color, int(255 * clamp(alpha)))
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont,
               max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = word if not line else f"{line} {word}"
        if _text_width(candidate, font) <= max_width or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines or [""]


def _rounded_card(draw: ImageDraw.ImageDraw, box: tuple[float, float, float, float],
                  radius: int = 30, fill: tuple[int, int, int] = CARD,
                  stroke: tuple[int, int, int] = HAIRLINE, alpha: float = 1.0,
                  shadow: bool = True) -> None:
    x1, y1, x2, y2 = box
    opacity = int(255 * clamp(alpha))
    if shadow:
        draw.rounded_rectangle((x1 + 2, y1 + 13, x2 + 2, y2 + 13), radius=radius,
                               fill=(12, 8, 6, int(105 * alpha)))
    draw.rounded_rectangle(box, radius=radius, fill=(*fill, opacity),
                           outline=(*stroke, int(210 * alpha)), width=2)
    # A narrow top edge gives the card a tangible, low-contrast depth cue.
    draw.line((x1 + radius, y1 + 2, x2 - radius, y1 + 2),
              fill=(194, 143, 82, int(60 * alpha)), width=2)


class CinematicVideoPipeline:
    """Render a 1080×1920 continuous visual system with synced VO and SFX."""

    def __init__(self, story: dict[str, Any] | None = None, output_file: str | Path = DEFAULT_OUTPUT,
                 voice_dir: str | Path = VOICE_DIR, fps: int = FPS,
                 preview: bool = False) -> None:
        self.story = story or _read_story(DEFAULT_STORY)
        validate_story(self.story)
        self.output_file = Path(output_file)
        self.voice_dir = Path(voice_dir)
        self.fps = 12 if preview else int(fps)
        if self.fps < 1 or self.fps > 60:
            raise ValueError("FPS must be between 1 and 60.")
        self.preview = preview
        self.out_width, self.out_height = (540, 960) if preview else (DESIGN_W, DESIGN_H)
        self.timing = self._build_timing()
        self.duration = self.timing["outro"]["end"]
        self.frame_count = int(math.ceil(self.duration * self.fps - 1e-9))
        self._hook_frame: Image.Image | None = None

    def _build_timing(self) -> dict[str, dict[str, float]]:
        ordered: list[tuple[str, float]] = [
            ("hook", 4.25),
            ("agitation", 5.30),
            ("body_1", 4.10),
            ("body_2", 4.10),
            ("body_3", 4.10),
            ("micro_climax", 5.10),
            ("outro", 4.55),
        ]
        timing: dict[str, dict[str, float]] = {}
        cursor = 0.0
        for name, minimum in ordered:
            audio_path = self.voice_dir / f"vo_{name}.wav"
            voice_duration = read_wav_duration(audio_path) if audio_path.exists() else 0.0
            # Leave space for the visual reveal before speech and a calm landing after it.
            duration = max(minimum, 0.24 + voice_duration + 0.72)
            timing[name] = {
                "start": cursor,
                "duration": duration,
                "end": cursor + duration,
                "voice_duration": voice_duration,
            }
            cursor += duration
        return timing

    def _base(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        canvas = Image.fromarray(_background()).convert("RGBA")
        return canvas, ImageDraw.Draw(canvas, "RGBA")

    def _header(self, draw: ImageDraw.ImageDraw, section_index: int, progress: float,
                step: int | None = None) -> None:
        # Static brand and editorial folio establish a stable spatial reference.
        draw.ellipse((79, 71, 116, 108), outline=(*AMBER, 225), width=3)
        draw.ellipse((91, 83, 104, 96), fill=(*AMBER_LIGHT, 235))
        _draw_text(draw, (135, 77), "KLIKTAHU", _font("sans_bold", 23), CREAM)
        _draw_text(draw, (1002, 80), "VISUAL NOTE  /  01", _font("mono", 17), MUTED, anchor="ra")
        draw.line((80, 145, 1000, 145), fill=(*HAIRLINE, 150), width=2)

        rail_left, rail_right, rail_y = 92, 986, 190
        positions = np.linspace(rail_left, rail_right, 5)
        progress = clamp(progress, 0.0, 4.0)
        for index in range(4):
            x1, x2 = positions[index], positions[index + 1]
            segment_progress = clamp(progress - index)
            if segment_progress > 0:
                draw.line((x1, rail_y, x1 + (x2 - x1) * segment_progress, rail_y),
                          fill=(*AMBER, 190), width=4)
            if segment_progress < 1:
                draw.line((x1 + (x2 - x1) * segment_progress, rail_y, x2, rail_y),
                          fill=(*DIM, 210), width=4)
        for index, x in enumerate(positions):
            active = index <= int(progress) or (index == 4 and progress >= 3.98)
            radius = 7 if index == int(progress) else 5
            color = AMBER_LIGHT if active else DIM
            draw.ellipse((x - radius, rail_y - radius, x + radius, rail_y + radius),
                        fill=(*color, 245))

        label = f"0{section_index + 1}  /  {STAGE_LABELS[section_index]}"
        if section_index == 2 and step is not None:
            label += f"     ·     STEP 0{step} / 03"
        _draw_text(draw, (88, 228), label, _font("mono", 21), AMBER_LIGHT)

    def _caption(self, canvas: Image.Image, draw: ImageDraw.ImageDraw, name: str,
                 global_time: float, alpha_scale: float = 1.0) -> None:
        voice_start = self.timing[name]["start"] + 0.22
        voice_duration = self.timing[name]["voice_duration"]
        if voice_duration <= 0 or not (voice_start <= global_time <= voice_start + voice_duration + 0.12):
            return
        fade_in = ease((global_time - voice_start) / 0.20)
        fade_out = ease((voice_start + voice_duration + 0.12 - global_time) / 0.18)
        alpha = min(fade_in, fade_out) * alpha_scale
        if alpha <= 0.01:
            return

        story_key = name
        if name.startswith("body_"):
            index = int(name.split("_")[1]) - 1
            text = self.story["body"][index]["caption"]
        elif name == "micro_climax":
            text = self.story["micro_climax"]["caption"]
        else:
            text = self.story[story_key]["caption"]
        font = _font("sans", 31)
        lines = _wrap_text(draw, text, font, 810)[:2]
        top = 1487
        line_height = 45
        panel_height = 42 + line_height * len(lines)
        opacity = int(205 * clamp(alpha))
        draw.rounded_rectangle((78, top - 13, 1002, top + panel_height), radius=22,
                               fill=(34, 25, 20, int(opacity * 0.90)))
        draw.rounded_rectangle((78, top - 13, 86, top + panel_height), radius=4,
                               fill=(*AMBER, int(235 * alpha)))
        for line_index, line in enumerate(lines):
            _draw_text(draw, (112, top + line_index * line_height), line, font, CREAM, alpha)

    def _draw_focus(self, canvas: Image.Image, draw: ImageDraw.ImageDraw,
                    center: tuple[float, float], radius: float = 68, strength: float = 0.72,
                    label: str = "IDE") -> None:
        cx, cy = center
        _draw_glow(canvas, center, radius=int(radius * 1.65), strength=strength)
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                     fill=(47, 33, 26, 230), outline=(*AMBER, 235), width=3)
        draw.ellipse((cx - radius * 0.18, cy - radius * 0.18,
                      cx + radius * 0.18, cy + radius * 0.18), fill=(*AMBER_LIGHT, 250))
        if label:
            _draw_text(draw, (cx, cy + radius + 24), label, _font("mono", 18), MUTED, anchor="mt")

    def _draw_stack(self, canvas: Image.Image, draw: ImageDraw.ImageDraw, local: float,
                    outgoing: float = 0.0, camera: float = 0.0) -> None:
        labels = self.story["agitation"]["labels"]
        base_x, base_y, card_w, card_h = 174 + camera, 897, 744, 105
        for index, label in enumerate(labels):
            stagger = 0.18 + index * 0.28
            visible = ease(clamp((local - stagger) / 0.28))
            if local > self.timing["agitation"]["duration"] - TRANSITION_SECONDS:
                visible = max(visible, 1.0 - outgoing * (0.24 + index * 0.21))
            if visible <= 0.02:
                continue
            depth = index
            x = base_x + depth * (19 - outgoing * 7)
            y = base_y + depth * (112 - outgoing * 41)
            width = card_w - depth * 38 + outgoing * depth * 14
            height = card_h + outgoing * (118 if index == 0 else 30)
            fill = CARD_LIFT if index == 0 else CARD
            outline = AMBER if index == 0 else HAIRLINE
            box = (x, y, x + width, y + height)
            _rounded_card(draw, box, radius=24, fill=fill, stroke=outline,
                          alpha=visible * (0.97 if index == 0 else 0.84 - depth * 0.08), shadow=True)
            inner_y = y + (height - 30) / 2 - 3
            size = 31 if index == 0 else 27
            _draw_text(draw, (x + 36, inner_y), label, _font("sans_bold", size),
                       CREAM if index == 0 else PAPER, visible)
            _draw_text(draw, (x + width - 34, inner_y + 2), f"0{index + 1}",
                       _font("mono", 20), AMBER if index == 0 else MUTED, visible, anchor="ra")

    def _draw_hook(self, local: float, global_time: float, force_opening: bool = False) -> Image.Image:
        canvas, draw = self._base()
        duration = self.timing["hook"]["duration"]
        p = clamp(local / duration)
        camera = 7.0 * math.sin(math.pi * p)
        self._header(draw, 0, 0.0)
        headlines = self.story["hook"]["headline"]
        _draw_text(draw, (87, 438), headlines[0], _fit_font(headlines[0], "serif_bold", 128, 902), CREAM)
        _draw_text(draw, (87, 575), headlines[1], _fit_font(headlines[1], "serif_bold", 114, 902), AMBER_LIGHT)
        _draw_text(draw, (91, 744), "Yang banyak terlihat belum tentu diingat.",
                   _font("sans", 28), MUTED)

        transition = 0.0 if force_opening else ease(clamp((local - duration + 0.70) / 0.70))
        cx, cy = 540 + camera, 1122
        ring_radius = 67 * (1.0 - 0.12 * transition)
        self._draw_focus(canvas, draw, (cx, cy), radius=ring_radius, strength=0.72,
                         label="SATU IDE")
        if transition > 0.01:
            # The single point begins to unfold into the information stack.
            for index, label in enumerate(self.story["agitation"]["labels"]):
                reveal = ease(clamp((transition - index * 0.18) / 0.48))
                if reveal <= 0.02:
                    continue
                y = cy - 21 + index * 30
                width = 210 + index * 34
                x = cx - width / 2
                draw.rounded_rectangle((x, y, x + width, y + 18), radius=9,
                                       fill=(*AMBER, int(198 * reveal)))
            _draw_text(draw, (cx, cy + 186), "BANYAK SINYAL", _font("mono", 18),
                       MUTED, transition, anchor="mt")

        if not force_opening:
            self._caption(canvas, draw, "hook", global_time)
        return canvas.convert("RGB")

    def _draw_agitation(self, local: float, global_time: float) -> Image.Image:
        canvas, draw = self._base()
        duration = self.timing["agitation"]["duration"]
        p = clamp(local / duration)
        camera = 6.0 * math.sin(math.pi * p)
        self._header(draw, 1, 1.0)
        lines = self.story["agitation"]["headline"]
        _draw_text(draw, (87, 420), lines[0], _fit_font(lines[0], "serif_bold", 88, 902, 64), CREAM)
        _draw_text(draw, (87, 524), lines[1], _fit_font(lines[1], "serif_bold", 75, 902, 58), AMBER_LIGHT)
        _draw_text(draw, (91, 672), "PERHATIAN TERPECAH  →  PESAN TENGGELAM",
                   _font("mono", 19), MUTED)
        outgoing = ease(clamp((local - duration + TRANSITION_SECONDS) / TRANSITION_SECONDS))
        self._draw_stack(canvas, draw, local, outgoing=outgoing, camera=camera)
        self._caption(canvas, draw, "agitation", global_time)
        return canvas.convert("RGB")

    def _draw_body(self, index: int, local: float, global_time: float) -> Image.Image:
        canvas, draw = self._base()
        duration = self.timing[f"body_{index + 1}"]["duration"]
        p = clamp(local / duration)
        camera = 5.0 * math.sin(math.pi * p)
        self._header(draw, 2, 2.0, step=index + 1)
        _draw_text(draw, (87, 401), "BUKA RUANG", _font("serif_bold", 88), CREAM)
        _draw_text(draw, (87, 498), "UNTUK MAKNA.", _font("serif_bold", 82), AMBER_LIGHT)
        _draw_text(draw, (91, 621), "TIGA GERAKAN. SATU CERITA.", _font("mono", 20), MUTED)

        card_in = ease(clamp(local / 0.48)) if index == 0 else 1.0
        card_x = 213 + camera
        card_y = 841 + (1.0 - card_in) * 22
        card_w, card_h = 780, 404
        # On the first value beat, the pile resolves to one card; later beats keep
        # that same card anchored and reveal only the next piece of copy.
        if index == 0 and local < 0.58:
            ghost_alpha = (1.0 - ease(local / 0.58)) * 0.50
            for ghost in range(2):
                gy = card_y + 17 + ghost * 19
                _rounded_card(draw, (card_x + 12 + ghost * 9, gy,
                                     card_x + card_w - 12 + ghost * 9, gy + card_h - 20),
                              radius=30, fill=CARD, stroke=HAIRLINE, alpha=ghost_alpha, shadow=False)

        _rounded_card(draw, (card_x, card_y, card_x + card_w, card_y + card_h),
                      radius=32, fill=CARD_LIFT, stroke=AMBER, alpha=card_in, shadow=True)
        # A restrained vertical progress rail is both the lesson's structure and its map.
        rail_x = 121 + camera * 0.3
        rail_top, rail_bottom = 904, 1197
        draw.line((rail_x, rail_top, rail_x, rail_bottom), fill=(*HAIRLINE, 220), width=3)
        for node_index in range(3):
            y = rail_top + node_index * (rail_bottom - rail_top) / 2
            active = node_index == index
            past = node_index < index
            radius = 15 if active else 8
            color = AMBER_LIGHT if active else (BURNT if past else DIM)
            if active:
                _draw_glow(canvas, (rail_x, y), radius=37, strength=0.42)
            draw.ellipse((rail_x - radius, y - radius, rail_x + radius, y + radius),
                         fill=(*color, int(245 * card_in)),
                         outline=(*AMBER, int(190 * card_in)) if active else None, width=2)

        point = self.story["body"][index]
        draw_x = card_x + 49
        copy_in = 1.0 if index == 0 else ease(clamp(local / 0.30))
        _draw_text(draw, (draw_x, card_y + 42), f"0{index + 1}",
                   _font("serif_bold", 70), AMBER_LIGHT, card_in * copy_in)
        title_font = _fit_font(point["title"], "sans_bold", 52, 685, 39)
        title_alpha = ease(clamp((local - 0.12) / 0.38))
        title_x = draw_x + (1.0 - title_alpha) * 12
        _draw_text(draw, (title_x, card_y + 149), point["title"], title_font, CREAM,
                   title_alpha * card_in)
        underline_width = int(120 + 210 * ease(clamp((local - 0.30) / 0.75)))
        draw.rounded_rectangle((draw_x, card_y + 232, draw_x + underline_width,
                                card_y + 239), radius=4,
                               fill=(*AMBER, int(220 * title_alpha * card_in)))
        support_font = _fit_font(point["support"], "sans", 32, 680, 26)
        _draw_text(draw, (draw_x, card_y + 276), point["support"], support_font,
                   PAPER, ease(clamp((local - 0.42) / 0.38)) * card_in)
        _draw_text(draw, (card_x + card_w - 40, card_y + card_h - 48),
                   f"{index + 1:02d} / 03", _font("mono", 18), MUTED, 0.88, anchor="ra")
        self._caption(canvas, draw, f"body_{index + 1}", global_time)
        return canvas.convert("RGB")

    def _draw_micro_climax(self, local: float, global_time: float) -> Image.Image:
        canvas, draw = self._base()
        duration = self.timing["micro_climax"]["duration"]
        p = clamp(local / duration)
        camera = 5.0 * math.sin(math.pi * p)
        self._header(draw, 3, 3.0)
        headlines = self.story["micro_climax"]["headline"]
        _draw_text(draw, (87, 395), headlines[0], _fit_font(headlines[0], "serif_bold", 85, 900, 66), CREAM)
        _draw_text(draw, (87, 493), headlines[1], _fit_font(headlines[1], "serif_bold", 78, 900, 60), MUTED)
        _draw_text(draw, (87, 585), headlines[2], _fit_font(headlines[2], "serif_bold", 88, 900, 66), AMBER_LIGHT)
        _draw_text(draw, (91, 713), "TIGA LANGKAH. SATU ALUR.", _font("mono", 20), MUTED)

        nodes = self.story["micro_climax"]["nodes"]
        centers = [(206 + camera, 1110), (540 + camera, 1110), (874 + camera, 1110)]
        reveal = [ease(clamp((local - 0.35 - i * 0.36) / 0.43)) for i in range(3)]

        # The line only becomes visible as the previously introduced ideas connect.
        for i in range(2):
            line_reveal = ease(clamp((local - 0.64 - i * 0.35) / 0.48))
            if line_reveal > 0:
                x1, y1 = centers[i]
                x2, y2 = centers[i + 1]
                end_x = x1 + (x2 - x1) * line_reveal
                draw.line((x1 + 52, y1, end_x - (1.0 - line_reveal) * 52, y2),
                          fill=(*AMBER, int(215 * line_reveal)), width=5)
                if line_reveal > 0.82:
                    arrow_x = x2 - 53
                    draw.polygon(((arrow_x - 9, y2 - 7), (arrow_x + 1, y2),
                                  (arrow_x - 9, y2 + 7)), fill=(*AMBER_LIGHT, int(230 * line_reveal)))

        for index, (label, center) in enumerate(zip(nodes, centers)):
            amount = reveal[index]
            if amount <= 0.01:
                continue
            cx, cy = center
            radius = 43 + 7 * amount
            _draw_glow(canvas, center, radius=77, strength=0.22 * amount)
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                         fill=(52, 37, 28, int(245 * amount)),
                         outline=(*AMBER_LIGHT, int(240 * amount)), width=3)
            draw.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(*AMBER_LIGHT, int(245 * amount)))
            label_font = _fit_font(label, "mono", 17, 210, 15)
            _draw_text(draw, (cx, cy + 81), label, label_font, CREAM, amount, anchor="mt")

        payoff_alpha = ease(clamp((local - 1.52) / 0.45))
        _draw_text(draw, (540, 1298), "SATU IDE  ·  SATU WAKTU  ·  SATU CERITA",
                   _fit_font("SATU IDE  ·  SATU WAKTU  ·  SATU CERITA", "sans_bold", 26, 910, 20),
                   AMBER_LIGHT, payoff_alpha, anchor="mt")
        if payoff_alpha > 0.8:
            draw.line((200, 1362, 880, 1362), fill=(*HAIRLINE, int(125 * payoff_alpha)), width=2)
        self._caption(canvas, draw, "micro_climax", global_time)
        return canvas.convert("RGB")

    def _draw_outro(self, local: float, global_time: float) -> Image.Image:
        canvas, draw = self._base()
        duration = self.timing["outro"]["duration"]
        p = clamp(local / duration)
        loop_return = ease(clamp((local - duration + 1.05) / 1.05))
        progress = 4.0 * (1.0 - loop_return)
        self._header(draw, 4 if loop_return < 0.96 else 0, progress)
        _draw_text(draw, (87, 429), "SATU CERITA", _font("serif_bold", 101), CREAM,
                   1.0 - loop_return)
        _draw_text(draw, (87, 551), "MEMBUKA BERIKUTNYA.",
                   _fit_font("MEMBUKA BERIKUTNYA.", "serif_bold", 76, 904, 55), AMBER_LIGHT,
                   1.0 - loop_return)
        _draw_text(draw, (91, 685), "TINGGALKAN RUANG UNTUK PERTANYAAN BARU.",
                   _font("mono", 18), MUTED, 1.0 - loop_return)

        nodes = self.story["micro_climax"]["nodes"]
        original = [(206, 1110), (540, 1110), (874, 1110)]
        target = (540, 1122)
        collapse = ease(clamp((local - duration * 0.43) / (duration * 0.40)))
        points: list[tuple[float, float]] = []
        for index, ((x, y), label) in enumerate(zip(original, nodes)):
            point = (x + (target[0] - x) * collapse, y + (target[1] - y) * collapse)
            points.append(point)
            radius = 45 * (1.0 - 0.72 * collapse)
            amount = 1.0 - 0.40 * collapse
            _draw_glow(canvas, point, radius=72, strength=0.20 * amount)
            draw.ellipse((point[0] - radius, point[1] - radius,
                          point[0] + radius, point[1] + radius),
                         fill=(52, 37, 28, int(240 * amount)),
                         outline=(*AMBER, int(230 * amount)), width=3)
            if collapse < 0.35:
                _draw_text(draw, (point[0], point[1] + 73), label,
                           _font("mono", 16), CREAM, 1.0 - collapse * 2.6, anchor="mt")

        for i in range(2):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            draw.line((x1 + 48, y1, x2 - 48, y2),
                      fill=(*AMBER, int(205 * (1.0 - collapse))), width=4)
        # This ring is the same physical anchor as the opening: the story comes full circle.
        if collapse > 0:
            radius = 51 + 18 * collapse
            _draw_glow(canvas, target, radius=112, strength=0.54 * collapse)
            draw.ellipse((target[0] - radius, target[1] - radius,
                          target[0] + radius, target[1] + radius),
                         fill=(47, 33, 26, int(230 * collapse)),
                         outline=(*AMBER_LIGHT, int(242 * collapse)), width=3)
            draw.ellipse((target[0] - 12, target[1] - 12,
                          target[0] + 12, target[1] + 12),
                         fill=(*AMBER_LIGHT, int(245 * collapse)))

        self._caption(canvas, draw, "outro", global_time,
                      alpha_scale=1.0 - ease(clamp((local - duration + 0.48) / 0.48)))
        return canvas.convert("RGB")

    def _draw_scene(self, sequence_index: int, local: float, global_time: float) -> Image.Image:
        if sequence_index == 0:
            return self._draw_hook(local, global_time)
        if sequence_index == 1:
            return self._draw_agitation(local, global_time)
        if 2 <= sequence_index <= 4:
            return self._draw_body(sequence_index - 2, local, global_time)
        if sequence_index == 5:
            return self._draw_micro_climax(local, global_time)
        return self._draw_outro(local, global_time)

    def _sequence(self) -> list[tuple[str, float]]:
        names = ("hook", "agitation", "body_1", "body_2", "body_3", "micro_climax", "outro")
        return [(name, self.timing[name]["duration"]) for name in names]

    def _transition_mask(self, target_index: int, phase: float) -> Image.Image:
        phase = ease(phase)
        mask = Image.new("L", (DESIGN_W, DESIGN_H), 0)
        draw = ImageDraw.Draw(mask)
        if target_index == 1:
            # Focus expands into a field of competing inputs.
            rx, ry = 5 + phase * 690, 5 + phase * 1_100
            draw.ellipse((540 - rx, 1110 - ry, 540 + rx, 1110 + ry), fill=255)
        elif target_index == 2:
            # The overloaded pile resolves into one card; reveal grows from its face.
            width, height = 18 + phase * 1_250, 24 + phase * 1_900
            draw.rounded_rectangle((540 - width / 2, 1_080 - height / 2,
                                    540 + width / 2, 1_080 + height / 2),
                                   radius=int(24 + phase * 95), fill=255)
        elif target_index in (5, 6):
            # Three previously shown steps become three connected nodes.
            radius = 4 + phase * 1_520
            for cx in (206, 540, 874):
                draw.ellipse((cx - radius, 1_110 - radius,
                              cx + radius, 1_110 + radius), fill=255)
        return mask

    @staticmethod
    def _blend_transition_bands(previous: Image.Image, incoming: Image.Image,
                                composite: Image.Image, phase: float,
                                include_card: bool = False) -> Image.Image:
        """Keep typography legible while the story's central motif morphs beneath it."""
        header_box = (72, 145, 1_008, 300)
        header = Image.blend(previous.crop(header_box), incoming.crop(header_box), clamp(phase))
        composite.paste(header, header_box[:2])

        regions = [
            (70, 350, 1_010, 790),       # whole headline block; never slice a glyph
            (70, 1_438, 1_010, 1_730),    # subtitle changes as one readable unit
        ]
        if include_card:
            regions.append((94, 820, 1_006, 1_322))
        alpha = clamp(phase)
        paper = Image.fromarray(_background())
        for box in regions:
            old_region = previous.crop(box)
            new_region = incoming.crop(box)
            blank_region = paper.crop(box)
            if alpha < 0.44:
                region = old_region
            elif alpha < 0.54:
                fade = ease((alpha - 0.44) / 0.10)
                region = Image.blend(old_region, blank_region, fade)
            else:
                reveal = ease((alpha - 0.54) / 0.46)
                region = Image.blend(blank_region, new_region, reveal)
            composite.paste(region, box[:2])
        return composite

    def _frame_at(self, time: float) -> Image.Image:
        sequence = self._sequence()
        cursor = 0.0
        index = len(sequence) - 1
        local = 0.0
        for candidate, (_, duration) in enumerate(sequence):
            if time < cursor + duration:
                index = candidate
                local = time - cursor
                break
            cursor += duration
        else:
            local = sequence[-1][1]

        if index == 0:
            frame = self._draw_hook(local, time)
        elif index == 6:
            frame = self._draw_outro(local, time)
            if local < TRANSITION_SECONDS:
                phase = ease(local / TRANSITION_SECONDS)
                previous = self._draw_scene(5,
                    max(0.0, sequence[5][1] - TRANSITION_SECONDS + local), time)
                incoming = frame
                mask = self._transition_mask(6, local / TRANSITION_SECONDS)
                frame = Image.composite(incoming, previous, mask)
                frame = self._blend_transition_bands(previous, incoming, frame, phase)

            outro_duration = self.timing["outro"]["duration"]
            return_start = outro_duration - 0.86
            if local >= return_start:
                phase = ease(clamp((local - return_start) / 0.86))
                opening = self._opening_frame()
                if phase >= 0.995:
                    frame = opening
                else:
                    mask = Image.new("L", (DESIGN_W, DESIGN_H), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    radius = 90 + phase * 1_600
                    mask_draw.ellipse((540 - radius, 1_122 - radius,
                                       540 + radius, 1_122 + radius), fill=255)
                    frame = Image.composite(opening, frame, mask)
        else:
            frame = self._draw_scene(index, local, time)
            if local < TRANSITION_SECONDS and index not in (3, 4):
                phase = ease(local / TRANSITION_SECONDS)
                previous = self._draw_scene(index - 1,
                    max(0.0, sequence[index - 1][1] - TRANSITION_SECONDS + local), time)
                mask = self._transition_mask(index, local / TRANSITION_SECONDS)
                frame = Image.composite(frame, previous, mask)
                if index in (1, 2, 5):
                    frame = self._blend_transition_bands(
                        previous, self._draw_scene(index, local, time), frame, phase,
                        include_card=(index == 2),
                    )

        if self.preview:
            frame = frame.resize((self.out_width, self.out_height), Image.Resampling.LANCZOS)
        return frame

    def _opening_frame(self) -> Image.Image:
        if self._hook_frame is None:
            self._hook_frame = self._draw_hook(0.0, 0.0, force_opening=True)
        return self._hook_frame.copy()

    def render(self) -> Path:
        """Create the final H.264/AAC video by streaming frames into FFmpeg."""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        executable = imageio_ffmpeg.get_ffmpeg_exe()
        with tempfile.TemporaryDirectory(prefix="kliktahu-render-") as temp_dir:
            audio_path = Path(temp_dir) / "mix.wav"
            build_audio_mix(self.timing, self.voice_dir, audio_path, body_count=3)
            command = [
                executable, "-y", "-hide_banner", "-loglevel", "error",
                "-f", "rawvideo", "-pixel_format", "rgb24",
                "-video_size", f"{self.out_width}x{self.out_height}",
                "-framerate", str(self.fps), "-i", "-",
                "-i", str(audio_path),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart", str(self.output_file),
            ]
            process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                assert process.stdin is not None
                for frame_index in range(self.frame_count):
                    time = frame_index / self.fps
                    frame = self._frame_at(time)
                    process.stdin.write(frame.convert("RGB").tobytes())
                process.stdin.close()
                stderr = process.stderr.read() if process.stderr is not None else b""
                return_code = process.wait()
            except (BrokenPipeError, OSError):
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
                stderr = process.stderr.read() if process.stderr is not None else b""
                return_code = process.wait()
                raise RuntimeError(f"FFmpeg stopped while rendering: {stderr.decode(errors='replace')}")
            if return_code != 0:
                raise RuntimeError(f"FFmpeg failed: {stderr.decode(errors='replace')}")
        return self.output_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a warm, no-music KlikTahu short film.")
    parser.add_argument("--story", type=Path, default=DEFAULT_STORY,
                        help="Story JSON (default: story.json).")
    parser.add_argument("--voice-dir", type=Path, default=VOICE_DIR,
                        help="Folder containing vo_<scene>.wav narration clips.")
    parser.add_argument("--output", type=Path, default=None, help="Output MP4 path.")
    parser.add_argument("--fps", type=int, default=FPS, help="Frame rate, 1–60 (default: 30).")
    parser.add_argument("--preview", action="store_true",
                        help="Render a 540x960, 12 fps review copy instead of the master.")
    args = parser.parse_args()

    story = _read_story(args.story)
    output = args.output or (ROOT / "KlikTahu_Preview.mp4" if args.preview else DEFAULT_OUTPUT)
    pipeline = CinematicVideoPipeline(story, output, args.voice_dir, fps=args.fps,
                                      preview=args.preview)
    print(f"[KlikTahu] Rendering {pipeline.duration:.1f}s at {pipeline.fps} fps…")
    print("[KlikTahu] Audio: voice-over + synchronized non-musical SFX; no music.")
    result = pipeline.render()
    print(f"[KlikTahu] Finished: {result}")


if __name__ == "__main__":
    main()
