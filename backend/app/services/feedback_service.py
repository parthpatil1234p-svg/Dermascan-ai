import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId

from app.core.config import Settings
from app.models.feedback import build_feedback_document, feedback_document_to_response
from app.repositories.feedback_repository import (
    find_owned_feedback,
    insert_feedback,
    list_owned_feedback,
    recent_owned_feedback,
    replace_feedback,
)
from app.schemas.feedback import (
    NEGATIVE_REASON_CODES,
    POSITIVE_REASON_CODES,
    PRODUCT_EXPERIENCE_REASON_CODES,
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackOptionsResponse,
    FeedbackResponse,
    FeedbackUpdate,
    FeedbackWithdrawalResponse,
    ProductAvoidanceListResponse,
    ProductAvoidanceResponse,
)
from app.schemas.pagination import pagination_metadata
from app.services.feedback_moderation_service import assess_feedback_moderation
from app.services.feedback_privacy_service import sanitize_feedback_fields
from app.services.feedback_signal_service import (
    rebuild_catalogue_signals,
    sync_improvement_signals,
    sync_product_avoidance,
)
from app.services.feedback_validation_service import validate_feedback_relationships


class FeedbackNotFoundError(Exception):
    pass


class FeedbackConflictError(Exception):
    pass


class FeedbackRateLimitError(Exception):
    pass


class FeedbackStateError(Exception):
    pass


