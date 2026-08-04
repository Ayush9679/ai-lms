"""
AI-LMS Analytics Models — User activity and course-level analytics.
"""
import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDBase


class UserActivity(UUIDBase):
    """
    Records every significant user action for analytics.
    Examples: lesson_view, quiz_attempt, enrollment, ai_chat.
    """
    __tablename__ = "user_activities"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    activity_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])  # type: ignore[name-defined]


class CourseAnalytics(UUIDBase):
    """
    Aggregated analytics snapshot for a course.
    Updated periodically by a background job or on-demand.
    """
    __tablename__ = "course_analytics"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_enrollments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_students: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_students: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_quiz_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_quiz_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_assignments_submitted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    course: Mapped["Course"] = relationship("Course", foreign_keys=[course_id])  # type: ignore[name-defined]
