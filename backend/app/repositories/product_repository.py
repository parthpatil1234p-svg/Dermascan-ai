from typing import Any


async def find_product(
    collection: Any, product_id_or_slug: str, *, include_inactive: bool = False
) -> dict[str, Any] | None:
    clauses: list[dict[str, Any]] = [
        {"$or": [{"product_id": product_id_or_slug}, {"slug": product_id_or_slug}]}
    ]
    if not include_inactive:
        clauses.append({"is_active": True})
    return await collection.find_one({"$and": clauses})


async def list_products(
    collection: Any, query: dict[str, Any], sort: list[tuple[str, int]], page: int, page_size: int
) -> tuple[list[dict[str, Any]], int]:
    total = await collection.count_documents(query)
    cursor = collection.find(query).sort(sort).skip((page - 1) * page_size).limit(page_size)
    return await cursor.to_list(length=page_size), total


async def insert_product(collection: Any, document: dict[str, Any]) -> None:
    await collection.insert_one(document)


async def replace_product(collection: Any, product_id: str, document: dict[str, Any]) -> bool:
    result = await collection.replace_one({"product_id": product_id}, document)
    return bool(result.matched_count)


async def update_product(collection: Any, product_id: str, fields: dict[str, Any]) -> bool:
    result = await collection.update_one({"product_id": product_id}, {"$set": fields})
    return bool(result.matched_count)
