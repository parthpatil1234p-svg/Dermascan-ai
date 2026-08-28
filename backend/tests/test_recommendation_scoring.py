from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.services.recommendation_engine_service import score_candidate
from app.services.recommendation_scoring_service import (
    calculate_penalties,
    calculate_score_breakdown,
    score_availability,
    score_band,
    score_brand,
    score_budget,
    score_ingredient_relevance,
    score_rating,
    score_sensitivity,
    score_skin_type,
    score_visible_concerns,
)
from tests.recommendation_fixtures import caution, recommendation_candidate, recommendation_context


def test_default_weights_total_one():
    assert sum(get_settings().recommendation_weights.values()) == pytest.approx(1.0)


def test_invalid_weight_total_is_rejected():
    with pytest.raises(ValidationError, match="must total 1.0"):
        Settings(RECOMMENDATION_WEIGHT_SKIN_TYPE=0.20)


@pytest.mark.parametrize(
    ("mappings", "expected"),
    [
        (["combination"], 100),
        (["all_skin_types"], 85),
        (["oily"], 70),
        (["dry"], 20),
    ],
)
def test_skin_type_scores(mappings, expected):
    assert (
        score_skin_type(
            recommendation_candidate(suitable_skin_types=mappings), recommendation_context()
        )
        == expected
    )


@pytest.mark.parametrize(
    ("mappings", "expected"),
    [
        (["all_skin_types"], 90),
        (["oily", "normal"], 80),
        (["dry"], 50),
        ([], 25),
    ],
)
def test_uncertain_skin_type_scores(mappings, expected):
    context = recommendation_context(
        skin_type={"value": "uncertain", "status": "uncertain", "confidence": 0.45}
    )
    assert (
        score_skin_type(recommendation_candidate(suitable_skin_types=mappings), context) == expected
    )


def test_concern_score_weights_observed_and_possible():
    candidate = recommendation_candidate(target_visible_concerns=["visible_oiliness"])
    assert score_visible_concerns(candidate, recommendation_context()) == pytest.approx(66.6666667)


def test_basic_category_has_concern_baseline():
    candidate = recommendation_candidate(target_visible_concerns=[])
    assert score_visible_concerns(candidate, recommendation_context()) == 60


def test_non_basic_no_match_has_low_concern_score():
    candidate = recommendation_candidate(category="serum", target_visible_concerns=[])
    assert score_visible_concerns(candidate, recommendation_context()) == 25


def test_ingredient_relevance_uses_taxonomy_roles():
    assert score_ingredient_relevance(recommendation_candidate(), recommendation_context()) >= 90


def test_missing_ingredients_score_zero():
    candidate = recommendation_candidate(normalized_ingredients=[], ingredient_roles=[])
    assert score_ingredient_relevance(candidate, recommendation_context()) == 0


@pytest.mark.parametrize(
    ("reported", "suitability", "expected"),
    [
        (True, "potentially_suitable", 100),
        (True, "use_with_caution", 55),
        (True, "not_specified", 45),
        (True, "unknown", 30),
        (False, "potentially_suitable", 90),
        (False, "unknown", 55),
    ],
)
def test_sensitivity_scores(reported, suitability, expected):
    assert (
        score_sensitivity(
            recommendation_candidate(sensitivity_suitability=suitability),
            recommendation_context(self_reported_sensitivity=reported),
        )
        == expected
    )


@pytest.mark.parametrize(("amount", "expected"), [(300, 100), (700, 90), (900, 75), (1000, 65)])
def test_strict_budget_gradual_score(amount, expected):
    assert (
        score_budget(
            recommendation_candidate(price={"amount": amount, "currency": "INR"}),
            recommendation_context(),
        )
        == expected
    )


def test_flexible_budget_overage_scores():
    context = recommendation_context(
        budget={"minimum": 200, "maximum": 1000, "currency": "INR", "mandatory": False}
    )
    assert (
        score_budget(recommendation_candidate(price={"amount": 1050, "currency": "INR"}), context)
        == 50
    )
    assert (
        score_budget(recommendation_candidate(price={"amount": 1100, "currency": "INR"}), context)
        == 30
    )


def test_availability_scores_are_controlled():
    assert score_availability(recommendation_candidate(availability_status="available")) == 100
    assert score_availability(recommendation_candidate(availability_status="limited")) == 60
    assert score_availability(recommendation_candidate(availability_status="unknown")) == 25


def test_brand_preference_is_low_weight_component():
    preferred = recommendation_context(preferred_brands=["dermademo labs"])
    other = recommendation_context(preferred_brands=["another brand"])
    assert score_brand(recommendation_candidate(), preferred) == 100
    assert score_brand(recommendation_candidate(), other) == 50
    assert score_brand(recommendation_candidate(), recommendation_context()) == 70


def test_missing_rating_is_neutral():
    assert score_rating(recommendation_candidate(rating=None)) == 50


def test_rating_count_adjustment_is_conservative():
    few = score_rating(recommendation_candidate(rating={"value": 4.8, "count": 3}))
    many = score_rating(recommendation_candidate(rating={"value": 4.6, "count": 5000}))
    assert many > few


def test_caution_penalties_apply_once_and_are_capped():
    settings = get_settings()
    candidate = recommendation_candidate(
        eligibility_status="eligible_with_caution",
        cautions=[
            caution("EXFOLIATING_ACTIVE_CAUTION"),
            caution("RETINOID_CAUTION"),
            caution("FRAGRANCE_CONFLICT"),
        ],
    )
    penalties, total = calculate_penalties(candidate, recommendation_context(), settings)
    assert [item.code for item in penalties].count("ACTIVE_INGREDIENT_CAUTION") == 1
    assert total <= settings.recommendation_max_total_penalty


def test_component_and_final_scores_are_clamped():
    breakdown, _, _ = calculate_score_breakdown(
        recommendation_candidate(), recommendation_context(), get_settings()
    )
    assert all(0 <= value <= 100 for value in breakdown.model_dump().values())


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (95, "Excellent Match"),
        (85, "Strong Match"),
        (75, "Good Match"),
        (65, "Moderate Match"),
        (59.99, "Low Match"),
    ],
)
def test_score_bands(score, expected):
    assert score_band(score) == expected


def test_excluded_and_insufficient_candidates_are_not_valid_scoring_inputs():
    with pytest.raises(ValidationError):
        recommendation_candidate(eligibility_status="excluded")
    with pytest.raises(ValidationError):
        recommendation_candidate(eligibility_status="insufficient_information")


def test_scoring_is_deterministic_and_does_not_round_early():
    first = score_candidate(recommendation_candidate(), recommendation_context(), get_settings())
    second = score_candidate(recommendation_candidate(), recommendation_context(), get_settings())
    assert first.final_score == second.final_score
    assert first.base_score == second.base_score


def test_stale_data_reduces_data_quality_and_adds_penalty_when_reported():
    old = datetime.now(timezone.utc) - timedelta(days=120)
    candidate = recommendation_candidate(
        source_verified_at=old,
        price_checked_at=old,
        cautions=[caution("PRICE_DATA_STALE"), caution("SOURCE_DATA_STALE")],
        eligibility_status="eligible_with_caution",
    )
    scored = score_candidate(candidate, recommendation_context(), get_settings())
    assert scored.score_breakdown.data_quality < 100
    assert scored.total_penalty > 0
