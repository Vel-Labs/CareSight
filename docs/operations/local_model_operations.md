# Local Model Operations

CareSight uses local models as downstream drafting and presentation helpers. SQLite remains canonical, YOLO26 MLX remains the vision lane, and Gemma/Holler must not make medical, emergency, or autonomous-dispatch decisions.

## Runtime Environment

The local model runtime is intentionally outside Git:

```bash
apps/caresight-hub/.venv
```

Expected local packages include `mlx-vlm`, `mlx-lm`, `mlx-audio`, `fastapi`, `uvicorn`, `soundfile`, `obsws-python`, and `huggingface_hub[cli]`.

Install or refresh the local runtime:

```bash
python3 apps/caresight-hub/scripts/caresight_install_runtime.py
```

Install the default local model set:

```bash
python3 apps/caresight-hub/scripts/caresight_install_models.py
```

Install one model:

```bash
python3 apps/caresight-hub/scripts/caresight_install_model.py gemma-e2b
python3 apps/caresight-hub/scripts/caresight_install_model.py holler-6bit
```

Install all default local prerequisites:

```bash
python3 apps/caresight-hub/scripts/caresight_install_all.py
```

Model weights and generated runtime data are ignored by Git:

```text
apps/caresight-hub/models/
apps/caresight-hub/data/
apps/caresight-hub/.venv/
```

## Gemma Endpoint

Start the local OpenAI-compatible Gemma endpoint:

```bash
python3 apps/caresight-hub/scripts/caresight_gemma_start.py
```

Default endpoint:

```text
http://127.0.0.1:8080/v1
```

Default model:

```text
apps/caresight-hub/models/reasoning/gemma/gemma-4-e2b-it-4bit
```

The selected runner is `mlx-vlm.server`, because it loads the existing Gemma 4 E2B MLX model. `mlx_lm.server` is not the selected runner for these local packages because it failed the model-load check.

Smoke test:

```bash
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "apps/caresight-hub/models/reasoning/gemma/gemma-4-e2b-it-4bit",
    "messages": [
      {
        "role": "system",
        "content": "You write bounded local-first CareSight caregiver messages. Do not claim diagnosis, fall certainty, injury, or emergency dispatch."
      },
      {
        "role": "user",
        "content": "Write one short caregiver alert for a possible floor stay in the living room. Mention human review."
      }
    ],
    "max_tokens": 80,
    "temperature": 0
  }'
```

Stop the endpoint:

```bash
python3 apps/caresight-hub/scripts/caresight_gemma_stop.py
```

The start script includes a chat-completions pulse check before it reports `gemma_started`.

Runtime files are written under ignored local data:

```text
apps/caresight-hub/data/runtime/gemma-server.pid
apps/caresight-hub/data/runtime/gemma-server.log
```

## Hermes Harness Readiness

Hermes is currently a vendored no-send service-wrapper harness, not a long-running daemon. The start script verifies the vendored tool import, config template, and no-send message-directory preflight, then writes a local readiness marker:

```bash
python3 apps/caresight-hub/scripts/caresight_hermes_start.py --require-gemma
```

Stop clears the readiness marker:

```bash
python3 apps/caresight-hub/scripts/caresight_hermes_stop.py
```

Runtime marker:

```text
apps/caresight-hub/data/runtime/hermes-ready.json
```

The Hermes readiness check calls only `send_message(action="list")`; it does not send messages, write notes, start FaceTime, play audio, or expose raw video.

## Local Stack

Start the local operator stack in dependency order:

```bash
python3 apps/caresight-hub/scripts/caresight_stack_start.py
```

This starts Gemma first, waits for the local chat-completions pulse check, then verifies Hermes readiness with Gemma required.

Stop the stack:

```bash
python3 apps/caresight-hub/scripts/caresight_stack_stop.py
```

Build local fixture/readiness outputs:

```bash
python3 apps/caresight-hub/scripts/caresight_setup_fixtures.py
```

## TTS Generation

Generate a local Holler TTS WAV without playback:

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py \
  --text "CareSight noted a possible floor stay in the living room. Please review when available."
```

Default output directory:

```text
apps/caresight-hub/data/tts/
```

Default voice:

```text
kit
```

Known local voices include `kit`, `dakota`, `nora`, `joe`, `oliver`, and `tessa`.

Playback is intentionally opt-in:

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py --play
```

Only use playback after the message wording has been approved for human validation. TTS may read an approved utterance; it must not decide what happened.

## 16 GB Mac Profile

Use Gemma 4 E2B 4-bit as the default 16 GB Mac mini target. The local smoke test reported roughly 3.77 GB peak memory for a short `/v1/chat/completions` request through `mlx-vlm.server`.

Keep context and generation bounded:

- Prefer `--max-kv-size 1024` for the demo path.
- Use short SQLite-derived evidence packets.
- Do not pass raw video or image bytes to Gemma.
- Keep TTS loaded only when generating or playing audio.

## Safety Boundaries

- No cloud fallback for care context unless explicitly approved.
- No iMessage, FaceTime, Apple Notes, OBS capture, or TTS playback without the relevant human approval gate.
- No medical diagnosis, fall certainty, injury claim, or autonomous emergency dispatch.
- JSON remains the machine/audit receipt; Gemma may draft concise caregiver-facing wording.

## Command Registry

The local command registry lives at:

```text
apps/caresight-hub/config/command-registry.json
```

It is an inspectable allowlist for local LLM/Hermes maneuvering. Commands that perform live actions are explicitly marked `human-review-required`.
