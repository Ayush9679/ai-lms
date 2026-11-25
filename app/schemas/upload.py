import uuid
from typing import Literal

from pydantic import Field

from app.schemas.common import BaseSchema


class PresignedUploadPart(BaseSchema):
    part_number: int = Field(gt=0)
    upload_url: str


class PresignUploadRequest(BaseSchema):
    resource_type: Literal["course", "lesson"]
    resource_id: uuid.UUID
    asset_type: Literal["thumbnail", "video", "pdf", "file"]
    mime_type: str = Field(min_length=3, max_length=100)
    size_bytes: int = Field(gt=0)
    original_name: str | None = Field(default=None, max_length=500)


class PresignUploadResponse(BaseSchema):
    upload_method: Literal["put", "multipart"]
    upload_url: str | None = None
    parts: list[PresignedUploadPart] = Field(default_factory=list)
    part_size_bytes: int | None = None
    upload_token: str
    expires_in: int


class CompletedUploadPart(BaseSchema):
    part_number: int = Field(gt=0)
    etag: str = Field(max_length=256)


class CompleteUploadRequest(BaseSchema):
    upload_token: str = Field(min_length=20)
    parts: list[CompletedUploadPart] = Field(default_factory=list, max_length=10000)


class CancelUploadRequest(CompleteUploadRequest):
    """Cancel a user-aborted upload or record a failed storage PUT."""

    failed: bool = False


class UploadStatusResponse(BaseSchema):
    status: Literal["ready", "cancelled"]
