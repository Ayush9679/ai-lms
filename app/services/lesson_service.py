"""
AI-LMS Lesson Service — lesson CRUD and progress tracking.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.lesson import Lesson, LessonProgress
from app.models.user import UserRole
from app.repositories.course_repo import CourseRepository
from app.repositories.enrollment_repo import EnrollmentRepository
from app.repositories.lesson_repo import LessonProgressRepository, LessonRepository
from app.schemas.lesson import CreateLessonRequest, LessonProgressUpdate, UpdateLessonRequest

logger = get_logger(__name__)


class LessonService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = LessonRepository(db)
        self.progress_repo = LessonProgressRepository(db)
        self.course_repo = CourseRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)

    async def _get_course_or_404(self, course_id: uuid.UUID):
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundError("Course", str(course_id))
        return course

    async def create_lesson(
        self,
        course_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        request: CreateLessonRequest,
    ) -> Lesson:
        course = await self._get_course_or_404(course_id)
        if requester_role != UserRole.admin and course.instructor_id != requester_id:
            raise ForbiddenError("You can only add lessons to your own courses")
        lesson = await self.repo.create(
            course_id=course_id,
            **request.model_dump(),
        )
        logger.info("Lesson created", extra={"lesson_id": str(lesson.id)})
        return lesson

    async def get_lesson(self, lesson_id: uuid.UUID) -> Lesson:
        lesson = await self.repo.get_by_id(lesson_id)
        if not lesson:
            raise NotFoundError("Lesson", str(lesson_id))
        return lesson

    async def get_course_lessons(
        self,
        course_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
    ) -> list[Lesson]:
        """Teachers see all lessons; students see only published."""
        await self._get_course_or_404(course_id)
        if requester_role in (UserRole.teacher, UserRole.admin):
            return await self.repo.get_by_course(course_id)
        return await self.repo.get_published_by_course(course_id)

    async def update_lesson(
        self,
        lesson_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        request: UpdateLessonRequest,
    ) -> Lesson:
        lesson = await self.get_lesson(lesson_id)
        course = await self._get_course_or_404(lesson.course_id)
        if requester_role != UserRole.admin and course.instructor_id != requester_id:
            raise ForbiddenError("You can only edit lessons in your own courses")
        update_data = request.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.update(lesson, **update_data)

    async def delete_lesson(
        self,
        lesson_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
    ) -> None:
        lesson = await self.get_lesson(lesson_id)
        course = await self._get_course_or_404(lesson.course_id)
        if requester_role != UserRole.admin and course.instructor_id != requester_id:
            raise ForbiddenError("You can only delete lessons in your own courses")
        await self.repo.soft_delete(lesson)

    async def update_progress(
        self,
        lesson_id: uuid.UUID,
        user_id: uuid.UUID,
        request: LessonProgressUpdate,
    ) -> LessonProgress:
        """Create or update a student's progress on a lesson."""
        lesson = await self.get_lesson(lesson_id)

        progress = await self.progress_repo.get_by_lesson_and_user(lesson_id, user_id)
        if progress:
            updated = await self.progress_repo.update(
                progress,
                watch_time_seconds=request.watch_time_seconds,
                completion_percentage=request.completion_percentage,
                is_completed=request.is_completed,
            )
        else:
            updated = await self.progress_repo.create(
                lesson_id=lesson_id,
                user_id=user_id,
                watch_time_seconds=request.watch_time_seconds,
                completion_percentage=request.completion_percentage,
                is_completed=request.is_completed,
            )

        # Recalculate enrollment progress
        await self._recalculate_course_progress(lesson.course_id, user_id)
        return updated

    async def get_progress(
        self, lesson_id: uuid.UUID, user_id: uuid.UUID
    ) -> LessonProgress | None:
        return await self.progress_repo.get_by_lesson_and_user(lesson_id, user_id)

    async def _recalculate_course_progress(
        self, course_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Recalculate overall course completion % and update enrollment."""
        enrollment = await self.enrollment_repo.get_by_student_and_course(user_id, course_id)
        if not enrollment:
            return

        total = await self.repo.count_by_course(course_id)
        if total == 0:
            return

        completed = await self.progress_repo.get_completed_count_for_course(user_id, course_id)
        progress_pct = (completed / total) * 100.0

        from app.models.enrollment import EnrollmentStatus
        new_status = (
            EnrollmentStatus.completed if progress_pct >= 100.0 else EnrollmentStatus.active
        )
        await self.enrollment_repo.update(
            enrollment,
            progress=round(progress_pct, 2),
            completed_lessons=completed,
            status=new_status,
        )
