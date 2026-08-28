from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class PaddingValues:
    top: int
    bottom: int
    left: int
    right: int

    @property
    def applied(self) -> bool:
        return any((self.top, self.bottom, self.left, self.right))

    def to_dict(self) -> dict[str, int]:
        return {
            "top": self.top,
            "bottom": self.bottom,
            "left": self.left,
            "right": self.right,
        }


@dataclass(frozen=True)
class LetterboxResult:
    image: np.ndarray
    padding: PaddingValues
    scale: float
    upscaling_applied: bool
    interpolation: str


def letterbox_resize(
    image: np.ndarray,
    target_width: int,
    target_height: int,
    *,
    padding_mode: str = "reflect",
    neutral_value: int = 127,
) -> LetterboxResult:
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("A three-channel image is required.")
    source_height, source_width = image.shape[:2]
    if source_width <= 0 or source_height <= 0:
        raise ValueError("Image dimensions must be positive.")

    scale = min(target_width / source_width, target_height / source_height)
    scaled_width = max(1, min(target_width, int(round(source_width * scale))))
    scaled_height = max(1, min(target_height, int(round(source_height * scale))))
    interpolation_code = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    interpolation_name = "area" if scale < 1.0 else "linear"
    resized = cv2.resize(
        image,
        (scaled_width, scaled_height),
        interpolation=interpolation_code,
    )

    horizontal_padding = target_width - scaled_width
    vertical_padding = target_height - scaled_height
    padding = PaddingValues(
        top=vertical_padding // 2,
        bottom=vertical_padding - vertical_padding // 2,
        left=horizontal_padding // 2,
        right=horizontal_padding - horizontal_padding // 2,
    )

    if not padding.applied:
        output = resized
    elif padding_mode == "reflect" and scaled_width > 1 and scaled_height > 1:
        output = cv2.copyMakeBorder(
            resized,
            padding.top,
            padding.bottom,
            padding.left,
            padding.right,
            cv2.BORDER_REFLECT_101,
        )
    elif padding_mode == "constant":
        output = cv2.copyMakeBorder(
            resized,
            padding.top,
            padding.bottom,
            padding.left,
            padding.right,
            cv2.BORDER_CONSTANT,
            value=(neutral_value, neutral_value, neutral_value),
        )
    else:
        output = cv2.copyMakeBorder(
            resized,
            padding.top,
            padding.bottom,
            padding.left,
            padding.right,
            cv2.BORDER_REPLICATE,
        )

    return LetterboxResult(
        image=output,
        padding=padding,
        scale=scale,
        upscaling_applied=scale > 1.0,
        interpolation=interpolation_name,
    )
