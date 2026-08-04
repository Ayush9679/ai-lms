"""
AI-LMS Course Schemas — course CRUD, file attachments, and search.
"""
import uuid
from datetime import datetime

from pydantic import Field, field_validator

from app.models.course import CourseLevel, CourseStatus, FileType
from app.schemas.common import BaseSchema
from app.schemas.user import UserSummary


class CreateCourseRequest(BaseSchema):
    """Teacher creates a new course."""
    title: str = Field(min_length=3, max_length=500, examples=["Introduction to Python"])
    description: str | None = Field(default=None, max_length=10000)
    category: str | None = Field(default=None, max_length=100, examples=["Programming"])
    level: CourseLevel = Field(default=CourseLevel.beginner)
    tags: str | None = Field(default=None, max_length=1000, examples=["python,beginner,programming"])


class UpdateCourseRequest(BaseSchema):
    """Teacher updates an existing course."""
    title: str | None = Field(default=None, min_length=3, max_length=500)
    description: str | None = Field(default=None, max_length=10000)
    category: str | None = Field(default=None, max_length=100)
    level: CourseLevel | None = None
    status: CourseStatus | None = None
    tags: str | None = None


class CourseFileResponse(BaseSchema):
    """A file attached to a course."""
    id: uuid.UUID
    file_name: str
    original_name: str
    file_path: str
    file_type: FileType
    mime_type: str
    size_bytes: int
    created_at: datetime


class CourseResponse(BaseSchema):
    """Full course details."""
    id: uuid.UUID
    title: str
    slug: str
    description: str | None
    category: str | None
    level: CourseLevel
    status: CourseStatus
    thumbnail: str | None
    price: float
    tags: str | None
    instructor: UserSummary
    instructor_id: uuid.UUID
    total_lessons: int = 0
    total_students: int = 0
    created_at: datetime
    updated_at: datetime


class CourseSummary(BaseSchema):
    """Compact course info for lists and search results."""
    id: uuid.UUID
    title: str
    slug: str
    description: str | None
    category: str | None
    level: CourseLevel
    status: CourseStatus
    thumbnail: str | None
    price: float
    instructor_name: str
    total_lessons: int = 0
    total_students: int = 0
    created_at: datetime


class CourseSearchParams(BaseSchema):
    """Validated query parameters for course search."""
    q: str | None = Field(default=None, description="Search query")
    category: str | None = None
    level: CourseLevel | None = None
    status: CourseStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at", examples=["created_at", "title", "total_students"])
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
