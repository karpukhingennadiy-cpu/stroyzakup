"""Rate limiting for API endpoints."""
from django.core.cache import cache
from django.http import JsonResponse
import time

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
            key = f'ratelimit:{ip}'
            window = 60  # 1 minute
            max_requests = 100  # 100 requests per minute
            
            now = time.time()
            data = cache.get(key, [])
            data = [t for t in data if t > now - window]
            
            if len(data) >= max_requests:
                return JsonResponse(
                    {'error': 'Too many requests', 'retry_after': window},
                    status=429
                )
            
            data.append(now)
            cache.set(key, data, window)
        
        return self.get_response(request)
