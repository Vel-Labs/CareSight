# CareSight Next Sprint: Master Codex Prompt

## Role

You are Codex working in the `Vel-Labs/CareSight` repository. Your job is to advance CareSight from a proven v0 blackbox care event loop into a polished, repeatable, local-first caregiver awareness sprint while preserving every current safety boundary.

You are not building a medical device. You are not building emergency dispatch. You are not building cloud surveillance. You are building a local care event engine that creates bounded records, drafts caregiver-friendly outputs, and lets authorized humans confirm, dismiss, journal, and escalate according to their family care plan.

## Current product shape to preserve

CareSight is a local-first care observation hub for families and broader caregiver ecosystems. The preferred product story is:

> CareSight turns a low-cost Apple Silicon Mac, local camera feeds, YOLO26 MLX, and a small local language layer into a home care blackbox. It observes configured events locally, stores non-destructive structured records in SQLite, drafts caregiver summaries, and offers bounded escalation paths such as local alerts, Apple Notes drafts, OBS/FaceTime handoff, and calm local TTS. It is designed for peace of mind around elders, children, pets, temporary caregivers, and home safety without defaulting to cloud video or unbounded surveillance.

The product must remain inspectable and boring:

```text
local camera frames
  -> YOLO26 MLX observations
  -> deterministic event policy
  -> SQLite blackbox records
  -> human review / acknowledgement
  -> journal and report-only handoff
  -> optional local draft/action adapters
```

## Non-negotiable laws

1. SQLite is canonical. Dashboard, alerts, notes, TTS, OBS, FaceTime, iMessage, and LLM outputs are derived.
2. Contracts come before behavior. Any new semantic shape belongs in `contracts/` first with valid and invalid examples.
3. Agents can summarize, draft, audit, and stage. Agents cannot confirm, dismiss, delete, diagnose, dispatch, or inspect raw video as decision-maker.
4. Vision may emit `possible_*` or `*_likely_observed` events. Vision must not confirm a fall, injury, medication ingestion, hydration completion, diagnosis, or medical state.
5. Human confirmation is required for review state changes.
6. Raw video stays local by default. Any snapshot must be local, event-scoped, and auditable.
7. No Ring/Nest/cloud camera adapters in this sprint.
8. No autonomous emergency dispatch.
9. No HIPAA compliance claim.
10. No biometric or face identity. Daily appearance profiles are temporary clothing/accessory continuity only.
11. No silent Apple Notes/iMessage/FaceTime actions. External-user-visible actions are draft-first or human-approved.
12. No OBS control exposed to LLMs except through an allow-listed CareSight action gateway.
13. No hard-coded machine-specific paths, account names, contacts, credentials, or reviewer names in source code.
14. Every new CLI command must be documented in `docs/cli/COMMANDS.md`.
15. Every behavior claim must have tests or an audit note.

## Hardware and model lane recommendation

Implement the sprint so it can run in three tiers:

### Tier A — Hackathon minimum / lowest-cost Mac pitch

- Apple Silicon Mac mini, 16GB unified memory.
- YOLO26n MLX for local vision.
- Gemma 4 E2B instruction-tuned 4-bit through MLX for local structured drafting.
- macOS `say` or pre-recorded audio for the first TTS demo; Kokoro-MLX loaded on demand only if memory is stable.
- Do not keep every model hot at once. The event loop owns vision; the LLM wakes after SQLite event insertion.

### Tier B — Recommended polished demo

- Mac mini M4 with 24GB or 32GB unified memory.
- YOLO26n MLX hot.
- Gemma 4 E4B instruction-tuned 4-bit through MLX for richer summaries.
- Kokoro-82M through MLX for calm TTS.
- OBS already open with Virtual Camera manually started.

### Tier C — Stretch / premium local product

- Mac mini M4 Pro with 48GB or 64GB unified memory.
- YOLO26n or YOLO26s MLX depending on FPS and confidence tradeoffs.
- Gemma 4 26B A4B 4-bit through MLX if latency is acceptable.
- TTS through Kokoro-MLX.
- Optional multi-camera and FaceTime/OBS demo.

The repo implementation must not require Tier C. Tier C is a premium story, not the core demo dependency.

