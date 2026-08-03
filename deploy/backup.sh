#!/usr/bin/env bash
# Daily PostgreSQL backup — Минитендер.рф
#
# Запуск вручную:  ./deploy/backup.sh
# Через cron:      23 3 * * * /opt/minitender/deploy/backup.sh
#
# Параметры можно переопределить переменными окружения (см. deploy/BACKUP.md).

set -euo pipefail

# --- Конфигурация (переопределяется через env) ---
DB_NAME="${DB_NAME:-minitender}"
DB_USER="${DB_USER:-minitender}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/minitender}"
KEEP_DAYS="${KEEP_DAYS:-7}"
LOG_FILE="${LOG_FILE:-/var/log/minitender-backup.log}"

# Логирование: в файл + stdout; если файл недоступен — только stdout
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/${DB_NAME}_${STAMP}.sql.gz"

log "Backup started: ${DB_NAME}@${DB_HOST}:${DB_PORT} -> ${OUT}"

if pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME" | gzip > "$OUT"; then
    SIZE="$(du -h "$OUT" | cut -f1)"
    log "Backup complete: ${OUT} (${SIZE})"
else
    log "ERROR: pg_dump failed, removing partial file"
    rm -f "$OUT"
    exit 1
fi

# Ротация: хранить бэкапы за последние KEEP_DAYS дней
DELETED="$(find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime "+${KEEP_DAYS}" -print -delete | wc -l)"
log "Rotation done: kept last ${KEEP_DAYS} days in ${BACKUP_DIR} (removed ${DELETED} old file(s))"
