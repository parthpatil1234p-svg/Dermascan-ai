from typing import Any

from bson import ObjectId


async def find_eligibility_report(
    collection: Any, upload_id: str, user_id: str
) -> dict[str, Any] | None:
    return await collection.find_one({"upload_id": upload_id, "user_id": ObjectId(user_id)})


async def upsert_eligibility_report(collection: Any, document: dict[str, Any]) -> None:
    existing = await collection.find_one({"upload_id": document["upload_id"]})
    if existing is None:
        await collection.insert_one(document)
    else:
        await collection.update_one({"_id": existing["_id"]}, {"$set": document})