## Required reading before code

Read these files before making changes:

```text
README.md
AGENTS.md
ROADMAP.md
DECISIONS.md
CHANGELOG.md
REPO_PROFILE.json
docs/project/PROJECT_BRIEF.md
docs/architecture/ARCHITECTURE.md
docs/architecture/REPO_BOUNDARIES.md
docs/architecture/bounded_control_loop.md
docs/architecture/obs_facetime_live_view.md
docs/roadmaps/CURRENT_STATE_AND_NEXT.md
docs/cli/COMMANDS.md
contracts/README.md
contracts/fail-closed-rules.md
contracts/lifecycle.md
contracts/llm-provider-contract.md
apps/caresight-hub/caresight/storage/sqlite_store.py
apps/caresight-hub/caresight/runtime/agents/policy.py
apps/caresight-hub/caresight/runtime/review/service.py
apps/caresight-hub/caresight/runtime/dashboard/service.py
apps/caresight-hub/caresight/runtime/alerts/service.py
```

## Sprint mission

Implement one integrated sprint with six workstreams:

1. Demo Surface Consolidation.
2. Agent/LLM Drafting Layer.
3. Daily Appearance Profiles.
4. Tracking Reliability Upgrade.
5. Multi-Camera Narrative Proof.
6. Routine Event Demo.

Each implementation sprint must absorb the contract pieces it consumes before runtime behavior. Keep `07-contract-json-pack.md` as a later contract continuity audit, not a standalone schema-copying sprint. The preferred execution order for separate Codex sessions is:

```text
01 demo surface consolidation
  -> 02 agent/LLM drafting layer
  -> 03 daily appearance profiles
  -> 04 tracking reliability upgrade
  -> 05 multi-camera narrative proof
  -> 06 routine event demo
  -> 07 contract continuity audit
  -> 08 README/product-shape refresh
```

Workstream order matters. Implement in this order unless a human explicitly overrides:

```text
contracts and examples
  -> deterministic storage/read models
  -> service logic
  -> CLI surfaces
  -> tests
  -> docs
  -> audit receipt
```

## Global implementation requirements

### Contracts

Add or update schemas only in `contracts/schemas/`.
Add valid examples in `contracts/examples/valid/`.
Add invalid examples in `contracts/examples/invalid/`.
Validation must include both positive and negative behavior.

Suggested new schemas:

```text
contracts/schemas/blackbox-receipt.schema.json
contracts/schemas/human-review-packet.schema.json
contracts/schemas/agent-draft.schema.json
contracts/schemas/agent-action-request.schema.json
contracts/schemas/appearance-profile.schema.json
contracts/schemas/tts-utterance.schema.json
```

Do not weaken existing schemas. If adding a new event type, update examples, tests, docs, and `DECISIONS.md` if authority changes.

### SQLite

SQLite remains source of truth. Prefer small migration files:

```text
apps/caresight-hub/caresight/storage/migrations/002_agent_drafts.sql
apps/caresight-hub/caresight/storage/migrations/003_appearance_profiles.sql
apps/caresight-hub/caresight/storage/migrations/004_action_requests.sql
```

If the current store reads only `001_init.sql`, add a migration runner rather than pasting all future schema into one giant SQL constant. The runner must be deterministic, idempotent, and covered by tests.

Suggested tables:

```sql
agent_drafts(
  draft_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  purpose TEXT NOT NULL,
  model_id TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  input_json TEXT NOT NULL,
  output_json TEXT NOT NULL,
  validation_status TEXT NOT NULL CHECK(validation_status IN ('valid','invalid','blocked')),
  created_at TEXT NOT NULL
);

action_requests(
  action_request_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  draft_id TEXT REFERENCES agent_drafts(draft_id) ON DELETE SET NULL,
  action_key TEXT NOT NULL,
  execution_class TEXT NOT NULL CHECK(execution_class IN ('report_only','human_approval_required','manual_operator')),
  status TEXT NOT NULL CHECK(status IN ('drafted','staged','human_approved','executed','blocked','failed')),
  payload_json TEXT NOT NULL,
  requested_by TEXT NOT NULL,
  approved_by TEXT,
  created_at TEXT NOT NULL,
  approved_at TEXT,
  executed_at TEXT
);

appearance_profiles(
  appearance_profile_id TEXT PRIMARY KEY,
  active_date TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  role_assignment TEXT NOT NULL,
  assignment_source TEXT NOT NULL,
  attributes_json TEXT NOT NULL,
  last_seen_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

appearance_profile_observations(
  observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  appearance_profile_id TEXT NOT NULL REFERENCES appearance_profiles(appearance_profile_id) ON DELETE CASCADE,
  event_id TEXT REFERENCES events(event_id) ON DELETE SET NULL,
  camera_id TEXT NOT NULL,
  track_id TEXT,
  observed_at TEXT NOT NULL,
  attributes_json TEXT NOT NULL,
  continuity_confidence REAL NOT NULL
);
```

