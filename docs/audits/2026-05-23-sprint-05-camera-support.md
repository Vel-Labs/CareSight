# Sprint 05 Camera Support

Date: 2026-05-23

Scope: deterministic Sprint 05 implementation for explicit local/network camera support. This is implemented for config, probe, health, frame-manager, and narrative receipts; it is not live Tapo production validation.

## Implemented Behavior

- Added explicit camera examples for `webcam`, `usb`, `continuity_camera`, and local `rtsp` sources with local-only privacy defaults.
- Added optional camera privacy metadata: `raw_video_storage` and `cloud_upload_default`.
- Rejected cloud/provider/discovery scope in camera config: Ring, Nest, Arlo, Wyze cloud, Home Assistant cloud, ONVIF discovery, LAN scan, and RTSP URIs with embedded credentials in committed runtime config.
- Added `caresight_camera_probe.py` for ignored local RTSP configs. The probe redacts credentials and reports reachability, stream open state, first-frame state, dimensions, FPS, and blockers.
- Added a sequential `MultiCameraFrameManager` that returns frames with `camera_id`, `room_id`, `room_label`, and `captured_at`.
- Camera source failures now become camera-health blockers in the frame manager, not synthetic care events.
- Added `care_console.py narrative <event_id> --format json|markdown` for SQLite-derived camera/room/track context with `likely_continuity_not_identity` as the claim boundary.

## Deterministic Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s apps/caresight-hub/tests -t apps/caresight-hub -p 'test_multi_camera_sources.py'
```

Result: passed, 6 tests OK.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s apps/caresight-hub/tests -t apps/caresight-hub -p 'test_multi_camera_narrative.py'
```

Result: passed, 2 tests OK.

```bash
python3 apps/caresight-hub/scripts/caresight_camera_probe.py --config apps/caresight-hub/config/tapo.local.example.json --dry-run
```

Result: passed. Output redacted `rtsp://***:***@192.0.2.55:554/stream1` and did not attempt a stream open.

```bash
python3 apps/caresight-hub/scripts/care_console.py --help
```

Result: passed and listed `narrative`.

## Boundaries

- No camera IPs, usernames, passwords, private still frames, raw video, or household network details were committed.
- No ONVIF discovery, LAN scanning, port forwarding, cloud camera API, Ring/Nest adapter, or Home Assistant cloud adapter was added.
- No OBS, FaceTime, iMessage, TTS, review lifecycle mutation, or emergency dispatch path was engaged.

## Remaining Work

- Live Tapo validation still requires an operator-owned ignored `tapo.local.json`, same-LAN camera access, and camera credentials.
- Multi-camera live event loop integration remains a follow-up if the existing `v0_floor_stay_live.py` grows too large; this slice provides the tested manager and narrative receipt foundation.
