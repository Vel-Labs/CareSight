# CLI Commands

This index tracks commands that are safe to run locally and explains their inputs, outputs, validation, and agent boundary.

## Agent Safety Classes

- `agent-safe-read`: agents may run without human approval.
- `human-review-required`: agents may prepare or summarize, but a human must explicitly authorize state changes.
- `manual-operator`: intended for a human because it uses live camera or local environment resources.

## YOLO26 Image Smoke

Command:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/yolo26_image_smoke.py
```

Purpose: run the CareSight-owned YOLO26 MLX inference harness against the bundled image smoke fixture.

Inputs: local YOLO26 MLX environment, `apps/caresight-hub/config/v0.local.json`, model path, room metadata, camera metadata, and image fixture.

Outputs: local result image plus terminal JSON with raw `detections`, normalized `observations`, and runtime metadata.

Validation: covered by the v0 smoke checkpoint audit and `test_inference_harness.py`; rerun before claiming model readiness on a new machine.

Agent safety: `manual-operator`.

## YOLO26 Webcam Smoke

Command:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/yolo26_webcam_smoke.py
```

Purpose: verify live webcam capture and YOLO26 MLX person labels through the CareSight-owned adapter boundary.

Inputs: local camera access, `apps/caresight-hub/config/v0.local.json`, camera metadata, room metadata, and YOLO26 MLX model.

Outputs: local preview window and terminal diagnostics.

Validation: deterministic adapter and normalization behavior is covered by `test_inference_harness.py`; live camera behavior remains manual/operator.

Agent safety: `manual-operator`.

## v0 Floor-Stay Live Loop

Command:

```bash
python apps/caresight-hub/scripts/v0_floor_stay_live.py
```

Purpose: create a local `possible_floor_stay` event after a person remains in the configured floor/low zone.

Inputs: `apps/caresight-hub/config/v0.local.json`, local camera, YOLO26 MLX model, SQLite database path.

Outputs: `event_persisted` terminal line, SQLite event row, event observation row with `track_id`, and local snapshot path.

Validation: `npm run py:check` covers deterministic event, SQLite, tracking, and snapshot behavior. Live camera behavior still needs manual verification.

Agent safety: `manual-operator`.

Configured source selection:

```bash
python3 apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room_usb --no-window --max-seconds 120 --stop-after-event
```

Purpose: select one configured local camera source from `config.cameras` while preserving `camera_id`, `source_type`, and room label in runtime config and SQLite-backed event provenance.

Supported source types: `webcam`, `usb`, `continuity_camera`, and local `rtsp`. Ring, Nest, Home Assistant, ONVIF discovery, LAN scanning, cloud-camera APIs, and credential handling remain out of scope.

Validation: `test_v0_config.py` verifies deterministic source selection and cloud/provider rejection without opening a camera.

Bounded audit run:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --max-seconds 60 --stop-after-event
```

Purpose: let an operator collect one `event_persisted` line without leaving the live loop unbounded.

Omit `--no-window` when the operator needs the preview overlay to position the floor/low zone.

Readiness check:

```bash
python3 apps/caresight-hub/scripts/v0_floor_stay_live.py --help
```

Purpose: verify CLI parsing and bounded proof flags without requiring OpenCV, camera access, or YOLO runtime imports.

## v0 Review Events: List

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py list
```

Purpose: show the local event inbox. Defaults to `awaiting_human_confirmation`.

Inputs: optional `--db <path>`, optional `--all`.

Outputs: human-readable event rows.

Validation: `test_v0_review_events.py` verifies default inbox filtering.

Agent safety: `agent-safe-read`.

## v0 Review Events: Show

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py show <event_id>
```

Purpose: render a deterministic human-readable event summary for a local event.

Inputs: `event_id`, optional `--db <path>`.

Outputs: event ID, status, zone, dwell, confidence, snapshot path, and blocked actions.

Validation: `test_v0_review_events.py` verifies required summary fields.

Agent safety: `agent-safe-read`.

## v0 Review Events: Confirm

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py confirm <event_id> --reviewer <name> --note "<note>"
```

Purpose: record an authorized human confirmation.

Inputs: `event_id`, required `--reviewer`, optional `--note`, optional `--db <path>`.

Outputs: updated event status, `event_reviews` row, `journal_entries` row, and report-only `agent_handoffs` row.

Validation: `test_v0_review_events.py` verifies the shared review service path, reviewer requirement, status update, review row, journal row, and handoff payload.

Agent safety: `human-review-required`.