### CLI

Every new CLI must be agent-safe by default. Mutating commands require human-review language and reviewer fields.

Suggested commands:

```bash
python apps/caresight-hub/scripts/care_console.py review-packet <event_id> --format json|markdown
python apps/caresight-hub/scripts/care_console.py blackbox-receipt <event_id> --format json|markdown --output <path>
python apps/caresight-hub/scripts/care_console.py draft-summary <event_id> --provider fake|gemma-mlx --format json
python apps/caresight-hub/scripts/care_console.py action-requests <event_id>
python apps/caresight-hub/scripts/care_console.py appearance-profile show <appearance_profile_id>
python apps/caresight-hub/scripts/care_console.py appearance-profile list --active-date YYYY-MM-DD
python apps/caresight-hub/scripts/care_console.py routine-demo <routine_id> --format json|markdown
```

Do not add a command that silently sends messages, silently appends Apple Notes, silently opens FaceTime, or silently switches OBS without a local action request record.

### Agent/LLM boundary

Build a CareSight-owned local drafting layer first. Treat OpenClaw/Hermes as optional downstream wrappers.

Allowed actions for LLM outputs:

```text
summarize_event
draft_caregiver_message
draft_journal_note
draft_apple_notes_entry
draft_handoff_packet
audit_handoff_payload
stage_tts_script
recommend_allowlisted_action
```

Forbidden actions:

```text
confirm_event
dismiss_event
delete_event
emergency_dispatch
diagnose
confirm_medication_taken
claim_hydration_completed
inspect_raw_video_for_decision
identify_named_person_from_vision
autonomously_send_imessage
autonomously_write_apple_note
autonomously_start_facetime
autonomously_control_obs_without_policy
```

### Draft prompt template

Use this prompt for local Gemma, fake provider tests, and future OpenClaw/Hermes wrapping:

```text
SYSTEM:
You are CareSight's local caregiver draft assistant. You are downstream of SQLite and deterministic event policy. You are not a doctor, dispatcher, reviewer, camera operator, or source of truth.

You may only use facts present in the provided JSON. You must not infer injury, medication ingestion, hydration completion, medical state, named identity, or emergency need. You must not request raw video. You must not execute actions. You produce draft JSON only.

DEVELOPER:
Return exactly one JSON object matching the requested schema. No markdown. No prose outside JSON. All user-visible wording must be calm, factual, and bounded. Include provenance.source_fields and safety_boundaries. If required fields are missing, return validation_status="blocked" and explain missing_fields.

USER:
Create a CareSight draft packet from this SQLite-backed audit chain:
<event_audit_chain_json>

Allowed output purposes:
<allowed_purposes>

Allowed action keys:
<allowed_action_keys>

Forbidden claims:
- fall confirmed
- injury detected
- medication taken
- hydration completed
- medical diagnosis
- emergency dispatch triggered
- named person identified from appearance
```

### Output validation

Do not trust LLM formatting. Always:

1. Parse JSON.
2. Validate against schema.
3. Verify `event_id` exists in SQLite.
4. Verify `source_fields` are in the allowed audit chain fields.
5. Verify no forbidden phrases or claims appear.
6. Verify requested actions are in the event's `allowed_actions` and CareSight action registry.
7. Store the draft and validation status in SQLite.
8. Return a local receipt.

### TTS boundary

TTS is output presentation only. It may speak a `tts_script` that has already passed draft validation. TTS may not decide what happened.

