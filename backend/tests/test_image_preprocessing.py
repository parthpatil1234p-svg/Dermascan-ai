from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2
import numpy as np
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
from app.core.model_input_config import get_model_input_contract
from app.core.security import create_access_token
from app.main import create_app
from app.services.image_preprocessing_service import (
    cleanup_expired_preprocessed_images,
)
from app.services.image_transform_service import (
    apply_conservative_denoise,
    transform_face_crop,
)
from app.utils.image_colour import decode_image_to_rgb
from app.utils.image_normalization import prepare_inference_tensor
from app.utils.image_resize import letterbox_resize


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self.documents = iter(documents)

    def __aiter__(self):
        return self

    async def __anext__(self) -> dict[str, Any]:
        try:
            return next(self.documents).copy()
        except StopIteration as exc:
            raise StopAsyncIteration from exc


def value_matches(value: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if "$lte" in expected:
            return value <= expected["$lte"]
        if "$ne" in expected:
            return value != expected["$ne"]
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


def make_settings(tmp_path: Path, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "app_name": "DermaScan AI",
        "app_env": "testing",
        "api_prefix": "/api",
        "mongodb_url": "mongodb://localhost:27017",
        "mongodb_database": "dermascan_preprocessing_test",
        "jwt_secret_key": "preprocessing-test-secret-key-at-least-32-bytes",
        "jwt_algorithm": "HS256",
        "access_token_expire_minutes": 60,
        "frontend_origin": "http://localhost:5173",
        "upload_directory": tmp_path / "uploads",
        "face_crop_directory": tmp_path / "face-crops",
        "preprocessed_image_directory": tmp_path / "processed",
        "temp_upload_expiry_minutes": 30,
        "face_crop_expiry_minutes": 30,
        "preprocessed_image_expiry_minutes": 30,
        "preprocess_enable_denoise": False,
    }
    values.update(overrides)
    return Settings(**values)


def create_client(tmp_path: Path, **settings_overrides: Any):
    collections = [FakeCollection() for _ in range(6)]
    users, profiles, uploads, quality, faces, preprocessing = collections
    skin_type_reports = FakeCollection()
    settings = make_settings(tmp_path, **settings_overrides)
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_users_collection] = lambda: users
    app.dependency_overrides[get_skin_profiles_collection] = lambda: profiles
    app.dependency_overrides[get_image_uploads_collection] = lambda: uploads
    app.dependency_overrides[get_image_quality_reports_collection] = lambda: quality
    app.dependency_overrides[get_face_detection_reports_collection] = lambda: faces
    app.dependency_overrides[get_image_preprocessing_reports_collection] = lambda: preprocessing
    app.dependency_overrides[get_skin_type_reports_collection] = lambda: skin_type_reports
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app), *collections, settings


