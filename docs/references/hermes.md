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

## Security Cautions

- Treat BlueBubbles credentials as local secrets.
- Do not allow Hermes to inspect raw video or snapshots as decision-maker.
- Do not allow Hermes to send iMessage, append Notes, or open FaceTime without a staged CareSight action request and human approval.
- Log every attempted harness handoff back to SQLite before execution exists.

## Sources

- [Hermes Agent Self-Hosting](https://hermes-agent.ai/self-hosting)
- [Hermes iMessage Integration](https://hermes-agent.ai/integrations/imessage)
- [Hermes BlueBubbles Docs](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/messaging/bluebubbles.md)
