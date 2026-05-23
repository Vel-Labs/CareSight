# CLI Commands

This index tracks commands that are safe to run locally and explains their inputs, outputs, validation, and agent boundary.

## Agent Safety Classes

- `agent-safe-read`: agents may run without human approval.
- `human-review-required`: agents may prepare or summarize, but a human must explicitly authorize state changes.
- `manual-operator`: intended for a human because it uses live camera or local environment resources.

## YOLO26 Image Smoke

Command:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/yolo26_image_smoke.py
```

Purpose: run the CareSight-owned YOLO26 MLX inference harness against the bundled image smoke fixture.

Inputs: local YOLO26 MLX environment, `apps/caresight-hub/config/v0.local.json`, model path, room metadata, camera metadata, and image fixture.

Outputs: local result image plus terminal JSON with raw `detections`, normalized `observations`, and runtime metadata.

Validation: covered by the v0 smoke checkpoint audit and `test_inference_harness.py`; rerun before claiming model readiness on a new machine.

Agent safety: `manual-operator`.

## YOLO26 Webcam Smoke

Command:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/yolo26_webcam_smoke.py
```

Purpose: verify live webcam capture and YOLO26 MLX person labels through the CareSight-owned adapter boundary.

Inputs: local camera access, `apps/caresight-hub/config/v0.local.json`, camera metadata, room metadata, and YOLO26 MLX model.

Outputs: local preview window and terminal diagnostics.

Validation: deterministic adapter and normalization behavior is covered by `test_inference_harness.py`; live camera behavior remains manual/operator.

Agent safety: `manual-operator`.

## v0 Floor-Stay Live Loop

Command:

```bash
python apps/caresight-hub/scripts/v0_floor_stay_live.py
```

Purpose: create a local `possible_floor_stay` event after a person remains in the configured floor/low zone.

Inputs: `apps/caresight-hub/config/v0.local.json`, local camera, YOLO26 MLX model, SQLite database path.

Outputs: `event_persisted` terminal line, SQLite event row, event observation row with `track_id`, and local snapshot path.

Validation: `npm run py:check` covers deterministic event, SQLite, tracking, and snapshot behavior. Live camera behavior still needs manual verification.

Agent safety: `manual-operator`.

Configured source selection:

```bash
python3 apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room_usb --no-window --max-seconds 120
```

Purpose: select one configured local camera source from `config.cameras` while preserving `camera_id`, `source_type`, and room label in runtime config and SQLite-backed event provenance.

Supported source types: `webcam`, `usb`, `continuity_camera`, and local `rtsp`. Ring, Nest, Home Assistant, ONVIF discovery, LAN scanning, cloud-camera APIs, and credential handling remain out of scope.

Validation: `test_v0_config.py` verifies deterministic source selection and cloud/provider rejection without opening a camera.

Bounded audit run:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --max-seconds 60 --stop-after-event
```

Purpose: let an operator collect one `event_persisted` line without leaving the live loop unbounded.

`--stop-after-event` is a demo/proof flag only. Do not use it for monitoring-style runs where CareSight should continue watching after the first event.

If no floor-stay event is created before the bounded run exits, the command persists an `observation_checks` row in SQLite and prints a `no_event_persisted` JSON line with `check_id`, `frame_count`, `elapsed_seconds`, `required_dwell_seconds`, `camera_id`, and `zone_id`. Use that row and line as the machine-readable receipt for normal/non-concerning no-event proof.

The startup line reports `required_dwell_seconds`; this is the configured threshold, not an observed floor dwell.

Omit `--no-window` when the operator needs the preview overlay to position the floor/low zone.

No-send agent pipeline:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --max-seconds 600 \
  --no-window \
  --auto-agent-dry-run
```

Purpose: after each persisted possible floor-stay event, automatically update the OBS overlay, create a local Gemma alert draft, stage an allowlisted iMessage request, and run Hermes no-send preflight.

Outputs: normal `event_persisted` line plus `post_event_agent_dry_run` receipt with `event_id`, `draft_id`, `request_id`, `attempt_id`, `execution_state`, and `external_action_performed: false`.

Validation: `test_v0_floor_stay_live.py` verifies the CLI option and machine-readable receipt formatting. Runtime validation requires a live event and must still stop before live iMessage or FaceTime execution.

Agent safety: `manual-operator`. This performs local no-send automation only. It does not send iMessage, start FaceTime, play TTS, dispatch help, or expose raw video to Gemma/Hermes.

Live iMessage test:

```bash
python3 apps/caresight-hub/scripts/caresight_contacts_config.py \
  --display-label "Primary emergency contact" \
  --imessage "<private-imessage-handle>"

export CARESIGHT_CONTACT_ALLOWLIST_PATH=apps/caresight-hub/config/hermes/allowlisted-contacts.local.json

apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --max-seconds 600 \
  --no-window \
  --obs-browser-feed \
  --auto-agent-live-run \
  --live-approved
```

Purpose: after each persisted possible floor-stay event, run the same post-event chain, then send the approved text to the allowlisted emergency-contact target:

```text
CareSight alert. Possible floor stay observed in the Living Room. Needs review. Would you like to connect to CareSight?
```

Outputs: normal `event_persisted` line, a Hermes dry-run attempt receipt in SQLite, and `post_event_agent_live_run` with the staged `request_id`, live `attempt_id`, and `external_action_performed: true`.

Agent safety: `human-review-required`. This sends one live iMessage only after `--live-approved` and a private target are provided. It does not automatically start FaceTime because reply monitoring is not enabled by default.

Private contact config:

