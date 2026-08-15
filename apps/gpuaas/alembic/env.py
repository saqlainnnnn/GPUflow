from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from apps.gpuaas.app.core.config import get_settings

# Import every GPUaaS model so they are registered with Base.metadata.
from apps.gpuaas.app.models import (  # noqa: F401
    Base,
    Customer,
    GPUAllocation,
    GPUCapacity,
    GPUJob,
    GPUUsageEvent,
    Invoice,
    InvoiceLineItem,
    OutboxEvent,
)
from apps.gpuaas.app.models.xero_connection import (  # noqa: F401
    XeroConnection,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

VERSION_TABLE = "alembic_version_gpuaas"

# Tables owned by Integration Hub live in the same PostgreSQL database
# but must never be managed by GPUaaS Alembic.
IGNORED_TABLES = {
    "integration_events",
    "alembic_version_integration",
}


def include_object(
    object_,
    name,
    type_,
    reflected,
    compare_to,
):
    if type_ == "table" and name in IGNORED_TABLES:
        return False

    if type_ == "index":
        table = getattr(object_, "table", None)

        if table is not None and table.name in IGNORED_TABLES:
            return False

    return True


def run_migrations_offline() -> None:
    settings = get_settings()

    context.configure(
        url=settings.sync_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        version_table=VERSION_TABLE,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    settings = get_settings()

    connectable = create_engine(
        settings.sync_database_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            version_table=VERSION_TABLE,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
