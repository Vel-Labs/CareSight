# Sprint 04 Complexity-Graded Validation Recovery

Date: 2026-05-23

Scope: deterministic recovery validation for tracking reliability. This receipt supplements the earlier Sprint 04 tracking-reliability receipt with named complexity cases and test commands.

Human visual/reference matrix:

```text
docs/audits/2026-05-23-sprint-03-04-visual-reference-matrix.md
```

## Complexity Matrix

| Target | Difficulty | Tested outcome | Deterministic proof |
| --- | --- | --- | --- |
| Same-track dwell | baseline | Emits `possible_floor_stay` only after the same tracked person reaches dwell threshold. | `test_emits_possible_floor_stay_after_person_dwells_in_floor_zone` |
| Escalation stages | medium | Same-track dwell maps to early/prolonged/critical concern stages without changing into a fall or medical claim. | `test_emits_prolonged_and_critical_escalation_stages_from_same_track_dwell` |
| Track churn | hard | No event; a shifted/new track cannot inherit the old track dwell timer. | `test_different_track_cannot_inherit_floor_stay_dwell_when_same_track_required` |
| Short occlusion | medium | Event still emits after a brief missing interval within the occlusion grace window. | `test_same_track_survives_short_occlusion_before_dwell_event` |
| Long occlusion reset | medium | No event; disappearance beyond the grace window resets dwell. | `test_long_occlusion_resets_floor_stay_dwell` |
| Dedupe window | baseline | First event emits; repeated event during the same dwell is suppressed. | `test_does_not_emit_repeated_events_during_same_dwell` |
| Distance / box scale | hard | Small/far low-posture candidate can emit bounded `possible_floor_stay` with no fall claim. | `test_complexity_grade_far_small_low_posture_can_emit_bounded_event` |
| Multi-person selection | hard | Emits from the low-posture floor candidate, not the higher-confidence standing person. | `test_complexity_grade_multiple_people_uses_floor_candidate_not_standing_person` |
| Standing false positive | hard | No event; diagnostic reports person detected but not a floor-stay candidate. | `test_complexity_grade_far_standing_person_remains_non_event` |
| Seated/desk false positive | hard | No event for a seated/desk-like posture. | `test_seated_desk_posture_does_not_emit_floor_stay` |
| Missing off-camera check-in | baseline | Emits check-in stage language only after configured missing window. | `test_emits_after_known_track_is_missing_for_configured_window` |
| Missing off-camera attention | medium | Emits attention stage after recent concern, still without identity/danger/dispatch claim. | `test_attention_language_after_recent_concern` |
| Missing off-camera urgent handoff | hard | Emits urgent-handoff wording for human review, not autonomous emergency dispatch. | `test_urgent_handoff_language_after_recent_high_concern` |

These were deterministic tests using synthetic detection boxes and policy state. They were not replay tests over previous camera feeds. The feed-replay/live gate remains separate and operator-owned.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s apps/caresight-hub/tests -t apps/caresight-hub -p 'test_floor_stay.py'
```

Expected result after recovery: passed, 12 tests OK.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s apps/caresight-hub/tests -t apps/caresight-hub -p 'test_missing_off_camera.py'
```

Expected result after recovery: passed, 5 tests OK.

```bash
npm run py:check
npm run check
```

Expected result: passed.

## Boundary

This is deterministic simulation/test evidence, not live-camera production validation. It does not confirm a fall, identify a person, diagnose danger, trigger dispatch, send messages, open FaceTime, play TTS, or mutate review status.

The remaining live gate is still the operator-owned bounded run documented in `docs/cli/COMMANDS.md`:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/v0_floor_stay_live.py \
  --camera-id living_room \
  --debug-floor-stay \
  --max-seconds 90 \
  --stop-after-event \
  --no-window
```
