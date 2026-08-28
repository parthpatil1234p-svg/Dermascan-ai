from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_image_preprocessing_reports_collection,
    get_image_uploads_collection,
    get_skin_profiles_collection,
    get_skin_type_reports_collection,
    require_complete_skin_profile,
)
from app.core.config import Settings, get_settings
from app.ml.model_registry import (
    SkinTypeModelRegistry,
    get_skin_type_model_registry,
)
from app.schemas.skin_type import SkinTypeModelStatusResponse, SkinTypeResponse
from app.schemas.user import UserPublic
from app.services.skin_type_inference_service import (
    SkinTypeAnalysisInProgressError,
    SkinTypeImageUnavailableError,
    SkinTypeInferenceError,
    SkinTypeModelUnavailableError,
    SkinTypePrerequisiteError,
    SkinTypeReportNotFoundError,
    SkinTypeUploadNotFoundError,
    analyze_owned_skin_type,
    get_owned_skin_type_report,
)

router = APIRouter(tags=["skin type"])


def raise_skin_type_http_error(error: Exception) -> None:
    if isinstance(error, SkinTypeUploadNotFoundError):
        raise HTTPException(status_code=404, detail="Image upload not found.") from error
    if isinstance(error, SkinTypePrerequisiteError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Image preprocessing must be completed before skin-type analysis.",
        ) from error
    if isinstance(error, SkinTypeImageUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The prepared image is no longer available.",
        ) from error
    if isinstance(error, SkinTypeAnalysisInProgressError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Skin-type analysis is already running.",
        ) from error
    if isinstance(error, SkinTypeModelUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The skin-type model is not available. Install a validated model artifact before running analysis.",
        ) from error
    if isinstance(error, SkinTypeReportNotFoundError):
        raise HTTPException(status_code=404, detail="Skin-type report not found.") from error
    if isinstance(error, SkinTypeInferenceError):
        raise HTTPException(
            status_code=500,
            detail="We could not complete the skin-type estimate. Please try again.",
        ) from error
    raise error


@router.post("/skin-type/{upload_id}/analyze", response_model=SkinTypeResponse)
async def analyze_skin_type(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    preprocessing_reports_collection=Depends(get_image_preprocessing_reports_collection),
    skin_profiles_collection=Depends(get_skin_profiles_collection),
    reports_collection=Depends(get_skin_type_reports_collection),
    registry: SkinTypeModelRegistry = Depends(get_skin_type_model_registry),
    settings: Settings = Depends(get_settings),
) -> SkinTypeResponse:
    try:
        return await analyze_owned_skin_type(
            uploads_collection,
            preprocessing_reports_collection,
            skin_profiles_collection,
            reports_collection,
            registry,
            upload_id,
            current_user.id,
            settings,
        )
    except Exception as error:
        raise_skin_type_http_error(error)


@router.get("/skin-type/{upload_id}", response_model=SkinTypeResponse)
async def read_skin_type_report(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    reports_collection=Depends(get_skin_type_reports_collection),
) -> SkinTypeResponse:
    try:
        return await get_owned_skin_type_report(
            uploads_collection, reports_collection, upload_id, current_user.id
        )
    except Exception as error:
        raise_skin_type_http_error(error)


@router.get("/models/skin-type/status", response_model=SkinTypeModelStatusResponse)
async def skin_type_model_status(
    registry: SkinTypeModelRegistry = Depends(get_skin_type_model_registry),
) -> SkinTypeModelStatusResponse:
    return SkinTypeModelStatusResponse(**registry.status())
