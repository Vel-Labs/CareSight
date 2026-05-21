#!/usr/bin/env python3
"""Install or verify OBS for local visual handoff."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


OBS_APP = Path("/Applications/OBS.app")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install or verify OBS.")
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if OBS_APP.exists():
        print(f"obs_installed path={OBS_APP}")
        return 0
    if args.check_only:
        print(f"obs_missing path={OBS_APP}")
        return 1
    brew = shutil.which("brew")
    if brew is None:
        print("obs_install_failed reason=homebrew_missing install_manually=https://obsproject.com/download")
        return 1
    subprocess.run([brew, "install", "--cask", "obs"], check=True)
    print(f"obs_installed path={OBS_APP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
