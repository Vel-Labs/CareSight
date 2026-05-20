# Care Console Dashboard and Alert Audit

Date: 2026-05-19

## Scope

This audit records the local presentation surface for dashboard state, concern feed, journal preview, and caregiver alert drafts.

## Implemented

- Added `care_console.py dashboard` for a local JSON dashboard read model.
- Added `care_console.py alert-draft <event_id>` for caregiver alert draft text.
- Routed dashboard state through `ReviewService`.
- Kept delete and dispatch marked forbidden in review controls.
- Added provenance fields for alert drafts.

## Boundaries

- SQLite remains the source of truth.
- Dashboard code does not directly mutate SQLite.
- Alert drafts are report-only and require human review.
- No autonomous emergency dispatch, diagnosis, or deletion is exposed.

## Deterministic Checks

Run:

```bash
npm run py:check
npm run check
```

Expected:

- `test_care_console.py` verifies the dashboard read model, review-control boundaries, and alert provenance.
