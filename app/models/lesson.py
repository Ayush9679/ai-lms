"""
AI-LMS Lesson Models — Lessons and per-student progress tracking.
"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDBase


class Lesson(UUIDBase):
    """
    A single lesson within a course.
    Supports text content, video URL, and PDF attachments.
    """
    __tablename__ = "lessons"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_upload_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    video_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    video_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    video_upload_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    pdf_upload_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    course: Mapped["Course"] = relationship(  # type: ignore[name-defined]
        "Course", back_populates="lessons"
    )
    progress_records: Mapped[list["LessonProgress"]] = relationship(
        "LessonProgress", back_populates="lesson", cascade="all, delete-orphan", lazy="selectin"
    )


class LessonProgress(UUIDBase):
    """
    Tracks per-student progress on each lesson.
    Used to calculate course completion percentage.
    """
    __tablename__ = "lesson_progress"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    watch_time_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    lesson: Mapped[Lesson] = relationship("Lesson", back_populates="progress_records")
    user: Mapped["User"] = relationship("User", back_populates="lesson_progress")  # type: ignore[name-defined]
