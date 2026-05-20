# T032 Live Proof Retry

Date: 2026-05-20

GoalBuddy task: `T032`

## Command

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 20 --stop-after-event
```

## Result

The command loaded the vendored YOLO26 MLX runtime and weights, then stopped before frame capture because macOS camera authorization is still blocked.

Key output:

```text
Matching weights: 594/594
Loaded weights successfully
OpenCV: not authorized to capture video (status 0), requesting...
OpenCV: camera failed to properly initialize!
Could not open camera 0
```

## Audit Finding

No fresh live proof was produced:

- no `event_persisted` line
- no fresh `event_id`
- no `snapshot_path`
- no authorized human review
- no journal entry
- no handoff
- no dashboard or alert proof
- no completed `live_proof_audit.py bundle`

The remaining blocker is unchanged: an operator must grant macOS camera access to the process running the vendored Python interpreter.

## Required Operator Command After Authorization

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 120 --stop-after-event
```
