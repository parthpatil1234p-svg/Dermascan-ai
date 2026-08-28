from __future__ import annotations

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
    get_skin_profiles_collection,
    get_skin_type_reports_collection,
    get_users_collection,
)
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.main import create_app
from app.ml.model_loader import (
    ModelMetadataError,
    ModelUnavailableError,
    SkinTypeModelBundle,
    load_skin_type_model_bundle,
)
from app.ml.model_registry import SkinTypeModelRegistry, get_skin_type_model_registry
from app.services.skin_type_fusion_service import (
    QuestionnaireEvidence,
    fuse_skin_type_prediction,
)
from app.services.skin_type_inference_service import (
    SkinTypeInferenceError,
    parse_model_probabilities,
    run_skin_type_inference,
)


class InsertResult:
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

    async def insert_one(self, document: dict[str, Any]) -> InsertResult:
        document_id = ObjectId()
        self.documents[document_id] = {**document, "_id": document_id}
        return InsertResult(document_id)

    async def update_one(self, query: dict[str, Any], operation: dict[str, Any]) -> None:
        for document in self.documents.values():
            if matches(document, query):
                document.update(operation["$set"])
                return


class FakeModel:
    input_shape = (None, 224, 224, 3)
    output_shape = (None, 4)

    def __init__(self, output: Any = None, *, raises: bool = False) -> None:
        self.output = output if output is not None else [[0.04, 0.84, 0.03, 0.09]]
        self.raises = raises
        self.last_tensor: np.ndarray | None = None

    def predict(self, tensor: np.ndarray, verbose: int = 0) -> Any:
        self.last_tensor = tensor.copy()
        if self.raises:
            raise RuntimeError("private model failure")
        return self.output


def settings_for(tmp_path: Path, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "app_name": "DermaScan AI",
        "app_env": "testing",
        "api_prefix": "/api",
        "mongodb_url": "mongodb://localhost:27017",
        "mongodb_database": "dermascan_skin_type_test",
        "jwt_secret_key": "skin-type-test-secret-key-at-least-32-bytes",
        "jwt_algorithm": "HS256",
        "access_token_expire_minutes": 60,
        "frontend_origin": "http://localhost:5173",
        "preprocessed_image_directory": tmp_path / "processed",
        "skin_type_model_file": tmp_path / "model.keras",
        "skin_type_metadata_file": tmp_path / "metadata.json",
        "skin_type_class_map_file": tmp_path / "class_map.json",
        "preprocess_enable_denoise": False,
    }
    values.update(overrides)
    return Settings(**values)


def valid_metadata() -> dict[str, Any]:
    return {
        "model_name": "DermaScan Skin Type Classifier",
        "model_version": "1.0.0-test",
        "input_width": 224,
        "input_height": 224,
        "input_channels": 3,
        "colour_space": "RGB",
        "normalization": "zero_to_one",
        "resize_mode": "letterbox",
        "classes": ["normal", "oily", "dry", "combination"],
    }


def bundle(model: FakeModel | None = None) -> SkinTypeModelBundle:
    return SkinTypeModelBundle(
        model=model or FakeModel(),
        metadata=valid_metadata(),
        class_map={0: "normal", 1: "oily", 2: "dry", 3: "combination"},
    )


def write_model_files(
    settings: Settings,
    *,
    metadata: dict[str, Any] | None = None,
    class_map: dict[str, str] | None = None,
) -> None:
    import json

    settings.skin_type_model_path.write_bytes(b"test model placeholder")
    settings.skin_type_metadata_path.write_text(
        json.dumps(metadata or valid_metadata()), encoding="utf-8"
    )
    settings.skin_type_class_map_path.write_text(
        json.dumps(class_map or {"0": "normal", "1": "oily", "2": "dry", "3": "combination"}),
        encoding="utf-8",
    )


