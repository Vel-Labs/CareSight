#!/usr/bin/env python3
"""Install the default ignored local CareSight model set."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "apps" / "caresight-hub" / "scripts" / "caresight_install_model.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install local CareSight models.")
    parser.add_argument("--include-larger", action="store_true", help="Also install Gemma E4B and Holler bf16 fallback.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    models = ["gemma-e2b", "holler-6bit"]
    if args.include_larger:
        models.extend(["gemma-e4b", "holler"])
    for model in models:
        subprocess.run(["python3", str(SCRIPT), model], cwd=REPO_ROOT, check=True)
    print(f"models_installed models={','.join(models)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
