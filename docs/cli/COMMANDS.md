# CLI Commands

This is the curated command index. Detailed operating notes live in the category files next to this page.

## Safety Classes

| Class | Meaning |
| --- | --- |
| `agent-safe-read` | Safe for agents to run unattended when local prerequisites exist. Reads or writes bounded local receipts only; no live caregiver action. |
| `manual-operator` | Requires a human/operator because it uses local hardware, windows, services, downloads, camera feeds, or long-running processes. |
| `human-review-required` | Requires explicit human approval because it confirms/dismisses events, assigns roles, sends messages, opens FaceTime, or plays audio. |

## Category Docs

| Category | File | Use it for |
| --- | --- | --- |
| Setup and local services | [`setup.md`](setup.md) | install, model setup, Gemma/Hermes stack, fixture readiness |
| Camera and feeds | [`camera.md`](camera.md) | camera discovery/probe/view, detector feeds, local feed exposure |
| Detection loop | [`detection.md`](detection.md) | YOLO26 smoke tests, floor-stay loop, bounded live checks |
| Review and records | [`review.md`](review.md) | event inbox, review lifecycle, dashboard, receipts, appearance profile, redaction |
| Agent handoff | [`agent-handoff.md`](agent-handoff.md) | drafts, staged requests, Hermes payloads, no-send attempts |
| OBS, TTS, FaceTime | [`obs-tts-facetime.md`](obs-tts-facetime.md) | OBS overlays/scenes, TTS, live approved handoff paths |
| Validation | [`validation.md`](validation.md) | unit gates, runtime heartbeat, proof audits, policy checks |

## Safe To Run Unattended

These commands are the default agent-safe inspection set. They do not send messages, open FaceTime, play TTS, confirm/dismiss events, dispatch help, or inspect raw video as a decision-maker.

| Command | Category |
| --- | --- |
| `python apps/caresight-hub/scripts/v0_review_events.py list` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/v0_review_events.py show <event_id>` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/v0_review_events.py journal <event_id>` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/v0_review_events.py audit <event_id>` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/care_console.py dashboard` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/care_console.py review-packet <event_id> --format json` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/care_console.py blackbox-receipt <event_id> --format json` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/care_console.py alert-draft <event_id>` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile list --active-date YYYY-MM-DD` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile show <appearance_profile_id>` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile list-samples <appearance_profile_id>` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile summarize-today --active-date YYYY-MM-DD` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile describe-image <local_image_path> --bbox X1,Y1,X2,Y2` | [`review.md`](review.md) |
| `python apps/caresight-hub/scripts/care_console.py agent-draft <event_id> --purpose caregiver_summary` | [`agent-handoff.md`](agent-handoff.md) |
| `python apps/caresight-hub/scripts/care_console.py stage-action-request <event_id> --draft-id <draft_id> --action create_apple_note --destination apple_notes` | [`agent-handoff.md`](agent-handoff.md) |
| `python apps/caresight-hub/scripts/care_console.py list-action-requests <event_id>` | [`agent-handoff.md`](agent-handoff.md) |
| `python apps/caresight-hub/scripts/care_console.py agent-harness-plan <request_id> --prefer auto` | [`agent-handoff.md`](agent-handoff.md) |
| `python apps/caresight-hub/scripts/care_console.py hermes-handoff-payload <request_id>` | [`agent-handoff.md`](agent-handoff.md) |
| `python apps/caresight-hub/scripts/care_console.py record-execution-attempt <request_id> --harness hermes --kind dry_run` | [`agent-handoff.md`](agent-handoff.md) |
| `python apps/caresight-hub/scripts/care_console.py hermes-dry-run <request_id>` | [`agent-handoff.md`](agent-handoff.md) |
| `python apps/caresight-hub/scripts/care_console.py list-execution-attempts <request_id>` | [`agent-handoff.md`](agent-handoff.md) |
| `python apps/caresight-hub/scripts/care_console.py hermes-config-plan` | [`agent-handoff.md`](agent-handoff.md) |
| `python apps/caresight-hub/scripts/care_console.py model-doctor` | [`setup.md`](setup.md) |
| `./scripts/update_obs_overlay.sh --event-id <event_id>` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `python3 apps/caresight-hub/scripts/live_proof_audit.py readiness --camera-authorization not_checked` | [`validation.md`](validation.md) |
| `python3 apps/caresight-hub/scripts/live_proof_audit.py bundle <event_id>` | [`validation.md`](validation.md) |

## Human Review Required

These commands must not be run as unattended automation. They change lifecycle state, assign human context, send a live message, open FaceTime, or play local audio.

