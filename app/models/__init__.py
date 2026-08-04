"""
AI-LMS Models Package — imports all models to ensure Alembic detects them.
"""
from app.models.ai_chat import (
    AIChatMessage,
    AIChatSession,
    FlashcardSet,
    GeneratedNote,
    StudyPlan,
)
from app.models.analytics import CourseAnalytics, UserActivity
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.base import UUIDBase
from app.models.course import Course, CourseFile, CourseLevel, CourseStatus, FileType
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.lesson import Lesson, LessonProgress
from app.models.quiz import DifficultyLevel, Question, QuestionType, Quiz, QuizAnswer, QuizAttempt
from app.models.user import EmailVerification, PasswordReset, User, UserRole

__all__ = [
    # Base
    "UUIDBase",
    # User
    "User",
    "UserRole",
    "EmailVerification",
    "PasswordReset",
    # Course
    "Course",
    "CourseFile",
    "CourseLevel",
    "CourseStatus",
    "FileType",
    # Lesson
    "Lesson",
    "LessonProgress",
    # Enrollment
    "Enrollment",
    "EnrollmentStatus",
    # Quiz
    "Quiz",
    "Question",
    "QuizAttempt",
    "QuizAnswer",
    "QuestionType",
    "DifficultyLevel",
    # Assignment
    "Assignment",
    "AssignmentSubmission",
    # AI
    "AIChatSession",
    "AIChatMessage",
    "GeneratedNote",
    "StudyPlan",
    "FlashcardSet",
    # Analytics
    "UserActivity",
    "CourseAnalytics",
]
