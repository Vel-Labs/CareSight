# T041 Final Live Proof

Date: 2026-05-20

GoalBuddy task: `T041`

## Result

The final live-proof bundle is complete for a fresh operator-run event with authorized human review.

Event ID:

```text
evt_d9aa38bdc636459c92ea4e25f665cd0d
```

Snapshot path:

```text
apps/caresight-hub/data/snapshots/evt_d9aa38bdc636459c92ea4e25f665cd0d.jpg
```

Human review command run by Steven:

```sh
python3 apps/caresight-hub/scripts/v0_review_events.py confirm evt_d9aa38bdc636459c92ea4e25f665cd0d --reviewer "Steven" --note "Reviewed live test snapshot; person is visibly lying in the floor/low zone for the configured dwell threshold. Confirmed as valid demo floor-stay event."
```

Output:

```text
Event evt_d9aa38bdc636459c92ea4e25f665cd0d status: human_confirmed
Review: review_f2b2b553ba9c4483b6405b1abf541a19
Journal: journal_9fcf5e31ea414c2a80e0b9c3f7976e5e
Agent handoff: handoff_dc62f62287ca4e4ab60e100f58e7a03d (report_only)
```

## Post-Review Audit

```sh
python3 apps/caresight-hub/scripts/v0_review_events.py audit evt_d9aa38bdc636459c92ea4e25f665cd0d
```

Key output:

```text
Status: human_confirmed
Observation rows: 1
Review rows: 1
Journal rows: 1
Agent handoff rows: 1
Latest reviewer: Steven
Latest review decision: human_confirmed
Latest handoff status: report_only
```

## Journal

```sh
python3 apps/caresight-hub/scripts/v0_review_events.py journal evt_d9aa38bdc636459c92ea4e25f665cd0d
```

Key output:

```text
possible_floor_stay human_confirmed
Created: 2026-05-20T02:38:02.406241Z by Steven
Blocked actions remained blocked: autonomous_emergency_dispatch, medical_diagnosis.
```

## Inspected SQLite Row

```sh
sqlite3 apps/caresight-hub/data/caresight-v0.sqlite3 "select e.event_id, e.status, e.camera_id, e.zone_id, json_extract(e.evidence_json, '$.snapshot_path'), o.track_id, r.reviewer, r.decision, j.journal_id, h.handoff_id, h.status from events e left join event_observations o on o.event_id=e.event_id left join event_reviews r on r.event_id=e.event_id left join journal_entries j on j.event_id=e.event_id left join agent_handoffs h on h.event_id=e.event_id where e.event_id='evt_d9aa38bdc636459c92ea4e25f665cd0d';"
```

Output:

```text
evt_d9aa38bdc636459c92ea4e25f665cd0d|human_confirmed|living_room|floor_zone|apps/caresight-hub/data/snapshots/evt_d9aa38bdc636459c92ea4e25f665cd0d.jpg|track_5|Steven|human_confirmed|journal_9fcf5e31ea414c2a80e0b9c3f7976e5e|handoff_dc62f62287ca4e4ab60e100f58e7a03d|report_only
```

## Dashboard And Alert

```sh
python3 apps/caresight-hub/scripts/care_console.py dashboard
```

The dashboard timeline includes `evt_d9aa38bdc636459c92ea4e25f665cd0d` as the newest event with `status: human_confirmed`. The dashboard also still reports four older awaiting-review demo rows; those are not used as final proof.

```sh
python3 apps/caresight-hub/scripts/care_console.py alert-draft evt_d9aa38bdc636459c92ea4e25f665cd0d
```

Key output:

```text
Status is human confirmed.
Snapshot path: apps/caresight-hub/data/snapshots/evt_d9aa38bdc636459c92ea4e25f665cd0d.jpg.
boundaries: draft_only, human_review_required, no_autonomous_dispatch, no_medical_diagnosis
provenance source: sqlite_audit_chain
```

## Live-Proof Bundle

```sh
python3 apps/caresight-hub/scripts/live_proof_audit.py bundle evt_d9aa38bdc636459c92ea4e25f665cd0d --max-event-age-minutes 60
```

Result:

```text
status: complete
blockers: []
observations: 1
reviews: 1
journal_entries: 1
agent_handoffs: 1
track_ids: track_5
source_of_truth: sqlite
```

## Boundary Notes

- SQLite remains canonical.
- The dashboard and alert outputs are derived, not source of truth.
- The agent did not confirm, dismiss, dispatch, diagnose, delete, or become reviewer of record.
- Raw video stayed local.
- The alert is a draft-only caregiver message, not emergency dispatch.

## Verification

```sh
node /Users/steven/.codex/plugins/cache/goalbuddy/goalbuddy/0.3.7/skills/goalbuddy/scripts/check-goal-state.mjs docs/goals/caresight-sprint-buildout/state.yaml
```

Result:

```text
ok: true
goal_status: done
active_task: null
errors: []
warnings: []
```

```sh
npm run check
```

Result:

```text
Scaffold validation passed.
Contract validation passed: 8 schema(s), 10 valid example(s), 6 invalid example(s).
Vitest: 2 files passed, 5 tests passed.
Typecheck: passed.
Python unittest: Ran 58 tests. OK.
```
