"""
AI-LMS Search Router — unified course and lesson search with filtering.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.course import CourseSummary
from app.services.course_service import CourseService

router = APIRouter()


@router.get(
    "/courses",
    response_model=PaginatedResponse[CourseSummary],
    summary="Search courses",
    description="Full-text search across course titles, descriptions, tags, and categories. Supports filtering by level, pagination, and sorting.",
)
async def search_courses(
    q: str | None = Query(default=None, description="Search term"),
    category: str | None = Query(default=None),
    level: str | None = Query(default=None, description="beginner|intermediate|advanced"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at", description="created_at|title|price"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> PaginatedResponse[CourseSummary]:
    svc = CourseService(db)
    skip = (page - 1) * page_size
    courses, total = await svc.search_courses(
        query=q,
        category=category,
        level=level,
        status=None,
        skip=skip,
        limit=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    items = [
        CourseSummary(
            id=c.id,
            title=c.title,
            slug=c.slug,
            description=c.description,
            category=c.category,
            level=c.level,
            status=c.status,
            thumbnail=c.thumbnail,
            price=float(c.price),
            instructor_name=c.instructor.full_name if c.instructor else "Unknown",
            total_lessons=0,
            total_students=0,
            created_at=c.created_at,
        )
        for c in courses
    ]
    return PaginatedResponse.create(items, total, page, page_size)
