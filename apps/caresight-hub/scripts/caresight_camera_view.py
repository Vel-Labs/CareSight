#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open one owner-authorized local RTSP camera preview window.")
    parser.add_argument("--config", required=True, help="Ignored local camera config JSON.")
    parser.add_argument("--window-title", default="CareSight Camera Preview")
    parser.add_argument("--max-seconds", type=float, default=0.0, help="Optional time limit; 0 means until q/Esc.")
    parser.add_argument("--save-frame", help="Optional ignored local path for one preview frame.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    camera = _load_camera(Path(args.config))
    try:
        import cv2
    except ModuleNotFoundError as error:
        if error.name != "cv2":
            raise
        raise SystemExit(
            "missing_cv2: run with apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python "
            "apps/caresight-hub/scripts/caresight_camera_view.py --config <local-config>"
        ) from error

    capture = cv2.VideoCapture(str(camera["source_uri"]))
    capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
    capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
    if not capture.isOpened():
        raise SystemExit(f"stream_open_failed: {_redact_uri(str(camera['source_uri']))}")

    started_at = time.monotonic()
    saved_frame = False
    receipt = {
        "schema": "camera-view-receipt",
        "camera_id": camera["camera_id"],
        "room_id": camera.get("room_id"),
        "room_label": camera.get("room_label"),
        "redacted_uri": _redact_uri(str(camera["source_uri"])),
        "frames_shown": 0,
        "save_frame": bool(args.save_frame),
        "saved_frame": False,
    }
    cv2.namedWindow(args.window_title, cv2.WINDOW_NORMAL)
    try:
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                receipt["blocker"] = "frame_read_failed"
                break
            receipt["frames_shown"] += 1
            if args.save_frame and not saved_frame:
                output = Path(args.save_frame)
                output.parent.mkdir(parents=True, exist_ok=True)
                receipt["saved_frame"] = bool(cv2.imwrite(str(output), frame))
                saved_frame = True
            cv2.imshow(args.window_title, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in {ord("q"), 27}:
                receipt["exit_reason"] = "operator_requested"
                break
            if args.max_seconds > 0 and time.monotonic() - started_at >= args.max_seconds:
                receipt["exit_reason"] = "max_seconds"
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()
    print(json.dumps(receipt, indent=2, sort_keys=True))


def _load_camera(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    camera = data.get("camera", data)
    if not isinstance(camera, dict):
        raise ValueError("camera config must be a JSON object")
    if camera.get("source_type") != "rtsp":
        raise ValueError("camera view currently supports explicit local rtsp configs")
    return camera


def _redact_uri(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.username or parsed.password:
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return urlunparse((parsed.scheme, f"***:***@{host}", parsed.path, "", parsed.query, ""))
    return uri


if __name__ == "__main__":
    main()
