import os
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

os.environ.setdefault("APP_NAME", "DermaScan AI")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("API_PREFIX", "/api")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DATABASE", "dermascan_ai_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-upload-tests-at-least-32-bytes")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from PIL import Image

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
from app.services.upload_service import cleanup_expired_uploads


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class DeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self.documents = iter(documents)

    def __aiter__(self) -> "FakeCursor":
        return self

    async def __anext__(self) -> dict[str, Any]:
        try:
            return next(self.documents)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


def matches_query(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        actual = document.get(key)
        if isinstance(expected, dict):
            if "$lte" in expected and not actual <= expected["$lte"]:
                return False
            if "$ne" in expected and actual == expected["$ne"]:
                return False
        elif actual != expected:
            return False
    return True


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[ObjectId, dict[str, Any]] = {}

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for document in self.documents.values():
            if matches_query(document, query):
                return document.copy()
        return None

    def find(self, query: dict[str, Any]) -> FakeCursor:
        return FakeCursor(
            [
                document.copy()
                for document in self.documents.values()
                if matches_query(document, query)
            ]
        )

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        inserted_id = ObjectId()
        self.documents[inserted_id] = {**document, "_id": inserted_id}
        return InsertOneResult(inserted_id)

    async def update_one(self, query: dict[str, Any], operation: dict[str, Any]) -> None:
        for document in self.documents.values():
            if matches_query(document, query):
                document.update(operation["$set"])
                return

    async def delete_one(self, query: dict[str, Any]) -> DeleteResult:
        for document_id, document in list(self.documents.items()):
            if matches_query(document, query):
                del self.documents[document_id]
                return DeleteResult(1)
        return DeleteResult(0)


def make_test_settings(upload_directory: Path) -> Settings:
    return Settings(
        app_name="DermaScan AI",
        app_env="testing",
        api_prefix="/api",
        mongodb_url="mongodb://localhost:27017",
        mongodb_database="dermascan_ai_test",
        jwt_secret_key="test-secret-key-for-upload-tests-at-least-32-bytes",
        jwt_algorithm="HS256",
        access_token_expire_minutes=60,
        frontend_origin="http://localhost:5173",
        max_upload_size_mb=1,
        allowed_image_types="image/jpeg,image/png",
        upload_directory=upload_directory,
        temp_upload_expiry_minutes=30,
        min_image_width=300,
        min_image_height=300,
        max_image_width=1000,
        max_image_height=1000,
    )


def create_test_client(
    tmp_path: Path,
) -> tuple[TestClient, FakeCollection, FakeCollection, FakeCollection, Settings]:
    users = FakeCollection()
    profiles = FakeCollection()
    uploads = FakeCollection()
    reports = FakeCollection()
    face_reports = FakeCollection()
    preprocessing_reports = FakeCollection()
    skin_type_reports = FakeCollection()
    settings = make_test_settings(tmp_path / "isolated_uploads")
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_users_collection] = lambda: users
    app.dependency_overrides[get_skin_profiles_collection] = lambda: profiles
    app.dependency_overrides[get_image_uploads_collection] = lambda: uploads
    app.dependency_overrides[get_image_quality_reports_collection] = lambda: reports
    app.dependency_overrides[get_face_detection_reports_collection] = lambda: face_reports
    app.dependency_overrides[get_image_preprocessing_reports_collection] = (
        lambda: preprocessing_reports
    )
    app.dependency_overrides[get_skin_type_reports_collection] = lambda: skin_type_reports
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app), users, profiles, uploads, settings


