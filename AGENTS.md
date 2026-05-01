# AGENTS.md

This file is the agent-facing companion to `README.md`. It captures the repo-specific commands, architecture, constraints, and verification rules that coding agents should follow when working in `hackspark`.

## Project overview

`hackspark` is a FastAPI microservices starter built around one public API gateway and three internal services:

- `gateway/` routes public traffic, validates JWTs, and proxies to downstream services.
- `services/auth_service/` owns registration, login, and current-user lookup.
- `services/item-service/` owns item CRUD-style inventory endpoints.
- `services/ai_agent_service/` owns the chat endpoint and currently uses a stubbed RAG + mock LLM flow.
- `shared/app_core/` holds cross-service utilities only: config, database helpers, security, logging, and request middleware.

External traffic should enter through the gateway first. Keep service boundaries HTTP-based; do not add direct business-logic imports between services.

## Setup commands

- Install dependencies: `uv sync`
- Refresh the lockfile after dependency changes: `uv lock`
- Copy environment defaults: `cp .env.example .env`
- Start the dev stack: `make up`
- Start the dev stack with rebuild: `make up-build`
- Stop the dev stack: `make down`
- Stop the dev stack and remove volumes: `make down-v`

The default compose file is `docker-compose.yml`. On this checkout, Postgres is published on host port `5434`, not `5432`.

## Developer commands

- Format code: `make format`
- Lint code: `make lint`
- Run type checks: `make typecheck`
- Run tests: `make test`
- Run the full local gate: `make check`
- Run the monitoring smoke check against a live Compose stack: `make monitoring-smoke`
- Run one test: `uv run pytest tests/path/to_test.py::test_name`
- Apply auth migrations: `make migrate-auth`
- Apply item migrations: `make migrate-items`
- Apply all migrations: `make migrate`
- Create an auth migration with Alembic autogenerate: `make revision-auth MSG=add_user_indexes`
- Create an item migration with Alembic autogenerate: `make revision-items MSG=add_item_status`
- Check auth Alembic state: `make alembic-check-auth`
- Check item Alembic state: `make alembic-check-items`
- Check all Alembic state: `make alembic-check`
- Roll back auth migrations one revision: `make downgrade-auth`
- Roll back item migrations one revision: `make downgrade-items`
- Roll back all migrations one revision: `make downgrade`
- Scaffold a service: `make add-service name=<name>`

## Dev environment tips

- Use `make check` as the default final verification for non-trivial changes.
- `ty` must be run per package because this repo intentionally reuses import roots across services.
- The Makefile already encodes the safe `ty` commands; prefer `make typecheck` over ad hoc root-level `ty` runs.
- For Alembic migrations, always create revision files through `make revision-auth MSG=...` or `make revision-items MSG=...`. Do not hand-write migration files from scratch.
- If `revision --autogenerate` fails because the target database is not up to date, run the matching migration and/or `make alembic-check-auth` / `make alembic-check-items` first.
- Alembic revision targets require `MSG=...` and use `--autogenerate`; review the generated migration file, then verify it with real upgrade and downgrade runs before considering the migration done.
- Migration rollback targets default to `REV=-1`. Override the revision explicitly when needed, for example: `make downgrade-auth REV=base`.
- If you need to run `ty` manually, use the service-local commands:
  - `uv run ty check shared`
  - `uv run --directory gateway ty check gateway`
  - `uv run --directory services/auth_service ty check auth_service`
  - `uv run --directory services/ai_agent_service ty check ai_agent_service`
  - `uv run --directory services/item-service ty check app`
- The filesystem path `services/item-service/` maps to Python package `app`. The auth and AI services use `auth_service` and `ai_agent_service` package names.

## Architecture

### Request flow

Public request flow is:

`Client -> gateway (:8000) -> auth_service (:8001) / item_service (:8002) / ai_agent_service (:8003)`

The gateway JWT middleware allows these public prefixes:

- `/health`
- `/auth/login`
- `/auth/register`
- `/docs`
- `/openapi.json`
- `/redoc`

Protected requests must carry a bearer token. The gateway decodes the JWT and stores the subject on `request.state.user_id` before proxying.

### Service layout

Most services follow this shape:

```text
<package>/
  api/routes.py
  core/config.py
  schemas/
  services/
  models/        # db-backed services
  db/session.py  # db-backed services
```

Keep route handlers thin. Put business logic in `services/`. Keep shared utilities generic inside `shared/app_core/`.

