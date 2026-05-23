from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .descriptors import AppearanceDescriptor, BBox


@dataclass(frozen=True)
class AppearanceSampleQuality:
    accepted: bool
    score: float
    reasons: list[str]


def score_appearance_sample(
    *,
    descriptor: AppearanceDescriptor,
    bbox_xyxy: BBox,
    frame_width: int,
    frame_height: int,
    detection_confidence: float,
) -> AppearanceSampleQuality:
    reasons: list[str] = []
    if descriptor.descriptor_status != "available":
        return AppearanceSampleQuality(False, 0.0, [f"descriptor_{descriptor.descriptor_status}"])

    x1, y1, x2, y2 = bbox_xyxy
    box_width = max(x2 - x1, 0.0)
    box_height = max(y2 - y1, 0.0)
    if box_width <= 0 or box_height <= 0 or frame_width <= 0 or frame_height <= 0:
        return AppearanceSampleQuality(False, 0.0, ["invalid_bbox"])

    aspect = box_width / box_height
    area_ratio = (box_width * box_height) / (frame_width * frame_height)
    bottom_truncated = y2 >= frame_height - 2
    side_truncated = x1 <= 2 or x2 >= frame_width - 2
    known_attributes = sum(
        1
        for value in [
            descriptor.upper_body_color.value,
            descriptor.lower_body_color.value,
            descriptor.headwear.value,
            descriptor.footwear.value,
        ]
        if value != "unknown"
    )

    score = 0.0
    score += min(max(detection_confidence, 0.0), 1.0) * 0.35
    score += min(known_attributes / 2, 1.0) * 0.30
    if 0.22 <= area_ratio <= 0.82:
        score += 0.15
    else:
        reasons.append("bbox_area_outside_preferred_range")
    if aspect <= 2.4:
        score += 0.10
    else:
        reasons.append("wide_prone_or_partial_bbox")
    if not bottom_truncated:
        score += 0.05
    else:
        reasons.append("bottom_truncated")
    if not side_truncated:
        score += 0.05
    else:
        reasons.append("side_truncated")

    if known_attributes == 0:
        reasons.append("no_known_appearance_attributes")
    if detection_confidence < 0.45:
        reasons.append("low_detection_confidence")
    accepted = score >= 0.62 and known_attributes > 0 and detection_confidence >= 0.45
    if accepted:
        reasons.insert(0, "accepted")
    else:
        reasons.insert(0, "rejected")
    return AppearanceSampleQuality(accepted, round(score, 3), reasons)


def summarize_appearance_samples(
    samples: list[dict],
    *,
    min_quality_score: float = 0.62,
) -> dict:
    good_samples = [
        sample
        for sample in samples
        if sample["descriptor_status"] == "available" and sample["quality_score"] >= min_quality_score
    ]
    upper_values = [
        sample["attributes"].get("upper_body_color", {}).get("value")
        for sample in good_samples
    ]
    lower_values = [
        sample["attributes"].get("lower_body_color", {}).get("value")
        for sample in good_samples
    ]
    headwear_values = [
        sample["attributes"].get("headwear", {}).get("value")
        for sample in good_samples
    ]
    footwear_values = [
        sample["attributes"].get("footwear", {}).get("value")
        for sample in good_samples
    ]
    upper_values = [value for value in upper_values if value and value != "unknown"]
    lower_values = [value for value in lower_values if value and value != "unknown"]
    headwear_values = [value for value in headwear_values if value and value != "unknown"]
    footwear_values = [value for value in footwear_values if value and value != "unknown"]
    return {
        "schema": "appearance-profile-sample-summary",
        "sample_count": len(samples),
        "good_sample_count": len(good_samples),
        "upper_body_color": _support_summary(upper_values),
        "lower_body_color": _support_summary(lower_values),
        "headwear": _support_summary(headwear_values),
        "footwear": _support_summary(footwear_values),
        "safety_boundaries": [
            "non_biometric_daily_appearance_only",
            "same_day_only",
            "no_named_person_identity",
            "no_face_recognition",
            "no_cross_day_identity",
        ],
    }


def _support_summary(values: list[str]) -> dict:
    if not values:
        return {"value": "unknown", "support_count": 0, "total_good_samples": 0, "support_ratio": 0.0}
    counts = Counter(values)
    value, support_count = counts.most_common(1)[0]
    total = len(values)
    return {
        "value": value,
        "support_count": support_count,
        "total_good_samples": total,
        "support_ratio": round(support_count / total, 3),
    }
