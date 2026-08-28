from datetime import datetime
from typing import Any

from bson import ObjectId

from app.schemas.user import UserPublic


def to_object_id(value: str) -> ObjectId | None:
    if not ObjectId.is_valid(value):
        return None
    return ObjectId(value)


def user_document_to_public(document: dict[str, Any]) -> UserPublic:
    return UserPublic(
        id=str(document["_id"]),
        full_name=document["full_name"],
        email=document["email"],
        age_group=document.get("age_group"),
        location=document.get("location"),
        is_active=document.get("is_active", True),
        is_admin=document.get("is_admin", False),
        created_at=document["created_at"],
        updated_at=document.get("updated_at"),
    )


def build_user_document(
    *,
    full_name: str,
    email: str,
    password_hash: str,
    age_group: str | None,
    location: str | None,
    created_at: datetime,
) -> dict[str, Any]:
    return {
        "full_name": full_name,
        "email": email,
        "password_hash": password_hash,
        "age_group": age_group,
        "location": location,
        "is_active": True,
        "is_admin": False,
        "created_at": created_at,
        "updated_at": created_at,
    }
