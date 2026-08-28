from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.core.config import Settings
from app.schemas.image_preprocessing import PreprocessingIssue
from app.services.model_input_service import build_inference_tensor
from app.utils.image_colour import (
    DecodedRgbImage,
    ImageColourDecodeError,
    decode_image_to_rgb,
)
from app.utils.image_resize import LetterboxResult, PaddingValues, letterbox_resize


class ImageTransformationError(Exception):
    pass


class ImageTransformationDecodeError(ImageTransformationError):
    pass


@dataclass(frozen=True)
class ImageTransformationResult:
    image: np.ndarray
    source_width: int
    source_height: int
    source_colour_space: str
    output_width: int
    output_height: int
    output_channels: int
    padding: PaddingValues
    resize_scale: float
    upscaling_applied: bool
    denoise_applied: bool
    clahe_applied: bool
    white_balance_applied: bool
    sharpening_applied: bool
    alpha_composited: bool
    status: str
    issues: list[PreprocessingIssue]
    manifest: dict[str, Any]


def preprocessing_issue(
    code: str,
    message: str,
    recommendation: str,
) -> PreprocessingIssue:
    return PreprocessingIssue(
        code=code,
        severity="warning",
        message=message,
        recommendation=recommendation,
    )


def estimate_noise(rgb_image: np.ndarray) -> float:
    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    softened = cv2.GaussianBlur(gray, (3, 3), 0)
    return float(np.mean(cv2.absdiff(gray, softened)))


def estimate_sharpness(rgb_image: np.ndarray) -> float:
    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def apply_conservative_denoise(
    rgb_image: np.ndarray,
    settings: Settings,
) -> tuple[np.ndarray, bool]:
    if not settings.preprocess_enable_denoise:
        return rgb_image, False
    if estimate_noise(rgb_image) < settings.preprocess_noise_threshold:
        return rgb_image, False
    if estimate_sharpness(rgb_image) < settings.blur_warning_threshold:
        return rgb_image, False
    strength = settings.preprocess_denoise_strength
    return (
        cv2.bilateralFilter(
            rgb_image,
            d=3,
            sigmaColor=max(5, strength * 3),
            sigmaSpace=3,
        ),
        True,
    )


def apply_mild_clahe(rgb_image: np.ndarray, settings: Settings) -> np.ndarray:
    lab = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
    luminance, channel_a, channel_b = cv2.split(lab)
    clahe = cv2.createCLAHE(
        clipLimit=settings.preprocess_clahe_clip_limit,
        tileGridSize=(
            settings.preprocess_clahe_grid_size,
            settings.preprocess_clahe_grid_size,
        ),
    )
    adjusted = cv2.merge((clahe.apply(luminance), channel_a, channel_b))
    return cv2.cvtColor(adjusted, cv2.COLOR_LAB2RGB)


def apply_limited_white_balance(rgb_image: np.ndarray) -> np.ndarray:
    values = rgb_image.astype(np.float32)
    channel_means = values.reshape(-1, 3).mean(axis=0)
    target = float(channel_means.mean())
    gains = np.divide(
        target,
        channel_means,
        out=np.ones_like(channel_means),
        where=channel_means > 0,
    )
    gains = np.clip(gains, 0.9, 1.1)
    return np.clip(values * gains, 0, 255).astype(np.uint8)


