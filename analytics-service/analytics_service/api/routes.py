from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from analytics_service.core.config import AnalyticsSettings, get_settings
from analytics_service.services.analytics import (
    compute_peak_window,
    compute_recommendations,
    compute_surge_days,
)
from shared.app_core.central_api import CentralAPIClient

router = APIRouter()


def _central_client(settings: AnalyticsSettings) -> CentralAPIClient:
    return CentralAPIClient(
        settings.central_api_url,
        settings.central_api_token,
    )


@router.get("/status")
async def status() -> dict:
    return {"service": "analytics-service", "status": "OK"}


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok", "service": "analytics-service"}


@router.get("/peak-window")
async def peak_window(
    from_month: str = Query(alias="from"),
    to_month: str = Query(alias="to"),
    settings: AnalyticsSettings = Depends(get_settings),
):
    data = await compute_peak_window(
        _central_client(settings),
        from_month=from_month,
        to_month=to_month,
    )
    return JSONResponse(content=data, status_code=200)


@router.get("/surge-days")
async def surge_days(
    month: str = Query(...),
    settings: AnalyticsSettings = Depends(get_settings),
):
    data = await compute_surge_days(
        _central_client(settings),
        month=month,
    )
    return JSONResponse(content=data, status_code=200)


@router.get("/recommendations")
async def recommendations(
    date: str = Query(...),
    limit: int = Query(5),
    settings: AnalyticsSettings = Depends(get_settings),
):
    data = await compute_recommendations(
        _central_client(settings),
        target_date=date,
        limit=limit,
    )
    return JSONResponse(content=data, status_code=200)
