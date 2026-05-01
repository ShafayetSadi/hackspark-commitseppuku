from fastapi import FastAPI

from ai_agent_service.api.routes import router
from ai_agent_service.core.config import get_settings
from shared.app_core.http import install_request_logging
from shared.app_core.logging import configure_logging, get_logger
from shared.app_core.metrics import install_metrics

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(settings.service_name)

app = FastAPI(
    title="AI Agent Service",
    version="0.1.0",
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

logger.info("ai_agent_service_configured", llm_provider=settings.llm_provider)
