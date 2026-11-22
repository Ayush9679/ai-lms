"""
AI-LMS Assignment Service — assignment CRUD, submission, and grading.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.course import CourseStatus
from app.models.enrollment import EnrollmentStatus
from app.models.user import UserRole
from app.repositories.assignment_repo import AssignmentRepository, SubmissionRepository
from app.repositories.course_repo import CourseRepository
from app.repositories.enrollment_repo import EnrollmentRepository
from app.schemas.assignment import (
    CreateAssignmentRequest,
    GradeSubmissionRequest,
    SubmitAssignmentRequest,
    UpdateAssignmentRequest,
)

logger = get_logger(__name__)


class AssignmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = AssignmentRepository(db)
        self.submission_repo = SubmissionRepository(db)
        self.course_repo = CourseRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)

    async def _get_course_instructor_id(self, course_id: uuid.UUID) -> uuid.UUID:
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundError("Course", str(course_id))
        return course.instructor_id

    async def create_assignment(
        self,
        course_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        request: CreateAssignmentRequest,
    ) -> Assignment:
        instructor_id = await self._get_course_instructor_id(course_id)
        if requester_role != UserRole.admin and instructor_id != requester_id:
            raise ForbiddenError("You can only create assignments for your own courses")

        assignment = await self.repo.create(
            course_id=course_id,
            created_by=requester_id,
            **request.model_dump(),
        )
        logger.info("Assignment created", extra={"assignment_id": str(assignment.id)})
        return assignment

    async def get_assignment(self, assignment_id: uuid.UUID) -> Assignment:
        assignment = await self.repo.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError("Assignment", str(assignment_id))
        return assignment

    async def list_course_assignments(self, course_id: uuid.UUID) -> list[Assignment]:
        return await self.repo.get_by_course(course_id)

    async def update_assignment(
        self,
        assignment_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        request: UpdateAssignmentRequest,
    ) -> Assignment:
        assignment = await self.get_assignment(assignment_id)
        if requester_role != UserRole.admin and assignment.created_by != requester_id:
            raise ForbiddenError("You can only edit your own assignments")
        update_data = request.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.update(assignment, **update_data)

    async def delete_assignment(
        self,
        assignment_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
    ) -> None:
        assignment = await self.get_assignment(assignment_id)
        if requester_role != UserRole.admin and assignment.created_by != requester_id:
            raise ForbiddenError("You can only delete your own assignments")
        await self.repo.soft_delete(assignment)

    async def submit_assignment(
        self,
        assignment_id: uuid.UUID,
        student_id: uuid.UUID,
        request: SubmitAssignmentRequest,
        file_url: str | None = None,
        file_name: str | None = None,
    ) -> AssignmentSubmission:
        await self.ensure_student_can_submit(assignment_id, student_id)
        if not request.text_content and not file_url:
            raise ValidationError("Submission must include text content or a file")

        # Check for existing submission (allow update)
        existing = await self.submission_repo.get_by_assignment_and_student(
            assignment_id, student_id
        )
        if existing:
            return await self.submission_repo.update(
                existing,
                text_content=request.text_content,
                file_url=file_url or existing.file_url,
                file_name=file_name or existing.file_name,
            )

        submission = await self.submission_repo.create(
            assignment_id=assignment_id,
            student_id=student_id,
            text_content=request.text_content,
            file_url=file_url,
            file_name=file_name,
        )
        return submission

    async def ensure_student_can_submit(
        self, assignment_id: uuid.UUID, student_id: uuid.UUID
    ) -> Assignment:
        assignment = await self.get_assignment(assignment_id)
        course = await self.course_repo.get_by_id(assignment.course_id)
        enrollment = await self.enrollment_repo.get_by_student_and_course(
            student_id, assignment.course_id
        )
        if (
            not course
            or course.status != CourseStatus.published
            or not enrollment
            or enrollment.status
            not in {
                EnrollmentStatus.active,
                EnrollmentStatus.completed,
            }
        ):
            raise ForbiddenError("You must be enrolled in this course to submit work")
        return assignment

    async def grade_submission(
        self,
        submission_id: uuid.UUID,
        grader_id: uuid.UUID,
        requester_role: UserRole,
        request: GradeSubmissionRequest,
    ) -> AssignmentSubmission:
        submission = await self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise NotFoundError("Submission", str(submission_id))

        assignment = await self.get_assignment(submission.assignment_id)

        if requester_role != UserRole.admin and assignment.created_by != grader_id:
            raise ForbiddenError("You can only grade submissions for your own assignments")

        if request.marks_obtained > assignment.max_marks:
            raise ValidationError(f"Marks cannot exceed max marks ({assignment.max_marks})")

        return await self.submission_repo.update(
            submission,
            marks_obtained=request.marks_obtained,
            feedback=request.feedback,
            graded_by=grader_id,
            graded_at=datetime.now(tz=timezone.utc),
        )

    async def get_assignment_submissions(
        self,
        assignment_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AssignmentSubmission]:
        assignment = await self.get_assignment(assignment_id)
        if requester_role != UserRole.admin and assignment.created_by != requester_id:
            raise ForbiddenError("You can only view submissions for your own assignments")
        return await self.submission_repo.get_by_assignment(assignment_id, skip, limit)

    async def get_student_submission(
        self, assignment_id: uuid.UUID, student_id: uuid.UUID
    ) -> AssignmentSubmission | None:
        return await self.submission_repo.get_by_assignment_and_student(assignment_id, student_id)

    async def get_student_submissions(
        self, student_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[AssignmentSubmission]:
        return await self.submission_repo.get_by_student(student_id, skip, limit)
