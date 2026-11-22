"""
AI-LMS Auth Router — registration, login, token refresh, email verification, password reset.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserPublic
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Creates a student or teacher account. Returns the created user profile. An email verification token is generated (check logs in dev).",
)
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserPublic:
    svc = AuthService(db)
    user, _verification_token = await svc.register(request)
    return UserPublic.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get JWT tokens",
    description="Authenticates with email/password. Returns access + refresh token pair.",
)
async def login(
    request: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    svc = AuthService(db)
    return await svc.login(request)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access + refresh token pair.",
)
async def refresh_tokens(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    svc = AuthService(db)
    return await svc.refresh_tokens(request.refresh_token)


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address",
    description="Verify email using the token sent after registration.",
)
async def verify_email(
    request: VerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = AuthService(db)
    user = await svc.verify_email(request.token)
    return MessageResponse(message=f"Email verified successfully for {user.email}")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Sends a password reset token (via email in prod, logged in dev). Always returns success to avoid email enumeration.",
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = AuthService(db)
    await svc.forgot_password(request.email)
    return MessageResponse(message="If that email exists, a reset link has been sent.")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with token",
    description="Set a new password using the reset token from the forgot-password step.",
)
async def reset_password(
    request: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = AuthService(db)
    await svc.reset_password(request.token, request.new_password)
    return MessageResponse(
        message="Password reset successfully. Please login with your new password."
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password (authenticated)",
    description="Change your own password. Requires current password verification.",
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = AuthService(db)
    await svc.change_password(current_user, request.current_password, request.new_password)
    return MessageResponse(message="Password changed successfully.")


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user profile",
    description="Returns the authenticated user's full profile.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPublic:
    return UserPublic.model_validate(current_user)
