"""AI-LMS dependencies package."""
from app.dependencies.auth import (
    get_current_active_user,
    get_current_user,
    require_admin,
    require_roles,
    require_student,
    require_teacher,
    require_teacher_or_student,
)
from app.database import get_db
