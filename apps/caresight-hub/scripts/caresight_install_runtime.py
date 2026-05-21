#!/usr/bin/env python3
"""Install the local CareSight Python runtime."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HUB_ROOT = REPO_ROOT / "apps" / "caresight-hub"
DEFAULT_VENV = HUB_ROOT / ".venv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the ignored local CareSight runtime venv.")
    parser.add_argument("--venv", type=Path, default=DEFAULT_VENV)
    return parser.parse_args()


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    args = parse_args()
    if not (args.venv / "bin" / "python").exists():
        run([sys.executable, "-m", "venv", str(args.venv)])
    python = args.venv / "bin" / "python"
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "mlx-lm",
            "mlx-vlm",
            "mlx-audio",
            "fastapi",
            "uvicorn",
            "soundfile",
            "obsws-python",
            "huggingface_hub[cli]",
        ]
    )
    print(f"runtime_installed venv={args.venv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
