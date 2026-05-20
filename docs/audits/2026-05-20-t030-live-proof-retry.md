# T030 Live Proof Retry

Date: 2026-05-20

GoalBuddy task: `T030`

## Command

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 20 --stop-after-event
```

## Result

The command reached the intended vendored runtime and loaded YOLO26 MLX weights, but did not reach frame capture or event persistence.

Key output:

```text
Matching weights: 594/594
Loaded weights successfully
OpenCV: not authorized to capture video (status 0), requesting...
OpenCV: camera failed to properly initialize!
Could not open camera 0
```

No `event_persisted` line was produced. No fresh `event_id`, `snapshot_path`, human review, journal entry, handoff, dashboard proof, alert draft, or live-proof audit bundle can be claimed from this attempt.

## Readiness Check

```sh
python3 apps/caresight-hub/scripts/live_proof_audit.py readiness --camera-authorization blocked
```

Result: `status` remained `not_ready` with blocker `camera_authorization_blocked`.

The readiness output confirmed:

- model file exists
- config file is ready
- SQLite database exists
- configured cameras include `living_room`, `living_room_usb`, `living_room_continuity`, and `kitchen_rtsp`
- camera authorization remains the live proof blocker

## Required Next Step

An operator must grant macOS camera access to the process running the vendored Python interpreter, then rerun:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 120 --stop-after-event
```

After a fresh `event_persisted` line appears, an authorized human reviewer must run the review path before the final blackbox proof can complete.
