# Operations

This guide covers runtime behavior, environment variables, Docker operations, migrations, and common troubleshooting steps.

## Runtime Model

The application is designed to run through Docker Compose:

- `postgres`
- `auth-service`
- `ai-agent-service`
- `item-service`
- `api-gateway`

The public entrypoint is `api-gateway` on port `8000`. In production it is the only published HTTP service.

## Start and Stop

Build and start development:

```bash
docker compose -f docker-compose.yml up --build
```

Build and start production:

```bash
docker compose -f docker-compose.prod.yml up --build
```

Stop and remove volumes:

```bash
docker compose -f docker-compose.yml down -v
```

Check status:

```bash
docker compose ps
```

Stream logs:

```bash
docker compose logs -f
```

## Observability

All services now emit structured JSON request logs. Each request gets:

- `request_started`
- `request_completed`
- `request_failed` for unhandled exceptions

The logging middleware also adds `X-Request-ID` to successful responses so request traces can be correlated across logs and clients.

Current request logs record query parameter names via `query_keys`, but not raw query values, to reduce accidental leakage of sensitive data.

For the full logging and monitoring setup, including Prometheus, Grafana, cAdvisor, and demo workflow, see [observability.md](./observability.md).

## Environment Variables

Primary variables from `.env`:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `AUTH_SERVICE_URL`
- `ITEM_SERVICE_URL`
- `AI_AGENT_SERVICE_URL`

Service-specific runtime variables also include:

- `DATABASE_BACKEND`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `SQLITE_PATH`

## Health Checks

Docker Compose health checks are configured for:

- `postgres` via `pg_isready`
- `auth-service` via `GET /health`
- `item-service` via `GET /health`
- `ai-agent-service` via `GET /health`
- `api-gateway` via `GET /health`

The gateway waits for dependent services to report healthy before starting fully.

## Database Operations

### Current strategy

The current scaffold uses Alembic revision files as the only schema source of truth. Service startup validates the migrated schema and fails loudly when required tables or columns are missing.

### Manual migration commands

Auth service:

```bash
make migrate-auth
```

Auth service autogenerate:

```bash
make revision-auth MSG=add_user_profile_fields
```

Auth service migration check:

```bash
make alembic-check-auth
```

Auth service rollback:

```bash
make downgrade-auth
```

Item service:

```bash
make migrate-items
```

Item service autogenerate:

```bash
make revision-items MSG=add_item_status
```

Item service migration check:

```bash
make alembic-check-items
```

Item service rollback:

```bash
make downgrade-items
```

Override the revision target when needed:

```bash
make downgrade-auth REV=base
make downgrade-items REV=0001_create_items
```

Always review autogenerate output before running `make migrate-auth` or `make migrate-items`.
If `alembic revision --autogenerate` fails with "Target database is not up to date", run the matching migrate target and `make alembic-check-auth` or `make alembic-check-items` before retrying.

## Docker Build Model

Each service Dockerfile:

- syncs dependencies from the root `uv.lock`
- installs only production dependencies
- sets `PYTHONPATH=/app`
- starts the service with `uvicorn` or a shell bootstrap script

This keeps local development and container builds aligned on one locked dependency graph.

## Operational Checks Before Demo

Run these checks before presenting:

1. `uv sync`
2. `make check`
3. `docker compose -f docker-compose.yml up --build`
4. `make monitoring-smoke`
5. Verify `http://localhost:8000/docs`
6. Register a user
7. Create an item
8. Call the AI chat endpoint

## Common Issues

### `uv` cache permission errors

In restricted environments, use:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync
```

You can apply the same pattern to `uv run` commands.

### Gateway returns `401`

Check:

- the request includes `Authorization: Bearer <token>`
- the token was issued by the current running stack
- all services share the same `JWT_SECRET`

### Gateway returns `502`

This usually means an upstream service is down or returning a server error. Inspect:

```bash
docker compose logs -f auth-service
docker compose logs -f item-service
docker compose logs -f ai-agent-service
```

### Gateway returns `504`

This means the upstream service did not respond before the proxy timeout. Check:

- whether the downstream service is healthy
- whether the route is blocked on a slow database or external API call
- whether the request is waiting on an LLM or other network dependency

### Auth or item service fails on startup

Check:

- PostgreSQL health status
- database credentials in `.env`
- whether the container can reach `postgres`

## Monitoring stack

The dev and prod Compose files include:

- Prometheus on `http://localhost:9090`
- Grafana on `http://localhost:3000`
- cAdvisor scraped internally by Prometheus
- baseline Prometheus alert rules loaded from `monitoring/prometheus/rules/hackspark-alerts.yml`

Security note:

- In `docker-compose.prod.yml`, `cadvisor` requires elevated host access (`privileged: true`, Docker socket, and host mounts).
- Keep this as an intentional observability tradeoff for trusted environments; do not treat it as a hardened production baseline without additional controls.

App metrics are exposed at:

- gateway: `http://localhost:8000/metrics`
- auth service: `http://auth-service:8000/metrics` on the Compose network
- item service: `http://item-service:8000/metrics` on the Compose network
- AI service: `http://ai-agent-service:8000/metrics` on the Compose network
- Prometheus itself: `http://localhost:9090/metrics`

Metrics endpoint controls:

- `METRICS_ENABLED=false` disables `/metrics` on app services
- `METRICS_TOKEN=<token>` protects `/metrics` and requires Prometheus scrape configs to send the same token

If `METRICS_TOKEN` is set but scrape configs are not updated, Prometheus will receive `401` responses for app targets.

The default Grafana dashboard is `Hackspark Overview`. It is provisioned from the repo and should appear automatically on startup. It now includes route-level latency/error panels, in-flight requests, Prometheus health, and active alert count in addition to the original service and container views.

### Type checking shows unresolved `app.*` imports

Use the repo targets from `make typecheck`. They intentionally run `ty` per service because each service has its own import root and `ty.toml`.

## Future Hardening Ideas

After the hackathon, consider:

- separate databases per service
- dedicated migration job instead of startup bootstrapping
- centralized metrics and tracing
- secret management beyond `.env`
- replacing the mock AI backend with a real provider abstraction
