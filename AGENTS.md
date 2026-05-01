# AGENTS.md

Agent-facing companion to `README.md`. Follow these rules exactly when working in this repo.

---

## Project overview

RentPi hackathon — FastAPI HTTP gateway + 4 services that expose HTTP status routes and gRPC business APIs.

| Folder | Docker service | Transport | Port | Responsibility |
| ------ | ------------- | --------- | ---- | -------------- |
| `api-gateway/` | `api-gateway` | HTTP (FastAPI) | 8000 | JWT validation, HTTP→gRPC translation, `/status` aggregation |
| `user-service/` | `user-service` | HTTP + gRPC | 8001 / 50051 | Auth (register/login/me), Postgres, Alembic |
| `rental-service/` | `rental-service` | HTTP + gRPC | 8002 / 50052 | Products/availability — proxies Central API |
| `analytics-service/` | `analytics-service` | HTTP + gRPC | 8003 / 50053 | Trend analysis, surge detection, recommendations |
| `agentic-service/` | `agentic-service` | HTTP + gRPC | 8004 / 50054 | AI chatbot, MongoDB session store |
| `frontend/` | `frontend` | HTTP | 3000 | Next.js UI, talks only through api-gateway |

Python packages **inside** each folder keep their original names:

- `api-gateway/gateway/`
- `user-service/auth_service/`
- `agentic-service/ai_agent_service/`
- `rental-service/rental_service/`
- `analytics-service/analytics_service/`

Proto definitions live in `proto/`. Generated stubs live in `shared/grpc_gen/` (committed, not built at runtime).

`shared/app_core/` holds cross-cutting utilities. Never put domain logic there.

---

## Setup commands

```bash
cp .env.example .env          # fill in CENTRAL_API_TOKEN and JWT_SECRET
docker compose up --build     # starts all services + postgres + mongodb
```

Local dev (no Docker):

```bash
uv sync
make up-build
```

---

## Developer commands

| Command | What it does |
| ------- | ----------- |
| `make up` | Start stack |
| `make up-build` | Start stack with rebuild |
| `make down` | Stop stack |
| `make down-v` | Stop stack and wipe volumes |
| `make proto` | Regenerate gRPC stubs from `proto/*.proto` into `shared/grpc_gen/` |
| `make migrate` | Run all Alembic migrations |
| `make migrate-user` | Run user-service migrations only |
| `make revision-user MSG=<desc>` | Autogenerate a new user-service migration |
| `make alembic-check` | Verify migration state |
| `make downgrade REV=-1` | Roll back one migration |
| `make format` | Run ruff formatter |
| `make lint` | Run ruff linter |
| `make typecheck` | Run ty on all packages |
| `make test` | Run pytest |
| `make check` | format + lint + typecheck + test |

Run one test: `uv run python -m pytest tests/path/to_test.py::test_name`

---

## Architecture

### Request flow

```text
Client → api-gateway:8000 (HTTP/JSON)
            → HTTP /<service>/status → service:800x /status
            → gRPC → user-service:50051       → Postgres
            → gRPC → rental-service:50052     → Central API (rate-limited)
            → gRPC → analytics-service:50053  → Central API (rate-limited)
            → gRPC → agentic-service:50054    → MongoDB + LLM
```

### Gateway public paths (no JWT required)

- `/status`
- `/health`
- `/user-service/status`
- `/rental-service/status`
- `/analytics-service/status`
- `/agentic-service/status`
- `/users/login`
- `/users/register`
- `/docs`, `/openapi.json`, `/redoc`, `/metrics`

All other paths require `Authorization: Bearer <jwt>`.

### Gateway HTTP endpoints

| Method | Path | gRPC call |
|--------|------|-----------|
| POST | `/users/register` | UserService.Register |
| POST | `/users/login` | UserService.Login |
| GET | `/users/me` | UserService.Me |
| GET | `/user-service/status` | HTTP proxy → `http://user-service:8001/status` |
| GET | `/rental-service/status` | HTTP proxy → `http://rental-service:8002/status` |
| GET | `/analytics-service/status` | HTTP proxy → `http://analytics-service:8003/status` |
| GET | `/agentic-service/status` | HTTP proxy → `http://agentic-service:8004/status` |
| GET | `/rentals/products` | RentalService.ListProducts |
| GET | `/rentals/products/{id}` | RentalService.GetProduct |
| GET | `/analytics/trends` | AnalyticsService.GetTrends |
| GET | `/analytics/surge` | AnalyticsService.GetSurge |
| GET | `/analytics/recommendations` | AnalyticsService.GetRecommendations |
| POST | `/chat` | AgenticService.Chat |

The gateway calls each downstream HTTP `/status` endpoint **in parallel** via `asyncio.gather` to build the aggregated `/status` response. Business traffic still uses gRPC.

---

## gRPC contracts

Proto files are in `proto/`. Stubs are pre-generated in `shared/grpc_gen/` — run `make proto` after editing any `.proto` file.

### Stub import rule

Always import stubs as:
```python
from shared.grpc_gen import user_pb2, user_pb2_grpc
```

Never import from `grpc_gen` directly — stubs have package-qualified cross-imports.