def seed_user(
    users: FakeCollection,
    profiles: FakeCollection,
    *,
    email: str = "preprocess@example.com",
    complete_profile: bool = True,
) -> tuple[str, str]:
    user_id = ObjectId()
    now = datetime.now(timezone.utc)
    users.documents[user_id] = {
        "_id": user_id,
        "full_name": "Preprocessing Test User",
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


def synthetic_rgb(width: int, height: int) -> np.ndarray:
    x = np.linspace(30, 220, width, dtype=np.uint8)
    y = np.linspace(20, 200, height, dtype=np.uint8)[:, None]
    red = np.broadcast_to(x, (height, width))
    green = np.broadcast_to(y, (height, width))
    blue = ((red.astype(np.uint16) + green.astype(np.uint16)) // 2).astype(np.uint8)
    return np.dstack((red, green, blue))


def write_crop(path: Path, width: int = 320, height: int = 400, mode: str = "RGB") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rgb = synthetic_rgb(width, height)
    if mode == "RGB":
        Image.fromarray(rgb, "RGB").save(path)
    elif mode == "L":
        Image.fromarray(rgb[:, :, 0], "L").save(path)
    elif mode == "RGBA":
        alpha = np.linspace(0, 255, width, dtype=np.uint8)
        alpha = np.broadcast_to(alpha, (height, width))
        Image.fromarray(np.dstack((rgb, alpha)), "RGBA").save(path)
    else:
        raise ValueError(mode)


def seed_workflow(
    uploads: FakeCollection,
    quality: FakeCollection,
    faces: FakeCollection,
    settings: Settings,
    user_id: str,
    *,
    quality_status: str = "passed",
    quality_warning_accepted: bool = False,
    face_status: str = "passed",
    face_warning_accepted: bool = False,
    crop_missing: bool = False,
    crop_expired: bool = False,
    crop_width: int = 320,
    crop_height: int = 400,
    crop_mode: str = "RGB",
) -> tuple[str, Path]:
    upload_id = str(uuid4())
    now = datetime.now(timezone.utc)
    upload_folder = settings.upload_path / user_id[:12]
    upload_folder.mkdir(parents=True, exist_ok=True)
    source_path = upload_folder / f"{uuid4().hex}.jpg"
    write_crop(source_path, 400, 400)
    upload_document_id = ObjectId()
    uploads.documents[upload_document_id] = {
        "_id": upload_document_id,
        "upload_id": upload_id,
        "user_id": ObjectId(user_id),
        "storage_reference": source_path.relative_to(settings.upload_path).as_posix(),
        "status": "face_detected",
        "consent_given": True,
        "created_at": now,
        "updated_at": now,
        "expires_at": now + timedelta(minutes=30),
    }
    quality_id = ObjectId()
    quality.documents[quality_id] = {
        "_id": quality_id,
        "quality_report_id": str(uuid4()),
        "upload_id": upload_id,
        "user_id": ObjectId(user_id),
        "quality_status": quality_status,
        "warning_accepted": quality_warning_accepted,
        "created_at": now,
        "updated_at": now,
    }
    crop_folder = settings.face_crop_path / user_id[:12] / upload_id[:12]
    crop_path = crop_folder / f"{uuid4().hex}.png"
    if not crop_missing:
        write_crop(crop_path, crop_width, crop_height, crop_mode)
    face_id = ObjectId()
    faces.documents[face_id] = {
        "_id": face_id,
        "face_report_id": str(uuid4()),
        "quality_report_id": quality.documents[quality_id]["quality_report_id"],
        "upload_id": upload_id,
        "user_id": ObjectId(user_id),
        "detection_status": face_status,
        "warning_accepted": face_warning_accepted,
        "crop_reference": crop_path.relative_to(settings.face_crop_path).as_posix(),
        "crop_expires_at": (
            now - timedelta(minutes=1) if crop_expired else now + timedelta(minutes=30)
        ),
        "expires_at": now + timedelta(minutes=30),
        "created_at": now,
        "updated_at": now,
    }
    return upload_id, crop_path


def ready_workflow(tmp_path: Path, **workflow_overrides: Any):
    client, users, profiles, uploads, quality, faces, preprocessing, settings = create_client(
        tmp_path
    )
    token, user_id = seed_user(users, profiles)
    upload_id, crop_path = seed_workflow(
        uploads, quality, faces, settings, user_id, **workflow_overrides
    )
    return (
        client,
        token,
        user_id,
        upload_id,
        crop_path,
        uploads,
        quality,
        faces,
        preprocessing,
        settings,
    )


def process(client: TestClient, token: str, upload_id: str):
    return client.post(
        f"/api/image-preprocessing/{upload_id}/process",
        headers={"Authorization": f"Bearer {token}"},
    )


def first_document(collection: FakeCollection) -> dict[str, Any]:
    return next(iter(collection.documents.values()))


def test_successful_preprocessing(tmp_path: Path) -> None:
    client, token, _, upload_id, _, _, _, _, reports, _ = ready_workflow(tmp_path)
    response = process(client, token, upload_id)
    assert response.status_code == 200
    assert response.json()["preprocessing_status"] == "completed"
    assert len(reports.documents) == 1


def test_reject_unauthenticated_request(tmp_path: Path) -> None:
    client, *_ = create_client(tmp_path)
    assert client.post("/api/image-preprocessing/missing/process").status_code == 401


def test_reject_another_users_upload(tmp_path: Path) -> None:
    client, users, profiles, uploads, quality, faces, _, settings = create_client(tmp_path)
    _, owner_id = seed_user(users, profiles, email="owner@example.com")
    other_token, _ = seed_user(users, profiles, email="other@example.com")
    upload_id, _ = seed_workflow(uploads, quality, faces, settings, owner_id)
    assert process(client, other_token, upload_id).status_code == 404


def test_reject_missing_upload(tmp_path: Path) -> None:
    client, users, profiles, *_ = create_client(tmp_path)
    token, _ = seed_user(users, profiles)
    assert process(client, token, "missing").status_code == 404


def test_reject_incomplete_skin_profile(tmp_path: Path) -> None:
    client, users, profiles, uploads, quality, faces, _, settings = create_client(tmp_path)
    token, user_id = seed_user(users, profiles, complete_profile=False)
    upload_id, _ = seed_workflow(uploads, quality, faces, settings, user_id)
    assert process(client, token, upload_id).status_code == 403


def test_reject_missing_quality_report(tmp_path: Path) -> None:
    client, token, _, upload_id, _, _, quality, _, _, _ = ready_workflow(tmp_path)
    quality.documents.clear()
    assert process(client, token, upload_id).status_code == 409


def test_reject_failed_quality_report(tmp_path: Path) -> None:
    client, token, _, upload_id, *_ = ready_workflow(tmp_path, quality_status="failed")
    assert process(client, token, upload_id).status_code == 409


def test_reject_missing_face_detection_report(tmp_path: Path) -> None:
    client, token, _, upload_id, _, _, _, faces, _, _ = ready_workflow(tmp_path)
    faces.documents.clear()
    assert process(client, token, upload_id).status_code == 409


def test_reject_failed_face_detection(tmp_path: Path) -> None:
    client, token, _, upload_id, *_ = ready_workflow(tmp_path, face_status="failed")
    assert process(client, token, upload_id).status_code == 409


def test_reject_missing_crop(tmp_path: Path) -> None:
    client, token, _, upload_id, *_ = ready_workflow(tmp_path, crop_missing=True)
    assert process(client, token, upload_id).status_code == 410


def test_reject_expired_crop_and_remove_it(tmp_path: Path) -> None:
    client, token, _, upload_id, crop_path, *_ = ready_workflow(tmp_path, crop_expired=True)
    assert process(client, token, upload_id).status_code == 410
    assert not crop_path.exists()


def test_decode_rgb_image(tmp_path: Path) -> None:
    path = tmp_path / "rgb.png"
    write_crop(path)
    decoded = decode_image_to_rgb(path)
    assert decoded.image.shape == (400, 320, 3)
    assert decoded.source_colour_space == "BGR"


def test_decode_grayscale_image_safely(tmp_path: Path) -> None:
    path = tmp_path / "gray.png"
    write_crop(path, mode="L")
    decoded = decode_image_to_rgb(path)
    assert decoded.image.shape == (400, 320, 3)
    assert decoded.source_colour_space == "GRAYSCALE"


def test_decode_rgba_image_safely(tmp_path: Path) -> None:
    path = tmp_path / "rgba.png"
    write_crop(path, mode="RGBA")
    decoded = decode_image_to_rgb(path, alpha_background=127)
    assert decoded.image.shape == (400, 320, 3)
    assert decoded.alpha_composited is True


def test_correct_bgr_to_rgb_conversion(tmp_path: Path) -> None:
    path = tmp_path / "colours.png"
    bgr = np.zeros((12, 12, 3), dtype=np.uint8)
    bgr[:] = (10, 20, 230)
    cv2.imwrite(str(path), bgr)
    rgb = decode_image_to_rgb(path).image
    assert tuple(rgb[0, 0]) == (230, 20, 10)


def test_letterbox_resize_preserves_aspect_ratio() -> None:
    result = letterbox_resize(np.ones((200, 100, 3), dtype=np.uint8), 224, 224)
    assert result.image.shape == (224, 224, 3)
    assert result.scale == pytest.approx(1.12)


def test_letterbox_padding_calculation() -> None:
    result = letterbox_resize(np.ones((200, 100, 3), dtype=np.uint8), 224, 224)
    assert result.padding.left == 56
    assert result.padding.right == 56
    assert result.padding.top == 0
    assert result.padding.bottom == 0


def test_output_size_matches_contract(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    path = tmp_path / "crop.png"
    write_crop(path)
    result = transform_face_crop(path, settings)
    assert result.image.shape[:2] == (224, 224)


def test_output_has_three_channels(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    path = tmp_path / "gray.png"
    write_crop(path, mode="L")
    assert transform_face_crop(path, settings).image.shape[2] == 3


def test_output_tensor_range_is_valid(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    path = tmp_path / "crop.png"
    write_crop(path)
    result = transform_face_crop(path, settings)
    tensor = prepare_inference_tensor(result.image, get_model_input_contract(settings))
    assert tensor.dtype == np.float32
    assert float(tensor.min()) >= 0.0
    assert float(tensor.max()) <= 1.0


def test_output_tensor_has_no_nan_or_infinite_values(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    path = tmp_path / "crop.png"
    write_crop(path)
    result = transform_face_crop(path, settings)
    tensor = prepare_inference_tensor(result.image, get_model_input_contract(settings))
    assert np.isfinite(tensor).all()


def test_mild_denoising_does_not_change_dimensions(tmp_path: Path) -> None:
    settings = make_settings(
        tmp_path,
        preprocess_enable_denoise=True,
        preprocess_noise_threshold=0,
        blur_fail_threshold=0,
        blur_warning_threshold=1,
    )
    image = synthetic_rgb(320, 400)
    denoised, applied = apply_conservative_denoise(image, settings)
    assert denoised.shape == image.shape
    assert applied is True


def test_disabled_clahe_is_not_applied(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, preprocess_enable_clahe=False)
    path = tmp_path / "crop.png"
    write_crop(path)
    assert transform_face_crop(path, settings).clahe_applied is False


def test_disabled_sharpening_is_not_applied(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, preprocess_enable_sharpening=False)
    path = tmp_path / "crop.png"
    write_crop(path)
    assert transform_face_crop(path, settings).sharpening_applied is False


def test_significant_upscaling_generates_warning(tmp_path: Path) -> None:
    client, token, _, upload_id, *_ = ready_workflow(tmp_path, crop_width=100, crop_height=100)
    response = process(client, token, upload_id)
    assert response.json()["preprocessing_status"] == "warning"
    assert any(
        issue["code"] == "SIGNIFICANT_UPSCALING_REQUIRED" for issue in response.json()["issues"]
    )


def test_output_file_uses_randomized_name(tmp_path: Path) -> None:
    client, token, _, upload_id, crop_path, _, _, _, reports, _ = ready_workflow(tmp_path)
    process(client, token, upload_id)
    reference = first_document(reports)["processed_image_reference"]
    assert crop_path.name not in reference
    assert Path(reference).suffix == ".jpg"


def test_physical_path_is_not_exposed(tmp_path: Path) -> None:
    client, token, _, upload_id, _, _, _, _, _, settings = ready_workflow(tmp_path)
    response = process(client, token, upload_id)
    assert "processed_image_reference" not in response.text
    assert str(settings.preprocessed_image_path) not in response.text


def test_report_is_stored_with_ownership(tmp_path: Path) -> None:
    client, token, user_id, upload_id, _, _, _, _, reports, _ = ready_workflow(tmp_path)
    process(client, token, upload_id)
    report = first_document(reports)
    assert str(report["user_id"]) == user_id
    assert report["upload_id"] == upload_id


def test_existing_report_is_updated(tmp_path: Path) -> None:
    client, token, _, upload_id, _, _, _, _, reports, settings = ready_workflow(tmp_path)
    first = process(client, token, upload_id).json()
    old_reference = first_document(reports)["processed_image_reference"]
    second = process(client, token, upload_id).json()
    assert len(reports.documents) == 1
    assert first["preprocessing_report_id"] == second["preprocessing_report_id"]
    assert not (settings.preprocessed_image_path / old_reference).exists()


def test_workflow_status_updates_to_skin_type_pending(tmp_path: Path) -> None:
    client, token, _, upload_id, _, uploads, *_ = ready_workflow(tmp_path)
    process(client, token, upload_id)
    assert first_document(uploads)["status"] == "skin_type_analysis_pending"


def test_parent_upload_deletion_removes_processed_file(tmp_path: Path) -> None:
    client, token, _, upload_id, _, _, _, _, reports, settings = ready_workflow(tmp_path)
    process(client, token, upload_id)
    processed_path = (
        settings.preprocessed_image_path / first_document(reports)["processed_image_reference"]
    )
    response = client.delete(
        f"/api/uploads/{upload_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert not processed_path.exists()
    assert len(reports.documents) == 0


@pytest.mark.asyncio
async def test_expiry_cleanup_removes_processed_file(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    reports = FakeCollection()
    processed_path = settings.preprocessed_image_path / "a" / "b" / "expired.jpg"
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    processed_path.write_bytes(b"expired")
    report_id = ObjectId()
    reports.documents[report_id] = {
        "_id": report_id,
        "processed_image_reference": processed_path.relative_to(
            settings.preprocessed_image_path
        ).as_posix(),
        "preprocessing_status": "completed",
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    assert await cleanup_expired_preprocessed_images(reports, settings) == 1
    assert not processed_path.exists()
    assert first_document(reports)["preprocessing_status"] == "expired"


def test_processing_exception_returns_safe_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, token, _, upload_id, _, uploads, *_ = ready_workflow(tmp_path)
    monkeypatch.setattr(
        "app.services.image_preprocessing_service.transform_face_crop",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("secret failure")),
    )
    response = process(client, token, upload_id)
    assert response.status_code == 500
    assert "secret failure" not in response.text
    assert first_document(uploads)["status"] == "face_detected"


def test_model_input_contract_remains_consistent(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    contract = get_model_input_contract(settings)
    assert contract.to_dict() == {
        "width": 224,
        "height": 224,
        "channels": 3,
        "colour_space": "RGB",
        "data_type": "float32",
        "normalization": "zero_to_one",
        "pixel_range": (0.0, 1.0),
        "resize_mode": "letterbox",
        "channel_order": "RGB",
    }
