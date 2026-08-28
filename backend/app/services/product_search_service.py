import re
from dataclasses import dataclass
from typing import Any

from app.core.catalogue import PUBLIC_DATA_TYPES
from app.models.product import normalize_key

SORT_FIELDS = {
    "name_asc": [("product_name", 1), ("product_id", 1)],
    "name_desc": [("product_name", -1), ("product_id", 1)],
    "price_low_to_high": [("price.amount", 1), ("product_name", 1)],
    "price_high_to_low": [("price.amount", -1), ("product_name", 1)],
    "newest": [("created_at", -1), ("product_id", 1)],
    "rating_high_to_low": [("rating.value", -1), ("rating.count", -1), ("product_name", 1)],
}


@dataclass(slots=True)
class ProductFilters:
    search: str | None = None
    brand: str | None = None
    category: str | None = None
    skin_type: str | None = None
    visible_concern: str | None = None
    ingredient: str | None = None
    exclude_ingredient: str | None = None
    country: str | None = None
    availability: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    fragrance_status: str | None = None
    data_type: str | None = None


def build_product_query(filters: ProductFilters) -> dict[str, Any]:
    clauses: list[dict[str, Any]] = [
        {"is_active": True},
        {"data_type": filters.data_type if filters.data_type else {"$in": list(PUBLIC_DATA_TYPES)}},
    ]
    if filters.search:
        value = " ".join(filters.search.split())[:100]
        pattern = re.compile(re.escape(value), re.IGNORECASE)
        clauses.append(
            {
                "$or": [
                    {"product_name": pattern},
                    {"brand_name": pattern},
                    {"short_description": pattern},
                    {"highlighted_ingredients": pattern},
                    {"target_visible_concerns": normalize_key(value).replace(" ", "_")},
                ]
            }
        )
    if filters.brand:
        brand = normalize_key(filters.brand)
        clauses.append({"$or": [{"brand_id": filters.brand}, {"normalized_brand_name": brand}]})
    exact_filters = {
        "category": filters.category,
        "suitable_skin_types": filters.skin_type,
        "target_visible_concerns": filters.visible_concern,
        "country_codes": filters.country.upper() if filters.country else None,
        "availability_status": filters.availability,
        "fragrance_status": filters.fragrance_status,
    }
    clauses.extend({key: value} for key, value in exact_filters.items() if value is not None)
    if filters.ingredient:
        clauses.append({"normalized_ingredients": normalize_key(filters.ingredient)})
    if filters.exclude_ingredient:
        clauses.append(
            {"normalized_ingredients": {"$ne": normalize_key(filters.exclude_ingredient)}}
        )
    price: dict[str, float] = {}
    if filters.min_price is not None:
        price["$gte"] = filters.min_price
    if filters.max_price is not None:
        price["$lte"] = filters.max_price
    if price:
        clauses.append({"price.amount": price})
    return {"$and": clauses}


def get_sort(sort: str) -> list[tuple[str, int]]:
    return SORT_FIELDS[sort]
