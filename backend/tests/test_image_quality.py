from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from PIL import Image, ImageFilter
from pydantic import ValidationError

from app.api.dependencies import (
    get_image_quality_reports_collection,
    get_image_uploads_collection,
    get_skin_profiles_collection,
    get_users_collection,
)
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.main import create_app


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


def matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    return all(document.get(key) == value for key, value in query.items())


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[ObjectId, dict[str, Any]] = {}

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents.values():
            if matches(document, query):
                return document.copy()
        return None

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        inserted_id = ObjectId()
        self.documents[inserted_id] = {**document, "_id": inserted_id}
        return InsertOneResult(inserted_id)

    async def update_one(self, query: dict[str, Any], operation: dict[str, Any]) -> None:
        for document in self.documents.values():
            if matches(document, query):
                document.update(operation["$set"])
                return


def make_settings(upload_directory: Path, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "app_name": "DermaScan AI",
        "app_env": "testing",
        "api_prefix": "/api",
        "mongodb_url": "mongodb://localhost:27017",
        "mongodb_database": "dermascan_quality_test",
        "jwt_secret_key": "quality-test-secret-key-at-least-32-bytes-long",
        "jwt_algorithm": "HS256",
        "access_token_expire_minutes": 60,
        "frontend_origin": "http://localhost:5173",
        "max_upload_size_mb": 5,
        "allowed_image_types": "image/jpeg,image/png",
        "upload_directory": upload_directory,
        "temp_upload_expiry_minutes": 30,
        "min_image_width": 300,
        "min_image_height": 300,
        "max_image_width": 1000,
        "max_image_height": 1000,
    }
    values.update(overrides)
    return Settings(**values)


def create_client(tmp_path: Path):
    users = FakeCollection()
    profiles = FakeCollection()
    uploads = FakeCollection()
    reports = FakeCollection()
    settings = make_settings(tmp_path / "quality_uploads")
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_users_collection] = lambda: users
    app.dependency_overrides[get_skin_profiles_collection] = lambda: profiles
    app.dependency_overrides[get_image_uploads_collection] = lambda: uploads
    app.dependency_overrides[get_image_quality_reports_collection] = lambda: reports
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app), users, profiles, uploads, reports, settings


