# Observability

This document describes the logging and monitoring setup that is implemented in `hackspark` today. It is meant to be the source of truth for demos, debugging, and future observability changes.

## Overview

The repo uses two complementary observability layers:

- structured JSON logs from every FastAPI service
- Prometheus-compatible metrics exported by the gateway and each internal service

The Docker stack also includes:

- `prometheus` for scraping and querying metrics
- `grafana` for dashboarding
- `cadvisor` for container CPU and memory metrics

The goal is pragmatic hackathon visibility:

- trace a request across services with `X-Request-ID`
- inspect latency and error behavior quickly
- show a live dashboard during judging

## Logging

### Implementation Logging

Structured logging is configured in `shared/app_core/logging.py` using `structlog` with JSON output to stdout.

The current setup also normalizes stdlib and Uvicorn logs through the same JSON formatter and disables Uvicorn access logs in the service entrypoints so request logging is not duplicated.

Request logging is installed by `shared/app_core/http.py` in:

- `gateway/gateway/main.py`
- `services/auth_service/auth_service/main.py`
- `services/item-service/app/main.py`
- `services/ai_agent_service/ai_agent_service/main.py`

Each request emits:

- `request_started`
- `request_completed`
- `request_failed`

### Logged fields

Common fields in request logs:

- `request_id`
- `method`
- `path`
- `has_query_params`
- `query_keys`
- `client_host`
- `status_code` on completion
- `duration_ms`
- `timestamp`
- `level`
- `logger`

`request_failed` is emitted for unhandled exceptions and includes the request metadata plus the exception stack trace from `logger.exception(...)`.

The middleware intentionally logs only query parameter names, not raw query values, to avoid leaking tokens or other sensitive data into the default log stream.

### Request correlation

The middleware accepts an incoming `X-Request-ID` header when present. If the client does not send one, the app generates a UUID.

The resolved request id is:

- stored on `request.state.request_id`
- written into every request log event
- returned in the response header on successful responses
- returned in the JSON body for middleware-generated `500` responses

This is the easiest way to correlate:

1. a browser or `curl` response
2. gateway logs
3. downstream logs when the id is forwarded by the client or calling layer

### Example log flow

For a successful request, expect:

```json
{"request_id":"...","method":"POST","path":"/users/login","event":"request_started","timestamp":"...","level":"info"}
{"request_id":"...","method":"POST","path":"/users/login","status_code":200,"duration_ms":12.41,"event":"request_completed","timestamp":"...","level":"info"}
```

For an unhandled failure, expect:

```json
{"request_id":"...","method":"GET","path":"/items","duration_ms":4.87,"event":"request_failed","timestamp":"...","level":"error"}
```

### How to read logs

To stream the full stack:

```bash
docker compose logs -f
```

To stream one service:

```bash
docker compose logs -f api-gateway
docker compose logs -f auth-service
docker compose logs -f item-service
docker compose logs -f ai-agent-service
```

When debugging:

- start with the gateway log line for the failing route
- copy the `request_id`
- search for the same id in the relevant downstream container logs

## Metrics

### Implementation Metrics

Prometheus metrics are installed by `shared/app_core/metrics.py`.

Each app exposes:

- `GET /metrics`

The gateway exposes `/metrics` publicly without JWT auth. Internal services also expose `/metrics`, but they are intended to be scraped over the Compose network rather than called directly from outside.

Metrics can be controlled with environment settings:

- `METRICS_ENABLED=true|false` to enable/disable endpoint registration
- `METRICS_TOKEN=<token>` to require a token on `/metrics`

If `METRICS_TOKEN` is set, Prometheus scrape jobs must send the same token (for example via `authorization` or `http_headers` in `monitoring/prometheus/prometheus.yml`), otherwise scrapes will return `401` and targets will show as down.

Example Prometheus job when `METRICS_TOKEN` is enabled:

```yaml
- job_name: api-gateway
  metrics_path: /metrics
  authorization:
    type: Bearer
    credentials: ${METRICS_TOKEN}
  static_configs:
    - targets: ["api-gateway:8000"]
```

Metrics use a per-process Prometheus registry so tests and multi-app imports do not collide inside one Python process.

### Exported application metrics

The current app metrics are:

- `hackspark_http_requests_total`
- `hackspark_http_request_duration_seconds`
- `hackspark_http_requests_in_flight`

Metric labels:

- `service`
- `method`
- `path_template`
- `status_code` for request totals

Important behavior:

