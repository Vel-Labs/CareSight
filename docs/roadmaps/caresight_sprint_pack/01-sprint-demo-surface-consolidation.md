# Sprint 01 — Demo Surface Consolidation

## Goal

Make the proof story clean, repeatable, and judge-ready while preserving the audit backlog.

The current demo already proved the essential blackbox loop:

```text
possible_floor_stay
  -> local event inbox
  -> human-readable summary
  -> authorized human confirm/dismiss
  -> SQLite status update
  -> journal row
  -> report-only handoff row
```

This sprint turns that proof into a focused, boring, repeatable demo surface.

## Product reason

Judges and caregivers should not need to understand the whole database to trust the system. They should see one selected event, the evidence chain, the human review, the journal entry, the caregiver alert draft, and the blocked actions. Older awaiting-review rows should remain visible as audit backlog but not confuse the focused proof story.

## Non-goals

- Do not delete stale events.
- Do not auto-dismiss stale events.
- Do not make dashboard state canonical.
- Do not hide unresolved concerns entirely.
- Do not add external message sending.
- Do not add medical/emergency language.

## Expected user story

A judge can run:

```bash
python3 apps/caresight-hub/scripts/care_console.py dashboard --event-id evt_d9aa38bdc636459c92ea4e25f665cd0d
python3 apps/caresight-hub/scripts/care_console.py review-packet evt_d9aa38bdc636459c92ea4e25f665cd0d --format markdown
python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt evt_d9aa38bdc636459c92ea4e25f665cd0d --format markdown --output docs/audits/demo-blackbox-receipt.md
```

The outputs should clearly show:

- event id
- event type
- event status
- camera and room
- zone
- timestamp
- severity and confidence
- track id
- local snapshot path when present
- observations count
- reviews count
- journal count
- agent handoffs count
- reviewer and review decision when present
- blocked actions
- provenance source: SQLite
- derived surfaces: dashboard, alert draft, review packet, receipt

## Required contracts

Add `contracts/schemas/human-review-packet.schema.json`.

Required shape:

```json
{
  "schema": "human-review-packet",
  "packet_id": "review_packet_evt_abc123",
  "event_id": "evt_abc123",
  "event_type": "possible_floor_stay",
  "status": "awaiting_human_confirmation",
  "created_at": "2026-05-20T00:00:00Z",
  "source_of_truth": "sqlite",
  "summary": {
    "headline": "Possible floor-stay event in Living Room",
    "bounded_language": true,
    "requires_human_confirmation": true
  },
  "evidence": {
    "camera_id": "living_room",
    "room": "Living Room",
    "zone_id": "floor_zone",
    "track_ids": ["track_5"],
    "snapshot_path": "apps/caresight-hub/data/snapshots/evt_abc123.jpg",
    "observation_count": 1
  },
  "review_state": {
    "review_count": 0,
    "latest_reviewer": null,
    "latest_decision": null
  },
  "available_human_actions": ["confirm", "dismiss", "needs_followup"],
  "blocked_actions": ["autonomous_emergency_dispatch", "medical_diagnosis"],
  "provenance": {
    "source": "sqlite_audit_chain",
    "source_fields": ["events", "event_observations", "event_reviews", "journal_entries", "agent_handoffs"]
  }
}
```

Add `contracts/schemas/blackbox-receipt.schema.json`.

Required shape:

```json
{
  "schema": "blackbox-receipt",
  "receipt_id": "receipt_evt_abc123",
  "event_id": "evt_abc123",
  "created_at": "2026-05-20T00:00:00Z",
  "source_of_truth": "sqlite",
  "completion_status": "complete",
  "event": {
    "event_type": "possible_floor_stay",
    "status": "human_confirmed",
    "occurred_at": "2026-05-20T02:36:31Z",
    "camera_id": "living_room",
    "zone_id": "floor_zone",
    "severity": "high",
    "confidence": "high"
  },
  "counts": {
    "observations": 1,
    "reviews": 1,
    "journal_entries": 1,
    "agent_handoffs": 1
  },
  "track_ids": ["track_5"],
  "human_review": {
    "reviewer": "Steven",
    "decision": "human_confirmed",
    "reviewed_at": "2026-05-20T02:38:02Z"
  },
  "derived_outputs": {
    "dashboard_includes_event": true,
    "alert_draft_has_provenance": true
  },
  "blocked_actions": ["autonomous_emergency_dispatch", "medical_diagnosis"],
  "safety_boundaries": ["raw_video_local", "human_review_required", "no_autonomous_dispatch", "no_medical_diagnosis"]
}
```

Add valid examples:

```text
contracts/examples/valid/human-review-packet.possible-floor-stay.json
contracts/examples/valid/blackbox-receipt.possible-floor-stay.json
```

