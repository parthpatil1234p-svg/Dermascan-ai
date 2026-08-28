from datetime import datetime, timezone

from app.schemas.product_eligibility import EligibilityReason, FilteringBudget, FilteringSkinType
from app.schemas.product_recommendation import RecommendationCandidate, RecommendationContext


def recommendation_context(**overrides):
    values = {
        "skin_type": FilteringSkinType(value="combination", status="estimated", confidence=0.84),
        "concerns": {"visible_oiliness": "observed", "visible_pores": "possible"},
        "self_reported_sensitivity": False,
        "oiliness_level": "High",
        "dryness_level": "Moderate",
        "country": "IN",
        "budget": FilteringBudget(minimum=200, maximum=1000, mandatory=True),
        "preferred_brands": [],
    }
    values.update(overrides)
    return RecommendationContext(**values)


def recommendation_candidate(**overrides):
    now = datetime.now(timezone.utc)
    values = {
        "product_id": "PRD-REC001",
        "product_name": "Test Relevant Cleanser",
        "brand_name": "DermaDemo Labs",
        "normalized_brand_name": "dermademo labs",
        "category": "cleanser",
        "eligibility_status": "eligible",
        "is_demo_product": False,
        "data_type": "verified_manual",
        "suitable_skin_types": ["combination"],
        "target_visible_concerns": ["visible_oiliness", "visible_pores"],
        "normalized_ingredients": ["niacinamide", "glycerin"],
        "highlighted_ingredients": ["Niacinamide", "Glycerin"],
        "ingredient_roles": ["oil-balance support", "moisture support"],
        "sensitivity_suitability": "potentially_suitable",
        "fragrance_status": "fragrance_free",
        "price": {"amount": 499, "currency": "INR"},
        "price_checked_at": now,
        "country_codes": ["IN"],
        "availability_status": "available",
        "availability_checked_at": now,
        "source_verified_at": now,
        "rating": None,
        "cautions": [],
        "positive_matches": [
            EligibilityReason(code="SKIN_TYPE_MATCH", message="Documented match.")
        ],
    }
    values.update(overrides)
    return RecommendationCandidate(**values)


def caution(code, message="A documented caution applies."):
    return EligibilityReason(code=code, message=message)
