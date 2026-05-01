from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from rental_service.core.config import RentalSettings, get_settings
from rental_service.services.central_api import get_central_client
from rental_service.services.rentals import (
    get_kth_busiest_date,
    get_longest_free_streak,
    get_merged_feed,
    get_product_availability,
    get_user_top_categories,
    parse_merged_feed_product_ids,
    require_merged_feed_limit,
)
from rental_service.services.rentals import (
    list_products as list_products_data,
)

router = APIRouter()


def _parse_int_param(value: str, *, field_name: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from exc


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
    data = await list_products_data(
        get_central_client(settings),
        category=params.get("category"),
        page=params.get("page"),
        limit=params.get("limit"),
        extra_params={
            key: value for key, value in params.items() if key not in {"category", "page", "limit"}
        },
    )
    return JSONResponse(content=data, status_code=200)


@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    settings: RentalSettings = Depends(get_settings),
):
    data = await get_central_client(settings).get(f"/api/data/products/{product_id}")
    return JSONResponse(content=data, status_code=200)


@router.get("/products/{product_id}/availability")
async def availability(
    product_id: int,
    from_date: str = Query(alias="from"),
    to_date: str = Query(alias="to"),
    settings: RentalSettings = Depends(get_settings),
):
    data = await get_product_availability(
        get_central_client(settings),
        product_id=product_id,
        from_date=from_date,
        to_date=to_date,
    )
    return JSONResponse(content=data, status_code=200)


@router.get("/kth-busiest-date")
async def kth_busiest_date(
    from_month: str = Query(alias="from"),
    to_month: str = Query(alias="to"),
    k: str = Query(),
    settings: RentalSettings = Depends(get_settings),
):
    data = await get_kth_busiest_date(
        get_central_client(settings),
        from_month=from_month,
        to_month=to_month,
        k=_parse_int_param(k, field_name="k"),
    )
    return JSONResponse(content=data, status_code=200)


@router.get("/users/{user_id}/top-categories")
async def top_categories(
    user_id: int,
    k: str = Query(default="5"),
    settings: RentalSettings = Depends(get_settings),
):
    data = await get_user_top_categories(
        get_central_client(settings),
        user_id=user_id,
        k=_parse_int_param(k, field_name="k"),
    )
    return JSONResponse(content=data, status_code=200)


@router.get("/products/{product_id}/free-streak")
async def free_streak(
    product_id: int,
    year: str = Query(),
    settings: RentalSettings = Depends(get_settings),
):
    data = await get_longest_free_streak(
        get_central_client(settings),
        product_id=product_id,
        year=_parse_int_param(year, field_name="year"),
    )
    return JSONResponse(content=data, status_code=200)


@router.get("/merged-feed")
async def merged_feed(
    product_ids: str = Query(alias="productIds"),
    limit: str = Query(),
    settings: RentalSettings = Depends(get_settings),
):
    data = await get_merged_feed(
        get_central_client(settings),
        product_ids=parse_merged_feed_product_ids(product_ids),
        limit=require_merged_feed_limit(_parse_int_param(limit, field_name="limit")),
    )
    return JSONResponse(content=data, status_code=200)
