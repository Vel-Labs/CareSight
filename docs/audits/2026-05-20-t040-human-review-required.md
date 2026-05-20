# T040 Human Review Required

Date: 2026-05-20

GoalBuddy task: `T040`

## Current Fresh Event

Event ID:

```text
evt_cf80f63995794c98b8bd6ebc197bf73d
```

Snapshot path:

```text
apps/caresight-hub/data/snapshots/evt_cf80f63995794c98b8bd6ebc197bf73d.jpg
```

Snapshot file status:

```text
snapshot_present
```

## Current Boundary

The live event is persisted and read-only audit evidence exists, but the event is still:

```text
awaiting_human_confirmation
```

Agents must not confirm or dismiss events unless an authorized human explicitly instructs the exact action.

## Required Human Instruction

An authorized human must choose one of these exact review paths:

Confirm:

```sh
python3 apps/caresight-hub/scripts/v0_review_events.py confirm evt_cf80f63995794c98b8bd6ebc197bf73d --reviewer "<authorized human>" --note "<review note>"
```

Dismiss:

```sh
python3 apps/caresight-hub/scripts/v0_review_events.py dismiss evt_cf80f63995794c98b8bd6ebc197bf73d --reviewer "<authorized human>" --note "<review note>"
```

## After Review

After the authorized human review command succeeds, collect:

```sh
python3 apps/caresight-hub/scripts/v0_review_events.py audit evt_cf80f63995794c98b8bd6ebc197bf73d
python3 apps/caresight-hub/scripts/care_console.py dashboard
python3 apps/caresight-hub/scripts/care_console.py alert-draft evt_cf80f63995794c98b8bd6ebc197bf73d
python3 apps/caresight-hub/scripts/live_proof_audit.py bundle evt_cf80f63995794c98b8bd6ebc197bf73d --max-event-age-minutes 60
```

The goal may only complete if the final bundle reports `status: complete`.
