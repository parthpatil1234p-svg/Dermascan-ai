from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId

from app.schemas.product_eligibility import StoredProductEligibilityResult, UserFilteringContext

FILTER_ENGINE_VERSION = "1.0.0"
CATALOGUE_VERSION = "2026.08-demo"


def build_eligibility_report_document(
    *,
    upload_id: str,
    user_id: str,
    skin_profile: dict[str, Any],
    skin_type_report: dict[str, Any],
    concern_report: dict[str, Any],
    context: UserFilteringContext,
    results: list[StoredProductEligibilityResult],
    now: datetime,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    counts = {
        status: 0
        for status in ("eligible", "eligible_with_caution", "excluded", "insufficient_information")
    }
    summary_codes: dict[str, int] = {}
    for result in results:
        counts[result.eligibility_status] += 1
        for reason in result.hard_exclusions + result.cautions + result.information_gaps:
            summary_codes[reason.code] = summary_codes.get(reason.code, 0) + 1
    return {
        "eligibility_report_id": (
            existing["eligibility_report_id"] if existing else f"ELG-{uuid4().hex.upper()}"
        ),
        "upload_id": upload_id,
        "user_id": ObjectId(user_id),
        "skin_profile_id": str(skin_profile["_id"]),
        "skin_type_report_id": skin_type_report["skin_type_report_id"],
        "skin_concern_report_id": concern_report["skin_concern_report_id"],
        "catalogue_version": CATALOGUE_VERSION,
        "filter_engine_version": FILTER_ENGINE_VERSION,
        "user_filter_context": context.model_dump(mode="python"),
        "total_products_evaluated": len(results),
        "eligible_count": counts["eligible"],
        "eligible_with_caution_count": counts["eligible_with_caution"],
        "excluded_count": counts["excluded"],
        "insufficient_information_count": counts["insufficient_information"],
        "product_results": [result.model_dump(mode="python") for result in results],
        "summary_reasons": summary_codes,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }
