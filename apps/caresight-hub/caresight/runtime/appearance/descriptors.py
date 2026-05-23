from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


COLOR_BUCKETS = {
    "black",
    "white",
    "gray",
    "dark gray",
    "light gray",
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "brown",
    "unknown",
}


@dataclass(frozen=True)
class ColorDescriptor:
    value: str
    confidence: float


@dataclass(frozen=True)
class AppearanceDescriptor:
    descriptor_status: str
    upper_body_color: ColorDescriptor
    lower_body_color: ColorDescriptor
    headwear: ColorDescriptor
    footwear: ColorDescriptor
    descriptor_source: str = "runtime_observation"
    frame_source: str | None = None
    snapshot_path: str | None = None
    event_id: str | None = None
    observation_id: str | None = None

    def to_storage_record(self) -> dict[str, object]:
        return {
            "descriptor_status": self.descriptor_status,
            "descriptor_source": self.descriptor_source,
            "frame_source": self.frame_source,
            "snapshot_path": self.snapshot_path,
            "event_id": self.event_id,
            "observation_id": self.observation_id,
            "upper_body_color": self.upper_body_color.value,
            "upper_body_color_confidence": self.upper_body_color.confidence,
            "lower_body_color": self.lower_body_color.value,
            "lower_body_color_confidence": self.lower_body_color.confidence,
            "headwear": self.headwear.value,
            "headwear_confidence": self.headwear.confidence,
            "footwear": self.footwear.value,
            "footwear_confidence": self.footwear.confidence,
        }


Frame = Sequence[Sequence[tuple[int, int, int]]]
BBox = tuple[float, float, float, float]


def extract_appearance_descriptor(
    *,
    bbox_xyxy: BBox,
    frame: Frame | None = None,
    snapshot_path: str | None = None,
    frame_source: str | None = None,
    descriptor_source: str = "runtime_observation",
    event_id: str | None = None,
    observation_id: str | None = None,
) -> AppearanceDescriptor:
    if descriptor_source not in {
        "runtime_observation",
        "seeded_test_fixture",
        "operator_demo_seed",
    }:
        descriptor_source = "runtime_observation"

    loaded = frame
    status = "available"
    if loaded is None:
        if snapshot_path is None:
            return _empty_descriptor(
                "unavailable",
                descriptor_source=descriptor_source,
                frame_source=frame_source,
                snapshot_path=snapshot_path,
                event_id=event_id,
                observation_id=observation_id,
            )
        try:
            loaded = read_image(Path(snapshot_path))
        except (OSError, ValueError):
            return _empty_descriptor(
                "unreadable",
                descriptor_source=descriptor_source,
                frame_source=frame_source,
                snapshot_path=snapshot_path,
                event_id=event_id,
                observation_id=observation_id,
            )

    width, height = _frame_size(loaded)
    if _is_low_quality_prone_bbox(bbox_xyxy, width=width, height=height):
        return _empty_descriptor(
            "unavailable",
            descriptor_source=descriptor_source,
            frame_source=frame_source,
            snapshot_path=snapshot_path,
            event_id=event_id,
            observation_id=observation_id,
        )
    regions = _bbox_regions(bbox_xyxy, width=width, height=height)
    if regions is None:
        status = "invalid_bbox"
        return _empty_descriptor(
            status,
            descriptor_source=descriptor_source,
            frame_source=frame_source,
            snapshot_path=snapshot_path,
            event_id=event_id,
            observation_id=observation_id,
        )

    head_region, upper_region, lower_region, foot_region = regions
    unknown = ColorDescriptor("unknown", 0.0)
    return AppearanceDescriptor(
        descriptor_status=status,
        upper_body_color=_region_color(loaded, upper_region),
        lower_body_color=_region_color(loaded, lower_region) if lower_region else unknown,
        headwear=_headwear_color(loaded, head_region) if head_region else unknown,
        footwear=_region_color(loaded, foot_region) if foot_region else unknown,
        descriptor_source=descriptor_source,
        frame_source=frame_source,
        snapshot_path=snapshot_path,
        event_id=event_id,
        observation_id=observation_id,
    )


