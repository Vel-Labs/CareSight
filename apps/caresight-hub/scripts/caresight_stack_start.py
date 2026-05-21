#!/usr/bin/env python3
"""Start the local CareSight operator stack."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "apps" / "caresight-hub" / "scripts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the local CareSight operator stack.")
    parser.add_argument("--skip-gemma", action="store_true")
    parser.add_argument("--skip-hermes", action="store_true")
    return parser.parse_args()


def run_step(name: str, command: list[str]) -> None:
    print(f"stack_step_start name={name}", flush=True)
    result = subprocess.run(command, cwd=REPO_ROOT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"stack_step_failed name={name} returncode={result.returncode}")
    print(f"stack_step_done name={name}", flush=True)


def main() -> int:
    args = parse_args()
    try:
        if not args.skip_gemma:
            run_step("gemma", ["python3", str(SCRIPTS_DIR / "caresight_gemma_start.py")])
        if not args.skip_hermes:
            hermes_command = ["python3", str(SCRIPTS_DIR / "caresight_hermes_start.py")]
            if not args.skip_gemma:
                hermes_command.append("--require-gemma")
            run_step("hermes", hermes_command)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("stack_started services=gemma,hermes", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
