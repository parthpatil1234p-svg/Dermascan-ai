from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import cv2
from bson import ObjectId
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.models.face_detection import (
    build_face_detection_document,
    face_detection_document_to_response,
)
from app.schemas.face_detection import (
    FaceDetectionIssue,
    FaceDetectionResponse,
    FaceWarningAcceptanceResponse,
)
from app.services.face_crop_service import (
    FaceCropStorageError,
    FaceCropTooSmallError,
    StoredFaceCrop,
    create_private_face_crop,
    delete_face_crop_reference,
)
from app.services.face_detection_service import (
    DetectedFace,
    FaceDetector,
    FaceDetectorProcessingError,
    FaceDetectorUnavailableError,
    get_face_detector,
)
from app.services.upload_service import as_utc, get_owned_upload_document
from app.utils.bounding_box import (
    NormalizedBoundingBox,
    PixelBoundingBox,
    add_padding_to_pixel_box,
    boundary_issue_codes,
    box_area_ratio,
    box_center_offset,
    normalized_box_has_image_overlap,
    normalized_to_pixel_box,
)
from app.utils.file_utils import delete_storage_reference, secure_child_path

DETECTABLE_UPLOAD_STATUSES = {
    "quality_passed",
    "quality_warning",
    "face_detection_pending",
    "face_detected",
    "face_detection_warning",
    "face_detection_failed",
    "preprocessing_pending",
}


class DetectionUploadNotFoundError(Exception):
    pass


class DetectionUploadUnavailableError(Exception):
    pass


class DetectionConsentRequiredError(Exception):
    pass


class DetectionUploadStatusError(Exception):
    pass


class DetectionQualityPrerequisiteError(Exception):
    pass


class DetectionAnalysisInProgressError(Exception):
    pass


class DetectionReportNotFoundError(Exception):
    pass


class DetectionWarningNotAllowedError(Exception):
    pass


class DetectionImageDecodeError(Exception):
    pass


class DetectionProcessingError(Exception):
    pass


@dataclass
class FaceDetectionEvaluation:
    detection_status: str
    face_count: int
    detection_confidence: float | None
    bounding_box_normalized: NormalizedBoundingBox | None
    bounding_box_pixels: PixelBoundingBox | None
    face_area_ratio: float | None
    face_center_offset: float | None
    face_position_status: str
    face_size_status: str
    crop_box: PixelBoundingBox | None
    issues: list[FaceDetectionIssue]
    recommendations: list[str]


def detection_issue(
    code: str,
    severity: str,
    message: str,
    recommendation: str,
) -> FaceDetectionIssue:
    return FaceDetectionIssue(
        code=code,
        severity=severity,
        message=message,
        recommendation=recommendation,
    )


def unique_recommendations(issues: list[FaceDetectionIssue]) -> list[str]:
    recommendations: list[str] = []
    seen: set[str] = set()
    for issue in issues:
        if issue.recommendation not in seen:
            seen.add(issue.recommendation)
            recommendations.append(issue.recommendation)
    return recommendations


def detection_status_from_issues(issues: list[FaceDetectionIssue]) -> str:
    if any(issue.severity == "error" for issue in issues):
        return "failed"
    if issues:
        return "warning"
    return "passed"


def empty_detection_result(
    issue: FaceDetectionIssue, face_count: int = 0
) -> FaceDetectionEvaluation:
    return FaceDetectionEvaluation(
        detection_status="failed",
        face_count=face_count,
        detection_confidence=None,
        bounding_box_normalized=None,
        bounding_box_pixels=None,
        face_area_ratio=None,
        face_center_offset=None,
        face_position_status="not_applicable",
        face_size_status="not_applicable",
        crop_box=None,
        issues=[issue],
        recommendations=[issue.recommendation],
    )