## v0 Review Events: Dismiss

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py dismiss <event_id> --reviewer <name> --note "<note>"
```

Purpose: record an authorized human dismissal.

Inputs: `event_id`, required `--reviewer`, optional `--note`, optional `--db <path>`.

Outputs: updated event status, `event_reviews` row, `journal_entries` row, and report-only `agent_handoffs` row.

Validation: `test_v0_review_events.py` verifies the shared review service path, dismissed status, review row, journal row, and handoff payload.

Agent safety: `human-review-required`.

## v0 Review Events: Journal

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py journal <event_id>
```

Purpose: show human-readable care journal entries for an event.

Inputs: `event_id`, optional `--db <path>`.

Outputs: local journal entries in readable text.

Validation: `test_v0_review_events.py` verifies journal rendering.

Agent safety: `agent-safe-read`.

## v0 Review Service Boundary

The CLI delegates event listing, summaries, human confirm/dismiss transitions, journal reads, and SQLite audit-chain reads to `caresight.runtime.review.ReviewService`.

State changes remain `human-review-required`: an authorized human reviewer is mandatory, automation-like reviewer names are rejected, and there are no CLI commands for deletion, emergency dispatch, diagnosis, or agent-owned acknowledgement. Review mutations are persisted through SQLite review, journal, and report-only handoff rows.

