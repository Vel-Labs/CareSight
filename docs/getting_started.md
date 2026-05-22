# Getting Started

This guide covers the local demo path for CareSight Hub.

## 1. Validate the Repo

```bash
npm run check
```

Install local prerequisites when setting up a new machine:

```bash
python3 apps/caresight-hub/scripts/caresight_install_all.py
```

This installs the ignored runtime environment, default local models, and OBS where possible. Model weights, local SQLite, generated audio, and runtime logs stay out of Git.

## 2. Run a Bounded Vision Proof

From the repo root:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --max-seconds 60 \
  --stop-after-event \
  --no-window
```

If no possible floor-stay event is created, the command persists a normal/no-event `observation_checks` row and prints `no_event_persisted`.

To run the local no-send agent pipeline automatically after each detected event, start Gemma/Hermes first, then add:

```bash
--auto-agent-dry-run
```

The automatic path updates the OBS overlay, creates a local Gemma draft, stages an allowlisted iMessage request, and runs Hermes no-send preflight. It does not send the message or start FaceTime.

## 3. Start Local Gemma

```bash
python3 apps/caresight-hub/scripts/caresight_gemma_start.py
```

Gemma is served locally at:

```text
http://127.0.0.1:8080/v1
```

Stop it when done:

```bash
python3 apps/caresight-hub/scripts/caresight_gemma_stop.py
```

For the normal local test stack, use:

```bash
python3 apps/caresight-hub/scripts/caresight_stack_start.py
```

Stop the stack:

```bash
python3 apps/caresight-hub/scripts/caresight_stack_stop.py
```

Details: [Local Model Operations](operations/local_model_operations.md).

## 4. Generate Local TTS

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py \
  --voice dakota \
  --text "CareSight alert. Possible floor stay observed in the Living Room. Needs review."
```

This generates a local WAV under ignored local data. Playback requires explicit human validation:

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py \
  --voice dakota \
  --text "CareSight alert. Possible floor stay observed in the Living Room. Needs review." \
  --play
```

## 5. Prepare OBS Visual Handoff Scenes

Dry-run the scene plan:

```bash
./scripts/setup_obs_scene.sh --dry-run
```

To create/update OBS scenes, open OBS, enable `Tools > WebSocket Server Settings`, export `OBS_WEBSOCKET_PASSWORD`, then run:

```bash
./scripts/setup_obs_scene.sh
```

Refresh overlay event data from SQLite:

```bash
./scripts/update_obs_overlay.sh --event-id evt_d9aa38bdc636459c92ea4e25f665cd0d
```

During live testing, keep the overlay following the latest SQLite event:

```bash
./scripts/update_obs_overlay.sh --watch
```

Optional preferred FaceTime path: install [Aitum Vertical Canvas](https://github.com/Aitum/obs-vertical-canvas) so the desktop OBS canvas can stay landscape while FaceTime uses a dedicated vertical canvas.

```bash
./scripts/install_obs_vertical_canvas.sh
open apps/obs-hub/vendor/aitum/vertical-canvas-macos-universal.pkg
```

After restarting OBS, create the Aitum vertical scene `CareSight Hub - FaceTime Mobile`, then check:

```bash
apps/obs-hub/tools/aitum_vertical.py status
```

Use OBS or Aitum Virtual Camera in FaceTime only after confirming the scene shows intended CareSight feed/dashboard content and no unrelated private desktop content.

## 6. Preserve the Control Loop

CareSight is a local-first caregiver awareness prototype. It does not diagnose, dispatch, or confirm events without human review.

Allowed path:

```text
local observation -> SQLite event/check -> human review -> bounded draft -> approved handoff
```

Blocked path:

```text
raw vision -> model certainty -> autonomous emergency action
```
