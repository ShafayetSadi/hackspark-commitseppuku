# API Documentation

This document describes the HTTP contracts implemented by the current scaffold.

## Base URL

When running locally through Docker:

```text
http://localhost:8000
```

The public client should usually call the API Gateway, not the individual services directly.

## Authentication Model

- Public routes:
  - `GET /health`
  - `POST /auth/register`
  - `POST /users/login`
- Protected routes:
  - `GET /auth/me`
  - `GET /items`
  - `POST /items`
  - `POST /ai/chat`

Protected requests must include:

```text
Authorization: Bearer <access_token>
```

## Error Response Format

All error responses follow one of two shapes depending on the source of the error.

**Application errors** (auth failures, conflicts, upstream issues) return a single string detail:

```json
{ "detail": "Invalid credentials" }
```

**Validation errors** (`422 Unprocessable Entity`) from malformed request bodies or invalid query parameters return a list:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

Common status codes across all services:

| Code | Meaning |
| ---- | ------- |
| `400` | Bad request (malformed input not caught by schema) |
| `401` | Missing, expired, or invalid bearer token; wrong credentials |
| `409` | Conflict — resource already exists (e.g. duplicate email) |
| `422` | Validation failure — request body or query params failed schema check |
| `502` | Gateway could not reach an upstream service |
| `504` | Upstream service timed out |

## Gateway Routes

### Health

`GET /health`

Response:

```json
{
  "status": "ok",
  "service": "api-gateway"
}
```

### Auth Proxy

- `POST /auth/register`
- `POST /users/login`
- `GET /auth/me`

### Item Proxy

- `GET /items`
- `POST /items`

### AI Proxy

- `POST /ai/chat`

## Gateway Failure Semantics

The gateway normalizes some upstream failures:

- `401` with `{"detail":"Missing bearer token"}` when a protected route is called without a bearer token
- `401` with `{"detail":"Invalid token"}` when JWT validation fails at the gateway
- `504` with `{"detail":"Upstream service timeout"}` when an upstream service does not respond within the configured proxy timeout
- `502` with `{"detail":"Upstream service unavailable"}` when an upstream service cannot be reached
- `502` with `{"detail":"Upstream service error"}` when an upstream service returns a `5xx` response

## Auth Service

Gateway path prefix: `/auth`

### POST /auth/register

Creates a user and returns a bearer token.

Request:

```json
{
  "email": "team@example.com",
  "password": "password123",
  "full_name": "Hack Team"
}
```

Response `201`:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Possible errors:

- `409` if the email already exists
- `422` if validation fails

### POST /users/login

Authenticates a user and returns a bearer token.

Request:

```json
{
  "email": "team@example.com",
  "password": "password123"
}
```

Response `200`:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Possible errors:

- `401` if credentials are invalid
- `422` if validation fails

### GET /auth/me

Returns the currently authenticated user.

Headers:

```text
Authorization: Bearer <jwt>
```

Response `200`:

```json
{
  "id": 1,
  "email": "team@example.com",
  "full_name": "Hack Team"
}
```

Possible errors:

- `401` if the token is missing, invalid, or references a deleted user

## Item Service

Gateway path prefix: `/items`

### GET /items

Returns a paginated list of items.

Query parameters:

- `page`: integer, default `1`
- `page_size`: integer, default `20`, max `100`
- `category`: optional string filter
- `search`: optional name search

Example:

```text
GET /items?page=1&page_size=20&category=rental&search=cam
```

Response `200`:

```json
{
  "items": [
    {
      "id": 1,
      "name": "Camera",
      "category": "rental",
      "quantity": 3,
      "created_at": "2026-04-28T00:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### POST /items

Creates an item.

Request:

```json
{
  "name": "Camera",
  "category": "rental",
  "quantity": 3
}
```

Response `201`:

```json
{
  "id": 1,
  "name": "Camera",
  "category": "rental",
  "quantity": 3,
  "created_at": "2026-04-28T00:00:00Z"
}
```

Possible errors:

- `401` if the bearer token is missing or invalid
- `422` if validation fails

## AI Agent Service

Gateway path prefix: `/ai`

### POST /ai/chat

Accepts a question and returns deterministic JSON output.

Request:

```json
{
  "query": "How does JWT auth protect item inventory endpoints?",
  "top_k": 2
}
```

Response `200`:

```json
{
  "answer": "Based on the indexed service context, the best answer to 'How does JWT auth protect item inventory endpoints?' is: JWT auth protects downstream services and keeps gateway checks centralized.",
  "sources": [
    "security/auth.md"
  ],
  "confidence": 0.6
}
```

Behavior notes:

- Irrelevant queries are rejected with a valid JSON payload rather than a transport error.
- The service uses lightweight relevance heuristics and an in-memory knowledge base.
- The response shape is stable even when no relevant context is found.

Example unrelated-query response:

```json
{
  "answer": "Query rejected because it is outside the supported business context.",
  "sources": [],
  "confidence": 0.0
}
```

## Downstream Health Endpoints

The following service-local routes exist mainly for container health checks:

- `GET /health` on `auth-service`
- `GET /health` on `item-service`
- `GET /health` on `ai-agent-service`

These are not intended as a substitute for gateway-level monitoring, but they are useful for debugging a specific container.
