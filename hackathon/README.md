# CareSight Hackathon Entry

This folder is the judge and operator entrypoint for the current CareSight demo. It points to the short path first, then links back to the deeper repo evidence.

CareSight is a bounded local-first caregiver awareness prototype. It is not a medical device, certified fall detector, HIPAA compliance claim, or emergency dispatch system. The demo language stays at possible events plus human review.

## Current Demo Cut

```text
Tapo RTSP cameras
  -> YOLO26 MLX local detector workers
  -> calibrated floor-plane overlay
  -> possible_floor_stay or missing_off_camera_extended event
  -> local SQLite receipt and snapshot
  -> Markdown review packet
  -> OBS caregiver handoff surface
```

## Three Visible Lanes

| Lane | What it proves | Start here |
| --- | --- | --- |
| Operator journey | Setup, configuration, and daily utilization commands | `hackathon/DEMO_JOURNEY.md` |
| Proof trail | What was tested, what is still operator-validated, and where receipts live | `hackathon/AUDIT_DIGEST.md` |
| Product concept | What becomes home care, external caregiver, and facility product work later | `docs/roadmaps/future_roadmap.md` |

## Demo Events

The hackathon story should center on two v1 care events:

- `possible_floor_stay`: someone may be on the floor long enough to require review.
- `missing_off_camera_extended`: someone who was recently visible is absent long enough to require a caregiver check.

Medication and hydration routines are kept out of the primary recorded demo. Vision alone must not confirm medication administration, and those routines need a separate validation lane before they are demo claims.

## Current Operator Command

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/caresight_detector_start.py \
  --appearance-overlay \
  --stop-existing
```

The command starts one detector worker per configured local camera and exposes OBS browser feeds. Current local ports are `8766` for Living Room and `8767` for Kitchen.

## Human Review Surfaces

Use these surfaces for the recorded demo once an event exists:

```bash
python3 apps/caresight-hub/scripts/care_console.py review-packet <event_id> --format markdown
python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt <event_id> --format markdown
python3 apps/caresight-hub/scripts/care_console.py escalation-receipt <event_id> --format markdown
python3 apps/caresight-hub/scripts/care_console.py narrative --format markdown
```

SQLite remains the canonical local record. OBS and Markdown are presentation layers.

