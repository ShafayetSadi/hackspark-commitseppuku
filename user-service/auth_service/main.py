import asyncio

import grpc.aio

from auth_service.core.config import get_settings
from auth_service.db.session import engine
from auth_service.grpc_service import UserServicer
from auth_service.http_app import app
from shared.app_core.database import validate_required_schema
from shared.app_core.grpc_interceptors import register_health
from shared.app_core.logging import configure_logging, get_logger
from shared.app_core.service_runtime import serve_http_and_grpc
from shared.grpc_gen import user_pb2_grpc

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(settings.service_name)


async def serve() -> None:
    await validate_required_schema(
        engine,
        version_table="alembic_version_auth",
        required_tables={"users": {"id", "email", "full_name", "hashed_password"}},
    )

    server = grpc.aio.server()
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)
    register_health(server, settings.service_name)
    await serve_http_and_grpc(
        grpc_server=server,
        grpc_port=settings.grpc_port,
        http_app=app,
        http_port=settings.service_port,
        logger=logger,
        log_event="user_service_started",
    )


if __name__ == "__main__":
    asyncio.run(serve())
