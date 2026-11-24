"""Exercise the payment API with signed callbacks and a mocked Razorpay client."""

import hmac
import json
import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.api.v1 import payments
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.middleware.rate_limit import limiter
from app.models.course import Course, CourseStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.lesson import Lesson
from app.models.payment import Payment, PaymentOrder, WebhookEvent
from app.models.user import User, UserRole
from app.services import payment_service
from app.services import course_service
from app.services.lesson_service import LessonService

pytestmark = pytest.mark.asyncio
PREFIX = "/api/v1/payments"
KEY_SECRET = "mock-checkout-secret"
WEBHOOK_SECRET = "mock-webhook-secret"


def sign(body, secret):
    return hmac.digest(secret.encode(), body, "sha256").hex()


@pytest.fixture
async def checkout(client, db, monkeypatch):
    limiter.reset()
    student = User(
        email=f"{uuid.uuid4().hex}@example.com",
        full_name="Payment Student",
        hashed_password="unused",
        role=UserRole.student,
        is_active=True,
        is_verified=True,
    )
    teacher = User(
        email=f"{uuid.uuid4().hex}@example.com",
        full_name="Payment Teacher",
        hashed_password="unused",
        role=UserRole.teacher,
        is_active=True,
        is_verified=True,
    )
    db.add_all([student, teacher])
    await db.flush()
    course = Course(
        title="Paid course",
        slug=uuid.uuid4().hex,
        instructor_id=teacher.id,
        price=Decimal("1000.00"),
        currency="INR",
        status=CourseStatus.published,
    )
    db.add(course)
    await db.commit()

    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY="test-secret-" * 4,
        DEBUG=False,
        RAZORPAY_ENABLED=True,
        RAZORPAY_TEST_MODE=True,
        RAZORPAY_KEY_ID="rzp_test_mock",
        RAZORPAY_KEY_SECRET=KEY_SECRET,
        RAZORPAY_WEBHOOK_SECRET=WEBHOOK_SECRET,
        PLATFORM_COMMISSION_PERCENT=10,
    )
    monkeypatch.setattr(payments, "get_settings", lambda: settings)
    monkeypatch.setattr(course_service, "get_settings", lambda: settings)
    order_id = f"order_{uuid.uuid4().hex}"
    payment_id = f"pay_{uuid.uuid4().hex}"
    remote = {
        "id": payment_id,
        "order_id": order_id,
        "status": "captured",
        "captured": True,
        "amount": 100000,
        "currency": "INR",
        "fee": 2400,
    }
    gateway = SimpleNamespace(order=Mock(), payment=Mock())
    gateway.order.create.return_value = {"id": order_id, "amount": 100000, "currency": "INR"}
    gateway.payment.fetch.return_value = remote
    remote_order = {
        "id": order_id,
        "status": "paid",
        "attempts": 1,
        "amount": 100000,
        "amount_paid": 100000,
        "amount_due": 0,
        "currency": "INR",
    }
    gateway.order.fetch.side_effect = lambda *_args, **_kwargs: {
        "receipt": gateway.order.create.call_args.args[0]["receipt"],
        **remote_order,
    }
    gateway.order.payments.return_value = {"count": 1, "items": [remote.copy()]}
    monkeypatch.setattr(payment_service, "make_gateway", lambda _: gateway)
    headers = {"Authorization": f"Bearer {create_access_token(student.id, student.role.value)}"}

    async def create(**extra):
        data = {"course_id": str(course.id), **extra}
        return await client.post(f"{PREFIX}/create-order", json=data, headers=headers)

    async def verify(signature=None, auth=None):
        return await client.post(
            f"{PREFIX}/verify",
            json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
                or sign(f"{order_id}|{payment_id}".encode(), KEY_SECRET),
            },
            headers=headers if auth is None else auth,
        )

    async def recover(auth=None, **extra):
        return await client.post(
            f"{PREFIX}/status",
            json={"razorpay_order_id": order_id, **extra},
            headers=headers if auth is None else auth,
        )

    async def webhook(event_type, event_id=None, signature=None):
        body = json.dumps(
            {
                "event": event_type,
                "payload": {
                    "payment": {"entity": {"order_id": order_id, "id": payment_id}},
                    "order": {"entity": {"id": order_id}},
                },
            }
        ).encode()
        return await client.post(
            f"{PREFIX}/webhook",
            content=body,
            headers={
                "X-Razorpay-Event-Id": event_id or uuid.uuid4().hex,
                "X-Razorpay-Signature": signature or sign(body, WEBHOOK_SECRET),
            },
        )

    yield SimpleNamespace(
        create=create,
        verify=verify,
        recover=recover,
        webhook=webhook,
        gateway=gateway,
        remote=remote,
        remote_order=remote_order,
        course=course,
        student=student,
        teacher=teacher,
        order_id=order_id,
        payment_id=payment_id,
        settings=settings,
    )
    limiter.reset()


