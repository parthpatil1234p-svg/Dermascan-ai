from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_face_detection_reports_collection,
    get_image_quality_reports_collection,
    get_image_uploads_collection,
    require_complete_skin_profile,
)
from app.core.config import Settings, get_settings
from app.schemas.face_detection import (
    FaceDetectionResponse,
    FaceWarningAcceptanceResponse,
)
from app.schemas.user import UserPublic
from app.services.detection_workflow_service import (
    DetectionAnalysisInProgressError,
    DetectionConsentRequiredError,
    DetectionImageDecodeError,
    DetectionProcessingError,
    DetectionQualityPrerequisiteError,
    DetectionReportNotFoundError,
    DetectionUploadNotFoundError,
    DetectionUploadStatusError,
    DetectionUploadUnavailableError,
    DetectionWarningNotAllowedError,
    accept_owned_face_detection_warning,
    analyze_owned_face_detection,
    get_owned_face_detection_report,
)

router = APIRouter(prefix="/face-detection", tags=["face detection"])


def raise_detection_http_error(error: Exception) -> None:
    if isinstance(error, DetectionUploadNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image upload not found.",
        ) from error
    if isinstance(error, DetectionUploadUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The uploaded image is no longer available.",
        ) from error
    if isinstance(error, DetectionConsentRequiredError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image-processing consent is required.",
        ) from error
    if isinstance(error, DetectionUploadStatusError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The image must pass quality validation before face detection.",
        ) from error
    if isinstance(error, DetectionQualityPrerequisiteError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The image must pass quality validation before face detection.",
        ) from error
    if isinstance(error, DetectionAnalysisInProgressError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Face detection is already running.",
        ) from error
    if isinstance(error, DetectionReportNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Face-detection report not found.",
        ) from error
    if isinstance(error, DetectionWarningNotAllowedError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only warning face-detection reports can be accepted.",
        ) from error
    if isinstance(error, DetectionImageDecodeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The uploaded image could not be decoded for face detection.",
        ) from error
    if isinstance(error, DetectionProcessingError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We could not complete face detection. Please try again.",
        ) from error
    raise error


@router.post("/{upload_id}/analyze", response_model=FaceDetectionResponse)
async def analyze_face_detection(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    quality_reports_collection=Depends(get_image_quality_reports_collection),
    reports_collection=Depends(get_face_detection_reports_collection),
    settings: Settings = Depends(get_settings),
) -> FaceDetectionResponse:
    try:
        return await analyze_owned_face_detection(
            uploads_collection,
            quality_reports_collection,
            reports_collection,
            upload_id,
            current_user.id,
            settings,
        )
    except Exception as error:
        raise_detection_http_error(error)


@router.get("/{upload_id}", response_model=FaceDetectionResponse)
async def read_face_detection_report(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    reports_collection=Depends(get_face_detection_reports_collection),
) -> FaceDetectionResponse:
    try:
        return await get_owned_face_detection_report(
            uploads_collection,
            reports_collection,
            upload_id,
            current_user.id,
        )
    except Exception as error:
        raise_detection_http_error(error)


@router.post(
    "/{upload_id}/accept-warning",
    response_model=FaceWarningAcceptanceResponse,
)
async def accept_face_detection_warning(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    uploads_collection=Depends(get_image_uploads_collection),
    reports_collection=Depends(get_face_detection_reports_collection),
) -> FaceWarningAcceptanceResponse:
    try:
        return await accept_owned_face_detection_warning(
            uploads_collection,
            reports_collection,
            upload_id,
            current_user.id,
        )
    except Exception as error:
        raise_detection_http_error(error)
