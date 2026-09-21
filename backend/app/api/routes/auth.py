from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_users_collection
from app.core.security import create_access_token
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.services.user_service import (
    DuplicateEmailError,
    ExpiredResetOtpError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidResetOtpError,
    UserNotFoundError,
    authenticate_user,
    create_password_reset_otp,
    create_user,
    reset_user_password,
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


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    users_collection=Depends(get_users_collection),
) -> ForgotPasswordResponse:
    try:
        otp, email_sent = await create_password_reset_otp(users_collection, payload.email)
    except UserNotFoundError:
        return ForgotPasswordResponse(
            message="If an account with this email exists, a password reset code has been sent.",
            email=payload.email,
        )
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        ) from exc

    dev_otp = None if email_sent else otp
    message = (
        "A 6-digit verification code has been sent to your email address."
        if email_sent
        else "Verification code generated. (Demo Mode: Code is provided for immediate testing)"
    )

    return ForgotPasswordResponse(
        message=message,
        email=payload.email,
        dev_otp=dev_otp,
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    users_collection=Depends(get_users_collection),
) -> ResetPasswordResponse:
    try:
        await reset_user_password(
            users_collection,
            payload.email,
            payload.otp,
            payload.new_password,
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address.",
        ) from exc
    except ExpiredResetOtpError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verification code has expired. Please request a new one.",
        ) from exc
    except InvalidResetOtpError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code.",
        ) from exc

    return ResetPasswordResponse(
        message="Password has been successfully reset. You can now login with your new password."
    )