def build_face_detection_evaluation(
    *,
    detections: list[DetectedFace],
    image_width: int,
    image_height: int,
    settings: Settings,
) -> FaceDetectionEvaluation:
    if not detections:
        return empty_detection_result(
            detection_issue(
                "NO_FACE_DETECTED",
                "error",
                "No clear face was detected.",
                "Upload a front-facing image with the complete face visible.",
            )
        )

    confident_faces = [
        face for face in detections if face.confidence >= settings.face_detection_min_confidence
    ]

    if not confident_faces:
        return empty_detection_result(
            detection_issue(
                "LOW_FACE_DETECTION_CONFIDENCE",
                "error",
                "The face detector could not identify a face with enough confidence.",
                "Use a clearer, front-facing image with even lighting.",
            ),
            face_count=len(detections),
        )

    if len(confident_faces) > 1:
        return FaceDetectionEvaluation(
            detection_status="failed",
            face_count=len(confident_faces),
            detection_confidence=max(face.confidence for face in confident_faces),
            bounding_box_normalized=None,
            bounding_box_pixels=None,
            face_area_ratio=None,
            face_center_offset=None,
            face_position_status="not_applicable",
            face_size_status="not_applicable",
            crop_box=None,
            issues=[
                detection_issue(
                    "MULTIPLE_FACES_DETECTED",
                    "error",
                    "Multiple faces were detected.",
                    "Upload an image containing only one person.",
                )
            ],
            recommendations=["Upload an image containing only one person."],
        )

    detected_face = confident_faces[0]
    normalized_box = detected_face.bounding_box
    if not normalized_box_has_image_overlap(normalized_box):
        return empty_detection_result(
            detection_issue(
                "INVALID_FACE_BOUNDING_BOX",
                "error",
                "The detected face area was invalid.",
                "Upload a clearer image with the full face visible.",
            ),
            face_count=1,
        )

    pixel_box = normalized_to_pixel_box(
        normalized_box,
        image_width,
        image_height,
    )
    if pixel_box is None:
        return empty_detection_result(
            detection_issue(
                "INVALID_FACE_BOUNDING_BOX",
                "error",
                "The detected face area could not be safely located.",
                "Upload a clearer image with the full face visible.",
            ),
            face_count=1,
        )

    area_ratio = box_area_ratio(pixel_box, image_width, image_height)
    center_offset = box_center_offset(pixel_box, image_width, image_height)
    issues: list[FaceDetectionIssue] = []

    if area_ratio < settings.face_min_area_ratio:
        face_size_status = "too_small"
        issues.append(
            detection_issue(
                "FACE_TOO_SMALL",
                "error",
                "The face is too far from the camera.",
                "Capture a closer image with the face clearly visible.",
            )
        )
    elif area_ratio > settings.face_max_area_ratio:
        face_size_status = "too_close"
        issues.append(
            detection_issue(
                "FACE_TOO_CLOSE",
                "error",
                "The face is too close to the camera.",
                "Move slightly back and keep the full face visible.",
            )
        )
    else:
        face_size_status = "acceptable"

    if center_offset > settings.face_max_center_offset:
        face_position_status = "too_far_off_center"
        issues.append(
            detection_issue(
                "FACE_NOT_CENTERED",
                "error",
                "The face is too far from the centre.",
                "Capture the image while looking directly at the camera.",
            )
        )
    elif center_offset >= settings.face_max_center_offset * 0.6:
        face_position_status = "slightly_off_center"
        issues.append(
            detection_issue(
                "FACE_SLIGHTLY_OFF_CENTER",
                "warning",
                "The face is slightly off-centre.",
                "Position the face near the centre of the camera frame.",
            )
        )
    else:
        face_position_status = "centered"

    if (
        normalized_box.x < 0
        or normalized_box.y < 0
        or normalized_box.x + normalized_box.width > 1
        or normalized_box.y + normalized_box.height > 1
    ):
        issues.append(
            detection_issue(
                "FACE_PARTIALLY_OUTSIDE_IMAGE",
                "warning",
                "Part of the detected face area may be outside the image.",
                "Keep the full forehead, cheeks, and chin visible.",
            )
        )

    edge_messages = {
        "FACE_TOUCHES_TOP_EDGE": "The face appears close to the top edge.",
        "FACE_TOUCHES_BOTTOM_EDGE": "The face appears close to the bottom edge.",
        "FACE_TOUCHES_LEFT_EDGE": "The face appears close to the left edge.",
        "FACE_TOUCHES_RIGHT_EDGE": "The face appears close to the right edge.",
    }
    for code in boundary_issue_codes(
        pixel_box,
        image_width,
        image_height,
        settings.face_edge_margin_ratio,
    ):
        issues.append(
            detection_issue(
                code,
                "warning",
                edge_messages[code],
                "Keep the full forehead, cheeks, and chin visible.",
            )
        )

    crop_box = None
    if not any(issue.severity == "error" for issue in issues):
        crop_box = add_padding_to_pixel_box(
            pixel_box,
            image_width,
            image_height,
            settings.face_crop_padding_ratio,
        )
        if crop_box is None:
            issues.append(
                detection_issue(
                    "FACE_CROP_FAILED",
                    "error",
                    "The facial region could not be prepared safely.",
                    "Upload a clearer image with the complete face visible.",
                )
            )

    return FaceDetectionEvaluation(
        detection_status=detection_status_from_issues(issues),
        face_count=1,
        detection_confidence=detected_face.confidence,
        bounding_box_normalized=normalized_box,
        bounding_box_pixels=pixel_box,
        face_area_ratio=area_ratio,
        face_center_offset=center_offset,
        face_position_status=face_position_status,
        face_size_status=face_size_status,
        crop_box=crop_box,
        issues=issues,
        recommendations=unique_recommendations(issues),
    )


