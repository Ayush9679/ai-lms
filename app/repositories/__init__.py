"""AI-LMS repositories package."""

from app.repositories.ai_repo import (
    ChatMessageRepository,
    ChatSessionRepository,
    FlashcardSetRepository,
    GeneratedNoteRepository,
    StudyPlanRepository,
)
from app.repositories.assignment_repo import AssignmentRepository, SubmissionRepository
from app.repositories.base import BaseRepository
from app.repositories.course_repo import CourseFileRepository, CourseRepository
from app.repositories.enrollment_repo import EnrollmentRepository
from app.repositories.lesson_repo import LessonProgressRepository, LessonRepository
from app.repositories.quiz_repo import (
    QuestionRepository,
    QuizAnswerRepository,
    QuizAttemptRepository,
    QuizRepository,
)
from app.repositories.user_repo import UserRepository
