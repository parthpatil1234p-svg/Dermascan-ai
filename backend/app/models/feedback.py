from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId

from app.schemas.feedback import FeedbackPayload, FeedbackResponse

FEEDBACK_ACKNOWLEDGEMENT = (
    "Thank you. Your feedback has been saved and will be used according to "
    "your selected consent preferences."
)


def build_feedback_document(
    *,
    payload: FeedbackPayload,
    user_id: str,
    related: dict[str, Any],
    sanitized_fields: dict[str, str | None],
    moderation_status: str,
    moderation_reasons: list[str],
    payload_hash: str,
    now: datetime,
) -> dict[str, Any]:
    data = payload.model_dump(mode="python")
    data.update(sanitized_fields)
    return {
        **data,
        "_id": ObjectId(),
        "feedback_id": f"FDB-{uuid4().hex[:8].upper()}",
        "user_id": ObjectId(user_id),
        "upload_id": related.get("upload_id"),
        "final_report_id": related.get("final_report_id"),
        "recommendation_report_id": related.get("recommendation_report_id"),
        "routine_report_id": related.get("routine_report_id"),
        "product_name": related.get("product_name"),
        "feedback_status": "flagged" if moderation_status == "flagged" else "active",
        "moderation_status": moderation_status,
        "moderation_reasons": moderation_reasons,
        "payload_hash": payload_hash,
        "created_at": now,
        "updated_at": now,
        "withdrawn_at": None,
    }


def feedback_document_to_response(
    document: dict[str, Any], *, include_acknowledgement: bool = False
) -> FeedbackResponse:
    fields = FeedbackPayload.model_fields
    payload = {name: document.get(name) for name in fields}
    payload["selected_reasons"] = document.get("selected_reasons", [])
    payload["exclude_product_from_future_recommendations"] = bool(
        document.get("exclude_product_from_future_recommendations", False)
    )
    payload["consent_for_analytics"] = bool(document.get("consent_for_analytics", False))
    payload["consent_for_research_review"] = bool(
        document.get("consent_for_research_review", False)
    )
    payload["is_anonymous_for_aggregate_use"] = bool(
        document.get("is_anonymous_for_aggregate_use", True)
    )
    return FeedbackResponse(
        **payload,
        feedback_id=document["feedback_id"],
        upload_id=document.get("upload_id"),
        feedback_status=document["feedback_status"],
        moderation_status=document.get("moderation_status", "clear"),
        moderation_reasons=document.get("moderation_reasons", []),
        product_name=document.get("product_name"),
        created_at=document["created_at"],
        updated_at=document["updated_at"],
        withdrawn_at=document.get("withdrawn_at"),
        acknowledgement=FEEDBACK_ACKNOWLEDGEMENT if include_acknowledgement else None,
    )
