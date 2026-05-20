# T036 Live Proof After Settings Handoff

Date: 2026-05-20

GoalBuddy task: `T036`

## Context

`T035` opened macOS Camera privacy settings for the operator. `T036` checks whether that unblock step changed the live proof state.

## Readiness

```sh
python3 apps/caresight-hub/scripts/live_proof_audit.py readiness --camera-authorization not_checked
```

Result: `status` remained `not_ready` with blocker `camera_authorization_not_verified`.

## Runtime Command

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --no-window --max-seconds 20 --stop-after-event
```

Result: YOLO26 MLX loaded successfully, then OpenCV reported camera authorization is still blocked.

Key output:

```text
Matching weights: 594/594
Loaded weights successfully
OpenCV: not authorized to capture video (status 0), requesting...
OpenCV: camera failed to properly initialize!
Could not open camera 0
```

## Audit Finding

The macOS Camera permission has not taken effect for the process running the vendored Python interpreter. No fresh `event_persisted` line or downstream live oracle evidence was produced.

The remaining blocker is unchanged: the operator must grant camera access for the terminal, Codex-launched process, or app that runs:

```sh
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python
```

After authorization, rerun the 120-second bounded command from the operator handoff and collect the review/audit/dashboard/alert/bundle chain for the fresh event.
