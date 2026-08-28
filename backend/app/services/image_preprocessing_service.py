from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2
from bson import ObjectId
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.model_input_config import get_model_input_contract
from app.models.image_preprocessing import (
    build_image_preprocessing_document,
    image_preprocessing_document_to_response,
)
from app.schemas.image_preprocessing import ImagePreprocessingResponse
from app.services.image_transform_service import (
    ImageTransformationDecodeError,
    ImageTransformationError,
    ImageTransformationResult,
    transform_face_crop,
)
from app.services.upload_service import as_utc, get_owned_upload_document
from app.utils.file_utils import (
    delete_file_safely,
    delete_storage_reference,
    ensure_directory,
    secure_child_path,
)
from app.utils.image_colour import decode_image_to_rgb
from app.utils.image_normalization import validate_model_image

logger = logging.getLogger(__name__)

PREPROCESSABLE_UPLOAD_STATUSES = {
    "face_detected",
    "face_detection_warning",
    "preprocessing_pending",
    "preprocessing_completed",
    "preprocessing_warning",
    "preprocessing_failed",
    "skin_type_analysis_pending",
}


class PreprocessingUploadNotFoundError(Exception):
    pass


class PreprocessingUploadUnavailableError(Exception):
    pass


class PreprocessingConsentRequiredError(Exception):
    pass


class PreprocessingUploadStatusError(Exception):
    pass


class PreprocessingQualityPrerequisiteError(Exception):
    pass


class PreprocessingFacePrerequisiteError(Exception):
    pass


class PreprocessingInProgressError(Exception):
    pass


class PreprocessingCropUnavailableError(Exception):
    pass


class PreprocessingDecodeError(Exception):
    pass


class PreprocessingReportNotFoundError(Exception):
    pass


class PreprocessingProcessingError(Exception):
    pass


@dataclass(frozen=True)
class StoredPreprocessedImage:
    storage_reference: str
    image_format: str
    file_size: int
    physical_path: Path


def get_private_face_crop_path(face_report: dict[str, Any], settings: Settings) -> Path:
    reference = face_report.get("crop_reference")
    if not isinstance(reference, str) or not reference:
        raise PreprocessingCropUnavailableError
    try:
        return secure_child_path(settings.face_crop_path, *Path(reference).parts)
    except ValueError as exc:
        raise PreprocessingCropUnavailableError from exc


def delete_preprocessed_reference(settings: Settings, storage_reference: str | None) -> bool:
    if not storage_reference:
        return False
    return delete_storage_reference(settings.preprocessed_image_path, storage_reference)


def store_preprocessed_image(
    result: ImageTransformationResult,
    *,
    user_id: str,
    upload_id: str,
    settings: Settings,
) -> StoredPreprocessedImage:
    root = settings.preprocessed_image_path
    ensure_directory(root)
    user_folder = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:24]
    upload_folder = hashlib.sha256(upload_id.encode("utf-8")).hexdigest()[:24]
    output_directory = secure_child_path(root, user_folder, upload_folder)
    ensure_directory(output_directory)

    extension = ".jpg" if settings.preprocessed_image_format == "JPEG" else ".png"
    output_path = secure_child_path(output_directory, f"{uuid4().hex}{extension}")
    bgr_image = cv2.cvtColor(result.image, cv2.COLOR_RGB2BGR)
    parameters = (
        [int(cv2.IMWRITE_JPEG_QUALITY), settings.preprocessed_jpeg_quality]
        if extension == ".jpg"
        else [int(cv2.IMWRITE_PNG_COMPRESSION), 3]
    )

    try:
        encoded, buffer = cv2.imencode(extension, bgr_image, parameters)
        if not encoded:
            raise PreprocessingProcessingError
        buffer.tofile(output_path)
        if not output_path.is_file() or output_path.stat().st_size <= 0:
            raise PreprocessingProcessingError
        decoded = decode_image_to_rgb(output_path)
        validate_model_image(decoded.image, get_model_input_contract(settings))
        if output_path.stat().st_size > settings.max_upload_size_bytes:
            raise PreprocessingProcessingError
    except Exception as exc:
        delete_file_safely(output_path)
        if isinstance(exc, PreprocessingProcessingError):
            raise
        raise PreprocessingProcessingError from exc

    return StoredPreprocessedImage(
        storage_reference=output_path.relative_to(root).as_posix(),
        image_format=settings.preprocessed_image_format,
        file_size=output_path.stat().st_size,
        physical_path=output_path,
    )


