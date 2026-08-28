from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId

from app.core.model_input_config import get_model_input_contract
from app.schemas.image_preprocessing import (
    ImagePreprocessingResponse,
    ModelInputMetadata,
    PreprocessingIssue,
    PreprocessingTransformations,
)


def build_image_preprocessing_document(
    *,
    upload_id: str,
    face_report_id: str,
    quality_report_id: str,
    user_id: str,
    result: Any,
    stored_image: Any,
    settings: Any,
    now: datetime,
    expires_at: datetime,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "preprocessing_report_id": (
            existing["preprocessing_report_id"] if existing else str(uuid4())
        ),
        "upload_id": upload_id,
        "face_report_id": face_report_id,
        "quality_report_id": quality_report_id,
        "user_id": ObjectId(user_id),
        "source_crop_width": result.source_width,
        "source_crop_height": result.source_height,
        "source_colour_space": result.source_colour_space,
        "output_width": result.output_width,
        "output_height": result.output_height,
        "output_channels": result.output_channels,
        "output_colour_space": "RGB",
        "resize_mode": settings.preprocess_resize_mode,
        "padding_applied": result.padding.applied,
        "padding_values": result.padding.to_dict(),
        "upscaling_applied": result.upscaling_applied,
        "resize_scale": round(result.resize_scale, 6),
        "denoise_applied": result.denoise_applied,
        "illumination_adjustment_applied": result.clahe_applied,
        "white_balance_applied": result.white_balance_applied,
        "sharpening_applied": result.sharpening_applied,
        "alpha_composited": result.alpha_composited,
        "normalization_mode": settings.preprocess_normalization_mode,
        "processed_image_reference": stored_image.storage_reference,
        "processed_image_format": stored_image.image_format,
        "processed_file_size": stored_image.file_size,
        "transformation_manifest": result.manifest,
        "preprocessing_status": result.status,
        "issues": [issue.model_dump() for issue in result.issues],
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
        "expires_at": expires_at,
    }


def image_preprocessing_document_to_response(
    document: dict[str, Any], settings: Any
) -> ImagePreprocessingResponse:
    contract = get_model_input_contract(settings)
    status = document["preprocessing_status"]
    can_continue = status in {"completed", "warning"}
    return ImagePreprocessingResponse(
        preprocessing_report_id=document["preprocessing_report_id"],
        upload_id=document["upload_id"],
        preprocessing_status=status,
        model_input=ModelInputMetadata(**contract.to_dict()),
        transformations=PreprocessingTransformations(
            resize_mode=document["resize_mode"],
            aspect_ratio_preserved=True,
            padding_applied=bool(document["padding_applied"]),
            padding_values=document["padding_values"],
            upscaling_applied=bool(document.get("upscaling_applied", False)),
            denoise_applied=bool(document["denoise_applied"]),
            illumination_adjustment_applied=bool(document["illumination_adjustment_applied"]),
            white_balance_applied=bool(document["white_balance_applied"]),
            sharpening_applied=bool(document["sharpening_applied"]),
            alpha_composited=bool(document.get("alpha_composited", False)),
        ),
        transformation_manifest=document["transformation_manifest"],
        issues=[PreprocessingIssue(**issue) for issue in document.get("issues", [])],
        can_continue=can_continue,
        next_route="/skin-type-analysis" if can_continue else None,
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
