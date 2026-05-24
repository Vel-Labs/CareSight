from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EscalationMethod:
    method_id: str
    execution_mode: str
    requires_human_approval: bool


NO_SEND_DRY_RUN = EscalationMethod("no_send_agent_dry_run", "dry_run", False)
OBS_UPDATE = EscalationMethod("obs_overlay_update", "local_only", False)
TEXT_HANDOFF = EscalationMethod("text_handoff", "human_approved_live", True)
FACETIME_HANDOFF = EscalationMethod("facetime_handoff", "reply_gated_live", True)
REVIEW_ONLY = EscalationMethod("review_only", "local_only", False)
