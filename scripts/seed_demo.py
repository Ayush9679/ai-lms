"""Create a small demo teacher, student, published course, and enrollment."""

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models import Course, CourseLevel, CourseStatus, Enrollment, EnrollmentStatus, Lesson, User, UserRole

DEMO_PASSWORD = "DemoOnly123!"
DEMO_TEACHER_EMAIL = "teacher-demo@ai-lms.local"
DEMO_STUDENT_EMAIL = "demo@ai-lms.local"


async def seed_demo() -> None:
    async with AsyncSessionLocal() as session:
        teacher = await session.scalar(
            select(User).where(User.email == DEMO_TEACHER_EMAIL)
        )
        if teacher is None:
            teacher = User(
                email=DEMO_TEACHER_EMAIL,
                full_name="AI-LMS Demo Teacher",
                hashed_password=hash_password(DEMO_PASSWORD),
                role=UserRole.teacher,
                is_active=True,
                is_verified=True,
            )
            session.add(teacher)

        student = await session.scalar(
            select(User).where(User.email == DEMO_STUDENT_EMAIL)
        )
        if student is None:
            student = User(
                email=DEMO_STUDENT_EMAIL,
                full_name="AI-LMS Demo Student",
                hashed_password=hash_password(DEMO_PASSWORD),
                role=UserRole.student,
                is_active=True,
                is_verified=True,
            )
            session.add(student)

        await session.flush()

        course = await session.scalar(select(Course).where(Course.slug == "demo-python-basics"))
        if course is None:
            course = Course(
                title="Python Basics (Demo)",
                slug="demo-python-basics",
                description="A short sample course for exploring the AI-LMS student experience.",
                category="Programming",
                level=CourseLevel.beginner,
                status=CourseStatus.published,
                instructor_id=teacher.id,
                tags="python,demo",
            )
            session.add(course)
            await session.flush()
            session.add(
                Lesson(
                    course_id=course.id,
                    title="Variables and Values",
                    content="A variable is a name that refers to a value. In Python, write count = 3 to bind the name count to the integer value 3.",
                    duration_minutes=5,
                    order_index=0,
                    is_published=True,
                )
            )

        enrollment = await session.scalar(
            select(Enrollment).where(
                Enrollment.student_id == student.id,
                Enrollment.course_id == course.id,
            )
        )
        if enrollment is None:
            session.add(
                Enrollment(
                    student_id=student.id,
                    course_id=course.id,
                    status=EnrollmentStatus.active,
                    progress=0,
                )
            )

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_demo())
