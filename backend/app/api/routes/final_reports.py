from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    get_current_user,
    get_face_detection_reports_collection,
    get_final_reports_collection,
    get_image_preprocessing_reports_collection,
    get_image_quality_reports_collection,
    get_image_uploads_collection,
    get_product_eligibility_reports_collection,
    get_product_recommendation_reports_collection,
    get_products_collection,
    get_skin_concern_reports_collection,
    get_skin_profiles_collection,
    get_skin_type_reports_collection,
    get_skincare_routine_reports_collection,
)
from app.models.final_report import (
    final_report_document_to_response,
    final_report_generation_response,
)
from app.schemas.final_report import (
    FinalReportArchiveResponse,
    FinalReportGenerationResponse,
    FinalReportListResponse,
    FinalReportResponse,
    FinalReportStatus,
)
from app.schemas.user import UserPublic
from app.services.final_report_service import (
    FinalReportArchivedError,
    FinalReportGenerationConflictError,
    FinalReportGenerationError,
    FinalReportNotFoundError,
    archive_owned_final_report,
    generate_owned_final_report,
    get_latest_report,
    get_owned_final_report,
    list_owned_reports,
)
from app.services.report_validation_service import ReportRelationshipError

router = APIRouter(prefix="/final-reports", tags=["final reports"])


def _collections(**values):
    return values


def raise_report_error(error: Exception) -> None:
    if isinstance(error, FinalReportNotFoundError):
        raise HTTPException(status_code=404, detail="Final report not found.") from error
    if isinstance(error, FinalReportArchivedError):
        raise HTTPException(
            status_code=410, detail="This final report has been archived."
        ) from error
    if isinstance(error, (FinalReportGenerationConflictError, ReportRelationshipError)):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, FinalReportGenerationError):
        raise HTTPException(
            status_code=500, detail="We could not safely generate the final report."
        ) from error
    raise error


def source_collections(
    profiles,
    uploads,
    quality,
    faces,
    preprocessing,
    skin_types,
    concerns,
    eligibility,
    recommendations,
    routines,
    products,
    final_reports,
) -> dict:
    return _collections(
        skin_profile=profiles,
        image_upload=uploads,
        image_quality=quality,
        face_detection=faces,
        image_preprocessing=preprocessing,
        skin_type=skin_types,
        skin_concern=concerns,
        product_eligibility=eligibility,
        product_recommendation=recommendations,
        skincare_routine=routines,
        products=products,
        final_reports=final_reports,
    )


@router.post(
    "/{upload_id}/generate",
    response_model=FinalReportGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_final_report(
    upload_id: str,
    current_user: UserPublic = Depends(get_current_user),
    profiles=Depends(get_skin_profiles_collection),
    uploads=Depends(get_image_uploads_collection),
    quality=Depends(get_image_quality_reports_collection),
    faces=Depends(get_face_detection_reports_collection),
    preprocessing=Depends(get_image_preprocessing_reports_collection),
    skin_types=Depends(get_skin_type_reports_collection),
    concerns=Depends(get_skin_concern_reports_collection),
    eligibility=Depends(get_product_eligibility_reports_collection),
    recommendations=Depends(get_product_recommendation_reports_collection),
    routines=Depends(get_skincare_routine_reports_collection),
    products=Depends(get_products_collection),
    final_reports=Depends(get_final_reports_collection),
) -> FinalReportGenerationResponse:
    try:
        document = await generate_owned_final_report(
            upload_id=upload_id,
            user_id=current_user.id,
            collections=source_collections(
                profiles,
                uploads,
                quality,
                faces,
                preprocessing,
                skin_types,
                concerns,
                eligibility,
                recommendations,
                routines,
                products,
                final_reports,
            ),
            force_new_version=False,
        )
        return final_report_generation_response(document)
    except Exception as error:
        raise_report_error(error)


@router.post(
    "/{upload_id}/regenerate",
    response_model=FinalReportGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def regenerate_final_report(
    upload_id: str,
    current_user: UserPublic = Depends(get_current_user),
    profiles=Depends(get_skin_profiles_collection),
    uploads=Depends(get_image_uploads_collection),
    quality=Depends(get_image_quality_reports_collection),
    faces=Depends(get_face_detection_reports_collection),
    preprocessing=Depends(get_image_preprocessing_reports_collection),
    skin_types=Depends(get_skin_type_reports_collection),
    concerns=Depends(get_skin_concern_reports_collection),
    eligibility=Depends(get_product_eligibility_reports_collection),
    recommendations=Depends(get_product_recommendation_reports_collection),
    routines=Depends(get_skincare_routine_reports_collection),
    products=Depends(get_products_collection),
    final_reports=Depends(get_final_reports_collection),
) -> FinalReportGenerationResponse:
    try:
        document = await generate_owned_final_report(
            upload_id=upload_id,
            user_id=current_user.id,
            collections=source_collections(
                profiles,
                uploads,
                quality,
                faces,
                preprocessing,
                skin_types,
                concerns,
                eligibility,
                recommendations,
                routines,
                products,
                final_reports,
            ),
            force_new_version=True,
        )
        return final_report_generation_response(document)
    except Exception as error:
        raise_report_error(error)


@router.get("/by-upload/{upload_id}/latest", response_model=FinalReportResponse)
async def read_latest_report(
    upload_id: str,
    current_user: UserPublic = Depends(get_current_user),
    reports=Depends(get_final_reports_collection),
    uploads=Depends(get_image_uploads_collection),
) -> FinalReportResponse:
    try:
        return final_report_document_to_response(
            await get_latest_report(reports, uploads, upload_id, current_user.id)
        )
    except Exception as error:
        raise_report_error(error)


@router.get("", response_model=FinalReportListResponse)
async def list_final_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    report_status: FinalReportStatus | None = Query(None, alias="status"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort: Literal["newest", "oldest"] = "newest",
    current_user: UserPublic = Depends(get_current_user),
    reports=Depends(get_final_reports_collection),
) -> FinalReportListResponse:
    return await list_owned_reports(
        reports,
        current_user.id,
        page=page,
        page_size=page_size,
        report_status=report_status,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
    )


@router.get("/{final_report_id}", response_model=FinalReportResponse)
async def read_final_report(
    final_report_id: str,
    current_user: UserPublic = Depends(get_current_user),
    reports=Depends(get_final_reports_collection),
) -> FinalReportResponse:
    try:
        return final_report_document_to_response(
            await get_owned_final_report(reports, final_report_id, current_user.id)
        )
    except Exception as error:
        raise_report_error(error)


@router.delete("/{final_report_id}", response_model=FinalReportArchiveResponse)
async def archive_final_report(
    final_report_id: str,
    current_user: UserPublic = Depends(get_current_user),
    reports=Depends(get_final_reports_collection),
) -> FinalReportArchiveResponse:
    try:
        return await archive_owned_final_report(reports, final_report_id, current_user.id)
    except Exception as error:
        raise_report_error(error)