async def test_order_uses_server_price_and_reuses_order(checkout):
    assert (await checkout.create(amount=1, currency="USD")).status_code == 422
    first = await checkout.create()
    assert first.status_code == 200, first.text
    assert first.json() == {
        "razorpay_key_id": "rzp_test_mock",
        "razorpay_order_id": checkout.order_id,
        "amount": 100000,
        "currency": "INR",
    }
    assert (await checkout.create()).json() == first.json()
    checkout.gateway.order.create.assert_called_once()
    assert checkout.gateway.order.create.call_args.args[0]["amount"] == 100000


@pytest.mark.parametrize(
    ("condition", "expected"),
    [("unknown", 404), ("draft", 404), ("free", 400), ("owner", 403), ("enrolled", 409)],
)
async def test_order_rejects_ineligible_course(checkout, db, condition, expected):
    extra = {}
    if condition == "unknown":
        extra["course_id"] = str(uuid.uuid4())
    elif condition == "draft":
        checkout.course.status = CourseStatus.draft
    elif condition == "free":
        checkout.course.price = Decimal("0")
    elif condition == "owner":
        checkout.course.instructor_id = checkout.student.id
    else:
        db.add(Enrollment(student_id=checkout.student.id, course_id=checkout.course.id))
    await db.commit()
    assert (await checkout.create(**extra)).status_code == expected
    checkout.gateway.order.create.assert_not_called()


async def test_disabled_endpoints(checkout, monkeypatch):
    monkeypatch.setattr(
        payments,
        "get_settings",
        lambda: get_settings().model_copy(update={"RAZORPAY_ENABLED": False}),
    )
    assert (await checkout.create()).status_code == 404
    assert (await checkout.verify()).status_code == 404
    assert (await checkout.recover()).status_code == 404
    assert (await checkout.webhook("order.paid")).status_code == 404


@pytest.mark.parametrize(
    "updates",
    [
        {"RAZORPAY_KEY_ID": "rzp_live_example"},
        {"RAZORPAY_KEY_SECRET": ""},
        {"RAZORPAY_WEBHOOK_SECRET": ""},
        {"RAZORPAY_TEST_MODE": False},
    ],
)
async def test_enabled_settings_require_test_credentials(checkout, updates):
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, **(checkout.settings.model_dump() | updates))
    assert KEY_SECRET not in str(error.value)
    assert WEBHOOK_SECRET not in str(error.value)


async def test_test_mode_paid_publishing_preserves_media_requirements(checkout, db):
    requirements = await course_service.CourseService(db).get_publish_requirements(checkout.course)
    assert requirements == [
        "Upload a course thumbnail.",
        "Upload and verify video for at least one lesson.",
    ]


async def test_gateway_failure(checkout):
    checkout.gateway.order.create.side_effect = TimeoutError("provider detail")
    response = await checkout.create()
    assert response.status_code == 502
    assert "provider detail" not in response.text


