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
    if args.play:
        command.append("--play")

    result = subprocess.run(command, cwd=REPO_ROOT, text=True)
    if result.returncode != 0:
        print(f"tts_failed returncode={result.returncode}", file=sys.stderr)
        return result.returncode

    print(
        f"tts_generated output_dir={args.output_dir} voice={args.voice} "
        f"played={str(args.play).lower()} model={args.model}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
