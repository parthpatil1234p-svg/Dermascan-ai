from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

import numpy as np
from bson import ObjectId
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.ml.model_loader import ModelUnavailableError, SkinTypeModelBundle
from app.ml.model_registry import SkinTypeModelRegistry
from app.models.skin_type import build_skin_type_document, skin_type_document_to_response
from app.schemas.skin_type import SkinTypeResponse
from app.services.model_input_service import build_inference_tensor
from app.services.skin_type_fusion_service import (
    QuestionnaireEvidence,
    fuse_skin_type_prediction,
)
from app.services.upload_service import get_owned_upload_document
from app.utils.file_utils import secure_child_path
from app.utils.image_colour import decode_image_to_rgb

INFERENCE_UPLOAD_STATUSES = {
    "skin_type_analysis_pending",
    "preprocessing_completed",
    "preprocessing_warning",
    "skin_type_estimated",
    "skin_type_uncertain",
    "skin_type_analysis_failed",
    "skin_concern_analysis_pending",
}
_prediction_lock = RLock()


class SkinTypeUploadNotFoundError(Exception):
    pass


class SkinTypePrerequisiteError(Exception):
    pass


class SkinTypeImageUnavailableError(Exception):
    pass


class SkinTypeAnalysisInProgressError(Exception):
    pass


class SkinTypeModelUnavailableError(Exception):
    pass


class SkinTypeInferenceError(Exception):
    pass


class SkinTypeReportNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class SkinTypePrediction:
    top_class: str
    top_confidence: float
    second_class: str
    second_confidence: float
    margin: float
    confidence_level: str
    probabilities: dict[str, float]
    is_uncertain: bool


def parse_model_probabilities(
    raw_output: Any,
    class_map: dict[int, str],
    settings: Settings,
) -> SkinTypePrediction:
    values = np.asarray(raw_output, dtype=np.float64)
    if values.shape != (1, len(class_map)) or not np.isfinite(values).all():
        raise SkinTypeInferenceError
    probabilities = values[0]
    if (probabilities < 0).any() or float(probabilities.sum()) <= 0:
        raise SkinTypeInferenceError
    probabilities = probabilities / probabilities.sum()
    order = np.argsort(probabilities)[::-1]
    top_index, second_index = int(order[0]), int(order[1])
    top_confidence = float(probabilities[top_index])
    second_confidence = float(probabilities[second_index])
    margin = top_confidence - second_confidence
    confidence_level = (
        "high"
        if top_confidence >= settings.skin_type_high_confidence
        else "moderate" if top_confidence >= settings.skin_type_min_confidence else "low"
    )
    return SkinTypePrediction(
        top_class=class_map[top_index],
        top_confidence=top_confidence,
        second_class=class_map[second_index],
        second_confidence=second_confidence,
        margin=margin,
        confidence_level=confidence_level,
        probabilities={
            class_map[index]: float(probabilities[index]) for index in range(len(class_map))
        },
        is_uncertain=(
            top_confidence < settings.skin_type_min_confidence
            or margin < settings.skin_type_min_margin
        ),
    )


def run_skin_type_inference(
    image_path: Path,
    bundle: SkinTypeModelBundle,
    settings: Settings,
) -> SkinTypePrediction:
    try:
        decoded = decode_image_to_rgb(image_path)
        tensor, _ = build_inference_tensor(decoded.image, settings)
        with _prediction_lock:
            output = bundle.model.predict(tensor, verbose=0)
        return parse_model_probabilities(output, bundle.class_map, settings)
    except SkinTypeInferenceError:
        raise
    except Exception as exc:
        raise SkinTypeInferenceError from exc


def get_private_preprocessed_path(preprocessing_report: dict[str, Any], settings: Settings) -> Path:
    reference = preprocessing_report.get("processed_image_reference")
    if not isinstance(reference, str) or not reference:
        raise SkinTypeImageUnavailableError
    try:
        path = secure_child_path(settings.preprocessed_image_path, *Path(reference).parts)
    except ValueError as exc:
        raise SkinTypeImageUnavailableError from exc
    if not path.is_file():
        raise SkinTypeImageUnavailableError
    return path


async def set_skin_type_upload_status(
    uploads_collection: Any,
    upload_document: dict[str, Any],
    value: str,
) -> None:
    await uploads_collection.update_one(
        {"_id": upload_document["_id"]},
        {"$set": {"status": value, "updated_at": datetime.now(timezone.utc)}},
    )


