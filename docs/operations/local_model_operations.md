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

Tracked model governance lives in `apps/caresight-hub/config/model-manifests.example.json`. The example manifest records each model lane's source URL, license, local path, checksum, expected size, runtime, allowed uses, blocked uses, validation command, and last validation status. Local operators should copy or override it with machine-specific checksums before claiming a model lane is ready.

Run the model doctor:

```bash
python apps/caresight-hub/scripts/care_console.py model-doctor --manifest apps/caresight-hub/config/model-manifests.example.json
```

The doctor checks manifest completeness, local path existence, size, and SHA-256. Add `--run-validation-command` only when the operator wants to execute the manifest's local validation command.

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
  --voice dakota \
  --text "CareSight alert. Possible floor stay observed in the Living Room. Needs review."
```

Default output directory:

```text
apps/caresight-hub/data/tts/
```

Preferred validation voice:

```text
dakota
```

Known local voices include `kit`, `dakota`, `nora`, `joe`, `oliver`, and `tessa`.

Playback is intentionally opt-in:

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py \
  --voice dakota \
  --text "CareSight alert. Possible floor stay observed in the Living Room. Needs review." \
  --play
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

## OBS Visual Handoff Scenes

CareSight OBS Hub lives under `apps/obs-hub/` and uses OBS browser sources for caregiver-facing overlays.

Dry-run:

```bash
./scripts/setup_obs_scene.sh --dry-run
```

Live local setup:

```bash
export OBS_WEBSOCKET_PASSWORD="your-obs-password"
./scripts/setup_obs_scene.sh
```

If OBS websocket is unavailable, enable it in OBS under `Tools > WebSocket Server Settings`, set port `4455`, set/copy the password, and rerun the setup command.

Optional experimental phone output with [Aitum Vertical Canvas](https://github.com/Aitum/obs-vertical-canvas):

```bash
./scripts/install_obs_vertical_canvas.sh
open apps/obs-hub/vendor/aitum/vertical-canvas-macos-universal.pkg
```

Restart OBS after installing Aitum Vertical Canvas, then check:

```bash
apps/obs-hub/tools/aitum_vertical.py status
```

The Aitum path lets CareSight keep the desktop OBS canvas at `1920x1080` while testing a purpose-built `1080x1920` vertical canvas. It is not the default live demo path because macOS FaceTime can stretch or mirror OBS/Aitum virtual-camera output even when the OBS vertical preview is correct. Keep `CARESIGHT_AITUM_VERTICAL_MODE=off` for the stable hackathon flow.

If status reports `No vendor was found by that name`, restart OBS after installing the plugin. Current Aitum websocket support covers switching/status/virtual-camera control, but vertical scene/source creation still requires the Aitum dock UI.

Refresh dynamic overlay state:

```bash
./scripts/update_obs_overlay.sh --event-id evt_d9aa38bdc636459c92ea4e25f665cd0d
```

Follow the latest SQLite event during live testing:

```bash
./scripts/update_obs_overlay.sh --watch
```

Local Gemma/Hermes tools should prefer the one-shot update command for explicit visual handoff updates. Operators should prefer watch mode during live testing. Both rewrite ignored `apps/obs-hub/config/current_event.json` and `apps/obs-hub/config/current_event.js` from SQLite-derived event context, while OBS scenes and browser sources remain stable.

## Automatic No-Send Event Pipeline

After `python3 apps/caresight-hub/scripts/caresight_stack_start.py` reports `stack_started`, the live detector can run the local no-send agent path automatically:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --max-seconds 600 \
  --no-window \
  --auto-agent-dry-run
```

For each persisted event, the detector updates OBS overlay state, asks local Gemma for a bounded alert draft, stages an allowlisted iMessage request, and records a Hermes no-send preflight receipt. It prints `post_event_agent_dry_run` when the chain succeeds.

This is not a live-send command. Human approval remains required before any iMessage, FaceTime, TTS playback, or visual handoff execution.

## Human-Approved Live Handoff Test

The bounded live test is split into two steps:

