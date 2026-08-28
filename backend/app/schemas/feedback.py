from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.pagination import PaginationMetadata

FeedbackCategory = Literal[
    "analysis_feedback",
    "skin_type_feedback",
    "skin_concern_feedback",
    "product_recommendation_feedback",
    "product_experience_feedback",
    "routine_feedback",
    "report_feedback",
    "application_feedback",
]
FeedbackStatus = Literal["active", "edited", "withdrawn", "flagged", "archived"]
ModerationStatus = Literal["clear", "flagged", "reviewed"]
AccuracyPerception = Literal[
    "matches_experience", "partially_matches", "does_not_match", "not_sure"
]
UserAssessment = Literal["helpful", "partially_helpful", "not_helpful", "not_sure"]
PriceFeedback = Literal[
    "within_budget", "slightly_expensive", "too_expensive", "price_changed", "price_unknown"
]
AvailabilityFeedback = Literal["available", "limited", "unavailable", "not_checked"]
ProductExperienceStatus = Literal[
    "not_used", "used_once", "used_short_term", "used_longer_term", "stopped_using"
]
IrritationStatus = Literal[
    "no_issue", "mild_discomfort", "visible_irritation", "serious_reaction", "not_sure"
]
RoutineDifficulty = Literal["very_easy", "easy", "manageable", "difficult", "too_complex"]
ReportLength = Literal["too_short", "appropriate", "too_long"]
TechnicalDetailLevel = Literal["too_simple", "appropriate", "too_technical"]


POSITIVE_REASON_CODES = (
    "RESULT_EASY_TO_UNDERSTAND",
    "SKIN_TYPE_SEEMS_RELEVANT",
    "VISIBLE_OBSERVATIONS_HELPFUL",
    "PRODUCTS_MATCH_BUDGET",
    "PRODUCTS_AVAILABLE_LOCALLY",
    "PRODUCTS_MATCH_PREFERENCES",
    "ROUTINE_IS_SIMPLE",
    "REPORT_IS_CLEAR",
)
NEGATIVE_REASON_CODES = (
    "SKIN_TYPE_DOES_NOT_MATCH_EXPERIENCE",
    "VISIBLE_OBSERVATION_SEEMS_INCORRECT",
    "PRODUCT_TOO_EXPENSIVE",
    "PRODUCT_NOT_AVAILABLE",
    "PRODUCT_CONTAINS_UNWANTED_INGREDIENT",
    "PRODUCT_DOES_NOT_MATCH_BRAND_PREFERENCE",
    "TOO_MANY_ROUTINE_STEPS",
    "ROUTINE_TOO_COMPLEX",
    "REPORT_TOO_TECHNICAL",
    "APPLICATION_ERROR",
    "OTHER",
)
PRODUCT_EXPERIENCE_REASON_CODES = (
    "PRODUCT_WORKED_WELL",
    "PRODUCT_TEXTURE_NOT_PREFERRED",
    "PRODUCT_CAUSED_DISCOMFORT",
    "PRODUCT_CAUSED_VISIBLE_IRRITATION",
    "PRODUCT_LABEL_DIFFERENT_FROM_CATALOGUE",
    "PRODUCT_PRICE_CHANGED",
    "PRODUCT_UNAVAILABLE",
    "STOPPED_USING_PRODUCT",
)
FEEDBACK_REASON_CODES = (
    *POSITIVE_REASON_CODES,
    *NEGATIVE_REASON_CODES,
    *PRODUCT_EXPERIENCE_REASON_CODES,
)


