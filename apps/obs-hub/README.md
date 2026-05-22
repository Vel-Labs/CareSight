# CareSight OBS Hub

CareSight OBS Hub creates local OBS scenes for caregiver review and FaceTime/OBS Virtual Camera demos. The scenes are human-facing review surfaces, not diagnostic or emergency-dispatch surfaces.

## Requirements

- OBS Studio 28 or newer.
- OBS websocket enabled under `Tools > WebSocket Server Settings`.
- Python 3.

Default websocket settings:

- Host: `127.0.0.1`
- Port: `4455`
- Password: `OBS_WEBSOCKET_PASSWORD`

## Setup

```bash
export OBS_WEBSOCKET_PASSWORD="your-obs-password"
./scripts/setup_obs_scene.sh
```

Dry-run without connecting to OBS:

```bash
./scripts/setup_obs_scene.sh --dry-run
```

Set a specific program scene:

```bash
./scripts/setup_obs_scene.sh --scene "CareSight Hub - Dashboard"
```

## Dynamic Overlay Data

OBS scenes are intentionally stable. Event-specific data is written to:

```text
apps/obs-hub/config/current_event.json
apps/obs-hub/config/current_event.js
```

The browser overlays prefer `current_event.js` because OBS Browser Source can load local scripts more reliably than JSON fetches from `file://` URLs. The overlays fall back to `current_event.json`, then `sample_event.json`, then embedded fixture data.

Update from the latest SQLite event:

```bash
./scripts/update_obs_overlay.sh
```

Update from a specific event:

```bash
./scripts/update_obs_overlay.sh --event-id evt_d9aa38bdc636459c92ea4e25f665cd0d
```

Continuously follow the latest SQLite event:

```bash
./scripts/update_obs_overlay.sh --watch
```

Preview fixture data without writing:

```bash
./scripts/update_obs_overlay.sh --sample --dry-run
```

This is the preferred integration point for local Gemma/Hermes tools: they should update the local overlay state file from approved SQLite context instead of creating OBS text layers or touching raw video.

In OBS, the bottom-right footer should show `Data: current_event.js` after a successful dynamic update. If it shows `sample_event.json` or `fallback`, refresh the browser source or rerun the OBS setup script after updating the overlay.

The caregiver UI intentionally displays a shortened event ID so it does not crowd the handoff panel. The full event ID remains in `current_event.json`, SQLite, and audit receipts.

## Scenes

- `CareSight Hub - Dashboard`
- `CareSight Hub - Escalation`
- `CareSight Hub - FaceTime Mobile`
- `CareSight Camera - Living Room`
- `CareSight Camera - Kitchen`
- `CareSight Camera - Hallway`
- `CareSight Camera - Bedroom`

## FaceTime Flow

1. Open OBS.
2. Run `./scripts/setup_obs_scene.sh`.
3. Start OBS Virtual Camera.
4. In FaceTime, select OBS Virtual Camera.
5. Use `CareSight Hub - Dashboard` for overview.
6. Switch to `CareSight Hub - Escalation` during desktop review.
7. Use `CareSight Hub - FaceTime Mobile` for phone FaceTime recipients.
8. Switch to an individual camera scene if the caregiver needs one zone.

The live handoff script attempts to switch OBS to `CareSight Hub - FaceTime Mobile` before opening FaceTime. This scene uses a 1080x1920 browser source and requests matching OBS video output so phone recipients do not receive a tiny portrait UI embedded in a landscape frame.

The FaceTime Mobile scene renders the detector feed through the OBS browser overlay. Start the detector with:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --obs-browser-feed
```

The detector serves annotated MJPEG locally at:

```text
http://127.0.0.1:8766/stream.mjpg
```

This is the preferred demo feed because OBS does not need to open the webcam separately while the Python detector owns the camera. The stream includes detector boxes and the floor-zone overlay. No raw video is sent to Gemma or Hermes.

`v0_floor_stay_live.py --obs-live-preview` can also write `apps/obs-hub/config/live_preview.jpg` as a fallback/debug artifact, but the MJPEG browser feed is the primary live path.

## Camera Sources

The default `apps/obs-hub/config/cameras.json` uses a Living Room image path and placeholder sources for the other camera scenes. To use a local image for the Living Room feed without editing tracked config:

```bash
export CARESIGHT_OBS_SAMPLE_IMAGE="/absolute/path/to/living-room-image.jpg"
./scripts/setup_obs_scene.sh
```

To replace placeholders with real camera devices, update local OBS sources after the scene is created or adjust `apps/obs-hub/config/cameras.json` in a local branch. Do not commit private camera credentials or raw video.

## Language Boundaries

Use bounded wording such as:

- Possible floor-stay
- Extended inactivity observed
- Routine activity observed
- Last movement observed
- Review required
- Draft caregiver alert prepared
- Human review required

Do not use unsafe wording such as:

- Fall detected
- Emergency detected
- Medication confirmed
- Patient stable
- AI diagnosis
- Dispatching help

Raw video stays local. CareSight does not diagnose, dispatch emergency services, certify falls, or replace caregivers.
