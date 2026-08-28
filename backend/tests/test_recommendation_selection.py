from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_image_uploads_collection,
    get_ingredients_collection,
    get_product_eligibility_reports_collection,
    get_product_recommendation_reports_collection,
    get_products_collection,
    get_skin_concern_reports_collection,
    get_skin_profiles_collection,
    get_users_collection,
)
from app.core.config import get_settings
from app.core.security import create_access_token
from app.main import create_app
from app.models.product_recommendation import SCORING_ENGINE_VERSION
from app.services.recommendation_engine_service import score_candidate
from app.services.recommendation_selection_service import select_recommendations, sort_candidates
from tests.catalogue_fakes import FakeCollection
from tests.eligibility_fixtures import filtering_context, real_product
from tests.recommendation_fixtures import caution, recommendation_candidate, recommendation_context


def scored(
    product_id,
    *,
    category="cleanser",
    brand="Brand A",
    amount=400,
    ingredients=None,
    final_score=None,
):
    candidate = recommendation_candidate(
        product_id=product_id,
        product_name=f"Product {product_id}",
        category=category,
        brand_name=brand,
        normalized_brand_name=brand.casefold(),
        price={"amount": amount, "currency": "INR"},
        normalized_ingredients=ingredients or [f"ingredient-{product_id}"],
    )
    result = score_candidate(candidate, recommendation_context(), get_settings())
    if final_score is not None:
        breakdown = result.score_breakdown.model_copy(update={"final_score": final_score})
        result = result.model_copy(
            update={"final_score": final_score, "score_breakdown": breakdown}
        )
    return result


def test_minimum_display_threshold_is_enforced():
    selected = select_recommendations([scored("LOW", final_score=59.9)], get_settings())
    assert selected == []


def test_category_ranking_selects_top_two():
    items = [scored("A", final_score=90), scored("B", final_score=80), scored("C", final_score=70)]
    selected = select_recommendations(items, get_settings())
    assert [item.product_id for item in selected] == ["A", "B"]
    assert [item.rank_within_category for item in selected] == [1, 2]


def test_diversity_limits_same_brand_overall():
    items = [
        scored("A", category="cleanser", brand="One", final_score=90),
        scored("B", category="serum", brand="One", final_score=89),
        scored("C", category="moisturizer", brand="One", final_score=88),
        scored("D", category="moisturizer", brand="Two", final_score=87),
    ]
    selected = select_recommendations(items, get_settings())
    assert sum(item.brand_name == "One" for item in selected) == 2
    assert any(item.product_id == "D" for item in selected)


def test_diversity_prefers_second_price_tier_when_available():
    items = [
        scored("A", amount=300, final_score=90),
        scored("B", amount=350, final_score=89),
        scored("C", amount=800, final_score=88),
    ]
    selected = select_recommendations(items, get_settings())
    assert {item.price_tier for item in selected} == {"value", "mid"}


def test_near_identical_ingredient_profiles_are_not_duplicated():
    items = [
        scored("A", ingredients=["niacinamide", "glycerin"], final_score=90),
        scored("B", ingredients=["niacinamide", "glycerin"], final_score=89),
        scored("C", ingredients=["ceramide"], final_score=88),
    ]
    selected = select_recommendations(items, get_settings())
    assert {item.product_id for item in selected} == {"A", "C"}


def test_diversity_never_uses_below_threshold_candidate():
    selected = select_recommendations(
        [
            scored("A", final_score=90),
            scored("LOW", amount=900, final_score=20),
        ],
        get_settings(),
    )
    assert [item.product_id for item in selected] == ["A"]


def test_tie_breaking_is_deterministic_by_product_name():
    a = scored("B", final_score=80).model_copy(update={"product_name": "Zulu"})
    b = scored("A", final_score=80).model_copy(update={"product_name": "Alpha"})
    assert [item.product_name for item in sort_candidates([a, b])] == ["Alpha", "Zulu"]


