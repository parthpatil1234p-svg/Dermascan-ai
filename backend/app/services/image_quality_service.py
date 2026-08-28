from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bson import ObjectId
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.models.image_quality import (
    build_image_quality_document,
    image_quality_document_to_response,
)
from app.schemas.image_quality import (
    ImageQualityResponse,
    WarningAcceptanceResponse,
)
from app.services.image_quality_scoring_service import evaluate_image_quality
from app.services.upload_service import as_utc, get_owned_upload_document
from app.utils.file_utils import delete_storage_reference, secure_child_path
from app.utils.image_metrics import ImageDecodeError, calculate_image_metrics

ANALYZABLE_UPLOAD_STATUSES = {
    "validated",
    "quality_passed",
    "quality_warning",
    "quality_failed",
    "face_detection_pending",
}


class QualityUploadNotFoundError(Exception):
    pass


class QualityUploadUnavailableError(Exception):
    pass


class QualityConsentRequiredError(Exception):
    pass


class QualityAnalysisInProgressError(Exception):
    pass


class QualityUploadStatusError(Exception):
    pass


class QualityReportNotFoundError(Exception):
    pass


class QualityWarningNotAllowedError(Exception):
    pass


class QualityImageDecodeError(Exception):
    pass


class QualityProcessingError(Exception):
    pass


def get_private_image_path(upload_document: dict[str, Any], settings: Settings) -> Path:
    reference = upload_document.get("storage_reference")
    if not isinstance(reference, str) or not reference:
        raise QualityUploadUnavailableError
    try:
        return secure_child_path(settings.upload_path, *Path(reference).parts)
    except ValueError as exc:
        raise QualityUploadUnavailableError from exc


async def set_upload_status(
    uploads_collection: Any,
    upload_document: dict[str, Any],
    status_value: str,
    now: datetime,
) -> None:
    await uploads_collection.update_one(
        {"_id": upload_document["_id"]},
        {"$set": {"status": status_value, "updated_at": now}},
    )


async def validate_owned_upload_for_quality(
    uploads_collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> tuple[dict[str, Any], Path]:
    upload_document = await get_owned_upload_document(uploads_collection, upload_id, user_id)
    if upload_document is None:
        raise QualityUploadNotFoundError

    now = datetime.now(timezone.utc)
    if as_utc(upload_document["expires_at"]) <= now:
        delete_storage_reference(settings.upload_path, upload_document.get("storage_reference", ""))
        await set_upload_status(uploads_collection, upload_document, "expired", now)
        raise QualityUploadUnavailableError
    if upload_document.get("consent_given") is not True:
        raise QualityConsentRequiredError

    upload_status = upload_document.get("status")
    if upload_status == "quality_checking":
        raise QualityAnalysisInProgressError
    if upload_status not in ANALYZABLE_UPLOAD_STATUSES:
        raise QualityUploadStatusError

    image_path = get_private_image_path(upload_document, settings)
    if not image_path.is_file():
        await set_upload_status(uploads_collection, upload_document, "quality_failed", now)
        raise QualityUploadUnavailableError
    return upload_document, image_path


async def upsert_quality_report(
    reports_collection: Any,
    *,
    upload_id: str,
    user_id: str,
    raw_metrics: Any,
    evaluation: Any,
    now: datetime,
) -> dict[str, Any]:
    ownership_query = {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    existing = await reports_collection.find_one(ownership_query)
    document = build_image_quality_document(
        upload_id=upload_id,
        user_id=user_id,
        raw_metrics=raw_metrics,
        evaluation=evaluation,
        now=now,
        existing=existing,
    )

    if existing is None:
        result = await reports_collection.insert_one(document)
        document["_id"] = result.inserted_id
    else:
        await reports_collection.update_one(
            {"_id": existing["_id"]},
            {"$set": document},
        )
        document["_id"] = existing["_id"]
    return document


async def analyze_owned_image_quality(
    uploads_collection: Any,
    reports_collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> ImageQualityResponse:
    upload_document, image_path = await validate_owned_upload_for_quality(
        uploads_collection, upload_id, user_id, settings
    )
    original_status = upload_document["status"]
    checking_time = datetime.now(timezone.utc)
    await set_upload_status(uploads_collection, upload_document, "quality_checking", checking_time)

    try:
        raw_metrics = await run_in_threadpool(
            calculate_image_metrics,
            image_path,
            dark_pixel_threshold=settings.dark_pixel_threshold,
            bright_pixel_threshold=settings.bright_pixel_threshold,
        )
        evaluation = evaluate_image_quality(raw_metrics, settings)
        completed_at = datetime.now(timezone.utc)
        report_document = await upsert_quality_report(
            reports_collection,
            upload_id=upload_id,
            user_id=user_id,
            raw_metrics=raw_metrics,
            evaluation=evaluation,
            now=completed_at,
        )
        final_upload_status = f"quality_{evaluation.quality_status}"
        await set_upload_status(
            uploads_collection,
            upload_document,
            final_upload_status,
            completed_at,
        )
        return image_quality_document_to_response(report_document)
    except ImageDecodeError as exc:
        await set_upload_status(
            uploads_collection,
            upload_document,
            "quality_failed",
            datetime.now(timezone.utc),
        )
        raise QualityImageDecodeError from exc
    except Exception as exc:
        await set_upload_status(
            uploads_collection,
            upload_document,
            original_status,
            datetime.now(timezone.utc),
        )
        raise QualityProcessingError from exc


async def get_owned_quality_report(
    uploads_collection: Any,
    reports_collection: Any,
    upload_id: str,
    user_id: str,
) -> ImageQualityResponse:
    upload_document = await get_owned_upload_document(uploads_collection, upload_id, user_id)
    if upload_document is None:
        raise QualityUploadNotFoundError

    document = await reports_collection.find_one(
        {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    )
    if document is None:
        raise QualityReportNotFoundError
    return image_quality_document_to_response(document)


async def accept_owned_quality_warning(
    uploads_collection: Any,
    reports_collection: Any,
    upload_id: str,
    user_id: str,
) -> WarningAcceptanceResponse:
    upload_document = await get_owned_upload_document(uploads_collection, upload_id, user_id)
    if upload_document is None:
        raise QualityUploadNotFoundError

    ownership_query = {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    document = await reports_collection.find_one(ownership_query)
    if document is None:
        raise QualityReportNotFoundError
    if document.get("quality_status") != "warning":
        raise QualityWarningNotAllowedError

    now = datetime.now(timezone.utc)
    await reports_collection.update_one(
        {"_id": document["_id"]},
        {
            "$set": {
                "warning_accepted": True,
                "warning_accepted_at": now,
                "updated_at": now,
            }
        },
    )
    await set_upload_status(uploads_collection, upload_document, "face_detection_pending", now)
    return WarningAcceptanceResponse(
        quality_report_id=document["quality_report_id"],
        upload_id=upload_id,
        quality_status="warning",
        warning_accepted=True,
        warning_accepted_at=now,
        can_continue=True,
        next_route="/face-detection",
    )
