from datetime import datetime
from typing import Literal

from pydantic import BaseModel

UploadStatus = Literal[
    "uploaded",
    "validated",
    "rejected",
    "expired",
    "processing",
    "completed",
    "failed",
    "quality_checking",
    "quality_passed",
    "quality_warning",
    "quality_failed",
    "face_detection_pending",
    "face_detecting",
    "face_detected",
    "face_detection_warning",
    "face_detection_failed",
    "preprocessing_pending",
    "preprocessing",
    "preprocessing_completed",
    "preprocessing_warning",
    "preprocessing_failed",
    "skin_type_analysis_pending",
    "skin_type_analyzing",
    "skin_type_estimated",
    "skin_type_uncertain",
    "skin_type_analysis_failed",
    "skin_concern_analysis_pending",
    "skin_concern_analyzing",
    "skin_concern_analysis_completed",
    "skin_concern_analysis_uncertain",
    "skin_concern_analysis_failed",
    "product_discovery_pending",
    "product_eligibility_pending",
    "product_eligibility_evaluating",
    "product_eligibility_completed",
    "product_eligibility_completed_with_gaps",
    "product_eligibility_failed",
    "recommendation_scoring_pending",
    "recommendation_scoring",
    "recommendations_completed",
    "recommendations_completed_with_limitations",
    "recommendations_failed",
    "routine_generation_pending",
    "routine_generating",
    "routine_completed",
    "routine_completed_with_limitations",
    "routine_generation_failed",
    "final_report_pending",
    "final_report_generating",
    "final_report_completed",
    "final_report_completed_with_limitations",
    "final_report_incomplete",
    "final_report_failed",
    "workflow_completed",
]


class UploadedFileInfo(BaseModel):
    format: Literal["JPEG", "PNG"]
    size_bytes: int
    width: int
    height: int


class ImageUploadStatusResponse(BaseModel):
    upload_id: str
    status: UploadStatus
    file: UploadedFileInfo
    created_at: datetime
    expires_at: datetime


class ImageUploadResponse(ImageUploadStatusResponse):
    next_route: str = "/image-quality-check"


class ImageUploadDeleteResponse(BaseModel):
    message: str
