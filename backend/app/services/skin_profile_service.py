from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.models.skin_profile import (
    build_skin_profile_document,
    skin_profile_document_to_response,
)
from app.schemas.skin_profile import SkinProfileCreate, SkinProfileResponse, SkinProfileUpdate


class DuplicateSkinProfileError(Exception):
    pass


class SkinProfileNotFoundError(Exception):
    pass


async def get_skin_profile_document(collection: Any, user_id: str) -> dict[str, Any] | None:
    return await collection.find_one({"user_id": ObjectId(user_id)})


async def create_skin_profile(
    collection: Any, user_id: str, payload: SkinProfileCreate
) -> SkinProfileResponse:
    if await get_skin_profile_document(collection, user_id):
        raise DuplicateSkinProfileError

    now = datetime.now(timezone.utc)
    document = build_skin_profile_document(user_id=user_id, payload=payload, created_at=now)
    try:
        result = await collection.insert_one(document)
    except DuplicateKeyError as exc:
        raise DuplicateSkinProfileError from exc
    document["_id"] = result.inserted_id
    return skin_profile_document_to_response(document)


async def get_skin_profile(collection: Any, user_id: str) -> SkinProfileResponse:
    document = await get_skin_profile_document(collection, user_id)
    if document is None:
        raise SkinProfileNotFoundError
    return skin_profile_document_to_response(document)


async def update_skin_profile(
    collection: Any, user_id: str, payload: SkinProfileUpdate
) -> SkinProfileResponse:
    existing = await get_skin_profile_document(collection, user_id)
    if existing is None:
        raise SkinProfileNotFoundError

    updates = {
        **payload.model_dump(),
        "is_complete": True,
        "updated_at": datetime.now(timezone.utc),
    }
    await collection.update_one({"user_id": ObjectId(user_id)}, {"$set": updates})
    return skin_profile_document_to_response({**existing, **updates})


async def delete_skin_profile(collection: Any, user_id: str) -> None:
    result = await collection.delete_one({"user_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise SkinProfileNotFoundError
