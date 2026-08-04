"""
AI-LMS AI Schemas — requests and responses for all AI features.
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.quiz import DifficultyLevel, QuestionType
from app.schemas.common import BaseSchema


# =============================================================================
# AI Tutor Chat
# =============================================================================

class ChatMessageRequest(BaseSchema):
    """Send a message to the AI tutor."""
    message: str = Field(min_length=1, max_length=10000, examples=["Explain recursion to me"])
    session_id: uuid.UUID | None = Field(
        default=None, description="Existing session ID; omit to create a new session"
    )
    course_id: uuid.UUID | None = Field(
        default=None, description="Optional course context for the AI"
    )


class ChatMessageResponse(BaseSchema):
    """AI tutor response to a chat message."""
    session_id: uuid.UUID
    session_title: str
    user_message: str
    ai_response: str
    message_count: int


class ChatSessionSummary(BaseSchema):
    """Compact chat session for listing."""
    id: uuid.UUID
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ChatHistoryResponse(BaseSchema):
    """Full chat session with all messages."""
    id: uuid.UUID
    title: str
    message_count: int
    messages: list[dict]
    created_at: datetime


# =============================================================================
# Notes Generation
# =============================================================================

class GenerateNotesRequest(BaseSchema):
    """Generate structured notes from a source."""
    source_type: str = Field(examples=["lesson", "pdf_text", "text"])
    source_id: uuid.UUID | None = Field(
        default=None, description="Lesson ID or Course ID"
    )
    source_text: str | None = Field(
        default=None,
        max_length=200000,
        description="Raw text to generate notes from",
    )
    title: str | None = None


class GenerateNotesResponse(BaseSchema):
    """AI-generated structured notes."""
    id: uuid.UUID
    title: str
    source_type: str
    content: str
    summary: str | None
    created_at: datetime


# =============================================================================
# Summarization
# =============================================================================

class SummarizeRequest(BaseSchema):
    """Summarize a lesson, PDF text, or custom text."""
    source_type: str = Field(examples=["lesson", "text"])
    source_id: uuid.UUID | None = None
    source_text: str | None = Field(default=None, max_length=200000)
    length: str = Field(default="medium", pattern="^(short|medium|long)$")


class SummarizeResponse(BaseSchema):
    """Summarization result."""
    summary: str
    key_points: list[str]
    source_type: str


# =============================================================================
# Flashcard Generation
# =============================================================================

class GenerateFlashcardsRequest(BaseSchema):
    """Generate flashcards from a lesson or text."""
    source_type: str = Field(examples=["lesson", "text"])
    source_id: uuid.UUID | None = None
    source_text: str | None = Field(default=None, max_length=200000)
    num_cards: int = Field(default=15, ge=5, le=50)
    title: str | None = None


class Flashcard(BaseSchema):
    """A single flashcard with front (question) and back (answer)."""
    front: str
    back: str


class FlashcardSetResponse(BaseSchema):
    """Generated flashcard set."""
    id: uuid.UUID
    title: str
    cards: list[Flashcard]
    card_count: int
    created_at: datetime


# =============================================================================
# Study Planner
# =============================================================================

class GenerateStudyPlanRequest(BaseSchema):
    """Generate a personalized study plan."""
    course_id: uuid.UUID | None = None
    topics: list[str] | None = Field(
        default=None, description="Specific topics to include in the plan"
    )
    duration_weeks: int = Field(default=4, ge=1, le=52)
    hours_per_day: int = Field(default=2, ge=1, le=12)
    goals: str | None = Field(
        default=None, max_length=1000, description="Student's learning goals"
    )


class StudyPlanResponse(BaseSchema):
    """AI-generated personalized study plan."""
    id: uuid.UUID
    title: str
    duration_weeks: int
    plan_data: dict
    is_active: bool
    created_at: datetime


# =============================================================================
# Learning Recommendations
# =============================================================================

class RecommendationResponse(BaseSchema):
    """AI-generated learning recommendations."""
    next_lessons: list[dict]
    weak_topics: list[str]
    practice_suggestions: list[str]
    recommended_courses: list[dict]
    message: str


# =============================================================================
# AI Quiz Generation (referenced from quiz schemas too)
# =============================================================================

class AIQuizGenerationResult(BaseSchema):
    """Result of AI quiz generation — the created quiz ID."""
    quiz_id: uuid.UUID
    title: str
    question_count: int
    difficulty: DifficultyLevel
    is_ai_generated: bool = True
