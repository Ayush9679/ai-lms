from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user, require_role
from app.models import User
from app.schemas import CourseCreate, CourseOut, LessonCreate, LessonOut
from app.services import course_service

router = APIRouter()


@router.get("", response_model=list[CourseOut])
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return course_service.list_courses(db, skip, limit)


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("instructor", "admin")),
):
    return course_service.create_course(db, data, user)


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db)):
    return course_service.get_course(db, course_id)


@router.put("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    data: CourseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("instructor", "admin")),
):
    return course_service.update_course(db, course_id, data, user)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("instructor", "admin")),
):
    course_service.delete_course(db, course_id, user)


@router.get("/{course_id}/lessons", response_model=list[LessonOut])
def list_lessons(course_id: int, db: Session = Depends(get_db)):
    course = course_service.get_course(db, course_id)
    return course.lessons


@router.post(
    "/{course_id}/lessons",
    response_model=LessonOut,
    status_code=status.HTTP_201_CREATED,
)
def add_lesson(
    course_id: int,
    data: LessonCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("instructor", "admin")),
):
    return course_service.add_lesson(db, course_id, data, user)
