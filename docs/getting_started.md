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
  --text "CareSight noted a possible floor stay in the living room. Please review when available."
```

This generates a local WAV under ignored local data. Playback requires explicit human validation:

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py --play
```

## 5. Preserve the Control Loop

CareSight is a local-first caregiver awareness prototype. It does not diagnose, dispatch, or confirm events without human review.

Allowed path:

```text
local observation -> SQLite event/check -> human review -> bounded draft -> approved handoff
```

Blocked path:

```text
raw vision -> model certainty -> autonomous emergency action
```
