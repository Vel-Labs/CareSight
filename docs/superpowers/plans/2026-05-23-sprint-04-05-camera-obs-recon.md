# CareSight Sprint 04/05 Camera And OBS Recon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Sprint 04 tracking reliability, then Sprint 05 robust explicit local/network camera support, then run a focused OBS/FaceTime/TTS troubleshooting and fix pass.

**Architecture:** Keep SQLite and contracts as source of truth. YOLO26 MLX remains the only vision lane; Tapo/RTSP/ONVIF cameras are input sources only. OBS, FaceTime, iMessage, and TTS remain downstream presentation or handoff layers with explicit human approval and audit receipts.

**Tech Stack:** Python, SQLite, YOLO26 MLX, OpenCV, RTSP over TCP, optional ONVIF Profile S metadata/probing, OBS WebSocket, local MJPEG browser feed, BlackHole/SwitchAudioSource, repo contract validation through `npm run check`.

---

## Source Facts And Boundaries

- TP-Link's current Tapo RTSP/ONVIF docs list `Tapo C210P2` and `Tapo C210` among supported models.
- Normal operation can avoid the Tapo app, but first setup still needs the app to create a dedicated camera account and, if needed, set stream quality.
- RTSP high quality uses `rtsp://<username>:<password>@<ip>:554/stream1`; standard quality uses `/stream2`.
- ONVIF uses service port `2020`; RTSP uses port `554`.
- Do not commit camera IPs, usernames, passwords, cloud account credentials, or household network details.
- Do not add cloud-provider camera integrations, ONVIF discovery, LAN scanning, or port-forwarding flows for hackathon scope.

## Workstream Declaration

**Workstream:** Sprint 04/05 camera reliability plus OBS recon.

