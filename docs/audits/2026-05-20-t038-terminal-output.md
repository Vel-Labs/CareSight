# T038 Terminal Live Proof Output

Date: 2026-05-20

GoalBuddy task: `T038`

## Action

Read the macOS Terminal tab launched by `T037` to inspect the actual live-proof command output.

Command used to inspect Terminal:

```sh
osascript -e 'tell application "Terminal" to get contents of selected tab of front window'
```

## Terminal Output Finding

The Terminal-launched live proof reached the vendored YOLO26 MLX runtime, loaded model weights, then failed at macOS Camera authorization:

```text
Matching weights: 594/594
Loaded weights successfully
OpenCV: not authorized to capture video (status 0), requesting...
OpenCV: camera failed to properly initialize!
Could not open camera 0
```

The prompt returned to:

```text
steven@Stevens-MacBook-Pro CareSight %
```

## Audit Finding

Terminal did not produce a fresh `event_persisted` line. No live oracle evidence exists from this attempt.

The blocker remains operator-controlled macOS Camera authorization for Terminal or the process running:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python
```

## Required Next Step

Grant Camera access to Terminal in macOS Privacy & Security > Camera, then rerun:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 120 --stop-after-event
```

Only after a fresh `event_persisted` line appears should the review/audit/dashboard/alert/bundle chain continue.
