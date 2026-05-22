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
DEFAULT_AITUM_SCRIPT = REPO_ROOT / "apps" / "obs-hub" / "tools" / "aitum_vertical.py"
DEFAULT_AITUM_INSTALLER = REPO_ROOT / "scripts" / "install_obs_vertical_canvas.sh"
DEFAULT_LOCAL_ENV_PATH = ROOT_DIR / "config" / "live-demo.local"
DEFAULT_YOLO_MODEL = ROOT_DIR / "vendor" / "yolo-mlx" / "models" / "yolo26n.npz"
DEFAULT_GEMMA_MODEL = ROOT_DIR / "models" / "reasoning" / "gemma" / "gemma-4-e2b-it-4bit"
DEFAULT_TTS_MODEL = ROOT_DIR / "models" / "tts" / "holler" / "holler-0.6b-6bit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check local CareSight live-demo readiness.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument(
        "--allowlist-config",
        default=os.environ.get("CARESIGHT_CONTACT_ALLOWLIST_PATH", str(DEFAULT_ALLOWLIST_PATH)),
    )
    parser.add_argument("--gemma-base-url", default=os.environ.get("CARESIGHT_GEMMA_BASE_URL", "http://127.0.0.1:8080/v1"))
    parser.add_argument("--gemma-model", default=os.environ.get("CARESIGHT_GEMMA_MODEL", str(DEFAULT_GEMMA_MODEL)))
    parser.add_argument("--tts-model", default=os.environ.get("CARESIGHT_TTS_MODEL", str(DEFAULT_TTS_MODEL)))
    parser.add_argument("--json", action="store_true", help="Print only JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    local_env = read_local_env(DEFAULT_LOCAL_ENV_PATH)
    checks = [
        file_check("sqlite_db", Path(args.db), required=False),
        file_check("contact_allowlist", Path(args.allowlist_config), required=True),
        file_check("local_demo_env", DEFAULT_LOCAL_ENV_PATH, required=False),
        file_check("yolo_python", ROOT_DIR / "vendor" / "yolo-mlx" / ".venv" / "bin" / "python", required=True),
        model_file_check("yolo_model", DEFAULT_YOLO_MODEL, model_id="yolo26n", required=True),
        model_file_check("gemma_model", Path(args.gemma_model), model_id=Path(args.gemma_model).name, required=True),
        model_file_check("tts_model", Path(args.tts_model), model_id=Path(args.tts_model).name, required=True),
        file_check("obs_live_preview", DEFAULT_OBS_PREVIEW_PATH, required=False),
        obs_dry_run_check(),
        file_check("aitum_vertical_installer", DEFAULT_AITUM_INSTALLER, required=False),
        aitum_vertical_check(local_env),
        executable_check("blackhole_switcher", "SwitchAudioSource", required=False),
        gemma_check(args.gemma_base_url),
        env_or_local_check("OBS_WEBSOCKET_PASSWORD", local_env, required=True),
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
            "--no-window",
            "--obs-browser-feed",
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


def model_file_check(name: str, path: Path, *, model_id: str, required: bool) -> dict[str, object]:
    exists = path.exists()
    kind = "directory" if exists and path.is_dir() else "file"
    display_path = display_path_for(path)
    return {
        "name": name,
        "ok": exists,
        "required": required,
        "model": model_id,
        "path": str(path),
        "display_path": display_path,
        "detail": f"{model_id} present at {display_path} ({kind})" if exists else f"{model_id} missing at {display_path}",
    }


def display_path_for(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


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


def env_or_local_check(name: str, local_env: dict[str, str], *, required: bool) -> dict[str, object]:
    if os.environ.get(name, "").strip():
        return {"name": name, "ok": True, "required": required, "detail": "set in current shell"}
    if local_env.get(name, "").strip():
        return {"name": name, "ok": True, "required": required, "detail": f"set in {DEFAULT_LOCAL_ENV_PATH}"}
    return {"name": name, "ok": False, "required": required, "detail": "missing from shell and local demo env"}


def read_local_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
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


def aitum_vertical_check(local_env: dict[str, str]) -> dict[str, object]:
    python = REPO_ROOT / ".venv-obs" / "bin" / "python"
    if not python.exists():
        python = Path(shutil.which("python3") or sys.executable)
    if not DEFAULT_AITUM_SCRIPT.exists():
        return {"name": "aitum_vertical_canvas", "ok": False, "required": False, "detail": "aitum_vertical.py missing"}
    env = os.environ.copy()
    for key, value in local_env.items():
        env.setdefault(key, value)
    result = subprocess.run(
        [str(python), str(DEFAULT_AITUM_SCRIPT), "status", "--json"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {
            "name": "aitum_vertical_canvas",
            "ok": False,
            "required": False,
            "detail": "optional plugin not reachable; plain OBS fallback remains available",
        }
    try:
        payload = json.loads(result.stdout)
    except Exception:
        payload = {}
    version = payload.get("version") or "unknown"
    current = payload.get("current_scene") or "none"
    virtual_camera = str(bool(payload.get("virtual_camera"))).lower()
    return {
        "name": "aitum_vertical_canvas",
        "ok": True,
        "required": False,
        "detail": f"ready version={version} current_scene={current} vertical_virtual_camera={virtual_camera}",
    }


def gemma_check(base_url: str) -> dict[str, object]:
    request = Request(base_url.rstrip("/") + "/models", method="GET")
    model_ids: list[str] = []
    try:
        with urlopen(request, timeout=2) as response:
            ok = 200 <= response.status < 300
            try:
                payload = json.loads(response.read().decode("utf-8"))
                data = payload.get("data", []) if isinstance(payload, dict) else []
                model_ids = [str(item.get("id")) for item in data if isinstance(item, dict) and item.get("id")]
            except Exception:
                model_ids = []
    except Exception as exc:
        return {
            "name": "gemma_endpoint",
            "ok": False,
            "required": False,
            "url": base_url,
            "detail": f"not ready: {exc}",
        }
    model_detail = f" models={','.join(model_ids)}" if model_ids else ""
    return {"name": "gemma_endpoint", "ok": ok, "required": False, "url": base_url, "models": model_ids, "detail": f"ready{model_detail}"}


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
