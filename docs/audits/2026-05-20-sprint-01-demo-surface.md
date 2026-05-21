# Sprint 01 Demo Surface Audit

Date: 2026-05-20

## Scope

Sprint 01 added contract-backed, read-only demo surfaces for the proven CareSight live proof event:

- `human-review-packet`
- `blackbox-receipt`
- focused dashboard mode with separate awaiting-review backlog

These surfaces are derived from SQLite audit-chain records through `ReviewService`. They do not confirm, dismiss, delete, dispatch, diagnose, or create events.

## Contract Evidence

Added schemas:

- `contracts/schemas/human-review-packet.schema.json`
- `contracts/schemas/blackbox-receipt.schema.json`

Added examples:

- `contracts/examples/valid/human-review-packet.possible-floor-stay.json`
- `contracts/examples/valid/blackbox-receipt.possible-floor-stay.json`
- `contracts/examples/invalid/human-review-packet-missing-provenance.json`
- `contracts/examples/invalid/blackbox-receipt-emergency-dispatch.json`
- `contracts/examples/invalid/blackbox-receipt-claims-diagnosis.json`

Command:

```bash
npm run validate:contracts
```

Observed result:

```text
Contract validation passed: 10 schema(s), 12 valid example(s), 9 invalid example(s).
```

## Runtime Evidence

Command:

```bash
npm run py:check
```

Observed result:

```text
Ran 68 tests in 0.853s
OK
```

## Demo Command Evidence

Target event:

```text
evt_d9aa38bdc636459c92ea4e25f665cd0d
```

### Focused dashboard

Command:

```bash
python3 apps/caresight-hub/scripts/care_console.py dashboard --event-id evt_d9aa38bdc636459c92ea4e25f665cd0d
```

Observed key fields:

```json
{
  "source_of_truth": "sqlite",
  "view": {
    "mode": "focused_event",
    "requested_event_id": "evt_d9aa38bdc636459c92ea4e25f665cd0d",
    "focused_event_found": true
  },
  "focused_event": {
    "event_id": "evt_d9aa38bdc636459c92ea4e25f665cd0d",
    "event_type": "possible_floor_stay",
    "status": "human_confirmed"
  },
  "awaiting_review_backlog": {
    "count": 4
  }
}
```

Interpretation: the focused proof event is shown separately from stale awaiting-review backlog rows.

### Human review packet

Command:

```bash
python3 apps/caresight-hub/scripts/care_console.py review-packet evt_d9aa38bdc636459c92ea4e25f665cd0d --format json
```

Observed key fields:

```json
{
  "schema": "human-review-packet",
  "event_id": "evt_d9aa38bdc636459c92ea4e25f665cd0d",
  "source_of_truth": "sqlite",
  "status": "human_confirmed",
  "review_state": {
    "latest_decision": "human_confirmed",
    "latest_reviewer": "Steven",
    "review_count": 1
  },
  "evidence": {
    "track_ids": ["track_5"],
    "observation_count": 1
  },
  "provenance": {
    "source": "sqlite_audit_chain"
  }
}
```

### Blackbox receipt

Command:

```bash
python3 apps/caresight-hub/scripts/care_console.py blackbox-receipt evt_d9aa38bdc636459c92ea4e25f665cd0d --format json
```

Observed key fields:

```json
{
  "schema": "blackbox-receipt",
  "event_id": "evt_d9aa38bdc636459c92ea4e25f665cd0d",
  "source_of_truth": "sqlite",
  "completion_status": "complete",
  "counts": {
    "observations": 1,
    "reviews": 1,
    "journal_entries": 1,
    "agent_handoffs": 1
  },
  "human_review": {
    "reviewer": "Steven",
    "decision": "human_confirmed"
  },
  "derived_outputs": {
    "dashboard_includes_event": true,
    "alert_draft_has_provenance": true
  },
  "track_ids": ["track_5"]
}
```

## Boundaries Preserved

- SQLite remains canonical.
- Dashboard, packets, receipts, and alert drafts are derived outputs.
- Stale awaiting-review rows remain visible as backlog.
- Agents may run these read-only commands.
- Agents still may not confirm, dismiss, delete, dispatch, diagnose, or become reviewer of record.
- The full Sprint 07 agent/action/appearance/TTS schema pack remains deferred.

## Validation

Full command:

```bash
npm run check
```

Final observed result is recorded in the GoalBuddy task receipt for this sprint.
