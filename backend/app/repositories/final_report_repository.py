from datetime import datetime
from typing import Any

from bson import ObjectId


async def find_owned_final_report(
    collection: Any, final_report_id: str, user_id: str
) -> dict | None:
    return await collection.find_one(
        {"final_report_id": final_report_id, "user_id": ObjectId(user_id)}
    )


async def find_latest_owned_report(collection: Any, upload_id: str, user_id: str) -> dict | None:
    cursor = collection.find(
        {
            "upload_id": upload_id,
            "user_id": ObjectId(user_id),
            "report_status": {"$ne": "superseded"},
            "is_archived": False,
        }
    ).sort([("report_version", -1)])
    items = await cursor.to_list(length=1)
    return items[0] if items else None


async def find_all_for_upload(collection: Any, upload_id: str, user_id: str) -> list[dict]:
    return (
        await collection.find({"upload_id": upload_id, "user_id": ObjectId(user_id)})
        .sort("report_version", -1)
        .to_list(length=None)
    )


async def insert_final_report(collection: Any, document: dict) -> None:
    await collection.insert_one(document)


async def supersede_report(
    collection: Any, previous: dict, new_report_id: str, now: datetime
) -> None:
    await collection.update_one(
        {"_id": previous["_id"]},
        {
            "$set": {
                "report_status": "superseded",
                "superseded_by_report_id": new_report_id,
                "updated_at": now,
            }
        },
    )


async def archive_report(collection: Any, document: dict, now: datetime) -> None:
    await collection.update_one(
        {"_id": document["_id"]},
        {"$set": {"is_archived": True, "archived_at": now, "updated_at": now}},
    )
