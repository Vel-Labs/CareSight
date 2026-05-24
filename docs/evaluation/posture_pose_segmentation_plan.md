# Posture, Pose, Depth, and Segmentation Evaluation Plan

Date: 2026-05-24

CareSight currently uses YOLO-box geometry as the baseline posture signal. Pose, depth, and segmentation candidates are advisory evidence only until measured local receipts show value beyond the existing `laying_low_possible` and `seated_on_floor_possible` boundary.

## Candidate Interface

Candidate outputs must preserve:

- `authority: advisory_only`
- `claim_boundary: cannot_confirm_fall_or_injury`
- source model manifest ID
- local validation command
- scenario label
- false-positive/false-negative notes

## Scenario Matrix

Compare candidates against the baseline on:

- seated-on-floor non-event
- lying-low calibrated floor-zone event
- couch or recliner non-floor context
- low light
- partial-body visibility
- multi-person scenes

## Promotion Rule

No product claim changes until the candidate has a model manifest, deterministic fixture tests, and local evaluation receipts. Advisory evidence cannot by itself create a stronger event type, confirm a fall, infer injury, diagnose, or trigger dispatch.
