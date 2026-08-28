from datetime import datetime
from typing import Any

from bson import ObjectId

from app.schemas.image_upload import (
    ImageUploadResponse,
    ImageUploadStatusResponse,
    UploadedFileInfo,
)


def build_image_upload_document(
    *,
    user_id: str,
    upload_id: str,
    stored_filename: str,
    storage_reference: str,
    original_extension: str,
    mime_type: str,
    image_format: str,
    file_size_bytes: int,
    width: int,
    height: int,
    created_at: datetime,
    expires_at: datetime,
) -> dict[str, Any]:
    return {
        "user_id": ObjectId(user_id),
        "upload_id": upload_id,
        "stored_filename": stored_filename,
        "storage_reference": storage_reference,
        "original_extension": original_extension,
        "mime_type": mime_type,
        "image_format": image_format,
        "file_size_bytes": file_size_bytes,
        "width": width,
        "height": height,
        "status": "validated",
        "consent_given": True,
        "consent_given_at": created_at,
        "created_at": created_at,
        "expires_at": expires_at,
        "updated_at": created_at,
    }


def image_upload_document_to_status(
    document: dict[str, Any],
) -> ImageUploadStatusResponse:
    return ImageUploadStatusResponse(
        upload_id=document["upload_id"],
        status=document["status"],
        file=UploadedFileInfo(
            format=document["image_format"],
            size_bytes=document["file_size_bytes"],
            width=document["width"],
            height=document["height"],
        ),
        created_at=document["created_at"],
        expires_at=document["expires_at"],
    )


def image_upload_document_to_response(
    document: dict[str, Any],
) -> ImageUploadResponse:
    status_response = image_upload_document_to_status(document)
    return ImageUploadResponse(**status_response.model_dump())
