from datetime import datetime
from typing import Any

from app.models.product import normalize_key
from app.schemas.brand import BrandCreate


def build_brand_document(payload: BrandCreate, now: datetime) -> dict[str, Any]:
    return {
        **payload.model_dump(mode="python"),
        "normalized_name": normalize_key(payload.brand_name),
        "created_at": now,
        "updated_at": now,
    }
