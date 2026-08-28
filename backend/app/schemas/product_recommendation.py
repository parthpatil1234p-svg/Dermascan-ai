from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.pagination import PaginationMetadata
from app.schemas.product import ProductSummaryResponse
from app.schemas.product_eligibility import EligibilityReason, FilteringBudget, FilteringSkinType

RecommendationConfidence = Literal["high", "moderate", "low"]
ScoreBand = Literal["Excellent Match", "Strong Match", "Good Match", "Moderate Match", "Low Match"]


class RecommendationCandidate(BaseModel):
    product_id: str
    product_name: str
    brand_name: str
    normalized_brand_name: str
    category: str
    eligibility_status: Literal["eligible", "eligible_with_caution"]
    is_demo_product: bool
    data_type: str
    suitable_skin_types: list[str]
    target_visible_concerns: list[str]
    normalized_ingredients: list[str]
    highlighted_ingredients: list[str]
    ingredient_roles: list[str]
    sensitivity_suitability: str
    fragrance_status: str
    price: dict | None = None
    price_checked_at: datetime | None = None
    country_codes: list[str]
    availability_status: str
    availability_checked_at: datetime | None = None
    source_verified_at: datetime | None = None
    rating: dict | None = None
    cautions: list[EligibilityReason]
    positive_matches: list[EligibilityReason]


class RecommendationContext(BaseModel):
    skin_type: FilteringSkinType
    concerns: dict[str, Literal["observed", "possible", "uncertain", "not_observed"]]
    self_reported_sensitivity: bool | None
    oiliness_level: str
    dryness_level: str
    country: str
    budget: FilteringBudget
    preferred_brands: list[str]


class AppliedPenalty(BaseModel):
    code: str
    amount: float = Field(ge=0, le=100)
    message: str


class RecommendationScoreBreakdown(BaseModel):
    skin_type_match: float = Field(ge=0, le=100)
    visible_concern_match: float = Field(ge=0, le=100)
    ingredient_relevance: float = Field(ge=0, le=100)
    sensitivity_compatibility: float = Field(ge=0, le=100)
    budget_fit: float = Field(ge=0, le=100)
    availability: float = Field(ge=0, le=100)
    brand_preference: float = Field(ge=0, le=100)
    data_quality: float = Field(ge=0, le=100)
    rating: float = Field(ge=0, le=100)
    base_score: float = Field(ge=0, le=100)
    caution_penalty: float = Field(ge=0, le=100)
    final_score: float = Field(ge=0, le=100)


class RecommendationFreshness(BaseModel):
    price: Literal["fresh", "stale", "missing"]
    availability: Literal["fresh", "stale", "missing"]
    source: Literal["fresh", "stale", "missing"]


class StoredRecommendation(BaseModel):
    product_id: str
    product_name: str
    brand_name: str
    normalized_brand_name: str
    category: str
    is_demo_product: bool
    price: dict | None = None
    availability_status: str
    eligibility_status: Literal["eligible", "eligible_with_caution"]
    base_score: float
    penalties: list[AppliedPenalty]
    total_penalty: float
    final_score: float
    score_band: ScoreBand
    score_breakdown: RecommendationScoreBreakdown
    positive_factors: list[str]
    caution_factors: list[str]
    why_recommended: str
    recommendation_confidence: RecommendationConfidence
    confidence_reasons: list[str]
    data_freshness: RecommendationFreshness
    ingredient_profile: list[str]
    price_tier: str
    rank_within_category: int | None = None
    overall_rank: int | None = None


class RecommendationProductResponse(BaseModel):
    rank: int
    overall_rank: int
    product_id: str
    product_name: str
    brand_name: str
    category: str
    is_demo_product: bool
    demo_label: str | None = None
    price: dict | None = None
    availability_status: str
    eligibility_status: Literal["eligible", "eligible_with_caution"]
    base_score: float
    caution_penalty: float
    final_score: float
    score_band: ScoreBand
    why_recommended: str
    positive_factors: list[str]
    caution_factors: list[str]
    score_breakdown: RecommendationScoreBreakdown
    applied_penalties: list[AppliedPenalty]
    recommendation_confidence: RecommendationConfidence
    confidence_reasons: list[str]
    data_freshness: RecommendationFreshness


class ProductRecommendationReportResponse(BaseModel):
    recommendation_report_id: str
    upload_id: str
    overall_confidence: RecommendationConfidence
    confidence_reasons: list[str]
    categories: dict[str, list[RecommendationProductResponse]]
    limitations: list[str]
    candidate_count: int
    recommended_count: int
    pagination: PaginationMetadata
    can_continue: bool
    next_route: str
    created_at: datetime
    updated_at: datetime


class ProductRecommendationDetailResponse(BaseModel):
    upload_id: str
    product: ProductSummaryResponse
    recommendation: RecommendationProductResponse
    disclaimer: str
