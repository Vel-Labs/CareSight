# Sprint 05 — Multi-Camera Narrative Proof

## Goal

Support a stronger local proof story:

```text
person likely observed in Kitchen
  -> likely same daily appearance profile later observed in Living Room
  -> possible floor-stay event occurs in Living Room
  -> caregiver sees room-by-room timeline
```

The goal is not full surveillance. The goal is bounded, local, auditable continuity across two explicitly configured local sources.

## Product value

A family caregiver often cares about movement between spaces: kitchen, hallway, living room, bedroom, medication station, pet bowl, exterior door. Multi-camera narrative lets CareSight explain “last seen” and “what happened next” without depending on cloud cameras.

## Non-goals

- No Ring/Nest adapters.
- No cloud camera APIs.
- No ONVIF discovery in this sprint.
- No LAN scanning.
- No credential harvesting.
- No public OBS WebSocket exposure.
- No raw video upload.
- No biometric cross-camera identity.

## Source policy

Allowed sources:

```text
webcam
usb
continuity_camera
local rtsp with explicit URI
```

Disallowed in this sprint:

```text
ring
nest
arlo
wyze cloud
home assistant cloud camera
onvif discovery
lan scan
public rtsp discovery
cloud raw video
```

## Config shape

Extend or normalize camera config to support explicit multi-source list:

```json
{
  "cameras": [
    {
      "camera_id": "kitchen_counter",
      "name": "Kitchen Counter Camera",
      "source_type": "webcam",
      "source_uri": 0,
      "room_id": "kitchen",
      "room_label": "Kitchen",
      "width": 1280,
      "height": 720,
      "fps": 15,
      "privacy": {
        "raw_video_storage": "disabled",
        "cloud_upload_default": false
      }
    },
    {
      "camera_id": "living_room",
      "name": "Living Room Camera",
      "source_type": "rtsp",
      "source_uri": "rtsp://192.168.1.50/local-only-stream",
      "room_id": "living_room",
      "room_label": "Living Room",
      "width": 1280,
      "height": 720,
      "fps": 15,
      "privacy": {
        "raw_video_storage": "disabled",
        "cloud_upload_default": false
      }
    }
  ],
  "multi_camera": {
    "enabled": true,
    "mode": "explicit_config_only",
    "round_robin_interval_ms": 100,
    "max_active_sources": 2,
    "forbid_discovery": true,
    "forbid_cloud_providers": true
  }
}
```

If current config structure uses a single `camera`, preserve backward compatibility. Do not break v0 commands.

## Runtime approach

For hackathon reliability, choose the simplest stable runtime:

### Option A — Sequential round-robin

One process, one model, two explicit sources, process frames from each source in turn.

Pros:

- simpler resource footprint
- avoids duplicate model loads
- easier audit

Cons:

- lower per-camera FPS

### Option B — Two processes

Each camera has its own runtime process and SQLite writes.

Pros:

- isolated failures
- simpler camera capture loops

Cons:

- duplicate model load
- more memory pressure
- harder demo orchestration

Recommendation: implement Option A first. Keep Option B as future work.

## Modules

Add or extend:

```text
apps/caresight-hub/caresight/runtime/cameras/sources.py
apps/caresight-hub/caresight/runtime/cameras/multi_camera.py
apps/caresight-hub/caresight/runtime/dashboard/service.py
apps/caresight-hub/caresight/runtime/appearance/service.py
```

Expected interfaces:

```python
class CameraSourceConfig:
    camera_id: str
    source_type: str
    source_uri: str | int
    room_id: str
    room_label: str

class MultiCameraFrame:
    camera_id: str
    room_id: str
    room_label: str
    frame: object
    captured_at: str

class MultiCameraSourceManager:
    def frames(self) -> Iterator[MultiCameraFrame]: ...
```

Rules:

- Each observation includes `camera_id`, `room_id`, `room_name`.
- Each event includes the camera where it occurred.
- Daily appearance continuity may link likely same profile across cameras but must remain bounded.
- Dashboard timeline groups by room/camera.
- If a camera fails, report camera health; do not synthesize events.

## Event narrative shape

Add a derived narrative object to dashboard and receipt, not canonical event state:

