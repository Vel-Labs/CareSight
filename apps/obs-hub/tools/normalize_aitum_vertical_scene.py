#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = ROOT / ".venv-obs" / "bin" / "python"
if VENV_PYTHON.exists() and Path(sys.executable) != VENV_PYTHON:
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])

try:
    from obsws_python import ReqClient
except Exception:  # pragma: no cover - operator environment dependent.
    ReqClient = None  # type: ignore[assignment]


APP_DIR = ROOT / "apps" / "obs-hub"
OVERLAY_DIR = APP_DIR / "overlays"
LAYOUT_PATH = APP_DIR / "config" / "overlay_layout.json"
LOCAL_DEMO_ENV = ROOT / "apps" / "caresight-hub" / "config" / "live-demo.local"

DEFAULT_SCENE = "CareSight Hub - FaceTime Mobile Vertical"
DEFAULT_FEED_SOURCE = "CareSight FaceTime Mobile Live Feed"
DEFAULT_OVERLAY_SOURCE = "CareSight Aitum FaceTime Mobile Overlay"
DEFAULT_BACKGROUND_SOURCE = "CareSight FaceTime Mobile Vertical Background"
DEFAULT_FEED_URL = "http://127.0.0.1:8766/live.html"
DEFAULT_CANVAS_WIDTH = 1080
DEFAULT_CANVAS_HEIGHT = 1920
DEFAULT_FEED_WIDTH = 1920
DEFAULT_FEED_HEIGHT = 1080


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


def load_layout() -> dict[str, Any]:
    if not LAYOUT_PATH.exists():
        return {}
    with LAYOUT_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def obs_get_attr(value: Any, key: str, attr: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, attr, None)


def file_url(path: Path) -> str:
    return path.resolve().as_uri()


def connect(args: argparse.Namespace) -> Any:
    if ReqClient is None:
        raise RuntimeError("obsws-python is not installed; run ./scripts/setup_obs_scene.sh once")
    return ReqClient(host=args.host, port=args.port, password=args.password, timeout=5)


def source_exists(client: Any, source_name: str) -> bool:
    for item in client.get_input_list().inputs:
        if obs_get_attr(item, "inputName", "input_name") == source_name:
            return True
    return False


def scene_exists(client: Any, scene_name: str) -> bool:
    for scene in client.get_scene_list().scenes:
        if obs_get_attr(scene, "sceneName", "scene_name") == scene_name:
            return True
    return False


def scene_item_id(client: Any, scene_name: str, source_name: str) -> int | None:
    try:
        item = client.get_scene_item_id(scene_name, source_name)
    except Exception:
        return None
    value = obs_get_attr(item, "sceneItemId", "scene_item_id")
    return int(value) if value is not None else None


def ensure_scene(client: Any, scene_name: str) -> None:
    if not scene_exists(client, scene_name):
        client.create_scene(scene_name)


def ensure_input(
    client: Any,
    scene_name: str,
    source_name: str,
    input_kind: str,
    settings: dict[str, Any],
) -> None:
    if source_exists(client, source_name):
        client.set_input_settings(source_name, settings, True)
        if scene_item_id(client, scene_name, source_name) is None:
            client.create_scene_item(scene_name, source_name, True)
        return
    client.create_input(scene_name, source_name, input_kind, settings, True)


def set_transform(client: Any, scene_name: str, source_name: str, transform: dict[str, Any]) -> None:
    item_id = scene_item_id(client, scene_name, source_name)
    if item_id is None:
        raise RuntimeError(f"source {source_name!r} is not in scene {scene_name!r}")
    client.set_scene_item_transform(scene_name, item_id, transform)


def set_source_order(client: Any, scene_name: str, source_names: list[str]) -> None:
    for index, source_name in enumerate(source_names):
        item_id = scene_item_id(client, scene_name, source_name)
        if item_id is None:
            continue
        try:
            client.set_scene_item_index(scene_name, item_id, index)
        except Exception:
            pass


def transform_rect(x: int, y: int, width: int, height: int) -> dict[str, Any]:
    return {
        "positionX": x,
        "positionY": y,
        "scaleX": 1.0,
        "scaleY": 1.0,
        "rotation": 0.0,
        "cropTop": 0,
        "cropBottom": 0,
        "cropLeft": 0,
        "cropRight": 0,
        "boundsType": "OBS_BOUNDS_SCALE_INNER",
        "boundsAlignment": 5,
        "boundsWidth": width,
        "boundsHeight": height,
        "alignment": 5,
    }