Default TTS ladder:

1. `fake_tts` in tests.
2. macOS `say` or pre-recorded short line for minimal demo.
3. Kokoro-MLX for polished local TTS.

No unconsented voice cloning. No impersonating family members. Log all synthetic speech.

## Sprint acceptance criteria

The sprint is complete only if:

1. `npm run validate:contracts` passes.
2. `npm run test:focused` passes.
3. `npm test` passes.
4. `npm run typecheck` passes.
5. `npm run py:check` passes.
6. `npm run check` passes.
7. Every new CLI is documented in `docs/cli/COMMANDS.md`.
8. Every new safety decision is recorded in `DECISIONS.md`.
9. `CHANGELOG.md` includes the sprint changes.
10. A new audit file exists under `docs/audits/YYYY-MM-DD-<short-name>.md` with exact commands and observed output.
11. No generated output claims medical authority, emergency dispatch, medication ingestion, hydration completion, or biometric identity.
12. Stale demo rows are visible as backlog/audit records but never drive the focused proof view.

## Pasteable master Codex prompt

```text
You are Codex in Vel-Labs/CareSight. Implement the next CareSight sprint as a local-first, bounded caregiver awareness product. Preserve the existing architecture: contracts are canonical, packages/core validates contracts, apps/caresight-hub owns Python runtime, SQLite is source of truth, dashboard/alerts/agents are derived.

Read README.md, AGENTS.md, ROADMAP.md, DECISIONS.md, CHANGELOG.md, docs/project/PROJECT_BRIEF.md, docs/architecture/ARCHITECTURE.md, docs/architecture/REPO_BOUNDARIES.md, docs/roadmaps/CURRENT_STATE_AND_NEXT.md, docs/cli/COMMANDS.md, contracts/README.md, contracts/fail-closed-rules.md, contracts/lifecycle.md, and contracts/llm-provider-contract.md before editing.

Implement one scoped sprint in this order:
1. Demo Surface Consolidation.
2. Agent/LLM Drafting Layer.
3. Daily Appearance Profiles.
4. Tracking Reliability Upgrade.
5. Multi-Camera Narrative Proof.
6. Routine Event Demo.

Non-negotiables: no medical-device claims, no HIPAA claims, no autonomous emergency dispatch, no medication ingestion confirmation, no hydration completion claim, no raw-video cloud defaults, no Ring/Nest/cloud adapters, no biometric identity, no agent review authority, no silent external actions. Use possible/likely-observed language unless an authorized human has confirmed a review state. Keep stale events in audit backlog, not hidden or deleted.

Add contracts before behavior. Suggested schemas: blackbox-receipt, human-review-packet, agent-draft, agent-action-request, appearance-profile, tts-utterance. Add valid and invalid examples. Add or update deterministic tests. Add SQLite migrations through an idempotent migration runner if new tables are needed. Add CLI commands only if documented in docs/cli/COMMANDS.md and classified as agent-safe-read, human-review-required, or manual-operator.

For the LLM layer, implement a fake provider first and local Gemma MLX as optional. The LLM receives only SQLite-backed event JSON, audit chains, journal rows, review state, handoff payloads, and bounded appearance descriptors. It never sees raw video. It returns JSON drafts only. Validate, store, and audit every draft. It may propose allow-listed action requests, but action execution must go through CareSight policy and human approval when user-visible external channels are involved.

For tooling, implement a CareSight-owned action gateway before OpenClaw/Hermes wrappers. OpenClaw/Hermes may be future wrappers for iMessage, Apple Notes, OBS, FaceTime, or TTS, but they must never bypass CareSight policy. Apple Notes writes are draft-first; iMessage is draft/stage-first; FaceTime is a prompted handoff; OBS control is localhost/password-protected and allow-listed; TTS only speaks validated scripts.

Run and report: npm run validate:scaffold, npm run validate:contracts, npm run test:focused, npm test, npm run typecheck, npm run py:check, npm run check. Update DECISIONS.md, CHANGELOG.md, docs/roadmaps/CURRENT_STATE_AND_NEXT.md, docs/cli/COMMANDS.md, and a new docs/audits receipt. Do not claim success without command output evidence.
```
