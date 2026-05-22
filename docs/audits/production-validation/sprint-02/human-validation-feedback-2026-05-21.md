# Sprint 02 Human Validation Feedback - 2026-05-21

## Gemma Alert Wording

Status: approved with requested context follow-up.

Approved wording:

```text
Possible floor stay observed in the Living Room. Needs review.
```

Operator feedback:

- The wording is good and bounded.
- Time relevance would add value, for example observed time or elapsed duration.
- Alert follow-up cadence should exist after an unresolved alert.
- A resolution update should be available once the situation appears resolved, including an estimated total duration.

Implementation note: keep the current wording approved for the immediate Case A validation path, then add alert-lifecycle follow-up and resolution wording as a later behavior change.

## TTS Playback

Status: approved after Dakota replay request.

Observed result:

- Audio played successfully.
- Voice was clean and understandable.
- Operator prefers the `dakota` voice.
- The phrase with double use of "possible" sounded awkward.
- TTS should use the same concise approved alert wording where practical.
- If a person asks for more information, the system should make clear the TTS is an alert/readout surface and not a conversational diagnostic feed.

Recommended next TTS text:

```text
CareSight alert. Possible floor stay observed in the Living Room. Needs review.
```

Recommended validation command:

```bash
python3 apps/caresight-hub/scripts/caresight_tts.py \
  --voice dakota \
  --text "CareSight alert. Possible floor stay observed in the Living Room. Needs review." \
  --play
```

Follow-up operator result:

```text
Dakota TTS: approved
```

## OBS / Visual Handoff

Status: scenes created, dynamic overlay update path required before FaceTime validation.

Accepted design:

- Use OBS websocket for programmatic scene/input creation.
- Use a camera/image/video source plus a local browser-source overlay.
- Avoid brittle native OBS text-layer composition.
- Keep the visual handoff calm, auditable, and non-alarmist.
- Do not expose raw model confidence in the default caregiver view.

Required local validation:

- Run `./scripts/setup_obs_scene.sh --dry-run`.
- Enable OBS websocket.
- Run `./scripts/setup_obs_scene.sh`.
- Run `./scripts/update_obs_overlay.sh --event-id <event_id>` to publish current event state.
- Confirm generated scenes show only intended CareSight feed/dashboard content.
- Confirm no private desktop, messages, contacts, browser tabs, files, or unrelated content appears.

Operator feedback:

- Scenes were created successfully.
- Current event, recent activity, and camera labels were too fixture-driven.
- A dynamic script/tool surface is needed so local Gemma/Hermes can update OBS overlay state from relevant event context.
- Event IDs should be shortened in the caregiver-facing panel because the full SQLite ID is too long for the OBS handoff UI.
- During live operation, the overlay should read from SQLite or a generated local state file automatically as events are triggered.

## Apple Contact Allowlist

Status: operator approved one real Apple contact for live testing.

Tracked contact ID:

```text
contact_emergency_primary
```

Approval:

- iMessage testing: approved.
- FaceTime testing: approved.

Live iMessage text approved:

```text
CareSight alert. Possible floor stay observed in the Living Room. Needs review.
```

FaceTime handoff remains on hold until OBS dynamic updates are validated.

Privacy boundary: the real Apple Contacts display name was provided by the operator in chat, but is intentionally not copied into Git-tracked files.
