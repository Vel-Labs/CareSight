#!/usr/bin/env python3
"""Clear the local CareSight Hermes readiness marker."""

from __future__ import annotations

import argparse
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HUB_ROOT = REPO_ROOT / "apps" / "caresight-hub"
DEFAULT_STATUS_FILE = HUB_ROOT / "data" / "runtime" / "hermes-ready.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clear the local CareSight Hermes readiness marker.")
    parser.add_argument("--status-file", type=Path, default=DEFAULT_STATUS_FILE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.status_file.exists():
        args.status_file.unlink()
        print(f"hermes_stopped status_file_removed={args.status_file}")
    else:
        print(f"hermes_not_running status_file_missing={args.status_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
