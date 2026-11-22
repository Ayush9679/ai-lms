"""
AI-LMS Auth Service — registration, login, token management, password reset.
"""

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_email_verification_token,
    decode_password_reset_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

logger = get_logger(__name__)


def _token_response(user: User) -> TokenResponse:
    from app.core.config import get_settings

    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, request: RegisterRequest) -> tuple[User, str]:
        """
        Register a new user.
        Returns (user, email_verification_token).
        Token should be sent via email or returned in debug mode.
        """
        if await self.user_repo.email_exists(request.email):
            raise ConflictError(f"An account with email '{request.email}' already exists")

        user = await self.user_repo.create_user(
            email=request.email,
            hashed_password=hash_password(request.password),
            full_name=request.full_name,
            role=request.role,
        )

        # Create email verification token
        verification_token = create_email_verification_token(user.id)
        await self.user_repo.create_email_verification(user.id, verification_token)

        logger.info("User registered", extra={"user_id": str(user.id)})
        return user, verification_token

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate and return JWT tokens."""
        user = await self.user_repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Your account has been deactivated. Contact support.")

        logger.info("User logged in", extra={"user_id": str(user.id)})
        return _token_response(user)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Issue new token pair from a valid refresh token."""
        try:
            payload = decode_refresh_token(refresh_token)
        except JWTError:
            raise UnauthorizedError("Invalid or expired refresh token")

        user = await self.user_repo.get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or deactivated")

        return _token_response(user)

    async def verify_email(self, token: str) -> User:
        """Mark user as email-verified."""
        try:
            decode_email_verification_token(token)
        except JWTError:
            raise ValidationError("Invalid or expired verification token")

        verification = await self.user_repo.get_email_verification(token)
        if not verification:
            raise ValidationError("Verification token already used or not found")

        user = await self.user_repo.get_by_id(verification.user_id)
        if not user:
            raise NotFoundError("User")

        await self.user_repo.mark_email_verified(verification, user)
        logger.info("Email verified", extra={"user_id": str(user.id)})
        return user

    async def forgot_password(self, email: str) -> str | None:
        """
        Initiate password reset.
        Returns the reset token (send via email in production).
        Returns None silently if email not found (security best practice).
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None  # Don't reveal whether email exists

        token = create_password_reset_token(user.id)
        await self.user_repo.create_password_reset(user.id, token)
        logger.info("Password reset initiated", extra={"user_id": str(user.id)})
        return token

    async def reset_password(self, token: str, new_password: str) -> None:
        """Complete a password reset."""
        try:
            decode_password_reset_token(token)
        except JWTError:
            raise ValidationError("Invalid or expired reset token")

        reset = await self.user_repo.get_password_reset(token)
        if not reset:
            raise ValidationError("Reset token already used or not found")

        user = await self.user_repo.get_by_id(reset.user_id)
        if not user:
            raise NotFoundError("User")

        await self.user_repo.mark_password_reset_used(reset, user, hash_password(new_password))
        logger.info("Password reset completed", extra={"user_id": str(user.id)})

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        """Change password for authenticated user."""
        if not verify_password(current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect")
        await self.user_repo.update(user, hashed_password=hash_password(new_password))
