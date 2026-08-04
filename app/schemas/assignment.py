"""
AI-LMS Assignment Schemas — assignment CRUD, submissions, and grading.
"""
import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema
from app.schemas.user import UserSummary


class CreateAssignmentRequest(BaseSchema):
    """Teacher creates an assignment."""
    title: str = Field(min_length=3, max_length=500)
    description: str | None = None
    instructions: str | None = Field(default=None, max_length=10000)
    due_date: datetime | None = None
    max_marks: float = Field(default=100.0, ge=1.0, le=1000.0)
    passing_marks: float = Field(default=40.0, ge=0.0)
    is_published: bool = True
    is_closed: bool = False


class UpdateAssignmentRequest(BaseSchema):
    """Teacher updates an assignment."""
    title: str | None = Field(default=None, min_length=3, max_length=500)
    description: str | None = None
    instructions: str | None = None
    due_date: datetime | None = None
    max_marks: float | None = None
    passing_marks: float | None = None
    is_published: bool | None = None
    is_closed: bool | None = None


class AssignmentResponse(BaseSchema):
    """Full assignment details."""
    id: uuid.UUID
    course_id: uuid.UUID
    created_by: uuid.UUID
    title: str
    description: str | None
    instructions: str | None
    due_date: datetime | None
    max_marks: float
    passing_marks: float
    is_published: bool = True
    is_closed: bool = False
    submission_count: int = 0
    created_at: datetime
    updated_at: datetime


class SubmitAssignmentRequest(BaseSchema):
    """Student submits a text response (file upload handled separately via /files endpoint)."""
    text_content: str | None = Field(default=None, max_length=50000)


class GradeSubmissionRequest(BaseSchema):
    """Teacher grades a student's submission."""
    marks_obtained: float = Field(ge=0.0)
    feedback: str | None = Field(default=None, max_length=5000)


class SubmissionResponse(BaseSchema):
    """Assignment submission details."""
    id: uuid.UUID
    assignment_id: uuid.UUID
    student_id: uuid.UUID
    file_url: str | None
    file_name: str | None
    text_content: str | None
    marks_obtained: float | None
    feedback: str | None
    graded_by: uuid.UUID | None
    graded_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SubmissionWithStudent(SubmissionResponse):
    """Submission with embedded student info (for teacher grading view)."""
    student: UserSummary