async def validate_skin_type_prerequisites(
    uploads_collection: Any,
    preprocessing_reports_collection: Any,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    upload = await get_owned_upload_document(uploads_collection, upload_id, user_id)
    if upload is None:
        raise SkinTypeUploadNotFoundError
    if upload.get("status") == "skin_type_analyzing":
        raise SkinTypeAnalysisInProgressError
    if upload.get("status") not in INFERENCE_UPLOAD_STATUSES:
        raise SkinTypePrerequisiteError
    report = await preprocessing_reports_collection.find_one(
        {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    )
    if report is None or report.get("preprocessing_status") not in {
        "completed",
        "warning",
    }:
        raise SkinTypePrerequisiteError
    return upload, report, get_private_preprocessed_path(report, settings)


async def upsert_skin_type_report(
    reports_collection: Any,
    *,
    upload_id: str,
    user_id: str,
    preprocessing_report: dict[str, Any],
    bundle: SkinTypeModelBundle,
    prediction: SkinTypePrediction,
    evidence: QuestionnaireEvidence,
    fused: Any,
    now: datetime,
) -> dict[str, Any]:
    query = {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    existing = await reports_collection.find_one(query)
    document = build_skin_type_document(
        upload_id=upload_id,
        user_id=user_id,
        preprocessing_report_id=preprocessing_report["preprocessing_report_id"],
        bundle=bundle,
        prediction=prediction,
        evidence=evidence,
        fused=fused,
        now=now,
        existing=existing,
    )
    if existing is None:
        inserted = await reports_collection.insert_one(document)
        document["_id"] = inserted.inserted_id
    else:
        await reports_collection.update_one({"_id": existing["_id"]}, {"$set": document})
        document["_id"] = existing["_id"]
    return document


async def analyze_owned_skin_type(
    uploads_collection: Any,
    preprocessing_reports_collection: Any,
    skin_profiles_collection: Any,
    reports_collection: Any,
    registry: SkinTypeModelRegistry,
    upload_id: str,
    user_id: str,
    settings: Settings,
) -> SkinTypeResponse:
    upload, preprocessing_report, image_path = await validate_skin_type_prerequisites(
        uploads_collection,
        preprocessing_reports_collection,
        upload_id,
        user_id,
        settings,
    )
    profile = await skin_profiles_collection.find_one({"user_id": ObjectId(user_id)})
    if profile is None or not profile.get("is_complete", False):
        raise SkinTypePrerequisiteError
    try:
        bundle = registry.require_bundle()
    except ModelUnavailableError as exc:
        raise SkinTypeModelUnavailableError from exc

    original_status = upload["status"]
    await set_skin_type_upload_status(uploads_collection, upload, "skin_type_analyzing")
    try:
        prediction = await run_in_threadpool(run_skin_type_inference, image_path, bundle, settings)
        evidence = QuestionnaireEvidence(
            oiliness_level=profile["oiliness_level"],
            dryness_level=profile["dryness_level"],
            self_reported_sensitivity=profile.get("is_sensitive"),
        )
        fused = fuse_skin_type_prediction(
            predicted_class=prediction.top_class,
            image_result_is_uncertain=prediction.is_uncertain,
            evidence=evidence,
        )
        now = datetime.now(timezone.utc)
        report = await upsert_skin_type_report(
            reports_collection,
            upload_id=upload_id,
            user_id=user_id,
            preprocessing_report=preprocessing_report,
            bundle=bundle,
            prediction=prediction,
            evidence=evidence,
            fused=fused,
            now=now,
        )
        final_status = (
            "skin_type_estimated" if fused.result_status == "estimated" else "skin_type_uncertain"
        )
        await set_skin_type_upload_status(uploads_collection, upload, final_status)
        return skin_type_document_to_response(report)
    except SkinTypeInferenceError:
        await set_skin_type_upload_status(uploads_collection, upload, "skin_type_analysis_failed")
        raise
    except Exception as exc:
        await set_skin_type_upload_status(uploads_collection, upload, original_status)
        raise SkinTypeInferenceError from exc


async def get_owned_skin_type_report(
    uploads_collection: Any,
    reports_collection: Any,
    upload_id: str,
    user_id: str,
) -> SkinTypeResponse:
    if await get_owned_upload_document(uploads_collection, upload_id, user_id) is None:
        raise SkinTypeUploadNotFoundError
    report = await reports_collection.find_one(
        {"upload_id": upload_id, "user_id": ObjectId(user_id)}
    )
    if report is None:
        raise SkinTypeReportNotFoundError
    return skin_type_document_to_response(report)
