# Agent Policy Boundaries Audit

Date: 2026-05-19

## Scope

This audit records the constrained agent/LLM layer for CareSight.

## Implemented

- Added deterministic agent policy helper under `caresight/runtime/agents/`.
- Added allowed actions for summaries, caregiver-message drafts, journal-note drafts, and handoff audits.
- Added forbidden actions for confirmation, dismissal, deletion, dispatch, diagnosis, medication-taken confirmation, and raw-video decision access.
- Added provenance and purpose requirements for agent outputs.
- Added docs in `docs/agents/AGENT_BOUNDARIES.md`.

## Deterministic Checks

Run:

```bash
npm run py:check
npm run check
```

Expected:

- `test_agent_policy.py` proves allowed actions need purpose and provenance.
- `test_agent_policy.py` proves forbidden actions raise policy errors.
