from dataclasses import dataclass

from app.core.config import Settings
from app.schemas.image_quality import QualityIssue
from app.utils.image_metrics import RawImageMetrics


@dataclass(frozen=True)
class QualityEvaluation:
    sharpness_status: str
    sharpness_score: int
    brightness_status: str
    brightness_score: int
    exposure_status: str
    exposure_score: int
    contrast_status: str
    contrast_score: int
    resolution_status: str
    resolution_score: int
    quality_score: int
    quality_status: str
    issues: list[QualityIssue]
    recommendations: list[str]


def clamp_score(value: float) -> int:
    return round(max(0.0, min(100.0, value)))


def interpolate(
    value: float,
    input_min: float,
    input_max: float,
    output_min: float,
    output_max: float,
) -> float:
    if input_max == input_min:
        return output_max
    ratio = (value - input_min) / (input_max - input_min)
    return output_min + ratio * (output_max - output_min)


def score_sharpness(value: float, settings: Settings) -> tuple[str, int, QualityIssue | None]:
    if value <= settings.blur_fail_threshold:
        score = clamp_score(interpolate(value, 0, settings.blur_fail_threshold, 0, 40))
        return (
            "too_blurry",
            score,
            QualityIssue(
                code="IMAGE_TOO_BLURRY",
                severity="error",
                message="The image is too blurry for reliable face analysis.",
                recommendation=(
                    "Clean the camera lens, hold the camera steady, and capture "
                    "the image in brighter light."
                ),
            ),
        )
    if value < settings.blur_warning_threshold:
        score = clamp_score(
            interpolate(
                value,
                settings.blur_fail_threshold,
                settings.blur_warning_threshold,
                40,
                80,
            )
        )
        return (
            "slightly_blurry",
            score,
            QualityIssue(
                code="IMAGE_SLIGHTLY_BLURRY",
                severity="warning",
                message="The image appears slightly blurry.",
                recommendation=(
                    "Use a steady camera and improve the lighting before taking " "another image."
                ),
            ),
        )
    score = clamp_score(
        interpolate(
            min(value, settings.blur_warning_threshold * 2),
            settings.blur_warning_threshold,
            settings.blur_warning_threshold * 2,
            80,
            100,
        )
    )
    return "clear", score, None


def score_brightness(value: float, settings: Settings) -> tuple[str, int, QualityIssue | None]:
    center = (settings.brightness_min_warning + settings.brightness_max_warning) / 2
    if value <= settings.brightness_min_fail:
        return (
            "too_dark",
            0,
            QualityIssue(
                code="IMAGE_TOO_DARK",
                severity="error",
                message="The image is too dark for reliable face analysis.",
                recommendation=("Capture the image in bright, evenly distributed lighting."),
            ),
        )
    if value < settings.brightness_min_warning:
        return (
            "slightly_dark",
            clamp_score(
                interpolate(
                    value,
                    settings.brightness_min_fail,
                    settings.brightness_min_warning,
                    20,
                    75,
                )
            ),
            QualityIssue(
                code="IMAGE_SLIGHTLY_DARK",
                severity="warning",
                message="The image is slightly dark.",
                recommendation=("Face a window or use evenly distributed indoor lighting."),
            ),
        )
    if value <= settings.brightness_max_warning:
        if value <= center:
            score = interpolate(
                value,
                settings.brightness_min_warning,
                center,
                75,
                100,
            )
        else:
            score = interpolate(
                value,
                center,
                settings.brightness_max_warning,
                100,
                75,
            )
        return "acceptable", clamp_score(score), None
    if value < settings.brightness_max_fail:
        return (
            "slightly_bright",
            clamp_score(
                interpolate(
                    value,
                    settings.brightness_max_warning,
                    settings.brightness_max_fail,
                    75,
                    20,
                )
            ),
            QualityIssue(
                code="IMAGE_SLIGHTLY_BRIGHT",
                severity="warning",
                message="The image is slightly too bright.",
                recommendation="Avoid direct flash and strong light on the face.",
            ),
        )
    return (
        "too_bright",
        0,
        QualityIssue(
            code="IMAGE_TOO_BRIGHT",
            severity="error",
            message="The image is too bright for reliable face analysis.",
            recommendation="Avoid direct flash or strong light on the face.",
        ),
    )


def score_exposure(
    metrics: RawImageMetrics, settings: Settings
) -> tuple[str, int, list[QualityIssue]]:
    under_ratio = metrics.underexposed_pixel_percent / max(settings.max_dark_pixel_percent, 0.01)
    over_ratio = metrics.overexposed_pixel_percent / max(settings.max_bright_pixel_percent, 0.01)
    score = clamp_score(100 - min(max(under_ratio, over_ratio), 2) * 50)
    issues: list[QualityIssue] = []

    if under_ratio > 1:
        issues.append(
            QualityIssue(
                code="IMAGE_UNDEREXPOSED",
                severity="warning",
                message="Large areas of the image appear underexposed.",
                recommendation=("Use more even front-facing light and avoid strong shadows."),
            )
        )
    if over_ratio > 1:
        issues.append(
            QualityIssue(
                code="IMAGE_OVEREXPOSED",
                severity="warning",
                message="Parts of the image appear overexposed.",
                recommendation=("Avoid direct flash and strong light behind the camera."),
            )
        )

    if under_ratio > 1 and over_ratio > 1:
        status = "mixed_exposure"
    elif under_ratio > 1:
        status = "underexposed"
    elif over_ratio > 1:
        status = "overexposed"
    else:
        status = "acceptable"
    return status, score, issues


