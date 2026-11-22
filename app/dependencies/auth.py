"""
AI-LMS Auth Dependencies — JWT extraction, user resolution, role guards.
"""

from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.database import AsyncSession, get_db
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository

logger = get_logger(__name__)
security_scheme = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """
    Resolve an optional bearer token for routes that expose published content publicly.
    """
    if not credentials or not credentials.credentials:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid token payload")
    except JWTError:
        raise UnauthorizedError("Invalid or expired access token")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if not user:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")
    if user.deleted_at is not None:
        raise UnauthorizedError("Account not found")

    return user


async def get_current_user(
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    """Require a valid, active authenticated user."""
    if current_user is None:
        raise UnauthorizedError("Bearer token required")
    return current_user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Returns the current user if active (alias for clarity in endpoints)."""
    return current_user


def require_roles(*roles: UserRole):
    """
    Role guard factory. Returns a FastAPI dependency that raises ForbiddenError
    if the current user's role is not in the allowed list.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user = Depends(require_roles(UserRole.admin))):
            ...
    """

    async def role_guard(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles:
            allowed = ", ".join(r.value for r in roles)
            raise ForbiddenError(f"This endpoint requires one of these roles: [{allowed}]")
        return current_user

    return role_guard


# Pre-built role guards for convenience
require_student = require_roles(UserRole.student)
require_teacher = require_roles(UserRole.teacher, UserRole.admin)
require_admin = require_roles(UserRole.admin)
require_teacher_or_student = require_roles(UserRole.student, UserRole.teacher)
