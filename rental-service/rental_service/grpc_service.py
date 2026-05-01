import json

import grpc
import grpc.aio
from fastapi import HTTPException

from rental_service.core.config import get_settings
from shared.app_core.central_api import CentralAPIClient
from shared.app_core.logging import get_logger
from shared.grpc_gen import rental_pb2, rental_pb2_grpc

logger = get_logger("rental-service")


class RentalServicer(rental_pb2_grpc.RentalServiceServicer):
    def __init__(self) -> None:
        self._settings = get_settings()

    def _client(self) -> CentralAPIClient:
        return CentralAPIClient(self._settings.central_api_url, self._settings.central_api_token)

    async def _abort_from_http_error(
        self, context: grpc.aio.ServicerContext, exc: HTTPException
    ) -> None:
        status_map = {
            404: grpc.StatusCode.NOT_FOUND,
            429: grpc.StatusCode.RESOURCE_EXHAUSTED,
            502: grpc.StatusCode.UNAVAILABLE,
            504: grpc.StatusCode.DEADLINE_EXCEEDED,
        }
        status = status_map.get(exc.status_code, grpc.StatusCode.INTERNAL)
        detail = str(exc.detail) if exc.detail else f"HTTP {exc.status_code}"
        await context.abort(status, detail)

    async def ListProducts(
        self, request: rental_pb2.ProductsQuery, context: grpc.aio.ServicerContext
    ):
        logger.info("grpc_list_products", category=request.category)
        try:
            params: dict[str, str] = {}
            if request.category:
                params["category"] = request.category
            if request.page:
                params["page"] = request.page
            if request.limit:
                params["limit"] = request.limit
            data = await self._client().get("/api/data/products", params=params)
            return rental_pb2.ProductsResponse(json_data=json.dumps(data))
        except HTTPException as exc:
            logger.error("list_products_error", status_code=exc.status_code, detail=str(exc.detail))
            await self._abort_from_http_error(context, exc)
        except Exception as exc:
            logger.error("list_products_error", error=str(exc))
            await context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))

    async def GetProduct(
        self, request: rental_pb2.GetProductRequest, context: grpc.aio.ServicerContext
    ):
        logger.info("grpc_get_product", product_id=request.product_id)
        try:
            data = await self._client().get(f"/api/data/products/{request.product_id}")
            return rental_pb2.ProductResponse(json_data=json.dumps(data))
        except HTTPException as exc:
            logger.error("get_product_error", status_code=exc.status_code, detail=str(exc.detail))
            await self._abort_from_http_error(context, exc)
        except Exception as exc:
            logger.error("get_product_error", error=str(exc))
            await context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))
