import json

import pytest
from conftest import AsyncSessionAdapter
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


@pytest.mark.anyio
@pytest.mark.integration
async def test_end_to_end_flow(
    gateway_runtime,
    auth_runtime,
    item_runtime,
    ai_runtime,
    monkeypatch,
):
    gateway_settings = gateway_runtime.core_config.get_settings()
    auth_settings = auth_runtime.core_config.get_settings()
    ai_settings = ai_runtime.core_config.get_settings()

    async def fake_forward_request(
        request: Request,
        upstream_base: str,
        subpath: str = "",
        **kwargs,
    ):
        body = await request.body()
        payload = json.loads(body.decode()) if body else {}

        if upstream_base == gateway_settings.auth_service_url:
            with auth_runtime.session_factory() as sync_session:
                session = AsyncSessionAdapter(sync_session)
                if request.method == "POST" and subpath == "register":
                    response = await auth_runtime.api_routes.register(
                        auth_runtime.schemas.RegisterRequest(**payload),
                        session=session,
                        settings=auth_settings,
                    )
                    return JSONResponse(status_code=201, content=jsonable_encoder(response))
                if request.method == "GET" and subpath == "me":
                    downstream_request = build_request("/me", headers=dict(request.headers))
                    downstream_request.state.user_id = request.state.user_id
                    current_user = await auth_runtime.api_dependencies.get_current_user(
                        downstream_request,
                        session=session,
                    )
                    response = await auth_runtime.api_routes.me(current_user)
                    return JSONResponse(status_code=200, content=jsonable_encoder(response))

        if upstream_base == gateway_settings.item_service_url:
            with item_runtime.session_factory() as sync_session:
                session = AsyncSessionAdapter(sync_session)
                if request.method == "POST" and subpath == "items":
                    response = await item_runtime.api_routes.post_item(
                        item_runtime.schemas.ItemCreateRequest(**payload),
                        session=session,
                    )
                    return JSONResponse(status_code=201, content=jsonable_encoder(response))

        if upstream_base == gateway_settings.ai_agent_service_url:
            if request.method == "POST" and subpath == "chat":
                response = await ai_runtime.api_routes.chat(
                    ai_runtime.schemas.ChatRequest(**payload),
                    settings=ai_settings,
                )
                return JSONResponse(status_code=200, content=jsonable_encoder(response))

        raise AssertionError(f"Unexpected proxy call: {request.method} {upstream_base}/{subpath}")

    monkeypatch.setattr(gateway_runtime.api_routes, "forward_request", fake_forward_request)

    register_request = build_request(
        "/auth/register",
        method="POST",
        body={"email": "team@example.com", "password": "password123", "full_name": "Hack Team"},
    )
    register_response = await gateway_runtime.api_routes.auth_proxy(
        "register",
        register_request,
        settings=gateway_settings,
    )
    token = json.loads(register_response.body.decode())["access_token"]

    me_response = await gateway_runtime.main.jwt_validation_middleware(
        build_request("/auth/me", headers={"Authorization": f"Bearer {token}"}),
        lambda req: gateway_runtime.api_routes.auth_proxy("me", req, settings=gateway_settings),
    )
    assert me_response.status_code == 200

    item_response = await gateway_runtime.main.jwt_validation_middleware(
        build_request(
            "/items",
            method="POST",
            headers={"Authorization": f"Bearer {token}"},
            body={"name": "Camera", "category": "rental", "quantity": 3},
        ),
        lambda req: gateway_runtime.api_routes.items_root_proxy(req, settings=gateway_settings),
    )
    assert item_response.status_code == 201

    ai_response = await gateway_runtime.main.jwt_validation_middleware(
        build_request(
            "/ai/chat",
            method="POST",
            headers={"Authorization": f"Bearer {token}"},
            body={"query": "How does JWT auth protect inventory endpoints?", "top_k": 2},
        ),
        lambda req: gateway_runtime.api_routes.ai_chat_proxy(req, settings=gateway_settings),
    )
    assert ai_response.status_code == 200
    assert json.loads(ai_response.body.decode())["sources"] == [
        "security/auth.md",
        "catalog/items.md",
    ]


def build_request(
    path: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict | None = None,
) -> Request:
    body_bytes = json.dumps(body).encode() if body is not None else b""

    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "state": {},
        "headers": [
            (key.lower().encode(), value.encode()) for key, value in (headers or {}).items()
        ],
    }
    return Request(scope, receive=receive)
