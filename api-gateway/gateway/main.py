from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from gateway.api.routes import router
from gateway.core.config import get_settings
from shared.app_core.http import install_request_logging
from shared.app_core.logging import configure_logging, get_logger
from shared.app_core.metrics import install_metrics
from shared.app_core.security import decode_token

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(settings.service_name)

PUBLIC_PATH_PREFIXES = {
    "/health",
    "/status",
    "/user-service/status",
    "/rental-service/status",
    "/analytics-service/status",
    "/agentic-service/status",
    "/users/login",
    "/users/register",
    "/docs",
    "/metrics",
    "/openapi.json",
    "/redoc",
}

app = FastAPI(
    title="API Gateway",
    version="0.1.0",
    docs_url="/docs" if settings.gateway_docs_enabled else None,
    redoc_url="/redoc" if settings.gateway_docs_enabled else None,
    openapi_url="/openapi.json" if settings.gateway_docs_enabled else None,
)
app.state.logger = logger


@app.middleware("http")
async def jwt_validation_middleware(request: Request, call_next):
    path = request.url.path
    is_public = any(
        path == prefix or path.startswith(f"{prefix}/") for prefix in PUBLIC_PATH_PREFIXES
    )
    if is_public:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Missing bearer token"})

    token = auth_header.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token, settings.jwt_secret, settings.jwt_algorithm)
    except ValueError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    request.state.user_id = payload.get("sub")
    return await call_next(request)


install_metrics(
    app,
    settings.service_name,
    enabled=settings.metrics_enabled,
    token=settings.metrics_token,
)
install_request_logging(app, logger)
app.include_router(router)
logger.info("gateway_ready", registry=settings.service_registry)
