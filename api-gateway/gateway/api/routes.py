import asyncio
import json
from typing import Any, cast

import grpc
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from gateway.core.config import GatewaySettings, get_settings
from gateway.grpc_clients import agentic_client, analytics_client, rental_client, user_client
from pydantic import AliasChoices, BaseModel, Field

from shared.app_core.grpc_errors import grpc_to_http_exception
from shared.grpc_gen import agentic_pb2, analytics_pb2, rental_pb2, user_pb2

router = APIRouter()
AGENTIC_PB2 = cast(Any, agentic_pb2)
ANALYTICS_PB2 = cast(Any, analytics_pb2)
RENTAL_PB2 = cast(Any, rental_pb2)
USER_PB2 = cast(Any, user_pb2)


def _parse_query_int(value: str, *, field_name: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from exc


# ── Health / Status ─────────────────────────────────────────────────────────


async def _check_service_status(name: str, base_url: str) -> tuple[str, str]:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{base_url}/status")
        if response.status_code != 200:
            return name, "UNREACHABLE"
        payload = response.json()
        return name, payload.get("status", "UNREACHABLE")
    except Exception:
        return name, "UNREACHABLE"


@router.get("/status")
async def status(settings: GatewaySettings = Depends(get_settings)) -> dict:
    results = await asyncio.gather(
        _check_service_status("user-service", settings.user_service_url),
        _check_service_status("rental-service", settings.rental_service_url),
        _check_service_status("analytics-service", settings.analytics_service_url),
        _check_service_status("agentic-service", settings.agentic_service_url),
    )
    return {"service": "api-gateway", "status": "OK", "downstream": dict(results)}


@router.get("/{service_name}/status")
async def service_status(service_name: str, settings: GatewaySettings = Depends(get_settings)):
    upstream_base = settings.service_registry.get(service_name)
    if upstream_base is None:
        raise HTTPException(status_code=404, detail="Unknown service")

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{upstream_base}/status")
    except httpx.RequestError:
        return JSONResponse(
            status_code=502,
            content={"service": service_name, "status": "UNREACHABLE"},
        )

    if response.status_code != 200:
        return JSONResponse(
            status_code=502,
            content={"service": service_name, "status": "UNREACHABLE"},
        )

    return JSONResponse(status_code=200, content=response.json())


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "api-gateway"}


# ── User / Auth ──────────────────────────────────────────────────────────────


