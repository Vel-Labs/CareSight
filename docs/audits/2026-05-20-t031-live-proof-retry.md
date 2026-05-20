# T031 Live Proof Retry

Date: 2026-05-20

GoalBuddy task: `T031`

## Board State

`T031` is the active PM task for operator camera authorization and fresh live-proof oracle collection.

## Readiness Check

```sh
python3 apps/caresight-hub/scripts/live_proof_audit.py readiness --camera-authorization not_checked
```

Result: `status` was `not_ready` with blocker `camera_authorization_not_verified`.

The readiness report confirmed config, model, and SQLite paths are present. It also listed the configured local cameras:

- `living_room` (`webcam`)
- `living_room_usb` (`usb`)
- `living_room_continuity` (`continuity_camera`)
- `kitchen_rtsp` (`rtsp`)

## Live Runtime Check

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 20 --stop-after-event
```

Result: the command reached the intended vendored runtime and loaded YOLO26 MLX weights, then failed at macOS camera authorization.

Key output:

```text
Matching weights: 594/594
Loaded weights successfully
OpenCV: not authorized to capture video (status 0), requesting...
OpenCV: camera failed to properly initialize!
Could not open camera 0
```

## Audit Finding

No `event_persisted` line was produced. There is no fresh live `event_id`, `snapshot_path`, authorized human review, journal entry, handoff, dashboard proof, alert draft, or live-proof audit bundle from this attempt.

The current blocker remains operator-controlled macOS camera authorization for the process running:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python
```

## Required Next Step

After camera access is granted, rerun:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 120 --stop-after-event
```

Then collect review, journal, audit, dashboard, alert, and `live_proof_audit.py bundle` output for the fresh event.
