# Roadmap

This is the high-level roadmap index for humans, judges, and coding agents.

## Current Ship Goal

CareSight Hub v1/v2 hackathon MVP: a local-first care event engine that runs YOLO26 MLX on Apple Silicon, stores structured events locally in SQLite, routes those records through local model assist, and keeps caregiver handoff behind human review.

Current ship chain:

```text
Local camera
  -> YOLO26 MLX
  -> bounded event policy
  -> SQLite memory
  -> local model assist: Gemma draft, Hermes Agent no-send harness, Holler TTS readback
  -> human review
  -> caregiver handoff
```

The local model layer is draft/readback/preflight only. It may summarize SQLite-derived context, prepare handoff payloads, or generate approved TTS audio, but it must not confirm events, rewrite records, inspect raw video as the decision-maker, dispatch help, or bypass the human review gate.

## Now

- Operational source of truth: `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- Hackathon roadmap: `docs/hackathon/hackathon_roadmap.md`
- Imported planning pack: `docs/caresight_hub_docs_pack/`
- Current live visual surface: OBS browser-feed overlays act as the intermediary review and FaceTime/recording surface while CareSight owns detection, events, and SQLite audit records.

## Future

- Product and enterprise roadmap: `docs/roadmaps/future_roadmap.md`
- Feature slices: `docs/roadmaps/features/`
- Dedicated CareSight camera/review dashboard: native calibration, multi-camera review, replay, posture indicators, missing-off-camera review, and audit navigation after the OBS-mediated hackathon path is stable.

## Product Lane Index

These lanes describe where the same bounded local-first loop could go after the hackathon. They are not deployment-readiness claims.

| Lane | Potential features / implementations | Readiness boundary |
| --- | --- | --- |
| Home Care | Mac mini-class appliance setup, local camera configuration, calibrated floor planes, SQLite diary, household review dashboard, privacy mode, local retention controls | Must be proven by clean-room home setup, multi-day local run, and household operator feedback |
| Remote Caregiver Practice | caregiver roles, allowlisted contacts, acknowledgement flow, no-response follow-up, event-scoped screenshot sharing, daily summary, temporary caregiver access | Requires explicit household approval, contact allowlists, and audit receipts for every external handoff |
| Care Homes / Medical Facilities | multi-room dashboards, staff shift handoffs, incident queues, retention policy, audit export, deployment/update tooling, hardware support packages | Future lane only; requires stricter validation, legal/regulatory review, facility workflow testing, and no medical-device or HIPAA claim by default |

## Dependency Order

1. Personalize scaffold contracts and docs.
2. Validate care-event, camera, routine, alert-policy, and caregiver-role schemas.
3. Keep TypeScript governance checks passing.
4. Add the Python runtime behind `apps/caresight-hub/`.
5. Prove v0 smoke test: one camera, YOLO26 MLX, one event, one SQLite write.
6. Build v1 hackathon MVP: two event types, dashboard, journal, alert.
7. Add v2 stretch only after v1 remains runnable.

## Do Not Start Yet

- Ring/Nest adapters.
- HIPAA compliance claims.
- Autonomous emergency dispatch.
- Medical-device claims.
- Cloud raw-video upload defaults.