## v0 Review Events: Audit

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py audit <event_id>
```

Purpose: show a read-only SQLite blackbox chain for one event after live observation and human review.

Inputs: `event_id`, optional `--db <path>`.

Outputs: event ID, event type, status, occurred timestamp, camera, zone, snapshot path, observation row count, review row count, journal row count, report-only handoff row count, latest reviewer, latest review timestamp, and latest handoff status.

Validation: `test_v0_review_events.py` verifies audit rendering from event, observation, review, journal, and handoff rows.

Agent safety: `agent-safe-read`.

## Routine Event Policy Checks

Routine events are currently deterministic runtime policies rather than standalone CLI commands. They require:

- a person observed in the configured routine zone
- narrow configured object-label evidence
- a configured routine time window
- human review before confirmation

Validation: `test_routine_events.py` verifies medication and hydration routine events remain `awaiting_human_confirmation` and do not claim medication administration or medical hydration state.

## Care Console Dashboard

Command:

```bash
python apps/caresight-hub/scripts/care_console.py dashboard
```

Purpose: render a local JSON dashboard read model from SQLite through `ReviewService`.

Inputs: optional `--db <path>`.

Outputs: source-of-truth marker, focused-event mode when `--event-id` is used, selected event summary, separate awaiting-review backlog, live-feed boundary, current state, event timeline, concern feed, review-control mapping, journal preview, and caregiver alert draft.

Validation: `test_care_console.py` verifies the dashboard reads SQLite state, keeps review actions routed through `ReviewService`, and marks delete/dispatch as forbidden.

Agent safety: `agent-safe-read`.

## Care Console Review Packet

Command:

```bash
python apps/caresight-hub/scripts/care_console.py review-packet <event_id> --format json
```

Purpose: render a read-only human review packet from the SQLite audit chain.

Inputs: `event_id`, optional `--db <path>`, optional `--format json|markdown`, and optional `--output <path>`.

Outputs: event status, bounded headline, evidence summary, track IDs, snapshot path, review state, available human actions, blocked actions, and provenance.

Validation: `test_care_console.py` verifies JSON and Markdown review-packet output from SQLite without mutating event lifecycle state.

Agent safety: `agent-safe-read`.

## Care Console Blackbox Receipt

Command:

```bash
python apps/caresight-hub/scripts/care_console.py blackbox-receipt <event_id> --format json
```

Purpose: render a read-only blackbox receipt for a selected event's observation, human review, journal, handoff, dashboard, and alert provenance.

Inputs: `event_id`, optional `--db <path>`, optional `--format json|markdown`, and optional `--output <path>`.

Outputs: completion status, blockers for incomplete chains, counts for observations/reviews/journal/handoffs, track IDs, human review summary, derived-output checks, blocked actions, and safety boundaries.

Validation: `test_care_console.py` verifies complete receipt output after human review and the demo-surface tests verify incomplete receipts report blockers.

Agent safety: `agent-safe-read`.

## Care Console Alert Draft

Command:

```bash
python apps/caresight-hub/scripts/care_console.py alert-draft <event_id>
```

Purpose: draft caregiver alert text with provenance from the SQLite audit chain.

Inputs: `event_id`, optional `--db <path>`.

Outputs: draft text, text-to-FaceTime channel sequence, source fields, and forbidden-action boundaries.

Validation: `test_care_console.py` verifies alert drafts include event provenance and remain report-only.

Agent safety: `agent-safe-read`.

## Care Console Agent Draft

Command:

```bash
python apps/caresight-hub/scripts/care_console.py agent-draft <event_id> --purpose caregiver_summary
```

Purpose: create and persist a fake-provider agent draft from the SQLite audit chain.

Inputs: `event_id`, optional `--db <path>`, and optional `--purpose caregiver_summary|alert_draft|apple_notes_entry|handoff_packet|audit_summary`.

Outputs: `agent-draft` JSON with provider `fake`, source-of-truth marker, validation status, draft text, safety boundaries, provenance, and any blocked claim reasons.

Validation: `test_agent_assist.py` and `test_care_console.py` verify validated drafts and blocked drafts are persisted in SQLite without real Gemma, OpenClaw, TTS, or external service calls.

Agent safety: `agent-safe-read`.

## Care Console Stage Action Request

Command:

```bash
python apps/caresight-hub/scripts/care_console.py stage-action-request <event_id> --draft-id <draft_id> --action create_apple_note --destination apple_notes
```

Purpose: stage a local action request from a validated agent draft without executing it.

Inputs: `event_id`, required `--draft-id`, required `--action send_caregiver_message|create_apple_note|prepare_handoff_packet|play_tts_utterance`, optional `--destination caregiver_console|apple_notes|local_tts|handoff_packet`, and optional `--db <path>`.

Outputs: `agent-action-request` JSON with `stage: staged`, `execution_state: not_executed`, `requires_human_approval: true`, source draft, destination, safety boundaries, and provenance.

Validation: `test_agent_assist.py` verifies staged requests stay local and blocked drafts cannot stage action requests. `test_care_console.py` verifies CLI staging persists only local SQLite rows.

Agent safety: `agent-safe-read`. Agents may stage and list action requests, but Sprint 02 provides no command that executes the requested action.

## Care Console List Action Requests

Command:

```bash
python apps/caresight-hub/scripts/care_console.py list-action-requests <event_id>
```

Purpose: list staged local action requests for one event.

Inputs: `event_id` and optional `--db <path>`.

Outputs: JSON array of staged `agent-action-request` records.

Validation: `test_care_console.py` verifies list output after staging.

Agent safety: `agent-safe-read`.

## Live Proof Audit Readiness

Command:

```bash
python3 apps/caresight-hub/scripts/live_proof_audit.py readiness --camera-authorization not_checked
```

Purpose: report whether the local config and YOLO26 MLX model path are ready for live proof collection, and surface camera authorization as an explicit readiness gate.

Inputs: optional `--config <path>`, optional `--model <path>`, optional `--db <path>`, and `--camera-authorization granted|blocked|not_checked`.

Outputs: JSON readiness report with Python/environment, model, config, SQLite path, camera authorization, blockers, and safety boundaries.

Validation: `test_live_proof_audit.py` verifies that `camera_authorization=blocked` yields `camera_authorization_blocked` without requiring camera access.

Agent safety: `agent-safe-read`. Agents may report readiness and blockers, but camera permission remains an operator action.

## Live Proof Audit Bundle

Command:

```bash
python3 apps/caresight-hub/scripts/live_proof_audit.py bundle <event_id>
```

Purpose: emit a read-only local audit bundle after an operator supplies a fresh `event_id` from a real `event_persisted` line.

Inputs: fresh `event_id`, optional `--db <path>`, optional `--max-event-age-minutes <minutes>`, and optional `--output <path>` for a local JSON report artifact.

Outputs: JSON bundle with SQLite-backed event, observation `track_id`, review, journal, report-only handoff, derived dashboard provenance, derived caregiver alert provenance, completion checks, and blockers. Missing review, journal, handoff, track ID, or stale event age yields `status: not_complete`.

Validation: `test_live_proof_audit.py` seeds SQLite rows and verifies complete provenance, missing downstream rows, stale event IDs, and CLI help.

Agent safety: `agent-safe-read`. The command must not create events, confirm, dismiss, dispatch, diagnose, delete, or become reviewer of record. Dashboard and alert data remain derived output, not canonical truth.

## Agent Policy Checks

Agent policy is enforced by runtime helpers rather than a standalone CLI command.

Allowed actions are summary, caregiver-message draft, journal-note draft, and handoff audit. Forbidden actions are event confirmation, dismissal, deletion, emergency dispatch, diagnosis, medication-taken confirmation, and raw-video inspection as decision-maker.

Validation: `test_agent_policy.py` verifies allowed actions require purpose and provenance, and forbidden actions raise deterministic policy errors.
