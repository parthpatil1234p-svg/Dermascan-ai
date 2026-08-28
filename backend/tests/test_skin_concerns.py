from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from PIL import Image

from app.api.dependencies import (
    get_image_preprocessing_reports_collection,
    get_image_uploads_collection,
    get_skin_concern_reports_collection,
    get_skin_profiles_collection,
    get_skin_type_reports_collection,
    get_users_collection,
)
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.core.skin_concern_labels import CONCERN_LABELS
from app.main import create_app
from app.ml.skin_concern_model_loader import (
    ConcernModelMetadataError,
    ConcernModelUnavailableError,
    SkinConcernModelBundle,
    load_skin_concern_model_bundle,
)
from app.ml.skin_concern_registry import (
    SkinConcernModelRegistry,
    get_skin_concern_model_registry,
)
from app.services.skin_concern_inference_service import (
    ConcernInferenceError,
    parse_concern_scores,
)


class Result:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


def matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    return all(document.get(key) == value for key, value in query.items())


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[ObjectId, dict[str, Any]] = {}

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        return next((item.copy() for item in self.documents.values() if matches(item, query)), None)

    async def insert_one(self, document: dict[str, Any]) -> Result:
        key = ObjectId()
        self.documents[key] = {**document, "_id": key}
        return Result(key)

    async def update_one(self, query: dict[str, Any], operation: dict[str, Any]) -> None:
        for document in self.documents.values():
            if matches(document, query):
                document.update(operation["$set"])
                return


class FakeModel:
    input_shape = (None, 224, 224, 3)
    output_shape = (None, 10)

    def __init__(self, output: Any = None, raises: bool = False) -> None:
        self.output = output or [[0.82, 0.2, 0.72, 0.51, 0.1, 0.9, 0.4, 0.3, 0.2, 0.1]]
        self.raises = raises
        self.last_tensor: np.ndarray | None = None

    def predict(self, tensor: np.ndarray, verbose: int = 0) -> Any:
        self.last_tensor = tensor.copy()
        if self.raises:
            raise RuntimeError("private concern model error")
        return self.output


def concern_settings(tmp_path: Path) -> Settings:
    return Settings(
        app_name="DermaScan AI",
        app_env="testing",
        api_prefix="/api",
        mongodb_url="mongodb://localhost:27017",
        mongodb_database="skin_concern_test",
        jwt_secret_key="skin-concern-test-secret-at-least-32-bytes",
        frontend_origin="http://localhost:5173",
        preprocessed_image_directory=tmp_path / "prepared",
        skin_concern_model_file=tmp_path / "concern.keras",
        skin_concern_metadata_file=tmp_path / "metadata.json",
        skin_concern_label_map_file=tmp_path / "labels.json",
        skin_concern_thresholds_file=tmp_path / "thresholds.json",
        preprocess_enable_denoise=False,
    )


def metadata() -> dict[str, Any]:
    return {
        "model_name": "DermaScan Visible Concern Classifier",
        "model_version": "1.0.0-test",
        "architecture": "MobileNetV2",
        "training_date": "2026-08-07T00:00:00+00:00",
        "dataset_version": "licensed-test-dataset-v1",
        "input_width": 224,
        "input_height": 224,
        "input_channels": 3,
        "colour_space": "RGB",
        "normalization": "zero_to_one",
        "resize_mode": "letterbox",
        "output_activation": "sigmoid",
        "labels": list(CONCERN_LABELS),
        "thresholds": {label: 0.5 for label in CONCERN_LABELS},
        "threshold_source": "validation_f1_tuning",
        "metrics": {"macro_f1": 0.5},
    }


def model_bundle(
    model: FakeModel | None = None, *, calibrated: bool = True
) -> SkinConcernModelBundle:
    return SkinConcernModelBundle(
        model=model or FakeModel(),
        metadata=metadata(),
        label_map={index: label for index, label in enumerate(CONCERN_LABELS)},
        thresholds={label: 0.5 for label in CONCERN_LABELS},
        thresholds_calibrated=calibrated,
    )


