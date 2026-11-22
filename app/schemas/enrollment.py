"""
AI-LMS Enrollment Schemas.
"""

import uuid
from datetime import datetime

from app.models.enrollment import EnrollmentStatus
from app.schemas.common import BaseSchema
from app.schemas.course import CourseSummary
from app.schemas.user import UserSummary


class EnrollRequest(BaseSchema):
    """Student enrolls in a course."""

    course_id: uuid.UUID


class EnrollmentResponse(BaseSchema):
    """Enrollment details."""

    id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID
    status: EnrollmentStatus
    progress: float
    completed_lessons: int
    created_at: datetime
    updated_at: datetime


class EnrollmentWithCourse(EnrollmentResponse):
    """Enrollment with embedded course info (for student dashboard)."""

    course: CourseSummary


class EnrollmentWithStudent(EnrollmentResponse):
    """Enrollment with embedded student info (for teacher view)."""

    student: UserSummary


class UpdateProgressRequest(BaseSchema):
    """Update enrollment progress (called after lesson completion)."""

    completed_lessons: int
    progress: float
