"""
AI-LMS Quiz Repository — database access for quizzes, questions, and attempts.
"""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Question, Quiz, QuizAnswer, QuizAttempt
from app.repositories.base import BaseRepository


class QuizRepository(BaseRepository[Quiz]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Quiz, db)

    async def get_by_course(self, course_id: uuid.UUID) -> list[Quiz]:
        result = await self.db.execute(
            select(Quiz)
            .where(Quiz.course_id == course_id, Quiz.deleted_at.is_(None))
            .order_by(Quiz.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_lesson(self, lesson_id: uuid.UUID) -> list[Quiz]:
        result = await self.db.execute(
            select(Quiz)
            .where(Quiz.lesson_id == lesson_id, Quiz.deleted_at.is_(None))
        )
        return list(result.scalars().all())


class QuestionRepository(BaseRepository[Question]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Question, db)

    async def get_by_quiz(self, quiz_id: uuid.UUID) -> list[Question]:
        result = await self.db.execute(
            select(Question)
            .where(Question.quiz_id == quiz_id, Question.deleted_at.is_(None))
            .order_by(Question.order_index.asc())
        )
        return list(result.scalars().all())


class QuizAttemptRepository(BaseRepository[QuizAttempt]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(QuizAttempt, db)

    async def get_by_student_and_quiz(
        self, student_id: uuid.UUID, quiz_id: uuid.UUID
    ) -> list[QuizAttempt]:
        result = await self.db.execute(
            select(QuizAttempt)
            .where(
                QuizAttempt.student_id == student_id,
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.deleted_at.is_(None),
            )
            .order_by(QuizAttempt.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_student_and_quiz(
        self, student_id: uuid.UUID, quiz_id: uuid.UUID
    ) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(QuizAttempt)
            .where(
                QuizAttempt.student_id == student_id,
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    async def get_by_student(
        self, student_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[QuizAttempt]:
        result = await self.db.execute(
            select(QuizAttempt)
            .where(
                QuizAttempt.student_id == student_id,
                QuizAttempt.deleted_at.is_(None),
            )
            .order_by(QuizAttempt.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_average_score_for_quiz(self, quiz_id: uuid.UUID) -> float:
        result = await self.db.execute(
            select(func.avg(QuizAttempt.percentage))
            .where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.deleted_at.is_(None),
            )
        )
        avg = result.scalar_one_or_none()
        return float(avg) if avg else 0.0


class QuizAnswerRepository(BaseRepository[QuizAnswer]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(QuizAnswer, db)

    async def get_by_attempt(self, attempt_id: uuid.UUID) -> list[QuizAnswer]:
        result = await self.db.execute(
            select(QuizAnswer)
            .where(
                QuizAnswer.attempt_id == attempt_id,
                QuizAnswer.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
