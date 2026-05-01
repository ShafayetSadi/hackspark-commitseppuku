import asyncio

import grpc.aio
import uvicorn
from fastapi import APIRouter, FastAPI

from shared.app_core.config import CommonSettings
from shared.app_core.http import install_request_logging
from shared.app_core.metrics import install_metrics


def build_service_app(
    *,
    title: str,
    version: str,
    settings: CommonSettings,
    router: APIRouter,
    logger,
) -> FastAPI:
    app = FastAPI(
        title=title,
        version=version,
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
    return app


async def serve_http_and_grpc(
    *,
    grpc_server: grpc.aio.Server,
    grpc_port: int,
    http_app: FastAPI,
    http_port: int,
    logger,
    log_event: str,
    extra_log_fields: dict[str, object] | None = None,
) -> None:
    grpc_listen_addr = f"[::]:{grpc_port}"
    grpc_server.add_insecure_port(grpc_listen_addr)

    http_server = uvicorn.Server(
        uvicorn.Config(
            http_app,
            host="0.0.0.0",
            port=http_port,
            log_config=None,
            access_log=False,
        )
    )

    await grpc_server.start()
    logger.info(
        log_event,
        grpc_addr=grpc_listen_addr,
        http_addr=f"0.0.0.0:{http_port}",
        **(extra_log_fields or {}),
    )

    grpc_task = asyncio.create_task(grpc_server.wait_for_termination())
    http_task = asyncio.create_task(http_server.serve())

    try:
        done, _ = await asyncio.wait(
            {grpc_task, http_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        if grpc_task in done and not http_task.done():
            http_server.should_exit = True
            await http_task

        if http_task in done and not grpc_task.done():
            await grpc_server.stop(grace=5)
            await grpc_task
    finally:
        http_server.should_exit = True
        await grpc_server.stop(grace=5)
        await asyncio.gather(grpc_task, http_task, return_exceptions=True)
