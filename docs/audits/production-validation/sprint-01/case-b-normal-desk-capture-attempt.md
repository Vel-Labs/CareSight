# Case B Normal Desk Capture Attempt

Date: 2026-05-21

## Intent

Capture a bounded normal desk/non-concerning Case B comparison while the operator is sitting normally at the desk.

Expected valid outcome:

- No `possible_floor_stay` event is created during the bounded run, or
- A captured event ID is audited and shown to be non-urgent before use as Case B.

## Command

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --max-seconds 60 --stop-after-event --no-window
```

## Result

The model loaded, but camera capture was blocked by macOS authorization before any normal desk proof could be collected.

Observed terminal output:

```text
OpenCV: not authorized to capture video (status 0), requesting...
OpenCV: camera failed to properly initialize!
Could not open camera 0
```

## Status

Blocked. This is not a valid Case B proof because no camera frames were captured.

## Required Operator Step

Grant camera access for the terminal/Python runtime, then rerun the bounded command while sitting normally at the desk:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --max-seconds 60 --stop-after-event --no-window
```

If the command exits without `event_persisted`, record that as the Case B no-event comparison. If it prints an `event_persisted` line, provide the event ID so it can be audited before being used as Case B.