| Command | Category | Gate |
| --- | --- | --- |
| `python apps/caresight-hub/scripts/v0_review_events.py confirm <event_id> --reviewer <name> --note "<note>" --review-purpose initial_review` | [`review.md`](review.md) | Authorized human reviewer. |
| `python apps/caresight-hub/scripts/v0_review_events.py dismiss <event_id> --reviewer <name> --note "<note>" --review-purpose initial_review` | [`review.md`](review.md) | Authorized human reviewer. |
| `python apps/caresight-hub/scripts/care_console.py journal-redact <event_id> --journal-id <journal_id> --export-classification local-only` | [`review.md`](review.md) | Human export/review decision. |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile assign-role <appearance_profile_id> --role resident_primary --reviewer <name>` | [`review.md`](review.md) | Human role assignment. |
| `python3 apps/caresight-hub/scripts/caresight_live_handoff.py send-imessage <request_id> --live-approved` | [`obs-tts-facetime.md`](obs-tts-facetime.md) | Approved live target and message. |
| `python3 apps/caresight-hub/scripts/caresight_live_handoff.py facetime-if-yes <request_id> --reply-text "yes connect" --live-approved` | [`obs-tts-facetime.md`](obs-tts-facetime.md) | Explicit yes-like reply and approved FaceTime target. |
| `python3 apps/caresight-hub/scripts/caresight_live_handoff.py wait-reply-facetime-tts <request_id> --since-unix-seconds <timestamp> --live-approved --tts-audio-route blackhole` | [`obs-tts-facetime.md`](obs-tts-facetime.md) | Live reply watch, FaceTime, and approved TTS path. |
| `python3 apps/caresight-hub/scripts/caresight_tts.py --text <approved_text> --play --play-volume 6.0 --play-repeat-count 2` | [`obs-tts-facetime.md`](obs-tts-facetime.md) | Human-approved playback. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --obs-browser-feed --auto-agent-live-run --live-approved --auto-facetime-on-reply --play-tts-after-facetime` | [`obs-tts-facetime.md`](obs-tts-facetime.md) | Approved live handoff chain. |

## Manual Operator

These commands are operator-owned because they use live local resources, install dependencies, start/stop services, open windows, or run long-lived loops.

| Command | Category |
| --- | --- |
| `python3 apps/caresight-hub/scripts/caresight_install_all.py` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_install_model.py gemma-e2b` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_install_obs.py` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_setup_fixtures.py` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_gemma_start.py` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_gemma_stop.py` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_hermes_start.py --require-gemma` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_hermes_stop.py` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_stack_start.py` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_stack_stop.py` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_demo_preflight.py` | [`setup.md`](setup.md) |
| `python3 apps/caresight-hub/scripts/caresight_contacts_config.py --display-label "Primary emergency contact" --imessage <private-imessage-handle>` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `python3 apps/caresight-hub/scripts/caresight_camera_discover.py --host <camera_ip> --camera-id <camera_id> --write-config apps/caresight-hub/config/<camera_id>.local.json` | [`camera.md`](camera.md) |
| `python3 apps/caresight-hub/scripts/caresight_camera_discover.py --subnet <local_subnet_cidr> --allow-lan-scan --scan-timeout-seconds 0.08 --progress-every 32` | [`camera.md`](camera.md) |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/caresight_camera_probe.py --config apps/caresight-hub/config/<camera_id>.local.json` | [`camera.md`](camera.md) |
| `python3 apps/caresight-hub/scripts/caresight_camera_probe.py --config apps/caresight-hub/config/tapo.local.example.json --dry-run` | [`camera.md`](camera.md) |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/caresight_camera_view.py --config apps/caresight-hub/config/<camera_id>.local.json` | [`camera.md`](camera.md) |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/caresight_detector_start.py --appearance-overlay --stop-existing` | [`camera.md`](camera.md) |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/yolo26_image_smoke.py` | [`detection.md`](detection.md) |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/yolo26_webcam_smoke.py` | [`detection.md`](detection.md) |
| `python apps/caresight-hub/scripts/v0_floor_stay_live.py` | [`detection.md`](detection.md) |
| `python3 apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room_usb --no-window --max-seconds 120` | [`detection.md`](detection.md) |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --max-seconds 60 --stop-after-event` | [`detection.md`](detection.md) |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --appearance-sampling --max-seconds 600` | [`detection.md`](detection.md) |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --auto-agent-dry-run --max-seconds 600 --no-window` | [`detection.md`](detection.md) |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --debug-floor-stay --max-seconds 90 --stop-after-event --no-window` | [`detection.md`](detection.md) |
| `python3 apps/caresight-hub/scripts/v0_floor_stay_live.py --help` | [`detection.md`](detection.md) |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile derive-from-event <event_id>` | [`review.md`](review.md) |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/caresight_yolo26_appearance_review.py <image_path> --output-dir apps/caresight-hub/data/appearance-validation/annotated` | [`review.md`](review.md) |
| `python3 apps/caresight-hub/scripts/caresight_audio_route.py check` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `python3 apps/caresight-hub/scripts/caresight_tts.py --voice dakota --text "CareSight alert. Possible floor stay observed in the Living Room. Needs review."` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `./scripts/setup_obs_scene.sh --dry-run` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `./scripts/install_obs_vertical_canvas.sh` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `apps/obs-hub/tools/aitum_vertical.py status` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `apps/obs-hub/tools/aitum_vertical.py switch --scene "CareSight Hub - FaceTime Mobile Vertical" --start-virtual-camera` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `apps/obs-hub/tools/normalize_aitum_vertical_scene.py` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `./scripts/update_obs_overlay.sh --watch` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `./scripts/open_demo_terminals.sh --terminal` | [`obs-tts-facetime.md`](obs-tts-facetime.md) |
| `apps/obs-hub/tools/check_obs_live_feed.py` | [`validation.md`](validation.md) |
| `python3 apps/caresight-hub/scripts/caresight_demo_preflight.py --heartbeat --json` | [`validation.md`](validation.md) |

## Current Demo Path

For a quick operator orientation, start with:

```bash
python3 apps/caresight-hub/scripts/caresight_demo_preflight.py --heartbeat --json
./scripts/open_demo_terminals.sh --print
```

Then use [`docs/status/OPERATING_STATUS.md`](../status/OPERATING_STATUS.md) to confirm which gates are deterministic, which are runtime probes, and which still require human approval.
