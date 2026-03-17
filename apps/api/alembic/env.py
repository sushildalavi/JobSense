"""
Alembic environment configuration — async-compatible with FastAPI/asyncpg.

Reads DATABASE_URL from application settings so migrations always use the
same database as the running application.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import application settings and Base so that the metadata and all models
# are fully registered before autogenerate inspection runs.
from app.core.config import settings
from app.core.database import Base

# Import every model module so SQLAlchemy can see all tables.
from app.models import (  # noqa: F401
    agent,
    application,
    calendar,
    document,
    email,
    job,
    profile,
    resume,
    user,
)

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to the alembic.ini file values.
# ---------------------------------------------------------------------------
config = context.config

# Point alembic at our actual database.  Strip the asyncpg driver when running
# in offline mode because the synchronous URL format is expected there.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))

# Interpret the config file for Python logging if one is present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata is used by autogenerate to detect schema drift.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migration helpers
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well.  By skipping the Engine creation we
    don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online / async migration helpers
# ---------------------------------------------------------------------------


def do_run_migrations(connection) -> None:
    """Execute migrations using an existing synchronous-compatible connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside a connection context."""
    configuration = config.get_section(config.config_ini_section, {})
    # Use the full asyncpg URL for the actual engine.
    configuration["sqlalchemy.url"] = settings.ASYNC_DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using asyncio."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
