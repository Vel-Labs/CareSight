# Tapo RTSP Validation

Date: 2026-05-23

Scope: Sprint 05 Tapo/local RTSP validation receipt.

## Command

```bash
python3 apps/caresight-hub/scripts/caresight_camera_probe.py \
  --config apps/caresight-hub/config/tapo.local.example.json \
  --dry-run
```

Live validation command used locally:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/caresight_camera_probe.py \
  --config apps/caresight-hub/config/tapo_living_room.local.json
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

Status: live local RTSP probe passed for the two owner-authorized Tapo C210 cameras after Camera Account setup.

Observed receipts:

- `tapo_living_room`: reachable true, stream opened true, first frame received true, `1920x1080`, `15.0` FPS, redacted RTSP URI.
- `tapo_kitchen`: reachable true, stream opened true, first frame received true, `1920x1080`, `15.0` FPS, redacted RTSP URI.

Important runtime note: system `python3` reported `missing_cv2`; live probe success used `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python`, because that venv includes OpenCV.

If live frames open, record frame dimensions, FPS, camera ID, room label, and whether the stream path is `stream1` or `stream2`. If live frames do not open, record ping/TCP reachability, RTSP open state, first-frame state, and blocker class.

No real camera IPs, credentials, still frames, or household details should be committed.
