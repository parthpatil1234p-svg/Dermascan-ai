from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_image_uploads_collection,
    get_ingredients_collection,
    get_product_eligibility_reports_collection,
    get_products_collection,
    get_skin_concern_reports_collection,
    get_skin_profiles_collection,
    get_skin_type_reports_collection,
    get_users_collection,
)
from app.core.config import get_settings
from app.core.security import create_access_token
from app.main import create_app
from app.models.product_eligibility import FILTER_ENGINE_VERSION
from app.schemas.product_eligibility import FilteringSkinType
from app.services.product_eligibility_service import (
    evaluate_product,
)
from tests.catalogue_fakes import FakeCollection
from tests.eligibility_fixtures import (
    filtering_context,
    ingredient_lookup,
    mapped_allergy,
    real_product,
)


def codes(reasons):
    return {reason.code for reason in reasons}


def test_product_with_complete_compatible_data_is_eligible():
    result = evaluate_product(
        real_product(), filtering_context(), ingredient_lookup(), get_settings()
    )
    assert result.eligibility_status == "eligible"
    assert {"SKIN_TYPE_MATCH", "VISIBLE_CONCERN_MATCH"} <= codes(result.positive_matches)


def test_inactive_product_is_excluded():
    result = evaluate_product(
        real_product(is_active=False), filtering_context(), ingredient_lookup(), get_settings()
    )
    assert result.eligibility_status == "excluded"
    assert "PRODUCT_INACTIVE" in codes(result.hard_exclusions)


def test_unverified_draft_is_excluded():
    product = real_product(data_type="unverified_draft")
    result = evaluate_product(product, filtering_context(), ingredient_lookup(), get_settings())
    assert result.eligibility_status == "excluded"
    assert "PRODUCT_UNVERIFIED" in codes(result.hard_exclusions)


def test_demo_product_keeps_visible_caution_label():
    product = real_product(data_type="demo_synthetic", is_demo_product=True)
    result = evaluate_product(product, filtering_context(), ingredient_lookup(), get_settings())
    assert result.eligibility_status == "eligible_with_caution"
    assert "DEMO_PRODUCT" in codes(result.cautions)


def test_missing_ingredients_with_allergy_is_insufficient_information():
    context = filtering_context(known_allergies=[mapped_allergy()])
    product = real_product(ingredients=[], normalized_ingredients=[])
    result = evaluate_product(product, context, ingredient_lookup(), get_settings())
    assert result.eligibility_status == "insufficient_information"
    assert "INGREDIENT_LIST_MISSING" in codes(result.information_gaps)


def test_fragrance_free_only_is_hard_exclusion():
    context = filtering_context(fragrance_preference="fragrance_free_only")
    product = real_product(fragrance_status="contains_added_fragrance")
    result = evaluate_product(product, context, ingredient_lookup(), get_settings())
    assert result.eligibility_status == "excluded"
    assert "FRAGRANCE_CONFLICT" in codes(result.hard_exclusions)


def test_fragrance_preference_is_caution():
    context = filtering_context(fragrance_preference="prefer_fragrance_free")
    product = real_product(fragrance_status="contains_added_fragrance")
    result = evaluate_product(product, context, ingredient_lookup(), get_settings())
    assert result.eligibility_status == "eligible_with_caution"
    assert "FRAGRANCE_CONFLICT" in codes(result.cautions)


def test_sensitive_user_active_flag_adds_caution_not_automatic_exclusion():
    context = filtering_context(self_reported_sensitivity=True)
    product = real_product(potential_irritant_flags=["contains_exfoliating_acid"])
    result = evaluate_product(product, context, ingredient_lookup(), get_settings())
    assert result.eligibility_status == "eligible_with_caution"
    assert "EXFOLIATING_ACTIVE_CAUTION" in codes(result.cautions)


def test_uncertain_skin_type_never_hard_filters():
    context = filtering_context(
        skin_type=FilteringSkinType(value="uncertain", status="uncertain", confidence=0.42)
    )
    result = evaluate_product(
        real_product(suitable_skin_types=["dry"]), context, ingredient_lookup(), get_settings()
    )
    assert result.eligibility_status == "eligible_with_caution"
    assert "SKIN_TYPE_PARTIAL_MATCH" in codes(result.cautions)


