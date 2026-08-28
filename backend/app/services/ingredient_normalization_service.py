from dataclasses import dataclass
from typing import Any

from app.models.product import normalize_key


@dataclass(slots=True)
class IngredientNormalizationResult:
    normalized_ids: list[str]
    unmapped: list[str]


async def build_ingredient_lookup(collection: Any) -> dict[str, str]:
    lookup: dict[str, str] = {}
    cursor = collection.find({"is_active": True})
    async for document in cursor:
        identifier = document["ingredient_id"]
        lookup[document["normalized_name"]] = identifier
        for alias in document.get("normalized_aliases", []):
            lookup[alias] = identifier
    return lookup


def normalize_ingredient_names(
    names: list[str], lookup: dict[str, str]
) -> IngredientNormalizationResult:
    normalized_ids: list[str] = []
    unmapped: list[str] = []
    seen_ids: set[str] = set()
    seen_unmapped: set[str] = set()
    for original in names:
        cleaned = " ".join(original.split())
        key = normalize_key(cleaned)
        ingredient_id = lookup.get(key)
        if ingredient_id and ingredient_id not in seen_ids:
            normalized_ids.append(ingredient_id)
            seen_ids.add(ingredient_id)
        elif not ingredient_id and key and key not in seen_unmapped:
            unmapped.append(cleaned)
            seen_unmapped.add(key)
    return IngredientNormalizationResult(normalized_ids, unmapped)
