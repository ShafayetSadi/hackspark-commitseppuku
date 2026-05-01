from fastapi import APIRouter, Depends, Request
from gateway.core.config import GatewaySettings, get_settings
from gateway.services.proxy import forward_request

router = APIRouter()


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok", "service": "api-gateway"}


@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def auth_proxy(
    path: str,
    request: Request,
    settings: GatewaySettings = Depends(get_settings),
):
    return await forward_request(request, settings.auth_service_url, path)


@router.api_route("/items", methods=["GET", "POST"])
async def items_root_proxy(
    request: Request,
    settings: GatewaySettings = Depends(get_settings),
):
    return await forward_request(request, settings.item_service_url, "items")


@router.api_route("/items/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def item_proxy(
    path: str,
    request: Request,
    settings: GatewaySettings = Depends(get_settings),
):
    return await forward_request(request, settings.item_service_url, f"items/{path}".strip("/"))


@router.api_route("/ai/chat", methods=["POST"])
async def ai_chat_proxy(
    request: Request,
    settings: GatewaySettings = Depends(get_settings),
):
    return await forward_request(request, settings.ai_agent_service_url, "chat")


@router.api_route("/ai/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def ai_proxy(
    path: str,
    request: Request,
    settings: GatewaySettings = Depends(get_settings),
):
    return await forward_request(request, settings.ai_agent_service_url, path)
