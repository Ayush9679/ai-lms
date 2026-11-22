"""
AI-LMS Courses Router — course CRUD, search, thumbnail upload, and file management.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.dependencies.auth import get_current_user, get_optional_user, require_teacher
from app.models.course import CourseStatus
from app.models.user import User, UserRole
from app.repositories.course_repo import CourseFileRepository
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.course import (
    CourseSummary,
    CourseFileResponse,
    CourseResponse,
    CreateCourseRequest,
    UpdateCourseRequest,
)
from app.services.course_service import CourseService
from app.services.file_service import FileService

router = APIRouter()


async def _course_to_summary(
    course, total_lessons: int = 0, total_students: int = 0
) -> CourseSummary:
    file_svc = FileService()
    return CourseSummary(
        id=course.id,
        title=course.title,
        slug=course.slug,
        description=course.description,
        category=course.category,
        level=course.level,
        status=course.status,
        thumbnail=await file_svc.resolve_url(course.thumbnail),
        price=float(course.price),
        instructor_name=course.instructor.full_name if course.instructor else "Unknown",
        total_lessons=total_lessons,
        total_students=total_students,
        created_at=course.created_at,
    )


@router.post(
    "/",
    response_model=CourseSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def create_course(
    request: CreateCourseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseSummary:
    svc = CourseService(db)
    course = await svc.create_course(current_user.id, request)
    return await _course_to_summary(course)


@router.get(
    "/",
    response_model=PaginatedResponse[CourseSummary],
    summary="List / search published courses",
    description="Public endpoint for published courses with text search, category/level filtering, pagination, and sorting.",
)
async def list_courses(
    q: str | None = Query(default=None, description="Search query"),
    category: str | None = Query(default=None),
    level: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> PaginatedResponse[CourseSummary]:
    svc = CourseService(db)
    skip = (page - 1) * page_size
    courses, total = await svc.search_courses(
        query=q,
        category=category,
        level=level,
        status=CourseStatus.published,
        skip=skip,
        limit=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    items = [await _course_to_summary(c) for c in courses]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/my",
    response_model=list[CourseSummary],
    summary="Get teacher's own courses",
    dependencies=[Depends(require_teacher)],
)
async def get_my_courses(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[CourseSummary]:
    svc = CourseService(db)
    skip = (page - 1) * page_size
    courses = await svc.list_teacher_courses(current_user.id, skip=skip, limit=page_size)
    return [await _course_to_summary(c) for c in courses]


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Get course details",
)
async def get_course(
    course_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> CourseResponse:
    svc = CourseService(db)
    course = await svc.get_course(course_id)
    if course.status != CourseStatus.published and (
        current_user is None
        or (current_user.role != UserRole.admin and course.instructor_id != current_user.id)
    ):
        raise NotFoundError("Course", str(course_id))
    total_lessons = await svc.get_total_lessons(course_id)
    total_students = await svc.get_total_students(course_id)
    return CourseResponse(
        id=course.id,
        title=course.title,
        slug=course.slug,
        description=course.description,
        category=course.category,
        level=course.level,
        status=course.status,
        thumbnail=await FileService().resolve_url(course.thumbnail),
        price=float(course.price),
        tags=course.tags,
        instructor=course.instructor,
        instructor_id=course.instructor_id,
        total_lessons=total_lessons,
        total_students=total_students,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )


@router.patch(
    "/{course_id}",
    response_model=CourseSummary,
    summary="Update course (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def update_course(
    course_id: uuid.UUID,
    request: UpdateCourseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseSummary:
    svc = CourseService(db)
    course = await svc.update_course(course_id, current_user.id, current_user.role, request)
    return await _course_to_summary(course)


@router.delete(
    "/{course_id}",
    response_model=MessageResponse,
    summary="Delete course (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def delete_course(
    course_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = CourseService(db)
    await svc.delete_course(course_id, current_user.id, current_user.role)
    return MessageResponse(message="Course deleted successfully")


@router.post(
    "/{course_id}/thumbnail",
    response_model=CourseSummary,
    summary="Upload course thumbnail (Teacher/Admin)",
    description="Upload a course thumbnail image.",
    dependencies=[Depends(require_teacher)],
)
async def upload_thumbnail(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> CourseSummary:
    svc = CourseService(db)
    course = await svc.get_manageable_course(course_id, current_user.id, current_user.role)

    file_svc = FileService()
    _, file_path, _, _, _ = await file_svc.save_image(file)
    course = await svc.set_thumbnail(course, current_user.id, current_user.role, file_path)
    return await _course_to_summary(course)


@router.post(
    "/{course_id}/files",
    response_model=CourseFileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file to course (Teacher/Admin)",
    description="Upload a PDF, video, or image to a course.",
    dependencies=[Depends(require_teacher)],
)
async def upload_course_file(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> CourseFileResponse:
    svc = CourseService(db)
    await svc.get_manageable_course(course_id, current_user.id, current_user.role)
    file_svc = FileService()
    file_name, file_path, size, file_type, mime_type = await file_svc.save_any(file)
    repo = CourseFileRepository(db)
    course_file = await repo.create(
        course_id=course_id,
        uploaded_by=current_user.id,
        file_name=file_name,
        original_name=file.filename or file_name,
        file_path=file_path,
        file_type=file_type,
        mime_type=mime_type,
        size_bytes=size,
    )
    return CourseFileResponse(
        **{
            **CourseFileResponse.model_validate(course_file).model_dump(),
            "file_path": await file_svc.resolve_url(course_file.file_path),
        }
    )


@router.get(
    "/{course_id}/files",
    response_model=list[CourseFileResponse],
    summary="List course files",
)
async def list_course_files(
    course_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> list[CourseFileResponse]:
    course = await CourseService(db).get_course(course_id)
    is_manager = bool(
        current_user
        and (current_user.role == UserRole.admin or course.instructor_id == current_user.id)
    )
    if not is_manager:
        if not current_user:
            raise ForbiddenError("Authentication is required to access course files")
        if course.price > 0:
            raise ForbiddenError("Paid course files require a completed purchase")
        from app.repositories.enrollment_repo import EnrollmentRepository

        enrollment = await EnrollmentRepository(db).get_by_student_and_course(
            current_user.id, course_id
        )
        if (
            course.status != CourseStatus.published
            or not enrollment
            or enrollment.status.value not in {"active", "completed"}
        ):
            raise ForbiddenError("You must be enrolled to access course files")
    repo = CourseFileRepository(db)
    files = await repo.get_by_course(course_id)
    file_svc = FileService()
    return [
        CourseFileResponse(
            **{
                **CourseFileResponse.model_validate(f).model_dump(),
                "file_path": await file_svc.resolve_url(f.file_path),
            }
        )
        for f in files
    ]