def run_face_detection_pipeline(
    *,
    image_path: Path,
    user_id: str,
    upload_id: str,
    settings: Settings,
    detector: FaceDetector,
) -> tuple[FaceDetectionEvaluation, StoredFaceCrop | None]:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise DetectionImageDecodeError

    image_height, image_width = image.shape[:2]
    try:
        detections = detector.detect(image)
    except (FaceDetectorProcessingError, FaceDetectorUnavailableError) as exc:
        raise DetectionProcessingError from exc
    except Exception as exc:
        raise DetectionProcessingError from exc

    evaluation = build_face_detection_evaluation(
        detections=detections,
        image_width=image_width,
        image_height=image_height,
        settings=settings,
    )

    if evaluation.crop_box is None:
        return evaluation, None

    try:
        crop = create_private_face_crop(
            image=image,
            crop_box=evaluation.crop_box,
            user_id=user_id,
            upload_id=upload_id,
            settings=settings,
        )
        return evaluation, crop
    except FaceCropTooSmallError:
        issue = detection_issue(
            "FACE_CROP_TOO_SMALL",
            "error",
            "The prepared facial region is too small.",
            "Upload a closer, clearer image with the complete face visible.",
        )
        evaluation.issues.append(issue)
        evaluation.recommendations = unique_recommendations(evaluation.issues)
        evaluation.detection_status = "failed"
        return evaluation, None
    except FaceCropStorageError as exc:
        raise DetectionProcessingError from exc


def get_private_upload_path(upload_document: dict[str, Any], settings: Settings) -> Path:
    reference = upload_document.get("storage_reference")
    if not isinstance(reference, str) or not reference:
        raise DetectionUploadUnavailableError
    try:
        return secure_child_path(settings.upload_path, *Path(reference).parts)
    except ValueError as exc:
        raise DetectionUploadUnavailableError from exc


async def set_detection_upload_status(
    uploads_collection: Any,
    upload_document: dict[str, Any],
    status_value: str,
    now: datetime,
) -> None:
    await uploads_collection.update_one(
        {"_id": upload_document["_id"]},
        {"$set": {"status": status_value, "updated_at": now}},
    )


