#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

try:
    from obsws_python import ReqClient
except Exception:  # pragma: no cover - exercised on operator machines.
    ReqClient = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[3]
APP_DIR = ROOT / "apps" / "obs-hub"
CONFIG_PATH = APP_DIR / "config" / "cameras.json"
EVENT_PATH = APP_DIR / "config" / "sample_event.json"
OVERLAY_DIR = APP_DIR / "overlays"
DEFAULT_BROWSER_FEED_URL = "http://127.0.0.1:8766/stream.mjpg"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def file_url(path: Path) -> str:
    return path.resolve().as_uri()


def validate_config(config: dict[str, Any]) -> tuple[int, int, list[dict[str, Any]]]:
    canvas = config.get("canvas")
    cameras = config.get("cameras")
    if not isinstance(canvas, dict):
        raise ValueError("cameras.json missing canvas object")
    if not isinstance(cameras, list):
        raise ValueError("cameras.json missing cameras array")

    width = int(canvas.get("width", 1920))
    height = int(canvas.get("height", 1080))
    required = {"id", "zone", "scene", "source_name", "source_type"}
    for camera in cameras:
        if not isinstance(camera, dict):
            raise ValueError("each camera entry must be an object")
        missing = required - set(camera)
        if missing:
            raise ValueError(f"camera entry missing required fields: {sorted(missing)}")
    return width, height, cameras


def print_obs_help() -> None:
    print(
        """
Could not connect to OBS websocket.

Open OBS and configure:

1. Tools > WebSocket Server Settings
2. Enable WebSocket server
3. Set port to 4455
4. Set/copy password
5. Run:
   export OBS_WEBSOCKET_PASSWORD='your-password'
   ./scripts/setup_obs_scene.sh
""".strip()
    )


def obs_get_attr(value: Any, key: str, attr: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, attr, None)


def ensure_scene(client: Any, scene_name: str) -> None:
    scenes = client.get_scene_list().scenes
    existing = {obs_get_attr(scene, "sceneName", "scene_name") for scene in scenes}
    if scene_name not in existing:
        client.create_scene(scene_name)


def source_exists(client: Any, source_name: str) -> bool:
    inputs = client.get_input_list().inputs
    for item in inputs:
        if obs_get_attr(item, "inputName", "input_name") == source_name:
            return True
    return False


def create_or_update_input(
    client: Any,
    scene_name: str,
    input_name: str,
    input_kind: str,
    settings: dict[str, Any],
    enabled: bool = True,
) -> None:
    if source_exists(client, input_name):
        client.set_input_settings(input_name, settings, True)
        add_existing_source_to_scene(client, scene_name, input_name)
        return
    client.create_input(scene_name, input_name, input_kind, settings, enabled)


def add_existing_source_to_scene(client: Any, scene_name: str, source_name: str) -> None:
    try:
        client.get_scene_item_id(scene_name, source_name)
    except Exception:
        try:
            client.create_scene_item(scene_name, source_name, True)
        except Exception:
            pass


def set_transform(client: Any, scene_name: str, source_name: str, transform: dict[str, Any]) -> None:
    try:
        item = client.get_scene_item_id(scene_name, source_name)
        scene_item_id = obs_get_attr(item, "sceneItemId", "scene_item_id")
        if scene_item_id is not None:
            client.set_scene_item_transform(scene_name, scene_item_id, transform)
    except Exception as exc:
        print(f"warn: could not set transform for {source_name}: {exc}")


def fill_transform(width: int, height: int) -> dict[str, Any]:
    return {
        "positionX": 0,
        "positionY": 0,
        "scaleX": 1.0,
        "scaleY": 1.0,
        "boundsType": "OBS_BOUNDS_SCALE_INNER",
        "boundsWidth": width,
        "boundsHeight": height,
        "alignment": 5,
    }


def ensure_browser_source(
    client: Any,
    scene_name: str,
    source_name: str,
    html_path: Path,
    width: int,
    height: int,
    query: str = "",
) -> None:
    settings = {
        "url": file_url(html_path) + query,
        "width": width,
        "height": height,
        "fps": 30,
        "shutdown": False,
        "restart_when_active": True,
        "css": "body { background-color: rgba(0, 0, 0, 0); }",
    }
    create_or_update_input(client, scene_name, source_name, "browser_source", settings, True)
    set_transform(client, scene_name, source_name, fill_transform(width, height))


def ensure_image_source(
    client: Any,
    scene_name: str,
    source_name: str,
    image_path: str,
    width: int,
    height: int,
) -> None:
    path = Path(image_path).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        print(f"warn: image path does not exist; using placeholder for {source_name}: {path}")
        ensure_placeholder_source(client, scene_name, source_name, width, height)
        return

    create_or_update_input(client, scene_name, source_name, "image_source", {"file": str(path)}, True)
    set_transform(client, scene_name, source_name, fill_transform(width, height))


def ensure_placeholder_source(client: Any, scene_name: str, source_name: str, width: int, height: int) -> None:
    settings = {
        "color": 0xFF101820,
        "width": width,
        "height": height,
    }
    create_or_update_input(client, scene_name, source_name, "color_source_v3", settings, True)
    set_transform(client, scene_name, source_name, fill_transform(width, height))


