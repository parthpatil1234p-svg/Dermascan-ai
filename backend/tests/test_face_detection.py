import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError

from app.api.dependencies import (
    get_face_detection_reports_collection,
    get_image_preprocessing_reports_collection,
    get_image_quality_reports_collection,
    get_image_uploads_collection,
    get_skin_profiles_collection,
    get_skin_type_reports_collection,
    get_users_collection,
)
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.main import create_app
from app.services.face_crop_service import cleanup_expired_face_crops
from app.services.face_detection_service import (
    DetectedFace,
    FaceDetectorProcessingError,
    FaceDetectorUnavailableError,
    MediaPipeFaceDetector,
)
from app.utils.bounding_box import NormalizedBoundingBox, normalized_to_pixel_box


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self.documents = documents
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self) -> dict[str, Any]:
        if self.index >= len(self.documents):
            raise StopAsyncIteration
        document = self.documents[self.index]
        self.index += 1
        return document.copy()


def value_matches(value: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        for operator, target in expected.items():
            if operator == "$lte" and not value <= target:
                return False
            if operator == "$ne" and not value != target:
                return False
        return True
    return value == expected


def matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    return all(value_matches(document.get(key), value) for key, value in query.items())


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[ObjectId, dict[str, Any]] = {}

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents.values():
            if matches(document, query):
                return document.copy()
        return None

    def find(self, query: dict[str, Any]) -> FakeCursor:
        return FakeCursor(
            [document for document in self.documents.values() if matches(document, query)]
        )

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        inserted_id = ObjectId()
        self.documents[inserted_id] = {**document, "_id": inserted_id}
        return InsertOneResult(inserted_id)

    async def update_one(self, query: dict[str, Any], operation: dict[str, Any]) -> None:
        for document in self.documents.values():
            if matches(document, query):
                document.update(operation["$set"])
                return

    async def delete_one(self, query: dict[str, Any]) -> None:
        for document_id, document in list(self.documents.items()):
            if matches(document, query):
                del self.documents[document_id]
                return


class StaticDetector:
    def __init__(
        self,
        detections: list[DetectedFace] | None = None,
        *,
        raises: bool = False,
    ) -> None:
        self.detections = detections or []
        self.raises = raises

    def detect(self, image):
        if self.raises:
            raise FaceDetectorProcessingError("detector exploded")
        return self.detections


def make_settings(upload_directory: Path, crop_directory: Path, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "app_name": "DermaScan AI",
        "app_env": "testing",
        "api_prefix": "/api",
        "mongodb_url": "mongodb://localhost:27017",
        "mongodb_database": "dermascan_face_test",
        "jwt_secret_key": "face-test-secret-key-at-least-32-bytes-long",
        "jwt_algorithm": "HS256",
        "access_token_expire_minutes": 60,
        "frontend_origin": "http://localhost:5173",
        "max_upload_size_mb": 5,
        "allowed_image_types": "image/jpeg,image/png",
        "upload_directory": upload_directory,
        "face_crop_directory": crop_directory,
        "temp_upload_expiry_minutes": 30,
        "face_crop_expiry_minutes": 30,
        "min_image_width": 300,
        "min_image_height": 300,
        "max_image_width": 1000,
        "max_image_height": 1000,
        "face_min_area_ratio": 0.15,
        "face_max_area_ratio": 0.85,
        "face_max_center_offset": 0.25,
        "face_crop_padding_ratio": 0.18,
        "face_min_crop_width": 224,
        "face_min_crop_height": 224,
        "face_detection_min_confidence": 0.60,
        "face_detection_max_faces": 1,
    }
    values.update(overrides)
    return Settings(**values)


def create_client(tmp_path: Path, **settings_overrides: Any):
    users = FakeCollection()
    profiles = FakeCollection()
    uploads = FakeCollection()
    quality_reports = FakeCollection()
    face_reports = FakeCollection()
    preprocessing_reports = FakeCollection()
    skin_type_reports = FakeCollection()
    settings = make_settings(
        tmp_path / "uploads",
        tmp_path / "face-crops",
        **settings_overrides,
    )
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_users_collection] = lambda: users
    app.dependency_overrides[get_skin_profiles_collection] = lambda: profiles
    app.dependency_overrides[get_image_uploads_collection] = lambda: uploads
    app.dependency_overrides[get_image_quality_reports_collection] = lambda: quality_reports
    app.dependency_overrides[get_face_detection_reports_collection] = lambda: face_reports
    app.dependency_overrides[get_image_preprocessing_reports_collection] = (
        lambda: preprocessing_reports
    )
    app.dependency_overrides[get_skin_type_reports_collection] = lambda: skin_type_reports
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app), users, profiles, uploads, quality_reports, face_reports, settings


