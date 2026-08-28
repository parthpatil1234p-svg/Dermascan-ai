from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.pagination import PaginationMetadata
from app.schemas.product import ProductSummaryResponse

EligibilityStatus = Literal[
    "eligible", "eligible_with_caution", "excluded", "insufficient_information"
]


class EligibilityReason(BaseModel):
    code: str
    message: str
    matched_value: str | None = None


class NormalizedAllergy(BaseModel):
    original: str
    normalized: str | None = None
    mapping_status: Literal["mapped", "unmapped"]


class NormalizedAvoidance(BaseModel):
    original: str
    normalized: str | None = None
    match_type: Literal["ingredient", "category", "unmapped"]


class FilteringSkinType(BaseModel):
    value: str
    status: Literal["estimated", "uncertain"]
    confidence: float = Field(ge=0, le=1)


class FilteringBudget(BaseModel):
    minimum: float | None = None
    maximum: float | None = None
    currency: str = "INR"
    mandatory: bool


class UserFilteringContext(BaseModel):
    user_id: str
    age_group: str
    country: str
    skin_type: FilteringSkinType
    visible_concerns: list[str]
    self_reported_sensitivity: bool | None
    known_allergies: list[NormalizedAllergy]
    ingredients_to_avoid: list[NormalizedAvoidance]
    fragrance_preference: Literal["fragrance_free_only", "prefer_fragrance_free", "no_preference"]
    budget: FilteringBudget
    preferred_brands: list[str]


class StoredProductEligibilityResult(BaseModel):
    product_id: str
    product_name: str
    brand_name: str
    category: str
    is_demo_product: bool
    price: dict | None = None
    price_checked_at: datetime | None = None
    availability_status: str
    availability_checked_at: datetime | None = None
    eligibility_status: EligibilityStatus
    hard_exclusions: list[EligibilityReason]
    cautions: list[EligibilityReason]
    positive_matches: list[EligibilityReason]
    information_gaps: list[EligibilityReason]


class EligibilityCandidateResponse(BaseModel):
    product_id: str
    product_name: str
    brand_name: str
    category: str
    is_demo_product: bool
    demo_label: str | None = None
    price: dict | None = None
    price_checked_at: datetime | None = None
    availability_status: str
    availability_checked_at: datetime | None = None
    eligibility_status: EligibilityStatus
    positive_match_count: int
    caution_count: int
    exclusion_count: int
    information_gap_count: int
    primary_reasons: list[EligibilityReason]


class EligibilitySummary(BaseModel):
    total_evaluated: int
    eligible: int
    eligible_with_caution: int
    excluded: int
    insufficient_information: int


class ProductEligibilityReportResponse(BaseModel):
    eligibility_report_id: str
    upload_id: str
    summary: EligibilitySummary
    candidate_products: list[EligibilityCandidateResponse]
    pagination: PaginationMetadata
    can_continue: bool
    next_route: str
    created_at: datetime
    updated_at: datetime


class ProductEligibilityDetailResponse(BaseModel):
    upload_id: str
    product: ProductSummaryResponse
    eligibility_status: EligibilityStatus
    hard_exclusions: list[EligibilityReason]
    cautions: list[EligibilityReason]
    positive_matches: list[EligibilityReason]
    information_gaps: list[EligibilityReason]
    disclaimer: str
