import pytest
from httpx import AsyncClient
import uuid

from app.models.course import Course, CourseStatus
from app.models.lesson import Lesson
from app.services import upload_service


class FakeStorage:
    def __init__(self):
        self.head_keys = []
        self.deleted = []

    async def presign_put(self, key, mime_type, size_bytes, expires_in):
        return f"https://private-r2.test/{key}?signed=put"

    async def head(self, key):
        self.head_keys.append(key)
        return {"ContentLength": 123, "ContentType": "video/mp4"}

    async def delete(self, key):
        self.deleted.append(key)


async def register_teacher(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Upload Teacher",
            "email": email,
            "password": "UploadPass123!",
            "role": "teacher",
        },
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "UploadPass123!"}
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_presigned_video_upload_verifies_object_and_cancellation_does_not_fake_ready(
    client: AsyncClient, db, monkeypatch
):
    fake_storage = FakeStorage()
    monkeypatch.setattr(upload_service, "get_object_storage", lambda: fake_storage)
    token = await register_teacher(client, "direct_upload_owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    course = await client.post(
        "/api/v1/courses/", json={"title": "Direct Upload Course"}, headers=headers
    )
    lesson_response = await client.post(
        f"/api/v1/courses/{course.json()['id']}/lessons",
        json={"title": "Upload Lesson"},
        headers=headers,
    )
    lesson_id = lesson_response.json()["id"]
    start = await client.post(
        "/api/v1/uploads/presign",
        json={
            "resource_type": "lesson",
            "resource_id": lesson_id,
            "asset_type": "video",
            "mime_type": "video/mp4",
            "size_bytes": 123,
        },
        headers=headers,
    )
    assert start.status_code == 200
    grant = start.json()
    assert "key" not in grant and "object_key" not in grant
    lesson = await db.get(Lesson, uuid.UUID(lesson_id))
    assert lesson.video_status == "uploading"

    complete = await client.post(
        "/api/v1/uploads/complete",
        json={"upload_token": grant["upload_token"], "key": "arbitrary/other/key"},
        headers=headers,
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "ready"
    assert lesson.video_status == "ready"
    assert lesson.video_url == f"r2://{fake_storage.head_keys[0]}"

    second = await client.post(
        "/api/v1/uploads/presign",
        json={
            "resource_type": "lesson",
            "resource_id": lesson_id,
            "asset_type": "video",
            "mime_type": "video/mp4",
            "size_bytes": 123,
        },
        headers=headers,
    )
    cancel = await client.post(
        "/api/v1/uploads/cancel",
        json={"upload_token": second.json()["upload_token"]},
        headers=headers,
    )
    assert cancel.status_code == 200
    assert lesson.video_status == "ready"  # The previous verified video remains available.

    stale_completion = await client.post(
        "/api/v1/uploads/complete",
        json={"upload_token": second.json()["upload_token"]},
        headers=headers,
    )
    assert stale_completion.status_code == 403


@pytest.mark.asyncio
async def test_paid_course_media_is_denied_without_purchase_support(client, db):
    owner_token = await register_teacher(client, "paid_media_owner@test.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    course_response = await client.post(
        "/api/v1/courses/", json={"title": "Paid Course"}, headers=owner_headers
    )
    course_id = course_response.json()["id"]
    course = await db.get(Course, uuid.UUID(course_id))
    course.thumbnail = "r2://test/paid-thumb.jpg"
    course.price = 12.50
    course.status = CourseStatus.published
    lesson = Lesson(
        course_id=course.id,
        title="Paid Video",
        is_published=True,
        video_url="r2://test/paid-video.mp4",
        video_status="ready",
    )
    db.add(lesson)
    await db.commit()

    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Student",
            "email": "paid_media_student@test.com",
            "password": "StudentPass123!",
            "role": "student",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "paid_media_student@test.com", "password": "StudentPass123!"},
    )
    student_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    enrollment = await client.post(
        "/api/v1/enrollments/", json={"course_id": course_id}, headers=student_headers
    )
    assert enrollment.status_code == 403
    lesson_read = await client.get(f"/api/v1/lessons/{lesson.id}", headers=student_headers)
    assert lesson_read.status_code == 403


@pytest.mark.asyncio
async def test_upload_grant_cannot_be_started_for_another_teachers_lesson(client: AsyncClient):
    owner_token = await register_teacher(client, "direct_upload_owner2@test.com")
    course = await client.post(
        "/api/v1/courses/",
        json={"title": "Owned Upload Course"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    lesson = await client.post(
        f"/api/v1/courses/{course.json()['id']}/lessons",
        json={"title": "Owned Upload Lesson"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    other_token = await register_teacher(client, "direct_upload_other@test.com")
    response = await client.post(
        "/api/v1/uploads/presign",
        json={
            "resource_type": "lesson",
            "resource_id": lesson.json()["id"],
            "asset_type": "video",
            "mime_type": "video/mp4",
            "size_bytes": 123,
        },
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403
