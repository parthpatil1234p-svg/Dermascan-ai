from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import Settings
from app.ml.model_registry import skin_type_model_registry
from app.ml.skin_concern_registry import skin_concern_model_registry


def _check_storage(paths: list[Path]) -> bool:
    try:
        for root in paths:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / f".readiness-{uuid4().hex}"
            probe.write_bytes(b"ready")
            probe.unlink()
        return True
    except OSError:
        return False


async def build_readiness_report(database: Any, settings: Settings) -> dict[str, Any]:
    database_ready = False
    catalogue_ready = False
    if database is not None:
        try:
            await database.command("ping")
            database_ready = True
            catalogue_ready = (
                await database["products"].count_documents({"is_active": True}, limit=1) > 0
            )
        except Exception:
            database_ready = False

    storage_ready = _check_storage(
        [
            settings.upload_path,
            settings.face_crop_path,
            settings.preprocessed_image_path,
            settings.report_export_path,
        ]
    )
    skin_type = skin_type_model_registry.status()
    skin_concern = skin_concern_model_registry.status()
    models_ready = bool(skin_type.get("loaded") and skin_concern.get("loaded"))
    ready = database_ready and catalogue_ready and storage_ready and models_ready
    return {
        "status": "ready" if ready else "not_ready",
        "database": "ready" if database_ready else "not_ready",
        "product_catalogue": "ready" if catalogue_ready else "not_ready",
        "skin_type_model": "ready" if skin_type.get("loaded") else "not_ready",
        "skin_concern_model": "ready" if skin_concern.get("loaded") else "not_ready",
        "storage": "ready" if storage_ready else "not_ready",
        "analysis_mode": "demonstration" if settings.ai_demo_mode else "model",
    }
