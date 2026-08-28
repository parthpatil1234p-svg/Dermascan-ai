from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class NormalizedRegionBox:
    left: float
    top: float
    right: float
    bottom: float


def clamp_region_box(box: NormalizedRegionBox) -> NormalizedRegionBox:
    left = min(1.0, max(0.0, box.left))
    top = min(1.0, max(0.0, box.top))
    right = min(1.0, max(left, box.right))
    bottom = min(1.0, max(top, box.bottom))
    return NormalizedRegionBox(left, top, right, bottom)


def create_region_mask(
    width: int,
    height: int,
    box: NormalizedRegionBox,
    *,
    minimum_pixels: int = 64,
) -> np.ndarray | None:
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive.")
    safe = clamp_region_box(box)
    left, right = round(safe.left * width), round(safe.right * width)
    top, bottom = round(safe.top * height), round(safe.bottom * height)
    left, right = max(0, left), min(width, right)
    top, bottom = max(0, top), min(height, bottom)
    if max(0, right - left) * max(0, bottom - top) < minimum_pixels:
        return None
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[top:bottom, left:right] = 1
    return mask


def combine_region_masks(*masks: np.ndarray) -> np.ndarray:
    if not masks or any(mask.shape != masks[0].shape for mask in masks):
        raise ValueError("Region masks must have one shared shape.")
    return np.maximum.reduce(masks)
