import asyncio

import grpc.aio

from ai_agent_service.core.config import get_settings
from ai_agent_service.grpc_service import AgenticServicer
from ai_agent_service.http_app import app
from ai_agent_service.services import session_store
from shared.app_core.grpc_interceptors import register_health
from shared.app_core.logging import configure_logging, get_logger
from shared.app_core.service_runtime import serve_http_and_grpc
from shared.grpc_gen import agentic_pb2_grpc

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(settings.service_name)


async def serve() -> None:
    session_store.init_mongo(settings.mongo_uri)

    server = grpc.aio.server()
    agentic_pb2_grpc.add_AgenticServiceServicer_to_server(AgenticServicer(), server)
    register_health(server, settings.service_name)
    await serve_http_and_grpc(
        grpc_server=server,
        grpc_port=settings.grpc_port,
        http_app=app,
        http_port=settings.service_port,
        logger=logger,
        log_event="agentic_service_started",
        extra_log_fields={"llm": settings.llm_provider},
    )


if __name__ == "__main__":
    asyncio.run(serve())
