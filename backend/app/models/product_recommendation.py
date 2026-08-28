from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId

from app.schemas.product_recommendation import StoredRecommendation

SCORING_ENGINE_VERSION = "1.0.0"
REPORT_LIMITATIONS = [
    "Recommendations depend on the available product catalogue.",
    "Product ingredients, prices, and availability may change.",
    "A relevance score cannot guarantee safety, effectiveness, or medical suitability.",
]


def build_recommendation_report_document(
    *,
    upload_id: str,
    user_id: str,
    eligibility_report: dict[str, Any],
    configuration: dict[str, Any],
    candidate_results: list[StoredRecommendation],
    recommendations: list[StoredRecommendation],
    overall_confidence: str,
    confidence_reasons: list[str],
    now: datetime,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    categories: dict[str, list[str]] = {}
    for item in recommendations:
        categories.setdefault(item.category, []).append(item.product_id)
    return {
        "recommendation_report_id": (
            existing["recommendation_report_id"] if existing else f"REC-{uuid4().hex.upper()}"
        ),
        "user_id": ObjectId(user_id),
        "upload_id": upload_id,
        "eligibility_report_id": eligibility_report["eligibility_report_id"],
        "skin_profile_id": eligibility_report["skin_profile_id"],
        "skin_type_report_id": eligibility_report["skin_type_report_id"],
        "skin_concern_report_id": eligibility_report["skin_concern_report_id"],
        "catalogue_version": eligibility_report["catalogue_version"],
        "scoring_engine_version": SCORING_ENGINE_VERSION,
        "scoring_configuration": configuration,
        "candidate_count": len(candidate_results),
        "recommended_count": len(recommendations),
        "category_results": categories,
        "candidate_results": [item.model_dump(mode="python") for item in candidate_results],
        "recommendations": [item.model_dump(mode="python") for item in recommendations],
        "overall_confidence": overall_confidence,
        "confidence_reasons": confidence_reasons,
        "limitations": REPORT_LIMITATIONS,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }
