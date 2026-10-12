"""Procedural, non-musical sound design and voice-over mixing for KlikTahu.

All effects are short, non-tonal noise Foley (soft clicks, air sweeps and muted
impacts). No music, score, looped beat, instrument or pitched ambience is used.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import wave

import numpy as np

SAMPLE_RATE = 48_000


@dataclass(frozen=True)
class Cue:
    time: float
    kind: str
    gain: float = 1.0
    pan: float = 0.0


def read_wav_duration(path: Path) -> float:
    """Read a PCM WAV duration without needing ffprobe or another audio package."""
    with wave.open(str(path), "rb") as source:
        if source.getframerate() <= 0:
            raise ValueError(f"Invalid WAV sample rate: {path}")
        return source.getnframes() / source.getframerate()


def _moving_average(signal: np.ndarray, width: int) -> np.ndarray:
    if width <= 1:
        return signal.copy()
    width = min(width, max(1, signal.size))
    left = width // 2
    right = width - 1 - left
    padded = np.pad(signal, (left, right), mode="edge")
    integral = np.concatenate(([0.0], np.cumsum(padded, dtype=np.float64)))
    return ((integral[width:] - integral[:-width]) / width).astype(np.float32)


def _effect(kind: str, duration: float, seed: int) -> np.ndarray:
    """Create a single short, unpitched Foley cue; never a musical tone."""
    count = max(1, int(round(duration * SAMPLE_RATE)))
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(count).astype(np.float32)
    t = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    x = np.linspace(0.0, 1.0, count, dtype=np.float32)

    if kind in {"soft_click", "label_tick", "step_tick"}:
        # A small paper/wood-like tick: filtered noise with a quick natural decay.
        low = _moving_average(noise, 25)
        high = noise - _moving_average(noise, 7)
        decay = np.exp(-t / (0.025 if kind == "soft_click" else 0.018))
        signal = (0.42 * low + 0.42 * high) * decay
    elif kind == "muted_impact":
        # Short, soft impact made from noise only; deliberately no bell or note.
        low = _moving_average(noise, 115)
        high = noise - _moving_average(noise, 10)
        signal = 0.95 * low * np.exp(-t / 0.12) + 0.16 * high * np.exp(-t / 0.022)
    elif kind == "air_sweep":
        # A brief broadband transition with a single swell, not a tonal riser.
        low = _moving_average(noise, 62)
        high = noise - _moving_average(noise, 12)
        envelope = np.clip(np.sin(np.pi * x), 0.0, 1.0) ** 1.35
        signal = (0.56 * low + 0.44 * high) * envelope
    elif kind == "reverse_air":
        # Reversed-feeling filtered air cue to carry the visual back to the hook.
        low = _moving_average(noise, 74)
        high = noise - _moving_average(noise, 14)
        envelope = np.sin((np.pi / 2.0) * x) ** 1.65
        signal = (0.62 * low + 0.38 * high) * envelope
    else:
        raise ValueError(f"Unknown sound-effect cue: {kind}")

    signal -= float(np.mean(signal))
    peak = float(np.max(np.abs(signal))) if signal.size else 0.0
    if peak > 1e-8:
        signal *= 0.9 / peak
    return signal.astype(np.float32)


def _to_stereo(source: np.ndarray) -> np.ndarray:
    """Read a PCM WAV and resample it to the project's 48 kHz stereo bus."""
    with wave.open(str(source), "rb") as reader:
        channels = reader.getnchannels()
        sample_rate = reader.getframerate()
        width = reader.getsampwidth()
        frames = reader.readframes(reader.getnframes())

    if channels < 1 or sample_rate < 1:
        raise ValueError(f"Invalid WAV header: {source}")
    if width == 1:
        raw = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
        raw = (raw - 128.0) / 128.0
    elif width == 2:
        raw = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
    elif width == 3:
        packed = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
        values = (
            packed[:, 0].astype(np.int32)
            | (packed[:, 1].astype(np.int32) << 8)
            | (packed[:, 2].astype(np.int32) << 16)
        )
        values = np.where(values & 0x800000, values - 0x1000000, values)
        raw = values.astype(np.float32) / 8_388_608.0
    elif width == 4:
        raw = np.frombuffer(frames, dtype="<i4").astype(np.float32) / 2_147_483_648.0
    else:
        raise ValueError(f"Unsupported PCM sample width ({width} bytes): {source}")

    if raw.size % channels:
        raw = raw[: raw.size - (raw.size % channels)]
    audio = raw.reshape(-1, channels)
    if channels == 1:
        audio = np.repeat(audio, 2, axis=1)
    else:
        audio = audio[:, :2]
        if channels > 2:
            audio = np.column_stack((raw.reshape(-1, channels)[:, :channels].mean(axis=1),) * 2)

    if sample_rate != SAMPLE_RATE and audio.size:
        old_count = audio.shape[0]
        new_count = max(1, int(round(old_count * SAMPLE_RATE / sample_rate)))
        old_positions = np.arange(old_count, dtype=np.float64)
        new_positions = np.arange(new_count, dtype=np.float64) * sample_rate / SAMPLE_RATE
        audio = np.column_stack(
            [np.interp(new_positions, old_positions, audio[:, channel]) for channel in range(2)]
        ).astype(np.float32)
    return audio.astype(np.float32, copy=False)


