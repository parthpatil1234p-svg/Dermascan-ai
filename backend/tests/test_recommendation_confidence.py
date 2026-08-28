from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.services.recommendation_confidence_service import calculate_overall_confidence
from app.services.recommendation_engine_service import score_candidate
from tests.recommendation_fixtures import caution, recommendation_candidate, recommendation_context


def test_complete_fresh_candidate_has_high_confidence():
    scored = score_candidate(
        recommendation_candidate(), recommendation_context(), get_settings(), score_gap=10
    )
    assert scored.recommendation_confidence == "high"


def test_uncertainty_cautions_and_stale_data_lower_confidence():
    old = datetime.now(timezone.utc) - timedelta(days=180)
    context = recommendation_context(
        skin_type={"value": "uncertain", "status": "uncertain", "confidence": 0.3},
        concerns={"visible_oiliness": "uncertain"},
    )
    candidate = recommendation_candidate(
        is_demo_product=True,
        data_type="demo_synthetic",
        price_checked_at=old,
        availability_checked_at=old,
        source_verified_at=old,
        eligibility_status="eligible_with_caution",
        cautions=[
            caution("SENSITIVITY_NOT_SPECIFIED"),
            caution("PRICE_DATA_STALE"),
            caution("AVAILABILITY_DATA_STALE"),
            caution("SOURCE_DATA_STALE"),
        ],
    )
    scored = score_candidate(candidate, context, get_settings())
    assert scored.recommendation_confidence == "low"
    assert any("uncertain" in reason.lower() for reason in scored.confidence_reasons)


def test_score_separation_contributes_confidence_reason():
    scored = score_candidate(
        recommendation_candidate(), recommendation_context(), get_settings(), score_gap=8
    )
    assert any("separated" in reason.lower() for reason in scored.confidence_reasons)


def test_no_recommendations_returns_low_overall_confidence():
    confidence, reasons = calculate_overall_confidence([], recommendation_context())
    assert confidence == "low"
    assert "No candidate" in reasons[0]


def test_overall_confidence_reports_uncertain_skin_type():
    context = recommendation_context(
        skin_type={"value": "uncertain", "status": "uncertain", "confidence": 0.4}
    )
    scored = score_candidate(recommendation_candidate(), context, get_settings())
    confidence, reasons = calculate_overall_confidence([scored], context)
    assert confidence in {"moderate", "low"}
    assert any("uncertainty" in reason.lower() for reason in reasons)
