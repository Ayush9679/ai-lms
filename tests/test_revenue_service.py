from decimal import Decimal

import pytest

from app.core.config import Settings
from app.services.revenue_service import split_completed_payment


def test_default_teacher_share_is_ninety_percent():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY="test-secret-key-that-is-at-least-thirty-two-bytes",
    )
    assert settings.TEACHER_REVENUE_SHARE == Decimal("0.90")


def test_minor_unit_revenue_split_uses_explicit_half_up_rounding():
    split = split_completed_payment(100_000)
    assert split.teacher_minor_units == 90_000
    assert split.platform_minor_units == 10_000
    assert split.teacher_minor_units + split.platform_minor_units == split.gross_minor_units

    smallest = split_completed_payment(1)
    assert smallest.teacher_minor_units == 1
    assert smallest.platform_minor_units == 0


def test_zero_verified_payment_produces_zero_and_invalid_amounts_are_rejected():
    assert split_completed_payment(0).teacher_minor_units == 0
    assert split_completed_payment(0).platform_minor_units == 0
    with pytest.raises(ValueError):
        split_completed_payment(-1)
    with pytest.raises(ValueError):
        split_completed_payment(1.5)  # type: ignore[arg-type]
