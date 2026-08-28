from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_current_user,
    get_image_uploads_collection,
    get_product_recommendation_reports_collection,
    get_skincare_routine_reports_collection,
)
from app.models.skincare_routine import routine_document_to_response
from app.schemas.skincare_routine import SkincareRoutineResponse
from app.schemas.user import UserPublic
from app.services.skincare_routine_service import (
    RoutineGenerationError,
    RoutinePrerequisiteError,
    RoutineReportNotFoundError,
    RoutineUploadNotFoundError,
    generate_owned_routine,
    get_owned_routine,
)

router = APIRouter(prefix="/skincare-routines", tags=["skincare routines"])


def raise_routine_error(error: Exception) -> None:
    if isinstance(error, (RoutineUploadNotFoundError, RoutineReportNotFoundError)):
        raise HTTPException(status_code=404, detail="Skincare routine report not found.") from error
    if isinstance(error, RoutinePrerequisiteError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, RoutineGenerationError):
        raise HTTPException(
            status_code=500, detail="We could not safely generate the skincare routine."
        ) from error
    raise error


@router.post(
    "/{upload_id}/generate",
    response_model=SkincareRoutineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_routine(
    upload_id: str,
    current_user: UserPublic = Depends(get_current_user),
    uploads=Depends(get_image_uploads_collection),
    recommendations=Depends(get_product_recommendation_reports_collection),
    routines=Depends(get_skincare_routine_reports_collection),
) -> SkincareRoutineResponse:
    try:
        document = await generate_owned_routine(
            upload_id=upload_id,
            user_id=current_user.id,
            uploads=uploads,
            recommendation_reports=recommendations,
            routine_reports=routines,
        )
        return routine_document_to_response(document)
    except Exception as error:
        raise_routine_error(error)


@router.get("/{upload_id}", response_model=SkincareRoutineResponse)
async def read_routine(
    upload_id: str,
    current_user: UserPublic = Depends(get_current_user),
    routines=Depends(get_skincare_routine_reports_collection),
) -> SkincareRoutineResponse:
    try:
        return routine_document_to_response(
            await get_owned_routine(routines, upload_id, current_user.id)
        )
    except Exception as error:
        raise_routine_error(error)