**Files expected to touch:**
- `apps/caresight-hub/caresight/runtime/tracking/state.py`
- `apps/caresight-hub/caresight/events/floor_stay.py`
- `apps/caresight-hub/caresight/events/missing_off_camera.py`
- `apps/caresight-hub/caresight/runtime/config.py`
- `apps/caresight-hub/caresight/runtime/cameras/sources.py`
- `apps/caresight-hub/caresight/runtime/cameras/multi_camera.py`
- `apps/caresight-hub/caresight/runtime/dashboard/service.py`
- `apps/caresight-hub/caresight/runtime/demo_surface/blackbox_receipt.py`
- `apps/caresight-hub/caresight/runtime/demo_surface/review_packet.py`
- `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- `apps/caresight-hub/scripts/care_console.py`
- `apps/obs-hub/tools/*.py`
- `scripts/setup_obs_scene.sh`
- `scripts/update_obs_overlay.sh`
- `docs/cli/COMMANDS.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/camera_integration_strategy.md`
- `docs/architecture/obs_facetime_live_view.md`
- `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- `CHANGELOG.md`
- `DECISIONS.md` only when introducing new architectural policy.

**Files/directories not to touch:**
- `apps/caresight-hub/vendor/hermes-agent/**`
- `apps/caresight-hub/vendor/yolo-mlx/**` except running existing runtime commands.
- Any ignored local camera credential file except creating templates or documented local-only examples.

**Dependencies:**
- Sprint 04 can run before live Tapo cameras are available.
- Sprint 05 config/source validation can run before live cameras are available.
- Sprint 05 live Tapo validation requires local camera account, IP address, same LAN, and credentials stored outside Git.
- OBS/FaceTime/TTS recon should wait until Sprint 05 can produce stable camera metadata and either an RTSP frame or a clear blocker receipt.

**Validation plan:**
- Run targeted Python tests after each tranche.
- Run `npm run check` before closeout.
- Produce audit receipts under `docs/audits/`.
- Produce human validation docs for live camera and OBS/TTS/FaceTime checks.

---

## Phase 0: Scope Sprint 06 Out Of Hackathon Critical Path

**Decision:** Defer Sprint 06 meaningful implementation unless time remains after tracking, network camera, and OBS stability. Routine events are already represented in contracts/runtime enough for roadmap continuity, while tracking and network cameras materially improve the demo.

- [ ] Update `docs/roadmaps/CURRENT_STATE_AND_NEXT.md` to state Sprint 06 remains a future deterministic routine-demo lane, not the current hackathon blocker.
- [ ] Add a `CHANGELOG.md` note that the active execution path is Sprint 04, Sprint 05, then OBS recon.
- [ ] Do not remove existing routine-event tests or contracts.

---

## Phase 1: Sprint 04 Tracking Reliability

### Task 1: Baseline Current Tracking And Floor-Stay Behavior

**Files:**
- Read: `apps/caresight-hub/caresight/runtime/tracking/state.py`
- Read: `apps/caresight-hub/caresight/events/floor_stay.py`
- Read: `apps/caresight-hub/tests/test_tracking_state.py`
- Read: `apps/caresight-hub/tests/test_floor_stay.py`

- [ ] Run `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python -m pytest apps/caresight-hub/tests/test_tracking_state.py apps/caresight-hub/tests/test_floor_stay.py -v`.
- [ ] Record failing or passing baseline in `docs/audits/YYYY-MM-DD-sprint-04-tracking-baseline.md`.
- [ ] Confirm whether current tests already cover track churn, occlusion grace, seated-desk false positive, and dedupe.

### Task 2: Add Stage-Aware Floor-Stay Evidence

**Files:**
- Modify: `apps/caresight-hub/caresight/events/floor_stay.py`
- Modify: `apps/caresight-hub/caresight/runtime/config.py`
- Test: `apps/caresight-hub/tests/test_floor_stay.py`

- [ ] Add failing tests for `early_concern`, `prolonged_concern`, and `critical_attention` evidence using same-track dwell durations.
- [ ] Add or normalize config defaults:
  - `dwell_seconds: 30`
  - `prolonged_dwell_seconds: 90`
  - `critical_dwell_seconds: 180`
  - `occlusion_grace_seconds: 5`
  - `dedupe_window_seconds: 90`
  - `same_track_required: true`
  - `min_person_confidence: 0.35`
- [ ] Implement evidence fields without broadening event type semantics:
  - `escalation_stage`
  - `same_track_dwell_seconds`
  - `occlusion_grace_seconds`
  - `dedupe_window_seconds`
  - `policy_version: floor_stay_v1_tracking_reliability`
  - `not_claimed: ["fall_confirmed", "injury_detected", "medical_emergency"]`
- [ ] Confirm severity remains `low|medium|high`; stage lives in evidence.

### Task 3: Harden Track Churn, Occlusion, And Dedupe

**Files:**
- Modify: `apps/caresight-hub/caresight/runtime/tracking/state.py`
- Modify: `apps/caresight-hub/caresight/events/floor_stay.py`
- Test: `apps/caresight-hub/tests/test_tracking_state.py`
- Test: `apps/caresight-hub/tests/test_floor_stay.py`

- [ ] Add tests proving a different track cannot inherit dwell.
- [ ] Add tests proving short occlusion preserves dwell.
- [ ] Add tests proving long occlusion resets dwell.
- [ ] Add tests proving a repeated same-track event inside the dedupe window updates evidence or suppresses a duplicate instead of creating spam.
- [ ] Implement the smallest state-machine change needed to pass those tests.
- [ ] Confirm debug output from `--debug-floor-stay` makes the rejection reason visible without leaking private imagery.

### Task 4: Bound Missing-Off-Camera Semantics

**Files:**
- Modify: `apps/caresight-hub/caresight/events/missing_off_camera.py`
- Test: `apps/caresight-hub/tests/test_missing_off_camera.py`

- [ ] Add tests for absence windows:
  - `<2 minutes`: observe only, no event.
  - `2-5 minutes`: check-in suggested language.
  - `5-10 minutes` after recent concern: attention language.
  - `10-15 minutes` after high concern: urgent handoff language, but no emergency dispatch.
- [ ] Add tests proving weak appearance-profile support says `a tracked person` instead of role-specific copy.
- [ ] Add tests rejecting copy that says `resident is missing`, `person is in danger`, `medical emergency`, or `dispatching help`.
- [ ] Implement missing-off-camera evidence with `policy_version: missing_off_camera_v1_tracking_reliability`.

### Task 5: Contract Examples And Review Surface Wording

**Files:**
- Create: `contracts/examples/valid/possible-floor-stay.tracking-reliability.event.json`
- Create: `contracts/examples/valid/missing-off-camera.tracking-reliability.event.json`
- Create: `contracts/examples/invalid/floor-stay-emergency-dispatch.event.json`
- Create: `contracts/examples/invalid/missing-off-camera-named-identity.event.json`
- Create: `contracts/examples/invalid/floor-stay-fall-confirmed-without-human.event.json`
- Modify: `apps/caresight-hub/caresight/runtime/demo_surface/review_packet.py`
- Modify: `apps/caresight-hub/caresight/runtime/demo_surface/blackbox_receipt.py`
- Test: `apps/caresight-hub/tests/test_demo_surface.py`

- [ ] Add examples with bounded wording and explicit `not_claimed`.
- [ ] Update review packet and blackbox receipt to display `escalation_stage` when present.
- [ ] Keep caregiver copy bounded: `Same tracked person remained low in the configured Living Room floor zone long enough to require human review.`
- [ ] Run `npm run check`.

### Task 6: Sprint 04 Human Validation Pack

**Files:**
- Create: `docs/audits/YYYY-MM-DD-sprint-04-tracking-reliability.md`
- Modify: `docs/cli/COMMANDS.md`
- Modify: `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- Modify: `CHANGELOG.md`

- [ ] Include commands for deterministic tests.
- [ ] Include optional operator live command using existing images or live loop:
  - `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/v0_floor_stay_live.py --camera-id living_room --debug-floor-stay --max-seconds 90 --stop-after-event --no-window`
- [ ] Include a human validation form with checkboxes for:
  - floor-zone trigger is understandable.
  - seated/desk posture does not create a floor-stay event.
  - debug reasons are clear.
  - review packet avoids emergency/medical language.

---

## Phase 2: Sprint 05 Explicit Local And Network Camera Support

### Task 7: Define Camera Config Contract For Explicit Sources

**Files:**
- Modify: `apps/caresight-hub/caresight/runtime/cameras/sources.py`
- Modify: `apps/caresight-hub/caresight/runtime/config.py`
- Test: `apps/caresight-hub/tests/test_multi_camera_sources.py`
- Create or update: `apps/caresight-hub/config/cameras.example.json`

- [ ] Add failing tests for `webcam`, `usb`, `continuity_camera`, and `rtsp`.
- [ ] Add failing tests rejecting `ring`, `nest`, `arlo`, `wyze_cloud`, `home_assistant_cloud`, `onvif_discovery`, `lan_scan`, and any public discovery mode.
- [ ] Add failing tests rejecting credential-bearing committed example files.
- [ ] Normalize camera fields:
  - `camera_id`
  - `name`
  - `source_type`
  - `source_uri`
  - `room_id`
  - `room_label`
  - `width`
  - `height`
  - `fps`
  - `privacy.raw_video_storage`
  - `privacy.cloud_upload_default`
- [ ] Preserve single-camera v0 config compatibility.

### Task 8: Add Tapo RTSP Local-Only Setup Path

**Files:**
- Modify: `docs/architecture/camera_integration_strategy.md`
- Modify: `docs/cli/COMMANDS.md`
- Create: `apps/caresight-hub/config/tapo.local.example.json`
- Create or modify: `apps/caresight-hub/scripts/caresight_camera_probe.py`
- Test: `apps/caresight-hub/tests/test_multi_camera_sources.py`

- [ ] Document Tapo C210/C210P2 assumptions:
  - One-time app setup creates a camera account.
  - Runtime uses local RTSP directly.
  - Stream 1 is high quality; stream 2 is lower bandwidth.
  - Port 554 is RTSP; port 2020 is ONVIF.
  - Keep camera on same LAN; do not expose RTSP publicly.
- [ ] Add a probe command that accepts an ignored local config path and prints redacted health:
  - reachable: true/false
  - stream_opened: true/false
  - first_frame_received: true/false
  - width/height/fps if available
  - redacted URI only, never credentials
- [ ] Use OpenCV RTSP over TCP when possible.
- [ ] Add timeout and retry settings so a dead camera creates a health blocker instead of hanging the live loop.

### Task 9: Multi-Camera Frame Manager

**Files:**
- Create or modify: `apps/caresight-hub/caresight/runtime/cameras/multi_camera.py`
- Test: `apps/caresight-hub/tests/test_multi_camera_sources.py`

- [ ] Implement sequential round-robin source manager first.
- [ ] Ensure `MultiCameraFrame` includes:
  - `camera_id`
  - `room_id`
  - `room_label`
  - `captured_at`
  - `frame`
- [ ] Add source health objects for:
  - open failure
  - stale frames
  - auth failure hint
  - timeout
  - unsupported source type
- [ ] Ensure failed camera source creates a health blocker, not a synthetic event.

### Task 10: Preserve Camera Metadata Through Observations And Events

**Files:**
- Modify: `apps/caresight-hub/scripts/v0_floor_stay_live.py`
- Modify: `apps/caresight-hub/caresight/runtime/inference/config.py`
- Modify: `apps/caresight-hub/caresight/runtime/dashboard/service.py`
- Test: `apps/caresight-hub/tests/test_v0_floor_stay_live.py`
- Test: `apps/caresight-hub/tests/test_inference_harness.py`

- [ ] Add tests proving event from camera B cannot inherit camera A metadata.
- [ ] Add `--multi-camera --camera-id <id> --camera-id <id>` only if it does not make `v0_floor_stay_live.py` too large; otherwise create `v1_multi_camera_live.py`.
- [ ] Keep `--stop-after-event`, `--debug-floor-stay`, `--obs-browser-feed`, and existing live-handoff flags compatible.
- [ ] Ensure every persisted observation/event includes camera and room metadata.

### Task 11: Derived Narrative Receipt

**Files:**
- Modify: `apps/caresight-hub/scripts/care_console.py`
- Create or modify: `apps/caresight-hub/caresight/runtime/demo_surface/multi_camera_narrative.py`
- Test: `apps/caresight-hub/tests/test_multi_camera_narrative.py`

- [ ] Add `care_console.py narrative --event-id <event_id> --format json|markdown`.
- [ ] Build the narrative only from SQLite-derived event/observation/profile data.
- [ ] Use claim boundary: `likely_continuity_not_identity`.
- [ ] Include `not_claimed: ["named_identity", "biometric_match", "fall_confirmed", "medical_emergency"]`.
- [ ] Markdown output must be caregiver-readable and not JSON-first.

### Task 12: Live Tapo Camera Validation Receipt

**Files:**
- Create: `docs/audits/YYYY-MM-DD-tapo-rtsp-validation.md`
- Modify: `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- Modify: `CHANGELOG.md`

- [ ] Run the camera probe against local ignored config.
- [ ] If live frames open, save a redacted proof receipt with frame dimensions, stream path type (`stream1` or `stream2`), camera ID, room label, and command.
- [ ] If live frames do not open, save a blocker receipt with ping result, RTSP open result, timeout/auth/network classification, and next operator step.
- [ ] Run one bounded `--max-seconds` multi-camera live attempt after probe succeeds.
- [ ] Do not commit real camera IPs, credentials, still frames, or household room details unless explicitly sanitized.

---

## Phase 3: OBS, FaceTime, And TTS Recon/Fix

### Task 13: OBS State And Scene Recon

**Files:**
- Read/modify: `apps/obs-hub/tools/check_obs_live_feed.py`
- Read/modify: `apps/obs-hub/tools/setup_obs_scenes.py`
- Read/modify: `apps/obs-hub/tools/update_obs_event.py`
- Read/modify: `apps/obs-hub/config/overlay_layout.json`
- Create: `docs/audits/YYYY-MM-DD-obs-recon.md`

- [ ] Run OBS live-feed check against `http://127.0.0.1:8766/live.html`.
- [ ] Verify whether scenes use the detector-owned MJPEG browser feed, not stale fixture media.
- [ ] Verify mobile/FaceTime scene does not black out the feed with overlay fill.
- [ ] Verify `obs_presentation_state` includes camera cards from real SQLite/camera health.
- [ ] Record exact OBS profile, scene names, source names, browser URLs, and failure states.

### Task 14: Dynamic Scene Selection Based On Tracking And Camera Movement

**Files:**
- Modify: `apps/obs-hub/tools/update_obs_event.py`
- Modify: `apps/obs-hub/overlays/*.html`
- Modify: `apps/obs-hub/overlays/obs-overlay.js`
- Test or script: `apps/obs-hub/tools/check_obs_live_feed.py`

- [ ] Define scene-selection inputs from SQLite/presentation state:
  - active event camera ID
  - active event room label
  - escalation stage
  - recent camera health
  - handoff status
- [ ] Implement scene selection as a staged/manual OBS command, not an LLM direct action.
- [ ] Add dry-run output showing which scene/source would be selected and why.
- [ ] Ensure no raw credential or RTSP URI is written into overlay JSON.

### Task 15: FaceTime Visual Handoff Recon

**Files:**
- Modify if needed: `apps/caresight-hub/scripts/caresight_live_handoff.py`
- Modify if needed: `apps/obs-hub/tools/aitum_vertical.py`
- Modify if needed: `apps/obs-hub/tools/normalize_aitum_vertical_scene.py`
- Create: `docs/audits/YYYY-MM-DD-facetime-visual-recon.md`

- [ ] Test landscape fallback first because prior evidence says FaceTime may distort virtual-camera output.
- [ ] Test Aitum vertical only as opt-in.
- [ ] Record whether FaceTime sees OBS Virtual Camera, what aspect ratio appears, and whether the detector feed is visible.
- [ ] If FaceTime visuals remain unreliable, document the stable boundary: FaceTime for reply-gated audio/TTS, OBS local surface for visual review.

### Task 16: TTS Audio Routing Recon

**Files:**
- Modify if needed: `apps/caresight-hub/scripts/caresight_tts.py`
- Modify if needed: `apps/caresight-hub/scripts/caresight_audio_route.py`
- Modify if needed: `apps/caresight-hub/scripts/caresight_live_handoff.py`
- Create: `docs/audits/YYYY-MM-DD-tts-routing-recon.md`

- [ ] Verify generated Dakota TTS WAV from approved short alert text.
- [ ] Verify playback volume with local speakers first.
- [ ] Verify BlackHole route switch and restore behavior.
- [ ] Verify post-playback hold prevents route restoration mid-utterance.
- [ ] Persist execution-attempt rows for playback attempts.
- [ ] Record human validation: audible, calm, no overclaiming, route restored.

### Task 17: End-To-End Demo Gate

**Files:**
- Create: `docs/audits/YYYY-MM-DD-sprint-04-05-obs-demo-gate.md`
- Modify: `docs/hackathon/demo_script.md`
- Modify: `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- Modify: `CHANGELOG.md`

- [ ] Run `npm run check`.
- [ ] Run targeted tests:
  - `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python -m pytest apps/caresight-hub/tests/test_tracking_state.py apps/caresight-hub/tests/test_floor_stay.py apps/caresight-hub/tests/test_missing_off_camera.py -v`
  - `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python -m pytest apps/caresight-hub/tests/test_multi_camera_sources.py apps/caresight-hub/tests/test_multi_camera_narrative.py -v`
- [ ] Run camera probe or record blocker.
- [ ] Run OBS live-feed check or record blocker.
- [ ] Run FaceTime/TTS checks only with explicit human approval.
- [ ] Close with status labels:
  - Sprint 04 implemented / production-validated / blocked.
  - Sprint 05 implemented / live-camera-validated / blocked.
  - OBS recon fixed / partially fixed / blocked.

---

## Acceptance Summary

Sprint 04 is done when tracking reliability tests pass, floor-stay evidence is stage-aware and bounded, missing-off-camera copy avoids identity/emergency claims, and a human validation doc exists.

Sprint 05 is done when explicit camera config supports local RTSP and existing local sources, Tapo RTSP probe is robust and redacted, multi-camera metadata persists through observations/events, narrative receipts are SQLite-derived, and live camera proof or a precise blocker receipt exists.

OBS recon is done when the stable visual/audio handoff boundary is known from evidence, dynamic scene selection has a dry-run/proof path, FaceTime visual behavior is either fixed or explicitly bounded, and TTS routing has an execution receipt plus human validation.
