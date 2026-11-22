"""Authenticated direct-upload grants for private R2 objects."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_teacher
from app.models.user import User
from app.schemas.upload import (
    CompleteUploadRequest,
    PresignUploadRequest,
    PresignUploadResponse,
    UploadStatusResponse,
)
from app.services.upload_service import UploadService

router = APIRouter()


@router.post(
    "/presign", response_model=PresignUploadResponse, dependencies=[Depends(require_teacher)]
)
async def presign_upload(
    request: PresignUploadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await UploadService(db).start(
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        asset_type=request.asset_type,
        mime_type=request.mime_type,
        size_bytes=request.size_bytes,
        requester_id=current_user.id,
        requester_role=current_user.role,
        original_name=request.original_name,
    )


@router.post(
    "/complete", response_model=UploadStatusResponse, dependencies=[Depends(require_teacher)]
)
async def complete_upload(
    request: CompleteUploadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return {
        "status": await UploadService(db).complete(
            request.upload_token, current_user.id, current_user.role
        )
    }


@router.post(
    "/cancel", response_model=UploadStatusResponse, dependencies=[Depends(require_teacher)]
)
async def cancel_upload(
    request: CompleteUploadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return {
        "status": await UploadService(db).cancel(
            request.upload_token, current_user.id, current_user.role
        )
    }
