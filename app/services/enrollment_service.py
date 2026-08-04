"""
AI-LMS Enrollment Service — student enrollment and progress.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyEnrolledError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.repositories.course_repo import CourseRepository
from app.repositories.enrollment_repo import EnrollmentRepository

logger = get_logger(__name__)


class EnrollmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = EnrollmentRepository(db)
        self.course_repo = CourseRepository(db)

    async def enroll(self, student_id: uuid.UUID, course_id: uuid.UUID) -> Enrollment:
        """Enroll a student in a course."""
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundError("Course", str(course_id))

        existing = await self.repo.get_by_student_and_course(student_id, course_id)
        if existing:
            if existing.status == EnrollmentStatus.dropped:
                # Re-enroll
                return await self.repo.update(
                    existing, status=EnrollmentStatus.active
                )
            raise AlreadyEnrolledError()

        enrollment = await self.repo.create(
            student_id=student_id,
            course_id=course_id,
            status=EnrollmentStatus.active,
            progress=0.0,
            completed_lessons=0,
        )
        logger.info(
            "Student enrolled",
            extra={"student_id": str(student_id), "course_id": str(course_id)},
        )
        return enrollment

    async def drop_enrollment(
        self, student_id: uuid.UUID, course_id: uuid.UUID
    ) -> None:
        """Drop a student from a course."""
        enrollment = await self.repo.get_by_student_and_course(student_id, course_id)
        if not enrollment:
            raise NotFoundError("Enrollment")
        await self.repo.update(enrollment, status=EnrollmentStatus.dropped)

    async def get_enrollment(
        self, student_id: uuid.UUID, course_id: uuid.UUID
    ) -> Enrollment:
        enrollment = await self.repo.get_by_student_and_course(student_id, course_id)
        if not enrollment:
            raise NotFoundError("Enrollment")
        return enrollment

    async def is_enrolled(self, student_id: uuid.UUID, course_id: uuid.UUID) -> bool:
        enrollment = await self.repo.get_by_student_and_course(student_id, course_id)
        return enrollment is not None and enrollment.status == EnrollmentStatus.active

    async def get_student_enrollments(
        self, student_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[Enrollment]:
        return await self.repo.get_by_student(student_id, skip, limit)

    async def get_course_students(
        self, course_id: uuid.UUID, requester_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Enrollment]:
        """Get students enrolled in a course (teacher/admin only)."""
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundError("Course", str(course_id))
        return await self.repo.get_by_course(course_id, skip, limit)

    async def count_enrolled(self, course_id: uuid.UUID) -> int:
        return await self.repo.count_by_course(course_id)