def seed_user(
    users: FakeCollection,
    profiles: FakeCollection,
    *,
    email: str = "face@example.com",
    complete_profile: bool = True,
) -> tuple[str, str]:
    user_id = ObjectId()
    now = datetime.now(timezone.utc)
    users.documents[user_id] = {
        "_id": user_id,
        "full_name": "Face Test User",
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


def seed_upload(
    uploads: FakeCollection,
    settings: Settings,
    user_id: str,
    *,
    status: str = "quality_passed",
    expired: bool = False,
    missing_file: bool = False,
) -> tuple[str, Path]:
    upload_id = str(uuid4())
    upload_directory = settings.upload_path / user_id[:12]
    upload_directory.mkdir(parents=True, exist_ok=True)
    image_path = upload_directory / f"{uuid4().hex}.png"
    if not missing_file:
        Image.new("RGB", (400, 400), color=(150, 170, 180)).save(
            image_path,
            format="PNG",
        )

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
        "width": 400,
        "height": 400,
        "status": status,
        "consent_given": True,
        "consent_given_at": now,
        "created_at": now,
        "updated_at": now,
        "expires_at": now - timedelta(minutes=1) if expired else now + timedelta(minutes=30),
    }
    return upload_id, image_path


def seed_quality_report(
    quality_reports: FakeCollection,
    upload_id: str,
    user_id: str,
    *,
    status: str = "passed",
    warning_accepted: bool = False,
) -> str:
    now = datetime.now(timezone.utc)
    report_id = str(uuid4())
    document_id = ObjectId()
    quality_reports.documents[document_id] = {
        "_id": document_id,
        "quality_report_id": report_id,
        "upload_id": upload_id,
        "user_id": ObjectId(user_id),
        "quality_status": status,
        "warning_accepted": warning_accepted,
        "warning_accepted_at": now if warning_accepted else None,
        "created_at": now,
        "updated_at": now,
    }
    return report_id


def face(
    x: float = 0.25,
    y: float = 0.15,
    width: float = 0.5,
    height: float = 0.65,
    confidence: float = 0.93,
) -> DetectedFace:
    return DetectedFace(
        bounding_box=NormalizedBoundingBox(x=x, y=y, width=width, height=height),
        confidence=confidence,
    )


def first_document(collection: FakeCollection) -> dict[str, Any]:
    return next(iter(collection.documents.values()))


def set_detector(monkeypatch: pytest.MonkeyPatch, detector: StaticDetector) -> None:
    monkeypatch.setattr(
        "app.services.detection_workflow_service.get_face_detector",
        lambda settings: detector,
    )


def test_mediapipe_without_solutions_api_uses_supported_fallback_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "mediapipe", SimpleNamespace())

    with pytest.raises(FaceDetectorUnavailableError):
        MediaPipeFaceDetector(min_confidence=0.6, max_faces=1)


def ready_upload(tmp_path: Path):
    client, users, profiles, uploads, quality, face_reports, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, image_path = seed_upload(uploads, settings, user_id)
    seed_quality_report(quality, upload_id, user_id)
    return client, token, user_id, upload_id, image_path, uploads, quality, face_reports, settings


