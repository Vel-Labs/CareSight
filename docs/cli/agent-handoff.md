# Agent Handoff Commands

Agent handoff commands are downstream of SQLite records. They can summarize, draft, stage, plan, and record no-send attempts, but they cannot confirm, dismiss, dispatch, diagnose, inspect raw video as decision-maker, or execute live delivery without a separate human-approved path.

## Agent-Safe Read

| Command | Purpose | Validation |
| --- | --- | --- |
| `python apps/caresight-hub/scripts/care_console.py agent-draft <event_id> --purpose caregiver_summary` | Create and persist a fake-provider or local Gemma draft from SQLite audit context. | `test_agent_assist.py` and `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py stage-action-request <event_id> --draft-id <draft_id> --action create_apple_note --destination apple_notes` | Stage a local action request without executing it. | `test_agent_assist.py` and `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py list-action-requests <event_id>` | List staged local action requests. | `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py agent-harness-plan <request_id> --prefer auto` | Render a non-executing OpenClaw/Hermes route plan. | `test_agent_assist.py` and `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py hermes-handoff-payload <request_id>` | Render a non-executing Hermes payload. | `test_agent_assist.py` and `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py record-execution-attempt <request_id> --harness hermes --kind dry_run` | Persist a local dry-run execution-attempt row. | `test_agent_assist.py`, `test_sqlite_store.py`, `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py hermes-dry-run <request_id>` | Invoke Hermes no-send message-directory preflight and persist the attempt. | `test_agent_assist.py` and `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py list-execution-attempts <request_id>` | List execution-attempt rows for a staged request. | `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py hermes-config-plan` | Render the workspace-local Hermes vendor/config plan. | `test_agent_assist.py` and `test_care_console.py`. |

## Boundaries

- `agent-draft` sends compact SQLite-derived context only; it does not send raw video or image bytes.
- Staged action requests remain `stage: staged` and `execution_state: not_executed`.
- Hermes dry runs keep `external_action_performed: false`.
- Live iMessage, FaceTime, and TTS playback live in [`obs-tts-facetime.md`](obs-tts-facetime.md) and require human approval.
