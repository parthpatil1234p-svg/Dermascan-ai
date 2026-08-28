from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.skin_concern_fusion_service import (
    ConcernQuestionnaireEvidence,
    compare_questionnaire,
)
from app.services.skin_concern_interpretation_service import (
    interpret_concern,
    visible_severity,
)


def settings() -> Settings:
    return Settings(
        app_name="DermaScan AI",
        app_env="testing",
        api_prefix="/api",
        mongodb_url="mongodb://localhost:27017",
        mongodb_database="concern_interpretation_test",
        jwt_secret_key="concern-interpretation-test-secret-32-bytes",
        frontend_origin="http://localhost:5173",
        upload_directory=Path("storage/tests"),
    )


@pytest.mark.parametrize(
    ("score", "expected"),
    [(0.57, "mild"), (0.70, "moderate"), (0.90, "prominent")],
)
def test_visible_severity_bands(score: float, expected: str) -> None:
    assert visible_severity(score, 0.5, settings(), calibrated=True) == expected


def test_uncalibrated_threshold_never_claims_severity() -> None:
    assert visible_severity(0.95, 0.5, settings(), calibrated=False) == "uncertain"


def test_near_threshold_result_is_uncertain() -> None:
    result = interpret_concern(
        concern_code="visible_pores",
        score=0.51,
        threshold=0.5,
        comparison=compare_questionnaire(
            "visible_pores", ConcernQuestionnaireEvidence("Moderate", "Low", True)
        ),
        regions=["Full Face"],
        settings=settings(),
        thresholds_calibrated=True,
    )
    assert result.status == "uncertain"
    assert result.visible_severity == "uncertain"
    assert result.regions == []


@pytest.mark.parametrize(
    ("score", "expected"),
    [(0.80, "observed"), (0.20, "not_observed")],
)
def test_clear_threshold_statuses(score: float, expected: str) -> None:
    result = interpret_concern(
        concern_code="visible_pores",
        score=score,
        threshold=0.5,
        comparison=compare_questionnaire(
            "visible_pores", ConcernQuestionnaireEvidence("Moderate", "Low", None)
        ),
        regions=["Full Face"],
        settings=settings(),
        thresholds_calibrated=True,
    )
    assert result.status == expected


def test_questionnaire_support_can_only_make_borderline_result_possible() -> None:
    result = interpret_concern(
        concern_code="visible_oiliness",
        score=0.51,
        threshold=0.5,
        comparison=compare_questionnaire(
            "visible_oiliness", ConcernQuestionnaireEvidence("High", "Low", False)
        ),
        regions=["Full Face"],
        settings=settings(),
        thresholds_calibrated=True,
    )
    assert result.status == "possible"
    assert result.visible_severity == "uncertain"


def test_questionnaire_disagreement_is_preserved() -> None:
    comparison = compare_questionnaire(
        "dry_looking_areas", ConcernQuestionnaireEvidence("High", "Low", None)
    )
    assert comparison.agreement == "Mixed"


def test_redness_does_not_infer_sensitivity() -> None:
    comparison = compare_questionnaire(
        "visible_redness", ConcernQuestionnaireEvidence("Low", "Low", True)
    )
    assert comparison.agreement == "Not Compared"
    assert "not inferred" in comparison.explanation
