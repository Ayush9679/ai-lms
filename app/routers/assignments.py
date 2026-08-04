from fastapi import APIRouter, Depends, File, Form, status, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user, require_role
from app.models import User
from app.schemas import AssignmentCreate, AssignmentOut, GradingOut, SubmissionOut
from app.services import assignment_service
from app.utils.file_upload import save_upload

router = APIRouter()


@router.post(
    "/courses/{course_id}/assignments",
    response_model=AssignmentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    course_id: int,
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("instructor", "admin")),
):
    return assignment_service.create_assignment(db, course_id, data, user)


@router.get("/assignments/{assignment_id}", response_model=AssignmentOut)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    return assignment_service.get_assignment(db, assignment_id)


@router.get("/assignments/{assignment_id}/submissions", response_model=list[SubmissionOut])
def list_submissions(
    assignment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("instructor", "admin")),
):
    return assignment_service.list_submissions(db, assignment_id)


@router.post(
    "/assignments/{assignment_id}/submit",
    response_model=SubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_assignment(
    assignment_id: int,
    user: current_user,
    db: Session = Depends(get_db),
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
):
    file_url = None
    if file is not None:
        file_url = await save_upload(file, "assignments")
    return assignment_service.submit_assignment(db, assignment_id, user, file_url, text)


@router.post("/submissions/{submission_id}/grade", response_model=GradingOut)
def grade_submission(
    submission_id: int,
    data: GradingOut,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("instructor", "admin")),
):
    submission = assignment_service.grade_submission(
        db, submission_id, data.grade, data.feedback
    )
    return GradingOut(grade=submission.grade, feedback=submission.feedback)
