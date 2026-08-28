from datetime import datetime, timezone

from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_catalogue_review_signals_collection,
    get_feedback_analytics_collection,
    get_feedback_collection,
    get_feedback_moderation_audit_collection,
    get_feedback_signals_collection,
    get_final_reports_collection,
    get_product_recommendation_reports_collection,
    get_skincare_routine_reports_collection,
    get_user_product_avoidance_collection,
    get_users_collection,
)
from app.core.config import get_settings
from app.core.security import create_access_token
from app.main import create_app
from tests.catalogue_fakes import FakeCollection
from tests.final_report_fixtures import full_source_documents


def _final_report(owner: ObjectId, documents: dict) -> dict:
    recommendation = documents["product_recommendation"]
    concerns = documents["skin_concern"]["concern_results"]
    snapshots = [
        {
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "brand_name": item["brand_name"],
            "category": item["category"],
            "score": item["final_score"],
            "demo_status": item["is_demo_product"],
        }
        for item in recommendation["recommendations"]
    ]
    visible = {"observed": [], "possible": [], "uncertain": []}
    for item in concerns:
        visible[item["status"]].append({"code": item["concern_code"], "name": item["display_name"]})
    return {
        "_id": ObjectId(),
        "final_report_id": "DSR-2026-FDBTEST1",
        "user_id": owner,
        "upload_id": documents["image_upload"]["upload_id"],
        "report_status": "complete_with_limitations",
        "source_report_ids": {
            "product_recommendation": recommendation["recommendation_report_id"],
            "skincare_routine": documents["skincare_routine"]["routine_report_id"],
        },
        "skin_type_summary": {"skin_type": "Combination"},
        "visible_concern_summary": visible,
        "product_recommendation_summary": snapshots,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def feedback_api_context(*, max_per_hour: int = 20):
    owner, documents = full_source_documents()
    admin_id = ObjectId()
    users = FakeCollection(
        [
            {
                "_id": owner,
                "full_name": "Feedback User",
                "email": "feedback@example.com",
                "is_active": True,
                "is_admin": False,
                "created_at": datetime.now(timezone.utc),
            },
            {
                "_id": admin_id,
                "full_name": "Feedback Admin",
                "email": "admin@example.com",
                "is_active": True,
                "is_admin": True,
                "created_at": datetime.now(timezone.utc),
            },
        ]
    )
    collections = {
        "feedback": FakeCollection(),
        "final_reports": FakeCollection([_final_report(owner, documents)]),
        "recommendation_reports": FakeCollection([documents["product_recommendation"]]),
        "routine_reports": FakeCollection([documents["skincare_routine"]]),
        "avoidances": FakeCollection(),
        "improvement_signals": FakeCollection(),
        "catalogue_signals": FakeCollection(),
        "analytics": FakeCollection(),
        "audit": FakeCollection(),
    }
    app = create_app(enable_lifespan=False)
    mapping = {
        get_users_collection: users,
        get_feedback_collection: collections["feedback"],
        get_final_reports_collection: collections["final_reports"],
        get_product_recommendation_reports_collection: collections["recommendation_reports"],
        get_skincare_routine_reports_collection: collections["routine_reports"],
        get_user_product_avoidance_collection: collections["avoidances"],
        get_feedback_signals_collection: collections["improvement_signals"],
        get_catalogue_review_signals_collection: collections["catalogue_signals"],
        get_feedback_analytics_collection: collections["analytics"],
        get_feedback_moderation_audit_collection: collections["audit"],
    }

    def override(collection):
        def provide():
            return collection

        return provide

    for dependency, collection in mapping.items():
        app.dependency_overrides[dependency] = override(collection)
    settings = get_settings().model_copy(
        update={
            "app_env": "testing",
            "feedback_max_submissions_per_hour": max_per_hour,
        }
    )
    app.dependency_overrides[get_settings] = lambda: settings
    return {
        "client": TestClient(app),
        "collections": collections,
        "owner": owner,
        "token": create_access_token(subject=str(owner)),
        "admin_token": create_access_token(subject=str(admin_id)),
        "final_report_id": "DSR-2026-FDBTEST1",
        "recommendation_report_id": documents["product_recommendation"]["recommendation_report_id"],
        "routine_report_id": documents["skincare_routine"]["routine_report_id"],
    }


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def analysis_payload(context, **overrides):
    payload = {
        "final_report_id": context["final_report_id"],
        "feedback_category": "analysis_feedback",
        "overall_rating": 4,
        "comment": "The workflow was easy to understand.",
        "consent_for_analytics": True,
    }
    payload.update(overrides)
    return payload


def product_payload(context, **overrides):
    payload = {
        "final_report_id": context["final_report_id"],
        "feedback_category": "product_recommendation_feedback",
        "product_id": "PRD-TEST001",
        "overall_rating": 4,
        "recommendation_relevance": 4,
        "price_feedback": "within_budget",
        "availability_feedback": "available",
        "selected_reasons": ["PRODUCTS_MATCH_BUDGET"],
        "comment": "This option was easy to find locally.",
    }
    payload.update(overrides)
    return payload
