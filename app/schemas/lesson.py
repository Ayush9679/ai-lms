"""
AI-LMS Lesson Schemas — lesson CRUD and progress tracking.
"""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema


class CreateLessonRequest(BaseSchema):
    """Teacher creates a new lesson in a course."""

    title: str = Field(min_length=2, max_length=500, examples=["Variables and Data Types"])
    content: str | None = Field(default=None, max_length=100000)
    video_url: str | None = Field(default=None, max_length=1000)
    pdf_url: str | None = Field(default=None, max_length=1000)
    transcript: str | None = Field(default=None, max_length=200000)
    duration_minutes: int | None = Field(default=None, ge=1, le=600)
    order_index: int = Field(default=0, ge=0)
    is_published: bool = False


class UpdateLessonRequest(BaseSchema):
    """Teacher updates an existing lesson."""

    title: str | None = Field(default=None, min_length=2, max_length=500)
    content: str | None = None
    video_url: str | None = None
    pdf_url: str | None = None
    transcript: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=600)
    order_index: int | None = Field(default=None, ge=0)
    is_published: bool | None = None


class LessonResponse(BaseSchema):
    """Full lesson details."""

    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    thumbnail: str | None = None
    content: str | None
    video_url: str | None
    video_status: str = "pending"
    video_size_bytes: int | None = None
    pdf_url: str | None
    transcript: str | None
    duration_minutes: int | None
    order_index: int
    is_published: bool
    created_at: datetime
    updated_at: datetime


class LessonSummary(BaseSchema):
    """Compact lesson info for course overview."""

    id: uuid.UUID
    title: str
    duration_minutes: int | None
    order_index: int
    is_published: bool
    video_status: str = "pending"
    has_video: bool
    has_pdf: bool


class LessonProgressUpdate(BaseSchema):
    """Student updates their progress on a lesson."""

    watch_time_seconds: int = Field(default=0, ge=0)
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    is_completed: bool = False


class LessonProgressResponse(BaseSchema):
    """A student's progress record for a lesson."""

    id: uuid.UUID
    lesson_id: uuid.UUID
    user_id: uuid.UUID
    is_completed: bool
    watch_time_seconds: int
    completion_percentage: float
    updated_at: datetime
