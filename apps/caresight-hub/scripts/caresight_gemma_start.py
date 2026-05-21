#!/usr/bin/env python3
"""Start the local CareSight Gemma endpoint."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HUB_ROOT = REPO_ROOT / "apps" / "caresight-hub"
DEFAULT_PYTHON = HUB_ROOT / ".venv" / "bin" / "python"
DEFAULT_MODEL = HUB_ROOT / "models" / "reasoning" / "gemma" / "gemma-4-e2b-it-4bit"
RUNTIME_DIR = HUB_ROOT / "data" / "runtime"
DEFAULT_PID_FILE = RUNTIME_DIR / "gemma-server.pid"
DEFAULT_LOG_FILE = RUNTIME_DIR / "gemma-server.log"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the local CareSight Gemma MLX endpoint.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--pid-file", type=Path, default=DEFAULT_PID_FILE)
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE)
    parser.add_argument("--max-tokens", type=int, default=96)
    parser.add_argument("--max-kv-size", type=int, default=1024)
    parser.add_argument("--kv-bits", default="4")
    parser.add_argument("--kv-quant-scheme", default="uniform")
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    parser.add_argument("--foreground", action="store_true", help="Run in the foreground.")
    return parser.parse_args()


def pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_existing_pid(path: Path) -> int | None:
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None
    return pid if pid_is_running(pid) else None


def wait_until_ready(host: str, port: int, model: str, timeout_seconds: float) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    url = f"http://{host}:{port}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Reply with exactly: caresight_gemma_ready",
            }
        ],
        "max_tokens": 16,
        "temperature": 0,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    last_error = "not_attempted"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                data = json.loads(response.read().decode("utf-8"))
            return {"ready": True, "response": data}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            time.sleep(1)
    return {"ready": False, "error": last_error}


def main() -> int:
    args = parse_args()
    args.pid_file.parent.mkdir(parents=True, exist_ok=True)
    args.log_file.parent.mkdir(parents=True, exist_ok=True)

    if not args.python.exists():
        print(f"gemma_start_failed python_missing={args.python}", file=sys.stderr)
        return 2
    if not args.model.exists():
        print(f"gemma_start_failed model_missing={args.model}", file=sys.stderr)
        return 2

    existing_pid = read_existing_pid(args.pid_file)
    if existing_pid is not None:
        print(
            f"gemma_already_running pid={existing_pid} base_url=http://{args.host}:{args.port}/v1 "
            f"pid_file={args.pid_file}"
        )
        return 0

    command = [
        str(args.python),
        "-m",
        "mlx_vlm.server",
        "--model",
        str(args.model),
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--max-tokens",
        str(args.max_tokens),
        "--max-kv-size",
        str(args.max_kv_size),
        "--kv-bits",
        str(args.kv_bits),
        "--kv-quant-scheme",
        args.kv_quant_scheme,
    ]

    if args.foreground:
        print(f"gemma_starting_foreground base_url=http://{args.host}:{args.port}/v1")
        return subprocess.call(command, cwd=REPO_ROOT)

    with args.log_file.open("ab") as log:
        process = subprocess.Popen(
            command,
            cwd=REPO_ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    args.pid_file.write_text(f"{process.pid}\n", encoding="utf-8")
    readiness = wait_until_ready(args.host, args.port, str(args.model), args.timeout_seconds)
    if not readiness["ready"]:
        try:
            os.kill(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        args.pid_file.unlink(missing_ok=True)
        print(
            "gemma_start_failed "
            f"pid={process.pid} base_url=http://{args.host}:{args.port}/v1 "
            f"log_file={args.log_file} error={readiness.get('error')}",
            file=sys.stderr,
        )
        return 1

    print(
        f"gemma_started pid={process.pid} base_url=http://{args.host}:{args.port}/v1 "
        f"model={args.model} pid_file={args.pid_file} log_file={args.log_file}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
