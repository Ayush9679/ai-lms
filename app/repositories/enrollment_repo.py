"""
AI-LMS Enrollment Repository — database access for enrollments.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enrollment import Enrollment, EnrollmentStatus
from app.repositories.base import BaseRepository


class EnrollmentRepository(BaseRepository[Enrollment]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Enrollment, db)

    async def get_by_student_and_course(
        self, student_id: uuid.UUID, course_id: uuid.UUID
    ) -> Enrollment | None:
        result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
                Enrollment.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_student(
        self, student_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[Enrollment]:
        result = await self.db.execute(
            select(Enrollment)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.deleted_at.is_(None),
            )
            .options(selectinload(Enrollment.course))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_course(
        self, course_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Enrollment]:
        result = await self.db.execute(
            select(Enrollment)
            .where(
                Enrollment.course_id == course_id,
                Enrollment.deleted_at.is_(None),
            )
            .options(selectinload(Enrollment.student))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_course(self, course_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Enrollment)
            .where(
                Enrollment.course_id == course_id,
                Enrollment.deleted_at.is_(None),
                Enrollment.status != EnrollmentStatus.dropped,
            )
        )
        return result.scalar_one()

    async def count_by_student(self, student_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Enrollment)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def count_active_students(self) -> int:
        """Count distinct students with at least one active enrollment."""
        result = await self.db.execute(
            select(func.count(func.distinct(Enrollment.student_id)))
            .select_from(Enrollment)
            .where(
                Enrollment.status == EnrollmentStatus.active,
                Enrollment.deleted_at.is_(None),
            )
        )
        return result.scalar_one()
