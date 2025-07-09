from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context
from src.core.settings import APP_SETTINGS
from src.models.user import User  # Import your models here

config = context.config
config.set_main_option("sqlalchemy.url", APP_SETTINGS.DATABASE_URL)

fileConfig(config.config_file_name)
target_metadata = SQLModel.metadata


def run_migrations_offline():
    context.configure(
        url=APP_SETTINGS.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