```bash
python3 apps/caresight-hub/scripts/caresight_contacts_config.py \
  --display-label "Primary emergency contact" \
  --imessage "<private-imessage-handle>" \
  --facetime "<private-facetime-handle>"
```

Purpose: create ignored `apps/caresight-hub/config/hermes/allowlisted-contacts.local.json` so live demo commands can resolve the allowlisted iMessage and FaceTime targets without putting private handles in every command line.

Validation: `test_care_console.py` verifies the generated allowlist shape.

Agent safety: `manual-operator`. The file is local and ignored by git. It stores private contact handles for explicit live tests only.

Reply-gated FaceTime handoff:

```bash
export CARESIGHT_LIVE_FACETIME_TARGET="<private-facetime-handle>"

python3 apps/caresight-hub/scripts/caresight_live_handoff.py \
  facetime-if-yes <request_id> \
  --reply-text "yes please" \
  --live-approved
```

Purpose: open FaceTime for the same allowlisted contact only when the operator-provided reply text is interpreted as yes-like.

Validation: `test_agent_assist.py` verifies yes/no reply interpretation, target redaction, and dry-run live-handoff receipts. `test_v0_floor_stay_live.py` verifies the live-run CLI option and receipt formatting.

Agent safety: `human-review-required`. This is an operator-mediated handoff. It does not start emergency dispatch, diagnose, or expose raw video to an agent. OBS Virtual Camera must be selected/configured by the operator.

Automatic reply-gated demo:

```bash
export CARESIGHT_LIVE_IMESSAGE_TARGET="<private-imessage-handle>"
export CARESIGHT_LIVE_FACETIME_TARGET="<private-facetime-handle>"

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

Purpose: send the approved text when a real event persists, watch the local Messages database for a yes-like reply from the same target, open FaceTime, wait briefly for the caregiver to answer, play the approved Dakota TTS readout, and keep monitoring until `--max-seconds` or operator stop.

Inputs: same private iMessage/FaceTime handles as the live iMessage test, `imsg` or local Messages database read access, OBS Virtual Camera already started/selected in FaceTime, and approved TTS playback.

Outputs: `post_event_agent_live_run` with reply-watch status, FaceTime attempt ID if opened, and TTS playback status if attempted.

The default live handoff does not depend on FaceTime receiving the OBS video feed. OBS remains the local operator/review surface, iMessage carries the alert and optional snapshot evidence, and FaceTime is used for the reply-gated call plus approved TTS audio. This avoids macOS FaceTime stretching or mirroring OBS/Aitum virtual-camera output during the demo.

To keep that stable default explicit:

```bash
export CARESIGHT_AITUM_VERTICAL_MODE="off"
export CARESIGHT_OBS_FACETIME_SCENE="CareSight Hub - Escalation"
export CARESIGHT_OBS_FACETIME_VIDEO_MODE="landscape"
```

The experimental Aitum portrait bridge is still available for investigation by setting `CARESIGHT_AITUM_VERTICAL_MODE=auto`, but it is not a production-validation gate for this sprint.

OBS video resolution is profile-global, not scene-local. If you need to preview phone output manually, use:

```bash
./scripts/setup_obs_scene.sh --scene "CareSight Hub - FaceTime Mobile" --video-mode portrait
```

To restore desktop output:

```bash
./scripts/setup_obs_scene.sh --scene "CareSight Hub - Dashboard" --video-mode landscape
```

`--reply-timeout-seconds` is the total reply watch window. `--no-response-escalation-seconds` controls when the one-time follow-up is sent inside that window. For example, timeout `120` and no-response escalation `90` means CareSight waits 90 seconds, sends the follow-up if there is still no reply, then watches for up to 30 more seconds.

If no caregiver reply is observed before `--no-response-escalation-seconds`, the live handoff sends one bounded follow-up iMessage with the local event snapshot attached:

```text
This is CareSight Hub escalation. We have not heard back, but there is an event that requires caregiver verification. Please see the image attached, and reply yes to see a live feed.
```

This is a no-response follow-up only. A negative reply does not trigger FaceTime or the follow-up escalation.

The attachment source is the event `evidence.snapshot_path`; if that file is unavailable, CareSight falls back to `apps/obs-hub/config/live_preview.jpg` when present. Execution receipts record `attachment_included` and a redacted attachment name, not the private local path.

Default TTS readout:

```text
This is an automated CareSight message. A possible floor stay was observed in the Living Room. Please review the live feed. CareSight will keep this handoff open briefly for review.
```

`--obs-browser-feed` serves the annotated detector feed at `http://127.0.0.1:8766/live.html`, backed by local MJPEG at `http://127.0.0.1:8766/stream.mjpg`. OBS should use the `/live.html` page as the Browser Source URL, so the caregiver sees the boxed detector view without OBS competing for the webcam. Browser-feed mode suppresses the OpenCV preview window by default; add `--show-window` only for local detector debugging.

`--obs-live-preview` still writes `apps/obs-hub/config/live_preview.jpg` as a fallback/snapshot-style local artifact. It is not the primary live video path.

`--tts-repeat-count 2` plays the approved Dakota handoff message twice after the FaceTime call is requested. The BlackHole audio route now holds the temporary route briefly after playback so the route is not restored mid-message.

Agent safety: `human-review-required`. This prefers `imsg` when installed, otherwise reads only the local Messages database for the configured contact target after the alert is sent. If macOS blocks database access, it fails closed with setup instructions; it does not bypass Full Disk Access, dispatch help, diagnose, or send raw video to an agent.

Demo preflight:

