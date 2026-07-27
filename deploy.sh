#!/bin/bash
set -e

echo "=== Deploy Minitender ==="
cd /opt/minitender || cd /root/stroyzakup

# 1. Pull latest code
git pull origin main

# 2. Build/update containers
docker compose -f docker-compose.prod.yml build

# 3. Run migrations
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate --noinput

# 4. Collect static
docker compose -f docker-compose.prod.yml run --rm backend python manage.py collectstatic --noinput

# 5. Restart services
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# 6. Health check
sleep 5
curl -sf http://localhost:8000/api/ && echo "Backend OK" || echo "Backend FAIL"
curl -sf http://localhost:3000/ && echo "Frontend OK" || echo "Frontend FAIL"

echo "=== Deploy complete ==="
