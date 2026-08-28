from datetime import datetime
from typing import Any

from app.models.product import normalize_key
from app.schemas.ingredient import IngredientCreate


def build_ingredient_document(payload: IngredientCreate, now: datetime) -> dict[str, Any]:
    return {
        **payload.model_dump(mode="python"),
        "normalized_name": normalize_key(payload.canonical_name),
        "normalized_aliases": [normalize_key(alias) for alias in payload.aliases],
        "created_at": now,
        "updated_at": now,
    }
