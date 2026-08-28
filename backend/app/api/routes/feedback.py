from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    get_catalogue_review_signals_collection,
    get_current_user,
    get_feedback_collection,
    get_feedback_signals_collection,
    get_final_reports_collection,
    get_product_recommendation_reports_collection,
    get_skincare_routine_reports_collection,
    get_user_product_avoidance_collection,
)
from app.core.config import Settings, get_settings
from app.schemas.feedback import (
    FeedbackCategory,
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackOptionsResponse,
    FeedbackResponse,
    FeedbackStatus,
    FeedbackUpdate,
    FeedbackWithdrawalResponse,
    ProductAvoidanceListResponse,
)
from app.schemas.user import UserPublic
from app.services.feedback_privacy_service import FeedbackTextError
from app.services.feedback_service import (
    FeedbackConflictError,
    FeedbackNotFoundError,
    FeedbackRateLimitError,
    FeedbackStateError,
    create_feedback,
    feedback_options,
    get_feedback_detail,
    get_feedback_history,
    get_owned_avoidance_responses,
    remove_owned_avoidance,
    update_feedback,
    withdraw_feedback,
)
from app.services.feedback_validation_service import FeedbackRelationshipError

router = APIRouter(prefix="/feedback", tags=["feedback"])


def feedback_collections(
    feedback,
    final_reports,
    recommendation_reports,
    routine_reports,
    avoidances,
    improvement_signals,
    catalogue_signals,
) -> dict:
    return {
        "feedback": feedback,
        "final_reports": final_reports,
        "recommendation_reports": recommendation_reports,
        "routine_reports": routine_reports,
        "avoidances": avoidances,
        "improvement_signals": improvement_signals,
        "catalogue_signals": catalogue_signals,
    }


def raise_feedback_error(error: Exception) -> None:
    if isinstance(error, FeedbackNotFoundError):
        raise HTTPException(status_code=404, detail="Feedback not found.") from error
    if isinstance(error, FeedbackRelationshipError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, (FeedbackConflictError, FeedbackStateError)):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, FeedbackRateLimitError):
        raise HTTPException(status_code=429, detail=str(error)) from error
    if isinstance(error, FeedbackTextError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    raise error


def common_collections(
    feedback=Depends(get_feedback_collection),
    final_reports=Depends(get_final_reports_collection),
    recommendation_reports=Depends(get_product_recommendation_reports_collection),
    routine_reports=Depends(get_skincare_routine_reports_collection),
    avoidances=Depends(get_user_product_avoidance_collection),
    improvement_signals=Depends(get_feedback_signals_collection),
    catalogue_signals=Depends(get_catalogue_review_signals_collection),
) -> dict:
    return feedback_collections(
        feedback,
        final_reports,
        recommendation_reports,
        routine_reports,
        avoidances,
        improvement_signals,
        catalogue_signals,
    )


@router.get("/options", response_model=FeedbackOptionsResponse)
async def read_feedback_options(
    _: UserPublic = Depends(get_current_user),
) -> FeedbackOptionsResponse:
    return feedback_options()


@router.get("/product-avoidance", response_model=ProductAvoidanceListResponse)
async def read_product_avoidances(
    current_user: UserPublic = Depends(get_current_user),
    collection=Depends(get_user_product_avoidance_collection),
) -> ProductAvoidanceListResponse:
    return await get_owned_avoidance_responses(collection, current_user.id)


@router.delete("/product-avoidance/{product_id}")
async def delete_product_avoidance(
    product_id: str,
    current_user: UserPublic = Depends(get_current_user),
    collection=Depends(get_user_product_avoidance_collection),
) -> dict[str, str]:
    try:
        await remove_owned_avoidance(collection, current_user.id, product_id)
        return {"message": "The product was removed from your private avoidance list."}
    except Exception as error:
        raise_feedback_error(error)


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate,
    current_user: UserPublic = Depends(get_current_user),
    collections: dict = Depends(common_collections),
    settings: Settings = Depends(get_settings),
) -> FeedbackResponse:
    try:
        return await create_feedback(
            payload=payload,
            user_id=current_user.id,
            collections=collections,
            settings=settings,
        )
    except Exception as error:
        raise_feedback_error(error)


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    category: FeedbackCategory | None = None,
    feedback_status: FeedbackStatus | None = Query(None, alias="status"),
    final_report_id: str | None = None,
    product_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: UserPublic = Depends(get_current_user),
    collection=Depends(get_feedback_collection),
) -> FeedbackListResponse:
    return await get_feedback_history(
        collection,
        current_user.id,
        page=page,
        page_size=page_size,
        category=category,
        feedback_status=feedback_status,
        final_report_id=final_report_id,
        product_id=product_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def read_feedback(
    feedback_id: str,
    current_user: UserPublic = Depends(get_current_user),
    collection=Depends(get_feedback_collection),
) -> FeedbackResponse:
    try:
        return await get_feedback_detail(collection, feedback_id, current_user.id)
    except Exception as error:
        raise_feedback_error(error)


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def edit_feedback(
    feedback_id: str,
    payload: FeedbackUpdate,
    current_user: UserPublic = Depends(get_current_user),
    collections: dict = Depends(common_collections),
    settings: Settings = Depends(get_settings),
) -> FeedbackResponse:
    try:
        return await update_feedback(
            feedback_id=feedback_id,
            payload=payload,
            user_id=current_user.id,
            collections=collections,
            settings=settings,
        )
    except Exception as error:
        raise_feedback_error(error)


@router.delete("/{feedback_id}", response_model=FeedbackWithdrawalResponse)
async def delete_feedback(
    feedback_id: str,
    current_user: UserPublic = Depends(get_current_user),
    collections: dict = Depends(common_collections),
) -> FeedbackWithdrawalResponse:
    try:
        return await withdraw_feedback(
            feedback_id=feedback_id, user_id=current_user.id, collections=collections
        )
    except Exception as error:
        raise_feedback_error(error)