def create_client(tmp_path: Path, model: FakeModel | None = None):
    users, profiles, uploads, preprocessing, reports = (FakeCollection() for _ in range(5))
    settings = settings_for(tmp_path)
    registry = SkinTypeModelRegistry()
    registry.set_bundle_for_testing(bundle(model))
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_users_collection] = lambda: users
    app.dependency_overrides[get_skin_profiles_collection] = lambda: profiles
    app.dependency_overrides[get_image_uploads_collection] = lambda: uploads
    app.dependency_overrides[get_image_preprocessing_reports_collection] = lambda: preprocessing
    app.dependency_overrides[get_skin_type_reports_collection] = lambda: reports
    app.dependency_overrides[get_skin_type_model_registry] = lambda: registry
    app.dependency_overrides[get_settings] = lambda: settings
    return (
        TestClient(app),
        users,
        profiles,
        uploads,
        preprocessing,
        reports,
        settings,
        registry,
    )


def seed_user(
    users: FakeCollection,
    profiles: FakeCollection,
    *,
    email: str = "skin@example.com",
    oily: str = "High",
    dry: str = "Low",
    sensitive: bool | None = True,
) -> tuple[str, str]:
    user_id = ObjectId()
    now = datetime.now(timezone.utc)
    users.documents[user_id] = {
        "_id": user_id,
        "full_name": "Skin Type User",
        "email": email,
        "password_hash": "unused",
        "age_group": "18-25",
        "location": "India",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    profile_id = ObjectId()
    profiles.documents[profile_id] = {
        "_id": profile_id,
        "user_id": user_id,
        "is_complete": True,
        "oiliness_level": oily,
        "dryness_level": dry,
        "is_sensitive": sensitive,
    }
    return create_access_token(subject=str(user_id)), str(user_id)


def seed_workflow(
    uploads: FakeCollection,
    preprocessing: FakeCollection,
    settings: Settings,
    user_id: str,
    *,
    status: str = "skin_type_analysis_pending",
    preprocessing_status: str = "completed",
    write_image: bool = True,
) -> str:
    upload_id = str(uuid4())
    now = datetime.now(timezone.utc)
    upload_object_id = ObjectId()
    uploads.documents[upload_object_id] = {
        "_id": upload_object_id,
        "upload_id": upload_id,
        "user_id": ObjectId(user_id),
        "status": status,
        "created_at": now,
        "updated_at": now,
        "expires_at": now + timedelta(minutes=30),
    }
    relative = Path(user_id[:12]) / upload_id[:12] / "prepared.jpg"
    image_path = settings.preprocessed_image_path / relative
    if write_image:
        image_path.parent.mkdir(parents=True, exist_ok=True)
        x = np.linspace(0, 255, 224, dtype=np.uint8)
        array = np.dstack(
            (
                np.broadcast_to(x, (224, 224)),
                np.broadcast_to(x[:, None], (224, 224)),
                np.full((224, 224), 180, dtype=np.uint8),
            )
        )
        Image.fromarray(array, "RGB").save(image_path)
    report_id = ObjectId()
    preprocessing.documents[report_id] = {
        "_id": report_id,
        "preprocessing_report_id": str(uuid4()),
        "upload_id": upload_id,
        "user_id": ObjectId(user_id),
        "preprocessing_status": preprocessing_status,
        "processed_image_reference": relative.as_posix(),
        "created_at": now,
        "updated_at": now,
    }
    return upload_id


def ready(tmp_path: Path, model: FakeModel | None = None, **profile: Any):
    context = create_client(tmp_path, model)
    client, users, profiles, uploads, preprocessing, reports, settings, registry = context
    token, user_id = seed_user(users, profiles, **profile)
    upload_id = seed_workflow(uploads, preprocessing, settings, user_id)
    return context + (token, user_id, upload_id)


def analyze(client: TestClient, token: str, upload_id: str):
    return client.post(
        f"/api/skin-type/{upload_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
    )


def test_successful_model_loading(tmp_path: Path) -> None:
    settings = settings_for(tmp_path)
    write_model_files(settings)
    loaded = load_skin_type_model_bundle(settings, lambda _: FakeModel())
    assert loaded.metadata["model_version"] == "1.0.0-test"


def test_missing_model_file(tmp_path: Path) -> None:
    with pytest.raises(ModelUnavailableError):
        load_skin_type_model_bundle(settings_for(tmp_path), lambda _: FakeModel())


def test_invalid_metadata(tmp_path: Path) -> None:
    settings = settings_for(tmp_path)
    write_model_files(settings, metadata={"model_name": "incomplete"})
    with pytest.raises(ModelMetadataError):
        load_skin_type_model_bundle(settings, lambda _: FakeModel())


def test_class_map_mismatch(tmp_path: Path) -> None:
    settings = settings_for(tmp_path)
    write_model_files(settings, class_map={"0": "oily"})
    with pytest.raises(ModelMetadataError):
        load_skin_type_model_bundle(settings, lambda _: FakeModel())


def test_input_shape_mismatch(tmp_path: Path) -> None:
    settings = settings_for(tmp_path)
    write_model_files(settings)
    model = FakeModel()
    model.input_shape = (None, 128, 128, 3)
    with pytest.raises(ModelMetadataError):
        load_skin_type_model_bundle(settings, lambda _: model)


def test_preprocessing_contract_mismatch(tmp_path: Path) -> None:
    settings = settings_for(tmp_path)
    metadata = valid_metadata()
    metadata["normalization"] = "minus_one_to_one"
    write_model_files(settings, metadata=metadata)
    with pytest.raises(ModelMetadataError):
        load_skin_type_model_bundle(settings, lambda _: FakeModel())


def test_successful_inference_with_mocked_model(tmp_path: Path) -> None:
    context = ready(tmp_path)
    response = analyze(context[0], context[8], context[10])
    assert response.status_code == 200
    assert response.json()["skin_type"] == "Oily"


def test_reject_unauthenticated_request(tmp_path: Path) -> None:
    context = ready(tmp_path)
    assert context[0].post(f"/api/skin-type/{context[10]}/analyze").status_code == 401


def test_reject_another_users_upload(tmp_path: Path) -> None:
    context = ready(tmp_path)
    other_token, _ = seed_user(context[1], context[2], email="other@example.com")
    assert analyze(context[0], other_token, context[10]).status_code == 404


def test_reject_missing_upload(tmp_path: Path) -> None:
    context = ready(tmp_path)
    assert analyze(context[0], context[8], "missing").status_code == 404


def test_reject_missing_preprocessing_report(tmp_path: Path) -> None:
    context = ready(tmp_path)
    context[4].documents.clear()
    assert analyze(context[0], context[8], context[10]).status_code == 409


def test_reject_failed_preprocessing(tmp_path: Path) -> None:
    context = ready(tmp_path)
    next(iter(context[4].documents.values()))["preprocessing_status"] = "failed"
    assert analyze(context[0], context[8], context[10]).status_code == 409


def test_reject_missing_processed_image(tmp_path: Path) -> None:
    context = ready(tmp_path)
    path = (
        context[6].preprocessed_image_path
        / next(iter(context[4].documents.values()))["processed_image_reference"]
    )
    path.unlink()
    assert analyze(context[0], context[8], context[10]).status_code == 410


def test_correct_rgb_tensor_shape(tmp_path: Path) -> None:
    model = FakeModel()
    context = ready(tmp_path, model)
    analyze(context[0], context[8], context[10])
    assert model.last_tensor is not None and model.last_tensor.shape == (1, 224, 224, 3)


def test_correct_normalization(tmp_path: Path) -> None:
    model = FakeModel()
    context = ready(tmp_path, model)
    analyze(context[0], context[8], context[10])
    assert model.last_tensor is not None
    assert model.last_tensor.dtype == np.float32
    assert 0.0 <= float(model.last_tensor.min()) < float(model.last_tensor.max()) <= 1.0


def test_no_double_normalization(tmp_path: Path) -> None:
    model = FakeModel()
    context = ready(tmp_path, model)
    analyze(context[0], context[8], context[10])
    assert model.last_tensor is not None
    assert float(model.last_tensor.max()) > 0.9


def test_correct_class_mapping(tmp_path: Path) -> None:
    result = parse_model_probabilities(
        [[0.1, 0.2, 0.6, 0.1]], bundle().class_map, settings_for(tmp_path)
    )
    assert result.top_class == "dry"


def test_valid_probability_parsing_normalizes_output(tmp_path: Path) -> None:
    result = parse_model_probabilities([[1, 2, 3, 4]], bundle().class_map, settings_for(tmp_path))
    assert sum(result.probabilities.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("output", [[[0.1, np.nan, 0.3, 0.4]], [[0.1, 0.2, 0.7]]])
def test_reject_invalid_model_output(tmp_path: Path, output: Any) -> None:
    with pytest.raises(SkinTypeInferenceError):
        parse_model_probabilities(output, bundle().class_map, settings_for(tmp_path))


def test_correct_top_second_and_margin(tmp_path: Path) -> None:
    result = parse_model_probabilities(
        [[0.05, 0.70, 0.10, 0.15]], bundle().class_map, settings_for(tmp_path)
    )
    assert (result.top_class, result.second_class) == ("oily", "combination")
    assert result.margin == pytest.approx(0.55)


def test_high_confidence_result(tmp_path: Path) -> None:
    result = parse_model_probabilities(
        [[0.03, 0.84, 0.04, 0.09]], bundle().class_map, settings_for(tmp_path)
    )
    assert result.confidence_level == "high" and result.is_uncertain is False


def test_low_confidence_result_is_uncertain(tmp_path: Path) -> None:
    result = parse_model_probabilities(
        [[0.20, 0.40, 0.15, 0.25]], bundle().class_map, settings_for(tmp_path)
    )
    assert result.is_uncertain is True


def test_low_margin_result_is_uncertain(tmp_path: Path) -> None:
    result = parse_model_probabilities(
        [[0.02, 0.47, 0.04, 0.47]], bundle().class_map, settings_for(tmp_path)
    )
    assert result.is_uncertain is True


def test_strong_questionnaire_agreement() -> None:
    result = fuse_skin_type_prediction(
        predicted_class="oily",
        image_result_is_uncertain=False,
        evidence=QuestionnaireEvidence("High", "Low", True),
    )
    assert result.final_skin_type == "Oily" and result.agreement == "Strong"


def test_strong_questionnaire_disagreement() -> None:
    result = fuse_skin_type_prediction(
        predicted_class="dry",
        image_result_is_uncertain=False,
        evidence=QuestionnaireEvidence("High", "Low", False),
    )
    assert result.final_skin_type == "Uncertain" and result.agreement == "Conflict"


def test_sensitivity_remains_separate(tmp_path: Path) -> None:
    context = ready(tmp_path, sensitive=True)
    data = analyze(context[0], context[8], context[10]).json()
    assert data["skin_type"] == "Oily"
    assert data["self_reported_sensitivity"] is True


def test_report_stored_with_model_version_and_no_path(tmp_path: Path) -> None:
    context = ready(tmp_path)
    response = analyze(context[0], context[8], context[10])
    report = next(iter(context[5].documents.values()))
    assert report["model_version"] == "1.0.0-test"
    assert report["user_id"] == ObjectId(context[9])
    assert "path" not in response.text.lower()
    assert "processed_image_reference" not in response.text


def test_existing_report_is_updated(tmp_path: Path) -> None:
    context = ready(tmp_path)
    first = analyze(context[0], context[8], context[10]).json()
    second = analyze(context[0], context[8], context[10]).json()
    assert len(context[5].documents) == 1
    assert first["skin_type_report_id"] == second["skin_type_report_id"]


def test_workflow_status_updated(tmp_path: Path) -> None:
    context = ready(tmp_path)
    analyze(context[0], context[8], context[10])
    assert next(iter(context[3].documents.values()))["status"] == "skin_type_estimated"


def test_get_owned_report_and_model_status(tmp_path: Path) -> None:
    context = ready(tmp_path)
    analyze(context[0], context[8], context[10])
    report = context[0].get(
        f"/api/skin-type/{context[10]}",
        headers={"Authorization": f"Bearer {context[8]}"},
    )
    status = context[0].get("/api/models/skin-type/status")
    assert report.status_code == 200
    assert status.json()["loaded"] is True
    assert "path" not in status.text.lower()


def test_safe_error_for_inference_exception(tmp_path: Path) -> None:
    context = ready(tmp_path, FakeModel(raises=True))
    response = analyze(context[0], context[8], context[10])
    assert response.status_code == 500
    assert "private model failure" not in response.text
    assert next(iter(context[3].documents.values()))["status"] == "skin_type_analysis_failed"


def test_direct_inference_rejects_decode_failure(tmp_path: Path) -> None:
    bad_image = tmp_path / "bad.jpg"
    bad_image.write_bytes(b"not an image")
    with pytest.raises(SkinTypeInferenceError):
        run_skin_type_inference(bad_image, bundle(), settings_for(tmp_path))
