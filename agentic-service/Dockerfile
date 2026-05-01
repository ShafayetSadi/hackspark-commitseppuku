FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.29 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock* .python-version README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/agentic-service:/app
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY scripts ./scripts
COPY shared ./shared
COPY agentic-service ./agentic-service

WORKDIR /app/agentic-service
CMD ["sh", "/app/scripts/start-agentic.sh"]
