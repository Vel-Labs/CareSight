# v0 Review and Acknowledgement

Status: implemented for local CLI and SQLite lifecycle checks.

## Goal

Prove the first credible agent-ready care loop without allowing an agent to overstep:

```text
possible_floor_stay event
  -> local event inbox
  -> human-readable summary
  -> human confirm/dismiss
  -> SQLite status update
  -> journal entry
  -> agent-ready handoff record
```

## Scope

- `v0_review_events.py list` shows awaiting events by default.
- `v0_review_events.py show <event_id>` renders deterministic human-readable text.
- `confirm` and `dismiss` require `--reviewer`.
- Confirm/dismiss update `events.status`.
- Confirm/dismiss create `event_reviews`, `journal_entries`, and report-only `agent_handoffs` rows.
- Agent handoff payloads include blocked actions and the human-confirmation requirement.

## Out of Scope

- Autonomous emergency dispatch.
- Medical diagnosis.
- Agent-initiated confirmation or dismissal.
- Live caregiver messaging adapters.
- Autonomous agent execution hooks.

## Future Hooks to Document Before Implementation

- `event_created`
- `event_reviewed`
- `journal_entry_created`
- `agent_handoff_created`
- `caregiver_message_drafted`

## Future Skills to Document Before Implementation

- `event-reviewer`
- `care-journal-writer`
- `caregiver-message-drafter`
- `agent-handoff-auditor`
- `privacy-boundary-checker`

## Completion Criteria

- A floor-stay event is generated.
- A human can list/show it from CLI.
- A human can confirm or dismiss it.
- SQLite records the review.
- A human-readable journal entry exists.
- An agent-ready handoff payload can be generated.
- All commands are documented in `docs/cli/COMMANDS.md`.
- Lifecycle transitions have tests.