### Shared library

Important shared modules:

- `shared/app_core/security.py`: password hashing and verification, JWT creation and decoding
- `shared/app_core/http.py`: request logging middleware with `X-Request-ID`
- `shared/app_core/logging.py`: structlog configuration
- `monitoring/prometheus/rules/hackspark-alerts.yml`: baseline recording and alert rules
- `shared/app_core/database.py`: async SQLAlchemy engine/session helpers
- `shared/app_core/config.py`: common settings base class

Password hashing already uses `argon2` via `argon2-cffi`. Do not reintroduce `passlib`/`bcrypt`.

### Gateway behavior

- Proxy logic lives in `gateway/gateway/services/proxy.py`.
- Preserve normalized gateway error behavior:
  - upstream timeout -> `504`
  - upstream unavailable -> `502`
  - upstream `5xx` -> `502`
- Preserve `X-Request-ID` propagation and structured request logging.
- Keep framework logs JSON-formatted and avoid reintroducing ad hoc `print(...)` debug output in service startup or metrics code.

### AI service status

The AI service is intentionally a scaffold:

- retrieval is in-memory
- relevance scoring is keyword-based
- prompt context is assembled locally
- `llm/mock_llm.py` returns a canned answer

If you replace the LLM path, do it behind the existing service boundary rather than spreading provider-specific logic across the repo.

## Code style and implementation rules

- Target Python `3.12`.
- Use `ruff` for formatting and import ordering.
- Keep changes small and local to the owning service whenever possible.
- Do not bypass the gateway by coupling services directly in Python.
- Reuse `shared/app_core/` only for truly cross-cutting concerns, not domain logic.
- Prefer explicit, stable JSON error responses over leaking downstream exceptions.
- Preserve structured logging events: `request_started`, `request_completed`, and `request_failed`.

## Testing instructions

- Tests live under `tests/`, split into `tests/unit/` and `tests/integration/`.
- Integration tests are marked with `@pytest.mark.integration`.
- To skip slow integration coverage, run: `uv run pytest -m 'not integration'`
- The test harness in `tests/conftest.py` isolates environments, rewrites `sys.path`, and clears module state so repeated package names do not collide across services.
- When changing gateway proxying, auth flow, service contracts, or request logging, add or update tests in `tests/integration/` or the relevant `tests/unit/` module.
- When changing monitoring assets, also update the config-coverage tests for Prometheus rules/dashboard expectations and rerun `make monitoring-smoke` if the Compose stack is up.

For most code changes:

1. Run targeted tests for the touched area.
2. Run `make typecheck`.
3. Run `make test`.
4. Run `make check` before finishing if the change is more than trivial.

For migration changes:

1. Generate the revision with `make revision-auth MSG=...` or `make revision-items MSG=...`.
2. Review the autogenerated file instead of replacing it with a hand-written migration.
3. Run the matching upgrade target.
4. Run the matching downgrade target.
5. Re-run the matching upgrade target so the repo is left in the intended final state.

## Manual verification

Prefer gateway-first smoke testing through `http://localhost:8000` rather than calling internal services first.

Useful endpoints:

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /items`
- `GET /items`
- `POST /ai/chat`

If the compose stack is running, gateway docs should be at `http://localhost:8000/docs`.

## Security and config notes

- `JWT_SECRET` is required and must match across gateway and downstream services.
- `DATABASE_BACKEND=postgresql` is the default runtime path.
- For local non-Docker tests, SQLite is supported via `DATABASE_BACKEND=sqlite` and `SQLITE_PATH`.
- In `docker-compose.prod.yml`, the frontend (`:3001`) and gateway (`:8000`) are publicly exposed for application traffic; Prometheus (`:9090`) and Grafana (`:3000`) are also published for observability.
- `docker-compose.prod.yml` currently includes privileged cAdvisor host mounts (including Docker socket access); treat it as an observability-oriented deployment, not a hardened production baseline.
- Do not commit secrets or hardcode provider credentials.

## When adding or changing services

If you scaffold or add a service, update all of the following together:

- `docker-compose*.yml`
- gateway routing/config
- `Makefile` `typecheck` target
- docs and any new env vars
- tests for the new route surface

## Change expectations

When you modify code in this repository, agents should:

- keep instructions aligned with the current implementation, not boilerplate assumptions
- verify behavior with commands, not by inspection alone
- update docs when behavior, commands, ports, or contracts change
- avoid speculative architecture rewrites unless explicitly requested
