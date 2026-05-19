# CareSight Hub

> Local-first care event engine using YOLO26 MLX on Apple Silicon.

## What it does

CareSight Hub turns a Mac and ordinary cameras into an ambient care awareness system. It uses YOLO26 MLX locally to detect care-relevant events, stores structured observations in SQLite, and routes alerts or journal entries to permissioned caregivers.

The person being cared for does not need to press a button, open an app, or remember a routine.

## Why I built it

Many care situations depend on a person being able to ask for help or document what happened. That fails when someone is injured, confused, asleep, overwhelmed, or simply forgets.

CareSight is designed as a local safety layer for families, temporary caregivers, pet sitters, and eventually small care environments. It creates observations that humans can confirm, dismiss, or act on.

## Challenge track

Useful / Enterprise-adjacent.

## Meaningful YOLO26 MLX use

YOLO26 MLX provides the on-device perception layer:

- person detection
- object detection
- pet detection where applicable
- zone membership
- temporal event detection
- care event confidence scoring

The system does not merely draw boxes. It converts detections into structured care events such as:

- possible floor-stay event
- medication routine likely observed
- pet food activity observed

## On-device execution

All YOLO inference runs locally on Apple Silicon using YOLO26 MLX. Raw video is not uploaded by default.

## Hardware used

- Machine: `<Mac model, e.g., M1 Pro MacBook Pro 16GB>`
- Camera: `<Mac webcam / USB webcam / iPhone Continuity Camera / RTSP camera>`
- OS: `<macOS version>`

## Model variant

- Primary: `yolo26n`
- Optional comparison: `yolo26s`

## How to run

```bash
git clone <repo-url>
cd caresight-hub
uv venv
source .venv/bin/activate
uv pip install -e .
python -m caresight.cli run --config config/demo.yaml
```

## Run dashboard

```bash
python -m caresight.app.dashboard
```

Then open:

```text
http://localhost:8000
```

## Demo events

### Possible floor-stay event

A person remains in a configured floor zone beyond the threshold.

### Medication routine likely observed

A person appears in the medication station zone during the expected routine window, with optional object evidence.

### Pet food activity observed

A pet remains near the food/water zone for a configured duration.

## Data storage

CareSight stores structured event records locally in SQLite.

Generated daily journals are derived from SQLite. Apple Notes/Markdown exports are human-readable mirrors, not the source of truth.

## Optional integrations

- OBS scene switching
- OBS Virtual Camera
- FaceTime handoff
- Apple Shortcuts alert/journal actions
- Gemma local summarizer
- OpenClaw hook/action gateway

## Privacy and safety

CareSight Hub is a prototype caregiver awareness system. It is not a medical device, certified fall detector, alarm service, or emergency dispatch product.

The system uses conservative event labels:

- “possible floor-stay event”
- “medication routine likely observed”
- “awaiting confirmation”

## Limitations

- The MVP does not identify people by face.
- Medication ingestion is not confirmed by vision alone.
- Ring/Nest integrations are not part of the core demo.
- FaceTime may require macOS permissions or prompts.
- Event accuracy depends on camera placement, lighting, and model confidence.

## Benchmarks

| Hardware | Model | Source | Resolution | FPS | Notes |
|---|---|---:|---:|---:|---|
| `<M1 Pro 16GB>` | `yolo26n` | webcam | 640px | `<fill>` | live demo |
| `<M1 Pro 16GB>` | `yolo26s` | webcam | 640px | `<fill>` | optional |

## Architecture

```text
camera → YOLO26 MLX → tracking/zones → event engine → SQLite → dashboard/journal/alert
```

Optional:

```text
event → OBS scene switch → FaceTime handoff
```

## Roadmap

- Multi-camera RTSP/ONVIF support.
- Home Assistant camera support.
- Role-based temporary caregiver access.
- Secure remote event view.
- Facility care-plan workflow.
- Custom fine-tuned care objects.

## License

`<choose and verify license compatibility before release>`

Note: verify upstream license obligations for YOLO26 MLX and any included dependencies before publishing.
