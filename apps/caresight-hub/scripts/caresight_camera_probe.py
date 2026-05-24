#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT_DIR.parents[1]
sys.path.insert(0, str(ROOT_DIR))
from caresight.runtime.validation import build_runtime_validation_receipt, current_timestamp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe one explicit local CareSight camera source.")
    parser.add_argument("--config", required=True, help="Ignored local camera config JSON.")
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--dry-run", action="store_true", help="Parse and redact config without opening the stream.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started_at = current_timestamp()
    camera = _load_camera(Path(args.config))
    parsed = urlparse(str(camera["source_uri"]))
    redacted_uri = _redact_uri(str(camera["source_uri"]))
    receipt = {
        "schema": "camera-probe-receipt",
        "camera_id": camera["camera_id"],
        "source_type": camera["source_type"],
        "room_id": camera.get("room_id"),
        "room_label": camera.get("room_label"),
        "redacted_uri": redacted_uri,
        "reachable": "not_attempted",
        "stream_opened": "not_attempted",
        "first_frame_received": "not_attempted",
        "width": None,
        "height": None,
        "fps": None,
        "blocker": None,
    }
    if args.dry_run:
        print(json.dumps(_runtime_receipt(receipt, args=args, started_at=started_at), indent=2, sort_keys=True))
        return

    if camera["source_type"] == "rtsp":
        receipt["reachable"] = _tcp_reachable(parsed.hostname, parsed.port or 554, args.timeout_seconds)
    try:
        import cv2
    except ModuleNotFoundError as error:
        if error.name != "cv2":
            raise
        receipt["stream_opened"] = False
        receipt["first_frame_received"] = False
        receipt["blocker"] = "missing_cv2"
        receipt["error"] = "OpenCV is not installed for this Python interpreter."
        receipt["next_command"] = (
            "apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python "
            "apps/caresight-hub/scripts/caresight_camera_probe.py --config <this-file>"
        )
    else:
        try:
            capture = cv2.VideoCapture(str(camera["source_uri"]))
            capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, int(args.timeout_seconds * 1000))
            capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, int(args.timeout_seconds * 1000))
            opened = bool(capture.isOpened())
            receipt["stream_opened"] = opened
            if opened:
                ok, _frame = capture.read()
                receipt["first_frame_received"] = bool(ok)
                receipt["width"] = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0) or None
                receipt["height"] = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0) or None
                receipt["fps"] = float(capture.get(cv2.CAP_PROP_FPS) or 0) or None
            else:
                receipt["blocker"] = "stream_open_failed"
            capture.release()
        except Exception as error:
            receipt["stream_opened"] = False
            receipt["first_frame_received"] = False
            receipt["blocker"] = "probe_error"
            receipt["error"] = str(error)
    print(json.dumps(_runtime_receipt(receipt, args=args, started_at=started_at), indent=2, sort_keys=True))


def _load_camera(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    camera = data.get("camera", data)
    if not isinstance(camera, dict):
        raise ValueError("camera config must be a JSON object")
    if camera.get("source_type") != "rtsp":
        raise ValueError("camera probe currently supports explicit local rtsp configs")
    return camera


def _redact_uri(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.username or parsed.password:
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return urlunparse((parsed.scheme, f"***:***@{host}", parsed.path, "", parsed.query, ""))
    return uri


def _tcp_reachable(hostname: str | None, port: int, timeout: float) -> bool:
    if not hostname:
        return False


def _runtime_receipt(receipt: dict, *, args: argparse.Namespace, started_at: str) -> dict[str, object]:
    blocked = []
    if receipt.get("blocker"):
        blocked.append({"code": str(receipt["blocker"]), "detail": str(receipt.get("error") or receipt.get("blocker"))})
    if receipt.get("first_frame_received") is False:
        blocked.append({"code": "first_frame_missing", "detail": "camera stream did not return a frame"})
    status = "not_attempted" if args.dry_run else ("blocked" if blocked else "pass")
    return build_runtime_validation_receipt(
        check_type="camera_probe",
        target=str(receipt.get("camera_id") or "camera"),
        command=f"python {Path(__file__).resolve().relative_to(REPO_ROOT)} --config {args.config}"
        + (" --dry-run" if args.dry_run else ""),
        status=status,
        started_at=started_at,
        result=receipt,
        blockers=blocked,
        safety_boundaries=["local_probe_only", "redacted_output", "no_live_send", "no_facetime_call", "no_tts_playback"],
    )
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    main()
