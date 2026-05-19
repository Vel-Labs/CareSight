# v0 Eventization Implementation Audit

Date: 2026-05-18

## Scope

This audit records the first CareSight Hub v0 implementation layer after the YOLO26 MLX smoke checkpoint.

The implemented layer turns live detections into contract-shaped `possible_floor_stay` events and persists them locally. The follow-up review layer turns that row into a human-confirmed or dismissed journaled event with a report-only agent handoff payload.

## Implemented Flow

```text
YOLO26 MLX detections
  -> normalized Detection objects
  -> configured floor/low zone
  -> dwell-time state
  -> possible_floor_stay event JSON
  -> local still snapshot
  -> SQLite event row
  -> SQLite triggering observation row
  -> terminal readback
  -> CLI event inbox
  -> human-readable event summary
  -> human confirm/dismiss
  -> review row
  -> journal entry
  -> report-only agent handoff row
```

## Configuration

Editable config:

```text
apps/caresight-hub/config/v0.local.json
```

The default config uses:

- camera: `living_room`
- source: webcam index `0`
- requested capture: `1280x720@30`
- zone: `floor_zone`
- zone geometry: bottom third of the frame
- dwell threshold: `8.0` seconds
- database: `apps/caresight-hub/data/caresight-v0.sqlite3`

## SQLite Tables

v0 creates these local tables:

- `cameras`: configured camera source snapshot.
- `zones`: configured zone geometry.
- `event_policies`: event threshold and policy snapshot.
- `events`: canonical care-event row.
- `event_observations`: triggering detection row for event evidence.
- `event_reviews`: authorized human review decision and note.
- `journal_entries`: human-readable care journal entries tied to events.
- `agent_handoffs`: report-only payloads for future agent workflows.
- `apps/caresight-hub/data/snapshots/`: local event still images named by `event_id`.

## Run Command

```bash
source apps/caresight-hub/vendor/yolo-mlx/.venv/bin/activate
python apps/caresight-hub/scripts/v0_floor_stay_live.py
```

Review commands:

```bash
python apps/caresight-hub/scripts/v0_review_events.py list
python apps/caresight-hub/scripts/v0_review_events.py show <event_id>
python apps/caresight-hub/scripts/v0_review_events.py confirm <event_id> --reviewer steven --note "Checked snapshot."
python apps/caresight-hub/scripts/v0_review_events.py dismiss <event_id> --reviewer steven --note "False positive."
python apps/caresight-hub/scripts/v0_review_events.py journal <event_id>
```

Manual test:

1. Start the v0 loop.
2. Move into the green `Floor / Low Zone`.
3. Stay low for at least the configured dwell threshold.
4. Confirm terminal prints `event_persisted`.
5. Confirm the event is stored in SQLite.
6. Confirm event evidence includes `snapshot_path` and `snapshot_stays_local`.
7. Confirm `list` shows the awaiting event by default.
8. Confirm `show` renders event ID, status, zone, dwell, snapshot, and blocked actions.
9. Confirm or dismiss only with an authorized `--reviewer`.
10. Confirm `event_reviews`, `journal_entries`, and `agent_handoffs` rows are created.

## Validation

Automated coverage added for:

- config save/load
- floor-zone dwell event creation
- repeated-event suppression during one dwell
- SQLite config snapshot persistence
- SQLite event readback
- SQLite event observation readback
- local snapshot evidence attachment
- review CLI inbox filtering
- deterministic human-readable event summary formatting
- reviewer requirement for confirm/dismiss
- status transitions for `human_confirmed` and `dismissed`
- review, journal, and report-only handoff row creation
- emergency dispatch absence from CLI commands

Command:

```bash
npm run check
```

Result at implementation time: passing.

## Boundaries

This is still v0. It does not claim fall detection, medical certainty, autonomous emergency dispatch, or medication confirmation.
