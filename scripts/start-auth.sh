#!/bin/sh
set -e

cd /app/services/auth_service
alembic upgrade head
exec uvicorn auth_service.main:app --host 0.0.0.0 --port 8000 --no-access-log