def normalize_scene(client: Any, args: argparse.Namespace) -> dict[str, Any]:
    layout = load_layout().get("facetime", {})
    feed = layout.get("liveFeed", {})
    feed_x = int(feed.get("x", 44))
    feed_y = int(feed.get("y", 168))
    feed_width = int(feed.get("width", 992))
    feed_height = int(feed.get("height", 558))
    feed_url = args.feed_url
    overlay_url = (
        file_url(OVERLAY_DIR / "facetime-mobile.html")
        + f"?video=external&feed_url={quote(feed_url, safe='')}"
    )

    ensure_scene(client, args.scene)
    ensure_input(
        client,
        args.scene,
        DEFAULT_BACKGROUND_SOURCE,
        "color_source_v3",
        {"color": 0xFF02060B, "width": args.width, "height": args.height},
    )
    ensure_input(
        client,
        args.scene,
        args.feed_source,
        "browser_source",
        {
            "url": feed_url,
            "width": DEFAULT_FEED_WIDTH,
            "height": DEFAULT_FEED_HEIGHT,
            "fps": 30,
            "shutdown": False,
            "restart_when_active": True,
            "css": "body { background-color: rgba(0, 0, 0, 0); }",
        },
    )
    ensure_input(
        client,
        args.scene,
        args.overlay_source,
        "browser_source",
        {
            "url": overlay_url,
            "width": args.width,
            "height": args.height,
            "fps": 30,
            "shutdown": False,
            "restart_when_active": True,
            "css": "body { background-color: rgba(0, 0, 0, 0); }",
        },
    )

    set_transform(client, args.scene, DEFAULT_BACKGROUND_SOURCE, transform_rect(0, 0, args.width, args.height))
    set_transform(client, args.scene, args.feed_source, transform_rect(feed_x, feed_y, feed_width, feed_height))
    set_transform(client, args.scene, args.overlay_source, transform_rect(0, 0, args.width, args.height))
    set_source_order(client, args.scene, [args.overlay_source, args.feed_source, DEFAULT_BACKGROUND_SOURCE])

    return {
        "schema": "caresight-aitum-vertical-normalize",
        "status": "normalized",
        "scene": args.scene,
        "canvas": {"width": args.width, "height": args.height},
        "live_feed": {
            "source": args.feed_source,
            "url": feed_url,
            "source_size": {"width": DEFAULT_FEED_WIDTH, "height": DEFAULT_FEED_HEIGHT},
            "bounds": {"x": feed_x, "y": feed_y, "width": feed_width, "height": feed_height},
        },
        "overlay": {
            "source": args.overlay_source,
            "url": overlay_url,
            "bounds": {"x": 0, "y": 0, "width": args.width, "height": args.height},
        },
    }


def parse_args() -> argparse.Namespace:
    load_local_env()
    parser = argparse.ArgumentParser(description="Normalize the CareSight Aitum vertical FaceTime scene geometry.")
    parser.add_argument("--host", default=os.environ.get("OBS_WEBSOCKET_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("OBS_WEBSOCKET_PORT", "4455")))
    parser.add_argument("--password", default=os.environ.get("OBS_WEBSOCKET_PASSWORD", ""))
    parser.add_argument("--scene", default=os.environ.get("CARESIGHT_AITUM_VERTICAL_SCENE", DEFAULT_SCENE))
    parser.add_argument("--width", type=int, default=int(os.environ.get("CARESIGHT_AITUM_VERTICAL_WIDTH", str(DEFAULT_CANVAS_WIDTH))))
    parser.add_argument("--height", type=int, default=int(os.environ.get("CARESIGHT_AITUM_VERTICAL_HEIGHT", str(DEFAULT_CANVAS_HEIGHT))))
    parser.add_argument("--feed-url", default=os.environ.get("CARESIGHT_OBS_BROWSER_FEED_URL", DEFAULT_FEED_URL))
    parser.add_argument("--feed-source", default=DEFAULT_FEED_SOURCE)
    parser.add_argument("--overlay-source", default=DEFAULT_OVERLAY_SOURCE)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    logging.disable(logging.CRITICAL)
    args = parse_args()
    if args.width >= args.height:
        print(f"Expected a portrait canvas, got {args.width}x{args.height}", file=sys.stderr)
        return 2

    if args.dry_run:
        feed = load_layout().get("facetime", {}).get("liveFeed", {})
        payload = {
            "schema": "caresight-aitum-vertical-normalize-plan",
            "scene": args.scene,
            "canvas": {"width": args.width, "height": args.height},
            "live_feed": {
                "source": args.feed_source,
                "url": args.feed_url,
                "source_size": {"width": DEFAULT_FEED_WIDTH, "height": DEFAULT_FEED_HEIGHT},
                "bounds": {
                    "x": int(feed.get("x", 44)),
                    "y": int(feed.get("y", 168)),
                    "width": int(feed.get("width", 992)),
                    "height": int(feed.get("height", 558)),
                },
            },
            "overlay": {"source": args.overlay_source, "bounds": {"x": 0, "y": 0, "width": args.width, "height": args.height}},
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    try:
        client = connect(args)
        payload = normalize_scene(client, args)
    except Exception as exc:
        print(f"Could not normalize Aitum vertical scene: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
