"""
AI-LMS Master API Router — aggregates all v1 routers.
"""
from fastapi import APIRouter

from app.api.v1 import (
    ai,
    assignments,
    auth,
    courses,
    dashboard,
    enrollments,
    lessons,
    quizzes,
    search,
    users,
)

api_router = APIRouter()

# Auth
api_router.include_router(auth.router, prefix="/auth", tags=["🔐 Authentication"])

# Users
api_router.include_router(users.router, prefix="/users", tags=["👤 Users"])

# Courses
api_router.include_router(courses.router, prefix="/courses", tags=["📚 Courses"])

# Lessons (nested under /courses/{id}/lessons and /lessons)
api_router.include_router(lessons.router, prefix="", tags=["📖 Lessons"])

# Enrollments
api_router.include_router(enrollments.router, prefix="/enrollments", tags=["🎓 Enrollments"])

# Quizzes
api_router.include_router(quizzes.router, prefix="", tags=["❓ Quizzes"])

# Assignments
api_router.include_router(assignments.router, prefix="", tags=["📝 Assignments"])

# AI Features
api_router.include_router(ai.router, prefix="/ai", tags=["🤖 AI Features"])

# Dashboard
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["📊 Dashboard"])

# Search
api_router.include_router(search.router, prefix="/search", tags=["🔍 Search"])
