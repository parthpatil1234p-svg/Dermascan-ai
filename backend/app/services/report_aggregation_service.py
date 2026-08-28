from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.schemas.final_report import ProductRecommendationSnapshot
from app.schemas.product_recommendation import StoredRecommendation
from app.services.ingredient_guidance_service import build_ingredient_guidance

SOURCE_ID_FIELDS = {
    "image_quality": "quality_report_id",
    "face_detection": "face_report_id",
    "image_preprocessing": "preprocessing_report_id",
    "skin_type": "skin_type_report_id",
    "skin_concern": "skin_concern_report_id",
    "product_eligibility": "eligibility_report_id",
    "product_recommendation": "recommendation_report_id",
    "skincare_routine": "routine_report_id",
}


async def load_source_reports(
    *,
    upload_id: str,
    user_id: str,
    collections: dict[str, Any],
) -> dict[str, dict[str, Any] | None]:
    owner = ObjectId(user_id)
    sources: dict[str, dict[str, Any] | None] = {
        "skin_profile": await collections["skin_profile"].find_one({"user_id": owner}),
        "image_upload": await collections["image_upload"].find_one(
            {"upload_id": upload_id, "user_id": owner}
        ),
    }
    for key in SOURCE_ID_FIELDS:
        sources[key] = await collections[key].find_one({"upload_id": upload_id, "user_id": owner})
    return sources


def source_metadata(
    sources: dict[str, dict[str, Any] | None],
) -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]:
    ids = {
        key: str(document[field])
        for key, field in SOURCE_ID_FIELDS.items()
        if (document := sources.get(key)) and document.get(field)
    }
    versions = {
        key: str(
            document.get("created_at")
            if key == "image_upload"
            else document.get("updated_at", document.get("created_at", "1"))
        )
        for key, document in sources.items()
        if document
    }
    skin = sources.get("skin_type") or {}
    concern = sources.get("skin_concern") or {}
    recommendation = sources.get("product_recommendation") or {}
    routine = sources.get("skincare_routine") or {}
    model_versions = {
        key: value
        for key, value in {
            "skin_type": skin.get("model_version"),
            "visible_concerns": concern.get("model_version"),
        }.items()
        if value
    }
    engine_versions = {
        key: value
        for key, value in {
            "recommendation": recommendation.get("scoring_engine_version"),
            "routine": routine.get("routine_engine_version"),
        }.items()
        if value
    }
    return ids, versions, model_versions, engine_versions


def _profile_summary(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "age_group": profile.get("age_group"),
        "country": profile.get("country"),
        "oiliness_level": profile.get("oiliness_level"),
        "dryness_level": profile.get("dryness_level"),
        "self_reported_sensitivity": profile.get("is_sensitive"),
        "known_allergies": profile.get("known_allergies", []),
        "ingredients_to_avoid": profile.get("ingredients_to_avoid", []),
        "fragrance_preference": profile.get("fragrance_preference"),
        "budget": {
            "minimum": profile.get("budget_min"),
            "maximum": profile.get("budget_max"),
            "currency": "INR",
        },
        "experience_level": profile.get("experience_level"),
    }


