from datetime import datetime, timezone

from app.schemas.product_eligibility import (
    FilteringBudget,
    FilteringSkinType,
    NormalizedAllergy,
    NormalizedAvoidance,
    UserFilteringContext,
)
from tests.catalogue_fakes import demo_product


def ingredient_lookup():
    return {
        "fragrance": {
            "ingredient_id": "ING-FRAG",
            "canonical_name": "Fragrance",
            "normalized_name": "fragrance",
            "ingredient_category": "fragrance",
        },
        "parfum": {
            "ingredient_id": "ING-FRAG",
            "canonical_name": "Fragrance",
            "normalized_name": "fragrance",
            "ingredient_category": "fragrance",
        },
        "niacinamide": {
            "ingredient_id": "ING-NIAC",
            "canonical_name": "Niacinamide",
            "normalized_name": "niacinamide",
            "ingredient_category": "active",
        },
        "vitamin b3": {
            "ingredient_id": "ING-NIAC",
            "canonical_name": "Niacinamide",
            "normalized_name": "niacinamide",
            "ingredient_category": "active",
        },
        "lavender oil": {
            "ingredient_id": "ING-LAV",
            "canonical_name": "Lavender Oil",
            "normalized_name": "lavender oil",
            "ingredient_category": "essential_oil",
        },
        "glycerin": {
            "ingredient_id": "ING-GLYC",
            "canonical_name": "Glycerin",
            "normalized_name": "glycerin",
            "ingredient_category": "humectant",
        },
    }


def filtering_context(**overrides):
    values = {
        "user_id": "507f1f77bcf86cd799439011",
        "age_group": "18-25",
        "country": "IN",
        "skin_type": FilteringSkinType(value="combination", status="estimated", confidence=0.84),
        "visible_concerns": ["visible_oiliness", "visible_pores"],
        "self_reported_sensitivity": False,
        "known_allergies": [],
        "ingredients_to_avoid": [],
        "fragrance_preference": "no_preference",
        "budget": FilteringBudget(minimum=None, maximum=None, mandatory=False),
        "preferred_brands": [],
    }
    values.update(overrides)
    return UserFilteringContext(**values)


def real_product(**overrides):
    now = datetime.now(timezone.utc)
    values = {
        "data_type": "verified_manual",
        "is_demo_product": False,
        "source_verified_at": now,
        "price_checked_at": now,
        "availability_checked_at": now,
    }
    values.update(overrides)
    return demo_product(**values)


def mapped_allergy(original="Perfume", normalized="added_fragrance"):
    return NormalizedAllergy(original=original, normalized=normalized, mapping_status="mapped")


def avoided(original="Niacinamide", normalized="niacinamide", match_type="ingredient"):
    return NormalizedAvoidance(original=original, normalized=normalized, match_type=match_type)
