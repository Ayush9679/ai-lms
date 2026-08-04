"""
AI-LMS Course Tests — CRUD, search, and RBAC enforcement.
"""
import pytest
from httpx import AsyncClient


async def _register_and_login(client, email, password, role="teacher"):
    await client.post(
        "/api/v1/auth/register",
        json={"full_name": "Test User", "email": email, "password": password, "role": role},
    )
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_teacher_can_create_course(client: AsyncClient):
    """Teacher can create a course."""
    token = await _register_and_login(
        client, "teacher1@test.com", "TeachPass123!", "teacher"
    )
    response = await client.post(
        "/api/v1/courses/",
        json={
            "title": "Python Fundamentals",
            "description": "Learn Python from scratch",
            "category": "Programming",
            "level": "beginner",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Python Fundamentals"
    assert "slug" in data
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_student_cannot_create_course(client: AsyncClient):
    """Student attempting to create a course gets 403."""
    token = await _register_and_login(
        client, "student1@test.com", "StudPass123!", "student"
    )
    response = await client.post(
        "/api/v1/courses/",
        json={"title": "Hacker Course", "level": "beginner"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_courses_public(client: AsyncClient):
    """Anyone can list published courses (no auth required)."""
    response = await client.get("/api/v1/courses/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_search_courses(client: AsyncClient):
    """Search endpoint returns paginated results."""
    response = await client.get(
        "/api/v1/search/courses",
        params={"q": "python", "page": 1, "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_course_crud_flow(client: AsyncClient):
    """Full CRUD: create → get → update → delete."""
    token = await _register_and_login(
        client, "crud_teacher@test.com", "CrudPass123!", "teacher"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Create
    create_r = await client.post(
        "/api/v1/courses/",
        json={"title": "CRUD Test Course", "level": "intermediate"},
        headers=headers,
    )
    assert create_r.status_code == 201
    course_id = create_r.json()["id"]

    # Get
    get_r = await client.get(f"/api/v1/courses/{course_id}")
    assert get_r.status_code == 200
    assert get_r.json()["id"] == course_id

    # Update
    update_r = await client.patch(
        f"/api/v1/courses/{course_id}",
        json={"title": "CRUD Updated Course", "status": "published"},
        headers=headers,
    )
    assert update_r.status_code == 200
    assert update_r.json()["title"] == "CRUD Updated Course"

    # Delete
    delete_r = await client.delete(
        f"/api/v1/courses/{course_id}",
        headers=headers,
    )
    assert delete_r.status_code == 200


@pytest.mark.asyncio
async def test_enroll_in_course(client: AsyncClient):
    """Student can enroll in a published course."""
    # Teacher creates and publishes a course
    t_token = await _register_and_login(
        client, "pub_teacher@test.com", "PubTeach123!", "teacher"
    )
    c_r = await client.post(
        "/api/v1/courses/",
        json={"title": "Enrollment Test Course", "level": "beginner"},
        headers={"Authorization": f"Bearer {t_token}"},
    )
    course_id = c_r.json()["id"]
    await client.patch(
        f"/api/v1/courses/{course_id}",
        json={"status": "published"},
        headers={"Authorization": f"Bearer {t_token}"},
    )

    # Student enrolls
    s_token = await _register_and_login(
        client, "enroll_student@test.com", "StudPass123!", "student"
    )
    enroll_r = await client.post(
        "/api/v1/enrollments/",
        json={"course_id": course_id},
        headers={"Authorization": f"Bearer {s_token}"},
    )
    assert enroll_r.status_code == 201
    assert enroll_r.json()["course_id"] == course_id

    # Duplicate enrollment returns 409
    dup_r = await client.post(
        "/api/v1/enrollments/",
        json={"course_id": course_id},
        headers={"Authorization": f"Bearer {s_token}"},
    )
    assert dup_r.status_code == 409


@pytest.mark.asyncio
async def test_lesson_crud(client: AsyncClient):
    """Teacher can create and manage lessons in their course."""
    token = await _register_and_login(
        client, "lesson_teacher@test.com", "LessonPass123!", "teacher"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Create course
    c_r = await client.post(
        "/api/v1/courses/",
        json={"title": "Lesson Test Course", "level": "beginner"},
        headers=headers,
    )
    course_id = c_r.json()["id"]

    # Create lesson
    l_r = await client.post(
        f"/api/v1/courses/{course_id}/lessons",
        json={
            "title": "Lesson 1: Introduction",
            "content": "Welcome to the course!",
            "order_index": 1,
            "is_published": True,
        },
        headers=headers,
    )
    assert l_r.status_code == 201
    lesson_id = l_r.json()["id"]

    # Get lesson
    get_r = await client.get(
        f"/api/v1/lessons/{lesson_id}",
        headers=headers,
    )
    assert get_r.status_code == 200

    # Update lesson
    upd_r = await client.patch(
        f"/api/v1/lessons/{lesson_id}",
        json={"title": "Lesson 1: Updated Introduction"},
        headers=headers,
    )
    assert upd_r.status_code == 200
    assert upd_r.json()["title"] == "Lesson 1: Updated Introduction"


@pytest.mark.asyncio
async def test_quiz_create_and_submit(client: AsyncClient):
    """Teacher creates quiz; student submits attempt and gets graded."""
    t_token = await _register_and_login(
        client, "quiz_teacher@test.com", "QuizTeach123!", "teacher"
    )
    t_headers = {"Authorization": f"Bearer {t_token}"}

    # Create course
    c_r = await client.post(
        "/api/v1/courses/",
        json={"title": "Quiz Course", "level": "beginner"},
        headers=t_headers,
    )
    course_id = c_r.json()["id"]

    # Create quiz
    q_r = await client.post(
        f"/api/v1/courses/{course_id}/quizzes",
        json={
            "title": "Quiz 1",
            "passing_score": 50.0,
            "questions": [
                {
                    "question_text": "What is 2 + 2?",
                    "question_type": "mcq",
                    "options": [
                        {"text": "3", "is_correct": False},
                        {"text": "4", "is_correct": True},
                        {"text": "5", "is_correct": False},
                    ],
                    "explanation": "Basic arithmetic",
                    "marks": 2.0,
                },
                {
                    "question_text": "Python is a programming language.",
                    "question_type": "true_false",
                    "correct_answer": "True",
                    "marks": 1.0,
                },
            ],
        },
        headers=t_headers,
    )
    assert q_r.status_code == 201
    quiz_id = q_r.json()["id"]
    question_ids = [q["id"] for q in q_r.json()["questions"]]

    # Publish the course so students can access it
    await client.patch(
        f"/api/v1/courses/{course_id}",
        json={"status": "published"},
        headers=t_headers,
    )

    # Student enrolls
    s_token = await _register_and_login(
        client, "quiz_student@test.com", "StudQuiz123!", "student"
    )
    s_headers = {"Authorization": f"Bearer {s_token}"}
    await client.post(
        "/api/v1/enrollments/",
        json={"course_id": course_id},
        headers=s_headers,
    )

    # Student submits attempt
    attempt_r = await client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts",
        json={
            "answers": [
                {"question_id": question_ids[0], "given_answer": "4"},
                {"question_id": question_ids[1], "given_answer": "True"},
            ],
            "time_taken_seconds": 45,
        },
        headers=s_headers,
    )
    assert attempt_r.status_code == 201
    result = attempt_r.json()
    assert result["passed"] is True
    assert result["percentage"] == 100.0
