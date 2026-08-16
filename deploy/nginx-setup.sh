#!/usr/bin/env bash
# deploy/nginx-setup.sh — Настройка Nginx + Let's Encrypt для Минитендер.рф
# =============================================================================
# ⚠️ ЗАПУСКАТЬ НА СЕРВЕРЕ (не локально). Скрипт требует root/sudo.
# =============================================================================

set -euo pipefail

echo "=== Nginx + SSL Setup for минитендер.рф ==="

# -----------------------------------------------------------------------------
# 1. Установка зависимостей
# -----------------------------------------------------------------------------
echo "[1/6] Installing certbot and nginx plugin..."
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx nginx

# -----------------------------------------------------------------------------
# 2. Подготовка директории для Let's Encrypt webroot
# -----------------------------------------------------------------------------
echo "[2/6] Creating certbot webroot..."
sudo mkdir -p /var/www/certbot

# -----------------------------------------------------------------------------
# 3. Временный nginx-конфиг для certbot challenge (если нужен)
# -----------------------------------------------------------------------------
# Если вы используете docker-compose.prod.yml с nginx-ssl.conf,
# убедитесь, что volume ./nginx/nginx-ssl.conf подключён к контейнеру.
# На bare-metal скопируйте nginx-ssl.conf в /etc/nginx/nginx.conf:
#   sudo cp nginx/nginx-ssl.conf /etc/nginx/nginx.conf
#   sudo nginx -t && sudo systemctl reload nginx

# -----------------------------------------------------------------------------
# 4. Получение SSL-сертификатов
# -----------------------------------------------------------------------------
echo "[3/6] Requesting SSL certificates from Let's Encrypt..."
sudo certbot certonly \
  --standalone \
  -d минитендер.рф \
  -d www.минитендер.рф \
  -d xn--h1alffa9f.xn--p1ai \
  -d www.xn--h1alffa9f.xn--p1ai \
  --agree-tos \
  --non-interactive \
  --email admin@минитендер.рф \
  || {
    echo "ERROR: certbot failed. Check DNS A-records point to this server."
    exit 1
  }

# -----------------------------------------------------------------------------
# 5. Настройка автообновления сертификатов
# -----------------------------------------------------------------------------
echo "[4/6] Setting up auto-renewal..."
# certbot устанавливает systemd timer автоматически, но проверим:
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Тестовый прогон автообновления (безопасный — только проверка)
echo "[5/6] Testing certbot renewal (dry-run)..."
sudo certbot renew --dry-run

# -----------------------------------------------------------------------------
# 6. Перезагрузка Nginx
# -----------------------------------------------------------------------------
echo "[6/6] Reloading Nginx..."
sudo nginx -t && sudo systemctl reload nginx

echo "=== Setup complete ==="
echo "Certificates: /etc/letsencrypt/live/минитендер.рф/"
echo "Renewal timer: sudo systemctl status certbot.timer"
echo "Manual renew:  sudo certbot renew"