def write_artifacts(settings: Settings, *, changed_metadata: dict[str, Any] | None = None) -> None:
    settings.skin_concern_model_path.write_bytes(b"model placeholder")
    settings.skin_concern_metadata_path.write_text(
        json.dumps(changed_metadata or metadata()), encoding="utf-8"
    )
    settings.skin_concern_label_map_path.write_text(
        json.dumps({str(i): label for i, label in enumerate(CONCERN_LABELS)}), encoding="utf-8"
    )
    settings.skin_concern_thresholds_path.write_text(
        json.dumps(
            {
                "source": "validation_f1_tuning",
                "calibrated": True,
                "thresholds": {label: 0.5 for label in CONCERN_LABELS},
            }
        ),
        encoding="utf-8",
    )


def create_context(tmp_path: Path, model: FakeModel | None = None):
    users, profiles, uploads, preprocessing, skin_types, concerns = (
        FakeCollection() for _ in range(6)
    )
    settings = concern_settings(tmp_path)
    registry = SkinConcernModelRegistry()
    registry.set_bundle_for_testing(model_bundle(model))
    app = create_app(enable_lifespan=False)

    def use(collection: FakeCollection):
        return lambda: collection

    for dependency, collection in (
        (get_users_collection, users),
        (get_skin_profiles_collection, profiles),
        (get_image_uploads_collection, uploads),
        (get_image_preprocessing_reports_collection, preprocessing),
        (get_skin_type_reports_collection, skin_types),
        (get_skin_concern_reports_collection, concerns),
    ):
        app.dependency_overrides[dependency] = use(collection)
    app.dependency_overrides[get_skin_concern_model_registry] = lambda: registry
    app.dependency_overrides[get_settings] = lambda: settings
    return (
        TestClient(app),
        users,
        profiles,
        uploads,
        preprocessing,
        skin_types,
        concerns,
        settings,
        registry,
    )


def seed(
    context, *, email: str = "concern@example.com", status: str = "skin_concern_analysis_pending"
):
    _, users, profiles, uploads, preprocessing, skin_types, _, settings, _ = context
    user_id = ObjectId()
    now = datetime.now(timezone.utc)
    users.documents[user_id] = {
        "_id": user_id,
        "full_name": "Concern User",
        "email": email,
        "password_hash": "unused",
        "age_group": "18-25",
        "location": "India",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    profiles.documents[ObjectId()] = {
        "_id": ObjectId(),
        "user_id": user_id,
        "is_complete": True,
        "oiliness_level": "High",
        "dryness_level": "Low",
        "is_sensitive": True,
    }
    upload_id = str(uuid4())
    upload_key = ObjectId()
    uploads.documents[upload_key] = {
        "_id": upload_key,
        "upload_id": upload_id,
        "user_id": user_id,
        "status": status,
        "expires_at": now + timedelta(minutes=30),
        "created_at": now,
        "updated_at": now,
    }
    relative = Path(str(user_id)[:12]) / upload_id[:12] / "prepared.jpg"
    path = settings.preprocessed_image_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    image = np.zeros((224, 224, 3), dtype=np.uint8)
    image[..., 0] = np.arange(224, dtype=np.uint8)
    image[..., 1] = 120
    image[..., 2] = 220
    Image.fromarray(image, "RGB").save(path)
    preprocessing.documents[ObjectId()] = {
        "_id": ObjectId(),
        "preprocessing_report_id": str(uuid4()),
        "upload_id": upload_id,
        "user_id": user_id,
        "preprocessing_status": "completed",
        "processed_image_reference": relative.as_posix(),
        "created_at": now,
        "updated_at": now,
    }
    skin_types.documents[ObjectId()] = {
        "_id": ObjectId(),
        "skin_type_report_id": str(uuid4()),
        "upload_id": upload_id,
        "user_id": user_id,
        "result_status": "estimated",
        "created_at": now,
        "updated_at": now,
    }
    return create_access_token(subject=str(user_id)), str(user_id), upload_id, path


def analyze(client: TestClient, token: str, upload_id: str):
    return client.post(
        f"/api/skin-concerns/{upload_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
    )


def test_model_artifacts_load_and_status(tmp_path: Path) -> None:
    settings = concern_settings(tmp_path)
    write_artifacts(settings)
    loaded = load_skin_concern_model_bundle(settings, lambda _: FakeModel())
    assert loaded.thresholds_calibrated is True
    context = create_context(tmp_path)
    response = context[0].get("/api/models/skin-concerns/status")
    assert response.status_code == 200 and response.json()["number_of_labels"] == 10
    assert "path" not in response.text.lower()


def test_missing_artifacts_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ConcernModelUnavailableError):
        load_skin_concern_model_bundle(concern_settings(tmp_path), lambda _: FakeModel())


