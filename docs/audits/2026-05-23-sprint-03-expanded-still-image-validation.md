# Sprint 03 Expanded Still-Image Validation Recovery

Date: 2026-05-23

Scope: actual local still-image descriptor runs for Sprint 03 Daily Appearance Profiles. This receipt uses existing local CareSight snapshot files and SQLite bounding boxes. It does not commit third-party media, identify a person, or prove production readiness.

Machine-readable run summary:

```text
apps/caresight-hub/config/appearance-still-image-validation-runs.example.json
```

Human visual/reference matrix:

```text
docs/audits/2026-05-23-sprint-03-04-visual-reference-matrix.md
```

Correction after visual review: the first matrix was too weak because it listed descriptor outputs without showing the selected person bbox or sampled descriptor subregions. The recovery path now uses `caresight_yolo26_appearance_review.py` for YOLO26-detected person candidates and `care_console.py appearance-profile describe-image --visual-output` for event/manual bboxes. Horizontal low-posture boxes are now posture-limited and use horizontal body-axis subregions; outputs still require visual review because this is geometry-based sampling, not a true pose/attribute model.

## Commands

Template used for each run:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/care_console.py appearance-profile describe-image LOCAL_IMAGE_PATH --bbox X1,Y1,X2,Y2 --visual-output LOCAL_ANNOTATION_PATH
```

Representative run:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python apps/caresight-hub/scripts/care_console.py appearance-profile describe-image \
  apps/caresight-hub/data/snapshots/evt_65d6ef11826a40898a0fa4f3acb34aba.jpg \
  --bbox 304.32,277.57,1280.0,712.98 \
  --visual-output apps/caresight-hub/data/appearance-validation/annotated/s03-local-004.png
```

Result summary from the local run set:

| Case | Coverage | Difficulty | Status | Descriptor result |
| --- | --- | --- | --- | --- |
| s03-local-001 | near, large low/floor box | medium | posture_limited | body-region red; lower/headwear/footwear unknown |
| s03-local-002 | partial body, mid-distance low/floor box | medium | posture_limited | body-region brown only |
| s03-local-003 | cropped, low-quality, bottom-truncated | hard | unavailable | safe failure, no invented descriptors |
| s03-local-004 | large near low/floor box | medium | posture_limited | body-region blue; lower/headwear/footwear unknown |
| s03-local-005 | partial, low confidence low/floor box | hard | posture_limited | body-region red only |
| s03-local-006 | YOLO26-selected prone/low person candidate | hard | posture_limited | upper/body-region blue, lower cream; headwear/footwear unknown; visual review required |
| s03-local-007 | cropped-left, near low/floor box | hard | posture_limited | body-region red only |
| s03-local-008 | small/far low-posture box | hard | posture_limited | body-region red only |
| s03-local-009 | far low/floor box | medium | posture_limited | body-region brown only |
| s03-local-010 | small/far, low confidence low/floor box | hard | posture_limited | body-region dark gray only |
| s03-source-011 | sourced crowded street image, broad manual bbox | hard | available | upper/lower blue, headwear dark gray, footwear gray |

## Coverage

Covered:

- low/floor-posture boxes with posture-limited body-region sampling
- partial-body and cropped boxes
- near, mid-distance, and far/smaller boxes
- bottom-truncated boxes
- low-quality safe failure
- fail-closed headwear/lower/footwear behavior when a horizontal posture makes those regions unjustified
- confidence and descriptor-status recording
- multi-person/crowded source-backed stress case from Wikimedia Commons

Source-backed crowded run:

```bash
curl -L --fail --silent --show-error \
  -o /private/tmp/caresight-street-crowd.jpg \
  'https://commons.wikimedia.org/wiki/Special:Redirect/file/Street_Crowd.jpg'

apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/care_console.py appearance-profile describe-image \
  /private/tmp/caresight-street-crowd.jpg \
  --bbox 220,120,920,840
```

The observed source page is `https://commons.wikimedia.org/wiki/File:Street_Crowd.jpg`, with license observed as CC0 1.0. The downloaded image remained under `/private/tmp` and was not committed.

YOLO26 visual review command shape:

```bash
apps/caresight-hub/vendor/yolo-mlx/.venv/bin/python \
  apps/caresight-hub/scripts/caresight_yolo26_appearance_review.py \
  apps/caresight-hub/data/snapshots/evt_7cb67a46193e4b4f8420ca0f428e3635.jpg \
  --output-dir apps/caresight-hub/data/appearance-validation/annotated/s03-local-006
```

Generated local visual evidence for each local matrix row: `/Users/steven/Workspace/40_Code/hackathons/CareSight/apps/caresight-hub/data/appearance-validation/annotated/s03-local-001.png` through `s03-local-010.png`.

Generated YOLO26 visual evidence for `s03-local-006`: `/Users/steven/Workspace/40_Code/hackathons/CareSight/apps/caresight-hub/data/appearance-validation/annotated/s03-local-006/person-01-living_room_2026-05-23T17:30:56.396185Z_0.png`.

Remaining gap: broader internet-media validation is still operator-owned if more source variety is needed.

## Boundary

This proves bounded descriptor behavior on actual local image inputs. It does not prove identity, face recognition, cross-day matching, medical state, confirmed fall, emergency dispatch, caregiver message readiness, or production camera readiness.

## Validation

```bash
python3 -m json.tool apps/caresight-hub/config/appearance-still-image-validation-runs.example.json >/dev/null
```

Expected result: valid JSON.
