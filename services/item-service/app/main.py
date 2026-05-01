from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.db.session import engine
from shared.app_core.database import validate_required_schema
from shared.app_core.http import install_request_logging
from shared.app_core.logging import configure_logging, get_logger
from shared.app_core.metrics import install_metrics

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(settings.service_name)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await validate_required_schema(
        engine,
        version_table="alembic_version_item",
        required_tables={
            "items": {"id", "name", "category", "quantity", "created_at"},
        },
    )
    logger.info("item_service_started", database_backend=settings.database_backend)
    yield


app = FastAPI(
    title="Item Service",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.service_docs_enabled else None,
    redoc_url="/redoc" if settings.service_docs_enabled else None,
    openapi_url="/openapi.json" if settings.service_docs_enabled else None,
)
app.state.logger = logger
install_metrics(
    app,
    settings.service_name,
    enabled=settings.metrics_enabled,
    token=settings.metrics_token,
)
install_request_logging(app, logger)
app.include_router(router)
