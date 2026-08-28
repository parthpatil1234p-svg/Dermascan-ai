from collections import Counter
from datetime import datetime, timezone
from statistics import mean
from typing import Any
from uuid import uuid4

from app.services.feedback_privacy_service import analytics_safe_snapshot


def _average(items: list[dict[str, Any]], field: str) -> float | None:
    values = [item[field] for item in items if isinstance(item.get(field), int)]
    return round(mean(values), 2) if values else None


def build_feedback_analytics(
    documents: list[dict[str, Any]], min_group_size: int
) -> dict[str, Any]:
    eligible = [
        item
        for item in documents
        if item.get("feedback_status") in {"active", "edited"}
        and item.get("consent_for_analytics") is True
        and item.get("moderation_status") != "flagged"
    ]
    all_count = len(documents)
    reasons = Counter(reason for item in eligible for reason in item.get("selected_reasons", []))
    product_reports = [item for item in eligible if item.get("product_id")]
    routine_reports = [
        item for item in eligible if item.get("feedback_category") == "routine_feedback"
    ]
    skin_type_reports = [
        item for item in eligible if item.get("feedback_category") == "skin_type_feedback"
    ]
    unavailable = sum(
        item.get("availability_feedback") == "unavailable" for item in product_reports
    )
    expensive = sum(item.get("price_feedback") == "too_expensive" for item in product_reports)
    discomfort = sum(
        item.get("irritation_reported")
        in {"mild_discomfort", "visible_irritation", "serious_reaction"}
        for item in product_reports
    )
    return analytics_safe_snapshot(
        {
            "eligible_feedback_count": len(eligible),
            "total_feedback_count": all_count,
            "feedback_submission_rate": None,
            "withdrawal_rate_percent": (
                round(
                    100
                    * sum(item.get("feedback_status") == "withdrawn" for item in documents)
                    / all_count,
                    2,
                )
                if all_count
                else 0.0
            ),
            "average_report_helpfulness": _average(eligible, "helpfulness_rating"),
            "average_recommendation_relevance": _average(eligible, "recommendation_relevance"),
            "product_unavailable_percent": (
                round(100 * unavailable / len(product_reports), 2) if product_reports else 0.0
            ),
            "product_too_expensive_percent": (
                round(100 * expensive / len(product_reports), 2) if product_reports else 0.0
            ),
            "routine_complexity_complaints": sum(
                item.get("routine_difficulty") in {"difficult", "too_complex"}
                for item in routine_reports
            ),
            "skin_type_disagreement_rate_percent": (
                round(
                    100
                    * sum(
                        item.get("accuracy_perception") == "does_not_match"
                        for item in skin_type_reports
                    )
                    / len(skin_type_reports),
                    2,
                )
                if skin_type_reports
                else 0.0
            ),
            "product_discomfort_report_count": discomfort,
            "most_common_reasons": [
                {"code": code, "count": count}
                for code, count in reasons.most_common(10)
                if count >= min_group_size
            ],
            "minimum_group_size": min_group_size,
        }
    )


async def create_analytics_snapshot(
    feedback_collection: Any, analytics_collection: Any, min_group_size: int
) -> dict[str, Any]:
    documents = await feedback_collection.find({}).to_list(length=None)
    now = datetime.now(timezone.utc)
    snapshot = {
        "snapshot_id": f"FAS-{uuid4().hex[:10].upper()}",
        **build_feedback_analytics(documents, min_group_size),
        "created_at": now,
    }
    await analytics_collection.insert_one(dict(snapshot))
    return snapshot
