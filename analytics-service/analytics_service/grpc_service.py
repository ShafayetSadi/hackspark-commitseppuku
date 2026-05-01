import json

import grpc
import grpc.aio

from analytics_service.core.config import get_settings
from analytics_service.services.analytics import (
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
