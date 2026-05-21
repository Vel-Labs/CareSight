# Sprint 03 — Daily Appearance Profiles

## Goal

Add non-biometric, local-only person continuity for caregiver context.

CareSight should help answer:

- “Who was last seen where?”
- “What was the resident-assigned profile wearing today?”
- “Was the likely same tracked person seen moving from the kitchen to the living room?”
- “What bounded description can a caregiver use during a stressful event?”

CareSight must not claim durable identity, face recognition, or biometric matching.

## Product value

Daily appearance profiles support family care without becoming surveillance identity infrastructure. They are useful for elders, children, visitors, temporary caregivers, pets-adjacent context, and multi-camera narratives. A caregiver under stress benefits from “resident-assigned profile for today, dark gray upper clothing, last seen in Living Room at 2:36 AM,” while the product avoids “this is Steven” unless a future explicit local enrollment feature is separately scoped.

## Core rule

Clothing and accessories are daily appearance memory, not identity.

Allowed language:

```text
likely same tracked person
resident-assigned profile for today
person wearing dark gray upper clothing
last seen in Living Room
human-assigned role: resident_primary
```

Forbidden language:

```text
this is Steven
face match
biometric identity
identity confirmed by clothing
resident identity verified
```

## Scope

Implement:

- Daily expiring appearance profiles.
- Conservative descriptor extraction from person observations.
- Human role assignment for the day.
- Links from observations/events to appearance profiles.
- Read-only CLI to inspect profiles.
- Dashboard inclusion as bounded context.

Defer:

- Face recognition.
- Long-term identity enrollment.
- Cloud image upload.
- Re-identification across days.
- Global person database.

## Required contract

Add `contracts/schemas/appearance-profile.schema.json`.

Required shape:

```json
{
  "schema": "appearance-profile",
  "appearance_profile_id": "appearance_2026_05_20_001",
  "active_date": "2026-05-20",
  "expires_at": "2026-05-21T04:00:00Z",
  "role_assignment": "resident_primary",
  "assignment_source": "human_confirmed",
  "identity_boundary": "non_biometric_daily_appearance_only",
  "attributes": {
    "upper_body_color": { "value": "dark gray", "confidence": 0.78 },
    "lower_body_color": { "value": "gray", "confidence": 0.70 },
    "eyewear": { "value": "glasses", "confidence": 0.64 },
    "headwear": { "value": "none", "confidence": 0.58 },
    "carried_object": { "value": "none", "confidence": 0.40 }
  },
  "last_seen": {
    "camera_id": "living_room",
    "room": "Living Room",
    "timestamp": "2026-05-20T02:36:31Z",
    "event_id": "evt_d9aa38bdc636459c92ea4e25f665cd0d",
    "track_id": "track_5"
  },
  "continuity": {
    "claim": "likely_same_tracked_person",
    "confidence": 0.72,
    "basis": ["same_day", "track_continuity", "clothing_color_similarity"]
  },
  "forbidden_claims": [
    "biometric_identity",
    "face_recognition",
    "named_person_identification",
    "cross_day_identity"
  ]
}
```

Allowed `role_assignment` enum:

```text
resident_primary
resident_secondary
caregiver_known
visitor_unknown
unknown_person
pet_context
```

Allowed `assignment_source` enum:

```text
unassigned
human_confirmed
operator_demo_seed
care_plan_config
```

Invalid examples:

- profile with `identity_boundary = biometric_identity`
- profile with `role_assignment = Steven`
- profile with `expires_at` more than 24 hours after active-date cutoff unless config explicitly allows it
- profile that claims `face_match`

## SQLite migration

Add:

```text
apps/caresight-hub/caresight/storage/migrations/003_appearance_profiles.sql
```

Suggested tables:

```sql
CREATE TABLE IF NOT EXISTS appearance_profiles (
  appearance_profile_id TEXT PRIMARY KEY,
  active_date TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  role_assignment TEXT NOT NULL,
  assignment_source TEXT NOT NULL,
  identity_boundary TEXT NOT NULL,
  attributes_json TEXT NOT NULL,
  last_seen_json TEXT NOT NULL,
  continuity_json TEXT NOT NULL,
  forbidden_claims_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS appearance_profile_observations (
  observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  appearance_profile_id TEXT NOT NULL REFERENCES appearance_profiles(appearance_profile_id) ON DELETE CASCADE,
  event_id TEXT REFERENCES events(event_id) ON DELETE SET NULL,
  camera_id TEXT NOT NULL,
  room TEXT,
  track_id TEXT,
  observed_at TEXT NOT NULL,
  bbox_json TEXT NOT NULL,
  attributes_json TEXT NOT NULL,
  continuity_confidence REAL NOT NULL
);
```

