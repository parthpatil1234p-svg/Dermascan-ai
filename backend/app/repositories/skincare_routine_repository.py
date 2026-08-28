from typing import Any

from bson import ObjectId


async def find_owned_routine(collection: Any, upload_id: str, user_id: str) -> dict | None:
    return await collection.find_one({"upload_id": upload_id, "user_id": ObjectId(user_id)})


async def upsert_routine(collection: Any, document: dict) -> None:
    await collection.replace_one({"upload_id": document["upload_id"]}, document, upsert=True)
