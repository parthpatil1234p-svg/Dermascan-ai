import pytest

from app.services.feedback_privacy_service import (
    FeedbackTextError,
    analytics_safe_snapshot,
    sanitize_feedback_text,
)
from tests.feedback_fixtures import analysis_payload, auth, feedback_api_context


def test_sanitizer_preserves_punctuation_and_escapes_html():
    value = sanitize_feedback_text("Useful, clear & practical! <b>Thanks</b>", 1000)
    assert value == "Useful, clear &amp; practical! &lt;b&gt;Thanks&lt;/b&gt;"


def test_sanitizer_removes_control_characters_and_rejects_oversize():
    assert sanitize_feedback_text("Helpful\x00 response", 1000) == "Helpful response"
    with pytest.raises(FeedbackTextError):
        sanitize_feedback_text("x" * 1001, 1000)


def test_analytics_privacy_filter_excludes_identifiers_and_raw_comments():
    result = analytics_safe_snapshot(
        {
            "email": "private@example.com",
            "full_name": "Private User",
            "user_id": "private",
            "comment": "private",
            "allergies": ["private"],
            "eligible_feedback_count": 2,
        }
    )
    assert result == {"eligible_feedback_count": 2}


def test_feedback_consents_default_false_and_are_withdrawn():
    context = feedback_api_context()
    headers = auth(context["token"])
    payload = analysis_payload(context)
    payload.pop("consent_for_analytics")
    created = context["client"].post("/api/feedback", json=payload, headers=headers).json()
    assert created["consent_for_analytics"] is False
    assert created["consent_for_research_review"] is False
    context["client"].delete(f"/api/feedback/{created['feedback_id']}", headers=headers)
    stored = context["collections"]["feedback"].documents[0]
    assert (
        stored["consent_for_analytics"] is False and stored["consent_for_research_review"] is False
    )


def test_feedback_options_are_controlled_and_authenticated():
    context = feedback_api_context()
    assert context["client"].get("/api/feedback/options").status_code == 401
    response = context["client"].get("/api/feedback/options", headers=auth(context["token"]))
    assert response.status_code == 200
    assert len(response.json()["categories"]) == 8
    assert response.json()["ratings"][0] == {"value": 1, "label": "Very Poor"}


def test_safe_errors_do_not_expose_internal_details():
    context = feedback_api_context()
    response = context["client"].get("/api/feedback/FDB-MISSING", headers=auth(context["token"]))
    assert response.status_code == 404
    text = response.text.lower()
    assert "objectid" not in text and "mongodb" not in text and "traceback" not in text
