from __future__ import annotations

import hashlib
import json
import os
import select
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from caresight.runtime.agent_assist.contacts import load_contact_allowlist
from caresight.runtime.agent_assist.harness import build_hermes_handoff_payload
from caresight.storage.sqlite_store import utc_now


DEFAULT_LIVE_MESSAGE = (
    "CareSight alert. Possible floor stay observed in the Living Room. Needs review. "
    "Would you like to connect to CareSight?"
)

AFFIRMATIVE_TERMS = {
    "yes",
    "y",
    "yeah",
    "yep",
    "sure",
    "ok",
    "okay",
    "please",
    "connect",
    "call",
    "facetime",
    "start",
    "go ahead",
}

NEGATIVE_TERMS = {
    "no",
    "n",
    "nope",
    "not now",
    "do not",
    "don't",
    "stop",
    "cancel",
}


def is_yes_like_reply(text: str) -> bool:
    normalized = " ".join(text.casefold().strip().split())
    if not normalized:
        return False
    tokens = set(normalized.replace(".", " ").replace(",", " ").replace("!", " ").replace("?", " ").split())
    if any(_term_present(term, normalized, tokens) for term in NEGATIVE_TERMS):
        return False
    return any(_term_present(term, normalized, tokens) for term in AFFIRMATIVE_TERMS)


def resolve_contact_target(
    *,
    contact_id: str,
    channel: str,
    allowlist_config: str | Path,
    explicit_target: str | None = None,
) -> tuple[str, str]:
    if explicit_target:
        return explicit_target, "cli"

    env_keys = {
        "imessage": ("CARESIGHT_LIVE_IMESSAGE_TARGET", "CARESIGHT_LIVE_CONTACT_TARGET"),
        "facetime": ("CARESIGHT_LIVE_FACETIME_TARGET", "CARESIGHT_LIVE_CONTACT_TARGET"),
    }
    for key in env_keys[channel]:
        value = os.environ.get(key, "").strip()
        if value:
            return value, f"env:{key}"

    allowlist = load_contact_allowlist(allowlist_config)
    try:
        channel_ref = str(allowlist[contact_id].get("channel_refs", {}).get(channel, "")).strip()
    except KeyError as exc:
        raise ValueError(f"contact id not allowlisted: {contact_id}") from exc
    if channel_ref and channel_ref != "redacted-local-channel-ref":
        return channel_ref, "allowlist"

    raise ValueError(
        f"missing live {channel} target for {contact_id}; set CARESIGHT_LIVE_{channel.upper()}_TARGET "
        "or use an ignored private allowlist"
    )


