"""
AI-LMS Structured Logging — JSON-formatted logs with request correlation.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured, machine-readable logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)

        # Include any extra fields attached to the record
        standard_attrs = {
            "args", "created", "exc_info", "exc_text", "filename",
            "funcName", "id", "levelname", "levelno", "lineno", "message",
            "module", "msecs", "msg", "name", "pathname", "process",
            "processName", "relativeCreated", "stack_info", "thread",
            "threadName",
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """Configure application-wide structured logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Remove existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy_logger in ["uvicorn.access", "sqlalchemy.engine"]:
        logging.getLogger(noisy_logger).setLevel(
            logging.DEBUG if settings.DEBUG else logging.WARNING
        )


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
