# Camera Authorization Operator Handoff

Date: 2026-05-20

GoalBuddy task: `T034`

## Current Gate

The CareSight live proof is blocked at macOS camera authorization for the process running:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python
```

Recent bounded live proof retries loaded YOLO26 MLX successfully, then stopped with:

```text
OpenCV: not authorized to capture video (status 0), requesting...
OpenCV: camera failed to properly initialize!
Could not open camera 0
```

No final proof can be claimed until a fresh live `event_persisted` line is produced and reviewed by an authorized human.

## Operator Steps

1. Open macOS System Settings.
2. Go to Privacy & Security > Camera.
3. Enable camera access for the terminal or Codex-launched app/process used to run the command.
4. If macOS does not show the process yet, run the bounded command once, let the permission prompt appear, approve it, then rerun the command.
5. Keep raw video local. Do not upload raw video or use cloud camera providers.

## Live Proof Command

Run this after camera access is granted:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 120 --stop-after-event
```

Expected successful output includes:

```text
v0_started camera=living_room ...
event_persisted { ... }
```

Record the `event_id` and `evidence.snapshot_path` from the `event_persisted` JSON.

## Human Review

Only an authorized human may confirm or dismiss the event.

Show the event:

```sh
python apps/caresight-hub/scripts/v0_review_events.py show <event_id>
```

Confirm if appropriate:

```sh
python apps/caresight-hub/scripts/v0_review_events.py confirm <event_id> --reviewer "<authorized human>" --note "<review note>"
```

Dismiss if appropriate:

```sh
python apps/caresight-hub/scripts/v0_review_events.py dismiss <event_id> --reviewer "<authorized human>" --note "<review note>"
```

Agents must not run confirm or dismiss unless the authorized human explicitly instructs the exact review action.

## Final Audit Collection

After human review, collect the blackbox proof:

```sh
python apps/caresight-hub/scripts/v0_review_events.py audit <event_id>
python apps/caresight-hub/scripts/care_console.py dashboard
python apps/caresight-hub/scripts/care_console.py alert-draft <event_id>
python3 apps/caresight-hub/scripts/live_proof_audit.py bundle <event_id> --max-event-age-minutes 60
```

The final bundle must report `status: complete`. If it reports `not_complete`, do not claim final proof; use its blockers as the next task.

## Completion Boundary

The GoalBuddy goal may only be completed after the final receipt includes:

- fresh `event_persisted` output from current code
- `event_id`
- `snapshot_path`
- one inspected SQLite-backed audit chain
- authorized human review row
- journal entry
- report-only handoff
- dashboard and alert derived outputs
- complete live-proof audit bundle
- passing `npm run check`
