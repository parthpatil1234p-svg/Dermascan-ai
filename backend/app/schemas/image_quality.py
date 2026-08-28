from datetime import datetime
from typing import Literal

from pydantic import BaseModel

QualityStatus = Literal["passed", "warning", "failed"]
IssueSeverity = Literal["warning", "error"]


class QualityIssue(BaseModel):
    code: str
    severity: IssueSeverity
    message: str
    recommendation: str


class SharpnessMetric(BaseModel):
    status: Literal["clear", "slightly_blurry", "too_blurry"]
    score: int


class BrightnessMetric(BaseModel):
    status: Literal[
        "too_dark",
        "slightly_dark",
        "acceptable",
        "slightly_bright",
        "too_bright",
    ]
    score: int
    mean: float


class ExposureMetric(BaseModel):
    status: Literal["acceptable", "underexposed", "overexposed", "mixed_exposure"]
    score: int
    underexposed_percent: float
    overexposed_percent: float


class ContrastMetric(BaseModel):
    status: Literal["low", "acceptable", "high"]
    score: int
    value: float


class ResolutionMetric(BaseModel):
    status: Literal["suitable", "too_small", "too_large", "unusual_aspect_ratio"]
    width: int
    height: int
    aspect_ratio: float
    score: int


class QualityMetricsResponse(BaseModel):
    sharpness: SharpnessMetric
    brightness: BrightnessMetric
    exposure: ExposureMetric
    contrast: ContrastMetric
    resolution: ResolutionMetric


class ImageQualityResponse(BaseModel):
    quality_report_id: str
    upload_id: str
    quality_status: QualityStatus
    quality_score: int
    metrics: QualityMetricsResponse
    issues: list[QualityIssue]
    recommendations: list[str]
    warning_accepted: bool
    warning_accepted_at: datetime | None
    can_continue: bool
    next_route: str | None
    created_at: datetime
    updated_at: datetime


class WarningAcceptanceResponse(BaseModel):
    quality_report_id: str
    upload_id: str
    quality_status: Literal["warning"]
    warning_accepted: bool
    warning_accepted_at: datetime
    can_continue: bool
    next_route: str