```json
{
  "multi_camera_narrative": {
    "source_of_truth": "sqlite_derived",
    "claim_boundary": "likely_continuity_not_identity",
    "timeline": [
      {
        "timestamp": "2026-05-20T02:10:00Z",
        "camera_id": "kitchen_counter",
        "room": "Kitchen",
        "summary": "Daily appearance profile observed near medication station.",
        "appearance_profile_id": "appearance_2026_05_20_001"
      },
      {
        "timestamp": "2026-05-20T02:36:31Z",
        "camera_id": "living_room",
        "room": "Living Room",
        "summary": "Likely same daily profile associated with possible floor-stay event.",
        "event_id": "evt_d9aa38bdc636459c92ea4e25f665cd0d"
      }
    ],
    "not_claimed": ["named_identity", "biometric_match", "fall_confirmed", "medical_emergency"]
  }
}
```

## OBS/FaceTime integration boundary

For the demo, OBS is a presentation bus, not source of truth.

Recommended demo flow:

```text
event fired with camera_id
  -> action request: switch_obs_event_scene
  -> operator-approved OBS WebSocket scene switch
  -> OBS scene shows local camera + event overlay
  -> OBS Virtual Camera already started manually
  -> FaceTime link/button is offered to caregiver/operator
```

Rules:

- OBS WebSocket must be localhost and password-protected.
- LLM may not directly call OBS.
- FaceTime launch is a handoff and may prompt on macOS.
- Document manual setup honestly.

## CLI

Add manual-operator command only if stable:

```bash
python apps/caresight-hub/scripts/v0_floor_stay_live.py --multi-camera --camera-id kitchen_counter --camera-id living_room --max-seconds 120 --stop-after-event
```

Or separate script:

```bash
python apps/caresight-hub/scripts/v1_multi_camera_live.py --camera-id kitchen_counter --camera-id living_room --max-seconds 120
```

Recommendation: avoid a new script unless current v0 script becomes too large. Keep files below repo line-length guidance.

Add read-only narrative command:

```bash
python apps/caresight-hub/scripts/care_console.py narrative --event-id evt_... --format json|markdown
```

## Tests

Add:

```text
apps/caresight-hub/tests/test_multi_camera_sources.py
apps/caresight-hub/tests/test_multi_camera_narrative.py
```

Required cases:

1. Explicit webcam/usb/continuity_camera/rtsp source configs normalize correctly.
2. Cloud provider source types are rejected.
3. RTSP credentials are not printed in logs or receipts.
4. Multi-camera frame includes camera and room metadata.
5. Event generated from camera B does not inherit camera A metadata.
6. Narrative groups timeline by room/camera.
7. Narrative uses likely continuity language only.
8. ONVIF discovery flag is rejected or ignored with blocker.
9. Camera failure creates health blocker, not synthetic events.
10. OBS action request is staged/manual-operator, not executed by LLM.

## Docs

Update:

```text
docs/architecture/camera_integration_strategy.md
docs/architecture/obs_facetime_live_view.md
docs/cli/COMMANDS.md
docs/roadmaps/CURRENT_STATE_AND_NEXT.md
CHANGELOG.md
docs/audits/YYYY-MM-DD-multi-camera-narrative-proof.md
```

Decision note if needed:

```text
CareSight v1/v2 multi-camera support uses explicitly configured local sources only. ONVIF discovery, LAN scanning, cloud-provider adapters, and credential-bearing provider flows remain out of scope.
```

## Definition of done

- Two explicitly configured local sources are supported at config/test level.
- Live path is manual-operator and honest about hardware proof.
- Dashboard/receipt can show room-by-room narrative.
- No cloud cameras or discovery added.
- OBS/FaceTime remain downstream handoff layers.
- `npm run check` passes.

## Pasteable Codex prompt

```text
Implement Sprint 05 Multi-Camera Narrative Proof. Add explicit local multi-camera config and deterministic source normalization for webcam, usb, continuity_camera, and local rtsp while preserving single-camera compatibility. Do not add Ring/Nest, cloud camera APIs, ONVIF discovery, LAN scanning, or credential discovery. Add a simple multi-camera source manager or extend existing camera source handling without duplicating model loads unnecessarily. Ensure observations/events preserve camera_id, room_id, and room_label. Add derived dashboard/receipt narrative grouped by room/camera using likely continuity language only. Stage OBS/FaceTime integration through action requests; do not execute from LLM. Tests must prove source validation, metadata preservation, cloud rejection, narrative boundaries, no credential logging, and camera health blockers. Update docs, changelog, CLI registry, and audit note. Run npm run check.
```
