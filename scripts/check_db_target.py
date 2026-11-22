"""Print the configured database target and, for PostgreSQL, verify it read-only."""

import asyncio
import json
import sys

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.database_ssl import create_database_ssl_context


async def main() -> int:
    settings = get_settings()
    url = make_url(settings.DATABASE_URL)
    configured = {
        "driver": url.drivername,
        "host": url.host,
        "port": url.port,
        "database": url.database,
    }

    if not url.drivername.startswith("postgresql"):
        print(json.dumps({"configured_target": configured, "connected": False}, indent=2))
        print("Set DATABASE_URL to the intended Supabase PostgreSQL URL before running Alembic.")
        return 1

    engine_options = {"poolclass": NullPool}
    if settings.DATABASE_SSL:
        engine_options["connect_args"] = {
            "ssl": create_database_ssl_context(settings.DATABASE_SSL_CA_FILE)
        }
    engine = create_async_engine(url, **engine_options)
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    """
                    SELECT current_database() AS database,
                           current_schema() AS current_schema,
                           current_schemas(true) AS search_path_schemas,
                           inet_server_addr()::text AS server_address,
                           inet_server_port() AS server_port
                    """
                )
            )
            actual = dict(result.mappings().one())
    except Exception as exc:
        # Do not print driver exceptions: some include connection details.
        print(
            json.dumps(
                {
                    "configured_target": configured,
                    "connected": False,
                    "error_type": type(exc).__name__,
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    finally:
        await engine.dispose()

    print(
        json.dumps({"configured_target": configured, "connected": True, "server": actual}, indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