def analyze(client: TestClient, token: str, upload_id: str):
    return client.post(
        f"/api/face-detection/{upload_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
    )


def test_successful_single_face_detection_through_mocked_detector(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, user_id, upload_id, _, uploads, _, reports, settings = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([face()]))
    response = analyze(client, token, upload_id)
    body = response.json()
    assert response.status_code == 200
    assert body["detection_status"] == "passed"
    assert body["face_count"] == 1
    assert body["detection_confidence"] == 93
    assert body["crop"]["prepared"] is True
    assert first_document(uploads)["status"] == "face_detected"
    report = first_document(reports)
    assert str(report["user_id"]) == user_id
    assert (settings.face_crop_path / report["crop_reference"]).is_file()


def test_reject_unauthenticated_request(tmp_path: Path) -> None:
    client, *_ = create_client(tmp_path)
    response = client.post("/api/face-detection/missing/analyze")
    assert response.status_code == 401


def test_reject_another_users_upload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, users, profiles, uploads, quality, _, settings = create_client(tmp_path)
    _, owner_id = seed_user(users, profiles, email="owner@example.com")
    other_token, _ = seed_user(users, profiles, email="other@example.com")
    upload_id, _ = seed_upload(uploads, settings, owner_id)
    seed_quality_report(quality, upload_id, owner_id)
    set_detector(monkeypatch, StaticDetector([face()]))
    assert analyze(client, other_token, upload_id).status_code == 404


def test_reject_missing_upload(tmp_path: Path) -> None:
    client, users, profiles, *_ = create_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = analyze(client, token, "missing-upload")
    assert response.status_code == 404


def test_reject_expired_upload_and_remove_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, users, profiles, uploads, quality, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, image_path = seed_upload(uploads, settings, user_id, expired=True)
    seed_quality_report(quality, upload_id, user_id)
    set_detector(monkeypatch, StaticDetector([face()]))
    response = analyze(client, token, upload_id)
    assert response.status_code == 410
    assert not image_path.exists()
    assert first_document(uploads)["status"] == "expired"


def test_reject_missing_temporary_file(tmp_path: Path) -> None:
    client, users, profiles, uploads, quality, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, missing_file=True)
    seed_quality_report(quality, upload_id, user_id)
    response = analyze(client, token, upload_id)
    assert response.status_code == 410
    assert first_document(uploads)["status"] == "face_detection_failed"


def test_reject_missing_quality_report(tmp_path: Path) -> None:
    client, users, profiles, uploads, _, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id)
    response = analyze(client, token, upload_id)
    assert response.status_code == 409


def test_reject_failed_quality_report(tmp_path: Path) -> None:
    client, users, profiles, uploads, quality, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, status="quality_failed")
    seed_quality_report(quality, upload_id, user_id, status="failed")
    response = analyze(client, token, upload_id)
    assert response.status_code == 409


def test_allow_accepted_quality_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, users, profiles, uploads, quality, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id, status="face_detection_pending")
    seed_quality_report(quality, upload_id, user_id, status="warning", warning_accepted=True)
    set_detector(monkeypatch, StaticDetector([face()]))
    assert analyze(client, token, upload_id).json()["detection_status"] == "passed"


@pytest.mark.parametrize(
    ("detections", "code"),
    [
        ([], "NO_FACE_DETECTED"),
        ([face(), face(x=0.1, y=0.1, width=0.25, height=0.35)], "MULTIPLE_FACES_DETECTED"),
        ([face(confidence=0.3)], "LOW_FACE_DETECTION_CONFIDENCE"),
        ([face(width=-0.3)], "INVALID_FACE_BOUNDING_BOX"),
        ([face(width=0.2, height=0.2)], "FACE_TOO_SMALL"),
        ([face(x=0.02, y=0.02, width=0.95, height=0.95)], "FACE_TOO_CLOSE"),
    ],
)
def test_failed_face_detection_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    detections: list[DetectedFace],
    code: str,
) -> None:
    client, token, _, upload_id, _, uploads, _, _, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector(detections))
    body = analyze(client, token, upload_id).json()
    assert body["detection_status"] == "failed"
    assert body["can_continue"] is False
    assert any(issue["code"] == code for issue in body["issues"])
    assert first_document(uploads)["status"] == "face_detection_failed"


