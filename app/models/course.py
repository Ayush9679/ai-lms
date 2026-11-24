"""
AI-LMS Course Models — Courses and uploaded course files.
"""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDBase


class CourseLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class CourseStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class FileType(str, enum.Enum):
    image = "image"
    video = "video"
    document = "document"
    assignment = "assignment"
    other = "other"


class Course(UUIDBase):
    """
    A course created by a teacher/instructor.
    Contains lessons, quizzes, assignments, and enrolled students.
    """
    __tablename__ = "courses"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(600), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    level: Mapped[CourseLevel] = mapped_column(
        Enum(CourseLevel, name="course_level"),
        default=CourseLevel.beginner,
        nullable=False,
    )
    status: Mapped[CourseStatus] = mapped_column(
        Enum(CourseStatus, name="course_status"),
        default=CourseStatus.draft,
        nullable=False,
        index=True,
    )
    thumbnail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_upload_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    file_upload_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), default="INR", server_default="INR", nullable=False
    )
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tags: Mapped[str | None] = mapped_column(String(1000), nullable=True)  # JSON string

    # Relationships
    instructor: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="courses_taught", lazy="selectin"
    )
    lessons: Mapped[list["Lesson"]] = relationship(  # type: ignore[name-defined]
        "Lesson",
        back_populates="course",
        order_by="Lesson.order_index",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(  # type: ignore[name-defined]
        "Enrollment", back_populates="course", lazy="selectin", cascade="all, delete-orphan"
    )
    quizzes: Mapped[list["Quiz"]] = relationship(  # type: ignore[name-defined]
        "Quiz", back_populates="course", lazy="selectin", cascade="all, delete-orphan"
    )
    assignments: Mapped[list["Assignment"]] = relationship(  # type: ignore[name-defined]
        "Assignment", back_populates="course", lazy="selectin", cascade="all, delete-orphan"
    )
    files: Mapped[list["CourseFile"]] = relationship(  # type: ignore[name-defined]
        "CourseFile", back_populates="course", lazy="selectin", cascade="all, delete-orphan"
    )


class CourseFile(UUIDBase):
    """Files uploaded to a course (PDFs, videos, images)."""
    __tablename__ = "course_files"
    __table_args__ = (Index("uq_course_files_upload_id", "upload_id", unique=True),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    upload_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType, name="file_type"), nullable=False
    )
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    course: Mapped[Course] = relationship("Course", back_populates="files")
