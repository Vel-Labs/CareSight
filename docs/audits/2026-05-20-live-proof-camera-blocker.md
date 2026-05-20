# Live Proof Camera Blocker

Date: 2026-05-19

GoalBuddy task: `T023`

## Purpose

Attempt the bounded live-camera proof with the intended vendored YOLO26 MLX runtime after `T022` fixed CLI readiness.

## Commands

```sh
python3 apps/caresight-hub/scripts/v0_floor_stay_live.py --no-window --max-seconds 8 --stop-after-event
```

Result: failed before runtime dependencies because base `python3` does not include `cv2`.

Key output:

```text
ModuleNotFoundError: No module named 'cv2'
```

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --no-window --max-seconds 8 --stop-after-event
```

Result: reached the intended vendored runtime outside the sandbox, loaded YOLO26 MLX weights, then failed at local camera authorization.

Key output:

```text
Loading npz weights from /Users/steven/Workspace/40_Code/hackathons/CareSight/apps/caresight-hub/vendor/yolo-mlx/models/yolo26n.npz
Matching weights: 594/594
Loaded weights successfully
OpenCV: not authorized to capture video (status 0), requesting...
OpenCV: camera failed to properly initialize!
Could not open camera 0
```

## Audit Finding

The live proof is still blocked, but the blocker moved from CLI/runtime readiness to macOS camera authorization for the process running the vendored Python interpreter.

No `event_persisted` line was produced. No event review, journal entry, handoff, dashboard proof, or alert draft can be claimed from this run.

## Required Operator Step

Grant camera access to the terminal or Codex-launched process that runs:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --no-window --max-seconds 120 --stop-after-event
```

After a fresh `event_persisted` line is produced, an authorized human reviewer must run the confirm or dismiss path before final blackbox proof can be completed.