- route templates are used when available, such as `/items` or `/auth/{path:path}`, to avoid label explosion
- `/metrics` is excluded from request counting and latency measurement so Prometheus scrapes do not distort charts
- `/health` remains instrumented and visible

### Scrape targets

Prometheus is configured in `monitoring/prometheus/prometheus.yml` to scrape:

- `prometheus:9090/metrics`
- `api-gateway:8000/metrics`
- `auth-service:8000/metrics`
- `item-service:8000/metrics`
- `ai-agent-service:8000/metrics`
- `cadvisor:8080/metrics`

Prometheus also loads baseline rules from `monitoring/prometheus/rules/hackspark-alerts.yml`, including:

- recording rules for service request rate and 5xx rate
- `HacksparkTargetDown`
- `HacksparkHigh5xxRate`

### Dashboarding

Grafana is pre-provisioned from the repo with the `Hackspark Overview` dashboard.

The dashboard includes:

- request rate by service
- p95 latency by service
- route-level p95 latency
- 4xx and 5xx error rate
- route-level error rate
- in-flight requests by service
- Prometheus `up` status for services, Prometheus, and cAdvisor
- active alert count
- Prometheus health
- container CPU usage
- container memory usage

Provisioning files live under:

- `monitoring/grafana/provisioning/`
- `monitoring/grafana/dashboards/`

## Running the stack

Start dev:

```bash
docker compose -f docker-compose.yml up --build
```

Start prod-style:

```bash
docker compose -f docker-compose.prod.yml up --build
```

Useful URLs:

- gateway docs: `http://localhost:8000/docs`
- gateway metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Prometheus targets: `http://localhost:9090/targets`
- Prometheus alerts: `http://localhost:9090/alerts`
- Grafana: `http://localhost:3000`

Default Grafana credentials:

- username: `${GRAFANA_ADMIN_USER:-admin}`
- password: `${GRAFANA_ADMIN_PASSWORD:-admin}`

## Demo workflow

For a judging/demo pass:

1. Open Grafana and the `Hackspark Overview` dashboard.
2. Open the gateway docs at `http://localhost:8000/docs`.
3. Execute a few requests:
   - `POST /auth/register`
   - `POST /users/login`
   - `GET /auth/me`
   - `POST /items`
   - `GET /items`
   - `POST /ai/chat`
4. Show the dashboard panels changing in real time.
5. Trigger one intentional error, such as calling a protected route without a bearer token, and show the error-rate panel move.
6. Open the Prometheus alerts page and show that baseline alert rules are loaded even if none are firing.
7. Show one `X-Request-ID` in the logs to connect the UI request with backend telemetry.

## Operational notes

- The gateway is the main demo surface. Start there before inspecting internal services directly.
- cAdvisor depends on Docker host mounts. In `docker-compose.prod.yml` it also runs with elevated privileges and Docker socket access; keep this only for trusted environments and revisit before hardened production deployment.
- If the event machine restricts those mounts, the fallback is to keep Prometheus and Grafana running with app metrics only.
- The current stack provides logging and metrics, not distributed tracing.
- `/metrics` is intentionally public on the gateway for demo convenience. If this repo is hardened beyond hackathon use, that exposure should be revisited.

## Verification

When observability code changes, run:

```bash
make typecheck
make test
make check
make monitoring-smoke
docker compose -f docker-compose.yml config
docker compose -f docker-compose.prod.yml config
```

Observability-focused tests currently live in:

- `tests/unit/test_metrics.py`
- `tests/unit/test_observability.py`
- `tests/unit/test_monitoring_assets.py`

## Quick PromQL

Useful queries when debugging:

```promql
up
sum by(service) (rate(hackspark_http_requests_total[5m]))
sum by(service, status_code) (rate(hackspark_http_requests_total{status_code=~"4..|5.."}[5m]))
histogram_quantile(0.95, sum by(service, le) (rate(hackspark_http_request_duration_seconds_bucket[5m])))
sum by(path_template) (rate(hackspark_http_requests_total[5m]))
sum by(container_label_com_docker_compose_service) (container_memory_working_set_bytes{container_label_com_docker_compose_service!=""})
sum by(container_label_com_docker_compose_service) (rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_service!=""}[1m]))
count(ALERTS{alertstate="firing"})
```

## Future extensions

Reasonable next steps after the hackathon:

- propagate `X-Request-ID` explicitly from gateway to downstream service calls
- add business-level metrics beyond HTTP transport metrics
- add tracing with OpenTelemetry if the stack grows beyond simple demo needs
