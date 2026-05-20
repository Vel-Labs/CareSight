from __future__ import annotations

import json
import os
import platform
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from caresight.runtime.alerts import draft_caregiver_alert
from caresight.runtime.config import CareSightConfig
from caresight.runtime.dashboard import build_dashboard_state
from caresight.runtime.review import ReviewService
from caresight.storage.sqlite_store import SQLiteStore

CameraAuthorization = Literal["granted", "blocked", "not_checked"]


class LiveProofAuditError(ValueError):
    pass


@dataclass(frozen=True)
class ReadinessInputs:
    config_path: Path
    model_path: Path
    camera_authorization: CameraAuthorization = "not_checked"


class LiveProofAuditCollector:
    def __init__(
        self,
        store: SQLiteStore,
        *,
        now: datetime | None = None,
        max_event_age: timedelta = timedelta(minutes=15),
    ):
        self._store = store
        self._service = ReviewService(store)
        self._now = now or datetime.now(UTC)
        self._max_event_age = max_event_age

    def collect(self, event_id: str) -> dict[str, Any]:
        event_id = event_id.strip()
        if not event_id:
            raise LiveProofAuditError("event_id is required")

        if not self._store.database_path.exists():
            return self._not_complete(event_id, ["missing_sqlite_database"])

        try:
            audit = self._service.get_audit_chain(event_id)
        except KeyError:
            return self._not_complete(event_id, ["missing_event_id"])

        dashboard = build_dashboard_state(self._service)
        alert = draft_caregiver_alert(audit)
        checks = self._completion_checks(audit, dashboard, alert)
        status = "complete" if not checks["blockers"] else "not_complete"

        return {
            "schema": "caresight.live_proof_audit_bundle.v1",
            "generated_at": self._now.isoformat().replace("+00:00", "Z"),
            "status": status,
            "source_of_truth": "sqlite",
            "event_id": event_id,
            "checks": checks,
            "bundle": {
                "event": audit["event"],
                "observations": audit["observations"],
                "reviews": audit["reviews"],
                "journal_entries": audit["journal_entries"],
                "agent_handoffs": audit["agent_handoffs"],
                "dashboard": {
                    "source_of_truth": dashboard["source_of_truth"],
                    "current_state": dashboard["current_state"],
                    "timeline_entry": _find_timeline_entry(dashboard, event_id),
                    "review_controls": dashboard["review_controls"],
                },
                "caregiver_alert_draft": alert,
            },
            "boundaries": [
                "collector_read_only",
                "sqlite_is_canonical",
                "dashboard_and_alert_are_derived_outputs",
                "no_event_creation",
                "no_confirmation_or_dismissal",
                "no_dispatch",
                "no_diagnosis",
            ],
        }

    def _not_complete(self, event_id: str, blockers: list[str]) -> dict[str, Any]:
        return {
            "schema": "caresight.live_proof_audit_bundle.v1",
            "generated_at": self._now.isoformat().replace("+00:00", "Z"),
            "status": "not_complete",
            "source_of_truth": "sqlite",
            "event_id": event_id,
            "checks": {
                "blockers": blockers,
                "warnings": [],
                "freshness": None,
                "counts": {
                    "observations": 0,
                    "reviews": 0,
                    "journal_entries": 0,
                    "agent_handoffs": 0,
                },
                "track_ids": [],
            },
            "bundle": None,
            "boundaries": [
                "collector_read_only",
                "sqlite_is_canonical",
                "no_event_creation",
                "no_confirmation_or_dismissal",
                "no_dispatch",
                "no_diagnosis",
            ],
        }

    def _completion_checks(
        self,
        audit: dict[str, Any],
        dashboard: dict[str, Any],
        alert: dict[str, Any],
    ) -> dict[str, Any]:
        event = audit["event"]
        observations = audit["observations"]
        reviews = audit["reviews"]
        journals = audit["journal_entries"]
        handoffs = audit["agent_handoffs"]
        event_id = event["event_id"]
        blockers: list[str] = []
        warnings: list[str] = []

        observed_track_ids = [
            observation.get("track_id") for observation in observations if observation.get("track_id")
        ]
        if not observations:
            blockers.append("missing_event_observation")
        if not observed_track_ids:
            blockers.append("missing_observation_track_id")
        if not reviews:
            blockers.append("missing_human_review")
        if not journals:
            blockers.append("missing_journal_entry")
        if not handoffs:
            blockers.append("missing_report_only_handoff")
        if _find_timeline_entry(dashboard, event_id) is None:
            blockers.append("missing_dashboard_timeline_entry")
        if alert.get("event_id") != event_id:
            blockers.append("missing_alert_provenance")

        occurred_at = _parse_timestamp(event["occurred_at"])
        age_seconds = (self._now - occurred_at).total_seconds()
        if age_seconds < 0:
            warnings.append("event_timestamp_is_future_relative_to_collector")
        elif age_seconds > self._max_event_age.total_seconds():
            blockers.append("stale_event_id")

        return {
            "blockers": blockers,
            "warnings": warnings,
            "freshness": {
                "occurred_at": event["occurred_at"],
                "max_age_seconds": int(self._max_event_age.total_seconds()),
                "age_seconds": int(age_seconds),
            },
            "counts": {
                "observations": len(observations),
                "reviews": len(reviews),
                "journal_entries": len(journals),
                "agent_handoffs": len(handoffs),
            },
            "track_ids": observed_track_ids,
        }


