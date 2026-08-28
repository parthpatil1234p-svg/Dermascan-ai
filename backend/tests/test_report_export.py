import os
from datetime import datetime, timedelta, timezone

import pytest
from pypdf import PdfReader

from app.core.config import Settings
from app.services.final_report_service import generate_owned_final_report
from app.services.report_cleanup_service import cleanup_expired_report_exports
from app.services.report_export_service import (
    ReportExportError,
    create_pdf_export,
    render_report_html,
)
from tests.final_report_fixtures import collection_map, full_source_documents


def export_settings(tmp_path):
    return Settings(
        APP_NAME="DermaScan AI",
        APP_ENV="testing",
        MONGODB_URL="mongodb://test",
        MONGODB_DATABASE="test",
        JWT_SECRET_KEY="test-secret-key-with-enough-length",
        REPORT_EXPORT_DIRECTORY=tmp_path,
    )


def pdf_text(path):
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


@pytest.fixture
async def report_document():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    return await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["standard", "privacy_reduced", "technical"])
async def test_generate_supported_pdf_modes(tmp_path, mode):
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    exported = create_pdf_export(report, mode, export_settings(tmp_path))
    assert (
        exported.physical_path.read_bytes().startswith(b"%PDF")
        and exported.physical_path.stat().st_size > 1000
    )


@pytest.mark.asyncio
async def test_pdf_storage_filename_is_randomized(tmp_path):
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    first = create_pdf_export(report, "standard", export_settings(tmp_path))
    second = create_pdf_export(report, "standard", export_settings(tmp_path))
    assert (
        first.physical_path.name != second.physical_path.name
        and report["final_report_id"] not in first.physical_path.name
    )


@pytest.mark.asyncio
async def test_pdf_excludes_raw_image_and_private_paths(tmp_path):
    owner, docs = full_source_documents()
    docs["image_upload"]["storage_reference"] = "secret-face.jpg"
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    data = create_pdf_export(
        report, "technical", export_settings(tmp_path)
    ).physical_path.read_bytes()
    assert b"secret-face.jpg" not in data and b"storage_reference" not in data


@pytest.mark.asyncio
async def test_pdf_download_name_uses_safe_public_id(tmp_path):
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    exported = create_pdf_export(report, "standard", export_settings(tmp_path))
    assert exported.download_filename.startswith(
        "DermaScan-DSR-"
    ) and exported.download_filename.endswith("-v1.pdf")


@pytest.mark.asyncio
async def test_pdf_includes_disclaimer_report_id_version_and_page_number(tmp_path):
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    exported = create_pdf_export(report, "standard", export_settings(tmp_path))
    text = pdf_text(exported.physical_path)
    assert (
        "not a medical diagnostic system" in text
        and report["final_report_id"] in text
        and "Version 1" in text
        and "Page 1" in text
    )


@pytest.mark.asyncio
async def test_privacy_reduced_pdf_hides_known_allergy(tmp_path):
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    standard = pdf_text(
        create_pdf_export(report, "standard", export_settings(tmp_path)).physical_path
    )
    reduced = pdf_text(
        create_pdf_export(report, "privacy_reduced", export_settings(tmp_path)).physical_path
    )
    assert "Added Fragrance" in standard and "Added Fragrance" not in reduced


@pytest.mark.asyncio
async def test_technical_pdf_contains_version_transparency(tmp_path):
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    text = pdf_text(create_pdf_export(report, "technical", export_settings(tmp_path)).physical_path)
    assert "Technical Transparency" in text and "1.0-test" in text


@pytest.mark.asyncio
async def test_incomplete_report_cannot_export(tmp_path):
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    collections["skin_type"].documents.clear()
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    with pytest.raises(ReportExportError):
        create_pdf_export(report, "standard", export_settings(tmp_path))


def test_report_html_escapes_user_controlled_text():
    owner, docs = full_source_documents()
    document = {
        "report_title": "Safe report",
        "final_report_id": "DSR-2026-ABCDEF12",
        "report_version": 1,
        "summary": "<script>alert(1)</script>",
        "skin_profile_summary": {"age_group": "18-25", "known_allergies": ["<img src=x>"]},
        "skin_type_summary": {"skin_type": "Combination"},
    }
    html = render_report_html(document, "standard")
    assert "<script>" not in html and "&lt;script&gt;" in html and "<img" not in html


def test_privacy_reduced_html_hides_allergies():
    document = {
        "report_title": "Safe",
        "final_report_id": "DSR-2026-ABCDEF12",
        "report_version": 1,
        "summary": "Summary",
        "skin_profile_summary": {"age_group": "18-25", "known_allergies": ["Private Allergy"]},
        "skin_type_summary": {"skin_type": "Combination"},
    }
    assert "Private Allergy" not in render_report_html(document, "privacy_reduced")


def test_cleanup_removes_only_expired_export_artifacts(tmp_path):
    old = tmp_path / "old.pdf"
    recent = tmp_path / "recent.pdf"
    unrelated = tmp_path / "keep.txt"
    old.write_bytes(b"old")
    recent.write_bytes(b"new")
    unrelated.write_text("keep")
    old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()
    os.utime(old, (old_time, old_time))
    removed = cleanup_expired_report_exports(
        export_settings(tmp_path), now=datetime.now(timezone.utc)
    )
    assert removed == 1 and not old.exists() and recent.exists() and unrelated.exists()
