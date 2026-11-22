"""
AI-LMS Quizzes Router — quiz CRUD, AI generation, and attempt submission.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_student, require_teacher
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.quiz import (
    CreateQuizRequest,
    GenerateQuizRequest,
    QuizAnswerResponse,
    QuizAttemptResponse,
    QuizAttemptSummary,
    QuizResponse,
    QuizSummary,
    QuestionResponse,
    SubmitAttemptRequest,
    UpdateQuizRequest,
)
from app.services.quiz_service import QuizService

router = APIRouter()


def _build_quiz_response(quiz, include_answers: bool = False) -> QuizResponse:
    questions = [
        QuestionResponse(
            id=q.id,
            quiz_id=q.quiz_id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            explanation=q.explanation,
            marks=q.marks,
            order_index=q.order_index,
        )
        for q in quiz.questions
    ]
    return QuizResponse(
        id=quiz.id,
        course_id=quiz.course_id,
        lesson_id=quiz.lesson_id,
        created_by=quiz.created_by,
        title=quiz.title,
        description=quiz.description,
        difficulty=quiz.difficulty,
        passing_score=quiz.passing_score,
        negative_marking=quiz.negative_marking,
        time_limit_minutes=quiz.time_limit_minutes,
        max_attempts=quiz.max_attempts,
        is_ai_generated=quiz.is_ai_generated,
        question_count=len(questions),
        questions=questions,
        created_at=quiz.created_at,
    )


@router.post(
    "/courses/{course_id}/quizzes",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a quiz manually (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def create_quiz(
    course_id: uuid.UUID,
    request: CreateQuizRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuizResponse:
    svc = QuizService(db)
    quiz = await svc.create_quiz(course_id, current_user.id, current_user.role, request)
    return _build_quiz_response(quiz)


@router.post(
    "/courses/{course_id}/quizzes/ai-generate",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a quiz with AI (Teacher/Admin)",
    description="Uses Gemini to generate quiz questions from a lesson, course, or text.",
    dependencies=[Depends(require_teacher)],
)
async def generate_ai_quiz(
    course_id: uuid.UUID,
    request: GenerateQuizRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuizResponse:
    svc = QuizService(db)
    quiz = await svc.create_ai_quiz(course_id, current_user.id, current_user.role, request)
    return _build_quiz_response(quiz)


@router.get(
    "/courses/{course_id}/quizzes",
    response_model=list[QuizSummary],
    summary="List quizzes for a course",
)
async def list_quizzes(
    course_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[QuizSummary]:
    svc = QuizService(db)
    quizzes = await svc.list_course_quizzes(course_id)
    return [
        QuizSummary(
            id=q.id,
            title=q.title,
            difficulty=q.difficulty,
            passing_score=q.passing_score,
            question_count=len(q.questions),
            time_limit_minutes=q.time_limit_minutes,
            is_ai_generated=q.is_ai_generated,
            created_at=q.created_at,
        )
        for q in quizzes
    ]


@router.get(
    "/quizzes/{quiz_id}",
    response_model=QuizResponse,
    summary="Get quiz (without answers for students)",
)
async def get_quiz(
    quiz_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuizResponse:
    svc = QuizService(db)
    quiz = await svc.get_quiz(quiz_id)
    return _build_quiz_response(quiz)


@router.patch(
    "/quizzes/{quiz_id}",
    response_model=QuizResponse,
    summary="Update quiz metadata (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def update_quiz(
    quiz_id: uuid.UUID,
    request: UpdateQuizRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuizResponse:
    svc = QuizService(db)
    quiz = await svc.update_quiz(quiz_id, current_user.id, current_user.role, request)
    return _build_quiz_response(quiz)


@router.delete(
    "/quizzes/{quiz_id}",
    response_model=MessageResponse,
    summary="Delete quiz (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def delete_quiz(
    quiz_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = QuizService(db)
    await svc.delete_quiz(quiz_id, current_user.id, current_user.role)
    return MessageResponse(message="Quiz deleted successfully")


@router.post(
    "/quizzes/{quiz_id}/attempts",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a quiz attempt (Student)",
    description="Submit answers and get instant grading with score breakdown.",
    dependencies=[Depends(require_student)],
)
async def submit_attempt(
    quiz_id: uuid.UUID,
    request: SubmitAttemptRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuizAttemptResponse:
    svc = QuizService(db)
    attempt = await svc.submit_attempt(quiz_id, current_user.id, request)

    # Build answer details from the attempt's transient attribute
    answer_details = getattr(attempt, "_answer_details", [])
    answers = [
        QuizAnswerResponse(
            question_id=a["question_id"],
            given_answer=a["given_answer"],
            correct_answer=a["correct_answer"],
            is_correct=a["is_correct"],
            marks_awarded=a["marks_awarded"],
            explanation=a.get("explanation"),
        )
        for a in answer_details
    ]

    return QuizAttemptResponse(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        student_id=attempt.student_id,
        score=attempt.score,
        max_score=attempt.max_score,
        percentage=attempt.percentage,
        passed=attempt.passed,
        time_taken_seconds=attempt.time_taken_seconds,
        attempt_number=attempt.attempt_number,
        answers=answers,
        created_at=attempt.created_at,
    )


@router.get(
    "/quizzes/{quiz_id}/my-attempts",
    response_model=list[QuizAttemptSummary],
    summary="Get my attempt history for a quiz",
    dependencies=[Depends(require_student)],
)
async def get_my_attempts(
    quiz_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[QuizAttemptSummary]:
    svc = QuizService(db)
    quiz = await svc.get_quiz(quiz_id)
    attempts = await svc.get_attempt_history(current_user.id, quiz_id)
    return [
        QuizAttemptSummary(
            id=a.id,
            quiz_id=a.quiz_id,
            quiz_title=quiz.title,
            score=a.score,
            percentage=a.percentage,
            passed=a.passed,
            attempt_number=a.attempt_number,
            created_at=a.created_at,
        )
        for a in attempts
    ]


@router.get(
    "/quizzes/students/quiz-history",
    response_model=list[QuizAttemptSummary],
    summary="Get all quiz attempts for current student",
    dependencies=[Depends(require_student)],
)
async def get_student_quiz_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[QuizAttemptSummary]:
    svc = QuizService(db)
    attempts = await svc.get_student_attempts(current_user.id)
    result = []
    for a in attempts:
        quiz = await svc.get_quiz(a.quiz_id)
        result.append(
            QuizAttemptSummary(
                id=a.id,
                quiz_id=a.quiz_id,
                quiz_title=quiz.title,
                score=a.score,
                percentage=a.percentage,
                passed=a.passed,
                attempt_number=a.attempt_number,
                created_at=a.created_at,
            )
        )
    return result
