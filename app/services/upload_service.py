"""Authorize and complete direct browser uploads to private object storage."""

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NoReturn

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AILMSException, ForbiddenError, InvalidFileTypeError, ValidationError
from app.core.logging import get_logger
from app.models.course import Course, FileType
from app.models.lesson import Lesson
from app.models.user import UserRole
from app.repositories.course_repo import CourseFileRepository
from app.services.course_service import CourseService
from app.services.lesson_service import LessonService
from app.services.storage_service import get_object_storage, is_r2_key
from app.utils.media_validation import content_matches_mime

settings = get_settings()
logger = get_logger(__name__)

IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
VIDEO_EXTENSIONS = {"video/mp4": ".mp4", "video/webm": ".webm", "video/ogg": ".ogv"}
PDF_MIME = "application/pdf"


class UploadService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.retired_object_keys: list[str] = []

    async def cleanup_retired_objects(self) -> None:
        """Delete superseded private objects only after the database commit succeeds."""
        storage = get_object_storage()
        for stored_value in self.retired_object_keys:
            try:
                await storage.delete(stored_value.removeprefix("r2://"))
            except Exception:
                logger.warning(
                    "Superseded R2 object cleanup failed",
                    extra={"operation": "delete_replaced_object"},
                )

    def _validate_asset(
        self, resource_type: str, asset_type: str, mime_type: str, size: int
    ) -> str:
        if asset_type == "thumbnail":
            extensions = IMAGE_EXTENSIONS
            max_size = settings.MAX_IMAGE_SIZE_BYTES
        elif asset_type == "video" and resource_type == "lesson":
            extensions = VIDEO_EXTENSIONS
            max_size = settings.MAX_VIDEO_SIZE_BYTES
        elif asset_type == "pdf" and resource_type == "lesson":
            extensions = {PDF_MIME: ".pdf"}
            max_size = settings.MAX_UPLOAD_SIZE_BYTES
        elif asset_type == "file" and resource_type == "course":
            extensions = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | {PDF_MIME: ".pdf"}
            max_size = (
                settings.MAX_IMAGE_SIZE_BYTES
                if mime_type in IMAGE_EXTENSIONS
                else settings.MAX_VIDEO_SIZE_BYTES
                if mime_type in VIDEO_EXTENSIONS
                else settings.MAX_UPLOAD_SIZE_BYTES
            )
        else:
            raise ValidationError("This asset type is not supported for the selected resource.")

        extension = extensions.get(mime_type)
        if not extension:
            raise InvalidFileTypeError(mime_type)
        if size > max_size:
            raise ValidationError(
                f"File exceeds the {max_size // (1024 * 1024)} MB limit for {asset_type} uploads."
            )
        return extension

    async def _get_owned_resource(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
    ) -> Course | Lesson:
        if resource_type == "course":
            return await CourseService(self.db).get_manageable_course(
                resource_id, requester_id, requester_role
            )
        if resource_type == "lesson":
            return await LessonService(self.db).get_editable_lesson(
                resource_id, requester_id, requester_role
            )
        raise ValidationError("Unsupported upload resource.")

    async def start(
        self,
        *,
        resource_type: str,
        resource_id: uuid.UUID,
        asset_type: str,
        mime_type: str,
        size_bytes: int,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        original_name: str | None = None,
    ) -> dict:
        extension = self._validate_asset(resource_type, asset_type, mime_type, size_bytes)
        resource = await self._get_owned_resource(
            resource_type, resource_id, requester_id, requester_role
        )
        upload_id = str(uuid.uuid4())
        folder = "files" if asset_type == "file" else asset_type
        key = f"{resource_type}s/{resource_id}/{folder}/{upload_id}{extension}"
        storage = get_object_storage()
        upload_url = await storage.presign_put(
            key, mime_type, size_bytes, settings.STORAGE_PRESIGNED_URL_TTL
        )

        upload_field = f"{asset_type}_upload_id"
        if hasattr(resource, upload_field):
            setattr(resource, upload_field, upload_id)
        if isinstance(resource, Lesson) and asset_type == "video":
            resource.video_status = "uploading"
        self.db.add(resource)
        await self.db.flush()

        now = datetime.now(timezone.utc)
        grant = {
            "type": "object_upload",
            "sub": str(requester_id),
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "asset_type": asset_type,
            "upload_id": upload_id,
            "key": key,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "original_name": Path((original_name or "upload").replace("\\", "/")).name[:500],
            "iat": now,
            "exp": now + timedelta(seconds=settings.STORAGE_UPLOAD_GRANT_TTL),
        }
        return {
            "upload_url": upload_url,
            "upload_token": jwt.encode(grant, settings.SECRET_KEY, algorithm=settings.ALGORITHM),
            "expires_in": settings.STORAGE_PRESIGNED_URL_TTL,
        }

    def _decode_grant(self, token: str, requester_id: uuid.UUID) -> dict:
        try:
            grant = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError as exc:
            raise ForbiddenError(
                "Upload authorization is invalid or expired. Start a new upload."
            ) from exc
        if grant.get("type") != "object_upload" or grant.get("sub") != str(requester_id):
            raise ForbiddenError("Upload authorization does not belong to this user.")
        return grant

    async def _reject_upload(
        self, resource: Course | Lesson, grant: dict, message: str
    ) -> NoReturn:
        """Invalidate the grant and leave video state failed after verified rejection."""
        upload_field = f"{grant.get('asset_type')}_upload_id"
        if getattr(resource, upload_field, None) == grant.get("upload_id"):
            setattr(resource, upload_field, None)
            if isinstance(resource, Lesson) and grant.get("asset_type") == "video":
                resource.video_status = "failed"
            self.db.add(resource)
            await self.db.flush()
        try:
            await get_object_storage().delete(grant["key"])
        except Exception:
            logger.warning(
                "Rejected upload object cleanup failed",
                extra={"operation": "delete_rejected_upload", "asset_type": grant.get("asset_type")},
            )
        raise ValidationError(message)

    async def complete(self, token: str, requester_id: uuid.UUID, requester_role: UserRole) -> str:
        grant = self._decode_grant(token, requester_id)
        resource: Course | Lesson | None = None
        try:
            resource_id = uuid.UUID(grant["resource_id"])
            resource = await self._get_owned_resource(
                grant["resource_type"], resource_id, requester_id, requester_role
            )
            upload_field = f"{grant['asset_type']}_upload_id"
            if isinstance(resource, Course) and grant.get("asset_type") == "file":
                existing_files = await CourseFileRepository(self.db).get_by_course(resource.id)
                if any(file.upload_id == grant.get("upload_id") for file in existing_files):
                    return "ready"
            if getattr(resource, upload_field, None) != grant.get("upload_id"):
                raise ForbiddenError("This upload was replaced or cancelled. Start a new upload.")
            metadata = await get_object_storage().head(grant["key"])
        except (KeyError, ValueError) as exc:
            raise ForbiddenError("Upload authorization is invalid. Start a new upload.") from exc
        except Exception as exc:
            if isinstance(exc, AILMSException):
                raise
            logger.warning(
                "R2 object HEAD verification failed",
                extra={"operation": "head_object", "asset_type": grant.get("asset_type")},
            )
            if resource is not None:
                await self._reject_upload(
                    resource, grant, "The uploaded object is missing or could not be verified. Retry upload."
                )
            raise ValidationError("The uploaded object is missing or could not be verified. Retry upload.") from exc

        if resource is None:
            raise ValidationError("The uploaded resource could not be verified. Start a new upload.")

        if metadata.get("ContentLength") != grant.get("size_bytes"):
            await self._reject_upload(
                resource,
                grant,
                "Uploaded file size did not match the authorized upload. Retry upload.",
            )
        if metadata.get("ContentType") != grant.get("mime_type"):
            await self._reject_upload(
                resource,
                grant,
                "Uploaded file type did not match the authorized upload. Retry upload.",
            )

        try:
            prefix = await get_object_storage().read_prefix(grant["key"])
        except Exception:
            logger.warning(
                "R2 object content verification failed",
                extra={"operation": "read_object_prefix", "asset_type": grant.get("asset_type")},
            )
            await self._reject_upload(
                resource, grant, "The uploaded file content could not be verified. Retry the upload."
            )
        if not content_matches_mime(grant["mime_type"], prefix):
            await self._reject_upload(
                resource,
                grant,
                "The file content does not match its declared type. Choose a valid file and retry.",
            )

        stored_key = f"r2://{grant['key']}"
        asset_type = grant["asset_type"]
        if isinstance(resource, Course):
            if asset_type == "thumbnail":
                if is_r2_key(resource.thumbnail) and resource.thumbnail != stored_key:
                    self.retired_object_keys.append(resource.thumbnail)
                resource.thumbnail = stored_key
            elif asset_type == "file":
                mime_type = grant["mime_type"]
                file_type = (
                    FileType.image
                    if mime_type in IMAGE_EXTENSIONS
                    else FileType.video
                    if mime_type in VIDEO_EXTENSIONS
                    else FileType.document
                )
                await CourseFileRepository(self.db).create(
                    course_id=resource.id,
                    uploaded_by=requester_id,
                    upload_id=grant["upload_id"],
                    file_name=Path(grant["key"]).name,
                    original_name=grant.get("original_name") or Path(grant["key"]).name,
                    file_path=stored_key,
                    file_type=file_type,
                    mime_type=mime_type,
                    size_bytes=grant["size_bytes"],
                )
        elif isinstance(resource, Lesson):
            if asset_type == "thumbnail":
                if is_r2_key(resource.thumbnail) and resource.thumbnail != stored_key:
                    self.retired_object_keys.append(resource.thumbnail)
                resource.thumbnail = stored_key
            elif asset_type == "video":
                if is_r2_key(resource.video_url) and resource.video_url != stored_key:
                    self.retired_object_keys.append(resource.video_url)
                resource.video_url = stored_key
                resource.video_size_bytes = grant["size_bytes"]
                resource.video_status = "ready"
            elif asset_type == "pdf":
                if is_r2_key(resource.pdf_url) and resource.pdf_url != stored_key:
                    self.retired_object_keys.append(resource.pdf_url)
                resource.pdf_url = stored_key
        setattr(resource, upload_field, None)
        self.db.add(resource)
        await self.db.flush()
        return "ready"

    async def cancel(
        self,
        token: str,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        *,
        failed: bool = False,
    ) -> str:
        grant = self._decode_grant(token, requester_id)
        try:
            resource_id = uuid.UUID(grant["resource_id"])
            resource = await self._get_owned_resource(
                grant["resource_type"], resource_id, requester_id, requester_role
            )
        except (KeyError, ValueError) as exc:
            raise ForbiddenError("Upload authorization is invalid.") from exc
        upload_field = f"{grant['asset_type']}_upload_id"
        if getattr(resource, upload_field, None) != grant.get("upload_id"):
            return "cancelled"
        setattr(resource, upload_field, None)
        if isinstance(resource, Lesson) and grant["asset_type"] == "video":
            resource.video_status = (
                "failed" if failed else "ready" if resource.video_url else "pending"
            )
        try:
            await get_object_storage().delete(grant["key"])
        except Exception:
            # An upload may have been cancelled before any object reached R2.
            pass
        self.db.add(resource)
        await self.db.flush()
        return "cancelled"
