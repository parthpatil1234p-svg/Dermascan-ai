PRODUCT_CATEGORIES = (
    "cleanser",
    "toner",
    "serum",
    "moisturizer",
    "sunscreen",
    "exfoliant",
    "spot_care",
    "under_eye_product",
    "face_mask",
    "night_cream",
    "lip_care",
)

CATEGORY_DISPLAY_NAMES = {value: value.replace("_", " ").title() for value in PRODUCT_CATEGORIES}

SKIN_TYPES = (
    "normal",
    "oily",
    "dry",
    "combination",
    "sensitive_self_reported",
    "all_skin_types",
)

VISIBLE_CONCERNS = (
    "visible_oiliness",
    "dry_looking_areas",
    "visible_pores",
    "visible_redness",
    "uneven_looking_tone",
    "dark_spots",
    "acne_like_spots",
    "under_eye_darkness",
    "dull_looking_appearance",
    "fine_line_visibility",
)

INGREDIENT_CATEGORIES = (
    "active",
    "humectant",
    "emollient",
    "occlusive",
    "surfactant",
    "antioxidant",
    "preservative",
    "fragrance",
    "essential_oil",
    "exfoliant",
    "uv_filter",
    "soothing_agent",
    "colourant",
    "solvent",
    "other",
)

CAUTION_FLAGS = (
    "contains_added_fragrance",
    "contains_essential_oils",
    "contains_drying_alcohol",
    "contains_common_contact_allergen",
    "contains_exfoliating_acid",
    "contains_retinoid",
    "contains_benzoyl_peroxide",
    "contains_uv_filters",
)

FRAGRANCE_STATUSES = (
    "fragrance_free",
    "contains_added_fragrance",
    "contains_fragrant_ingredients",
    "unknown",
)
ESSENTIAL_OIL_STATUSES = ("free", "contains", "unknown")
SENSITIVITY_SUITABILITY = (
    "potentially_suitable",
    "use_with_caution",
    "not_specified",
    "unknown",
)
AVAILABILITY_STATUSES = ("available", "limited", "unavailable", "unknown")
DATA_TYPES = ("verified_real", "verified_manual", "demo_synthetic", "unverified_draft")
PUBLIC_DATA_TYPES = ("verified_real", "verified_manual", "demo_synthetic")
AGE_GROUPS = (
    "Under 18",
    "18-25",
    "26-35",
    "36-45",
    "46-60",
    "Above 60",
    "All adults",
    "Not specified",
)
USAGE_TIMES = ("morning", "night", "morning_and_night", "as_needed", "not_specified")
SORT_OPTIONS = (
    "name_asc",
    "name_desc",
    "price_low_to_high",
    "price_high_to_low",
    "newest",
    "rating_high_to_low",
)
COUNTRY_CODE_PATTERN = r"^[A-Z]{2}$"
SUPPORTED_CURRENCIES = ("INR",)
