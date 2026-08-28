from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SkinTypeName = Literal["Normal", "Oily", "Dry", "Combination", "Uncertain"]
ResultStatus = Literal["estimated", "uncertain", "failed"]


class SkinTypeResponse(BaseModel):
    skin_type_report_id: str
    upload_id: str
    analysis_mode: Literal["model", "demonstration"] = "model"
    result_status: ResultStatus
    skin_type: SkinTypeName
    confidence: int
    confidence_level: Literal["Low", "Moderate", "High"]
    agreement: Literal["Strong", "Weak", "Conflict", "Insufficient"]
    self_reported_sensitivity: bool | None
    probabilities: dict[str, int]
    explanation: str
    limitations: list[str]
    issues: list[str]
    can_continue: bool
    next_route: str
    created_at: datetime
    updated_at: datetime


class SkinTypeModelStatusResponse(BaseModel):
    loaded: bool
    mode: Literal["model", "demonstration"] | None = None
    reason: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    input_size: list[int] | None = None
    classes: list[str] | None = None
