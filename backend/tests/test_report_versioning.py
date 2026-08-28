import pytest

from app.repositories.final_report_repository import find_latest_owned_report
from app.services.final_report_service import generate_owned_final_report
from app.services.report_version_service import next_report_version, source_fingerprint
from tests.final_report_fixtures import collection_map, full_source_documents


def test_version_one_for_empty_history():
    assert next_report_version([]) == 1


def test_next_version_uses_highest_preserved_version():
    assert next_report_version([{"report_version": 1}, {"report_version": 4}]) == 5


def test_source_fingerprint_is_stable_across_dictionary_order():
    assert source_fingerprint({"b": "2", "a": "1"}, {"z": "3"}) == source_fingerprint(
        {"a": "1", "b": "2"}, {"z": "3"}
    )


@pytest.mark.asyncio
async def test_normal_generate_is_idempotent_for_same_sources():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    upload_id = docs["image_upload"]["upload_id"]
    first = await generate_owned_final_report(
        upload_id=upload_id, user_id=str(owner), collections=collections
    )
    second = await generate_owned_final_report(
        upload_id=upload_id, user_id=str(owner), collections=collections
    )
    assert (
        first["final_report_id"] == second["final_report_id"]
        and len(collections["final_reports"].documents) == 1
    )


@pytest.mark.asyncio
async def test_regenerate_creates_version_two_and_supersedes_one():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    upload_id = docs["image_upload"]["upload_id"]
    first = await generate_owned_final_report(
        upload_id=upload_id, user_id=str(owner), collections=collections
    )
    second = await generate_owned_final_report(
        upload_id=upload_id, user_id=str(owner), collections=collections, force_new_version=True
    )
    assert (
        second["report_version"] == 2 and second["supersedes_report_id"] == first["final_report_id"]
    )
    old = next(
        item
        for item in collections["final_reports"].documents
        if item["final_report_id"] == first["final_report_id"]
    )
    assert (
        old["report_status"] == "superseded"
        and old["superseded_by_report_id"] == second["final_report_id"]
    )


@pytest.mark.asyncio
async def test_historical_price_snapshot_is_not_mutated():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    upload_id = docs["image_upload"]["upload_id"]
    first = await generate_owned_final_report(
        upload_id=upload_id, user_id=str(owner), collections=collections
    )
    collections["products"].documents[0]["price"]["amount"] = 999
    second = await generate_owned_final_report(
        upload_id=upload_id, user_id=str(owner), collections=collections, force_new_version=True
    )
    assert first["product_recommendation_summary"][0]["price_at_report_time"]["amount"] == 499
    assert second["product_recommendation_summary"][0]["price_at_report_time"]["amount"] == 999


@pytest.mark.asyncio
async def test_latest_report_returns_active_version():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    upload_id = docs["image_upload"]["upload_id"]
    await generate_owned_final_report(
        upload_id=upload_id, user_id=str(owner), collections=collections
    )
    second = await generate_owned_final_report(
        upload_id=upload_id, user_id=str(owner), collections=collections, force_new_version=True
    )
    latest = await find_latest_owned_report(collections["final_reports"], upload_id, str(owner))
    assert latest["final_report_id"] == second["final_report_id"]


@pytest.mark.asyncio
async def test_regeneration_preserves_two_documents():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    upload_id = docs["image_upload"]["upload_id"]
    await generate_owned_final_report(
        upload_id=upload_id, user_id=str(owner), collections=collections
    )
    await generate_owned_final_report(
        upload_id=upload_id, user_id=str(owner), collections=collections, force_new_version=True
    )
    assert len(collections["final_reports"].documents) == 2
