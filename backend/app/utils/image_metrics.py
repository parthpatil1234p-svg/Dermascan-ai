from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


class ImageDecodeError(ValueError):
    pass


@dataclass(frozen=True)
class RawImageMetrics:
    sharpness_variance: float
    mean_brightness: float
    min_brightness: int
    max_brightness: int
    contrast_standard_deviation: float
    underexposed_pixel_percent: float
    overexposed_pixel_percent: float
    width: int
    height: int
    aspect_ratio: float


def calculate_image_metrics(
    image_path: Path,
    *,
    dark_pixel_threshold: int,
    bright_pixel_threshold: int,
) -> RawImageMetrics:
    try:
        encoded = np.fromfile(image_path, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    except (OSError, ValueError, cv2.error) as exc:
        raise ImageDecodeError from exc

    if image is None or image.size == 0:
        raise ImageDecodeError

    try:
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = grayscale.shape
        sharpness = float(cv2.Laplacian(grayscale, cv2.CV_64F).var())
    except cv2.error as exc:
        raise ImageDecodeError from exc

    return RawImageMetrics(
        sharpness_variance=sharpness,
        mean_brightness=float(grayscale.mean()),
        min_brightness=int(grayscale.min()),
        max_brightness=int(grayscale.max()),
        contrast_standard_deviation=float(grayscale.std()),
        underexposed_pixel_percent=float(
            np.count_nonzero(grayscale < dark_pixel_threshold) / grayscale.size * 100
        ),
        overexposed_pixel_percent=float(
            np.count_nonzero(grayscale > bright_pixel_threshold) / grayscale.size * 100
        ),
        width=int(width),
        height=int(height),
        aspect_ratio=float(width / height),
    )
