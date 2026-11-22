"""
AI-LMS Core Configuration
Pydantic v2 BaseSettings with full validation and computed fields.
"""

from functools import lru_cache
from typing import Any

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # =========================================================================
    # Application
    # =========================================================================
    APP_NAME: str = "AI-LMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # =========================================================================
    # Database
    # =========================================================================
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0)
    DATABASE_SSL: bool = False

    # =========================================================================
    # Security
    # =========================================================================
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = Field(default="HS256", pattern="^HS256$")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=90)

    # =========================================================================
    # CORS
    # =========================================================================
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except Exception:
                return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, origins: list[str]) -> list[str]:
        if not origins or any(origin == "*" for origin in origins):
            raise ValueError("CORS_ORIGINS must contain explicit origins and cannot use '*'")
        return [origin.rstrip("/") for origin in origins]

    # =========================================================================
    # File Uploads
    # =========================================================================
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = Field(default=50, ge=1, le=1024)
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    ALLOWED_VIDEO_TYPES: list[str] = ["video/mp4", "video/webm", "video/ogg"]
    ALLOWED_DOCUMENT_TYPES: list[str] = ["application/pdf"]

    @field_validator(
        "ALLOWED_IMAGE_TYPES", "ALLOWED_VIDEO_TYPES", "ALLOWED_DOCUMENT_TYPES", mode="before"
    )
    @classmethod
    def parse_list_fields(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except Exception:
                return [item.strip() for item in v.split(",")]
        return v

    @computed_field  # type: ignore[misc]
    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @computed_field  # type: ignore[misc]
    @property
    def ALLOWED_MIME_TYPES(self) -> list[str]:
        return self.ALLOWED_IMAGE_TYPES + self.ALLOWED_VIDEO_TYPES + self.ALLOWED_DOCUMENT_TYPES

    # =========================================================================
    # Gemini AI
    # =========================================================================
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # =========================================================================
    # Rate Limiting
    # =========================================================================
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, ge=1)
    AI_RATE_LIMIT_PER_MINUTE: int = Field(default=10, ge=1)

    # =========================================================================
    # Email
    # =========================================================================
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str = "noreply@ailms.com"
    EMAILS_FROM_NAME: str = "AI-LMS"

    @computed_field  # type: ignore[misc]
    @property
    def EMAIL_ENABLED(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USERNAME and self.SMTP_PASSWORD)


@lru_cache
def get_settings() -> Settings:
    return Settings()
