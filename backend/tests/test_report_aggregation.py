import pytest

from app.services.ingredient_guidance_service import build_ingredient_guidance
from app.services.report_aggregation_service import (
    aggregate_sections,
    load_source_reports,
    source_metadata,
)
from app.services.report_summary_service import generate_executive_summary
from app.services.report_validation_service import (
    ReportRelationshipError,
    determine_report_status,
    missing_required_sources,
    validate_source_relationships,
)
from tests.final_report_fixtures import collection_map, full_source_documents


@pytest.mark.asyncio
async def test_aggregates_required_report_sections():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    sources = await load_source_reports(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    sections = await aggregate_sections(sources, collections["products"])
    assert {
        "skin_profile",
        "image_processing",
        "skin_type",
        "visible_observations",
        "ingredient_guidance",
        "product_recommendations",
        "morning_routine",
        "night_routine",
    }.issubset(sections)


@pytest.mark.asyncio
async def test_image_summary_excludes_private_paths_and_landmarks():
    owner, docs = full_source_documents()
    docs["image_preprocessing"]["processed_image_reference"] = "private/file.jpg"
    docs["face_detection"]["bounding_box_pixels"] = {"x": 1}
    collections = collection_map(docs)
    sources = await load_source_reports(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    text = str((await aggregate_sections(sources, collections["products"]))["image_processing"])
    assert "private/file" not in text and "bounding" not in text


@pytest.mark.asyncio
async def test_product_snapshot_preserves_price_and_availability():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    sources = await load_source_reports(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    item = (await aggregate_sections(sources, collections["products"]))["product_recommendations"][
        0
    ]
    assert (
        item["price_at_report_time"]["amount"] == 499
        and item["availability_at_report_time"] == "available"
    )


def test_relationship_validation_accepts_consistent_sources():
    owner, docs = full_source_documents()
    validate_source_relationships(docs, str(owner), docs["image_upload"]["upload_id"])


def test_relationship_validation_rejects_other_owner():
    owner, docs = full_source_documents()
    docs["skin_type"]["user_id"] = type(owner)()
    with pytest.raises(ReportRelationshipError):
        validate_source_relationships(docs, str(owner), docs["image_upload"]["upload_id"])


def test_relationship_validation_rejects_conflicting_report_ids():
    owner, docs = full_source_documents()
    docs["skin_concern"]["skin_type_report_id"] = "OTHER"
    with pytest.raises(ReportRelationshipError):
        validate_source_relationships(docs, str(owner), docs["image_upload"]["upload_id"])


def test_relationship_validation_rejects_unrecommended_routine_product():
    owner, docs = full_source_documents()
    docs["skincare_routine"]["morning_routine"][0]["product_id"] = "EXCLUDED"
    with pytest.raises(ReportRelationshipError):
        validate_source_relationships(docs, str(owner), docs["image_upload"]["upload_id"])


def test_relationship_validation_requires_consent():
    owner, docs = full_source_documents()
    docs["image_upload"]["consent_given"] = False
    with pytest.raises(ReportRelationshipError):
        validate_source_relationships(docs, str(owner), docs["image_upload"]["upload_id"])


@pytest.mark.parametrize(
    "missing",
    [
        "skin_profile",
        "image_quality",
        "face_detection",
        "image_preprocessing",
        "skin_type",
        "skin_concern",
        "product_eligibility",
        "product_recommendation",
        "skincare_routine",
    ],
)
def test_missing_required_module_is_detected(missing):
    _, docs = full_source_documents()
    docs[missing] = None
    assert missing in missing_required_sources(docs)


def test_complete_status_without_limitations():
    _, docs = full_source_documents()
    docs["product_recommendation"]["recommendations"] = [
        dict(item, is_demo_product=False)
        for item in docs["product_recommendation"]["recommendations"]
    ]
    status, limitations = determine_report_status(docs, [])
    assert status == "complete" and limitations == []


def test_quality_warning_produces_complete_with_limitations():
    _, docs = full_source_documents()
    docs["image_quality"]["quality_status"] = "warning"
    docs["image_quality"]["warning_accepted"] = True
    status, limitations = determine_report_status(docs, [])
    assert status == "complete_with_limitations" and any("quality" in item for item in limitations)


def test_uncertain_skin_type_produces_limitation():
    _, docs = full_source_documents()
    docs["skin_type"]["result_status"] = "uncertain"
    assert any("uncertain" in item for item in determine_report_status(docs, [])[1])


def test_stale_product_data_produces_dynamic_limitation():
    _, docs = full_source_documents()
    docs["product_recommendation"]["recommendations"][0]["data_freshness"]["price"] = "stale"
    status, limitations = determine_report_status(docs, [])
    assert status == "complete_with_limitations" and any("stale" in item for item in limitations)


def test_incomplete_status_names_missing_section():
    _, docs = full_source_documents()
    status, limitations = determine_report_status(docs, ["skin_type"])
    assert status == "incomplete" and "skin type" in limitations[0]


def test_ingredient_guidance_uses_controlled_roles_and_avoidances():
    _, docs = full_source_documents()
    result = build_ingredient_guidance(
        docs["skin_profile"], docs["skin_type"], docs["skin_concern"]
    )
    assert any(
        item.ingredient_role == "Balanced hydration support" for item in result.potentially_relevant
    )
    assert {item.item for item in result.avoid_or_review} >= {"Added Fragrance", "Drying Alcohol"}


def test_summary_mentions_uncertainty_without_diagnosis():
    _, docs = full_source_documents()
    docs["skin_type"]["final_skin_type"] = "Uncertain"
    summary = generate_executive_summary(
        docs["skin_type"], docs["skin_concern"], docs["skin_profile"]
    )
    assert "uncertain" in summary.lower() and "diagnos" not in summary.lower()


def test_incomplete_summary_does_not_infer_missing_result():
    summary = generate_executive_summary(None, None, None, incomplete=True)
    assert "incomplete" in summary.lower() and "inferred" in summary.lower()


def test_source_metadata_records_models_and_engines():
    _, docs = full_source_documents()
    _, _, models, engines = source_metadata(docs)
    assert models["skin_type"] == "1.0-test" and engines["routine"] == "1.0.0"


@pytest.mark.parametrize(
    "source,field",
    [
        ("skin_type", "model_version"),
        ("skin_concern", "model_version"),
        ("product_recommendation", "scoring_engine_version"),
        ("skincare_routine", "routine_engine_version"),
    ],
)
def test_missing_source_version_makes_report_incomplete(source, field):
    _, docs = full_source_documents()
    docs[source][field] = None
    assert any(source in item and field in item for item in missing_required_sources(docs))
