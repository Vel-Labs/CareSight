# CareSight Demo Journey

This is the short operator path for the recorded hackathon demo. It intentionally separates setup, configuration, and utilization.

## 1. Setup

Install local prerequisites:

```bash
npm run install:local
python3 apps/caresight-hub/scripts/caresight_install_all.py
```

Run the deterministic gate:

```bash
npm run check
```

Run the demo preflight:

```bash
python3 apps/caresight-hub/scripts/caresight_demo_preflight.py
```

## 2. Camera Configuration

For Tapo cameras, create a separate camera account in the Tapo app. That account is the RTSP/NVR credential path. Static IP is useful but not required for RTSP authentication.

Probe the local camera config with the YOLO26 venv so OpenCV is available:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/caresight_camera_probe.py \
  --config apps/caresight-hub/config/tapo_living_room.local.json

apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/caresight_camera_probe.py \
  --config apps/caresight-hub/config/tapo_kitchen.local.json
```

Expected proof: `reachable=true`, `stream_opened=true`, and `first_frame_received=true`.

## 3. Start Local Detector Feeds

Start both configured camera workers and stop older workers first:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/caresight_detector_start.py \
  --appearance-overlay \
  --stop-existing
```

Default OBS browser feed URLs:

| Camera | URL |
| --- | --- |
| Living Room | `http://127.0.0.1:8766/live.html` |
| Kitchen | `http://127.0.0.1:8767/live.html` |

Health checks:

```bash
curl http://127.0.0.1:8766/health
curl http://127.0.0.1:8767/health
```

## 4. Event Proof

The primary demo event is:

```text
possible_floor_stay
```

The second v1 event is:

```text
missing_off_camera_extended
```

`missing_off_camera_extended` follows the same bounded review path as floor-stay. It should show the last local snapshot, last-seen room/camera, and advisory daily appearance attributes from the last visible frame. If the person returns, the follow-up path should be a separate acknowledgement message that the subject is visible again. That return-follow-up is a next implementation slice, not a completed demo claim yet.

For a bounded single-camera operator proof:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --config apps/caresight-hub/config/tapo-runtime.local.json \
  --camera-id tapo_living_room \
  --obs-browser-feed \
  --obs-browser-feed-port 8766 \
  --obs-live-preview \
  --appearance-overlay \
  --missing-off-camera-events \
  --debug-floor-stay \
  --stop-after-event
```

## 5. Review And Handoff

After an event is persisted, render the human-readable review packet:

```bash
python3 apps/caresight-hub/scripts/care_console.py review-packet <event_id> --format markdown
```

Render the local blackbox receipt:

```bash
python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt <event_id> --format markdown
```

Render escalation evidence:

```bash
python3 apps/caresight-hub/scripts/care_console.py escalation-receipt <event_id> --format markdown
```

Render a multi-camera narrative:

```bash
python3 apps/caresight-hub/scripts/care_console.py narrative --format markdown
```

For the recorded demo, the safest path is: visible alert text, screenshot evidence, staged handoff, and explicitly approved FaceTime escalation if the operator chooses to show the live step.

## 6. OBS Control

For this demo, OBS should stay as the visible presentation surface. Browser sources should use the local detector feeds above.

Programmatic OBS control should prefer obs-websocket scene/source control later. OBS hotkeys are acceptable as a fallback for recorded-demo operation, but they are more brittle than named scene/source control because they depend on the local OBS profile and keyboard focus.

## 7. Set-And-Forget Future

The product direction is a quiet appliance:

```text
launchd or service wrapper
  -> detector worker heartbeat
  -> camera health and reconnect
  -> SQLite event store health check
  -> OBS/live surface health check
  -> bounded restart policy
```

That heartbeat/restart suite is future product infrastructure. It is not required for the recorded hackathon demo, but it is the right architecture for a stable home deployment.

