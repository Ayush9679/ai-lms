"""
AI-LMS Common Schemas — shared response envelopes and pagination.
"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common config for all AI-LMS schemas."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
    )


class MessageResponse(BaseSchema):
    """Generic message response."""
    message: str
    success: bool = True


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response envelope."""
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        pages = max(1, -(-total // page_size))  # ceiling division
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class PaginationParams(BaseSchema):
    """Query parameters for paginated endpoints."""
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
