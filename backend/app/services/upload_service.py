import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId
from fastapi import UploadFile

from app.core.config import Settings
from app.models.image_upload import (
    build_image_upload_document,
    image_upload_document_to_response,
    image_upload_document_to_status,
)
from app.schemas.image_upload import ImageUploadResponse, ImageUploadStatusResponse
from app.services.file_validation_service import validate_and_store_image
from app.utils.file_utils import delete_file_safely, delete_storage_reference

logger = logging.getLogger(__name__)


class ImageUploadNotFoundError(Exception):
    pass


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


async def create_validated_upload(
    collection: Any,
    uploaded_file: UploadFile,
    user_id: str,
    settings: Settings,
) -> ImageUploadResponse:
    stored_image = await validate_and_store_image(uploaded_file, user_id, settings)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.temp_upload_expiry_minutes)
    document = build_image_upload_document(
        user_id=user_id,
        upload_id=stored_image.upload_id,
        stored_filename=stored_image.stored_filename,
        storage_reference=stored_image.storage_reference,
        original_extension=stored_image.original_extension,
        mime_type=stored_image.mime_type,
        image_format=stored_image.image_format,
        file_size_bytes=stored_image.file_size_bytes,
        width=stored_image.width,
        height=stored_image.height,
        created_at=now,
        expires_at=expires_at,
    )

    try:
        result = await collection.insert_one(document)
    except Exception:
        delete_file_safely(stored_image.physical_path)
        raise

    document["_id"] = result.inserted_id
    return image_upload_document_to_response(document)


async def get_owned_upload_document(
    collection: Any,
    upload_id: str,
    user_id: str,
) -> dict[str, Any] | None:
    return await collection.find_one({"upload_id": upload_id, "user_id": ObjectId(user_id)})


async def get_owned_upload_status(
    collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> ImageUploadStatusResponse:
    document = await get_owned_upload_document(collection, upload_id, user_id)
    if document is None:
        raise ImageUploadNotFoundError

    now = datetime.now(timezone.utc)
    if as_utc(document["expires_at"]) <= now and document.get("status") != "expired":
        delete_storage_reference(settings.upload_path, document["storage_reference"])
        await collection.update_one(
            {"_id": document["_id"]},
            {"$set": {"status": "expired", "updated_at": now}},
        )
        document = {**document, "status": "expired", "updated_at": now}

    return image_upload_document_to_status(document)


async def delete_owned_upload(
    collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
    quality_reports_collection: Any | None = None,
    face_reports_collection: Any | None = None,
    preprocessing_reports_collection: Any | None = None,
    skin_type_reports_collection: Any | None = None,
    skin_concern_reports_collection: Any | None = None,
) -> None:
    document = await get_owned_upload_document(collection, upload_id, user_id)
    if document is None:
        raise ImageUploadNotFoundError

    delete_storage_reference(settings.upload_path, document["storage_reference"])
    if quality_reports_collection is not None:
        await quality_reports_collection.delete_one(
            {"upload_id": upload_id, "user_id": ObjectId(user_id)}
        )
    if face_reports_collection is not None:
        face_report = await face_reports_collection.find_one(
            {"upload_id": upload_id, "user_id": ObjectId(user_id)}
        )
        if face_report is not None:
            delete_storage_reference(
                settings.face_crop_path,
                face_report.get("crop_reference") or "",
            )
            await face_reports_collection.delete_one({"_id": face_report["_id"]})
    if preprocessing_reports_collection is not None:
        preprocessing_report = await preprocessing_reports_collection.find_one(
            {"upload_id": upload_id, "user_id": ObjectId(user_id)}
        )
        if preprocessing_report is not None:
            delete_storage_reference(
                settings.preprocessed_image_path,
                preprocessing_report.get("processed_image_reference") or "",
            )
            await preprocessing_reports_collection.delete_one({"_id": preprocessing_report["_id"]})
    if skin_type_reports_collection is not None:
        await skin_type_reports_collection.delete_one(
            {"upload_id": upload_id, "user_id": ObjectId(user_id)}
        )
    if skin_concern_reports_collection is not None:
        await skin_concern_reports_collection.delete_one(
            {"upload_id": upload_id, "user_id": ObjectId(user_id)}
        )
    await collection.delete_one({"_id": document["_id"]})
    logger.info("Temporary file removed.")


async def cleanup_expired_uploads(
    collection: Any,
    settings: Settings,
    quality_reports_collection: Any | None = None,
    face_reports_collection: Any | None = None,
    preprocessing_reports_collection: Any | None = None,
    skin_type_reports_collection: Any | None = None,
    skin_concern_reports_collection: Any | None = None,
) -> int:
    now = datetime.now(timezone.utc)
    cursor = collection.find(
        {
            "expires_at": {"$lte": now},
            "status": {"$ne": "expired"},
        }
    )
    cleaned_count = 0
    async for document in cursor:
        delete_storage_reference(settings.upload_path, document["storage_reference"])
        if quality_reports_collection is not None:
            await quality_reports_collection.delete_one(
                {
                    "upload_id": document["upload_id"],
                    "user_id": document["user_id"],
                }
            )
        if face_reports_collection is not None:
            face_report = await face_reports_collection.find_one(
                {
                    "upload_id": document["upload_id"],
                    "user_id": document["user_id"],
                }
            )
            if face_report is not None:
                delete_storage_reference(
                    settings.face_crop_path,
                    face_report.get("crop_reference") or "",
                )
                await face_reports_collection.delete_one({"_id": face_report["_id"]})
        if preprocessing_reports_collection is not None:
            preprocessing_report = await preprocessing_reports_collection.find_one(
                {
                    "upload_id": document["upload_id"],
                    "user_id": document["user_id"],
                }
            )
            if preprocessing_report is not None:
                delete_storage_reference(
                    settings.preprocessed_image_path,
                    preprocessing_report.get("processed_image_reference") or "",
                )
                await preprocessing_reports_collection.delete_one(
                    {"_id": preprocessing_report["_id"]}
                )
        if skin_type_reports_collection is not None:
            await skin_type_reports_collection.delete_one(
                {
                    "upload_id": document["upload_id"],
                    "user_id": document["user_id"],
                }
            )
        if skin_concern_reports_collection is not None:
            await skin_concern_reports_collection.delete_one(
                {
                    "upload_id": document["upload_id"],
                    "user_id": document["user_id"],
                }
            )
        await collection.update_one(
            {"_id": document["_id"]},
            {"$set": {"status": "expired", "updated_at": now}},
        )
        cleaned_count += 1
        logger.info("Expired upload cleaned.")
    return cleaned_count
