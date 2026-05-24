# Review Commands

Review commands read or mutate local SQLite event state. Agents may list, show, summarize, and render receipts. Confirm, dismiss, journal export decisions, and role assignment require a human.

## Agent-Safe Read

| Command | Purpose | Validation |
| --- | --- | --- |
| `python apps/caresight-hub/scripts/v0_review_events.py list` | Show the local event inbox. | `test_v0_review_events.py`. |
| `python apps/caresight-hub/scripts/v0_review_events.py show <event_id>` | Render a deterministic human-readable event summary. | `test_v0_review_events.py`. |
| `python apps/caresight-hub/scripts/v0_review_events.py journal <event_id>` | Show journal entries for an event. | `test_v0_review_events.py`. |
| `python apps/caresight-hub/scripts/v0_review_events.py audit <event_id>` | Show a read-only SQLite blackbox chain. | `test_v0_review_events.py`. |
| `python apps/caresight-hub/scripts/care_console.py dashboard` | Render a local dashboard read model from SQLite. | `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py review-packet <event_id> --format json` | Render a read-only human review packet. | `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py blackbox-receipt <event_id> --format json` | Render a read-only blackbox receipt. | `test_care_console.py` and demo-surface tests. |
| `python apps/caresight-hub/scripts/care_console.py alert-draft <event_id>` | Draft caregiver alert text with provenance. | `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile list --active-date YYYY-MM-DD` | List same-day non-biometric appearance profiles. | `test_appearance_profiles.py`, `test_sqlite_store.py`, `test_care_console.py`. |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile show <appearance_profile_id>` | Show one appearance profile. | Same as above. |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile list-samples <appearance_profile_id>` | Show retained appearance samples. | Same as above. |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile summarize-today --active-date YYYY-MM-DD` | Summarize same-day descriptor support ratios. | Same as above. |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile describe-image <local_image_path> --bbox X1,Y1,X2,Y2` | Describe clothing/accessory regions in a local image. | Same as above. |
| `apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/caresight_yolo26_appearance_review.py <image_path> --output-dir apps/caresight-hub/data/appearance-validation/annotated` | Run YOLO26 on a local still image and write visual descriptor annotations. | Local visual-review evidence only. |

## Human Review Required

| Command | Purpose | Gate |
| --- | --- | --- |
| `python apps/caresight-hub/scripts/v0_review_events.py confirm <event_id> --reviewer <name> --note "<note>" --review-purpose initial_review` | Record an authorized human confirmation. | Human reviewer required; automation-like names are rejected. |
| `python apps/caresight-hub/scripts/v0_review_events.py dismiss <event_id> --reviewer <name> --note "<note>" --review-purpose initial_review` | Record an authorized human dismissal. | Human reviewer required; automation-like names are rejected. |
| `python apps/caresight-hub/scripts/care_console.py journal-redact <event_id> --journal-id <journal_id> --export-classification local-only` | Preview local redaction before export/share. | Human export/review decision; privacy filters are aids, not guarantees. |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile assign-role <appearance_profile_id> --role resident_primary --reviewer <name>` | Assign a bounded same-day role. | Human reviewer required. |

## Manual Operator

| Command | Purpose | Boundary |
| --- | --- | --- |
| `python apps/caresight-hub/scripts/care_console.py appearance-profile derive-from-event <event_id>` | Write local appearance rows from an existing event and snapshot. | Local-only, non-biometric, same-day appearance context. |

Review mutations are persisted through `ReviewService` and SQLite review, journal, and report-only handoff rows. There are no commands for deletion, autonomous emergency dispatch, diagnosis, or agent-owned acknowledgement.
