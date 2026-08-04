"""
AI-LMS Lesson Repository — database access for lessons and progress.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson, LessonProgress
from app.repositories.base import BaseRepository


class LessonRepository(BaseRepository[Lesson]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Lesson, db)

    async def get_by_course(self, course_id: uuid.UUID) -> list[Lesson]:
        """Return all lessons for a course ordered by index."""
        result = await self.db.execute(
            select(Lesson)
            .where(Lesson.course_id == course_id, Lesson.deleted_at.is_(None))
            .order_by(Lesson.order_index.asc())
        )
        return list(result.scalars().all())

    async def get_published_by_course(self, course_id: uuid.UUID) -> list[Lesson]:
        """Return only published lessons for a course (student view)."""
        result = await self.db.execute(
            select(Lesson)
            .where(
                Lesson.course_id == course_id,
                Lesson.is_published.is_(True),
                Lesson.deleted_at.is_(None),
            )
            .order_by(Lesson.order_index.asc())
        )
        return list(result.scalars().all())

    async def count_by_course(self, course_id: uuid.UUID) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count())
            .select_from(Lesson)
            .where(Lesson.course_id == course_id, Lesson.deleted_at.is_(None))
        )
        return result.scalar_one()


class LessonProgressRepository(BaseRepository[LessonProgress]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(LessonProgress, db)

    async def get_by_lesson_and_user(
        self, lesson_id: uuid.UUID, user_id: uuid.UUID
    ) -> LessonProgress | None:
        result = await self.db.execute(
            select(LessonProgress).where(
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.user_id == user_id,
                LessonProgress.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_completed_count_for_course(
        self, user_id: uuid.UUID, course_id: uuid.UUID
    ) -> int:
        """Count completed lessons for a student in a specific course."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count())
            .select_from(LessonProgress)
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .where(
                LessonProgress.user_id == user_id,
                Lesson.course_id == course_id,
                LessonProgress.is_completed.is_(True),
                LessonProgress.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def get_by_user_and_course(
        self, user_id: uuid.UUID, course_id: uuid.UUID
    ) -> list[LessonProgress]:
        result = await self.db.execute(
            select(LessonProgress)
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .where(
                LessonProgress.user_id == user_id,
                Lesson.course_id == course_id,
                LessonProgress.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
