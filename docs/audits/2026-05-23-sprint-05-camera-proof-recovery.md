# Sprint 05 Camera Proof Recovery

Date: 2026-05-23

Scope: proof-or-blocker recovery receipt for explicit local/network camera support. This receipt does not attempt unauthorized access, network scanning, credential guessing, or live camera probing.

## Source-Backed Camera Assumptions

Sources checked:

- TP-Link Tapo RTSP/ONVIF FAQ: `https://www.tp-link.com/us/support/faq/4465/`
- Tapo RTSP setup FAQ: `https://www.tapo.com/us/faq/34/`

Relevant assumptions for CareSight:

- Tapo C210/C210P2 class cameras are documented in the RTSP/ONVIF support path.
- RTSP/ONVIF use requires a camera account created in the Tapo app; this is separate from the cloud account login.
- RTSP stream paths use `stream1` and `stream2`; RTSP port is `554`.
- ONVIF service port is documented as `2020`.
- CareSight should keep cameras on a trusted local network and must not expose RTSP publicly.

## Deterministic Local Probe

Command:

```bash
python3 apps/caresight-hub/scripts/caresight_camera_probe.py \
  --config apps/caresight-hub/config/tapo.local.example.json \
  --dry-run
```

Result:

```json
{
  "blocker": null,
  "camera_id": "tapo_living_room",
  "first_frame_received": "not_attempted",
  "fps": null,
  "height": null,
  "reachable": "not_attempted",
  "redacted_uri": "rtsp://***:***@192.0.2.55:554/stream1",
  "room_id": "living_room",
  "room_label": "Living Room",
  "schema": "camera-probe-receipt",
  "source_type": "rtsp",
  "stream_opened": "not_attempted",
  "width": null
}
```

Assessment: deterministic dry-run proof passes and preserves redaction, but it is not live camera proof. The example uses documentation-safe placeholder IP space and intentionally does not open a stream.

## Live Proof Gate

Live Tapo or RTSP proof requires all of these operator-owned inputs:

- ignored local config copied from `apps/caresight-hub/config/tapo.local.example.json`
- owner-authorized camera account username and password
- same-LAN camera IP address
- operator consent to open the local RTSP stream

Live command:

```bash
python3 apps/caresight-hub/scripts/caresight_camera_probe.py \
  --config apps/caresight-hub/config/tapo.local.json
```

Acceptable live receipt outcomes:

- `reachable=true`, `stream_opened=true`, `first_frame_received=true`, with width/height/FPS present and URI redacted.
- A precise blocker such as `auth_failed`, `timeout`, `stream_open_failed`, `first_frame_timeout`, or `config_missing`, with no credentials printed.

## Narrative Output Gate

`care_console.py narrative <event_id> --format markdown` is valid only after there is a SQLite event or frame context with preserved camera metadata. The claim boundary must remain `likely_continuity_not_identity`; a camera-health failure must not synthesize a `possible_floor_stay` or missing-off-camera event.

## Boundary

No Ring/Nest integration, ONVIF discovery, LAN scan, port forwarding, cloud camera API, credential-bearing committed file, raw frame commit, FaceTime call, iMessage, TTS playback, event confirmation, event dismissal, or emergency dispatch was performed.
