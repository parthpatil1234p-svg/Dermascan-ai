from datetime import datetime
from typing import Any

from bson import ObjectId

from app.schemas.final_report import (
    FinalReportGenerationResponse,
    FinalReportListItem,
    FinalReportResponse,
    IngredientGuidance,
    ProductRecommendationSnapshot,
)
from app.schemas.skincare_routine import RoutineAlternative, RoutineStep
from app.services.report_version_service import REPORT_GENERATOR_VERSION

REPORT_TITLE = "Personalized Skin Analysis and Skincare Guidance Report"
MEDICAL_DISCLAIMER = (
    "DermaScan AI provides general skincare guidance based on visible facial characteristics "
    "and user-provided information. It is not a medical diagnostic system, does not prescribe "
    "treatment, and does not replace advice from a qualified dermatologist."
)
SAFETY_GUIDANCE = [
    "Review the latest product label and follow the manufacturer instructions.",
    "Introduce new products gradually and consider patch testing; patch testing cannot guarantee safety.",
    "Do not use products that conflict with known allergies or selected avoidance preferences.",
    "Stop using a product if a serious reaction occurs and seek qualified professional guidance.",
    "Do not apply products to broken or infected skin without professional advice.",
    "Seek professional advice for severe, painful, infected, persistent, rapidly changing, or unusual skin concerns.",
    "Product prices and availability may change after this report is generated.",
]


def build_final_report_document(
    *,
    final_report_id: str,
    user_id: str,
    upload_id: str,
    report_version: int,
    report_status: str,
    source_report_ids: dict[str, str],
    source_versions: dict[str, str],
    source_fingerprint: str,
    summary: str,
    sections: dict[str, Any],
    limitations: list[str],
    model_versions: dict[str, str],
    engine_versions: dict[str, str],
    analysis_date: datetime,
    now: datetime,
    supersedes_report_id: str | None,
    analysis_mode: str = "model",
) -> dict[str, Any]:
    return {
        "final_report_id": final_report_id,
        "user_id": ObjectId(user_id),
        "upload_id": upload_id,
        "report_version": report_version,
        "report_status": report_status,
        "analysis_mode": analysis_mode,
        "source_report_ids": source_report_ids,
        "source_versions": source_versions,
        "source_fingerprint": source_fingerprint,
        "report_title": REPORT_TITLE,
        "summary": summary,
        "generated_at": now,
        "analysis_date": analysis_date,
        "sections_available": [
            key for key, value in sections.items() if value not in (None, [], {})
        ],
        "skin_profile_summary": sections.get("skin_profile", {}),
        "image_processing_summary": sections.get("image_processing", {}),
        "skin_type_summary": sections.get("skin_type", {}),
        "visible_concern_summary": sections.get(
            "visible_observations", {"observed": [], "possible": [], "uncertain": []}
        ),
        "ingredient_guidance": sections.get(
            "ingredient_guidance", {"potentially_relevant": [], "avoid_or_review": []}
        ),
        "product_recommendation_summary": sections.get("product_recommendations", []),
        "morning_routine": sections.get("morning_routine", []),
        "night_routine": sections.get("night_routine", []),
        "optional_products": sections.get("optional_products", []),
        "safety_guidance": SAFETY_GUIDANCE,
        "limitations": limitations,
        "medical_disclaimer": MEDICAL_DISCLAIMER,
        "data_freshness": sections.get("data_freshness", []),
        "model_versions": model_versions,
        "engine_versions": {**engine_versions, "report_generator": REPORT_GENERATOR_VERSION},
        "export_status": "not_exported",
        "supersedes_report_id": supersedes_report_id,
        "superseded_by_report_id": None,
        "is_archived": False,
        "archived_at": None,
        "created_at": now,
        "updated_at": now,
    }


def final_report_generation_response(document: dict[str, Any]) -> FinalReportGenerationResponse:
    report_id = document["final_report_id"]
    return FinalReportGenerationResponse(
        final_report_id=report_id,
        upload_id=document["upload_id"],
        report_version=document["report_version"],
        report_status=document["report_status"],
        analysis_mode=document.get("analysis_mode", "model"),
        title=document["report_title"],
        summary=document["summary"],
        generated_at=document["generated_at"],
        sections_available=document.get("sections_available", []),
        print_url=f"/reports/{report_id}/print",
        can_export_pdf=document["report_status"] in {"complete", "complete_with_limitations"},
    )


def final_report_document_to_response(document: dict[str, Any]) -> FinalReportResponse:
    base = final_report_generation_response(document).model_dump()
    return FinalReportResponse(
        **base,
        analysis_date=document["analysis_date"],
        skin_profile_summary=document.get("skin_profile_summary", {}),
        image_processing_summary=document.get("image_processing_summary", {}),
        skin_type_summary=document.get("skin_type_summary", {}),
        visible_concern_summary=document.get(
            "visible_concern_summary", {"observed": [], "possible": [], "uncertain": []}
        ),
        ingredient_guidance=IngredientGuidance.model_validate(
            document.get("ingredient_guidance", {})
        ),
        product_recommendations=[
            ProductRecommendationSnapshot.model_validate(item)
            for item in document.get("product_recommendation_summary", [])
        ],
        morning_routine=[
            RoutineStep.model_validate(item) for item in document.get("morning_routine", [])
        ],
        night_routine=[
            RoutineStep.model_validate(item) for item in document.get("night_routine", [])
        ],
        optional_products=[
            RoutineAlternative.model_validate(item)
            for item in document.get("optional_products", [])
        ],
        safety_guidance=document.get("safety_guidance", SAFETY_GUIDANCE),
        limitations=document.get("limitations", []),
        medical_disclaimer=document["medical_disclaimer"],
        data_freshness=document.get("data_freshness", []),
        model_versions=document.get("model_versions", {}),
        engine_versions=document.get("engine_versions", {}),
        source_report_ids=document.get("source_report_ids", {}),
        source_versions=document.get("source_versions", {}),
        supersedes_report_id=document.get("supersedes_report_id"),
        superseded_by_report_id=document.get("superseded_by_report_id"),
        is_archived=bool(document.get("is_archived", False)),
        archived_at=document.get("archived_at"),
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )


def final_report_list_item(document: dict[str, Any]) -> FinalReportListItem:
    observations = document.get("visible_concern_summary", {}).get("observed", [])
    return FinalReportListItem(
        final_report_id=document["final_report_id"],
        report_version=document["report_version"],
        report_status=document["report_status"],
        analysis_date=document["analysis_date"],
        generated_at=document["generated_at"],
        skin_type=document.get("skin_type_summary", {}).get("skin_type", "Unavailable"),
        main_visible_observations=[
            item.get("name", "Visible observation") for item in observations[:3]
        ],
        routine_status=(
            "available"
            if document.get("morning_routine") or document.get("night_routine")
            else "unavailable"
        ),
        is_archived=bool(document.get("is_archived", False)),
    )
