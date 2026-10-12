"""Optional AI-assisted story and Indonesian voice-over generation.

No API key is embedded or read from a file. Network calls happen only when the
user explicitly requests --ai and/or --voiceover; the default project story
renders offline from story.json and the included narration clips.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_STORY_PATH = ROOT / "story.json"
DEFAULT_VOICE_DIR = ROOT / "audio"

# Keep the provider model configurable because model availability varies by account.
# Override with OPENAI_MODEL if a different current model is enabled for your account.
DEFAULT_MODEL = "gpt-6-astra"
DEFAULT_TTS_MODEL = "gpt-4o-mini-tts"
DEFAULT_TTS_VOICE = "echo"


STORY_INSTRUCTIONS = """You are an Indonesian short-form cinematic story editor.
Return one valid JSON object only, with no Markdown fences or commentary. Follow
this exact narrative order and keep the language natural, specific, and concise:
The Hook, The Agitation / The Problem, three progressive value beats, The
Micro-Climax, then a Seamless Outro that echoes the opening question. The three
value beats must each reveal only one actionable idea. The Micro-Climax must
connect all three beats into one visual payoff. Do not invent statistics or make
unsupported factual claims. The outro must lead naturally back to the hook.

The JSON schema is:
{
  "topic": "string",
  "hook": {"headline": ["short line", "short line"], "narration": "one short sentence", "caption": "concise subtitle"},
  "agitation": {"headline": ["short line", "short line"], "labels": ["short label", "short label", "short label"], "narration": "one or two short sentences", "caption": "concise subtitle"},
  "body": [
    {"title": "short card title", "support": "one short supporting thought", "narration": "one short sentence", "caption": "concise subtitle"},
    {"title": "short card title", "support": "one short supporting thought", "narration": "one short sentence", "caption": "concise subtitle"},
    {"title": "short card title", "support": "one short supporting thought", "narration": "one short sentence", "caption": "concise subtitle"}
  ],
  "micro_climax": {"headline": ["short line", "short line", "short line"], "nodes": ["short label", "short label", "short label"], "narration": "one short sentence tying the three beats together", "caption": "concise subtitle"},
  "outro": {"narration": "one short question that loops toward the hook", "caption": "concise subtitle"}
}
Keep each body title under 32 characters, each supporting thought under 58,
each caption under 90, and each narration section under about 30 words. Write
all visible copy and narration in Bahasa Indonesia. The hook should open a
curiosity gap; the problem should make the tension recognizable; the value
should progressively resolve it; the payoff should feel earned; and the outro
should echo the hook without adding a new topic."""


def _client() -> Any:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "Set OPENAI_API_KEY in your local environment or GitHub Actions secret; "
            "this project never stores API keys in source files."
        )
    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError("Install the project dependencies first: pip install -r requirements.txt") from error
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def load_story(path: str | Path = DEFAULT_STORY_PATH) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream:
        story = json.load(stream)
    from cinematic_engine import validate_story

    validate_story(story)
    return story


def save_story(story: dict[str, Any], path: str | Path = DEFAULT_STORY_PATH) -> Path:
    from cinematic_engine import validate_story

    validate_story(story)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(story, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination


def generate_cinematic_script(topic: str, model: str | None = None) -> dict[str, Any]:
    """Generate a strict five-part story with the currently configured text model."""
    from cinematic_engine import validate_story

    selected_model = model or os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
    response = _client().responses.create(
        model=selected_model,
        input=[
            {"role": "system", "content": STORY_INSTRUCTIONS},
            {"role": "user", "content": f"Buat video pendek cinematic bertopik: {topic}"},
        ],
        text={"format": {"type": "json_object"}},
    )
    output = getattr(response, "output_text", "")
    if not output:
        raise RuntimeError("The model returned no story text.")
    try:
        story = json.loads(output)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"The model response was not valid JSON: {error}") from error
    validate_story(story)
    story["topic"] = topic
    return story


def narration_segments(story: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("hook", story["hook"]["narration"]),
        ("agitation", story["agitation"]["narration"]),
        *[(f"body_{index + 1}", point["narration"]) for index, point in enumerate(story["body"])],
        ("micro_climax", story["micro_climax"]["narration"]),
        ("outro", story["outro"]["narration"]),
    ]


def generate_voice_over(story: dict[str, Any], output_dir: str | Path = DEFAULT_VOICE_DIR,
                        model: str | None = None, voice: str | None = None) -> list[Path]:
    """Generate one dialogue-only WAV per beat to keep picture and speech aligned."""
    selected_model = model or os.environ.get("OPENAI_TTS_MODEL", DEFAULT_TTS_MODEL)
    selected_voice = voice or os.environ.get("OPENAI_TTS_VOICE", DEFAULT_TTS_VOICE)
    client = _client()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for name, text in narration_segments(story):
        target = destination / f"vo_{name}.wav"
        speech = client.audio.speech.create(
            model=selected_model,
            voice=selected_voice,
            input=text,
            instructions=(
                "Narrate in clear, natural Bahasa Indonesia. Warm, intimate documentary voice; "
                "measured pacing, thoughtful pauses, calm confidence, no theatrical exaggeration."
            ),
            response_format="wav",
        )
        speech.stream_to_file(str(target))
        saved.append(target)
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an optional AI script and Indonesian voice-over.")
    parser.add_argument("--topic", default=None, help="Topic for an AI-generated story.")
    parser.add_argument("--ai", action="store_true", help="Generate a fresh story with OPENAI_MODEL.")
    parser.add_argument("--voiceover", action="store_true",
                        help="Generate scene-aligned speech WAVs with OPENAI_TTS_MODEL.")
    parser.add_argument("--story", type=Path, default=DEFAULT_STORY_PATH, help="Story JSON path.")
    parser.add_argument("--voice-dir", type=Path, default=DEFAULT_VOICE_DIR, help="Narration WAV folder.")
    parser.add_argument("--model", default=None, help="Override OPENAI_MODEL for this run.")
    parser.add_argument("--tts-model", default=None, help="Override OPENAI_TTS_MODEL for this run.")
    parser.add_argument("--voice", default=None, help="Override OPENAI_TTS_VOICE for this run.")
    args = parser.parse_args()

    story = load_story(args.story)
    if args.ai:
        topic = args.topic or story.get("topic", "video pendek cinematic")
        model = args.model or os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
        print(f"[KlikTahu] Generating Indonesian story with {model}…")
        story = generate_cinematic_script(topic, model=model)
        save_story(story, args.story)
        print(f"[KlikTahu] Story saved: {args.story}")
    elif args.topic:
        parser.error("--topic is used with --ai; use --ai --topic \"...\" to generate a new story.")

    if args.voiceover:
        model = args.tts_model or os.environ.get("OPENAI_TTS_MODEL", DEFAULT_TTS_MODEL)
        print(f"[KlikTahu] Generating dialogue-only Indonesian VO with {model}…")
        clips = generate_voice_over(story, args.voice_dir, model=model, voice=args.voice)
        print(f"[KlikTahu] Saved {len(clips)} scene-aligned WAV clips to {args.voice_dir}")

    if not args.ai and not args.voiceover:
        print(f"Topic: {story.get('topic', '(untitled)')}")
        print("Use --ai and/or --voiceover to explicitly request API generation.")
        print("No network request is made by this command without those flags.")


if __name__ == "__main__":
    main()
