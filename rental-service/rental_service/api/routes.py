from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from rental_service.core.config import RentalSettings, get_settings
from shared.app_core.central_api import CentralAPIClient

router = APIRouter()


def _client(settings: RentalSettings) -> CentralAPIClient:
    return CentralAPIClient(settings.central_api_url, settings.central_api_token)


@router.get("/status")
async def status() -> dict:
    return {"service": "rental-service", "status": "OK"}


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok", "service": "rental-service"}


@router.get("/products")
async def list_products(
    request: Request,
    settings: RentalSettings = Depends(get_settings),
):
    params = dict(request.query_params)
    data = await _client(settings).get("/api/data/products", params=params)
    return JSONResponse(content=data, status_code=200)


@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    settings: RentalSettings = Depends(get_settings),
):
    data = await _client(settings).get(f"/api/data/products/{product_id}")
    return JSONResponse(content=data, status_code=200)
