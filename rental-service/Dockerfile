FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.29 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock* .python-version README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/rental-service:/app
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY scripts ./scripts
COPY shared ./shared
COPY rental-service ./rental-service

WORKDIR /app/rental-service
CMD ["sh", "/app/scripts/start-rental.sh"]
