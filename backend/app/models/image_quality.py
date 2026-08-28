from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId

from app.schemas.image_quality import (
    BrightnessMetric,
    ContrastMetric,
    ExposureMetric,
    ImageQualityResponse,
    QualityIssue,
    QualityMetricsResponse,
    ResolutionMetric,
    SharpnessMetric,
)
from app.services.image_quality_scoring_service import QualityEvaluation
from app.utils.image_metrics import RawImageMetrics


def build_image_quality_document(
    *,
    upload_id: str,
    user_id: str,
    raw_metrics: RawImageMetrics,
    evaluation: QualityEvaluation,
    now: datetime,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "quality_report_id": (existing["quality_report_id"] if existing else str(uuid4())),
        "upload_id": upload_id,
        "user_id": ObjectId(user_id),
        "sharpness_value": round(raw_metrics.sharpness_variance, 3),
        "sharpness_score": evaluation.sharpness_score,
        "sharpness_status": evaluation.sharpness_status,
        "brightness_value": round(raw_metrics.mean_brightness, 3),
        "brightness_min": raw_metrics.min_brightness,
        "brightness_max": raw_metrics.max_brightness,
        "brightness_score": evaluation.brightness_score,
        "brightness_status": evaluation.brightness_status,
        "contrast_value": round(raw_metrics.contrast_standard_deviation, 3),
        "contrast_score": evaluation.contrast_score,
        "contrast_status": evaluation.contrast_status,
        "exposure_score": evaluation.exposure_score,
        "exposure_status": evaluation.exposure_status,
        "underexposed_pixel_percent": round(raw_metrics.underexposed_pixel_percent, 3),
        "overexposed_pixel_percent": round(raw_metrics.overexposed_pixel_percent, 3),
        "width": raw_metrics.width,
        "height": raw_metrics.height,
        "aspect_ratio": round(raw_metrics.aspect_ratio, 4),
        "resolution_score": evaluation.resolution_score,
        "resolution_status": evaluation.resolution_status,
        "quality_score": evaluation.quality_score,
        "quality_status": evaluation.quality_status,
        "issues": [issue.model_dump() for issue in evaluation.issues],
        "recommendations": evaluation.recommendations,
        "warning_accepted": False,
        "warning_accepted_at": None,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }


def image_quality_document_to_response(
    document: dict[str, Any],
) -> ImageQualityResponse:
    quality_status = document["quality_status"]
    warning_accepted = bool(document.get("warning_accepted", False))
    can_continue = quality_status == "passed" or (quality_status == "warning" and warning_accepted)
    if can_continue:
        next_route = "/face-detection"
    elif quality_status == "failed":
        next_route = "/face-scan"
    else:
        next_route = None

    return ImageQualityResponse(
        quality_report_id=document["quality_report_id"],
        upload_id=document["upload_id"],
        quality_status=quality_status,
        quality_score=document["quality_score"],
        metrics=QualityMetricsResponse(
            sharpness=SharpnessMetric(
                status=document["sharpness_status"],
                score=document["sharpness_score"],
            ),
            brightness=BrightnessMetric(
                status=document["brightness_status"],
                score=document["brightness_score"],
                mean=round(document["brightness_value"], 1),
            ),
            exposure=ExposureMetric(
                status=document["exposure_status"],
                score=document["exposure_score"],
                underexposed_percent=round(document["underexposed_pixel_percent"], 1),
                overexposed_percent=round(document["overexposed_pixel_percent"], 1),
            ),
            contrast=ContrastMetric(
                status=document["contrast_status"],
                score=document["contrast_score"],
                value=round(document["contrast_value"], 1),
            ),
            resolution=ResolutionMetric(
                status=document["resolution_status"],
                width=document["width"],
                height=document["height"],
                aspect_ratio=round(document["aspect_ratio"], 2),
                score=document["resolution_score"],
            ),
        ),
        issues=[QualityIssue(**issue) for issue in document.get("issues", [])],
        recommendations=document.get("recommendations", []),
        warning_accepted=warning_accepted,
        warning_accepted_at=document.get("warning_accepted_at"),
        can_continue=can_continue,
        next_route=next_route,
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
