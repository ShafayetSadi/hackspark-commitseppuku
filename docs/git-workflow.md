# Git Workflow

This repository is meant for fast parallel execution by a small team. The workflow should stay disciplined enough to avoid merge chaos, but light enough for a hackathon.

## Branch Strategy

Recommended branches:

- `main`: stable demo-ready branch
- `dev`: integration branch for active team work
- `feat/<short-name>`: feature branches
- `fix/<short-name>`: bug-fix branches
- `docs/<short-name>`: documentation-only branches

If the team is very small, `dev` can be optional. If multiple people are working at once, keep it.

## Branch Naming Examples

- `feat/auth-refresh`
- `feat/item-filters`
- `fix/gateway-token-check`
- `docs/api-reference`

## Daily Workflow

1. Pull the latest changes from the integration branch.
2. Create a focused branch for one task.
3. Keep changes scoped to one feature or one fix.
4. Run `make check` before opening a merge request or asking for review.
5. Merge back quickly to reduce drift.

## Commit Guidelines

Prefer short, descriptive commits:

- `feat(auth): add duplicate email guard`
- `feat(items): add category filter and pagination`
- `fix(gateway): reject missing bearer token`
- `docs(api): document chat response contract`
- `chore(dev): migrate project to uv and ruff`

Rules:

- One commit should represent one coherent change.
- Avoid mixing docs, refactors, and behavior changes without a reason.
- If the change modifies an API contract, update docs in the same branch.

## Pull Request Checklist

Before merging:

- code builds locally or in Docker
- `make check` passes
- docs are updated for behavior changes
- new environment variables are documented
- gateway and service contracts are still aligned

## Team Ownership Suggestions

For hackathon speed, assign broad ownership areas:

- one person on gateway and auth
- one person on domain services
- one person on AI integration or prompt behavior
- one person on frontend or demo flow

Even when ownership is broad, shared utilities should be changed carefully because they affect every service.

## Merge Discipline

- Rebase or merge from `dev` frequently if the team is moving fast.
- Prefer smaller merges several times a day instead of one large end-of-day merge.
- If two branches touch the same service entrypoints, resolve the contract before coding diverges further.

## Documentation Workflow

Documentation is not a post-hack cleanup item. Update:

- `docs/api-documentation.md` when routes or payloads change
- `docs/architecture.md` when service boundaries change
- `docs/development-guide.md` when setup or tooling changes
- `docs/operations.md` when Docker, health checks, or environment variables change

## Release and Demo Flow

Before a demo or judging session:

1. Merge the selected changes into `main`.
2. Run `docker compose -f docker-compose.prod.yml up --build`.
3. Verify auth, item creation, and AI chat via the gateway.
4. Confirm only `api-gateway` is published with `docker compose -f docker-compose.prod.yml ps`.
5. Tag the demo commit if needed.

## If the Repository Is Not Yet Initialized

If Git has not been initialized in the current working directory yet:

```bash
git init
git add .
git commit -m "chore: initialize hackathon boilerplate"
```

Then create `main` and `dev` according to the team workflow.
