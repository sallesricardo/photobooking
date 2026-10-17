#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT="$BACKUP_DIR/photobooking-$STAMP.sql.gz"

echo "Creating PostgreSQL backup: $OUTPUT"
docker compose -f "$COMPOSE_FILE" exec -T db pg_dump \
  -U "${POSTGRES_USER:?POSTGRES_USER must be set}" \
  -d "${POSTGRES_DB:?POSTGRES_DB must be set}" \
  --no-owner --no-privileges | gzip > "$OUTPUT"

echo "Backup completed."
