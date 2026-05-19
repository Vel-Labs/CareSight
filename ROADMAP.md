# Roadmap

This is the high-level roadmap index for humans, judges, and coding agents.

## Current Ship Goal

CareSight Hub v1/v2 hackathon MVP: a local-first care event engine that runs YOLO26 MLX on Apple Silicon, stores structured events locally, creates a daily journal, and alerts permissioned caregivers.

## Now

- Operational source of truth: `docs/roadmaps/CURRENT_STATE_AND_NEXT.md`
- Hackathon roadmap: `docs/hackathon/hackathon_roadmap.md`
- Imported planning pack: `docs/caresight_hub_docs_pack/`

## Future

- Product and enterprise roadmap: `docs/roadmaps/future_roadmap.md`
- Feature slices: `docs/roadmaps/features/`

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
