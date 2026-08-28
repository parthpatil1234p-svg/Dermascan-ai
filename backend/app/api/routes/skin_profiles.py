from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_skin_profiles_collection
from app.schemas.skin_profile import (
    SkinProfileCompletionResponse,
    SkinProfileCreate,
    SkinProfileDeleteResponse,
    SkinProfileResponse,
    SkinProfileUpdate,
)
from app.schemas.user import UserPublic
from app.services.skin_profile_service import (
    DuplicateSkinProfileError,
    SkinProfileNotFoundError,
    create_skin_profile,
    delete_skin_profile,
    get_skin_profile,
    get_skin_profile_document,
    update_skin_profile,
)

router = APIRouter(prefix="/skin-profile", tags=["skin profile"])


@router.get("/status", response_model=SkinProfileCompletionResponse)
async def read_skin_profile_status(
    current_user: UserPublic = Depends(get_current_user),
    collection=Depends(get_skin_profiles_collection),
) -> SkinProfileCompletionResponse:
    profile = await get_skin_profile_document(collection, current_user.id)
    is_complete = bool(profile and profile.get("is_complete"))
    return SkinProfileCompletionResponse(
        exists=profile is not None,
        is_complete=is_complete,
        next_route="/face-scan" if is_complete else "/skin-profile",
    )


@router.post("", response_model=SkinProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_current_user_skin_profile(
    payload: SkinProfileCreate,
    current_user: UserPublic = Depends(get_current_user),
    collection=Depends(get_skin_profiles_collection),
) -> SkinProfileResponse:
    try:
        return await create_skin_profile(collection, current_user.id, payload)
    except DuplicateSkinProfileError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A skin profile already exists for this user.",
        ) from exc


@router.get("", response_model=SkinProfileResponse)
async def read_current_user_skin_profile(
    current_user: UserPublic = Depends(get_current_user),
    collection=Depends(get_skin_profiles_collection),
) -> SkinProfileResponse:
    try:
        return await get_skin_profile(collection, current_user.id)
    except SkinProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skin profile not found.",
        ) from exc


@router.put("", response_model=SkinProfileResponse)
async def update_current_user_skin_profile(
    payload: SkinProfileUpdate,
    current_user: UserPublic = Depends(get_current_user),
    collection=Depends(get_skin_profiles_collection),
) -> SkinProfileResponse:
    try:
        return await update_skin_profile(collection, current_user.id, payload)
    except SkinProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skin profile not found.",
        ) from exc


@router.delete("", response_model=SkinProfileDeleteResponse)
async def delete_current_user_skin_profile(
    current_user: UserPublic = Depends(get_current_user),
    collection=Depends(get_skin_profiles_collection),
) -> SkinProfileDeleteResponse:
    try:
        await delete_skin_profile(collection, current_user.id)
    except SkinProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skin profile not found.",
        ) from exc
    return SkinProfileDeleteResponse(message="Skin profile deleted successfully.")