def eligibility_item(product, status="eligible", cautions=None):
    return {
        "product_id": product["product_id"],
        "product_name": product["product_name"],
        "brand_name": product["brand_name"],
        "category": product["category"],
        "is_demo_product": product["is_demo_product"],
        "price": product.get("price"),
        "price_checked_at": product.get("price_checked_at"),
        "availability_status": product["availability_status"],
        "availability_checked_at": product.get("availability_checked_at"),
        "eligibility_status": status,
        "hard_exclusions": [],
        "cautions": [item.model_dump() for item in (cautions or [])],
        "positive_matches": [],
        "information_gaps": [],
    }


def api_context():
    now = datetime.now(timezone.utc)
    user_id, upload_id = ObjectId(), "upload-step12"
    users = FakeCollection(
        [
            {
                "_id": user_id,
                "full_name": "Recommendation User",
                "email": "recommend@example.com",
                "password_hash": "unused",
                "is_active": True,
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
                "is_sensitive": False,
                "oiliness_level": "High",
                "dryness_level": "Moderate",
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
                "status": "recommendation_scoring_pending",
                "image_format": "JPEG",
                "file_size_bytes": 200000,
                "width": 1080,
                "height": 1080,
                "created_at": now,
                "updated_at": now,
                "expires_at": now + timedelta(minutes=30),
            }
        ]
    )
    product_one = real_product(product_id="PRD-R001", slug="rec-one", category="cleanser")
    product_two = real_product(
        product_id="PRD-R002",
        slug="rec-two",
        product_name="Caution Serum",
        category="serum",
        sensitivity_suitability="use_with_caution",
    )
    excluded = real_product(
        product_id="PRD-R003", slug="rec-three", product_name="Excluded Product"
    )
    gap = real_product(product_id="PRD-R004", slug="rec-four", product_name="Unknown Product")
    products = FakeCollection([product_one, product_two, excluded, gap])
    context = filtering_context(user_id=str(user_id))
    eligibility = FakeCollection(
        [
            {
                "_id": ObjectId(),
                "eligibility_report_id": "ELG-STEP12",
                "upload_id": upload_id,
                "user_id": user_id,
                "skin_profile_id": str(profile_id),
                "skin_type_report_id": "ST-STEP12",
                "skin_concern_report_id": "SC-STEP12",
                "catalogue_version": "test-catalogue",
                "filter_engine_version": "1.0.0",
                "user_filter_context": context.model_dump(mode="python"),
                "product_results": [
                    eligibility_item(product_one),
                    eligibility_item(
                        product_two,
                        "eligible_with_caution",
                        [caution("SENSITIVITY_USE_WITH_CAUTION")],
                    ),
                    eligibility_item(excluded, "excluded"),
                    eligibility_item(gap, "insufficient_information"),
                ],
                "created_at": now,
                "updated_at": now,
            }
        ]
    )
    concerns = FakeCollection(
        [
            {
                "_id": ObjectId(),
                "skin_concern_report_id": "SC-STEP12",
                "upload_id": upload_id,
                "user_id": user_id,
                "overall_status": "completed",
                "concern_results": [
                    {"concern_code": "visible_oiliness", "status": "observed"},
                    {"concern_code": "visible_pores", "status": "possible"},
                ],
            }
        ]
    )
    ingredients = FakeCollection(
        [
            {
                "ingredient_id": "ING-NIAC",
                "normalized_name": "niacinamide",
                "normalized_aliases": [],
                "common_skincare_roles": ["oil-balance support"],
                "is_active": True,
            },
            {
                "ingredient_id": "ING-GLYC",
                "normalized_name": "glycerin",
                "normalized_aliases": [],
                "common_skincare_roles": ["moisture support"],
                "is_active": True,
            },
        ]
    )
    reports = FakeCollection()
    app = create_app(enable_lifespan=False)
    mapping = {
        get_users_collection: users,
        get_skin_profiles_collection: profiles,
        get_image_uploads_collection: uploads,
        get_product_eligibility_reports_collection: eligibility,
        get_product_recommendation_reports_collection: reports,
        get_products_collection: products,
        get_ingredients_collection: ingredients,
        get_skin_concern_reports_collection: concerns,
    }

    def override(collection):
        def provide():
            return collection

        return provide

    for dependency, collection in mapping.items():
        app.dependency_overrides[dependency] = override(collection)
    return TestClient(app), mapping, upload_id, create_access_token(subject=str(user_id))


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_successful_generation_only_scores_allowed_candidates():
    client, collections, upload_id, token = api_context()
    response = client.post(
        f"/api/product-recommendations/{upload_id}/generate", headers=auth(token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["candidate_count"] == 2
    assert "PRD-R003" not in response.text and "PRD-R004" not in response.text
    assert (
        collections[get_image_uploads_collection].documents[0]["status"]
        == "routine_generation_pending"
    )
    assert len(collections[get_product_recommendation_reports_collection].documents) == 1


def test_generation_requires_authentication():
    client, _, upload_id, _ = api_context()
    assert client.post(f"/api/product-recommendations/{upload_id}/generate").status_code == 401


def test_other_user_cannot_generate_for_upload():
    client, collections, upload_id, _ = api_context()
    other_id = ObjectId()
    collections[get_users_collection].documents.append(
        {
            "_id": other_id,
            "full_name": "Other",
            "email": "other-rec@example.com",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
    )
    response = client.post(
        f"/api/product-recommendations/{upload_id}/generate",
        headers=auth(create_access_token(subject=str(other_id))),
    )
    assert response.status_code == 404


def test_missing_eligibility_report_is_rejected():
    client, collections, upload_id, token = api_context()
    collections[get_product_eligibility_reports_collection].documents.clear()
    assert (
        client.post(
            f"/api/product-recommendations/{upload_id}/generate", headers=auth(token)
        ).status_code
        == 409
    )


def test_report_update_preserves_one_document_and_version_snapshot():
    client, collections, upload_id, token = api_context()
    assert (
        client.post(
            f"/api/product-recommendations/{upload_id}/generate", headers=auth(token)
        ).status_code
        == 200
    )
    collections[get_image_uploads_collection].documents[0]["status"] = "recommendations_completed"
    assert (
        client.post(
            f"/api/product-recommendations/{upload_id}/generate", headers=auth(token)
        ).status_code
        == 200
    )
    reports = collections[get_product_recommendation_reports_collection].documents
    assert len(reports) == 1
    assert reports[0]["scoring_engine_version"] == SCORING_ENGINE_VERSION
    assert sum(reports[0]["scoring_configuration"]["weights"].values()) == 1


def test_get_report_filters_and_returns_safe_paginated_data():
    client, _, upload_id, token = api_context()
    client.post(f"/api/product-recommendations/{upload_id}/generate", headers=auth(token))
    response = client.get(
        f"/api/product-recommendations/{upload_id}?category=cleanser&page=1&page_size=1&minimum_score=60",
        headers=auth(token),
    )
    assert response.status_code == 200
    assert response.json()["pagination"]["page_size"] == 1
    assert "storage_reference" not in response.text and "user_filter_context" not in response.text


def test_owned_recommendation_detail_is_safe():
    client, _, upload_id, token = api_context()
    generated = client.post(
        f"/api/product-recommendations/{upload_id}/generate", headers=auth(token)
    ).json()
    product_id = next(
        item["product_id"] for values in generated["categories"].values() for item in values
    )
    response = client.get(
        f"/api/product-recommendations/{upload_id}/products/{product_id}", headers=auth(token)
    )
    assert response.status_code == 200
    assert "not medical scores" in response.json()["disclaimer"]
    assert '"_id":' not in response.text


def test_missing_report_get_returns_404_without_generation():
    client, _, upload_id, token = api_context()
    assert (
        client.get(f"/api/product-recommendations/{upload_id}", headers=auth(token)).status_code
        == 404
    )


def test_no_candidate_report_is_low_confidence_and_does_not_lower_threshold():
    client, collections, upload_id, token = api_context()
    eligibility = collections[get_product_eligibility_reports_collection].documents[0]
    for item in eligibility["product_results"]:
        item["eligibility_status"] = "excluded"
    response = client.post(
        f"/api/product-recommendations/{upload_id}/generate", headers=auth(token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["candidate_count"] == 0 and data["recommended_count"] == 0
    assert data["overall_confidence"] == "low" and data["can_continue"] is False
