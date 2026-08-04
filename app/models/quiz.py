"""
AI-LMS Quiz Models — Quizzes, Questions, Attempts, and Answers.
Supports MCQ, True/False, and Subjective question types.
"""
import enum
import uuid
from typing import Any

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import UUIDBase


class QuestionType(str, enum.Enum):
    mcq = "mcq"
    true_false = "true_false"
    subjective = "subjective"


class DifficultyLevel(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class Quiz(UUIDBase):
    """
    A quiz attached to a course, containing one or more questions.
    Supports negative marking and a configurable passing score.
    """
    __tablename__ = "quizzes"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level"),
        default=DifficultyLevel.medium,
        nullable=False,
    )
    passing_score: Mapped[float] = mapped_column(Float, default=60.0, nullable=False)
    negative_marking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    negative_marks_per_wrong: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 = unlimited

    course: Mapped["Course"] = relationship("Course", back_populates="quizzes")  # type: ignore[name-defined]
    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="quiz", cascade="all, delete-orphan",
        order_by="Question.order_index", lazy="selectin"
    )
    attempts: Mapped[list["QuizAttempt"]] = relationship(
        "QuizAttempt", back_populates="quiz", cascade="all, delete-orphan", lazy="selectin"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])  # type: ignore[name-defined]


class Question(UUIDBase):
    """
    A single question within a quiz.
    For MCQ, options are stored as a JSON list of dicts: [{text, is_correct}].
    For True/False, options are implicitly ["True", "False"].
    """
    __tablename__ = "questions"

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type"), nullable=False
    )
    options: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    marks: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    quiz: Mapped[Quiz] = relationship("Quiz", back_populates="questions")
    answers: Mapped[list["QuizAnswer"]] = relationship(
        "QuizAnswer", back_populates="question", cascade="all, delete-orphan"
    )


class QuizAttempt(UUIDBase):
    """Records a student's attempt at a quiz, including score and pass/fail."""
    __tablename__ = "quiz_attempts"

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    time_taken_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    quiz: Mapped[Quiz] = relationship("Quiz", back_populates="attempts")
    student: Mapped["User"] = relationship("User", back_populates="quiz_attempts")  # type: ignore[name-defined]
    answers: Mapped[list["QuizAnswer"]] = relationship(
        "QuizAnswer", back_populates="attempt", cascade="all, delete-orphan", lazy="selectin"
    )


class QuizAnswer(UUIDBase):
    """Stores a student's answer to a single question within an attempt."""
    __tablename__ = "quiz_answers"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    given_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    marks_awarded: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    attempt: Mapped[QuizAttempt] = relationship("QuizAttempt", back_populates="answers")
    question: Mapped[Question] = relationship("Question", back_populates="answers")
