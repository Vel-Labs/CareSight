# Sprint 02 — Agent/LLM Drafting Layer

## Goal

Add a local, constrained language layer that turns SQLite-backed event records into caregiver-friendly drafts without gaining authority over review decisions, raw video, external communication, or emergency escalation.

The LLM is not the care authority. The LLM is a wording assistant downstream of SQLite.

## Target architecture

```text
SQLite blackbox
  -> audit chain JSON
  -> local draft input validator
  -> fake provider for deterministic tests
  -> optional Gemma 4 MLX provider
  -> draft JSON validator
  -> agent_drafts SQLite row
  -> optional action_request row
  -> human review / Apple Notes draft / alert draft / OBS / FaceTime / TTS
```

OpenClaw/Hermes are optional wrappers after this layer exists. They must not bypass CareSight policy.

## Model recommendation

Use a tiered model selector so the demo can run on modest Apple hardware:

```json
{
  "default_minimum": "mlx-community/gemma-4-e2b-it-4bit",
  "preferred_demo": "mlx-community/gemma-4-e4b-it-4bit",
  "premium_stretch": "mlx-community/gemma-4-26b-a4b-it-4bit",
  "test_provider": "fake"
}
```

Guidance:

- Use Gemma 4 E2B 4-bit as default for 16GB Mac mini.
- Use Gemma 4 E4B 4-bit for the recommended 24GB/32GB Mac mini demo.
- Use Gemma 4 26B A4B 4-bit only on higher-memory M4 Pro or better hardware.
- Keep the LLM event-driven; do not run continuous LLM inference alongside vision.
- The LLM should not receive snapshots or raw frames in v1/v2.
- Use a fake provider first for tests and reproducible CI.

## Non-goals

- No raw video inspection.
- No image-to-text summarization from snapshots in this sprint.
- No autonomous Apple Notes writes.
- No autonomous iMessage sends.
- No autonomous FaceTime call starts.
- No autonomous OBS control from LLM output.
- No emergency dispatch.
- No medical diagnosis.
- No medication ingestion or hydration completion claims.
- No named person identification.

## Required contracts

Add `contracts/schemas/agent-draft.schema.json`.

Core shape:

```json
{
  "schema": "agent-draft",
  "draft_id": "draft_evt_abc123_001",
  "event_id": "evt_abc123",
  "created_at": "2026-05-20T00:00:00Z",
  "provider": "gemma-mlx",
  "model_id": "mlx-community/gemma-4-e2b-it-4bit",
  "prompt_version": "caregiver-draft-v1",
  "validation_status": "valid",
  "purpose": "caregiver_summary_packet",
  "outputs": {
    "caregiver_summary": "A possible floor-stay event was confirmed in the Living Room. The local record includes a snapshot, human review, journal entry, and report-only handoff.",
    "apple_notes_entry": "CareSight confirmed a possible floor-stay event in the Living Room. Reviewed by an authorized human. No autonomous emergency dispatch or medical diagnosis was performed.",
    "alert_draft": "CareSight confirmed a possible floor-stay event in the Living Room. Please review the local record and follow your care plan.",
    "handoff_packet": "SQLite-backed event evt_abc123 is human_confirmed and ready for caregiver review.",
    "tts_script": "CareSight recorded a possible safety event in the Living Room. A caregiver review is available."
  },
  "recommended_action": {
    "action_key": "stage_caregiver_alert",
    "reason": "High-severity human-confirmed event has a validated alert draft."
  },
  "missing_fields": [],
  "safety_boundaries": [
    "draft_only",
    "human_review_required",
    "no_autonomous_dispatch",
    "no_medical_diagnosis",
    "no_raw_video_access"
  ],
  "blocked_actions": [
    "confirm_event",
    "dismiss_event",
    "delete_event",
    "emergency_dispatch",
    "diagnose",
    "confirm_medication_taken",
    "claim_hydration_completed",
    "identify_named_person_from_vision"
  ],
  "not_claimed": [
    "fall_confirmed",
    "injury_detected",
    "medication_taken",
    "hydration_completed",
    "medical_state",
    "named_identity"
  ],
  "provenance": {
    "source": "sqlite_audit_chain",
    "source_fields": [
      "event.event_id",
      "event.event_type",
      "event.status",
      "event.occurred_at",
      "event.camera_id",
      "event.zone_id",
      "event.evidence",
      "event_observations.track_id",
      "event_reviews",
      "journal_entries",
      "agent_handoffs"
    ]
  }
}
```

Add `contracts/schemas/agent-action-request.schema.json`.

Core shape:

```json
{
  "schema": "agent-action-request",
  "action_request_id": "action_evt_abc123_001",
  "event_id": "evt_abc123",
  "draft_id": "draft_evt_abc123_001",
  "action_key": "stage_apple_notes_entry",
  "execution_class": "human_approval_required",
  "status": "staged",
  "created_at": "2026-05-20T00:00:00Z",
  "requested_by": "local_agent_draft",
  "approved_by": null,
  "payload": {
    "title": "CareSight Event evt_abc123",
    "body": "Draft note text goes here.",
    "target": "apple_notes_draft"
  },
  "requires_human_approval": true,
  "blocked_without_approval": true,
  "provenance": {
    "source": "agent_drafts",
    "source_fields": ["draft_id", "event_id", "outputs.apple_notes_entry"]
  }
}
```

