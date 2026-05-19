# License Notes

This document is project guidance, not legal advice.

## Hackathon License Posture

CareSight Hub uses `AGPL-3.0-only` for the public hackathon repository.

This is intentional:

- The core runtime currently depends on the `thewebAI/yolo-mlx` submodule.
- That upstream project is licensed under `AGPL-3.0-only`.
- The hackathon build is meant to be an inspectable, accessible local-first baseline.
- AGPL reciprocity fits the project ethos: people can study, run, modify, and share the system, while public network-service modifications should remain available to users.

## Commercial Product Direction

The license choice for this hackathon repo does not prevent a future business. It does mean future product architecture needs to be deliberate.

Likely commercial value-adds can live around the open baseline:

- reliable packaging and installation
- hardware bundles
- managed updates
- support
- caregiver workflow design
- camera compatibility testing
- alert routing
- deployment tooling

If a future closed-source runtime is needed, the project should revisit the vision dependency strategy before commercialization. Options may include a separate permissive/commercial vision runtime, a commercial license from an upstream vendor if available, or a clearer separation between open AGPL components and proprietary service layers.

## Current Distribution Rules

- Do not commit model weights unless their license permits redistribution.
- Do not commit private camera URLs, private footage, credentials, or local event data.
- Keep third-party notices intact.
- Keep the root `LICENSE`, `NOTICE.md`, and this note synchronized when licensing posture changes.
