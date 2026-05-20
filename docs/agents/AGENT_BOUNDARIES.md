# CareSight Agent Boundaries

Agents may help with structured CareSight records, but they do not become the reviewer of record.

## Allowed

- Summarize structured event JSON.
- Draft caregiver wording.
- Draft journal-note text.
- Audit handoff payload completeness.

Every generated output needs:

- `purpose`
- `event_id`
- source fields used
- a clear draft/report-only boundary

## Forbidden

- Confirm an event.
- Dismiss an event.
- Delete records.
- Trigger emergency dispatch.
- Diagnose a person.
- Confirm medication was taken.
- Inspect raw video as the decision-maker.

## Runtime Enforcement

`caresight.runtime.agents.assert_agent_action_allowed` enforces the allowed action set and provenance requirements in deterministic tests.
