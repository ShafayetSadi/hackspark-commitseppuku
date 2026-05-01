# Documentation

This folder is the operational documentation set for the `hackspark` microservices boilerplate. The goal is to make the repository easy to onboard, modify, review, and demo during a hackathon without relying on tribal knowledge.

## Contents

- [development-guide.md](./development-guide.md): local setup, daily workflow, quality checks, and how to add or change services.
- [architecture.md](./architecture.md): system design, service boundaries, data flow, and repository layout.
- [api-documentation.md](./api-documentation.md): API surface for the gateway and each backend service, with request and response examples.
- [git-workflow.md](./git-workflow.md): lightweight branch, review, and commit workflow suitable for a short team sprint.
- [operations.md](./operations.md): dev/prod Docker runtime notes, environment variables, migrations, health checks, and troubleshooting.
- [observability.md](./observability.md): structured logging, request correlation, Prometheus metrics, Grafana dashboards, and demo workflow.

## Recommended Reading Order

1. Read [architecture.md](./architecture.md) to understand the service boundaries.
2. Follow [development-guide.md](./development-guide.md) to set up the environment.
3. Use [api-documentation.md](./api-documentation.md) while building features or integrating a frontend.
4. Use [git-workflow.md](./git-workflow.md) when the team starts parallel work.
5. Keep [operations.md](./operations.md) nearby while running or debugging Docker.
6. Use [observability.md](./observability.md) when demoing, debugging, or extending logging and monitoring.

## Documentation Standards

- Update docs in the same change that modifies behavior, routes, environment variables, or service boundaries.
- Prefer exact file paths and command examples over abstract descriptions.
- Keep the gateway contract and downstream service contracts synchronized.
- Keep dev-mode and prod-mode behavior documented separately when they differ.
- If a quick hack is added for demo speed, call it out explicitly so the team knows what is production-safe and what is hackathon-only.
