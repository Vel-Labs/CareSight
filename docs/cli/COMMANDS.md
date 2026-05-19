# CLI Commands

This index tracks commands that are safe to run locally and explains their inputs, outputs, validation, and agent boundary.

## Agent Safety Classes

- `agent-safe-read`: agents may run without human approval.
- `human-review-required`: agents may prepare or summarize, but a human must explicitly authorize state changes.
- `manual-operator`: intended for a human because it uses live camera or local environment resources.

## YOLO26 Image Smoke

Command:

```bash
python apps/caresight-hub/scripts/yolo26_image_smoke.py
```

Purpose: run YOLO26 MLX against the bundled image smoke fixture.

Inputs: local YOLO26 MLX environment, model path, and image fixture.

Outputs: local result image and terminal detection output.

Validation: covered by the v0 smoke checkpoint audit; rerun before claiming model readiness on a new machine.

Agent safety: `manual-operator`.

## YOLO26 Webcam Smoke

Command:

```bash
python apps/caresight-hub/scripts/yolo26_webcam_smoke.py
```

Purpose: verify live webcam capture and YOLO26 MLX person labels.

Inputs: local camera access and YOLO26 MLX model.

Outputs: local preview window and terminal diagnostics.

Validation: use for manual live-camera smoke checks only.

Agent safety: `manual-operator`.

## v0 Floor-Stay Live Loop

Command:

```bash
python apps/caresight-hub/scripts/v0_floor_stay_live.py
```

Purpose: create a local `possible_floor_stay` event after a person remains in the configured floor/low zone.

Inputs: `apps/caresight-hub/config/v0.local.json`, local camera, YOLO26 MLX model, SQLite database path.

Outputs: `event_persisted` terminal line, SQLite event row, event observation row, and local snapshot path.

Validation: `npm run py:check` covers deterministic event, SQLite, and snapshot behavior. Live camera behavior still needs manual verification.

Agent safety: `manual-operator`.

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

Validation: `test_v0_review_events.py` verifies reviewer requirement, status update, review row, journal row, and handoff payload.

Agent safety: `human-review-required`.

## v0 Review Events: Dismiss

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py dismiss <event_id> --reviewer <name> --note "<note>"
```

Purpose: record an authorized human dismissal.

Inputs: `event_id`, required `--reviewer`, optional `--note`, optional `--db <path>`.

Outputs: updated event status, `event_reviews` row, `journal_entries` row, and report-only `agent_handoffs` row.

Validation: `test_v0_review_events.py` verifies dismissed status, review row, journal row, and handoff payload.

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
