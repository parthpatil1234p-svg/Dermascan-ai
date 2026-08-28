from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

import numpy as np
from bson import ObjectId
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.skin_concern_labels import CONCERN_LABELS
from app.ml.skin_concern_model_loader import (
    ConcernModelUnavailableError,
    SkinConcernModelBundle,
)
from app.ml.skin_concern_registry import SkinConcernModelRegistry
from app.models.skin_concern import (
    build_skin_concern_document,
    skin_concern_document_to_response,
)
from app.schemas.skin_concern import SkinConcernResponse
from app.services.model_input_service import build_inference_tensor
from app.services.skin_concern_fusion_service import (
    ConcernQuestionnaireEvidence,
    compare_questionnaire,
)
from app.services.skin_concern_interpretation_service import interpret_concern
from app.services.skin_concern_region_service import (
    region_names_for_global_prediction,
    validate_region_geometry,
)
from app.services.upload_service import get_owned_upload_document
from app.utils.file_utils import secure_child_path
from app.utils.image_colour import decode_image_to_rgb

ALLOWED_CONCERN_UPLOAD_STATUSES = {
    "skin_type_estimated",
    "skin_type_uncertain",
    "skin_concern_analysis_pending",
    "skin_concern_analysis_completed",
    "skin_concern_analysis_uncertain",
    "skin_concern_analysis_failed",
    "product_discovery_pending",
}
_inference_lock = RLock()


class ConcernUploadNotFoundError(Exception):
    pass


class ConcernPrerequisiteError(Exception):
    pass


class ConcernImageUnavailableError(Exception):
    pass


class ConcernAnalysisInProgressError(Exception):
    pass


class ConcernModelUnavailableForAnalysisError(Exception):
    pass


class ConcernInferenceError(Exception):
    pass


class ConcernReportNotFoundError(Exception):
    pass


def parse_concern_scores(raw_output: Any, label_map: dict[int, str]) -> dict[str, float]:
    values = np.asarray(raw_output, dtype=np.float64)
    if values.shape != (1, len(CONCERN_LABELS)) or not np.isfinite(values).all():
        raise ConcernInferenceError
    if (values < 0).any() or (values > 1).any():
        raise ConcernInferenceError
    return {label_map[index]: float(values[0, index]) for index in range(len(label_map))}


def run_concern_inference(
    image_path: Path,
    bundle: SkinConcernModelBundle,
    settings: Settings,
) -> tuple[dict[str, float], np.ndarray]:
    try:
        decoded = decode_image_to_rgb(image_path)
        expected_shape = (
            settings.model_input_height,
            settings.model_input_width,
            settings.model_input_channels,
        )
        if decoded.image.shape != expected_shape:
            raise ConcernInferenceError
        tensor, _ = build_inference_tensor(decoded.image, settings)
        with _inference_lock:
            output = bundle.model.predict(tensor, verbose=0)
        return parse_concern_scores(output, bundle.label_map), decoded.image
    except ConcernInferenceError:
        raise
    except Exception as exc:
        raise ConcernInferenceError from exc


def resolve_preprocessed_path(report: dict[str, Any], settings: Settings) -> Path:
    reference = report.get("processed_image_reference")
    if not isinstance(reference, str) or not reference:
        raise ConcernImageUnavailableError
    try:
        path = secure_child_path(settings.preprocessed_image_path, *Path(reference).parts)
    except ValueError as exc:
        raise ConcernImageUnavailableError from exc
    if not path.is_file():
        raise ConcernImageUnavailableError
    return path


async def set_concern_upload_status(collection: Any, upload: dict[str, Any], value: str) -> None:
    await collection.update_one(
        {"_id": upload["_id"]},
        {"$set": {"status": value, "updated_at": datetime.now(timezone.utc)}},
    )