Add `contracts/schemas/tts-utterance.schema.json`.

Core shape:

```json
{
  "schema": "tts-utterance",
  "utterance_id": "tts_evt_abc123_001",
  "event_id": "evt_abc123",
  "draft_id": "draft_evt_abc123_001",
  "created_at": "2026-05-20T00:00:00Z",
  "engine": "kokoro-mlx",
  "voice_id": "calm_default",
  "script": "CareSight recorded a possible safety event in the Living Room. A caregiver review is available.",
  "consent_boundary": "synthetic_default_voice_only",
  "status": "staged",
  "provenance": {
    "source": "validated_agent_draft",
    "source_fields": ["outputs.tts_script"]
  }
}
```

Invalid examples must prove:

- draft claims medication was taken
- draft claims injury or diagnosis
- draft requests emergency dispatch
- draft has no provenance
- action request writes Apple Notes without human approval
- TTS utterance uses cloned/familiar voice without consent flag

## LLM provider contract

Add valid contract:

```text
contracts/examples/valid/gemma-local-mlx.llm-provider.json
```

Suggested JSON:

```json
{
  "schema": "llm-provider",
  "id": "gemma-local-mlx",
  "lifecycle": "proposed",
  "provider": "Gemma Local MLX",
  "mode": "local",
  "ownedBy": "apps/caresight-hub/runtime/llm_drafts",
  "authority": {
    "canonicalSource": "contracts/",
    "implementationBoundary": "apps/caresight-hub/"
  },
  "environmentVariables": [
    {
      "name": "CARESIGHT_GEMMA_MODEL",
      "required": false,
      "secret": false,
      "purpose": "Optional Hugging Face model id or local model path for the Gemma MLX provider."
    },
    {
      "name": "CARESIGHT_GEMMA_ENDPOINT",
      "required": false,
      "secret": false,
      "purpose": "Optional local OpenAI-compatible MLX endpoint."
    }
  ],
  "modelDefaults": {
    "model": "mlx-community/gemma-4-e2b-it-4bit",
    "maxOutputTokens": 800,
    "contextWindowTokens": 8192
  },
  "safety": {
    "fakeFallbackRequired": true,
    "forbidSecretLogging": true,
    "forbidAutonomousExternalActions": true
  },
  "manualGates": [
    "human approval before Apple Notes writes",
    "human approval before iMessage sends",
    "operator prompt before FaceTime handoff",
    "policy allow-list before OBS scene switch",
    "human review before event confirmation or dismissal"
  ]
}
```

## Runtime modules

Add:

```text
apps/caresight-hub/caresight/runtime/llm_drafts/__init__.py
apps/caresight-hub/caresight/runtime/llm_drafts/provider.py
apps/caresight-hub/caresight/runtime/llm_drafts/fake_provider.py
apps/caresight-hub/caresight/runtime/llm_drafts/gemma_mlx_provider.py
apps/caresight-hub/caresight/runtime/llm_drafts/prompts.py
apps/caresight-hub/caresight/runtime/llm_drafts/service.py
apps/caresight-hub/caresight/runtime/llm_drafts/validation.py
apps/caresight-hub/caresight/runtime/actions/__init__.py
apps/caresight-hub/caresight/runtime/actions/registry.py
apps/caresight-hub/caresight/runtime/actions/service.py
apps/caresight-hub/caresight/runtime/tts/__init__.py
apps/caresight-hub/caresight/runtime/tts/service.py
```

Provider interface:

```python
from typing import Protocol, Any

class DraftProvider(Protocol):
    provider_id: str
    model_id: str

    def generate_json(self, *, prompt: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        ...
```

Fake provider:

- Deterministic.
- No network.
- Returns valid draft JSON from known audit chain fields.
- Can be configured in tests to return forbidden phrases or malformed JSON.

Gemma MLX provider:

- Optional.
- If endpoint env var exists, call local OpenAI-compatible endpoint.
- If no endpoint exists, optionally shell out to local MLX command only when explicitly requested.
- Do not fail the whole repo if Gemma is unavailable.
- Do not download models inside tests.
- Do not log prompts containing private caregiver notes unless explicitly in a local audit artifact.

## Draft service behavior

`DraftService.create_event_draft(event_id, purposes, provider="fake")` must:

1. Read audit chain from `ReviewService.get_audit_chain(event_id)`.
2. Build input JSON using only allowed fields.
3. Build prompt from `prompts.py`.
4. Call provider.
5. Parse JSON.
6. Validate schema.
7. Run forbidden-claim scan.
8. Run action allow-list scan.
9. Insert `agent_drafts` row with `validation_status`.
10. Optionally insert `action_requests` row for a recommended action.
11. Return draft receipt.

If output is invalid, insert `validation_status="blocked"` and return blockers. Do not silently repair unsafe output.

