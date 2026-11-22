"""
AI-LMS Dashboard Service — aggregated stats for all three dashboard types.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course, CourseStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.user import User, UserRole
from app.repositories.assignment_repo import AssignmentRepository, SubmissionRepository
from app.repositories.course_repo import CourseRepository
from app.repositories.enrollment_repo import EnrollmentRepository
from app.repositories.quiz_repo import QuizAttemptRepository
from app.repositories.user_repo import UserRepository


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.course_repo = CourseRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.quiz_attempt_repo = QuizAttemptRepository(db)
        self.assignment_repo = AssignmentRepository(db)
        self.submission_repo = SubmissionRepository(db)

    async def get_student_dashboard(self, student_id: uuid.UUID) -> dict:
        """Dashboard data for a student user."""
        enrollments = await self.enrollment_repo.get_by_student(student_id, skip=0, limit=10)
        attempts = await self.quiz_attempt_repo.get_by_student(student_id, skip=0, limit=20)

        # Compute stats
        total_enrolled = await self.enrollment_repo.count_by_student(student_id)
        completed_count = sum(1 for e in enrollments if e.status == EnrollmentStatus.completed)
        avg_progress = (
            sum(e.progress for e in enrollments) / len(enrollments) if enrollments else 0.0
        )

        total_quizzes_taken = len(attempts)
        passed_quizzes = sum(1 for a in attempts if a.passed)
        avg_score = (
            sum(a.percentage for a in attempts) / total_quizzes_taken
            if total_quizzes_taken
            else 0.0
        )

        return {
            "progress_summary": {
                "total_courses": total_enrolled,
                "completed_courses": completed_count,
                "average_progress": round(avg_progress, 1),
            },
            "quiz_summary": {
                "total_quizzes_taken": total_quizzes_taken,
                "passed_quizzes": passed_quizzes,
                "average_score": round(avg_score, 1),
            },
            "enrolled_courses": [],
            "recent_activity": [],
            "recommended_courses": [],
        }

    async def get_teacher_dashboard(self, teacher_id: uuid.UUID) -> dict:
        """Dashboard data for a teacher user."""
        courses = await self.course_repo.get_by_instructor(teacher_id, skip=0, limit=10)

        total_courses = await self.course_repo.count_by_instructor(teacher_id)
        published_courses = sum(1 for c in courses if c.status == CourseStatus.published)

        # Approximate total students across all courses
        total_students = 0
        for course in courses:
            total_students += await self.enrollment_repo.count_by_course(course.id)

        # Approximate total quizzes across teacher's courses
        total_quizzes_built = sum(len(c.quizzes) for c in courses)

        course_list = []
        for course in courses:
            lessons_count = len(course.lessons)
            quizzes_count = len(course.quizzes)
            enrollments_count = await self.enrollment_repo.count_by_course(course.id)

            # calculate average progress
            avg_prog = 0.0
            if course.enrollments:
                avg_prog = sum(e.progress for e in course.enrollments) / len(course.enrollments)

            course_list.append(
                {
                    "id": str(course.id),
                    "title": course.title,
                    "status": course.status.value,
                    "lessons_count": lessons_count,
                    "quizzes_count": quizzes_count,
                    "enrollments_count": enrollments_count,
                    "average_progress": round(avg_prog, 1),
                }
            )

        return {
            "course_stats": {
                "total_courses": total_courses,
                "published_courses": published_courses,
                "draft_courses": total_courses - published_courses,
            },
            "student_stats": {
                "total_students": total_students,
                "active_students_this_month": total_students,
            },
            "quiz_stats": {
                "total_quizzes_built": total_quizzes_built,
            },
            "course_list": course_list,
            "recent_activity": [],
        }

    async def get_admin_dashboard(self) -> dict:
        """Dashboard data for admin users."""
        total_users = await self.user_repo.count()
        total_students = await self.user_repo.count(
            [User.role == UserRole.student, User.deleted_at.is_(None)]
        )
        total_teachers = await self.user_repo.count(
            [User.role == UserRole.teacher, User.deleted_at.is_(None)]
        )

        # Count courses
        result = await self.db.execute(
            select(func.count()).select_from(Course).where(Course.deleted_at.is_(None))
        )
        total_courses = result.scalar_one()

        # Total enrollments
        result = await self.db.execute(
            select(func.count()).select_from(Enrollment).where(Enrollment.deleted_at.is_(None))
        )
        total_enrollments = result.scalar_one()

        return {
            "metrics": {
                "total_users": total_users,
                "total_students": total_students,
                "total_teachers": total_teachers,
                "total_courses": total_courses,
                "total_enrollments": total_enrollments,
            },
            "recent_activity": [],
            "system_logs": [],
        }
