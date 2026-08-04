"""
AI-LMS User Models — User accounts with RBAC roles.
"""
import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDBase


class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class User(UUIDBase):
    """
    Core user account. Supports student, teacher, and admin roles.
    Email verification and password reset are handled via token models.
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.student, nullable=False
    )
    profile_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    courses_taught: Mapped[list["Course"]] = relationship(  # type: ignore[name-defined]
        "Course",
        back_populates="instructor",
        foreign_keys="Course.instructor_id",
        lazy="selectin",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(  # type: ignore[name-defined]
        "Enrollment", back_populates="student", lazy="selectin"
    )
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(  # type: ignore[name-defined]
        "QuizAttempt", back_populates="student", lazy="selectin"
    )
    submissions: Mapped[list["AssignmentSubmission"]] = relationship(  # type: ignore[name-defined]
        "AssignmentSubmission",
        back_populates="student",
        foreign_keys="AssignmentSubmission.student_id",
        lazy="selectin",
    )
    chat_sessions: Mapped[list["AIChatSession"]] = relationship(  # type: ignore[name-defined]
        "AIChatSession", back_populates="user", lazy="selectin"
    )
    generated_notes: Mapped[list["GeneratedNote"]] = relationship(  # type: ignore[name-defined]
        "GeneratedNote", back_populates="user", lazy="selectin"
    )
    study_plans: Mapped[list["StudyPlan"]] = relationship(  # type: ignore[name-defined]
        "StudyPlan", back_populates="user", lazy="selectin"
    )
    lesson_progress: Mapped[list["LessonProgress"]] = relationship(  # type: ignore[name-defined]
        "LessonProgress", back_populates="user", lazy="selectin"
    )
    flashcard_sets: Mapped[list["FlashcardSet"]] = relationship(  # type: ignore[name-defined]
        "FlashcardSet", back_populates="user", lazy="selectin"
    )


class EmailVerification(UUIDBase):
    """Email verification tokens (24-hour expiry)."""
    __tablename__ = "email_verifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])


class PasswordReset(UUIDBase):
    """Password reset tokens (1-hour expiry)."""
    __tablename__ = "password_resets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
