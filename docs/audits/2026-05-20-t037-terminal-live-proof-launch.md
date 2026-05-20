# T037 Terminal Live Proof Launch

Date: 2026-05-20

GoalBuddy task: `T037`

## Action

Launched the bounded live proof command in macOS Terminal so macOS can associate the Camera permission prompt with Terminal:

```sh
osascript -e 'tell application "Terminal" to activate' \
  -e 'tell application "Terminal" to do script "cd /Users/steven/Workspace/40_Code/hackathons/CareSight && apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 120 --stop-after-event"'
```

The AppleScript command returned:

```text
tab 1 of window id 1789
```

## Why

Prior Codex-launched attempts loaded YOLO26 MLX successfully but failed at macOS Camera authorization. Running the command in Terminal gives the operator a normal macOS app context where the Camera permission prompt may appear and can be approved.

## Evidence Boundary

This action does not prove the live oracle by itself. Codex cannot claim proof unless the Terminal run produces fresh output containing:

- `event_persisted`
- fresh `event_id`
- `evidence.snapshot_path`

After that, an authorized human must run the review path, followed by the SQLite audit/dashboard/alert/live-proof bundle commands.

## Next Required Operator Action

If macOS prompts for Camera access, approve it for Terminal. Then rerun or let the Terminal command complete and capture the `event_persisted` JSON.
