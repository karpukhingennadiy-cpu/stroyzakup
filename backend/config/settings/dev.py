from .base import *

DEBUG = True
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# Remove django.contrib.gis for local dev (no GDAL needed)
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django.contrib.gis"]

# SQLite for local dev (no Docker needed)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Inbound email domain for reply addresses

# CORS for frontend dev
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True


# Sync Celery tasks in dev (no worker needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
# Force sync fallback: no broker = .delay() raises = sync fallback in views
CELERY_BROKER_URL = None
CELERY_RESULT_BACKEND = None