def _fade_clip(clip: np.ndarray, fade_in: int, fade_out: int) -> np.ndarray:
    clip = clip.copy()
    if clip.size == 0:
        return clip
    fade_in = min(fade_in, clip.shape[0])
    fade_out = min(fade_out, clip.shape[0])
    if fade_in:
        clip[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)[:, None]
    if fade_out:
        clip[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)[:, None]
    return clip


def _cue_schedule(timing: dict[str, dict[str, float]], body_count: int) -> list[Cue]:
    """Key every audible cue to a corresponding visual reveal or transition."""
    cues = [Cue(0.035, "soft_click", gain=0.42, pan=0.0)]  # opening focus point

    problem = timing["agitation"]["start"]
    cues.append(Cue(problem + 0.04, "air_sweep", gain=0.33, pan=0.10))
    for index in range(3):
        cues.append(Cue(problem + 0.34 + index * 0.28, "label_tick", gain=0.22, pan=(-0.14 + index * 0.14)))

    for index in range(body_count):
        start = timing[f"body_{index + 1}"]["start"]
        cues.append(Cue(start + 0.30, "step_tick", gain=0.25, pan=(-0.10 if index % 2 == 0 else 0.10)))

    climax = timing["micro_climax"]["start"]
    for index in range(3):
        cues.append(Cue(climax + 0.42 + index * 0.36, "label_tick", gain=0.22, pan=(-0.16 + index * 0.16)))
    cues.append(Cue(climax + 1.52, "muted_impact", gain=0.26, pan=0.0))

    outro = timing["outro"]
    cues.append(Cue(outro["start"] + 0.30, "reverse_air", gain=0.28, pan=0.0))
    cues.append(Cue(max(outro["start"] + 0.55, outro["end"] - 0.90), "air_sweep", gain=0.20, pan=0.0))
    return [cue for cue in cues if cue.time < timing["outro"]["end"]]


def _ambient_texture(count: int) -> np.ndarray:
    """Very quiet, non-periodic air/room texture; no pitch, beat or tonal bed."""
    rng = np.random.default_rng(20261012)
    noise = rng.standard_normal(count).astype(np.float32)
    # Keep a soft air band and remove DC. This is texture, not a musical drone.
    air = noise - _moving_average(noise, 24)
    air /= max(float(np.max(np.abs(air))), 1e-8)
    stereo = np.column_stack((air, np.roll(air, 173))).astype(np.float32)
    return stereo * 0.0020


