#!/usr/bin/env python3
"""Build local CareSight fixture/readiness receipts without live actions."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "apps" / "caresight-hub" / "scripts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Set up local CareSight fixtures/readiness receipts.")
    parser.add_argument("--skip-stack-check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    subprocess.run(["npm", "run", "check"], cwd=REPO_ROOT, check=True)
    if not args.skip_stack_check:
        subprocess.run(["python3", str(SCRIPTS / "caresight_stack_start.py")], cwd=REPO_ROOT, check=True)
        subprocess.run(["python3", str(SCRIPTS / "caresight_stack_stop.py")], cwd=REPO_ROOT, check=True)
    subprocess.run(["python3", str(SCRIPTS / "caresight_tts.py")], cwd=REPO_ROOT, check=True)
    print("setup_fixtures_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
