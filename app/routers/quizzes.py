from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user, require_role
from app.models import User
from app.schemas import QuizCreate, QuizOut, QuizResult, QuizSubmit
from app.services import quiz_service

router = APIRouter()


@router.post(
    "/courses/{course_id}/quizzes",
    response_model=QuizOut,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(
    course_id: int,
    data: QuizCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("instructor", "admin")),
):
    return quiz_service.create_quiz(db, course_id, data, user)


@router.get("/quizzes/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    return quiz_service.get_quiz(db, quiz_id)


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizResult)
def submit_quiz(
    quiz_id: int,
    data: QuizSubmit,
    user: current_user,
    db: Session = Depends(get_db),
):
    quiz = quiz_service.get_quiz(db, quiz_id)
    attempt = quiz_service.grade_quiz(db, quiz, data, user)
    return QuizResult(score=attempt.score, passed=attempt.passed)
