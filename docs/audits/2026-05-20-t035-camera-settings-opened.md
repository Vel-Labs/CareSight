# T035 Camera Settings Opened

Date: 2026-05-20

GoalBuddy task: `T035`

## Action

Opened macOS Camera privacy settings for the operator:

```sh
open 'x-apple.systempreferences:com.apple.preference.security?Privacy_Camera'
```

## Result

The command completed successfully and should present the macOS Camera privacy settings pane to the operator.

## Remaining Operator Action

The operator must enable camera access for the terminal, Codex-launched app, or process used to run:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python
```

After camera access is granted, rerun:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 120 --stop-after-event
```

Do not claim final proof until a fresh `event_persisted` line is produced, reviewed by an authorized human, and completed by the SQLite audit/dashboard/alert/live-proof bundle chain.