def feedback_payload_hash(payload: FeedbackCreate | FeedbackUpdate, related: dict[str, Any]) -> str:
    safe_payload = payload.model_dump(mode="json")
    safe_payload.update(
        {
            "resolved_final_report_id": related.get("final_report_id"),
            "resolved_upload_id": related.get("upload_id"),
        }
    )
    serialized = json.dumps(safe_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


async def enforce_submission_limits(
    collection: Any,
    user_id: str,
    payload_hash: str,
    settings: Settings,
    now: datetime,
    *,
    exclude_feedback_id: str | None = None,
) -> None:
    hour_items = await recent_owned_feedback(collection, user_id, now - timedelta(hours=1))
    new_items = [item for item in hour_items if item.get("feedback_id") != exclude_feedback_id]
    if len(new_items) >= settings.feedback_max_submissions_per_hour:
        raise FeedbackRateLimitError("Feedback submission limit reached. Please try again later.")
    if settings.feedback_duplicate_window_seconds == 0:
        return
    duplicate_cutoff = now - timedelta(seconds=settings.feedback_duplicate_window_seconds)
    if any(
        item.get("payload_hash") == payload_hash
        and item.get("created_at") >= duplicate_cutoff
        and item.get("feedback_status") != "withdrawn"
        for item in new_items
    ):
        raise FeedbackConflictError("This feedback was already submitted recently.")


async def create_feedback(
    *,
    payload: FeedbackCreate,
    user_id: str,
    collections: dict[str, Any],
    settings: Settings,
) -> FeedbackResponse:
    related = await validate_feedback_relationships(
        payload=payload,
        user_id=user_id,
        final_reports=collections["final_reports"],
        recommendation_reports=collections["recommendation_reports"],
        routine_reports=collections["routine_reports"],
    )
    now = datetime.now(timezone.utc)
    payload_hash = feedback_payload_hash(payload, related)
    await enforce_submission_limits(collections["feedback"], user_id, payload_hash, settings, now)
    raw_texts = [
        payload.comment,
        payload.irritation_description,
        payload.morning_routine_feedback,
        payload.night_routine_feedback,
        payload.export_experience,
    ]
    moderation_status, moderation_reasons = assess_feedback_moderation(raw_texts)
    sanitized = sanitize_feedback_fields(payload, settings.feedback_max_comment_length)
    document = build_feedback_document(
        payload=payload,
        user_id=user_id,
        related=related,
        sanitized_fields=sanitized,
        moderation_status=moderation_status,
        moderation_reasons=moderation_reasons,
        payload_hash=payload_hash,
        now=now,
    )
    await insert_feedback(collections["feedback"], document)
    await sync_improvement_signals(collections["improvement_signals"], document, now, active=True)
    await sync_product_avoidance(collections["avoidances"], document, now, active=True)
    await rebuild_catalogue_signals(
        collections["feedback"],
        collections["catalogue_signals"],
        document.get("product_id"),
        set(document.get("selected_reasons", [])),
        now,
    )
    return feedback_document_to_response(document, include_acknowledgement=True)


async def get_feedback_detail(collection: Any, feedback_id: str, user_id: str) -> FeedbackResponse:
    document = await find_owned_feedback(collection, feedback_id, user_id)
    if document is None:
        raise FeedbackNotFoundError
    return feedback_document_to_response(document)


async def get_feedback_history(
    collection: Any,
    user_id: str,
    *,
    page: int,
    page_size: int,
    category: str | None,
    feedback_status: str | None,
    final_report_id: str | None,
    product_id: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> FeedbackListResponse:
    query: dict[str, Any] = {}
    if category:
        query["feedback_category"] = category
    if feedback_status:
        query["feedback_status"] = feedback_status
    if final_report_id:
        query["final_report_id"] = final_report_id
    if product_id:
        query["product_id"] = product_id
    if date_from or date_to:
        query["created_at"] = {}
        if date_from:
            query["created_at"]["$gte"] = date_from
        if date_to:
            query["created_at"]["$lte"] = date_to
    items, total = await list_owned_feedback(
        collection, user_id, query, page=page, page_size=page_size
    )
    return FeedbackListResponse(
        feedback=[feedback_document_to_response(item) for item in items],
        pagination=pagination_metadata(page, page_size, total),
    )


async def update_feedback(
    *,
    feedback_id: str,
    payload: FeedbackUpdate,
    user_id: str,
    collections: dict[str, Any],
    settings: Settings,
) -> FeedbackResponse:
    document = await find_owned_feedback(collections["feedback"], feedback_id, user_id)
    if document is None:
        raise FeedbackNotFoundError
    if document.get("feedback_status") in {"withdrawn", "archived"}:
        raise FeedbackStateError("Withdrawn or archived feedback cannot be edited.")
    related = await validate_feedback_relationships(
        payload=payload,
        user_id=user_id,
        final_reports=collections["final_reports"],
        recommendation_reports=collections["recommendation_reports"],
        routine_reports=collections["routine_reports"],
    )
    for key in ("final_report_id", "recommendation_report_id", "routine_report_id", "upload_id"):
        if document.get(key) != related.get(key):
            raise FeedbackConflictError(
                "The related analysis report cannot be changed during editing."
            )
    if document.get("product_id") != payload.product_id:
        raise FeedbackConflictError("The related product cannot be changed during editing.")
    now = datetime.now(timezone.utc)
    payload_hash = feedback_payload_hash(payload, related)
    await enforce_submission_limits(
        collections["feedback"],
        user_id,
        payload_hash,
        settings,
        now,
        exclude_feedback_id=feedback_id,
    )
    old_reasons = set(document.get("selected_reasons", []))
    raw_texts = [
        payload.comment,
        payload.irritation_description,
        payload.morning_routine_feedback,
        payload.night_routine_feedback,
        payload.export_experience,
    ]
    moderation_status, moderation_reasons = assess_feedback_moderation(raw_texts)
    document.update(payload.model_dump(mode="python"))
    document.update(sanitize_feedback_fields(payload, settings.feedback_max_comment_length))
    document.update(
        {
            "feedback_status": "flagged" if moderation_status == "flagged" else "edited",
            "moderation_status": moderation_status,
            "moderation_reasons": moderation_reasons,
            "payload_hash": payload_hash,
            "updated_at": now,
        }
    )
    await replace_feedback(collections["feedback"], document)
    await sync_improvement_signals(collections["improvement_signals"], document, now, active=True)
    await sync_product_avoidance(collections["avoidances"], document, now, active=True)
    await rebuild_catalogue_signals(
        collections["feedback"],
        collections["catalogue_signals"],
        document.get("product_id"),
        old_reasons | set(document.get("selected_reasons", [])),
        now,
    )
    return feedback_document_to_response(document, include_acknowledgement=True)


async def withdraw_feedback(
    *, feedback_id: str, user_id: str, collections: dict[str, Any]
) -> FeedbackWithdrawalResponse:
    document = await find_owned_feedback(collections["feedback"], feedback_id, user_id)
    if document is None:
        raise FeedbackNotFoundError
    if document.get("feedback_status") == "withdrawn":
        raise FeedbackStateError("This feedback has already been withdrawn.")
    now = datetime.now(timezone.utc)
    document.update(
        {
            "feedback_status": "withdrawn",
            "withdrawn_at": now,
            "updated_at": now,
            "consent_for_analytics": False,
            "consent_for_research_review": False,
        }
    )
    await replace_feedback(collections["feedback"], document)
    await sync_improvement_signals(collections["improvement_signals"], document, now, active=False)
    await sync_product_avoidance(collections["avoidances"], document, now, active=False)
    await rebuild_catalogue_signals(
        collections["feedback"],
        collections["catalogue_signals"],
        document.get("product_id"),
        set(document.get("selected_reasons", [])),
        now,
    )
    return FeedbackWithdrawalResponse(
        feedback_id=feedback_id,
        feedback_status="withdrawn",
        withdrawn_at=now,
        message="Your feedback was withdrawn and removed from active analytics and improvement signals.",
    )


def feedback_options() -> FeedbackOptionsResponse:
    labels = {
        "analysis_feedback": "Analysis Result",
        "skin_type_feedback": "Skin Type",
        "skin_concern_feedback": "Visible Observation",
        "product_recommendation_feedback": "Product Recommendation",
        "product_experience_feedback": "Product Experience",
        "routine_feedback": "Skincare Routine",
        "report_feedback": "Final Report",
        "application_feedback": "Application Experience",
    }
    return FeedbackOptionsResponse(
        categories=[{"value": value, "label": label} for value, label in labels.items()],
        ratings=[
            {"value": value, "label": label}
            for value, label in enumerate(
                ("Very Poor", "Poor", "Acceptable", "Good", "Excellent"), start=1
            )
        ],
        reason_groups={
            "positive": list(POSITIVE_REASON_CODES),
            "negative": list(NEGATIVE_REASON_CODES),
            "product_experience": list(PRODUCT_EXPERIENCE_REASON_CODES),
        },
        values={
            "accuracy_perception": [
                "matches_experience",
                "partially_matches",
                "does_not_match",
                "not_sure",
            ],
            "user_assessment": ["helpful", "partially_helpful", "not_helpful", "not_sure"],
            "price_feedback": [
                "within_budget",
                "slightly_expensive",
                "too_expensive",
                "price_changed",
                "price_unknown",
            ],
            "availability_feedback": ["available", "limited", "unavailable", "not_checked"],
            "product_experience_status": [
                "used_once",
                "used_short_term",
                "used_longer_term",
                "stopped_using",
            ],
            "irritation_reported": [
                "no_issue",
                "mild_discomfort",
                "visible_irritation",
                "serious_reaction",
                "not_sure",
            ],
            "routine_difficulty": ["very_easy", "easy", "manageable", "difficult", "too_complex"],
            "report_length": ["too_short", "appropriate", "too_long"],
            "technical_detail_level": ["too_simple", "appropriate", "too_technical"],
        },
    )


async def get_owned_avoidance_responses(
    collection: Any, user_id: str
) -> ProductAvoidanceListResponse:
    documents = (
        await collection.find({"user_id": ObjectId(user_id), "is_active": True})
        .sort("updated_at", -1)
        .to_list(length=None)
    )
    return ProductAvoidanceListResponse(
        avoidances=[
            ProductAvoidanceResponse.model_validate(
                {key: item.get(key) for key in ProductAvoidanceResponse.model_fields}
            )
            for item in documents
        ]
    )


async def remove_owned_avoidance(collection: Any, user_id: str, product_id: str) -> None:
    document = await collection.find_one(
        {"user_id": ObjectId(user_id), "product_id": product_id, "is_active": True}
    )
    if document is None:
        raise FeedbackNotFoundError
    await collection.update_one(
        {"_id": document["_id"]},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
    )
