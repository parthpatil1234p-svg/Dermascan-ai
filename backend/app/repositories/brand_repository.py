import re
from typing import Any


async def list_brands(
    collection: Any, search: str | None, page: int, page_size: int
) -> tuple[list[dict[str, Any]], int]:
    query: dict[str, Any] = {"is_active": True}
    if search:
        query["brand_name"] = re.compile(re.escape(" ".join(search.split())), re.IGNORECASE)
    total = await collection.count_documents(query)
    cursor = (
        collection.find(query).sort("brand_name", 1).skip((page - 1) * page_size).limit(page_size)
    )
    return await cursor.to_list(length=page_size), total


async def find_brand(collection: Any, brand_id: str) -> dict[str, Any] | None:
    return await collection.find_one({"brand_id": brand_id, "is_active": True})
