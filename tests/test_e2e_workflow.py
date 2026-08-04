import io
import pytest
from httpx import AsyncClient
from app.models.user import User


async def _register_and_login(client, email, password, role="teacher"):
    await client.post(
        "/api/v1/auth/register",
        json={"full_name": "E2E User", "email": email, "password": password, "role": role},
    )
    r = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_complete_e2e_workflow(client: AsyncClient, admin_user: User):
    # 1. Teacher Register & Login
    t_token = await _register_and_login(client, "e2eteacher@test.com", "TeachPass123!", "teacher")
    t_headers = {"Authorization": f"Bearer {t_token}"}

    # 2. Create Course
    c_res = await client.post(
        "/api/v1/courses/",
        json={
            "title": "E2E Quality Course",
            "description": "Learn E2E testing standard practices",
            "category": "Testing",
            "level": "intermediate",
            "price": 0.0,
        },
        headers=t_headers,
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    # 3. Upload Thumbnail
    thumbnail_data = b"dummy_thumbnail_data"
    thumbnail_file = {"file": ("thumbnail.png", io.BytesIO(thumbnail_data), "image/png")}
    thumb_res = await client.post(
        f"/api/v1/courses/{course_id}/thumbnail",
        files=thumbnail_file,
        headers=t_headers,
    )
    assert thumb_res.status_code == 200

    # 4. Upload Lesson
    l_res = await client.post(
        f"/api/v1/courses/{course_id}/lessons",
        json={
            "title": "Introduction to E2E Testing",
            "content": "In this lesson we learn how E2E testing ensures quality.",
            "order_index": 1,
            "is_published": True,
        },
        headers=t_headers,
    )
    assert l_res.status_code == 201
    lesson_id = l_res.json()["id"]

    # 5. Upload PDF to Lesson
    pdf_data = b"dummy_pdf_data"
    pdf_file = {"file": ("lesson_guide.pdf", io.BytesIO(pdf_data), "application/pdf")}
    pdf_res = await client.post(
        f"/api/v1/lessons/{lesson_id}/pdf",
        files=pdf_file,
        headers=t_headers,
    )
    assert pdf_res.status_code == 200

    # 6. Upload Assignment to Course
    asg_res = await client.post(
        f"/api/v1/courses/{course_id}/assignments",
        json={
            "title": "E2E Homework 1",
            "description": "Write a short summary of E2E testing principles.",
            "instructions": "Submit in PDF or plain text.",
            "max_marks": 10.0,
            "passing_marks": 4.0,
            "due_date": "2026-12-31T23:59:59Z",
        },
        headers=t_headers,
    )
    assert asg_res.status_code == 201
    assignment_id = asg_res.json()["id"]

    # 7. Generate AI Quiz
    quiz_res = await client.post(
        f"/api/v1/courses/{course_id}/quizzes/ai-generate",
        json={
            "source_type": "text",
            "source_text": "Photosynthesis is the process by which green plants use sunlight to synthesize nutrients.",
            "num_questions": 3,
            "difficulty": "medium",
            "title": "Photosynthesis Quiz",
        },
        headers=t_headers,
    )
    assert quiz_res.status_code == 201
    quiz_id = quiz_res.json()["id"]
    question_ids = [q["id"] for q in quiz_res.json()["questions"]]

    # 8. Publish Course
    pub_res = await client.patch(
        f"/api/v1/courses/{course_id}",
        json={"status": "published"},
        headers=t_headers,
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "published"

    # 9. Student Register & Login
    s_token = await _register_and_login(client, "e2estudent@test.com", "StudPass123!", "student")
    s_headers = {"Authorization": f"Bearer {s_token}"}

    # 10. Browse Courses & Verify course appears
    browse_res = await client.get("/api/v1/courses/")
    assert browse_res.status_code == 200
    items = browse_res.json()["items"]
    assert any(item["id"] == course_id for item in items)

    # 11. Enroll in course
    enroll_res = await client.post(
        "/api/v1/enrollments/",
        json={"course_id": course_id},
        headers=s_headers,
    )
    assert enroll_res.status_code == 201

    # 12. Open lesson & Verify Details
    get_lesson_res = await client.get(
        f"/api/v1/lessons/{lesson_id}",
        headers=s_headers,
    )
    assert get_lesson_res.status_code == 200
    assert get_lesson_res.json()["title"] == "Introduction to E2E Testing"

    # 13. Update lesson progress (Mark as completed)
    progress_res = await client.post(
        f"/api/v1/lessons/{lesson_id}/progress",
        json={
            "is_completed": True,
            "watch_time_seconds": 120,
            "completion_percentage": 100.0,
        },
        headers=s_headers,
    )
    assert progress_res.status_code == 200
    assert progress_res.json()["is_completed"] is True

    # 14. Submit Assignment
    sub_res = await client.post(
        f"/api/v1/assignments/{assignment_id}/submit",
        json={"text_content": "Here is my E2E testing assignment submission text."},
        headers=s_headers,
    )
    assert sub_res.status_code == 201
    submission_id = sub_res.json()["id"]

    # 15. Attempt Quiz
    answers_payload = [{"question_id": q_id, "given_answer": "True"} for q_id in question_ids]
    attempt_res = await client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts",
        json={
            "answers": answers_payload,
            "time_taken_seconds": 30,
        },
        headers=s_headers,
    )
    assert attempt_res.status_code == 201

    # 16. Use AI Tutor
    tutor_res = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Can you explain lexicals?"},
        headers=s_headers,
    )
    assert tutor_res.status_code == 200
    assert "ai_response" in tutor_res.json()

    # 17. Generate Notes
    notes_res = await client.post(
        "/api/v1/ai/notes/generate",
        json={
            "source_type": "text",
            "source_text": "Sample text content to generate notes from.",
            "title": "E2E Study Notes",
        },
        headers=s_headers,
    )
    assert notes_res.status_code == 201

    # 18. Generate Summary
    sum_res = await client.post(
        "/api/v1/ai/summarize",
        json={
            "source_type": "text",
            "source_text": "Sample text content to summarize.",
            "length": "short",
        },
        headers=s_headers,
    )
    assert sum_res.status_code == 200

    # 19. Generate Flashcards
    fc_res = await client.post(
        "/api/v1/ai/flashcards/generate",
        json={
            "source_type": "text",
            "source_text": "Sample text content to generate flashcards.",
            "num_cards": 5,
            "title": "E2E Flashcards",
        },
        headers=s_headers,
    )
    assert fc_res.status_code == 201

    # 20. Generate Study Plan
    plan_res = await client.post(
        "/api/v1/ai/study-plan/generate",
        json={
            "topics": ["Testing", "E2E"],
            "duration_weeks": 2,
            "hours_per_day": 1,
        },
        headers=s_headers,
    )
    assert plan_res.status_code == 201

    # 21. Teacher Views Enrolled Students
    students_res = await client.get(
        f"/api/v1/enrollments/courses/{course_id}/students",
        headers=t_headers,
    )
    assert students_res.status_code == 200
    assert len(students_res.json()) == 1

    # 22. Teacher Grades Assignment
    grade_res = await client.patch(
        f"/api/v1/submissions/{submission_id}/grade",
        json={
            "marks_obtained": 9.5,
            "feedback": "Outstanding E2E testing concept analysis!",
        },
        headers=t_headers,
    )
    assert grade_res.status_code == 200

    # 23. Student Checks Dashboard & Submissions (verify marks, feedback)
    my_subs_res = await client.get(
        "/api/v1/my-submissions",
        headers=s_headers,
    )
    assert my_subs_res.status_code == 200
    sub_detail = next(sub for sub in my_subs_res.json() if sub["id"] == submission_id)
    assert sub_detail["marks_obtained"] == 9.5
    assert sub_detail["feedback"] == "Outstanding E2E testing concept analysis!"

    # 24. Student Dashboard Stats & Notifications
    student_db_res = await client.get(
        "/api/v1/dashboard/student",
        headers=s_headers,
    )
    assert student_db_res.status_code == 200
    db_data = student_db_res.json()
    assert db_data["progress_summary"]["total_courses"] == 1

    # 25. Admin Verification
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "TestPass123!"}
    )
    assert r.status_code == 200
    a_token = r.json()["access_token"]
    a_headers = {"Authorization": f"Bearer {a_token}"}

    admin_db_res = await client.get(
        "/api/v1/dashboard/admin",
        headers=a_headers,
    )
    assert admin_db_res.status_code == 200
    admin_metrics = admin_db_res.json()["metrics"]
    assert admin_metrics["total_courses"] >= 1
