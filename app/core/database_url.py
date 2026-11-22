"""Database URL normalization shared by the application and Alembic."""

from sqlalchemy.engine import make_url


def normalize_async_database_url(value: str) -> str:
    """Select asyncpg for PostgreSQL URLs used with SQLAlchemy async engines."""
    url = make_url(value)
    if url.drivername in {"postgresql", "postgres"}:
        return url.set(drivername="postgresql+asyncpg").render_as_string(hide_password=False)
    return value
