from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_image_quality_reports_collection,
    get_image_uploads_collection,
    require_complete_skin_profile,
)
from app.core.config import Settings, get_settings
from app.schemas.image_quality import (
    ImageQualityResponse,
    WarningAcceptanceResponse,
)
from app.schemas.user import UserPublic
from app.services.image_quality_service import (
    QualityAnalysisInProgressError,
    QualityConsentRequiredError,
    QualityImageDecodeError,
    QualityProcessingError,
    QualityReportNotFoundError,
    QualityUploadNotFoundError,
    QualityUploadStatusError,
    QualityUploadUnavailableError,
    QualityWarningNotAllowedError,
    accept_owned_quality_warning,
    analyze_owned_image_quality,
    get_owned_quality_report,
)

router = APIRouter(prefix="/image-quality", tags=["image quality"])


def raise_quality_http_error(error: Exception) -> None:
    if isinstance(error, QualityUploadNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image upload not found.",
        ) from error
    if isinstance(error, QualityUploadUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The uploaded image is no longer available.",
        ) from error
    if isinstance(error, QualityConsentRequiredError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image-processing consent is required.",
        ) from error
    if isinstance(error, QualityAnalysisInProgressError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Image-quality analysis is already running.",
        ) from error
    if isinstance(error, QualityUploadStatusError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This upload is not available for image-quality analysis.",
        ) from error
    if isinstance(error, QualityReportNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image-quality report not found.",
        ) from error
    if isinstance(error, QualityWarningNotAllowedError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only warning reports can be accepted.",
        ) from error
    if isinstance(error, QualityImageDecodeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The uploaded image could not be decoded for quality analysis.",
        ) from error
    if isinstance(error, QualityProcessingError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=("We could not complete the image-quality check. Please try again."),
        ) from error
    raise error


@router.post(
    "/{upload_id}/analyze",
    response_model=ImageQualityResponse,
)
async def analyze_image_quality(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    reports_collection=Depends(get_image_quality_reports_collection),
    settings: Settings = Depends(get_settings),
) -> ImageQualityResponse:
    try:
        return await analyze_owned_image_quality(
            uploads_collection,
            reports_collection,
            upload_id,
            current_user.id,
            settings,
        )
    except Exception as error:
        raise_quality_http_error(error)


@router.get("/{upload_id}", response_model=ImageQualityResponse)
async def read_image_quality_report(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    reports_collection=Depends(get_image_quality_reports_collection),
) -> ImageQualityResponse:
    try:
        return await get_owned_quality_report(
            uploads_collection,
            reports_collection,
            upload_id,
            current_user.id,
        )
    except Exception as error:
        raise_quality_http_error(error)


@router.post(
    "/{upload_id}/accept-warning",
    response_model=WarningAcceptanceResponse,
)
async def accept_image_quality_warning(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    reports_collection=Depends(get_image_quality_reports_collection),
) -> WarningAcceptanceResponse:
    try:
        return await accept_owned_quality_warning(
            uploads_collection,
            reports_collection,
            upload_id,
            current_user.id,
        )
    except Exception as error:
        raise_quality_http_error(error)
