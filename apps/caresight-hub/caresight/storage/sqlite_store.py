from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from caresight.runtime.config import CareSightConfig


class SQLiteStore:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            ensure_column(conn, table="event_observations", column="track_id", definition="TEXT")

    def upsert_config(self, config: CareSightConfig) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cameras (camera_id, name, source_type, source_uri, width, height, fps)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(camera_id) DO UPDATE SET
                  name=excluded.name,
                  source_type=excluded.source_type,
                  source_uri=excluded.source_uri,
                  width=excluded.width,
                  height=excluded.height,
                  fps=excluded.fps
                """,
                (
                    config.camera.camera_id,
                    config.camera.name,
                    config.camera.source_type,
                    str(config.camera.source_uri),
                    config.camera.width,
                    config.camera.height,
                    config.camera.fps,
                ),
            )
            conn.execute(
                """
                INSERT INTO zones (zone_id, camera_id, name, kind, x_min, y_min, x_max, y_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(zone_id) DO UPDATE SET
                  camera_id=excluded.camera_id,
                  name=excluded.name,
                  kind=excluded.kind,
                  x_min=excluded.x_min,
                  y_min=excluded.y_min,
                  x_max=excluded.x_max,
                  y_max=excluded.y_max
                """,
                (
                    config.floor_zone.zone_id,
                    config.floor_zone.camera_id,
                    config.floor_zone.name,
                    config.floor_zone.kind,
                    config.floor_zone.x_min,
                    config.floor_zone.y_min,
                    config.floor_zone.x_max,
                    config.floor_zone.y_max,
                ),
            )
            conn.execute(
                """
                INSERT INTO event_policies (
                  policy_id,
                  event_type,
                  dwell_seconds,
                  severity,
                  confidence,
                  requires_human_confirmation
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(policy_id) DO UPDATE SET
                  event_type=excluded.event_type,
                  dwell_seconds=excluded.dwell_seconds,
                  severity=excluded.severity,
                  confidence=excluded.confidence,
                  requires_human_confirmation=excluded.requires_human_confirmation
                """,
                (
                    "floor_stay_v0",
                    "possible_floor_stay",
                    config.floor_stay.dwell_seconds,
                    config.floor_stay.severity,
                    config.floor_stay.confidence,
                    1,
                ),
            )

    def insert_event(self, event: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (
                  event_id,
                  event_type,
                  occurred_at,
                  camera_id,
                  zone_id,
                  severity,
                  confidence,
                  status,
                  requires_human_confirmation,
                  allowed_actions_json,
                  blocked_actions_json,
                  evidence_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    event["event_type"],
                    event["occurred_at"],
                    event["camera_id"],
                    event.get("zone_id"),
                    event["severity"],
                    event["confidence"],
                    event["status"],
                    int(event["requires_human_confirmation"]),
                    json.dumps(event["allowed_actions"]),
                    json.dumps(event["blocked_actions"]),
                    json.dumps(event["evidence"]),
                ),
            )
            self._insert_event_observation(conn, event)

    def get_event(self, event_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        if row is None:
            raise KeyError(event_id)
        return event_from_row(row)

    def get_event_context(self, event_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                  events.*,
                  cameras.name AS camera_name,
                  zones.name AS zone_name
                FROM events
                LEFT JOIN cameras ON cameras.camera_id = events.camera_id
                LEFT JOIN zones ON zones.zone_id = events.zone_id
                WHERE events.event_id = ?
                """,
                (event_id,),
            ).fetchone()
        if row is None:
            raise KeyError(event_id)
        event = event_from_row(row)
        event["camera_name"] = row["camera_name"]
        event["zone_name"] = row["zone_name"]
        return event

    def list_events(self, status: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if status is None:
                rows = conn.execute(
                    "SELECT * FROM events ORDER BY occurred_at DESC, event_id"
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM events
                    WHERE status = ?
                    ORDER BY occurred_at DESC, event_id
                    """,
                    (status,),
                ).fetchall()
        return [event_from_row(row) for row in rows]

    def list_zones(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM zones ORDER BY zone_id").fetchall()
        return [dict(row) for row in rows]

    def list_event_observations(self, event_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM event_observations
                WHERE event_id = ?
                ORDER BY observation_id
                """,
                (event_id,),
            ).fetchall()
        observations = []
        for row in rows:
            observation = dict(row)
            observation["bbox_json"] = json.loads(row["bbox_json"])
            observations.append(observation)
        return observations

    def record_event_review(
        self,
        event_id: str,
        reviewer: str,
        decision: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        reviewer = reviewer.strip()
        if not reviewer:
            raise ValueError("reviewer is required")
        if is_automation_reviewer(reviewer):
            raise ValueError("reviewer must be an authorized human, not an agent or automation")
        if decision not in {"human_confirmed", "dismissed", "needs_followup"}:
            raise ValueError(f"unsupported decision: {decision}")

        reviewed_at = utc_now()
        review_id = f"review_{uuid4().hex}"
        with self._connect() as conn:
            event_row = conn.execute(
                "SELECT * FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            if event_row is None:
                raise KeyError(event_id)

            conn.execute(
                "UPDATE events SET status = ? WHERE event_id = ?",
                (decision, event_id),
            )
            conn.execute(
                """
                INSERT INTO event_reviews (
                  review_id,
                  event_id,
                  reviewer,
                  decision,
                  note,
                  reviewed_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (review_id, event_id, reviewer, decision, note, reviewed_at),
            )
            event = event_from_row(event_row)
            event["status"] = decision
            journal = self._insert_review_journal(conn, event, reviewer, decision, note, reviewed_at)
            handoff = self._insert_agent_handoff(
                conn,
                event,
                reviewer=reviewer,
                decision=decision,
                review_id=review_id,
                journal_id=journal["journal_id"],
                reviewed_at=reviewed_at,
            )

        return {
            "review_id": review_id,
            "event_id": event_id,
            "reviewer": reviewer,
            "decision": decision,
            "note": note,
            "reviewed_at": reviewed_at,
            "journal_id": journal["journal_id"],
            "handoff_id": handoff["handoff_id"],
        }

    def list_journal_entries(self, event_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM journal_entries
                WHERE event_id = ?
                ORDER BY created_at, journal_id
                """,
                (event_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_event_reviews(self, event_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM event_reviews
                WHERE event_id = ?
                ORDER BY reviewed_at, review_id
                """,
                (event_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_agent_handoffs(self, event_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM agent_handoffs
                WHERE event_id = ?
                ORDER BY created_at, handoff_id
                """,
                (event_id,),
            ).fetchall()
        handoffs = []
        for row in rows:
            handoff = dict(row)
            handoff["payload"] = json.loads(row["payload_json"])
            handoffs.append(handoff)
        return handoffs

    def insert_agent_draft(self, draft: dict[str, Any]) -> None:
        with self._connect() as conn:
            event_row = conn.execute(
                "SELECT event_id FROM events WHERE event_id = ?",
                (draft["event_id"],),
            ).fetchone()
            if event_row is None:
                raise KeyError(draft["event_id"])
            conn.execute(
                """
                INSERT INTO agent_drafts (
                  draft_id,
                  event_id,
                  created_at,
                  provider,
                  purpose,
                  validation_status,
                  draft_text,
                  safe_rewrite,
                  blocked_claims_json,
                  safety_boundaries_json,
                  provenance_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    draft["draft_id"],
                    draft["event_id"],
                    draft["created_at"],
                    draft["provider"],
                    draft["purpose"],
                    draft["validation_status"],
                    draft["draft_text"],
                    draft.get("safe_rewrite"),
                    json.dumps(draft["blocked_claims"], sort_keys=True),
                    json.dumps(draft["safety_boundaries"], sort_keys=True),
                    json.dumps(draft["provenance"], sort_keys=True),
                ),
            )

    def list_agent_drafts(self, event_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM agent_drafts
                WHERE event_id = ?
                ORDER BY created_at, draft_id
                """,
                (event_id,),
            ).fetchall()
        return [agent_draft_from_row(row) for row in rows]

    def get_agent_draft(self, draft_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM agent_drafts WHERE draft_id = ?",
                (draft_id,),
            ).fetchone()
        if row is None:
            raise KeyError(draft_id)
        return agent_draft_from_row(row)

    def insert_agent_action_request(self, request: dict[str, Any]) -> None:
        with self._connect() as conn:
            draft_row = conn.execute(
                "SELECT draft_id FROM agent_drafts WHERE draft_id = ? AND event_id = ?",
                (request["source_draft_id"], request["event_id"]),
            ).fetchone()
            if draft_row is None:
                raise KeyError(request["source_draft_id"])
            conn.execute(
                """
                INSERT INTO agent_action_requests (
                  request_id,
                  event_id,
                  created_at,
                  requested_action,
                  stage,
                  execution_state,
                  requires_human_approval,
                  source_draft_id,
                  destination,
                  safety_boundaries_json,
                  provenance_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request["request_id"],
                    request["event_id"],
                    request["created_at"],
                    request["requested_action"],
                    request["stage"],
                    request["execution_state"],
                    int(request["requires_human_approval"]),
                    request["source_draft_id"],
                    request.get("destination"),
                    json.dumps(request["safety_boundaries"], sort_keys=True),
                    json.dumps(request["provenance"], sort_keys=True),
                ),
            )

    def list_agent_action_requests(self, event_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM agent_action_requests
                WHERE event_id = ?
                ORDER BY created_at, request_id
                """,
                (event_id,),
            ).fetchall()
        return [agent_action_request_from_row(row) for row in rows]

    def get_agent_action_request(self, request_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM agent_action_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            raise KeyError(request_id)
        return agent_action_request_from_row(row)

    def _insert_event_observation(self, conn: sqlite3.Connection, event: dict[str, Any]) -> None:
        evidence = event["evidence"]
        bbox = evidence.get("bbox_xyxy")
        detection_confidence = evidence.get("detection_confidence")
        if bbox is None or detection_confidence is None:
            return

        conn.execute(
            """
            INSERT INTO event_observations (
              event_id,
              observed_at,
              class_name,
              confidence,
              bbox_json,
              track_id,
              zone_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                event["occurred_at"],
                "person",
                detection_confidence,
                json.dumps(bbox),
                evidence.get("track_id"),
                event.get("zone_id"),
            ),
        )

    def _insert_review_journal(
        self,
        conn: sqlite3.Connection,
        event: dict[str, Any],
        reviewer: str,
        decision: str,
        note: str | None,
        created_at: str,
    ) -> dict[str, str]:
        journal_id = f"journal_{uuid4().hex}"
        title = f"{event['event_type']} {decision}"
        body = review_journal_body(event, reviewer, decision, note)
        conn.execute(
            """
            INSERT INTO journal_entries (
              journal_id,
              event_id,
              entry_type,
              title,
              body,
              created_at,
              created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (journal_id, event["event_id"], "event_review", title, body, created_at, reviewer),
        )
        return {"journal_id": journal_id, "body": body}

    def _insert_agent_handoff(
        self,
        conn: sqlite3.Connection,
        event: dict[str, Any],
        reviewer: str,
        decision: str,
        review_id: str,
        journal_id: str,
        reviewed_at: str,
    ) -> dict[str, str]:
        handoff_id = f"handoff_{uuid4().hex}"
        evidence = event["evidence"]
        payload = {
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "status": decision,
            "review_id": review_id,
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "journal_id": journal_id,
            "snapshot_path": evidence.get("snapshot_path"),
            "requires_human_confirmation": event["requires_human_confirmation"],
            "blocked_actions": event["blocked_actions"],
            "human_confirmation_requirement": "Agents may summarize or draft; humans must confirm or dismiss events.",
        }
        conn.execute(
            """
            INSERT INTO agent_handoffs (
              handoff_id,
              event_id,
              target_framework,
              purpose,
              payload_json,
              status,
              created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                handoff_id,
                event["event_id"],
                "local_agent",
                "review_acknowledgement_summary",
                json.dumps(payload, sort_keys=True),
                "report_only",
                reviewed_at,
            ),
        )
        return {"handoff_id": handoff_id}

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.database_path)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            with conn:
                yield conn
        finally:
            conn.close()


def event_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "schema": "care-event",
        "event_id": row["event_id"],
        "event_type": row["event_type"],
        "occurred_at": row["occurred_at"],
        "camera_id": row["camera_id"],
        "zone_id": row["zone_id"],
        "severity": row["severity"],
        "confidence": row["confidence"],
        "status": row["status"],
        "requires_human_confirmation": bool(row["requires_human_confirmation"]),
        "allowed_actions": json.loads(row["allowed_actions_json"]),
        "blocked_actions": json.loads(row["blocked_actions_json"]),
        "evidence": json.loads(row["evidence_json"]),
    }


def agent_draft_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "schema": "agent-draft",
        "draft_id": row["draft_id"],
        "event_id": row["event_id"],
        "created_at": row["created_at"],
        "provider": row["provider"],
        "source_of_truth": "sqlite",
        "purpose": row["purpose"],
        "validation_status": row["validation_status"],
        "draft_text": row["draft_text"],
        "safe_rewrite": row["safe_rewrite"],
        "blocked_claims": json.loads(row["blocked_claims_json"]),
        "safety_boundaries": json.loads(row["safety_boundaries_json"]),
        "provenance": json.loads(row["provenance_json"]),
    }


def agent_action_request_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "schema": "agent-action-request",
        "request_id": row["request_id"],
        "event_id": row["event_id"],
        "created_at": row["created_at"],
        "requested_action": row["requested_action"],
        "stage": row["stage"],
        "execution_state": row["execution_state"],
        "requires_human_approval": bool(row["requires_human_approval"]),
        "source_draft_id": row["source_draft_id"],
        "destination": row["destination"],
        "safety_boundaries": json.loads(row["safety_boundaries_json"]),
        "provenance": json.loads(row["provenance_json"]),
    }


def review_journal_body(
    event: dict[str, Any],
    reviewer: str,
    decision: str,
    note: str | None,
) -> str:
    decision_text = decision.replace("_", " ")
    lines = [
        f"Event {event['event_id']} was {decision_text} by {reviewer}.",
        f"Event type: {event['event_type']}.",
        f"Status: {decision}.",
    ]
    if note:
        lines.append(f"Reviewer note: {note}")
    lines.append("Blocked actions remained blocked: " + ", ".join(event["blocked_actions"]) + ".")
    return "\n".join(lines)


def is_automation_reviewer(reviewer: str) -> bool:
    normalized = reviewer.strip().lower().replace("_", " ").replace("-", " ")
    automation_names = {"agent", "ai", "llm", "dashboard", "script", "automation", "carebot"}
    return normalized in automation_names


def ensure_column(conn: sqlite3.Connection, *, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column in columns:
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


SCHEMA_SQL = (Path(__file__).resolve().parent / "migrations" / "001_init.sql").read_text(encoding="utf-8")
