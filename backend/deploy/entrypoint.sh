#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS_ONLY:-false}" = "true" ]; then
  echo "Running database migrations..."
  exec alembic upgrade head
  exit 0
fi

if [ "${RUN_MIGRATIONS_ON_START:-false}" = "true" ]; then
  echo "Running database migrations before application start..."
  alembic upgrade head
fi

if [ "${RUN_SEED:-false}" = "true" ]; then
  echo "Running catalog seed..."
  python -m app.db.seed
fi

echo "Starting PhotoBooking API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-2}"
