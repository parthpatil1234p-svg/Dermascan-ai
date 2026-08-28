from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


class ImageColourDecodeError(Exception):
    pass


@dataclass(frozen=True)
class DecodedRgbImage:
    image: np.ndarray
    source_colour_space: str
    alpha_composited: bool


def decode_image_to_rgb(
    image_path: Path,
    *,
    alpha_background: int = 127,
) -> DecodedRgbImage:
    try:
        encoded = np.fromfile(image_path, dtype=np.uint8)
        decoded = cv2.imdecode(encoded, cv2.IMREAD_UNCHANGED)
    except (OSError, cv2.error, ValueError) as exc:
        raise ImageColourDecodeError from exc

    if decoded is None or decoded.size == 0:
        raise ImageColourDecodeError

    if decoded.ndim == 2:
        rgb = cv2.cvtColor(decoded, cv2.COLOR_GRAY2RGB)
        source_colour_space = "GRAYSCALE"
        alpha_composited = False
    elif decoded.ndim == 3 and decoded.shape[2] == 3:
        rgb = cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)
        source_colour_space = "BGR"
        alpha_composited = False
    elif decoded.ndim == 3 and decoded.shape[2] == 4:
        alpha = decoded[:, :, 3:4].astype(np.float32) / 255.0
        bgr = decoded[:, :, :3].astype(np.float32)
        background = np.full_like(bgr, float(alpha_background))
        composited_bgr = np.rint(bgr * alpha + background * (1.0 - alpha)).astype(np.uint8)
        rgb = cv2.cvtColor(composited_bgr, cv2.COLOR_BGR2RGB)
        source_colour_space = "BGRA"
        alpha_composited = True
    else:
        raise ImageColourDecodeError

    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise ImageColourDecodeError
    return DecodedRgbImage(rgb, source_colour_space, alpha_composited)
