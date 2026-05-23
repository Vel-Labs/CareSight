#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_CONFIG = ROOT / "config" / "tapo-runtime.local.json"
DEFAULT_PYTHON = ROOT / "vendor" / "yolo-mlx" / ".venv" / "bin" / "python"
DEFAULT_LOG_DIR = ROOT / "data" / "runtime"
DEFAULT_CAMERA_PORTS = ["tapo_living_room:8766", "tapo_kitchen:8767"]


def parse_camera_port(value: str) -> tuple[str, int]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("expected <camera_id>:<port>")
    camera_id, raw_port = value.rsplit(":", 1)
    if not camera_id.strip():
        raise argparse.ArgumentTypeError("camera_id cannot be empty")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if port <= 0:
        raise argparse.ArgumentTypeError("port must be positive")
    return camera_id.strip(), port


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start detached CareSight YOLO26 detector feeds for OBS.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Ignored local runtime config with camera credentials.")
    parser.add_argument(
        "--camera",
        action="append",
        type=parse_camera_port,
        default=[],
        help="Camera feed to start as <camera_id>:<port>. Repeat for multiple cameras.",
    )
    parser.add_argument("--python", default=str(DEFAULT_PYTHON), help="Python runtime with YOLO26/OpenCV dependencies.")
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR), help="Directory for detached detector PID and log files.")
    parser.add_argument("--wait-seconds", type=float, default=12.0, help="Wait this long for each detector health endpoint.")
    parser.add_argument("--appearance-overlay", action="store_true", help="Draw clothing descriptor sub-boxes on person detections.")
    parser.add_argument("--stop-existing", action="store_true", help="Stop matching PID-file processes before starting.")
    return parser.parse_args()


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop_existing(pid_path: Path) -> dict[str, object] | None:
    if not pid_path.exists():
        return None
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except ValueError:
        pid_path.unlink(missing_ok=True)
        return {"status": "stale_pid_removed"}
    if not process_alive(pid):
        pid_path.unlink(missing_ok=True)
        return {"pid": pid, "status": "not_running"}
    os.kill(pid, signal.SIGTERM)
    for _ in range(20):
        if not process_alive(pid):
            pid_path.unlink(missing_ok=True)
            return {"pid": pid, "status": "stopped"}
        time.sleep(0.1)
    return {"pid": pid, "status": "still_running_after_sigterm"}


def wait_for_health(port: int, timeout_seconds: float) -> dict[str, object]:
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1.0) as response:
                payload = json.loads(response.read().decode("utf-8"))
                if response.status == 200 and bool(payload.get("frame_available")):
                    return {"ok": True, "payload": payload, "url": url}
                last_error = "health endpoint reachable but no detector frame is available yet"
        except Exception as exc:  # noqa: BLE001 - receipt should preserve concrete blocker.
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(0.4)
    return {"ok": False, "error": last_error, "url": url}


def start_detector(args: argparse.Namespace, camera_id: str, port: int) -> dict[str, object]:
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    safe_camera_id = camera_id.replace("/", "_")
    pid_path = log_dir / f"{safe_camera_id}_detector.pid"
    log_path = log_dir / f"{safe_camera_id}_detector.log"
    stopped = stop_existing(pid_path) if args.stop_existing else None
    command = [
        args.python,
        str(ROOT / "scripts" / "v0_floor_stay_live.py"),
        "--config",
        args.config,
        "--camera-id",
        camera_id,
        "--obs-browser-feed",
        "--obs-browser-feed-port",
        str(port),
        "--no-window",
    ]
    if args.appearance_overlay:
        command.append("--appearance-overlay")

    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    with log_path.open("wb") as log_handle:
        process = subprocess.Popen(
            command,
            cwd=REPO_ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    pid_path.write_text(f"{process.pid}\n", encoding="utf-8")
    health = wait_for_health(port, args.wait_seconds)
    return {
        "camera_id": camera_id,
        "feed_url": f"http://127.0.0.1:{port}/live.html",
        "health": health,
        "log_path": str(log_path),
        "pid": process.pid,
        "pid_path": str(pid_path),
        "port": port,
        "stopped_existing": stopped,
        "stream_url": f"http://127.0.0.1:{port}/stream.mjpg",
    }


def main() -> int:
    args = parse_args()
    cameras = args.camera or [parse_camera_port(value) for value in DEFAULT_CAMERA_PORTS]
    results = [start_detector(args, camera_id, port) for camera_id, port in cameras]
    payload = {
        "appearance_overlay": args.appearance_overlay,
        "feeds": results,
        "ready": all(bool(result["health"].get("ok")) for result in results),
        "schema": "caresight-detector-start-receipt",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
