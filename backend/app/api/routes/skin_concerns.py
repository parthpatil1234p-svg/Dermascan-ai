from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_image_preprocessing_reports_collection,
    get_image_uploads_collection,
    get_skin_concern_reports_collection,
    get_skin_profiles_collection,
    get_skin_type_reports_collection,
    require_complete_skin_profile,
)
from app.core.config import Settings, get_settings
from app.ml.skin_concern_registry import (
    SkinConcernModelRegistry,
    get_skin_concern_model_registry,
)
from app.schemas.skin_concern import SkinConcernModelStatusResponse, SkinConcernResponse
from app.schemas.user import UserPublic
from app.services.skin_concern_inference_service import (
    ConcernAnalysisInProgressError,
    ConcernImageUnavailableError,
    ConcernInferenceError,
    ConcernModelUnavailableForAnalysisError,
    ConcernPrerequisiteError,
    ConcernReportNotFoundError,
    ConcernUploadNotFoundError,
    analyze_owned_skin_concerns,
    get_owned_concern_report,
)

router = APIRouter(tags=["visible skin concerns"])


def raise_skin_concern_http_error(error: Exception) -> None:
    if isinstance(error, ConcernUploadNotFoundError):
        raise HTTPException(status_code=404, detail="Image upload not found.") from error
    if isinstance(error, ConcernPrerequisiteError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Complete image preprocessing and skin-type estimation before "
                "visible skin-concern analysis."
            ),
        ) from error
    if isinstance(error, ConcernImageUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The prepared image is no longer available.",
        ) from error
    if isinstance(error, ConcernAnalysisInProgressError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Visible skin-concern analysis is already running.",
        ) from error
    if isinstance(error, ConcernModelUnavailableForAnalysisError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The visible skin-concern model is not available. Install validated "
                "model, metadata, label-map, and calibrated-threshold artifacts."
            ),
        ) from error
    if isinstance(error, ConcernReportNotFoundError):
        raise HTTPException(status_code=404, detail="Skin-concern report not found.") from error
    if isinstance(error, ConcernInferenceError):
        raise HTTPException(
            status_code=500,
            detail=(
                "We could not complete the visible skin-concern analysis. "
                "No medical diagnosis was performed."
            ),
        ) from error
    raise error


@router.post("/skin-concerns/{upload_id}/analyze", response_model=SkinConcernResponse)
async def analyze_skin_concerns(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    preprocessing_reports_collection=Depends(get_image_preprocessing_reports_collection),
    skin_type_reports_collection=Depends(get_skin_type_reports_collection),
    skin_profiles_collection=Depends(get_skin_profiles_collection),
    reports_collection=Depends(get_skin_concern_reports_collection),
    registry: SkinConcernModelRegistry = Depends(get_skin_concern_model_registry),
    settings: Settings = Depends(get_settings),
) -> SkinConcernResponse:
    try:
        return await analyze_owned_skin_concerns(
            uploads_collection,
            preprocessing_reports_collection,
            skin_type_reports_collection,
            skin_profiles_collection,
            reports_collection,
            registry,
            upload_id,
            current_user.id,
            settings,
        )
    except Exception as error:
        raise_skin_concern_http_error(error)


@router.get("/skin-concerns/{upload_id}", response_model=SkinConcernResponse)
async def read_skin_concern_report(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    reports_collection=Depends(get_skin_concern_reports_collection),
) -> SkinConcernResponse:
    try:
        return await get_owned_concern_report(
            uploads_collection, reports_collection, upload_id, current_user.id
        )
    except Exception as error:
        raise_skin_concern_http_error(error)


@router.get("/models/skin-concerns/status", response_model=SkinConcernModelStatusResponse)
async def skin_concern_model_status(
    registry: SkinConcernModelRegistry = Depends(get_skin_concern_model_registry),
) -> SkinConcernModelStatusResponse:
    return SkinConcernModelStatusResponse(**registry.status())