```bash
python3 apps/caresight-hub/scripts/caresight_demo_preflight.py
```

Purpose: check the local demo runway before an operator gets on the floor: SQLite path, ignored contact allowlist, YOLO runtime/model, OBS scene tooling, local demo env, live preview artifact, Gemma endpoint, BlackHole switcher, and whether `OBS_WEBSOCKET_PASSWORD` is present in the shell or `apps/caresight-hub/config/live-demo.local`.

Outputs: a skimmable readiness report and the recommended live command. Use `--json` for a machine-readable receipt.

Agent safety: `manual-operator`. The command checks local readiness only and does not send messages, place calls, play TTS, or write event state.

Escalation receipt:

```bash
python3 apps/caresight-hub/scripts/care_console.py \
  escalation-receipt <event_id> \
  --format markdown
```

Purpose: link one `event_id` to its escalation evidence: local event details, snapshot path, agent drafts, staged action requests, Hermes/live execution attempts, OBS overlay state, and local live preview evidence.

Outputs: JSON or Markdown. The receipt is read-only and local.

Validation: `test_care_console.py` verifies the receipt includes action requests and execution attempts for the event.

Agent safety: `agent-safe-read`. The command reads SQLite and local OBS evidence paths only.

Floor-stay detector diagnostics:

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

Purpose: print one `floor_stay_debug` JSON line per second showing the observed person boxes, whether each bottom-center is inside the configured floor zone, whether the box passes low-posture shape checks, and the current dwell seconds.

Use this when a live test appears not to trigger. A valid possible-floor-stay event requires a person detection that is both inside the floor zone and low-posture for the configured dwell window.

OBS live-feed verification:

```bash
apps/obs-hub/tools/check_obs_live_feed.py
```

Purpose: prove the detector-owned MJPEG server is running and OBS live-feed/browser sources are pointed at `http://127.0.0.1:8766/live.html` or its underlying stream, not a fixture image or stale local preview. In the escalation scene, the source named `CareSight Escalation Live Feed` should sit behind `CareSight Escalation Overlay`.

Run this in a second terminal after starting `v0_floor_stay_live.py --obs-browser-feed`. If it reports `detector_mjpeg_health` as blocked, the detector is not serving frames yet. If it reports an OBS source as blocked, rerun `./scripts/setup_obs_scene.sh` after confirming OBS websocket is enabled.

The desktop and mobile feed/text positions are controlled by:

```text
apps/obs-hub/config/overlay_layout.json
apps/obs-hub/config/overlay_layout.js
```

`overlay_layout.json` drives OBS source transforms; `overlay_layout.js` lets browser overlays align labels and panels with those source transforms. The FaceTime fallback scene uses a separate `CareSight FaceTime Mobile Live Feed` source plus a transparent `CareSight FaceTime Mobile Overlay` in `video=external` mode.

Optional audio route check:

```bash
python3 apps/caresight-hub/scripts/caresight_audio_route.py check
python3 apps/caresight-hub/scripts/caresight_audio_route.py install-plan
```

Purpose: verify whether `SwitchAudioSource` and `BlackHole 2ch` are available for temporarily routing Dakota TTS into FaceTime. The install plan prints the Homebrew commands for `imsg`, `switchaudio-osx`, and `blackhole-2ch`.

Agent safety: `manual-operator`. This check does not change audio devices. The `run-with-blackhole` subcommand temporarily switches default input/output to `BlackHole 2ch` only while its child command runs, then restores the prior devices.

Readiness check:

```bash
python3 apps/caresight-hub/scripts/v0_floor_stay_live.py --help
```

Purpose: verify CLI parsing and bounded proof flags without requiring OpenCV, camera access, or YOLO runtime imports.

## v0 Review Events: List

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py list
```

Purpose: show the local event inbox. Defaults to `awaiting_human_confirmation`.

Inputs: optional `--db <path>`, optional `--all`.

Outputs: human-readable event rows.

Validation: `test_v0_review_events.py` verifies default inbox filtering.

Agent safety: `agent-safe-read`.

## v0 Review Events: Show

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py show <event_id>
```

Purpose: render a deterministic human-readable event summary for a local event.

Inputs: `event_id`, optional `--db <path>`.

Outputs: event ID, status, zone, dwell, confidence, snapshot path, and blocked actions.

Validation: `test_v0_review_events.py` verifies required summary fields.

Agent safety: `agent-safe-read`.

## v0 Review Events: Confirm

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py confirm <event_id> --reviewer <name> --note "<note>"
```

Purpose: record an authorized human confirmation.

Inputs: `event_id`, required `--reviewer`, optional `--note`, optional `--db <path>`.

Outputs: updated event status, `event_reviews` row, `journal_entries` row, and report-only `agent_handoffs` row.

Validation: `test_v0_review_events.py` verifies the shared review service path, reviewer requirement, status update, review row, journal row, and handoff payload.

Agent safety: `human-review-required`.

## v0 Review Events: Dismiss

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py dismiss <event_id> --reviewer <name> --note "<note>"
```

Purpose: record an authorized human dismissal.

Inputs: `event_id`, required `--reviewer`, optional `--note`, optional `--db <path>`.

Outputs: updated event status, `event_reviews` row, `journal_entries` row, and report-only `agent_handoffs` row.

Validation: `test_v0_review_events.py` verifies the shared review service path, dismissed status, review row, journal row, and handoff payload.

Agent safety: `human-review-required`.

