"""
AI-LMS Core Configuration
Pydantic v2 BaseSettings with full validation and computed fields.
"""
from functools import lru_cache
from typing import Annotated, Any

from pydantic import AnyHttpUrl, Field, PostgresDsn, computed_field, field_validator
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
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://ailms:ailms_secret@postgres:5432/ailms_db"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # =========================================================================
    # Security
    # =========================================================================
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

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

    # =========================================================================
    # File Uploads
    # =========================================================================
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    ALLOWED_VIDEO_TYPES: list[str] = ["video/mp4", "video/webm", "video/ogg"]
    ALLOWED_DOCUMENT_TYPES: list[str] = ["application/pdf"]

    @field_validator("ALLOWED_IMAGE_TYPES", "ALLOWED_VIDEO_TYPES", "ALLOWED_DOCUMENT_TYPES", mode="before")
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
    RATE_LIMIT_PER_MINUTE: int = 100
    AI_RATE_LIMIT_PER_MINUTE: int = 10

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
