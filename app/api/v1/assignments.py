"""
AI-LMS Assignments Router — assignment CRUD, submission, and grading.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_teacher
from app.models.user import User
from app.schemas.assignment import (
    AssignmentResponse,
    CreateAssignmentRequest,
    GradeSubmissionRequest,
    SubmissionResponse,
    SubmissionWithStudent,
    SubmitAssignmentRequest,
    UpdateAssignmentRequest,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserSummary
from app.services.assignment_service import AssignmentService
from app.services.file_service import FileService

router = APIRouter()


@router.post(
    "/courses/{course_id}/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an assignment (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def create_assignment(
    course_id: uuid.UUID,
    request: CreateAssignmentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssignmentResponse:
    svc = AssignmentService(db)
    assignment = await svc.create_assignment(
        course_id, current_user.id, current_user.role, request
    )
    return AssignmentResponse(
        id=assignment.id,
        course_id=assignment.course_id,
        created_by=assignment.created_by,
        title=assignment.title,
        description=assignment.description,
        instructions=assignment.instructions,
        due_date=assignment.due_date,
        max_marks=assignment.max_marks,
        passing_marks=assignment.passing_marks,
        is_published=assignment.is_published,
        is_closed=assignment.is_closed,
        submission_count=0,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


@router.get(
    "/courses/{course_id}/assignments",
    response_model=list[AssignmentResponse],
    summary="List assignments for a course",
)
async def list_assignments(
    course_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AssignmentResponse]:
    svc = AssignmentService(db)
    assignments = await svc.list_course_assignments(course_id)
    result = []
    for a in assignments:
        from app.repositories.assignment_repo import SubmissionRepository
        repo = SubmissionRepository(db)
        count = await repo.count_by_assignment(a.id)
        result.append(
            AssignmentResponse(
                id=a.id,
                course_id=a.course_id,
                created_by=a.created_by,
                title=a.title,
                description=a.description,
                instructions=a.instructions,
                due_date=a.due_date,
                max_marks=a.max_marks,
                passing_marks=a.passing_marks,
                is_published=a.is_published,
                is_closed=a.is_closed,
                submission_count=count,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )
    return result


@router.get(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Get assignment details",
)
async def get_assignment(
    assignment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssignmentResponse:
    svc = AssignmentService(db)
    a = await svc.get_assignment(assignment_id)
    from app.repositories.assignment_repo import SubmissionRepository
    count = await SubmissionRepository(db).count_by_assignment(a.id)
    return AssignmentResponse(
        id=a.id, course_id=a.course_id, created_by=a.created_by, title=a.title,
        description=a.description, instructions=a.instructions, due_date=a.due_date,
        max_marks=a.max_marks, passing_marks=a.passing_marks, 
        is_published=a.is_published, is_closed=a.is_closed,
        submission_count=count, created_at=a.created_at, updated_at=a.updated_at,
    )


@router.patch(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Update assignment (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def update_assignment(
    assignment_id: uuid.UUID,
    request: UpdateAssignmentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssignmentResponse:
    svc = AssignmentService(db)
    a = await svc.update_assignment(assignment_id, current_user.id, current_user.role, request)
    return AssignmentResponse(
        id=a.id, course_id=a.course_id, created_by=a.created_by, title=a.title,
        description=a.description, instructions=a.instructions, due_date=a.due_date,
        max_marks=a.max_marks, passing_marks=a.passing_marks, 
        is_published=a.is_published, is_closed=a.is_closed,
        submission_count=0, created_at=a.created_at, updated_at=a.updated_at,
    )


@router.delete(
    "/assignments/{assignment_id}",
    response_model=MessageResponse,
    summary="Delete assignment (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def delete_assignment(
    assignment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    svc = AssignmentService(db)
    await svc.delete_assignment(assignment_id, current_user.id, current_user.role)
    return MessageResponse(message="Assignment deleted successfully")


@router.post(
    "/assignments/{assignment_id}/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit assignment (Student)",
    description="Submit text content. To attach a file, use the /submit-file endpoint.",
)
async def submit_assignment(
    assignment_id: uuid.UUID,
    request: SubmitAssignmentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SubmissionResponse:
    svc = AssignmentService(db)
    submission = await svc.submit_assignment(assignment_id, current_user.id, request)
    return SubmissionResponse.model_validate(submission)


@router.post(
    "/assignments/{assignment_id}/submit-file",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit assignment with file (Student)",
    description="Upload a file submission for an assignment (PDF or image).",
)
async def submit_assignment_file(
    assignment_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> SubmissionResponse:
    file_svc = FileService()
    _, file_path, _, _, _ = await file_svc.validate_and_save(
        file, allowed_types=["application/pdf", "image/jpeg", "image/png"]
    )
    svc = AssignmentService(db)
    from app.schemas.assignment import SubmitAssignmentRequest as SAR
    submission = await svc.submit_assignment(
        assignment_id,
        current_user.id,
        SAR(),
        file_url=file_svc.get_full_path(file_path),
        file_name=file.filename,
    )
    return SubmissionResponse.model_validate(submission)


@router.get(
    "/assignments/{assignment_id}/submissions",
    response_model=list[SubmissionWithStudent],
    summary="Get all submissions for an assignment (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def get_submissions(
    assignment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> list[SubmissionWithStudent]:
    svc = AssignmentService(db)
    skip = (page - 1) * page_size
    submissions = await svc.get_assignment_submissions(
        assignment_id, current_user.id, current_user.role, skip, page_size
    )
    result = []
    for s in submissions:
        student_summary = None
        if s.student:
            student_summary = UserSummary(
                id=s.student.id,
                full_name=s.student.full_name,
                email=s.student.email,
                role=s.student.role,
                profile_image=s.student.profile_image,
            )
        result.append(
            SubmissionWithStudent(
                id=s.id, assignment_id=s.assignment_id, student_id=s.student_id,
                file_url=s.file_url, file_name=s.file_name, text_content=s.text_content,
                marks_obtained=s.marks_obtained, feedback=s.feedback,
                graded_by=s.graded_by, graded_at=s.graded_at,
                created_at=s.created_at, updated_at=s.updated_at,
                student=student_summary,
            )
        )
    return result


@router.patch(
    "/submissions/{submission_id}/grade",
    response_model=SubmissionResponse,
    summary="Grade a submission (Teacher/Admin)",
    dependencies=[Depends(require_teacher)],
)
async def grade_submission(
    submission_id: uuid.UUID,
    request: GradeSubmissionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SubmissionResponse:
    svc = AssignmentService(db)
    submission = await svc.grade_submission(
        submission_id, current_user.id, current_user.role, request
    )
    return SubmissionResponse.model_validate(submission)


@router.get(
    "/my-submissions",
    response_model=list[SubmissionResponse],
    summary="Get all my submissions (Student)",
)
async def get_my_submissions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SubmissionResponse]:
    svc = AssignmentService(db)
    submissions = await svc.get_student_submissions(current_user.id)
    return [SubmissionResponse.model_validate(s) for s in submissions]
