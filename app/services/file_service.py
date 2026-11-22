"""
AI-LMS File Service — secure file upload, validation, and storage.
Validates MIME type, enforces size limits, generates unique filenames.
"""

import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import FileTooLargeError, InvalidFileTypeError
from app.core.logging import get_logger
from app.models.course import FileType
from app.services.storage_service import get_object_storage, is_r2_key

logger = get_logger(__name__)
settings = get_settings()

# MIME type → FileType mapping
MIME_TO_FILE_TYPE: dict[str, FileType] = {}
for mime in settings.ALLOWED_IMAGE_TYPES:
    MIME_TO_FILE_TYPE[mime] = FileType.image
for mime in settings.ALLOWED_VIDEO_TYPES:
    MIME_TO_FILE_TYPE[mime] = FileType.video
for mime in settings.ALLOWED_DOCUMENT_TYPES:
    MIME_TO_FILE_TYPE[mime] = FileType.document

# Extension map for generating filenames
EXTENSION_MAP: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/ogg": ".ogv",
    "application/pdf": ".pdf",
}


class FileService:
    def __init__(self) -> None:
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _get_subdir(self, file_type: FileType) -> Path:
        subdir = self.upload_dir / file_type.value
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir

    def _generate_filename(self, mime_type: str) -> str:
        ext = EXTENSION_MAP.get(mime_type, ".bin")
        return f"{uuid.uuid4().hex}{ext}"

    async def validate_and_save(
        self,
        upload: UploadFile,
        allowed_types: list[str] | None = None,
    ) -> tuple[str, str, int, FileType, str]:
        """
        Validate and save an uploaded file.
        Returns: (file_name, file_path, size_bytes, file_type, mime_type)
        """
        # Read content first to validate
        content = await upload.read()
        size = len(content)

        if size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise FileTooLargeError(settings.MAX_UPLOAD_SIZE_MB)

        # Determine MIME type from content type header
        mime_type = upload.content_type or "application/octet-stream"

        # Validate MIME type
        allowed = allowed_types or settings.ALLOWED_MIME_TYPES
        if mime_type not in allowed:
            raise InvalidFileTypeError(mime_type)

        file_type = MIME_TO_FILE_TYPE.get(mime_type, FileType.other)
        upload_limit = settings.MAX_UPLOAD_SIZE_BYTES
        if file_type == FileType.image:
            upload_limit = min(upload_limit, settings.MAX_IMAGE_SIZE_BYTES)
        if size > upload_limit:
            raise FileTooLargeError(upload_limit // (1024 * 1024))
        file_name = self._generate_filename(mime_type)
        r2_configured = any(
            (
                settings.STORAGE_ENDPOINT_URL,
                settings.STORAGE_ACCOUNT_ID,
                settings.STORAGE_ACCESS_KEY_ID,
                settings.STORAGE_SECRET_ACCESS_KEY,
            )
        )
        if r2_configured:
            relative_path = await get_object_storage().put(
                content, mime_type, file_type.value, Path(file_name).suffix
            )
        else:
            subdir = self._get_subdir(file_type)
            file_path = subdir / file_name
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            relative_path = f"/{file_type.value}/{file_name}"
        logger.info("File saved", extra={"path": relative_path, "size": size, "mime": mime_type})
        return file_name, relative_path, size, file_type, mime_type

    async def save_image(self, upload: UploadFile) -> tuple[str, str, int, FileType, str]:
        """Save an image file only."""
        return await self.validate_and_save(upload, settings.ALLOWED_IMAGE_TYPES)

    async def save_video(self, upload: UploadFile) -> tuple[str, str, int, FileType, str]:
        """Save a video file only."""
        return await self.validate_and_save(upload, settings.ALLOWED_VIDEO_TYPES)

    async def save_document(self, upload: UploadFile) -> tuple[str, str, int, FileType, str]:
        """Save a PDF or document file only."""
        return await self.validate_and_save(upload, settings.ALLOWED_DOCUMENT_TYPES)

    async def save_any(self, upload: UploadFile) -> tuple[str, str, int, FileType, str]:
        """Save any allowed file type."""
        return await self.validate_and_save(upload)

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from disk given its relative path."""
        full_path = self.upload_dir / file_path.lstrip("/")
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def get_full_path(self, relative_path: str) -> str:
        """Convert a relative path to the full URL path for serving."""
        return f"/static{relative_path}"

    async def resolve_url(self, stored_path: str | None) -> str | None:
        if not stored_path:
            return None
        if is_r2_key(stored_path):
            return await get_object_storage().presign(stored_path)
        if stored_path.startswith("http://") or stored_path.startswith("https://"):
            return stored_path
        if stored_path.startswith("/static/"):
            return stored_path
        return self.get_full_path(stored_path)
