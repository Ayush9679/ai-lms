from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase, ORMModel):
    id: int
    role: str
    profile_image: str | None = None
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CourseCreate(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    level: str = "beginner"


class CourseOut(CourseCreate, ORMModel):
    id: int
    instructor_id: int
    created_at: datetime


class LessonCreate(BaseModel):
    title: str
    content: str | None = None
    order_index: int = 0


class LessonOut(LessonCreate, ORMModel):
    id: int
    course_id: int
    material_url: str | None = None
    created_at: datetime


class EnrollmentCreate(BaseModel):
    course_id: int


class EnrollmentOut(ORMModel):
    id: int
    user_id: int
    course_id: int
    status: str
    progress: float
    enrolled_at: datetime


class QuizCreate(BaseModel):
    title: str
    questions: list[dict]
    passing_score: float = 60.0


class QuizOut(QuizCreate, ORMModel):
    id: int
    course_id: int
    created_at: datetime


class QuizSubmit(BaseModel):
    answers: list[dict]


class QuizResult(BaseModel):
    score: float
    passed: bool


class AssignmentCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None


class AssignmentOut(AssignmentCreate, ORMModel):
    id: int
    course_id: int
    created_at: datetime


class SubmissionOut(ORMModel):
    id: int
    assignment_id: int
    user_id: int
    file_url: str | None = None
    text: str | None = None
    grade: float | None = None
    feedback: str | None = None
    submitted_at: datetime


class GradingOut(BaseModel):
    grade: float
    feedback: str | None = None


class DashboardStats(BaseModel):
    total_courses: int
    active_courses: int
    completed_courses: int
    avg_progress: float
    upcoming_assignments: int


class Message(BaseModel):
    message: str


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
