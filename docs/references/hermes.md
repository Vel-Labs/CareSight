# Hermes Reference

## Role in CareSight

Hermes can act as the first controlled service-wrapper trial for staged CareSight action requests.

## Possible CareSight Uses

- iMessage drafts through BlueBubbles.
- Apple Notes handoff through a local adapter after human approval.
- FaceTime handoff planning, not autonomous call start.
- TTS script routing after validation.

## Current Review

Lean Hermes for the first harness trial because the public docs show a direct BlueBubbles iMessage route, broad integrations, and self-hosting support. Keep OpenClaw available as the stronger gateway/policy fallback because its docs expose explicit iMessage pairing, session isolation, and allowlist controls.

## Workspace Setup

Hermes is vendored at `apps/caresight-hub/vendor/hermes-agent` and pinned to `v2026.5.16`.

CareSight config templates live under `apps/caresight-hub/config/hermes/`. They are safe repo templates only; they do not install Hermes globally, write `~/.hermes`, or configure live BlueBubbles credentials.

## Model Routing

The default route is Hermes `provider: custom` plus `base_url: http://127.0.0.1:8080/v1`, pointed at a local OpenAI-compatible server for the Gemma MLX reasoning lane.

OpenRouter is not required for this path. Treat OpenRouter as an explicit cloud fallback only, because care context may leave the local machine.

## Handoff Payloads

`care_console.py hermes-handoff-payload <request_id>` renders the message Hermes would receive for a staged request. For urgent handoffs, the payload targets an allowlisted `emergency_contact` and offers bounded options:

- text update for the journal
- local screen capture by human request
- FaceTime handoff by human request

The payload remains `payload_only`; it does not send iMessage, attach screenshots, start FaceTime, run OBS, or expose raw video to Hermes.

## Dry-Run Status

`care_console.py hermes-dry-run <request_id>` invokes the vendored Hermes no-send `send_message(action='list')` preflight and records the result in SQLite as an execution-attempt receipt.

Current local status: the no-send preflight works when run through the existing project-local YOLO MLX venv because that interpreter has `yaml` available. The persisted CareSight receipt redacts the raw Hermes target directory because that directory can include non-CareSight channels and is broader than the CareSight contact allowlist.

## Local readiness script

Use the CareSight wrapper to verify Hermes readiness without live execution:

```bash
python3 apps/caresight-hub/scripts/caresight_hermes_start.py --require-gemma
```

This is not a live send/call daemon. It verifies the vendored Hermes tool import, config template, local Gemma endpoint when requested, and no-send `send_message(action='list')` preflight. It writes an ignored local readiness marker at `apps/caresight-hub/data/runtime/hermes-ready.json`.

Clear the marker:

```bash
python3 apps/caresight-hub/scripts/caresight_hermes_stop.py
```

## Security Cautions

- Treat BlueBubbles credentials as local secrets.
- Do not allow Hermes to inspect raw video or snapshots as decision-maker.
- Do not allow Hermes to send iMessage, append Notes, or open FaceTime without a staged CareSight action request and human approval.
- Log every attempted harness handoff back to SQLite before execution exists.

## Sources

- [Hermes Agent Self-Hosting](https://hermes-agent.ai/self-hosting)
- [Hermes iMessage Integration](https://hermes-agent.ai/integrations/imessage)
- [Hermes BlueBubbles Docs](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/messaging/bluebubbles.md)
