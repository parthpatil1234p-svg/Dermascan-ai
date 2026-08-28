import pytest

from app.models.skincare_routine import routine_document_to_response
from app.schemas.product_recommendation import StoredRecommendation
from app.services.skincare_routine_service import (
    RoutinePrerequisiteError,
    build_routines,
    generate_owned_routine,
)
from tests.catalogue_fakes import FakeCollection
from tests.final_report_fixtures import full_source_documents


def test_routine_orders_morning_and_night_categories():
    _, docs = full_source_documents()
    items = [
        StoredRecommendation.model_validate(item)
        for item in docs["product_recommendation"]["recommendations"]
    ]
    morning, night, _, warnings = build_routines(items)
    assert [item.category for item in morning] == ["cleanser", "moisturizer", "sunscreen"]
    assert [item.category for item in night] == [
        "cleanser",
        "serum",
        "moisturizer",
    ] and warnings == []


def test_serum_is_optional():
    _, docs = full_source_documents()
    items = [
        StoredRecommendation.model_validate(item)
        for item in docs["product_recommendation"]["recommendations"]
    ]
    _, night, _, _ = build_routines(items)
    assert next(item for item in night if item.category == "serum").is_optional is True


def test_missing_sunscreen_is_a_limitation_not_a_substitution():
    _, docs = full_source_documents()
    items = [
        StoredRecommendation.model_validate(item)
        for item in docs["product_recommendation"]["recommendations"]
        if item["category"] != "sunscreen"
    ]
    morning, _, _, warnings = build_routines(items)
    assert "sunscreen" not in {item.category for item in morning} and any(
        "sunscreen" in item for item in warnings
    )


def test_ineligible_product_is_rejected():
    _, docs = full_source_documents()
    docs["product_recommendation"]["recommendations"][0]["eligibility_status"] = "excluded"
    with pytest.raises(Exception):
        build_routines(
            [
                StoredRecommendation.model_validate(item)
                for item in docs["product_recommendation"]["recommendations"]
            ]
        )


@pytest.mark.asyncio
async def test_generate_routine_is_owner_scoped_and_updates_status():
    owner, docs = full_source_documents()
    upload = docs["image_upload"]
    upload["status"] = "routine_generation_pending"
    uploads = FakeCollection([upload])
    recommendations = FakeCollection([docs["product_recommendation"]])
    routines = FakeCollection()
    result = await generate_owned_routine(
        upload_id=upload["upload_id"],
        user_id=str(owner),
        uploads=uploads,
        recommendation_reports=recommendations,
        routine_reports=routines,
    )
    assert (
        result["routine_status"] == "completed"
        and uploads.documents[0]["status"] == "final_report_pending"
    )
    assert routine_document_to_response(result).can_continue is True


@pytest.mark.asyncio
async def test_generate_routine_requires_recommendation_report():
    owner, docs = full_source_documents()
    upload = docs["image_upload"]
    upload["status"] = "routine_generation_pending"
    with pytest.raises(RoutinePrerequisiteError):
        await generate_owned_routine(
            upload_id=upload["upload_id"],
            user_id=str(owner),
            uploads=FakeCollection([upload]),
            recommendation_reports=FakeCollection(),
            routine_reports=FakeCollection(),
        )
