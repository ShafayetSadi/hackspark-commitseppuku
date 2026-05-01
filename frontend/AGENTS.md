<!-- BEGIN:nextjs-agent-rules -->
# Frontend agent guide (Next.js App Router)

This frontend uses **Next.js 16 + App Router** and is wired to the backend auth flow through server-side route handlers.

> Important: treat this as a modern Next.js App Router project (Server Components by default, Client Components only where needed).

## Current frontend architecture

- Main page: `app/page.tsx` (Server Component)
- Interactive auth UI: `app/components/auth-panel.tsx` (`"use client"`)
- Backend bridge routes (same-origin):
  - `app/api/auth/login/route.ts`
  - `app/api/auth/register/route.ts`
  - `app/api/auth/me/route.ts`
  - `app/api/auth/logout/route.ts`
- Shared auth helpers: `lib/auth-service.ts`

The browser should call `/api/auth/*` (Next handlers), **not** backend services directly.

## Auth integration contract

Gateway/auth endpoints used by route handlers:

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

Token handling:

- Store JWT in HTTP-only cookie: `hackspark_auth_token`
- Cookie options come from `authCookieOptions()` in `lib/auth-service.ts`
- For auth failures/unreachable backend, return stable JSON with `detail`

When backend is unavailable, route handlers should return:

- `503` + JSON `detail` message (do not leak stack traces)

## Environment

- `GATEWAY_URL` controls upstream base URL for Next route handlers.
- Default fallback: `http://localhost:8000`
- Local override file: `frontend/.env.local`

Example:

```env
GATEWAY_URL=http://localhost:8000
```

## Developer commands

From `frontend/`:

- Install deps: `npm install`
- Dev server: `npm run dev`
- Dev server custom port: `npm run dev -- -p 4001`
- Lint: `npm run lint`
- Build: `npm run build`

From repo root (dockerized frontend + backend):

- `docker compose -f docker-compose.yml up --build`
- frontend URL: `http://localhost:${FRONTEND_PORT:-3001}`

## Implementation rules

1. Keep `app/page.tsx` server-rendered unless interactivity is required.
2. Put interactive state/event logic in Client Components only.
3. Do not expose auth token to browser JS storage; keep HTTP-only cookie flow.
4. Keep error responses consistent (`{ detail: string }`).
5. Preserve dark/light styling conventions in existing UI files.
6. Use TypeScript types for request/response payloads.

## Verification checklist

For non-trivial frontend changes, run:

1. `npm run lint`
2. `npm run build`

If auth behavior changed, manually verify:

- Register
- Login
- Refresh profile (`/api/auth/me`)
- Logout
- Backend-down behavior returns clean 503 JSON
<!-- END:nextjs-agent-rules -->
