"""
AI-LMS Enrollments Router — student enrollment management.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_teacher
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.enrollment import EnrollmentResponse, EnrollmentWithCourse, EnrollmentWithStudent, EnrollRequest
from app.schemas.user import UserSummary
from app.services.enrollment_service import EnrollmentService

router = APIRouter()


@router.post(
    "/",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll in a course (Student)",
    description="Enroll the authenticated student in a course.",
)
async def enroll(
    request: EnrollRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnrollmentResponse:
    svc = EnrollmentService(db)
    enrollment = await svc.enroll(current_user.id, request.course_id)
    return EnrollmentResponse.model_validate(enrollment)


@router.get(
    "/my",
    response_model=list[EnrollmentWithCourse],
    summary="Get my enrollments (Student)",
    description="List all courses the current student is enrolled in.",
)
async def get_my_enrollments(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[EnrollmentWithCourse]:
    svc = EnrollmentService(db)
    skip = (page - 1) * page_size
    enrollments = await svc.get_student_enrollments(current_user.id, skip, page_size)
    result = []
    for e in enrollments:
        from app.schemas.course import CourseSummary
        course_summary = None
        if e.course:
            course_summary = CourseSummary(
                id=e.course.id,
                title=e.course.title,
                slug=e.course.slug,
                description=e.course.description,
                category=e.course.category,
                level=e.course.level,
                status=e.course.status,
                thumbnail=e.course.thumbnail,
                price=float(e.course.price),
                instructor_name=e.course.instructor.full_name if e.course.instructor else "Unknown",
                total_lessons=0,
                total_students=0,
                created_at=e.course.created_at,
            )
        result.append(
            EnrollmentWithCourse(
                id=e.id,
                student_id=e.student_id,
                course_id=e.course_id,
                status=e.status,
                progress=e.progress,
                completed_lessons=e.completed_lessons,
                created_at=e.created_at,
                updated_at=e.updated_at,
                course=course_summary,
            )
        )
    return result


@router.delete(
    "/{course_id}",
    response_model=MessageResponse,
    summary="Drop a course enrollment (Student)",
)
async def drop_enrollment(
    course_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = EnrollmentService(db)
    await svc.drop_enrollment(current_user.id, course_id)
    return MessageResponse(message="Successfully dropped from course")


@router.get(
    "/courses/{course_id}/students",
    response_model=list[EnrollmentWithStudent],
    summary="List enrolled students in a course (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def get_course_students(
    course_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> list[EnrollmentWithStudent]:
    svc = EnrollmentService(db)
    skip = (page - 1) * page_size
    enrollments = await svc.get_course_students(course_id, current_user.id, skip, page_size)
    result = []
    for e in enrollments:
        student_summary = None
        if e.student:
            student_summary = UserSummary(
                id=e.student.id,
                full_name=e.student.full_name,
                email=e.student.email,
                role=e.student.role,
                profile_image=e.student.profile_image,
            )
        result.append(
            EnrollmentWithStudent(
                id=e.id,
                student_id=e.student_id,
                course_id=e.course_id,
                status=e.status,
                progress=e.progress,
                completed_lessons=e.completed_lessons,
                created_at=e.created_at,
                updated_at=e.updated_at,
                student=student_summary,
            )
        )
    return result


@router.get(
    "/{course_id}/status",
    response_model=EnrollmentResponse | None,
    summary="Check enrollment status for a course",
)
async def check_enrollment(
    course_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnrollmentResponse | None:
    svc = EnrollmentService(db)
    try:
        enrollment = await svc.get_enrollment(current_user.id, course_id)
        return EnrollmentResponse.model_validate(enrollment)
    except Exception:
        return None
