#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=/data/backups/tool
DB_PATH=/data/toll.db
RETENTION_DAYS=14

mkdir -p "$BACKUP_DIR"
ts=$(date +%Y%m%d-%H%M%S)
cp "$DB_PATH" "$BACKUP_DIR/tool-$ts.db"

find "$BACKUP_DIR" -type f -name 'tool-*.db' -mtime +$RETENTION_DAYS -delete
