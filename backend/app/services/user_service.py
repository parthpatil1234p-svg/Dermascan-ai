from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.security import hash_password, verify_password
from app.models.user import build_user_document, to_object_id, user_document_to_public
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserPublic


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


DUMMY_PASSWORD_HASH = hash_password("dermascan-authentication-timing-placeholder")


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def get_user_by_email(
    users_collection: Any,
    email: str,
) -> dict[str, Any] | None:
    return await users_collection.find_one({"email": normalize_email(email)})


async def get_user_by_id(
    users_collection: Any,
    user_id: str,
) -> dict[str, Any] | None:
    object_id = to_object_id(user_id)
    if object_id is None:
        return None
    return await users_collection.find_one({"_id": object_id})


async def create_user(
    users_collection: Any,
    payload: RegisterRequest,
) -> UserPublic:
    email = normalize_email(payload.email)

    if await get_user_by_email(users_collection, email):
        raise DuplicateEmailError("An account with this email already exists.")

    now = datetime.now(timezone.utc)
    document = build_user_document(
        full_name=payload.full_name,
        email=email,
        password_hash=hash_password(payload.password),
        age_group=payload.age_group,
        location=payload.location,
        created_at=now,
    )

    try:
        insert_result = await users_collection.insert_one(document)
    except DuplicateKeyError as exc:
        raise DuplicateEmailError("An account with this email already exists.") from exc

    document["_id"] = insert_result.inserted_id
    return user_document_to_public(document)


async def authenticate_user(
    users_collection: Any,
    email: str,
    password: str,
) -> UserPublic:
    user = await get_user_by_email(users_collection, email)
    candidate_hash = user["password_hash"] if user else DUMMY_PASSWORD_HASH
    password_is_valid = verify_password(password, candidate_hash)

    if not user or not password_is_valid:
        raise InvalidCredentialsError("Invalid email or password.")

    if not user.get("is_active", True):
        raise InactiveUserError("Account is inactive.")

    return user_document_to_public(user)


def ensure_object_id(value: str | ObjectId) -> str:
    return str(value)
