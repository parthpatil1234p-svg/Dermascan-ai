CATEGORY_ALIASES = {
    "essential oil": "essential_oil",
    "essential oils": "essential_oil",
    "fragrance": "fragrance",
    "fragrances": "fragrance",
    "uv filter": "uv_filter",
    "uv filters": "uv_filter",
    "exfoliating acid": "exfoliant",
    "exfoliating acids": "exfoliant",
}

ACTIVE_CAUTION_FLAGS = {
    "contains_drying_alcohol": (
        "DRYING_ALCOHOL_CAUTION",
        "This product contains a drying-alcohol flag. Review the current label and your individual tolerance.",
    ),
    "contains_exfoliating_acid": (
        "EXFOLIATING_ACTIVE_CAUTION",
        "This product contains an exfoliating active. Introduce new products cautiously and review the current label.",
    ),
    "contains_retinoid": (
        "RETINOID_CAUTION",
        "This product contains a retinoid flag and needs additional care for a sensitivity-aware routine.",
    ),
    "contains_benzoyl_peroxide": (
        "BENZOYL_PEROXIDE_CAUTION",
        "This product contains a benzoyl-peroxide flag and needs additional care for a sensitivity-aware routine.",
    ),
}
