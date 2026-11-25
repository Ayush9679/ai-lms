"""Create Test Mode orders and reconcile captured payments."""

import hmac
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import razorpay
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.exceptions import AILMSException
from app.models.course import Course, CourseStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.payment import Payment, PaymentOrder, WebhookEvent
from app.models.user import User
from app.services.revenue_service import split_completed_payment

SUPPORTED_EVENTS = {"payment.captured", "payment.failed", "order.paid"}
ENROLLED_STATUSES = {EnrollmentStatus.active, EnrollmentStatus.completed}
RecoveryStatus = Literal["created", "pending", "authorized", "captured", "enrolled", "unknown"]


@dataclass(frozen=True)
class OrderRecovery:
    status: RecoveryStatus
    safe_to_retry: bool = False
    attempt_status: Literal["failed"] | None = None


def valid_signature(body: bytes, secret: str, signature: str) -> bool:
    expected = hmac.digest(secret.encode(), body, "sha256").hex()
    return hmac.compare_digest(expected.encode(), signature.encode())


async def has_captured_payment(
    db: AsyncSession, student_id: uuid.UUID, course_id: uuid.UUID
) -> bool:
    payment_id = await db.scalar(
        select(Payment.id)
        .join(PaymentOrder, Payment.order_id == PaymentOrder.id)
        .where(
            PaymentOrder.student_id == student_id,
            PaymentOrder.course_id == course_id,
            Payment.status == "captured",
        )
        .limit(1)
    )
    return payment_id is not None


def make_gateway(settings: Settings) -> razorpay.Client:
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET.get_secret_value())
    )


async def gateway_call(operation: Callable, *args) -> dict:
    try:
        # The SDK is synchronous. Keep network I/O off the event loop.
        result = await run_in_threadpool(operation, *args, timeout=10)
    except (
        razorpay.errors.ServerError,
        razorpay.errors.BadRequestError,
        razorpay.errors.GatewayError,
        OSError,
        ValueError,
    ):
        raise AILMSException("Payment gateway temporarily unavailable", 502) from None
    if not isinstance(result, dict):
        raise AILMSException("Invalid payment gateway response", 502)
    return result


