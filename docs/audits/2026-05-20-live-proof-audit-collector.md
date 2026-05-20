# Live Proof Audit Collector

Date: 2026-05-20

GoalBuddy task: `T025`

## Purpose

Add a read-only collector for live-proof readiness and post-event audit bundles without weakening the real live-data oracle.

## Readiness Behavior

Command:

```sh
python3 apps/caresight-hub/scripts/live_proof_audit.py readiness --camera-authorization blocked
```

Expected status: `not_ready`.

Expected blocker:

```text
camera_authorization_blocked
```

The readiness command checks local Python/environment metadata, config parsing, YOLO26 MLX model path, and the SQLite path reported by config. Camera authorization is reported as a named gate because deterministic tests must not require camera permission and T023 remains blocked until the operator grants camera access.

## Bundle Behavior

Command:

```sh
python3 apps/caresight-hub/scripts/live_proof_audit.py bundle <fresh_event_id>
```

The operator must supply a fresh `event_id` copied from a real `event_persisted` line. The collector reads SQLite through runtime services and emits event, observation `track_id`, human review, journal, report-only handoff, dashboard provenance, and alert provenance.

The collector returns `not_complete` when review, journal, handoff, observation `track_id`, dashboard timeline provenance, alert provenance, or event freshness is missing. A stale event ID is not accepted as final live proof.

## Boundaries

- The collector is read-only against SQLite.
- Optional `--output` writes only a report artifact.
- The collector does not create, confirm, dismiss, dispatch, diagnose, delete, synthesize, or reclassify events.
- SQLite remains canonical; dashboard and alert records are derived provenance outputs.
- T023 remains blocked until an operator grants camera access and captures a fresh `event_persisted` line.

## Deterministic Evidence

`test_live_proof_audit.py` seeds SQLite with event, observation, review, journal, and handoff rows, then verifies the collector returns a complete bundle with dashboard and alert provenance. Negative tests verify missing review/journal/handoff and stale event IDs return `not_complete`.
