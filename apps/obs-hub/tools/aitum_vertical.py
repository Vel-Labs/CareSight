#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = ROOT / ".venv-obs" / "bin" / "python"
if VENV_PYTHON.exists() and Path(sys.executable) != VENV_PYTHON:
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])

try:
    from obsws_python import ReqClient
except Exception:  # pragma: no cover - operator environment dependent.
    ReqClient = None  # type: ignore[assignment]


VENDOR_NAME = "aitum-vertical-canvas"
DEFAULT_SCENE = "CareSight Hub - FaceTime Mobile Vertical"
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920
LOCAL_DEMO_ENV = ROOT / "apps" / "caresight-hub" / "config" / "live-demo.local"
AITUM_CONFIG = Path.home() / "Library" / "Application Support" / "obs-studio" / "plugin_config" / "vertical-canvas" / "config.json"


def load_local_env() -> None:
    if not LOCAL_DEMO_ENV.exists():
        return
    for raw_line in LOCAL_DEMO_ENV.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def parse_args() -> argparse.Namespace:
    load_local_env()
    default_width, default_height = configured_canvas_default()
    parser = argparse.ArgumentParser(description="Inspect or control the optional Aitum Vertical Canvas OBS plugin.")
    parser.add_argument("--host", default=os.environ.get("OBS_WEBSOCKET_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("OBS_WEBSOCKET_PORT", "4455")))
    parser.add_argument("--password", default=os.environ.get("OBS_WEBSOCKET_PASSWORD", ""))
    parser.add_argument("--width", type=int, default=int(os.environ.get("CARESIGHT_AITUM_VERTICAL_WIDTH", str(default_width))))
    parser.add_argument("--height", type=int, default=int(os.environ.get("CARESIGHT_AITUM_VERTICAL_HEIGHT", str(default_height))))

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


def configured_canvas_default() -> tuple[int, int]:
    if os.environ.get("CARESIGHT_AITUM_VERTICAL_WIDTH") and os.environ.get("CARESIGHT_AITUM_VERTICAL_HEIGHT"):
        return DEFAULT_WIDTH, DEFAULT_HEIGHT
    if not AITUM_CONFIG.exists():
        return DEFAULT_WIDTH, DEFAULT_HEIGHT
    try:
        payload = json.loads(AITUM_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_WIDTH, DEFAULT_HEIGHT
    canvases = payload.get("canvas", []) if isinstance(payload, dict) else []
    for canvas in canvases:
        if not isinstance(canvas, dict):
            continue
        width = int(canvas.get("width", 0) or 0)
        height = int(canvas.get("height", 0) or 0)
        if width > 0 and height > width:
            return width, height
    return DEFAULT_WIDTH, DEFAULT_HEIGHT


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


def scene_config_state(width: int, height: int) -> dict[str, Any]:
    config_path = AITUM_CONFIG
    if not config_path.exists():
        return {"config_path": str(config_path), "configured": False}
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"config_path": str(config_path), "configured": False, "error": str(exc)}
    canvases = payload.get("canvas", []) if isinstance(payload, dict) else []
    for canvas in canvases:
        if not isinstance(canvas, dict):
            continue
        if int(canvas.get("width", 0)) == width and int(canvas.get("height", 0)) == height:
            return {
                "config_path": str(config_path),
                "configured": True,
                "current_scene": canvas.get("current_scene"),
                "width": width,
                "height": height,
            }
    return {"config_path": str(config_path), "configured": False, "width": width, "height": height}


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
    local_config = payload.get("local_config", {})
    if isinstance(local_config, dict) and local_config.get("configured"):
        print(f"local_config_scene={local_config.get('current_scene')}")


def main() -> int:
    logging.disable(logging.CRITICAL)
    args = parse_args()
    try:
        client = connect(args)
    except Exception as exc:
        payload = {
            "schema": "caresight-aitum-vertical-error",
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "canvas": {"width": args.width, "height": args.height},
            "local_config": scene_config_state(args.width, args.height),
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
            payload["local_config"] = scene_config_state(args.width, args.height)
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