def test_no_concern_match_is_only_caution_for_active_category():
    product = real_product(category="serum", target_visible_concerns=["dark_spots"])
    result = evaluate_product(product, filtering_context(), ingredient_lookup(), get_settings())
    assert "NO_VISIBLE_CONCERN_MATCH" in codes(result.cautions)


def test_under_18_retinoid_rule_excludes():
    context = filtering_context(age_group="Under 18")
    product = real_product(potential_irritant_flags=["contains_retinoid"])
    result = evaluate_product(product, context, ingredient_lookup(), get_settings())
    assert "AGE_GROUP_RESTRICTION" in codes(result.hard_exclusions)


def test_contradictory_demo_flags_are_insufficient():
    product = real_product(data_type="demo_synthetic", is_demo_product=False)
    result = evaluate_product(product, filtering_context(), ingredient_lookup(), get_settings())
    assert result.eligibility_status == "insufficient_information"
    assert "PRODUCT_DATA_CONTRADICTION" in codes(result.information_gaps)


def test_multiple_hard_exclusions_are_collected_and_never_overridden():
    context = filtering_context(
        known_allergies=[mapped_allergy()],
        fragrance_preference="fragrance_free_only",
    )
    product = real_product(fragrance_status="contains_added_fragrance", country_codes=["GB"])
    result = evaluate_product(product, context, ingredient_lookup(), get_settings())
    assert result.eligibility_status == "excluded"
    assert {"KNOWN_ALLERGY_MATCH", "FRAGRANCE_CONFLICT", "UNAVAILABLE_IN_USER_COUNTRY"} <= codes(
        result.hard_exclusions
    )
    assert result.positive_matches


def api_context():
    now = datetime.now(timezone.utc)
    user_id = ObjectId()
    upload_id = "upload-step11"
    users = FakeCollection(
        [
            {
                "_id": user_id,
                "full_name": "Eligibility User",
                "email": "eligibility@example.com",
                "password_hash": "unused",
                "is_active": True,
                "is_admin": False,
                "created_at": now,
                "updated_at": now,
            }
        ]
    )
    profile_id = ObjectId()
    profiles = FakeCollection(
        [
            {
                "_id": profile_id,
                "user_id": user_id,
                "is_complete": True,
                "age_group": "18-25",
                "country": "India",
                "is_sensitive": True,
                "known_allergies": [],
                "ingredients_to_avoid": [],
                "fragrance_preference": "No preference",
                "budget_min": 200,
                "budget_max": 1000,
                "preferred_brands": [],
            }
        ]
    )
    uploads = FakeCollection(
        [
            {
                "_id": ObjectId(),
                "upload_id": upload_id,
                "user_id": user_id,
                "status": "skin_concern_analysis_completed",
                "image_format": "JPEG",
                "file_size_bytes": 240000,
                "width": 1080,
                "height": 1080,
                "expires_at": now + timedelta(minutes=30),
                "created_at": now,
                "updated_at": now,
            }
        ]
    )
    skin_types = FakeCollection(
        [
            {
                "_id": ObjectId(),
                "skin_type_report_id": "skin-type-report",
                "upload_id": upload_id,
                "user_id": user_id,
                "result_status": "estimated",
                "final_skin_type": "Combination",
                "model_confidence": 0.84,
            }
        ]
    )
    concerns = FakeCollection(
        [
            {
                "_id": ObjectId(),
                "skin_concern_report_id": "concern-report",
                "upload_id": upload_id,
                "user_id": user_id,
                "overall_status": "completed",
                "concern_results": [{"concern_code": "visible_oiliness", "status": "observed"}],
            }
        ]
    )
    products = FakeCollection(
        [
            real_product(
                product_id="PRD-API001", slug="api-one", price={"amount": 499, "currency": "INR"}
            ),
            real_product(
                product_id="PRD-API002",
                slug="api-two",
                product_name="Second Product",
                price={"amount": 1500, "currency": "INR"},
            ),
        ]
    )
    ingredient_docs = []
    seen = set()
    for document in ingredient_lookup().values():
        if document["ingredient_id"] not in seen:
            seen.add(document["ingredient_id"])
            ingredient_docs.append({**document, "normalized_aliases": [], "is_active": True})
    ingredients = FakeCollection(ingredient_docs)
    reports = FakeCollection()
    app = create_app(enable_lifespan=False)
    mapping = {
        get_users_collection: users,
        get_skin_profiles_collection: profiles,
        get_image_uploads_collection: uploads,
        get_skin_type_reports_collection: skin_types,
        get_skin_concern_reports_collection: concerns,
        get_products_collection: products,
        get_ingredients_collection: ingredients,
        get_product_eligibility_reports_collection: reports,
    }

    def collection_override(collection):
        def provide_collection():
            return collection

        return provide_collection

    for dependency, collection in mapping.items():
        app.dependency_overrides[dependency] = collection_override(collection)
    return (
        TestClient(app),
        mapping,
        str(user_id),
        upload_id,
        create_access_token(subject=str(user_id)),
    )


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_successful_evaluation_stores_report_updates_workflow_and_returns_summary():
    client, collections, _, upload_id, token = api_context()
    response = client.post(f"/api/product-eligibility/{upload_id}/evaluate", headers=auth(token))
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_evaluated"] == 2
    assert len(collections[get_product_eligibility_reports_collection].documents) == 1
    assert (
        collections[get_image_uploads_collection].documents[0]["status"]
        == "recommendation_scoring_pending"
    )
    stored = collections[get_product_eligibility_reports_collection].documents[0]
    assert stored["filter_engine_version"] == FILTER_ENGINE_VERSION
    upload_response = client.get(f"/api/uploads/{upload_id}", headers=auth(token))
    assert upload_response.status_code == 200
    assert upload_response.json()["status"] == "recommendation_scoring_pending"


