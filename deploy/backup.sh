#!/bin/bash
# Daily PostgreSQL backup
BACKUP_DIR=/opt/backups/minitender
mkdir -p 
DATE=20260727_225014
pg_dump -U minitender -h localhost minitender | gzip > /minitender_.sql.gz
# Keep last 7 days
find  -name '*.sql.gz' -mtime +7 -delete
echo "Backup complete: minitender_.sql.gz"