def descriptor_attributes(descriptor: AppearanceDescriptor) -> dict[str, dict[str, float | str]]:
    return {
        "upper_body_color": {
            "value": descriptor.upper_body_color.value,
            "confidence": descriptor.upper_body_color.confidence,
        },
        "lower_body_color": {
            "value": descriptor.lower_body_color.value,
            "confidence": descriptor.lower_body_color.confidence,
        },
        "headwear": {
            "value": descriptor.headwear.value,
            "confidence": descriptor.headwear.confidence,
        },
        "footwear": {
            "value": descriptor.footwear.value,
            "confidence": descriptor.footwear.confidence,
        },
    }


def read_image(path: Path) -> list[list[tuple[int, int, int]]]:
    if path.suffix.lower() == ".ppm":
        return read_ppm(path)
    try:
        return read_with_pillow(path)
    except (ImportError, OSError, ValueError):
        pass
    try:
        return read_with_cv2(path)
    except (ImportError, OSError, ValueError):
        pass
    raise ValueError("unsupported or unreadable image format")


def read_with_pillow(path: Path) -> list[list[tuple[int, int, int]]]:
    from PIL import Image

    with Image.open(path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        pixels = list(rgb.getdata())
    return [
        [pixels[(y * width) + x] for x in range(width)]
        for y in range(height)
    ]


def read_with_cv2(path: Path) -> list[list[tuple[int, int, int]]]:
    import cv2

    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("cv2 could not read image")
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width = rgb.shape[:2]
    return [
        [tuple(int(channel) for channel in rgb[y, x]) for x in range(width)]
        for y in range(height)
    ]


def read_ppm(path: Path) -> list[list[tuple[int, int, int]]]:
    data = path.read_bytes()
    tokens: list[bytes] = []
    index = 0
    while len(tokens) < 4:
        while index < len(data) and data[index:index + 1].isspace():
            index += 1
        if index >= len(data):
            raise ValueError("truncated PPM header")
        if data[index:index + 1] == b"#":
            while index < len(data) and data[index:index + 1] != b"\n":
                index += 1
            continue
        start = index
        while index < len(data) and not data[index:index + 1].isspace():
            index += 1
        tokens.append(data[start:index])
    magic, width_raw, height_raw, max_raw = tokens
    if magic != b"P6" or int(max_raw) != 255:
        raise ValueError("unsupported PPM format")
    while index < len(data) and data[index:index + 1].isspace():
        index += 1
    width = int(width_raw)
    height = int(height_raw)
    expected = width * height * 3
    pixels = data[index:index + expected]
    if len(pixels) != expected:
        raise ValueError("truncated PPM pixels")
    rows = []
    cursor = 0
    for _ in range(height):
        row = []
        for _ in range(width):
            row.append((pixels[cursor], pixels[cursor + 1], pixels[cursor + 2]))
            cursor += 3
        rows.append(row)
    return rows


def _empty_descriptor(
    status: str,
    *,
    descriptor_source: str,
    frame_source: str | None,
    snapshot_path: str | None,
    event_id: str | None,
    observation_id: str | None,
) -> AppearanceDescriptor:
    unknown = ColorDescriptor("unknown", 0.0)
    return AppearanceDescriptor(
        descriptor_status=status,
        upper_body_color=unknown,
        lower_body_color=unknown,
        headwear=unknown,
        footwear=unknown,
        descriptor_source=descriptor_source,
        frame_source=frame_source,
        snapshot_path=snapshot_path,
        event_id=event_id,
        observation_id=observation_id,
    )


def _frame_size(frame: Frame) -> tuple[int, int]:
    height = len(frame)
    width = len(frame[0]) if height else 0
    return width, height


def _bbox_regions(
    bbox_xyxy: BBox,
    *,
    width: int,
    height: int,
) -> tuple[
    tuple[int, int, int, int] | None,
    tuple[int, int, int, int],
    tuple[int, int, int, int] | None,
    tuple[int, int, int, int] | None,
] | None:
    x1, y1, x2, y2 = bbox_xyxy
    if x2 <= x1 or y2 <= y1 or width <= 0 or height <= 0:
        return None
    left = max(0, int(round(x1)))
    right = min(width, int(round(x2)))
    top = max(0, int(round(y1)))
    bottom = min(height, int(round(y2)))
    if right <= left or bottom <= top:
        return None

    box_width = right - left
    box_height = bottom - top
    truncated_at_bottom = bottom >= height - 2
    sample_left = left + int(round(box_width * 0.30))
    sample_right = left + int(round(box_width * 0.70))
    accessory_left = left + int(round(box_width * 0.36))
    accessory_right = left + int(round(box_width * 0.64))
    if sample_right <= sample_left:
        return None
    head_region = None
    if top > 2 and accessory_right > accessory_left:
        head_top = top + int(round(box_height * 0.02))
        head_bottom = top + int(round(box_height * 0.16))
        if head_bottom > head_top:
            head_region = (accessory_left, head_top, accessory_right, head_bottom)

    if truncated_at_bottom:
        upper_top = top + int(round(box_height * 0.60))
        upper_bottom = top + int(round(box_height * 0.90))
        lower_region = None
        foot_region = None
    else:
        upper_top = top + int(round(box_height * 0.38))
        upper_bottom = top + int(round(box_height * 0.62))
        lower_top = top + int(round(box_height * 0.62))
        lower_bottom = top + int(round(box_height * 0.90))
        lower_region = (sample_left, lower_top, sample_right, lower_bottom)
        foot_top = top + int(round(box_height * 0.90))
        foot_bottom = top + int(round(box_height * 0.98))
        foot_region = (accessory_left, foot_top, accessory_right, foot_bottom) if foot_bottom > foot_top else None

    if upper_bottom <= upper_top:
        return None
    return head_region, (sample_left, upper_top, sample_right, upper_bottom), lower_region, foot_region


def _is_low_quality_prone_bbox(
    bbox_xyxy: BBox,
    *,
    width: int,
    height: int,
) -> bool:
    x1, y1, x2, y2 = bbox_xyxy
    if x2 <= x1 or y2 <= y1 or width <= 0 or height <= 0:
        return False
    left = max(0, int(round(x1)))
    right = min(width, int(round(x2)))
    top = max(0, int(round(y1)))
    bottom = min(height, int(round(y2)))
    box_width = right - left
    box_height = bottom - top
    if box_height <= 0:
        return False
    return bottom >= height - 2 and box_width / box_height > 2.2


def _region_color(
    frame: Frame,
    region: tuple[int, int, int, int],
) -> ColorDescriptor:
    x1, y1, x2, y2 = region
    pixels = [frame[y][x] for y in range(y1, y2) for x in range(x1, x2)]
    if not pixels:
        return ColorDescriptor("unknown", 0.0)
    midpoint = len(pixels) // 2
    red = sorted(pixel[0] for pixel in pixels)[midpoint]
    green = sorted(pixel[1] for pixel in pixels)[midpoint]
    blue = sorted(pixel[2] for pixel in pixels)[midpoint]
    return ColorDescriptor(_bucket_color(red, green, blue), 0.78)


def _headwear_color(
    frame: Frame,
    region: tuple[int, int, int, int],
) -> ColorDescriptor:
    color = _region_color(frame, region)
    if color.value in {"unknown", "brown", "orange", "yellow"}:
        return ColorDescriptor("unknown", 0.0)
    return ColorDescriptor(color.value, 0.62)


def _bucket_color(red: float, green: float, blue: float) -> str:
    maximum = max(red, green, blue)
    minimum = min(red, green, blue)
    brightness = maximum
    saturation = 0.0 if maximum == 0 else (maximum - minimum) / maximum

    if brightness < 35:
        return "black"
    if saturation < 0.12:
        if brightness > 220:
            return "white"
        if brightness > 170:
            return "light gray"
        if brightness < 80:
            return "dark gray"
        return "gray"

    hue = _rgb_hue(red, green, blue)
    if 20 <= hue < 45 and brightness < 150:
        return "brown"
    if hue < 15 or hue >= 345:
        return "red"
    if hue < 45:
        return "orange"
    if hue < 70:
        return "yellow"
    if hue < 165:
        return "green"
    if hue < 255:
        return "blue"
    if hue < 305:
        return "purple"
    return "red"


def _rgb_hue(red: float, green: float, blue: float) -> float:
    maximum = max(red, green, blue)
    minimum = min(red, green, blue)
    delta = maximum - minimum
    if delta == 0:
        return 0.0
    if maximum == red:
        hue = 60 * (((green - blue) / delta) % 6)
    elif maximum == green:
        hue = 60 * (((blue - red) / delta) + 2)
    else:
        hue = 60 * (((red - green) / delta) + 4)
    return hue % 360
