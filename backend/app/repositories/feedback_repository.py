from datetime import datetime
from typing import Any

from bson import ObjectId

ACTIVE_FEEDBACK_STATUSES = ("active", "edited", "flagged")


async def insert_feedback(collection: Any, document: dict[str, Any]) -> None:
    await collection.insert_one(document)


async def find_owned_feedback(collection: Any, feedback_id: str, user_id: str) -> dict | None:
    return await collection.find_one({"feedback_id": feedback_id, "user_id": ObjectId(user_id)})


async def replace_feedback(collection: Any, document: dict[str, Any]) -> None:
    await collection.replace_one({"_id": document["_id"]}, document)


async def recent_owned_feedback(collection: Any, user_id: str, since: datetime) -> list[dict]:
    return await collection.find(
        {"user_id": ObjectId(user_id), "created_at": {"$gte": since}}
    ).to_list(length=None)


async def list_owned_feedback(
    collection: Any, user_id: str, query: dict[str, Any], *, page: int, page_size: int
) -> tuple[list[dict], int]:
    owned_query = {"user_id": ObjectId(user_id), **query}
    total = await collection.count_documents(owned_query)
    items = (
        await collection.find(owned_query)
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list(length=page_size)
    )
    return items, total
