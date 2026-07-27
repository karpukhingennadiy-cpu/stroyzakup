# Настройка домена минитендер.рф

## DNS (панель Beget)
A       @              IP сервера
MX      in             mx1.beget.com     10
TXT     @              v=spf1 include:spf.beget.com ~all
TXT     _dmarc         v=DMARC1; p=none; rua=mailto:admin@минитендер.рф

## Почтовые ящики Beget
rfq@минитендер.рф, notify@минитендер.рф, support@минитендер.рф

## .env (production)
DEBUG=False
DEFAULT_FROM_EMAIL=Минитендер RFQ <rfq@минитендер.рф>
INBOUND_EMAIL_DOMAIN=in.минитендер.рф

## Деплой
git clone https://github.com/karpukhingennadiy-cpu/stroyzakup.git /opt/minitender
cd /opt/minitender/backend && python3 -m venv .venv && pip install -r requirements.txt
python manage.py migrate && gunicorn config.wsgi --bind 127.0.0.1:8000 &
cd /opt/minitender/frontend && npm install && npm run build && npx next start -p 3000 &

## Nginx
server { server_name минитендер.рф; location / { proxy_pass http://127.0.0.1:3000; } }