def seed_user(
    users: FakeCollection,
    profiles: FakeCollection,
    *,
    complete_profile: bool = True,
    email: str = "upload@example.com",
) -> tuple[str, str]:
    user_id = ObjectId()
    now = datetime.now(timezone.utc)
    users.documents[user_id] = {
        "_id": user_id,
        "full_name": "Upload Test User",
        "email": email,
        "password_hash": "not-used-in-upload-tests",
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


def image_bytes(
    image_format: str = "JPEG",
    size: tuple[int, int] = (400, 400),
    *,
    include_exif: bool = False,
) -> bytes:
    output = BytesIO()
    image = Image.new("RGB", size, color=(120, 170, 190))
    save_options: dict[str, Any] = {}
    if include_exif:
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = "temporary test metadata"
        save_options["exif"] = exif
    image.save(output, format=image_format, **save_options)
    return output.getvalue()


def upload_image(
    client: TestClient,
    token: str,
    *,
    content: bytes | None = None,
    filename: str = "face.jpg",
    mime_type: str = "image/jpeg",
    consent: str | None = "true",
):
    data = {} if consent is None else {"consent_given": consent}
    return client.post(
        "/api/uploads/face-image",
        headers={"Authorization": f"Bearer {token}"},
        data=data,
        files={"file": (filename, content or image_bytes(), mime_type)},
    )


def first_upload(uploads: FakeCollection) -> dict[str, Any]:
    return next(iter(uploads.documents.values()))


def test_successful_jpeg_upload(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token)
    assert response.status_code == 201
    assert response.json()["file"]["format"] == "JPEG"


def test_successful_png_upload(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(
        client,
        token,
        content=image_bytes("PNG"),
        filename="face.png",
        mime_type="image/png",
    )
    assert response.status_code == 201
    assert response.json()["file"]["format"] == "PNG"


def test_reject_unauthenticated_request(tmp_path: Path) -> None:
    client, _, _, _, _ = create_test_client(tmp_path)
    response = client.post(
        "/api/uploads/face-image",
        data={"consent_given": "true"},
        files={"file": ("face.jpg", image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 401


def test_reject_incomplete_skin_profile(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles, complete_profile=False)
    response = upload_image(client, token)
    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Complete your skin profile before uploading a facial image."
    )


def test_reject_missing_consent(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token, consent=None)
    assert response.status_code == 400
    assert "Consent is required" in response.json()["detail"]


def test_reject_false_consent(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token, consent="false")
    assert response.status_code == 400


def test_reject_oversized_file(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token, content=b"x" * (1024 * 1024 + 1))
    assert response.status_code == 413
    assert "1 MB upload limit" in response.json()["detail"]


def test_reject_unsupported_extension(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token, filename="face.gif")
    assert response.status_code == 400
    assert response.json()["detail"] == "Only JPG, JPEG, and PNG images are supported."


def test_reject_path_traversal_filename(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token, filename="../../face.jpg")
    assert response.status_code == 400


def test_reject_unsupported_mime_type(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token, mime_type="application/octet-stream")
    assert response.status_code == 400


def test_reject_fake_image_disguised_as_jpg(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token, content=b"This is not an image.")
    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is not a valid image."


def test_reject_corrupted_image(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token, content=b"\xff\xd8\xff\xe0corrupted")
    assert response.status_code == 400


def test_reject_image_below_minimum_dimensions(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token, content=image_bytes(size=(299, 400)))
    assert response.status_code == 400
    assert "at least 300 x 300" in response.json()["detail"]


def test_reject_image_above_maximum_dimensions(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(client, token, content=image_bytes(size=(1001, 400)))
    assert response.status_code == 400
    assert "must not exceed 1000 x 1000" in response.json()["detail"]


def test_create_upload_database_record(tmp_path: Path) -> None:
    client, users, profiles, uploads, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    assert upload_image(client, token).status_code == 201
    document = first_upload(uploads)
    assert document["status"] == "validated"
    assert document["consent_given"] is True
    assert document["stored_filename"] != "face.jpg"


def test_store_authenticated_user_ownership(tmp_path: Path) -> None:
    client, users, profiles, uploads, _ = create_test_client(tmp_path)
    token, user_id = seed_user(users, profiles)
    upload_image(client, token)
    assert first_upload(uploads)["user_id"] == ObjectId(user_id)


def test_return_only_safe_upload_metadata(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    data = upload_image(client, token).json()
    assert set(data) == {
        "upload_id",
        "status",
        "file",
        "created_at",
        "expires_at",
        "next_route",
    }
    assert "storage_reference" not in str(data)
    assert "stored_filename" not in str(data)


def test_sanitized_copy_removes_exif_and_normalizes_orientation(tmp_path: Path) -> None:
    client, users, profiles, uploads, settings = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    response = upload_image(
        client,
        token,
        content=image_bytes(size=(400, 500), include_exif=True),
    )
    assert response.status_code == 201
    assert response.json()["file"]["width"] == 500
    document = first_upload(uploads)
    stored_path = settings.upload_path / document["storage_reference"]
    with Image.open(stored_path) as stored_image:
        assert len(stored_image.getexif()) == 0


def test_get_owned_upload_status(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    upload_id = upload_image(client, token).json()["upload_id"]
    response = client.get(
        f"/api/uploads/{upload_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["upload_id"] == upload_id


def test_get_upload_status_handles_mongodb_naive_datetime(tmp_path: Path) -> None:
    client, users, profiles, uploads, _ = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    upload_id = upload_image(client, token).json()["upload_id"]
    document = first_upload(uploads)
    document["expires_at"] = document["expires_at"].replace(tzinfo=None)

    response = client.get(
        f"/api/uploads/{upload_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "validated"


def test_reject_access_to_another_users_upload(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    first_token, _ = seed_user(users, profiles, email="first@example.com")
    second_token, _ = seed_user(users, profiles, email="second@example.com")
    upload_id = upload_image(client, first_token).json()["upload_id"]
    response = client.get(
        f"/api/uploads/{upload_id}",
        headers={"Authorization": f"Bearer {second_token}"},
    )
    assert response.status_code == 404


def test_reject_deleting_another_users_upload(tmp_path: Path) -> None:
    client, users, profiles, _, _ = create_test_client(tmp_path)
    first_token, _ = seed_user(users, profiles, email="first@example.com")
    second_token, _ = seed_user(users, profiles, email="second@example.com")
    upload_id = upload_image(client, first_token).json()["upload_id"]
    response = client.delete(
        f"/api/uploads/{upload_id}",
        headers={"Authorization": f"Bearer {second_token}"},
    )
    assert response.status_code == 404


def test_delete_owned_temporary_upload(tmp_path: Path) -> None:
    client, users, profiles, uploads, settings = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    upload_id = upload_image(client, token).json()["upload_id"]
    document = first_upload(uploads)
    stored_path = settings.upload_path / document["storage_reference"]
    assert stored_path.exists()
    response = client.delete(
        f"/api/uploads/{upload_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert not stored_path.exists()
    assert not uploads.documents


@pytest.mark.asyncio
async def test_cleanup_expired_upload(tmp_path: Path) -> None:
    client, users, profiles, uploads, settings = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    upload_image(client, token)
    document = first_upload(uploads)
    document["expires_at"] = datetime.now(timezone.utc) - timedelta(minutes=1)
    stored_path = settings.upload_path / document["storage_reference"]
    cleaned = await cleanup_expired_uploads(uploads, settings)
    assert cleaned == 1
    assert not stored_path.exists()
    assert first_upload(uploads)["status"] == "expired"


def test_delete_handles_missing_temporary_file(tmp_path: Path) -> None:
    client, users, profiles, uploads, settings = create_test_client(tmp_path)
    token, _ = seed_user(users, profiles)
    upload_id = upload_image(client, token).json()["upload_id"]
    document = first_upload(uploads)
    (settings.upload_path / document["storage_reference"]).unlink()
    response = client.delete(
        f"/api/uploads/{upload_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert not uploads.documents
