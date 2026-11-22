"""
AI-LMS User Service — profile management and admin user operations.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.schemas.user import AdminUpdateUserRequest, UpdateProfileRequest

logger = get_logger(__name__)


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        return user

    async def update_profile(self, user: User, request: UpdateProfileRequest) -> User:
        """Student/Teacher updates their own profile."""
        update_data = request.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.update(user, **update_data)

    async def update_profile_image(self, user: User, image_url: str) -> User:
        return await self.repo.update(user, profile_image=image_url)

    async def list_users(
        self,
        role: UserRole | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        """Admin: list all users, optionally filtered by role."""
        if role:
            return await self.repo.get_by_role(role, skip, limit)
        return await self.repo.get_all(skip, limit)

    async def admin_update_user(
        self, target_user_id: uuid.UUID, request: AdminUpdateUserRequest
    ) -> User:
        """Admin: update role, active status, or verified status of any user."""
        user = await self.repo.get_by_id(target_user_id)
        if not user:
            raise NotFoundError("User", str(target_user_id))
        update_data = request.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.update(user, **update_data)

    async def admin_delete_user(self, target_user_id: uuid.UUID) -> None:
        """Admin: soft-delete a user account."""
        user = await self.repo.get_by_id(target_user_id)
        if not user:
            raise NotFoundError("User", str(target_user_id))
        await self.repo.soft_delete(user)
        logger.info("User deleted by admin", extra={"user_id": str(target_user_id)})

    async def count_users(self, role: UserRole | None = None) -> int:
        if role:
            filters = [User.role == role, User.deleted_at.is_(None)]
            return await self.repo.count(filters)
        return await self.repo.count()
