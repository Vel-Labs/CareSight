# Agent Harness Review

Date: 2026-05-21

## Decision

Use Hermes as the first controlled harness trial for CareSight service wrappers, with OpenClaw retained as the gateway/policy fallback.

## Evidence

- Hermes documents iMessage through BlueBubbles, including webhook ingress, REST API egress, group chats, attachments, reactions, read receipts, and setup variables.
- Hermes documents self-hosting for local control, model/provider flexibility, persistent memory, and automation.
- OpenClaw documents a broad self-hosted gateway, multi-channel support, multi-agent routing, media support, a local dashboard, and iMessage pairing/allowlist/session controls.
- OpenClaw iMessage docs expose useful safety controls such as allowlists, group mention patterns, pairing checks, attachment root allowlists, and config-write disabling.

## CareSight Routing

- `send_imessage_draft` defaults to Hermes.
- `create_apple_note` defaults to Hermes as a staged local-adapter path.
- `prepare_facetime_handoff` defaults to Hermes as a handoff plan, not call execution.
- `play_tts_utterance` routes to the Holler TTS model lane.
- OpenClaw can be forced with `--prefer openclaw` for gateway fallback review.
- Urgent handoffs use an allowlisted `emergency_contact` role and can offer a text update, local screen capture by request, or FaceTime handoff by request.

## Current Implementation

- Added non-executing harness planning through `care_console.py agent-harness-plan`.
- Added `send_imessage_draft` and `prepare_facetime_handoff` as staged action request types.
- Added model-lane routing for Gemma reasoning and Holler TTS.
- Added Hermes as a pinned workspace vendor submodule at `apps/caresight-hub/vendor/hermes-agent`.
- Added safe Hermes config templates under `apps/caresight-hub/config/hermes/` for a local OpenAI-compatible Gemma endpoint.
- Added `care_console.py hermes-handoff-payload` to render the non-executing Hermes payload for staged requests.
- No OpenClaw or Hermes process is invoked by CareSight.
- No Apple Notes, iMessage, FaceTime, OBS, or TTS action is executed.

## Local Model Serving

Hermes supports custom OpenAI-compatible endpoints. CareSight's default plan is:

- serve Gemma MLX locally at `http://127.0.0.1:8080/v1`
- configure Hermes with `provider: custom`
- route validated drafts through staged `agent_action_requests`
- keep OpenRouter unset unless a human explicitly approves cloud fallback testing

## Urgent Handoff Wording

The staged urgent-handoff payload asks for caregiver direction:

- provide a text update for the journal
- request a local screen capture from the configured video feed
- request a FaceTime handoff to view the feed

The payload does not attach raw video, start FaceTime, send iMessage, run OBS, or claim an emergency.

## Remaining Gate

Before enabling a real harness:

- create local secret handling for BlueBubbles/OpenClaw credentials
- add allowlists for caregiver recipients and group chats
- add SQLite execution-attempt logs
- require human approval per staged action
- prove the harness cannot bypass CareSight forbidden-claim validation
- measure memory and latency with YOLO26, Gemma, and the selected harness running
