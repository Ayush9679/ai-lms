"""Decimal-safe allocation helper for future verified completed-payment records."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from app.core.config import get_settings


@dataclass(frozen=True)
class RevenueSplit:
    gross_minor_units: int
    teacher_minor_units: int
    platform_minor_units: int


def split_completed_payment(
    gross_minor_units: int, *, teacher_share: Decimal | None = None
) -> RevenueSplit:
    """Split a verified completed payment in minor units.

    Callers must establish completed payment status and idempotency before using this helper.
    It does not record payment or recognized earnings.
    """
    if type(gross_minor_units) is not int or gross_minor_units < 0:
        raise ValueError("gross_minor_units must be a nonnegative integer")

    if teacher_share is None:
        teacher_share = get_settings().TEACHER_REVENUE_SHARE
    gross = Decimal(gross_minor_units)
    teacher = int((gross * teacher_share).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return RevenueSplit(
        gross_minor_units=gross_minor_units,
        teacher_minor_units=teacher,
        platform_minor_units=gross_minor_units - teacher,
    )
