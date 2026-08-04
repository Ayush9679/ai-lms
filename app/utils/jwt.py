from datetime import datetime, timedelta
from typing import Any

from jose import jwt

from app.config import get_settings

settings = get_settings()


def create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str) -> str:
    return create_token(
        subject,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
    )


def create_refresh_token(subject: str) -> str:
    return create_token(
        subject,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
    )


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
