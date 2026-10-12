from __future__ import annotations

import json
from pathlib import Path
import unittest
import wave

import numpy as np

from audio_engine import _ambient_texture, _cue_schedule, _effect, read_wav_duration
from cinematic_engine import CinematicVideoPipeline, validate_story

ROOT = Path(__file__).resolve().parents[1]


class StoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.story = json.loads((ROOT / "story.json").read_text(encoding="utf-8"))

    def test_default_story_has_the_required_narrative_order(self) -> None:
        validate_story(self.story)
        self.assertEqual(len(self.story["body"]), 3)
        self.assertTrue(self.story["hook"]["headline"])
        self.assertEqual(self.story["micro_climax"]["nodes"], ["SATU IDE", "URUTAN", "JEDA"])

    def test_incomplete_story_is_rejected_before_render(self) -> None:
        story = json.loads(json.dumps(self.story))
        story["body"].pop()
        with self.assertRaisesRegex(ValueError, "exactly three"):
            validate_story(story)

    def test_timeline_has_positive_scene_lengths_in_story_order(self) -> None:
        pipeline = CinematicVideoPipeline(self.story, preview=True, voice_dir=ROOT / "missing-audio")
        expected = ["hook", "agitation", "body_1", "body_2", "body_3", "micro_climax", "outro"]
        self.assertEqual(list(pipeline.timing), expected)
        self.assertTrue(all(item["duration"] > 0 for item in pipeline.timing.values()))
        self.assertAlmostEqual(pipeline.duration, sum(item["duration"] for item in pipeline.timing.values()))

    def test_last_frame_matches_the_hook_for_a_visual_loop(self) -> None:
        pipeline = CinematicVideoPipeline(self.story, preview=True, voice_dir=ROOT / "missing-audio")
        first = pipeline._frame_at(0.0)
        last = pipeline._frame_at(pipeline.duration - 1.0 / pipeline.fps)
        self.assertEqual(first.size, (540, 960))
        self.assertEqual(first.tobytes(), last.tobytes())

    def test_scene_aligned_indonesian_voice_clips_are_present(self) -> None:
        pipeline = CinematicVideoPipeline(self.story, voice_dir=ROOT / "audio")
        for scene in pipeline.timing:
            clip = ROOT / "audio" / f"vo_{scene}.wav"
            self.assertTrue(clip.is_file(), f"Missing narration clip: {clip.name}")
            self.assertGreater(read_wav_duration(clip), 0.5)
            with wave.open(str(clip), "rb") as audio:
                self.assertEqual(audio.getnchannels(), 1)
                self.assertEqual(audio.getsampwidth(), 2)
                samples = np.frombuffer(audio.readframes(audio.getnframes()), dtype="<i2")
                self.assertGreater(int(np.max(np.abs(samples))), 500)


class SoundDesignTests(unittest.TestCase):
    def test_effects_and_ambient_texture_are_finite_and_nonempty(self) -> None:
        kinds = ("soft_click", "label_tick", "step_tick", "muted_impact", "air_sweep", "reverse_air")
        for index, kind in enumerate(kinds):
            cue = _effect(kind, 0.4, 100 + index)
            self.assertGreater(float(np.max(np.abs(cue))), 0.0)
            self.assertTrue(np.isfinite(cue).all())
        ambience = _ambient_texture(48_000)
        self.assertTrue(np.isfinite(ambience).all())
        self.assertLess(float(np.max(np.abs(ambience))), 0.01)

    def test_sound_cues_are_scene_synced_and_contain_no_music_track(self) -> None:
        names = ["hook", "agitation", "body_1", "body_2", "body_3", "micro_climax", "outro"]
        timing = {}
        start = 0.0
        for name in names:
            timing[name] = {"start": start, "end": start + 4.0, "duration": 4.0}
            start += 4.0
        cues = _cue_schedule(timing, body_count=3)
        self.assertGreaterEqual(len(cues), 12)
        self.assertNotIn("music", {cue.kind for cue in cues})
        self.assertTrue(all(cue.time >= 0 for cue in cues))


if __name__ == "__main__":
    unittest.main()
