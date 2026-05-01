# Hackathon FastAPI Microservices Boilerplate

This repository is a minimal but production-minded baseline for a 10-hour hackathon. It gives a team a clean gateway, auth service, AI agent service, and CRUD template so time goes into business logic instead of infrastructure wiring.

Detailed project documentation lives under [docs/README.md](./docs/README.md).

## Architecture

```text
repo/
├── pyproject.toml
├── uv.lock
├── gateway/
│   ├── app/
│   ├── Dockerfile
│   └── ...
├── frontend/
│   ├── app/
│   ├── Dockerfile
│   └── ...
├── services/
│   ├── ai-agent-service/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── ...
│   ├── auth-service/
│   │   ├── alembic/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── ...
│   └── item-service/
│       ├── alembic/
│       ├── app/
│       ├── Dockerfile
│       └── ...
├── shared/
│   └── app_core/
├── scripts/
├── .env.example
├── docker-compose.yml
└── Makefile
```

## Design Notes

- `frontend` is a Next.js App Router UI container that talks to the backend via server-side `/api/auth/*` handlers.
- `api-gateway` validates JWTs before forwarding protected traffic to internal services.
- Services communicate over HTTP only. There is no direct Python import coupling between service business modules.
- `shared/app_core` contains only generic cross-cutting utilities: config, logging, database factory, and JWT/password helpers.
- Auth and item services use async SQLAlchemy with Alembic as the single schema source of truth.
- The AI agent service is intentionally RAG-lite: deterministic relevance filtering, context selection, and a mockable answer function.
- PostgreSQL is the default runtime target. Switching to SQLite is possible by setting `DATABASE_BACKEND=sqlite` and `SQLITE_PATH`.
- Dependencies are managed once at the repo root through `uv`, while Docker images sync a production-only `.venv` from the shared lockfile.
- `ruff` handles formatting and linting; `ty` is wired as the fast type-checker and runs per service to avoid collisions between repeated `app` packages.

## Quick Start

1. Copy the env file:

    ```bash
    cp .env.example .env
    ```

2. Create the local environment:

    ```bash
    uv sync
    ```

3. Start the development stack:

    ```bash
    docker compose -f docker-compose.yml up --build
    ```

4. Open the frontend app:

    ```text
    http://localhost:3001
    ```

5. Open the gateway docs:

    ```text
    http://localhost:8000/docs
    ```

6. Open the monitoring stack:

    ```text
    Gateway metrics: http://localhost:8000/metrics
    Prometheus:      http://localhost:9090
    Grafana:         http://localhost:3000
    ```

## Developer Commands

```bash
make format
make lint
make typecheck
make test
make check
make up
```

The `typecheck` target runs `ty` separately in `gateway/` and each service directory because the repo intentionally reuses the package name `app` in multiple microservices.

## Environments

- Development: `docker compose -f docker-compose.yml up --build`
  - Frontend is published on `http://localhost:${FRONTEND_PORT:-3001}`
  - Gateway and each service expose `/docs`
  - Internal services are reachable on localhost ports
- Production: `docker compose -f docker-compose.prod.yml up --build`
  - Frontend is published on `http://localhost:${FRONTEND_PORT:-3001}`
  - `api-gateway` is also published for direct API access/docs
  - Internal app services stay private on the Compose network
  - Prometheus (`:9090`) and Grafana (`:3000`) are also published for observability
  - Unified API docs stay available only at the gateway
  - `cadvisor` runs with elevated host access for container metrics; treat this compose profile as demo/ops-oriented, not a hardened production baseline

## Example Flow

Register:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"team@example.com","password":"password123","full_name":"Hack Team"}'
```

Create an item:

```bash
TOKEN="<paste access token>"

curl -X POST http://localhost:8000/items \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Camera","category":"rental","quantity":3}'
```

Query the AI agent:

```bash
curl -X POST http://localhost:8000/ai/chat \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"query":"How does JWT auth protect item inventory endpoints?","top_k":2}'
```

## Service Contracts

### Auth Service

- `POST /register`
- `POST /login`
- `GET /me`

### Item Service

- `GET /items?page=1&page_size=20&category=rental&search=camera`
- `POST /items`

### AI Agent Service

- `POST /chat`
- Response shape:

```json
{
  "answer": "string",
  "sources": ["string"],
  "confidence": 0.73
}
```

## Performance and Maintainability Choices

- Async FastAPI handlers across all services.
- Count and page queries are separated to keep list endpoints predictable.
- DB indexes are included on high-signal lookup fields.
- Structured JSON logging is enabled via `structlog`.
- Prometheus metrics are exposed on `/metrics` for the gateway and each internal service.
- Prometheus self-scrapes, loads baseline alert rules, and exposes alert state at `/alerts`.
- Grafana is pre-provisioned with a hackathon dashboard covering request rate, p95 latency, route hot spots, in-flight requests, service health, active alerts, and container CPU/memory.
- Gateway forwarding uses a small `httpx` proxy layer so routes stay explicit and easy to extend.
- Alembic is present for real schema evolution, but startup bootstrap keeps the first demo fast.
- `uv.lock` gives a single reproducible dependency set across local dev and Docker builds.

## Monitoring Demo

Bring the full stack up with:

```bash
docker compose -f docker-compose.yml up --build
```

Then:

- Generate traffic through `http://localhost:8000/docs`
- Inspect raw metrics at `http://localhost:8000/metrics`
- Check scrape targets in Prometheus at `http://localhost:9090/targets`
- Check loaded alert rules in Prometheus at `http://localhost:9090/alerts`
- Open Grafana at `http://localhost:3000` with `${GRAFANA_ADMIN_USER:-admin}` / `${GRAFANA_ADMIN_PASSWORD:-admin}`
- Run `make monitoring-smoke` after the stack is up to verify the observability path end to end

The provisioned `Hackspark Overview` dashboard shows:

- request throughput by service
- p95 request latency
- route-level p95 latency
- 4xx/5xx error rate
- route-level error rate
- in-flight requests
- service `up` status
- Prometheus health and active alerts
- container CPU and memory from cAdvisor

## What Teams Usually Change First

- Add domain tables and service logic inside `services/item-service/app`.
- Replace the mock AI answerer with a real provider in `services/ai_agent_service/ai_agent_service/services/chat_service.py`.
- Extend gateway route maps or add a second domain service following the same structure.
