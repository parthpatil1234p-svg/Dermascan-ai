from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings
from app.core.security import TokenDecodeError, TokenExpiredError, decode_access_token
from app.models.user import user_document_to_public
from app.schemas.user import UserPublic
from app.services.skin_profile_service import get_skin_profile_document
from app.services.user_service import get_user_by_id

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


def get_database(request: Request) -> Any:
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is not available.",
        )
    return database


def get_users_collection(database: Any = Depends(get_database)) -> Any:
    return database["users"]


def get_skin_profiles_collection(database: Any = Depends(get_database)) -> Any:
    return database["skin_profiles"]


def get_image_uploads_collection(database: Any = Depends(get_database)) -> Any:
    return database["image_uploads"]


def get_image_quality_reports_collection(
    database: Any = Depends(get_database),
) -> Any:
    return database["image_quality_reports"]


def get_face_detection_reports_collection(
    database: Any = Depends(get_database),
) -> Any:
    return database["face_detection_reports"]


def get_image_preprocessing_reports_collection(
    database: Any = Depends(get_database),
) -> Any:
    return database["image_preprocessing_reports"]


def get_skin_type_reports_collection(
    database: Any = Depends(get_database),
) -> Any:
    return database["skin_type_reports"]


def get_skin_concern_reports_collection(
    database: Any = Depends(get_database),
) -> Any:
    return database["skin_concern_reports"]


def get_optional_skin_concern_reports_collection(request: Request) -> Any | None:
    database = getattr(request.app.state, "database", None)
    return None if database is None else database["skin_concern_reports"]


def get_products_collection(database: Any = Depends(get_database)) -> Any:
    return database["products"]


def get_ingredients_collection(database: Any = Depends(get_database)) -> Any:
    return database["ingredients"]


def get_brands_collection(database: Any = Depends(get_database)) -> Any:
    return database["brands"]


def get_product_import_jobs_collection(database: Any = Depends(get_database)) -> Any:
    return database["product_import_jobs"]


def get_product_eligibility_reports_collection(database: Any = Depends(get_database)) -> Any:
    return database["product_eligibility_reports"]


def get_product_recommendation_reports_collection(database: Any = Depends(get_database)) -> Any:
    return database["product_recommendation_reports"]


def get_skincare_routine_reports_collection(database: Any = Depends(get_database)) -> Any:
    return database["skincare_routine_reports"]


def get_final_reports_collection(database: Any = Depends(get_database)) -> Any:
    return database["final_skin_reports"]


def get_feedback_collection(database: Any = Depends(get_database)) -> Any:
    return database["user_feedback"]


def get_user_product_avoidance_collection(database: Any = Depends(get_database)) -> Any:
    return database["user_product_avoidance"]


def get_optional_user_product_avoidance_collection(request: Request) -> Any | None:
    database = getattr(request.app.state, "database", None)
    return None if database is None else database["user_product_avoidance"]


def get_feedback_signals_collection(database: Any = Depends(get_database)) -> Any:
    return database["recommendation_improvement_signals"]


def get_catalogue_review_signals_collection(database: Any = Depends(get_database)) -> Any:
    return database["catalogue_review_signals"]


def get_feedback_analytics_collection(database: Any = Depends(get_database)) -> Any:
    return database["feedback_analytics_snapshots"]


def get_feedback_moderation_audit_collection(database: Any = Depends(get_database)) -> Any:
    return database["feedback_moderation_audit"]


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    users_collection: Any = Depends(get_users_collection),
) -> UserPublic:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise TokenDecodeError("Token subject is missing.")
    except TokenExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except TokenDecodeError as exc:
        raise credentials_exception from exc

    user = await get_user_by_id(users_collection, subject)
    if user is None:
        raise credentials_exception

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    return user_document_to_public(user)


async def require_complete_skin_profile(
    current_user: UserPublic = Depends(get_current_user),
    skin_profiles_collection: Any = Depends(get_skin_profiles_collection),
) -> UserPublic:
    profile = await get_skin_profile_document(skin_profiles_collection, current_user.id)
    if profile is None or not profile.get("is_complete", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete your skin profile before uploading a facial image.",
        )
    return current_user


async def require_admin(
    current_user: UserPublic = Depends(get_current_user),
) -> UserPublic:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Catalogue administrator access is required.",
        )
    return current_user
