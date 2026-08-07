import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# 1. Import our App Configuration and Database Base Blueprint
from app.core.config import settings
from app.core.database import Base

# 2. IMPORTANT: Import all domain models so Alembic can "see" them!
# If you don't import a model here, Alembic won't create its table.
from app.domain.auth.models import CAFirm, CAUser, Tenant
from app.domain.ims_recon.models import ErpInvoice, Gstr2bInvoice, ImsReconciliation
from app.domain.tds_align.models import TdsAnomaly, TdsLedger
from app.domain.tally_bridge.models import TallySyncJob
from app.domain.ingestion.models import IngestionJob

# This is the Alembic Config object, which provides access to values within alembic.ini
config = context.config

# 3. Override the database URL in alembic.ini with the one from our .env file
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Setup loggers from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 4. Point Alembic to our master blueprint catalog (Base.metadata)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This generates raw SQL commands without actually connecting to the database.
    Useful if you need to hand a SQL script to a database administrator.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Helper function that executes the migration inside an active transaction."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using our async database engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Main entry point when running 'alembic upgrade'."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()