def send_imessage(
    target: str,
    message: str,
    *,
    attachment_path: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    attachment = Path(attachment_path).expanduser() if attachment_path else None
    if attachment and not attachment.exists():
        raise FileNotFoundError(f"iMessage attachment not found: {attachment}")
    backend = os.environ.get("CARESIGHT_IMESSAGE_BACKEND", "auto").strip().casefold()
    if backend in {"auto", "imsg"} and shutil.which("imsg"):
        return send_imessage_with_imsg(target, message, attachment_path=attachment, dry_run=dry_run)
    if backend == "imsg":
        raise RuntimeError("imsg backend requested but unavailable")
    command = _imessage_command(target, message, attachment)
    if dry_run:
        delivery = {
            "status": "dry_run",
            "platform": "macos_messages",
            "command_preview": ["osascript", "-e", "<script>", "<redacted-target>", "<message>"],
        }
        if attachment:
            delivery["attachment"] = _redacted_attachment(attachment)
        return delivery

    result = subprocess.run(command, capture_output=True, check=False, text=True)
    if result.returncode != 0:
        raise RuntimeError(_redact_text(result.stderr.strip() or result.stdout.strip() or "osascript failed", target))
    delivery = {"status": "sent", "platform": "macos_messages_applescript"}
    if attachment:
        delivery["attachment"] = _redacted_attachment(attachment)
    return delivery


def send_imessage_with_imsg(
    target: str,
    message: str,
    *,
    attachment_path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    command = ["imsg", "send", "--to", target, "--text", message, "--service", "imessage"]
    if attachment_path is not None:
        command.extend(["--file", str(attachment_path)])
    if dry_run:
        delivery = {
            "status": "dry_run",
            "platform": "imsg",
            "command_preview": ["imsg", "send", "--to", "<redacted-target>", "--text", "<message>"],
        }
        if attachment_path is not None:
            delivery["command_preview"].extend(["--file", "<redacted-attachment>"])
            delivery["attachment"] = _redacted_attachment(attachment_path)
        return delivery
    result = subprocess.run(command, capture_output=True, check=False, text=True)
    if result.returncode != 0:
        raise RuntimeError(_redact_text(result.stderr.strip() or result.stdout.strip() or "imsg send failed", target))
    delivery = {"status": "sent", "platform": "imsg"}
    if attachment_path is not None:
        delivery["attachment"] = _redacted_attachment(attachment_path)
    return delivery


def open_facetime(target: str, *, dry_run: bool = False) -> dict[str, Any]:
    url = "facetime://" + quote(target, safe="@+")
    if dry_run:
        return {"status": "dry_run", "platform": "facetime", "url_preview": "facetime://<redacted-target>"}

    obs_scene = switch_obs_to_facetime_scene()
    result = subprocess.run(["open", url], capture_output=True, check=False, text=True)
    if result.returncode != 0:
        raise RuntimeError(_redact_text(result.stderr.strip() or result.stdout.strip() or "open facetime failed", target))
    auto_call = os.environ.get("CARESIGHT_FACETIME_PRESS_CALL", "1").strip() not in {"0", "false", "False"}
    call_result = press_facetime_call_button(target) if auto_call else {"status": "not_requested"}
    return {"status": "open_requested", "platform": "facetime", "obs_scene": obs_scene, "call_button": call_result}


def switch_obs_to_facetime_scene() -> dict[str, Any]:
    scene = os.environ.get("CARESIGHT_OBS_FACETIME_SCENE", "").strip()
    if not scene:
        return {"status": "not_requested"}
    repo_root = Path(__file__).resolve().parents[5]
    aitum_result = switch_aitum_vertical_scene(repo_root, scene)
    if aitum_result["status"] == "scene_requested":
        return aitum_result

    script = repo_root / "apps" / "obs-hub" / "tools" / "setup_obs_scenes.py"
    python = repo_root / ".venv-obs" / "bin" / "python"
    if not python.exists():
        python = Path(shutil.which("python3") or "python3")
    if not script.exists():
        return {"status": "blocked", "reason": "setup_obs_scenes_missing", "scene": scene}
    video_mode = os.environ.get("CARESIGHT_OBS_FACETIME_VIDEO_MODE", "").strip().lower()
    if not video_mode:
        video_mode = "portrait" if scene == "CareSight Hub - FaceTime Mobile" else "landscape"
    command = [str(python), str(script), "--scene", scene, "--video-mode", video_mode, "--refresh-overlays"]
    result = subprocess.run(command, cwd=repo_root, capture_output=True, check=False, text=True, timeout=10)
    if result.returncode != 0:
        return {
            "status": "failed",
            "scene": scene,
            "preferred_path": aitum_result,
            "returncode": result.returncode,
            "stderr": result.stderr.strip()[-500:],
        }
    return {"status": "scene_requested", "scene": scene, "video_mode": video_mode, "preferred_path": aitum_result}


def switch_aitum_vertical_scene(repo_root: Path, scene: str) -> dict[str, Any]:
    mode = os.environ.get("CARESIGHT_AITUM_VERTICAL_MODE", "off").strip().lower()
    if mode in {"0", "off", "false", "disabled"}:
        return {"status": "not_requested", "path": "aitum_vertical"}
    script = repo_root / "apps" / "obs-hub" / "tools" / "aitum_vertical.py"
    python = repo_root / ".venv-obs" / "bin" / "python"
    if not python.exists():
        python = Path(shutil.which("python3") or "python3")
    if not script.exists():
        return {"status": "blocked", "path": "aitum_vertical", "reason": "aitum_vertical_tool_missing"}

    aitum_scene = os.environ.get("CARESIGHT_AITUM_VERTICAL_SCENE", scene).strip() or scene
    command = [
        str(python),
        str(script),
        "switch",
        "--scene",
        aitum_scene,
        "--start-virtual-camera",
        "--json",
    ]
    result = subprocess.run(command, cwd=repo_root, capture_output=True, check=False, text=True, timeout=10)
    if result.returncode != 0:
        if mode in {"1", "on", "true", "required"}:
            return {
                "status": "failed",
                "path": "aitum_vertical",
                "scene": aitum_scene,
                "returncode": result.returncode,
                "stderr": result.stderr.strip()[-500:],
                "stdout": result.stdout.strip()[-500:],
            }
        return {"status": "fallback", "path": "aitum_vertical", "scene": aitum_scene, "reason": "not_available"}
    try:
        payload = json.loads(result.stdout)
    except Exception:
        payload = {"raw_stdout": result.stdout.strip()[-500:]}
    status = str(payload.get("status", "scene_requested"))
    if status != "scene_requested":
        if mode in {"1", "on", "true", "required"}:
            return {"status": "failed", "path": "aitum_vertical", "scene": aitum_scene, "payload": payload}
        return {"status": "fallback", "path": "aitum_vertical", "scene": aitum_scene, "payload": payload}
    return {"status": "scene_requested", "path": "aitum_vertical", "scene": aitum_scene, "payload": payload}


def press_facetime_call_button(target: str) -> dict[str, Any]:
    script = """
tell application "FaceTime" to activate
delay 1.8
tell application "System Events"
  tell process "FaceTime"
    set didClick to false
    set clickMethod to "none"
    if not (exists window 1) then error "FaceTime window not available"

    repeat with buttonLabel in {"Call", "Video", "FaceTime"}
      if exists button buttonLabel of window 1 then
        click button buttonLabel of window 1
        set didClick to true
        set clickMethod to "accessibility_button:" & buttonLabel
        exit repeat
      end if
    end repeat

    if didClick is false then
      set windowPosition to position of window 1
      set windowSize to size of window 1
      set callX to (item 1 of windowPosition) + 84
      set callY to (item 2 of windowPosition) + (item 2 of windowSize) - 57
      click at {callX, callY}
      set didClick to true
      set clickMethod to "coordinate_fallback:" & callX & "," & callY
    end if

    return clickMethod
  end tell
end tell
""".strip()
    result = subprocess.run(["osascript", "-e", script], capture_output=True, check=False, text=True)
    if result.returncode != 0:
        return {
            "status": "failed",
            "error": _redact_text(result.stderr.strip() or result.stdout.strip() or "could not press FaceTime Call", target),
        }
    return {"status": "requested", "method": result.stdout.strip() or "unknown"}


def execute_live_imessage(
    store: Any,
    *,
    request_id: str,
    message: str = DEFAULT_LIVE_MESSAGE,
    contact_id: str = "contact_emergency_primary",
    allowlist_config: str | Path,
    target: str | None = None,
    attachment_path: str | Path | None = None,
    result_name: str | None = None,
    live_approved: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    if not live_approved and not dry_run:
        raise ValueError("live iMessage execution requires --live-approved")

    request = store.get_agent_action_request(request_id)
    draft = store.get_agent_draft(request["source_draft_id"])
    _validate_live_request(request, contact_id=contact_id, destination="imessage")
    resolved_target, target_source = resolve_contact_target(
        contact_id=contact_id,
        channel="imessage",
        allowlist_config=allowlist_config,
        explicit_target=target,
    )
    delivery = send_imessage(resolved_target, message, attachment_path=attachment_path, dry_run=dry_run)
    attempt = _build_live_attempt(
        request=request,
        draft=draft,
        contact_id=contact_id,
        target=resolved_target,
        target_source=target_source,
        channel="imessage",
        message=message,
        delivery=delivery,
        dry_run=dry_run,
        result=result_name or ("imessage_sent" if not dry_run else "imessage_live_dry_run"),
        external_action_performed=not dry_run,
    )
    store.insert_agent_execution_attempt(attempt)
    return attempt


def execute_facetime_if_yes(
    store: Any,
    *,
    request_id: str,
    reply_text: str,
    contact_id: str = "contact_emergency_primary",
    allowlist_config: str | Path,
    target: str | None = None,
    live_approved: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    yes_like = is_yes_like_reply(reply_text)
    if not yes_like:
        request = store.get_agent_action_request(request_id)
        draft = store.get_agent_draft(request["source_draft_id"])
        attempt = _build_live_attempt(
            request=request,
            draft=draft,
            contact_id=contact_id,
            target="",
            target_source="not_resolved",
            channel="facetime",
            message="",
            delivery={"status": "not_requested", "reply_interpreted_as_yes": False},
            dry_run=True,
            result="facetime_not_requested_reply_not_yes_like",
            external_action_performed=False,
        )
        store.insert_agent_execution_attempt(attempt)
        return attempt

    if not live_approved and not dry_run:
        raise ValueError("live FaceTime handoff requires --live-approved")

    request = store.get_agent_action_request(request_id)
    draft = store.get_agent_draft(request["source_draft_id"])
    _validate_live_request(request, contact_id=contact_id, destination="imessage")
    resolved_target, target_source = resolve_contact_target(
        contact_id=contact_id,
        channel="facetime",
        allowlist_config=allowlist_config,
        explicit_target=target,
    )
    delivery = open_facetime(resolved_target, dry_run=dry_run)
    delivery["reply_interpreted_as_yes"] = True
    attempt = _build_live_attempt(
        request=request,
        draft=draft,
        contact_id=contact_id,
        target=resolved_target,
        target_source=target_source,
        channel="facetime",
        message="",
        delivery=delivery,
        dry_run=dry_run,
        result="facetime_open_requested" if not dry_run else "facetime_live_dry_run",
        external_action_performed=not dry_run,
    )
    store.insert_agent_execution_attempt(attempt)
    return attempt


def wait_for_yes_reply(
    *,
    target: str,
    since_unix_seconds: float,
    timeout_seconds: float = 180.0,
    poll_interval_seconds: float = 2.0,
    messages_db: str | Path | None = None,
) -> dict[str, Any]:
    backend = os.environ.get("CARESIGHT_REPLY_WATCH_BACKEND", "auto").strip().casefold()
    if backend in {"auto", "imsg"} and shutil.which("imsg"):
        result = wait_for_yes_reply_with_imsg(
            target=target,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        if result["status"] != "blocked" or backend == "imsg":
            return result
    elif backend == "imsg":
        return {
            "status": "blocked",
            "reason": "imsg_not_installed",
            "instruction": "Install imsg with: brew install steipete/tap/imsg",
            "source": "imsg",
            "target": _redacted_target(target),
        }

    deadline = time.time() + timeout_seconds
    last_error: str | None = None
    while time.time() < deadline:
        try:
            reply = latest_incoming_reply(
                target=target,
                since_unix_seconds=since_unix_seconds,
                messages_db=messages_db,
            )
        except sqlite3.OperationalError as exc:
            last_error = str(exc)
            break
        if reply is not None:
            return {
                "status": "reply_observed",
                "reply_text": reply["text"],
                "reply_interpreted_as_yes": is_yes_like_reply(reply["text"]),
                "source": "macos_messages_db",
                "target": _redacted_target(target),
            }
        time.sleep(poll_interval_seconds)
    if last_error:
        return {
            "status": "blocked",
            "reason": "messages_db_unavailable",
            "error": last_error,
            "instruction": "Grant Full Disk Access to Terminal or the Python runner, then retry.",
            "source": "macos_messages_db",
            "target": _redacted_target(target),
        }
    return {
        "status": "timeout",
        "reply_interpreted_as_yes": False,
        "source": "macos_messages_db",
        "target": _redacted_target(target),
    }


def wait_for_yes_reply_with_imsg(
    *,
    target: str,
    timeout_seconds: float = 180.0,
    poll_interval_seconds: float = 2.0,
) -> dict[str, Any]:
    command = [
        "imsg",
        "watch",
        "--participants",
        target,
        "--json",
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.time() + timeout_seconds
    stderr_tail = ""
    try:
        while time.time() < deadline:
            if process.poll() is not None:
                stderr_tail = (process.stderr.read() if process.stderr else "").strip()[-500:]
                return {
                    "status": "blocked",
                    "reason": "imsg_watch_exited",
                    "error": _redact_text(stderr_tail or "imsg watch exited", target),
                    "instruction": "Confirm imsg is installed and Full Disk Access is enabled for this terminal.",
                    "source": "imsg",
                    "target": _redacted_target(target),
                }
            if not process.stdout:
                break
            readable, _, _ = select.select([process.stdout], [], [], poll_interval_seconds)
            if not readable:
                continue
            line = process.stdout.readline()
            if not line:
                continue
            payload = _parse_imsg_line(line)
            text = _imsg_text(payload)
            is_from_me = _imsg_is_from_me(payload)
            if text and not is_from_me:
                return {
                    "status": "reply_observed",
                    "reply_text": text,
                    "reply_interpreted_as_yes": is_yes_like_reply(text),
                    "source": "imsg",
                    "target": _redacted_target(target),
                }
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()
    return {
        "status": "timeout",
        "reply_interpreted_as_yes": False,
        "source": "imsg",
        "target": _redacted_target(target),
    }


def latest_incoming_reply(
    *,
    target: str,
    since_unix_seconds: float,
    messages_db: str | Path | None = None,
) -> dict[str, Any] | None:
    db_path = Path(messages_db) if messages_db else Path.home() / "Library" / "Messages" / "chat.db"
    apple_threshold = int((since_unix_seconds - 978307200) * 1_000_000_000)
    handles = _target_handle_candidates(target)
    placeholders = ",".join("?" for _ in handles)
    query = f"""
        SELECT message.text, message.date, handle.id
        FROM message
        JOIN handle ON message.handle_id = handle.ROWID
        WHERE message.is_from_me = 0
          AND message.text IS NOT NULL
          AND message.date > ?
          AND handle.id IN ({placeholders})
        ORDER BY message.date DESC
        LIMIT 1
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        row = conn.execute(query, [apple_threshold, *handles]).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {"text": str(row[0]), "date": int(row[1]), "handle": str(row[2])}


def _validate_live_request(request: dict[str, Any], *, contact_id: str, destination: str) -> None:
    if request["stage"] != "staged" or request["execution_state"] != "not_executed":
        raise ValueError("live handoff requires a staged, not_executed request")
    if request.get("destination") != destination:
        raise ValueError(f"live handoff requires destination={destination}")
    if contact_id not in request.get("allowed_contact_ids", []):
        raise ValueError(f"contact id not present on staged request: {contact_id}")
    if not request.get("requires_human_approval"):
        raise ValueError("live handoff requires human approval")


def _build_live_attempt(
    *,
    request: dict[str, Any],
    draft: dict[str, Any],
    contact_id: str,
    target: str,
    target_source: str,
    channel: str,
    message: str,
    delivery: dict[str, Any],
    dry_run: bool,
    result: str,
    external_action_performed: bool,
) -> dict[str, Any]:
    payload = build_hermes_handoff_payload(request, draft=draft)
    payload.update(
        {
            "execution_state": "executed" if external_action_performed else "dry_run",
            "live_channel": channel,
            "live_message_text": message or None,
            "approved_contact_id": contact_id,
            "target": _redacted_target(target) if target else None,
            "target_source": target_source,
            "delivery": delivery,
        }
    )
    return {
        "schema": "agent-execution-attempt",
        "attempt_id": f"attempt_{uuid4().hex}",
        "request_id": request["request_id"],
        "event_id": request["event_id"],
        "created_at": utc_now(),
        "harness": "local_macos_live_handoff",
        "attempt_kind": "live" if external_action_performed else "dry_run",
        "execution_state": "executed" if external_action_performed else "dry_run",
        "result": result,
        "error": None,
        "external_action_performed": external_action_performed,
        "payload": payload,
        "safety_boundaries": [
            "human_review_required",
            "allowlisted_recipient_only",
            "operator_configured_contact_target",
            "no_autonomous_dispatch",
            "no_medical_diagnosis",
            "raw_video_stays_local",
        ],
        "provenance": {
            "source": "sqlite_action_request_and_operator_live_approval",
            "source_fields": ["agent_action_requests", "agent_drafts", "agent_execution_attempts"],
        },
    }


def _imessage_command(target: str, message: str, attachment: Path | None = None) -> list[str]:
    script = """
on run argv
  set targetHandle to item 1 of argv
  set messageText to item 2 of argv
  set attachmentPath to item 3 of argv
  tell application "Messages"
    activate
    set targetService to 1st service whose service type = iMessage
    set targetBuddy to buddy targetHandle of targetService
    send messageText to targetBuddy
    if attachmentPath is not "" then
      set attachmentFile to POSIX file attachmentPath as alias
      delay 2
      send attachmentFile to targetBuddy
      delay 1
    end if
  end tell
end run
""".strip()
    return ["osascript", "-e", script, target, message, str(attachment) if attachment else ""]


def _term_present(term: str, normalized_text: str, tokens: set[str]) -> bool:
    if " " in term or "'" in term:
        return term in normalized_text
    return term in tokens


def _target_handle_candidates(target: str) -> list[str]:
    stripped = target.strip()
    candidates = {stripped}
    digits = "".join(ch for ch in stripped if ch.isdigit())
    if digits:
        candidates.add(digits)
        candidates.add("+" + digits)
        if len(digits) == 10:
            candidates.add("+1" + digits)
        if len(digits) == 11 and digits.startswith("1"):
            candidates.add("+" + digits)
            candidates.add(digits[1:])
    return sorted(candidates)


def _parse_imsg_line(line: str) -> dict[str, Any]:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return {"raw": line}
    return payload if isinstance(payload, dict) else {"raw": payload}


def _imsg_text(payload: dict[str, Any]) -> str:
    for key in ("text", "body", "message", "messageText"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    nested = payload.get("message")
    if isinstance(nested, dict):
        return _imsg_text(nested)
    return ""


def _imsg_is_from_me(payload: dict[str, Any]) -> bool:
    for key in ("isFromMe", "is_from_me", "fromMe"):
        if key in payload:
            return bool(payload[key])
    nested = payload.get("message")
    if isinstance(nested, dict):
        return _imsg_is_from_me(nested)
    return False


def _redacted_target(target: str) -> dict[str, Any]:
    digest = hashlib.sha256(target.encode("utf-8")).hexdigest()[:12]
    return {"redacted": True, "sha256_prefix": digest, "length": len(target)}


def _redacted_attachment(path: Path) -> dict[str, Any]:
    resolved = path.expanduser()
    return {
        "redacted": True,
        "name": resolved.name,
        "suffix": resolved.suffix,
        "exists": resolved.exists(),
    }


def _redact_text(text: str, target: str) -> str:
    return text.replace(target, "<redacted-target>")
