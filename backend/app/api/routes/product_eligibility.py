from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import (
    get_current_user,
    get_image_uploads_collection,
    get_ingredients_collection,
    get_optional_user_product_avoidance_collection,
    get_product_eligibility_reports_collection,
    get_products_collection,
    get_skin_concern_reports_collection,
    get_skin_profiles_collection,
    get_skin_type_reports_collection,
)
from app.core.catalogue import PRODUCT_CATEGORIES
from app.core.config import Settings, get_settings
from app.schemas.product_eligibility import (
    EligibilityStatus,
    ProductEligibilityDetailResponse,
    ProductEligibilityReportResponse,
)
from app.schemas.user import UserPublic
from app.services.product_eligibility_service import (
    EligibilityCatalogueEmptyError,
    EligibilityEvaluationError,
    EligibilityPrerequisiteError,
    EligibilityProductNotFoundError,
    EligibilityReportNotFoundError,
    EligibilityUploadNotFoundError,
    evaluate_owned_catalogue,
    get_owned_product_detail,
    get_owned_report,
    report_response,
)

router = APIRouter(prefix="/product-eligibility", tags=["product eligibility"])


def raise_eligibility_error(error: Exception) -> None:
    if isinstance(error, EligibilityUploadNotFoundError):
        raise HTTPException(status_code=404, detail="Image upload not found.") from error
    if isinstance(error, EligibilityReportNotFoundError):
        raise HTTPException(
            status_code=404, detail="Product eligibility report not found."
        ) from error
    if isinstance(error, EligibilityProductNotFoundError):
        raise HTTPException(
            status_code=404, detail="Product eligibility result not found."
        ) from error
    if isinstance(error, EligibilityCatalogueEmptyError):
        raise HTTPException(
            status_code=409, detail="The active product catalogue is empty."
        ) from error
    if isinstance(error, EligibilityPrerequisiteError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, EligibilityEvaluationError):
        raise HTTPException(
            status_code=500,
            detail="We could not safely evaluate the product catalogue. No recommendation ranking was created.",
        ) from error
    raise error


@router.post("/{upload_id}/evaluate", response_model=ProductEligibilityReportResponse)
async def evaluate_product_eligibility(
    upload_id: str,
    current_user: UserPublic = Depends(get_current_user),
    uploads=Depends(get_image_uploads_collection),
    profiles=Depends(get_skin_profiles_collection),
    skin_types=Depends(get_skin_type_reports_collection),
    concerns=Depends(get_skin_concern_reports_collection),
    products=Depends(get_products_collection),
    ingredients=Depends(get_ingredients_collection),
    reports=Depends(get_product_eligibility_reports_collection),
    user_avoidances=Depends(get_optional_user_product_avoidance_collection),
    settings: Settings = Depends(get_settings),
) -> ProductEligibilityReportResponse:
    try:
        document = await evaluate_owned_catalogue(
            upload_id=upload_id,
            user_id=current_user.id,
            uploads=uploads,
            profiles=profiles,
            skin_types=skin_types,
            concerns=concerns,
            products=products,
            ingredients=ingredients,
            reports=reports,
            settings=settings,
            user_avoidances=user_avoidances,
        )
        return report_response(document)
    except Exception as error:
        raise_eligibility_error(error)


@router.get("/{upload_id}", response_model=ProductEligibilityReportResponse)
async def read_product_eligibility_report(
    upload_id: str,
    eligibility_status: EligibilityStatus | None = Query(None, alias="status"),
    category: Literal[*PRODUCT_CATEGORIES] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserPublic = Depends(get_current_user),
    reports=Depends(get_product_eligibility_reports_collection),
) -> ProductEligibilityReportResponse:
    try:
        document = await get_owned_report(reports, upload_id, current_user.id)
        return report_response(
            document,
            status=eligibility_status,
            category=category,
            page=page,
            page_size=page_size,
        )
    except Exception as error:
        raise_eligibility_error(error)


@router.get(
    "/{upload_id}/products/{product_id}",
    response_model=ProductEligibilityDetailResponse,
)
async def read_product_eligibility_detail(
    upload_id: str,
    product_id: str,
    current_user: UserPublic = Depends(get_current_user),
    reports=Depends(get_product_eligibility_reports_collection),
    products=Depends(get_products_collection),
    settings: Settings = Depends(get_settings),
) -> ProductEligibilityDetailResponse:
    try:
        return await get_owned_product_detail(
            reports, products, upload_id, product_id, current_user.id, settings
        )
    except Exception as error:
        raise_eligibility_error(error)
