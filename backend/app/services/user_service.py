from datetime import datetime, timedelta, timezone
import secrets
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.user import build_user_document, to_object_id, user_document_to_public
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserPublic
from app.services.email_service import send_password_reset_email


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class InvalidResetOtpError(Exception):
    pass


class ExpiredResetOtpError(Exception):
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


async def create_password_reset_otp(
    users_collection: Any,
    email: str,
) -> tuple[str, bool]:
    settings = get_settings()
    user = await get_user_by_email(users_collection, email)
    if not user:
        raise UserNotFoundError("No account found with this email address.")

    if not user.get("is_active", True):
        raise InactiveUserError("Account is inactive.")

    # Generate 6-digit numeric OTP
    otp = "".join(secrets.choice("0123456789") for _ in range(6))
    otp_hash = hash_password(otp)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.reset_otp_expire_minutes)

    await users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "reset_otp_hash": otp_hash,
                "reset_otp_expires_at": expires_at,
                "updated_at": now,
            }
        },
    )

    email_sent = await send_password_reset_email(
        recipient_email=user["email"],
        otp=otp,
        user_name=user.get("full_name"),
    )

    return otp, email_sent


async def reset_user_password(
    users_collection: Any,
    email: str,
    otp: str,
    new_password: str,
) -> UserPublic:
    user = await get_user_by_email(users_collection, email)
    if not user:
        raise UserNotFoundError("No account found with this email address.")

    stored_hash = user.get("reset_otp_hash")
    expires_at = user.get("reset_otp_expires_at")

    if not stored_hash or not expires_at:
        raise InvalidResetOtpError("No active password reset request found. Please request a new code.")

    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        raise ExpiredResetOtpError("The verification code has expired. Please request a new one.")

    if not verify_password(otp, stored_hash):
        raise InvalidResetOtpError("Invalid verification code.")

    new_hash = hash_password(new_password)

    await users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": new_hash,
                "updated_at": now,
            },
            "$unset": {
                "reset_otp_hash": "",
                "reset_otp_expires_at": "",
            },
        },
    )

    updated_user = await users_collection.find_one({"_id": user["_id"]})
    return user_document_to_public(updated_user)


def ensure_object_id(value: str | ObjectId) -> str:
    return str(value)