## v0 Review Events: Journal

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py journal <event_id>
```

Purpose: show human-readable care journal entries for an event.

Inputs: `event_id`, optional `--db <path>`.

Outputs: local journal entries in readable text.

Validation: `test_v0_review_events.py` verifies journal rendering.

Agent safety: `agent-safe-read`.

## v0 Review Service Boundary

The CLI delegates event listing, summaries, human confirm/dismiss transitions, journal reads, and SQLite audit-chain reads to `caresight.runtime.review.ReviewService`.

State changes remain `human-review-required`: an authorized human reviewer is mandatory, automation-like reviewer names are rejected, and there are no CLI commands for deletion, emergency dispatch, diagnosis, or agent-owned acknowledgement. Review mutations are persisted through SQLite review, journal, and report-only handoff rows.

## v0 Review Events: Audit

Command:

```bash
python apps/caresight-hub/scripts/v0_review_events.py audit <event_id>
```

Purpose: show a read-only SQLite blackbox chain for one event after live observation and human review.

Inputs: `event_id`, optional `--db <path>`.

Outputs: event ID, event type, status, occurred timestamp, camera, zone, snapshot path, observation row count, review row count, journal row count, report-only handoff row count, latest reviewer, latest review timestamp, and latest handoff status.

Validation: `test_v0_review_events.py` verifies audit rendering from event, observation, review, journal, and handoff rows.

Agent safety: `agent-safe-read`.

## Routine Event Policy Checks

Routine events are currently deterministic runtime policies rather than standalone CLI commands. They require:

- a person observed in the configured routine zone
- narrow configured object-label evidence
- a configured routine time window
- human review before confirmation

Validation: `test_routine_events.py` verifies medication and hydration routine events remain `awaiting_human_confirmation` and do not claim medication administration or medical hydration state.

## Care Console Dashboard

Command:

```bash
python apps/caresight-hub/scripts/care_console.py dashboard
```

Purpose: render a local JSON dashboard read model from SQLite through `ReviewService`.

Inputs: optional `--db <path>`.

Outputs: source-of-truth marker, focused-event mode when `--event-id` is used, selected event summary, separate awaiting-review backlog, live-feed boundary, current state, event timeline, concern feed, review-control mapping, journal preview, and caregiver alert draft.

Validation: `test_care_console.py` verifies the dashboard reads SQLite state, keeps review actions routed through `ReviewService`, and marks delete/dispatch as forbidden.

Agent safety: `agent-safe-read`.

## Care Console Review Packet

Command:

```bash
python apps/caresight-hub/scripts/care_console.py review-packet <event_id> --format json
```

Purpose: render a read-only human review packet from the SQLite audit chain.

Inputs: `event_id`, optional `--db <path>`, optional `--format json|markdown`, and optional `--output <path>`.

Outputs: event status, bounded headline, evidence summary, track IDs, snapshot path, review state, available human actions, blocked actions, and provenance. Markdown output is the human-facing review surface: it leads with a short plain-language summary, at-a-glance status, suggested next step, safety boundaries, and compact audit details.

Validation: `test_care_console.py` verifies JSON and Markdown review-packet output from SQLite without mutating event lifecycle state.

Agent safety: `agent-safe-read`.

## Care Console Blackbox Receipt

Command:

```bash
python apps/caresight-hub/scripts/care_console.py blackbox-receipt <event_id> --format json
```

Purpose: render a read-only blackbox receipt for a selected event's observation, human review, journal, handoff, dashboard, and alert provenance.

Inputs: `event_id`, optional `--db <path>`, optional `--format json|markdown`, and optional `--output <path>`.

Outputs: completion status, blockers for incomplete chains, counts for observations/reviews/journal/handoffs, track IDs, human review summary, derived-output checks, blocked actions, and safety boundaries. Markdown output is the human-facing proof surface: it summarizes whether the local audit trail is complete, then lists the proof chain, event details, and boundaries without requiring a caregiver to read JSON.

Validation: `test_care_console.py` verifies complete receipt output after human review and the demo-surface tests verify incomplete receipts report blockers.

Agent safety: `agent-safe-read`.

## Care Console Alert Draft

Command:

```bash
python apps/caresight-hub/scripts/care_console.py alert-draft <event_id>
```

Purpose: draft caregiver alert text with provenance from the SQLite audit chain.

Inputs: `event_id`, optional `--db <path>`.

Outputs: draft text, text-to-FaceTime channel sequence, source fields, and forbidden-action boundaries.

Validation: `test_care_console.py` verifies alert drafts include event provenance and remain report-only.

Agent safety: `agent-safe-read`.

## Care Console Agent Draft

Command:

```bash
python apps/caresight-hub/scripts/care_console.py agent-draft <event_id> --purpose caregiver_summary
```

Purpose: create and persist a fake-provider or local Gemma agent draft from the SQLite audit chain.

Inputs: `event_id`, optional `--db <path>`, optional `--purpose caregiver_summary|alert_draft|apple_notes_entry|handoff_packet|audit_summary`, optional `--provider fake|gemma`, optional `--gemma-base-url <url>`, and optional `--gemma-model <model-or-local-path>`.

Outputs: `agent-draft` JSON with provider `fake` or `gemma_mlx`, source-of-truth marker, validation status, draft text, safety boundaries, provenance, and any blocked claim reasons.

Validation: `test_agent_assist.py` and `test_care_console.py` verify validated drafts and blocked drafts are persisted in SQLite. The Gemma provider sends compact SQLite-derived context only; it does not send raw video or image bytes.

Agent safety: `agent-safe-read`. The Gemma provider calls the local endpoint only and does not execute external actions.

## Care Console Stage Action Request

Command:

```bash
python apps/caresight-hub/scripts/care_console.py stage-action-request <event_id> --draft-id <draft_id> --action create_apple_note --destination apple_notes
```

Purpose: stage a local action request from a validated agent draft without executing it.

Inputs: `event_id`, required `--draft-id`, required `--action send_caregiver_message|send_imessage_draft|create_apple_note|prepare_handoff_packet|prepare_facetime_handoff|play_tts_utterance`, optional `--destination caregiver_console|imessage|apple_notes|facetime|local_tts|handoff_packet`, optional `--escalation-level routine|attention|urgent_handoff`, optional `--recipient-role caregiver|emergency_contact`, repeatable `--allowed-contact-id contact_<id>`, optional `--allowlist-config <path>` for redacted contact IDs, repeatable `--response-option acknowledge_text_update|request_local_screen_capture|request_facetime_handoff|dismiss_after_review`, and optional `--db <path>`.

Outputs: `agent-action-request` JSON with `stage: staged`, `execution_state: not_executed`, `requires_human_approval: true`, source draft, destination, escalation level, recipient role, allowlisted contact IDs, response options, safety boundaries, and provenance.

Validation: `test_agent_assist.py` verifies staged requests stay local, blocked drafts cannot stage action requests, and unknown iMessage/FaceTime contact IDs are rejected when a contact allowlist is configured. `test_care_console.py` verifies CLI staging persists only local SQLite rows and blocks unconfigured contact IDs.

Agent safety: `agent-safe-read`. Agents may stage and list action requests, but Sprint 02 provides no command that executes the requested action. iMessage and FaceTime destinations require contact IDs from the configured redacted allowlist.

## Care Console Agent Harness Plan

Command:

```bash
python apps/caresight-hub/scripts/care_console.py agent-harness-plan <request_id> --prefer auto
```

Purpose: render a non-executing OpenClaw/Hermes harness plan for one staged action request.

Inputs: `request_id`, optional `--db <path>`, and optional `--prefer auto|hermes|openclaw`.

Outputs: selected harness, source draft, action request, model lane, routing metadata, and safety boundaries.

Validation: `test_agent_assist.py` and `test_care_console.py` verify iMessage defaults to the Hermes harness plan, TTS routes to the Holler model lane, and the command never performs external execution.

Agent safety: `agent-safe-read`. This command plans routing only; it does not send iMessage, append Apple Notes, open FaceTime, invoke TTS, or call OpenClaw/Hermes.

## Care Console Hermes Handoff Payload

Command:

```bash
python apps/caresight-hub/scripts/care_console.py hermes-handoff-payload <request_id>
```

Purpose: render the non-executing Hermes payload for a staged action request.

Inputs: `request_id` and optional `--db <path>`.

Outputs: selected destination, recipient role, allowlisted contact IDs, escalation level, caregiver-facing message text, response options, media options, payload provenance, and safety boundaries.

Validation: `test_agent_assist.py` and `test_care_console.py` verify urgent iMessage handoffs offer a local screen capture or FaceTime handoff by request only, remain `payload_only`, and never include raw video execution.

Agent safety: `agent-safe-read`. This command does not send iMessage, append Apple Notes, open FaceTime, invoke TTS, attach screenshots, expose raw video, or call Hermes.

## Care Console Record Execution Attempt

Command:

```bash
python apps/caresight-hub/scripts/care_console.py record-execution-attempt <request_id> --harness hermes --kind dry_run
```

Purpose: persist a local dry-run execution-attempt row for a staged action request and its Hermes handoff payload.

Inputs: `request_id`, optional `--db <path>`, optional `--harness hermes`, and optional `--kind dry_run`.

Outputs: `agent-execution-attempt` JSON with request ID, event ID, harness, execution state, result, payload snapshot, safety boundaries, and provenance.

Validation: `test_agent_assist.py`, `test_sqlite_store.py`, and `test_care_console.py` verify dry-run attempts are persisted in SQLite, keep `external_action_performed: false`, and leave the source action request in `not_executed`.

Agent safety: `agent-safe-read`. This command records a no-send attempt receipt only; it does not send iMessage, append Apple Notes, open FaceTime, invoke TTS, attach screenshots, expose raw video, or call Hermes.

## Care Console Hermes Dry Run

Command:

```bash
python apps/caresight-hub/scripts/care_console.py hermes-dry-run <request_id>
```

Purpose: invoke the vendored Hermes no-send message-directory preflight for one staged request, then persist the attempt as a local execution-attempt receipt.

Inputs: `request_id`, optional `--db <path>`, and optional `--vendor-path <path>`.

Outputs: `agent-execution-attempt` JSON with `harness: hermes`, `attempt_kind: dry_run`, `external_action_performed: false`, the original handoff payload, and `hermes_preflight` status. If Hermes dependencies or gateway config are unavailable, the attempt is still logged with `execution_state: blocked`.

Validation: `test_agent_assist.py` and `test_care_console.py` verify the command records a no-send attempt and does not mutate the staged action request into an executed state.

Agent safety: `agent-safe-read`. This command only calls Hermes `send_message(action='list')`; it does not send iMessage, append Apple Notes, open FaceTime, invoke TTS, attach screenshots, expose raw video, or execute Hermes delivery.

## Care Console List Execution Attempts

Command:

```bash
python apps/caresight-hub/scripts/care_console.py list-execution-attempts <request_id>
```

Purpose: list local execution-attempt rows for one staged action request.

Inputs: `request_id` and optional `--db <path>`.

Outputs: JSON array of `agent-execution-attempt` records.

Validation: `test_care_console.py` verifies list output after recording a dry-run attempt.

Agent safety: `agent-safe-read`.

## Care Console Hermes Config Plan

Command:

```bash
python apps/caresight-hub/scripts/care_console.py hermes-config-plan
```

Purpose: render the workspace-local Hermes vendor/config plan and the local model serving route.

Inputs: optional `--db <path>` for CLI consistency. The command does not read event rows.

Outputs: Hermes vendor submodule path and pinned tag, safe config template paths, local OpenAI-compatible `base_url`, Gemma/Holler model lanes, and the cloud-router boundary.

Validation: `test_agent_assist.py` and `test_care_console.py` verify the plan uses a local endpoint, keeps OpenRouter optional, and reports that no global Hermes install or external execution was performed.

Agent safety: `agent-safe-read`. This command does not install Hermes, write `~/.hermes`, start a model server, call OpenRouter, connect BlueBubbles, send iMessage, append Apple Notes, open FaceTime, or invoke TTS.

## CareSight Gemma Start

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_gemma_start.py
```

