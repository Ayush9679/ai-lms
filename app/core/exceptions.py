"""
AI-LMS Custom Exceptions and FastAPI Exception Handlers.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Domain Exceptions
# =============================================================================


class AILMSException(Exception):
    """Base exception for all AI-LMS domain errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AILMSException):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str | int | None = None) -> None:
        detail = f"{resource} not found"
        if identifier is not None:
            detail = f"{resource} with id '{identifier}' not found"
        super().__init__(detail, status.HTTP_404_NOT_FOUND)


class UnauthorizedError(AILMSException):
    """Authentication required or token invalid."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AILMSException):
    """Insufficient permissions."""

    def __init__(self, message: str = "You do not have permission to perform this action") -> None:
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ConflictError(AILMSException):
    """Resource already exists or state conflict."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status.HTTP_409_CONFLICT)


class ValidationError(AILMSException):
    """Business rule validation failure."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class FileTooLargeError(AILMSException):
    """Uploaded file exceeds size limit."""

    def __init__(self, max_mb: int) -> None:
        super().__init__(
            f"File exceeds maximum allowed size of {max_mb}MB",
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )


class InvalidFileTypeError(AILMSException):
    """Uploaded file has unsupported MIME type."""

    def __init__(self, mime_type: str) -> None:
        super().__init__(
            f"File type '{mime_type}' is not allowed",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


class AIServiceError(AILMSException):
    """AI service failure (Gemini API error, not configured, etc.)."""

    def __init__(self, message: str = "AI service is currently unavailable") -> None:
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


class AlreadyEnrolledError(ConflictError):
    """Student is already enrolled in the course."""

    def __init__(self) -> None:
        super().__init__("You are already enrolled in this course")


# =============================================================================
# Exception Handlers
# =============================================================================


def _error_response(status_code: int, message: str, detail: object = None) -> JSONResponse:
    content: dict = {"error": True, "message": message}
    if detail is not None:
        content["detail"] = detail
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(AILMSException)
    async def ailms_exception_handler(request: Request, exc: AILMSException) -> JSONResponse:
        logger.warning(
            "Domain exception",
            extra={
                "path": request.url.path,
                "status_code": exc.status_code,
                "error_message": exc.message,
            },
        )
        return _error_response(exc.status_code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({"field": field, "message": error["msg"]})
        logger.warning(
            "Validation error",
            extra={"path": request.url.path, "errors": errors},
        )
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Validation failed",
            errors,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            exc_info=True,
            extra={"path": request.url.path},
        )
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred. Please try again later.",
        )