### gRPC error mapping (gateway)

`shared/app_core/grpc_errors.grpc_to_http_exception()` converts gRPC status codes to HTTP:
- `NOT_FOUND` → 404, `UNAUTHENTICATED` → 401, `ALREADY_EXISTS` → 409
- `INVALID_ARGUMENT` → 400, `DEADLINE_EXCEEDED` → 504, `UNAVAILABLE` → 502

Always use it in gateway route handlers:
```python
except grpc.RpcError as exc:
    raise grpc_to_http_exception(exc) from exc
```

---

## Central API — CRITICAL RULES

**Base URL:** `https://technocracy.brittoo.xyz`
**Hard limit:** 30 req/min per team token. Each violation costs **−20 points**.
**Our enforced ceiling:** 20 req/min per service process (10 req/min safety buffer).

### Rule: always use `CentralAPIClient`, never raw httpx

Every call to the Central API **must** go through:

```python
from shared.app_core.central_api import CentralAPIClient

client = CentralAPIClient(settings.central_api_url, settings.central_api_token)
data = await client.get("/api/data/products", params={"category": "TOOLS"})
```

`CentralAPIClient` uses a sliding-window rate limiter that blocks callers (backpressure) when the limit would be exceeded.

### Token rules

- Token lives in `.env` as `CENTRAL_API_TOKEN`. Never hardcode it.
- `.env` is gitignored. Never commit it.

---

## Shared library (`shared/app_core/`)

| Module | Purpose |
|--------|---------|
| `central_api.py` | **Rate-limited Central API client** — use for all Central API calls |
| `config.py` | `CommonSettings` base class (pydantic-settings) |
| `security.py` | Argon2 password hashing, JWT creation/decoding |
| `database.py` | Async SQLAlchemy engine/session helpers |
| `grpc_errors.py` | gRPC→HTTP status code mapping for the gateway |
| `grpc_interceptors.py` | `register_health()` — wires gRPC health check into a server |
| `http.py` | Request logging middleware (`X-Request-ID`) — gateway only |
| `logging.py` | structlog configuration |
| `metrics.py` | Prometheus metrics middleware — gateway only |

Password hashing uses `argon2-cffi`. Do **not** introduce `passlib` or `bcrypt`.

---

## Code rules

- Python 3.12. Use `ruff` for formatting and imports.
- Gateway: FastAPI route handlers are thin — just gRPC stub call + error mapping.
- Services: gRPC servicer methods are thin — business logic in `services/`.
- Do not import domain logic from one service into another — use gRPC.
- Do not store any data in Postgres other than auth (users table). All product/rental data comes from Central API.
- Preserve structured logging events: `grpc_request_started`, `grpc_request_completed` in servicers.
- Gateway error mapping: gRPC `DEADLINE_EXCEEDED` → 504, `UNAVAILABLE` → 502.

---

## LLM provider selection (agentic-service)

Set `LLM_PROVIDER` in `.env`:
- `mock` — no API key needed, useful for dev/tests
- `gemini` — requires `GEMINI_API_KEY` (free tier available, recommended)
- `openai` — requires `OPENAI_API_KEY`
- `groq` — requires `GROQ_API_KEY`

---

## Adding a new gRPC endpoint

1. Add the RPC to the relevant `.proto` file in `proto/`
2. Run `make proto` to regenerate stubs
3. Implement the method in the service's `grpc_service.py`
4. Add the corresponding HTTP route in `api-gateway/gateway/api/routes.py`

---

## Adding or changing services

When scaffolding or changing any service, update all of:

- `proto/` (add/modify proto file, run `make proto`)
- `docker-compose.yml` and `docker-compose.prod.yml`
- gateway routing in `api-gateway/gateway/api/routes.py`
- gateway config in `api-gateway/gateway/core/config.py`
- `Makefile` `typecheck` target
- `pyproject.toml` `[tool.ty.environment].extra-paths`
- `.env.example` for any new env vars
- This file (`AGENTS.md`)

---

## Migrations (user-service only)

```bash
make revision-user MSG=describe_the_change   # autogenerate
make migrate-user                            # apply
make downgrade REV=-1                        # roll back one
```

Always review autogenerated files before applying. Run upgrade → downgrade → upgrade to verify reversibility.

---

## Typecheck commands (per-package)

```bash
uv run ty check shared
uv run --directory api-gateway ty check gateway
uv run --directory user-service ty check auth_service
uv run --directory agentic-service ty check ai_agent_service
```

`rental-service` and `analytics-service` are not yet in the typecheck target — add them when their code is non-trivial.

---

## Manual smoke test

With the stack running:

```bash
curl http://localhost:8000/status          # gateway aggregated status (gRPC health checks)
curl http://localhost:8000/health          # gateway HTTP health

# Register
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}'

# Login → get token
TOKEN=$(curl -s -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Protected endpoints
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/users/me
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/rentals/products
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/analytics/trends
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/analytics/surge
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/analytics/recommendations

# Chat
curl -X POST -H "Authorization: Bearer $TOKEN" http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"How does JWT auth protect inventory endpoints?","top_k":3}'
```

Gateway Swagger docs: `http://localhost:8000/docs`