def apply_mild_sharpening(rgb_image: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(rgb_image, (3, 3), 0)
    return cv2.addWeighted(rgb_image, 1.08, blurred, -0.08, 0)


def build_transformation_manifest(
    decoded: DecodedRgbImage,
    resized: LetterboxResult,
    *,
    source_width: int,
    source_height: int,
    settings: Settings,
    denoise_applied: bool,
    clahe_applied: bool,
    white_balance_applied: bool,
    sharpening_applied: bool,
) -> dict[str, Any]:
    padding_values = resized.padding.to_dict()
    transformations = [
        {"name": "orientation_verification", "applied": True},
        {
            "name": "alpha_composite",
            "applied": decoded.alpha_composited,
            "background_value": settings.preprocess_alpha_background,
        },
        {
            "name": "mild_denoising",
            "applied": denoise_applied,
            "strength": settings.preprocess_denoise_strength,
        },
        {
            "name": "luminance_clahe",
            "applied": clahe_applied,
            "clip_limit": settings.preprocess_clahe_clip_limit,
        },
        {"name": "limited_white_balance", "applied": white_balance_applied},
        {"name": "mild_sharpening", "applied": sharpening_applied},
        {
            "name": "letterbox_resize",
            "applied": True,
            "scale": round(resized.scale, 6),
            "interpolation": resized.interpolation,
        },
        {"name": "padding", "applied": resized.padding.applied, **padding_values},
    ]
    return {
        "source": {
            "width": source_width,
            "height": source_height,
            "colour_space": decoded.source_colour_space,
        },
        "output": {
            "width": settings.model_input_width,
            "height": settings.model_input_height,
            "channels": settings.model_input_channels,
            "colour_space": settings.model_input_colour_space,
        },
        "transformations": transformations,
        "inference_normalization": settings.preprocess_normalization_mode,
        "beauty_filters_applied": False,
        "random_augmentation_applied": False,
    }


def transform_face_crop(
    image_path: Path,
    settings: Settings,
) -> ImageTransformationResult:
    try:
        decoded = decode_image_to_rgb(
            image_path,
            alpha_background=settings.preprocess_alpha_background,
        )
        rgb_image = decoded.image
        source_height, source_width = rgb_image.shape[:2]

        transformed, denoise_applied = apply_conservative_denoise(rgb_image, settings)
        clahe_applied = settings.preprocess_enable_clahe
        if clahe_applied:
            transformed = apply_mild_clahe(transformed, settings)
        white_balance_applied = settings.preprocess_enable_white_balance
        if white_balance_applied:
            transformed = apply_limited_white_balance(transformed)
        sharpening_applied = settings.preprocess_enable_sharpening
        if sharpening_applied:
            transformed = apply_mild_sharpening(transformed)

        resized = letterbox_resize(
            transformed,
            settings.model_input_width,
            settings.model_input_height,
            padding_mode=settings.preprocess_padding_mode,
            neutral_value=settings.preprocess_alpha_background,
        )
        build_inference_tensor(resized.image, settings)

        issues: list[PreprocessingIssue] = []
        if resized.scale >= settings.preprocess_upscale_warning_factor:
            issues.append(
                preprocessing_issue(
                    "SIGNIFICANT_UPSCALING_REQUIRED",
                    "The facial crop required significant enlargement.",
                    "A closer source image may improve later analysis reliability.",
                )
            )

        manifest = build_transformation_manifest(
            decoded,
            resized,
            source_width=source_width,
            source_height=source_height,
            settings=settings,
            denoise_applied=denoise_applied,
            clahe_applied=clahe_applied,
            white_balance_applied=white_balance_applied,
            sharpening_applied=sharpening_applied,
        )
        return ImageTransformationResult(
            image=resized.image,
            source_width=source_width,
            source_height=source_height,
            source_colour_space=decoded.source_colour_space,
            output_width=resized.image.shape[1],
            output_height=resized.image.shape[0],
            output_channels=resized.image.shape[2],
            padding=resized.padding,
            resize_scale=resized.scale,
            upscaling_applied=resized.upscaling_applied,
            denoise_applied=denoise_applied,
            clahe_applied=clahe_applied,
            white_balance_applied=white_balance_applied,
            sharpening_applied=sharpening_applied,
            alpha_composited=decoded.alpha_composited,
            status="warning" if issues else "completed",
            issues=issues,
            manifest=manifest,
        )
    except ImageColourDecodeError as exc:
        raise ImageTransformationDecodeError from exc
    except ImageTransformationError:
        raise
    except Exception as exc:
        raise ImageTransformationError from exc
