from app.core.config import Settings

ACTIVE_CAUTION_CODES = {
    "DRYING_ALCOHOL_CAUTION",
    "EXFOLIATING_ACTIVE_CAUTION",
    "RETINOID_CAUTION",
    "BENZOYL_PEROXIDE_CAUTION",
}


def get_penalty_configuration(settings: Settings) -> dict[str, float]:
    return {
        "eligible_with_caution": settings.penalty_eligible_with_caution,
        "sensitivity_not_specified": settings.penalty_sensitivity_not_specified,
        "active_ingredient_caution": settings.penalty_active_ingredient_caution,
        "fragrance_preference_conflict": settings.penalty_fragrance_preference_conflict,
        "price_stale": settings.penalty_price_stale,
        "availability_stale": settings.penalty_availability_stale,
        "limited_availability": settings.penalty_limited_availability,
        "significant_data_gap": settings.penalty_significant_data_gap,
        "uncertain_skin_type": settings.penalty_uncertain_skin_type,
        "maximum_total": settings.recommendation_max_total_penalty,
    }
