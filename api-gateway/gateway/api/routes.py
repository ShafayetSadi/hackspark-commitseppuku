import asyncio
import json

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
    password: str
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
        resp: user_pb2.AuthResponse = await stub.Register(
            user_pb2.RegisterRequest(email=body.email, password=body.password, full_name=body.name)
        )
        return {"access_token": resp.access_token, "token_type": resp.token_type}
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.post("/users/login")
async def login(body: LoginBody, settings: GatewaySettings = Depends(get_settings)):
    stub = user_client.get_stub(settings.user_service_addr)
    try:
        resp: user_pb2.AuthResponse = await stub.Login(
            user_pb2.LoginRequest(email=body.email, password=body.password)
        )
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
        resp: user_pb2.UserResponse = await stub.Me(user_pb2.MeRequest(user_id=str(user_id)))
        return {"id": resp.id, "email": resp.email, "name": resp.full_name}
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


# ── Rentals ──────────────────────────────────────────────────────────────────


@router.get("/rentals/products")
async def list_products(request: Request, settings: GatewaySettings = Depends(get_settings)):
    params = dict(request.query_params)
    stub = rental_client.get_stub(settings.rental_service_addr)
    try:
        resp: rental_pb2.ProductsResponse = await stub.ListProducts(
            rental_pb2.ProductsQuery(
                category=params.get("category", ""),
                page=params.get("page", ""),
                limit=params.get("limit", ""),
            )
        )
        return JSONResponse(content=json.loads(resp.json_data))
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/rentals/products/{product_id}")
async def get_product(product_id: int, settings: GatewaySettings = Depends(get_settings)):
    stub = rental_client.get_stub(settings.rental_service_addr)
    try:
        resp: rental_pb2.ProductResponse = await stub.GetProduct(
            rental_pb2.GetProductRequest(product_id=product_id)
        )
        return JSONResponse(content=json.loads(resp.json_data))
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


# ── Analytics ─────────────────────────────────────────────────────────────────


@router.get("/analytics/trends")
async def get_trends(request: Request, settings: GatewaySettings = Depends(get_settings)):
    category = request.query_params.get("category", "")
    stub = analytics_client.get_stub(settings.analytics_service_addr)
    try:
        resp: analytics_pb2.AnalyticsResponse = await stub.GetTrends(
            analytics_pb2.TrendsRequest(category=category)
        )
        return JSONResponse(content=json.loads(resp.json_data))
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/analytics/surge")
async def get_surge(request: Request, settings: GatewaySettings = Depends(get_settings)):
    category = request.query_params.get("category", "")
    stub = analytics_client.get_stub(settings.analytics_service_addr)
    try:
        resp: analytics_pb2.AnalyticsResponse = await stub.GetSurge(
            analytics_pb2.SurgeRequest(category=category)
        )
        return JSONResponse(content=json.loads(resp.json_data))
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/analytics/recommendations")
async def get_recommendations(request: Request, settings: GatewaySettings = Depends(get_settings)):
    category = request.query_params.get("category", "")
    limit = int(request.query_params.get("limit", "5"))
    stub = analytics_client.get_stub(settings.analytics_service_addr)
    try:
        resp: analytics_pb2.AnalyticsResponse = await stub.GetRecommendations(
            analytics_pb2.RecommendationsRequest(category=category, limit=limit)
        )
        return JSONResponse(content=json.loads(resp.json_data))
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


# ── Chat ──────────────────────────────────────────────────────────────────────


class ChatBody(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=5)
    session_id: str | None = None


@router.post("/chat")
async def chat(body: ChatBody, settings: GatewaySettings = Depends(get_settings)):
    stub = agentic_client.get_stub(settings.agentic_service_addr)
    try:
        resp: agentic_pb2.ChatResponse = await stub.Chat(
            agentic_pb2.ChatRequest(
                query=body.query,
                top_k=body.top_k,
                session_id=body.session_id or "",
            )
        )
        return {
            "answer": resp.answer,
            "sources": list(resp.sources),
            "confidence": resp.confidence,
            "session_id": resp.session_id,
        }
    except grpc.RpcError as exc:
        raise grpc_to_http_exception(exc) from exc


@router.get("/chat/sessions")
async def chat_sessions(settings: GatewaySettings = Depends(get_settings)):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.agentic_service_url}/chat/sessions")
            response.raise_for_status()
        return JSONResponse(status_code=response.status_code, content=response.json())
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text or "Agentic service returned an error"
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Agentic service unavailable") from exc


@router.get("/chat/{session_id}/history")
async def chat_history(session_id: str, settings: GatewaySettings = Depends(get_settings)):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.agentic_service_url}/chat/{session_id}/history")
            response.raise_for_status()
        return JSONResponse(status_code=response.status_code, content=response.json())
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text or "Agentic service returned an error"
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Agentic service unavailable") from exc


@router.delete("/chat/{session_id}")
async def delete_chat_session(session_id: str, settings: GatewaySettings = Depends(get_settings)):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.delete(f"{settings.agentic_service_url}/chat/{session_id}")
            response.raise_for_status()
        return JSONResponse(status_code=response.status_code, content=response.json())
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text or "Agentic service returned an error"
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Agentic service unavailable") from exc
