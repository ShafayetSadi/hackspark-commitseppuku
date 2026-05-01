"""Mapping between gRPC status codes and HTTP status codes for the gateway."""

import grpc
from fastapi import HTTPException

_GRPC_TO_HTTP: dict[grpc.StatusCode, int] = {
    grpc.StatusCode.OK: 200,
    grpc.StatusCode.NOT_FOUND: 404,
    grpc.StatusCode.UNAUTHENTICATED: 401,
    grpc.StatusCode.PERMISSION_DENIED: 403,
    grpc.StatusCode.INVALID_ARGUMENT: 400,
    grpc.StatusCode.ALREADY_EXISTS: 409,
    grpc.StatusCode.RESOURCE_EXHAUSTED: 429,
    grpc.StatusCode.DEADLINE_EXCEEDED: 504,
    grpc.StatusCode.UNAVAILABLE: 502,
    grpc.StatusCode.UNIMPLEMENTED: 501,
}


def grpc_to_http_exception(exc: grpc.RpcError) -> HTTPException:
    code: grpc.StatusCode = exc.code()  # type: ignore[union-attr]
    detail: str = exc.details() or str(code)  # type: ignore[union-attr]
    http_status = _GRPC_TO_HTTP.get(code, 500)
    return HTTPException(status_code=http_status, detail=detail)
