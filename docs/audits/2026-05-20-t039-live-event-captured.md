# T039 Live Event Captured

Date: 2026-05-20

GoalBuddy task: `T039`

## Live Event

The Terminal-launched bounded live proof produced a fresh `event_persisted` line from current code.

Event ID:

```text
evt_cf80f63995794c98b8bd6ebc197bf73d
```

Snapshot path:

```text
apps/caresight-hub/data/snapshots/evt_cf80f63995794c98b8bd6ebc197bf73d.jpg
```

Track ID:

```text
track_1
```

The event is still `awaiting_human_confirmation`.

## Read-Only Review Output

```sh
python3 apps/caresight-hub/scripts/v0_review_events.py show evt_cf80f63995794c98b8bd6ebc197bf73d
```

Key output:

```text
Possible floor-stay event in Living Room Built-in Webcam.
Observed in Floor / Low Zone for 8.18 seconds.
Detection confidence: 91.4%.
Status: awaiting human confirmation.
Snapshot: apps/caresight-hub/data/snapshots/evt_cf80f63995794c98b8bd6ebc197bf73d.jpg
```

## SQLite Audit Output

```sh
python3 apps/caresight-hub/scripts/v0_review_events.py audit evt_cf80f63995794c98b8bd6ebc197bf73d
```

Key output:

```text
Status: awaiting_human_confirmation
Snapshot path: apps/caresight-hub/data/snapshots/evt_cf80f63995794c98b8bd6ebc197bf73d.jpg
Observation rows: 1
Review rows: 0
Journal rows: 0
Agent handoff rows: 0
```

## Inspected SQLite Row

```sh
sqlite3 apps/caresight-hub/data/caresight-v0.sqlite3 "select e.event_id, e.status, e.camera_id, e.zone_id, json_extract(e.evidence_json, '$.snapshot_path') as snapshot_path, o.track_id from events e left join event_observations o on o.event_id=e.event_id where e.event_id='evt_cf80f63995794c98b8bd6ebc197bf73d';"
```

Output:

```text
evt_cf80f63995794c98b8bd6ebc197bf73d|awaiting_human_confirmation|living_room|floor_zone|apps/caresight-hub/data/snapshots/evt_cf80f63995794c98b8bd6ebc197bf73d.jpg|track_1
```

## Derived Read Models

The dashboard read model shows this event as the current event and keeps SQLite as the source of truth.

The caregiver alert draft is draft-only, human-review-required, and has SQLite audit-chain provenance.

## Live-Proof Bundle

```sh
python3 apps/caresight-hub/scripts/live_proof_audit.py bundle evt_cf80f63995794c98b8bd6ebc197bf73d --max-event-age-minutes 60
```

Result:

```text
status: not_complete
blockers: missing_human_review, missing_journal_entry, missing_report_only_handoff
observations: 1
reviews: 0
journal_entries: 0
agent_handoffs: 0
track_ids: track_1
```

## Boundary

Agents did not confirm or dismiss this event. The next required step is an authorized human review action. Only after that can the final journal, handoff, dashboard, alert, and live-proof bundle be completed.