def build_audio_mix(
    timing: dict[str, dict[str, float]],
    voice_dir: Path,
    output_path: Path,
    body_count: int = 3,
    sample_rate: int = SAMPLE_RATE,
) -> None:
    """Mix scene voice clips above ducked procedural SFX; never adds music."""
    if sample_rate != SAMPLE_RATE:
        raise ValueError(f"The audio engine is designed for {SAMPLE_RATE} Hz, got {sample_rate} Hz")

    total_duration = timing["outro"]["end"]
    frame_count = int(np.ceil(total_duration * SAMPLE_RATE))
    speech_bus = np.zeros((frame_count, 2), dtype=np.float32)
    speech_presence = np.zeros(frame_count, dtype=np.float32)

    scene_names = ["hook", "agitation"] + [f"body_{i + 1}" for i in range(body_count)] + ["micro_climax", "outro"]
    for name in scene_names:
        clip_path = voice_dir / f"vo_{name}.wav"
        if not clip_path.exists():
            continue
        clip = _to_stereo(clip_path)
        if not clip.size:
            continue

        # Keep narration intelligible and comfortably below full scale.
        peak = float(np.max(np.abs(clip)))
        rms = float(np.sqrt(np.mean(np.square(clip))))
        if peak > 1e-7 and rms > 1e-7:
            gain = min(0.90 / peak, 0.145 / rms)
            clip *= gain
        clip = _fade_clip(clip, int(SAMPLE_RATE * 0.025), int(SAMPLE_RATE * 0.055))

        start = int(round((timing[name]["start"] + 0.22) * SAMPLE_RATE))
        end = min(frame_count, start + clip.shape[0])
        if start >= frame_count or end <= start:
            continue
        clip = clip[: end - start]
        speech_bus[start:end] += clip

        # Side-chain SFX under speech with short ramps at both ends.
        active_start = max(0, start - int(SAMPLE_RATE * 0.10))
        active_end = min(frame_count, end + int(SAMPLE_RATE * 0.16))
        speech_presence[active_start:active_end] = 1.0
        ramp = min(int(SAMPLE_RATE * 0.12), (active_end - active_start) // 2)
        if ramp:
            speech_presence[active_start : active_start + ramp] = np.linspace(0.0, 1.0, ramp, dtype=np.float32)
            speech_presence[active_end - ramp : active_end] = np.linspace(1.0, 0.0, ramp, dtype=np.float32)

    effects_bus = np.zeros((frame_count, 2), dtype=np.float32)
    for index, cue in enumerate(_cue_schedule(timing, body_count)):
        lengths = {
            "soft_click": 0.11,
            "label_tick": 0.09,
            "step_tick": 0.13,
            "muted_impact": 0.34,
            "air_sweep": 0.72,
            "reverse_air": 0.72,
        }
        mono = _effect(cue.kind, lengths[cue.kind], seed=3100 + index)
        pan = float(np.clip(cue.pan, -1.0, 1.0))
        left = np.sqrt((1.0 - pan) * 0.5)
        right = np.sqrt((1.0 + pan) * 0.5)
        stereo = np.column_stack((mono * left, mono * right)) * cue.gain
        start = int(round(cue.time * SAMPLE_RATE))
        end = min(frame_count, start + stereo.shape[0])
        if start < frame_count and end > start:
            effects_bus[start:end] += stereo[: end - start]

    # Subtle unpitched room air is kept well below dialogue and dips further under speech.
    ambient = _ambient_texture(frame_count)
    effects_bus *= (1.0 - 0.55 * speech_presence)[:, None]
    ambient *= (1.0 - 0.28 * speech_presence)[:, None]
    mixed = speech_bus + effects_bus + ambient

    # Gentle peak control protects the AAC encode without audible hard clipping.
    peak = float(np.max(np.abs(mixed))) if mixed.size else 0.0
    if peak > 0.94:
        mixed *= 0.94 / peak
    fade = min(int(SAMPLE_RATE * 0.28), mixed.shape[0])
    if fade:
        mixed[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(mixed, -1.0, 1.0)
    pcm16 = np.round(pcm * 32767.0).astype("<i2")
    with wave.open(str(output_path), "wb") as target:
        target.setnchannels(2)
        target.setsampwidth(2)
        target.setframerate(SAMPLE_RATE)
        target.writeframes(pcm16.tobytes())
