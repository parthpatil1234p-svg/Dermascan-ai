from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.rules.category_rules import BASIC_ROUTINE_CATEGORIES
from app.rules.caution_penalties import ACTIVE_CAUTION_CODES, get_penalty_configuration
from app.rules.scoring_weights import get_scoring_weights
from app.schemas.product_recommendation import (
    AppliedPenalty,
    RecommendationCandidate,
    RecommendationContext,
    RecommendationFreshness,
    RecommendationScoreBreakdown,
)


def clamp(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def score_skin_type(candidate: RecommendationCandidate, context: RecommendationContext) -> float:
    mappings = set(candidate.suitable_skin_types)
    if context.skin_type.status == "uncertain":
        if "all_skin_types" in mappings:
            return 90.0
        if len(mappings) >= 2:
            return 80.0
        return 50.0 if mappings else 25.0
    if context.skin_type.value in mappings:
        return 100.0
    if "all_skin_types" in mappings:
        return 85.0
    partial_pairs = {
        "combination": {"oily", "normal"},
        "oily": {"combination"},
        "dry": {"normal"},
        "normal": {"combination", "dry"},
    }
    if mappings & partial_pairs.get(context.skin_type.value, set()):
        return 70.0
    return 20.0 if mappings else 40.0


def score_visible_concerns(
    candidate: RecommendationCandidate,
    context: RecommendationContext,
) -> float:
    weights = {"observed": 1.0, "possible": 0.5, "uncertain": 0.0, "not_observed": 0.0}
    relevant = {
        code: weights[status] for code, status in context.concerns.items() if weights[status] > 0
    }
    if not relevant:
        return 60.0 if candidate.category in BASIC_ROUTINE_CATEGORIES else 30.0
    matched = sum(
        weight for code, weight in relevant.items() if code in candidate.target_visible_concerns
    )
    calculated = matched / sum(relevant.values()) * 100.0
    if candidate.category in BASIC_ROUTINE_CATEGORIES:
        return max(60.0, calculated)
    return calculated if matched else 25.0


def _relevant_role_terms(context: RecommendationContext, category: str) -> set[str]:
    terms = {"hydration", "moisture", "barrier", "comfort", "softening"}
    concern_terms = {
        "visible_oiliness": {"oil-balance", "visible pores", "exfoliation"},
        "visible_pores": {"visible pores", "oil-balance", "exfoliation"},
        "dry_looking_areas": {"hydration", "moisture", "barrier", "softening"},
        "visible_redness": {"comfort", "barrier"},
        "uneven_looking_tone": {"uneven tone", "antioxidant"},
        "dark_spots": {"uneven tone", "antioxidant"},
        "acne_like_spots": {"oil-balance", "exfoliation"},
        "under_eye_darkness": {"hydration", "antioxidant"},
        "dull_looking_appearance": {"dull", "antioxidant", "exfoliation"},
        "fine_line_visibility": {"hydration", "antioxidant", "moisture"},
    }
    for code, status in context.concerns.items():
        if status in {"observed", "possible"}:
            terms.update(concern_terms.get(code, set()))
    if context.oiliness_level == "High":
        terms.update({"oil-balance", "visible pores"})
    if context.dryness_level == "High":
        terms.update({"hydration", "moisture", "barrier", "softening"})
    if category == "sunscreen":
        terms.add("uv filter")
    return terms


def score_ingredient_relevance(
    candidate: RecommendationCandidate,
    context: RecommendationContext,
) -> float:
    if not candidate.normalized_ingredients:
        return 0.0
    roles = {role.casefold() for role in candidate.ingredient_roles}
    terms = _relevant_role_terms(context, candidate.category)
    matches = {role for role in roles if any(term in role for term in terms)}
    if len(matches) >= 3:
        return 100.0
    if len(matches) == 2:
        return 90.0
    if len(matches) == 1:
        return 72.0
    return 35.0 if roles else 20.0


def score_sensitivity(candidate: RecommendationCandidate, context: RecommendationContext) -> float:
    reported = context.self_reported_sensitivity is True
    if reported:
        values = {
            "potentially_suitable": 100.0,
            "use_with_caution": 55.0,
            "not_specified": 45.0,
            "unknown": 30.0,
        }
    else:
        values = {
            "potentially_suitable": 90.0,
            "use_with_caution": 70.0,
            "not_specified": 70.0,
            "unknown": 55.0,
        }
    return values.get(candidate.sensitivity_suitability, 55.0)


def score_budget(candidate: RecommendationCandidate, context: RecommendationContext) -> float:
    if candidate.price is None:
        return 0.0
    amount = float(candidate.price["amount"])
    minimum, maximum = context.budget.minimum, context.budget.maximum
    if minimum is None and maximum is None:
        return 70.0
    minimum = minimum or 0.0
    maximum = maximum if maximum is not None else amount
    if amount < minimum:
        return 65.0
    if amount > maximum:
        if context.budget.mandatory or maximum <= 0:
            return 0.0
        overage = (amount - maximum) / maximum
        if overage <= 0.05:
            return 50.0
        if overage <= 0.10:
            return 30.0
        return 0.0
    span = maximum - minimum
    if span <= 0:
        return 100.0
    position = (amount - minimum) / span
    if position <= 0.5:
        return 100.0
    if position <= 0.8:
        return 90.0
    if position < 1.0:
        return 75.0
    return 65.0


def score_availability(candidate: RecommendationCandidate) -> float:
    return {
        "available": 100.0,
        "limited": 60.0,
        "unknown": 25.0,
        "unavailable": 0.0,
    }.get(candidate.availability_status, 25.0)


def score_brand(candidate: RecommendationCandidate, context: RecommendationContext) -> float:
    if not context.preferred_brands:
        return 70.0
    return 100.0 if candidate.normalized_brand_name in context.preferred_brands else 50.0


def score_data_quality(
    candidate: RecommendationCandidate, freshness: RecommendationFreshness
) -> float:
    if candidate.is_demo_product:
        score = 70.0
    elif candidate.data_type in {"verified_real", "verified_manual"}:
        score = 100.0
    else:
        score = 50.0
    stale_count = sum(value != "fresh" for value in freshness.model_dump().values())
    return clamp(score - stale_count * 10.0)


def score_rating(candidate: RecommendationCandidate) -> float:
    if not candidate.rating:
        return 50.0
    value = float(candidate.rating.get("value", 0))
    count = max(0, int(candidate.rating.get("count", 0)))
    prior_value, prior_count = 3.5, 20
    adjusted = (count * value + prior_count * prior_value) / (count + prior_count)
    return clamp(adjusted / 5.0 * 100.0)


def _freshness(value: datetime | None, days: int) -> str:
    if value is None:
        return "missing"
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return "stale" if value < datetime.now(timezone.utc) - timedelta(days=days) else "fresh"


def get_data_freshness(
    candidate: RecommendationCandidate,
    settings: Settings,
) -> RecommendationFreshness:
    return RecommendationFreshness(
        price=_freshness(candidate.price_checked_at, settings.product_price_stale_days),
        availability=_freshness(
            candidate.availability_checked_at,
            settings.product_availability_stale_days,
        ),
        source=_freshness(
            candidate.source_verified_at,
            settings.product_source_verification_stale_days,
        ),
    )


def calculate_penalties(
    candidate: RecommendationCandidate,
    context: RecommendationContext,
    settings: Settings,
) -> tuple[list[AppliedPenalty], float]:
    config = get_penalty_configuration(settings)
    reason_codes = {reason.code for reason in candidate.cautions}
    penalties: list[AppliedPenalty] = []

    def add(code: str, amount: float, message: str) -> None:
        if amount > 0 and code not in {item.code for item in penalties}:
            penalties.append(AppliedPenalty(code=code, amount=amount, message=message))

    if candidate.eligibility_status == "eligible_with_caution":
        add(
            "ELIGIBLE_WITH_CAUTION",
            config["eligible_with_caution"],
            "The eligibility report contains caution factors.",
        )
    if "SENSITIVITY_NOT_SPECIFIED" in reason_codes:
        add(
            "SENSITIVITY_NOT_SPECIFIED",
            config["sensitivity_not_specified"],
            "Sensitivity suitability was not specified.",
        )
    if reason_codes & ACTIVE_CAUTION_CODES:
        add(
            "ACTIVE_INGREDIENT_CAUTION",
            config["active_ingredient_caution"],
            "An active-ingredient caution applies.",
        )
    if "FRAGRANCE_CONFLICT" in reason_codes:
        add(
            "FRAGRANCE_PREFERENCE_CONFLICT",
            config["fragrance_preference_conflict"],
            "The product conflicts with the fragrance preference.",
        )
    if "PRICE_DATA_STALE" in reason_codes:
        add("PRICE_DATA_STALE", config["price_stale"], "Price information may be outdated.")
    if "AVAILABILITY_DATA_STALE" in reason_codes:
        add(
            "AVAILABILITY_DATA_STALE",
            config["availability_stale"],
            "Availability information may be outdated.",
        )
    if "LIMITED_AVAILABILITY" in reason_codes:
        add(
            "LIMITED_AVAILABILITY",
            config["limited_availability"],
            "Availability is limited in the selected country.",
        )
    if reason_codes & {"INGREDIENT_DATA_INCOMPLETE", "SOURCE_DATA_STALE"}:
        add(
            "SIGNIFICANT_DATA_GAP",
            config["significant_data_gap"],
            "A non-critical catalogue data limitation applies.",
        )
    if context.skin_type.status == "uncertain":
        add(
            "UNCERTAIN_SKIN_TYPE",
            config["uncertain_skin_type"],
            "The broad skin-type estimate was uncertain.",
        )
    total = min(sum(item.amount for item in penalties), config["maximum_total"])
    if total < sum(item.amount for item in penalties):
        running = 0.0
        capped: list[AppliedPenalty] = []
        for item in penalties:
            remaining = max(0.0, total - running)
            amount = min(item.amount, remaining)
            if amount:
                capped.append(item.model_copy(update={"amount": amount}))
                running += amount
        penalties = capped
    return penalties, total


def score_band(score: float) -> str:
    if score >= 90:
        return "Excellent Match"
    if score >= 80:
        return "Strong Match"
    if score >= 70:
        return "Good Match"
    if score >= 60:
        return "Moderate Match"
    return "Low Match"


def calculate_score_breakdown(
    candidate: RecommendationCandidate,
    context: RecommendationContext,
    settings: Settings,
) -> tuple[RecommendationScoreBreakdown, list[AppliedPenalty], RecommendationFreshness]:
    freshness = get_data_freshness(candidate, settings)
    values = {
        "skin_type_match": score_skin_type(candidate, context),
        "visible_concern_match": score_visible_concerns(candidate, context),
        "ingredient_relevance": score_ingredient_relevance(candidate, context),
        "sensitivity_compatibility": score_sensitivity(candidate, context),
        "budget_fit": score_budget(candidate, context),
        "availability": score_availability(candidate),
        "brand_preference": score_brand(candidate, context),
        "data_quality": score_data_quality(candidate, freshness),
        "rating": score_rating(candidate),
    }
    weights = get_scoring_weights(settings)
    base_score = clamp(sum(values[key] * weights[key] for key in weights))
    penalties, total_penalty = calculate_penalties(candidate, context, settings)
    final_score = clamp(base_score - total_penalty)
    return (
        RecommendationScoreBreakdown(
            **values,
            base_score=base_score,
            caution_penalty=total_penalty,
            final_score=final_score,
        ),
        penalties,
        freshness,
    )
