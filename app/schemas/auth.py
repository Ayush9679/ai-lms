"""
AI-LMS Auth Schemas — registration, login, token refresh, password management.
"""

from pydantic import EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.common import BaseSchema


class RegisterRequest(BaseSchema):
    """New user registration request."""

    full_name: str = Field(min_length=2, max_length=255, examples=["Jane Doe"])
    email: EmailStr = Field(examples=["jane@example.com"])
    password: str = Field(min_length=8, max_length=128, examples=["SecurePass123!"])
    role: UserRole = Field(default=UserRole.student, examples=["student"])

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("role")
    @classmethod
    def no_admin_self_register(cls, v: UserRole) -> UserRole:
        if v == UserRole.admin:
            raise ValueError("Cannot self-register as admin")
        return v


class LoginRequest(BaseSchema):
    """User login request."""

    email: EmailStr = Field(examples=["jane@example.com"])
    password: str = Field(examples=["SecurePass123!"])


class TokenResponse(BaseSchema):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseSchema):
    """Request to exchange a refresh token for a new access token."""

    refresh_token: str


class ForgotPasswordRequest(BaseSchema):
    """Initiate a password reset by email."""

    email: EmailStr


class ResetPasswordRequest(BaseSchema):
    """Complete a password reset with the token from email."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class VerifyEmailRequest(BaseSchema):
    """Verify email with the token from the verification email."""

    token: str


class ChangePasswordRequest(BaseSchema):
    """Authenticated user changes their own password."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