def create_camera_scene(client: Any, camera: dict[str, Any], width: int, height: int) -> None:
    scene = str(camera["scene"])
    zone = str(camera["zone"])
    camera_id = str(camera["id"])
    feed_source = str(camera["source_name"])

    ensure_scene(client, scene)
    if camera.get("source_type") == "image":
        ensure_image_source(client, scene, feed_source, str(camera.get("image_path", "")), width, height)
    else:
        ensure_placeholder_source(client, scene, feed_source, width, height)

    query = f"?camera={quote(camera_id)}&zone={quote(zone)}"
    ensure_browser_source(
        client,
        scene,
        f"CareSight Overlay - {zone}",
        OVERLAY_DIR / "camera-feed.html",
        width,
        height,
        query,
    )


def create_dashboard_scene(client: Any, width: int, height: int) -> None:
    scene = "CareSight Hub - Dashboard"
    ensure_scene(client, scene)
    ensure_browser_source(client, scene, "CareSight Dashboard Overlay", OVERLAY_DIR / "dashboard.html", width, height)


def create_escalation_scene(client: Any, width: int, height: int) -> None:
    scene = "CareSight Hub - Escalation"
    ensure_scene(client, scene)
    ensure_placeholder_source(client, scene, "CareSight Escalation Background", width, height)
    feed_url = quote(os.environ.get("CARESIGHT_OBS_BROWSER_FEED_URL", DEFAULT_BROWSER_FEED_URL), safe="")
    ensure_browser_source(
        client,
        scene,
        "CareSight Escalation Overlay",
        OVERLAY_DIR / "escalation.html",
        width,
        height,
        f"?feed=mjpeg&feed_url={feed_url}",
    )


def create_facetime_mobile_scene(client: Any, width: int, height: int) -> None:
    scene = "CareSight Hub - FaceTime Mobile"
    mobile_width = 1080
    mobile_height = 1920
    ensure_scene(client, scene)
    ensure_placeholder_source(client, scene, "CareSight FaceTime Mobile Background", mobile_width, mobile_height)
    feed_url = quote(os.environ.get("CARESIGHT_OBS_BROWSER_FEED_URL", DEFAULT_BROWSER_FEED_URL), safe="")
    ensure_browser_source(
        client,
        scene,
        "CareSight FaceTime Mobile Overlay",
        OVERLAY_DIR / "facetime-mobile.html",
        mobile_width,
        mobile_height,
        f"?feed=mjpeg&feed_url={feed_url}",
    )


def set_video_output_for_scene(client: Any, scene_name: str) -> dict[str, Any]:
    if scene_name != "CareSight Hub - FaceTime Mobile":
        return {"status": "not_requested", "scene": scene_name}
    try:
        client.set_video_settings(
            base_width=1080,
            base_height=1920,
            output_width=1080,
            output_height=1920,
        )
        return {"status": "requested", "base": "1080x1920", "output": "1080x1920"}
    except Exception as exc:
        print(f"warn: could not set vertical OBS video output: {exc}")
        return {"status": "failed", "error": str(exc)}


def planned_scenes(cameras: list[dict[str, Any]]) -> list[str]:
    return [
        "CareSight Hub - Dashboard",
        "CareSight Hub - Escalation",
        "CareSight Hub - FaceTime Mobile",
        *[str(camera["scene"]) for camera in cameras],
    ]


def apply_environment_overrides(cameras: list[dict[str, Any]]) -> None:
    sample_image = os.environ.get("CARESIGHT_OBS_SAMPLE_IMAGE")
    if not sample_image:
        return
    for camera in cameras:
        if camera.get("id") == "C1":
            camera["source_type"] = "image"
            camera["image_path"] = sample_image


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or update CareSight OBS scenes.")
    parser.add_argument("--host", default=os.environ.get("OBS_WEBSOCKET_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("OBS_WEBSOCKET_PORT", "4455")))
    parser.add_argument("--password", default=os.environ.get("OBS_WEBSOCKET_PASSWORD", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--scene", default="CareSight Hub - Escalation")
    parser.add_argument("--refresh-overlays", action="store_true", help="Accepted for idempotent reruns; browser sources are always updated.")
    args = parser.parse_args()

    config = load_json(CONFIG_PATH)
    load_json(EVENT_PATH)
    width, height, cameras = validate_config(config)
    apply_environment_overrides(cameras)
    scenes = planned_scenes(cameras)

    if args.dry_run:
        print("Planned OBS scenes:")
        for scene in scenes:
            print(f"- {scene}")
        print("Planned overlay files:")
        for overlay in ["dashboard.html", "escalation.html", "facetime-mobile.html", "camera-feed.html"]:
            print(f"- {file_url(OVERLAY_DIR / overlay)}")
        return 0

    if ReqClient is None:
        print("Missing dependency: obsws-python")
        return 2

    try:
        client = ReqClient(host=args.host, port=args.port, password=args.password, timeout=5)
    except Exception:
        print_obs_help()
        return 2

    create_dashboard_scene(client, width, height)
    create_escalation_scene(client, width, height)
    create_facetime_mobile_scene(client, width, height)
    for camera in cameras:
        create_camera_scene(client, camera, width, height)

    try:
        client.set_current_program_scene(args.scene)
        video_settings = set_video_output_for_scene(client, args.scene)
        if video_settings["status"] == "requested":
            print("OBS video output set for FaceTime Mobile: 1080x1920")
    except Exception as exc:
        print(f"warn: could not switch to scene {args.scene}: {exc}")

    print("CareSight OBS scenes are ready.")
    print(f"Current scene target: {args.scene}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