async def test_verify_signature_and_order_ownership(checkout, db):
    assert (await checkout.create()).status_code == 200
    assert (await checkout.verify(signature="0" * 64)).status_code == 400
    assert (await checkout.verify(auth={})).status_code == 401
    checkout.teacher.role = UserRole.student
    await db.commit()
    token = create_access_token(checkout.teacher.id, UserRole.student.value)
    assert (await checkout.verify(auth={"Authorization": f"Bearer {token}"})).status_code == 404
    checkout.gateway.payment.fetch.assert_not_called()


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": "authorized", "captured": False},
        {"amount": 99999},
        {"currency": "USD"},
        {"order_id": "order_wrong"},
    ],
)
async def test_verify_rejects_mismatched_or_uncaptured_payment(checkout, db, overrides):
    assert (await checkout.create()).status_code == 200
    checkout.remote.update(overrides)
    assert (await checkout.verify()).status_code == 409
    order = await db.scalar(
        select(PaymentOrder).where(PaymentOrder.razorpay_order_id == checkout.order_id)
    )
    assert await db.scalar(select(Payment).where(Payment.order_id == order.id)) is None
    assert (
        await db.scalar(select(Enrollment).where(Enrollment.course_id == checkout.course.id))
        is None
    )


async def test_capture_credits_once_and_unlocks_lesson(checkout, db):
    from app.core.exceptions import ForbiddenError

    lesson = Lesson(course_id=checkout.course.id, title="Paid lesson", is_published=True)
    db.add(lesson)
    await db.commit()
    service = LessonService(db)
    with pytest.raises(ForbiddenError):
        await service.get_lesson_for_user(lesson.id, checkout.student.id, UserRole.student)

    assert (await checkout.create()).status_code == 200
    assert (await checkout.verify()).json() == {
        "status": "captured",
        "razorpay_payment_id": checkout.payment_id,
    }
    assert (await checkout.verify()).status_code == 200
    assert (await checkout.webhook("payment.captured")).status_code == 200
    checkout.gateway.payment.fetch.assert_called_once()
    payment = await db.scalar(
        select(Payment).where(Payment.razorpay_payment_id == checkout.payment_id)
    )
    assert (payment.platform_commission_paise, payment.teacher_earnings_paise) == (10000, 90000)
    assert payment.gateway_fee_paise == 2400
    enrollments = list(
        await db.scalars(select(Enrollment).where(Enrollment.course_id == checkout.course.id))
    )
    assert len(enrollments) == 1
    assert enrollments[0].status == EnrollmentStatus.active
    assert (
        await service.get_lesson_for_user(lesson.id, checkout.student.id, UserRole.student)
        == lesson
    )


async def test_webhook_signature_retry_deduplication_and_late_failure(checkout, db):
    assert (await checkout.create()).status_code == 200
    order = await db.scalar(
        select(PaymentOrder).where(PaymentOrder.razorpay_order_id == checkout.order_id)
    )
    assert (await checkout.webhook("payment.failed", signature="0" * 64)).status_code == 400
    assert (await checkout.webhook("payment.failed")).status_code == 200
    assert order.status == "failed"
    assert await db.scalar(select(Payment).where(Payment.order_id == order.id)) is None

    event_id = uuid.uuid4().hex
    assert (await checkout.webhook("order.paid", event_id)).status_code == 200
    assert (await checkout.webhook("order.paid", event_id)).status_code == 200
    assert (await checkout.webhook("payment.failed")).status_code == 200
    assert order.status == "paid"
    assert (
        await db.scalar(
            select(func.count(WebhookEvent.id)).where(WebhookEvent.provider_event_id == event_id)
        )
        == 1
    )
    checkout.gateway.payment.fetch.assert_called_once()


