import gc
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from caresight.events.floor_stay import FloorStayDetector
from caresight.runtime.config import CareSightConfig
from caresight.storage.sqlite_store import SQLiteStore
from caresight.vision.detections import Detection


class SQLiteStoreTest(unittest.TestCase):
    def test_stores_config_snapshot_and_event_readback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            config = CareSightConfig.default()
            store = SQLiteStore(db_path)
            store.initialize()
            store.upsert_config(config)

            detector = FloorStayDetector(config)
            detection = Detection(
                class_name="person",
                confidence=0.91,
                bbox_xyxy=(200, 430, 1080, 715),
                frame_width=1280,
                frame_height=720,
            )
            detector.update([detection], now=100.0)
            event = detector.update([detection], now=109.0)
            assert event is not None

            store.insert_event(event)
            stored = store.get_event(event["event_id"])

            self.assertEqual(stored["event_id"], event["event_id"])
            self.assertEqual(stored["event_type"], "possible_floor_stay")
            self.assertEqual(stored["zone_id"], "floor_zone")
            self.assertEqual(stored["evidence"]["raw_video_stays_local"], True)
            self.assertEqual(store.list_zones()[0]["zone_id"], "floor_zone")
            observations = store.list_event_observations(event["event_id"])
            self.assertEqual(len(observations), 1)
            self.assertEqual(observations[0]["class_name"], "person")
            self.assertEqual(observations[0]["zone_id"], "floor_zone")
            self.assertEqual(observations[0]["track_id"], event["evidence"]["track_id"])
            self.assertEqual(observations[0]["bbox_json"], event["evidence"]["bbox_xyxy"])

    def test_initialize_adds_track_id_to_existing_observations_without_deleting_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "legacy.sqlite3"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE event_observations (
                  observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  event_id TEXT NOT NULL,
                  observed_at TEXT NOT NULL,
                  class_name TEXT NOT NULL,
                  confidence REAL NOT NULL,
                  bbox_json TEXT NOT NULL,
                  zone_id TEXT
                );
                INSERT INTO event_observations (
                  event_id,
                  observed_at,
                  class_name,
                  confidence,
                  bbox_json,
                  zone_id
                )
                VALUES (
                  'evt_legacy',
                  '2026-05-19T03:20:36Z',
                  'person',
                  0.91,
                  '[1, 2, 3, 4]',
                  'floor_zone'
                );
                """
            )
            conn.close()

            store = SQLiteStore(db_path)
            store.initialize()

            conn = sqlite3.connect(db_path)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(event_observations)")}
            row = conn.execute(
                "SELECT event_id, class_name, track_id FROM event_observations WHERE event_id = 'evt_legacy'"
            ).fetchone()
            conn.close()

            self.assertIn("track_id", columns)
            self.assertEqual(row, ("evt_legacy", "person", None))

    def test_stores_observation_check_without_event_review_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            config = CareSightConfig.default()
            store = SQLiteStore(db_path)
            store.initialize()
            store.upsert_config(config)
            check = {
                "check_id": "check_normal_desk",
                "check_type": "normal_presence_no_event",
                "started_at": "2026-05-21T18:00:00Z",
                "completed_at": "2026-05-21T18:01:00Z",
                "camera_id": "living_room",
                "zone_id": "floor_zone",
                "status": "no_event_persisted",
                "frame_count": 1800,
                "elapsed_seconds": 60.0,
                "required_dwell_seconds": 8.0,
                "event_id": None,
                "result": {
                    "status": "no_possible_floor_stay_event",
                    "camera_id": "living_room",
                    "zone_id": "floor_zone",
                },
            }

            store.insert_observation_check(check)
            stored = store.get_observation_check("check_normal_desk")

            self.assertEqual(stored["schema"], "observation-check")
            self.assertEqual(stored["status"], "no_event_persisted")
            self.assertIsNone(stored["event_id"])
            self.assertEqual(stored["frame_count"], 1800)
            self.assertEqual(stored["result"]["status"], "no_possible_floor_stay_event")
            self.assertEqual(store.list_events(), [])
            self.assertEqual(store.list_observation_checks()[0]["check_id"], "check_normal_desk")

    def test_stores_agent_execution_attempt_without_changing_action_request_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            config = CareSightConfig.default()
            store = SQLiteStore(db_path)
            store.initialize()
            store.upsert_config(config)
            event = _floor_stay_event(config)
            store.insert_event(event)
            draft = {
                "draft_id": "draft_exec_attempt",
                "event_id": event["event_id"],
                "created_at": "2026-05-21T19:00:00Z",
                "provider": "fake",
                "purpose": "alert_draft",
                "validation_status": "validated",
                "draft_text": "CareSight recorded a possible event.",
                "safe_rewrite": None,
                "blocked_claims": [],
                "safety_boundaries": ["draft_only"],
                "provenance": {"source": "test"},
            }
            request = {
                "request_id": "action_req_exec_attempt",
                "event_id": event["event_id"],
                "created_at": "2026-05-21T19:00:01Z",
                "requested_action": "send_imessage_draft",
                "stage": "staged",
                "execution_state": "not_executed",
                "requires_human_approval": True,
                "source_draft_id": draft["draft_id"],
                "destination": "imessage",
                "escalation_level": "urgent_handoff",
                "recipient_role": "emergency_contact",
                "allowed_contact_ids": ["contact_emergency_primary"],
                "response_options": ["acknowledge_text_update"],
                "safety_boundaries": ["stage_only", "no_external_execution"],
                "provenance": {"source": "test"},
            }
            attempt = {
                "attempt_id": "attempt_exec_attempt",
                "request_id": request["request_id"],
                "event_id": event["event_id"],
                "created_at": "2026-05-21T19:00:02Z",
                "harness": "hermes",
                "attempt_kind": "dry_run",
                "execution_state": "dry_run",
                "result": "payload_logged_no_send",
                "external_action_performed": False,
                "payload": {"schema": "hermes-handoff-payload"},
                "safety_boundaries": ["no_external_execution"],
                "provenance": {"source": "test"},
            }

            store.insert_agent_draft(draft)
            store.insert_agent_action_request(request)
            store.insert_agent_execution_attempt(attempt)
            stored = store.list_agent_execution_attempts(request["request_id"])[0]

            self.assertEqual(stored["schema"], "agent-execution-attempt")
            self.assertEqual(stored["attempt_id"], "attempt_exec_attempt")
            self.assertEqual(stored["execution_state"], "dry_run")
            self.assertFalse(stored["external_action_performed"])
            self.assertEqual(stored["payload"]["schema"], "hermes-handoff-payload")
            self.assertEqual(
                store.get_agent_action_request(request["request_id"])["execution_state"],
                "not_executed",
            )

    def test_persists_dynamic_appearance_profile_with_observation_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            store = SQLiteStore(db_path)
            store.initialize()

            profile = {
                "appearance_profile_id": "appearance_2026_05_22_001",
                "active_date": "2026-05-22",
                "created_at": "2026-05-22T14:00:00Z",
                "updated_at": "2026-05-22T14:00:00Z",
                "expires_at": "2026-05-23T04:00:00Z",
                "descriptor_source": "runtime_observation",
                "descriptor_status": "available",
                "source_event_id": "evt_runtime_profile",
                "source_observation_id": 42,
                "snapshot_path": "data/snapshots/evt_runtime_profile.jpg",
                "frame_source": "living_room_camera",
                "last_seen_at": "2026-05-22T14:00:00Z",
                "last_seen_camera_id": "living_room",
                "last_seen_room": "Living Room",
                "attributes": {
                    "upper_body_color": {"value": "dark gray", "confidence": 0.78},
                    "lower_body_color": {"value": "gray", "confidence": 0.7},
                },
            }
            observation = {
                "profile_observation_id": "appearance_obs_001",
                "appearance_profile_id": profile["appearance_profile_id"],
                "observed_at": "2026-05-22T14:00:01Z",
                "camera_id": "living_room",
                "room": "Living Room",
                "track_id": "track_person_001",
                "source_event_id": "evt_runtime_profile",
                "source_observation_id": 42,
                "snapshot_path": "data/snapshots/evt_runtime_profile.jpg",
                "frame_source": "living_room_camera",
                "descriptor_source": "runtime_observation",
                "descriptor_status": "available",
                "attributes": {"carried_object": {"value": "mug", "confidence": 0.66}},
                "confidence": 0.72,
            }

            store.insert_appearance_profile(profile)
            store.insert_appearance_profile_observation(observation)
            stored = store.get_appearance_profile(profile["appearance_profile_id"])
            observations = store.list_appearance_profile_observations(profile["appearance_profile_id"])

            self.assertEqual(stored["schema"], "appearance-profile")
            self.assertEqual(stored["descriptor_source"], "runtime_observation")
            self.assertEqual(stored["descriptor_status"], "available")
            self.assertEqual(stored["source_event_id"], "evt_runtime_profile")
            self.assertEqual(stored["source_observation_id"], 42)
            self.assertEqual(stored["snapshot_path"], "data/snapshots/evt_runtime_profile.jpg")
            self.assertEqual(stored["frame_source"], "living_room_camera")
            self.assertEqual(stored["attributes"]["upper_body_color"]["value"], "dark gray")
            self.assertEqual(observations[0]["schema"], "appearance-profile-observation")
            self.assertEqual(observations[0]["source_event_id"], "evt_runtime_profile")
            self.assertEqual(observations[0]["source_observation_id"], 42)
            self.assertEqual(observations[0]["descriptor_source"], "runtime_observation")
            self.assertEqual(observations[0]["descriptor_status"], "available")
            self.assertEqual(observations[0]["attributes"]["carried_object"]["value"], "mug")

    def test_persists_and_prunes_capped_appearance_profile_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            store = SQLiteStore(db_path)
            store.initialize()
            profile = _appearance_profile(
                "appearance_samples",
                active_date="2026-05-22",
                expires_at="2026-05-23T04:00:00Z",
                descriptor_source="runtime_observation",
            )
            store.upsert_appearance_profile(profile)
            snapshot_paths = []
            for index, quality_score in enumerate([0.91, 0.72, 0.84], start=1):
                snapshot = Path(tmpdir) / f"sample_{index}.jpg"
                snapshot.write_bytes(b"fake image")
                snapshot_paths.append(snapshot)
                store.insert_appearance_profile_sample(
                    {
                        "sample_id": f"sample_{index}",
                        "appearance_profile_id": "appearance_samples",
                        "active_date": "2026-05-22",
                        "captured_at": f"2026-05-22T14:0{index}:00Z",
                        "camera_id": "living_room",
                        "room": "Living Room",
                        "track_id": "track_1",
                        "source_event_id": None,
                        "source_observation_id": None,
                        "snapshot_path": str(snapshot),
                        "frame_source": "periodic_live_sample",
                        "descriptor_status": "available",
                        "quality_score": quality_score,
                        "quality_reasons": ["accepted"],
                        "detection_confidence": 0.9,
                        "bbox_xyxy": [10, 10, 50, 70],
                        "attributes": {
                            "upper_body_color": {"value": "blue", "confidence": 0.78},
                            "lower_body_color": {"value": "white", "confidence": 0.78},
                        },
                        "created_at": f"2026-05-22T14:0{index}:00Z",
                    }
                )

            removed = store.prune_appearance_profile_samples("appearance_samples", max_samples=2)
            samples = store.list_appearance_profile_samples("appearance_samples")

            self.assertEqual([sample["sample_id"] for sample in samples], ["sample_1", "sample_3"])
            self.assertEqual([sample["retained_rank"] for sample in samples], [1, 2])
            self.assertEqual(removed[0]["sample_id"], "sample_2")
            self.assertFalse(snapshot_paths[1].exists())
            self.assertEqual(store.list_appearance_samples_for_date("2026-05-22")[0]["sample_id"], "sample_1")

    def test_event_lookup_can_find_same_day_track_profile_from_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            config = CareSightConfig.default()
            store = SQLiteStore(db_path)
            store.initialize()
            store.upsert_config(config)
            event = _floor_stay_event(config)
            event["occurred_at"] = "2026-05-22T14:03:00Z"
            event["evidence"]["track_id"] = "track_1"
            store.insert_event(event)
            profile = _appearance_profile(
                "appearance_2026_05_22_track_1",
                active_date="2026-05-22",
                expires_at="2026-05-23T04:00:00Z",
                descriptor_source="runtime_observation",
            )
            store.upsert_appearance_profile(profile)
            store.insert_appearance_profile_sample(
                {
                    "sample_id": "sample_track_link",
                    "appearance_profile_id": profile["appearance_profile_id"],
                    "active_date": "2026-05-22",
                    "captured_at": "2026-05-22T14:00:00Z",
                    "camera_id": "living_room",
                    "room": "Living Room",
                    "track_id": "track_1",
                    "snapshot_path": str(Path(tmpdir) / "sample.jpg"),
                    "frame_source": "periodic_live_sample",
                    "descriptor_status": "available",
                    "quality_score": 0.82,
                    "quality_reasons": ["accepted"],
                    "detection_confidence": 0.91,
                    "bbox_xyxy": [10, 10, 50, 70],
                    "attributes": {"upper_body_color": {"value": "blue", "confidence": 0.78}},
                    "created_at": "2026-05-22T14:00:00Z",
                }
            )

            profiles = store.list_appearance_profiles_for_event(event["event_id"])

            self.assertEqual([profile["appearance_profile_id"] for profile in profiles], ["appearance_2026_05_22_track_1"])

    def test_lists_only_unexpired_active_appearance_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            store = SQLiteStore(db_path)
            store.initialize()

            active = _appearance_profile(
                "appearance_active",
                active_date="2026-05-22",
                expires_at="2026-05-23T04:00:00Z",
                descriptor_source="operator_demo_seed",
            )
            expired = _appearance_profile(
                "appearance_expired",
                active_date="2026-05-22",
                expires_at="2026-05-22T13:00:00Z",
                descriptor_source="seeded_test_fixture",
            )
            different_day = _appearance_profile(
                "appearance_other_day",
                active_date="2026-05-21",
                expires_at="2026-05-23T04:00:00Z",
                descriptor_source="runtime_observation",
            )

            store.upsert_appearance_profile(active)
            store.upsert_appearance_profile(expired)
            store.upsert_appearance_profile(different_day)
            profiles = store.list_active_appearance_profiles(
                active_date="2026-05-22",
                now="2026-05-22T14:00:00Z",
            )

            self.assertEqual([profile["appearance_profile_id"] for profile in profiles], ["appearance_active"])
            self.assertEqual(profiles[0]["descriptor_source"], "operator_demo_seed")

    def test_assigns_appearance_profile_role_with_human_reviewer_and_rejects_automation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            store = SQLiteStore(db_path)
            store.initialize()
            profile = _appearance_profile(
                "appearance_role",
                active_date="2026-05-22",
                expires_at="2026-05-23T04:00:00Z",
                descriptor_source="runtime_observation",
            )
            store.upsert_appearance_profile(profile)

            assigned = store.assign_appearance_profile_role(
                "appearance_role",
                role_assignment="resident_primary",
                reviewer="Steven",
                assigned_at="2026-05-22T14:05:00Z",
            )

            self.assertEqual(assigned["role_assignment"], "resident_primary")
            self.assertEqual(assigned["assignment_source"], "human_confirmed")
            self.assertEqual(assigned["assigned_by"], "Steven")
            self.assertEqual(assigned["assigned_at"], "2026-05-22T14:05:00Z")
            self.assertEqual(
                store.get_appearance_profile("appearance_role")["role_assignment"],
                "resident_primary",
            )

            for reviewer in ("", "   ", "agent", "codex", "automation"):
                with self.subTest(reviewer=reviewer):
                    with self.assertRaises(ValueError):
                        store.assign_appearance_profile_role(
                            "appearance_role",
                            role_assignment="caregiver_known",
                            reviewer=reviewer,
                            assigned_at="2026-05-22T14:06:00Z",
                        )

    def test_store_operations_do_not_leave_unclosed_sqlite_connections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "caresight.sqlite3"
            store = SQLiteStore(db_path)

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ResourceWarning)
                store.initialize()
                store.upsert_config(CareSightConfig.default())
                self.assertEqual(store.list_zones()[0]["zone_id"], "floor_zone")
                gc.collect()

            sqlite_warnings = [
                warning
                for warning in caught
                if issubclass(warning.category, ResourceWarning)
                and "sqlite" in str(warning.message).lower()
                and "unclosed" in str(warning.message).lower()
            ]
            self.assertEqual(sqlite_warnings, [])


def _floor_stay_event(config: CareSightConfig) -> dict:
    detector = FloorStayDetector(config)
    detection = Detection(
        class_name="person",
        confidence=0.91,
        bbox_xyxy=(200, 430, 1080, 715),
        frame_width=1280,
        frame_height=720,
    )
    detector.update([detection], now=100.0)
    event = detector.update([detection], now=109.0)
    assert event is not None
    return event


def _appearance_profile(
    appearance_profile_id: str,
    *,
    active_date: str,
    expires_at: str,
    descriptor_source: str,
) -> dict:
    return {
        "appearance_profile_id": appearance_profile_id,
        "active_date": active_date,
        "created_at": f"{active_date}T12:00:00Z",
        "updated_at": f"{active_date}T12:00:00Z",
        "expires_at": expires_at,
        "descriptor_source": descriptor_source,
        "descriptor_status": "available",
        "source_event_id": None,
        "source_observation_id": None,
        "snapshot_path": None,
        "frame_source": None,
        "last_seen_at": f"{active_date}T12:00:00Z",
        "last_seen_camera_id": "living_room",
        "last_seen_room": "Living Room",
        "attributes": {"upper_body_color": {"value": "blue", "confidence": 0.71}},
    }


if __name__ == "__main__":
    unittest.main()
