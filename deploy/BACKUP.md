# Бэкапы БД — Минитендер.рф

Ежедневный бэкап PostgreSQL скриптом `deploy/backup.sh`: `pg_dump` → `.sql.gz`, ротация (хранятся бэкапы за последние 7 дней), лог в `/var/log/minitender-backup.log`.

## Установка на сервере

```bash
sudo mkdir -p /opt/backups/minitender
sudo touch /var/log/minitender-backup.log
sudo chown $(whoami) /var/log/minitender-backup.log
chmod +x deploy/backup.sh
```

## Запуск вручную

```bash
./deploy/backup.sh
```

Результат: `/opt/backups/minitender/minitender_YYYYMMDD_HHMMSS.sql.gz`.

## Cron (ежедневно в 03:23)

```cron
23 3 * * * /opt/minitender/deploy/backup.sh
```

Добавить: `crontab -e`. Скрипт сам пишет в `/var/log/minitender-backup.log`, дополнительное перенаправление не нужно.

## Конфигурация через переменные окружения

| Переменная | Default | Назначение |
|-----------|---------|-----------|
| `DB_NAME` | `minitender` | Имя базы |
| `DB_USER` | `minitender` | Пользователь PostgreSQL |
| `DB_HOST` | `localhost` | Хост БД |
| `DB_PORT` | `5432` | Порт БД |
| `BACKUP_DIR` | `/opt/backups/minitender` | Каталог бэкапов |
| `KEEP_DAYS` | `7` | Сколько дней хранить бэкапы |
| `LOG_FILE` | `/var/log/minitender-backup.log` | Файл лога |

Пример: `KEEP_DAYS=14 BACKUP_DIR=/mnt/backups ./deploy/backup.sh`

## Восстановление

```bash
gunzip -c /opt/backups/minitender/minitender_YYYYMMDD_HHMMSS.sql.gz | psql -U minitender -h localhost minitender
```

## Docker-контур

Если БД в Docker (`docker-compose.prod.yml`), запускайте `pg_dump` внутри контейнера:

```bash
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U minitender minitender | gzip > /opt/backups/minitender/minitender_$(date +%Y%m%d_%H%M%S).sql.gz
```

## Проверка бэкапов

- Лог: `tail -20 /var/log/minitender-backup.log`
- Список файлов: `ls -lh /opt/backups/minitender/`
- Рекомендуется периодически проверять восстановление на тестовой базе.
