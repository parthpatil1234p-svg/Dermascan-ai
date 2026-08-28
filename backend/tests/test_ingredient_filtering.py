from app.services.ingredient_filter_service import (
    evaluate_avoided_ingredients,
    normalize_avoidances,
)
from tests.eligibility_fixtures import avoided, ingredient_lookup, real_product


def test_normalize_exact_avoided_ingredient():
    result = normalize_avoidances([" Vitamin B3 "], ingredient_lookup())
    assert result[0].normalized == "niacinamide"
    assert result[0].match_type == "ingredient"


def test_normalize_avoided_ingredient_category():
    result = normalize_avoidances(["Essential oils"], ingredient_lookup())
    assert result[0].normalized == "essential_oil"
    assert result[0].match_type == "category"


def test_exact_avoided_ingredient_excludes_product():
    exclusions, _ = evaluate_avoided_ingredients(
        real_product(normalized_ingredients=["niacinamide"]),
        [avoided()],
        ingredient_lookup(),
    )
    assert exclusions[0].code == "USER_AVOIDED_INGREDIENT_MATCH"
    assert exclusions[0].matched_value == "Niacinamide"


def test_category_avoidance_reports_exact_product_ingredient():
    category = avoided("Essential oils", "essential_oil", "category")
    exclusions, _ = evaluate_avoided_ingredients(
        real_product(normalized_ingredients=["lavender oil"]), [category], ingredient_lookup()
    )
    assert exclusions[0].matched_value == "Lavender Oil"


def test_category_matching_uses_taxonomy_not_name_guess():
    category = avoided("Essential oils", "essential_oil", "category")
    exclusions, _ = evaluate_avoided_ingredients(
        real_product(normalized_ingredients=["mystery essential oil name"]),
        [category],
        ingredient_lookup(),
    )
    assert exclusions == []


def test_unmapped_avoidance_adds_caution_not_allergy():
    values = normalize_avoidances(["Unknown botanical"], ingredient_lookup())
    exclusions, cautions = evaluate_avoided_ingredients(real_product(), values, ingredient_lookup())
    assert exclusions == []
    assert cautions[0].code == "INGREDIENT_DATA_INCOMPLETE"


def test_duplicate_avoidance_entries_removed_case_insensitively():
    result = normalize_avoidances(["Niacinamide", " niacinamide "], ingredient_lookup())
    assert len(result) == 1
