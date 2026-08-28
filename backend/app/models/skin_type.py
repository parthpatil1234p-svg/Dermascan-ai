from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId

from app.schemas.skin_type import SkinTypeResponse

LIMITATIONS = [
    "Lighting and camera quality can affect the result.",
    "Skin sensitivity is based on your questionnaire and is not diagnosed from the image.",
    "This estimate is general skincare guidance, not a medical diagnosis.",
]


def build_skin_type_document(
    *,
    upload_id: str,
    user_id: str,
    preprocessing_report_id: str,
    bundle: Any,
    prediction: Any,
    evidence: Any,
    fused: Any,
    now: datetime,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "skin_type_report_id": existing["skin_type_report_id"] if existing else str(uuid4()),
        "upload_id": upload_id,
        "user_id": ObjectId(user_id),
        "preprocessing_report_id": preprocessing_report_id,
        "model_name": bundle.metadata["model_name"],
        "model_version": bundle.metadata["model_version"],
        "analysis_mode": bundle.metadata.get("analysis_mode", "model"),
        "model_prediction": prediction.top_class,
        "model_confidence": prediction.top_confidence,
        "second_prediction": prediction.second_class,
        "second_confidence": prediction.second_confidence,
        "confidence_margin": prediction.margin,
        "confidence_level": prediction.confidence_level,
        "class_probabilities": prediction.probabilities,
        "questionnaire_oiliness": evidence.oiliness_level,
        "questionnaire_dryness": evidence.dryness_level,
        "self_reported_sensitivity": evidence.self_reported_sensitivity,
        "agreement_status": fused.agreement,
        "final_skin_type": fused.final_skin_type,
        "result_status": fused.result_status,
        "explanation": fused.explanation,
        "issues": fused.issues,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }


def skin_type_document_to_response(document: dict[str, Any]) -> SkinTypeResponse:
    probabilities = {
        label.title(): int(round(value * 100))
        for label, value in document["class_probabilities"].items()
    }
    return SkinTypeResponse(
        skin_type_report_id=document["skin_type_report_id"],
        upload_id=document["upload_id"],
        analysis_mode=document.get("analysis_mode", "model"),
        result_status=document["result_status"],
        skin_type=document["final_skin_type"],
        confidence=int(round(document["model_confidence"] * 100)),
        confidence_level=document["confidence_level"].title(),
        agreement=document["agreement_status"].title(),
        self_reported_sensitivity=document["self_reported_sensitivity"],
        probabilities=probabilities,
        explanation=document["explanation"],
        limitations=LIMITATIONS,
        issues=document.get("issues", []),
        can_continue=True,
        next_route="/skin-concern-analysis",
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
