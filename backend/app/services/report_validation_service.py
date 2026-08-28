from typing import Any

from bson import ObjectId


class ReportRelationshipError(Exception):
    pass


REQUIRED_SOURCES = (
    "skin_profile",
    "image_upload",
    "image_quality",
    "face_detection",
    "image_preprocessing",
    "skin_type",
    "skin_concern",
    "product_eligibility",
    "product_recommendation",
    "skincare_routine",
)


def missing_required_sources(sources: dict[str, dict[str, Any] | None]) -> list[str]:
    missing = [name for name in REQUIRED_SOURCES if sources.get(name) is None]
    version_fields = {
        "skin_type": "model_version",
        "skin_concern": "model_version",
        "product_recommendation": "scoring_engine_version",
        "skincare_routine": "routine_engine_version",
    }
    for source, field in version_fields.items():
        document = sources.get(source)
        if document is not None and not document.get(field):
            missing.append(f"{source}_{field}")
    return missing


def validate_source_relationships(
    sources: dict[str, dict[str, Any] | None],
    user_id: str,
    upload_id: str,
) -> None:
    owner = ObjectId(user_id)
    for name, document in sources.items():
        if document is None:
            continue
        if document.get("user_id") != owner:
            raise ReportRelationshipError(
                f"The {name.replace('_', ' ')} report ownership is inconsistent."
            )
        if name != "skin_profile" and document.get("upload_id") != upload_id:
            raise ReportRelationshipError(
                f"The {name.replace('_', ' ')} report belongs to a different workflow."
            )

    upload = sources.get("image_upload")
    if upload and not upload.get("consent_given"):
        raise ReportRelationshipError("Facial-image processing consent was not recorded.")
    quality = sources.get("image_quality")
    face = sources.get("face_detection")
    prep = sources.get("image_preprocessing")
    skin = sources.get("skin_type")
    concerns = sources.get("skin_concern")
    eligibility = sources.get("product_eligibility")
    recommendations = sources.get("product_recommendation")
    routine = sources.get("skincare_routine")
    links = [
        (face, "quality_report_id", quality, "quality_report_id"),
        (prep, "face_report_id", face, "face_report_id"),
        (prep, "quality_report_id", quality, "quality_report_id"),
        (skin, "preprocessing_report_id", prep, "preprocessing_report_id"),
        (concerns, "skin_type_report_id", skin, "skin_type_report_id"),
        (recommendations, "eligibility_report_id", eligibility, "eligibility_report_id"),
        (routine, "recommendation_report_id", recommendations, "recommendation_report_id"),
    ]
    for child, child_key, parent, parent_key in links:
        if child and parent and child.get(child_key) != parent.get(parent_key):
            raise ReportRelationshipError("Required source report relationships are inconsistent.")

    if recommendations and routine:
        eligible_ids = {
            item["product_id"]
            for item in recommendations.get("recommendations", [])
            if item.get("eligibility_status") in {"eligible", "eligible_with_caution"}
        }
        routine_ids = {
            item["product_id"]
            for key in ("morning_routine", "night_routine", "optional_products")
            for item in routine.get(key, [])
        }
        if not routine_ids.issubset(eligible_ids):
            raise ReportRelationshipError(
                "The routine contains a product outside the recommendation report."
            )


def determine_report_status(
    sources: dict[str, dict[str, Any] | None], missing: list[str]
) -> tuple[str, list[str]]:
    if missing:
        return "incomplete", [
            f"Missing required section: {name.replace('_', ' ')}." for name in missing
        ]
    limitations: list[str] = []
    quality = sources["image_quality"]
    face = sources["face_detection"]
    skin = sources["skin_type"]
    concerns = sources["skin_concern"]
    recommendations = sources["product_recommendation"]
    routine = sources["skincare_routine"]
    if quality.get("quality_status") == "warning":
        limitations.append("The image-quality warning was accepted before continuing.")
    if face.get("detection_status") == "warning":
        limitations.append("The face-detection warning was accepted before continuing.")
    if skin.get("result_status") == "uncertain":
        limitations.append("The broad skin-type estimate was uncertain.")
    if concerns.get("overall_status") == "completed_with_uncertainty":
        limitations.append("One or more visible observations were uncertain.")
    if any(
        (sources.get(name) or {}).get("analysis_mode") == "demonstration"
        for name in ("skin_type", "skin_concern")
    ):
        limitations.append(
            "Demonstration Mode used deterministic mock outputs, not trained-model inference."
        )
    limitations.extend(recommendations.get("limitations", []))
    limitations.extend(routine.get("warnings", []))
    freshness_values = [
        value
        for item in recommendations.get("recommendations", [])
        for value in item.get("data_freshness", {}).values()
    ]
    if "stale" in freshness_values:
        limitations.append(
            "One or more product price, availability, or source records were stale when this report was generated."
        )
    if "missing" in freshness_values:
        limitations.append(
            "One or more product freshness dates were unavailable when this report was generated."
        )
    if any(item.get("is_demo_product") for item in recommendations.get("recommendations", [])):
        limitations.append("The recommendation catalogue contains demonstration products.")
    return ("complete_with_limitations" if limitations else "complete"), list(
        dict.fromkeys(limitations)
    )