def build_readiness_report(inputs: ReadinessInputs) -> dict[str, Any]:
    blockers: list[str] = []
    checks: dict[str, Any] = {
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
        },
        "environment": {
            "cwd": os.getcwd(),
        },
        "model": _path_check(inputs.model_path),
        "config": _config_check(inputs.config_path),
        "camera_authorization": {
            "status": inputs.camera_authorization,
            "required_for_live_proof": True,
        },
    }

    if not checks["model"]["exists"]:
        blockers.append("model_missing")
    if checks["config"]["status"] != "ready":
        blockers.append("config_not_ready")
    if inputs.camera_authorization == "blocked":
        blockers.append("camera_authorization_blocked")
    elif inputs.camera_authorization == "not_checked":
        blockers.append("camera_authorization_not_verified")

    db_path = checks["config"].get("storage_database_path")
    if db_path:
        checks["sqlite"] = _path_check(Path(db_path))
        checks["sqlite"]["required_before_bundle"] = True

    return {
        "schema": "caresight.live_proof_readiness.v1",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "ready" if not blockers else "not_ready",
        "checks": checks,
        "blockers": blockers,
        "boundaries": [
            "readiness_only",
            "does_not_create_events",
            "does_not_confirm_or_dismiss_events",
            "camera_authorization_must_be_resolved_by_operator",
        ],
    }


def write_json_report(payload: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _path_check(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
    }


def _config_check(path: Path) -> dict[str, Any]:
    result = _path_check(path)
    if not path.exists():
        result["status"] = "missing"
        return result
    try:
        config = CareSightConfig.load(path)
    except Exception as exc:  # pragma: no cover - exact parser failures are environment-specific.
        result["status"] = "invalid"
        result["error"] = str(exc)
        return result
    result.update(
        {
            "status": "ready",
            "camera_id": config.camera.camera_id,
            "camera_name": config.camera.name,
            "room_id": config.room.room_id,
            "room_label": config.room.name,
            "camera_source_type": config.camera.source_type,
            "camera_source_uri": str(config.camera.source_uri),
            "configured_cameras": [
                {
                    "camera_id": camera.camera_id,
                    "camera_name": camera.name,
                    "room_id": camera.room_id,
                    "room_label": camera.room_label,
                    "source_type": camera.source_type,
                }
                for camera in config.cameras
            ],
            "floor_zone_id": config.floor_zone.zone_id,
            "storage_database_path": config.storage.database_path,
        }
    )
    return result


def _find_timeline_entry(dashboard: dict[str, Any], event_id: str) -> dict[str, Any] | None:
    for entry in dashboard.get("timeline", []):
        if entry.get("event_id") == event_id:
            return entry
    return None


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
