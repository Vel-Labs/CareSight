# Contract Lifecycle

Canonical project artifacts move through explicit states.

## States

```text
draft
  -> proposed
  -> accepted
  -> active
  -> deprecated
  -> retired
```

## State meaning

- `draft`: incomplete work that cannot be enforced.
- `proposed`: ready for review, not yet authoritative.
- `accepted`: approved as canonical truth, not yet required by runtime behavior.
- `active`: canonical truth that executable enforcement must honor.
- `deprecated`: still recognized, but should not be used for new work.
- `retired`: no longer valid for new work.

## Promotion rules

- `draft` may become `proposed` only when required fields and examples exist.
- `proposed` may become `accepted` only with a decision record or audit note.
- `accepted` may become `active` only after validation and focused tests pass.
- `active` may become `deprecated` only with a migration or follow-up note.
- `deprecated` may become `retired` only when downstream references have been removed or explicitly waived.

## Blocking rule

When lifecycle state is missing, unknown, or unsupported, consumers must fail closed.

## Care Event Review Transitions

Runtime review changes use a separate event-review lifecycle purpose so final state changes are not silent overwrites.

Allowed purposes:

- `initial_review`: first authorized human review of an awaiting event.
- `followup_note`: additional human context that does not silently replace the original review.
- `amendment`: explicit change to a previous review; must name the amended `review_id`.
- `correction`: human correction that keeps the prior state visible in the audit trail.

Allowed status transitions:

- `awaiting_human_confirmation` -> `human_confirmed`
- `awaiting_human_confirmation` -> `dismissed`
- `awaiting_human_confirmation` -> `needs_followup`
- `needs_followup` -> `human_confirmed`
- `needs_followup` -> `dismissed`
- `human_confirmed` -> `dismissed` only with `review_purpose=amendment`
- `dismissed` -> `human_confirmed` only with `review_purpose=amendment`

Every mutation must preserve `previous_status`, `review_purpose`, reviewer, timestamp, note when provided, and the amendment target when applicable.
