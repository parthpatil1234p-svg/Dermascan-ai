import pytest
from bson import ObjectId

from app.api.dependencies import (
    get_image_uploads_collection,
    get_ingredients_collection,
    get_product_eligibility_reports_collection,
    get_products_collection,
    get_skin_concern_reports_collection,
    get_skin_profiles_collection,
    get_skin_type_reports_collection,
)
from app.core.config import get_settings
from app.services.product_eligibility_service import evaluate_owned_catalogue
from tests.catalogue_fakes import FakeCollection
from tests.feedback_fixtures import auth, feedback_api_context, product_payload
from tests.test_product_eligibility import api_context as eligibility_api_context


def experience_payload(context, **overrides):
    payload = product_payload(
        context,
        feedback_category="product_experience_feedback",
        product_experience_status="used_short_term",
        irritation_reported="visible_irritation",
        irritation_description="I noticed discomfort and stopped using it.",
        exclude_product_from_future_recommendations=True,
        selected_reasons=["PRODUCT_CAUSED_VISIBLE_IRRITATION"],
    )
    payload.update(overrides)
    return payload


def test_product_experience_requires_actual_use_and_irritation_response():
    context = feedback_api_context()
    headers = auth(context["token"])
    response = context["client"].post(
        "/api/feedback",
        json=experience_payload(context, product_experience_status="not_used"),
        headers=headers,
    )
    assert response.status_code == 422


def test_irritation_creates_private_product_avoidance_and_improvement_signal():
    context = feedback_api_context()
    response = context["client"].post(
        "/api/feedback", json=experience_payload(context), headers=auth(context["token"])
    )
    assert response.status_code == 201
    avoidance = context["collections"]["avoidances"].documents[0]
    assert avoidance["product_id"] == "PRD-TEST001"
    assert avoidance["user_id"] == context["owner"] and avoidance["is_active"] is True
    assert avoidance["avoidance_reason"] == "USER_REPORTED_PRODUCT_AVOIDANCE"
    signals = context["collections"]["improvement_signals"].documents
    assert any(item["signal_type"] == "USER_REPORTS_PRODUCT_AVOIDANCE" for item in signals)


def test_avoidance_is_not_global_and_can_be_removed():
    context = feedback_api_context()
    headers = auth(context["token"])
    context["client"].post("/api/feedback", json=experience_payload(context), headers=headers)
    avoidance = context["collections"]["avoidances"].documents[0]
    assert avoidance["user_id"] != ObjectId()
    listed = context["client"].get("/api/feedback/product-avoidance", headers=headers)
    assert listed.status_code == 200 and len(listed.json()["avoidances"]) == 1
    removed = context["client"].delete(
        "/api/feedback/product-avoidance/PRD-TEST001", headers=headers
    )
    assert removed.status_code == 200
    assert context["collections"]["avoidances"].documents[0]["is_active"] is False


def test_withdrawal_deactivates_avoidance_and_improvement_signals():
    context = feedback_api_context()
    headers = auth(context["token"])
    created = (
        context["client"]
        .post("/api/feedback", json=experience_payload(context), headers=headers)
        .json()
    )
    context["client"].delete(f"/api/feedback/{created['feedback_id']}", headers=headers)
    assert context["collections"]["avoidances"].documents[0]["is_active"] is False
    assert all(
        not item["is_active"] for item in context["collections"]["improvement_signals"].documents
    )


def test_price_and_availability_feedback_create_catalogue_review_signals_only():
    context = feedback_api_context()
    payload = experience_payload(
        context,
        irritation_reported="no_issue",
        exclude_product_from_future_recommendations=False,
        selected_reasons=["PRODUCT_PRICE_CHANGED", "PRODUCT_UNAVAILABLE"],
        price_feedback="price_changed",
        availability_feedback="unavailable",
    )
    before = context["collections"]["final_reports"].documents[0].copy()
    response = context["client"].post("/api/feedback", json=payload, headers=auth(context["token"]))
    assert response.status_code == 201
    signals = context["collections"]["catalogue_signals"].documents
    assert {item["signal_type"] for item in signals} == {"price_changed", "product_unavailable"}
    assert context["collections"]["final_reports"].documents[0] == before


def test_skin_type_disagreement_is_signal_not_historical_overwrite():
    context = feedback_api_context()
    report_before = context["collections"]["final_reports"].documents[0].copy()
    payload = {
        "final_report_id": context["final_report_id"],
        "feedback_category": "skin_type_feedback",
        "accuracy_perception": "does_not_match",
        "selected_reasons": ["SKIN_TYPE_DOES_NOT_MATCH_EXPERIENCE"],
        "comment": "My usual experience is different.",
    }
    response = context["client"].post("/api/feedback", json=payload, headers=auth(context["token"]))
    assert response.status_code == 201
    assert context["collections"]["final_reports"].documents[0] == report_before
    assert (
        context["collections"]["improvement_signals"].documents[0]["signal_type"]
        == "USER_SKIN_TYPE_RESULT_DISAGREEMENT"
    )


def test_routine_complexity_creates_controlled_signal():
    context = feedback_api_context()
    payload = {
        "routine_report_id": context["routine_report_id"],
        "feedback_category": "routine_feedback",
        "routine_practicality": 2,
        "routine_difficulty": "too_complex",
        "selected_reasons": ["ROUTINE_TOO_COMPLEX"],
    }
    context["client"].post("/api/feedback", json=payload, headers=auth(context["token"]))
    assert (
        context["collections"]["improvement_signals"].documents[0]["signal_type"]
        == "USER_PREFERS_SIMPLER_ROUTINE"
    )


@pytest.mark.asyncio
async def test_active_user_avoidance_is_a_hard_future_eligibility_exclusion():
    _, collections, user_id, upload_id, _ = eligibility_api_context()
    avoidances = FakeCollection(
        [
            {
                "user_id": ObjectId(user_id),
                "product_id": "PRD-API001",
                "is_active": True,
            }
        ]
    )
    report = await evaluate_owned_catalogue(
        upload_id=upload_id,
        user_id=user_id,
        uploads=collections[get_image_uploads_collection],
        profiles=collections[get_skin_profiles_collection],
        skin_types=collections[get_skin_type_reports_collection],
        concerns=collections[get_skin_concern_reports_collection],
        products=collections[get_products_collection],
        ingredients=collections[get_ingredients_collection],
        reports=collections[get_product_eligibility_reports_collection],
        settings=get_settings(),
        user_avoidances=avoidances,
    )
    result = next(item for item in report["product_results"] if item["product_id"] == "PRD-API001")
    assert result["eligibility_status"] == "excluded"
    assert result["hard_exclusions"][0]["code"] == "USER_REPORTED_PRODUCT_AVOIDANCE"
