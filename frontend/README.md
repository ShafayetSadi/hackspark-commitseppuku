# Hackspark Frontend

This is a Next.js (App Router) frontend for the Hackspark backend.

## Features

- Register (`POST /auth/register`)
- Login (`POST /auth/login`)
- Session lookup (`GET /auth/me`)
- Logout (local cookie clear)

The browser talks to internal Next.js API routes under `/api/auth/*`, and those routes call the gateway/auth service. This avoids browser CORS issues in local dev.

## Run locally

From `frontend/`:

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Run on a custom port

```bash
npm run dev -- -p 4001
```

## Docker

A production-style container image is available via `frontend/Dockerfile`.

From repo root, run the full stack (including frontend) with Compose:

```bash
docker compose -f docker-compose.yml up --build
```

Frontend will be available at:

```text
http://localhost:3001
```

(Override with `FRONTEND_PORT` in `.env`.)

## Environment

Set the backend gateway URL used by Next.js route handlers:

```bash
GATEWAY_URL=http://localhost:8000
```

If unset, it defaults to `http://localhost:8000`.

Create `frontend/.env.local` if needed:

```env
GATEWAY_URL=http://localhost:8000
```
