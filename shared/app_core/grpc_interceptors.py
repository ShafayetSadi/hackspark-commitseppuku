"""gRPC server utilities shared across all services."""

import grpc
import grpc.aio
from grpc_health.v1 import health, health_pb2, health_pb2_grpc


def build_server(port: int) -> grpc.aio.Server:
    return grpc.aio.server()


def register_health(server: grpc.aio.Server, service_name: str) -> health.HealthServicer:
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    health_servicer.set(service_name, health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    return health_servicer
