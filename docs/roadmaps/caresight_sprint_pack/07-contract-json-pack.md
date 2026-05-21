# CareSight Contract Continuity Audit Pack

This file consolidates contract shapes that are absorbed by the implementation sprints that consume them. Do not treat this as a standalone schema-copying sprint.

Use it as a continuity audit after the relevant implementation layers exist:

- Sprint 01 owns `blackbox-receipt` and `human-review-packet`.
- Sprint 02 owns `agent-draft`, `agent-action-request`, `tts-utterance`, and forbidden claim/action vocabulary.
- Sprint 03 owns `appearance-profile`.

The Sprint 07 job is to verify continuity across schemas, examples, validators, runtime outputs, CLI docs, audit receipts, and safety vocabulary.

## 1. `blackbox-receipt.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://project-governance-scaffold.local/schemas/blackbox-receipt.schema.json",
  "title": "BlackboxReceipt",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema",
    "receipt_id",
    "event_id",
    "created_at",
    "source_of_truth",
    "completion_status",
    "event",
    "counts",
    "blocked_actions",
    "safety_boundaries"
  ],
  "properties": {
    "schema": { "const": "blackbox-receipt" },
    "receipt_id": { "type": "string", "pattern": "^receipt_[a-z0-9_-]+$" },
    "event_id": { "type": "string", "pattern": "^evt_[a-z0-9_-]+$" },
    "created_at": { "type": "string", "format": "date-time" },
    "source_of_truth": { "const": "sqlite" },
    "completion_status": { "type": "string", "enum": ["complete", "not_complete"] },
    "blockers": { "type": "array", "items": { "type": "string" } },
    "event": {
      "type": "object",
      "additionalProperties": false,
      "required": ["event_type", "status", "occurred_at", "camera_id", "severity", "confidence"],
      "properties": {
        "event_type": { "type": "string" },
        "status": { "type": "string" },
        "occurred_at": { "type": "string", "format": "date-time" },
        "camera_id": { "type": "string" },
        "zone_id": { "type": ["string", "null"] },
        "severity": { "type": "string", "enum": ["low", "medium", "high"] },
        "confidence": { "type": "string", "enum": ["low", "medium", "high"] }
      }
    },
    "counts": {
      "type": "object",
      "additionalProperties": false,
      "required": ["observations", "reviews", "journal_entries", "agent_handoffs"],
      "properties": {
        "observations": { "type": "integer", "minimum": 0 },
        "reviews": { "type": "integer", "minimum": 0 },
        "journal_entries": { "type": "integer", "minimum": 0 },
        "agent_handoffs": { "type": "integer", "minimum": 0 }
      }
    },
    "track_ids": {
      "type": "array",
      "uniqueItems": true,
      "items": { "type": "string" }
    },
    "human_review": {
      "type": ["object", "null"],
      "additionalProperties": false,
      "required": ["reviewer", "decision", "reviewed_at"],
      "properties": {
        "reviewer": { "type": "string" },
        "decision": { "type": "string", "enum": ["human_confirmed", "dismissed", "needs_followup"] },
        "reviewed_at": { "type": "string", "format": "date-time" }
      }
    },
    "derived_outputs": {
      "type": "object",
      "additionalProperties": true
    },
    "blocked_actions": {
      "type": "array",
      "minItems": 1,
      "contains": { "const": "autonomous_emergency_dispatch" },
      "items": { "type": "string" }
    },
    "safety_boundaries": {
      "type": "array",
      "minItems": 1,
      "contains": { "const": "human_review_required" },
      "items": { "type": "string" }
    }
  }
}
```

## 2. `human-review-packet.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://project-governance-scaffold.local/schemas/human-review-packet.schema.json",
  "title": "HumanReviewPacket",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema",
    "packet_id",
    "event_id",
    "event_type",
    "status",
    "created_at",
    "source_of_truth",
    "summary",
    "evidence",
    "review_state",
    "available_human_actions",
    "blocked_actions",
    "provenance"
  ],
  "properties": {
    "schema": { "const": "human-review-packet" },
    "packet_id": { "type": "string", "pattern": "^review_packet_[a-z0-9_-]+$" },
    "event_id": { "type": "string", "pattern": "^evt_[a-z0-9_-]+$" },
    "event_type": { "type": "string" },
    "status": { "type": "string" },
    "created_at": { "type": "string", "format": "date-time" },
    "source_of_truth": { "const": "sqlite" },
    "summary": {
      "type": "object",
      "additionalProperties": false,
      "required": ["headline", "bounded_language", "requires_human_confirmation"],
      "properties": {
        "headline": { "type": "string" },
        "bounded_language": { "const": true },
        "requires_human_confirmation": { "type": "boolean" }
      }
    },
    "evidence": {
      "type": "object",
      "additionalProperties": true,
      "required": ["camera_id", "observation_count"],
      "properties": {
        "camera_id": { "type": "string" },
        "room": { "type": ["string", "null"] },
        "zone_id": { "type": ["string", "null"] },
        "track_ids": { "type": "array", "items": { "type": "string" } },
        "snapshot_path": { "type": ["string", "null"] },
        "observation_count": { "type": "integer", "minimum": 0 }
      }
    },
    "review_state": {
      "type": "object",
      "additionalProperties": false,
      "required": ["review_count", "latest_reviewer", "latest_decision"],
      "properties": {
        "review_count": { "type": "integer", "minimum": 0 },
        "latest_reviewer": { "type": ["string", "null"] },
        "latest_decision": { "type": ["string", "null"] }
      }
    },
    "available_human_actions": {
      "type": "array",
      "items": { "type": "string", "enum": ["confirm", "dismiss", "needs_followup"] }
    },
    "blocked_actions": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string" }
    },
    "provenance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["source", "source_fields"],
      "properties": {
        "source": { "const": "sqlite_audit_chain" },
        "source_fields": { "type": "array", "minItems": 1, "items": { "type": "string" } }
      }
    }
  }
}
```

## 3. `agent-draft.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://project-governance-scaffold.local/schemas/agent-draft.schema.json",
  "title": "AgentDraft",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema",
    "draft_id",
    "event_id",
    "created_at",
    "provider",
    "model_id",
    "prompt_version",
    "validation_status",
    "purpose",
    "outputs",
    "safety_boundaries",
    "blocked_actions",
    "not_claimed",
    "provenance"
  ],
  "properties": {
    "schema": { "const": "agent-draft" },
    "draft_id": { "type": "string", "pattern": "^draft_[a-z0-9_-]+$" },
    "event_id": { "type": "string", "pattern": "^evt_[a-z0-9_-]+$" },
    "created_at": { "type": "string", "format": "date-time" },
    "provider": { "type": "string", "enum": ["fake", "gemma-mlx"] },
    "model_id": { "type": "string", "minLength": 2 },
    "prompt_version": { "type": "string", "minLength": 3 },
    "validation_status": { "type": "string", "enum": ["valid", "invalid", "blocked"] },
    "purpose": { "type": "string", "enum": ["caregiver_summary_packet", "apple_notes_entry", "alert_draft", "handoff_packet", "audit_summary", "tts_script"] },
    "outputs": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "caregiver_summary": { "type": "string" },
        "apple_notes_entry": { "type": "string" },
        "alert_draft": { "type": "string" },
        "handoff_packet": { "type": "string" },
        "audit_summary": { "type": "string" },
        "tts_script": { "type": "string" }
      }
    },
    "recommended_action": {
      "type": ["object", "null"],
      "additionalProperties": false,
      "required": ["action_key", "reason"],
      "properties": {
        "action_key": { "type": "string" },
        "reason": { "type": "string" }
      }
    },
    "missing_fields": { "type": "array", "items": { "type": "string" } },
    "safety_boundaries": {
      "type": "array",
      "minItems": 1,
      "contains": { "const": "draft_only" },
      "items": { "type": "string" }
    },
    "blocked_actions": {
      "type": "array",
      "minItems": 1,
      "contains": { "const": "emergency_dispatch" },
      "items": { "type": "string" }
    },
    "not_claimed": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string" }
    },
    "provenance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["source", "source_fields"],
      "properties": {
        "source": { "const": "sqlite_audit_chain" },
        "source_fields": { "type": "array", "minItems": 1, "items": { "type": "string" } }
      }
    }
  }
}
```

## 4. `agent-action-request.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://project-governance-scaffold.local/schemas/agent-action-request.schema.json",
  "title": "AgentActionRequest",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema",
    "action_request_id",
    "event_id",
    "action_key",
    "execution_class",
    "status",
    "created_at",
    "requested_by",
    "payload",
    "requires_human_approval",
    "blocked_without_approval",
    "provenance"
  ],
  "properties": {
    "schema": { "const": "agent-action-request" },
    "action_request_id": { "type": "string", "pattern": "^action_[a-z0-9_-]+$" },
    "event_id": { "type": "string", "pattern": "^evt_[a-z0-9_-]+$" },
    "draft_id": { "type": ["string", "null"], "pattern": "^draft_[a-z0-9_-]+$" },
    "action_key": {
      "type": "string",
      "enum": [
        "stage_caregiver_alert",
        "stage_apple_notes_entry",
        "stage_imessage_text",
        "prepare_facetime_handoff",
        "switch_obs_event_scene",
        "stage_tts_script"
      ]
    },
    "execution_class": { "type": "string", "enum": ["report_only", "human_approval_required", "manual_operator"] },
    "status": { "type": "string", "enum": ["drafted", "staged", "human_approved", "executed", "blocked", "failed"] },
    "created_at": { "type": "string", "format": "date-time" },
    "requested_by": { "type": "string" },
    "approved_by": { "type": ["string", "null"] },
    "payload": { "type": "object", "additionalProperties": true },
    "requires_human_approval": { "type": "boolean" },
    "blocked_without_approval": { "type": "boolean" },
    "provenance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["source", "source_fields"],
      "properties": {
        "source": { "type": "string", "enum": ["agent_drafts", "sqlite_audit_chain", "human_review"] },
        "source_fields": { "type": "array", "minItems": 1, "items": { "type": "string" } }
      }
    }
  },
  "allOf": [
    {
      "if": { "properties": { "action_key": { "enum": ["stage_apple_notes_entry", "stage_imessage_text", "prepare_facetime_handoff"] } }, "required": ["action_key"] },
      "then": { "properties": { "requires_human_approval": { "const": true }, "blocked_without_approval": { "const": true } } }
    }
  ]
}
```

## 5. `appearance-profile.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://project-governance-scaffold.local/schemas/appearance-profile.schema.json",
  "title": "AppearanceProfile",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema",
    "appearance_profile_id",
    "active_date",
    "expires_at",
    "role_assignment",
    "assignment_source",
    "identity_boundary",
    "attributes",
    "last_seen",
    "continuity",
    "forbidden_claims"
  ],
  "properties": {
    "schema": { "const": "appearance-profile" },
    "appearance_profile_id": { "type": "string", "pattern": "^appearance_[0-9]{4}_[0-9]{2}_[0-9]{2}_[a-z0-9_-]+$" },
    "active_date": { "type": "string", "format": "date" },
    "expires_at": { "type": "string", "format": "date-time" },
    "role_assignment": { "type": "string", "enum": ["resident_primary", "resident_secondary", "caregiver_known", "visitor_unknown", "unknown_person", "pet_context"] },
    "assignment_source": { "type": "string", "enum": ["unassigned", "human_confirmed", "operator_demo_seed", "care_plan_config"] },
    "identity_boundary": { "const": "non_biometric_daily_appearance_only" },
    "attributes": { "type": "object", "additionalProperties": { "$ref": "#/$defs/attribute" } },
    "last_seen": {
      "type": "object",
      "additionalProperties": false,
      "required": ["camera_id", "timestamp"],
      "properties": {
        "camera_id": { "type": "string" },
        "room": { "type": ["string", "null"] },
        "timestamp": { "type": "string", "format": "date-time" },
        "event_id": { "type": ["string", "null"], "pattern": "^evt_[a-z0-9_-]+$" },
        "track_id": { "type": ["string", "null"] }
      }
    },
    "continuity": {
      "type": "object",
      "additionalProperties": false,
      "required": ["claim", "confidence", "basis"],
      "properties": {
        "claim": { "type": "string", "enum": ["likely_same_tracked_person", "daily_profile_context", "unassigned_context"] },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "basis": { "type": "array", "items": { "type": "string" } }
      }
    },
    "forbidden_claims": {
      "type": "array",
      "minItems": 1,
      "contains": { "const": "biometric_identity" },
      "items": { "type": "string" }
    }
  },
  "$defs": {
    "attribute": {
      "type": "object",
      "additionalProperties": false,
      "required": ["value", "confidence"],
      "properties": {
        "value": { "type": "string" },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    }
  }
}
```

## 6. `tts-utterance.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://project-governance-scaffold.local/schemas/tts-utterance.schema.json",
  "title": "TtsUtterance",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema",
    "utterance_id",
    "event_id",
    "created_at",
    "engine",
    "voice_id",
    "script",
    "consent_boundary",
    "status",
    "provenance"
  ],
  "properties": {
    "schema": { "const": "tts-utterance" },
    "utterance_id": { "type": "string", "pattern": "^tts_[a-z0-9_-]+$" },
    "event_id": { "type": "string", "pattern": "^evt_[a-z0-9_-]+$" },
    "draft_id": { "type": ["string", "null"], "pattern": "^draft_[a-z0-9_-]+$" },
    "created_at": { "type": "string", "format": "date-time" },
    "engine": { "type": "string", "enum": ["fake", "macos_say", "kokoro-mlx"] },
    "voice_id": { "type": "string" },
    "script": { "type": "string", "minLength": 1, "maxLength": 500 },
    "consent_boundary": { "type": "string", "enum": ["synthetic_default_voice_only", "pre_recorded_generic", "explicit_voice_consent_recorded"] },
    "status": { "type": "string", "enum": ["drafted", "staged", "spoken", "blocked"] },
    "provenance": {
      "type": "object",
      "additionalProperties": false,
      "required": ["source", "source_fields"],
      "properties": {
        "source": { "type": "string", "enum": ["validated_agent_draft", "static_template", "human_authored"] },
        "source_fields": { "type": "array", "minItems": 1, "items": { "type": "string" } }
      }
    }
  }
}
```

## Forbidden phrase scanner seed list

Use this in Python validation as a supplement to JSON Schema:

```python
FORBIDDEN_CLAIM_PHRASES = {
    "fall confirmed",
    "fall detected",
    "injury detected",
    "injured",
    "medical emergency confirmed",
    "911 called",
    "emergency dispatch triggered",
    "medication was taken",
    "medicine was taken",
    "pill was taken",
    "dose was administered",
    "medication administered",
    "hydration completed",
    "person drank water",
    "medical compliance confirmed",
    "diagnosis",
    "identified as",
    "face match",
    "biometric identity"
}
```

Do not rely only on phrase scanning. Schema, action registry, provenance requirements, and event-state validation must also run.
