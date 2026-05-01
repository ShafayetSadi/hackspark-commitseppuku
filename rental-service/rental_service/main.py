import asyncio

import grpc.aio

from rental_service.core.config import get_settings
from rental_service.grpc_service import RentalServicer
from rental_service.http_app import app
from shared.app_core.grpc_interceptors import register_health
from shared.app_core.logging import configure_logging, get_logger
from shared.app_core.service_runtime import serve_http_and_grpc
from shared.grpc_gen import rental_pb2_grpc

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(settings.service_name)


async def serve() -> None:
    server = grpc.aio.server()
    rental_pb2_grpc.add_RentalServiceServicer_to_server(RentalServicer(), server)
    register_health(server, settings.service_name)
    await serve_http_and_grpc(
        grpc_server=server,
        grpc_port=settings.grpc_port,
        http_app=app,
        http_port=settings.service_port,
        logger=logger,
        log_event="rental_service_started",
    )


if __name__ == "__main__":
    asyncio.run(serve())
