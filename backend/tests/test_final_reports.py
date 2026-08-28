from datetime import datetime, timezone

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_face_detection_reports_collection,
    get_final_reports_collection,
    get_image_preprocessing_reports_collection,
    get_image_quality_reports_collection,
    get_image_uploads_collection,
    get_product_eligibility_reports_collection,
    get_product_recommendation_reports_collection,
    get_products_collection,
    get_skin_concern_reports_collection,
    get_skin_profiles_collection,
    get_skin_type_reports_collection,
    get_skincare_routine_reports_collection,
    get_users_collection,
)
from app.core.config import get_settings
from app.core.security import create_access_token
from app.main import create_app
from app.models.final_report import final_report_document_to_response
from app.services.final_report_service import (
    FinalReportArchivedError,
    FinalReportNotFoundError,
    archive_owned_final_report,
    generate_owned_final_report,
    get_owned_final_report,
    list_owned_reports,
)
from tests.catalogue_fakes import FakeCollection
from tests.final_report_fixtures import collection_map, full_source_documents


def api_context(tmp_path):
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    users = FakeCollection(
        [
            {
                "_id": owner,
                "full_name": "Report User",
                "email": "report@example.com",
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
        ]
    )
    app = create_app(enable_lifespan=False)
    mapping = {
        get_users_collection: users,
        get_skin_profiles_collection: collections["skin_profile"],
        get_image_uploads_collection: collections["image_upload"],
        get_image_quality_reports_collection: collections["image_quality"],
        get_face_detection_reports_collection: collections["face_detection"],
        get_image_preprocessing_reports_collection: collections["image_preprocessing"],
        get_skin_type_reports_collection: collections["skin_type"],
        get_skin_concern_reports_collection: collections["skin_concern"],
        get_product_eligibility_reports_collection: collections["product_eligibility"],
        get_product_recommendation_reports_collection: collections["product_recommendation"],
        get_skincare_routine_reports_collection: collections["skincare_routine"],
        get_products_collection: collections["products"],
        get_final_reports_collection: collections["final_reports"],
    }

    def override(collection):
        def provide():
            return collection

        return provide

    for dependency, collection in mapping.items():
        app.dependency_overrides[dependency] = override(collection)
    settings = get_settings().model_copy(
        update={"app_env": "testing", "report_export_directory": tmp_path}
    )
    app.dependency_overrides[get_settings] = lambda: settings
    token = create_access_token(subject=str(owner))
    return TestClient(app), collections, users, docs["image_upload"]["upload_id"], token


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_successful_complete_with_limitations_report_generation():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    assert report["report_status"] == "complete_with_limitations"
    assert report["final_report_id"].startswith("DSR-2026-")
    assert collections["image_upload"].documents[0]["status"] == "workflow_completed"


@pytest.mark.asyncio
async def test_complete_report_without_warning_or_demo_limitation():
    owner, docs = full_source_documents()
    for item in docs["product_recommendation"]["recommendations"]:
        item["is_demo_product"] = False
    docs["product_recommendation"]["limitations"] = []
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    assert report["report_status"] == "complete"


@pytest.mark.asyncio
async def test_missing_required_report_creates_clearly_incomplete_snapshot():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    collections["skin_type"].documents.clear()
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    assert report["report_status"] == "incomplete" and "incomplete" in report["summary"].lower()
    assert collections["image_upload"].documents[0]["status"] == "final_report_incomplete"


@pytest.mark.asyncio
async def test_other_user_cannot_generate_report():
    _, docs = full_source_documents()
    collections = collection_map(docs)
    with pytest.raises(FinalReportNotFoundError):
        await generate_owned_final_report(
            upload_id=docs["image_upload"]["upload_id"],
            user_id=str(ObjectId()),
            collections=collections,
        )


@pytest.mark.asyncio
async def test_safe_response_excludes_internal_and_image_fields():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    text = final_report_document_to_response(report).model_dump_json()
    for forbidden in (
        "storage_reference",
        "processed_image_reference",
        "bounding_box",
        "password",
        "access_token",
        '"_id"',
        '"user_id"',
    ):
        assert forbidden not in text


@pytest.mark.asyncio
async def test_report_contains_expected_sections_and_disclaimer():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    response = final_report_document_to_response(report)
    assert response.skin_profile_summary["age_group"] == "18-25"
    assert response.morning_routine and response.night_routine
    assert "not a medical diagnostic system" in response.medical_disclaimer


@pytest.mark.asyncio
async def test_report_excludes_excluded_products():
    owner, docs = full_source_documents()
    docs["product_recommendation"]["recommendations"][0]["eligibility_status"] = "excluded"
    collections = collection_map(docs)
    with pytest.raises(Exception):
        await generate_owned_final_report(
            upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
        )


@pytest.mark.asyncio
async def test_list_returns_only_owner_reports_with_pagination():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    listed = await list_owned_reports(
        collections["final_reports"],
        str(owner),
        page=1,
        page_size=1,
        report_status=None,
        date_from=None,
        date_to=None,
        sort="newest",
    )
    assert len(listed.reports) == 1 and listed.pagination.page_size == 1
    other = await list_owned_reports(
        collections["final_reports"],
        str(ObjectId()),
        page=1,
        page_size=10,
        report_status=None,
        date_from=None,
        date_to=None,
        sort="newest",
    )
    assert other.reports == []


@pytest.mark.asyncio
async def test_archive_report_is_soft_and_hidden_from_get():
    owner, docs = full_source_documents()
    collections = collection_map(docs)
    report = await generate_owned_final_report(
        upload_id=docs["image_upload"]["upload_id"], user_id=str(owner), collections=collections
    )
    result = await archive_owned_final_report(
        collections["final_reports"], report["final_report_id"], str(owner)
    )
    assert result.is_archived is True and len(collections["final_reports"].documents) == 1
    with pytest.raises(FinalReportArchivedError):
        await get_owned_final_report(
            collections["final_reports"], report["final_report_id"], str(owner)
        )


def test_generate_endpoint_rejects_unauthenticated_request():
    client = TestClient(create_app(enable_lifespan=False))
    assert client.post("/api/final-reports/UP-MISSING/generate").status_code == 401


def test_report_identifier_does_not_encode_email_or_object_id():
    from app.services.report_version_service import generate_public_report_id

    value = generate_public_report_id(datetime(2026, 8, 7, tzinfo=timezone.utc))
    assert value.startswith("DSR-2026-") and "@" not in value and len(value) == 17


def test_no_medical_diagnosis_language_in_summary_or_guidance():
    _, docs = full_source_documents()
    combined = str(docs["skincare_routine"]).lower()
    assert "diagnosis of" not in combined and "cure" not in combined


def test_authenticated_api_generation_retrieval_and_history(tmp_path):
    client, _, _, upload_id, token = api_context(tmp_path)
    generated = client.post(f"/api/final-reports/{upload_id}/generate", headers=auth(token))
    assert generated.status_code == 201
    report_id = generated.json()["final_report_id"]
    detail = client.get(f"/api/final-reports/{report_id}", headers=auth(token))
    history = client.get("/api/final-reports?page=1&page_size=5", headers=auth(token))
    assert detail.status_code == 200 and history.status_code == 200
    assert history.json()["reports"][0]["final_report_id"] == report_id
    assert "known_allergies" not in history.text


def test_api_cross_user_report_access_returns_404(tmp_path):
    client, _, users, upload_id, token = api_context(tmp_path)
    report_id = client.post(f"/api/final-reports/{upload_id}/generate", headers=auth(token)).json()[
        "final_report_id"
    ]
    other = ObjectId()
    users.documents.append(
        {
            "_id": other,
            "full_name": "Other",
            "email": "other@example.com",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
    )
    response = client.get(
        f"/api/final-reports/{report_id}", headers=auth(create_access_token(subject=str(other)))
    )
    assert response.status_code == 404


def test_api_pdf_export_returns_safe_download(tmp_path):
    client, _, _, upload_id, token = api_context(tmp_path)
    report_id = client.post(f"/api/final-reports/{upload_id}/generate", headers=auth(token)).json()[
        "final_report_id"
    ]
    response = client.post(
        f"/api/final-reports/{report_id}/export/pdf",
        headers=auth(token),
        json={"privacy_mode": "privacy_reduced"},
    )
    assert response.status_code == 200 and response.headers["content-type"].startswith(
        "application/pdf"
    )
    assert response.headers["cache-control"] == "no-store" and response.content.startswith(b"%PDF")
    assert "storage" not in response.headers.get("content-disposition", "").lower()


def test_api_invalid_privacy_mode_is_rejected(tmp_path):
    client, _, _, upload_id, token = api_context(tmp_path)
    report_id = client.post(f"/api/final-reports/{upload_id}/generate", headers=auth(token)).json()[
        "final_report_id"
    ]
    response = client.post(
        f"/api/final-reports/{report_id}/export/pdf",
        headers=auth(token),
        json={"privacy_mode": "public"},
    )
    assert response.status_code == 422


def test_api_archive_hides_report_detail(tmp_path):
    client, _, _, upload_id, token = api_context(tmp_path)
    report_id = client.post(f"/api/final-reports/{upload_id}/generate", headers=auth(token)).json()[
        "final_report_id"
    ]
    assert client.delete(f"/api/final-reports/{report_id}", headers=auth(token)).status_code == 200
    assert client.get(f"/api/final-reports/{report_id}", headers=auth(token)).status_code == 410