def score_contrast(value: float, settings: Settings) -> tuple[str, int, QualityIssue | None]:
    if value < settings.min_contrast_fail:
        return (
            "low",
            clamp_score(interpolate(value, 0, settings.min_contrast_fail, 0, 45)),
            QualityIssue(
                code="IMAGE_LOW_CONTRAST",
                severity="warning",
                message=(
                    "The image has low contrast and may not contain enough visible "
                    "facial detail."
                ),
                recommendation=("Use clear, even lighting and ensure the camera lens is clean."),
            ),
        )
    if value < settings.min_contrast_warning:
        return (
            "low",
            clamp_score(
                interpolate(
                    value,
                    settings.min_contrast_fail,
                    settings.min_contrast_warning,
                    45,
                    75,
                )
            ),
            QualityIssue(
                code="IMAGE_LOW_CONTRAST",
                severity="warning",
                message="The image contrast is lower than recommended.",
                recommendation="Use brighter, even lighting for clearer detail.",
            ),
        )
    if value <= settings.max_contrast_warning:
        return "acceptable", 100, None
    return (
        "high",
        clamp_score(
            interpolate(
                min(value, 255),
                settings.max_contrast_warning,
                255,
                85,
                60,
            )
        ),
        QualityIssue(
            code="IMAGE_HARSH_CONTRAST",
            severity="warning",
            message="The image has harsh contrast that may hide facial detail.",
            recommendation="Use softer, evenly distributed light and avoid shadows.",
        ),
    )


def score_resolution(
    metrics: RawImageMetrics, settings: Settings
) -> tuple[str, int, QualityIssue | None]:
    if metrics.width < settings.min_image_width or metrics.height < settings.min_image_height:
        return (
            "too_small",
            0,
            QualityIssue(
                code="IMAGE_TOO_SMALL",
                severity="error",
                message="The image resolution is below the required minimum.",
                recommendation=(
                    f"Upload an image at least {settings.min_image_width} x "
                    f"{settings.min_image_height} pixels."
                ),
            ),
        )
    if metrics.width > settings.max_image_width or metrics.height > settings.max_image_height:
        return (
            "too_large",
            0,
            QualityIssue(
                code="IMAGE_DIMENSIONS_TOO_LARGE",
                severity="error",
                message="The image dimensions exceed the supported maximum.",
                recommendation=(
                    f"Use an image no larger than {settings.max_image_width} x "
                    f"{settings.max_image_height} pixels."
                ),
            ),
        )
    if not (
        settings.min_suitable_aspect_ratio
        <= metrics.aspect_ratio
        <= settings.max_suitable_aspect_ratio
    ):
        return (
            "unusual_aspect_ratio",
            70,
            QualityIssue(
                code="IMAGE_UNUSUAL_ASPECT_RATIO",
                severity="warning",
                message="The image is unusually wide or tall.",
                recommendation="Upload a closer, front-facing portrait or square image.",
            ),
        )
    return "suitable", 100, None


def evaluate_image_quality(metrics: RawImageMetrics, settings: Settings) -> QualityEvaluation:
    sharpness_status, sharpness_score, sharpness_issue = score_sharpness(
        metrics.sharpness_variance, settings
    )
    brightness_status, brightness_score, brightness_issue = score_brightness(
        metrics.mean_brightness, settings
    )
    exposure_status, exposure_score, exposure_issues = score_exposure(metrics, settings)
    contrast_status, contrast_score, contrast_issue = score_contrast(
        metrics.contrast_standard_deviation, settings
    )
    resolution_status, resolution_score, resolution_issue = score_resolution(metrics, settings)

    issues = [
        issue
        for issue in [
            sharpness_issue,
            brightness_issue,
            *exposure_issues,
            contrast_issue,
            resolution_issue,
        ]
        if issue is not None
    ]
    quality_score = clamp_score(
        sharpness_score * 0.35
        + brightness_score * 0.25
        + exposure_score * 0.20
        + contrast_score * 0.10
        + resolution_score * 0.10
    )

    has_hard_failure = any(issue.severity == "error" for issue in issues)
    if has_hard_failure or quality_score < settings.quality_warning_score:
        quality_status = "failed"
    elif issues or quality_score < settings.quality_pass_score:
        quality_status = "warning"
    else:
        quality_status = "passed"

    recommendations = list(dict.fromkeys(issue.recommendation for issue in issues))
    return QualityEvaluation(
        sharpness_status=sharpness_status,
        sharpness_score=sharpness_score,
        brightness_status=brightness_status,
        brightness_score=brightness_score,
        exposure_status=exposure_status,
        exposure_score=exposure_score,
        contrast_status=contrast_status,
        contrast_score=contrast_score,
        resolution_status=resolution_status,
        resolution_score=resolution_score,
        quality_score=quality_score,
        quality_status=quality_status,
        issues=issues,
        recommendations=recommendations,
    )
