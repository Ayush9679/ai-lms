import uuid
from typing import Literal

from pydantic import Field

from app.schemas.common import BaseSchema


class PresignUploadRequest(BaseSchema):
    resource_type: Literal["course", "lesson"]
    resource_id: uuid.UUID
    asset_type: Literal["thumbnail", "video", "pdf", "file"]
    mime_type: str = Field(min_length=3, max_length=100)
    size_bytes: int = Field(gt=0)
    original_name: str | None = Field(default=None, max_length=500)


class PresignUploadResponse(BaseSchema):
    upload_url: str
    upload_token: str
    expires_in: int


class CompleteUploadRequest(BaseSchema):
    upload_token: str = Field(min_length=20)


class CancelUploadRequest(CompleteUploadRequest):
    """Cancel a user-aborted upload or record a failed storage PUT."""

    failed: bool = False


class UploadStatusResponse(BaseSchema):
    status: Literal["ready", "cancelled"]
