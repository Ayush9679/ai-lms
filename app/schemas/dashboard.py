"""
AI-LMS Dashboard Schemas — schemas for student, teacher, and admin dashboard response structures.
"""
from typing import Any
from app.schemas.common import BaseSchema

class ProgressSummary(BaseSchema):
    total_courses: int
    completed_courses: int
    average_progress: float

class QuizSummary(BaseSchema):
    total_quizzes_taken: int
    passed_quizzes: int
    average_score: float

class StudentDashboardOut(BaseSchema):
    progress_summary: ProgressSummary
    quiz_summary: QuizSummary
    enrolled_courses: list[Any] = []
    recent_activity: list[Any] = []
    recommended_courses: list[Any] = []

class CourseStats(BaseSchema):
    total_courses: int
    published_courses: int
    draft_courses: int

class StudentStats(BaseSchema):
    total_students: int
    active_students_this_month: int

class QuizStats(BaseSchema):
    total_quizzes_built: int

class TeacherCourseSummary(BaseSchema):
    id: str
    title: str
    status: str
    lessons_count: int
    quizzes_count: int
    enrollments_count: int
    average_progress: float

class TeacherDashboardOut(BaseSchema):
    course_stats: CourseStats
    student_stats: StudentStats
    quiz_stats: QuizStats
    course_list: list[TeacherCourseSummary] = []
    recent_activity: list[Any] = []

class AdminMetrics(BaseSchema):
    total_users: int
    total_students: int
    total_teachers: int
    total_courses: int
    total_enrollments: int

class AdminDashboardOut(BaseSchema):
    metrics: AdminMetrics
    recent_activity: list[Any] = []
    system_logs: list[Any] = []
