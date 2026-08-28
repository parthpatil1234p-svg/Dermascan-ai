from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import (
    get_face_detection_reports_collection,
    get_image_preprocessing_reports_collection,
    get_image_quality_reports_collection,
    get_image_uploads_collection,
    get_optional_skin_concern_reports_collection,
    get_skin_type_reports_collection,
    require_complete_skin_profile,
)
from app.core.config import Settings, get_settings
from app.schemas.image_upload import (
    ImageUploadDeleteResponse,
    ImageUploadResponse,
    ImageUploadStatusResponse,
)
from app.schemas.user import UserPublic
from app.services.file_validation_service import UploadValidationError
from app.services.upload_service import (
    ImageUploadNotFoundError,
    create_validated_upload,
    delete_owned_upload,
    get_owned_upload_status,
)

router = APIRouter(prefix="/uploads", tags=["image uploads"])


@router.post(
    "/face-image",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_face_image(
    file: UploadFile = File(...),
    consent_given: bool | None = Form(default=None),
    current_user: UserPublic = Depends(require_complete_skin_profile),
    collection=Depends(get_image_uploads_collection),
    settings: Settings = Depends(get_settings),
) -> ImageUploadResponse:
    if consent_given is not True:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent is required before the image can be processed.",
        )

    try:
        return await create_validated_upload(collection, file, current_user.id, settings)
    except UploadValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/{upload_id}", response_model=ImageUploadStatusResponse)
async def read_upload_status(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    collection=Depends(get_image_uploads_collection),
    settings: Settings = Depends(get_settings),
) -> ImageUploadStatusResponse:
    try:
        return await get_owned_upload_status(collection, upload_id, current_user.id, settings)
    except ImageUploadNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image upload not found.",
        ) from exc


@router.delete("/{upload_id}", response_model=ImageUploadDeleteResponse)
async def delete_upload(
    upload_id: str,
    current_user: UserPublic = Depends(require_complete_skin_profile),
    collection=Depends(get_image_uploads_collection),
    quality_reports_collection=Depends(get_image_quality_reports_collection),
    face_reports_collection=Depends(get_face_detection_reports_collection),
    preprocessing_reports_collection=Depends(get_image_preprocessing_reports_collection),
    skin_type_reports_collection=Depends(get_skin_type_reports_collection),
    skin_concern_reports_collection=Depends(get_optional_skin_concern_reports_collection),
    settings: Settings = Depends(get_settings),
) -> ImageUploadDeleteResponse:
    try:
        await delete_owned_upload(
            collection,
            upload_id,
            current_user.id,
            settings,
            quality_reports_collection,
            face_reports_collection,
            preprocessing_reports_collection,
            skin_type_reports_collection,
            skin_concern_reports_collection,
        )
    except ImageUploadNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image upload not found.",
        ) from exc
    return ImageUploadDeleteResponse(message="Temporary image deleted successfully.")
