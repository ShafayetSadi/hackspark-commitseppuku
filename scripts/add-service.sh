#!/bin/sh
# Usage: sh scripts/add-service.sh <service-name>
# Example: sh scripts/add-service.sh notification
#
# Creates services/<service-name>-service/ with a working FastAPI skeleton
# that mirrors the existing service structure.
set -e

SERVICE_NAME="${1:?Usage: add-service.sh <service-name>  (e.g. notification)}"
KEBAB="${SERVICE_NAME}-service"
SNAKE=$(echo "$SERVICE_NAME" | tr '-' '_')
DIR="services/${KEBAB}"
PKG="${DIR}/${SNAKE}_service"
CLASS_BASE=$(printf '%s\n' "$SERVICE_NAME" | awk -F '[-_]' '
{
  out = ""
  for (i = 1; i <= NF; i++) {
    if ($i == "") {
      continue
    }
    part = tolower($i)
    out = out toupper(substr(part, 1, 1)) substr(part, 2)
  }
  print out
}')
DISPLAY_NAME=$(printf '%s\n' "$SERVICE_NAME" | awk -F '[-_]' '
{
  for (i = 1; i <= NF; i++) {
    if ($i == "") {
      continue
    }
    part = tolower($i)
    $i = toupper(substr(part, 1, 1)) substr(part, 2)
  }
  OFS = " "
  print $0
}')

if [ -d "$DIR" ]; then
  echo "ERROR: $DIR already exists." >&2
  exit 1
fi

echo "→ Scaffolding $DIR ..."

mkdir -p \
  "${PKG}/api" \
  "${PKG}/core" \
  "${PKG}/schemas" \
  "${PKG}/services"

# ── __init__.py files ──────────────────────────────────────────────────────────
for d in "${PKG}" "${PKG}/api" "${PKG}/core" "${PKG}/schemas" "${PKG}/services"; do
  touch "${d}/__init__.py"
done

# ── core/config.py ─────────────────────────────────────────────────────────────
cat > "${PKG}/core/config.py" <<PYEOF
from functools import lru_cache

from shared.app_core.config import CommonSettings


class ${CLASS_BASE}ServiceSettings(CommonSettings):
    service_name: str = "${SNAKE}-service"
    service_port: int = 8000


@lru_cache
def get_settings() -> ${CLASS_BASE}ServiceSettings:
    return ${CLASS_BASE}ServiceSettings()
PYEOF

# ── schemas/base.py ────────────────────────────────────────────────────────────
cat > "${PKG}/schemas/base.py" <<PYEOF
from pydantic import BaseModel


class ExampleRequest(BaseModel):
    message: str


class ExampleResponse(BaseModel):
    reply: str
PYEOF

# ── api/routes.py ──────────────────────────────────────────────────────────────
cat > "${PKG}/api/routes.py" <<PYEOF
from fastapi import APIRouter

from ${SNAKE}_service.core.config import get_settings
from ${SNAKE}_service.schemas.base import ExampleRequest, ExampleResponse

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/example", response_model=ExampleResponse)
async def example(request: ExampleRequest):
    settings = get_settings()
    return ExampleResponse(reply=f"[{settings.service_name}] got: {request.message}")
PYEOF

# ── main.py ────────────────────────────────────────────────────────────────────
cat > "${PKG}/main.py" <<PYEOF
from fastapi import FastAPI

from ${SNAKE}_service.api.routes import router
from ${SNAKE}_service.core.config import get_settings
from shared.app_core.http import install_request_logging
from shared.app_core.logging import configure_logging, get_logger
from shared.app_core.metrics import install_metrics

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(settings.service_name)

app = FastAPI(
    title="${DISPLAY_NAME} Service",
    version="0.1.0",
    docs_url="/docs" if settings.service_docs_enabled else None,
    redoc_url="/redoc" if settings.service_docs_enabled else None,
    openapi_url="/openapi.json" if settings.service_docs_enabled else None,
)
app.state.logger = logger
install_metrics(app, settings.service_name)
install_request_logging(app, logger)
app.include_router(router)

logger.info("${SNAKE}_service_started")
PYEOF

# ── ty.toml ────────────────────────────────────────────────────────────────────
cat > "${DIR}/ty.toml" <<TOEOF
[environment]
python-version = "3.12"
root = ["."]
extra-paths = ["../.."]

[terminal]
error-on-warning = true
output-format = "concise"
TOEOF

# ── Dockerfile ─────────────────────────────────────────────────────────────────
cat > "${DIR}/Dockerfile" <<DEOF
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.29 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock* .python-version README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \\
    uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:\$PATH"

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY shared ./shared
COPY services/${KEBAB} ./services/${KEBAB}

WORKDIR /app/services/${KEBAB}
CMD ["uvicorn", "${SNAKE}_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
DEOF

# ── start script ───────────────────────────────────────────────────────────────
cat > "scripts/start-${SERVICE_NAME}.sh" <<SEOF
#!/bin/sh
set -e
cd /app/services/${KEBAB}
exec uvicorn ${SNAKE}_service.main:app --host 0.0.0.0 --port 8000 --no-access-log
SEOF
chmod +x "scripts/start-${SERVICE_NAME}.sh"

echo ""
echo "✓ Created ${DIR}/"
echo ""
echo "Next steps:"
echo "  1. Add to docker-compose.yml:"
echo "       ${KEBAB}:"
echo "         build:"
echo "           context: ."
echo "           dockerfile: services/${KEBAB}/Dockerfile"
echo "         env_file: [.env]"
echo "         environment:"
echo "           APP_ENV: dev"
echo "         ports: ['80XX:8000']"
echo ""
echo "  2. Register in gateway/gateway/core/config.py:"
echo "       ${SNAKE}_service_url: str = 'http://${KEBAB}:8000'"
echo "       and add to service_registry: {'${SNAKE}': self.${SNAKE}_service_url}"
echo ""
echo "  3. Add proxy routes in gateway/gateway/api/routes.py"
echo ""
echo "  4. Add Makefile typecheck step:"
echo "       uv run --directory services/${KEBAB} ty check ${SNAKE}_service"
echo ""
echo "  5. Add Prometheus scrape target in monitoring/prometheus/prometheus.yml:"
echo "       - job_name: ${KEBAB}"
echo "         metrics_path: /metrics"
echo "         static_configs:"
echo "           - targets: ['${KEBAB}:8000']"
echo ""
echo "  6. If this service should run in Compose, update docker-compose.yml and docker-compose.prod.yml"
echo "     consistently, then run:"
echo "       make check"
echo "       make monitoring-smoke"