def _image_summary(sources: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    upload = sources["image_upload"] or {}
    quality = sources["image_quality"] or {}
    face = sources["face_detection"] or {}
    prep = sources["image_preprocessing"] or {}
    return {
        "image_uploaded": bool(upload),
        "consent_confirmed": bool(upload.get("consent_given")),
        "image_quality_status": quality.get("quality_status"),
        "quality_score": quality.get("quality_score"),
        "quality_warning_accepted": bool(quality.get("warning_accepted")),
        "face_count": face.get("face_count"),
        "face_detection_status": face.get("detection_status"),
        "face_warning_accepted": bool(face.get("warning_accepted")),
        "preprocessing_status": prep.get("preprocessing_status"),
        "model_input_ready": prep.get("preprocessing_status") in {"completed", "warning"},
    }


def _skin_type_summary(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "analysis_mode": document.get("analysis_mode", "model"),
        "skin_type": document.get("final_skin_type", "Uncertain"),
        "result_status": document.get("result_status"),
        "confidence_level": str(document.get("confidence_level", "low")).title(),
        "model_confidence": round(float(document.get("model_confidence", 0)) * 100),
        "questionnaire_agreement": str(document.get("agreement_status", "insufficient")).title(),
        "self_reported_sensitivity": document.get("self_reported_sensitivity"),
        "explanation": document.get("explanation", ""),
        "limitations": ["Lighting and camera quality can affect this broad estimate."],
    }


def _concern_summary(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {"observed": [], "possible": [], "uncertain": []}
    for item in document.get("concern_results", []):
        status = item.get("status")
        if status not in groups:
            continue
        groups[status].append(
            {
                "code": item.get("concern_code"),
                "name": item.get("display_name"),
                "status": status,
                "visible_severity": item.get("visible_severity"),
                "confidence": round(float(item.get("score", 0)) * 100),
                "regions": item.get("regions", []),
                "explanation": item.get("explanation", ""),
            }
        )
    return groups


def analysis_mode(sources: dict[str, dict[str, Any] | None]) -> str:
    modes = {
        (sources.get(name) or {}).get("analysis_mode", "model")
        for name in ("skin_type", "skin_concern")
    }
    return "demonstration" if "demonstration" in modes else "model"


async def _product_snapshots(recommendation: dict[str, Any], products: Any) -> list[dict[str, Any]]:
    items = [
        StoredRecommendation.model_validate(item)
        for item in recommendation.get("recommendations", [])
    ]
    ids = [item.product_id for item in items]
    documents = (
        await products.find({"product_id": {"$in": ids}}).to_list(length=None) if ids else []
    )
    lookup = {item["product_id"]: item for item in documents}
    snapshots: list[ProductRecommendationSnapshot] = []
    for item in sorted(items, key=lambda value: value.overall_rank or 10_000):
        source = lookup.get(item.product_id, {})
        snapshots.append(
            ProductRecommendationSnapshot(
                rank=item.rank_within_category or 0,
                product_id=item.product_id,
                product_name=item.product_name,
                brand_name=item.brand_name,
                category=item.category,
                score=round(item.final_score, 2),
                score_band=item.score_band,
                why_recommended=item.why_recommended,
                cautions=item.caution_factors,
                price_at_report_time=source.get("price", item.price),
                price_checked_at=source.get("price_checked_at"),
                availability_at_report_time=source.get(
                    "availability_status", item.availability_status
                ),
                availability_checked_at=source.get("availability_checked_at"),
                source_verified_at=source.get("source_verified_at"),
                source_status=source.get("data_type", "snapshot_from_recommendation"),
                demo_status=item.is_demo_product,
            )
        )
    return [item.model_dump(mode="python") for item in snapshots]


async def aggregate_sections(
    sources: dict[str, dict[str, Any] | None], products: Any
) -> dict[str, Any]:
    sections: dict[str, Any] = {}
    profile = sources.get("skin_profile")
    skin = sources.get("skin_type")
    concerns = sources.get("skin_concern")
    recommendations = sources.get("product_recommendation")
    routine = sources.get("skincare_routine")
    if profile:
        sections["skin_profile"] = _profile_summary(profile)
    if sources.get("image_upload"):
        sections["image_processing"] = _image_summary(sources)
    if skin:
        sections["skin_type"] = _skin_type_summary(skin)
    if concerns:
        sections["visible_observations"] = _concern_summary(concerns)
    if profile:
        sections["ingredient_guidance"] = build_ingredient_guidance(
            profile, skin, concerns
        ).model_dump(mode="python")
    if recommendations:
        snapshots = await _product_snapshots(recommendations, products)
        sections["product_recommendations"] = snapshots
        sections["data_freshness"] = [
            {
                "product_id": item["product_id"],
                "price_checked_at": item.get("price_checked_at"),
                "availability_checked_at": item.get("availability_checked_at"),
                "source_verified_at": item.get("source_verified_at"),
                "report_generated_at": datetime.now(timezone.utc),
            }
            for item in snapshots
        ]
    if routine:
        sections["morning_routine"] = routine.get("morning_routine", [])
        sections["night_routine"] = routine.get("night_routine", [])
        sections["optional_products"] = routine.get("optional_products", [])
    return sections
