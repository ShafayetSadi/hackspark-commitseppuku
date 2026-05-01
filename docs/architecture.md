# Architecture

RentPi is a microservices stack built for a hackathon sprint. The API gateway is the public HTTP entry point; all internal service-to-service traffic uses gRPC.

![RentPi System Architecture](./images/RentPi%20Microservices%20System%20Architecture.png)

## System Overview

| Service | Folder | HTTP Port | gRPC Port | Responsibility |
|---------|--------|-----------|-----------|----------------|
| `api-gateway` | `api-gateway/` | 8000 | — | JWT validation, HTTP→gRPC translation, `/status` aggregation |
| `user-service` | `user-service/` | 8001 | 50051 | Auth (register/login/me), Postgres, Alembic |
| `rental-service` | `rental-service/` | 8002 | 50052 | Products, availability, interval algorithms — proxies Central API |
| `analytics-service` | `analytics-service/` | 8003 | 50053 | Trends, surge detection, recommendations — proxies Central API |
| `agentic-service` | `agentic-service/` | 8004 | 50054 | AI chatbot, Redis session store, gRPC grounding via rental/analytics |
| `frontend` | `frontend/` | 3000 | — | Next.js 16 UI, talks only through api-gateway |

Infrastructure containers: `postgres` (5432), `redis` (6379).

## Request Flow

```text
Client
  |
  v
api-gateway:8000  (HTTP/JSON)
  |
  |-- JWT validation (public paths bypass)
  |
  |-- /users/*          --gRPC--> user-service:50051       --> PostgreSQL
  |-- /rentals/*        --gRPC--> rental-service:50052     --> Central API
  |-- /analytics/*      --gRPC--> analytics-service:50053  --> Central API
  |-- /chat             --gRPC--> agentic-service:50054    --> Redis
  |                                                        --> rental-service:50052 (tool calls)
  |                                                        --> analytics-service:50053 (tool calls)
  |
  |-- /<service>/status --HTTP--> service:800x/status   (parallel, asyncio.gather)
```

## Design Principles

### gRPC internally, HTTP externally

The gateway translates HTTP/JSON to gRPC for every downstream call. Services expose HTTP only for health/status checks — not for business logic.

### Explicit service boundaries

No service imports domain logic from another service. Cross-service calls always go through gRPC stubs.

### Shared only where it pays off

`shared/app_core/` contains:
- `central_api.py` — rate-limited Central API client (20 req/min)
- `config.py` — `CommonSettings` base class (pydantic-settings)
- `security.py` — Argon2 password hashing, JWT creation/decoding
- `database.py` — async SQLAlchemy engine/session helpers
- `grpc_errors.py` — gRPC→HTTP status code mapping for the gateway
- `grpc_interceptors.py` — `register_health()` for gRPC health protocol
- `service_runtime.py` — `serve_http_and_grpc()` dual-protocol server factory
- `http.py` — request logging middleware with `X-Request-ID`
- `logging.py` — structlog JSON configuration
- `metrics.py` — Prometheus metrics middleware

### Central API rate limiting

The Central API enforces 30 req/min per team token. `CentralAPIClient` uses a sliding-window rate limiter capped at 20 req/min (10 req/min safety buffer). It retries with exponential backoff and raises a `503` after 3 failed attempts.

## Repository Layout

```text
.
├── api-gateway/
│   └── gateway/
│       ├── main.py
│       ├── core/config.py
│       ├── api/routes.py
│       └── grpc_clients/
├── user-service/
│   └── auth_service/
│       ├── main.py
│       ├── grpc_service.py
│       ├── http_app.py
│       ├── services/
│       ├── models/
│       └── api/
├── rental-service/
│   └── rental_service/
│       ├── main.py
│       ├── grpc_service.py
│       ├── services/
│       └── utils/
├── analytics-service/
│   └── analytics_service/
│       ├── main.py
│       ├── grpc_service.py
│       └── services/
├── agentic-service/
│   └── ai_agent_service/
│       ├── main.py
│       ├── grpc_service.py
│       ├── services/
│       │   ├── chat_service.py
│       │   ├── session_store.py
│       │   ├── tool_executor.py
│       │   └── llm/
│       └── rag/
├── frontend/
│   ├── app/
│   │   ├── api/          # Next.js server-side proxies
│   │   └── ...           # App Router pages
│   └── lib/auth-service.ts
├── proto/                # .proto source files
│   ├── user.proto
│   ├── rental.proto
│   ├── analytics.proto
│   └── agentic.proto
├── shared/
│   ├── app_core/         # cross-cutting utilities
│   └── grpc_gen/         # generated stubs (committed, not built at runtime)
├── tests/
├── monitoring/
│   ├── prometheus/
│   └── grafana/
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── pyproject.toml
└── uv.lock
```

