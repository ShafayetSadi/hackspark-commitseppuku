from asyncio import run

from alembic import context
from auth_service.core.config import get_settings
from auth_service.models.user import User
from sqlalchemy import MetaData, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
version_table = "alembic_version_auth"
managed_tables = {"users"}
target_metadata = MetaData()
User.__table__.to_metadata(target_metadata)


def include_name(name, type_, parent_names) -> bool:
    if type_ == "table":
        return name in managed_tables or name == version_table
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_name=include_name,
        version_table=version_table,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_name=include_name,
        version_table=version_table,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run(run_migrations_online())
