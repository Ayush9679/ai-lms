"""
AI-LMS Course Tests — CRUD, search, and RBAC enforcement.
"""

import pytest
from httpx import AsyncClient
import uuid
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.course import CourseStatus


async def _register_and_login(client, email, password, role="teacher"):
    await client.post(
        "/api/v1/auth/register",
        json={"full_name": "Test User", "email": email, "password": password, "role": role},
    )
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


async def _meet_publish_requirements(db, course_id: str) -> None:
    course = await db.get(Course, uuid.UUID(course_id))
    course.thumbnail = "/static/test/course-thumbnail.png"
    db.add(
        Lesson(
            course_id=course.id,
            title="Ready video lesson",
            video_url="/static/test/video.mp4",
            video_status="ready",
        )
    )
    await db.commit()


@pytest.mark.asyncio
async def test_teacher_can_create_course(client: AsyncClient):
    """Teacher can create a course."""
    token = await _register_and_login(client, "teacher1@test.com", "TeachPass123!", "teacher")
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
    token = await _register_and_login(client, "student1@test.com", "StudPass123!", "student")
    response = await client.post(
        "/api/v1/courses/",
        json={"title": "Hacker Course", "level": "beginner"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_teacher_cannot_upload_file_to_another_teachers_course(client: AsyncClient):
    owner_token = await _register_and_login(
        client, "course_owner@test.com", "OwnerPass123!", "teacher"
    )
    course_response = await client.post(
        "/api/v1/courses/",
        json={"title": "Owner Course", "level": "beginner"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    course_id = course_response.json()["id"]

    other_teacher_token = await _register_and_login(
        client, "other_teacher@test.com", "OtherPass123!", "teacher"
    )
    response = await client.post(
        f"/api/v1/courses/{course_id}/files",
        files={"file": ("notes.pdf", b"not a real pdf", "application/pdf")},
        headers={"Authorization": f"Bearer {other_teacher_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_access_teacher_dashboard(client: AsyncClient):
    token = await _register_and_login(
        client, "dashboard_student@test.com", "DashPass123!", "student"
    )
    response = await client.get(
        "/api/v1/dashboard/teacher",
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
async def test_course_crud_flow(client: AsyncClient, db):
    """Full CRUD: create → get → update → delete."""
    token = await _register_and_login(client, "crud_teacher@test.com", "CrudPass123!", "teacher")
    headers = {"Authorization": f"Bearer {token}"}

    # Create
    create_r = await client.post(
        "/api/v1/courses/",
        json={"title": "CRUD Test Course", "level": "intermediate"},
        headers=headers,
    )
    assert create_r.status_code == 201
    course_id = create_r.json()["id"]
    await _meet_publish_requirements(db, course_id)

    # Get
    anonymous_get = await client.get(f"/api/v1/courses/{course_id}")
    assert anonymous_get.status_code == 404
    get_r = await client.get(f"/api/v1/courses/{course_id}", headers=headers)
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
async def test_enroll_in_course(client: AsyncClient, db):
    """Student can enroll in a published course."""
    # Teacher creates and publishes a course
    t_token = await _register_and_login(client, "pub_teacher@test.com", "PubTeach123!", "teacher")
    c_r = await client.post(
        "/api/v1/courses/",
        json={"title": "Enrollment Test Course", "level": "beginner"},
        headers={"Authorization": f"Bearer {t_token}"},
    )
    course_id = c_r.json()["id"]
    await _meet_publish_requirements(db, course_id)
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
async def test_quiz_create_and_submit(client: AsyncClient, db):
    """Teacher creates quiz; student submits attempt and gets graded."""
    t_token = await _register_and_login(client, "quiz_teacher@test.com", "QuizTeach123!", "teacher")
    t_headers = {"Authorization": f"Bearer {t_token}"}

    # Create course
    c_r = await client.post(
        "/api/v1/courses/",
        json={"title": "Quiz Course", "level": "beginner"},
        headers=t_headers,
    )
    course_id = c_r.json()["id"]
    await _meet_publish_requirements(db, course_id)

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
    s_token = await _register_and_login(client, "quiz_student@test.com", "StudQuiz123!", "student")
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


@pytest.mark.asyncio
async def test_publish_rejects_missing_requirements_with_actionable_errors(client, db):
    token = await _register_and_login(
        client, "publish_rules@test.com", "PublishRules123!", "teacher"
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post(
        "/api/v1/courses/", json={"title": "Publishing Rules Course"}, headers=headers
    )
    course_id = response.json()["id"]
    course = await db.get(Course, uuid.UUID(course_id))
    course.title = "   "
    await db.commit()

    rejected = await client.patch(
        f"/api/v1/courses/{course_id}", json={"status": "published"}, headers=headers
    )
    assert rejected.status_code == 422
    message = rejected.json()["message"]
    assert "nonempty course title" in message
    assert "course thumbnail" in message
    assert "at least one lesson" in message

    course.title = "Publishing Rules Course"
    course.thumbnail = "/static/test/thumb.png"
    db.add(
        Lesson(
            course_id=course.id,
            title="Ready video",
            video_url="/static/test/ready.mp4",
            video_status="ready",
        )
    )
    db.add(Lesson(course_id=course.id, title="Still processing", video_status="uploading"))
    await db.commit()
    published = await client.patch(
        f"/api/v1/courses/{course_id}", json={"status": "published"}, headers=headers
    )
    assert published.status_code == 200
    assert published.json()["status"] == "published"


@pytest.mark.asyncio
async def test_other_teacher_cannot_publish_course(client):
    owner = await _register_and_login(
        client, "publish_owner@test.com", "PublishOwner123!", "teacher"
    )
    course = await client.post(
        "/api/v1/courses/",
        json={"title": "Owned Draft"},
        headers={"Authorization": f"Bearer {owner}"},
    )
    other = await _register_and_login(
        client, "publish_other@test.com", "PublishOther123!", "teacher"
    )
    response = await client.patch(
        f"/api/v1/courses/{course.json()['id']}",
        json={"status": "published"},
        headers={"Authorization": f"Bearer {other}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_course_owner_can_preview_draft_while_students_follow_enrollment_rules(
    client: AsyncClient, db, admin_user
):
    owner_token = await _register_and_login(
        client, "owner_preview@test.com", "OwnerPreview123!", "teacher"
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    created = await client.post(
        "/api/v1/courses/", json={"title": "Owner Preview Course"}, headers=owner_headers
    )
    course_id = created.json()["id"]
    course = await db.get(Course, uuid.UUID(course_id))
    private_lesson = Lesson(
        course_id=course.id,
        title="Unpublished lesson",
        is_published=False,
        video_url="/static/private.mp4",
        video_status="ready",
    )
    public_lesson = Lesson(
        course_id=course.id,
        title="Published lesson",
        is_published=True,
        video_url="/static/public.mp4",
        video_status="ready",
    )
    db.add_all([private_lesson, public_lesson])
    await db.commit()

    assert (await client.get(f"/api/v1/courses/{course_id}", headers=owner_headers)).status_code == 200
    owner_list = await client.get(f"/api/v1/courses/{course_id}/lessons", headers=owner_headers)
    assert {lesson["id"] for lesson in owner_list.json()} == {
        str(private_lesson.id), str(public_lesson.id)
    }
    assert (await client.get(f"/api/v1/lessons/{private_lesson.id}", headers=owner_headers)).status_code == 200

    student_token = await _register_and_login(
        client, "preview_student@test.com", "PreviewStudent123!", "student"
    )
    student_headers = {"Authorization": f"Bearer {student_token}"}
    assert (await client.get(f"/api/v1/courses/{course_id}", headers=student_headers)).status_code == 404
    assert (await client.get(f"/api/v1/lessons/{private_lesson.id}", headers=student_headers)).status_code == 404

    course.status = CourseStatus.published
    course.thumbnail = "/static/course.png"
    await db.commit()
    student_list = await client.get(f"/api/v1/courses/{course_id}/lessons", headers=student_headers)
    assert [lesson["id"] for lesson in student_list.json()] == [str(public_lesson.id)]
    assert (await client.get(f"/api/v1/lessons/{public_lesson.id}", headers=student_headers)).status_code == 403
    enrolled = await client.post(
        "/api/v1/enrollments/", json={"course_id": course_id}, headers=student_headers
    )
    assert enrolled.status_code == 201
    assert (await client.get(f"/api/v1/lessons/{public_lesson.id}", headers=student_headers)).status_code == 200

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "TestPass123!"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    assert (await client.get(f"/api/v1/lessons/{private_lesson.id}", headers=admin_headers)).status_code == 200


@pytest.mark.asyncio
async def test_course_price_is_decimal_validated_and_paid_courses_cannot_publish_until_checkout(
    client: AsyncClient, db,
):
    token = await _register_and_login(
        client, "pricing_teacher@test.com", "PricingTeacher123!", "teacher"
    )
    headers = {"Authorization": f"Bearer {token}"}
    created = await client.post(
        "/api/v1/courses/",
        json={"title": "INR Pricing", "price": "1000.50", "currency": "INR"},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["price"] == 1000.5
    assert created.json()["currency"] == "INR"

    negative = await client.patch(
        f"/api/v1/courses/{created.json()['id']}", json={"price": "-1.00"}, headers=headers
    )
    assert negative.status_code == 422
    precision = await client.patch(
        f"/api/v1/courses/{created.json()['id']}", json={"price": "1.001"}, headers=headers
    )
    assert precision.status_code == 422
    unsupported = await client.patch(
        f"/api/v1/courses/{created.json()['id']}", json={"currency": "USD"}, headers=headers
    )
    assert unsupported.status_code == 422

    await _meet_publish_requirements(db, created.json()["id"])
    publish = await client.patch(
        f"/api/v1/courses/{created.json()['id']}",
        json={"status": "published"},
        headers=headers,
    )
    assert publish.status_code == 422
    assert "Paid-course publishing is disabled" in publish.json()["message"]

    free_price = await client.patch(
        f"/api/v1/courses/{created.json()['id']}", json={"price": "0.00"}, headers=headers
    )
    assert free_price.status_code == 200
    published = await client.patch(
        f"/api/v1/courses/{created.json()['id']}",
        json={"status": "published"},
        headers=headers,
    )
    assert published.status_code == 200
    paid_price_after_publish = await client.patch(
        f"/api/v1/courses/{created.json()['id']}", json={"price": "5.00"}, headers=headers
    )
    assert paid_price_after_publish.status_code == 422

    invalid_thumbnail = await client.patch(
        f"/api/v1/courses/{created.json()['id']}",
        json={"thumbnail": "https://attacker.invalid/image.png"},
        headers=headers,
    )
    assert invalid_thumbnail.status_code == 422
