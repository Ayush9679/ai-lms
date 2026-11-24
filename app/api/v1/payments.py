"""Authenticated Razorpay Checkout endpoints and signed webhook delivery."""

import json
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AILMSException
from app.database import get_db
from app.dependencies.auth import require_student
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.services.payment_service import (
    SUPPORTED_EVENTS,
    PaymentService,
    RecoveryStatus,
    valid_signature,
)


def payment_settings() -> Settings:
    settings = get_settings()
    if not settings.RAZORPAY_ENABLED:
        raise AILMSException("Payments are unavailable", 404)
    return settings


router = APIRouter(dependencies=[Depends(payment_settings)])
PaymentSettings = Annotated[Settings, Depends(payment_settings)]
Student = Annotated[User, Depends(require_student)]
Database = Annotated[AsyncSession, Depends(get_db)]


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_id: UUID


class CreateOrderResponse(BaseModel):
    razorpay_key_id: str
    razorpay_order_id: str
    amount: int
    currency: str


class VerifyRequest(BaseModel):
    razorpay_order_id: str = Field(pattern=r"^order_[A-Za-z0-9]+$", max_length=80)
    razorpay_payment_id: str = Field(pattern=r"^pay_[A-Za-z0-9]+$", max_length=80)
    razorpay_signature: str = Field(pattern=r"^[0-9a-f]{64}$")


class VerifyResponse(BaseModel):
    razorpay_payment_id: str
    status: str


class OrderStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    razorpay_order_id: str = Field(pattern=r"^order_[A-Za-z0-9]+$", max_length=80)


class OrderStatusResponse(BaseModel):
    razorpay_order_id: str
    course_id: UUID
    status: RecoveryStatus
    safe_to_retry: bool
    attempt_status: Literal["failed"] | None


@router.post("/create-order")
async def create_order(
    data: CreateOrderRequest, student: Student, db: Database, settings: PaymentSettings
) -> CreateOrderResponse:
    order = await PaymentService(db, settings).create_order(student.id, data.course_id)
    return CreateOrderResponse(
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
        razorpay_order_id=order.razorpay_order_id,
        amount=order.amount_paise,
        currency=order.currency,
    )


@router.post("/verify")
async def verify(
    data: VerifyRequest, student: Student, db: Database, settings: PaymentSettings
) -> VerifyResponse:
    payment = await PaymentService(db, settings).verify(
        student.id, data.razorpay_order_id, data.razorpay_payment_id, data.razorpay_signature
    )
    return VerifyResponse(razorpay_payment_id=payment.razorpay_payment_id, status=payment.status)


@router.post("/status")
@limiter.limit("10/minute", override_defaults=False)
async def order_status(
    request: Request,
    response: Response,
    data: OrderStatusRequest,
    student: Student,
    db: Database,
    settings: PaymentSettings,
) -> OrderStatusResponse:
    """Check or recover the authenticated student's existing Razorpay order."""
    order, recovery = await PaymentService(db, settings).recover_order(
        student.id, data.razorpay_order_id
    )
    response.headers["Cache-Control"] = "no-store"
    return OrderStatusResponse(
        razorpay_order_id=order.razorpay_order_id,
        course_id=order.course_id,
        status=recovery.status,
        safe_to_retry=recovery.safe_to_retry,
        attempt_status=recovery.attempt_status,
    )


@router.post("/webhook")
async def webhook(
    request: Request,
    db: Database,
    settings: PaymentSettings,
    signature: Annotated[str, Header(alias="X-Razorpay-Signature")] = "",
    event_id: Annotated[str, Header(alias="X-Razorpay-Event-Id")] = "",
) -> dict[str, str]:
    raw = await request.body()
    if not valid_signature(raw, settings.RAZORPAY_WEBHOOK_SECRET.get_secret_value(), signature):
        raise AILMSException("Invalid webhook signature", 400)
    try:
        event = json.loads(raw)
        event_type = event["event"]
        if not isinstance(event_type, str):
            raise ValueError
        if event_type not in SUPPORTED_EVENTS:
            return {"status": "ignored"}
        entity = event["payload"]["payment"]["entity"]
        order_id = entity["order_id"]
        payment_id = entity["id"]
        if order_id is None:
            return {"status": "ignored"}
        if (
            not event_id
            or len(event_id) > 128
            or not isinstance(order_id, str)
            or not order_id.startswith("order_")
            or len(order_id) > 80
            or not isinstance(payment_id, str)
            or not payment_id.startswith("pay_")
            or len(payment_id) > 80
        ):
            raise ValueError
        if event_type == "order.paid" and event["payload"]["order"]["entity"]["id"] != order_id:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise AILMSException("Invalid webhook payload", 400) from None

    await PaymentService(db, settings).process_event(event_id, event_type, order_id, payment_id)
    return {"status": "ok"}
