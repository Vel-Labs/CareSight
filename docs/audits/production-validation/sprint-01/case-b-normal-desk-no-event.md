# Case B Normal Desk No-Event Proof

Date: 2026-05-21

## Result

Case B passed as a non-concerning no-event comparison.

The operator reran the bounded live loop while sitting normally at the desk. The run processed 60 seconds of frames and did not create a `possible_floor_stay` event.

## Operator Output

```text
v0_started camera=living_room room=Living Room source_type=webcam zone=floor_zone required_dwell_seconds=8.0 db=/Users/steven/Workspace/40_Code/hackathons/CareSight/apps/caresight-hub/data/caresight-v0.sqlite3
no_event_persisted {"camera_id": "living_room", "elapsed_seconds": 60.0, "frame_count": 1800, "required_dwell_seconds": 8.0, "status": "no_possible_floor_stay_event", "zone_id": "floor_zone"}
```

## Interpretation

This is the valid Case B comparison for Sprint 01/02 seeded-real A/B validation:

- Case A proves a concerning `possible_floor_stay` path with a human-confirmed event.
- Case B proves normal desk posture can run for the bounded window without creating a `possible_floor_stay` event.

Because Case B intentionally produced no event, there is no Case B `event_id`, snapshot, human-review packet, or blackbox receipt to generate. The `no_event_persisted` line is the machine-readable receipt for this run.

Future bounded normal/no-event runs are persisted as `observation_checks` rows in SQLite. Those checks are continuity evidence that the local system was running and did not escalate for the configured window. They are not reviewable events and should not create human-review packets.

## Boundary

This proof does not claim the heuristic is complete for all normal postures. It proves this specific normal desk comparison after the seated-desk false-positive regression fix.