async def test_capture_webhook_can_retry_after_provider_failure(checkout, db):
    assert (await checkout.create()).status_code == 200
    event_id = uuid.uuid4().hex
    checkout.gateway.payment.fetch.side_effect = TimeoutError
    assert (await checkout.webhook("payment.captured", event_id)).status_code == 502
    # The shared client fixture bypasses get_db's production rollback handler.
    await db.rollback()
    assert (
        await db.scalar(select(WebhookEvent.id).where(WebhookEvent.provider_event_id == event_id))
        is None
    )
    checkout.gateway.payment.fetch.side_effect = None
    assert (await checkout.webhook("payment.captured", event_id)).status_code == 200
    assert (
        await db.scalar(select(Payment).where(Payment.razorpay_payment_id == checkout.payment_id))
        is not None
    )


async def test_recovery_requires_student_and_hides_other_orders(checkout, db):
    assert (await checkout.create()).status_code == 200
    assert (await checkout.recover(auth={})).status_code == 401
    teacher_token = create_access_token(checkout.teacher.id, UserRole.teacher.value)
    assert (
        await checkout.recover(auth={"Authorization": f"Bearer {teacher_token}"})
    ).status_code == 403

    checkout.teacher.role = UserRole.student
    await db.commit()
    token = create_access_token(checkout.teacher.id, UserRole.student.value)
    auth = {"Authorization": f"Bearer {token}"}
    other = await checkout.recover(auth=auth)
    missing = await checkout.recover(auth=auth, razorpay_order_id="order_missing")
    assert other.status_code == missing.status_code == 404
    assert other.json() == missing.json()
    assert (await checkout.recover(razorpay_payment_id=checkout.payment_id)).status_code == 422
    checkout.gateway.order.fetch.assert_not_called()


async def test_recovery_records_capture_once_and_interoperates_with_verify_and_webhook(
    checkout, db
):
    assert (await checkout.create()).status_code == 200
    first = await checkout.recover()
    assert first.status_code == 200, first.text
    assert first.headers["Cache-Control"] == "no-store"
    assert first.json() == {
        "razorpay_order_id": checkout.order_id,
        "course_id": str(checkout.course.id),
        "status": "enrolled",
        "safe_to_retry": False,
        "attempt_status": None,
    }
    assert (await checkout.recover()).json() == first.json()
    assert (await checkout.verify()).status_code == 200
    assert (await checkout.webhook("payment.captured")).status_code == 200
    checkout.gateway.order.fetch.assert_called_once_with(checkout.order_id, timeout=10)
    checkout.gateway.order.payments.assert_called_once_with(checkout.order_id, timeout=10)
    checkout.gateway.payment.fetch.assert_called_once_with(checkout.payment_id, timeout=10)
    assert (
        await db.scalar(
            select(func.count(Payment.id)).where(Payment.razorpay_payment_id == checkout.payment_id)
        )
        == 1
    )
    enrollment = await db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == checkout.student.id,
            Enrollment.course_id == checkout.course.id,
        )
    )
    assert enrollment.status == EnrollmentStatus.active

    enrollment.status = EnrollmentStatus.dropped
    await db.commit()
    body = (await checkout.recover()).json()
    assert body["status"] == "captured"
    assert body["safe_to_retry"] is False
    assert enrollment.status == EnrollmentStatus.dropped
    checkout.gateway.order.fetch.assert_called_once()


@pytest.mark.parametrize(
    ("attempt", "expected_status", "expected_attempt"),
    [
        ("created", "pending", None),
        ("authorized", "authorized", None),
        ("failed", "pending", "failed"),
    ],
)
async def test_unsettled_recovery_never_enrolls(
    checkout, db, attempt, expected_status, expected_attempt
):
    assert (await checkout.create()).status_code == 200
    checkout.remote_order.update(status="attempted", amount_paid=0, amount_due=100000)
    checkout.gateway.order.payments.return_value["items"][0].update(status=attempt, captured=False)
    body = (await checkout.recover()).json()
    assert body["status"] == expected_status
    assert body["safe_to_retry"] is False
    assert body["attempt_status"] == expected_attempt
    checkout.gateway.payment.fetch.assert_not_called()
    assert (
        await db.scalar(select(Enrollment.id).where(Enrollment.course_id == checkout.course.id))
        is None
    )