Add indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_appearance_profiles_active_date ON appearance_profiles(active_date);
CREATE INDEX IF NOT EXISTS idx_appearance_profiles_expires_at ON appearance_profiles(expires_at);
CREATE INDEX IF NOT EXISTS idx_appearance_observations_event_id ON appearance_profile_observations(event_id);
CREATE INDEX IF NOT EXISTS idx_appearance_observations_track_id ON appearance_profile_observations(track_id);
```

## Runtime modules

Add:

```text
apps/caresight-hub/caresight/runtime/appearance/__init__.py
apps/caresight-hub/caresight/runtime/appearance/descriptors.py
apps/caresight-hub/caresight/runtime/appearance/profiles.py
apps/caresight-hub/caresight/runtime/appearance/service.py
apps/caresight-hub/caresight/runtime/appearance/render.py
```

Descriptor extraction should be deterministic and conservative.

### Minimal descriptor extraction

For hackathon scope, use person bounding box crop and simple color bands:

```text
upper body band: y 15% to 50% inside person box
lower body band: y 50% to 90% inside person box
ignore face-specific features
ignore skin tone
ignore exact body measurements
map average/median HSV to coarse color buckets
```

Color buckets:

```text
black
white
gray
dark gray
light gray
red
orange
yellow
green
blue
purple
brown
unknown
```

Do not store raw crop images unless explicitly event snapshot storage already exists and is local. Store descriptors, confidence, and provenance only.

### Continuity scoring

Use conservative scoring:

```text
same track_id within active window: strong signal
same camera and short time gap: medium signal
cross-camera same-day clothing similarity: weak-to-medium signal
human role assignment: label only, not identity proof
```

Never let clothing similarity alone produce a high-confidence identity claim.

Suggested function:

```python
def score_profile_match(profile: dict, observation_descriptor: dict, *, track_id: str | None, camera_id: str, observed_at: str) -> dict:
    return {
        "claim": "likely_same_tracked_person",
        "confidence": 0.0,
        "basis": []
    }
```

Maximum confidence rules:

- same `track_id` and same day: max 0.85
- clothing-only same camera: max 0.65
- clothing-only cross-camera: max 0.55
- expired profile: 0.0 and no match
- conflicting role assignment: max 0.40

## Config

Add to `apps/caresight-hub/config/v0.local.json` or runtime config model:

```json
{
  "appearance_profiles": {
    "enabled": true,
    "active_window_hours": 18,
    "expire_at_local_hour": 4,
    "min_match_confidence": 0.55,
    "allow_cross_camera_likely_continuity": true,
    "forbid_biometric_identity": true,
    "forbid_cross_day_matching": true
  }
}
```

Default should be enabled for deterministic tests but safe if no frame image is available. If image/crop is unavailable, create no descriptor rather than hallucinating.

## CLI

Add:

```bash
python apps/caresight-hub/scripts/care_console.py appearance-profile list --active-date 2026-05-20
python apps/caresight-hub/scripts/care_console.py appearance-profile show appearance_2026_05_20_001
python apps/caresight-hub/scripts/care_console.py appearance-profile assign-role appearance_2026_05_20_001 --role resident_primary --reviewer "Human Name"
```

Safety classes:

- `list`: agent-safe-read
- `show`: agent-safe-read
- `assign-role`: human-review-required

Role assignment must reject automation-like reviewer names.

## Dashboard addition

Add bounded appearance context to event-focused dashboard:

```json
{
  "appearance_context": {
    "identity_boundary": "non_biometric_daily_appearance_only",
    "profile_id": "appearance_2026_05_20_001",
    "role_assignment": "resident_primary",
    "assignment_source": "human_confirmed",
    "summary": "Resident-assigned profile for today; dark gray upper clothing; last seen in Living Room at 02:36.",
    "forbidden_claims": ["named_person_identification", "face_recognition", "biometric_identity"]
  }
}
```

## Tests

Add:

```text
apps/caresight-hub/tests/test_appearance_profiles.py
```

Required cases:

1. Creates profile with daily expiration.
2. Rejects biometric identity boundary.
3. Rejects named person role assignment.
4. Stores descriptors without raw image bytes.
5. Links profile to event and track id.
6. Same-track same-day match is allowed.
7. Expired profile does not match.
8. Cross-day matching is blocked.
9. Clothing-only cross-camera confidence is capped.
10. Role assignment requires authorized human reviewer.
11. Dashboard appearance context includes forbidden claims.
12. LLM draft input may include bounded appearance descriptor but not raw crop or named identity.

## Docs

Update:

```text
docs/architecture/ARCHITECTURE.md
docs/architecture/REPO_BOUNDARIES.md
docs/cli/COMMANDS.md
docs/roadmaps/CURRENT_STATE_AND_NEXT.md
CHANGELOG.md
DECISIONS.md
docs/audits/YYYY-MM-DD-daily-appearance-profiles.md
```

Decision note should say:

```text
CareSight daily appearance profiles are non-biometric, same-day, local descriptors for caregiver continuity. They do not identify named people and do not persist identity across days.
```

## Definition of done

- Appearance profile schema validates.
- Invalid biometric/named identity examples fail validation.
- Profiles expire by default.
- Dashboard and LLM draft input use bounded language.
- Human role assignment is recorded with reviewer and timestamp.
- `npm run check` passes.

## Pasteable Codex prompt

```text
Implement Sprint 03 Daily Appearance Profiles. Add a non-biometric appearance-profile contract with valid and invalid examples. Add SQLite migration and runtime services for same-day expiring appearance profiles, descriptor extraction, conservative continuity scoring, human role assignment, and read-only dashboard context. Do not implement face recognition, named identity, cross-day identity, or raw crop storage. Add care_console.py appearance-profile list/show/assign-role commands with assign-role human-review-required. Tests must prove expiration, no biometric identity, no named role claims, descriptor storage, event/track linking, cross-day blocking, confidence caps, and dashboard bounded language. Update docs, decisions, changelog, CLI registry, and audit note. Run npm run check.
```
