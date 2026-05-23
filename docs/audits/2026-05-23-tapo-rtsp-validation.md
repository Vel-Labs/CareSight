# Tapo RTSP Validation

Date: 2026-05-23

Scope: Sprint 05 Tapo/local RTSP validation receipt.

## Command

```bash
python3 apps/caresight-hub/scripts/caresight_camera_probe.py \
  --config apps/caresight-hub/config/tapo.local.example.json \
  --dry-run
```

## Result

The committed example dry-run passed and produced a redacted receipt:

```json
{
  "camera_id": "tapo_living_room",
  "redacted_uri": "rtsp://***:***@192.0.2.55:554/stream1",
  "reachable": "not_attempted",
  "stream_opened": "not_attempted",
  "first_frame_received": "not_attempted"
}
```

## Live Validation Status

Status: blocked on operator-owned hardware/network credentials.

Required operator inputs:

- Copy `apps/caresight-hub/config/tapo.local.example.json` to an ignored local config.
- Replace the TEST-NET IP, placeholder camera username, and placeholder camera password.
- Keep the camera and CareSight machine on the same LAN.
- Run the probe without `--dry-run`.

If live frames open, record frame dimensions, FPS, camera ID, room label, and whether the stream path is `stream1` or `stream2`. If live frames do not open, record ping/TCP reachability, RTSP open state, first-frame state, and blocker class.

No real camera IPs, credentials, still frames, or household details should be committed.