1. Send the approved alert text after a real persisted event.
2. Open FaceTime only if the caregiver reply is yes-like and the operator supplies that reply text.

The live alert text is:

```text
CareSight alert. Possible floor stay observed in the Living Room. Needs review. Would you like to connect to CareSight?
```

Set private contact targets in the shell or in an ignored private allowlist. Do not commit real phone numbers, emails, BlueBubbles credentials, or contact handles.

```bash
python3 apps/caresight-hub/scripts/caresight_contacts_config.py \
  --display-label "Primary emergency contact" \
  --imessage "<private-imessage-handle>" \
  --facetime "<private-facetime-handle>"

export CARESIGHT_CONTACT_ALLOWLIST_PATH=apps/caresight-hub/config/hermes/allowlisted-contacts.local.json
```

The generated `allowlisted-contacts.local.json` file is ignored by git. Shell env targets still work for one-off tests, but the local allowlist is the preferred demo setup because it keeps repeated commands smaller and gives Hermes/local tools a stable contact source.

For first-time setup, operators can also copy and edit:

```text
apps/caresight-hub/config/hermes/allowlisted-contacts.local.example.json
apps/caresight-hub/config/live-demo.local.example
```

Copy them to `allowlisted-contacts.local.json` and `live-demo.local`. The local files are ignored by git and are the closest project equivalent to `.env.local`.

Live detector command:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --max-seconds 600 \
  --no-window \
  --obs-browser-feed \
  --auto-agent-live-run \
  --live-approved
```

When `post_event_agent_live_run` prints, copy its `request_id`. If the caregiver replies affirmatively, run:

```bash
python3 apps/caresight-hub/scripts/caresight_live_handoff.py \
  facetime-if-yes <request_id> \
  --reply-text "yes connect" \
  --live-approved
```

FaceTime approval requires an explicit phrase such as `yes connect` or `yes FaceTime`. Ambiguous or opportunity replies create follow-up context but do not authorize the live handoff.

The repo does not poll the macOS Messages database by default. Reply polling would require a separate privacy decision because it usually needs Full Disk Access.

## Privacy Redaction Lane

`model_openai_privacy_filter` is listed as an optional privacy-filter manifest for local PII detection review. CareSight treats it as a redaction aid only, not anonymization, HIPAA compliance, safety proof, or medical privacy clearance. Journal export review can run through:

```bash
python3 apps/caresight-hub/scripts/care_console.py journal-redact <event_id> \
  --journal-id <journal_id> \
  --export-classification local-only
```

For the hackathon live demo, the detector can run the full approved flow for bounded `possible_floor_stay` events that are awaiting human confirmation:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --max-seconds 600 \
  --no-window \
  --auto-agent-live-run \
  --live-approved \
  --obs-live-preview \
  --auto-facetime-on-reply \
  --no-response-escalation-seconds 90 \
  --play-tts-after-facetime \
  --tts-audio-route blackhole \
  --tts-volume 6.0 \
  --tts-repeat-count 2 \
  --tts-repeat-delay-seconds 1.5 \
  --tts-after-facetime-delay-seconds 16 \
  --post-facetime-hold-seconds 30
```

This prefers `imsg` for a yes-like reply after the alert send, then falls back to the scoped SQLite reader. `imsg` and the fallback both need macOS Full Disk Access to read Messages. If access is blocked, the command fails closed after the text/snapshot stage and no FaceTime/TTS step runs automatically. After FaceTime is requested, the command waits briefly before TTS playback and then keeps running for a bounded review window so the OBS feed does not disappear immediately. Missing-off-camera remains a separate review/escalation lane and should not reuse the floor-stay live call path.

The stable handoff path does not rely on FaceTime receiving OBS video. OBS remains the local operator/review surface, iMessage carries the alert and optional snapshot evidence, and FaceTime is used for the reply-gated call plus approved TTS audio. The experimental Aitum portrait bridge can be enabled with `CARESIGHT_AITUM_VERTICAL_MODE=auto`, but it is not required for sprint validation because FaceTime may distort that virtual-camera output.

