from math import sqrt


def clamp_int(value: float, minimum: int, maximum: int) -> int:
    return max(minimum, min(int(round(value)), maximum))


def normalized_center_offset(
    *,
    center_x: float,
    center_y: float,
    image_width: int,
    image_height: int,
) -> float:
    if image_width <= 0 or image_height <= 0:
        return 1.0
    normalized_x = (center_x - (image_width / 2)) / image_width
    normalized_y = (center_y - (image_height / 2)) / image_height
    return sqrt((normalized_x * normalized_x) + (normalized_y * normalized_y))
