from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    class_name: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
    frame_width: int
    frame_height: int

    @property
    def bottom_center_normalized(self) -> tuple[float, float]:
        x1, _y1, x2, y2 = self.bbox_xyxy
        center_x = ((x1 + x2) / 2.0) / self.frame_width
        bottom_y = y2 / self.frame_height
        return center_x, bottom_y

    def is_person(self) -> bool:
        return self.class_name == "person"
