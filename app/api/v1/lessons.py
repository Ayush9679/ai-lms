"""
AI-LMS Lessons Router — lesson CRUD, file upload, and progress tracking.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.logging import get_logger
from app.dependencies.auth import get_current_user, require_student, require_teacher
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.lesson import (
    CreateLessonRequest,
    LessonProgressResponse,
    LessonProgressUpdate,
    LessonResponse,
    LessonSummary,
    UpdateLessonRequest,
)
from app.services.file_service import FileService
from app.services.lesson_service import LessonService
from app.services.storage_service import get_object_storage, is_r2_key

router = APIRouter()
logger = get_logger(__name__)


async def _lesson_response(lesson) -> LessonResponse:
    data = LessonResponse.model_validate(lesson).model_dump()
    file_svc = FileService()
    data["video_url"] = await file_svc.resolve_url(lesson.video_url)
    data["thumbnail"] = await file_svc.resolve_url(lesson.thumbnail)
    data["pdf_url"] = await file_svc.resolve_url(lesson.pdf_url)
    return LessonResponse(**data)


@router.post(
    "/courses/{course_id}/lessons",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a lesson in a course (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def create_lesson(
    course_id: uuid.UUID,
    request: CreateLessonRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LessonResponse:
    svc = LessonService(db)
    lesson = await svc.create_lesson(course_id, current_user.id, current_user.role, request)
    return await _lesson_response(lesson)


@router.get(
    "/courses/{course_id}/lessons",
    response_model=list[LessonSummary],
    summary="List lessons in a course",
    description="Teachers see all lessons; students see only published ones.",
)
async def list_lessons(
    course_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[LessonSummary]:
    svc = LessonService(db)
    lessons = await svc.get_course_lessons(course_id, current_user.id, current_user.role)
    return [
        LessonSummary(
            id=lesson.id,
            title=lesson.title,
            duration_minutes=lesson.duration_minutes,
            order_index=lesson.order_index,
            is_published=lesson.is_published,
            video_status=lesson.video_status,
            has_video=bool(lesson.video_url),
            has_pdf=bool(lesson.pdf_url),
        )
        for lesson in lessons
    ]


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonResponse,
    summary="Get lesson details",
)
async def get_lesson(
    lesson_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LessonResponse:
    svc = LessonService(db)
    lesson = await svc.get_lesson_for_user(lesson_id, current_user.id, current_user.role)
    return await _lesson_response(lesson)


@router.patch(
    "/lessons/{lesson_id}",
    response_model=LessonResponse,
    summary="Update a lesson (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def update_lesson(
    lesson_id: uuid.UUID,
    request: UpdateLessonRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LessonResponse:
    svc = LessonService(db)
    previous_video = None
    if "video_url" in request.model_fields_set and request.video_url is None:
        editable = await svc.get_editable_lesson(lesson_id, current_user.id, current_user.role)
        previous_video = editable.video_url
    lesson = await svc.update_lesson(lesson_id, current_user.id, current_user.role, request)
    if previous_video and lesson.video_url is None:
        await db.commit()
        if is_r2_key(previous_video):
            try:
                await get_object_storage().delete(previous_video.removeprefix("r2://"))
            except Exception:
                logger.warning("Deleted lesson video object cleanup failed", extra={"operation": "delete_video"})
        elif previous_video.startswith("/") and not previous_video.startswith("/static/"):
            FileService().delete_file(previous_video)
    return await _lesson_response(lesson)


@router.delete(
    "/lessons/{lesson_id}",
    response_model=MessageResponse,
    summary="Delete a lesson (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def delete_lesson(
    lesson_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = LessonService(db)
    await svc.delete_lesson(lesson_id, current_user.id, current_user.role)
    return MessageResponse(message="Lesson deleted successfully")


@router.post(
    "/lessons/{lesson_id}/video",
    response_model=LessonResponse,
    summary="Upload lesson video (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def upload_lesson_video(
    lesson_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> LessonResponse:
    svc = LessonService(db)
    await svc.get_editable_lesson(lesson_id, current_user.id, current_user.role)
    file_svc = FileService()
    _, file_path, _, _, _ = await file_svc.save_video(file)
    lesson = await svc.update_lesson(
        lesson_id,
        current_user.id,
        current_user.role,
        UpdateLessonRequest(video_url=file_path),
    )
    lesson.video_status = "ready"
    return await _lesson_response(lesson)


@router.post(
    "/lessons/{lesson_id}/pdf",
    response_model=LessonResponse,
    summary="Upload lesson PDF (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def upload_lesson_pdf(
    lesson_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> LessonResponse:
    svc = LessonService(db)
    await svc.get_editable_lesson(lesson_id, current_user.id, current_user.role)
    file_svc = FileService()
    _, file_path, _, _, _ = await file_svc.save_document(file)
    lesson = await svc.update_lesson(
        lesson_id,
        current_user.id,
        current_user.role,
        UpdateLessonRequest(pdf_url=file_path),
    )
    return await _lesson_response(lesson)


@router.post(
    "/lessons/{lesson_id}/progress",
    response_model=LessonProgressResponse,
    summary="Update lesson progress (Student)",
    description="Track how much of the lesson a student has watched/read.",
    dependencies=[Depends(require_student)],
)
async def update_progress(
    lesson_id: uuid.UUID,
    request: LessonProgressUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LessonProgressResponse:
    svc = LessonService(db)
    progress = await svc.update_progress(lesson_id, current_user.id, request)
    return LessonProgressResponse.model_validate(progress)


@router.get(
    "/lessons/{lesson_id}/progress",
    response_model=LessonProgressResponse | None,
    summary="Get lesson progress for current student",
    dependencies=[Depends(require_student)],
)
async def get_progress(
    lesson_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LessonProgressResponse | None:
    svc = LessonService(db)
    progress = await svc.get_progress(lesson_id, current_user.id)
    if not progress:
        return None
    return LessonProgressResponse.model_validate(progress)
