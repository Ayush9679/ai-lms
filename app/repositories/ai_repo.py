"""
AI-LMS AI Repository — database access for chat sessions, notes, study plans, flashcards.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_chat import (
    AIChatMessage,
    AIChatSession,
    FlashcardSet,
    GeneratedNote,
    StudyPlan,
)
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[AIChatSession]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AIChatSession, db)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[AIChatSession]:
        result = await self.db.execute(
            select(AIChatSession)
            .where(
                AIChatSession.user_id == user_id,
                AIChatSession.deleted_at.is_(None),
            )
            .order_by(AIChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class ChatMessageRepository(BaseRepository[AIChatMessage]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AIChatMessage, db)

    async def get_by_session(self, session_id: uuid.UUID) -> list[AIChatMessage]:
        result = await self.db.execute(
            select(AIChatMessage)
            .where(
                AIChatMessage.session_id == session_id,
                AIChatMessage.deleted_at.is_(None),
            )
            .order_by(AIChatMessage.created_at.asc())
        )
        return list(result.scalars().all())


class GeneratedNoteRepository(BaseRepository[GeneratedNote]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(GeneratedNote, db)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[GeneratedNote]:
        result = await self.db.execute(
            select(GeneratedNote)
            .where(
                GeneratedNote.user_id == user_id,
                GeneratedNote.deleted_at.is_(None),
            )
            .order_by(GeneratedNote.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class StudyPlanRepository(BaseRepository[StudyPlan]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(StudyPlan, db)

    async def get_active_by_user(self, user_id: uuid.UUID) -> list[StudyPlan]:
        result = await self.db.execute(
            select(StudyPlan)
            .where(
                StudyPlan.user_id == user_id,
                StudyPlan.is_active.is_(True),
                StudyPlan.deleted_at.is_(None),
            )
            .order_by(StudyPlan.created_at.desc())
        )
        return list(result.scalars().all())


class FlashcardSetRepository(BaseRepository[FlashcardSet]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(FlashcardSet, db)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[FlashcardSet]:
        result = await self.db.execute(
            select(FlashcardSet)
            .where(
                FlashcardSet.user_id == user_id,
                FlashcardSet.deleted_at.is_(None),
            )
            .order_by(FlashcardSet.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
