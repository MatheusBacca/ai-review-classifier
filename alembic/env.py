"""Alembic environment: uses the same `DATABASE_URL` as the app (via pydantic-settings)."""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

# Project root (parent of this `alembic` package)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.config import settings

# Import app models so table metadata is registered on SQLModel.metadata
import app.models  # noqa: F401

# Alembic Config and logging
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Match SQLModel / SQLAlchemy models used by the app
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = SQLModel.metadata


def get_url() -> str:
    return settings.database_url


def run_migrations_offline() -> None:
    """Emit SQL to script output (no live DB connection)."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a real connection (default for `upgrade` / `downgrade`)."""
    connectable = create_engine(get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