Purpose: start the local Gemma 4 E2B MLX endpoint through `mlx-vlm.server` with an OpenAI-compatible `/v1/chat/completions` route.

Inputs: ignored local runtime venv at `apps/caresight-hub/.venv`, local Gemma model files under `apps/caresight-hub/models/reasoning/gemma/`, and optional host/port/model arguments.

Outputs: local server process, PID file, log file, and terminal readiness line with `base_url`.

Validation: the script performs a bounded local chat-completions readiness request before reporting `gemma_started`.

Agent safety: `manual-operator`. This starts a local model server only; it does not send messages, call FaceTime, invoke Hermes delivery, inspect raw video, or use cloud fallback.

## CareSight Install All

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_install_all.py
```

Purpose: install local CareSight prerequisites: runtime venv, default local models, and OBS.

Inputs: network access for package/model/app download and local disk space for ignored model assets.

Outputs: ignored local runtime and model files under `apps/caresight-hub/.venv` and `apps/caresight-hub/models/`.

Validation: rerun `npm run check`, then `python3 apps/caresight-hub/scripts/caresight_stack_start.py`.

Agent safety: `manual-operator`. This downloads/install local dependencies; it does not execute live caregiver actions.

## CareSight Install Model

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_install_model.py gemma-e2b
```

Purpose: install one ignored local model from Hugging Face.