class RegisterBody(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(
        min_length=2,
        max_length=255,
        validation_alias=AliasChoices("name", "full_name"),
    )


class LoginBody(BaseModel):
    email: str
    password: str


@router.post("/users/register", status_code=201)
async def register(body: RegisterBody, settings: GatewaySettings = Depends(get_settings)):
    stub = user_client.get_stub(settings.user_service_addr)
    try:
        resp = await stub.Register(
            USER_PB2.RegisterRequest(email=body.email, password=body.password, full_name=body.name)
        )
        return {"access_token": resp.access_token, "token_type": resp.token_type}
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.post("/users/login")
async def login(body: LoginBody, settings: GatewaySettings = Depends(get_settings)):
    stub = user_client.get_stub(settings.user_service_addr)
    try:
        resp = await stub.Login(USER_PB2.LoginRequest(email=body.email, password=body.password))
        return {"access_token": resp.access_token, "token_type": resp.token_type}
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/users/me")
async def me(request: Request, settings: GatewaySettings = Depends(get_settings)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    stub = user_client.get_stub(settings.user_service_addr)
    try:
        resp = await stub.Me(USER_PB2.MeRequest(user_id=str(user_id)))
        return {"id": resp.id, "email": resp.email, "name": resp.full_name}
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/users/{user_id}/discount")
async def discount(user_id: int, settings: GatewaySettings = Depends(get_settings)):
    stub = user_client.get_stub(settings.user_service_addr)
    try:
        resp = await stub.GetDiscount(USER_PB2.DiscountRequest(user_id=user_id))
        return {
            "userId": resp.user_id,
            "securityScore": resp.security_score,
            "discountPercent": resp.discount_percent,
        }
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


# ── Rentals ──────────────────────────────────────────────────────────────────


@router.get("/rentals/products")
async def list_products(request: Request, settings: GatewaySettings = Depends(get_settings)):
    params = dict(request.query_params)
    stub = rental_client.get_stub(settings.rental_service_addr)
    try:
        resp = await stub.ListProducts(
            RENTAL_PB2.ProductsQuery(
                category=params.get("category", ""),
                page=params.get("page", ""),
                limit=params.get("limit", ""),
                extra_params={
                    key: value
                    for key, value in params.items()
                    if key not in {"category", "page", "limit"}
                },
            )
        )
        return JSONResponse(content=json.loads(resp.json_data))
    except grpc.RpcError as exc:
        http_exc = grpc_to_http_exception(exc)
        if isinstance(http_exc.detail, dict):
            return JSONResponse(status_code=http_exc.status_code, content=http_exc.detail)
        raise http_exc from exc


@router.get("/rentals/products/{product_id}")
async def get_product(product_id: int, settings: GatewaySettings = Depends(get_settings)):
    stub = rental_client.get_stub(settings.rental_service_addr)
    try:
        resp = await stub.GetProduct(RENTAL_PB2.GetProductRequest(product_id=product_id))
        return JSONResponse(content=json.loads(resp.json_data))
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/rentals/products/{product_id}/availability")
async def get_product_availability(
    product_id: int,
    request: Request,
    settings: GatewaySettings = Depends(get_settings),
):
    from_date = request.query_params.get("from", "")
    to_date = request.query_params.get("to", "")
    stub = rental_client.get_stub(settings.rental_service_addr)
    try:
        resp = await stub.GetAvailability(
            RENTAL_PB2.AvailabilityRequest(
                product_id=product_id,
                from_date=from_date,
                to_date=to_date,
            )
        )
        return {
            "productId": resp.product_id,
            "from": resp.from_date,
            "to": resp.to_date,
            "available": resp.available,
            "busyPeriods": [{"start": item.start, "end": item.end} for item in resp.busy_periods],
            "freeWindows": [{"start": item.start, "end": item.end} for item in resp.free_windows],
        }
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/rentals/kth-busiest-date")
async def kth_busiest_date(request: Request, settings: GatewaySettings = Depends(get_settings)):
    from_month = request.query_params.get("from", "")
    to_month = request.query_params.get("to", "")
    k = _parse_query_int(request.query_params.get("k", "0"), field_name="k")
    stub = rental_client.get_stub(settings.rental_service_addr)
    try:
        resp = await stub.GetKthBusiestDate(
            RENTAL_PB2.KthBusiestDateRequest(from_month=from_month, to_month=to_month, k=k)
        )
        return {
            "from": resp.from_month,
            "to": resp.to_month,
            "k": resp.k,
            "date": resp.date,
            "rentalCount": resp.rental_count,
        }
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/rentals/users/{user_id}/top-categories")
async def top_categories(
    user_id: int,
    request: Request,
    settings: GatewaySettings = Depends(get_settings),
):
    k = _parse_query_int(request.query_params.get("k", "5"), field_name="k")
    stub = rental_client.get_stub(settings.rental_service_addr)
    try:
        resp = await stub.GetUserTopCategories(
            RENTAL_PB2.UserTopCategoriesRequest(user_id=user_id, k=k)
        )
        return {
            "userId": resp.user_id,
            "topCategories": [
                {"category": item.category, "rentalCount": item.rental_count}
                for item in resp.top_categories
            ],
        }
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/rentals/products/{product_id}/free-streak")
async def free_streak(
    product_id: int,
    request: Request,
    settings: GatewaySettings = Depends(get_settings),
):
    year = _parse_query_int(request.query_params.get("year", "0"), field_name="year")
    stub = rental_client.get_stub(settings.rental_service_addr)
    try:
        resp = await stub.GetLongestFreeStreak(
            RENTAL_PB2.LongestFreeStreakRequest(product_id=product_id, year=year)
        )
        return {
            "productId": resp.product_id,
            "year": resp.year,
            "longestFreeStreak": {
                "from": resp.longest_free_streak.from_date,
                "to": resp.longest_free_streak.to_date,
                "days": resp.longest_free_streak.days,
            },
        }
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


# ── Analytics ─────────────────────────────────────────────────────────────────


@router.get("/analytics/trends")
async def get_trends(request: Request, settings: GatewaySettings = Depends(get_settings)):
    category = request.query_params.get("category", "")
    stub = analytics_client.get_stub(settings.analytics_service_addr)
    try:
        resp = await stub.GetTrends(ANALYTICS_PB2.TrendsRequest(category=category))
        return JSONResponse(content=json.loads(resp.json_data))
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/analytics/surge")
async def get_surge(request: Request, settings: GatewaySettings = Depends(get_settings)):
    category = request.query_params.get("category", "")
    stub = analytics_client.get_stub(settings.analytics_service_addr)
    try:
        resp = await stub.GetSurge(ANALYTICS_PB2.SurgeRequest(category=category))
        return JSONResponse(content=json.loads(resp.json_data))
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/analytics/recommendations")
async def get_recommendations(request: Request, settings: GatewaySettings = Depends(get_settings)):
    category = request.query_params.get("category", "")
    limit = int(request.query_params.get("limit", "5"))
    stub = analytics_client.get_stub(settings.analytics_service_addr)
    try:
        resp = await stub.GetRecommendations(
            ANALYTICS_PB2.RecommendationsRequest(category=category, limit=limit)
        )
        return JSONResponse(content=json.loads(resp.json_data))
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


# ── Chat ──────────────────────────────────────────────────────────────────────


class ChatBody(BaseModel):
    query: str = Field(min_length=5, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=5)
    session_id: str = ""


@router.post("/chat")
async def chat(body: ChatBody, settings: GatewaySettings = Depends(get_settings)):
    stub = agentic_client.get_stub(settings.agentic_service_addr)
    try:
        resp = await stub.Chat(
            AGENTIC_PB2.ChatRequest(query=body.query, top_k=body.top_k, session_id=body.session_id)
        )
        return {
            "answer": resp.answer,
            "sources": list(resp.sources),
            "confidence": resp.confidence,
            "session_id": resp.session_id,
        }
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc
