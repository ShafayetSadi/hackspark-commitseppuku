UV_CACHE_DIR ?= /tmp/uv-cache
COMPOSE ?= docker compose -f docker-compose.yml
REV ?= -1
MSG ?=
FRONTEND_DIR ?= frontend
FRONTEND_PORT ?= 3001
NPM ?= npm
ALEMBIC_AUTH := alembic -c /app/services/auth_service/alembic.ini
ALEMBIC_ITEMS := alembic -c /app/services/item-service/alembic.ini

.PHONY: up down down-v logs build ps migrate-auth migrate-items migrate revision-auth revision-items alembic-check-auth alembic-check-items alembic-check downgrade-auth downgrade-items downgrade sync lock format lint typecheck test check add-service monitoring-smoke frontend-install frontend-dev frontend-lint frontend-build frontend-check

up:
	$(COMPOSE) up

up-build:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

down-v:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

build:
	$(COMPOSE) build

ps:
	$(COMPOSE) ps

migrate-auth:
	$(COMPOSE) exec auth-service $(ALEMBIC_AUTH) upgrade head

migrate-items:
	$(COMPOSE) exec item-service $(ALEMBIC_ITEMS) upgrade head

migrate: migrate-auth migrate-items

revision-auth:
	@test -n "$(MSG)" || (echo "Usage: make revision-auth MSG=create_users_table" && exit 1)
	$(COMPOSE) exec auth-service $(ALEMBIC_AUTH) revision --autogenerate -m "$(MSG)"

revision-items:
	@test -n "$(MSG)" || (echo "Usage: make revision-items MSG=create_items_table" && exit 1)
	$(COMPOSE) exec item-service $(ALEMBIC_ITEMS) revision --autogenerate -m "$(MSG)"

alembic-check-auth:
	$(COMPOSE) exec auth-service $(ALEMBIC_AUTH) check

alembic-check-items:
	$(COMPOSE) exec item-service $(ALEMBIC_ITEMS) check

alembic-check: alembic-check-auth alembic-check-items

downgrade-auth:
	$(COMPOSE) exec auth-service $(ALEMBIC_AUTH) downgrade $(REV)

downgrade-items:
	$(COMPOSE) exec item-service $(ALEMBIC_ITEMS) downgrade $(REV)

downgrade: downgrade-auth downgrade-items

add-service:
	@test -n "$(name)" || (echo "Usage: make add-service name=my-service" && exit 1)
	@sh scripts/add-service.sh "$(name)"

sync:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv sync

lock:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv lock

format:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format .

lint:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check .

typecheck:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ty check shared
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --directory gateway ty check gateway
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --directory services/auth_service ty check auth_service
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --directory services/ai_agent_service ty check ai_agent_service
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --directory services/item-service ty check app

test:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run pytest tests

check:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format --check .
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check .
	$(MAKE) typecheck
	$(MAKE) test

monitoring-smoke:
	curl -fsS http://localhost:8000/metrics >/dev/null
	curl -fsS http://localhost:9090/-/healthy >/dev/null
	curl -fsS http://localhost:9090/api/v1/query?query=up >/dev/null
	curl -fsS http://localhost:3000/api/health >/dev/null
	$(COMPOSE) exec prometheus wget -qO- "http://localhost:9090/api/v1/query?query=up{job=\"prometheus\"}" >/dev/null

frontend-install:
	cd $(FRONTEND_DIR) && $(NPM) install

frontend-dev:
	cd $(FRONTEND_DIR) && $(NPM) run dev -- -p $(FRONTEND_PORT)

frontend-lint:
	cd $(FRONTEND_DIR) && $(NPM) run lint

frontend-build:
	cd $(FRONTEND_DIR) && $(NPM) run build

frontend-check: frontend-lint frontend-build
