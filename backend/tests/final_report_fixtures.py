from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId

from app.models.skincare_routine import build_routine_document
from app.schemas.product_recommendation import StoredRecommendation
from app.services.skincare_routine_service import build_routines
from tests.catalogue_fakes import FakeCollection, demo_product

NOW = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)


def stored_recommendation(**overrides: Any) -> dict[str, Any]:
    data = {
        "product_id": "PRD-TEST001",
        "product_name": "Test Gentle Cleanser",
        "brand_name": "DermaDemo Labs",
        "normalized_brand_name": "dermademo labs",
        "category": "cleanser",
        "is_demo_product": True,
        "price": {"amount": 499.0, "currency": "INR"},
        "availability_status": "available",
        "eligibility_status": "eligible",
        "base_score": 82.0,
        "penalties": [],
        "total_penalty": 0.0,
        "final_score": 82.0,
        "score_band": "Strong Match",
        "score_breakdown": {
            "skin_type_match": 90,
            "visible_concern_match": 80,
            "ingredient_relevance": 80,
            "sensitivity_compatibility": 90,
            "budget_fit": 100,
            "availability": 100,
            "brand_preference": 50,
            "data_quality": 70,
            "rating": 50,
            "base_score": 82,
            "caution_penalty": 0,
            "final_score": 82,
        },
        "positive_factors": ["The category aligns with available profile evidence."],
        "caution_factors": [],
        "why_recommended": "This option aligns with the stored profile and visible skincare observations.",
        "recommendation_confidence": "moderate",
        "confidence_reasons": ["Required evidence was available."],
        "data_freshness": {"price": "fresh", "availability": "fresh", "source": "fresh"},
        "ingredient_profile": ["glycerin", "niacinamide"],
        "price_tier": "value",
        "rank_within_category": 1,
        "overall_rank": 1,
    }
    data.update(overrides)
    return data


