#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = ROOT / ".venv-obs" / "bin" / "python"
if VENV_PYTHON.exists() and Path(sys.executable) != VENV_PYTHON:
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]])

try:
    from obsws_python import ReqClient
except Exception:  # pragma: no cover - operator environment dependent.
    ReqClient = None  # type: ignore[assignment]


LOCAL_DEMO_ENV = ROOT / "apps" / "caresight-hub" / "config" / "live-demo.local"
DEFAULT_FEED_URL = "http://127.0.0.1:8766/live.html"
DEFAULT_STREAM_URL = "http://127.0.0.1:8766/stream.mjpg"
DEFAULT_HEALTH_URL = "http://127.0.0.1:8766/health"
DEFAULT_LIVE_SOURCES = [
    "CareSight Escalation Live Feed",
    "CareSight FaceTime Mobile Live Feed",
]
DEFAULT_OVERLAY_SOURCES = [
    "CareSight FaceTime Mobile Overlay",
    "CareSight Aitum FaceTime Mobile Overlay",
]


def load_local_env() -> dict[str, str]:
    if not LOCAL_DEMO_ENV.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in LOCAL_DEMO_ENV.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def parse_args() -> argparse.Namespace:
    local_env = load_local_env()
    for key, value in local_env.items():
        os.environ.setdefault(key, value)

    configured_feed_url = os.environ.get("CARESIGHT_OBS_BROWSER_FEED_URL", DEFAULT_FEED_URL)
    if configured_feed_url == DEFAULT_STREAM_URL:
        configured_feed_url = DEFAULT_FEED_URL

    parser = argparse.ArgumentParser(description="Check whether OBS is wired to the live CareSight detector feed.")
    parser.add_argument("--host", default=os.environ.get("OBS_WEBSOCKET_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("OBS_WEBSOCKET_PORT", "4455")))
    parser.add_argument("--password", default=os.environ.get("OBS_WEBSOCKET_PASSWORD", ""))
    parser.add_argument("--feed-url", default=configured_feed_url)
    parser.add_argument("--stream-url", default=DEFAULT_STREAM_URL)
    parser.add_argument("--health-url", default=DEFAULT_HEALTH_URL)
    parser.add_argument("--source", action="append", dest="sources", default=[])
    parser.add_argument("--overlay-source", action="append", dest="overlay_sources", default=[])
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def detector_health(url: str) -> dict[str, Any]:
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=2) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body)
            return {
                "name": "detector_mjpeg_health",
                "ok": response.status == 200 and bool(payload.get("frame_available")),
                "required": True,
                "url": url,
                "detail": (
                    "live MJPEG server has a frame"
                    if payload.get("frame_available")
                    else "MJPEG server is reachable but no detector frame is available yet"
                ),
                "payload": payload,
            }
    except Exception as exc:
        return {
            "name": "detector_mjpeg_health",
            "ok": False,
            "required": True,
            "url": url,
            "detail": f"not reachable: {type(exc).__name__}: {exc}",
        }


def connect_obs(args: argparse.Namespace) -> Any:
    if ReqClient is None:
        raise RuntimeError("obsws-python is not installed; run ./scripts/setup_obs_scene.sh once")
    return ReqClient(host=args.host, port=args.port, password=args.password, timeout=5)


def source_url_ok(url: str, args: argparse.Namespace) -> bool:
    decoded_url = unquote(url)
    return args.feed_url in decoded_url or args.stream_url in decoded_url


def overlay_url_ok(url: str, args: argparse.Namespace) -> bool:
    decoded_url = unquote(url)
    return source_url_ok(url, args) or "video=external" in decoded_url


def read_obs_source_url(client: Any, source_name: str) -> str:
    response = client.get_input_settings(source_name)
    settings = response.input_settings
    return str(settings.get("url", ""))


def obs_source_checks(args: argparse.Namespace) -> list[dict[str, Any]]:
    live_source_names = args.sources or DEFAULT_LIVE_SOURCES
    overlay_source_names = args.overlay_sources or DEFAULT_OVERLAY_SOURCES
    try:
        client = connect_obs(args)
    except Exception as exc:
        return [
            {
                "name": "obs_websocket",
                "ok": False,
                "required": True,
                "detail": f"not reachable: {type(exc).__name__}: {exc}",
            }
        ]

    checks: list[dict[str, Any]] = [
        {"name": "obs_websocket", "ok": True, "required": True, "detail": "reachable"}
    ]
    for source_name in live_source_names:
        try:
            url = read_obs_source_url(client, source_name)
            decoded_url = unquote(url)
            ok = source_url_ok(url, args)
            checks.append(
                {
                    "name": f"obs_source:{source_name}",
                    "ok": ok,
                    "required": True,
                    "url": url,
                    "decoded_url": decoded_url,
                    "detail": "points at live MJPEG feed" if ok else "does not point at live MJPEG feed",
                }
            )
        except Exception as exc:
            checks.append(
                {
                    "name": f"obs_source:{source_name}",
                    "ok": False,
                    "required": True,
                    "detail": f"missing or unreadable: {type(exc).__name__}: {exc}",
                }
            )
    for source_name in overlay_source_names:
        try:
            url = read_obs_source_url(client, source_name)
            decoded_url = unquote(url)
            ok = overlay_url_ok(url, args)
            checks.append(
                {
                    "name": f"obs_overlay:{source_name}",
                    "ok": ok,
                    "required": True,
                    "url": url,
                    "decoded_url": decoded_url,
                    "detail": "overlay uses live feed or transparent external-video mode" if ok else "overlay is not wired for live/external video",
                }
            )
        except Exception as exc:
            checks.append(
                {
                    "name": f"obs_overlay:{source_name}",
                    "ok": False,
                    "required": True,
                    "detail": f"missing or unreadable: {type(exc).__name__}: {exc}",
                }
            )
    return checks


def main() -> int:
    logging.disable(logging.CRITICAL)
    args = parse_args()
    checks = [detector_health(args.health_url), *obs_source_checks(args)]
    payload = {
        "schema": "caresight-obs-live-feed-check",
        "ready": all(check["ok"] or not check["required"] for check in checks),
        "stream_url": args.stream_url,
        "feed_url": args.feed_url,
        "checks": checks,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("CareSight OBS live feed check")
        print(f"ready={str(payload['ready']).lower()}")
        print(f"feed_url={args.feed_url}")
        print(f"stream_url={args.stream_url}")
        for check in checks:
            marker = "OK" if check["ok"] else ("WARN" if not check["required"] else "BLOCKED")
            print(f"{marker} {check['name']}: {check['detail']}")
    return 0 if payload["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