## Service Details

### API Gateway (`api-gateway/`)

- Public HTTP entry point on port 8000.
- JWT validation for all routes except the public list below.
- Routes HTTP requests to downstream gRPC services via stub clients in `gateway/grpc_clients/`.
- Aggregates `/status` from all services in parallel using `asyncio.gather`.

Public (no JWT required): `/status`, `/health`, `/user-service/status`, `/rental-service/status`, `/analytics-service/status`, `/agentic-service/status`, `/users/login`, `/users/register`, `/docs`, `/openapi.json`, `/redoc`, `/metrics`.

### User Service (`user-service/`)

- Runs gRPC on 50051 and HTTP on 8001 (status only).
- Owns the `users` table in PostgreSQL (Alembic migrations).
- gRPC methods: `Register`, `Login`, `Me`, `GetDiscount`.
- Discount is computed from a security score via Central API.

### Rental Service (`rental-service/`)

- Runs gRPC on 50052 and HTTP on 8002.
- Proxies all product data from the Central API through `CentralAPIClient`.
- Implements interval algorithms: availability windows, k-th busiest date, longest free streak, merged feed, user top categories.

### Analytics Service (`analytics-service/`)

- Runs gRPC on 50053 and HTTP on 8003.
- Proxies analytics data from the Central API.
- gRPC methods: `GetTrends`, `GetSurge`, `GetRecommendations`, `GetPeakWindow`, `GetSurgeDays`.

### Agentic Service (`agentic-service/`)

- Runs gRPC on 50054 and HTTP on 8004.
- Stores conversation sessions in Redis (TTL-based auto-cleanup).
- LLM provider is configurable: `mock`, `gemini`, `openai`, `groq`.
- Chat pipeline: load session → LLM decides tool → execute tool via gRPC → synthesize answer.
- Exposes HTTP routes for session management (`/chat/sessions`, `/chat/{id}/history`).

### Frontend (`frontend/`)

- Next.js 16, React 19, TypeScript, Tailwind CSS 4.
- Runs on port 3000.
- All API calls go through Next.js server-side API routes (`/app/api/*`) which proxy to the gateway.
- JWT stored in an HTTP-only cookie (`hackspark_auth_token`).

## Data and Persistence

| Store | Owner | Data |
|-------|-------|------|
| PostgreSQL | user-service | `users` table (id, email, full_name, hashed_password) |
| Redis | agentic-service | Chat session history and metadata |
| Central API | rental-service, analytics-service | All product, rental, and analytics data |

No service stores product or rental data locally.

## gRPC Contracts

Proto files live in `proto/`. Generated stubs are in `shared/grpc_gen/` — committed to the repo; run `make proto` after editing any `.proto`.

Always import stubs as:
```python
from shared.grpc_gen import user_pb2, user_pb2_grpc
```

gRPC error mapping (gateway): `shared/app_core/grpc_errors.grpc_to_http_exception()` converts gRPC status codes to HTTP 400/401/404/409/502/504.

## Infrastructure

### Containerization

- One Dockerfile per service (multi-stage, Python 3.12 or Node 22).
- `docker-compose.yml` — dev stack (all services + postgres + redis + monitoring).
- `docker-compose.prod.yml` — production-like variant (gateway public, internal services private).
- Health checks on every container.

### Quality tooling

- `ruff` — formatting and linting
- `ty` — type checking per service
- `pytest` — unit and integration tests
- `make check` — runs format + lint + typecheck + test

## Known Intentional Tradeoffs

- The gateway validates JWT locally rather than delegating to user-service to reduce hop latency.
- All backend services share one PostgreSQL instance (only user-service actually writes to it).
- The Central API rate limit is enforced per-process, not cluster-wide; avoid horizontal scaling without a shared Redis limiter.
- Redis is required for agentic-service session storage; the service will fail to start if Redis is unreachable.
- Dev mode exposes all internal service ports; prod mode restricts them.
- The `LLM_PROVIDER=mock` setting lets the stack run without any external LLM API key.
