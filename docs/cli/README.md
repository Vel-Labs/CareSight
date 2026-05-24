# CLI Documentation

CareSight commands are split by operator task so future agents do not need to scan the full command history before choosing a safe path.

Start with [`COMMANDS.md`](COMMANDS.md) for the safety-class index, then open the relevant category:

- [`setup.md`](setup.md): install, models, stack, and readiness setup.
- [`camera.md`](camera.md): camera discovery, probes, local preview, detector feeds, and feed exposure.
- [`detection.md`](detection.md): YOLO26 smoke checks and the floor-stay live loop.
- [`review.md`](review.md): event inbox, review lifecycle, dashboard, receipts, appearance, and redaction.
- [`agent-handoff.md`](agent-handoff.md): drafts, staged requests, Hermes payloads, and no-send receipts.
- [`obs-tts-facetime.md`](obs-tts-facetime.md): OBS, TTS, FaceTime, live handoff, and demo terminal surfaces.
- [`validation.md`](validation.md): unit gates, heartbeat receipts, live-proof audit, feed checks, and policy checks.

Safety rule: agents may run `agent-safe-read` commands. `manual-operator` commands require local operator ownership. `human-review-required` commands require explicit human approval.