Inputs: model key `gemma-e2b|gemma-e4b|holler-6bit|holler`, Hugging Face CLI, network access, and local disk space.

Outputs: ignored local model folder under `apps/caresight-hub/models/`.

Validation: for Gemma, start the stack; for TTS, run `caresight_tts.py` without `--play`.

Agent safety: `manual-operator`.

## CareSight Install OBS

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_install_obs.py
```

Purpose: install or verify OBS for local visual handoff.

Inputs: `/Applications/OBS.app` or Homebrew cask install capability.

Outputs: OBS app installed locally or a manual install prompt.

Validation: `python3 apps/caresight-hub/scripts/caresight_install_obs.py --check-only`.

Agent safety: `manual-operator`.

## CareSight Setup Fixtures

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_setup_fixtures.py
```

Purpose: build local fixture/readiness outputs after install.

Inputs: local runtime/model prerequisites.

Outputs: validation pass, stack start/stop readiness, and local TTS generation.

Validation: script exits successfully.

Agent safety: `manual-operator`. It performs no live external caregiver actions.

## CareSight Gemma Stop

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_gemma_stop.py
```

Purpose: stop the local Gemma server started by `caresight_gemma_start.py`.

Inputs: PID file at `apps/caresight-hub/data/runtime/gemma-server.pid` unless overridden.

Outputs: terminal stop status and removed stale/current PID file.

Validation: covered by operator use and the PID-file boundary; no external action is performed.

Agent safety: `manual-operator`.

## CareSight TTS

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py --voice dakota --text "CareSight alert. Possible floor stay observed in the Living Room. Needs review."
```

Purpose: generate local Holler TTS audio from approved bounded text.

Inputs: ignored local runtime venv, Holler model files under `apps/caresight-hub/models/tts/holler/`, utterance text, optional voice, and optional output directory.

Outputs: local audio file under `apps/caresight-hub/data/tts/` by default.

Validation: local generation succeeds. Operator feedback on 2026-05-21 confirmed playback functionally works and sounds clean, with `dakota` preferred for the final validation pass. Playback is not part of default validation.

Agent safety: `manual-operator`. The default command generates audio only. `--play` requires explicit human approval because it plays local audio.

## CareSight OBS Scene Setup

Command:

```bash
./scripts/setup_obs_scene.sh --dry-run
```

Purpose: create or inspect the local CareSight OBS scene package for caregiver-facing visual handoff demos.

Inputs: OBS Studio 28 or newer, optional `OBS_WEBSOCKET_HOST`, optional `OBS_WEBSOCKET_PORT`, optional `OBS_WEBSOCKET_PASSWORD`, optional `CARESIGHT_OBS_SAMPLE_IMAGE`, and local files under `apps/obs-hub/`.

Outputs: a repo-local `.venv-obs/`, validated scene plan, and when OBS websocket is enabled, the scenes `CareSight Hub - Dashboard`, `CareSight Hub - Escalation`, `CareSight Camera - Living Room`, `CareSight Camera - Kitchen`, `CareSight Camera - Hallway`, and `CareSight Camera - Bedroom`.

