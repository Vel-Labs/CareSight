from __future__ import annotations

from pathlib import Path
from typing import Sequence

from caresight.runtime.inference.types import Detection

from .descriptors import (
    descriptor_attributes,
    extract_appearance_descriptor,
    write_appearance_annotation,
)


def build_yolo_appearance_review(
    *,
    snapshot_path: str,
    detections: Sequence[Detection],
    output_dir: str,
) -> dict[str, object]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    people = []
    for index, detection in enumerate(_person_detections(detections), start=1):
        bbox = (
            detection.bbox.x_min,
            detection.bbox.y_min,
            detection.bbox.x_max,
            detection.bbox.y_max,
        )
        descriptor = extract_appearance_descriptor(
            snapshot_path=snapshot_path,
            bbox_xyxy=bbox,
            frame_source="yolo26_still_image",
            descriptor_source="runtime_observation",
            observation_id=detection.detection_id,
        )
        visual = write_appearance_annotation(
            snapshot_path=snapshot_path,
            output_path=str(output / f"person-{index:02d}-{detection.detection_id}.png"),
            bbox_xyxy=bbox,
            descriptor=descriptor,
            label=f"person {index}",
        )
        people.append(
            {
                "person_index": index,
                "detection_id": detection.detection_id,
                "model_id": detection.model_id,
                "label": detection.label,
                "confidence": round(detection.confidence, 4),
                "bbox_xyxy": [round(value, 2) for value in bbox],
                "descriptor_status": descriptor.descriptor_status,
                "attributes": descriptor_attributes(descriptor),
                "visual_evidence": visual,
            }
        )
    return {
        "schema": "yolo26-appearance-review",
        "source_of_truth": "yolo26_mlx_detections",
        "snapshot_path": snapshot_path,
        "person_count": len(people),
        "people": people,
        "safety_boundaries": [
            "non_biometric_daily_appearance_only",
            "no_named_person_identity",
            "no_face_recognition",
            "no_cross_day_identity",
            "visual_review_only",
        ],
    }


def _person_detections(detections: Sequence[Detection]) -> list[Detection]:
    return [detection for detection in detections if detection.label == "person"]
