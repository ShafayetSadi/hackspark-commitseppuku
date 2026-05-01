# Observability

Logging, metrics, and dashboarding setup for the RentPi stack.

## Overview

Two complementary observability layers:
- Structured JSON logs from every FastAPI service (via `structlog`)
- Prometheus-compatible metrics exported by the gateway and each service

The prod Docker stack (`docker-compose.prod.yml`) also includes:
- `prometheus` for scraping and querying metrics
- `grafana` for dashboarding
- `cadvisor` for container CPU and memory metrics

The dev stack (`docker-compose.yml`) does not include monitoring containers — run the prod compose to get Grafana and Prometheus.

Goals:
- Trace a request across services with `X-Request-ID`
- Inspect latency and error behavior quickly
- Show a live dashboard during judging

## Logging

### Implementation

Structured logging is configured in `shared/app_core/logging.py` using `structlog` with JSON output to stdout.

The setup normalizes stdlib and Uvicorn logs through the same JSON formatter and disables Uvicorn access logs so request logging is not duplicated.

Request logging is installed by `shared/app_core/http.py` in every service's `main.py` via `serve_http_and_grpc()`.

Each request emits three events:
- `request_started`
- `request_completed`
- `request_failed` (for unhandled exceptions, includes stack trace)

gRPC servicers also emit:
- `grpc_request_started`
- `grpc_request_completed`

### Log Fields

Common fields in every request log:

| Field | Description |
|-------|-------------|
| `request_id` | UUID, from `X-Request-ID` header or auto-generated |
| `method` | HTTP method |
| `path` | Request path |
| `query_keys` | Names of query params (not values, to avoid leaking tokens) |
| `client_host` | Client IP |
| `status_code` | On `request_completed` |
| `duration_ms` | On `request_completed` and `request_failed` |
| `timestamp` | ISO 8601 |
| `level` | Log level |
| `logger` | Logger name |

### Request Correlation

The middleware accepts an incoming `X-Request-ID` header. If absent, it generates a UUID.

The resolved ID is:
- stored on `request.state.request_id`
- included in every log event for that request
- returned in the `X-Request-ID` response header on success

To trace a single request:
1. Capture `X-Request-ID` from the gateway response header.
2. Search for that ID in gateway logs.
3. Search for the same ID in the downstream service logs.

### Example Log Flow

Successful request:
```json
{"request_id":"abc123","method":"POST","path":"/users/login","event":"request_started","timestamp":"...","level":"info"}
{"request_id":"abc123","method":"POST","path":"/users/login","status_code":200,"duration_ms":12.41,"event":"request_completed","timestamp":"...","level":"info"}
```

Unhandled failure:
```json
{"request_id":"abc123","method":"GET","path":"/rentals/products","duration_ms":4.87,"event":"request_failed","timestamp":"...","level":"error"}
```

### Reading Logs

Stream all services:
```bash
docker compose logs -f
```

Stream one service:
```bash
docker compose logs -f api-gateway
docker compose logs -f user-service
docker compose logs -f rental-service
docker compose logs -f analytics-service
docker compose logs -f agentic-service
```

## Metrics

### Implementation

Prometheus metrics are installed by `shared/app_core/metrics.py` in each service.

Each app exposes `GET /metrics`. The gateway exposes it publicly (no JWT required). Internal services expose it for Prometheus scraping over the Compose network.

Control via environment variables:
- `METRICS_ENABLED=true|false` — enable or disable the endpoint
- `METRICS_TOKEN=<token>` — require a bearer token on `/metrics`

If `METRICS_TOKEN` is set, update `monitoring/prometheus/prometheus.yml` to send the same token in scrape configs:
```yaml
- job_name: api-gateway
  metrics_path: /metrics
  authorization:
    type: Bearer
    credentials: ${METRICS_TOKEN}
  static_configs:
    - targets: ["api-gateway:8000"]
```