Validation: `apps/obs-hub/tools/setup_obs_scenes.py --dry-run` validates JSON config and prints planned scenes without connecting to OBS. Live OBS setup requires the operator to enable OBS websocket and confirm the scene shows only intended CareSight content.

Agent safety: `manual-operator`. The setup can create local OBS scenes, but it must not start FaceTime, start OBS Virtual Camera for a live handoff, capture private desktop content, send raw video, or perform caregiver messaging without human approval.

## CareSight OBS Aitum Vertical Canvas

Install helper:

```bash
./scripts/install_obs_vertical_canvas.sh
```

Purpose: download the latest macOS universal installer for the optional Aitum Vertical Canvas OBS plugin without committing plugin binaries.

Inputs: internet access to GitHub releases and local write access to ignored `apps/obs-hub/vendor/`.

Outputs: `apps/obs-hub/vendor/aitum/vertical-canvas-macos-universal.pkg`.

Validation: install the package, restart OBS, confirm the Vertical dock appears, and run:

```bash
apps/obs-hub/tools/aitum_vertical.py status
```

If status reports `No vendor was found by that name`, restart OBS. The plugin can be installed and visible before its websocket vendor API is registered in the current OBS process.

Switch the vertical canvas and start the Aitum vertical virtual camera:

```bash
apps/obs-hub/tools/aitum_vertical.py switch \
  --scene "CareSight Hub - FaceTime Mobile Vertical" \
  --start-virtual-camera
```

Normalize the CareSight vertical scene after manual OBS resizing:

```bash
apps/obs-hub/tools/normalize_aitum_vertical_scene.py
```

Purpose: reset the Aitum FaceTime scene to a portrait `1080x1920` canvas with a separate 16:9 live detector browser source under a full-canvas transparent overlay. This clears stale manual crops/scales that can make FaceTime look stretched or too small.

Validation: run `apps/obs-hub/tools/normalize_aitum_vertical_scene.py --dry-run` to inspect the planned geometry, then run `apps/obs-hub/tools/aitum_vertical.py status` to confirm the vertical scene and virtual camera are active.

Agent safety: `manual-operator`. This may start the Aitum vertical virtual camera, so it belongs only in the operator-approved FaceTime handoff path. It does not send messages, open FaceTime, play TTS, or change event lifecycle state.

Current limitation: Aitum's websocket vendor API supports vertical scene switching/status/virtual-camera control. Creating or editing vertical scenes still requires the Aitum Vertical dock UI.

## CareSight OBS Overlay Update

Command:

```bash
./scripts/update_obs_overlay.sh --event-id <event_id>
```

Purpose: refresh the local browser-overlay state file from SQLite so OBS scenes show current event and recent activity context without rebuilding OBS scenes.

Inputs: optional `--db <path>`, optional `--event-id <event_id>`, optional `--sample`, optional `--dry-run`, optional `--watch`, optional `--interval-seconds <seconds>`, and local files under `apps/obs-hub/config/`.

Outputs: `apps/obs-hub/config/current_event.json` and `apps/obs-hub/config/current_event.js` by default. Browser overlays prefer the JavaScript state file because OBS Browser Source can load local scripts more reliably than JSON fetches from `file://` URLs.

The overlay state includes a richer presentation model, not just the event row:

- `current_event`: event label, room, review state, display ID, and suggested next step.
- `alert_feed`: lifecycle milestones from SQLite receipts, including event creation, Gemma draft readiness, staged action request, Hermes preflight, iMessage send, no-response follow-up, and FaceTime handoff when present.
- `camera_cards`: active/configured/not-configured camera cards for the desktop right rail.
- `handoff_status`: current bounded handoff phase for the event.

Validation: `./scripts/update_obs_overlay.sh --sample --dry-run` prints bounded fixture overlay JSON. `./scripts/update_obs_overlay.sh --event-id <event_id> --dry-run` prints SQLite-derived overlay JSON without writing. The tool rejects unsafe display wording such as detected-fall or dispatch language.

Watch mode:

```bash
./scripts/update_obs_overlay.sh --watch
```

Watch mode follows the latest SQLite event and refreshes the OBS overlay state at the configured interval. It is the preferred operator command during live testing because new events appear in OBS without manually rerunning the update command.

Agent safety: `agent-safe-read` for one-shot updates and `manual-operator` for watch mode. The command reads SQLite and writes local overlay state only; it does not create OBS scenes, start virtual camera, start FaceTime, send messages, expose raw video, or execute Hermes delivery.

## CareSight Hermes Start

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_hermes_start.py --require-gemma
```

Purpose: verify the vendored Hermes harness is ready for CareSight no-send dry-run use.

Inputs: vendored Hermes path, local config template, optional running Gemma endpoint, and ignored local runtime data directory.

Outputs: `apps/caresight-hub/data/runtime/hermes-ready.json` readiness marker and terminal status.

Validation: imports the vendored `send_message` tool and runs only `send_message(action="list")`; with `--require-gemma`, also verifies the local Gemma endpoint responds.

Agent safety: `manual-operator`. This does not send iMessage, write Apple Notes, start FaceTime, invoke TTS playback, attach screenshots, expose raw video, or execute Hermes delivery.

## CareSight Hermes Stop

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_hermes_stop.py
```

Purpose: clear the local Hermes readiness marker.

Inputs: readiness marker path.

Outputs: terminal stop status.

Validation: local marker removal only.

Agent safety: `manual-operator`.

