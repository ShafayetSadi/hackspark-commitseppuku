from collections.abc import AsyncIterator, Mapping

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def session_dependency(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def validate_required_schema(
    engine: AsyncEngine,
    *,
    version_table: str,
    required_tables: Mapping[str, set[str]],
) -> None:
    def _validate(connection) -> None:
        inspector = inspect(connection)
        existing_tables = set(inspector.get_table_names())
        if version_table not in existing_tables:
            raise RuntimeError(
                f"Missing Alembic version table '{version_table}'. Run migrations before startup."
            )

        for table_name, required_columns in required_tables.items():
            if table_name not in existing_tables:
                raise RuntimeError(
                    f"Missing required table '{table_name}'. Run migrations before startup."
                )

            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            missing_columns = required_columns - existing_columns
            if missing_columns:
                missing_list = ", ".join(sorted(missing_columns))
                raise RuntimeError(
                    f"Schema mismatch for '{table_name}'. Missing columns: {missing_list}."
                )

    async with engine.connect() as connection:
        await connection.run_sync(_validate)
