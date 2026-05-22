#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT_DIR.parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "caresight-v0.sqlite3"
DEFAULT_ALLOWLIST_PATH = ROOT_DIR / "config" / "hermes" / "allowlisted-contacts.local.json"
DEFAULT_OBS_PREVIEW_PATH = REPO_ROOT / "apps" / "obs-hub" / "config" / "live_preview.jpg"
DEFAULT_OBS_SCRIPT = REPO_ROOT / "apps" / "obs-hub" / "tools" / "setup_obs_scenes.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local CareSight live-demo readiness.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument(
        "--allowlist-config",
        default=os.environ.get("CARESIGHT_CONTACT_ALLOWLIST_PATH", str(DEFAULT_ALLOWLIST_PATH)),
    )
    parser.add_argument("--gemma-base-url", default=os.environ.get("CARESIGHT_GEMMA_BASE_URL", "http://127.0.0.1:8080/v1"))
    parser.add_argument("--json", action="store_true", help="Print only JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    checks = [
        file_check("sqlite_db", Path(args.db), required=False),
        file_check("contact_allowlist", Path(args.allowlist_config), required=True),
        file_check("yolo_python", ROOT_DIR / "vendor" / "yolo-mlx" / ".venv" / "bin" / "python", required=True),
        file_check("yolo_model", ROOT_DIR / "vendor" / "yolo-mlx" / "models" / "yolo26n.npz", required=True),
        file_check("obs_live_preview", DEFAULT_OBS_PREVIEW_PATH, required=False),
        obs_dry_run_check(),
        executable_check("blackhole_switcher", "SwitchAudioSource", required=False),
        gemma_check(args.gemma_base_url),
        env_check("OBS_WEBSOCKET_PASSWORD", required=True),
    ]
    payload = {
        "schema": "caresight-demo-preflight",
        "ready": all(check["ok"] or not check["required"] for check in checks),
        "checks": checks,
        "recommended_live_command": [
            "apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python",
            "apps/caresight-hub/scripts/v0_floor_stay_live.py",
            "--camera-id",
            "living_room",
            "--max-seconds",
            "600",
            "--stop-after-event",
            "--no-window",
            "--obs-live-preview",
            "--auto-agent-live-run",
            "--live-approved",
            "--auto-facetime-on-reply",
            "--reply-timeout-seconds",
            "120",
            "--play-tts-after-facetime",
            "--tts-audio-route",
            "blackhole",
        ],
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print_human(payload)


def file_check(name: str, path: Path, *, required: bool) -> dict[str, object]:
    return {
        "name": name,
        "ok": path.exists(),
        "required": required,
        "path": str(path),
        "detail": "present" if path.exists() else "missing",
    }


def executable_check(name: str, executable: str, *, required: bool) -> dict[str, object]:
    found = shutil.which(executable)
    return {
        "name": name,
        "ok": bool(found),
        "required": required,
        "path": found,
        "detail": "present" if found else f"{executable} not found",
    }


def env_check(name: str, *, required: bool) -> dict[str, object]:
    present = bool(os.environ.get(name, "").strip())
    return {
        "name": name,
        "ok": present,
        "required": required,
        "detail": "set" if present else "missing from this shell",
    }


def obs_dry_run_check() -> dict[str, object]:
    python = REPO_ROOT / ".venv-obs" / "bin" / "python"
    if not python.exists():
        python = Path(shutil.which("python3") or sys.executable)
    if not DEFAULT_OBS_SCRIPT.exists():
        return {"name": "obs_scene_tool", "ok": False, "required": True, "detail": "setup_obs_scenes.py missing"}
    result = subprocess.run(
        [str(python), str(DEFAULT_OBS_SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": "obs_scene_tool",
        "ok": result.returncode == 0,
        "required": True,
        "detail": "dry-run passed" if result.returncode == 0 else (result.stderr or result.stdout).strip()[-300:],
    }


def gemma_check(base_url: str) -> dict[str, object]:
    request = Request(base_url.rstrip("/") + "/models", method="GET")
    try:
        with urlopen(request, timeout=2) as response:
            ok = 200 <= response.status < 300
    except Exception as exc:
        return {
            "name": "gemma_endpoint",
            "ok": False,
            "required": False,
            "url": base_url,
            "detail": f"not ready: {exc}",
        }
    return {"name": "gemma_endpoint", "ok": ok, "required": False, "url": base_url, "detail": "ready"}


def print_human(payload: dict[str, object]) -> None:
    print("CareSight demo preflight")
    print(f"ready={str(payload['ready']).lower()}")
    for check in payload["checks"]:
        marker = "OK" if check["ok"] else ("WARN" if not check["required"] else "BLOCKED")
        print(f"{marker} {check['name']}: {check['detail']}")
    print("")
    print("Recommended live command:")
    print(" ".join(payload["recommended_live_command"]))


if __name__ == "__main__":
    main()