Add invalid examples:

```text
contracts/examples/invalid/blackbox-receipt-emergency-dispatch.json
contracts/examples/invalid/human-review-packet-missing-provenance.json
contracts/examples/invalid/blackbox-receipt-claims-diagnosis.json
```

## Runtime implementation

Add service module:

```text
apps/caresight-hub/caresight/runtime/demo_surface/__init__.py
apps/caresight-hub/caresight/runtime/demo_surface/review_packet.py
apps/caresight-hub/caresight/runtime/demo_surface/blackbox_receipt.py
```

Expected service functions:

```python
def build_human_review_packet(audit_chain: dict) -> dict: ...
def build_blackbox_receipt(audit_chain: dict, dashboard_state: dict | None = None, alert_draft: dict | None = None) -> dict: ...
def render_review_packet_markdown(packet: dict) -> str: ...
def render_blackbox_receipt_markdown(receipt: dict) -> str: ...
```

Rules:

- Read from `ReviewService.get_audit_chain(event_id)`.
- Never mutate SQLite.
- Never synthesize missing observation/review/journal/handoff rows as success.
- Mark `completion_status` as `not_complete` when required rows are missing.
- Include `blockers` array for missing pieces.
- Preserve `track_id` where present.
- Use `raw_video_local`, not `raw_video_available`.

## Dashboard changes

Update `build_dashboard_state(...)` so focused mode is explicit:

```json
{
  "view": {
    "mode": "focused_event",
    "requested_event_id": "evt_...",
    "focused_event_found": true
  },
  "focused_event": { "event_id": "evt_..." },
  "awaiting_review_backlog": {
    "count": 4,
    "events": [
      { "event_id": "evt_old", "status": "awaiting_human_confirmation", "age_label": "stale_demo_backlog" }
    ]
  }
}
```

Existing `timeline`, `concerns`, `journal_preview`, and `caregiver_alert_draft` may remain, but the top-level shape should make clear which event is being demonstrated.

## CLI changes

Update `apps/caresight-hub/scripts/care_console.py` with:

```bash
review-packet <event_id> --format json|markdown --output <path optional>
blackbox-receipt <event_id> --format json|markdown --output <path optional>
```

Behavior:

- Default format: JSON.
- `--output` writes a local file and prints the path plus `source_of_truth=sqlite`.
- Without `--output`, print to stdout.
- These commands are `agent-safe-read`.
- They must not confirm, dismiss, delete, dispatch, or call external tools.

## Tests

Add or update:

```text
apps/caresight-hub/tests/test_demo_surface.py
apps/caresight-hub/tests/test_care_console.py
```

Test cases:

1. Review packet includes event id, event type, status, track id, blocked actions, and SQLite provenance.
2. Review packet for missing event raises `KeyError` or CLI exits non-zero without mutation.
3. Blackbox receipt is `complete` when event + observation + review + journal + handoff exist.
4. Blackbox receipt is `not_complete` when review missing.
5. Blackbox receipt refuses to mark emergency dispatch as allowed.
6. Dashboard focused mode returns selected event even when older awaiting-review rows exist.
7. Awaiting-review backlog remains visible but separate.
8. Markdown render includes “SQLite is source of truth” and “No autonomous emergency dispatch”.

## Docs to update

```text
docs/cli/COMMANDS.md
docs/roadmaps/CURRENT_STATE_AND_NEXT.md
CHANGELOG.md
DECISIONS.md only if authority semantics change
docs/audits/YYYY-MM-DD-demo-surface-consolidation.md
```

## Definition of done

- A clean demo can be run from one selected event id.
- Stale awaiting-review rows are visible but not driving the focused proof view.
- One Markdown blackbox receipt can be exported for the proof event.
- All new outputs identify SQLite as source of truth.
- `npm run check` passes.

## Pasteable Codex prompt

```text
Implement Sprint 01 Demo Surface Consolidation. Preserve SQLite as source of truth and keep dashboard/alert/review-packet/receipt as derived read-only outputs. Add human-review-packet and blackbox-receipt schemas with valid and invalid examples. Add demo_surface runtime services that read ReviewService audit chains and produce JSON/Markdown. Add care_console.py review-packet and blackbox-receipt commands with optional --output. Update dashboard state to explicitly separate focused_event from awaiting_review_backlog. Do not delete or dismiss stale rows. Do not add external actions. Tests must prove complete and not_complete receipts, focused dashboard behavior, provenance, and blocked actions. Update docs/cli/COMMANDS.md, CURRENT_STATE_AND_NEXT.md, CHANGELOG.md, and add an audit note with exact commands and outputs. Run npm run check and report results.
```
