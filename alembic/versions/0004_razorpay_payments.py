"""Add Test Mode Razorpay payment records.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_orders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("razorpay_order_id", sa.String(80), unique=True, nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("student_id", "course_id", name="uq_payment_order_student_course"),
    )
    op.create_index("ix_payment_orders_course_id", "payment_orders", ["course_id"])
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "order_id", sa.Uuid(), sa.ForeignKey("payment_orders.id"), unique=True, nullable=False
        ),
        sa.Column("razorpay_payment_id", sa.String(80), unique=True, nullable=False),
        sa.Column("captured_amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("platform_commission_paise", sa.BigInteger(), nullable=False),
        sa.Column("teacher_earnings_paise", sa.BigInteger(), nullable=False),
        sa.Column("gateway_fee_paise", sa.BigInteger()),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("provider_event_id", sa.String(128), unique=True, nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("webhook_events")
    op.drop_table("payments")
    op.drop_index("ix_payment_orders_course_id", table_name="payment_orders")
    op.drop_table("payment_orders")