## CareSight Stack Start

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_stack_start.py
```

Purpose: bring the local CareSight test stack online in dependency order.

Inputs: local Gemma model/runtime and vendored Hermes harness.

Outputs: running Gemma endpoint plus Hermes readiness marker.

Validation: starts Gemma with a chat-completions pulse check, then verifies Hermes with `--require-gemma`.

Agent safety: `manual-operator`. This starts/verifies local services only; it does not execute live caregiver actions.

## CareSight Demo Terminal Launcher

Command:

```bash
./scripts/open_demo_terminals.sh
```

Purpose: open a named macOS Terminal tab set for the live demo from one command.

Use explicit modes:

```bash
./scripts/open_demo_terminals.sh --terminal
./scripts/open_demo_terminals.sh --tabs
./scripts/open_demo_terminals.sh --windows
./scripts/open_demo_terminals.sh --print
```

`--tabs` is the default and opens named macOS Terminal tabs to keep the demo surface compact. `--windows` and `--terminal` open separate Terminal windows as a fallback if macOS UI automation blocks tab creation. `--print` prints the same names and commands for manual use in VS Code integrated terminals or any other terminal app. The script does not automate VS Code tabs because that requires brittle UI automation and can unexpectedly focus/open VS Code windows.

Tabs:

- `CareSight Stack`: starts Gemma/Hermes readiness.
- `OBS Overlay Watch`: keeps `current_event.js/json` refreshed from SQLite.
- `OBS Feed Check`: runs the live-feed/OBS sanity check once and leaves a shell open.
- `Live Detector + Handoff`: waits for Enter before starting the camera, approved iMessage, reply-gated FaceTime, and TTS path.
- `CareSight Status Board`: renders a clean status dashboard and curated event feed from local status files and `current_event.json`.

Inputs: macOS Terminal, local `apps/caresight-hub/config/live-demo.local` when present, and the same runtime prerequisites as the individual commands.

Validation: `bash -n scripts/open_demo_terminals.sh` and `bash -n scripts/demo_status_dashboard.sh`.

Agent safety: `manual-operator`. The launcher opens the live detector terminal but pauses before executing the live caregiver flow. macOS may ask for Automation/Accessibility permission when `--tabs` is used.

The launcher spaces tab startup by about one second. The OBS/feed check waits and retries while Terminal 4 is still waiting to start the detector, so the status board should show `Waiting` instead of immediately marking the feed check blocked.

During the live detector run, the post-event caregiver chain runs in a background worker unless `--auto-agent-fail-closed` is set. This keeps the OBS browser feed moving while CareSight waits for a reply, sends the optional no-response follow-up, opens FaceTime, or plays TTS. If another event is persisted while a live caregiver chain is still running, the detector logs `post_event_agent_live_run_skipped` instead of sending duplicate caregiver messages.

## CareSight Stack Stop

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_stack_stop.py
```

Purpose: stop the local CareSight test stack.

Inputs: local runtime PID/marker files.

Outputs: cleared Hermes readiness marker and stopped Gemma process if running.

Validation: local stop commands only.

Agent safety: `manual-operator`.

## Care Console List Action Requests

Command:

```bash
python apps/caresight-hub/scripts/care_console.py list-action-requests <event_id>
```

Purpose: list staged local action requests for one event.

Inputs: `event_id` and optional `--db <path>`.

Outputs: JSON array of staged `agent-action-request` records.

Validation: `test_care_console.py` verifies list output after staging.

Agent safety: `agent-safe-read`.

## Live Proof Audit Readiness

Command:

```bash
python3 apps/caresight-hub/scripts/live_proof_audit.py readiness --camera-authorization not_checked
```

Purpose: report whether the local config and YOLO26 MLX model path are ready for live proof collection, and surface camera authorization as an explicit readiness gate.

Inputs: optional `--config <path>`, optional `--model <path>`, optional `--db <path>`, and `--camera-authorization granted|blocked|not_checked`.

Outputs: JSON readiness report with Python/environment, model, config, SQLite path, camera authorization, blockers, and safety boundaries.

Validation: `test_live_proof_audit.py` verifies that `camera_authorization=blocked` yields `camera_authorization_blocked` without requiring camera access.

Agent safety: `agent-safe-read`. Agents may report readiness and blockers, but camera permission remains an operator action.

## Live Proof Audit Bundle

Command:

```bash
python3 apps/caresight-hub/scripts/live_proof_audit.py bundle <event_id>
```

Purpose: emit a read-only local audit bundle after an operator supplies a fresh `event_id` from a real `event_persisted` line.

Inputs: fresh `event_id`, optional `--db <path>`, optional `--max-event-age-minutes <minutes>`, and optional `--output <path>` for a local JSON report artifact.

Outputs: JSON bundle with SQLite-backed event, observation `track_id`, review, journal, report-only handoff, derived dashboard provenance, derived caregiver alert provenance, completion checks, and blockers. Missing review, journal, handoff, track ID, or stale event age yields `status: not_complete`.

Validation: `test_live_proof_audit.py` seeds SQLite rows and verifies complete provenance, missing downstream rows, stale event IDs, and CLI help.

Agent safety: `agent-safe-read`. The command must not create events, confirm, dismiss, dispatch, diagnose, delete, or become reviewer of record. Dashboard and alert data remain derived output, not canonical truth.

## Agent Policy Checks

Agent policy is enforced by runtime helpers rather than a standalone CLI command.

Allowed actions are summary, caregiver-message draft, journal-note draft, and handoff audit. Forbidden actions are event confirmation, dismissal, deletion, emergency dispatch, diagnosis, medication-taken confirmation, and raw-video inspection as decision-maker.

Validation: `test_agent_policy.py` verifies allowed actions require purpose and provenance, and forbidden actions raise deterministic policy errors.