The mobile scene uses a local browser-rendered detector feed. The live detector serves annotated MJPEG at:

```text
http://127.0.0.1:8766/live.html
http://127.0.0.1:8766/stream.mjpg
```

OBS should use the `/live.html` page as a Browser Source URL. That page renders the underlying MJPEG stream. Python owns the camera and draws the boxes/zone overlay; OBS does not open the webcam separately. `apps/obs-hub/config/live_preview.jpg` remains a fallback artifact when `--obs-live-preview` is enabled, not the primary live feed.

If no reply is observed before the no-response escalation window, the command sends one follow-up iMessage with the local event snapshot attached:

```text
This is CareSight Hub escalation. We have not heard back, but there is an event that requires caregiver verification. Please see the image attached, and reply yes to see a live feed.
```

The follow-up uses the same allowlisted target and remains bounded to caregiver verification. It does not dispatch help, diagnose, or send raw video to an agent.

`--obs-live-preview` writes a fallback annotated detector frame to:

```text
apps/obs-hub/config/live_preview.jpg
```

`--obs-browser-feed` is the primary live OBS feed. The JPG exists for audit/debug fallback and screenshot-style evidence.

When the detector appears not to fire, add `--debug-floor-stay` to the same live command or run a short diagnostic-only pass:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --max-seconds 60 \
  --no-window \
  --obs-browser-feed \
  --obs-live-preview \
  --debug-floor-stay
```

Each `floor_stay_debug` line reports whether a person box is in the configured floor zone, whether it has low-posture shape, and the current dwell seconds. This is the fastest way to tell camera/source setup problems from post-event iMessage/FaceTime failures.

The TTS readout uses Dakota by default:

```text
This is an automated CareSight message. A possible floor stay was observed in the Living Room. Please review the live feed. CareSight will keep this handoff open briefly for review.
```

Audio routing into the FaceTime call depends on the operator's macOS audio setup. `--tts-audio-route blackhole` uses `SwitchAudioSource` to temporarily set default input/output to `BlackHole 2ch` while TTS plays, then restores the prior devices. This requires:

```bash
brew install switchaudio-osx
brew install --cask blackhole-2ch
```

BlackHole install requires a reboot before the device appears. Run:

```bash
python3 apps/caresight-hub/scripts/caresight_audio_route.py check
```

The temporary BlackHole route is intended for the TTS moment only; it is not a permanent microphone change.

Recovery note: `docs/audits/2026-05-23-sprint-02-facetime-obs-tts-resolution-ladder.md` is the current no-call troubleshooting ladder. It treats OBS as the stable local visual surface, FaceTime as an operator-approved audio/TTS handoff, and OBS/Aitum virtual-camera-to-FaceTime video as optional until a human validates the actual macOS output.

Before live testing, run:

```bash
python3 apps/caresight-hub/scripts/caresight_demo_preflight.py
```

This checks the local contact allowlist, YOLO runtime/model, OBS scene tooling, Gemma endpoint, BlackHole switcher, live preview file, and whether the current shell has `OBS_WEBSOCKET_PASSWORD`.

For a repeatable non-invasive runtime status receipt, run:

```bash
python3 apps/caresight-hub/scripts/caresight_demo_preflight.py --heartbeat --json
```

The heartbeat emits `runtime-validation-receipt` JSON and keeps live actions out of scope: no iMessage send, no FaceTime call, no camera-opening probe, and no TTS playback. Treat this as a runtime health layer, not as a replacement for `npm run check`.

After any event escalation, generate a local receipt:

```bash
python3 apps/caresight-hub/scripts/care_console.py \
  escalation-receipt <event_id> \
  --format markdown
```

The receipt links the event ID to drafts, staged action requests, live/dry-run execution attempts, snapshot evidence, OBS overlay state, and local live preview evidence.

## Command Registry

The local command registry lives at:

```text
apps/caresight-hub/config/command-registry.json
```

It is an inspectable allowlist for local LLM/Hermes maneuvering. Commands that perform live actions are explicitly marked `human-review-required`.
