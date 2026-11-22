"""
AI-LMS Course Repository — database access for courses and course files.
"""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course, CourseFile, CourseLevel, CourseStatus
from app.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Course, db)

    async def get_by_slug(self, slug: str) -> Course | None:
        result = await self.db.execute(
            select(Course).where(Course.slug == slug, Course.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        course = await self.get_by_slug(slug)
        return course is not None

    async def get_published(self, skip: int = 0, limit: int = 20) -> list[Course]:
        result = await self.db.execute(
            select(Course)
            .where(
                Course.status == CourseStatus.published,
                Course.deleted_at.is_(None),
            )
            .order_by(Course.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_instructor(
        self, instructor_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[Course]:
        result = await self.db.execute(
            select(Course)
            .where(
                Course.instructor_id == instructor_id,
                Course.deleted_at.is_(None),
            )
            .order_by(Course.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        query: str | None = None,
        category: str | None = None,
        level: CourseLevel | None = None,
        status: CourseStatus | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Course], int]:
        """Full-text search with filters. Returns (items, total)."""
        base_query = select(Course).where(Course.deleted_at.is_(None))

        if query:
            base_query = base_query.where(
                or_(
                    Course.title.ilike(f"%{query}%"),
                    Course.description.ilike(f"%{query}%"),
                    Course.tags.ilike(f"%{query}%"),
                    Course.category.ilike(f"%{query}%"),
                )
            )
        if category:
            base_query = base_query.where(Course.category.ilike(f"%{category}%"))
        if level:
            base_query = base_query.where(Course.level == level)
        if status:
            base_query = base_query.where(Course.status == status)
        else:
            base_query = base_query.where(Course.status == CourseStatus.published)

        count_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        sort_col = getattr(Course, sort_by, Course.created_at)
        if sort_order == "desc":
            sort_col = sort_col.desc()
        else:
            sort_col = sort_col.asc()

        result = await self.db.execute(base_query.order_by(sort_col).offset(skip).limit(limit))
        return list(result.scalars().all()), total

    async def count_by_instructor(self, instructor_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Course)
            .where(Course.instructor_id == instructor_id, Course.deleted_at.is_(None))
        )
        return result.scalar_one()


class CourseFileRepository(BaseRepository[CourseFile]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(CourseFile, db)

    async def get_by_course(self, course_id: uuid.UUID) -> list[CourseFile]:
        result = await self.db.execute(
            select(CourseFile).where(
                CourseFile.course_id == course_id,
                CourseFile.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
