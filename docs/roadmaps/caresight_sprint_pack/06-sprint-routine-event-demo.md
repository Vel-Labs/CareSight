# Sprint 06 — Routine Event Demo

## Goal

Demonstrate medication and hydration routine events without overclaiming.

CareSight should show that deterministic policy can observe a likely routine context:

```text
person + object label + routine zone + routine window
  -> medication_routine_likely_observed
  -> human review packet
  -> journal language
  -> caregiver alert draft
```

It must not claim medication was taken or hydration was completed.

## Product value

Families and care workers often need reassurance that a routine was likely observed in the right place and time. CareSight can create a helpful checkpoint while keeping the final interpretation with humans.

## Current event names to preserve

```text
medication_routine_likely_observed
hydration_routine_likely_observed
```

Do not rename these to `medication_taken`, `pill_ingested`, `hydration_complete`, or similar.

## Allowed language

```text
Medication routine likely observed near the configured medication station.
Hydration routine likely observed near the configured hydration zone.
The local record needs human confirmation.
CareSight observed person + object-label context during the routine window.
```

## Forbidden language

```text
Medication was taken.
Dose was administered.
Pill identified.
Hydration completed.
Resident drank water.
Medical compliance confirmed.
Health status improved.
```

## Contract checks

Existing `care-event.schema.json` already includes routine event types. Add additional valid examples if needed:

```text
contracts/examples/valid/medication-routine.review-packet.json
contracts/examples/valid/hydration-routine.review-packet.json
contracts/examples/valid/medication-routine.agent-draft.json
contracts/examples/valid/hydration-routine.agent-draft.json
```

Invalid examples:

```text
contracts/examples/invalid/medication-routine-claims-taken.json
contracts/examples/invalid/hydration-routine-claims-completed.json
contracts/examples/invalid/medication-routine-autoconfirmed-by-vision.json
```

## Routine policy evidence

Routine event evidence should include:

```json
{
  "raw_video_stays_local": true,
  "routine_id": "morning_medication",
  "routine_window": "13:00-15:00",
  "person_label": "person",
  "person_confidence": 0.82,
  "object_label": "bottle",
  "object_confidence": 0.61,
  "zone_id": "medication_station",
  "camera_id": "kitchen_counter",
  "room_id": "kitchen",
  "room_name": "Kitchen",
  "wording": "likely observed",
  "requires_human_confirmation": true,
  "not_claimed": [
    "specific_medication_taken",
    "medication_administered",
    "medical_compliance",
    "hydration_completed",
    "medical_state"
  ],
  "policy_version": "routine_v1_likely_observed"
}
```

## Review packet wording

Medication packet:

```text
CareSight observed a person and a configured object-label signal in the medication station during the morning medication routine window. This is a likely-observed routine event, not proof that medication was taken. Human confirmation is required.
```

Hydration packet:

```text
CareSight observed a person and a configured hydration object-label signal in the hydration zone during the configured routine window. This is a likely-observed routine event, not proof that hydration was completed. Human confirmation is required.
```

## Journal wording

When awaiting review:

```text
CareSight recorded a medication routine likely observed event in Kitchen. The event is awaiting human confirmation. CareSight did not confirm medication ingestion, dose, or medical compliance.
```

When human confirmed:

```text
An authorized human confirmed the CareSight medication routine likely observed event. This confirmation records review of the CareSight event, not a medical claim that medication was ingested.
```

## Alert draft wording

```text
CareSight routine note: medication routine likely observed near Kitchen medication station. Please review the local record and confirm or dismiss according to your care plan. CareSight did not confirm medication was taken.
```

## Demo CLI

Add one of these paths:

### Option A — read-only demo packet from seeded event

```bash
python apps/caresight-hub/scripts/care_console.py routine-demo medication --format markdown
python apps/caresight-hub/scripts/care_console.py routine-demo hydration --format markdown
```

This uses deterministic fixture events and does not need camera.

### Option B — live routine check

```bash
python apps/caresight-hub/scripts/v1_routine_live.py --routine-id morning_medication --max-seconds 120 --stop-after-event
```

This is manual-operator and should only be added if stable.

Recommendation: implement Option A first for hackathon reliability. Keep live routine policy tests as deterministic.

## LLM draft integration

When Agent/LLM Drafting Layer exists, routine events should be draftable with strict claim blocking.

Required LLM draft fields:

```json
{
  "outputs": {
    "caregiver_summary": "Medication routine likely observed in Kitchen during the configured routine window. Human review is required.",
    "apple_notes_entry": "CareSight recorded medication_routine_likely_observed. This does not confirm medication ingestion.",
    "alert_draft": "Medication routine likely observed. Please review the local record.",
    "tts_script": "CareSight recorded a routine event that needs caregiver review."
  },
  "not_claimed": ["medication_taken", "hydration_completed", "medical_compliance"]
}
```

Any LLM output containing these phrases should be blocked:

```text
medication was taken
pill was taken
dose was administered
hydration completed
person drank
medical compliance confirmed
```

## Tests

Add or extend:

```text
apps/caresight-hub/tests/test_routine_events.py
apps/caresight-hub/tests/test_demo_surface.py
apps/caresight-hub/tests/test_llm_drafts.py
```

Required cases:

1. Medication event requires person + configured object label + configured zone + routine window.
2. Hydration event requires person + configured hydration object label + configured zone + routine window.
3. No event outside routine window.
4. No event without person.
5. No event without object evidence.
6. Event status is `awaiting_human_confirmation`.
7. Event blocked actions include medication confirmation without authorized human and medical diagnosis.
8. Review packet says likely observed, not taken/completed.
9. Journal says likely observed, not taken/completed.
10. Alert draft says review required.
11. LLM draft claiming medication taken is blocked.
12. LLM draft claiming hydration completed is blocked.

## Docs

Update:

```text
docs/cli/COMMANDS.md
docs/roadmaps/CURRENT_STATE_AND_NEXT.md
docs/hackathon/demo_script.md
CHANGELOG.md
docs/audits/YYYY-MM-DD-routine-event-demo.md
```

Decision note if needed:

```text
Routine events remain likely-observed care context. Human confirmation confirms review of the CareSight event, not medication ingestion, hydration completion, or medical compliance.
```

## Definition of done

- Medication and hydration demo packets exist.
- Demo wording never overclaims.
- Routine event tests pass.
- LLM claim-blocking covers routine events.
- CLI docs include routine demo command.
- `npm run check` passes.

## Pasteable Codex prompt

```text
Implement Sprint 06 Routine Event Demo. Preserve event names medication_routine_likely_observed and hydration_routine_likely_observed. Add or update contract examples and invalid examples proving the system never claims medication taken, dose administered, hydration completed, or medical compliance. Add a stable care_console.py routine-demo command that renders medication and hydration review packets from deterministic fixtures or existing SQLite records. Keep live routine capture optional/manual-operator only. Update review packet, journal, alert, and LLM draft wording to say likely observed and human review required. Tests must cover person+object+zone+window requirements, awaiting_human_confirmation status, blocked actions, safe wording, and LLM forbidden-claim blocking. Update docs, changelog, demo script, CLI registry, and audit receipt. Run npm run check.
```