def test_slightly_off_center_face_returns_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, _, uploads, _, _, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([face(x=0.41, y=0.25, width=0.5, height=0.5)]))
    body = analyze(client, token, upload_id).json()
    assert body["detection_status"] == "warning"
    assert body["face_position"] == "slightly_off_center"
    assert any(issue["code"] == "FACE_SLIGHTLY_OFF_CENTER" for issue in body["issues"])
    assert first_document(uploads)["status"] == "face_detection_warning"


def test_severely_off_center_face_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, _, _, _, _, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([face(x=0.6, y=0.25, width=0.35, height=0.45)]))
    body = analyze(client, token, upload_id).json()
    assert body["detection_status"] == "failed"
    assert any(issue["code"] == "FACE_NOT_CENTERED" for issue in body["issues"])


def test_boundary_touch_returns_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, _, _, _, _, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([face(x=0.01, y=0.2, width=0.6, height=0.5)]))
    body = analyze(client, token, upload_id).json()
    assert body["detection_status"] == "warning"
    assert any(issue["code"] == "FACE_TOUCHES_LEFT_EDGE" for issue in body["issues"])


def test_coordinate_clamping_allows_safe_partial_box(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, _, _, _, reports, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([face(x=-0.01, y=0.2, width=0.65, height=0.5)]))
    body = analyze(client, token, upload_id).json()
    assert body["detection_status"] == "warning"
    assert any(issue["code"] == "FACE_PARTIALLY_OUTSIDE_IMAGE" for issue in body["issues"])
    assert first_document(reports)["bounding_box_pixels"]["x"] == 0
    assert normalized_to_pixel_box(face(x=-0.01, width=0.55).bounding_box, 400, 400).x == 0


def test_successful_padded_crop_is_created(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, _, _, _, reports, settings = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([face()]))
    analyze(client, token, upload_id)
    report = first_document(reports)
    assert report["crop_width"] > report["bounding_box_pixels"]["width"]
    assert report["crop_height"] > report["bounding_box_pixels"]["height"]
    assert (settings.face_crop_path / report["crop_reference"]).is_file()


def test_crop_too_small_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, users, profiles, uploads, quality, _, settings = create_client(
        tmp_path,
        face_min_crop_width=390,
        face_min_crop_height=390,
    )
    token, user_id = seed_user(users, profiles)
    upload_id, _ = seed_upload(uploads, settings, user_id)
    seed_quality_report(quality, upload_id, user_id)
    set_detector(monkeypatch, StaticDetector([face(x=0.25, y=0.25, width=0.5, height=0.5)]))
    body = analyze(client, token, upload_id).json()
    assert body["detection_status"] == "failed"
    assert any(issue["code"] == "FACE_CROP_TOO_SMALL" for issue in body["issues"])


def test_crop_storage_uses_randomized_name_and_safe_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, image_path, _, _, reports, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([face()]))
    response = analyze(client, token, upload_id)
    report = first_document(reports)
    assert image_path.name not in report["crop_reference"]
    assert report["crop_reference"].endswith(".jpg")
    assert "crop_reference" not in response.text
    assert "storage" not in response.text
    assert "path" not in response.text


def test_existing_report_is_updated_without_duplicate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, _, _, _, reports, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([face()]))
    first = analyze(client, token, upload_id).json()
    set_detector(monkeypatch, StaticDetector([face(x=0.41, y=0.25, width=0.5, height=0.5)]))
    second = analyze(client, token, upload_id).json()
    assert len(reports.documents) == 1
    assert first["face_report_id"] == second["face_report_id"]
    assert first["created_at"] == second["created_at"]
    assert second["updated_at"] >= first["updated_at"]
    assert second["detection_status"] == "warning"


