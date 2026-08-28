import copy
import re
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def nested(document: dict[str, Any], key: str) -> Any:
    value: Any = document
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in query.items():
        if key == "$and":
            if not all(matches(document, item) for item in expected):
                return False
            continue
        if key == "$or":
            if not any(matches(document, item) for item in expected):
                return False
            continue
        actual = nested(document, key)
        if isinstance(expected, re.Pattern):
            values = actual if isinstance(actual, list) else [actual]
            if not any(value is not None and expected.search(str(value)) for value in values):
                return False
        elif isinstance(expected, dict):
            for operator, operand in expected.items():
                if operator == "$in":
                    if isinstance(actual, list):
                        ok = any(value in operand for value in actual)
                    else:
                        ok = actual in operand
                    if not ok:
                        return False
                elif operator == "$ne":
                    if actual == operand or (isinstance(actual, list) and operand in actual):
                        return False
                elif operator == "$gte" and (actual is None or actual < operand):
                    return False
                elif operator == "$lte" and (actual is None or actual > operand):
                    return False
                elif operator == "$lt" and (actual is None or actual >= operand):
                    return False
                elif operator == "$size" and len(actual or []) != operand:
                    return False
        elif isinstance(actual, list):
            if expected not in actual:
                return False
        elif actual != expected:
            return False
    return True


class Result:
    def __init__(
        self, *, inserted_id: ObjectId | None = None, matched_count: int = 0, deleted_count: int = 0
    ):
        self.inserted_id = inserted_id
        self.matched_count = matched_count
        self.modified_count = matched_count
        self.deleted_count = deleted_count


class FakeCursor:
    def __init__(self, documents: list[dict[str, Any]]):
        self.documents = [copy.deepcopy(document) for document in documents]

    def sort(self, field: str | list[tuple[str, int]], direction: int | None = None):
        fields = field if isinstance(field, list) else [(field, direction or 1)]
        for key, order in reversed(fields):
            self.documents.sort(
                key=lambda doc: (nested(doc, key) is None, nested(doc, key)), reverse=order < 0
            )
        return self

    def skip(self, count: int):
        self.documents = self.documents[count:]
        return self

    def limit(self, count: int):
        self.documents = self.documents[:count]
        return self

    async def to_list(self, length: int | None = None):
        return copy.deepcopy(self.documents if length is None else self.documents[:length])

    def __aiter__(self):
        self._iterator = iter(self.documents)
        return self

    async def __anext__(self):
        try:
            return copy.deepcopy(next(self._iterator))
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeCollection:
    def __init__(self, documents: list[dict[str, Any]] | None = None):
        self.documents = [copy.deepcopy(document) for document in (documents or [])]
        for document in self.documents:
            document.setdefault("_id", ObjectId())

    async def find_one(self, query: dict[str, Any]):
        return next((copy.deepcopy(doc) for doc in self.documents if matches(doc, query)), None)

    def find(self, query: dict[str, Any]):
        return FakeCursor([doc for doc in self.documents if matches(doc, query)])

    async def count_documents(self, query: dict[str, Any]):
        return sum(matches(doc, query) for doc in self.documents)

    async def insert_one(self, document: dict[str, Any]):
        item = copy.deepcopy(document)
        item.setdefault("_id", ObjectId())
        self.documents.append(item)
        return Result(inserted_id=item["_id"])

    async def replace_one(
        self, query: dict[str, Any], document: dict[str, Any], upsert: bool = False
    ):
        for index, item in enumerate(self.documents):
            if matches(item, query):
                replacement = copy.deepcopy(document)
                replacement.setdefault("_id", item["_id"])
                self.documents[index] = replacement
                return Result(matched_count=1)
        if upsert:
            await self.insert_one(document)
        return Result()

    async def update_one(self, query: dict[str, Any], operation: dict[str, Any]):
        for item in self.documents:
            if matches(item, query):
                item.update(copy.deepcopy(operation.get("$set", {})))
                return Result(matched_count=1)
        return Result()


def demo_product(**overrides: Any) -> dict[str, Any]:
    now = datetime(2026, 8, 1, tzinfo=timezone.utc)
    data = {
        "product_id": "PRD-TEST001",
        "slug": "dermademo-test-cleanser",
        "product_name": "Test Gentle Cleanser",
        "normalized_product_name": "test gentle cleanser",
        "brand_id": "BRD-DEMO",
        "brand_name": "DermaDemo Labs",
        "normalized_brand_name": "dermademo labs",
        "category": "cleanser",
        "short_description": "A fictional product used only in isolated automated tests.",
        "data_type": "demo_synthetic",
        "is_demo_product": True,
        "suitable_skin_types": ["combination", "oily"],
        "target_visible_concerns": ["visible_oiliness"],
        "compatibility_notes": [],
        "sensitivity_suitability": "not_specified",
        "ingredients": [{"display_name": "Niacinamide", "position": 1}],
        "normalized_ingredients": ["niacinamide"],
        "unmapped_ingredients": [],
        "highlighted_ingredients": ["Niacinamide"],
        "potential_irritant_flags": [],
        "allergen_flags": [],
        "fragrance_status": "fragrance_free",
        "essential_oil_status": "free",
        "comedogenic_claim_status": "not_specified",
        "minimum_age_group": "Not specified",
        "maximum_age_group": "Not specified",
        "usage_time": "not_specified",
        "usage_frequency": None,
        "price": {"amount": 499.0, "currency": "INR"},
        "package_size": {"quantity": 100.0, "unit": "ml"},
        "price_per_unit": None,
        "price_checked_at": now,
        "price_source": "Synthetic demonstration value",
        "country_codes": ["IN"],
        "availability_status": "available",
        "availability_checked_at": now,
        "official_product_url": None,
        "source_name": "Synthetic demonstration record",
        "source_url": None,
        "source_verified_at": now,
        "rating": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return data
