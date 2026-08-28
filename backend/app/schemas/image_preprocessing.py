from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

PreprocessingStatus = Literal["completed", "warning", "failed", "expired"]
PreprocessingIssueSeverity = Literal["warning", "error"]


class PreprocessingIssue(BaseModel):
    code: str
    severity: PreprocessingIssueSeverity
    message: str
    recommendation: str


class ModelInputMetadata(BaseModel):
    width: int
    height: int
    channels: int
    colour_space: Literal["RGB"]
    data_type: Literal["float32"]
    normalization: Literal["zero_to_one"]
    pixel_range: tuple[float, float]
    resize_mode: Literal["letterbox"]
    channel_order: Literal["RGB"]


class PreprocessingTransformations(BaseModel):
    resize_mode: Literal["letterbox"]
    aspect_ratio_preserved: bool
    padding_applied: bool
    padding_values: dict[str, int]
    upscaling_applied: bool
    denoise_applied: bool
    illumination_adjustment_applied: bool
    white_balance_applied: bool
    sharpening_applied: bool
    alpha_composited: bool


class ImagePreprocessingResponse(BaseModel):
    preprocessing_report_id: str
    upload_id: str
    preprocessing_status: PreprocessingStatus
    model_input: ModelInputMetadata
    transformations: PreprocessingTransformations
    transformation_manifest: dict[str, Any]
    issues: list[PreprocessingIssue]
    can_continue: bool
    next_route: str | None
    created_at: datetime
    updated_at: datetime
