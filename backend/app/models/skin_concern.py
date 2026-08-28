from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId

from app.schemas.skin_concern import ConcernObservationResponse, SkinConcernResponse

REPORT_LIMITATIONS = [
    "Lighting, camera quality, makeup, and image processing can affect visible characteristics.",
    "The global model does not provide medically validated localization.",
    "These are general visual observations and not medical diagnoses.",
]


def build_skin_concern_document(
    *,
    upload_id: str,
    user_id: str,
    preprocessing_report_id: str,
    skin_type_report_id: str,
    bundle: Any,
    scores: dict[str, float],
    results: list[Any],
    region_context: Any,
    overall_status: str,
    now: datetime,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "skin_concern_report_id": (
            existing["skin_concern_report_id"] if existing else str(uuid4())
        ),
        "upload_id": upload_id,
        "user_id": ObjectId(user_id),
        "preprocessing_report_id": preprocessing_report_id,
        "skin_type_report_id": skin_type_report_id,
        "model_name": bundle.metadata["model_name"],
        "model_version": bundle.metadata["model_version"],
        "analysis_mode": bundle.metadata.get("analysis_mode", "model"),
        "model_scores": scores,
        "thresholds": bundle.thresholds,
        "thresholds_calibrated": bundle.thresholds_calibrated,
        "concern_results": [result.__dict__ for result in results],
        "region_results": {
            "precise_regions_available": region_context.precise_regions_available,
            "available_regions": list(region_context.available_regions),
        },
        "questionnaire_comparison": {
            result.concern_code: {
                "agreement": result.questionnaire_agreement,
                "reported_value": result.questionnaire_reported_value,
                "explanation": result.questionnaire_explanation,
            }
            for result in results
        },
        "overall_status": overall_status,
        "issues": [region_context.issue_code] if region_context.issue_code else [],
        "limitations": REPORT_LIMITATIONS,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }


def _public_observation(result: dict[str, Any]) -> ConcernObservationResponse:
    return ConcernObservationResponse(
        code=result["concern_code"],
        name=result["display_name"],
        status=result["status"],
        visible_severity=result["visible_severity"],
        confidence=int(round(result["score"] * 100)),
        regions=result["regions"],
        explanation=result["explanation"],
        questionnaire_agreement=result["questionnaire_agreement"],
        questionnaire_reported_value=result.get("questionnaire_reported_value"),
        questionnaire_explanation=result["questionnaire_explanation"],
        limitations=result["limitations"],
    )


def skin_concern_document_to_response(document: dict[str, Any]) -> SkinConcernResponse:
    observations = [
        _public_observation(result)
        for result in document["concern_results"]
        if result["status"] in {"observed", "possible"}
    ]
    uncertain = [
        _public_observation(result)
        for result in document["concern_results"]
        if result["status"] == "uncertain"
    ]
    return SkinConcernResponse(
        skin_concern_report_id=document["skin_concern_report_id"],
        upload_id=document["upload_id"],
        analysis_mode=document.get("analysis_mode", "model"),
        overall_status=document["overall_status"],
        observations=observations,
        uncertain_observations=uncertain,
        region_information_available=document["region_results"]["precise_regions_available"],
        issues=document.get("issues", []),
        limitations=document.get("limitations", REPORT_LIMITATIONS),
        can_continue=document["overall_status"] != "failed",
        next_route="/product-eligibility",
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
