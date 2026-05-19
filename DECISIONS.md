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
