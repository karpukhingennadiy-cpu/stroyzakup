#!/bin/bash
# Minitender.rf local server starter
cd /root/stroyzakup
echo '=== Minitender.rf - local server ==='
# Backend
if curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/ 2>/dev/null | grep -qE '401|200'; then
    echo 'Backend: already running on :8000'
else
    cd backend && .venv/bin/python manage.py runserver 0.0.0.0:8000 &
    sleep 2
    echo 'Backend: started on :8000'
fi
# Frontend
if curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/ 2>/dev/null | grep -q '200'; then
    echo 'Frontend: already running on :3000'
else
    cd /root/stroyzakup/frontend && npx next start -p 3000 -H 0.0.0.0 &
    sleep 3
    echo 'Frontend: started on :3000'
fi
echo ''
echo 'Site:     http://localhost:3000'
echo 'Admin:    http://localhost:8000/admin/'
echo 'Demo:     demo@minitender.ru / demo1234'
