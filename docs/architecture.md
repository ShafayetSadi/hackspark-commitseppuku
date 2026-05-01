# Architecture

This repository is a minimal microservices baseline optimized for a fast team sprint. The intent is to keep infrastructure concerns solved early so most work happens inside service business logic.

## System Overview

The stack consists of:

- `api-gateway`: the public entrypoint and unified API docs surface.
- `auth-service`: user registration, login, and token-backed identity lookup.
- `ai-agent-service`: deterministic RAG-lite chat endpoint.
- `item-service`: CRUD-style service template for domain entities.
- `postgres`: shared database container for persisted services.

## High-Level Request Flow

```text
Client
  |
  v
API Gateway
  |-- /auth/* --> auth-service
  |-- /items* --> item-service
  '-- /ai/* --> ai-agent-service

auth-service <----> PostgreSQL
item-service <----> PostgreSQL
ai-agent-service -> in-memory knowledge base
```

## Design Principles

### 1. Explicit service boundaries

- Each service owns its routes, schemas, and business logic.
- The gateway forwards requests but does not absorb downstream domain logic.

### 2. Shared only where it pays off

`shared/app_core` contains:

- configuration primitives
- database engine and session helpers
- structured logging setup
- shared HTTP request logging middleware
- shared Prometheus metrics middleware and exporter
- password hashing and JWT helpers

This keeps repetitive plumbing consistent without coupling service internals.

### 3. Hackathon-first pragmatism

- Alembic is the only schema source of truth for persisted services.
- Service startup validates the migrated schema and fails loudly on drift or missing tables.
- The AI service uses deterministic RAG-lite components and a replaceable mock LLM instead of a fragile external dependency by default.

## Repository Layout

```text
.
├── docs/
├── gateway/
│   └── app/
├── services/
│   ├── ai-agent-service/
│   ├── auth-service/
│   └── item-service/
├── shared/
│   └── app_core/
├── scripts/
├── docker-compose.yml
├── docker-compose.prod.yml
├── pyproject.toml
└── uv.lock
```

## Service Details

### API Gateway

Responsibilities:

- public entrypoint
- JWT validation for protected routes
- request forwarding to downstream services
- service registry via environment variables

Important files:

- `gateway/gateway/main.py`
- `gateway/gateway/api/routes.py`
- `gateway/gateway/services/proxy.py`

Notes:

- `/auth/register`, `/users/login`, and `/health` are treated as public.
- Protected routes require a bearer token validated with the shared JWT secret.
- Forwarding now includes explicit timeout and upstream-network failure handling in `gateway/gateway/services/proxy.py`.
- Request logging is centralized through `shared/app_core/http.py`.
- Gateway docs remain enabled in both dev and prod.

### Auth Service

Responsibilities:

- user registration
- credential verification
- JWT issuance
- current-user lookup

Important files:

- `services/auth_service/auth_service/main.py`
- `services/auth_service/auth_service/api/routes.py`
- `services/auth_service/auth_service/api/dependencies.py`
- `services/auth_service/auth_service/services/auth_service.py`
- `services/auth_service/auth_service/models/user.py`

Notes:

- Passwords are hashed with `argon2-cffi`.
- User lookup is persisted in PostgreSQL by default.
- The `/me` endpoint depends on token context populated by middleware.
- Use-case code raises service-specific errors and leaves HTTP translation to the route layer.
- Swagger/OpenAPI routes are enabled only in `APP_ENV=dev`.

### AI Agent Service

Responsibilities:

- validate chat input
- run relevance filtering
- retrieve lightweight context from an internal knowledge set
- return deterministic JSON output through a replaceable LLM interface

Important files:

- `services/ai_agent_service/ai_agent_service/api/routes.py`
- `services/ai_agent_service/ai_agent_service/services/chat_service.py`
- `services/ai_agent_service/ai_agent_service/services/rag/relevance.py`
- `services/ai_agent_service/ai_agent_service/services/rag/retriever.py`
- `services/ai_agent_service/ai_agent_service/services/rag/context_builder.py`
- `services/ai_agent_service/ai_agent_service/services/llm/base.py`
- `services/ai_agent_service/ai_agent_service/services/llm/mock_llm.py`
- `services/ai_agent_service/ai_agent_service/services/knowledge_base.py`

Notes:

- No external LLM dependency is required to boot the system.
- The mock LLM is deterministic and avoids prompt echoing.
- Swagger/OpenAPI routes are enabled only in `APP_ENV=dev`.

### Item Service

Responsibilities:

- example service template for CRUD-like domain logic
- pagination and filtering
- database-backed resource access

Important files:

- `services/item-service/app/api/routes.py`
- `services/item-service/app/services/item_service.py`
- `services/item-service/app/models/item.py`

Notes:

- The service demonstrates query filtering and paginated reads.
- Composite and single-column indexes are included as examples.
- Swagger/OpenAPI routes are enabled only in `APP_ENV=dev`.

## Data and Persistence

Persisted services:

- `auth-service`
- `item-service`

Database characteristics:

- async SQLAlchemy sessions
- PostgreSQL by default
- SQLite fallback support for simplified local runs
- indexed columns where lookups are expected

Current schema ownership:

- `users` table belongs to `auth-service`
- `items` table belongs to `item-service`

## Infrastructure

### Dependency management

- Root `pyproject.toml`
- Root `uv.lock`
- Local `.venv` via `uv sync`
- Docker syncs production dependencies from the same lockfile

### Containerization

- one Dockerfile per service
- `docker-compose.yml` for debug-friendly local work
- `docker-compose.prod.yml` for production-like app exposure (gateway public; internal app services private) plus bundled monitoring endpoints
- health checks for every container
- service-to-service traffic over the Compose network

### Quality tooling

- `ruff` for formatting and linting
- `ty` for type checking
- `pytest` for auth, item, AI, and gateway integration coverage
- `Makefile` for the common developer workflow

## Known Intentional Tradeoffs

- The gateway performs token validation locally instead of delegating each check to the auth service. This reduces request hops and keeps the public edge simple, but requires secret consistency across services.
- The two persisted services share one PostgreSQL instance. That is acceptable for a hackathon baseline, but stricter isolation may be preferable later.
- The AI service is not a full RAG system. It is designed for predictable hackathon demos and simple future replacement.
- Dev mode deliberately exposes internal service ports and docs for debugging; prod mode removes internal app-service host entrypoints, but still publishes gateway, Prometheus, and Grafana for observability.
- `docker-compose.prod.yml` includes privileged cAdvisor host mounts as an observability tradeoff and is not a hardened production blueprint by itself.