## Action registry

Create a small registry:

```python
ACTION_REGISTRY = {
    "stage_caregiver_alert": {
        "execution_class": "report_only",
        "requires_human_approval": False,
        "adapter": "care_console_alert_draft"
    },
    "stage_apple_notes_entry": {
        "execution_class": "human_approval_required",
        "requires_human_approval": True,
        "adapter": "apple_notes_draft"
    },
    "stage_imessage_text": {
        "execution_class": "human_approval_required",
        "requires_human_approval": True,
        "adapter": "imessage_draft"
    },
    "prepare_facetime_handoff": {
        "execution_class": "manual_operator",
        "requires_human_approval": True,
        "adapter": "facetime_url"
    },
    "switch_obs_event_scene": {
        "execution_class": "manual_operator",
        "requires_human_approval": True,
        "adapter": "obs_localhost_websocket"
    },
    "stage_tts_script": {
        "execution_class": "report_only",
        "requires_human_approval": False,
        "adapter": "local_tts"
    }
}
```

Rules:

- Agents may request but not execute.
- Human approval is required for external-user-visible writes/sends/calls.
- OBS scene switch may be operator-approved for demo but must log action request.
- FaceTime handoff must acknowledge macOS user prompt.

## CLI

Add:

```bash
python apps/caresight-hub/scripts/care_console.py draft-summary <event_id> --provider fake|gemma-mlx --format json
python apps/caresight-hub/scripts/care_console.py action-requests <event_id>
python apps/caresight-hub/scripts/care_console.py tts-script <event_id> --provider fake|gemma-mlx --format json
```

Do not add direct `send-imessage`, `write-note`, or `start-facetime` commands in this sprint unless they only stage an action request.

## Tests

Add:

```text
apps/caresight-hub/tests/test_llm_drafts.py
apps/caresight-hub/tests/test_action_registry.py
apps/caresight-hub/tests/test_tts_service.py
```

Required cases:

1. Fake provider returns valid draft and stores `agent_drafts` row.
2. Draft input excludes raw video and snapshot image bytes.
3. Draft includes provenance and source fields.
4. Draft with “medication taken” is blocked.
5. Draft with “injury detected” is blocked.
6. Draft with “emergency dispatch triggered” is blocked.
7. Unknown action key is blocked.
8. Apple Notes action request requires human approval.
9. iMessage action request requires human approval.
10. FaceTime action request is manual-operator.
11. TTS script is derived from validated draft only.
12. Missing event id fails without mutation.
13. `gemma-mlx` provider unavailable returns clear blocker without breaking `npm run check`.

## Prompt text to store in code

```text
You are CareSight's local caregiver draft assistant.

Authority boundary:
- SQLite is the source of truth.
- Human reviewers confirm or dismiss events.
- You draft only.

Evidence boundary:
- Use only the JSON fields supplied.
- Do not request raw video.
- Do not invent unseen facts.

Forbidden claims:
- Do not say a fall was confirmed unless the event status is human_confirmed, and even then say the human confirmed the CareSight event, not a medical fall diagnosis.
- Do not say injury detected.
- Do not say medication was taken.
- Do not say hydration completed.
- Do not diagnose.
- Do not identify a named person from appearance.
- Do not say emergency dispatch occurred or is required.

Output boundary:
- Return one JSON object only.
- Match the agent-draft schema.
- Include safety_boundaries, blocked_actions, not_claimed, and provenance.
- Use calm, factual, caregiver-friendly language.
```

## Documentation

Update:

```text
docs/agents/AGENT_BOUNDARIES.md
docs/cli/COMMANDS.md
docs/integrations/LLM_PROVIDER_INTEGRATION.md
docs/roadmaps/CURRENT_STATE_AND_NEXT.md
CHANGELOG.md
DECISIONS.md
docs/audits/YYYY-MM-DD-agent-llm-drafting-layer.md
```

## Definition of done

- Fake provider path fully works and passes tests.
- Local Gemma MLX provider is documented and optional.
- Drafts are schema-validated, stored, and auditable.
- Unsafe drafts are blocked and stored as blocked, not silently ignored.
- Action requests are staged, not executed.
- TTS scripts are staged from validated drafts only.
- `npm run check` passes without local Gemma installed.

## Pasteable Codex prompt

```text
Implement Sprint 02 Agent/LLM Drafting Layer. Add contracts for agent-draft, agent-action-request, and tts-utterance with valid and invalid examples. Add a proposed gemma-local-mlx llm-provider contract. Implement a CareSight-owned llm_drafts runtime with fake provider first, optional Gemma MLX provider second, prompt builder, validator, and SQLite persistence. Add an action registry that stages action requests and never executes external actions silently. Add TTS script staging from validated drafts only. Add care_console.py draft-summary, action-requests, and tts-script commands. The LLM receives only SQLite audit-chain JSON and bounded descriptors; no raw video or image bytes. Tests must prove provenance, storage, forbidden-claim blocking, human-approval requirements, and provider-unavailable fallback. Update docs, decisions, changelog, CLI registry, and audit receipt. Run npm run check.
```
