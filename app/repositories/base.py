"""
AI-LMS Base Repository — generic CRUD operations for SQLAlchemy 2.0 async.
"""
import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import UUIDBase

ModelT = TypeVar("ModelT", bound=UUIDBase)


class BaseRepository(Generic[ModelT]):
    """
    Generic async repository with common CRUD operations.
    All repositories inherit from this and call super().__init__(model, db).
    """

    def __init__(self, model: type[ModelT], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, id: uuid.UUID | str) -> ModelT | None:
        """Fetch a record by UUID, excluding soft-deleted."""
        if isinstance(id, str):
            try:
                id = uuid.UUID(id)
            except ValueError:
                return None
        result = await self.db.execute(
            select(self.model).where(
                self.model.id == id,
                self.model.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: list[Any] | None = None,
    ) -> list[ModelT]:
        """Fetch a paginated list with optional filters, excluding soft-deleted."""
        query = select(self.model).where(self.model.deleted_at.is_(None))
        if filters:
            query = query.where(*filters)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: list[Any] | None = None) -> int:
        """Count records with optional filters, excluding soft-deleted."""
        query = select(func.count()).select_from(self.model).where(
            self.model.deleted_at.is_(None)
        )
        if filters:
            query = query.where(*filters)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, **kwargs: Any) -> ModelT:
        """Create and persist a new record."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelT, **kwargs: Any) -> ModelT:
        """Update fields on an existing record."""
        for field, value in kwargs.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def soft_delete(self, instance: ModelT) -> ModelT:
        """Mark a record as deleted (soft delete)."""
        instance.soft_delete()
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def hard_delete(self, instance: ModelT) -> None:
        """Permanently remove a record from the database."""
        await self.db.delete(instance)
        await self.db.flush()
