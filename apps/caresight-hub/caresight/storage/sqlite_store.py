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
from caresight.storage.connection import sqlite_connection
from caresight.storage.migrations import SCHEMA_SQL, ensure_column
from caresight.storage.reviews import validate_review_transition


class SQLiteStore:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            ensure_column(conn, table="event_observations", column="track_id", definition="TEXT")
            ensure_column(
                conn,
                table="agent_action_requests",
                column="escalation_level",
                definition="TEXT NOT NULL DEFAULT 'attention'",
            )
            ensure_column(conn, table="agent_action_requests", column="recipient_role", definition="TEXT")
            ensure_column(
                conn,
                table="agent_action_requests",
                column="allowed_contact_ids_json",
                definition="TEXT NOT NULL DEFAULT '[]'",
            )
            ensure_column(
                conn,
                table="agent_action_requests",
                column="response_options_json",
                definition="TEXT NOT NULL DEFAULT '[]'",
            )
            ensure_column(
                conn,
                table="event_reviews",
                column="review_purpose",
                definition="TEXT NOT NULL DEFAULT 'initial_review'",
            )
            ensure_column(conn, table="event_reviews", column="amendment_of_review_id", definition="TEXT")
            ensure_column(
                conn,
                table="event_reviews",
                column="previous_status",
                definition="TEXT NOT NULL DEFAULT 'awaiting_human_confirmation'",
            )
            ensure_column(
                conn,
                table="journal_entries",
                column="export_classification",
                definition="TEXT NOT NULL DEFAULT 'local-only'",
            )
            ensure_column(conn, table="journal_entries", column="redaction_receipt_json", definition="TEXT")
            self._rebuild_agent_execution_attempts_if_needed(conn)

    def _rebuild_agent_execution_attempts_if_needed(self, conn: sqlite3.Connection) -> None:
        sql_row = conn.execute(
            """
            SELECT sql FROM sqlite_master
            WHERE type = 'table' AND name = 'agent_execution_attempts'
            """
        ).fetchone()
        if sql_row is None or "pending_execution" in str(sql_row["sql"]):
            return
        conn.executescript(
            """
            ALTER TABLE agent_execution_attempts RENAME TO agent_execution_attempts_old;
            CREATE TABLE agent_execution_attempts (
              attempt_id TEXT PRIMARY KEY,
              request_id TEXT NOT NULL REFERENCES agent_action_requests(request_id) ON DELETE CASCADE,
              event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
              created_at TEXT NOT NULL,
              harness TEXT NOT NULL,
              attempt_kind TEXT NOT NULL CHECK(attempt_kind IN ('dry_run', 'live')),
              execution_state TEXT NOT NULL CHECK(execution_state IN ('pending_execution', 'dry_run', 'blocked', 'executed', 'failed')),
              result TEXT NOT NULL,
              error TEXT,
              external_action_performed INTEGER NOT NULL,
              payload_json TEXT NOT NULL,
              safety_boundaries_json TEXT NOT NULL,
              provenance_json TEXT NOT NULL
            );
            INSERT INTO agent_execution_attempts
            SELECT * FROM agent_execution_attempts_old;
            DROP TABLE agent_execution_attempts_old;
            """
        )

    def insert_appearance_profile(self, profile: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO appearance_profiles (
                  appearance_profile_id,
                  active_date,
                  created_at,
                  updated_at,
                  expires_at,
                  descriptor_source,
                  descriptor_status,
                  source_event_id,
                  source_observation_id,
                  snapshot_path,
                  frame_source,
                  last_seen_at,
                  last_seen_camera_id,
                  last_seen_room,
                  role_assignment,
                  assignment_source,
                  assigned_by,
                  assigned_at,
                  attributes_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                appearance_profile_values(profile),
            )

    def upsert_appearance_profile(self, profile: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO appearance_profiles (
                  appearance_profile_id,
                  active_date,
                  created_at,
                  updated_at,
                  expires_at,
                  descriptor_source,
                  descriptor_status,
                  source_event_id,
                  source_observation_id,
                  snapshot_path,
                  frame_source,
                  last_seen_at,
                  last_seen_camera_id,
                  last_seen_room,
                  role_assignment,
                  assignment_source,
                  assigned_by,
                  assigned_at,
                  attributes_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(appearance_profile_id) DO UPDATE SET
                  active_date=excluded.active_date,
                  updated_at=excluded.updated_at,
                  expires_at=excluded.expires_at,
                  descriptor_source=excluded.descriptor_source,
                  descriptor_status=excluded.descriptor_status,
                  source_event_id=excluded.source_event_id,
                  source_observation_id=excluded.source_observation_id,
                  snapshot_path=excluded.snapshot_path,
                  frame_source=excluded.frame_source,
                  last_seen_at=excluded.last_seen_at,
                  last_seen_camera_id=excluded.last_seen_camera_id,
                  last_seen_room=excluded.last_seen_room,
                  role_assignment=excluded.role_assignment,
                  assignment_source=excluded.assignment_source,
                  assigned_by=excluded.assigned_by,
                  assigned_at=excluded.assigned_at,
                  attributes_json=excluded.attributes_json
                """,
                appearance_profile_values(profile),
            )

    def get_appearance_profile(self, appearance_profile_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM appearance_profiles WHERE appearance_profile_id = ?",
                (appearance_profile_id,),
            ).fetchone()
        if row is None:
            raise KeyError(appearance_profile_id)
        return appearance_profile_from_row(row)

    def list_active_appearance_profiles(
        self,
        *,
        active_date: str | None = None,
        now: str | None = None,
    ) -> list[dict[str, Any]]:
        if now is None:
            now = utc_now()
        if active_date is None:
            active_date = now[:10]
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM appearance_profiles
                WHERE active_date = ?
                  AND expires_at > ?
                ORDER BY last_seen_at DESC, appearance_profile_id
                """,
                (active_date, now),
            ).fetchall()
        return [appearance_profile_from_row(row) for row in rows]

    def insert_appearance_profile_observation(self, observation: dict[str, Any]) -> None:
        with self._connect() as conn:
            profile_row = conn.execute(
                """
                SELECT appearance_profile_id FROM appearance_profiles
                WHERE appearance_profile_id = ?
                """,
                (observation["appearance_profile_id"],),
            ).fetchone()
            if profile_row is None:
                raise KeyError(observation["appearance_profile_id"])
            conn.execute(
                """
                INSERT INTO appearance_profile_observations (
                  profile_observation_id,
                  appearance_profile_id,
                  observed_at,
                  camera_id,
                  room,
                  track_id,
                  source_event_id,
                  source_observation_id,
                  snapshot_path,
                  frame_source,
                  descriptor_source,
                  descriptor_status,
                  confidence,
                  attributes_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                appearance_profile_observation_values(observation),
            )

    def list_appearance_profile_observations(
        self,
        appearance_profile_id: str,
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM appearance_profile_observations
                WHERE appearance_profile_id = ?
                ORDER BY observed_at, profile_observation_id
                """,
                (appearance_profile_id,),
            ).fetchall()
        return [appearance_profile_observation_from_row(row) for row in rows]

    def insert_appearance_profile_sample(self, sample: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO appearance_profile_samples (
                  sample_id,
                  appearance_profile_id,
                  active_date,
                  captured_at,
                  camera_id,
                  room,
                  track_id,
                  source_event_id,
                  source_observation_id,
                  snapshot_path,
                  frame_source,
                  descriptor_status,
                  quality_score,
                  quality_reasons_json,
                  detection_confidence,
                  bbox_json,
                  attributes_json,
                  retained_rank,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                appearance_profile_sample_values(sample),
            )

    def list_appearance_profile_samples(
        self,
        appearance_profile_id: str,
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM appearance_profile_samples
                WHERE appearance_profile_id = ?
                ORDER BY quality_score DESC, captured_at DESC, sample_id
                """,
                (appearance_profile_id,),
            ).fetchall()
        return [appearance_profile_sample_from_row(row) for row in rows]

    def list_appearance_samples_for_date(self, active_date: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM appearance_profile_samples
                WHERE active_date = ?
                ORDER BY appearance_profile_id, quality_score DESC, captured_at DESC, sample_id
                """,
                (active_date,),
            ).fetchall()
        return [appearance_profile_sample_from_row(row) for row in rows]

    def prune_appearance_profile_samples(
        self,
        appearance_profile_id: str,
        *,
        max_samples: int,
        delete_files: bool = True,
    ) -> list[dict[str, Any]]:
        if max_samples < 1:
            raise ValueError("max_samples must be >= 1")
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM appearance_profile_samples
                WHERE appearance_profile_id = ?
                ORDER BY quality_score DESC, captured_at DESC, sample_id
                """,
                (appearance_profile_id,),
            ).fetchall()
            kept = rows[:max_samples]
            removed = rows[max_samples:]
            for rank, row in enumerate(kept, start=1):
                conn.execute(
                    """
                    UPDATE appearance_profile_samples
                    SET retained_rank = ?
                    WHERE sample_id = ?
                    """,
                    (rank, row["sample_id"]),
                )
            for row in removed:
                conn.execute(
                    "DELETE FROM appearance_profile_samples WHERE sample_id = ?",
                    (row["sample_id"],),
                )
        removed_samples = [appearance_profile_sample_from_row(row) for row in removed]
        if delete_files:
            for sample in removed_samples:
                try:
                    Path(sample["snapshot_path"]).unlink(missing_ok=True)
                except OSError:
                    pass
        return removed_samples

    def list_appearance_profiles_for_event(self, event_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT appearance_profiles.*
                FROM appearance_profiles
                LEFT JOIN events
                  ON events.event_id = ?
                LEFT JOIN event_observations
                  ON event_observations.event_id = events.event_id
                LEFT JOIN appearance_profile_observations
                  ON appearance_profile_observations.appearance_profile_id =
                     appearance_profiles.appearance_profile_id
                LEFT JOIN appearance_profile_samples
                  ON appearance_profile_samples.appearance_profile_id =
                     appearance_profiles.appearance_profile_id
                WHERE appearance_profiles.source_event_id = ?
                   OR appearance_profile_observations.source_event_id = ?
                   OR (
                        events.event_id IS NOT NULL
                        AND appearance_profiles.active_date = substr(events.occurred_at, 1, 10)
                        AND event_observations.track_id IS NOT NULL
                        AND (
                          appearance_profile_observations.track_id = event_observations.track_id
                          OR appearance_profile_samples.track_id = event_observations.track_id
                        )
                      )
                ORDER BY appearance_profiles.last_seen_at DESC,
                         appearance_profiles.appearance_profile_id
                """,
                (event_id, event_id, event_id),
            ).fetchall()
        return [appearance_profile_from_row(row) for row in rows]

    def assign_appearance_profile_role(
        self,
        appearance_profile_id: str,
        *,
        role_assignment: str,
        reviewer: str,
        assigned_at: str | None = None,
    ) -> dict[str, Any]:
        role_assignment = role_assignment.strip()
        reviewer = reviewer.strip()
        if not role_assignment:
            raise ValueError("role_assignment is required")
        if not reviewer:
            raise ValueError("reviewer is required")
        if is_automation_reviewer(reviewer):
            raise ValueError("reviewer must be an authorized human, not an agent or automation")
        if assigned_at is None:
            assigned_at = utc_now()

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT appearance_profile_id FROM appearance_profiles
                WHERE appearance_profile_id = ?
                """,
                (appearance_profile_id,),
            ).fetchone()
            if row is None:
                raise KeyError(appearance_profile_id)
            conn.execute(
                """
                UPDATE appearance_profiles
                SET role_assignment = ?,
                    assignment_source = ?,
                    assigned_by = ?,
                    assigned_at = ?,
                    updated_at = ?
                WHERE appearance_profile_id = ?
                """,
                (
                    role_assignment,
                    "human_confirmed",
                    reviewer,
                    assigned_at,
                    assigned_at,
                    appearance_profile_id,
                ),
            )

        return {
            "appearance_profile_id": appearance_profile_id,
            "role_assignment": role_assignment,
            "assignment_source": "human_confirmed",
            "assigned_by": reviewer,
            "assigned_at": assigned_at,
        }

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
        review_purpose: str = "initial_review",
        amendment_of_review_id: str | None = None,
    ) -> dict[str, Any]:
        reviewer = reviewer.strip()
        if not reviewer:
            raise ValueError("reviewer is required")
        if is_automation_reviewer(reviewer):
            raise ValueError("reviewer must be an authorized human, not an agent or automation")

        reviewed_at = utc_now()
        review_id = f"review_{uuid4().hex}"
        with self._connect() as conn:
            event_row = conn.execute(
                "SELECT * FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            if event_row is None:
                raise KeyError(event_id)
            previous_status = str(event_row["status"])
            transition = validate_review_transition(
                previous_status=previous_status,
                decision=decision,
                review_purpose=review_purpose,
                amendment_of_review_id=amendment_of_review_id,
            )

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
                  review_purpose,
                  amendment_of_review_id,
                  previous_status,
                  reviewed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    event_id,
                    reviewer,
                    decision,
                    note,
                    transition.review_purpose,
                    transition.amendment_of_review_id,
                    transition.previous_status,
                    reviewed_at,
                ),
            )
            event = event_from_row(event_row)
            event["status"] = decision
            journal = self._insert_review_journal(
                conn,
                event,
                reviewer,
                decision,
                note,
                reviewed_at,
                review_purpose=transition.review_purpose,
                previous_status=transition.previous_status,
                amendment_of_review_id=transition.amendment_of_review_id,
            )
            handoff = self._insert_agent_handoff(
                conn,
                event,
                reviewer=reviewer,
                decision=decision,
                review_id=review_id,
                journal_id=journal["journal_id"],
                reviewed_at=reviewed_at,
                review_purpose=transition.review_purpose,
                previous_status=transition.previous_status,
                amendment_of_review_id=transition.amendment_of_review_id,
            )

        return {
            "review_id": review_id,
            "event_id": event_id,
            "reviewer": reviewer,
            "decision": decision,
            "note": note,
            "review_purpose": review_purpose,
            "amendment_of_review_id": amendment_of_review_id,
            "previous_status": previous_status,
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

    def update_journal_redaction(
        self,
        journal_id: str,
        *,
        export_classification: str,
        redaction_receipt: dict[str, Any],
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE journal_entries
                SET export_classification = ?, redaction_receipt_json = ?
                WHERE journal_id = ?
                """,
                (export_classification, json.dumps(redaction_receipt, sort_keys=True), journal_id),
            )

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
                  escalation_level,
                  recipient_role,
                  allowed_contact_ids_json,
                  response_options_json,
                  safety_boundaries_json,
                  provenance_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    request.get("escalation_level", "attention"),
                    request.get("recipient_role"),
                    json.dumps(request.get("allowed_contact_ids", []), sort_keys=True),
                    json.dumps(request.get("response_options", []), sort_keys=True),
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
        requests = [agent_action_request_from_row(row) for row in rows]
        for request in requests:
            attempts = self.list_agent_execution_attempts(request["request_id"])
            request["latest_attempt_state"] = latest_attempt_state(attempts)
        return requests

    def get_agent_action_request(self, request_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM agent_action_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            raise KeyError(request_id)
        request = agent_action_request_from_row(row)
        request["latest_attempt_state"] = latest_attempt_state(self.list_agent_execution_attempts(request_id))
        return request

    def insert_agent_execution_attempt(self, attempt: dict[str, Any]) -> None:
        with self._connect() as conn:
            request_row = conn.execute(
                "SELECT event_id FROM agent_action_requests WHERE request_id = ?",
                (attempt["request_id"],),
            ).fetchone()
            if request_row is None:
                raise KeyError(attempt["request_id"])
            if request_row["event_id"] != attempt["event_id"]:
                raise ValueError("execution attempt event_id does not match action request")
            conn.execute(
                """
                INSERT INTO agent_execution_attempts (
                  attempt_id,
                  request_id,
                  event_id,
                  created_at,
                  harness,
                  attempt_kind,
                  execution_state,
                  result,
                  error,
                  external_action_performed,
                  payload_json,
                  safety_boundaries_json,
                  provenance_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt["attempt_id"],
                    attempt["request_id"],
                    attempt["event_id"],
                    attempt["created_at"],
                    attempt["harness"],
                    attempt["attempt_kind"],
                    attempt["execution_state"],
                    attempt["result"],
                    attempt.get("error"),
                    int(attempt["external_action_performed"]),
                    json.dumps(attempt["payload"], sort_keys=True),
                    json.dumps(attempt["safety_boundaries"], sort_keys=True),
                    json.dumps(attempt["provenance"], sort_keys=True),
                ),
            )

    def update_agent_execution_attempt(self, attempt: dict[str, Any]) -> None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT request_id, event_id FROM agent_execution_attempts WHERE attempt_id = ?",
                (attempt["attempt_id"],),
            ).fetchone()
            if row is None:
                raise KeyError(attempt["attempt_id"])
            if row["request_id"] != attempt["request_id"] or row["event_id"] != attempt["event_id"]:
                raise ValueError("execution attempt identity fields cannot change")
            conn.execute(
                """
                UPDATE agent_execution_attempts
                SET harness = ?,
                    attempt_kind = ?,
                    execution_state = ?,
                    result = ?,
                    error = ?,
                    external_action_performed = ?,
                    payload_json = ?,
                    safety_boundaries_json = ?,
                    provenance_json = ?
                WHERE attempt_id = ?
                """,
                (
                    attempt["harness"],
                    attempt["attempt_kind"],
                    attempt["execution_state"],
                    attempt["result"],
                    attempt.get("error"),
                    int(attempt["external_action_performed"]),
                    json.dumps(attempt["payload"], sort_keys=True),
                    json.dumps(attempt["safety_boundaries"], sort_keys=True),
                    json.dumps(attempt["provenance"], sort_keys=True),
                    attempt["attempt_id"],
                ),
            )

    def list_agent_execution_attempts(self, request_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM agent_execution_attempts
                WHERE request_id = ?
                ORDER BY created_at, attempt_id
                """,
                (request_id,),
            ).fetchall()
        return [agent_execution_attempt_from_row(row) for row in rows]

    def list_agent_execution_attempts_for_event(self, event_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM agent_execution_attempts
                WHERE event_id = ?
                ORDER BY created_at, attempt_id
                """,
                (event_id,),
            ).fetchall()
        return [agent_execution_attempt_from_row(row) for row in rows]

    def insert_observation_check(self, check: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO observation_checks (
                  check_id,
                  check_type,
                  started_at,
                  completed_at,
                  camera_id,
                  zone_id,
                  status,
                  frame_count,
                  elapsed_seconds,
                  required_dwell_seconds,
                  event_id,
                  result_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    check["check_id"],
                    check["check_type"],
                    check["started_at"],
                    check["completed_at"],
                    check["camera_id"],
                    check.get("zone_id"),
                    check["status"],
                    check["frame_count"],
                    check["elapsed_seconds"],
                    check.get("required_dwell_seconds"),
                    check.get("event_id"),
                    json.dumps(check["result"], sort_keys=True),
                ),
            )

    def get_observation_check(self, check_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM observation_checks WHERE check_id = ?",
                (check_id,),
            ).fetchone()
        if row is None:
            raise KeyError(check_id)
        return observation_check_from_row(row)

    def list_observation_checks(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM observation_checks
                ORDER BY completed_at DESC, check_id
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [observation_check_from_row(row) for row in rows]

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
        review_purpose: str,
        previous_status: str,
        amendment_of_review_id: str | None,
    ) -> dict[str, str]:
        journal_id = f"journal_{uuid4().hex}"
        title = f"{event['event_type']} {review_purpose} {decision}"
        body = review_journal_body(
            event,
            reviewer,
            decision,
            note,
            review_purpose=review_purpose,
            previous_status=previous_status,
            amendment_of_review_id=amendment_of_review_id,
        )
        conn.execute(
            """
            INSERT INTO journal_entries (
              journal_id,
              event_id,
              entry_type,
              title,
              body,
              created_at,
              created_by,
              export_classification
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (journal_id, event["event_id"], "event_review", title, body, created_at, reviewer, "local-only"),
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
        review_purpose: str,
        previous_status: str,
        amendment_of_review_id: str | None,
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
            "review_purpose": review_purpose,
            "previous_status": previous_status,
            "amendment_of_review_id": amendment_of_review_id,
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
        with sqlite_connection(self.database_path) as conn:
            yield conn


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
        "escalation_level": row["escalation_level"],
        "recipient_role": row["recipient_role"],
        "allowed_contact_ids": json.loads(row["allowed_contact_ids_json"]),
        "response_options": json.loads(row["response_options_json"]),
        "safety_boundaries": json.loads(row["safety_boundaries_json"]),
        "provenance": json.loads(row["provenance_json"]),
    }


def observation_check_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "schema": "observation-check",
        "check_id": row["check_id"],
        "check_type": row["check_type"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
        "camera_id": row["camera_id"],
        "zone_id": row["zone_id"],
        "status": row["status"],
        "frame_count": row["frame_count"],
        "elapsed_seconds": row["elapsed_seconds"],
        "required_dwell_seconds": row["required_dwell_seconds"],
        "event_id": row["event_id"],
        "result": json.loads(row["result_json"]),
    }


def agent_execution_attempt_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "schema": "agent-execution-attempt",
        "attempt_id": row["attempt_id"],
        "request_id": row["request_id"],
        "event_id": row["event_id"],
        "created_at": row["created_at"],
        "harness": row["harness"],
        "attempt_kind": row["attempt_kind"],
        "execution_state": row["execution_state"],
        "result": row["result"],
        "error": row["error"],
        "external_action_performed": bool(row["external_action_performed"]),
        "payload": json.loads(row["payload_json"]),
        "safety_boundaries": json.loads(row["safety_boundaries_json"]),
        "provenance": json.loads(row["provenance_json"]),
    }


def latest_attempt_state(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    if not attempts:
        return {"status": "staged", "attempt_id": None, "result": None, "error": None}
    latest = attempts[-1]
    return {
        "status": latest["execution_state"],
        "attempt_id": latest["attempt_id"],
        "result": latest["result"],
        "error": latest.get("error"),
    }


def appearance_profile_values(profile: dict[str, Any]) -> tuple[Any, ...]:
    return (
        profile["appearance_profile_id"],
        profile["active_date"],
        profile["created_at"],
        profile["updated_at"],
        profile["expires_at"],
        profile.get("descriptor_source", profile.get("created_from")),
        profile["descriptor_status"],
        profile.get("source_event_id"),
        profile.get("source_observation_id"),
        profile.get("snapshot_path"),
        profile.get("frame_source"),
        profile.get("last_seen_at"),
        profile.get("last_seen_camera_id"),
        profile.get("last_seen_room"),
        profile.get("role_assignment", "unknown_person"),
        profile.get("assignment_source", "unassigned"),
        profile.get("assigned_by"),
        profile.get("assigned_at"),
        json.dumps(profile["attributes"], sort_keys=True),
    )


def appearance_profile_from_row(row: sqlite3.Row) -> dict[str, Any]:
    descriptor_source = row["descriptor_source"]
    return {
        "schema": "appearance-profile",
        "appearance_profile_id": row["appearance_profile_id"],
        "active_date": row["active_date"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "expires_at": row["expires_at"],
        "descriptor_source": descriptor_source,
        "created_from": descriptor_source,
        "descriptor_status": row["descriptor_status"],
        "source_event_id": row["source_event_id"],
        "source_observation_id": row["source_observation_id"],
        "snapshot_path": row["snapshot_path"],
        "frame_source": row["frame_source"],
        "last_seen_at": row["last_seen_at"],
        "last_seen_camera_id": row["last_seen_camera_id"],
        "last_seen_room": row["last_seen_room"],
        "role_assignment": row["role_assignment"],
        "assignment_source": row["assignment_source"],
        "assigned_by": row["assigned_by"],
        "assigned_at": row["assigned_at"],
        "attributes": json.loads(row["attributes_json"]),
    }


def appearance_profile_observation_values(observation: dict[str, Any]) -> tuple[Any, ...]:
    return (
        observation["profile_observation_id"],
        observation["appearance_profile_id"],
        observation["observed_at"],
        observation.get("camera_id"),
        observation.get("room"),
        observation.get("track_id"),
        observation.get("source_event_id"),
        observation.get("source_observation_id"),
        observation.get("snapshot_path"),
        observation.get("frame_source"),
        observation.get("descriptor_source", observation.get("created_from")),
        observation["descriptor_status"],
        observation.get("confidence"),
        json.dumps(observation["attributes"], sort_keys=True),
    )


def appearance_profile_observation_from_row(row: sqlite3.Row) -> dict[str, Any]:
    descriptor_source = row["descriptor_source"]
    return {
        "schema": "appearance-profile-observation",
        "profile_observation_id": row["profile_observation_id"],
        "appearance_profile_id": row["appearance_profile_id"],
        "observed_at": row["observed_at"],
        "camera_id": row["camera_id"],
        "room": row["room"],
        "track_id": row["track_id"],
        "source_event_id": row["source_event_id"],
        "source_observation_id": row["source_observation_id"],
        "snapshot_path": row["snapshot_path"],
        "frame_source": row["frame_source"],
        "descriptor_source": descriptor_source,
        "created_from": descriptor_source,
        "descriptor_status": row["descriptor_status"],
        "confidence": row["confidence"],
        "attributes": json.loads(row["attributes_json"]),
    }


def appearance_profile_sample_values(sample: dict[str, Any]) -> tuple[Any, ...]:
    return (
        sample["sample_id"],
        sample["appearance_profile_id"],
        sample["active_date"],
        sample["captured_at"],
        sample.get("camera_id"),
        sample.get("room"),
        sample.get("track_id"),
        sample.get("source_event_id"),
        sample.get("source_observation_id"),
        sample["snapshot_path"],
        sample["frame_source"],
        sample["descriptor_status"],
        sample["quality_score"],
        json.dumps(sample["quality_reasons"], sort_keys=True),
        sample.get("detection_confidence"),
        json.dumps(sample["bbox_xyxy"], sort_keys=True),
        json.dumps(sample["attributes"], sort_keys=True),
        sample.get("retained_rank", 0),
        sample["created_at"],
    )


def appearance_profile_sample_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "schema": "appearance-profile-sample",
        "sample_id": row["sample_id"],
        "appearance_profile_id": row["appearance_profile_id"],
        "active_date": row["active_date"],
        "captured_at": row["captured_at"],
        "camera_id": row["camera_id"],
        "room": row["room"],
        "track_id": row["track_id"],
        "source_event_id": row["source_event_id"],
        "source_observation_id": row["source_observation_id"],
        "snapshot_path": row["snapshot_path"],
        "frame_source": row["frame_source"],
        "descriptor_status": row["descriptor_status"],
        "quality_score": row["quality_score"],
        "quality_reasons": json.loads(row["quality_reasons_json"]),
        "detection_confidence": row["detection_confidence"],
        "bbox_xyxy": json.loads(row["bbox_json"]),
        "attributes": json.loads(row["attributes_json"]),
        "retained_rank": row["retained_rank"],
        "created_at": row["created_at"],
    }


def review_journal_body(
    event: dict[str, Any],
    reviewer: str,
    decision: str,
    note: str | None,
    *,
    review_purpose: str,
    previous_status: str,
    amendment_of_review_id: str | None,
) -> str:
    decision_text = decision.replace("_", " ")
    lines = [
        f"Event {event['event_id']} was {decision_text} by {reviewer}.",
        f"Event type: {event['event_type']}.",
        f"Review purpose: {review_purpose}.",
        f"Lifecycle transition: {previous_status} -> {decision}.",
        f"Status: {decision}.",
    ]
    if amendment_of_review_id:
        lines.append(f"Amends review: {amendment_of_review_id}.")
    if note:
        lines.append(f"Reviewer note: {note}")
    lines.append("Blocked actions remained blocked: " + ", ".join(event["blocked_actions"]) + ".")
    return "\n".join(lines)


def is_automation_reviewer(reviewer: str) -> bool:
    normalized = reviewer.strip().lower().replace("_", " ").replace("-", " ")
    automation_names = {
        "agent",
        "ai",
        "assistant",
        "automation",
        "bot",
        "carebot",
        "chatgpt",
        "codex",
        "dashboard",
        "llm",
        "model",
        "openclaw",
        "script",
    }
    return normalized in automation_names


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
