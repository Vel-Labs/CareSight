#!/usr/bin/env python3
"""Verify the local CareSight Hermes harness is ready for no-send use."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HUB_ROOT = REPO_ROOT / "apps" / "caresight-hub"
DEFAULT_PYTHON = HUB_ROOT / ".venv" / "bin" / "python"
DEFAULT_VENDOR_PATH = HUB_ROOT / "vendor" / "hermes-agent"
DEFAULT_CONFIG_PATH = HUB_ROOT / "config" / "hermes" / "config.caresight.local.yaml"
DEFAULT_STATUS_FILE = HUB_ROOT / "data" / "runtime" / "hermes-ready.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the local CareSight Hermes harness.")
    parser.add_argument("--vendor-path", type=Path, default=DEFAULT_VENDOR_PATH)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--status-file", type=Path, default=DEFAULT_STATUS_FILE)
    parser.add_argument("--require-gemma", action="store_true", help="Require the local Gemma endpoint to answer.")
    parser.add_argument("--gemma-base-url", default="http://127.0.0.1:8080/v1")
    return parser.parse_args()


def gemma_ready(base_url: str) -> dict[str, object]:
    import urllib.error
    import urllib.request

    request = urllib.request.Request(f"{base_url.rstrip('/')}/models", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            body = response.read().decode("utf-8")
        return {"status": "ready", "http_status": response.status, "body_preview": body[:120]}
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"status": "blocked", "error": str(exc)}


def hermes_preflight(vendor_path: Path) -> dict[str, object]:
    if not vendor_path.exists():
        return {"status": "blocked", "reason": "vendor_path_missing", "vendor_path": str(vendor_path)}

    inserted = str(vendor_path)
    sys.path.insert(0, inserted)
    try:
        from tools.send_message_tool import SEND_MESSAGE_SCHEMA, send_message_tool

        result_text = send_message_tool({"action": "list"})
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            result = {"raw_result": result_text}
        if isinstance(result, dict) and result.get("error"):
            return {
                "status": "blocked",
                "tool": SEND_MESSAGE_SCHEMA["name"],
                "action": "list",
                "reason": "message_directory_unavailable",
                "error": result["error"],
            }
        return {
            "status": "ready",
            "tool": SEND_MESSAGE_SCHEMA["name"],
            "action": "list",
            "result_summary": summarize_targets(result),
            "result_redacted": True,
        }
    except Exception as exc:
        return {"status": "blocked", "reason": "import_or_preflight_failed", "error": str(exc)}
    finally:
        if sys.path and sys.path[0] == inserted:
            sys.path.pop(0)


def summarize_targets(result: object) -> dict[str, object]:
    targets = result.get("targets") if isinstance(result, dict) else None
    if not isinstance(targets, str):
        return {"available": bool(result)}
    target_lines = [line for line in targets.splitlines() if line.startswith("  ")]
    return {"available": bool(target_lines), "target_count": len(target_lines), "target_names_redacted": True}


def main() -> int:
    args = parse_args()
    if DEFAULT_PYTHON.exists() and os.environ.get("CARESIGHT_HERMES_REEXEC") != "1":
        env = {**os.environ, "CARESIGHT_HERMES_REEXEC": "1"}
        os.execve(str(DEFAULT_PYTHON), [str(DEFAULT_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]], env)

    config_status = "present" if args.config.exists() else "missing"
    preflight = hermes_preflight(args.vendor_path)
    gemma = gemma_ready(args.gemma_base_url) if args.require_gemma else {"status": "not_required"}
    ready = preflight["status"] == "ready" and config_status == "present"
    if args.require_gemma and gemma["status"] != "ready":
        ready = False

    receipt = {
        "schema": "caresight-hermes-runtime-readiness",
        "status": "ready" if ready else "blocked",
        "vendor_path": str(args.vendor_path),
        "config_path": str(args.config),
        "config_status": config_status,
        "gemma": gemma,
        "hermes_preflight": preflight,
        "external_action_performed": False,
        "safety_boundaries": [
            "no_send",
            "no_facetime",
            "no_notes_write",
            "no_tts_playback",
            "raw_target_names_redacted",
        ],
    }
    args.status_file.parent.mkdir(parents=True, exist_ok=True)
    args.status_file.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"hermes_{receipt['status']} status_file={args.status_file} "
        f"config={config_status} preflight={preflight['status']} gemma={gemma['status']}"
    )
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
