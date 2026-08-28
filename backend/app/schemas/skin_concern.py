from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ConcernObservationResponse(BaseModel):
    code: str
    name: str
    status: Literal["observed", "possible", "uncertain"]
    visible_severity: Literal["mild", "moderate", "prominent", "uncertain"]
    confidence: int
    regions: list[str]
    explanation: str
    questionnaire_agreement: str
    questionnaire_reported_value: str | None = None
    questionnaire_explanation: str
    limitations: list[str]


class SkinConcernResponse(BaseModel):
    skin_concern_report_id: str
    upload_id: str
    analysis_mode: Literal["model", "demonstration"] = "model"
    overall_status: Literal["completed", "completed_with_uncertainty", "failed"]
    observations: list[ConcernObservationResponse]
    uncertain_observations: list[ConcernObservationResponse]
    region_information_available: bool
    issues: list[str]
    limitations: list[str]
    can_continue: bool
    next_route: str
    created_at: datetime
    updated_at: datetime


class SkinConcernModelStatusResponse(BaseModel):
    loaded: bool
    mode: Literal["model", "demonstration"] | None = None
    reason: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    number_of_labels: int | None = None
    thresholds_calibrated: bool | None = None
    supported_observations: list[str] | None = None