class PaymentService:
    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    async def _lock_student(self, student_id: uuid.UUID) -> None:
        # One student lock serializes order creation and reconciliation across workers.
        await self.db.scalar(select(User.id).where(User.id == student_id).with_for_update())

    async def _enrollment(self, student_id: uuid.UUID, course_id: uuid.UUID) -> Enrollment | None:
        return await self.db.scalar(
            select(Enrollment)
            .where(Enrollment.student_id == student_id, Enrollment.course_id == course_id)
            .with_for_update()
        )

    async def create_order(self, student_id: uuid.UUID, course_id: uuid.UUID) -> PaymentOrder:
        await self._lock_student(student_id)
        course = await self.db.scalar(
            select(Course).where(Course.id == course_id, Course.deleted_at.is_(None))
        )
        if not course or course.status != CourseStatus.published:
            raise AILMSException("Purchasable course not found", 404)
        if course.instructor_id == student_id:
            raise AILMSException("You cannot purchase your own course", 403)
        if course.price <= 0 or course.currency != "INR":
            raise AILMSException("Payments require a paid INR course", 400)
        enrollment = await self._enrollment(student_id, course_id)
        if enrollment and enrollment.deleted_at is None and enrollment.status in ENROLLED_STATUSES:
            raise AILMSException("You are already enrolled in this course", 409)

        amount = int(course.price * 100)  # Numeric(10, 2) yields an exact Decimal.
        existing = await self.db.scalar(
            select(PaymentOrder).where(
                PaymentOrder.student_id == student_id,
                PaymentOrder.course_id == course_id,
            )
        )
        if existing:
            if existing.status == "paid" or existing.amount_paise != amount:
                raise AILMSException("An order already exists for this course", 409)
            return existing

        order_id = uuid.uuid4()
        gateway = make_gateway(self.settings)
        remote = await gateway_call(
            gateway.order.create,
            {
                "amount": amount,
                "currency": course.currency,
                "receipt": order_id.hex,
                "partial_payment": False,
            },
        )
        provider_id = remote.get("id")
        if (
            not isinstance(provider_id, str)
            or not provider_id.startswith("order_")
            or len(provider_id) > 80
            or remote.get("amount") != amount
            or remote.get("currency") != course.currency
        ):
            raise AILMSException("Invalid payment gateway order", 502)
        order = PaymentOrder(
            id=order_id,
            student_id=student_id,
            course_id=course_id,
            razorpay_order_id=provider_id,
            amount_paise=amount,
            currency=course.currency,
        )
        self.db.add(order)
        await self.db.commit()
        return order

    async def _owned_order(self, student_id: uuid.UUID, order_id: str) -> PaymentOrder:
        order = await self.db.scalar(
            select(PaymentOrder).where(
                PaymentOrder.razorpay_order_id == order_id,
                PaymentOrder.student_id == student_id,
            )
        )
        if order is None:
            raise AILMSException("Payment order not found", 404)
        return order

    async def verify(
        self, student_id: uuid.UUID, order_id: str, payment_id: str, signature: str
    ) -> Payment:
        order = await self._owned_order(student_id, order_id)
        secret = self.settings.RAZORPAY_KEY_SECRET.get_secret_value()
        if not valid_signature(
            f"{order.razorpay_order_id}|{payment_id}".encode(), secret, signature
        ):
            raise AILMSException("Invalid Checkout signature", 400)
        await self._lock_student(student_id)
        payment = await self._capture(order, payment_id)
        await self.db.commit()
        return payment

    async def recover_order(
        self, student_id: uuid.UUID, order_id: str
    ) -> tuple[PaymentOrder, OrderRecovery]:
        order = await self._owned_order(student_id, order_id)
        await self._lock_student(student_id)
        await self.db.refresh(order)
        payment = await self.db.scalar(select(Payment).where(Payment.order_id == order.id))
        if payment and payment.status == "captured":
            enrollment = await self._enrollment(student_id, order.course_id)
            enrolled = (
                enrollment is not None
                and enrollment.deleted_at is None
                and enrollment.status in ENROLLED_STATUSES
            )
            return order, OrderRecovery("enrolled" if enrolled else "captured")
        if payment or order.status == "paid":
            return order, OrderRecovery("unknown")

        try:
            return order, await self._reconcile_order(order)
        except AILMSException as exc:
            if exc.status_code not in {409, 502}:
                raise
            return order, OrderRecovery("unknown")

    async def _reconcile_order(self, order: PaymentOrder) -> OrderRecovery:
        gateway = make_gateway(self.settings)
        remote = await gateway_call(gateway.order.fetch, order.razorpay_order_id)
        provider_status = remote.get("status")
        attempts = remote.get("attempts")
        amount_paid = remote.get("amount_paid")
        amount_due = remote.get("amount_due")
        if (
            remote.get("id") != order.razorpay_order_id
            or remote.get("receipt") != order.id.hex
            or remote.get("currency") != order.currency
            or provider_status not in ("created", "attempted", "paid")
            or type(remote.get("amount")) is not int
            or remote["amount"] != order.amount_paise
            or type(attempts) is not int
            or attempts < 0
            or type(amount_paid) is not int
            or type(amount_due) is not int
        ):
            return OrderRecovery("unknown")

        collection = await gateway_call(gateway.order.payments, order.razorpay_order_id)
        items = collection.get("items")
        if not isinstance(items, list) or collection.get("count") != len(items):
            return OrderRecovery("unknown")
        if attempts != len(items):
            return OrderRecovery("pending")

        statuses: dict[str, str] = {}
        for item in items:
            if not isinstance(item, dict):
                return OrderRecovery("unknown")
            payment_id = item.get("id")
            status = item.get("status")
            if (
                not isinstance(payment_id, str)
                or not re.fullmatch(r"pay_[A-Za-z0-9]{1,76}", payment_id)
                or payment_id in statuses
                or item.get("order_id") != order.razorpay_order_id
                or type(item.get("amount")) is not int
                or item["amount"] != order.amount_paise
                or item.get("currency") != order.currency
                or status not in ("created", "authorized", "captured", "failed", "refunded")
                or item.get("captured") is not (status in ("captured", "refunded"))
            ):
                return OrderRecovery("unknown")
            statuses[payment_id] = status

        captured = [payment_id for payment_id, status in statuses.items() if status == "captured"]
        if provider_status == "paid":
            if amount_paid == order.amount_paise and amount_due == 0 and len(captured) == 1:
                await self._capture(order, captured[0])
                await self.db.commit()
                return OrderRecovery("enrolled")
            return OrderRecovery("pending")

        if amount_paid != 0 or amount_due != order.amount_paise or captured:
            return OrderRecovery("pending")
        if provider_status == "attempted" and statuses:
            if "authorized" in statuses.values():
                return OrderRecovery("authorized")
            if all(status == "failed" for status in statuses.values()):
                # A failed attempt can still authorize later. Keep the order pending.
                return OrderRecovery("pending", attempt_status="failed")
            return OrderRecovery("pending")
        if provider_status == "created" and order.status == "created" and attempts == 0:
            return OrderRecovery("created", safe_to_retry=await self._can_resume_checkout(order))
        return OrderRecovery("unknown")

    async def _can_resume_checkout(self, order: PaymentOrder) -> bool:
        course = await self.db.scalar(
            select(Course).where(Course.id == order.course_id, Course.deleted_at.is_(None))
        )
        if (
            not course
            or course.status != CourseStatus.published
            or course.instructor_id == order.student_id
            or course.price <= 0
            or course.currency != "INR"
            or course.currency != order.currency
            or course.price * 100 != order.amount_paise
        ):
            return False
        enrollment = await self._enrollment(order.student_id, order.course_id)
        return (
            enrollment is None
            or enrollment.deleted_at is not None
            or enrollment.status not in ENROLLED_STATUSES
        )

    async def _capture(self, order: PaymentOrder, payment_id: str) -> Payment:
        existing = await self.db.scalar(select(Payment).where(Payment.order_id == order.id))
        if existing:
            if existing.razorpay_payment_id != payment_id:
                raise AILMSException("A different payment was recorded for this order", 409)
            return existing

        gateway = make_gateway(self.settings)
        remote = await gateway_call(gateway.payment.fetch, payment_id)
        if remote.get("status") != "captured" or remote.get("captured") is not True:
            raise AILMSException("Payment has not been captured", 409)
        if (
            remote.get("id") != payment_id
            or remote.get("order_id") != order.razorpay_order_id
            or remote.get("amount") != order.amount_paise
            or remote.get("currency") != order.currency
            or remote.get("amount_refunded", 0) != 0
        ):
            raise AILMSException("Captured payment does not match the order", 409)

        split = split_completed_payment(
            order.amount_paise,
            teacher_share=1 - self.settings.PLATFORM_COMMISSION_PERCENT / 100,
        )
        payment = Payment(
            order_id=order.id,
            razorpay_payment_id=payment_id,
            captured_amount_paise=order.amount_paise,
            platform_commission_paise=split.platform_minor_units,
            teacher_earnings_paise=split.teacher_minor_units,
            gateway_fee_paise=remote.get("fee"),
        )
        self.db.add(payment)
        order.status = "paid"
        enrollment = await self._enrollment(order.student_id, order.course_id)
        if enrollment is None:
            self.db.add(Enrollment(student_id=order.student_id, course_id=order.course_id))
        else:
            enrollment.restore()
            if enrollment.status != EnrollmentStatus.completed:
                enrollment.status = EnrollmentStatus.active
        return payment

    async def process_event(
        self, event_id: str, event_type: str, order_id: str, payment_id: str
    ) -> None:
        order = await self.db.scalar(
            select(PaymentOrder).where(PaymentOrder.razorpay_order_id == order_id)
        )
        if order is None:
            return  # The Test Mode account can also deliver events for other applications.
        await self._lock_student(order.student_id)
        await self.db.refresh(order)
        insert = sqlite_insert if self.db.get_bind().dialect.name == "sqlite" else postgres_insert
        claimed = await self.db.scalar(
            insert(WebhookEvent)
            .values(provider_event_id=event_id, event_type=event_type)
            .on_conflict_do_nothing(index_elements=[WebhookEvent.provider_event_id])
            .returning(WebhookEvent.id)
        )
        if claimed is None:
            return

        if event_type == "payment.failed":
            if order.status != "paid":
                order.status = "failed"
        else:
            await self._capture(order, payment_id)
        await self.db.commit()
