"""
AI-LMS Assignment Repository — database access for assignments and submissions.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment, AssignmentSubmission
from app.repositories.base import BaseRepository


class AssignmentRepository(BaseRepository[Assignment]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Assignment, db)

    async def get_by_course(self, course_id: uuid.UUID) -> list[Assignment]:
        result = await self.db.execute(
            select(Assignment)
            .where(
                Assignment.course_id == course_id,
                Assignment.deleted_at.is_(None),
            )
            .order_by(Assignment.created_at.desc())
        )
        return list(result.scalars().all())


class SubmissionRepository(BaseRepository[AssignmentSubmission]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AssignmentSubmission, db)

    async def get_by_assignment_and_student(
        self, assignment_id: uuid.UUID, student_id: uuid.UUID
    ) -> AssignmentSubmission | None:
        result = await self.db.execute(
            select(AssignmentSubmission).where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student_id,
                AssignmentSubmission.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_assignment(
        self, assignment_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[AssignmentSubmission]:
        result = await self.db.execute(
            select(AssignmentSubmission)
            .where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.deleted_at.is_(None),
            )
            .order_by(AssignmentSubmission.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_student(
        self, student_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[AssignmentSubmission]:
        result = await self.db.execute(
            select(AssignmentSubmission)
            .where(
                AssignmentSubmission.student_id == student_id,
                AssignmentSubmission.deleted_at.is_(None),
            )
            .order_by(AssignmentSubmission.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_assignment(self, assignment_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(AssignmentSubmission)
            .where(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.deleted_at.is_(None),
            )
        )
        return result.scalar_one()
