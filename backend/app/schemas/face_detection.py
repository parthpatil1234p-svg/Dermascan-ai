from datetime import datetime
from typing import Literal

from pydantic import BaseModel

DetectionStatus = Literal["passed", "warning", "failed"]
IssueSeverity = Literal["warning", "error"]
FacePositionStatus = Literal[
    "centered",
    "slightly_off_center",
    "too_far_off_center",
    "not_applicable",
]
FaceSizeStatus = Literal[
    "acceptable",
    "too_small",
    "too_close",
    "not_applicable",
]


class FaceDetectionIssue(BaseModel):
    code: str
    severity: IssueSeverity
    message: str
    recommendation: str


class FaceCropResponse(BaseModel):
    prepared: bool
    width: int | None = None
    height: int | None = None


class FaceDetectionResponse(BaseModel):
    face_report_id: str
    upload_id: str
    detection_status: DetectionStatus
    face_count: int
    detection_confidence: int | None
    face_position: FacePositionStatus
    face_size: FaceSizeStatus
    crop: FaceCropResponse
    issues: list[FaceDetectionIssue]
    recommendations: list[str]
    warning_accepted: bool
    warning_accepted_at: datetime | None
    can_continue: bool
    next_route: str | None
    created_at: datetime
    updated_at: datetime


class FaceWarningAcceptanceResponse(BaseModel):
    face_report_id: str
    upload_id: str
    detection_status: Literal["warning"]
    warning_accepted: bool
    warning_accepted_at: datetime
    can_continue: bool
    next_route: str
