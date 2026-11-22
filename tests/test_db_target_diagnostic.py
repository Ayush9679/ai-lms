"""Tests for safe URL normalization and error handling in the DB diagnostic."""

import asyncio
import json
import ssl

from sqlalchemy.engine import URL, make_url

from scripts import check_db_target
from app.core.config import Settings
from app.core.database_url import normalize_async_database_url


def test_plain_postgresql_url_uses_asyncpg_without_changing_credentials():
    original = URL.create(
        "postgresql",
        username="service_user",
        password="test:password/with@symbols",
        host="db.example.supabase.co",
        port=5432,
        database="postgres",
        query={"sslmode": "require"},
    )

    normalized = make_url(
        normalize_async_database_url(original.render_as_string(hide_password=False))
    )

    assert normalized.drivername == "postgresql+asyncpg"
    assert normalized.username == original.username
    assert normalized.password == original.password
    assert normalized.host == original.host
    assert normalized.port == original.port
    assert normalized.database == original.database
    assert normalized.query == original.query


def test_existing_asyncpg_url_is_unchanged():
    original = URL.create(
        "postgresql+asyncpg",
        username="service_user",
        password="test-password",
        host="db.example.supabase.co",
        database="postgres",
    )

    normalized = make_url(
        normalize_async_database_url(original.render_as_string(hide_password=False))
    )

    assert normalized == original


def test_settings_centralizes_bare_postgresql_url_normalization():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://user:password@db.example.supabase.co:5432/postgres",
        SECRET_KEY="test-secret-key-that-is-long-enough-for-validation",
        DEBUG=False,
    )

    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")


def test_settings_preserves_asyncpg_url():
    original = "postgresql+asyncpg://user:password@db.example.supabase.co:5432/postgres"
    settings = Settings(
        _env_file=None,
        DATABASE_URL=original,
        SECRET_KEY="test-secret-key-that-is-long-enough-for-validation",
        DEBUG=False,
    )

    assert settings.DATABASE_URL == original


def test_diagnostic_uses_verified_ssl_context_and_redacts_connection_errors(monkeypatch, capsys):
    secret = "do-not-print-this-password"
    settings = Settings(
        _env_file=None,
        DATABASE_URL=(
            "postgresql://service_user:do-not-print-this-password@"
            "db.example.supabase.co:5432/postgres"
        ),
        SECRET_KEY="test-secret-key-that-is-long-enough-for-validation",
        DEBUG=False,
        DATABASE_SSL=True,
        DATABASE_SSL_CA_FILE="certs/supabase-root-ca.crt",
    )
    ssl_context = object()
    observed = {}

    class FailingConnection:
        async def __aenter__(self):
            raise ssl.SSLCertVerificationError(
                f"failed URL: postgresql://service_user:{secret}@db.example/postgres"
            )

        async def __aexit__(self, *_args):
            return False

    class FailingEngine:
        def connect(self):
            return FailingConnection()

        async def dispose(self):
            return None

    def create_engine(url, **kwargs):
        observed["driver"] = url.drivername
        observed.update(kwargs)
        return FailingEngine()

    monkeypatch.setattr(check_db_target, "get_settings", lambda: settings)
    monkeypatch.setattr(check_db_target, "create_database_ssl_context", lambda _cafile: ssl_context)
    monkeypatch.setattr(check_db_target, "create_async_engine", create_engine)

    result = asyncio.run(check_db_target.main())
    output = capsys.readouterr()

    assert result == 2
    assert observed["driver"] == "postgresql+asyncpg"
    assert observed["connect_args"]["ssl"] is ssl_context
    assert "SSLCertVerificationError" in output.err
    assert secret not in output.err + output.out
    assert "postgresql://" not in output.err + output.out
    diagnostic = json.loads(output.err)
    assert diagnostic["connected"] is False
