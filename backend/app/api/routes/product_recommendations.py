from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import (
    get_current_user,
    get_image_uploads_collection,
    get_ingredients_collection,
    get_product_eligibility_reports_collection,
    get_product_recommendation_reports_collection,
    get_products_collection,
    get_skin_concern_reports_collection,
    get_skin_profiles_collection,
)
from app.core.catalogue import PRODUCT_CATEGORIES
from app.core.config import Settings, get_settings
from app.schemas.product_recommendation import (
    ProductRecommendationDetailResponse,
    ProductRecommendationReportResponse,
)
from app.schemas.user import UserPublic
from app.services.recommendation_engine_service import (
    RecommendationGenerationError,
    RecommendationPrerequisiteError,
    RecommendationProductNotFoundError,
    RecommendationReportNotFoundError,
    RecommendationUploadNotFoundError,
    generate_owned_recommendations,
    get_owned_recommendation_detail,
    get_owned_recommendation_report,
    recommendation_report_response,
)

router = APIRouter(prefix="/product-recommendations", tags=["product recommendations"])


def raise_recommendation_error(error: Exception) -> None:
    if isinstance(error, RecommendationUploadNotFoundError):
        raise HTTPException(status_code=404, detail="Image upload not found.") from error
    if isinstance(error, RecommendationReportNotFoundError):
        raise HTTPException(
            status_code=404, detail="Product recommendation report not found."
        ) from error
    if isinstance(error, RecommendationProductNotFoundError):
        raise HTTPException(status_code=404, detail="Recommended product not found.") from error
    if isinstance(error, RecommendationPrerequisiteError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, RecommendationGenerationError):
        raise HTTPException(
            status_code=500,
            detail="We could not safely generate product recommendations. No safety exclusions were changed.",
        ) from error
    raise error


@router.post("/{upload_id}/generate", response_model=ProductRecommendationReportResponse)
async def generate_product_recommendations(
    upload_id: str,
    current_user: UserPublic = Depends(get_current_user),
    uploads=Depends(get_image_uploads_collection),
    eligibility_reports=Depends(get_product_eligibility_reports_collection),
    recommendation_reports=Depends(get_product_recommendation_reports_collection),
    products=Depends(get_products_collection),
    ingredients=Depends(get_ingredients_collection),
    profiles=Depends(get_skin_profiles_collection),
    concerns=Depends(get_skin_concern_reports_collection),
    settings: Settings = Depends(get_settings),
) -> ProductRecommendationReportResponse:
    try:
        document = await generate_owned_recommendations(
            upload_id=upload_id,
            user_id=current_user.id,
            uploads=uploads,
            eligibility_reports=eligibility_reports,
            recommendation_reports=recommendation_reports,
            products=products,
            ingredients=ingredients,
            profiles=profiles,
            concerns=concerns,
            settings=settings,
        )
        return recommendation_report_response(document, page_size=100)
    except Exception as error:
        raise_recommendation_error(error)


@router.get("/{upload_id}", response_model=ProductRecommendationReportResponse)
async def read_product_recommendation_report(
    upload_id: str,
    category: Literal[*PRODUCT_CATEGORIES] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    minimum_score: float = Query(0, ge=0, le=100),
    current_user: UserPublic = Depends(get_current_user),
    reports=Depends(get_product_recommendation_reports_collection),
) -> ProductRecommendationReportResponse:
    try:
        document = await get_owned_recommendation_report(reports, upload_id, current_user.id)
        return recommendation_report_response(
            document,
            category=category,
            minimum_score=minimum_score,
            page=page,
            page_size=page_size,
        )
    except Exception as error:
        raise_recommendation_error(error)


@router.get(
    "/{upload_id}/products/{product_id}",
    response_model=ProductRecommendationDetailResponse,
)
async def read_product_recommendation_detail(
    upload_id: str,
    product_id: str,
    current_user: UserPublic = Depends(get_current_user),
    reports=Depends(get_product_recommendation_reports_collection),
    products=Depends(get_products_collection),
    settings: Settings = Depends(get_settings),
) -> ProductRecommendationDetailResponse:
    try:
        return await get_owned_recommendation_detail(
            reports, products, upload_id, product_id, current_user.id, settings
        )
    except Exception as error:
        raise_recommendation_error(error)
