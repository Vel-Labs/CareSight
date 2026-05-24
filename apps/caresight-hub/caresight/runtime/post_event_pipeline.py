from __future__ import annotations

import json


def should_run_live_handoff(event: dict) -> bool:
    return event.get("event_type") == "possible_floor_stay"


def format_post_event_agent_line(receipt: dict) -> str:
    return "post_event_agent_dry_run " + json.dumps(receipt, sort_keys=True)


def format_post_event_agent_live_line(receipt: dict) -> str:
    return "post_event_agent_live_run " + json.dumps(receipt, sort_keys=True)


def format_post_event_agent_error_line(event_id: str, error: BaseException) -> str:
    payload = {
        "error": str(error),
        "event_id": event_id,
        "external_action_performed": False,
        "status": "post_event_agent_dry_run_failed",
    }
    return "post_event_agent_dry_run_failed " + json.dumps(payload, sort_keys=True)


def format_post_event_agent_live_error_line(event_id: str, error: BaseException) -> str:
    payload = {
        "error": str(error),
        "event_id": event_id,
        "external_action_performed": False,
        "status": "post_event_agent_live_run_failed",
    }
    return "post_event_agent_live_run_failed " + json.dumps(payload, sort_keys=True)


def format_post_event_agent_live_skip_line(event_id: str) -> str:
    payload = {
        "event_id": event_id,
        "reason": "post_event_agent_live_run_already_in_progress",
        "status": "post_event_agent_live_run_skipped",
    }
    return "post_event_agent_live_run_skipped " + json.dumps(payload, sort_keys=True)
