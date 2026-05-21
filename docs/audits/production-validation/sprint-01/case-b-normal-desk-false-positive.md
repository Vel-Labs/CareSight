# Case B Normal Desk False Positive

Date: 2026-05-21

## Intent

Use the operator sitting normally at a desk as the non-concerning Case B comparison.

Expected valid Case B outcome:

- No `possible_floor_stay` event during the bounded run, or
- A non-urgent event that can be audited without concern escalation.

## Operator-Run Command

The operator ran the live loop from the home directory with absolute script paths:

```bash
/Users/steven/Workspace/40_Code/hackathons/CareSight/apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python /Users/steven/Workspace/40_Code/hackathons/CareSight/apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --max-seconds 60 --stop-after-event --no-window
```

## Observed Event

The run created this event while the operator reported sitting normally at the desk:

```text
evt_d2737bde216d4c6eb9d2bc63f29dc7ef
```

Because the command was launched from `~` and the config database path was relative at the time, the event was written outside the repo checkout:

```text
/Users/steven/apps/caresight-hub/data/caresight-v0.sqlite3
```

Audit command:

```bash
python3 apps/caresight-hub/scripts/v0_review_events.py --db /Users/steven/apps/caresight-hub/data/caresight-v0.sqlite3 audit evt_d2737bde216d4c6eb9d2bc63f29dc7ef
```

Key audit output:

```text
Event type: possible_floor_stay
Status: awaiting_human_confirmation
Snapshot path: apps/caresight-hub/data/snapshots/evt_d2737bde216d4c6eb9d2bc63f29dc7ef.jpg
Observation rows: 1
Review rows: 0
Journal rows: 0
Agent handoff rows: 0
```

## Result

This is not a passing Case B. It is a false-positive/over-trigger finding for the current floor-zone heuristic.

The event should not be confirmed, dismissed, or used as proof of a concerning floor-stay by an agent. It requires human review if the operator wants to mutate lifecycle state.

## Implementation Follow-Up

The live runner was updated after this attempt so:

- startup output labels the threshold as `required_dwell_seconds`, not observed dwell;
- normal no-event runs print a `no_event_persisted` machine-readable receipt;
- relative runtime database paths resolve to the repo root rather than the caller's shell working directory.
- the floor-stay detector now rejects the observed seated-desk bounding-box shape as a regression case.

Case B remains open until a bounded normal desk run produces a clear no-event receipt or a tuned non-urgent event path.
