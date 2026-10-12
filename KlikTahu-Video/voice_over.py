"""
voice_over.py — pembuat narasi (voice-over) untuk KlikTahu Video Engine.

Menghasilkan satu file per beat ke folder `narration/`:
    narration/01_hook.mp3        (audio)
    narration/01_hook.json       (opsional: timing per kata)

Timing kata diambil dari metadata WordBoundary edge-tts, dipakai engine untuk
menyalakan sorotan kata TEPAT saat kata itu diucapkan. Bila file .json tidak
ada, engine tetap jalan dengan pembagian waktu menurut panjang kata.

Jalankan (butuh koneksi internet):
    python voice_over.py                # semua beat
    python voice_over.py --only hook    # satu beat saja
    python voice_over.py --voice id-ID-GadisNeural
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from script_kliktahu import BEATS, VOICE_ID

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "narration"
SR = 48_000


def _require_edge_tts():
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        raise SystemExit(
            "edge-tts belum terpasang. Jalankan: pip install edge-tts\n"
            "atau pakai narration/ yang sudah ada di repo.")
    import edge_tts
    return edge_tts


async def synth_one(index: int, key: str, text: str, voice: str, rate: str,
                    volume: str, out_dir: Path) -> dict:
    edge_tts = _require_edge_tts()
    stem = f"{index + 1:02d}_{key}"
    mp3_path = out_dir / f"{stem}.mp3"
    json_path = out_dir / f"{stem}.json"

    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    words: list[dict] = []
    with open(mp3_path, "wb") as fh:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                fh.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append(dict(
                    word=chunk["text"],
                    offset_ms=int(chunk["offset"] / 10_000),      # 100ns -> ms
                    duration_ms=int(chunk["duration"] / 10_000),
                ))
    json_path.write_text(json.dumps(dict(voice=voice, rate=rate, text=text,
                                         words=words), ensure_ascii=False, indent=1))
    print(f"  [{stem}] {len(words):2d} kata -> {mp3_path.name} "
          f"({mp3_path.stat().st_size / 1024:.0f} KB)")
    return dict(stem=stem, words=words)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Pembuat voice-over KlikTahu")
    ap.add_argument("--voice", default=VOICE_ID, help="nama suara edge-tts")
    ap.add_argument("--rate", default="+9%", help="kecepatan bicara")
    ap.add_argument("--volume", default="+0%")
    ap.add_argument("--only", default=None, help="hanya beat dengan key tertentu")
    ap.add_argument("--out", default=str(OUT_DIR))
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    beats = [b for b in BEATS if args.only in (None, b["key"])]
    if not beats:
        raise SystemExit(f"[vo] tidak ada beat dengan key {args.only!r}")

    print(f"[vo] suara={args.voice} rate={args.rate} -> {out_dir}")

    async def run():
        for i, spec in enumerate(BEATS):
            if args.only not in (None, spec["key"]):
                continue
            await synth_one(i, spec["key"], spec["vo"], args.voice, args.rate,
                            args.volume, out_dir)

    try:
        asyncio.run(run())
    except Exception as exc:                      # jaringan diblokir / DNS gagal
        print(f"[vo] GAGAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("[vo] Periksa koneksi internet. Bila server tanpa internet, video "
              "tetap bisa dirender memakai narration/ yang ada di repo.", file=sys.stderr)
        return 2
    print("[vo] selesai")
    return 0


if __name__ == "__main__":
    sys.exit(main())
