"""
AI-LMS User Schemas — user profile read/update/list models.
"""
import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import BaseSchema


class UserPublic(BaseSchema):
    """Public-facing user profile (safe to return in any context)."""
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    profile_image: str | None = None
    bio: str | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserSummary(BaseSchema):
    """Compact user info for embedding in related objects."""
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    profile_image: str | None = None


class UpdateProfileRequest(BaseSchema):
    """Request to update the authenticated user's profile."""
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    bio: str | None = Field(default=None, max_length=2000)


class AdminUpdateUserRequest(BaseSchema):
    """Admin-only: update any user's role or active status."""
    role: UserRole | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class UserListResponse(BaseSchema):
    """List of users for admin panel."""
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
