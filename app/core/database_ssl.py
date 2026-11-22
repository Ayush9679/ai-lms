"""Verified TLS configuration for PostgreSQL connections."""

import ssl
from os import PathLike


def create_database_ssl_context(cafile: str | PathLike[str] | None = None) -> ssl.SSLContext:
    """Create a TLS context that always verifies the CA chain and hostname."""
    context = ssl.create_default_context(cafile=str(cafile) if cafile else None)
    if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
        raise RuntimeError("Database TLS context must verify certificates and hostnames")
    return context