async def validate_owned_upload_for_detection(
    uploads_collection: Any,
    quality_reports_collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    upload_document = await get_owned_upload_document(uploads_collection, upload_id, user_id)
    if upload_document is None:
        raise DetectionUploadNotFoundError

    now = datetime.now(timezone.utc)
    if as_utc(upload_document["expires_at"]) <= now:
        delete_storage_reference(settings.upload_path, upload_document.get("storage_reference", ""))
        await set_detection_upload_status(
            uploads_collection,
            upload_document,
            "expired",
            now,
        )
        raise DetectionUploadUnavailableError

    if upload_document.get("consent_given") is not True:
        raise DetectionConsentRequiredError

    upload_status = upload_document.get("status")
    if upload_status == "face_detecting":
        raise DetectionAnalysisInProgressError
    if upload_status not in DETECTABLE_UPLOAD_STATUSES:
        raise DetectionUploadStatusError

    quality_report = await quality_reports_collection.find_one(
        {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    )
    if quality_report is None:
        raise DetectionQualityPrerequisiteError

    quality_status = quality_report.get("quality_status")
    quality_warning_accepted = bool(quality_report.get("warning_accepted", False))
    if quality_status == "failed" or (quality_status == "warning" and not quality_warning_accepted):
        raise DetectionQualityPrerequisiteError
    if quality_status not in {"passed", "warning"}:
        raise DetectionQualityPrerequisiteError

    image_path = get_private_upload_path(upload_document, settings)
    if not image_path.is_file():
        await set_detection_upload_status(
            uploads_collection,
            upload_document,
            "face_detection_failed",
            now,
        )
        raise DetectionUploadUnavailableError

    return upload_document, quality_report, image_path


async def upsert_face_detection_report(
    reports_collection: Any,
    *,
    upload_id: str,
    user_id: str,
    quality_report_id: str,
    evaluation: FaceDetectionEvaluation,
    crop: StoredFaceCrop | None,
    settings: Settings,
    now: datetime,
) -> dict[str, Any]:
    ownership_query = {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    existing = await reports_collection.find_one(ownership_query)
    expires_at = now + timedelta(minutes=settings.face_crop_expiry_minutes)
    document = build_face_detection_document(
        upload_id=upload_id,
        quality_report_id=quality_report_id,
        user_id=user_id,
        evaluation=evaluation,
        crop=crop,
        now=now,
        expires_at=expires_at,
        existing=existing,
    )

    try:
        if existing is None:
            result = await reports_collection.insert_one(document)
            document["_id"] = result.inserted_id
        else:
            await reports_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": document},
            )
            document["_id"] = existing["_id"]
    except Exception:
        if crop is not None:
            delete_face_crop_reference(settings, crop.storage_reference)
        raise

    old_crop_reference = existing.get("crop_reference") if existing else None
    if old_crop_reference and old_crop_reference != document.get("crop_reference"):
        delete_face_crop_reference(settings, old_crop_reference)

    return document


def upload_status_for_detection_result(status_value: str) -> str:
    return {
        "passed": "face_detected",
        "warning": "face_detection_warning",
        "failed": "face_detection_failed",
    }[status_value]


async def analyze_owned_face_detection(
    uploads_collection: Any,
    quality_reports_collection: Any,
    reports_collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
    detector: FaceDetector | None = None,
) -> FaceDetectionResponse:
    upload_document, quality_report, image_path = await validate_owned_upload_for_detection(
        uploads_collection,
        quality_reports_collection,
        upload_id,
        user_id,
        settings,
    )
    original_status = upload_document["status"]
    now = datetime.now(timezone.utc)
    await set_detection_upload_status(
        uploads_collection,
        upload_document,
        "face_detecting",
        now,
    )

    try:
        selected_detector = detector or get_face_detector(settings)
        evaluation, crop = await run_in_threadpool(
            run_face_detection_pipeline,
            image_path=image_path,
            user_id=user_id,
            upload_id=upload_id,
            settings=settings,
            detector=selected_detector,
        )
        completed_at = datetime.now(timezone.utc)
        report_document = await upsert_face_detection_report(
            reports_collection,
            upload_id=upload_id,
            user_id=user_id,
            quality_report_id=quality_report["quality_report_id"],
            evaluation=evaluation,
            crop=crop,
            settings=settings,
            now=completed_at,
        )
        await set_detection_upload_status(
            uploads_collection,
            upload_document,
            upload_status_for_detection_result(evaluation.detection_status),
            completed_at,
        )
        return face_detection_document_to_response(report_document)
    except DetectionImageDecodeError:
        await set_detection_upload_status(
            uploads_collection,
            upload_document,
            "face_detection_failed",
            datetime.now(timezone.utc),
        )
        raise
    except DetectionProcessingError:
        await set_detection_upload_status(
            uploads_collection,
            upload_document,
            original_status,
            datetime.now(timezone.utc),
        )
        raise
    except Exception as exc:
        await set_detection_upload_status(
            uploads_collection,
            upload_document,
            original_status,
            datetime.now(timezone.utc),
        )
        raise DetectionProcessingError from exc


async def get_owned_face_detection_report(
    uploads_collection: Any,
    reports_collection: Any,
    upload_id: str,
    user_id: str,
) -> FaceDetectionResponse:
    upload_document = await get_owned_upload_document(uploads_collection, upload_id, user_id)
    if upload_document is None:
        raise DetectionUploadNotFoundError

    document = await reports_collection.find_one(
        {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    )
    if document is None:
        raise DetectionReportNotFoundError
    return face_detection_document_to_response(document)


async def accept_owned_face_detection_warning(
    uploads_collection: Any,
    reports_collection: Any,
    upload_id: str,
    user_id: str,
) -> FaceWarningAcceptanceResponse:
    upload_document = await get_owned_upload_document(uploads_collection, upload_id, user_id)
    if upload_document is None:
        raise DetectionUploadNotFoundError

    ownership_query = {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    document = await reports_collection.find_one(ownership_query)
    if document is None:
        raise DetectionReportNotFoundError
    if document.get("detection_status") != "warning":
        raise DetectionWarningNotAllowedError

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
    await set_detection_upload_status(
        uploads_collection,
        upload_document,
        "preprocessing_pending",
        now,
    )
    return FaceWarningAcceptanceResponse(
        face_report_id=document["face_report_id"],
        upload_id=upload_id,
        detection_status="warning",
        warning_accepted=True,
        warning_accepted_at=now,
        can_continue=True,
        next_route="/image-preprocessing",
    )
