from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_users_collection
from app.core.security import create_access_token
from app.schemas.auth import AuthResponse, LoginRequest, LogoutResponse, RegisterRequest
from app.services.user_service import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
    authenticate_user,
    create_user,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    users_collection=Depends(get_users_collection),
) -> AuthResponse:
    try:
        user = await create_user(users_collection, payload)
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc

    token = create_access_token(subject=user.id)
    return AuthResponse(access_token=token, user=user)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    users_collection=Depends(get_users_collection),
) -> AuthResponse:
    try:
        user = await authenticate_user(
            users_collection,
            payload.email,
            payload.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        ) from exc

    token = create_access_token(subject=user.id)
    return AuthResponse(access_token=token, user=user)


@router.post("/logout", response_model=LogoutResponse)
async def logout() -> LogoutResponse:
    return LogoutResponse(
        message=(
            "Logout acknowledged. Remove the access token from the frontend; "
            "stateless JWT access tokens are not server-invalidated by this endpoint."
        )
    )
