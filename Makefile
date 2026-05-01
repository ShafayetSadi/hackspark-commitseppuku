UV_CACHE_DIR ?= /tmp/uv-cache
COMPOSE ?= docker compose -f docker-compose.yml
REV ?= -1
MSG ?=
FRONTEND_DIR ?= frontend
NPM ?= npm
ALEMBIC_USER := alembic -c /app/user-service/alembic.ini

.PHONY: up down down-v logs build ps migrate migrate-user revision-user alembic-check downgrade sync lock format lint typecheck test check proto verify-chapter1 verify-chapter2 verify-chapter3 frontend-install frontend-dev frontend-lint frontend-build frontend-check

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

migrate-user:
	$(COMPOSE) exec user-service $(ALEMBIC_USER) upgrade head

migrate: migrate-user

revision-user:
	@test -n "$(MSG)" || (echo "Usage: make revision-user MSG=add_column" && exit 1)
	$(COMPOSE) exec user-service $(ALEMBIC_USER) revision --autogenerate -m "$(MSG)"

alembic-check:
	$(COMPOSE) exec user-service $(ALEMBIC_USER) check

downgrade:
	$(COMPOSE) exec user-service $(ALEMBIC_USER) downgrade $(REV)

proto:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m grpc_tools.protoc \
		-I proto \
		--python_out=shared/grpc_gen \
		--grpc_python_out=shared/grpc_gen \
		proto/user.proto proto/rental.proto proto/agentic.proto proto/analytics.proto
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -c "\
import re, pathlib; \
[f.write_text(re.sub(r'^import (\\w+_pb2) as', r'from shared.grpc_gen import \\1 as', f.read_text(), flags=re.MULTILINE)) \
 for f in pathlib.Path('shared/grpc_gen').glob('*_pb2_grpc.py')]"

verify-chapter1:
	sh scripts/verify-chapter1.sh

verify-chapter2:
	sh scripts/verify-chapter2.sh

verify-chapter3:
	sh scripts/verify-chapter3.sh

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
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --directory api-gateway ty check gateway
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --directory user-service ty check auth_service
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --directory rental-service ty check rental_service
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --directory agentic-service ty check ai_agent_service

test:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run pytest tests

check:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format --check .
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check .
	$(MAKE) typecheck
	$(MAKE) test

frontend-install:
	cd $(FRONTEND_DIR) && $(NPM) install

frontend-dev:
	cd $(FRONTEND_DIR) && $(NPM) run dev

frontend-lint:
	cd $(FRONTEND_DIR) && $(NPM) run lint

frontend-build:
	cd $(FRONTEND_DIR) && $(NPM) run build

frontend-check: frontend-lint frontend-build
