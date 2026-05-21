from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from caresight.storage.sqlite_store import utc_now


MODEL_LANES = {
    "reasoning": {
        "provider": "gemma_mlx",
        "default_model": "gemma-4-e2b-it-4bit",
        "path": "apps/caresight-hub/models/reasoning/gemma/gemma-4-e2b-it-4bit",
    },
    "tts": {
        "provider": "holler_mlx",
        "default_model": "holler-0.6b-6bit",
        "path": "apps/caresight-hub/models/tts/holler/holler-0.6b-6bit",
    },
    "vision": {
        "provider": "yolo26_mlx",
        "default_model": "yolo26n.npz",
        "path": "apps/caresight-hub/models/vision/yolo26-mlx/converted/yolo26n.npz",
    },
}

HERMES_CONFIG = {
    "vendor_path": "apps/caresight-hub/vendor/hermes-agent",
    "pinned_tag": "v2026.5.16",
    "workspace_config": "apps/caresight-hub/config/hermes/config.caresight.local.yaml",
    "workspace_env_example": "apps/caresight-hub/config/hermes/env.caresight.example",
    "model_routes": "apps/caresight-hub/config/hermes/model-routes.json",
    "local_openai_base_url": "http://127.0.0.1:8080/v1",
    "default_reasoning_model": "gemma-4-e2b-it-4bit",
}


HARNESS_CANDIDATES = {
    "hermes": {
        "role": "first controlled service-wrapper trial",
        "strengths": [
            "BlueBubbles iMessage route",
            "broad hosted and self-hosted integration catalog",
            "local model/provider routing posture",
        ],
        "care_sight_channels": ["imessage", "apple_notes_via_local_adapter", "facetime_handoff", "tts"],
        "risks": [
            "BlueBubbles setup and credentials are external to CareSight",
            "must not receive raw video or bypass staged action requests",
        ],
    },
    "openclaw": {
        "role": "policy-heavy gateway fallback",
        "strengths": [
            "explicit gateway/session/channel routing",
            "iMessage pairing and allowlist controls",
            "plugin and BYOM architecture",
        ],
        "care_sight_channels": ["imessage", "gateway_hooks", "facetime_handoff", "tts"],
        "risks": [
            "full tool/gateway access must be sandboxed",
            "must disable config writes and require allowlists before live channels",
        ],
    },
}


def build_harness_plan(
    request: dict[str, Any],
    *,
    draft: dict[str, Any],
    preferred_harness: str = "auto",
) -> dict[str, Any]:
    if request["stage"] != "staged" or request["execution_state"] != "not_executed":
        raise ValueError("only staged, not_executed requests can be planned")
    if not request["requires_human_approval"]:
        raise ValueError("harness planning requires human-approved action-request policy")
    if draft["validation_status"] != "validated":
        raise ValueError("harness planning requires a validated source draft")

    harness = choose_harness(request, preferred_harness)
    model_lane = choose_model_lane(request["requested_action"])
    return {
        "schema": "agent-harness-plan",
        "request_id": request["request_id"],
        "event_id": request["event_id"],
        "source_draft_id": request["source_draft_id"],
        "selected_harness": harness,
        "harness": HARNESS_CANDIDATES[harness],
        "model_lane": model_lane,
        "execution_state": "plan_only",
        "requires_human_approval": True,
        "external_execution": "not_allowed_by_this_command",
        "routing": {
            "requested_action": request["requested_action"],
            "destination": request.get("destination"),
            "payload_source": "validated_agent_draft",
            "policy_source": "agent_action_requests",
        },
        "safety_boundaries": [
            "stage_only",
            "human_review_required",
            "no_external_execution",
            "sqlite_canonical",
            "no_raw_video_to_agent",
            "no_autonomous_dispatch",
        ],
    }


