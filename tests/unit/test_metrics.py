import importlib
import sys
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

install_metrics = importlib.import_module("shared.app_core.metrics").install_metrics


@pytest.mark.anyio
async def test_gateway_metrics_are_public_and_exclude_self_scrapes(gateway_runtime):
    transport = httpx.ASGITransport(app=gateway_runtime.main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        health_response = await client.get("/health")
        assert health_response.status_code == 200

        unauthorized_response = await client.get("/items")
        assert unauthorized_response.status_code == 401

        metrics_response = await client.get("/metrics")
        assert metrics_response.status_code == 200

    body = metrics_response.text
    assert "hackspark_http_requests_total" in body
    assert "hackspark_http_request_duration_seconds_bucket" in body
    assert 'service="api-gateway"' in body
    assert 'path_template="/health"' in body
    assert 'path_template="/items"' in body
    assert 'status_code="401"' in body
    assert 'path_template="/metrics"' not in body


@pytest.mark.anyio
async def test_metrics_endpoint_can_be_disabled():
    app = FastAPI()
    install_metrics(app, "test-service", enabled=False)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/metrics")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_metrics_endpoint_requires_token_when_configured():
    app = FastAPI()
    install_metrics(app, "test-service", token="metrics-secret")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        unauthorized_response = await client.get("/metrics")
        assert unauthorized_response.status_code == 401

        wrong_token_response = await client.get(
            "/metrics",
            headers={"X-Metrics-Token": "wrong-token"},
        )
        assert wrong_token_response.status_code == 401

        authorized_response = await client.get(
            "/metrics",
            headers={"Authorization": "Bearer metrics-secret"},
        )
        assert authorized_response.status_code == 200

    assert "hackspark_http_requests_total" in authorized_response.text


@pytest.mark.anyio
async def test_internal_services_expose_metrics(auth_runtime, item_runtime, ai_runtime):
    runtimes = [
        (auth_runtime, "auth-service"),
        (item_runtime, "item-service"),
        (ai_runtime, "ai-agent-service"),
    ]

    for runtime, service_name in runtimes:
        transport = httpx.ASGITransport(app=runtime.main.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            health_response = await client.get("/health")
            assert health_response.status_code == 200

            metrics_response = await client.get("/metrics")
            assert metrics_response.status_code == 200

        body = metrics_response.text
        assert "hackspark_http_requests_total" in body
        assert "hackspark_http_request_duration_seconds_count" in body
        assert f'service="{service_name}"' in body
        assert 'path_template="/health"' in body