async def validate_concern_prerequisites(
    uploads_collection: Any,
    preprocessing_collection: Any,
    skin_type_collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Path]:
    upload = await get_owned_upload_document(uploads_collection, upload_id, user_id)
    if upload is None:
        raise ConcernUploadNotFoundError
    if upload.get("status") == "skin_concern_analyzing":
        raise ConcernAnalysisInProgressError
    if upload.get("status") not in ALLOWED_CONCERN_UPLOAD_STATUSES:
        raise ConcernPrerequisiteError
    now = datetime.now(timezone.utc)
    upload_expiry = upload.get("expires_at")
    if upload_expiry is not None:
        if upload_expiry.tzinfo is None:
            upload_expiry = upload_expiry.replace(tzinfo=timezone.utc)
        if upload_expiry <= now:
            raise ConcernImageUnavailableError
    query = {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    preprocessing = await preprocessing_collection.find_one(query)
    if preprocessing is None or preprocessing.get("preprocessing_status") not in {
        "completed",
        "warning",
    }:
        raise ConcernPrerequisiteError
    preprocessing_expiry = preprocessing.get("expires_at")
    if preprocessing_expiry is not None:
        if preprocessing_expiry.tzinfo is None:
            preprocessing_expiry = preprocessing_expiry.replace(tzinfo=timezone.utc)
        if preprocessing_expiry <= now:
            raise ConcernImageUnavailableError
    skin_type = await skin_type_collection.find_one(query)
    if skin_type is None or skin_type.get("result_status") not in {
        "estimated",
        "uncertain",
    }:
        raise ConcernPrerequisiteError
    return upload, preprocessing, skin_type, resolve_preprocessed_path(preprocessing, settings)


async def analyze_owned_skin_concerns(
    uploads_collection: Any,
    preprocessing_collection: Any,
    skin_type_collection: Any,
    profiles_collection: Any,
    reports_collection: Any,
    registry: SkinConcernModelRegistry,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> SkinConcernResponse:
    upload, preprocessing, skin_type, image_path = await validate_concern_prerequisites(
        uploads_collection,
        preprocessing_collection,
        skin_type_collection,
        upload_id,
        user_id,
        settings,
    )
    profile = await profiles_collection.find_one({"user_id": ObjectId(user_id)})
    if profile is None or not profile.get("is_complete", False):
        raise ConcernPrerequisiteError
    try:
        bundle = registry.require_bundle()
    except ConcernModelUnavailableError as exc:
        raise ConcernModelUnavailableForAnalysisError from exc

    original_status = upload["status"]
    await set_concern_upload_status(uploads_collection, upload, "skin_concern_analyzing")
    try:
        scores, image = await run_in_threadpool(run_concern_inference, image_path, bundle, settings)
        evidence = ConcernQuestionnaireEvidence(
            oiliness_level=profile["oiliness_level"],
            dryness_level=profile["dryness_level"],
            self_reported_sensitivity=profile.get("is_sensitive"),
        )
        region_context = validate_region_geometry(image, None)
        regions = region_names_for_global_prediction(region_context)
        results = [
            interpret_concern(
                concern_code=label,
                score=scores[label],
                threshold=bundle.thresholds[label],
                comparison=compare_questionnaire(label, evidence),
                regions=regions,
                settings=settings,
                thresholds_calibrated=bundle.thresholds_calibrated,
            )
            for label in CONCERN_LABELS
        ]
        has_uncertainty = any(result.status in {"possible", "uncertain"} for result in results)
        overall = "completed_with_uncertainty" if has_uncertainty else "completed"
        now = datetime.now(timezone.utc)
        query = {"upload_id": upload_id, "user_id": ObjectId(user_id)}
        existing = await reports_collection.find_one(query)
        document = build_skin_concern_document(
            upload_id=upload_id,
            user_id=user_id,
            preprocessing_report_id=preprocessing["preprocessing_report_id"],
            skin_type_report_id=skin_type["skin_type_report_id"],
            bundle=bundle,
            scores=scores,
            results=results,
            region_context=region_context,
            overall_status=overall,
            now=now,
            existing=existing,
        )
        if existing is None:
            inserted = await reports_collection.insert_one(document)
            document["_id"] = inserted.inserted_id
        else:
            await reports_collection.update_one({"_id": existing["_id"]}, {"$set": document})
            document["_id"] = existing["_id"]
        final_status = (
            "skin_concern_analysis_uncertain"
            if has_uncertainty
            else "skin_concern_analysis_completed"
        )
        await set_concern_upload_status(uploads_collection, upload, final_status)
        return skin_concern_document_to_response(document)
    except ConcernInferenceError:
        await set_concern_upload_status(uploads_collection, upload, "skin_concern_analysis_failed")
        raise
    except Exception as exc:
        await set_concern_upload_status(uploads_collection, upload, original_status)
        raise ConcernInferenceError from exc


async def get_owned_concern_report(
    uploads_collection: Any,
    reports_collection: Any,
    upload_id: str,
    user_id: str,
) -> SkinConcernResponse:
    if await get_owned_upload_document(uploads_collection, upload_id, user_id) is None:
        raise ConcernUploadNotFoundError
    report = await reports_collection.find_one(
        {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    )
    if report is None:
        raise ConcernReportNotFoundError
    return skin_concern_document_to_response(report)
