"""
AI-LMS Request/Response Logging Middleware.
Logs every request with method, path, status code, and duration.
"""
import time
import uuid as uuid_lib

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger("ailms.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid_lib.uuid4())[:8]
        start = time.perf_counter()

        # Attach request ID for downstream correlation
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception:
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
                exc_info=True,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "HTTP request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response
