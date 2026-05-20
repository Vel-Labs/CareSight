# Decisions

## 2026-05-18: Adopt Project Scaffold as CareSight Governance Backbone

CareSight Hub uses the TypeScript scaffold for contracts, validation, governance, quality gates, and agent operating rules. Runtime implementation lives separately in `apps/caresight-hub/`.

Rationale: this preserves the scaffold's contract-first strengths while avoiding a mixed TypeScript/Python implementation boundary.

## 2026-05-18: Keep CareSight Local-First and Human-Confirmed

CareSight events are local structured observations. The system may alert caregivers and create journals, but it must not autonomously dispatch emergency services, diagnose medical conditions, or confirm medication administration from vision alone.

Rationale: the hackathon demo should show responsible AI boundaries through schemas, examples, and implementation constraints.

## 2026-05-18: Clone YOLO26 MLX as Vendored Runtime Dependency

The upstream `thewebAI/yolo-mlx` repository is cloned under `apps/caresight-hub/vendor/yolo-mlx` for local testing and troubleshooting. CareSight-owned glue scripts live in `apps/caresight-hub/scripts/` and runtime code stays in `apps/caresight-hub/caresight/`.

Rationale: this keeps the challenge-critical YOLO26 MLX implementation close enough for offline inspection and debugging while preserving a clear boundary between AGPL upstream code and CareSight-specific runtime work.

## 2026-05-18: Make v0 Review Human-Gated and Agent-Ready

CareSight v0 review commands may list and summarize local events, but confirm/dismiss transitions require an explicit human reviewer. Each review creates a durable review row, journal row, and report-only agent handoff payload.

Rationale: this proves the first agent-ready lifecycle while preserving the bounded control loop and preventing autonomous emergency dispatch, medical diagnosis, or agent-owned acknowledgement.

## 2026-05-19: Use AGPL-3.0-Only for the Hackathon Repository

CareSight Hub uses `AGPL-3.0-only` for the public hackathon repository. The current runtime depends on the `thewebAI/yolo-mlx` submodule, which is also licensed under `AGPL-3.0-only`.

Rationale: this keeps the hackathon build open, inspectable, and compatible with the current YOLO MLX dependency posture while leaving future commercial packaging, support, managed updates, hardware compatibility, and other service layers as separate product decisions.

## 2026-05-19: Keep v0 Audit Read-Only and SQLite-Canonical

The v0 audit command reads event, observation, review, journal, and handoff rows from SQLite and does not mutate event lifecycle state. Review lifecycle mutations still require an explicit human reviewer, and automation-like reviewer names are rejected.

Rationale: this lets operators and agents inspect the blackbox chain without making generated summaries, dashboards, scripts, agents, or LLM output canonical truth.

## 2026-05-19: Put Review Lifecycle Mutations Behind a Shared Service

CareSight v0 review lifecycle actions route through `caresight.runtime.review.ReviewService`. The CLI is one adapter over that service, and future console buttons should call the same service rather than creating separate confirm, dismiss, journal, or handoff logic.

Rationale: a single review boundary keeps reviewer validation, SQLite blackbox writes, report-only agent handoffs, and forbidden automation actions consistent across operator surfaces.

## 2026-05-19: Keep Inference Adapter Fail-Closed and Observation-Normalized

CareSight-owned inference code lives under `apps/caresight-hub/caresight/runtime/inference/`. The adapter loads YOLO26 MLX only when the configured model is present and importable, returns raw detections from actual model output, and normalizes those detections into observations with configured camera and room metadata.

Rationale: downstream event policies need stable CareSight observations, but the demo must not synthesize detections or hide model/runtime failures behind plausible-looking output.

## 2026-05-19: Start Tracking with a Lightweight Deterministic State Machine

CareSight starts v1 tracking with a local IoU-based track state machine instead of adding a heavier tracker dependency. Floor-stay events now require a stable `track_id` to remain in the configured low zone, and missing-off-camera is represented as a separate human-review event when a known track is absent beyond the configured window.

Rationale: the hackathon build needs track-aware event semantics and SQLite-visible `track_id` evidence before comparing ByteTrack or BoT-SORT. The lightweight state machine is deterministic, testable, and keeps emergency dispatch, diagnosis, and medication claims out of the tracking layer.

## 2026-05-19: Keep Routine Events Deterministic and Human-Confirmed

Medication and hydration routine events require a person in the configured routine zone, narrow configured object-label evidence, and a routine time window. These events are recorded as `*_likely_observed` and remain `awaiting_human_confirmation`.

Rationale: routine awareness is useful for the demo, but vision must not claim that medication was taken, hydration was medically sufficient, or any care action was confirmed without an authorized human.

## 2026-05-19: Keep Dashboard and Alert Drafts Presentation-Only

The local care console renders dashboard state and caregiver alert drafts from SQLite through `ReviewService`. It may show review controls and draft text-to-FaceTime escalation wording, but delete, dispatch, diagnosis, and confirmation remain outside presentation code.

Rationale: the demo needs a visible care surface, but SQLite remains the blackbox source of truth and the review service remains the only lifecycle mutation boundary.

## 2026-05-19: Constrain Agents to Provenance-Bearing Drafts and Audits

CareSight agents may summarize structured events, draft caregiver or journal wording, and audit handoff payloads only when outputs include purpose and event provenance. Agents must not confirm, dismiss, delete, dispatch, diagnose, confirm medication, or inspect raw video as the decision-maker.

Rationale: agent assistance can make the demo more useful, but it must remain downstream of SQLite truth and human review.

## 2026-05-19: Preserve Existing SQLite Blackbox Rows During Schema Upgrades

CareSight initialization applies additive SQLite schema upgrades such as adding `event_observations.track_id` to existing local databases. Upgrade logic must preserve prior rows and avoid destructive rewrites.

Rationale: local SQLite is the blackbox source of truth. New sprint fields should not require deleting earlier event evidence.

## 2026-05-20: Make Live Proof Collection Bounded

The v0 live loop supports `--max-seconds` and `--stop-after-event` so an operator can collect one `event_persisted` receipt without leaving the process open-ended.

Rationale: live demo proof should be operationally repeatable and auditable without forcing a GUI quit path or an unbounded process.

## 2026-05-20: Keep Live CLI Help Independent of Camera Runtime Imports

`v0_floor_stay_live.py` parses arguments before importing OpenCV or YOLO26 MLX, and it adds the vendored YOLO path before live runtime imports.

Rationale: operators need a reliable readiness/help command even on shells where camera/model runtime dependencies are unavailable.

## 2026-05-20: Keep Live-Proof Audit Bundles Read-Only

`live_proof_audit.py` collects readiness and post-event audit bundles without writing SQLite rows. It accepts an operator-supplied fresh `event_id`, reads event, observation, review, journal, and handoff records from SQLite-backed services, and includes dashboard and alert provenance only as derived outputs.

Rationale: live proof should become easier to audit without letting stale rows, dashboards, alerts, agents, or scripts become canonical truth or perform lifecycle actions.

## 2026-05-20: Keep Multi-Camera Support Deterministic and Local-Configured

CareSight v0 supports configured source selection for `webcam`, `usb`, `continuity_camera`, and local `rtsp` sources by camera ID or unambiguous source type. The runtime rejects cloud/provider camera scope and credential-bearing RTSP URLs, and it still writes selected camera provenance through the existing SQLite event path.

Rationale: the demo needs credible multi-camera setup without claiming live proof, adding discovery, handling credentials, or making any source other than SQLite canonical for event lifecycle state.
