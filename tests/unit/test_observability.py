import importlib
import json
import logging
import sys
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

install_request_logging = importlib.import_module("shared.app_core.http").install_request_logging
logging_module = importlib.import_module("shared.app_core.logging")
configure_logging = logging_module.configure_logging
get_logger = logging_module.get_logger


class FakeLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, str, dict[str, object]]] = []

    def info(self, event: str, **fields) -> None:
        self.records.append(("info", event, fields))

    def exception(self, event: str, **fields) -> None:
        self.records.append(("exception", event, fields))


@pytest.mark.asyncio
async def test_request_logging_propagates_request_id_and_redacts_query_values():
    logger = FakeLogger()
    app = FastAPI()
    install_request_logging(app, logger)

    @app.get("/echo")
    async def echo(request: Request):
        return JSONResponse({"request_id": request.state.request_id})

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(
            "/echo?token=super-secret&page=2",
            headers={"X-Request-ID": "req-123"},
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"
    assert response.json() == {"request_id": "req-123"}

    assert logger.records[0] == (
        "info",
        "request_started",
        {
            "request_id": "req-123",
            "method": "GET",
            "path": "/echo",
            "has_query_params": True,
            "query_keys": ["page", "token"],
            "client_host": "127.0.0.1",
        },
    )
    assert logger.records[1][0] == "info"
    assert logger.records[1][1] == "request_completed"
    assert logger.records[1][2]["request_id"] == "req-123"
    assert "query" not in logger.records[0][2]


@pytest.mark.asyncio
async def test_request_logging_returns_request_id_on_internal_error():
    logger = FakeLogger()
    app = FastAPI()
    install_request_logging(app, logger)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("broken")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Internal server error"
    assert "request_id" in body
    assert logger.records[0][1] == "request_started"
    assert logger.records[1][0] == "exception"
    assert logger.records[1][1] == "request_failed"
    assert logger.records[1][2]["request_id"] == body["request_id"]


def test_configure_logging_formats_structlog_and_stdlib_as_json(capsys):
    configure_logging("INFO")

    logging.getLogger("uvicorn.error").info("booting")
    logging.getLogger("stdlib-service").info("stdlib_event")
    get_logger("test-service").info("structured_event", ok=True)

    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]

    assert any(line["event"] == "booting" and line["logger"] == "uvicorn.error" for line in lines)
    assert any(
        line["event"] == "stdlib_event" and line["logger"] == "stdlib-service" for line in lines
    )
    assert any(
        line["event"] == "structured_event"
        and line["logger"] == "test-service"
        and line["ok"] is True
        for line in lines
    )
