# Documentation

Operational documentation for the RentPi microservices stack. The goal is to make the repo easy to onboard, modify, review, and demo without relying on tribal knowledge.

## Contents

- [architecture.md](./architecture.md) — System design, service map, gRPC contracts, data ownership, request flow, and repository layout.
- [api-documentation.md](./api-documentation.md) — Full HTTP API surface for the gateway: all endpoints, request/response shapes, auth model, and error codes.
- [development-guide.md](./development-guide.md) — Local setup, daily commands, gRPC workflow, how to add endpoints and services, database migrations, LLM provider config.
- [operations.md](./operations.md) — Docker runtime, environment variables, health checks, migration commands, and troubleshooting.
- [observability.md](./observability.md) — Structured logging, request correlation, Prometheus metrics, Grafana dashboards, and demo workflow.
- [git-workflow.md](./git-workflow.md) — Branch strategy, commit guidelines, and PR checklist for a short team sprint.
- [chat-curl-examples.md](./chat-curl-examples.md) — End-to-end curl examples for the chat endpoints (register → login → chat → session history).

## Recommended Reading Order

1. [architecture.md](./architecture.md) — understand the service boundaries and gRPC topology.
2. [development-guide.md](./development-guide.md) — get the environment running.
3. [api-documentation.md](./api-documentation.md) — reference while building features or integrating the frontend.
4. [chat-curl-examples.md](./chat-curl-examples.md) — smoke-test the full chat flow end-to-end.
5. [git-workflow.md](./git-workflow.md) — follow when the team starts parallel work.
6. [operations.md](./operations.md) — keep nearby while running or debugging Docker.
7. [observability.md](./observability.md) — use when demoing or extending logging and monitoring.

## Documentation Standards

- Update docs in the same change that modifies behavior, routes, environment variables, or service boundaries.
- Prefer exact file paths and command examples over abstract descriptions.
- Keep gateway contracts and downstream service contracts synchronized.
- Document dev-mode and prod-mode behavior separately when they differ.
- If a quick hack is added for demo speed, call it out explicitly so the team knows what is production-safe.