def test_get_existing_report_does_not_rerun_detection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, _, _, _, reports, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([face()]))
    analyze(client, token, upload_id)
    before = first_document(reports).copy()
    set_detector(monkeypatch, StaticDetector([]))
    response = client.get(
        f"/api/face-detection/{upload_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["detection_status"] == "passed"
    assert first_document(reports)["updated_at"] == before["updated_at"]


def test_reject_get_report_for_another_user(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, users, profiles, uploads, quality, _, settings = create_client(tmp_path)
    owner_token, owner_id = seed_user(users, profiles, email="owner2@example.com")
    other_token, _ = seed_user(users, profiles, email="other2@example.com")
    upload_id, _ = seed_upload(uploads, settings, owner_id)
    seed_quality_report(quality, upload_id, owner_id)
    set_detector(monkeypatch, StaticDetector([face()]))
    analyze(client, owner_token, upload_id)
    response = client.get(
        f"/api/face-detection/{upload_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 404


def test_warning_acceptance_works(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, _, uploads, _, reports, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([face(x=0.41, y=0.25, width=0.5, height=0.5)]))
    analyze(client, token, upload_id)
    response = client.post(
        f"/api/face-detection/{upload_id}/accept-warning",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["can_continue"] is True
    assert response.json()["next_route"] == "/image-preprocessing"
    assert first_document(reports)["warning_accepted"] is True
    assert first_document(uploads)["status"] == "preprocessing_pending"


def test_failed_result_cannot_accept_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, _, _, _, _, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector([]))
    analyze(client, token, upload_id)
    response = client.post(
        f"/api/face-detection/{upload_id}/accept-warning",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


def test_parent_upload_deletion_removes_crop_and_reports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, image_path, _, quality, face_reports, settings = ready_upload(
        tmp_path
    )
    set_detector(monkeypatch, StaticDetector([face()]))
    analyze(client, token, upload_id)
    crop_path = settings.face_crop_path / first_document(face_reports)["crop_reference"]
    response = client.delete(
        f"/api/uploads/{upload_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert not image_path.exists()
    assert not crop_path.exists()
    assert len(quality.documents) == 0
    assert len(face_reports.documents) == 0


@pytest.mark.asyncio
async def test_expired_crop_cleanup_removes_private_file(tmp_path: Path) -> None:
    _, _, _, _, _, face_reports, settings = create_client(tmp_path)
    crop_directory = settings.face_crop_path / "abc" / "def"
    crop_directory.mkdir(parents=True, exist_ok=True)
    crop_path = crop_directory / "expired.jpg"
    crop_path.write_bytes(b"expired-crop")
    report_id = ObjectId()
    face_reports.documents[report_id] = {
        "_id": report_id,
        "upload_id": str(uuid4()),
        "user_id": ObjectId(),
        "crop_reference": crop_path.relative_to(settings.face_crop_path).as_posix(),
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    cleaned = await cleanup_expired_face_crops(face_reports, settings)
    assert cleaned == 1
    assert not crop_path.exists()
    assert len(face_reports.documents) == 0


def test_detector_exception_returns_safe_error_and_restores_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, token, _, upload_id, _, uploads, _, _, _ = ready_upload(tmp_path)
    set_detector(monkeypatch, StaticDetector(raises=True))
    response = analyze(client, token, upload_id)
    assert response.status_code == 500
    assert "detector exploded" not in response.text
    assert first_document(uploads)["status"] == "quality_passed"


def test_invalid_face_threshold_configuration_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        make_settings(
            tmp_path / "uploads",
            tmp_path / "crops",
            face_min_area_ratio=0.9,
            face_max_area_ratio=0.5,
        )
