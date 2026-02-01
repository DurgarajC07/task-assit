"""Alembic environment configuration."""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import settings and Base
from app.config import settings
from app.models.base import Base

# Import all models to ensure they're registered with SQLAlchemy
import app.models  # This imports all models via __init__.py

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from settings
# For development, use SQLite if PostgreSQL URL is not accessible
database_url = settings.database_url
if database_url.startswith('postgresql'):
    # Try PostgreSQL, fall back to SQLite if not available
    try:
        from sqlalchemy import create_engine
        engine = create_engine(database_url.replace('+asyncpg', ''), pool_pre_ping=True)
        with engine.connect():
            pass
        config.set_main_option("sqlalchemy.url", database_url.replace('+asyncpg', ''))
    except Exception:
        # PostgreSQL not available, use SQLite
        database_url = "sqlite:///./task_assistant.db"
        config.set_main_option("sqlalchemy.url", database_url)
else:
    config.set_main_option("sqlalchemy.url", database_url.replace('+aiosqlite', ''))

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.
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


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
