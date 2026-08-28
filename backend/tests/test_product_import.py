import json

import pytest

from app.schemas.product import ProductCreate
from app.services.product_import_service import (
    ProductImportFormatError,
    import_product_records,
    parse_import_content,
)
from tests.catalogue_fakes import FakeCollection
from tests.test_products import product_payload


def record(**overrides):
    return ProductCreate.model_validate(product_payload(**overrides)).model_dump(mode="json")


def test_parse_json_import():
    parsed = parse_import_content(json.dumps([record()]).encode(), "json")
    assert parsed[0]["product_id"] == "PRD-TEST001"


def test_parse_csv_import_with_controlled_lists():
    content = (
        "product_id,product_name,suitable_skin_types,is_demo_product\n"
        "PRD-CSV001,CSV Product,normal|dry,true\n"
    ).encode()
    parsed = parse_import_content(content, "csv")
    assert parsed[0]["suitable_skin_types"] == ["normal", "dry"]
    assert parsed[0]["is_demo_product"] is True


def test_reject_unsupported_import_format():
    with pytest.raises(ProductImportFormatError):
        parse_import_content(b"content", "xlsx")


@pytest.mark.asyncio
async def test_import_dry_run_does_not_insert_products():
    products, jobs = FakeCollection(), FakeCollection()
    result = await import_product_records(
        [record()], "demo.json", "json", products, jobs, dry_run=True
    )
    assert result.status == "preview_ready"
    assert result.valid_records == 1
    assert products.documents == []
    assert len(jobs.documents) == 1


@pytest.mark.asyncio
async def test_import_reports_invalid_rows():
    products, jobs = FakeCollection(), FakeCollection()
    invalid = record()
    invalid["category"] = "prescription"
    result = await import_product_records(
        [invalid], "invalid.json", "json", products, jobs, dry_run=True
    )
    assert result.invalid_records == 1
    assert result.errors[0].startswith("Row 1:")


@pytest.mark.asyncio
async def test_import_detects_duplicate_rows():
    products, jobs = FakeCollection(), FakeCollection()
    result = await import_product_records(
        [record(), record(product_id="PRD-OTHER001")],
        "duplicates.json",
        "json",
        products,
        jobs,
        dry_run=True,
    )
    assert result.duplicate_records == 1
    assert result.valid_records == 1


@pytest.mark.asyncio
async def test_import_inserts_valid_records_and_job_report():
    products, jobs = FakeCollection(), FakeCollection()
    result = await import_product_records(
        [record()], "demo.json", "json", products, jobs, dry_run=False
    )
    assert result.status == "completed"
    assert result.inserted_records == 1
    assert products.documents[0]["normalized_brand_name"] == "dermademo labs"
    assert "source_filename" in jobs.documents[0]


@pytest.mark.asyncio
async def test_import_updates_matching_product_id_without_duplicate():
    products, jobs = FakeCollection(), FakeCollection()
    await import_product_records([record()], "first.json", "json", products, jobs, dry_run=False)
    changed = record(
        short_description="A changed fictional description that remains suitable for testing."
    )
    result = await import_product_records(
        [changed], "second.json", "json", products, jobs, dry_run=False
    )
    assert result.updated_records == 1
    assert len(products.documents) == 1
    assert products.documents[0]["short_description"].startswith("A changed")
