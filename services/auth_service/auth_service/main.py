from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from auth_service.api.routes import router
from auth_service.core.config import get_settings
from auth_service.db.session import engine
from shared.app_core.database import validate_required_schema
from shared.app_core.http import install_request_logging
from shared.app_core.logging import configure_logging, get_logger
from shared.app_core.metrics import install_metrics
from shared.app_core.security import decode_token

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(settings.service_name)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await validate_required_schema(
        engine,
        version_table="alembic_version_auth",
        required_tables={
            "users": {"id", "email", "full_name", "hashed_password"},
        },
    )
    logger.info("auth_service_started", database_backend=settings.database_backend)
    yield


app = FastAPI(
    title="Auth Service",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.service_docs_enabled else None,
    redoc_url="/redoc" if settings.service_docs_enabled else None,
    openapi_url="/openapi.json" if settings.service_docs_enabled else None,
)
app.state.logger = logger


@app.middleware("http")
async def auth_context_middleware(request: Request, call_next):
    auth_header = request.headers.get("Authorization", "")
    request.state.user_id = None
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        try:
            payload = decode_token(token, settings.jwt_secret, settings.jwt_algorithm)
            request.state.user_id = payload.get("sub")
        except ValueError:
            if request.url.path == "/me":
                return JSONResponse(status_code=401, content={"detail": "Missing or invalid token"})
    return await call_next(request)


install_metrics(
    app,
    settings.service_name,
    enabled=settings.metrics_enabled,
    token=settings.metrics_token,
)
install_request_logging(app, logger)
app.include_router(router)
