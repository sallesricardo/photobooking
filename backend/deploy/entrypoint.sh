#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS_ONLY:-false}" = "true" ]; then
  echo "Running database migrations..."
  exec alembic upgrade head
fi

echo "Starting PhotoBooking API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-2}"
