import tempfile
import unittest
from pathlib import Path

from caresight.events.floor_stay import FloorStayDetector
from caresight.runtime.agent_assist import (
    build_agent_draft,
    build_harness_plan,
    build_hermes_config_plan,
    stage_action_request,
    validate_draft_text,
)
from caresight.runtime.config import CareSightConfig
from caresight.storage.sqlite_store import SQLiteStore
from caresight.vision.detections import Detection


class AgentAssistTest(unittest.TestCase):
    def test_fake_provider_persists_validated_draft_to_sqlite(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id)
            stored = seed.store.list_agent_drafts(seed.event_id)

            self.assertEqual(draft["provider"], "fake")
            self.assertEqual(draft["validation_status"], "validated")
            self.assertEqual(draft["blocked_claims"], [])
            self.assertIn("draft_only", draft["safety_boundaries"])
            self.assertEqual(stored[0]["draft_id"], draft["draft_id"])
            self.assertEqual(stored[0]["source_of_truth"], "sqlite")
            self.assertEqual(stored[0]["provenance"]["source"], "sqlite_audit_chain")

    def test_blocked_draft_is_persisted_with_reasons_and_safe_rewrite(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(
                seed.store,
                seed.event_id,
                override_text="CareSight called 911 because a fall detected diagnosis was made.",
            )
            stored = seed.store.list_agent_drafts(seed.event_id)[0]

            self.assertEqual(draft["validation_status"], "blocked")
            self.assertIn("autonomous_emergency_dispatch", draft["blocked_claims"])
            self.assertIn("vision_overcertainty", draft["blocked_claims"])
            self.assertIn("possible event", draft["safe_rewrite"])
            self.assertEqual(stored["validation_status"], "blocked")
            self.assertEqual(stored["blocked_claims"], draft["blocked_claims"])

    def test_forbidden_claim_vocabulary_blocks_sprint_02_claims(self) -> None:
        blocked = validate_draft_text(
            "This HIPAA compliant medical device confirmed medication and dispatched emergency services."
        )

        self.assertIn("hipaa_compliance", blocked)
        self.assertIn("medical_device", blocked)
        self.assertIn("medication_administration", blocked)
        self.assertIn("autonomous_emergency_dispatch", blocked)

    def test_action_request_staging_persists_without_execution(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id)
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="create_apple_note",
                destination="apple_notes",
            )
            stored = seed.store.list_agent_action_requests(seed.event_id)

            self.assertEqual(request["stage"], "staged")
            self.assertEqual(request["execution_state"], "not_executed")
            self.assertTrue(request["requires_human_approval"])
            self.assertIn("no_external_execution", request["safety_boundaries"])
            self.assertEqual(stored[0]["request_id"], request["request_id"])
            self.assertEqual(stored[0]["execution_state"], "not_executed")

    def test_blocked_draft_cannot_stage_action_request(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(
                seed.store,
                seed.event_id,
                override_text="CareSight called 911 for a diagnosed fall detected event.",
            )

            with self.assertRaises(ValueError):
                stage_action_request(
                    seed.store,
                    event_id=seed.event_id,
                    source_draft_id=draft["draft_id"],
                    requested_action="send_caregiver_message",
                )

    def test_harness_plan_routes_imessage_to_hermes_without_execution(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id)
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="send_imessage_draft",
                destination="imessage",
            )
            plan = build_harness_plan(request, draft=draft)

            self.assertEqual(plan["selected_harness"], "hermes")
            self.assertEqual(plan["execution_state"], "plan_only")
            self.assertEqual(plan["external_execution"], "not_allowed_by_this_command")
            self.assertEqual(plan["model_lane"]["provider"], "gemma_mlx")
            self.assertIn("no_raw_video_to_agent", plan["safety_boundaries"])

    def test_harness_plan_routes_tts_to_holler_lane(self) -> None:
        with seeded_store() as seed:
            draft = build_agent_draft(seed.store, seed.event_id)
            request = stage_action_request(
                seed.store,
                event_id=seed.event_id,
                source_draft_id=draft["draft_id"],
                requested_action="play_tts_utterance",
                destination="local_tts",
            )
            plan = build_harness_plan(request, draft=draft, preferred_harness="openclaw")

            self.assertEqual(plan["selected_harness"], "openclaw")
            self.assertEqual(plan["model_lane"]["provider"], "holler_mlx")
            self.assertEqual(plan["model_lane"]["default_model"], "holler-0.6b-6bit")

    def test_hermes_config_plan_uses_local_endpoint_not_openrouter(self) -> None:
        plan = build_hermes_config_plan()

        self.assertEqual(plan["schema"], "hermes-config-plan")
        self.assertEqual(plan["vendor"]["pinned_tag"], "v2026.5.16")
        self.assertFalse(plan["vendor"]["global_install_performed"])
        self.assertEqual(plan["local_model_serving"]["default"], "local_openai_compatible_endpoint")
        self.assertEqual(plan["local_model_serving"]["base_url"], "http://127.0.0.1:8080/v1")
        self.assertFalse(plan["local_model_serving"]["openrouter_required"])
        self.assertIn("no_cloud_router_by_default", plan["safety_boundaries"])


class Seed:
    def __init__(self, tmpdir: tempfile.TemporaryDirectory[str]):
        self.tmpdir = tmpdir
        self.db_path = Path(tmpdir.name) / "caresight.sqlite3"
        self.config = CareSightConfig.default()
        self.store = SQLiteStore(self.db_path)
        self.store.initialize()
        self.store.upsert_config(self.config)
        detector = FloorStayDetector(self.config)
        detection = Detection(
            class_name="person",
            confidence=0.91,
            bbox_xyxy=(360, 520, 640, 710),
            frame_width=1280,
            frame_height=720,
        )
        detector.update([detection], now=100.0)
        event = detector.update([detection], now=109.0)
        assert event is not None
        self.event_id = event["event_id"]
        self.store.insert_event(event)

    def __enter__(self) -> "Seed":
        return self

    def __exit__(self, *_args: object) -> None:
        self.tmpdir.cleanup()


def seeded_store() -> Seed:
    return Seed(tempfile.TemporaryDirectory())


if __name__ == "__main__":
    unittest.main()
