from datetime import datetime, timezone
from typing import Any

from app.models.skincare_routine import build_routine_document
from app.repositories.recommendation_repository import find_recommendation_report
from app.repositories.skincare_routine_repository import find_owned_routine, upsert_routine
from app.schemas.product_recommendation import StoredRecommendation
from app.schemas.skincare_routine import RoutineAlternative, RoutineStep
from app.services.upload_service import get_owned_upload_document


class RoutineUploadNotFoundError(Exception):
    pass


class RoutineReportNotFoundError(Exception):
    pass


class RoutinePrerequisiteError(Exception):
    pass


class RoutineGenerationError(Exception):
    pass


PURPOSES = {
    "cleanser": "Remove surface oil, sunscreen, and daily residue gently.",
    "serum": "Provide an optional focused support step based on the available recommendation evidence.",
    "moisturizer": "Support hydration and the skin barrier.",
    "sunscreen": "Support daily protection from ultraviolet exposure.",
}
GUIDANCE = {
    "cleanser": "Use as directed on the current product label and rinse gently.",
    "serum": "Introduce gradually and follow the product label; skip if irritation occurs.",
    "moisturizer": "Apply as directed after lighter products.",
    "sunscreen": "Use in the morning as directed and reapply according to the product label.",
}


def _step(item: StoredRecommendation, number: int, *, optional: bool = False) -> RoutineStep:
    return RoutineStep(
        step_number=number,
        category=item.category,
        product_id=item.product_id,
        product_name=item.product_name,
        brand_name=item.brand_name,
        purpose=PURPOSES[item.category],
        usage_guidance=GUIDANCE[item.category],
        why_selected=item.why_recommended,
        cautions=item.caution_factors,
        is_optional=optional,
        is_demo_product=item.is_demo_product,
    )


def build_routines(
    recommendations: list[StoredRecommendation],
) -> tuple[list[RoutineStep], list[RoutineStep], list[RoutineAlternative], list[str]]:
    ranked = sorted(recommendations, key=lambda item: item.overall_rank or 10_000)
    by_category: dict[str, list[StoredRecommendation]] = {}
    for item in ranked:
        if item.eligibility_status not in {"eligible", "eligible_with_caution"}:
            raise RoutinePrerequisiteError(
                "The recommendation report contains an ineligible product."
            )
        by_category.setdefault(item.category, []).append(item)

    warnings: list[str] = []
    for category in ("cleanser", "moisturizer", "sunscreen"):
        if not by_category.get(category):
            warnings.append(f"No qualifying {category} was available in the recommendation report.")

    morning_items = [
        by_category[c][0] for c in ("cleanser", "moisturizer", "sunscreen") if by_category.get(c)
    ]
    night_items = [by_category["cleanser"][0]] if by_category.get("cleanser") else []
    if by_category.get("serum"):
        night_items.append(by_category["serum"][0])
    if by_category.get("moisturizer"):
        night_items.append(by_category["moisturizer"][0])

    morning = [_step(item, index + 1) for index, item in enumerate(morning_items)]
    night = [
        _step(item, index + 1, optional=item.category == "serum")
        for index, item in enumerate(night_items)
    ]
    used = {item.product_id for item in morning_items + night_items}
    alternatives = [
        RoutineAlternative(
            category=item.category,
            product_id=item.product_id,
            product_name=item.product_name,
            brand_name=item.brand_name,
            guidance="Alternative option; use instead of the primary product in this category.",
            cautions=item.caution_factors,
            is_demo_product=item.is_demo_product,
        )
        for item in ranked
        if item.product_id not in used
    ]
    return morning, night, alternatives, warnings


async def generate_owned_routine(
    *,
    upload_id: str,
    user_id: str,
    uploads: Any,
    recommendation_reports: Any,
    routine_reports: Any,
) -> dict[str, Any]:
    upload = await get_owned_upload_document(uploads, upload_id, user_id)
    if upload is None:
        raise RoutineUploadNotFoundError
    if upload.get("status") == "routine_generating":
        raise RoutinePrerequisiteError("Routine generation is already running.")
    allowed = {
        "routine_generation_pending",
        "routine_completed",
        "routine_completed_with_limitations",
        "final_report_pending",
        "final_report_incomplete",
        "final_report_failed",
    }
    if upload.get("status") not in allowed:
        raise RoutinePrerequisiteError(
            "Complete product recommendation scoring before generating a routine."
        )
    recommendation = await find_recommendation_report(recommendation_reports, upload_id, user_id)
    if recommendation is None or not recommendation.get("recommendations"):
        raise RoutinePrerequisiteError("A completed product recommendation report is required.")
    existing = await find_owned_routine(routine_reports, upload_id, user_id)
    await uploads.update_one({"_id": upload["_id"]}, {"$set": {"status": "routine_generating"}})
    try:
        items = [
            StoredRecommendation.model_validate(item) for item in recommendation["recommendations"]
        ]
        morning, night, alternatives, warnings = build_routines(items)
        now = datetime.now(timezone.utc)
        document = build_routine_document(
            upload_id=upload_id,
            user_id=user_id,
            recommendation_report_id=recommendation["recommendation_report_id"],
            morning=morning,
            night=night,
            optional_products=alternatives,
            warnings=warnings,
            now=now,
            existing=existing,
        )
        await upsert_routine(routine_reports, document)
        await uploads.update_one(
            {"_id": upload["_id"]}, {"$set": {"status": "final_report_pending", "updated_at": now}}
        )
        return document
    except RoutinePrerequisiteError:
        raise
    except Exception as exc:
        await uploads.update_one(
            {"_id": upload["_id"]}, {"$set": {"status": "routine_generation_failed"}}
        )
        raise RoutineGenerationError from exc


async def get_owned_routine(collection: Any, upload_id: str, user_id: str) -> dict[str, Any]:
    document = await find_owned_routine(collection, upload_id, user_id)
    if document is None:
        raise RoutineReportNotFoundError
    return document
