from __future__ import annotations

import os
from pathlib import Path
from typing import Any

os.environ.setdefault("APP_NAME", "DermaScan AI")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("API_PREFIX", "/api")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DATABASE", "dermascan_ai_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-system-tests-at-least-32-bytes")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")

import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.rate_limit import InMemoryRateLimiter
from app.main import create_app
from app.ml.demo_models import create_demo_concern_bundle, create_demo_skin_type_bundle
from app.ml.model_registry import skin_type_model_registry
from app.ml.skin_concern_registry import skin_concern_model_registry
from app.services.readiness_service import build_readiness_report


class ReadyProducts:
    async def count_documents(self, query: dict[str, Any], **kwargs: Any) -> int:
        assert query == {"is_active": True}
        assert kwargs == {"limit": 1}
        return 1


class ReadyDatabase:
    async def command(self, name: str) -> dict[str, int]:
        assert name == "ping"
        return {"ok": 1}

    def __getitem__(self, name: str) -> ReadyProducts:
        assert name == "products"
        return ReadyProducts()


def production_settings(**overrides: Any) -> Settings:
    values = {
        "APP_NAME": "DermaScan AI",
        "APP_ENV": "production",
        "API_PREFIX": "/api",
        "MONGODB_URL": "mongodb://database:27017",
        "MONGODB_DATABASE": "dermascan_ai",
        "JWT_SECRET_KEY": "deployment-specific-secret-that-is-long-enough",
        "FRONTEND_ORIGIN": "https://dermascan.example",
    }
    values.update(overrides)
    return Settings(**values)


def test_production_configuration_rejects_weak_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        production_settings(JWT_SECRET_KEY="change-me")


def test_production_configuration_rejects_origin_paths() -> None:
    with pytest.raises(ValidationError, match="FRONTEND_ORIGIN"):
        production_settings(FRONTEND_ORIGIN="https://dermascan.example/private")


def test_rate_limiter_uses_sliding_window() -> None:
    limiter = InMemoryRateLimiter()
    assert limiter.allow("login:client", 2, 60, now=10) == (True, 0)
    assert limiter.allow("login:client", 2, 60, now=20) == (True, 0)
    allowed, retry_after = limiter.allow("login:client", 2, 60, now=30)
    assert allowed is False
    assert retry_after == 41
    assert limiter.allow("login:client", 2, 60, now=71) == (True, 0)


def test_demo_models_are_deterministic_and_explicitly_labelled() -> None:
    settings = get_settings().model_copy(update={"ai_demo_mode": True})
    skin_bundle = create_demo_skin_type_bundle(settings)
    concern_bundle = create_demo_concern_bundle(settings)
    tensor = np.full((1, 224, 224, 3), 0.5, dtype=np.float32)
    first = skin_bundle.model.predict(tensor)
    second = skin_bundle.model.predict(tensor)
    assert np.array_equal(first, second)
    assert first.shape == (1, 4)
    assert concern_bundle.model.predict(tensor).shape == (1, 10)
    assert skin_bundle.metadata["analysis_mode"] == "demonstration"
    assert concern_bundle.metadata["analysis_mode"] == "demonstration"
    assert concern_bundle.thresholds_calibrated is False


@pytest.mark.asyncio
async def test_readiness_reports_all_required_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = get_settings().model_copy(
        update={
            "upload_directory": tmp_path / "uploads",
            "face_crop_directory": tmp_path / "crops",
            "preprocessed_image_directory": tmp_path / "processed",
            "report_export_directory": tmp_path / "exports",
        }
    )
    monkeypatch.setattr(skin_type_model_registry, "status", lambda: {"loaded": True})
    monkeypatch.setattr(skin_concern_model_registry, "status", lambda: {"loaded": True})
    report = await build_readiness_report(ReadyDatabase(), settings)
    assert report == {
        "status": "ready",
        "database": "ready",
        "product_catalogue": "ready",
        "skin_type_model": "ready",
        "skin_concern_model": "ready",
        "storage": "ready",
        "analysis_mode": "model",
    }


def test_health_response_has_request_id_and_security_headers() -> None:
    app = create_app(enable_lifespan=False)
    with TestClient(app) as client:
        response = client.get("/api/health", headers={"X-Request-ID": "audit-test-1"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "audit-test-1"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_unexpected_errors_do_not_expose_exception_details() -> None:
    app = create_app(enable_lifespan=False)

    @app.get("/test-only-failure")
    async def fail() -> None:
        raise RuntimeError("private database and filesystem details")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-only-failure")
    assert response.status_code == 500
    assert response.json()["detail"] == "The requested resource could not be processed."
    assert response.json()["code"] == "INTERNAL_SERVER_ERROR"
    assert "private database" not in response.text
