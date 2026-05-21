#!/usr/bin/env python3
"""Install the local CareSight demo prerequisites."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "apps" / "caresight-hub" / "scripts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install local CareSight prerequisites.")
    parser.add_argument("--skip-models", action="store_true")
    parser.add_argument("--skip-obs", action="store_true")
    parser.add_argument("--include-larger-models", action="store_true")
    return parser.parse_args()


def run(script: str, *extra: str) -> None:
    subprocess.run(["python3", str(SCRIPTS / script), *extra], cwd=REPO_ROOT, check=True)


def main() -> int:
    args = parse_args()
    run("caresight_install_runtime.py")
    if not args.skip_models:
        model_args = ["--include-larger"] if args.include_larger_models else []
        run("caresight_install_models.py", *model_args)
    if not args.skip_obs:
        run("caresight_install_obs.py")
    print("install_all_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
