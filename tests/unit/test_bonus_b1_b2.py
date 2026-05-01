from __future__ import annotations

import json

import httpx
import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_agentic_recommendations_tool_uses_analytics_grpc(ai_runtime, monkeypatch):
    recorded: dict[str, object] = {}
    execute_tool = ai_runtime.chat_service.execute_tool
    tool_globals = execute_tool.__globals__

    class FakeChannel:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeAnalyticsStub:
        def __init__(self, _channel) -> None:
            pass

        async def GetRecommendations(self, request, timeout=None):
            recorded["category"] = request.category
            recorded["date"] = request.date
            recorded["limit"] = request.limit
            recorded["timeout"] = timeout
            return tool_globals["analytics_pb2"].AnalyticsResponse(
                json_data=json.dumps(
                    {
                        "date": request.date,
                        "recommendations": [
                            {
                                "productId": 42,
                                "name": "Rotary Hammer Drill",
                                "category": "tools",
                                "score": 11,
                            }
                        ],
                    }
                )
            )

    monkeypatch.setattr(tool_globals["grpc"].aio, "insecure_channel", lambda _addr: FakeChannel())
    monkeypatch.setattr(
        tool_globals["analytics_pb2_grpc"],
        "AnalyticsServiceStub",
        FakeAnalyticsStub,
    )

    result = await execute_tool(
        "get_recommendations",
        {"category": "tools"},
        ai_runtime.core_config.get_settings(),
    )

    assert recorded["category"] == "tools"
    assert recorded["limit"] == 3
    assert recorded["timeout"] == 30.0
    assert result.result["recommendations"] == ["Rotary Hammer Drill"]
    assert "gRPC" in result.result["note"]


@pytest.mark.asyncio
async def test_agentic_top_category_tool_uses_analytics_grpc(ai_runtime, monkeypatch):
    execute_tool = ai_runtime.chat_service.execute_tool
    tool_globals = execute_tool.__globals__

    class FakeChannel:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeAnalyticsStub:
        def __init__(self, _channel) -> None:
            pass

        async def GetTrends(self, request, timeout=None):
            assert request.category == ""
            assert timeout is None
            return tool_globals["analytics_pb2"].AnalyticsResponse(
                json_data=json.dumps(
                    {"total_products": 10, "by_category": {"tools": 6, "outdoor": 4}}
                )
            )

    monkeypatch.setattr(tool_globals["grpc"].aio, "insecure_channel", lambda _addr: FakeChannel())
    monkeypatch.setattr(
        tool_globals["analytics_pb2_grpc"],
        "AnalyticsServiceStub",
        FakeAnalyticsStub,
    )

    result = await execute_tool(
        "get_top_category",
        {},
        ai_runtime.core_config.get_settings(),
    )

    assert result.result["top_category"] == "Tools"
    assert result.result["rental_count"] == 6


@pytest.mark.asyncio
async def test_central_api_client_retries_then_succeeds(monkeypatch, capsys):
    from shared.app_core.central_api import CentralAPIClient

    responses = [
        httpx.Response(429, json={"retryAfterSeconds": 18}),
        httpx.Response(429, json={"retryAfterSeconds": 18}),
        httpx.Response(200, json={"ok": True}),
    ]
    waits: list[int] = []

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None, headers=None):
            return responses.pop(0)

    async def fake_sleep(seconds: int) -> None:
        waits.append(seconds)

    monkeypatch.setattr("shared.app_core.central_api.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr("shared.app_core.central_api.asyncio.sleep", fake_sleep)
    monkeypatch.setattr("shared.app_core.central_api.random.uniform", lambda _a, _b: 1.0)

    client = CentralAPIClient("https://example.com", "token")
    payload = await client.get("/api/data/products")

    assert payload == {"ok": True}
    assert waits == [18, 36]
    stdout = capsys.readouterr().out
    assert "[retry 1/3] waiting 18s before retrying GET /api/data/products" in stdout
    assert "[retry 2/3] waiting 36s before retrying GET /api/data/products" in stdout


@pytest.mark.asyncio
async def test_central_api_client_returns_required_503_after_three_failed_retries(
    monkeypatch, capsys
):
    from shared.app_core.central_api import CentralAPIClient

    responses = [
        httpx.Response(429, json={"retryAfterSeconds": 18}),
        httpx.Response(429, json={"retryAfterSeconds": 18}),
        httpx.Response(429, json={"retryAfterSeconds": 18}),
        httpx.Response(429, json={"retryAfterSeconds": 18}),
    ]
    waits: list[int] = []

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None, headers=None):
            return responses.pop(0)

    async def fake_sleep(seconds: int) -> None:
        waits.append(seconds)

    monkeypatch.setattr("shared.app_core.central_api.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr("shared.app_core.central_api.asyncio.sleep", fake_sleep)
    monkeypatch.setattr("shared.app_core.central_api.random.uniform", lambda _a, _b: 1.0)

    client = CentralAPIClient("https://example.com", "token")

    with pytest.raises(HTTPException) as exc_info:
        await client.get("/api/data/products")

    assert waits == [18, 36, 72]
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == {
        "error": "Central API unavailable after 3 retries",
        "lastRetryAfter": 72,
        "suggestion": "Try again in ~2 minutes",
    }
    stdout = capsys.readouterr().out
    assert "[retry 3/3] waiting 72s before retrying GET /api/data/products" in stdout
