import uuid
from datetime import datetime
from typing import Any


def new_id() -> str:
    return uuid.uuid4().hex


def utc_now() -> datetime:
    return datetime.utcnow()


def to_dict(obj: Any, exclude: set[str] | None = None) -> dict:
    exclude = exclude or set()
    result = {}
    for column in obj.__table__.columns:
        if column.name not in exclude:
            result[column.name] = getattr(obj, column.name)
    return result
