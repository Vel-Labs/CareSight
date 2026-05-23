# Sprint 03 Sourced Still-Image Validation Receipt

Date: 2026-05-23

## Scope

This receipt records a source-backed validation matrix for Sprint 03 Daily Appearance Profiles. It does not download, commit, crop, or redistribute third-party media. The matrix lives at:

```text
apps/caresight-hub/config/appearance-still-image-sources.example.json
```

The matrix is intended for operator-owned local checks of the existing read-only still-image harness:

```bash
python apps/caresight-hub/scripts/care_console.py appearance-profile describe-image LOCAL_IMAGE_PATH --bbox X1,Y1,X2,Y2
```

## Source Matrix

| Coverage | Candidate | Source | License observed |
| --- | --- | --- | --- |
| Headwear / hat | `HK people boy wearing hat September 2024 R12S 01.jpg` | `https://commons.wikimedia.org/wiki/File:HK_people_boy_wearing_hat_September_2024_R12S_01.jpg` | CC0 1.0 |
| Full outfit / street fashion | `Harajuku Fashion Street Snap (2018-01-08 18.18.29 by Dick Thomas Johnson).jpg` | `https://commons.wikimedia.org/wiki/File:Harajuku_Fashion_Street_Snap_(2018-01-08_18.18.29_by_Dick_Thomas_Johnson).jpg` | CC BY 2.0 |
| Upper clothing / red shirt | `Red shirt in Bangkok.JPG` | `https://commons.wikimedia.org/wiki/File:Red_shirt_in_Bangkok.JPG` | CC BY-SA 2.0 |
| Lower clothing / jeans | `Baggy jeans guy 1.jpg` | `https://commons.wikimedia.org/wiki/File:Baggy_jeans_guy_1.jpg` | CC BY-SA 4.0 |
| Footwear / sneakers | `Man in sneakers at beach (Unsplash).jpg` | `https://commons.wikimedia.org/wiki/File:Man_in_sneakers_at_beach_(Unsplash).jpg` | CC0 1.0 |
| Footwear / boots | `Brisbane, winter female street fashion in 2019; t-shirt, shorts and boots.jpg` | `https://commons.wikimedia.org/wiki/File:Brisbane,_winter_female_street_fashion_in_2019;_t-shirt,_shorts_and_boots.jpg` | CC BY-SA 4.0 |

## Operator Procedure

1. Review the source page and license terms before downloading media locally.
2. Download any selected image into an ignored local directory such as `apps/caresight-hub/data/appearance-validation/`.
3. Select a manual person bounding box for the visible person region.
4. Run `care_console.py appearance-profile describe-image` with the local image path and bounding box.
5. Record the command output and local path in a follow-up audit receipt if the validation run is used as proof.

## Expected Checks

- `describe-image` returns `schema: appearance-profile-still-image-descriptor`.
- `identity_boundary` remains `non_biometric_daily_appearance_only`.
- Upper clothing, lower clothing, headwear, and footwear are coarse color descriptors only.
- Blurry, cropped, occluded, or unsuitable boxes return unavailable or unknown descriptors rather than invented attributes.
- Standalone sourced still images do not create care events, assign roles, trigger caregiver messages, or confirm identity.

## Boundaries

This receipt does not prove live-camera Sprint 03 production readiness. It proves that the repo now has a durable, inspectable source matrix for local still-image validation without committing media.

Forbidden claims remain:

- named identity
- face recognition or biometric match
- cross-day identity
- fall confirmation
- medical emergency
- autonomous emergency dispatch

## Validation

Planned deterministic checks:

```bash
python3 -m json.tool apps/caresight-hub/config/appearance-still-image-sources.example.json >/dev/null
npm run check
```
