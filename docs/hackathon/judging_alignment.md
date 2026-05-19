# Judging Alignment

## Core Claim

CareSight Hub demonstrates a local-first care loop on Apple Silicon:

```text
YOLO26 MLX perception
  -> bounded event engine
  -> SQLite local memory
  -> care journal
  -> caregiver alert
```

## Evidence to Show

- On-device model lane: YOLO26 MLX is the vision path.
- Local data lane: event records and journal entries stay local by default.
- Safety lane: contracts block medical overclaims, autonomous emergency dispatch, and default raw-video cloud upload.
- Product lane: the demo shows care events and escalation, not only bounding boxes.

## Language to Use

- `possible floor-stay event`
- `medication routine likely observed`
- `awaiting caregiver acknowledgement`
- `raw video stays local by default`

## Language to Avoid

- medical device
- certified fall detection
- HIPAA compliant
- autonomous emergency dispatch
- confirmed medication ingestion from vision