async def set_preprocessing_upload_status(
    uploads_collection: Any,
    upload_document: dict[str, Any],
    status_value: str,
    now: datetime,
) -> None:
    await uploads_collection.update_one(
        {"_id": upload_document["_id"]},
        {"$set": {"status": status_value, "updated_at": now}},
    )


async def validate_owned_upload_for_preprocessing(
    uploads_collection: Any,
    quality_reports_collection: Any,
    face_reports_collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Path]:
    upload_document = await get_owned_upload_document(uploads_collection, upload_id, user_id)
    if upload_document is None:
        raise PreprocessingUploadNotFoundError

    now = datetime.now(timezone.utc)
    if as_utc(upload_document["expires_at"]) <= now:
        await set_preprocessing_upload_status(uploads_collection, upload_document, "expired", now)
        raise PreprocessingUploadUnavailableError
    if upload_document.get("consent_given") is not True:
        raise PreprocessingConsentRequiredError
    if upload_document.get("status") == "preprocessing":
        raise PreprocessingInProgressError
    if upload_document.get("status") not in PREPROCESSABLE_UPLOAD_STATUSES:
        raise PreprocessingUploadStatusError

    ownership_query = {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    quality_report = await quality_reports_collection.find_one(ownership_query)
    if quality_report is None:
        raise PreprocessingQualityPrerequisiteError
    quality_status = quality_report.get("quality_status")
    if quality_status not in {"passed", "warning"} or (
        quality_status == "warning" and not bool(quality_report.get("warning_accepted", False))
    ):
        raise PreprocessingQualityPrerequisiteError

    face_report = await face_reports_collection.find_one(ownership_query)
    if face_report is None:
        raise PreprocessingFacePrerequisiteError
    detection_status = face_report.get("detection_status")
    if detection_status not in {"passed", "warning"} or (
        detection_status == "warning" and not bool(face_report.get("warning_accepted", False))
    ):
        raise PreprocessingFacePrerequisiteError

    crop_expiry = face_report.get("crop_expires_at") or face_report.get("expires_at")
    if not isinstance(crop_expiry, datetime) or as_utc(crop_expiry) <= now:
        delete_storage_reference(settings.face_crop_path, face_report.get("crop_reference") or "")
        raise PreprocessingCropUnavailableError

    crop_path = get_private_face_crop_path(face_report, settings)
    if not crop_path.is_file():
        raise PreprocessingCropUnavailableError
    return upload_document, quality_report, face_report, crop_path


async def upsert_preprocessing_report(
    reports_collection: Any,
    *,
    upload_id: str,
    user_id: str,
    quality_report: dict[str, Any],
    face_report: dict[str, Any],
    result: ImageTransformationResult,
    stored_image: StoredPreprocessedImage,
    settings: Settings,
    now: datetime,
) -> dict[str, Any]:
    ownership_query = {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    existing = await reports_collection.find_one(ownership_query)
    expires_at = now + timedelta(minutes=settings.preprocessed_image_expiry_minutes)
    document = build_image_preprocessing_document(
        upload_id=upload_id,
        face_report_id=face_report["face_report_id"],
        quality_report_id=quality_report["quality_report_id"],
        user_id=user_id,
        result=result,
        stored_image=stored_image,
        settings=settings,
        now=now,
        expires_at=expires_at,
        existing=existing,
    )
    try:
        if existing is None:
            inserted = await reports_collection.insert_one(document)
            document["_id"] = inserted.inserted_id
        else:
            await reports_collection.update_one({"_id": existing["_id"]}, {"$set": document})
            document["_id"] = existing["_id"]
    except Exception:
        delete_preprocessed_reference(settings, stored_image.storage_reference)
        raise

    old_reference = existing.get("processed_image_reference") if existing else None
    if old_reference and old_reference != stored_image.storage_reference:
        delete_preprocessed_reference(settings, old_reference)
    return document


def upload_status_for_preprocessing(status_value: str) -> str:
    if status_value == "completed":
        return "skin_type_analysis_pending"
    if status_value == "warning":
        return "preprocessing_warning"
    return "preprocessing_failed"


async def process_owned_face_crop(
    uploads_collection: Any,
    quality_reports_collection: Any,
    face_reports_collection: Any,
    reports_collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> ImagePreprocessingResponse:
    upload_document, quality_report, face_report, crop_path = (
        await validate_owned_upload_for_preprocessing(
            uploads_collection,
            quality_reports_collection,
            face_reports_collection,
            upload_id,
            user_id,
            settings,
        )
    )
    original_status = upload_document["status"]
    await set_preprocessing_upload_status(
        uploads_collection,
        upload_document,
        "preprocessing",
        datetime.now(timezone.utc),
    )

    try:
        result = await run_in_threadpool(transform_face_crop, crop_path, settings)
        stored_image = await run_in_threadpool(
            store_preprocessed_image,
            result,
            user_id=user_id,
            upload_id=upload_id,
            settings=settings,
        )
        completed_at = datetime.now(timezone.utc)
        report = await upsert_preprocessing_report(
            reports_collection,
            upload_id=upload_id,
            user_id=user_id,
            quality_report=quality_report,
            face_report=face_report,
            result=result,
            stored_image=stored_image,
            settings=settings,
            now=completed_at,
        )
        await set_preprocessing_upload_status(
            uploads_collection,
            upload_document,
            upload_status_for_preprocessing(result.status),
            completed_at,
        )
        return image_preprocessing_document_to_response(report, settings)
    except ImageTransformationDecodeError as exc:
        await set_preprocessing_upload_status(
            uploads_collection,
            upload_document,
            "preprocessing_failed",
            datetime.now(timezone.utc),
        )
        raise PreprocessingDecodeError from exc
    except (ImageTransformationError, PreprocessingProcessingError) as exc:
        await set_preprocessing_upload_status(
            uploads_collection,
            upload_document,
            original_status,
            datetime.now(timezone.utc),
        )
        raise PreprocessingProcessingError from exc
    except Exception as exc:
        await set_preprocessing_upload_status(
            uploads_collection,
            upload_document,
            original_status,
            datetime.now(timezone.utc),
        )
        raise PreprocessingProcessingError from exc


async def get_owned_preprocessing_report(
    uploads_collection: Any,
    reports_collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> ImagePreprocessingResponse:
    upload_document = await get_owned_upload_document(uploads_collection, upload_id, user_id)
    if upload_document is None:
        raise PreprocessingUploadNotFoundError
    report = await reports_collection.find_one(
        {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    )
    if report is None:
        raise PreprocessingReportNotFoundError
    return image_preprocessing_document_to_response(report, settings)


async def cleanup_expired_preprocessed_images(collection: Any, settings: Settings) -> int:
    now = datetime.now(timezone.utc)
    cursor = collection.find({"expires_at": {"$lte": now}})
    cleaned_count = 0
    async for document in cursor:
        delete_preprocessed_reference(settings, document.get("processed_image_reference"))
        await collection.update_one(
            {"_id": document["_id"]},
            {
                "$set": {
                    "preprocessing_status": "expired",
                    "processed_image_reference": None,
                    "updated_at": now,
                }
            },
        )
        cleaned_count += 1
        logger.info("Expired preprocessed image cleaned.")
    return cleaned_count
