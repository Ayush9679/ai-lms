"""
AI-LMS Dashboard Router — role-specific dashboard data.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_admin, require_student, require_teacher
from app.models.user import User
from app.schemas.dashboard import (
    StudentDashboardOut,
    TeacherDashboardOut,
    AdminDashboardOut,
)
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get(
    "/student",
    response_model=StudentDashboardOut,
    summary="Student dashboard data",
    description="Returns enrolled courses, progress, quiz scores, and recent activity for the current student.",
    dependencies=[Depends(require_student)],
)
async def student_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    svc = DashboardService(db)
    return await svc.get_student_dashboard(current_user.id)


@router.get(
    "/teacher",
    response_model=TeacherDashboardOut,
    summary="Teacher dashboard data",
    description="Returns course stats, enrolled students, and recent activity for the current teacher.",
    dependencies=[Depends(require_teacher)],
)
async def teacher_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    svc = DashboardService(db)
    return await svc.get_teacher_dashboard(current_user.id)


@router.get(
    "/admin",
    response_model=AdminDashboardOut,
    summary="Admin dashboard data (Admin only)",
    description="Platform-wide statistics: users, courses, enrollments, active students.",
    dependencies=[Depends(require_admin)],
)
async def admin_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    svc = DashboardService(db)
    return await svc.get_admin_dashboard()
