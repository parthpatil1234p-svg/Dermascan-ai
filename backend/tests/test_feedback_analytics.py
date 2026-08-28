from datetime import datetime, timezone

from bson import ObjectId

from app.services.feedback_analytics_service import build_feedback_analytics
from tests.feedback_fixtures import analysis_payload, auth, feedback_api_context, product_payload


def test_aggregate_analytics_use_only_consented_active_feedback_and_no_comments():
    documents = [
        {
            "user_id": ObjectId(),
            "feedback_status": "active",
            "moderation_status": "clear",
            "consent_for_analytics": True,
            "feedback_category": "report_feedback",
            "helpfulness_rating": 5,
            "selected_reasons": ["REPORT_IS_CLEAR"],
            "comment": "private text",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "user_id": ObjectId(),
            "feedback_status": "withdrawn",
            "moderation_status": "clear",
            "consent_for_analytics": True,
            "feedback_category": "report_feedback",
            "helpfulness_rating": 1,
            "selected_reasons": ["REPORT_TOO_TECHNICAL"],
            "comment": "withdrawn private text",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "user_id": ObjectId(),
            "feedback_status": "active",
            "moderation_status": "clear",
            "consent_for_analytics": False,
            "feedback_category": "report_feedback",
            "helpfulness_rating": 1,
            "selected_reasons": [],
            "created_at": datetime.now(timezone.utc),
        },
    ]
    result = build_feedback_analytics(documents, min_group_size=1)
    assert result["eligible_feedback_count"] == 1
    assert result["average_report_helpfulness"] == 5
    assert "comment" not in result and "user_id" not in result and "raw_comments" not in result


def test_minimum_group_threshold_suppresses_sparse_reason_counts():
    document = {
        "feedback_status": "active",
        "moderation_status": "clear",
        "consent_for_analytics": True,
        "selected_reasons": ["REPORT_IS_CLEAR"],
    }
    assert build_feedback_analytics([document], min_group_size=3)["most_common_reasons"] == []


def test_admin_analytics_is_protected_and_snapshot_is_aggregate():
    context = feedback_api_context()
    context["client"].post(
        "/api/feedback", json=analysis_payload(context), headers=auth(context["token"])
    )
    assert (
        context["client"]
        .get("/api/admin/feedback/analytics", headers=auth(context["token"]))
        .status_code
        == 403
    )
    response = context["client"].get(
        "/api/admin/feedback/analytics", headers=auth(context["admin_token"])
    )
    assert response.status_code == 200
    body = response.json()
    assert body["snapshot_id"].startswith("FAS-") and "comment" not in body


def test_withdrawn_feedback_is_excluded_from_admin_analytics():
    context = feedback_api_context()
    headers = auth(context["token"])
    created = (
        context["client"]
        .post(
            "/api/feedback",
            json=product_payload(context, consent_for_analytics=True),
            headers=headers,
        )
        .json()
    )
    context["client"].delete(f"/api/feedback/{created['feedback_id']}", headers=headers)
    analytics = (
        context["client"]
        .get("/api/admin/feedback/analytics", headers=auth(context["admin_token"]))
        .json()
    )
    assert analytics["eligible_feedback_count"] == 0
    assert analytics["withdrawal_rate_percent"] == 100


def test_admin_catalogue_review_requires_admin_and_does_not_mutate_catalogue():
    context = feedback_api_context()
    context["client"].post(
        "/api/feedback",
        json=product_payload(
            context, selected_reasons=["PRODUCT_PRICE_CHANGED"], price_feedback="price_changed"
        ),
        headers=auth(context["token"]),
    )
    assert (
        context["client"]
        .get("/api/admin/catalogue-review-signals", headers=auth(context["token"]))
        .status_code
        == 403
    )
    response = context["client"].get(
        "/api/admin/catalogue-review-signals", headers=auth(context["admin_token"])
    )
    assert (
        response.status_code == 200 and response.json()["signals"][0]["review_status"] == "pending"
    )


def test_admin_moderation_action_is_audited():
    context = feedback_api_context()
    created = (
        context["client"]
        .post("/api/feedback", json=analysis_payload(context), headers=auth(context["token"]))
        .json()
    )
    response = context["client"].patch(
        f"/api/admin/feedback/{created['feedback_id']}/moderate",
        json={
            "moderation_status": "reviewed",
            "feedback_status": "active",
            "moderation_note": "Reviewed for project analytics.",
        },
        headers=auth(context["admin_token"]),
    )
    assert response.status_code == 200
    assert context["collections"]["audit"].documents[0]["feedback_id"] == created["feedback_id"]