async def test_recovery_reopens_only_an_unattempted_existing_order(checkout, db):
    assert (await checkout.create()).status_code == 200
    checkout.remote_order.update(status="created", attempts=0, amount_paid=0, amount_due=100000)
    checkout.gateway.order.payments.return_value = {"count": 0, "items": []}
    body = (await checkout.recover()).json()
    assert body["status"] == "created"
    assert body["safe_to_retry"] is True
    assert (await checkout.create()).json()["razorpay_order_id"] == checkout.order_id
    checkout.gateway.order.create.assert_called_once()

    checkout.course.price = Decimal("2000.00")
    await db.commit()
    assert (await checkout.recover()).json()["safe_to_retry"] is False


async def test_conflicting_gateway_snapshots_do_not_allow_another_checkout(checkout):
    assert (await checkout.create()).status_code == 200
    checkout.remote_order.update(status="created", attempts=0, amount_paid=0, amount_due=100000)
    body = (await checkout.recover()).json()
    assert body["status"] == "pending"
    assert body["safe_to_retry"] is False
    checkout.gateway.payment.fetch.assert_not_called()


async def test_recovery_can_find_capture_after_a_failed_webhook(checkout):
    assert (await checkout.create()).status_code == 200
    assert (await checkout.webhook("payment.failed")).status_code == 200
    assert (await checkout.recover()).json()["status"] == "enrolled"


@pytest.mark.parametrize("operation", ["order", "attempts", "payment"])
async def test_recovery_gateway_timeout_is_unknown_without_leaking_details(checkout, db, operation):
    assert (await checkout.create()).status_code == 200
    call = {
        "order": checkout.gateway.order.fetch,
        "attempts": checkout.gateway.order.payments,
        "payment": checkout.gateway.payment.fetch,
    }[operation]
    call.side_effect = TimeoutError("private provider response")
    response = await checkout.recover()
    assert response.status_code == 200
    assert response.json()["status"] == "unknown"
    assert response.json()["safe_to_retry"] is False
    assert "private provider response" not in response.text
    assert (
        await db.scalar(
            select(Payment.id).where(Payment.razorpay_payment_id == checkout.payment_id)
        )
        is None
    )


@pytest.mark.parametrize(
    ("source", "override"),
    [
        ("order", {"id": "order_other"}),
        ("order", {"receipt": "another receipt"}),
        ("order", {"amount": 100}),
        ("order", {"currency": "USD"}),
        ("attempt", {"order_id": "order_other"}),
        ("payment", {"order_id": "order_other"}),
        ("payment", {"amount_refunded": 1}),
    ],
)
async def test_recovery_rejects_mismatched_gateway_data(checkout, db, source, override):
    assert (await checkout.create()).status_code == 200
    fields = {
        "order": checkout.remote_order,
        "attempt": checkout.gateway.order.payments.return_value["items"][0],
        "payment": checkout.remote,
    }[source]
    fields.update(override)
    response = await checkout.recover()
    assert response.json()["status"] == "unknown"
    assert response.json()["safe_to_retry"] is False
    assert (
        await db.scalar(select(Enrollment.id).where(Enrollment.course_id == checkout.course.id))
        is None
    )


async def test_recovery_rate_limit_caps_gateway_calls(checkout):
    assert (await checkout.create()).status_code == 200
    checkout.gateway.order.fetch.side_effect = TimeoutError
    for _ in range(10):
        assert (await checkout.recover()).status_code == 200
    assert (await checkout.recover()).status_code == 429
    assert checkout.gateway.order.fetch.call_count == 10
