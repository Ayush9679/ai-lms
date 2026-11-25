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
        self.objects = {}
        self.multipart_uploads = {}
        self.completed_parts = {}
        self.aborted_uploads = []

    async def presign_put(self, key, mime_type, size_bytes, expires_in):
        self.objects[key] = {"mime_type": mime_type, "size": size_bytes}
        return f"https://private-r2.test/{key}?signed=put"

    async def create_multipart_upload(self, key, mime_type):
        upload_id = f"multipart-{len(self.multipart_uploads) + 1}"
        self.multipart_uploads[key] = {"upload_id": upload_id, "mime_type": mime_type}
        return upload_id

    async def presign_upload_part(self, key, upload_id, part_number, expires_in):
        return f"https://private-r2.test/{key}?part={part_number}"

    async def complete_multipart_upload(self, key, upload_id, parts):
        self.completed_parts[key] = parts

    async def abort_multipart_upload(self, key, upload_id):
        self.aborted_uploads.append((key, upload_id))

    async def set_uploaded_object(self, key, mime_type, size_bytes):
        self.objects[key] = {"mime_type": mime_type, "size": size_bytes}

    async def head(self, key):
        self.head_keys.append(key)
        obj = self.objects[key]
        return {"ContentLength": obj["size"], "ContentType": obj["mime_type"]}

    async def read_prefix(self, key, length=32):
        if "prefix" in self.objects[key]:
            return self.objects[key]["prefix"][:length]
        mime_type = self.objects[key]["mime_type"]
        signatures = {
            "video/mp4": b"\x00\x00\x00\x18ftypisom",
            "image/png": b"\x89PNG\r\n\x1a\n",
            "image/jpeg": b"\xff\xd8\xff\xe0",
            "image/webp": b"RIFF\x00\x00\x00\x00WEBP",
            "image/gif": b"GIF89a",
            "application/pdf": b"%PDF-1.7",
        }
        return signatures[mime_type][:length]

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
    assert grant["upload_method"] == "put"
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
    assert lesson.video_size_bytes == 123

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
async def test_multipart_video_is_not_ready_until_verified_and_cancellation_aborts(
    client: AsyncClient, db, monkeypatch
):
    fake_storage = FakeStorage()
    monkeypatch.setattr(upload_service, "get_object_storage", lambda: fake_storage)
    token = await register_teacher(client, "multipart_upload_owner@test.com")
    headers = {"Authorization": "Bearer " + token}
    course = await client.post(
        "/api/v1/courses/", json={"title": "Multipart Course"}, headers=headers
    )
    assert course.status_code == 201, course.text
    lesson_response = await client.post(
        f"/api/v1/courses/{course.json()['id']}/lessons",
        json={"title": "Multipart Lesson"},
        headers=headers,
    )
    lesson = await db.get(Lesson, uuid.UUID(lesson_response.json()["id"]))
    size_bytes = 65 * 1024 * 1024
    start = await client.post(
        "/api/v1/uploads/presign",
        json={
            "resource_type": "lesson",
            "resource_id": str(lesson.id),
            "asset_type": "video",
            "mime_type": "video/mp4",
            "size_bytes": size_bytes,
        },
        headers=headers,
    )
    assert start.status_code == 200
    grant = start.json()
    assert grant["upload_method"] == "multipart"
    assert grant["part_size_bytes"] == 64 * 1024 * 1024
    assert [part["part_number"] for part in grant["parts"]] == [1, 2]
    assert lesson.video_status == "uploading"
    assert lesson.video_url is None

    key = next(iter(fake_storage.multipart_uploads))
    await fake_storage.set_uploaded_object(key, "video/mp4", size_bytes)
    complete = await client.post(
        "/api/v1/uploads/complete",
        json={
            "upload_token": grant["upload_token"],
            "parts": [
                {"part_number": 1, "etag": '"part-one"'},
                {"part_number": 2, "etag": '"part-two"'},
            ],
        },
        headers=headers,
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "ready"
    assert fake_storage.completed_parts[key] == [
        {"PartNumber": 1, "ETag": '"part-one"'},
        {"PartNumber": 2, "ETag": '"part-two"'},
    ]
    assert lesson.video_status == "ready"
    assert lesson.video_url == f"r2://{key}"

    existing_multipart_keys = set(fake_storage.multipart_uploads)
    cancel_start = await client.post(
        "/api/v1/uploads/presign",
        json={
            "resource_type": "lesson",
            "resource_id": str(lesson.id),
            "asset_type": "video",
            "mime_type": "video/mp4",
            "size_bytes": size_bytes,
        },
        headers=headers,
    )
    cancel_grant = cancel_start.json()
    cancel_key = next(key for key in fake_storage.multipart_uploads if key not in existing_multipart_keys)
    canceled = await client.post(
        "/api/v1/uploads/cancel",
        json={"upload_token": cancel_grant["upload_token"]},
        headers=headers,
    )
    assert canceled.status_code == 200
    assert cancel_key in [key for key, _ in fake_storage.aborted_uploads]
    assert lesson.video_status == "ready"


@pytest.mark.asyncio
async def test_lesson_upload_only_allows_mp4_and_pdf_and_limits_pdf_to_2048_mb(client: AsyncClient):
    token = await register_teacher(client, "upload_validation_owner@test.com")
    headers = {"Authorization": "Bearer " + token}
    course = await client.post(
        "/api/v1/courses/", json={"title": "Validation Course"}, headers=headers
    )
    assert course.status_code == 201, course.text
    lesson = await client.post(
        f"/api/v1/courses/{course.json()['id']}/lessons",
        json={"title": "Validation Lesson"},
        headers=headers,
    )

    webm = await client.post(
        "/api/v1/uploads/presign",
        json={
            "resource_type": "lesson",
            "resource_id": lesson.json()["id"],
            "asset_type": "video",
            "mime_type": "video/webm",
            "size_bytes": 100,
        },
        headers=headers,
    )
    assert webm.status_code == 415

    large_pdf = await client.post(
        "/api/v1/uploads/presign",
        json={
            "resource_type": "lesson",
            "resource_id": lesson.json()["id"],
            "asset_type": "pdf",
            "mime_type": "application/pdf",
            "size_bytes": 2048 * 1024 * 1024 + 1,
        },
        headers=headers,
    )
    assert large_pdf.status_code == 422


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
async def test_course_thumbnail_upload_persists_replaces_and_clears_private_object(
    client: AsyncClient, db, monkeypatch
):
    fake_storage = FakeStorage()
    monkeypatch.setattr(upload_service, "get_object_storage", lambda: fake_storage)
    from app.services import file_service
    from app.api.v1 import courses as courses_api

    monkeypatch.setattr(file_service, "get_object_storage", lambda: fake_storage)
    monkeypatch.setattr(courses_api, "get_object_storage", lambda: fake_storage)

    async def signed_url(self, stored_path):
        if stored_path and stored_path.startswith("r2://"):
            return f"https://private-r2.test/get/{stored_path.removeprefix('r2://')}?signed=get"
        return stored_path

    monkeypatch.setattr(courses_api.FileService, "resolve_url", signed_url)
    token = await register_teacher(client, "thumbnail_owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = await client.post(
        "/api/v1/courses/", json={"title": "Thumbnail Course"}, headers=headers
    )
    course_id = created.json()["id"]

    async def upload_png():
        presign = await client.post(
            "/api/v1/uploads/presign",
            json={
                "resource_type": "course",
                "resource_id": course_id,
                "asset_type": "thumbnail",
                "mime_type": "image/png",
                "size_bytes": 8,
            },
            headers=headers,
        )
        assert presign.status_code == 200
        return presign.json()

    first = await upload_png()
    completed = await client.post(
        "/api/v1/uploads/complete",
        json={"upload_token": first["upload_token"]},
        headers=headers,
    )
    assert completed.status_code == 200
    detail = await client.get(f"/api/v1/courses/{course_id}", headers=headers)
    first_key = detail.json()["thumbnail"].split("/get/", 1)[1].split("?", 1)[0]
    assert first_key.startswith(f"courses/{course_id}/thumbnail/")

    second = await upload_png()
    replaced = await client.post(
        "/api/v1/uploads/complete",
        json={"upload_token": second["upload_token"]},
        headers=headers,
    )
    assert replaced.status_code == 200
    assert first_key in fake_storage.deleted

    removed = await client.patch(
        f"/api/v1/courses/{course_id}", json={"thumbnail": None}, headers=headers
    )
    assert removed.status_code == 200
    assert removed.json()["thumbnail"] is None
    assert (await client.get(f"/api/v1/courses/{course_id}", headers=headers)).json()["thumbnail"] is None


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


@pytest.mark.asyncio
async def test_failed_video_verification_is_not_marked_ready(client: AsyncClient, db, monkeypatch):
    fake_storage = FakeStorage()
    monkeypatch.setattr(upload_service, "get_object_storage", lambda: fake_storage)
    token = await register_teacher(client, "failed_video_owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    course = await client.post("/api/v1/courses/", json={"title": "Failed Video"}, headers=headers)
    lesson_response = await client.post(
        f"/api/v1/courses/{course.json()['id']}/lessons",
        json={"title": "Bad Video"},
        headers=headers,
    )
    lesson = await db.get(Lesson, uuid.UUID(lesson_response.json()["id"]))
    grant_response = await client.post(
        "/api/v1/uploads/presign",
        json={
            "resource_type": "lesson",
            "resource_id": str(lesson.id),
            "asset_type": "video",
            "mime_type": "video/mp4",
            "size_bytes": 123,
        },
        headers=headers,
    )
    key = next(iter(fake_storage.objects))
    fake_storage.objects[key]["prefix"] = b"this is not an MP4"
    completed = await client.post(
        "/api/v1/uploads/complete",
        json={"upload_token": grant_response.json()["upload_token"]},
        headers=headers,
    )
    assert completed.status_code == 422
    assert lesson.video_status == "failed"
    assert lesson.video_url is None


@pytest.mark.asyncio
async def test_failed_put_can_be_distinguished_from_user_cancellation(client: AsyncClient, db, monkeypatch):
    fake_storage = FakeStorage()
    monkeypatch.setattr(upload_service, "get_object_storage", lambda: fake_storage)
    token = await register_teacher(client, "cancel_video_owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    course = await client.post("/api/v1/courses/", json={"title": "Cancel Video"}, headers=headers)
    lesson_response = await client.post(
        f"/api/v1/courses/{course.json()['id']}/lessons",
        json={"title": "Cancelled Video"},
        headers=headers,
    )
    lesson = await db.get(Lesson, uuid.UUID(lesson_response.json()["id"]))
    grant_response = await client.post(
        "/api/v1/uploads/presign",
        json={
            "resource_type": "lesson",
            "resource_id": str(lesson.id),
            "asset_type": "video",
            "mime_type": "video/mp4",
            "size_bytes": 123,
        },
        headers=headers,
    )
    response = await client.post(
        "/api/v1/uploads/cancel",
        json={"upload_token": grant_response.json()["upload_token"], "failed": True},
        headers=headers,
    )
    assert response.status_code == 200
    assert lesson.video_status == "failed"


@pytest.mark.asyncio
async def test_teacher_can_delete_video_through_lesson_patch(client: AsyncClient, db, monkeypatch):
    fake_storage = FakeStorage()
    from app.api.v1 import lessons as lessons_api

    monkeypatch.setattr(lessons_api, "get_object_storage", lambda: fake_storage)
    token = await register_teacher(client, "delete_video_owner@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    course = await client.post("/api/v1/courses/", json={"title": "Delete Video"}, headers=headers)
    lesson_response = await client.post(
        f"/api/v1/courses/{course.json()['id']}/lessons",
        json={"title": "Video To Delete"},
        headers=headers,
    )
    lesson = await db.get(Lesson, uuid.UUID(lesson_response.json()["id"]))
    lesson.video_url = "r2://lessons/lesson/video/old.mp4"
    lesson.video_status = "ready"
    lesson.video_size_bytes = 123
    await db.commit()

    removed = await client.patch(
        f"/api/v1/lessons/{lesson.id}", json={"video_url": None}, headers=headers
    )
    assert removed.status_code == 200
    assert removed.json()["video_url"] is None
    assert removed.json()["video_status"] == "pending"
    assert removed.json()["video_size_bytes"] is None
    assert fake_storage.deleted == ["lessons/lesson/video/old.mp4"]
