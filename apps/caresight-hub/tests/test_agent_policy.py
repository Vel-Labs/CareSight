import unittest

from caresight.runtime.agents import AgentPolicyError, assert_agent_action_allowed


class AgentPolicyTest(unittest.TestCase):
    def test_allows_summary_with_event_provenance_and_purpose(self) -> None:
        assert_agent_action_allowed(
            "summarize_event",
            {
                "purpose": "caregiver_summary",
                "provenance": {
                    "event_id": "evt_possible_floor_stay_demo",
                    "source_fields": ["event.event_id", "event.evidence"],
                },
            },
        )

    def test_blocks_lifecycle_and_dangerous_actions(self) -> None:
        for action in (
            "confirm_event",
            "dismiss_event",
            "delete_event",
            "emergency_dispatch",
            "diagnose",
            "confirm_medication_taken",
            "inspect_raw_video_for_decision",
        ):
            with self.subTest(action=action):
                with self.assertRaisesRegex(AgentPolicyError, "forbidden"):
                    assert_agent_action_allowed(action, valid_payload())

    def test_requires_provenance_and_purpose(self) -> None:
        with self.assertRaisesRegex(AgentPolicyError, "requires provenance"):
            assert_agent_action_allowed("draft_caregiver_message", {"purpose": "draft"})

        with self.assertRaisesRegex(AgentPolicyError, "requires event_id"):
            assert_agent_action_allowed(
                "draft_caregiver_message",
                {"purpose": "draft", "provenance": {"source_fields": ["event.event_id"]}},
            )

        with self.assertRaisesRegex(AgentPolicyError, "requires purpose"):
            assert_agent_action_allowed(
                "draft_caregiver_message",
                {
                    "provenance": {
                        "event_id": "evt_possible_floor_stay_demo",
                        "source_fields": ["event.event_id"],
                    }
                },
            )


def valid_payload() -> dict:
    return {
        "purpose": "caregiver_summary",
        "provenance": {
            "event_id": "evt_possible_floor_stay_demo",
            "source_fields": ["event.event_id"],
        },
    }


if __name__ == "__main__":
    unittest.main()