class FeedbackPayload(BaseModel):
    final_report_id: str | None = Field(default=None, max_length=40)
    recommendation_report_id: str | None = Field(default=None, max_length=80)
    routine_report_id: str | None = Field(default=None, max_length=80)
    product_id: str | None = Field(default=None, max_length=80)
    feedback_category: FeedbackCategory
    overall_rating: int | None = Field(default=None, ge=1, le=5)
    helpfulness_rating: int | None = Field(default=None, ge=1, le=5)
    clarity_rating: int | None = Field(default=None, ge=1, le=5)
    accuracy_perception: AccuracyPerception | None = None
    concern_code: str | None = Field(default=None, max_length=80)
    user_assessment: UserAssessment | None = None
    recommendation_relevance: int | None = Field(default=None, ge=1, le=5)
    price_feedback: PriceFeedback | None = None
    availability_feedback: AvailabilityFeedback | None = None
    preference_match: bool | None = None
    product_experience_status: ProductExperienceStatus | None = None
    irritation_reported: IrritationStatus | None = None
    irritation_description: str | None = None
    exclude_product_from_future_recommendations: bool = False
    routine_practicality: int | None = Field(default=None, ge=1, le=5)
    routine_difficulty: RoutineDifficulty | None = None
    step_count_preference: str | None = Field(default=None, max_length=80)
    morning_routine_feedback: str | None = None
    night_routine_feedback: str | None = None
    report_clarity: int | None = Field(default=None, ge=1, le=5)
    report_length: ReportLength | None = None
    technical_detail_level: TechnicalDetailLevel | None = None
    export_experience: str | None = None
    selected_reasons: list[str] = Field(default_factory=list, max_length=20)
    comment: str | None = None
    consent_for_analytics: bool = False
    consent_for_research_review: bool = False
    is_anonymous_for_aggregate_use: bool = True

    @model_validator(mode="after")
    def validate_category_fields(self) -> "FeedbackPayload":
        invalid_reasons = sorted(set(self.selected_reasons) - set(FEEDBACK_REASON_CODES))
        if invalid_reasons:
            raise ValueError(f"Unsupported feedback reason: {invalid_reasons[0]}.")
        if len(self.selected_reasons) != len(set(self.selected_reasons)):
            raise ValueError("Feedback reasons must not contain duplicates.")
        related_categories = {
            "analysis_feedback",
            "skin_type_feedback",
            "skin_concern_feedback",
            "product_recommendation_feedback",
            "product_experience_feedback",
            "routine_feedback",
            "report_feedback",
        }
        if self.feedback_category in related_categories and not (
            self.final_report_id or self.recommendation_report_id or self.routine_report_id
        ):
            raise ValueError("This feedback category requires a related report.")
        if self.feedback_category == "skin_type_feedback" and not self.accuracy_perception:
            raise ValueError("Skin-type feedback requires an accuracy perception.")
        if self.feedback_category == "skin_concern_feedback" and not (
            self.concern_code and self.user_assessment
        ):
            raise ValueError("Visible-observation feedback requires an observation and assessment.")
        product_categories = {"product_recommendation_feedback", "product_experience_feedback"}
        if self.feedback_category in product_categories and not self.product_id:
            raise ValueError("Product feedback requires a recommended product.")
        if self.feedback_category == "product_experience_feedback":
            if self.product_experience_status in {None, "not_used"}:
                raise ValueError(
                    "Confirm that you have used the product before sharing experience feedback."
                )
            if self.irritation_reported is None:
                raise ValueError(
                    "Product experience feedback requires a response about discomfort or irritation."
                )
        if self.exclude_product_from_future_recommendations and self.irritation_reported not in {
            "mild_discomfort",
            "visible_irritation",
            "serious_reaction",
        }:
            raise ValueError(
                "Product avoidance can be requested only after reporting discomfort or irritation."
            )
        if self.feedback_category == "routine_feedback" and not (
            self.routine_practicality or self.routine_difficulty
        ):
            raise ValueError(
                "Routine feedback requires a practicality rating or difficulty selection."
            )
        if self.feedback_category == "report_feedback" and not (
            self.report_clarity or self.overall_rating
        ):
            raise ValueError("Report feedback requires a clarity or overall rating.")
        if self.feedback_category in {"analysis_feedback", "application_feedback"} and not (
            self.overall_rating or (self.comment and self.comment.strip())
        ):
            raise ValueError("Provide an overall rating or comment.")
        return self


class FeedbackCreate(FeedbackPayload):
    pass


class FeedbackUpdate(FeedbackPayload):
    pass


class FeedbackResponse(FeedbackPayload):
    feedback_id: str
    upload_id: str | None = None
    feedback_status: FeedbackStatus
    moderation_status: ModerationStatus
    moderation_reasons: list[str]
    product_name: str | None = None
    created_at: datetime
    updated_at: datetime
    withdrawn_at: datetime | None = None
    acknowledgement: str | None = None


class FeedbackListResponse(BaseModel):
    feedback: list[FeedbackResponse]
    pagination: PaginationMetadata


class FeedbackWithdrawalResponse(BaseModel):
    feedback_id: str
    feedback_status: Literal["withdrawn"]
    withdrawn_at: datetime
    message: str


class FeedbackOptionsResponse(BaseModel):
    categories: list[dict[str, str]]
    ratings: list[dict[str, int | str]]
    reason_groups: dict[str, list[str]]
    values: dict[str, list[str]]


class ProductAvoidanceResponse(BaseModel):
    product_id: str
    product_name: str | None = None
    avoidance_reason: str
    source_feedback_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductAvoidanceListResponse(BaseModel):
    avoidances: list[ProductAvoidanceResponse]


class ModerationRequest(BaseModel):
    moderation_status: Literal["clear", "flagged", "reviewed"]
    feedback_status: Literal["active", "flagged", "archived"]
    moderation_note: str = Field(min_length=2, max_length=500)


class CatalogueReviewUpdate(BaseModel):
    review_status: Literal["pending", "under_review", "resolved", "dismissed"]
    resolution_notes: str | None = Field(default=None, max_length=1000)