def test_label_map_mismatch_is_rejected(tmp_path: Path) -> None:
    settings = concern_settings(tmp_path)
    write_artifacts(settings)
    settings.skin_concern_label_map_path.write_text(
        json.dumps({"0": "visible_redness"}), encoding="utf-8"
    )
    with pytest.raises(ConcernModelMetadataError):
        load_skin_concern_model_bundle(settings, lambda _: FakeModel())


def test_threshold_map_mismatch_is_rejected(tmp_path: Path) -> None:
    settings = concern_settings(tmp_path)
    write_artifacts(settings)
    settings.skin_concern_thresholds_path.write_text(
        json.dumps(
            {
                "source": "validation_f1_tuning",
                "calibrated": True,
                "thresholds": {"visible_oiliness": 0.5},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConcernModelMetadataError):
        load_skin_concern_model_bundle(settings, lambda _: FakeModel())


def test_uncalibrated_thresholds_are_rejected(tmp_path: Path) -> None:
    settings = concern_settings(tmp_path)
    write_artifacts(settings)
    settings.skin_concern_thresholds_path.write_text(
        json.dumps(
            {
                "source": "development_default",
                "calibrated": False,
                "thresholds": {label: 0.5 for label in CONCERN_LABELS},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ConcernModelMetadataError):
        load_skin_concern_model_bundle(settings, lambda _: FakeModel())


@pytest.mark.parametrize(
    ("attribute", "shape"),
    [("input_shape", (None, 128, 128, 3)), ("output_shape", (None, 9))],
)
def test_model_shape_mismatch_is_rejected(
    tmp_path: Path, attribute: str, shape: tuple[Any, ...]
) -> None:
    settings = concern_settings(tmp_path)
    write_artifacts(settings)
    model = FakeModel()
    setattr(model, attribute, shape)
    with pytest.raises(ConcernModelMetadataError):
        load_skin_concern_model_bundle(settings, lambda _: model)


@pytest.mark.parametrize("field", ["labels", "normalization", "output_activation"])
def test_metadata_contract_mismatch_is_rejected(tmp_path: Path, field: str) -> None:
    settings = concern_settings(tmp_path)
    changed = metadata()
    changed[field] = [] if field == "labels" else "wrong"
    write_artifacts(settings, changed_metadata=changed)
    with pytest.raises(ConcernModelMetadataError):
        load_skin_concern_model_bundle(settings, lambda _: FakeModel())


@pytest.mark.parametrize(
    "output",
    [
        [[0.1] * 9],
        [[0.1] * 9 + [np.nan]],
        [[0.1] * 9 + [np.inf]],
        [[0.1] * 9 + [1.2]],
    ],
)
def test_invalid_model_output_is_rejected(output: Any) -> None:
    with pytest.raises(ConcernInferenceError):
        parse_concern_scores(output, model_bundle().label_map)


def test_successful_analysis_stores_safe_owned_report(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    token, user_id, upload_id, _ = seed(context)
    response = analyze(context[0], token, upload_id)
    assert response.status_code == 200
    body = response.json()
    assert any(item["code"] == "visible_oiliness" for item in body["observations"])
    assert any(item["code"] == "visible_redness" for item in body["uncertain_observations"])
    assert body["region_information_available"] is False
    assert "storage" not in response.text.lower() and "path" not in response.text.lower()
    stored = next(iter(context[6].documents.values()))
    assert stored["user_id"] == ObjectId(user_id)
    assert stored["model_version"] == "1.0.0-test"
    assert (
        stored["questionnaire_comparison"]["visible_oiliness"]["reported_value"] == "High oiliness"
    )
    oiliness = next(item for item in body["observations"] if item["code"] == "visible_oiliness")
    assert oiliness["questionnaire_reported_value"] == "High oiliness"


def test_tensor_is_rgb_normalized_once(tmp_path: Path) -> None:
    model = FakeModel()
    context = create_context(tmp_path, model)
    token, _, upload_id, _ = seed(context)
    analyze(context[0], token, upload_id)
    assert model.last_tensor is not None
    assert model.last_tensor.shape == (1, 224, 224, 3)
    assert model.last_tensor.dtype == np.float32
    assert 0 <= model.last_tensor.min() and model.last_tensor.max() > 0.8


def test_authentication_ownership_and_prerequisites(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    token, _, upload_id, _ = seed(context)
    assert context[0].post(f"/api/skin-concerns/{upload_id}/analyze").status_code == 401
    other_token, _, _, _ = seed(context, email="other@example.com")
    assert analyze(context[0], other_token, upload_id).status_code == 404
    next(iter(context[5].documents.values()))["result_status"] = "failed"
    assert analyze(context[0], token, upload_id).status_code == 409


def test_missing_upload_and_missing_prerequisites(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    token, _, upload_id, _ = seed(context)
    assert analyze(context[0], token, "missing-upload").status_code == 404
    context[4].documents.clear()
    assert analyze(context[0], token, upload_id).status_code == 409

    context = create_context(tmp_path / "second")
    token, _, upload_id, _ = seed(context)
    context[5].documents.clear()
    assert analyze(context[0], token, upload_id).status_code == 409


def test_missing_image_and_missing_report_are_safe(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    token, _, upload_id, path = seed(context)
    path.unlink()
    assert analyze(context[0], token, upload_id).status_code == 410
    response = context[0].get(
        f"/api/skin-concerns/{upload_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_expired_upload_and_wrong_prepared_shape_are_rejected(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    token, _, upload_id, _ = seed(context)
    next(iter(context[3].documents.values()))["expires_at"] = datetime.now(
        timezone.utc
    ) - timedelta(seconds=1)
    assert analyze(context[0], token, upload_id).status_code == 410

    context = create_context(tmp_path / "wrong-shape")
    token, _, upload_id, path = seed(context)
    Image.new("RGB", (200, 224), "white").save(path)
    response = analyze(context[0], token, upload_id)
    assert response.status_code == 500
    assert "200" not in response.text


def test_rerun_updates_one_report_and_workflow_status(tmp_path: Path) -> None:
    context = create_context(tmp_path)
    token, _, upload_id, _ = seed(context)
    first = analyze(context[0], token, upload_id).json()
    second = analyze(context[0], token, upload_id).json()
    assert len(context[6].documents) == 1
    assert first["skin_concern_report_id"] == second["skin_concern_report_id"]
    assert next(iter(context[3].documents.values()))["status"] == "skin_concern_analysis_uncertain"


def test_model_exception_is_not_exposed(tmp_path: Path) -> None:
    context = create_context(tmp_path, FakeModel(raises=True))
    token, _, upload_id, _ = seed(context)
    response = analyze(context[0], token, upload_id)
    assert response.status_code == 500
    assert "private concern model error" not in response.text
    assert next(iter(context[3].documents.values()))["status"] == "skin_concern_analysis_failed"
