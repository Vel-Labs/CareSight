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
