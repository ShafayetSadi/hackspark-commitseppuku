import json

import pytest
from fastapi import Request

from shared.app_core.security import create_access_token


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


@pytest.mark.asyncio
@pytest.mark.integration
async def test_end_to_end_gateway_flow(gateway_runtime, monkeypatch):
    settings = gateway_runtime.core_config.get_settings()

    class UserStub:
        async def Register(self, request):
            assert request.email == "team@example.com"
            token = create_access_token(
                subject="42",
                secret=settings.jwt_secret,
                algorithm=settings.jwt_algorithm,
                expires_minutes=settings.access_token_expire_minutes,
            )
            return gateway_runtime.api_routes.USER_PB2.AuthResponse(
                access_token=token,
                token_type="bearer",
            )

        async def Me(self, request):
            assert request.user_id == "42"
            return gateway_runtime.api_routes.USER_PB2.UserResponse(
                id=42,
                email="team@example.com",
                full_name="Hack Team",
            )

    class AgenticStub:
        async def Chat(self, request):
            assert request.session_id == ""
            return gateway_runtime.api_routes.AGENTIC_PB2.ChatResponse(
                answer="JWT auth protects inventory endpoints by requiring a bearer token.",
                sources=["security/auth.md", "catalog/items.md"],
                confidence=0.92,
                session_id="session-1",
            )

    monkeypatch.setattr(
        gateway_runtime.api_routes.user_client, "get_stub", lambda _addr: UserStub()
    )
    monkeypatch.setattr(
        gateway_runtime.api_routes.agentic_client, "get_stub", lambda _addr: AgenticStub()
    )

    register_response = await gateway_runtime.api_routes.register(
        gateway_runtime.api_routes.RegisterBody(
            email="team@example.com",
            password="password123",
            name="Hack Team",
        ),
        settings=settings,
    )
    token = register_response["access_token"]

    me_response = await gateway_runtime.main.jwt_validation_middleware(
        build_request("/users/me", headers={"Authorization": f"Bearer {token}"}),
        lambda req: gateway_runtime.api_routes.me(req, settings=settings),
    )
    assert me_response == {
        "id": 42,
        "email": "team@example.com",
        "name": "Hack Team",
    }

    chat_response = await gateway_runtime.main.jwt_validation_middleware(
        build_request(
            "/chat",
            method="POST",
            headers={"Authorization": f"Bearer {token}"},
            body={"query": "How does JWT auth protect inventory endpoints?", "top_k": 2},
        ),
        lambda req: gateway_runtime.api_routes.chat(
            gateway_runtime.api_routes.ChatBody(
                query="How does JWT auth protect inventory endpoints?",
                top_k=2,
                session_id="",
            ),
            settings=settings,
        ),
    )
    assert chat_response["sources"] == ["security/auth.md", "catalog/items.md"]
    assert chat_response["session_id"] == "session-1"
