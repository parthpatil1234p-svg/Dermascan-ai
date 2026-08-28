from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.pagination import PaginationMetadata
from app.schemas.skincare_routine import RoutineAlternative, RoutineStep

FinalReportStatus = Literal[
    "complete", "complete_with_limitations", "incomplete", "failed", "superseded"
]
PrivacyMode = Literal["standard", "privacy_reduced", "technical"]


class IngredientGuidanceItem(BaseModel):
    ingredient_role: str | None = None
    examples: list[str] = Field(default_factory=list)
    item: str | None = None
    reason: str


class IngredientGuidance(BaseModel):
    potentially_relevant: list[IngredientGuidanceItem]
    avoid_or_review: list[IngredientGuidanceItem]


class ProductRecommendationSnapshot(BaseModel):
    rank: int
    product_id: str
    product_name: str
    brand_name: str
    category: str
    score: float
    score_band: str
    why_recommended: str
    cautions: list[str]
    price_at_report_time: dict[str, Any] | None = None
    price_checked_at: datetime | None = None
    availability_at_report_time: str
    availability_checked_at: datetime | None = None
    source_verified_at: datetime | None = None
    source_status: str
    demo_status: bool


class FinalReportGenerationResponse(BaseModel):
    final_report_id: str
    upload_id: str
    report_version: int
    report_status: FinalReportStatus
    analysis_mode: Literal["model", "demonstration"] = "model"
    title: str
    summary: str
    generated_at: datetime
    sections_available: list[str]
    print_url: str
    can_export_pdf: bool


class FinalReportResponse(FinalReportGenerationResponse):
    analysis_date: datetime
    skin_profile_summary: dict[str, Any]
    image_processing_summary: dict[str, Any]
    skin_type_summary: dict[str, Any]
    visible_concern_summary: dict[str, list[dict[str, Any]]]
    ingredient_guidance: IngredientGuidance
    product_recommendations: list[ProductRecommendationSnapshot]
    morning_routine: list[RoutineStep]
    night_routine: list[RoutineStep]
    optional_products: list[RoutineAlternative]
    safety_guidance: list[str]
    limitations: list[str]
    medical_disclaimer: str
    data_freshness: list[dict[str, Any]]
    model_versions: dict[str, str]
    engine_versions: dict[str, str]
    source_report_ids: dict[str, str]
    source_versions: dict[str, str]
    supersedes_report_id: str | None = None
    superseded_by_report_id: str | None = None
    is_archived: bool
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class FinalReportListItem(BaseModel):
    final_report_id: str
    report_version: int
    report_status: FinalReportStatus
    analysis_date: datetime
    generated_at: datetime
    skin_type: str
    main_visible_observations: list[str]
    routine_status: str
    is_archived: bool


class FinalReportListResponse(BaseModel):
    reports: list[FinalReportListItem]
    pagination: PaginationMetadata


class FinalReportArchiveResponse(BaseModel):
    final_report_id: str
    is_archived: bool
    archived_at: datetime
    message: str


class PdfExportRequest(BaseModel):
    privacy_mode: PrivacyMode = "standard"
