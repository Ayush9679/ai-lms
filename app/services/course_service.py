"""
AI-LMS Course Service — course CRUD, publishing, and thumbnail management.
"""

import uuid
from typing import Any

from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.course import Course, CourseStatus
from app.models.user import UserRole
from app.repositories.course_repo import CourseRepository
from app.repositories.enrollment_repo import EnrollmentRepository
from app.repositories.lesson_repo import LessonRepository
from app.schemas.course import (
    CreateCourseRequest,
    UpdateCourseRequest,
)

logger = get_logger(__name__)


class CourseService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = CourseRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.lesson_repo = LessonRepository(db)

    async def _generate_unique_slug(self, title: str, exclude_id: uuid.UUID | None = None) -> str:
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while await self.repo.slug_exists(slug):
            # If we're updating, check if the existing slug belongs to this course
            if exclude_id:
                existing = await self.repo.get_by_slug(slug)
                if existing and existing.id == exclude_id:
                    break
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    async def _build_course_response(self, course: Course) -> dict[str, Any]:
        """Build a CourseResponse dict with computed counts."""
        total_lessons = await self.lesson_repo.count_by_course(course.id)
        total_students = await self.enrollment_repo.count_by_course(course.id)
        return {
            **{c.key: getattr(course, c.key) for c in course.__table__.columns},
            "instructor": course.instructor,
            "total_lessons": total_lessons,
            "total_students": total_students,
        }

    async def create_course(self, instructor_id: uuid.UUID, request: CreateCourseRequest) -> Course:
        slug = await self._generate_unique_slug(request.title)
        course = await self.repo.create(
            title=request.title,
            slug=slug,
            description=request.description,
            category=request.category,
            level=request.level,
            tags=request.tags,
            instructor_id=instructor_id,
            status=CourseStatus.draft,
        )
        logger.info("Course created", extra={"course_id": str(course.id)})
        return course

    async def get_course(self, course_id: uuid.UUID) -> Course:
        course = await self.repo.get_by_id(course_id)
        if not course:
            raise NotFoundError("Course", str(course_id))
        return course

    async def get_manageable_course(
        self,
        course_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
    ) -> Course:
        course = await self.get_course(course_id)
        if requester_role != UserRole.admin and course.instructor_id != requester_id:
            raise ForbiddenError("You can only manage your own courses")
        return course

    async def get_course_by_slug(self, slug: str) -> Course:
        course = await self.repo.get_by_slug(slug)
        if not course:
            raise NotFoundError("Course", slug)
        return course

    async def update_course(
        self,
        course_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        request: UpdateCourseRequest,
    ) -> Course:
        course = await self.get_manageable_course(course_id, requester_id, requester_role)

        update_data = request.model_dump(exclude_unset=True, exclude_none=True)

        if update_data.get("status") == CourseStatus.published:
            requirements = await self.get_publish_requirements(
                course, title=update_data.get("title", course.title)
            )
            if requirements:
                raise ValidationError("Cannot publish course: " + " ".join(requirements))

        # Re-slug if title changed
        if "title" in update_data:
            update_data["slug"] = await self._generate_unique_slug(
                update_data["title"], exclude_id=course_id
            )

        return await self.repo.update(course, **update_data)

    async def get_publish_requirements(self, course: Course, title: str | None = None) -> list[str]:
        """Return actionable unmet publishing requirements for a course."""
        requirements = []
        effective_title = course.title if title is None else title
        if not effective_title or not effective_title.strip():
            requirements.append("Add a nonempty course title.")
        if not course.thumbnail or not course.thumbnail.strip():
            requirements.append("Upload a course thumbnail.")
        if await self.lesson_repo.count_ready_video_by_course(course.id) < 1:
            requirements.append("Upload and verify video for at least one lesson.")
        return requirements

    async def delete_course(
        self, course_id: uuid.UUID, requester_id: uuid.UUID, requester_role: UserRole
    ) -> None:
        course = await self.get_manageable_course(course_id, requester_id, requester_role)
        await self.repo.soft_delete(course)
        logger.info("Course deleted", extra={"course_id": str(course_id)})

    async def set_thumbnail(
        self,
        course: Course,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        thumbnail_url: str,
    ) -> Course:
        if requester_role != UserRole.admin and course.instructor_id != requester_id:
            raise ForbiddenError("You can only manage your own courses")
        return await self.repo.update(course, thumbnail=thumbnail_url)

    async def list_published_courses(self, skip: int = 0, limit: int = 20) -> list[Course]:
        return await self.repo.get_published(skip, limit)

    async def list_teacher_courses(
        self, instructor_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[Course]:
        return await self.repo.get_by_instructor(instructor_id, skip, limit)

    async def search_courses(
        self,
        query: str | None,
        category: str | None,
        level: Any,
        status: Any,
        skip: int,
        limit: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Course], int]:
        return await self.repo.search(
            query=query,
            category=category,
            level=level,
            status=status,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_total_lessons(self, course_id: uuid.UUID) -> int:
        return await self.lesson_repo.count_by_course(course_id)

    async def get_total_students(self, course_id: uuid.UUID) -> int:
        return await self.enrollment_repo.count_by_course(course_id)
