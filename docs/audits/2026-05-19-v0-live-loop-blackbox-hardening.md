# v0 Live-Loop Blackbox Hardening

Date: 2026-05-19

## Scope

This audit records deterministic hardening for the v0 live-loop path. Live-camera proof still requires a local operator with camera access.

## Deterministic Hardening

- Added a read-only review CLI audit command for SQLite blackbox inspection.
- The audit command reports `event_id`, status, occurred timestamp, camera, zone, `snapshot_path`, observation count, review count, journal count, handoff count, latest reviewer, latest review timestamp, and report-only handoff state.
- Report-only handoff payloads now include reviewer, review ID, journal ID, and review timestamp.
- Reviewer-gated state changes reject automation-like reviewer names so an agent, script, dashboard, or LLM cannot become reviewer of record.

## Operator Live Checklist

Run these steps only when live camera hardware and an authorized human reviewer are available:

```bash
python apps/caresight-hub/scripts/v0_floor_stay_live.py
python apps/caresight-hub/scripts/v0_review_events.py list
python apps/caresight-hub/scripts/v0_review_events.py show <event_id>
python apps/caresight-hub/scripts/v0_review_events.py confirm <event_id> --reviewer <authorized-human> --note "<operator note>"
python apps/caresight-hub/scripts/v0_review_events.py journal <event_id>
python apps/caresight-hub/scripts/v0_review_events.py audit <event_id>
```

The operator may use `dismiss` instead of `confirm` when the authorized human determines the event should be dismissed.

## Required Evidence

Capture the terminal output proving:

- `event_persisted` appeared for one real `possible_floor_stay` dwell.
- The event row has `event_id`, `snapshot_path`, `status`, and timestamps.
- `event_observations` has at least one row for the event.
- `event_reviews` includes the authorized human reviewer and `reviewed_at`.
- `journal_entries` includes the human review note.
- `agent_handoffs` is `report_only` and includes reviewer, review ID, journal ID, reviewed timestamp, blocked actions, and `snapshot_path`.

## Boundaries

SQLite rows remain canonical. The audit command, agents, dashboards, LLM output, and scripts may inspect or summarize rows, but they must not confirm, dismiss, dispatch, diagnose, delete, or become reviewer of record.
