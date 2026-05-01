# API Documentation

HTTP contracts exposed by the API gateway. All requests go to `http://localhost:8000` when running locally.

## Authentication Model

**Public (no JWT required):**
- `GET /health`
- `GET /status`
- `GET /user-service/status`
- `GET /rental-service/status`
- `GET /analytics-service/status`
- `GET /agentic-service/status`
- `POST /users/register`
- `POST /users/login`
- `GET /docs`, `GET /redoc`, `GET /openapi.json`
- `GET /metrics`

**Protected** — all other routes require:
```text
Authorization: Bearer <access_token>
```

## Error Response Format

**Application errors:**
```json
{ "detail": "Invalid credentials" }
```

**Validation errors (422):**
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error.email" }
  ]
}
```

**Common status codes:**

| Code | Meaning |
|------|---------|
| `400` | Bad request — malformed input |
| `401` | Missing, expired, or invalid bearer token; wrong credentials |
| `404` | Resource not found |
| `409` | Conflict — resource already exists (e.g. duplicate email) |
| `422` | Schema validation failure |
| `502` | Gateway could not reach an upstream service (gRPC `UNAVAILABLE`) |
| `503` | Central API rate limit exceeded after retries |
| `504` | Upstream service timed out (gRPC `DEADLINE_EXCEEDED`) |

---

## Health & Status

### GET /health

```json
{ "status": "ok", "service": "api-gateway" }
```

### GET /status

Aggregates gRPC health checks from all downstream services in parallel.

```json
{
  "gateway": "ok",
  "user-service": "ok",
  "rental-service": "ok",
  "analytics-service": "ok",
  "agentic-service": "ok"
}
```

### GET /{service}/status

Returns the raw `/status` response from an individual service.

---

## User Service

### POST /users/register

Creates a user and returns a bearer token.

Request:
```json
{
  "email": "team@example.com",
  "password": "password123",
  "name": "Hack Team"
}
```

Response `201`:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Errors: `409` (email already exists), `422` (validation failure).

### POST /users/login

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

Errors: `401` (invalid credentials), `422`.

### GET /users/me

Returns the currently authenticated user.

Response `200`:
```json
{
  "id": "uuid",
  "email": "team@example.com",
  "full_name": "Hack Team"
}
```

Errors: `401`.

### GET /users/{user_id}/discount

Returns the discount percentage for a user based on their security score.

Response `200`:
```json
{
  "user_id": "uuid",
  "security_score": 85,
  "discount_percent": 10
}
```

Errors: `401`, `404`.

---

## Rental Service

All rental endpoints require `Authorization: Bearer <token>`.

### GET /rentals/products

Query parameters:
- `category`: optional string filter
- `page`: integer, default `1`
- `page_size`: integer, default `20`

Response `200`:
```json
{
  "products": [
    { "id": "...", "name": "Power Drill", "category": "TOOLS", "price_per_day": 25.0 }
  ],
  "total": 1
}
```

### GET /rentals/products/{product_id}

Response `200`: single product object.

Errors: `404`.

### GET /rentals/products/{product_id}/availability

Query parameters:
- `start_date`: `YYYY-MM-DD`
- `end_date`: `YYYY-MM-DD`

Response `200`:
```json
{
  "product_id": "...",
  "busy_periods": [
    { "start": "2026-05-01", "end": "2026-05-07" }
  ],
  "free_windows": [
    { "start": "2026-05-08", "end": "2026-05-31" }
  ]
}
```

### GET /rentals/kth-busiest-date

Query parameters:
- `k`: integer — rank position
- `start_date`: `YYYY-MM-DD`
- `end_date`: `YYYY-MM-DD`

Response `200`:
```json
{ "date": "2026-05-15", "rental_count": 42 }
```

### GET /rentals/products/{product_id}/free-streak

Query parameters:
- `year`: integer

Response `200`:
```json
{
  "product_id": "...",
  "year": 2026,
  "streak_start": "2026-06-01",
  "streak_end": "2026-06-30",
  "length_days": 30
}
```

### GET /rentals/merged-feed

Query parameters:
- `product_ids`: comma-separated list of product IDs
- `start_date`: `YYYY-MM-DD`
- `end_date`: `YYYY-MM-DD`

Response `200`:
```json
{
  "rentals": [
    { "product_id": "...", "start": "2026-05-01", "end": "2026-05-05", "user_id": "..." }
  ]
}
```

### GET /rentals/users/{user_id}/top-categories

Query parameters:
- `k`: integer — number of top categories to return

Response `200`:
```json
{
  "user_id": "...",
  "categories": [
    { "category": "TOOLS", "rental_count": 12 },
    { "category": "CAMERAS", "rental_count": 8 }
  ]
}
```

---

## Analytics Service

All analytics endpoints require `Authorization: Bearer <token>`.

### GET /analytics/trends

Query parameters:
- `category`: optional string
- `period`: optional (e.g. `monthly`, `weekly`)

Response `200`:
```json
{ "data": { ... } }
```

### GET /analytics/surge

Response `200`:
```json
{ "data": { ... } }
```

### GET /analytics/recommendations

Response `200`:
```json
{ "data": { ... } }
```

### GET /analytics/peak-window

Query parameters:
- `category`: optional string
- `month`: integer (1–12)
- `year`: integer

Response `200`:
```json
{ "data": { ... } }
```

### GET /analytics/surge-days

Query parameters:
- `category`: optional string
- `month`: integer
- `year`: integer

Response `200`:
```json
{ "data": { ... } }
```

---

## Agentic Service (Chat)

All chat endpoints require `Authorization: Bearer <token>`.

### POST /chat

Accepts a query and returns an AI-generated answer grounded in rental and analytics data.

Request:
```json
{
  "query": "Is the tools category growing?",
  "top_k": 3,
  "session_id": "optional-existing-session-id"
}
```

Response `200`:
```json
{
  "answer": "Yes, tools rentals are up 18% month-over-month...",
  "sources": ["analytics/trends", "rental/products"],
  "confidence": 0.85,
  "session_id": "uuid"
}
```

If `session_id` is omitted, a new session is created and the ID is returned.

### GET /chat/sessions

Returns a list of all active chat sessions.

Response `200`:
```json
{
  "sessions": [
    { "session_id": "uuid", "created_at": "...", "message_count": 5 }
  ]
}
```

### GET /chat/{session_id}/history

Returns the full conversation history for a session.

Response `200`:
```json
{
  "session_id": "uuid",
  "messages": [
    { "role": "user", "content": "Is tools growing?", "timestamp": "..." },
    { "role": "assistant", "content": "Yes, ...", "timestamp": "..." }
  ]
}
```

### DELETE /chat/{session_id}

Deletes a chat session and its history from Redis.

Response `204`: no content.

---

## Gateway Failure Semantics

| Response | Cause |
|----------|-------|
| `401 {"detail":"Missing bearer token"}` | Protected route called without `Authorization` header |
| `401 {"detail":"Invalid token"}` | JWT validation failed at gateway |
| `502 {"detail":"Upstream service unavailable"}` | gRPC `UNAVAILABLE` from downstream |
| `503 {"detail":"Central API rate limit exceeded"}` | Central API returned 429 after retries |
| `504 {"detail":"Upstream service timeout"}` | gRPC `DEADLINE_EXCEEDED` from downstream |

---

## Downstream Status Endpoints

Each service exposes `GET /status` on its HTTP port for container health checks:
- `http://user-service:8001/status`
- `http://rental-service:8002/status`
- `http://analytics-service:8003/status`
- `http://agentic-service:8004/status`

These are not proxied through the gateway for direct client use, but they are accessible through `GET /{service}/status` on the gateway.
