#!/usr/bin/env python3
"""Install one ignored local CareSight model from Hugging Face."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HUB_ROOT = REPO_ROOT / "apps" / "caresight-hub"

MODELS = {
    "gemma-e2b": {
        "repo": "SanfranTroy/gemma4_e2b_q4_mlx_lm",
        "path": HUB_ROOT / "models" / "reasoning" / "gemma" / "gemma-4-e2b-it-4bit",
    },
    "gemma-e4b": {
        "repo": "mlx-community/gemma-4-e4b-it-4bit",
        "path": HUB_ROOT / "models" / "reasoning" / "gemma" / "gemma-4-e4b-it-4bit",
    },
    "holler-6bit": {
        "repo": "sentiuminc/holler-0.6b-6bit",
        "path": HUB_ROOT / "models" / "tts" / "holler" / "holler-0.6b-6bit",
    },
    "holler": {
        "repo": "sentiuminc/holler-0.6b",
        "path": HUB_ROOT / "models" / "tts" / "holler" / "holler-0.6b",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install one local CareSight model.")
    parser.add_argument("model", choices=sorted(MODELS))
    parser.add_argument("--force", action="store_true", help="Pass through to huggingface-cli download.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec = MODELS[args.model]
    target = Path(spec["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "huggingface-cli",
        "download",
        spec["repo"],
        "--local-dir",
        str(target),
        "--local-dir-use-symlinks",
        "False",
    ]
    if args.force:
        command.append("--force-download")
    subprocess.run(command, cwd=REPO_ROOT, check=True)
    print(f"model_installed model={args.model} repo={spec['repo']} path={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
