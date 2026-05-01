from __future__ import annotations

import importlib
import os
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]


def clear_service_modules() -> None:
    for module_name in list(sys.modules):
        if (
            module_name == "app"
            or module_name.startswith("app.")
            or module_name == "gateway"
            or module_name.startswith("gateway.")
            or module_name == "auth_service"
            or module_name.startswith("auth_service.")
            or module_name == "ai_agent_service"
            or module_name.startswith("ai_agent_service.")
            or module_name == "shared.app_core"
            or module_name.startswith("shared.app_core.")
        ):
            sys.modules.pop(module_name, None)


@contextmanager
def service_environment(service_dir: Path, env: dict[str, str]) -> Iterator[None]:
    previous_values = {key: os.environ.get(key) for key in env}
    previous_sys_path = list(sys.path)

    sys.path.insert(0, str(service_dir))
    sys.path.insert(0, str(ROOT))
    os.environ.update(env)
    clear_service_modules()
    try:
        yield
    finally:
        clear_service_modules()
        sys.path[:] = previous_sys_path
        for key, value in previous_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def load_runtime(
    service_path: Path,
    env: dict[str, str],
    modules_to_load: dict[str, str],
) -> SimpleNamespace:
    modules: dict[str, object] = {}
    with service_environment(service_path, env):
        for alias, module_name in modules_to_load.items():
            modules[alias] = importlib.import_module(module_name)
    return SimpleNamespace(**modules)


def prepare_auth_database(database_path: str) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                hashed_password VARCHAR(255) NOT NULL
            )
            """
        )
        connection.execute("CREATE UNIQUE INDEX ix_users_email ON users (email)")
        connection.execute("CREATE TABLE alembic_version_auth (version_num VARCHAR(32) NOT NULL)")
        connection.execute(
            "INSERT INTO alembic_version_auth (version_num) VALUES ('0001_create_users')"
        )
        connection.commit()


def prepare_item_database(database_path: str) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100) NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute("CREATE INDEX ix_items_category ON items (category)")
        connection.execute(
            "CREATE INDEX ix_items_category_created_at ON items (category, created_at)"
        )
        connection.execute("CREATE INDEX ix_items_name ON items (name)")
        connection.execute("CREATE TABLE alembic_version_item (version_num VARCHAR(32) NOT NULL)")
        connection.execute(
            "INSERT INTO alembic_version_item (version_num) VALUES ('0001_create_items')"
        )
        connection.commit()


class AsyncSessionAdapter:
    def __init__(self, sync_session):
        self.sync_session = sync_session

    def add(self, instance) -> None:
        self.sync_session.add(instance)

    async def scalar(self, statement):
        return self.sync_session.scalar(statement)

    async def scalars(self, statement):
        return self.sync_session.scalars(statement)

    async def commit(self) -> None:
        self.sync_session.commit()

    async def refresh(self, instance) -> None:
        self.sync_session.refresh(instance)

    async def rollback(self) -> None:
        self.sync_session.rollback()


def build_sync_session_factory(database_path: str):
    engine = create_engine(f"sqlite:///{database_path}")
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest.fixture
def auth_env(tmp_path) -> dict[str, str]:
    return {
        "APP_ENV": "dev",
        "DATABASE_BACKEND": "sqlite",
        "SQLITE_PATH": str(tmp_path / "auth.db"),
        "JWT_SECRET": "test-secret",
    }


@pytest.fixture
def item_env(tmp_path) -> dict[str, str]:
    return {
        "APP_ENV": "dev",
        "DATABASE_BACKEND": "sqlite",
        "SQLITE_PATH": str(tmp_path / "items.db"),
        "JWT_SECRET": "test-secret",
    }


@pytest.fixture
def ai_env() -> dict[str, str]:
    return {
        "APP_ENV": "dev",
        "JWT_SECRET": "test-secret",
    }


@pytest.fixture
def gateway_env() -> dict[str, str]:
    return {
        "APP_ENV": "prod",
        "JWT_SECRET": "test-secret",
        "AUTH_SERVICE_URL": "http://auth-service:8000",
        "ITEM_SERVICE_URL": "http://item-service:8000",
        "AI_AGENT_SERVICE_URL": "http://ai-agent-service:8000",
    }


@pytest.fixture
def auth_runtime(auth_env):
    prepare_auth_database(auth_env["SQLITE_PATH"])
    runtime = load_runtime(
        ROOT / "services" / "auth_service",
        auth_env,
        {
            "api_dependencies": "auth_service.api.dependencies",
            "api_routes": "auth_service.api.routes",
            "core_config": "auth_service.core.config",
            "main": "auth_service.main",
            "schemas": "auth_service.schemas.auth",
        },
    )
    runtime.session_factory = build_sync_session_factory(auth_env["SQLITE_PATH"])
    return runtime


@pytest.fixture
def item_runtime(item_env):
    prepare_item_database(item_env["SQLITE_PATH"])
    runtime = load_runtime(
        ROOT / "services" / "item-service",
        item_env,
        {
            "api_routes": "app.api.routes",
            "core_config": "app.core.config",
            "main": "app.main",
            "schemas": "app.schemas.item",
        },
    )
    runtime.session_factory = build_sync_session_factory(item_env["SQLITE_PATH"])
    return runtime


@pytest.fixture
def ai_runtime(ai_env):
    return load_runtime(
        ROOT / "services" / "ai_agent_service",
        ai_env,
        {
            "api_routes": "ai_agent_service.api.routes",
            "core_config": "ai_agent_service.core.config",
            "main": "ai_agent_service.main",
            "schemas": "ai_agent_service.schemas.chat",
        },
    )


@pytest.fixture
def gateway_runtime(gateway_env):
    return load_runtime(
        ROOT / "gateway",
        gateway_env,
        {
            "api_routes": "gateway.api.routes",
            "core_config": "gateway.core.config",
            "main": "gateway.main",
        },
    )
