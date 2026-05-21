#!/usr/bin/env python3
"""Stop the local CareSight operator stack."""

from __future__ import annotations

import subprocess
import argparse
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "apps" / "caresight-hub" / "scripts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stop the local CareSight operator stack.")
    return parser.parse_args()


def main() -> int:
    parse_args()
    subprocess.run(["python3", str(SCRIPTS_DIR / "caresight_hermes_stop.py")], cwd=REPO_ROOT, text=True)
    subprocess.run(["python3", str(SCRIPTS_DIR / "caresight_gemma_stop.py")], cwd=REPO_ROOT, text=True)
    print("stack_stopped services=hermes,gemma")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
