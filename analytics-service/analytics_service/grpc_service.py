import json

import grpc
import grpc.aio
from fastapi import HTTPException

from analytics_service.core.config import get_settings
from analytics_service.services.analytics import (
    compute_peak_window,
    compute_recommendations,
    compute_surge,
    compute_trends,
)
from shared.app_core.central_api import CentralAPIClient
from shared.app_core.logging import get_logger
from shared.grpc_gen import analytics_pb2, analytics_pb2_grpc

logger = get_logger("analytics-service")


class AnalyticsServicer(analytics_pb2_grpc.AnalyticsServiceServicer):
    def __init__(self) -> None:
        self._settings = get_settings()

    def _client(self) -> CentralAPIClient:
        return CentralAPIClient(
            self._settings.central_api_url,
            self._settings.central_api_token,
            redis_url=self._settings.central_api_redis_url,
            max_calls=self._settings.central_api_rate_limit,
            window_seconds=self._settings.central_api_rate_window_seconds,
        )

    async def _abort_from_http_error(
        self, context: grpc.aio.ServicerContext, exc: HTTPException
    ) -> None:
        status_map = {
            400: grpc.StatusCode.INVALID_ARGUMENT,
            404: grpc.StatusCode.NOT_FOUND,
            401: grpc.StatusCode.UNAUTHENTICATED,
            409: grpc.StatusCode.ALREADY_EXISTS,
            429: grpc.StatusCode.RESOURCE_EXHAUSTED,
            502: grpc.StatusCode.UNAVAILABLE,
            504: grpc.StatusCode.DEADLINE_EXCEEDED,
        }
        status = status_map.get(exc.status_code, grpc.StatusCode.INTERNAL)
        detail = json.dumps(exc.detail) if exc.detail else f"HTTP {exc.status_code}"
        await context.abort(status, detail)

    async def GetTrends(
        self, request: analytics_pb2.TrendsRequest, context: grpc.aio.ServicerContext
    ):
        logger.info("grpc_get_trends", category=request.category or None)
        try:
            data = await compute_trends(self._client(), request.category or None)
            return analytics_pb2.AnalyticsResponse(json_data=json.dumps(data))
        except Exception as exc:
            logger.error("trends_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Analytics computation failed")

    async def GetSurge(
        self, request: analytics_pb2.SurgeRequest, context: grpc.aio.ServicerContext
    ):
        logger.info("grpc_get_surge", category=request.category or None)
        try:
            data = await compute_surge(self._client(), request.category or None)
            return analytics_pb2.AnalyticsResponse(json_data=json.dumps(data))
        except Exception as exc:
            logger.error("surge_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Analytics computation failed")

    async def GetRecommendations(
        self, request: analytics_pb2.RecommendationsRequest, context: grpc.aio.ServicerContext
    ):
        logger.info("grpc_get_recommendations", category=request.category or None)
        try:
            limit = request.limit if request.limit > 0 else 5
            data = await compute_recommendations(self._client(), request.category or None, limit)
            return analytics_pb2.AnalyticsResponse(json_data=json.dumps(data))
        except Exception as exc:
            logger.error("recommendations_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Analytics computation failed")

    async def GetPeakWindow(
        self, request: analytics_pb2.PeakWindowRequest, context: grpc.aio.ServicerContext
    ):
        logger.info(
            "grpc_get_peak_window",
            from_month=request.from_month,
            to_month=request.to_month,
        )
        try:
            data = await compute_peak_window(
                self._client(),
                from_month=request.from_month,
                to_month=request.to_month,
            )
            return analytics_pb2.AnalyticsResponse(json_data=json.dumps(data))
        except HTTPException as exc:
            logger.error("peak_window_error", status_code=exc.status_code, detail=str(exc.detail))
            await self._abort_from_http_error(context, exc)
        except Exception as exc:
            logger.error("peak_window_error", error=str(exc))
            await context.abort(grpc.StatusCode.INTERNAL, "Analytics computation failed")
