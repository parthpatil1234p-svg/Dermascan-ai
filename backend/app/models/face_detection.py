from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId

from app.schemas.face_detection import (
    FaceCropResponse,
    FaceDetectionIssue,
    FaceDetectionResponse,
)


def build_face_detection_document(
    *,
    upload_id: str,
    quality_report_id: str,
    user_id: str,
    evaluation: Any,
    crop: Any | None,
    now: datetime,
    expires_at: datetime,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "face_report_id": existing["face_report_id"] if existing else str(uuid4()),
        "upload_id": upload_id,
        "quality_report_id": quality_report_id,
        "user_id": ObjectId(user_id),
        "face_count": evaluation.face_count,
        "detection_confidence": evaluation.detection_confidence,
        "bounding_box_normalized": (
            evaluation.bounding_box_normalized.to_dict()
            if evaluation.bounding_box_normalized
            else None
        ),
        "bounding_box_pixels": (
            evaluation.bounding_box_pixels.to_dict() if evaluation.bounding_box_pixels else None
        ),
        "face_area_ratio": (
            round(evaluation.face_area_ratio, 6) if evaluation.face_area_ratio is not None else None
        ),
        "face_center_offset": (
            round(evaluation.face_center_offset, 6)
            if evaluation.face_center_offset is not None
            else None
        ),
        "face_position_status": evaluation.face_position_status,
        "face_size_status": evaluation.face_size_status,
        "crop_reference": crop.storage_reference if crop else None,
        "crop_format": crop.crop_format if crop else None,
        "crop_width": crop.crop_width if crop else None,
        "crop_height": crop.crop_height if crop else None,
        "crop_file_size": crop.crop_file_size if crop else None,
        "crop_created_at": now if crop else None,
        "crop_expires_at": expires_at if crop else None,
        "detection_status": evaluation.detection_status,
        "issues": [issue.model_dump() for issue in evaluation.issues],
        "recommendations": evaluation.recommendations,
        "warning_accepted": False,
        "warning_accepted_at": None,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
        "expires_at": expires_at,
    }


def face_detection_document_to_response(
    document: dict[str, Any],
) -> FaceDetectionResponse:
    detection_status = document["detection_status"]
    warning_accepted = bool(document.get("warning_accepted", False))
    can_continue = detection_status == "passed" or (
        detection_status == "warning" and warning_accepted
    )
    if can_continue:
        next_route = "/image-preprocessing"
    elif detection_status == "failed":
        next_route = "/face-scan"
    else:
        next_route = None

    confidence = document.get("detection_confidence")
    confidence_percent = int(round(float(confidence) * 100)) if confidence is not None else None

    return FaceDetectionResponse(
        face_report_id=document["face_report_id"],
        upload_id=document["upload_id"],
        detection_status=detection_status,
        face_count=document["face_count"],
        detection_confidence=confidence_percent,
        face_position=document.get("face_position_status", "not_applicable"),
        face_size=document.get("face_size_status", "not_applicable"),
        crop=FaceCropResponse(
            prepared=bool(document.get("crop_reference")),
            width=document.get("crop_width"),
            height=document.get("crop_height"),
        ),
        issues=[FaceDetectionIssue(**issue) for issue in document.get("issues", [])],
        recommendations=document.get("recommendations", []),
        warning_accepted=warning_accepted,
        warning_accepted_at=document.get("warning_accepted_at"),
        can_continue=can_continue,
        next_route=next_route,
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