def build_hermes_handoff_payload(request: dict[str, Any], *, draft: dict[str, Any]) -> dict[str, Any]:
    if request["stage"] != "staged" or request["execution_state"] != "not_executed":
        raise ValueError("only staged, not_executed requests can become Hermes handoff payloads")
    if draft["validation_status"] != "validated":
        raise ValueError("Hermes handoff payload requires a validated source draft")
    if request.get("destination") in {"imessage", "facetime"} and not request.get("allowed_contact_ids"):
        raise ValueError("Hermes handoff payload requires an allowlisted contact for live-contact destinations")

    escalation_level = request.get("escalation_level", "attention")
    response_options = request.get("response_options", [])
    message = _render_handoff_message(draft, escalation_level, response_options)
    return {
        "schema": "hermes-handoff-payload",
        "request_id": request["request_id"],
        "event_id": request["event_id"],
        "harness": "hermes",
        "execution_state": "payload_only",
        "destination": request.get("destination"),
        "recipient_role": request.get("recipient_role"),
        "allowed_contact_ids": request.get("allowed_contact_ids", []),
        "escalation_level": escalation_level,
        "message_text": message,
        "response_options": response_options,
        "media_options": {
            "screen_capture": "available_by_human_request_only"
            if "request_local_screen_capture" in response_options
            else "not_offered",
            "facetime_handoff": "available_by_human_request_only"
            if "request_facetime_handoff" in response_options
            else "not_offered",
            "obs_virtual_camera": "operator_configured_only",
        },
        "payload_source": {
            "draft_id": draft["draft_id"],
            "draft_validation_status": draft["validation_status"],
            "source_of_truth": draft["source_of_truth"],
            "provenance": draft["provenance"],
        },
        "safety_boundaries": [
            "payload_only",
            "human_review_required",
            "allowlisted_recipient_only",
            "no_external_execution",
            "no_raw_video_to_agent",
            "no_autonomous_dispatch",
            "sqlite_canonical",
        ],
    }


def build_execution_attempt(
    store: Any,
    *,
    request: dict[str, Any],
    payload: dict[str, Any],
    harness: str,
    attempt_kind: str,
    result: str,
    error: str | None = None,
    execution_state: str = "dry_run",
) -> dict[str, Any]:
    if harness not in HARNESS_CANDIDATES:
        raise ValueError(f"unsupported harness: {harness}")
    if attempt_kind != "dry_run":
        raise ValueError("this local prototype only records dry_run attempts without live execution")
    if execution_state not in {"dry_run", "blocked"}:
        raise ValueError(f"unsupported dry-run execution state: {execution_state}")
    if request["stage"] != "staged" or request["execution_state"] != "not_executed":
        raise ValueError("execution attempts require a staged, not_executed action request")
    if payload.get("request_id") != request["request_id"]:
        raise ValueError("payload request_id does not match action request")

    attempt = {
        "schema": "agent-execution-attempt",
        "attempt_id": f"attempt_{uuid4().hex}",
        "request_id": request["request_id"],
        "event_id": request["event_id"],
        "created_at": utc_now(),
        "harness": harness,
        "attempt_kind": attempt_kind,
        "execution_state": execution_state,
        "result": result,
        "error": error,
        "external_action_performed": False,
        "payload": payload,
        "safety_boundaries": [
            "dry_run_only",
            "human_review_required",
            "no_external_execution",
            "sqlite_canonical",
            "no_autonomous_dispatch",
        ],
        "provenance": {
            "source": "sqlite_action_request_and_payload",
            "source_fields": [
                "agent_action_requests",
                "agent_drafts",
                "agent_execution_attempts",
            ],
        },
    }
    store.insert_agent_execution_attempt(attempt)
    return attempt


def run_hermes_dry_run(
    store: Any,
    *,
    request: dict[str, Any],
    draft: dict[str, Any],
    vendor_path: str | Path = HERMES_CONFIG["vendor_path"],
) -> dict[str, Any]:
    payload = build_hermes_handoff_payload(request, draft=draft)
    preflight = invoke_hermes_no_send_preflight(vendor_path)
    execution_state = "dry_run" if preflight["status"] == "ready" else "blocked"
    result = "hermes_no_send_preflight_ready" if execution_state == "dry_run" else "blocked_hermes_preflight"
    payload_with_preflight = {**payload, "hermes_preflight": preflight}
    return build_execution_attempt(
        store,
        request=request,
        payload=payload_with_preflight,
        harness="hermes",
        attempt_kind="dry_run",
        execution_state=execution_state,
        result=result,
        error=preflight.get("error"),
    )


