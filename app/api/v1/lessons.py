"""
AI-LMS Lessons Router — lesson CRUD, file upload, and progress tracking.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_teacher
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

router = APIRouter()


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
    return LessonResponse.model_validate(lesson)


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
            id=l.id,
            title=l.title,
            duration_minutes=l.duration_minutes,
            order_index=l.order_index,
            is_published=l.is_published,
            has_video=bool(l.video_url),
            has_pdf=bool(l.pdf_url),
        )
        for l in lessons
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
    lesson = await svc.get_lesson(lesson_id)
    return LessonResponse.model_validate(lesson)


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
    lesson = await svc.update_lesson(lesson_id, current_user.id, current_user.role, request)
    return LessonResponse.model_validate(lesson)


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
    file_svc = FileService()
    _, file_path, _, _, _ = await file_svc.save_video(file)
    svc = LessonService(db)
    lesson = await svc.get_lesson(lesson_id)
    lesson = await svc.repo.update(lesson, video_url=file_svc.get_full_path(file_path))
    return LessonResponse.model_validate(lesson)


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
    file_svc = FileService()
    _, file_path, _, _, _ = await file_svc.save_document(file)
    svc = LessonService(db)
    lesson = await svc.get_lesson(lesson_id)
    lesson = await svc.repo.update(lesson, pdf_url=file_svc.get_full_path(file_path))
    return LessonResponse.model_validate(lesson)


@router.post(
    "/lessons/{lesson_id}/progress",
    response_model=LessonProgressResponse,
    summary="Update lesson progress (Student)",
    description="Track how much of the lesson a student has watched/read.",
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
