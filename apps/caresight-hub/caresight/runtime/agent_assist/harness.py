from __future__ import annotations

from typing import Any


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
