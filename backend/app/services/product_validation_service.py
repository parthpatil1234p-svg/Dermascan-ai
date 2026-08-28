from typing import Any

from app.models.product import normalize_key, product_fingerprint
from app.schemas.product import ProductCreate


class DuplicateProductError(Exception):
    pass


async def find_potential_duplicate(
    collection: Any, payload: ProductCreate
) -> dict[str, Any] | None:
    package = payload.package_size.model_dump() if payload.package_size else {}
    query = {
        "normalized_product_name": normalize_key(payload.product_name),
        "normalized_brand_name": normalize_key(payload.brand_name),
        "category": payload.category,
        "package_size.quantity": package.get("quantity"),
        "package_size.unit": package.get("unit"),
    }
    return await collection.find_one(query)


def detect_duplicate_rows(documents: list[dict[str, Any]]) -> set[int]:
    seen: dict[tuple[Any, ...], int] = {}
    duplicates: set[int] = set()
    for index, document in enumerate(documents):
        fingerprint = product_fingerprint(document)
        if fingerprint in seen:
            duplicates.add(index)
        else:
            seen[fingerprint] = index
    return duplicates
