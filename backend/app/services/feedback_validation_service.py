from typing import Any

from bson import ObjectId

from app.schemas.feedback import FeedbackPayload


class FeedbackRelationshipError(Exception):
    pass


async def validate_feedback_relationships(
    *,
    payload: FeedbackPayload,
    user_id: str,
    final_reports: Any,
    recommendation_reports: Any,
    routine_reports: Any,
) -> dict[str, Any]:
    owner = ObjectId(user_id)
    related: dict[str, Any] = {
        "final_report_id": None,
        "recommendation_report_id": None,
        "routine_report_id": None,
        "upload_id": None,
        "product_name": None,
    }
    final_report = None
    recommendation = None
    routine = None
    if payload.final_report_id:
        final_report = await final_reports.find_one(
            {"final_report_id": payload.final_report_id, "user_id": owner}
        )
        if final_report is None:
            raise FeedbackRelationshipError("Related final report not found.")
        source_ids = final_report.get("source_report_ids", {})
        related.update(
            {
                "final_report_id": final_report["final_report_id"],
                "recommendation_report_id": source_ids.get("product_recommendation"),
                "routine_report_id": source_ids.get("skincare_routine"),
                "upload_id": final_report.get("upload_id"),
            }
        )
    if payload.recommendation_report_id:
        recommendation = await recommendation_reports.find_one(
            {
                "recommendation_report_id": payload.recommendation_report_id,
                "user_id": owner,
            }
        )
        if recommendation is None:
            raise FeedbackRelationshipError("Related recommendation report not found.")
        if related["upload_id"] and related["upload_id"] != recommendation.get("upload_id"):
            raise FeedbackRelationshipError(
                "The related reports do not belong to the same analysis."
            )
        related["recommendation_report_id"] = recommendation["recommendation_report_id"]
        related["upload_id"] = recommendation.get("upload_id")
    if payload.routine_report_id:
        routine = await routine_reports.find_one(
            {"routine_report_id": payload.routine_report_id, "user_id": owner}
        )
        if routine is None:
            raise FeedbackRelationshipError("Related routine report not found.")
        if related["upload_id"] and related["upload_id"] != routine.get("upload_id"):
            raise FeedbackRelationshipError(
                "The related reports do not belong to the same analysis."
            )
        related["routine_report_id"] = routine["routine_report_id"]
        related["upload_id"] = routine.get("upload_id")

    if payload.product_id:
        products = (
            final_report.get("product_recommendation_summary", [])
            if final_report
            else recommendation.get("recommendations", []) if recommendation else []
        )
        product = next(
            (item for item in products if item.get("product_id") == payload.product_id), None
        )
        if product is None:
            raise FeedbackRelationshipError(
                "The selected product is not part of the related recommendation report."
            )
        related["product_name"] = product.get("product_name")

    if payload.concern_code:
        observations = []
        for values in (final_report or {}).get("visible_concern_summary", {}).values():
            observations.extend(values if isinstance(values, list) else [])
        if not any(item.get("code") == payload.concern_code for item in observations):
            raise FeedbackRelationshipError(
                "The selected visible observation is not part of the related final report."
            )
    return related
