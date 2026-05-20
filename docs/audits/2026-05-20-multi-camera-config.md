# Multi-Camera Config Checkpoint

Date: 2026-05-20

GoalBuddy task: `T027`

## Finding

CareSight now has deterministic configuration-level source selection for configured `webcam`, `usb`, `continuity_camera`, and local `rtsp` camera sources.

This is not live proof. T023 remains blocked until an operator grants camera authorization to the vendored Python runtime and captures a fresh `event_persisted` line from live hardware.

## Boundaries

- No camera authorization is required for the deterministic tests.
- No live hardware proof is claimed by config selection.
- Ring, Nest, Home Assistant, ONVIF discovery, LAN scanning, cloud-camera APIs, and credential-bearing RTSP URLs are rejected or out of scope.
- SQLite remains canonical for event, review, journal, handoff, dashboard, and alert provenance.

## Evidence

`test_v0_config.py` verifies that selecting a configured camera preserves `camera_id`, `room_label`, `source_type`, and OpenCV source normalization without opening the camera.

`camera-config.schema.json` allows only `webcam`, `usb`, `continuity_camera`, and `rtsp`; `ring-camera-provider-out-of-scope.json` verifies cloud/provider scope remains invalid.
