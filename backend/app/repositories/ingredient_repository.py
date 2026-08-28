import re
from typing import Any


async def list_ingredients(
    collection: Any, query: dict[str, Any], page: int, page_size: int
) -> tuple[list[dict[str, Any]], int]:
    total = await collection.count_documents(query)
    cursor = (
        collection.find(query)
        .sort("canonical_name", 1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return await cursor.to_list(length=page_size), total


async def find_ingredient(collection: Any, ingredient_id: str) -> dict[str, Any] | None:
    return await collection.find_one({"ingredient_id": ingredient_id, "is_active": True})


async def find_by_name_or_alias(collection: Any, value: str) -> dict[str, Any] | None:
    normalized = " ".join(value.casefold().split())
    return await collection.find_one(
        {
            "is_active": True,
            "$or": [{"normalized_name": normalized}, {"normalized_aliases": normalized}],
        }
    )


def ingredient_search_query(search: str | None, category: str | None) -> dict[str, Any]:
    clauses: list[dict[str, Any]] = [{"is_active": True}]
    if search:
        pattern = re.compile(re.escape(" ".join(search.split())), re.IGNORECASE)
        clauses.append({"$or": [{"canonical_name": pattern}, {"aliases": pattern}]})
    if category:
        clauses.append({"ingredient_category": category})
    return {"$and": clauses}
