from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user, require_role
from app.models import Enrollment, User
from app.schemas import EnrollmentCreate, EnrollmentOut
from app.services import course_service

router = APIRouter()


@router.get("", response_model=list[EnrollmentOut])
def my_enrollments(user: current_user, db: Session = Depends(get_db)):
    return (
        db.query(Enrollment).filter(Enrollment.user_id == user.id).all()
    )


@router.post(
    "",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
)
def enroll(
    data: EnrollmentCreate,
    user: current_user,
    db: Session = Depends(get_db),
):
    course_service.get_course(db, data.course_id)
    existing = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == user.id,
            Enrollment.course_id == data.course_id,
        )
        .first()
    )
    if existing:
        return existing

    enrollment = Enrollment(user_id=user.id, course_id=data.course_id, status="active")
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.patch("/{enrollment_id}/progress", response_model=EnrollmentOut)
def update_progress(
    enrollment_id: int,
    progress: float,
    user: current_user,
    db: Session = Depends(get_db),
):
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment or enrollment.user_id != user.id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Enrollment not found")
    enrollment.progress = max(0.0, min(100.0, progress))
    if enrollment.progress >= 100:
        enrollment.status = "completed"
    db.commit()
    db.refresh(enrollment)
    return enrollment
