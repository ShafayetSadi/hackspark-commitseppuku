import json
from typing import Any, cast

import grpc
import grpc.aio
from fastapi import HTTPException

from rental_service.core.config import RentalSettings, get_settings
from rental_service.services.central_api import get_central_client
from rental_service.services.rentals import (
    get_kth_busiest_date,
    get_longest_free_streak,
    get_product_availability,
    get_user_top_categories,
    list_products,
)
from shared.app_core.logging import get_logger
from shared.grpc_gen import rental_pb2, rental_pb2_grpc

logger = get_logger("rental-service")
RENTAL_PB2 = cast(Any, rental_pb2)


class RentalServicer(rental_pb2_grpc.RentalServiceServicer):
    def __init__(self) -> None:
        self._settings = get_settings()

    def _settings_for_client(self) -> RentalSettings:
        return self._settings

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

    async def ListProducts(self, request: Any, context: grpc.aio.ServicerContext):
        logger.info("grpc_list_products", category=request.category)
        try:
            data = await list_products(
                get_central_client(self._settings_for_client()),
                category=request.category or None,
                page=request.page or None,
                limit=request.limit or None,
                extra_params=dict(request.extra_params),
            )
            return RENTAL_PB2.ProductsResponse(json_data=json.dumps(data))
        except HTTPException as exc:
            logger.error("list_products_error", status_code=exc.status_code, detail=str(exc.detail))
            await self._abort_from_http_error(context, exc)
        except Exception as exc:
            logger.error("list_products_error", error=str(exc))
            await context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))

    async def GetProduct(self, request: Any, context: grpc.aio.ServicerContext):
        logger.info("grpc_get_product", product_id=request.product_id)
        try:
            data = await get_central_client(self._settings_for_client()).get(
                f"/api/data/products/{request.product_id}"
            )
            return RENTAL_PB2.ProductResponse(json_data=json.dumps(data))
        except HTTPException as exc:
            logger.error("get_product_error", status_code=exc.status_code, detail=str(exc.detail))
            await self._abort_from_http_error(context, exc)
        except Exception as exc:
            logger.error("get_product_error", error=str(exc))
            await context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))

    async def GetAvailability(self, request: Any, context: grpc.aio.ServicerContext):
        logger.info(
            "grpc_get_availability",
            product_id=request.product_id,
            from_date=request.from_date,
            to_date=request.to_date,
        )
        try:
            data = await get_product_availability(
                get_central_client(self._settings_for_client()),
                product_id=request.product_id,
                from_date=request.from_date,
                to_date=request.to_date,
            )
            return RENTAL_PB2.AvailabilityResponse(
                product_id=data["productId"],
                from_date=data["from"],
                to_date=data["to"],
                available=data["available"],
                busy_periods=[
                    RENTAL_PB2.DateRange(start=item["start"], end=item["end"])
                    for item in data["busyPeriods"]
                ],
                free_windows=[
                    RENTAL_PB2.DateRange(start=item["start"], end=item["end"])
                    for item in data["freeWindows"]
                ],
            )
        except HTTPException as exc:
            logger.error(
                "availability_error",
                status_code=exc.status_code,
                detail=str(exc.detail),
            )
            await self._abort_from_http_error(context, exc)
        except Exception as exc:
            logger.error("availability_error", error=str(exc))
            await context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))

    async def GetKthBusiestDate(self, request: Any, context: grpc.aio.ServicerContext):
        logger.info(
            "grpc_get_kth_busiest_date",
            from_month=request.from_month,
            to_month=request.to_month,
            k=request.k,
        )
        try:
            data = await get_kth_busiest_date(
                get_central_client(self._settings_for_client()),
                from_month=request.from_month,
                to_month=request.to_month,
                k=request.k,
            )
            return RENTAL_PB2.KthBusiestDateResponse(
                from_month=data["from"],
                to_month=data["to"],
                k=data["k"],
                date=data["date"],
                rental_count=data["rentalCount"],
            )
        except HTTPException as exc:
            logger.error(
                "kth_busiest_date_error",
                status_code=exc.status_code,
                detail=str(exc.detail),
            )
            await self._abort_from_http_error(context, exc)
        except Exception as exc:
            logger.error("kth_busiest_date_error", error=str(exc))
            await context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))

    async def GetUserTopCategories(self, request: Any, context: grpc.aio.ServicerContext):
        logger.info("grpc_get_user_top_categories", user_id=request.user_id, k=request.k)
        try:
            data = await get_user_top_categories(
                get_central_client(self._settings_for_client()),
                user_id=request.user_id,
                k=request.k,
            )
            return RENTAL_PB2.UserTopCategoriesResponse(
                user_id=data["userId"],
                top_categories=[
                    RENTAL_PB2.CategoryCount(
                        category=item["category"],
                        rental_count=item["rentalCount"],
                    )
                    for item in data["topCategories"]
                ],
            )
        except HTTPException as exc:
            logger.error(
                "user_top_categories_error",
                status_code=exc.status_code,
                detail=str(exc.detail),
            )
            await self._abort_from_http_error(context, exc)
        except Exception as exc:
            logger.error("user_top_categories_error", error=str(exc))
            await context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))

    async def GetLongestFreeStreak(self, request: Any, context: grpc.aio.ServicerContext):
        logger.info(
            "grpc_get_longest_free_streak", product_id=request.product_id, year=request.year
        )
        try:
            data = await get_longest_free_streak(
                get_central_client(self._settings_for_client()),
                product_id=request.product_id,
                year=request.year,
            )
            streak = data["longestFreeStreak"]
            return RENTAL_PB2.LongestFreeStreakResponse(
                product_id=data["productId"],
                year=data["year"],
                longest_free_streak=RENTAL_PB2.FreeStreak(
                    from_date=streak["from"],
                    to_date=streak["to"],
                    days=streak["days"],
                ),
            )
        except HTTPException as exc:
            logger.error(
                "longest_free_streak_error",
                status_code=exc.status_code,
                detail=str(exc.detail),
            )
            await self._abort_from_http_error(context, exc)
        except Exception as exc:
            logger.error("longest_free_streak_error", error=str(exc))
            await context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))
