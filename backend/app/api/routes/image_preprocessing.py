from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_face_detection_reports_collection,
    get_image_preprocessing_reports_collection,
    get_image_quality_reports_collection,
    get_image_uploads_collection,
    require_complete_skin_profile,
)
from app.core.config import Settings, get_settings
from app.schemas.image_preprocessing import ImagePreprocessingResponse
from app.schemas.user import UserPublic
from app.services.image_preprocessing_service import (
    PreprocessingConsentRequiredError,
    PreprocessingCropUnavailableError,
    PreprocessingDecodeError,
    PreprocessingFacePrerequisiteError,
    PreprocessingInProgressError,
    PreprocessingProcessingError,
    PreprocessingQualityPrerequisiteError,
    PreprocessingReportNotFoundError,
    PreprocessingUploadNotFoundError,
    PreprocessingUploadStatusError,
    PreprocessingUploadUnavailableError,
    get_owned_preprocessing_report,
    process_owned_face_crop,
)

router = APIRouter(prefix="/image-preprocessing", tags=["image preprocessing"])


def raise_preprocessing_http_error(error: Exception) -> None:
    if isinstance(error, PreprocessingUploadNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image upload not found.",
        ) from error
    if isinstance(error, PreprocessingUploadUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The uploaded image is no longer available.",
        ) from error
    if isinstance(error, PreprocessingConsentRequiredError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image-processing consent is required.",
        ) from error
    if isinstance(error, PreprocessingInProgressError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Image preprocessing is already running.",
        ) from error
    if isinstance(error, PreprocessingUploadStatusError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Face detection must be completed before image preprocessing.",
        ) from error
    if isinstance(error, PreprocessingQualityPrerequisiteError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Image quality must be approved before preprocessing.",
        ) from error
    if isinstance(error, PreprocessingFacePrerequisiteError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Face detection must be completed before image preprocessing.",
        ) from error
    if isinstance(error, PreprocessingCropUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The prepared facial crop is no longer available.",
        ) from error
    if isinstance(error, PreprocessingDecodeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The prepared facial crop could not be decoded.",
        ) from error
    if isinstance(error, PreprocessingReportNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image-preprocessing report not found.",
        ) from error
    if isinstance(error, PreprocessingProcessingError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We could not prepare the image. Please try again.",
        ) from error
    raise error


@router.post("/{upload_id}/process", response_model=ImagePreprocessingResponse)
async def process_image(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    quality_reports_collection=Depends(get_image_quality_reports_collection),
    face_reports_collection=Depends(get_face_detection_reports_collection),
    reports_collection=Depends(get_image_preprocessing_reports_collection),
    settings: Settings = Depends(get_settings),
) -> ImagePreprocessingResponse:
    try:
        return await process_owned_face_crop(
            uploads_collection,
            quality_reports_collection,
            face_reports_collection,
            reports_collection,
            upload_id,
            current_user.id,
            settings,
        )
    except Exception as error:
        raise_preprocessing_http_error(error)


@router.get("/{upload_id}", response_model=ImagePreprocessingResponse)
async def read_preprocessing_report(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    reports_collection=Depends(get_image_preprocessing_reports_collection),
    settings: Settings = Depends(get_settings),
) -> ImagePreprocessingResponse:
    try:
        return await get_owned_preprocessing_report(
            uploads_collection,
            reports_collection,
            upload_id,
            current_user.id,
            settings,
        )
    except Exception as error:
        raise_preprocessing_http_error(error)
