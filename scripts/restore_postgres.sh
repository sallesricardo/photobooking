#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
INPUT="${1:?Usage: $0 backups/file.sql.gz}"

test -f "$INPUT"
echo "WARNING: this replaces data in the target database."
read -r -p "Type RESTORE to continue: " CONFIRM
[ "$CONFIRM" = "RESTORE" ]

gunzip -c "$INPUT" | docker compose -f "$COMPOSE_FILE" exec -T db psql \
  -U "${POSTGRES_USER:?POSTGRES_USER must be set}" \
  -d "${POSTGRES_DB:?POSTGRES_DB must be set}"
