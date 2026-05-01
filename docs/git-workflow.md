# Git Workflow

Lightweight branch, review, and commit workflow for a short hackathon sprint.

## Branch Strategy

- `main` — stable demo-ready branch
- `dev` — integration branch for active team work (optional for very small teams)
- `feat/<short-name>` — feature branches
- `fix/<short-name>` — bug-fix branches
- `docs/<short-name>` — documentation-only branches

## Branch Naming Examples

- `feat/rental-availability`
- `feat/analytics-surge`
- `feat/chat-sessions`
- `fix/gateway-grpc-timeout`
- `docs/api-reference`

## Daily Workflow

1. Pull the latest changes from the integration branch.
2. Create a focused branch for one task.
3. Keep changes scoped to one feature or one fix.
4. Run `make check` before opening a merge request or asking for review.
5. Merge back quickly to reduce drift.

## Commit Guidelines

Prefer short, descriptive commits:

- `feat(rental): add availability interval algorithm`
- `feat(analytics): add surge detection endpoint`
- `feat(chat): add Redis session store`
- `fix(gateway): correct gRPC deadline error mapping`
- `feat(proto): add GetDiscount RPC to user.proto`
- `docs(api): document rental endpoints`
- `chore(proto): regenerate grpc stubs`

Rules:
- One commit = one coherent change.
- Avoid mixing docs, refactors, and behavior changes without a reason.
- If the change modifies an API contract, update `docs/api-documentation.md` in the same branch.
- If the change adds a new proto RPC, commit the updated `.proto` **and** the regenerated stubs together.

## Pull Request Checklist

Before merging:
- Code builds locally or in Docker
- `make check` passes
- Docs updated for behavior changes
- New environment variables added to `.env.example`
- Proto changes regenerated with `make proto`
- Gateway routes and service contracts are still aligned
- No `CENTRAL_API_TOKEN` or other secrets committed

## Team Ownership Suggestions

For hackathon speed, assign broad ownership areas:
- One person on gateway and user-service
- One person on rental-service algorithms
- One person on analytics-service and agentic-service
- One person on frontend and demo flow

When touching `shared/app_core/` or `proto/`, coordinate — these affect every service.

## Merge Discipline

- Rebase or merge from `dev` frequently when the team is moving fast.
- Prefer smaller merges several times a day over one large end-of-day merge.
- If two branches touch the same service's gRPC contract or gateway routes, resolve the contract before coding diverges further.

## Documentation Workflow

Documentation is not a post-hack cleanup item. Update in the same PR:

- `docs/api-documentation.md` when routes or payloads change
- `docs/architecture.md` when service boundaries change
- `docs/development-guide.md` when setup or tooling changes
- `docs/operations.md` when Docker, health checks, or environment variables change
- `CLAUDE.md` when adding or changing services (the AGENTS.md table)

## Release and Demo Flow

Before a demo or judging session:

1. Merge selected changes into `main`.
2. Run `make down-v && make up-build` for a clean start.
3. Run the smoke tests from `CLAUDE.md` (register, login, rentals, analytics, chat).
4. Confirm `http://localhost:8000/status` shows all services green.
5. Confirm `http://localhost:3000` (frontend) is responsive.
6. Tag the demo commit if needed.

## If the Repository Is Not Yet Initialized

```bash
git init
git add .
git commit -m "chore: initialize hackathon boilerplate"
```

Then create `main` and `dev` branches according to the team workflow.
