"""
AI-LMS Core Configuration
Pydantic v2 BaseSettings with full validation and computed fields.
"""

from functools import lru_cache
from decimal import Decimal
from typing import Any

from pydantic import Field, SecretStr, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.database_url import normalize_async_database_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        hide_input_in_errors=True,
    )

    # =========================================================================
    # Application
    # =========================================================================
    APP_NAME: str = "AI-LMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    RAZORPAY_ENABLED: bool = False
    RAZORPAY_TEST_MODE: bool = True
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: SecretStr = SecretStr("")
    RAZORPAY_WEBHOOK_SECRET: SecretStr = SecretStr("")
    PLATFORM_COMMISSION_PERCENT: Decimal = Field(default=Decimal("10"), ge=0, le=100)

    @model_validator(mode="after")
    def validate_razorpay(self) -> "Settings":
        if self.RAZORPAY_ENABLED:
            if (
                not self.RAZORPAY_TEST_MODE
                or not self.RAZORPAY_KEY_ID.startswith("rzp_test_")
                or self.RAZORPAY_KEY_ID == "rzp_test_"
            ):
                raise ValueError("Razorpay requires a Test Mode key in this release")
            if not all(
                secret.get_secret_value().strip()
                for secret in (self.RAZORPAY_KEY_SECRET, self.RAZORPAY_WEBHOOK_SECRET)
            ):
                raise ValueError("Razorpay requires API and webhook secrets")
        return self

    # =========================================================================
    # Database
    # =========================================================================
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0)
    DATABASE_SSL: bool = False
    DATABASE_SSL_CA_FILE: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        return normalize_async_database_url(value)

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
    STORAGE_ENDPOINT_URL: str | None = None
    STORAGE_REGION: str = "auto"
    STORAGE_ACCESS_KEY_ID: str | None = None
    STORAGE_SECRET_ACCESS_KEY: str | None = None
    STORAGE_BUCKET: str = "ai-lms-media"
    STORAGE_ACCOUNT_ID: str | None = None
    STORAGE_PRESIGNED_URL_TTL: int = Field(default=900, ge=60, le=3600)
    STORAGE_UPLOAD_GRANT_TTL: int = Field(default=86400, ge=900, le=604800)
    MAX_UPLOAD_SIZE_MB: int = Field(default=50, ge=1, le=1024)
    MAX_VIDEO_SIZE_MB: int = Field(default=2048, ge=1, le=5120)
    MAX_IMAGE_SIZE_MB: int = Field(default=10, ge=1, le=1024)
    TEACHER_REVENUE_SHARE: Decimal = Field(default=Decimal("0.90"), ge=0, le=1)
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
    def MAX_VIDEO_SIZE_BYTES(self) -> int:
        return self.MAX_VIDEO_SIZE_MB * 1024 * 1024

    @computed_field  # type: ignore[misc]
    @property
    def MAX_IMAGE_SIZE_BYTES(self) -> int:
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024

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
