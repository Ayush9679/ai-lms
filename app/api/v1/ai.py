"""
AI-LMS AI Router — tutor chat, notes, summaries, flashcards, study plans, recommendations.
All endpoints require authentication. AI endpoints have stricter rate limits.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.middleware.rate_limit import ai_limit, limiter
from app.models.user import User
from app.schemas.ai import (
    ChatHistoryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionSummary,
    FlashcardSetResponse,
    GenerateFlashcardsRequest,
    GenerateNotesRequest,
    GenerateNotesResponse,
    GenerateStudyPlanRequest,
    RecommendationResponse,
    StudyPlanResponse,
    SummarizeRequest,
    SummarizeResponse,
    Flashcard,
)
from app.schemas.common import MessageResponse
from app.ai.ai_service import AIService

router = APIRouter()


# =============================================================================
# AI Tutor Chat
# =============================================================================

@router.post(
    "/chat",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with AI tutor",
    description="Send a message to the AI tutor. Context-aware within a session.",
)
@limiter.limit(ai_limit)
async def chat(
    request: Request,
    body: ChatMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatMessageResponse:
    svc = AIService(db)
    result = await svc.chat(
        user_id=current_user.id,
        message=body.message,
        session_id=body.session_id,
        course_id=body.course_id,
    )
    return ChatMessageResponse(**result)


@router.get(
    "/chat/sessions",
    response_model=list[ChatSessionSummary],
    summary="List AI chat sessions",
)
async def list_chat_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChatSessionSummary]:
    svc = AIService(db)
    sessions = await svc.get_chat_sessions(current_user.id)
    return [
        ChatSessionSummary(
            id=s.id,
            title=s.title,
            message_count=s.message_count,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.get(
    "/chat/sessions/{session_id}",
    response_model=ChatHistoryResponse,
    summary="Get full chat session history",
)
async def get_chat_history(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatHistoryResponse:
    svc = AIService(db)
    history = await svc.get_chat_history(current_user.id, session_id)
    return ChatHistoryResponse(**history)


@router.delete(
    "/chat/sessions/{session_id}",
    response_model=MessageResponse,
    summary="Delete a chat session",
)
async def delete_chat_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = AIService(db)
    await svc.delete_chat_session(current_user.id, session_id)
    return MessageResponse(message="Chat session deleted successfully")


# =============================================================================
# Notes Generation
# =============================================================================

@router.post(
    "/notes/generate",
    response_model=GenerateNotesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate structured notes from a lesson or text",
    description="AI generates comprehensive, structured study notes. Provide either source_id (lesson) or source_text.",
)
@limiter.limit(ai_limit)
async def generate_notes(
    request: Request,
    body: GenerateNotesRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GenerateNotesResponse:
    svc = AIService(db)
    note = await svc.generate_notes(
        user_id=current_user.id,
        source_type=body.source_type,
        source_id=body.source_id,
        source_text=body.source_text,
        title=body.title,
    )
    return GenerateNotesResponse(
        id=note.id,
        title=note.title,
        source_type=note.source_type,
        content=note.content,
        summary=note.summary,
        created_at=note.created_at,
    )


@router.get(
    "/notes",
    response_model=list[GenerateNotesResponse],
    summary="List my generated notes",
)
async def list_notes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[GenerateNotesResponse]:
    svc = AIService(db)
    notes = await svc.get_user_notes(current_user.id)
    return [
        GenerateNotesResponse(
            id=n.id, title=n.title, source_type=n.source_type,
            content=n.content, summary=n.summary, created_at=n.created_at,
        )
        for n in notes
    ]


# =============================================================================
# Summarization
# =============================================================================

@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarize a lesson or text",
    description="Returns a structured summary with key points. Length: short|medium|long.",
)
@limiter.limit(ai_limit)
async def summarize(
    request: Request,
    body: SummarizeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SummarizeResponse:
    svc = AIService(db)
    result = await svc.summarize(
        source_type=body.source_type,
        source_id=body.source_id,
        source_text=body.source_text,
        length=body.length,
    )
    return SummarizeResponse(**result)


# =============================================================================
# Flashcards
# =============================================================================

@router.post(
    "/flashcards/generate",
    response_model=FlashcardSetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate flashcards from a lesson or text",
)
@limiter.limit(ai_limit)
async def generate_flashcards(
    request: Request,
    body: GenerateFlashcardsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FlashcardSetResponse:
    svc = AIService(db)
    flashcard_set = await svc.generate_flashcards(
        user_id=current_user.id,
        source_type=body.source_type,
        source_id=body.source_id,
        source_text=body.source_text,
        num_cards=body.num_cards,
        title=body.title,
    )
    return FlashcardSetResponse(
        id=flashcard_set.id,
        title=flashcard_set.title,
        cards=[Flashcard(**c) for c in flashcard_set.cards],
        card_count=flashcard_set.card_count,
        created_at=flashcard_set.created_at,
    )


@router.get(
    "/flashcards",
    response_model=list[FlashcardSetResponse],
    summary="List my flashcard sets",
)
async def list_flashcards(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[FlashcardSetResponse]:
    svc = AIService(db)
    sets = await svc.get_user_flashcards(current_user.id)
    return [
        FlashcardSetResponse(
            id=s.id, title=s.title,
            cards=[Flashcard(**c) for c in s.cards],
            card_count=s.card_count, created_at=s.created_at,
        )
        for s in sets
    ]


# =============================================================================
# Study Planner
# =============================================================================

@router.post(
    "/study-plan/generate",
    response_model=StudyPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a personalized study plan",
)
@limiter.limit(ai_limit)
async def generate_study_plan(
    request: Request,
    body: GenerateStudyPlanRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudyPlanResponse:
    svc = AIService(db)
    plan = await svc.generate_study_plan(
        user_id=current_user.id,
        course_id=body.course_id,
        topics=body.topics,
        duration_weeks=body.duration_weeks,
        hours_per_day=body.hours_per_day,
        goals=body.goals,
    )
    return StudyPlanResponse(
        id=plan.id,
        title=plan.title,
        duration_weeks=plan.duration_weeks,
        plan_data=plan.plan_data,
        is_active=plan.is_active,
        created_at=plan.created_at,
    )


@router.get(
    "/study-plans",
    response_model=list[StudyPlanResponse],
    summary="List my active study plans",
)
async def list_study_plans(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[StudyPlanResponse]:
    svc = AIService(db)
    plans = await svc.get_study_plans(current_user.id)
    return [
        StudyPlanResponse(
            id=p.id, title=p.title, duration_weeks=p.duration_weeks,
            plan_data=p.plan_data, is_active=p.is_active, created_at=p.created_at,
        )
        for p in plans
    ]


# =============================================================================
# Recommendations
# =============================================================================

@router.get(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Get personalized learning recommendations",
    description="AI analyzes your progress and suggests what to study next.",
)
@limiter.limit(ai_limit)
async def get_recommendations(
    request: Request,
    course_id: uuid.UUID | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> RecommendationResponse:
    svc = AIService(db)
    result = await svc.get_recommendations(current_user.id, course_id)
    return RecommendationResponse(**result)
