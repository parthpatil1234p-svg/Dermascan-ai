from dataclasses import dataclass

import numpy as np

from app.utils.facial_regions import NormalizedRegionBox, create_safe_region_mask

SUPPORTED_REGION_NAMES = {
    "forehead",
    "nose",
    "left_cheek",
    "right_cheek",
    "chin",
    "under_left_eye",
    "under_right_eye",
    "jawline",
    "t_zone",
    "full_face",
}


@dataclass(frozen=True)
class RegionContext:
    precise_regions_available: bool
    available_regions: tuple[str, ...]
    issue_code: str | None


def validate_region_geometry(
    image: np.ndarray,
    region_boxes: dict[str, NormalizedRegionBox] | None,
) -> RegionContext:
    if not region_boxes:
        return RegionContext(False, ("full_face",), "REGION_INFORMATION_UNAVAILABLE")
    valid: list[str] = []
    for name, box in region_boxes.items():
        if name not in SUPPORTED_REGION_NAMES or name == "full_face":
            continue
        mask = create_safe_region_mask(image.shape[1], image.shape[0], box)
        if mask is not None:
            valid.append(name)
    if not valid:
        return RegionContext(False, ("full_face",), "REGION_INFORMATION_UNAVAILABLE")
    return RegionContext(True, tuple(valid), None)


def region_names_for_global_prediction(context: RegionContext) -> list[str]:
    # The Step 9 classifier is global. Geometry alone cannot localize its score.
    return ["Full Face"] if not context.precise_regions_available else []
