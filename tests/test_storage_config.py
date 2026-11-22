from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.exceptions import ValidationError
from app.services import storage_service
from app.services.upload_service import UploadService


def test_render_r2_environment_names_are_canonical(monkeypatch):
    values = {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-that-is-at-least-thirty-two-bytes",
        "STORAGE_ENDPOINT_URL": "https://account.r2.cloudflarestorage.com",
        "STORAGE_REGION": "auto",
        "STORAGE_ACCESS_KEY_ID": "test-key-id",
        "STORAGE_SECRET_ACCESS_KEY": "test-secret-value",
        "STORAGE_BUCKET": "ai-lms-media",
        "MAX_VIDEO_SIZE_MB": "2048",
        "MAX_IMAGE_SIZE_MB": "10",
        "TEACHER_REVENUE_SHARE": "0.70",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)

    assert settings.STORAGE_ENDPOINT_URL == values["STORAGE_ENDPOINT_URL"]
    assert settings.STORAGE_REGION == "auto"
    assert settings.STORAGE_BUCKET == "ai-lms-media"
    assert settings.STORAGE_BUCKET != "ai-lms-media-wrong"
    assert settings.MAX_VIDEO_SIZE_BYTES == 2048 * 1024 * 1024
    assert settings.MAX_IMAGE_SIZE_BYTES == 10 * 1024 * 1024
    assert settings.TEACHER_REVENUE_SHARE == 0.70


def test_storage_endpoint_url_wins_over_account_id(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        storage_service,
        "get_settings",
        lambda: SimpleNamespace(
            STORAGE_BUCKET="ai-lms-media",
            STORAGE_PRESIGNED_URL_TTL=900,
            STORAGE_ENDPOINT_URL="https://configured-endpoint.example",
            STORAGE_ACCOUNT_ID="must-not-be-used",
            STORAGE_ACCESS_KEY_ID="key",
            STORAGE_SECRET_ACCESS_KEY="secret",
            STORAGE_REGION="auto",
        ),
    )
    monkeypatch.setattr(
        storage_service.boto3, "client", lambda *args, **kwargs: captured.update(kwargs) or object()
    )

    storage_service.ObjectStorage()

    assert captured["endpoint_url"] == "https://configured-endpoint.example"
    assert captured["region_name"] == "auto"


def test_storage_account_id_is_endpoint_fallback(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        storage_service,
        "get_settings",
        lambda: SimpleNamespace(
            STORAGE_BUCKET="ai-lms-media",
            STORAGE_PRESIGNED_URL_TTL=900,
            STORAGE_ENDPOINT_URL=None,
            STORAGE_ACCOUNT_ID="account-id",
            STORAGE_ACCESS_KEY_ID="key",
            STORAGE_SECRET_ACCESS_KEY="secret",
            STORAGE_REGION="auto",
        ),
    )
    monkeypatch.setattr(
        storage_service.boto3,
        "client",
        lambda *args, **kwargs: captured.update(kwargs) or object(),
    )

    storage_service.ObjectStorage()

    assert captured["endpoint_url"] == "https://account-id.r2.cloudflarestorage.com"


def test_single_put_accepts_configured_two_gib_video_limit():
    service = UploadService(None)
    size = 2048 * 1024 * 1024
    assert service._validate_asset("lesson", "video", "video/mp4", size) == ".mp4"
    with pytest.raises(ValidationError, match="2048 MB limit"):
        service._validate_asset("lesson", "video", "video/mp4", size + 1)