def full_source_documents(
    user_id: ObjectId | None = None, upload_id: str = "UP-FINAL-001"
) -> tuple[ObjectId, dict[str, dict[str, Any]]]:
    owner = user_id or ObjectId()
    recs = [
        stored_recommendation(),
        stored_recommendation(
            product_id="PRD-MOIST",
            product_name="Test Barrier Moisturizer",
            category="moisturizer",
            final_score=78,
            score_band="Good Match",
            rank_within_category=1,
            overall_rank=2,
        ),
        stored_recommendation(
            product_id="PRD-SUN",
            product_name="Test Daily Sunscreen",
            category="sunscreen",
            final_score=76,
            score_band="Good Match",
            rank_within_category=1,
            overall_rank=3,
        ),
        stored_recommendation(
            product_id="PRD-SERUM",
            product_name="Test Optional Serum",
            category="serum",
            final_score=71,
            score_band="Good Match",
            rank_within_category=1,
            overall_rank=4,
        ),
    ]
    recommendation_models = [StoredRecommendation.model_validate(item) for item in recs]
    morning, night, alternatives, warnings = build_routines(recommendation_models)
    routine = build_routine_document(
        upload_id=upload_id,
        user_id=str(owner),
        recommendation_report_id="REC-FINAL",
        morning=morning,
        night=night,
        optional_products=alternatives,
        warnings=warnings,
        now=NOW,
    )
    documents = {
        "skin_profile": {
            "_id": ObjectId(),
            "user_id": owner,
            "age_group": "18-25",
            "country": "India",
            "oiliness_level": "High",
            "dryness_level": "Moderate",
            "is_sensitive": True,
            "known_allergies": ["Added Fragrance"],
            "ingredients_to_avoid": ["Drying Alcohol"],
            "fragrance_preference": "Fragrance-free only",
            "budget_min": 200,
            "budget_max": 1000,
            "experience_level": "Beginner",
            "is_complete": True,
            "created_at": NOW,
            "updated_at": NOW,
        },
        "image_upload": {
            "_id": ObjectId(),
            "user_id": owner,
            "upload_id": upload_id,
            "consent_given": True,
            "status": "final_report_pending",
            "created_at": NOW,
            "updated_at": NOW,
            "expires_at": NOW + timedelta(minutes=30),
        },
        "image_quality": {
            "_id": ObjectId(),
            "user_id": owner,
            "upload_id": upload_id,
            "quality_report_id": "Q-FINAL",
            "quality_status": "passed",
            "quality_score": 86,
            "warning_accepted": False,
            "created_at": NOW,
            "updated_at": NOW,
        },
        "face_detection": {
            "_id": ObjectId(),
            "user_id": owner,
            "upload_id": upload_id,
            "face_report_id": "FACE-FINAL",
            "quality_report_id": "Q-FINAL",
            "detection_status": "passed",
            "face_count": 1,
            "warning_accepted": False,
            "created_at": NOW,
            "updated_at": NOW,
        },
        "image_preprocessing": {
            "_id": ObjectId(),
            "user_id": owner,
            "upload_id": upload_id,
            "preprocessing_report_id": "PRE-FINAL",
            "face_report_id": "FACE-FINAL",
            "quality_report_id": "Q-FINAL",
            "preprocessing_status": "completed",
            "created_at": NOW,
            "updated_at": NOW,
        },
        "skin_type": {
            "_id": ObjectId(),
            "user_id": owner,
            "upload_id": upload_id,
            "skin_type_report_id": "ST-FINAL",
            "preprocessing_report_id": "PRE-FINAL",
            "model_name": "Test Skin Type Model",
            "model_version": "1.0-test",
            "final_skin_type": "Combination",
            "result_status": "estimated",
            "model_confidence": 0.82,
            "confidence_level": "moderate",
            "agreement_status": "strong",
            "self_reported_sensitivity": True,
            "explanation": "The saved image estimate and questionnaire evidence were broadly aligned.",
            "created_at": NOW,
            "updated_at": NOW,
        },
        "skin_concern": {
            "_id": ObjectId(),
            "user_id": owner,
            "upload_id": upload_id,
            "skin_concern_report_id": "SC-FINAL",
            "preprocessing_report_id": "PRE-FINAL",
            "skin_type_report_id": "ST-FINAL",
            "model_name": "Test Concern Model",
            "model_version": "1.0-test",
            "overall_status": "completed",
            "concern_results": [
                {
                    "concern_code": "visible_oiliness",
                    "display_name": "Visible Oiliness",
                    "status": "observed",
                    "visible_severity": "moderate",
                    "score": 0.81,
                    "regions": ["T-zone"],
                    "explanation": "Visible shine was observed.",
                },
                {
                    "concern_code": "visible_pores",
                    "display_name": "Visible Pores",
                    "status": "possible",
                    "visible_severity": "mild",
                    "score": 0.62,
                    "regions": ["Nose"],
                    "explanation": "Visible pores may be present.",
                },
            ],
            "created_at": NOW,
            "updated_at": NOW,
        },
        "product_eligibility": {
            "_id": ObjectId(),
            "user_id": owner,
            "upload_id": upload_id,
            "eligibility_report_id": "ELG-FINAL",
            "created_at": NOW,
            "updated_at": NOW,
        },
        "product_recommendation": {
            "_id": ObjectId(),
            "user_id": owner,
            "upload_id": upload_id,
            "recommendation_report_id": "REC-FINAL",
            "eligibility_report_id": "ELG-FINAL",
            "scoring_engine_version": "1.0.0",
            "overall_confidence": "moderate",
            "recommendations": recs,
            "limitations": [],
            "created_at": NOW,
            "updated_at": NOW,
        },
        "skincare_routine": {"_id": ObjectId(), **routine},
    }
    return owner, documents


def collection_map(documents: dict[str, dict[str, Any]]) -> dict[str, FakeCollection]:
    products = [
        demo_product(),
        demo_product(
            product_id="PRD-MOIST",
            slug="test-moist",
            product_name="Test Barrier Moisturizer",
            category="moisturizer",
        ),
        demo_product(
            product_id="PRD-SUN",
            slug="test-sun",
            product_name="Test Daily Sunscreen",
            category="sunscreen",
        ),
        demo_product(
            product_id="PRD-SERUM",
            slug="test-serum",
            product_name="Test Optional Serum",
            category="serum",
        ),
    ]
    return {
        **{key: FakeCollection([value]) for key, value in documents.items()},
        "products": FakeCollection(products),
        "final_reports": FakeCollection(),
    }
