"""
AI-LMS Enrollment Model — Student-to-course relationships with progress.
"""
import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDBase


class EnrollmentStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    dropped = "dropped"
    pending = "pending"


class Enrollment(UUIDBase):
    """
    Records a student's enrollment in a course.
    Tracks overall progress (0.0–100.0) and status.
    """
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus, name="enrollment_status"),
        default=EnrollmentStatus.active,
        nullable=False,
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completed_lessons: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    student: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="enrollments"
    )
    course: Mapped["Course"] = relationship(  # type: ignore[name-defined]
        "Course", back_populates="enrollments"
    )
