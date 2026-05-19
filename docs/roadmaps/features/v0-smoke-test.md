# v0 Smoke Test

Status: live YOLO26 MLX smoke complete; v0 eventization implemented; review and acknowledgement CLI implemented.

## Goal

Prove the minimal local loop:

```text
one camera -> YOLO26 MLX -> one zone/dwell rule -> one SQLite event row
```

## Completed Smoke Layer

- YOLO26 MLX cloned under `apps/caresight-hub/vendor/yolo-mlx`.
- `yolo26n.npz` converted and verified.
- Image smoke test works.
- Live webcam smoke test works with better native color, FPS/settings overlay, and COCO labels.
- Audit receipt: `docs/audits/2026-05-18-yolo26-mlx-smoke-checkpoint.md`.

## Next Resolution Layer

Run and verify the live floor-stay scenario end to end:

```text
webcam
  -> YOLO26 MLX
  -> floor-zone dwell
  -> local still snapshot
  -> event_persisted terminal output
  -> SQLite readback
  -> CLI inbox and summary
  -> human confirm/dismiss
  -> review, journal, and agent handoff rows
```

## Acceptance Criteria

- One local camera source can be processed.
- Person detections are available from YOLO26 MLX.
- A configured dwell rule creates `possible_floor_stay`.
- The event is persisted locally and inspectable after exit.
- A human can list/show the event from the CLI.
- A human can confirm or dismiss the event from the CLI.
- SQLite records the review, journal entry, and report-only agent handoff.

## Proposed Runtime Files

- `apps/caresight-hub/caresight/runtime/main.py`
- `apps/caresight-hub/caresight/runtime/config.py`
- `apps/caresight-hub/caresight/vision/yolo26_mlx_runner.py`
- `apps/caresight-hub/caresight/vision/detections.py`
- `apps/caresight-hub/caresight/vision/zones.py`
- `apps/caresight-hub/caresight/events/engine.py`
- `apps/caresight-hub/caresight/events/floor_stay.py`
- `apps/caresight-hub/caresight/storage/sqlite_store.py`
- `apps/caresight-hub/caresight/storage/migrations/001_init.sql`
- `apps/caresight-hub/scripts/v0_review_events.py`
- `apps/caresight-hub/tests/test_floor_stay.py`
- `apps/caresight-hub/tests/test_sqlite_store.py`
- `apps/caresight-hub/tests/test_v0_review_events.py`

## v0 Database Tables

- `cameras`
- `zones`
- `event_policies`
- `events`
- `event_observations`
- `event_reviews`
- `journal_entries`
- `agent_handoffs`

## Local Snapshot Output

Event stills are saved locally under:

```text
apps/caresight-hub/data/snapshots/
```

Each event includes `snapshot_path` and `snapshot_stays_local` in `evidence`.

## Run Command

```bash
source apps/caresight-hub/vendor/yolo-mlx/.venv/bin/activate
python apps/caresight-hub/scripts/v0_floor_stay_live.py
```

Review command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py list
python apps/caresight-hub/scripts/v0_review_events.py show <event_id>
python apps/caresight-hub/scripts/v0_review_events.py confirm <event_id> --reviewer steven --note "Checked snapshot."
python apps/caresight-hub/scripts/v0_review_events.py dismiss <event_id> --reviewer steven --note "False positive."
python apps/caresight-hub/scripts/v0_review_events.py journal <event_id>
```
