from __future__ import annotations

import os
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]


def clear_service_modules() -> None:
    prefixes = (
        "auth_service",
        "rental_service",
        "analytics_service",
        "ai_agent_service",
        "gateway",
        "shared.app_core",
    )
    for mod in list(sys.modules):
        if any(mod == p or mod.startswith(f"{p}.") for p in prefixes):
            sys.modules.pop(mod, None)


@contextmanager
def service_environment(service_dir: Path, env: dict[str, str]):
    prev_env = {k: os.environ.get(k) for k in env}
    prev_path = list(sys.path)

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(service_dir))
    os.environ.update(env)
    clear_service_modules()
    try:
        yield
    finally:
        clear_service_modules()
        sys.path[:] = prev_path
        for k, v in prev_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def load_runtime(
    service_path: Path, env: dict[str, str], modules: dict[str, str]
) -> SimpleNamespace:
    loaded: dict[str, object] = {}
    with service_environment(service_path, env):
        import importlib

        for alias, mod_name in modules.items():
            loaded[alias] = importlib.import_module(mod_name)
    return SimpleNamespace(**loaded)


def prepare_auth_database(database_path: str) -> None:
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            "CREATE TABLE users ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "email VARCHAR(255) NOT NULL,"
            "full_name VARCHAR(255) NOT NULL,"
            "hashed_password VARCHAR(255) NOT NULL)"
        )
        conn.execute("CREATE UNIQUE INDEX ix_users_email ON users (email)")
        conn.execute("CREATE TABLE alembic_version_auth (version_num VARCHAR(32) NOT NULL)")
        conn.execute("INSERT INTO alembic_version_auth VALUES ('0001_create_users')")
        conn.commit()


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


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def auth_env(tmp_path) -> dict[str, str]:
    return {
        "APP_ENV": "dev",
        "DATABASE_BACKEND": "sqlite",
        "SQLITE_PATH": str(tmp_path / "auth.db"),
        "JWT_SECRET": "test-secret",
    }


@pytest.fixture
def ai_env() -> dict[str, str]:
    return {
        "APP_ENV": "dev",
        "JWT_SECRET": "test-secret",
        "LLM_PROVIDER": "mock",
        "MONGO_URI": "mongodb://localhost:27017/test",
    }


@pytest.fixture
def auth_runtime(auth_env):
    prepare_auth_database(auth_env["SQLITE_PATH"])
    runtime = load_runtime(
        ROOT / "user-service",
        auth_env,
        {
            "api_dependencies": "auth_service.api.dependencies",
            "api_routes": "auth_service.api.routes",
            "core_config": "auth_service.core.config",
            "schemas": "auth_service.schemas.auth",
        },
    )
    runtime.session_factory = build_sync_session_factory(auth_env["SQLITE_PATH"])
    return runtime


@pytest.fixture
def ai_runtime(ai_env):
    return load_runtime(
        ROOT / "agentic-service",
        ai_env,
        {
            "core_config": "ai_agent_service.core.config",
            "schemas": "ai_agent_service.schemas.chat",
            "chat_service": "ai_agent_service.services.chat_service",
            "llm_factory": "ai_agent_service.services.llm.factory",
            "rag_retriever": "ai_agent_service.services.rag.retriever",
            "rag_relevance": "ai_agent_service.services.rag.relevance",
            "rag_context": "ai_agent_service.services.rag.context_builder",
        },
    )


@pytest.fixture
def gateway_env() -> dict[str, str]:
    return {
        "APP_ENV": "dev",
        "JWT_SECRET": "test-secret",
        "USER_SERVICE_ADDR": "localhost:50051",
        "RENTAL_SERVICE_ADDR": "localhost:50052",
        "ANALYTICS_SERVICE_ADDR": "localhost:50053",
        "AGENTIC_SERVICE_ADDR": "localhost:50054",
    }


@pytest.fixture
def gateway_runtime(gateway_env):
    return load_runtime(
        ROOT / "api-gateway",
        gateway_env,
        {
            "main": "gateway.main",
            "core_config": "gateway.core.config",
            "api_routes": "gateway.api.routes",
        },
    )