def test_evaluation_requires_authentication():
    client, _, _, upload_id, _ = api_context()
    assert client.post(f"/api/product-eligibility/{upload_id}/evaluate").status_code == 401


def test_other_user_cannot_evaluate_owned_upload():
    client, collections, _, upload_id, _ = api_context()
    other_id = ObjectId()
    collections[get_users_collection].documents.append(
        {
            "_id": other_id,
            "full_name": "Other",
            "email": "other@example.com",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
    )
    response = client.post(
        f"/api/product-eligibility/{upload_id}/evaluate",
        headers=auth(create_access_token(subject=str(other_id))),
    )
    assert response.status_code == 404


def test_missing_profile_skin_type_and_concern_are_rejected():
    for dependency in (
        get_skin_profiles_collection,
        get_skin_type_reports_collection,
        get_skin_concern_reports_collection,
    ):
        client, collections, _, upload_id, token = api_context()
        collections[dependency].documents.clear()
        response = client.post(
            f"/api/product-eligibility/{upload_id}/evaluate", headers=auth(token)
        )
        assert response.status_code == 409


def test_existing_report_is_updated_not_duplicated():
    client, collections, _, upload_id, token = api_context()
    assert (
        client.post(
            f"/api/product-eligibility/{upload_id}/evaluate", headers=auth(token)
        ).status_code
        == 200
    )
    collections[get_image_uploads_collection].documents[0][
        "status"
    ] = "product_eligibility_completed"
    assert (
        client.post(
            f"/api/product-eligibility/{upload_id}/evaluate", headers=auth(token)
        ).status_code
        == 200
    )
    assert len(collections[get_product_eligibility_reports_collection].documents) == 1


def test_get_report_supports_status_pagination_and_safe_urls():
    client, _, _, upload_id, token = api_context()
    client.post(f"/api/product-eligibility/{upload_id}/evaluate", headers=auth(token))
    response = client.get(
        f"/api/product-eligibility/{upload_id}?status=excluded&page=1&page_size=1",
        headers=auth(token),
    )
    assert response.status_code == 200
    assert response.json()["pagination"]["page_size"] == 1
    assert "storage_reference" not in response.text and "password" not in response.text


def test_product_detail_is_owned_and_safe():
    client, _, _, upload_id, token = api_context()
    client.post(f"/api/product-eligibility/{upload_id}/evaluate", headers=auth(token))
    response = client.get(
        f"/api/product-eligibility/{upload_id}/products/PRD-API001",
        headers=auth(token),
    )
    assert response.status_code == 200
    assert response.json()["product"]["product_id"] == "PRD-API001"
    assert "guarantee" in response.json()["disclaimer"].lower()
    assert (
        client.get(f"/api/product-eligibility/{upload_id}/products/PRD-API001").status_code == 401
    )


def test_report_not_found_returns_404_without_rerun():
    client, _, _, upload_id, token = api_context()
    assert (
        client.get(f"/api/product-eligibility/{upload_id}", headers=auth(token)).status_code == 404
    )
