# Development Guide

This guide explains how to work on the repository locally with `uv`, `ruff`, `ty`, and Docker.

## Prerequisites

- Python `3.12`
- `uv`
- Docker and Docker Compose v2 (`docker compose`)

## First-Time Setup

1. Copy the environment file.

```bash
cp .env.example .env
```

2. Sync the project environment.

```bash
uv sync
```

3. Start the stack.

```bash
docker compose -f docker-compose.yml up --build
```

4. Open the gateway Swagger UI.

```text
http://localhost:8000/docs
```

## Daily Commands

Install or refresh dependencies:

```bash
uv sync
```

Format the codebase:

```bash
make format
```

Run lint checks:

```bash
make lint
```

Run type checks:

```bash
make typecheck
```

Run gateway smoke tests:

```bash
make test
```

Run the full local quality gate:

```bash
make check
```

Start the containers:

```bash
make up
```

Stop the containers and remove volumes:

```bash
make down-v
```

## Repository Conventions

### Python environment

- The repository uses a single root `pyproject.toml` and `uv.lock`.
- Local development uses `.venv/` created by `uv sync`.
- Docker images reuse the same locked dependency set, but install only production dependencies.

### Formatting and linting

- `ruff` handles formatting and linting.
- Import ordering is enforced by `ruff`, so let the formatter fix import blocks rather than editing them manually for style.

### Type checking

- `ty` is configured per service because every microservice uses an `app` package as its import root.
- Do not collapse all services into one global type-check command unless the package layout changes.

### Shared code

- Only cross-cutting primitives belong in `shared/app_core`.
- Business logic should stay inside each service unless it is truly generic.

### Service boundaries

- Route modules should stay thin and handle HTTP concerns only.
- Service modules should own use-case logic and should avoid raising framework-specific exceptions unless there is a strong reason.
- Shared HTTP behavior such as request logging should live in reusable infrastructure helpers, not be reimplemented per service.

## How To Add a New Feature

1. Start at the gateway contract:
   Decide whether the feature should be exposed publicly or stay internal.
2. Update the appropriate downstream service:
   Add schemas, service logic, and routes inside that service.
3. Update persistence if needed:
   Add or modify the SQLAlchemy model and migration.
4. Expose the route through the gateway if the service is externally reachable.
5. Update docs:
   At minimum, update `docs/api-documentation.md` and any architecture notes affected by the change.
6. Run `make check`.

## How To Add a New Microservice

1. Copy the layout of `services/item-service/`.
2. Add the new service to `docker-compose.yml`.
3. Add a Dockerfile that syncs from the root `uv.lock`.
4. Add a local `ty.toml` file if the service uses `app` as its import package.
5. Add gateway routes and a service URL environment variable if the service should be reachable through the gateway.
6. Document the new service in `docs/architecture.md` and `docs/api-documentation.md`.

## Database Development Notes

- PostgreSQL is the default runtime database.
- SQLite fallback exists for simplicity, but team development should prefer PostgreSQL to stay aligned with Docker and async behavior.
- Auth and item services include Alembic scaffolding and startup schema validation.
- If the schema starts changing frequently, rely on Alembic revisions instead of implicit startup table creation.

## Local Troubleshooting

If `uv` fails with a cache permission error in constrained environments, use a writable cache directory:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync
```

If type checking fails with unresolved `app.*` imports, verify you are running the per-service command from `make typecheck` and that the local `ty.toml` file for that service still exists.
