# CareSight Hackathon Entry

CareSight is a local-first caregiver awareness prototype for the moments when families do not have enough continuity: someone may be on the floor, someone may have left the camera view, a caregiver may need context quickly, and the home should be able to preserve what was observed without turning into a cloud surveillance product.

The hero demo is the local care observation engine:

```text
Local Care Observation Engine
  -> YOLO26 MLX local perception
  -> bounded care event, such as possible floor-stay / suspected fall or missing-off-camera
  -> local SQLite memory and snapshot
  -> human-readable review prepared with local Gemma 4 E2B MLX
  -> loved-one / caregiver handoff through Hermes agent harness
  -> Gemma-prepared text, screenshot escalation, optional FaceTime live feed through OBS,
     and optional local Holler TTS playback using the Dakota voice
```

CareSight is not a medical device, certified fall detector, HIPAA compliance claim, alarm service, or emergency dispatch system. It creates possible care observations that authorized humans can review.

This folder is the judge and operator entrypoint for the current demo. It points to the short path first, then links back to the deeper repo evidence.

## Affordable Home Bundle Concept

The camera hardware is not the product story; it is the accessibility story. Low-cost RTSP cameras make it possible to assemble a small local care-awareness setup without specialized equipment.

Example small-domicile setup:

| Piece | Conceptual cost | Role |
| --- | ---: | --- |
| Mac mini class machine, 16 GB | about `$600` | Local appliance for YOLO26 MLX, SQLite, local models, and handoff services |
| Accessible RTSP cameras | about `$50` each | Room views for a 2-3 camera home setup |
| Existing home internet | household-dependent | Caregiver message/call path, not raw-video cloud storage by default |
| Setup time | not clean-room validated yet | Current target is under 1 hour, but a first-time setup should still budget a couple hours for model downloads, camera account setup, room labels, and floor-plane calibration. |

The product direction is a practical home bundle: Mac mini, accessible cameras, local models, clear setup commands, and enough audit structure that a household can track possible care instances, keep a local diary, and escalate to a loved one or caregiver. The setup-time target still needs a clean-room install test before it should be treated as a proven claim.

## Current Demo Cut

```text
local camera feeds
  -> YOLO26 MLX detector workers on the Mac
  -> calibrated floor-plane overlay and bounded event policies
  -> SQLite local memory, event receipt, and snapshot
  -> Gemma 4 E2B MLX local review/draft layer
  -> Hermes staged handoff harness for caregiver text and escalation payloads
  -> OBS local review / optional FaceTime live-feed surface
  -> Holler TTS local handoff audio with Dakota voice when explicitly approved
```

The current hardware path uses owner-authorized local Tapo RTSP cameras because they are cheap, available, and enough to prove the home-bundle concept. They are replaceable inputs, not the center of the architecture.

The important privacy and trust boundary is that raw camera context, event memory, model drafting, and proof receipts are designed to run locally first. The SQLite store acts like a local blackbox: events, observations, reviews, drafts, snapshots, and execution attempts are structured records that agents can read from and add to through bounded services, but they are not supposed to delete records or rewrite history. The handoff path should expose only the event-scoped context that a caregiver needs: message text, a screenshot when approved, and a live feed only when the operator chooses that escalation path.

## Three Visible Lanes

| Lane | What it proves | Start here |
| --- | --- | --- |
| Operator journey | Setup, configuration, and daily utilization commands | `hackathon/DEMO_JOURNEY.md` |
| Proof trail | What was tested, what is still operator-validated, and where receipts live | `hackathon/AUDIT_DIGEST.md` |
| Product concept | What becomes home care, external caregiver, and facility product work later | `docs/roadmaps/future_roadmap.md` |

## Demo Events

The hackathon story centers on two v1 care events:

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

## Agentic-Ready Architecture

CareSight is built so coding agents and local service agents can safely extend it without becoming the authority layer. The architecture separates observation, memory, drafting, service handoff, and human confirmation.

- `contracts/` owns schemas and examples.
- `packages/core/` owns TypeScript validation and contract enforcement.
- `apps/caresight-hub/` owns the Python runtime for YOLO26 MLX, camera input, SQLite, review packets, local Gemma drafting, Hermes handoff preparation, OBS updates, and Holler TTS helpers.
- `docs/` and `hackathon/` own the human-readable operating story, audit trail, and roadmap.

Local model and agent lanes:

| Lane | Tooling | Boundary |
| --- | --- | --- |
| Vision | YOLO26 MLX | Detects people/objects locally and feeds bounded event policy. |
| Memory | SQLite | Stores event receipts, snapshots, reviews, drafts, and execution attempts as a local blackbox. |
| Drafting | Gemma 4 E2B MLX | Prepares human-readable review and caregiver alert wording from SQLite-derived context. |
| Handoff harness | Hermes | Stages and records caregiver handoff payloads instead of bypassing CareSight policy. |
| Visual handoff | OBS | Presents the local live/review surface and optional FaceTime feed source. |
| Audio handoff | Holler TTS, Dakota voice | Plays approved local handoff audio only after explicit operator approval. |

Agents may summarize events, draft caregiver text, update OBS presentation state, and prepare handoff payloads through contract-shaped records. They must not confirm or dismiss events, delete records, rewrite the blackbox history, diagnose, claim medical certainty, dispatch help, or upload raw video as a default path. That boundary is what lets the repo be highly agentic while still respecting the human care loop.

The project uses open-source components and local-first defaults so the work can be inspected, reused, and improved for general good rather than hidden behind an opaque cloud-only care pipeline.
