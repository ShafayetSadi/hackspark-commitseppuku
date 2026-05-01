FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.29 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock* .python-version README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/api-gateway:/app
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY shared ./shared
COPY api-gateway ./api-gateway

WORKDIR /app/api-gateway
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
