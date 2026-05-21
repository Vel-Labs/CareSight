#!/usr/bin/env python3
"""Stop the local CareSight Gemma endpoint."""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HUB_ROOT = REPO_ROOT / "apps" / "caresight-hub"
DEFAULT_PID_FILE = HUB_ROOT / "data" / "runtime" / "gemma-server.pid"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stop the local CareSight Gemma MLX endpoint.")
    parser.add_argument("--pid-file", type=Path, default=DEFAULT_PID_FILE)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    return parser.parse_args()


def pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def main() -> int:
    args = parse_args()
    try:
        pid = int(args.pid_file.read_text(encoding="utf-8").strip())
    except FileNotFoundError:
        print(f"gemma_not_running pid_file_missing={args.pid_file}")
        return 0
    except ValueError:
        print(f"gemma_stop_failed invalid_pid_file={args.pid_file}", file=sys.stderr)
        return 2

    if not pid_is_running(pid):
        args.pid_file.unlink(missing_ok=True)
        print(f"gemma_not_running stale_pid={pid} pid_file_removed={args.pid_file}")
        return 0

    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + args.timeout_seconds
    while time.monotonic() < deadline:
        if not pid_is_running(pid):
            args.pid_file.unlink(missing_ok=True)
            print(f"gemma_stopped pid={pid}")
            return 0
        time.sleep(0.25)

    os.kill(pid, signal.SIGKILL)
    args.pid_file.unlink(missing_ok=True)
    print(f"gemma_stopped_forced pid={pid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
