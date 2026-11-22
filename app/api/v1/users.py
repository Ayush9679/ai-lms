"""
AI-LMS Users Router — profile management and admin user operations.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User, UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import (
    AdminUpdateUserRequest,
    UpdateProfileRequest,
    UserListResponse,
    UserPublic,
)
from app.services.file_service import FileService
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user profile",
)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserPublic,
    summary="Update own profile",
    description="Update full_name and bio. Upload profile image separately via /me/avatar.",
)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserPublic:
    svc = UserService(db)
    updated = await svc.update_profile(current_user, request)
    return UserPublic.model_validate(updated)


@router.post(
    "/me/avatar",
    response_model=UserPublic,
    summary="Upload profile avatar",
    description="Upload a profile image (JPEG, PNG, WebP, GIF). Max 50MB.",
)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> UserPublic:
    file_svc = FileService()
    _, file_path, _, _, _ = await file_svc.save_image(file)
    svc = UserService(db)
    updated = await svc.update_profile_image(current_user, file_svc.get_full_path(file_path))
    return UserPublic.model_validate(updated)


@router.get(
    "/",
    response_model=PaginatedResponse[UserListResponse],
    summary="List all users (Admin only)",
    dependencies=[Depends(require_admin)],
)
async def list_users(
    role: UserRole | None = Query(default=None, description="Filter by role"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> PaginatedResponse[UserListResponse]:
    svc = UserService(db)
    skip = (page - 1) * page_size
    users = await svc.list_users(role=role, skip=skip, limit=page_size)
    total = await svc.count_users(role=role)
    items = [UserListResponse.model_validate(u) for u in users]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/{user_id}",
    response_model=UserPublic,
    summary="Get user by ID (Admin only)",
    dependencies=[Depends(require_admin)],
)
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserPublic:
    svc = UserService(db)
    user = await svc.get_user(user_id)
    return UserPublic.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserPublic,
    summary="Update any user (Admin only)",
    description="Admin can change role, active status, and verified status.",
    dependencies=[Depends(require_admin)],
)
async def admin_update_user(
    user_id: uuid.UUID,
    request: AdminUpdateUserRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserPublic:
    svc = UserService(db)
    user = await svc.admin_update_user(user_id, request)
    return UserPublic.model_validate(user)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete user (Admin only)",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)],
)
async def delete_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = UserService(db)
    await svc.admin_delete_user(user_id)
    return MessageResponse(message="User deleted successfully")