def invoke_hermes_no_send_preflight(vendor_path: str | Path) -> dict[str, Any]:
    resolved_vendor = Path(vendor_path)
    if not resolved_vendor.exists():
        return {
            "status": "blocked",
            "reason": "vendor_path_missing",
            "vendor_path": str(resolved_vendor),
            "external_action_performed": False,
        }

    inserted_path = str(resolved_vendor)
    sys.path.insert(0, inserted_path)
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
                "reason": "hermes_message_directory_unavailable",
                "tool": SEND_MESSAGE_SCHEMA["name"],
                "action": "list",
                "error": result["error"],
                "external_action_performed": False,
            }
        return {
            "status": "ready",
            "tool": SEND_MESSAGE_SCHEMA["name"],
            "action": "list",
            "result_summary": _summarize_hermes_directory_result(result),
            "result_redacted": True,
            "external_action_performed": False,
        }
    except Exception as exc:
        return {
            "status": "blocked",
            "reason": "hermes_import_failed",
            "error": str(exc),
            "external_action_performed": False,
        }
    finally:
        if sys.path and sys.path[0] == inserted_path:
            sys.path.pop(0)


def _summarize_hermes_directory_result(result: Any) -> dict[str, Any]:
    targets = result.get("targets") if isinstance(result, dict) else None
    if not isinstance(targets, str):
        return {"available": bool(result)}
    target_lines = [line for line in targets.splitlines() if line.startswith("  ")]
    return {
        "available": bool(target_lines),
        "target_count": len(target_lines),
        "target_names_redacted": True,
    }


def choose_harness(request: dict[str, Any], preferred_harness: str) -> str:
    if preferred_harness in {"hermes", "openclaw"}:
        return preferred_harness
    action = request["requested_action"]
    destination = request.get("destination")
    if action in {"send_imessage_draft", "create_apple_note", "prepare_facetime_handoff"}:
        return "hermes"
    if destination in {"imessage", "facetime", "apple_notes"}:
        return "hermes"
    return "openclaw"


def choose_model_lane(requested_action: str) -> dict[str, str]:
    if requested_action == "play_tts_utterance":
        return MODEL_LANES["tts"]
    return MODEL_LANES["reasoning"]


def _render_handoff_message(draft: dict[str, Any], escalation_level: str, response_options: list[str]) -> str:
    prefix = "CareSight noted a possible event"
    if escalation_level == "urgent_handoff":
        prefix = "CareSight noted a possible urgent event"
    elif escalation_level == "routine":
        prefix = "CareSight has a routine update"

    asks: list[str] = []
    if "request_local_screen_capture" in response_options:
        asks.append("I can provide a local screen capture from the configured video feed if you want it")
    if "request_facetime_handoff" in response_options:
        asks.append("or I can prepare a FaceTime handoff so you can view the feed")
    if "acknowledge_text_update" in response_options:
        asks.append("you can also reply with a text update for the journal")
    ask_text = " ".join(asks).strip()
    if ask_text:
        ask_text = f" {ask_text}."
    return f"{prefix}. {draft['draft_text']}{ask_text}"


def build_hermes_config_plan() -> dict[str, Any]:
    return {
        "schema": "hermes-config-plan",
        "harness": "hermes",
        "role": "service-capable runner behind CareSight staged action requests",
        "vendor": {
            "path": HERMES_CONFIG["vendor_path"],
            "pinned_tag": HERMES_CONFIG["pinned_tag"],
            "install_scope": "workspace_vendor_submodule",
            "global_install_performed": False,
        },
        "local_model_serving": {
            "default": "local_openai_compatible_endpoint",
            "base_url": HERMES_CONFIG["local_openai_base_url"],
            "model": HERMES_CONFIG["default_reasoning_model"],
            "reasoning_lane": MODEL_LANES["reasoning"],
            "tts_lane": MODEL_LANES["tts"],
            "openrouter_required": False,
            "openrouter_use": "explicit_cloud_fallback_only",
        },
        "workspace_files": {
            "config_template": HERMES_CONFIG["workspace_config"],
            "env_example": HERMES_CONFIG["workspace_env_example"],
            "model_routes": HERMES_CONFIG["model_routes"],
        },
        "routing_policy": {
            "input_source": "validated_agent_drafts",
            "action_source": "agent_action_requests",
            "execution": "not_enabled",
            "approval": "human_required_before_any_live_harness",
        },
        "safety_boundaries": [
            "sqlite_canonical",
            "stage_only",
            "no_external_execution",
            "no_raw_video_to_agent",
            "no_autonomous_dispatch",
            "no_cloud_router_by_default",
        ],
    }
