#!/usr/bin/env bash
# Бэкап PostgreSQL (pg_dump, custom format) + retention 14 дней.
# Использование:
#   ./scripts/backup_db.sh
#   DB_HOST=... DB_PASS` + 'WORD' + `=... ./scripts/backup_db.sh
# Для контейнера prod (docker-compose.prod.yml, сервис db):
#   docker compose -f docker-compose.prod.yml exec -T db pg_dump -U minitender -d minitender -Fc > backups/minitender.dump
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-minitender}"
DB_USER="${DB_USER:-minitender}"
export PGPASSWORD="${DB_PASSWORD:-}"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
FILE="$BACKUP_DIR/minitender_${STAMP}.dump"

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "ERROR: pg_dump not found (install postgresql-client)" >&2
  exit 1
fi

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -Fc -f "$FILE"
SIZE="$(du -h "$FILE" | cut -f1)"
echo "Backup OK: $FILE ($SIZE)"

OLD="$(find "$BACKUP_DIR" -name 'minitender_*.dump' -mtime +"$RETENTION_DAYS" | wc -l)"
find "$BACKUP_DIR" -name 'minitender_*.dump' -mtime +"$RETENTION_DAYS" -delete
echo "Retention: удалено $OLD файлов старше ${RETENTION_DAYS} дней"

# Cron на сервере:
#   0 3 * * * cd /opt/minitender && ./scripts/backup_db.sh >> /var/log/minitender-backup.log 2>&1