def seed_user(
    users: FakeCollection,
    profiles: FakeCollection,
    *,
    email: str = "quality@example.com",
    complete_profile: bool = True,
) -> tuple[str, str]:
    user_id = ObjectId()
    now = datetime.now(timezone.utc)
    users.documents[user_id] = {
        "_id": user_id,
        "full_name": "Quality Test User",
        "email": email,
        "password_hash": "not-used",
        "age_group": "18-25",
        "location": "India",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    if complete_profile:
        profile_id = ObjectId()
        profiles.documents[profile_id] = {
            "_id": profile_id,
            "user_id": user_id,
            "is_complete": True,
        }
    return create_access_token(subject=str(user_id)), str(user_id)


def checker_image(
    size: tuple[int, int] = (400, 400),
    low: int = 80,
    high: int = 180,
    block: int = 10,
) -> Image.Image:
    width, height = size
    y, x = np.indices((height, width))
    pattern = ((x // block + y // block) % 2).astype(np.uint8)
    grayscale = np.where(pattern == 0, low, high).astype(np.uint8)
    rgb = np.repeat(grayscale[:, :, None], 3, axis=2)
    return Image.fromarray(rgb, "RGB")


def seed_upload(
    uploads: FakeCollection,
    settings: Settings,
    user_id: str,
    image: Image.Image | None = None,
    *,
    status: str = "validated",
    consent_given: bool = True,
    expired: bool = False,
    corrupt: bool = False,
    missing_file: bool = False,
) -> tuple[str, Path]:
    upload_id = str(uuid4())
    user_directory = settings.upload_path / user_id[:12]
    user_directory.mkdir(parents=True, exist_ok=True)
    image_path = user_directory / f"{uuid4().hex}.png"
    if not missing_file:
        if corrupt:
            image_path.write_bytes(b"not an image")
        else:
            (image or checker_image()).save(image_path, format="PNG")

    now = datetime.now(timezone.utc)
    document_id = ObjectId()
    uploads.documents[document_id] = {
        "_id": document_id,
        "user_id": ObjectId(user_id),
        "upload_id": upload_id,
        "stored_filename": image_path.name,
        "storage_reference": image_path.relative_to(settings.upload_path).as_posix(),
        "original_extension": ".png",
        "mime_type": "image/png",
        "image_format": "PNG",
        "file_size_bytes": image_path.stat().st_size if image_path.exists() else 0,
        "width": image.width if image else 400,
        "height": image.height if image else 400,
        "status": status,
        "consent_given": consent_given,
        "consent_given_at": now if consent_given else None,
        "created_at": now,
        "updated_at": now,
        "expires_at": now - timedelta(minutes=1) if expired else now + timedelta(minutes=30),
    }
    return upload_id, image_path


def analyze(client: TestClient, token: str, upload_id: str):
    return client.post(
        f"/api/image-quality/{upload_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
    )


def first_document(collection: FakeCollection) -> dict[str, Any]:
    return next(iter(collection.documents.values()))


def test_successful_quality_analysis(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id)
    response = analyze(client, token, upload_id)
    assert response.status_code == 200
    assert response.json()["quality_status"] == "passed"
    assert response.json()["can_continue"] is True


def test_reject_unauthenticated_request(tmp_path: Path) -> None:
    client, _, _, _, _, _ = create_client(tmp_path)
    assert client.post("/api/image-quality/missing/analyze").status_code == 401


def test_reject_incomplete_profile(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles, complete_profile=False)
    upload_id, _ = seed_upload(uploads, settings, user_id)
    assert analyze(client, token, upload_id).status_code == 403


def test_reject_another_users_upload(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    owner_token, owner_id = seed_user(users, profiles, email="owner@example.com")
    other_token, _ = seed_user(users, profiles, email="other@example.com")
    upload_id, _ = seed_upload(uploads, settings, owner_id)
    assert owner_token
    assert analyze(client, other_token, upload_id).status_code == 404


def test_reject_missing_upload(tmp_path: Path) -> None:
    client, users, profiles, _, _, _ = create_client(tmp_path)
    token, _ = seed_user(users, profiles)
    assert analyze(client, token, "missing-upload").status_code == 404


def test_reject_expired_upload_and_remove_file(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, image_path = seed_upload(uploads, settings, user_id, expired=True)
    response = analyze(client, token, upload_id)
    assert response.status_code == 410
    assert not image_path.exists()
    assert first_document(uploads)["status"] == "expired"


def test_reject_missing_temporary_file(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, missing_file=True)
    response = analyze(client, token, upload_id)
    assert response.status_code == 410
    assert first_document(uploads)["status"] == "quality_failed"


def test_detect_blurred_synthetic_image(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    blurred = checker_image().filter(ImageFilter.GaussianBlur(radius=12))
    upload_id, _ = seed_upload(uploads, settings, user_id, blurred)
    body = analyze(client, token, upload_id).json()
    assert body["metrics"]["sharpness"]["status"] == "too_blurry"
    assert any(issue["code"] == "IMAGE_TOO_BLURRY" for issue in body["issues"])
    assert body["quality_status"] == "failed"


def test_detect_clear_synthetic_image(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, checker_image())
    body = analyze(client, token, upload_id).json()
    assert body["metrics"]["sharpness"]["status"] == "clear"
    assert body["metrics"]["sharpness"]["score"] >= 80


@pytest.mark.parametrize(
    ("image", "expected_code", "expected_status"),
    [
        (checker_image(low=10, high=30), "IMAGE_TOO_DARK", "too_dark"),
        (checker_image(low=230, high=250), "IMAGE_TOO_BRIGHT", "too_bright"),
    ],
)
def test_detect_extreme_brightness(
    tmp_path: Path,
    image: Image.Image,
    expected_code: str,
    expected_status: str,
) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, image)
    body = analyze(client, token, upload_id).json()
    assert body["metrics"]["brightness"]["status"] == expected_status
    assert any(issue["code"] == expected_code for issue in body["issues"])
    assert body["quality_status"] == "failed"


def test_detect_underexposure(tmp_path: Path) -> None:
    image = Image.new("RGB", (400, 400), color=(150, 150, 150))
    image.paste((10, 10, 10), (0, 0, 240, 400))
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, image)
    body = analyze(client, token, upload_id).json()
    assert body["metrics"]["exposure"]["underexposed_percent"] > 45
    assert any(issue["code"] == "IMAGE_UNDEREXPOSED" for issue in body["issues"])


def test_detect_overexposure(tmp_path: Path) -> None:
    image = Image.new("RGB", (400, 400), color=(130, 130, 130))
    image.paste((250, 250, 250), (0, 0, 160, 400))
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, image)
    body = analyze(client, token, upload_id).json()
    assert body["metrics"]["exposure"]["overexposed_percent"] > 35
    assert any(issue["code"] == "IMAGE_OVEREXPOSED" for issue in body["issues"])


def test_detect_low_contrast(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, checker_image(low=124, high=132))
    body = analyze(client, token, upload_id).json()
    assert body["metrics"]["contrast"]["status"] == "low"
    assert any(issue["code"] == "IMAGE_LOW_CONTRAST" for issue in body["issues"])


def test_reject_insufficient_resolution_with_failed_report(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, checker_image(size=(200, 200)))
    body = analyze(client, token, upload_id).json()
    assert body["quality_status"] == "failed"
    assert body["can_continue"] is False
    assert any(issue["code"] == "IMAGE_TOO_SMALL" for issue in body["issues"])


def test_warn_unusual_aspect_ratio(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, checker_image(size=(900, 350)))
    body = analyze(client, token, upload_id).json()
    assert body["metrics"]["resolution"]["status"] == "unusual_aspect_ratio"
    assert any(issue["code"] == "IMAGE_UNUSUAL_ASPECT_RATIO" for issue in body["issues"])


def test_scores_are_normalized_and_hard_failures_win(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, checker_image(low=5, high=35))
    body = analyze(client, token, upload_id).json()
    scores = [
        body["quality_score"],
        body["metrics"]["sharpness"]["score"],
        body["metrics"]["brightness"]["score"],
        body["metrics"]["exposure"]["score"],
        body["metrics"]["contrast"]["score"],
        body["metrics"]["resolution"]["score"],
    ]
    assert all(0 <= score <= 100 for score in scores)
    assert body["quality_status"] == "failed"


def test_store_safe_quality_report_and_update_upload_status(tmp_path: Path) -> None:
    client, users, profiles, uploads, reports, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id)
    response = analyze(client, token, upload_id)
    assert response.status_code == 200
    assert len(reports.documents) == 1
    report = first_document(reports)
    assert str(report["user_id"]) == user_id
    assert report["upload_id"] == upload_id
    assert first_document(uploads)["status"] == "quality_passed"
    response_text = response.text
    assert "storage_reference" not in response_text
    assert "stored_filename" not in response_text
    assert "physical" not in response_text


def test_reanalysis_updates_report_without_duplicate(tmp_path: Path) -> None:
    client, users, profiles, uploads, reports, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, image_path = seed_upload(uploads, settings, user_id)
    first = analyze(client, token, upload_id).json()
    checker_image(low=110, high=146).save(image_path, format="PNG")
    second = analyze(client, token, upload_id).json()
    assert len(reports.documents) == 1
    assert first["quality_report_id"] == second["quality_report_id"]
    assert first["created_at"] == second["created_at"]
    assert second["updated_at"] >= first["updated_at"]
    assert second["quality_status"] == "warning"


def test_get_existing_report_does_not_rerun_analysis(tmp_path: Path) -> None:
    client, users, profiles, uploads, reports, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id)
    analyze(client, token, upload_id)
    report_before = first_document(reports).copy()
    response = client.get(
        f"/api/image-quality/{upload_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert first_document(reports)["updated_at"] == report_before["updated_at"]


def test_accept_warning_and_record_permission(tmp_path: Path) -> None:
    client, users, profiles, uploads, reports, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, checker_image(low=110, high=146))
    report = analyze(client, token, upload_id).json()
    assert report["quality_status"] == "warning"
    response = client.post(
        f"/api/image-quality/{upload_id}/accept-warning",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["can_continue"] is True
    assert response.json()["next_route"] == "/face-detection"
    assert first_document(reports)["warning_accepted"] is True
    assert first_document(uploads)["status"] == "face_detection_pending"


def test_reject_warning_acceptance_for_failed_result(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, checker_image(low=10, high=30))
    analyze(client, token, upload_id)
    response = client.post(
        f"/api/image-quality/{upload_id}/accept-warning",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


def test_reject_missing_consent_and_analysis_in_progress(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    no_consent_id, _ = seed_upload(uploads, settings, user_id, consent_given=False)
    checking_id, _ = seed_upload(uploads, settings, user_id, status="quality_checking")
    assert analyze(client, token, no_consent_id).status_code == 400
    assert analyze(client, token, checking_id).status_code == 409


def test_decode_failure_is_safe_and_marks_upload_failed(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, corrupt=True)
    response = analyze(client, token, upload_id)
    assert response.status_code == 422
    assert "OpenCV" not in response.text
    assert first_document(uploads)["status"] == "quality_failed"


def test_processing_exception_restores_recoverable_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, users, profiles, uploads, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id)

    def fail_metrics(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("internal detail that must not leak")

    monkeypatch.setattr(
        "app.services.image_quality_service.calculate_image_metrics",
        fail_metrics,
    )
    response = analyze(client, token, upload_id)
    assert response.status_code == 500
    assert "internal detail" not in response.text
    assert first_document(uploads)["status"] == "validated"


def test_invalid_threshold_configuration_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        make_settings(
            tmp_path / "invalid",
            blur_fail_threshold=120,
            blur_warning_threshold=100,
        )
