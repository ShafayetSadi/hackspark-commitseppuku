#!/bin/sh
set -e

cd /app/services/item-service
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
