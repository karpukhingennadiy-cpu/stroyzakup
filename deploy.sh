#!/bin/bash
# Автоматический деплой Минитендер.рф
set -e

echo "=== Минитендер.рф — деплой ==="

# Проверка прав
if [ "0" -ne 0 ]; then echo "Запустите от root: sudo bash deploy.sh"; exit 1; fi


# Зависимости
apt update && apt install -y python3 python3-venv python3-pip nginx postgresql redis nodejs npm git

# Клонирование
cd /opt
git clone https://github.com/karpukhingennadiy-cpu/stroyzakup.git minitender || (cd minitender && git pull)
cd minitender

# Бэкенд
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
echo "!!! Отредактируйте backend/.env: SECRET_KEY, DB_PASSWORD, SMTP_PASSWORD, LLM_API_KEY !!!"
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi --bind 127.0.0.1:8000 --daemon
echo "Backend: OK (127.0.0.1:8000)"

# Фронтенд
cd ../frontend
npm install && npm run build
npx next start -p 3000 &
echo "Frontend: OK (127.0.0.1:3000)"

# Nginx
cat > /etc/nginx/sites-available/minitender << 'NGINX'
server {
    listen 80;
    server_name минитендер.рф app.минитендер.рф;
    client_max_body_size 50M;
    location /api/ { proxy_pass http://127.0.0.1:8000; proxy_set_header Host ; proxy_set_header X-Real-IP ; }
    location /admin/ { proxy_pass http://127.0.0.1:8000; proxy_set_header Host ; }
    location / { proxy_pass http://127.0.0.1:3000; proxy_set_header Host ; }
}
NGINX
ln -sf /etc/nginx/sites-available/minitender /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Redis + Celery
systemctl enable --now redis
cd /opt/minitender/backend && source .venv/bin/activate && celery -A config worker --daemon

# HTTPS (Certbot)
apt install -y certbot python3-certbot-nginx
certbot --nginx -d минитендер.рф -d app.минитендер.рф --non-interactive --agree-tos -m admin@минитендер.рф

echo ""
echo "=== Деплой завершен ==="
echo "Сайт: https://минитендер.рф"
echo "API:  https://минитендер.рф/api/docs/"
echo "Не забудьте:"
echo "  1. Настроить DNS A-записи на IP этого сервера"
echo "  2. Заполнить backend/.env реальными паролями"
echo "  3. Создать почтовые ящики в панели Beget"
