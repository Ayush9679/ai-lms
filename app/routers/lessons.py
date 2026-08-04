from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user, require_role
from app.models import User
from app.schemas import LessonOut
from app.services import course_service

router = APIRouter()


@router.get("/lessons/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    return course_service.get_lesson(db, lesson_id)


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("instructor", "admin")),
):
    course_service.delete_lesson(db, lesson_id, user)
