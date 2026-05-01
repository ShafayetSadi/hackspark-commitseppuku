from __future__ import annotations

from dataclasses import dataclass
from hmac import compare_digest
from time import perf_counter

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)


@dataclass(slots=True)
class MetricsState:
    registry: CollectorRegistry
    requests_total: Counter
    request_duration_seconds: Histogram
    requests_in_flight: Gauge


def _build_metrics_state() -> MetricsState:
    registry = CollectorRegistry()
    return MetricsState(
        registry=registry,
        requests_total=Counter(
            "hackspark_http_requests_total",
            "Total HTTP requests processed by the app.",
            ("service", "method", "path_template", "status_code"),
            registry=registry,
        ),
        request_duration_seconds=Histogram(
            "hackspark_http_request_duration_seconds",
            "HTTP request latency in seconds.",
            ("service", "method", "path_template"),
            registry=registry,
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
        ),
        requests_in_flight=Gauge(
            "hackspark_http_requests_in_flight",
            "In-flight HTTP requests.",
            ("service",),
            registry=registry,
        ),
    )


def _resolve_path_template(request: Request) -> str:
    route = request.scope.get("route")
    path_template = getattr(route, "path", None)
    return path_template or request.url.path


def _extract_metrics_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    token_header = request.headers.get("X-Metrics-Token")
    if token_header:
        return token_header.strip()
    return None


def install_metrics(
    app: FastAPI,
    service_name: str,
    *,
    enabled: bool = True,
    token: str | None = None,
) -> None:
    if not enabled:
        return

    metrics = _build_metrics_state()
    app.state.metrics = metrics
    required_token = token.strip() if token else None

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint(request: Request) -> Response:
        if required_token is not None:
            provided_token = _extract_metrics_token(request)
            if provided_token is None or not compare_digest(provided_token, required_token):
                return Response(status_code=401, content="Unauthorized")

        return Response(
            content=generate_latest(metrics.registry),
            media_type=CONTENT_TYPE_LATEST,
        )

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        metrics.requests_in_flight.labels(service=service_name).inc()
        started_at = perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = perf_counter() - started_at
            path_template = _resolve_path_template(request)
            metrics.requests_total.labels(
                service=service_name,
                method=request.method,
                path_template=path_template,
                status_code=str(status_code),
            ).inc()
            metrics.request_duration_seconds.labels(
                service=service_name,
                method=request.method,
                path_template=path_template,
            ).observe(duration)
            metrics.requests_in_flight.labels(service=service_name).dec()
