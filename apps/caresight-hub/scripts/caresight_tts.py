#!/usr/bin/env python3
"""Generate local CareSight TTS audio from bounded text."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HUB_ROOT = REPO_ROOT / "apps" / "caresight-hub"
DEFAULT_PYTHON = HUB_ROOT / ".venv" / "bin" / "python"
DEFAULT_MODEL = HUB_ROOT / "models" / "tts" / "holler" / "holler-0.6b-6bit"
DEFAULT_OUTPUT_DIR = HUB_ROOT / "data" / "tts"
DEFAULT_TEXT = "CareSight noted a possible floor stay in the living room. Please review when available."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate local CareSight TTS audio.")
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--text-file", type=Path, help="Read utterance text from a local file.")
    parser.add_argument("--voice", default="kit", help="Known local voices include kit, dakota, nora, joe, oliver, and tessa.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--file-prefix", default="caresight_tts")
    parser.add_argument("--max-tokens", type=int, default=96)
    parser.add_argument("--audio-format", default="wav")
    parser.add_argument("--play", action="store_true", help="Play audio locally after generation. Requires human approval.")
    parser.add_argument("--play-volume", type=float, default=6.0, help="afplay playback gain used with --play.")
    parser.add_argument("--play-repeat-count", type=int, default=1, help="Number of times to play the generated audio.")
    parser.add_argument(
        "--play-repeat-delay-seconds",
        type=float,
        default=1.0,
        help="Pause between repeated playback attempts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.python.exists():
        print(f"tts_failed python_missing={args.python}", file=sys.stderr)
        return 2
    if not args.model.exists():
        print(f"tts_failed model_missing={args.model}", file=sys.stderr)
        return 2

    text = args.text_file.read_text(encoding="utf-8").strip() if args.text_file else args.text.strip()
    if not text:
        print("tts_failed empty_text", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        str(args.python),
        "-m",
        "mlx_audio.tts.generate",
        "--model",
        str(args.model),
        "--text",
        text,
        "--voice",
        args.voice,
        "--max_tokens",
        str(args.max_tokens),
        "--output_path",
        str(args.output_dir),
        "--file_prefix",
        args.file_prefix,
        "--audio_format",
        args.audio_format,
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, text=True)
    if result.returncode != 0:
        print(f"tts_failed returncode={result.returncode}", file=sys.stderr)
        return result.returncode

    generated_path = newest_generated_audio(args.output_dir, args.file_prefix, args.audio_format)
    if args.play:
        if generated_path is None:
            print("tts_failed generated_audio_not_found", file=sys.stderr)
            return 2
        repeat_count = max(1, args.play_repeat_count)
        for index in range(repeat_count):
            playback = subprocess.run(["afplay", "-v", str(args.play_volume), str(generated_path)], check=False)
            if playback.returncode != 0:
                print(f"tts_playback_failed repeat={index + 1} returncode={playback.returncode}", file=sys.stderr)
                return playback.returncode
            if index + 1 < repeat_count and args.play_repeat_delay_seconds > 0:
                __import__("time").sleep(args.play_repeat_delay_seconds)

    print(
        f"tts_generated output_dir={args.output_dir} voice={args.voice} "
        f"played={str(args.play).lower()} play_volume={args.play_volume} "
        f"play_repeat_count={max(1, args.play_repeat_count)} "
        f"audio_path={generated_path or 'unknown'} model={args.model}"
    )
    return 0


def newest_generated_audio(output_dir: Path, file_prefix: str, audio_format: str) -> Path | None:
    candidates = sorted(
        output_dir.glob(f"{file_prefix}_*.{audio_format}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


if __name__ == "__main__":
    raise SystemExit(main())
