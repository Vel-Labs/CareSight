#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

try:
    from obsws_python import ReqClient
except Exception:  # pragma: no cover - operator environment dependent.
    ReqClient = None  # type: ignore[assignment]


VENDOR_NAME = "aitum-vertical-canvas"
DEFAULT_SCENE = "CareSight Hub - FaceTime Mobile"
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect or control the optional Aitum Vertical Canvas OBS plugin.")
    parser.add_argument("--host", default=os.environ.get("OBS_WEBSOCKET_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("OBS_WEBSOCKET_PORT", "4455")))
    parser.add_argument("--password", default=os.environ.get("OBS_WEBSOCKET_PASSWORD", ""))
    parser.add_argument("--width", type=int, default=int(os.environ.get("CARESIGHT_AITUM_VERTICAL_WIDTH", str(DEFAULT_WIDTH))))
    parser.add_argument("--height", type=int, default=int(os.environ.get("CARESIGHT_AITUM_VERTICAL_HEIGHT", str(DEFAULT_HEIGHT))))

    subparsers = parser.add_subparsers(dest="command", required=True)
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--json", action="store_true")

    switch_parser = subparsers.add_parser("switch")
    switch_parser.add_argument("--scene", default=os.environ.get("CARESIGHT_AITUM_VERTICAL_SCENE", DEFAULT_SCENE))
    switch_parser.add_argument("--start-virtual-camera", action="store_true")
    switch_parser.add_argument("--json", action="store_true")

    start_parser = subparsers.add_parser("start-virtual-camera")
    start_parser.add_argument("--json", action="store_true")
    stop_parser = subparsers.add_parser("stop-virtual-camera")
    stop_parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def call_vendor(client: Any, request_type: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    response = client.call_vendor_request(VENDOR_NAME, request_type, data or {})
    attrs = vars(response)
    if "response_data" in attrs and isinstance(attrs["response_data"], dict):
        return attrs["response_data"]
    if "request_response_data" in attrs and isinstance(attrs["request_response_data"], dict):
        return attrs["request_response_data"]
    for value in attrs.values():
        if isinstance(value, dict):
            return value
    return attrs


def connect(args: argparse.Namespace) -> Any:
    if ReqClient is None:
        raise RuntimeError("obsws-python is not installed; run ./scripts/setup_obs_scene.sh once to create .venv-obs")
    return ReqClient(host=args.host, port=args.port, password=args.password, timeout=5)


def vertical_state(client: Any, width: int, height: int) -> dict[str, Any]:
    version = call_vendor(client, "version")
    scenes = call_vendor(client, "get_scenes", {"width": width, "height": height})
    current_scene = call_vendor(client, "current_scene", {"width": width, "height": height})
    status = call_vendor(client, "status", {"width": width, "height": height})
    return {
        "schema": "caresight-aitum-vertical-status",
        "plugin": "aitum-vertical-canvas",
        "available": bool(version.get("success", True)),
        "version": version.get("version"),
        "canvas": {"width": width, "height": height},
        "current_scene": current_scene.get("scene", ""),
        "scenes": [scene.get("name") for scene in scenes.get("scenes", []) if isinstance(scene, dict)],
        "virtual_camera": bool(status.get("virtual_camera", False)),
        "raw_status": status,
    }


def print_human(payload: dict[str, Any]) -> None:
    print("CareSight Aitum Vertical Canvas")
    print(f"available={str(payload.get('available', False)).lower()}")
    print(f"version={payload.get('version') or 'unknown'}")
    canvas = payload.get("canvas", {})
    print(f"canvas={canvas.get('width')}x{canvas.get('height')}")
    print(f"current_scene={payload.get('current_scene') or '(none)'}")
    print(f"vertical_virtual_camera={str(payload.get('virtual_camera', False)).lower()}")
    scenes = payload.get("scenes", [])
    if scenes:
        print("scenes:")
        for scene in scenes:
            print(f"- {scene}")
    else:
        print("scenes=(none found for this canvas)")


def main() -> int:
    args = parse_args()
    try:
        client = connect(args)
    except Exception as exc:
        payload = {
            "schema": "caresight-aitum-vertical-error",
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "hint": "Open OBS, enable OBS websocket, and verify OBS_WEBSOCKET_PASSWORD.",
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Could not connect to OBS websocket: {type(exc).__name__}: {exc}")
        return 2

    try:
        if args.command == "status":
            payload = vertical_state(client, args.width, args.height)
        elif args.command == "switch":
            scenes = vertical_state(client, args.width, args.height).get("scenes", [])
            if scenes and args.scene not in scenes:
                payload = {
                    "schema": "caresight-aitum-vertical-switch",
                    "status": "blocked",
                    "reason": "vertical_scene_missing",
                    "scene": args.scene,
                    "available_scenes": scenes,
                }
            else:
                result = call_vendor(client, "switch_scene", {"scene": args.scene})
                virtual_camera = None
                if args.start_virtual_camera:
                    virtual_camera = call_vendor(client, "start_virtual_camera")
                payload = {
                    "schema": "caresight-aitum-vertical-switch",
                    "status": "scene_requested" if result.get("success", True) else "failed",
                    "scene": args.scene,
                    "switch": result,
                    "virtual_camera": virtual_camera,
                }
        elif args.command == "start-virtual-camera":
            payload = {"schema": "caresight-aitum-vertical-virtual-camera", "action": "start", "result": call_vendor(client, "start_virtual_camera")}
        elif args.command == "stop-virtual-camera":
            payload = {"schema": "caresight-aitum-vertical-virtual-camera", "action": "stop", "result": call_vendor(client, "stop_virtual_camera")}
        else:  # pragma: no cover
            raise ValueError(args.command)
    except Exception as exc:
        payload = {
            "schema": "caresight-aitum-vertical-error",
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "hint": "Install Aitum Vertical Canvas, restart OBS, and keep OBS websocket enabled.",
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(payload["hint"])
            print(f"{payload['error_type']}: {payload['error']}")
        return 2

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if args.command == "status":
            print_human(payload)
        else:
            print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
