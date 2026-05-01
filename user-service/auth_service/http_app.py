from auth_service.api.routes import router
from auth_service.core.config import get_settings
from shared.app_core.logging import get_logger
from shared.app_core.service_runtime import build_service_app


def create_app():
    settings = get_settings()
    logger = get_logger(settings.service_name)
    return build_service_app(
        title="User Service",
        version="0.1.0",
        settings=settings,
        router=router,
        logger=logger,
    )


app = create_app()
