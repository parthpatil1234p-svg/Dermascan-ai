from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId

CATALOGUE_REASON_SIGNALS = {
    "PRODUCT_PRICE_CHANGED": "price_changed",
    "PRODUCT_UNAVAILABLE": "product_unavailable",
    "PRODUCT_LABEL_DIFFERENT_FROM_CATALOGUE": "label_changed",
}
IRRITATION_VALUES = {"mild_discomfort", "visible_irritation", "serious_reaction"}


def improvement_signal_types(document: dict[str, Any]) -> list[str]:
    reasons = set(document.get("selected_reasons", []))
    signals: list[str] = []
    if (
        reasons & {"TOO_MANY_ROUTINE_STEPS", "ROUTINE_TOO_COMPLEX"}
        or document.get("routine_difficulty") == "too_complex"
    ):
        signals.append("USER_PREFERS_SIMPLER_ROUTINE")
    if "PRODUCT_TOO_EXPENSIVE" in reasons or document.get("price_feedback") == "too_expensive":
        signals.append("USER_REJECTS_EXPENSIVE_PRODUCTS")
    if "PRODUCT_NOT_AVAILABLE" in reasons or document.get("availability_feedback") == "unavailable":
        signals.append("USER_REPORTS_PRODUCT_UNAVAILABLE")
    if document.get("accuracy_perception") == "does_not_match":
        signals.append("USER_SKIN_TYPE_RESULT_DISAGREEMENT")
    if document.get("exclude_product_from_future_recommendations"):
        signals.append("USER_REPORTS_PRODUCT_AVOIDANCE")
    return list(dict.fromkeys(signals))


async def sync_improvement_signals(
    collection: Any, document: dict[str, Any], now: datetime, *, active: bool
) -> None:
    existing = await collection.find({"source_feedback_id": document["feedback_id"]}).to_list(
        length=None
    )
    for item in existing:
        await collection.update_one(
            {"_id": item["_id"]}, {"$set": {"is_active": False, "updated_at": now}}
        )
    if not active:
        return
    for signal_type in improvement_signal_types(document):
        previous = next((item for item in existing if item["signal_type"] == signal_type), None)
        payload = {
            "signal_id": previous["signal_id"] if previous else f"RIS-{uuid4().hex[:10].upper()}",
            "user_id": document["user_id"],
            "product_id": document.get("product_id"),
            "signal_type": signal_type,
            "source_feedback_id": document["feedback_id"],
            "is_active": True,
            "created_at": previous["created_at"] if previous else now,
            "updated_at": now,
        }
        if previous:
            payload["_id"] = previous["_id"]
            await collection.replace_one({"_id": previous["_id"]}, payload)
        else:
            await collection.insert_one(payload)


async def sync_product_avoidance(
    collection: Any, document: dict[str, Any], now: datetime, *, active: bool
) -> None:
    product_id = document.get("product_id")
    if not product_id:
        return
    existing = await collection.find_one({"user_id": document["user_id"], "product_id": product_id})
    should_avoid = (
        active
        and bool(document.get("exclude_product_from_future_recommendations"))
        and document.get("irritation_reported") in IRRITATION_VALUES
    )
    if not should_avoid:
        if existing and existing.get("source_feedback_id") == document["feedback_id"]:
            await collection.update_one(
                {"_id": existing["_id"]}, {"$set": {"is_active": False, "updated_at": now}}
            )
        return
    payload = {
        "user_id": document["user_id"],
        "product_id": product_id,
        "product_name": document.get("product_name"),
        "avoidance_reason": "USER_REPORTED_PRODUCT_AVOIDANCE",
        "source_feedback_id": document["feedback_id"],
        "is_active": True,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }
    if existing:
        payload["_id"] = existing["_id"]
        await collection.replace_one({"_id": existing["_id"]}, payload)
    else:
        await collection.insert_one(payload)


async def rebuild_catalogue_signals(
    feedback_collection: Any,
    signal_collection: Any,
    product_id: str | None,
    reason_codes: set[str],
    now: datetime,
) -> None:
    if not product_id:
        return
    for reason_code in reason_codes & set(CATALOGUE_REASON_SIGNALS):
        signal_type = CATALOGUE_REASON_SIGNALS[reason_code]
        reports = await feedback_collection.find(
            {
                "product_id": product_id,
                "feedback_status": {"$in": ["active", "edited", "flagged"]},
                "selected_reasons": reason_code,
            }
        ).to_list(length=None)
        existing = await signal_collection.find_one(
            {"product_id": product_id, "signal_type": signal_type}
        )
        payload = {
            "signal_id": existing["signal_id"] if existing else f"CRS-{uuid4().hex[:10].upper()}",
            "product_id": product_id,
            "signal_type": signal_type,
            "feedback_count": len(reports),
            "first_reported_at": min((item["created_at"] for item in reports), default=now),
            "last_reported_at": max((item["updated_at"] for item in reports), default=now),
            "review_status": existing.get("review_status", "pending") if existing else "pending",
            "reviewed_at": existing.get("reviewed_at") if existing else None,
            "resolution_notes": existing.get("resolution_notes") if existing else None,
            "updated_at": now,
        }
        if existing:
            payload["_id"] = existing["_id"]
            await signal_collection.replace_one({"_id": existing["_id"]}, payload)
        else:
            await signal_collection.insert_one(payload)


async def list_owned_avoidances(collection: Any, user_id: str) -> list[dict[str, Any]]:
    return (
        await collection.find({"user_id": ObjectId(user_id), "is_active": True})
        .sort("updated_at", -1)
        .to_list(length=None)
    )
