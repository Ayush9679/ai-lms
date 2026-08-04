"""
AI-LMS Quiz Schemas — quiz CRUD, questions, attempts, and scoring.
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from app.models.quiz import DifficultyLevel, QuestionType
from app.schemas.common import BaseSchema


# =============================================================================
# Question Schemas
# =============================================================================

class MCQOption(BaseSchema):
    """A single option in an MCQ question."""
    text: str = Field(min_length=1, max_length=500)
    is_correct: bool = False


class CreateQuestionRequest(BaseSchema):
    """Create a question within a quiz."""
    question_text: str = Field(min_length=5, max_length=5000)
    question_type: QuestionType
    options: list[MCQOption] | None = None  # MCQ only
    correct_answer: str | None = None       # True/False and Subjective
    explanation: str | None = None
    marks: float = Field(default=1.0, ge=0.1, le=100.0)
    order_index: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_question_type(self) -> "CreateQuestionRequest":
        if self.question_type == QuestionType.mcq:
            if not self.options or len(self.options) < 2:
                raise ValueError("MCQ questions require at least 2 options")
            if not any(opt.is_correct for opt in self.options):
                raise ValueError("At least one MCQ option must be marked correct")
        if self.question_type == QuestionType.true_false:
            if self.correct_answer not in ("True", "False"):
                raise ValueError("True/False answer must be 'True' or 'False'")
        return self


class QuestionResponse(BaseSchema):
    """Full question details (excludes correct_answer for student-facing calls)."""
    id: uuid.UUID
    quiz_id: uuid.UUID
    question_text: str
    question_type: QuestionType
    options: list[dict] | None
    explanation: str | None
    marks: float
    order_index: int


class QuestionWithAnswer(QuestionResponse):
    """Question with correct answer — only for teachers/post-attempt review."""
    correct_answer: str | None


# =============================================================================
# Quiz Schemas
# =============================================================================

class CreateQuizRequest(BaseSchema):
    """Teacher creates a quiz manually."""
    title: str = Field(min_length=3, max_length=500)
    description: str | None = None
    difficulty: DifficultyLevel = DifficultyLevel.medium
    passing_score: float = Field(default=60.0, ge=0.0, le=100.0)
    negative_marking: bool = False
    negative_marks_per_wrong: float = Field(default=0.25, ge=0.0, le=5.0)
    time_limit_minutes: int | None = Field(default=None, ge=5, le=300)
    max_attempts: int = Field(default=0, ge=0)  # 0 = unlimited
    questions: list[CreateQuestionRequest] = Field(default_factory=list)


class GenerateQuizRequest(BaseSchema):
    """AI generates a quiz from a source."""
    source_type: str = Field(examples=["lesson", "pdf", "course", "text"])
    source_id: uuid.UUID | None = None        # lesson_id or course_id
    source_text: str | None = None            # raw text input
    num_questions: int = Field(default=10, ge=3, le=50)
    difficulty: DifficultyLevel = DifficultyLevel.medium
    question_types: list[QuestionType] = Field(
        default_factory=lambda: [QuestionType.mcq, QuestionType.true_false]
    )
    title: str | None = None


class UpdateQuizRequest(BaseSchema):
    """Update quiz metadata."""
    title: str | None = Field(default=None, min_length=3, max_length=500)
    description: str | None = None
    difficulty: DifficultyLevel | None = None
    passing_score: float | None = Field(default=None, ge=0.0, le=100.0)
    negative_marking: bool | None = None
    time_limit_minutes: int | None = None
    max_attempts: int | None = None
    questions: list[CreateQuestionRequest] | None = None


class QuizResponse(BaseSchema):
    """Full quiz details with questions (no correct answers for students)."""
    id: uuid.UUID
    course_id: uuid.UUID
    lesson_id: uuid.UUID | None
    created_by: uuid.UUID
    title: str
    description: str | None
    difficulty: DifficultyLevel
    passing_score: float
    negative_marking: bool
    time_limit_minutes: int | None
    max_attempts: int
    is_ai_generated: bool
    question_count: int
    questions: list[QuestionResponse]
    created_at: datetime


class QuizSummary(BaseSchema):
    """Compact quiz info for listing."""
    id: uuid.UUID
    title: str
    difficulty: DifficultyLevel
    passing_score: float
    question_count: int
    time_limit_minutes: int | None
    is_ai_generated: bool
    created_at: datetime


# =============================================================================
# Attempt Schemas
# =============================================================================

class SubmitAnswerRequest(BaseSchema):
    """A student's answer to a single question."""
    question_id: uuid.UUID
    given_answer: str | None = None


class SubmitAttemptRequest(BaseSchema):
    """Student submits a completed quiz attempt."""
    answers: list[SubmitAnswerRequest]
    time_taken_seconds: int | None = Field(default=None, ge=0)


class QuizAnswerResponse(BaseSchema):
    """Result of a single answer after grading."""
    question_id: uuid.UUID
    given_answer: str | None
    correct_answer: str | None
    is_correct: bool | None
    marks_awarded: float
    explanation: str | None


class QuizAttemptResponse(BaseSchema):
    """Full attempt result with score breakdown."""
    id: uuid.UUID
    quiz_id: uuid.UUID
    student_id: uuid.UUID
    score: float
    max_score: float
    percentage: float
    passed: bool
    time_taken_seconds: int | None
    attempt_number: int
    answers: list[QuizAnswerResponse]
    created_at: datetime


class QuizAttemptSummary(BaseSchema):
    """Compact attempt info for history."""
    id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_title: str
    score: float
    percentage: float
    passed: bool
    attempt_number: int
    created_at: datetime