### Exported Application Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `hackspark_http_requests_total` | Counter | Total HTTP requests |
| `hackspark_http_request_duration_seconds` | Histogram | HTTP request latency |
| `hackspark_http_requests_in_flight` | Gauge | Active HTTP requests |

Labels: `service`, `method`, `path_template`, `status_code` (totals only).

Notes:
- Route templates (e.g. `/rentals/products/{id}`) are used to prevent label explosion.
- `/metrics` is excluded from request counting so Prometheus scrapes do not distort charts.
- `/health` and `/status` remain instrumented.

### Scrape Targets

Prometheus is configured in `monitoring/prometheus/prometheus.yml` to scrape:

| Target | Address |
|--------|---------|
| `prometheus` | `prometheus:9090/metrics` |
| `api-gateway` | `api-gateway:8000/metrics` |
| `user-service` | `user-service:8001/metrics` |
| `rental-service` | `rental-service:8002/metrics` |
| `analytics-service` | `analytics-service:8003/metrics` |
| `agentic-service` | `agentic-service:8004/metrics` |
| `cadvisor` | `cadvisor:8080/metrics` |

Prometheus loads baseline rules from `monitoring/prometheus/rules/hackspark-alerts.yml`:
- Recording rules for request rate and 5xx rate per service
- `HacksparkTargetDown`
- `HacksparkHigh5xxRate`

### Dashboarding

Grafana is pre-provisioned from `monitoring/grafana/` with the `Hackspark Overview` dashboard.

The dashboard includes:
- Request rate by service
- p95 latency by service
- Route-level p95 latency
- 4xx and 5xx error rate
- Route-level error rate
- In-flight requests by service
- Prometheus `up` status for all services and cAdvisor
- Active alert count
- Container CPU and memory usage

## Running the Stack

Dev (app only, no monitoring):
```bash
make up-build
```

Prod (app + monitoring):
```bash
docker compose -f docker-compose.prod.yml up --build
```

Useful URLs:
- Gateway docs: `http://localhost:8000/docs`
- Gateway metrics: `http://localhost:8000/metrics`
- Prometheus: only accessible inside the Compose network in prod (no host port exposed)
- Grafana: `http://localhost:9091` (prod only; default credentials: `admin` / `admin`)

## Demo Workflow

1. Open Grafana and the `Hackspark Overview` dashboard.
2. Open `http://localhost:8000/docs`.
3. Execute a sequence of requests:
   - `POST /users/register`
   - `POST /users/login`
   - `GET /users/me`
   - `GET /rentals/products`
   - `GET /analytics/trends`
   - `POST /chat`
4. Show dashboard panels changing in real time.
5. Trigger an intentional error (call a protected route without a bearer token) and show the error-rate panel move.
6. Show the Prometheus alerts page with baseline rules loaded.
7. Copy an `X-Request-ID` from the gateway response and find it in the container logs.

## Operational Notes

- The gateway is the main demo surface — start there before inspecting internal services.
- cAdvisor requires Docker host mounts. In `docker-compose.prod.yml` it runs with elevated privileges; keep this only for trusted environments.
- If the event machine restricts those mounts, Prometheus and Grafana will still work with app metrics only.
- The current stack provides logging and metrics but not distributed tracing.
- `/metrics` is public on the gateway for demo convenience — revisit before hardened production use.

## Verification

After observability changes:
```bash
make typecheck
make test
make check
docker compose -f docker-compose.yml config
docker compose -f docker-compose.prod.yml config
```

Observability tests:
- `tests/unit/test_metrics.py`
- `tests/unit/test_observability.py`
- `tests/unit/test_monitoring_assets.py`

## Quick PromQL

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

## Future Extensions

- Propagate `X-Request-ID` explicitly from gateway gRPC calls to downstream servicers
- Add business-level metrics (Central API call rate, LLM response latency, chat sessions active)
- OpenTelemetry tracing if the stack grows beyond demo needs
