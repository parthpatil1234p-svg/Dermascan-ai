from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId

from app.schemas.skincare_routine import (
    RoutineAlternative,
    RoutineStep,
    SkincareRoutineResponse,
)

ROUTINE_ENGINE_VERSION = "1.0.0"
ROUTINE_LIMITATIONS = [
    "The routine uses the available recommendation catalogue and may omit a category.",
    "Product instructions and formulas can change; review the current label before use.",
    "This routine is general skincare guidance, not a medical prescription.",
]


def build_routine_document(
    *,
    upload_id: str,
    user_id: str,
    recommendation_report_id: str,
    morning: list[RoutineStep],
    night: list[RoutineStep],
    optional_products: list[RoutineAlternative],
    warnings: list[str],
    now: datetime,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "routine_report_id": (
            existing["routine_report_id"] if existing else f"RTN-{uuid4().hex.upper()}"
        ),
        "user_id": ObjectId(user_id),
        "upload_id": upload_id,
        "recommendation_report_id": recommendation_report_id,
        "routine_engine_version": ROUTINE_ENGINE_VERSION,
        "routine_status": "completed_with_limitations" if warnings else "completed",
        "morning_routine": [item.model_dump(mode="python") for item in morning],
        "night_routine": [item.model_dump(mode="python") for item in night],
        "optional_products": [item.model_dump(mode="python") for item in optional_products],
        "warnings": warnings,
        "limitations": ROUTINE_LIMITATIONS,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }


def routine_document_to_response(document: dict[str, Any]) -> SkincareRoutineResponse:
    return SkincareRoutineResponse(
        routine_report_id=document["routine_report_id"],
        upload_id=document["upload_id"],
        routine_status=document["routine_status"],
        morning_routine=[RoutineStep.model_validate(item) for item in document["morning_routine"]],
        night_routine=[RoutineStep.model_validate(item) for item in document["night_routine"]],
        optional_products=[
            RoutineAlternative.model_validate(item)
            for item in document.get("optional_products", [])
        ],
        warnings=document.get("warnings", []),
        limitations=document.get("limitations", ROUTINE_LIMITATIONS),
        routine_engine_version=document["routine_engine_version"],
        can_continue=True,
        next_route="/final-report",
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
