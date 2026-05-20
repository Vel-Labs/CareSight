# T033 Live Proof Retry

Date: 2026-05-20

GoalBuddy task: `T033`

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

No fresh live proof was produced. The current blocker remains operator-controlled macOS camera authorization for the process running:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python
```

Do not claim final proof from stale events. The final oracle still requires fresh `event_persisted`, `event_id`, `snapshot_path`, authorized human review, journal, handoff, dashboard, alert, and live-proof bundle output.
