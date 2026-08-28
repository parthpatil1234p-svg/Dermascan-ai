from dataclasses import asdict, dataclass
from math import isfinite

from app.utils.image_coordinates import clamp_int, normalized_center_offset


@dataclass(frozen=True)
class NormalizedBoundingBox:
    x: float
    y: float
    width: float
    height: float

    def to_dict(self) -> dict[str, float]:
        return {key: round(value, 6) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class PixelBoundingBox:
    x: int
    y: int
    width: int
    height: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def normalized_box_has_image_overlap(box: NormalizedBoundingBox) -> bool:
    values = [box.x, box.y, box.width, box.height]
    if not all(isfinite(value) for value in values):
        return False
    if box.width <= 0 or box.height <= 0:
        return False
    return box.x < 1 and box.y < 1 and (box.x + box.width) > 0 and (box.y + box.height) > 0


def normalized_to_pixel_box(
    box: NormalizedBoundingBox,
    image_width: int,
    image_height: int,
) -> PixelBoundingBox | None:
    if image_width <= 0 or image_height <= 0:
        return None
    if not normalized_box_has_image_overlap(box):
        return None

    x1 = clamp_int(box.x * image_width, 0, image_width)
    y1 = clamp_int(box.y * image_height, 0, image_height)
    x2 = clamp_int((box.x + box.width) * image_width, 0, image_width)
    y2 = clamp_int((box.y + box.height) * image_height, 0, image_height)

    if x2 <= x1 or y2 <= y1:
        return None
    return PixelBoundingBox(x=x1, y=y1, width=x2 - x1, height=y2 - y1)


def add_padding_to_pixel_box(
    box: PixelBoundingBox,
    image_width: int,
    image_height: int,
    padding_ratio: float,
) -> PixelBoundingBox | None:
    padding_x = box.width * padding_ratio
    padding_y = box.height * padding_ratio
    x1 = clamp_int(box.x - padding_x, 0, image_width)
    y1 = clamp_int(box.y - padding_y, 0, image_height)
    x2 = clamp_int(box.x + box.width + padding_x, 0, image_width)
    y2 = clamp_int(box.y + box.height + padding_y, 0, image_height)
    if x2 <= x1 or y2 <= y1:
        return None
    return PixelBoundingBox(x=x1, y=y1, width=x2 - x1, height=y2 - y1)


def box_area_ratio(
    box: PixelBoundingBox,
    image_width: int,
    image_height: int,
) -> float:
    image_area = image_width * image_height
    if image_area <= 0:
        return 0
    return (box.width * box.height) / image_area


def box_center_offset(
    box: PixelBoundingBox,
    image_width: int,
    image_height: int,
) -> float:
    return normalized_center_offset(
        center_x=box.x + (box.width / 2),
        center_y=box.y + (box.height / 2),
        image_width=image_width,
        image_height=image_height,
    )


def boundary_issue_codes(
    box: PixelBoundingBox,
    image_width: int,
    image_height: int,
    edge_margin_ratio: float,
) -> list[str]:
    margin_x = image_width * edge_margin_ratio
    margin_y = image_height * edge_margin_ratio
    codes: list[str] = []
    if box.x <= margin_x:
        codes.append("FACE_TOUCHES_LEFT_EDGE")
    if box.y <= margin_y:
        codes.append("FACE_TOUCHES_TOP_EDGE")
    if box.x + box.width >= image_width - margin_x:
        codes.append("FACE_TOUCHES_RIGHT_EDGE")
    if box.y + box.height >= image_height - margin_y:
        codes.append("FACE_TOUCHES_BOTTOM_EDGE")
    return codes
