import re
from datetime import datetime
from typing import Any

from app.schemas.product import ProductCreate


def normalize_key(value: str) -> str:
    return " ".join(value.casefold().split())


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug[:180] or "product"


def build_product_document(payload: ProductCreate, now: datetime) -> dict[str, Any]:
    document = payload.model_dump(mode="python")
    document["slug"] = payload.slug or slugify(f"{payload.brand_name} {payload.product_name}")
    document["normalized_product_name"] = normalize_key(payload.product_name)
    document["normalized_brand_name"] = normalize_key(payload.brand_name)
    document["normalized_ingredients"] = [
        normalize_key(value) for value in payload.normalized_ingredients
    ]
    document["created_at"] = now
    document["updated_at"] = now
    return document


def product_fingerprint(document: dict[str, Any]) -> tuple[Any, ...]:
    package = document.get("package_size") or {}
    return (
        normalize_key(document["product_name"]),
        normalize_key(document["brand_name"]),
        document["category"],
        package.get("quantity"),
        package.get("unit"),
    )
