#!/bin/bash
# Healthcheck dev-окружения: backend / frontend / redis.
set -uo pipefail

backend_code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/ 2>/dev/null)
backend_status="DOWN"
if [ "$backend_code" = "401" ] || [ "$backend_code" = "200" ]; then
    backend_status="OK (HTTP $backend_code)"
fi

frontend_code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/ 2>/dev/null)
frontend_status="DOWN"
if [ "$frontend_code" = "200" ]; then
    frontend_status="OK (HTTP $frontend_code)"
fi

redis_pong=$(redis-cli ping 2>/dev/null)
redis_status="DOWN"
if [ "$redis_pong" = "PONG" ]; then
    redis_status="OK (PONG)"
fi

printf "%-12s | %s\n" "Service" "Status"
printf "%-12s | %s\n" "----------" "----------"
printf "%-12s | %s\n" "Backend" "$backend_status"
printf "%-12s | %s\n" "Frontend" "$frontend_status"
printf "%-12s | %s\n" "Redis" "$redis_status"