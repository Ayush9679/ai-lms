"""
AI-LMS Security — JWT tokens, password hashing, token verification.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# Password Utilities
# =============================================================================


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# JWT Token Utilities
# =============================================================================


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Internal factory for creating signed JWT tokens."""
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: str | UUID, role: str) -> str:
    """Create a short-lived JWT access token."""
    return _create_token(
        subject=str(user_id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"role": role},
    )


def create_refresh_token(user_id: str | UUID) -> str:
    """Create a long-lived JWT refresh token."""
    return _create_token(
        subject=str(user_id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def create_email_verification_token(user_id: str | UUID) -> str:
    """Create a 24-hour email verification token."""
    return _create_token(
        subject=str(user_id),
        token_type="email_verify",
        expires_delta=timedelta(hours=24),
    )


def create_password_reset_token(user_id: str | UUID) -> str:
    """Create a 1-hour password reset token."""
    return _create_token(
        subject=str(user_id),
        token_type="password_reset",
        expires_delta=timedelta(hours=1),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode an access token and verify its type."""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Decode a refresh token and verify its type."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type")
    return payload


def decode_email_verification_token(token: str) -> dict[str, Any]:
    """Decode an email verification token and verify its type."""
    payload = decode_token(token)
    if payload.get("type") != "email_verify":
        raise JWTError("Invalid token type")
    return payload


def decode_password_reset_token(token: str) -> dict[str, Any]:
    """Decode a password reset token and verify its type."""
    payload = decode_token(token)
    if payload.get("type") != "password_reset":
        raise JWTError("Invalid token type")
    return payload
