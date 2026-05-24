from __future__ import annotations

import hashlib
import re
from typing import Any


EXPORT_CLASSIFICATIONS = {"local-only", "caregiver-shareable", "clinical-review", "do-not-share"}
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")


def classify_journal_export(entry: dict[str, Any], classification: str | None = None) -> dict[str, Any]:
    export_classification = classification or entry.get("export_classification") or "local-only"
    if export_classification not in EXPORT_CLASSIFICATIONS:
        raise ValueError(f"unsupported journal export classification: {export_classification}")
    share_allowed = export_classification == "caregiver-shareable"
    return {
        "journal_id": entry["journal_id"],
        "export_classification": export_classification,
        "export_allowed": share_allowed,
        "share_allowed": share_allowed,
        "human_review_required": export_classification in {"clinical-review", "do-not-share", "local-only"},
        "blocked_reason": None if share_allowed else f"{export_classification}_not_shareable_without_human_review",
    }


def redact_text_for_export(text: str) -> tuple[str, list[str]]:
    labels: list[str] = []
    redacted = text
    if _EMAIL.search(redacted):
        labels.append("email")
        redacted = _EMAIL.sub("[redacted-email]", redacted)
    if _PHONE.search(redacted):
        labels.append("phone_number")
        redacted = _PHONE.sub("[redacted-phone]", redacted)
    return redacted, labels


def build_privacy_redaction_receipt(
    *,
    text: str,
    input_type: str = "journal_text",
    engine: str = "local_rules",
    model_manifest_id: str | None = None,
) -> dict[str, Any]:
    _redacted, labels = redact_text_for_export(text)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return {
        "schema": "privacy-redaction-receipt",
        "receipt_id": f"redaction_receipt_{digest}",
        "input_type": input_type,
        "redaction_engine": engine,
        "model_manifest_id": model_manifest_id,
        "labels_detected": labels,
        "redaction_status": "completed" if labels else "not_attempted",
        "human_review_required": True,
        "not_claimed": [
            "anonymization",
            "hipaa_compliance",
            "safety_guarantee",
            "medical_privacy_clearance",
        ],
    }
