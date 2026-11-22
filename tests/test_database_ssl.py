"""Tests for verified asyncpg TLS configuration."""

import ssl

import pytest

from app.core import database_ssl


def test_database_ssl_context_loads_configured_ca_and_verifies_hostname(monkeypatch):
    context = ssl.create_default_context()
    calls = []

    def create_default_context(*, cafile):
        calls.append(cafile)
        return context

    monkeypatch.setattr(database_ssl.ssl, "create_default_context", create_default_context)

    result = database_ssl.create_database_ssl_context("certs/supabase-root-ca.crt")

    assert result is context
    assert calls == ["certs/supabase-root-ca.crt"]
    assert result.verify_mode == ssl.CERT_REQUIRED
    assert result.check_hostname is True


def test_database_ssl_context_uses_system_store_when_no_ca_file_is_set(monkeypatch):
    context = ssl.create_default_context()
    calls = []

    def create_default_context(*, cafile):
        calls.append(cafile)
        return context

    monkeypatch.setattr(database_ssl.ssl, "create_default_context", create_default_context)

    result = database_ssl.create_database_ssl_context()

    assert result is context
    assert calls == [None]
    assert result.verify_mode == ssl.CERT_REQUIRED
    assert result.check_hostname is True


def test_database_ssl_context_rejects_an_unverified_context(monkeypatch):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    monkeypatch.setattr(database_ssl.ssl, "create_default_context", lambda **kwargs: context)

    with pytest.raises(RuntimeError, match="must verify certificates and hostnames"):
        database_ssl.create_database_ssl_context("certs/supabase-root-ca.crt")
