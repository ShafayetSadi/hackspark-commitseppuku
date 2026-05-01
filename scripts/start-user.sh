#!/bin/sh
set -e

cd /app/user-service
alembic -c /app/user-service/alembic.ini upgrade head
exec python -m auth_service.main
