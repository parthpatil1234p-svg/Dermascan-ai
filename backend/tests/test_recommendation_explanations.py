from app.core.config import get_settings
from app.services.recommendation_engine_service import score_candidate
from app.services.recommendation_explanation_service import explanation_uses_candidate_evidence
from tests.recommendation_fixtures import caution, recommendation_candidate, recommendation_context


def test_explanation_uses_real_candidate_evidence():
    candidate = recommendation_candidate()
    scored = score_candidate(candidate, recommendation_context(), get_settings())
    assert explanation_uses_candidate_evidence(scored.why_recommended, candidate)
    assert "Niacinamide" in " ".join(scored.positive_factors)


def test_explanation_contains_actual_concern_matches():
    scored = score_candidate(recommendation_candidate(), recommendation_context(), get_settings())
    text = " ".join(scored.positive_factors).lower()
    assert "visible oiliness" in text and "visible pores" in text


def test_caution_explanation_uses_eligibility_message():
    message = "Sensitivity suitability was not established in the catalogue."
    candidate = recommendation_candidate(
        eligibility_status="eligible_with_caution",
        cautions=[caution("SENSITIVITY_NOT_SPECIFIED", message)],
    )
    scored = score_candidate(candidate, recommendation_context(), get_settings())
    assert message in scored.caution_factors


def test_explanations_do_not_make_medical_guarantees():
    scored = score_candidate(recommendation_candidate(), recommendation_context(), get_settings())
    text = (scored.why_recommended + " " + " ".join(scored.positive_factors)).lower()
    banned = [
        "guaranteed",
        "perfect product",
        "best product",
        "dermatologist-approved",
        "cure",
        "treats acne",
    ]
    assert not any(term in text for term in banned)


def test_low_match_wording_remains_catalogue_specific():
    candidate = recommendation_candidate(
        category="serum",
        suitable_skin_types=["dry"],
        target_visible_concerns=[],
        normalized_ingredients=["water"],
        highlighted_ingredients=[],
        ingredient_roles=["formula base"],
        availability_status="limited",
    )
    scored = score_candidate(candidate, recommendation_context(), get_settings())
    assert "catalogue match" in scored.why_recommended.lower()
