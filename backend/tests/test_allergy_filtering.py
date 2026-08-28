import pytest

from app.services.allergy_filter_service import evaluate_allergies, normalize_allergies
from tests.eligibility_fixtures import ingredient_lookup, mapped_allergy, real_product


@pytest.mark.parametrize("value", ["Fragrance", " perfume ", "Parfum", "Added fragrance"])
def test_normalize_fragrance_aliases(value):
    result = normalize_allergies([value], ingredient_lookup())
    assert result[0].normalized == "added_fragrance"
    assert result[0].mapping_status == "mapped"
    assert result[0].original == value.strip()


def test_normalize_ingredient_alias_to_canonical_name():
    result = normalize_allergies(["Vitamin B3"], ingredient_lookup())
    assert result[0].normalized == "niacinamide"


def test_preserve_unmapped_allergy():
    result = normalize_allergies(["Mystery resin"], ingredient_lookup())
    assert result[0].original == "Mystery resin"
    assert result[0].mapping_status == "unmapped"


def test_known_fragrance_allergy_excludes_matching_product():
    product = real_product(fragrance_status="contains_added_fragrance")
    exclusions, cautions = evaluate_allergies(product, [mapped_allergy()], ingredient_lookup())
    assert exclusions[0].code == "KNOWN_ALLERGY_MATCH"
    assert cautions == []


def test_exact_ingredient_allergy_match():
    product = real_product(normalized_ingredients=["niacinamide"])
    allergy = mapped_allergy("Vitamin B3", "niacinamide")
    exclusions, _ = evaluate_allergies(product, [allergy], ingredient_lookup())
    assert exclusions[0].matched_value == "Vitamin B3"


def test_avoid_unsafe_substring_allergy_match():
    product = real_product(normalized_ingredients=["niacinamide"])
    allergy = normalize_allergies(["Niacin"], ingredient_lookup())
    exclusions, cautions = evaluate_allergies(product, allergy, ingredient_lookup())
    assert exclusions == []
    assert cautions[0].code == "POTENTIAL_ALLERGEN_PRESENT"


def test_unmapped_allergy_with_no_direct_match_adds_caution():
    allergies = normalize_allergies(["Unknown botanical"], ingredient_lookup())
    exclusions, cautions = evaluate_allergies(real_product(), allergies, ingredient_lookup())
    assert exclusions == []
    assert cautions[0].code == "POTENTIAL_ALLERGEN_PRESENT"
